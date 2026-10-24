"""tools/game_files.raw_plan: which raw game files each patch gets in data/stats/<v>/ (no store needed)."""
from tools import game_files as gf


def _fake_store(monkeypatch, heroes, root, include_list):
    monkeypatch.setattr(gf, "listing", lambda v, d: [f"scripts/npc/heroes/{h}" for h in heroes])
    monkeypatch.setattr(gf, "read_bytes", lambda v, rel: b"x" if rel.rsplit("/", 1)[1] in root + ["npc_dota_hero_base.txt"]
                        else None)
    monkeypatch.setattr(gf, "read", lambda v, rel: '#base "heroes/npc_dota_hero_axe.txt"' if include_list else '"DOTAHeroes"')
    monkeypatch.setattr(gf, "_order", lambda: {"7.34e": 0, "7.41b": 1, "7.41c": 2, "7.41f": 3})


def test_per_hero_files_only_before_the_raw_txt_era(monkeypatch):
    _fake_store(monkeypatch, ["npc_dota_hero_axe.txt", "npc_dota_hero_base.txt"], ["items.txt"], False)
    assert gf.raw_plan("7.41b") == {"heroes/npc_dota_hero_axe.txt": "scripts/npc/heroes/npc_dota_hero_axe.txt"}


def test_root_kv_files_from_7_41c_and_the_hero_base_where_npc_heroes_is_an_include_list(monkeypatch):
    _fake_store(monkeypatch, ["npc_dota_hero_axe.txt", "npc_dota_hero_base.txt"], ["items.txt", "npc_heroes.txt"], False)
    assert set(gf.raw_plan("7.41c")) == {"heroes/npc_dota_hero_axe.txt", "items.txt", "npc_heroes.txt"}
    _fake_store(monkeypatch, ["npc_dota_hero_axe.txt", "npc_dota_hero_base.txt"], ["items.txt", "npc_heroes.txt"], True)
    plan = gf.raw_plan("7.41f")
    assert plan["npc_dota_hero_base.txt"] == "scripts/npc/heroes/npc_dota_hero_base.txt"
    assert "heroes/npc_dota_hero_base.txt" not in plan
