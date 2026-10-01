# Terrain page (`terrain.html`)

5th tab under **Materials**. Compares the Dota map **old → new** with a swipe
slider, plus that patch's *Terrain Changes* list. Built by `builders/terrain.py`
(standalone, like `builders/heroes_dyn.py`); CI runs it after `builders/build_patches.py`.

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
  **1536²** (sharp under the lens), via `scripts/gen/build_terrain_maps.py`.

## Maps — `scripts/gen/build_terrain_maps.py`

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
aligned), resize to **1536²** webp. Re-run: `python scripts/gen/build_terrain_maps.py 7.40 7.41`.

## Data sources (primary)

- Interactive map: <https://tools.spectral.gg/interactive-map>
- Coords (GitHub): `leamare/dota-interactive-map`
  - `assets/data/<ver>/mapdata.json` — per-version entity coords (trees, neutral
    camps, towers, watchers, twin gates, lotus pools, tormentor/miniboss, …).
  - root `worlddata.json` — world bounds (`minX -10464 .. maxX 10400`, same Y).
- Diff: `scripts/gen/build_terrain_diff.py` reads the two cached `mapdata.json`
  (under `.cache/leamare/`, not committed) → `data/terrain_diff.json` (committed).
- Projection: world `[-10464, 10400]` → `1280px`. Verified pixel-accurate by
  overlaying all 7.41 trees on the map render (they land exactly on the forest).
- The 7.40→7.41 diff: **+324 / −305 trees, camps moved/relocated + 2 demoted,
  2 towers, tormentor/twin-gate/lotus moves** — all match the 7.41 text list.

## Our own map data — from the game files (2026-09-30)

`scripts/gen/extract_map_entities.py` reads the map VPKs of the local game install with Source2Viewer-CLI
(path in env `S2V_CLI`; no game running, no downloads) → `data/map/mapdata_<code>.json` (committed), same
shape as leamare's `mapdata.json`. `build_terrain_diff.py` prefers these files and falls back to the
`.cache/leamare/` export only for maps we don't have yet.

- Source: the entity lumps `maps/dota/entities/*.vents_c` — `default_ents` + the `world_layer_*_base` layers,
  NOT `*_destruction`. Trees = `ent_dota_tree`; camps = `npc_dota_neutral_spawner` (`neutraltype`,
  `pulltype`, `volumename`); camp boxes = the `trigger_multiple` volume's hull bounds (`m_vMin/MaxBounds` in its
  `.vmdl_c`, or the sibling `.vphys_c` in legacy maps; several hulls → one box) + the entity origin/yaw;
  Roshan = the spawner + `info_player_start_dota` `roshan_location_2`; Tormentors = `miniboss_location_*`;
  shrines (7.00–7.22) = buildings with `mapunitname` `*_healers`. Coordinates rounded to whole units.
- Maps on disk: the live `dota.vpk` (= 7.41 terrain) + legacy snapshots the game keeps for old replays:
  `dota_683 / 685 / 688 / 706 / 719 / 722 / 728 / 732 / 737.vpk`.
- Checked against leamare (`tests/test_map_entities.py`, skips without the cache): trees, camps + types, boxes,
  towers, runes, Roshan, Tormentors, gates, lotus, watchers, outposts identical for 7.41, 7.35 (=737), 7.32,
  7.22, 7.19. Only differences: leamare's hand-added `landmarks` / `landmark_aura` (not in the map files) and one
  7.06 camp box (his is wider). Counts: 6.83 2669 trees · 6.85 2489 · 6.88 2371 · 7.06 2190 · 7.19 2205 ·
  7.22 2208 · 7.28 2104 · 7.32 2303 · 7.37 2531 · 7.41 2475.
