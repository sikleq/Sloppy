"""Item stat and cost cards: properties_change(), components_change(), render_cost_card() and the items.txt stat lines they compare. Split out of patch/elements.py (audit 2026-10-26 #8)."""

import json as _json
import os as _os
import re

from .images import ITEM_CDN, ITEM_SLUG
from .state import _State, page_cache
from .elements import _PROP_TAG_CSS, _dyn_record_card, _note_cost_panel, _prop_row_text
from .cards_item_abilities import _iab_hint, _iab_note, _tone_cls


def _prop_tag(tag):
    if not tag:
        return '<span class="row-tag-empty"></span>'
    key = tag.upper()
    cls = _PROP_TAG_CSS.get(key, 'misc')
    overall = 'buff' if key in ('BUFF', 'NEW') else ('nerf' if key in ('NERF', 'DEL') else 'buff')
    return f'<span class="badge {cls}" data-tag="{key.lower()}" data-overall="{overall}">{key}</span>'


def _prop_cells(row):
    if row is None:
        return ('', '', '')
    if isinstance(row, str):
        return ('', row, '')
    if len(row) == 2:
        return (row[0], row[1], '')
    return (row[0], row[1], row[2])


# ---- Unchanged stat lines of a "before -> after" item card (owner 2026-09-27, Mage Slayer 7.38) ----
# The card must list ALL the item's stats; patch notes only name the changed ones, so the rest comes
# from the game's items.txt of the previous and this patch (data/rules/item_stat_lines.json, built by
# tools/build_item_stat_lines.py). Stat key -> (display name, is %, words that mean it in a row).
# Not listed on purpose: % attack speed and projectile speed — on items those are an active's numbers
# (Drum / Boots of Bearing Endurance, Ethereal Blade), never a passive stat line.
_STAT_LINE = {
    "magic_res": ("Magic Resistance", True, r"magic(?:al)? resist"),
    "mana_regen": ("Mana Regen", False, r"mana regen(?!\w* amp)"),
    "health_regen": ("Health Regen", False, r"(?:health|hp) regen(?!\w* amp)"),
    "damage": ("Damage", False, r"(?<!spell )(?<!block )\bdamage\b(?! block)"),
    "attack_speed": ("Attack Speed", False, r"attack speed"),
    "all_stats": ("All Attributes", False, r"all (?:attributes|stats)"),
    "strength": ("Strength", False, r"\bstrength\b"),
    "agility": ("Agility", False, r"\bagility\b"),
    "intelligence": ("Intelligence", False, r"\bintelligence\b"),
    "primary_attribute": ("Primary Attribute", False, r"primary attribute"),
    "armor": ("Armor", False, r"\barmor\b"),
    "health": ("Health", False, r"\bhealth\b(?! regen| restoration)"),
    "mana": ("Mana", False, r"\bmana\b(?! regen| cost| loss)"),
    "evasion": ("Evasion", True, r"\bevasion\b"),
    "lifesteal": ("Lifesteal", True, r"(?<!spell )\blifesteal\b(?! amp)"),
    "spell_lifesteal": ("Spell Lifesteal", True, r"spell lifesteal(?! amp)"),
    "cast_range": ("Cast Range", False, r"cast range"),
    "attack_range": ("Attack Range", False, r"attack range"),
    "cooldown_reduction": ("Cooldown Reduction", True, r"cooldown reduction"),
    "slow_res": ("Slow Resistance", True, r"slow resist"),
    "status_res": ("Status Resistance", True, r"status resist"),
    "restoration_amp": ("Health Restoration", True,
                        r"health restoration|regen and lifesteal amp|health and lifesteal amp|lifesteal and health regen amp"),
    "spell_amp": ("Spell Amplification", True, r"spell amp"),
    "mana_regen_amp": ("Mana Regen Amplification", True, r"mana regen\w* amp"),
    "spell_lifesteal_amp": ("Spell Lifesteal Amplification", True, r"spell lifesteal amp"),
    "manacost_reduction": ("Mana Cost Reduction", True, r"mana cost"),
    "aoe_bonus": ("AoE Bonus", False, r"aoe (?:bonus|radius)|area of effect"),
    "debuff_amp": ("Debuff Amplification", True, r"debuff amp"),
    "heal_amp": ("Heal Amplification", True, r"heal(?:ing)? amp"),
    "night_vision": ("Night Vision", False, r"night vision"),
    "move_speed": ("Movement Speed", False, r"move(?:ment)? speed"),
    "move_speed_pct": ("Movement Speed", True, r"move(?:ment)? speed"),
    "boots_move_speed": ("Movement Speed", False, r"move(?:ment)? speed"),
}


