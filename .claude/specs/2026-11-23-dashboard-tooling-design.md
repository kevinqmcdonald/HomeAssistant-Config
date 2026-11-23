# Dashboard tooling and design system: design

Date: 2026-11-23 · Status: draft, awaiting approval · Owner: Kevin

## Intent

Make dashboards for this HA instance cheaper to design, build and test, and make them look
consistent. Three problems drive this:

1. **Three devices.** The same dashboards are used on a wall tablet, a phone and a desktop.
   Testing all three by hand takes too long.
2. **Style drift.** Each card owns its own styling, so the UI looks inconsistent. Today the
   Security dashboard copies Warm Home's colours by hand into about 40 `card_mod` blocks, and
   the calendar colours are defined twice.
3. **Mockup to implementation.** Many design ideas are hard or impossible in Lovelace, and
   telling which is which takes deep expertise.

This effort builds the **tooling and the design system** (theme plus shared components).
The three dashboards are redesigned afterwards, in later sessions, using this tooling.

## Goals

- One theme owns the look. Standard cards follow it with no per-card styling.
- Turning a mockup into a dashboard is a repeatable pipeline: feasibility breakdown → HTML
  preview → YAML build → automatic checks → Kevin's check on the real devices.
- Every build is screenshotted automatically at the three real device sizes.
- Static lint catches card types that aren't installed, hardcoded colours, stray `card_mod`
  and bad entity IDs.
- Agents and skills only propose cards that are installed (from the catalogue), unless
  they flag a new install explicitly.
- Dashboards live as YAML in this repo, so they're version-controlled and reviewable.

## Non-goals

- Redesigning or migrating the three existing dashboards. That's the follow-up work.
- A light theme. The theme is dark only.
- Different content per device. Content is the same everywhere; only the layout adapts.
- Pruning unused HACS cards. That happens after the redesign, with Kevin's approval.

## Anti-goals (failure even if it "works")

- Tooling that writes to real dashboards, themes or resources, or that pushes or restarts
  HA, without explicit approval. Only the scratch dashboard is exempt.
- A preview that promises something HA can't do. Previews may show only elements the
  feasibility step marked achievable, each mapped to a named card or technique.
- Designs that look right on one device and break on another.
- Hardcoded colours or per-card `card_mod` creeping back into ordinary cards.

## Constraints

