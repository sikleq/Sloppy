# Dota 2 Enhanced Patch Reader and Materials

A static site that turns Valve's raw Dota 2 patch notes into a readable, filterable changelog, plus a set of
reference tables built from the game's own files. Every change is tagged (BUFF / NERF / REWORK / NEW / DEL / MISC /
QoL), every numeric delta is computed as a percentage, every per-level formula unfolds into a per-level table.

**Live site:** <https://sikleq.github.io/Sloppy/>

## What it does differently from dota2.com/patches

- **Direction at a glance.** Each row shows a coloured `+12% BUFF` / `-9% NERF` badge derived from the numbers — no
  arithmetic required. Rows the notes word ambiguously are checked against the game files of both patches.
- **Per-level scaling unfolded.** Formula rows (`14% + 1% per level`) expand into a full table by level.
- **Before → after cards.** Reworked abilities, facets and item abilities side by side, as in the game's tooltips
  (cast range, mana, cooldown in a header strip); item stats and recipes as before → after cards with their prices.
- **Filter by tag.** Click a chip to surface only BUFF, NERF, DEL, … rows across the page.
- **Every hero, item and unit on its own page** — all its changes across patches, with a patch-by-patch strip.
- **Calendar.** Patch lifespans and yearly stats.
- **Terrain comparison.** An old ↔ new map slider per map change, with trees, camps, towers, runes and objectives as
  layers. The map pictures are rendered in Source Filmmaker (`scripts/gen/stitch_sfm.py`) and the map entities are
  read straight from the game's map files (`scripts/gen/extract_map_entities.py`).
- **Silent changes.** What a patch changed in the game files without a line in the notes, per hero
  (`dist/patches/silent/<ver>.html`, since 7.35).
- **Materials.** Hero stats with the history of every cell, Hero Lab, hero/item change matrices, neutral creeps and
  their abilities, mana items, AoE bonuses, structures.

## Where the data comes from

