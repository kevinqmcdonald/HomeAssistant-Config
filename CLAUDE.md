# CLAUDE.md

Home Assistant configuration, written in YAML. This repo **is** the live `/config` directory: changes go live when they are pushed and then pulled on the HA host (a Raspberry Pi running HA OS). The ha-mcp MCP server may also be connected, for reading or changing the live instance.

## How config is loaded

[configuration.yaml](configuration.yaml) wires everything together. Each folder uses a different include style, so the file shape has to match:

| Folder | Include | File must contain |
| --- | --- | --- |
| `automation/` | `!include_dir_merge_list` | a **list** of automations |
| `scene/` | `!include_dir_merge_list` | a **list** of scenes |
| `sensor/` | `!include_dir_merge_list` | a **list** of platform sensors |
| `script/` | `!include_dir_merge_named` | a **mapping** of `script_id: {...}` |
| `themes/` | `!include_dir_merge_named` | a **mapping** of `Theme Name: {...}` |
| `packages/` | `!include_dir_named` | a mapping of integration domains (`template:`, `scene:`, `binary_sensor:`…). The filename becomes the package name. |
| `dashboards/` | not included by `configuration.yaml`; each top-level file is registered under `lovelace: dashboards:` as a YAML-mode dashboard | a Lovelace dashboard config (`views:`). `components/` and `views/` hold `!include`d pieces. |

- Automations, scripts and scenes each have a `ui` key (`automations.yaml`, `scripts.yaml`, `scenes.yaml`) and a `yaml` key (the matching folder). **Keep the three root files empty** (`[]` / `{}`). They exist only so the HA UI editor has somewhere to write. Never put hand-written config in them.
- IDs must be unique across both the UI and YAML sources.

## Where new things go

**Folders first.** Put new automations, scripts, scenes and sensors in `automation/`, `script/`, `scene/` or `sensor/`, grouped into a file by topic (e.g. `automation/air_quality.yaml`). Use `packages/` only for a self-contained subsystem whose helpers, templates, scenes and automations belong together (e.g. `packages/security.yaml`, `packages/primary_bathroom_lighting.yaml`).

## Conventions

- **IDs:** use readable snake_case slugs for every `id` and `unique_id` (e.g. `primary_bathroom_standard`). Some older items have UUIDs. Leave those alone unless asked, because changing an ID orphans the entity's registry entry and history.
- **File header:** every YAML file starts with the `#####` / `# ---` comment banner and a one-line description. Match the existing style.
- **Package headers document the hardware and the reasoning.** Follow [packages/primary_bathroom_lighting.yaml](packages/primary_bathroom_lighting.yaml): list device models, protocol details, and the reason behind any non-obvious choice (e.g. "don't add HA automations for tap/hold, the Zigbee binding handles it"). Read these headers before changing a package. They record constraints you can't see in the logic.
- Use current HA syntax: `triggers:` / `trigger:`, `conditions:`, `actions:` / `action:` (not `platform:` / `service:`).
- Templates should give defaults (`| int(0)`, `| float(0)`) so they don't break while an entity is unavailable.
- Use `!secret` for anything sensitive. Never write real secrets into a tracked file.

## .gitignore is a whitelist

[.gitignore](.gitignore) starts with `*` and lets through only listed folders plus `*.yaml`, `*.md`, `.gitignore` and `.gitkeep`. Two consequences:
- A **new top-level folder** or a **new file type** (e.g. `.yamllint`, `.py`, `.jinja`) is silently ignored until it's added to the whitelist. Check `git status` after creating one.
- `secrets.yaml`, `custom_components/`, `www/community/`, `ip_bans.yaml`, `known_devices.yaml` and `*.local.md` are deliberately excluded. Don't un-ignore them.

## Dashboards

- Before designing or building a dashboard, read [.claude/reference/dashboard-catalog.md](.claude/reference/dashboard-catalog.md) (installed cards and how each one takes styling) and [.claude/reference/dashboard-style-guide.md](.claude/reference/dashboard-style-guide.md) (tokens, card preference order, layout rules). Only use cards listed there. A new HACS install must be proposed explicitly.
- Workflow: `/dashboard-design` (mockup → feasibility table → HTML preview), then `/dashboard-build` (YAML → scratch dashboard → `dashboard-lint` + `dashboard-reviewer` agents). Deploy with `/deploy`.
- Target devices (CSS viewport): tablet 1715×965, phone 384×798, desktop 2372×1294.
- **Scratch exception:** Claude may create, update and delete the hidden storage dashboard `dashboard-scratch` through ha-mcp without asking. Every other live dashboard, theme or resource change still needs approval.

## Validating changes

1. **Lint locally:** run `yamllint .` from the repo root (config in [.yamllint](.yamllint)). It must exit 0. The two line-length warnings in the vendored `blueprints/script/TheAppleFreak/notify_alexa.yaml` are expected, so don't edit third-party blueprints. HA tags such as `!include`, `!secret` and `!include_dir_*` are valid. Don't "fix" them.
   - Line endings are LF everywhere ([.gitattributes](.gitattributes)) because HA runs on Linux. Don't write CRLF files.
   - Run the tooling tests: `python -m unittest discover -s .claude/scripts/tests`.
2. **Run an HA config check** on the live instance (via ha-mcp, or `ha core check` on the host) once the change is deployed and before any restart or reload.
3. **Never restart Home Assistant or reload integrations, automations, scripts or scenes without asking first.** It affects a live house.
4. Never commit, push, or change the live instance through ha-mcp without being asked.

## Key external dependencies

- **HACS** with card-mod (loaded through `frontend.extra_module_url`). Every theme in `themes/` sets `card-mod-theme`.
- **Alexa Media Player** (custom component), called through `script.send_notification_to_alexa`. That script is built from the [TheAppleFreak notify_alexa blueprint](blueprints/script/TheAppleFreak/notify_alexa.yaml). Use it for announcements instead of calling `notify.alexa_media_*` directly.
- **ZHA** on a Home Assistant Connect ZBT coordinator (Inovelli switches, Hue bulbs). Zigbee group bindings handle some behavior with no HA involvement. Package headers say where.
- **Nest** (thermostat, `nest.set_fan_timer`) and **SleepNumber** (bed positions in the bedroom scenes).
