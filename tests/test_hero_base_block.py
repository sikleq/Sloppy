"""Every hero inherits the engine defaults of npc_dota_hero_base (120 HP, 75 mana, 25% magic resist, ...).
From 7.41f the slim heroes.json has no base block; Hero Stats / Hero Lab must take it from heroes_raw.json,
not from the hand-typed _FIELD_DEFAULTS — or a new base value never reaches the pages."""
import json

from builders import heroes_stats as hs


def _snaps(version):
    snap = json.loads((hs.STATS_DIR / version / "heroes.json").read_text(encoding="utf-8"))
    snaps, raws = {version: snap}, {version: hs._load_raw_heroes(version)}
    hs._inject_hero_base(snaps, raws)
    return snaps[version], raws[version]


def test_latest_snapshot_gets_the_games_base_block():
    latest = hs._versions()[-1]
    snap, raw = _snaps(latest)
    base = raw.get("npc_dota_hero_base") or {}
    assert base, f"heroes_raw.json of {latest} has no npc_dota_hero_base"
    missing = [k for k in hs._FIELD_DEFAULTS if k not in snap["npc_dota_hero_base"]]
    assert not missing, f"base block of {latest} lacks {missing}: Hero Stats would use typed-in defaults"


def test_base_values_reach_a_hero_without_its_own_field():
    latest = hs._versions()[-1]
    snap, raw = _snaps(latest)
    base = raw["npc_dota_hero_base"]
    assert "StatusHealth" not in snap["npc_dota_hero_axe"]
    assert hs._field(snap, "npc_dota_hero_axe", "StatusHealth") == float(base["StatusHealth"])
    assert hs._field(snap, "npc_dota_hero_axe", "StatusMana") == float(base["StatusMana"])


def test_injection_follows_a_changed_base_value():
    snaps = {"9.99": {"npc_dota_hero_axe": {}}}
    raws = {"9.99": {"npc_dota_hero_base": {"StatusHealth": "140", "Model": "x"}}}
    hs._inject_hero_base(snaps, raws)
    assert hs._field(snaps["9.99"], "npc_dota_hero_axe", "StatusHealth") == 140.0
    assert "Model" not in snaps["9.99"]["npc_dota_hero_base"]
