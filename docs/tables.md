# Tables subsystem (Creeps / Unit Abilities / Mana Items)

Separate from the patch-notes pipeline (`build_patch.py`, see [architecture.md](architecture.md)).
This covers the sortable data tables under the **Materials** section.

## Pages & builders

| Page | Content | Builder |
|---|---|---|
| `neutral_creeps.html` | **Neutral Creeps** table (stats + abilities). `creeps.html` and `materials.html` are now redirects → `neutral_creeps.html`. | `build_creeps.py` |
| `neutral_abilities.html` | Per-unit-ability table (one row per unit×ability). The Materials sub-nav presents it as a child of Neutral Creeps. `unit_abilities.html` is now a small meta-redirect for backwards compatibility. | `build_creeps.py` (same run) |
| `mana_items.html` | Mana / mana-regen items + gold-efficiency metrics. | `build_mana_items.py` |
| `heroes_dyn.html` | **Hero Dynamics matrix** — rows = every hero (icon+name, alphabetical), columns = every patch (version + release date oldest→newest), each cell = that hero's patch-dynamics **dyn-cell** for that patch. Same diamond-pill widget as patch pages. | `build_heroes_dyn.py` |
| `items_dyn.html` | **Item Dynamics matrix** — like heroes_dyn but rows = every item/enchantment touched across tracked patches (172: 101 regular + 49 neutral + 22 enchant). Adds an **In game** toggle (hide removed/obsolete items, ON by default) + a **Show** class filter (Items / Neutral Items / Enchantments). | `build_items_dyn.py` |
| nav / asset version / `data/site_meta.json` | Shared header, sub-tabs, cache-busting. | `site_common.py` |

Header sub-tabs (under the logo) switch between Neutral Creeps / Unit Abilities / Mana Items.

## Build order (IMPORTANT)

```bash
# On Windows always:  PYTHONIOENCODING=utf-8
python build_patch.py        # 1. writes data/site_meta.json (asset version, patch list)
python build_creeps.py       # 2. -> neutral_creeps.html + neutral_abilities.html (+ creeps/materials/unit_abilities redirects)
python build_mana_items.py   # 3. -> mana_items.html  (run AFTER build_patch)
python build_heroes_dyn.py   # 4. -> heroes_dyn.html  (run AFTER build_patch — reads _dynamics.json)
python build_items_dyn.py    # 5. -> items_dyn.html   (run AFTER build_patch — reads _dynamics.json)
```

### Shared dynamics renderer (`dyn_matrix_common.py`)
Both dynamics pages call `dyn_matrix_common.save_dyn_matrix(...)` — the matrix
renderer is **entity-agnostic**. `build_heroes_dyn.py` passes the hero config
(`kind="hero"`, `roster_key="heroes"`, `icon_dir="icons/heroes"`, …),
`build_items_dyn.py` the item config (`kind="item"`, `roster_key="items"`,
`icon_dir="icons/items"`, `from_token="items_dyn"`, …). Both emit the SAME
`class="creeps-table heroes-dyn-table"` so the shared CSS + `scripts.js`
(`dynBuildMatrix`/`dynLayoutMatrix`/`dynSetupMatrix`) apply unchanged.
- `build_patch.py` writes BOTH rosters into `_dynamics.json` (`heroes` = full
  HERO_SLUG roster; `items` = every `item|<slug>` entity touched in any tracked
  patch, with its icon slug stamped in `_register_entity`).
- **Back-arrow token is data-driven:** each page sets `<body data-dyn-from=...>`;
  `dynFillMatrix` reads it so a clicked cell's patch page returns to the right
  matrix (`?from=heroes_dyn` / `?from=items_dyn`, handled in the back-arrow IIFE).
- **index Dynamics tile** opens an in-place sub-panel (same generic mechanism as
  Support: `data-panel-open`/`data-panel-close`, `.<name>-open` book class) with
  Heroes → heroes_dyn and Items → items_dyn.

### Item classification (items_dyn) — from the GAME FILES, not patch notes
`build_patch.py::_load_item_classes(version)` parses the latest
`data/stats/<ver>/items.txt` (authoritative Valve KV):
- **neutral item** — block has `"ItemIsNeutralActiveDrop" "1"`.
- **enchantment** — slug prefix `item_enhancement_` (these are NOT neutral-flagged).
- **removed/obsolete** — `"IsObsolete" "1"` (still in the file for old replays, but
  out of the game, e.g. Cornucopia / Eternal Shroud).
