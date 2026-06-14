"""HTML builder functions — li, ul, section, ability, item, hero headers, etc."""

import html as _html
import json as _json
import os as _os
import re

from .images import (HERO_CDN, ITEM_CDN, ABIL_CDN, HERO_SLUG, ITEM_SLUG,
                     hero_img, item_img, abil_img, _LOCAL_ABIL_ICONS)
from .output import H, W
from .state import _State

# ---- Icon / placeholder URLs ----
TALENT_ICON_URL  = "../icons/misc/talents.svg"
INNATE_ICON_URL  = "../icons/misc/innate_icon.png"
MISSING_ICON_URL = "../icons/misc/missing.svg"
OTHER_ICON_URL   = "../icons/other.svg"

STAT_ICONS = {
    "movement_speed":    "../icons/move_speed.png",
    "attack_speed":      "../icons/attack_speed.png",
    "attack_time":       "../icons/attack_time.png",
    "attack_projectile": "../icons/attack_projectile.png",
    "damage":            "../icons/damage.png",
    "armor":             "../icons/armor.png",
    "attack_range":      "../icons/range.png",
    "vision":            "../icons/vision.png",
    "evasion":           "../icons/evasion.png",
    "magic_resist":      "../icons/magic_resist.png",
    "strength":          "../icons/strength.webp",
    "agility":           "../icons/agility.webp",
    "intelligence":      "../icons/intelligence.webp",
    "universal":         "../icons/universal.webp",
}

STAT_DETECT_RULES = [
    ("attack_projectile", ("attack projectile", "projectile speed")),
    ("magic_resist",      ("magic resist", "magic resistance")),
    ("evasion",           ("evasion",)),
    ("vision",            ("night vision", "day vision", "vision")),
    ("movement_speed",    ("movement speed", "move speed")),
    ("attack_time",       ("base attack time",)),
    ("attack_speed",      ("attack speed",)),
    ("attack_range",      ("attack range",)),
    ("armor",             ("base armor", "armor",)),
    ("damage",            ("base damage", "damage",)),
    ("strength",          ("strength",)),
    ("agility",           ("agility",)),
    ("intelligence",      ("intelligence",)),
    ("universal",         ("universal",)),
]

# ---- Innate slug / name sets (loaded from data/) ----
def _load_innate_slugs():
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "abilities_slim.json")
    if not _os.path.exists(p):
        return set()
    with open(p, encoding="utf-8") as f:
        d = _json.load(f)
    return {k for k, v in d.items() if v.get("is_innate")}

_INNATE_SLUGS = _load_innate_slugs()


def _load_facet_innate_names():
    from .badges import FACETS
    names = {nm for (nm, _color) in FACETS.values()}
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "abilities_slim.json")
    if _os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for v in _json.load(f).values():
                if isinstance(v, dict) and v.get("is_innate") and v.get("dname"):
                    names.add(v["dname"])
    return names

_FACET_INNATE_NAMES = _load_facet_innate_names()
_FACET_INNATE_PREFIX_RE = re.compile(r"^\s*([A-Z][A-Za-z0-9''.\- ]+?):\s")

INNATE_ABILITIES = {
    ("pudge", "Flesh Heap"),
    ("tidehunter", "Leviathan's Catch"),
    ("doom_bringer", "Lvl ? Pain"),
    ("legion_commander", "Outfight Them!"),
    ("dazzle", "Weave"),
    ("drow_ranger", "Precision Aura"),
    ("earth_spirit", "Stone Remnant"),
    ("enchantress", "Rabble-Rouser"),
    ("kez", "Switch Discipline"),
    ("riki", "Backstab"),
    ("ringmaster", "Dark Carnival Barker"),
    ("troll_warlord", "Battle Stance"),
    ("abyssal_underlord", "Invading Force"),
}

# ---- PROP_TAG_CSS ----
_PROP_TAG_CSS = {
    'BUFF':   'buff-text',
    'NERF':   'nerf-text',
    'REWORK': 'rework',
    'MISC':   'misc',
    'QOL':    'qol',
    'NEW':    'new',
    'DEL':    'del',
}

# ---- Enchantment data ----
_ATTR_ICON = {
    "str": "../icons/strength.webp",
    "agi": "../icons/agility.webp",
    "int": "../icons/intelligence.webp",
    "uni": "../icons/universal.webp",
}
_ATTR_LABEL = {
    "str": "Strength", "agi": "Agility",
    "int": "Intelligence", "uni": "Universal",
}

_ENCHANT_DESC = {
    "Alert":      {1: ["+7 Attack Speed"], 2: ["+15 Attack Speed", "+150 Bonus Night Vision"], 3: ["+23 Attack Speed", "+225 Bonus Night Vision"], 4: ["+31 Attack Speed", "+300 Bonus Night Vision", "+100 Attack Range"]},
    "Brawny":     {1: ["+110 Health"], 2: ["+150 Health", "+3 Health Regen"], 3: ["+190 Health", "+6 Health Regen"], 4: ["+230 Health", "+9 Health Regen", "+25% Slow Resistance"]},
    "Tough":      {1: ["+7 Damage"], 2: ["+10 Damage", "+4 Armor"], 3: ["+13 Damage", "+6 Armor"], 4: ["+16 Damage", "+8 Armor", "+40% Knockback Resistance"]},
    "Mystical":   {1: ["+1 Mana Regen"], 2: ["+1.75 Mana Regen", "+10% Magic Resistance"], 3: ["+2.5 Mana Regen", "+13% Magic Resistance"], 4: ["+3.25 Mana Regen", "+16% Magic Resistance", "+15% Mana Cost/Loss Reduction"]},
    "Quickened":  {1: ["+15 Movement Speed"], 2: ["+20 Movement Speed", "+100 Mana"], 3: ["+25 Movement Speed", "+160 Mana"], 4: ["+30 Movement Speed", "+220 Mana", "+15% Evasion"]},
    "Vital":      {1: ["+2 Health Regen"]},
    "Greedy":     {2: ["+75 GPM", "+200 Mana", "−30 Attack Damage"], 3: ["+100 GPM", "+250 Mana", "−60 Attack Damage"]},
    "Crude":      {2: ["+10% Health Restoration", "+8% BAT Reduction", "−6% Intelligence"], 3: ["+15% Health Restoration", "+12% BAT Reduction", "−6% Intelligence"], 4: ["+20% Health Restoration", "+16% BAT Reduction", "−6% Intelligence", "Also modifies incoming healing"]},
    "Nimble":     {2: ["+6% Movement Speed", "+10 Damage", "−1.5 Health Regen"], 3: ["+8% Movement Speed", "+15 Damage", "−2.25 Health Regen"], 4: ["+10% Movement Speed", "+20 Damage", "−3 Health Regen"]},
    "Keen-Eyed":  {2: ["+125 Cast Range", "+1 Mana Regen", "−10% Max Mana"], 3: ["+135 Cast Range", "+1.5 Mana Regen", "−12% Max Mana"], 4: ["+145 Cast Range", "+2 Mana Regen", "−14% Max Mana"]},
    "Titanic":    {2: ["+8% Attack Damage", "+10% Status Resistance", "−10% Attack Speed"], 3: ["+12% Attack Damage", "+12% Status Resistance", "−12% Attack Speed"], 4: ["+16% Attack Damage", "+14% Status Resistance", "−14% Attack Speed"]},
    "Timeless":   {4: ["+10% Debuff Amplification", "+8% Spell Amplification"], 5: ["+15% Debuff Amplification", "+16% Spell Amplification"]},
    "Vampiric":   {5: ["+30% Lifesteal", "+20% Spell Lifesteal", "+300 Bonus Night Vision"]},
    "Evolved":    {5: ["+40 Primary Stat", "(+24 All Attributes for Universal heroes)"]},
    "Fleetfooted":{5: ["+115 Movement Speed", "Does not stack with boots"]},
    "Hulking":    {5: ["+5% Max Health", "+1.5% Max Health Regen", "−30% Attack Speed"]},
    "Audacious":  {5: ["+100 Attack Speed", "+80 Magic Attack Damage", "+10% Incoming Damage"]},
    "Feverish":   {5: ["+15% Cooldown Reduction", "+7% Mana Cost/Loss Increase"]},
    "Manic":      {5: ["−18% Base Attack Time", "+20% Cast Speed", "−20% Vision"]},
}

