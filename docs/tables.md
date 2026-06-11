# Tables subsystem (Creeps / Unit Abilities / Mana Items)

Separate from the patch-notes pipeline (`build_patch.py`, see [architecture.md](architecture.md)).
This covers the sortable data tables under the **Materials** section.

## Pages & builders

| Page | Content | Builder |
|---|---|---|
| `neutral_creeps.html` | **Neutral Creeps** table (stats + abilities). `creeps.html` and `materials.html` are now redirects → `neutral_creeps.html`. | `build_creeps.py` |
| `neutral_abilities.html` | Per-unit-ability table (one row per unit×ability). The Materials sub-nav presents it as a child of Neutral Creeps. `unit_abilities.html` is now a small meta-redirect for backwards compatibility. | `build_creeps.py` (same run) |
| `mana_items.html` | Mana / mana-regen items + gold-efficiency metrics. | `build_mana_items.py` |
| `heroes_stats.html` | **Hero Stats** — one row per hero (127), every base stat. Three View modes (`#hs-view-mode`): **Base** = raw KV values; **Starting** (default) = level-1 values WITH attribute bonuses; **Expanded** = Starting + extra inspection columns (`Gains/lvl`, `Armor %`, `Dmg min/max`, `Time to hit`, projectile speed, turn rate, collision size, bound radius). Header groups mirror Neutral Creeps: Basic / Essentials / Attributes / Defense / Attack / Vision / Mobility. Cells whose value differs between Base & Starting carry `data-base-sort/-html/-hist`; the View IIFE swaps them. **Per-hero special cases:** Huskar MP/regen forced to 0; Ogre Magi mana/regen scale with Str. **Innate attribute-conversion modifiers** (`_innate_bonus`, patch-gated): Morphling Ebb&Flow Agi→Range/MoveSpeed (7.41+, 0.2→0.25 range @7.41d), Void Spirit Intrinsic Edge (+33% secondary bonuses in 7.36, +25% in 7.36b–7.40, then 7.41+ = Universal damage multiplier ×1.15 plus +30% HP regen / mana regen / attack speed from Str/Int/Agi, no armor/MR), Centaur Horsepower Str→MoveSpeed (7.36+). Every numeric cell carries full 7.08→today change history (`data-hist`+`data-net`); attribute cell logs primary-attr swaps. **Patch-note shift layer** shifts KV-detected changes back to the patch that `patchnotes_english.txt` announces. Reuses mr-table front-end (`mr-table hs-table`) with its own Neutral-Creeps-style two-row header. | `build_heroes_stats.py` |
| `heroes_dyn.html` | **Hero Dynamics matrix** — rows = every hero (icon+name, alphabetical), columns = every patch (version + release date oldest→newest), each cell = that hero's patch-dynamics **dyn-cell** for that patch. Same diamond-pill widget as patch pages. | `build_heroes_dyn.py` |
| `items_dyn.html` | **Item Dynamics matrix** — like heroes_dyn, rows = **every real game item** (parity with heroes_dyn listing every hero), columns = every patch. Untouched items render as empty rows. Currently **350** (199 regular + 129 neutral + 22 enchant); 91 not-current (incl. 80 cycled-out neutrals — only the live pool of 49 shows by default), every one with an accurate removal patch. Adds an **In game** toggle (hide removed items, ON) + Type & Category multi-select dropdowns. | `build_items_dyn.py` |
| nav / asset version / `data/site_meta.json` | Shared header, sub-tabs, cache-busting. | `site_common.py` |

Hero Stats current layout note: `heroes_stats.html` uses a Neutral-Creeps-style
two-row header with Basic / Essentials / Attributes / Defense / Attack / Vision /
Mobility groups. Expanded mode no longer shows STR30/AGI30/INT30, Total lvl 1,
Total lvl 30, or Gains by lvl 30. Expanded-only columns are `Gains/lvl`,
`Armor %`, `Dmg min`, `Dmg max`, `Time to hit`, projectile speed, turn rate,
collision size, and bound radius.

Header sub-tabs (under the logo) switch between Neutral Creeps / Unit Abilities / Mana Items.

