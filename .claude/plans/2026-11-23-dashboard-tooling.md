# Dashboard Tooling and Design System: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the skills, agents, scripts and design-system scaffolding that turn a dashboard mockup into a consistent, multi-device HA dashboard, and prove them by building the new "Walnut" theme through the pipeline.

**Architecture:** Two Python scripts do the deterministic work: resolving `!include` in dashboard YAML to JSON, and linting dashboards against a machine-readable card allowlist. Two agents wrap them: `dashboard-lint` (static checks) and `dashboard-reviewer` (screenshots at 3 device sizes). Two skills drive the flow: `/dashboard-design` (mockup → feasibility table → HTML preview) and `/dashboard-build` (YAML → scratch dashboard → agents → hand-over). One theme owns the look. Shared button-card templates cover what standard cards can't.

**Tech Stack:** Python 3.11 + PyYAML 6 (stdlib `unittest`, no pytest), Claude Code skills and agents (Markdown), HA Lovelace YAML, the ha-mcp tools, the Artifact tool for HTML previews.

**Spec:** [.claude/specs/2026-11-23-dashboard-tooling-design.md](../specs/2026-11-23-dashboard-tooling-design.md). Also read [.claude/reference/dashboard-catalog.md](../reference/dashboard-catalog.md) and [CLAUDE.md](../../CLAUDE.md).

## Global Constraints

- Device viewports (W×H): tablet **1715×965**, phone **384×798**, desktop **2372×1294**. Never use the screenshot presets.
- Layout classes: **wide** = tablet + desktop (≥ 1024px); **narrow** = phone (< 1024px).
- Minimum touch target on the tablet and phone: **48px**.
- Theme name: **`Walnut`**, file `themes/walnut.yaml`. Theme token prefix: `--wn-`.
- Background photo: Unsplash `J2gEgTPM_OA` (Nathan Dumlao, Unsplash License), saved as `www/backgrounds/walnut.jpg`, ≥ 2560px wide. Served at `/local/backgrounds/walnut.jpg`.
- Scratch dashboard: url_path **`dashboard-scratch`**, title `Scratch`, `show_in_sidebar: false`, storage mode. Claude may write it without asking. Every other live change (real dashboards, themes, resources, add-on options, reloads, restarts, pushes) needs Kevin's explicit OK.
- **Commits:** CLAUDE.md forbids committing unless asked. Commit steps below run only if Kevin authorised commits for this plan at the start of execution. Never push except through `/deploy`.
- Every YAML file: the `#####` / `# ---` banner header, LF line endings, `yamllint .` exits 0.
- Card preference order: built-in → Mushroom → house button-card templates → other installed cards (`card_mod` only on tier-D cards).
- Tests: `python -m unittest discover -s .claude/scripts/tests -v` from the repo root.

## Review Focus

1. **Nested `!include` paths**: a view file in `dashboards/views/x/` that includes `../../components/partials/y.yaml` must resolve relative to *the including file*, not the repo root. → Task 2, `test_nested_include_resolves_relative_to_including_file`.
2. **`!secret` in a dashboard**: rendering must fail loudly, not push a `None` placeholder to scratch. → Task 2, `test_secret_raises`.
3. **Legitimate theme-token colours** such as `rgba(var(--rgb-primary-color), 0.2)`, Mushroom named colours (`icon_color: red`) and Bubble pop-up hashes (`#bedroom`) must not be flagged as hardcoded colours. → Task 3, `test_token_colours_not_flagged`.
4. **Screenshot engine theme leak**: passing `theme=` can persist on the engine's HA user. The reviewer must leave it as it found it. → Task 6, Step 3.
5. **Engine-only render artefacts** (e.g. blank Mushroom icons seen 2026-11-23): the reviewer must re-capture with a longer `wait_ms` before reporting a blank icon, and label the finding "verify on real device" if it persists. → Task 6, Step 3.

---

### Task 1: Repo scaffolding and docs

**Files:**
- Modify: `.gitignore` (add the whitelist entries)
- Create: `dashboards/components/partials/.gitkeep`, `dashboards/views/.gitkeep`, `www/backgrounds/.gitkeep`
- Modify: `CLAUDE.md`, `README.md`

**Interfaces:**
- Produces: the folders `dashboards/`, `dashboards/components/`, `dashboards/components/partials/`, `dashboards/views/` and `www/backgrounds/`, tracked by git. `www/community/` stays ignored.

