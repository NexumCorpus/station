"""Drift check: the pulse must leave a PULSE note within 5h (3h schedule
+ 2h grace). Two beats died silently with 0xC000013A on 2026-07-04 and
nothing in the estate said so — a heart that can stop silently isn't a
heart. FAIL here = investigate schtasks StationPulse Last Result first."""
import json
import pathlib
import time

last = None
for ln in pathlib.Path("E:/station/spine.jsonl").read_text(
        encoding="utf-8").splitlines():
    try:
        r = json.loads(ln)
    except json.JSONDecodeError:
        continue
    if r.get("kind") == "note" and str(r.get("body", "")).startswith("PULSE"):
        last = r["t"]
if last is None:
    print("NO-PULSE-EVER")
else:
    t = time.mktime(time.strptime(last[:19], "%Y-%m-%dT%H:%M:%S"))
    t -= time.timezone if not time.daylight else time.altzone
    age_h = (time.time() - t) / 3600
    print("OK" if age_h <= 5 else f"FLATLINE {age_h:.1f}h since last beat")