_ITEM_STATS = None


def _item_stats_at(slug, version):
    """{stat: value} of an item in a patch, or None when that patch has no data for it."""
    global _ITEM_STATS
    if _ITEM_STATS is None:
        try:
            with open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                                    "data", "rules", "item_stat_lines.json"), encoding="utf-8") as f:
                _ITEM_STATS = _json.load(f)
        except OSError:
            _ITEM_STATS = {"versions": [], "items": {}}
    vers = _ITEM_STATS["versions"]
    if version not in vers:
        return None
    out = None
    for first, stats in _ITEM_STATS["items"].get(slug, []):
        if vers.index(first) <= vers.index(version):
            out = stats
    return out


_ATTRS = ("strength", "agility", "intelligence")


def _plain_stats(stats):
    """items.txt snapshot without the Strength / Agility / Intelligence copies of an All Attributes bonus
    (Ethereal Blade lists both)."""
    every = stats.get("all_stats")
    return {s: x for s, x in stats.items() if not (s in _ATTRS and every is not None and x == every)}


def item_stats_pair(name, version):
    """The item's stats (items.txt) in the patch before `version` and in `version`: (before, after), or
    None when either is unknown."""
    from .meta import RELEASE_HISTORY
    order = [r["version"] for r in RELEASE_HISTORY]          # newest first
    if version not in order or order.index(version) + 1 >= len(order):
        return None
    slug = ITEM_SLUG.get(name, name.lower().replace(" ", "_").replace("'", ""))
    before = _item_stats_at(slug, order[order.index(version) + 1])
    after = _item_stats_at(slug, version)
    return (_plain_stats(before), _plain_stats(after)) if before and after else None


def _stat_named(stat, named):
    """Does the text already speak of this stat? ("+6 All Attributes" covers Strength / Agility / Intelligence)"""
    return bool(re.search(_STAT_LINE[stat][2], named)
                or (stat in _ATTRS and re.search(_STAT_LINE["all_stats"][2], named)))


def silent_stat_changes(name, version, named):
    """Stats the game's items.txt shows changed in `version` but `named` (the item's card rows and its
    "+N stat" mentions) never speaks of — the patch notes kept quiet (Gleipnir 7.38 lost +25 Damage and
    +25 Attack Speed). Lists of (stat, before, after): removed, added, changed."""
    pair = item_stats_pair(name, version)
    if not pair:
        return [], [], []
    before, after = pair
    quiet = sorted(s for s in set(before) | set(after) if s in _STAT_LINE and not _stat_named(s, named))
    removed = [(s, before[s], None) for s in quiet if s in before and s not in after]
    added = [(s, None, after[s]) for s in quiet if s in after and s not in before]
    changed = [(s, before[s], after[s]) for s in quiet if s in before and s in after and before[s] != after[s]]
    return removed, added, changed


def _card_stats(old, new):
    """(before, after, named) for the item block being rendered: its stats in the previous patch and in
    this one (items.txt), and the card's own rows as lower-case text. None when there is no data."""
    ek = _State.current_entity_key or ""
    ver = _State.current_patch_version
    if not ek.startswith("item|") or not ver:
        return None
    pair = item_stats_pair(_State.current_entity_display or "", ver)
    if not pair:
        return None
    named = " ".join(re.sub(r"<[^>]+>", " ", str(r[1])).lower()
                     for r in list(old) + list(new) if isinstance(r, (tuple, list)) and len(r) >= 2)
    return pair[0], pair[1], named


def _stat_text(stat, x):
    spec = _STAT_LINE[stat]
    return f"{'+' if x > 0 else ''}{x:g}{'%' if spec[1] else ''} {spec[0]}"