# ---- Ability display-name → CDN slug overrides ----
ABILITY_DISPLAY_TO_SLUG = {
    ("antimage", "Persecutor"): "persectur",
    ("alchemist", "Greevil's Greed"): "goblins_greed",
    ("bounty_hunter", "Shadow Walk"): "wind_walk",
    ("drow_ranger", "Gust"): "wave_of_silence",
    ("naga_siren", "Deluge"): "deluge",
    ("vengefulspirit", "Vengeance Aura"): "command_aura",
    ("furion", "Nature's Call"): "force_of_nature",
    ("obsidian_destroyer", "Sanity's Eclipse"): "sanity_eclipse",
    ("sand_king", "Stinger"): "scorpion_strike",
    ("pangolier", "Roll Up"): "rollup",
    ("phantom_lancer", "Phantom Rush"): "phantom_edge",
    ("nevermore", "Shadowraze"): "shadowraze1",
    ("nevermore", "Presence of the Dark Lord"): "dark_lord",
    ("sven", "Storm Hammer"): "storm_bolt",
    ("techies", "M.A.D."): "mutually_assured_destruction",
    ("skeleton_king", "Wraithfire Blast"): "hellfire_blast",
    ("marci", "Bodyguard"): "bodyguard",
    ("mars", "Spear of Mars"): "spear",
    ("mirana", "Sacred Arrow"): "arrow",
    ("lone_druid", "Summon Spirit Bear"): "spirit_bear",
    ("rattletrap", "Cog"): "power_cogs",
    ("tidehunter", "Leviathan's Catch"): "leviathans_catch",
    ("hoodwink", "Hunter's Boomerang"): "hunters_boomerang",
    ("broodmother", "Spinner's Snare"): "sticky_snare",
    ("viper", "Nosedive"): "nose_dive",
    ("troll_warlord", "Whirling Axes (Ranged)"): "whirling_axes_ranged",
    ("troll_warlord", "Whirling Axes (Melee)"): "whirling_axes_melee",
    ("storm_spirit", "Galvanized"): "galvanized",
    ("largo", "Bullbelly Blitz"): "song_fight_song",
    ("largo", "Hotfeet Hustle"): "song_double_time",
    ("largo", "Island Elixir"): "song_good_vibrations",
    ('enigma', 'Demonic Summoning'): 'demonic_conversion',
    ('monkey_king', 'Changing of the Guard'): 'transfiguration',
    ('pangolier', 'Rolling Thunder'): 'gyroshell',
    ('pudge', 'Flesh Heap'): 'innate_graft_flesh',
    ('slardar', 'Guardian Sprint'): 'sprint',
    ('tiny', 'Tree Volley'): 'tree_channel',
    ('doom_bringer', 'Lvl ? Pain'): 'lvl_pain',
    ('kez', "Raven's Veil"): 'ravens_veil',
    ('legion_commander', 'Outfight Them!'): 'outfight_them',
    ('muerta', 'Pierce the Veil'): 'pierce_the_veil',
    ('oracle', "Fortune's End"): 'fortunes_end',
    ('techies', 'Proximity Mines'): 'land_mines',
    ('windrunner', 'Focus Fire'): 'focusfire',
    ('abaddon', 'Mist Coil'): 'death_coil',
    ('bane', 'Ichor of Nyctasha'): 'ichor_of_nyctasha',
    ('beastmaster', 'Summon Raptors'): 'summon_raptor',
    ('broodmother', "Spider's Milk"): 'spiders_milk',
    ('crystal_maiden', 'Arcane Aura'): 'brilliance_aura',
    ('dark_seer', 'Quick Wit'): 'aggrandize',
    ('dazzle', 'Weave'): 'innate_weave',
    ('dragon_knight', "Wyrm's Wrath"): 'wyrms_wrath',
    ('drow_ranger', 'Precision Aura'): 'trueshot',
    ('earth_spirit', 'Stone Remnant'): 'stone_caller',
    ('elder_titan', 'Astral Spirit'): 'ancestral_spirit',
    ('enchantress', 'Rabble-Rouser'): 'rabblerouser',
    ('enchantress', "Nature's Attendants"): 'natures_attendants',
    ('grimstroke', 'Stroke of Fate'): 'dark_artistry',
    ('gyrocopter', 'Side Gunner'): 'side_gunner_spawn_ability',
    ('huskar', "Berserker's Blood"): 'berserkers_blood',
    ('jakiro', 'Liquid Frost'): 'liquid_ice',
    ('kez', 'Switch Discipline'): 'switch_weapons',
    ('largo', 'Hotfeet Hustle'): 'song_double_time',
    ('legion_commander', 'Moment of Courage'): 'moment_of_courage',
    ('lich', 'Sacrifice'): 'death_charge',
    ('lion', 'To Hell and Back'): 'to_hell_and_back',
    ('lion', 'Finger of Death'): 'finger_of_death',
    ('marci', 'Rebound'): 'companion_run',
    ('medusa', "Gorgon's Grasp"): 'gorgon_grasp',
    ('monkey_king', "Wukong's Command"): 'wukongs_command',
    ('morphling', 'Ebb and Flow'): 'ebb_and_flow',
    ('morphling', 'Adaptive Strike'): 'adaptive_strike_agi',
    ('furion', 'Spirit of the Forest'): 'spirit_of_the_forest',
    ('night_stalker', 'Hunter in the Night'): 'hunter_in_the_night',
    ('nyx_assassin', 'Mana Burn'): 'neuro_sting',
    ('nyx_assassin', 'Mind Flare'): 'jolt',
    ('oracle', "Diviner's Deck"): 'diviners_deck',
    ('obsidian_destroyer', 'Essence Flux'): 'equilibrium',
    ('riki', 'Backstab'): 'innate_backstab',
    ('riki', 'Tricks of the Trade'): 'tricks_of_the_trade',
    ('ringmaster', 'Dark Carnival Barker'): 'dark_carnival_souvenirs',
    ('ringmaster', 'Escape Act'): 'the_box',
    ('ringmaster', 'Impalement Arts'): 'impalement',
    ('nevermore', 'Feast of Souls'): 'frenzy',
    ('nevermore', 'Requiem of Souls'): 'requiem',
    ('silencer', 'Suffer In Silence'): 'brain_drain',
    ('silencer', 'Arcane Curse'): 'curse_of_the_silent',
    ('silencer', 'Glaives of Wisdom'): 'glaives_of_wisdom',
    ('skywrath_mage', 'Shield of the Scion'): 'shield_of_the_scion',
    ('spirit_breaker', 'Empowering Haste'): 'bull_rush',
    ('spirit_breaker', 'Charge of Darkness'): 'charge_of_darkness',
    ('sven', 'Wrath of God'): 'wrath_of_god',
    ('techies', 'Blast Off!'): 'suicide',
    ('tinker', 'March of the Machines'): 'march_of_the_machines',
    ('tinker', 'Warp Flare'): 'warp_grenade',
    ('tiny', 'Tree Throw'): 'toss_tree',
    ('treant', "Nature's Guise"): 'natures_guise',
    ('treant', 'Eyes In The Forest'): 'eyes_in_the_forest',
    ('troll_warlord', 'Battle Stance'): 'switch_stance',
    ('troll_warlord', "Berserker's Rage"): 'berserkers_rage',
    ('abyssal_underlord', 'Invading Force'): 'raid_boss',
    ('visage', 'Silent as the Grave'): 'silent_as_the_grave',
    ('weaver', 'Threads of Fate'): 'threads_of_fate',
    ('winter_wyvern', "Eldwurm's Edda"): 'eldwurms_edda',
    ('winter_wyvern', "Winter's Curse"): 'winters_curse',
    ('zuus', "Thundergod's Wrath"): 'thundergods_wrath',
    ('zuus', 'Nimbus'): 'cloud',
    ('morphling', 'Morph'): 'replicate',
}

HERO_TO_ABIL_PREFIX = {
    "sand_king": "sandking",
}

ITEM_DISPLAY_OVERRIDES = {
    'item_bfury':            'Battle Fury',
    'item_boots':            'Boots of Speed',
    'item_recipe':           'Recipe',
    'item_pers':             'Perseverance',
    'item_lifesteal':        'Morbid Mask',
    'item_buckler':          'Buckler',
    'item_ogre_axe':         'Ogre Axe',
    'item_belt_of_strength': 'Belt of Strength',
    'item_band_of_elvenskin':'Band of Elvenskin',
    'item_robe':             'Robe of the Magi',
    'item_diadem':           'Diadem',
    'item_voodoo_mask':      'Voodoo Mask',
    'item_helm_of_the_dominator': 'Helm of the Dominator',
    'item_ultimate_orb':     'Ultimate Orb',
    'item_tiara_of_selemene':'Tiara of Selemene',
    'item_soul_booster':     'Soul Booster',
    'item_kaya':             'Kaya',
    'item_crown':            'Crown',
    'item_yasha':            'Yasha',
    'item_vanguard':         'Vanguard',
    'item_ring_of_health':   'Ring of Health',
    'item_void_stone':       'Void Stone',
    'item_oblivion_staff':   'Oblivion Staff',
    'item_hyperstone':       'Hyperstone',
    'item_blades_of_attack': 'Blades of Attack',
    'item_gloves':           'Gloves of Haste',
    'item_quelling_blade':   'Quelling Blade',
    'item_orb_of_venom':     'Orb of Venom',
    'item_blade_of_alacrity':'Blade of Alacrity',
    'item_broadsword':       'Broadsword',
    'item_claymore':         'Claymore',
    'item_cornucopia':       'Cornucopia',
    'item_chainmail':        'Chainmail',
    'item_splintmail':       'Splintmail',
    'item_helm_of_iron_will':'Helm of Iron Will',
    'item_ring_of_basilius': 'Ring of Basilius',
    'item_ring_of_regen':    'Ring of Regen',
    'item_wizard_hat':       'Wizard Hat',
    'item_energy_booster':   'Energy Booster',
    'item_point_booster':    'Point Booster',
    'item_vitality_booster': 'Vitality Booster',
    'item_shawl':            'Shawl',
    'item_cloak':            'Cloak',
    'item_headdress':        'Headdress',
    'item_fluffy_hat':       'Fluffy Hat',
    'item_talisman_of_evasion':'Talisman of Evasion',
    'item_staff_of_wizardry':'Staff of Wizardry',
    'item_chasm_stone':      'Chasm Stone',
    'item_urn_of_shadows':   'Urn of Shadows',
    'item_veil_of_discord':  'Veil of Discord',
    'item_blink':            'Blink Dagger',
    'item_mask_of_madness':  'Mask of Madness',
    'item_mask_of_death':    'Morbid Mask',
}


