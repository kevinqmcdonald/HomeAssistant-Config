"""PreToolUse hook: Claude may never deploy on its own.

The Pi's Git pull add-on polls origin/main and auto-restarts Home Assistant, so
anything that lands commits on GitHub is a deploy. This hook forces a human
permission prompt ("ask") for:

- git push (any form: git -C <dir> push, git.exe push, --all, --mirror, ...)
- gh pr merge / gh repo sync / gh api calls that merge (they update main on GitHub)

"ask" overrides allow rules and auto mode, so the push only runs after the user
approves it in the UI. Every other command passes through untouched.
"""
import json
import re
import sys

# git, then any global options (-C dir, -c k=v, --git-dir=..., --no-pager), then push
GIT_PUSH = re.compile(
    r"""\bgit(?:\.exe)?["']?
        (?:\s+(?:-[Cc]\s+(?:"[^"]*"|'[^']*'|\S+)|--[\w-]+(?:=\S+)?))*
        \s+push\b""",
    re.IGNORECASE | re.VERBOSE,
)
GH_MERGE = re.compile(
    r"\bgh(?:\.exe)?\s+(?:pr\s+merge|repo\s+sync)\b|\bgh(?:\.exe)?\s+api\b[^|;&]*\bmerges?\b",
    re.IGNORECASE,
)


def main() -> int:
    data = json.load(sys.stdin)
    if data.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    command = (data.get("tool_input") or {}).get("command") or ""

    if GIT_PUSH.search(command):
        what = "git push"
    elif GH_MERGE.search(command):
        what = "a GitHub merge"
    else:
        return 0

    reason = (
        f"This command runs {what}. Pushing to main deploys: the Pi's Git pull "
        "add-on pulls within ~5 min and auto-restarts Home Assistant. "
        "Only approve if you asked for this deploy."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
