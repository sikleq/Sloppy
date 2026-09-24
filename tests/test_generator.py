"""Tests for generate_patch_code_v2 tag heuristics and l=True logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from generate_patch_code_v2 import (
    _guess_tag, LOWER_IS_BUFF, _NOT_LOWER_IS_BUFF,
    _postprocess_recipe_cost_zero_net, _DMG_L1_RE,
)
import generate_patch_code_v2 as g


# ── _guess_tag: canonical phrase → expected tag ────────────────────────────

@pytest.mark.parametrize("text, expected", [
    # NEW
    ("Added to Captains Mode", "NEW"),
    ("Can now be disassembled", "NEW"),
    ("Now also grants 10% evasion", "NEW"),
    ("Added a new passive component", "NEW"),
    # DEL
    ("Removed from Captains Mode", "DEL"),
    ("No longer provides bonus damage", "DEL"),
    ("No longer applied by illusions", "DEL"),
    ("Can no longer target magic immune units", "DEL"),
    ("Aghanim's Scepter no longer reduces cooldown by 25s", "DEL"),
    # REWORK
    ("Replaced with a new ability", "REWORK"),
    ("Reworked", "REWORK"),
    ("Rescaled from 10/20/30 to 15/25", "REWORK"),
    ("No longer levels with Duel", "REWORK"),
    ("Changed from a passive to an active", "REWORK"),
    # BUFF — direction keyword without from/to
    ("Damage increased", "BUFF"),
    ("Armor raised", "BUFF"),
    ("Range improved", "BUFF"),
    # NERF — direction keyword without from/to
    ("Damage decreased", "NERF"),
    ("Duration reduced", "NERF"),
    ("Range lowered", "NERF"),
    # MISC
    ("Fixed tooltip description", "QoL"),
    ("Fixed a bug where stun lasted too long", "MISC"),
    ("Unchanged", "MISC"),
    # TAG_OVERRIDES
    ("Now shares cooldown with Blink Dagger", "MISC"),
    ("Respawn time increased from 25 to 30", "NERF"),
    ("Respawn time decreased from 30 to 25", "BUFF"),
    ("Now requires Blade of Alacrity instead of Band of Elvenskin", "REWORK"),
    # "No longer has a penalty" → BUFF (not DEL)
    ("No longer has a movement speed penalty", "BUFF"),
    ("No longer has an attack speed debuff slow", "BUFF"),
    # from/to present → None (let b() decide)
    ("Damage increased from 100 to 120", None),
    ("Cooldown decreased from 30 to 25", None),
    # ── classes found by the 2026-09-18 datafeed proofread ──
    # removed own restriction / self-penalty → BUFF
    ("Toggling is no longer disabled by silence", "BUFF"),
    ("Can no longer be disabled by Silence", "BUFF"),
    ("Now can be toggled while silenced", "BUFF"),
    ("Raptor Dance: Can no longer be interrupted by casting Grappling Claw", "BUFF"),
    ("Activation no longer interrupts movement", "BUFF"),
    ("Land sub-ability no longer cancels channeling or interrupts movement", "BUFF"),
    ("Now can be cast without cancelling Charge of Darkness", "BUFF"),
    ("No longer has reduced movement slow against creeps", "BUFF"),
    ("No longer has illusion vision penalty", "BUFF"),
    ("No longer freezes Reincarnation cooldown while Wraith Delay is active", "BUFF"),
    ("Atrophy Aura: No longer loses cleave on death", "BUFF"),
    ("Duration is no longer decreased on Largo from his own abilities", "BUFF"),
    ("Gaining max stacks requirement for the speedup buff is removed", "BUFF"),
    # own buff / debuff becomes undispellable → BUFF; becomes dispellable / disjointable → NERF
    ("Buff is no longer dispellable", "BUFF"),
    ("Break debuff is no longer dispellable", "BUFF"),
    ("Fate's Edict that was cast on Oracle or his ally is now dispellable by enemies", "NERF"),
    ("Draw Forth initial projectile is now disjointable", "NERF"),
    # new restriction / limit / delay → NERF
    ("Now only affects enemy heroes", "NERF"),
    ("Now only available with Aghanim's Scepter", "NERF"),
    ("Now affects only attacks made on enemy heroes", "NERF"),
    ("Now has a 0.3s cast point", "NERF"),
    ("Falcon Rush: Now has an 825 break distance", "NERF"),
    ("Spellover now has a 0.1s internal cooldown", "NERF"),
    ("Effect now ends if Spirit Breaker is more than 900 units away from the target", "NERF"),
    ("Zombies summoned by the facet effect now die when Undying dies", "NERF"),
    ("The active effect may only trigger up to a maximum of 500 stacks", "NERF"),
    ("Movement is now cancelled if Magnus is interrupted", "NERF"),
    ("Now disabled by roots", "NERF"),
    ("Health regen reduction does not affect enemies in fountain", "NERF"),
    # removed capability → DEL
    ("Certain spells that are toggleable are no longer stealable", "DEL"),
    ("No longer benefits from mana cost reduction effects", "DEL"),
    ("Clones can no longer copy Bottle", "DEL"),
    ("No longer has an alt-cast", "DEL"),
    ("Defense Matrix: No longer blinks Tinker if he is rooted or leashed", "DEL"),
    # structural → REWORK
    ("Now a Universal melee hero instead of a creep", "REWORK"),
    ("Now an Agility Hero", "REWORK"),
    ("Now Spectre's ultimate ability", "REWORK"),
    ("Ability is now Innate to Spirit Bear", "REWORK"),
    # 7.38 base-patch classes
    ("Is now an Agility Hero", "REWORK"),
    ("Is now a Universal Hero", "REWORK"),
    ("Now follows global Lifesteal rules (as a result, gained 40% creep penalty)", "NERF"),
    ("Aghanim's Shard no longer decreases cooldown by 10s", "DEL"),
    ("Reality: No longer decreases cooldown", "DEL"),
    ("No longer instantly kills enemy illusions", "DEL"),
    ("Shadowraze: No longer slows attack speed", "DEL"),
    ("No longer buffs allies", "DEL"),
    ("No longer restores mana", "DEL"),
    ("Sharpshooter: No longer decreases max wind-up time", "BUFF"),
    # 7.38 audit: "No longer <heals/casts> ... by default" removes a beneficial effect → DEL
    ("No longer heals Invoker when dealing damage by default", "DEL"),
    ("No longer casts Press the Attack on victory by default", "DEL"),
    # 2026-09-22 generator-vs-proofread diff on 7.38 (confident direction flips)
    ("Tempest Double no longer has penalties when more than 2000 range away from Arc Warden", "BUFF"),
    ("Passive: Buried Treasure. Gold loss on death is reduced by 100%", "BUFF"),
    ("No longer freezes enemy ability and item cooldowns", "DEL"),
    ("No longer reduces vision", "DEL"),
    ("Now isn't removed on attack by default", "BUFF"),
    ("Ghost Shroud: Now also makes enemies have their restoration amplification decreased by the same value", "BUFF"),
    # unparseable from/to ("3 minutes") falls back to increased/decreased — must honour lower-is-better
    ("Spawn interval increased from 3 minutes to 4 minutes", "NERF"),
    ("Spawn interval decreased from 4 minutes to 3 minutes", "BUFF"),
    # a NEGATIVE cooldown amount is a cooldown-reduction talent: bigger magnitude = buff
    ("Level 10 Talent increased from -5s Unstable Concoction Cooldown to -8s", "BUFF"),
    # user rule: adding an icon / indicator is QoL, not a buff
    ("Added a Roshan icon near the minimap that shows Roshan's state (alive, dead, maybe alive) and location:", "QoL"),
    ("Added a visual indicator over the caster of the smoke.", "QoL"),
    ("Now is an innate ability", "REWORK"),
    ("Now levels with Marksmanship", "REWORK"),
    ("Now requires Aghanim's Scepter to cast other abilities during channeling", "NERF"),
    ("Affected units no longer take increased magical and pure damage bonus from Winter Wyvern by default", "NERF"),
])
def test_guess_tag(text, expected):
    assert _guess_tag(text) == expected


# ── Damage-at-level ranges → br() at ANY level (7.38 audit: was level-1 only) ──

@pytest.mark.parametrize("text, groups", [
    ("Damage at level 1 increased from 44-48 to 48-54", ("44", "48", "48", "54")),
    ("Damage at level 30 decreased by 61 (from 227-234 to 166-173)", ("227", "234", "166", "173")),
    ("Damage at level 30 decreased by 51-49 (from 196-204 to 145-155)", ("196", "204", "145", "155")),
    ("Damage at level 25 increased by 27 (from 122-126 to 149-153)", ("122", "126", "149", "153")),
])
def test_damage_at_level_range_matches(text, groups):
    m = _DMG_L1_RE.search(text)
    assert m and m.groups() == groups


# ── LOWER_IS_BUFF: keywords that flip direction ───────────────────────────

@pytest.mark.parametrize("text, should_match", [
    # Should match (l=True)
    ("Cooldown increased from 10 to 12", True),
    ("Mana Cost decreased from 100 to 80", True),
    ("Gold Cost increased from 900 to 1000", True),
    ("Base Attack Time decreased from 1.7 to 1.6", True),
    ("Cast Point increased from 0.3 to 0.4", True),
    ("Channel Time decreased from 3 to 2.5", True),
    ("Recharge Time increased from 60 to 70", True),
    ("Incoming Damage increased from 10% to 15%", True),
    ("Damage Taken increased from 5% to 8%", True),
    ("Damage Vulnerability increased from 10% to 15%", True),
    ("Building Damage Penalty decreased from 50% to 40%", True),
    ("Penalty increased from 5 to 10", True),
    ("Recipe cost decreased from 1000 to 800", True),
    ("Respawn Time increased from 25 to 30", True),
    ("Activation Time decreased from 0.5 to 0.3", True),
    ("Restore Time increased from 3 to 4", True),
    ("Disable range decreased from 400 to 325", True),
    ("Enemy hero disable range decreased from 325 to 300", True),
    ("Damage interval improved from 1s to 0.5s", True),
    ("Attack Interval increased from 1.15s to 1.2s", True),
    ("Flight time decreased from 1.25s to 1.1s", True),
    ("Keen Eye disable duration on taking damage increased from 3s to 6s", True),
    ("Stun duration from falling off the cut tree decreased from 4s to 3s", True),
    ("Relentless slow resistance loss per enemy hero in range decreased from 20% to 10%", True),
    ("Creep penalty decreased from 50% to 35%", True),
    ("Max Mana Penalty increased from 10% to 10/12/14%", True),
    ("Voodoo Restoration: Mana per second rescaled from 8/12/16/20 to 9/12/15/18", True),
    ("Health Cost increased from 10% to 12%", True),
    ("Reverberate damage threshold increased from 180 to 220", True),
    # trigger thresholds (higher = fires less = worse) and pulse/spawn intervals (wider = fewer = worse)
    ("Burn Through damage threshold increased from 40 to 55", True),
    ("Damage threshold increased from 350 to 375", True),
    ("Spellover damage threshold increased from 100 to 200", True),
    ("Aghanim's Shard pulse interval decreased from 3.5s to 3s", True),
    ("Twister spawn interval increased from 300 to 400", True),
    # 2026-09-22 7.38 diff: owner-side timers / trigger requirements
    ("Restock Time decreased from 80s to 70s", True),
    ("Sai Base Attack Rate increased from 1.2/1.1/1.0/0.9s to 1.3/1.2/1.1/1s", True),
    ("Number of enemy units in range required to trigger a cast increased from 1 to 3", True),
    ("Summon Familiars: Familiar Gold Bounty decreased from 70 to 50", True),   # own summon's bounty
    # Should NOT match (normal direction)
    # own bonuses that merely mention a lower-is-better word
    ("Level 25 Talent BAT Reduction during Insatiable Hunger decreased from 0.3s to 0.25s", False),
    ("Thirst: Bonus Move Speed while on cooldown increased from 0% to 50%", False),
    ("Double Edge: Damage taken as damage bonus increased from 25% to 35%", False),
    # enemy debuff strengths (higher = better for the caster): armor / attack-speed / resistance reduction, armor loss
    ("Armor Reduction decreased from 5/6/7/8 to 3.5/5/6.5/8", False),
    ("Attack Speed Reduction increased from 30% to 35%", False),
    ("Natural Order: Magic Resistance Reduction per second decreased from 1% to 0.8%", False),
    ("Viscous Nasal Goo: Armor Loss per stack decreased from 2.5/3/3.5/4 to 2/2.5/3/3.5", False),
    ("Damage Threshold Reduction increased from 25 to 30", False),
    ("Magic Resistance increased from 5/10/15/20% to 8/12/16/20%", False),
    ("Disseminate: Health loss decreased from 9/11/13/15% to 9/10/11/12%", False),
    ("Slow per cooldown decreased from 7/8/9/10% to 4/5/6/7%", False),
    ("Level 10 Talent Time Dilation DPS Per Cooldown decreased from +9 to +6", False),
    ("Max Slow increased from 35/40/45/50% to 50%", False),
    ("Magic Resistance bonus decreased from +20% to +18%", False),
    ("Ether Blast magic damage vulnerability decreased from 40% to 30%", True),
    ("Relentless enemy search radius increased from 300 to 600", False),
    ("Dominate target unit's max health minimum increased from 1800 to 1900", False),
    ("Damage increased from 100 to 120", False),
    ("Duration increased from 4 to 5", False),
    ("Heal increased from 200 to 250", False),
    ("Bonus Agility increased from 10 to 15", False),
    ("Attack Speed increased from 30 to 40", False),
])
def test_lower_is_buff(text, should_match):
    match = bool(LOWER_IS_BUFF.search(text))
    not_excluded = not bool(_NOT_LOWER_IS_BUFF.search(text))
    result = match and not_excluded
    assert result == should_match, f"LOWER_IS_BUFF for '{text}': got {result}, expected {should_match}"


# ── _NOT_LOWER_IS_BUFF: exclusions ───────────────────────────────────────

@pytest.mark.parametrize("text", [
    "Cooldown Reduction increased from 10% to 15%",
    "Cooldown Advance increased from 2 to 3",
    "Mana Cost Reduction increased from 10% to 15%",
    "Penalty Reduction increased from 5% to 10%",
    "Cooldown speed is increased by 30% while in water",
])
def test_not_lower_is_buff_exclusions(text):
    assert LOWER_IS_BUFF.search(text), f"Should match LOWER_IS_BUFF base: {text}"
    assert _NOT_LOWER_IS_BUFF.search(text), f"Should be excluded by _NOT_LOWER_IS_BUFF: {text}"


# ── Recipe cost with unchanged total → BUFF/NERF (not MISC) ────────────────
# A cheaper recipe with an unchanged total is a real player benefit (component
# stats arrive earlier, the final combine is cheaper); a pricier recipe is a
# nerf. The recipe b() badge must drive the row, never t("MISC").

def _pp1(line):
    return _postprocess_recipe_cost_zero_net([line])[0]


def test_recipe_cheaper_total_unchanged_inline_is_buff_not_misc():
    out = _pp1('W(li("Recipe cost decreased from 600 to 400. Total cost unchanged at 3900g", b(600, 400, l=True)))')
    assert 't("MISC")' not in out
    assert 'b(600, 400, l=True)))' in out


def test_recipe_pricier_total_unchanged_inline_keeps_nerf_badge():
    out = _pp1('W(li("Recipe cost increased from 500 to 525. Total cost unchanged at 1625g", b(500, 525, l=True)))')
    assert 't("MISC")' not in out
    assert 'b(500, 525, l=True)))' in out


def test_recipe_total_unchanged_split_note_is_badge_not_misc():
    out = _pp1('W(li("Recipe cost decreased from 1350 to 1250", b(1350, 1250, l=True), '
               'extra=inline_note("Total cost unchanged at 4500g")))')
    assert 't("MISC")' not in out
    assert 'b(1350, 1250, l=True)' in out
    assert 'extra=inline_note("Total cost unchanged at 4500g")' in out


def test_recipe_and_total_both_change_still_tags_by_total():
    out = _pp1('W(li("Recipe cost decreased from 300 to 200. Total cost increased from 2500 to 2600", b(2500, 2600, l=True)))')
    # recipe % inline, total badge drives the row
    assert '+ b(300, 200, l=True)' in out
    assert out.rstrip().endswith('b(2500, 2600, l=True)))')


# ---- Generated scaffolds must be valid Python for every datafeed version ----
# Regression: a "Base X increased" row already carries extra=note_box(...); when an
# indented "Damage on level 1 ..." sub-row was folded onto it, the generator appended
# a SECOND `extra=` kwarg -> SyntaxError ("keyword argument repeated") for 7.41+.
_ALL_VERSIONS = sorted(
    os.path.basename(p)[:-len("_datafeed.json")]
    for p in __import__("glob").glob(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "*_datafeed.json"))
)


@pytest.mark.parametrize("version", ["7.41", "7.41a", "7.41b", "7.41c", "7.41d", "7.41f"])
def test_generated_scaffold_compiles(version, capsys):
    src = g.generate(version)
    capsys.readouterr()
    compile(src, f"_generated_p_{version}", "exec")      # raises SyntaxError on duplicate kwargs


def test_folded_subrow_merges_into_existing_extra(capsys):
    src = g.generate("7.41a")
    capsys.readouterr()
    for ln in src.splitlines():
        if ln.startswith("W(li(") and "note_box(" in ln and "inline_note(" in ln:
            assert ln.count("extra=") == 1, ln
            assert "+ inline_note(" in ln, ln
            break
    else:
        pytest.fail("expected a Base-stat row with both note_box and a folded inline_note")


# Regression: neutral-creep headers were emitted as `_NC_CDN + "x.png"`, a name that
# only exists if the content file defines it by hand -> NameError when the scaffold
# runs. The generator must reference an icon prefix exported by patch.api.
@pytest.mark.parametrize("version", ["7.31", "7.38", "7.41"])
def test_generated_scaffold_executes(version, capsys):
    src = g.generate(version)
    capsys.readouterr()
    ns = {}
    # save_html stubbed: the scaffold ends with save_html('patches/<ver>.html'),
    # which would overwrite the real built page in dist/ with the raw scaffold.
    exec("from patch.api import *\nsave_html = lambda *a, **k: None\n" + src, ns)
    capsys.readouterr()


# ---- Sub-note folding (2026-09-23) ----
# Before: only the FIRST deeper row folded into the parent's "?" popup; its
# siblings became stand-alone rows (7.38 "Reflected spells ... following:" put
# "Caster's facet upgrades" in the popup, "Bonuses from talents" and the Aghs line
# as separate rows, and hung the Aghs explanation on the wrong row).
def _gen_rows(notes):
    from generate_patch_code_v2 import _emit_notes
    lines, _ = _emit_notes(notes)
    return [l for l in lines if l.startswith("W(li(")]


def test_enumeration_children_all_fold_into_parent_popup():
    rows = _gen_rows([
        {"indent_level": 1, "note": "Reflected spells now benefit from all bonuses the original cast had, including the following:"},
        {"indent_level": 2, "note": "Caster's facet upgrades"},
        {"indent_level": 2, "note": "Bonuses from talents"},
        {"indent_level": 2, "note": "Aghanim's Shard and Aghanim's Scepter upgrades", "aghanims": "scepter"},
        {"indent_level": 3, "note": "Upgrades used to depend on Aghanim's items the reflecting unit had"},
        {"indent_level": 1, "note": "Units no longer gain bonus movement speed during the night"},
    ])
    assert len(rows) == 2, rows
    r = rows[0]
    for part in ("Caster's facet upgrades", "Bonuses from talents",
                 "Aghanim's Shard and Aghanim's Scepter upgrades — Upgrades used to depend"):
        assert part in r, (part, r)
    assert r.count("inline_note(") == 1


def test_single_child_still_folds_as_info():
    rows = _gen_rows([
        {"indent_level": 1, "note": "Universal Heroes' damage per attribute decreased from 0.7 to 0.45"},
        {"indent_level": 2, "note": "As a result, many heroes have had their Base Damages and attribute gains changed"},
    ])
    assert len(rows) == 1 and "inline_note(\"As a result" in rows[0]


def test_nested_sub_changes_also_fold_into_parent_popup():
    # The official page indents them under the parent -> they are its info.
    rows = _gen_rows([
        {"indent_level": 1, "note": "Tormentor's abilities now scale with game time instead of the number of deaths"},
        {"indent_level": 2, "note": "Unyielding Shield: Damage absorb rescaled from 2500 + (200 per death) to 1900 + (20 per minute of game time)"},
        {"indent_level": 2, "note": "Reflect: Damage percentage rescaled from 90 + (20 per death) to 50 + (2 per minute of game time)"},
        {"indent_level": 1, "note": "The Shining: Radius decreased from 1200 to 1000"},
    ])
    assert len(rows) == 2, rows
    assert "Unyielding Shield" in rows[0] and "<br>Reflect:" in rows[0]


def test_damage_at_level_1_kid_stays_a_visible_row():
    rows = _gen_rows([
        {"indent_level": 1, "note": "Base Damage decreased by 2"},
        {"indent_level": 2, "note": "Damage at level 1 decreased from 51-58 to 49-56"},
    ])
    assert len(rows) == 2 and "inline_note(" not in rows[0], rows


def test_card_body_parents_keep_their_kids_as_rows():
    rows = _gen_rows([
        {"indent_level": 1, "note": "Ability Reworked"},
        {"indent_level": 2, "note": "Cast Range: 900, Mana Cost: 100, Cooldown: 22s"},
        {"indent_level": 2, "note": "Base Damage: 120/160/200/240"},
    ])
    assert len(rows) == 3, rows


def test_item_reworked_title_gets_changed_label_and_component_diff():
    from generate_patch_code_v2 import _render_item
    item = {"ability_id": 1, "title": '<span class="Rework">Item Reworked</span>',
            "ability_notes": [
                {"indent_level": 1, "note": "Requires Orb of Frost (250), Orb of Blight (300) and Band of Elvenskin (450). Total cost: 1000"},
                {"indent_level": 1, "note": "Provides +8 Agility"},
            ]}
    out = "\n".join(_render_item(item, "7.38"))
    assert 'changed="Item Reworked"' in out
    assert 'auto_components_change(' in out and '"7.38"' in out
    assert "Requires Orb of Frost" not in out
    assert "Provides +8 Agility" in out


def test_attribute_change_row_uses_attr_change_with_old_attribute():
    row = g._emit_li("Is now a Universal Hero", hero_name="Arc Warden", version="7.38")
    assert row == 'W(li(attr_change("Agility", "Universal"), t("REWORK")))'


def test_attr_change_markup_coloured_names_and_entity_arrow():
    from patch.elements import attr_change
    html = attr_change("Agility", "Universal")
    assert "&rarr;" in html and "→" not in html          # entity, never a literal arrow
    assert "<img" not in html                                   # same font as the row, no icons
    assert '<b class="attr-chip is-agi">Agility</b>' in html and '<b class="attr-chip is-uni">Universal</b>' in html
    assert html.startswith("Main attribute changed from")


def test_minute_formula_diff_becomes_li_formula_with_minute_table():
    line = 'W(li("Gold provided after the initial set rescaled from 36 + (9 per 5 minutes) to 40 + (6 per 4 minutes)", t("REWORK")))'
    out = g._postprocess_minute_formula([line])[0]
    assert out.startswith("W(li_formula(")
    assert "lambda M: 36 + 9 * (M // 5)" in out and "lambda M: 40 + 6 * (M // 4)" in out
    compile(out, "<t>", "eval")


def test_plain_per_level_line_is_not_a_minute_formula():
    line = 'W(li("Damage changed from 10 + 2 per level to 12 + 1 per level", t("REWORK")))'
    assert g._postprocess_minute_formula([line]) == [line]


def test_new_building_block_under_map_objectives_is_new_objective():
    lines = [
        'W(plain_header("Map Objectives"))',
        'W(subgroup("Shrines of Wisdom"))',
        'W(li("Wisdom Runes removed and replaced with new buildings: Shrines of Wisdom", t("DEL")))',
        'W(li("Shrines are located in the jungle", t("MISC")))',
        'W(subgroup("Bounty Runes"))',
        'W(li("Spawn interval increased from 3 minutes to 4 minutes", t("NERF")))',
    ]
    out = g._postprocess_new_block_label(lines)
    assert out[1] == 'W(subgroup("Shrines of Wisdom", new="New objective"))'
    assert 't("NEW")' in out[3]
    assert out[4] == lines[4]


def test_twin_rows_with_same_info_merge_into_one():
    a = 'W(li("Lotus Pools will now spawn Great Lotuses after Tier 4 Neutral Items are available", t("NEW"), extra=inline_note("All remaining Lotuses in Lotus Pools will be combined and rounded up to the nearest number of Great Lotuses they could form")))'
    b = 'W(li("Lotus Pools will now spawn Greater Lotuses after Tier 5 Neutral Items are available", t("NEW"), extra=inline_note("All remaining Great Lotuses in Lotus Pools will be combined and rounded up to the nearest number of Greater Lotuses they could form")))'
    out = g._postprocess_merge_twin_rows([a, b])
    assert len(out) == 1
    assert "Tier 4 Neutral Items are available, and Greater Lotuses after Tier 5" in out[0]
    assert out[0].count("inline_note(") == 1


def test_removed_thing_gets_own_subgroup_above_new_block():
    lines = [
        'W(plain_header("Map Objectives"))',
        'W(subgroup("Shrines of Wisdom"))', 'W(ul_open())',
        'W(li("Wisdom Runes removed and replaced with new buildings: Shrines of Wisdom", t("DEL")))',
        'W(li("Experience will be granted to a random hero", t("MISC"), extra=inline_note("Same as Wisdom Runes")))',
        'W(ul_close())',
    ]
    out = g._postprocess_new_block_label(lines)
    assert out[1:5] == ['W(subgroup("Wisdom Runes"))', 'W(ul_open())', lines[3], 'W(ul_close())']
    assert out[5] == 'W(subgroup("Shrines of Wisdom", new="New objective"))'
    assert 't("NEW")' in out[7]


def test_boss_block_splits_abilities_and_marks_reworked_objective():
    lines = [
        'W(subgroup("Tormentor"))', 'W(ul_open())',
        'W(li("Tormentor spawns repositioned to the corners of the map", t("REWORK")))',
        'W(li("There is only a single Tormentor active at a time", t("REWORK")))',
        'W(li("Tormentor\'s abilities now scale with game time instead of the number of deaths", t("REWORK"), extra=inline_note("Reflect: Damage percentage rescaled from 90 + (20 per death) to 50 + (2 per minute of game time)")))',
        'W(li("Tormentor now grants 250 gold to each team member on death", t("NEW")))',
        'W(li("The Shining: Radius decreased from 1200 to 1000", b(1200, 1000)))',
        'W(li("Alleviation: New ability. Heals nearby units", t("MISC")))',
        'W(ul_close())',
    ]
    out = g._postprocess_boss_blocks(lines)
    assert out[0].startswith('W(unit_header("Tormentor"') and 'new_mech="Reworked objective"' in out[0]
    assert not any("The Shining:" in ln or "inline_note(\"Reflect" in ln for ln in out)
    assert any(ln.startswith('# v2-todo: Reflect') for ln in out)
    assert 'W(ability("The Shining", icon_url="../icons/abilities/miniboss_radiance.png"))' in out
    assert any(ln.startswith('W(ability_change(None, {"name": "Alleviation"') and 'tag="new"' in ln for ln in out)


@pytest.mark.parametrize("text,tag", [
    ("Tormentor now spawns for the first time at 15:00", "REWORK"),
    ("Tormentor spawns repositioned to the corners of the map", "REWORK"),
    ("Roshan no longer drops Aghanim's Blessing", "DEL"),
    ("Lotus Pools will now spawn Great Lotuses after Tier 4 Neutral Items are available", "NEW"),
    ("Tormentor now grants 250 gold to each team member on death", "NEW"),
])
def test_map_objective_canonical_tags(text, tag):
    assert g._guess_tag(text) == tag


def test_all_rework_plain_header_becomes_reworked_mechanic():
    lines = ['\nW(plain_header("Lifesteal"))', 'W(ul_open())',
             'W(li("a", t("REWORK")))', 'W(li("b", t("REWORK")))', 'W(li("c", t("REWORK")))',
             'W(li("Holding Alt shows more", t("QoL")))', 'W(ul_close())', '\nW(section("Next"))']
    out = g._postprocess_new_block_label(lines)
    assert out[0] == '\nW(plain_header("Lifesteal", new="Reworked mechanic"))'


def test_nested_child_keeps_its_own_valve_info():
    notes = [{"indent_level": 1, "note": "The following sources do not provide any lifesteal"},
             {"indent_level": 2, "note": "Reflected damage ", "info": "Example: Blade Mail return damage"}]
    txt = g._nested_info_text(notes, 1, [1])
    assert 'Reflected damage <span class="pop-note">(Example: Blade Mail return damage)</span>' == txt


def test_multi_line_info_popup_is_a_bulleted_list():
    from patch.elements import info_tip
    html = info_tip("first<br>second<br>&nbsp;&nbsp;– deeper")
    assert html.count('class="pop-li"') == 2 and 'class="pop-li pop-sub">deeper' in html
    assert 'pop-li' not in info_tip("just one line")


def test_new_item_becomes_card_price_bonuses_then_abilities():
    lines = ['W(item_header("Crella\'s Crozier", new="New Magical Item"))', 'W(ul_open())',
             'W(li("Passive: Putrefaction Aura. Reduces health restoration", t("MISC")))',
             'W(li("Requires Ghost Scepter (1500), Soul Booster (3000), and a recipe (300). Total cost: 4800g", t("MISC")))',
             'W(li("Provides +6 All Attributes, +450 Health, and +450 Mana", t("MISC")))',
             'W(ul_close())']
    out = g._postprocess_new_item_card(lines)
    assert out[1] == 'W(components(("Ghost Scepter", 1500), ("Soul Booster", 3000), recipe=("Recipe", 300), total=4800))'
    assert out[2] == 'W(provides("+6 All Attributes, +450 Health, +450 Mana"))'
    assert out[3:] == ['W(ul_open())', 'W(li("Passive: Putrefaction Aura. Reduces health restoration", t("NEW")))', 'W(ul_close())']


def test_new_item_without_bonuses_has_no_bonus_row_and_gets_kv_price():
    lines = ['W(item_header("Orb of Frost", new="New Basic Equipment Item"))', 'W(ul_open())',
             'W(li("Provides no bonuses", t("MISC")))', 'W(li("Passive: Frost. Slows", t("MISC")))', 'W(ul_close())']
    out = g._postprocess_new_item_card(lines, "7.38")
    assert out[1] == 'W(item_cost(250))'
    assert not any("no bonuses" in ln for ln in out)


@pytest.mark.parametrize("text,tag", [
    ("No longer unbreakable", "NEW"),
    ("Scrumptious now restores 3000 health and 2000 mana when consumed", "NEW"),
    ("Scrumptious' Savory Shield now has a 5 minute duration", "REWORK"),
    ("Scrumptious can no longer be cast on an ally to give them the buff. However, item is still fully shareable", "REWORK"),
    ("No longer refills when carrier has a lingering fountain regeneration buff", "DEL"),
    ("Poison Attack now has a 9s cooldown", "NEW"),
    ("Roshan's knockback now has a 2s cooldown before it can be applied to the same unit again", "NERF"),
])
def test_item_and_creep_canonical_tags_738(text, tag):
    assert g._guess_tag(text) == tag


def test_creep_level_change_is_misc_not_a_percent_badge():
    assert g._emit_li("Level increased from 5 to 6") == 'W(li("Level increased from 5 to 6", t("MISC")))'


def test_no_longer_stacks_is_del():
    assert g._guess_tag("No longer stacks with itself") == "DEL"