# ---- Internal helpers ----

def _open_block(extra_cls='', extra_attrs=''):
    pre = _close_ability_block()
    cls = 'entity-block' + ((' ' + extra_cls) if extra_cls else '')
    s = (pre + ('</div>\n' if _State.block_open else '')
         + f'<div class="{cls}"{extra_attrs}>\n')
    _State.block_open = True
    cls = extra_cls or ''
    _State.dyn_skip_li = False
    if (('is-new' in cls) or ('is-changed' in cls)) \
            and _State.current_entity_key and _State.current_patch_version:
        forced_tag = 'new' if 'is-new' in cls else 'rework'
        rec = _State.dynamics.get(_State.current_entity_key)
        if rec is not None:
            bucket = rec["patches"].setdefault(_State.current_patch_version, {})
            bucket[forced_tag] = bucket.get(forced_tag, 0) + 1
        if forced_tag == 'new':
            _State.dyn_skip_li = True
    return s


def _close_block():
    out = _close_ability_block()
    if _State.block_open:
        _State.block_open = False
        out += '</div>\n'
    return out


def _close_ability_block():
    if _State.ability_block_open:
        _State.ability_block_open = False
        return '</div>\n'
    return ''


_DYN_TAG_WHITELIST = {"buff", "nerf", "new", "del", "rework", "misc", "qol"}


def _dyn_record_li(tags):
    if _State.dyn_skip_li:
        return
    ek = _State.current_entity_key
    pv = _State.current_patch_version
    if not ek or not pv:
        return
    rec = _State.dynamics.get(ek)
    if rec is None:
        return
    patch_bucket = rec["patches"].setdefault(pv, {})
    for tag in tags:
        if tag in _DYN_TAG_WHITELIST:
            patch_bucket[tag] = patch_bucket.get(tag, 0) + 1


def _slugify(name):
    s = name.lower().replace("'", "").replace("’", "")
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def _register_entity(kind, name):
    if _State.current_section_slug == 'general':
        _State.current_entity_key = None
        _State.current_entity_display = None
        return ''
    slug = _slugify(name)
    key = f"{kind}|{slug}"
    _State.current_entity_key = key
    _State.current_entity_display = name
    rec = _State.dynamics.setdefault(key, {"name": name, "kind": kind, "patches": {}})
    rec["name"] = name
    if kind == "hero":
        rec["icon"] = HERO_SLUG.get(
            name, name.lower().replace(" ", "_").replace("'", "").replace("-", ""))
    elif kind == "item":
        rec["icon"] = ITEM_SLUG.get(
            name, name.lower().replace(" ", "_").replace("'", ""))
        if _State.current_section_slug == 'neutral-items':
            rec["neutral_section"] = True
    elif kind == "enchant":
        rec["icon"] = "enhancement_" + name.lower().replace(
            " ", "_").replace("-", "_").replace("'", "")
    return f' id="dyn-{kind}-{slug}"'


def _section_slug(title):
    t = re.sub(r'\s+Updates?$', '', title).strip()
    pluralise = {'Hero': 'Heroes', 'Item': 'Items',
                 'Neutral Item': 'Neutral Items', 'Neutral Creep': 'Neutral Creeps'}
    label = pluralise.get(t, t)
    slug = label.lower().replace(' ', '-')
    return slug, label


def _item_display_name(slug):
    if slug in ITEM_DISPLAY_OVERRIDES:
        return ITEM_DISPLAY_OVERRIDES[slug]
    s = slug[5:] if slug.startswith('item_') else slug
    return s.replace('_', ' ').title()


# ---- Public element functions ----

def hero_header(name):
    _State.current_hero = HERO_SLUG.get(name, name.lower().replace(" ", "_").replace("'", "").replace("-", ""))
    _State.next_ul_is_hero_stats = True
    _State.seen_abilities_subgroup = False
    _State.seen_facets_subgroup = False
    eid = _register_entity("hero", name)
    return _open_block() + f'''<div class="entity hero-entity"{eid}>
  <div class="entity-icon hero-icon"><img src="{hero_img(name)}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def unit_header(name, icon_url, kind=None):
    _State.current_hero = None
    kind_attr = f' data-kind="{kind}"' if kind else ''
    entity_kind = "creep-hero" if (kind and kind.lower().startswith("creep-hero")) else "unit"
    eid = _register_entity(entity_kind, name)
    return _open_block() + f'''<div class="entity unit-entity"{kind_attr}{eid}>
  <div class="entity-icon hero-icon"><img src="{icon_url}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def item_header(name, new=False, changed=False):
    out = _close_ability_block()
    _State.current_hero = None
    if new:
        tag_text = 'NEW'
        type_text = new if isinstance(new, str) else ''
        type_label = (f' <span class="entity-new-type">{type_text}</span>'
                      if type_text else '')
        extra_cls = 'is-new'
        block_data_attr = f' data-new-tag="{tag_text}"'
    elif changed:
        label_text = changed if isinstance(changed, str) else 'Recipe changed'
        type_label = f' <span class="entity-changed-type">{label_text}</span>'
        extra_cls = 'is-changed'
        block_data_attr = ''
    else:
        type_label = ''
        extra_cls = ''
        block_data_attr = ''
    eid = _register_entity("item", name)
    return out + _open_block(extra_cls, block_data_attr) + f'''<div class="entity item-entity"{eid}>
  <div class="entity-icon item-icon"><img src="{item_img(name)}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}{type_label}</div>
</div>'''


def plain_header(name, dynamics=True, terrain_link=None):
    out = _close_ability_block()
    _State.current_hero = None
    if dynamics:
        eid = _register_entity("plain", name)
    else:
        _State.current_entity_key = None
        eid = ''
    link_html = ''
    if terrain_link:
        link_html = (
            f'<a class="terrain-jump-btn" href="../terrain.html?patch={terrain_link}" '
            f'title="See these changes on the map">'
            f'<img src="../icons/ui/gothic/icon_terrain.png" alt="" width="16" height="16">'
            f'<span>View on map</span></a>')
    return out + _open_block() + f'<div class="entity plain-entity"{eid}><div class="entity-name">{name}</div>{link_html}</div>'


def enchant_header(name, slug=None, new=False):
    if slug is None:
        slug = name.lower().replace(" ", "_").replace("-", "_").replace("'", "")
    icon = f"{ITEM_CDN}enhancement_{slug}.png"
    if new:
        type_text = new if isinstance(new, str) else ''
        type_label = (f' <span class="entity-new-type">{type_text}</span>'
                      if type_text else '')
        extra_cls = 'is-new'
        block_data_attr = ' data-new-tag="NEW"'
    else:
        type_label = ''
        extra_cls = ''
        block_data_attr = ''
    eid = _register_entity("enchant", name)
    return _open_block(extra_cls, block_data_attr) + f'''<div class="entity item-entity"{eid}>
  <div class="entity-icon item-icon"><img src="{icon}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}{type_label}</div>
</div>'''


def section(title):
    _State.current_hero = None
    slug, label = _section_slug(title)
    _State.current_section_slug = slug
    _State.current_sections.append({'slug': slug, 'label': label})
    out = _close_block()
    if _State.section_panel_open:
        out += '</section>'
    out += (f'<section class="cat-panel">'
            f'<h2 class="section" data-section="{slug}">{title}</h2>')
    _State.section_panel_open = True
    return out


def subgroup(title):
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if title.lower() == "abilities":
        _State.seen_abilities_subgroup = True
    if title.lower() == "talents":
        on_err = (
            "this.onerror=function(){this.style.display='none'};"
            f"this.src='{MISSING_ICON_URL}';"
        )
        icon = (f'<img src="{TALENT_ICON_URL}" alt="" '
                f'class="ability-icon-img" loading="lazy" onerror="{on_err}">')
        _State.ability_icons.add(TALENT_ICON_URL)
        _State.ability_block_open = True
        return out + (f'<h4 class="subgroup">{title}</h4>'
                      f'<div class="ability-block talents-block">'
                      f'<div class="ability-icon-wrap">{icon}</div>')
    return out + f'<h4 class="subgroup">{title}</h4>'