- [ ] **Step 1: Check that they're ignored today.** Run `git check-ignore -v dashboards/views/.gitkeep www/backgrounds/x.jpg`. Expected: both print a matching `*` rule (ignored).
- [ ] **Step 2: Edit `.gitignore`.** Add `!dashboards/`, `!dashboards/**`, `!www/`, `!www/backgrounds/`, `!www/backgrounds/**`, `!www/fonts/`, `!www/fonts/**` to the folder whitelist. Add `!*.jpg`, `!*.webp`, `!*.woff2` to the file whitelist. Put `www/*`, `!www/backgrounds/` and `!www/fonts/` *after* the whitelist so the rest of `www/` stays ignored (the existing `www/community/` ignore must still win).
- [ ] **Step 3: Verify.** Create the `.gitkeep` files, then run `git check-ignore -v www/backgrounds/x.jpg dashboards/views/.gitkeep www/community/foo.js www/sunset-predictor-card.js`. Expected: only the last two are reported as ignored. `git status --short` shows the new `.gitkeep` files.
- [ ] **Step 4: Update docs.** In `CLAUDE.md`, add a `dashboards/` row to the include table ("YAML-mode Lovelace dashboards; not loaded via configuration.yaml until registered under `lovelace: dashboards:`"). Add a **Dashboards** section that:
  - points to the catalogue, style guide, `/dashboard-design` and `/dashboard-build`,
  - states the `dashboard-scratch` standing exception,
  - adds `python -m unittest discover -s .claude/scripts/tests` to "Validating changes".

  Add a `dashboards/` row to the `README.md` layout table.
- [ ] **Step 5: Lint.** Run `yamllint .`. Expected: exit 0.
- [ ] **Step 6: Commit** `.gitignore`, the `.gitkeep` files, `CLAUDE.md`, `README.md`: `chore: scaffold dashboards/ and www/backgrounds/`.

### Task 2: `render_dashboard.py` (YAML with includes → JSON)

**Files:**
- Create: `.claude/scripts/render_dashboard.py`
- Create: `.claude/scripts/tests/test_render_dashboard.py`
- Create: `.claude/scripts/tests/fixtures/render/` (fixture YAML: `main.yaml`, `views/home/home.yaml`, `components/partials/clock.yaml`, `components/button_card_templates.yaml`, `templates_dir/a.yaml` + `b.yaml`, `secret.yaml`)

**Interfaces:**
- Produces:
  - `class DashboardLoadError(Exception)`
  - `load_dashboard(path: str | os.PathLike) -> dict`: resolves `!include`, `!include_dir_named`, `!include_dir_merge_named`, `!include_dir_list` and `!include_dir_merge_list` relative to the file that contains the tag (directory includes are sorted by filename, like HA). Raises `DashboardLoadError` on `!secret`, on any other tag, on a missing file, and on an include cycle.
  - `main(argv: list[str]) -> int`: CLI `python .claude/scripts/render_dashboard.py FILE [--theme NAME] [--out FILE]`. Prints JSON (or writes it to `--out`). `--theme` sets `theme: NAME` on every view that has no `theme`. Returns 0, or 2 on `DashboardLoadError` with the message on stderr.

- [ ] **Step 1: Write failing tests** in `test_render_dashboard.py` (`unittest.TestCase`):
  - `test_plain_include`: `main.yaml` has `button_card_templates: !include components/button_card_templates.yaml`. The result's `button_card_templates` equals that file's mapping.
  - `test_nested_include_resolves_relative_to_including_file`: `views/home/home.yaml` contains `- !include ../../components/partials/clock.yaml`. The resolved view's `cards[0]["type"]` equals the partial's type.
  - `test_include_dir_merge_named`: `!include_dir_merge_named templates_dir` → a dict with the keys of both `a.yaml` and `b.yaml`.
  - `test_include_dir_list_sorted`: `!include_dir_list templates_dir` → `[a, b]` in filename order.
  - `test_secret_raises`: `load_dashboard("secret.yaml")` raises `DashboardLoadError`, and the message contains `"!secret"`.
  - `test_missing_include_raises`: the message contains the missing path.
  - `test_theme_flag_sets_only_missing`: `main(["main.yaml", "--theme", "Walnut", "--out", tmp])`. Views without `theme` get `"Walnut"`; a view with `theme: Other` keeps it.
  - `test_cli_exit_code_on_error`: `main(["secret.yaml"]) == 2`.
