"""Neutral Abilities companion page (neutral_abilities.html) — built in the
same run as Neutral Stats by builders/creeps.py.

One row per (creep, ability), mirroring the Creeps Table's Lvl + Unit
identity columns (Unit shows just the hover-zoom icon). Property columns
come from the CURRENT patch's npc_abilities.json (av_* + standard KV
fields) so a patch that changes an ability updates here automatically.
Effect / Effect 2 / Effect 3 and Stackable aren't present in our data
files, so they render blank (would need a manual/external source).
"""
import os as _os
import re

import builders.site_common as _site
from builders.creeps_common import (
    ABILITY_COLS, DASH, abil_icon_html, attr_esc, esc, has_abil_icon,
    page_shell, write_dist,
)

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

# Through-BKB lookup — kept separate from ABIL_MANUAL so the Through BKB
# column has a single source of truth. Anything not listed renders "—".
THROUGH_BKB = {
    # Pierces magic immunity:
    'spawnlord_master_freeze':              'yes',  # Petrify
    # Pierces magic immunity (additional yes-cases):
    'forest_troll_high_priest_heal':        'yes',  # Heal
    'frogmen_water_bubble_small':           'yes',  # Water Bubble (Small)
    'frogmen_water_bubble_medium':          'yes',  # Water Bubble (Medium)
    'frogmen_water_bubble_large':           'yes',  # Water Bubble (Large)
    'big_thunder_lizard_frenzy':            'yes',  # Frenzy
    # Blocked by BKB:
    'enraged_wildkin_tornado':              'no',   # Tornado
    'kobold_disarm':                        'no',   # Steal Weapon
    'berserker_troll_break':                'no',   # Break
    'gnoll_assassin_envenomed_weapon':      'no',   # Envenomed Weapon
    'fel_beast_haunt':                      'no',   # Vex
    'ogre_bruiser_ogre_smash':              'no',   # Ogre Smash!
    'satyr_trickster_purge':                'no',   # Purge
    'giant_wolf_intimidate':                'no',   # Intimidate
    'dark_troll_warlord_ensnare':           'no',   # Ensnare
    'ghost_frost_attack':                   'no',   # Frost Attack
    'black_drake_magic_amplification_aura': 'no',   # Magic Amplification Aura
    'ogre_magi_frost_armor':                'no',   # Ice Armor
    'mud_golem_hurl_boulder':               'no',   # Hurl Boulder
    'frogmen_arm_of_the_deep':              'no',   # Arm of the Deep
    'frogmen_tendrils_of_the_deep':         'no',   # Tendrils of the Deep
    'satyr_soulstealer_mana_burn':          'no',   # Mana Burn
    'centaur_khan_war_stomp':               'no',   # War Stomp
    'polar_furbolg_ursa_warrior_thunder_clap': 'no',  # Thunder Clap
    'enraged_wildkin_hurricane':            'no',   # Hurricane
    'warpine_raider_seed_shot':             'no',   # Seed Shot
    'frogmen_congregation_of_the_deep':     'no',   # Congregations of the Deep
    'ancient_rock_golem_weakening_aura':    'no',   # Weakening Aura
    'satyr_hellcaller_shockwave':           'no',   # Shockwave
    'spawnlord_master_stomp':               'no',   # Desecrate
    'black_dragon_fireball':                'no',   # Fireball
    'harpy_storm_chain_lightning':          'no',   # Chain Lightning
    'big_thunder_lizard_slam':              'no',   # Slam
    'ice_shaman_incendiary_bomb':           'no',   # Icefire Bomb
}
# Per-cell `?` hints in the Through BKB column. Keyed by ability slug.
THROUGH_BKB_TIPS = {
    'ogre_magi_frost_armor': (
        'Can be cast on an ally under BKB, '
        "but the slow on an enemy under BKB doesn't work"),
    'forest_troll_high_priest_heal':
        'Can be cast on an ally under BKB',
    'satyr_trickster_purge': (
        'Can be cast on an ally under BKB, '
        "but the effect on an enemy under BKB doesn't work"),
    'enraged_wildkin_hurricane': (
        'Can be cast on an ally under BKB, '
        "but the effect on an enemy under BKB doesn't work"),
}

DMG_TYPE = {'DAMAGE_TYPE_MAGICAL': 'Magical', 'DAMAGE_TYPE_PHYSICAL': 'Physical',
            'DAMAGE_TYPE_PURE': 'Pure', 'DAMAGE_TYPE_HP_REMOVAL': 'HP Removal'}
DISPEL = {'SPELL_DISPELLABLE_YES': 'Yes', 'SPELL_DISPELLABLE_YES_STRONG': 'Strong only',
          'SPELL_DISPELLABLE_NO': 'No'}
