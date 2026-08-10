"""Data coordinator for the MotoGP Sensor integration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import MotogpApiClient, MotogpApiError
from .const import (
    DOMAIN,
    EVENT_LIVE_TIMING_OFFLINE,
    EVENT_LIVE_TIMING_ONLINE,
    EVENT_MOTOGP,
    EVENT_RACE_WEEK_ENDED,
    EVENT_RACE_WEEK_STARTED,
    EVENT_SESSION_CANCELLED,
    EVENT_SESSION_DELAYED,
    EVENT_SESSION_FINISHED,
    EVENT_SESSION_IN_PROGRESS,
    EVENT_SESSION_RED_FLAG,
    LIVE_POLLING_ACTIVE,
    LIVE_POLLING_IDLE,
    LIVE_SOURCE_AUTO,
    LIVE_SOURCE_OFFICIAL,
    LIVE_SOURCE_PULSELIVE,
    STATIC_REFRESH_INTERVAL,
)
from .helpers import (
    aggregate_constructor_standings,
    events_to_calendar,
    find_next_event,
    is_race_week,
    parse_classification,
    parse_live_timing,
    parse_standings,
)

_LOGGER = logging.getLogger(__name__)

# Session types, best race first (used to pick "the race" of a weekend).
RACE_SESSION_PRIORITY = ("RAC", "SPR")


class MotogpCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and hold MotoGP live and static data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MotogpApiClient,
        live_source: str,
        race_week_start_day: str,
        enabled_sensors: list[str],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=LIVE_POLLING_IDLE,
        )
        self.api = api
        self.live_source = live_source
        self.race_week_start_day = race_week_start_day
        self.enabled_sensors = set(enabled_sensors)
        self.device_id: str | None = None
        self.no_spoiler = False
        self._race_week = False

        self._last_static_refresh: datetime | None = None
        self._prev_live_online: bool | None = None
        self._prev_session_status: str | None = None
        self._prev_race_week: bool | None = None

        self.static: dict[str, Any] = {
            "season": None,
            "events": [],
            "calendar": [],
            "next_event": None,
            "rider_standings": [],
            "constructor_standings": [],
            "last_race_results": [],
            "track_weather": None,
        }

    # ── Public helpers for entities ─────────────────────────────────────────
    @property
    def live_data(self) -> dict[str, Any] | None:
        """Return the parsed live timing payload (or None)."""
        data = self.data.get("live") if self.data else None
        return data

    @property
    def live_online(self) -> bool:
        """True when a live timing feed is currently reachable."""
        return bool(self.data and self.data.get("live_online"))

    @property
    def session_in_progress(self) -> bool:
        """True when the current session is in progress."""
        live = self.live_data
        if not live:
            return False
        return live.get("session_status_id") == "I"

    @property
    def race_week(self) -> bool:
        """True when we are inside the current race week window."""
        return self._race_week

    def _fire_event(self, event_type: str) -> None:
        """Fire a MotoGP device event on the HA bus."""
        if not self.device_id:
            return
        self.hass.bus.async_fire(
            EVENT_MOTOGP,
            {"device_id": self.device_id, "type": event_type},
        )
        _LOGGER.debug("Fired MotoGP event: %s", event_type)

    # ── Update loop ─────────────────────────────────────────────────────────
    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data."""
        now = dt_util.utcnow()

        # 1. Live timing (with source fallback)
        live: dict[str, Any] | None = None
        live_online = False
        try:
            payload = await self.api.async_get_live_timing(self.live_source)
            live = parse_live_timing(payload)
            live_online = True
        except MotogpApiError as err:
            _LOGGER.debug("Live timing failed on %s: %s", self.live_source, err)
            if self.live_source in (LIVE_SOURCE_AUTO, LIVE_SOURCE_OFFICIAL):
                try:
                    payload = await self.api.async_get_live_timing(LIVE_SOURCE_PULSELIVE)
                    live = parse_live_timing(payload)
                    live_online = True
                except MotogpApiError as err2:
                    _LOGGER.debug("Live timing fallback failed: %s", err2)

        # 2. Static data refresh (throttled)
        if (
            self._last_static_refresh is None
            or now - self._last_static_refresh >= STATIC_REFRESH_INTERVAL
        ):
            try:
                await self._async_refresh_static(now)
                self._last_static_refresh = now
            except MotogpApiError as err:
                _LOGGER.warning("Static data refresh failed: %s", err)

        # 3. Detect state transitions and fire events
        self._detect_transitions(live, live_online, now)

        # 4. Adapt polling interval to session activity
        active = live_online and live is not None and live.get("session_status_id") == "I"
        self.update_interval = LIVE_POLLING_ACTIVE if active else LIVE_POLLING_IDLE

        return {"live": live, "live_online": live_online}

    # ── Static data ─────────────────────────────────────────────────────────
    async def _async_refresh_static(self, now: datetime) -> None:
        """Fetch season, events, standings and last race results."""
        # Season
        seasons = await self.api.async_get_seasons()
        season = next((s for s in seasons if s.get("current")), seasons[0] if seasons else None)
        season_uuid = season.get("id") if season else None
        self.static["season"] = season

        if not season_uuid:
            return

        # Category (MotoGP class)
        categories = await self.api.async_get_categories(season_uuid)
        category = next(
            (c for c in categories if str(c.get("name", "")).startswith("MotoGP")),
            categories[0] if categories else None,
        )
        category_uuid = category.get("id") if category else None

        # Events + calendar
        events = await self.api.async_get_events(season_uuid)
        events = [e for e in events if isinstance(e, dict)]
        self.static["events"] = events
        self.static["calendar"] = events_to_calendar(events)
        self.static["next_event"] = find_next_event(events, now)

        if category_uuid:
            # Standings (rider + aggregated constructor)
            try:
                standings = await self.api.async_get_standings(season_uuid, category_uuid)
                rider_standings = parse_standings(standings.get("classification", []))
            except MotogpApiError as err:
                _LOGGER.debug("Rider standings failed: %s", err)
                rider_standings = []
            self.static["rider_standings"] = rider_standings
            self.static["constructor_standings"] = aggregate_constructor_standings(
                rider_standings
            )

            # Last race results + track weather for the relevant events
            await self._async_refresh_event_details(events, category_uuid, now)

    async def _async_refresh_event_details(
        self, events: list[dict[str, Any]], category_uuid: str, now: datetime
    ) -> None:
        """Fetch sessions/classification for the relevant events."""
        # Weather: from the current/next event's sessions
        target = self.static.get("next_event")
        if target is not None:
            try:
                sessions = await self.api.async_get_sessions(
                    target["id"], category_uuid
                )
            except MotogpApiError as err:
                _LOGGER.debug("Sessions failed: %s", err)
                sessions = []

            weather = None
            for sess in sessions:
                cond = sess.get("condition")
                if isinstance(cond, dict) and cond:
                    weather = {
                        "track": cond.get("track") or "",
                        "air": cond.get("air") or "",
                        "ground": cond.get("ground") or "",
                        "humidity": cond.get("humidity") or "",
                        "weather": cond.get("weather") or "",
                    }
            self.static["track_weather"] = weather

        # Last race results: from the most recent finished event
        past = [
            e
            for e in events
            if _event_end(e) is not None and _event_end(e) < now
        ]
        past.sort(key=lambda e: _event_end(e) or now, reverse=True)
        last_event = past[0] if past else None
        if last_event is None:
            self.static["last_race_results"] = []
            return

        try:
            sessions = await self.api.async_get_sessions(
                last_event["id"], category_uuid
            )
        except MotogpApiError as err:
            _LOGGER.debug("Sessions failed: %s", err)
            self.static["last_race_results"] = []
            return

        # Pick the best session type (RAC > SPR)
        race = None
        for s_type in RACE_SESSION_PRIORITY:
            race = next(
                (
                    s
                    for s in sessions
                    if s.get("type") == s_type and s.get("status") == "FINISHED"
                ),
                None,
            )
            if race:
                break
        if race:
            try:
                classification = await self.api.async_get_classification(race["id"])
                self.static["last_race_results"] = parse_classification(
                    classification.get("classification", [])
                )
            except MotogpApiError as err:
                _LOGGER.debug("Classification failed: %s", err)
                self.static["last_race_results"] = []
        else:
            self.static["last_race_results"] = []

    # ── Transitions / device events ─────────────────────────────────────────
    def _detect_transitions(
        self,
        live: dict[str, Any] | None,
        live_online: bool,
        now: datetime,
    ) -> None:
        """Fire events when the state changes between updates."""

        # Live timing online/offline
        if self._prev_live_online is not None:
            if live_online and not self._prev_live_online:
                self._fire_event(EVENT_LIVE_TIMING_ONLINE)
            elif not live_online and self._prev_live_online:
                self._fire_event(EVENT_LIVE_TIMING_OFFLINE)
        self._prev_live_online = live_online

        # Session status changes
        if live is not None:
            status_id = live.get("session_status_id")
            if status_id != self._prev_session_status:
                if status_id == "I":
                    self._fire_event(EVENT_SESSION_IN_PROGRESS)
                elif status_id == "F":
                    self._fire_event(EVENT_SESSION_FINISHED)
                elif status_id == "R":
                    self._fire_event(EVENT_SESSION_RED_FLAG)
                elif status_id == "C":
                    self._fire_event(EVENT_SESSION_CANCELLED)
                elif status_id == "D":
                    self._fire_event(EVENT_SESSION_DELAYED)
                self._prev_session_status = status_id
        elif self._prev_session_status is not None:
            self._prev_session_status = None

        # Race week start/end
        race_week = is_race_week(
            self.static.get("next_event"), now, self.race_week_start_day
        )
        self._race_week = race_week
        if self._prev_race_week is not None:
            if race_week and not self._prev_race_week:
                self._fire_event(EVENT_RACE_WEEK_STARTED)
            elif not race_week and self._prev_race_week:
                self._fire_event(EVENT_RACE_WEEK_ENDED)
        self._prev_race_week = race_week