- [ ] **Step 2: Run** `python -m unittest discover -s .claude/scripts/tests -v`. Expected: FAIL (`ModuleNotFoundError: render_dashboard`). Tests add `.claude/scripts` to `sys.path`.
- [ ] **Step 3: Implement** `render_dashboard.py`. Use a `yaml.SafeLoader` subclass created per file, so each constructor knows its file's directory. Track the set of open paths to catch cycles. Module docstring in the same style as `extract_entity_refs.py`.
- [ ] **Step 4: Run the tests.** Expected: all PASS.
- [ ] **Step 5: Commit**: `feat: add render_dashboard.py to resolve dashboard includes`.

### Task 3: Card allowlist and `lint_dashboard.py`

**Files:**
- Create: `.claude/reference/installed-cards.yaml`
- Create: `.claude/scripts/lint_dashboard.py`
- Create: `.claude/scripts/tests/test_lint_dashboard.py`, `.claude/scripts/tests/fixtures/lint/` (`good.yaml`, `bad.yaml`, `allow.yaml`)

**Interfaces:**
- Consumes: `load_dashboard` from Task 2.
- Produces:
  - `installed-cards.yaml` schema: a top-level `cards:` list of `{type: <glob>, source: core|hacs|manual, repo: <owner/name or null>, tier: A|B|C|D, card_mod: allowed|discouraged}`. It covers every `custom:` type in the catalogue (Mushroom as `custom:mushroom-*`, layout-card as `custom:*-layout` and `custom:layout-card`, rows such as `custom:template-entity-row`, `custom:popup-card` from browser_mod) plus the built-in card types used today (`tile`, `heading`, `entities`, `glance`, `markdown`, `picture-entity`, `weather-forecast`, `map`, `alarm-panel`, `grid`, `horizontal-stack`, `vertical-stack`, `conditional`, `picture`). Tier-D cards get `card_mod: allowed`; all others get `discouraged`.
  - `@dataclass Finding(rule: str, severity: str, file: str, where: str, message: str)`. `severity` is `"error"` or `"warning"`. `where` is a JSON-pointer path (structure rules) or `line N` (text rules).
  - `load_allowlist(path: str = ".claude/reference/installed-cards.yaml") -> list[dict]`
  - `lint_file(path: str, allowlist: list[dict]) -> list[Finding]`
  - `main(argv: list[str]) -> int`: CLI `python .claude/scripts/lint_dashboard.py [FILE ...]` (default: `dashboards/*.yaml`, top-level files only; included files are covered through their parent). Prints `{"findings": [...], "errors": N, "warnings": M}`. Exit 1 if `errors > 0`.
- Rules (exact names):
  - `unknown-card-type` (error): any dict whose `type` starts with `custom:` and matches no allowlist glob (`fnmatch`).
  - `hardcoded-color` (error, text rule on the raw lines of the file and every file it includes): matches `#[0-9a-fA-F]{3}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{8}\b`, or `\b(rgb|rgba|hsl|hsla)\(` *not* immediately followed by `\s*var\(`. A line containing `# lint-ignore: hardcoded-color` is skipped.
  - `card-mod-not-allowed` (error): a dict with a `card_mod` key whose `type` matches an entry with `card_mod: discouraged`, or matches nothing.
  - `card-mod-used` (warning): a `card_mod` key on a type with `card_mod: allowed` (still reported, so every use is visible).
  - `view-missing-path` (warning): a view without `path`.
  - `duplicated-template` (warning): an identical string containing `{{` or `{%`, longer than 80 chars, appearing 2+ times in the resolved config. Reported once per string with all its paths.

