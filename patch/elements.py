"""HTML builder functions — li, ul, section, ability, item, hero headers, etc. The cards live in their own modules
(cards_hero_stats, cards_aghs, cards_item_abilities, cards_item_stats, cards_ability_change; audit 2026-10-26 #8), and
so do the enchantments, row scoring, terrain notes, formulas, Captains Mode and note boxes (2026-11-07,
docs/architecture.md)."""

import html as _html
import json as _json
import os as _os
from .weights import row_scores as _row_scores
import re

from .images import (ITEM_CDN, ABIL_CDN, HERO_SLUG, ITEM_SLUG, hero_img,
                     item_img, _LOCAL_ABIL_ICONS)
from .state import _State
from .mech_abilities import LIST_TIPS, TIP_RAW, ability_chip, lift_ability_lists, row_examples, rune_row_chip
from .row_scores import (_TOTAL_UNCHANGED_RE, _cost_panel_covered, _dyn_record_li, _flush_cell_rows, _flush_cost_panel,
                         _flush_damage_rows, _flush_rework, _note_cell_row, _note_damage_row, _row_ctx,
                         _score_folded_damage)
from .terrain_notes import terrain_button, terrain_note, terrain_num_chip

try:
    with open(_os.path.join(_os.path.dirname(__file__), '..', 'data', 'abilities_slim.json'),
              encoding='utf-8') as _f:
        _SLIM_CACHE = _json.loads(_f.read())
except Exception:
    _SLIM_CACHE = {}

# ---- Icon / placeholder URLs ----
TALENT_ICON_URL  = "../icons/misc/talents.svg"
INNATE_ICON_URL  = "../icons/misc/innate_icon.png"
MISSING_ICON_URL = "../icons/misc/missing.svg"
# subgroup headings that only label a list: hidden under a tag filter (src/css/patch-formula-tables.css)
GENERIC_SUBGROUPS = {"abilities", "facets", "talents", "general"}
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
    "health_regen":      "../icons/health_regen.svg",     # scripts/gen/gen_regen_icons.py (owner 2026-11-06)
    "mana_regen":        "../icons/mana_regen.svg",
}

STAT_DETECT_RULES = [
    ("health_regen",      ("health regen", "hp regen")),
    ("mana_regen",        ("mana regen",)),
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
    'SWAP': 'swap',
    'MISC':   'misc',
    'QOL':    'qol',
    'NEW':    'new',
    'DEL':    'del',
}

