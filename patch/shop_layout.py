"""The shop as the game lays it out — one source for Item Changes and the Hero Lab picker (owner 2026-11-23: "брать из
игры так, как там (порядок) и автоматически при выходе патча определять, где что снова стоит").

- data/shops.txt (scripts/shops.txt of the game): every shop category's items in their in-game order;
- data/neutral_items.txt (scripts/npc/neutral_items.txt): each neutral tier's unlock time and its items, pool by pool.
Both are written by scripts/fetch/extract_shops.py, a step of tools/new_patch.py ("shops").
"""
from __future__ import annotations

import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# shops.txt section -> the category name the site shows, in the shop's own order (Basics, then Upgrades)
CATEGORIES = [
    ("consumables", "Consumables"), ("attributes", "Attributes"), ("weapons_armor", "Equipment"),
    ("misc", "Miscellaneous"), ("secretshop", "Secret Shop"),
    ("basics", "Accessories"), ("support", "Support"), ("magics", "Magical"),
    ("defense", "Armor"), ("weapons", "Weapons"), ("artifacts", "Armaments"),
]


def _read(name):
    with open(os.path.join(_ROOT, "data", name), encoding="utf-8") as f:
        return f.read()


def shop_order():
    """{category name: [item slug without "item_", in the game's order]} — raises when shops.txt has none."""
    want = dict(CATEGORIES)
    out, cur = {}, None
    for ln in _read("shops.txt").splitlines():
        mi = re.match(r'^\s*"item"\s*"item_([a-z0-9_]+)"', ln)
        if mi:
            if cur in want:
                out.setdefault(want[cur], []).append(mi.group(1))
            continue
        ms = re.match(r'^\s*"([a-z0-9_]+)"\s*(?://.*)?$', ln)
        if ms:
            cur = ms.group(1)
    if not out:
        raise ValueError("data/shops.txt: no shop categories read")
    return out


def neutral_tiers():
    """{tier number: {"time": "30:00", "items": [slug, …]}} — the items in the order of their pools (pool_a, pool_b, …),
    as the game's shop lists them; enchantments are not here."""
    text = _read("neutral_items.txt")
    block = text[text.index('"neutral_tiers"'):]
    out = {}
    for m in re.finditer(r'^\t\t"(\d+)"\s*\n\t\t\{(.*?)^\t\t\}', block, re.S | re.M):
        body = m.group(2)
        time = re.search(r'"start_time"\s*"([0-9:]+)"', body)
        pools = body.split('"enhancements"')[0]
        items = re.findall(r'"item_([a-z0-9_]+)"\s*"1"', pools)
        out[int(m.group(1))] = {"time": time.group(1) if time else "", "items": items}
    if not out or not all(t["items"] and t["time"] for t in out.values()):
        raise ValueError("data/neutral_items.txt: a neutral tier without its time or items")
    return out
