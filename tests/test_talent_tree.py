"""Talent tree icon: the changed twigs light up on the side the game shows them (owner 2026-09-26)."""
from patch import talent_tree as tt


def test_first_talent_of_a_pair_is_the_right_twig():
    # Liquipedia, Abaddon 7.41: level 10 right = Curse of Avernus DPS, left = Aphotic Shield regen
    right, left = tt.talent_slots("7.41", "abaddon")[10]
    assert "curse" in right and "aphotic" in left


def test_abaddon_741_swaps_light_right_10_and_15():
    rows = ["Level 10 Talent: +10% Withering Mist Health Restoration Reduction replaced with +25 Curse of Avernus DPS",
            "Level 15 Talent: +40 Curse of Avernus DPS replaced with -10s Borrowed Time Cooldown"]
    assert tt.changed_branches("7.41", "abaddon", rows) == {"10r", "15r"}


def test_old_patch_uses_that_patchs_meaning_of_a_reused_slug():
    # sniper_5 was Shrapnel Slow in 7.26c (level 15 left); today it is Take Aim range
    assert tt.changed_branches("7.26c", "sniper", ["Level 15 Talent: reduced from +16% Shrapnel Slow to +14%"]) == {"15l"}


def test_unplaced_row_keeps_the_plain_icon():
    html = ('<div class="entity hero-entity" id="dyn-hero-axe">\n  <div class="entity-icon hero-icon"><a href="x">'
            '<img src="../icons/_t/heroes/axe.webp"></a></div></div>'
            '<div class="ability-block talents-block"><div class="ability-icon-wrap">'
            '<img src="../icons/misc/talents.svg" class="ability-icon-img"></div>\n<ul class="changes">'
            '<li><span class="row-text">Level 10 Talent: something unknown</span></li></ul>')
    assert tt.light_talent_trees(html, "7.41f") == html


def test_placed_row_gets_the_gold_overlay():
    html = ('<div class="entity hero-entity" id="dyn-hero-abaddon">\n  <div class="entity-icon hero-icon"><a href="x">'
            '<img src="../icons/_t/heroes/abaddon.webp"></a></div></div>'
            '<div class="ability-block talents-block"><div class="ability-icon-wrap">'
            '<img src="../icons/misc/talents.svg" class="ability-icon-img"></div>\n<ul class="changes">'
            '<li><span class="row-text">Level 15 Talent: +40 Curse of Avernus DPS replaced with -10s Borrowed Time '
            'Cooldown</span></li></ul>')
    out = tt.light_talent_trees(html, "7.41")
    assert 'class="ability-icon-img ttree"' in out and "talents_gold.svg" in out
    assert tt.BRANCH_POLYS["15r"] in out and tt.BRANCH_POLYS["15l"] not in out
    assert 'data-tt="15r"' in out and 'data-b="15r"' in out        # a filter can switch this twig off
