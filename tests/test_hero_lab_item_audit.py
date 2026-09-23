"""Regression coverage from the 7.41f Hero Lab item audit.

Each test pins one CLASS of bug found by diffing Hero Lab item data against
the Valve KV (data/stats/<ver>/items.txt) and localization
(data/abilities_english.txt).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from builders.hero_lab import _HERE, STATS_DIR, _load_items, _versions
from mana_items import parse_kv

_ROOT = Path(__file__).resolve().parent.parent
_LOC_RE = re.compile(r'^\s*"([^"]+)"\s+"((?:[^"\\]|\\.)*)"', re.M)
# Items whose stat rows are intentionally rebuilt by the builder/JS
# (level modes, attribute toggle, toggle modes).
_CUSTOM_ROWS = {"item_dagon", "item_power_treads", "item_rapier"}


@pytest.fixture(scope="module")
def version():
    versions = _versions()
    if not versions:
        pytest.skip("no patch data available")
    return versions[-1]


@pytest.fixture(scope="module")
def items(version):
    result = {item["id"]: item for item in _load_items(version)}
    if not result:
        pytest.skip("no items loaded (data files missing)")
    return result


@pytest.fixture(scope="module")
def kv(version):
    return parse_kv((STATS_DIR / version / "items.txt").read_text(encoding="utf-8"))["DOTAAbilities"]


@pytest.fixture(scope="module")
def loc():
    text = (_HERE / "data" / "abilities_english.txt").read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for m in _LOC_RE.finditer(text):
        out.setdefault(m.group(1).lower(), m.group(2))
    return out


def _kv_fields(data: dict) -> dict[str, str]:
    out = {k.lower(): v for k, v in data.items() if not isinstance(v, dict)}
    for k, v in (data.get("AbilityValues") or {}).items():
        out.setdefault(k.lower(), v["value"] if isinstance(v, dict) and "value" in v else v)
    return out


def _num(text: str) -> str:
    n = float(text)
    return str(int(n)) if n == int(n) else str(n)


def test_every_valve_stat_row_is_shown_with_its_own_kv_value(items, kv, loc):
    """Valve semantics: `DOTA_Tooltip_ability_<item>_<field>` = "+$token" shows
    the value of KV `<field>`; `$token` only picks the label. Resolving the
    token through aliases dropped Ethereal Blade's "+24 All Attributes" and
    Solar Crest's "+25 Movement Speed"."""
    missing = []
    for iid, item in items.items():
        if item["class"] != "regular" or iid in _CUSTOM_ROWS or iid not in kv:
            continue
        fields = _kv_fields(kv[iid])
        shown = {re.sub(r"<[^>]+>", "", row).split(" ")[0].lstrip("+-").rstrip("%")
                 for row in item.get("tip", {}).get("attribs", [])}
        prefix = f"dota_tooltip_ability_{iid}_"
        for key, text in loc.items():
            if not key.startswith(prefix) or "$" not in text:
                continue
            value = str(fields.get(key[len(prefix):], "")).strip()
            if not re.fullmatch(r"-?[\d.]+", value) or float(value) == 0:
                continue
            if _num(value.lstrip("-")) not in shown:
                missing.append((iid, key[len(prefix):], value))
    assert missing == []


def test_ethereal_blade_and_solar_crest_rows(items):
    assert "+24 All Attributes" in items["item_ethereal_blade"]["tip"]["attribs"]
    solar = items["item_solar_crest"]
    assert "+25 Movement Speed" in solar["tip"]["attribs"]
    assert solar["bonus"]["ms"] == pytest.approx(25)


@pytest.mark.parametrize("item_id", ["item_ethereal_blade", "item_nullifier", "item_harpoon"])
def test_active_projectile_speed_is_not_a_passive_stat(items, item_id):
    assert items[item_id]["bonus"]["projSpeed"] == 0


@pytest.mark.parametrize("item_id", ["item_witch_blade", "item_devastator"])
def test_passive_projectile_speed_is_kept(items, item_id):
    assert items[item_id]["bonus"]["projSpeed"] > 0


def test_attack_range_rows_keep_valve_melee_ranged_qualifier(items):
    mkb = items["item_monkey_king_bar"]
    assert "+50 Attack Range (Melee Only)" in mkb["tip"]["attribs"]
    # 7.41: "+50 Attack Range to melee heroes only" — must not feed the
    # ranged/all bucket that scripts.js applies to ranged heroes.
    assert mkb["bonus"]["rangeUniqueMelee"] == pytest.approx(50)
    assert mkb["bonus"].get("rangeUniqueAll", 0) == 0
    assert any("(Ranged Only)" in row for row in items["item_dragon_lance"]["tip"]["attribs"])


def test_butterfly_base_attack_speed_is_modelled(items):
    fly = items["item_butterfly"]
    assert fly["bonus"]["baseAspdPct"] == pytest.approx(20)
    assert fly["bonus"]["aspd"] == 0
    assert "+20% Base Attack Speed" in fly["tip"]["attribs"]


def test_scripts_js_applies_melee_range_and_base_aspd():
    js = (_ROOT / "src" / "scripts.js").read_text(encoding="utf-8")
    assert "b.rangeUniqueMelee && !isRanged" in js
    assert re.search(r"\*\s*\(1 \+ \(itemsTotal\.baseAspdPct \|\| 0\) / 100\)", js)


def test_multi_level_description_values_show_every_level(items):
    """BKB Avatar duration is 9/8/7 in 7.41 — not just the first level."""
    desc = items["item_black_king_bar"]["tip"]["desc"]
    assert '<span class="GameplayVariable">9 / 8 / 7</span>' in desc


def test_purchasable_upgrade_levels_are_offered(items, kv):
    bot2 = items.get("item_travel_boots_2")
    assert bot2 is not None, "Boots of Travel 2 is purchasable in KV but missing"
    assert bot2["cost"] == int(kv["item_travel_boots_2"]["ItemCost"])
    assert bot2["icon"].endswith("travel_boots_2.png")
    assert bot2.get("isBoot") is True
