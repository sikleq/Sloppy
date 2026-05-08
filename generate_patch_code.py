"""
Generate annotated Python code (b()/li()/t() calls) for a Dota patch
from raw Valve KV entries.

Usage:
    python3 generate_patch_code.py <patch_version>

E.g.: python3 generate_patch_code.py 7.41c
Reads /mnt/user-data/uploads/patchnotes_english.txt, writes patch code
to /tmp/p_<version>.py
"""
import re
import sys

KV_FILE = '/mnt/user-data/uploads/patchnotes_english.txt'

# ---------- LOAD HERO_SLUG ----------

def load_hero_internal_to_display(build_py='/home/claude/build_patch.py'):
    """Comprehensive map: Valve internal name → display name. Includes all
    heroes that exist in any Dota 2 patch from 7.06 through 7.41c."""
    return {
        'abaddon': 'Abaddon', 'alchemist': 'Alchemist',
        'ancient_apparition': 'Ancient Apparition', 'antimage': 'Anti-Mage',
        'arc_warden': 'Arc Warden', 'axe': 'Axe', 'bane': 'Bane',
        'batrider': 'Batrider', 'beastmaster': 'Beastmaster',
        'bloodseeker': 'Bloodseeker', 'bounty_hunter': 'Bounty Hunter',
        'brewmaster': 'Brewmaster', 'bristleback': 'Bristleback',
        'broodmother': 'Broodmother', 'centaur': 'Centaur Warrunner',
        'chaos_knight': 'Chaos Knight', 'chen': 'Chen', 'clinkz': 'Clinkz',
        'crystal_maiden': 'Crystal Maiden', 'dark_seer': 'Dark Seer',
        'dark_willow': 'Dark Willow', 'dawnbreaker': 'Dawnbreaker',
        'dazzle': 'Dazzle', 'death_prophet': 'Death Prophet',
        'disruptor': 'Disruptor', 'doom_bringer': 'Doom',
        'dragon_knight': 'Dragon Knight', 'drow_ranger': 'Drow Ranger',
        'earth_spirit': 'Earth Spirit', 'earthshaker': 'Earthshaker',
        'elder_titan': 'Elder Titan', 'ember_spirit': 'Ember Spirit',
        'enchantress': 'Enchantress', 'enigma': 'Enigma',
        'faceless_void': 'Faceless Void', 'furion': "Nature's Prophet",
        'grimstroke': 'Grimstroke', 'gyrocopter': 'Gyrocopter',
        'hoodwink': 'Hoodwink', 'huskar': 'Huskar', 'invoker': 'Invoker',
        'jakiro': 'Jakiro', 'juggernaut': 'Juggernaut',
        'keeper_of_the_light': 'Keeper of the Light', 'kez': 'Kez',
        'kunkka': 'Kunkka', 'largo': 'Largo', 'legion_commander': 'Legion Commander',
        'leshrac': 'Leshrac', 'lich': 'Lich', 'life_stealer': 'Lifestealer',
        'lina': 'Lina', 'lion': 'Lion', 'lone_druid': 'Lone Druid',
        'luna': 'Luna', 'lycan': 'Lycan', 'magnataur': 'Magnus',
        'marci': 'Marci', 'mars': 'Mars', 'medusa': 'Medusa', 'meepo': 'Meepo',
        'mirana': 'Mirana', 'monkey_king': 'Monkey King',
        'morphling': 'Morphling', 'muerta': 'Muerta', 'naga_siren': 'Naga Siren',
        'necrolyte': 'Necrophos', 'nevermore': 'Shadow Fiend',
        'night_stalker': 'Night Stalker', 'nyx_assassin': 'Nyx Assassin',
        'obsidian_destroyer': 'Outworld Destroyer', 'ogre_magi': 'Ogre Magi',
        'omniknight': 'Omniknight', 'oracle': 'Oracle', 'pangolier': 'Pangolier',
        'phantom_assassin': 'Phantom Assassin', 'phantom_lancer': 'Phantom Lancer',
        'phoenix': 'Phoenix', 'primal_beast': 'Primal Beast', 'puck': 'Puck',
        'pudge': 'Pudge', 'pugna': 'Pugna', 'queenofpain': 'Queen of Pain',
        'rattletrap': 'Clockwerk', 'razor': 'Razor', 'riki': 'Riki',
        'ringmaster': 'Ringmaster', 'rubick': 'Rubick', 'sand_king': 'Sand King',
        'shadow_demon': 'Shadow Demon', 'shadow_shaman': 'Shadow Shaman',
        'shredder': 'Timbersaw', 'silencer': 'Silencer', 'skeleton_king': 'Wraith King',
        'skywrath_mage': 'Skywrath Mage', 'slardar': 'Slardar', 'slark': 'Slark',
        'snapfire': 'Snapfire', 'sniper': 'Sniper', 'spectre': 'Spectre',
        'spirit_breaker': 'Spirit Breaker', 'storm_spirit': 'Storm Spirit',
        'sven': 'Sven', 'techies': 'Techies', 'templar_assassin': 'Templar Assassin',
        'terrorblade': 'Terrorblade', 'tidehunter': 'Tidehunter', 'tinker': 'Tinker',
        'tiny': 'Tiny', 'treant': 'Treant Protector', 'troll_warlord': 'Troll Warlord',
        'tusk': 'Tusk', 'undying': 'Undying', 'ursa': 'Ursa',
        'vengefulspirit': 'Vengeful Spirit', 'venomancer': 'Venomancer',
        'viper': 'Viper', 'visage': 'Visage', 'void_spirit': 'Void Spirit',
        'warlock': 'Warlock', 'weaver': 'Weaver', 'windrunner': 'Windranger',
        'winter_wyvern': 'Winter Wyvern', 'wisp': 'Io', 'witch_doctor': 'Witch Doctor',
        'zuus': 'Zeus',
    }