# ---- Ability display-name → CDN slug overrides ----
ABILITY_DISPLAY_TO_SLUG = {
    ("antimage", "Persecutor"): "persectur",
    ("grimstroke", "Soulbind"): "soul_chain",
    ("luna", "Bouncing Glaives"): "moon_glaive",
    ("luna", "Moon Glaives"): "moon_glaive",
    ("ogre_magi", "Fire Shield"): "smash",
    ("centaur", "Retaliate"): "return",
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

def _mech_tag(label):
    """A "Reworked objective / mechanic" block describes how the REWORKED thing works now: its
    REWORK rows form the description box. Any other label (New mechanic / New objective): NEW rows."""
    return "rework" if isinstance(label, str) and label.lower().startswith("reworked") else "new"


def _open_block(extra_cls='', extra_attrs=''):
    _flush_cost_panel()                                   # the previous item's components panel
    _flush_damage_rows()                                  # the previous hero's damage rows, once
    _flush_cell_rows()                                    # ... its replacements (before signal R)
    _flush_rework()                                       # ... and its REWORK rows (signal R)
    pre = _close_ability_block()
    _State.new_mech_header = _State.new_mech = False     # a new block ends any "new mechanic" run
    _State.new_mech_one_box = False
    _State.terrain_rows = None                            # ... and any terrain block
    cls = 'entity-block' + ((' ' + extra_cls) if extra_cls else '')
    s = (pre + ('</div>\n' if _State.block_open else '')
         + f'<div class="{cls}"{extra_attrs}>\n')
    _State.block_open = True
    # A new entity block starts a new weights context: the ability slug of the previous hero's
    # last ability() block must not leak into units / items / enchantments (it gave Tormentor rows
    # Wraith King's ultimate x1.3 and enchantment rows Zeus' skill-priority multiplier).
    _State.current_ability_slug = None
    _State.current_ability_innate = False
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
    _flush_cost_panel()
    _flush_damage_rows()
    _flush_cell_rows()
    _flush_rework()
    out = _close_ability_block()
    if _State.block_open:
        _State.block_open = False
        out += '</div>\n'
    return out


def _close_ability_block():
    cards = _aghs_parts_cards()                 # an ability with no rows under it draws its card here
    if _State.ability_block_open:
        _State.ability_block_open = False
        _State.current_block_is_facet = False
        _State.facet_block_had_ul = False
        return cards + '</div>\n'
    return cards


def _entity_link(folder, name):
    """Patch page -> the entity's Changes page (builders/entity_changes.py), same slug as its
    dyn id: ../heroes/<slug>.html / ../items/<slug>.html."""
    ver = _State.current_patch_version
    return f"../{folder}/{_slugify(name)}.html" + (f"?from={ver}" if ver else "")


def _slugify(name):
    s = name.lower().replace("'", "").replace("’", "")
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def _register_entity(kind, name, force=False, slug=None):
    """force=True: tracked even inside General Updates (map units with their own Changes
    page: Roshan, Tormentor). slug: the page's own slug when it isn't the name's (a lane creep's card,
    "Flagbearer Creep" -> flagbearer-creep)."""
    if _State.current_section_slug == 'general' and not force:
        _State.current_entity_key = None
        _State.current_entity_display = None
        return ''
    slug = slug or _slugify(name)
    key = f"{kind}|{slug}"
    _State.current_entity_key = key
    _State.current_ability_kv = None
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
    _State.current_ability_slug = None
    _State.current_ability_innate = False
    _State.current_hero_title = name
    _State.current_hero = HERO_SLUG.get(name,name.lower().replace(" ", "_").replace("'", "").replace("-", ""))
    _State.current_unit = None
    _State.next_ul_is_hero_stats = True
    _State.seen_abilities_subgroup = False
    _State.seen_facets_subgroup = False
    eid = _register_entity("hero", name)
    href = _entity_link("heroes", name)
    return _open_block() + f'''<div class="entity hero-entity"{eid}>
  <div class="entity-icon hero-icon"><a class="entity-link" href="{href}" title="All changes of {name}"><img src="{hero_img(name)}" alt="{name}" loading="lazy" width="256" height="144"></a></div>
  <div class="entity-name"><a class="entity-link" href="{href}" title="All changes of {name}">{name}</a></div>
</div>'''


def unit_header(name, icon_url, kind=None, new=False, label=None, general=True, new_mech=None, track=False, page=None):
    """`new="New Neutral Creep"` renders the same NEW-entity block as
    item_header(new=...): is-new block + type label after the name. Pair it with unit_sheet(slug) for its numbers and t("NEW") ability rows (the
    is-new CSS hides per-row chips but keeps data-tag="new" for the filter).
    `label="Returning Ancient Melee Creep"` shows only the type label: a unit
    that comes back WITH numeric changes keeps its normal GENERAL block and
    per-row chips instead of a NEW card.
    general=False: no GENERAL block — a map unit / building (Roshan, Tormentor, Shrine of Wisdom,
    Lotus Pool): its rows follow the header directly.
    new_mech="New mechanic": label + description-box rows, as plain_header(new=…)."""
    _State.current_hero = None
    # A unit's own base-stat ul is rendered exactly like a hero's: the first ul
    # after the header becomes the GENERAL block (Spirit Bear 7.41e).
    _State.current_unit = name
    _State.seen_abilities_subgroup = False       # an ability() below gets the "Abilities" heading, as for heroes
    _State.next_ul_is_hero_stats = (not new) and general   # a NEW unit shows its unit_sheet instead
    kind_attr = f' data-kind="{kind}"' if kind else ''
    entity_kind = "creep-hero" if (kind and kind.lower().startswith("creep-hero")) else "unit"
    # page="flagbearer-creep": a lane creep's card in General Updates links to its unit page and gets the
    # patch strip, like any tracked unit (owner 2026-10-16: "Flagbearer Creep и Siege Creep не кликабельны")
    eid = _register_entity(entity_kind, name, force=track or bool(page), slug=page)
    if new:
        type_text = new if isinstance(new, str) else ''
        type_label = f' <span class="entity-new-type">{type_text}</span>' if type_text else ''
        extra_cls, block_attr = 'is-new', ' data-new-tag="NEW"'
    else:
        label = label or new_mech
        type_label = f' <span class="entity-new-type">{label}</span>' if label else ''
        extra_cls, block_attr = '', ''
    head = _open_block(extra_cls, block_attr)
    _State.new_mech_header = _State.new_mech = bool(new_mech)
    _State.new_mech_tag = _mech_tag(new_mech)
    img = f'<img src="{icon_url}" alt="{name}" loading="lazy" width="128" height="72">'
    if eid:          # a tracked unit has a Changes page (units/<slug>.html; a creep-hero lives with the heroes)
        href = _entity_link("heroes" if entity_kind == "creep-hero" else "units", page or name)
        img = f'<a class="entity-link" href="{href}">{img}</a>'
        name_html = f'<a class="entity-link" href="{href}">{name}</a>'
    else:            # General Updates (Roshan, Tormentor…): no dynamics id, no page
        name_html = name
    return head + f'''<div class="entity unit-entity"{kind_attr}{eid}>
  <div class="entity-icon hero-icon">{img}</div>
  <div class="entity-name">{name_html}{type_label}</div>
</div>'''


def _removed_label(removed):
    """("Neutral Item cycled out" / "Item removed" / "Enchantment removed") — an item that was only taken out: its
    label in the DEL colour where "Returning Tier 2 Artifact" stands; its one DEL row stays, hidden, for the filters
    (owner 2026-10-17: "the tag itself set hidden for the filters")."""
    return f' <span class="entity-removed-type">{removed}</span>', 'is-removed'


def item_header(name, new=False, changed=False, removed=None, old_title=None, cost=None):
    """old_title: a renamed item shows "Old → New" like a renamed ability, no "renamed to" row (owner 2026-10-22).
    cost: a new item's price, a tag on its icon instead of a line of its own (owner 2026-11-05, 7.38 Orb of Frost); a later
    change of the price is a row as ever."""
    out = _close_ability_block()
    _State.current_hero = None
    _State.current_unit = None
    if removed:
        type_label, extra_cls = _removed_label(removed)
        block_data_attr = ''
    elif new:
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
    href = _entity_link("items", name)
    name_html = f'<a class="entity-link" href="{href}" title="All changes of {name}">{name}</a>'
    if old_title and old_title != name:
        name_html = (f'<span class="ability-title-rename"><span class="ability-title-old">{old_title}</span>'
                     f'<span class="ability-title-arrow">→</span>{name_html}</span>')
    price = f'<span class="item-icon-cost" aria-label="Cost {cost}">{cost}</span>' if cost else ''
    # item-block: every framed box of an item hangs out on one common edge (CSS, owner 2026-09-28)
    return out + _open_block((extra_cls + ' item-block').strip(), block_data_attr) + f'''<div class="entity item-entity"{eid}>
  <div class="entity-icon item-icon"><a class="entity-link" href="{href}" title="All changes of {name}"><img src="{item_img(name)}" alt="{name}" loading="lazy" width="88" height="64"></a>{price}</div>
  <div class="entity-name">{name_html}{type_label}</div>
</div>'''


def plain_header(name, dynamics=True, terrain_link=None, sublabel=False, new=None, one_box=False):
    """new="New mechanic": a label after the title says the whole block is new; its NEW rows
    then drop the per-row chip (the header already says it) — other tags keep theirs. one_box: no row has a chip
    (owner 2026-10-30, 7.37 Breakability: "везде убрать теги"), as subgroup(one_box=True)."""
    out = _close_ability_block()
    _State.current_hero = None
    _State.current_unit = None
    if dynamics:
        eid = _register_entity("plain", name)
    else:
        _State.current_entity_key = None
        eid = ''
    link_html = ''
    if terrain_link:
        # every patch with terrain notes has its own Terrain page (builders/terrain.py)
        _tfile = f"terrain_{terrain_link.replace('.', '')}.html"
        # the page's first terrain block is #terrain: the Terrain page's patch label links to it (the owner
        # 2026-10-03: "click the patch switcher to jump to that patch")
        _anchor = '' if _State.terrain_anchor else ' id="terrain"'
        _State.terrain_anchor = True
        link_html = (
            f'<a class="terrain-jump-btn"{_anchor} href="../{_tfile}" '
            f'title="See these changes on the map">'
            f'<img src="../icons/ui/gothic/icon_terrain.png" alt="" width="16" height="16">'
            f'<span>View on map</span></a>')
    extra_cls = ' label-only' if sublabel else ''
    head = _open_block(extra_cls)
    if terrain_link:
        # terrain rows are numbered in their category, no tag (the owner 2026-10-03); data-tag stays for the
        # filters / weights
        _State.terrain_rows = 0
    _State.new_mech_header = _State.new_mech = bool(new)
    _State.new_mech_tag = _mech_tag(new)
    _State.new_mech_one_box = bool(new) and one_box
    label = f' <span class="entity-new-type">{new}</span>' if new else ''
    return out + head + f'<div class="entity plain-entity"{eid}><div class="entity-name">{name}{label}</div>{link_html}</div>'


def section(title):
    _State.current_hero = None
    _State.current_unit = None
    slug, label = _section_slug(title)
    _State.current_section_slug = slug
    _State.current_sections.append({'slug': slug, 'label': label})
    out = _close_block()
    if _State.section_panel_open:
        out += '</section>'
    # (the patch's date and official link left the first header for a card above the filters, page.patch_info_html)
    out += f'<section class="cat-panel"><h2 class="section" data-section="{slug}">{title}</h2>'
    _State.section_panel_open = True
    return out


def subgroup(title, new=None, one_box=False):
    """new="New mechanic": same as plain_header(new=…) for one subgroup (a label after the title,
    NEW rows of its lists without chips). Without it the subgroup inherits the header's state.
    one_box: with new=…, every row of its list in one description box whatever its tag, no chips (data-tag stays for
    the filters), a row's table inside the box (owner 2026-10-28, 7.41 Reflected Damage)."""
    _State.new_mech_one_box = bool(new) and one_box
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    # rows under a subgroup no longer belong to the last ability: Clockwerk 7.41's talents read as rows of the
    # Scepter-granted Overclocking card above them and got the Aghanim stripe (owner 2026-10-21)
    _State.current_ability_slug = None
    if _State.terrain_rows is not None:
        _State.terrain_rows = 0                           # each terrain category counts from 1
    _State.new_mech = bool(new) or _State.new_mech_header
    if new:
        _State.new_mech_tag = _mech_tag(new)
    if title.lower() == "abilities":
        _State.seen_abilities_subgroup = True
    if title.lower() == "facets":
        _State.seen_facets_subgroup = True   # the facet blocks after it don't repeat the heading (7.38 removed facets)
    if title.lower() == "talents":
        on_err = (
            "this.onerror=function(){this.style.display='none'};"
            f"this.src='{MISSING_ICON_URL}';"
        )
        icon = (f'<img src="{TALENT_ICON_URL}" alt="" '
                f'class="ability-icon-img" loading="lazy" width="128" height="128" onerror="{on_err}">')
        _State.ability_icons.add(TALENT_ICON_URL)
        _State.ability_block_open = True
        return out + (f'<h4 class="subgroup">{title}</h4>'
                      f'<div class="ability-block talents-block">'
                      f'<div class="ability-icon-wrap">{icon}</div>')
    label = f' <span class="subgroup-new-type">{new}</span>' if new else ''
    # a heading that names what its rows are about (7.38 "Lotus Pools", "Shrines of Wisdom") stays under a filter;
    # only the list labels (Abilities, Facets, General) go (owner 2026-11-07: "при включении фильтра new исчезли
    # названия")
    named = "" if title.lower() in GENERIC_SUBGROUPS else " subgroup-named"
    return out + f'<h4 class="subgroup{named}">{title}{label}</h4>'


def _hero_ability_slug(hero, title):
    """A hero's ability slug from its display name (tinker + "Defense Matrix" -> tinker_defense_matrix)."""
    part = ABILITY_DISPLAY_TO_SLUG.get((hero, title))
    if part is None:
        part = title.lower()
        for a, b in (("'", ""), ("-", "_"), (" ", "_"), (".", ""), ("(", ""), (")", "")):
            part = part.replace(a, b)
    return f"{HERO_TO_ABIL_PREFIX.get(hero, hero)}_{part}"


_FACET_ROW_ABILITY_RE = re.compile(r"([A-Z][\w'.\- ]{2,40}?):\s")


def _facet_row_ability_chip(text):
    """A facet's row that opens with an ability's name ("Defense Matrix: No longer blinks Tinker …", 7.39b
    Translocator): that ability's icon as a small square in place of the name, the name on hover only — like a facet
    talent's facet chip (owner 2026-10-27). The row's text with the chip, or the text as it was when the name is no
    ability of the hero's with an icon."""
    m = _FACET_ROW_ABILITY_RE.match(text) if _State.current_hero else None
    if not m:
        return text
    if m.group(1) == _State.current_facet_name:
        # the facet's own name: the header above already says it (owner 2026-10-27, 7.40 "Arsonist: No longer has
        # decreased number of +2 All Attributes bonuses" -> "No longer has …")
        rest = text[m.end():]
        return rest[:1].upper() + rest[1:]
    name = m.group(1)
    slug = _hero_ability_slug(_State.current_hero, name)
    if slug in _LOCAL_ABIL_ICONS:
        return ability_chip(name, f"{ABIL_CDN}{slug}.png") + text[m.end():]
    # an innate without art of its own: the generic innate icon, as its block's header (owner 2026-11-05, 7.38 Ironwood
    # Treant "Spirit of the Forest: Treant Multiplier …")
    if slug in _INNATE_SLUGS or (_State.current_hero, name) in INNATE_ABILITIES:
        return ability_chip(name, INNATE_ICON_URL) + text[m.end():]
    return text


def ability(title, slug=None, innate=None, icon_url=None, sub=False, old_title=None):
    """old_title: a rename shown in the header "Old → New", like ability_change's (owner 2026-10-21)."""
    icon_html = ''
    is_innate = False
    key = None
    if slug is None and _State.current_hero:
        key = (_State.current_hero, title)
        slug = _hero_ability_slug(_State.current_hero, title)
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
                      f'class="ability-icon-img" loading="lazy" width="128" height="128" '
                      f'title="missing icon: {title}">')
    elif slug and not icon_url and slug not in _LOCAL_ABIL_ICONS:
        _State.ability_icons.add(f"{ABIL_CDN}{slug}.png")
        from .ability_kv import facet_of_ability
        from .badges import FACETS
        facet = facet_of_ability(slug, _State.current_patch_version)
        if facet in FACETS:
            # a facet's ability without art of its own: the facet's icon, as the game shows it (owner 2026-10-27,
            # 7.38b Venomous Volley); no innate marker, no "missing"
            icon_inner, skip_marker = _facet_icon_html(facet), True
        elif is_innate:
            icon_inner = (f'<img src="{INNATE_ICON_URL}" alt="{title}" '
                          f'class="ability-icon-img" loading="lazy" width="128" height="128" '
                          f'data-slug="{slug}">')
            skip_marker = True
        else:
            icon_inner = (f'<img src="{MISSING_ICON_URL}" alt="{title}" '
                          f'class="ability-icon-img" loading="lazy" width="128" height="128" '
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
                      f'class="ability-icon-img" loading="lazy" width="128" height="128"{slug_attr} '
                      f'onerror="{on_err}">')
        if not icon_url:
            _State.ability_icons.add(src)
        if icon_url == INNATE_ICON_URL:
            skip_marker = True
    if is_innate and not skip_marker:
        icon_inner += (f'<img src="{INNATE_ICON_URL}" alt="" '
                       f'class="innate-marker">')
    icon_html = f'<div class="ability-icon-wrap">{icon_inner}</div>' if icon_inner else ''
    if not sub and _State.current_block_is_facet and not _State.facet_block_had_ul:
        import sys
        print(f'[WARN] ability("{title}") called directly inside a facet block — '
              f'this closes the facet before any content. '
              f'Put li() items inside the facet block instead, prefixed with the ability name.',
              file=sys.stderr)
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if not sub and not _State.seen_abilities_subgroup and (_State.current_hero or _State.current_unit):
        out += '<h4 class="subgroup">Abilities</h4>'
        _State.seen_abilities_subgroup = True
    _State.ability_block_open = True
    _State.current_block_is_facet = False
    _State.current_ability_slug = slug
    _State.aghs_part_slug = (slug, _State.current_hero)
    _State.current_ability_innate = bool(is_innate)
    from .ability_kv import slug_of
    _State.current_ability_kv = slug or slug_of(icon_url or "")
    return out + (f'<div class="ability-block{" is-innate" if is_innate else ""}">'
                  f'{icon_html}'
                  f'<h4 class="ability-title">{_renamed_title(old_title, title)}</h4>')


