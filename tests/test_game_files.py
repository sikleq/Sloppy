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


def test_missing_raw_names_what_a_clone_without_the_store_lacks(tmp_path, monkeypatch):
    monkeypatch.setattr(gf, "_order", lambda: {"7.41c": 2, "7.41f": 3})
    assert gf.missing_raw("7.41f", tmp_path) == ["items.txt", "npc_abilities.txt", "npc_heroes.txt", "npc_units.txt",
                                                 "heroes/"]
    d = tmp_path / "7.41f"
    (d / "heroes").mkdir(parents=True)
    (d / "heroes" / "npc_dota_hero_axe.txt").write_text("x")
    for n in ("items.txt", "npc_abilities.txt", "npc_heroes.txt", "npc_units.txt"):
        (d / n).write_text("x")
    assert gf.missing_raw("7.41f", tmp_path) == []


def test_the_site_build_stops_with_what_to_do_when_raw_files_are_missing(monkeypatch, capsys):
    import build_site
    monkeypatch.setattr(gf, "missing_raw", lambda v: ["items.txt", "heroes/"])
    monkeypatch.setattr(build_site.sys, "argv", ["build_site.py"])
    assert build_site.main() == 2
    err = capsys.readouterr().err
    assert "missing: items.txt, heroes/" in err and "python tools/game_files.py materialize" in err


def test_a_hero_without_a_kv_file_has_an_empty_kit_not_a_crash():
    from builders import entity_changes
    assert entity_changes._hero_kit("no_such_hero_for_the_test") == []


def test_the_file_cache_follows_the_store_commit_not_just_the_version(tmp_path, monkeypatch):
    monkeypatch.setattr(gf, "CACHE", tmp_path)
    monkeypatch.setattr(gf, "versions", lambda: frozenset({"7.41e"}))
    store = {"commit": "a" * 40, "data": b"old"}
    monkeypatch.setattr(gf, "commit_of", lambda v: store["commit"])
    monkeypatch.setattr(gf, "read_bytes", lambda v, rel: store["data"])
    assert open(gf.path("7.41e", "scripts/npc/items.txt"), "rb").read() == b"old"
    store.update(commit="b" * 40, data=b"new")             # the store was rebuilt: 7.41e is another build now
    assert open(gf.path("7.41e", "scripts/npc/items.txt"), "rb").read() == b"new"
