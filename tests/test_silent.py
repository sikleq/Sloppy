"""Тесты аналитики «тихих изменений» (builders/silent.py).

silent.py уже хорошо разложен: `diff_versions` — чистая функция
`данные → дельты`, а `render_diff_html` отдельно. Но покрытия не было.
Здесь запираем поведение чистого ядра: KV-парсер, flatten, noise/interesting
фильтры и сам diff — плюс smoke на реальных данных.
"""

from builders.silent import (
    parse_kv, _flatten, _is_noise, _interesting, diff_versions,
    load_hero_abilities,
)


# --- KV-парсер -------------------------------------------------------------

def test_parse_kv_nested():
    text = '"Root" { "a" "1" "b" { "c" "2" } }'
    assert parse_kv(text) == {"Root": {"a": "1", "b": {"c": "2"}}}


def test_parse_kv_skips_line_comments():
    text = '"Root" {\n  // комментарий\n  "a" "1"\n}'
    assert parse_kv(text) == {"Root": {"a": "1"}}


def test_parse_kv_duplicate_key_last_wins():
    text = '"Root" { "a" "1" "a" "2" }'
    assert parse_kv(text) == {"Root": {"a": "2"}}


def test_parse_kv_empty():
    assert parse_kv("") == {}


# --- flatten + noise -------------------------------------------------------

def test_flatten_nested_paths():
    d = {"Block": {"Inner": {"Cooldown": "5"}, "Range": "600"}}
    assert _flatten(d) == {"Block.Inner.Cooldown": "5", "Block.Range": "600"}


def test_flatten_drops_engine_noise():
    # FireSound содержит "sound" → инженерный шум, выкидывается.
    d = {"Mod": {"OnCreated": {"FireSound": "s.vsndevt"}, "Cooldown": "5"}}
    assert _flatten(d) == {"Mod.Cooldown": "5"}


def test_is_noise_patterns():
    assert _is_noise("Modifier.OnHit.FireSound")
    assert _is_noise("SomeParticleSystem")
    assert not _is_noise("AbilityCooldown")


# --- interesting-фильтр ----------------------------------------------------

def test_interesting_whitelist_and_av():
    assert _interesting("AbilityCooldown")
    assert _interesting("AbilityValues.damage")  # top в whitelist
    assert _interesting("av_damage.value")        # av_* всегда интересен
    assert not _interesting("SomeRandomInternalField")


def test_interesting_full_diff_env(monkeypatch):
    monkeypatch.setenv("SC_FULL_DIFF", "1")
    # При SC_FULL_DIFF=1 интересно всё.
    assert _interesting("SomeRandomInternalField")


# --- diff_versions ---------------------------------------------------------

def test_diff_versions_added_removed_changed_and_filtered():
    prev = {"npc_dota_hero_x": {
        "abil_keep":  {"AbilityCooldown": "10", "RandomNoiseField": "z"},
        "abil_gone":  {"AbilityDamage": "5"},
    }}
    curr = {"npc_dota_hero_x": {
        "abil_keep":  {"AbilityCooldown": "12", "RandomNoiseField": "q"},
        "abil_new":   {"AbilityDamage": "7"},
    }}
    diff = diff_versions(prev, curr)
    assert diff == {"npc_dota_hero_x": {
        "abil_keep": {"AbilityCooldown": ("10", "12")},   # изменено
        "abil_gone": {"AbilityDamage": ("5", None)},      # удалено
        "abil_new":  {"AbilityDamage": (None, "7")},      # добавлено
    }}
    # Неинтересное поле (RandomNoiseField) не попало в дельты.
    assert "RandomNoiseField" not in diff["npc_dota_hero_x"]["abil_keep"]


def test_diff_versions_identical_is_empty():
    data = {"npc_dota_hero_x": {"a": {"AbilityCooldown": "10"}}}
    assert diff_versions(data, data) == {}


# --- smoke на реальных данных ----------------------------------------------

def test_load_real_heroes_shape():
    data = load_hero_abilities("7.41c")
    assert len(data) > 100                       # ~127 героев
    hero = data["npc_dota_hero_abaddon"]
    assert isinstance(hero, dict) and hero        # есть способности
    # значения flat-полей — строки KV
    some_ability = next(iter(hero.values()))
    assert all(isinstance(v, str) for v in some_ability.values())


def test_diff_real_adjacent_pair_is_wellformed():
    prev = load_hero_abilities("7.41b")
    curr = load_hero_abilities("7.41c")
    diff = diff_versions(prev, curr)
    # Детерминизм + корректная форма: каждый лист — пара (old, new).
    assert diff == diff_versions(prev, curr)
    for abilities in diff.values():
        for fields in abilities.values():
            for delta in fields.values():
                assert isinstance(delta, tuple) and len(delta) == 2
                assert delta[0] != delta[1]


