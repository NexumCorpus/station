"""Drift check: every declared xenograft still survives from pinned bytes."""
import sys
from pathlib import Path

HERE = Path("E:/station")
sys.path.insert(0, str(HERE))
import graft  # noqa: E402

manifests = sorted((HERE / "grafts").glob("*/manifest.json"))
if not manifests:
    print("GRAFT-ROT no manifests")
    sys.exit(1)
bad = []
for path in manifests:
    result = graft.run(path)
    if result["status"] != "GRAFT-OK":
        bad.append(f"{path.parent.name}:{result['status']} "
                   + "; ".join(result.get("problems", [])))
if bad:
    print("GRAFT-ROT " + " | ".join(bad))
    sys.exit(1)
print(f"CHECK-OK xenografts: {len(manifests)} transplanted capabilities survive")
