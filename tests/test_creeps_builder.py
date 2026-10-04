"""Neutral Stats / Neutral Abilities builder pieces, tested on their own.

2026-10-05: save_creeps_html() was one 2459-line function with ~50 nested helpers; it is now
split into module-level functions (builders/creeps.py + creeps_common / creeps_history /
creeps_abilities). These tests pin the pieces with small synthetic inputs.
"""
from builders import creeps, creeps_abilities as ua, creeps_common as cc, creeps_history as ch
from builders import entity_changes as ec


def _hist(patches=(), dates=None, raw=None, abil=None):
    return ch.StatHistory(patches=tuple(patches), patch_dates=dates or {},
                          raw_by_patch=raw or {}, abil_by_patch=abil or {})


def test_numbers_use_a_decimal_comma():
    assert cc.fmt_num(0.9) == '0,9'
    assert cc.fmt_num('12') == '12'
    assert cc.fmt_regen(1.5) == '1,50'
    assert cc.fmt_regen(0) == '0'


def test_value_history_records_each_change():
    hist = _hist(('7.08', '7.09', '7.10'), {'7.09': '01.01.2018'},
                 {'StatusHealth': {'7.08': {'u': 500}, '7.09': {'u': 550}, '7.10': {'u': 550}}})
    assert ch.value_history(hist, 'u', ch.COL_HIST['hp']) == [('7.09', '01.01.2018', '500', '550')]
    assert ch.value_history(hist, None, ch.COL_HIST['hp']) == []


def test_ability_changelog_skips_the_baseline_and_tracks_identity():
    alive = {v: {'u': 500} for v in ('7.08', '7.09', '7.10')}
    hist = _hist(('7.08', '7.09', '7.10'), {},
                 {'StatusHealth': alive,
                  'Ability1': {v: {'u': 'a_slug'} for v in alive},
                  'Ability2': {'7.10': {'u': 'b_slug'}}},
                 {'7.08': {'a_slug': {'AbilityCooldown': '10'}},
                  '7.09': {'a_slug': {'AbilityCooldown': '8'}},
                  '7.10': {'a_slug': {'AbilityCooldown': '8'}}})
    # cooldown drop = buff → polarity 'lo'; present since the first patch → no ADDED entry
    assert ch.ability_changelog(hist, {}, 'u', 0) == [('7.09', '', 'F', 'Cooldown', '10', '8', 'lo')]
    # an ability that first appears mid-history reads as ADDED
    assert ch.ability_changelog(hist, {}, 'u', 1) == [('7.10', '', 'A', 'B Slug')]


def test_row_data_shows_self_aura_and_skips_marker_abilities():
    npc = {'StatusHealth': '600', 'AttackDamageMin': '30', 'AttackDamageMax': '33',
           'ArmorPhysical': '4', 'Ability1': 'neutral_upgrade', 'Ability2': 'alpha_wolf_critical_strike'}
    src = creeps.CreepSources(units={}, npc_data={'npc_dota_neutral_alpha_wolf': npc},
                              abil_slim={'alpha_wolf_critical_strike': {'dname': 'Critical Strike'}},
                              hist=_hist())
    d = creeps._row_data('npc_dota_neutral_alpha_wolf', 'alpha', src)
    assert (d['dmg_min'], d['dmg_max'], d['dmg_avg']) == ('30 (36)', '33 (40)', '32 (38)')  # Command Aura x1.2
    assert (d['hp_regen'], d['mp'], d['mp_regen']) == ('0', '-', '-')
    assert (d['armor'], d['armor_pct'], d['camp']) == ('4', '19%', 'mid')
    assert (d['ability1'], d['ability1_slug'], d['ability2']) == ('Critical Strike', 'alpha_wolf_critical_strike', '')


def test_build_rows_skips_legend_and_lane_rows_but_keeps_their_level():
    header = ['', 'Ур.', '', 'createhero', '', 'Тип атаки']
    rows = [header,
            ['', '1', 'ТИР 1', '', '', ''],
            ['', '', 'Kobold', 'kobold', '', 'Обычный'],
            ['', '2', '', 'ranged', '', ''],
            ['', '', '', 'gnoll', '', 'Проникающий*']]
    src = creeps.CreepSources(units={}, npc_data={}, abil_slim={}, hist=_hist())
    out = creeps.build_rows(rows, src)
    assert [(r['data']['name'], r['level'], r['tier_break'], r['data']['attack_type']) for r in out] == [
        ('Kobold', '1', True, 'Default'), ('Gnoll Assassin', '2', True, 'Piercing')]


def test_abil_props_aura_defaults_and_manual_overrides():
    p = ua.abil_props('x_aura', {'x_aura': {'av_bonus_armor': '2 3 4 5'}})
    assert (p['type'], p['duration'], p['stackable'], p['lvl_up']) == ('Aura', '0.5', 'No', 'Yes')
    p = ua.abil_props('dark_troll_warlord_raise_dead', {})
    assert p['manacost'] == '50' and 'effect' in p['_leveled'] and '_force_leveled' not in p


def test_prop_cell_collapses_level_runs_and_adds_bkb_tip():
    cell = ua.prop_cell('effect', '+20/25/30/40 gold per minute', {'_leveled': {'effect'}})
    assert 'class="ua-effect leveled"' in cell and '>+20→40</button> gold per minute' in cell
    cell = ua.prop_cell('through_bkb', 'no', {'_through_bkb_tip': 'Tip "x"'})
    assert 'data-sort="1"' in cell and 'cell-wrap' in cell and 'Tip &quot;x&quot;' in cell


def test_entity_changes_still_reads_the_creep_tables():
    """Unit Changes parses CREEP_CAMP / CREEP_NAME_TO_NPC / CREEP_DISPLAY_NAMES out of
    builders/creeps.py's source text — moving them out of that file breaks it silently."""
    camp = ec._unit_camp_map()
    assert camp['npc_dota_neutral_kobold'] == 'Small'
    assert camp['npc_dota_neutral_centaur_outrunner'] == 'Medium'   # ['mid', 'big'] → smallest
    every_neutral = {creeps.CREEP_NAME_TO_NPC[k] for k in creeps.CREEP_CAMP
                     if creeps.CREEP_NAME_TO_NPC.get(k, '').startswith('npc_dota_neutral_')}
    assert every_neutral <= set(camp)                                 # the whole table, not a prefix of it
    assert ec._creep_display_names()['npc_dota_neutral_polar_furbolg_ursa_warrior'] == 'Hellbear'
