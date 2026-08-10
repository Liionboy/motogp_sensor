"""Shared Home Assistant stubs for local testing.

Allows importing the integration modules without a Home Assistant
installation. Only used by the local test scripts.
"""

from __future__ import annotations

import sys
import types


def stub_homeassistant() -> None:
    """Install minimal stubs for the HA modules used by the integration."""
    ha = types.ModuleType("homeassistant")
    ha_const = types.ModuleType("homeassistant.const")

    class Platform:
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        CALENDAR = "calendar"
        SWITCH = "switch"
        SELECT = "select"

    ha_const.Platform = Platform
    ha_const.CONF_NAME = "name"
    ha_const.CONF_DEVICE_ID = "device_id"
    ha_const.CONF_DOMAIN = "domain"
    ha_const.CONF_TYPE = "type"
    ha_const.CONF_PLATFORM = "platform"
    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.const"] = ha_const

    def mk(name: str, **attrs: object) -> types.ModuleType:
        module = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(module, key, value)
        sys.modules[name] = module
        return module

    class DummyDeviceInfo:
        pass

    class DummyCoordinatorEntity:
        def __init__(self, coordinator: object, *args: object, **kwargs: object) -> None:
            self.coordinator = coordinator

        def __class_getitem__(cls, item: object) -> type:
            return cls

    class DummySensorEntity:
        pass

    class DummyBinarySensorEntity:
        pass

    class DummyCalendarEntity:
        pass

    class DummySwitchEntity:
        pass

    class DummySelectEntity:
        pass

    class DummyDataUpdateCoordinator:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __class_getitem__(cls, item: object) -> type:
            return cls

    class DummyCalendarEvent:
        pass

    class DummyDeviceTriggerBaseSchema:
        @staticmethod
        def extend(schema: object) -> object:
            return schema

    class DummyUpdateFailed(Exception):
        pass

    class DummyClientSession:
        pass

    class DummyClientTimeout:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

    class DummyClientError(Exception):
        pass

    class DummyConfigFlow:
        def __init_subclass__(cls, **kwargs: object) -> None:
            super().__init_subclass__()

    class DummyOptionsFlow:
        pass

    class DummyConfigFlowResult:
        pass

    mk("homeassistant.config_entries", ConfigEntry=None, ConfigFlow=DummyConfigFlow,
      ConfigFlowResult=DummyConfigFlowResult, OptionsFlow=DummyOptionsFlow)
    mk("homeassistant.helpers", config_validation=None)
    mk("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=DummyDataUpdateCoordinator,
      UpdateFailed=DummyUpdateFailed, CoordinatorEntity=DummyCoordinatorEntity)
    mk("homeassistant.helpers.device_registry", DeviceInfo=DummyDeviceInfo)
    mk("homeassistant.helpers.entity_platform", AddEntitiesCallback=None)
    mk("homeassistant.components.sensor", SensorEntity=DummySensorEntity,
      SensorEntityDescription=type("SED", (), {"__init__": lambda self, **kw: self.__dict__.update(kw)}))
    mk("homeassistant.components.binary_sensor", BinarySensorEntity=DummyBinarySensorEntity,
      BinarySensorEntityDescription=type("BSED", (), {"__init__": lambda self, **kw: self.__dict__.update(kw)}))
    mk("homeassistant.components.calendar", CalendarEntity=DummyCalendarEntity, CalendarEvent=DummyCalendarEvent)
    mk("homeassistant.components.switch", SwitchEntity=DummySwitchEntity,
      SwitchEntityDescription=type("SWED", (), {"__init__": lambda self, **kw: self.__dict__.update(kw)}))
    mk("homeassistant.components.select", SelectEntity=DummySelectEntity,
      SelectEntityDescription=type("SELED", (), {"__init__": lambda self, **kw: self.__dict__.update(kw)}))
    mk("homeassistant.components.device_automation", DEVICE_TRIGGER_BASE_SCHEMA=DummyDeviceTriggerBaseSchema())
    mk("homeassistant.core", HomeAssistant=None, Event=None, callback=lambda f: f)
    mk("homeassistant.helpers.trigger", TriggerActionType=None, TriggerInfo=None)
    mk("homeassistant.helpers.typing", ConfigType=None)
    mk("homeassistant.util", dt=None)
    mk("aiohttp", ClientSession=DummyClientSession, ClientTimeout=DummyClientTimeout,
      ClientError=DummyClientError)

    # Minimal voluptuous stub (schema building is not exercised in these tests)
    vol = types.ModuleType("voluptuous")
    vol.Required = lambda x: x
    vol.Optional = lambda x, default=None: x
    vol.In = lambda x: x
    vol.Schema = lambda x: x
    vol.All = lambda *x: x
    sys.modules["voluptuous"] = vol
