"""MotoGP Sensor integration for Home Assistant."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .api import MotogpApiClient
from .const import (
    CONF_DEVICE_NAME,
    CONF_ENABLED_SENSORS,
    CONF_LIVE_SOURCE,
    CONF_RACE_WEEK_START_DAY,
    DOMAIN,
    LIVE_SOURCE_PULSELIVE,
    PLATFORMS,
    RACE_WEEK_START_MONDAY,
)
from .coordinator import MotogpCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MotoGP Sensor from a config entry."""
    coordinator = await _create_coordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Resolve the device id so device triggers can be matched.
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device({(DOMAIN, entry.entry_id)})
    if device:
        coordinator.device_id = device.id

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: MotogpCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry (used by the options flow)."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _create_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> MotogpCoordinator:
    """Create and start the data coordinator for an entry."""
    options = {**entry.data, **(entry.options or {})}

    session = aiohttp.ClientSession()
    api = MotogpApiClient(session)

    coordinator = MotogpCoordinator(
        hass,
        api,
        live_source=options.get(CONF_LIVE_SOURCE, LIVE_SOURCE_PULSELIVE),
        race_week_start_day=options.get(
            CONF_RACE_WEEK_START_DAY, RACE_WEEK_START_MONDAY
        ),
        enabled_sensors=options.get(CONF_ENABLED_SENSORS, []),
    )
    await coordinator.async_config_entry_first_refresh()
    return coordinator
