"""Select platform for the MotoGP Sensor integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_NAME,
    CONF_LIVE_SOURCE,
    DOMAIN,
    LIVE_SOURCE_OPTIONS,
)
from .coordinator import MotogpCoordinator
from .entity import MotogpEntity

LIVE_SOURCE_KEY = "live_source"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MotoGP selects from a config entry."""
    coordinator: MotogpCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_name = entry.data.get(CONF_DEVICE_NAME, "MotoGP")
    description = SelectEntityDescription(
        key=LIVE_SOURCE_KEY,
        translation_key=LIVE_SOURCE_KEY,
        icon="mdi:source-branch",
    )
    async_add_entities([LiveSourceSelect(coordinator, device_name, description)])


class LiveSourceSelect(MotogpEntity, SelectEntity):
    """Select the live timing source."""

    def __init__(
        self,
        coordinator: MotogpCoordinator,
        device_name: str,
        description: SelectEntityDescription,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator, device_name)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{LIVE_SOURCE_KEY}"
        self._attr_options = LIVE_SOURCE_OPTIONS
        self._attr_current_option = coordinator.live_source

    async def async_select_option(self, option: str) -> None:
        """Change the live timing source at runtime."""
        if option not in self._attr_options:
            return
        self.coordinator.live_source = option
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