def _renamed_title(old, new):
    if not old or old == new:
        return new
    return (f'<span class="ability-title-rename"><span class="ability-title-old">{old}</span>'
            f'<span class="ability-title-arrow">→</span><span class="ability-title-new">{new}</span></span>')


def _facet_from_game(slug):
    """(name, colour, icon) of a facet the site's list lacks, from the game files of the patch before this one (a
    facet this patch removes) or of this patch — 7.38's removed facets (owner 2026-10-29: "где картинки фасетов?")."""
    from .ability_kv import hero_facets
    from .meta import _prev_patch_version
    hero, version = _State.current_hero, _State.current_patch_version
    for v in (_prev_patch_version(version) if version else None, version):
        found = hero_facets(hero, v).get(slug) if v and hero else None
        if found and found[0]:
            return found
    return None


def _facet_any(slug):
    """(name, gradient css, icon file stem or None) of a facet of the site's list or of the game's files; None if neither."""
    from .badges import FACETS, _FACET_COLOR_GRADIENT, facet_look
    if slug in FACETS:
        name, color, icon_name = facet_look(slug)
    elif (game := _facet_from_game(slug)):
        name, color, icon_name = game
    else:
        return None
    return name, _FACET_COLOR_GRADIENT.get(color, _FACET_COLOR_GRADIENT["Gray0"]), icon_name