# Aura Stack column: which auras stack with another copy of the same aura.
# Only these stack (green check); other auras don't (red x); non-auras get
# a dash. Rally has no 'aura' in its slug but behaves as a stacking aura.
AURA_STACK_YES = {'black_dragon_dragonhide_aura', 'hill_troll_rally'}
# Manual dispellable values for abilities whose KV lacks SpellDispellableType
# (dispellability lives in their modifier/code). User-supplied.
DISPEL_MANUAL = {
    'berserker_troll_break': 'Yes',        # Break
    'fel_beast_haunt': 'Yes',              # Vex
    'dark_troll_warlord_ensnare': 'Yes',   # Ensnare
    'ogre_magi_frost_armor': 'Yes',        # Ice Armor
    'furbolg_enrage_attack_speed': 'Yes',  # Death Throe: Rush
    'furbolg_enrage_damage': 'Yes',        # Death Throe: Power
    'warpine_raider_seed_shot': 'Yes',     # Seed Shot
    'spawnlord_master_freeze': 'Yes',      # Petrify
    'kobold_disarm': 'Yes',                # Steal Weapon
    'giant_wolf_intimidate': 'Yes',        # Intimidate
    'harpy_scout_take_off': 'No',          # Take Off
    'black_dragon_fireball': 'No',         # Fireball
}
# Single merged Type column — fully hand-curated (replaces the old Type +
# Damage Type pair). Keyed by ability slug; anything not listed → dash.
TYPE_MANUAL = {
    'enraged_wildkin_tornado': 'Active, Magic Damage',
    'kobold_tunneler_prospecting': 'Passive, Buff Aura',
    'kobold_disarm': 'Passive, Debuff',
    'hill_troll_rally': 'Passive, Buff Aura',
    'berserker_troll_break': 'Passive, Debuff',
    'gnoll_assassin_envenomed_weapon': 'Passive, HP Removal Damage',
    'fel_beast_haunt': 'Active, Debuff',
    'ogre_bruiser_ogre_smash': 'Active, Magic Damage',
    'kobold_taskmaster_speed_aura': 'Passive, Buff Aura',
    'forest_troll_high_priest_heal_amp_aura': 'Passive, Buff Aura',
    'mudgolem_cloak_aura': 'Passive, Buff Aura',
    'frogmen_riverborn_aura': 'Passive, Buff Aura',
    'giant_wolf_intimidate': 'Active, Debuff',
    'dark_troll_warlord_ensnare': 'Active, Debuff',
    'ghost_frost_attack': 'Passive, Debuff',
    'harpy_storm_chain_lightning': 'Active, Magic Damage',
    'black_drake_magic_amplification_aura': 'Passive, Debuff Aura',
    'spawnlord_aura': 'Passive, Buff Aura',
    'ogre_magi_frost_armor': 'Active, Buff',
    'mud_golem_hurl_boulder': 'Active, Magic Damage',
    'frogmen_arm_of_the_deep': 'Active, Magic Damage',
    'frogmen_tendrils_of_the_deep': 'Active, Magic Damage',
    'frogmen_water_bubble_small': 'Active, Buff',
    'frogmen_water_bubble_medium': 'Active, Buff',
    'frogmen_water_bubble_large': 'Active, Buff',
    'centaur_khan_endurance_aura': 'Passive, Buff Aura',
    'furbolg_enrage_attack_speed': 'Passive, Buff',
    'satyr_soulstealer_mana_burn': 'Active, Magic Damage',
    'forest_troll_high_priest_mana_aura': 'Passive, Buff Aura',
    'alpha_wolf_critical_strike': 'Passive, Physical Damage',
    'alpha_wolf_command_aura': 'Passive, Buff Aura',
    'centaur_khan_war_stomp': 'Active, Magic Damage',
    'polar_furbolg_ursa_warrior_thunder_clap': 'Active, Magic Damage',
    'furbolg_enrage_damage': 'Passive, Buff',
    'enraged_wildkin_toughness_aura': 'Passive, Buff Aura',
    'warpine_raider_seed_shot': 'Active, Magic Damage',
    'frogmen_congregation_of_the_deep': 'Active, Magic Damage',
    'ancient_rock_golem_weakening_aura': 'Passive, Debuff Aura',
    'frostbitten_golem_time_warp_aura': 'Passive, Buff Aura',
    'big_thunder_lizard_wardrums_aura': 'Passive, Buff Aura',
    'satyr_hellcaller_shockwave': 'Active, Magic Damage',
    'satyr_hellcaller_unholy_aura': 'Passive, Buff Aura',
    'spawnlord_master_stomp': 'Active, Physical Damage',
    'spawnlord_master_freeze': 'Active, Physical Damage',
    'black_dragon_fireball': 'Active, Magic Damage',
    'black_dragon_splash_attack': 'Passive, Physical Damage',
    'black_dragon_dragonhide_aura': 'Passive, Buff Aura',
    'granite_golem_hp_aura': 'Passive, Buff Aura',
    'big_thunder_lizard_slam': 'Active, Magic Damage',
    'big_thunder_lizard_frenzy': 'Active, Buff',
    'ice_shaman_incendiary_bomb': 'Active, Magic Damage',
    'dark_troll_warlord_raise_dead': 'Active, Summon',
}
# Abilities whose hand-curated Type says "Aura" even without 'aura' in the slug.
MANUAL_AURAS = frozenset(s for s, t in TYPE_MANUAL.items() if 'Aura' in t)
# (legacy) Damage Type curation — no longer rendered as its own column.
DMGTYPE_MANUAL = {
    'gnoll_assassin_envenomed_weapon': 'HP Removal',
    'spawnlord_master_stomp': 'Physical',      # Desecrate
    'spawnlord_master_freeze': 'Physical',     # Petrify
    'black_dragon_splash_attack': 'Physical',
    'alpha_wolf_critical_strike': 'Physical',
    'enraged_wildkin_tornado': 'Magical',
    'ogre_bruiser_ogre_smash': 'Magical',
    'harpy_storm_chain_lightning': 'Magical',
    'mud_golem_hurl_boulder': 'Magical',
    'frogmen_arm_of_the_deep': 'Magical',
    'frogmen_tendrils_of_the_deep': 'Magical',
    'satyr_soulstealer_mana_burn': 'Magical',
    'centaur_khan_war_stomp': 'Magical',
    'polar_furbolg_ursa_warrior_thunder_clap': 'Magical',
    'warpine_raider_seed_shot': 'Magical',
    'frogmen_congregation_of_the_deep': 'Magical',
    'satyr_hellcaller_shockwave': 'Magical',
    'black_dragon_fireball': 'Magical',
    'big_thunder_lizard_slam': 'Magical',
    'ice_shaman_incendiary_bomb': 'Magical',
}


def _f1(val):
    s = str(val).strip()
    return s.split()[0] if s else ''


def _prog(val):
    """Full per-level progression as '40/36/32/26'; trims trailing .0."""
    out = []
    for t in str(val).split():
        try:
            f = float(t)
            out.append(str(int(f)) if f == int(f) else str(f))
        except ValueError:
            out.append(t)
    return '/'.join(out)


def _qhint(tip):
    """Framed `?` badge with a hover tooltip. `tip` must already be escaped."""
    return (f'<span class="qhint" tabindex="0" role="button" '
            f'aria-label="{tip}" data-tooltip="{tip}">?</span>')


# Manual columns not present in our data files (effect text + aura
# stackability). Filled by hand from the legacy creep-spreadsheet
# (Эффект / Второй эффект / Третий эффект columns); keyed by ability
# slug. Anything here overrides the auto-derived blanks.
_DMG_NUM_RE = re.compile(r'[\d./\-–]*\d+[\d./\-–]*')


def _dmg_color_html(text: str) -> str:
    """Wrap numeric runs in `.dmg-num` so the damage-type colour paints
    only the numbers, not the words ("per sec.", "(юниты)", "+ 250% Int")."""
    return _DMG_NUM_RE.sub(
        lambda m: f'<span class="dmg-num">{m.group()}</span>', text)


def _val_qhint(text: str, tip: str) -> str:
    """Raw-HTML cell value: text + framed `?` badge with tooltip. Generic
    version (no number-colour wrap) — for non-Damage columns like Duration."""
    return ('\x01<span class="cell-wrap">' + esc(text) +
            _qhint(esc(tip)) + '</span>')


def _dmg_qhint(text: str, tip: str) -> str:
    """Raw-HTML damage cell: value + framed `?` badge with tooltip."""
    return ('\x01<span class="dmg-wrap">' + _dmg_color_html(text) +
            _qhint(esc(tip)) + '</span>')


