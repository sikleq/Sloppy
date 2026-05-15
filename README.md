# Sloppy — Dota 2 Patch Notes, Reorganized

A static site that turns Valve's raw Dota 2 patch notes into a readable, filterable changelog. Every change is tagged (BUFF / NERF / REWORK / NEW / DEL / MISC / QoL), every numeric delta is computed as a percentage, every per-level formula is expandable into a per-hero-level table.

**Live site:** <https://sikleq.github.io/Sloppy/>

## What it does differently from dota2.com/patches

- **Direction at a glance.** Each row shows a coloured `+12% BUFF` / `-9% NERF` badge derived from the underlying numbers — no need to do arithmetic in your head.
- **Per-level scaling unfolded.** Formula rows (`14% + 1% per level`) expand into a per-hero-level table with the delta at L1 … L30, instead of leaving the reader to compute.
- **Stat changes verified against game data.** Base stat deltas (HP, damage, armor, etc.) auto-cross-reference `data/stats/<patch>/heroes.json` extracted from Valve's KV files — never trust the patchnote text alone.
- **Ability reworks rendered as before/after panes** with the icons stacked and shuffleable, so you can see the swap at a glance.
- **Aghanim's Scepter / Shard upgrades** get their own visual stripe and are always merged with their description.
- **Filter by tag.** Click a filter chip to surface only BUFF, NERF, DEL, etc. rows across the page.

## Repository layout

```
build_patch.py            ← generator. Contains HTML helpers, CSS, JS, and patch content
generate_patch_code.py    ← KV → Python codegen. Run before integrating a new patch
apply_stats_to_build.py   ← post-processor: t() → bstat_h() where stats DB knows the value
check_icons.py            ← validates every ability icon URL against Valve CDN

data/
  patchnotes_english.txt  ← raw Valve KV
  patchnotes_russian.txt  ← raw Valve KV (Russian)
  abilities_slim.json     ← ability slug → display name + innate flag
  stats/<version>/        ← npc_heroes.json + items.json + abilities.json per patch

patches/                  ← generated HTML (output of build_patch.py)
icons/                    ← local mirror of hero, item, ability icons
docs/                     ← architecture, data format, contribution workflow

index.html                ← landing redirect → latest patch
calendar.html             ← chronological patch list
styles.css / scripts.js   ← standalone CSS/JS for index.html and calendar.html
```

## Quick start

```bash
git clone https://github.com/sikleq/Sloppy.git
cd Sloppy

# Re-render every patch HTML
python build_patch.py
```

This regenerates `patches/*.html`, `calendar.html`, `styles.css`, `scripts.js`, and the `_ability_icons.txt` audit list. Open `patches/7.41c.html` (or any other version) to view.

## Adding a new patch

1. Drop the new patch's KV file into `data/patchnotes_english.txt`.
2. Generate a Python scaffold:
   ```bash
   python generate_patch_code.py 7.42
   ```
   produces `_generated_p_7.42.py` — review and edit it (the autodetector gets tags right ~80% of the time).
3. Integrate the reviewed code into `build_patch.py` under the appropriate version section.
4. If new heroes / items appeared, register their slugs in `HERO_SLUG` / `ITEM_SLUG` at the top of `build_patch.py`.
5. Rebuild:
   ```bash
   python build_patch.py
   ```
6. Open `patches/7.42.html` in a browser. Verify filters, formula tables, icons.

Full step-by-step guide: [docs/workflow.md](docs/workflow.md).

## Architecture & data format

- [docs/architecture.md](docs/architecture.md) — how `generate_patch_code.py` and `build_patch.py` fit together.
- [docs/data-format.md](docs/data-format.md) — Valve KV format, the `b()` / `bf()` / `t()` helper API, the `l=True` flag rules.

## Contributing

Pull requests welcome. The most useful contributions:

- **Patch ports** for older versions (anything pre-7.33 currently lacks the stats DB layer).
- **Tag corrections** when the autodetector mislabels a change (e.g. a `no longer has a penalty` row that should be BUFF, not DEL).
- **Icon mirror updates** if Valve adds an innate ability icon that we still fall back to the generic marker for.

Bug reports: include the patch version, the hero/item/ability, and what you expected the row to show vs what's rendered.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

- Game data extracted via [muk-as/DOTA2_CLIENT](https://github.com/muk-as/DOTA2_CLIENT) (npc_heroes.txt / items.txt history since 7.33).
- Icons from Valve's official `cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/` CDN.
- Patch notes © Valve Corporation. This is an unofficial fan project, not affiliated with or endorsed by Valve.
