"""Suite for the station itself (spiral turn 15). The tool that verifies
every other repo was the only load-bearing code with no suite of its own.
Focus: the SPOOR machinery (say/refute/walk/recheck), attribution, errata —
the newest organs, where regressions would corrupt records silently."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import station  # noqa: E402


class StationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._spine, self._errata = station.SPINE, station.ERRATA
        station.SPINE = self.tmp / "spine.jsonl"
        station.ERRATA = self.tmp / "errata.jsonl"

    def tearDown(self):
        station.SPINE, station.ERRATA = self._spine, self._errata

    def _spine_events(self):
        return [json.loads(ln) for ln in
                station.SPINE.read_text(encoding="utf-8").splitlines()]

    def test_run_check_exit0_without_expect(self):
        ok, code, _ = station._run_check("cmd /c exit 0", "")
        self.assertTrue(ok)
        self.assertEqual(code, 0)

    def test_run_check_expect_fragment(self):
        ok, _, out = station._run_check("cmd /c echo hello-spoor", "hello-spoor")
        self.assertTrue(ok)
        bad, _, _ = station._run_check("cmd /c echo hello-spoor", "absent")
        self.assertFalse(bad)

    def test_say_true_claim_lands_as_fact(self):
        station.cmd_say(["a true thing", "--cmd", "cmd /c echo yes-42",
                        "--expect", "yes-42"])
        ev = self._spine_events()[-1]
        self.assertEqual(ev["kind"], "fact")
        self.assertTrue(ev["body"]["ok"])
        self.assertEqual(ev["body"]["claim"], "a true thing")

    def test_say_false_claim_refused_and_recorded(self):
        with self.assertRaises(SystemExit) as cm:
            station.cmd_say(["a false thing", "--cmd", "cmd /c echo actual",
                            "--expect", "claimed"])
        self.assertEqual(cm.exception.code, 1)
        ev = self._spine_events()[-1]
        self.assertEqual(ev["kind"], "refuted")   # false version never a fact
        self.assertFalse(ev["body"]["ok"])

    def test_walk_facts_detects_world_move(self):
        probe = self.tmp / "world.txt"
        probe.write_text("state-A", encoding="utf-8")
        station.cmd_say(["world is A", "--cmd", f'cmd /c type "{probe}"',
                        "--expect", "state-A"])
        (f, ok, _), = station._walk_facts(1)
        self.assertTrue(ok)                        # true while world holds
        probe.write_text("state-B", encoding="utf-8")
        (f, ok, out), = station._walk_facts(1)
        self.assertFalse(ok)                       # STALE when world moves
        self.assertIn("state-B", out)              # fresh truth travels

    def test_spine_attribution(self):
        os.environ["STATION_ACTOR"] = "suite-probe"
        try:
            station._spine_append("note", "attributed")
        finally:
            del os.environ["STATION_ACTOR"]
        station._spine_append("note", "anonymous")
        events = self._spine_events()
        self.assertEqual(events[-2]["by"], "suite-probe")
        self.assertTrue(events[-1]["by"].startswith("pid"))

    def test_burn_rollup_idempotent_and_cert_marked(self):
        # the cumulative counter's one integrity invariant: a day lands ONCE
        _led, _scan, _cert = (station.BURN_LEDGER, station._burn_days,
                              station._certified_count)
        station.BURN_LEDGER = self.tmp / "burn.jsonl"
        station._burn_days = lambda days: {d: 1000 for d in days}
        station._certified_count = lambda: 5
        try:
            station.cmd_burn()
            station.cmd_burn()   # second run must add nothing
            recs = [json.loads(ln) for ln in station.BURN_LEDGER.read_text(
                encoding="utf-8").splitlines()]
        finally:
            station.BURN_LEDGER, station._burn_days = _led, _scan
            station._certified_count = _cert
        days = [r["day"] for r in recs if r["kind"] == "day"]
        self.assertEqual(len(days), len(set(days)))   # no double-append
        self.assertEqual(len(days), 28)
        certs = [r for r in recs if r["kind"] == "cert"]
        self.assertEqual(len(certs), 1)               # marker lands once
        self.assertEqual(certs[0]["certified"], 5)

    def test_eras_split_at_cert_markers(self):
        import io
        from contextlib import redirect_stdout
        _led, _scan = station.BURN_LEDGER, station._burn_days
        station.BURN_LEDGER = self.tmp / "burn.jsonl"
        with station.BURN_LEDGER.open("w", encoding="utf-8") as f:
            for rec in (
                {"kind": "day", "day": "2026-01-01", "burn": 100},
                {"kind": "day", "day": "2026-01-02", "burn": 200},
                {"kind": "cert", "certified": 1, "day": "2026-01-02"},
                {"kind": "day", "day": "2026-01-03", "burn": 50},
            ):
                f.write(json.dumps(rec) + "\n")
        station._burn_days = lambda days: {d: 25 for d in days}
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                station.cmd_eras()
        finally:
            station.BURN_LEDGER, station._burn_days = _led, _scan
        out = buf.getvalue()
        self.assertIn("burn~300 -> cert #1", out)     # closed era summed
        self.assertIn("burn~75", out)                 # open = 50 + 25 partial
        self.assertIn("OK", out)                      # 75 <= 300

    def test_recheck_stale_lands_one_deduped_spine_event(self):
        probe = self.tmp / "world.txt"
        probe.write_text("state-A", encoding="utf-8")
        station.cmd_say(["world is A", "--cmd", f'cmd /c type "{probe}"',
                        "--expect", "state-A"])
        probe.write_text("state-B", encoding="utf-8")   # the world moves
        for _ in range(2):                              # unattended cadence
            with self.assertRaises(SystemExit) as cm:
                station.cmd_recheck(3)
            self.assertEqual(cm.exception.code, 1)
        stales = [e for e in self._spine_events() if e["kind"] == "stale"]
        self.assertEqual(len(stales), 1)                # news once, not 8x/day
        self.assertEqual(stales[0]["body"]["n"], 1)
        self.assertIn("world is A", stales[0]["body"]["claims"][0])

    def test_superseded_fact_leaves_the_walk(self):
        probe = self.tmp / "world.txt"
        probe.write_text("state-A", encoding="utf-8")
        route = f'cmd /c type "{probe}"'
        station.cmd_say(["world is A", "--cmd", route, "--expect", "state-A"])
        probe.write_text("state-B", encoding="utf-8")   # world moves on
        station.cmd_say(["world is B", "--cmd", route, "--expect", "state-B"])
        walked = station._walk_facts(5)
        self.assertEqual(len(walked), 1)                # one fact per route
        f, ok, _ = walked[0]
        self.assertEqual(f["body"]["claim"], "world is B")
        self.assertTrue(ok)                             # and it is current

    def test_retire_removes_fact_from_walk_but_not_record(self):
        probe = self.tmp / "world.txt"
        probe.write_text("state-A", encoding="utf-8")
        station.cmd_say(["moment fact", "--cmd", f'cmd /c type "{probe}"',
                        "--expect", "state-A"])
        probe.write_text("state-B", encoding="utf-8")   # fact now stale
        station.cmd_retire("moment fact")
        self.assertEqual(station._walk_facts(5), [])    # gone from the walk
        kinds = [e["kind"] for e in self._spine_events()]
        self.assertIn("fact", kinds)                    # record untouched
        self.assertIn("retired", kinds)                 # retirement witnessed

    def test_seal_stamps_clock_and_discards_typed_t(self):
        import io
        led = self.tmp / "led.jsonl"
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(
            {"t": "1999-01-01T00:00:00Z", "turn": 99, "x": 1}))
        try:
            station.cmd_seal(str(led))
        finally:
            sys.stdin = old_stdin
        r = json.loads(led.read_text(encoding="utf-8").splitlines()[-1])
        self.assertNotEqual(r["t"], "1999-01-01T00:00:00Z")  # typed t dies
        self.assertRegex(r["t"], r"^20\d\d-\d\d-\d\dT")       # clock stamped
        self.assertEqual(r["x"], 1)                           # payload intact
        self.assertIn("by", r)                                # attributed

    def test_concurrent_spine_appends_never_tear(self):
        # turn-33 stress at full scale: plain 'a'-mode lost 1553/4000 and
        # tore 177. This is the scaled invariant guard (5 procs x 50).
        import subprocess
        wf = self.tmp / "w.py"
        wf.write_text(
            "import sys; sys.path.insert(0, r'E:\\station')\n"
            "import station\nfrom pathlib import Path\n"
            "station.SPINE = Path(sys.argv[1])\n"
            "for i in range(50):\n"
            "    station._spine_append('stress', {'w': int(sys.argv[2]), 'i': i})\n",
            encoding="utf-8")
        procs = [subprocess.Popen([sys.executable, str(wf),
                                   str(station.SPINE), str(w)])
                 for w in range(5)]
        for p in procs:
            p.wait()
        seen = set()
        for ev in self._spine_events():          # raises on any torn line
            seen.add((ev["body"]["w"], ev["body"]["i"]))
        self.assertEqual(len(seen), 250)         # nothing lost

    def test_errata_add_appends_classed_entry(self):
        station.cmd_errata(["add", "test-class", "what happened",
                           "the cost", "the guard"])
        e = json.loads(station.ERRATA.read_text(encoding="utf-8")
                       .splitlines()[-1])
        self.assertEqual(e["cls"], "test-class")
        self.assertEqual(e["guard"], "the guard")


class PreregTests(unittest.TestCase):
    def test_verdict_entry_supersedes_armed_status(self):
        import tempfile as tf
        tmp = Path(tf.mkdtemp())
        _p, _s = station.PREREGS, station.SPINE
        station.PREREGS = tmp / "preregs.jsonl"
        station.SPINE = tmp / "spine.jsonl"
        try:
            with station.PREREGS.open("w", encoding="utf-8") as f:
                f.write(json.dumps({"id": "x", "status": "armed",
                                    "due": "2020-01-01", "rule": "r"}) + "\n")
            regs = station._fold_preregs()
            self.assertEqual(regs["x"]["status"], "armed")
            station.cmd_preregs(["score", "x", "FAIL", "the organ died"])
            regs = station._fold_preregs()
            self.assertEqual(regs["x"]["status"], "FAIL")
            self.assertEqual(regs["x"]["evidence"], "the organ died")
        finally:
            station.PREREGS, station.SPINE = _p, _s


class MarketTests(unittest.TestCase):
    """Income is only an external signal if the ledger refuses self-report."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._market, self._packs, self._spine = (station.MARKET,
                                                  station.MARKET_PACKS,
                                                  station.SPINE)
        station.MARKET = self.tmp / "market.jsonl"
        station.MARKET_PACKS = self.tmp / "packs"
        station.SPINE = self.tmp / "spine.jsonl"
        self.proof = self.tmp / "proof.txt"
        self.proof.write_text("verified evidence", encoding="utf-8")
        self.receipt = self.tmp / "receipt.txt"
        self.receipt.write_text("external payment receipt", encoding="utf-8")

    def tearDown(self):
        station.MARKET, station.MARKET_PACKS, station.SPINE = (self._market,
                                                                 self._packs,
                                                                 self._spine)

    def _thesis(self):
        return {
            "id": "proof-offer", "buyer": "an engineering team",
            "problem": "agent behavior cannot be reproduced",
            "offer": "an evidence-bound reliability diagnostic",
            "proofs": [str(self.proof)],
            "test": "a buyer asks to review the scope",
            "kill": "no qualified external signal by due date",
            "due": "2099-01-01",
        }

    def _arm(self):
        import io
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(self._thesis()))
        try:
            station.cmd_market(["arm"])
        finally:
            sys.stdin = old_stdin

    def test_market_arm_requires_existing_proof_and_folds(self):
        self._arm()
        row = station._fold_market()["proof-offer"]
        self.assertEqual(row["status"], "armed")
        self.assertEqual(row["proofs"], [str(self.proof)])
        self.assertEqual(self._spine_events()[-1]["kind"], "market-arm")

    def _spine_events(self):
        return [json.loads(line) for line in
                station.SPINE.read_text(encoding="utf-8").splitlines()]

    def test_paid_signal_requires_receipt_pointer(self):
        self._arm()
        with self.assertRaises(SystemExit):
            station.cmd_market(["score", "proof-offer", "PAID", "someone said yes"])
        station.cmd_market(["score", "proof-offer", "INTEREST",
                            "meeting notes: buyer requested scope"])
        self.assertEqual(station._fold_market()["proof-offer"]["status"], "INTEREST")
        station.cmd_market(["score", "proof-offer", "PAID",
                            f"receipt:{self.receipt}"])
        self.assertEqual(station._fold_market()["proof-offer"]["status"], "PAID")

    def test_market_pack_carries_hashes_and_kill_condition(self):
        self._arm()
        station.cmd_market(["verify", "proof-offer"])
        station.cmd_market(["pack", "proof-offer"])
        packet = station.MARKET_PACKS / "proof-offer.md"
        body = packet.read_text(encoding="utf-8")
        self.assertIn("sha256:", body)
        self.assertIn(self._thesis()["kill"], body)
        self.assertIn("does not claim customer demand", body)


