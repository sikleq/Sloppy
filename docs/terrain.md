# Terrain page (`terrain.html`)

5th tab under **Materials**. Compares the Dota map **old → new** with a swipe
slider, plus that patch's *Terrain Changes* list. Built by `build_terrain.py`
(standalone, like `build_heroes_dyn.py`); CI runs it after `build_patch.py`.

## Status (2026-06-04)

- ✅ **Swipe slider** — divider moves ONLY by dragging the handle (or arrow
  keys). Handle uses the pixel-arrow nav design.
- ✅ **Top control bar** (`.tc-topbar`) overlaid on the map's non-playable top
  edge: version labels (7.40 left / 7.41 right) + **Trees** / **Camps** layer
  checkboxes + **Loupe** mode button.
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
tiles ≈ 4864px). We stitch z2, crop to the shared content bbox
`(152,183)-(4943,5120)` (≈4791×4937, same for 7.40 & 7.41 so the swipe stays
aligned), resize to **1280²** webp. Re-run: `python scripts/build_terrain_maps.py 7.40 7.41`.

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

## TODO / action items

1. **No-map fallback.** When a patch *has* terrain changes but we don't have a
   map yet: show the previous patch's map **blurred** with a centered English
   overlay (e.g. "Map changes for X.YZ are not available yet"), but STILL render
   the textual terrain-change list. So the page is useful before the art lands.
2. **Patch picker.** A dropdown to choose the patch — but list **only patches
   that have terrain changes**. Implies per-patch terrain data: each entry needs
   its own change-list + (old,new) maps + diff. Today the list is a single
   hardcoded `_TERRAIN_CHANGES`; generalize to per-patch (ideally sourced from
   the build_patch.py terrain section so it can't drift).
3. ✅ **Marker redesign — done.** Toggleable tree + camp layers, both split
   old/new by the slider; magnifier lens. **Projection is now EXACT** — uses the
   real leamare transform (`src/js/conversion.js worldToLatLon` + mapConstants
   `map_x_boundaries [-10829.42, 11487.75]`, `map_y_boundaries [11351.48,
   -10939.96]`, MAP_W 20480; zoom-2 tile = 1024 map-px → ÷4 canvas). The crop
   box + bounds are written to `data/terrain_map_meta.json` by
   build_terrain_maps.py and read by build_terrain.py's `_projector`. (Earlier
   it wrongly used worlddata.json bounds → trees were misplaced.)
4. ✅ **Map source — done.** Stitched from spectral tiles
   (`scripts/build_terrain_maps.py`, zoom 2 → 1280²).
5. **Lens polish (optional):** show tree dots inside the lens too; clamp the
   lens at map edges; touch support (tap-to-pin).

## Gotchas

- **Right patch section.** `build_patch.py` has multiple `Terrain Changes`
  blocks (one per patch). Use the one under the matching `write_head("X.YZ")`.
  The 7.40 list (streams into bases, Wisdom Shrines to low ground, defender's
  gates, bridges) is the big rework and is NOT the 7.41 list.
- **Pixel alignment.** Both maps must be cropped identically; the swipe relies
  on them being pixel-aligned (verified: best-shift 0,0).
- Scratch/preview PNGs must not be committed — `icons/` is deployed wholesale.