def _unchanged_stat_rows(old, new):
    """("", "+20% Magic Resistance") rows for the stats the card doesn't name and the patch didn't
    change — to be shown on BOTH sides. Empty when the item or either patch has no data."""
    data = _card_stats(old, new)
    if not data:
        return []
    before, after, named = data
    return [("", _stat_text(stat, x)) for stat, x in before.items()
            if stat in _STAT_LINE and after.get(stat) == x and not _stat_named(stat, named)]


def _prop_layout(old_rows, new_rows, same, old_extras, new_extras):
    """Owner 2026-09-27 (Mage Slayer 7.38: a blank row in the old pane before the unchanged stats):
    changed pairs first, then the unchanged stats on both sides (dimmed, tag "="), then the one-sided
    rows (DEL left / NEW right) zipped — so a shorter pane only ends earlier, never has a hole."""
    pairs, lone_o, lone_n = [], [], []
    for i, (o, n) in enumerate(zip(old_rows, new_rows)):
        ot = o[0] if isinstance(o, (tuple, list)) and o else None
        nt = n[0] if isinstance(n, (tuple, list)) and n else None
        if o is not None and n is not None and ot != "DEL" and nt != "NEW":
            pairs.append((i, o, i, n))
            continue
        if o is not None:
            lone_o.append((i, o))
        if n is not None:
            lone_n.append((i, n))
    rows = pairs + [(None, ("=",) + tuple(s[1:]), None, ("=",) + tuple(s[1:])) for s in same]
    for k in range(max(len(lone_o), len(lone_n))):
        oi, o = lone_o[k] if k < len(lone_o) else (None, None)
        ni, n = lone_n[k] if k < len(lone_n) else (None, None)
        rows.append((oi, o, ni, n))
    new_old_ex = {j: old_extras[oi] for j, (oi, _, _, _) in enumerate(rows) if oi in old_extras}
    new_new_ex = {j: new_extras[ni] for j, (_, _, ni, _) in enumerate(rows) if ni in new_extras}
    return [r[1] for r in rows], [r[3] for r in rows], new_old_ex, new_new_ex


