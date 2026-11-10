"""Guards the tag rules of the generator (which badge NEW / BUFF / NERF / REWORK / DEL / QoL / MISC a row gets,
which direction is better) and its other output rules: where a hero note goes, row wording, its own audits.
"""

import importlib
import os
import pathlib
import pytest
import re
import sys
import tools.generate_patch_code_v2 as g
from patch import item_ability_text

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
_ROOT_738 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _p738():
    with open(os.path.join(_ROOT_738, "content", "p738.py"), encoding="utf-8") as f:
        return f.read()


tags = importlib.import_module("patchgen.tags")
rows = importlib.import_module("patchgen.rows")


def test_generator_hero_rules_of_2026_11_06():
    # owner 2026-11-06: a new main attribute first in General; "Added three orb-centered facets…" hidden under the
    # facet cards; an ability gaining an active part -> old > new card (7.38 Special Delivery); Dauntless REWORK
    from tools.patchgen.post_hero import _postprocess_attr_change_first, _postprocess_facets_summary_covered
    from tools.patchgen.tags import _guess_tag
    lines = ['    W(hero_header("X"))', "    W(ul_open())", "    W(hero_stat_card())", '    W(li("Base damage", t("BUFF")))',
             '    W(li(attr_change("Universal", "Intelligence"), t("REWORK")))', "    W(ul_close())"]
    out = _postprocess_attr_change_first(lines)
    assert out[3].strip().startswith("W(li(attr_change(") and out[4].strip().startswith('W(li("Base damage"')
    lines = ['    W(hero_header("Invoker"))', '    W(li("Added three orb-centered facets. Each provides", t("NEW")))',
             '    W(new_facet("a", desc=[]))', '    W(new_facet("b", desc=[]))']
    assert _postprocess_facets_summary_covered(lines)[1].endswith(', t("NEW"), covered=True))')
    chosen = lines[:2] + ['    W(li("Aghanim\'s Scepter also provides a level to the orb of the chosen facet", t("BUFF")))'] + lines[2:]
    assert _postprocess_facets_summary_covered(chosen)[2].endswith("covered=True))")
    assert _guess_tag("Now affects only Mars himself") == "REWORK"
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert 'old=dict(name="Special Delivery", slug="marci_special_delivery", desc=game_ability_desc(' in p738
    assert 'Cast point: 1s", t("NEW"), covered=True))' in p738


def test_neutral_ai_rows_are_misc():
    from tools.patchgen.tags import _guess_tag
    assert _guess_tag("Neutrals will cast this ability on the closest enemy if there are three or more enemies") == "MISC"
    p738 = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert not re.search(r'li\("Neutrals will [^"]*", t\("(?:NEW|NERF)"\)', p738)
    assert 'W(li("Now has +25% base Slow Resistance", t("NEW")))' in p738


def test_amplifications_replaced_by_less_health_restoration_are_a_nerf():
    # "+25% Lifesteal and Health Regen Amplifications replaced with +20% Health Restoration — а разве это не nerf?"
    from tools.patchgen.post_general import _postprocess_umbrella_stat_rows
    row = ('    W(li("+25% Lifesteal and Health Regen Amplifications replaced with +20% Health Restoration", '
           't("REWORK")))')
    assert _postprocess_umbrella_stat_rows([row]) == [
        '    W(li("+25% Lifesteal and Health Regen Amplifications replaced with +20% Health Restoration", b(25, 20)))']
    other = '    W(li("Mana Burn replaced with Mana Break", t("REWORK")))'
    assert _postprocess_umbrella_stat_rows([other]) == [other]
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert "Amplifications replaced with +20% Health Restoration\", t(\"REWORK\")" not in p739


def test_a_healing_cut_turned_into_a_7_39_health_restoration_cut_is_a_nerf():
    # "другие случаи тоже проверь": 7.39 Health Restoration did not touch incoming heals (it does since 7.41)
    from tools.patchgen.post_general import _postprocess_lost_heal_cut_rows
    lost = ('    W(li("Frost instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 13%, now reduces '
            'Health Restoration by 13%", t("MISC")))')
    out = _postprocess_lost_heal_cut_rows([lost])[0]
    assert ', t("NERF"), extra=inline_note("Health Restoration does not reduce incoming healing' in out
    # Skadi also cuts Heal Amplification: the healing cut stays, MISC
    kept = ('    W(li("Cold Attack instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 40%, now '
            'reduces Health Restoration and Heal Amplification by 40%", t("MISC")))')
    assert _postprocess_lost_heal_cut_rows([kept]) == [kept]
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert p739.count('t("NERF"), extra=inline_note("Health Restoration does not reduce incoming healing') == 7