def _open_facet_block(name, icon_html, block_class="ability-block facet-block"):
    """A facet's block with `icon_html` as its picture, after the hero's "Facets" title if this is his first."""
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if _State.current_hero and not _State.seen_facets_subgroup:
        out += '<h4 class="subgroup">Facets</h4>'
        _State.seen_facets_subgroup = True
    _State.ability_block_open = True
    _State.current_block_is_facet = True
    _State.current_facet_name = name
    return out + f'<div class="{block_class}">{icon_html}<h4 class="ability-title">{name}</h4>'


def facet_header(slug):
    found = _facet_any(slug)
    if not found:
        return f'<!-- facet_header: unknown slug {slug} -->'
    name, gradient, icon_name = found
    icon_overlay = (f'<img src="../icons/facets/{icon_name}.png" alt="" '
                    f'class="facet-icon-overlay" loading="lazy" width="72" height="72" '
                    f'data-slug="{slug}">') if icon_name else ''
    icon_html = (f'<div class="ability-icon-wrap facet-icon-wrap" '
                 f'style="background-image:{gradient}">{icon_overlay}</div>')
    return _open_facet_block(name, icon_html)


def _facet_parts(slug):
    """(name, gradient css, icon file stem or None) of a facet."""
    from .badges import FACETS, _FACET_COLOR_GRADIENT, facet_look
    if slug not in FACETS:
        raise KeyError(f"unknown facet {slug!r}: add it to patch/badges.FACETS")
    name, color, icon = facet_look(slug)
    return name, _FACET_COLOR_GRADIENT.get(color, _FACET_COLOR_GRADIENT["Gray0"]), icon


def _facet_icon_html(slug):
    """An ability header's icon drawn as its facet's (gradient + icon), for a facet's ability without art."""
    name, grad, icon = _facet_parts(slug)
    img = (f'<img src="../icons/facets/{icon}.png" alt="" loading="lazy" width="72" height="72">' if icon else '')
    return (f'<span class="facet-ability-icon" style="background-image:{grad}" role="img" '
            f'aria-label="{_html.escape(name)}">{img}</span>')


def _facet_chip(slug):
    """A facet as a small square, as its header's icon: the facet's gradient and icon, the name on hover only (owner
    2026-10-27: the named chip made a talent row too long)."""
    name, grad, icon = _facet_parts(slug)
    img = f'<img src="../icons/facets/{icon}.png" alt="" loading="lazy" width="16" height="16">' if icon else ''
    label = _html.escape(name)
    return (f'<span class="facet-chip" style="background-image:{grad}" data-tooltip="{label}" role="img" '
            f'aria-label="{label}">{img}</span>')




def ul_open():
    out = ''
    if _State.next_ul_is_hero_stats and (_State.current_hero or _State.current_unit):
        on_err = (
            "this.onerror=function(){this.style.display='none'};"
            f"this.src='{OTHER_ICON_URL}';"
        )
        icon = (f'<img src="{OTHER_ICON_URL}" alt="" '
                f'class="ability-icon-img" loading="lazy" width="128" height="128" onerror="{on_err}">')
        out += ('<h4 class="subgroup">GENERAL</h4>'
                '<div class="ability-block other-block">'
                f'<div class="ability-icon-wrap">{icon}</div>')
        _State.ability_block_open = True
        _State.next_ul_is_hero_stats = False
        _State.in_stats_ul = True
    if _State.current_block_is_facet:
        _State.facet_block_had_ul = True
    # marker read by patch/page.py _new_mech_rows (NEW rows lose the chip, keep data-tag)
    one = ':all' if _State.new_mech_one_box else ''
    return out + '<ul class="changes">' + (f'<!--NEWMECH:{_State.new_mech_tag}{one}-->' if _State.new_mech else '')


def ul_close():
    _State.in_stats_ul = False
    _State.card_meta = {}            # the rows under an ability_change card end here
    _State.card_innate = None
    cards, _State.aghs_cards = "".join(_State.aghs_cards), []
    return '</ul>' + cards + _aghs_parts_cards()


# "Level 25 Talent is +4s Burning Spears Duration instead of +6s" → "Level 25 Talent: +4s …", not "Talent: is +4s"
_TALENT_PREFIX_RE = re.compile(r'^(Level \d+ Talent) (?!:)(?:is )?')


