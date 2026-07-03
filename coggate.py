"""coggate — the station's own growth gate (D4: the last hand-crank).

Until now the station's cognitive artifacts (skills, plays, preambles,
doctrines) were adopted on the author's say-so — the exact epistemic
position Specimen 0's self-assessed progress occupied. This gate closes the
recursion: an artifact claiming to improve agent performance is ADOPTED only
if cold agents GIVEN it measurably outperform cold agents WITHOUT it.

PRE-REGISTERED ADOPTION RULE (fixed 2026-07-03, before the first trial):
  - A/B trial, n >= 4 per arm, same task, fresh workspaces, same model.
  - Primary: mean transfer_rate(treatment) >= mean transfer_rate(control)
    + 0.10  ->  ADOPT.
  - Secondary path (efficiency claims): transfer non-inferior (>= control
    - 0.02) AND mean duration <= 0.75 x control  ->  ADOPT-EFFICIENCY.
  - Anything else -> REJECT. Ties reject: adoption requires evidence.
  - Trials run on a WEAK model (default haiku) for headroom; external
    validity to stronger agents is a stated caveat, never assumed away.
  - Dispatch failures excluded per estate law; trial void if either arm
    ends with n < 4 scored.
Every trial appends to coggate-ledger.jsonl (witness-registered): artifact
hash, arms, per-organism results, verdict. Rejections are permanent record.

Usage: python coggate.py <artifact.md> <task_dir> [n_per_arm] [model]
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MISSION = Path("E:/boundary/mission1")
RUNS = Path("E:/mission-runs")
LEDGER = HERE / "coggate-ledger.jsonl"
TIMEOUT_S = 900
PACE_S = 15

sys.path.insert(0, str(MISSION))
from scorer import score_organism, load_task_config   # noqa: E402

DIRECTIVE = ("Implement {module} according to brief.md so that all public "
             "tests pass and the functions behave correctly for every case "
             "the brief describes. Read brief.md carefully first. You have "
             "about 15 minutes; ship the best working version you have "
             "rather than nothing.")


def dispatch(ws: Path, prompt: str, model: str) -> dict:
    claude = shutil.which("claude")
    t0 = time.time()
    try:
        p = subprocess.run([claude, "-p", prompt, "--model", model,
                            "--permission-mode", "bypassPermissions"],
                           cwd=str(ws), capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=TIMEOUT_S)
        code, out = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        code, out = -1, "(timed out)"
    (ws / "_agent.log").write_text(out, encoding="utf-8")
    return {"exit": code, "duration_s": round(time.time() - t0, 1)}


def run_arm(arm: str, trial: str, n: int, task_dir: Path, prompt: str,
            model: str) -> list[dict]:
    results = []
    for k in range(n):
        ws = RUNS / f"cog_{trial}_{arm}_{k}"
        shutil.copytree(task_dir / "skeleton", ws)
        shutil.copy2(task_dir / "brief.md", ws / "brief.md")
        meta = dispatch(ws, prompt, model)
        if meta["exit"] != 0:
            results.append({"k": k, "excluded": f"exit={meta['exit']}"})
            print(f"[cog] {arm}#{k} EXCLUDED exit={meta['exit']}", flush=True)
        else:
            s = score_organism(ws, task_dir)
            results.append({"k": k, "transfer": s["transfer_rate"],
                            "duration_s": meta["duration_s"],
                            "public": s["public_pass"]})
            print(f"[cog] {arm}#{k} transfer={s['transfer_rate']:.2f} "
                  f"dur={meta['duration_s']:.0f}s", flush=True)
        time.sleep(PACE_S)
    return results


def main():
    artifact = Path(sys.argv[1])
    task_dir = Path(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    model = sys.argv[4] if len(sys.argv) > 4 else "haiku"
    cfg = load_task_config(task_dir)
    trial = time.strftime("%Y%m%d_%H%M%S")
    art_text = artifact.read_text(encoding="utf-8-sig")
    art_sha = hashlib.sha256(art_text.encode()).hexdigest()[:16]

    base = DIRECTIVE.format(module=cfg["module_file"])
    treated = ("Operating notes (follow them):\n" + art_text.strip()
               + "\n\n---\n\n" + base)

    print(f"[cog] trial {trial}: {artifact.name} @{art_sha} on "
          f"{task_dir.name}, n={n}/arm, model={model}", flush=True)
    control = run_arm("ctl", trial, n, task_dir, base, model)
    treatment = run_arm("trt", trial, n, task_dir, treated, model)

    def stats(rows):
        ok = [r for r in rows if "excluded" not in r]
        if len(ok) < 4:
            return None
        tr = sum(r["transfer"] for r in ok) / len(ok)
        du = sum(r["duration_s"] for r in ok) / len(ok)
        return {"n": len(ok), "transfer": round(tr, 4),
                "duration_s": round(du, 1)}

    c, t = stats(control), stats(treatment)
    if c is None or t is None:
        verdict = "VOID (an arm fell below n=4 scored)"
    elif t["transfer"] >= c["transfer"] + 0.10:
        verdict = "ADOPT"
    elif (t["transfer"] >= c["transfer"] - 0.02
          and t["duration_s"] <= 0.75 * c["duration_s"]):
        verdict = "ADOPT-EFFICIENCY"
    else:
        verdict = "REJECT (no evidenced improvement)"

    entry = {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "trial": trial, "artifact": artifact.name, "sha": art_sha,
             "task": task_dir.name, "model": model,
             "control": c, "treatment": t,
             "raw": {"control": control, "treatment": treatment},
             "verdict": verdict}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[cog] control={c} treatment={t}")
    print(f"[cog] VERDICT: {verdict} -> ledgered")
    sys.exit(0 if verdict.startswith("ADOPT") else 2)


if __name__ == "__main__":
    main()