def properties_change(old, new, old_extras=None, new_extras=None):
    old_extras = old_extras or {}
    new_extras = new_extras or {}
    n = max(len(old), len(new))
    old_rows = list(old) + [None] * (n - len(old))
    new_rows = list(new) + [None] * (n - len(new))
    same = _unchanged_stat_rows(old, new)                  # laid out by _prop_layout below
    # An untagged row the content repeats on both sides ("+35 Damage" -> "+35 Damage", Abyssal Blade
    # 7.38) is an unchanged stat too: dimmed with the others (owner 2026-09-27)
    keep, twins = [], []
    for i, (o, nw) in enumerate(zip(old_rows, new_rows)):
        if (isinstance(o, (tuple, list)) and isinstance(nw, (tuple, list)) and len(o) == 2 and len(nw) == 2
                and not o[0] and not nw[0] and o[1] == nw[1] and i not in old_extras and i not in new_extras):
            twins.append(("", o[1]))
        else:
            keep.append(i)
    if twins:
        old_extras = {keep.index(i): v for i, v in old_extras.items()}
        new_extras = {keep.index(i): v for i, v in new_extras.items()}
        old_rows, new_rows = [old_rows[i] for i in keep], [new_rows[i] for i in keep]
        same = twins + same
    # A value that CHANGED ("+10 Strength" -> "+26 Strength +160%") carries its BUFF/NERF chip
    # on the NEW side, next to the new value and its badge — content may give it on either side.
    # DEL stays on the old side (the property is gone), NEW on the new side.
    for i, (o, nw) in enumerate(zip(old_rows, new_rows)):
        if (isinstance(o, (tuple, list)) and isinstance(nw, (tuple, list)) and len(o) >= 2
                and o[0] in ("BUFF", "NERF", "REWORK", "MISC", "QoL") and not nw[0]):
            old_rows[i] = ("",) + tuple(o[1:])
            new_rows[i] = (o[0],) + tuple(nw[1:])
    _DYN_PROP_MAP = {"BUFF": "buff", "NERF": "nerf", "NEW": "new",
                     "DEL": "del", "REWORK": "rework", "SWAP": "swap", "MISC": "misc",
                     "QoL": "qol"}
    # Tally AND score every tagged property (after the normalisation above a changed value carries
    # its tag on the new side; the multiset of tags is unchanged). A changed value is scored as
    # "<Stat> bonus changed from <old> to <new>" with the new side's % badge, so priced stats land
    # on the item gold scale like the equivalent li() row; NEW/DEL properties score like NEW/DEL rows.
    for o, nw in zip(old_rows, new_rows):
        for side in (o, nw):
            if not (isinstance(side, (tuple, list)) and len(side) >= 1):
                continue
            tid = _DYN_PROP_MAP.get(side[0])
            if not tid:
                continue
            if tid in ("buff", "nerf"):
                _o = o if isinstance(o, (tuple, list)) else None
                _n = nw if isinstance(nw, (tuple, list)) else None
                _badge = _n[2] if (_n and len(_n) >= 3) else (side[2] if len(side) >= 3 else "")
                _dyn_record_card({tid}, _prop_row_text(_o, _n), _badge or "")
            else:
                _dyn_record_card({tid}, re.sub(r'<[^>]+>', ' ', side[1] if len(side) >= 2 else ""))

    def pane_cells(rows, extras):
        cells = []
        cur_row = 1
        for i, row in enumerate(rows):
            if row is None:
                cells.append(
                    f'<span class="property-row-empty" '
                    f'style="grid-row:{cur_row};grid-column:1/-1">&nbsp;</span>'
                )
            else:
                tag, text, badge = _prop_cells(row)
                if badge:
                    cells.append(
                        f'<span class="property-tag" style="grid-row:{cur_row};grid-column:1">'
                        f'{_prop_tag(tag)}</span>'
                        f'<span class="property-text" style="grid-row:{cur_row};grid-column:2">'
                        f'{text}</span>'
                        f'<span class="property-badge" style="grid-row:{cur_row};grid-column:3">'
                        f'{badge}</span>'
                    )
                else:
                    same_cls = " property-same" if tag == "=" else ""   # an unchanged stat (dimmed)
                    cells.append(
                        f'<span class="property-tag" style="grid-row:{cur_row};grid-column:1">'
                        f'{_prop_tag("" if tag == "=" else tag)}</span>'
                        f'<span class="property-text{same_cls}" style="grid-row:{cur_row};grid-column:2/-1">'
                        f'{text}</span>'
                    )
            cur_row += 1
            ex = extras.get(i, '')
            if ex:
                cells.append(
                    f'<div class="property-extra" '
                    f'style="grid-row:{cur_row};grid-column:2/-1">{ex}</div>'
                )
                cur_row += 1
        return ''.join(cells), cur_row - 1

    if same:
        old_rows, new_rows, old_extras, new_extras = _prop_layout(old_rows, new_rows, same, old_extras, new_extras)
    # the unchanged stats fill BOTH panes: a card whose only change is a removed stat still shows the
    # item's stats of this patch on the right (owner 2026-09-27, Bloodstone 7.38), not an empty space
    old_empty = (not old or all(r is None for r in old)) and not same
    new_empty = (not new or all(r is None for r in new)) and not same
    old_body, old_n = pane_cells(old_rows, old_extras)
    new_body, new_n = pane_cells(new_rows, new_extras)
    total_rows = max(old_n, new_n)

    if old_empty and not new_empty:
        return (
            f'<div class="properties-change new-only" '
            f'style="grid-template-rows:repeat({new_n},auto)">'
            f'<span class="properties-arrow" aria-hidden="true" '
            f'style="visibility:hidden">→</span>'
            f'<div class="properties-pane pane-new">{new_body}</div>'
            f'</div>'
        )
    if new_empty and not old_empty:
        return (
            f'<div class="properties-change old-only" '
            f'style="grid-template-rows:repeat({old_n},auto)">'
            f'<div class="properties-pane pane-old">{old_body}</div>'
            f'<span class="properties-arrow" aria-hidden="true" '
            f'style="visibility:hidden">→</span>'
            f'</div>'
        )

    return (
        f'<div class="properties-change" '
        f'style="grid-template-rows:repeat({total_rows},auto)">'
        f'<div class="properties-pane pane-old">{old_body}</div>'
        f'<span class="properties-arrow">→</span>'
        f'<div class="properties-pane pane-new">{new_body}</div>'
        f'</div>'
    )


