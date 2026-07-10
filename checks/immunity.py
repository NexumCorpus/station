"""Drift check: a claimed immune guard must still be fresh and discriminating.

Every armed trial must have a latest KILLED outcome, and the target's current
bytes must still match the bytes that were wounded. A normal source edit expires
the result until an operator replays the exact lesion.
"""
import json
import sys
from pathlib import Path

HERE = Path("E:/station")
sys.path.insert(0, str(HERE))
import immunity  # noqa: E402

ledger = HERE / "immunity.jsonl"
if not ledger.is_file():
    print("IMMUNE-ROT missing ledger")
    sys.exit(1)
rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()]
state = immunity.fold(rows)
registry = json.loads((HERE / "station.json").read_text(encoding="utf-8-sig"))
suites = immunity.suite_index(registry)

if not state:
    print("IMMUNE-ROT no trials")
    sys.exit(1)
bad = []
for ident, row in sorted(state.items()):
    problems = immunity.verify(row["trial"], row.get("outcome"), suites)
    if problems:
        bad.append(f"{ident}:{' / '.join(problems)}")

if bad:
    print("IMMUNE-ROT " + " | ".join(bad))
    sys.exit(1)
print(f"CHECK-OK counterfactual immunity: {len(state)} current lesions all KILLED")
