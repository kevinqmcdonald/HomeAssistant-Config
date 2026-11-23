# Walnut theme

## Intent
The single, dark-only theme for every dashboard: the dark walnut photo, frosted translucent
tiles, white sans-serif text, and a blue/gold/tan palette. It replaces Warm Home. The main
device is the wall tablet, used by Kevin, Jordan and guests: readable across the room,
with 48px touch targets.

## Feasibility
| # | element | rating | how (card / technique) | closest alternative | narrow vs wide |
| --- | --- | --- | --- | --- | --- |
| 1 | Wood photo behind every view | theme-css | `lovelace-background` with a dim gradient layer + `url(/local/backgrounds/walnut.jpg)` | `fixed` attachment is ignored by some mobile browsers, so the photo scrolls with the page there | same |
| 2 | Frosted translucent tiles | theme-css | `ha-card-background` = `--wn-surface` + `card-mod-card` `backdrop-filter: blur(var(--wn-blur))` | – | same |
| 3 | White Inter text | theme-css | `primary-font-family` / `ha-font-family-body` = `--wn-font`. Inter self-hosted in `www/fonts` and loaded by a `css` Lovelace resource | Falls back to the system sans-serif until the resource is added | same |
| 4 | Blue-led accents, gold for "on" | theme-css | `primary-color` blue; `state-*-active-color` gold for lights/switches/fans | Cards that set their own colours (gauge-card-pro segments, calendar colours) keep them | same |
| 5 | 48px touch targets on tile features | theme-css | `feature-height: var(--wn-touch-min)` | – | same |
| 6 | Dark dialogs, sidebar and header | theme-css | theme defined under `modes: dark` so HA renders dark everywhere; sidebar/header vars set | – | same |
| 7 | Consistent house buttons | installed-card | `custom:button-card` templates `wn_base`, `wn_alert` | – | same |

## Layout
Style sample view (`dashboards/style-sample.yaml`): a `sections` view with `max_columns: 4`.
- Wide: Home (alert + alarm) | Rooms (4 tiles, 2-up) | Now playing | Weather.
- Narrow: the same sections stacked in that order.

## Components
- `wn_base`: unchanged, plus an explicit icon size (`--wn-icon-size`, 28px).
- `wn_alert` (new): an entity-driven banner. Warn styling when the entity is `on`, ok styling otherwise. Variables: none. Uses `name`, `entity` and `label`.

## Entities
- 1 badges: `alarm_control_panel.home_alarm`, `binary_sensor.door_entry_sensors`, `binary_sensor.window_entry_sensors`, `person.kevin_mcdonald`, `person.jordan_cassino`
- alert: `binary_sensor.is_any_entry_sensor_open`
- alarm tile: `alarm_control_panel.home_alarm`
- rooms: `light.kitchen_light`, `light.living_room_light`, `light.bedroom_light_1`, `light.office_light`
- media: `media_player.kitchen_echo_dot`
- weather: `weather.local_weather_tracker`

## Preview
https://claude.ai/artifact/LSq6Vy4TAArh8ZULt8SXAn (variant B chosen)

## Approved
2026-11-23. Kevin chose variant **B · Smoked blue** (Inter font, darker glass, blue-led).
Token values are as in the preview's variant B. Adding the Inter `css` resource is a live
change, so ask at deploy.
