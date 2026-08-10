#!/usr/bin/env python3
"""Local API client tests using recorded real payloads.

Validates that every client method builds the correct URL and parses
responses that match the real Pulselive API shape.

Usage:  python3 tests/test_api.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "custom_components"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ha_stubs import stub_homeassistant  # noqa: E402

stub_homeassistant()

from motogp_sensor.api import MotogpApiClient  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "✓" if condition else "✗"
    print(f"  {status} {name}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


class FakeResponse:
    status = 200

    def __init__(self, payload: object) -> None:
        self._payload = payload

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False

    async def json(self, **kwargs: object) -> object:
        return self._payload


class FakeSession:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def get(self, url: str, **kwargs: object) -> FakeResponse:
        self.calls.append(url)
        payload = self.responses.get(url)
        if payload is None:
            raise AssertionError(f"URL neasteptat: {url}")
        return FakeResponse(payload)


def _load(name: str) -> object:
    with open(FIXTURES / name) as fh:
        return json.load(fh)


async def main() -> int:
    B = "https://api.motogp.pulselive.com/motogp/v1"
    season = "e88b4e43-2209-47aa-8e83-0e0b1cedde6e"
    cat = "e8c110ad-64aa-4e8e-8a86-f2f152f6a942"
    event = "6a16e0cb-ef4b-44b1-92e5-2e958cca0815"
    race = "cdee8aec-30af-403a-86fd-64316afc60b5"

    responses: dict[str, object] = {
        f"{B}/results/seasons": _load("seasons.json"),
        f"{B}/results/categories?seasonUuid={season}": _load("categories.json"),
        f"{B}/results/events?seasonUuid={season}": _load("events.json"),
        f"{B}/results/sessions?eventUuid={event}&categoryUuid={cat}": _load("sessions.json"),
        f"{B}/results/session/{race}/classification": _load("classification.json"),
        f"{B}/results/standings?seasonUuid={season}&categoryUuid={cat}": _load("standings.json"),
        f"{B}/results/standings?seasonUuid={season}&categoryUuid={cat}&type=team": _load("team_standings.json"),
        f"{B}/timing-gateway/livetiming-lite": _load("live.json"),
    }

    session = FakeSession(responses)
    client = MotogpApiClient(session)

    print("== API client ==")
    seasons = await client.async_get_seasons()
    check("seasons", seasons[0]["year"] == 2026 and seasons[0]["current"] is True)

    categories = await client.async_get_categories(season)
    check("categories", str(categories[0]["name"]).startswith("MotoGP"))

    events = await client.async_get_events(season)
    check("events", any(e.get("short_name") == "GBR" for e in events))

    sessions = await client.async_get_sessions(event, cat)
    check("sessions", sessions[0]["type"] == "FP")

    classification = await client.async_get_classification(race)
    check("classification", classification["classification"][0]["position"] == 1)

    standings = await client.async_get_standings(season, cat)
    check("rider standings", standings["classification"][0]["points"] > 0)

    team = await client.async_get_standings(season, cat, team=True)
    check("team standings", team["classification"][0]["points"] > 0)

    live = await client.async_get_live_timing("pulselive")
    check("live timing", "head" in live and "rider" in live)

    check("8 metode, 8 request-uri corecte", len(session.calls) == 8)

    print(f"\n{'=' * 40}")
    if FAILURES:
        print(f"❌ {len(FAILURES)} teste esuate: {FAILURES}")
        return 1
    print("✅ Toate testele au trecut")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
