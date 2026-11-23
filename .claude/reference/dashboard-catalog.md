# Dashboard catalogue

Inventory of every frontend building block installed on the live instance, how each
one takes styling, and where it's already used. Skills and agents that design or build
dashboards **must read this first** and only propose cards listed here (or built-ins).
Suggesting a new HACS install is allowed, but call it out explicitly as a new dependency.

- Snapshot taken: 2026-11-23 from HACS (Marketplace 2026.11.1) + Lovelace resources.
- Lovelace mode: **storage** (dashboards live in `.storage`, edited via UI or ha-mcp, not in this repo).
- Refresh: re-run `ha_get_hacs_info(action="search", installed_only=True, category="plugin")`
  and `ha_config_list_dashboard_resources()` and diff against this file.

## Dashboards today

| url_path | Views | Theme | Notes |
| --- | --- | --- | --- |
| `dashboard-home` | Home (sections, no `path`), Entertainment, Map (sidebar), Deliveries | `Warm Home` (view-level) | Heaviest custom-card mix. First view has no stable path. |
| `dashboard-security` | Overview, Cameras, Sensors & Health (all sections) | none set; hardcodes Warm Home colours (`#fefcf8`, `rgba(180,130,80,…)`) in ~40 `card_mod` blocks | Same Jinja dicts copy-pasted 3–4× per card. |
| `dashboard-calendar` | Monthly (sections, no `path`), Daily (sidebar), Yearly To-Do (panel) | none | Calendar colours duplicated from `dashboard-home`'s atomic-calendar `card_mod`. |

## Themes (`themes/`)

| Theme | Source | Notes |
| --- | --- | --- |
| **Walnut** | repo (`themes/walnut.yaml`) | **The house theme** (since 2026-11-23): dark-only, walnut photo, frosted tiles, Inter, blue/gold/tan. All tokens (`--wn-*`) are listed in the style guide. Currently applied only to the style sample on `dashboard-scratch`; the real dashboards switch over during the redesign. |
| Warm Home | repo | Being replaced by Walnut. Still applied to `dashboard-home` and hardcoded into `dashboard-security`'s `card_mod` until the redesign. |
| Luxury Gold, Material You, Soft Pastel | repo | Unused. |
| nordic, nordic-blue | HACS (coltondick/nordic-theme-main) | Unused. |

Backend default theme is `default`; no dark theme configured.

## Styling model: who owns which style

This is the root of the "inconsistent UI" problem. Every card falls into one of these:

| Tier | Mechanism | Cards |
| --- | --- | --- |
| **A. Theme-native** | Reads standard HA vars (`--ha-card-*`, `--primary-color`, `--state-*`, fonts) | Built-ins (tile, heading, entities, glance, markdown, badges), Mushroom, TrashCard |
| **B. Own var namespace** | Exposes its own CSS vars you can set *in the theme* | Mushroom (`--mush-*`), Bubble Card (`--bubble-*`), mini-graph (partial) |
| **C. Own config styling** | Style lives in each card's YAML (`styles:`, colour keys, templates) | button-card (`styles:` + dashboard-level `button_card_templates`), gauge-card-pro, daylight-calendar (`colors`), simple-timer, clock-weather, Foundry |
| **D. Opaque / shadow-DOM heavy** | Only reachable via `card_mod` with `$` shadow selectors; fragile across updates | SpotifyPlus card, advanced-camera-card, atomic-calendar-revive, vacuum-card, weather-radar, Mail & Packages card, tracking-number-card |

Design rule of thumb: prefer tiers A/B, centralise tier C via templates, use tier D
only where no alternative exists, and expect it to look "off-theme".

## Layout & structure

