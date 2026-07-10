"""Drift check: every declared passive-context suture is exact and current."""
import json
import sys
from pathlib import Path

HERE = Path("E:/station")
sys.path.insert(0, str(HERE))
import suture  # noqa: E402

packs = sorted((HERE / "sutures").glob("*.json"))
if not packs:
    print("SUTURE-ROT no declared context sutures")
    sys.exit(1)
bad = []
for path in packs:
    try:
        pack = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        bad.append(f"{path.name}:unreadable:{exc}")
        continue
    result = suture.verify(pack)
    if result["status"] != "SUTURE-OK":
        bad.append(f"{path.stem}:{result['status']}:{';'.join(result.get('problems', []))}")
if bad:
    print("SUTURE-ROT " + " | ".join(bad))
    sys.exit(1)
print(f"CHECK-OK context sutures: {len(packs)} exact passive slices current")
