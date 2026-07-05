"""Drift check (spiral turn 58): §17's conversion vital sign must stay
DECIDABLE. §17's own kill clause is that counting performance->possession
conversions fails to yield a continuously-decidable metric — if that ever
happens, §17's promised exit from §15's blocked ratio has failed and the
section is decoration. This re-derives the stock independently of the verb
and asserts it is non-degenerate (every layer readable, stock>0). It does NOT
assert the number is large or rising — only that the metric COMPUTES, which is
the falsifiable property §17 rests on."""
import json
import sys
from pathlib import Path


def count_lines(p: Path) -> int:
    return (sum(1 for ln in p.read_text(encoding="utf-8-sig").splitlines()
                if ln.strip()) if p.is_file() else 0)


drift_n = count_lines(Path("E:/station/drift.jsonl"))
reg = json.loads(Path("E:/station/station.json").read_text(encoding="utf-8-sig"))
witnessed = len(reg.get("witness", []))
certified = 0
claims_p = reg.get("claims", "")
if claims_p and Path(claims_p).is_file():
    d = json.loads(Path(claims_p).read_text(encoding="utf-8-sig"))
    arr = d if isinstance(d, list) else d.get("claims", [])
    certified = len({c.get("id") for c in arr if c.get("verified") is True})

stock = certified + drift_n + witnessed
if certified <= 0 or drift_n <= 0 or witnessed <= 0:
    print(f"CONVERSIONS-UNDECIDABLE certified={certified} drift={drift_n} "
          f"witnessed={witnessed} — a §17 layer went unreadable/empty")
    sys.exit(1)
print(f"CHECK-OK conversion metric decidable: stock={stock} "
      f"(HARD certified={certified} STRUCTURAL drift={drift_n} "
      f"witnessed={witnessed})")