## Build order (IMPORTANT)

```bash
# On Windows always:  PYTHONIOENCODING=utf-8
python build_patch.py        # 1. writes data/site_meta.json (asset version, patch list)
python build_creeps.py       # 2. -> neutral_creeps.html + neutral_abilities.html (+ creeps/materials/unit_abilities redirects)
python build_mana_items.py   # 3. -> mana_items.html  (run AFTER build_patch)
python build_heroes_stats.py # 3b. -> heroes_stats.html (run AFTER build_patch — needs site_meta dates)
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

### Full item roster (`build_patch.py::_load_full_game_items`) — list EVERY item
The roster is NOT just touched items — it lists every real game item so the matrix
matches heroes_dyn (which lists every hero). Untouched items render as empty rows.
Inclusion mirrors **Liquipedia's Portal:Items** (the reference the user gave).
- **Touched items** come from the dynamics (`_State.dynamics`, kind `item`/`enchant`)
  with the full lifespan/removal data (`removed_in`, tallies). Built first.
- **`_load_full_game_items()`** then adds every other real item from the latest
  `items.txt` + display names from `data/itemlist.json` (slugs are often legacy joke
  names — `item_angels_demise` = "Khanda", `item_gungir` = "Gleipnir", `item_royale_with_cheese`
  = "Block of Cheese" — so the datafeed `name_english_loc` is authoritative; titlecased-slug
  fallback for the few missing). **Kept:** has `icons/items/<icon>.png`, not `item_recipe_*`;
  all neutrals + enchantments; regular shop items with `ItemPurchasable != 0` AND `ItemCost > 0`;
  a small `_FREE_ALLOW` allowlist of free / boss-reward / collectible items (Aegis, Cheese,
  Refresher Shard, Roshan's Banner, Healing Lotus ×3, Block of Cheese, Madstone, Observer Ward,
  Aghanim's Blessing); and **removed items** (`IsObsolete`) — kept too, `current=False`.
  **Dropped:** numbered / level VARIANTS (`_2..9`, `_roshan`, `_broken`, `tango_single`) EXCEPT
  the distinct named `item_ultimate_scepter_2` (Aghanim's Blessing); a blocklist `_ITEM_BLOCK`
  + River Vials (Bag of Gold, caster_rapier, pocket_roshan, `item_river_painter*`); and
  **unreleased FREE items** (apex, ofrenda*, grisgris, philosophers_stone … — auto-dropped:
  free and not in `_FREE_ALLOW`, which is exactly why the cost filter on regulars is kept).
- **Lifespan / n/a dots** (`_presence_window`): scans every patch's `items.json` for the item
  → `added` = first appearance (columns before render faint "n/a" dots), and if it has left the
  files, `removed` = last appearance. ⚠ `items.json` keeps OBSOLETE item keys forever (Necronomicon
  is still a 7.41d key), so presence can't date those removals → `_OBSOLETE_REMOVED` hardcodes the
  patch-note-confirmed removal version for the 8 untouched classics (Necronomicon 7.29, Hood of
  Defiance / Flicker / Nether Shawl / Wraith Pact / Tome of Knowledge 7.33, Stout Shield 7.23
  [Liquipedia], Quarterstaff 7.35). Touched removals come from the patch-note DEL row (`removed_in`).
- **Dedup** is by the icon's game slug (`item_<icon>`): a touched item already has the richer entry,
  so its game-file twin is skipped. (User's choice: "all items, no variants / event-only pickups";
  removed items kept with correct lifespans.) Current total: **350** (199 reg + 129 neut + 22 ench);
  91 not-current. **Class of an item that changed type over time = its LATEST class** — e.g.
  Specialist's Array was a neutral, now a purchasable regular → classified `regular`; its n/a dots
  correctly precede 7.32 (its first appearance), no mid-life gap (it stayed in the files throughout).

#### Neutral pool — current vs cycled-out (`_NEUTRAL_POOL_CURRENT`, AUTO-DERIVED)
The game files CANNOT tell an active neutral from a cycled-out one: items.txt keeps every dropped
neutral flagged `ItemIsNeutralActiveDrop "1"` forever and never marks it `IsObsolete`. The **live
pool is auto-derived from Valve's datafeed** (`data/itemlist.json`, field `neutral_item_tier >= 0`)
by `_load_neutral_pool_current()` — no hand-maintained list. ✅ **Self-updating:** when a new patch
lands, run `python scripts/fetch_itemlist.py` to refresh `itemlist.json`, then rebuild; added /
removed / cycled neutrals are picked up automatically (currently **49** in pool). The datafeed is
authoritative — a hand-written Liquipedia list was tried first but silently missed Cloak of Flames /
Dandelion Amulet / Medallion of Courage (all re-added as neutrals in 7.41), which the datafeed has.
A neutral's `current` = membership in that set (applied in BOTH `_item_class_and_current` for touched
neutrals AND `_load_full_game_items` for untouched ones; an item in the datafeed pool is also forced
to `class=neutral`, e.g. Medallion of Courage which left the shop). Pool membership overrides any
stale `removed_in`. Everything else flagged-neutral = cycled out → `current=False` (hidden under the
Deleted toggle). Cycle-out **version** for the lifespan tail comes from `_NEUTRAL_CYCLED`: patch-note
"cycled out" events (~7.33+) merged with `_NEUTRAL_REMOVED_MANUAL` (49 older neutrals dated from their
Liquipedia /Changelogs pages — mostly the 7.38 neutral overhaul), so every cycled-out neutral has an
accurate n/a tail. Never-released entries are excluded entirely via `_PHANTOM_ITEMS`: 3 neutrals
(Bottomless Chalice / Horizon / Mechanical Arm — "Added to game files, unreleased") + 5 enchantments
that never appeared in any patch note and have no Liquipedia page (Unleashed/curious, Dominant, Fierce,
Restorative, Thick). Released-then-removed enchants (Wise / Boundless / Vast) stay as removed.
⚠ Legacy joke slugs: Stygian Desolator = `desolator_2` (a current tier-5 neutral, so it's exempt
from the `_2` variant drop), Book of the Dead = `demonicon`, Witchbane = `heavy_blade`, Tumbler's
Toy = `pogo_stick`. **Phantom neutrals** flagged BOTH neutral AND `SpeciallyBannedFromNeutralSlot`
(Greater Mango, Greater Faerie Fire — never shipped) are in `_PHANTOM_ITEMS` → excluded entirely.

#### Search aliases (`dyn_matrix_common._search_alias`)
Each row's identity `<td>` carries a `data-alias` of extra search keywords so the placeholder's
promise ("aghs") works: a manual abbreviation map (`_ITEM_SEARCH_ALIASES`: aghs→Aghanim's Scepter,
bkb, mkb, deso, euls, pms, sny, hotd, midas …) plus an auto **acronym** of the words (Black King
Bar→bkb; on heroes_dyn this also gives cm→Crystal Maiden, pa→Phantom Assassin). `scripts.js`
`applyRowFilters` matches each search term against `data-sort` (name) OR `data-alias`.

The items_dyn controls (`current_toggle` / `class_filter` / `price_filter` /
`category_filter` params of `save_dyn_matrix`) put `data-class` + `data-current` +
`data-price` + `data-category` on each `<tr>`; `scripts.js dynSetupMatrix` combines
name-search + the dropdowns + "Show deleted" toggle + price min/max into ONE
visibility pass (no-ops on heroes_dyn, whose roster lacks those fields). **Price** =
latest items.json `ItemCost`; items with no cost (neutrals/enchants = 0 → roster
`price=None`, no `data-price`) are EXEMPT from the range filter.

#### Multi-select dropdowns (`dyn_matrix_common._multiselect_dropdown` + `initHdDropdowns`)
**Type** and **Category** lead the toolbar — each ONE control = a flat button that
opens a checkbox popover (not a row of loose chips). The builder emits
`.hd-dd[data-dd="<key>"]` with a button (`.hd-dd-btn` + gold `.hd-dd-badge`) and a
`.hd-dd-menu[data-dd="<key>"]` holding a top **"All"** checkbox (`data-dd-all`, toggles
every option) + option `<input data-<key>="<value>">`. `initHdDropdowns`:
- **portals each menu to `<body>`** and positions it `fixed` under the button — so
  `.creeps-scroll`'s `contain:paint` can't clip it and an empty table can't push a
  scrollbar (the earlier bug). Closes on outside-click / scroll / resize.
- badge shows **"all"** when every option is checked, else the count (`applyRowFilters`
  finds each menu by `data-dd` since it now lives on `<body>`, not inside `.hd-dd`).
- a row with **no** `data-<key>` is EXEMPT (so Category never hides neutrals/enchants).
- **Type** (`class`): Items / Neutral Items / Enchantments. Default: Items only.
- **Category** (`category`): the shop tabs (Consumables / Attributes / Equipment /
  Miscellaneous / Accessories / Support / Magical / Armor / Weapons / **Armaments** /
  Secret Shop / Other). Default: all selected. Source = `data/shops.txt` (the game's
  shop layout, extracted by `scripts/extract_shops.py`); `build_patch._load_shop_categories`
  maps each item to its FIRST shop section (sideshop/pregame/event sections excluded;
  the `"magics" // Magical` inline comment must be tolerated by the section regex; an
  UNMAPPED section with items prints a build warning), uncategorized regular items (boss
  rewards, collectibles, Aghanim's Blessing, removed items) → "Other". `artifacts` is
  shown as **Armaments** (its in-game name). The ordered list ships in
  `_dynamics.json["item_categories"]`. ⚠ Refresh `data/shops.txt` per patch.

**Unified toolbar panel:** all dynamics controls live inside ONE bordered surface
`.toolbar-panel` (not separate floating pills). EVERYTHING inside goes FLAT —
switches, the Type/Category dropdown buttons AND the price control are all
transparent (no nested box), uniform 32px height, separated by thin dividers; only
the panel has a border (+ the search box on its own bottom row). The dropdown popovers
are portaled to `<body>` (`position:fixed`, `z-index:1000`). The same flat price pill
is reused on **mana_items** (`hd-price-range` + `.mr-price-label`).

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
  Now 91 not-current (3 removed enchants + ~10 removed items + ~80 cycled-out neutrals —
  see the neutral-pool note below; the live pool of 49 neutrals shows by default). EVERY
  one has an accurate removal patch now (see `_NEUTRAL_REMOVED_MANUAL`).
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
11. **Measure the frozen identity-column width ONCE over ALL rows, then cache it — never re-measure
    over a filtered subset.** The column-fit (`dynLayoutMatrix`) derives the patch-column count/width
    from `avail = boxWidth − heroW − gutter`, so `heroW` (the longest name + icon + gap) MUST be
    consistent with the fit. Measure it at setup BEFORE any default filter hides rows (items_dyn hides
    Neutral/Enchant/Deleted by default), cache on the table, and reuse on resize/load. If you re-measure
    after rows are hidden, hidden rows report `scrollWidth 0` → a SMALLER `heroW`; the fit gets computed
    from the small value while the real `--hd-hero-w` is the larger cached one → the table is wider than
    the box → a phantom **horizontal scrollbar** (this bit items_dyn but not heroes_dyn, which has no
    default filter). Names use the system font (no web-font reflow), so the setup measure needs no
    font-settle re-measure; `load`/`resize` should only re-FIT columns, not re-measure the name width.

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
| `data/stats/<patch>/heroes.json` | per-patch HERO stats (attributes, armor, dmg, BAT, MS, range, HP/mana base, magic res, regen) → Hero Stats cells + history. All 116 patches. |
| `data/stats/<patch>/heroes_raw.json` | per-patch HERO raw-only fields (vision day/night, projectile speed, base attack speed, turn rate, collision hull, bound radius) — NOT in heroes.json. Built by `scripts/fetch_hero_history.py` from dotabuff/d2vpkr's historical `npc_heroes.txt` (same commit-by-date matching as `fetch_npc_history.py`). Coverage 7.36→today (d2vpkr's window for this file). Run after a new patch lands to backfill. |
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