class ImmunityTests(unittest.TestCase):
    """A test earns protection only by rejecting its declared nearby wound."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "specimen"
        self.root.mkdir()
        (self.root / "subject.py").write_text("VALUE = 7\n", encoding="utf-8")
        (self.root / "check.py").write_text(
            "import subject\nassert subject.VALUE == 7\n", encoding="utf-8")
        self._immune, self._spine, self._registry = (station.IMMUNITY,
                                                       station.SPINE,
                                                       station._registry)
        station.IMMUNITY = self.tmp / "immunity.jsonl"
        station.SPINE = self.tmp / "spine.jsonl"
        station._registry = lambda: {"suites": [{
            "name": "specimen", "cwd": str(self.root),
            "cmd": f'"{sys.executable}" check.py',
        }]}

    def tearDown(self):
        station.IMMUNITY, station.SPINE, station._registry = (self._immune,
                                                                self._spine,
                                                                self._registry)

    def _trial(self):
        return {"id": "value-guard", "suite": "specimen", "target": "subject.py",
                "find": "VALUE = 7", "replace": "VALUE = 0",
                "reason": "The checker must distinguish the guarded value.",
                "kill": "The mutant exits zero or the live source changes."}

    def _arm(self):
        import io
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(self._trial()))
        try:
            station.cmd_immune(["arm"])
        finally:
            sys.stdin = old_stdin

    def test_disposable_lesion_is_killed_without_touching_live_source(self):
        self._arm()
        station.cmd_immune(["run", "value-guard"])
        row = station._fold_immunity()["value-guard"]
        self.assertEqual(row["outcome"]["status"], "KILLED")
        self.assertEqual((self.root / "subject.py").read_text(encoding="utf-8"),
                         "VALUE = 7\n")
        events = [json.loads(line) for line in
                  station.SPINE.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["kind"], "immune-run")


class OrganTests(unittest.TestCase):
    """station organs (spiral turn 51): the ledger read as a registry."""

    def setUp(self):
        import tempfile as tf
        self.tmp = Path(tf.mkdtemp())
        self.ledger = self.tmp / "spiral.jsonl"
        self.alive = self.tmp / "alive.txt"
        self.alive.write_text("x", encoding="utf-8")
        rows = [
            {"turn": 1, "target": "crystal", "verdict": "GAIN",
             "built": f"a thing at {self.alive} plus station wake",
             "kill": "if the thing rots"},
            {"turn": 2, "target": "efficiency", "verdict": "GAIN",
             "built": f"gone artifact {self.tmp / 'missing.py'}",
             "open": "parked verification"},
        ]
        with self.ledger.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def _run(self, args):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                station.cmd_organs(args, path=self.ledger)
        return cm.exception.code, buf.getvalue()

    def test_missing_ref_flagged_and_exit1(self):
        code, out = self._run([])
        self.assertEqual(code, 1)
        self.assertIn("ORGANS entries=2", out)
        self.assertIn("MISSING:", out)
        self.assertIn("missing.py", out)
        self.assertNotIn("T1 ", out)          # healthy organ hidden by default
        self.assertIn("OPEN | parked verification", out)

    def test_all_lists_healthy_organs_too(self):
        code, out = self._run(["--all"])
        self.assertEqual(code, 1)             # ledger still has one MISSING
        self.assertIn("refs=2/2", out)        # path + station:wake both ok

    def test_kill_mode_emits_falsifier_corpus_exit0(self):
        code, out = self._run(["--kill"])
        self.assertEqual(code, 0)
        self.assertIn("if the thing rots", out)
        self.assertNotIn("MISSING:", out)     # no per-row flags in kill mode


class LeaseTests(unittest.TestCase):
    def setUp(self):
        import tempfile as tf
        self._leases = station.LEASES
        station.LEASES = Path(tf.mkdtemp()) / "leases"

    def tearDown(self):
        station.LEASES = self._leases

    def test_lease_lifecycle_and_expiry_takeover(self):
        self.assertTrue(station._lease_acquire("x", 900))
        # same pid re-acquires (reentrant by design)
        self.assertTrue(station._lease_acquire("x", 900))
        # a live foreign holder blocks
        (station.LEASES / "y.lease").write_text(json.dumps(
            {"pid": -1, "exp": 9e12, "by": "other"}), encoding="utf-8")
        self.assertFalse(station._lease_acquire("y", 900))
        # an EXPIRED foreign holder is taken over — dead holders never wedge
        (station.LEASES / "z.lease").write_text(json.dumps(
            {"pid": -1, "exp": 0, "by": "dead"}), encoding="utf-8")
        self.assertTrue(station._lease_acquire("z", 900))
        station._lease_release("x")
        self.assertTrue(station._lease_acquire("x", 900))


class PulseSpeakerTests(unittest.TestCase):
    """The autonomic speakers (turns 11 + 35): wrong dedupe = spine spam
    or silenced transitions; both corrupt the record's signal."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        import pulse
        self.pulse = pulse
        self._here, self._demi = pulse.HERE, pulse.DEMIURGE
        self._run = pulse.run
        pulse.HERE = self.tmp                    # spine read path
        pulse.DEMIURGE = self.tmp                # hunt ledger path
        self.calls = []
        pulse.run = lambda cmd, cwd, timeout: (self.calls.append(cmd)
                                               or (0, ""))

    def tearDown(self):
        self.pulse.HERE, self.pulse.DEMIURGE = self._here, self._demi
        self.pulse.run = self._run

    def _ledger(self, *kinds):
        with (self.tmp / "ledger.jsonl").open("a", encoding="utf-8") as f:
            for k in kinds:
                f.write(json.dumps({"t": "x", "kind": k,
                                    "cell": "q9n9r9"}) + "\n")

    def test_hunt_last_returns_latest_kind(self):
        self._ledger("hunt-noemit", "hunt-attempt", "hunt-certified")
        self.assertEqual(self.pulse.hunt_last("q9n9r9"), "hunt-certified")
        self.assertEqual(self.pulse.hunt_last("absent-cell"), "none")

    def test_say_hunt_speaks_transitions_dedupes_repeats(self):
        self._ledger("hunt-noemit")
        self.pulse.say_hunt("q9n9r9")            # first outcome: speaks
        self.assertEqual(len(self.calls), 1)
        # simulate the fact landing in the spine, then an unchanged rerun
        (self.tmp / "spine.jsonl").write_text(json.dumps(
            {"kind": "fact", "body":
             {"claim": "hunt q9n9r9 latest outcome = hunt-noemit"}}) + "\n",
            encoding="utf-8")
        self.pulse.say_hunt("q9n9r9")            # repeat: silent
        self.assertEqual(len(self.calls), 1)
        self._ledger("hunt-certified")           # transition: speaks again
        self.pulse.say_hunt("q9n9r9")
        self.assertEqual(len(self.calls), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
