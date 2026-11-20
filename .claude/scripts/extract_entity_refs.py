"""Extract entity_id and service references from Home Assistant YAML.

Used by the entity-ref-checker subagent. Prints JSON:

  {
    "scope": [files scanned for references],
    "entities": {"sensor.foo": ["path:line", ...], ...},
    "services": {"light.turn_on": ["path:line", ...], ...},
    "defined_in_repo": {"script.bar": "script/alexa.yaml", ...}
  }

"defined_in_repo" is a best-effort list of entity_ids that this repo's YAML
creates (scripts, automations, scenes, template/group sensors, input_* helpers).
IDs derived from a name/alias are guesses: HA slugifies the name the first
time it registers the entity, so a later rename can make them differ.

Usage (from the repo root):
  python .claude/scripts/extract_entity_refs.py            # files changed vs origin/main
  python .claude/scripts/extract_entity_refs.py --all      # every config YAML
  python .claude/scripts/extract_entity_refs.py FILE ...   # specific files
"""
import json
import os
import re
import subprocess
import sys

import yaml  # PyYAML ships with yamllint

ENTITY_DOMAINS = (
    "air_quality alarm_control_panel assist_satellite automation binary_sensor button "
    "calendar camera climate conversation counter cover date datetime device_tracker "
    "event fan group humidifier image image_processing input_boolean input_button "
    "input_datetime input_number input_select input_text lawn_mower light lock "
    "media_player notify number person remote scene schedule script select sensor "
    "siren stt sun switch text time timer todo tts update vacuum valve wake_word "
    "water_heater weather zone"
).split()

ID_RE = re.compile(r"(?<![\w.])(" + "|".join(ENTITY_DOMAINS) + r")\.([a-z0-9_]+)\b(?!\()")
SERVICE_LINE_RE = re.compile(r"^\s*-?\s*(?:action|service)\s*:\s*['\"]?([a-z0-9_]+\.[a-z0-9_]+)")
FILE_SUFFIXES = {"yaml", "yml", "json", "py", "md", "txt", "jinja", "log"}
SKIP_DIRS = ("blueprints/", ".claude/", "custom_components/", "www/", ".storage/")
UI_FILES = {"automations.yaml", "scripts.yaml", "scenes.yaml"}


class AnyTagLoader(yaml.SafeLoader):
    """SafeLoader that turns HA tags (!include, !secret, !input, ...) into None."""


AnyTagLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def slugify(text: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(text).lower())).strip("_")


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return [l.strip() for l in r.stdout.splitlines() if l.strip()] if r.returncode == 0 else []


def is_config_yaml(path: str) -> bool:
    p = path.replace("\\", "/")
    return p.endswith((".yaml", ".yml")) and not p.startswith(SKIP_DIRS) and os.path.isfile(p)


def changed_files():
    files = set(git("diff", "--name-only", "origin/main"))
    files |= set(git("ls-files", "--others", "--exclude-standard"))
    return sorted(f for f in files if is_config_yaml(f))


def all_files():
    return sorted(f for f in git("ls-files") if is_config_yaml(f))


def scan_refs(files):
    entities, services = {}, {}
    for path in files:
        with open(path, encoding="utf-8") as fh:
            for n, raw in enumerate(fh, 1):
                line = re.sub(r"(^|\s)#.*$", "", raw)  # drop comments
                if not line.strip():
                    continue
                where = f"{path}:{n}"
                svc = SERVICE_LINE_RE.match(line)
                svc_id = svc.group(1) if svc else None
                if svc_id:
                    services.setdefault(svc_id, []).append(where)
                for m in ID_RE.finditer(line):
                    ident = f"{m.group(1)}.{m.group(2)}"
                    if ident == svc_id or m.group(2) in FILE_SUFFIXES:
                        continue
                    entities.setdefault(ident, []).append(where)
    return entities, services


def add_defs_from_domain(defs, domain, value, src):
    """Record entity_ids a top-level/package domain block creates."""
    if domain == "template" and isinstance(value, list):
        for block in value:
            if not isinstance(block, dict):
                continue
            for sub, items in block.items():
                if sub in ("trigger", "triggers", "condition", "conditions", "action", "actions"):
                    continue
                for item in items if isinstance(items, list) else []:
                    if isinstance(item, dict):
                        eid = item.get("default_entity_id")
                        if eid:
                            defs[eid] = src
                        elif item.get("name"):
                            defs[f"{sub}.{slugify(item['name'])}"] = src
        return
    if isinstance(value, dict) and domain in ENTITY_DOMAINS:
        for key in value:
            defs[f"{domain}.{key}"] = src
    elif isinstance(value, list) and domain in ENTITY_DOMAINS:
        for item in value:
            if isinstance(item, dict):
                label = item.get("alias") or item.get("name")
                if label:
                    defs[f"{domain}.{slugify(label)}"] = src
                if domain == "automation" and item.get("id") and not label:
                    defs[f"automation.{slugify(item['id'])}"] = src


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.load(fh, Loader=AnyTagLoader)
    except yaml.YAMLError:
        return None


def collect_defs():
    defs = {}
    folder_domain = {"automation/": "automation", "scene/": "scene", "sensor/": "sensor", "script/": "script"}
    for path in all_files():
        p = path.replace("\\", "/")
        if p in UI_FILES:
            continue
        data = load(p)
        if data is None:
            continue
        domain = next((d for prefix, d in folder_domain.items() if p.startswith(prefix)), None)
        if domain:
            add_defs_from_domain(defs, domain, data, p)
        elif (p.startswith("packages/") or p == "configuration.yaml") and isinstance(data, dict):
            for dom, value in data.items():
                add_defs_from_domain(defs, dom, value, p)
    return defs


def main(argv):
    if "--all" in argv:
        files = all_files()
    elif argv:
        files = [f for f in argv if is_config_yaml(f) or os.path.isfile(f)]
    else:
        files = changed_files()
    entities, services = scan_refs(files)
    print(json.dumps({
        "scope": files,
        "entities": dict(sorted(entities.items())),
        "services": dict(sorted(services.items())),
        "defined_in_repo": dict(sorted(collect_defs().items())),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
