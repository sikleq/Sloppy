"""Image URL helpers, HERO_SLUG, ITEM_SLUG, and icon loading."""

import os as _os

# Local mirrors. Patch HTMLs sit in /patches/ so they reference ../icons/...
# Originals are kept under git history for reference; mirror script: _mirror_icons.py.
HERO_CDN = "../icons/heroes/"
ITEM_CDN = "../icons/items/"
ABIL_CDN = "../icons/abilities/"

# Local ability-icon filenames (slug, no extension), loaded once. Used to
# decide at build time whether an ability icon actually exists on disk — if not,
# we render the fallback (innate marker / missing placeholder) DIRECTLY as the
# <img src> instead of a broken path that only swaps via onerror. The broken
# path leaked into the search index (which reads img.src at load time, before
# the lazy onerror fired), so abilities like Timbersaw's innate "Exposure
# Therapy" showed missing.svg in the search dropdown. ~28 innate abilities have
# no public CDN icon and are affected identically.
_ABIL_ICON_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "icons", "abilities")
try:
    _LOCAL_ABIL_ICONS = {
        _os.path.splitext(f)[0] for f in _os.listdir(_ABIL_ICON_DIR)
        if f.lower().endswith(".png")
    }
except OSError:
    _LOCAL_ABIL_ICONS = set()

HERO_SLUG = {
    "Abaddon": "abaddon", "Underlord": "abyssal_underlord", "Alchemist": "alchemist",
    "Ancient Apparition": "ancient_apparition", "Anti-Mage": "antimage",
    "Arc Warden": "arc_warden", "Axe": "axe", "Bane": "bane",
    "Batrider": "batrider", "Beastmaster": "beastmaster",
    "Bloodseeker": "bloodseeker", "Bounty Hunter": "bounty_hunter",
    "Brewmaster": "brewmaster", "Bristleback": "bristleback",
    "Broodmother": "broodmother", "Centaur Warrunner": "centaur",
    "Chaos Knight": "chaos_knight", "Chen": "chen", "Clinkz": "clinkz",
    "Clockwerk": "rattletrap", "Crystal Maiden": "crystal_maiden",
    "Dark Seer": "dark_seer", "Dark Willow": "dark_willow",
    "Dawnbreaker": "dawnbreaker", "Dazzle": "dazzle",
    "Death Prophet": "death_prophet", "Disruptor": "disruptor",
    "Doom": "doom_bringer", "Dragon Knight": "dragon_knight",
    "Drow Ranger": "drow_ranger", "Earth Spirit": "earth_spirit",
    "Earthshaker": "earthshaker", "Elder Titan": "elder_titan",
    "Ember Spirit": "ember_spirit", "Enchantress": "enchantress",
    "Enigma": "enigma", "Faceless Void": "faceless_void",
    "Grimstroke": "grimstroke", "Gyrocopter": "gyrocopter",
    "Hoodwink": "hoodwink", "Huskar": "huskar", "Invoker": "invoker",
    "Io": "wisp", "Jakiro": "jakiro", "Juggernaut": "juggernaut",
    "Keeper of the Light": "keeper_of_the_light", "Kez": "kez",
    "Kunkka": "kunkka", "Largo": "largo",
    "Legion Commander": "legion_commander", "Leshrac": "leshrac",
    "Lich": "lich", "Lifestealer": "life_stealer", "Lina": "lina",
    "Lion": "lion", "Lone Druid": "lone_druid", "Luna": "luna",
    "Lycan": "lycan", "Magnus": "magnataur", "Marci": "marci",
    "Mars": "mars", "Medusa": "medusa", "Meepo": "meepo",
    "Mirana": "mirana", "Monkey King": "monkey_king",
    "Morphling": "morphling", "Muerta": "muerta", "Naga Siren": "naga_siren",
    "Nature's Prophet": "furion", "Necrophos": "necrolyte",
    "Night Stalker": "night_stalker", "Nyx Assassin": "nyx_assassin",
    "Ogre Magi": "ogre_magi", "Omniknight": "omniknight",
    "Oracle": "oracle", "Outworld Destroyer": "obsidian_destroyer",
    "Pangolier": "pangolier", "Phantom Assassin": "phantom_assassin",
    "Phantom Lancer": "phantom_lancer", "Phoenix": "phoenix",
    "Primal Beast": "primal_beast", "Puck": "puck", "Pudge": "pudge",
    "Pugna": "pugna", "Queen of Pain": "queenofpain", "Razor": "razor",
    "Riki": "riki", "Ringmaster": "ringmaster", "Rubick": "rubick",
    "Sand King": "sand_king", "Shadow Demon": "shadow_demon",
    "Shadow Fiend": "nevermore", "Shadow Shaman": "shadow_shaman",
    "Silencer": "silencer", "Skywrath Mage": "skywrath_mage",
    "Slardar": "slardar", "Slark": "slark", "Snapfire": "snapfire",
    "Sniper": "sniper", "Spectre": "spectre", "Spirit Breaker": "spirit_breaker",
    "Storm Spirit": "storm_spirit", "Sven": "sven", "Techies": "techies",
    "Templar Assassin": "templar_assassin", "Terrorblade": "terrorblade",
    "Tidehunter": "tidehunter", "Timbersaw": "shredder", "Tinker": "tinker",
    "Tiny": "tiny", "Treant Protector": "treant",
    "Troll Warlord": "troll_warlord", "Tusk": "tusk", "Underlord": "abyssal_underlord",
    "Undying": "undying", "Ursa": "ursa", "Vengeful Spirit": "vengefulspirit",
    "Venomancer": "venomancer", "Viper": "viper", "Visage": "visage",
    "Void Spirit": "void_spirit", "Warlock": "warlock", "Weaver": "weaver",
    "Windranger": "windrunner", "Winter Wyvern": "winter_wyvern",
    "Witch Doctor": "witch_doctor", "Wraith King": "skeleton_king",
    "Zeus": "zuus",
}

