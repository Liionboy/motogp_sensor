"""Pure parsing helpers for MotoGP data.

All functions here are deterministic and side-effect free, so they can be
unit-tested against real API payloads.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .const import SESSION_STATUS_MAP

RACE_WEEK_GRACE = timedelta(hours=3)


def session_status_name(status_id: str | None) -> str:
    """Map a session status id to a human readable name."""
    if not status_id:
        return "Unknown"
    return SESSION_STATUS_MAP.get(status_id, status_id)


def _dict_get(data: Any) -> dict[str, Any]:
    """Safely coerce a value to a dict."""
    return data if isinstance(data, dict) else {}


def parse_live_timing(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the useful bits from a live timing payload."""
    head = _dict_get(payload.get("head"))
    riders_raw = _dict_get(payload.get("rider"))

    riders: list[dict[str, Any]] = []
    for rider in riders_raw.values():
        r = _dict_get(rider)
        pos = r.get("pos")
        if pos is None:
            continue
        riders.append(
            {
                "position": pos,
                "number": r.get("rider_number") or r.get("rider_id"),
                "shortname": r.get("rider_shortname") or "",
                "firstname": r.get("rider_name") or "",
                "surname": r.get("rider_surname") or "",
                "nation": r.get("rider_nation") or "",
                "team": r.get("team_name") or "",
                "bike": r.get("bike_name") or "",
                "lap_time": r.get("lap_time") or "",
                "num_lap": r.get("num_lap"),
                "last_lap_time": r.get("last_lap_time") or "",
                "gap_first": r.get("gap_first") or "",
                "gap_prev": r.get("gap_prev") or "",
                "on_pit": bool(r.get("on_pit")),
                "status_name": r.get("status_name") or "",
            }
        )

    riders.sort(key=lambda x: (x["position"] is None, x["position"]))

    return {
        "session_status_id": head.get("session_status_id") or "N",
        "session_status_name": session_status_name(head.get("session_status_id")),
        "session_shortname": head.get("session_shortname") or "",
        "session_name": head.get("session_name") or "",
        "circuit_name": head.get("circuit_name") or "",
        "event_name": head.get("event_tv_name") or "",
        "event_shortname": head.get("event_shortname") or "",
        "num_laps": head.get("num_laps"),
        "remaining": head.get("remaining") or "0",
        "riders": riders,
    }


def find_next_event(events: list[dict[str, Any]], today: datetime) -> dict[str, Any] | None:
    """Return the next race event (not a test) from a list of events."""
    candidates = [
        e for e in events if isinstance(e, dict) and not e.get("test", False)
    ]
    if not candidates:
        return None
    # The "next" event is the one whose window still contains today, or the
    # earliest event that has not ended yet.
    current = None
    future = None
    for e in candidates:
        start = _parse_date(e.get("date_start"))
        end = _parse_date(e.get("date_end"))
        if start is None or end is None:
            continue
        if start <= today <= end + RACE_WEEK_GRACE:
            current = e
            break
        if end + RACE_WEEK_GRACE >= today and (
            future is None or start < _parse_date(future.get("date_start"))
        ):
            future = e
    return current or future


def is_race_week(
    next_event: dict[str, Any] | None, today: datetime, start_day: str
) -> bool:
    """Return True when today falls inside the race week window."""
    if not next_event:
        return False
    start = _parse_date(next_event.get("date_start"))
    end = _parse_date(next_event.get("date_end"))
    if start is None or end is None:
        return False
    window_start = _week_start_for(start, start_day)
    return window_start <= today <= end + RACE_WEEK_GRACE


def _week_start_for(event_start: datetime, start_day: str) -> datetime:
    """Compute the race week window start for an event start date."""
    weekday_map = {"monday": 0, "saturday": 5, "sunday": 6}
    target = weekday_map.get(start_day, 0)
    days_back = (event_start.weekday() - target) % 7
    window_start = (event_start - timedelta(days=days_back)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return window_start


def events_to_calendar(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert events into calendar entries."""
    entries: list[dict[str, str]] = []
    for e in events:
        if not isinstance(e, dict) or e.get("test", False):
            continue
        start = _parse_date(e.get("date_start"))
        end = _parse_date(e.get("date_end"))
        if start is None or end is None:
            continue
        name = e.get("name") or e.get("sponsored_name") or "MotoGP Event"
        entries.append(
            {
                "summary": name,
                "start": start.date().isoformat(),
                "end": (end.date() + timedelta(days=1)).isoformat(),
            }
        )
    return entries


def parse_standings(classification: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize championship standings entries."""
    result: list[dict[str, Any]] = []
    for entry in classification:
        if not isinstance(entry, dict):
            continue
        rider = _dict_get(entry.get("rider"))
        team = _dict_get(entry.get("team"))
        result.append(
            {
                "position": entry.get("position"),
                "rider": rider.get("full_name") or "",
                "team": team.get("name") or "",
                "constructor": _dict_get(entry.get("constructor")).get("name") or "",
                "points": entry.get("points"),
                "wins": entry.get("race_wins"),
                "podiums": entry.get("podiums"),
            }
        )
    return result


def parse_classification(classification: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a session classification (race results)."""
    result: list[dict[str, Any]] = []
    for entry in classification:
        if not isinstance(entry, dict):
            continue
        rider = _dict_get(entry.get("rider"))
        team = _dict_get(entry.get("team"))
        result.append(
            {
                "position": entry.get("position"),
                "rider": rider.get("full_name") or "",
                "team": team.get("name") or "",
                "constructor": _dict_get(entry.get("constructor")).get("name") or "",
                "time": entry.get("time") or "",
                "gap": entry.get("gap") or "",
                "points": entry.get("points"),
                "status": entry.get("status") or "",
                "total_laps": entry.get("total_laps"),
            }
        )
    return result


def _parse_date(value: Any) -> datetime | None:
    """Parse a date string from the API (YYYY-MM-DD or ISO)."""
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None