def sub_ability(slug, name):
    """A small icon + name of another ability inside a card's text (7.41 Overclocking: the abilities it supercharges,
    owner 2026-10-21)."""
    # an ability without art (7.41 Silencer's old Brain Drain) gets the innate icon, as the headers do — at build
    # time, not by a request to a file that isn't there (2026-10-27: the site's page check listed 3 such)
    on_err = f"this.onerror=null;this.src='{INNATE_ICON_URL}';"
    _State.ability_icons.add(f"{ABIL_CDN}{slug}.png")          # scripts/fetch/fetch_icons.py downloads it
    src = f"{ABIL_CDN}{slug}.png" if slug in _LOCAL_ABIL_ICONS else INNATE_ICON_URL
    return (f'<span class="ac-sub"><img class="ac-sub-ico" src="{src}" alt="" loading="lazy" '
            f'onerror="{on_err}">'
            f'<b class="ac-sub-name">{name}</b></span>')


def _mark_talent_swap(text, badge, extra):
    """A talent swap row: the removed talent red, a brand-new one gold (the row stays SWAP), a talent that only
    changed level plain with a note (patch/talent_marks.py; owner 2026-10-21)."""
    from . import talent_marks
    if 'data-tag="swap"' not in (badge or "") or "<" in text:
        return text, badge, extra
    fate = talent_marks.mark(text, _State.current_hero_title)
    if not fate:
        return text, badge, extra
    old_fate, new_fate, note = fate
    m = talent_marks.SWAP_RE.match(text)
    old, new = m.group(2), m.group(3)
    if old_fate == "gone":
        old = hl(old, "del")
    if new_fate == "fresh":
        # gold only: the row stays SWAP — as NEW it scored as a buff and moved 7.38's net from +54 to +86 (2026-10-21)
        new = hl(new, "new")
    text = text[:m.start(2)] + old + text[m.end(2):m.start(3)] + new + text[m.end(3):]
    if note:
        extra = (extra or "") + inline_note(note)
    return text, badge, extra


def hl(text, kind):
    """A phrase coloured like the item cards' changes: kind = new / del / buff / nerf / rework."""
    return f'<span class="iab-hl iab-hl-{kind}">{text}</span>'


# a highlight holding only a number ("45/40/35/30s", "+150", "25%"): a number change — the text's colour and a dotted
# underline like the item cards' values, not a highlighter strip (owner 2026-10-25: "числовые изменения цветом текста
# и пунктиром, а текстовые цветовыми полосками"; cards, talents, headers). Marked at save time, so every generator
# regex that reads "<span class="iab-hl iab-hl-X">" keeps working.
_HL_NUM_BODY = r"(?:<b class=\"iab-num\">)?[+\-−]?\d[\d.,]*(?:\s*/\s*[+\-−]?\d[\d.,]*)*\s*(?:%|s|x)?(?:</b>)?"
_HL_NUM_RE = re.compile(rf'<span class="iab-hl (iab-hl-\w+)"((?: data-tag="\w+")?)>({_HL_NUM_BODY})</span>')


def mark_number_highlights(html_text: str) -> str:
    return _HL_NUM_RE.sub(r'<span class="iab-hl \1 iab-hl-num"\2>\3</span>', html_text)


def _li_text(text, badge, extra, examples):
    """li() step 1, the row's own words: its terrain pictures, the talent prefix, its examples, a talent swap's colours.
    (text, badge, extra, the plain words the weights read or None, the terrain phrase)."""
    _tphrase = ""
    _plain_text = None
    if isinstance(text, str):
        # a terrain note's micro-screenshots ride along under its text, opened by the words naming its object
        _tphrase, _tshots = terrain_note(_State.current_patch_version, text)
        extra = (extra or "") + _tshots
        text = _TALENT_PREFIX_RE.sub(r'\1: ', text)
        _plain_text = text                     # the weights read the words, not the highlight spans
        text, _aside = row_examples(text, examples)
        if _aside:                             # the examples' aside in brackets: under the row's "?" (2026-11-07)
            extra = inline_note(_aside) + (extra or "")
        text, badge, extra = _mark_talent_swap(text, badge, extra)
        if _State.in_stats_ul:
            _m = _FACET_INNATE_PREFIX_RE.match(text)
            if _m and _m.group(1) in _FACET_INNATE_NAMES:
                print(f"  [warn] '{_m.group(1)}' is a known facet/innate but sits in "
                      f"STATS ({_State.current_hero}) — use facet_header()/ability() instead")
    return text, badge, extra, _plain_text, _tphrase


def _li_dyn_tags(badge, force_tag):
    """li() step 2: the tags the row is tallied under."""
    if force_tag is not None:
        return set(force_tag.split())
    primary = re.findall(r'data-tag="(\w+)"', badge)
    if primary:
        return set(primary)
    return set(re.findall(r'data-overall="(\w+)"', badge))


def _li_covered(text, _plain_text, dyn_tags, covered):
    """li() step 3: whether a card above already shows the row (it is hidden then), and a removed Aghanim's row's
    text. (text, covered)."""
    if isinstance(text, str) and _State.card_innate and re.fullmatch(
            rf"\s*{re.escape(_State.card_innate)} is now an innate ability(?: \(previously a basic ability\))?\.?\s*",
            _plain_text):
        # the card above shows it as the innate already (owner 2026-10-25, 7.41 Poison Sting); "(previously granted by
        # Aghanim's Scepter)" says what the card doesn't and stays
        covered = True
    elif isinstance(text, str) and not covered and _granted_now_covered(_plain_text):
        covered = True                          # "Now granted by Aghanim's X": the upgrade's card under it says so
    elif isinstance(text, str) and _aghs_rework_card(_plain_text, covered):
        covered = True                          # the old -> new upgrade card under the rows shows it
    elif isinstance(text, str) and not covered and "rework" in dyn_tags and _upgrade_wording_covered(_plain_text):
        covered = True                          # "Aghanim's Scepter's X changed from … to …": the card's two texts say it
    elif isinstance(text, str) and not covered and _scale_card(_plain_text):
        covered = True                          # ... the old -> new header strips show what it scales with
    elif isinstance(text, str) and not covered and not re.match(r"\s*Aghanim's", _plain_text):
        _granted_card(dyn_tags)                 # an upgrade-granted ability's new text: a card, the row stays
    if isinstance(text, str) and not covered and _aghs_removed_row(_plain_text):
        text = _aghs_removed_row(_plain_text)   # the weights still read the patch note's words (_plain_text)
    return text, covered


def _li_record(text, _plain_text, _score_text, extra, badge, dyn_tags, also_dyn):
    """li() step 4: the row's scores and tag tallies in the patch dynamics; a removed item / enchantment notes the
    patch it left in."""
    _ctx = _row_ctx(_plain_text if isinstance(text, str) else "")
    _scores = _row_scores(_score_text, dyn_tags, badge, ctx=_ctx)
    _dyn_record_li(dyn_tags, extra_keys=also_dyn, scores=_scores)
    _note_cell_row(_score_text, dyn_tags, _scores, _ctx)
    _note_damage_row(_score_text, _scores)
    _score_folded_damage(extra)
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