- [ ] **Step 1: Write failing tests** (`unittest.TestCase`):
  - `test_good_file_clean`: `lint_file("good.yaml")` → `[]`.
  - `test_unknown_custom_card`: `bad.yaml` with `type: custom:not-installed-card` → one `unknown-card-type` at `/views/0/sections/0/cards/0`.
  - `test_hex_and_rgba_flagged`: `bad.yaml` lines with `color: "#c47a3a"` and `background: rgba(180,130,80,0.15)` → two `hardcoded-color` findings with the correct `line N`.
  - `test_token_colours_not_flagged`: `good.yaml` contains `rgba(var(--rgb-primary-color), 0.2)`, `icon_color: red`, `navigation_path: "#bedroom"` → no findings.
  - `test_lint_ignore_comment`: `allow.yaml` with `colors: {calendar.kevin: "#008c00"}  # lint-ignore: hardcoded-color` → no `hardcoded-color` finding.
  - `test_card_mod_on_tile_is_error` and `test_card_mod_on_tier_d_is_warning` (`custom:atomic-calendar-revive`).
  - `test_view_missing_path` → a warning at `/views/1`.
  - `test_duplicated_template` → one warning listing 2 paths.
  - `test_cli_exit_codes`: `main(["good.yaml"]) == 0`, `main(["bad.yaml"]) == 1`.
  - `test_allowlist_covers_live_dashboards`: every `custom:` type that appears in `.claude/reference/dashboard-catalog.md` table rows matches some allowlist glob (guards catalogue/allowlist drift).
- [ ] **Step 2: Run the tests.** Expected: FAIL (module missing).
- [ ] **Step 3: Write `installed-cards.yaml`** (banner header; data from the catalogue).
- [ ] **Step 4: Implement `lint_file` and `main`** in `lint_dashboard.py`. Structure rules walk `load_dashboard()` output. Text rules re-read the raw lines (collect included file paths from the loader for that).
- [ ] **Step 5: Run the tests.** Expected: all PASS. Then `yamllint .` exits 0.
- [ ] **Step 6: Commit**: `feat: add card allowlist and lint_dashboard.py`.

### Task 4: Style guide and component library skeleton

**Files:**
- Create: `.claude/reference/dashboard-style-guide.md`
- Create: `dashboards/components/button_card_templates.yaml`

**Interfaces:**
- Produces:
  - **Token names**, every one defined by `themes/walnut.yaml` in Task 9. Their values are left as `TBD (Task 9)` in the guide until then:
    - `--wn-bg-image`
    - `--wn-surface`, `--wn-surface-strong`, `--wn-border`, `--wn-blur`
    - `--wn-text`, `--wn-text-secondary`, `--wn-text-disabled`
    - `--wn-accent-blue`, `--wn-accent-gold`, `--wn-accent-tan`
    - `--wn-ok`, `--wn-warn`, `--wn-alert`
    - `--wn-radius`, `--wn-gap`, `--wn-touch-min` (= `48px`)
    - `--wn-font`, `--wn-font-xs`, `--wn-font-sm`, `--wn-font-md`, `--wn-font-lg`, `--wn-font-xl`
  - The base button-card template **`wn_base`**: glass surface, radius, font and colours from `--wn-*` vars only, `min-height: var(--wn-touch-min)`, `section_mode: true`. Every later house template sets `template: wn_base`.
- The style guide's sections (rules, no essays):
  1. Devices and layout classes (from Global Constraints).
  2. The token table: name, purpose, value.
  3. The card preference order and when each tier is allowed.
  4. `card_mod` policy: tier D only, `var(--wn-*)` values only, every use shows up as a lint warning.
  5. Layout: sections view by default. Use `visibility: [{condition: screen, media_query: "(max-width: 1023px)"}]` for narrow-only cards, and the inverse for wide-only cards. layout-card `grid-layout` + `mediaquery` only when a mockup needs exact placement.
  6. Readability: tablet body text ≥ `--wn-font-md`, status text ≥ `--wn-font-lg`, white text on `--wn-surface` must meet WCAG AA (4.5:1) against the lightest area of the photo.
  7. A component index: a table of house templates (name, purpose, parameters). It starts with `wn_base`.

- [ ] **Step 1: Write the style guide.**
- [ ] **Step 2: Write `button_card_templates.yaml`** with `wn_base` (banner header).
- [ ] **Step 3: Verify.** `python .claude/scripts/lint_dashboard.py dashboards/components/button_card_templates.yaml` → `"errors": 0`. `yamllint .` exits 0.
- [ ] **Step 4: Commit**: `docs: add dashboard style guide and wn_base template`.

### Task 5: Live infrastructure (scratch dashboard, restart_ignore, /deploy)

**Files:**
- Modify: `.claude/skills/deploy/SKILL.md`

**Interfaces:**
- Produces:
  - the storage dashboard `dashboard-scratch` (empty view `path: scratch`)
  - add-on `restart_ignore` including `dashboards/`, `themes/` and `www/`
  - `/deploy` that knows which paths don't need a restart and offers `frontend.reload_themes`

