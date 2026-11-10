"""Neutral enchantments on the patch pages: the 7.38 list drawn as one table (enchant_list_head, enchant_row), an
enchantment's header with its tier table before -> after (enchant_header) and the number rows that table covers
(_ench_covered), the chips of a tier box with their hover (enchant_tier_box, enchant_attr_row, souvenir_chip). Cut out
of elements.py (2026-11-07); elements imports _ench_covered back at its end."""

import html as _html
import json as _json
import os as _os
import re

from .images import ABIL_CDN, ITEM_CDN
from .state import _State
from .elements import _entity_link, _open_block, _register_entity, _removed_label
from .cards_item_abilities import _iab_hint, _iab_stems, _tone_cls


# ---- Enchantment data ----
_ATTR_ICON = {
    "str": "../icons/strength.webp",
    "agi": "../icons/agility.webp",
    "int": "../icons/intelligence.webp",
    "uni": "../icons/universal.webp",
}


_ATTR_LABEL = {
    "str": "Strength", "agi": "Agility",
    "int": "Intelligence", "uni": "Universal",
}


_ENCHANT_DESC = {
    "Alert":      {1: ["+7 Attack Speed"], 2: ["+15 Attack Speed", "+125 Bonus Night Vision"], 3: ["+23 Attack Speed", "+175 Bonus Night Vision"], 4: ["+31 Attack Speed", "+225 Bonus Night Vision", "+80 Attack Range"]},
    "Brawny":     {1: ["+110 Health"], 2: ["+150 Health", "+3 Health Regen"], 3: ["+190 Health", "+6 Health Regen"], 4: ["+230 Health", "+9 Health Regen", "+25% Slow Resistance"]},
    "Tough":      {1: ["+7 Damage"], 2: ["+10 Damage", "+4 Armor"], 3: ["+13 Damage", "+6 Armor"], 4: ["+16 Damage", "+8 Armor", "+40% Knockback Resistance"]},
    "Mystical":   {1: ["+1 Mana Regen"], 2: ["+1.75 Mana Regen", "+10% Magic Resistance"], 3: ["+2.5 Mana Regen", "+13% Magic Resistance"], 4: ["+3.25 Mana Regen", "+16% Magic Resistance", "+15% Mana Cost/Loss Reduction"]},
    "Quickened":  {1: ["+15 Movement Speed"], 2: ["+20 Movement Speed", "+100 Mana"], 3: ["+25 Movement Speed", "+160 Mana"], 4: ["+30 Movement Speed", "+220 Mana", "+15% Evasion"]},
    "Vital":      {1: ["+2.25 Health Regen"]},
    "Greedy":     {2: ["+75 GPM", "+200 Mana", "−30 Attack Damage"], 3: ["+100 GPM", "+250 Mana", "−60 Attack Damage"]},
    "Crude":      {2: ["+10% Health Restoration", "+8% BAT Reduction", "−6% Intelligence"], 3: ["+15% Health Restoration", "+12% BAT Reduction", "−6% Intelligence"], 4: ["+20% Health Restoration", "+16% BAT Reduction", "−6% Intelligence", "Also modifies incoming healing"]},
    "Nimble":     {2: ["+6% Movement Speed", "+10 Damage", "−1.5 Health Regen"], 3: ["+8% Movement Speed", "+15 Damage", "−2.25 Health Regen"], 4: ["+10% Movement Speed", "+20 Damage", "−3 Health Regen"]},
    "Keen-Eyed":  {2: ["+125 Cast Range", "+1 Mana Regen", "−10% Max Mana"], 3: ["+135 Cast Range", "+1.5 Mana Regen", "−12% Max Mana"], 4: ["+145 Cast Range", "+2 Mana Regen", "−14% Max Mana"]},
    "Titanic":    {2: ["+8% Attack Damage", "+10% Status Resistance", "−9% Attack Speed"], 3: ["+12% Attack Damage", "+12% Status Resistance", "−9% Attack Speed"], 4: ["+16% Attack Damage", "+14% Status Resistance", "−9% Attack Speed"]},
    "Timeless":   {4: ["+10% Debuff Amplification", "+8% Spell Amplification"], 5: ["+15% Debuff Amplification", "+16% Spell Amplification"]},
    "Vampiric":   {5: ["+30% Lifesteal", "+20% Spell Lifesteal", "+300 Bonus Night Vision"]},
    "Evolved":    {5: ["+40 Primary Stat", "(+24 All Attributes for Universal heroes)"]},
    "Fleetfooted":{5: ["+115 Movement Speed", "Does not stack with boots"]},
    "Hulking":    {5: ["+5% Max Health", "+1.5% Max Health Regen", "−30% Attack Speed"]},
    "Audacious":  {5: ["+100 Attack Speed", "+80 Magic Attack Damage", "+10% Incoming Damage"]},
    "Feverish":   {5: ["+15% Cooldown Reduction", "+7% Mana Cost/Loss Increase"]},
    "Manic":      {5: ["−18% Base Attack Time", "+20% Cast Speed", "−20% Vision"]},
}