| Component | Type string | Ver. | Use for | Watch out |
| --- | --- | --- | --- | --- |
| Sections view (built-in) | `type: sections` | core | Default for every dashboard here. 12-col grid per section, `grid_options`, `column_span`, `max_columns`. Reflows by width automatically. | Limited control over *which* sections go where per device; use `visibility` (`screen`, `user` conditions) for that. |
| Sidebar / panel view (built-in) | `type: sidebar` / `panel` | core | Map + list; full-bleed single card (floorplan, calendar). | Sidebar collapses to one column on narrow screens. |
| layout-card | `custom:grid-layout`, `custom:masonry-layout`, `custom:horizontal-layout`, `custom:vertical-layout` (views); `custom:layout-card` (card) | v2.4.7 | CSS-grid layouts with `mediaquery:` blocks — the strongest tool for truly *different* layouts per device (tablet vs phone vs desktop) in one view. `grid-template-areas` for mockup-faithful placement. | Replaces sections view (no drag-drop editing). Unused today. |
| vertical-stack-in-card | `custom:vertical-stack-in-card` | v1.1.4 | Merge several cards into one visual card. | Used on Deliveries; needs card_mod to strip inner borders. |
| simple-swipe-card | `custom:simple-swipe-card` | v3.1.0 | Swipeable carousel — good for phone to compress tablet-wide rows. | Unused. |
| auto-entities | `custom:auto-entities` | v1.16.1 | Filter-driven lists (open doors, low batteries). Wraps any card. | Used on Security. Could replace the hand-maintained battery/tamper dicts. |
| Bubble Card pop-ups | `custom:bubble-card` `card_type: pop-up` | v3.4.3 | Hash-triggered (`#kitchen`) bottom-sheet pop-ups; native-app feel on phone/tablet. Also has Module Store for shared styles. | Installed, unused. |
| browser_mod | integration + `custom:popup-card` | v3.4.2 | Per-device identity (each tablet/phone/desktop browser is an entity), popups, per-browser theme/sidebar/header hiding, kiosk-like control of the wall tablet. | Used for the Spotify popup. Only real way to make HA know *which device* is viewing. |
| card-mod | `card_mod:` key + theme `card-mod-*` | v4.2.1 | Escape hatch for any CSS. Theme-level `card-mod-card`/`card-mod-root`/`card-mod-view` give global rules. | Loaded via `frontend.extra_module_url` **and** as a resource. Per-card card_mod is the main source of drift today. |
| config-template-card | `custom:config-template-card` | 2.2.0 (2.3.0 pending) | JS-templating any card's config. | Heavy; prefer native Jinja-capable cards first. Unused. |

## Controls & entity cards

| Component | Type string | Ver. | Tier | Use for | Notes |
| --- | --- | --- | --- | --- | --- |
| Tile (built-in) | `tile` | core | A | Default entity control; `features` (sliders, playback, etc.), `vertical`. | Used widely on Security/Entertainment. |
| Mushroom | `custom:mushroom-*-card` (entity, light, person, alarm-control-panel, template, chips, title, climate, cover, media-player, …) | v5.3.0 | A/B | Clean consistent look via `--mush-*` theme vars. v5 template card supports `color`, `features`. | Person + alarm + template used. Icons in template/alarm cards rendered blank in a screenshot-engine capture on 2026-11-23 — verify on real devices. |
| button-card | `custom:button-card` | v7.0.1 | C | Pixel-level custom tiles, `custom_fields`, JS `[[[ ]]]` templates, **`button_card_templates`** at dashboard root = reusable design components. `section_mode: true` for sections grids. | Only 1 use today (Spotify button). Best candidate for a house "component library". |
| Bubble Card | `custom:bubble-card` | v3.4.3 | B/C | Buttons, sliders, media, climate, cover, separators, horizontal button stacks; pop-ups. Mobile-first. | Unused. |
| Foundry Card | `custom:foundry-*` | v26.11.1 | C | Industrial/vintage gauges, thermostats, clocks. | Aesthetic clashes with Warm Home. Unused. |
| template-entity-row | `custom:template-entity-row` (row) | v1.4.1 | A | Arbitrary rows inside `entities`. | Last updated 2024. Unused. |
| secondaryinfo-entity-row | `custom:secondaryinfo-entity-row` (row) | 5.0 | A | Templated secondary line in rows. | Stale (2021); prefer template-entity-row or tile `state_content`. |

