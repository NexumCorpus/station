"""Drift check (spiral turn 48): the self-model must not silently fall
behind its own change-ledger. ALIEN-ARCHITECTURE.md is the estate's
crystallized self-understanding; spiral.jsonl is the append-only record of
what actually changed. The constitution may LAG (not every turn reshapes the
animal) but not drift far. Assert §16's 'through turn N' is within LAG of the
newest sealed spiral turn."""
import json
import re
import sys
from pathlib import Path

LAG = 12  # turns the constitution may trail before it counts as rotted

doc = Path("E:/station/ALIEN-ARCHITECTURE.md").read_text(encoding="utf-8")
m = re.search(r"through turn (\d+)", doc)
if not m:
    print("NO-SELFMODEL-MARKER: §16 lost its 'through turn N' anchor")
    sys.exit(1)
claimed = int(m.group(1))

turns = [json.loads(ln)["turn"] for ln in
         Path("E:/station/spiral.jsonl").read_text(encoding="utf-8-sig")
         .splitlines() if ln.strip() and '"turn"' in ln]
newest = max(turns) if turns else 0

if newest - claimed > LAG:
    print(f"SELFMODEL-ROT: constitution through turn {claimed}, spiral at "
          f"{newest} (lag {newest - claimed} > {LAG}) — update §16")
    sys.exit(1)
print(f"CHECK-OK self-model through turn {claimed}, spiral at {newest} "
      f"(lag {newest - claimed} <= {LAG})")
