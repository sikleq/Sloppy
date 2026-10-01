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
- **Calendar and changelog.** Patch lifespans and yearly stats; the site's own changelog.
- **Terrain comparison.** An old ↔ new map slider per map change, with trees, camps, towers, runes and objectives as
  layers. Map entities are read straight from the game's map files (`scripts/gen/extract_map_entities.py`).
- **Materials.** Hero stats, Hero Lab, hero/item change matrices, neutral creeps and their abilities, mana items,
  AoE bonuses, structures.

## Repository layout

```
build_site.py               ← SINGLE entrypoint: python build_site.py [steps] [--latest]
builders/
  build_patches.py          ← patch pages: auto-discovers content/p*.py → dist/patches/<ver>.html
  entity_changes.py         ← one page per hero / item / unit + the Hero / Item / Unit Changes indexes
  changelog.py              ← calendar.html, changelog.html
  creeps.py                 ← neutral_stats.html, neutral_abilities.html
  heroes_stats.py / heroes_dyn.py / items_dyn.py / hero_lab.py / mana_items.py / aoe_increase.py
  terrain.py                ← terrain_<ver>.html (one page per map change)
  silent.py                 ← dist/patches/silent/<ver>.html (changes the notes don't mention)
  site_common.py            ← shared nav, favicons, asset versioning

generate_patch_code_v2.py   ← Valve datafeed → Python scaffold for content/p<ver>.py + normalized JSON
styles.css / src/scripts.js ← the one stylesheet and script of every page (minified into dist/)

patch/                      ← the content API used by content/p*.py: li(), b(), t(), headers, cards, …
content/p<version>.py       ← one annotated patch each; auto-discovered, no registration
tests/                      ← pytest (run in CI)

data/
  stats/<version>/          ← per-patch game-file snapshots (heroes, items, abilities, units)
  <version>_datafeed.json   ← cached Valve datafeed
  normalized/patches/*.json ← structured per-patch artifact
  map/mapdata_<code>.json   ← map entities read from the game's map files
icons/                      ← local mirror of hero, item, ability and map images
scripts/
  fetch/                    ← data fetchers
  gen/                      ← generators: map entities, map pictures, layer icons, …
  audit/                    ← content and icon audits

dist/                       ← build output, served by GitHub Pages (not committed)
```

## Quick start

Requires **Python 3.10+**. The build has **no third-party dependencies**; the test suite needs `pytest`, `rcssmin`,
`rjsmin`.

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

1. Register the version in `patch/meta.py` (`PATCHES` + `RELEASE_HISTORY`).
2. Refresh `data/stats/<version>/` with the `scripts/fetch/` helpers, then the global snapshots
   (`patchnotes_english.txt`, `abilities_slim.json`, `herolist.json`, `itemlist.json`).
3. Generate the scaffold: `python generate_patch_code_v2.py 7.42`.
4. Review it and save it as `content/p742.py` (auto-discovered).
5. Run the gates:
   ```powershell
   python -m pytest tests -q
   python build_site.py
   python tools/validate_data.py
   python scripts/audit/check_icons.py
   python scripts/audit/audit_all.py
   ```

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

- Game data history from [muk-as/DOTA2_CLIENT](https://github.com/muk-as/DOTA2_CLIENT) and
  [dotabuff/d2vpkr](https://github.com/dotabuff/d2vpkr).
- Game files read with [ValveResourceFormat](https://github.com/ValveResourceFormat/ValveResourceFormat) (Source2Viewer).
- Map tiles and coordinates for older map versions from [Spectral](https://spectral.gg) /
  [leamare/dota-interactive-map](https://github.com/leamare/dota-interactive-map).
- Icons from Valve's CDN; patch notes from Valve's datafeed.
- Landing-page inventory UI: [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui) by **abyssowl**.
