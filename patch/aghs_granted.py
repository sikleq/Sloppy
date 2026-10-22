"""Abilities that Aghanim's Shard / Scepter GRANT (KV "IsGrantedByShard" / "IsGrantedByScepter" "1").

Their change rows are Aghanim rows even when the text never says "Aghanim's Shard" (Medusa 7.38
"Cold Blooded: The single-target Mystic Snake now always turns the enemy into stone for 1s" — a Shard
ability; owner 2026-09-26). Read from the per-hero KV snapshots in data/stats/<version>/heroes/ (7.34e on);
older patches keep only slim JSON there, so their flags come from data/rules/aghs_granted_old.json, built by
tools/build_aghs_granted_old.py from the full npc_abilities.txt of each patch (owner 2026-10-22: 7.08 had none).
"""
import glob
import json
import os
import re

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BLOCK_RE = re.compile(r'(?m)^\s*"([a-z0-9_]+)"\s*$')
_GRANT_RE = re.compile(r'"IsGrantedBy(Shard|Scepter)"\s+"1"')
OLD_PATH = os.path.join(_HERE, "data", "rules", "aghs_granted_old.json")


def _braced(text, i):
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i:j]
    return text[i:]


def scan(text) -> tuple:
    """({slug: "shard" | "scepter"}, {hidden one-level non-innate slugs}) of one KV text, comments ignored.
    Hidden + one level + not innate is how a granted ability looks (Centaur's Hitch A Ride lost its
    IsGrantedByScepter after 7.35 but is still the Scepter's)."""
    text = "\n".join(line.split("//")[0] for line in text.splitlines())
    grants, hidden = {}, set()
    for m in _BLOCK_RE.finditer(text):
        if not text[m.end():].lstrip().startswith("{"):
            continue
        body = _braced(text, text.index("{", m.end()))
        if '"AbilityBehavior"' not in body:
            continue                                 # a hero, unit or value block, not an ability
        g = _GRANT_RE.search(body)
        if g:
            grants[m.group(1)] = g.group(1).lower()
        if ("DOTA_ABILITY_BEHAVIOR_HIDDEN" in body and re.search(r'"MaxLevel"\s+"1"', body)
                and not re.search(r'"Innate"\s+"1"', body)):
            hidden.add(m.group(1))
    return grants, hidden


_OLD = None
_DATA: dict = {}


def _old():
    global _OLD
    if _OLD is None:
        _OLD = {}
        if os.path.exists(OLD_PATH):
            with open(OLD_PATH, encoding="utf-8") as fh:
                _OLD = json.load(fh)["versions"]
    return _OLD


def _data(version):
    """(grants, hidden) of one patch, or None when there is no data for it."""
    if version not in _DATA:
        files = glob.glob(os.path.join(_HERE, "data", "stats", version, "heroes", "npc_dota_hero_*.txt"))
        if files:
            grants, hidden = {}, set()
            for f in files:
                with open(f, encoding="utf-8", errors="replace") as fh:
                    g, h = scan(fh.read())
                grants.update(g)
                hidden |= h
            _DATA[version] = (grants, hidden)
        elif version in _old():
            rec = _old()[version]
            _DATA[version] = (rec["granted"], set(rec["hidden_one_level"]))
        else:
            _DATA[version] = None
    return _DATA[version]


def _versions():
    stats = {d for d in os.listdir(os.path.join(_HERE, "data", "stats"))
             if os.path.isdir(os.path.join(_HERE, "data", "stats", d, "heroes"))}
    return stats | set(_old())


_ANY: dict = {}


def granted(version="*") -> dict:
    """{slug: "shard" | "scepter"}: in any patch, or only in `version`'s."""
    if version != "*":
        d = _data(version)
        return d[0] if d else {}
    if not _ANY:
        for v in _versions():
            for slug, kind in (_data(v) or ({}, set()))[0].items():
                _ANY.setdefault(slug, kind)
        _ANY.setdefault("", "")                      # computed, even when empty
    return _ANY


def has_snapshot(version) -> bool:
    return bool(version) and _data(version) is not None


def kind_of(slug, version="*") -> str:
    """"shard", "scepter" or "" for an ability slug; with a version, as that patch's KV has it (Visage 7.41
    Silent as the Grave: a Scepter ability before, innate now; Jakiro's Liquid Ice: Shard in 7.34e–7.35d only).
    A patch with no data answers as any patch did. A hidden one-level ability that some patch granted stays
    granted though its flag is gone (Hitch A Ride), and so does one the patch removed."""
    if version != "*" and not has_snapshot(version):
        version = "*"
    kind = granted(version).get(slug or "", "")
    if not kind and version != "*" and (slug in _data(version)[1] or slug not in _present(version)):
        kind = granted().get(slug, "")           # flag gone, ability the same — or the patch removed it
    return kind


_PRESENT: dict = {}


def _present(version) -> set:
    """Abilities in some hero's slots (heroes.json AbilityN) of that snapshot: one a patch REMOVED keeps the stripe
    of what it was (7.40 Counterspell Ally "Ability removed" — Valve left its block in the file, without the flag)."""
    if version not in _PRESENT:
        names = set()
        p = os.path.join(_HERE, "data", "stats", version, "heroes.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                for rec in json.load(fh).values():
                    names |= {v for k, v in rec.items() if re.fullmatch(r"Ability\d+", k) and isinstance(v, str)}
        _PRESENT[version] = names
    return _PRESENT[version]