ITEM_SLUG = {
    # CDN file is still under the engine name `angels_demise`; in-game display
    # name was renamed to "Khanda". Use display "Khanda" in item_header() but
    # icon resolves to icons/items/angels_demise.png via this slug map.
    # Add an entry here for every item whose in-game name was renamed AND
    # whose engine slug doesn't fall out of the naive derivation
    # (lowercase + spaces->underscores + strip apostrophes). Verify against
    # the live Valve datafeed: dota2.com/datafeed/itemlist
    "Khanda": "angels_demise",
    "Book of the Dead": "demonicon",
    "Witchbane": "heavy_blade",
    "Gunpowder Gauntlet": "gunpowder_gauntlets",
    "Refresher Orb": "refresher",
    "Eye of Skadi": "skadi",
    # 7.40-era / engine-slug-vs-display-name overrides
    "Brigand's Blade": "misericorde",
    "Ghost Scepter": "ghost",
    "Giant's Maul": "giant_maul",
    "Healing Salve": "flask",
    "Iron Branch": "branches",
    "Shadow Blade": "invis_sword",
    "Scythe of Vyse": "sheepstick",
    "Observer Ward": "ward_observer",
    "Sentry Ward": "ward_sentry",
    "Revenant's Brooch": "revenants_brooch",
    "Ripper's Lash": "rippers_lash",
    "Sister's Shroud": "sisters_shroud",
    "Battle Fury": "bfury",
    "Blink Dagger": "blink",
    "Bloodstone": "bloodstone",
    "Boots of Bearing": "boots_of_bearing",
    "Crella's Crozier": "crellas_crozier",
    "Disperser": "disperser",
    "Essence Distiller": "essence_distiller",
    "Harpoon": "harpoon",
    "Heart of Tarrasque": "heart",
    "Mage Slayer": "mage_slayer",
    "Shiva's Guard": "shivas_guard",
    "Silver Edge": "silver_edge",
    "Soul Ring": "soul_ring",
    "Specialist's Array": "specialists_array",
    "Manta Style": "manta",
    "Drum of Endurance": "ancient_janggo",
    "Gleipnir": "gungir",
    "Orchid Malevolence": "orchid",
    "Pipe of Insight": "pipe",
    "Perseverance": "pers",
    "Phylactery": "phylactery",
    "Heaven's Halberd": "heavens_halberd",
    "Glimmer Cape": "glimmer_cape",
    "Spirit Vessel": "spirit_vessel",
    "Witch Blade": "witch_blade",
    "Vladmir's Offering": "vladmir",
    "Aether Lens": "aether_lens",
    "Octarine Core": "octarine_core",
    "Helm of the Overlord": "helm_of_the_overlord",
    "Rod of Atos": "rod_of_atos",
    "Sange and Yasha": "sange_and_yasha",
    "Sange": "sange",
    "Meteor Hammer": "meteor_hammer",
    "Abyssal Blade": "abyssal_blade",
    "Aeon Disk": "aeon_disk",
    "Arcane Boots": "arcane_boots",
    "Ash Legion Shield": "ash_legion_shield",
    "Black King Bar": "black_king_bar",
    "Blade Mail": "blade_mail",
    "Bloodthorn": "bloodthorn",
    "Chainmail": "chainmail",
    "Chasm Stone": "chasm_stone",
    "Chipped Vest": "chipped_vest",
    "Cloak": "cloak",
    "Cloak of Flames": "cloak_of_flames",
    "Conjurer's Catalyst": "conjurers_catalyst",
    "Consecrated Wraps": "consecrated_wraps",
    "Cornucopia": "cornucopia",
    "Crimson Guard": "crimson_guard",
    "Crippling Crossbow": "crippling_crossbow",
    "Dagger of Ristul": "dagger_of_ristul",
    "Dagon": "dagon",
    "Dandelion Amulet": "dandelion_amulet",
    "Demonicon": "demonicon",
    "Dragon Lance": "dragon_lance",
    "Enchanted Mango": "enchanted_mango",
    "Enchanter's Bauble": "enchanters_bauble",
    "Eternal Shroud": "eternal_shroud",
    "Ethereal Blade": "ethereal_blade",
    "Faerie Fire": "faerie_fire",
    "Foragers Kit": "foragers_kit",
    "Force Staff": "force_staff",
    "Guardian Greaves": "guardian_greaves",
    "Gunpowder Gauntlets": "gunpowder_gauntlets",
    "Hand of Midas": "hand_of_midas",
    "Harmonizer": "harmonizer",
    "Heavy Blade": "heavy_blade",
    "Holy Locket": "holy_locket",
    "Hurricane Pike": "hurricane_pike",
    "Hydras Breath": "hydras_breath",
    "Idol of Scree'auk": "idol_of_screeauk",
    "Jidi Pollen Bag": "jidi_pollen_bag",
    "Kaya": "kaya",
    "Kaya and Sange": "kaya_and_sange",
    "Lotus Orb": "lotus_orb",
    "Mask of Madness": "mask_of_madness",
    "Medallion of Courage": "medallion_of_courage",
    "Mekansm": "mekansm",
    "Metamorphic Mandible": "metamorphic_mandible",
    "Minotaur Horn": "minotaur_horn",
    "Monkey King Bar": "monkey_king_bar",
    "Nullifier": "nullifier",
    "Oblivion Staff": "oblivion_staff",
    "Orb of Corrosion": "orb_of_corrosion",
    "Orb of Frost": "orb_of_frost",
    "Partisans Brand": "partisans_brand",
    "Pavise": "pavise",
    "Phase Boots": "phase_boots",
    "Possessed Mask": "possessed_mask",
    "Prophets Pendulum": "prophets_pendulum",
    "Radiance": "radiance",
    "Rattlecage": "rattlecage",
    "Refresher Orb": "refresher",
    "Refresher Shard": "refresher_shard",
    "Revenant's Brooch": "revenants_brooch",
    "Riftshadow Prism": "riftshadow_prism",
    "Ring of Health": "ring_of_health",
    "Searing Signet": "searing_signet",
    "Seeds of Serenity": "seeds_of_serenity",
    "Serrated Shiv": "serrated_shiv",
    "Shawl": "shawl",
    "Skadi": "skadi",
    "Solar Crest": "solar_crest",
    "Spellslinger": "spellslinger",
    "Spider Legs": "spider_legs",
    "Splintmail": "splintmail",
    "Stonefeather Satchel": "stonefeather_satchel",
    "Stormcrafter": "stormcrafter",
    "Tranquil Boots": "tranquil_boots",
    "Veil of Discord": "veil_of_discord",
    "Void Stone": "void_stone",
    "Voodoo Mask": "voodoo_mask",
    "Weighted Dice": "weighted_dice",
    "Whisper of the Dread": "whisper_of_the_dread",
    "Wizard Hat": "wizard_hat",
    "Yasha and Kaya": "yasha_and_kaya",
}


