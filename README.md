# Home Assistant Config

My Home Assistant configuration, written in YAML and organized by type, with self-contained packages for larger subsystems.

## Setup

- **Host:** Raspberry Pi 4 running Home Assistant OS
- **Zigbee:** ZHA with a Home Assistant Connect ZBT coordinator
- **Frontend:** [HACS](https://hacs.xyz/) with [card-mod](https://github.com/thomasloven/lovelace-card-mod) for themes
- **Deployment:** the HA `/config` directory is a clone of this repo. Changes are pushed here, then pulled on the host.

## Layout

| Path | What's in it | Loaded by |
| --- | --- | --- |
| [configuration.yaml](configuration.yaml) | Core config that wires everything together | — |
| [automation/](automation/) | YAML automations, one file per topic | `!include_dir_merge_list` |
| [script/](script/) | Reusable scripts called by automations | `!include_dir_merge_named` |
| [scene/](scene/) | Lighting and ambiance presets | `!include_dir_merge_list` |
| [sensor/](sensor/) | Standalone utility sensors | `!include_dir_merge_list` |
| [packages/](packages/) | Self-contained subsystems (security, media, a room's lighting) | `!include_dir_named` |
| [blueprints/](blueprints/) | Imported automation and script blueprints | HA blueprint loader |
| [themes/](themes/) | card-mod themes | `!include_dir_merge_named` |
| [logger.yaml](logger.yaml), [recorder.yaml](recorder.yaml) | Log levels and history retention | `!include` |

### UI and YAML side by side

Automations, scripts and scenes are each loaded twice under different keys:

```yaml
automation ui: !include automations.yaml          # written by the HA UI editor
automation yaml: !include_dir_merge_list automation  # hand-written, version-controlled
```

`automations.yaml`, `scripts.yaml` and `scenes.yaml` stay empty in the repo, so the UI editor keeps working without mixing its output into the hand-written files.

## Secrets and ignored files

[.gitignore](.gitignore) ignores **everything** by default and lets through only listed folders and the `*.yaml` / `*.md` file types. `secrets.yaml`, `custom_components/`, HACS downloads, the database and `.storage/` are never committed. Values that shouldn't be public use `!secret`.

## Using this as a reference

Feel free to borrow. Entity IDs are specific to my devices, so expect to rename them. The packages, especially [primary_bathroom_lighting.yaml](packages/primary_bathroom_lighting.yaml), record their hardware dependencies and design choices in a header comment, which is a good place to start.
