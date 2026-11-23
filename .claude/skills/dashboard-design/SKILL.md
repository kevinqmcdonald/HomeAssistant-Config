---
name: dashboard-design
description: Use when Kevin shares a dashboard mockup, screenshot or idea, or asks "can HA do this?", or wants a new dashboard, view or theme designed, before any dashboard YAML is written. Also use for "is this possible in Lovelace", "make my dashboard look like this", and for redesigning an existing view.
---

# Dashboard design: mockup → feasibility → preview → approved design note

This skill turns an idea into an **approved design note**. `/dashboard-build` refuses to
start without one. This skill never writes dashboard YAML, themes or live config.

## Read first, every time

1. [.claude/reference/dashboard-catalog.md](../../reference/dashboard-catalog.md): the installed cards and their styling tiers.
2. [.claude/reference/dashboard-style-guide.md](../../reference/dashboard-style-guide.md): devices, tokens, card preference order, layout, touch and readability rules.
3. [.claude/reference/installed-cards.yaml](../../reference/installed-cards.yaml): the exact `custom:` type strings lint accepts.

If the request redesigns an existing view, or the mockup is a screenshot of one, also read
that view's current config (`ha_config_get_dashboard(url_path=..., view_path=...)`). It
names the entities and card settings already in use.

A mockup's colours and fonts are **not** a request for a different theme. The theme is
Walnut (dark wood, frosted tiles, white sans-serif, blue/gold/tan). Read the mockup for
its layout, content and interactions. Only treat its visual style as a theme request if
Kevin says so.

## Your first reply has these parts, in this order

**1. Intent.** Two or three lines: what the view is for, its main device, who uses it.

**2. Feasibility table.** One row per visible element of the mockup, numbered. An element
whose purpose you can't tell from the image doesn't get a rating. Put it in Questions
("What does the round icon top-left do?").

| # | element | rating | how (card / technique) | closest alternative | narrow vs wide |
| --- | --- | --- | --- | --- | --- |

`rating` is exactly one of these:
- `native`: a built-in card or feature does it.
- `installed-card`: an installed custom card does it. Name its `custom:` type from the allowlist.
- `theme-css`: needs a theme variable or `card-mod-theme` rule, which belongs in the theme.
- `card_mod`: needs per-card `card_mod`. Only valid for tier-D cards, per the style guide.
- `new-install`: needs a HACS card that isn't installed. Name the repo. Kevin must approve it.
- `not-possible`: Lovelace can't do it as drawn.

The `closest alternative` column is **required** for `not-possible` and `new-install`
rows, and for any row where the result will visibly differ from the mockup (e.g. an
opaque tier-D card on the glass theme). Write "–" only when the build will match the
mockup.

`narrow vs wide` says how the element behaves on the phone (384×798) compared with the
tablet (1715×965) and desktop (2372×1294): same, reordered, collapsed into a pop-up,
hidden on narrow (only if it's shown elsewhere), and so on.

**3. Entities.** For each element that shows state, give the real entity ID. Find it with
`ha_search` (`limit=50`, so results aren't cut off), then confirm every ID with one bulk
`ha_get_state` call (a list of IDs, `fields=["state"]`). Never guess an ID. Mark an element "needs helper/template
sensor" when no entity exists (e.g. a computed "anything open?" value), and name the
sensor you'd create.

**4. Layout sketch.** A text sketch of the wide layout and the narrow layout (column
order). Say whether it's a `sections` view or a layout-card `grid-layout` and why (style
guide §5).

**5. Questions.** Only the decisions that change what gets built. One per line, each
with your recommended answer.

## The preview (after Kevin answers, before any YAML)

1. Load the `artifact-design` skill. For a new artifact, call `Artifact` with
   `action: "quickstart"` and `intent: "other"` first.
2. Build an HTML page with **three device frames side by side**, each at its true aspect
   ratio, scaled to fit:
   - tablet 1715×965
   - phone 384×798
   - desktop 2372×1294
3. Show **only elements rated native / installed-card / theme-css / card_mod**, plus any
   `new-install` rows Kevin approved. Draw each one as the named card would look under
   the Walnut tokens. Use the alternative for `not-possible` rows, never the original.
4. Use the token values from the style guide. If a token is still `TBD`, propose values
   and show them in a small legend on the page.
5. For the wood background, publish the photo `www/backgrounds/walnut.jpg` with the page
   through the Artifact `files` map. Don't link to HA.
6. Publish it as a private Artifact. Give Kevin the link and ask what to change.
7. Revise and republish to the same file path until Kevin approves.

When the design is a theme, show 2–3 variants (e.g. glass opacity, accent mapping,
font) on the same sample content so he can pick.

## The design note (on approval)

Write `.claude/designs/<YYYY-MM-DD>-<slug>.md` with exactly these sections:

```markdown
# <View or theme name>
## Intent
## Feasibility        (the final table)
## Layout             (wide + narrow sketch, view type)
## Components         (wn_* templates to reuse or add, with their variables)
## Entities           (id → element #; helpers/template sensors to create)
## Preview            (Artifact URL)
## Approved           (date, plus anything Kevin said to change during the build)
```

Then tell Kevin: "Run `/dashboard-build .claude/designs/<file>` to build it on the scratch dashboard."

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Going straight to YAML or scratch screenshots | Feasibility table → preview → approved note. Building is `/dashboard-build`'s job. |
| Proposing a card without checking the allowlist | Every `installed-card` row names a type that matches `installed-cards.yaml`. |
| Showing the mockup's own look in the preview | Render the achievable version under Walnut tokens. |
| Treating "looks slightly different" as "native" | Put the difference in "closest alternative". |
| Guessing entity IDs from names | `ha_search`, then confirm with `ha_get_state`. |
| Asking ten questions | Only the ones that change the build, each with a recommendation. |
