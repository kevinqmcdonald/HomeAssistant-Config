# Walnut Home dashboard

## Intent
Redesign all four views of `dashboard-home` (Home, Entertainment, Map, Deliveries) in the
Walnut theme and move them from storage mode to YAML. The main device is the wall tablet,
used by Kevin, Jordan and guests: house status at a glance, without scrolling the Home view.
The phone and desktop show the same content. Home controls (thermostats, lights, scenes)
are out of scope: Kevin will build a separate dashboard for them later.

## Feasibility
| # | element | rating | how (card / technique) | closest alternative | narrow vs wide |
| --- | --- | --- | --- | --- | --- |
| | **Home** | | | | |
| 1 | Kevin and Jordan | installed-card | `custom:button-card`, `wn_status`, tap navigates to the Map view | Icon, not photo | same, 2-up |
| 2 | Toby and Louie | installed-card | `custom:button-card`, `wn_status`, icon `mdi:dog`, grey while `unknown` | – | same, 2-up |
| 3 | Doors and windows | installed-card | `custom:button-card`, `wn_alert`. Label names what is open (JS over the group members and the gate). Tap opens `/dashboard-security/sensors-health` | – | same |
| 4 | Alarm status | installed-card | `custom:button-card`, `wn_status` | – | same |
| 5 | Arm home / Arm away / Disarm | installed-card | `custom:button-card`, new `wn_action`, 3-up. The active mode is highlighted. Disarm has `confirmation`; the arm buttons don't. | – | 3-up; icon above label on narrow |
| 6 | Attention notices | installed-card | `custom:button-card`, new `wn_notice`, each with a `state: "on"` visibility condition | – | same, 2-up |
| 7 | Alexa timers | installed-card | `custom:simple-timer-card`, shown only while a timer runs | Circle keeps its own drawing style | same |
| 8 | Weather and forecast | native | `weather-forecast`, daily, current + forecast | – | same |
| 9 | UV index and air quality | native | `tile` with `bar-gauge`, `state_content: [state, level]` | One bar colour, not a needle and rainbow | same, 2-up |
| 10 | Radar | card_mod | `custom:weather-radar-card` with `theme_mode: dark`, 320px high | Map tiles don't turn to glass | after trash day on narrow |
| 14 | Trash day | installed-card | `custom:trash-card`, `card_style: card`, `with_label: true`, 2-up | Icon colours from its named palette | higher on narrow (one copy per screen size) |
| 15 | This week's events | card_mod | `custom:atomic-calendar-revive` | Its own inner layout; per-calendar colours stay literal (see Components) | last on narrow |
| | **Entertainment** | | | | |
| 16 | Open Spotify | installed-card | `custom:button-card`, `wn_base`, gold icon, fires the browser_mod pop-up | Gold, not Spotify green | full width |
| 17 | Spotify pop-up | installed-card | `custom:popup-card` (`popup_card_id: spotify-browser`) with `custom:spotifyplus-card`, config carried over unchanged | Contents keep Spotify's look | near full screen on narrow |
| 18 | Speakers and TVs | native | `tile` with `media-player-playback` and `media-player-volume-slider` | – | speakers 3-up, TVs 1-up wide; stacked narrow |
| | **Map** | | | | |
| 19 | Map | native | `map`, `theme_mode: dark`, `auto_fit: true` | Rounded card, not full-bleed | above the list on narrow |
| 20 | Tracked people and items | native | `tile`, `state_content: [state, last_changed]` (`last_updated` for the four items, as today) | – | beside / below the map |
| | **Deliveries** | | | | |
| 21a | USPS mail | native | `tile`, `state_content: [state, last_updated]` | Tile icon, not the USPS logo | full width |
| 21b | Packages by carrier | installed-card | `custom:button-card`, new `wn_carrier`: logo, then "N in transit · N delivered", dimmed when both are 0 | Ten counts become five rows | 1-up, same |
| 22 | Tracking numbers | card_mod | `custom:tracking-number-card`, same title and sort as today | Keeps its own layout; scrolls with many packages | full width |

Numbers match the design conversation. 11–13 (thermostats, lights, scenes) were dropped.
No new HACS installs.

