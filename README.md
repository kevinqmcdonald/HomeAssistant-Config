Live view of the `config/` directory my Home Assistant instance loads every night. Use this README as a map when you want to jump directly into the most interesting packages, automations, and supporting assets.

### Quick navigation
- You are here: `config/` (configuration root)
- Directory highlights: [packages](packages), [automation](automation), [script](script), [scene](scene), [templates](templates), [dashboards](dashboards), [www](www), [custom_components](custom_components)

### What this folder is (and isn't)
- Every YAML file here is live and version-controlled; anything missing is intentionally ignored via `.gitignore` (databases, logs, caches, etc.).
- This is a split-configuration layout: `configuration.yaml` simply includes the files and directories documented here so changes are easy to isolate.

### How the config is organized
- **Packages (`packages/`)** – complete subsystems that bundle sensors, switches, automations, scripts, and lovelace assets for a single feature (alarm, garage, water shutoff, etc.).
- **Automations (`automation/`)** – event-driven YAML broken out by area or device; the legacy `automations.yaml` remains for UI-created flows.
- **Scripts & scenes (`script/`, `scene/`)** – curated lighting, notification, and AGENT engineer handoff helpers used by presence, holiday, seasonal, and infrastructure routines.
- **Templates (`templates/`)** – Jinja helpers and speech templates reused by the notify/speech engines.
- **Dashboards (`dashboards/`)** – YAML-managed Lovelace dashboards and UI resources (generated from storage, then maintained as code).
- **www/ + custom components** – branding assets, floorplans, and any custom components the core install depends on.
- **Custom Sidebar** – `www/custom-sidebar-config.yaml` controls the bottom Developer Tools shortcut; HACS owns the plugin files under `www/community/custom-sidebar`.

### Featured automations by section
| Section            | Why start here                                                                         | Featured automation(s) |
| ------------------ | -------------------------------------------------------------------------------------- | ---------------------- |
| Packages           | Self-contained subsystems that highlight patterns like combined alerts + actions.      |                        |
| Automations        | Real-world triggers that tie Zwave, MQTT, and REST sensors into the rest of the house. |                        |
| Scripts            | Reusable building blocks for lighting, notifications, safety responses, etc.           |                        |
| Scenes             | Seasonal and ambiance presets that the scripts and automations call into.              |                        |
| Templates & Speech | Human-friendly voice briefings and templated responses.                                |                        |
| Dashboards & Media | UI chrome, floorplans, sound bites, and automation assets.                             |                        |

### Gear tied to these automations
Only including devices that have active references in the files above.

| Device | What it drives (friendly name -> file) | Buy |
| ------ | -------------------------------------- | --- |
|        |                                        |     |

### Tips for re-use
- Copy a package folder and adjust entity IDs in one place instead of hunting through automations.
- Use the scripts and scenes as examples of how to break complicated flows into composable blocks.
- The `www/` assets are ideal references when building your own Lovelace floorplans or dashboards.
