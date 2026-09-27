"""An item's abilities as they were in a patch, as one-line texts for item_abilities_change():
"Passive: Empower Spell. The next Unit Target spell ... Cooldown: 6s".

Text = the game's tooltip of that patch (tools/loc_history.py, d2vpkr), numbers = that patch's items.txt
(data/stats/<v>/items.txt or the items_history kept with the weights model). Nothing is invented: a
placeholder the KV doesn't have leaves the ability out (returns None for the item).

    from tools.item_ability_text import item_abilities
    item_abilities("angels_demise", "7.37e")
"""
import html as _html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))
from builders.silent import parse_kv  # noqa: E402
from loc_history import tooltip  # noqa: E402

HIST = os.path.join(os.path.expanduser("~"), "outputs", "valve-revealed-weights-20260915", "items_history")
_KV = {}


def _kv_path(v):
    for p in (os.path.join(HERE, "data", "stats", v, "items.txt"), os.path.join(HIST, v, "items.txt")):
        if os.path.exists(p):
            return p
    return None


def _items(v):
    if v not in _KV:
        p = _kv_path(v)
        root = parse_kv(open(p, encoding="utf-8", errors="replace").read()) if p else {}
        _KV[v] = root.get("DOTAAbilities", root)
    return _KV[v]


def _num(s):
    parts = []
    for x in str(s).split():
        try:
            f = float(x)
        except ValueError:
            return None
        parts.append(f"{f:g}")
    return "/".join(parts) if parts else None


def _values(blk):
    out = {}
    av = blk.get("AbilityValues")
    if isinstance(av, dict):
        for k, v in av.items():
            n = _num(v.get("value", "") if isinstance(v, dict) else v)
            if n is not None:
                out[k.lower()] = n
    asp = blk.get("AbilitySpecial")
    if isinstance(asp, dict):
        for d in asp.values():
            if isinstance(d, dict):
                for k, v in d.items():
                    if k not in ("var_type", "LinkedSpecialBonus") and k.lower() not in out:
                        n = _num(v)
                        if n is not None:
                            out[k.lower()] = n
    return out


def _fill(text, vals):
    """%name% -> value, %name%%% -> value%; None when a placeholder has no value."""
    missing = []

    def rep(m):
        key = m.group(1).lower()
        if key not in vals:
            missing.append(key)
            return m.group(0)
        return vals[key] + ("%" if m.group(2) else "")
    out = re.sub(r"%([A-Za-z_][\w]*)%(%%)?", rep, text)
    return None if missing else out


def _clean(s):
    """Tooltip html -> one line; the tooltip's line breaks become sentence ends ("Duration: 9s. Dispel Type: ...")."""
    s = s.replace("\\n", "\n")                                   # the file's escaped line breaks
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    lines = [re.sub(r"\s+", " ", _html.unescape(x)).strip() for x in s.split("\n")]
    out = ""
    for x in (x for x in lines if x):
        out = f"{out} {x}" if not out or out[-1] in ".!?:" else f"{out}. {x}"
    return re.sub(r"\s+([.,])", r"\1", out).strip()


def _norm(texts):
    return [re.sub(r"[-+]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*%?s?", "#", t) for t in texts]


_META_SENTENCE_RE = re.compile(r"(?:Cast Range|Mana Cost|Health Cost|Cooldown|Radius)\s*:?\s*[\d./%s]+\.?|No Mana Cost\.?|"
                               r"No Cooldown\.?", re.I)


def _same_words(old, new):
    """Every ability says the same words on both sides once its header values (range, cost, cooldown, radius)
    are set aside — the game's tooltip didn't change (Block of Cheese 7.38: "Try me!" both times, only the
    250 cast range gone): a card would show two identical boxes (owner 2026-09-27), so the rows stay."""
    strip = lambda ts: sorted(re.sub(r"\s+", " ", _META_SENTENCE_RE.sub(" ", t)).strip() for t in ts)
    return strip(old) == strip(new)


_STRUCT_TAG_RE = re.compile(r't\("(NEW|DEL|REWORK)"\)')
_NOT_ABILITY_RE = re.compile(r"cycled out|removed from the game|disassembl|now is a tier|guaranteed|tier|total cost|"
                             r"recipe|^\s*cost\b|^\s*\+[\d.]+", re.I)