- **regular** — present, not neutral, not obsolete.
- ⚠ Neutral items also carry `ItemPurchasable "0"` — do NOT use purchasable as the
  removed signal; use `IsObsolete`.

`_register_entity` stamps each item/enchant entity's `icon` slug (item → ITEM_SLUG;
enchant → `enhancement_<slug>`; game slug for both = `item_<icon>`) plus a
`neutral_section` fallback (set under `section("Neutral Item Updates")`) for the
rare neutral that's been fully removed from the game file. `build_patch` writes the
enriched **items roster** into `_dynamics.json` — each entry has `class`
(`regular`/`neutral`/`enchant`) and `current` (in game vs removed). The
section-based method and the game-file method agree 100% (cross-checked: 49/49
neutral, 0 false pos/neg).

The items_dyn controls (`current_toggle` / `class_filter` / `price_filter` params
of `save_dyn_matrix`) put `data-class` + `data-current` + `data-price` on each
`<tr>`; `scripts.js dynSetupMatrix` combines name-search + class chips + "Show
deleted" toggle + price min/max into ONE visibility pass (no-ops on heroes_dyn,
whose roster lacks those fields). **Price** = latest items.json `ItemCost`; items
with no cost (neutrals/enchants = 0 → roster `price=None`, no `data-price`) are
EXEMPT from the range filter. The price widget reuses mana_items' `.mr-price-range`
markup/CSS with `hd-price-*` ids.

**Unified toolbar panel:** all dynamics controls live inside ONE bordered surface
`.hd-tb-inner` (not separate floating pills). Inside it the switches + filter
groups go flat (transparent), separated by thin dividers (switches | Remove |
Show | Price), search flush right. Tag/class chips keep their own design. The
outer `.hd-toolbar` keeps the 28px Materials side inset + top/bottom rhythm gaps.

### Item lifespan — blanked cells outside [added … removed]
Each items roster entry also carries `added` + `removed` patch versions so the
matrix only draws the item's slots WITHIN its life:
- **added** = oldest patch whose `items.json` contains `item_<slug>` (every one of
  the 116 patches has items.json → authoritative; e.g. Searing Signet = 7.38).
  Columns before `added` render `td.hd-cell.hd-absent` (a faint "n/a" dot, not the
  empty-slot square).