def load_item_internal_to_display(build_py='/home/claude/build_patch.py'):
    src = open(build_py).read()
    m = re.search(r'ITEM_SLUG\s*=\s*\{(.+?)\}', src, re.DOTALL)
    if not m:
        return {}
    pairs = re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1))
    return {slug: name for name, slug in pairs}


HERO_MAP = load_hero_internal_to_display()
ITEM_MAP = load_item_internal_to_display()

# Sort hero internal names by length descending for prefix matching
HERO_INTERNALS_SORTED = sorted(HERO_MAP.keys(), key=len, reverse=True)

# Some items in the patch may not be in ITEM_MAP — fall back to titlecase
def item_display_name(slug):
    if slug in ITEM_MAP:
        return ITEM_MAP[slug]
    # Special hand-mapped names
    overrides = {
        'heart': 'Heart of Tarrasque',
        'shivas_guard': "Shiva's Guard",
        'sange_and_yasha': 'Sange and Yasha',
        'kaya_and_sange': 'Kaya and Sange',
        'crellas_crozier': "Crella's Crozier",
        'specialists_array': "Specialist's Array",
        'enchanters_bauble': "Enchanter's Bauble",
        'conjurers_catalyst': "Conjurer's Catalyst",
        'jidi_pollen_bag': 'Jidi Pollen Bag',
        'idol_of_screeauk': 'Idol of Screeauk',
        'metamorphic_mandible': 'Metamorphic Mandible',
        'rattlecage': 'Rattlecage',
        'demonicon': 'Demonicon',
        'minotaur_horn': 'Minotaur Horn',
        'riftshadow_prism': 'Riftshadow Prism',
        'gungir': 'Gungir',
        'heavens_halberd': "Heaven's Halberd",
        'helm_of_the_overlord': 'Helm of the Overlord',
        'holy_locket': 'Holy Locket',
        'mage_slayer': 'Mage Slayer',
        'sange': 'Sange',
        'abyssal_blade': 'Abyssal Blade',
        'consecrated_wraps': 'Consecrated Wraps',
        'black_king_bar': 'Black King Bar',
        'enhancement_crude': 'Crude',
        'enhancement_greedy': 'Greedy',
        'enhancement_tough': 'Tough',
    }
    if slug in overrides:
        return overrides[slug]
    # Fallback: title case
    return slug.replace('_', ' ').title()


# ---------- VALUE PARSING ----------

NUMBER_RE = re.compile(r'-?\d+(?:\.\d+)?')


def _parse_num(s):
    m = NUMBER_RE.search(s)
    if not m:
        return None
    n = m.group(0)
    f = float(n)
    if f.is_integer() and '.' not in n:
        return int(f)
    return f


# Match "from X to Y" with possible /-separated lists and units
FROM_TO_RE = re.compile(
    r'from\s+'
    r'((?:[+\-]?\d+(?:\.\d+)?)(?:/[+\-]?\d+(?:\.\d+)?)*'
    r'(?:s|%|g)?)'
    r'\s+to\s+'
    r'((?:[+\-]?\d+(?:\.\d+)?)(?:/[+\-]?\d+(?:\.\d+)?)*'
    r'(?:s|%|g)?)',
    re.I
)


def _split_values(s):
    s = re.sub(r'[sg%]$', '', s)
    parts = s.split('/')
    nums = [_parse_num(p) for p in parts]
    if any(n is None for n in nums):
        return None
    if len(nums) == 1:
        return nums[0]
    return nums


L_KEYWORDS = [
    'cooldown', 'manacost', 'mana cost', 'recipe cost', 'total cost',
    'gold cost', 'penalty', 'intelligence required',
    'agility required', 'strength required', 'cast point',
    'channel time', 'activation time', 'restore time', 'recharge',
    'requirement', 'minimum', 'threshold for slow',
]


def _detect_l(text):
    t = text.lower()
    for kw in L_KEYWORDS:
        if kw in t:
            return True
    return False


def _detect_text_tag(text):
    t = text.lower()
    if any(p in t for p in ['no longer', "can't", 'cannot', "won't be applied",
                             'will no longer']):
        return 'NERF'
    if 'now grants' in t and ('ability point' in t or 'true sight' in t):
        return 'BUFF'
    if 'replaced with' in t or 'rescaled' in t:
        return 'REWORK'
    if 'now has' in t or 'now gains' in t or 'now applies' in t:
        return 'REWORK'
    if 'now starts with' in t or 'now reflects' in t:
        return 'REWORK'
    if 'is now' in t or 'are now' in t or 'now follows' in t:
        return 'REWORK'
    if re.search(r'\bnow\b', t):
        return 'REWORK'
    if 'fixed' in t:
        return 'MISC'
    if 'updated' in t or 'added' in t:
        return 'MISC'
    if 'unchanged' in t:
        return 'MISC'
    if 'increased' in t and 'decreased' not in t:
        return 'BUFF'
    if 'decreased' in t and 'increased' not in t:
        return 'NERF'
    if 'improved' in t:
        return 'BUFF'
    return 'MISC'


