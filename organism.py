"""Whole-body rehearsal primitives (spiral 125).

An organism report is a receipt for a *fixed* roster of independently owned
organs.  It is deliberately not a planner: the runner is allowed to execute
only registered local checks, then record what happened.  A clean receipt says
the named routes passed at the named source revisions; it does not authorize a
mutation, an external action, or a claim about future performance.
"""
from __future__ import annotations

from collections.abc import Iterable


ORGANS = ("atlas", "rde", "boundary", "ege", "director2", "demiurge",
          "station", "continuity")
REQUIRED_RESULT = ("organ", "status", "route", "head", "state", "exit",
                   "seconds", "tail")


def validate_plan(plan: Iterable[dict], repos: dict) -> list[str]:
    """Reject a rehearsal whose roster silently lost an organ or gained a
    caller-provided command.  Routes are fixed by station.py, not its CLI."""
    rows = list(plan)
    names = [row.get("organ") for row in rows]
    defects = []
    if tuple(names) != ORGANS:
        defects.append("roster must be exactly " + ",".join(ORGANS))
    for row in rows:
        organ = str(row.get("organ", "?"))
        if row.get("repo") not in repos:
            defects.append(f"{organ}: unknown registry repo")
        if not isinstance(row.get("route"), str) or not row["route"]:
            defects.append(f"{organ}: missing fixed route label")
    return defects


def report(now: str, results: list[dict]) -> dict:
    """Build a schema-checked, appendable receipt from individual organ runs."""
    defects = []
    names = []
    for row in results:
        names.append(row.get("organ"))
        missing = [key for key in REQUIRED_RESULT if key not in row]
        if missing:
            defects.append(f"{row.get('organ', '?')}: missing {','.join(missing)}")
        if row.get("status") not in ("OK", "ROT"):
            defects.append(f"{row.get('organ', '?')}: invalid status")
        if not isinstance(row.get("seconds"), (int, float)) or row.get("seconds") < 0:
            defects.append(f"{row.get('organ', '?')}: invalid duration")
    if tuple(names) != ORGANS:
        defects.append("result roster must be exactly " + ",".join(ORGANS))
    if defects:
        raise ValueError("organism receipt invalid: " + "; ".join(defects))
    passed = sum(1 for row in results if row["status"] == "OK")
    return {
        "kind": "organism-rehearsal",
        "t": now,
        "executor": "deterministic fixed-route runner",
        "authority": "none: observation only; no mutation, external action, or claim authorization",
        "verdict": "BODY-OK" if passed == len(results) else "BODY-ROT",
        "passed": passed,
        "total": len(results),
        "results": results,
    }


def render(receipt: dict) -> str:
    """Dense human/agent readout.  Tails are receipt evidence, not claims."""
    lines = [f"ORGANISM {receipt['verdict']} {receipt['passed']}/{receipt['total']} "
             f"executor=deterministic authority=none t={receipt['t']}"]
    for row in receipt["results"]:
        tail = str(row["tail"]).replace("\n", " ")[-160:]
        lines.append(f"{row['status']:<3} {row['organ']:<10} head={row['head']:<12} "
                     f"state={row['state']:<12} exit={row['exit']:<4} "
                     f"{row['seconds']:.2f}s | {tail}")
    return "\n".join(lines)
