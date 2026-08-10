"""Calendar platform for the MotoGP Sensor integration."""

from __future__ import annotations

from datetime import date

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import CONF_DEVICE_NAME, DOMAIN
from .coordinator import MotogpCoordinator
from .entity import MotogpEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the MotoGP calendar from a config entry."""
    coordinator: MotogpCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_name = entry.data.get(CONF_DEVICE_NAME, "MotoGP")
    async_add_entities([MotogpCalendar(coordinator, device_name)])


class MotogpCalendar(MotogpEntity, CalendarEntity):
    """Calendar showing the MotoGP race schedule."""

    def __init__(
        self,
        coordinator: MotogpCoordinator,
        device_name: str,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator, device_name)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming calendar event."""
        entries = self.coordinator.static.get("calendar", [])
        if not entries:
            return None
        now = dt_util.now()
        today = now.date()
        for entry in entries:
            start = entry.get("start", "")
            end = entry.get("end", "")
            if start and end and start <= today.isoformat() < end:
                return self._to_event(entry)
        for entry in entries:
            start = entry.get("start", "")
            if start and start >= today.isoformat():
                return self._to_event(entry)
        return None

    @staticmethod
    def _to_event(entry: dict[str, str]) -> CalendarEvent:
        """Build a CalendarEvent from a calendar entry.

        Passing ``date`` objects (instead of datetimes) makes the event
        all-day in modern Home Assistant versions.
        """
        start = date.fromisoformat(entry["start"])
        end = date.fromisoformat(entry["end"])
        return CalendarEvent(
            summary=entry["summary"],
            start=start,
            end=end,
        )