def test_legion_commanders_7_39_rework_counts_as_a_nerf_in_the_weights():
    # "оставить rework, но вообще стоило бы в весах учитывать и как нерф"
    from patch.weights import row_scores
    p739 = (ROOT / "content" / "p739.py").read_text(encoding="utf-8")
    assert ('now increases Health Restoration by 30/40/50/60%", t("REWORK"), covered=True, force_tag="rework nerf"))'
            in p739)
    net, vol = row_scores("Instead of increasing Healing by 50%, now increases Health Restoration by 30/40/50/60%",
                          {"rework", "nerf"})
    assert net < 0 < vol


def test_a_sub_ability_that_stops_cancelling_channeling_is_qol():
    from tools.patchgen.tags import _guess_tag
    assert _guess_tag("Land sub-ability no longer cancels channeling or interrupts movement") == "QoL"
    p740 = (ROOT / "content" / "p740.py").read_text(encoding="utf-8")
    assert 'W(li("Land sub-ability no longer cancels channeling or interrupts movement", t("QoL")))' in p740


def test_the_same_effect_from_what_replaced_a_removed_thing_is_misc():
    from tools.patchgen.tags import _guess_tag
    assert _guess_tag("Now applies to Shrines of Wisdom instead of removed Wisdom Runes") == "MISC"
    assert _guess_tag("Now requires Ogre Axe instead of Belt of Strength") == "REWORK"


@pytest.mark.parametrize("text, tag", [
    ("No longer an innate ability", "REWORK"),
    ("Starting from his second death, Roshan now always drops Roshan's Banner", "NEW"),
    ("The following are now Fully Disabled by Break", "NERF"),
    ("Fade no longer requires the target to remain still", "BUFF"),
    ("Returning as a Tier 1 Neutral item", "NEW"),
    ("Now is a Tier 3 Neutral item", "REWORK"),
    ("No longer procs Magic Stick", "BUFF"),
    ("Now procs Magic Stick", "NERF"),
    ("Illusory Orb: Now shows a preview of the orb trajectory", "QoL"),
    ("Can now be put on alt-cast to only pull Tusk towards his target ally", "NEW"),
    ("New Facet", "NEW"),
])
def test_7_37_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_every_value_negative_compares_the_sizes():
    """"Armor Corruption decreased from -4 to -3": a weaker armor reduction — a nerf, as Valve's word says."""
    assert g._emit_badge("Level 20 Talent Armor Corruption decreased from -4 to -3") == "b(4, 3)"
    assert g._normalize_note_text("Level 20 Talent Armor Corruption decreased from -4 to -3")["tag"] == "nerf"


def test_a_row_without_from_still_has_its_badge():
    assert g._emit_badge("Damage increase per armor decreased 0.3% to 0.25%") == "b(0.3, 0.25)"
    assert g._emit_badge("Split Amount rescaled 80/85/90/95/100% to 85/90/95/100%") == \
        "b([80, 85, 90, 95, 100], [85, 90, 95, 100])"


def test_a_rows_known_fact_stays_after_a_rewrap():
    lines = ['W(li("Teleport time to Roshan\'s outposts decreased from 6s to 4s", b(6, 4)))']
    assert "corner outposts" in g._postprocess_row_notes(lines)[0]


def test_two_lists_back_to_back_become_one():
    lines = ['W(ul_open())', 'W(li("a"))', 'W(ul_close())', 'W(ul_open())', 'W(li("b"))', 'W(ul_close())']
    assert g._merge_adjacent_lists(lines) == ['W(ul_open())', 'W(li("a"))', 'W(li("b"))', 'W(ul_close())']


