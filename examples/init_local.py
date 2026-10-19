"""Write station.local.json: a minimal registry that points Station at THIS checkout.

station.json is the author's estate (E:/ paths); station.py prefers station.local.json when present,
so a fresh clone can run `wake`, `suites` and `log` against itself without touching any other path.
"""
import json
from pathlib import Path

here = Path(__file__).resolve().parent.parent
root = here.as_posix()
reg = {
    "repos": {"station": root},
    "claims": f"{root}/CLAIMS.json",
    "suites": [{"name": "station-selftest", "cwd": root, "cmd": "python tests_station.py"}],
    "witness": [f"{root}/spine.jsonl"],
    "logs": {"spine": f"{root}/spine.jsonl"},
}
out = here / "station.local.json"
out.write_text(json.dumps(reg, indent=1) + "\n", encoding="utf-8")
print(f"wrote {out}")
