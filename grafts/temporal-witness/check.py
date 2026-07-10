"""The temporal witness must run from this stripped graft, not E:/station."""
from pathlib import Path

import forecast

here = Path.cwd().resolve()
assert Path(forecast.__file__).resolve().parent == here, forecast.__file__
route = {
    "kind": "jsonl_count_at_least",
    "path": str(here / "signal.jsonl"),
    "where": {"kind": "signal"},
    "at_least": 1,
}
forecast.validate_forecast({
    "id": "grafted-future", "question": "Will the grafted witness observe its local signal?",
    "p": 0.8, "due": "2026-08-10", "route": route,
    "if_yes": "keep the pure module portable", "if_no": "externalize its hidden dependency",
}, forecast.date("2026-07-10"))
observed = forecast.evaluate(route)
assert observed["yes"] is True, observed
assert forecast.brier(0.8, observed["yes"]) == 0.04
print("XENOGRAFT-TEMPORAL-WITNESS-OK")