def test_a_facet_prefix_with_the_word_facet_and_an_old_abilitys_real_slug():
    """"Cold Comfort Facet: Blueheart Floe: …" is the facet Cold Comfort; "Selemene's Favor: Ability removed" is the
    7.36 innate luna_selemenes_favor (from the files), not a made-up luna_selemene_s_favor."""
    cm = "\n".join(g._render_hero({"hero_id": 5, "hero_notes": [{"indent_level": 1, "note":
         "Cold Comfort Facet: Blueheart Floe: Now also increases mana regen amplification from 50% to 75%"}]},
         version="7.37"))
    assert 'facet_header("crystal_maiden_cold_comfort")' in cm and "Cold Comfort Facet" not in cm
    luna = "\n".join(g._render_hero({"hero_id": 48, "hero_notes": [
        {"indent_level": 1, "note": "Selemene's Favor: Ability removed"}]}, version="7.37"))
    assert 'slug="luna_selemenes_favor"' in luna


def test_a_former_innates_level0_row_is_a_nerf_not_a_rework():
    """Owner 2026-10-30: "Warpath почему-то rework везде вместо buff/nerf". Levels 1-3 the same, the level-0 value gone:
    NERF (what the hero had before the first point is gone, as Night Stalker 7.38's free level by points spent); a 0
    at level 0 lost nothing — MISC, but NERF once "No longer an innate ability" leads the row."""
    lines = ['W(hero_header("Bristleback"))', 'W(ability("Warpath", slug="bristleback_warpath"))', "W(ul_open())",
             'W(li("No longer an innate ability", t("REWORK")))',
             'W(li("Damage per stack rescaled from 5/15/20/25 to 15/20/25", b([5, 15, 20, 25], [15, 20, 25])))',
             'W(li("Movement per stack rescaled from 0/2/3/4% to 2/3/4%", b([0, 2, 3, 4], [2, 3, 4])))', "W(ul_close())"]
    out = g._postprocess_innate_level0(lines, "7.37")
    assert 't("NERF")' in out[4] and 'the 5 it had at level 0' in out[4]
    assert 't("MISC")' in out[5] and "nothing is lost" in out[5]
    merged = g._merge_no_longer_innate(['W(ul_open())', 'W(li("No longer an innate ability", t("REWORK")))', out[5],
                                        'W(ul_close())'])
    assert merged[1].startswith('W(li("No longer an innate ability. Movement') and 't("NERF")' in merged[1]
    assert "nothing is lost" not in merged[1]


def test_instead_of_rows_are_tagged_by_their_effect():
    """Owner 2026-10-30 ("много где ещё такие же ситуации"): a talent's "+4s … instead of +6s" is a number badge; a
    Silence instead of nothing BUFF; a single-tree requirement and the current speed instead of the max NERF."""
    assert g._emit_badge("Level 25 Talent is +4s Burning Spears Duration instead of +6s") == "b(6, 4)"
    assert g._guess_tag("Reality Rift: Instead of a 33% chance to do Nothing, now has a 33% chance to Silence") == "BUFF"
    assert g._guess_tag("Nature's Call: Now requires a single target tree to be selected to cast") == "NERF"
    assert g._guess_tag("Charge of Darkness: Lingering bonus movement speed is now determined by Spirit Breaker's "
                        "current bonus speed, instead of always the max") == "NERF"
    assert g._guess_tag("No longer scales with Vendetta") == "DEL"
    assert g._guess_tag("Now scales with Pierce the Veil") == "BUFF"


def test_a_talent_rows_is_goes_with_its_name():
    """7.37 Huskar: "Level 25 Talent is +4s …" read "Talent: is +4s …" on the page (visual check 2026-10-30)."""
    from patch.elements import _TALENT_PREFIX_RE
    text = "Level 25 Talent is +4s Burning Spears Duration instead of +6s"
    assert _TALENT_PREFIX_RE.sub(r"\1: ", text) == "Level 25 Talent: +4s Burning Spears Duration instead of +6s"
    assert _TALENT_PREFIX_RE.sub(r"\1: ", "Level 10 Talent +20 Damage") == "Level 10 Talent: +20 Damage"