def hero_img(name):
    slug = HERO_SLUG.get(name, name.lower().replace(" ", "_").replace("'", ""))
    return f"{HERO_CDN}{slug}.png"


def item_img(name):
    slug = ITEM_SLUG.get(name, name.lower().replace(" ", "_").replace("'", ""))
    return f"{ITEM_CDN}{slug}.png"


# Ability image URL: slug = internal ability name, e.g. "antimage_blink"
# Pattern: hero_slug + "_" + ability_internal_name (from npc_heroes.txt AbilityName keys)
# Example: abil_img("antimage_mana_void")
def abil_img(slug):
    return f"{ABIL_CDN}{slug}.png"


# Slug -> (color, icon_name) — collected from patchnotes datafeeds 7.34..7.41d
# (scripts: see prompt that built data/facets_icons.json). Provides the
# generic facet-icon name (e.g. "cooldown", "gold", "snake") for every
# facet that ever appeared as a `hero_facet` subsection. PNGs extracted
# from pak01_dir.vpk live in icons/facets/<icon>.png (white silhouette
# on transparent — designed to overlay on the colored facet block).
def _load_facet_icons():
    import json as _json2
    import os as _os2
    p = _os2.path.join(_os2.path.dirname(_os2.path.abspath(__file__)), "..", "data", "facets_icons.json")
    if not _os2.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return _json2.load(f)

_FACET_ICONS = _load_facet_icons()
