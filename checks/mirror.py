"""Drift check (spiral turn 18): the continuity mirror is restore-worthy.
For append-only ledgers, the mirror must be a PREFIX of the source — that
single property proves intact lineage while tolerating honest lag between
backups. A diverged mirror (mirror line absent from source head) means the
restore path would resurrect a corrupted or foreign history: alarm, never
tolerate. Also: the mirror must not be empty while the source is not."""
import sys
from pathlib import Path

PAIRS = [
    ("E:/station/spine.jsonl", "E:/continuity/station/spine.jsonl"),
    ("E:/station/grimoire.jsonl", "E:/continuity/station/grimoire.jsonl"),
    ("E:/station/spiral.jsonl", "E:/continuity/station/spiral.jsonl"),
    ("E:/station/market.jsonl", "E:/continuity/station/market.jsonl"),
    ("E:/atlas-station/CLAIMS.json", "E:/continuity/atlas/CLAIMS.json"),
]
bad = []
for src_p, mir_p in PAIRS:
    src, mir = Path(src_p), Path(mir_p)
    if not src.is_file():
        continue                              # unborn ledger: no history to mirror
    if not mir.is_file():
        bad.append(f"{mir.name}:MISSING")
        continue
    s = src.read_text(encoding="utf-8-sig").splitlines()
    m = mir.read_text(encoding="utf-8-sig").splitlines()
    if src_p.endswith(".jsonl"):
        if not m:
            bad.append(f"{mir.name}:EMPTY")
        elif s[:len(m)] != m:
            bad.append(f"{mir.name}:DIVERGED")
    elif not m:                             # non-jsonl: existence + non-empty
        bad.append(f"{mir.name}:EMPTY")
print("CHECK-OK all mirrors prefix-intact" if not bad
      else "MIRROR-ROT " + ",".join(bad))
sys.exit(1 if bad else 0)
