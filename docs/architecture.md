# Architecture

## Data flow

```
data/<version>_datafeed.json        (Valve datafeed JSON, cached)
data/stats/<version>/               (full per-patch KV+JSON snapshot)
        ↓
generate_patch_code_v2.py           (parser → patch/ helper calls)
        ↓
_generated_p_<version>_v2.py        (intermediate, reviewed by hand)
data/normalized/patches/<ver>.json  (structured artifact, CI-required)
        ↓
content/p<version>.py               (reviewed def build(); auto-discovered)
        ↓
build_site.py                       (single entrypoint, runs all steps)
   └─ builders/build_patches.py     (auto-discovers content/p*.py)
   └─ builders/{creeps,mana_items,heroes_stats,heroes_dyn,
               items_dyn,hero_lab,aoe_increase,terrain,silent}.py
        ↓
dist/                               (final site, served by GitHub Pages)
```

## The `patch/` package

Helpers are imported in every `content/p*.py` via `from patch.api import *`.

| Module | Purpose |
|---|---|
| `patch/images.py` | CDN constants, `HERO_SLUG` / `ITEM_SLUG`, `_LOCAL_ABIL_ICONS` |
| `patch/badges.py` | `gradient_class()`, `b()`, `br()`, `bf()`, `t()`, `scale_pill()` |
| `patch/elements.py` | HTML helpers: `hero_header()`, `item_header()`, `section()`, `ability()`, `li()`, `subnote()`, … |
| `patch/output.py` / `patch/state.py` | `W()` writer accumulator + `_State` build singleton |
| `patch/page.py` | `write_head()` / `write_footer()` / `save_html()`; reads `styles.css` + `src/scripts.js` from disk, minifies into `dist/`, stamps a cache-busting `?v=` |
| `patch/meta.py` | `PATCHES`, `RELEASE_HISTORY`, `latest_stats_version()` |
| `patch/known_exceptions.py` | shared ability/icon allowlists (imported by audits AND builders so they cannot drift) |
| `patch/rosters.py` | hero/item rosters, writes `_dynamics.json` |
| `patch/index_page.py` / `patch/calendar.py` | landing "inventory book" + calendar/cadence infographic |
| `content/p<version>.py` | per-patch `def build()` — auto-discovered, never imported manually |
| `builders/build_patches.py` | orchestrator — walks `content/p*.py` in chronological order from `RELEASE_HISTORY` |

`python build_site.py` writes everything to `dist/`: one HTML per patch
under `dist/patches/`, plus `index.html`, `calendar.html`, `neutral_stats.html`
(with `creeps.html` / `neutral_creeps.html` / `materials.html` redirects),
`unit_abilities.html`, `structures.html`, `heroes_stats.html`, `heroes_dyn.html`,
`items_dyn.html`, `hero_lab.html`, `mana_items.html`, `aoe_increase.html`,
`terrain_<code>.html` (one per map-changing patch) + `terrain_stats.html`,
`hero_changes.html` / `item_changes.html` / `unit_changes.html`, `changelog.html`, the
`dist/patches/silent/*.html` KV-diff pages, `_dynamics.json`, and minified
copies of `styles.css` + `src/scripts.js`. `styles.css` and `src/scripts.js`
in the repo root are **source files, not outputs**.

### Patch-dynamics widget (dyn-cells)

Each entity header (`hero_header`/`item_header`/`unit_header`/`plain_header`) calls
`_register_entity()`, which emits an `id="dyn-<kind>-<slug>"` and feeds the per-patch
tag tally (`_dynamics.json`); `scripts.js` then renders a diamond row on every
`.entity[id^="dyn-"]`. **Exception:** everything under the big **"General Updates"**
section (slug `general` — General Changes, Map Objectives, Terrain Changes, Captains
Mode, …) gets **no dyn-cells**. `_register_entity()` short-circuits when
`_State.current_section_slug == 'general'` (set by `section()`), so no id is emitted
and nothing there is tallied. This is automatic — any `plain_header` placed in
General Updates is covered without per-call flags.

### Ability icons — missing-file fallback

`ABIL_CDN` points at the local mirror `../icons/abilities/`. When a slug's local PNG
is absent (most innate abilities have no public CDN icon), `ability()` renders the
fallback **directly as the `<img src>`** (innate → `innate_icon.png`, else
`missing.svg`) instead of a broken path patched by `onerror` — otherwise the
entity-search dropdown (which reads `img.src`) showed the wrong icon. The set of
present files is cached in `_LOCAL_ABIL_ICONS` at module load.

Confirmed-real innates without public CDN art live in
`patch/known_exceptions.py::KNOWN_INNATE_NO_CDN_ICON`. **Builders must not
silently substitute** `innate_icon.png` for any other missing slug — that
would hide an accidentally-deleted icon from `check_icons.py`. The
established three-state pattern (see `builders/aoe_increase.py`):

```
if local_png_exists:        use it
elif slug in allowlist:     emit innate_icon.png directly
else:                       raise RuntimeError — real missing file
```

## generate_patch_code_v2.py

The canonical scaffold generator (datafeed-aware):

1. Loads the cached datafeed JSON (`data/<version>_datafeed.json`) + `itemlist.json` / `herolist.json`.
2. Walks each top-level section (General → Items → Neutral Creeps → Neutral Items → Heroes) and each entity's note tree, preserving the `indent_level` hierarchy, facet subsections, aghanims markers, and info clarifications.
3. Applies text-heuristic tag inference (BUFF / NERF / REWORK / MISC / QoL / NEW / DEL) + `l=True` for cost / BAT / cooldown / manacost / cast-point keywords + canonical-phrase tags.
4. Emits Python lines like `W(li("Mana cost reduced from 100 to 80", b(100, 80, l=True)))` and writes `_generated_p_<version>_v2.py`.

The autodetector is right ~80% of the time. Tag classification, `l=True` placement, and per-level formula extraction need human review before saving as `content/p<version>.py`.

## How CSS / JS reach the HTML

`styles.css` (repo root) and `src/scripts.js` are **hand-edited source files**, shared
by every page. They are **linked, not embedded**: patch pages reference
`../styles.css?v=…` / `../src/scripts.js?v=…`, and root pages (`index.html`,
`calendar.html`, `neutral_stats.html`, …) reference them relative to root.
`patch/page.py` reads them from disk and stamps a cache-busting `?v=` asset
version — editing happens in one place, no copy is embedded.

## Stats DB

`data/stats/<version>/` holds the relevant subset of `npc_heroes.txt` and `items.txt` parsed into JSON. Coverage is from 7.33 onward (source: muk-as/DOTA2_CLIENT). Pre-7.33 patches fall back to text-tag rendering without a numeric badge.

Key fields:

- `heroes.json`: `ArmorPhysical`, `AttackDamageMin`/`Max`, `AttackRate`, `MovementSpeed`, `AttackRange`, `AttributeBaseStrength`/`Agility`/`Intelligence`, `Attribute*Gain`, `StatusHealth`/`Mana`/`HealthRegen`/`ManaRegen`.
- `items.json`: `ItemCost`, `ItemCooldown`, `AbilityManaCost`, `ItemRequirements`, `ItemRecipe`, `ItemResult`.
- `abilities.json`: neutral creep abilities only (hero abilities live elsewhere).

`bstat_h(hero, field, before_patch, delta)` resolves a base-stat change against the named patch's snapshot and renders the actual `+N%` badge instead of a generic BUFF / NERF tag.
