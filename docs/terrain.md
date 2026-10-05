# Terrain pages (`terrain_<code>.html`)

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
  OLD side (`.tc-trees-old`, left of the handle since 2026-10-03) and the 7.41 forest clipped to the NEW
  side (`.tc-trees-new`, right of it), so sweeping the handle shows the forest
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
  (under `.cache/leamare/`, not committed) → `data/terrain_diff_<patch>.json` (committed, one per patch).
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
  got copied, then the few clean patches ran out). The owner rejected that too ("terrible"), so since 2026-10-02
  the site's pictures use `--void-black`: the corners stay as the game draws them (near-black, nothing lit out
  there) and only SFM's grey rim is painted black. Why they're dark: the game lights nothing beyond the playable
  edge — on the current engine and on the 7.40c engine alike, for 7.38-7.41f maps alike; none of mat_fullbright,
  sc_disable_baked_lighting, r_indirectlighting, r_dota_shadow_ambient_light, r_deferred_height_fog,
  dota_height_fog_scale, r_dota_height_fog_plane_height changes a pixel (SFM, 2026-10-01). Leamare's pictures
  show lit ground there from an older pipeline.
- Older maps on the current engine: the water of 7.38-7.40c maps renders as maroon triangles (7.41 reworked the
  water shader; ~20 000 px per 4096 picture, none on 7.41+). Swapping in only the old shaders gives black frames.
  So 7.38-7.40c are rendered on a copy of the whole game as it was on 2026-03-16 (the 7.40c build): the install
  robocopied to another drive, then every depot brought to that day's manifest with DepotDownloader `-validate`
  (only ~4.5 GB differed); manifests per depot from their histories. SFM runs from that copy (its dota2.exe needs
  the owner to answer a Windows Firewall prompt once). The rendering scripts take the game folder from DOTA_GAME.
- Check the first exported frame: now and then (3 of 26 exports) SFM writes frame 0 before the camera reaches its
  first key — a patch of Radiant jungle instead of the empty bottom-left corner (mean brightness ~102 against
  ~25). That frame is the empty corner, so a sound frame 0 of the same map from another export replaces it.
- Edge strip (2026-10-02, the owner: "a white strip at the left edge when zoomed in"): where the outer frames stop
  5-6 px short of the picture's edge, SFM's flat grey (55) stayed — too thin for `_void_mask`'s opening and its
  flatness test. Neutral grey within `BORDER_PX` (16) of the edge is now always void; every picture, its webp,
  zoom tiles and release asset were redone (`sfm/reblack_edges.py`).
- Pink objects = a material the build we render on lacks. 7.39's release map file holds two "templar gates"
  (`npc_dota_unit_templar_gate`, the Twin Gate model `team_portal.vmdl` with skin 2, at (1875, -5075) and
  (-1527, 4000)) that no patch note mentions and 7.39b removed; the 7.40c build has no material for that skin. The
  owner (2026-10-02, "shouldn't this pink object be gone in 7.39?") — they're mended out:
  `scripts/gen/mend_map.py BAD_full.png DONOR_full.png OUT NAME --at=x,y …` takes the pink object (+ its rim and
  shadow, ≤6 px) from a donor render with the same ground there (7.39b: nothing moved within 900 units), not the
  ground around it — 7.39b painted grass where the portal stood, 7.39 keeps its sand. The unmended render is kept
  as `map_<sha8>_sfm_full_pink.png`; the work script `stitch_final.py` (`MEND`) re-applies it. Tests:
  tests/test_mend_map.py.
