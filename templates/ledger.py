"""TEMPLATE: append-only JSONL ledger — the estate's standard record shape.
Hardened: utf-8-sig reads (BOM survivors), atomic cursor/state writes,
guarded parses. Copy-adapt; do not re-derive."""
from __future__ import annotations

import json
import os
from pathlib import Path


def append(ledger: Path, record: dict) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def read_all(ledger: Path) -> list[dict]:
    if not ledger.is_file():
        return []
    out = []
    for ln in ledger.read_text(encoding="utf-8-sig").splitlines():
        if not ln.strip():
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue                      # a torn tail line is not fatal
    return out


def write_state_atomic(path: Path, obj) -> None:
    """Crash-safe small-state write (cursors, caches): tmp + os.replace."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def read_state(path: Path, default):
    """Corrupt/zero-byte state file -> default, never a crash."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, ValueError):
        return default
