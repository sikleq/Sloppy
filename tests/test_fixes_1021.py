"""Generator fixes of 2026-10-21 (owner's 7.41 review)."""
from patch import elements as el


def test_bold_mana_and_cooldown_labels_go_to_the_head():
    # "<b>Mana Cost:</b> 50." stayed in the text under a head that already showed 50 (7.41 Zealot)
    values, desc = el._iab_take_meta("Teleports units. <b>Mana Cost:</b> 50. <b>Cooldown:</b> 10s.")
    assert values == {"manacost": "50", "cooldown": "10"}
    assert desc == "Teleports units."


def test_a_renamed_ability_shows_old_arrow_new_in_its_header():
    html = el.ability("Summon Razorback", slug="beastmaster_summon_razorback", old_title="Call of the Wild Boar")
    assert ('<span class="ability-title-old">Call of the Wild Boar</span><span class="ability-title-arrow">→</span>'
            '<span class="ability-title-new">Summon Razorback</span>') in html


def test_the_boar_card_opens_summon_razorback():
    from builders import entity_changes as ec
    assert ec._SUMMON_PARENT["npc_dota_beastmaster_boar"] == ("heroes/beastmaster.html", "Summon Razorback")


def test_enchant_change_table_heads_its_stats_column():
    import re
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / "dist" / "patches" / "7.41.html").read_text(encoding="utf-8")
    assert re.search(r'class="ench-tiers ench-change"><span class="ench-row-h"><span class="ench-stat-h">Stats</span>',
                     html)
