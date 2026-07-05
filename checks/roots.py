"""Drift check (spiral turn 60): the trust floor must not silently shift.
ROOTS.md names the estate's Tier-1 frozen-trusted roots — artifacts audited
ONCE and trusted thereafter (the trusted scorer, the auditor-of-auditors).
They cannot be re-derived cheaply, so the honest guard is change detection: if
a frozen root's bytes change, its one-time audit is STALE and the trust is no
longer earned. This recomputes each pinned root's sha16 and fails on any
mismatch or missing root — a changed root must be re-audited and re-pinned in
ROOTS.md, not silently trusted. (Tier-2 roots ride running auditors; the Tier-3
seed — the non-fabrication norm — cannot be pinned and is named, not checked:
that residual is the point, not a gap this check can close.)"""
import hashlib
import re
import sys
from pathlib import Path

ROOTS = Path("E:/station/ROOTS.md")
if not ROOTS.is_file():
    print("NO-ROOTS-MANIFEST: ROOTS.md is gone — the trust floor is unnamed")
    sys.exit(1)

text = ROOTS.read_text(encoding="utf-8")
# Tier-1 rows: | <sha16> | <path> | ...
rows = re.findall(r"\|\s*([0-9a-f]{16})\s*\|\s*(E:/[^\s|]+)\s*\|", text)
if not rows:
    print("ROOTS-EMPTY: no Tier-1 frozen roots parsed from ROOTS.md — the "
          "floor names nothing (a trust floor with no roots is not humility, "
          "it is an unaudited claim of zero trust)")
    sys.exit(1)

bad = []
for pinned, path in rows:
    p = Path(path)
    if not p.is_file():
        bad.append(f"{path} MISSING")
        continue
    live = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    if live != pinned:
        bad.append(f"{path} CHANGED {pinned}->{live} (re-audit + re-pin)")

if bad:
    print("ROOTS-STALE: " + " | ".join(bad))
    sys.exit(1)
print(f"CHECK-OK trust floor intact: {len(rows)} frozen roots match their "
      f"one-time audit; the un-pinnable seed (non-fabrication norm) named in Tier 3")
