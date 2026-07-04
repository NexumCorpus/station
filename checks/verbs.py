"""Drift check (spiral turn 17): every dispatchable station verb appears in
station.py's __doc__ - the help text is a cold instance's only discovery
surface, and it rots silently as verbs are added. Born catching 11 missing
verbs (fixed in the same commit)."""
import re
import sys
from pathlib import Path

src = Path("E:/station/station.py").read_text(encoding="utf-8")
doc = src.split('"""')[1]                       # module docstring
verbs = set(re.findall(r'\bcmd == "(\w+)"', src)) | {"wake"}
missing = sorted(v for v in verbs
                 if not re.search(rf"station {v}\b", doc))
if missing:
    print(f"DOC-ROT missing from help: {', '.join(missing)}")
    sys.exit(1)
print(f"CHECK-OK {len(verbs)} verbs documented")