@pytest.mark.parametrize("text, tag", [
    ("Hookshot: Now refunds Clockwerk 75% of the mana spent", "NEW"),
    ("Enchant: Now also increases attack range for units under Enchantress' control against the target", "NEW"),
    ("Scurry: Now increases duration to 3.5/4/4.5/5s", "NEW"),
    ("Burning Spear: Duration is no longer reduced", "BUFF"),
    ("Can now be cast during channeling and does not break invisibility", "NEW"),
    ("Level 15 Talent All Stats per hero hit with Reverse Polarity now stacks instead of refreshing", "NEW"),
    ("100% of bonus damage is converted to base damage for Phantom Lancer. Phantom Lancer illusions still convert 65% "
     "of the bonus damage", "BUFF"),
    ("Trample: Now provides +10% Self Bonus Move Speed when activated", "NEW"),
    ("Stun Duration now increases by 0.2s per ally in Snowball", "NEW"),
    ("Now counts one debuff per unique ability/item (e.g. Shiva's Guard will count as 1 debuff instead of 3)", "NERF"),
    ("Bonus damage is now decreased by the illusion damage reduction amount if applied by illusions", "NERF"),
    ("Death Ward: Now has a primary and secondary target", "NEW"),
])
def test_7_37b_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_less_time_to_reach_the_max_is_lower_is_better():
    assert "l=True" in g._emit_badge("Time to max damage/attack speed decreased from 8s to 6s (total duration unchanged)")


def test_a_hero_note_named_after_a_facet_of_that_patch_goes_under_the_facet():
    """7.37b "Elitist: Exort: Spell Amplification …" — Elitist was Invoker's facet (not in badges.FACETS: removed in
    7.38); it became an innate ability block."""
    out = "\n".join(g._render_hero({"hero_id": 74, "hero_notes": [
        {"indent_level": 1, "note": "Elitist: Exort: Spell Amplification per instance increased from 2/3% to 3/4%"}]},
        version="7.37b"))
    assert 'W(facet_header("invoker_elitist"))' in out
    assert "innate=True" not in out


def test_a_value_of_the_new_secondary_target_goes_in_the_rows_question_mark():
    """Owner 2026-10-30 (7.37b Death Ward): "Damage to secondary target is equal to 65% of the primary" is not a row of
    its own — it goes in the "?" of "Now has a primary and secondary target", even with another row between them."""
    body, _ = g._emit_notes([
        {"indent_level": 1, "note": "Death Ward: Damage to primary target increased from 45/70/95 to 55/90/125"},
        {"indent_level": 1, "note": "Death Ward: Now has a primary and secondary target"},
        {"indent_level": 1, "note": "Death Ward: Damage to secondary target is equal to 65% of the primary"}])
    rows = [ln for ln in body if ln.startswith("W(li(")]
    assert len(rows) == 2
    assert ('W(li("Death Ward: Now has a primary and secondary target", t("NEW"), '
            'extra=inline_note("Damage to secondary target is equal to 65% of the primary")))') in rows


def test_the_validator_reads_a_negated_direction():
    from tools.validate_data import _check_change
    issues = []
    _check_change({"name": "Huskar"}, {"text": "Burning Spear: Duration is no longer reduced", "tag": "buff"}, issues)
    assert issues == []


@pytest.mark.parametrize("text, tag", [
    # owner 2026-10-29: NEW, not BUFF
    ("No longer requires Enchant Totem to be leveled to be active", "NEW"),
    ("Multicasts now prioritize Ogre Magi himself, followed by heroes, then buildings, then creeps, skipping units that "
     "already have the buff", "NEW"),
    ("Bonus Agility is now applied during the rush as well as the 1.5s after it ends", "NEW"),
])
def test_7_37c_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_a_hero_note_named_after_a_basic_ability_goes_in_its_block():
    """7.37c Tinker "Defense Matrix: Cast Range decreased …" sat among the hero's general rows; Defense Matrix was one of
    his abilities that patch, so the rows go in its own block (as 7.37d's innate Duelist)."""
    out = "\n".join(g._render_hero({"hero_id": 34, "hero_notes": [
        {"indent_level": 1, "note": "Base Mana Regen decreased from 0.75 to 0.5"},
        {"indent_level": 1, "note": "Defense Matrix: Cast Range decreased from 700/750/800/850 to 700"}]},
        version="7.37c"))
    assert 'W(ability("Defense Matrix", slug="tinker_defense_matrix"))' in out
    assert 'W(li("Cast Range decreased from 700/750/800/850 to 700"' in out