## Layout
All views are `type: sections`: nothing needs exact placement, and sections reflow on their
own. Section columns stay at HA's 500px maximum, which keeps the desktop from stretching.

```
HOME  path: home, max_columns 3
wide:   | Home               | Outside      | Today            |
        | 3 doors/windows    | 8 weather    | 14 trash (2-up)  |
        | 4 alarm            | 9 UV | AQI   | 15 events        |
        | 5 arm/away/disarm  | 10 radar     |                  |
        | 1 Kevin | Jordan   |              |                  |
        | 2 Toby  | Louie    |              |                  |
        | 6 notices (2-up)   |              |                  |
        | 7 timer            |              |                  |
narrow: Home -> Trash day (narrow-only section) -> Outside -> Today (events only)

ENTERTAINMENT  path: entertainment, max_columns 4
wide:   Speakers (column_span 3: Kitchen | Primary Bedroom | Office, then Spotify) | TVs
narrow: speakers -> Spotify -> TVs

MAP  path: map, max_columns 4
wide:   map (column_span 3) | Tracked list
narrow: map -> list
Map height uses fixed rows per screen, with visibility: narrow, wide up to 1100px high
(tablet), wide taller than that (desktop).

DELIVERIES  path: deliveries, max_columns 2
wide:   Mail + Packages today | Tracking
narrow: Mail -> Packages today -> Tracking
```

The notices stay below the people cards, so the alarm and people don't move when one appears.
With every notice and a timer showing, the Home column must still fit 1715×965.

## Components
- `wn_base`: reused as is (Spotify button).
- `wn_alert`: reused. The label lists open entries ("Open: Back Door"), or "All closed".
- `wn_status`: **change**. For a `person` / `device_tracker`, treat `unknown` and `unavailable` as `--wn-text-secondary`. Today they fall through to the tan "zone" colour.
- `wn_action` (new): 56px+ button with icon and label. Variables: `active_state`, the state that highlights it. The action and any `confirmation` are set on the card.
- `wn_notice` (new): 56px icon + label row at `--wn-font-md`. Variables: `tone` (`info` = blue border, `warn` = amber border).
- `wn_carrier` (new): logo, name, count line. Variables: `transit` and `delivered` (entity IDs), `logo` (image path).
- Theme: **add** `state-alarm_control_panel-pending-color: var(--wn-warn)`.
- UV / AQI bars use one fixed colour, the theme's blue. The preview drew them green, but a fixed green would look "safe" at any level. The level word carries the meaning.
- Literal colours: the events card keeps Kevin's existing per-calendar colours, as previewed. Each line takes `# lint-ignore: hardcoded-color`. The reason is that they identify calendars and match `dashboard-calendar`. The existing `cal-episodecalendar-com` rule is missing a `;` after `color: white !important`, so add it.
- Carrier logos: reuse the live images `/local/usps.png`, `/local/ups.png`, `/local/fedex.jpeg`, `/local/amazon-wh.png`, `/local/walmart.png`. They are in `www/`, which isn't tracked.

## Entities
All existing IDs were confirmed live on 2026-11-24.

- 1, 2: `person.kevin_mcdonald`, `person.jordan_cassino`, `person.toby`, `person.louie`
- 3: `binary_sensor.is_any_entry_sensor_open`. Names come from `binary_sensor.door_entry_sensors`, `binary_sensor.window_entry_sensors` (their `entity_id` members) and `binary_sensor.backyard_gate_sensor`
- 4, 5: `alarm_control_panel.home_alarm`
- 6: `binary_sensor.music_playing_anywhere` (info, tap → Entertainment), `binary_sensor.package_arriving_today` (info, tap → Deliveries), `binary_sensor.car_gas_low` (warn), `binary_sensor.oven_is_running` (warn), `binary_sensor.is_any_security_device_battery_low` (warn, tap → `/dashboard-security/sensors-health`)
- 7: `sensor.kitchen_echo_dot_next_timer`, `sensor.office_echo_dot_next_timer_2`, `sensor.primary_bedroom_echo_show_next_timer_2`
- 8: `weather.local_weather_tracker`
- 9: **create** two template sensors with a numeric state and a `level` attribute, in a new package `packages/outdoor_conditions.yaml`. They need a deploy and reload before the tiles and lint's entity check work.
  - `sensor.outdoor_uv_index` from `sensor.local_weather_tracker_live_uv_index`. Levels as today: Low ≤3, Moderate ≤6, High ≤8, Very High ≤11, else Extreme. Gauge 0–14.
  - `sensor.outdoor_air_quality` from `sensor.local_weather_tracker_air_quality`. Levels as today: Good ≤50, Moderate ≤100, Slightly Unhealthy ≤150, Unhealthy ≤200, Very Unhealthy ≤300, else Hazardous. Gauge 0–350.
  - These replace the working names `sensor.uv_level` and `sensor.outdoor_air_quality_level`, because `bar-gauge` needs the number as the state.
