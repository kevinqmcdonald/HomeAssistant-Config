"""Static lint for YAML-mode Lovelace dashboards.

Used by the dashboard-lint agent. Checks a dashboard (and every file it includes)
against the card allowlist in .claude/reference/installed-cards.yaml and the style
guide's rules. Prints JSON:

  {"findings": [{"rule", "severity", "file", "where", "message"}, ...],
   "errors": N, "warnings": M}

Rules:
  unknown-card-type     (error)   custom: card type not in the allowlist
  hardcoded-color       (error)   hex / rgb() / hsl() literal; colours belong in themes/
                                  (rgba(var(--x), a) is fine; skip a line with
                                  "# lint-ignore: hardcoded-color")
  card-mod-not-allowed  (error)   card_mod on a card that should follow the theme
  card-mod-used         (warning) card_mod on a tier-D card (allowed, but kept visible)
  view-missing-path     (warning) view has no stable `path`
  duplicated-template   (warning) same long Jinja string in 2+ places; use a template sensor

Exit status: 1 if any error, else 0.

Usage (from the repo root):
  python .claude/scripts/lint_dashboard.py                 # dashboards/*.yaml
  python .claude/scripts/lint_dashboard.py dashboards/home.yaml
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import sys
from dataclasses import asdict, dataclass

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_dashboard import DashboardLoadError, load_dashboard_with_files  # noqa: E402

DEFAULT_ALLOWLIST = os.path.join(".claude", "reference", "installed-cards.yaml")
HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
FUNC_RE = re.compile(r"\b(?:rgba?|hsla?)\((?!\s*var\()[^)]*\)?")
IGNORE_COLOR = "lint-ignore: hardcoded-color"
TEMPLATE_MIN_LEN = 80


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    where: str
    message: str


def load_allowlist(path=DEFAULT_ALLOWLIST):
    with open(path, encoding="utf-8") as fh:
        return (yaml.safe_load(fh) or {}).get("cards", [])


def _entry_for(card_type, allowlist):
    if not isinstance(card_type, str):
        return None
    for entry in allowlist:
        if fnmatch.fnmatchcase(card_type, entry["type"]):
            return entry
    return None


def _rel(path):
    try:
        return os.path.relpath(path).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def _walk(node, pointer=""):
    yield pointer, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, f"{pointer}/{str(key).replace('~', '~0').replace('/', '~1')}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{pointer}/{i}")


def _structure_findings(config, root, allowlist):
    findings = []
    templates = {}
    for pointer, node in _walk(config):
        if isinstance(node, str):
            if ("{{" in node or "{%" in node) and len(node) > TEMPLATE_MIN_LEN:
                templates.setdefault(node, []).append(pointer)
            continue
        if not isinstance(node, dict):
            continue
        card_type = node.get("type")
        entry = _entry_for(card_type, allowlist)
        if isinstance(card_type, str) and card_type.startswith("custom:") and entry is None:
            findings.append(Finding("unknown-card-type", "error", root, pointer,
                                    f"{card_type} is not in installed-cards.yaml"))
        if "card_mod" in node:
            if entry is not None and entry.get("card_mod") == "allowed":
                findings.append(Finding("card-mod-used", "warning", root, pointer,
                                        f"card_mod on {card_type} (tier D); use var(--wn-*) values only"))
            else:
                findings.append(Finding("card-mod-not-allowed", "error", root, pointer,
                                        f"card_mod on {card_type or 'untyped element'}; style it through the theme"))
    if isinstance(config, dict):
        for i, view in enumerate(config.get("views") or []):
            if isinstance(view, dict) and not view.get("path"):
                findings.append(Finding("view-missing-path", "warning", root, f"/views/{i}",
                                        "view has no path; screenshots and links need a stable one"))
    for text, pointers in templates.items():
        if len(pointers) > 1:
            findings.append(Finding("duplicated-template", "warning", root, ", ".join(pointers),
                                    "same Jinja template repeated; move it into a template sensor"))
    return findings


def _color_findings(path):
    findings = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            stripped = line.lstrip()
            if stripped.startswith("#") or IGNORE_COLOR in line:
                continue
            hits = HEX_RE.findall(line) + FUNC_RE.findall(line)
            if hits:
                findings.append(Finding("hardcoded-color", "error", _rel(path), f"line {n}",
                                        f"colour literal {hits[0]!r}; use a theme variable"))
    return findings


def lint_file(path, allowlist):
    config, files = load_dashboard_with_files(path)
    findings = _structure_findings(config, _rel(path), allowlist)
    for f in files:
        findings.extend(_color_findings(f))
    return findings


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*")
    parser.add_argument("--allowlist", default=DEFAULT_ALLOWLIST)
    args = parser.parse_args(argv)
    files = args.files or sorted(glob.glob(os.path.join("dashboards", "*.yaml")))
    allowlist = load_allowlist(args.allowlist)
    findings = []
    for path in files:
        try:
            findings.extend(lint_file(path, allowlist))
        except DashboardLoadError as err:
            findings.append(Finding("load-error", "error", _rel(path), "", str(err)))
    errors = sum(f.severity == "error" for f in findings)
    print(json.dumps({"findings": [asdict(f) for f in findings], "errors": errors,
                      "warnings": len(findings) - errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