| Constraint | Detail |
| --- | --- |
| Devices (CSS viewport, measured by browser_mod) | Tablet **1715×965** (Apolosign 15.6", landscape, Companion app, non-admin user). Phone **384×798** (Galaxy S24+, Companion app). Desktop **2372×1294** (4K at 150% scaling, maximised browser). |
| Tablet users | Jordan and guests. Big touch targets (≥ 48px), readable across the room. Kiosk: browser_mod keeps the sidebar collapsed (still expandable) and controls its items. |
| Look | Dark only. A real dark-wood photo as the background, frosted translucent tiles, white sans-serif text. Palette: blue, gold/yellow, tan. Replaces Warm Home. |
| Installed cards | See [`.claude/reference/dashboard-catalog.md`](../reference/dashboard-catalog.md). New HACS installs are allowed if flagged. |
| Live-instance rules | CLAUDE.md: no restarts, reloads, commits, pushes or live changes without asking. **Standing exception:** Claude may create, update and delete the hidden scratch dashboard `dashboard-scratch` without asking. |
| Deploy | The Git Pull add-on polls every 300 s with `auto_restart: true`. Its current `restart_ignore` is `ui-lovelace.yaml, .gitignore, .claude/, CLAUDE.md, README.md, .vscode/`. It does **not** cover dashboards, themes or `www/`, so pushing those would restart HA. |
| Repo | `.gitignore` is a whitelist. New top-level folders must be added to it. Files use LF line endings and must pass `yamllint .`. |
| Lovelace | Resources stay in storage mode. YAML dashboards are declared under `lovelace: dashboards:` in `configuration.yaml` (adding one needs a restart; editing its YAML only needs a browser refresh). |
| Screenshot engine | `ha_get_dashboard_screenshot` takes a custom `width`/`height`. Passing `theme` may persist it on the engine's HA user (restore it with `ha_manage_theme set_engine_theme`). |

## Approaches considered

**Tooling shape**
- **A. Separate skills for each stage, plus two checking agents (chosen).** Each stage can
  be used on its own, and the agents keep large screenshots and configs out of the main
  conversation.
- B. One `/dashboard` skill that runs every phase. Rejected: long and brittle, and
  screenshots fill up the conversation.
- C. Mostly agents (designer, builder, reviewer). Rejected: fewer points where Kevin
  approves, and he wants a feasibility check and a preview before anything is built.

**How consistency is enforced**
- **A. The theme owns the look, and a few shared components cover the rest (chosen).**
- B. Theme plus per-card styling, cleaned up. Rejected: it's the pattern that caused the drift.
- C. Bubble Card everywhere. Rejected: rebuilds everything in one card system and ties the
  dashboards to it for the long term.

Kevin picked A for both.

## Design

### 1. Repo layout (new)

```
dashboards/                         # NEW top-level, whitelisted in .gitignore
  <dashboard>.yaml                  # one file per YAML-mode dashboard (added during redesign)
  views/<dashboard>/<view>.yaml     # optional per-view split, pulled in via !include
  components/button_card_templates.yaml   # house components, shared by every dashboard
  components/partials/*.yaml        # reusable card snippets (!include)
themes/<new-theme>.yaml             # dark-wood theme, the single source of truth for style
www/backgrounds/                    # wood photo (NEW whitelisted path; www/community stays ignored)
www/fonts/                          # self-hosted sans-serif font files, if a webfont is used
.claude/reference/dashboard-catalog.md       # installed cards + styling tiers (exists)
.claude/reference/dashboard-style-guide.md   # design rules the tooling enforces (new)
.claude/reference/installed-cards.yaml       # machine-readable allowlist for lint (new)
.claude/scripts/render_dashboard.py          # resolves !include → JSON for the scratch push (new)
.claude/scripts/lint_dashboard.py            # static dashboard lint (new)
.claude/skills/dashboard-design/SKILL.md     # new
.claude/skills/dashboard-build/SKILL.md      # new
.claude/agents/dashboard-reviewer.md         # new
.claude/agents/dashboard-lint.md             # new
```

Each dashboard file references the shared components with
`button_card_templates: !include components/button_card_templates.yaml`.

### 2. Design system

**Theme** (new file in `themes/`, set as the default for every dashboard and user):
- Tokens: background, glass surface (translucent fill plus `backdrop-filter: blur`), border,
  text (primary is white, plus secondary and disabled), accents (blue, gold/yellow, tan),
  status colours (ok, warn, alert, which must hold up against dark wood), radius, spacing,
  font family and type scale.
- Standard HA variables come from the tokens: `--ha-card-*`, `--primary-color`, `--state-*`,
  `--lovelace-background` (the wood photo), and so on.
- Mushroom `--mush-*` and Bubble `--bubble-*` variables are set from the same tokens.
- `card-mod-theme` sets the global glass tile style once (`card-mod-card`, `card-mod-view`,
  `card-mod-root`). No per-card copies.
- Typography sizes are large enough for reading across the room on the tablet.

**Components** (`dashboards/components/button_card_templates.yaml`): a small house library
of button-card templates for things standard cards can't do (e.g. status tile, room tile,
alert banner, big kiosk button). Every template takes all its colours and sizes from the
theme variables. The library starts small and grows during the redesign.

**Card preference order** (written into the style guide and enforced by lint):
1. Built-in cards: tile, heading, badges, entities, markdown and so on.
2. Mushroom.
3. House button-card templates.
4. Other installed cards, but only where 1–3 can't do the job. Cards that can only be styled
   through `card_mod` (catalogue tier D) need a `card_mod` override that uses theme
   variables only, and each must be on lint's allowlist.

**Layout rules:** sections view by default, with `visibility: screen` conditions where
phone and wide layouts must differ. layout-card `grid-layout` with `mediaquery` is allowed
when a mockup needs exact placement. The tablet (1715) and the desktop (2372) share the
"wide" layout. The phone is the "narrow" layout.

The style guide (`dashboard-style-guide.md`) writes all of this down as concrete rules:
token names, minimum touch target, type scale, card preference order, when `card_mod` is
allowed, and layout breakpoints.

### 3. Skills

**`/dashboard-design`** (Kevin runs it; given a mockup image(s) or a described idea)
1. Read the catalogue and the style guide.
2. Break the mockup into elements. For each element, the **feasibility table** gives:
   - how hard it is: native / installed custom card / theme CSS / `card_mod` / new install
     needed / not possible
   - the card or technique to use
   - the closest achievable alternative, when it isn't possible as drawn
   - how the element adapts on the phone versus the wide layout
