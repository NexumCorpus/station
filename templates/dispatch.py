"""TEMPLATE: dispatch a CLI agent organism/worker — the hardened pattern.
Carries: out-of-repo workspace law (INCIDENT-001), timeout partial capture,
throttle-vs-wall discrimination, exclusion-not-scoring for dispatch
failures, pacing. Copy-adapt; do not re-derive."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

RUNS = Path("E:/mission-runs")        # OUTSIDE every git repo. Always.
TIMEOUT_S = 1200
PACE_S = 20                           # burst-throttle pacing between dispatches
MODEL = "sonnet"


def dispatch(workspace: Path, prompt: str, timeout_s: int = TIMEOUT_S) -> dict:
    """One agent run. Returns meta dict; NEVER raises on agent failure."""
    claude = shutil.which("claude")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [claude, "-p", prompt, "--model", MODEL,
             "--permission-mode", "bypassPermissions"],
            cwd=str(workspace), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout_s)
        exit_code, out = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as exc:
        def _d(b):
            if b is None:
                return ""
            return b.decode("utf-8", errors="replace") if isinstance(b, bytes) else b
        exit_code, out = -1, "(timed out)\n" + _d(exc.stdout) + _d(exc.stderr)
    (workspace / "_agent.log").write_text(out, encoding="utf-8")
    meta = {"exit": exit_code, "duration_s": round(time.time() - t0, 1)}
    (workspace / "_meta.json").write_text(json.dumps(meta, indent=1),
                                          encoding="utf-8")
    return meta


def classify_failure(workspace: Path, exit_code: int) -> str | None:
    """None = success. 'hard-wall' = session budget gone (STOP the wave).
    'throttle' = transient burst limit (cooldown + continue).
    'exit=N' = agent error (exclude, continue)."""
    if exit_code == 0:
        return None
    log = (workspace / "_agent.log").read_text(
        encoding="utf-8", errors="replace").lower()
    if "resets" in log and "limit" in log:
        return "hard-wall"
    if "limit" in log:
        return "throttle"
    return f"exit={exit_code}"
# Loop discipline: dispatch failures are EXCLUDED from data, never scored
# (a quota kill must not masquerade as a capability failure). Pace PACE_S
# between dispatches; cool down 180s after 2 consecutive exclusions; only
# hard-wall stops the run.
