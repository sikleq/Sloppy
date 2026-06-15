# Terrain page (`terrain.html`)

5th tab under **Materials**. Compares the Dota map **old → new** with a swipe
slider, plus that patch's *Terrain Changes* list. Built by `builders/terrain.py`
(standalone, like `builders/heroes_dyn.py`); CI runs it after `builders/patch.py`.

## Status (2026-06-04)

- ✅ **Swipe slider** — divider moves ONLY by dragging the handle (or arrow
  keys). Handle uses the pixel-arrow nav design.
- ✅ **Control bar** (`.tc-controls-bar`) now sits ABOVE the map (not overlaid —
  the map is edge-to-edge after the tight crop): **Zoom** mode button + **Trees**
  / **Camps** + 8 point-entity layer toggles. Version labels (7.40 bottom-left /
  7.41 top-right) stay as map-corner chips.
- ✅ **Loupe is a MODE** — the top-bar button toggles `.loupe-on`. Only then
  does hovering the MAP (not the handle / top-bar — those keep normal/resize
  cursor, no lens) show the gold magnifier following the cursor; **click pins**
  it, sweeping the handle compares that spot old↔new inside the circle. The
  cloned tree/camp markers ride along in the lens. `data-zoom=1.9` (pulled back),
  `data-lens=184`. Math: lens centred on cursor, inner layers scaled by zoom,
  seam = `--pos` reused (verified analytically).
- ✅ **Trees layer** — TWO same-colour layouts: the 7.40 forest clipped to the
  OLD side (`.tc-trees-old`, clip right) and the 7.41 forest clipped to the NEW
  side (`.tc-trees-new`, clip left), so sweeping the handle shows the forest
  move. One **Trees** button, `.show-trees`. (Data: `treesOld`+`treesNew`, full
  sets.) No add/remove colouring.
- ✅ **Camps layer** — tier icons (`icons/camps/`: small/mid/big/ancient, by
  `neutralType` 0–3 per leamare styleDefinitions), split old/new by the slider
  like trees (`.tc-camps-old` clip right = `camps40`, `.tc-camps-new` clip left
  = `camps41`) so you see what a camp became + where it moved. No "changed"
  ring. **Camps** button, `.show-camps`.
- ✅ **Top bar buttons** — Zoom / Trees / Camps are gold-chip toggle buttons
  (`.tc-btn`, `aria-pressed`); OFF = greyed + inset. Bar height == a version
  chip. **7.40** label sits in the bottom-left map corner, **7.41** top-right
  in the bar.
- ✅ **Counts** under the list (two lines): `Trees: 2456 in 7.40 → 2475 in 7.41
  (+19)` and `Neutral camps: 2 ancients, 6 large, 14 medium, 6 small`.
- ✅ Move objects (Lotus/Tormentor/Twin Gate) NOT marked — seen via lens+list.
- ✅ Correct **7.41** Terrain Changes list (was mistakenly the 7.40 rework list).
- ✅ **Map quality** — stitched from the spectral courier **tile server** at
  **1536²** (sharp under the lens), via `scripts/build_terrain_maps.py`.

## Maps — `scripts/build_terrain_maps.py`