# --- корневые файлы: items.txt, npc_units.txt, npc_abilities.txt (2026-10-21) ------------------------------
# Некрономикон билда 6946 (цена, рецепт, статы в items.txt) Silent Changes не видела: сравнивались только heroes/.

ITEMS_OLD = '''"DOTAAbilities" { "Version" "1"
  "item_recipe_necronomicon" { "ItemCost" "2050" "ItemRequirements" { "01" "item_sobi_mask;item_sobi_mask" } }
  "item_necronomicon" { "ItemCost" "2050" "Model" "a.vmdl" "AbilityValues" { "bonus_mana_regen" "2 3 4" } }
  "item_dagon" { "ItemCost" "3050" }  "item_dagon_2" { "ItemCost" "4200" } }'''
ITEMS_NEW = '''"DOTAAbilities" { "Version" "1"
  "item_recipe_necronomicon" { "ItemCost" "2050" "ItemRequirements" { "01" "item_staff_of_wizardry" } }
  "item_necronomicon" { "ItemCost" "2700" "Model" "b.vmdl" "AbilityValues" { "bonus_intellect" "15 20 25" } }
  "item_dagon" { "ItemCost" "3000" }  "item_dagon_2" { "ItemCost" "4100" } }'''
UNITS_OLD = '"DOTAUnits" { "npc_dota_necronomicon_warrior_1" { "StatusHealth" "700" "Model" "x" "Ability1" "a" } }'
UNITS_NEW = '"DOTAUnits" { "npc_dota_necronomicon_warrior_1" { "StatusHealth" "800" "Model" "y" "Ability1" "b" } }'


def _two_patches(tmp_path, monkeypatch):
    import builders.silent as sc
    for v, items, units in (("1.00", ITEMS_OLD, UNITS_OLD), ("1.01", ITEMS_NEW, UNITS_NEW)):
        d = tmp_path / v
        d.mkdir()
        (d / "items.txt").write_text(items, encoding="utf-8")
        (d / "npc_units.txt").write_text(units, encoding="utf-8")
        (d / "npc_abilities.txt").write_text('"DOTAAbilities" { "Version" "1" }', encoding="utf-8")
    monkeypatch.setattr(sc, "DATA_DIR", tmp_path)
    return sc


def test_root_files_diff_items_and_units_without_noise(tmp_path, monkeypatch):
    sc = _two_patches(tmp_path, monkeypatch)
    sections = {title: (kind, ents) for title, kind, ents in sc.diff_root_files("1.00", "1.01")}
    assert set(sections) == {"Items", "Units"}               # no change in npc_abilities.txt -> no section
    items = sections["Items"][1]
    assert items["item_necronomicon"] == {
        "AbilityValues.bonus_intellect": (None, "15 20 25"),
        "AbilityValues.bonus_mana_regen": ("2 3 4", None),
        "ItemCost": ("2050", "2700"),                         # the model path is engine noise
    }
    assert items["item_recipe_necronomicon"] == {
        "ItemRequirements.01": ("item_sobi_mask;item_sobi_mask", "item_staff_of_wizardry")}
    assert sections["Units"][1] == {"npc_dota_necronomicon_warrior_1": {
        "Ability1": ("a", "b"), "StatusHealth": ("700", "800")}}


def test_root_files_render_as_their_own_sections_with_unambiguous_names(tmp_path, monkeypatch):
    sc = _two_patches(tmp_path, monkeypatch)
    monkeypatch.setattr(sc, "_entity_names", lambda: ({"item_necronomicon": "Necronomicon", "item_dagon": "Dagon",
                                                       "item_dagon_2": "Dagon"},
                                                      {"npc_dota_necronomicon_warrior_1": "Demonic Warrior"}))
    html = sc.render_diff_html("1.01", "1.00", {}, sc.diff_root_files("1.00", "1.01"))
    assert '<section class="sc-hero sc-group"><h2>Items</h2>' in html
    assert '<section class="sc-hero sc-group"><h2>Units</h2>' in html
    assert ">Necronomicon Recipe</h3>" in html                # recipe named after its item, as the datafeed does
    assert ">Dagon (item_dagon)</h3>" in html and ">Dagon (item_dagon_2)</h3>" in html
    assert ">Demonic Warrior</h3>" in html
    assert "No diff detected" not in html


def test_old_snapshots_without_root_files_get_no_extra_sections(tmp_path, monkeypatch):
    sc = _two_patches(tmp_path, monkeypatch)
    (tmp_path / "1.00" / "items.txt").unlink()
    titles = [t for t, _, _ in sc.diff_root_files("1.00", "1.01")]
    assert titles == ["Units"]