def _component_cell(name, cost, mark=None):
    slug = ITEM_SLUG.get(name, name.lower().replace(' ', '_').replace("'", ''))
    if name.lower() == 'recipe':
        slug = 'recipe'
    cls = 'component'
    if mark == 'added':
        cls += ' component-added'
    elif mark == 'removed':
        cls += ' component-removed'
    return (f'<div class="{cls}">'
            f'<img src="{ITEM_CDN}{slug}.png" alt="{name}" title="{name}" loading="lazy">'
            f'<div class="component-price">{cost}</div></div>')


def _components_side(parts, recipe, total, marks):
    cells = [_component_cell(n, c, marks.get(n)) for n, c in parts]
    if recipe:
        cells.append(_component_cell(recipe[0], recipe[1]))
    body = '<span class="components-plus">+</span>'.join(cells)
    return (f'<div class="components-row">{body}</div>'
            f'<div class="components-total">= <span>{total}</span></div>')


_COST_CARDS = page_cache({})  # "<ek>|<pv>" -> components_change arguments, drawn by render_cost_card


_COST_MARKS = page_cache({})  # "<ek>|<pv>" -> {"total": dir, "recipe": dir, "note": html} from the hidden cost rows


def components_change(old, new, total_old, total_new,
                      recipe_old=None, recipe_new=None,
                      added=None, removed=None):
    _note_cost_panel(total_old, total_new)
    args = (old, new, total_old, total_new, recipe_old, recipe_new, added, removed)
    ek = _State.current_entity_key or ""
    if not ek.startswith("item|") or not _State.current_patch_version:
        return _components_html(*args)
    # drawn when the page is saved: the cost rows under it (hidden, still counted) mark it first
    key = f"{ek}|{_State.current_patch_version}"
    _COST_CARDS[key] = args
    _State.cost_card = {"ek": ek, "pv": _State.current_patch_version, "key": key,
                        "total_old": total_old, "total_new": total_new,
                        "recipe_old": recipe_old[1] if recipe_old else None,
                        "recipe_new": recipe_new[1] if recipe_new else None}
    return f"<!--COSTCARD:{key}-->"


def _in_old_order(old, new):
    """The new components in the old side's order, the added ones after (owner 2026-10-17, Guardian Greaves 7.41:
    "1775 + 1400 → 1500 + 1775" read as a cheaper Mekansm — each component stands under itself)."""
    rest = list(new)
    out = []
    for name, _cost in old:
        k = next((i for i, (n, _c) in enumerate(rest) if n == name), None)
        if k is not None:
            out.append(rest.pop(k))
    return out + rest


def _components_html(old, new, total_old, total_new, recipe_old=None, recipe_new=None,
                     added=None, removed=None, marks=None):
    new = _in_old_order(old, new)
    marks_old = {name: 'removed' for name in (removed or [])}
    marks_new = {name: 'added' for name in (added or [])}
    right = _components_side(new, recipe_new, total_new, marks_new)
    marks = marks or {}
    from .badges import b
    ro, rn = (recipe_old or (None, None))[1], (recipe_new or (None, None))[1]
    if ro and rn and ro != rn and _is_num(ro) and _is_num(rn):
        # the new recipe price coloured in its %'s shade (cheaper = green), the % on hover under a dotted line
        # (owner 2026-09-27)
        price = '<div class="component-price">'
        i = right.rfind(price)
        j = right.index("</div>", i)
        pct = b(ro, rn, l=True)
        tone = _tone_cls(pct, f'cost-{"buff" if rn < ro else "nerf"}')
        right = (right[:i] + price + f'<span class="{tone}">' + _iab_hint(right[i + len(price):j], pct)
                 + "</span>" + right[j:])
    changed = _is_num(total_old) and _is_num(total_new) and total_old != total_new
    if changed or marks.get("note"):
        tone = _tone_cls(b(total_old, total_new, l=True), f'cost-{"buff" if total_new < total_old else "nerf"}')
        cls = f' class="{tone}"' if changed else ""
        right = right.replace(f'= <span>{total_new}</span>',
                              f'= <span{cls}>{_iab_hint(str(total_new), marks.get("note", ""))}</span>', 1)
    if changed:
        # the total's change at the end of the block, on the change rows' % column (owner 2026-09-27)
        right += f'<span class="components-pct">{b(total_old, total_new, l=True)}</span>'
    return (f'<div class="components-change">'
            f'<div class="components-box components-pane">'
            f'{_components_side(old, recipe_old, total_old, marks_old)}'
            f'</div>'
            f'<span class="components-arrow">→</span>'
            f'<div class="components-box components-pane">{right}</div>'
            f'</div>')


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def render_cost_card(key):
    """The components card html (page.save_html fills <!--COSTCARD:key-->)."""
    if key not in _COST_CARDS:
        return ""
    return _components_html(*_COST_CARDS[key], marks=_COST_MARKS.get(key))


