---
name: dashboard-build
description: Use when Kevin runs /dashboard-build, or asks to build, implement or render an approved dashboard design. Also use when changing an existing YAML dashboard under dashboards/ and he wants to see it on the scratch dashboard. Takes a design note from /dashboard-design.
---

# Dashboard build: design note → YAML → scratch → lint + review → hand-over

Builds an approved design as YAML in `dashboards/`, renders it on the hidden
`dashboard-scratch` dashboard, and checks it at the three device sizes. **It never
deploys**, and never writes real dashboards, themes or resources.

## Before you start

- **Design note required.** The argument is a path like `.claude/designs/<file>.md`. If
  there isn't one, or it has no `## Approved` section, stop. Ask Kevin to run
  `/dashboard-design` first. A small change to an existing YAML dashboard counts as
  approved if Kevin described it in this conversation. Write that description down as a
  short design note before building.
- Read the note, [dashboard-style-guide.md](../../reference/dashboard-style-guide.md),
  [installed-cards.yaml](../../reference/installed-cards.yaml) and
  [dashboards/components/button_card_templates.yaml](../../../dashboards/components/button_card_templates.yaml).
- Load the ha-mcp tools with ToolSearch. `ha_config_set_dashboard` needs a
  `BestPracticeKey`. Read it from `ha_get_skill_guide(file="references/dashboard-guide.md")`
  (it rotates hourly). Pass it with `MandatoryBPS=false`.

## Steps

**1. Write the YAML.**
- The file is `dashboards/<slug>.yaml`, with the repo's `#####` banner header. Large
  views go in `dashboards/views/<slug>/<view>.yaml` via `!include`.
- The top of every dashboard has
  `button_card_templates: !include components/button_card_templates.yaml`.
- Every view has `path`. Use `type: sections` unless the note says `grid-layout`.
- Follow the card preference order and the note's Feasibility table exactly. A card not
  in the table is a design change, so ask Kevin.
- A pattern used twice becomes a `wn_*` template (in `button_card_templates.yaml`, plus a
  row in the style guide's component index) or a partial in `dashboards/components/partials/`.
  Don't copy-paste card YAML.
- Colours, fonts and sizes come only from `var(--wn-*)` tokens. Long Jinja used more than
  once becomes a template sensor (in `sensor/` or a package), not a repeated string.

**2. Static check (fast, local).** Run `yamllint <files>` and
`python .claude/scripts/lint_dashboard.py dashboards/<slug>.yaml`. Fix errors before going on.

**3. Render to scratch.**
- Run `python .claude/scripts/render_dashboard.py dashboards/<slug>.yaml --out <scratchpad>/render.json`.
  Add `--theme Walnut` only if `ha_manage_theme(action="list")` lists `Walnut`. Otherwise
  render without a theme, and tell the reviewer the theme isn't deployed yet.
- Read the JSON and write it with
  `ha_config_set_dashboard(url_path="dashboard-scratch", config=<json>, BestPracticeKey=..., MandatoryBPS=false)`.
  This is the one live write you may make without asking. Never pass any other `url_path`.

**4. Check: dispatch both agents in the same message.**
- `dashboard-lint` with the dashboard file path.
- `dashboard-reviewer` with `url_path=dashboard-scratch`, the view paths, `theme=Walnut`
  (only if deployed), and focus notes from the design note.

Each report starts with `RESULT: PASS` or `RESULT: FAIL (…)`.

**5. Fix loop.** If either says FAIL, fix the errors in the YAML (not in scratch), then
repeat steps 2–4. An error whose fix belongs in the **theme** (e.g. built-in tile feature
buttons are about 42px tall, under the 48px minimum, which needs `--feature-height` in the
theme) is not a YAML fix. Don't work around it with `card_mod`. List it in the hand-over
as "theme change needed" and treat it as resolved for this loop. Stop after **3 rounds**, even if errors remain. Warnings don't block.
List them in the hand-over.

**6. Hand-over to Kevin.** Capture the main view yourself at the three sizes
(`ha_get_dashboard_screenshot`, url_path `dashboard-scratch`, widths 1715/384/2372, heights
965/798/1294, plus `theme` if deployed) so he can see it. Capture **one at a time**
(the Pi's engine times out on parallel full-size renders), with `wait_ms=10000`, because
icons often render blank at shorter waits. Passing `theme` can persist on
the screenshot engine's user. Read `ha_manage_theme(action="get_engine_theme")` before the
captures. If it changed afterwards, restore it with `set_engine_theme`, passing the
**inner** `{"dark": …, "theme": …}` object as `value` and the current one as
`expected_current`. Restore it even if a capture fails. Then write the hand-over with:
- the lint and review results (the final `RESULT:` lines, and any remaining findings or
  warnings)
- the files created or changed
- the real-device checklist below, with the scratch URL path `/dashboard-scratch/<view>`
  (admin only, hidden from the sidebar)
- "When you're happy, run `/deploy`. Registering a *new* dashboard in `configuration.yaml`
  restarts HA. Changing an existing YAML dashboard doesn't."

Real-device checklist:
- **Tablet:** status readable from across the room; every tap target easy to hit; nothing
  needs a long-press; the sidebar stays collapsed.
- **Phone:** one column; no sideways scrolling; the main controls reachable with one hand
  near the top.
- **Desktop:** no stretched tiles; no big empty bands.

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Fixing the scratch config by hand | Fix the YAML, then re-render. Scratch is disposable output. |
| Writing to the real dashboard "since it's the same content" | Only `dashboard-scratch`. Deploying is `/deploy`, with Kevin's go-ahead. |
| Running the agents one after the other | Dispatch both in one message. |
| A 4th fix round | Stop at 3 and report what's left. Kevin decides. |
| Hardcoding a colour "just for this card" | Add a token to the theme (a design change, so ask) or use an existing one. |
