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
ILLUSION_RUNE_POTENCY = 40     # 7.42 notes: "Illusions created by Illusion Rune now have 40% Item Potency"


def _illusion_sources(version):
    """(name, Item Potency %) of the common illusions, the strongest first: Illusion Rune, Manta Style (its
    "illusion_effectiveness" in that patch's items.txt, 35 in 7.42), a standard illusion (owner 2026-11-21: "можно
    разделить на 3 строки")."""
    av = (_items(version).get("item_manta") or {}).get("AbilityValues")
    manta = av.get("illusion_effectiveness") if isinstance(av, dict) else None
    manta = manta.get("value") if isinstance(manta, dict) else manta
    out = [("Illusion Rune", ILLUSION_RUNE_POTENCY)]
    try:
        out.append(("Manta Style", float(manta)))
    except (TypeError, ValueError):
        pass
    return out + [("Standard illusion", ILLUSION_POTENCY)]


def _illusion_row(text, version):
    """The same numbers on illusions, one row per source: value × potency / 100 (owner 2026-11-19, Diffusal Blade's
    Manabreak: "нет строчки про то, как это работает на иллюзиях"; 2026-11-21: Rune, Manta, standard)."""
    nums = re.findall(r"<b>([-+]?\d+(?:\.\d+)?)(%?)</b>", text)
    if not nums:
        return ""
    rows = []
    for name, p in _illusion_sources(version):
        vals = " / ".join(f"<b>{round(float(v) * p / 100, 2):g}{pct}</b>" for v, pct in nums)
        rows.append(f'<span class="pop-li pop-sub"><span class="pop-t">{name} ({p:g}%) = {vals}</span></span>')
    return "".join(rows)


def _curio_pct(version):
    """Dormant Curio's own bonus, its "item_potency" in that patch's items.txt (30 in 7.42); None when it has none."""
    av = (_items(version).get("item_dormant_curio") or {}).get("AbilityValues")
    if not isinstance(av, dict):
        return None
    v = av.get("item_potency")
    v = v.get("value") if isinstance(v, dict) else v
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _curio_text(text, pct):
    """Each scaled number as "50 → 65" — what Dormant Curio makes of it, only a value above 0 grows (server.dll 6983);
    owner 2026-11-19, Red Ledger's Most Wanted: the mark repeated the description instead of showing the bonus."""
    def one(m):
        v = float(m.group(1))
        if v <= 0:
            return m.group(0)
        return f'<span class="mech-old">{m.group(1)}{m.group(2)}</span> → <b>{round(v * (100 + pct) / 100, 2):g}{m.group(2)}</b>'
    return re.sub(r"<b>(\d+(?:\.\d+)?)(%?)</b>", one, text)


def item_marks(name, version):
    if not version:
        return ""
    slug = ITEM_SLUG.get(name, name.lower().replace(" ", "_").replace("'", ""))
    blk = _items(version).get(f"item_{slug}")
    if not isinstance(blk, dict):
        return ""
    out = ""
    curio = _curio_pct(version)
    for kind, flag, head, icon in _FLAGS:
        keys = _flagged(blk, flag)
        if not keys or (kind == "curio" and not curio):
            continue
        found = _rows(slug, version, blk, keys)
        if kind == "curio":
            head = f"With Dormant Curio (+{curio:g}%)"
            found = [(n, _curio_text(t, curio)) for n, t in found]
        rows = "".join(f'<span class="pop-li"><span class="pop-t">{f"{n}: " if n else ""}{t}</span></span>'
                       + (_illusion_row(t, version) if kind == "potency" else "")
                       for n, t in found)
        src = icon or item_img("Dormant Curio")
        out += (f'<span class="info-tip item-mark item-mark-{kind}" tabindex="0"><img src="{src}" alt="">'
                f'<span class="info-pop"><span class="info-pop-h">{head}</span>{rows}</span></span>')
    return f'<span class="item-marks">{out}</span>' if out else ""
