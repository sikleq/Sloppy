"""Тесты аналитики «тихих изменений» (builders/silent.py).

silent.py уже хорошо разложен: `diff_versions` — чистая функция
`данные → дельты`, а `render_diff_html` отдельно. Но покрытия не было.
Здесь запираем поведение чистого ядра: KV-парсер, flatten, noise/interesting
фильтры и сам diff — плюс smoke на реальных данных.
"""
import pytest

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