ABIL_MANUAL = {
    'enraged_wildkin_tornado': {
        # Wildkin's `enraged_wildkin_tornado` is only the CAST. The actual
        # tornado unit's damage/AoE live in `tornado_tempest`, which isn't
        # in our extracted KV — fill from the legacy sheet by hand.
        'damage': _dmg_qhint(
            '15-45 per sec.',
            "Depends on the proximity to the Tornado's epicenter"),
        'aoe': '150–600',
        'duration': _val_qhint(
            '10 (15)',
            "Channeling duration is 10 seconds + 5 if it's ended or cancelled"),
        'as_effect': '-15%', 'ms_effect': '-15%',
        'effect': 'AoE damage',
        'effect2': '300/300 vision',
        'effect3': 'Slow'},
    'kobold_tunneler_prospecting': {
        'effect': '+20/25/30/40 gold per minute'},
    'kobold_disarm': {
        'effect': 'Disarms 1 target', 'effect2': 'Requires 3 attacks'},
    'hill_troll_rally': {
        'effect': '+2 attack damage to allies'},
    'berserker_troll_break': {
        'effect': 'Break on 1 target'},
    'gnoll_assassin_envenomed_weapon': {
        # HP Removal is rare enough on neutrals to flag in the cell itself
        # (it bypasses magic immunity, ignores magic resist, can't kill etc).
        'damage': _dmg_qhint('0/20/40/80 per sec.', 'HP Removal damage type'),
        'duration': _val_qhint(
            '2 or 20', 'Lasts much longer on creeps (20)'),
        'effect': 'Damage over time',
        'effect2': 'HP regeneration reduction: 75/80/85/90%'},
    'fel_beast_haunt': {
        'effect': 'Silences 1 target',
        'effect2': 'Projectile Speed is 500/600/700/800'},
    'harpy_scout_take_off': {
        # Toggle ability: 20 to activate, then 4% of max MP per second
        # while active (av_cost_per_second:"4").
        'manacost': _val_qhint(
            '20 + 4%',
            'Activation cost 20, plus 4% of max MP per second while active'),
        'ms_effect': _val_qhint(
            '-50/-40/-30/-10%',
            'The unit itself is slowed while the ability is active'),
        'effect': 'Gives flying movement with 1200/800 vision',
        'effect2': 'Slows itself while active'},
    'ogre_bruiser_ogre_smash': {
        # av_damage_pct:"8" — bonus 8% of target's current HP, not surfaced
        # in any other column.
        'damage': _dmg_qhint(
            '200/250/300/400 + 8%',
            "Adds 8% of the target's current HP to the damage"),
        'effect': 'AoE damage', 'effect2': 'Stun'},
    'kobold_taskmaster_speed_aura': {
        'ms_effect': '+12/13/14/16%',
        'effect': 'Movement speed bonus'},
    'forest_troll_high_priest_heal_amp_aura': {
        'effect': 'Increases healing on allies by 15%'},
    'forest_troll_high_priest_heal': {
        'effect': 'Heals +100 HP'},
    'mudgolem_cloak_aura': {
        'effect': 'Heroes magic resistance bonus: +10/12/14/16%',
        'effect2': 'Creeps magic resistance bonus: +20/24/28/32%'},
    'frogmen_riverborn_aura': {
        'ms_effect': '+10/12/14/16%',
        'effect': 'Outgoing damage +10/12/14/16%'},
    'satyr_trickster_purge': {
        # Slow decays from -50% to -10% over 5 seconds; not in any av_* field.
        'ms_effect': _val_qhint(
            '-50% to -10%',
            'Movement slow decays by 10% each second over 5 seconds'),
        'effect': 'Dispel', 'effect2': 'Movement slow'},
    'giant_wolf_intimidate': {
        'effect': 'Reduces attack damage by 60%'},
    'dark_troll_warlord_ensnare': {
        # No entry in <latest>/npc_abilities.json — fill from in-game tooltip.
        'manacost': '75', 'cooldown': '15', 'duration': '1.75',
        'cast_range': '550/625/700/825',
        'effect': 'Roots the target', 'effect2': 'True Sight on the target'},
    'ghost_frost_attack': {
        'effect': 'Slows both attack and movement speed'},
    'harpy_storm_chain_lightning': {
        # KV has AbilityManaCost 60, but in-game tooltip / user verifies 50.
        'manacost': '50',
        # av_initial_damage carries the bounce damage; av_damage_percent_loss
        # is the per-bounce falloff (25/20/15/10%).
        'damage': _dmg_qhint(
            '120/170/220/270',
            'Each bounce reduces damage by 25/20/15/10%'),
        'cast_range': _val_qhint('900', 'Bounces range is 500'),
        'effect': 'Damage to 4 targets'},
    'black_drake_magic_amplification_aura': {
        'effect': _val_qhint(
            'Outgoing spell damage: 5/6/7/9%',
            "Amplifies any damage type if it's spell damage")},
    'spawnlord_aura': {
        'effect': '+9/10/11/12% lifesteal',
        'effect2': '+9/10/11/12 HP regen'},
    'ogre_magi_frost_armor': {
        # Slug missing from <latest>/npc_abilities.json — fill from in-game.
        'manacost': '40', 'cooldown': '5', 'duration': '45',
        'cast_range': '800',
        'as_effect': '-22/24/26/30%', 'ms_effect': '-22/24/26/30%',
        'effect': '+4/5/6/8 armor',
        'effect2': _val_qhint(
            'Shield slows attackers on hit',
            'The slow applies to towers as well')},
    'mud_golem_hurl_boulder': {
        # 75 hero / 150 creep; pretty form with hint icon for the split.
        'damage': _dmg_qhint(
            '75 or 150', 'Deals double the damage to creeps (150)'),
        'effect': 'Single target stun'},
    'mud_golem_rock_destroy': {
        # av_radius describes the death stun (internal tech) — blank to
        # match the old sheet. av_duration in KV is 2 (the death stun),
        # but the SHARD LIFETIME the user cares about is 60s.
        'aoe': '', 'duration': '60',
        # Property 1: spawns-on-death + qhint with shard tier stats. Each
        # row of the qhint is its own .qh-line so the tooltip renders
        # multiline. Marked `leveled` because the qhint shows progressions.
        'effect': (
            '\x01<span class="cell-wrap">'
            'Spawns Golems on death 2/2/3/3'
            '<span class="qhint" tabindex="0" role="button" '
            'aria-label="Shard stats per tier" data-tooltip="'
            '&lt;div class=&quot;qh-line&quot;&gt;HP = 250/280/310/370&lt;/div&gt;'
            '&lt;div class=&quot;qh-line&quot;&gt;Attack damage = 12/16/20/28&lt;/div&gt;'
            '&lt;div class=&quot;qh-line&quot;&gt;Quantity = 2/2/3/3&lt;/div&gt;'
            "&lt;div class=&quot;qh-line&quot;&gt;Hurl Boulder is the same as Mud Golem's&lt;/div&gt;"
            '&lt;div class=&quot;qh-line&quot;&gt;When Devoured, Doom will also spawn 2/2/3/3 small Golems but with his own model&lt;/div&gt;'
            '">?</span></span>'),
        'effect2': (
            '\x01Golems have <a class="ua-inline-link" '
            'href="neutral_abilities.html#mud-mud_golem_hurl_boulder">'
            'Hurl Boulder</a>'),
    },
    'frogmen_arm_of_the_deep': {
        # av_radius missing in KV; the actual stun radius is the
        # av_projectile_width (100). Tentacles also extend +100 further.
        'aoe': '100',
        'cast_range': _val_qhint('275', '375 with tentacles radius'),
        'effect': 'AoE stun', 'effect2': 'AoE damage'},
    'frogmen_tendrils_of_the_deep': {
        'aoe': '100',
        'cast_range': _val_qhint('300', '400 with tentacles radius'),
        'effect': 'AoE stun', 'effect2': 'AoE damage'},
    'frogmen_water_bubble_small': {
        'effect': '100/120/140/160 magic barrier'},
    'frogmen_water_bubble_medium': {
        'effect': '150/180/210/240 magic barrier'},
    'centaur_khan_endurance_aura': {
        'effect': 'Attack speed bonus'},
    'furbolg_enrage_attack_speed': {
        'effect': 'Attack speed bonus over time'},
    'satyr_soulstealer_mana_burn': {
        # Burn = flat + Int multiplier. Raw HTML so we can inline the
        # intelligence icon; sentinel `\x01` lets prop_cell skip esc.
        # Only the flat amount is coloured (it deals damage of the cell's
        # type). The Int-multiplier tail stays default colour and sits on
        # a second line so the cell can stay narrow.
        'damage': ('\x01<span class="dmg-wrap dmg-multiline">'
                   '<span class="dmg-num">20/25/30/35</span>'
                   '<span class="dmg-line2">+ 200/250/350/400%'
                   '<img class="stat-ico" src="icons/intelligence.webp" '
                   'alt="Int"></span></span>'),
        'effect': 'Mana burn', 'effect2': 'Damage for burnt mana'},
    'forest_troll_high_priest_mana_aura': {
        'effect': '2 MP/sec regen'},
    'alpha_wolf_command_aura': {
        'effect': '+20% damage increase'},
    'alpha_wolf_critical_strike': {
        'effect': '20% chance to crit for 200/225/250/300%'},
    'centaur_khan_war_stomp': {
        'duration': _val_qhint(
            '1.6 or 3',
            'Lasts longer on creeps (3)'),
        'effect': 'AoE stun', 'effect2': 'AoE damage'},
    'polar_furbolg_ursa_warrior_thunder_clap': {
        'effect': 'AoE damage', 'effect2': 'AoE slow'},
    'furbolg_enrage_damage': {
        'effect': '+60% damage increase over time'},
    'enraged_wildkin_toughness_aura': {
        'effect': '+3 armor'},
    'enraged_wildkin_hurricane': {
        # No av_duration in KV; the knockback travel time is fixed at 0.5s.
        'duration': '0.5',
        'effect': 'Pushes a unit in the vector-targeted direction'},
    'warpine_raider_seed_shot': {
        'cast_range': _val_qhint('575', 'Bounces range is 500'),
        'ms_effect': '-100%',
        'effect': 'Damage to 4/6/8/12 targets',
        'effect2': 'Movement slow'},
    'frogmen_congregation_of_the_deep': {
        # AbilityCastRange=0 (self-cast); effective tentacle reach is the
        # av_range (300) +100 spread = 400.
        'aoe': '100',
        'cast_range': _val_qhint('300', '400 with tentacles radius'),
        'effect': 'AoE stun', 'effect2': 'AoE damage'},
    'ancient_rock_golem_weakening_aura': {
        'effect': '-3/-4/-5/-6 armor'},
    'frostbitten_golem_time_warp_aura': {
        'effect': '8/9/10/11% cooldown reduction'},
    'big_thunder_lizard_wardrums_aura': {
        'effect': 'Attack speed bonus',
        'effect2': 'Accuracy 40/43/46/51%'},
    'frogmen_water_bubble_large': {
        'effect': '210/240/270/300 magic barrier',
        'effect2': '50% of the barrier burst heals the target'},
    'satyr_hellcaller_unholy_aura': {
        'effect': '+3/5/7/11 HP/sec regen'},
    'satyr_hellcaller_shockwave': {
        # av_radius_start:"180", av_radius_end:"200" — cone widens.
        # av_distance:"1380" + av_speed:"900"; effective max range ~1580.
        'aoe': _val_qhint(
            '180', '200 at the end (cone widens along the path)'),
        'cast_range': _val_qhint(
            '700', 'Max travel distance is 1580'),
        'effect': 'AoE damage with a projectile'},
    'dark_troll_warlord_raise_dead': {
        'manacost': '50', 'cooldown': '20', 'duration': '35',
        '_force_leveled': ('effect',),
        'effect': (
            '\x01<span class="cell-wrap">Summons 3 <a class="ua-inline-link" '
            'href="neutral_stats.html#unit-skeleton_warrior">'
            'Skeleton Warriors</a>'
            '<span class="qhint" tabindex="0" role="button" '
            'aria-label="HP = 250/275/300/375, attack damage = 12/15/18/21" '
            'data-tooltip="HP = 250/275/300/375, attack damage = 12/15/18/21"'
            '>?</span></span>'),
        'effect2': (
            '\x01Skeletons have <a class="ua-inline-link" '
            'href="neutral_abilities.html#skeleton_warrior-hill_troll_rally">'
            'Rally</a> aura'),
    },
    'spawnlord_master_stomp': {
        'effect': 'Reduces base (white) armor by 50%',
        'effect2': 'Deals damage'},
    'spawnlord_master_freeze': {
        # av_damage:"100" with av_tick_interval:"0.1" is mislabeled in KV —
        # the in-game tooltip and old sheet both say 100/sec, so force it.
        'damage': _dmg_qhint(
            '100 per sec.', 'Deals damage in 0.1 seconds intervals'),
        'effect': 'Immobilizes', 'effect2': 'Damage over time'},
    'black_dragon_dragonhide_aura': {
        'effect': '+3 armor'},
    'black_dragon_fireball': {
        # av_damage:"85" is mislabeled — actual game effect is 85/sec
        # (total 722.5 over 8s); av_damage path takes priority, so override.
        'damage': '85 per sec.',
        'effect': 'AoE damage', 'effect2': 'Flying vision 300/300'},
    'black_dragon_splash_attack': {
        # av_range:"250" is the splash radius, but our auto-derive reads
        # av_radius only.
        'aoe': '250',
        'effect': 'AoE damage applied by attacks'},
    'granite_golem_hp_aura': {
        'effect': '+16/17/18/19% max HP increase'},
    'big_thunder_lizard_slam': {
        'duration': _val_qhint(
            '2/2.25/2.5/3 or 4',
            'Scaling duration on heroes. Lasts longer on creeps (4)'),
        'as_effect': '-60%',
        'effect': 'AoE damage', 'effect2': 'AoE slow'},
    'big_thunder_lizard_frenzy': {
        'effect': 'Attack speed bonus on 1 ally'},
    'ice_shaman_incendiary_bomb': {
        # av_burn_damage = 50, av_building_damage_pct = 25 → 12.5 to buildings.
        'damage': _dmg_qhint(
            '50 or 12.5 per sec.',
            'Deals 25% of the damage to structures (12.5/sec before resistances).'),
        'effect': 'Single target damage over time (works on buildings)'},
}