def test_the_from_audit_takes_a_left_out_hero_value_from_the_patchs_base_hero():
    """7.37c Dawnbreaker "Base Health Regen increased from 0.25 to 0.5": 7.37b's Dawnbreaker had no own value, so the
    0.25 of npc_dota_hero_base; a hero absent from the patch (Ringmaster in 7.37b) stays unknown."""
    from tests.test_code_health import _from_audit
    a = _from_audit()
    assert (0.25,) in a._base_values("7.37b", "dawnbreaker")
    assert not a._base_values("7.37b", "ringmaster")


def test_an_auto_registered_facet_takes_the_game_files_colour():
    """Valve's web feed gave Convergence "Yellow0"; npc_heroes.txt of every 7.37 build says Yellow + GradientID 1."""
    from patch.ability_kv import hero_facets
    from patch.badges import FACETS
    assert hero_facets("phantom_lancer", "7.37c")["phantom_lancer_convergence"][1] == "Yellow1"
    assert FACETS["phantom_lancer_convergence"] == ("Convergence", "Yellow1")
    assert FACETS["earthshaker_slugger"][0] == "Slugger"      # the feed's title said "Slugger Facet"


@pytest.mark.parametrize("text, tag", [
    ("No longer doubles its bonuses at 25 minutes", "DEL"),
    ("Suppress no longer makes caster or ally unslowable", "DEL"),
    ("Soul Release now always gains a charge when the owner dies", "NEW"),                 # owner 2026-10-29
    ("Sacrificing creeps with Martyrdom (Aghanim's Scepter) now triggers On Death effects", "NEW"),   # owner
    ("Enemy heroes caught are no longer pulled to the center of the formation. Now they are placed inside as far away "
     "from the center as possible while not touching a cog", "REWORK"),                     # owner
    ("Alt cast behavior now has 50% of base spell's cast range", "NERF"),                  # owner
    ("Now heals creeps for 50% effectiveness", "NERF"),   # creeps were healed in full in 7.37c (KV, tooltip)
    ("Absorbing damage with Mana Shield now disables Blink Dagger", "NERF"),
    ("Aghanim's Shard no longer allows to hit the same enemy unit by multiple secondary Starstorms in a single cast",
     "DEL"),
    ("Effects that percentually change the base damage now also affect base damage bonus provided by Illusory "
     "Armaments", "NEW"),                                                                  # owner 2026-10-29
    ("Toggling items no longer breaks invisibility", "QoL"),
    ("Focus Fire: Windranger can no longer shoot arrows while channeling", "DEL"),
    ("Aghanim's Scepter invisibility buff is now dispelled if the base Windrun buff is dispelled", "NERF"),
])
def test_7_37d_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


def test_a_min_max_range_per_level_is_compared_by_each_middle():
    """7.37d Nature's Call: "Treant Damage decreased from 28-32/44-48/60-64/76-80 to 22-26/40-44/58-62/76-80" — a % per
    level against each range's middle, as the 7.37e single range, not a bare NERF tag."""
    text = "Nature's Call: Treant Damage decreased from 28-32/44-48/60-64/76-80 to 22-26/40-44/58-62/76-80"
    assert g._emit_badge(text) == "b([30, 46, 62, 78], [24, 42, 60, 78])"


def test_the_same_text_for_two_abilities_is_not_flagged_as_misplaced():
    """7.37d Omniknight: Purification and Repel both "Mana Cost increased from 80/95/110/125 to 90/105/120/135" (both
    changed in the game) — the loc map kept only the last key, and Purification's row read "belongs to omniknight_martyr"."""
    loc = g._load_patchnotes_loc("7.37d")["omniknight"]
    slugs = loc["mana cost increased from 80/95/110/125 to 90/105/120/135"]
    assert slugs == {"omniknight_purification", "omniknight_martyr"}


