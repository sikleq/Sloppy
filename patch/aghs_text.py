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
    """KV "100" / "+100" / "=500" / "8 10 12" / "-50%" -> "100" / "8/10/12" / "-50%"; None when not a number list."""
    parts = []
    for x in str(raw).split():
        pct = x.endswith("%")                   # "-50%": a share of the base value (7.41 Pugna's Life Drain cooldown)
        try:
            f = float(x.lstrip("+=x").rstrip("%"))
        except ValueError:
            return None
        parts.append(f"{f:g}" + ("%" if pct else ""))
    return "/".join(parts) if parts else None


def _nonzero(n):
    return any(float(x.rstrip("%")) for x in n.split("/"))


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
                # "%bonus_AbilityCooldown%" = the upgrade's own bonus to that value (7.41 Vendetta, 7.40 Infest);
                # "%shard_bonus_spell_damage%" the same (7.37 Lina's Fiery Soul)
                out["bonus_" + k.lower()] = out[f"{kind}_" + k.lower()] = _num(bonus)
        else:
            n = _num(v)
        if n is not None:
            out[k.lower()] = n
    for k, v in block.items():                       # "%AbilityCastRange%" (7.41 Side Gunner)
        if k.startswith("Ability") and isinstance(v, str) and _num(v) is not None:
            out.setdefault(k.lower(), _num(v))
    asp = block.get("AbilitySpecial")
    for d in (asp.values() if isinstance(asp, dict) else ()):
        if isinstance(d, dict):
            for k, v in d.items():
                if k not in ("var_type", "LinkedSpecialBonus") and k.lower() not in out:
                    n = _num(v)
                    if n is not None:
                        out[k.lower()] = n
    return out


_HEADER_LABELS = {"abilitycooldown": "Cooldown", "abilitymanacost": "Mana cost", "abilityhealthcost": "Health cost",
                  "abilitycastrange": "Cast range", "abilitychargerestoretime": "Charge restore time",
                  "abilitycharges": "Charges", "abilityduration": "Duration", "abilitycastpoint": "Cast point",
                  "abilitychanneltime": "Channel time"}
_SECONDS = {"abilitycooldown", "abilitychargerestoretime", "abilityduration", "abilitycastpoint", "abilitychanneltime"}


def _value_lines(block, kind, slug, version, tooltip):
    """The upgrade's own numbers as the game lists them under the description ("RADIUS: 600 (+100)"): every value the
    upgrade sets that has a label -> "Radius: +100." (a bonus on a base value keeps its sign, an upgrade-only value is
    bare; "%LABEL" = a percent)."""
    out = []
    req = "RequiresScepter" if kind == "scepter" else "RequiresShard"
    av = block.get("AbilityValues")
    for k, v in (av.items() if isinstance(av, dict) else ()):
        if not isinstance(v, dict):
            continue
        raw = next((v[b] for b in (f"special_bonus_{kind}", "special_bonus_aghanim" if kind == "scepter" else "")
                    if b and b in v), None)
        only = raw is None and str(v.get(req, "0")).strip() == "1"
        if only:
            raw = v.get("value")                # a value only the upgrade has: "RequiresScepter" (7.33 Assimilate)
        # the header values have no tooltip label of their own: "AbilityCooldown" -3 = "Cooldown: -3" (7.40 Huskar's
        # Inner Fire said "Lowers Inner Fire cooldown" with no number)
        label = (tooltip(f"DOTA_Tooltip_ability_{slug}_{k}", version) or _HEADER_LABELS.get(k.lower())
                 if raw is not None else None)
        n = _num(raw) if raw is not None else None
        if not label or n is None or not re.search(r"[A-Za-z]", label) or not _nonzero(n):
            continue                                     # "+0": the upgrade no longer sets it (Sven 7.41 armor)
        pct = label.lstrip().startswith("%")
        label = re.sub(r"^[%$+\s]+|[:\s]+$", "", label).strip().capitalize()
        base = _num(v.get("value", "")) if "value" in v else None
        signed = not only and base is not None and _nonzero(base)
        sign = "-" if str(raw).strip().startswith("-") else "+"
        val = (sign + n.lstrip("-")) if signed else n
        unit = "%" if pct else "s" if k.lower() in _SECONDS and not n.endswith("%") else ""
        out.append(f"{label}: {val}{unit}.")
    # before 7.31 ("AbilitySpecial"): a value the upgrade sets is its own entry marked "RequiresScepter" / "RequiresShard"
    # ("damage_scepter" 200, 7.08-7.30) — the game lists it bare
    asp = block.get("AbilitySpecial")
    for d in (asp.values() if isinstance(asp, dict) else ()):
        if not isinstance(d, dict) or str(d.get(req, "0")).strip() != "1":
            continue
        for k, raw in d.items():
            if k in ("var_type", "LinkedSpecialBonus", "RequiresScepter", "RequiresShard", "CalculateSpellDamageTooltip"):
                continue
            n = _num(raw)
            label = tooltip(f"DOTA_Tooltip_ability_{slug}_{k}", version)
            if not label or n is None or not re.search(r"[A-Za-z]", label) or not _nonzero(n):
                continue
            pct = label.lstrip().startswith("%")
            label = re.sub(r"^[%$+\s]+|[:\s]+$", "", label).strip().capitalize()
            out.append(f"{label}: {n}{'%' if pct else ''}.")
    return out


