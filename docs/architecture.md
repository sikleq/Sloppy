# Architecture

## Data flow

```
data/patchnotes_english.txt   (Valve KV)
        ↓
generate_patch_code.py        (parser → Python helper calls)
        ↓
_generated_p_<version>.py     (intermediate, reviewed by hand)
        ↓
build_patch.py                (integrated by hand + CSS + JS + helpers)
        ↓
patches/<version>.html        (final site output)
```

## build_patch.py — top-to-bottom layout

| Section | Purpose |
|---|---|
| CDN constants | URLs for hero / item / ability icons |
| `HERO_SLUG` / `ITEM_SLUG` | Display-name → CDN-slug maps |
| Gradient helpers | `gradient_class()`, `b()`, `br()`, `bf()`, `t()` |
| HTML helpers | `hero_header()`, `item_header()`, `section()`, `ability()`, `li()`, `subnote()` |
| CSS / JS load | `styles.css` and `JS_TEXT` are **read from the standalone `styles.css` / `scripts.js` files on disk** at module load — they are hand-edited **source files**, NOT generated. |
| Scaffold | `W()` writer, HTML wrapper, top nav, filter chrome |
| Patch content | One section per version with calls to the helpers |
| `save_index_html` | Landing page — game "inventory book" (gothic pixel UI slots → section links). |
| `save_calendar_html` | Calendar + custom year picker + "Patch cadence" SVG-sparkline infographic. |

Running `python build_patch.py` writes: one HTML file per patch (under `patches/`),
`index.html`, `calendar.html`, `_ability_icons.txt`, and `data/site_meta.json`.
`styles.css` / `scripts.js` are **source files, not outputs** (they're read, not
written). The tables — `materials.html`, `neutral_abilities.html`, `mana_items.html` —
are built separately by `build_creeps.py` / `build_mana_items.py` (run AFTER
`build_patch.py`; see [tables.md](tables.md)).

### Ability icons — missing-file fallback

`ABIL_CDN` points at the local mirror `../icons/abilities/`. When a slug's local PNG
is absent (most innate abilities have no public CDN icon), `ability()` renders the
fallback **directly as the `<img src>`** (innate → `innate_icon.png`, else
`missing.svg`) instead of a broken path patched by `onerror` — otherwise the
entity-search dropdown (which reads `img.src`) showed the wrong icon. The set of
present files is cached in `_LOCAL_ABIL_ICONS` at module load.

## generate_patch_code.py

1. Reads `data/patchnotes_english.txt`.
2. Greps for `"DOTA_Patch_7_41c_<key>" "<value>"` lines.
3. `parse_key()` decomposes the key into entity type (hero / item / general / etc.) and target entity.
4. `parse_value_change()` tries to extract `from X to Y`, formula, range, or guesses the tag from text patterns.
5. Emits Python lines like `W(li("Mana cost reduced from 100 to 80", b(100, 80, l=True)))`.
6. Writes to `_generated_p_<version>.py`.

The autodetector is right ~80% of the time. Tag classification, `l=True` placement, and per-level formula extraction need human review before integration.

## How CSS / JS reach the HTML

`styles.css` and `scripts.js` at the repo root are **hand-edited source files**, shared
by every page. They are **linked, not embedded**: patch pages reference
`../styles.css?v=…` / `../scripts.js?v=…`, and root pages (`index.html`,
`calendar.html`, `materials.html`, …) reference `styles.css?v=…` / `scripts.js?v=…`.
`build_patch.py` reads them from disk at module load (e.g. into `JS_TEXT`) and stamps
a cache-busting `?v=` asset version — editing happens in one place, no copy is embedded.

## Stats DB

`data/stats/<version>/` holds the relevant subset of `npc_heroes.txt` and `items.txt` parsed into JSON. Coverage is from 7.33 onward (source: muk-as/DOTA2_CLIENT). Pre-7.33 patches fall back to text-tag rendering without a numeric badge.

Key fields:

- `heroes.json`: `ArmorPhysical`, `AttackDamageMin`/`Max`, `AttackRate`, `MovementSpeed`, `AttackRange`, `AttributeBaseStrength`/`Agility`/`Intelligence`, `Attribute*Gain`, `StatusHealth`/`Mana`/`HealthRegen`/`ManaRegen`.
- `items.json`: `ItemCost`, `ItemCooldown`, `AbilityManaCost`, `ItemRequirements`, `ItemRecipe`, `ItemResult`.
- `abilities.json`: neutral creep abilities only (hero abilities live elsewhere).

`bstat_h(hero, field, before_patch, delta)` resolves a base-stat change against the named patch's snapshot and renders the actual `+N%` badge instead of a generic BUFF / NERF tag.
