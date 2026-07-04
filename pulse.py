"""station pulse — the estate's heartbeat. Runs WITHOUT any LLM: pure
deterministic advancement of every standing campaign, scheduled (Windows
Task Scheduler), zero tokens except the organisms it dispatches — which are
the point. Neither operator nor agent needs to be present for the estate to
move.

Each beat, in priority order (one advancing action per beat + hygiene):
  1. HYGIENE GATE: drift + witness. Any alarm/drift -> record, DO NOT
     advance (a machine that advances on corrupted records compounds the
     corruption).
  2. WAVE COMPLETION: if wave-2 has unscored (tier, instance) slots and no
     sweep is already running -> resume it (paced, wall-aware, idempotent).
  3. REGISTERED ANALYSIS: if all tiers reached n>=8 and no verdict file
     exists -> run analyze_w2, write the verdict artifact, telegraph it.
  4. HUNT (free only): else, if the local ollama proposer is up and no KILL
     file -> one covering-code record attempt (demiurge/hunt.py) on the
     LOCAL model. The pulse NEVER launches a metered hunt — quota strain is
     a standing condition, not a surprise (flag analysis 2026-07-03). A
     certified WORLD_FIRST is ledgered for the operator; never announced.
  5. DEMIURGE CYCLE: else, if no KILL file -> one gated self-improvement
     cycle (the compounding loop, beating nightly instead of when someone
     remembers).
  6. NIGHT MIND: hermes digest — free local model pre-digests new log bytes
     into advisory candidates (own cursor namespace; never steals the wake's
     unread signal; extractive-only per sleep-compute evidence).
  7. BACKUP + spine note, every beat.

Usage: python pulse.py [--dry]     Schedule: schtasks (see register_pulse.ps1)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MISSION = Path("E:/boundary/mission1")
RUNS = Path("E:/mission-runs")
DEMIURGE = Path("E:/demiurge")
VERDICT = RUNS / "w2_verdict.txt"
TIERS = ["T1", "T2", "T3", "T4"]
TARGET_N = 8
HUNT_CELLS = ["q2n14r2", "q3n8r1", "q2n13r2", "q3n7r1", "q2n12r2", "q3n6r1"]
HUNT_MODEL = "ollama:qwen2.5-coder:7b"    # free local proposer ONLY
PY = sys.executable
DRY = "--dry" in sys.argv
JLEDGER = HERE / "pulse-ledger.jsonl"
BEAT_ID = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def jnote(step: str, **kw):
    """Beat journal: one dense line per step, append-only. A beat killed
    mid-flight (console close, timeout, crash) leaves its tail naming the
    exact in-flight command — forensics in one cursor read instead of
    schtasks/process/spine archaeology."""
    rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "beat": BEAT_ID, "pid": os.getpid(), "step": step}
    if DRY:
        rec["dry"] = True
    rec.update(kw)
    try:
        # locked append (turn 33): beats can overlap manual/dry runs; plain
        # 'a'-mode writes tear under contention on Windows
        import station
        station._append_line(JLEDGER, json.dumps(rec) + "\n")
    except OSError:
        pass                              # journaling must never kill a beat


def run(cmd: list, cwd: Path, timeout: int = 7200):
    tail = " ".join(str(c) for c in cmd)[-160:]
    jnote("run", cmd=tail)
    if DRY:
        print("[dry]", tail)
        jnote("ran", cmd=tail, exit=0, secs=0)
        return 0, ""
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    jnote("ran", cmd=tail, exit=p.returncode,
          secs=round(time.time() - t0, 1))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def note(txt: str):
    if DRY:
        print("[dry] note:", txt)
        return
    subprocess.run([PY, str(HERE / "station.py"), "note", txt],
                   capture_output=True)


def scored_counts() -> dict:
    counts = {t: 0 for t in TIERS}
    ledger = RUNS / "w2_results.jsonl"
    if ledger.is_file():
        for ln in ledger.read_text(encoding="utf-8-sig").splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            if ("excluded" not in r and not r.get("pilot")
                    and r.get("tier") in counts):
                counts[r["tier"]] += 1
    return counts


def ollama_up() -> bool:
    """Self-healing: WSL has no systemd, so a nohup'd `ollama serve` dies when
    the distro idles down between beats. If the API is unreachable, start it
    (as root, per grimoire #23) and re-probe once. Zero metered tokens either
    way — this only gates the FREE hunt branch."""
    probe = ("curl -s --max-time 8 http://localhost:11434/api/tags")
    code, out = run(["wsl", "-d", "Ubuntu", "--", "bash", "-lc", probe], HERE, 30)
    if "models" in out:
        return True
    run(["wsl", "-d", "Ubuntu", "-u", "root", "--", "bash", "-lc",
         "nohup ollama serve >/tmp/ollama.log 2>&1 & sleep 6"], HERE, 40)
    code, out = run(["wsl", "-d", "Ubuntu", "--", "bash", "-lc", probe], HERE, 30)
    return "models" in out


def say_counts(counts: dict):
    """Autonomic SPOOR (Law I — work migrates downward): the beat utters its
    wave counts as a spine FACT. The route re-executes at write, so a wrong
    count lands as 'refuted', never as fact; a mid-utterance world-move
    (sweep scoring during the say) is an honest refutation, not an error.
    Skips when unchanged since last said — facts are news, not heartbeat
    filler. This closes spiral turn 10's adoption risk structurally: the
    handoff's standing-facts block is fed by trusted code, not by an agent
    remembering a reflex."""
    claim = f"wave-2 scored slots {json.dumps(counts)}"
    spine = HERE / "spine.jsonl"
    if spine.is_file():
        for ln in reversed(spine.read_text(encoding="utf-8").splitlines()):
            if '"kind": "fact"' in ln and 'wave-2 scored slots' in ln:
                if json.loads(ln)["body"]["claim"] == claim:
                    return                    # unchanged — say nothing
                break
    run([PY, str(HERE / "station.py"), "say", claim,
         "--cmd", f'"{PY}" "{HERE / "pulse.py"}" --counts',
         "--expect", json.dumps(counts)], HERE, 120)


def hunt_last(cell: str) -> str:
    """Last hunt outcome kind for a cell from the demiurge ledger — the
    stable re-derivation route for the hunt speaker."""
    led = DEMIURGE / "ledger.jsonl"
    last = "none"
    if led.is_file():
        for ln in led.read_text(encoding="utf-8-sig").splitlines():
            if '"kind": "hunt' in ln and f'"{cell}"' in ln:
                last = json.loads(ln).get("kind", "none")
    return last


def say_hunt(cell: str):
    """Autonomic SPOOR speaker #2 (turn 35, closes turn-11's open item):
    after a hunt cycle, the outcome becomes a spine FACT routed into the
    demiurge ledger. Deduped on the claim — a repeat noemit is not news;
    a transition (noemit -> certified/rejected) always is."""
    outcome = hunt_last(cell)
    claim = f"hunt {cell} latest outcome = {outcome}"
    spine = HERE / "spine.jsonl"
    if spine.is_file():
        for ln in reversed(spine.read_text(encoding="utf-8").splitlines()):
            if '"kind": "fact"' in ln and f"hunt {cell}" in ln:
                if json.loads(ln)["body"]["claim"] == claim:
                    return
                break
    run([PY, str(HERE / "station.py"), "say", claim,
         "--cmd", f'"{PY}" "{HERE / "pulse.py"}" --hunt-last {cell}',
         "--expect", outcome], HERE, 120)


_sweep_probe = None                       # per-beat memo (turn 14): the
                                          # branch chain asks 3x; the answer
                                          # cannot legitimately change inside
                                          # one decision, so probe once


def sweep_already_running() -> bool:
    global _sweep_probe
    if _sweep_probe is not None:
        return _sweep_probe
    code, out = run(["powershell", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_Process -Filter \"Name like "
                     "'%python%'\" | Where-Object { $_.CommandLine -match "
                     "'sweep_w2|sweep\\.py|autoloop' }).Count"], HERE, 120)
    try:
        _sweep_probe = int(out.strip().splitlines()[-1]) > 0
    except (ValueError, IndexError):
        _sweep_probe = True               # unsure -> don't double-dispatch
    return _sweep_probe


def main():
    # self-name for spine attribution; every child (sweep, hunt, digest,
    # station calls) inherits it — anonymous estate events end here
    os.environ["STATION_ACTOR"] = f"pulse-beat-{BEAT_ID}"
    beat = {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    jnote("beat-start")

    # 1 — hygiene gate
    d_code, _ = run([PY, str(HERE / "station.py"), "drift"], HERE, 600)
    w_code, _ = run([PY, str(HERE / "station.py"), "witness"], HERE, 600)
    if d_code != 0 or w_code != 0:
        beat["action"] = f"HALTED-HYGIENE drift={d_code} witness={w_code}"
        note(f"PULSE {beat['action']} — estate NOT advanced; investigate")
        jnote("beat-end", action=beat["action"])
        print(beat)
        return

    counts = scored_counts()
    say_counts(counts)
    incomplete = {t: n for t, n in counts.items() if n < TARGET_N}

    if incomplete and not sweep_already_running():
        # 2 — advance the wave. Two manual rules, now structural:
        # (a) husk cleanup: an excluded/crashed dispatch leaves a workspace
        #     without _score.json, which skip-existing would block forever;
        # (b) top-up with FRESH instance numbers (instances are never
        #     reused), sized per tier to reach TARGET_N.
        import shutil as sh
        for d in RUNS.glob("w2_T*_*"):
            if (d.is_dir() and not (d / "_score.json").is_file()
                    and "husk" not in d.name):
                sh.rmtree(d, ignore_errors=True)
        for tier, n in incomplete.items():
            used = [int(p.name.split("_")[-1])
                    for p in RUNS.glob(f"w2_{tier}_*") if p.name[-2:].isdigit()]
            ledger = RUNS / "w2_results.jsonl"
            if ledger.is_file():
                used += [r.get("instance", 0) for r in
                         (json.loads(x) for x in
                          ledger.read_text(encoding="utf-8-sig").splitlines()
                          if x.strip())
                         if r.get("tier") == tier]
            start = max(used, default=0) + 1
            fresh = ",".join(str(i) for i in
                             range(start, start + (TARGET_N - n)))
            code, out = run([PY, "-u", str(MISSION / "sweep_w2.py"),
                             tier, fresh], MISSION, timeout=4 * 3600)
            if "HARD WALL" in out:
                beat["wall"] = tier
                break
        beat["action"] = f"wave-topup counts={scored_counts()}"
    elif not incomplete and not VERDICT.exists():
        # 3 — the registered analysis fires itself the moment n is reached
        code, out = run([PY, str(MISSION / "analyze_w2.py")], MISSION, 600)
        if not DRY:
            VERDICT.write_text(out, encoding="utf-8")
        beat["action"] = f"REGISTERED-VERDICT written exit={code}"
        note("PULSE: wave-2 complete -> registered P4-P7 analysis executed "
             "-> E:/mission-runs/w2_verdict.txt (operator: read + report)")
    elif (not (DEMIURGE / "KILL").exists() and not sweep_already_running()
          and ollama_up()):
        # 4 — free-proposer record hunt: zero metered tokens, so it takes
        # priority over the metered demiurge cycle whenever the local model
        # is up. Certification stays behind the same external gate. Cells
        # rotate by day-of-year so the whole record front gets attacked.
        cell = HUNT_CELLS[int(time.strftime("%j")) % len(HUNT_CELLS)]
        code, out = run([PY, str(DEMIURGE / "hunt.py"), cell,
                         HUNT_MODEL], DEMIURGE, timeout=3600)
        tail = out.strip().splitlines()[-1][:120] if out.strip() else ""
        beat["action"] = f"hunt-cycle({cell}) exit={code} | {tail}"
        if not DRY:
            say_hunt(cell)                # speaker #2: outcome -> spine fact
    elif not (DEMIURGE / "KILL").exists() and not sweep_already_running():
        # 5 — the compounding loop beats on its own
        code, out = run([PY, str(DEMIURGE / "autoloop.py"), "1", "5", "900"],
                        DEMIURGE, timeout=3600)
        tail = out.strip().splitlines()[-1][:120] if out.strip() else ""
        beat["action"] = f"demiurge-cycle exit={code} | {tail}"
    else:
        beat["action"] = "idle (work in flight or KILL present)"
    jnote("action", action=beat["action"])

    # 6 — night mind: pre-digest new log bytes on the FREE model (advisory
    # candidates; wake cursors untouched, raw bytes remain the record).
    # Evidence-bounded: extractive+schema only (station/research/sleep-compute.md).
    if not DRY and ollama_up():
        code, out = run([PY, str(HERE / "hermes.py"), "digest"], HERE, 1800)
        beat["digest"] = out.strip().splitlines()[-1][:80] if out.strip() else ""

    # 7 — survivability, every beat
    # vitals sample first: the section-15 trend needs a time series nobody
    # has to remember to take (8 samples/day; ~2s; spine 'vitals' events)
    run([PY, str(HERE / "station.py"), "vitals", "24"], HERE, 300)
    # daily burn rollup + cert markers (no-op unless a UTC day completed or
    # certified moved; feeds station eras — the SS15 decidable form)
    run([PY, str(HERE / "station.py"), "burn"], HERE, 300)
    # autonomic fact hygiene: re-derive the last sealed facts; a world-move
    # after seal lands as a deduped 'stale' spine event instead of crossing
    # a molt as a quotable lie (exit 1 on stale is expected, not a beat fail)
    run([PY, str(HERE / "station.py"), "recheck", "8"], HERE, 600)
    run([PY, str(HERE / "station.py"), "backup"], HERE, 900)
    note(f"PULSE {beat['action']}")
    jnote("beat-end", action=beat["action"])
    print(beat)


if __name__ == "__main__":
    if "--counts" in sys.argv:
        # the stable re-derivation route for the beat's autonomic fact
        print(json.dumps(scored_counts()))
    elif "--hunt-last" in sys.argv:
        # stable route for the hunt speaker's fact
        print(hunt_last(sys.argv[sys.argv.index("--hunt-last") + 1]))
    else:
        main()