# Manual overrides for descriptions where heuristics give wrong tags.
# Match by substring (case-sensitive). New entries can be added freely.
# Value: tag string ("BUFF"/"NERF"/"REWORK"/"MISC") or None for empty badge.
TAG_OVERRIDES = {
    # 7.41b
    "Avatar now has a fixed duration and is not affected by buff": "NERF",
    "All charges are consumed when the barrier is created": "NERF",
    "Charge Restore Time of Hallowed is not affected by effects": "NERF",
    "Hallowed now starts with all 3 charges": "MISC",
    "Gaining max stacks requirement for the speedup buff is removed": "BUFF",
    "While on the glacier, Marksmanship now can be disabled": "NERF",
    "Max Health and Max Mana bonuses from items are now penalized": "NERF",
    "No longer shares cooldowns of Town Portal Scrolls": "BUFF",
    "Now gains fish on every even level": "NERF",
    "Talent Anchor Smash affects buildings now deals 50% damage": "NERF",
    "Aghanim's Scepter no longer makes activation faster": None,  # no badge
    "No longer has an alt-cast": "MISC",
}


# Match formulas like "from 10% + 1% per level to 8% + 1% per level"
# Captures four numbers: old_base, old_perlvl, new_base, new_perlvl
FORMULA_RE = re.compile(
    r'from\s+(\d+(?:\.\d+)?)\s*%\s*\+\s*(\d+(?:\.\d+)?)\s*%\s+per\s+level\s+to\s+'
    r'(\d+(?:\.\d+)?)\s*%\s*\+\s*(\d+(?:\.\d+)?)\s*%\s+per\s+level',
    re.I
)


# Match "from X-Y to A-B" (damage range like "Damage at level 1 from 45-51 to 47-53")
# Captures min1, max1, min2, max2
RANGE_TO_RANGE_RE = re.compile(
    r'from\s+(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)',
    re.I
)

# Match "from X-Y to A-B/C-D/E-F" (range that becomes per-level)
RANGE_TO_RANGE_LIST_RE = re.compile(
    r'from\s+(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s+to\s+'
    r'((?:\d+(?:\.\d+)?-\d+(?:\.\d+)?)(?:/\d+(?:\.\d+)?-\d+(?:\.\d+)?)+)',
    re.I
)


def parse_value_change(text):
    # 0) Check manual overrides first (highest priority)
    for substr, override_tag in TAG_OVERRIDES.items():
        if substr in text:
            if override_tag is None:
                return '""'  # empty badge
            return f't("{override_tag}")'

    # 1) Try per-level formula "from X% + Y% per level to A% + B% per level"
    m = FORMULA_RE.search(text)
    if m:
        old_base, old_per = float(m.group(1)), float(m.group(2))
        new_base, new_per = float(m.group(3)), float(m.group(4))
        # Extract prefix BEFORE the "from" clause
        prefix = text[:m.start()].rstrip()
        if prefix.lower().endswith('from'):
            prefix = prefix[:-4].rstrip()
        old_formula = f"{m.group(1)}% + {m.group(2)}% per level"
        new_formula = f"{m.group(3)}% + {m.group(4)}% per level"
        l = _detect_l(text)
        l_arg = ', l=True' if l else ''
        # Marker prefix tells generator to emit W(li_formula(...)) directly
        return (f'__FORMULA__:li_formula("{_escape(prefix)}", '
                f'"{old_formula}", "{new_formula}", '
                f'lambda L: {old_base} + {old_per}*L, '
                f'lambda L: {new_base} + {new_per}*L{l_arg})')

    # 2) Try multi-range "from X-Y to A-B/C-D/E-F"
    m = RANGE_TO_RANGE_LIST_RE.search(text)
    if m:
        min1, max1 = float(m.group(1)), float(m.group(2))
        old_avg = (min1 + max1) / 2
        new_ranges = m.group(3).split('/')
        new_avgs = []
        for r in new_ranges:
            a, b = r.split('-')
            new_avgs.append((float(a) + float(b)) / 2)
        old_v = int(old_avg) if old_avg.is_integer() else old_avg
        new_v = [int(x) if x.is_integer() else x for x in new_avgs]
        l = _detect_l(text)
        l_arg = ', l=True' if l else ''
        return f'b({old_v!r}, {new_v!r}{l_arg})'

    # 3) Try simple range-to-range "from X-Y to A-B" (single comparison)
    m = RANGE_TO_RANGE_RE.search(text)
    if m:
        min1, max1 = float(m.group(1)), float(m.group(2))
        min2, max2 = float(m.group(3)), float(m.group(4))
        old_avg = (min1 + max1) / 2
        new_avg = (min2 + max2) / 2
        old_v = int(old_avg) if old_avg.is_integer() else old_avg
        new_v = int(new_avg) if new_avg.is_integer() else new_avg
        l = _detect_l(text)
        l_arg = ', l=True' if l else ''
        return f'b({old_v!r}, {new_v!r}{l_arg})'

    # 4) Original "from X to Y" with /-separated lists
    m = FROM_TO_RE.search(text)
    if m:
        old_v = _split_values(m.group(1))
        new_v = _split_values(m.group(2))
        if old_v is not None and new_v is not None:
            l = _detect_l(text)
            l_arg = ', l=True' if l else ''
            return f'b({old_v!r}, {new_v!r}{l_arg})'
    tag = _detect_text_tag(text)
    return f't("{tag}")'


