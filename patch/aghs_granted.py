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


def kind_of(slug, version="*") -> str:
    """"shard", "scepter" or "" for an ability slug; with a version, only as that patch's KV has it
    (Visage 7.41 Silent as the Grave: a Scepter ability before, innate now)."""
    return granted(version).get(slug or "", "")
