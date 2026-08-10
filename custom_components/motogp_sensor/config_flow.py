"""Config flow for the MotoGP Sensor integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import (
    ALL_SENSORS,
    CONF_DEVICE_NAME,
    CONF_ENABLED_SENSORS,
    CONF_LIVE_SOURCE,
    CONF_RACE_WEEK_START_DAY,
    DOMAIN,
    LIVE_SOURCE_AUTO,
    LIVE_SOURCE_OFFICIAL,
    LIVE_SOURCE_OPTIONS,
    LIVE_SOURCE_PULSELIVE,
    RACE_WEEK_START_MONDAY,
    RACE_WEEK_START_OPTIONS,
    SENSOR_CONSTRUCTOR_STANDINGS,
    SENSOR_CURRENT_SEASON,
    SENSOR_CURRENT_SESSION,
    SENSOR_FASTEST_LAP,
    SENSOR_LAST_RACE_RESULTS,
    SENSOR_LEADER,
    SENSOR_NEXT_RACE,
    SENSOR_PIT_STOPS,
    SENSOR_RACE_LAP_COUNT,
    SENSOR_RIDER_POSITIONS,
    SENSOR_RIDER_STANDINGS,
    SENSOR_SESSION_STATUS,
    SENSOR_SESSION_TIME_REMAINING,
    SENSOR_TOP_THREE,
    SENSOR_TRACK_WEATHER,
)

_LOGGER = logging.getLogger(__name__)

SENSOR_LABELS: dict[str, str] = {
    SENSOR_SESSION_STATUS: "Session status",
    SENSOR_CURRENT_SESSION: "Current session",
    SENSOR_RACE_LAP_COUNT: "Race lap count",
    SENSOR_RIDER_POSITIONS: "Rider positions",
    SENSOR_TOP_THREE: "Top three",
    SENSOR_LEADER: "Leader",
    SENSOR_FASTEST_LAP: "Fastest lap",
    SENSOR_SESSION_TIME_REMAINING: "Session time remaining",
    SENSOR_TRACK_WEATHER: "Track weather",
    SENSOR_PIT_STOPS: "Pit stops",
    SENSOR_NEXT_RACE: "Next race",
    SENSOR_CURRENT_SEASON: "Current season",
    SENSOR_RIDER_STANDINGS: "Rider standings",
    SENSOR_CONSTRUCTOR_STANDINGS: "Constructor standings",
    SENSOR_LAST_RACE_RESULTS: "Last race results",
}

LIVE_SOURCE_LABELS: dict[str, str] = {
    LIVE_SOURCE_PULSELIVE: "Pulselive (recommended)",
    LIVE_SOURCE_OFFICIAL: "Official motogp.com (experimental)",
    LIVE_SOURCE_AUTO: "Auto (Pulselive with official fallback)",
}


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the config/options schema with the given defaults."""
    return vol.Schema(
        {
            vol.Required(CONF_DEVICE_NAME, default=defaults.get(CONF_DEVICE_NAME, "MotoGP")): str,
            vol.Optional(
                CONF_ENABLED_SENSORS,
                default=defaults.get(CONF_ENABLED_SENSORS, ALL_SENSORS),
            ): cv.multi_select(SENSOR_LABELS),
            vol.Optional(
                CONF_LIVE_SOURCE,
                default=defaults.get(CONF_LIVE_SOURCE, LIVE_SOURCE_PULSELIVE),
            ): vol.In(LIVE_SOURCE_OPTIONS),
            vol.Optional(
                CONF_RACE_WEEK_START_DAY,
                default=defaults.get(CONF_RACE_WEEK_START_DAY, RACE_WEEK_START_MONDAY),
            ): vol.In(RACE_WEEK_START_OPTIONS),
        }
    )


class MotogpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MotoGP Sensor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            device_name = user_input.get(CONF_DEVICE_NAME, "MotoGP").strip()
            if not device_name:
                errors[CONF_DEVICE_NAME] = "required"
            else:
                return self.async_create_entry(
                    title=device_name,
                    data={
                        CONF_NAME: device_name,
                        CONF_DEVICE_NAME: device_name,
                        CONF_ENABLED_SENSORS: list(user_input.get(CONF_ENABLED_SENSORS, ALL_SENSORS)),
                        CONF_LIVE_SOURCE: user_input.get(CONF_LIVE_SOURCE, LIVE_SOURCE_PULSELIVE),
                        CONF_RACE_WEEK_START_DAY: user_input.get(
                            CONF_RACE_WEEK_START_DAY, RACE_WEEK_START_MONDAY
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema({}),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigFlowResult,  # type: ignore[override]
    ) -> OptionsFlow:
        """Get the options flow for this handler."""
        return MotogpOptionsFlow(config_entry)


class MotogpOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigFlowResult) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_DEVICE_NAME: user_input.get(CONF_DEVICE_NAME, "MotoGP"),
                    CONF_ENABLED_SENSORS: list(user_input.get(CONF_ENABLED_SENSORS, ALL_SENSORS)),
                    CONF_LIVE_SOURCE: user_input.get(CONF_LIVE_SOURCE, LIVE_SOURCE_PULSELIVE),
                    CONF_RACE_WEEK_START_DAY: user_input.get(
                        CONF_RACE_WEEK_START_DAY, RACE_WEEK_START_MONDAY
                    ),
                },
            )

        defaults = dict(self._config_entry.data)
        defaults.update(self._config_entry.options or {})
        return self.async_show_form(
            step_id="init",
            data_schema=_user_schema(defaults),
        )
