# Tables subsystem (Creeps / Unit Abilities / Mana Items)

Separate from the patch-notes pipeline (`build_patch.py`, see [architecture.md](architecture.md)).
This covers the sortable data tables under the **Materials** section.

## Pages & builders

| Page | Content | Builder |
|---|---|---|
| `materials.html` | **Neutral Creeps** table (stats + abilities). `creeps.html` is now a redirect → `materials.html`. | `build_creeps.py` |
| `neutral_abilities.html` | Per-unit-ability table (one row per unit×ability). The Materials sub-nav presents it as a child of Neutral Creeps. `unit_abilities.html` is now a small meta-redirect for backwards compatibility. | `build_creeps.py` (same run) |
| `mana_items.html` | Mana / mana-regen items + gold-efficiency metrics. | `build_mana_items.py` |
| nav / asset version / `data/site_meta.json` | Shared header, sub-tabs, cache-busting. | `site_common.py` |

Header sub-tabs (under the logo) switch between Neutral Creeps / Unit Abilities / Mana Items.

## Build order (IMPORTANT)

```bash
# On Windows always:  PYTHONIOENCODING=utf-8
python build_patch.py        # 1. writes data/site_meta.json (asset version, patch list)
python build_creeps.py       # 2. -> materials.html + neutral_abilities.html (+ unit_abilities.html redirect)
python build_mana_items.py   # 3. -> mana_items.html  (run AFTER build_patch)
```

`site_common.py` reads `data/site_meta.json`, so `build_patch.py` must run first.
Generated HTML is **gitignored** and rebuilt by CI; only the `.py` / `styles.css` /
`scripts.js` sources are committed.

`styles.css` and `scripts.js` are **source files, hand-edited directly** — shared by
every page including the patch notes.

## Data sources (tables)

| File | Provides |
|---|---|
| `data/creeps_raw.csv` | creep order, level, `createhero` shortcut, attack-type |
| `data/stats/<patch>/items.json` | per-patch item stats (cost, mana, regen…) → cell history |
| `data/stats/<patch>/units.json` | per-patch unit stats (HP, armor, mana, dmg) |
| `data/stats/<patch>/npc_units.txt` | 7.41c-only: regen, bounty, vision, magres, abilities |
| `data/stats/<patch>/npc_abilities.json` | per-patch neutral ability balance (`av_*`) |
| `data/abilities_english.txt` | ability + **item** tooltip descriptions (icon hover) |
| `data/abilities_slim.json` | ability display names (`dname`) |

Note: KV engine slug ≠ in-game display name (e.g. `frostmourne` → "Curse of Avernus").
`createhero` CSV shortcuts ≠ URL slugs.

## Scroll / sticky architecture (the tricky part)

**Neutral Creeps & Unit Abilities** scroll inside an inner box `.creeps-scroll`
within a non-scrolling `.creeps-page`. This exists to:
- freeze identity columns on the LEFT (`.sticky-col`, JS sets per-cell `left`), and
- draw frozen-pane dividers as **overlay divs** (`.sticky-frame` vertical) because
  **Chrome drops `box-shadow`/`border` on `position:sticky` cells mid-scroll**.

**One scrollbar, not two.** The box is `overflow:auto; position:sticky; max-height:
calc(100vh − nav − 24px)`, and the PAGE is locked via
`body:has(.creeps-scroll){overflow:hidden}` (+ 12px top/bottom `.creeps-page`
padding) so ONLY the box scrolls — one vertical scrollbar, plus a horizontal one
for the wide table. (History: we briefly tried page-level scroll for these two
tables on 2026-06-01, but the wide Unit Abilities table overflowed/looked broken,
so we reverted to this contained box.)

**Mana Items** now uses the **same `.creeps-scroll` box** as the other two (since
2026-06-02) so all three Materials pages share one shell: identical header, the
Materials sub-nav INSIDE the box, blurb + toolbar as `inbox-bar` (sticky-left, scroll
away), and the table header pinned at `top:0` of the box. It has no frozen identity
columns, so it skips the `.sticky-frame` overlays (the creeps sticky-column JS no-ops on
`.mr-table`). Earlier it page-scrolled (rows sliding under the glass nav) — that was the
odd one out and was unified away. `.mr-table thead th` pins at `top:0` (was a page-level
`top: var(--mr-thead-top)`).