def ability(title, slug=None, innate=None, icon_url=None):
    icon_html = ''
    is_innate = False
    key = None
    if slug is None and _State.current_hero:
        hero = _State.current_hero
        prefix = HERO_TO_ABIL_PREFIX.get(hero, hero)
        key = (hero, title)
        if key in ABILITY_DISPLAY_TO_SLUG:
            ability_part = ABILITY_DISPLAY_TO_SLUG[key]
        else:
            ability_part = (title.lower()
                            .replace("'", "")
                            .replace("-", "_")
                            .replace(" ", "_")
                            .replace(".", "")
                            .replace("(", "")
                            .replace(")", ""))
        slug = f"{prefix}_{ability_part}"
    elif _State.current_hero:
        key = (_State.current_hero, title)
    if innate is not None:
        is_innate = bool(innate)
    elif slug:
        is_innate = (slug in _INNATE_SLUGS) or (key is not None and key in INNATE_ABILITIES)
    icon_inner = ''
    skip_marker = False
    if not (icon_url or slug):
        icon_inner = (f'<img src="{MISSING_ICON_URL}" alt="" '
                      f'class="ability-icon-img" loading="lazy" '
                      f'title="missing icon: {title}">')
    elif slug and not icon_url and slug not in _LOCAL_ABIL_ICONS:
        _State.ability_icons.add(f"{ABIL_CDN}{slug}.png")
        if is_innate:
            icon_inner = (f'<img src="{INNATE_ICON_URL}" alt="{title}" '
                          f'class="ability-icon-img" loading="lazy" '
                          f'data-slug="{slug}">')
            skip_marker = True
        else:
            icon_inner = (f'<img src="{MISSING_ICON_URL}" alt="{title}" '
                          f'class="ability-icon-img" loading="lazy" '
                          f'data-slug="{slug}" title="missing icon: {slug}">')
    if (icon_url or slug) and not icon_inner:
        src = icon_url if icon_url else f"{ABIL_CDN}{slug}.png"
        if is_innate:
            on_err = (
                "this.onerror=function(){this.style.display='none'};"
                "var m=this.parentElement.querySelector('.innate-marker');"
                "if(m)m.style.display='none';"
                f"this.src='{INNATE_ICON_URL}';"
            )
        else:
            on_err = (
                "this.onerror=function(){this.style.display='none'};"
                f"this.src='{MISSING_ICON_URL}';"
            )
        slug_attr = f' data-slug="{slug}"' if slug else ''
        if slug and not is_innate:
            on_err += (f"this.title='missing icon: {slug}';")
        icon_inner = (f'<img src="{src}" alt="{title}" '
                      f'class="ability-icon-img" loading="lazy"{slug_attr} '
                      f'onerror="{on_err}">')
        if not icon_url:
            _State.ability_icons.add(src)
    if is_innate and not skip_marker:
        icon_inner += (f'<img src="{INNATE_ICON_URL}" alt="" '
                       f'class="innate-marker">')
    icon_html = f'<div class="ability-icon-wrap">{icon_inner}</div>' if icon_inner else ''
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if not _State.seen_abilities_subgroup and _State.current_hero:
        out += '<h4 class="subgroup">Abilities</h4>'
        _State.seen_abilities_subgroup = True
    _State.ability_block_open = True
    return out + (f'<div class="ability-block{" is-innate" if is_innate else ""}">'
                  f'{icon_html}'
                  f'<h4 class="ability-title">{title}</h4>')


def facet_header(slug):
    from .badges import FACETS, _FACET_COLOR_GRADIENT
    from .images import _FACET_ICONS
    if slug not in FACETS:
        return f'<!-- facet_header: unknown slug {slug} -->'
    name, color = FACETS[slug]
    icon_name = None
    fi = _FACET_ICONS.get(slug)
    if isinstance(fi, list) and len(fi) > 1:
        icon_name = fi[1]
    gradient = _FACET_COLOR_GRADIENT.get(color, _FACET_COLOR_GRADIENT["Gray0"])
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if _State.current_hero and not _State.seen_facets_subgroup:
        out += '<h4 class="subgroup">Facets</h4>'
        _State.seen_facets_subgroup = True
    _State.ability_block_open = True
    icon_overlay = (f'<img src="../icons/facets/{icon_name}.png" alt="" '
                    f'class="facet-icon-overlay" loading="lazy">') if icon_name else ''
    icon_html = (f'<div class="ability-icon-wrap facet-icon-wrap" '
                 f'style="background-image:{gradient}">{icon_overlay}</div>')
    return out + (f'<div class="ability-block facet-block">'
                  f'{icon_html}'
                  f'<h4 class="ability-title">{name}</h4>')


def ul_open():
    out = ''
    if _State.next_ul_is_hero_stats and _State.current_hero:
        on_err = (
            "this.onerror=function(){this.style.display='none'};"
            f"this.src='{OTHER_ICON_URL}';"
        )
        icon = (f'<img src="{OTHER_ICON_URL}" alt="" '
                f'class="ability-icon-img" loading="lazy" onerror="{on_err}">')
        out += ('<h4 class="subgroup">STATS</h4>'
                '<div class="ability-block other-block">'
                f'<div class="ability-icon-wrap">{icon}</div>')
        _State.ability_block_open = True
        _State.next_ul_is_hero_stats = False
        _State.in_stats_ul = True
    return out + '<ul class="changes">'


def ul_close():
    _State.in_stats_ul = False
    return '</ul>'


_TALENT_PREFIX_RE = re.compile(r'^(Level \d+ Talent) (?!:)')


def li(text, badge="", extra="", force_tag=None, ability_row=False):
    if isinstance(text, str):
        text = _TALENT_PREFIX_RE.sub(r'\1: ', text)
        if _State.in_stats_ul:
            _m = _FACET_INNATE_PREFIX_RE.match(text)
            if _m and _m.group(1) in _FACET_INNATE_NAMES:
                print(f"  [warn] '{_m.group(1)}' is a known facet/innate but sits in "
                      f"STATS ({_State.current_hero}) — use facet_header()/ability() instead")
    tags = set()
    if force_tag is not None:
        dyn_tags = set(force_tag.split())
    else:
        primary = re.findall(r'data-tag="(\w+)"', badge)
        if primary:
            dyn_tags = set(primary)
        else:
            dyn_tags = set(re.findall(r'data-overall="(\w+)"', badge))
    _dyn_record_li(dyn_tags)
    if isinstance(text, str) and 'del' in dyn_tags:
        _low = text.strip().rstrip('.').lower()
        if _low in ('removed', 'item removed from the game',
                    'enchantment removed from the game', 'item cycled out'):
            _ek = _State.current_entity_key
            _pv = _State.current_patch_version
            if _ek and _pv:
                _rec = _State.dynamics.get(_ek)
                if _rec is not None and _rec.get('kind') in ('item', 'enchant'):
                    _rec.setdefault('removed_in', _pv)
    if force_tag is not None:
        tag_str = force_tag
        for tok in force_tag.split():
            tags.add(tok)
    else:
        overalls = re.findall(r'data-overall="(\w+)"', badge)
        for o in overalls:
            tags.add(o)
        for tag_id in re.findall(r'data-tag="(\w+)"', badge):
            tags.add(tag_id)
    if force_tag is None:
        if not overalls:
            for cls in re.findall(r'badge (buff|nerf)\d+', badge):
                tags.add(cls)
        tag_str = " ".join(sorted(tags))

    text_tag_re = re.search(
        r'<span class="badge (buff-text|nerf-text|rework|misc|qol|new|del)"[^>]*>\w+</span>\s*',
        badge
    )
    if text_tag_re:
        left_tag = text_tag_re.group(0).rstrip()
        rest = badge[:text_tag_re.start()] + badge[text_tag_re.end():]
    elif 'data-overall="buff"' in badge:
        left_tag = '<span class="badge buff-text" data-tag="buff" data-overall="buff">BUFF</span>'
        rest = badge
    elif 'data-overall="nerf"' in badge:
        left_tag = '<span class="badge nerf-text" data-tag="nerf" data-overall="nerf">NERF</span>'
        rest = badge
    else:
        left_tag = '<span class="row-tag-empty"></span>'
        rest = badge

    classes = []
    marker = ""
    text_noclass = (re.sub(r'<!--TIP-->.*?<!--/TIP-->', '', text, flags=re.S)
                    if isinstance(text, str) else text)
    if isinstance(text, str) and "Aghanim's Scepter" in text_noclass:
        classes.append("aghanim-scepter")
        marker = '<span class="aghanim-marker scepter"></span>'
    elif isinstance(text, str) and "Aghanim's Shard" in text_noclass:
        classes.append("aghanim-shard")
        marker = '<span class="aghanim-marker shard"></span>'
    if isinstance(text, str) and re.match(r'^\s*(Passive|Active|Toggle|Aura|Ability)\s*:', text):
        classes.append("ability-row")
        text = re.sub(r'^(\s*)(Passive|Active|Toggle|Aura|Ability)(\s*:)',
                      r'\1<b>\2\3</b>', text)
    elif ability_row:
        classes.append("ability-row")
    cls_attr = f' class="{" ".join(classes)}"' if classes else ""
    attr = f' data-tag="{tag_str}"' if tag_str else ""
    trailing_tips = []
    if isinstance(text, str):
        text_base = text
        while text_base.rstrip().endswith('<!--/TIP-->'):
            _i = text_base.rfind('<!--TIP-->')
            if _i < 0:
                break
            trailing_tips.insert(0, text_base[_i:])
            text_base = text_base[:_i].rstrip()
    else:
        text_base = text
    if isinstance(extra, str) and '<!--INLINETIP-->' in extra:
        _lifted = re.findall(r'<!--INLINETIP-->(.*?)<!--/INLINETIP-->', extra, re.S)
        extra = re.sub(r'<!--INLINETIP-->.*?<!--/INLINETIP-->', '', extra, flags=re.S)
        trailing_tips.extend(_lifted)
    if not isinstance(text_base, str):
        text_inner = text_base
    elif trailing_tips:
        cluster = marker + ''.join(trailing_tips)
        _mw = re.search(r'(\S+)\s*$', text_base)
        if _mw and '<' not in _mw.group(1) and '>' not in _mw.group(1):
            text_inner = (text_base[:_mw.start(1)]
                          + f'<span class="li-tail">{_mw.group(1)}{cluster}</span>')
        else:
            text_inner = f'{text_base} <span class="li-tail">{cluster}</span>'
    else:
        text_inner = f'{text_base}{marker}'
    return f'<li{attr}{cls_attr}>{left_tag}<span class="row-text">{text_inner}</span>{rest}{extra}</li>'