def test_a_hero_note_named_after_an_innate_goes_in_the_innate_block():
    """7.37d "Duelist: Bonus damage increased from 10% to 12%" — Juggernaut's innate that patch: its own innate block,
    not a plain row under the hero."""
    from patch.ability_kv import hero_abilities
    assert hero_abilities("juggernaut", "7.37d").get("duelist") == ("juggernaut_duelist", True)
    out = "\n".join(g._render_hero({"hero_id": 8, "hero_notes": [
        {"indent_level": 1, "note": "Duelist: Bonus damage increased from 10% to 12%"}]}, version="7.37d"))
    assert 'W(ability("Duelist", slug="juggernaut_duelist", innate=True))' in out
    assert 'W(li("Bonus damage increased from 10% to 12%", b(10, 12)))' in out


@pytest.mark.parametrize("text, tag", [
    ("Natural Order: Enemies that leave the AoE now lose 1 stack per second instead of all stacks instantly", "BUFF"),
    ("Now also applies to units under Lycan's control. Bonus is still based on Lycan's level", "BUFF"),
    ("Chain Frost: If the affected hero dies and buys back, Chain Frost will no longer follow that hero", "DEL"),
    ("Presence of the Dark Lord: Now Bonus Armor Reduction buff is removed when Shadow Fiend dies", "NERF"),
    ("Rolling Thunder: Turn Rate bonus changed from flat +110 to +40% (results in +48)", "NERF"),
    ("Nature's Call: Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40", "NERF"),
    ("Imps no longer explode if killed by enemy heroes", "DEL"),
    ("Eidolon gold bounty increased from 14-20 to 17-20", "NERF"),
    ("Stroke of Fate: Improved behavior when casting at maximum cast range", "QoL"),   # owner 2026-10-28
])
def test_7_37e_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


@pytest.mark.parametrize("text", [
    "Aghanim's Scepter charge restoration time increased from 60s to 70/65/60s",
    "Outgoing Spell Damage reflected increased from 20% to 21%",
])
def test_own_waits_and_self_damage_are_lower_is_better(text):
    assert "l=True" in g._emit_badge(text)


def test_an_old_min_max_range_is_compared_by_its_middle():
    """Owner 2026-10-28: "Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40" — a % per level against
    the middle of 18-24, not a bare tag; the enemy's gold, so lower is better."""
    text = "Nature's Call: Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40"
    assert g._emit_badge(text, hero_side=True) == "b(21, [16, 24, 32, 40], l=True)"
    assert g._emit_badge("Eidolon gold bounty increased from 14-20 to 17-20", hero_side=True) == "br(14, 20, 17, 20, l=True)"


def test_a_flat_bonus_turned_percent_compares_the_totals():
    """Owner 2026-10-29: Rolling Thunder "from flat +110 to +40% (results in +48)" — the base is 48 / 40% = 120, so the
    turn rate went 230 → 168 (−27%), a % badge, not a bare NERF tag."""
    text = "Rolling Thunder: Turn Rate bonus changed from flat +110 to +40% (results in +48)"
    assert g._emit_badge(text) == "b(230, 168)"


def test_an_enemy_damage_reflection_stays_higher_is_better():
    assert "l=True" not in g._emit_badge("Damage reflected increased from 10% to 12%")


@pytest.mark.parametrize("text, tag", [
    ("Vision Radius is now affected by changes to Area of Effect", "NEW"),
    ("All sources of evasion are doubled for the duration, including Redirect Chance from Mistwoods Wayfarer", "NEW"),
    ("Secondary shot now prioritizes heroes, then non-hero units, then buildings", "NEW"),
    ("Tricks of the Trade: When Riki kills a non-hero unit during Tricks of the Trade, the cooldown is reduced by 0.75s",
     "NEW"),
    ("Backstab: Riki also gets 25/75/125/175 bonus experience for courier and ward kills", "NEW"),
    ("Succubus: Now also makes Spell Lifesteal apply to reflected Magical and Pure Damage", "NEW"),
    ("Compared to previous iterations, ability duration can now be decreased by Status Resistance or increased by "
     "Debuff Duration bonuses", "NEW"),
    ("Now Talent Tree's All Attribute bonus provides an additional +3 to Morphling's primary attribute", "NEW"),
    ("Improved Glaive collision behavior for orbiting Glaives", "QoL"),
    ("Can now be put on autocast so Clinkz will throw a tar bomb when attacking, if the ability is available", "QoL"),
])
def test_7_38_rows_get_the_tag_of_their_effect(text, tag):
    assert g._guess_tag(text) == tag


