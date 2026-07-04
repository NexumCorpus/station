"""Drift check (spiral turn 34): every dispatchable station verb appears in
CAPSULE.md - the capsule is what dispatched agents read INSTEAD of being
briefed (dense-dispatch doctrine), and it rots faster than help because
nothing forces it through the same commit as a new verb. Born catching a
capsule that documented 6 of 30 verbs."""
import re
import sys
from pathlib import Path

src = Path("E:/station/station.py").read_text(encoding="utf-8")
cap = Path("E:/station/CAPSULE.md").read_text(encoding="utf-8")
verbs = set(re.findall(r'\bcmd == "(\w+)"', src)) | {"wake"}
missing = sorted(v for v in verbs if not re.search(rf"\b{v}\b", cap))
if missing:
    print(f"CAPSULE-ROT missing verbs: {', '.join(missing)}")
    sys.exit(1)
print(f"CHECK-OK capsule covers {len(verbs)} verbs")
