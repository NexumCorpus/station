"""Temporal-witness primitives (spiral 107).

Forecasts are append-only commitments to a future mechanical observation. They
never execute a caller-provided command: a route is a small, frozen local file
predicate. One resolved row establishes one dated observation, not calibration.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path


REQUIRED = ("id", "question", "p", "due", "route", "if_yes", "if_no")
ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}$")
ROUTE_KEYS = {
    "file_exists": {"kind", "path"},
    "file_contains": {"kind", "path", "needle"},
    "jsonl_count_at_least": {"kind", "path", "where", "at_least"},
}


def sha16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("due must be YYYY-MM-DD") from exc


def _path(value) -> Path:
    path = Path(str(value))
    if not path.is_absolute():
        raise ValueError("route path must be an absolute local path")
    return path


def validate_route(route: dict):
    if not isinstance(route, dict):
        raise ValueError("route must be an object")
    kind = route.get("kind")
    if kind not in ROUTE_KEYS:
        raise ValueError("route kind must be " + ", ".join(sorted(ROUTE_KEYS)))
    if set(route) != ROUTE_KEYS[kind]:
        raise ValueError(f"route keys for {kind} must be exactly "
                         + ", ".join(sorted(ROUTE_KEYS[kind])))
    _path(route["path"])
    if kind == "file_contains" and not isinstance(route["needle"], str):
        raise ValueError("file_contains needle must be a string")
    if kind == "file_contains" and not route["needle"]:
        raise ValueError("file_contains needle must not be empty")
    if kind == "jsonl_count_at_least":
        if not isinstance(route["at_least"], int) or isinstance(route["at_least"], bool) \
                or route["at_least"] < 1:
            raise ValueError("jsonl_count_at_least at_least must be an integer >=1")
        where = route["where"]
        if not isinstance(where, dict):
            raise ValueError("jsonl_count_at_least where must be an object")
        if any(isinstance(v, (dict, list)) for v in where.values()):
            raise ValueError("jsonl_count_at_least where values must be scalar")


def validate_forecast(record: dict, today: dt.date | None = None):
    if not isinstance(record, dict):
        raise ValueError("forecast must be a JSON object")
    missing = [key for key in REQUIRED if record.get(key) in (None, "")]
    if missing:
        raise ValueError("forecast missing " + ", ".join(missing))
    if not ID.fullmatch(str(record["id"])):
        raise ValueError("id must be 3-64 lowercase letters, digits, or hyphens")
    if not isinstance(record["question"], str) or len(record["question"].strip()) < 12:
        raise ValueError("question must be a specific sentence of at least 12 characters")
    p = record["p"]
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not math.isfinite(p) \
            or not 0 <= p <= 1:
        raise ValueError("p must be a finite probability in [0,1]")
    due = date(record["due"])
    if due <= (today or dt.datetime.now(dt.timezone.utc).date()):
        raise ValueError("due must be strictly after today; forecasts cannot be backfilled")
    yes, no = record["if_yes"], record["if_no"]
    if not isinstance(yes, str) or not isinstance(no, str) or not yes.strip() or not no.strip():
        raise ValueError("if_yes and if_no must be non-empty action branches")
    if yes.strip() == no.strip():
        raise ValueError("if_yes and if_no must prescribe different actions")
    validate_route(record["route"])


def evaluate(route: dict) -> dict:
    """Frozen, side-effect-free future observation with hash-carrying evidence."""
    validate_route(route)
    path = _path(route["path"])
    if not path.is_file():
        return {"yes": False, "path": str(path), "source_sha": None,
                "detail": "missing"}
    data = path.read_bytes()
    base = {"path": str(path), "source_sha": sha16(data), "bytes": len(data)}
    if route["kind"] == "file_exists":
        return {"yes": True, **base, "detail": "exists"}
    text = data.decode("utf-8", errors="replace")
    if route["kind"] == "file_contains":
        yes = route["needle"] in text
        return {"yes": yes, **base,
                "detail": "contains" if yes else "needle-absent"}
    rows = []
    malformed = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1
    where = route["where"]
    count = sum(1 for row in rows if isinstance(row, dict)
                and all(row.get(key) == value for key, value in where.items()))
    yes = count >= route["at_least"]
    return {"yes": yes, **base, "detail": f"count={count}/{route['at_least']}",
            "count": count, "malformed": malformed}


def brier(p: float, yes: bool) -> float:
    return round((float(p) - (1.0 if yes else 0.0)) ** 2, 6)


def fold(rows: list[dict]) -> dict[str, dict]:
    """Fold append-only forecast/resolution/review events; never rewrite history."""
    state: dict[str, dict] = {}
    for row in rows:
        ident = row.get("id")
        if not isinstance(ident, str):
            continue
        if row.get("kind") == "forecast":
            state[ident] = {"forecast": row, "resolution": None, "review": None}
        elif row.get("kind") == "resolution" and ident in state:
            state[ident]["resolution"] = row
        elif row.get("kind") == "review" and ident in state:
            state[ident]["review"] = row
    return state


def status(row: dict) -> str:
    if not row.get("resolution"):
        return "ARMED"
    return "REVIEWED" if row.get("review") else "UNREVIEWED"


def stats(state: dict[str, dict]) -> dict:
    rows = list(state.values())
    resolved = [row for row in rows if row.get("resolution")]
    reviewed = [row for row in resolved if row.get("review")]
    losses = [row["resolution"]["brier"] for row in resolved]
    return {"total": len(rows), "resolved": len(resolved), "reviewed": len(reviewed),
            "mean_brier": round(sum(losses) / len(losses), 6) if losses else None}


def report_text(row: dict) -> str:
    forecast, resolution, review = row["forecast"], row.get("resolution"), row.get("review")
    lines = [
        f"# Temporal witness: {forecast['id']}",
        "",
        f"Status: **{status(row)}**",
        "",
        "## Forecast sealed before due",
        f"- Question: {forecast['question']}",
        f"- Probability: `{forecast['p']}`",
        f"- Due: `{forecast['due']}`",
        f"- Route: `{json.dumps(forecast['route'], sort_keys=True)}`",
        "",
        "## Precommitted action branches",
        f"- YES: {forecast['if_yes']}",
        f"- NO: {forecast['if_no']}",
        "",
    ]
    if resolution:
        lines += [
            "## Mechanical resolution",
            f"- Outcome: `{'YES' if resolution['yes'] else 'NO'}`",
            f"- Brier loss: `{resolution['brier']}`",
            f"- Source hash: `{resolution['observation'].get('source_sha')}`",
            f"- Observation: `{resolution['observation'].get('detail')}`",
            "",
        ]
    if review:
        lines += ["## Review", review["note"], ""]
    lines += [
        "## Boundary",
        "This is one sealed forecast and one frozen local observation. It does not establish calibration, causality, demand, or certainty.",
        "",
    ]
    return "\n".join(lines)
