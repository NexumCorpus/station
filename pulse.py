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
  6. BACKUP + spine note, every beat.

Usage: python pulse.py [--dry]     Schedule: schtasks (see register_pulse.ps1)
"""
from __future__ import annotations

import json
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
HUNT_CELL = "q2n14r2"
HUNT_MODEL = "ollama:qwen2.5-coder:7b"    # free local proposer ONLY
PY = sys.executable
DRY = "--dry" in sys.argv


def run(cmd: list, cwd: Path, timeout: int = 7200):
    if DRY:
        print("[dry]", " ".join(str(c) for c in cmd))
        return 0, ""
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def note(txt: str):
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


def sweep_already_running() -> bool:
    code, out = run(["powershell", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_Process -Filter \"Name like "
                     "'%python%'\" | Where-Object { $_.CommandLine -match "
                     "'sweep_w2|sweep\\.py|autoloop' }).Count"], HERE, 120)
    try:
        return int(out.strip().splitlines()[-1]) > 0
    except (ValueError, IndexError):
        return True                       # unsure -> don't double-dispatch


def main():
    beat = {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    # 1 — hygiene gate
    d_code, _ = run([PY, str(HERE / "station.py"), "drift"], HERE, 600)
    w_code, _ = run([PY, str(HERE / "station.py"), "witness"], HERE, 600)
    if d_code != 0 or w_code != 0:
        beat["action"] = f"HALTED-HYGIENE drift={d_code} witness={w_code}"
        note(f"PULSE {beat['action']} — estate NOT advanced; investigate")
        print(beat)
        return

    counts = scored_counts()
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
        # is up. Certification stays behind the same external gate.
        code, out = run([PY, str(DEMIURGE / "hunt.py"), HUNT_CELL,
                         HUNT_MODEL], DEMIURGE, timeout=3600)
        tail = out.strip().splitlines()[-1][:120] if out.strip() else ""
        beat["action"] = f"hunt-cycle({HUNT_CELL}) exit={code} | {tail}"
    elif not (DEMIURGE / "KILL").exists() and not sweep_already_running():
        # 5 — the compounding loop beats on its own
        code, out = run([PY, str(DEMIURGE / "autoloop.py"), "1", "5", "900"],
                        DEMIURGE, timeout=3600)
        tail = out.strip().splitlines()[-1][:120] if out.strip() else ""
        beat["action"] = f"demiurge-cycle exit={code} | {tail}"
    else:
        beat["action"] = "idle (work in flight or KILL present)"

    # 5 — survivability, every beat
    run([PY, str(HERE / "station.py"), "backup"], HERE, 900)
    note(f"PULSE {beat['action']}")
    print(beat)


if __name__ == "__main__":
    main()
