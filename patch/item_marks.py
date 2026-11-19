"""Marks on an item's icon for values the game scales (owner 2026-11-19, variant 2 of the mock): Item Potency (the
game's own icon, panorama status_icons/ability_effectiveness_icon) and, under it, Dormant Curio. Which values: the
item's AbilityValues entries flagged "apply_effectiveness" "1" / "apply_curio_bonus" "1" in that patch's items.txt —
nothing is guessed. The hover lists them as the game's own tooltip sentences, the scaled numbers in bold.

    from patch.item_marks import item_marks
    item_marks("Eye of Skadi", "7.42")   # '<span class="item-marks">…</span>' or ''
"""
import re

from .images import ITEM_SLUG, item_img
from .item_ability_text import _clean, _fill, _items, _values
from .loc_history import tooltip

_FLAGS = (("potency", "apply_effectiveness", "Modified by Item Potency", "../icons/stats/item_potency.png"),
          ("curio", "apply_curio_bonus", "Improved by Dormant Curio", None))


def _flagged(blk, flag):
    av = blk.get("AbilityValues")
    if not isinstance(av, dict):
        return []
    return [k.lower() for k, v in av.items() if isinstance(v, dict) and str(v.get(flag, "")).strip() == "1"]


def _sentences(desc):
    """The tooltip's sentences, each with its ability's name before it ("Cold Attack: Attacks lower …")."""
    out = []
    for part in re.split(r"(?=<h1>)", desc.replace("\\n", "\n")):
        head = re.match(r"<h1>\s*(?:Active|Passive|Toggle|Aura|Use)?\s*:?\s*([^<]*)</h1>", part)
        name = head.group(1).strip() if head else ""
        body = part[head.end():] if head else part
        for s in re.split(r"(?<=[.!?])\s+|\n+", body):
            if s.strip():
                out.append((name, s.strip()))
    return out


def _rows(slug, version, blk, keys):
    desc = tooltip(f"DOTA_Tooltip_Ability_item_{slug}_Description", version) or ""
    vals, rows, left = _values(blk), [], set(keys)
    for name, s in _sentences(desc):
        hit = [k for k in keys if re.search(rf"%{k}%", s, re.I)]
        if not hit:
            continue
        marked = re.sub(r"%(\w+)%(%%)?", lambda m: (f"<b>%{m.group(1)}%{m.group(2) or ''}</b>"
                                                     if m.group(1).lower() in hit else m.group(0)), s)
        text = _fill(marked, vals)
        if text:
            rows.append((name, _clean(text) if "<b>" not in text else re.sub(r"\s+", " ", text)))
            left -= set(hit)
    for k in sorted(left):                         # a value no sentence names: its key and number
        rows.append(("", f"{k.replace('_', ' ').capitalize()}: <b>{vals.get(k, '?')}</b>"))
    return rows


def item_marks(name, version):
    if not version:
        return ""
    slug = ITEM_SLUG.get(name, name.lower().replace(" ", "_").replace("'", ""))
    blk = _items(version).get(f"item_{slug}")
    if not isinstance(blk, dict):
        return ""
    out = ""
    for kind, flag, head, icon in _FLAGS:
        keys = _flagged(blk, flag)
        if not keys:
            continue
        rows = "".join(f'<span class="pop-li"><span class="pop-t">{f"{n}: " if n else ""}{t}</span></span>'
                       for n, t in _rows(slug, version, blk, keys))
        src = icon or item_img("Dormant Curio")
        out += (f'<span class="info-tip item-mark item-mark-{kind}" tabindex="0"><img src="{src}" alt="">'
                f'<span class="info-pop"><span class="info-pop-h">{head}</span>{rows}</span></span>')
    return f'<span class="item-marks">{out}</span>' if out else ""
