"""Drift check: the executive frontier stays structurally honest.

This does not require an empty horizon; live obligations are the point. It
requires every surfaced obligation to retain an evidence boundary, executor,
authority, and next route, so aggregation never turns into unauthorized agency.
"""
import sys
from pathlib import Path

HERE = Path("E:/station")
sys.path.insert(0, str(HERE))
import horizon  # noqa: E402
import station  # noqa: E402

items = station._horizon_items()
defects = horizon.validate(items)
if defects:
    print("HORIZON-ROT " + " | ".join(defects))
    sys.exit(1)
urgent = sum(1 for item in items if item["rank"] < 100)
print(f"CHECK-OK executive horizon: items={len(items)} urgent={urgent}; "
      "ranking is non-authorizing")
