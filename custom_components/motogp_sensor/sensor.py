"""Sensor platform for the MotoGP Sensor integration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_NAME,
    DOMAIN,
    LIVE_SENSORS,
    SENSOR_CONSTRUCTOR_STANDINGS,
    SENSOR_CURRENT_SEASON,
    SENSOR_CURRENT_SESSION,
    SENSOR_FASTEST_LAP,
    SENSOR_LAST_RACE_RESULTS,
    SENSOR_LEADER,
    SENSOR_NEXT_RACE,
    SENSOR_NEXT_RACE_IN,
    SENSOR_PIT_STOPS,
    SENSOR_RACE_LAP_COUNT,
    SENSOR_RIDER_POSITIONS,
    SENSOR_RIDER_STANDINGS,
    SENSOR_SESSION_STATUS,
    SENSOR_SESSION_TIME_REMAINING,
    SENSOR_TOP_THREE,
    SENSOR_TRACK_WEATHER,
)
from .coordinator import MotogpCoordinator
from .entity import MotogpEntity
from .helpers import parse_api_date

LIVE = "live"
STATIC = "static"

SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    SENSOR_SESSION_STATUS: SensorEntityDescription(
        key=SENSOR_SESSION_STATUS,
        translation_key=SENSOR_SESSION_STATUS,
        icon="mdi:flag-checkered",
    ),
    SENSOR_CURRENT_SESSION: SensorEntityDescription(
        key=SENSOR_CURRENT_SESSION,
        translation_key=SENSOR_CURRENT_SESSION,
        icon="mdi:motorbike",
    ),
    SENSOR_RACE_LAP_COUNT: SensorEntityDescription(
        key=SENSOR_RACE_LAP_COUNT,
        translation_key=SENSOR_RACE_LAP_COUNT,
        icon="mdi:counter",
    ),
    SENSOR_RIDER_POSITIONS: SensorEntityDescription(
        key=SENSOR_RIDER_POSITIONS,
        translation_key=SENSOR_RIDER_POSITIONS,
        icon="mdi:format-list-numbered",
    ),
    SENSOR_TOP_THREE: SensorEntityDescription(
        key=SENSOR_TOP_THREE,
        translation_key=SENSOR_TOP_THREE,
        icon="mdi:podium",
    ),
    SENSOR_LEADER: SensorEntityDescription(
        key=SENSOR_LEADER,
        translation_key=SENSOR_LEADER,
        icon="mdi:medal",
    ),
    SENSOR_FASTEST_LAP: SensorEntityDescription(
        key=SENSOR_FASTEST_LAP,
        translation_key=SENSOR_FASTEST_LAP,
        icon="mdi:av-timer",
    ),
    SENSOR_SESSION_TIME_REMAINING: SensorEntityDescription(
        key=SENSOR_SESSION_TIME_REMAINING,
        translation_key=SENSOR_SESSION_TIME_REMAINING,
        icon="mdi:timer-outline",
    ),
    SENSOR_TRACK_WEATHER: SensorEntityDescription(
        key=SENSOR_TRACK_WEATHER,
        translation_key=SENSOR_TRACK_WEATHER,
        icon="mdi:weather-partly-cloudy",
    ),
    SENSOR_PIT_STOPS: SensorEntityDescription(
        key=SENSOR_PIT_STOPS,
        translation_key=SENSOR_PIT_STOPS,
        icon="mdi:garage-variant",
    ),
    SENSOR_NEXT_RACE: SensorEntityDescription(
        key=SENSOR_NEXT_RACE,
        translation_key=SENSOR_NEXT_RACE,
        icon="mdi:calendar-star",
    ),
    SENSOR_NEXT_RACE_IN: SensorEntityDescription(
        key=SENSOR_NEXT_RACE_IN,
        translation_key=SENSOR_NEXT_RACE_IN,
        icon="mdi:calendar-clock",
        unit_of_measurement="d",
    ),
    SENSOR_CURRENT_SEASON: SensorEntityDescription(
        key=SENSOR_CURRENT_SEASON,
        translation_key=SENSOR_CURRENT_SEASON,
        icon="mdi:calendar",
    ),
    SENSOR_RIDER_STANDINGS: SensorEntityDescription(
        key=SENSOR_RIDER_STANDINGS,
        translation_key=SENSOR_RIDER_STANDINGS,
        icon="mdi:podium",
    ),
    SENSOR_CONSTRUCTOR_STANDINGS: SensorEntityDescription(
        key=SENSOR_CONSTRUCTOR_STANDINGS,
        translation_key=SENSOR_CONSTRUCTOR_STANDINGS,
        icon="mdi:garage",
    ),
    SENSOR_LAST_RACE_RESULTS: SensorEntityDescription(
        key=SENSOR_LAST_RACE_RESULTS,
        translation_key=SENSOR_LAST_RACE_RESULTS,
        icon="mdi:flag-checkered",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MotoGP sensors from a config entry."""
    coordinator: MotogpCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_name = entry.data.get(CONF_DEVICE_NAME, "MotoGP")

    entities: list[MotogpSensor] = []
    for key, description in SENSOR_DESCRIPTIONS.items():
        if key not in coordinator.enabled_sensors:
            continue
        sensor_type = LIVE if key in LIVE_SENSORS else STATIC
        entities.append(
            MotogpSensor(coordinator, device_name, description, key, sensor_type)
        )
    async_add_entities(entities)