def inline_note(text):
    return f'<!--INLINETIP-->{info_tip(text)}<!--/INLINETIP-->'


def info_tip(*lines, header=None):
    body = '<br>'.join(lines)
    head = f'<span class="info-pop-h">{header}</span>' if header else ''
    return ('<!--TIP--><span class="info-tip" tabindex="0">?'
            f'<span class="info-pop">{head}{body}</span></span><!--/TIP-->')


def show_list(*items, summary='Show list'):
    items_html = ''.join(f'<span class="show-list-item">{it}</span>' for it in items)
    return (f'<details class="show-list-inline">'
            f'<summary><span class="show-list-chevron">▸</span>'
            f'{summary} <span class="subnote-count">({len(items)})</span></summary>'
            f'<div class="show-list-body">{items_html}</div></details>')


def _fmt_formula(expr):
    expr = expr.replace('*', '×')
    return re.sub(
        r'[A-Za-z_]\w*|\d+(?:\.\d+)?',
        lambda m: (f'<span class="f-var">{m.group(0)}</span>'
                   if m.group(0)[0].isalpha() or m.group(0)[0] == '_'
                   else f'<span class="f-num">{m.group(0)}</span>'),
        expr)


def _eval_formula(expr, env):
    return eval(expr.replace('^', '**'), {"__builtins__": {}}, dict(env))


def _num_fmt(x):
    return f'{round(float(x), 1):g}'


def _formula_pct_badge(o, n, lower=False):
    from .badges import gradient_class
    if o == 0 or n == o:
        inner = '<span class="badge neutral">0%</span>'
    else:
        raw = (n - o) / o * 100
        is_buff = (n < o) if lower else (n > o)
        disp = ('+' if n > o else '-') + f'{round(abs(raw), 1):g}%'
        inner = f'<span class="badge {gradient_class(abs(raw), is_buff)}">{disp}</span>'
    return f'<span class="badge-group">{inner}</span>'


def formula_change(name, old, new, *, tag="REWORK", vary=None, fixed=None,
                   unit="", lower_better=False):
    _TAG = {'NEW': ('new', 'new'), 'REWORK': ('rework', 'rework'),
            'BUFF': ('buff-text', 'buff'), 'NERF': ('nerf-text', 'nerf'),
            'DEL': ('del', 'del'), 'MISC': ('misc', 'misc'), 'QOL': ('qol', 'qol')}
    badge_cls, tag_id = _TAG.get(tag.upper(), (tag.lower(), tag.lower()))
    badge = f'<span class="badge {badge_cls}" data-tag="{tag_id}">{tag}</span>'
    has_ex = bool(vary)
    has_input = bool(vary and fixed)
    input_html = ''
    data_attrs = ''
    if has_input:
        var_name, label, values = vary
        in_var = next(iter(fixed))
        in_def = fixed[in_var]
        def_disp = f'{in_def:,}' if isinstance(in_def, int) else f'{in_def:g}'
        input_html = (
            '<div class="formula-input-row">'
            f'<span class="formula-input-label">Set <span class="fx-vname">{in_var}</span>:</span>'
            '<input type="number" class="formula-input" min="0" inputmode="numeric" '
            f'placeholder="By default: {def_disp}"></div>')
        data_attrs = (
            f' data-fx-old="{_html.escape(old, quote=True)}"'
            f' data-fx-new="{_html.escape(new, quote=True)}"'
            f' data-fx-invar="{in_var}" data-fx-default="{in_def}"'
            f' data-fx-varyvar="{var_name}" data-fx-lower="{1 if lower_better else 0}"')

    def _ex_table(this_is_old):
        if not has_ex:
            return ''
        var_name, label, values = vary
        th_pct = '' if this_is_old else '<th class="fx-pct-h">Δ%</th>'
        head = f'<thead><tr><th>{label}</th><th>{unit}</th>{th_pct}</tr></thead>'
        body = ''
        for v in values:
            env = dict(fixed or {})
            env[var_name] = v
            oval = _eval_formula(old, env)
            nval = _eval_formula(new, env)
            if this_is_old:
                body += (f'<tr data-h="{v}"><td class="fx-k">{v}</td>'
                         f'<td class="fx-gold">{_num_fmt(oval)}</td></tr>')
            else:
                body += (f'<tr data-h="{v}"><td class="fx-k">{v}</td>'
                         f'<td class="fx-gold">{_num_fmt(nval)}</td>'
                         f'<td class="fx-pct">{_formula_pct_badge(oval, nval, lower_better)}</td></tr>')
        return f'<table class="formula-ex">{head}<tbody>{body}</tbody></table>'

    def _pane(expr, cls, is_old):
        return (f'<div class="formula-pane formula-pane-{cls}">'
                f'<code class="formula-expr">{_fmt_formula(expr)}</code>'
                f'{_ex_table(is_old)}</div>')

    return (f'<div class="formula-change" data-tag="{tag_id}"{data_attrs}>'
            f'<div class="formula-change-title">{badge}'
            f'<span class="formula-change-name">{name}</span></div>'
            f'{input_html}'
            f'<div class="formula-change-panes">'
            f'{_pane(old, "old", True)}'
            f'<span class="ability-change-arrow">→</span>'
            f'{_pane(new, "new", False)}'
            f'</div></div>')


def cm_draft(*phases, first_label="First pick", second_label="Second pick"):
    if not phases:
        return ''
    full_old = ''.join(o for _, o, _ in phases)
    full_new = ''.join(n for _, _, n in phases)
    if len(full_new) != len(full_old):
        raise ValueError('cm_draft: old and new draft sequences differ in length')

    def _num(step, team, gr):
        side = 'cm-to-left' if team == 'first' else 'cm-to-right'
        return (f'<span class="cm-vnum {side}" '
                f'style="grid-column:2;grid-row:{gr}">{step}</span>')

    def _slot(team, kind, gr, span):
        col = 1 if team == 'first' else 3
        side = 'cm-left' if team == 'first' else 'cm-right'
        gr_v = f'{gr}/span {span}' if span > 1 else f'{gr}'
        return (f'<span class="cm-token {kind} {side}" '
                f'style="grid-column:{col};grid-row:{gr_v}"></span>')

    def _board(which):
        seq = full_old if which == 'Old' else full_new
        cells = [
            f'<span class="cm-vhead" style="grid-column:1;grid-row:1">{first_label}</span>',
            '<span class="cm-vnum cm-vnum-head" style="grid-column:2;grid-row:1"></span>',
            f'<span class="cm-vhead" style="grid-column:3;grid-row:1">{second_label}</span>',
        ]
        def _team(ch):
            return 'first' if ch in 'Ff' else 'second'
        row = 2
        i = 0
        n = len(seq)
        while i < n:
            a = seq[i]
            if a in 'fs':
                if (i + 1 < n and seq[i + 1] in 'fs'
                        and _team(seq[i + 1]) != _team(a)):
                    b = seq[i + 1]
                    cells.append(_num(i + 1, _team(a), row))
                    cells.append(_num(i + 2, _team(b), row + 1))
                    cells.append(_slot(_team(a), 'pick', row, 2))
                    cells.append(_slot(_team(b), 'pick', row, 2))
                    row += 2
                    i += 2
                else:
                    cells.append(_num(i + 1, _team(a), f'{row}/span 2'))
                    cells.append(_slot(_team(a), 'pick', row, 2))
                    row += 2
                    i += 1
            else:
                cells.append(_num(i + 1, _team(a), row))
                cells.append(_slot(_team(a), 'ban', row, 1))
                row += 1
                i += 1
        grid = f'<div class="cm-vgrid">{"".join(cells)}</div>'
        return f'<div class="cm-board">{grid}</div>'

    boards = (f'<div class="cm-boards">{_board("Old")}'
              f'<span class="cm-arrow">→</span>'
              f'{_board("New")}</div>')
    return f'<div class="cm-draft"><div class="cm-scroll">{boards}</div></div>'


