"""Counterfactual-immunity primitives (spiral 97).

The live estate is never mutated. A registered suite root is copied to a
temporary specimen, its declared single-site lesion is applied there, and the
same registered suite is run before and after. This proves sensitivity to one
specific nearby failure, never universal coverage.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REQUIRED = ("id", "suite", "target", "find", "replace", "reason", "kill")
ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}$")
IGNORED = {".git", "__pycache__", ".pytest_cache", "cursors", "digests"}


def sha16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def suite_index(registry: dict) -> dict[str, dict]:
    return {str(s.get("name")): s for s in registry.get("suites", [])
            if isinstance(s, dict) and s.get("name")}


def validate_trial(trial: dict, suites: dict[str, dict]):
    """Reject ambiguous or self-selected mutations before they enter a ledger."""
    if not isinstance(trial, dict):
        raise ValueError("trial must be a JSON object")
    missing = [field for field in REQUIRED if not trial.get(field)]
    if missing:
        raise ValueError("trial missing " + ", ".join(missing))
    ident = str(trial["id"])
    if not ID.fullmatch(ident):
        raise ValueError("id must be 3-64 lowercase letters, digits, or hyphens")
    suite = suites.get(str(trial["suite"]))
    if not suite:
        raise ValueError("suite is not registered: " + str(trial["suite"]))
    root = Path(str(suite.get("cwd", "")))
    if not root.is_dir() or not suite.get("cmd"):
        raise ValueError("registered suite has no runnable local root")
    target = Path(str(trial["target"]))
    if target.is_absolute() or ".." in target.parts or target == Path("."):
        raise ValueError("target must be a non-empty relative path inside the suite root")
    if not (root / target).is_file():
        raise ValueError("target does not exist in suite root: " + str(target))
    find, replace = str(trial["find"]), str(trial["replace"])
    if not find or find == replace:
        raise ValueError("find and replace must be distinct, non-empty strings")
    hits = (root / target).read_text(encoding="utf-8", errors="strict").count(find)
    if hits != 1:
        raise ValueError(f"find must occur exactly once in target (found {hits})")


def fold(rows: list[dict]) -> dict[str, dict]:
    """Fold the append-only trial/outcome stream into its current projection."""
    trials: dict[str, dict] = {}
    for row in rows:
        ident = row.get("id")
        if not isinstance(ident, str):
            continue
        if row.get("kind") == "trial":
            trials[ident] = {"trial": row, "outcome": None}
        elif row.get("kind") == "outcome" and ident in trials:
            trials[ident]["outcome"] = row
    return trials


def _ignore(_dir: str, names: list[str]) -> list[str]:
    return [name for name in names if name in IGNORED]


def _run(command: str, cwd: Path, timeout_s: int = 180) -> dict:
    try:
        p = subprocess.run(command, shell=True, cwd=str(cwd), text=True,
                           capture_output=True, timeout=timeout_s)
        text = ((p.stdout or "") + (p.stderr or "")).strip()
        return {"exit": p.returncode, "tail": text[-400:]}
    except subprocess.TimeoutExpired:
        return {"exit": -124, "tail": f"timeout after {timeout_s}s"}
    except OSError as exc:
        return {"exit": -127, "tail": f"runner error: {exc}"}


def run_trial(trial: dict, suites: dict[str, dict]) -> dict:
    """Exercise a declared lesion in a disposable copy of its suite root."""
    validate_trial(trial, suites)
    suite = suites[trial["suite"]]
    root = Path(suite["cwd"]).resolve()
    target = Path(trial["target"])
    source = root / target
    source_bytes = source.read_bytes()
    original = source_bytes.decode("utf-8")
    mutated = original.replace(trial["find"], trial["replace"], 1)
    source_sha = sha16(source_bytes)

    base = {"suite": trial["suite"], "source": str(source),
            "target": str(target).replace("\\", "/"),
            "source_sha": source_sha}
    with tempfile.TemporaryDirectory(prefix="station-immune-") as tmp:
        specimen = Path(tmp) / "specimen"
        shutil.copytree(root, specimen, ignore=_ignore)
        baseline = _run(str(suite["cmd"]), specimen)
        base["baseline"] = baseline
        if baseline["exit"] != 0:
            return {**base, "status": "BASELINE-BROKEN",
                    "mutant": {"exit": None, "tail": "not run"}}
        wound = specimen / target
        wound.write_text(mutated, encoding="utf-8")
        base["mutant_sha"] = sha16(wound.read_bytes())
        # A malformed program can make any suite exit nonzero without its
        # assertions ever observing the intended wound. Syntax failure is a
        # bad experiment, not a killed guard. Python gets a cheap preflight;
        # other file types stay eligible for suites that own their grammar.
        if wound.suffix == ".py":
            syntax = _run(f'"{sys.executable}" -B -m py_compile "{target}"',
                          specimen)
            if syntax["exit"] != 0:
                return {**base, "status": "MUTANT-INVALID", "mutant": syntax}
        # The baseline can create same-second .pyc files. A source mutation of
        # equal byte length may then import yesterday's code and fabricate a
        # SURVIVED result. Generated bytecode is neither specimen nor evidence;
        # remove it before the counterfactual run (joint failure paid live).
        for cache in specimen.rglob("__pycache__"):
            shutil.rmtree(cache)
        mutant = _run(str(suite["cmd"]), specimen)
        return {**base, "mutant": mutant,
                "status": "KILLED" if mutant["exit"] != 0 else "SURVIVED"}


def verify(trial: dict, outcome: dict | None, suites: dict[str, dict]) -> list[str]:
    """Return failures. An old result cannot silently bless edited source."""
    if not outcome:
        return ["never exercised"]
    if outcome.get("status") != "KILLED":
        return ["latest outcome is " + str(outcome.get("status"))]
    suite = suites.get(str(trial.get("suite")))
    if not suite:
        return ["registered suite disappeared"]
    target = Path(str(suite["cwd"])) / str(trial["target"])
    if not target.is_file():
        return ["target disappeared: " + str(target)]
    current = sha16(target.read_bytes())
    if current != outcome.get("source_sha"):
        return [f"STALE source sha={current}, exercised={outcome.get('source_sha')}"]
    if outcome.get("baseline", {}).get("exit") != 0:
        return ["baseline was not green"]
    if outcome.get("mutant", {}).get("exit") in (None, 0):
        return ["mutant did not fail"]
    return []


def report_text(trial: dict, outcome: dict | None) -> str:
    """A compact receipt that says exactly what one counterfactual established."""
    status = "UNEXERCISED" if not outcome else str(outcome.get("status"))
    lines = [
        f"# Counterfactual immunity: {trial['id']}",
        "",
        f"Status: **{status}**",
        "",
        "## Declared lesion",
        f"- Suite: `{trial['suite']}` (registered, not supplied by this trial)",
        f"- Target: `{trial['target']}`",
        f"- Reason: {trial['reason']}",
        f"- Find: `{trial['find']}`",
        f"- Replace: `{trial['replace']}`",
        "",
    ]
    if outcome:
        lines += [
            "## Replay receipt",
            f"- Original sha256: `{outcome.get('source_sha', '?')}`",
            f"- Mutant sha256: `{outcome.get('mutant_sha', '?')}`",
            f"- Baseline exit: `{outcome.get('baseline', {}).get('exit', '?')}`",
            f"- Mutant exit: `{outcome.get('mutant', {}).get('exit', '?')}`",
            "",
        ]
    lines += [
        "## Kill condition",
        trial["kill"],
        "",
        "## Boundary",
        "KILLED means this registered suite rejected this exact single-site lesion in a disposable copy. It does not prove complete coverage, safety, or general causal adequacy.",
        "",
    ]
    return "\n".join(lines)
