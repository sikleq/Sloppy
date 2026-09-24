"""Per-hero KV files changed layout in 7.41f (abilities moved under DOTAHeroes → hero →
AbilityDefinitions). Readers must handle both, or pages silently lose every ability
(AoE Increase showed no radii at all)."""
from builders import site_common as site


def test_hero_ability_blocks_old_layout():
    kv = {"DOTAAbilities": {"Version": "1", "abaddon_death_coil": {"AbilityValues": {}}}}
    assert "abaddon_death_coil" in site.hero_ability_blocks(kv)


def test_hero_ability_blocks_741f_layout():
    kv = {"DOTAHeroes": {"npc_dota_hero_abaddon": {
        "Model": "x", "AbilityDefinitions": {"abaddon_death_coil": {"AbilityValues": {}}}}}}
    assert list(site.hero_ability_blocks(kv)) == ["abaddon_death_coil"]


def test_aoe_page_finds_radii_in_latest_patch():
    import builders.aoe_increase as aoe
    latest = aoe._versions()[-1]
    kits = aoe._load_hero_kits(latest)
    assert kits.get("abaddon"), "hero kits empty — #base includes not followed"
    assert aoe._hero_abilities(latest, "crystal_maiden", kits.get("crystal_maiden")), \
        "no AoE abilities for Crystal Maiden — per-hero KV layout not understood"