- **Patch notes** — Valve's datafeed (`data/<version>_datafeed.json`) and the game's own `patchnotes_english.txt`.
- **Game files of every patch since 7.08** — our own copy: one snapshot per patch, taken from that patch's own
  build (the first build with its notes, plus the release-day fixes within 24 h and a later build that brings the patch's own noted values). The slim per-patch tables the site needs are
  committed in `data/stats/<version>/`; the game files themselves live in a separate private store, read through
  `patch/game_files.py`. The raw files some pages need (per-hero KV, the newest patches' root KV) are laid out into
  `data/stats/` from the store by `python tools/game_files.py materialize` — CI does it with a read-only deploy key,
  so a full build needs access to the store. New patches are taken from the installed game (`tools/new_patch.py`).
- **Icons** — Valve's CDN, mirrored in `icons/`; **map entities** — the game's map files.

## Repository layout

```
build_site.py               ← SINGLE entrypoint: python build_site.py [steps] [--latest]
builders/
  build_patches.py          ← patch pages: auto-discovers content/p*.py → dist/patches/<ver>.html
  entity_changes.py         ← one page per hero / item / unit + the Hero / Item / Unit Changes indexes
  creeps.py                 ← neutral_stats.html, neutral_abilities.html
  creeps_common.py / creeps_history.py / creeps_abilities.py  ← its helpers, cell history, abilities page
  heroes_stats.py / heroes_dyn.py / items_dyn.py / hero_lab.py / mana_items.py / aoe_increase.py
  terrain.py                ← terrain_<ver>.html (one page per map change)
  silent.py                 ← dist/patches/silent/<ver>.html (changes the notes don't mention)

tools/generate_patch_code_v2.py   ← Valve datafeed → Python scaffold for content/p<ver>.py + normalized JSON
styles.css / src/scripts.js ← the one stylesheet and script of every page (minified into dist/)

patch/                      ← the content API used by content/p*.py: li(), b(), t(), headers, cards, …
                              and the release list (patch/meta.py RELEASE_HISTORY); also the core every builder
                              shares — site_common.py (nav, favicons, asset versioning), kv.py, game_files.py (the
                              game-files store), loc_history.py, terrain_index.py; it imports nothing from builders/
                              or tools/
content/p<version>.py       ← one annotated patch each; auto-discovered, no registration
tests/                      ← pytest (run in CI)
tools/                      ← commands: new_patch.py (a new patch end to end), game_files.py materialize,
                              item_history.py, resync_snapshots.py, slim_from_kv.py, patch_check.py, ci_local.py, …

data/
  stats/<version>/          ← per-patch snapshots of the game files (heroes, items, abilities, units)
  <version>_datafeed.json   ← cached Valve datafeed
  normalized/patches/*.json ← structured per-patch artifact
  rules/                    ← tables built from the game history (talent slots, item stat prices, weights, …)
  map/mapdata_<code>.json   ← map entities read from the game's map files
icons/                      ← local mirror of hero, item, ability and map images
scripts/
  fetch/                    ← data fetchers (local game, Valve datafeed, the game-files store)
  gen/                      ← generators: map entities, map pictures, layer icons, …
  audit/                    ← content and icon audits
docs/                       ← architecture, workflow, data format, agent rules

dist/                       ← build output, served by GitHub Pages (not committed)
```

## Quick start

Requires **Python 3.10+**. The build has **no third-party dependencies**; the test suite needs `pytest`, `rcssmin`,
`rjsmin`. The maintenance scripts (fetching icons and game files, map tools) need more — not for the build:
`pip install -r requirements-tools.txt`.

```powershell
git clone https://github.com/sikleq/Sloppy.git
cd Sloppy

python build_site.py                               # everything → dist/
python -m http.server 8765 --directory dist        # serve locally

pip install -r requirements-dev.txt
python -m pytest tests -q
```

## Adding a new patch

Short version (full guide: [docs/workflow.md](docs/workflow.md)):

1. One command does the data side — registers the version, reads the game files from the installed game, builds the
   snapshots and shared tables, drafts the page, builds the site and checks it:
   ```powershell
   python tools/new_patch.py 7.42 21.10.2026
   ```
2. Proofread the draft into `content/p742.py` (auto-discovered), then `python tools/new_patch.py 7.42 --from enchant`.
3. Run the gates: `python -m pytest tests -q` and `python tools/ci_local.py` (the CI audits).

## Architecture & rules

- [docs/architecture.md](docs/architecture.md) — how the modules fit together.
- [docs/data-format.md](docs/data-format.md) — the KV format and the `b()` / `bf()` / `t()` helpers.
- [docs/agent-rules/](docs/agent-rules/) — tagging, formulas, rendering and style rules.
- [docs/terrain.md](docs/terrain.md) — the Terrain pages and the map pipeline.

## CI

- **`.github/workflows/build.yml`** — every push to `main` and every PR: pytest, the full build, minification check,
  normalized-JSON validation, content audits, the current-patch stats manifest, icon check. On `main` the resulting
  `dist/` is published to GitHub Pages.
- **`.github/workflows/audit-live.yml`** — daily (and on demand): checks display names against Valve's live datafeed.
  Kept out of the deploy path, so a Valve outage never blocks a deploy.
- **`.github/workflows/game-build-watch.yml`** — daily: opens an issue when a new game build differs from the newest
  snapshot (a new patch, or a build without notes).

## Contributing

Pull requests welcome — tag corrections, older patch ports, missing icons. For a bug report include the patch, the
hero / item / ability, and what you expected vs. what the page shows.

## License

The code is released under the **MIT License** — see [LICENSE](LICENSE).

Not covered by it: Dota 2 game content — patch notes text, names, icons, images, map pictures and game data — is
© Valve Corporation and is used here as an unofficial fan project, not affiliated with or endorsed by Valve. The
landing page's [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui) pack by **abyssowl** stays under its own
license.

## Acknowledgements

- The history of the game files before our own snapshots was assembled once from the archives of
  [SteamTracking/GameTracking-Dota2](https://github.com/SteamTracking/GameTracking-Dota2) (2016 – 2023) and
  [muk-as/DOTA2_CLIENT](https://github.com/muk-as/DOTA2_CLIENT) (2023 – now); GameTracking also feeds the daily
  new-build watch.
- Game files read with [ValveResourceFormat](https://github.com/ValveResourceFormat/ValveResourceFormat) (Source2Viewer)
  and [vpk](https://github.com/ValvePython/vpk).
- Terrain page: inspired by [devilesk](https://github.com/devilesk/dota-interactive-map); map pictures and data:
  [Oldgrowth](https://github.com/sikleq/Oldgrowth).
- Icons from Valve's CDN; patch notes from Valve's datafeed.
- Landing-page inventory UI: [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui) by **abyssowl**.