def _li_tag_str(badge, force_tag):
    """li() step 5: the row's data-tag, what the filters read."""
    tags = set()
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
    return tag_str


def _li_left_tag(text, badge, force_tag, covered):
    """li() step 6: the chip in the row's tag column and the rest of its badge. (left_tag, rest)."""
    text_tag_re = re.search(
        r'<span class="badge (buff-text|nerf-text|rework|swap|misc|qol|new|del)"[^>]*>\w+</span>\s*',
        badge
    )
    if text_tag_re:
        left_tag = text_tag_re.group(0).rstrip()
        rest = badge[:text_tag_re.start()] + badge[text_tag_re.end():]
    elif force_tag in ("buff", "nerf"):
        # the chip says what the row is filtered as: 7.41c Bloodstone's wrongly stated "+600 -> +625" (+4%) is
        # really 650 -> 625, force_tag="nerf" — its chip said BUFF while the NERF filter showed it
        left_tag = (f'<span class="badge {force_tag}-text" data-tag="{force_tag}" data-overall="{force_tag}">'
                    f'{force_tag.upper()}</span>')
        rest = badge
    elif 'data-overall="buff"' in badge:
        left_tag = '<span class="badge buff-text" data-tag="buff" data-overall="buff">BUFF</span>'
        rest = badge
    elif 'data-overall="nerf"' in badge:
        left_tag = '<span class="badge nerf-text" data-tag="nerf" data-overall="nerf">NERF</span>'
        rest = badge
    else:
        left_tag = '<span class="row-tag-empty"></span>'
        rest = badge
    if _State.terrain_rows is not None and isinstance(text, str):
        # a terrain row's chip is its number in its category (the owner 2026-10-03: "just number the rows instead of
        # tag chips"); data-tag keeps the tag for the filters / weights
        _State.terrain_rows += 0 if covered else 1     # a hidden row takes no number: the first one seen is 1
        left_tag = terrain_num_chip(_State.terrain_rows, badge if force_tag is None else "")
    return left_tag, rest


def _li_classes(text, extra, badge, dyn_tags, covered, major, ability_row):
    """li() step 7: the row's classes — terrain, major, Aghanim's, an ability row (an item's / unit's drawn as its
    card), and the rows a card above covers (hidden). (classes, Aghanim's marker, text)."""
    classes = ["terrain-row"] if _State.terrain_rows is not None and isinstance(text, str) else []
    if major:                 # the change that sums up a patch (7.41 "Facets removed from the game"): a stand-out row
        classes.append("li-major")
    marker = ""
    text_noclass = (re.sub(r'<!--TIP-->.*?<!--/TIP-->', '', text, flags=re.S)
                    if isinstance(text, str) else text)
    if isinstance(text, str) and "Aghanim's Scepter" in text_noclass:
        classes.append("aghanim-scepter")
        marker = '<span class="aghanim-marker scepter"></span>'
    elif isinstance(text, str) and "Aghanim's Shard" in text_noclass:
        classes.append("aghanim-shard")
        marker = '<span class="aghanim-marker shard"></span>'
    elif isinstance(text, str) and _State.current_ability_slug:
        # a row of an ability that Aghanim's Shard / Scepter GRANTS is an Aghanim row even without the
        # words (Medusa 7.38 Cold Blooded; owner 2026-09-26) — KV IsGrantedByShard / IsGrantedByScepter
        from .aghs_granted import kind_of
        _aghs = kind_of(_State.current_ability_slug, _State.current_patch_version or "*")
        if _aghs:
            classes.append(f"aghanim-{_aghs}")
            marker = f'<span class="aghanim-marker {_aghs}"></span>'
    if isinstance(text, str) and re.match(r'^\s*(Passive|Active|Toggle|Aura|Ability)\s*:', text):
        classes.append("ability-row")
        # a unit's ability too (owner 2026-09-30: 7.38 Boglet "Active: ... Range: 275. Mana Cost: 40. Cooldown: 16s")
        _ek = _State.current_entity_key or ""
        _props = None
        if _ek.startswith("unit|") and _State.current_ability_kv:   # its values from the game files (radius 1200)
            from .ability_kv import ability_props
            _props = ability_props(_State.current_ability_kv, _State.current_patch_version)
        _card = (_item_ability_html(text, _props) if _ek.startswith(("item|", "unit|"))
                 and dyn_tags <= {"new", "rework"} else None)
        if _card and _iab_shown_in_card(text, extra):
            # its full text is the card's right pane already: kept hidden (scored above, tag counted by filters)
            classes.remove("ability-row")
            classes += ["iab-covered", "covered-iab"]
        elif _card:
            classes.append("item-ability")
            text = _card
        else:
            text = re.sub(r'^(\s*)(Passive|Active|Toggle|Aura|Ability)(\s*:)',
                          r'\1<b>\2\3</b>', text)
    elif ability_row:
        classes.append("ability-row")
    # a number change the abilities card above already shows: hidden, its number coloured in the card
    # a QoL row tells what no tooltip does (7.38 Bloodthorn: "silence visual … tinted red"): never the card's
    if (isinstance(text, str) and "iab-covered" not in classes and "item-ability" not in classes
            and (_State.current_entity_key or "").startswith("item|") and "qol" not in dyn_tags
            and (_iab_covered_change(text, dyn_tags, extra, badge)
                 # the card shows it as text: an ability only one side has, or words a row without numbers
                 # describes (a row with a note keeps showing it)
                 or _iab_unpaired_row(text, dyn_tags, extra)
                 or (not extra and _iab_text_change(text, dyn_tags)))):
        classes += ["iab-covered", "covered-iab"]       # covered-*: the card that shows it (tag filters)
    _meta_hit = isinstance(text, str) and _card_meta_covered(text)      # also confirms an explicit covered=True row
    if (covered or _meta_hit) and "iab-covered" not in classes:
        classes += ["iab-covered", "covered-card"]
    # a number row of an enchantment its tier table above shows (owner 2026-10-17, 7.41 variant A)
    if (isinstance(text, str) and "iab-covered" not in classes
            and (_State.current_entity_key or "").startswith("enchant|") and _ench_covered(text)):
        classes += ["iab-covered", "covered-ench"]
    # an attribute / damage row the hero's attributes card shows: hidden, its tag on the card
    if (isinstance(text, str) and "iab-covered" not in classes
            and (_State.current_entity_key or "").startswith("hero|") and _hs_covered(text, dyn_tags)):
        classes += ["iab-covered", "covered-hs"]
    # a cost row the components card above already shows: hidden, the card gets its % and colours
    if (isinstance(text, str) and "iab-covered" not in classes
            and (_State.current_entity_key or "").startswith("item|") and _cost_covered(text, extra)):
        classes += ["iab-covered", "covered-cost"]
    return classes, marker, text