_ENCHANT_TIERS = (1, 2, 3, 4, 5)


def enchant_list_head():
    """The column titles over a list of enchantments drawn as one table (owner 2026-09-28, 7.38 "List of
    Neutral Enchantments"): Tier 1 … Tier 5 above the value columns of every enchant_row below."""
    cells = "".join(f'<span class="ench-tier-h">Tier {t}</span>' for t in _ENCHANT_TIERS)
    return (_open_block("enchant-list-head")
            + f'<div class="ench-name-h">Enchantment</div><div class="ench-tiers ench-tiers-h">'
              f'<span class="ench-stat-h">Bonus</span>{cells}</div><div class="ench-dyn-h">Patches</div>')


def enchant_row(name, stats, tiers, slug=None, new=True):
    """One enchantment as a row of that table: icon + name | its bonuses, a value per tier it can be rolled at
    (an empty cell: not offered at that tier) | the patch squares. `stats` = [(label, values, negative)],
    values one per tier in `tiers` (a single value = the same at every tier; 0 = no such bonus at that tier).
    The row stays an entity block of its own — the patch squares and the enchantment's Changes page read it.
    Replaces the per-enchantment rows and the repeated "Available at Tiers 1, 2, 3, and 4"."""
    if slug is None:
        slug = name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    icon = f"{ITEM_CDN}enhancement_{slug}.png"
    eid = _register_entity("enchant", name)
    href = _entity_link("items", "enchantment " + name)
    lines = []
    for label, values, negative in stats:
        vals = list(values) if len(values) > 1 else list(values) * len(tiers)
        by_tier = dict(zip(tiers, vals))
        cells = []
        for t in _ENCHANT_TIERS:
            v = by_tier.get(t)
            if v is None:
                cells.append('<span class="ench-v ench-off"></span>')
            elif re.fullmatch(r"[+\-]?0(?:\.0+)?%?", str(v)):
                cells.append('<span class="ench-v ench-zero">—</span>')
            else:
                cells.append(f'<span class="ench-v{" ench-neg" if negative else ""}">{v}</span>')
        cls = " ench-neg" if negative else ""
        lines.append(f'<span class="ench-stat{cls}">{label}</span>{"".join(cells)}')
    tag = ' data-tag="new"' if new else ""
    # the tier titles again, shown only where the table's head row isn't (the enchantment's Changes page)
    own_head = ('<span class="ench-row-h"><span class="ench-stat-h"></span>'
                + "".join(f'<span class="ench-tier-h">Tier {t}</span>' for t in _ENCHANT_TIERS) + "</span>")
    lines.insert(0, own_head)
    return (_open_block(("is-new " if new else "") + "item-block enchant-list-row", ' data-new-tag="NEW"' if new else "")
            + f'''<div class="entity item-entity"{eid}>
  <div class="entity-icon item-icon"><a class="entity-link" href="{href}" title="All changes of {name}"><img src="{icon}" alt="{name}" loading="lazy"></a></div>
  <div class="entity-name"><a class="entity-link" href="{href}" title="All changes of {name}">{name}</a></div>
</div><div class="ench-tiers"{tag}>{"".join(lines)}</div>''')


def enchant_header(name, slug=None, new=False, removed=None):
    if slug is None:
        slug = name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    icon = f"{ITEM_CDN}enhancement_{slug}.png"
    if removed:
        type_label, extra_cls = _removed_label(removed)
        block_data_attr = ''
    elif new:
        type_text = new if isinstance(new, str) else ''
        type_label = (f' <span class="entity-new-type">{type_text}</span>'
                      if type_text else '')
        extra_cls = 'is-new'
        block_data_attr = ' data-new-tag="NEW"'
    else:
        type_label = ''
        extra_cls = ''
        block_data_attr = ''
    eid = _register_entity("enchant", name)
    href = _entity_link("items", "enchantment " + name)
    table = "" if removed else _enchant_change(name)
    return _open_block((extra_cls + ' item-block').strip(), block_data_attr) + f'''<div class="entity item-entity"{eid}>
  <div class="entity-icon item-icon"><a class="entity-link" href="{href}" title="All changes of {name}"><img src="{icon}" alt="{name}" loading="lazy"></a></div>
  <div class="entity-name"><a class="entity-link" href="{href}" title="All changes of {name}">{name}</a>{type_label}</div>
</div>''' + table