_DECREASE_RE = re.compile(r"\b((?:[Dd]ecreas|[Rr]educ|[Ll]ower)\w*\b[^.]*?\b(?:by|to)\s+)-(?=\d)")


_FLAGS = {"scepter": ("HasScepterUpgrade", "IsGrantedByScepter"), "shard": ("HasShardUpgrade", "IsGrantedByShard")}


def _blocks(version):
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from patch.ability_kv import _hero_blocks
    return _hero_blocks(version)


def _granted(block, kind):
    """The upgrade grants this ability: IsGrantedByShard, or an "enabled" 0 -> +1 the upgrade sets (7.41 Oracle's
    Diviner's Deck)."""
    if not isinstance(block, dict):
        return False
    if str(block.get(_FLAGS[kind][1], "0")).strip() == "1":
        return True
    av = block.get("AbilityValues")
    return any(isinstance(v, dict) and str(v.get("value", "")).strip() == "0"
               and str(v.get(f"special_bonus_{kind}", "")).strip() in ("1", "+1")
               for v in (av.values() if isinstance(av, dict) else ()))


def holders(hero, kind, version):
    """The hero's abilities the upgrade improves or grants in `version` (the game's HasShardUpgrade /
    IsGrantedByShard flags), sorted."""
    if not hero or kind not in _FLAGS:
        return []
    return sorted(s for s, b in _blocks(version).items()
                  if s.startswith(hero + "_") and isinstance(b, dict)
                  and any(str(b.get(f, "0")).strip() == "1" for f in _FLAGS[kind]))


def ability_name(slug, version):
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from tools.loc_history import tooltip
    return tooltip(f"DOTA_Tooltip_ability_{slug}", version)


def _granted_text(slug, kind, version, block):
    """An ability the upgrade grants: "Grants this ability: <its description>." (the game shows the ability itself;
    the card names it with its icon)."""
    # with the numbers the game lists under it (7.38 Treant's Eyes in the Forest: "Vision radius: 800")
    text = ability_text(slug, version, kind)
    return f"Grants this ability: {text}" if text else None


def _per_level(base, inc, pct=""):
    """"10% + 1% per level"; a value that shrinks with level: "6.9 - 0.1 per level" (7.41 Weave)."""
    sign = "-" if str(inc).startswith("-") else "+"
    return f"{base}{pct} {sign} {str(inc).lstrip('-')}{pct} per level"