@pytest.mark.parametrize("text, tag", [
    ("Strike Damage is now classified as reflection damage", "REWORK"),
    ("Quill Sprays that were released by the ability now deal damage that is classified as reflection damage", "REWORK"),
    ("Affected units no longer take increased magical and pure damage bonus from Winter Wyvern by default", "DEL"),
    ("Skill points can now be spent on All Attributes starting at level 2 instead of level 6", "REWORK"),
    ("Hookshot: Now requires at least one other allied hero to be within a 350 radius of the Hookshot target", "NEW"),
])
def test_the_owners_answers_on_7_38(text, tag):
    assert g._guess_tag(text) == tag
    row = re.search(re.escape(text) + r'", t\("(\w+)"\)', _p738())
    assert row and row.group(1) == tag


def test_arc_wardens_same_effect_is_rework_on_its_cards():
    # the row became the summary of a card (owner 2026-11-05): patch/two_selves.py writes the tag
    from patch.two_selves import SAME_EFFECT
    assert g._guess_tag(SAME_EFFECT) == "REWORK"


def test_precision_auras_tag_counts_every_hero_level_not_only_the_shown_columns():
    # owner 2026-11-02: NERF. 5% against 2% at level 1 is +150%, one of nine columns made the row BUFF; over all 30 levels -1.75%
    from patch.formula_rows import li_formula
    shown = [1, 5, 6, 11, 12, 17, 18, 25, 30]

    def row(**kw):
        return li_formula("Bonus rescaled", "2% per hero level", "4/8/12/16% + 1% per level", lambda L: 2 * L,
                          lambda L: [4, 8, 12, 16][0 if L < 6 else min(3, (L - 6) // 6 + 1)] + L,
                          levels=shown, label="Hero level", value_fmt="{:g}%", **kw)
    assert 'data-tag="buff"' in row()
    html = row(tag_levels=range(1, 31))
    assert 'data-tag="nerf"' in html and 'data-tag="buff"' not in html
    assert "150%" in html and "-23%" in html                      # the badges still show the start and the end
    head = html[html.index("<thead>"):html.index("</thead>")]
    assert len(re.findall(r"<th[ >]", head)) == len(shown) + 1    # the table keeps its columns


@pytest.mark.parametrize("text", [
    "Vision Radius is now affected by changes to Area of Effect",
    "All sources of evasion are doubled for the duration, including Redirect Chance from Mistwoods Wayfarer",
    "Secondary shot now prioritizes heroes, then non-hero units, then buildings",
    "Improved Glaive collision behavior for orbiting Glaives",
])
def test_the_page_carries_the_tag_the_generator_gives(text):
    row = re.search(re.escape(text) + r'", t\("(\w+)"\)', _p738())
    assert row and row.group(1) == g._guess_tag(text)


@pytest.mark.parametrize("left", [
    "Accumulation:", "Ruin and Restoration:", "Tar Bomb:",
])
def test_a_note_named_after_an_ability_sits_in_that_ability_block(left):
    assert f'li("{left}' not in _p738()


def test_the_blocks_those_notes_moved_to_exist():
    src = _p738()
    assert 'ability("Accumulation", slug="morphling_accumulation", innate=True)' in src
    assert 'ability("Ruin and Restoration", slug="skywrath_mage_ruin_and_restoration", innate=True)' in src
    assert 'ability("Tar Bomb", slug="clinkz_tar_bomb")' in src


def test_valves_whole_sentence_about_blocked_camps():
    assert "attempting to stack that camp will not create another Ancient creep" in _p738()


@pytest.mark.parametrize("text, tag", [
    ("Death Pact: Now can be cast while rooted or leashed, but without teleporting Clinkz to the target location", "NEW"),
    ("Can now be cast while rooted, but will not knock Sniper back if he is under the effect of root", "NEW"),
    ("Release sub-ability can now be cast while silenced", "NEW"),
    ("Return Astral Spirit and Move Astral Spirit sub-abilities can now be used while Elder Titan is disabled", "NEW"),
    ("Death Pact: Added alt-cast mode which disables teleportation", "QoL"),
    ("Neutrals will autocast this ability only if the Ancient Prowler Shaman has less than 90% health at the start of the attack", "MISC"),
    ("Neutrals will cast this ability on a random ally that is below 50% health", "MISC"),   # owner 2026-11-06
    ("Now is a Point Targeted ability with 900 cast range", "REWORK"),
    ("Arena Of Blood: Now provides 50% of the bonuses to all allies that are in the arena when an enemy dies inside of it", "NEW"),
    ("Sprout: Allied Tangos provide double the heal duration when consuming a tree created by Sprout", "NEW"),
    ("Exorcism: If a hero dies during Exorcism, their spirit is now added to both the current Exorcism, and as a charge for the next one", "NEW"),
    ("No longer disabled by Silence", "NEW"),
    # toggles keep the owner's older decision (2026-09-27)
    ("Toggling is no longer disabled by silence", "MISC"),
    ("Now can be toggled while silenced", "MISC"),
    ("Can no longer be disabled by Silence", "NEW"),
    # the other half of the old rule stays: nothing changed for these
    ("Can no longer be cast while rooted", "DEL"),
    ("Can now be cast without a target", "BUFF"),
])
def test_the_owners_tag_for_a_row(text, tag):
    assert tags._guess_tag(text) == tag


@pytest.mark.parametrize("text", [
    "Aghanim's Shard now increases Summon Duration by 5s (from 25s to 30s)",
    "Aghanim's Shard now increases damage by 20% (from 80/160/240/320 to 96/192/288/384)",
    "Aghanim's Scepter now increases movement speed slow by 20% (from 30/40/50% to 50/60/70%)",
])
def test_a_new_property_of_an_upgrade_is_new_without_a_percent(text):
    assert tags._guess_tag(text) == "NEW"
    assert rows._NEW_UPGRADE_RE.search(text)


def test_a_multiplier_with_x_is_read_as_numbers():
    badge = rows._emit_badge("Treant Multiplier rescaled from x2/x3/x4/x5/x6 to x4")
    assert badge == "b([2, 3, 4, 5, 6], 4)"


def test_a_tooltip_may_name_the_blocks_channel_time():
    assert item_ability_text._values({"AbilityChannelTime": "1"})["abilitychanneltime"] == "1"
    assert item_ability_text._fill("Channel for %abilitychanneltime% second.", {"abilitychanneltime": "1"}) == "Channel for 1 second."


@pytest.mark.parametrize("text", [
    "Wyrm's Wrath: Instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 14/21/28/35%, now reduces "
    "Health Restoration by 14/21/28/35%",
    "Aghanim's Scepter instead of reducing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 10% per stack, now "
    "reduces Health Restoration by 10% per stack",
    "Hobble 40% Healing, Health Regen, Lifesteal and Spell Lifesteal reductions replaced with a new 40% Health "
    "Restoration reduction stat",
])
def test_a_renamed_heal_mechanic_with_the_same_numbers_is_misc(text):
    assert g._guess_tag(text) == "MISC"


def test_a_renamed_heal_mechanic_with_new_numbers_stays_a_change():
    assert g._guess_tag("Instead of increasing Healing, Health Regen, Lifesteal, and Spell Lifesteal by 50%, now "
                        "increases Health Restoration by 30/40/50/60%") == "REWORK"


@pytest.mark.parametrize("text", [
    "Added an auto-cast. Right-click the ability to make Bristleback automatically cast it whenever it's possible",
    "Astral Spirit no longer automatically rejoins Elder Titan on collision with him. Now requires the duration to run "
    "out or the Return ability to be cast",
])
def test_control_conveniences_are_qol(text):
    assert g._guess_tag(text) == "QoL"


def test_a_follow_up_list_stays_in_its_rows_note():
    """7.38c Flaming Lasso: "The following abilities continue to break the lasso" is the rest of the row above's note
    (the generator writes it so), not a row of its own (owner 2026-10-27)."""
    import glob
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bad = [f"{os.path.basename(p)}:{n}" for p in glob.glob(os.path.join(root, "content", "p*.py"))
           for n, line in enumerate(open(p, encoding="utf-8"), 1) if 'W(li("The following abilities continue' in line]
    assert not bad, bad


def test_losing_the_blink_overshoot_penalty_is_a_buff():
    # a click past max range used to blink 75% of it (owner 2026-10-27)
    assert g._guess_tag("Blink no longer has an overshoot range") == "BUFF"