def components(*parts, total, recipe=None):
    cells = []
    def cell(slug, name, cost):
        return (
            f'<div class="component">'
            f'<img src="{ITEM_CDN}{slug}.png" alt="{name}" title="{name}" loading="lazy">'
            f'<div class="component-price">{cost}</div>'
            f'</div>'
        )
    for name, cost in parts:
        slug = ITEM_SLUG.get(name, name.lower().replace(' ', '_').replace("'", ''))
        cells.append(cell(slug, name, cost))
    if recipe:
        rname, rcost = recipe
        cells.append(cell('recipe', rname, rcost))
    body = '<span class="components-plus">+</span>'.join(cells)
    return (f'<div class="components-box">'
            f'<div class="components-row">{body}</div>'
            f'<div class="components-total">= <span>{total}</span></div>'
            f'</div>')


def item_cost(gold):
    return (f'<div class="item-cost-box">'
            f'<span class="item-cost-label">Cost</span>'
            f'<span class="item-cost-val">{gold}</span>'
            f'</div>')


def provides(*items):
    if len(items) == 1 and isinstance(items[0], str) and ',' in items[0]:
        items = [s.strip() for s in items[0].split(',') if s.strip()]
    rows = ''.join(f'<div class="provides-row">{it}</div>' for it in items)
    return f'<div class="provides-box">{rows}</div>'


def _prop_tag(tag):
    if not tag:
        return '<span class="row-tag-empty"></span>'
    key = tag.upper()
    cls = _PROP_TAG_CSS.get(key, 'misc')
    overall = 'buff' if key in ('BUFF', 'NEW') else ('nerf' if key in ('NERF', 'DEL') else 'buff')
    return f'<span class="badge {cls}" data-tag="{key.lower()}" data-overall="{overall}">{key}</span>'


def _prop_cells(row):
    if row is None:
        return ('', '', '')
    if isinstance(row, str):
        return ('', row, '')
    if len(row) == 2:
        return (row[0], row[1], '')
    return (row[0], row[1], row[2])


def properties_change(old, new, old_extras=None, new_extras=None):
    old_extras = old_extras or {}
    new_extras = new_extras or {}
    n = max(len(old), len(new))
    old_rows = list(old) + [None] * (n - len(old))
    new_rows = list(new) + [None] * (n - len(new))
    _DYN_PROP_MAP = {"BUFF": "buff", "NERF": "nerf", "NEW": "new",
                     "DEL": "del", "REWORK": "rework", "MISC": "misc",
                     "QoL": "qol"}
    for row in list(old) + list(new):
        if isinstance(row, (tuple, list)) and len(row) >= 1:
            tag = row[0]
            tid = _DYN_PROP_MAP.get(tag)
            if tid:
                _dyn_record_li({tid})

    def pane_cells(rows, extras):
        cells = []
        cur_row = 1
        for i, row in enumerate(rows):
            if row is None:
                cells.append(
                    f'<span class="property-row-empty" '
                    f'style="grid-row:{cur_row};grid-column:1/-1">&nbsp;</span>'
                )
            else:
                tag, text, badge = _prop_cells(row)
                if badge:
                    cells.append(
                        f'<span class="property-tag" style="grid-row:{cur_row};grid-column:1">'
                        f'{_prop_tag(tag)}</span>'
                        f'<span class="property-text" style="grid-row:{cur_row};grid-column:2">'
                        f'{text}</span>'
                        f'<span class="property-badge" style="grid-row:{cur_row};grid-column:3">'
                        f'{badge}</span>'
                    )
                else:
                    cells.append(
                        f'<span class="property-tag" style="grid-row:{cur_row};grid-column:1">'
                        f'{_prop_tag(tag)}</span>'
                        f'<span class="property-text" style="grid-row:{cur_row};grid-column:2/-1">'
                        f'{text}</span>'
                    )
            cur_row += 1
            ex = extras.get(i, '')
            if ex:
                cells.append(
                    f'<div class="property-extra" '
                    f'style="grid-row:{cur_row};grid-column:2/-1">{ex}</div>'
                )
                cur_row += 1
        return ''.join(cells), cur_row - 1

    old_empty = not old or all(r is None for r in old)
    new_empty = not new or all(r is None for r in new)
    old_body, old_n = pane_cells(old_rows, old_extras)
    new_body, new_n = pane_cells(new_rows, new_extras)
    total_rows = max(old_n, new_n)

    if old_empty and not new_empty:
        return (
            f'<div class="properties-change new-only" '
            f'style="grid-template-rows:repeat({new_n},auto)">'
            f'<span class="properties-arrow" aria-hidden="true" '
            f'style="visibility:hidden">→</span>'
            f'<div class="properties-pane pane-new">{new_body}</div>'
            f'</div>'
        )
    if new_empty and not old_empty:
        return (
            f'<div class="properties-change old-only" '
            f'style="grid-template-rows:repeat({old_n},auto)">'
            f'<div class="properties-pane pane-old">{old_body}</div>'
            f'<span class="properties-arrow" aria-hidden="true" '
            f'style="visibility:hidden">→</span>'
            f'</div>'
        )

    return (
        f'<div class="properties-change" '
        f'style="grid-template-rows:repeat({total_rows},auto)">'
        f'<div class="properties-pane pane-old">{old_body}</div>'
        f'<span class="properties-arrow">→</span>'
        f'<div class="properties-pane pane-new">{new_body}</div>'
        f'</div>'
    )


def _component_cell(name, cost, mark=None):
    slug = ITEM_SLUG.get(name, name.lower().replace(' ', '_').replace("'", ''))
    if name.lower() == 'recipe':
        slug = 'recipe'
    cls = 'component'
    if mark == 'added':
        cls += ' component-added'
    elif mark == 'removed':
        cls += ' component-removed'
    return (f'<div class="{cls}">'
            f'<img src="{ITEM_CDN}{slug}.png" alt="{name}" title="{name}" loading="lazy">'
            f'<div class="component-price">{cost}</div></div>')


def _components_side(parts, recipe, total, marks):
    cells = [_component_cell(n, c, marks.get(n)) for n, c in parts]
    if recipe:
        cells.append(_component_cell(recipe[0], recipe[1]))
    body = '<span class="components-plus">+</span>'.join(cells)
    return (f'<div class="components-row">{body}</div>'
            f'<div class="components-total">= <span>{total}</span></div>')


def components_change(old, new, total_old, total_new,
                      recipe_old=None, recipe_new=None,
                      added=None, removed=None):
    marks_old = {name: 'removed' for name in (removed or [])}
    marks_new = {name: 'added' for name in (added or [])}
    return (f'<div class="components-change">'
            f'<div class="components-box components-pane">'
            f'{_components_side(old, recipe_old, total_old, marks_old)}'
            f'</div>'
            f'<span class="components-arrow">→</span>'
            f'<div class="components-box components-pane">'
            f'{_components_side(new, recipe_new, total_new, marks_new)}'
            f'</div>'
            f'</div>')


def aghs_line(text, kind="scepter", inline_note_text=None):
    note = (f'<div class="inline-note">{inline_note_text}</div>'
            if inline_note_text else '')
    return (f'<div class="ability-change-row aghanim-{kind}">'
            f'<span class="aghanim-marker {kind}"></span>{text}{note}</div>')


def aghs_shard_line(text):
    return aghs_line(text, kind="shard")