def ability_text(slug, version, kind="base"):
    """An ability's own description in `version` with that patch's numbers; a value growing with hero level
    ("hero_levelup") reads "10% + 1% per level" (7.41 innates). kind: the Aghanim's upgrade that grants it, whose
    values ("special_bonus_scepter": "800") are its numbers. None when the files don't have it."""
    from tools.item_ability_text import _clean, _fill
    from tools.loc_history import tooltip
    block = _blocks(version).get(slug)
    desc = tooltip(f"DOTA_Tooltip_ability_{slug}_Description", version)
    if not isinstance(block, dict) or not desc:
        return None
    av = block.get("AbilityValues")
    grow = {k.lower(): (_num(v.get("value", "0")), _num(v["hero_levelup"]))
            for k, v in (av.items() if isinstance(av, dict) else ()) if isinstance(v, dict) and "hero_levelup" in v}

    def per_level(m):
        base, inc = grow.get(m.group(1).lower(), (None, None))
        if base is None or inc is None:
            return m.group(0)
        pct = "%" if m.group(2) else ""
        return _per_level(base, inc, pct)
    filled = _fill(re.sub(r"%([A-Za-z_]\w*)%(%%)?", per_level, desc),
                   _with_kin_values(desc, _values(block, kind), slug, kind, version))
    text = _clean(filled).replace("%%", "%") if filled is not None else ""      # "0%%" the file writes bare
    if not text:
        return None
    text += "" if text.endswith((".", "!")) else "."
    # the values the game lists under the description ("AGILITY BASE BONUS: 10% + 1%"): 7.41 Precision Aura's text
    # names no number at all
    lines = []
    asp = block.get("AbilitySpecial")
    entries = list(av.items() if isinstance(av, dict) else ())
    for d in (asp.values() if isinstance(asp, dict) else ()):          # before 7.31: "AbilitySpecial" {"01": {k: v}}
        if isinstance(d, dict):
            entries += [(k, x) for k, x in d.items() if k not in ("var_type", "LinkedSpecialBonus", "RequiresScepter",
                                                                   "RequiresShard", "CalculateSpellDamageTooltip")]
    for k, v in entries:
        label = tooltip(f"DOTA_Tooltip_ability_{slug}_{k}", version)
        n = _num((v.get("value") or v.get(f"special_bonus_{kind}", "")) if isinstance(v, dict) else v)
        if not label or not re.search(r"[A-Za-z]", label) or n is None:
            continue
        pct = "%" if label.lstrip().startswith("%") else ""
        label = re.sub(r"^[%$+\s]+|[:\s]+$", "", label).strip().capitalize()
        base, inc = grow.get(k.lower(), (None, None))
        val = _per_level(n, inc, pct) if inc else f"{n}{pct}"
        if inc or _nonzero(n):
            lines.append(f"{label}: {val}.")
    return text + ("\n" + " ".join(lines) if lines else "")


def _with_kin_values(desc, vals, slug, kind, version):
    """A placeholder the ability's own KV doesn't have, taken from another ability of the same hero when exactly one
    value is found there (7.22 Nature's Prophet's Scepter: "%treant_large_damage_bonus%" lives on Nature's Call)."""
    missing = {m.group(1).lower() for m in re.finditer(r"%([A-Za-z_]\w*)%", desc or "")} - set(vals)
    if not missing:
        return vals
    pre = slug.split("_")[0] + "_"
    found = {}
    for other, blk in _blocks(version).items():
        if other == slug or not other.startswith(pre) or not isinstance(blk, dict):
            continue
        for k, v in _values(blk, kind).items():
            if k in missing:
                found.setdefault(k, set()).add(v)
    return {**vals, **{k: next(iter(v)) for k, v in found.items() if len(v) == 1}}


def aghs_text(slug, kind, version):
    """The upgrade text of `slug` ("scepter" / "shard") in `version`: the description, then (after a line break) its
    numbers "Radius: +100. Barrier duration: 6." — or None. An ability the upgrade grants: "Grants <name>: …"."""
    if not slug or not version or kind not in _KEYS:
        return None
    from tools.item_ability_text import _clean, _fill
    from tools.loc_history import tooltip
    block = _blocks(version).get(slug)
    # "<slug>_ad_shard_description": the only key 7.30-7.31b Skywrath's Mystic Flare Shard had (Valve's own name)
    desc = next((d for d in (tooltip(f"DOTA_Tooltip_ability_{slug}_{pre}{k}", version)
                             for pre in ("", "ad_") for k in _KEYS[kind]) if d), None)
    if not desc and _granted(block, kind):
        return _granted_text(slug, kind, version, block)
    if not isinstance(block, dict) or not desc:
        return None
    filled = _fill(desc, _with_kin_values(desc, _values(block, kind), slug, kind, version))
    if filled is None:
        return None
    text = _DECREASE_RE.sub(r"\1", _clean(filled))     # "Decreases cooldown by -2s": the word says the minus
    text = re.sub(r"(\d%)s\b", r"\1", text)             # "by %abilitycooldown%s" with "-50%" -> "by 50%" (7.41 Pugna)
    if not text:
        return None
    text += "" if text.endswith((".", "!")) else "."
    values = _value_lines(block, kind, slug, version, tooltip)
    return text + ("\n" + " ".join(values) if values else "")      # the numbers: a line of their own
