"""Binary sensor platform for the MotoGP Sensor integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BINARY_LIVE_TIMING_ONLINE,
    BINARY_RACE_WEEK,
    CONF_DEVICE_NAME,
    DOMAIN,
)
from .coordinator import MotogpCoordinator
from .entity import MotogpEntity

BINARY_DESCRIPTIONS: dict[str, BinarySensorEntityDescription] = {
    BINARY_RACE_WEEK: BinarySensorEntityDescription(
        key=BINARY_RACE_WEEK,
        translation_key=BINARY_RACE_WEEK,
        icon="mdi:flag-variant",
    ),
    BINARY_LIVE_TIMING_ONLINE: BinarySensorEntityDescription(
        key=BINARY_LIVE_TIMING_ONLINE,
        translation_key=BINARY_LIVE_TIMING_ONLINE,
        icon="mdi:access-point-network",
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MotoGP binary sensors from a config entry."""
    coordinator: MotogpCoordinator = hass.data[DOMAIN][entry.entry_id]
    device_name = entry.data.get(CONF_DEVICE_NAME, "MotoGP")
    async_add_entities(
        MotogpBinarySensor(coordinator, device_name, description)
        for description in BINARY_DESCRIPTIONS.values()
    )


class MotogpBinarySensor(MotogpEntity, BinarySensorEntity):
    """A MotoGP binary sensor."""

    def __init__(
        self,
        coordinator: MotogpCoordinator,
        device_name: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, device_name)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        if self.entity_description.key == BINARY_RACE_WEEK:
            return self.coordinator.race_week
        if self.entity_description.key == BINARY_LIVE_TIMING_ONLINE:
            return self.coordinator.live_online
        return None