- 10: `zone.home`, plus the existing radar settings
- 14: `calendar.garbage_collection`
- 15: `calendar.birthdays`, `calendar.florida_gators_football`, `calendar.florida_gators_men_s_basketball`, `calendar.holidays_in_united_states`, `calendar.household`, `calendar.jordan`, `calendar.kevin`, `calendar.travel`, `calendar.episodecalendar_com_2` (replaces `calendar.episodecalendar_com`, which is unavailable)
- 17: `media_player.spotifyplus_home`
- 18: `media_player.kitchen_echo_dot`, `media_player.primary_bedroom_echo_show_2`, `media_player.office_echo_dot_2`, `media_player.living_room_tv`, `media_player.primary_bedroom_tv`
- 19, 20: `person.kevin_mcdonald`, `person.jordan_cassino`, `device_tracker.audi_car_position`, `device_tracker.briefcase`, `device_tracker.kevin_car_keys`, `device_tracker.travel_pouch`, `device_tracker.golf_bag`
- 21a: `sensor.package_tracker_mail_usps_mail`
- 21b in transit: `sensor.package_tracker_mail_usps_packages`, `sensor.package_tracker_mail_ups_packages`, `sensor.package_tracker_mail_fedex_packages`, `sensor.package_tracker_mail_amazon_packages`, `sensor.package_tracker_mail_walmart_packages`
- 21b delivered: `sensor.package_tracker_mail_usps_delivered`, `sensor.package_tracker_mail_ups_delivered`, `sensor.package_tracker_mail_fedex_delivered`, `sensor.package_tracker_mail_amazon_packages_delivered`, `sensor.package_tracker_mail_walmart_delivered`
- 22: `sensor.package_tracking_numbers`

## Preview
https://claude.ai/artifact/RJ58jsT9epn8KzetSLi6Ec (Preview 1)

## Approved
2026-11-24. Kevin approved Preview 1 ("Previews look good, proceed") with no changes.
Earlier instructions from Kevin: no Control column, keep Toby and Louie.

Changed after Kevin checked the scratch build (2026-11-24):
- **Trash day icons:** gold (Recycle) and blue (Trash), not green and blue. A named colour
  triggers a trash-card 2.4.7 bug that makes the text unreadable on a dark theme.
- **Tracking numbers:** link and copy targets enlarged to 48px with `card_mod`. The
  "Tracking" heading is removed, because the card has its own title.
- **Map zoom buttons:** Kevin waived the 48px minimum (about 31px, Home Assistant's own).

Deploy decisions (Kevin, 2026-11-24): registered at the new URL `/home-dashboard`, with the
old `dashboard-home` kept as a fallback, so links to `/dashboard-home/...` above became
`/home-dashboard/...`. `theme: Walnut` is set on each view, because making Walnut the
default would make the Security dashboard's hardcoded cream cards hard to read.

To check during the build:
- **Screenshots:** one at a time, fixed sizes, no `full_page`. See the safety rules in `.claude/agents/dashboard-reviewer.md`.
- **Forecast days:** on Tuesday 2026-11-24 the live forecast card started at "Mon". Check whether the labels are a day early before building on it.
- **Map base tiles:** the engine drew a blank map. Check on a real device.
- **Radar dark mode:** `theme_mode` comes from the card's current README. Check that the installed v4.0.0 supports it.
