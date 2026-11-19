Live collection of plug-and-play Home Assistant packages. Each YAML file in this folder bundles sensors, helpers, automations, scripts, and Lovelace assets needed for a specific subsystem so you can drop it into `configuration.yaml` with a single `packages:` include.

### Why packages exist
- Keep everything for a subsystem (alarm, garage, water shutoff, etc.) in one file, which makes versioning, troubleshooting, and sharing dramatically easier.
- Encapsulate helpers (input_booleans, sensors, scripts) so enabling/disabling a capability is as simple as moving one file in or out of the packages/ include.
- Document hardware dependencies right next to the logic so you remember which gear keeps each automation alive.
