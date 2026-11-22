"""Which side of the map each neutral creep spawns on, from the game files (owner 2026-11-22: "Я думал мы и так знаем,
кто где" — the 7.42 page's home-jungle table and Unit Changes' Side switch were hand-kept lists).

Two game sources:
- the map: every npc_dota_neutral_spawner has a size (neutralType 0-3) and the 1-based range of make-ups it may roll
  (minSpawnType..maxSpawnType) — data/map/mapdata_<code>.json, scripts/gen/extract_map_entities.py;
- server.dll's camp table: per size, the make-ups by number (data/rules/camp_table.json, one entry per patch, read
  from the DLL with the project's IDA researcher).

A creep is on a side when a spawner of that side ("neutralcamp_good_*" Radiant, "neutralcamp_evil_*" Dire) may roll a
make-up with it. 7.42: Radiant small/medium/large 1-3, Dire 4-6, ancients 1-5 on both.
"""
from __future__ import annotations

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SIDE = {"good": "radiant", "evil": "dire"}


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def camp_table(patch):
    """{size: [[npc, …] per make-up]} of `patch` from data/rules/camp_table.json; raises when the patch is missing."""
    tables = _load(os.path.join(_ROOT, "data", "rules", "camp_table.json"))
    if patch not in tables:
        raise KeyError(f"camp_table.json has no {patch}: read server.dll's camp table for it")
    return {int(k): v for k, v in tables[patch]["tiers"].items()}


def spawners(map_code):
    """[(side, size, first, last)] of the map's neutral spawners (side "radiant" / "dire")."""
    md = _load(os.path.join(_ROOT, "data", "map", f"mapdata_{map_code}.json"))
    out = []
    for c in md["data"]["npc_dota_neutral_spawner"]:
        side = _SIDE.get(c["triggerName"].split("_")[1]) if c["triggerName"].count("_") >= 2 else None
        if side is None or not c.get("minSpawnType"):
            raise ValueError(f"mapdata_{map_code}: spawner {c['triggerName']} has no side or no spawn range — "
                             "re-run scripts/gen/extract_map_entities.py")
        out.append((side, int(c["neutralType"]), int(c["minSpawnType"]), int(c["maxSpawnType"])))
    if not out:
        raise ValueError(f"mapdata_{map_code}: no neutral spawners")
    return out


def creep_sides(patch, map_code):
    """{npc name: {"radiant", "dire"}} — every creep a spawner of the map may roll, with the sides it spawns on."""
    table = camp_table(patch)
    sides = {}
    for side, size, first, last in spawners(map_code):
        rows = table.get(size, [])
        for i in range(first, last + 1):
            if i > len(rows):
                raise ValueError(f"{patch}: a {side} size-{size} spawner rolls make-up {i}, the table has {len(rows)}")
            for npc in rows[i - 1]:
                sides.setdefault(npc, set()).add(side)
    return sides


def home_side(patch, map_code):
    """{npc: "radiant" | "dire"} — only the creeps that spawn on one side (a creep of both sides is not in it)."""
    return {npc: next(iter(s)) for npc, s in creep_sides(patch, map_code).items() if len(s) == 1}