def ability_change(old, new, summary=None, tag=None):
    if tag == 'new':
        _dyn_record_li({'new'})
    elif tag == 'rework':
        _dyn_record_li({'rework'})
    else:
        _dyn_record_li({'new', 'del', 'rework'})
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if _State.current_hero and not _State.seen_abilities_subgroup:
        out += '<h4 class="subgroup">Abilities</h4>'
        _State.seen_abilities_subgroup = True

    def _resolve_icon(spec):
        icon_url = spec.get("icon_url")
        used_innate_fallback = False
        if not icon_url:
            slug = spec.get("slug")
            if slug:
                icon_url = f"{ABIL_CDN}{slug}.png"
            elif spec.get("innate"):
                icon_url = INNATE_ICON_URL
                used_innate_fallback = True
            else:
                icon_url = MISSING_ICON_URL
        return icon_url, used_innate_fallback

    single_new = old is None
    _new_icon, _ = _resolve_icon(new)
    _new_rows = len(new.get("desc", []))
    if single_new:
        _old_icon, _old_rows = _new_icon, 0
        in_place = new_taller_inplace = False
    else:
        _old_icon, _ = _resolve_icon(old)
        _old_rows = len(old.get("desc", []))
        in_place = (old["name"] == new["name"]) and (_old_icon == _new_icon)
        new_taller_inplace = in_place and (_new_rows > _old_rows)

    unified = (summary is not None) or (tag is not None) or single_new
    if not in_place and not unified and abs(_old_rows - _new_rows) >= 2:
        compact_side = 'old' if _old_rows < _new_rows else 'new'
    else:
        compact_side = None

    def _side(spec, kind):
        name = spec["name"]
        icon_url, used_innate_fallback = _resolve_icon(spec)
        innate_cls = ' is-innate' if spec.get("innate") else ''
        innate_marker = (
            f'<img src="{INNATE_ICON_URL}" alt="" '
            f'class="innate-marker">'
            if spec.get("innate") and not used_innate_fallback else ''
        )
        desc_html = ''.join(
            (d if isinstance(d, str) and d.lstrip().startswith('<div')
             else f'<div class="ability-change-row">{d}</div>')
            for d in spec.get("desc", []))
        tables_html = ''.join(
            f'<div class="formula-table-wrap">{tbl}</div>'
            for tbl in (spec.get("tables", []) or [])
        )
        if unified:
            head_html = ''
        else:
            placeholder_cls = ' is-placeholder' if (in_place and kind == 'new') else ''
            head_html = (
                f'<div class="ability-change-head{placeholder_cls}">'
                f'<div class="ability-change-icon-wrap">'
                f'<img class="ability-change-icon" src="{icon_url}" alt="{name}" '
                f'loading="lazy" onerror="this.onerror=null;'
                f'var m=this.parentElement.querySelector(\'.innate-marker\');'
                f'if(m)m.style.display=\'none\';'
                f'this.src=\'{INNATE_ICON_URL}\';">'
                f'{innate_marker}'
                f'</div>'
                f'<div class="ability-change-name">{name}</div>'
                f'</div>'
            )
        return (
            f'<div class="ability-change-pane ability-change-{kind}{innate_cls}">'
            f'{head_html}'
            f'<div class="ability-change-body">{desc_html}{tables_html}</div>'
            f'</div>'
        )

    extra_cls = ''
    if in_place:
        extra_cls = ' is-in-place'
        if new_taller_inplace:
            extra_cls += ' is-new-taller'
    elif compact_side == 'old':
        extra_cls = ' compact-old'
    elif compact_side == 'new':
        extra_cls = ' compact-new'

    if unified:
        _State.next_ul_is_hero_stats = False
        if _State.current_hero and not _State.seen_abilities_subgroup:
            out = ''
            out += '<h4 class="subgroup">Abilities</h4>'
            _State.seen_abilities_subgroup = True
        unified_icon = _new_icon
        is_innate = bool(new.get("innate"))
        old_is_innate = (not single_new) and bool(old.get("innate"))
        has_old_underlay = (not single_new) and (_old_icon != _new_icon)
        new_marker_html = (
            f'<img src="{INNATE_ICON_URL}" alt="" '
            f'class="innate-marker innate-marker-new">'
            if is_innate and _new_icon != INNATE_ICON_URL else ''
        )
        old_marker_html = (
            f'<img src="{INNATE_ICON_URL}" alt="" '
            f'class="innate-marker innate-marker-old">'
            if (has_old_underlay and old_is_innate
                and _old_icon != INNATE_ICON_URL) else ''
        )
        on_err = (
            "this.onerror=function(){this.style.display='none'};"
            "var m=this.parentElement.querySelector('.innate-marker-new');"
            "if(m)m.style.display='none';"
            f"this.src='{INNATE_ICON_URL}';"
        )
        old_underlay_html = ''
        if has_old_underlay:
            old_on_err = (
                "this.onerror=function(){this.style.display='none'};"
                f"this.src='{INNATE_ICON_URL}';"
            )
            old_underlay_html = (
                f'<img src="{_old_icon}" alt="" '
                f'class="ability-icon-old-underlay" loading="lazy" '
                f'onerror="{old_on_err}">'
            )
        wrap_cls = 'ability-icon-wrap'
        if has_old_underlay:
            wrap_cls += ' has-old-underlay'
        icon_html = (
            f'<div class="{wrap_cls}">'
            f'{old_underlay_html}'
            f'<img src="{unified_icon}" alt="{new["name"]}" '
            f'class="ability-icon-img" loading="lazy" onerror="{on_err}">'
            f'{new_marker_html}'
            f'{old_marker_html}'
            f'</div>'
        )
        same_name = single_new or (old["name"] == new["name"])
        if same_name:
            title_inner = new["name"]
        else:
            title_inner = (
                f'<span class="ability-title-old">{old["name"]}</span>'
                f'<span class="ability-title-arrow">→</span>'
                f'<span class="ability-title-new">{new["name"]}</span>'
            )
        title_html = f'<h4 class="ability-title">{title_inner}</h4>'
        tag_key = (tag or '').lower()
        if tag_key not in ('new', 'rework'):
            tag_key = 'new'
        tag_label = tag_key.upper()
        summary_row = (
            f'<ul class="changes ability-change-summary-ul">'
            f'<li data-tag="{tag_key}">'
            f'<span class="badge {tag_key}" data-tag="{tag_key}">{tag_label}</span>'
            f'<span class="row-text">{summary or ""}</span>'
            f'</li>'
            f'</ul>'
        )
        _State.ability_block_open = True
        block_cls = 'ability-block ability-change-block'
        if is_innate:
            block_cls += ' is-innate'
        connector_html = '' if single_new else (
            '<svg class="ability-change-connector" '
            'viewBox="0 0 100 100" preserveAspectRatio="none" '
            'aria-hidden="true">'
            '<path d="" fill="none" '
            'stroke="rgba(139, 148, 158, 0.45)" stroke-width="1.3" '
            'stroke-dasharray="3 3" stroke-linecap="round" />'
            '</svg>'
        )
        if single_new:
            panes_html = (
                f'<div class="ability-change unified-panes is-single-new" '
                f'data-tag="new">'
                f'{_side(new, "new")}'
                f'</div>'
            )
        else:
            panes_html = (
                f'<div class="ability-change unified-panes{extra_cls}" '
                f'data-tag="new del rework">'
                f'{_side(old, "old")}'
                f'<span class="ability-change-arrow">→</span>'
                f'{_side(new, "new")}'
                f'</div>'
            )
        return out + (
            f'<div class="{block_cls}">'
            f'{icon_html}'
            f'{title_html}'
            f'{summary_row}'
            f'{connector_html}'
            f'{panes_html}'
        )

    return out + (
        f'<div class="ability-change{extra_cls}" data-tag="new del rework">'
        f'{_side(old, "old")}'
        f'<span class="ability-change-arrow">→</span>'
        f'{_side(new, "new")}'
        f'</div>'
    )


def _enchant_tooltip(name, tiers):
    desc = _ENCHANT_DESC.get(name, {})
    if isinstance(tiers, int):
        tiers = [tiers]
    parts = []
    multi = len([t for t in tiers if t in desc]) > 1
    for t in tiers:
        lines = desc.get(t)
        if not lines:
            continue
        body = "\n".join(lines)
        parts.append(f"Tier {t}\n{body}" if multi else body)
    return "\n\n".join(parts) if parts else name


def _enchant_chip(name, tiers):
    slug = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
    icon = f"{ITEM_CDN}enhancement_{slug}.png"
    tooltip = _html.escape(_enchant_tooltip(name, tiers), quote=True)
    return (f'<span class="enchant-chip" data-tooltip="{tooltip}">'
            f'<img src="{icon}" alt="{name}" loading="lazy">'
            f'<span>{name}</span></span>')


def souvenir_chip(name, slug, removed=False, tooltip=None):
    icon = f"{ABIL_CDN}{slug}.png"
    cls = "enchant-chip souvenir-chip" + (" removed" if removed else "")
    tip_attr = ''
    if tooltip:
        tip_attr = f' data-tooltip="{_html.escape(tooltip, quote=True)}"'
    return (f'<span class="{cls}"{tip_attr}>'
            f'<img src="{icon}" alt="" loading="lazy">'
            f'<span>{name}</span></span>')


def enchant_attr_row(attr, enchantments, tiers):
    if attr == "all":
        icons = ''.join(
            f'<img src="{_ATTR_ICON[a]}" alt="">' for a in ("str", "agi", "int", "uni")
        )
        label = (f'<span class="enchant-attr-icons all-attrs">{icons}</span>'
                 f'<span class="enchant-attr-name is-all">All Heroes</span>')
    else:
        label = (f'<img class="enchant-attr-ico" src="{_ATTR_ICON[attr]}" alt="">'
                 f'<span class="enchant-attr-name is-{attr}">{_ATTR_LABEL[attr]}</span>')
    chips = ''.join(_enchant_chip(e, tiers) for e in enchantments)
    return (f'<div class="enchant-attr-row">'
            f'<div class="enchant-attr-label">{label}</div>'
            f'<div class="enchant-attr-list">{chips}</div>'
            f'</div>')


def enchant_tier_box(rows, tiers):
    body = ''.join(enchant_attr_row(a, es, tiers) for a, es in rows)
    return f'<div class="enchant-attr-grid">{body}</div>'


