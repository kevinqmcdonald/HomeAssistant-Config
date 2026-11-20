"""PreToolUse hook: block Claude from changing files that must not be hand-edited.

- secrets.yaml           -> real secrets; never written by Claude
- blueprints/**          -> vendored third-party blueprints
- automations.yaml, scripts.yaml, scenes.yaml (repo root)
                         -> HA UI editor targets; must stay empty

Edit/Write: blocks by file_path.
Bash/PowerShell: blocks a command that names a protected path AND looks like a
write (redirect, sed -i, tee, mv/cp/rm, Set-Content, git checkout, ...).
Reads such as `git diff automations.yaml` or `cat scenes.yaml` are allowed.
This is a heuristic guard against accidents, not a security boundary.

Exit 2 blocks the tool call and feeds stderr back to Claude.
"""
import json
import os
import re
import sys

UI_FILES = {"automations.yaml", "scripts.yaml", "scenes.yaml"}

# Path-like tokens that could name a protected file.
PATH_TOKEN = re.compile(
    r"""[^\s"'`<>|;&(),]*(?:secrets\.yaml|blueprints(?:[/\\][^\s"'`<>|;&(),]*)?|(?:automations|scripts|scenes)\.yaml)""",
    re.IGNORECASE,
)

# Harmless redirects to strip before looking for write redirects.
SAFE_REDIRECTS = re.compile(r"\d*>&\d+|\d*>>?\s*(?:/dev/null|\$null|nul\b)", re.IGNORECASE)

WRITE_PATTERNS = re.compile(
    r"""
    >                                             # any remaining redirect
    | \bsed\b[^|;&]*\s(?:-i|--in-place)           # sed in-place
    | \bperl\b[^|;&]*\s-[a-z]*i                   # perl -i
    | \b(?:yq|jq)\b[^|;&]*\s-i\b                  # yq/jq in-place
    | \b(?:tee|mv|cp|rm|truncate|touch|dd|install|ln|rsync)\b
    | \bgit\s+(?:checkout|restore|rm|mv|reset|stash|apply|am)\b
    | \b(?:set|add|clear)-content\b
    | \bout-file\b
    | \b(?:remove|move|copy|rename|new)-item\b
    | \b(?:sc|ac|ri|del|erase|move|copy|ren|ni)\s
    | \bwrite                                     # .write(), write_text, WriteAllText
    """,
    re.IGNORECASE | re.VERBOSE,
)


def norm(p: str) -> str:
    p = p.replace("\\", "/")
    m = re.match(r"^/([a-zA-Z])/(.*)", p)  # Git Bash style /c/Users/...
    if m:
        p = f"{m.group(1)}:/{m.group(2)}"
    return os.path.normcase(os.path.abspath(p)).replace("\\", "/")


def protected_reason(rel: str):
    if rel.split("/")[-1] == "secrets.yaml":
        return "secrets.yaml holds real secrets and is never edited by Claude."
    if rel == "blueprints" or rel.startswith("blueprints/"):
        return "blueprints/ holds vendored third-party blueprints; don't edit them."
    if rel in UI_FILES:
        return (
            f"{rel} is the HA UI editor's target and must stay empty. "
            "Put hand-written config in the matching folder (automation/, script/, scene/)."
        )
    return None


def rel_to_root(path: str, root: str, cwd: str):
    if not re.match(r"^(?:[a-zA-Z]:|/|\\)", path):
        path = os.path.join(cwd, path)
    target = norm(path)
    if target == root:
        return None
    if not target.startswith(root + "/"):
        return None  # outside the repo (scratchpad, memory, etc.)
    return target[len(root) + 1:]


def main() -> int:
    data = json.load(sys.stdin)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    root_raw = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    root = norm(root_raw)
    cwd = data.get("cwd") or root_raw

    if tool in ("Bash", "PowerShell"):
        command = tool_input.get("command") or ""
        if not WRITE_PATTERNS.search(SAFE_REDIRECTS.sub(" ", command)):
            return 0
        for token in PATH_TOKEN.findall(command):
            rel = rel_to_root(token, root, cwd)
            reason = rel and protected_reason(rel)
            if reason:
                print(
                    f"Blocked {tool} command that may modify {rel}: {reason} "
                    "If this is really a read-only command, rewrite it without "
                    "redirects or write commands, or use the Read tool.",
                    file=sys.stderr,
                )
                return 2
        return 0

    path = tool_input.get("file_path") or ""
    if not path:
        return 0
    rel = rel_to_root(path, root, cwd)
    reason = rel and protected_reason(rel)
    if reason:
        print(f"Blocked edit to {rel}: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