# ---------- KEY PARSING ----------

def parse_key(suffix):
    """
    suffix is the part after 'DOTA_Patch_<version>_'.
    Returns dict with:
        type: 'section_title' | 'group_title' | 'general' | 'item' | 'item_info'
              | 'neutral' | 'enchantment' | 'hero_base' | 'hero_ability'
              | 'hero_talent' | 'hero_info'
        entity: internal id (item slug, hero slug, etc.)
        ability: ability internal name (or None)
        index: 1, 2, 3 ... (for ordering)
        is_info: True if "_info" suffix
    """
    s = suffix
    is_info = False
    # Special section titles for 7.41b
    if s in ('Artifact_changes_Title', 'Enchantment_changes_Title'):
        return {'type': 'subgroup_title', 'title': s.replace('_Title', '').replace('_', ' '),
                'entity': None, 'index': 0, 'is_info': False}
    # General_X_Title
    if s.startswith('General_') and s.endswith('_Title'):
        return {'type': 'group_title', 'title': s[8:-6].replace('_', ' '),
                'entity': None, 'index': 0, 'is_info': False}
    # General_X or General_X_2
    if s.startswith('General_'):
        rest = s[8:]
        idx = 1
        m_idx = re.search(r'_(\d+)$', rest)
        if m_idx:
            idx = int(m_idx.group(1))
            rest = rest[:m_idx.start()]
        # Check for trailing _info
        if rest.endswith('_info'):
            is_info = True
            rest = rest[:-5]
        return {'type': 'general', 'group': rest.replace('_', ' '),
                'entity': rest, 'index': idx, 'is_info': is_info}

    # _info suffix?
    if s.endswith('_info'):
        is_info = True
        s = s[:-5]

    # Numeric index suffix
    idx = 1
    m_idx = re.search(r'_(\d+)$', s)
    if m_idx:
        idx = int(m_idx.group(1))
        s = s[:m_idx.start()]

    # Item entries
    if s.startswith('item_'):
        rest = s[5:]
        # Neutral enchantments
        if rest.startswith('enhancement_'):
            return {'type': 'enchantment', 'entity': rest[12:],
                    'index': idx, 'is_info': is_info}
        return {'type': 'item', 'entity': rest, 'index': idx, 'is_info': is_info}

    # Neutral creep
    if s.startswith('npc_'):
        # npc_dota_neutral_<name>
        m = re.match(r'npc_dota_neutral_(.+)$', s)
        if m:
            return {'type': 'neutral', 'entity': m.group(1),
                    'index': idx, 'is_info': is_info}
        return {'type': 'neutral', 'entity': s.replace('npc_', ''),
                'index': idx, 'is_info': is_info}

    # Hero entry: longest-prefix match against HERO_INTERNALS_SORTED
    # Special-case: druid_bear1 / druid_bear1_talent → Lone Druid Spirit Bear
    if s.startswith('druid_bear1'):
        rest = s[len('druid_bear1'):].lstrip('_')
        if rest == 'talent':
            return {'type': 'spirit_bear_talent', 'entity': 'lone_druid',
                    'index': idx, 'is_info': is_info}
        return {'type': 'spirit_bear', 'entity': 'lone_druid',
                'index': idx, 'is_info': is_info}

    hero = None
    for h in HERO_INTERNALS_SORTED:
        if s == h:
            return {'type': 'hero_base', 'entity': h, 'ability': None,
                    'index': idx, 'is_info': is_info}
        if s.startswith(h + '_'):
            hero = h
            rest = s[len(h) + 1:]
            break

    if not hero:
        return {'type': 'unknown', 'raw': s, 'index': idx, 'is_info': is_info}

    # rest can be: 'talent', '<hero>_<ability>', or other
    if rest == 'talent':
        return {'type': 'hero_talent', 'entity': hero,
                'index': idx, 'is_info': is_info}
    if rest.startswith(hero + '_'):
        ability = rest[len(hero) + 1:]
        return {'type': 'hero_ability', 'entity': hero, 'ability': ability,
                'index': idx, 'is_info': is_info}
    # Some abilities may not have hero prefix (rare)
    return {'type': 'hero_ability', 'entity': hero, 'ability': rest,
            'index': idx, 'is_info': is_info}


# ---------- ABILITY DISPLAY NAMES ----------

