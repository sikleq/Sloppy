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
    # "1" or "true" (the game reads both; server.dll 6983, research 2026-11-19); "-1" divides instead — not marked
    return [k.lower() for k, v in av.items()
            if isinstance(v, dict) and str(v.get(flag, "")).strip().lower() in ("1", "true")]


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


_ABIL_RULES = None


def _version_key(v):
    m = re.match(r"7\.(\d+)([a-z]?)", v or "")
    return (int(m.group(1)), m.group(2)) if m else (0, "")


def ability_marks(slug, version):
    """The Item Potency mark on an ability's icon: an ability that sets the potency of attacks (Swashbuckle 60%) —
    data/rules/item_potency_abilities.json, from the code of 7.42; '' before 7.42 or for any other ability (owner
    2026-11-19: "Ставить такой значок на иконки этих способностей — да")."""
    global _ABIL_RULES
    if _ABIL_RULES is None:
        import json
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "rules",
                            "item_potency_abilities.json")
        with open(path, encoding="utf-8") as f:
            _ABIL_RULES = json.load(f)
    text = _ABIL_RULES["abilities"].get(slug or "")
    if not text or _version_key(version) < _version_key(_ABIL_RULES["since"]):
        return ""
    return (f'<span class="item-marks"><span class="info-tip item-mark item-mark-potency" tabindex="0">'
            f'<img src="{_FLAGS[0][3]}" alt=""><span class="info-pop"><span class="info-pop-h">Item Potency</span>'
            f'<span class="pop-li"><span class="pop-t">{text}</span></span></span></span></span>')


ILLUSION_POTENCY = 20     # an illusion's Item Potency unless its creator sets one (server.dll 6983, research 2026-11-19)


def _illusion_row(text):
    """The same numbers on a default illusion: value × 20 / 100 (owner 2026-11-19, Diffusal Blade's Manabreak: "нет
    строчки про то, как это работает на иллюзиях")."""
    nums = re.findall(r"<b>([-+]?\d+(?:\.\d+)?)(%?)</b>", text)
    if not nums:
        return ""
    vals = " / ".join(f"<b>{round(float(v) * ILLUSION_POTENCY / 100, 2):g}{pct}</b>" for v, pct in nums)
    return f'<span class="pop-li pop-sub"><span class="pop-t">Illusions: {vals}</span></span>'     # owner 2026-11-19


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
                       + (_illusion_row(t) if kind == "potency" else "")
                       for n, t in _rows(slug, version, blk, keys))
        src = icon or item_img("Dormant Curio")
        out += (f'<span class="info-tip item-mark item-mark-{kind}" tabindex="0"><img src="{src}" alt="">'
                f'<span class="info-pop"><span class="info-pop-h">{head}</span>{rows}</span></span>')
    return f'<span class="item-marks">{out}</span>' if out else ""
