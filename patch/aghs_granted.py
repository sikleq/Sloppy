"""Abilities that Aghanim's Shard / Scepter GRANT (KV "IsGrantedByShard" / "IsGrantedByScepter" "1").

Their change rows are Aghanim rows even when the text never says "Aghanim's Shard" (Medusa 7.38
"Cold Blooded: The single-target Mystic Snake now always turns the enemy into stone for 1s" — a Shard
ability; owner 2026-09-26). Read once from every per-hero KV snapshot in data/stats/<version>/heroes/,
comments ignored, so an ability granted in any patch counts.
"""
import glob
import os
import re

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BLOCK_RE = re.compile(r'(?m)^\s*"([a-z0-9_]+)"\s*$')
_GRANT_RE = re.compile(r'"IsGrantedBy(Shard|Scepter)"\s+"1"')
_CACHE: dict = {}


_BY_VERSION: dict = {}


def granted(version="*") -> dict:
    """{slug: "shard" | "scepter"}: in any snapshot, or only in `version`'s."""
    cache = _CACHE if version == "*" else _BY_VERSION.setdefault(version, {})
    if cache:
        return cache
    for f in glob.glob(os.path.join(_HERE, "data", "stats", version, "heroes", "npc_dota_hero_*.txt")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            text = "\n".join(line.split("//")[0] for line in fh)
        heads = list(_BLOCK_RE.finditer(text))
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
            g = _GRANT_RE.search(text, m.end(), end)
            if g:
                cache[m.group(1)] = g.group(1).lower()
    cache.setdefault("", "")                     # computed, even when empty
    return cache


_HIDDEN_ONE_LEVEL: dict = {}


def _hidden_one_level(version) -> set:
    """Abilities of that snapshot that are hidden, have one level and are not innate — how a granted ability
    looks. Centaur's Hitch A Ride lost its IsGrantedByScepter after 7.35 but is still the Scepter's."""
    if version not in _HIDDEN_ONE_LEVEL:
        ever = set(granted()) - {""}                 # only abilities some patch granted can qualify
        out = set()
        for f in glob.glob(os.path.join(_HERE, "data", "stats", version, "heroes", "npc_dota_hero_*.txt")):
            with open(f, encoding="utf-8", errors="replace") as fh:
                text = "\n".join(line.split("//")[0] for line in fh)
            for m in _BLOCK_RE.finditer(text):
                if m.group(1) not in ever or not text[m.end():].lstrip().startswith("{"):
                    continue
                body = _braced(text, text.index("{", m.end()))
                if ("DOTA_ABILITY_BEHAVIOR_HIDDEN" in body and re.search(r'"MaxLevel"\s+"1"', body)
                        and not re.search(r'"Innate"\s+"1"', body)):
                    out.add(m.group(1))
        _HIDDEN_ONE_LEVEL[version] = out
    return _HIDDEN_ONE_LEVEL[version]


def _braced(text, i):
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i:j]
    return text[i:]


def has_snapshot(version) -> bool:
    return bool(version) and os.path.isdir(os.path.join(_HERE, "data", "stats", version, "heroes"))


def kind_of(slug, version="*") -> str:
    """"shard", "scepter" or "" for an ability slug; with a version, as that patch's KV has it (Visage 7.41
    Silent as the Grave: a Scepter ability before, innate now; Jakiro's Liquid Ice: Shard in 7.34e–7.35d only).
    A patch with no snapshot (7.08) answers as any patch did. A hidden one-level ability that some patch granted
    stays granted though its flag is gone (Hitch A Ride)."""
    if version != "*" and not has_snapshot(version):
        version = "*"
    kind = granted(version).get(slug or "", "")
    if not kind and version != "*" and (slug in _hidden_one_level(version) or slug not in _present(version)):
        kind = granted().get(slug, "")           # flag gone, ability the same — or the patch removed it
    return kind


_PRESENT: dict = {}


def _present(version) -> set:
    """Abilities in some hero's slots (heroes.json AbilityN) of that snapshot: one a patch REMOVED keeps the stripe
    of what it was (7.40 Counterspell Ally "Ability removed" — Valve left its block in the file, without the flag)."""
    if version not in _PRESENT:
        import json
        names = set()
        p = os.path.join(_HERE, "data", "stats", version, "heroes.json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                for rec in json.load(fh).values():
                    names |= {v for k, v in rec.items() if re.fullmatch(r"Ability\d+", k) and isinstance(v, str)}
        _PRESENT[version] = names
    return _PRESENT[version]