# Ability internal name -> human display name. Built via a mix of common
# transformations and overrides for ones with quirky names.
ABILITY_OVERRIDES = {
    # 7.41c — abilities present
    'alchemist_alchemist_goblins_greed': "Greevil's Greed",
    'alchemist_alchemist_acid_spray': 'Acid Spray',
    'alchemist_alchemist_chemical_rage': 'Chemical Rage',
    'ancient_apparition_ancient_apparition_ice_blast': 'Ice Blast',
    'antimage_antimage_persectur': 'Persecutor',
    'bane_bane_brain_sap': 'Brain Sap',
    'batrider_batrider_sticky_napalm': 'Sticky Napalm',
    'batrider_batrider_firefly': 'Firefly',
    'batrider_batrider_flaming_lasso': 'Flaming Lasso',
    'beastmaster_beastmaster_wild_axes': 'Wild Axes',
    'beastmaster_beastmaster_summon_razorback': 'Summon Razorback',
    'beastmaster_beastmaster_drums_of_slom': 'Drums of Slom',
    'bounty_hunter_bounty_hunter_shuriken_toss': 'Shuriken Toss',
    'bounty_hunter_bounty_hunter_wind_walk': 'Shadow Walk',
    'bounty_hunter_bounty_hunter_track': 'Track',
    'brewmaster_brewmaster_primal_split': 'Primal Split',
    'bristleback_bristleback_warpath': 'Warpath',
    'bristleback_bristleback_hairball': 'Hairball',
    'broodmother_broodmother_insatiable_hunger': 'Insatiable Hunger',
    'broodmother_broodmother_sticky_snare': "Spinner's Snare",
    'chaos_knight_chaos_knight_chaos_strike': 'Chaos Strike',
    'dark_willow_dark_willow_terrorize': 'Terrorize',
    'dawnbreaker_dawnbreaker_solar_guardian': 'Solar Guardian',
    'doom_bringer_doom_bringer_scorched_earth': 'Scorched Earth',
    'drow_ranger_drow_ranger_frost_arrows': 'Frost Arrows',
    'drow_ranger_drow_ranger_wave_of_silence': 'Gust',
    'elder_titan_elder_titan_echo_stomp': 'Echo Stomp',
    'gyrocopter_gyrocopter_afterburner': 'Afterburner',
    'hoodwink_hoodwink_sharpshooter': 'Sharpshooter',
    'wisp_wisp_tether': 'Tether',
    'wisp_wisp_spirits': 'Spirits',
    'jakiro_jakiro_macropyre': 'Macropyre',
    'juggernaut_juggernaut_blade_fury': 'Blade Fury',
    'kunkka_kunkka_admirals_rum': "Admiral's Rum",
    'lich_lich_sinister_gaze': 'Sinister Gaze',
    'lina_lina_light_strike_array': 'Light Strike Array',
    'lina_lina_laguna_blade': 'Laguna Blade',
    'lone_druid_lone_druid_spirit_bear': 'Summon Spirit Bear',
    'lone_druid_lone_druid_spirit_link': 'Spirit Link',
    'lone_druid_lone_druid_savage_roar': 'Savage Roar',
    'lycan_lycan_feral_impulse': 'Feral Impulse',
    'magnataur_magnataur_shockwave': 'Shockwave',
    'marci_marci_bodyguard': 'Bodyguard',
    'mars_mars_dauntless': 'Dauntless',
    'mars_mars_spear': 'Spear of Mars',
    'mirana_mirana_arrow': 'Sacred Arrow',
    'monkey_king_monkey_king_primal_spring': 'Primal Spring',
    'morphling_morphling_waveform': 'Waveform',
    'muerta_muerta_supernatural': 'Supernatural',
    'furion_furion_force_of_nature': "Nature's Call",
    'omniknight_omniknight_martyr': 'Repel',
    'omniknight_omniknight_hammer_of_purity': 'Hammer of Purity',
    'obsidian_destroyer_obsidian_destroyer_objurgation': 'Objurgation',
    'obsidian_destroyer_obsidian_destroyer_sanity_eclipse': "Sanity's Eclipse",
    'pangolier_pangolier_swashbuckle': 'Swashbuckle',
    'pangolier_pangolier_rollup': 'Roll Up',
    'phantom_lancer_phantom_lancer_phantom_edge': 'Phantom Rush',
    'phoenix_phoenix_dying_light': 'Dying Light',
    'phoenix_phoenix_sun_ray': 'Sun Ray',
    'phoenix_phoenix_supernova': 'Supernova',
    'primal_beast_primal_beast_trample': 'Trample',
    'queenofpain_queenofpain_shadow_strike': 'Shadow Strike',
    'nevermore_nevermore_shadowraze1': 'Shadowraze',
    'nevermore_nevermore_dark_lord': 'Presence of the Dark Lord',
    'skywrath_mage_skywrath_mage_mystic_flare': 'Mystic Flare',
    'slardar_slardar_slithereen_crush': 'Slithereen Crush',
    'spectre_spectre_dispersion': 'Dispersion',
    'storm_spirit_storm_spirit_galvanized': 'Galvanized',
    'sven_sven_storm_bolt': 'Storm Hammer',
    'techies_techies_mutually_assured_destruction': 'M.A.D.',
    'techies_techies_reactive_tazer': 'Reactive Tazer',
    'shredder_shredder_reactive_armor': 'Reactive Armor',
    'tinker_tinker_deploy_turrets': 'Deploy Turrets',
    'tiny_tiny_grow': 'Grow',
    'treant_treant_eyes_in_the_forest': 'Eyes in the Forest',
    'troll_warlord_troll_warlord_whirling_axes_ranged': 'Whirling Axes (Ranged)',
    'troll_warlord_troll_warlord_whirling_axes_melee': 'Whirling Axes (Melee)',
    'tusk_tusk_drinking_buddies': 'Drinking Buddies',
    'vengefulspirit_vengefulspirit_command_aura': 'Vengeance Aura',
    'venomancer_venomancer_poison_sting': 'Poison Sting',
    'venomancer_venomancer_snakebite': 'Snakebite',
    'viper_viper_nose_dive': 'Nosedive',
    'weaver_weaver_the_swarm': 'The Swarm',
    'winter_wyvern_winter_wyvern_splinter_blast': 'Splinter Blast',
    'witch_doctor_witch_doctor_voodoo_restoration': 'Voodoo Restoration',

    # 7.41b — additional abilities
    'alchemist_alchemist_corrosive_weaponry': 'Corrosive Weaponry',
    'ancient_apparition_ancient_apparition_bone_chill': 'Bone Chill',
    'antimage_antimage_mana_break': 'Mana Break',
    'arc_warden_arc_warden_magnetic_field': 'Magnetic Field',
    'arc_warden_arc_warden_spark_wraith': 'Spark Wraith',
    'arc_warden_arc_warden_runic_infusion': 'Runic Infusion',
    'bloodseeker_bloodseeker_rupture': 'Rupture',
    'chaos_knight_chaos_knight_phantasm': 'Phantasm',
    'chen_chen_holy_persuasion': 'Holy Persuasion',
    'clinkz_clinkz_strafe': 'Strafe',
    'crystal_maiden_crystal_maiden_crystal_clone': 'Crystal Clone',
    'dawnbreaker_dawnbreaker_break_of_dawn': 'Break of Dawn',
    'death_prophet_death_prophet_exorcism': 'Exorcism',
    'doom_bringer_doom_bringer_doom': 'Doom',
    'doom_bringer_doom_bringer_devour': 'Devour',
    'doom_bringer_doom_bringer_infernal_blade': 'Infernal Blade',
    'drow_ranger_drow_ranger_marksmanship': 'Marksmanship',
    'drow_ranger_drow_ranger_glacier': 'Glacier',
    'drow_ranger_drow_ranger_multishot': 'Multishot',
    'elder_titan_elder_titan_momentum': 'Momentum',
    'ember_spirit_ember_spirit_sleight_of_fist': 'Sleight of Fist',
    'enigma_enigma_event_horizon': 'Event Horizon',
    'enigma_enigma_demonic_conversion': 'Demonic Conversion',
    'gyrocopter_gyrocopter_flak_cannon': 'Flak Cannon',
    'gyrocopter_gyrocopter_call_down': 'Call Down',
    'hoodwink_hoodwink_hunters_boomerang': "Hunter's Boomerang",
    'invoker_invoker_invoke': 'Invoke',
    'jakiro_jakiro_dual_breath': 'Dual Breath',
    'jakiro_jakiro_liquid_fire': 'Liquid Fire',
    'juggernaut_juggernaut_bladeform': 'Bladeform',
    'keeper_of_the_light_keeper_of_the_light_bright_speed': 'Bright Speed',
    'keeper_of_the_light_keeper_of_the_light_spirit_form': 'Spirit Form',
    'largo_largo_encore': 'Encore',
    'largo_largo_croak_of_genius': 'Croak of Genius',
    'largo_largo_song_fight_song': 'Fight Song',
    'lycan_lycan_shapeshift': 'Shapeshift',
    'meepo_meepo_ransack': 'Ransack',
    'meepo_meepo_divided_we_stand': 'Divided We Stand',
    'meepo_meepo_megameepo': 'MegaMeepo',
    'monkey_king_monkey_king_transfiguration': 'Transfiguration',
    'naga_siren_naga_siren_eelskin': 'Eelskin',
    'furion_furion_wrath_of_nature': 'Wrath of Nature',
    'necrolyte_necrolyte_death_seeker': 'Death Seeker',
    'nyx_assassin_nyx_assassin_vendetta': 'Vendetta',
    'omniknight_omniknight_guardian_angel': 'Guardian Angel',
    'pangolier_pangolier_lucky_shot': 'Lucky Shot',
    'pangolier_pangolier_gyroshell': 'Gyroshell',
    'phantom_assassin_phantom_assassin_phantom_strike': 'Phantom Strike',
    'phantom_assassin_phantom_assassin_coup_de_grace': 'Coup de Grace',
    'primal_beast_primal_beast_pulverize': 'Pulverize',
    'pudge_pudge_innate_graft_flesh': 'Graft Flesh',
    'rubick_rubick_fade_bolt': 'Fade Bolt',
    'shadow_demon_shadow_demon_disruption': 'Disruption',
    'slardar_slardar_sprint': 'Sprint',
    'slark_slark_essence_shift': 'Essence Shift',
    'snapfire_snapfire_scatterblast': 'Scatterblast',
    'spectre_spectre_spectral_dagger': 'Spectral Dagger',
    'tidehunter_tidehunter_leviathans_catch': "Leviathan's Catch",
    'tidehunter_tidehunter_anchor_smash': 'Anchor Smash',
    'tidehunter_tidehunter_gush': 'Gush',
    'shredder_shredder_whirling_death': 'Whirling Death',
    'shredder_shredder_timber_chain': 'Timber Chain',
    'shredder_shredder_chakram': 'Chakram',
    'tiny_tiny_tree_channel': 'Tree Channel',
    'treant_treant_natures_grasp': "Nature's Grasp",
    'tusk_tusk_bitter_chill': 'Bitter Chill',
    'void_spirit_void_spirit_dissimilate': 'Dissimilate',
    'windrunner_windrunner_powershot': 'Powershot',
    'windrunner_windrunner_gale_force': 'Gale Force',
    'winter_wyvern_winter_wyvern_cold_embrace': 'Cold Embrace',

    # Special: SK has unusual key format `sand_king_sandking_*`
    'sand_king_sandking_scorpion_strike': 'Stinger',
    'sand_king_sandking_epicenter': 'Epicenter',
}