- Map history: `scripts/gen/map_history.py` — which dota.vpk each patch shipped (SHA-1 from depot 373301's
  manifests, one Steam login per manifest, with pauses: Steam rate-limits logins) and one download per distinct
  file. 7.38-7.41f: 16 map files; 7.08-7.37: 49. Their pictures, objects and counts go to
  [Oldgrowth](https://github.com/sikleq/Oldgrowth).
- Map size changes (the owner 2026-10-01: "what if a patch's map was a different size?"): trees and buildings
  reach ±7680 units until 7.32 (6.83-7.32 legacy maps), ±8768 from 7.33 (7.37-7.39e), slightly more from 7.40
  (x to 8960, y to -9088); the ancients never moved. Every picture uses one world rectangle and scale (2 units/px),
  so a smaller map is drawn smaller, at its true size, and the slider and the object layers stay aligned.
  `stitch_sfm.check_fits` stops a render whose frames don't cover the rectangle or whose objects (`--mapdata`)
  come closer than 300 units to its edge — then the camera path and data/terrain_map_meta.json must grow.
- Provenance: `data/map/renders.json` lists the versions whose picture is ours (all of them). No credit line
  under the slider: it read "Inspired by Leamare and devilesk" from 2026-10-01 until the owner asked to remove it
  on 2026-10-03 — every picture and object list is ours, and the Oldgrowth README credits them. Test:
  tests/test_terrain_credit.py.
- Since 2026-10-02 every map file 7.38-7.41f is on the site (`icons/maps/map_<first patch>.webp`, the Oldgrowth
  pictures) and every patch whose file changed has its own Terrain page ("One page per patch" below).
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
  old+new coord sets in `terrain_diff_<patch>.json["entities"]` (built by
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

- **Picker** (`_picker_html`) — the version menu in the header nav (`.nav-context-terrain`): one link per Terrain
  page, newest first; the subpatch arrows (`initSubpatchPicker`) step to the neighbouring links.
- **Change lists are PARSED from `content/` patch files** (`builders/terrain.py::_terrain_notes_by_patch`)
  → no drift. One `(text, TAG)` list per `plain_header("Terrain Changes")`
  section. `b(...)` rows → BUFF/NERF by direction honouring `l=True`.
- **One page per patch (2026-10-02)** — the owner: "the difference between the letter patches has to be shown too,
  not just two major versions" (7.39b's own changes used to sit under a 7.39 → 7.40 slider). `builders/map_versions.py`
  reads `data/map/patch_maps.json` (which map file every patch shipped — `map_history.py`'s `patch_maps.json`) and
  `data/map/renders.json` (the files we hold a picture of). A **step** = a patch whose map file differs from the
  patch before's, both files pictured → a page `terrain_<code>.html` (unless quiet, below). The OLD side is labelled with
  the patch right before and shows the picture of the file that patch ran — 7.40b shipped 7.40's file, so the 7.40c
  page compared `map_7.40.webp`. A patch with terrain notes but no step still gets a page, with the fallback.
- **Fullscreen zoom tiles (2026-10-02)** — the owner: "is this quality normal when zoomed?" (fullscreen zoom goes to
  8× the screen width, the 4096 picture blurred). `scripts/gen/map_tiles.py FULL.png OUT` squeezes the full render
  into an 8192 square (the 4096 picture's own geometry, ×2) and cuts 16 × 16 webp tiles of 512 px (~10 MB a map).
  They live in Oldgrowth `tiles/<ver>/<row>_<col>.webp`, served by its GitHub Pages
  (`https://sikleq.github.io/Oldgrowth/`, `.nojekyll`) — the owner chose that over growing Sloppy by ~190 MB.
  `data/map/renders.json` "tiles" lists the pictures that have them → `_compare_html` writes
  `data-tiles-old/-new`; scripts.js `updateTiles` (fullscreen only, after zoom/pan) lays the tiles in view over each
  picture — the old ones next to `.tc-old`, the new ones inside the clipped `.tc-new-layer` — once a picture pixel
  would be drawn bigger than a screen pixel. Pages' 1 GB limit: tiles for the site's maps only.
- **Terrain notes with micro-screenshots (2026-10-03)** — the owner: the terrain rows were "all under one tag, mush —
  maybe micro-screenshots, tree positions, now that we know which tree went where". `data/terrain_spots.json` places
  each note that can be seen on the map: `{"match": <the row's text start>, "spots": [[x, y], …], "r": half size}`
  (a moved object → the midpoint of its old and new spot; a mirrored change → one spot per side). Coordinates come
  from the diff (scratchpad `changes_xy.py`-style listing: tree clusters, moved objects, changed boxes, each by its
  nearest landmark — `terrain_audit.landmarks`). `scripts/gen/terrain_shots.py` crops the same square from the old
  and the new full SFM render (2 units/px → 240 px a side), outlines what changed inside (removed red / added green
  / moved yellow — the chips' `_changed_points`; squares round trees and camps, circles round entities; changed spawn
  boxes red / green), labels the halves with their versions and writes `icons/terrain/<code>_<i>.webp` (i = spot
  order in the file; ~35 KB each) plus a large copy `<code>_<i>_lg.webp` (600-px halves, ~140 KB). Only the
  note's own objects are outlined (the owner 2026-10-03: "a camps note shows only the camps, not the trees and
  everything else"): `terrain_shots.show_keys` takes the note's FIRST object word (camp / spawn box → camps +
  re-tiered + boxes, tree / juke path, watcher, tower / tier N, lotus, twin gates, tormentor, bounty rune, Roshan
  pit, wisdom shrine, outpost); a ground word first (cliff, ramp, stream, path, entrance, areas) → no outlines;
  a spot's `"show": [...]` overrides (3 do: the triangle's cliff + camps, a path cut through trees, the cleared
  Tormentor areas). `patch/elements.py terrain_note` puts them under a matching row — `li()` does it for patch
  pages, `_change_li` for the Terrain page's own list — opened by the row's words naming its object (see "the
  objective's name opens the pictures" below); the pictures open below in their own rounded box, centred, framed like the
  item ability cards (`hidden`, so the lazy pictures load only when opened), and a click on a picture opens its
  large copy (`data-large`) in a lightbox, not the Terrain page ("View on map" in the section header is for that).
  scripts.js "Terrain note pictures".
  More on the pictures (the owner 2026-10-03, "show these on the map too, check the other patches"): a spot's
  `"mark": [[x, y], …]` outlines, white, the camp nearest each point on EACH map picture (`mapdata_<code>.json`
  spawners — a camp may stand elsewhere on the old map) for notes about an unchanged camp (7.39 pull timers, 7.41
  evolutions); `"tiers": {"old": [...], "new": [...]}` puts the game's minimap camp icons (`icons/camps/
  creepcamp_<small|mid|big|ancient>.png`, 32 / 64 px unblurred) as a chain "mid → big → ancient" on a plate in the
  top-right corner of each half (bottom-right when a marked camp sits high) — demotions and evolutions; `"show":
  ["nowards"]` outlines the changed no-ward cells (turned wardable red on the old side, turned no-ward green on the
  new) for ground notes (7.39 cliff, 7.39d ward spot, 7.41 ramp). New spots are appended to a patch's list so the
  older pictures keep their numbers. Not shown (no place on the map or no data): rules (stream speed, watcher
  vision, gate mana), "Touched up the map" / "additional adjustments to this area", fixes the files don't record
  (7.39b warding blocks, 7.38c vision rules).
- **Terrain rows: numbered, the objective's name opens the pictures (2026-10-03)** — the owner went numbers →
  "Show" in the tag's place → back: "no Show buttons inside the tags: the expandable screenshot sits in the name of
  the objective that moved — 'tier 1 safe lane towers', 'several trees', 'medium flooded camp', 'safe lane small
  camp', 'Tormentor spawns'; the rows are just numbered instead of tag chips". The chip is the row's number in its
  category (`terrain_num_chip`, `.badge.tnum`): `li()` inside a `plain_header(terrain_link=…)` block
  (`_State.terrain_rows` not None) counts, `subgroup()` restarts at 1; `_changes_html` numbers the Terrain page's
  list the same way, so a row has the same number on both pages. The words come from `patch/terrain_notes.py
  note_phrase` (the subject word `show_keys` finds, plus the words describing it — left up to an article, a side
  (Radiant / Dire), a verb, a preposition or an adverb, right up to one or a participle) or a spot's `"phrase"`
  (3 do: "top and bottom outer rim areas", "top Radiant Tier 2", "actual bridges"); `wrap_phrase` makes the first
  plain-text occurrence `<button class="tshots-btn">` — dotted underline, a caret that flips when open; the build
  warns when markup splits it. Outside a terrain block the row keeps its tag and the words still open the pictures.
  Both lists keep Valve's order; terrain rows carry `class="terrain-row"` and `_sort_changes_li` leaves them in
  order. The tag canon still decides each row's `data-tag` (filters, weights).
- **The list's patch label opens that patch (2026-10-03)** — the owner: "make the patch switcher clickable, it
  jumps to that patch (the back arrow appears there)". scripts.js `initSubpatchPicker` makes `.tsp-label` an `<a>`
  to `patches/<ver>.html?from=terrain_<code>#terrain` (re-pointed when the arrows step); `plain_header` puts
  `id="terrain"` on the page's FIRST terrain block's View on map button (`_State.terrain_anchor`, reset by
  `write_head`); `?from=terrain_<code>` shows the patch page's bottom-left back arrow, pointed at that map. Dotted
  underline like the notes' picture buttons. The "On the map" tiles pop out on hover (`.tf-tile:hover`, scale
  1.12, a soft gold glow, the dynamics cells' z-index trick) — the owner: "softly, like our dynamics cells".
- **Changelog animations** — `tools/changelog_terrain_anim.py [layer]` records the trees in every mode on four
  patches (the other layers moved to the slider sweeps, `tools/changelog_terrain_sweep.py`: no two news show the same
  layer); needs dist/ on :8799.
- **Terrain Stats (2026-10-04)** — the owner: "add the Oldgrowth table somewhere, carefully, not breaking the Terrain
  page visually or technically — a sub-tab of the Terrain button, Terrain Stats, with more info". Materials ▸ Terrain is
  now a group (`MATERIALS_GROUPS` "terrain_grp": Terrain, Terrain Stats). `builders/terrain_stats.py` →
  dist/terrain_stats.html (build step "tstats"), left-aligned like every Materials page (no intro), the headings 10 px
  in: tiles centred (patches, "65 map files" linking to the Oldgrowth repo with a dotted label, trees and camps since
  7.08); an inline-SVG step chart of the trees on a faint grid (a line per 100 trees and per year, faint axes), each
  point's version and tree count on hover ("7.38 · 2496", CSS `.ts-pt:hover .ts-tip`), no labels on the chart (the
  owner: "remove 7.20, 7.23…"), a version without a letter drawn as a bolder point (`.ts-dot-major`), a faint red
  least-squares trend line through all the files (`.ts-trend`); and the table, newest first, full width (a clicked
  row framed in gold like the other table pages, `.ts-row-selected`, scripts.js "TERRAIN STATS") — map files
  with nothing different from the one before glued into its row (`group`: 65 files → 33 rows), the "Map version" a
  range ("7.35 – 7.37e", the owner: "easier than listing them"), the date as dd-mm-yy, no icon on Map version / Date,
  17 kinds of object (trees, camps and each tier, towers, outposts, watchers, lotus pools,
  wisdom, Twin Gates, bounty / power runes, shrines — `tc_shrines`: a 24-px pixel drawing
  of the Radiant shrine's game model (radiant_statue001: a stone basin of water on a rock, ivy round it;
  `SHRINE_GLYPH` in gen_terrain_layer_icons.py, scaled 2x). Two tries before it were turned down, 2026-10-04/05: a
  drawn stone well ("nothing like the game, not the others' style") and the game's minimap icon of the shrines,
  `minimap_miscbuilding`, tinted green ("looks awful, like a barrel of toxic waste — look at the model") —,
  Roshan pits, Tormentors), each cell its count plus what changed since the file before: the RESULT of what was added
  and removed ("+20" green / "−9" red / "±0" — the owner: "not +734 −548, write the result, +186"; the Terrain page's
  "Changed in the map file" chips likewise, `_chip`), moved / changed yellow (no "what moved" sentence column; the owner: "show moved like removed / added, in yellow";
  no Spawn boxes column — "nearly always empty"),
  and a 28-px square of the map (`icons/maps/thumbs/<sha8>.webp`, scripts/gen/map_thumbs.py) linking to its Oldgrowth
  picture. Data: `data/map/map_history.json` (counts + `moves` parsed from the "what moved" text) from Oldgrowth's
  versions.json (`scripts/gen/map_history_table.py`, rerun when Oldgrowth gains a patch) — the CI build can't reach the
  Oldgrowth folder. Local folders these scripts read are env vars with home-relative defaults (no personal paths in
  the repo, 2026-10-04): `OLDGROWTH_DIR` (~/Documents/Oldgrowth), `SFM_FINAL` (~/tools/maprender/sfm/final),
  `DEPOTDOWNLOADER` (~/tools/depotdownloader/DepotDownloader.exe), `SLOPPY_FETCH_STATS` (fetch_stats.py outside the repo). Styles all under `.terrain-stats-page` / `.ts-*`; terrain.py's stale-page sweep is
  `terrain_[0-9]*.html`, so it never deletes terrain_stats.html.
- **Bigger pictures with a minimap (2026-10-03)** — the owner: "when you show where something is, add a minimap
  with a mark, otherwise it's unclear; the pictures should be bigger and the camera a bit further out". The row
  picture is 726 x 360 (360-px halves, shown 480 x 238 css), the large copy 1450 x 720; every spot's square is
  `ZOOM_OUT` = 1.4 times its `r`; the old half's bottom-left corner holds the whole map (`MINIMAP` = 0.32 of a
  half, from the same full render) with the pictured square framed yellow. ~65 KB / ~190 KB a picture.
