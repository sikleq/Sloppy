r"""Talent slots of every hero in every patch -> data/rules/talent_slots.json (read by patch/talent_tree.py).

The game's talent tree has a left and a right twig per level 10/15/20/25. In npc_heroes.txt the
hero's first 8 "special_bonus_*" ability slots, in slot order, are the pairs of levels 10..25, and the
FIRST of each pair is the RIGHT twig (checked against Liquipedia: Axe 7.41 Ability10 "Culling Blade
Kill Buff Duration" = level 10 right). Invoker keeps them at Ability17+, so the order is used, not
fixed slot numbers.

Sources: the d2vpkr npc_heroes.txt history kept with the weights model
(~/outputs/valve-revealed-weights-20260915/heroes_history/<v>/npc_heroes.txt), and for a patch not
there yet the repo's own data/stats/<v>/heroes/npc_dota_hero_<slug>.txt (7.41f+ layout, where
npc_heroes.txt is only an include list).

Each talent also gets HINT words from the KV of its own patch: the display name of the ability whose
values the talent changes and the value's key ("Shrapnel slow movement speed"). Today's tooltip of a
reused slug can mean something else (sniper_5 was Shrapnel Slow in 7.26c, Take Aim range now), the
ability link of that patch does not.

Stored compactly: per hero, [version, [r10, l10, ... l25], [hint, ...]] only when something changes.
Usage: python tools/build_talent_slots.py
"""
import bisect
import json
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(os.path.expanduser("~"), "outputs", "valve-revealed-weights-20260915", "heroes_history")
STATS = os.path.join(HERE, "data", "stats")
OUT = os.path.join(HERE, "data", "rules", "talent_slots.json")

_HERO_HEAD = re.compile(r'^\t"npc_dota_hero_([a-z0-9_]+)"\s*$', re.M)
_SLOT = re.compile(r'^\t\t"Ability(\d+)"\s+"(special_bonus_[a-z0-9_]+)"', re.M)


def _talents(block):
    """The first 8 talent slugs of one hero block, by slot number (facet bonuses skipped)."""
    slots = sorted((int(n), s.lower()) for n, s in _SLOT.findall(block) if not s.startswith("special_bonus_facet"))
    return [s for _, s in slots[:8]] if len(slots) >= 8 else None


def from_npc_heroes(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    heads = list(_HERO_HEAD.finditer(text))
    out = {}
    for i, m in enumerate(heads):
        block = text[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        t = _talents(block)
        if t and m.group(1) != "base":
            out[m.group(1)] = t
    return out


def from_hero_files(folder):
    out = {}
    for f in os.listdir(folder):
        m = re.match(r"npc_dota_hero_([a-z0-9_]+)\.txt$", f)
        if not m:
            continue
        text = open(os.path.join(folder, f), encoding="utf-8", errors="replace").read()
        hm = re.search(rf'^\t"npc_dota_hero_{m.group(1)}"\s*$', text, re.M)
        t = _talents(text[hm.end():]) if hm else None
        if t:
            out[m.group(1)] = t
    return out


ABIL_HIST = os.path.join(os.path.dirname(HIST), "abilities_history")
_META_KEYS = {"var_type", "value", "linkedspecialbonus", "linkedspecialbonusfield", "linkedspecialbonusoperation",
              "calculatespelldamagetooltip", "requiresscepter", "requiresshard", "ad_linked_abilities",
              "dynamicvalue", "levelkey", "affected_by_aoe_increase"}
_NAME_RE = re.compile(r'"DOTA_Tooltip_ability_([a-z0-9_]+)"\s*"([^"]*)"', re.I)
_names = None


def _ability_names():
    global _names
    if _names is None:
        text = open(os.path.join(HERE, "data", "abilities_english.txt"), encoding="utf-8", errors="replace").read()
        _names = {k.lower(): v for k, v in _NAME_RE.findall(text) if not k.lower().startswith("special_bonus")}
    return _names


def talent_hints(texts):
    """slug -> hint words (ability display name + value keys) from the KV texts of one patch."""
    names = _ability_names()
    hints = {}
    for text in texts:
        heads = [(m.start(), m.group(1)) for m in re.finditer(r'^\s*"([a-z0-9_]+)"\s*\n\s*\{', text, re.M)
                 if m.group(1) in names]
        pos_list = [p for p, _ in heads]
        for m in re.finditer(r'"(special_bonus_[a-z0-9_]+)"', text):
            line_start = text.rfind("\n", 0, m.start()) + 1
            if re.match(r'\s*"(?:Ability)?\d+"', text[line_start:m.start()]):   # slot lists, bot builds
                continue
            if re.match(r'\s*\{', text[m.end():m.end() + 40]):          # the talent's own definition
                continue
            i = bisect.bisect_right(pos_list, m.start()) - 1
            if i < 0:
                continue
            owner = heads[i][1]
            body = text[heads[i][0]: m.start()]
            if body.count("{") <= body.count("}"):                       # the owner block already ended
                continue
            brace = text.rfind("{", heads[i][0], m.start())
            seg = text[brace + 1: m.start()] if brace >= 0 else ""
            keys = [k for k in re.findall(r'^\s*"([a-z_]+)"[ \t]+"', seg, re.M) if k.lower() not in _META_KEYS]
            head = re.search(r'"([a-z_]+)"\s*$', text[heads[i][0]: brace].rstrip()) if brace > 0 else None
            if head and head.group(1) != owner:
                keys.append(head.group(1))
            words = [names[owner]] + [k.replace("_", " ") for k in keys]
            slug = m.group(1).lower()
            if slug not in hints:
                hints[slug] = " ".join(words)
    return hints


def _kv_texts(v):
    out = []
    for p in (os.path.join(ABIL_HIST, v, "npc_abilities.txt"), os.path.join(STATS, v, "npc_abilities.txt")):
        if os.path.exists(p):
            out.append(open(p, encoding="utf-8", errors="replace").read())
            break
    own = os.path.join(STATS, v, "heroes")
    if os.path.isdir(own):
        out += [open(os.path.join(own, f), encoding="utf-8", errors="replace").read() for f in os.listdir(own)]
    return out


def main():
    versions = sorted(v for v in os.listdir(STATS) if os.path.isdir(os.path.join(STATS, v)))
    per_version = {}
    for v in versions:
        hist = os.path.join(HIST, v, "npc_heroes.txt")
        own = os.path.join(STATS, v, "heroes")
        if os.path.exists(hist):
            per_version[v] = from_npc_heroes(hist)
        elif os.path.isdir(own):
            per_version[v] = from_hero_files(own)
    heroes = {}
    for v in versions:
        if v not in per_version:
            continue
        hints = talent_hints(_kv_texts(v))
        for h, t in per_version[v].items():
            hint = [hints.get(s, "") for s in t]
            runs = heroes.setdefault(h, [])
            if not runs or runs[-1][1] != t or runs[-1][2] != hint:
                runs.append([v, t, hint])
    doc = {"_doc": "Per hero: [first version, [r10, l10, r15, l15, r20, l20, r25, l25], [hint words per talent]] "
                   "whenever something changes. Built by tools/build_talent_slots.py.",
           "versions": [v for v in versions if v in per_version], "heroes": heroes}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(per_version)} versions, {len(heroes)} heroes, {os.path.getsize(OUT):,} bytes")


if __name__ == "__main__":
    main()