## Data display

| Component | Type string | Ver. | Tier | Notes |
| --- | --- | --- | --- | --- |
| gauge-card-pro | `custom:gauge-card-pro` | v2.5.0 | C | Gradient segments, Jinja value/colour. Used for UV + AQI (segment colours hardcoded). |
| mini-graph-card | `custom:mini-graph-card` | v0.13.0 | B/C | Sparkline/history. Unused. |
| clock-weather-card | `custom:clock-weather-card` | v3.1.0 | C | Clock + forecast — natural wall-tablet hero. Unused. |
| weather-radar-card | `custom:weather-radar-card` | v4.0.0 | D | Used on Home (NOAA, 320px fixed height). |
| ha-floorplan | `custom:floorplan-card` | v1.1.5 | C (SVG + CSS you own) | Most design freedom of anything installed: your own SVG, entity-driven CSS classes. Best for tablet hero views. Unused. |

## Domain-specific

| Component | Type string | Ver. | Tier | Used? |
| --- | --- | --- | --- | --- |
| advanced-camera-card | `custom:advanced-camera-card` | v8.2.0 | D | No (Security uses `picture-entity`). |
| atomic-calendar-revive | `custom:atomic-calendar-revive` | v10.3.1 | D | Home view, styled with large card_mod block. |
| daylight-calendar-card | `custom:daylight-calendar-card` (file `skylight-calendar-card.js`) | v4.14.0 (v5.0.0 pending — major) | C | Calendar dashboard ×3. |
| TrashCard | `custom:trash-card` | 2.4.7 | A (Mushroom-based) | Home. |
| simple-timer-card | `custom:simple-timer-card` | v2.9.1 (2.9.2 pending) | C | Home (Alexa timers). |
| SpotifyPlus card | `custom:spotifyplus-card` | v1.0.77 | D | Entertainment popup. |
| vacuum-card | `custom:vacuum-card` | v2.12.0 | D | No. |
| Mail and Packages card | `custom:mail-and-packages-card` | 0.06 | D | No. Stale (2021). |
| tracking-number-card | `custom:tracking-number-card` | manual install (not HACS) | D | Deliveries. |
| sunset-predictor-card | `/local/sunset-predictor-card.js` | manual install (not HACS), origin unknown | ? | Not referenced by any dashboard. |
| Inter font (not a card) | `/local/fonts/inter.css?v=1` (`css` resource) | repo `www/fonts/`, added 2026-11-23 | n/a | Loads the Walnut theme's `--wn-font`. Bump `?v=` when the file changes. |

## Target devices

Every design must work on all three. Same content everywhere, with the layout adapted per device.

| Device | Client | CSS viewport (W×H, measured by browser_mod) | Notes |
| --- | --- | --- | --- |
| Apolosign 15.6" wall tablet, **landscape** | HA Companion app (Android), dedicated non-admin user | **1715×965** | Kiosk: browser_mod keeps the sidebar collapsed (still expandable) and controls the sidebar items. Roles: ambient status, home control. Used by Jordan and guests: big touch targets, readable across the room. |
| Samsung Galaxy S24+ | HA Companion app, portrait | **384×798** | |
| 3840×2160 desktop, 150% scaling, maximised | Browser | **2372×1294** | Wide: watch `max_columns` and runaway stretching. |

Screenshot every change at these three exact sizes with `ha_get_dashboard_screenshot`
(`width`/`height`). Don't use its presets (390×844 / 768×1024 / 1280×800): they don't
match any of these devices. The Mushroom icons that rendered blank in an engine capture
should be checked on a real device.