# ---- Ability properties (one row's values) ----

# Flat-AS bonuses keep no suffix; AS slow and all MS values are %.
_AS_FIELDS = (('av_speed_bonus', '+{}'), ('av_bonus_attack_speed', '+{}'),
              ('av_bonus_aspd', '+{}'), ('av_attackspeed_bonus', '+{}'),
              ('av_attackspeed_slow', '{}%'))
_MS_FIELDS = (('av_bonus_movement_speed', '+{}%'),
              ('av_movespeed_slow', '{}%'),
              ('av_move_speed_penalty', '{}%'))
# Mark cells that carry a per-level progression (3+ slash-separated
# numeric tokens) — surfaced as a blue outline when the Upgrades view
# toggle is on. 3+ tokens, not 2+, to avoid false positives like
# "1200/800 vision" (those are independent values, not a level table).
# Allow a leading minus so negative progressions (e.g. Frost Attack's
# "-25/-28/-31/-37" AS/MS slow) are detected as leveled.
_LVL_RE = re.compile(r'-?\d+(?:\.\d+)?(?:/-?\d+(?:\.\d+)?){2,}')


def _posnum(x):
    try:
        return float(_f1(x)) > 0
    except Exception:
        return False


def _abil_type(slug, g):
    """`g(field)` reads the ability's current KV ('' when missing)."""
    # Type resolution order:
    #  1) Aura — by slug token OR a TYPE_MANUAL entry containing "Aura".
    #  2) TYPE_MANUAL — first comma-separated word ("Active"/"Passive")
    #     overrides the heuristic for abilities where cd/mc presence is
    #     misleading (Break has a cd but is passive; Ice Armor lacks data).
    #  3) Heuristic — active if cd/mc/cast-range present, else passive.
    if 'aura' in slug or slug in MANUAL_AURAS:
        return 'Aura'
    if slug in TYPE_MANUAL:
        return TYPE_MANUAL[slug].split(',')[0].strip()
    if _posnum(g('AbilityCooldown')) or _posnum(g('AbilityManaCost')) or g('AbilityCastRange'):
        return 'Active'
    return 'Passive'


