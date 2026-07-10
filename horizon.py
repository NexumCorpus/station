"""Executive-horizon primitives (spiral 117).

This module ranks *accepted obligations*, never projects or desires. Every
frontier item carries its executor tier and remaining authority so a ranked
list cannot be mistaken for permission to act.
"""
from __future__ import annotations

import datetime as dt


REQUIRED = ("id", "source", "kind", "rank", "due", "status", "executor",
            "authority", "evidence", "next")


def _date(value: str) -> dt.date:
    return dt.date.fromisoformat(str(value))


def _item(**kwargs) -> dict:
    missing = [key for key in REQUIRED if kwargs.get(key) in (None, "")]
    if missing:
        raise ValueError("horizon item missing " + ", ".join(missing))
    return kwargs


def _wait_rank(due: str, today: dt.date) -> int:
    return 100 + max(0, min(90, (_date(due) - today).days))


def _forecast_state(row: dict) -> str:
    if not row.get("resolution"):
        return "ARMED"
    return "REVIEWED" if row.get("review") else "UNREVIEWED"


def collect(today: str, preregs: dict, market: dict, forecasts: dict,
            immune_rot: list[dict] | None = None) -> list[dict]:
    """Create a deterministic, non-executing decision frontier.

    Priority is cost of delay, not value: integrity > overdue observation >
    overdue scoring > external deadline > waiting. Inputs are already-folded
    ledgers supplied by station.py, keeping this module pure and testable.
    """
    now = _date(today)
    items: list[dict] = []
    for rot in immune_rot or []:
        ident = str(rot.get("id", "?"))
        problems = "; ".join(str(p) for p in rot.get("problems", [])) or "verification failed"
        items.append(_item(
            id=ident, source="immunity", kind="INTEGRITY-ROT", rank=0,
            due=today, status="ROT", executor="deterministic registered suite",
            authority="registered suite plus current source hash",
            evidence=problems, next=f"station immune run {ident}"))
    for ident, row in preregs.items():
        if row.get("status") != "armed":
            continue
        due = str(row.get("due", "9999-12-31"))
        overdue = _date(due) <= now
        items.append(_item(
            id=ident, source="prereg", kind="PREREG-DUE" if overdue else "PREREG-WAIT",
            rank=30 if overdue else _wait_rank(due, now), due=due,
            status="DUE" if overdue else "WAIT",
            executor="deep evidence audit + human ratification" if overdue else "wait",
            authority="the preregistered scorer and human ratification",
            evidence=str(row.get("score_hint") or row.get("rule") or "named scorer"),
            next=(f"station preregs score {ident} PASS|FAIL|NARROWED <evidence>"
                  if overdue else f"WAIT until {due}; then score {ident}")))
    for ident, row in market.items():
        if row.get("status") != "armed":
            continue
        due = str(row.get("due", "9999-12-31"))
        overdue = _date(due) <= now
        items.append(_item(
            id=ident, source="market", kind="MARKET-DUE" if overdue else "MARKET-WAIT",
            rank=40 if overdue else _wait_rank(due, now), due=due,
            status="DUE" if overdue else "WAIT", executor="human + external evidence",
            authority="qualified external signal; local receipt for PAID",
            evidence=str(row.get("test") or row.get("kill") or "external test"),
            next=(f"station market score {ident} INTEREST|PAID|REJECTED|NARROWED <evidence>"
                  if overdue else f"WAIT until {due}; then score {ident}")))
    for ident, row in forecasts.items():
        forecast = row["forecast"]
        due, state = str(forecast["due"]), _forecast_state(row)
        if state == "UNREVIEWED":
            items.append(_item(
                id=ident, source="forecast", kind="FORECAST-REVIEW", rank=25,
                due=due, status="REVIEW", executor="human direction",
                authority="observed branch or explicit DECLINE",
                evidence=f"resolved {'YES' if row['resolution']['yes'] else 'NO'}; brier={row['resolution']['brier']}",
                next=f"station forecast review {ident} YES|NO|DECLINE <note>"))
        elif state == "ARMED":
            overdue = _date(due) <= now
            items.append(_item(
                id=ident, source="forecast",
                kind="FORECAST-DUE" if overdue else "FORECAST-WAIT",
                rank=20 if overdue else _wait_rank(due, now), due=due,
                status="DUE" if overdue else "WAIT",
                executor="deterministic observation then human review" if overdue else "wait",
                authority="station clock + frozen local route",
                evidence=str(forecast["question"]),
                next=(f"station forecast resolve {ident}" if overdue
                      else f"WAIT until {due}; then resolve {ident}")))
    return sorted(items, key=lambda item: (item["rank"], item["due"], item["source"], item["id"]))


def validate(items: list[dict]) -> list[str]:
    """Return structural defects; empty is a trustworthy frontier shape."""
    defects = []
    for item in items:
        missing = [key for key in REQUIRED if item.get(key) in (None, "")]
        if missing:
            defects.append(f"{item.get('id', '?')}:missing {','.join(missing)}")
        if item.get("executor") == "human + external evidence" and "external" not in item.get("authority", ""):
            defects.append(f"{item.get('id', '?')}:market authority drift")
        if item.get("kind") == "INTEGRITY-ROT" and item.get("rank") != 0:
            defects.append(f"{item.get('id', '?')}:integrity rank drift")
    return defects


def render(items: list[dict]) -> str:
    urgent = sum(1 for item in items if item["rank"] < 100)
    lines = [f"HORIZON items={len(items)} urgent={urgent} | decision frontier, not authorization"]
    for item in items:
        lines.append(f"P{item['rank']:03d} {item['kind']:<16} {item['source']}/{item['id']} "
                     f"due={item['due']} status={item['status']}")
        lines.append(f"  executor: {item['executor']} | authority: {item['authority']}")
        lines.append(f"  evidence: {item['evidence'][:180]}")
        lines.append(f"  next: {item['next']}")
    return "\n".join(lines)
