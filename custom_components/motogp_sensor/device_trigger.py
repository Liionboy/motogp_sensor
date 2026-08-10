"""Device triggers for the MotoGP Sensor integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.const import CONF_DEVICE_ID, CONF_DOMAIN, CONF_TYPE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

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
)

TRIGGER_TYPES: dict[str, str] = {
    EVENT_RACE_WEEK_STARTED: "Race week started",
    EVENT_RACE_WEEK_ENDED: "Race week ended",
    EVENT_SESSION_IN_PROGRESS: "Session in progress",
    EVENT_SESSION_FINISHED: "Session finished",
    EVENT_SESSION_RED_FLAG: "Red flag",
    EVENT_SESSION_CANCELLED: "Session cancelled",
    EVENT_SESSION_DELAYED: "Session delayed",
    EVENT_LIVE_TIMING_ONLINE: "Live timing online",
    EVENT_LIVE_TIMING_OFFLINE: "Live timing offline",
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device triggers for MotoGP devices."""
    return [
        {
            "platform": "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: trigger_type,
        }
        for trigger_type in TRIGGER_TYPES
    ]


async def async_validate_trigger_config(
    hass: HomeAssistant, config: ConfigType
) -> ConfigType:
    """Validate config."""
    return TRIGGER_SCHEMA(config)


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> Callable[[], None]:
    """Attach a trigger."""
    trigger_type = config[CONF_TYPE]
    device_id = config[CONF_DEVICE_ID]
    description = TRIGGER_TYPES[trigger_type]

    @callback
    def _handle_event(event: Event) -> None:
        """Listen for events and fire the trigger."""
        if event.data.get(CONF_DEVICE_ID) != device_id:
            return
        if event.data.get("type") != trigger_type:
            return
        hass.async_run_hass_job(
            action,
            {
                "trigger": {
                    **config,
                    "description": description,
                }
            },
        )

    return hass.bus.async_listen(EVENT_MOTOGP, _handle_event)