def _abil_damage(g):
    # Damage cell. Priority:
    #  1) hero/creep split when both av_damage and av_damage_creeps exist
    #     ("75 (герои) / 150 (крипы)" mirrors the legacy sheet)
    #  2) plain av_damage / AbilityDamage
    #  3) av_damage_per_second → "<v> per sec."
    #  4) av_burn_damage + av_burn_interval → "<v/interval> per sec."
    dmg = g('av_damage') or g('AbilityDamage')
    dmg_creeps = g('av_damage_creeps')
    if dmg and dmg_creeps:
        return f'{_prog(dmg)} (герои) / {_prog(dmg_creeps)} (крипы)'
    if dmg:
        return _prog(dmg)
    if g('av_damage_per_second'):
        return f'{_prog(g("av_damage_per_second"))} per sec.'
    if g('av_burn_damage'):
        interval = g('av_burn_interval')
        try:
            burn = float(_f1(g('av_burn_damage')))
            ivl = float(_f1(interval)) if interval else 1.0
            dps = burn / ivl if ivl else burn
            return f'{int(dps) if dps == int(dps) else dps} per sec.'
        except (ValueError, ZeroDivisionError):
            return _prog(g('av_burn_damage'))
    return ''


def _abil_duration(g):
    # Duration cell. Priority:
    #  1) hero/non-hero duration split  (Slam, Envenomed Weapon)
    #  2) hero/non-hero stun-duration split  (War Stomp)
    #  3) plain av_duration / AbilityDuration / av_hero_*  (single value)
    hd, nd = g('av_hero_duration'), g('av_non_hero_duration')
    hsd, nsd = g('av_hero_stun_duration'), g('av_non_hero_stun_duration')
    if hd and nd:
        return f'{_prog(hd)} (герои) / {_prog(nd)} (крипы)'
    if hsd and nsd:
        return f'{_prog(hsd)} (герои) / {_prog(nsd)} (крипы)'
    return _prog(g('av_duration') or g('AbilityDuration') or hd or hsd)


def _abil_cast_range(g):
    # Cast range cell — augment with jump/bounce range when present.
    cr = _prog(g('AbilityCastRange'))
    jr = g('av_jump_range') or g('av_bounce_range')
    if cr and jr:
        return f'{cr} ({_prog(jr)} у прыжков)'
    return cr


def _speed_effect(g, fields):
    return ' '.join(lbl.format(_prog(g(k))) for k, lbl in fields if g(k))


def _aura_stack(slug):
    if slug in AURA_STACK_YES:
        return 'Yes'
    if 'aura' in slug or slug in MANUAL_AURAS:
        return 'No'
    return ''


def _leveled_cells(props):
    """Keys of the cells whose visible text holds a per-level progression."""
    leveled = set()
    for k, v in props.items():
        if k.startswith('_'):
            continue
        if isinstance(v, str) and v.startswith('\x01'):
            text = re.sub(r'<[^>]+>', '', v[1:])
        else:
            text = str(v or '')
        if _LVL_RE.search(text):
            leveled.add(k)
    return leveled


def abil_props(slug, cur_ab):
    """Every property cell value for one ability. `cur_ab` is the current
    patch's npc_abilities data ({slug: {field: value}}); ABIL_MANUAL wins
    over the auto-derived values. Keys starting with '_' are render hints."""
    a = cur_ab.get(slug, {})

    def g(k):   # the ability's KV field, '' when missing
        return a.get(k, '')

    typ = _abil_type(slug, g)
    props = {
        'type': typ,
        'dmg_type': DMGTYPE_MANUAL.get(slug, ''),
        'damage': _abil_damage(g),
        'aoe': _prog(g('av_radius')),
        'manacost': _prog(g('AbilityManaCost')),
        'cooldown': _prog(g('AbilityCooldown')),
        'duration': _abil_duration(g),
        'cast_range': _abil_cast_range(g),
        'as_effect': _speed_effect(g, _AS_FIELDS),
        'ms_effect': _speed_effect(g, _MS_FIELDS),
        'effect': '', 'effect2': '', 'effect3': '',
        'dispel': DISPEL_MANUAL.get(slug) or DISPEL.get(g('SpellDispellableType'), ''),
        'through_bkb': THROUGH_BKB.get(slug, ''),
        '_through_bkb_tip': THROUGH_BKB_TIPS.get(slug, ''),
        'stackable': _aura_stack(slug),
        'lvl_up': 'Yes' if any(len(str(v).split()) > 1 for v in a.values()) else 'No',
    }
    # Every aura updates on a 0.5s tick (Valve convention); show it in the
    # Duration cell so it isn't confused with empty/instant abilities.
    if typ == 'Aura' and not props['duration']:
        props['duration'] = '0.5'
    props.update(ABIL_MANUAL.get(slug, {}))
    leveled = _leveled_cells(props)
    # Manual overrides can force cells to render as leveled even when the
    # visible text doesn't carry a slash-progression (e.g. "Summons 3 …"
    # with per-level HP/damage values surfaced via tooltip only).
    leveled.update(props.pop('_force_leveled', ()))
    props['_leveled'] = leveled
    return props


