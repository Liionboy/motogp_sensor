#!/usr/bin/env python3
"""Local logic tests for the MotoGP integration.

Validates parsing and sensor value logic against real API payloads
(loaded from tests/fixtures/ when present).

Usage:  python3 tests/test_logic.py
"""

from __future__ import annotations

import importlib
import json
import sys
import types
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "custom_components"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ha_stubs import stub_homeassistant  # noqa: E402

stub_homeassistant()

from motogp_sensor import helpers  # noqa: E402
from motogp_sensor import sensor as sensor_mod  # noqa: E402
from motogp_sensor.sensor import SENSOR_DESCRIPTIONS  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "✓" if condition else "✗"
    print(f"  {status} {name}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def load_fixture(name: str) -> dict | list | None:
    path = FIXTURES / name
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> int:
    print("== Import check ==")
    for module in (
        "const", "api", "helpers", "coordinator", "entity", "sensor",
        "binary_sensor", "calendar", "switch", "select", "device_trigger",
        "config_flow", "__init__",
    ):
        importlib.import_module(f"motogp_sensor.{module}")
    print("  ✓ toate modulele s-au importat")

    print("\n== Live timing parsing ==")
    live = load_fixture("live.json")
    if live:
        parsed = helpers.parse_live_timing(live)
        check("status mapat", parsed["session_status_name"] in ("Finished", "In Progress", "Not Started"))
        check("riders parsati", len(parsed["riders"]) > 0)
        check("riders sortati dupa pozitie", all(
            parsed["riders"][i]["position"] <= parsed["riders"][i + 1]["position"]
            for i in range(len(parsed["riders"]) - 1)
        ))
        check("rider are nume", bool(parsed["riders"][0].get("surname") or parsed["riders"][0].get("shortname")))
    else:
        print("  (fara fixture live.json — test sintetic)")

    print("\n== Sensor extractors ==")
    class FakeCoord:
        no_spoiler = False
        race_week = True
        live_online = True
        config_entry = type("E", (), {"entry_id": "test"})()
        static = {
            "next_event": None,
            "season": None,
            "rider_standings": [],
            "constructor_standings": [],
            "last_race_results": [],
            "track_weather": {"track": "Dry", "air": "19º", "ground": "34º",
                              "humidity": "46%", "weather": "Partly-Cloudy"},
        }

    coord = FakeCoord()
    coord.static["season"] = {"year": 2026, "id": "x"}
    coord.static["next_event"] = {
        "name": "QATAR AIRWAYS GP OF GREAT BRITAIN", "short_name": "GBR",
        "date_start": "2026-08-07", "date_end": "2026-08-09",
        "circuit": {"name": "Silverstone Circuit"}, "country": {"name": "Great Britain"},
    }
    coord.static["rider_standings"] = [
        {"position": 1, "rider": "A", "constructor": "B", "points": 100},
        {"position": 2, "rider": "C", "constructor": "D", "points": 90},
    ]

    check("next_race value", "QATAR AIRWAYS" in str(sensor_mod._static_value("next_race", coord)))
    check("current_season value", sensor_mod._static_value("current_season", coord) == 2026)
    check("standings value", "2 riders" in str(sensor_mod._static_value("rider_standings", coord)))
    check("standings attrs", sensor_mod._static_attributes("rider_standings", coord).get("count") == 2)
    check("next_race attrs", sensor_mod._static_attributes("next_race", coord).get("circuit") == "Silverstone Circuit")
    check("weather attrs", sensor_mod._static_attributes("track_weather", coord).get("air") == "19º")
    check("weather value", sensor_mod._static_value("track_weather", coord) == "Partly-Cloudy")

    # Days until next race (computed dynamically against today)
    coord.static["next_event"]["date_start"] = "2026-08-28"
    expected_days = (date(2026, 8, 28) - date.today()).days
    got_days = sensor_mod._static_value("next_race_in", coord)
    check("next_race_in value", got_days == max(expected_days, 0), f"got {got_days}, expected {max(expected_days, 0)}")
    check("next_race_in attrs", sensor_mod._static_attributes("next_race_in", coord).get("short_name") == "GBR")
    check("next_race_in unit", SENSOR_DESCRIPTIONS["next_race_in"].unit_of_measurement == "d")

    # Constructor standings aggregation
    aggregated = helpers.aggregate_constructor_standings(coord.static["rider_standings"])
    check("constructor aggregation: 2 echipe", len(aggregated) == 2)
    check("constructor aggregation: suma puncte", aggregated[0]["points"] == 100)
    check("constructor aggregation: pozitii", aggregated[0]["position"] == 1 and aggregated[1]["position"] == 2)
    coord.static["constructor_standings"] = aggregated
    check("constructor standings value", "teams" in str(sensor_mod._static_value("constructor_standings", coord)))

    if live:
        parsed_live = helpers.parse_live_timing(live)
        coord.live_data = parsed_live
        check("session_status value", sensor_mod._live_value("session_status", parsed_live))
        check("leader value", sensor_mod._live_value("leader", parsed_live))
        check("lap count value", sensor_mod._live_value("race_lap_count", parsed_live) is not None)
        check("pit stops value", sensor_mod._live_value("pit_stops", parsed_live) is not None)

    print("\n== No spoiler mode ==")
    if live:
        parsed_live = helpers.parse_live_timing(live)
        from motogp_sensor.sensor import MotogpSensor

        desc = types.SimpleNamespace()
        sensor_obj = MotogpSensor(coord, "MotoGP", desc, "session_status", "live")
        coord.live_data = parsed_live
        coord.no_spoiler = False
        check("live vizibil fara spoiler", sensor_obj.native_value not in (None, "Hidden"))
        coord.no_spoiler = True
        check("live ascuns cu spoiler", sensor_obj.native_value == "Hidden")
        check("attrs marcate", sensor_obj.extra_state_attributes.get("spoiler_mode") is True)
        coord.no_spoiler = False
    else:
        print("  (fara fixture — skip)")

    print("\n== Race week logic ==")
    events = [
        {"name": "THA", "short_name": "THA", "date_start": "2026-02-27", "date_end": "2026-03-01", "test": False},
        {"name": "GBR", "short_name": "GBR", "date_start": "2026-08-07", "date_end": "2026-08-09", "test": False},
        {"name": "AUT", "short_name": "AUT", "date_start": "2026-08-14", "date_end": "2026-08-16", "test": False},
    ]
    cases = [
        ("2026-03-05T12:00", False),  # pauza intre THA si GBR
        ("2026-08-05T12:00", True),   # lunea saptamanii GBR
        ("2026-08-09T12:00", True),   # in plin weekend GBR (cursa duminica)
        ("2026-08-10T12:00", True),   # race week AUT incepe luni
        ("2026-08-11T12:00", True),   # in window-ul AUT
        ("2026-08-17T12:00", False),  # dupa AUT + grace
    ]
    for date_str, expected in cases:
        today = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        nxt = helpers.find_next_event(events, today)
        got = helpers.is_race_week(nxt, today, "monday")
        check(f"race week {date_str} = {expected}", got == expected)

    # HA foloseste datetime timezone-aware (dt_util.utcnow()) — trebuie sa mearga
    today_aware = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)
    nxt = helpers.find_next_event(events, today_aware)
    check("aware datetime: find_next_event", nxt is not None and nxt["short_name"] == "GBR")
    check("aware datetime: race week", helpers.is_race_week(nxt, today_aware, "monday") is True)

    print(f"\n{'=' * 40}")
    if FAILURES:
        print(f"❌ {len(FAILURES)} teste esuate: {FAILURES}")
        return 1
    print("✅ Toate testele au trecut")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