_BULLET_SPLIT = re.compile(r'(?:^|<br>)+\s*\*\s+', re.I)


def subnote(text):
    parts = _BULLET_SPLIT.split(text)
    intro_raw = parts[0] if parts else ''
    items = [p.strip() for p in parts[1:] if p.strip()]
    if len(items) >= 3:
        intro = re.sub(r'<br>+\s*$', '', intro_raw).rstrip(' :').strip()
        items_html = ''.join(f'<li>{it}</li>' for it in items)
        summary = (intro if intro else 'Show list') + \
                  f' <span class="subnote-count">({len(items)})</span>'
        return ('<ul class="subnotes"><li>'
                f'<details class="subnote-collapse">'
                f'<summary>{summary}</summary>'
                f'<ul class="subnote-items">{items_html}</ul>'
                '</details></li></ul>')
    return f'<ul class="subnotes"><li>{text}</li></ul>'


def section_intro(text):
    return f'<p class="section-intro">{text}</p>'


def _days_ago(version):
    if not version:
        return None
    from .meta import RELEASE_HISTORY
    date_str = None
    for row in RELEASE_HISTORY:
        if row.get('version') == version:
            date_str = row.get('date')
            break
    if not date_str:
        return None
    from datetime import datetime, date
    try:
        d = datetime.strptime(date_str, "%d.%m.%Y").date()
    except Exception:
        return None
    return (date.today() - d).days


def _patch_link(version):
    if not version:
        return ''
    return f'<span class="patch-ref"><b>{version}</b></span>'


def _format_age(days):
    if days is None:
        return None
    if days < 365:
        return f"{days} days ago"
    years = days // 365
    months = (days % 365) // 30
    yr = f"{years} year{'s' if years != 1 else ''}"
    if months == 0:
        return f"{yr} ago"
    mo = f"{months} month{'s' if months != 1 else ''}"
    return f"{yr} {mo} ago"


def _fmt_val(v):
    if v is None:
        return "?"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def note_box(text=None, *, hero=None, item=None, unit=None, field=None, before_patch=None,
             prev_val=None, prev_patch=None, new_val=None, extra_note=None):
    from .stats import stat_h, stat_i, stat_u, prev_change_patch_h, prev_change_patch_i, prev_change_patch_u
    cur = _State.current_patch_version
    if prev_val is None and (hero or item or unit):
        if hero:
            prev_val = stat_h(hero, field, before_patch)
            prev_patch = prev_change_patch_h(hero, field, before_patch) or before_patch
            if new_val is None and cur:
                new_val = stat_h(hero, field, cur)
        elif item:
            prev_val = stat_i(item, field, before_patch)
            prev_patch = prev_change_patch_i(item, field, before_patch) or before_patch
            if new_val is None and cur:
                new_val = stat_i(item, field, cur)
        else:
            prev_val = stat_u(unit, field, before_patch)
            prev_patch = prev_change_patch_u(unit, field, before_patch) or before_patch
            if new_val is None and cur:
                new_val = stat_u(unit, field, cur)
    show_val = new_val if new_val is not None else prev_val
    if show_val is not None and prev_patch is not None:
        if isinstance(prev_patch, str) and prev_patch.startswith("<"):
            ver = prev_patch[1:]
            tail = (f'Unchanged across all tracked patches '
                    f'(since {_patch_link(ver)}) — first recorded change')
        else:
            ago_phrase = _format_age(_days_ago(prev_patch))
            ago_str = f' <span class="days-ago">({ago_phrase})</span>' if ago_phrase else ''
            tail = f'Before this patch it was changed in {_patch_link(prev_patch)}{ago_str}'
        body = f"Now it's <b>{_fmt_val(show_val)}</b>. {tail}"
        if extra_note:
            body += f'<br>{extra_note}'
        return f'<!--INLINETIP-->{info_tip(body)}<!--/INLINETIP-->'
    note = text or ""
    if extra_note:
        note = f'{note}<br>{extra_note}' if note else extra_note
    return f'<!--INLINETIP-->{info_tip(note, header="Note:")}<!--/INLINETIP-->'


def li_formula(prefix, old_formula, new_formula, old_fn, new_fn, l=False,
               rework_badge=True, inline_note_text=None, **bf_kwargs):
    from .badges import bf
    trigger, badge, table = bf(old_fn, new_fn, new_formula, l=l, **bf_kwargs)
    full_text = (f'{prefix} from <span class="formula-old">{old_formula}</span> '
                 f'to {trigger}')
    overall_match = re.search(r'data-overall="(buff|nerf)"', badge)
    force_match = re.search(r'data-force-left="(buff|nerf)"', badge)
    kind = (force_match.group(1) if force_match
            else overall_match.group(1) if overall_match
            else None)
    if kind:
        cls = "buff-text" if kind == "buff" else "nerf-text"
        label = "BUFF" if kind == "buff" else "NERF"
        full_badge = (f'<span class="badge {cls}" data-tag="{kind}" '
                      f'data-overall="{kind}">{label}</span>' + badge)
    elif bf_kwargs.get('effective_unchanged'):
        full_badge = ('<span class="badge misc" data-tag="misc">MISC</span>'
                      + badge)
    elif rework_badge:
        full_badge = ('<span class="badge rework" data-tag="rework">REWORK</span>'
                      + badge)
    else:
        full_badge = badge
    extra = table
    if inline_note_text:
        extra = inline_note(inline_note_text) + extra
    return li(full_text, full_badge, extra=extra)


def auto_components_change(item_display, this_version):
    from .stats import _STATS_I
    from .meta import RELEASE_HISTORY

    def _patch_index(version):
        for i, p in enumerate(RELEASE_HISTORY):
            if p['version'] == version:
                return i
        return None

    def _prev_patch_version(version):
        idx = _patch_index(version)
        if idx is None or idx + 1 >= len(RELEASE_HISTORY):
            return None
        return RELEASE_HISTORY[idx + 1]['version']

    def _next_patch_version(version):
        idx = _patch_index(version)
        if idx is None or idx == 0:
            return None
        return RELEASE_HISTORY[idx - 1]['version']

    def _get_recipe(item_display, version):
        raw_slug = ITEM_SLUG.get(item_display,
                                  item_display.lower().replace(' ', '_').replace("'", ''))
        bucket = _STATS_I.get(version, {})
        recipe_entry = bucket.get(f'item_recipe_{raw_slug}', {})
        req = recipe_entry.get('ItemRequirements', {}).get('01') if recipe_entry else None
        recipe_cost = recipe_entry.get('ItemCost', 0) if recipe_entry else 0
        item_entry = bucket.get(f'item_{raw_slug}', {})
        total = item_entry.get('ItemCost')
        if not req or total is None:
            return None
        parts = []
        raw_slugs = []
        for part in req.split(';'):
            part = part.strip().rstrip('*')
            if not part:
                continue
            comp_cost = bucket.get(part, {}).get('ItemCost', 0)
            parts.append((_item_display_name(part), comp_cost))
            raw_slugs.append(part)
        return {'components': parts, 'recipe_cost': recipe_cost,
                'total': total, 'raw_slugs': raw_slugs}

    prev_v = _prev_patch_version(this_version)
    if not prev_v:
        return f'<!-- auto_components_change: no prev for {this_version} -->'
    old = _get_recipe(item_display, prev_v)
    new = _get_recipe(item_display, this_version)
    if old and new and old['raw_slugs'] == new['raw_slugs'] \
       and old['recipe_cost'] == new['recipe_cost'] \
       and old['total'] == new['total']:
        nxt = _next_patch_version(this_version)
        while nxt:
            candidate = _get_recipe(item_display, nxt)
            if candidate and (candidate['raw_slugs'] != old['raw_slugs']
                              or candidate['recipe_cost'] != old['recipe_cost']
                              or candidate['total'] != old['total']):
                new = candidate
                break
            nxt = _next_patch_version(nxt)
    if not old or not new:
        return (f'<!-- auto_components_change: recipe missing for '
                f'{item_display} in {prev_v}/{this_version} -->')
    leftover_new = [n for n, _ in new['components']]
    leftover_old = [n for n, _ in old['components']]
    for n in list(leftover_new):
        if n in leftover_old:
            leftover_old.remove(n)
            leftover_new.remove(n)
    added = list(dict.fromkeys(leftover_new))
    removed = list(dict.fromkeys(leftover_old))
    if (not added and not removed
            and old['recipe_cost'] == new['recipe_cost']
            and old['total'] == new['total']):
        return (f'<!-- auto_components_change: no top-level diff for '
                f'{item_display} between {prev_v}/{this_version} '
                f'(sub-component change?) -->')
    return components_change(
        old=old['components'],
        new=new['components'],
        recipe_old=('Recipe', old['recipe_cost']) if old['recipe_cost'] else None,
        recipe_new=('Recipe', new['recipe_cost']) if new['recipe_cost'] else None,
        total_old=old['total'],
        total_new=new['total'],
        added=added or None,
        removed=removed or None,
    )