# ---- Table structure ----

UA_COLS = [
    ('lvl', 'Lvl'), ('unit', 'Unit'), ('ability', 'Ability'),
    ('type', 'Type'), ('damage', 'Damage'),
    ('manacost', 'Manacost'), ('cooldown', 'Cooldown'),
    ('duration', 'Duration'), ('cast_range', 'Cast Range'),
    ('aoe', 'Radius'), ('stackable', 'Aura Stack'),
    ('dispel', 'Dispellable'), ('through_bkb', 'Through BKB'),
    ('as_effect', 'AS Effect'), ('ms_effect', 'MS Effect'),
    ('effect', 'Property'), ('effect2', 'Property 2'), ('effect3', 'Property 3'),
]
UA_STICKY = {'lvl', 'unit', 'ability'}
# Vertical dividers are drawn at CATEGORY boundaries only (scripts.js
# markCatEdges, adapts to both views) — no manual per-column separators.
UA_SEP = set()
# Super-category grouping shown above the column headers (mirrors Neutral
# Creeps so both tables look symmetric). Order/colspans must match UA_COLS.
# Each column header carries data-cat so scripts.js recomputeCatColspans()
# can size each category cell — WITHOUT data-cat it counts 0 and collapses
# every category to colspan=1.
UA_CATEGORIES = [
    ('Basic',      'basic',      ['lvl', 'unit', 'ability']),
    ('Essentials', 'essentials', ['type', 'damage', 'manacost', 'cooldown',
                                  'duration', 'cast_range', 'aoe']),
    ('Extra',      'extra',      ['stackable', 'dispel', 'through_bkb',
                                  'as_effect', 'ms_effect']),
    ('Effects',    'effects',    ['effect', 'effect2', 'effect3']),
]
UA_COL_CAT = {col: slug for _cat, slug, cols in UA_CATEGORIES for col in cols}
# Column-header tooltips surfaced via a `?` badge next to the header label.
# Values support inline HTML (rendered via innerHTML in scripts.js).
UA_HEAD_HINTS = {
    'duration': 'Most of the auras have linger duration of 0.5 seconds',
    'damage': (
        '<div class="qh-line">Numbers in color mean different damage types: '
        '<span class="dt-magical">magical</span>, '
        '<span class="dt-physical">physical</span>, '
        '<span class="dt-hpremoval">HP removal</span>.</div>'
    ),
    'through_bkb': (
        '<div class="qh-line">If an ability doesn\'t pierce BKB but '
        'also deals damage on top of its effect, the damage still goes '
        'through — reduced by the magic resistance BKB provides.</div>'
        '<div class="qh-line"><span class="hint-aura">Aura</span>: all '
        'positive auras keep working on allies under BKB, but negative '
        'auras don\'t affect enemies under the same effect.</div>'
    ),
    'dispel': (
        '<div class="qh-line">'
        '<span class="ua-yn ua-yn-strong">Yes</span>'
        ' — Strong Dispel only</div>'
        '<div class="qh-line">'
        '<span class="ua-yn ua-yn-yes">Yes</span>'
        ' — Any dispel</div>'
        '<div class="qh-line">'
        '<span class="ua-yn ua-yn-no">No</span>'
        ' — Not dispellable, mostly due to different kind of ability</div>'
    ),
}
PROP_COLS = [k for k, _ in UA_COLS
             if k not in ('lvl', 'unit', 'ability')]

DMG_TYPE_CLS = {'Magical': 'dt-magical', 'Physical': 'dt-physical',
                'HP Removal': 'dt-hpremoval', 'Pure': 'dt-pure'}

# Abilities that are identical across multiple units (same slug, same
# values) get a single canonical row on the UA page — pinned to the listed
# createhero. Other units' rows are skipped, and creeps.html ability
# links route to the canonical row for that slug.
UA_CANONICAL_UNIT = {
    'frogmen_riverborn_aura': 'tad',
}
UA_SHARED_TOOLTIP = {
    'frogmen_riverborn_aura': 'This aura is identical for all frog units',
}


def _ua_head_html():
    out = []
    for idx, (k, label) in enumerate(UA_COLS):
        cls = (f'ua-{k}' + (' sticky-col' if k in UA_STICKY else '')
               + (' col-sep' if k in UA_SEP else ''))
        # Tooltip value may contain inline HTML (rendered via innerHTML
        # client-side) — escape quotes so the attribute survives.
        hint = _qhint(attr_esc(UA_HEAD_HINTS[k])) if k in UA_HEAD_HINTS else ''
        out.append(
            f'<th class="{cls} sortable" data-col="{k}" data-idx="{idx}" '
            f'data-cat="{UA_COL_CAT.get(k, "")}">'
            f'<span class="th-label">{label}</span>{hint}'
            f'<span class="sort-ind"></span></th>')
    return ''.join(out)


def _ua_cat_cells():
    # Super-category row above the column headers (one cell per category,
    # colspan = its leaf columns). scripts.js recomputeCatColspans() then keeps
    # the colspans in sync with the visible columns (via the data-cat above).
    return ''.join(
        f'<th class="cat-head cat-{slug}" data-cat="{slug}" '
        f'colspan="{len(cols)}">{esc(cat)}</th>'
        for cat, slug, cols in UA_CATEGORIES
    )


# ---- Property cells ----

# A run of >=3 slash-separated numbers ("75/80/85/90", "-15%/-18%/-21%/-25%",
# "+20/25/30/40"). Each value may carry a trailing %.
_RUN_RE = re.compile(r'[+-]?\d+(?:[.,]\d+)?%?(?:/[+-]?\d+(?:[.,]\d+)?%?){2,}')

# Coloured yes/no text. Sort rank: dash (0) < no (1) < yes (2).
_YES = '<span class="ua-yn ua-yn-yes">yes</span>'
_NO = '<span class="ua-yn ua-yn-no">no</span>'
_STRONG = '<span class="ua-yn ua-yn-strong">yes</span>'


def _run_button(run):
    """A collapsed "first→last" button for a slash-run; full list in data-full."""
    p = run.split('/')   # run is pure digits/slashes/%/+/- → safe unescaped
    return (f'<button type="button" class="lvl-toggle" aria-expanded="false" '
            f'title="Show per-tier values" data-full="{attr_esc(" / ".join(p))}">'
            f'{p[0]}→{p[-1]}</button>')


def _collapse_runs(text):
    """Collapse every long slash-run in PLAIN `text` (escapes non-run text)."""
    out, last = [], 0
    for m in _RUN_RE.finditer(text):
        out.append(esc(text[last:m.start()]))
        out.append(_run_button(m.group(0)))
        last = m.end()
    out.append(esc(text[last:]))
    return ''.join(out)


def _collapse_runs_html(s):
    """Collapse runs in an already-built HTML fragment (\\x01 manual cells) —
    only in text BETWEEN tags, so attribute tooltips (which also contain
    slashed lists) are never touched."""
    return ''.join(
        tok if tok.startswith('<') else _RUN_RE.sub(lambda m: _run_button(m.group(0)), tok)
        for tok in re.split(r'(<[^>]+>)', s)
    )