- Missing so far: 7.38, 7.38b/c, 7.39*, 7.40* — the game install has no snapshot of them. Next: take
  `maps/dota.vpk` from old builds (DepotDownloader `-filelist`, Steam login by the owner) and pass it with
  `--vpk`. Rendering the top-down image ourselves: Source2Viewer glTF export → Blender orthographic (needs
  Source2Viewer 20.0 for Dota's terrain shaders).
- How leamare does it (for reference): a Lua custom game in Workshop Tools dumps entities to the console
  (`leamare/dota-map-coordinates`); the image is SFM camera sweeps stitched in Microsoft ICE and calibrated by
  hand (`dota-interactive-map/docs/05-mapimage.md`). The courier tile server DOES have some letter patches
  (738b, 739b).

## Our own top-down picture — shot in the game (2026-10-01)

`scripts/gen/capture_map.py` = leamare's SFM method without SFM's clicks: Dota 2 in Workshop Tools mode runs our
custom game `scripts/gen/topdown_addon` (installed with `--install`; no fog of war, no day/night, pre-game forever,
`topdown_hide` hides heroes / couriers / Roshan / Tormentors / creeps, `topdown_cam x y dist` = Panorama
`GameUI.SetCameraPitchMin/Max(90)` + `SetCameraTargetPosition`), driven over the remote console
(`scripts/gen/game_console.py`, VConsole2 TCP 29000; replies are read from `console.log` — launch with `-condebug`).
Launch: `dota2.exe -tools -novid -vconsole -condebug -windowed -w 1920 -h 1080 -addon sloppy_topdown
+dota_launch_custom_game sloppy_topdown dota`.

What it took (each one silently broke the shots):
- `r_always_render_all_windows 1` (Tools' "Render All Windows") — else the game window is not redrawn and every
  screenshot is the same old frame; `engine_no_focus_sleep 0`; `r_drawpanorama 0`, `dota_hud_healthbars 0`.
- `dota_camera_lerp_duration 0` + `dota_camera_smooth_count 1` — else the camera glides and a shot 1 s after a move
  is taken mid-flight (scale off by ~20%).
- Setup stages of the custom game ≥ 1 s each — all at 0 left the client on its loading screen.
- The game camera is wide-angle (~97°) and its field of view can't be changed (`default_fov`, `fov_desired`,
  stage cvars, `point_camera` + `GameUI.SetCameraEntity` — none work), so only the middle of each shot is kept:
  7680×4320 shots from 5000 up → 1.4925 units/px, 900-unit tiles, 23×24 = 552 shots, ~2 s each (~20 min).
  Higher up the game drops its detail level (15360 px from 13400: pixelated), so don't go higher.
- The camera's look-at point is clamped to the playable area (7.41: x ±8448, y -9472..8448, probed by
  `look_at_bounds`): edge tiles are shot from the nearest allowed point and cut off-centre.
- A camera move sent right after another is now and then lost: `Camera.goto` reads the look-at point back
  (`dota_camera_get_lookatpos` → console.log) and resends until the camera is there.
- One game session per capture: tiles of two sessions differed in scale by ~4% (same calibration, same spot).
  Resuming into a tiles folder from another session mixes them — start a fresh folder after a restart.