- **Where a moved object stood: a dashed ghost (2026-10-03)** — the owner, on a camp moved a little ("why the yellow
  squares?"): "on the new map show with a light dashed line where the object was before". The new side draws, at
  each moved object's OLD spot, the same shape dashed and faint: on the Terrain page `_dashed_outlines(…, ghost=True)`
  (inside `g.tm-hl-g-moved`, so the "moved" switch hides it), in the pictures `terrain_shots._dashed`. Yellow solid = where
  it stands on that side; on the new side the dashed one shows where it came from. Spawn boxes too ("a camp that
  moves moves its spawn boxes — it doesn't show they moved"): the pictures draw the old box red dashed over the new
  green one on the new side (`_boxes`; the Terrain page's spawn box layer already overlays old dashed on new). The
  dashes go on top of the solid outlines, so a shift of a few pixels still shows. **Dashed = old, everywhere** (the
  owner, same day: "on the old versions let everything be dashed — then, looking at the new map layer, dashed clearly
  means old"): the old side's outlines — removed red, moved yellow where it stood, the old spawn boxes — are dashed
  too, solid lines are only ever the new state. Pictures: `_outlines` / `_boxes` call `_dashed` / `_dashed_poly` on
  the old side. Terrain page: `_dashed_outlines` strokes the outline with thin, close dashes along its edges —
  squares merged into their union's outer edge (`_union_edges`: each square's edges minus what other squares cover,
  collinear pieces joined), so a grove is one dashed contour like the solid one; discs stay circles. Width 0.85 ×
  the solid stroke, dash 1.25 ×, gap 0.9 × (trees: 1.36 / 2.0 / 1.44 viewBox units). First try (10-03) masked the
  merged contour with 45° stripes — the owner 10-04: "too thick a dashed line with few gaps; take the outline we
  already draw round a tree and just make it dashed". **Trees since 2026-10-04: the square itself** — the owner,
  next to the red dashed contour round a grove and the row pictures' coloured squares: "not an outline round the
  square — outline the square itself in the colour of its change, only dashed". `_square_outlines` (trees only,
  `_HL_PER_SQUARE`): each changed tree's own 6.4 square (`_HL_SHAPE["trees"]` = the tree layer's half side) gets its
  border in the change colour — dashed on the old side over a 35%-opacity solid of the same colour (so the tree's
  green border does not show in the gaps), solid on the new side, a faint dashed square where a moved tree stood.
  No union, no mask; camps, towers and the rest keep their ring. 2026-10-05 ("too thick, dashed or not — 2–2.5 times
  thinner, on the outer edge"): the tree line is 0.7 (dashed 0.59, dash 0.88 / gap 0.63), drawn just OUTSIDE the
  square (rect half = 3.2 + line / 2), so the tree square itself stays whole. No-ward cells stay filled, they are areas, not outlines. **A picture from another patch (2026-10-03)** — the owner asked for pictures of 7.41's "Radiant offlane
  tier 2 tower has been adjusted slightly to the left", which the map file did in 7.40 (37 units west), not 7.41: a
  spot `[x, y, "7.40"]` pictures that patch's two maps (`spot_patch`; its own changes outlined, the entry's marks
  and tier icons left out), so the note shows 7.40c → 7.41 with the tower marked white (`"mark_kind": "towers"`,
  `MARK_KINDS`) and 7.39e → 7.40 with the move. Not placed: notes the map can't show (watcher rules, camp evolutions, pull timers, fixes) and the doubled 7.38c
  "Several additional tree and visual adjustments". With the shots, the terrain tag canon (docs/agent-rules/
  patch-tags.md): moved / reshaped REWORK, added NEW, removed DEL, demoted NERF, fixes MISC.
- **Slider performance (2026-10-03)** — the owner: "check Terrain for lag and needless loading — weak PCs". A
  Playwright probe (drag the handle across and back, CDP Performance metrics, 4× CPU throttle) found a drag spent
  13 s in style recalc, p95 frame 167-183 ms, layers on or off: `apply()` set `--pos` on `.tc-stage`, and a custom
  property inherits — every move re-styled all ~6500 marker shapes under the stage, hidden layers too. Now
  `apply()` writes `clip-path` straight onto the split elements (`.tc-new-layer, .tm-new, .tc-trees-new,
  .tc-camps-new, .tc-lens-new` → `inset(0 0 0 X%)`; `.tm-old, .tc-trees-old, .tc-camps-old` → `inset(0 (100-X)% 0
  0)`) and the handle's `left`; the CSS `var(--pos)` rules stay as the no-JS default. After: p95 16.7 ms (60 fps)
  with every layer on, recalc 0.3 s per drag. Don't set an inherited custom property on the stage per frame again.
- **Small pictures first (2026-10-03)** — same request. A page fetched both 4096 pictures (~8.3 MB) and the lens
  pointed at them too, though the map is drawn ~720 px wide. `scripts/gen/map_small.py` writes a 2048-px copy of
  every picture (`icons/maps/map_<ver>_2k.webp`, q82, ~0.87 MB; rerun it after adding a map picture). The base
  images open on the copy (`src` = `data-small`, the 4096 file in `data-full`; `_picture_attrs` falls back to the
  full file when no copy exists); the lens images carry no `src` until the lens is first switched on. `fitSrc` swaps
  an image to `data-full` once its drawn width × devicePixelRatio passes 2048 × 1.05 (a big retina screen, the lens
  at ZOOM 1.9 on a 2× screen, fullscreen zoom via `updateTiles`) and never swaps back. Probe
  (`terrain_741.html`, 1400×900): DPR 1 loads only the two copies (1.75 MB) and the lens reuses them; DPR 2 adds the
  two full pictures when the lens goes on.
- **Fullscreen panel (2026-10-03)** — the owner: the "Changed in the map file" filters belong in fullscreen too,
  "maybe a separate panel, left or right, that opens and closes … everything neat". The fullscreen bar under the map
  became `.tc-fs-bar` = a 236 px panel LEFT of the map (`order: -1` in a row flex): Exit + a fold toggle
  (`.tc-fsp-toggle`), "Layers" as a 5-wide grid of the layer buttons, "Changed in the map file" with the moved /
  removed / added switches and the chips (the very markup `_change_controls` writes under the list — scripts.js
  `initChangeHighlights` presses every copy of a key / kind together), the mouse hints at the foot. Folded
  (`.tc-fsp-closed` on `.terrain-compare`) it's a 48 px strip with the two buttons; the map keeps its place against
  the canvas centre (`stage.left += Δwidth / 2`). Under 720 px wide it sits under the map instead.
- **Terrain audit (2026-10-02)** — the owner: "check the changed terrain for other errors too, both what the
  notes say and what actually changed". `scripts/gen/terrain_audit.py [PATCH…] --pictures sfm/final` prints, per
  step, the notes next to every change placed by its nearest landmark (tree clusters, camps moved / re-tiered /
  boxes, towers and point objects with direction, ground changes from the pictures). Found and fixed:
  - 7.38b's and 7.38c's pages said "no terrain changes": their map notes sat in the General list / under "Dire
    Safe Lane Jungle", "Top Roshan Pit", "Bottom Lane". Now **a block with `terrain_link=` is map notes, whatever
    its title**; 7.38b's two rows moved into a "Terrain Changes" block. The notes are read as Python (ast), so a
    row's inline note (7.41's "Result:" lines) comes along as the (?) popup.
  - "camp tiers changed" missed a camp demoted AND moved (7.40 read 2 of 4): `_retiered` pairs camps by mutual
    nearest position within 1000 units — not by trigger name (7.38 renumbered its camps).
  - Valve vs the map file: every direction checks out (towers, camps, pits, lotus pools, runes, watchers, gates,
    Tormentors). One claim doesn't: 7.41 "Radiant offlane tier 2 tower has been adjusted slightly to the left" —
    the tower moved 37 units west in 7.40 (whose notes say so) and not in 7.41. Changes no note mentions show in
    "Moved in the map file" (e.g. 7.39 moved Radiant bot T1 42 S and Dire top T1 67 W).