def _type_cell(val, sep, dc):
    if not val:
        return f'<td class="ua-type{sep}"{dc}>{DASH}</td>'
    return f'<td class="ua-type ua-type-{val.lower()}{sep}"{dc}>{esc(val)}</td>'


def _damage_cell(val, props, sep, dc):
    dt = (props or {}).get('dmg_type', '')
    dt_cls = f' {DMG_TYPE_CLS[dt]}' if dt in DMG_TYPE_CLS else ''
    if isinstance(val, str) and val.startswith('\x01'):
        # Manual override already has .dmg-num spans where appropriate;
        # still collapse any long slash-run inside its text.
        return (f'<td class="ua-damage{dt_cls}{sep}"{dc}>'
                f'{_collapse_runs_html(val[1:])}</td>')
    if not val:
        return f'<td class="ua-damage{dt_cls}{sep}"{dc}>{DASH}</td>'
    collapsed = _collapse_runs(str(val))
    # If a run was collapsed the button carries the dt-* colour via CSS;
    # otherwise keep the per-number .dmg-num colouring.
    inner = collapsed if 'lvl-toggle' in collapsed else _dmg_color_html(esc(val))
    return f'<td class="ua-damage{dt_cls}{sep}"{dc}>{inner}</td>'


def _stack_glyph(val):
    if val == 'Yes':
        return _YES, 2
    if val == 'No':
        return _NO, 1
    return DASH, 0


def _dispel_glyph(val):
    # Per-cell legend was moved to the column header's `?` badge —
    # cells render just the colored yes/no glyph.
    if val == 'Yes':
        return _YES, 2
    if val == 'Strong only':
        return _STRONG, 2
    if val == 'No':
        return _NO, 1
    return DASH, 0


def _bkb_glyph(val, tip):
    # Through BKB: same yes/no glyphs as Dispellable. Sorted yes(2) > no(1) > —(0).
    # Optional per-cell tooltip via `_through_bkb_tip` in props (THROUGH_BKB_TIPS).
    v = (val or '').strip().lower()
    if v == 'yes':
        g, rank = _YES, 2
    elif v == 'no':
        g, rank = _NO, 1
    else:
        g, rank = DASH, 0
    if tip:
        g = f'<span class="cell-wrap">{g}{_qhint(attr_esc(tip))}</span>'
    return g, rank


def prop_cell(pk, val, props=None):
    # Type → colour-coded text. Damage cell carries the dt-* class so the
    # value text inherits the damage-type colour (replaces the standalone
    # Damage Type column). Stackable / Dispellable → glyph icons. Every
    # <td> carries data-col so the view-toggle JS can reorder columns by key.
    sep = ' col-sep' if pk in UA_SEP else ''
    # Cells with per-level progression get a `leveled` marker class; the
    # Upgrades view toggle (.show-upgrades) draws a blue outline on them.
    if pk in (props or {}).get('_leveled', ()):
        sep += ' leveled'
    dc = f' data-col="{pk}" data-cat="{UA_COL_CAT.get(pk, "")}"'
    if pk == 'type':
        return _type_cell(val, sep, dc)
    if pk == 'damage':
        return _damage_cell(val, props, sep, dc)
    if pk == 'stackable':
        g, rank = _stack_glyph(val)
        return f'<td class="ua-stackable{sep}"{dc} data-sort="{rank}">{g}</td>'
    if pk == 'dispel':
        g, rank = _dispel_glyph(val)
        return f'<td class="ua-dispel{sep}"{dc} data-sort="{rank}">{g}</td>'
    if pk == 'through_bkb':
        g, rank = _bkb_glyph(val, (props or {}).get('_through_bkb_tip', ''))
        return f'<td class="ua-through_bkb{sep}"{dc} data-sort="{rank}">{g}</td>'
    # Raw-HTML sentinel: ABIL_MANUAL values prefixed with \x01 bypass esc
    # so we can inline <img> / <span> markup (used for Mana Burn's Int icon).
    # Still collapse long slash-runs in the inline text (between tags).
    if isinstance(val, str) and val.startswith('\x01'):
        return f'<td class="ua-{pk}{sep}"{dc}>{_collapse_runs_html(val[1:])}</td>'
    sval = '' if val is None else str(val)
    # Collapse any long per-tier run ("75/80/85/90") — even inside descriptive
    # text — to "first→last"; surrounding text kept, full list in a click
    # popover (scripts.js). Empty → dash.
    inner = _collapse_runs(sval) if sval != '' else DASH
    return f'<td class="ua-{pk}{sep}"{dc}>{inner}</td>'


# ---- Rows ----

# Valve ships a single localization file with all ability tooltips, including
# neutral-creep abilities that don't appear in dota_english.txt.
# Case-insensitive: Valve mixes `ability_` and `Ability_` (capital A)
# in the key names — same key, different casing.
_DESC_RE = r'"DOTA_Tooltip_[Aa]bility_([a-z0-9_]+?)_Description"\s+"((?:[^"\\]|\\.)+)"'


def load_ability_descriptions():
    """{slug: description} parsed once from data/abilities_english.txt;
    rendered as a hover tooltip on each ability icon."""
    descs: dict[str, str] = {}
    path = _os.path.join(_HERE, 'data', 'abilities_english.txt')
    if not _os.path.exists(path):
        return descs
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        text = f.read()
    for m in re.finditer(_DESC_RE, text):
        slug, desc = m.group(1), m.group(2)
        # Strip Valve's localization escapes / formatting macros that don't
        # carry meaning in a plain tooltip (newlines kept as spaces).
        desc = (desc.replace('\\n', ' ')
                    .replace('<br>', ' ')
                    .replace('  ', ' ')
                    .strip())
        if slug not in descs:
            descs[slug] = desc
    return descs


_PLACEHOLDER_RE = re.compile(r"%([A-Za-z_][A-Za-z0-9_]*)%")


def _fill_placeholders(desc, fields):
    """Valve's %name% placeholders -> the ability's own values ("2 / 3 / 4" for levels), "%%" -> "%". Before this the
    raw "%hero_stun_duration%" / "%damage_pct%%%" reached 8 tooltips on Neutral Abilities (audit 2026-10-05).
    A name the KV doesn't carry becomes "?" rather than leaking the raw key."""
    def value(m):
        key = m.group(1)
        raw = fields.get("av_" + key, fields.get(key, ""))
        parts = str(raw).split()
        if not parts:
            return "?"
        return " / ".join(p[:-2] if p.endswith(".0") else p for p in parts)
    out = _PLACEHOLDER_RE.sub(value, desc)
    return out.replace("%%", "%")


