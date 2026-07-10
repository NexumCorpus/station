"""Drift check: the temporal witness must not leave futures unobserved.

Armed contracts are valid only before their due date. A resolved contract must
be reviewed. This is not a quality verdict on probabilities; it only keeps the
forecast→observation→action loop from degrading into a cemetery of claims.
"""
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path("E:/station")
sys.path.insert(0, str(HERE))
import forecast  # noqa: E402

ledger = HERE / "forecasts.jsonl"
if not ledger.is_file():
    print("FORECAST-ROT missing ledger")
    sys.exit(1)
rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()]
state = forecast.fold(rows)
if not state:
    print("FORECAST-ROT no contracts")
    sys.exit(1)
today = dt.datetime.now(dt.timezone.utc).date()
bad = []
for ident, row in sorted(state.items()):
    item = row["forecast"]
    try:
        # Validate every frozen field except the intentional passage of time.
        forecast.validate_route(item["route"])
        if item["if_yes"].strip() == item["if_no"].strip():
            raise ValueError("identical action branches")
    except (KeyError, ValueError) as exc:
        bad.append(f"{ident}:schema {exc}")
        continue
    status = forecast.status(row)
    if status == "ARMED" and forecast.date(item["due"]) <= today:
        bad.append(f"{ident}:OVERDUE unresolved since {item['due']}")
    if status == "UNREVIEWED":
        bad.append(f"{ident}:resolution lacks review")

if bad:
    print("FORECAST-ROT " + " | ".join(bad))
    sys.exit(1)
summary = forecast.stats(state)
print(f"CHECK-OK temporal witness: {summary['total']} contracts, "
      f"resolved={summary['resolved']} reviewed={summary['reviewed']}")
