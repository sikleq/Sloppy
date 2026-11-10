# Dota 2 Enhanced Patch Reader and Materials

Valve's Dota 2 patch notes as a readable, filterable changelog, plus reference tables built from the game's own files.

**Live site:** <https://sikleq.github.io/Sloppy/>

## What you get

| | |
|---|---|
| **Tags and percents** | Every row is tagged BUFF / NERF / REWORK / NEW / DEL / MISC / QoL and shows its change in percent. Rows the notes word ambiguously are checked against the game files of both patches. |
| **Formulas by level** | `14% + 1% per level` unfolds into a table by level. |
| **Before and after** | A reworked ability, facet or item as a card: the new one on top, the old one a click away, its values beside the text with what changed in colour. |
| **Filters and search** | Show only the tags you want; find any hero, item or ability on the page. |
| **A page for everything** | Each hero, item and unit has its own page with all its changes across patches. |
| **Terrain** | An old ↔ new map slider for every map change, with trees, camps, towers, runes and objectives as layers. |
| **Silent changes** | What a patch changed in the game files without a line in the notes (since 7.35). |
| **Materials** | Hero stats with the history of every cell, Hero Lab, hero and item change matrices, neutral creeps, mana items, AoE bonuses, structures. |
| **Calendar** | Patch lifespans and yearly stats. |

## Quick start

Python 3.10+. The build needs no third-party packages.

```powershell
git clone https://github.com/sikleq/Sloppy.git
cd Sloppy
python build_site.py                               # everything → dist/
python -m http.server 8765 --directory dist        # open http://localhost:8765
```

Tests and minification: `pip install -r requirements-dev.txt`, then `python -m pytest tests -q`.
Maintenance scripts (icons, game files, map tools): `pip install -r requirements-tools.txt`.

A full build needs raw game files from a separate private store (`patch/game_files.py`, laid out by
`python tools/game_files.py materialize`); CI has a read-only key for it.

## Where the data comes from

- **Patch notes** — Valve's datafeed and the game's own `patchnotes_english.txt`.
- **Game files of every patch since 7.08** — one snapshot per patch, taken from that patch's own build. The slim
  tables the site needs are in `data/stats/<version>/`.
- **Icons** — Valve's CDN, mirrored in `icons/`. **Map entities and pictures** — the game's map files, rendered in
  Source Filmmaker ([Oldgrowth](https://github.com/sikleq/Oldgrowth)).

## Layout

```
build_site.py        the single entrypoint: python build_site.py [steps] [--latest]
content/p<ver>.py    one annotated patch each; found automatically
patch/               what content files are written with (rows, badges, cards) and the core every builder shares
builders/            one module per kind of page: patches, hero / item / unit pages, tables, terrain, silent changes
src/css, src/js      styles and scripts of every page, glued and minified into dist/
data/                per-patch snapshots (stats/), cached datafeeds, rules tables, map entities
icons/               hero, item, ability and map images
tools/, scripts/     commands and data fetchers / generators / audits
tests/               pytest, run in CI
docs/                architecture, workflow, data format, rules
dist/                build output, served by GitHub Pages (not committed)
```

## Adding a new patch

1. `python tools/new_patch.py 7.42 21.10.2026` — registers the version, reads the installed game, builds the
   snapshots, drafts the page, builds the site and checks it.
2. Proofread the draft into `content/p742.py`, then `python tools/new_patch.py 7.42 --from enchant`.
3. Run the gates: `python -m pytest tests -q` and `python tools/ci_local.py`.

Full guide: [docs/workflow.md](docs/workflow.md).

## Docs

- [docs/architecture.md](docs/architecture.md) — how the modules fit together
- [docs/data-format.md](docs/data-format.md) — the data files and the `b()` / `bf()` / `t()` helpers
- [docs/agent-rules/](docs/agent-rules/) — tagging, formulas, rendering and style rules
- [docs/terrain.md](docs/terrain.md) — the Terrain pages and the map pipeline

## CI

- `build.yml` — on every push to `main` and every PR: tests, the full build, content and icon audits. On `main` the
  result is published to GitHub Pages.
- `audit-live.yml` — daily: checks display names against Valve's live datafeed. Kept out of the deploy path, so a
  Valve outage never blocks a deploy.

## Contributing

Pull requests welcome: tag corrections, older patch ports, missing icons. For a bug report name the patch, the hero /
item / ability, and what you expected against what the page shows.

## License

Code: **MIT**, see [LICENSE](LICENSE). Dota 2 content (patch notes text, names, icons, images, map pictures, game
data) is © Valve Corporation; this is an unofficial fan project, not affiliated with or endorsed by Valve. The landing
page's [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui) pack by **abyssowl** stays under its own license.

## Acknowledgements

- Game-file history before our own snapshots:
  [SteamTracking/GameTracking-Dota2](https://github.com/SteamTracking/GameTracking-Dota2) (2016 – 2023) and
  [muk-as/DOTA2_CLIENT](https://github.com/muk-as/DOTA2_CLIENT) (2023 – now); GameTracking also feeds the daily
  new-build watch.
- Calendar's Test servers tab: Experimental and Staging builds from the log of
  [muk-as/DOTA2_WEB](https://github.com/muk-as/DOTA2_WEB) (since November 2023) and the same author's channel
  t.me/DOTA_DM_SPAM (October 2021 to November 2023); newer builds from Valve's Web API.
- Game files read with [ValveResourceFormat](https://github.com/ValveResourceFormat/ValveResourceFormat) and
  [vpk](https://github.com/ValvePython/vpk).
- Terrain page inspired by [devilesk](https://github.com/devilesk/dota-interactive-map).
