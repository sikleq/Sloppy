"""A new patch must flow into the Materials pages: current values from the new game files,
history extended with the right per-patch values. Guards the ways this broke before."""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "fetch"))

from patch import meta  # noqa: E402


def test_release_history_is_newest_first():
    dates = [datetime.datetime.strptime(p["date"], "%d.%m.%Y") for p in meta.RELEASE_HISTORY]
    assert dates == sorted(dates, reverse=True)
    assert meta.PATCHES[0]["version"] == meta.RELEASE_HISTORY[0]["version"] or "filename" not in meta.RELEASE_HISTORY[0]


def test_latest_heroes_raw_matches_the_local_per_hero_kv():
    """7.41f froze at the 7.41e values because heroes_raw.json came from a stale d2vpkr commit
    (Earth Spirit / KotL / Warlock base attack speed). For the per-hero layout it is built
    from the local files — every hero field there must match heroes_raw.json."""
    from fetch_hero_history import build_from_local
    ver = meta.latest_stats_version()
    ver_dir = os.path.join(ROOT, "data", "stats", ver)
    import pathlib
    local = build_from_local(pathlib.Path(ver_dir))
    if local is None:                      # pre-7.41f layout: d2vpkr stays the source
        return
    with open(os.path.join(ver_dir, "heroes_raw.json"), encoding="utf-8") as f:
        raw = json.load(f)
    diffs = [(h, k) for h, fields in local.items() for k, v in fields.items() if raw.get(h, {}).get(k) != v]
    assert not diffs, diffs[:10]
    assert "npc_dota_hero_base" in raw


def test_mana_items_history_uses_the_int_constant_of_each_patch():
    from builders import mana_items as m
    assert m._int_const_at(m._INT_MANA_HIST, "7.37") == 11      # 7.36 – 7.38c: 11 mana per Int
    assert m._int_const_at(m._INT_MANA_HIST, "7.39") == 12
    assert m._int_const_at(m._INT_MANA_HIST, None) == m.INT_TO_MAX_MANA
    item = {"bonus_intellect": "10"}
    assert m._flat_metric(item, "mana", patch="7.37") == 110
    assert m._flat_metric(item, "mana", patch="7.41f") == 120