class MotogpSensor(MotogpEntity, SensorEntity):
    """A MotoGP sensor."""

    def __init__(
        self,
        coordinator: MotogpCoordinator,
        device_name: str,
        description: SensorEntityDescription,
        sensor_key: str,
        sensor_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_name)
        self.entity_description = description
        self._key = sensor_key
        self._type = sensor_type
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{sensor_key}"

    @property
    def native_value(self) -> Any:
        """Return the sensor state."""
        if self._type == LIVE:
            if self.coordinator.no_spoiler:
                return "Hidden"
            live = self.coordinator.live_data
            if not live:
                return None
            return _live_value(self._key, live)
        return _static_value(self._key, self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        if self._type == LIVE:
            if self.coordinator.no_spoiler:
                return {"spoiler_mode": True}
            live = self.coordinator.live_data
            if not live:
                return None
            return _live_attributes(self._key, live)
        return _static_attributes(self._key, self.coordinator)


# ── Live value/attribute extractors ─────────────────────────────────────────

def _riders_sorted(live: dict[str, Any]) -> list[dict[str, Any]]:
    return live.get("riders", [])


def _live_value(key: str, live: dict[str, Any]) -> Any:
    """Compute the state value for a live sensor."""
    riders = _riders_sorted(live)
    if key == SENSOR_SESSION_STATUS:
        return live.get("session_status_name") or "Unknown"
    if key == SENSOR_CURRENT_SESSION:
        return live.get("session_shortname") or "None"
    if key == SENSOR_RACE_LAP_COUNT:
        laps = [r.get("num_lap") for r in riders if r.get("num_lap") is not None]
        return max(laps) if laps else 0
    if key == SENSOR_RIDER_POSITIONS:
        if not riders:
            return "No riders"
        top = ", ".join(
            f"{r['position']}. {r['surname']}" for r in riders[:3]
        )
        return f"{top} ({len(riders)} riders)"
    if key == SENSOR_TOP_THREE:
        if not riders:
            return "No riders"
        return ", ".join(f"{r['position']}. {r['surname']}" for r in riders[:3])
    if key == SENSOR_LEADER:
        if not riders:
            return "No leader"
        return riders[0].get("surname") or riders[0].get("shortname") or "Unknown"
    if key == SENSOR_FASTEST_LAP:
        laps = [
            (r.get("last_lap_time") or "", r)
            for r in riders
            if r.get("last_lap_time")
        ]
        if not laps:
            return "No data"
        return min(laps, key=lambda x: _lap_seconds(x[0]))[0]
    if key == SENSOR_SESSION_TIME_REMAINING:
        return live.get("remaining") or "0"
    if key == SENSOR_PIT_STOPS:
        return len([r for r in riders if r.get("on_pit")])
    return None


def _live_attributes(key: str, live: dict[str, Any]) -> dict[str, Any]:
    """Compute extra attributes for a live sensor."""
    riders = _riders_sorted(live)
    attrs: dict[str, Any] = {
        "session_shortname": live.get("session_shortname"),
        "session_status_id": live.get("session_status_id"),
        "circuit": live.get("circuit_name"),
        "event": live.get("event_name"),
    }
    if key == SENSOR_SESSION_STATUS:
        attrs["session_name"] = live.get("session_name")
        attrs["event_shortname"] = live.get("event_shortname")
    elif key == SENSOR_RACE_LAP_COUNT:
        attrs["num_laps"] = live.get("num_laps")
        attrs["riders_on_track"] = len(riders)
    elif key == SENSOR_RIDER_POSITIONS:
        attrs["riders"] = riders
        attrs["count"] = len(riders)
    elif key == SENSOR_TOP_THREE:
        attrs["podium"] = riders[:3]
    elif key == SENSOR_LEADER:
        attrs["leader_details"] = riders[0] if riders else None
        attrs["gap_to_leader"] = riders[1].get("gap_first") if len(riders) > 1 else None
    elif key == SENSOR_FASTEST_LAP:
        laps = [
            (r.get("last_lap_time") or "", r)
            for r in riders
            if r.get("last_lap_time")
        ]
        if laps:
            _, best = min(laps, key=lambda x: _lap_seconds(x[0]))
            attrs["fastest_rider"] = best.get("surname")
            attrs["fastest_rider_number"] = best.get("number")
    elif key == SENSOR_SESSION_TIME_REMAINING:
        attrs["session_duration"] = live.get("num_laps")
    elif key == SENSOR_PIT_STOPS:
        attrs["riders_in_pit"] = [
            r.get("surname") for r in riders if r.get("on_pit")
        ]
    return attrs


def _lap_seconds(lap_time: str) -> float:
    """Convert a lap time like '1'28.634' or '39:45.930' to seconds."""
    try:
        if ":" in lap_time:
            parts = lap_time.replace("'", ":").split(":")
            minutes = int(parts[0])
            seconds = float(parts[1]) if len(parts) > 1 else 0.0
            return minutes * 60 + seconds
        if "'" in lap_time:
            minutes, rest = lap_time.split("'")
            return int(minutes) * 60 + float(rest)
        return float(lap_time)
    except (ValueError, IndexError):
        return float("inf")


# ── Static value/attribute extractors ───────────────────────────────────────

def _static_value(key: str, coordinator: MotogpCoordinator) -> Any:
    """Compute the state value for a static sensor."""
    static = coordinator.static
    if key == SENSOR_NEXT_RACE:
        event = static.get("next_event")
        return event.get("name") if event else "No race scheduled"
    if key == SENSOR_NEXT_RACE_IN:
        event = static.get("next_event")
        if not event:
            return None
        start = parse_api_date(event.get("date_start"))
        if start is None:
            return None
        days = (start.date() - datetime.now(timezone.utc).date()).days
        return max(days, 0)
    if key == SENSOR_CURRENT_SEASON:
        season = static.get("season")
        return season.get("year") if season else None
    if key == SENSOR_RIDER_STANDINGS:
        standings = static.get("rider_standings", [])
        if not standings:
            return "No standings"
        top = ", ".join(
            f"{s['position']}. {s['rider']}" for s in standings[:3]
        )
        return f"{top} ({len(standings)} riders)"
    if key == SENSOR_CONSTRUCTOR_STANDINGS:
        standings = static.get("constructor_standings", [])
        if not standings:
            return "No standings"
        top = ", ".join(
            f"{s['position']}. {s['team']}" for s in standings[:3]
        )
        return f"{top} ({len(standings)} teams)"
    if key == SENSOR_LAST_RACE_RESULTS:
        results = static.get("last_race_results", [])
        if not results:
            return "No results"
        top = ", ".join(
            f"{r['position']}. {r['rider']}" for r in results[:3]
        )
        return f"{top} ({len(results)} riders)"
    return None


def _static_attributes(key: str, coordinator: MotogpCoordinator) -> dict[str, Any]:
    """Compute extra attributes for a static sensor."""
    static = coordinator.static
    attrs: dict[str, Any] = {}
    if key == SENSOR_NEXT_RACE:
        event = static.get("next_event")
        if event:
            attrs["short_name"] = event.get("short_name")
            attrs["date_start"] = event.get("date_start")
            attrs["date_end"] = event.get("date_end")
            attrs["circuit"] = _event_circuit(event)
            attrs["country"] = _event_country(event)
            attrs["sponsored_name"] = event.get("sponsored_name")
    elif key == SENSOR_NEXT_RACE_IN:
        event = static.get("next_event")
        if event:
            attrs["race"] = event.get("name")
            attrs["short_name"] = event.get("short_name")
            attrs["date_start"] = event.get("date_start")
            attrs["date_end"] = event.get("date_end")
            attrs["circuit"] = _event_circuit(event)
    elif key == SENSOR_CURRENT_SEASON:
        season = static.get("season")
        if season:
            attrs["season_id"] = season.get("id")
            attrs["year"] = season.get("year")
    elif key == SENSOR_RIDER_STANDINGS:
        attrs["standings"] = static.get("rider_standings", [])
        attrs["count"] = len(static.get("rider_standings", []))
    elif key == SENSOR_CONSTRUCTOR_STANDINGS:
        attrs["standings"] = static.get("constructor_standings", [])
        attrs["count"] = len(static.get("constructor_standings", []))
    elif key == SENSOR_LAST_RACE_RESULTS:
        attrs["results"] = static.get("last_race_results", [])
        attrs["count"] = len(static.get("last_race_results", []))
    elif key == SENSOR_TRACK_WEATHER:
        weather = static.get("track_weather")
        if weather:
            attrs.update(weather)
    return attrs


def _event_circuit(event: dict[str, Any]) -> str | None:
    circuit = event.get("circuit")
    if isinstance(circuit, dict):
        return circuit.get("name")
    return None


def _event_country(event: dict[str, Any]) -> str | None:
    country = event.get("country")
    if isinstance(country, dict):
        return country.get("name")
    return None