_COST_SENTENCES = (
    ("total", re.compile(r"Total [Cc]ost (?:increased|decreased) from (\d+)g? to (\d+)g?")),
    ("total_same", re.compile(r"Total [Cc]ost unchanged(?: at (\d+)g?)?")),
    ("recipe", re.compile(r"Recipe [Cc]ost (?:increased|decreased) from (\d+)g? to (\d+)g?")),
    ("recipe_same", re.compile(r"Recipe [Cc]ost unchanged(?: at (\d+)g?)?")),
    ("recipe_gone", re.compile(r"No longer requires an? (\d+) gold recipe")),
)


def _cost_sentence_ok(kind, nums, card):
    n = [int(x) for x in nums if x]
    to, tn, ro, rn = card["total_old"], card["total_new"], card["recipe_old"], card["recipe_new"]
    if kind == "total":
        return n == [to, tn]
    if kind == "total_same":
        return to == tn and all(x == tn for x in n)
    if kind == "recipe":
        return n == [ro, rn]
    if kind == "recipe_same":
        return ro == rn and all(x == rn for x in n)
    return rn is None and n == [ro]                            # recipe_gone


def _cost_covered(text, extra=""):
    """A cost row whose every number the components card above already shows (the recipe chip, the
    "= total"): hidden, still counted (owner 2026-09-27: "Total cost decreased from 2825 to 2800" ->
    the card's own % at the end of the block). Records the colours, the % and the row's note."""
    card = getattr(_State, "cost_card", None)
    if not card or (card["ek"], card["pv"]) != (_State.current_entity_key, _State.current_patch_version):
        return False
    plain = re.sub(r"<[^>]+>", " ", re.sub(r"<!--TIP-->.*?<!--/TIP-->", " ", text, flags=re.S))
    rest, kinds = plain, set()
    for kind, rx in _COST_SENTENCES:
        m = rx.search(rest)
        if not m:
            continue
        if not _cost_sentence_ok(kind, m.groups(), card):
            return False
        kinds.add(kind)
        rest = rest[:m.start()] + " " + rest[m.end():]
    # "Recipe cost unchanged at 500" with the total in its note (Solar Crest 7.41, owner 2026-10-17) counts too
    if not kinds & {"total", "recipe", "recipe_gone", "total_same", "recipe_same"}:
        return False
    rest = re.sub(r"[+\-−]\d+%", " ", rest)                   # a b() badge written into the text (Pipe 7.41)
    rest = re.sub(r"\s+", " ", rest).strip(" .,;")
    if re.search(r"\d", rest) or (rest and not re.match(r"\(?(?:change is \w+ )?due to ", rest, re.I)):
        return False                                           # something the card can't show: keep the row
    note = _iab_note(text, extra)
    if rest and not rest.startswith("("):
        note = "<br>".join(x for x in (note, rest[:1].upper() + rest[1:]) if x)
    to, tn, ro, rn = card["total_old"], card["total_new"], card["recipe_old"], card["recipe_new"]
    _COST_MARKS[card["key"]] = {
        "total": ("buff" if tn < to else "nerf") if to != tn else None,
        "recipe": ("buff" if rn < ro else "nerf") if ro and rn and ro != rn else None,
        "note": note}
    return True