def _li_tips(text, extra):
    """li() step 8: the (?) tips at the row's end, lifted out of its text and its extra, and a mechanic's tables of
    abilities. (text without them, the tips, the tables, extra)."""
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
    _abil_rows = ""
    if isinstance(extra, str) and '<!--MECHTABLE-->' in extra:      # mech_table: under the row's text
        _abil_rows = "".join(re.findall(r'<!--MECHTABLE-->(.*?)<!--/MECHTABLE-->', extra, re.S))
        extra = re.sub(r'<!--MECHTABLE-->.*?<!--/MECHTABLE-->', '', extra, flags=re.S)
    # only in General Updates, where the mechanics are: other parts of the site keep their "?" (owner 2026-10-28)
    if _State.new_mech and _State.current_section_slug == "general" and isinstance(text_base, str):
        # a reworked mechanic's list of abilities: rows of icons under the text, not a "?" (owner 2026-10-28)
        trailing_tips, _lifted_rows, _list_notes = lift_ability_lists([x.strip() for x in trailing_tips],
                                                                    open_text=_State.new_mech_tag == "rework",
                                                                    row_text=text_base)
        _abil_rows += _lifted_rows
        if 'mech-captioned' in _lifted_rows:    # the row's text leads its table (owner 2026-10-30, 7.37)
            text_base = ""
        for _n in _list_notes:              # "All three of these …": in one line with the row's text (owner 2026-10-28)
            _end = "" if text_base.rstrip().endswith((".", ":", "!", "?")) else "."
            text_base = f'{text_base.rstrip()}{_end} <span class="mech-row-note">{_n}</span>'
    trailing_tips = merge_tips(trailing_tips)
    return text_base, trailing_tips, _abil_rows, extra


def _li_inner(text_base, trailing_tips, _abil_rows, classes, marker, _tphrase, facet):
    """li() step 9: the row's text as drawn — the tips and the Aghanim's marker with its last word, the terrain
    button, a facet's / ability's / rune's chip, the tables under it."""
    if not isinstance(text_base, str):
        text_inner = text_base
    elif trailing_tips and "item-ability" in classes:          # the (?) stays with the description's last word
        text_inner = iab_attach_tail(text_base, marker + ''.join(trailing_tips))
    elif trailing_tips:
        cluster = marker + ''.join(trailing_tips)
        _mw = re.search(r'(\S+)\s*$', text_base)
        if _mw and '<' not in _mw.group(1) and '>' not in _mw.group(1):
            text_inner = (text_base[:_mw.start(1)]
                          + f'<span class="li-tail">{_mw.group(1)}{cluster}</span>')
        else:
            text_inner = f'{text_base} <span class="li-tail">{cluster}</span>'
    elif marker:
        _mw = re.search(r'(\S+)\s*$', text_base)
        if _mw and '<' not in _mw.group(1) and '>' not in _mw.group(1):
            text_inner = (text_base[:_mw.start(1)]
                          + f'<span class="li-tail">{_mw.group(1)}{marker}</span>')
        else:
            text_inner = f'{text_base}{marker}'
    else:
        text_inner = text_base
    if _tphrase and isinstance(text_inner, str):
        text_inner = terrain_button(text_inner, _tphrase)
    if facet and isinstance(text_inner, str):
        # a facet's talent among the hero's Talents: the facet's chip says whose (owner 2026-10-27, 7.39 Nature's
        # Profit); only on screen — the weights and the talent context read the row's own words
        text_inner = f'{_facet_chip(facet)} {text_inner}'
    elif _State.current_block_is_facet and isinstance(text_inner, str):
        text_inner = _facet_row_ability_chip(text_inner)
    elif isinstance(text_inner, str):
        text_inner = rune_row_chip(text_inner)      # "Haste Rune: …" -> the rune's icon (owner 2026-10-28)
    if _abil_rows:
        text_inner += _abil_rows
    return text_inner


def li(text, badge="", extra="", force_tag=None, ability_row=False, also_dyn=None, major=False, covered=False,
       facet=None, examples=None):
    """covered=True: the card above already shows this change (highlighted) — the row is hidden but keeps its weight
    and tag for the filters, like the item cards' covered rows (owner 2026-10-21, 7.41 Overclocking).
    facet="<facet slug>": a facet's talent, written under the hero's Talents with the facet's chip before it.
    The steps, in this order: _li_text, _li_dyn_tags, _li_covered, _li_record, _li_tag_str, _li_left_tag,
    _li_classes, _li_tips, _li_inner."""
    text, badge, extra, _plain_text, _tphrase = _li_text(text, badge, extra, examples)
    dyn_tags = _li_dyn_tags(badge, force_tag)
    _score_text = _plain_text if isinstance(text, str) else ""
    if isinstance(extra, str) and _TOTAL_UNCHANGED_RE.search(extra):
        # "Recipe cost 1350 -> 1250" + note "Total cost unchanged": the buyer pays the same
        _score_text += ". " + re.sub(r'<[^>]+>', ' ', extra)
    _cost_panel_covered(_score_text)
    text, covered = _li_covered(text, _plain_text, dyn_tags, covered)
    _li_record(text, _plain_text, _score_text, extra, badge, dyn_tags, also_dyn)
    tag_str = _li_tag_str(badge, force_tag)
    left_tag, rest = _li_left_tag(text, badge, force_tag, covered)
    classes, marker, text = _li_classes(text, extra, badge, dyn_tags, covered, major, ability_row)
    cls_attr = f' class="{" ".join(classes)}"' if classes else ""
    attr = f' data-tag="{tag_str}"' if tag_str else ""
    if also_dyn:
        # the row also belongs to these entities ("unit|melee-creep"): their squares count it (above) and their
        # own pages show it under this patch (builders/entity_changes._collect) — owner 2026-10-06: the 7.41 lane
        # creep rows sat in General Updates and the creep cards stayed unclickable
        attr += f' data-also="{" ".join(also_dyn if isinstance(also_dyn, list) else [also_dyn])}"'
    text_base, trailing_tips, _abil_rows, extra = _li_tips(text, extra)
    text_inner = _li_inner(text_base, trailing_tips, _abil_rows, classes, marker, _tphrase, facet)
    # An ability row with its own chip keeps the chip as the li's first child: page.py
    # marks its whole box `ability-box-tagged`, and the CSS moves the box right by the tag
    # column so the chip sits in the SAME column, size and height as every other row's
    # chip (it used to be folded into the text: 13px right, 8px low, narrower).
    return f'<li{attr}{cls_attr}>{left_tag}<span class="row-text">{text_inner}</span>{rest}{extra}</li>'


_ATTR_CHIP_CLS = {"Strength": "is-str", "Agility": "is-agi", "Intelligence": "is-int", "Universal": "is-uni"}