_ENCHANT_TABLES = None


def _enchant_tables():
    global _ENCHANT_TABLES
    if _ENCHANT_TABLES is None:
        try:
            with open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                                    "data", "rules", "enchant_tables.json"), encoding="utf-8") as f:
                _ENCHANT_TABLES = _json.load(f)
        except OSError:
            _ENCHANT_TABLES = {}
    return _ENCHANT_TABLES


def _ench_num(v):
    m = re.search(r"\d+(?:\.\d+)?", v or "")
    return float(m.group(0)) if m else 0.0


def _ench_cell(old, new, penalty, brand_new, added_line=False):
    """One tier's cell: the value; "was → now" coloured by what it does to the owner; a tier it has only now gold
    (a whole new penalty red: Titanic 7.41 "Now also provides -10/12/14% Attack Speed", NERF), one it lost struck in
    the DEL colour; "—" for no such bonus at that tier."""
    zero = lambda v: v is not None and _ench_num(v) == 0
    if old is None and new is None:
        return '<span class="ench-v ench-off"></span>'
    if new is not None and (brand_new or old == new or (zero(old) and zero(new))):
        return '<span class="ench-v ench-zero">—</span>' if zero(new) else f'<span class="ench-v">{new}</span>'
    if new is None or zero(new):
        if old is None or zero(old):
            return '<span class="ench-v ench-zero">—</span>'
        return f'<span class="ench-v"><span class="iab-lv iab-del">{old}</span></span>'
    if old is None or zero(old):
        tone = "nerf" if added_line and penalty else "new"
        return f'<span class="ench-v"><span class="iab-lv iab-{tone}">{new}</span></span>'
    up = _ench_num(new) > _ench_num(old)
    d = "nerf" if up == penalty else "buff"
    # the new value dotted, its % on hover / tap, in that %'s own shade — as the item cards' values (owner
    # 2026-10-17: "подчеркнуть пунктиром новые значения, а при нажатии видеть % разницы")
    from .badges import b
    pct = b(_ench_num(old), _ench_num(new), l=penalty)
    tone = _tone_cls(pct)
    value = _iab_hint(new, f'<span class="iab-tip-pct">{pct}</span>')
    return (f'<span class="ench-v ench-chg"><span class="ench-was">{old}</span><span class="ench-arrow">→</span>'
            f'<span class="iab-lv iab-{d}{" " + tone if tone else ""}">{value}</span></span>')


def _enchant_change(name):
    """An enchantment's bonuses by tier, before → after (owner 2026-10-17, 7.41: "Vital is written as a bare row… a
    table? a card?" — variant A: the 7.38 table, a changed cell "was → now" in colour). Data:
    data/rules/enchant_tables.json (scripts/gen/enchant_table.py). The number rows under it go into it
    (_ench_covered); "Now is a guaranteed option …" rows stay."""
    ent = _enchant_tables().get(_State.current_patch_version or "", {}).get(name)
    _State.ench_card = None
    if not ent or not ent["stats"]:
        return ""
    _State.ench_card = {"ek": _State.current_entity_key, "pv": _State.current_patch_version,
                        "labels": [s["label"] for s in ent["stats"]]}
    head = ('<span class="ench-row-h"><span class="ench-stat-h">Stats</span>'
            + "".join(f'<span class="ench-tier-h">Tier {t}</span>' for t in _ENCHANT_TIERS) + "</span>")
    lines = [head]
    for s in ent["stats"]:
        gone = not any(_ench_num(v) for v in s["new"].values())
        added = not ent["brand_new"] and not any(_ench_num(v) for v in s["old"].values())
        cells = "".join(_ench_cell(s["old"].get(str(t)), s["new"].get(str(t)), s["penalty"], ent["brand_new"], added)
                        for t in _ENCHANT_TIERS)
        cls = (" ench-neg" if s["penalty"] else "") + (" ench-gone" if gone else " ench-added" if added else "")
        lines.append(f'<span class="ench-stat{cls}">{s["label"]}</span>{cells}')
    return f'<div class="ench-tiers ench-change">{"".join(lines)}</div>'