- **removed** = the patch where the entity itself is removed, stamped in `li()`
  → `rec["removed_in"]`. This is the AUTHORITATIVE removal signal and overrides the
  game-file `current` (`current = game-file-current AND removed_in is None`).
  Columns after `removed` are blanked; the row is `data-current="0"` (hidden unless
  the **Deleted** toggle is on). Detection is gated on the **DEL** tag (all entity
  removal/pool-exit rows carry it) and matches the phrasings PRECISELY:
  - bare `"Removed"` (enchants — **Wise / Boundless / Vast**, removed 7.41),
    `"Item removed from the game"` (items — Cornucopia / Eternal Shroud), and
    `"Item cycled out"` (neutrals rotated OUT of the pool — Spark of Courage,
    Ripper's Lash, Gale Guard … 9 in 7.40 + Whisper of the Dread 7.41).
  - ⚠ The cycle-out rows are authored as `t("DEL")` (a pool exit IS a removal) —
    don't tag them MISC.
  A **returned guard**: if the entity is touched in a patch strictly NEWER than its
  removal/cycle-out patch, it came back → `removed` cleared, current again.
  ⚠ NEITHER game file detects these: items.json keeps obsolete items as keys
  (Cornucopia is still a 7.41d key); items.txt keeps removed ENCHANT + cycled-out
  NEUTRAL definitions WITHOUT `IsObsolete`. Only the patch note does. ⚠ Must NOT
  match `"Facets removed from the game"` (Crude keeps living) nor
  `"Removed <facet/ability>"` (a sub-feature, e.g. Riftshadow Prism's facet list).
  Currently 15 not-current: 3 enchants + 2 items removed + 10 cycled-out neutrals.
  (NB: Liquipedia's changelog summary disagreed — it's stale on the 7.41 enchant
  removals and the cycle-outs; the Valve patch notes in build_patch.py are truth.)
- A touched cell (has a tag tally) ALWAYS renders its pill, even if the lifespan
  math would blank it (a touch means it existed). heroes_dyn rows have no
  added/removed → nothing is blanked there (could be wired later via heroes.json).

### Hero Dynamics matrix (`build_heroes_dyn.py`)
- Reads **`_dynamics.json`** (written by build_patch): `patches` (newest-first), `entities`
  (`hero|<slug>` → per-patch tag tallies), and **`heroes`** (full roster `[{name, icon, key}]`,
  added so every hero lists even if untouched in a rendered patch). build_patch also stamps an
  `icon` field on each hero entity. build_heroes_dyn does **not** import build_patch (no `__main__`
  guard there).
- Table = `creeps-table heroes-dyn-table`, ONE sticky-col (hero icon+name), single `col-row`
  header (no cat-row), 115 patch columns oldest→newest. `<body data-dyn-path="_dynamics.json">`
  tells `scripts.js` where to fetch the manifest (patch pages use the default `../_dynamics.json`).
- **Cells:** the builder marks only *touched* cells with `data-ver/data-hkey/data-eid`; `scripts.js`
  `dynBuildMatrix()` fills those with a coloured pill (reusing `dynBuildPill`, so colour logic stays
  single-sourced). Untouched cells are `td.hd-cell.hd-empty` → a static empty diamond via CSS
  `::after` (keeps the ~14k-cell grid's HTML light; runtime work scales with real data only).
- Clicking a pill → `patches/<ver>.html#dyn-hero-<slug>` (filePrefix `'patches/'` passed to
  `dynBuildPill`). The `.dyn-cell`/`.dyn-cell-wrap` CSS was de-scoped from `.patch-dynamics` so the
  pill renders anywhere.
- **Layout (`scripts.js` `dynLayoutMatrix`, runs on load + resize):** `table-layout: fixed; width:
  max-content` (override `.creeps-table`'s `min-width:100%`). Column widths are CSS vars set live:
  `--hd-hero-w` = longest hero name measured at runtime + icon + gap + zoom clearance (so names
  never wrap and icons/names line up); `--hd-col-w` = patch-column width (28px pill, `box-sizing:
  border-box`). ONE sticky-col (hero), single `col-row` (no cat-row). Patch headers show only the
  version; the **release date is a hover tooltip** (`th.hd-patch[data-tooltip]`, in `TIP_SEL`).
- **Fit-to-width / latest flush right:** `dynLayoutMatrix` shows the most-recent patches that fit
  the box width (sized to fill it exactly, latest column flush at the right edge) and hides the
  older ones via a SINGLE injected `<style>` rule (`:nth-child` range — cheap vs toggling thousands
  of cells). "Hide old" OFF shows all 115 (scroll, parked at the right so the latest stays in view).
- **Toolbar toggles** (styled as the shared `.ua-upgrades-toggle` switches, wired in `dynSetupMatrix`):
  - `#hd-hide-old` (ON by default) → fit-to-width (above). OFF → all patches, scroll.
  - `#hd-bn-only` (off) → rebuilds pills via `dynFillMatrix(...,bnOnly)` → `dynBuildPill(...,bnOnly=true)`
    collapses the gradient to TWO bands: **buff+NEW = green, nerf+DEL = red** (NEW counts as a buff,
    DEL as a nerf), proportioned to fill the cell. Tooltip still shows every original tag.
- **Click → patch page + back:** pills pass `fromVersion='heroes_dyn'` so the destination patch page
  shows a `.nav-back-arrow` returning to `../heroes_dyn.html` (handled in the back-arrow IIFE,
  alongside `from=calendar` / `from=<patch>`). The patch page **re-anchors** to `#dyn-hero-<slug>`
  after `dynInit` renders the per-entity pill rows (each adds ~28px, drifting the target down) and
  again on `load` (lazy-image drift), offsetting for the sticky nav.

### Cross-table RULES (apply to every table page — confirmed conventions)
1. **Even grid:** equal, fixed-width columns so cells line up on clean vertical lines.
2. **Hover-zoom above the sticky header:** a hovered/zoomed *content* element (dyn-cell, etc.) must
   sit ABOVE the pinned header, never behind it. The scroll box is the stacking context
   (`contain:paint`), so bumping the hovered element's `z-index` over the header's (50/51) lifts it
   clear. (Exception kept from Neutral Creeps: the row *portrait* zoom intentionally stays UNDER the
   header — it lives in a `sticky-col` at z3.)
3. **Portrait hover-zoom that doesn't cover text:** icon scales on `td:hover` (like Neutral Creeps),
   with enough `gap` in the icon+name flex so the zoom never overlaps the name.
4. **Identical left alignment — use the shared shell AS-IS:** do NOT add per-page padding to
   `.creeps-scroll`. Every Materials page must keep the SAME left positions — subnav `.materials-
   subnav-inner` 10px, blurb/toolbar 28px, table flush (0). (An earlier per-page `padding-left`
   on heroes_dyn shifted its subnav + table right of the others — that's the bug to avoid.)
5. **Sortable headers:** every sortable `<th>` carries `class="sortable"` + `data-col` (+`data-idx`
   for body-cell mapping) AND a `<span class="sort-ind"></span>` so the ↕/↑/↓ arrow renders. The
   shared JS gives a 3-state cycle: neutral → descending → ascending → neutral.
6. **Row-mark = one band + frame:** the gold `.row-marked` is a single inset frame around the whole
   row + a uniform tint (see Neutral Creeps). Any decorative per-cell fill (e.g. heroes_dyn's empty
   diamonds) must be dropped inside a marked row (`tr.row-marked …::after{background:transparent}`)
   so it doesn't read as separate per-cell boxes.
7. **Edge hover-pop clearance:** a hovered cell's zoom-pop overflows its cell (~18px for the 2.5×
   dyn-cell). Keep a right gutter (heroes_dyn: `HD_RIGHT_GUTTER` in `dynLayoutMatrix`) so the last
   column's pop isn't clipped by the box edge / vertical scrollbar.
8. **Big-grid paint:** for very large grids (heroes_dyn ≈ 14k cells), keep the bulk cell cheap to
   paint — flat fill, NO `box-shadow` (thousands of inset shadows were the scroll-jank source; flat
   fills scroll at 100+ FPS). Hidden columns use `display:none` (skipped from layout/paint).
9. **First-column override:** the shared `.creeps-table td:first-child` rule forces center-align + a
   symbol font + `white-space:normal` (for tier-dot glyphs). Any table whose first column is NOT
   tier-dots (e.g. heroes_dyn's hero name) must override these — and needs HIGHER specificity than
   `.creeps-table td:first-child` (equal-specificity loses on source order): prefix with the table's
   own class, e.g. `.creeps-table.heroes-dyn-table td.hd-hero`.
10. **Super-category header (colspan) ⇒ use `table-layout:auto`:** a colspan'd category row as the
    FIRST `<thead>` row makes `table-layout:fixed` derive column widths from it (ignoring the leaf
    columns). Use `table-layout:auto` + `width/min-width/max-width` on the leaf cells to force an
    equal grid; recompute the category colspans to the VISIBLE leaf columns after any column-hide
    (see `dynRecomputeSupercats`, keyed by `data-base`/`data-cat`). Don't put `overflow:hidden` on a
    cell whose content hover-pops (clips the pop) — clip the header label cell only.

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
Note `.creeps-page` is shared by **all three** Materials tables (neutral_creeps.html,
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

### Overall net-change summary (tooltip top line)
Cells flagged `data-net=""` (a value cell that changed **>1 time**) get an extra line at the
**TOP** of the hover tooltip, above the newest patch, with a divider:
`overall <first observed> → <today> <pct>%`. Built by `netSummary()` in `scripts.js`:
- scans past `A`/`R`/`P` markers to the **first and last real value entries** (`valEntry()`
  handles `V`/`F`/`C`/`N`; `C` uses the raw numerics for the %, the pretty values for display);
- needs ≥2 value entries; net **0%** (drifted then returned to start) is still shown (`flat`);
- colour = buff/nerf via `.stat-pct up/down/flat`; label is "overall".

Who flags `data-net`:
- **Neutral Creeps** — every numeric `COL_HIST` cell (`build_creeps.py`), NOT ability cells.
- **Mana Items** — every `_cost_cell`/`_metric_cell` (`build_mana_items.py`). These also
  **dropped `data-name`** (the item-name tooltip header was a redundant duplicate; the row
  already identifies the item). The blurb's `_int_const_chip` keeps its `data-name`.
- **Neutral Abilities** — no per-patch history (current-patch snapshot) → no summary.
CSS: `.stat-hist-tip .stat-net` (divider) + `.stat-net-label`.

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