Tile server (same render as <https://tools.spectral.gg/interactive-map>):
`https://courier.spectral.gg/images/dota/maps/tiles/<code>/<skin>/<z>/tile_<col>_<row>.jpg`
— `<code>` = patch w/o dot (`741`), `<skin>` = `default`, `<z>` = 0..4, tiles 256².

**Tile scheme (reverse-engineered, NOT plain 2^z):** the render has grey
placeholder padding (`rgb 56,57,49`) on top + a little left; the map is flush
bottom/right. Out-of-range requests return that grey tile with **HTTP 200**
(and truly-missing margin tiles 404) — so detect content by colour distance,
not status. At **zoom 2** the whole map fits a 24×24 grid (content ≈ 19×19
tiles ≈ 4864px). We stitch z2, crop to the shared **tight** content bbox (now
`(186,287)-(4783,5082)` ≈4597×4795 — `_content_bbox` strips the flat-grey
placeholder, so no fat grey borders; same box for 7.40 & 7.41 so the swipe stays
aligned), resize to **1536²** webp. Re-run: `python scripts/build_terrain_maps.py 7.40 7.41`.

## Data sources (primary)

- Interactive map: <https://tools.spectral.gg/interactive-map>
- Coords (GitHub): `leamare/dota-interactive-map`
  - `assets/data/<ver>/mapdata.json` — per-version entity coords (trees, neutral
    camps, towers, watchers, twin gates, lotus pools, tormentor/miniboss, …).
  - root `worlddata.json` — world bounds (`minX -10464 .. maxX 10400`, same Y).
- Diff: `scripts/build_terrain_diff.py` reads the two cached `mapdata.json`
  (under `.cache/leamare/`, not committed) → `data/terrain_diff.json` (committed).
- Projection: world `[-10464, 10400]` → `1280px`. Verified pixel-accurate by
  overlaying all 7.41 trees on the map render (they land exactly on the forest).
- The 7.40→7.41 diff: **+324 / −305 trees, camps moved/relocated + 2 demoted,
  2 towers, tormentor/twin-gate/lotus moves** — all match the 7.41 text list.

## Map source availability (investigated 2026-06-04)

- **Tiles** `maps/tiles/<ver>/default/<z>/…` — only the `default` skin (no
  `realistic`/`simple` tiles → 404). Versions available: list at
  `maps/tiles/` (688, 700, …, **740, 741**, …). This is the ONLY source with
  per-version maps → required for the 7.40↔7.41 swipe. **Use this.**
- **Flat minimap PNGs** `minimap/<ver>[_skin].png` (skins: `_realistic`,
  `_simple`, `_mapzones`) — pre-cropped & aligned, but list (`minimap/?list`)
  stops at `739b` then jumps to `current` (= latest = 7.41). **No `740`/`741`
  versioned PNGs** → can't build a matched 7.40↔7.41 pair from these. Only good
  for "latest map" single views. `current_realistic.png` is 1000², canonical
  crop — handy as an **alignment reference** (our tile crop matches it within
  ~2%; use it to pin the world→pixel projection when markers come back).
- For the **patch picker** (below): a version qualifies only if `maps/tiles/`
  has BOTH that patch and its predecessor (to diff/compare) AND it has terrain
  changes.

## Entity layers + tight crop (added 2026-06-04)

- **10 point-entity toggle layers** beyond Trees/Camps: towers, lotus pools, twin
  gates, tormentors, bounty runes, power runes, wisdom shrines, **outposts**,
  **watchers**, **roshan** (`_ENTITY_LAYERS` in builders/terrain.py). Data = full
  old+new coord sets in `terrain_diff.json["entities"]` (built by
  build_terrain_diff.py). **leamare keys (`layerDefinitions.js`):** `npc_dota_tower`,
  `npc_dota_lotus_pool`, `npc_dota_unit_twin_gate`, `npc_dota_miniboss_spawner`,
  `dota_item_rune_spawner_bounty` / `_powerup`, `npc_dota_xp_fountain`,
  **Outpost = `npc_dota_watch_tower` (2)**, **Watcher = `npc_dota_lantern` (10)**
  (SEPARATE layers!), `npc_dota_roshan_spawner` (2). Split old/new by the slider.
- **Map marker** (`marker_g`) = a **dark backing circle** (`#0d100b` @0.66, so the
  busy map doesn't show through and read as "muddy") + a faint type-colour tint
  (@0.34) + a light-gold ring + the icon on top. The icon is the LIGHTENED type
  colour so it pops on its own disc.
- **Icons** (`scripts/gen_terrain_layer_icons.py`) — GAME map icons from
  `icons/ref/` (`REFS`): towers.svg, roashan.svg, tormentor_png.png,
  watcher_lantern.png, Bounty_Rune_…png, and **lotus_pool/twin_gate/outpost
  cells cut from `minimap_sheet_psd_*.png`** (the 11×11 64px sheet — split into
  `icons/ref/sheet_cells/r{row}_c{col}.png` by hand-picked cell). SVGs rasterised
  via ImageMagick `magick`. Tinted to the type colour (`COLORS`, brightness from
  the ref's luminance) **except `NATURAL` icons (bounty + the power runes) which
  keep their real colours** — the dark marker backing gives contrast, so no
  lightening needed. **Wisdom** has no game icon → `wisdom_icon()` draws a dense
  bright-purple inner ring + inward glow (the shrine's capture glow). All 48px,
  canvas FILLED + UnsharpMask, shown SMOOTH (`image-rendering: auto`). Same PNG is
  the button AND the marker; `COLORS` ↔ `_ENTITY_LAYERS` colours stay in sync.
- **Power-rune cycling** — a power-rune spot can roll any of the 7 runes, so the
  Power layer is special: its 7 icons (`tc_rune_0..6.png`, downloaded from
  liquipedia into `icons/ref/runes/`, kept in their NATURAL colours + soft
  outline) cycle on the MAP every 3 s while the layer is ON (scripts.js
  `togglePowerCycle` / `setRune`, sets `<image>` `href`/`xlink:href`). The toolbar
  button shows a RANDOM rune on load. `tc_power.png` (button + initial marker
  default) = the regeneration rune. Markers still sit in the faint-green power
  disc. Order: amplify, arcane, haste, illusion, invisibility, regeneration, shield.
- **Controls ABOVE the map** (`.tc-controls-bar`) — icon-only toggle buttons with
  tooltips. Generic JS handler over `.tc-layer-btn[data-layer]` flips
  root `.show-<key>`.
- **Patch picker** lives in the change-list heading as the version
  (`[7.41 ▾] Terrain Changes`), not a toolbar.
- **Maps cropped tight** — `_content_bbox` now strips the flat-grey placeholder
  (per-row/col ≥10% real content), not "any non-grey pixel" (that left fat grey
  borders: L11 R54 T32 B13). Margins ≈0 now. The projection auto-follows via the
  updated `data/terrain_map_meta.json` crop box (re-verified: trees still land
  exactly on the forest).

## Patch picker + per-patch data (added 2026-06-04)

- **Picker** (`_picker_html`) — gold-skinned calendar year-picker in a
  `.cal-toggle-bar` toolbar, lists every patch with terrain changes (newest
  first). `scripts.js initTerrainPicker` toggles `.terrain-map-pane` +
  `.terrain-list-pane` by `data-patch`.
- **Change lists are PARSED from `content/` patch files** (`builders/terrain.py::_terrain_changes_by_patch`)
  → no drift. One `(text, TAG)` list per `plain_header("Terrain Changes")`
  section. `b(...)` rows → BUFF/NERF by direction honouring `l=True`.
- **Map pairs** — `_MAP_PAIRS` maps `patch → (old_ver, new_ver)` for every patch
  we hold matched old→new webp for. Today: `7.41`→(7.40,7.41) and
  `7.40`→(7.39,7.40). `_compare_html(old_ver, new_ver, markers_svg)` builds the
  swipe slider for any pair (map URLs derived from the versions).
- **Markers + layer toolbar are PER-PATCH** — each patch ships its own
  `data/terrain_diff_<ver>.json` (`scripts/build_terrain_diff.py <prev>:<new>`,
  generic keys `treesOld/New`, `campsOld/New`, `entities`). `save_terrain_html`
  builds `markers_by_patch` / `counts_by_patch` via `_load_diff(ver)` and renders
  each pane's overlays. The SHARED crop meta (`terrain_map_meta.json`) projects
  any patch's markers correctly — no per-patch projection. A pair WITHOUT a diff
  passes empty `markers_svg` → `_controls_html(layers=False)` (Zoom only, no dead
  toggles). **Add a new patch:** (1) `build_terrain_maps.py <prev> <new> …ALL…`
  (shared crop must stay put), (2) `build_terrain_diff.py <prev>:<new>`, (3) add a
  `_MAP_PAIRS` entry; `git add` the new `map_<ver>.webp` + `terrain_diff_<ver>.json`.
- **scripts.js inits ALL sliders** — `initTerrainCompare` does
  `querySelectorAll('.terrain-compare').forEach(initOneTerrainCompare)`; the
  default-hidden second pane (7.40) still gets a working handle/lens/toggles so the
  picker can reveal it. (Was a single `querySelector` → only the first pane worked.)
- **No-map fallback (`_fallback_html`)** — for a patch with changes but no map
  pair: the latest map blurred + dimmed with a centred "Map comparison for X
  isn't available yet" overlay; the textual change list still renders.
- **Deep-link from patch pages** — `plain_header("Terrain Changes",
  terrain_link="<base_ver>")` (`patch/elements.py`) renders a gold `.terrain-jump-btn`
  "View on map" link in the section header → `../terrain.html?patch=<base_ver>`.
  `initTerrainPicker` reads `?patch=` on load and preselects that pane via the
  existing picker. ONE shared page — no per-patch `terrain_<ver>.html`.
  ⚠ The parser regex is `plain_header\("Terrain Changes"` (no trailing `\)`) so
  the new `terrain_link=` arg doesn't make it miss every block.

## TODO / action items

1. ✅ **No-map fallback** — done (`_fallback_html`).
2. ✅ **Patch picker** — done; lists only patches with terrain changes, sourced
   from `content/` so it can't drift. Next: when a NEW patch gets a real
   old→new map pair, add it to `_MAP_PAIRS` + drop its maps in `icons/maps/`.
3. ✅ **Marker redesign — done.** Toggleable tree + camp layers, both split
   old/new by the slider; magnifier lens. **Projection is now EXACT** — uses the
   real leamare transform (`src/js/conversion.js worldToLatLon` + mapConstants
   `map_x_boundaries [-10829.42, 11487.75]`, `map_y_boundaries [11351.48,
   -10939.96]`, MAP_W 20480; zoom-2 tile = 1024 map-px → ÷4 canvas). The crop
   box + bounds are written to `data/terrain_map_meta.json` by
   build_terrain_maps.py and read by builders/terrain.py's `_projector`. (Earlier
   it wrongly used worlddata.json bounds → trees were misplaced.)
4. ✅ **Map source — done.** Stitched from spectral tiles
   (`scripts/build_terrain_maps.py`, zoom 2 → 1280²).
5. **Lens polish (optional):** show tree dots inside the lens too; clamp the
   lens at map edges; touch support (tap-to-pin).

## Gotchas

- **Right patch section.** The `content/` files have multiple `Terrain Changes`
  blocks (one per patch). Use the one under the matching `write_head("X.YZ")`.
  The 7.40 list (streams into bases, Wisdom Shrines to low ground, defender's
  gates, bridges) is the big rework and is NOT the 7.41 list.
- **Pixel alignment.** Both maps must be cropped identically; the swipe relies
  on them being pixel-aligned (verified: best-shift 0,0).
- Scratch/preview PNGs must not be committed — `icons/` is deployed wholesale.
