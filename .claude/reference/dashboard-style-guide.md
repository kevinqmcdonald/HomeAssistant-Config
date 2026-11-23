# Dashboard style guide

Rules for every dashboard in this repo. `/dashboard-design`, `/dashboard-build`,
`dashboard-lint` and `dashboard-reviewer` all apply them. Installed cards and their
styling tiers are in [dashboard-catalog.md](dashboard-catalog.md). The lint allowlist is
[installed-cards.yaml](installed-cards.yaml).

## 1. Devices and layout classes

| Device | CSS viewport (W×H) | Layout class | Users |
| --- | --- | --- | --- |
| Apolosign 15.6" wall tablet, landscape, Companion app | 1715×965 | wide | Kevin, Jordan, guests |
| Galaxy S24+, Companion app, portrait | 384×798 | narrow | Kevin, Jordan |
| 4K desktop at 150% scaling, maximised browser | 2372×1294 | wide | Kevin |

- **wide** = 1024px or wider. **narrow** = below 1024px.
- Content is the same on every device. Only the layout changes.
- Review every change at all three sizes above. Don't use generic presets.

## 2. Tokens

The `Walnut` theme ([themes/walnut.yaml](../../themes/walnut.yaml)) defines every token.
Cards and templates reference tokens only, never literal colours or fonts. Lint rejects
colour literals outside `themes/`.

| Token | Purpose | Value |
| --- | --- | --- |
| `--wn-bg-image` | View background (dark-wood photo) | TBD (Task 9) |
| `--wn-surface` | Frosted tile fill (translucent) | TBD (Task 9) |
| `--wn-surface-strong` | Emphasised tile / pop-up fill | TBD (Task 9) |
| `--wn-border` | Hairline tile border | TBD (Task 9) |
| `--wn-blur` | Backdrop blur radius | TBD (Task 9) |
| `--wn-text` | Primary text (white) | TBD (Task 9) |
| `--wn-text-secondary` | Secondary text | TBD (Task 9) |
| `--wn-text-disabled` | Disabled / unavailable | TBD (Task 9) |
| `--wn-accent-blue` | Accent: cool / water / info | TBD (Task 9) |
| `--wn-accent-gold` | Accent: primary / active / "on" | TBD (Task 9) |
| `--wn-accent-tan` | Accent: neutral / secondary actions | TBD (Task 9) |
| `--wn-ok` | Status: good | TBD (Task 9) |
| `--wn-warn` | Status: attention | TBD (Task 9) |
| `--wn-alert` | Status: problem | TBD (Task 9) |
| `--wn-radius` | Tile corner radius | TBD (Task 9) |
| `--wn-gap` | Inner padding / gap unit | TBD (Task 9) |
| `--wn-touch-min` | Minimum touch target | `48px` |
| `--wn-font` | Font family (sans-serif) | TBD (Task 9) |
| `--wn-font-xs` … `--wn-font-xl` | Type scale (5 steps) | TBD (Task 9) |

When a card needs an RGB triplet (e.g. Mushroom `--rgb-*`), the theme defines it next
to the token, and cards use `rgba(var(--rgb-…), alpha)`. Lint allows that pattern.

## 3. Card preference order

Use the first option that can do the job:

1. **Built-in cards**: `tile` (with `features`), `heading`, badges, `entities`, `markdown`, and so on.
2. **Mushroom** (`custom:mushroom-*`): it follows the theme through `--mush-*`.
3. **House templates**: `custom:button-card` with `template: wn_*` from
   [dashboards/components/button_card_templates.yaml](../../dashboards/components/button_card_templates.yaml).
   A new repeated pattern becomes a new `wn_*` template, never copy-pasted card YAML.
4. **Other installed cards**: only when 1–3 can't do it (camera, calendar, radar, Spotify…).
   Name the reason in the design note.

A new HACS install is allowed, but the design note must propose it explicitly and Kevin
must approve it. After installing, add it to `installed-cards.yaml` and the catalogue.

## 4. `card_mod` policy

- Allowed only on **tier-D** cards (`card_mod: allowed` in `installed-cards.yaml`). Lint
  reports every use as a warning, and every other use as an error.
- Values must be `var(--wn-*)` / `var(--…)` tokens. No literals.
- Global styling (glass tiles, fonts) lives in the theme's `card-mod-theme` blocks, not on cards.
- A deliberate colour that has to stay literal (e.g. a calendar's per-calendar colour
  config) needs a trailing `# lint-ignore: hardcoded-color` and a reason in the design note.

## 5. Layout

- **Default:** `type: sections` views, `max_columns` chosen for the desktop (2372 wide),
  sections sized with `column_span` and cards with `grid_options`.
- **Device-specific cards:** use visibility conditions.
  - narrow only: `visibility: [{condition: screen, media_query: "(max-width: 1023px)"}]`
  - wide only: `visibility: [{condition: screen, media_query: "(min-width: 1024px)"}]`
  - The same entity must not be shown twice on one device.
- **Exact placement** (a mockup needs fixed areas): layout-card `custom:grid-layout` view
  with `grid-template-areas` and a `mediaquery:` block for `(max-width: 1023px)`.
- Every view has a stable `path` (lint warns otherwise).
- Phone: a single column, no horizontal scroll, the most-used controls in the top two
  screens. Pop-ups (Bubble Card `pop-up` or browser_mod) for detail.
- Desktop: avoid stretched tiles. Cap the width with `max_columns` or empty columns rather
  than full-width cards.

## 6. Readability and touch

- Every tappable element on the tablet and phone is ≥ `--wn-touch-min` (48px) in both
  dimensions.
- No action reachable only by long-press or double-tap on the tablet. Guests won't find it.
- Tablet body text ≥ `--wn-font-md`, and key status (alarm, doors, who's home) ≥ `--wn-font-lg`,
  so it reads from across the room.
- White text on `--wn-surface` must reach WCAG AA (4.5:1) over the **lightest** area of the
  wood photo, not just the average.
- Status meaning never relies on colour alone: pair `--wn-ok/warn/alert` with an icon or word.

## 7. Component index

House templates live in `dashboards/components/button_card_templates.yaml`. Each sets
`template: wn_base` (directly or through another `wn_*`).

| Template | Purpose | Parameters (`variables:`) |
| --- | --- | --- |
| `wn_base` | Base for all house buttons: section-grid sizing, 48px minimum, token typography. Glass surface comes from the theme. | none |