- **Changed spawn boxes stand out (2026-10-02)** — the owner: 7.39d "Increased spawnboxes of Triangle Ancient camps",
  yet the map showed nothing: the old dashed box hid a few px inside the new one, and the summary didn't count
  boxes. Now a box that didn't change is drawn once (`.tc-sb-same`), a changed one thick (`.tc-sb-changed`: new
  with a stronger fill, old dashed red over it), matched by corners (`_box_key`), and `_moved_summary` says
  "camp spawn boxes changed: n".
- **SFM session in the repo (2026-10-02)** — `scripts/gen/sfm_map_session.dmx` (KeyValues2 text, export folder =
  `FRAMES_DIR`) + `scripts/gen/sfm_session.py FRAMES OUT.dmx` (fills it in, converts with dmxconvert); the
  render scripts use it. Tests: tests/test_sfm_session.py.
- **"All layers" toggle (2026-10-02)** — the owner: "add an 'all' filter that turns every object filter on". First
  of the layer buttons (`layer_btn("all", …)`, both bars); scripts.js turns every layer on, or all off when all are
  on already, and keeps it pressed exactly while every layer is on. Icon `tc_all.png` — a 16-px pixel glyph of three
  stacked map layers in the site's gold ramp (the owner: "simpler, like our other icons"; four coloured discs were
  rejected), from `scripts/gen/gen_terrain_layer_icons.py tc_all` (the generator now takes icon names; its root
  path was one level short and wrote into scripts/icons/).
