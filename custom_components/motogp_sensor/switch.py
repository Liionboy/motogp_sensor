"""Switch platform for the MotoGP Sensor integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_NAME, DOMAIN
from .coordinator import MotogpCoordinator
from .entity import MotogpEntity

NO_SPOILER_KEY = "no_spoiler"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MotoGP switches from a config entry."""
    coordinator: MotogpCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_name = entry.data.get(CONF_DEVICE_NAME, "MotoGP")
    description = SwitchEntityDescription(
        key=NO_SPOILER_KEY,
        translation_key=NO_SPOILER_KEY,
        icon="mdi:eye-off",
    )
    async_add_entities([NoSpoilerSwitch(coordinator, device_name, description)])


class NoSpoilerSwitch(MotogpEntity, SwitchEntity):
    """Switch that hides live race data (spoiler protection)."""

    def __init__(
        self,
        coordinator: MotogpCoordinator,
        device_name: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, device_name)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{NO_SPOILER_KEY}"

    @property
    def is_on(self) -> bool:
        """Return the switch state."""
        return self.coordinator.no_spoiler

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable spoiler protection."""
        self.coordinator.no_spoiler = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable spoiler protection."""
        self.coordinator.no_spoiler = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