def insert_cards(lines, version, prev, name_to_slug):
    """Generator / backfill pass (owner 2026-09-27): after the header (and its components / stats cards) of
    every item whose ABILITY changed — a NEW / DEL / REWORK row about it — and whose tooltip text changed
    beyond numbers, insert W(item_abilities_change(old=[...], new=[...])). Items without both tooltips
    (brand-new, missing localization) are left alone. Returns the new line list."""
    out = list(lines)
    i = 0
    while i < len(out):
        m = re.match(r'(\s*)W\(item_header\("((?:[^"\\]|\\.)*)"(.*)$', out[i])
        if not m or "new=" in m.group(3):
            i += 1
            continue
        ind, name = m.group(1), json.loads('"' + m.group(2) + '"')
        slug = name_to_slug.get(name)
        j = i + 1
        while j < len(out) and not re.match(r'\s*W\((?:item_header|hero_header|unit_header|enchant_header|plain_header|section)\(', out[j]):
            j += 1
        block = out[i:j]
        if not slug or any("item_abilities_change(" in x for x in block):
            i = j
            continue
        old, new = item_abilities(slug, prev), item_abilities(slug, version)
        if old is None or new is None or not (old or new) or _norm(old) == _norm(new) or _same_words(old, new):
            i = j
            continue
        names = {re.match(r"\w+: ([^.!]+)", t).group(1).lower() for t in old + new if re.match(r"\w+: ([^.!]+)", t)}
        about = False
        stmts, cur, depth = [], "", 0                  # whole statements: an li() may span several lines
        for x in block:
            cur += x + "\n"
            depth += re.sub(r'"(?:[^"\\]|\\.)*"', '""', x).count("(") - re.sub(r'"(?:[^"\\]|\\.)*"', '""', x).count(")")
            if depth <= 0:
                stmts.append(cur)
                cur, depth = "", 0
        for x in stmts:
            if "properties_change(" in x:               # "Damage Block (passive)" removed in the stats card
                for pm in re.finditer(r'\(\s*"(?:DEL|NEW|REWORK)"\s*,\s*"((?:[^"\\]|\\.)*)"', x):
                    t = pm.group(1).lower()
                    if "(passive)" in t or "(active)" in t or any(n and n in t for n in names):
                        about = True
            if about:
                break
            tm = re.search(r'W\(li\(\s*"((?:[^"\\]|\\.)*)"', x)
            if not tm or not _STRUCT_TAG_RE.search(x) or _NOT_ABILITY_RE.search(tm.group(1)):
                continue
            t = tm.group(1).lower()
            if re.match(r"^\s*(passive|active|toggle|aura)\s*:", t) or "ability" in t or any(n and n in t for n in names):
                about = True
                break
        if not about:
            i = j
            continue
        k = i + 1                                   # after the components / stats cards and comments
        while k < j and out[k].strip().startswith(("W(auto_components_change(", "W(properties_change(",
                                                    "W(components_change(", "#")):
            depth = 0
            while k < j:
                code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', out[k])
                depth += code.count("(") - code.count(")")
                k += 1
                if depth <= 0:
                    break
        lit = lambda s: json.dumps(s, ensure_ascii=False)
        card = ([f"{ind}# abilities before -> after: the game's tooltips of each patch (tools/item_ability_text.py)",
                 f"{ind}W(item_abilities_change("]
                + [f"{ind}    old=[" + (",\n" + ind + "         ").join(lit(t) for t in old) + "],"]
                + [f"{ind}    new=[" + (",\n" + ind + "         ").join(lit(t) for t in new) + "]))"])
        card = "\n".join(card).split("\n")
        out[k:k] = card
        i = j + len(card)
    return out


def item_abilities(slug, version):
    """[one-line ability text, ...] of item_<slug> in `version`, [] when it has no ability, None when the
    tooltip or a value is missing (never guess)."""
    blk = _items(version).get(f"item_{slug}")
    desc = tooltip(f"DOTA_Tooltip_Ability_item_{slug}_Description", version)
    if not isinstance(blk, dict) or desc is None:
        return None
    vals = _values(blk)
    filled = _fill(desc, vals)
    if filled is None:
        return None
    parts = re.split(r"<h1>\s*(Active|Passive|Toggle|Aura|Use)\s*:\s*([^<]*)</h1>", filled)
    out = []
    for i in range(1, len(parts) - 2, 3):
        kind, name, body = parts[i], _clean(parts[i + 1]), _clean(parts[i + 2])
        if body and not body.endswith((".", "!")):
            body += "."
        out.append([kind, name, body])
    if not out:
        return []
    meta = []
    rng, mana, cd = (_num(blk.get(k, "")) for k in ("AbilityCastRange", "AbilityManaCost", "AbilityCooldown"))
    host = next((a for a in out if a[0] == "Active"), out[0])      # the cooldown belongs to the active
    said = host[2].lower()                                          # the tooltip may state them itself (Dagon)
    if rng and rng != "0" and "cast range" not in said:
        meta.append(f"Cast Range: {rng}.")
    if mana and mana != "0" and "mana cost" not in said:
        meta.append(f"Mana Cost: {mana}.")
    if cd and cd != "0" and "cooldown" not in said:
        meta.append(f"Cooldown: {cd}s")
    if meta:
        host[2] = (host[2] + " " + " ".join(meta)).strip()
    return [f"{k}: {n}. {b}".replace(". .", ".") for k, n, b in out]