def _ability_cell(slug, name, abil_desc, fields=None):
    if has_abil_icon(slug):
        aico = abil_icon_html(slug, name)
        # Hover-tooltip with Valve's ability description (parsed from
        # abilities_english.txt). Reuses the body-level qhint-tip JS via
        # an `.abil-ico-hint` element carrying data-tooltip.
        desc = abil_desc.get(slug)
        if desc:
            desc = _fill_placeholders(desc, fields or {})
        if desc:
            t = attr_esc(desc)
            aico = (f'<span class="abil-ico-hint" tabindex="0" '
                    f'role="button" aria-label="{t}" '
                    f'data-tooltip="{t}">{aico}</span>')
    else:
        aico = ''
    # Question-mark hint icon appended to the ability name when this
    # row stands in for multiple units (Riverborn Aura). Hovering the
    # rest of the cell will surface patchnotes later, so explicit
    # author hints must come through a dedicated `?` badge.
    qhint = _qhint(esc(UA_SHARED_TOOLTIP[slug])) if slug in UA_SHARED_TOOLTIP else ''
    return (f'<td class="ua-ability sticky-col" data-col="ability" data-cat="basic">'
            f'<span class="ua-ability-inner">{aico}'
            f'<span class="ua-ability-name">{esc(name)}</span>'
            f'{qhint}</span></td>')


def _unit_rows(row, cur_ab, abil_desc):
    """The <tr>s of one creep — one per ability it has."""
    d = row['data']
    lvl = row.get('level', '')
    ch = (d.get('createhero') or '').strip()
    icon = d.get('icon')
    unit_img = (
        # the link wraps an alt="" picture, so it names itself (57 nameless links, audit 2026-10-05)
        f'<a class="unit-link" href="neutral_stats.html#unit-{esc(ch)}" aria-label="{esc(d.get("name", ch))}">'
        f'<img class="creep-copy" src="{esc(icon)}" alt="" loading="lazy" '
        f'onerror="this.style.visibility=\'hidden\'"></a>' if icon else '')
    out = []
    for kk in ABILITY_COLS:
        slug, name = d.get(kk + '_slug', ''), d.get(kk, '')
        if not slug:
            continue
        # Skip duplicate canonical-aura rows.
        if slug in UA_CANONICAL_UNIT and UA_CANONICAL_UNIT[slug] != ch:
            continue
        p = abil_props(slug, cur_ab)
        # Every ability row carries its own Lvl + Unit cells (no rowspan):
        # the table is sortable, and sorting reorders rows, which would
        # tear a rowspanned group apart and dump continuation cells into
        # the wrong columns. Self-contained rows always stay aligned.
        cells = [
            f'<td class="ua-lvl lvl-cell sticky-col" data-col="lvl" '
            f'data-cat="basic" data-lvl="{esc(lvl)}">{esc(lvl)}</td>',
            f'<td class="ua-unit creep-icon-cell sticky-col" data-col="unit" '
            f'data-cat="basic" data-sort="{esc(d.get("name", ""))}">{unit_img}</td>',
            _ability_cell(slug, name, abil_desc, cur_ab.get(slug, {})),
        ]
        cells += [prop_cell(pk, p[pk], p) for pk in PROP_COLS]
        aura_cls = ' class="ua-row-aura"' if p['type'] == 'Aura' else ''
        out.append(
            f'<tr id="{esc(ch)}-{slug}" data-unit="{esc(ch)}"{aura_cls}>'
            f'{"".join(cells)}</tr>')
    return out


def ua_rows(rendered, cur_ab, abil_desc):
    """Every Neutral Abilities <tr>, in the Neutral Stats row order."""
    return [tr for row in rendered for tr in _unit_rows(row, cur_ab, abil_desc)]


# ---- Page ----

_UA_TOOLBAR = (
    '<div class="cal-toggle-bar inbox-bar"><div class="toolbar-panel">'
    '<span class="view-group">'
    '<strong>View</strong>'
    '<select class="cal-mode-select" id="ua-view-mode">'
    '<option value="standard">Standard</option>'
    '<option value="auras">Auras</option>'
    '</select>'
    '</span>'
    # Upgrades — binary switch. ON marks every per-level progression
    # value in the table with a dotted underline (each "40/36/32/26"
    # number gets the marker), so leveled cells self-identify through
    # their own content rather than via an Excel-style outline.
    '<label class="ua-upgrades-toggle">'
    '<span class="ua-upgrades-label">Upgrades</span>'
    '<input type="checkbox" id="ua-upgrades-mode" class="ua-switch-input" checked>'
    '<span class="ua-switch" aria-hidden="true"></span>'
    '</label>'
    '</div></div>\n'
)

# Tiny redirect for the old URL so existing links (including from
# generated patch pages, bookmarks, external references) don't 404.
UA_REDIRECT_HTML = (
    '<!DOCTYPE html><html><head><meta charset="UTF-8">'
    '<meta http-equiv="refresh" content="0; url=neutral_abilities.html">'
    '<link rel="canonical" href="neutral_abilities.html">'
    '<title>Sloppy - moved</title></head><body>'
    '<p>This page moved to <a href="neutral_abilities.html">'
    'neutral_abilities.html</a>.</p></body></html>'
)


def ua_page_html(rows, asset_version):
    nav_ua = _site.render_top_nav('materials', _site.latest_patch_href(),
                                  patch_context=False, subtabs_active='abilities',
                                  subnav_in_header=False)
    inner = (
        # Sub-tab bar + blurb + toolbar live INSIDE the scroll box so they
        # scroll away with the table (Mana Items behaviour); sticky-left keeps
        # them put during horizontal scroll.
        f'{_site.render_materials_subnav("abilities")}'
        + _UA_TOOLBAR +
        '<table class="creeps-table unit-abilities-table">\n'
        f'<thead><tr class="cat-row">{_ua_cat_cells()}</tr>'
        f'<tr class="col-row">{_ua_head_html()}</tr></thead>\n'
        f'<tbody>\n{chr(10).join(rows)}\n</tbody>\n'
        '</table>\n'
    )
    return page_shell('Neutral Abilities', nav_ua, inner, asset_version)


def current_ability_patch(hist):
    """Current patch — pick the chronologically newest version with extracted
    ability data. `hist.patches` is already sorted; fall back to the canonical
    latest stats version if it's empty (e.g. clean checkout without stats
    dump)."""
    from patch.meta import latest_stats_version
    return next((v for v in reversed(hist.patches)
                 if v in hist.abil_by_patch), latest_stats_version())


def save_neutral_abilities_html(rendered, hist, asset_version):
    """Write neutral_abilities.html (+ the unit_abilities.html redirect) from
    the Neutral Stats rows (`rendered`, builders/creeps.py build_rows)."""
    cur_ver = current_ability_patch(hist)
    print(f"  neutral_abilities source patch: {cur_ver}")
    cur_ab = hist.abil_by_patch.get(cur_ver, {})
    html = ua_page_html(ua_rows(rendered, cur_ab, load_ability_descriptions()),
                        asset_version)
    write_dist('neutral_abilities.html', html)
    print(f"  -> dist/neutral_abilities.html: {len(html):,} bytes")
    write_dist('unit_abilities.html', UA_REDIRECT_HTML)
    print(f"  -> dist/unit_abilities.html: {len(UA_REDIRECT_HTML)} bytes (redirect)")