- **Map changes no note mentions — tracked every patch (the owner 2026-10-02: "useful that you mark map changes
  nobody wrote about — track it with every patch").** For each patch with a new map file: `python
  scripts/gen/terrain_audit.py <patch> --pictures <sfm/final>` (and the No-ward cells in its diff), set each change
  against the notes, and add what no note covers here (the page's "Changed in the map file" table shows the numbers;
  this list says what they are). So far:
  | Patch | Changed in the map file, no note about it |
  |---|---|
  | 7.38b | 2 trees added (the notes only remove); 16 cells turned no-ward by both Ancient camps by the offlane T1 |
  | 7.39 | Radiant bot T1 42 units S, Dire top T1 67 W; Radiant safe-lane small camp 383 NE; two "templar gates" placed (pink in our render, mended; removed in 7.39b) |
  | 7.39b | Radiant safe-lane small and large camps moved (26 / 89 units) with their spawn boxes; a watcher 22 E |
  | 7.39e, 7.40c, 7.41f | the map file changed, nothing in it moved (pictures: render noise only) |
  | 7.41 | Dire small camp 11 moved 338 E, Radiant small camp 14 439 W. And the other way round: "Radiant offlane tier 2 tower has been adjusted slightly to the left" — it didn't move (it did in 7.40; note on the patch page) |
  | 7.41a | 1 tree removed by the Dire secret shop |
  | 7.41c | 149 cells by the Twin Gates and Tormentors became wardable |
  | 7.41d | 23 cells turned no-ward (by Dire small camp 11, a Tormentor, a watcher); 693 cells at the map's edge out of bounds |
  | 7.41e | 2 cells by Radiant top T2 turned no-ward |
- **Heights layer (2026-10-05)** — the owner: "decode dota.vhcg and make a height layer; we don't go to leamare any
  more" (a ward map that knows high ground comes later). Every map file since 7.08 carries `maps/dota.vhcg`; decoded
  from the file alone (`scripts/gen/heightmap.py`, format in its docstring): a 128-byte header ("vhcg", version 1,
  cell 128, W 165, H 938, sub-grid S 5, then cell / x0 -10752 / y0 -109440 as floats), W x H records of 9 bytes
  (f32 ground height — -16384 = none; f32 a second surface, the river's water 16 above its bed; u8 flag), then one
  5 x 5 block of f32 heights per flagged (not flat) cell in the same row-major order, samples every 32 units, edges
  shared with the neighbours (7.41f: 5206 / 5206 edges agree). Heights on 7.41f: river 0, low ground 128, high ground
  256, 384, 512, 640, walls 768+. `heightmap.py all` writes, for every map file with a gridnav, a 16-bit grid
  `data/map/heights_<code>.png` (height + 1024, 0 = no ground, one value per 32 units over x -10240..10240,
  y -10752..10240 — the data a ward tool reads back) and the layer picture `icons/maps/heights_<ver>.png` (bands
  filled faintly — low ground lightest — and the step drawn on its upper side). builders/terrain.py lays it under
  every other layer (`tm-layer-heights`, old/new split by the slider), adds the "Heights" button (`tc_heights`, a
  terraced hill in the site's gold, "not so rainbow") and, only where both sides have pictures, one switch per height
  under the change list and in the fullscreen panel (`_heights_buttons`, numbers only — "0", "128" … "768+", the owner:
  "instead of River 0, Base 512 keep only the values"; 2026-10-05: the key moved off the map, "then 0, 128 … can be
  clicked to turn those layers on and off"). Each height is its own picture (`icons/maps/heights_<ver>_<band>.png`,
  heightmap.band_overlays); a switch toggles `.hband-off-<band>` on the map (scripts.js initHeightBands; with the
  layer off, a click turns it on showing just that height). In fullscreen the change chips shrink to icon + "7/28"
  (`.tf-chip-word` hidden, the word kept in the chip's tooltip). The control
  bar's gap went 6px → 2px so the 16 toggles + Zoom + Full stay one row (from a 1280-px window up). Samples with no
  height are all gridnav "void" (off the map — 7.41: 53 324, none on walkable ground), not holes in the data. Tests: tests/test_heightmap.py. The same session fixed `gridnav.py extract`: Source2Viewer-CLI keeps the
  file's path inside the `-o` folder, so `-o FILE` had made a folder and the read failed.
- **No-ward ground layer (2026-10-02)** — the owner: "a layer of every place where wards can't be placed". The map's
  gridnav (`maps/dota.gnv`, one byte per 64-unit cell; `scripts/gen/gridnav.py`) carries it: bit0 = walkable,
  bit4 = no wards (set on the walkable ground of both fountains, both Roshan pits and the secret shop — the five
  `trigger_no_wards` volumes baked in — and on every cliff edge), 20 = out of bounds. A ward stands on a walkable
  cell without bit4 (trees aside — they are entities). Stored per map file as `data/map/gridnav_<code>.gnv.gz`;
  `gridnav.py overlay` draws `icons/maps/nowards_<ver>.png` (one pixel per cell, magenta: walkable no-ward zones
  strong (210), cliffs and the void off the map one fainter shade (105; 175 / 60 until 2026-10-05, the owner: "a bit
  more saturated, it's nearly transparent" — and the two strengths are two kinds of cell, not stacked layers: bright =
  walkable no-ward ground, faint = ground nobody walks on) — until 2026-10-03 cliffs 95 / void 38, but
  7.41d moving the map's edge (670 cliff cells turned "off the map", 23 wardable ones too) then looked "more
  transparent, though nothing was added there" to the owner), laid over x -10240..10240, y -10752..10240 with
  `image-rendering: pixelated`, old/new
  split by the slider. `build_terrain_diff.py` adds `"wards": {old, new, lost, gained, cells}`; "No-ward cells
  +lost −gained" joins the changes, so 7.41c-e (only ward cells changed: invisible in the pictures) got pages.
  The layer starts off on every page, those too (the owner: "forgot to turn it off by default").
  **"How did Valve fix 7.39b's 'locations incorrectly blocked for warding'?"** Not in the map file's ward data: its
  gridnav, the five no-ward volumes (byte-identical models) and the world physics are the same as 7.39's. Not in
  server.dll either (the owner: "let's take server.dll apart" — the dota2-ida-researcher agent on the last 7.39 and
  the first 7.39b build, depot 373303 manifests 6843372111976121097 / 639057744321842479): the ward-location check
  (7.39 0x1C8FEE0) is the same — a cell must be walkable (bit 0x01) with none of 0x02 / 0x10 / 0x100, then no object
  flagged 0x20 and no live building at the point (`#dota_hud_error_no_wards_here`); of 68 real code changes none is
  ward-related. What 7.39b removed that blocks wards at runtime: the two unannounced `npc_dota_unit_templar_gate`
  ("templar portals") — `CDOTA_Unit_Templar_Gate` derives from `CDOTA_BaseNPC_Building` (building flag set on
  spawn, FILLER hull ≈ 96-112 radius, 450 HP), spawns hidden (`modifier_generic_hidden`, lifted only by an unreleased
  `CDOTA_Ability_Templar_Assassin_Hidden_Gates`). Most likely those two hidden "buildings" were the "locations
  incorrectly blocked for warding" (INFERRED: not checked whether a hidden unit stays in the ward check's point
  query). Our No-ward layer shows the map file's part of the check; trees (0x02 at runtime) and buildings add theirs
  in the game. 7.39d's "Fixed a ward spot in
  Radiant safe lane hard camp" IS in the file: 10 cells turned no-ward (4 there, 6 by the Dire safe lane small
  camp). 7.41c opened 149 cells by the Twin Gates and Tormentors, 7.41d closed 23, 7.41e 2 — no notes.