- [ ] **Step 1: Create the scratch dashboard** (standing OK): `ha_config_set_dashboard(url_path="dashboard-scratch", title="Scratch", icon="mdi:flask-outline", show_in_sidebar=False, require_admin=True, config={"views":[{"title":"Scratch","path":"scratch","type":"sections","sections":[]}]})`. Verify with `ha_config_get_dashboard(list_only=True)`: it should list `dashboard-scratch`.
- [ ] **Step 2: Ask Kevin** (AskUserQuestion) to approve changing the Git Pull add-on's `restart_ignore` from the current list to the current list + `dashboards/`, `themes/`, `www/`. Only if approved: `ha_manage_app` options update. Verify with `ha_get_app(slug="core_git_pull")`.
- [ ] **Step 3: Update `/deploy`**:
  - its "How deployment actually works" note: these paths are ignored for restarts, so a change only to them needs a browser refresh
  - step 2: when `themes/` changed, the restart verdict says "No restart; themes need a reload"
  - a post-push step: after the add-on has pulled (check that the new commit's files exist via `ha_get_logs` or after waiting 300 s), ask before calling `frontend.reload_themes`
- [ ] **Step 4: Commit**: `chore: teach /deploy about dashboards and themes`.

### Task 6: `dashboard-lint` and `dashboard-reviewer` agents

**Files:**
- Create: `.claude/agents/dashboard-lint.md`, `.claude/agents/dashboard-reviewer.md`

**Interfaces:**
- Consumes: `lint_dashboard.py` (Task 3), `extract_entity_refs.py` (exists; it already scans `dashboards/`), the style guide (Task 4), `dashboard-scratch` (Task 5).
- Produces: two agents. Both return a Markdown report whose first line is `RESULT: PASS` or `RESULT: FAIL (<n> errors, <m> warnings)`, followed by a findings table (`severity | rule/check | device | location | message | suggested fix`). `/dashboard-build` parses that first line.

**dashboard-lint**
- Frontmatter: `model: sonnet`, tools `Read, Grep, Glob, Bash, mcp__ha-mcp__ha_get_state, mcp__ha-mcp__ha_get_entity, mcp__ha-mcp__ha_search, mcp__ha-mcp__ha_list_services, mcp__ha-mcp__ha_get_hacs_info, mcp__ha-mcp__ha_config_list_dashboard_resources`. Read-only.
- Procedure:
  1. Run `lint_dashboard.py` on the given files (default: all).
  2. Run the `entity-ref-checker` procedure (extract + bulk `ha_get_state`) on the same files.
  3. Check for catalogue drift: compare installed HACS plugins (`installed_only=True, category="plugin"`) and the resource URLs against `installed-cards.yaml` repos. Report anything added or removed as a warning `catalog-drift`.

**dashboard-reviewer**
- Frontmatter: no `model` (inherits; visual judgement needs the strongest model). Tools `Read, mcp__ha-mcp__ha_get_dashboard_screenshot, mcp__ha-mcp__ha_config_get_dashboard, mcp__ha-mcp__ha_manage_theme`. It writes nothing except the engine-theme restore.
- Inputs: `url_path` (default `dashboard-scratch`), optional view paths, optional `theme`.
- Procedure:
  1. `ha_manage_theme(action="get_engine_theme")` and record the value.
  2. For each view × device (1715×965, 384×798, 2372×1294): capture with `height="auto"` and `wait_ms=4000` (plus `theme` if given).
  3. If a capture shows blank icons or cards, re-capture that one with `wait_ms=10000`. If it's still blank, report it with "verify on real device".
  4. Check every capture against the style guide's checklist: horizontal overflow or clipping, unrendered cards or icons, cards that ignore the theme (light/opaque surfaces, a different font), text too small or low-contrast, touch targets < 48px (tablet/phone), excessive stretching or empty columns on the desktop, and whether the narrow layout drops or duplicates content compared with wide.
  5. Locate each finding through `ha_config_get_dashboard` (card path).
  6. Read the engine theme again. If it changed, restore it with `set_engine_theme` using `expected_current`.

- [ ] **Step 1: Write both agent files** (frontmatter + procedure + report format).
- [ ] **Step 2: Test the lint agent.** Dispatch `dashboard-lint` on `.claude/scripts/tests/fixtures/lint/bad.yaml`. Expected: `RESULT: FAIL` listing the `unknown-card-type`, both `hardcoded-color` and the `card-mod-not-allowed` findings.
- [ ] **Step 3: Test the reviewer agent.** Copy the live `dashboard-security` config into `dashboard-scratch` (read via `ha_config_get_dashboard`, write via `ha_config_set_dashboard(config=...)`), then dispatch `dashboard-reviewer` on it. Expected:
  - a report covering 3 views × 3 devices
  - the blank Mushroom icon handled per procedure step 3
  - engine theme the same before and after (check it yourself with `get_engine_theme`)
- [ ] **Step 4: Reset scratch** to the empty config from Task 5 Step 1.
- [ ] **Step 5: Commit**: `feat: add dashboard-lint and dashboard-reviewer agents`.

### Task 7: `/dashboard-design` skill

**Files:**
- Create: `.claude/skills/dashboard-design/SKILL.md`

**Interfaces:**
- Consumes: the catalogue, the style guide, `installed-cards.yaml`.
- Produces: an approved design note saved to `.claude/designs/<YYYY-MM-DD>-<slug>.md`, read by `/dashboard-build`. Sections, in order:
  1. `## Intent`
  2. `## Feasibility` (the table below)
  3. `## Layout` (wide / narrow sketch)
  4. `## Components` (house templates to add or reuse)
  5. `## Entities`
  6. `## Preview` (Artifact URL)
  7. `## Approved` (date)

  `.claude/designs/` is covered by `.claude/**`.

Use superpowers:writing-skills while writing this skill. The SKILL.md must make the agent:
1. Read the catalogue, style guide and allowlist before anything else.
2. Break the mockup (image path(s) or a description) into numbered elements.
3. Build the **feasibility table** with columns `# | element | rating | how (card / technique) | closest alternative | narrow vs wide`. `rating` is one of `native`, `installed-card`, `theme-css`, `card_mod`, `new-install`, `not-possible`. A `new-install` row names the HACS repo and asks Kevin. A `not-possible` row must give an alternative.
4. Find the real entity IDs with `ha_search`. Never guess.
5. Build the HTML preview of **achievable elements only**:
   - Load the artifact-design skill first (Artifact quickstart).
   - Show three device frames side by side at their true aspect ratios (1715×965, 384×798, 2372×1294, scaled).
   - Use the `--wn-*` token values from the style guide (or proposed values when the theme is in progress).
   - Publish as a private Artifact.
6. Stop for Kevin's approval. Revise until approved, then write the design note.

- [ ] **Step 1: Write SKILL.md** (frontmatter `name: dashboard-design`, a description that triggers on "mockup", "dashboard design", "can HA do this").
- [ ] **Step 2: Test it** on the existing Home dashboard's first view as if it were a mockup: take a screenshot at 1715×965 → run the skill. Expected:
  - every element gets a rating
  - the weather radar is rated `installed-card` (`custom:weather-radar-card`)
  - the preview Artifact shows 3 frames
  - no element in the preview is rated `not-possible`
- [ ] **Step 3: Commit**: `feat: add /dashboard-design skill`.

### Task 8: `/dashboard-build` skill

**Files:**
- Create: `.claude/skills/dashboard-build/SKILL.md`

**Interfaces:**
- Consumes: the design note (Task 7), `render_dashboard.py` (`--theme`, `--out`), `dashboard-scratch`, the two agents and their `RESULT:` line (Task 6), the `wn_base` template.
- Produces: YAML under `dashboards/`, a scratch render, and a hand-over message.

Use superpowers:writing-skills. The SKILL.md must make the agent:
1. Refuse to start without an approved design note (or ask Kevin to run `/dashboard-design`).
2. Write YAML following the card preference order. Every repeated card pattern becomes a `wn_*` template in `button_card_templates.yaml` or a partial in `components/partials/`. Views get a `path`.
3. Render with `python .claude/scripts/render_dashboard.py <file> --theme Walnut --out <scratchpad>/render.json`, then write it to `dashboard-scratch` with `ha_config_set_dashboard(config=...)`.
4. Dispatch `dashboard-lint` and `dashboard-reviewer` **in parallel**. Fix errors and repeat, at most **3 rounds**, then stop and report what's left.
5. Hand over:
   - the reviewer's key screenshots, one per device
   - lint and review results
   - a real-device checklist (tablet: readable from across the room, tap targets, sidebar behaviour; phone: one-handed reach, no horizontal scroll; desktop: no stretching)
   - "run `/deploy` when happy"
6. Never touch real dashboards, themes or resources, and never deploy.

- [ ] **Step 1: Write SKILL.md.**
- [ ] **Step 2: Test it** with a minimal design note (one view: a `heading` + two `tile` cards + one `wn_base` button) saved as `dashboards/_smoke.yaml`. Expected:
  - scratch shows it
  - both agents run in parallel and return `RESULT:` lines
  - hand-over includes 3 screenshots
- [ ] **Step 3: Clean up.** Delete `dashboards/_smoke.yaml` and the test design note, then reset scratch.
- [ ] **Step 4: Commit**: `feat: add /dashboard-build skill`.

### Task 9: First use, the Walnut theme through the pipeline

**Files:**
- Create: `themes/walnut.yaml`, `www/backgrounds/walnut.jpg`, `dashboards/style-sample.yaml`, `.claude/designs/2026-11-23-walnut-theme.md`
- Modify: `.claude/reference/dashboard-style-guide.md` (fill in the token values), `.claude/reference/dashboard-catalog.md` (themes table)

**Interfaces:**
- Consumes: everything above.
- Produces: the `Walnut` theme defining every `--wn-*` token. It also maps the HA variables onto them:
  - `--ha-card-background`, `--ha-card-border-color`, `--ha-card-border-radius`, `--ha-card-box-shadow`
  - `--primary-color`, `--accent-color`, `--primary-text-color`, `--secondary-text-color`, `--state-*`
  - `--lovelace-background: center / cover no-repeat fixed url("/local/backgrounds/walnut.jpg")`
  - `--mush-*` and `--bubble-*`
  - `card-mod-theme: Walnut`, and `card-mod-card` applying `backdrop-filter: blur(var(--wn-blur))`

  `dashboards/style-sample.yaml` is a reference view that shows every token and house template, so later reviews can check against it.

- [ ] **Step 1: Download the photo.** Fetch `https://unsplash.com/photos/J2gEgTPM_OA/download?force=true&w=2560` into its own new scratchpad directory, then copy it to `www/backgrounds/walnut.jpg`. Expected: `file` reports JPEG, width ≥ 2560.
- [ ] **Step 2: Run `/dashboard-design`** with intent "Walnut theme" on a sample view: a status header, 4 room tiles, an alert banner, a media tile, a weather block. The preview offers **2–3 variants** (glass opacity/blur, accent mapping, font). Kevin picks one, and the design note records the chosen token values.
- [ ] **Step 3: Write the files.** Write `themes/walnut.yaml`, fill in the style guide token values, and add any `wn_*` templates the sample needs. Write `dashboards/style-sample.yaml` (view theme `Walnut`).
- [ ] **Step 4: Static checks.** `yamllint .` exits 0. `python .claude/scripts/lint_dashboard.py dashboards/style-sample.yaml` → `"errors": 0`. The unit tests pass.
- [ ] **Step 5: Deploy** the theme and photo with `/deploy`. This needs Kevin's go-ahead, and theme reload approval after the pull. If Task 5 Step 2 wasn't approved, `/deploy` will report a restart.
- [ ] **Step 6: Build.** Run `/dashboard-build` on `style-sample.yaml` → scratch. Expected: lint and reviewer return `RESULT: PASS` (warnings allowed) within 3 rounds.
- [ ] **Step 7: Kevin checks on the real devices.** He opens `/dashboard-scratch/...` on the tablet, phone and desktop. Record his feedback in the design note, and loop Steps 3–6 until he approves.
- [ ] **Step 8: Update** the catalogue themes table (`Walnut` = in use, the replacement for Warm Home), then commit: `feat: add Walnut theme and style sample`.

## Out of scope (follow-up sessions)

- Registering YAML dashboards under `lovelace: dashboards:` in `configuration.yaml` (that needs a restart) and migrating `dashboard-home`, `dashboard-security` and `dashboard-calendar`.
- Setting `Walnut` as the backend default theme, and tablet kiosk settings in browser_mod (sidebar collapsed, sidebar items), plus naming the browser_mod browsers.
- Pruning unused cards.