def ability_display_name(ability_internal):
    if ability_internal in ABILITY_OVERRIDES:
        return ABILITY_OVERRIDES[ability_internal]
    # Fallback: titlecase the snake_case
    return ability_internal.replace('_', ' ').title()


def neutral_display_name(slug):
    overrides = {
        'frostbitten_golem': 'Frostbitten Golem',
    }
    if slug in overrides:
        return overrides[slug]
    return slug.replace('_', ' ').title()


# ---------- MAIN GENERATOR ----------

def generate(version):
    text = open(KV_FILE, encoding='utf-8').read()
    pattern = re.compile(rf'\s*"DOTA_Patch_{re.escape(version.replace(".", "_"))}_([^"]+)"\s+"([^"]*)"')
    entries = []
    for line in text.splitlines():
        m = pattern.match(line)
        if m:
            entries.append((m.group(1), m.group(2)))

    print(f"# {version}: {len(entries)} entries", file=sys.stderr)

    # Group entries into ordered structure preserving file order
    # Walk entries; track current section / entity
    out = []  # list of generated Python source lines

    current_section = None  # 'general' | 'items' | 'heroes' | None
    current_subgroup = None  # 'Artifact changes' / 'Enchantment changes' / None
    current_entity = None    # tuple (kind, slug)
    current_ability = None
    items_section_open = False
    heroes_section_open = False
    general_section_open = False

    # Group title for general (Mechanics, Tormentor) — track for plain_header
    current_general_group = None

    # Collect entries by entity in walked order
    # Pass 1: parse all keys
    parsed = []
    for key, desc in entries:
        info = parse_key(key)
        info['_key'] = key
        info['_desc'] = desc
        parsed.append(info)

    # Pass 2: emit code
    def open_general():
        nonlocal general_section_open
        if not general_section_open:
            end_ul()
            out.append('# ===== GENERAL UPDATES =====')
            out.append('W(section("General Updates"))')
            out.append('')
            general_section_open = True

    def open_items():
        nonlocal items_section_open
        if not items_section_open:
            end_ul()
            out.append('')
            out.append('# ===== ITEM UPDATES =====')
            out.append('W(section("Item Updates"))')
            out.append('')
            items_section_open = True

    def open_heroes():
        nonlocal heroes_section_open
        if not heroes_section_open:
            end_ul()
            out.append('')
            out.append('# ===== HERO UPDATES =====')
            out.append('W(section("Hero Updates"))')
            out.append('')
            heroes_section_open = True

    def close_ul():
        if out and out[-1] == 'W(ul_open())':
            out.pop()
        elif current_entity is not None:
            out.append('W(ul_close())')

    in_ul = False

    def start_ul():
        nonlocal in_ul
        if not in_ul:
            out.append('W(ul_open())')
            in_ul = True

    def end_ul():
        nonlocal in_ul
        if in_ul:
            out.append('W(ul_close())')
            in_ul = False

    last_entity_key = None
    last_ability = None

    for info in parsed:
        t = info['type']
        desc = info['_desc']
        # Skip empty <br> placeholder entries
        if desc.strip() == '<br>':
            continue

        if t == 'group_title':
            # General_X_Title — emit plain_header for that group
            open_general()
            end_ul()
            out.append(f'W(plain_header("{info["title"]}"))')
            current_general_group = info['title']
            continue

        if t == 'subgroup_title':
            # Artifact_changes / Enchantment_changes
            end_ul()
            out.append(f'W(subgroup("{info["title"]}"))')
            continue

        if t == 'general':
            open_general()
            # entity here is the group identifier
            entity_key = ('general', info['entity'])
            if entity_key != last_entity_key:
                end_ul()
                # plain_header was already emitted by group_title — but if not,
                # emit it now using the group name
                if current_general_group is None:
                    out.append(f'W(plain_header("{info["entity"].replace("_", " ")}"))')
                last_entity_key = entity_key
            if info['is_info']:
                if _try_merge_info(out, desc):
                    continue
                end_ul()
                out.append(f'W(subnote("{_escape(desc)}"))')
            else:
                start_ul()
                call = parse_value_change(desc)
                _emit_li(out, desc, call)
            continue

        if t == 'item':
            open_items()
            entity_key = ('item', info['entity'])
            if entity_key != last_entity_key:
                end_ul()
                name = item_display_name(info['entity'])
                out.append(f'W(item_header("{_escape(name)}"))')
                last_entity_key = entity_key
            if info['is_info']:
                if _try_merge_info(out, desc):
                    continue
                end_ul()
                out.append(f'W(subnote("{_escape(desc)}"))')
            else:
                start_ul()
                call = parse_value_change(desc)
                _emit_li(out, desc, call)
            continue

        if t == 'enchantment':
            # Falls under "Enchantment changes" subgroup if active, otherwise emit as item
            entity_key = ('enchantment', info['entity'])
            if entity_key != last_entity_key:
                end_ul()
                name = item_display_name('enhancement_' + info['entity'])
                out.append(f'W(plain_header("{_escape(name)}"))')
                last_entity_key = entity_key
            if info['is_info']:
                if _try_merge_info(out, desc):
                    continue
                end_ul()
                out.append(f'W(subnote("{_escape(desc)}"))')
            else:
                start_ul()
                call = parse_value_change(desc)
                _emit_li(out, desc, call)
            continue

        if t == 'neutral':
            # Neutral creep / unit
            entity_key = ('neutral', info['entity'])
            if entity_key != last_entity_key:
                end_ul()
                name = neutral_display_name(info['entity'])
                out.append(f'W(plain_header("{_escape(name)}"))')
                last_entity_key = entity_key
            start_ul()
            call = parse_value_change(desc)
            _emit_li(out, desc, call)
            continue

        if t in ('hero_base', 'hero_ability', 'hero_talent', 'spirit_bear', 'spirit_bear_talent'):
            open_heroes()
            entity_key = ('hero', info['entity'])
            if entity_key != last_entity_key:
                end_ul()
                hero_name = HERO_MAP.get(info['entity'], info['entity'].replace('_', ' ').title())
                out.append('')
                out.append(f'# {hero_name}')
                out.append(f'W(hero_header("{_escape(hero_name)}"))')
                last_entity_key = entity_key
                last_ability = None
            if t == 'hero_base':
                start_ul()
                call = parse_value_change(desc)
                _emit_li(out, desc, call)
            elif t == 'hero_talent':
                if last_ability != '__talent__':
                    end_ul()
                    out.append('W(subgroup("Talents"))')
                    last_ability = '__talent__'
                start_ul()
                call = parse_value_change(desc)
                _emit_li(out, desc, call)
            elif t == 'spirit_bear':
                if last_ability != '__spirit_bear__':
                    end_ul()
                    out.append('W(subgroup("Spirit Bear"))')
                    last_ability = '__spirit_bear__'
                start_ul()
                call = parse_value_change(desc)
                _emit_li(out, desc, call)
            elif t == 'spirit_bear_talent':
                if last_ability != '__spirit_bear_talent__':
                    end_ul()
                    out.append('W(subgroup("Spirit Bear Talents"))')
                    last_ability = '__spirit_bear_talent__'
                start_ul()
                call = parse_value_change(desc)
                _emit_li(out, desc, call)
            elif t == 'hero_ability':
                ab = info['ability']
                if last_ability != ab:
                    end_ul()
                    name = ability_display_name(info['entity'] + '_' + info['entity'] + '_' + ab) \
                           if (info['entity'] + '_' + info['entity'] + '_' + ab) in ABILITY_OVERRIDES \
                           else ability_display_name(info['entity'] + '_' + ab)
                    out.append(f'W(ability("{_escape(name)}"))')
                    last_ability = ab
                if info['is_info']:
                    if _try_merge_info(out, desc):
                        continue
                    end_ul()
                    out.append(f'W(subnote("{_escape(desc)}"))')
                else:
                    start_ul()
                    call = parse_value_change(desc)
                    _emit_li(out, desc, call)
            continue

        if t == 'unknown':
            # Emit as comment
            out.append(f'# UNKNOWN KEY: {info["raw"]}  →  {desc[:60]}')

    end_ul()
    return '\n'.join(out)