- Nothing moves (2026-10-01, the owner: "outposts visible, ambient like butterflies, moving water — or stop
  time"): `topdown_hide` removes the outposts (`npc_dota_watch_tower`, their ring with them; the round white
  platforms left are the wisdom shrines — map objects); SETUP turns off critters (`dota_ambient_creatures 0`),
  tree shake and cloth, **wind in the foliage** (`r_dota_allow_wind_on_trees 0`), **drifting cloud shadows**
  (`r_dota_clouds 0`) and freezes particles (`r_freezeparticles 1`). Two shots of one spot 3 s apart then differ in
  0.03% of the pixels (one pond's ripples). Pausing the game (`PauseGame`) was tried: it stops neither the foliage
  nor the water, and a paused server runs console commands 10-20 s late — the camera stayed put for whole shots.
  Never leave `host_timescale` below 1: the server then runs a command every ~20 s.
- The player's own `autoexec.cfg` / video settings apply (FSR upscaling here): turning FSR off made the ground
  blurrier, not sharper; at the site's 4096 px its blockiness doesn't show. `sc_force_lod_level 0` changes nothing.
- Colours (the owner 2026-10-01: "our map is too bright, it should look like leamare's"): the game's picture is
  warmer and more saturated (lime grass, orange sand, light tree shadows). A colour grade on top was tried (a
  pixel-against-pixel fit washed the picture out; a histogram transfer dirtied the ground and kept the orange camp
  glows) and removed 2026-10-01 — the Source Filmmaker route below replaced this capture.
- Output: `<work>/map_<ver>_game_full.png` (13399×13970 for 7.41, the game's own colours) + `map_<ver>_game.webp`
  4096² on the same world rectangle as our map images (data/terrain_map_meta.json) — checked: buildings
  land where the current picture has them.
- Blender route (`scripts/gen/render_map.py`: glTF export + our multiblend rebuild) stays as a fallback: exact
  geometry, but not the game's own look.

## Our own top-down picture — rendered in Source Filmmaker (2026-10-01) — the way to go

The in-game capture above never looked like leamare's pictures (the owner: "too bright", "orange spots", "dirty
ground"): the game camera adds its post-processing, low-detail models from 5000 up, the player's FSR upscaling, and
the camps' orange glows — 12 game settings (lights, particles, overlays, decals, bloom, tone map, time of day) don't
remove them, and colour grading on top only traded one fault for another. Source Filmmaker (Workshop Tools →
Tools → Source Filmmaker, `tools/sfm.dll`) renders leamare's look:

- The session (`*.dmx`, kept outside the repo — SFM sessions live in `game/dota_addons/<addon>/elements/sessions`;
  `game/bin/win64/dmxconvert.exe -i in.dmx -o out.dmx -oe keyvalues2` makes it text, `-oe binary` back):
  camera `fieldOfView 1`, at z 240000 (`znear 200000`, `zfar 300000`), orientation quaternion
  `-0.49645 0.50352 0.50352 0.49645` (straight down but 0.81° off: the view centre lands 3395 units west of the
  camera), position keyed once a second in a serpentine — x -6000…12000 step 3600, y -9793…10207 step 2000 = 6 × 11
  frames, 66 s at `frameRate 1`; render settings `modelLod 0`, `SkipMainPipelinePostProcessing 1`,
  `ambientOcclusionMode 1`, progressive refinement on; movie: image sequence, PNG, 3840×2160, 0–66 s. Frames are
  ~4190 × 2360 units at 1.09 units/px with ~15% overlap; they cover x -11489…10699, y -10971…11385 — our picture
  rectangle with room to spare (7.33's camera path fits 7.41 unchanged).
- Steps: launch `dota2.exe -tools -addon dotamapsfm`, Tools → Source Filmmaker, open the session, File → Export →
  Movie (Ctrl+M) into a frames folder (~2 min for 66 frames), then
  `python scripts/gen/stitch_sfm.py SESSION.dmx FRAMES 7.41 --work D:\maprender`.
- `stitch_sfm.py` reads the camera path from the session (position log, the channels clip's time offset, the
  movie's frame rate and range) and places every frame by geometry — the lens is narrow enough to be
  near-orthographic, so no feature matching (the guide this follows used Microsoft ICE). Units per pixel are measured
  on neighbouring frames (1.0902 against 1.0904 from the lens). Frames meet in cells around their centres,
  cross-faded over 64 px either side of a border: a hard cut showed as a line across water, whose glints depend on
  where the water is in a frame. Frame brightness otherwise matches (overlap means within 0.1%).
- Output: `map_<ver>_sfm_full.png` (9999×10425 at 2 units/px) + `map_<ver>_sfm.webp` 4096². The corners beyond
  the map's edge render black (nothing there; the outermost ~12 px are SFM's flat grey background). `fill_void`
  paints them in our own way: plain ground continues past the edge (the owner: "fill the black corners, in our own
  way", "the bottom-left is all murky", then "trees in the corners? remove them if they aren't really there").
  A pool of up to 400 clean 128-px patches of the void's own ground is collected from the whole map (searched at
  1/4 size): the colour to match is the most common plain ground near the void (grass by Radiant, grey ground by
  Dire — not the land right along it: cliffs, lava); a patch qualifies with nothing darker than that ground in it
  (no bush, tree or shadow), colour within 12 of it, little colour spread (no paving), little detail. The pool is
  quilted into the void (Efros & Freeman: 32-px overlaps, best of 80 random patches, minimum-error seams), then
  everything wider than ~60 px is evened out to the ground's colour (rows of patches showed as stripes); 80%
  brightness, a soft shadow under the map's edge. Tried before: mirroring the edge (duplicated cliffs), a blurred
  fade (murky), six big source windows (on Radiant's lawns every big window has bushes or paving: bushes and paving
  got copied, then the few clean patches ran out).
- Map size changes (the owner 2026-10-01: "what if a patch's map was a different size?"): trees and buildings
  reach ±7680 units until 7.32 (6.83-7.32 legacy maps), ±8768 from 7.33 (7.37-7.39e), slightly more from 7.40
  (x to 8960, y to -9088); the ancients never moved. Every picture uses one world rectangle and scale (2 units/px),
  so a smaller map is drawn smaller, at its true size, and the slider and the object layers stay aligned.
  `stitch_sfm.check_fits` stops a render whose frames don't cover the rectangle or whose objects (`--mapdata`)
  come closer than 300 units to its edge — then the camera path and data/terrain_map_meta.json must grow.
- Provenance: `data/map/renders.json` lists the versions whose picture is ours; the Terrain page's credit line
  ("Inspired by Leamare and devilesk", linked to their repositories, kept to the minimum — the owner
  2026-10-01) names a version whose map is still borrowed (a picture not in renders.json, map objects without
  `data/map/mapdata_<code>.json`), so it never claims more than is true. Tests: tests/test_terrain_credit.py.
- 7.41 on the site since 2026-10-01 (`icons/maps/map_7.41.webp`): registered on the old picture's grid within
  ±1 px at 4096 (phase correlation at five spots), so the 7.40 ↔ 7.41 slider still lines up.
- Clicking SFM: no command opens SFM or a session, and SFM in Dota has no Python (the script window has no
  interpreter behind it), so it is driven through its menus.

## Map source availability (investigated 2026-06-04)

- **Tiles** `maps/tiles/<ver>/default/<z>/…` — only the `default` skin (no
  `realistic`/`simple` tiles → 404). Versions available: list at
  `maps/tiles/` (688, 700, …, **740, 741**, …). This is the ONLY source with
  per-version maps → required for the 7.40↔7.41 swipe. **Use this.**
- **Flat minimap PNGs** `minimap/<ver>[_skin].png` (skins: `_realistic`,
  `_simple`, `_mapzones`) — pre-cropped & aligned, but list (`minimap/?list`)
  stops at `739b` then jumps to `current` (an alias for whatever the upstream considers latest, not a fixed patch). **No `740`/`741`
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
- **Icons** (`scripts/gen/gen_terrain_layer_icons.py`) — GAME map icons from
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
  `data/terrain_diff_<ver>.json` (`scripts/gen/build_terrain_diff.py <prev>:<new>`,
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
   (`scripts/gen/build_terrain_maps.py`, zoom 2 → 1280²).
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
