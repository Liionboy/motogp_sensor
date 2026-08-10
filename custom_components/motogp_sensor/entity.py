"""Base entity for the MotoGP Sensor integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import MotogpCoordinator


class MotogpEntity(CoordinatorEntity[MotogpCoordinator]):
    """Base entity for MotoGP sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MotogpCoordinator,
        device_name: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_name = device_name

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this entity."""
        entry_id = self.coordinator.config_entry.entry_id
        return DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version="1.0.0",
            configuration_url="https://github.com/Liionboy/motogp_sensor",
        )