def _emit_li(out, desc, call):
    """Emit either W(li(text, badge)) or W(li_formula(...)) based on parser output."""
    if call.startswith('__FORMULA__:'):
        out.append(f'W({call[len("__FORMULA__:"):]})')
    else:
        out.append(f'W(li("{_escape(desc)}", {call}))')


def _try_merge_info(out, info_desc):
    """If info_desc is 'From X-Y to A-B[/C-D...]' style (range info),
    merge it with the previous main li entry instead of emitting a subnote.
    Returns True if successfully merged, False to fall back to subnote."""
    if not out or not out[-1].startswith('W(li('):
        return False
    # Detect range-to-range[-list] pattern in info text
    m = re.search(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s+to\s+([\d./\-]+)', info_desc, re.I)
    if not m:
        return False
    old_min, old_max = float(m.group(1)), float(m.group(2))
    new_part = m.group(3).strip().rstrip('.')
    try:
        new_avgs = []
        for r in new_part.split('/'):
            if '-' not in r:
                return False
            a, b_v = r.split('-')
            new_avgs.append((float(a) + float(b_v)) / 2)
    except ValueError:
        return False
    # Extract prefix from previous main entry's text
    pm = re.match(r'W\(li\("([^"]+)", (.+?)\)\)$', out[-1])
    if not pm:
        return False
    prev_text = pm.group(1)
    prefix_m = re.match(r'^(.+?)\s+from\s+', prev_text)
    if not prefix_m:
        return False
    prefix = prefix_m.group(1)
    # Numbers
    old_avg = (old_min + old_max) / 2
    old_v = int(old_avg) if old_avg.is_integer() else old_avg
    new_v = [int(x) if x.is_integer() else x for x in new_avgs]
    # Display: original range strings (preserve formatting)
    old_range_disp = f'{m.group(1)}-{m.group(2)}'
    new_range_disp = new_part
    # Build merged HTML text. Use repr() to safely embed in Python source
    merged_html = (f'{prefix} from <span class="formula-old">{old_range_disp}</span> '
                   f'↪ {new_range_disp}')
    out[-1] = f'W(li({merged_html!r}, b({old_v!r}, {new_v!r})))'
    return True


def _escape(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 generate_patch_code.py <version>")
        sys.exit(1)
    version = sys.argv[1]
    code = generate(version)
    out_file = f'/tmp/p_{version}.py'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(code + '\n')
    print(f"Generated: {out_file} ({len(code):,} chars)")