def attr_change(old, new):
    """Row text for a main-attribute change: "Main attribute changed from Agility → Universal",
    both names bold in the row's own font, coloured with the site attribute palette (--attr-*, no icons).
    The arrow is the HTML entity &rarr; (never a literal "→" in content: it gets mangled by
    non-UTF-8 shells/consoles)."""
    def chip(a):
        if a not in _ATTR_CHIP_CLS:
            raise ValueError(f"attr_change: unknown attribute {a!r}")
        return f'<b class="attr-chip {_ATTR_CHIP_CLS[a]}">{a}</b>'
    return f'Main attribute changed from {chip(old)} &rarr; {chip(new)}'


def creep_ref(name, icon_url, count=None):
    """A unit named inside a row: small portrait + bold name, e.g. camp compositions
    ("Medium camp: 2× [icon] Boglet, 1× [icon] Marshmage Apprentice"). The icon is capped to
    the text height so the row keeps its line height."""
    n = f"{count}× " if count else ""
    return (f'<span class="creep-ref">{n}<img src="{icon_url}" alt="" width="28" height="16">'
            f'<b>{name}</b></span>')


def camp_table(rows):
    """Camp compositions as a light table so the creep names line up in columns, each camp's average bounty in its own
    columns after the name (owner 2026-11-04, it was Valve's "?" on the camp):
    camp_table([("Small camp", [(3, "Pollywog", icon)], 54, 90),
                ("Medium camp", [(2, "Boglet", icon), (1, "Marshmage Apprentice", icon)], 81, 126)])
    A number that changed is (new, old, the % badge): coloured and dotted, the old one on hover (7.38 Ancient Prowlers)."""
    from .unit_numbers import changed_value

    def num(value):
        return changed_value("camp-v", value[0], value[1], value[2]) if isinstance(value, tuple) else value
    width = max(len(row[1]) for row in rows)
    cells = ['<span class="camp-name camp-head">Camp</span>',
             '<span class="camp-cell camp-num camp-head">Average Gold</span>',
             '<span class="camp-cell camp-num camp-head">Average XP</span>',
             f'<span class="camp-cell camp-head" style="grid-column: span {width}">Creeps</span>']
    for camp, creeps, gold, xp in rows:
        cells.append(f'<span class="camp-name">{camp}</span>')
        cells.append(f'<span class="camp-cell camp-num camp-gold">{num(gold)}</span>')
        cells.append(f'<span class="camp-cell camp-num camp-xp">{num(xp)}</span>')
        for i in range(width):
            if i < len(creeps):
                n, name, icon = creeps[i]
                cells.append(f'<span class="camp-cell">{creep_ref(name, icon, n)}</span>')
            else:
                cells.append('<span class="camp-cell"></span>')
    return (f'<span class="camp-table" style="--camp-cols:{width + 2}">' + "".join(cells) + '</span>')


def inline_note(text):
    return f'<!--INLINETIP-->{info_tip(text)}<!--/INLINETIP-->'


def inline_list(text):
    """inline_note of a list the row introduces (Valve's "…:" / "The following …"): in a Reworked mechanic it is a
    table open under the row, not a "?" (owner 2026-10-28, 7.38 Lifesteal)."""
    tip = info_tip(text)
    LIST_TIPS.add(tip)
    return f'<!--INLINETIP-->{tip}<!--/INLINETIP-->'


_POP_SUB = '&nbsp;&nbsp;– '


def _pop_list(body):
    """A popup of several lines is an enumeration: one bullet per line (an "&nbsp;&nbsp;– x"
    line is a sub-item of the line above). A single line stays plain text."""
    items = [x for x in body.split('<br>') if x.strip()]
    if len(items) < 2:
        return body
    return ''.join(
        f'<span class="pop-li pop-sub">{x[len(_POP_SUB):]}</span>' if x.startswith(_POP_SUB)
        else f'<span class="pop-li">{x}</span>' for x in items)


def info_tip(*lines, header=None):
    body = _pop_list('<br>'.join(lines))
    head = f'<span class="info-pop-h">{header}</span>' if header else ''
    out = ('<!--TIP--><span class="info-tip" tabindex="0">?'
           f'<span class="info-pop">{head}{body}</span></span><!--/TIP-->')
    TIP_RAW[out] = '<br>'.join(lines)     # a mechanic's list of abilities is read back as icon rows (li)
    return out


_TIP_RE = re.compile(r'<!--TIP--><span class="info-tip" tabindex="0">\?<span class="info-pop">(.*)</span></span>'
                     r'<!--/TIP-->', re.S)


def merge_tips(tips):
    """Several (?) at the end of one row → one (?) (owner 2026-10-09: "два «?» подряд — соединять"): each popup
    becomes a part of one popup, the parts split by a thin line (.pop-part). Tips of another shape stay as they are."""
    bodies = [_TIP_RE.fullmatch(t) for t in tips]
    if len(tips) < 2 or not all(bodies):
        return tips
    parts = ''.join(f'<span class="pop-part">{m.group(1)}</span>' for m in bodies)
    return [f'<!--TIP--><span class="info-tip" tabindex="0">?<span class="info-pop">{parts}</span></span><!--/TIP-->']


def show_list(*items, summary='Show list'):
    items_html = ''.join(f'<span class="show-list-item">{it}</span>' for it in items)
    return (f'<details class="show-list-inline">'
            f'<summary><span class="show-list-chevron">▸</span>'
            f'{summary} <span class="subnote-count">({len(items)})</span></summary>'
            f'<div class="show-list-body">{items_html}</div></details>')


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


def provides(*items):
    if len(items) == 1 and isinstance(items[0], str) and ',' in items[0]:
        items = [s.strip() for s in items[0].split(',') if s.strip()]
    rows = ''.join(f'<div class="provides-row">{it}</div>' for it in items)
    return f'<div class="provides-box">{rows}</div>'


def auto_components_change(item_display, this_version):
    from .stats import _STATS_I
    from .meta import _prev_patch_version

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
    # No look-ahead to a later snapshot any more: it covered stale items.json copies (7.41 = 7.40c,
    # 7.37e without Khanda's 7.37e recipe), which tools/resync_snapshots.py fixed at the root
    # (2026-09-27) — and a look-ahead would put a later patch's price into this one.
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

# the cards split out of this file (audit 2026-10-26 #8) import their helpers from here, so they come last
from .cards_hero_stats import _hs_covered  # noqa: E402
from .cards_item_abilities import (  # noqa: E402
    _iab_covered_change,
    _iab_shown_in_card,
    _iab_text_change,
    _iab_unpaired_row,
    _item_ability_html,
    iab_attach_tail,
)
from .cards_item_stats import _cost_covered, components_change  # noqa: E402
from .cards_aghs import (  # noqa: E402
    _aghs_parts_cards,
    _aghs_removed_row,
    _aghs_rework_card,
    _card_meta_covered,
    _granted_card,
    _granted_now_covered,
    _scale_card,
    _upgrade_wording_covered,
)
from .enchants import _ench_covered  # noqa: E402
