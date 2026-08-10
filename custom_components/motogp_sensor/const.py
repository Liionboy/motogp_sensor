"""Constants for the MotoGP Sensor integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "motogp_sensor"
MANUFACTURER = "Dorna Sports (unofficial)"
MODEL = "MotoGP Live Timing"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.SWITCH,
    Platform.SELECT,
]

# ── Configuration keys ───────────────────────────────────────────────────────
CONF_DEVICE_NAME = "device_name"
CONF_LIVE_SOURCE = "live_source"
CONF_ENABLED_SENSORS = "enabled_sensors"
CONF_RACE_WEEK_START_DAY = "race_week_start_day"

# ── Live source options ──────────────────────────────────────────────────────
LIVE_SOURCE_PULSELIVE = "pulselive"
LIVE_SOURCE_OFFICIAL = "official"
LIVE_SOURCE_AUTO = "auto"
LIVE_SOURCE_OPTIONS = [
    LIVE_SOURCE_PULSELIVE,
    LIVE_SOURCE_OFFICIAL,
    LIVE_SOURCE_AUTO,
]

# ── Race week start day options ──────────────────────────────────────────────
RACE_WEEK_START_MONDAY = "monday"
RACE_WEEK_START_SATURDAY = "saturday"
RACE_WEEK_START_SUNDAY = "sunday"
RACE_WEEK_START_OPTIONS = [
    RACE_WEEK_START_MONDAY,
    RACE_WEEK_START_SATURDAY,
    RACE_WEEK_START_SUNDAY,
]

# ── Polling intervals ────────────────────────────────────────────────────────
LIVE_POLLING_ACTIVE = timedelta(seconds=10)   # session in progress
LIVE_POLLING_IDLE = timedelta(seconds=300)    # no active session
STATIC_REFRESH_INTERVAL = timedelta(hours=6)  # standings/calendar refresh

# ── HTTP ─────────────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (HomeAssistant motogp_sensor/1.0.4)"

# ── Pulselive REST API ───────────────────────────────────────────────────────
PULSELIVE_BASE_URL = "https://api.motogp.pulselive.com/motogp/v1"
PULSELIVE_LIVE_TIMING_URL = f"{PULSELIVE_BASE_URL}/timing-gateway/livetiming-lite"
PULSELIVE_SEASONS_URL = f"{PULSELIVE_BASE_URL}/results/seasons"
PULSELIVE_CATEGORIES_URL = f"{PULSELIVE_BASE_URL}/results/categories"
PULSELIVE_EVENTS_URL = f"{PULSELIVE_BASE_URL}/results/events"
PULSELIVE_SESSIONS_URL = f"{PULSELIVE_BASE_URL}/results/sessions"
PULSELIVE_SESSION_CLASSIFICATION_URL = (
    f"{PULSELIVE_BASE_URL}/results/session/{{uuid}}/classification"
)
PULSELIVE_STANDINGS_URL = (
    f"{PULSELIVE_BASE_URL}/results/standings"
    "?seasonUuid={season_uuid}&categoryUuid={category_uuid}"
)
PULSELIVE_TEAM_STANDINGS_URL = (
    f"{PULSELIVE_BASE_URL}/results/standings"
    "?seasonUuid={season_uuid}&categoryUuid={category_uuid}&type=team"
)

# ── Official / experimental source ───────────────────────────────────────────
OFFICIAL_LIVE_TIMING_URL = "https://www.motogp.com/en/json/live_timing"

# ── Session status ID → human-readable string ────────────────────────────────
SESSION_STATUS_MAP: dict[str, str] = {
    "C": "Cancelled",
    "D": "Delayed",
    "F": "Finished",
    "I": "In Progress",
    "N": "Not Started",
    "R": "Red Flag",
}

# ── Sensor keys ──────────────────────────────────────────────────────────────
SENSOR_SESSION_STATUS = "session_status"
SENSOR_CURRENT_SESSION = "current_session"
SENSOR_RACE_LAP_COUNT = "race_lap_count"
SENSOR_RIDER_POSITIONS = "rider_positions"
SENSOR_TOP_THREE = "top_three"
SENSOR_LEADER = "leader"
SENSOR_FASTEST_LAP = "fastest_lap"
SENSOR_SESSION_TIME_REMAINING = "session_time_remaining"
SENSOR_TRACK_WEATHER = "track_weather"
SENSOR_PIT_STOPS = "pit_stops"
SENSOR_NEXT_RACE = "next_race"
SENSOR_CURRENT_SEASON = "current_season"
SENSOR_RIDER_STANDINGS = "rider_standings"
SENSOR_CONSTRUCTOR_STANDINGS = "constructor_standings"
SENSOR_LAST_RACE_RESULTS = "last_race_results"

LIVE_SENSORS = [
    SENSOR_SESSION_STATUS,
    SENSOR_CURRENT_SESSION,
    SENSOR_RACE_LAP_COUNT,
    SENSOR_RIDER_POSITIONS,
    SENSOR_TOP_THREE,
    SENSOR_LEADER,
    SENSOR_FASTEST_LAP,
    SENSOR_SESSION_TIME_REMAINING,
    SENSOR_TRACK_WEATHER,
    SENSOR_PIT_STOPS,
]

STATIC_SENSORS = [
    SENSOR_NEXT_RACE,
    SENSOR_CURRENT_SEASON,
    SENSOR_RIDER_STANDINGS,
    SENSOR_CONSTRUCTOR_STANDINGS,
    SENSOR_LAST_RACE_RESULTS,
]

ALL_SENSORS = LIVE_SENSORS + STATIC_SENSORS

# ── Binary sensor keys ───────────────────────────────────────────────────────
BINARY_RACE_WEEK = "race_week"
BINARY_LIVE_TIMING_ONLINE = "live_timing_online"

# ── Event types fired on the HA event bus (device triggers) ──────────────────
EVENT_MOTOGP = "motogp_sensor_event"
EVENT_RACE_WEEK_STARTED = "race_week_started"
EVENT_RACE_WEEK_ENDED = "race_week_ended"
EVENT_SESSION_IN_PROGRESS = "session_in_progress"
EVENT_SESSION_FINISHED = "session_finished"
EVENT_SESSION_RED_FLAG = "session_red_flag"
EVENT_SESSION_CANCELLED = "session_cancelled"
EVENT_SESSION_DELAYED = "session_delayed"
EVENT_LIVE_TIMING_ONLINE = "live_timing_online"
EVENT_LIVE_TIMING_OFFLINE = "live_timing_offline"

# ── Device trigger types ─────────────────────────────────────────────────────
TRIGGER_TYPE_EVENT = "event"
