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
| `CSS` string | Entire site CSS embedded as a Python string |
| `JS_TEXT` string | Entire site JS embedded as a Python string |
| Scaffold | `W()` writer, HTML wrapper, top nav, filter chrome |
| Patch content | One section per version with calls to the helpers |

The result of running `python build_patch.py` is one HTML file per patch (under `patches/`) plus `styles.css`, `scripts.js`, `calendar.html`, and `_ability_icons.txt`.

## generate_patch_code.py

1. Reads `data/patchnotes_english.txt`.
2. Greps for `"DOTA_Patch_7_41c_<key>" "<value>"` lines.
3. `parse_key()` decomposes the key into entity type (hero / item / general / etc.) and target entity.
4. `parse_value_change()` tries to extract `from X to Y`, formula, range, or guesses the tag from text patterns.
5. Emits Python lines like `W(li("Mana cost reduced from 100 to 80", b(100, 80, l=True)))`.
6. Writes to `_generated_p_<version>.py`.

The autodetector is right ~80% of the time. Tag classification, `l=True` placement, and per-level formula extraction need human review before integration.

## How CSS / JS reach the HTML

Patch pages embed `<style>{CSS}</style>` and load `<script src="../scripts.js"></script>` from the standalone `scripts.js` file at the repo root.

The standalone `styles.css` and `scripts.js` at the repo root serve `index.html` and `calendar.html` directly; the same JS source is written from the `JS_TEXT` Python string in `build_patch.py` so editing happens in one place.

## Stats DB

`data/stats/<version>/` holds the relevant subset of `npc_heroes.txt` and `items.txt` parsed into JSON. Coverage is from 7.33 onward (source: muk-as/DOTA2_CLIENT). Pre-7.33 patches fall back to text-tag rendering without a numeric badge.

Key fields:

- `heroes.json`: `ArmorPhysical`, `AttackDamageMin`/`Max`, `AttackRate`, `MovementSpeed`, `AttackRange`, `AttributeBaseStrength`/`Agility`/`Intelligence`, `Attribute*Gain`, `StatusHealth`/`Mana`/`HealthRegen`/`ManaRegen`.
- `items.json`: `ItemCost`, `ItemCooldown`, `AbilityManaCost`, `ItemRequirements`, `ItemRecipe`, `ItemResult`.
- `abilities.json`: neutral creep abilities only (hero abilities live elsewhere).

`bstat_h(hero, field, before_patch, delta)` resolves a base-stat change against the named patch's snapshot and renders the actual `+N%` badge instead of a generic BUFF / NERF tag.