3. Build an **HTML preview** of the achievable version only, using the theme tokens. It shows
   the design at all three device sizes side by side. It's published as a private Artifact.
4. Stop for Kevin's approval. The output is an approved design note that `/dashboard-build`
   reads.

**`/dashboard-build`** (Kevin runs it; given an approved design)
1. Write or modify YAML in `dashboards/` using the card preference order and house components.
   New reusable patterns become templates, not copy-pasted card YAML.
2. Resolve the includes with `render_dashboard.py`, then push the result to
   `dashboard-scratch` through ha-mcp (standing permission).
3. Run the `dashboard-lint` and `dashboard-reviewer` agents (in parallel). Fix what they
   find and repeat (cap: 3 rounds, then report what's left).
4. Hand over: the screenshots, the lint result, and a checklist for Kevin to test on the
   real devices.
5. Never deploy. Deploying stays with the existing `/deploy` skill, with Kevin's go-ahead.

### 4. Agents

**`dashboard-reviewer`** (read-only, except for screenshots)
- Screenshots `dashboard-scratch` (or a named dashboard) at 1715×965, 384×798 and
  2372×1294, full page.
- Checks against the style guide:
  - overflow, clipping and horizontal scroll
  - icons or cards that didn't render
  - cards that ignore the theme (light backgrounds, wrong fonts)
  - text too small or contrast too low on the wood background
  - touch targets below 48px on the tablet and phone
  - wide-screen stretching on the desktop
- Before and after: reads the screenshot engine's theme, and restores it if a capture changed it.
- Returns findings with the view, the device and the card (by its path in the config).

**`dashboard-lint`** (read-only)
- Runs `lint_dashboard.py` on the YAML, which flags:
  - card types not in `installed-cards.yaml`
  - hex or rgba colours outside `themes/`
  - `card_mod` on cards not on the allowlist
  - Jinja copy-pasted between cards (suggest a template sensor instead)
  - missing `path` on views
  - the catalogue being out of date compared with the live HACS list
- Runs the existing `entity-ref-checker` steps (via `extract_entity_refs.py` + ha-mcp) for
  entity IDs. `extract_entity_refs.py` is extended to scan `dashboards/` if it doesn't already.

### 5. One-time infrastructure changes (each needs Kevin's approval where it touches live HA)

1. `.gitignore`: whitelist `dashboards/`, `dashboards/**`, `www/backgrounds/`, `www/fonts/`.
   Keep `www/community/` ignored.
2. Git Pull add-on `restart_ignore`: add `dashboards/`, `themes/`, `www/`. YAML dashboards and
   static files don't need a restart. Themes need `frontend.reload_themes`, which `/deploy`
   offers after the push, with approval. **This is a live config change.**
3. Create the `dashboard-scratch` storage dashboard (hidden from the sidebar).
4. Update `/deploy` to know about `dashboards/` and themes (after the push: refresh the
   browser, offer a theme reload).
5. Update CLAUDE.md: the `dashboards/` folder, the scratch dashboard exception, a pointer to
   the catalogue and style guide.

### 6. First use (proving the tooling)

The new theme is the first thing to go through the pipeline: `/dashboard-design` previews
the theme options (wood photo, glass opacity, accent mapping) on a sample view, Kevin picks
one, then `/dashboard-build` writes the theme and a sample view to scratch and the agents
review it at all three sizes. The real redesigns follow in later sessions.

## Left to the builder

- Exact token names and values, and the type scale (decided in the theme preview).
- The internals of the scripts, the exact lint rules and the output format, within the
  behaviour above.
- The first set of house components (only what the sample view needs).
- How to name the browser_mod browsers (suggested: `wall-tablet`, `kevin-phone`, `desktop`).

## Background photo (decided 2026-11-23)

"Dark brown wooden surface texture" by Nathan Dumlao on Unsplash
(<https://unsplash.com/photos/dark-brown-wooden-surface-texture-J2gEgTPM_OA>), free under the
Unsplash License. It's landscape: warm mid-to-dark brown horizontal planks. Download it at
≥ 2560px wide to `www/backgrounds/`. It's lighter than the other candidates, so the glass
tile tint must be dark enough for white text to pass contrast (the theme preview checks this).
