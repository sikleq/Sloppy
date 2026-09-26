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


def granted() -> dict:
    """{slug: "shard" | "scepter"}."""
    if _CACHE:
        return _CACHE
    for f in glob.glob(os.path.join(_HERE, "data", "stats", "*", "heroes", "npc_dota_hero_*.txt")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            text = "\n".join(line.split("//")[0] for line in fh)
        heads = list(_BLOCK_RE.finditer(text))
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
            g = _GRANT_RE.search(text, m.end(), end)
            if g:
                _CACHE[m.group(1)] = g.group(1).lower()
    _CACHE.setdefault("", "")                    # computed, even when empty
    return _CACHE


def kind_of(slug) -> str:
    """"shard", "scepter" or "" for an ability slug."""
    return granted().get(slug or "", "")