def _ench_covered(text):
    """A number row of an enchantment whose table (above) shows that bonus, or a "Tiers changed …" row: hidden,
    still counted by the tag filters (like the item cards' rows)."""
    card = getattr(_State, "ench_card", None)
    if not card or (card["ek"], card["pv"]) != (_State.current_entity_key, _State.current_patch_version):
        return False
    plain = re.sub(r"<[^>]+>", " ", re.sub(r"<!--TIP-->.*?<!--/TIP-->", " ", text, flags=re.S))
    low = plain.lower()
    if "guaranteed" in low:
        return False
    if re.search(r"\btiers? changed from\b", low):
        return True
    if not re.search(r"\d", low):
        return False
    words = _iab_stems(low)
    # a short label ("GPM") has no stem: the whole label as a word (owner 2026-11-08, 7.41e Greedy "GPM Bonus
    # decreased from +75/100 to +65/90" stood as a row under the card that shows it)
    return any(_iab_stems(lab.lower()) & words or re.search(rf"\b{re.escape(lab.lower())}\b", low)
               for lab in card["labels"])


_ENCHANT_VALUES = None


def _enchant_desc(name, version):
    """{tier: lines} of an enchantment in a patch: that patch's own numbers (data/rules/enchant_values.json,
    scripts/gen/enchant_values.py — owner 2026-10-17, 7.41 Vital's hover said +2.25, its row +2), else the table."""
    global _ENCHANT_VALUES
    if _ENCHANT_VALUES is None:
        try:
            with open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                                    "data", "rules", "enchant_values.json"), encoding="utf-8") as f:
                _ENCHANT_VALUES = _json.load(f)
        except OSError:
            _ENCHANT_VALUES = {}
    own = _ENCHANT_VALUES.get(version or "", {}).get(name)
    return {int(t): lines for t, lines in own.items()} if own else _ENCHANT_DESC.get(name, {})


def _enchant_tooltip(name, tiers):
    desc = _enchant_desc(name, _State.current_patch_version)
    if isinstance(tiers, int):
        tiers = [tiers]
    parts = []
    multi = len([t for t in tiers if t in desc]) > 1
    for t in tiers:
        lines = desc.get(t)
        if not lines:
            continue
        body = "\n".join(lines)
        parts.append(f"Tier {t}\n{body}" if multi else body)
    return "\n\n".join(parts) if parts else name


def _enchant_chip(name, tiers):
    slug = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
    icon = f"{ITEM_CDN}enhancement_{slug}.png"
    tooltip = _html.escape(_enchant_tooltip(name, tiers), quote=True)
    return (f'<span class="enchant-chip" data-tooltip="{tooltip}">'
            f'<img src="{icon}" alt="{name}" loading="lazy">'
            f'<span>{name}</span></span>')


def souvenir_chip(name, slug, removed=False, tooltip=None):
    icon = f"{ABIL_CDN}{slug}.png"
    cls = "enchant-chip souvenir-chip" + (" removed" if removed else "")
    tip_attr = ''
    if tooltip:
        tip_attr = f' data-tooltip="{_html.escape(tooltip, quote=True)}"'
    return (f'<span class="{cls}"{tip_attr}>'
            f'<img src="{icon}" alt="" loading="lazy">'
            f'<span>{name}</span></span>')


def enchant_attr_row(attr, enchantments, tiers):
    if attr == "all":
        icons = ''.join(
            f'<img src="{_ATTR_ICON[a]}" alt="">' for a in ("str", "agi", "int", "uni")
        )
        label = (f'<span class="enchant-attr-icons all-attrs">{icons}</span>'
                 f'<span class="enchant-attr-name is-all">All Heroes</span>')
    else:
        label = (f'<img class="enchant-attr-ico" src="{_ATTR_ICON[attr]}" alt="">'
                 f'<span class="enchant-attr-name is-{attr}">{_ATTR_LABEL[attr]}</span>')
    chips = ''.join(_enchant_chip(e, tiers) for e in enchantments)
    return (f'<div class="enchant-attr-row">'
            f'<div class="enchant-attr-label">{label}</div>'
            f'<div class="enchant-attr-list">{chips}</div>'
            f'</div>')


def enchant_tier_box(rows, tiers):
    body = ''.join(enchant_attr_row(a, es, tiers) for a, es in rows)
    return f'<div class="enchant-attr-grid">{body}</div>'
