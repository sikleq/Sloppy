# Dota 2 Enhanced Patch Reader and Materials

A static site that turns Valve's raw Dota 2 patch notes into a readable, filterable changelog. Every change is tagged (BUFF / NERF / REWORK / NEW / DEL / MISC / QoL), every numeric delta is computed as a percentage, every per-level formula is expandable into a per-hero-level table.

**Live site:** <https://sikleq.github.io/Sloppy/>

## What it does differently from dota2.com/patches

- **Direction at a glance.** Each row shows a coloured `+12% BUFF` / `-9% NERF` badge derived from the underlying numbers — no arithmetic required.
- **Per-level scaling unfolded.** Formula rows (`14% + 1% per level`) expand into a full L1–L30 table.
- **Stat changes verified against game data.** Base stat deltas auto-cross-reference `data/stats/<patch>/heroes.json` extracted from Valve's KV files.
- **Ability reworks as before/after panes** with icons stacked side-by-side.
- **Filter by tag.** Click a chip to surface only BUFF, NERF, DEL, etc. rows across the page.
- **Calendar view.** Chronological patch list with lifespans, sparklines, and yearly stats.
- **Terrain comparison.** Side-by-side map diff slider comparing Dota 2 map layouts across patches.
- **Hero/item dynamics matrix.** Tag breakdown per entity across all patches.

## Repository layout

```
build_site.py               ← SINGLE entrypoint: python build_site.py [steps] [--latest]
builders/
  build_patches.py          ← orchestrator: auto-discovers content/p*.py
  creeps.py                 ← generates dist/creeps.html
  heroes_stats.py           ← generates dist/heroes_stats.html
  heroes_dyn.py             ← generates dist/heroes_dyn.html
  items_dyn.py              ← generates dist/items_dyn.html
  hero_lab.py               ← generates dist/hero_lab.html
  mana_items.py             ← generates dist/mana_items.html
  aoe_increase.py           ← generates dist/aoe_increase.html
  terrain.py                ← generates dist/terrain.html
  silent.py                 ← generates dist/patches/silent/{version}.html

generate_patch_code_v2.py   ← KV → Python scaffold + data/normalized/patches/<ver>.json
styles.css                  ← site stylesheet (minified into dist/)
src/scripts.js              ← site JavaScript (minified into dist/)

patch/
  output.py / state.py      ← HTML accumulator + global build state
  api.py                    ← public re-export consumed by content/p*.py
  images.py                 ← HERO_SLUG, ITEM_SLUG, _LOCAL_ABIL_ICONS
  stats.py                  ← stat DB loaders, stat_h/i/u(), bstat_*()
  badges.py                 ← b(), br(), bf(), t(), facet_badge(), scale_pill()
  elements.py               ← HTML builders: li(), section(), ability(), headers…
  meta.py                   ← PATCHES, RELEASE_HISTORY, latest_stats_version()
  page.py                   ← write_head/footer, save_html, asset minification
  calendar.py / index_page.py / rosters.py
  known_exceptions.py       ← shared ability/icon allowlists (audits + builders)

content/p<version>.py       ← per-patch def build(); auto-discovered, no registration
tests/                      ← pytest unit tests (run in CI)

data/
  abilities_slim.json       ← authoritative ability slug → dname + is_innate
  patchnotes_english.txt    ← Valve loc keys; herolist.json / itemlist.json
                              (global snapshots — refresh every patch, workflow Step 2b)
  stats/<version>/          ← full per-patch snapshot — see docs/workflow.md
  normalized/patches/*.json ← structured per-patch artifact (CI-required)
  <version>_datafeed.json   ← cached Valve datafeed JSON

icons/                      ← local mirror of hero, item, ability icons
scripts/
  fetch/                    ← data fetchers (fetch_icons, fetch_*_history, …)
                              extract_patchnotes.py: VPK → repo sync (patch notes + KV)
  gen/                      ← asset generators (terrain maps, layer icons, …)
  audit/                    ← auditors (audit_all, audit_*, check_icons)

# Build output — not committed:
dist/                       ← everything served by GitHub Pages
```