- **Facts under the list (2026-10-02)** — the owner: the lines "Trees / Neutral camps / Moved in the map file / X
  changed nothing" should be laid out better; then two centred tables "aren't harmonious — it can be better". Now
  `_facts_html` speaks the list's own look: headings styled as the list's subgroup heads (`.tf-head`), "On the
  map" as five tiles (trees, then the camp tiers small → ancient — the owner: "from smaller to bigger"), then
  (2026-10-03, the owner: "add all the other objects … trees and camps on one row, everything else on the
  others") a second grid `.tf-tiles-more` 12 px below: one tile per other kind of object the step's maps hold
  (towers, lotus pools, twin gates, Tormentors, bounty / power runes, wisdom shrines / runes, outposts, watchers,
  Roshan pits — `_MOVED_NAMES` order, counts from `counts["entities"]`), "Changed in the map file" as one chip
  per kind of object, "icon: change" (the owner: not "Added / removed: No-ward cells +2"): the layer icon (the
  name in its alt text) and "+added −removed" or "n/of all moved / re-tiered / resized" ("Bounty runes 1 moved
  (1/2)"). Tiles and chips share one gold-outline style; everything left-aligned like the list. No sentences: a
  patch whose notes say nothing about the map shows nothing for them — just the empty `ul.changes` (the subpatch
  arrows hang off it) and the facts (2026-10-03, the owner: drop "Patch notes / No terrain changes", "we won't
  write anything if there were no changes"; before that it was a list row, whose `li.li-notext::before` tag box
  drew "a red rectangular stub"); patches that changed nothing on the map are not mentioned at all (the owner:
  "remove 'Unchanged in 7.41f'").
- **Which side is which (2026-10-03)** — the OLD map is LEFT of the handle, the NEW one RIGHT, under their corner
  chips "← 7.41c OLD" / "NEW 7.41d →". Until then the new map was revealed from the left while the chips said the
  opposite, so the owner read a change outlined on 7.41c as "drawn on 7.41d". Every side rule flips together in
  styles.css: `.tc-new-layer` / `.tm-new` / `.tc-trees-new` / `.tc-camps-new` / `.tc-lens-new` clip
  `inset(0 0 0 var(--pos))`, `.tm-old` / `.tc-trees-old` / `.tc-camps-old` clip `inset(0 calc(100% - var(--pos))
  0 0)`.
- **A chip outlines its changes (2026-10-02, reworked 2026-10-03)** — pressing a "Changed in the map file" chip
  outlines the changed places on the map, except spawn boxes (their layer already draws the changed boxes red).
  Each chip but spawn boxes is a `<button class="tf-chip tf-chip-btn" data-hl="<key>" data-layer="<layer>">`.
  `_changed_points` sorts each kind of object's changes: `removed` (only on the old map), `added` (only on the new
  map), `moved` = (old spot, new spot) pairs — a removed and an added spot that are each other's nearest within
  `_MOVE_REACH` (trees 200 units, camps 1000, entities 1500), plus re-tiered camps (`_retiered_pairs`). The owner
  2026-10-03: colour = what happened (on 7.41d's "+23" no-ward cells drawn red: "it should be green, since they
  were added"), the shape = the object's own marker ("a square outline, like the tree itself"), a moved tree
  "outlined yellow on the old map — and in its new spot, yellow too, when you slide to the new map", "choose what
  to show: moved, removed or added", "taking the Trees filter into account". So `_highlights_svg` draws two hidden
  SVGs per key: `svg.tm-hl.tm-hl-<key>.tm-old` (removed red + moved yellow where it stood) and `.tm-new` (added
  green + moved yellow where it stands), each `data-layer` = its map layer (`_HL_LAYER`); squares round trees and
  camp icons, circles round the round entity markers (`_HL_SHAPE`). Overlapping outlines of one colour merge into
  ONE contour (a slightly moved object showed "two frames"): `_outline_union` draws every shape widened by half
  the stroke through an SVG mask of every shape narrowed by half the stroke, inside `g.tm-hl-g-<kind>`. Ward cells
  are filled, not outlined (the owner: "filled, more transparent, like the original purple"): `_cells_fill`, red
  on the old map = turned wardable (`wards.toWardable`), green on the new map = turned no-ward
  (`wards.toNoWard`), both from `gridnav.changed_cells`. `initChangeHighlights` (src/scripts.js): a pressed chip
  clicks its layer's bar button on when it's off, and its SVGs get `.tm-hl-on` only while that layer is shown
  (re-checked on every bar click); a layer a chip switched on (`autoLayers`) goes off again with the last pressed
  chip of that layer, unless the viewer clicked that layer (or "All") meanwhile — then it's theirs and stays (the
  owner 2026-10-03: a chip turned the No-ward layer on and it stayed on); the moved / removed / added switches by the heading (`.tf-kind`, only the
  kinds the step has — `_hl_kinds`) put `.hl-hide-<kind>` on the map. The layer bar spreads its buttons across
  the map's width (`justify-content: space-between`) — "like the minimap's header".
- **Quiet patches get no page** (the owner 2026-10-02: "if nothing changed in a patch, there's nothing to compare"):
  a same-file patch (7.40b, 7.41b) and a step whose notes list nothing and whose map file moved nothing
  (`_quiet`: 7.39e, 7.40c). The NEWEST step keeps its page all the same (the owner 2026-10-03: without it "one
  could think the patch doesn't exist") — 7.41f, the current map. Their pictures differ from the patch before only by render noise —
  `scripts/gen/map_picture_diff.py OLD_full.png NEW_full.png` (biggest blob ≤ 616 px at 8 units/px; a real change
  like 7.39 → 7.39b makes 1000-3800). The page before names them: "7.41b – 7.41f changed nothing on the map"
  (`_quiet_runs`). 10 pages now: 7.38, 7.38b, 7.38c, 7.39, 7.39b, 7.39c, 7.39d, 7.40, 7.41, 7.41a.
- **7.38's page** (the owner 2026-10-02: "make the 7.37e picture so 7.38 has a page"): 7.37e rendered on the 7.40c
  clone like the others (its water renders fine there). 7.38's map notes sit under `plain_header("Wandering
  Waters")` and `("Other Terrain Changes")` — the parser takes those too, each as a subgroup, and the headers carry
  `terrain_link="7.38"`. Before 7.38 the Lotus Pools were `npc_dota_mango_tree` and wisdom came from
  `dota_item_rune_spawner_xp` runes: `build_terrain_diff.py` reads the old class name for the lotus layer and keeps
  a `wisdomRunes` entity set (no map layer), so 7.38 reads "lotus pools moved: 2, wisdom runes +0 −2".
- **Pictures and objects per map file**, named by the FIRST patch that shipped the file: `icons/maps/map_<ver>.webp`,
  `data/map/mapdata_<code>.json` (so `mapdata_741` = 7.41's release map, 2476 trees; `741f` = today's, 2475).
- **Each page's list = that patch's own notes**; a patch whose notes list none shows "The patch notes list no terrain
  changes." Under the counts, **"Moved in the map file"** (`_moved_summary`, read off the diff: "trees +38 −27, camps
  moved: 2, towers moved: 1, watchers moved: 1" for 7.39b — what its notes say) or "nothing (the file still changed)".
- **Markers + layer toolbar** — every step ships `data/terrain_diff_<patch>.json`
  (`python scripts/gen/build_terrain_diff.py` builds every step; `<old>:<new>` one pair; generic keys
  `treesOld/New`, `campsOld/New`, `entities`). The SHARED crop meta (`terrain_map_meta.json`) projects any patch's
  markers. A pair WITHOUT a diff passes empty `markers_svg` → `_controls_html(layers=False)` (Zoom only).
  **Add a new patch:** render its map file (SFM section), copy the picture + `mapdata` under the first-shipping
  patch's name, refresh `data/map/patch_maps.json` + `renders.json`, run `build_terrain_diff.py`; the page appears.
- **scripts.js inits ALL sliders** — `initTerrainCompare` does
  `querySelectorAll('.terrain-compare').forEach(initOneTerrainCompare)`; the
  default-hidden second pane (7.40) still gets a working handle/lens/toggles so the
  picker can reveal it. (Was a single `querySelector` → only the first pane worked.)
- **No-map fallback (`_fallback_html`)** — for a patch with changes but no map
  pair: the latest map blurred + dimmed with a centred "Map comparison for X
  isn't available yet" overlay; the textual change list still renders.
- **Deep-link from patch pages** — `plain_header("Terrain Changes",
  terrain_link="<base_ver>")` (`patch/elements.py`) renders a gold `.terrain-jump-btn`
  "View on map" link in the section header → `../terrain_<code>.html` — that patch's own page (every patch with
  terrain notes has one). The subpatch arrows (`initSubpatchPicker`) step to the neighbouring pages in the header
  menu's order. ⚠ The parser regex is `plain_header\("Terrain Changes"` (no trailing `\)`) so
  the new `terrain_link=` arg doesn't make it miss every block.

## TODO / action items

1. ✅ **No-map fallback** — done (`_fallback_html`).
2. ✅ **Patch picker** — done; one page per patch whose map file changed (+ any patch with terrain notes). A new
   patch: see "One page per patch" above. 7.37e's picture (done 2026-10-02) gives 7.38 its page.
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
