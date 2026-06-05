# Data format and helper API

## Valve KV format (patchnotes_english.txt)

```
"DOTA_Patch_7_41c_item_blink_1"               "Blink Dagger cooldown from 14 to 12"
"DOTA_Patch_7_41c_axe_1"                       "Base armor increased from 2 to 4"
"DOTA_Patch_7_41c_axe_axe_berserkers_call_1"  "Duration from 2.6/2.8/3/3.2 to 3/3.1/3.2/3.3"
"DOTA_Patch_7_41c_General_Roshan_Title"        "Roshan"
```

Key shape: `DOTA_Patch_<ver>_<entity_key>_<index>`.

A few key conventions:

- `_info` suffix marks a clarifying row — emit as `inline_note(...)` attached to the previous row, never as a standalone `<li>`.
- `_title` ends a section header.
- `hero_innate_<entity>_<ability>` marks innate-ability content.

## Badge helpers

### `b(old, new, l=False)` — numeric badge

```python
b(100, 80)              # 80 → 100 = +25% buff
b(100, 80, l=True)      # lower-is-better (cooldown, mana cost, BAT): 80 = buff
b([100, 110, 120],
  [110, 120, 130])      # per-skill-level values
```

Overall direction (the left BUFF/NERF tag + filter) is computed from the **max-rank** delta (last non-zero per-level value) — the late-game state players settle into — with two automatic refinements:

- **Front-loaded rescale:** if max-rank is a *small* nerf (≤12%) but the per-level deltas average to a buff, it flips to **buff** (early-level buffs outweigh an insignificant late dip). E.g. `b([15,30,45,60],[25,35,45,55])` (+67/+17/0/-8) → buff.
- **Flatten** (`b([a,b,c,d], X)` — per-level scaling collapsed to one flat value): tagged by comparing the flat value to the **old average** — **buff if `new ≥ avg(old)`** (ties → buff, since early levels still rose), nerf otherwise; `l=True` inverts. E.g. `b([4,8,12,16], 10)` (avg 10 = 10) → buff; `b([1100,1400,1700,2000], 1500)` (1500 < 1550) → nerf.

Override the result outright with `force_overall="buff"` / `"nerf"`. (Per-level % badges are never affected by the overall tag.) See `b()`'s docstring / AGENTS.md for the full rationale.

### `br(old_min, old_max, new_min, new_max, l=False)` — range badge

Compares midpoints. Use for stats expressed as a range (e.g. damage `51-57` → `52-58`).

```python
br(45, 51, 47, 53)      # midpoint comparison: 48 → 50
```

### `bf(old_fn, new_fn, formula_text, levels=None, l=False, …)` — formula badge

Returns `(trigger_html, badge_html, table_html)`. Builds an expandable per-hero-level table.

```python
trigger, badge, table = bf(
    lambda L: 10 + 2*L,
    lambda L: 8 + 2*L,
    "8% + 2% per level",
)
W(li("Max damage decreased", badge, extra=table))
```

For row-level convenience, use `li_formula(...)`:

```python
W(li_formula(
    "Max damage decreased",
    "10 + 2 per level", "8 + 2 per level",
    lambda L: 10 + 2*L,
    lambda L: 8 + 2*L,
))
```

### `t(tag)` — text-only tag

```python
t("BUFF")    # green
t("NERF")    # red
t("REWORK")  # blue
t("MISC")    # grey
t("QoL")     # yellow
t("NEW")     # purple (filters as buff)
t("DEL")     # red strikethrough (filters as nerf)
```

## HTML helpers

```python
section("Hero Updates")                  # <h2> divider
hero_header("Anti-Mage")                 # entity block with hero icon
item_header("Blink Dagger")              # entity block with item icon
ability("Mana Void")                     # <h4> ability heading
subgroup("Talents")                      # <h4> subgroup
plain_header("Roshan")                   # entity block without icon
ul_open() / ul_close()                   # wrap a changes list
li("Mana cost", b(100, 80, l=True))      # change row with badge
subnote("Available at level 6")          # supplementary note
li_formula(prefix, old_fmt, new_fmt,
           old_fn, new_fn)               # formula row with expandable table
scale_pill(text, fn, …)                  # standalone formula pill (no comparison)
ability_change(old=…, new=…, summary=…,
               tag=…)                    # 2-pane before/after swap
aghs_line(text, kind="scepter"|"shard")  # Aghanim's upgrade row inside ability_change
inline_note(text)                        # ↳ hanging note attached to a li / desc
```

## `l=True` cheat-sheet

| Always `l=True` | Never `l=True` |
|---|---|
| cooldown | damage |
| mana cost / manacost | heal |
| cast point | range |
| channel time | duration (usually) |
| gold cost | HP |
| recharge time | move speed |
| penalty | strength / agility / intelligence |
| Base Attack Time (BAT) | HP / mana / armor (as values) |

Exception: talent values like `X Cooldown Reduction`, `X Mana Cost Reduction`, `Cooldown Advance` — these are **benefit values** (bigger reduction = better) and must **not** carry `l=True`.

## `bstat_h(hero, field, before_patch, delta, l=False)`

Resolves a hero base-stat change against the named patch's snapshot in `data/stats/<before_patch>/heroes.json`. Returns the actual `+N%` badge instead of a text tag. Falls back to `t("BUFF")` / `t("NERF")` if the stat isn't in the DB.

```python
W(li(
    "Base Intelligence increased by 1",
    bstat_h("Abaddon", "AttributeBaseIntelligence", "7.41b", 1),
    extra=note_box(hero="Abaddon", field="AttributeBaseIntelligence", before_patch="7.41b"),
))
```

`note_box(...)` renders the `Previously: <patch link> (age)` correction line.

## `TAG_OVERRIDES` (generate_patch_code.py)

Manual overrides for the autodetector's tag guesses:

```python
TAG_OVERRIDES = {
    "Avatar now has a fixed duration": "NERF",
    "Aghanim's Scepter no longer makes activation faster": None,  # no badge
}
```

Add entries when the autodetector mislabels a row consistently across patches.