## Quick start

Requires **Python 3.10+**. The build itself has **no third-party
dependencies** — only the test suite does (`pytest`, `rcssmin`, `rjsmin`).

```powershell
git clone https://github.com/sikleq/Sloppy.git
cd Sloppy

# Build everything — output goes to dist/
python build_site.py

# Serve locally
python -m http.server 8765 --directory dist

# Run tests
pip install -r requirements-dev.txt
python -m pytest tests -q
```

## Adding a new patch

Short version (full guide: [docs/workflow.md](docs/workflow.md)):

1. Register the version in `patch/meta.py` (`PATCHES` + `RELEASE_HISTORY`).
2. Refresh `data/stats/<version>/` via the `scripts/fetch/` helpers — the
   strict CI manifest checks every required JSON/TXT. Then refresh the
   **global** snapshots (`patchnotes_english.txt`, `abilities_slim.json`,
   `herolist.json`, `itemlist.json`) — workflow Step 2b; `tests/test_snapshots_fresh.py`
   fails if `patchnotes_english.txt` lacks the newest patch.
3. Generate the scaffold + normalized JSON:
   ```powershell
   python generate_patch_code_v2.py 7.42
   ```
4. Review the scaffold and save it as `content/p742.py` (auto-discovered;
   no registration in any builder).
5. Register any new slugs in `HERO_SLUG` / `ITEM_SLUG`; confirm new ability
   slugs against `data/abilities_slim.json`.
6. Run the gates:
   ```powershell
   python -m pytest tests -q
   python build_site.py
   python tools/validate_data.py
   python scripts/audit/check_icons.py
   python scripts/audit/audit_all.py
   ```

## Architecture & data format

- [docs/architecture.md](docs/architecture.md) — how the modules fit together.
- [docs/data-format.md](docs/data-format.md) — Valve KV format, the `b()` / `bf()` / `t()` helper API, the `l=True` flag rules.

## CI

Two GitHub Actions workflows:

- **`.github/workflows/build.yml`** — runs on every push to `main` and on
  PRs. Required before deploy: pytest, full `build_site.py`,
  minification verification, normalized-JSON validation, content-rule
  audits (tag direction, BAT `l=True`, trailing whitespace, ul balance,
  ability-slug registry),
  the strict current-patch stats manifest, and `check_icons.py`. On `main`,
  the resulting `dist/` is published to GitHub Pages.
- **`.github/workflows/audit-live.yml`** — runs on a daily schedule (and
  on `workflow_dispatch`). Performs `audit_all.py`, which makes live HTTP
  requests to `dota2.com/datafeed/...` to verify display names against
  Valve's API. **Deliberately decoupled from the deploy path** — a Valve
  outage or rate limit must not block a good deploy.

## Contributing

Pull requests welcome. Most useful:

- **Patch ports** for older versions (anything pre-7.33 lacks the stats DB layer).
- **Tag corrections** when the autodetector mislabels a change.
- **Icon mirror updates** for new innate ability icons.

Bug reports: include the patch version, hero/item/ability, and expected vs rendered output.

## License

**PolyForm Noncommercial 1.0.0** — see [LICENSE](LICENSE).

Source is open for reading, learning, hobby and educational use. **Commercial use is not permitted** without a separate license.
Contact [@sikleq](https://github.com/sikleq) for commercial licensing inquiries.

## Acknowledgements

- Game data extracted via [muk-as/DOTA2_CLIENT](https://github.com/muk-as/DOTA2_CLIENT) (npc_heroes.txt / items.txt history since 7.33).
- Icons from Valve's official `cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/` CDN.
- Landing-page inventory UI uses the [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui) pack by **abyssowl**.
- Patch notes © Valve Corporation. Unofficial fan project, not affiliated with or endorsed by Valve.
