"""An ability's Aghanim's Scepter / Shard upgrade as the game described it in one patch: the tooltip of that patch's
build (tools/loc_history.py) with that patch's numbers (data/stats/<v>/heroes, patch/ability_kv.py). Nothing is
invented: a missing tooltip or a placeholder the KV doesn't have gives None.

    from patch.aghs_text import aghs_text
    aghs_text("legion_commander_overwhelming_odds", "shard", "7.40c")
"""
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KEYS = {"scepter": ("aghanim_description", "scepter_description"), "shard": ("shard_description",)}


def _num(raw):
    """KV "100" / "+100" / "=500" / "8 10 12" -> "100" / "8/10/12"; None when not a number list."""
    parts = []
    for x in str(raw).split():
        try:
            f = float(x.lstrip("+=x"))
        except ValueError:
            return None
        parts.append(f"{f:g}")
    return "/".join(parts) if parts else None


def _values(block, kind):
    """{placeholder: value} of an ability block; a value the upgrade itself sets ("special_bonus_shard" "+100")
    wins over the base value: the upgrade's tooltip speaks of it."""
    out = {}
    av = block.get("AbilityValues")
    for k, v in (av.items() if isinstance(av, dict) else ()):
        if isinstance(v, dict):
            bonus = next((v[b] for b in (f"special_bonus_{kind}", f"special_bonus_{kind}".replace("scepter", "aghanim"))
                          if b in v), None)
            n = _num(bonus if bonus is not None else v.get("value", ""))
            if bonus is not None and _num(bonus) is not None:
                # "%bonus_AbilityCooldown%" = the upgrade's own bonus to that value (7.41 Vendetta, 7.40 Infest)
                out["bonus_" + k.lower()] = _num(bonus)
        else:
            n = _num(v)
        if n is not None:
            out[k.lower()] = n
    asp = block.get("AbilitySpecial")
    for d in (asp.values() if isinstance(asp, dict) else ()):
        if isinstance(d, dict):
            for k, v in d.items():
                if k not in ("var_type", "LinkedSpecialBonus") and k.lower() not in out:
                    n = _num(v)
                    if n is not None:
                        out[k.lower()] = n
    return out


def _value_lines(block, kind, slug, version, tooltip):
    """The upgrade's own numbers as the game lists them under the description ("RADIUS: 600 (+100)"): every value the
    upgrade sets that has a label -> "Radius: +100." (a bonus on a base value keeps its sign, an upgrade-only value is
    bare; "%LABEL" = a percent)."""
    out = []
    av = block.get("AbilityValues")
    for k, v in (av.items() if isinstance(av, dict) else ()):
        if not isinstance(v, dict):
            continue
        raw = next((v[b] for b in (f"special_bonus_{kind}", "special_bonus_aghanim" if kind == "scepter" else "")
                    if b and b in v), None)
        label = tooltip(f"DOTA_Tooltip_ability_{slug}_{k}", version) if raw is not None else None
        n = _num(raw) if raw is not None else None
        if not label or n is None or not re.search(r"[A-Za-z]", label) or not any(float(x) for x in n.split("/")):
            continue                                     # "+0": the upgrade no longer sets it (Sven 7.41 armor)
        pct = label.lstrip().startswith("%")
        label = re.sub(r"^[%$+\s]+|[:\s]+$", "", label).strip().capitalize()
        base = _num(v.get("value", "")) if "value" in v else None
        signed = base is not None and any(float(x) for x in base.split("/"))
        sign = "-" if str(raw).strip().startswith("-") else "+"
        val = (sign + n.lstrip("-")) if signed else n
        out.append(f"{label}: {val}{'%' if pct else ''}.")
    return out


_DECREASE_RE = re.compile(r"\b((?:[Dd]ecreas|[Rr]educ|[Ll]ower)\w*\b[^.]*?\b(?:by|to)\s+)-(?=\d)")


def aghs_text(slug, kind, version):
    """The upgrade text of `slug` ("scepter" / "shard") in `version`: the description, then (after a line break) its
    numbers "Radius: +100. Barrier duration: 6." — or None."""
    if not slug or not version or kind not in _KEYS:
        return None
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from patch.ability_kv import _hero_blocks
    from tools.item_ability_text import _clean, _fill
    from tools.loc_history import tooltip
    block = _hero_blocks(version).get(slug)
    desc = next((d for d in (tooltip(f"DOTA_Tooltip_ability_{slug}_{k}", version) for k in _KEYS[kind]) if d), None)
    if not isinstance(block, dict) or not desc:
        return None
    filled = _fill(desc, _values(block, kind))
    if filled is None:
        return None
    text = _DECREASE_RE.sub(r"\1", _clean(filled))     # "Decreases cooldown by -2s": the word says the minus
    if not text:
        return None
    text += "" if text.endswith((".", "!")) else "."
    values = _value_lines(block, kind, slug, version, tooltip)
    return text + ("\n" + " ".join(values) if values else "")      # the numbers: a line of their own