### scrollbar-gutter convention
`html { scrollbar-gutter: stable }` is the **default** (styles.css top) — it reserves the
scrollbar track so the layout doesn't jump horizontally when filtering changes a page's
height (patch notes, silent changes). Pages that DON'T page-scroll opt out, otherwise the
reserved track shows as an empty gap on the right:
```css
html:has(.main-page),      /* single-screen index            */
html:has(.calendar-page),  /* calendar — fits the screen     */
html:has(.creeps-page)     /* Neutral Creeps / Neutral Abilities / Mana Items */
{ scrollbar-gutter: auto; }
```
Note `.creeps-page` is shared by **all three** Materials tables (materials.html,
neutral_abilities.html, mana_items.html), and **all three now lock the page and scroll
inside `.creeps-scroll`** (one scrollbar inside the box). **New page rule:** single-screen
or self-scrolling → give it one of these classes (or add to the opt-out); long filterable
page → leave the default `stable`.

### Two-row sticky header (Neutral Creeps)
- `<tr class="cat-row">` (BASIC / VITALITY / …) sticks at `top: 0` (of the box).
- `<tr class="col-row">` (Lvl / Unit / HP …) sticks at `top: calc(var(--cat-row-h) - 2px)`.
- `--cat-row-h` is set by `scripts.js` from the category row's measured height.
  Unit Abilities has no `.cat-row` → its single header row pins at `top: 0`.
- The col-row carries an upward `box-shadow: 0 -14px 0 0 #161b22` that fills any
  rounding gap between the two pinned rows; the cat-row (higher z-index) paints over
  the overlapping part. This is what actually kills the "body shows through the gap"
  bug — a `-2px` pull-up alone wasn't enough when `--cat-row-h` rounded high.
- The blue scrolled-edge line is painted **flush** as an `inset box-shadow` on the
  col-row bottom (matching Mana Items) — NOT a separate horizontal overlay (that left a gap).

### z-index ladder (`.creeps-table`)
- body cells `0`, sticky-col body `3`, hover-zoom (`.creep-icon-cell:hover`,
  `.ua-ability:hover` `40`; `.abil-ico-wrap:hover` `30`),
  header `th` `50`, header corner sticky-col `51`, **category row `52`**.
- The header sits ABOVE the hover-zoom (40/30) — ⚠ the zoom rule lives at
  `styles.css` ~3395 (`z-index:40`), so the header MUST stay above 40, else a hovered
  row near the top paints over the pinned header.

## Highlight / interaction (`scripts.js`)
- **Click a row** → `.row-marked` (gold frame), single-select.
- **Anchor jump** (`#unit-ability` from a link) → `centerHash()` scrolls + applies the
  same `.row-marked` (replaced the old yellow `:target` flash).
- **Cross-hover** lights the hovered row + column by `cellIndex`.
  ⚠ Because it's positional, a semantically-shared ability must sit in the SAME column
  across rows to co-highlight — e.g. **Riverborn Aura is pinned to Ability 1 for every
  frog unit** (see `build_creeps.py`, the `abilities.sort(...)` on the riverborn slug).

## Cell change-history tooltips (`data-hist`)
Payload: `patch|date|KIND|…` segments joined by `;`. Decoded in `scripts.js` `entryParts()`.

| KIND | Meaning |
|---|---|
| `A` / `R` / `P` | ability Added / Removed / Replaced |
| `V` | stat value change `old→new` + % (polarity `hi`/`lo`) |
| `F` | labelled ability value change |
| `N` | value change, **no %** |
| `C` | **computed column**: pretty short display + % computed from RAW values carried alongside (`…|disp_old|disp_new|raw_old|raw_new|pol`). Needed because `_short_plain` renders ≥1000 as thousands "5,0" but <1000 as "714" — different scales would skew a %. |

Mana-metric history (`build_mana_items.py load_metric_history`) is built by diffing each
patch's `items.json`; only patches whose JSON carries the **deep mana fields** count —
those exist from **7.33 onward** (older slim JSON has only `ItemCost`). So mana history
starts at 7.33 and runs forward; a missing tail just means a stale rebuild.

## Mana Items specifics (`build_mana_items.py`)
- Intelligence: +12 max mana, +0.05 regen per point (7.41c engine constants).
- Items whose ACTIVE restores mana (Arcane Boots) are split into a base row + hidden
  `(Active)` sub-row (`mr-active-row`, toggled by "Hide Active").
- **Active-only** items (Soul Ring — no passive regen) render as a single
  `Name (Active)` row also tagged `mr-active-row`.
- Item **icon hover tooltip**: reuses the global `.abil-ico-hint` + `data-tooltip`
  (`scripts.js` renders it as innerHTML). Built by `_item_tooltip_html()` — splits the
  Valve description on `<h1>Active:/Passive:</h1>` into separate `<br>` lines.
  ⚠ `%value%` placeholders are NOT resolved → "for seconds" (no number).

## Conventions
- Dota attribute colours (str/agi/int/uni) — canonical hex, see `MEMORY.md`.
- Dark theme, glass nav, heatmap cells, sticky polish; user reviews locally via Ctrl+F5
  (no preview servers / screenshots) and triggers deploys himself.
