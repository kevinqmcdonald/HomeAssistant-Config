"""Resolve a YAML-mode Lovelace dashboard (with HA include tags) into plain JSON.

Used by /dashboard-build to push a draft to the scratch dashboard through ha-mcp,
and by lint_dashboard.py to read the full config a dashboard file expands to.

Supported tags, resolved relative to the file that contains them (as HA does):
  !include FILE
  !include_dir_list DIR          -> list of each file's content (sorted by name)
  !include_dir_named DIR         -> {filename_stem: content}
  !include_dir_merge_list DIR    -> concatenation of each file's list
  !include_dir_merge_named DIR   -> merge of each file's mapping
!secret and any other tag raise DashboardLoadError: dashboards must not hold secrets,
and a silently dropped value would push a broken draft.

Usage (from the repo root):
  python .claude/scripts/render_dashboard.py dashboards/home.yaml
  python .claude/scripts/render_dashboard.py dashboards/home.yaml --theme Walnut --out render.json
"""
import argparse
import json
import os
import sys

import yaml  # PyYAML ships with yamllint


class DashboardLoadError(Exception):
    """A dashboard file could not be resolved."""


def _yaml_files(directory):
    if not os.path.isdir(directory):
        raise DashboardLoadError(f"include directory not found: {directory}")
    return [
        os.path.join(directory, name)
        for name in sorted(os.listdir(directory))
        if name.endswith((".yaml", ".yml")) and os.path.isfile(os.path.join(directory, name))
    ]


class _Resolver:
    def __init__(self):
        self.files = []
        self._open = []

    def load(self, path):
        path = os.path.normpath(os.path.abspath(path))
        if path in self._open:
            chain = " -> ".join(self._open + [path])
            raise DashboardLoadError(f"include cycle: {chain}")
        if not os.path.isfile(path):
            where = f" (included from {self._open[-1]})" if self._open else ""
            raise DashboardLoadError(f"file not found: {path}{where}")
        self._open.append(path)
        if path not in self.files:
            self.files.append(path)
        try:
            with open(path, encoding="utf-8") as fh:
                return yaml.load(fh, Loader=self._loader_for(os.path.dirname(path)))
        except yaml.YAMLError as err:
            raise DashboardLoadError(f"YAML error in {path}: {err}") from err
        finally:
            self._open.pop()

    def _loader_for(self, base):
        resolver = self

        class Loader(yaml.SafeLoader):
            pass

        def target(loader, node):
            return os.path.join(base, loader.construct_scalar(node))

        def include(loader, node):
            return resolver.load(target(loader, node))

        def dir_list(loader, node):
            return [resolver.load(f) for f in _yaml_files(target(loader, node))]

        def dir_named(loader, node):
            return {
                os.path.splitext(os.path.basename(f))[0]: resolver.load(f)
                for f in _yaml_files(target(loader, node))
            }

        def dir_merge_list(loader, node):
            merged = []
            for f in _yaml_files(target(loader, node)):
                merged.extend(resolver.load(f) or [])
            return merged

        def dir_merge_named(loader, node):
            merged = {}
            for f in _yaml_files(target(loader, node)):
                merged.update(resolver.load(f) or {})
            return merged

        def reject(loader, suffix, node):
            raise DashboardLoadError(
                f"unsupported tag !{suffix} in {resolver._open[-1]} line {node.start_mark.line + 1}"
                + (" (dashboards must not reference secrets)" if suffix == "secret" else "")
            )

        Loader.add_constructor("!include", include)
        Loader.add_constructor("!include_dir_list", dir_list)
        Loader.add_constructor("!include_dir_named", dir_named)
        Loader.add_constructor("!include_dir_merge_list", dir_merge_list)
        Loader.add_constructor("!include_dir_merge_named", dir_merge_named)
        Loader.add_multi_constructor("!", reject)
        return Loader


def load_dashboard_with_files(path):
    """Return (resolved config, absolute paths of every file read, root first)."""
    resolver = _Resolver()
    config = resolver.load(path)
    return config, list(resolver.files)


def load_dashboard(path):
    """Return the fully resolved dashboard config for a YAML file."""
    return load_dashboard_with_files(path)[0]


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file")
    parser.add_argument("--theme", help="set this theme on every view that has none")
    parser.add_argument("--out", help="write JSON here instead of stdout")
    args = parser.parse_args(argv)
    try:
        config = load_dashboard(args.file)
    except DashboardLoadError as err:
        print(f"render_dashboard: {err}", file=sys.stderr)
        return 2
    if args.theme and isinstance(config, dict):
        for view in config.get("views") or []:
            if isinstance(view, dict) and "theme" not in view:
                view["theme"] = args.theme
    text = json.dumps(config, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
