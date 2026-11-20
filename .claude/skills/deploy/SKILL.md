---
name: deploy
description: Use when the user runs /deploy or asks to deploy, ship, or push Home Assistant config changes to the live Pi. Covers linting, commit, the push that triggers the Git Pull add-on, and post-deploy verification.
disable-model-invocation: true
---

# Deploy HA config to the Pi

## How deployment actually works here

The Pi runs the **Git pull add-on** (`core_git_pull`). It polls `origin/main` every
**300 s**, and `auto_restart` is **on**. On each poll that finds new commits, it:

1. pulls into `/config`,
2. runs its own HA config check,
3. **restarts Home Assistant** if the check passes, unless every changed file
   matches `restart_ignore`.

**So `git push` to `main` is the restart button.** CLAUDE.md says never to restart HA
without asking, which means the push is the step that needs the user's explicit
go-ahead. Nothing after the push can be undone before the restart happens.

Re-read the add-on config at the start of every deploy, because the user may have
changed it: `ha_get_app(slug="core_git_pull")` → `options.auto_restart`,
`options.restart_ignore`, `options.repeat.interval`, `options.git_branch`. If any
of them differ from the values above, follow what the live config says and tell the
user what changed.

## Steps

### 1. Preflight (local, read-only)

- `git branch --show-current` must be `main`, which is the branch the add-on tracks.
  If it isn't, stop and ask. Don't merge or switch on your own.
- `git fetch origin` then `git status -sb`. If local is behind `origin/main`, stop and
  ask. Someone may have pushed from elsewhere.
- **Lint:** `yamllint .` from the repo root must exit 0. The two line-length warnings
  in `blueprints/script/TheAppleFreak/notify_alexa.yaml` are expected. Fix any other
  problem before continuing.
- **Static HA check:** run the `homeassistant-config:ha-check` skill on the repo. Fix
  any errors it reports. Report warnings to the user.
- **Whitelist trap:** `.gitignore` is a whitelist, so a new folder or file type can
  silently drop out of the commit. Run `git status --short --ignored` and look for
  ignored files that ought to be deployed. Ignored files that are expected:
  `secrets.yaml`, `custom_components/`, `www/community/`, `ip_bans.yaml`,
  `known_devices.yaml`, `*.local.md`, `*.local.json`. If anything else is ignored,
  stop and ask whether to whitelist it.
- **Secrets:** `secrets.yaml` is not in git, so the Pi's copy is the only one. Find new
  secret references with
  `git diff origin/main -- . ':!*.md' | grep '^+.*!secret'`. If there are any, list
  them and ask the user to confirm that each key already exists in the Pi's
  `secrets.yaml`. A missing key fails the add-on's config check, and the config is
  then pulled but HA isn't restarted.

### 2. Classify the change and ask for go-ahead

List the files that will ship: the staged and unstaged changes you intend to commit,
plus any local commits not yet on `origin/main`
(`git diff --name-only origin/main`, plus working-tree changes).

For each file, check it against `restart_ignore`. An entry ending in `/` is a
directory prefix. Every other entry is an exact path.

- **Any file not ignored** → the push **will restart HA** within about one poll
  interval.
- **All files ignored** (e.g. only `.claude/`, `CLAUDE.md`, `README.md`) → the push
  pulls without a restart.

Then ask the user **one** question, using AskUserQuestion, that gives:
- the file list and a one-line summary of what changes,
- the restart verdict, in plain words: "This will restart Home Assistant within
  ~5 minutes of the push" or "No restart; docs or tooling only",
- the proposed commit message.

Options: **Deploy now** / **Commit only, don't push** / **Cancel**. Don't push on
anything other than an explicit "Deploy now".

### 3. Commit and push

- Stage only the files you listed. Don't use `git add -A` or `git add .`.
- Commit message: an imperative summary line in the repo's existing style ("Add
  basement humidity alert"), and a body if the why isn't obvious. End it with the
  co-author trailer this session specifies.
- `git push origin main`. The `guard_push.py` hook always turns a push into a
  permission prompt, even in auto mode, so the user approves it a second time in
  the UI. That's expected. If they decline, stop: the commit stays local. Never try
  to get around the prompt (with a different command, a script, `gh`, or the
  GitHub API). If the push is rejected, stop and report. Never force-push.
- Note the time of the push.

### 4. Watch the add-on pick it up

The pull happens at the next poll, no later than `interval` seconds after the
previous poll. To work out when that is, read the add-on log:
`ha_get_logs(source="supervisor", slug="core_git_pull", limit=40)` and take the most
recent `Start git fetch...` timestamp, plus the interval.

Tell the user when to expect the pull. Then wait for it with a Monitor until-loop
on the clock, about 30 s past the expected poll; don't use a foreground sleep. After
that, read the add-on log again.

What to look for, newest first:

| Log shows | Meaning | Next |
| --- | --- | --- |
| `Nothing has changed.` after your push time | The poll didn't see your commit | Check that `origin/main` has your commit. Wait one more interval. |
| Config check failure / "does not pass the config check" | The config was pulled, but HA was **not** restarted. The Pi is now running old config, with broken config on disk. | Report the error verbatim. Fix it locally and redeploy. Don't restart HA. |
| Restart message | HA is restarting | Go to step 5 |
| Only ignored files changed / no restart required | Done, no restart | Go to step 5 (logs only) |

Speeding it up is optional. Restarting the add-on (`ha_manage_app(slug="core_git_pull",
action="restart")`) pulls straight away, and it **also triggers the HA restart
straight away**. Only offer it as a choice. Don't do it unless the user picks it.

### 5. Verify after restart

HA takes about 1–3 minutes to come back on a Pi. Then:

- `ha_get_overview` or `ha_get_system_health` should respond.
- `ha_get_logs(source="system")`: list any ERROR or WARNING entries that first
  occurred after the restart, especially from the domains you touched (automation,
  template, script, scene, the package's integrations).
- For new or renamed automations, scripts and scenes, check with `ha_search` or
  `ha_get_state` that the entities exist and aren't `unavailable`.

Finish with a short report: the commit hash, whether HA restarted, any new errors, and
anything the user still has to do (such as adding a secret on the Pi).

## Common mistakes

| Mistake | Why it's wrong |
| --- | --- |
| Pushing first and asking afterwards | The push is the restart. There's nothing left to ask about. |
| Calling `ha_restart` or a reload after the deploy "to be safe" | The add-on already restarted HA. A second restart affects the house twice. |
| Treating a failed add-on config check as "nothing happened" | The broken config is now on disk on the Pi. The next manual restart will load it. |
| `git add -A` | Picks up stray files, and the whitelist may silently drop the files you meant to ship. |
| Skipping the secret check because yamllint passed | yamllint can't see the Pi's `secrets.yaml`. |
