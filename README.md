# MotoGP Sensor for Home Assistant

Custom [Home Assistant](https://www.home-assistant.io/) integration that brings
the world of MotoGP into your smart home: live session timing, rider
positions, championship standings and the full race calendar.

Built from scratch and tested against the live Pulselive API — no affiliation
with Dorna Sports or MotoGP.

> Inspired by the F1 Sensor concept, but 100% original code, with a working
> release pipeline out of the box.

## Features

**Live timing** (polled every 10s while a session is in progress, every 5min otherwise):

| Sensor | Description |
| ------ | ----------- |
| Session status | In Progress, Finished, Red Flag, Cancelled, Delayed… |
| Current session | Session abbreviation (RAC, SPR, Q1, FP1…) |
| Race lap count | Current lap across all riders |
| Rider positions | Full position board with gaps and lap times |
| Top three | Podium snapshot |
| Leader | Current session leader |
| Fastest lap | Fastest lap of the session |
| Session time remaining | Remaining session time |
| Track weather | Air/track temperature, humidity, conditions |
| Pit stops | Riders currently in the pits |

**Season data** (refreshed every 6h):

| Sensor | Description |
| ------ | ----------- |
| Next race | Name, dates, circuit and country of the next GP |
| Current season | Active season year |
| Rider standings | Full championship standings |
| Constructor standings | Team championship standings |
| Last race results | Classification of the most recent race |
| Calendar | All GPs as a HA calendar entity |

**Binary sensors**:

| Sensor | Description |
| ------ | ----------- |
| Race week | ON during a race weekend (configurable start day + 3h grace) |
| Live timing online | ON while a live timing feed is reachable |

**Extras**:

- **No spoiler mode** — switch that hides all live race data (for watching on delay)
- **Live source select** — choose Pulselive, official or auto at runtime
- **9 device triggers** for automations: `race_week_started`, `race_week_ended`,
  `session_in_progress`, `session_finished`, `session_red_flag`,
  `session_cancelled`, `session_delayed`, `live_timing_online`,
  `live_timing_offline`
- UI translations for English and Romanian

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋯ → **Custom repositories**
2. Add `https://github.com/Liionboy/motogp_sensor` with category **Integration**
3. Search for **MotoGP Sensor** and install
4. Restart Home Assistant
5. Settings → Devices & Services → Add Integration → **MotoGP Sensor**

### Manual

1. Copy the `custom_components/motogp_sensor` folder into your HA
   `custom_components` directory
2. Restart Home Assistant
3. Add the integration from Settings → Devices & Services

## Configuration

| Option | Description | Default |
| ------ | ----------- | ------- |
| Device name | Label for the HA device | `MotoGP` |
| Sensors to enable | Multi-select of all available sensors | All enabled |
| Live timing source | `pulselive` / `official` / `auto` | `pulselive` |
| Race week start day | Day the Race Week sensor turns ON | `monday` |

Change options any time: Devices & Services → MotoGP Sensor → Configure.

## Data sources

| Source | Endpoint | Notes |
| ------ | -------- | ----- |
| Pulselive (default) | `api.motogp.pulselive.com/motogp/v1` | REST + live timing |
| Official | `motogp.com/en/json/live_timing` | Experimental — may be unavailable |

## Automations

Example — lights flash when the MotoGP race goes live:

```yaml
automation:
  - alias: "MotoGP race started"
    trigger:
      - platform: device
        domain: motogp_sensor
        type: session_in_progress
        device_id: YOUR_DEVICE_ID
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          flash: short
```

## Disclaimer

This project is an unofficial integration and is not affiliated with or
endorsed by Dorna Sports or MotoGP. MotoGP and the MotoGP logo are trademarks
of Dorna Sports S.L.
