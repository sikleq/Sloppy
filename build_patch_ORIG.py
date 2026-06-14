#!/usr/bin/env python3
"""Generate annotated Dota 2 7.41c patch notes HTML."""

import json as _json
import os as _os
import html as _html
import re

# ---------- STATS DATABASE ----------
# Loads data/stats/{version}/heroes.json + items.json into memory at build time.
# Use stat_h(hero_display, field, version) / stat_i(item_display, field, version)
# to look up values. Use bstat_h() to auto-generate a badge from a delta.

def _load_stats_db():
    db_h, db_i, db_u = {}, {}, {}
    base = _os.path.join(_os.path.dirname(__file__), "data", "stats")
    if not _os.path.isdir(base):
        return db_h, db_i, db_u
    for ver in _os.listdir(base):
        vdir = _os.path.join(base, ver)
        if not _os.path.isdir(vdir):
            continue
        for fname, target in (("heroes.json", db_h),
                              ("items.json",  db_i),
                              ("units.json",  db_u)):
            fp = _os.path.join(vdir, fname)
            if _os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    target[ver] = _json.load(f)
    return db_h, db_i, db_u

_STATS_H, _STATS_I, _STATS_U = _load_stats_db()


def _load_item_classes(version):
    """Parse data/stats/<version>/items.txt → (neutral, obsolete, present) sets of
    game slugs ('item_<x>'). Authoritative item classification for items_dyn,
    straight from Valve's KV (no patch-note dependency):
      - neutral item     : "ItemIsNeutralActiveDrop" "1"
      - removed/obsolete  : "IsObsolete" "1"  (kept in the file for old replays,
                            but no longer in the game — e.g. Cornucopia)
      - enchantments are detected by the item_enhancement_ prefix (caller side).
      - regular item      : present, not neutral, not obsolete.
    'current' (still in the game) = present AND not obsolete. NOTE: neutral items
    carry ItemPurchasable "0" too, so DON'T use purchasable as the removed signal.
    Returns empty sets if the file is absent (degrade gracefully)."""
    path = _os.path.join(_os.path.dirname(__file__), "data", "stats", version, "items.txt")
    present, neutral, obsolete = set(), set(), set()
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return neutral, obsolete, present
    cur = None
    name_re = re.compile(r'^\s*"(item_[a-z0-9_]+)"\s*$')
    for ln in lines:
        m = name_re.match(ln)
        if m:
            cur = m.group(1)
            present.add(cur)
            continue
        if not cur:
            continue
        if 'ItemIsNeutralActiveDrop' in ln and '"1"' in ln:
            neutral.add(cur)
        if 'IsObsolete' in ln and '"1"' in ln:
            obsolete.add(cur)
    return neutral, obsolete, present


def _stat_h_raw(npc_key: str, field: str, version: str):
    """Look up `field` for `npc_key` at `version`; fall back to npc_dota_hero_base
    when the hero doesn't override (Valve KV inheritance)."""
    bucket = _STATS_H.get(version, {})
    val = bucket.get(npc_key, {}).get(field)
    if val is None:
        val = bucket.get("npc_dota_hero_base", {}).get(field)
    return val


def stat_h(hero_display: str, field: str, version: str):
    """
    Возвращает числовое значение стата героя в указанном патче или None.
    Если у героя нет явного значения в KV — берёт из npc_dota_hero_base
    (Valve использует наследование, скрейпер выгребает только явные поля).
    """
    raw_slug = HERO_SLUG.get(hero_display,
                              hero_display.lower().replace(" ", "_").replace("'", ""))
    return _stat_h_raw("npc_dota_hero_" + raw_slug, field, version)


def stat_i(item_display: str, field: str, version: str):
    """
    Возвращает числовое значение стата предмета в указанном патче или None.

    item_display — отображаемое имя (как в ITEM_SLUG), например "Blink Dagger"
    field        — ключ из items.txt, например "ItemCost", "ItemCooldown"
    version      — патч, например "7.41"
    """
    raw_slug = ITEM_SLUG.get(item_display,
                              item_display.lower().replace(" ", "_").replace("'", ""))
    item_key = "item_" + raw_slug
    return _STATS_I.get(version, {}).get(item_key, {}).get(field)


def bstat_h(hero_display: str, field: str, patch_before: str, delta,
            l: bool = False):
    """
    Бейдж для изменения стата героя на delta от патча patch_before.

    Автоматически берёт старое значение из БД и вычисляет новое.
    delta — число: положительное = увеличение, отрицательное = уменьшение.

    Пример:
        # "Base Armor decreased by 1" в 7.41a, до этого патча было 7.41
        W(li("Base Armor decreased by 1", bstat_h("Doom", "ArmorPhysical", "7.41", -1)))
    """
    old = stat_h(hero_display, field, patch_before)
    if old is None:
        return t("NERF") if delta < 0 else t("BUFF")
    new = old + delta
    return b(old, new, l=l)


def _patch_sort_key(v: str):
    """Sort key for patch versions like '7.41', '7.41b'. Returns (major, minor, suffix)."""
    parts = v.split(".")
    major = int(parts[0]) if parts[0].isdigit() else 0
    rest = parts[1] if len(parts) > 1 else "0"
    num = ""
    suf = ""
    for c in rest:
        if c.isdigit():
            num += c
        else:
            suf += c
    return (major, int(num) if num else 0, suf)


def _prev_change_patch(db: dict, key_with_prefix: str, field: str, before_patch: str):
    """Returns the patch in which the value at `before_patch` was first set
    (i.e. the most recent earlier patch where the value differs from the
    target, +1 step). None if value never changed within known history.
    Falls back to npc_dota_hero_base / item_base when the entity doesn't
    override the field (Valve KV inheritance)."""
    base_key = "npc_dota_hero_base" if key_with_prefix.startswith("npc_dota_hero_") else None

    def _at(v):
        bucket = db.get(v, {})
        val = bucket.get(key_with_prefix, {}).get(field)
        if val is None and base_key:
            val = bucket.get(base_key, {}).get(field)
        return val

    target = _at(before_patch)
    if target is None:
        return None
    versions = sorted([v for v in db
                       if _patch_sort_key(v) <= _patch_sort_key(before_patch)],
                      key=_patch_sort_key)
    last_with_target = before_patch
    for v in reversed(versions[:-1]):
        if _at(v) != target:
            return last_with_target
        last_with_target = v
    # No transition found — value held since the oldest patch in our DB.
    # Signal this with a "<oldest" marker so the caller can render "before X".
    return f"<{versions[0]}" if versions else last_with_target


def prev_change_patch_h(hero_display: str, field: str, before_patch: str):
    raw_slug = HERO_SLUG.get(hero_display,
                              hero_display.lower().replace(" ", "_").replace("'", ""))
    return _prev_change_patch(_STATS_H, "npc_dota_hero_" + raw_slug, field, before_patch)


def prev_change_patch_i(item_display: str, field: str, before_patch: str):
    raw_slug = ITEM_SLUG.get(item_display,
                              item_display.lower().replace(" ", "_").replace("'", ""))
    return _prev_change_patch(_STATS_I, "item_" + raw_slug, field, before_patch)


def bstat_i(item_display: str, field: str, patch_before: str, delta,
            l: bool = False):
    """Аналог bstat_h для предметов."""
    old = stat_i(item_display, field, patch_before)
    if old is None:
        return t("NERF") if delta < 0 else t("BUFF")
    new = old + delta
    return b(old, new, l=l)


def stat_u(unit_key: str, field: str, version: str):
    """Unit stat lookup. `unit_key` is the full npc key, e.g.
    'npc_dota_beastmaster_boar'. Returns None when missing."""
    return _STATS_U.get(version, {}).get(unit_key, {}).get(field)


def prev_change_patch_u(unit_key: str, field: str, before_patch: str):
    return _prev_change_patch(_STATS_U, unit_key, field, before_patch)


def bstat_u(unit_key: str, field: str, patch_before: str, delta,
            l: bool = False):
    """Same as bstat_h/_i but for summons / neutral creeps."""
    old = stat_u(unit_key, field, patch_before)
    if old is None:
        return t("NERF") if delta < 0 else t("BUFF")
    new = old + delta
    return b(old, new, l=l)


# ---------- IMAGE URL HELPERS ----------

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
_ABIL_ICON_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "icons", "abilities")
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
    # (lowercase + spaces→underscores + strip apostrophes). Verify against
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


# ---------- BADGE HELPERS ----------

def gradient_class(magnitude, is_buff):
    """10-tier gradient based on absolute %. Covers 0-100%+ smoothly."""
    prefix = "buff" if is_buff else "nerf"
    if magnitude == 0:
        return "neutral"
    if magnitude <= 5:    return f"{prefix}1"
    if magnitude <= 10:   return f"{prefix}2"
    if magnitude <= 15:   return f"{prefix}3"
    if magnitude <= 20:   return f"{prefix}4"
    if magnitude <= 25:   return f"{prefix}5"
    if magnitude <= 33:   return f"{prefix}6"
    if magnitude <= 45:   return f"{prefix}7"
    if magnitude <= 60:   return f"{prefix}8"
    if magnitude <= 80:   return f"{prefix}9"
    return f"{prefix}10"


def b(old, new, l=False, slash=False, force_overall=None):
    """Generate per-level badges. old/new can be scalar or list.
    l=True means lower-is-buff (cooldowns, mana costs, penalties).
    slash=True separates the badges with " / " instead of ", " — use it for
    PAIRED dimensions (e.g. daytime / nighttime vision), not level progressions.
    If all per-level badges turn out identical, collapses to a single badge.
    Determines OVERALL buff/nerf tag by the MAX-RANK (last non-zero) per-level
    value's direction. Refinement: when max-rank is a SMALL nerf (≤12%) but the
    per-level deltas AVERAGE to a buff (early-level buffs outweigh an
    insignificant late dip), it flips to BUFF — so a front-loaded rescale like
    15/30/45/60→25/35/45/55 (+67/+17/0/-8) reads as a buff. The ≤12% cap keeps
    "flattening" rescales (big max-rank nerf, e.g. Drow 4/8/12/16→10 =
    +150/+25/-17/-38) as a max-rank nerf, and the inverse case (early nerf, late
    buff — Disseminate) is already buff via max-rank. Pass force_overall=
    "buff"/"nerf" to override outright. Per-level % badges are never affected.

    Sign convention: the `+`/`-` reflects the RAW numeric direction
    (`+` when new > old, `-` when new < old). The badge COLOUR reflects
    player benefit (`l=True` flips green/red). So a cost going 600 → 700
    renders as `+17%` red — sign matches the arithmetic, colour matches
    the impact on the player.
    """
    if not isinstance(old, (list, tuple)):
        old = [old]
    if not isinstance(new, (list, tuple)):
        new = [new]
    if len(old) == 1 and len(new) > 1:
        old = old * len(new)
    if len(new) == 1 and len(old) > 1:
        new = new * len(old)

    parts = []
    keys = []
    signed_pcts = []
    for o, n in zip(old, new):
        if n == o:
            parts.append('<span class="badge neutral">0%</span>')
            keys.append(("neutral", "0%"))
            signed_pcts.append(0)
            continue
        if o == 0:
            # Old value was 0 → % delta is undefined (0 → X has no meaningful
            # percentage). Emit a plain BUFF / NERF text-tag with no numeric
            # chip; the row still classifies for filtering.
            is_buff = (n < o) if l else (n > o)
            if is_buff:
                parts.append('<span class="badge buff-text" data-overall="buff">BUFF</span>')
                keys.append(("buff-text", "BUFF"))
                signed_pcts.append(1)
            else:
                parts.append('<span class="badge nerf-text" data-overall="nerf">NERF</span>')
                keys.append(("nerf-text", "NERF"))
                signed_pcts.append(-1)
            continue
        raw = (n - o) / o * 100
        pct = round(raw)
        # Tiny non-zero deltas (e.g. +252 → +253 = +0.4%) round to 0 with
        # integer rounding but are still meaningful directional changes.
        # Show one-decimal precision so the buff/nerf direction surfaces.
        is_buff = (n < o) if l else (n > o)
        if pct == 0:
            # Sub-percent delta → render as "+0.X%" / "-0.X%" with one-decimal
            # rounding (drops to integer-zero only when the raw value is
            # literally 0). Magnitude floored at 1 for gradient/tag purposes.
            small = round(abs(raw), 1)
            if small == 0:
                parts.append('<span class="badge neutral">0%</span>')
                keys.append(("neutral", "0%"))
                signed_pcts.append(0)
                continue
            # Sign follows the RAW numeric direction; colour (via gradient_class)
            # reflects player benefit. See docstring.
            sign = "+" if n > o else "-"
            display = f"{sign}{small}%"
            cls = gradient_class(1, is_buff)  # weakest gradient
            signed_pcts.append(small if is_buff else -small)
            parts.append(f'<span class="badge {cls}">{display}</span>')
            keys.append((cls, display))
            continue
        magnitude = abs(pct)
        signed_pcts.append(magnitude if is_buff else -magnitude)
        sign = "+" if n > o else "-"
        cls = gradient_class(magnitude, is_buff)
        display = f"{sign}{magnitude}%"
        parts.append(f'<span class="badge {cls}">{display}</span>')
        keys.append((cls, display))

    # Determine overall tag.
    # Rule: tag by the MAX-RANK (last) per-level value's direction — that's
    # the level the hero settles at once the ability is maxed, which the
    # player feels for most of the late game. Falls back to scanning
    # backwards if the max-rank delta is neutral.
    #
    # Counter-example that motivated this rule: Disseminate
    # 20/25/30/35% → 16/24/32/40%. Per-level deltas: -20%, -4%, +7%, +14%.
    # Signed avg ≈ -0.75% → previously tagged NERF. But at L4 (max rank,
    # where the ability lives most of the game) it's 35→40 = +14% buff.
    # Max-rank-based tagging surfaces that correctly.
    #
    # Formula rows (li_formula / bf) intentionally keep their own avg-based
    # logic — they show explicit L1/L_end badges, so the overall tag's
    # role is different there.
    overall = ""
    max_rank = 0
    if signed_pcts:
        for v in reversed(signed_pcts):
            if v != 0:
                max_rank = v
                overall = "buff" if v > 0 else "nerf"
                break
        # Front-loaded rescale: max-rank is a SMALL nerf (≤12%) but the per-level
        # deltas AVERAGE to a buff — the early-level buffs outweigh an
        # insignificant late dip → BUFF (Riki Blink Strike 15/30/45/60→25/35/45/55
        # = +67/+17/0/-8). Inverse case (early nerf, late buff — Disseminate) is
        # already buff via max-rank, untouched.
        if (overall == "nerf" and abs(max_rank) <= 12
                and sum(signed_pcts) / len(signed_pcts) > 0):
            overall = "buff"
        # Mirror case — BACK-loaded rescale: max-rank is a SMALL buff (≤12%)
        # but the per-level deltas AVERAGE to a nerf (early-level nerfs
        # outweigh an insignificant late gain) → NERF. Kez Kazurai Katana
        # 5/7/9/11→3/6/9/12% (-40/-14/0/+9, avg -11.25%) reads as a nerf.
        # Disseminate (-20/-4/+7/+14, max +14 > 12) keeps its max-rank BUFF.
        if (overall == "buff" and abs(max_rank) <= 12
                and sum(signed_pcts) / len(signed_pcts) < 0):
            overall = "nerf"
        # "Flatten" rescale (X/Y/Z/W → ONE flat value): level-scaling removed.
        # Classify by whether the flat value beats the old AVERAGE — ties (mean
        # unchanged) go to BUFF, since the early levels still rose even when the
        # average nets even (Drow Agility 4/8/12/16→10: mean 10=10, but L1/L2
        # jumped up). l=True flips the compare. Supersedes the max-rank tag for
        # flattens (the maxed level isn't the whole story when every other level
        # shifted the other way).
        if len(set(new)) == 1 and len(set(old)) > 1:
            old_mean = sum(old) / len(old)
            flat_v = new[0]
            better = (flat_v <= old_mean) if l else (flat_v >= old_mean)
            overall = "buff" if better else "nerf"
    # Per-row override: when the max-rank heuristic disagrees with the real
    # gameplay impact (e.g. a rescale that buffs early levels and only slightly
    # nerfs max rank), pass force_overall="buff"/"nerf" to set the left tag
    # + filter direction explicitly. Per-level % badges are unaffected.
    if force_overall is not None:
        overall = force_overall

    # Collapse if every level produced an identical badge
    if len(keys) > 1 and len(set(keys)) == 1:
        parts = [parts[0]]

    overall_attr = f' data-overall="{overall}"' if overall else ""
    grp_cls = "badge-group slash-sep" if slash else "badge-group"
    return f'<span class="{grp_cls}"{overall_attr}>' + "".join(parts) + "</span>"


def br(old_min, old_max, new_min, new_max, l=False):
    """Damage range (min-max). Computes single % from midpoint average.
    Use this for 'Damage at level 1: 51-57 to 52-58' style lines."""
    old_avg = (old_min + old_max) / 2
    new_avg = (new_min + new_max) / 2
    return b(old_avg, new_avg, l=l)


def _compute_pct(old_v, new_v, l):
    """Return (cls, display, signed_pct, overall_tag)."""
    if old_v == 0 or new_v == old_v:
        return ("neutral", "0%", 0, "")
    raw = (new_v - old_v) / old_v * 100
    pct = round(raw)
    if pct == 0:
        return ("neutral", "0%", 0, "")
    is_buff = (new_v < old_v) if l else (new_v > old_v)
    magnitude = abs(pct)
    # Sign reflects raw arithmetic direction; colour (via gradient_class)
    # reflects player benefit. See b()'s docstring for the rationale.
    sign = "+" if new_v > old_v else "-"
    cls = gradient_class(magnitude, is_buff)
    return (cls, f"{sign}{magnitude}%", magnitude if is_buff else -magnitude,
            "buff" if is_buff else "nerf")


_formula_id_counter = [0]

def fold(text):
    """Wrap an OLD formula in a span with subtle dotted underline (visual reference only)."""
    return f'<span class="formula-old">{text}</span>'


def bf(old_fn, new_fn, formula_text, levels=None, l=False, value_fmt="{:g}",
       level_prefix='L', level_fmt=None, jump_at=20, headline_level=1,
       effective_unchanged=False):
    """Formula-based change. Returns (trigger_html, badge_html, table_html).
    The trigger wraps formula_text as a clickable pill that toggles the table.
    Tag is determined by `headline_level` (default L1).
    levels: list of int levels to show; defaults to L1-15 + L20, L25, L30.
            Can also pass an int N → range(1, N+1).
    value_fmt: format string for level values (e.g. '{:.2f}%' or '{:g}').
    level_prefix: prefix shown before each column header (default 'L').
                  Ignored when level_fmt is provided.
    level_fmt: optional callable(L) → header label; lets the caller override
               the default 'L1', 'L2'… formatting (e.g. '1:00', '2:00').
    jump_at: level value that gets the visual gap class (default 20).

    The Δ% row is dropped automatically when every level resolves to the same
    delta — in that case the headline badge already conveys the full picture."""
    if levels is None:
        levels = list(range(1, 16)) + [20, 25, 30]
    elif isinstance(levels, int):
        levels = list(range(1, levels + 1))

    if level_fmt is None:
        level_fmt = lambda L: f'{level_prefix}{L}'

    _formula_id_counter[0] += 1
    fid = f"f{_formula_id_counter[0]}"

    # Caller-declared reformulation: Valve's patch note explicitly states
    # "Effective values are not changed" (formula re-parametrized but the
    # final in-game values match across all relevant contexts). The raw
    # per-level Δ% would be misleading here — show a single-row "value"
    # table and an empty badge-group so the left REWORK tag carries the
    # row's meaning.
    if effective_unchanged:
        def _cls(L): return ' class="lvl-jump"' if L == jump_at else ''
        head_cells = "".join(f'<th{_cls(L)}>{level_fmt(L)}</th>' for L in levels)
        val_cells  = "".join(f'<td{_cls(L)}>{value_fmt.format(new_fn(L))}</td>' for L in levels)
        trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'
        badge   = '<span class="badge-group"></span>'
        table   = (f'<table class="formula-table" id="{fid}" hidden>'
                   f'<thead><tr><th></th>{head_cells}</tr></thead>'
                   f'<tbody><tr><th class="row-label-new">value</th>{val_cells}</tr></tbody>'
                   f'</table>')
        return trigger, badge, table

    # Headline-level inline badge (used when row is collapsed).
    # "start" always means L1 (the level the user thinks of as the beginning
    # of the game) — even if L1's delta is 0%. Do NOT shift to a later level
    # just because that level shows a more dramatic delta; the reader can see
    # the per-level breakdown by clicking the formula trigger.
    cls1, disp1, _, overall1 = _compute_pct(old_fn(headline_level), new_fn(headline_level), l)
    # Overall buff/nerf for the filter: average the SIGNED per-level
    # deltas across ALL levels (including 0% ones) — same convention as
    # `b()`. Per-level formulas like "2% → 1.9% + 0.1% per level" can be
    # 0% at L1 but a clear buff later; the filter still surfaces them.
    signed_pcts = []
    for L in levels:
        ov, nv = old_fn(L), new_fn(L)
        if ov == nv or ov == 0:
            signed_pcts.append(0.0)
            continue
        pct = (nv - ov) / ov * 100
        if round(pct) == 0:
            signed_pcts.append(0.0)
            continue
        is_buff = (nv < ov) if l else (nv > ov)
        signed_pcts.append(abs(pct) if is_buff else -abs(pct))
    avg_signed = sum(signed_pcts) / len(signed_pcts) if signed_pcts else 0.0
    overall_eff = ('buff' if avg_signed > 0 else
                   'nerf' if avg_signed < 0 else
                   overall1)
    overall_attr = f' data-overall="{overall_eff}"' if overall_eff else ""
    # If the headline-level cell is 0% but the formula is a net buff/nerf
    # across other levels (e.g. "2% → 1.9% + 0.1% per level" — flat at L1,
    # ramps up later), promote the rightmost level's delta to the headline
    # slot so the row shows a meaningful "+X%" instead of "0%". Embed a
    # `data-force-left="buff"|"nerf"` hint on the badge-group so li_formula
    # swaps its default REWORK left tag for a matching BUFF/NERF text tag.
    force_left_attr = ""
    # Per-level formula that visibly differs across levels — show TWO
    # badges (L1 = "start", last level = "end") so the reader sees both
    # the early-game and late-game impact at a glance. Falls back to a
    # single badge when start and end are identical (no per-level
    # variation worth surfacing).
    last_L = levels[-1]
    clsN, dispN, _, _ = _compute_pct(old_fn(last_L), new_fn(last_L), l)
    different_endpoints = (cls1, disp1) != (clsN, dispN)
    # Force start/end pair whenever the formula's per-level impact differs
    # across the table — either the endpoints themselves differ, OR they
    # both read 0% but the overall avg is non-neutral (mid-game levels
    # carry the change). In both cases the reader should see "L1 start /
    # last end" so the row visibly signals "this is a per-level formula".
    needs_pair = different_endpoints or (cls1 == "neutral" and overall_eff in ("buff", "nerf"))
    if needs_pair:
        badge_inner = (
            f'<span class="badge {cls1}">{disp1}</span>'
            f'<span class="formula-endpoint-label">start</span>'
            f'<span class="badge {clsN}">{dispN}</span>'
            f'<span class="formula-endpoint-label">end</span>'
        )
        # Left tag uses the overall avg direction (not L1's), so a row that
        # is a nerf at L1 but a buff at L30 still classifies by net trend.
        if overall_eff in ("buff", "nerf"):
            force_left_attr = f' data-force-left="{overall_eff}"'
    else:
        badge_inner = f'<span class="badge {cls1}">{disp1}</span>'
    badge = f'<span class="badge-group"{overall_attr}{force_left_attr}>{badge_inner}</span>'

    # Trigger
    trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'

    def cls_for(L):
        return ' class="lvl-jump"' if L == jump_at else ''

    head_cells = "".join(f'<th{cls_for(L)}>{level_fmt(L)}</th>' for L in levels)
    old_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(old_fn(L))}</td>' for L in levels)
    new_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(new_fn(L))}</td>' for L in levels)

    # Reformulation only (e.g. 7.41 innate notation change with subnote
    # "Effective values are not changed"): both fns produce the same number
    # at every level. Collapse the old/new pair into a single "value" row —
    # the diff table would just show two identical lines otherwise.
    values_unchanged = all(old_fn(L) == new_fn(L) for L in levels)
    if values_unchanged:
        table = (
            f'<table class="formula-table" id="{fid}" hidden>'
            f'<thead><tr><th></th>{head_cells}</tr></thead>'
            f'<tbody><tr><th class="row-label-new">value</th>{new_cells}</tr></tbody>'
            f'</table>'
        )
        return trigger, badge, table

    pct_data = [_compute_pct(old_fn(L), new_fn(L), l) for L in levels]
    pct_cells = [
        f'<td{cls_for(L)}><span class="badge {cls}">{disp}</span></td>'
        for L, (cls, disp, _, _) in zip(levels, pct_data)
    ]
    uniform_delta = len({(cls, disp) for cls, disp, _, _ in pct_data}) == 1

    pct_row = "" if uniform_delta else (
        f'<tr><th>Δ %</th>{"".join(pct_cells)}</tr>'
    )

    table = (
        f'<table class="formula-table" id="{fid}" hidden>'
        f'<thead><tr><th></th>{head_cells}</tr></thead>'
        f'<tbody>'
        f'<tr><th class="row-label-old">old</th>{old_cells}</tr>'
        f'<tr><th class="row-label-new">new</th>{new_cells}</tr>'
        f'{pct_row}'
        f'</tbody>'
        f'</table>'
    )

    return trigger, badge, table


# Facet metadata keyed by facet slug (e.g. "broodmother_necrotic_webs").
# Sourced from Valve's live patchnotes datafeed:
#   /datafeed/patchnotes?version=<X>&language=english → heroes[].subsections[]
#     {title, facet, facet_color, facet_icon, abilities: [...]}
# Run scripts/fetch_facets.py to regenerate this dict for a given patch.
# Value tuple: (display_title, valve_color_key).
FACETS = {
    # 7.40 — fetched 2026-05-19 from /datafeed/patchnotes?version=7.40
    "batrider_arsonist":                ("Arsonist",             "Yellow1"),
    "bounty_hunter_mugging":            ("Cutpurse",             "Yellow0"),
    "bristleback_snot_rocket":          ("Snot Rocket",          "Green0"),
    "enchantress_overprotective_wisps": ("Overprotective Wisps", "Green0"),
    "gyrocopter_afterburner":           ("Afterburner",          "Yellow1"),
    "hoodwink_hunter":                  ("Go Nuts",              "Yellow0"),
    "leshrac_misanthropy":              ("Misanthropy",          "Purple0"),
    "magnataur_diminishing_return":     ("Diminishing Return",   "Blue2"),
    "meepo_more_meepo":                 ("More Meepo",           "Blue2"),
    "mirana_starstruck":                ("Starstruck",           "Blue1"),
    "monkey_king_simian_stride":        ("Simian Stride",        "Green4"),
    "morphling_str":                    ("Flow",                 "Red0"),
    "naga_siren_active_riptide":        ("Deluge",               "Green2"),
    "naga_siren_passive_riptide":       ("Rip Tide",             "Yellow2"),
    "necrolyte_profane_potency":        ("Profane Potency",      "Yellow2"),
    "night_stalker_voidbringer":        ("Voidbringer",          "Blue0"),
    "primal_beast_ferocity":            ("Ferocity",             "Yellow3"),
    "pugna_siphoning_ward":             ("Siphoning Ward",       "Green0"),
    "queenofpain_facet_bondage":        ("Bondage",              "Blue0"),
    "razor_thunderhead":                ("Thunderhead",          "Gray0"),
    "shadow_shaman_massive_serpent_ward":("Massive Serpent Ward","Red1"),
    "silencer_spread_the_knowledge":    ("Synaptic Split",       "Purple1"),
    "venomancer_plague_carrier":        ("Plague Carrier",       "Yellow0"),
    "witch_doctor_malpractice":         ("Malpractice",          "Red2"),
    # 7.40c — fetched 2026-05-16 from /datafeed/patchnotes?version=7.40c
    "huskar_cauterize":         ("Cauterize",      "Red0"),
    "broodmother_necrotic_webs":("Necrotic Webs",  "Gray0"),
    "shadow_demon_promulgate":  ("Promulgate",     "Gray0"),
    "ringmaster_carny_classics":("Carny Classics", "Yellow1"),
    # 7.40b — fetched 2026-05-16 from /datafeed/patchnotes?version=7.40b
    "drow_ranger_sidestep":          ("Sidestep",         "Blue1"),
    "invoker_wex_focus":             ("Mind of Tornarus", "Purple0"),
    "legion_commander_spoils_of_war":("Spoils of War",    "Red0"),
    "pudge_fresh_meat":              ("Fresh Meat",       "Red0"),
    "skeleton_king_facet_bone_guard":("Bone Guard",       "Yellow0"),
    "tidehunter_sizescale":          ("Krill Eater",      "Green0"),
    "ursa_debuff_reduce":            ("Bear Down",        "Blue0"),
    "viper_caustic_bath":            ("Caustic Bath",     "Yellow2"),
    "windrunner_tangled":            ("Tangled",          "Yellow2"),
    "witch_doctor_cleft_death":      ("Cleft Death",      "Purple0"),
    # --- Removed in 7.40 — colours lifted from the pre-7.40 datafeed
    #     (scripts/fetch_facets.py over 7.36..7.39e). Kept here manually so a
    #     future fetch_facets regen for a current patch doesn't drop them. ---
    "brewmaster_roll_out_the_barrel":   ("Roll Out the Barrel", "Red1"),
    "brewmaster_drunken_master":        ("Drunken Master",      "Yellow1"),
    "clinkz_suppressive_fire":          ("Suppressive Fire",    "Gray3"),
    "clinkz_engulfing_step":            ("Engulfing Step",      "Yellow0"),
    "doom_bringer_boost_selling":       ("Devil's Bargain",     "Yellow0"),
    "earth_spirit_resonance":           ("Resonance",           "Green0"),
    "earth_spirit_stepping_stone":      ("Stepping Stone",      "Gray2"),
    "earth_spirit_ready_to_roll":       ("Ready to Roll",       "Yellow1"),
    "lone_druid_bear_with_me":          ("Bear with Me",        "Green1"),
    "lone_druid_bear_necessities":      ("Bear Necessities",    "Gray1"),
    "pangolier_double_jump":            ("Double Jump",         "Red1"),
    "pangolier_thunderbolt":            ("Thunderbolt",         "Yellow1"),
    "phantom_lancer_divergence":        ("Divergence",          "Blue2"),
    "phantom_lancer_lancelot":          ("Lancelot",            "Yellow0"),   # = renamed Convergence
    "riki_contract_killer":             ("Contract Killer",     "Gray3"),
    "riki_exterminator":                ("Exterminator",        "Purple2"),
    "slark_leeching_leash":             ("Leeching Leash",      "Green2"),
    "slark_dark_reef_renegade":         ("Dark Reef Renegade",  "Blue2"),
    "spectre_forsaken":                 ("Forsaken",            "Gray0"),
    "spectre_twist_the_knife":          ("Twist the Knife",     "Purple2"),
    "treant_primeval_power":            ("Primeval Power",      "Yellow2"),
    "treant_sapling":                   ("Sapling",             "Green2"),
    "marci_fleeting_fury":              ("Fleeting Fury",       "Red1"),      # COLOUR GUESSED
    # --- Other current facets referenced in patch text but never emitted as a
    #     standalone hero_facet subsection in the datafeed (so fetch_facets
    #     can't see them). Colours pulled from prior-name datafeed snapshots
    #     when the slug was renamed. ---
    "abaddon_the_quickening":           ("The Quickening",      "Gray0"),     # = renamed abaddon_death_dude (7.36 datafeed Gray0)
}

# Slug → (color, icon_name) — collected from patchnotes datafeeds 7.34..7.41d
# (scripts: see prompt that built data/facets_icons.json). Provides the
# generic facet-icon name (e.g. "cooldown", "gold", "snake") for every
# facet that ever appeared as a `hero_facet` subsection. PNGs extracted
# from pak01_dir.vpk live in icons/facets/<icon>.png (white silhouette
# on transparent — designed to overlay on the colored facet block).
def _load_facet_icons():
    import json as _json2
    p = _os.path.join(_os.path.dirname(__file__), "data", "facets_icons.json")
    if not _os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return _json2.load(f)
_FACET_ICONS = _load_facet_icons()

# Mapping from Valve's facet_color name → CSS gradient that EXACTLY matches
# the in-game / dota2.com patch-page facet pill. Each pill is a simple
# 2-stop `linear-gradient(to right, light, dark)` — the LEFT end is the
# tinted (themed) tone, the RIGHT end is a near-black version of the same
# hue. dota2.com positions the facet icon on the lighter LEFT side and
# the facet name text on the darker RIGHT side, so the text always lands
# on a high-contrast surface regardless of hue.
#
# Source: extracted from dota2.com/public/css/dota_react/main.css by
# resolving the hashed CSS-Module classnames in main.js (FacetColorXxx →
# class hash → .Background → gradient).
_FACET_COLOR_GRADIENT = {
    "Gray0":   "linear-gradient(to right, #565C61, #1B1B21)",
    "Gray1":   "linear-gradient(to right, #6A6D73, #29272C)",
    "Gray2":   "linear-gradient(to right, #95A9B1, #3E464F)",
    "Gray3":   "linear-gradient(to right, #ADB6BE, #4E5557)",
    "Red0":    "linear-gradient(to right, #9F3C3C, #4A2040)",
    "Red1":    "linear-gradient(to right, #954533, #452732)",
    "Red2":    "linear-gradient(to right, #A3735E, #4F2A25)",
    "Yellow0": "linear-gradient(to right, #C8A45C, #6F3D21)",
    "Yellow1": "linear-gradient(to right, #C6A158, #604928)",
    "Yellow2": "linear-gradient(to right, #CAC194, #433828)",
    "Yellow3": "linear-gradient(to right, #C3A99A, #4D352B)",
    "Green0":  "linear-gradient(to right, #A2B23E, #2D5A18)",
    "Green1":  "linear-gradient(to right, #7EC2B2, #29493A)",
    "Green2":  "linear-gradient(to right, #538564, #1C3D3F)",
    "Green3":  "linear-gradient(to right, #9A9F6A, #223824)",
    "Green4":  "linear-gradient(to right, #9FAD8E, #3F4129)",
    "Blue0":   "linear-gradient(to right, #727CB2, #342D5B)",
    "Blue1":   "linear-gradient(to right, #547EA6, #2A385E)",
    "Blue2":   "linear-gradient(to right, #6BAEBC, #135459)",
    "Blue3":   "linear-gradient(to right, #94B5BA, #385B59)",
    "Purple0": "linear-gradient(to right, #B57789, #412755)",
    "Purple1": "linear-gradient(to right, #9C70A4, #282752)",
    "Purple2": "linear-gradient(to right, #675CAE, #261C44)",
}


def facet_badge(facet_slug):
    """Render the facet pill for a Valve facet slug like
    "broodmother_necrotic_webs". Looks up name + color in FACETS and emits
    a gradient-styled square chip matching the tag-badge geometry.

    Usage:
        W(li(facet_badge("broodmother_necrotic_webs") +
             " Max Charges decreased from 4/6/8/10 to 3/5/7/9",
             b([4,6,8,10], [3,5,7,9])))
    """
    if facet_slug not in FACETS:
        raise KeyError(
            f"Unknown facet slug {facet_slug!r}. Add it to FACETS — "
            f"run scripts/fetch_facets.py <patch> to grab the live data."
        )
    name, color = FACETS[facet_slug]
    grad = _FACET_COLOR_GRADIENT.get(color, _FACET_COLOR_GRADIENT["Gray1"])
    return (f'<span class="badge facet-badge" '
            f'style="background-image:{grad}">{name}</span>')


def t(tag):
    """Text-only tag for non-numeric changes.
    NEW (mechanic/property the entity didn't have before) is treated as a buff
    for filter purposes — data-overall='buff' so the BUFF filter also catches it."""
    cls_map = {
        "BUFF":   ("buff-text", "buff"),
        "NERF":   ("nerf-text", "nerf"),
        "REWORK": ("rework",    "rework"),
        "MISC":   ("misc",      "misc"),
        "QoL":    ("qol",       "qol"),
        "NEW":    ("new",       "new"),
        "DEL":    ("del",       "del"),
    }
    color_cls, tag_id = cls_map[tag]
    if tag == "NEW":
        extra = ' data-overall="buff"'   # NEW counts as buff for filtering
    elif tag == "DEL":
        extra = ' data-overall="nerf"'   # DEL (removed) counts as nerf
    else:
        extra = ''
    return f'<span class="badge {color_cls}" data-tag="{tag_id}"{extra}>{tag}</span>'


# ---------- HTML BUILDING ----------

class _State:
    block_open = False
    current_hero = None  # internal slug of current hero block (for ability icon derivation)
    ability_icons = set()  # all ability-icon URLs emitted during build (for icon-validator)
    ability_block_open = False  # tracks <div class="ability-block"> wrapper
    # Auto-categorize hero block contents (Stats / Abilities / Talents subgroups):
    next_ul_is_hero_stats = False    # set by hero_header(), consumed by ul_open()
    in_stats_ul = False              # True while inside the auto-"STATS" ul (sanity-check facet/innate rows)
    section_panel_open = False       # True while inside a <section class="cat-panel"> wrapper
    seen_abilities_subgroup = False  # set when first ability() emits "Abilities" subgroup
    seen_facets_subgroup = False     # set when first facet_header() emits "Facets" subgroup
    current_sections = []            # per-patch list of {slug, label}; reset in save_html()
    current_section_slug = None      # slug of the active section(); "general" suppresses dyn-cells
    # Patch-dynamics widget: tag tallies per (entity, patch). Populated by
    # headers (set current entity key) + li() (increment tag count). Dumped
    # as _dynamics.json at end of build for the JS widget to consume.
    current_patch_version = None     # set by write_head()
    current_entity_key = None        # "<kind>|<slug>" — set by hero/item/unit/plain_header
    current_entity_display = None    # human name for hover tooltip
    dynamics = {}                    # {entity_key: {"name":..., "kind":..., "patches":{ver:{tag:count}}}}
    dyn_skip_li = False              # set by _open_block when block is .is-new —
                                     # whole entity is conceptually a single NEW
                                     # tally; per-li tags inside are stat/property
                                     # rows that shouldn't inflate the dynamics.

def _open_block(extra_cls='', extra_attrs=''):
    pre = _close_ability_block()
    cls = 'entity-block' + ((' ' + extra_cls) if extra_cls else '')
    s = (pre + ('</div>\n' if _State.block_open else '')
         + f'<div class="{cls}"{extra_attrs}>\n')
    _State.block_open = True
    # Dynamics — block-level tag injection:
    #   .is-new      → entity is brand-new; record ONE `new` tally and
    #                  silence subsequent li() tallies (per-row stat lines
    #                  are part of "the entity is new", not separate events).
    #   .is-changed  → recipe changed; record ONE `rework` tally so the
    #                  REWORK filter surfaces the item and the dynamics
    #                  square shows the rework color. Subsequent li()
    #                  tallies still count — other changes inside the
    #                  block remain independent events.
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


# Tags we surface in the dynamics widget. "buff new"/"del nerf" composite
# data-tag strings produce two counts (a NEW row that's also a buff is
# tallied as both new AND buff so filter-relevant colors show up).
_DYN_TAG_WHITELIST = {"buff", "nerf", "new", "del", "rework", "misc", "qol"}


def _dyn_record_li(tags):
    """Increment dynamics tag counts for the current entity/patch.
    `tags` is a set of normalized tag ids (e.g. {'buff','new'})."""
    if _State.dyn_skip_li:
        # NEW-item / NEW-enchantment block — the single `new` tally was
        # recorded in _open_block; per-row stat/property tags inside the
        # block are NOT independent changes and must not inflate counts.
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
    """Lowercase, strip apostrophes/punct, spaces → '-'. Used for entity DOM
    anchors and dynamics-manifest keys."""
    s = name.lower().replace("'", "").replace("'", "")
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def _register_entity(kind, name):
    """Set current entity (for the dynamics tallies) and return the DOM id
    attribute string. Call from every header (hero/item/unit/plain).

    Under the big "General Updates" tab nothing gets a dyn-cell — no entity is
    registered and no id is emitted (single chokepoint for every header type)."""
    if _State.current_section_slug == 'general':
        _State.current_entity_key = None
        _State.current_entity_display = None
        return ''
    slug = _slugify(name)
    key = f"{kind}|{slug}"
    _State.current_entity_key = key
    _State.current_entity_display = name
    rec = _State.dynamics.setdefault(key, {"name": name, "kind": kind, "patches": {}})
    rec["name"] = name  # keep latest display
    # Heroes/items carry their icon slug so the dynamics matrix pages can render
    # the portrait/icon without importing this module (build_patch has no
    # __main__ guard). icons/heroes/<slug>.png and icons/items/<slug>.png.
    if kind == "hero":
        rec["icon"] = HERO_SLUG.get(
            name, name.lower().replace(" ", "_").replace("'", "").replace("-", ""))
    elif kind == "item":
        rec["icon"] = ITEM_SLUG.get(
            name, name.lower().replace(" ", "_").replace("'", ""))
        # Neutral-item section fallback (for the items_dyn class filter): true when
        # this item_header sits under "Neutral Item Updates". Used only when the
        # game file can't classify it (e.g. a fully-removed neutral). Monotonic —
        # once neutral, stays neutral across patches.
        if _State.current_section_slug == 'neutral-items':
            rec["neutral_section"] = True
    elif kind == "enchant":
        # Neutral enchantment icon: icons/items/enhancement_<slug>.png (same dir as
        # items, 'enhancement_' prefix) → game slug item_enhancement_<slug>.
        rec["icon"] = "enhancement_" + name.lower().replace(
            " ", "_").replace("-", "_").replace("'", "")
    return f' id="dyn-{kind}-{slug}"'


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
    """Header for a separate summoned unit / neutral creep (e.g. Spirit Bear,
    Ancient Marshmage) with custom icon URL. Marked `.unit-entity` so the
    search index labels it as a creep/unit, not a hero.

    Pass kind='Creep-hero' (or any custom label) to override the default
    'creep' kind chip in the search dropdown — used for hero-like creeps
    that level/talent up such as Spirit Bear."""
    _State.current_hero = None
    kind_attr = f' data-kind="{kind}"' if kind else ''
    entity_kind = "creep-hero" if (kind and kind.lower().startswith("creep-hero")) else "unit"
    eid = _register_entity(entity_kind, name)
    return _open_block() + f'''<div class="entity unit-entity"{kind_attr}{eid}>
  <div class="entity-icon hero-icon"><img src="{icon_url}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def item_header(name, new=False, changed=False):
    """Item header.

    new=True               → 'NEW' tag, block gets `.is-new` outline.
    new='New X Item'       → tag renders verbatim uppercased ('NEW X ITEM').
    changed=True           → 'Recipe changed' label in neutral colour, same
                             position/style as the new-item type label but no
                             gold tint and no NEW outline.
    changed='custom text'  → custom label in the same neutral style.
    new=False (default)    → no tag, no outline.
    """
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


def components(*parts, total, recipe=None):
    """Visual components block — replaces the 'Requires X (a), Y (b), and a
    recipe (c). Total cost: Ng' row for new items.

    parts:  one or more (item_display_name, cost) tuples. Each part renders
            as the item icon with its cost beneath; parts are separated by
            visual '+' glyphs.
    recipe: (label, cost) for the item's recipe — rendered with the generic
            recipe.png icon. Pass None if the item has no recipe.
    total:  total gold cost of the assembled item, rendered after '=' on the
            right edge of the box.

    Example for Consecrated Wraps:
        W(components(('Vitality Booster', 1000), ('Shawl', 450),
                     ('Crown', 450), recipe=('Recipe', 700), total=2600))
    """
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
    """Flat purchase price for a BASIC (no-recipe) new item — a bordered box
    matching the components() build box (same border/padding), showing the gold
    cost on the right like a recipe item's total. Use under item_header() for
    new shop items that have no build, paired with provides() for their stats."""
    return (f'<div class="item-cost-box">'
            f'<span class="item-cost-label">Cost</span>'
            f'<span class="item-cost-val">{gold}</span>'
            f'</div>')


def provides(*items):
    """Visual properties block — one stat per row, soft outlined box. Use:
        provides('+1.75 Mana Regen', '+3 All Attributes', '+6 Armor')
    Legacy single-string mode with comma-separated values is auto-split."""
    if len(items) == 1 and isinstance(items[0], str) and ',' in items[0]:
        items = [s.strip() for s in items[0].split(',') if s.strip()]
    rows = ''.join(f'<div class="provides-row">{it}</div>' for it in items)
    return f'<div class="provides-box">{rows}</div>'


_PROP_TAG_CSS = {
    'BUFF':   'buff-text',
    'NERF':   'nerf-text',
    'REWORK': 'rework',
    'MISC':   'misc',
    'QOL':    'qol',
    'NEW':    'new',
    'DEL':    'del',
}


def _prop_tag(tag):
    """Render a property-row left tag span. tag is one of BUFF/NERF/REWORK/
    MISC/QoL/NEW/DEL (case-insensitive) or empty string → placeholder span
    that still occupies the tag column so all rows align vertically."""
    if not tag:
        return '<span class="row-tag-empty"></span>'
    key = tag.upper()
    cls = _PROP_TAG_CSS.get(key, 'misc')
    overall = 'buff' if key in ('BUFF', 'NEW') else ('nerf' if key in ('NERF', 'DEL') else 'buff')
    return f'<span class="badge {cls}" data-tag="{key.lower()}" data-overall="{overall}">{key}</span>'


def _prop_cells(row):
    """Normalize a properties_change row spec into (tag, text, badge)."""
    if row is None:
        return ('', '', '')
    if isinstance(row, str):
        return ('', row, '')
    if len(row) == 2:
        return (row[0], row[1], '')
    return (row[0], row[1], row[2])


def properties_change(old, new, old_extras=None, new_extras=None):
    """Two-pane stat properties diff (old grant set → new grant set).

    Each row in `old`/`new` is one of:
      * None                  — explicit blank row (used to align across panes)
      * string                — plain text, no tag, no badge
      * (tag, text)           — left tag (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL)
      * (tag, text, badge)    — tag + right-edge badge (e.g. b(...) %-delta)

    Structurally renders two real `.properties-pane` boxes (equal width via
    grid-template-columns: 1fr arrow 1fr on the parent) with CSS subgrid for
    rows — so row N of the left pane vertically aligns with row N of the
    right pane regardless of which side's content is taller.

    old_extras/new_extras: optional {row_index: html} — drops an extra row
    (show_list etc.) in that pane only, immediately below row_index.
    """
    old_extras = old_extras or {}
    new_extras = new_extras or {}
    n = max(len(old), len(new))
    old_rows = list(old) + [None] * (n - len(old))
    new_rows = list(new) + [None] * (n - len(new))
    # Dynamics tally: each property row carries its own change-tag in the
    # tuple — record it so the entity's dyn-cell reflects buff/nerf/del/new
    # events from properties_change (not just li()-driven rows).
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
                # Empty row — placeholder that occupies the row track so
                # the row gets a minimum height. Spans the pane's 3 inner cols.
                cells.append(
                    f'<span class="property-row-empty" '
                    f'style="grid-row:{cur_row};grid-column:1/-1">&nbsp;</span>'
                )
            else:
                tag, text, badge = _prop_cells(row)
                # When a row has NO numeric badge, let its text span the badge
                # column too (grid-column 2/-1) so it isn't needlessly narrowed
                # by the badge column reserved for other rows — keeps trailing
                # bits like an (i)-tip on the same line.
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

    # Special case: only one side has changes — render just that pane in its
    # own column (left/right) so its position matches the 2-pane layout.
    # An invisible arrow placeholder keeps the centre column at the same
    # width as in 2-pane mode so the visible pane's width matches the
    # components_change panes above it.
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


def inline_note(text):
    """Clarifying note for a single change row (pass via `extra=`).

    Renders as a circled-'i' info marker (see `info_tip`) that `li()`
    relocates INLINE right after the row text — matching the (i) bubbles in
    the official Dota patchnotes. The note body (which may contain rich HTML
    badges / <br>) shows in a hover/focus popup. Wrapped in sentinel comments
    so `li()` can lift it out of `extra` into the row text; in any other
    context the comments are inert and the (i) still works in place."""
    return f'<!--INLINETIP-->{info_tip(text)}<!--/INLINETIP-->'


def info_tip(*lines, header=None):
    """Small circled-'i' marker with a hover/focus popup, mirroring the (i)
    info bubbles in the official Dota patchnotes. Place INLINE inside a li's
    text (or let `inline_note` route it there automatically).

    `lines` are popup body lines (joined with <br>; pass '' for a blank
    separator line). Each line may contain rich HTML (badges, <b>, <br>).
    Optional `header` is shown bold at the top of the popup."""
    body = '<br>'.join(lines)
    head = f'<span class="info-pop-h">{header}</span>' if header else ''
    # Wrapped in <!--TIP--> sentinels so li()'s auto-classifier can exclude the
    # popup text (e.g. a list item mentioning "Aghanim's Scepter" must NOT make
    # the whole row an Aghanim stripe). save_html strips the sentinel comments.
    return ('<!--TIP--><span class="info-tip" tabindex="0">?'
            f'<span class="info-pop">{head}{body}</span></span><!--/TIP-->')


def show_list(*items, summary='Show list'):
    """Collapsible info row attached AFTER a sentence li. Renders on a new
    line below the row text with a rotating triangle arrow, matching the
    style of subnote-collapse but staying inside the same ability box.

    Pass via the `extra=` parameter of `li()` so the details element becomes
    a sibling of .row-text inside the same <li> (not nested in row-text).
    Uses <div>/<span> instead of <ul>/<li> to avoid interfering with the
    ability-box wrapper that augments top-level <li> elements."""
    items_html = ''.join(f'<span class="show-list-item">{it}</span>' for it in items)
    return (f'<details class="show-list-inline">'
            f'<summary><span class="show-list-chevron">▸</span>'
            f'{summary} <span class="subnote-count">({len(items)})</span></summary>'
            f'<div class="show-list-body">{items_html}</div></details>')


def _fmt_formula(expr):
    """Light syntax styling for a formula string: `*`→`×`, wrap identifiers as
    `.f-var` and numbers as `.f-num`; parentheses/operators stay muted (base)."""
    expr = expr.replace('*', '×')
    return re.sub(
        r'[A-Za-z_]\w*|\d+(?:\.\d+)?',
        lambda m: (f'<span class="f-var">{m.group(0)}</span>'
                   if m.group(0)[0].isalpha() or m.group(0)[0] == '_'
                   else f'<span class="f-num">{m.group(0)}</span>'),
        expr)


def _eval_formula(expr, env):
    """Evaluate a plain arithmetic formula string (author-controlled) with the
    given variable bindings. Restricted namespace — no builtins. `^` is treated
    as exponentiation (Valve writes `x^2`), NOT bitwise xor. Write implicit
    products explicitly (`10 * (x-1)`, not `10(x-1)`)."""
    return eval(expr.replace('^', '**'), {"__builtins__": {}}, dict(env))


def _num_fmt(x):
    """Format a computed number: round to 1 dp, drop a trailing .0."""
    return f'{round(float(x), 1):g}'


def _formula_pct_badge(o, n, lower=False):
    """Old→new % for a formula row — wrapped in `.badge-group` so it renders as
    plain coloured text (no pill box), exactly like the % at the end of patch rows."""
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
    """Render an important game-formula change (Assist Gold, Experience, …) as an
    old→new block — same pane + `→` styling as the ability_change rework swap, with
    the formula CENTRED in each pane and variables/numbers lightly coloured. The
    tag badge sits on the LEFT; panes carry NO "Old"/"New" labels (the `→` shows
    direction).

    Interactive worked examples (recommended for every formula): pass
        vary  = (var_name, display_label, [values])   e.g. ("NumHeroes", "Heroes", [1,2,3,4,5])
        fixed = {input_var: default}                   e.g. {"VictimNetworth": 10000}
        unit  = result column header                   e.g. "Gold"
        lower_better = True if a SMALLER result is the buff (default higher=buff)
    Each pane then gets a small grid table (one row per `vary` value) showing that
    formula's result + the old→new Δ% (coloured like b()). A number input lets the
    reader change the `fixed` variable; scripts.js recomputes every row live
    (default shown as the placeholder "By default: <value>"). If a formula has
    `NumHeroes`, give up to 5 rows (1–5, the max team size).

    Emit via ``W()`` — standalone block ``<div>`` carrying its own filter tag.
    See docs/formula-change.md."""
    # tag → (badge css class, filter key). BUFF/NERF use the *-text classes.
    _TAG = {'NEW': ('new', 'new'), 'REWORK': ('rework', 'rework'),
            'BUFF': ('buff-text', 'buff'), 'NERF': ('nerf-text', 'nerf'),
            'DEL': ('del', 'del'), 'MISC': ('misc', 'misc'), 'QOL': ('qol', 'qol')}
    badge_cls, tag_id = _TAG.get(tag.upper(), (tag.lower(), tag.lower()))
    badge = f'<span class="badge {badge_cls}" data-tag="{tag_id}">{tag}</span>'
    has_ex = bool(vary)                 # examples need a vary var
    has_input = bool(vary and fixed)    # input only if there's a free (fixed) var to type

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
        # Δ% column exists only in the NEW table.
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
    """Render the WHOLE Captains Mode draft like the in-game pick/ban screen:
    VERTICAL, step numbers running down the centre, the acting team's slot on the
    LEFT (Team 1 / first pick) or RIGHT (Team 2 / second pick). The Old draft and
    the New draft are shown as two side-by-side vertical boards. Keep the plain
    summary ``li(... t("REWORK"))`` above it; emit via ``W()`` after ``ul_close()``.

    Pass the ENTIRE draft as consecutive phases — each a 3-tuple
    ``(phase_title, old_subseq, new_subseq)`` covering that phase's actions, in
    order. Concatenated they form the full draft; steps are numbered continuously
    1..N (the in-game step numbers, e.g. 1–24). Each seq char encodes one action:

        'F' = BAN  by the first-pick team    'S' = BAN  by the second-pick team
        'f' = PICK by the first-pick team    's' = PICK by the second-pick team

    Side (left = first pick, right = second pick) encodes the team — no colours.
    Layout is symmetric between Old and New (each step sits at the SAME row in
    both boards, so only the patch's side changes stand out): BANS are one fixed
    1-row slot each (all identical size); PICKS pair up — two consecutive picks
    (one per side) share a 2-row band so they sit FACING each other and read
    taller, like the in-game board. (Picks are identical in Old/New, so pairing
    them keeps the boards aligned.) Bans are narrow boxes, picks fill the lane. A
    long connector ties each number to its slot. Phase
    titles are required in the tuples (document the structure) but not drawn; there
    is no legend and no change-highlight.

    See docs/captains-mode.md for the authoring rule (when/how to use this)."""
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
                # PICKS pair up (consecutive opposite-side picks) into a 2-row band
                # so they sit FACING each other. The pick structure is identical in
                # Old and New, so this keeps the two boards perfectly aligned.
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
                # Each BAN is its own single row at a FIXED position: every ban is
                # the same size, and step N sits at the same row in BOTH boards —
                # only the side changes for the bans the patch reordered, so Old
                # and New stay symmetric.
                cells.append(_num(i + 1, _team(a), row))
                cells.append(_slot(_team(a), 'ban', row, 1))
                row += 1
                i += 1
        grid = f'<div class="cm-vgrid">{"".join(cells)}</div>'
        return f'<div class="cm-board">{grid}</div>'

    # Old on the left, New on the right (implied by the arrow — no Old/New labels).
    # Same arrow glyph as the ability_change rework panes.
    boards = (f'<div class="cm-boards">{_board("Old")}'
              f'<span class="cm-arrow">→</span>'
              f'{_board("New")}</div>')
    return f'<div class="cm-draft"><div class="cm-scroll">{boards}</div></div>'


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


ITEM_DISPLAY_OVERRIDES = {
    'item_bfury':           'Battle Fury',
    'item_boots':           'Boots of Speed',
    'item_recipe':          'Recipe',
    'item_pers':            'Perseverance',
    'item_lifesteal':       'Morbid Mask',
    'item_buckler':         'Buckler',
    'item_ogre_axe':        'Ogre Axe',
    'item_belt_of_strength':'Belt of Strength',
    'item_band_of_elvenskin':'Band of Elvenskin',
    'item_robe':            'Robe of the Magi',
    'item_diadem':          'Diadem',
    'item_voodoo_mask':     'Voodoo Mask',
    'item_helm_of_the_dominator': 'Helm of the Dominator',
    'item_ultimate_orb':    'Ultimate Orb',
    'item_tiara_of_selemene':'Tiara of Selemene',
    'item_soul_booster':    'Soul Booster',
    'item_kaya':            'Kaya',
    'item_crown':           'Crown',
    'item_yasha':           'Yasha',
    'item_vanguard':        'Vanguard',
    'item_ring_of_health':  'Ring of Health',
    'item_void_stone':      'Void Stone',
    'item_oblivion_staff':  'Oblivion Staff',
    'item_hyperstone':      'Hyperstone',
    'item_blades_of_attack':'Blades of Attack',
    'item_gloves':          'Gloves of Haste',
    'item_quelling_blade':  'Quelling Blade',
    'item_orb_of_venom':    'Orb of Venom',
    'item_blade_of_alacrity':'Blade of Alacrity',
    'item_broadsword':      'Broadsword',
    'item_claymore':        'Claymore',
    'item_cornucopia':      'Cornucopia',
    'item_chainmail':       'Chainmail',
    'item_splintmail':      'Splintmail',
    'item_helm_of_iron_will':'Helm of Iron Will',
    'item_ring_of_basilius':'Ring of Basilius',
    'item_ring_of_regen':   'Ring of Regen',
    'item_wizard_hat':      'Wizard Hat',
    'item_energy_booster':  'Energy Booster',
    'item_point_booster':   'Point Booster',
    'item_vitality_booster':'Vitality Booster',
    'item_shawl':           'Shawl',
    'item_cloak':           'Cloak',
    'item_headdress':       'Headdress',
    'item_fluffy_hat':      'Fluffy Hat',
    'item_talisman_of_evasion':'Talisman of Evasion',
    'item_staff_of_wizardry':'Staff of Wizardry',
    'item_chasm_stone':     'Chasm Stone',
    'item_urn_of_shadows':  'Urn of Shadows',
    'item_veil_of_discord': 'Veil of Discord',
    'item_blink':           'Blink Dagger',
    'item_mask_of_madness': 'Mask of Madness',
    'item_mask_of_death':   'Morbid Mask',
}


def _item_display_name(slug):
    """Convert items.json slug ('item_chainmail' → 'Chainmail',
    'item_bfury' → 'Battle Fury') for use in components rendering."""
    if slug in ITEM_DISPLAY_OVERRIDES:
        return ITEM_DISPLAY_OVERRIDES[slug]
    s = slug[5:] if slug.startswith('item_') else slug
    return s.replace('_', ' ').title()


def _patch_index(version):
    for i, p in enumerate(RELEASE_HISTORY):
        if p['version'] == version:
            return i
    return None


def _prev_patch_version(version):
    """Return the version that came immediately BEFORE `version` (older).
    RELEASE_HISTORY is newest-first, so prev = index + 1."""
    idx = _patch_index(version)
    if idx is None or idx + 1 >= len(RELEASE_HISTORY):
        return None
    return RELEASE_HISTORY[idx + 1]['version']


def _get_recipe(item_display, version):
    """Look up item_recipe_<slug> in items.json for `version`.
    Returns {'components': [(display, cost), ...], 'recipe_cost': int,
    'total': int, 'raw_slugs': [slug, ...]} or None if not present."""
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


def _next_patch_version(version):
    """Return the version that came immediately AFTER `version`, or None."""
    idx = _patch_index(version)
    if idx is None or idx == 0:
        return None
    return RELEASE_HISTORY[idx - 1]['version']


def auto_components_change(item_display, this_version):
    """Auto-derive old → new components_change(...) for `item_display`
    whose recipe changed in patch `this_version`.

    Uses the stats DB: old build from the previous patch, new build from
    this patch. If `this_version`'s items.json still shows the same recipe
    as the previous patch (data lag — muk-as commits sometimes capture the
    state right before the patch propagated), falls back to the next-patch
    data which captures the settled state.
    """
    prev_v = _prev_patch_version(this_version)
    if not prev_v:
        return f'<!-- auto_components_change: no prev for {this_version} -->'
    old = _get_recipe(item_display, prev_v)
    new = _get_recipe(item_display, this_version)
    # Walk forward if 'new' equals 'old' (data lag)
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
    # Multiset diff: components present in new but not in old → added,
    # vice versa → removed. Duplicates are preserved (Battle Fury has two
    # Broadswords; if neither is removed, neither is highlighted).
    leftover_new = [n for n, _ in new['components']]
    leftover_old = [n for n, _ in old['components']]
    for n in list(leftover_new):
        if n in leftover_old:
            leftover_old.remove(n)
            leftover_new.remove(n)
    added = list(dict.fromkeys(leftover_new))
    removed = list(dict.fromkeys(leftover_old))
    # If absolutely nothing changed — components, recipe_cost, total all
    # identical — refuse to emit a visually empty diff. Caller should not
    # use `auto_components_change` here (the recipe change is in a sub-
    # component, not visible at the top level), and should keep the regular
    # text rows.
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


def components_change(old, new, total_old, total_new,
                      recipe_old=None, recipe_new=None,
                      added=None, removed=None):
    """Old → New components panes for items whose recipe changed.

    added:   list of names highlighted with a gold border on the NEW side
             (matches 'Now requires X' / 'Now also requires X').
    removed: list of names highlighted with a faint red border on the OLD side
             (matches 'instead of Y').
    """
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
    """Aghanim's Scepter/Shard upgrade row — full-width light-blue stripe
    with the canonical glyph from `icons/stats/aghs_<kind>_icon.png` prepended.
    Visually matches the existing `ul.changes li.aghanim-scepter/shard` rows
    used elsewhere on the site.

    `kind` is "scepter" (default) or "shard". Returns a full row div
    (`.ability-change-row.aghanim-<kind>`) — pass it as one of the `desc=[…]`
    items in `ability_change(...)`.

    `inline_note_text`: optional clarification rendered as a ↳ inline-note
    inside the same row, below the main text. Use for edge-case semantics
    that explain the upgrade (e.g. "Invisibility is not shared between
    Visage and each familiar")."""
    note = (f'<div class="inline-note">{inline_note_text}</div>'
            if inline_note_text else '')
    return (f'<div class="ability-change-row aghanim-{kind}">'
            f'<span class="aghanim-marker {kind}"></span>{text}{note}</div>')


def aghs_shard_line(text):
    """Convenience alias for `aghs_line(text, kind="shard")`."""
    return aghs_line(text, kind="shard")


def scale_pill(formula_text, fn, levels=None, value_fmt="{:g}",
               level_prefix='L', jump_at=20):
    """Single-formula scaling pill (no old↔new comparison).
    Returns (trigger_html, table_html). Caller embeds `trigger` inline in
    description text where the formula appears; appends `table` after the
    description rows. Use for brand-new abilities whose scaling shouldn't
    be diffed against a previous version."""
    if levels is None:
        levels = list(range(1, 16)) + [20, 25, 30]
    elif isinstance(levels, int):
        levels = list(range(1, levels + 1))
    _formula_id_counter[0] += 1
    fid = f"f{_formula_id_counter[0]}"
    trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'

    def cls_for(L):
        return ' class="lvl-jump"' if L == jump_at else ''

    head_cells = "".join(f'<th{cls_for(L)}>{level_prefix}{L}</th>' for L in levels)
    val_cells  = "".join(f'<td{cls_for(L)}>{value_fmt.format(fn(L))}</td>' for L in levels)
    table = (
        f'<table class="formula-table" id="{fid}" hidden>'
        f'<thead><tr><th></th>{head_cells}</tr></thead>'
        f'<tbody><tr><th class="row-label-new">value</th>{val_cells}</tr></tbody>'
        f'</table>'
    )
    return trigger, table


def ability_change(old, new, summary=None, tag=None):
    """Two-pane ability swap visual (one ability removed, another added) —
    same visual idiom as components_change but for abilities. Each side is
    a dict:
      name     : str
      icon_url : optional explicit URL
      slug     : optional CDN slug (used if icon_url not given)
      innate   : optional bool — if no slug/url, falls back to INNATE_ICON_URL
      desc     : list of strings (HTML allowed); each rendered as one row
      tables   : optional list of table-HTML appended to the body (use
                 scale_pill's `table` return value)

    Optional unified-header mode:
      summary : str — annotation rendered below the unified header title
                (e.g. "New innate ability (now also has its own icon).").
      tag     : "new" or "rework" — badge chip in the header.

    When `summary` or `tag` is provided, switches to a unified layout:
      [icon]  OldName → NewName            [NEW/REWORK]
              "summary text"
      ┌────────────────┬────────────────┐
      │ old desc body  │ new desc body  │   (no per-pane heads)
      └────────────────┴────────────────┘

    The icon comes from `new` (or `old` if `new` has no real icon and
    fallback would just be the generic innate marker). When `old.name ==
    new.name`, the arrow is hidden and only one name is shown."""
    # Dynamics tally: an ability_change block represents a structural
    # event that wouldn't otherwise hit _dyn_record_li (it doesn't emit
    # any li() rows of its own). `tag` arg picks the dominant flavor:
    # 'new' → NEW only, 'rework' → REWORK only, default swap → all
    # three of {new, del, rework} matching the data-tag on the block.
    if tag == 'new':
        _dyn_record_li({'new'})
    elif tag == 'rework':
        _dyn_record_li({'rework'})
    else:
        _dyn_record_li({'new', 'del', 'rework'})
    out = _close_ability_block()
    # Consume the "auto-emit Other header for the first ul after hero_header"
    # flag — ability_change IS the first ability content for this hero, so the
    # next ul belongs to this ability, not to a generic Other group.
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

    # Detect "in-place rework": same name AND same resolved icon URL on both
    # sides. We hide the right pane's header in that case (would be a redundant
    # twin of the left header) — the panes stay equal width via grid, so the
    # description body stays vertically aligned with the left side.
    #
    # IMPORTANT: in_place CSS vertically centers the new pane on the
    # assumption that new is SHORTER than old (small floating card next to
    # tall original). When new has MORE rows than old, centering puts new's
    # first row at the Y-level of old's HEADER (not old's body), producing a
    # visibly off-axis layout. In that case, fall back to the full
    # symmetrical render (both heads shown) so the bodies top-align naturally.
    # old=None → a single-pane "New ability" card: the same block visual
    # (icon + name + NEW badge + summary) but ONLY the new pane, no old/arrow/
    # connector. For genuinely-new abilities that don't replace or rework an
    # existing one (NOT for Aghanim's Shard/Scepter sub-abilities — those stay
    # inline). Neutralise every old-pane reference below.
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
        # When the two sides share identity AND new has more rows than old, the
        # default `is-in-place` CSS (center new pane vertically) puts new's first
        # row at the Y-level of old's HEADER instead of old's body — visibly
        # off-axis. Mark the block with `is-new-taller` so CSS can switch to
        # top-anchored, full-width layout for the new pane while still hiding
        # the duplicate header.
        new_taller_inplace = in_place and (_new_rows > _old_rows)
    # Asymmetric content: whichever side has fewer description rows gets
    # the compact-and-centered treatment so the shorter pane doesn't show
    # a sea of empty space next to the taller one. Skipped in `in_place`
    # (handled by the existing is-in-place layout) and when row counts
    # match.
    # Require a meaningful row-count gap (≥2) before triggering compact
    # mode — a 1-row difference (e.g. 2 vs 3) isn't enough empty space to
    # justify centering one pane and looks odd: the smaller pane appears
    # offset rightward from the subgroup header above.
    unified = (summary is not None) or (tag is not None) or single_new

    if not in_place and not unified and abs(_old_rows - _new_rows) >= 2:
        compact_side = 'old' if _old_rows < _new_rows else 'new'
    else:
        compact_side = None

    def _side(spec, kind):
        name = spec["name"]
        icon_url, used_innate_fallback = _resolve_icon(spec)
        innate_cls = ' is-innate' if spec.get("innate") else ''
        # Innate marker overlay (same visual as `ability()`'s innate badge):
        # only when we have a real ability icon — skip when the main image
        # already IS the innate fallback (would just duplicate the glyph).
        innate_marker = (
            f'<img src="{INNATE_ICON_URL}" alt="" '
            f'class="innate-marker">'
            if spec.get("innate") and not used_innate_fallback else ''
        )
        # If a desc item already starts with a block-level element (`<div`),
        # render it as-is (used by `aghs_line` which provides its own row
        # div with extra classes). Otherwise wrap in a plain row.
        desc_html = ''.join(
            (d if isinstance(d, str) and d.lstrip().startswith('<div')
             else f'<div class="ability-change-row">{d}</div>')
            for d in spec.get("desc", []))
        tables_html = ''.join(
            f'<div class="formula-table-wrap">{tbl}</div>'
            for tbl in (spec.get("tables", []) or [])
        )
        # Unified mode: skip BOTH per-pane heads (names + icon live in the
        # single top-level header above the panes).
        # In-place rework: emit the right pane's head as an invisible
        # placeholder — keeps the layout footprint (~47px) so the new pane's
        # body top-aligns with the old pane's body, but hides the duplicate
        # name/icon visually. CSS `.is-placeholder { visibility: hidden }`.
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

    # Unified-header layout: renders as a regular ability-block (icon, title,
    # one tag+summary row) with the swap panes inside its body. Visually
    # matches how a regular ability (e.g. March of the Machines) is structured
    # — icon in the same place, tag in the same place, title in the same
    # place (with `Old → New` instead of single name).
    if unified:
        # Auto-emit Abilities subgroup before the first ability content
        # for this hero (mirrors the ability() helper).
        _State.next_ul_is_hero_stats = False
        if _State.current_hero and not _State.seen_abilities_subgroup:
            # Override the earlier-emitted subgroup-header (we emitted one at
            # the top of this function for the legacy layout — drop it here
            # because the unified layout owns its own).
            out = ''
            out += '<h4 class="subgroup">Abilities</h4>'
            _State.seen_abilities_subgroup = True
        # Icon: prefer new side's (front). Old side becomes back-layer when
        # icons differ; hover swaps z-index so the old icon flips to front.
        unified_icon = _new_icon
        is_innate = bool(new.get("innate"))
        old_is_innate = (not single_new) and bool(old.get("innate"))
        has_old_underlay = (not single_new) and (_old_icon != _new_icon)
        # Innate marker on the NEW icon — visible by default, hidden on hover
        # when an old underlay exists (so the old icon's own marker takes over).
        # Skip the marker when the icon already IS the generic innate icon
        # (would just stack the same image on itself).
        new_marker_html = (
            f'<img src="{INNATE_ICON_URL}" alt="" '
            f'class="innate-marker innate-marker-new">'
            if is_innate and _new_icon != INNATE_ICON_URL else ''
        )
        # Innate marker on the OLD icon — hidden by default, shown on hover.
        # Only rendered when there's an underlay to swap with AND old is innate
        # AND old has a real icon distinct from the generic innate icon.
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
        # Tag badge: NEW or REWORK row with the summary text.
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
        # Open the ability-block; leave it open so subsequent unrelated
        # content (next W(ability(...)) or W(ul_open()) for outside-the-swap
        # numeric rows) auto-closes it via _close_ability_block().
        _State.ability_block_open = True
        block_cls = 'ability-block ability-change-block'
        if is_innate:
            block_cls += ' is-innate'
        # Visual connector: a thin curve from icon's bottom-center going
        # down then right, landing near the horizontal center of the old
        # pane. Hints that the swap panes are derived from the icon above.
        # Initial `d=""` so nothing renders pre-JS. drawAbilityChangeConnectors()
        # sets the real path after measuring layout — prevents a brief flash of
        # the placeholder curve at load time.
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
            # One pane, full width — no old side, no arrow.
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
        # data-tag="new del rework" — a swap represents simultaneously a
        # removal, an addition, and a structural rework, so all three filters
        # (NEW, DEL, REWORK) should surface the block.
        f'<div class="ability-change{extra_cls}" data-tag="new del rework">'
        f'{_side(old, "old")}'
        f'<span class="ability-change-arrow">→</span>'
        f'{_side(new, "new")}'
        f'</div>'
    )


def plain_header(name, dynamics=True, terrain_link=None):
    """Section / category header with no icon.

    dynamics=False  — suppress the patch-dynamics widget. Use for
                      item-category wrappers like "Basic Items" or
                      "Upgrades" where each contained item already has
                      its own widget, so the category-level dyn-cell row
                      would be redundant noise.

    terrain_link=<base_ver>  — append a gold "View on map" button that jumps to
                      terrain.html with that patch preselected (e.g. "7.41" →
                      ../terrain.html?patch=7.41). Used on the "Terrain Changes"
                      header so the reader can see the moves on the map slider.

    Everything under the big "General Updates" tab (General Changes, Map
    Objectives, Terrain Changes, Captains Mode, …) NEVER shows a dyn-cell row —
    dynamics is forced off there regardless of the argument.
    """
    out = _close_ability_block()
    _State.current_hero = None
    if dynamics:
        eid = _register_entity("plain", name)   # returns '' under General Updates
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
    """Header for a Neutral Enchantment with item-style icon.
    slug: short name (e.g. 'crude'); CDN file = items/enhancement_<slug>.png.
         If None, derived from `name` (lowercased, spaces/hyphens → '_').
    new: same semantics as item_header — True → 'NEW' tag/outline;
         str → custom verbatim label (e.g. 'New Tier 5 Enchantment')."""
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


# ---- Enchantment-by-attribute grid (7.41 Tier-based selection rework) ---------
# Dota in-game attribute colours: str=#e73c06, agi=#3dcb37, int=#00d3e7, uni=#d3e700
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

# Per-enchantment bonuses at each tier as of 7.41 (post-rework, before 7.41a/b/c).
# Each value is a list of stat lines for that specific tier.
_ENCHANT_DESC = {
    "Alert": {
        1: ["+7 Attack Speed"],
        2: ["+15 Attack Speed", "+150 Bonus Night Vision"],
        3: ["+23 Attack Speed", "+225 Bonus Night Vision"],
        4: ["+31 Attack Speed", "+300 Bonus Night Vision", "+100 Attack Range"],
    },
    "Brawny": {
        1: ["+110 Health"],
        2: ["+150 Health", "+3 Health Regen"],
        3: ["+190 Health", "+6 Health Regen"],
        4: ["+230 Health", "+9 Health Regen", "+25% Slow Resistance"],
    },
    "Tough": {
        1: ["+7 Damage"],
        2: ["+10 Damage", "+4 Armor"],
        3: ["+13 Damage", "+6 Armor"],
        4: ["+16 Damage", "+8 Armor", "+40% Knockback Resistance"],
    },
    "Mystical": {
        1: ["+1 Mana Regen"],
        2: ["+1.75 Mana Regen", "+10% Magic Resistance"],
        3: ["+2.5 Mana Regen", "+13% Magic Resistance"],
        4: ["+3.25 Mana Regen", "+16% Magic Resistance", "+15% Mana Cost/Loss Reduction"],
    },
    "Quickened": {
        1: ["+15 Movement Speed"],
        2: ["+20 Movement Speed", "+100 Mana"],
        3: ["+25 Movement Speed", "+160 Mana"],
        4: ["+30 Movement Speed", "+220 Mana", "+15% Evasion"],
    },
    "Vital": {
        1: ["+2 Health Regen"],
    },
    "Greedy": {
        2: ["+75 GPM", "+200 Mana", "−30 Attack Damage"],
        3: ["+100 GPM", "+250 Mana", "−60 Attack Damage"],
    },
    "Crude": {
        2: ["+10% Health Restoration", "+8% BAT Reduction", "−6% Intelligence"],
        3: ["+15% Health Restoration", "+12% BAT Reduction", "−6% Intelligence"],
        4: ["+20% Health Restoration", "+16% BAT Reduction", "−6% Intelligence",
            "Also modifies incoming healing"],
    },
    "Nimble": {
        2: ["+6% Movement Speed", "+10 Damage", "−1.5 Health Regen"],
        3: ["+8% Movement Speed", "+15 Damage", "−2.25 Health Regen"],
        4: ["+10% Movement Speed", "+20 Damage", "−3 Health Regen"],
    },
    "Keen-Eyed": {
        2: ["+125 Cast Range", "+1 Mana Regen", "−10% Max Mana"],
        3: ["+135 Cast Range", "+1.5 Mana Regen", "−12% Max Mana"],
        4: ["+145 Cast Range", "+2 Mana Regen", "−14% Max Mana"],
    },
    "Titanic": {
        2: ["+8% Attack Damage", "+10% Status Resistance", "−10% Attack Speed"],
        3: ["+12% Attack Damage", "+12% Status Resistance", "−12% Attack Speed"],
        4: ["+16% Attack Damage", "+14% Status Resistance", "−14% Attack Speed"],
    },
    "Timeless": {
        4: ["+10% Debuff Amplification", "+8% Spell Amplification"],
        5: ["+15% Debuff Amplification", "+16% Spell Amplification"],
    },
    "Vampiric": {
        5: ["+30% Lifesteal", "+20% Spell Lifesteal", "+300 Bonus Night Vision"],
    },
    "Evolved": {
        5: ["+40 Primary Stat", "(+24 All Attributes for Universal heroes)"],
    },
    "Fleetfooted": {
        5: ["+115 Movement Speed", "Does not stack with boots"],
    },
    "Hulking": {
        5: ["+5% Max Health", "+1.5% Max Health Regen", "−30% Attack Speed"],
    },
    "Audacious": {
        5: ["+100 Attack Speed", "+80 Magic Attack Damage", "+10% Incoming Damage"],
    },
    "Feverish": {
        5: ["+15% Cooldown Reduction", "+7% Mana Cost/Loss Increase"],
    },
    "Manic": {
        5: ["−18% Base Attack Time", "+20% Cast Speed", "−20% Vision"],
    },
}


def _enchant_tooltip(name, tiers):
    """Build a tooltip string for `name` covering one or more tiers."""
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
    """Pill-style chip for one Ringmaster Dark Carnival souvenir — boxed
    icon + name with optional hover tooltip describing what the souvenir
    does. Shares the .enchant-chip pill style (border + background). The
    chip enters a vertical stack via the surrounding `.souvenir-group`
    CSS (flex-direction: column).

    `removed=True` greys the icon and dims the chip so dropped souvenirs
    read as inactive (no strike-through — rejected as visual noise).
    `tooltip` is required for any souvenir without explanatory text right
    beside it (the row's main description doesn't list per-souvenir effects)."""
    icon = f"{ABIL_CDN}{slug}.png"
    cls = "enchant-chip souvenir-chip" + (" removed" if removed else "")
    tip_attr = ''
    if tooltip:
        tip_attr = f' data-tooltip="{_html.escape(tooltip, quote=True)}"'
    return (f'<span class="{cls}"{tip_attr}>'
            f'<img src="{icon}" alt="" loading="lazy">'
            f'<span>{name}</span></span>')


def enchant_attr_row(attr, enchantments, tiers):
    """One row inside an enchant-tier-box.
    attr: 'str' | 'agi' | 'int' | 'uni' | 'all'.
    enchantments: list of display names.
    tiers: int or list of ints — tier scope for chip tooltips."""
    if attr == "all":
        icons = ''.join(
            f'<img src="{_ATTR_ICON[a]}" alt="">' for a in ("str", "agi", "int", "uni")
        )
        label = (f'<span class="enchant-attr-icons all-attrs">{icons}</span>'
                 f'<span class="enchant-attr-name is-all">All Heroes</span>')
    else:
        label = (f'<img class="enchant-attr-ico" src="{_ATTR_ICON[attr]}" alt="">'
                 f'<span class="enchant-attr-name is-{attr}">{_ATTR_LABEL[attr]}</span>')
    label_cls = "enchant-attr-label"
    chips = ''.join(_enchant_chip(e, tiers) for e in enchantments)
    return (f'<div class="enchant-attr-row">'
            f'<div class="{label_cls}">{label}</div>'
            f'<div class="enchant-attr-list">{chips}</div>'
            f'</div>')


def enchant_tier_box(rows, tiers):
    """Bordered grid of attribute → enchantments. `rows` is a list of
    (attr_code, [enchantment_names]) tuples. `tiers` is the tier scope
    (int or list) used for chip tooltips."""
    body = ''.join(enchant_attr_row(a, es, tiers) for a, es in rows)
    return f'<div class="enchant-attr-grid">{body}</div>'


def _section_slug(title):
    """'Hero Updates' → 'heroes', 'Neutral Item Updates' → 'neutral-items', etc."""
    t = re.sub(r'\s+Updates?$', '', title).strip()
    # Pluralise single-word categories for nicer button labels (Hero → Heroes).
    pluralise = {'Hero': 'Heroes', 'Item': 'Items',
                 'Neutral Item': 'Neutral Items', 'Neutral Creep': 'Neutral Creeps'}
    label = pluralise.get(t, t)
    slug = label.lower().replace(' ', '-')
    return slug, label


def section(title):
    _State.current_hero = None
    slug, label = _section_slug(title)
    _State.current_section_slug = slug
    _State.current_sections.append({'slug': slug, 'label': label})
    # Each category is its own panel (cat-panel) so categories visually break
    # apart — the textured background shows in the gaps between them.
    out = _close_block()
    if _State.section_panel_open:
        out += '</section>'
    out += (f'<section class="cat-panel">'
            f'<h2 class="section" data-section="{slug}">{title}</h2>')
    _State.section_panel_open = True
    return out


# Talent icon — Valve's official SVG used in www.dota2.com/patches/.
TALENT_ICON_URL = "../icons/misc/talents.svg"
INNATE_ICON_URL = "../icons/misc/innate_icon.png"
# Visible "?" placeholder shown when an ability/icon URL 404s. NOT a substitute
# for innate_icon — meant to make missing assets traceable so the slug can be
# located and the icon added. Title attribute preserves the failed slug.
MISSING_ICON_URL = "../icons/misc/missing.svg"
# "Other" subgroup icon — neutral inline SVG (three sliders) for stat/misc changes.
OTHER_ICON_URL = "../icons/other.svg"
# Stat-specific icons used when an Other-block has exactly one row — in that
# case the generic "Other" icon is swapped for an icon matching the stat.
# Files live in /icons/ at the repo root; patches reference ../icons/<file>.
STAT_ICONS = {
    "movement_speed":   "../icons/move_speed.png",
    "attack_speed":     "../icons/attack_speed.png",
    "attack_time":      "../icons/attack_time.png",
    "attack_projectile":"../icons/attack_projectile.png",
    "damage":           "../icons/damage.png",
    "armor":            "../icons/armor.png",
    "attack_range":     "../icons/range.png",
    "vision":           "../icons/vision.png",
    "evasion":          "../icons/evasion.png",
    "magic_resist":     "../icons/magic_resist.png",
    "strength":         "../icons/strength.webp",
    "agility":          "../icons/agility.webp",
    "intelligence":     "../icons/intelligence.webp",
    "universal":        "../icons/universal.webp",
}
# Order matters: longer/more-specific keys first to avoid e.g. "damage" matching
# inside "magic damage" before we get a chance to check more specific phrases.
STAT_DETECT_RULES = [
    # Listed most-specific first so e.g. "attack projectile" wins over a
    # bare "attack" prefix and "base attack time" wins over "attack speed".
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

# Innate abilities — marked with INNATE_ICON inside the .ability-block.
# Auto-loaded from data/abilities_slim.json (mirrored from odota/dotaconstants
# build/abilities.json, field is_innate). Refresh by re-running the snippet
# in build_patch.py top-of-file commit message — manual entries only needed
# when an innate isn't yet in dotaconstants.
def _load_innate_slugs():
    p = _os.path.join(_os.path.dirname(__file__), "data", "abilities_slim.json")
    if not _os.path.exists(p):
        return set()
    with open(p, encoding="utf-8") as f:
        d = _json.load(f)
    return {k for k, v in d.items() if v.get("is_innate")}

_INNATE_SLUGS = _load_innate_slugs()

# Display names of every facet (FACETS) and innate ability (abilities_slim) —
# used by li()'s sanity check to flag a stats row that's really a facet/innate
# change miscategorised under "STATS" (e.g. "Rawhide: Bonus Max Health ...").
def _load_facet_innate_names():
    names = {nm for (nm, _color) in FACETS.values()}
    p = _os.path.join(_os.path.dirname(__file__), "data", "abilities_slim.json")
    if _os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for v in _json.load(f).values():
                if isinstance(v, dict) and v.get("is_innate") and v.get("dname"):
                    names.add(v["dname"])
    return names

_FACET_INNATE_NAMES = _load_facet_innate_names()
_FACET_INNATE_PREFIX_RE = re.compile(r"^\s*([A-Z][A-Za-z0-9'’.\- ]+?):\s")

# Manual fallback for innates not yet in dotaconstants (rare).
# Manual innate-overrides for (hero_slug, ability_display_name) pairs whose
# resolved CDN slug doesn't match the engine slug used in abilities_slim.json
# (so the innate auto-detector via _INNATE_SLUGS misses them). Without this
# the ability() helper renders the icon without the bottom-center innate
# marker. Discovered via audit cross-referencing every ability() display
# name against abilities_slim.json's is_innate flag.
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

def subgroup(title):
    """Subgroup heading (e.g., 'Stats', 'Abilities', 'Talents', 'Tier 1').
    For 'Talents', emits subgroup label + opens an .ability-block.talents-block
    so subsequent ul.changes appears next to a large talents icon (like ability blocks)."""
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if title.lower() == "abilities":
        # Manual "Abilities" subgroup — mark flag so auto-emit in ability() doesn't duplicate
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


# Manual ability-name → CDN-slug overrides for cases where naive transform is wrong.
# Key = display name (within hero context); value = CDN slug part (after the hero_internal prefix).
ABILITY_DISPLAY_TO_SLUG = {
    # Anti-Mage
    ("antimage", "Persecutor"): "persectur",
    # Alchemist
    ("alchemist", "Greevil's Greed"): "goblins_greed",
    # Bounty Hunter
    ("bounty_hunter", "Shadow Walk"): "wind_walk",
    # Drow Ranger
    ("drow_ranger", "Gust"): "wave_of_silence",
    # Skywrath Mage
    # Naga Siren
    ("naga_siren", "Deluge"): "deluge",
    # Vengeful Spirit
    ("vengefulspirit", "Vengeance Aura"): "command_aura",
    # Nature's Prophet
    ("furion", "Nature's Call"): "force_of_nature",
    # Outworld Destroyer
    ("obsidian_destroyer", "Sanity's Eclipse"): "sanity_eclipse",
    # Sand King
    ("sand_king", "Stinger"): "scorpion_strike",
    # Pangolier
    ("pangolier", "Roll Up"): "rollup",
    # Phantom Lancer
    ("phantom_lancer", "Phantom Rush"): "phantom_edge",
    # Shadow Fiend
    ("nevermore", "Shadowraze"): "shadowraze1",
    ("nevermore", "Presence of the Dark Lord"): "dark_lord",
    # Sven
    ("sven", "Storm Hammer"): "storm_bolt",
    # Techies
    ("techies", "M.A.D."): "mutually_assured_destruction",
    # Wraith King
    ("skeleton_king", "Wraithfire Blast"): "hellfire_blast",
    # Largo
    # Marci
    ("marci", "Bodyguard"): "bodyguard",
    # Mars
    ("mars", "Spear of Mars"): "spear",
    # Mirana
    ("mirana", "Sacred Arrow"): "arrow",
    # Lone Druid
    ("lone_druid", "Summon Spirit Bear"): "spirit_bear",
    # Clockwerk (rattletrap)
    ("rattletrap", "Cog"): "power_cogs",
    # Tidehunter
    ("tidehunter", "Leviathan's Catch"): "leviathans_catch",
    # Hoodwink
    ("hoodwink", "Hunter's Boomerang"): "hunters_boomerang",
    # Broodmother
    ("broodmother", "Spinner's Snare"): "sticky_snare",
    # Viper
    ("viper", "Nosedive"): "nose_dive",
    # Troll Warlord
    ("troll_warlord", "Whirling Axes (Ranged)"): "whirling_axes_ranged",
    ("troll_warlord", "Whirling Axes (Melee)"): "whirling_axes_melee",
    # Pudge
    # Storm Spirit
    ("storm_spirit", "Galvanized"): "galvanized",
    # Largo — abilities use 'song_<old_name>' internal slugs; display names were renamed.
    ("largo", "Bullbelly Blitz"): "song_fight_song",
    ("largo", "Hotfeet Hustle"): "song_double_time",
    ("largo", "Island Elixir"): "song_good_vibrations",
    # Auto-added by display-name normalization (dotaconstants 2026-05).
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
    # Some heroes use a non-snake_case prefix on ability internal names.
    "sand_king": "sandking",
}

def ability(title, slug=None, innate=None, icon_url=None):
    """Ability heading. Adds an icon when we know the CDN slug.
    The slug is derived from the current hero context + ability title:
      - manual override in ABILITY_DISPLAY_TO_SLUG, OR
      - naive: lowercased + spaces→underscores; strips ', -, ., (, ).
    If innate is None, auto-detects from INNATE_ABILITIES; explicit True/False overrides.
    icon_url overrides the CDN-derived URL entirely (for non-hero abilities like
    neutral creep skills hosted on Liquipedia/wiki CDNs).
    On 404 the ability icon swaps to the generic innate-icon (via onerror)."""
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
        # Explicit slug supplied — still build `key` so the manual
        # INNATE_ABILITIES override can match by (hero, title).
        key = (_State.current_hero, title)
    # Innate detection runs whether the slug was derived or explicit:
    # `is_innate=True/False` from the caller wins; otherwise consult the
    # dotaconstants is_innate set and the manual override map.
    if innate is not None:
        is_innate = bool(innate)
    elif slug:
        is_innate = (slug in _INNATE_SLUGS) or (key is not None and key in INNATE_ABILITIES)
    icon_inner = ''
    skip_marker = False
    # Fallback: if no source for the icon at all, show the missing-placeholder
    # so the row is identifiable rather than text-only.
    if not (icon_url or slug):
        icon_inner = (f'<img src="{MISSING_ICON_URL}" alt="" '
                      f'class="ability-icon-img" loading="lazy" '
                      f'title="missing icon: {title}">')
    # Local icon file is absent (no public CDN icon — typical of the ~28 hero
    # innate abilities). Render the correct fallback DIRECTLY as the src so the
    # heading AND the search index (which reads img.src) get a real, loadable
    # image instead of a broken path that only swaps via onerror. The broken
    # path leaked into search (img.src read before the lazy onerror fired), so
    # e.g. Timbersaw's innate "Exposure Therapy" showed missing.svg there.
    elif slug and not icon_url and slug not in _LOCAL_ABIL_ICONS:
        # Keep the CDN slug queued so fetch_icons can still pick it up if Valve
        # ever publishes the art.
        _State.ability_icons.add(f"{ABIL_CDN}{slug}.png")
        if is_innate:
            # The innate marker IS the canonical image — use it as the icon and
            # skip the redundant separate marker overlay below.
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
        # On 404: innate abilities fall back to the innate icon (Valve doesn't
        # expose innate-ability icons on the public CDN — the innate marker
        # itself IS the canonical image). Everything else falls back to the
        # "missing" placeholder so the absent slug remains traceable.
        if is_innate:
            fallback = INNATE_ICON_URL
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
        # No `title=` on success — the title was previously set unconditionally
        # to "missing icon: <slug>", which the browser then showed on hover
        # even when the icon loaded fine. The `onerror` handler patches the
        # title in only when the load actually fails — but only for NON-innate
        # icons: innate abilities fall back to the generic innate marker by
        # design (Valve doesn't expose innate icons on the public CDN), so the
        # "missing icon" tooltip would be misleading on hover.
        if slug and not is_innate:
            on_err += (f"this.title='missing icon: {slug}';")
        icon_inner = (f'<img src="{src}" alt="{title}" '
                      f'class="ability-icon-img" loading="lazy"{slug_attr} '
                      f'onerror="{on_err}">')
        if not icon_url:
            _State.ability_icons.add(src)
    if is_innate and not skip_marker:
        # Innate marker overlays bottom-center of the ability icon.
        icon_inner += (f'<img src="{INNATE_ICON_URL}" alt="" '
                       f'class="innate-marker">')
    icon_html = f'<div class="ability-icon-wrap">{icon_inner}</div>' if icon_inner else ''

    out = _close_ability_block()
    # Auto-emit 'Abilities' subgroup before the first ability of the current hero.
    _State.next_ul_is_hero_stats = False
    if not _State.seen_abilities_subgroup and _State.current_hero:
        out += '<h4 class="subgroup">Abilities</h4>'
        _State.seen_abilities_subgroup = True
    _State.ability_block_open = True
    return out + (f'<div class="ability-block{" is-innate" if is_innate else ""}">'
                  f'{icon_html}'
                  f'<h4 class="ability-title">{title}</h4>')


def facet_header(slug):
    """Facet heading — same geometry as ability(): 48px square + h4 title.
    The square shows the facet's gradient color (from FACETS / datafeed)
    with the generic facet icon (extracted from pak01_dir.vpk) overlaid
    on top — matches dota2.com's facet pill styling.

    Auto-emits a "Facets" subgroup before the first facet of the current
    hero — parallel to `ability()` auto-emitting "Abilities".
    """
    if slug not in FACETS:
        return f'<!-- facet_header: unknown slug {slug} -->'
    name, color = FACETS[slug]
    # Prefer the datafeed-derived icon (covers all facets); fall back to
    # nothing if unknown (renders as plain color block).
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
        # On 404: fall back to the generic Other icon (e.g. when the stat
        # icon hasn't been added to /icons/ yet); if that ALSO fails, hide.
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

import os
import re

_TALENT_PREFIX_RE = re.compile(r'^(Level \d+ Talent) (?!:)')

def li(text, badge="", extra="", force_tag=None, ability_row=False):
    """Generate <li>. Layout is: [left-tag] [description] [right percentages] [extra].
    The left tag is either:
      - Extracted from `badge` if it contains a text tag (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL)
      - OR derived from data-overall (numeric badges → BUFF or NERF text tag on left)
      - OR an empty placeholder for visual alignment if neither.
    Auto-extracts data-tag from badges for filtering.
    Auto-inserts colon after 'Level N Talent ' prefix to match Valve's notation."""
    if isinstance(text, str):
        text = _TALENT_PREFIX_RE.sub(r'\1: ', text)
        # Sanity check: a row inside the auto-"STATS" group that starts with a
        # known facet/innate name ("Rawhide: ...", "Voidbringer: ...") is almost
        # certainly miscategorised — it belongs in a facet_header() / ability()
        # block, not STATS. Warn at build time so it gets fixed.
        if _State.in_stats_ul:
            _m = _FACET_INNATE_PREFIX_RE.match(text)
            if _m and _m.group(1) in _FACET_INNATE_NAMES:
                print(f"  [warn] '{_m.group(1)}' is a known facet/innate but sits in "
                      f"STATS ({_State.current_hero}) — use facet_header()/ability() instead")
    tags = set()
    # Tags for the dynamics tally: only the row's PRIMARY tag(s). A
    # `t("NEW")` badge carries both data-tag="new" and a filter-shadow
    # data-overall="buff" (so the BUFF filter surfaces NEW rows). Counting
    # both would double-tally each NEW as both new+buff in the dynamics
    # square. data-tag wins when present; data-overall is only a fallback
    # for numeric badges from b() that have no text-tag.
    if force_tag is not None:
        dyn_tags = set(force_tag.split())
    else:
        primary = re.findall(r'data-tag="(\w+)"', badge)
        if primary:
            dyn_tags = set(primary)
        else:
            dyn_tags = set(re.findall(r'data-overall="(\w+)"', badge))
    _dyn_record_li(dyn_tags)
    # Lifespan (items_dyn): stamp the patch where an item/enchant itself is removed
    # so the matrix marks it deleted + blanks every SUBSEQUENT patch. Gated on the
    # DEL tag and matched PRECISELY against the entity-removal phrasings — bare
    # "Removed" (enchants: Wise/Boundless/Vast) or "Item removed from the game"
    # (items: Cornucopia). NOT "Facets removed from the game" (Crude keeps living)
    # nor "Removed <facet/ability>" (a sub-feature, not the entity). setdefault
    # keeps the NEWEST removal (newer patch blocks appear earlier in this file).
    if isinstance(text, str) and 'del' in dyn_tags:
        # Entity removal/pool-exit phrasings (all carry the DEL tag): "Removed"
        # (enchants), "Item removed from the game" (items), "Item cycled out"
        # (neutrals rotated out of the pool). Matched PRECISELY so a descriptive
        # "Removed <facet>" or "Facets removed from the game" can't trigger it.
        # setdefault keeps the NEWEST event (newer patch blocks appear earlier).
        _low = text.strip().rstrip('.').lower()
        if _low in ('removed', 'item removed from the game',
                    'enchantment removed from the game', 'item cycled out'):
            _ek = _State.current_entity_key
            _pv = _State.current_patch_version
            if _ek and _pv:
                _rec = _State.dynamics.get(_ek)
                if _rec is not None and _rec.get('kind') in ('item', 'enchant'):
                    _rec.setdefault('removed_in', _pv)
    # Tags for the li's own data-tag attribute (page-side filtering). Keep
    # the wider set so a NEW row still surfaces under the BUFF filter.
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

    # Extract or derive the LEFT tag
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
    # Auto-classify any line that prominently references Aghanim's Scepter /
    # Shard — covers both "Aghanim's Scepter: ..." starters and phrasings like
    # "No longer upgraded with Aghanim's Shard" / "Aghanim's Scepter upgrade reworked".
    # Exclude info_tip popup text (a list item may mention Aghanim's Scepter
    # without the ROW being an Aghanim change).
    text_noclass = (re.sub(r'<!--TIP-->.*?<!--/TIP-->', '', text, flags=re.S)
                    if isinstance(text, str) else text)
    if isinstance(text, str) and "Aghanim's Scepter" in text_noclass:
        classes.append("aghanim-scepter")
        marker = '<span class="aghanim-marker scepter"></span>'
    elif isinstance(text, str) and "Aghanim's Shard" in text_noclass:
        classes.append("aghanim-shard")
        marker = '<span class="aghanim-marker shard"></span>'
    # Item ability description rows (Passive: / Active: / Toggle: / Aura:)
    # open a soft bordered box. Continuation rows (rows BETWEEN two ability-
    # rows or AFTER the final ability-row in the same ul) are tagged in
    # save_html's post-processor so the box spans the entire description.
    if isinstance(text, str) and re.match(r'^\s*(Passive|Active|Toggle|Aura|Ability)\s*:', text):
        classes.append("ability-row")
        # Bold the leading keyword + colon so 'Passive:' / 'Active:' jumps out.
        text = re.sub(r'^(\s*)(Passive|Active|Toggle|Aura|Ability)(\s*:)',
                      r'\1<b>\2\3</b>', text)
    elif ability_row:
        # Explicit opt-in to the ability-box visual without a "Passive:" prefix
        # (e.g. multi-bullet "what this passive provides" descriptions).
        classes.append("ability-row")
    cls_attr = f' class="{" ".join(classes)}"' if classes else ""
    attr = f' data-tag="{tag_str}"' if tag_str else ""
    # Assemble the trailing cluster — [Aghanim glyph][(i) tip…] — that follows
    # the change text. The (i) tips come from two places:
    #   1. an inline info_tip baked into `text` (e.g. brewling rows), delimited
    #      by <!--TIP-->…<!--/TIP--> — peeled off the end here;
    #   2. inline_note tips lifted out of `extra` (<!--INLINETIP-->…).
    # Order is always [text] [Aghanim glyph] [(i)] — never (i) then glyph.
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
        # Glyph + (i)s kept on one line. Pull the last plain-text word INTO the
        # nowrap tail so [word][Aghanim glyph][(i)] are one unbreakable unit — the
        # (i) can never orphan onto its own (otherwise-empty) wrapped line (which
        # would also show a blank Aghanim stripe).
        cluster = marker + ''.join(trailing_tips)
        _mw = re.search(r'(\S+)\s*$', text_base)
        if _mw and '<' not in _mw.group(1) and '>' not in _mw.group(1):
            text_inner = (text_base[:_mw.start(1)]
                          + f'<span class="li-tail">{_mw.group(1)}{cluster}</span>')
        else:
            text_inner = f'{text_base} <span class="li-tail">{cluster}</span>' 
    else:
        text_inner = f'{text_base}{marker}'
    return f'<li{attr}{cls_attr}>{left_tag}<span class="row-text">{text_inner}</span>{rest}{extra}</li>'


_BULLET_SPLIT = re.compile(r'(?:^|<br>)+\s*\*\s+', re.I)

def subnote(text):
    """Subnote (↳ small grey row). If `text` looks like a bullet list of
    3+ '* item' entries, render it as a collapsible <details>: the optional
    intro line is the summary, the bullets sit inside the closed panel."""
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
    """Descriptive lead-in under a plain_header that FRAMES a category without
    being a tagged change row — no badge, no bullet, no dynamics tally. Use for
    section preambles (e.g. the Invulnerability Targeting summary) where the
    sentence only sets up the per-spell rows below; a change-tag (MISC/etc.)
    would wrongly read as "a miscellaneous change". Emit right after the
    plain_header(), before the first subgroup()/ul_open()."""
    return f'<p class="section-intro">{text}</p>'


def _days_ago(version):
    """Return integer days from today since the patch was released, or None
    if the version is unknown. RELEASE_HISTORY is referenced lazily because
    it's defined further down the file."""
    if not version:
        return None
    date_str = None
    for row in globals().get('RELEASE_HISTORY', []):
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
    """Render a patch version as plain underlined text (NOT a link). These
    only appear inside note_box (i)-popups now, where a link wouldn't be
    clickable anyway — so it's just a solid underline, no anchor."""
    if not version:
        return ''
    return f'<span class="patch-ref"><b>{version}</b></span>'


def _format_age(days):
    """Render an age-in-days as a human-friendly phrase.

    < 365 days  → "N days ago"
    >= 365 days → "Y years M months ago" (months omitted when zero,
                  singular forms used at 1)."""
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
    """Pretty-print a numeric stat value: drop .0 on integers."""
    if v is None:
        return "?"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def note_box(text=None, *, hero=None, item=None, unit=None, field=None, before_patch=None,
             prev_val=None, prev_patch=None, new_val=None, extra_note=None):
    """Inline NOTE (i)-popup rendered after a row.

    Usage modes:
      - Legacy free-form:  note_box("any text")  → "Note:" popup.
      - Auto-derived from stats DB: provide hero=/item=/unit= + field= +
        before_patch= → "Now it's <b>X</b>. … changed in <b>PATCH</b>", where X
        is the value AFTER this patch's change (current patch version).
        `unit` takes the full npc key, e.g. 'npc_dota_beastmaster_boar'.
      - Manual override: pass prev_val= + prev_patch= (and new_val= for the
        post-patch value). Use when the value isn't in the parsed DB — e.g. a
        summon whose stat lives on an un-parsed base unit (Spirit Bear's regen
        inherits from npc_dota_lone_druid_bear, so units.json carries None).
    """
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
    # Show the value AFTER this patch's change ("Now it's X"); fall back to the
    # pre-patch value only if the new value couldn't be resolved.
    show_val = new_val if new_val is not None else prev_val
    if show_val is not None and prev_patch is not None:
        if isinstance(prev_patch, str) and prev_patch.startswith("<"):
            ver = prev_patch[1:]
            # The stat held its value for every patch we have on record (DB
            # starts at the oldest version listed in `versions`). Whether it
            # ever changed before that is unknown — phrase the note to claim
            # only what's verifiable.
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
    """Convenience: emit <li> with formula table.

    prefix:        text BEFORE 'from' (e.g. 'Max Damage Increase decreased')
    old_formula:   human-readable old-formula string
    new_formula:   human-readable new-formula string
    old_fn/new_fn: callable(level) → value, used to compute per-level table
    l:             lower-is-buff flag (passed through to bf gradient)
    rework_badge:  if True (default), prepend a REWORK text-tag to the badge group
    **bf_kwargs:   forwarded to bf() (e.g. levels, level_prefix, jump_at, value_fmt)
    """
    trigger, badge, table = bf(old_fn, new_fn, new_formula, l=l, **bf_kwargs)
    full_text = (f'{prefix} from <span class="formula-old">{old_formula}</span> '
                 f'to {trigger}')
    # Left tag picks the overall direction by default — REWORK is reserved
    # for the rare case where the overall avg is genuinely neutral. The
    # row classifies itself as BUFF / NERF when the per-level deltas
    # average to a clear direction (avg_signed sign embedded in
    # data-overall by bf()).
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
        # Reformulation with no effective change (Valve "Effective values are
        # not changed" subnote) — semantically neutral, render as MISC, not
        # REWORK. Matches the global-changes row tag for the 7.41
        # "per level up" → "per level" rename.
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


# ---------- CSS ----------

CSS = (_os.path.join(_os.path.dirname(__file__), "styles.css"))
with open(CSS, encoding="utf-8") as _f:
    CSS = _f.read()

# Cache-busting query for styles.css / scripts.js — computed in the shared
# site_common module so build_patch.py and build_creeps.py agree on it.
import site_common as _site
_ASSET_VERSION = _site.compute_asset_version()

# ---------- CONTENT ----------

H = []
def W(s): H.append(s)


# ============================================================
# MULTI-PATCH SUPPORT
# ============================================================

PATCHES = [
    {"version": "7.41d", "date": "04.06.2026", "filename": "patches/7.41d.html"},
    {"version": "7.41c", "date": "06.05.2026", "filename": "patches/7.41c.html"},
    {"version": "7.41b", "date": "07.04.2026", "filename": "patches/7.41b.html"},
    {"version": "7.41a", "date": "28.03.2026", "filename": "patches/7.41a.html"},
    {"version": "7.41",  "date": "24.03.2026", "filename": "patches/7.41.html"},
    {"version": "7.40c", "date": "21.01.2026", "filename": "patches/7.40c.html"},
    {"version": "7.40b", "date": "23.12.2025", "filename": "patches/7.40b.html"},
    {"version": "7.40",  "date": "15.12.2025", "filename": "patches/7.40.html"},
    {"version": "7.08",  "date": "01.02.2018", "filename": "patches/7.08.html"},
]

# Includes patches without HTML (e.g. 7.41a) — used only for "days between" math.
# Major-patch dates from odota/dotaconstants. Sub-patches sourced from Liquipedia
# and Fandom. Append new entries here when patches release; sorted internally.
RELEASE_HISTORY = [
    # 7.41 cycle
    {"version": "7.41d", "date": "04.06.2026"},
    {"version": "7.41c", "date": "06.05.2026"},
    {"version": "7.41b", "date": "07.04.2026"},
    {"version": "7.41a", "date": "28.03.2026"},
    {"version": "7.41",  "date": "24.03.2026"},
    # 7.40 cycle
    {"version": "7.40c", "date": "21.01.2026"},
    {"version": "7.40b", "date": "23.12.2025"},
    {"version": "7.40",  "date": "15.12.2025"},
    # 7.39 cycle
    {"version": "7.39e", "date": "02.10.2025"},
    {"version": "7.39d", "date": "05.08.2025"},
    {"version": "7.39c", "date": "24.06.2025"},
    {"version": "7.39b", "date": "29.05.2025"},
    {"version": "7.39",  "date": "21.05.2025"},
    # 7.38 cycle
    {"version": "7.38c", "date": "27.03.2025"},
    {"version": "7.38b", "date": "05.03.2025"},
    {"version": "7.38",  "date": "19.02.2025"},
    # 7.37 cycle
    {"version": "7.37e", "date": "19.11.2024"},
    {"version": "7.37d", "date": "01.10.2024"},
    {"version": "7.37c", "date": "28.08.2024"},
    {"version": "7.37b", "date": "14.08.2024"},
    {"version": "7.37",  "date": "31.07.2024"},
    # 7.36 cycle
    {"version": "7.36c", "date": "24.06.2024"},
    {"version": "7.36b", "date": "05.06.2024"},
    {"version": "7.36a", "date": "26.05.2024"},
    {"version": "7.36",  "date": "22.05.2024"},
    # 7.35 cycle
    {"version": "7.35d", "date": "21.03.2024"},
    {"version": "7.35c", "date": "21.02.2024"},
    {"version": "7.35b", "date": "21.12.2023"},
    {"version": "7.35",  "date": "14.12.2023"},
    # 7.34 cycle
    {"version": "7.34e", "date": "20.11.2023"},
    {"version": "7.34d", "date": "05.10.2023"},
    {"version": "7.34c", "date": "08.09.2023"},
    {"version": "7.34b", "date": "14.08.2023"},
    {"version": "7.34",  "date": "08.08.2023"},
    # 7.33 cycle
    {"version": "7.33e", "date": "13.07.2023"},
    {"version": "7.33d", "date": "15.06.2023"},
    {"version": "7.33c", "date": "13.05.2023"},
    {"version": "7.33b", "date": "25.04.2023"},
    {"version": "7.33",  "date": "20.04.2023"},
    # 7.32 cycle
    {"version": "7.32e", "date": "07.03.2023"},
    {"version": "7.32d", "date": "29.11.2022"},
    {"version": "7.32c", "date": "27.09.2022"},
    {"version": "7.32b", "date": "30.08.2022"},
    {"version": "7.32",  "date": "24.08.2022"},
    # 7.31 cycle
    {"version": "7.31d", "date": "08.06.2022"},
    {"version": "7.31c", "date": "04.05.2022"},
    {"version": "7.31b", "date": "28.02.2022"},
    {"version": "7.31",  "date": "23.02.2022"},
    # 7.30 cycle
    {"version": "7.30e", "date": "28.10.2021"},
    {"version": "7.30d", "date": "25.09.2021"},
    {"version": "7.30c", "date": "11.09.2021"},
    {"version": "7.30b", "date": "23.08.2021"},
    {"version": "7.30",  "date": "18.08.2021"},
    # 7.29 cycle
    {"version": "7.29d", "date": "24.05.2021"},
    {"version": "7.29c", "date": "29.04.2021"},
    {"version": "7.29b", "date": "16.04.2021"},
    {"version": "7.29",  "date": "09.04.2021"},
    # 7.28 cycle
    {"version": "7.28c", "date": "19.02.2021"},
    {"version": "7.28b", "date": "10.01.2021"},
    {"version": "7.28a", "date": "22.12.2020"},
    {"version": "7.28",  "date": "17.12.2020"},
    # 7.27 cycle
    {"version": "7.27d", "date": "26.08.2020"},
    {"version": "7.27c", "date": "17.07.2020"},
    {"version": "7.27b", "date": "15.07.2020"},
    {"version": "7.27a", "date": "04.07.2020"},
    {"version": "7.27",  "date": "28.06.2020"},
    # 7.26 cycle
    {"version": "7.26c", "date": "02.05.2020"},
    {"version": "7.26b", "date": "28.04.2020"},
    {"version": "7.26a", "date": "21.04.2020"},
    {"version": "7.26",  "date": "17.04.2020"},
    # 7.25 cycle
    {"version": "7.25c", "date": "06.04.2020"},
    {"version": "7.25b", "date": "25.03.2020"},
    {"version": "7.25a", "date": "18.03.2020"},
    {"version": "7.25",  "date": "17.03.2020"},
    # 7.24 cycle
    {"version": "7.24b", "date": "26.02.2020"},
    {"version": "7.24",  "date": "26.01.2020"},
    # 7.23 cycle
    {"version": "7.23f", "date": "07.01.2020"},
    {"version": "7.23e", "date": "14.12.2019"},
    {"version": "7.23d", "date": "11.12.2019"},
    {"version": "7.23c", "date": "06.12.2019"},
    {"version": "7.23b", "date": "29.11.2019"},
    {"version": "7.23a", "date": "27.11.2019"},
    {"version": "7.23",  "date": "26.11.2019"},
    # 7.22 cycle
    {"version": "7.22h", "date": "29.09.2019"},
    {"version": "7.22g", "date": "06.09.2019"},
    {"version": "7.22f", "date": "28.07.2019"},
    {"version": "7.22e", "date": "14.07.2019"},
    {"version": "7.22d", "date": "30.06.2019"},
    {"version": "7.22c", "date": "09.06.2019"},
    {"version": "7.22b", "date": "27.05.2019"},
    {"version": "7.22",  "date": "24.05.2019"},
    # 7.21 cycle
    {"version": "7.21d", "date": "24.03.2019"},
    {"version": "7.21c", "date": "02.03.2019"},
    {"version": "7.21b", "date": "16.02.2019"},
    {"version": "7.21",  "date": "29.01.2019"},
    # 7.20 cycle
    {"version": "7.20e", "date": "09.12.2018"},
    {"version": "7.20d", "date": "30.11.2018"},
    {"version": "7.20c", "date": "24.11.2018"},
    {"version": "7.20b", "date": "20.11.2018"},
    {"version": "7.20",  "date": "19.11.2018"},
    # 7.19 cycle
    {"version": "7.19d", "date": "12.10.2018"},
    {"version": "7.19c", "date": "14.09.2018"},
    {"version": "7.19b", "date": "01.09.2018"},
    {"version": "7.19",  "date": "29.07.2018"},
    # 7.08-7.18 (Spring Cleaning era)
    {"version": "7.18",  "date": "25.06.2018"},
    {"version": "7.17",  "date": "10.06.2018"},
    {"version": "7.16",  "date": "27.05.2018"},
    {"version": "7.15",  "date": "10.05.2018"},
    {"version": "7.14",  "date": "26.04.2018"},
    {"version": "7.13b", "date": "13.04.2018"},
    {"version": "7.13",  "date": "12.04.2018"},
    {"version": "7.12",  "date": "29.03.2018"},
    {"version": "7.11",  "date": "15.03.2018"},
    {"version": "7.10",  "date": "01.03.2018"},
    {"version": "7.09",  "date": "15.02.2018"},
    {"version": "7.08",  "date": "01.02.2018"},
]


def _parse_date(dmy):
    """'06.05.2026' → date(2026, 5, 6)."""
    from datetime import date as _D
    d, m, y = dmy.split('.')
    return _D(int(y), int(m), int(d))


def _patch_meta_parts(version):
    """Return (prev_part, age_part) — two short labelled strings used by the
    toolbar patch-info row.

    prev_part  →  "+29 days after 7.41b"   (empty if no previous patch)
    age_part   →  "Live 25 days"  on the newest patch,
                  "Ran 29 days"   on every older one.
    """
    from datetime import date as _D
    today = _D.today()
    sorted_releases = sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    for i, p in enumerate(sorted_releases):
        if p["version"] != version:
            continue
        cur_date = _parse_date(p["date"])
        prev_part = ""
        if i > 0:
            prev = sorted_releases[i - 1]
            n = (cur_date - _parse_date(prev["date"])).days
            prev_part = f'<b>{n}</b> days after <b>{prev["version"]}</b>'
        if i < len(sorted_releases) - 1:
            nxt = sorted_releases[i + 1]
            n = (_parse_date(nxt["date"]) - cur_date).days
            age_part = f'Ran: <b>{n}</b> days'
        else:
            n = (today - cur_date).days
            unit = "day" if n == 1 else "days"
            age_part = (f'Live: <b>{n}</b> {unit}' if n > 0
                        else 'Released today')
        return prev_part, age_part
    return "", ""


def _patch_age_line(version):
    """Build the small subtitle under the release date.

    For latest patch:   "29 days after 7.41b · running for 2 days"
    For older patches:  "10 days after 7.41a · ran for 29 days"
    Returns empty string if previous patch unknown.
    """
    from datetime import date as _D
    today = _D.today()
    sorted_releases = sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))
    for i, p in enumerate(sorted_releases):
        if p["version"] != version:
            continue
        cur_date = _parse_date(p["date"])
        prev_part = ""
        if i > 0:
            prev = sorted_releases[i - 1]
            n = (cur_date - _parse_date(prev["date"])).days
            prev_part = f"{n} days after {prev['version']}"
        if i < len(sorted_releases) - 1:
            nxt = sorted_releases[i + 1]
            n = (_parse_date(nxt["date"]) - cur_date).days
            tail = f"ran for {n} days"
        else:
            n = (today - cur_date).days
            unit = "day" if n == 1 else "days"
            tail = f"running for {n} {unit}" if n > 0 else "released today"
        return f"{prev_part} · {tail}" if prev_part else tail
    return ""


def _dropdown_options_html(current_version, patch_context=False):
    """Render menu items list for the version dropdown.
    patch_context=True when rendered inside a patch page (patches/ folder) —
    links use plain 'version.html' (same directory) instead of root-relative paths."""
    items = []
    for p in PATCHES:
        cls = "version-item current" if p["version"] == current_version else "version-item"
        if p["version"] == current_version:
            href = "#"
        elif patch_context:
            href = p["version"] + ".html"
        else:
            href = p["filename"]
        items.append(
            f'<a class="{cls}" href="{href}">'
            f'<span class="vi-name">{p["version"]}</span>'
            f'<span class="vi-date">{p["date"]}</span>'
            f'</a>'
        )
    return "".join(items)


def _render_top_nav(active="changelogs", current_version=None, date=None, patch_context=False, centre_tabs=True):
    """Render the top nav by delegating to site_common.render_top_nav. This
    wrapper builds the patch-page version picker (prev/next arrows + version
    dropdown + release-info) and passes it as picker_html; the shared module
    owns the tab list and the flat-tab placeholder."""
    latest_href = (PATCHES[0]['version'] + ".html" if patch_context
                   else PATCHES[0]['filename']) if PATCHES else "#"

    picker_html = None
    show_picker = (active == "changelogs"
                   and current_version is not None and date is not None)
    if show_picker:
        age_line = _patch_age_line(current_version)
        age_html = f'<span class="patch-age">{age_line}</span>' if age_line else ''
        options = _dropdown_options_html(current_version, patch_context=patch_context)
        # Prev/Next arrows flanking the version button — let the user
        # walk one step backward / forward through the patch list
        # without opening the dropdown. PATCHES is sorted newest-first,
        # so older = idx+1 (left arrow) and newer = idx-1 (right arrow).
        idx = next((i for i, p in enumerate(PATCHES) if p["version"] == current_version), None)
        older = PATCHES[idx + 1] if idx is not None and idx + 1 < len(PATCHES) else None
        newer = PATCHES[idx - 1] if idx is not None and idx - 1 >= 0 else None

        def _nav_arrow(target, direction):
            # Direction-modifier class drives the clip-path arrow shape
            # in CSS. The element renders without any text glyph — the
            # block itself is the arrow.
            dir_cls = 'is-prev' if direction == 'Older' else 'is-next'
            if target:
                return (f'<a class="version-nav-arrow {dir_cls}" '
                        f'href="{target["filename"].split("/")[-1]}" '
                        f'title="{direction}: {target["version"]} ({target["date"]})" '
                        f'aria-label="{direction} patch: {target["version"]}"></a>')
            return (f'<span class="version-nav-arrow {dir_cls} is-disabled" '
                    f'aria-hidden="true"></span>')

        prev_arrow = _nav_arrow(older, "Older")
        next_arrow = _nav_arrow(newer, "Newer")

        # Patch info (date + age) was previously in this header block — it has
        # moved to the .toolbar below so the header stays compact. Only the
        # arrows + version dropdown remain on the right.
        picker_html = f'''
    <div class="nav-context nav-context-picker">
      <div class="version-picker">
        {prev_arrow}
        <div class="version-dropdown">
          <button class="version" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Select patch version">
            {current_version} <span class="version-chev">▾</span>
          </button>
          <div class="version-menu" role="menu">
            {options}
          </div>
        </div>
        {next_arrow}
      </div>
    </div>'''

    return _site.render_top_nav(active, latest_href,
                                patch_context=patch_context,
                                picker_html=picker_html,
                                centre_tabs=centre_tabs)


def write_head(version, date):
    """Render head + top nav (Changelogs+Calendar tabs + version) + container + toolbar."""
    _State.current_patch_version = version
    _State.current_entity_key = None
    _State.current_section_slug = None
    nav = _render_top_nav(active="changelogs", current_version=version, date=date, patch_context=True)
    # Patch info block in the toolbar — three discrete labelled facts on a
    # single right-aligned row: release date, gap from the previous patch,
    # how long this version has been live (or how long it ran). Plain text,
    # no pill / no border.
    prev_part, age_part = _patch_meta_parts(version)
    parts = [f'<span class="ti-released">Released: <b>{date}</b></span>']
    if prev_part:
        parts.append(f'<span class="ti-after">{prev_part}</span>')
    if age_part:
        parts.append(f'<span class="ti-live">{age_part}</span>')
    patch_info_html = (
        '<div class="toolbar-patch-info">' + ''.join(parts) + '</div>'
    )
    W(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SIKLE | Changelogs {version}</title>
{_site.favicon_links(prefix="../")}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">
<link rel="stylesheet" href="../styles.css?v={_ASSET_VERSION}">
</head>
<body class="patch-page">

{nav}
<a class="nav-back-arrow" href="../calendar.html" aria-label="Back to calendar" title="Back to calendar"></a>
<div class="toolbar">
  <div class="toolbar-inner">
    <div class="legend-stack">
      <div class="legend-tags">
        <strong>Tags:</strong>
        <button class="badge buff-text filter-btn" data-filter="buff">BUFF</button>
        <button class="badge nerf-text filter-btn" data-filter="nerf">NERF</button>
        <button class="badge new filter-btn" data-filter="new">NEW</button>
        <button class="badge del filter-btn" data-filter="del">DEL</button>
        <button class="badge rework filter-btn" data-filter="rework">REWORK</button>
        <button class="badge misc filter-btn" data-filter="misc">MISC</button>
        <button class="badge qol filter-btn" data-filter="qol">QoL</button>
      </div>
      <div class="legend-categories"><!--CATEGORIES_BAR--></div>
    </div>
    <div class="search-box">
      <input type="text" id="entity-search" placeholder="Search heroes, items, abilities…" autocomplete="off" spellcheck="false">
      <div class="search-results" id="search-results"></div>
    </div>
    {patch_info_html}
  </div>
</div>
<div class="container">
''')


JS_TEXT = (_os.path.join(_os.path.dirname(__file__), "scripts.js"))
with open(JS_TEXT, encoding="utf-8") as _f:
    JS_TEXT = _f.read()

def write_footer():
    """Render close-block + back-to-top button + script tag + closing tags."""
    W(_close_block())
    if _State.section_panel_open:
        W('</section>')
        _State.section_panel_open = False
    W('<button class="back-to-top" aria-label="Back to top" title="Back to top" onclick="window.scrollTo({top:0, behavior:\'smooth\'})"></button>')
    W(f'<script src="../scripts.js?v={_ASSET_VERSION}"></script>')
    W('</div></body></html>')


def save_assets():
    """No-op kept for backward compatibility.
    styles.css and scripts.js are source files (read at module load),
    not generated artefacts. Nothing to write."""
    pass


_LI_RE = re.compile(r'<li\b([^>]*)>(.*?)</li>', re.S)
_UL_CHANGES_RE = re.compile(r'(<ul class="changes">)(.*?)(</ul>)', re.S)
def _wrap_ability_boxes(html):
    """For each <ul class="changes">, walk its <li> sequence and assign:
      - ability-row-start  : first li of an ability description
      - ability-row-cont   : continuation li (no Passive/Active keyword) that
                              still belongs to the previous ability
      - ability-row-end    : last li of an ability description (start+end on
                              the same li if the box is one row only)
    The CSS uses these classes to draw a soft box that spans the whole group.
    """
    def fix_ul(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        parts = []
        last_idx = 0
        items = list(_LI_RE.finditer(body))
        if not items:
            return m.group(0)

        # First pass: classify each li as "starter" (has ability-row class)
        # or "continuation" while inside a box.
        is_starter = []
        for it in items:
            is_starter.append(' ability-row' in it.group(1) or 'class="ability-row' in it.group(1))

        # Determine grouping: a starter opens a box; following non-starters
        # until next starter (or end of ul) are continuations.
        # Each li gets one of: 'start', 'cont', 'end', 'solo', or None.
        roles = [None] * len(items)
        in_box = False
        box_start_idx = None
        for i, st in enumerate(is_starter):
            if st:
                # close previous box if any
                if in_box:
                    roles[i - 1] = 'cont-end' if roles[i - 1] == 'cont' else (
                        'solo' if box_start_idx == i - 1 else 'cont-end')
                roles[i] = 'start'
                in_box = True
                box_start_idx = i
            elif in_box:
                roles[i] = 'cont'
        if in_box:
            last = len(items) - 1
            if roles[last] == 'start':
                roles[last] = 'solo'
            else:
                roles[last] = 'cont-end'

        # Rebuild body with augmented classes on each <li>
        def aug_class(li_match, extra):
            attrs = li_match.group(1)
            if 'class="' in attrs:
                attrs = re.sub(r'class="([^"]*)"', lambda mm: f'class="{mm.group(1)} {extra}"', attrs)
            else:
                attrs = ' class="' + extra + '"' + attrs
            return f'<li{attrs}>{li_match.group(2)}</li>'

        out_lis = []
        for it, role in zip(items, roles):
            if role is None:
                out_lis.append(it.group(0))
            elif role == 'solo':
                out_lis.append(aug_class(it, 'ability-row-solo'))
            elif role == 'start':
                out_lis.append(aug_class(it, 'ability-row-start'))
            elif role == 'cont':
                out_lis.append(aug_class(it, 'ability-row-cont'))
            elif role == 'cont-end':
                out_lis.append(aug_class(it, 'ability-row-cont ability-row-end'))

        # Reassemble: prefix (everything in body before first li) +
        # interleaved lis + suffix (text after last li)
        body_out = body[:items[0].start()]
        for i, it in enumerate(items):
            body_out += out_lis[i]
            if i + 1 < len(items):
                body_out += body[it.end():items[i + 1].start()]
        body_out += body[items[-1].end():]
        return head + body_out + tail

    return _UL_CHANGES_RE.sub(fix_ul, html)


_OTHER_BLOCK_RE = re.compile(
    r'(<div class="ability-block other-block">.*?<img\b[^>]*?\bsrc=")([^"]+)(".*?<ul class="changes">)(.*?)(</ul>)',
    re.S
)
_STAT_DETECT_SKIP_PHRASES = (
    # Cosmetic / informational rows that mention an attribute name but aren't
    # actually a stat change — the generic Other icon stays so the icon doesn't
    # mislead the reader into thinking the row is a Strength/Agility/etc. change.
    "model size",
    "hero size",
)


def _swap_single_row_other_icons(html):
    """For each .other-block containing exactly one <li>, swap the generic
    'Other' icon for a stat-specific one matched against the row's text.

    Rows whose text matches a phrase in _STAT_DETECT_SKIP_PHRASES keep the
    neutral icon — they mention a stat name without being a stat change."""
    def repl(m):
        head, src, mid, ul_inner, ul_close = m.groups()
        if len(re.findall(r'<li\b', ul_inner)) != 1:
            return m.group(0)
        text = re.sub(r'<[^>]+>', ' ', ul_inner).lower()
        if any(skip in text for skip in _STAT_DETECT_SKIP_PHRASES):
            return m.group(0)
        for key, phrases in STAT_DETECT_RULES:
            if any(p in text for p in phrases):
                return head + STAT_ICONS.get(key, src) + mid + ul_inner + ul_close
        return m.group(0)
    return _OTHER_BLOCK_RE.sub(repl, html)


_CHANGES_UL_RE = re.compile(r'(<ul class="changes"[^>]*>)(.*?)(</ul>)', re.DOTALL)


def _split_top_li(content):
    """Walk `content` and yield (prefix, [li_html, ...], suffix). Tracks depth
    so nested <li> inside an inline-note's collapsible details, subnote ul,
    etc. don't get treated as siblings."""
    items, pos = [], 0
    first_start = content.find('<li')
    prefix = content[:first_start] if first_start != -1 else content
    if first_start == -1:
        return prefix, [], ''
    pos = first_start
    while True:
        start = content.find('<li', pos)
        if start == -1:
            break
        gt = content.find('>', start)
        if gt == -1:
            break
        depth, scan = 1, gt + 1
        while depth > 0 and scan < len(content):
            nxt_open = content.find('<li', scan)
            nxt_close = content.find('</li>', scan)
            if nxt_close == -1:
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                gt2 = content.find('>', nxt_open)
                if gt2 == -1:
                    break
                depth += 1
                scan = gt2 + 1
            else:
                depth -= 1
                scan = nxt_close + 5
        items.append(content[start:scan])
        pos = scan
    suffix = content[pos:]
    return prefix, items, suffix


def _li_rank(li_html):
    """Rank an <li> for tag-order sorting (lower = comes first):
       1 NEW
       2 REWORK
       3 BUFF  (numeric badge with overall=buff, or textual t("BUFF"))
       4 NERF  (numeric badge with overall=nerf, or textual t("NERF"))
       5 DEL
       6 QoL   (quality-of-life convenience — grouped before the MISC catch-all)
       7 MISC
       8 untagged (kept at end so they don't displace tagged rows).

    QoL and MISC have DISTINCT ranks so QoL rows group together instead of
    interleaving with MISC (a stable sort can't separate equal ranks).

    Classification reads the LEFT-TAG span's class — that's the only reliable
    signal because data-tag stores both the visible kind AND the filter alias
    (NEW carries data-tag='buff new', DEL carries 'del nerf'). For numeric
    rows the left-tag is synthesized in li() based on data-overall, so
    'buff-text' / 'nerf-text' covers both textual and numeric BUFF/NERF."""
    m = re.search(r'<span class="badge (buff-text|nerf-text|rework|misc|qol|new|del)"', li_html)
    if m:
        kind = m.group(1)
        return {
            'new': 1, 'rework': 2,
            'buff-text': 3, 'nerf-text': 4,
            'del': 5,
            'qol': 6, 'misc': 7,
        }[kind]
    # No explicit left text-tag — numeric-only rows always synthesize a
    # BUFF/NERF left-tag in li() based on data-overall, so the above regex
    # catches them. Reaching here means the row is untagged (ability
    # description, structural intro, etc.) → keep at the bottom.
    if 'class="badge-group"' in li_html:
        # Safety net for any badge-group row that escaped the left-tag
        # synth path — fall into BUFF rank as a neutral default.
        return 3
    return 8


def _sort_changes_li(html):
    """Enforce the canonical row order inside every <ul class="changes"> block:
       NEW → REWORK → BUFF → NERF → DEL → QoL → MISC → untagged.
    Stable sort preserves the patch-note ordering within each rank. Applies
    PER-ABILITY (each `<ul class="changes">` belongs to one ability/hero
    block via the surrounding ability()/hero_header() emitter).

    Skipped when the block contains item-description (.ability-row) rows —
    those have an authored visual sequence (Passive:/Active:/Aura: + their
    bullets) that the sort must not disrupt."""
    def repl(m):
        open_tag, inner, close_tag = m.groups()
        prefix, lis, suffix = _split_top_li(inner)
        if not lis:
            return m.group(0)
        if any('class="ability-row"' in li or 'class="ability-row ' in li
               or ' ability-row"' in li or ' ability-row ' in li for li in lis):
            return m.group(0)
        # Stable sort: Python's sorted is stable, so equal ranks keep order.
        ranked = sorted(enumerate(lis), key=lambda iv: (_li_rank(iv[1]), iv[0]))
        ordered = [li for _, li in ranked]
        return open_tag + prefix + ''.join(ordered) + suffix + close_tag
    return _CHANGES_UL_RE.sub(repl, html)


def _categories_bar_html():
    """Render the Categories filter buttons for the currently-accumulated patch."""
    if not _State.current_sections:
        return ''
    btns = []
    for s in _State.current_sections:
        btns.append(
            f'<button class="badge cat-filter-btn" data-category="{s["slug"]}">'
            f'{s["label"]}</button>'
        )
    return '<strong>Group:</strong>' + ''.join(btns)


def save_html(filename):
    """Write current accumulator to ./{filename} and reset state."""
    out = "\n".join(H)
    out = out.replace('<!--CATEGORIES_BAR-->', _categories_bar_html())
    out = _swap_single_row_other_icons(out)
    out = _sort_changes_li(out)
    out = _wrap_ability_boxes(out)
    # Safety net: any inline_note (i)-tip sentinel that wasn't lifted into a
    # row by li() (e.g. used outside an `extra=`) ships without its markers —
    # the (i) bubble still renders in place; only the comments are stripped.
    out = out.replace('<!--INLINETIP-->', '').replace('<!--/INLINETIP-->', '')
    out = out.replace('<!--TIP-->', '').replace('<!--/TIP-->', '')
    # Perf: let the browser decode images off the main thread (smoother render
    # on icon-heavy pages — 600+ icons). Safe + universal; no visual change.
    out = out.replace('<img ', '<img decoding="async" ')
    path = filename
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  → {filename}: {len(out):,} bytes")
    H.clear()
    _State.block_open = False
    _State.current_sections = []
    _State.current_entity_key = None


# Pre-computed KV-entry counts per patch (from patchnotes_english.txt analysis).
# Used in calendar to highlight "extra-major" patches that contain >= 500 entries.
# When patches release, these counts get updated. Missing keys default to 0.
PATCH_ENTRY_COUNTS = {
    "7.08":   140, "7.09":    14, "7.10":    66, "7.11":    44, "7.12":    77,
    "7.13":    52, "7.13b":    8, "7.14":    65, "7.15":    33, "7.16":    74,
    "7.17":    32, "7.18":    33, "7.19":   122, "7.19b":   42, "7.19c":   38,
    "7.19d":   40, "7.20":   428, "7.20b":   77, "7.20c":  104, "7.20d":   45,
    "7.20e":   75, "7.21":   245, "7.21b":  124, "7.21c":   68, "7.21d":   65,
    "7.22":   336, "7.22b":   13, "7.22c":   57, "7.22d":   63, "7.22e":   45,
    "7.22f":   85, "7.22g":   33, "7.22h":   16, "7.23":   349, "7.23a":   47,
    "7.23b":   90, "7.23c":   28, "7.23d":   37, "7.23e":   68, "7.23f":   53,
    "7.24":   232, "7.24b":   70, "7.25":   210, "7.25a":   11, "7.25b":    9,
    "7.25c":   84, "7.26":     6, "7.26a":   24, "7.26b":   17, "7.26c":   46,
    "7.27":   367, "7.27a":    3, "7.27b":  495, "7.27c":   34, "7.27d":   75,
    "7.28":   353, "7.28a":  153, "7.28b":  165, "7.28c":  200, "7.29":  1066,
    "7.29b":  127, "7.29c":   68, "7.29d":   91, "7.30":   698, "7.30b":   11,
    "7.30c":   54, "7.30d":  148, "7.30e":   77, "7.31":  1204, "7.31b":  168,
    "7.31c":  158, "7.31d":  203, "7.32":   729, "7.32b":  152, "7.32c":   78,
    "7.32d":  121, "7.32e":   73, "7.33":  1463, "7.33b":  274, "7.33c":  260,
    "7.33d":  256, "7.33e":   99, "7.34":   636, "7.34b":  132, "7.34c":  292,
    "7.34d":  104, "7.34e":  147, "7.35":   643, "7.35b":  102, "7.35c":  189,
    "7.35d":  151, "7.36":  1869, "7.36a":  286, "7.36b":  100, "7.36c":  225,
    "7.37":   692, "7.37b":  259, "7.37c":   84, "7.37d":  216, "7.37e":  119,
    "7.38":  1768, "7.38b":  202, "7.38c":   68, "7.39":   821, "7.39b":  133,
    "7.39c":  162, "7.39d":  146, "7.39e":   86, "7.40":  1054, "7.40b":  143,
    "7.40c":  152, "7.41":  1795, "7.41a":   60, "7.41b":  191, "7.41c":  204, "7.41d":  192,
}



def _current_version():
    """Return version string of the most recently released patch."""
    if not RELEASE_HISTORY:
        return None
    return sorted(RELEASE_HISTORY, key=lambda p: _parse_date(p["date"]))[-1]["version"]


def save_calendar_html():
    """Generate calendar.html — both modes inside a shared collapsible year block."""
    from datetime import datetime
    from calendar import monthrange
    import re as _re

    patches = []
    for r in RELEASE_HISTORY:
        d = datetime.strptime(r['date'], '%d.%m.%Y').date()
        patches.append({
            'version': r['version'], 'date': r['date'],
            'year': d.year, 'month': d.month, 'day': d.day,
        })

    by_month = {}
    for p in patches:
        by_month.setdefault((p['year'], p['month']), []).append(p)
    for k in by_month:
        by_month[k].sort(key=lambda p: p['day'])

    by_day = {(p['year'], p['month'], p['day']): p for p in patches}
    current_v = _current_version()
    years = sorted({p['year'] for p in patches}, reverse=True)

    # Per-patch lifespan: days between this release and the next release in
    # RELEASE_HISTORY (history is sorted newest-first there). Latest patch
    # uses today as the right edge. Then per-year longest/shortest.
    from datetime import datetime as _dt, date as _date
    today = _date.today()
    sorted_by_date = sorted(patches, key=lambda p: _dt.strptime(p['date'], '%d.%m.%Y').date())
    spans = {}  # version → days_running
    for i, p in enumerate(sorted_by_date):
        d = _dt.strptime(p['date'], '%d.%m.%Y').date()
        if i + 1 < len(sorted_by_date):
            nd = _dt.strptime(sorted_by_date[i+1]['date'], '%d.%m.%Y').date()
        else:
            nd = today
        spans[p['version']] = max(0, (nd - d).days)

    def year_summary(year_patches):
        if not year_patches:
            return None
        ranked = sorted(year_patches, key=lambda p: spans.get(p['version'], 0))
        min_days = spans.get(ranked[0]['version'], 0)
        max_days = spans.get(ranked[-1]['version'], 0)
        shortest_vers = [p['version'] for p in ranked if spans.get(p['version'], 0) == min_days]
        longest_vers  = [p['version'] for p in ranked if spans.get(p['version'], 0) == max_days]
        return {
            'total': len(year_patches),
            'shortest': (shortest_vers, min_days),
            'longest':  (longest_vers,  max_days),
        }
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    has_html = {p['version'] for p in PATCHES}
    expanded_years = {years[0]} if years else set()  # only current (newest) year expanded by default

    def patch_class(v):
        if _re.search(r'[a-z]$', v):
            return 'sub'
        return 'major'

    def chip_tag(v):
        if v in has_html:
            return ('a', f' href="patches/{v}.html?from=calendar"')
        return ('span', '')

    body = []
    body.append('<div class="calendar mode-full">')

    # Single year block. Year selector replaces per-year collapsible headers;
    # all years' grids are rendered in panes and only the selected pane is
    # visible at a time. The Compact toggle lives in this block's top-right
    # corner (added after the picker, below).
    body.append('<div class="cal-year-block is-current" data-collapsed="false">')
    body.append('<div class="cal-year-label">')
    default_year = years[0] if years else None
    body.append('<div class="cal-year-picker">')
    body.append(
        '<button type="button" class="cal-year-current" '
        'aria-haspopup="listbox" aria-expanded="false">'
        f'<span class="cal-year-current-val">{default_year}</span>'
        '<span class="cal-year-caret" aria-hidden="true">▾</span>'
        '</button>'
    )
    body.append('<ul class="cal-year-menu" role="listbox" hidden>')
    for year in years:
        sel = ' is-selected' if year == default_year else ''
        asel = 'true' if year == default_year else 'false'
        body.append(
            f'<li class="cal-year-opt{sel}" role="option" '
            f'data-year="{year}" aria-selected="{asel}">{year}</li>'
        )
    body.append('</ul>')
    body.append('</div>')  # cal-year-picker
    # Compact toggle — top-right corner of the calendar block, styled to match
    # the year-picker button (see .cal-compact-toggle in styles.css).
    body.append(
        '<label class="ua-upgrades-toggle cal-compact-toggle" '
        'title="Compact view">'
        '<span class="ua-upgrades-label">Compact</span>'
        '<input type="checkbox" class="ua-switch-input cal-compact-input">'
        '<span class="ua-switch"></span>'
        '</label>'
    )
    body.append('</div>')  # cal-year-label

    for year in years:
        hidden = '' if year == default_year else ' hidden'
        body.append(f'<div class="cal-year-pane" data-year="{year}"{hidden}>')

        # ---- MODE FULL ----
        body.append('<div class="cal-mode-full">')
        body.append('<div class="cal-full-grid">')
        for month in range(1, 13):
            body.append(
                f'<div class="cal-full-month-name" data-month="{month}">'
                f'{months[month-1]}</div>'
            )
            days_in_m = monthrange(year, month)[1]
            for d in range(1, 32):
                if d > days_in_m:
                    body.append(
                        f'<div class="cal-full-day no-day" '
                        f'data-month="{month}" data-day="{d}"></div>')
                    continue
                p = by_day.get((year, month, d))
                attrs = f' data-month="{month}" data-day="{d}"'
                if p:
                    cls = patch_class(p['version'])
                    tag, href = chip_tag(p['version'])
                    cur = " current" if p['version'] == current_v else ""
                    body.append(f'<{tag} class="cal-full-day has-patch {cls}{cur}"{href}{attrs}>{p["version"]}</{tag}>')
                else:
                    body.append(f'<div class="cal-full-day"{attrs}>{d}</div>')
        body.append('</div></div>')

        # ---- MODE COMPACT ----
        body.append('<div class="cal-mode-compact">')
        body.append('<div class="cal-grid">')
        for mi, mname in enumerate(months, 1):
            body.append('<div class="cal-month">')
            body.append(f'<div class="cal-month-name">{mname}</div>')
            body.append('<div class="cal-month-cells">')
            for p in by_month.get((year, mi), []):
                v = p['version']
                cls = patch_class(v)
                tag, href = chip_tag(v)
                cur = " current" if v == current_v else ""
                body.append(
                    f'<{tag} class="cal-patch {cls}{cur}"{href}>'
                    f'<span class="cal-version">{v}</span>'
                    f'<span class="cal-day">{p["day"]:02d}</span>'
                    f'</{tag}>'
                )
            body.append('</div></div>')
        body.append('</div></div>')

        # ---- YEAR SUMMARY ----
        ys = year_summary([p for p in patches if p['year'] == year])
        if ys:
            body.append(
                '<div class="cal-year-summary">'
                '<div class="cal-year-summary-left">'
                f'<span class="cal-year-summary-key">Total count:</span> '
                f'<span class="cal-year-summary-val">{ys["total"]}</span>'
                '</div>'
                '<div class="cal-year-summary-right">'
                f'<span class="cal-year-summary-key">Longest:</span> '
                f'<span class="cal-year-summary-val">{" &amp; ".join(ys["longest"][0])}</span>'
                f' <span class="cal-year-summary-meta">({ys["longest"][1]} days)</span>'
                f' &middot; '
                f'<span class="cal-year-summary-key">Shortest:</span> '
                f'<span class="cal-year-summary-val">{" &amp; ".join(ys["shortest"][0])}</span>'
                f' <span class="cal-year-summary-meta">({ys["shortest"][1]} days)</span>'
                '</div>'
                '</div>'
            )

        body.append('</div>')  # cal-year-pane

    body.append('</div>')  # cal-year-block

    # ---- INFOGRAPHIC: patch cadence (compact card under the calendar) ----
    year_counts = {}
    for p in patches:
        year_counts[p['year']] = year_counts.get(p['year'], 0) + 1
    month_counts = [0] * 12
    for p in patches:
        month_counts[p['month'] - 1] += 1
    total_patches = len(patches)
    years_tracked = len(year_counts)
    avg_per_year = (total_patches / years_tracked) if years_tracked else 0
    span_vals = sorted(spans.values())
    if span_vals:
        n = len(span_vals)
        median_span = (span_vals[n // 2] if n % 2
                       else (span_vals[n // 2 - 1] + span_vals[n // 2]) // 2)
    else:
        median_span = 0
    max_year_count = max(year_counts.values()) if year_counts else 1
    max_month_count = max(month_counts) if month_counts else 1

    min_year = min(year_counts) if year_counts else None

    def _spark_svg(values, labels, tips, uid):
        """Smooth (Catmull-Rom) sparkline with: gradient area fill, faint
        horizontal gridlines, a left y-axis (with min/max ticks), an x-axis
        baseline separating the category labels from the plot, point dots and a
        per-point value that appears on hover. Crisp SVG, scales via CSS."""
        n = len(values)
        maxv = max(values) if values and max(values) > 0 else 1
        # "Nice" axis top: round the data max UP to a clean 5-step scale, so the
        # axis reads e.g. 0..25 (step 5) when the real max is 21 — the peak sits
        # below the top tick instead of pinned to it.
        nice_step = next(st for st in (1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 25, 50, 100, 200, 500)
                         if st * 5 >= maxv)
        nice_max = nice_step * 5
        viewW, padL, padR, padTop, chartH, labelH = 520, 32, 14, 12, 86, 18
        totalH = chartH + labelH
        x0p, x1p = padL, viewW - padR
        step = (x1p - x0p) / (n - 1) if n > 1 else 0
        pts = [(x0p + i * step,
                padTop + (1 - v / nice_max) * (chartH - padTop)) for i, v in enumerate(values)]

        def pt(i):
            return pts[min(max(i, 0), n - 1)]
        d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
        for i in range(1, n):
            x0, y0 = pt(i - 2)
            x1, y1 = pt(i - 1)
            x2, y2 = pt(i)
            x3, y3 = pt(i + 1)
            c1x, c1y = x1 + (x2 - x0) / 6, y1 + (y2 - y0) / 6
            c2x, c2y = x2 - (x3 - x1) / 6, y2 - (y3 - y1) / 6
            d += f" C {c1x:.1f} {c1y:.1f} {c2x:.1f} {c2y:.1f} {x2:.1f} {y2:.1f}"
        area = d + f" L {pts[-1][0]:.1f} {chartH} L {pts[0][0]:.1f} {chartH} Z"

        s = [f'<svg class="cal-ig-spark" viewBox="0 0 {viewW} {totalH}" role="img">']
        s.append(f'<defs><linearGradient id="sg-{uid}" x1="0" y1="0" x2="0" y2="1">'
                 '<stop offset="0" stop-color="#79c0ff" stop-opacity="0.28"/>'
                 '<stop offset="1" stop-color="#79c0ff" stop-opacity="0"/>'
                 '</linearGradient></defs>')
        # Horizontal gridlines + y-axis ticks on the 5-step nice scale.
        for k in range(6):                       # 0,1,2,3,4,5 → 0..nice_max
            gy = padTop + (1 - k / 5) * (chartH - padTop)
            if 0 < k < 5:
                s.append(f'<line class="cal-ig-grid" x1="{x0p}" y1="{gy:.1f}" x2="{x1p}" y2="{gy:.1f}"/>')
            s.append(f'<text class="cal-ig-ytick" x="{x0p - 6}" y="{gy + 3:.1f}" '
                     f'text-anchor="end">{nice_step * k}</text>')
        # Vertical minor gridlines — one per category (skip the first, it sits on
        # the y-axis).
        for vx, _vy in pts[1:]:
            s.append(f'<line class="cal-ig-grid cal-ig-grid-v" x1="{vx:.1f}" y1="{padTop}" '
                     f'x2="{vx:.1f}" y2="{chartH}"/>')
        # y-axis (left).
        s.append(f'<line class="cal-ig-axis" x1="{x0p}" y1="{padTop}" x2="{x0p}" y2="{chartH}"/>')
        # area + line.
        s.append(f'<path d="{area}" fill="url(#sg-{uid})"/>')
        s.append(f'<path d="{d}" fill="none" stroke="#58a6ff" stroke-width="2.4" '
                 'stroke-linecap="round" stroke-linejoin="round"/>')
        # x-axis baseline — separates the plot from the category labels below.
        s.append(f'<line class="cal-ig-axis is-base" x1="{x0p}" y1="{chartH}" x2="{x1p}" y2="{chartH}"/>')
        # Points: each in a hover group (wide invisible hit rect → value pops).
        for i, (x, y) in enumerate(pts):
            hx = x - (step / 2 if step else 14)
            hw = step if step else 28
            s.append(f'<g class="cal-ig-pt"><title>{_html.escape(tips[i])}</title>')
            s.append(f'<rect class="cal-ig-hit" x="{hx:.1f}" y="{padTop}" '
                     f'width="{hw:.1f}" height="{chartH - padTop:.1f}"/>')
            s.append(f'<circle class="cal-ig-dot" cx="{x:.1f}" cy="{y:.1f}" '
                     f'fill="#79c0ff" stroke="#0d1117" stroke-width="1.4"/>')
            s.append(f'<text class="cal-ig-pt-val" x="{x:.1f}" y="{y - 8:.1f}" '
                     f'text-anchor="middle">{values[i]}</text>')
            s.append('</g>')
            s.append(f'<text x="{x:.1f}" y="{chartH + 13}" text-anchor="middle" '
                     f'class="cal-ig-spark-lbl">{labels[i]}</text>')
        s.append('</svg>')
        return ''.join(s)

    # Whole (major, e.g. 7.41) vs lettered (sub, e.g. 7.41a) patch counts.
    major_count = sum(1 for p in patches if not _re.search(r'[a-z]$', p['version']))
    sub_count = total_patches - major_count

    ig = ['<div class="cal-infographic">']

    # Lead panel: title + inline key stats (compact, no big chips).
    ig.append('<div class="cal-ig-panel cal-ig-lead">')
    ig.append('<div class="cal-ig-title">Patch cadence</div>')
    ig.append(f'<div class="cal-ig-sub">{min_year} – now</div>')
    ig.append('<div class="cal-ig-statline">'
              f'<span><b>{total_patches}</b> patches:</span>'
              '<span class="cal-ig-rule"></span>'
              f'<span><b class="cal-ig-major">{major_count}</b> major</span>'
              f'<span><b>{sub_count}</b> letter</span>'
              '<span class="cal-ig-rule"></span>'
              f'<span><b>{avg_per_year:.1f}</b> / year</span>'
              f'<span><b>{median_span}</b>d median life</span>'
              '</div>')
    ig.append('</div>')

    # Per-year sparkline (chronological left→right).
    yrs = sorted(year_counts)
    ig.append('<div class="cal-ig-panel">')
    ig.append('<div class="cal-ig-h">Per year</div>')
    ig.append(_spark_svg(
        [year_counts[y] for y in yrs],
        [str(y)[2:] for y in yrs],
        [f"{y}: {year_counts[y]} patch(es)" for y in yrs],
        'yr'))
    ig.append('</div>')

    # Per-month sparkline (all years combined).
    ig.append('<div class="cal-ig-panel">')
    ig.append('<div class="cal-ig-h">Per month</div>')
    ig.append(_spark_svg(
        month_counts,
        [months[mi][0] for mi in range(12)],
        [f"{months[mi]}: {month_counts[mi]} patch(es)" for mi in range(12)],
        'mo'))
    ig.append('</div>')
    ig.append('</div>')  # cal-infographic
    body.append('\n'.join(ig))

    body.append('</div>')  # .calendar

    toggle_script = '''<script>
(function() {
  const cal = document.querySelector('.calendar');
  const compact = document.querySelector('.cal-compact-input');
  if (compact) {
    compact.addEventListener('change', () => {
      cal.classList.remove('mode-full', 'mode-compact');
      cal.classList.add(compact.checked ? 'mode-compact' : 'mode-full');
    });
  }
  const picker = document.querySelector('.cal-year-picker');
  if (picker) {
    const btn  = picker.querySelector('.cal-year-current');
    const menu = picker.querySelector('.cal-year-menu');
    const valEl = picker.querySelector('.cal-year-current-val');
    const opts = [...menu.querySelectorAll('.cal-year-opt')];
    const open  = () => { menu.hidden = false; picker.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true'); };
    const close = () => { menu.hidden = true;  picker.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); };
    const selectYear = (year) => {
      valEl.textContent = year;
      opts.forEach(o => {
        const on = o.dataset.year === year;
        o.classList.toggle('is-selected', on);
        o.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      document.querySelectorAll('.cal-year-pane').forEach(p => {
        p.hidden = (p.dataset.year !== year);
      });
    };
    btn.addEventListener('click', e => { e.stopPropagation(); menu.hidden ? open() : close(); });
    opts.forEach(o => o.addEventListener('click', () => { selectYear(o.dataset.year); close(); }));
    document.addEventListener('click', e => { if (!picker.contains(e.target)) close(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }
  // Row + column cross-highlight on the Full grid. Event-delegated so it
  // works across all year panes (only one is visible at a time).
  document.querySelectorAll('.cal-full-grid').forEach(grid => {
    let activeRow = null, activeCol = null;
    const clear = () => {
      grid.querySelectorAll('.cross-row,.cross-col').forEach(el => {
        el.classList.remove('cross-row', 'cross-col');
      });
      activeRow = activeCol = null;
    };
    grid.addEventListener('mouseover', e => {
      const cell = e.target.closest('[data-day],[data-month]');
      if (!cell || !grid.contains(cell)) return;
      const m = cell.dataset.month, d = cell.dataset.day;
      if (m === activeRow && d === activeCol) return;
      clear();
      activeRow = m; activeCol = d;
      if (m) grid.querySelectorAll(`[data-month="${m}"]`).forEach(
        el => el.classList.add('cross-row'));
      if (d) grid.querySelectorAll(`[data-day="${d}"]`).forEach(
        el => el.classList.add('cross-col'));
    });
    grid.addEventListener('mouseleave', clear);
  });
})();
</script>'''

    cur_v = _current_version()
    cur_date = next((r["date"] for r in RELEASE_HISTORY if r["version"] == cur_v), None)
    nav = _render_top_nav(active="calendar", current_version=cur_v, date=cur_date)
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<title>SIKLE | Calendar</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={_ASSET_VERSION}">\n'
        '</head>\n<body>\n\n'
        + nav
        + '\n<div class="container calendar-page">\n'
        + '\n'.join(body)
        + '\n</div>\n\n'
        + f'<script src="scripts.js?v={_ASSET_VERSION}"></script>\n'
        + toggle_script + '\n'
        + '</body>\n</html>\n'
    )
    with open('calendar.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → calendar.html: {len(html):,} bytes")


def save_index_html():
    """Generate index.html — the Main landing tab. Currently a placeholder
    that just renders the unified top-nav; reserved for a hub/about page
    later. Title and structure mirror the other tabs so the header stays
    in step."""
    # Index hub: hide the centre nav tabs — they duplicate the tile grid below.
    nav = _render_top_nav(active="main", patch_context=False, centre_tabs=False)
    # Landing page styled as a game inventory opened in a leather-bound book:
    # an ornate parchment panel with square slots; the filled slots are the
    # site's sections (gothic pixel-art icons), the rest are empty inventory
    # cells. Assets: icons/ui/gothic/ (Gothic Pixel UI FREE, gold variant).
    latest = PATCHES[0]['version'] if PATCHES else None
    # Captions are placeholder words for now (final wording TBD); the hrefs are
    # the real destinations. Font matches the "sikle" wordmark (Jersey 10).
    # Top row = two simple link tiles, three SUB-PANEL openers (Creeps / Items /
    # Heroes, which expand in place like Support instead of redirecting), then
    # Terrain. Each link tile swaps its static PNG for an animated GIF on hover:
    # calendar (date burn, JS), patch (page-flip, CSS), terrain (levitate, CSS).
    _INV_LINKS = {
        'patch':    ('Changelogs', f'patches/{latest}.html' if latest else 'calendar.html'),
        'calendar': ('Calendar',   'calendar.html'),
        'terrain':  ('Terrain',    'terrain.html'),
    }
    # Arcana (Neutral Abilities) lives under the Materials sub-nav, so it has no
    # hub tile of its own.
    _INV_PLACEHOLDERS = []

    def _link_tile(key):
        label, href = _INV_LINKS[key]
        if key == "terrain":
            # Terrain = a floating earth block: on hover it levitates + bobs and
            # sheds occasional pixel "dirt" from its underside (CSS particles).
            return (
                f'<a class="inv-cell inv-filled inv-cell-terrain" href="{href}">'
                '<span class="inv-slot">'
                '<img class="inv-icon" src="icons/ui/gothic/icon_terrain.png" alt="">'
                '<span class="terrain-dirt" aria-hidden="true">'
                + '<i class="dirt"></i>' * 5 +
                '</span>'
                '</span>'
                f'<span class="inv-cap">{label}</span>'
                '</a>'
            )
        return (
            f'<a class="inv-cell inv-filled inv-cell-{key}" href="{href}">'
            f'<span class="inv-slot">'
            f'<img class="inv-icon" src="icons/ui/gothic/icon_{key}.png" alt="">'
            f'</span>'
            f'<span class="inv-cap">{label}</span>'
            f'</a>'
        )

    def _opener_tile(key, label, panel, icon):
        # A tile that expands a sub-panel in place (like Support). `key` doubles
        # as the .inv-cell-<key> hover class, so passing 'creeps' keeps the
        # beetle-crawl GIF; placeholder openers (items/heroes) use a key with no
        # hover rule, so they stay static.
        return (
            f'<a class="inv-cell inv-filled inv-cell-{key}" href="#{panel}" '
            f'data-panel-open="{panel}" role="button" aria-expanded="false">'
            '<span class="inv-slot">'
            f'<img class="inv-icon" src="icons/ui/gothic/{icon}" alt="">'
            '</span>'
            f'<span class="inv-cap">{label}</span>'
            '</a>'
        )

    cells = [
        _link_tile('patch'),
        _link_tile('calendar'),
        # Creeps opener keeps the beetle-crawl hover (.inv-cell-creeps).
        _opener_tile('creeps', 'Creeps', 'creeps', 'icon_creeps.png'),
        # Items opener: closed treasure chest at rest; hover plays the chest-open
        # APNG (key → lid opens → gold beam + treasure). See .inv-cell-items CSS.
        _opener_tile('items', 'Items', 'items', 'icon_chest.png'),
        _opener_tile('heroes', 'Heroes', 'heroes', 'icon_hat.png'),
        _link_tile('terrain'),
    ]
    # Special "star" tile — the slot emits a faint pixel-gold glow (hinting it's
    # special); on hover the star pulses (grows/shrinks) and throws off a burst
    # of magic dust (CSS). Instead of redirecting, clicking it opens the Support
    # SUB-PANEL in place (the grid hides, two ways to support appear). See the
    # `.support-panel` below + the toggle handler in scripts.js.
    cells.append(
        '<a class="inv-cell inv-filled inv-cell-star inv-special" '
        'href="#support" data-panel-open="support" '
        'role="button" aria-expanded="false">'
        '<span class="inv-slot">'
        '<img class="inv-icon" src="icons/ui/gothic/icon_star.png" alt="">'
        # Magic dust: 6 base sparks drift faintly at rest; 8 burst sparks ignite
        # on hover (the burst layer fades out on mouse-out → graceful disappear).
        '<span class="inv-sparks" aria-hidden="true">'
        '<span class="dust-base">' + '<i class="spark"></i>' * 6 +
        '</span><span class="dust-burst">' + '<i class="spark"></i>' * 8 +
        '</span></span>'
        '</span>'
        '<span class="inv-cap">Support</span>'
        '</a>'
    )
    empties = ''.join(
        f'<span class="inv-cell inv-ph" title="placeholder">'
        f'<span class="inv-slot">'
        f'<img class="inv-icon" src="icons/ui/gothic/icon_{key}.png" alt="">'
        f'</span>'
        f'<span class="inv-cap">{label}</span>'
        f'</span>'
        for key, label in _INV_PLACEHOLDERS
    )
    # Support sub-panel — hidden until the Support tile is clicked, then it
    # replaces the grid (the book heading + divider stay). Two ways to support:
    # Telegram (the previous Tribute link) and Donation (link TBD). A back arrow
    # returns to the inventory grid. Icons are gothic-gold pixel art.
    TRIBUTE = 'https://t.me/tribute/app?startapp=so4y'
    # Support sub-panel: two tiles the SAME size as the grid tiles, centred.
    #  - Telegram = a crumpled envelope that beats like a heart on hover and
    #    sheds faint hollow hearts that linger then fade (like the star's dust).
    #  - Donation = a glass jar of coins; on hover a coin keeps dropping in (loop).
    #    Link not wired yet → inert "soon" tile (hover animation still plays).
    support_panel = (
        '<div class="inv-panel support-panel" data-panel="support" aria-hidden="true">'
        '<div class="support-options">'
        f'<a class="support-btn support-telegram" href="{TRIBUTE}" '
        'target="_blank" rel="noopener noreferrer">'
        '<span class="inv-slot">'
        '<img class="inv-icon" src="icons/ui/gothic/icon_telegram.png" alt="">'
        '<span class="tg-hearts" aria-hidden="true">'
        + '<i class="tg-heart"></i>' * 8 +
        '</span>'
        '</span>'
        '<span class="inv-cap">Telegram</span></a>'
        '<span class="support-btn support-donation support-soon" '
        'aria-disabled="true" title="Coming soon">'
        '<span class="inv-slot">'
        '<img class="inv-icon" src="icons/ui/gothic/icon_donation.png" alt="">'
        '<span class="don-coin" aria-hidden="true"></span>'
        '<span class="support-soon-tag">soon</span></span>'
        '<span class="inv-cap">Donation</span></span>'
        '</div>'
        '</div>'
    )
    # Sub-panels opened by the Creeps / Heroes / Items tiles (same mechanism as
    # Support). Buttons reuse the .support-btn shell; an .inv-cell-<key> class on
    # a button carries over that tile's hover animation (creeps crawl, dynamics
    # bars, mana fill). Unwired buttons render as inert "soon" tiles.
    def _panel_link_btn(anim_cls, href, icon, label):
        cls = ('support-btn ' + anim_cls).strip()
        return (
            f'<a class="{cls}" href="{href}">'
            '<span class="inv-slot">'
            f'<img class="inv-icon" src="icons/ui/gothic/{icon}" alt="">'
            '</span>'
            f'<span class="inv-cap">{label}</span></a>'
        )

    def _panel_soon_btn(icon, label):
        return (
            '<span class="support-btn support-soon" '
            'aria-disabled="true" title="Coming soon">'
            '<span class="inv-slot">'
            f'<img class="inv-icon" src="icons/ui/gothic/{icon}" alt="">'
            '<span class="support-soon-tag">soon</span></span>'
            f'<span class="inv-cap">{label}</span></span>'
        )

    creeps_panel = (
        '<div class="inv-panel creeps-panel" data-panel="creeps" aria-hidden="true">'
        '<div class="support-options">'
        + _panel_link_btn('inv-cell-creeps', 'neutral_stats.html', 'icon_creeps.png', 'Neutrals')
        + _panel_soon_btn('icon_abilities.png', 'Summons')
        + _panel_soon_btn('icon_tree.png', 'Lane Creeps')
        + '</div></div>'
    )
    heroes_panel = (
        '<div class="inv-panel heroes-panel" data-panel="heroes" aria-hidden="true">'
        '<div class="support-options">'
        + _panel_link_btn('inv-cell-dynamics', 'heroes_dyn.html', 'icon_dynamics.png', 'Dynamics')
        + _panel_link_btn('', 'heroes_stats.html', 'icon_typewriter.png', 'Stats')
        + '</div></div>'
    )
    items_panel = (
        '<div class="inv-panel items-panel" data-panel="items" aria-hidden="true">'
        '<div class="support-options">'
        + _panel_link_btn('inv-cell-mana', 'mana_items.html', 'icon_mana.png', 'Mana')
        + _panel_link_btn('inv-cell-dynamics', 'items_dyn.html', 'icon_dynamics.png', 'Dynamics')
        + '</div></div>'
    )
    # The divider keeps its place under the title; when the Support panel is
    # open a gothic left-arrow ornament appears to its left as the "back" control
    # (styled like the divider, signalling it's clickable).
    divider_row = (
        '<div class="inv-divider-row">'
        '<button type="button" class="support-back" data-panel-close '
        'aria-label="Back to menu" title="Back">'
        '<img class="support-back-orn" src="icons/ui/gothic/divider_arrow_left.png" alt="">'
        '</button>'
        '<img class="inv-divider" src="icons/ui/gothic/divider.png" alt="" aria-hidden="true">'
        '</div>'
    )
    # The grid + support panel share one fixed-height stage: the grid stays in
    # flow (defines the height) and only goes invisible when Support opens, while
    # the panel is absolutely centred over it. So the book never changes size and
    # the divider above it never moves.
    grid_html = (
        '<div class="inv-book">'
        '<div class="inv-head">'
        '<h1 class="inv-title">What does a hero truly need?</h1>'
        '</div>'
        f'{divider_row}'
        '<div class="inv-stage">'
        f'<div class="inv-grid">{"".join(cells)}{empties}</div>'
        f'{support_panel}'
        f'{creeps_panel}'
        f'{heroes_panel}'
        f'{items_panel}'
        '</div>'
        '</div>'
    )

    # ---- WALL OF SIGNATURES ----
    # Faint pixel-font "graffiti" of channel-member display names scattered
    # around the book. Real names come from data/signatures.json, produced by
    # scripts/fetch_signatures.py (run via run_signatures.ps1). We show display
    # names, not @usernames, so a member can't be found/DMed from the wall.
    # Members with an empty or punctuation-only name collapse into one
    # "Hidden (xN)" sign. If the file is missing we fall back to random
    # placeholders so the page still builds. scripts.js positions every sign
    # (no overlap with book/nav/each other) on load + resize.
    _names: list[str] = []
    _hidden = 0
    _sig_path = _os.path.join(_os.path.dirname(__file__), 'data', 'signatures.json')
    try:
        with open(_sig_path, encoding='utf-8') as _f:
            _sig_data = _json.load(_f)
        _names = [str(u).strip() for u in _sig_data.get('names', []) if str(u).strip()]
        _hidden = int(_sig_data.get('hidden', 0) or 0)
    except (FileNotFoundError, ValueError, OSError):
        _names = []

    if not _names:
        # Fallback: 100 random placeholder usernames (no real data yet).
        import random as _rnd
        _rng = _rnd.Random(1337)
        _A = ['shadow', 'frost', 'blood', 'iron', 'dire', 'arc', 'void', 'ember',
              'storm', 'night', 'rune', 'grim', 'swift', 'mad', 'lone', 'dark',
              'gold', 'silent', 'feral', 'toxic', 'salty', 'tilted', 'cheeky',
              'turbo', 'mega', 'ultra', 'lil', 'big', 'old', 'crazy', 'sleepy']
        _N = ['wolf', 'mage', 'blade', 'crit', 'ward', 'creep', 'mid', 'carry',
              'pudge', 'invoker', 'meepo', 'wisp', 'goblin', 'knight', 'reaper',
              'sniper', 'enjoyer', 'andy', 'chad', 'gamer', 'feeder', 'smurf',
              'gosu', 'main', 'diff', 'simp', 'fan', 'boi', 'lord', 'btw']
        _SUF = ['', '', '', '7', '42', '69', '99', '228', '322', '1337', 'xd', 'ttv']

        def _uname():
            a, n, s = _rng.choice(_A), _rng.choice(_N), _rng.choice(_SUF)
            r = _rng.random()
            if r < 0.22:
                return f'xX_{a}{n}_Xx'
            if r < 0.46:
                return f'{a}_{n}{s}'
            if r < 0.68:
                return f'{a}{n}{s}'
            if r < 0.85:
                return f'{n}_{s or _rng.randint(10, 9999)}'
            return f'{a}{_rng.randint(1, 999)}'

        _seen = set()
        while len(_names) < 100:
            u = _uname()
            if u not in _seen:
                _seen.add(u)
                _names.append(u)

    # VIP names — always present regardless of the collected/placeholder list,
    # rendered in their own colour (azure). When a beam lights one it throws off
    # pixel "forge sparks" (scripts.js), as if the name was just forged. Drop any
    # duplicate from the regular list so a VIP never shows twice.
    _VIP_NAMES = ['iKrivetko', 'DMorg']
    _vip_lower = {v.lower() for v in _VIP_NAMES}
    _names = [u for u in _names if u.lower() not in _vip_lower]

    # Telegram display names sometimes contain colour emoji — gold star, blue
    # check, party popper, etc. Rendered raw they break the signature wall's
    # uniform palette (the sigs are supposed to read as a single monochrome
    # crowd). Wrap each emoji run in <span class="inv-emo"> so CSS can flatten
    # it to the current text colour via the classic transparent-text + 0,0,0
    # text-shadow trick (works on colour-emoji glyphs cross-browser).
    _EMO_RE = re.compile(
        '['
        '\U0001F1E6-\U0001F1FF'   # regional indicators (flags)
        '\U0001F300-\U0001F5FF'   # symbols & pictographs
        '\U0001F600-\U0001F64F'   # emoticons
        '\U0001F680-\U0001F6FF'   # transport & map
        '\U0001F700-\U0001F77F'
        '\U0001F780-\U0001F7FF'
        '\U0001F800-\U0001F8FF'
        '\U0001F900-\U0001F9FF'   # supplemental symbols
        '\U0001FA00-\U0001FA6F'
        '\U0001FA70-\U0001FAFF'   # symbols extended-A
        '☀-➿'            # misc symbols + dingbats (star, check, etc.)
        '⌀-⏿'            # misc technical (gear, hourglass)
        '⬀-⯿'            # arrows extended
        ']+'
    )

    def _wrap_emoji(s: str) -> str:
        # Escape HTML first so user-supplied < > & stay safe, then wrap any
        # emoji runs (which html.escape passes through verbatim).
        return _EMO_RE.sub(
            lambda m: f'<span class="inv-emo">{m.group(0)}</span>',
            _html.escape(s))

    _sigs = ''.join(
        f'<span class="inv-sig inv-sig-vip">{_wrap_emoji(v)}</span>' for v in _VIP_NAMES)
    _sigs += ''.join(f'<span class="inv-sig">{_wrap_emoji(u)}</span>' for u in _names)
    if _hidden > 0:
        _sigs += f'<span class="inv-sig inv-sig-hidden">Hidden (x{_hidden})</span>'
    sig_layer = f'<div class="inv-signatures" aria-hidden="true">{_sigs}</div>'
    html = (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<title>SIKLE | dota.vpk</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        # Handjet = pixel/dot-matrix font WITH Cyrillic (Jersey 10 is Latin-only),
        # used for the signature wall so Cyrillic member names render in-style.
        'href="https://fonts.googleapis.com/css2?family=Handjet:wght@400..700&family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={_ASSET_VERSION}">\n'
        '</head>\n'
        '<body>\n'
        f'{nav}\n'
        f'{sig_layer}\n'
        f'<div class="container main-page">{grid_html}</div>\n'
        f'<script src="scripts.js?v={_ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → index.html: {len(html):,} bytes")


# save_creeps_html() moved to build_creeps.py (standalone side-project).
# Run `python build_creeps.py` after build_patch.py to regenerate creeps.html.



# ============================================================
# 7.41d content
# ============================================================
save_assets()
write_head("7.41d", "04.06.2026")

# 7.41d — auto-generated from data/7.41d_datafeed.json (generate_patch_code_v2.py)
# then hand-reviewed: cooldown/timer rows promoted from MISC to numeric badges
# with l=True, base-stat "by N" rows resolved via bstat_h against 7.41c, Spirit
# Bear folded into a Lone Druid section, per-level formula rows on li_formula.

# ===== GENERAL UPDATES =====
W(section("General Updates"))

W(plain_header("Mechanics"))
W(ul_open())
W(li("Dire Fountain: Rejuvenation Aura radius has been slightly increased", t("MISC")))
W(li("Self-Cast on Town Portal Scroll's Teleport and other similar abilities now place the hero slightly closer to the Ancient", t("QoL")))
W(li("Town Portal Scroll's Teleport and other similar ability effects now partially follow the channeling unit even if they move after starting their teleport", t("QoL"),
     extra=inline_note(
         "This makes it possible to track the real spot a hero teleported from while using a movement ability during the channel (e.g. Ball Lightning, Pounce, Sun Ray, etc.). "
         "Previously the teleport animation stayed in one place while the displaced hero actually landed somewhere else. "
         "Now the circle animation plays where the Town Portal Scroll was used, but the full animation and effects appear where the hero lands."
     )))
W(ul_close())

# ===== ITEM UPDATES =====
W(section("Item Updates"))
W(item_header("Dagon"))
W(ul_open())
W(li("Recipe cost decreased from 1150 to 1100", b(1150, 1100, l=True), extra=inline_note("Total cost decreased from 3050/4200/5350/6500/7650g to 3000/4100/5200/6300/" + '<span class="li-tail">7400g — ' + b([3050, 4200, 5350, 6500, 7650], [3000, 4100, 5200, 6300, 7400], l=True) + '</span>')))
W(ul_close())
W(item_header("Mage Slayer"))
W(ul_open())
W(li("Damage bonus decreased from +15 to +12", b(15, 12)))
W(ul_close())
W(item_header("Smoke of Deceit"))
W(ul_open())
W(li("Using Smoke of Deceit now broadcasts a chat message in allied chat", t("QoL")))
W(ul_close())

# ===== NEUTRAL ITEM UPDATES =====
W(section("Neutral Item Updates"))

W(plain_header("Artifacts", dynamics=False))
W(item_header("Flayer's Bota"))
W(ul_open())
W(li("Bloodrush range increased from 1200 to 1500", b(1200, 1500)))
W(ul_close())
W(item_header("Idol of Scree'auk"))
W(ul_open())
W(li("False Flight bonus evasion increased from 25% to 35%", b(25, 35)))
W(ul_close())
W(item_header("Prophet's Pendulum"))
W(ul_open())
W(li("Linger delayed damage is now non-lethal if the incoming damage source was non-lethal", t("MISC"), extra=inline_note("Fixes a bug where a hero could kill themselves with their own non-lethal damage (Huskar, Soul Ring, Rot etc.)")))
W(ul_close())
W(item_header("Dezun Bloodrite"))
W(ul_open())
W(li("Blood Invocation bonus AoE increased from 16% to 20%", b(16, 20)))
W(ul_close())
W(item_header("Fallen Sky"))
W(ul_open())
W(li("Fallen Sky building impact damage increased from 75 to 110", b(75, 110)))
W(ul_close())
W(item_header("Harmonizer"))
W(ul_open())
W(li("Balance mana cost reduction per ability off cooldown increased from 5% to 7%", b(5, 7)))
W(ul_close())
W(item_header("Riftshadow Prism"))
W(ul_open())
W(li("Refract illusion's outgoing damage increased from 50% to 60%", b(50, 60)))
W(ul_close())
W(item_header("Spider Legs"))
W(ul_open())
W(li("Skitter cooldown decreased from 20s to 15s", b(20, 15, l=True)))
W(li("Skitter duration decreased from 14s to 12s", b(14, 12)))
W(ul_close())
W(item_header("Witchbane"))
W(ul_open())
W(li("Cleanse cast range increased from 500 to 700", b(500, 700)))
W(li("Cleanse: Mana Cost decreased from 150 to 50", b(150, 50, l=True)))
W(ul_close())

W(plain_header("Enchantments", dynamics=False))
W(enchant_header("Alert"))
W(ul_open())
W(li("Night Vision bonus decreased from +0/150/225/300 to +0/125/175/225", b([0, 150, 225, 300], [0, 125, 175, 225])))
W(li("Attack Range bonus decreased from +0/0/0/100 to +0/0/0/80", b([0, 0, 0, 100], [0, 0, 0, 80])))
W(ul_close())
W(enchant_header("Timeless"))
W(ul_open())
W(li("Spell Amplification bonus decreased from +6/16% to +5/12%", b([6, 16], [5, 12])))
W(ul_close())
W(enchant_header("Titanic"))
W(ul_open())
W(li("Attack Speed penalty decreased from 10/12/14% to 9%", b([10, 12, 14], 9, l=True)))
W(ul_close())
W(enchant_header("Vital"))
W(ul_open())
W(li("Health Regen bonus increased from +2 to +2.25", b(2, 2.25)))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))

# Abaddon
W(hero_header("Abaddon"))
W(ul_open())
W(li("Base Attack Speed increased from 95 to 100", b(95, 100)))
W(ul_close())
W(ability("Withering Mist", slug="abaddon_withering_mist"))
W(ul_open())
W(li_formula("Heal Reduction increased",
             "24.5% + 0.5% per level", "29.5% + 0.5% per level",
             lambda L: 24.5 + 0.5 * L, lambda L: 29.5 + 0.5 * L,
             value_fmt="{:g}%"))
W(ul_close())

# Ancient Apparition
W(hero_header("Ancient Apparition"))
W(ability("Cold Feet", slug="ancient_apparition_cold_feet"))
W(ul_open())
W(li("Damage per second increased from 20/40/60/80 to 25/45/65/85", b([20, 40, 60, 80], [25, 45, 65, 85])))
W(ul_close())
W(ability("Chilling Touch", slug="ancient_apparition_chilling_touch"))
W(ul_open())
W(li("Cooldown decreased from 12/9/6/3s to 10/7.5/5/2.5s", b([12, 9, 6, 3], [10, 7.5, 5, 2.5], l=True)))
W(li("Damage increased from 30/60/90/120 to 35/65/95/125", b([30, 60, 90, 120], [35, 65, 95, 125])))
W(ul_close())

# Anti-Mage
W(hero_header("Anti-Mage"))
W(ul_open())
W(li("Base Agility increased from 24 to 25", b(24, 25)))
W(li("Damage at level 1 increased by 1 (from 53-57 to 54-58)", br(53, 57, 54, 58)))
W(ul_close())
W(ability("Blink", slug="antimage_blink"))
W(ul_open())
W(li("Mana Cost decreased from 65/60/55/50 to 60/55/50/45", b([65, 60, 55, 50], [60, 55, 50, 45], l=True)))
W(ul_close())

# Arc Warden
W(hero_header("Arc Warden"))
W(ability("Flux", slug="arc_warden_flux"))
W(ul_open())
W(li("Cast Range increased from 500/600/700/800 to 625/700/775/850", b([500, 600, 700, 800], [625, 700, 775, 850])))
W(li("Movement Speed Slow increased from 14/21/28/35% to 20/25/30/35%", b([14, 21, 28, 35], [20, 25, 30, 35])))
W(ul_close())

# Axe
W(hero_header("Axe"))
W(ul_open())
W(li("Base Health Regen decreased by 0.5", bstat_h("Axe", "StatusHealthRegen", "7.41c", -0.5), extra=inline_note("Valve also lists \"Sense of Foreboding increased from 0 to 0.5\", but no such ability exists anywhere in the game files (likely a Valve leftover) — the only real change is the base Health Regen reduction")))
W(ul_close())
W(ability("Battle Hunger", slug="axe_battle_hunger"))
W(ul_open())
W(li("Cast Range decreased from 700/775/850/925 to 600/700/800/900", b([700, 775, 850, 925], [600, 700, 800, 900])))
W(ul_close())

# Bloodseeker
W(hero_header("Bloodseeker"))
W(ability("Bloodrage", slug="bloodseeker_bloodrage"))
W(ul_open())
W(li("No longer procs Magic Stick or its upgrades", t("BUFF")))
W(ul_close())
W(ability("Rupture", slug="bloodseeker_rupture"))
W(ul_open())
W(li("Aghanim's Scepter health damage increased from 13% to 15%", b(13, 15)))
W(ul_close())

# Bounty Hunter
W(hero_header("Bounty Hunter"))
W(ability("Big Game Hunter", slug="bounty_hunter_big_game_hunter"))
W(ul_open())
W(li("Bonus gold increased from 15% to 20%", b(15, 20)))
W(ul_close())

# Brewmaster
W(hero_header("Brewmaster"))
W(ability("Thunder Clap", slug="brewmaster_thunder_clap"))
W(ul_open())
W(li("Slow duration increased from 4s to 4/4.25/4.5/4.75s", b(4, [4, 4.25, 4.5, 4.75])))
W(ul_close())
W(ability("Liquid Courage", slug="brewmaster_liquid_courage"))
W(ul_open())
W(li("Aghanim's Shard max HP regen per second increased from 2.5% to 3%", b(2.5, 3)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Brewlings Base Damage decreased from +14 to +13", b(14, 13)))
W(li("Level 20 Talent Primal Split Cooldown Reduction decreased from 15s to 12s", b(15, 12)))
W(ul_close())

# Broodmother
W(hero_header("Broodmother"))
W(ability("Spawn Spiderlings", slug="broodmother_spawn_spiderlings"))
W(ul_open())
W(li("Spiderlings HP increased from 300 to 325", b(300, 325)))
W(ul_close())

# Chaos Knight
W(hero_header("Chaos Knight"))
W(ability("Phantasm", slug="chaos_knight_phantasm"))
W(ul_open())
W(li("Phantasm Damage increased from 50/75/100% to 60/80/100%", b([50, 75, 100], [60, 80, 100])))
W(ul_close())

# Clinkz
W(hero_header("Clinkz"))
W(ability("Death Pact", slug="clinkz_death_pact"))
W(ul_open())
W(li("Mana Cost decreased from 60 to 50", b(60, 50, l=True)))
W(ul_close())

# Clockwerk
W(hero_header("Clockwerk"))
W(ability("Power Cogs", slug="rattletrap_power_cogs"))
W(ul_open())
W(li("Pushback and damage now apply against heroes with no mana", t("BUFF"), extra=inline_note("Targets Huskar in particular — previously Power Cogs had no effect on him at all, as he has no mana to drain.")))
W(li("Mana Cost increased from 60/65/70/75 to 75", b([60, 65, 70, 75], 75, l=True)))
W(li("Damage rescaled from 50/125/200/275 to 55/110/165/220", b([50, 125, 200, 275], [55, 110, 165, 220])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Hookshot Cooldown Reduction decreased from 10s to 8s", b(10, 8)))
W(ul_close())

# Dark Seer
W(hero_header("Dark Seer"))
W(ul_open())
W(li("Base Health Regen increased by 0.5", bstat_h("Dark Seer", "StatusHealthRegen", "7.41c", 0.5), extra=note_box(hero="Dark Seer", field="StatusHealthRegen", before_patch="7.41c")))
W(ul_close())

# Dark Willow
W(hero_header("Dark Willow"))
W(ul_open())
W(li("Base Intelligence increased from 21 to 22", b(21, 22)))
W(li("Damage at level 1 increased by 1 (from 48-56 to 49-57)", br(48, 56, 49, 57)))
W(ul_close())
W(ability("Cursed Crown", slug="dark_willow_cursed_crown"))
W(ul_open())
W(li("Cast Range increased from 600/625/650/675 to 700", b([600, 625, 650, 675], 700)))
W(ul_close())

# Dawnbreaker
W(hero_header("Dawnbreaker"))
W(ability("Starbreaker", slug="dawnbreaker_fire_wreath"))
W(ul_open())
W(li("Mana Cost increased from 100 to 110", b(100, 110, l=True)))
W(ul_close())

# Dazzle
W(hero_header("Dazzle"))
W(ability("Poison Touch", slug="dazzle_poison_touch"))
W(ul_open())
W(li("Bonus Slow Per Hit increased from 2/2.5/3/3.5% to 2.5/3/3.5/4%", b([2, 2.5, 3, 3.5], [2.5, 3, 3.5, 4])))
W(ul_close())

# Disruptor
W(hero_header("Disruptor"))
W(ul_open())
W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
W(ul_close())
W(ability("Thunder Strike", slug="disruptor_thunder_strike"))
W(ul_open())
W(li("Mana Cost decreased from 125/130/135/140 to 115/120/125/130", b([125, 130, 135, 140], [115, 120, 125, 130], l=True)))
W(ul_close())

# Doom
W(hero_header("Doom"))
W(ul_open())
W(li("Intelligence gain increased from 1.9 to 2.1", b(1.9, 2.1)))
W(ul_close())
W(ability("Devour", slug="doom_bringer_devour"))
W(ul_open())
W(li("Aghanim's Shard bonus AoE decreased from 20% to 15%", b(20, 15)))
W(ul_close())

# Dragon Knight
W(hero_header("Dragon Knight"))
W(ability("Dragon Tail", slug="dragon_knight_dragon_tail"))
W(ul_open())
W(li("AoE increased from 25 to 50", b(25, 50)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Breathe Fire Damage increased from +200 to +220", b(200, 220)))
W(ul_close())

# Earth Spirit
W(hero_header("Earth Spirit"))
W(ability("Stone Remnant", slug="earth_spirit_stone_caller"))
W(ul_open())
W(li("Passive bonus damage per unused charge increased from 2.5% to 3%", b(2.5, 3)))
W(ul_close())

# Earthshaker
W(hero_header("Earthshaker"))
W(ul_open())
W(li("Base Mana Regen increased by 0.25", bstat_h("Earthshaker", "StatusManaRegen", "7.41c", 0.25), extra=note_box(hero="Earthshaker", field="StatusManaRegen", before_patch="7.41c")))
W(ul_close())

# Elder Titan
W(hero_header("Elder Titan"))
W(ability("Natural Order", slug="elder_titan_natural_order"))
W(ul_open())
W(li("Radius increased from 350 to 375", b(350, 375)))
W(ul_close())
W(ability("Earth Splitter", slug="elder_titan_earth_splitter"))
W(ul_open())
W(li("Movement Slow increased from 30/40/50% to 40/45/50%", b([30, 40, 50], [40, 45, 50])))
W(ul_close())

# Ember Spirit
W(hero_header("Ember Spirit"))
W(ability("Sleight of Fist", slug="ember_spirit_sleight_of_fist"))
W(ul_open())
W(li("Bonus Hero Damage decreased from 50/90/130/170 to 40/80/120/160", b([50, 90, 130, 170], [40, 80, 120, 160])))
W(ul_close())

# Enigma
W(hero_header("Enigma"))
W(ability("Demonic Summoning", slug="enigma_demonic_conversion"))
W(ul_open())
W(li("Cooldown rescaled from 40/38/36/34s to 45/40/35/30s", b([40, 38, 36, 34], [45, 40, 35, 30], l=True)))
W(ul_close())

# Faceless Void
W(hero_header("Faceless Void"))
W(ability("Time Walk", slug="faceless_void_time_walk"))
W(ul_open())
W(li("Aghanim's Scepter Time Lock radius decreased from 400 to 325", b(400, 325)))
W(ul_close())
W(ability("Time Dilation", slug="faceless_void_time_dilation"))
W(ul_open())
W(li("Radius decreased from 775 to 700", b(775, 700)))
W(ul_close())

# Grimstroke
W(hero_header("Grimstroke"))
W(ability("Dark Portrait", slug="grimstroke_dark_portrait"))
W(ul_open())
W(li("Magic Resistance decreased from 95% to 90%", b(95, 90)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Attacks to Destroy Phantom decreased from +3 to +2", b(3, 2)))
W(ul_close())

# Gyrocopter
W(hero_header("Gyrocopter"))
W(ul_open())
W(li("Night Vision increased from 800 to 1000", b(800, 1000)))
W(ul_close())
W(ability("Flak Cannon", slug="gyrocopter_flak_cannon"))
W(ul_open())
W(li("No longer provides 200 Bonus Night Vision", t("DEL")))
W(ul_close())
W(ability("Call Down", slug="gyrocopter_call_down"))
W(ul_open())
W(li("Missile Slow increased from 50% to 60%", b(50, 60)))
W(ul_close())
W(ability("Side Gunner", slug="gyrocopter_side_gunner_spawn_ability"))
W(ul_open())
W(li("No longer attacks 2 units at a time while Flak Cannon is active", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Flak Cannon Cooldown Reduction increased from 4s to 6s", b(4, 6)))
W(ul_close())

# Hoodwink
W(hero_header("Hoodwink"))
W(ability("Acorn Shot", slug="hoodwink_acorn_shot"))
W(ul_open())
W(li("Cooldown increased from 16/14/12/10s to 19/16/13/10s", b([16, 14, 12, 10], [19, 16, 13, 10], l=True)))
W(ul_close())
W(ability("Scurry", slug="hoodwink_scurry"))
W(ul_open())
W(li("Bonus Movement Speed decreased from 20/25/30/35% to 15/20/25/30%", b([20, 25, 30, 35], [15, 20, 25, 30])))
W(ul_close())

# Huskar
W(hero_header("Huskar"))
W(ability("Burning Spear", slug="huskar_burning_spear"))
W(ul_open())
W(li("Burn Damage decreased from 5/10/15/20 to 4/8/12/16", b([5, 10, 15, 20], [4, 8, 12, 16])))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(ability("Ghost Walk", slug="invoker_ghost_walk"))
W(ul_open())
W(li("Cooldown increased from 32s to 40s", b(32, 40, l=True)))
W(ul_close())
W(ability("Chaos Meteor", slug="invoker_chaos_meteor"))
W(ul_open())
W(li("Contact Damage decreased from 55/80/105/130/155/180/205/220/235 to 55/75/95/115/135/155/175/195/215", b([55, 80, 105, 130, 155, 180, 205, 220, 235], [55, 75, 95, 115, 135, 155, 175, 195, 215])))
W(ul_close())
W(ability("Ice Wall", slug="invoker_ice_wall"))
W(ul_open())
W(li("Movement Slow rescaled from 20/40/60/80/100/120/140/160/180% to 30/45/60/75/90/105/120/135/150%", b([20, 40, 60, 80, 100, 120, 140, 160, 180], [30, 45, 60, 75, 90, 105, 120, 135, 150])))
W(ul_close())

# Jakiro
W(hero_header("Jakiro"))
W(ul_open())
W(li("Base Intelligence increased from 25 to 26", b(25, 26)))
W(li("Damage at level 1 increased by 1 (from 52-60 to 53-61)", br(52, 60, 53, 61)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Ice Path Damage increased from +75 to +100", b(75, 100)))
W(li("Level 25 Talent Liquid Frost and Fire Max Health Damage increased from +3% to +3.5%", b(3, 3.5)))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
W(ability("Blade Fury", slug="juggernaut_blade_fury"))
W(ul_open())
W(li("Mana Cost decreased from 120 to 110", b(120, 110, l=True)))
W(ul_close())

# Kez
W(hero_header("Kez"))
W(ability("Switch Discipline", slug="kez_switch_weapons"))
W(ul_open())
W(li("Katana Bonus Agility Base Damage decreased from 16% to 12%", b(16, 12)))
W(ul_close())
W(ability("Kazurai Katana", slug="kez_kazurai_katana"))
W(ul_open())
W(li("Cooldown increased from 20/15/10/5s to 24/18/12/6s", b([20, 15, 10, 5], [24, 18, 12, 6], l=True)))
W(ul_close())
W(ability("Shodo Sai", slug="kez_shodo_sai"))
W(ul_open())
W(li("Cooldown increased from 20/15/10/5s to 24/18/12/6s", b([20, 15, 10, 5], [24, 18, 12, 6], l=True)))
W(li("Parry Duration decreased from 2s to 1.5s", b(2, 1.5)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +12% Magic Resistance replaced with +6% Switch Discipline Swap Bonuses", t("REWORK"), extra=inline_note("Katana Swap Bonus Damage from 12% to 18%. Sai Swap Movement Speed from 12% to 18%")))
W(ul_close())

# Largo
W(hero_header("Largo"))
W(ability("Encore", slug="largo_encore"))
W(ul_open())
W(li_formula("Bonus Duration increased",
             "10% + 1% per level", "15% + 1% per level",
             lambda L: 10 + 1 * L, lambda L: 15 + 1 * L))
W(ul_close())
W(ability("Amphibian Rhapsody", slug="largo_amphibian_rhapsody"))
W(ul_open())
W(li("Song Mana Costs increased from 20/32/44 to 25/35/45", b([20, 32, 44], [25, 35, 45], l=True)))
W(ul_close())

# Legion Commander
W(hero_header("Legion Commander"))
W(ability("Duel", slug="legion_commander_duel"))
W(ul_open())
W(li("Mana Cost increased from 75 to 80/100/120", b(75, [80, 100, 120], l=True)))
W(ul_close())

# Leshrac
W(hero_header("Leshrac"))
W(ability("Pulse Nova", slug="leshrac_pulse_nova"))
W(ul_open())
W(li("Mana/Sec decreased from 25/45/65 to 20/40/60", b([25, 45, 65], [20, 40, 60], l=True)))
W(ul_close())
W(ability("Nihilism", slug="leshrac_greater_lightning_storm"))
W(ul_open())
W(li("Slow increased from 30% to 40%", b(30, 40)))
W(ul_close())

# Lina
W(hero_header("Lina"))
W(ability("Dragon Slave", slug="lina_dragon_slave"))
W(ul_open())
W(li("Mana Cost decreased from 100/110/120/130 to 90/100/110/120", b([100, 110, 120, 130], [90, 100, 110, 120], l=True)))
W(ul_close())

# Lion
W(hero_header("Lion"))
W(ability("Finger of Death", slug="lion_finger_of_death"))
W(ul_open())
W(li("Damage per kill decreased from 30 to 25", b(30, 25)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Hex Cooldown Reduction decreased from 2.5s to 2s", b(2.5, 2)))
W(ul_close())

# Lone Druid (Spirit Bear changes — id 1961 — folded into Lone Druid)
W(hero_header("Lone Druid"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Movement Speed decreased from +20 to +15", b(20, 15)))
W(ul_close())
W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
W(ul_open())
W(li("Base Health Regen decreased by 1.5", b(3, 1.5), extra=note_box(prev_val=3, new_val=1.5, prev_patch="7.40")))
W(ul_close())

# Marci
W(hero_header("Marci"))
W(ability("Special Delivery", slug="marci_special_delivery"))
W(ul_open())
W(li_formula("Cooldown decreased",
             "245s − 5s per level", "215s − 5s per level",
             lambda L: 245 - 5 * L, lambda L: 215 - 5 * L, l=True))
W(ul_close())
W(ability("Bodyguard", slug="marci_bodyguard"))
W(ul_open())
W(li("Mana Cost decreased from 60/65/70/75 to 60", b([60, 65, 70, 75], 60, l=True)))
W(ul_close())

# Mars
W(hero_header("Mars"))
W(ability("Dauntless", slug="mars_dauntless"))
W(ul_open())
W(li("Radius increased from 700 to 900", b(700, 900)))
W(ul_close())
W(ability("God's Rebuke", slug="mars_gods_rebuke"))
W(ul_open())
W(li("Now turns Mars in the cast direction when cast with Bulwark toggled on", t("QoL")))
W(ul_close())
W(ability("Arena Of Blood", slug="mars_arena_of_blood"))
W(ul_open())
W(li("Spear Damage increased from 80/160/240 to 80/170/260", b([80, 160, 240], [80, 170, 260])))
W(ul_close())

# Mirana
W(hero_header("Mirana"))
W(ability("Celestial Quiver", slug="mirana_celestial_quiver"))
W(ul_open())
W(li_formula("Max Charges increased",
             "2 + 1 per 7 levels", "2 + 1 per 6 levels",
             lambda L: 2 + L // 7, lambda L: 2 + L // 6,
             levels=[1, 6, 7, 12, 14, 18, 21, 24, 28, 30]))
W(ul_close())
W(ability("Starstorm", slug="mirana_starfall"))
W(ul_open())
W(li("Second Meteor Damage increased from 70% to 80%", b(70, 80)))
W(ul_close())

# Morphling
W(hero_header("Morphling"))
W(ul_open())
W(li("Base Strength decreased from 23 to 16", b(23, 16)))
W(li("Base Agility increased from 24 to 33", b(24, 33)))
W(li("Damage at level 1 increased by 9 (from 36-45 to 45-54)", br(36, 45, 45, 54)))
W(ul_close())
W(ability("Ebb and Flow", slug="morphling_ebb_and_flow"))
W(ul_open())
W(li("Agility to Attack Range increased from 20% to 25%", b(20, 25)))
W(li("Strength to Cast Range increased from 20% to 25%", b(20, 25)))
W(li("Strength to Slow Resistance increased from 20% to 25%", b(20, 25)))
W(ul_close())
W(ability("Morph", slug="morphling_replicate"))
W(ul_open())
W(li("Aghanim's Scepter illusion incoming damage decreased from 300% to 200%", b(300, 200, l=True)))
W(ul_close())

# Nature's Prophet
W(hero_header("Nature's Prophet"))
W(ability("Spirit of the Forest", slug="furion_spirit_of_the_forest"))
W(ul_open())
W(li("Treants that are alive now always contribute to the bonus damage, even if they are out of range", t("BUFF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Sprout Damage increased from +220 to +240", b(220, 240)))
W(ul_close())

# Night Stalker
W(hero_header("Night Stalker"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Dark Ascension Cooldown Reduction decreased from 40s to 35s", b(40, 35)))
W(ul_close())

# Ogre Magi
W(hero_header("Ogre Magi"))
W(ul_open())
W(li("Base Strength increased from 25 to 26", b(25, 26)))
W(li("Damage at level 1 increased by 1 (from 70-76 to 71-77)", br(70, 76, 71, 77)))
W(ul_close())

# Omniknight
W(hero_header("Omniknight"))
W(ul_open())
W(li("Base Intelligence increased from 16 to 18", b(16, 18)))
W(ul_close())

# Outworld Destroyer
W(hero_header("Outworld Destroyer"))
W(ul_open())
W(li("Min Base damage increased by 4", bstat_h("Outworld Destroyer", "AttackDamageMin", "7.41c", 4)))
W(li("Max Base damage increased by 1", bstat_h("Outworld Destroyer", "AttackDamageMax", "7.41c", 1)))
W(li("Damage at level 1 increased from 49-61 to 53-62", br(49, 61, 53, 62), extra=inline_note("Damage spread decreased from 12 to 9")))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ul_open())
W(li("Base Agility decreased from 18 to 17", b(18, 17)))
W(li("Damage at level 1 decreased from 50-56 to 49-55", br(50, 56, 49, 55)))
W(li("Base Armor decreased by 1", bstat_h("Pangolier", "ArmorPhysical", "7.41c", -1), extra=note_box(hero="Pangolier", field="ArmorPhysical", before_patch="7.41c")))
W(ul_close())

# Phoenix
W(hero_header("Phoenix"))
W(ability("Fire Spirits", slug="phoenix_fire_spirits"))
W(ul_open())
W(li("Attack Speed Slow decreased from 50/80/110/140 to 35/70/105/140", b([50, 80, 110, 140], [35, 70, 105, 140])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Max Health Sun Ray Damage decreased from +1.5% to +1.25%", b(1.5, 1.25)))
W(ul_close())

# Puck
W(hero_header("Puck"))
W(ul_open())
W(li("Agility gain decreased from 2.3 to 2.1", b(2.3, 2.1)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Illusory Orb Damage decreased from +40 to +35", b(40, 35)))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(ul_open())
W(li("Base Agility increased from 11 to 13", b(11, 13)))
W(ul_close())

# Pugna
W(hero_header("Pugna"))
W(ul_open())
W(li("Base Mana Regen increased by 0.25", bstat_h("Pugna", "StatusManaRegen", "7.41c", 0.25), extra=note_box(hero="Pugna", field="StatusManaRegen", before_patch="7.41c")))
W(ul_close())
W(ability("Nether Ward", slug="pugna_nether_ward"))
W(ul_open())
W(li("Cast Range increased from 150 to 175", b(150, 175)))
W(ul_close())

# Razor
W(hero_header("Razor"))
W(ul_open())
W(li("Base Attack Speed increased from 100 to 110", b(100, 110)))
W(ul_close())

# Riki
W(hero_header("Riki"))
W(ability("Backstab", slug="riki_innate_backstab"))
W(ul_open())
W(li("Effectiveness on allies increased from 25% to 30%", b(25, 30)))
W(ul_close())
W(ability("Smoke Screen", slug="riki_smoke_screen"))
W(ul_open())
W(li("Cooldown rescaled from 17/15/13/11s to 15/14/13/12s", b([17, 15, 13, 11], [15, 14, 13, 12], l=True)))
W(ul_close())
W(ability("Blink Strike", slug="riki_blink_strike"))
W(ul_open())
W(li("Bonus Damage rescaled from 15/30/45/60 to 25/35/45/55", b([15, 30, 45, 60], [25, 35, 45, 55])))
W(ul_close())

# Ringmaster
W(hero_header("Ringmaster"))
W(ability("Funhouse Mirror", slug="ringmaster_funhouse_mirror"))
W(ul_open())
W(li("Proportion Distortion Illusion damage increased from 28% to 100%", b(28, 100)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Wheel of Wonder Radius and Range increased from +100 to +150", b(100, 150)))
W(ul_close())

# Rubick
W(hero_header("Rubick"))
W(ability("Fade Bolt", slug="rubick_fade_bolt"))
W(ul_open())
W(li("Damage decreased from 100/175/250/325 to 85/165/245/325", b([100, 175, 250, 325], [85, 165, 245, 325])))
W(li("Debuff Duration decreased from 10s to 9s", b(10, 9)))
W(ul_close())

# Sand King
W(hero_header("Sand King"))
W(ul_open())
W(li("Strength gain increased from 2.3 to 2.5", b(2.3, 2.5)))
W(li("Damage gain per level increased from 2.8 to 2.9", b(2.8, 2.9)))
W(ul_close())

# Shadow Demon
W(hero_header("Shadow Demon"))
W(ability("Shadow Poison", slug="shadow_demon_shadow_poison"))
W(ul_open())
W(li("Mana Cost decreased from 45 to 40", b(45, 40, l=True)))
W(li("Damage per additional stack over 5 stacks increased from 50 to 60", b(50, 60)))
W(ul_close())

# Shadow Shaman
W(hero_header("Shadow Shaman"))
W(ability("Mass Serpent Ward", slug="shadow_shaman_mass_serpent_ward"))
W(ul_open())
W(li("Gold Bounty decreased from 22-30 to 20-26", br(22, 30, 20, 26, l=True)))
W(ul_close())
W(ability("Urnaconda", slug="shadow_shaman_urnaconda"))
W(ul_open())
W(li("Mana Cost increased from 115 to 140", b(115, 140, l=True)))
W(ul_close())

# Skywrath Mage
W(hero_header("Skywrath Mage"))
W(ul_open())
W(li("Base Strength increased from 21 to 22", b(21, 22)))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ability("Corrosive Haze", slug="slardar_amplify_damage"))
W(ul_open())
W(li("Armor Reduction decreased from 10/15/20 to 8/14/20", b([10, 15, 20], [8, 14, 20])))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(ability("Saltwater Shiv", slug="slark_saltwater_shiv"))
W(ul_open())
W(li("Cooldown decreased from 14/12/10/8s to 12/10.5/9/7.5s", b([14, 12, 10, 8], [12, 10.5, 9, 7.5], l=True)))
W(ul_close())

# Snapfire
W(hero_header("Snapfire"))
W(ability("Boomstick", slug="snapfire_boomstick"))
W(ul_open())
W(li("No longer applies on denies or buildings", t("DEL")))
W(ul_close())
W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
W(ul_open())
W(li("Aghanim's Shard heal amount decreased from 200 to 175", b(200, 175)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Firesnap Cookie Cooldown Reduction decreased from 4s to 3s", b(4, 3)))
W(ul_close())

# Sniper
W(hero_header("Sniper"))
W(ability("Keen Scope", slug="sniper_keen_scope"))
W(ul_open())
W(li("No longer applies on denies or buildings", t("DEL")))
W(ul_close())

# Spectre
W(hero_header("Spectre"))
W(ul_open())
W(li("Base Strength increased from 21 to 22", b(21, 22)))
W(li("Agility gain decreased from 2.4 to 2.3", b(2.4, 2.3)))
W(ul_close())
W(ability("Spectral Dagger", slug="spectre_spectral_dagger"))
W(ul_open())
W(li("Movement Speed Change rescaled from 10/14/18/22% to 14/16/18/20%", b([10, 14, 18, 22], [14, 16, 18, 20])))
W(ul_close())
W(ability("Shadow Step", slug="spectre_shadow_step"))
W(ul_open())
W(li("Illusion Damage Taken rescaled from 200/185/170/155% to 175%", b([200, 185, 170, 155], 175, l=True)))
W(li("Cast Range rescaled from 825/950/1075/1200 to 1000", b([825, 950, 1075, 1200], 1000)))
W(ul_close())
W(ability("Haunt", slug="spectre_haunt"))
W(ul_open())
W(li("Mana Cost increased from 125/150/175 to 125/175/225", b([125, 150, 175], [125, 175, 225], l=True)))
W(li("Aghanim's Scepter fear duration increased from 1.5s to 2s", b(1.5, 2)))
W(ul_close())

# Spirit Breaker
W(hero_header("Spirit Breaker"))
W(ability("Charge of Darkness", slug="spirit_breaker_charge_of_darkness"))
W(ul_open())
W(li("Mana Cost decreased from 90/100/110/120 to 80/90/100/110", b([90, 100, 110, 120], [80, 90, 100, 110], l=True)))
W(ul_close())
W(ability("Greater Bash", slug="spirit_breaker_greater_bash"))
W(ul_open())
W(li("Aghanim's Scepter creep damage decreased from 25% to 20%", b(25, 20)))
W(ul_close())

# Storm Spirit
W(hero_header("Storm Spirit"))
W(ul_open())
W(li("Base Attack Speed decreased from 115 to 110", b(115, 110)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent 2x Overload Attack Bounce damage decreased from 65% to 50%", b(65, 50)))
W(ul_close())

# Sven
W(hero_header("Sven"))
W(ability("Storm Hammer", slug="sven_storm_bolt"))
W(ul_open())
W(li("Stun Duration increased from 1/1.2/1.4/1.6s to 1/1.25/1.5/1.75s", b([1, 1.2, 1.4, 1.6], [1, 1.25, 1.5, 1.75])))
W(ul_close())
W(ability("God's Strength", slug="sven_gods_strength"))
W(ul_open())
W(li("Slow Resistance increased from 30% to 40%", b(30, 40)))
W(ul_close())

# Techies
W(hero_header("Techies"))
W(ability("Reactive Tazer", slug="techies_reactive_tazer"))
W(ul_open())
W(li("Disarm duration decreased from 2.4/2.7/3/3.3s to 2.25/2.5/2.75/3s", b([2.4, 2.7, 3, 3.3], [2.25, 2.5, 2.75, 3])))
W(ul_close())
W(ability("Proximity Mines", slug="techies_land_mines"))
W(ul_open())
W(li("Debuff Duration decreased from 5s to 4s", b(5, 4)))
W(ul_close())

# Templar Assassin
W(hero_header("Templar Assassin"))
W(ability("Inner Peace", slug="templar_assassin_inner_peace"))
W(ul_open())
W(li("Time until meditation starts decreased from 0.25s to 0.2s", b(0.25, 0.2, l=True)))
W(li_formula("Meditation Time Until Max Bonus decreased",
             "2.05s − 0.05s per level", "1.85s − 0.05s per level",
             lambda L: 2.05 - 0.05 * L, lambda L: 1.85 - 0.05 * L, l=True))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Psionic Trap Slow increased from +10% to +15%", b(10, 15)))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ul_open())
W(li("Base Attack Speed decreased from 100 to 90", b(100, 90)))
W(ul_close())
W(ability("Whirling Death", slug="shredder_whirling_death"))
W(ul_open())
W(li("Stat Loss Duration decreased from 11/12/13/14s to 7/9/11/13s", b([11, 12, 13, 14], [7, 9, 11, 13])))
W(ul_close())
W(ability("Flamethrower", slug="shredder_flamethrower"))
W(ul_open())
W(li("Move Slow increased from 30% to 40%", b(30, 40)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Chakram Slow increased from +5% to +6%", b(5, 6)))
W(li("Level 20 Talent Exposure Therapy Heals Per Tree Destroyed increased from 10 to 12", b(10, 12)))
W(ul_close())

# Tiny
W(hero_header("Tiny"))
W(ability("Insurmountable", slug="tiny_insurmountable"))
W(ul_open())
W(li("Strength to Slow Resist decreased from 20% to 15%", b(20, 15)))
W(ul_close())
W(ability("Toss", slug="tiny_toss"))
W(ul_open())
W(li("Flight time decreased from 1.25s to 1.1s", b(1.25, 1.1)))
W(ul_close())
W(ability("Tree Grab", slug="tiny_tree_grab"))
W(ul_open())
W(li("Cooldown increased from 15/12/9/6s to 16/13/10/7s", b([15, 12, 9, 6], [16, 13, 10, 7], l=True)))
W(ul_close())
W(ability("Tree Throw", slug="tiny_toss_tree"))
W(ul_open())
W(li("Cast Range decreased from 1200 to 1000", b(1200, 1000)))
W(ul_close())
W(ability("Grow", slug="tiny_grow"))
W(ul_open())
W(li("Aghanim's Shard movement slow increased from 25% to 35%", b(25, 35)))
W(li("Aghanim's Shard slow duration increased from 2.5s to 3s", b(2.5, 3)))
W(ul_close())
W(ability("Tree Volley", slug="tiny_tree_channel"))
W(ul_open())
W(li("Mana Cost decreased from 200 to 150", b(200, 150, l=True)))
W(ul_close())

# Troll Warlord
W(hero_header("Troll Warlord"))
W(ability("Battle Trance", slug="troll_warlord_battle_trance"))
W(ul_open())
W(li("Movement Speed increased from 25/30/35% to 35%", b([25, 30, 35], 35)))
W(ul_close())

# Undying
W(hero_header("Undying"))
W(ul_open())
W(li("Base Mana Regen increased by 0.25", bstat_h("Undying", "StatusManaRegen", "7.41c", 0.25), extra=note_box(hero="Undying", field="StatusManaRegen", before_patch="7.41c")))
W(ul_close())

# Vengeful Spirit
W(hero_header("Vengeful Spirit"))
W(ul_open())
W(li("Base Health Regen increased by 0.5", bstat_h("Vengeful Spirit", "StatusHealthRegen", "7.41c", 0.5), extra=note_box(hero="Vengeful Spirit", field="StatusHealthRegen", before_patch="7.41c")))
W(ul_close())
W(ability("Magic Missile", slug="vengefulspirit_magic_missile"))
W(ul_open())
W(li("Damage increased from 85/170/255/340 to 100/180/260/340", b([85, 170, 255, 340], [100, 180, 260, 340])))
W(ul_close())

# Venomancer
W(hero_header("Venomancer"))
W(ul_open())
W(li("Intelligence gain increased from 1.8 to 1.9", b(1.8, 1.9)))
W(li("Damage gain per level increased from 3.0 to 3.1", b(3.0, 3.1)))
W(ul_close())

# Visage
W(hero_header("Visage"))
W(ability("Grave Chill", slug="visage_grave_chill"))
W(ul_open())
W(li("Attack Speed Drain rescaled from 25/40/55/70 to 35/45/55/65", b([25, 40, 55, 70], [35, 45, 55, 65])))
W(ul_close())

# Warlock
W(hero_header("Warlock"))
W(ability("Upheaval", slug="warlock_upheaval"))
W(ul_open())
W(li("Cooldown decreased from 60/50/40/30s to 45/40/35/30s", b([60, 50, 40, 30], [45, 40, 35, 30], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Fatal Bonds Targets increased from +4 to +5", b(4, 5)))
W(ul_close())

# Weaver
W(hero_header("Weaver"))
W(ability("Threads of Fate", slug="weaver_threads_of_fate"))
W(ul_open())
W(li("Slow Duration increased from 0.2s to 0.4s", b(0.2, 0.4)))
W(ul_close())

# Winter Wyvern
W(hero_header("Winter Wyvern"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Damage decreased from +35 to +30", b(35, 30)))
W(li("Level 20 Talent Arctic Burn Slow decreased from +15% to +10%", b(15, 10)))
W(ul_close())

# Wraith King
W(hero_header("Wraith King"))
W(ul_open())
W(li("Base Damage increased by 2", bstat_h("Wraith King", "AttackDamageMin", "7.41c", 2)))
W(li("Damage at level 1 increased from 60-62 to 62-64", br(60, 62, 62, 64)))
W(ul_close())
W(ability("Vampiric Spirit", slug="skeleton_king_vampiric_spirit"))
W(ul_open())
W(li_formula("Lifesteal rescaled",
             "14% + 1% per level", "20% + 0.5% per level",
             lambda L: 14 + 1 * L, lambda L: 20 + 0.5 * L))
W(ul_close())
W(ability("Reincarnation", slug="skeleton_king_reincarnation"))
W(ul_open())
W(li("Aghanim's Scepter cooldown increased from 165/135/105s to 170/140/110s", b([165, 135, 105], [170, 140, 110], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Vampiric Spirit Lifesteal decreased from +10% to +8%", b(10, 8)))
W(ul_close())

write_footer()
save_html('patches/7.41d.html')

# ============================================================
# 7.41c content
# ============================================================
save_assets()
write_head("7.41c", "06.05.2026")

# 7.41c content is HANDCRAFTED — preserves manual corrections, formula tables,
# wrong-line/wrong-word annotations and subnotes that auto-gen can't produce.
# 7.41c content was originally raw HTML — converted to W() calls
# via _convert_handcrafted.py. Special inline HTML preserved as W('''...''').
W(section("General Updates"))
W(plain_header("Mechanics"))
W(ul_open())
W(li("Units with flying vision no longer ignore vision restrictions of Roshan's pits. They can no longer see into them from outside and vice versa", t("NERF")))
W(ul_close())
W(subnote("Affects Clockwerk during Jetpack, Drow Ranger's Glacier, Monkey King during Tree Dance, Night Stalker during Dark Ascension, Treant Protector's Eyes in the Forest, and Visage's Familiars"))
W(plain_header("Map Objectives"))
W(subgroup("Tormentor"))
W(ul_open())
W(li("Alleviation: Max health regen increased from 2% to 2.25%", b(2, 2.25)))
W(li("Alleviation: Duration increased from 10s to 15s", b(10, 15)))
W(ul_close())
W(section("Item Updates"))
W(item_header("Bloodstone"))
W(ul_open())
W(li(
    '<span class="wrong-word">Health bonus increased from +600 to +625</span>',
    '<span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span>',
    extra=note_box('This change is wrongly stated. The real change is 650 → 625 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span></span>'),
    force_tag="nerf"
))
W(li("Bloodpact cooldown increased from 30s to 35s", b(30, 35, l=True)))
W(li("Spell Weakness Aura damage from spells taken decreased from 12% to 10%", b(12, 10)))
W(ul_close())
W(item_header("Boots of Bearing"))
W(ul_open())
W(li("Swiftness Aura allied movement speed decreased from 20 to 15", b(20, 15)))
W(ul_close())
W(item_header("Crella's Crozier"))
W(ul_open())
W(li("Rite of Rumusque movement speed steal increased from 5% to 6%", b(5, 6)))
W(ul_close())
W(item_header("Disperser"))
W(ul_open())
W(li("Suppress duration decreased from 5s to 4s", b(5, 4)))
W(ul_close())
W(item_header("Essence Distiller"))
W(ul_open())
W(li("Soul Release radius when ground targeted increased from 400 to 450", b(400, 450)))
W(ul_close())
W(item_header("Harpoon"))
W(ul_open())
W(li("Draw Forth can no longer move the Harpoon caster if they are rooted/leashed/bound", t("NERF")))
W(ul_close())
W(subnote("Still affects rooted/leashed/bound targets"))
W(item_header("Heart of Tarrasque"))
W(ul_open())
W(li("Recipe cost increased from 600 to 700", b(600, 700, l=True)))
W(li("Total cost increased from 5100g to 5200g", b(5100, 5200, l=True)))
W(ul_close())
W(item_header("Mage Slayer"))
W(ul_open())
W(li("Mage Slayer damage per second decreased from 40 to 35", b(40, 35)))
W(ul_close())
W(item_header("Silver Edge"))
W(ul_open())
W(li("Shadow Walk bonus movement speed decreased from 25% to 22%", b(25, 22)))
W(li("Shadow Walk cooldown increased from 20s to 22s", b(20, 22, l=True)))
W(ul_close())
W(item_header("Shiva's Guard"))
W(ul_open())
W(li("Freezing Aura attack speed reduction decreased from 45 to 40", b(45, 40)))
W(ul_close())
W(item_header("Soul Ring"))
W(ul_open())
W(li("Cooldown increased from 25s to 30s", b(25, 30, l=True)))
W(ul_close())
W(item_header("Specialist's Array"))
W(ul_open())
W(li("Agility bonus increased from +12 to +15", b(12, 15)))
W(ul_close())
W(section("Neutral Item Updates"))
W(enchant_header("Crude", "crude"))
W(ul_open())
W(li("Intelligence penalty increased from 6% to 9%", b(6, 9, l=True)))
W(ul_close())
W(enchant_header("Greedy", "greedy"))
W(ul_open())
W(li("Mana bonus decreased from 200/250 to 150/200", b([200, 250], [150, 200])))
W(ul_close())
W(enchant_header("Tough", "tough"))
W(ul_open())
W(li("Damage bonus decreased from +7/10/13/16 to +6/9/12/15", b([7, 10, 13, 16], [6, 9, 12, 15])))
W(ul_close())
W(section("Hero Updates"))
W(hero_header("Abaddon"))
W(ul_open())
W(li("Base Intelligence increased by 1", bstat_h("Abaddon", "AttributeBaseIntelligence", "7.41b", 1), extra=note_box(hero="Abaddon", field="AttributeBaseIntelligence", before_patch="7.41b", extra_note="Damage at level 1 unchanged at 49-59")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Curse of Avernus DPS increased from +25 to +30", b(25, 30)))
W(ul_close())
W(hero_header("Alchemist"))
W(subgroup("Abilities"))
W(ability("Greevil's Greed", slug="alchemist_goblins_greed"))
W(ul_open())
W(li("Bonus base/max Extra Gold per melted Scepter decreased from +6 to +3", b(6, 3)))
W(ul_close())
W(ability("Acid Spray"))
W(ul_open())
W(li("Cooldown rescaled from 22/21/20/19s to 21s", b([22, 21, 20, 19], 21, l=True)))
W(ul_close())
W(ability("Chemical Rage"))
W(ul_open())
W(li("Bonus Health Regen decreased from 60/90/120 to 50/85/120", b([60, 90, 120], [50, 85, 120])))
W(ul_close())
W(hero_header("Ancient Apparition"))
W(subgroup("Abilities"))
W(ability("Ice Blast"))
W(ul_open())
W(li("Path Radius increased from 275 to 300", b(275, 300)))
W(li("Base Area of Effect Radius increased from 275 to 300", b(275, 300)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20: Chilling Touch Damage increased from +80 to +100", b(80, 100)))
W(ul_close())
W(hero_header("Anti-Mage"))
W(subgroup("Abilities"))
W(ability("Persecutor", slug="antimage_persectur"))
W(ul_open())
W(li("Minimum mana threshold for slow improved from 50% to 60%", b(50, 60)))
W(ul_close())
W(hero_header("Arc Warden"))
W(ul_open())
W(li("Base Agility increased from 20 to 22", b(20, 22)))
W(li("Damage at level 1 increased from 51-57 to 52-58", br(51, 57, 52, 58)))
W(ul_close())
W(hero_header("Bane"))
W(subgroup("Abilities"))
W(ability("Brain Sap"))
W(ul_open())
W(li("Mana Cost decreased from 120/130/140/150 to 105/120/135/150", b([120, 130, 140, 150], [105, 120, 135, 150], l=True)))
W(ul_close())
W(hero_header("Batrider"))
W(ul_open())
W(li("Base Movement Speed decreased from 320 to 310", b(320, 310)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Sticky Napalm"))
W(ul_open())
W(li("Aghanim's Shard building damage decreased from 25% to 20%", b(25, 20)))
W(ul_close())
W(ability("Firefly"))
W(ul_open())
W(li("Damage per second decreased from 25/50/75/100 to 20/40/60/80", b([25, 50, 75, 100], [20, 40, 60, 80])))
W(ul_close())
W(ability("Flaming Lasso"))
W(ul_open())
W(li("Total Damage decreased from 200/350/500 to 125/250/375", b([200, 350, 500], [125, 250, 375])))
W(ul_close())
W(hero_header("Beastmaster"))
W(ul_open())
W(li("Base Strength decreased from 25 to 24", b(25, 24)))
W(li("Damage at level 1 decreased from 50-54 to 49-53", br(50, 54, 49, 53)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Wild Axes"))
W(ul_open())
W(li("Mana Cost increased from 50/55/60/65 to 65", b([50, 55, 60, 65], 65, l=True)))
W(ul_close())
W(ability("Summon Razorback"))
W(ul_open())
W(li("Boar Attack Damage decreased from 30/45/60/75 to 24/41/58/75", b([30, 45, 60, 75], [24, 41, 58, 75])))
W(ul_close())
W(ability("Drums of Slom"))
W(ul_open())
W(li("Damage Radius decreased from 600 to 525", b(600, 525)))
W(li("Drum Hit Damage decreased from 80 to 70", b(80, 70)))
W(ul_close())
W(hero_header("Bounty Hunter"))
W(subgroup("Abilities"))
W(ability("Shuriken Toss"))
W(ul_open())
W(li("Mana Cost increased from 75/80/85/90 to 75/85/95/105", b([75, 80, 85, 90], [75, 85, 95, 105], l=True)))
W(ul_close())
W(ability("Shadow Walk", slug="bounty_hunter_wind_walk"))
W(ul_open())
W(li("Bonus Speed increased from 8/12/16/20% to 11/14/17/20%", b([8, 12, 16, 20], [11, 14, 17, 20])))
W(ul_close())
W(ability("Track"))
W(ul_open())
W(li("Mana Cost decreased from 60 to 50", b(60, 50, l=True)))
W(ul_close())
W(hero_header("Brewmaster"))
W(subgroup("Abilities"))
W(ability("Primal Split"))
W(ul_open())
W(li("Cancel Split now has a 3s initial cooldown", '<span class="badge qol" data-tag="qol">QoL</span>'))
W(ul_close())
W(hero_header("Bristleback"))
W(subgroup("Abilities"))
W(ability("Warpath"))
W(ul_open())
W(li("Damage per stack decreased from 15/20/25 to 12/16/20", b([15, 20, 25], [12, 16, 20])))
W(ul_close())
W(ability("Hairball"))
W(ul_open())
W(li("Cooldown increased from 13s to 15s", b(13, 15, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25: Bristleback Damage Threshold Reduction increased from 25 to 30", b(25, 30)))
W(ul_close())
W(hero_header("Broodmother"))
W(subgroup("Abilities"))
W(ability("Insatiable Hunger"))
W(ul_open())
W(li("Spiderling Radius increased from 800 to 1200", b(800, 1200)))
W(ul_close())
W(ability("Spinner's Snare", slug="broodmother_sticky_snare"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 70", b(100, 70, l=True)))
W(ul_close())
W(hero_header("Centaur Warrunner"))
W(ul_open())
W(li("Base Strength increased from 27 to 28", b(27, 28)))
W(li("Damage at level 1 increased from 63-65 to 64-66", br(63, 65, 64, 66)))
W(li("Strength gain increased from 4.2 to 4.3", b(4.2, 4.3)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25: Hoof Stomp Duration increased from +0.8s to +1.0s", b(0.8, 1)))
W(ul_close())
W(hero_header("Chaos Knight"))
W(subgroup("Abilities"))
W(ability("Chaos Strike"))
W(ul_open())
W(li("Critical Max increased from 140/180/220/260% to 150/190/230/270%", b([140, 180, 220, 260], [150, 190, 230, 270])))
W(ul_close())
W(hero_header("Dark Seer"))
W(ul_open())
W(li("Base Intelligence increased from 22 to 23", b(22, 23)))
W(li("Damage at level 1 increased from 53-59 to 54-60", br(53, 59, 54, 60)))
W(ul_close())
W(hero_header("Dark Willow"))
W(subgroup("Abilities"))
W(ability("Terrorize"))
W(ul_open())
W(li("Radius increased from 400/450/500 to 450/500/550", b([400, 450, 500], [450, 500, 550])))
W(ul_close())
W(hero_header("Dawnbreaker"))
W(ul_open())
W(li("Base Damage decreased by 1", bstat_h("Dawnbreaker", "AttackDamageMin", "7.41b", -1), extra=note_box(hero="Dawnbreaker", field="AttackDamageMin", before_patch="7.41b")))
W(li("Damage at level 1 decreased from 56-60 to 55-59", br(56, 60, 55, 59)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Solar Guardian"))
W(ul_open())
W(li("Landing Stun Duration decreased from 1.4/1.6/1.8s to 1.2/1.4/1.6s", b([1.4, 1.6, 1.8], [1.2, 1.4, 1.6])))
W(ul_close())
W(hero_header("Doom"))
W(subgroup("Abilities"))
W(ability("Scorched Earth"))
W(ul_open())
W(li("Bonus HP Regen decreased from 7/8/9/10 to 6.66", b([7, 8, 9, 10], 6.66)))
W(ul_close())
W(hero_header("Drow Ranger"))
W(subgroup("Abilities"))
W(ability("Frost Arrows"))
W(ul_open())
W(li("Bonus Damage increased from 10/15/20/25 to 12/18/24/30", b([10, 15, 20, 25], [12, 18, 24, 30])))
W(ul_close())
W(ability("Gust", slug="drow_ranger_wave_of_silence"))
W(ul_open())
W(li("Mana Cost decreased from 70 to 55", b(70, 55, l=True)))
W(ul_close())
W(hero_header("Earth Spirit"))
W(ul_open())
W(li("Base Strength increased from 22 to 23", b(22, 23)))
W(li("Damage at level 1 increased from 47-51 to 48-52", br(47, 51, 48, 52)))
W(ul_close())
W(hero_header("Elder Titan"))
W(subgroup("Abilities"))
W(ability("Echo Stomp"))
W(ul_open())
W(li("Damage increased from 60/100/140/180 to 65/110/155/200", b([60, 100, 140, 180], [65, 110, 155, 200])))
W(li("Aghanim's Shard with alt-cast no longer swaps the position if Elder Titan is rooted", t("NERF")))
W(ul_close())
W(hero_header("Ember Spirit"))
W(ul_open())
W(li("Base Strength decreased from 22 to 21", b(22, 21)))
W(ul_close())
W(hero_header("Faceless Void"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20: Time Walk Cooldown Reduction decreased from 1.25s to 1s", b(1.25, 1)))
W(li("Level 20: Attack Speed during Chronosphere decreased from +100 to +80", b(100, 80)))
W(ul_close())
W(hero_header("Gyrocopter"))
W(subgroup("Abilities"))
W(ability("Afterburner"))
W(ul_open())
W(li("Duration increased from 4s to 5s", b(4, 5)))
W(ul_close())
W(hero_header("Hoodwink"))
W(ul_open())
W(li("Base Damage increased by 3", t("MISC") + bstat_h("Hoodwink", "AttackDamageMin", "7.41b", 3), extra=note_box(hero="Hoodwink", field="AttackDamageMin", before_patch="7.41b", extra_note="Damage at level 1 unchanged at 47-54")))
W(li("Base Agility decreased from 25 to 22", b(25, 22)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Sharpshooter"))
W(ul_open())
W(li("Knockback to Hoodwink won't be applied if Hoodwink is rooted", t("NERF")))
W(ul_close())
W(hero_header("Huskar"))
W(ul_open())
W(li("Base Health Regen decreased by 0.25", t("NERF")))
W(ul_close())
W(hero_header("Invoker"))
W(ul_open())
W(li("Base Movement Speed decreased from 285 to 280", b(285, 280)))
W(ul_close())
W(hero_header("Io"))
W(subgroup("Abilities"))
W(ability("Tether"))
W(ul_open())
W(li("HP/Mana Transfer decreased from 60/80/100/120% to 55/75/95/115%", b([60, 80, 100, 120], [55, 75, 95, 115])))
W(ul_close())
W(ability("Spirits"))
W(ul_open())
W(li("Now remembers the radius of the spirits between casts", '<span class="badge qol" data-tag="qol">QoL</span>'))
W(ul_close())
W(hero_header("Jakiro"))
W(ul_open())
W(li("Strength gain increased from 2.5 to 2.6", b(2.5, 2.6)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Macropyre"))
W(ul_open())
W(li("Mana Cost decreased from 250/350/450 to 225/325/425", b([250, 350, 450], [225, 325, 425], l=True)))
W(ul_close())
W(hero_header("Juggernaut"))
W(subgroup("Abilities"))
W(ability("Blade Fury"))
W(ul_open())
W(li("Damage per second increased from 80/110/140/170 to 85/115/145/175", b([80, 110, 140, 170], [85, 115, 145, 175])))
W(ul_close())
W(hero_header("Keeper of the Light"))
W(ul_open())
W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
W(ul_close())
W(hero_header("Kunkka"))
W(subgroup("Abilities"))
W(ability("Admiral's Rum"))
W(ul_open())
W(li_formula("Cooldown decreased",
             "60.5s − 0.5s per level", "50.5s − 0.5s per level",
             lambda L: 60.5 - 0.5 * L, lambda L: 50.5 - 0.5 * L, l=True,
             value_fmt="{:g}s"))
W(ul_close())
W(hero_header("Largo"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20: +200 Catchy Lick Damage replaced with 2× Catchy Lick Charges", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(li("Level 25: 2× Catchy Lick Charges replaced with 2× Frogstomp Stomps / Interval", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(ul_close())
W(hero_header("Lich"))
W(subgroup("Abilities"))
W(ability("Sinister Gaze"))
W(ul_open())
W(li("Mana Drain per second increased from 20% to 25%", b(20, 25)))
W(ul_close())
W(hero_header("Lina"))
W(subgroup("Abilities"))
W(ability("Light Strike Array"))
W(ul_open())
W(li("Damage increased from 80/120/160/200 to 80/125/170/215", b([80, 120, 160, 200], [80, 125, 170, 215])))
W(ul_close())
W(ability("Laguna Blade"))
W(ul_open())
W(li("Damage increased from 380/565/750 to 400/580/760", b([380, 565, 750], [400, 580, 760])))
W(ul_close())
W(hero_header("Lone Druid"))
W(subgroup("Abilities"))
W(ability("Summon Spirit Bear", slug="lone_druid_spirit_bear"))
W(ul_open())
W(li("Mana Cost increased from 75 to 100", b(75, 100, l=True)))
W(ul_close())
W(ability("Spirit Link"))
W(ul_open())
W(li("Shared Lifesteal now follows general lifesteal rules and has a creep penalty of 40%", t("NERF"),
     extra=inline_note("Previously creeps used a 100% lifesteal multiplier; now follows the global creep-lifesteal value — " + b(100, 60))))
W(ul_close())
W(ability("Savage Roar"))
W(ul_open())
W(li("Aghanim's Shard buff duration decreased from 5s to 4s", b(5, 4)))
W(ul_close())
W(ul_open())
W(li("Aghanim's Shard bonus movement speed decreased from 15% to 10%", b(15, 10)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: −25s Summon Spirit Bear Cooldown replaced with +5s True Form Duration", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(ul_close())
W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
W(ul_open())
W(li_formula("Gold/Experience Bounty changed",
             "175 + 8 per Spirit Bear level", "165 + 10 per Spirit Bear level",
             lambda L: 175 + 8 * L,
             lambda L: 165 + 10 * L,
             levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30],
             l=True,
             rework_badge=False))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25: Demolish Bonus Building Damage decreased from +20% to +15%", b(20, 15)))
W(ul_close())
W(hero_header("Lycan"))
W(subgroup("Abilities"))
W(ability("Feral Impulse"))
W(ul_open())
W(li("Health Regen increased from 1/3/5/7 to 2/4/6/8", b([1, 3, 5, 7], [2, 4, 6, 8])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Wolves Damage increased from +10 to +14", b(10, 14)))
W(li("Level 15: Summon Wolves Health increased from +350 to +375", b(350, 375)))
W(ul_close())
W(hero_header("Magnus"))
W(subgroup("Abilities"))
W(ability("Shockwave"))
W(ul_open())
W(li("Slow Duration increased from 0.4/0.6/0.8/1.0s to 0.55/0.7/0.85/1.0s", b([0.4, 0.6, 0.8, 1], [0.55, 0.7, 0.85, 1])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15: All Attributes per hero hit with Reverse Polarity increased from +12 to +14", b(12, 14)))
W(ul_close())
W(hero_header("Marci"))
W(subgroup("Abilities"))
W(ability("Bodyguard"))
W(ul_open())
W(li("Cast Range increased from 500 to 600", b(500, 600)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15: Dispose Damage increased from +100 to +115", b(100, 115)))
W(ul_close())
W(hero_header("Mars"))
W(subgroup("Abilities"))
W(ability("Dauntless"))
W(ul_open())
W(li("HP Regen per extra enemy increased from 40% to 50%", b(40, 50)))
W(ul_close())
W(ability("Spear of Mars", slug="mars_spear"))
W(ul_open())
W(li("Mana Cost decreased from 100/110/120/130 to 90/100/110/120", b([100, 110, 120, 130], [90, 100, 110, 120], l=True)))
W(ul_close())
W(hero_header("Mirana"))
W(subgroup("Abilities"))
W(ability("Sacred Arrow", slug="mirana_arrow"))
W(ul_open())
W(li("Damage increased from 60/150/240/330 to 60/160/260/360", b([60, 150, 240, 330], [60, 160, 260, 360])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15: Leap Attack Speed increased from +90 to +100", b(90, 100)))
W(li("Level 20: Celestial Quiver Damage increased from +40 to +50", b(40, 50)))
W(ul_close())
W(hero_header("Monkey King"))
W(ul_open())
W(li("Base Agility decreased from 24 to 23", b(24, 23)))
W(li("Damage at level 1 decreased from 53-57 to 52-56", br(53, 57, 52, 56)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Primal Spring"))
W(ul_open())
W(li("Movement Slow decreased from 35/50/65/80% to 30/40/50/60%", b([35, 50, 65, 80], [30, 40, 50, 60])))
W(ul_close())
W(hero_header("Morphling"))
W(subgroup("Abilities"))
W(ability("Waveform"))
W(ul_open())
W(li("Will now be cast in the desired direction, if the target location is further than the cast range", '<span class="badge qol" data-tag="qol">QoL</span>'))
W(ul_close())
W(hero_header("Muerta"))
W(ul_open())
W(li("Base Attack Speed decreased from 115 to 110", b(115, 110)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Supernatural"))
W(ul_open())
W(li_formula("Maximum Stack Count increased",
             "1 per hero level",
             "5 + 1 per hero level",
             lambda L: 1 * L,
             lambda L: 5 + 1 * L,
             rework_badge=False))
W(ul_close())
W(hero_header("Nature's Prophet"))
W(subgroup("Abilities"))
W(ability("Nature's Call", slug="furion_force_of_nature"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 85/90/95/100", b(100, [85, 90, 95, 100], l=True)))
W(li("Treant Bonus Hero Damage increased from 4/8/12/16 to 6/10/14/18", b([4, 8, 12, 16], [6, 10, 14, 18])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20: Sprout Damage increased from +170 to +220", b(170, 220)))
W(li("Level 20: Wrath of Nature Cooldown Reduction increased from 15s to 20s", b(15, 20)))
W(ul_close())
W(hero_header("Ogre Magi"))
W(ul_open())
W(li("Strength gain decreased from 4.2 to 4.0", b(4.2, 4)))
W(ul_close())
W(hero_header("Omniknight"))
W(subgroup("Abilities"))
W(ability("Repel", slug="omniknight_martyr"))
W(ul_open())
W(li("Cooldown decreased from 40/36/32/28s to 40/35/30/25s", b([40, 36, 32, 28], [40, 35, 30, 25], l=True)))
W(ul_close())
W(ability("Hammer of Purity"))
W(ul_open())
W(li("Damage increased from 20/40/60/80 to 25/45/65/85", b([20, 40, 60, 80], [25, 45, 65, 85])))
W(ul_close())
W(hero_header("Outworld Destroyer"))
W(subgroup("Abilities"))
W(ability("Objurgation"))
W(ul_open())
W(li("Mana Cost decreased from 250 to 175", b(250, 175, l=True)))
W(ul_close())
W(ability("Sanity's Eclipse", slug="obsidian_destroyer_sanity_eclipse"))
W(ul_open())
W(li("Radius increased from 450/500/550 to 500/525/550", b([450, 500, 550], [500, 525, 550])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20: Astral Imprisonment Mana Capacity Steal increased from 10% to 12%", b(10, 12)))
W(ul_close())
W(hero_header("Pangolier"))
W(ul_open())
W(li("Base Health Regen decreased by 1.0", bstat_h("Pangolier", "StatusHealthRegen", "7.41b", -1), extra=note_box(hero="Pangolier", field="StatusHealthRegen", before_patch="7.41b")))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Swashbuckle"))
W(ul_open())
W(li("Mana Cost increased from 75/80/85/90 to 85/90/95/100", b([75, 80, 85, 90], [85, 90, 95, 100], l=True)))
W(ul_close())
W(ability("Roll Up", slug="pangolier_rollup"))
W(ul_open())
W(li("Mana Cost increased from 50 to 75", b(50, 75, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Lucky Shot Armor Reduction decreased from +3 to +2", b(3, 2)))
W(ul_close())
W(hero_header("Phantom Assassin"))
W(ul_open())
W(li("Base Agility increased from 21 to 22", b(21, 22)))
W(li("Damage at level 1 increased from 56-58 to 57-59", br(56, 58, 57, 59)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Phantom Strike Duration increased from +0.6 to +0.8s", b(0.6, 0.8)))
W(ul_close())
W(hero_header("Phantom Lancer"))
W(subgroup("Abilities"))
W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
W(ul_open())
W(li("Aghanim's Scepter bonus max rush distance decreased from +625 to +575", b(625, 575),
     extra=inline_note("Effective max rush distance per Phantom Rush level: 1225/1300/1375/1450 → 1175/1250/1325/1400.")))
W(ul_close())
W(hero_header("Phoenix"))
W(subgroup("Abilities"))
W(ability("Dying Light"))
W(ul_open())
W(li("Missing Health as Damage decreased from 4% to 3.5%", b(4, 3.5)))
W(ul_close())
W(ability("Sun Ray"))
W(ul_open())
W(li("Max Health as Heal per second decreased from 0.5/1/1.5/2% to 0.4/0.8/1.2/1.6%", b([0.5, 1, 1.5, 2], [0.4, 0.8, 1.2, 1.6])))
W(ul_close())
W(ability("Supernova"))
W(ul_open())
W(li("Damage per second decreased from 60/90/120 to 50/80/110", b([60, 90, 120], [50, 80, 110])))
W(ul_close())
W(hero_header("Primal Beast"))
W(subgroup("Abilities"))
W(ability("Trample"))
W(ul_open())
W(li("Damage AoE decreased from 230 to 200", b(230, 200)))
W(ul_close())
W(hero_header("Puck"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15: −15s Dream Coil Cooldown replaced with +2% Puckish Health and Mana Restoration", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(li("Level 25: Dream Coil Pierces Debuff Immunity replaced with −30s Dream Coil Cooldown", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(ul_close())
W(hero_header("Queen of Pain"))
W(ul_open())
W(li("Base Agility decreased from 22 to 20", b(22, 20)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Shadow Strike"))
W(ul_open())
W(li("Cooldown rescaled from 13/10/7/4s to 11/9/7/5s", b([13, 10, 7, 4], [11, 9, 7, 5], l=True)))
W(li("Aghanim's Scepter AoE decreased from 375 to 300", b(375, 300)))
W(ul_close())
W(hero_header("Razor"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15: Static Link Damage Steal increased from +5 to +6", b(5, 6)))
W(li("Level 20: Storm Surge Slow and Damage increased from +30% to +35%", b(30, 35)))
W(ul_close())
W(hero_header("Rubick"))
W(ul_open())
W(li("Agility gain decreased from 2.5 to 2.2", b(2.5, 2.2)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15: Fade Bolt Cooldown Reduction increased from 3s to 4s", b(3, 4)))
W(li("Level 15: Stolen Spells Mana Cost Reduction decreased from 50% to 40%", b(50, 40)))
W(li("Level 25: Curiosity Bonuses decreased from 2× to 1.5×", b(2, 1.5)))
W(ul_close())
W(hero_header("Sand King"))
W(ul_open())
W(li("Base Attack Speed decreased from 110 to 100", b(110, 100)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Stinger", slug="sandking_scorpion_strike"))
W(ul_open())
W(li("Slow Duration rescaled from 4/5/6/7s to 5s", b([4, 5, 6, 7], 5)))
W(ul_close())
W(ability("Epicenter", slug="sandking_epicenter"))
W(ul_open())
W(li("Base Radius decreased from 500 to 450", b(500, 450)))
W(ul_close())
W(hero_header("Shadow Fiend"))
W(subgroup("Abilities"))
W(ability("Shadowraze", slug="nevermore_shadowraze1"))
W(ul_open())
W(li("Mana Cost decreased from 80 to 75", b(80, 75, l=True)))
W(ul_close())
W(ability("Presence of the Dark Lord", slug="nevermore_dark_lord"))
W(ul_open())
W(li("Armor Reduction rescaled from 3/4/5/6 to 2.5/4/5.5/7", b([3, 4, 5, 6], [2.5, 4, 5.5, 7])))
W(ul_close())
W(hero_header("Skywrath Mage"))
W(subgroup("Abilities"))
W(ability("Mystic Flare"))
W(ul_open())
W(li("Cooldown decreased from 60/40/20s to 55/35/15s", b([60, 40, 20], [55, 35, 15], l=True)))
W(ul_close())
W(hero_header("Slardar"))
W(subgroup("Abilities"))
W(ability("Slithereen Crush"))
W(ul_open())
W(li("Cooldown increased from 7s to 8.5/8/7.5/7s", b(7, [8.5, 8, 7.5, 7], l=True)))
W(ul_close())
W(hero_header("Snapfire"))
W(ul_open())
W(li("Base Damage increased by 2", bstat_h("Snapfire", "AttackDamageMin", "7.41b", 2), extra=note_box(hero="Snapfire", field="AttackDamageMin", before_patch="7.41b")))
W(li("Damage at level 1 increased from 51-57 to 53-59", br(51, 57, 53, 59)))
W(ul_close())
W(hero_header("Spectre"))
W(ul_open())
W(li("Base Agility increased from 26 to 29", b(26, 29)))
W(li("Damage at level 1 increased from 49-53 to 52-56", br(49, 53, 52, 56)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Dispersion"))
W(ul_open())
W(li("Damage rescaled from 8/12/16/20% to 9/12/15/18%", b([8, 12, 16, 20], [9, 12, 15, 18])))
W(ul_close())
W(hero_header("Storm Spirit"))
W(subgroup("Abilities"))
W(ability("Galvanized"))
W(ul_open())
W(li('Now gains a charge every 3 levels', '<span class="badge new" data-tag="new" data-overall="buff">NEW</span>'))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Overload Attack/Movement Speed Slow increased from +20/20% to +25/25%", b([20, 20], [25, 25])))
W(ul_close())
W(hero_header("Sven"))
W(subgroup("Abilities"))
W(ability("Storm Hammer", slug="sven_storm_bolt"))
W(ul_open())
W(li("Mana Cost decreased from 110/115/120/125 to 110", b([110, 115, 120, 125], 110, l=True)))
W(ul_close())
W(hero_header("Techies"))
W(ul_open())
W(li("Base Mana Regen decreased by 0.5", bstat_h("Techies", "StatusManaRegen", "7.41b", -0.5), extra=note_box(hero="Techies", field="StatusManaRegen", before_patch="7.41b")))
W(li("Intelligence gain decreased from 3.0 to 2.7", b(3, 2.7)))
W(li("Damage gain per level decreased from 3.3 to 3.2 as a result", b(3.3, 3.2)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("M.A.D.", slug="techies_mutually_assured_destruction"))
W(ul_open())
W(li_formula("Mana Pool as Regen rescaled",
             "0.08% + 0.02% per level", "0.1% + 0.01% per level",
             lambda L: 0.08 + 0.02 * L, lambda L: 0.1 + 0.01 * L,
             value_fmt="{:.2f}%"))
W(ul_close())
W(ability("Reactive Tazer"))
W(ul_open())
W(li("Explosion Radius decreased from 450 to 400", b(450, 400)))
W(ul_close())
W(hero_header("Templar Assassin"))
W(ul_open())
W(li("Base Movement Speed increased from 310 to 315", b(310, 315)))
W(ul_close())
W(hero_header("Tidehunter"))
W(ul_open())
W(li("Base Mana Regen decreased by 0.5", bstat_h("Tidehunter", "StatusManaRegen", "7.41b", -0.5), extra=note_box(hero="Tidehunter", field="StatusManaRegen", before_patch="7.41b")))
W(ul_close())
W(hero_header("Timbersaw"))
W(ul_open())
W(li("Base Damage increased by 2", bstat_h("Timbersaw", "AttackDamageMin", "7.41b", 2), extra=note_box(hero="Timbersaw", field="AttackDamageMin", before_patch="7.41b")))
W(li(
    'Damage at level 1 <span class="wrong-word">decreased</span> from 46-50 to 48-52',
    '<span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span>',
    extra=note_box('The patch text says "decreased", but the values actually went up.'),
    force_tag="buff"
))
W(li("Base Intelligence increased from 23 to 24", b(23, 24)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Reactive Armor"))
W(ul_open())
W(li("Bonus HP Regen increased from 0.4/0.5/0.6/0.7 to 0.5/0.6/0.7/0.8", b([0.4, 0.5, 0.6, 0.7], [0.5, 0.6, 0.7, 0.8])))
W(ul_close())
W(hero_header("Tinker"))
W(subgroup("Abilities"))
W(ability("Deploy Turrets"))
W(ul_open())
W(li("Updated sound effects", '<span class="badge misc" data-tag="misc">MISC</span>'))
W(ul_close())
W(hero_header("Tiny"))
W(ul_open())
W(li("Base Attack Speed decreased from 90 to 85", b(90, 85)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Grow"))
W(ul_open())
W(li("Toss Bonus Damage increased from 50/175/300 to 50/200/350", b([50, 175, 300], [50, 200, 350])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: +8 Strength replaced with +2 Tree Grab Attacks", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(li("Level 15: −8% Grow Attack Speed Reduction replaced with +10 Strength", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(ul_close())
W(hero_header("Treant Protector"))
W(subgroup("Abilities"))
W(ability("Eyes In The Forest"))
W(ul_open())
W(li("Added AoE indicator to cast", '<span class="badge qol" data-tag="qol">QoL</span>'))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Living Armor Heal Per Second decreased from +4 to +3", b(4, 3)))
W(ul_close())
W(hero_header("Troll Warlord"))
W(subgroup("Abilities"))
W(ability("Whirling Axes (Ranged)"))
W(ul_open())
W(li("Mana Cost decreased from 60 to 50", b(60, 50, l=True)))
W(ul_close())
W(ability("Whirling Axes (Melee)"))
W(ul_open())
W(li("Damage increased from 50/100/150/200 to 75/120/165/210", b([50, 100, 150, 200], [75, 120, 165, 210])))
W(ul_close())
W(hero_header("Tusk"))
W(subgroup("Abilities"))
W(ability("Drinking Buddies"))
W(ul_open())
W(li("No longer castable while rooted", t("DEL")))
W(ul_close())
W(hero_header("Vengeful Spirit"))
W(subgroup("Abilities"))
W(ability("Vengeance Aura", slug="vengefulspirit_command_aura"))
W(ul_open())
W(li("Self Bonus increased from 20% to 25%", b(20, 25)))
W(ul_close())
W(hero_header("Venomancer"))
W(subgroup("Abilities"))
W(ability("Poison Sting"))
W(ul_open())
W(li("Movement Slow decreased from 10% to 8%", b(10, 8)))
W(ul_close())
W(ability("Snakebite"))
W(ul_open())
W(li("Damage per second rescaled from 20/25/30/35 to 10/20/30/40", b([20, 25, 30, 35], [10, 20, 30, 40])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15: Poison Sting Slow increased from +7% to +10%", b(7, 10)))
W(li("Level 20: +40% Snakebite Damage replaced with +100 Snakebite Initial Damage", '<span class="badge rework" data-tag="rework">REWORK</span>'))
W(ul_close())
W(hero_header("Viper"))
W(subgroup("Abilities"))
W(ability("Nosedive", slug="viper_nose_dive"))
W(ul_open())
W(li("Cooldown increased from 20s to 25s", b(20, 25, l=True)))
W(ul_close())
W(hero_header("Weaver"))
W(subgroup("Abilities"))
W(ability("The Swarm"))
W(ul_open())
W(li("Mana Cost decreased from 110 to 110/105/100/95", b(110, [110, 105, 100, 95], l=True)))
W(ul_close())
W(hero_header("Windranger"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25: Focus Fire Cooldown Advance on Kills decreased from 18s to 16s", b(18, 16)))
W(li("Level 25: Powershot Max HP Execution Threshold increased from 15% to 16%", b(15, 16)))
W(ul_close())
W(hero_header("Winter Wyvern"))
W(subgroup("Abilities"))
W(ability("Splinter Blast"))
W(ul_open())
W(li("Movement Slow decreased from 28/32/36/40% to 27/30/33/36%", b([28, 32, 36, 40], [27, 30, 33, 36])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Cold Embrace Base Heal per Second decreased from +20 to +15", b(20, 15)))
W(ul_close())
W(hero_header("Witch Doctor"))
W(subgroup("Abilities"))
W(ability("Voodoo Restoration"))
W(ul_open())
W(li("Radius increased from 500/550/600/650 to 650", b([500, 550, 600, 650], 650)))
W(ul_close())


write_footer()
save_html('patches/7.41c.html')

# ============================================================
# 7.41b content
# ============================================================
write_head("7.41b", "07.04.2026")

# ===== GENERAL UPDATES =====
W(section("General Updates"))

W(plain_header("Map Objectives"))
W(subgroup("Tormentor"))
W(ul_open())
W(li("Reflect Damage reflection per minute decreased from 2% to 1.5%", b(2, 1.5)))
W(ul_close())

# ===== NEUTRAL CREEP UPDATES =====
W(section("Neutral Creep Updates"))
W(unit_header("Frostbitten Golem", "../icons/units/npc_dota_neutral_frostbitten_golem.png"))
W(ability("Time Warp Aura", icon_url="../icons/abilities/frostbitten_golem_time_warp_aura.png"))
W(ul_open())
W(li("Cooldown Reduction decreased from 10/11/12/14% to 8/9/10/11%", b([10, 11, 12, 14], [8, 9, 10, 11], l=True)))
W(ul_close())

# ===== ITEM UPDATES =====
W(section("Item Updates"))

W(item_header("Black King Bar"))
W(ul_open())
W(li("Avatar now has a fixed duration and is not affected by buff duration amplification", t("NERF")))
W(ul_close())
W(item_header("Consecrated Wraps"))
W(ul_open())
W(li("All Attributes bonus decreased from +6 to +5", b(6, 5)))
W(li("Hallowed stacks are now item charges instead of a stack counter on the buff", t("REWORK")))
W(li("All charges are consumed when the barrier is created", t("NERF")))
W(li("Charge Restore Time of Hallowed is not affected by effects that reduce or modify cooldowns", t("NERF")))
W(li("Hallowed now starts with all 3 charges when Consecrated Wraps is purchased or built", t("MISC")))
W(li("Gaining max stacks requirement for the speedup buff is removed", t("BUFF")))
W(li("Initial 3 charges don't provide the movement speed buff", t("MISC")))
W(li("Hallowed charge gain time increased from 3s to 4s", b(3, 4)))
W(ul_close())
W(item_header("Gleipnir"))
W(ul_open())
W(li("Eternal Chains radius increased from 275 to 325", b(275, 325)))
W(li("Effective radius increased from 350 to 400 due to item's built-in Area of Effect bonus", b(350, 400)))
W(ul_close())
W(item_header("Heaven's Halberd"))
W(ul_open())
W(li("Health Regen bonus increased from +6 to +6.5", b(6, 6.5)))
W(ul_close())
W(item_header("Helm of the Overlord"))
W(ul_open())
W(li("Dominate cooldown decreased from 45s to 40s", b(45, 40, l=True)))
W(li("Dominate target unit's max health minimum increased from 1800 to 1900", b(1800, 1900, l=True)))
W(ul_close())
W(item_header("Holy Locket"))
W(ul_open())
W(li("Energy Charge incoming Heal Amplification increased from 10% to 15%", b(10, 15)))
W(li("Holy Blessing outgoing Heal Amplification decreased from 15% to 10%", b(15, 10)))
W(ul_close())
W(item_header("Mage Slayer"))
W(ul_open())
W(li("Health Regen bonus decreased from +6 to +5.5", b(6, 5.5)))
W(li("Magic Resistance bonus decreased from 20% to 18%", b(20, 18)))
W(ul_close())
W(item_header("Sange"))
W(ul_open())
W(li("Health Restoration bonus decreased from 16% to 12%", b(16, 12)))
W(ul_close())
W(item_header("Abyssal Blade"))
W(ul_open())
W(li("Health Restoration bonus decreased from 20% to 16%", b(20, 16)))
W(ul_close())
W(item_header("Sange and Yasha"))
W(ul_open())
W(li("Health Restoration bonus decreased from 20% to 16%", b(20, 16)))
W(ul_close())
W(item_header("Kaya and Sange"))
W(ul_open())
W(li("Health Restoration bonus decreased from 20% to 16%", b(20, 16)))
W(ul_close())
# ===== NEUTRAL ITEM UPDATES =====
W(section("Neutral Item Updates"))
W(plain_header("Artifact changes", dynamics=False))
W(item_header("Jidi Pollen Bag"))
W(ul_open())
W(li("Pollinate radius increased from 700 to 900", b(700, 900)))
W(ul_close())
W(item_header("Conjurer's Catalyst"))
W(ul_open())
W(li("Spellover now has a 0.1s internal cooldown", t("REWORK")))
W(ul_close())
W(subnote("Still can proc multiple times from a single instance of high damage"))
W(ul_open())
W(li("Spellover damage threshold increased from 100 to 200", b(100, 200)))
W(li("Spellover damage from hero targets increased from 40 to 80", b(40, 80)))
W(ul_close())
W(subnote("From 52 to 104 with Dormant Curio"))
W(ul_open())
W(li("Spellover damage from creep targets increased from 15 to 30", b(15, 30)))
W(ul_close())
W(subnote("From 19.5 to 39 with Dormant Curio"))
W(item_header("Enchanter's Bauble"))
W(ul_open())
W(li("Enchant base Neutral Enchantment bonus decreased from 15% to 10%", b(15, 10)))
W(ul_close())
W(item_header("Idol of Scree'auk"))
W(ul_open())
W(li("False Flight duration increased from 5s to 6.5s", b(5, 6.5)))
W(ul_close())
W(subnote("From 6.5s to 8.45s with Dormant Curio"))
W(item_header("Metamorphic Mandible"))
W(ul_open())
W(li("Pupate movement speed bonus increased from 15% to 20%", b(15, 20)))
W(ul_close())
W(item_header("Rattlecage"))
W(ul_open())
W(li("Reverberate projectile physical damage decreased from 110 to 90", b(110, 90)))
W(ul_close())
W(subnote("From 143 to 117 with Dormant Curio"))
W(item_header("Book of the Dead"))
W(ul_open())
W(li("Demonic Warrior no longer has True Sight ability", t("DEL")))
W(ul_close())
W(item_header("Minotaur Horn"))
W(ul_open())
W(li("Lesser Avatar bonus magic resistance increased from 50% to 60%", b(50, 60)))
W(ul_close())
W(item_header("Riftshadow Prism"))
W(ul_open())
W(li("Refract cooldown decreased from 30s to 27s", b(30, 27, l=True)))
W(ul_close())
W(plain_header("Enchantment changes", dynamics=False))
W(enchant_header("Crude", "crude"))
W(ul_open())
W(li("Health Restoration bonus decreased from +10/15/20% to +9/12/15%", b([10, 15, 20], [9, 12, 15])))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))


# Alchemist
W(hero_header("Alchemist"))
W(ul_open())
W(li("Base Agility decreased from 22 to 19", b(22, 19)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +1 Acid Spray Armor Reduction replaced with +1% Corrosive Weaponry Slow / Damage Reduction Per Stack", t("REWORK")))
W(li("Level 15 Talent +1% Corrosive Weaponry Slow / Damage Reduction Per Stack replaced with +1 Acid Spray Armor Reduction", t("REWORK")))
W(ul_close())

# Ancient Apparition
W(hero_header("Ancient Apparition"))
W(ability("Bone Chill"))
W(ul_open())
W(li("Aghanim's Scepter Strength Reduction bonus increased from 0.3 to 0.8", b(0.3, 0.8)))
W(ul_close())

# Anti-Mage
W(hero_header("Anti-Mage"))
W(ability("Mana Break"))
W(ul_open())
W(li("Max Mana Burned per hit increased from 1.6/2.4/3.2/4% to 1.8/2.7/3.6/4.5%", b([1.6, 2.4, 3.2, 4], [1.8, 2.7, 3.6, 4.5])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Blink Cast Range decreased from +150 to +125", b(150, 125)))
W(ul_close())

# Arc Warden
W(hero_header("Arc Warden"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Magnetic Field Cooldown Reduction decreased from 5s to 4s", b(5, 4, l=True)))
W(li("Level 20 Talent +200 Spark Wraith Damage replaced with +30s Spark Wraith Duration", t("REWORK")))
W(li("Level 25 Talent +30s Spark Wraith Duration replaced with +240 Spark Wraith Damage", t("REWORK")))
W(li("Level 25 Talent Runic Infusion All Attributes Bonus decreased from +1.5 to +1", b(1.5, 1)))
W(ul_close())

# Batrider
W(hero_header("Batrider"))
W(ul_open())
W(li("Base Armor decreased by 1", bstat_h("Batrider", "ArmorPhysical", "7.41a", -1), extra=note_box(hero="Batrider", field="ArmorPhysical", before_patch="7.41a")))
W(ul_close())
W(ability("Firefly"))
W(ul_open())
W(li("Cooldown increased from 45/40/35/30s to 48/42/36/30s", b([45, 40, 35, 30], [48, 42, 36, 30], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Sticky Napalm Movement Slow increased from +0.5% to +0.75%", b(0.5, 0.75)))
W(ul_close())

# Beastmaster
W(hero_header("Beastmaster"))
W(ul_open())
W(li("Base Attack Speed decreased from 100 to 90", b(100, 90)))
W(ul_close())
W(ability("Wild Axes"))
W(ul_open())
W(li("Debuff Duration rescaled from 12s to 10/11/12/13s", b(12, [10, 11, 12, 13])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Armor decreased from +5 to +4", b(5, 4)))
W(li("Level 10 Talent Wild Axes Damage Amp Per Stack decreased from +2% to +1.5%", b(2, 1.5)))
W(ul_close())

# Bloodseeker
W(hero_header("Bloodseeker"))
W(ability("Rupture"))
W(ul_open())
W(li("Mana Cost increased from 100/150/200 to 125/175/225", b([100, 150, 200], [125, 175, 225], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Max Thirst Move Speed decreased from +18% to +15%", b(18, 15)))
W(ul_close())

# Broodmother
W(hero_header("Broodmother"))
W(ul_open())
W(li("Base agility increased from 18 to 20", b(18, 20)))
W(li("Damage at level 1 increased from 45-51 to 47-53", br(45, 51, 47, 53)))
W(ul_close())

# Chaos Knight
W(hero_header("Chaos Knight"))
W(ability("Phantasm"))
W(ul_open())
W(li("Cooldown increased from 75s to 85/80/75s", b(75, [85, 80, 75], l=True)))
W(li("Number of Phantasms increased from 1/2/3 to 3", b([1, 2, 3], 3)))
W(li("Phantasm Damage decreased from 100% to 50/75/100%", b(100, [50, 75, 100])))
W(ul_close())

# Chen
W(hero_header("Chen"))
W(ability("Holy Persuasion"))
W(ul_open())
W(li("Bonus Damage increased from 0/6/12/18% to 5/10/15/20%", b([0, 6, 12, 18], [5, 10, 15, 20])))
W(ul_close())

# Clinkz
W(hero_header("Clinkz"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Strafe Duration increased from +0.75s to +1s", b(0.75, 1)))
W(ul_close())

# Crystal Maiden
W(hero_header("Crystal Maiden"))
W(ability("Crystal Clone"))
W(ul_open())
W(li("Cooldown increased from 10s to 12s", b(10, 12, l=True)))
W(ul_close())

# Dawnbreaker
W(hero_header("Dawnbreaker"))
W(ability("Break of Dawn"))
W(ul_open())
W(li_formula("Max Damage Increase decreased", "10% + 1% per level", "8% + 1% per level", lambda L: 10.0 + 1.0*L, lambda L: 8.0 + 1.0*L))
W(ul_close())

# Death Prophet
W(hero_header("Death Prophet"))
W(ability("Exorcism"))
W(ul_open())
W(li("Spirit Damage increased from 64 to 65/68/71", b(64, [65, 68, 71])))
W(ul_close())
W(subnote("From 62-67 to 62-68/65-71/68-74"))

# Doom
W(hero_header("Doom"))
W(ability("Scorched Earth"))
W(ul_open())
W(li("Damage decreased from 20/35/50/65 to 20/30/40/50", b([20, 35, 50, 65], [20, 30, 40, 50])))
W(ul_close())
W(ability("Doom"))
W(ul_open())
W(li("Damage per second decreased from 25/45/66 to 22/44/66", b([25, 45, 66], [22, 44, 66])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Devour grants 15% Magic Resistance replaced with +10% Magic Resistance", t("REWORK")))
W(li("Level 15 Talent +66 Damage replaced with +1.5% Infernal Blade Max HP As Damage", t("REWORK")))
W(li("Level 20 Talent +2.5% Infernal Blade Max HP As Damage replaced with +66 Damage", t("REWORK")))
W(ul_close())

# Drow Ranger
W(hero_header("Drow Ranger"))
W(ul_open())
W(li("Base Agility increased from 22 to 24", b(22, 24)))
W(li("Damage at level 1 increased from 49-56 to 51-58", br(49, 56, 51, 58)))
W(ul_close())
W(ability("Marksmanship"))
W(ul_open())
W(li("Enemy hero disable range decreased from 325 to 300", b(325, 300)))
W(ul_close())
W(ability("Glacier"))
W(ul_open())
W(li("While on the glacier, Marksmanship now can be disabled by enemies in the proximity", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Multishot Waves increased from +1 to +2", b(1, 2)))
W(ul_close())

# Elder Titan
W(hero_header("Elder Titan"))
W(ability("Momentum"))
W(ul_open())
W(li_formula("Bonus Speed to Armor increased", "3.6% + 0.4% per level", "5.0% + 0.5% per level", lambda L: 3.6 + 0.4*L, lambda L: 5.0 + 0.5*L))
W(ul_close())

# Ember Spirit
W(hero_header("Ember Spirit"))
W(ul_open())
W(li("Base Damage decreased by 3", bstat_h("Ember Spirit", "AttackDamageMin", "7.41a", -3), extra=note_box(hero="Ember Spirit", field="AttackDamageMin", before_patch="7.41a")))
W(li("Damage at level 1 decreased from 55-59 to 52-56", br(55, 59, 52, 56)))
W(ul_close())
W(ability("Sleight of Fist"))
W(ul_open())
W(li("Mana Cost increased from 60/65/70/75 to 75", b([60, 65, 70, 75], 75, l=True)))
W(ul_close())

# Enigma
W(hero_header("Enigma"))
W(ability("Event Horizon"))
W(ul_open())
W(li_formula("Movement Slow increased", "4% + 1% per level", "5% + 1% per level", lambda L: 4.0 + 1.0*L, lambda L: 5.0 + 1.0*L))
W(ul_close())
W(ability("Demonic Summoning", slug="enigma_demonic_conversion"))
W(ul_open())
W(li("Fixed Eidolons not having an 8 attack damage spread", t("MISC")))
W(li("Eidolon Damage increased from 16/27/38/49 to 16/28/40/52", b([16, 27, 38, 49], [16, 28, 40, 52]),
     extra=inline_note("As a result, damage changed from 16/27/38/49 to 12-20/24-32/36-44/48-56")))
W(ul_close())

# Gyrocopter
W(hero_header("Gyrocopter"))
W(ability("Flak Cannon"))
W(ul_open())
W(li("Cooldown rescaled from 26/24/22/20s to 25s", b([26, 24, 22, 20], 25, l=True)))
W(ul_close())
W(ability("Call Down"))
W(ul_open())
W(li("Cooldown decreased from 90/75/60s to 75/65/55s", b([90, 75, 60], [75, 65, 55], l=True)))
W(ul_close())

# Hoodwink
W(hero_header("Hoodwink"))
W(ability("Hunter's Boomerang"))
W(ul_open())
W(li("Debuff Duration decreased from 7s to 6s", b(7, 6)))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(ability("Invoke"))
W(ul_open())
W(li("Now grants Invoker an additional Ability Point at hero levels 6, 12, and 18", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +1 Orb Levels replaced with +50% Forged Spirit Armor Reduction", t("REWORK")))
W(ul_close())

# Jakiro
W(hero_header("Jakiro"))
W(ability("Dual Breath"))
W(ul_open())
W(li("Cooldown rescaled from 10s to 12/11/10/9s", b(10, [12, 11, 10, 9], l=True)))
W(ul_close())
W(ability("Liquid Fire"))
W(ul_open())
W(li("Burn Damage rescaled from 15/25/35/45 to 12/24/36/48", b([15, 25, 35, 45], [12, 24, 36, 48])))
W(ul_close())
W(ability("Macropyre"))
W(ul_open())
W(li("Mana Cost decreased from 300/400/500 to 250/350/450", b([300, 400, 500], [250, 350, 450], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Macropyre Damage increased from +20 to +25", b(20, 25)))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
W(ul_open())
W(li("Base Movement Speed increased from 300 to 305", b(300, 305)))
W(ul_close())
W(ability("Bladeform"))
W(ul_open())
W(li_formula("Base Agility per stack increased", "2.5% + 0.05% per level", "2.5% + 0.1% per level", lambda L: 2.5 + 0.05*L, lambda L: 2.5 + 0.1*L))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Blade Fury Damage per second increased from +100 to +120", b(100, 120)))
W(ul_close())

# Keeper of the Light
W(hero_header("Keeper of the Light"))
W(ability("Bright Speed"))
W(ul_open())
W(li("Intelligence required for 1 movement speed increased from 2.5 to 3", b(2.5, 3, l=True)))
W(ul_close())
W(ability("Spirit Form"))
W(ul_open())
W(li("Cast Range Bonus decreased from 100/200/300 to 100/175/250", b([100, 200, 300], [100, 175, 250])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Spirit Form Bright Speed Bonus decreased from +30% to +25%", b(30, 25)))
W(ul_close())

# Largo
W(hero_header("Largo"))
W(ability("Encore"))
W(ul_open())
W(li_formula("Bonus Duration increased", "9% + 1% per level", "10% + 1% per level", lambda L: 9.0 + 1.0*L, lambda L: 10.0 + 1.0*L))
W(ul_close())
W(ability("Croak of Genius"))
W(ul_open())
W(li("Mana Cost rescaled from 25/35/45/55 to 40", b([25, 35, 45, 55], 40, l=True)))
W(li("Duration increased from 12/18/24/30s to 15/20/25/30s", b([12, 18, 24, 30], [15, 20, 25, 30])))
W(ul_close())
W(ability("Bullbelly Blitz", slug="largo_song_fight_song"))
W(ul_open())
W(li("Aghanim's Scepter Damage per stack decreased from 6/12/18 to 6/10/14", b([6, 12, 18], [6, 10, 14])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Catchy Lick Damage increased from +170 to +200", b(170, 200)))
W(ul_close())

# Lycan
W(hero_header("Lycan"))
W(ability("Shapeshift"))
W(ul_open())
W(li("Cooldown decreased from 110/100/90s to 105/95/85s", b([110, 100, 90], [105, 95, 85], l=True)))
W(ul_close())

# Magnus
W(hero_header("Magnus"))
W(ul_open())
W(li("Agility gain increased from 2.0 to 2.2", b(2.0, 2.2)))
W(li("Damage gain per level increased from 3.2 to 3.3 as a result", b(3.2, 3.3)))
W(ul_close())

# Meepo
W(hero_header("Meepo"))
W(ul_open())
W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
W(li("Strength gain decreased from 2.2 to 2.0", b(2.2, 2.0)))
W(ul_close())
W(ability("Ransack"))
W(ul_open())
W(li("Health Steal (Heroes) decreased from 9/12/15/18 to 7/10/13/16", b([9, 12, 15, 18], [7, 10, 13, 16])))
W(ul_close())
W(ability("Divided We Stand"))
W(ul_open())
W(li("Max Health and Max Mana bonuses from items are now penalized by the number of Meepos (like other item bonuses)", t("NERF")))
W(li("No longer shares cooldowns of Town Portal Scrolls", t("BUFF")))
W(ul_close())
W(ability("MegaMeepo"))
W(ul_open())
W(li("Cooldown increased from 60s to 90s", b(60, 90, l=True)))
W(li("Duration decreased from 25s to 20s", b(25, 20)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +40 Poof Damage replaced with -1.5s Earthbind Cooldown", t("REWORK")))
W(li("Level 15 Talent -2.5s Earthbind Cooldown replaced with +40 Poof Damage", t("REWORK")))
W(li("Level 20 Talent Ransack Health Steal decreased from +7 to +6", b(7, 6)))
W(ul_close())

# Monkey King
W(hero_header("Monkey King"))
W(ability("Changing of the Guard", slug="monkey_king_transfiguration"))
W(ul_open())
W(li("Cooldown increased from 3s to 5s", b(3, 5, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Tree Dance Cast Range decreased from +350 to +300", b(350, 300)))
W(ul_close())

# Naga Siren
W(hero_header("Naga Siren"))
W(ul_open())
W(li("Base Attack Speed decreased from 110 to 100", b(110, 100)))
W(ul_close())
W(ability("Eelskin"))
W(ul_open())
W(li_formula("Evasion per Naga decreased", "4.9% + 0.1% per level", "4% + 0.1% per level", lambda L: 4.9 + 0.1*L, lambda L: 4.0 + 0.1*L))
W(ul_close())

# Nature's Prophet
W(hero_header("Nature's Prophet"))
W(ability("Wrath of Nature"))
W(ul_open())
W(li("Base Damage increased from 90/130/170 to 100/140/180", b([90, 130, 170], [100, 140, 180])))
W(ul_close())

# Necrophos
W(hero_header("Necrophos"))
W(ability("Death Seeker"))
W(ul_open())
W(li("Mana Cost increased from 125 to 160", b(125, 160, l=True)))
W(ul_close())

# Night Stalker
W(hero_header("Night Stalker"))
W(ul_open())
W(li("Base Health Regen decreased by 1.25", bstat_h("Night Stalker", "StatusHealthRegen", "7.41a", -1.25), extra=note_box(hero="Night Stalker", field="StatusHealthRegen", before_patch="7.41a")))
W(ul_close())

# Nyx Assassin
W(hero_header("Nyx Assassin"))
W(ability("Vendetta"))
W(ul_open())
W(li("Duration decreased from 60s to 45/50/55s", b(60, [45, 50, 55])))
W(ul_close())

# Omniknight
W(hero_header("Omniknight"))
W(ability("Hammer of Purity"))
W(ul_open())
W(li("Damage to heal increased from 30% to 35%", b(30, 35)))
W(ul_close())
W(ability("Guardian Angel"))
W(ul_open())
W(li("Duration increased from 4/4.5/5s to 4/4.75/5.5s", b([4, 4.5, 5], [4, 4.75, 5.5])))
W(li("Aghanim's Scepter Bonus Health Restoration decreased from 100% to 50%", b(100, 50)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Degen Aura Radius increased from +125 to +150", b(125, 150)))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ability("Lucky Shot"))
W(ul_open())
W(li("Attack Speed Reduction decreased from 40/80/120/160 to 35/70/105/140", b([40, 80, 120, 160], [35, 70, 105, 140])))
W(ul_close())
W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
W(ul_open())
W(li("Total Attack Damage as Damage decreased from 100% to 80%", b(100, 80)))
W(ul_close())

# Phantom Assassin
W(hero_header("Phantom Assassin"))
W(ul_open())
W(li("Strength gain increased from 2.0 to 2.2", b(2.0, 2.2)))
W(ul_close())
W(ability("Phantom Strike"))
W(ul_open())
W(li("Duration increased from 2.5s to 3s", b(2.5, 3)))
W(li("Bonus Attack Speed rescaled from 100/130/160/190 to 80/120/160/200", b([100, 130, 160, 190], [80, 120, 160, 200])))
W(ul_close())
W(ability("Coup de Grace"))
W(ul_open())
W(li("Critical Damage increased from 200/300/400% to 200/325/450%", b([200, 300, 400], [200, 325, 450])))
W(ul_close())

# Phoenix
W(hero_header("Phoenix"))
W(ul_open())
W(li("Base Attack Range decreased from 525 to 500", b(525, 500)))
W(ul_close())
W(ability("Sun Ray"))
W(ul_open())
W(li("Aghanim's Shard no longer slows affected enemies by 10%", t("NERF")))
W(ul_close())

# Primal Beast
W(hero_header("Primal Beast"))
W(ability("Pulverize"))
W(ul_open())
W(li("Cooldown increased from 40/35/30s to 45/40/35s", b([40, 35, 30], [45, 40, 35], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Damage decreased from +30 to +25", b(30, 25)))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(ability("Meat Shield", slug="pudge_flesh_heap"))
W(ul_open())
W(li("Strength gain per stack increased from 1.6 to 2.0", b(1.6, 2.0)))
W(ul_close())

# Rubick
W(hero_header("Rubick"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Telekinesis Landing Damage decreased from 325 to 300", b(325, 300)))
W(ul_close())

# Sand King
W(hero_header("Sand King"))
W(ability("Epicenter", slug="sandking_epicenter"))
W(ul_open())
W(li("Attack Slow decreased from 50/55/60 to 30/40/50", b([50, 55, 60], [30, 40, 50])))
W(li("Aghanim's Scepter Stinger damage decreased from 50% to 40%", b(50, 40)))
W(ul_close())

# Shadow Demon
W(hero_header("Shadow Demon"))
W(ability("Disruption"))
W(ul_open())
W(li("Illusion Duration decreased from 11/12/13/14s to 8/10/12/14s", b([11, 12, 13, 14], [8, 10, 12, 14])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Movement Speed decreased from +25 to +20", b(25, 20)))
W(ul_close())

# Shadow Shaman
W(hero_header("Shadow Shaman"))
W(ul_open())
W(li("Intelligence gain decreased from 3.5 to 3.3", b(3.5, 3.3)))
W(ul_close())

# Silencer
W(hero_header("Silencer"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Global Silence Cooldown Reduction decreased from 20s to 15s", b(20, 15, l=True)))
W(ul_close())

# Skywrath Mage
W(hero_header("Skywrath Mage"))
W(ul_open())
W(li("Base Mana Regen increased by 0.25", bstat_h("Skywrath Mage", "StatusManaRegen", "7.41a", 0.25), extra=note_box(hero="Skywrath Mage", field="StatusManaRegen", before_patch="7.41a")))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ability("Guardian Sprint", slug="slardar_sprint"))
W(ul_open())
W(li("Cooldown increased from 29/25/21/17s to 33/28/23/18s", b([29, 25, 21, 17], [33, 28, 23, 18], l=True)))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(ability("Essence Shift"))
W(ul_open())
W(li_formula("Duration decreased", "12.5s + 2.5s per level", "10s + 2.5s per level", lambda L: 12.5 + 2.5*L, lambda L: 10.0 + 2.5*L, l=False))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Essence Shift Duration decreased from +25s to +20s", b(25, 20)))
W(ul_close())

# Snapfire
W(hero_header("Snapfire"))
W(ability("Scatterblast"))
W(ul_open())
W(li("Cooldown decreased from 18/15/12/9s to 17/14/11/8s", b([18, 15, 12, 9], [17, 14, 11, 8], l=True)))
W(li("Initial radius increased from 225 to 250", b(225, 250)))
W(ul_close())

# Spectre
W(hero_header("Spectre"))
W(ul_open())
W(li("Strength gain decreased from 2.4 to 2.3", b(2.4, 2.3)))
W(ul_close())
W(ability("Dispersion"))
W(ul_open())
W(li("Max Radius decreased from 800 to 700", b(800, 700)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Spectral Dagger Cooldown Reduction decreased from 4s to 3s", b(4, 3, l=True)))
W(ul_close())

# Techies
W(hero_header("Techies"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Magic Resistance decreased from +20% to +15%", b(20, 15)))
W(li("Level 15 Talent Blast Off! Damage decreased from +200 to +175", b(200, 175)))
W(ul_close())

# Terrorblade
W(hero_header("Terrorblade"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Conjure Image Duration decreased from +10s to +8s", b(10, 8)))
W(ul_close())

# Tidehunter
W(hero_header("Tidehunter"))
W(ul_open())
W(li("Base Strength decreased from 26 to 25", b(26, 25)))
W(li("Damage at level 1 decreased from 51-57 to 50-56", br(51, 57, 50, 56)))
W(ul_close())
W(ability("Leviathan's Catch"))
W(ul_open())
W(li("Now gains fish on every even level instead of every level", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Gush Damage decreased from +100 to +90", b(100, 90)))
W(li("Level 25 Talent Anchor Smash damage to buildings decreased from 100% to 50%", b(100, 50)))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ability("Whirling Death"))
W(ul_open())
W(li("Damage rescaled from 75/120/165/210 to 60/120/180/240", b([75, 120, 165, 210], [60, 120, 180, 240])))
W(ul_close())
W(ability("Timber Chain"))
W(ul_open())
W(li("Damage increased from 45/100/155/210 to 45/105/165/225", b([45, 100, 155, 210], [45, 105, 165, 225])))
W(ul_close())
W(ability("Chakram"))
W(ul_open())
W(li("Pass Damage rescaled from 100/150/200 to 75/150/225", b([100, 150, 200], [75, 150, 225])))
W(ul_close())

# Tinker
W(hero_header("Tinker"))
W(ability("Deploy Turrets"))
W(ul_open())
W(li("Missile speed increased from 1200 to 1350", b(1200, 1350)))
W(li("Base activation time decreased from 0.3s to 0s", b(0.3, 0, l=True)))
W(li("Aghanim's Scepter no longer makes activation faster", ""))
W(ul_close())

# Tiny
W(hero_header("Tiny"))
W(ul_open())
W(li("Intelligence gain increased from 2.2 to 2.4", b(2.2, 2.4)))
W(ul_close())
W(ability("Tree Volley", slug="tiny_tree_channel"))
W(ul_open())
W(li("No longer applies cleave", t("DEL")))
W(ul_close())

# Treant Protector
W(hero_header("Treant Protector"))
W(ability("Nature's Grasp"))
W(ul_open())
W(li("Cooldown increased from 20/19/18/17s to 23/21/19/17s", b([20, 19, 18, 17], [23, 21, 19, 17], l=True)))
W(ul_close())

# Tusk
W(hero_header("Tusk"))
W(ability("Bitter Chill"))
W(ul_open())
W(li_formula("Attack Slow decreased", "17 + 3 per level", "12 + 3 per level", lambda L: 17.0 + 3.0*L, lambda L: 12.0 + 3.0*L))
W(ul_close())
W(ability("Drinking Buddies"))
W(ul_open())
W(li("No longer has an alt-cast", t("MISC")))
W(li("Bonus Armor decreased from 10 to 7", b(10, 7)))
W(ul_close())

# Void Spirit
W(hero_header("Void Spirit"))
W(ability("Dissimilate"))
W(ul_open())
W(li("Damage decreased from 120/200/280/360 to 105/185/265/345", b([120, 200, 280, 360], [105, 185, 265, 345])))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ul_open())
W(li("Base Health Regen increased by 0.5", bstat_h("Windranger", "StatusHealthRegen", "7.41b", 0.5), extra=note_box(hero="Windranger", field="StatusHealthRegen", before_patch="7.41b")))
W(ul_close())
W(ability("Powershot"))
W(ul_open())
W(li("Slow increased from 20/25/30/35% to 22/28/34/40%", b([20, 25, 30, 35], [22, 28, 34, 40])))
W(ul_close())
W(ability("Gale Force"))
W(ul_open())
W(li("Cooldown decreased from 30s to 25s", b(30, 25, l=True)))
W(ul_close())

write_footer()
save_html('patches/7.41b.html')

# ============================================================
# 7.41a content
# ============================================================
write_head("7.41a", "28.03.2026")

# ===== ITEM UPDATES =====
W(section("Item Updates"))

W(item_header("Consecrated Wraps"))
W(ul_open())
W(li("Magic Resistance bonus decreased from +15% to +12%", b(15, 12)))
W(li("Hallowed movement speed on stack gain decreased from 20% to 15%", b(20, 15)))
W(li("Hallowed barrier and movement speed duration decreased from 7s to 5s", b(7, 5)))
W(ul_close())

# ===== NEUTRAL ITEM UPDATES =====
W(section("Neutral Item Updates"))
W(plain_header("Enchantment changes", dynamics=False))
W(enchant_header("Crude", "crude"))
W(ul_open())
W(li("Base Attack Time Reduction bonus worsened from 8/12/16% to 6/9/12%", b([8, 12, 16], [6, 9, 12])))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))


# Alchemist
W(hero_header("Alchemist"))
W(ul_open())
W(li("Base movement speed decreased from 295 to 290", b(295, 290)))
W(ul_close())
W(ability("Greevil's Greed", slug="alchemist_goblins_greed"))
W(ul_open())
W(li("Max Bonus Gold Per Kill decreased from 18 to 16", b(18, 16)))
W(li("Bonus Damage per Scepter decreased from +25 to +15", b(25, 15)))
W(ul_close())

# Ancient Apparition
W(hero_header("Ancient Apparition"))
W(ability("Bone Chill"))
W(ul_open())
W(li("Base Strength Reduction increased from 0.1 to 0.2", b(0.1, 0.2)))
W(ul_close())

# Anti-Mage
W(hero_header("Anti-Mage"))
W(ul_open())
W(li("Base Movement Speed increased from 310 to 315", b(310, 315)))
W(li("Base Health Regen increased by 0.5", bstat_h("Anti-Mage", "StatusHealthRegen", "7.41", 0.5), extra=note_box(hero="Anti-Mage", field="StatusHealthRegen", before_patch="7.41")))
W(ul_close())
W(ability("Mana Break"))
W(ul_open())
W(li("Mana Burned As Damage increased from 50% to 60%", b(50, 60)))
W(ul_close())

# Bloodseeker
W(hero_header("Bloodseeker"))
W(ability("Bloodrage"))
W(ul_open())
W(li("Attack Speed decreased from 60/90/120/150 to 55/80/105/130", b([60, 90, 120, 150], [55, 80, 105, 130])))
W(li("Aghanim's Shard target's max health as damage decreased from 2% to 1.5%", b(2, 1.5)))
W(ul_close())

# Centaur Warrunner
W(hero_header("Centaur Warrunner"))
W(ability("Horsepower"))
W(ul_open())
W(li("Strength as Bonus Movement Speed increased from 30% to 40%", b(30, 40)))
W(ul_close())

# Chaos Knight
W(hero_header("Chaos Knight"))
W(ul_open())
W(li("Base Damage increased by 3", bstat_h("Chaos Knight", "AttackDamageMin", "7.41", 3), extra=note_box(hero="Chaos Knight", field="AttackDamageMin", before_patch="7.41")))
W(li("Damage at level 1 increased from 53–73 to 56–76", br(53, 73, 56, 76)))
W(ul_close())

# Chen
W(hero_header("Chen"))
W(ability("Penitence"))
W(ul_open())
W(li("Damage increased from 50/75/100/125 to 50/100/150/200", b([50, 75, 100, 125], [50, 100, 150, 200])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Penitence Slow increased from +14% to +15%", b(14, 15)))
W(ul_close())

# Clockwerk
W(hero_header("Clockwerk"))
W(ability("Power Cogs"))
W(ul_open())
W(li("Mana Burn increased from 35/75/115/155 to 40/80/120/160", b([35, 75, 115, 155], [40, 80, 120, 160])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Battery Assault Damage increased from +24 to +25", b(24, 25)))
W(li("Level 20 Talent Power Cogs Mana Burn increased from +70 to +80", b(70, 80)))
W(ul_close())

# Death Prophet
W(hero_header("Death Prophet"))
W(ability("Spirit Siphon"))
W(ul_open())
W(li("Mana Cost decreased from 80 to 60", b(80, 60, l=True)))
W(ul_close())

# Doom
W(hero_header("Doom"))
W(ul_open())
W(li("Base Armor decreased by 1", bstat_h("Doom", "ArmorPhysical", "7.41", -1), extra=note_box(hero="Doom", field="ArmorPhysical", before_patch="7.41")))
W(ul_close())
W(ability("Lvl ? Pain", slug="doom_bringer_lvl_pain"))
W(ul_open())
W(li("Curse Damage decreased from 15% to 10%", b(15, 10)))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(ul_open())
W(li("Base Intelligence increased from 20 to 22", b(20, 22)))
W(li("Damage at level 1 increased from 39–45 to 41–47", br(39, 45, 41, 47)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Tornado Cooldown Reduction increased from 4s to 5s", b(4, 5, l=True)))
W(ul_close())

# Io
W(hero_header("Io"))
W(ability("Equilibrium"))
W(ul_open())
W(li_formula("Max Damage Amp and Max Heal Amplification decreased", "5% + 0.5% per level", "4% + 0.4% per level", lambda L: 5.0 + 0.5*L, lambda L: 4.0 + 0.4*L))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Attack Tethered Ally's Target Damage decreased from 75% to 50%", b(75, 50)))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
W(ability("Blade Fury"))
W(ul_open())
W(li("Cooldown decreased from 36/30/24/18s to 30/26/22/18s", b([36, 30, 24, 18], [30, 26, 22, 18], l=True)))
W(ul_close())
W(ability("Blade Dance"))
W(ul_open())
W(li("Critical Damage increased from 130/150/170/190% to 140/160/180/200%", b([130, 150, 170, 190], [140, 160, 180, 200])))
W(ul_close())

# Kez
W(hero_header("Kez"))
W(ability("Raptor Dance"))
W(ul_open())
W(li("Base Damage increased from 30/60/90 to 40/70/100", b([30, 60, 90], [40, 70, 100])))
W(ul_close())
W(ability("Raven's Veil"))
W(ul_open())
W(li("Buff Duration increased from 7/8/9s to 8/10/12s", b([7, 8, 9], [8, 10, 12])))
W(ul_close())

# Legion Commander
W(hero_header("Legion Commander"))
W(ability("Outfight Them!", slug="legion_commander_outfight_them"))
W(ul_open())
W(li("No longer grants a passive armor bonus before casting abilities", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Duel Duration decreased from +1s to +0.75s", b(1, 0.75)))
W(li("Level 25 Talent Moment of Courage Lifesteal increased from +75% to +100%", b(75, 100)))
W(ul_close())

# Leshrac
W(hero_header("Leshrac"))
W(ul_open())
W(li("Strength gain decreased from 2.8 to 2.5", b(2.8, 2.5)))
W(ul_close())
W(ability("Diabolic Edict"))
W(ul_open())
W(li("Damage per explosion decreased from 10/18/26/34 to 9/16/23/30", b([10, 18, 26, 34], [9, 16, 23, 30])))
W(ul_close())

# Lifestealer
W(hero_header("Lifestealer"))
W(ul_open())
W(li("Base Damage decreased by 3", bstat_h("Lifestealer", "AttackDamageMin", "7.41", -3), extra=note_box(hero="Lifestealer", field="AttackDamageMin", before_patch="7.41")))
W(li("Damage at level 1 decreased from 49–55 to 46–52", br(49, 55, 46, 52)))
W(ul_close())
W(ability("Ghoul Frenzy"))
W(ul_open())
W(li_formula("Bonus Attack Speed decreased", "5 per level", "4 per level", lambda L: 5.0*L, lambda L: 4.0*L))
W(ul_close())
W(ability("Rage"))
W(ul_open())
W(li("Movespeed Bonus decreased from 9/12/15/18% to 6/9/12/15%", b([9, 12, 15, 18], [6, 9, 12, 15])))
W(ul_close())
W(ability("Feast"))
W(ul_open())
W(li("Max HP per Hero Kill decreased from 10/15/20/25 to 10", b([10, 15, 20, 25], 10)))
W(ul_close())

# Meepo
W(hero_header("Meepo"))
W(ability("Divided We Stand"))
W(ul_open())
W(li("Evasion no longer diminishes when shared between Meepos and has full strength on each", t("BUFF")))
W(li("Clones can no longer copy Bottle", t("NERF")))
W(ul_close())

# Mirana
W(hero_header("Mirana"))
W(ability("Celestial Quiver"))
W(ul_open())
W(li_formula("Bonus Damage changed", "3 per level", "5 + 3 per level", lambda L: 3.0*L, lambda L: 5.0 + 3.0*L))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Celestial Quiver Damage increased from +35 to +40", b(35, 40)))
W(ul_close())

# Morphling
W(hero_header("Morphling"))
W(ul_open())
W(li("Agility gain increased from 3.9 to 4.2", b(3.9, 4.2)))
W(ul_close())

# Muerta
W(hero_header("Muerta"))
W(ability("The Calling"))
W(ul_open())
W(li("Cooldown decreased from 30s to 30/28/26/24s", b(30, [30, 28, 26, 24], l=True)))
W(ul_close())
W(ability("Pierce the Veil"))
W(ul_open())
W(li("Base Damage Bonus rescaled from 75% to 70/85/100%", b(75, [70, 85, 100])))
W(ul_close())

# Oracle
W(hero_header("Oracle"))
W(ability("Fortune's End"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 80", b(100, 80, l=True)))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
W(ul_open())
W(li("Cooldown increased from 90/85/80s to 100/90/80s", b([90, 85, 80], [100, 90, 80], l=True)))
W(ul_close())

# Phantom Lancer
W(hero_header("Phantom Lancer"))
W(ability("Spirit Lance"))
W(ul_open())
W(li("Slow Duration decreased from 3.75s to 3s", b(3.75, 3)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Spirit Lance Slow Duration decreased from +1.25s to +1s", b(1.25, 1)))
W(ul_close())

# Primal Beast
W(hero_header("Primal Beast"))
W(ability("Colossal"))
W(ul_open())
W(li("Now slightly grows in size when crossing an HP threshold", t("MISC")))
W(ul_close())

# Puck
W(hero_header("Puck"))
W(ability("Illusory Orb"))
W(ul_open())
W(li("Impact Damage decreased from 75/150/225/300 to 70/140/210/280", b([75, 150, 225, 300], [70, 140, 210, 280])))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(ability("Shadow Dance"))
W(ul_open())
W(li("Bonus Movement Speed decreased from 24/36/48% to 20/30/40%", b([24, 36, 48], [20, 30, 40])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +1 Agility gain/stolen per Essence Shift Stack replaced with +25s Essence Shift Duration", t("REWORK")))
W(li("Level 25 Talent +35s Essence Shift Duration replaced with +1 Agility gain/stolen per Essence Shift Stack", t("REWORK")))
W(ul_close())

# Spectre
W(hero_header("Spectre"))
W(ability("Spectral Dagger"))
W(ul_open())
W(li("Damage rescaled from 70/120/170/220 to 80/120/160/200", b([70, 120, 170, 220], [80, 120, 160, 200])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Health decreased from +325 to +300", b(325, 300)))
W(li("Level 25 Talent Dispersion decreased from +5% to +4%", b(5, 4)))
W(ul_close())

# Spirit Breaker
W(hero_header("Spirit Breaker"))
W(ability("Greater Bash"))
W(ul_open())
W(li("Aghanim's Scepter upgrade unit collision radius no longer affected by Area of Effect bonuses", t("NERF")))
W(ul_close())

# Techies
W(hero_header("Techies"))
W(ability("Proximity Mines", slug="techies_land_mines"))
W(ul_open())
W(li("Damage decreased from 450/575/750 to 400/550/700", b([450, 575, 750], [400, 550, 700])))
W(li("Portion of damage dealt on the edge of AoE decreased from 60% to 50%", b(60, 50)))
W(li("Minimum Damage decreased from 240/345/450 to 200/225/350", b([240, 345, 450], [200, 225, 350])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Proximity Mines Cooldown Reduction decreased from 3s to 2s", b(3, 2, l=True)))
W(ul_close())

# Tidehunter
W(hero_header("Tidehunter"))
W(ability("Leviathan's Catch"))
W(ul_open())
W(li("Fish spawn launch distance decreased from 400 to 200", b(400, 200)))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ability("Exposure Therapy"))
W(ul_open())
W(li_formula("Mana Restore increased", "3.75 + 0.25 per level", "4 + 0.5 per level", lambda L: 3.75 + 0.25*L, lambda L: 4.0 + 0.5*L))
W(ul_close())
W(ability("Chakram"))
W(ul_open())
W(li("Mana Cost decreased from 100/140/180 to 90/120/150", b([100, 140, 180], [90, 120, 150], l=True)))
W(li("Mana Cost per second decreased from 14/22/30 to 10/15/20", b([14, 22, 30], [10, 15, 20], l=True)))
W(ul_close())

# Tinker
W(hero_header("Tinker"))
W(ability("Deploy Turrets"))
W(ul_open())
W(li("Tinker Knockback increased from 350 to 400", b(350, 400)))
W(ul_close())

# Tiny
W(hero_header("Tiny"))
W(ability("Tree Grab"))
W(ul_open())
W(li("Number of Attacks increased from 4/5/6/7 to 5/6/7/8", b([4, 5, 6, 7], [5, 6, 7, 8])))
W(ul_close())
W(ability("Grow"))
W(ul_open())
W(li("Bonus Damage increased from 55/110/165 to 60/120/180", b([55, 110, 165], [60, 120, 180])))
W(li("Movement Speed Bonus increased from 10/15/20 to 10/20/30", b([10, 15, 20], [10, 20, 30])))
W(ul_close())

# Void Spirit
W(hero_header("Void Spirit"))
W(ul_open())
W(li("Base Mana Regen decreased by 0.6", bstat_h("Void Spirit", "StatusManaRegen", "7.41", -0.6), extra=note_box(hero="Void Spirit", field="StatusManaRegen", before_patch="7.41")))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ul_open())
W(li("Base Agility increased from 17 to 20", b(17, 20)))
W(li("Damage at level 1 increased from 47–59 to 49–61", br(47, 59, 49, 61)))
W(ul_close())
W(ability("Tailwind"))
W(ul_open())
W(li("Duration increased from 2s to 2.5s", b(2, 2.5)))
W(li("Aghanim's Scepter bonus is still +1s, so it's increased to 3.5s", t("BUFF")))
W(ul_close())
W(ability("Focus Fire", slug="windrunner_focusfire"))
W(ul_open())
W(li("Cooldown decreased from 70/50/30s to 50/40/30s", b([70, 50, 30], [50, 40, 30], l=True)))
W(ul_close())

# Wraith King
W(hero_header("Wraith King"))
W(ul_open())
W(li("Base Attack Time worsened from 1.7s to 1.8s", b(1.7, 1.8, l=True)))
W(li("Intelligence gain decreased from 1.6 to 1.4", b(1.6, 1.4)))
W(ul_close())
W(ability("Bone Guard"))
W(ul_open())
W(li("Skeleton Duration decreased from 46s to 40s", b(46, 40)))
W(ul_close())
W(ability("Mortal Strike"))
W(ul_open())
W(li("Cooldown rescaled from 6/5.5/5/4.5s to 5s", b([6, 5.5, 5, 4.5], 5, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Health decreased from +350 to +300", b(350, 300)))
W(li("Level 15 Talent Wraithfire Blast Stun Duration decreased from +1s to +0.75s", b(1, 0.75)))
W(ul_close())

write_footer()
save_html('patches/7.41a.html')

# ============================================================
# 7.41 content
# ============================================================
write_head("7.41", "24.03.2026")

# ===== GENERAL UPDATES =====
W(section("General Updates"))

W(plain_header("Global Changes"))
W(ul_open())
W(li("Facets removed from the game", t("DEL")))
W(li("Innate abilities no longer scale with other abilities' level", t("REWORK")))
W(li("All innate abilities that used to scale with other abilities now either provide unchangeable bonuses or improve on 'per level' basis", t("REWORK"),
     extra=inline_note(
         "Abilities that improve with hero level have a <b>base value</b> and an <b>increment value</b>. Some also specify the <b>number of levels required per increment</b>."
         "<br>Abilities that improve every level provide their increment value already at level 1."
     )))
W(li("Added UI icon that shows you which parameters increase with hero level and what is the current value. Some non-innate ability might have this per level UI as well", t("QoL"),
     extra=inline_note("Pressing ALT key will show base value and increment of the ability.")))
W(li("Abilities that had 'per level up' scaling changed to be 'per level'", t("MISC"),
     extra=inline_note("This mostly affects heroes reworked in update 7.40 and Largo.")))
W(li("Flagbearer Creep Experience Bounty increased from 57 to 60", b(57, 60)))
W(li("First +1 siege creep timing decreased from 35:00 to 30:00", b(35, 30, l=True)))
W(li("Second +1 siege creep timing now occurs at 60:00", t("NEW")))
W(li("Adjusted the meeting point of the lane creeps toward the offlane", t("MISC"),
     extra=inline_note(
         "Now offlane creeps are slightly slowed upon leaving the base for a couple of seconds. Safe lane creeps are slightly accelerated upon leaving the base for a couple of seconds. Both of these changes are effective until the 7:30 mark."
     )))
W(li("All sections of currents now give a max movement speed bonus of 150", t("BUFF"),
     extra=inline_note("Previously was only provided by sections on the base and near it, while other sections provided max bonus of 100.")))
W(ul_close())
W(plain_header("Map Objectives"))

W(subgroup("Tormentor"))
W(ul_open())
W(li("Tormentor's spawn preference has switched", t("MISC"),
     extra=inline_note("Now begins in the Bottom Chasm.")))
W(li("Unyielding Shield Base barrier increased from 2000 to 3000", b(2000, 3000)))
W(li("Unyielding Shield Barrier upgrade per minute increased from 20 to 50", b(20, 50)))
W(li("Unyielding Shield Base barrier regen decreased from 40 to 20", b(40, 20)))
W(li_formula("Unyielding Shield Barrier regen upgrade increased",
             "3.5 per minute", "5 per minute",
             lambda M: 3.5 * M, lambda M: 5.0 * M,
             levels=[0, 5, 10, 15, 20, 25, 30, 40, 50, 60],
             level_prefix='M', rework_badge=False))
W(li("Reflect Base damage reflection percentage decreased from 50% to 30%", b(50, 30)))
W(li("Reflect radius can now be seen by holding ALT key", t("QoL")))
W(li_formula("The Shining damage rescaled",
             "60",
             "20 + 2 per minute",
             lambda M: 60,
             lambda M: 20 + 2 * M,
             levels=[0, 5, 10, 15, 20, 25, 30, 40, 50, 60],
             level_fmt=lambda M: f"{M}:00",
             rework_badge=False,
             headline_level=30))
W(li("Now has 25% Status Resistance", t("NEW")))
W(li("No longer deals damage to neutral units", t("DEL")))
W(li("Player that got Aghanim's Shard will no longer receive 175 gold", t("DEL"),
     extra=inline_note(
         f'Total team gold reward decreased from <b>875 to 700</b> {b(875, 700)}'
         f' (total networth change decreased from <b>2275 to 2100</b> {b(2275, 2100)}).'
     )))
W(li("Reward if all players have Aghanim's Shard decreased from 455 gold to 415 gold", b(455, 415)))
W(ul_close())

W(subgroup("Roshan"))
W(ul_open())
W(li("Roshan's pit preference has switched", t("MISC"),
     extra=inline_note("Now begins in the Top Pit.")))
W(ul_close())

W(subgroup("Wisdom Shrines"))
W(ul_open())
W(li("Wisdom Shrines and Lotus Pools now reverse their countdowns if heroes from opposing teams enter the area, instead of pausing the countdown", t("REWORK")))
W(li_formula("Wisdom Shrine Experience changed",
             "280 per interval",
             "200 base and 300 per subsequent shrine",
             lambda N: 280 * N,
             lambda N: 200 + 300 * (N - 1),
             levels=[1, 2, 3, 4, 5, 6, 7],
             level_fmt=lambda N: f"#{N}",
             rework_badge=False,
             headline_level=2))
W(ul_close())
W(plain_header("Terrain Changes", terrain_link="7.41"))
W(ul_open())
W(li("Tormentor spawns have been positioned closer towards Lotus Pools", t("MISC")))
W(li("Tormentor spawn areas have been reduced to low ground relative to the lane's level", t("MISC")))
W(li("Lotus Pools have been moved slightly closer to their respective offlane tower", t("MISC")))
W(li("Twin Gates slightly moved away from the stairs towards the map border", t("MISC")))
W(li("The watcher between the safe lane tier 1 tower and the tormentor has been repositioned", t("MISC"),
     extra=inline_note(
         "Tormentor is on the low ground which has three stairs: one leading to the Lotus Pool, one leading to the lane, and one leading to even higher ground area with the Twin Gate."
         "<br>Twin Gate highground area is now smaller and has three stairs: one that leads to new Tormentor area, one that leads back to the lane, and one that goes two levels down straight to the end of the stream."
         "<br>Watcher is now between two stairs: one that goes down to the Tormentor and one that goes up to the Twin Gate."
     )))
W(li("Ancient neutral camps near stream ends demoted to medium camps and moved slightly towards bases", t("NERF")))
W(li("Medium neutral camp near offlane defender's gate has been demoted to a small neutral camp", t("NERF")))
W(li("The tier 1 safe lane towers have been moved slightly away from their pull camps and where the creeps meet", t("MISC")))
W(li("Radiant safe lane small camp has been slightly moved north away from the lane", t("MISC")))
W(li("Radiant safe lane hard camp's spawn box has been moved towards the offlane to remove a bad ward location", t("MISC")))
W(li("Radiant offlane tier 2 tower has been adjusted slightly to the left, such that creeps do not path on both sides of the tower", t("MISC")))
W(li("The ramp leading from the Radiant tier 1 tower to the stream has been decreased in width and moved away from the tower", t("MISC")))
W(li("The medium flooded camp near the safe lane tier 2 towers moved closer to the middle of the stream (substantially more for Dire than for Radiant)", t("MISC")))
W(li("The medium flooded camp near the safe lane tier 2 towers can now only evolve once into a hard camp, rather than into an Ancient Camp", t("NERF")))
W(li("The medium flooded camp near the bounty runes can now evolve twice into an Ancient Camp", t("REWORK")))
W(li("Removed several trees from Dire Safelane easy pull camp and Radiant Safelane hard pull camp", t("MISC")))
W(ul_close())
W(plain_header("Mechanics Changes"))

W(subgroup("Health Restoration"))
W(ul_open())
W(li("Health Restoration now applies to all forms of life gain", t("REWORK"), extra=inline_note("Previously, it did not apply to incoming heals")))
W(ul_close())
W(ul_open())
W(li("Incoming Heal Amplification now stacks diminishingly with Health Restoration instead of additively with Outgoing Heal Amplification", t("REWORK")))
W(li("Spells that previously had a separate value for incoming heal reduction now only modify Health Restoration " + info_tip(
        "Eye of Skadi's Cold Attack", "Spirit Vessel's Soul Release",
        "Omniknight's Guardian Angel with Aghanim's Scepter", "Pudge's Rot with Aghanim's Scepter",
        header="Affected spells:"), t("REWORK")))
W(ul_close())
W(ul_open())
W(li("As a result of the changes, spells that only modified Health Restoration will now additionally affect incoming heals " + info_tip(
        "Sange", "Kaya and Sange", "Sange and Yasha", "Abyssal Blade", "Orb of Frost's Frost",
        "Orb of Corrosion's Corrosion", "Crippling Crossbow's Hobble", "Jidi Pollen Bag's Pollinate",
        "Item bonus from Crude enchantment", "Abaddon’s Withering Mist",
        "Drow Ranger’s Frost Arrows with Aghanim’s Scepter", "Slark's Saltwater Shiv",
        header="Affected spells:"), t("REWORK")))
W(ul_close())

W(subgroup("Lifesteal and Damage Manipulations"))
W(ul_open())
W(li("Physical and Magical Lifesteal will now take into account overall damage reductions/amplifications when computing how much to lifesteal " + info_tip(
        "Aeon Disk", "Bloodstone", "Consecrated Wraps", "Veil of Discord", "Prophet's Pendulum",
        "Audacious Enchantment", "Abaddon's Borrowed Time with Aghanim's Scepter", "Beastmaster's Wild Axes",
        "Bounty Hunter's Shadow Walk with talent", "Bristleback's Bristleback", "Centaur Warrunner's Stampede",
        "Grimstroke's Ink Trail", "Grimstroke's Soulbind with talent", "Hoodwink's Hunter's Boomerang",
        "Leshrac's Pulse Nova with talent", "Lich's Frost Shield", "Luna's Lunar Orbit",
        "Kunkka's Admiral's Rum", "Mars' Bulwark", "Nyx Assassin's Burrow", "Ogre Magi's Fire Shield",
        "Oracle's False Promise", "Pudge's Flesh Heap", "Shadow Demon's Menace", "Spectre's Dispersion",
        "Treant Protector's Living Armor", "Underlord's Invading Force", "Undying's Flesh Golem",
        "Ursa's Enrage", "Visage's Gravekeeper's Cloak", "Warlock's Golem with talent",
        header="This affects the following:"), t("REWORK")))
W(ul_close())
W(ul_open())
W(li("Historically, Lifesteal was calculated before some damage reductions or amplifications were applied. As a result, you could gain health from attacks that dealt no damage (like attacks against a hero affected by Aeon Disk's Combo Breaker). This will not happen anymore", t("REWORK"), extra=inline_note("The only amplification that is not taken into account is increased damage against illusions")))
W(ul_close())

W(subgroup("Miscellaneous"))
W(ul_open())
W(li("Reflected damage cannot be reflected back", t("NEW")))
W(li("Lifesteal and Spell Lifesteal don't apply to reflected damage", t("NEW")))
W(li("Reflected damage doesn't affect Debuff Immune units", t("NEW")))
W(li("Units with free movement now can miss their attacks when attacking uphill targets " + info_tip(
        "Batrider during Firefly", "Dragon Knight during Elder Dragon Form with Aghanim's Scepter",
        "Lina during Flame Cloak", "Terrorblade's Reflection illusions",
        header="Affected units:"), t("NEW")))
W(li("All sources of reflection damage now have an ALT-note detailing mechanics of reflected damage " + info_tip(
        "Tormentor's Reflect ability", "Blade Mail (both active and passive)", "Chipped Vest", "Rattlecage",
        "Axe's Counter Helix", "Bristleback's Quill Spray triggered by Bristleback passive",
        "Centaur Warrunner's Retaliate", "Nyx Assassin's Spiked Carapace", "Queen of Pain's Scream of Pain",
        "Razor's Storm Surge", "Shadow Demon's Disseminate", "Spectre's Dispersion",
        "Tidehunter's Anchor Smash triggered by Kraken Shell passive", "Viper's Corrosive Skin",
        "Warlock's Fatal Bonds",
        header="The following items and abilities deal reflected damage:"), t("QoL")))
W(ul_close())

# ===== NEUTRAL CREEP UPDATES =====
W(section("Neutral Creep Updates"))
_NC_CDN = "../icons/units/npc_dota_neutral_"
W(unit_header("Kobold Foreman", _NC_CDN + "kobold_taskmaster.png"))
W(ul_open())
W(li("Damage increased from 22–24 to 24–26", b(23, 25)))
W(ul_close())
W(unit_header("Kobold Soldier", _NC_CDN + "kobold_tunneler.png"))
W(ul_open())
W(li("Damage increased from 20–21 to 22–23", b(20.5, 22.5)))
W(ul_close())
W(unit_header("Kobold", _NC_CDN + "kobold.png"))
W(ul_open())
W(li("Damage increased from 13–14 to 15–16", b(13.5, 15.5)))
W(ul_close())
W(unit_header("Vhoul Assassin", _NC_CDN + "gnoll_assassin.png"))
W(ul_open())
W(li("Damage decreased from 30–32 to 25–27", b(31, 26)))
W(ul_close())
W(unit_header("Ghost Scepter", _NC_CDN + "ghost.png"))
W(ul_open())
W(li("Damage decreased from 45–50 to 38–43", b(47.5, 40.5)))
W(ul_close())
W(unit_header("Harpy Stormcrafter", _NC_CDN + "harpy_storm.png"))
W(ability("Chain Lightning", icon_url="../icons/abilities/harpy_storm_chain_lightning.png"))
W(ul_open())
W(li("Damage rescaled from 140/180/220/260 to 120/170/220/270", b([140, 180, 220, 260], [120, 170, 220, 270])))
W(ul_close())
W(unit_header("Satyr Tormenter", _NC_CDN + "satyr_hellcaller.png"))
W(ability("Shockwave", icon_url="../icons/abilities/satyr_hellcaller_shockwave.png"))
W(ul_open())
W(li("Damage rescaled from 160 to 140/160/180/200", b(160, [140, 160, 180, 200])))
W(ul_close())
W(unit_header("Warpine Raider", _NC_CDN + "warpine_raider.png"))
W(ability("Seed Shot", icon_url="../icons/abilities/warpine_raider_seed_shot.png"))
W(ul_open())
W(li("Damage rescaled from 100 to 80/95/110/125", b(100, [80, 95, 110, 125])))
W(ul_close())
W(unit_header("Boglet", _NC_CDN + "froglet.png"))
W(ability("Arm of the Deep", icon_url="../icons/abilities/frogmen_arm_of_the_deep.png"))
W(ul_open())
W(li("After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown", t("MISC")))
W(ul_close())
W(subnote("Previously affected other copies of this ability"))
W(unit_header("Croaker", _NC_CDN + "grown_frog.png"))
W(ability("Tendrils of the Deep", icon_url="../icons/abilities/frogmen_tendrils_of_the_deep.png"))
W(ul_open())
W(li("After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown", t("MISC")))
W(ul_close())
W(subnote("Previously affected other copies of this ability"))
W(unit_header("Ancient Croaker", _NC_CDN + "ancient_frog.png"))
W(ability("Congregations of the Deep", icon_url="../icons/abilities/frogmen_congregation_of_the_deep.png"))
W(ul_open())
W(li("After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown", t("MISC")))
W(ul_close())
W(subnote("Previously affected other copies of this ability"))
W(ul_open())
W(li("Radius is now affected by Area of Effect bonuses", t("BUFF")))
W(ul_close())
W(unit_header("Ancient Marshmage", _NC_CDN + "ancient_frog_mage.png"))
W(ability("Water Bubble (Large)", icon_url="../icons/abilities/frogmen_water_bubble_large.png"))
W(ul_open())
W(li("Radius is now affected by Area of Effect bonuses", t("BUFF")))
W(ul_close())

# ===== ITEM UPDATES =====
W(section("Item Updates"))

W(plain_header("Shop Reshuffle", dynamics=False))
W(ul_open())
W(li("Items in all shop categories except for Consumables have been rearranged to accommodate new items", t("QoL")))
W(li("Consumables now includes Infused Raindrops", t("QoL")))
W(ul_close())

W(plain_header("Basic Items", dynamics=False))
W(item_header("Chasm Stone", new="New Miscellaneous Item"))
W(item_cost(800))
W(provides('+40 Area of Effect ' + info_tip("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack")))
W(item_header("Shawl", new="New Miscellaneous Item"))
W(item_cost(450))
W(provides('+10% Magic Resistance'))
W(item_header("Splintmail", new="New Equipment Item"))
W(item_cost(950))
W(provides('+7 Armor'))
W(item_header("Wizard Hat", new="New Miscellaneous Item"))
W(item_cost(250))
W(provides('+125 Mana'))
W(item_header("Chainmail"))
W(ul_open())
W(li("Cost decreased from 550g to 500g", b(550, 500, l=True)))
W(ul_close())
W(item_header("Cloak"))
W(ul_open())
W(li("Cost increased from 800g to 900g", b(800, 900, l=True)))
W(li("Magic Resistance bonus decreased from +20% to +18%", b(20, 18, l=True)))
W(ul_close())
W(item_header("Cornucopia"))
W(ul_open())
W(li("Item removed from the game", t("DEL")))
W(ul_close())
W(item_header("Orb of Frost"))
W(ul_open())
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Refresher Shard"))
W(ul_open())
W(li("Reset Cooldowns no longer refreshes items", t("DEL")))
W(ul_close())
W(item_header("Ring of Health"))
W(ul_open())
W(li("Item moved back to Secret Shop from Miscellaneous Shop", t("MISC")))
W(ul_close())
W(item_header("Void Stone"))
W(ul_open())
W(li("Item moved back to Secret Shop from Miscellaneous Shop", t("MISC")))
W(ul_close())
W(item_header("Voodoo Mask"))
W(ul_open())
W(li("Spell Lifesteal bonus increased from +12% to +15%", b(12, 15)))
W(ul_close())

W(plain_header("Upgrades", dynamics=False))
W(item_header("Consecrated Wraps", new="New Armor Item"))
W(components(('Vitality Booster', 1000), ('Shawl', 450), ('Crown', 450),
             recipe=('Recipe', 700), total=2600))
W(provides('+15% Magic Resistance, +250 Health, +6 All Attributes'))
W(ul_open())
W(li("Passive: Hallowed. Gain a stack every 3s, up to a maximum of 3 stacks. Whenever the wearer takes damage from a player-controlled unit or Roshan, all stacks are removed to create an all-damage barrier for 7s that absorbs 120 damage per removed stack (up to 360). If the wearer reached a max amount of stacks at least once in a game, regaining a stack provides a non-stacking buff that increases movespeed by 20% for 7s", t("NEW")))
W(li("Has no damage threshold, but doesn't proc from Health Loss damage (like Heartstopper Aura)", t("NEW")))
W(li("Can't gain stacks for 3s after taking damage from Roshan or player-controlled sources", t("NERF")))
W(ul_close())
W(item_header("Crella's Crozier", new="New Magical Item"))
W(components(('Ghost Scepter', 1500), ('Soul Booster', 3000),
             recipe=('Recipe', 300), total=4800))
W(provides('+6 All Attributes, +450 Health, +450 Mana'))
W(ul_open())
W(li("Active: Rite of Rumusque. The wearer enters ghost form for 4 seconds, becoming immune to physical damage, but is unable to attack and 30% more vulnerable to magic damage. Steals 5% movement speed from enemy heroes in a 900 radius every second. Movement speed steal lasts 1.5s. Bonuses stack and have duration refreshed on gaining new stacks. No Mana Cost. Cooldown: 20s", t("NEW")))
W(li("The ghost form and stolen speed can be dispelled off the wearer, but the stealing debuff that provides new stacks can't", t("NERF")))
W(li("Passive: Putrefaction Aura. Reduces health restoration of nearby enemy heroes by 30%. While Rite of Rumusque is active, the effect is increased to 75% and all of the lost Health Restoration is redirected to the wearer every second. Radius: 900", t("BUFF")))
W(ul_close())
W(item_header("Essence Distiller", new="New Support Item"))
W(components(('Urn of Shadows', 825), ('Chainmail', 500), ('Wizard Hat', 250),
             recipe=('Recipe', 200), total=1775))
W(provides('+1.75 Mana Regen, +3 All Attributes, +6 Armor, +150 Mana'))
W(ul_open())
W(li("Active: Soul Release. When cast on an ally, provides 40 health regeneration. If the ally is attacked by an enemy hero or Roshan, the effect is lost. When cast on an enemy, deals 25 damage per second, provides True Sight over them and shares their vision with the wearer's team. Both effects last 8 seconds. Can be cast on the ground to put a dormant effect that will latch to the first enemy hero that comes within 400 range from it. The effect waits for 15s and provides 400 vision until it disappears. Gains charges every time an enemy hero dies within 1500 units. Cast Range: 1000. No Mana Cost. Cooldown: 10s", t("NEW")))
W(li("Gains one charge if the wearer dies with an empty Essence Distiller", t("NEW")))
W(li("Gains two charges if Essence Distiller had no charges and an enemy hero dies within radius", t("NEW")))
W(ul_close())
W(item_header("Specialist's Array", new="Returning Armaments Item"))
W(components(('Blade of Alacrity', 1000), ('Broadsword', 1000),
             recipe=('Recipe', 550), total=2550))
W(provides('+20 Damage, +12 Agility'))
W(ul_open())
W(li("Passive: Splitshot. Ranged Only. Ranged attacks have a 30% chance to fire additional projectiles at up to 2 nearby enemies that aren't the original attack target within 120 degree angle in front of the wearer and within attack range + 150. The additional projectiles deal 20 + 75% damage of a normal attack and do not trigger on hit effects. The primary attack deals 20 + full damage of a normal attack when the ability procs", t("NEW")))
W(li("Doesn't work with other sources of secondary projectiles from hero abilities " + info_tip(
        "Gyrocopter's Flak Cannon", "Medusa's Split Shot", "Muerta's Gunslinger",
        header="Affected abilities:"),
     t("NEW")))
W(ul_close())
W(item_header("Hydra's Breath", new="New Armaments Item"))
W(components(("Specialist's Array", 2550), ('Dragon Lance', 1900), ('Orb of Venom', 350),
             recipe=('Recipe', 1100), total=5900))
W(provides('+25 Damage, +30 Agility, +15 Strength, +150 Attack Range (Ranged Only)'))
W(ul_open())
W(li("Passive: Miasma. Attacks poison the target for 3 seconds, dealing magical damage equal to 2.5% of the target's max health every second. If the debuff is reapplied, the duration is refreshed. Can't be applied by illusions or to Roshan", t("NEW")))
W(li("Passive: Polycephaly. Ranged attacks have a 30% chance to fire at up to 3 nearby enemies that aren't the original attack target within 120 degree angle in front of the wearer and within attack range + 150. The additional projectiles deal 20 + 75% damage of a normal attack and do not trigger on hit effects except for Miasma. The primary attack deals 20 + full damage of a normal attack when the ability procs", t("NEW")))
W(li("Similarly to Specialist's Array, doesn't work with other sources of secondary projectiles from hero abilities", t("NEW")))
W(ul_close())
W(item_header("Arcane Boots", changed=True))
W(auto_components_change("Arcane Boots", "7.41"))
W(properties_change(
    old=[],
    new=[("NEW", "+125 Mana")]))
W(ul_open())
W(li("Recipe cost decreased from 475 to 325 " + b(475, 325, l=True) + ". Total cost increased from 1400g to 1500g", b(1400, 1500, l=True)))
W(ul_close())
W(item_header("Guardian Greaves"))
W(ul_open())
W(li("Recipe cost increased from 1125 to 1175 " + b(1125, 1175, l=True) + ". Total cost increased from 4300g to 4450g (due to Arcane Boots cost increase)", b(4300, 4450, l=True)))
W(li("Mana Regen bonus decreased from +1.5 to +1", b(1.5, 1)))
W(li("Now also provides +150 Mana", t("NEW")))
W(ul_close())
W(item_header("Battle Fury", changed=True))
W(auto_components_change("Battle Fury", "7.41"))
W(ul_open())
W(li("Recipe cost decreased from 600 to 400 " + b(600, 400, l=True) + ". Total cost unchanged at 3900g", t("MISC")))
W(ul_close())
W(item_header("Black King Bar"))
W(ul_open())
W(li("Avatar duration changed from 9/8/7/6s to 9/8/7s", t("REWORK")))
W(ul_close())
W(item_header("Blade Mail", changed=True))
W(auto_components_change("Blade Mail", "7.41"))
W(properties_change(
    old=[("BUFF", "+6 Armor")],
    new=[("",     "+7 Armor", b(6, 7))]))
W(ul_open())
W(li("Recipe cost decreased from 750 to 450 " + b(750, 450, l=True) + ". Total cost increased from 2300g to 2400g", b(2300, 2400, l=True)))
W(ul_close())
W(item_header("Crimson Guard"))
W(ul_open())
W(li("Armor bonus decreased from +8 to +6", b(8, 6)))
W(li("Guard max health damage block decreased from 2.2% to 2%", b(2.2, 2)))
W(li("Guard base damage block rescaled from 70 for all units to 70 on melee heroes and buildings and 45 on ranged heroes", t("REWORK")))
W(ul_close())
W(item_header("Dagon", changed=True))
W(auto_components_change("Dagon", "7.41"))
W(properties_change(
    old=[("NERF", "+7/9/11/13/15 All Attributes"),
         ("DEL",  "+15/16/17/18/19% Spell Lifesteal")],
    new=[("",    "+6/7/8/9/10 All Attributes", b([7, 9, 11, 13, 15], [6, 7, 8, 9, 10])),
         ("NEW", "+200/210/220/230/240 Health"),
         ("NEW", "+350/375/400/425/450 Mana"),
         ("NEW", "+60/90/120/150/180 Cast Range " + info_tip(
             "Cast Range Bonus does not stack with Aether Lens or multiple Dagons",
             header="Stacking rules"))]))
W(ul_open())
W(li("Recipe cost unchanged at 1150. Total cost increased from 2800/3950/5100/6250/7400g to 3050/4200/5350/6500/7650g", b([2800, 3950, 5100, 6250, 7400], [3050, 4200, 5350, 6500, 7650], l=True)))
W(li("Energy Burst cast range decreased from 700/750/800/850/900 to 640", b([700, 750, 800, 850, 900], 640)))
W(li("Effective cast range with item's built-in Cast Range bonus decreased from 700/750/800/850/900 to 700/730/760/790/820", b([700, 750, 800, 850, 900], [700, 730, 760, 790, 820])))
W(li("Energy Burst no longer instantly kills non-ancient creeps", t("DEL")))
W(li("Energy Burst no longer heals for 75% of damage dealt", t("DEL")))
W(ul_close())
W(item_header("Dragon Lance"))
W(ul_open())
W(li("Ranged Attack Range bonus decreased from +140 to +130", b(140, 130)))
W(ul_close())
W(item_header("Hurricane Pike"))
W(ul_open())
W(li("Ranged Attack Range bonus decreased from +140 to +130", b(140, 130)))
W(li("Hurricane Thrust cast range on enemies decreased from 450 to 425", b(450, 425)))
W(li("Hurricane Thrust enemy push distance decreased from 450 to 425", b(450, 425)))
W(ul_close())
W(item_header("Drum of Endurance", changed=True))
W(auto_components_change("Drum of Endurance", "7.41"))
W(properties_change(
    old=[("BUFF", "+7 Strength"),
         ("DEL",  "+7 Intelligence")],
    new=[("",     "+8 Strength", b(7, 8))]))
W(ul_open())
W(li("Endurance now shares cooldown with Boots of Bearing", t("NERF")))
W(li("Swiftness Aura now also provides +2.5 Health Regen", t("NEW")))
W(li("Recipe cost increased from 500 to 525 " + b(500, 525, l=True) + ". Total cost unchanged at 1625g", t("MISC")))
W(ul_close())
W(item_header("Boots of Bearing"))
W(ul_open())
W(li("Endurance now shares cooldown with Drum of Endurance", t("NERF")))
W(li("No longer provides +8 Intelligence", t("DEL")))
W(li("Swiftness Aura now also provides +2.5 Health Regen", t("NEW")))
W(ul_close())
W(item_header("Eternal Shroud"))
W(ul_open())
W(li("Item removed from the game", t("DEL")))
W(ul_close())
W(item_header("Ethereal Blade"))
W(ul_open())
W(li("Can no longer be disassembled", t("DEL")))
W(ul_close())
W(item_header("Gleipnir", changed=True))
W(auto_components_change("Gleipnir", "7.41"))
W(ul_open())
W(li("Recipe cost decreased from 1100 to 400 " + b(1100, 400, l=True) + ". Total cost increased from 4550g to 4650g", b(4550, 4650, l=True)))
W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))
W(ul_close())
W(item_header("Glimmer Cape", changed=True))
W(auto_components_change("Glimmer Cape", "7.41"))
W(ul_open())
W(li("Recipe cost increased from 450 to 800 " + b(450, 800, l=True) + ". Total cost unchanged at 2150g", t("MISC")))
W(ul_close())
W(item_header("Hand of Midas"))
W(ul_open())
W(li("Transmute no longer prevents camp-clearing Madstone Bundles from spawning if it was used on the last creep in neutral camp", t("MISC")))
W(li("Getting guaranteed Madstone Bundle from Transmute used to prevent the camp-clearing bundle from spawning", t("MISC")))
W(ul_close())
W(item_header("Harpoon"))
W(ul_open())
W(li("Draw Forth can now target trees and will pull the caster to it, destroying all trees on the way", t("NEW")))
W(ul_close())
W(item_header("Heaven's Halberd", changed=True))
W(auto_components_change("Heaven's Halberd", "7.41"))
W(properties_change(
    old=[("DEL",  "+275 Health"),
         ("DEL",  "Damage Block (passive)"),
         ("BUFF", "+6 Health Regen")],
    new=[("NEW",  "+9 Armor"),
         ("NEW",  "+25% Evasion"),
         ("",     "+6.5 Health Regen", b(6, 6.5))]))
W(ul_open())
W(li("Disarm cooldown decreased from 20s to 16s", b(20, 16, l=True)))
W(li("Disarm cast range increased from 650 to 750", b(650, 750)))
W(li("Disarm duration increased from 3s to 3.5s", b(3, 3.5)))
W(li("Can no longer be disassembled", t("DEL")))
W(ul_close())
W(item_header("Kaya"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +40% to +30%", b(40, 30)))
W(ul_close())
W(item_header("Kaya and Sange"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +50% to +40%", b(50, 40)))
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Meteor Hammer"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +40% to +35%", b(40, 35)))
W(ul_close())
W(item_header("Yasha and Kaya"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +50% to +40%", b(50, 40)))
W(ul_close())
W(item_header("Lotus Orb"))
W(ul_open())
W(li("Can no longer be disassembled", t("DEL")))
W(ul_close())
W(item_header("Mage Slayer", changed=True))
W(auto_components_change("Mage Slayer", "7.41"))
W(properties_change(
    old=[("BUFF", "+5 Health Regen"),
         ("BUFF", "+2 Mana Regen"),
         ("BUFF", "+8 Damage"),
         ("DEL",  "+30 Attack Speed")],
    new=[("",     "+6 Health Regen",  b(5, 6)),
         ("",     "+2.5 Mana Regen",  b(2, 2.5)),
         ("",     "+15 Damage",       b(8, 15))]))
W(ul_open())
W(li("Mage Slayer damage per second increased from 20 to 40", b(20, 40)))
W(li("Total cost increased from 2800g to 3100g (change is bigger due to Cloak cost increase)", b(2800, 3100, l=True)))
W(li("Mage Slayer damage type changed from magical to physical", t("REWORK")))
W(ul_close())
W(item_header("Mask of Madness"))
W(ul_open())
W(li("Berserk armor reduction decreased from 8 to 7", b(8, 7, l=True)))
W(li("Berserk now also grants 30% Slow Resistance for the duration", t("NEW")))
W(li("Berserk bonus Movement Speed changed from +25 for all heroes to +8%/12% for Ranged/Melee", t("REWORK")))
W(ul_close())
W(item_header("Mekansm"))
W(ul_open())
W(li("Recipe cost increased from 800 to 850", t("MISC") + b(800, 850, l=True), extra=inline_note("Total cost unchanged at 1775g (due to Chainmail cost decrease)")))
W(ul_close())
W(item_header("Monkey King Bar"))
W(ul_open())
W(li("Damage bonus increased from +40 to +50", b(40, 50)))
W(li("Attack Speed bonus increased from +45 to +50", b(45, 50)))
W(li("Recipe cost increased from 600 to 900 " + b(600, 900, l=True) + ". Total cost increased from 4700g to 5000g", b(4700, 5000, l=True)))
W(li("Now also provides +50 Attack Range to melee heroes only", t("NEW")))
W(ul_close())
W(item_header("Nullifier", changed=True))
W(auto_components_change("Nullifier", "7.41"))
W(ul_open())
W(li("No longer provides +6 Health Regen", t("DEL")))
W(li("Total cost decreased from 4375g to 4350g", b(4375, 4350, l=True)))
W(ul_close())
W(item_header("Oblivion Staff"))
W(ul_open())
W(li("Mana Regen bonus increased from +1 to +1.25", b(1, 1.25)))
W(ul_close())
W(item_header("Orchid Malevolence", changed=True))
W(auto_components_change("Orchid Malevolence", "7.41"))
W(properties_change(
    old=[("BUFF", "+10 Damage"),
         ("NERF", "+3 Mana Regen"),
         ("BUFF", "+10 Intelligence"),
         ("DEL",  "+6 Health Regen")],
    new=[("",     "+20 Damage",       b(10, 20)),
         ("",     "+2.5 Mana Regen",  b(3, 2.5)),
         ("",     "+12 Intelligence", b(10, 12))]))
W(ul_open())
W(li("Recipe cost decreased from 450 to 300 " + b(450, 300, l=True) + ". Total cost unchanged at 3275g", t("MISC")))
W(ul_close())
W(item_header("Bloodthorn", changed=True))
W(auto_components_change("Bloodthorn", "7.41"))
W(properties_change(
    old=[("BUFF", "+10 Intelligence"),
         ("NERF", "+95 Attack Speed"),
         ("BUFF", "+3.25 Mana Regen"),
         ("BUFF", "+10 Damage"),
         ("DEL",  "+6.5 Health Regen")],
    new=[("",     "+25 Intelligence", b(10, 25)),
         ("",     "+70 Attack Speed", b(95, 70)),
         ("",     "+4 Mana Regen",    b(3.25, 4)),
         ("",     "+20 Damage",       b(10, 20))]))
W(ul_open())
W(li("Recipe cost increased from 450 to 600 " + b(450, 600, l=True) + ". Total cost decreased from 6625g to 6400g", b(6625, 6400, l=True)))
W(li("Soul Rend Mana Cost increased from 125 to 150", b(125, 150, l=True)))
W(ul_close())
W(item_header("Orb of Corrosion"))
W(ul_open())
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Eye of Skadi"))
W(ul_open())
W(li("Cold Attack no longer has a separate value for incoming heal reduction", t("MISC"),
     extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
W(li("Cold Attack health restoration reduction increased from 40% to 50%", b(40, 50)))
W(ul_close())
W(item_header("Pavise", changed=True))
W(auto_components_change("Pavise", "7.41"))
W(properties_change(
    old=[("NERF", "+250 Mana")],
    new=[("",     "+175 Mana", b(250, 175))]))
W(ul_open())
W(li("Recipe cost increased from 175 to 675 " + b(175, 675, l=True) + ". Total cost decreased from 1400g to 1350g", b(1400, 1350, l=True)))
W(ul_close())
W(item_header("Solar Crest", changed=True))
W(auto_components_change("Solar Crest", "7.41"))
W(properties_change(
    old=[("BUFF", "+4 Armor"),
         ("NERF", "+300 Mana"),
         ("BUFF", "+175 Health"),
         ("DEL",  "+4 All Attributes")],
    new=[("",     "+7 Armor",    b(4, 7)),
         ("",     "+200 Mana",   b(300, 200)),
         ("",     "+200 Health", b(175, 200))]))
W(ul_open())
W(li("Recipe cost unchanged at 500. Total cost unchanged at 2575g (due to Pavise cost decrease)", t("MISC")))
W(ul_close())
W(item_header("Perseverance"))
W(ul_open())
W(li("Health Regen bonus decreased from +6.5 to +5.5", b(6.5, 5.5)))
W(ul_close())
W(item_header("Phase Boots"))
W(ul_open())
W(li("Cost decreased from 1500g to 1450g (due to Chainmail cost decrease)", b(1500, 1450, l=True)))
W(ul_close())
W(item_header("Phylactery"))
W(ul_open())
W(li("Health Regen bonus decreased from +6.5 to +5.5", b(6.5, 5.5)))
W(ul_close())
W(item_header("Pipe of Insight", changed=True))
W(auto_components_change("Pipe of Insight", "7.41"))
W(ul_open())
W(li("Recipe Cost decreased from 800 to 675", t("MISC") + b(800, 675, l=True), extra=inline_note("Total cost unchanged at 3725g (due to Cloak cost increase)")))
W(li("Barrier no longer affects units that have been affected by Barrier within Pipe of Insight's cooldown", t("NERF")))
W(li("Insight Aura no longer provides 2.5 health regen", t("DEL")))
W(ul_close())
W(item_header("Radiance"))
W(ul_open())
W(li("Burn toggling no longer breaks invisibility nor stops channels", t("MISC")))
W(ul_close())
W(item_header("Refresher Orb"))
W(ul_open())
W(li("Health Regen bonus increased from +12 to +14", b(12, 14)))
W(li("Mana Regen bonus increased from +6 to +7", b(6, 7)))
W(li("Reset Cooldowns cooldown decreased from 180/190/200/210s to 180s", b([180, 190, 200, 210], 180, l=True),
     extra=inline_note("No longer scales with uses")))
W(li("Reset Cooldowns mana cost decreased from 400 to 325", b(400, 325, l=True)))
W(li("Reset Cooldowns no longer refreshes items", t("DEL")))
W(ul_close())
W(item_header("Revenant's Brooch"))
W(ul_open())
W(li("Spell Lifesteal bonus increased from +14% to +15%", b(14, 15)))
W(ul_close())
W(item_header("Sange"))
W(ul_open())
W(li("Slow Resistance bonus increased from +20% to +25%", b(20, 25)))
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Abyssal Blade"))
W(ul_open())
W(li("Slow Resistance bonus increased from +25% to +30%", b(25, 30)))
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Sange and Yasha"))
W(ul_open())
W(li("Status Resistance bonus increased from +15% to +16%", b(15, 16)))
W(li("Slow Resistance bonus increased from +25% to +30%", b(25, 30)))
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Shiva's Guard", changed=True))
W(auto_components_change("Shiva's Guard", "7.41"))
W(properties_change(
    old=[("BUFF", "+15 Armor"),
         ("DEL",  "+5 Strength"),
         ("DEL",  "+5 Agility"),
         ("DEL",  "+5 Intelligence"),
         ("DEL",  "+5 Health Regen")],
    new=[("",    "+17 Armor", b(15, 17)),
         ("NEW", "+75 Area of Effect")]))
W(ul_open())
W(li("Recipe cost decreased from 2050 to 1350 " + b(2050, 1350, l=True) + ". Total cost decreased from 5175g to 4500g", b(5175, 4500, l=True)))
W(li("Arctic Blast damage increased from 200 to 260", b(200, 260)))
W(li("Freezing Aura now pierces debuff immunity", t("NEW")))
W(li("Arctic Blast no longer increases damage taken from spells", t("DEL")))
W(li("Freezing Aura no longer reduces Health Restoration and Incoming Heal Amplification by 25%", t("DEL")))
W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))
W(li("Arctic Blast radius decreased from 900 to 825", t("MISC"),
     extra=inline_note("Effective spell radius unchanged due to item's built-in Area of Effect bonus")))
W(ul_close())
W(item_header("Spirit Vessel"))
W(ul_open())
W(li("Soul Release no longer has a separate value for incoming heal reduction", t("MISC"),
     extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
W(ul_close())
W(item_header("Tranquil Boots"))
W(ul_open())
W(li("Break now also goes on cooldown when the item is disassembled. Reassembling the item will remember the time remaining", t("REWORK")))
W(ul_close())
W(item_header("Veil of Discord", changed=True))
W(auto_components_change("Veil of Discord", "7.41"))
W(properties_change(
    old=[("DEL", "+4 Armor"),
         ("DEL", "+4 All Attributes"),
         ("DEL", "+4.5 Health Regen")],
    new=[("NEW", "+10 Intelligence"),
         ("NEW", "+175 Health"),
         ("NEW", "+18% Spell Lifesteal")]))
W(ul_open())
W(li("Magic Weakness renamed to Spell Weakness", t("MISC")))
W(ul_close())
W(item_header("Bloodstone", changed=True))
W(auto_components_change("Bloodstone", "7.41"))
W(properties_change(
    old=[("NERF", "+25% Spell Lifesteal"),
         ("BUFF", "+450 Health"),
         ("DEL",  "+3 Mana Regen")],
    new=[("",    "+20% Spell Lifesteal", b(25, 20)),
         ("",    "+650 Health",          b(450, 650)),
         ("NEW", "+15 Intelligence")]))
W(ul_open())
W(li("Bloodpact no longer has a 30s self debuff preventing repeated usage of Bloodpact", t("BUFF")))
W(li("Total cost increased from 4350g to 4700g", b(4350, 4700, l=True)))
W(li("Bloodpact no longer multiplies spell lifesteal bonus by 3. Now increases spell lifesteal to 60% instead", b(75, 60),
     extra=inline_note("Spell Lifesteal during Bloodpact decreased from 75% to 60%")))
W(li("Bloodpact no longer applies a basic dispel", t("DEL")))
W(li("Now also provides passive Spell Weakness Aura", t("NEW")))
W(li("Passive: Enemy units within 1200 radius take 12% increased damage from spells", "",
     extra=inline_note("Effect does not stack with Veil of Discord's Spell Weakness")))
W(ul_close())
W(item_header("Witch Blade"))
W(ul_open())
W(li("Recipe cost increased from 250 to 300", t("MISC") + b(250, 300, l=True), extra=inline_note("Total cost unchanged at 2775g (due to Chainmail cost decrease)")))
W(ul_close())
# ===== NEUTRAL ITEM UPDATES =====
W(section("Neutral Item Updates"))
W(plain_header("General changes", dynamics=False))
W(ul_open())
W(li("Tier 1 availability changed from 5:00 to 0:00", t("REWORK")))
W(li("Madstone crafting cost for Tier 1 items increased from 5 to 6", t("REWORK")))
W(ul_close())
W(plain_header("Artifact changes", dynamics=False))
W(ul_open())
W(li("Number of artifact choices increased from 4 to 5 for Tiers 2-5", t("REWORK")))
W(ul_close())
W(item_header("Ash Legion Shield"))
W(ul_open())
W(li("Shield Wall damage barrier increased from 140 to 160", b(140, 160)))
W(li("Shield Wall movement speed reduction increased from 12 to 20", b(12, 20, l=True)))
W(ul_close())
W(item_header("Chipped Vest"))
W(ul_open())
W(li("Chipper damage returned to attacking creeps decreased from 20 to 15", b(20, 15)))
W(ul_close())
W(item_header("Dagger of Ristul", new="Returning Tier 1 Artifact"))
W(ul_open())
W(li("Active: Imbrue. Increase attack damage by 25 for 8s. Health Cost: 100. Cooldown: 30s", t("NEW")))
W(ul_close())
W(item_header("Forager's Kit", new="New Tier 1 Artifact"))
W(ul_open())
# First li opens the ability-row box; subsequent lis without ability_row=True
# are treated as continuations by the box-wrapper state machine, so all 8
# rows land inside ONE shared bordered box.
W(li("When this item is off cooldown, the wearer can see trees that can be foraged. Standing next to one of those trees for 1s will give the wearer one of the following items. Cooldown: 60s. Tree reveal radius: 1200", t("NEW"), ability_row=True))
W(li("All items except for bag of gold are placed in inventory (if there are slots available) and can stack up to 5 times per slot.", t("NEW")))
W(li("&nbsp;", t("NEW")))
W(li("Possible items:", t("NEW")))
W(li("Ironwood Nut: Passively provides +3 Movement Speed. Grants +1 Primary Stat when consumed (+.4 all stats for universal heroes)", t("NEW")))
W(li("Tomo'kan Ringcap: Passively Provides +2 Intelligence. Can be consumed to instantly grant a target 50 + 5% of their maximum mana", t("NEW")))
W(li("Vital Toadstool: Passively Provides +2 Damage. Can be consumed to grant a target +1% Max Health Regeneration for 10s. If the unit is attacked by an enemy hero or Roshan the bonus is lost", t("NEW")))
W(li("Bag of Gold: Provides 30 gold to the wearer. Don't need to be picked up", t("NEW")))
W(ul_close())
W(item_header("Possessed Mask", new="Returning Tier 1 Artifact"))
W(ul_open())
W(li("Passive: Lifesteal. Attacks heal for 5 health", t("NEW"),
     extra=inline_note("This counts as lifesteal and is manipulated by Health Restoration")))
W(ul_close())
W(item_header("Stonefeather Satchel", new="New Tier 1 Artifact"))
W(ul_open())
W(li("Toggle: Transmogrify. Activate to switch the contents of the satchel between Feathers or Rocks. No Mana Cost. Cooldown: 6s.", t("NEW")))
W(li("Pound of Feathers: Increases movement speed by 12 and distance of forced movement effects on yourself by 30%", t("NEW")))
W(li("Pound of Rocks: Increases armor by 3 and decreases distance of forced movement effects by 30%", t("NEW")))
W(ul_close())
W(item_header("Weighted Dice"))
W(ul_open())
W(li("Loaded now also increases max base damage by 6", t("NEW")))
W(ul_close())
W(item_header("Crippling Crossbow"))
W(ul_open())
W(li("Hobble initial damage decreased from 75 to 25", b(75, 25)))
W(li("Hobble Max slow decreased from 80% to 50%", b(80, 50)))
W(li("Hobble Cast Range decreased from 800 to 650", b(800, 650)))
W(li("Hobble now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(li("Moved from Tier 4 to Tier 2", t("REWORK")))
W(ul_close())
W(item_header("Medallion of Courage", new="Returning Tier 2 Artifact"))
W(ul_open())
W(li("Active: Valor. If cast on an ally, increases their armor by 7 for 8s. If cast on an enemy, decreases their armor by 4 for 8s. Cannot be cast on self. Cast Range: 1000. Mana Cost: 30. Cooldown: 18s", t("NEW"),
     extra=inline_note("Dormant Curio increases duration from 8s to 10.4s")))
W(ul_close())
W(item_header("Searing Signet"))
W(ul_open())
W(li("Burn Through: Total Damage decreased from 90 to 80", b(90, 80)))
W(ul_close())
W(subnote("From 117 to 104 with Dormant Curio"))
W(ul_open())
W(li("Burn Through: Damage Threshold increased from 55 to 60", b(55, 60, l=True)))
W(ul_close())
W(item_header("Seeds of Serenity", new="Returning Tier 2 Artifact"))
W(ul_open())
W(li("Active: Verdurous Dale. Place a 400 unit circle on the ground for 8s that increases health regeneration of allies inside by 8 + 25% of the caster's health regeneration. Cast Range: 350. No Mana Cost. Cooldown: 35s", t("NEW"),
     extra=inline_note("Dormant Curio increases health regeneration from 8 to 10.4 and from 25% to 32.5%")))
W(ul_close())
W(item_header("Whisper of the Dread"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Cloak of Flames", new="Returning Tier 3 Artifact"))
W(ul_open())
W(li("Passive: Immolate. Burns enemy units in a 375 unit radius for 40 damage per second. Illusions deal 25 damage per second", t("NEW"),
     extra=inline_note("Dormant Curio increases damage from 40 to 52 and illusion damage from 25 to 32.5")))
W(ul_close())
W(item_header("Gunpowder Gauntlet"))
W(ul_open())
W(li("Beat the Crowd cooldown increased from 6s to 10s", b(6, 10, l=True)))
W(ul_close())
W(item_header("Jidi Pollen Bag"))
W(ul_open())
W(li("Pollinate health restoration loss increased from 30% to 50%", b(30, 50)))
W(li("Pollinate now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Partisan's Brand", new="New Tier 3 Artifact"))
W(ul_open())
W(li("Passive: Brand. Increases spell damage against player controlled units by 9%", t("NEW"),
     extra=inline_note("Dormant Curio increases bonus spell damage from 9% to 11.7%")))
W(li("Player controlled units includes heroes and any creep summoned or converted by them", t("NEW")))
W(ul_close())
W(item_header("Serrated Shiv"))
W(ul_open())
W(li("Gut 'Em cooldown increased from 1s to 1.5s", b(1, 1.5, l=True)))
W(ul_close())
W(item_header("Spellslinger", new="New Tier 3 Artifact"))
W(ul_open())
W(li("Passive: Salvo. Whenever you cast a spell, 20% of the spell's mana cost is restored over 10s. Tick rate: 2s", t("NEW"),
     extra=inline_note("Dormant Curio increases mana restored from 20% to 26%")))
W(li("Mana recovery duration cannot be modified", t("NERF")))
W(ul_close())
W(item_header("Stormcrafter", new="Returning Tier 3 Artifact"))
W(ul_open())
W(li("Passive: Bottled Lightning. Every 6s, zaps up to 2 enemies within 700 units, slowing them by 40% for 0.4s and dealing 70 magic damage", t("NEW"),
     extra=inline_note("Dormant Curio increases damage from 70 to 91")))
W(ul_close())
W(item_header("Conjurer's Catalyst", new="New Tier 3 Artifact"))
W(ul_open())
W(li("Passive: Spellover. Every 100 spell damage dealt to an enemy deals damage to their surrounding allies in a 300 unit radius. Hero targets deal 40 damage to their allies, other targets deal 15 damage", t("NEW"),
     extra=inline_note("Dormant Curio increases hero damage from 40 to 52 and non-hero damage from 15 to 19.5")))
W(ul_close())
W(item_header("Dandelion Amulet", new="Returning Tier 4 Artifact"))
W(ul_open())
W(li("Passive: Magical Damage Block. Blocks 300 magic damage from instances over 75 damage. Cooldown: 12s", t("NEW"),
     extra=inline_note("Dormant Curio increases blocked damage from 300 to 390")))
W(ul_close())
W(item_header("Enchanter's Bauble", new="New Tier 4 Artifact"))
W(ul_open())
W(li("Passive: Enchant. Increases bonuses of the item's Neutral Enchantment by 15%. Every time you craft this item again the bonus is increased by 40%", t("NEW"),
     extra=inline_note("Dormant Curio increases recraft stat bonus from 40% to 52%")))
W(li("You can select any Enchantments during re-craft and bonus will still keep increasing as long as you keep Enchanter's Bauble", t("NEW")))
W(ul_close())
W(item_header("Metamorphic Mandible"))
W(ul_open())
W(li("Pupate duration increased from 4s to 5s", b(4, 5)))
W(ul_close())
W(subnote("From 5.2s to 6.5s with Dormant Curio"))
W(ul_open())
W(li("Pupate bonus magic resistance increased from 35% to 50%", b(35, 50)))
W(ul_close())
W(item_header("Prophet's Pendulum", new="New Tier 4 Artifact"))
W(ul_open())
W(li("Passive: Linger. 30% of damage taken is delayed over 5 seconds. Damage Ticks every 1 second and is lethal", t("NEW"),
     extra=inline_note("Dormant Curio increases damage delayed from 30% to 39%")))
W(ul_close())
W(item_header("Rattlecage"))
W(ul_open())
W(li("Reverberate damage threshold increased from 180 to 220", b(180, 220)))
W(ul_close())
W(item_header("Harmonizer", new="New Tier 5 Artifact"))
W(ul_open())
W(li("Passive: Balance. Grants 5% mana cost reduction for every hero ability off cooldown and 6% spell amplification for every spell on cooldown", t("NEW"),
     extra=inline_note("Dormant Curio increases mana cost reduction from 5% to 6.5% and spell amplification from 6% to 7.8%")))
W(li("Item spells are affected by both effects, however item cooldowns don't affect the Harmonizer buff", t("NEW")))
W(li("The buff counts only current abilities that have cooldown, even if it's passive", t("NEW")))
W(li("Invoked abilities and sub-abilities don't count when they're hidden", t("NEW")))
W(ul_close())
W(item_header("Riftshadow Prism"))
W(ul_open())
W(li("Refract health cost decreased from 10% to 8%", b(10, 8, l=True)))
W(li("Refract incoming damage decreased from 240% to 200%", b(240, 200, l=True)))
W(ul_close())
W(item_header("Spider Legs"))
W(ul_open())
W(li("Skitter: Duration increased from 10s to 14s", b(10, 14)))
W(ul_close())
W(item_header("Witchbane", new="Returning Tier 5 Artifact"))
W(ul_open())
W(li("Active: Cleanse. Apply basic dispel on all units in a 300 unit radius area. Cast Range: 500. Mana Cost: 150. Cooldown: 40s", t("NEW")))
W(li("Passive: Subjugate. Your attacks deal bonus magical damage equal to 4% of target's Max Mana", t("NEW"),
     extra=inline_note("Dormant Curio increases damage from 4% to 5.2%")))
W(ul_close())
W(plain_header("Enchantment Changes", dynamics=False))
W(ul_open())
W(li("Number of Enchantment choices increased from 4 to 5 for Tiers 2-5", b(4, 5)))
W(li("Enchantments are no longer randomized. Now options are based on your hero's primary attribute, with some enchantments available to all heroes", t("REWORK")))
W(ul_close())

W(subgroup("Tier 1"))
W(enchant_tier_box([
    ("all", ["Quickened", "Vital"]),
    ("str", ["Brawny", "Tough"]),
    ("agi", ["Alert", "Brawny"]),
    ("int", ["Mystical", "Tough"]),
    ("uni", ["Alert", "Mystical"]),
], tiers=1))

W(subgroup("Tiers 2-3"))
W(enchant_tier_box([
    ("all", ["Quickened", "Greedy"]),
    ("str", ["Brawny", "Tough", "Crude"]),
    ("agi", ["Alert", "Brawny", "Nimble"]),
    ("int", ["Mystical", "Tough", "Keen-Eyed"]),
    ("uni", ["Alert", "Mystical", "Titanic"]),
], tiers=[2, 3]))

W(subgroup("Tier 4"))
W(enchant_tier_box([
    ("all", ["Quickened", "Timeless"]),
    ("str", ["Brawny", "Tough", "Crude"]),
    ("agi", ["Alert", "Brawny", "Nimble"]),
    ("int", ["Mystical", "Tough", "Keen-Eyed"]),
    ("uni", ["Alert", "Mystical", "Titanic"]),
], tiers=4))

W(subgroup("Tier 5"))
W(enchant_tier_box([
    ("all", ["Evolved", "Fleetfooted", "Timeless", "Vampiric"]),
    ("str", ["Hulking"]),
    ("agi", ["Audacious"]),
    ("int", ["Feverish"]),
    ("uni", ["Manic"]),
], tiers=5))
W(enchant_header("Boundless"))
W(ul_open())
W(li("Removed", t("DEL")))
W(ul_close())
W(enchant_header("Vast"))
W(ul_open())
W(li("Removed", t("DEL")))
W(ul_close())
W(enchant_header("Wise"))
W(ul_open())
W(li("Removed", t("DEL")))
W(ul_close())
W(enchant_header("Quickened"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for all heroes", t("REWORK")))
W(ul_close())
W(enchant_header("Vital", new="New Tier 1 Enchantment"))
W(ul_open())
W(li("+2 Health Regen", t("NEW")))
W(ul_close())
W(enchant_header("Brawny"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Strength and Agility heroes", t("REWORK")))
W(ul_close())
W(enchant_header("Tough"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Strength and Intelligence heroes", t("REWORK")))
W(ul_close())
W(enchant_header("Alert"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Agility and Universal heroes", t("REWORK")))
W(li("Attack Speed bonus decreased from +10/17/24/31 to +7/15/23/31", b([10, 17, 24, 31], [7, 15, 23, 31])))
W(ul_close())
W(enchant_header("Mystical"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Intelligence and Universal heroes", t("REWORK")))
W(li("No longer provides +100 Cast Range bonus at Tier 4", t("DEL")))
W(li("Now provides +15% Mana Cost/Mana Loss Reduction at Tier 4", t("NEW")))
W(ul_close())
W(enchant_header("Greedy", "greedy"))
W(ul_open())
W(li("Now is a guaranteed option for all heroes on Tiers 2-3", t("REWORK")))
W(ul_close())
W(enchant_header("Crude", "crude"))
W(ul_open())
W(li("Health Restoration bonus rescaled from +30/40% to +10/15/20%", b([30, 40], [10, 15, 20])))
W(li("Base Attack Time Reduction bonus rescaled from 12/18% to 8/12/16%", b([12, 18], [8, 12, 16])))
W(li("Intelligence Penalty increased from 5% to 6%", b(5, 6, l=True)))
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(li("Now is a guaranteed option for Strength heroes only", t("REWORK")))
W(li("Tiers changed from 4/5 to 2-4", t("REWORK")))
W(ul_close())
W(enchant_header("Nimble", new="New Tiers 2-4 Enchantment"))
W(ul_open())
W(li("+6/8/10% Movement Speed", t("NEW")))
W(li("+10/15/20 Damage", t("NEW")))
W(li("-1.5/2.25/3 <font color='#e03e2e'>Health Regen</font>", t("NEW")))
W(ul_close())
W(enchant_header("Keen-Eyed"))
W(ul_open())
W(li("Max Mana Penalty increased from 10% to 10/12/14%", b(10, [10, 12, 14], l=True)))
W(li("Cast Range bonus rescaled from +125/135 to +125/135/145", t("NEW")))
W(li("Mana Regen bonus rescaled from 1/1.5 to 1/1.5/2", t("NEW")))
W(li("Now is a guaranteed option for Intelligence heroes only", t("REWORK")))
W(li("Tiers changed from 2/3 to 2-4", t("REWORK")))
W(ul_close())
W(enchant_header("Titanic"))
W(ul_open())
W(li("Attack Damage bonus rescaled from +10/20% to +8/12/16%", b([10, 20], [8, 12, 16])))
W(li("Status Resistance rescaled from 10/15% to +10/12/14%", b([10, 15], [10, 12, 14])))
W(li("Now also provides -10/12/14% <font color='#e03e2e'>Attack Speed</font>", t("NEW")))
W(li("Now is a guaranteed option for Universal heroes only", t("REWORK")))
W(li("Tiers changed from 4/5 to 2-4", t("REWORK")))
W(ul_close())
W(enchant_header("Timeless"))
W(ul_open())
W(li("Now is a guaranteed Tiers 4-5 option for all heroes", t("REWORK")))
W(ul_close())
W(enchant_header("Evolved"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for all heroes", t("REWORK")))
W(ul_close())
W(enchant_header("Fleetfooted"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for all heroes", t("REWORK")))
W(ul_close())
W(enchant_header("Vampiric"))
W(ul_open())
W(li("Now is a guaranteed option for all heroes", t("REWORK")))
W(li("Tiers changed from 2-4 to 5", t("REWORK")))
W(li("Lifesteal bonus increased from +12/14/16% to +30%", b([12, 14, 16], 30)))
W(li("Spell Lifesteal increased from +6/8/10% to +20%", b([6, 8, 10], 20)))
W(li("Bonus Night Vision increased from +0/0/200 to +300", b([0, 0, 200], 300)))
W(ul_close())
W(enchant_header("Hulking", new="New Tier 5 Enchantment"))
W(ul_open())
W(li("+5% Max Health", t("NEW")))
W(li("+1.5% Max Health Regen", t("NEW")))
W(li("-30% <font color='#e03e2e'>Attack Speed</font>", t("NEW")))
W(ul_close())
W(enchant_header("Audacious"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for Agility heroes only", t("REWORK")))
W(ul_close())
W(enchant_header("Feverish"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for Intelligence heroes only", t("REWORK")))
W(ul_close())
W(enchant_header("Manic", new="New Tier 5 Enchantment"))
W(ul_open())
W(li("-18% Base Attack Time", t("NEW")))
W(li("+20% Cast Speed", t("NEW")))
W(li("-20% <font color='#e03e2e'>Vision</font>", t("NEW")))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))


# Abaddon
W(hero_header("Abaddon"))
W(ability("Withering Mist"))
W(ul_open())
W(li_formula("Health Restoration Reduction changed",
             "35%", "24.5% + 0.5% per level",
             lambda L: 35.0, lambda L: 24.5 + 0.5 * L))
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(ability("Mist Coil", slug="abaddon_death_coil"))
W(ul_open())
W(li("Damage/Heal increased from 95/160/225/290 to 95/170/245/320", b([95, 160, 225, 290], [95, 170, 245, 320])))
W(ul_close())
W(ability("Borrowed Time"))
W(ul_open())
W(li("Cooldown decreased from 90/85/80s to 85/75/65s", b([90, 85, 80], [85, 75, 65], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +10% Withering Mist Health Restoration Reduction replaced with +25 Curse of Avernus DPS", t("REWORK")))
W(li("Level 15 Talent +40 Curse of Avernus DPS replaced with -10s Borrowed Time Cooldown", t("REWORK")))
W(ul_close())

# Alchemist
W(hero_header("Alchemist"))
W(ability("Greevil's Greed", slug="alchemist_goblins_greed"))
W(ul_open())
W(li("Aghanim's Scepter now also increases Base Bonus Gold and Max Bonus Gold per kill by 6 per melted Aghanim's Scepter", t("NEW")))
W(ul_close())
W(ability("Corrosive Weaponry"))
W(ul_open())
W(li("Movement Slow per stack increased from 2/2.5/3/3.5% to 2.5/3/3.5/4%", b([2, 2.5, 3, 3.5], [2.5, 3, 3.5, 4])))
W(li("Base Attack Damage Reduction per stack increased from 2/2.5/3/3.5% to 2.5/3/3.5/4%", b([2, 2.5, 3, 3.5], [2.5, 3, 3.5, 4])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Unstable Concoction Radius increased from +125 to +150", b(125, 150)))
W(li("Level 15 Talent Damage per Greevil's Greed stack increased from +2.5 to +3", b(2.5, 3)))
W(li("Level 15 Talent Acid Spray grants armor to allies replaced with +1% Corrosive Weaponry Slow/Damage Reduction Per Stack", t("REWORK")))
W(ul_close())

# Ancient Apparition
W(hero_header("Ancient Apparition"))
_bc_pill, _bc_table = scale_pill(
    "0.1 + 0.1 per 3 levels",
    lambda L: 0.1 + 0.1 * (L // 3),
    levels=[1, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30],
    value_fmt="{:.2f}",
)
W(ability_change(
    old=dict(
        name="Death Rime",
        innate=True,
        desc=[
            "Passive.",
            "Ancient Apparition's abilities apply frost stacks that deal <b>10 damage per second</b> and <b>1.5% movement slow</b> for each stack on the enemy.",
        ],
    ),
    new=dict(
        name="Bone Chill",
        slug="ancient_apparition_bone_chill",
        innate=True,
        desc=[
            "Passive.",
            "When Ancient Apparition deals magic damage with his abilities, affected enemies are chilled for 4s, reducing their movement speed by 2% per stack. Each instance stacks and has independent duration.",
            "If the target is an enemy hero, the debuff also reduces their Strength by "
            + _bc_pill
            + ".",
            aghs_line("Increases Base Strength Reduction by 0.3."),
        ],
        tables=[_bc_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Cold Feet"))
W(ul_open())
W(li("Now deals 20/40/60/80 damage per second", t("NEW")))
W(ul_close())
W(ability("Ice Vortex"))
W(ul_open())
W(li("Now deals 10/20/30/40 damage per second", t("NEW")))
W(li("Now slows movement by 8%", t("NEW")))
W(ul_close())
W(ability("Chilling Touch"))
W(ul_open())
W(li("Mana Cost decreased from 45/50/55/60 to 35", b([45, 50, 55, 60], 35, l=True)))
W(li("Aghanim's Scepter no longer reduces mana cost", t("DEL")))
W(ul_close())
W(ability("Ice Blast"))
W(ul_open())
W(li("Now deals 12/24/36 damage per second", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +2 Cold Feet Death Rime Stacks replaced with +30 Cold Feet Damage Per Second", t("REWORK")))
W(li("Level 15 Talent Cold Feet Break Distance decreased from +300 to +250", b(300, 250)))
W(li("Level 25 Talent +50% Death Rime Slow/Damage replaced with 450 AoE Cold Feet", t("REWORK")))
W(ul_close())

# Anti-Mage
W(hero_header("Anti-Mage"))
W(ul_open())
W(li("Base Armor increased by 1", bstat_h("Anti-Mage", "ArmorPhysical", "7.40c", 1), extra=note_box(hero="Anti-Mage", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
W(ability("Persecutor", slug="antimage_persectur"))
W(ul_open())
W(li("No longer levels with Mana Void", t("REWORK")))
W(li_formula("Min Movement Slow rescaled",
             "12.5/15/17.5/20%", "12% + 0.5% per level",
             lambda L: 20.0, lambda L: 12.0 + 0.5 * L))
W(li_formula("Max Movement Slow rescaled",
             "25/30/35/40%", "24% + 1% per level",
             lambda L: 40.0, lambda L: 24.0 + 1.0 * L))
W(ul_close())
W(ability("Mana Break"))
W(ul_open())
W(li("Effectiveness when applied by illusions decreased from 50% to 25%", b(50, 25)))
W(li("Aghanim's Scepter: Increases Max Mana Burned per hit by an additional 1.5%", t("NEW")))
W(ul_close())
W(ability("Blink"))
W(ul_open())
W(li("Cast Range rescaled from 750/900/1050/1200 to 875/950/1025/1100", b([750, 900, 1050, 1200], [875, 950, 1025, 1100])))
W(li("Cooldown decreased from 12/10/8/6s to 10.5/9/7.5/6s", b([12, 10, 8, 6], [10.5, 9, 7.5, 6], l=True)))
W(li("Mana Cost increased from 50 to 65/60/55/50", b(50, [65, 60, 55, 50], l=True)))
W(li("Aghanim's Scepter no longer decreases cooldown by 1s", t("DEL")))
W(ul_close())
W(ability("Counterspell"))
W(ul_open())
W(li("Magic Resistance decreased from 16/24/32/40% to 14/21/28/35%", b([16, 24, 32, 40], [14, 21, 28, 35])))
W(li("Duration increased from 1.2s to 1.3s", b(1.2, 1.3)))
W(ul_close())
W(ability("Mana Void"))
W(ul_open())
W(li("Cooldown increased from 70s to 100/85/70s", b(70, [100, 85, 70], l=True)))
W(li("Radius decreased from 500 to 400/450/500", b(500, [400, 450, 500])))
W(li("Damage per 1 Mana Missing rescaled from 0.8/0.95/1.1 to 1", b([0.8, 0.95, 1.1], 1)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +1% Max Mana Mana Burn replaced with +0.2 Mana Void Damage Multiplier", t("REWORK")))
W(li("Level 20 Talent +0.2 Mana Void Damage Multiplier replaced with +150 Blink Cast Range", t("REWORK")))
W(li("Level 25 Talent +200 Blink Cast Range replaced with -1s Blink Cooldown", t("REWORK")))
W(ul_close())

# Arc Warden
W(hero_header("Arc Warden"))
W(ul_open())
W(li("Strength gain decreased from 2.4 to 2.2", b(2.4, 2.2)))
W(li("Agility gain decreased from 3.0 to 2.7", b(3.0, 2.7)))
W(li("Damage gain per level decreased from 3.6 to 3.4 as a result", b(3.6, 3.4)))
W(li("Base Movement Speed increased from 285 to 300", b(285, 300)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Runic Infusion",
        slug="arc_warden_runic_infusion",
        innate=True,
        desc=[
            "Passive.",
            "Upon activating any rune, Arc Warden gains the Regeneration Rune buff for 4s. Duration is reduced by 34% for activating Bounty or Water Runes.",
            "Activating a Wisdom Rune provides a full 4s buff. Activating a Regeneration Rune creates a stackable second effect.",
        ],
    ),
    new=dict(
        name="Runic Infusion",
        slug="arc_warden_runic_infusion",
        innate=True,
        desc=[
            "Passive.",
            "Whenever Arc Warden or the Tempest Double activates a Power Rune, Arc Warden permanently gains +1.5 all attributes.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Magnetic Field"))
W(ul_open())
W(li("The field now also pulls runes, and automatically activates ones that are inside. Rune Pull Force: 100. Rune Pull Radius: 800/1200/1600/2000", t("NEW")))
W(ul_close())
W(ability("Spark Wraith"))
W(ul_open())
W(li("Slow Duration increased from 0.5/0.6/0.7/0.8s to 0.7/0.8/0.9/1s", b([0.5, 0.6, 0.7, 0.8], [0.7, 0.8, 0.9, 1])))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Tempest Double"))
W(ul_open())
W(li_formula("Gold and XP Bounty rescaled",
             "180/240/300", "70 + 10 per level",
             lambda L: 300.0, lambda L: 70.0 + 10.0 * L))
W(li("Aghanim's Shard: The Tempest Double is infused with the bonuses of Arcane, Invisibility, and Haste Runes for 12s. These bonuses don't provide Runic Infusion stacks", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +50% Spark Wraith Damage replaced with +200 Spark Wraith Damage", t("REWORK")))
W(li("Level 25 Talent -1.1s Spark Wraith Activation Delay replaced with +30s Spark Wraith Duration", t("REWORK")))
W(li("Level 25 Talent Tempest Double Has No Penalties replaced with +1.5 Runic Infusion All Attributes Bonus (applies retroactively)", t("REWORK")))
W(ul_close())

# Axe
W(hero_header("Axe"))
W(ability_change(
    old=dict(
        name="Coat of Blood",
        innate=True,
        desc=[
            "Passive.",
            "Whenever Axe kills an enemy, he gains <b>+1 permanent armor</b>. Kills with Culling Blade give <b>2×</b> that amount.",
        ],
    ),
    new=dict(
        name="One Man Army",        innate=True,
        desc=[
            "Passive.",
            "Increases Axe's Strength by 50% of his armor, as long as there are no allied heroes within a 700 unit radius of him.",
            "The effect fades over 3s after an ally walks within range. Bonus Strength can be broken.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Culling Blade"))
W(ul_open())
W(li("Now each hero kill made with Culling Blade provides a permanent stack, which provides 1/1.5/2 armor depending on the current level of Culling Blade", t("NEW")))
W(ul_close())

# Bane
W(hero_header("Bane"))
W(ul_open())
W(li("Strength gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
W(li("Agility gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
W(li("Intelligence gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
W(li("Damage gain per level decreased from 3.6 to 3.4 as a result", b(3.6, 3.4),
     extra=inline_note("Bane is Universal — all three attribute decreases contribute")))
W(li("Attack Range increased from 400 to 425", b(400, 425)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Ichor of Nyctasha",
        slug="bane_ichor_of_nyctasha",
        innate=True,
        desc=[
            "Passive.",
            "Bane's attribute gains are always evenly distributed across all three attributes.",
            "Example: Belt of Strength that provides +6 Strength will instead increase all three attributes by 2.",
        ],
    ),
    new=dict(
        name="Ichor of Nyctasha",
        slug="bane_ichor_of_nyctasha",
        innate=True,
        desc=[
            "Passive.",
            "Every time Bane kills an enemy hero or they die under the effect of any debuff applied by Bane, they receive a Terror for the rest of the game.",
            "Each Terror stack decreases the enemy's status resistance to all Bane's debuffs by 5%. Max Terror stacks per hero: 5.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Nightmare"))
W(ul_open())
W(li("Now a Unit Vector Target Spell", t("REWORK")))
W(li("Sleeping units walk in Bane's chosen direction at a speed of 110", t("MISC"),
     extra=inline_note("Can be put on alt-cast to disable sleepwalking behavior")))
W(ul_close())

# Batrider
W(hero_header("Batrider"))
W(ability("Firefly"))
W(ul_open())
W(li("Now also provides an increasing movement speed bonus that reaches its maximum of 12/18/24/30% at the end of Firefly's duration", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +50 Flamebreak Knockback Distance replaced with +1s Smoldering Resin Duration", t("REWORK")))
W(li("Level 10 Talent +50 Sticky Napalm Radius replaced with +5% Firefly Max Movement Speed Bonus", t("REWORK")))
W(li("Level 15 Talent -8s Flaming Lasso Cooldown replaced with +0.5% Sticky Napalm Movement Slow", t("REWORK")))
W(li("Level 15 Talent +20 Movement Speed replaced with +30 Firefly Damage Per Second", t("REWORK")))
W(li("Level 20 Talent +4s Smoldering Resin Duration replaced with Attacks apply 1 Stack of Sticky Napalm", t("REWORK")))
W(li("Level 25 Talent +10 Sticky Napalm Damage replaced with +0.75s Flaming Lasso Duration", t("REWORK")))
W(ul_close())

# Beastmaster
W(hero_header("Beastmaster"))
_ib_pill, _ib_table = scale_pill(
    "7 + 3 per level",
    lambda L: 7.0 + 3.0 * L,
)
W(ability_change(
    old=dict(
        name="Rugged",
        innate=True,
        desc=[
            "Passive.",
            "Beastmaster's chance to <b>block damage from non-hero unit attacks</b> is increased to <b>100%</b> (from the melee hero base of 50%).",
        ],
    ),
    new=dict(
        name="Inner Beast",
        slug="beastmaster_inner_beast",
        innate=True,
        desc=[
            "Passive.",
            "Provides bonus Attack Speed to Beastmaster and units under his control: " + _ib_pill + ".",
        ],
        tables=[_ib_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Wild Axes"))
W(ul_open())
W(li("Damage per axe increased from 30/65/100/135 to 40/80/120/160", b([30, 65, 100, 135], [40, 80, 120, 160])))
W(li("Damage Amp per stack decreased from 6/9/11/13% to 5/6/7/8%", b([6, 9, 11, 13], [5, 6, 7, 8])))
W(li("Aghanim's Shard: Beastmaster's attacks on enemy heroes also apply the Wild Axes debuff of its corresponding level. Illusions of Beastmaster don't apply Wild Axes stacks", t("NEW")))
W(ul_close())
W(ability("Summon Razorback"))
W(ul_open())
W(li("Call of the Wild Boar renamed to Summon Razorback", t("MISC")))
W(li("Boar's armor increased by 1",
     bstat_u("npc_dota_beastmaster_boar", "ArmorPhysical", "7.40c", 1),
     extra=note_box(unit="npc_dota_beastmaster_boar", field="ArmorPhysical", before_patch="7.40c")))
W(li("Boar Attack Damage increased from 25/40/55/70 to 30/45/60/75", b([25, 40, 55, 70], [30, 45, 60, 75])))
W(ul_close())
W(ability_change(
    old=dict(
        name="Call of the Wild Hawk",
        slug="beastmaster_call_of_the_wild_hawk",
        desc=[
            "Active.",
            "Beastmaster summons a Hawk that circles around him and dives onto an enemy within 500 range, dealing 50/80/110/140 damage and rooting them for 0.25/0.5/0.75/1s.",
            "Hawk cannot be controlled, prioritizes heroes, and is killed upon Beastmaster's death. Hawk has an attack interval of 4s, but it scales with attack speed.",
            "Hawk Duration: 25s. Mana Cost: 50. Cooldown: 45/40/35/30s.",
            aghs_shard_line("Summons an additional Hawk."),
        ],
    ),
    new=dict(
        name="Summon Raptors",
        slug="beastmaster_summon_raptor",
        desc=[
            "Active. Now a separately leveled ability, occupying Inner Beast's old slot (Inner Beast moved to innate).",
            "Summons 2 hawks (with 0.75s delay between them) that circle around Beastmaster and dive onto an enemy within 500 range, dealing 60/95/130/165 damage and rooting them for 0.4/0.6/0.8/1s.",
            "Hawks now prioritize Beastmaster's current attack target when selecting their Dive target.",
            "Hawks are invisible whenever Beastmaster is invisible or affected by Smoke of Deceit. They do not attack while invisible.",
            "Mana Cost: 50. Cooldown: 30s.",
        ],
    ),
    summary="New ability.",
    tag="new",
))
W(ul_open())
W(li("Cooldown decreased from 45/40/35/30s to 30s", b([45, 40, 35, 30], 30, l=True)))
W(li("Dive Damage increased from 50/80/110/140 to 60/95/130/165", b([50, 80, 110, 140], [60, 95, 130, 165])))
W(li("Root Duration increased from 0.25/0.5/0.75/1s to 0.4/0.6/0.8/1s", b([0.25, 0.5, 0.75, 1], [0.4, 0.6, 0.8, 1])))
W(li("Hawk armor increased by 1",
     bstat_u("npc_dota_beastmaster_hawk", "ArmorPhysical", "7.40c", 1),
     extra=note_box(unit="npc_dota_beastmaster_hawk", field="ArmorPhysical", before_patch="7.40c")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent -5s Call of the Wild Cooldown replaced with +5 Armor", t("REWORK")))
W(li("Level 15 Talent +15 Inner Beast Attack Speed replaced with +200 Primal Roar Cast Range", t("REWORK")))
W(ul_close())

# Bloodseeker
W(hero_header("Bloodseeker"))
W(ability("Sanguivore"))
W(ul_open())
W(li_formula("Max Health Heal changed",
             "1.5% + 1.5% per level up", "1.5% per level",
             lambda L: 1.5 * L, lambda L: 1.5 * L))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Bloodrage"))
W(ul_open())
W(li("Now a no target ability that affects only Bloodseeker", t("REWORK")))
W(li("Pure damage based on target's max health with Aghanim's Shard now pierces Debuff Immunity", t("BUFF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Blood Rite Silence Duration increased from +2.5s to +3s", b(2.5, 3)))
W(ul_close())

# Bounty Hunter
W(hero_header("Bounty Hunter"))
W(ability_change(
    old=dict(
        name="Big Game Hunter",
        innate=True,
        desc=[
            "Passive.",
            "When getting a kill or assist on an enemy with a kill streak, Bounty Hunter gains <b>10% extra gold</b>.",
        ],
    ),
    new=dict(
        name="Big Game Hunter",
        innate=True,
        desc=[
            "Passive.",
            "Bounty Hunter receives <b>15% more kill and assist gold</b> if the dying enemy hero is <b>Big Game</b>. An enemy hero is considered Big Game if they are one of the <b>top 3 net worth heroes</b> on the enemy team."
            + inline_note(
                "Bounty Hunter has a list of heroes currently considered Big Game, accessible by pressing a special button over the innate."
                "<br>These heroes also have a debuff pointing out that they're among the three Big Game targets — visible only to Bounty Hunter and his allies."
            ),
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Jinada"))
W(ul_open())
W(li("Gold Steal increased from 12/20/28/36 to 15/22/29/36", b([12, 20, 28, 36], [15, 22, 29, 36])))
W(ul_close())
W(ability("Shadow Walk", slug="bounty_hunter_wind_walk"))
W(ul_open())
W(li("Now grants 8/12/16/20% bonus movement speed when active", t("BUFF"),
     extra=inline_note("Also applies to Friendly Shadow")))
W(ul_close())
W(ability("Track"))
W(ul_open())
W(li("No longer grants 12/16/20% bonus movement speed to Bounty Hunter", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Damage increased from +25 to +30", b(25, 30)))
W(ul_close())

# Brewmaster
W(hero_header("Brewmaster"))
W(ability("Liquid Courage"))
W(ul_open())
W(li_formula("Max Status Resist changed",
             "10.5% + 0.5% per level up", "10% + 0.5% per level",
             lambda L: 10.0 + 0.5 * L, lambda L: 10.0 + 0.5 * L))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Primal Split"))
W(ul_open())
W(li("Earth Brewling's Hurl Boulder Stun Duration decreased from 1.6/1.6/1.6/2s to 1.6/1.6/1.6/1.8s", b([1.6, 1.6, 1.6, 2], [1.6, 1.6, 1.6, 1.8])))
W(li("Storm Brewling's Cyclone Duration decreased from 3/4/5/6s to 3/3.75/4.5/5.25s", b([3, 4, 5, 6], [3, 3.75, 4.5, 5.25])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +1s Drunken Brawler Brewed Up / Extend Duration replaced with +2/1s Drunken Brawler Brewed Up / Extend Duration", t("REWORK")))
W(ul_close())

# Bristleback
W(hero_header("Bristleback"))
W(ability("Prickly"))
W(ul_open())
W(li_formula("Damage and debuff duration amplification changed",
             "10%", "4.5% + 0.5% per level",
             lambda L: 10.0, lambda L: 4.5 + 0.5 * L))
W(ul_close())
W(ability("Viscous Nasal Goo"))
W(ul_open())
W(li("Stack Limit increased from 4 to 6", b(4, 6)))
W(li("Now has the same duration on all units", t("NERF"),
     extra=inline_note("Used to have double duration on creeps")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +12% Spell Lifesteal replaced with -25 Bristleback Damage Threshold", t("REWORK")))
W(ul_close())

# Broodmother
W(hero_header("Broodmother"))
W(ability("Spider's Milk"))
W(ul_open())
W(li_formula("Hero Health as Heal changed",
             "2%", "1.9% + 0.1% per level",
             lambda L: 2.0, lambda L: 1.9 + 0.1 * L))
W(ul_close())
W(ability("Insatiable Hunger"))
W(ul_open())
W(li("Now also applies lifesteal to Spiderlings within 800 range of Broodmother", t("NEW")))
W(ul_close())
W(ability("Spin Web"))
W(ul_open())
W(li("Movespeed Bonus decreased from 10/22/34/46% to 10/20/30/40%", b([10, 22, 34, 46], [10, 20, 30, 40])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Spiderlings Health increased from +150 to +175", b(150, 175)))
W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +6 to +5", b(6, 5)))
W(li("Level 25 Talent -0.15s BAT during Insatiable Hunger now also affects Spiderlings within 800 range", t("NEW")))
W(ul_close())

# Centaur Warrunner
W(hero_header("Centaur Warrunner"))
W(ul_open())
W(li("Strength gain increased from 4.0 to 4.2", b(4.0, 4.2)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Rawhide",
        innate=True,
        desc=[
            "Passive.",
            "Centaur Warrunner permanently gains <b>+40 max health</b> every <b>120s</b>.",
        ],
    ),
    new=dict(
        name="Horsepower",
        innate=True,
        desc=[
            "Passive.",
            "Centaur Warrunner gains <b>30% of his Strength as bonus movement speed</b>."
            + inline_note("This movement speed bonus does not stack with bonuses from boots."),
        ],
    ),
    summary="New innate ability.",
    tag="new",
))

# Chaos Knight
W(hero_header("Chaos Knight"))
W(ability_change(
    old=dict(
        name="Reins of Chaos",
        innate=True,
        desc=[
            "Passive.",
            "Whenever illusions of Chaos Knight are created, there is a 50% chance that an additional 1 illusion will spawn.",
        ],
    ),
    new=dict(
        name="Fundamental Forging",
        innate=True,
        desc=[
            "Passive.",
            "When Chaos Knight crafts a neutral item, it gets an <b>additional random enchantment</b> that doesn't provide negative stats."
            + inline_note(
                "The random enchantment is selected from all available enchantments in that tier, including ones that are normally not available for Strength heroes."
                "<br>Due to negative stats, Chaos Knight can't randomly get Crude, Nimble, Keen-Eyed, Titanic, Greedy, Hulking, Audacious, Feverish, and Manic enchantments."
                "<br>The random enchantment is different from the one used in crafting."
            ),
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Reality Rift"))
W(ul_open())
W(li("Cooldown decreased from 18/14/10/6s to 15/12/9/6s", b([18, 14, 10, 6], [15, 12, 9, 6], l=True)))
W(ul_close())
W(ability("Chaos Strike"))
W(ul_open())
W(li("Critical Lifesteal increased from 24/36/48/60% to 30/40/50/60%", b([24, 36, 48, 60], [30, 40, 50, 60])))
W(ul_close())
W(ability("Phantasm"))
W(ul_open())
W(li("Aghanim's Scepter now provides a passive component to this ability", t("NEW"),
     extra=inline_note("Whenever an illusion of Chaos Knight is created, there is a 50% chance to create an additional illusion under Chaos Knight's control. Bonus illusion will be under Chaos Knight's control even if other illusions were made by an enemy.")))
W(li("Aghanim's Scepter no longer guarantees to create an additional illusion on cast", t("DEL")))
W(ul_close())

# Chen
W(hero_header("Chen"))
W(ability_change(
    old=dict(
        name="Summon Convert",
        innate=True,
        desc=[
            "Active, levels with Holy Persuasion.",
            "Chen summons a convert to fight for him. The convert gains bonuses from Holy Persuasion, including its abilities. Health is set to 200 + 80 × Chen's Level. The convert is considered a creep-hero.",
            "Only one convert can be summoned at a time, and it dies if Chen dies. Mana Cost: 50. Cooldown: 30s. Cooldown starts once the convert dies and automatically refreshes on Chen's respawn.",
            "Which creature is summoned depends on the chosen Facet. Summoned convert counts toward Holy Persuasion's Max Units limit.",
        ],
    ),
    new=dict(
        name="Zealot",
        slug="chen_zealot",
        innate=True,
        desc=[
            "Passive and active components. Improves with game's time.",
            "When Chen respawns, he is joined in battle by a Zealot — a melee creep warrior with the Martyrdom ability. Zealot has the same stats as the current melee creeps on his team (including super or mega form), but has 125 attack range, base damage increased by 2 per Chen's level, base health regen increased from 0.5 to 2.5, and doesn't have Runty attack type. Zealot respawns after 60s dead.",
            "<b>Martyrdom:</b> 500-range unit-targeted ability on the Zealot creep, targeting either an enemy or ally. When cast, the Zealot sacrifices itself, firing a projectile at 1000 speed dealing damage to enemies or healing allies. Damage = 25 + 20% of the Zealot's current health; healing = 50% of these values.",
            "Can also be cast on a controlled unit to teleport it to Chen after a 6s delay. Self-targeting teleports all controlled units. <b>Mana Cost:</b> 50. <b>Cooldown:</b> 10s."
            + inline_note("Mechanics moved from Divine Favor without any changes."),
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Holy Persuasion"))
W(ul_open())
W(li("Zealots receive the benefits from Holy Persuasion", t("NEW")))
W(li("Now may be cast on existing persuaded creeps that have not been damaged in the last 3 seconds to unsummon them", t("NEW"),
     extra=inline_note("Unsummoning a unit has a global cast range, costs no mana and sets ability to a 3s cooldown")))
W(li("Now increases all of creature's outgoing damage by 0/6/12/18% instead of only increasing attack damage by 4/8/12/16", t("REWORK")))
W(ul_close())
W(ability("Divine Favor"))
W(ul_open())
W(li("Self-casting no longer teleports Chen's creeps to him", t("DEL"),
     extra=inline_note("Still applies the Divine Favor buff to all of them")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +150 Convert Attack Speed replaced with +25% Zealot Health/Damage", t("REWORK")))
W(li("Level 15 Talent +14 Holy Persuasion Damage replaced with +12% Holy Persuasion Damage", t("REWORK")))
W(ul_close())

# Clinkz
W(hero_header("Clinkz"))
W(ul_open())
W(li("Base Movement Speed decreased from 290 to 285", b(290, 285)))
W(ul_close())
W(ability("Strafe"))
W(ul_open())
W(li("Skeleton attack speed multiplier decreased from 50% to 40%", b(50, 40)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Death Pact Health increased from +350 to +400", b(350, 400)))
W(ul_close())

# Clockwerk
W(hero_header("Clockwerk"))
W(ability_change(
    old=dict(
        name="Armor Power",
        innate=True,
        desc=[
            "Passive.",
            "Clockwerk's outgoing damage is increased by 0.25% per point of armor.",
        ],
    ),
    new=dict(
        name="Armor Power",
        innate=True,
        desc=[
            "Passive.",
            "Clockwerk's outgoing damage is increased by 0.25% per point of armor.",
            "Clockwerk can self-cast a Chainmail item to consume it, gaining +4 Armor per Chainmail consumed. Number of stacks is unlimited.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Battery Assault"))
W(ul_open())
W(li("Mana Cost decreased from 90 to 75/80/85/90", b(90, [75, 80, 85, 90], l=True)))
W(ul_close())
W(ability("Power Cogs"))
W(ul_open())
W(li("Clockwerk can now move freely through the cogs, sinking them down while walking over them. Other units can also walk over sunken Power Cogs", t("NEW")))
W(li("Mana Cost rescaled from 70 to 60/65/70/75", b(70, [60, 65, 70, 75], l=True)))
W(li("Mana Burn increased from 35/70/105/140 to 35/75/115/155", b([35, 70, 105, 140], [35, 75, 115, 155])))
W(ul_close())
W(ability_change(
    old=dict(
        name="Overclocking",
        slug="rattletrap_overclocking",
        desc=[
            "Active (Aghanim's Scepter upgrade). All of Clockwerk's abilities are supercharged for the duration:",
            "&nbsp;&nbsp;• Battery Assault damages and stuns all enemies within its radius.",
            "&nbsp;&nbsp;• Power Cogs increase Clockwerk's Attack Speed by 250 while he is inside.",
            "&nbsp;&nbsp;• Rocket Flare cooldown decreased to 3.5s and fires 2 additional flares to either side of the target.",
            "&nbsp;&nbsp;• Hookshot stun radius and duration increased by 50%.",
            "&nbsp;&nbsp;• Jetpack movement speed bonus increased from 20% to 40%.",
            "When duration expires, Clockwerk's movement and attack speed are slowed by 100% briefly.",
            "Duration: 13s. Mana: 90. Cooldown: 50s.",
        ],
    ),
    new=dict(
        name="Overclocking",
        slug="rattletrap_overclocking",
        desc=[
            "Active (Aghanim's Scepter upgrade). All of Clockwerk's abilities are supercharged for the duration:",
            "&nbsp;&nbsp;• Battery Assault damages and stuns all enemies within its radius — radius increased to 330.",
            "&nbsp;&nbsp;• Power Cogs radius increased to 330 and Clockwerk gets +25% bonus armor while near cogs.",
            "&nbsp;&nbsp;• Rocket Flare damage, vision and slow duration increased by 35%.",
            "&nbsp;&nbsp;• Hookshot stun radius and duration increased by 50%.",
            "&nbsp;&nbsp;• Jetpack movement speed bonus increased from 20% to 40%.",
            "Duration: 18s. Mana: 90. Cooldown: 50s.",
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ul_open())
W(li("Duration increased from 13s to 18s", b(13, 18)))
W(li("Now also increases Battery Assault radius to 330", t("NEW")))
W(li("Now also increases Power Cogs radius to 330 and provides 25% bonus armor to Clockwerk while he is near cogs", t("NEW")))
W(li("Now increases Rocket Flare damage, vision and slow duration by 35%", t("NEW")))
W(li("No longer increases Clockwerk's attack speed while inside Power Cogs", t("DEL")))
W(li("No longer decreases Rocket Flare cooldown to 3.5s", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.4s Rocket Flare Slow Duration replaced with +1.5 Mana Regen", t("REWORK")))
W(li("Level 15 Talent +2 Power Cogs Hits To Kill replaced with -10s Hookshot Cooldown", t("REWORK")))
W(li("Level 25 Talent Debuff Immunity Inside Power Cogs replaced with 3 Rocket Flare Charges", t("REWORK")))
W(ul_close())

# Crystal Maiden
W(hero_header("Crystal Maiden"))
_cm_pill, _cm_table = scale_pill(
    "30% + 2% per level",
    lambda L: 30.0 + 2.0 * L,
)
W(ability_change(
    old=dict(
        name="Blueheart Floe",
        innate=True,
        desc=[
            "Passive.",
            "Crystal Maiden has <b>50% Mana Regen Amplification</b>.",
        ],
    ),
    new=dict(
        name="Glacial Guard",
        slug="crystal_maiden_glacial_guard",
        innate=True,
        desc=[
            "Passive.",
            "A portion of the mana Crystal Maiden spends on her abilities is converted into a physical barrier for 8s. Barriers stack, but each instance has independent duration.",
            "Mana Spent to Barrier: " + _cm_pill + ".",
        ],
        tables=[_cm_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Arcane Aura", slug="crystal_maiden_brilliance_aura"))
W(ul_open())
W(li("Now also passively provides Crystal Maiden with 20/40/60/80% mana regen amplification", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +225 Attack Speed replaced with +20% Glacial Guard Mana Spent To Barrier", t("REWORK")))
W(ul_close())

# Dark Seer
W(hero_header("Dark Seer"))
W(ability_change(
    old=dict(
        name="Aggrandize",
        innate=True,
        desc=[
            "Passive.",
            "When Dark Seer levels up, he restores a percentage of his max Health and Mana. Restore percentage = <b>10% + 2% per hero level</b>. Disabled by Break.",
            "Also passively grants <b>1 Attack Speed per point of Intelligence</b>.",
        ],
    ),
    new=dict(
        name="Quick Wit",
        slug="dark_seer_aggrandize",
        innate=True,
        desc=[
            "Passive.",
            "Whenever Dark Seer casts an ability, he restores 8.5% of Max Health and 8.5% of Max Mana, plus 1.5% per Dark Seer level.",
            "Also provides Dark Seer with +1 attack speed for each point of Intelligence.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ul_open())
W(li("Max Health and Mana Restore base value decreased from 10% to 8.5%", b(10, 8.5)))
W(li("Now also provides Dark Seer +1 attack speed from each point of Intelligence", t("NEW")))
W(li("Aggrandize renamed to Quick Wit", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Ion Shell Provides +250 Max Health replaced with -1.5s Surge Cooldown", t("REWORK")))
W(ul_close())

# Dark Willow
W(hero_header("Dark Willow"))
W(ability_change(
    old=dict(
        name="Pixie Dust",
        innate=True,
        desc=[
            "Passive.",
            "Whenever a hero ability makes Dark Willow untargetable or hidden, she gains <b>+100% Health Regen</b> and <b>+100% Mana Regen</b> while in that state.",
        ],
    ),
    new=dict(
        name="Pixie Dust",
        innate=True,
        desc=[
            "Passive.",
            "Dark Willow's Health Regen and Mana Regen always have 20% Amplification.",
            "Amplification increases to 100% whenever she becomes untargetable or invulnerable.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Intelligence increased from +10 to +12", b(10, 12)))
W(li("Level 15 Talent Terrorize Cooldown Reduction increased from 15s to 20s", b(15, 20, l=True)))
W(ul_close())

# Dawnbreaker
W(hero_header("Dawnbreaker"))
W(ul_open())
W(li("Base damage increased by 6", bstat_h("Dawnbreaker", "AttackDamageMin", "7.40c", 6), extra=note_box(hero="Dawnbreaker", field="AttackDamageMin", before_patch="7.40c")))
W(li("Damage at level 1 increased from 50–54 to 56–60", br(50, 54, 56, 60)))
W(ul_close())
W(ability("Break of Dawn"))
W(ul_open())
W(li_formula("Max Damage Increase changed",
             "25%", "10% + 1% per level",
             lambda L: 25.0, lambda L: 10.0 + 1.0 * L))
W(li("Bonuses granted are now at their maximum for any daytime caused by Dawnbreaker's abilities for the entirety of that daytime", t("NEW")))
W(li("Aghanim's Scepter: Amplifies heals Dawnbreaker provides by Break of Dawn's current damage increase value", t("NEW")))
W(ul_close())
W(ability("Solar Guardian"))
W(ul_open())
W(li("Cooldown decreased from 120/105/90s to 110/100/90s", b([120, 105, 90], [110, 100, 90], l=True)))
W(li("Now causes a 6 second temporary daytime when the cast starts", t("NEW")))
W(li("Aghanim's Scepter no longer increases heal per pulse", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +15% Celestial Hammer Slow replaced with Celestial Hammer Trail Grants Movement Speed to Allies", t("REWORK")))
W(li("Level 10 Talent +15% Break of Dawn Max Damage replaced with +25% Luminosity Critical Strike Damage", t("REWORK")))
W(li("Level 15 Talent Solar Guardian Cooldown Reduction increased from 15s to 20s", b(15, 20)))
W(li("Level 15 Talent +40% Luminosity Critical Strike Damage replaced with +40% Celestial Hammer Trail/Hammer Damage", t("REWORK")))
W(ul_close())

# Dazzle
W(hero_header("Dazzle"))
W(ability("Weave", slug="dazzle_innate_weave"))
W(ul_open())
W(li("No longer levels with Nothl Projection", t("REWORK")))
W(li("Armor Change per stack rescaled from 0.5/0.75/1/1.25 to 1", b([0.5, 0.75, 1, 1.25], 1)))
W(li_formula("Duration changed", "8s", "6.9s + 0.1s per level",
             lambda L: 8.0, lambda L: 6.9 + 0.1*L, value_fmt="{:.1f}s"))
W(li("Aghanim's Shard: Applying a stack of Weave on an ally heals them for 60 per stack of Weave, including the stack that was just applied", t("NEW")))
W(ul_close())
W(ability("Nothl Projection"))
W(ul_open())
W(li("No longer does a hard dispel on Dazzle when projection ends", t("DEL")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())

# Death Prophet
W(hero_header("Death Prophet"))
W(ul_open())
W(li("Base Armor increased by 1", bstat_h("Death Prophet", "ArmorPhysical", "7.40c", 1), extra=note_box(hero="Death Prophet", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
W(ability("Witchcraft"))
W(ul_open())
W(li_formula("Movement speed bonus changed",
             "0.75% + 0.75% per level up", "0.5% + 0.75% per level",
             lambda L: 0.5 + 0.75 * L, lambda L: 0.5 + 0.75 * L))
W(li_formula("Cooldown Reduction changed",
             "0.75% + 0.75% per level up", "0.75% per level",
             lambda L: 0.75 * L, lambda L: 0.75 * L))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Silence"))
W(ul_open())
W(li("Projectile speed increased from 1400 to 1750", b(1400, 1750)))
W(ul_close())
W(ability("Exorcism"))
W(ul_open())
W(li("Ghost spawn rate improved from 0.35s to 0.25s", b(0.35, 0.25)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +12% Magic Resistance replaced with +200 Health", t("REWORK")))
W(li("Level 10 Talent +30 Attack Speed replaced with +75 Silence AoE", t("REWORK")))
W(li("Level 15 Talent +100 Silence AoE replaced with +50 Attack Speed", t("REWORK")))
W(li("Level 20 Talent +400 Health replaced with +6 Exorcism Spirits", t("REWORK")))
W(li("Level 25 Talent +8 Exorcism Spirits replaced with Deaths During Exorcism Extend Duration by +8s (both allied and enemy heroes count)", t("REWORK")))
W(ul_close())

# Disruptor
W(hero_header("Disruptor"))
W(ability("Electromagnetic Repulsion"))
W(ul_open())
W(li("Now deals damage equal to 1.5x of Disruptor's Intelligence", t("NEW")))
W(ul_close())
W(ability("Thunder Strike"))
W(ul_open())
W(li("Strike Damage increased from 25/55/85/115 to 30/60/90/120", b([25, 55, 85, 115], [30, 60, 90, 120])))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Kinetic Fence"))
W(ul_open())
W(li("Cast Range increased from 1050 to 1200", b(1050, 1200)))
W(li("Cooldown decreased from 20/18/16/14s to 14s", b([20, 18, 16, 14], 14, l=True)))
W(li("Duration increased from 2.6/3.2/3.8/4.4s to 4.4s", b([2.6, 3.2, 3.8, 4.4], 4.4),
     extra=inline_note("Can be increased with Kinetic Field Duration talent")))
W(li("Formation Delay increased from 0.4s to 1s", b(0.4, 1)))
W(li("Aghanim's Shard: Now grants the Kinetic Field ability. Has only one level instead of sharing levels with Kinetic Fence", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +10%/300 Glimpse Distance To Damage/Max increased to +15%/300", t("BUFF")))
W(li("Level 20 Talent +150 Electromagnetic Repulsion Radius/Knockback replaced with +75 Static Storm Radius", t("REWORK")))
W(li("Level 25 Talent +150 Static Storm Radius replaced with +6 Thunder Strike Strikes (also decreases Strike Interval by 50%)", t("REWORK"),
     extra=inline_note("As a result, increases overall duration from 6s to 9s — " + b(6, 9))))
W(li("Level 25 Talent -12s Glimpse Cooldown replaced with 2 Glimpse Charges", t("REWORK")))
W(ul_close())

# Doom
W(hero_header("Doom"))
W(ability_change(
    old=dict(
        name="Lvl ? Pain",
        slug="doom_bringer_lvl_pain",
        innate=True,
        desc=[
            "Passive.",
            "Doom's attacks deal <b>25% more damage</b> to enemies whose level is lower than his."
            + inline_note("Also works at level 30. Only Doom's own attacks count, not damage from allied sources."),
        ],
    ),
    new=dict(
        name="Lvl ? Pain",
        slug="doom_bringer_lvl_pain",
        innate=True,
        desc=[
            "Passive.",
            "When Doom attacks enemy heroes, he applies a curse upon them. After 2.5s, the cursed hero bursts with a pillar of fire, damaging itself and all enemy units in a 66 AoE for 15% of the damage taken from Doom (the hero) over this duration, including damage from the attack that applied the curse.",
            "If the cursed hero's level is a multiple of 6, the curse damage and radius will be increased by 66%.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Devour"))
W(ul_open())
W(li("Cooldown decreased from 70s to 66s", b(70, 66, l=True)))
W(li("Aghanim's Shard: Replaces cooldown with 2 charges with 66s restore time. Allows to devour Ancient Neutral Creeps. Gained spells also have 20% bonus AoE and 40% Spell Amplification", t("NEW")))
W(li("Now the default cast gained on learning Devour is the one that grants abilities of devoured creeps, and alt-cast state keeps the ones that Doom currently has", t("MISC")))
W(ul_close())
W(ability("Scorched Earth"))
W(ul_open())
W(li("Radius increased from 600 to 666", b(600, 666)))
W(li("Now also provides Doom with 7/8/9/10 bonus health regen", t("NEW")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Infernal Blade"))
W(ul_open())
W(li("Stun Duration increased from 0.6s to 0.66s", b(0.6, 0.66)))
W(ul_close())
W(ability("Doom"))
W(ul_open())
W(li("Damage per second increased from 25/45/65 to 25/45/66", b([25, 45, 65], [25, 45, 66])))
W(li("Aghanim's Scepter now also applies Break to affected enemies", t("NEW")))
W(li("Aghanim's Scepter no longer increases damage per second by 15", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Devour Can Target Ancients replaced with +66 Damage", t("REWORK")))
W(li("Level 15 Talent Scorched Earth Movement Speed increased from +5% to +7%", b(5, 7)))
W(li("Level 20 Talent -10s Scorched Earth Cooldown replaced with -10s Doom Cooldown", t("REWORK")))
W(li("Level 25 Talent Doom applies Break replaced with Permanent Scorched Earth (ability becomes toggleable with no mana cost and a 2.5s cooldown between toggles)", t("REWORK")))
W(ul_close())

# Dragon Knight
W(hero_header("Dragon Knight"))
W(ul_open())
W(li("Strength gain decreased from 3.6 to 3.2", b(3.6, 3.2)))
W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
W(ul_close())
W(ability("Breathe Fire"))
W(ul_open())
W(li("Damage Reduction rescaled from 30% to 20/24/28/32%", b(30, [20, 24, 28, 32])))
W(li("Cast range increased from 600 to 1000", b(600, 1000)))
W(li("Fixed the cast indicator not matching the actual damage range of the ability, and also to properly reflect cast range bonuses", t("QoL")))
W(ul_close())
W(ability("Dragon Tail"))
W(ul_open())
W(li("Now has 25 radius AoE by default", t("NEW")))
W(li("No longer has an Elder Dragon specific cast range", t("DEL")))
W(ul_close())
W(ability("Wyrm's Wrath"))
W(ul_open())
W(li("Now always grants the 10/20/30/40 bonus magic damage on attack, and 25/50/75/100 Area of Effect bonus", t("NEW")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Elder Dragon Form",
        slug="dragon_knight_elder_dragon_form",
        desc=[
            "Ultimate. No target, transforms Dragon Knight into a ranged dragon for the duration. Levels of the ability determine which dragon form is used.",
            "Level 1: Bonus attack range, +20 bonus move speed, and bonus attack damage. Splash damage 50% within 250 AoE.",
            "Level 2: Adds a Frost debuff on attacks that slows the target's attack and movement speed.",
            "Level 3: Adds a Corrosive poison on attacks that deals magical damage over time and affects buildings.",
            aghs_line("Upgrades to Level 4 Black Dragon (combined effects, magic resistance, free pathing). Also improves Wyrm's Wrath effectiveness while in Dragon Form."),
        ],
    ),
    new=dict(
        name="Elder Dragon Form",
        slug="dragon_knight_elder_dragon_form",
        desc=[
            "Ultimate. No target, transforms Dragon Knight into a ranged dragon for the duration. Now <b>evolves per level — bonuses are cumulative</b>:",
            "<b>Level 1 — Green Dragon:</b> Attacks apply a Corrosive poison that deals 25 magical damage per second for 3s. Affects buildings.",
            "<b>Level 2 — Red Dragon:</b> Attacks gain splash damage dealing 75% of attack damage to all enemies within 275 AoE. Splash also applies Corrosive poison; other attack modifiers only affect the primary target.",
            "<b>Level 3 — Blue Dragon:</b> Attacks also apply a Frost debuff (pierces Debuff Immunity) — 50 attack slow and 30% move slow. Splash attacks now apply both Corrosive poison and Frost to all affected units; other attack modifiers only affect the primary target.",
            "Bonus Move Speed: 25/30/35 (was flat 20). No longer provides bonus attack damage. Now also increases cast range of all abilities by 350 (doesn't affect items).",
            aghs_line("Upgrades to Level 4 Black Dragon: 40 Bonus Move Speed, 35 Corrosive Damage, 100% Splash Damage, 350 Splash Radius, 65 Attack Slow, 45% Movement Slow, +20% Magic Resistance, and free pathing. No longer improves Wyrm's Wrath effectiveness while in Dragon Form. Black Dragon stats slightly rescaled."),
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ul_open())
W(li("Bonus Move Speed increased from 20 to 25/30/35", b(20, [25, 30, 35])))
W(li("Now also increases cast range of all abilities by 350", t("NEW"),
     extra=inline_note("Doesn't affect items")))
W(li("Aghanim's Scepter Black Dragon stats slightly rescaled", t("REWORK")))
W(li("No longer provides bonus attack damage", t("DEL")))
W(li("Aghanim's Scepter no longer improves Wyrm's Wrath effectiveness while in Dragon Form", t("DEL")))
W(ul_close())
W(ability("Fireball"))
W(ul_open())
W(li("No longer has an Elder Dragon specific cast range", t("DEL")))
W(li("Damage per second increased from 75 to 85", b(75, 85)))
W(li("Duration decreased from 8s to 6s", b(8, 6)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +60% Breathe Fire Damage/Cast Range replaced with +200 Breathe Fire Damage", t("REWORK")))
W(li("Level 25 Talent +50% Wyrm's Wrath effect during Elder Dragon Form replaced with +50% Wyrm's Wrath Bonuses", t("REWORK")))
W(ul_close())

# Drow Ranger
W(hero_header("Drow Ranger"))
W(ul_open())
W(li("Base Damage decreased by 2", bstat_h("Drow Ranger", "AttackDamageMin", "7.40c", -2), extra=note_box(hero="Drow Ranger", field="AttackDamageMin", before_patch="7.40c")))
W(li("Damage at level 1 decreased from 51–58 to 49–56", br(51, 58, 49, 56)))
W(ul_close())
W(ability("Precision Aura", slug="drow_ranger_trueshot"))
W(ul_open())
W(li("No longer levels with Marksmanship", t("REWORK")))
W(li("Agility Base Bonus rescaled from 4/8/12/16% to 10%", b([4, 8, 12, 16], 10)))
W(ul_close())
W(ability("Frost Arrows"))
W(ul_open())
W(li("Now also modifies incoming healing with Aghanim's Scepter", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(ability("Gust", slug="drow_ranger_wave_of_silence"))
W(ul_open())
W(li("Knockback duration now scales inversely with distance from the target, similar to knockback distance. Minimum knockback duration is 0.4 seconds", t("REWORK")))
W(ul_close())
W(ability("Multishot"))
W(ul_open())
W(li("Now allows Drow Ranger to move with a 35% penalty and use items while casting Multishot", t("NEW")))
W(ul_close())
W(ability("Glacier"))
W(ul_open())
W(li("Now Drow Ranger deals 25% more damage when attacking from high ground while on the Glacier", t("NEW")))
W(li("No longer increases the number of Multishot arrows", t("DEL")))
W(li("No longer grants True Strike on the hill", t("DEL")))
W(ul_close())

# Earth Spirit
W(hero_header("Earth Spirit"))
W(ability("Stone Remnant", slug="earth_spirit_stone_caller"))
W(ul_open())
W(li_formula("Max Charges changed",
             "7 + 1 per 4 level ups", "7 + 1 per 4 levels",
             lambda L: 7 + (L - 1) // 4, lambda L: 7 + L // 4,
             levels=[1, 4, 8, 12, 16, 20, 24, 28, 30],
             value_fmt="{:.0f}"))
W(ul_close())
W(subnote("Bonus charges are gained 1 level earlier (on levels 4/8/12... instead of 5/9/13...)"))
W(ability("Boulder Smash"))
W(ul_open())
W(li("Slow Duration increased from 1.25/2.5/3.25/4s to 1.75/2.5/3.25/4s", b([1.25, 2.5, 3.25, 4], [1.75, 2.5, 3.25, 4])))
W(ul_close())
W(ability("Geomagnetic Grip"))
W(ul_open())
W(li("Silence Duration increased from 2/2.5/3/3.5s to 2.3/2.7/3.1/3.5s", b([2, 2.5, 3, 3.5], [2.3, 2.7, 3.1, 3.5])))
W(ul_close())
W(ability("Magnetize"))
W(ul_open())
W(li("Damage per second increased from 45/85/125 to 45/90/135", b([45, 85, 125], [45, 90, 135])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Geomagnetic Grip Remnant Damage increased from +175 to +250", b(175, 250)))
W(ul_close())

# Earthshaker
W(hero_header("Earthshaker"))
W(ability("Slugger"))
W(ul_open())
W(li("No longer levels with Echo Slam", t("REWORK")))
W(li_formula("Damage (Creep Death) changed",
             "30/45/60/75", "27 + 3 per level",
             lambda L: 75.0, lambda L: 27.0 + 3.0 * L))
W(li_formula("Damage (Hero Death) changed",
             "150/250/350/450", "135 + 15 per level",
             lambda L: 450.0, lambda L: 135.0 + 15.0 * L))
W(ul_close())
W(ability("Fissure"))
W(ul_open())
W(li("Stun Duration increased from 0.8/1.0/1.2/1.4s to 1.0/1.2/1.4/1.6s", b([0.8, 1.0, 1.2, 1.4], [1.0, 1.2, 1.4, 1.6])))
W(ul_close())
W(ability("Aftershock"))
W(ul_open())
W(li("Radius increased from 300 to 350", b(300, 350)))
W(ul_close())
W(ability("Echo Slam"))
W(ul_open())
W(li("Shockwave projectile speed increased from 550 to 650", b(550, 650)))
W(ul_close())

# Elder Titan
W(hero_header("Elder Titan"))
_et_pill, _et_table = scale_pill(
    "3.6% + 0.4% per level",
    lambda L: 3.6 + 0.4 * L,
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Tip The Scales",
        innate=True,
        desc=[
            "Passive.",
            "(7.37 introduction did not include a mechanic line in the patchnote — needs canonical in-game text.)",
        ],
    ),
    new=dict(
        name="Momentum",        innate=True,
        desc=[
            "Passive.",
            "Elder Titan's armor increases by " + _et_pill + " of his bonus movement speed."
            '<div class="inline-note">Only counts movement speed he has above his base (305) value. '
            'Cannot reduce armor when he is slowed below base movement speed.</div>',
        ],
        tables=[_et_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Astral Spirit", slug="elder_titan_ancestral_spirit"))
W(ul_open())
W(li("No longer provides armor on return", t("DEL"),
     extra=inline_note("Still grants movement speed, which is then used by the innate ability to provide armor")))
W(ul_close())
W(ability("Earth Splitter"))
W(ul_open())
W(li("Cooldown decreased from 100s to 100/95/90s", b(100, [100, 95, 90], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +25 Attack Speed replaced with +150 Echo Stomp Wake Damage", t("REWORK")))
W(li("Level 15 Talent +25 Astral Spirit Hero Attack replaced with 20% of Bonus Movement Speed as Attack Speed", t("REWORK")))
W(li("Level 20 Talent +350 Echo Stomp Wake Damage replaced with +30 Astral Spirit Bonus Damage per Hero", t("REWORK")))
W(ul_close())

# Ember Spirit
W(hero_header("Ember Spirit"))
W(ul_open())
W(li("Strength gain increased from 2.3 to 2.5", b(2.3, 2.5)))
W(ul_close())
W(ability("Immolation"))
W(ul_open())
W(li("No longer levels with Fire Remnant", t("REWORK")))
W(li_formula("Damage per second changed",
             "10/18/26/34", "10 + 1 per level",
             lambda L: 34.0, lambda L: 10.0 + 1.0 * L))
W(li("Radius increased from 175 to 200", b(175, 200)))
W(li("Aghanim's Shard bonus radius decreased from 175 to 150", b(175, 150)))
W(ul_close())
W(subnote("Total Shard radius unchanged with base radius increase"))
W(ability("Searing Chains"))
W(ul_open())
W(li("Mana Cost decreased from 95/105/115/125 to 80/90/100/110", b([95, 105, 115, 125], [80, 90, 100, 110], l=True)))
W(ul_close())
W(ability("Sleight of Fist"))
W(ul_open())
W(li("Bonus Hero Damage increased from 25/70/115/160 to 50/90/130/170", b([25, 70, 115, 160], [50, 90, 130, 170])))
W(ul_close())

# Enchantress
W(hero_header("Enchantress"))
W(ability("Rabble-Rouser", slug="enchantress_rabblerouser"))
W(ul_open())
W(li_formula("Damage Increase changed",
             "4% + 4% per level up", "4% per level",
             lambda L: 4.0 * L, lambda L: 4.0 * L))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Enchant"))
W(ul_open())
W(li("Cast Range increased from 500/550/600/650 to 500/600/700/800", b([500, 550, 600, 650], [500, 600, 700, 800])))
W(li("Now enchanting enemy heroes increases attack range against them by 50/100/150/200 for Enchantress and units under her control", t("NEW")))
W(ul_close())
W(ability("Nature's Attendants"))
W(ul_open())
W(li("Added a tooltip to display the total max possible heal", t("QoL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Untouchable Attack Slow increased from +70 to +80", b(70, 80)))
W(ul_close())

# Enigma
W(hero_header("Enigma"))
_en_pill, _en_table = scale_pill(
    "4% + 1% per level",
    lambda L: 4 + 1 * L,
)
W(ability_change(
    old=dict(
        name="Gravity Well",
        innate=True,
        desc=[
            "Passive, scales with Black Hole.",
            "Allies in a 500 unit radius around Enigma have an Incoming Damage Reduction buff that gradually increases with proximity: 0% at 500 distance, up to 9/11/13/15% at 200 distance.",
            "Doesn't affect Enigma itself.",
        ],
    ),
    new=dict(
        name="Event Horizon",        innate=True,
        desc=[
            "Passive.",
            "Units in a 600 radius moving away from Enigma have a movespeed penalty equal to " + _en_pill + ".",
        ],
        tables=[_en_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +60 Malefice Instance Damage replaced with +100 Event Horizon Radius", t("REWORK")))
W(ul_close())

# Faceless Void
W(hero_header("Faceless Void"))
W(ability_change(
    old=dict(
        name="Distortion Field",
        innate=True,
        desc=[
            "Passive, levels up with Chronosphere.",
            "Enemy attack projectiles are slowed when they fly near Faceless Void. Affects projectiles even if Faceless Void isn't the target.",
            "<b>Projectile Slow:</b> 25/30/35/40%. <b>Radius:</b> 500.",
        ],
    ),
    new=dict(
        name="Distortion Field",
        innate=True,
        desc=[
            "Passive, no longer levels with Chronosphere.",
            "Now only applies to projectiles targeting Faceless Void or an allied hero within a 1200 radius of him.",
            "Slows enemy attack projectile speed by a flat 40% within a 500 radius around the targeted hero.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ul_open())
W(li("Enemy attack projectile speed slow rescaled from 35/40/45/50% to 40%", b([35, 40, 45, 50], 40)))
W(li("Max slow distance rescaled from 600 around Faceless Void to 500 around the targeted hero", t("REWORK")))
W(li("Now only applies to projectiles targeting Faceless Void or an allied hero within a 1200 radius of him", t("REWORK")))
W(li("No longer levels with Chronosphere", t("REWORK")))
W(ul_close())
W(ability("Time Walk"))
W(ul_open())
W(li("Aghanim's Scepter now also provides Reverse Time Walk sub-ability", t("NEW")))
W(li("Aghanim's Scepter Time Lock attacks will no longer miss if Reverse Time Walk is used too quickly after Time Walk", t("MISC")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Time Dilation"))
W(ul_open())
W(li("Duration no longer counts down while under effect of Chronosphere", t("BUFF")))
W(li("Aghanim's Shard: Increases Attack/Movement Slow per cooldown by 5/5%. Provides Faceless Void with bonus movement and attack speed by the same values per each enemy cooldown extended. The bonus degrades over the duration of the buff. 9/10/11/12 Attack Speed + the same value per affected cooldown, 9/10/11/12% Movement Speed + the same value per affected cooldown",
     t("NEW"),
     extra=inline_note("This buff also doesn't count down under effect of Chronosphere")))
W(ul_close())
W(ability("Chronosphere"))
W(ul_open())
W(li("Now the default ultimate ability", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +8% Time Dilation Slow per Cooldown replaced with +125 Time Walk Range", t("REWORK")))
W(ul_close())

# Grimstroke
W(hero_header("Grimstroke"))
W(ability("Ink Trail"))
W(ul_open())
W(li("Now also applied when an enemy hero is affected by any of Grimstroke's abilities", t("NEW")))
W(li("Now also applied by attacks from Grimstroke's illusions (including Dark Portrait)", t("NEW")))
_gs_pill, _gs_table = scale_pill(
    "5% + 0.5% per level",
    lambda L: 5.0 + 0.5 * L,
    value_fmt="{:.1f}%",
)
W(li("Grimstroke now takes " + _gs_pill + " less damage from enemies affected by Ink Trail",
     t("NEW"), extra=_gs_table))
W(ul_close())
W(ability("Stroke of Fate", slug="grimstroke_dark_artistry"))
W(ul_open())
W(li("Can now be put on alt-cast to send the stroke straight", t("MISC")))
W(ul_close())

# Gyrocopter
W(hero_header("Gyrocopter"))
W(ul_open())
W(li("Base Movement Speed decreased from 320 to 315", b(320, 315)))
W(ul_close())
_gy_pill, _gy_table = scale_pill(
    "3.9s + 0.1s per level",
    lambda L: 3.9 + 0.1 * L,
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Chop Shop",
        innate=True,
        desc=[
            "Passive.",
            "Gyrocopter can disassemble most items at all times and sells any Recipe he has for a full cost.",
            "Cannot disassemble Divine Rapier or Hand of Midas.",
        ],
    ),
    new=dict(
        name="Afterburner",
        slug="gyrocopter_afterburner",
        innate=True,
        desc=[
            "Passive.",
            "Whenever Gyrocopter damages an enemy with attacks or abilities, he gains +1 movement speed per hero damaged and +0.5 per creep. Effects stack independently.",
            "Buff duration: " + _gy_pill + ".",
        ],
        tables=[_gy_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Flak Cannon"))
W(ul_open())
W(li("Aghanim's Scepter upgrade moved into a separate ability", t("MISC")))
W(ul_close())
W(ability("Side Gunner", slug="gyrocopter_side_gunner_spawn_ability"))
W(ul_open())
W(li("Aghanim's Scepter: Side Gunner is now a separate ability granted by Scepter (effect is unchanged)", t("NEW")))
W(ul_close())

# Hoodwink
W(hero_header("Hoodwink"))
W(ability("Mistwoods Wayfarer"))
W(ul_open())
W(li("No longer levels with Sharpshooter", t("REWORK")))
W(li_formula("Redirect Chance changed",
             "14/21/28/35%", "14% + 1% per level",
             lambda L: 35.0, lambda L: 14.0 + 1.0 * L))
W(ul_close())
W(ability("Acorn Shot"))
W(ul_open())
W(li("Cast Range rescaled from (Hoodwink's attack range + 100) to 675/700/725/750", t("REWORK"),
     extra=inline_note("As a result, Cast Range increased from 675 to 675/700/725/750 — " + b(675, [675, 700, 725, 750]))))
W(ul_close())
W(ability("Bushwhack"))
W(ul_open())
W(li("Cast Range increased from 1000 to 1100", b(1000, 1100)))
W(ul_close())
W(ability("Scurry"))
W(ul_open())
W(li("No longer doubles all sources of evasion for the duration", t("DEL")))
W(li("Now doubles redirect chance of Mistwoods Wayfarer for the duration", t("NEW")))
W(ul_close())
W(ability("Sharpshooter"))
W(ul_open())
W(li("Now treats creep heroes as creeps", t("MISC"),
     extra=inline_note("The projectile flies through creeps, dealing them damage for half value, but still applying Slow and Break at full force and duration."
                       "<br>Since Spirit Bear is considered a true hero, the projectile will stop on impact with it.")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Health increased from +150 to +175", b(150, 175)))
W(li("Level 15 Talent +1 Acorn Shot Bounce replaced with +10 Agility", t("REWORK")))
W(li("Level 20 Talent -3 Armor Corruption replaced with +2 Acorn Shot Bounces", t("REWORK")))
W(ul_close())

# Huskar
W(hero_header("Huskar"))
W(ul_open())
W(li("Intelligence gain decreased from 1.5 to 0", t("MISC"),
     extra=inline_note("Cosmetic for Huskar — his abilities use Health costs, not mana; Intelligence has no functional impact on him.")))
W(li("Base Movement Speed decreased from 295 to 290", b(295, 290)))
W(ul_close())
W(ability("Inner Fire"))
W(ul_open())
W(li("Damage increased from 105/170/235/300 to 110/180/250/320", b([105, 170, 235, 300], [110, 180, 250, 320])))
W(li("Knockback Duration now scales based on Knockback Distance to a minimum of 0.4s", t("REWORK"),
     extra=inline_note("Enemies which are 375 units or farther now receive a flat knockback of 25 units")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Burning Spear"))
W(ul_open())
W(li("Health Cost changed from 4% of current health to 2% of max health", t("REWORK")))
W(li("Now also burns enemies for 0.5% of their max health", t("NEW")))
W(ul_close())
W(subnote("Huskar can use this ability even if he has less health than the health cost requires"))
W(ul_open())
W(li("Now also burns enemies for 0.5% of their max health", t("REWORK")))
W(ul_close())
W(ability("Berserker's Blood"))
W(ul_open())
W(li("Aghanim's Shard: Can be activated for a health cost. Applies basic dispel to Huskar, then after a delay, heals for the amount of health consumed plus an additional bonus per debuff dispelled. Current HP Cost: 30%. Cooldown: 20s. Cauterize Delay: 3s. Max HP Heal per debuff: 3%", t("NEW")))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(ability("Quas"))
W(ul_open())
W(li("Max Level increased from 7 to 8", b(7, 8)))
W(ul_close())
W(ability("Wex"))
W(ul_open())
W(li("Max Level increased from 7 to 8", b(7, 8)))
W(ul_close())
W(ability("Exort"))
W(ul_open())
W(li("Max Level increased from 7 to 8", b(7, 8)))
W(ul_close())
W(ability("Tornado"))
W(ul_open())
W(li_formula("Aghanim's Scepter twister damage decreased",
             "40 + 10 × Wex Level", "30 + 10 × Wex Level",
             lambda W: 40 + 10 * W, lambda W: 30 + 10 * W,
             levels=list(range(2, 12)), level_prefix='W',
             value_fmt="{:g}"))
W(ul_close())
W(ability("Invoke"))
W(ul_open())
W(li("Now whenever Invoker gets Aghanim's Scepter or Aghanim's Shard, these items are inert in the inventory until Invoker activates them manually. Upon activation, he will be presented with three upgrades to choose from. Upgrades themselves for both Aghanim's Scepter and Aghanim's Shard are unchanged", t("REWORK")))
W(li("You can't change selected upgrades. Selling Aghanim's Scepter and buying it again will provide the same upgrade you chose the first time", t("NERF")))
W(li("Aghanim's Scepter no longer provides +1 level to all three orbs. Now it provides +1 level only to a single orb you choose", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +1 Facet Orb Level replaced with +25 Alacrity Speed/Damage", t("REWORK")))
W(li("Level 20 Talent +50 Alacrity Speed/Damage replaced with +1 Orb Levels", t("REWORK")))
W(ul_close())

# Io
W(hero_header("Io"))
_io_pill, _io_table = scale_pill(
    "5% + 0.5% per level",
    lambda L: 5 + 0.5 * L,
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Wellspring",
        innate=True,
        desc=[
            "Passive.",
            "Consumable items and item abilities that restore Health and Mana over time affect Io <b>twice as fast</b>. Total amount of restored Health or Mana remains the same.",
            "Applies to: Healing Salve, Tango, Clarity, Bottle, Urn of Shadows, Spirit Vessel, Pollywog Charm, Mana Draught.",
            "Example: Clarity normally restores 150 mana over 25s; for Io, 150 mana over 12.5s.",
        ],
    ),
    new=dict(
        name="Equilibrium",
        slug="wisp_equilibrium",
        innate=True,
        desc=[
            "Passive.",
            "Io always has bonus Outgoing Damage Amp that linearly scales with its health, reaching maximum " + _io_pill + " at 100% Health.",
            "At the same time, Io has Health Restoration and Healing Amplifications that also linearly scale with its health, reaching the same maximum at 0% Health.",
        ],
        tables=[_io_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Overcharge"))
W(ul_open())
W(li("Now also provides 35/60/85/110 Attack Speed and 8/10/12/14% Spell Amplification to Io and any tethered Allies", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Strength increased from +7 to +8", b(7, 8)))
W(li("Level 25 Talent Relocate Cast Delay Reduction increased from 1.5s to 2s", b(1.5, 2)))
W(ul_close())

# Jakiro
W(hero_header("Jakiro"))
W(ability("Double Trouble"))
W(ul_open())
W(li_formula("Attack Damage Reduction changed",
             "50%", "51% - 1% per level",
             lambda L: 50.0, lambda L: 51.0 - 1.0 * L, l=True))
W(ul_close())
W(ability("Liquid Fire"))
W(ul_open())
W(li("Now has a 20 mana cost", t("NERF")))
W(li("Aghanim's Shard now also reduces mana cost to 0", t("NEW")))
W(ul_close())
W(ability("Liquid Frost", slug="jakiro_liquid_ice"))
W(ul_open())
W(li("Now has a 20 mana cost", t("NERF")))
W(li("Aghanim's Shard now also reduces mana cost to 0", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Ice Path Damage increased +60 to +75", t("BUFF")))
W(li("Level 15 Talent Dual Breath Cooldown Reduction increased from 3s to 3.5s", b(3, 3.5, l=True)))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
_jg_pill, _jg_table = scale_pill(
    "2.5% + 0.05% per level",
    lambda L: 2.5 + 0.05 * L,
    value_fmt="{:.2f}",
)
W(ability_change(
    old=dict(
        name="Duelist",
        innate=True,
        desc=[
            "Passive.",
            "Juggernaut deals <b>10% more damage</b> to targets that are facing him. Damage bonus is always applied during Omnislash.",
        ],
    ),
    new=dict(
        name="Bladeform",        innate=True,
        desc=[
            "Passive.",
            "Juggernaut receives a stack of Bladeform every 2s he does not take damage. Maximum 10 stacks. Stacks fade after 2s upon taking any damage.",
            "Each stack grants " + _jg_pill + " base Agility bonus and 1% movement bonus.",
        ],
        tables=[_jg_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Blade Fury"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Healing Ward"))
W(ul_open())
W(li("Aghanim's Shard: Increases healing by 1.5% and hits to destroy by 1", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +4% Duelist Damage replaced with -1s Bladeform Stack Gain Interval", t("REWORK")))
W(li("Level 15 Talent +1% Healing Ward Heal replaced with -15s Omnislash Cooldown", t("REWORK")))
W(li("Level 15 Talent Movement Speed During Blade Fury increased from +40 to +45", b(40, 45)))
W(li("Level 20 Talent Blade Fury DPS increased from +90 to +100", b(90, 100)))
W(li("Level 20 Talent +1 Healing Ward Hits to Destroy replaced with +15% Blade Dance Crit Damage", t("REWORK")))
W(ul_close())

# Keeper of the Light
W(hero_header("Keeper of the Light"))
W(ul_open())
W(li("Base Movement Speed decreased from 320 to 315", b(320, 315)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Special Reserve",
        innate=True,
        desc=[
            "Passive.",
            "Keeper of the Light's mana <b>cannot go below 75</b>.",
        ],
    ),
    new=dict(
        name="Bright Speed",
        slug="keeper_of_the_light_bright_speed",
        innate=True,
        desc=[
            "Passive.",
            "Keeper of the Light gains +1 movement speed for every 2.5 Intelligence.",
            "Whenever Keeper of the Light moves 300 distance, he leaves behind light that allows him to see in 400 range for 3 seconds.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Chakra Magic"))
W(ul_open())
W(li("Cooldown rescaled from 18/16/14/12s to 19/16/13/10s", b([18, 16, 14, 12], [19, 16, 13, 10], l=True)))
W(li("Mana Restore increased from 90/160/230/300 to 105/170/235/300", b([90, 160, 230, 300], [105, 170, 235, 300])))
W(ul_close())
W(ability("Blinding Light"))
W(ul_open())
W(li("Cast Range increased from 400/500/600/700 to 500/575/650/725", b([400, 500, 600, 700], [500, 575, 650, 725])))
W(li("Knockback distance changed from 400 to knocking back to the edges of the effect radius, but a minimum knockback distance is 175", t("MISC")))
W(ul_close())
W(subnote("Min distance is used for enemies near the edge of AoE"))
W(ability("Spirit Form"))
W(ul_open())
W(li("No longer grants bonus movement speed percentage", t("DEL")))
W(li("Now increases movement speed bonus of Bright Speed by 50% while active", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent -5s Blinding Light Cooldown replaced with +90 Blinding Light Damage", t("REWORK")))
W(li("Level 15 Talent -2s Chakra Magic Cooldown replaced with +30% Spirit Form Bright Speed Bonus", t("REWORK")))
W(li("Level 20 Talent +200 Chakra Magic Mana replaced with +10% Solar Bind Magic Resistance Reduction", t("REWORK")))
W(li("Level 20 Talent +10% Spirit Form Movement Speed Bonus replaced with +15s Spirit Form Duration", t("REWORK")))
W(ul_close())

# Kez
W(hero_header("Kez"))
W(ul_open())
W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
W(li("Base Attack Speed decreased from 110 to 100", b(110, 100)))
W(ul_close())
W(ability("Switch Discipline", slug="kez_switch_weapons"))
W(ul_open())
W(li_formula("Cooldown changed",
             "7.75s - 0.25s per level up", "8s - 0.25s per level",
             lambda L: 8.0 - 0.25 * L, lambda L: 8.0 - 0.25 * L, l=True))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ul_open())
W(li("Now the first katana hit or ability will deal 12% bonus damage after switching to Katana, and after switching to Sai Kez gains +12% movement speed for 2 seconds", t("NEW")))
W(li("Aghanim's Scepter no longer restarts the alternate ability cooldown if it was already on cooldown", t("MISC")))
W(ul_close())
W(ability("Grappling Claw"))
W(ul_open())
W(li("When targeting a tree, now always destroys the targeted tree and ends in the tree's position", t("MISC")))
W(ul_close())
W(ability("Talon Toss"))
W(ul_open())
W(li("Cast Range decreased from 1200 to 650/750/850/950", b(1200, [650, 750, 850, 950])))
W(ul_close())
W(subnote("Now matches Grappling Claw"))
W(ability("Shodo Sai"))
W(ul_open())
W(li("The proc effect now triggers a critical strike only instead of creating a Mark", t("REWORK")))
W(li("18% Chance to Mark replaced with 20% Critical Strike Chance", t("REWORK"),
     extra=inline_note("As a result, marks are applied only by parrying and casting Raven's Veil")))
W(li("No longer restricts Kez from proccing passive Bash spells of Skull Basher and Abyssal Blade", t("BUFF")))
W(li("Mark Stun Duration increased from 0.4s to 0.5/0.6/0.7/0.8s", b(0.4, [0.5, 0.6, 0.7, 0.8])))
W(li("No longer has a parry bonus by default", t("DEL")))
W(li("Aghanim's Shard: Parrying creates a stronger mark that will stun the target for an additional 0.2s and an a crit bonus of 50%", t("NEW")))
W(ul_close())
W(ability("Raptor Dance"))
W(ul_open())
W(li("No longer provides magic damage immunity", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +100% Shodo Sai Mark Critical Strike replaced with +80% Shodo Sai Critical Strike", t("REWORK")))
W(ul_close())

# Kunkka
W(hero_header("Kunkka"))
W(ability("Admiral's Rum"))
W(ul_open())
W(li("Can no longer be applied by multiple sources, and will no longer trigger passively if Ghostship already applied the buff", t("MISC"),
     extra=inline_note("Previously, overlapping Rum buffs from different sources could overwrite one another — the strongest buff sometimes ended early when a weaker source re-applied it.")))
W(li_formula("Cooldown changed",
             "60s", "60.5s - 0.5s per level",
             lambda L: 60.0, lambda L: 60.5 - 0.5 * L, l=True))
W(li_formula("Bonus Movement Speed rescaled",
             "10%", "7.75% + 0.25% per level",
             lambda L: 10.0, lambda L: 7.75 + 0.25 * L))
W(li("Duration decreased from 6s to 5s", b(6, 5)))
W(li("Delayed Damage decreased from 20% to 18%", b(20, 18)))
W(ul_close())
W(ability("Ghostship"))
W(ul_open())
W(li("Now applies Admiral's Rum at a 2x factor", t("NEW"),
     extra=inline_note("Multiplication applies to duration, delayed damage and movement speed bonus")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent -15s Admiral's Rum Cooldown replaced with +1s Admiral's Rum Buff Duration", t("REWORK")))
W(li("Level 15 Talent Tidebringer Damage increased from +70 to +75", b(70, 75)))
W(li("Level 20 Talent +15% Admiral's Rum Damage Delayed replaced with +80% Tidebringer Cleave", t("REWORK")))
W(li("Level 25 Talent +130% Tidebringer Cleave replaced with Tidebringer Ignores 25% Armor", t("REWORK")))
W(ul_close())

# Largo
W(hero_header("Largo"))
W(ability("Encore"))
W(ul_open())
W(li_formula("Bonus Duration changed",
             "10% + 1% per level up", "9% + 1% per level",
             # Both lambdas resolve to the same in-game values — Valve
             # re-parametrized the formula with a 1-level shift so the old
             # "10% + 1%·L" and the new "9% + 1%·L" produce identical
             # numbers at the hero levels the player actually plays at
             # (hence the "Effective values are not changed" subnote).
             lambda L: 9.0 + 1.0 * L, lambda L: 9.0 + 1.0 * L))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Catchy Lick"))
W(ul_open())
W(li("Now can lick runes to pull them. Rune-licking refunds spent mana", t("NEW")))
W(li("Health Regen Duration decreased from 10s to 8s", b(10, 8)))
W(li("Bonus health regen is now also provided if the target is killed by Catchy Lick", t("NEW")))
W(ul_close())
W(ability("Amphibian Rhapsody"))
W(ul_open())
W(li("Aghanim's Scepter no longer adds damage to double-strumming", t("DEL")))
W(ul_close())
W(ability("Bullbelly Blitz", slug="largo_song_fight_song"))
W(ul_open())
W(li("Now also deals 20/30/40 magical damage by default", t("NEW")))
W(li("Aghanim's Scepter: Increases magic damage by 6/12/18 per Groovin' stack when this song is used in double-strumming", t("NEW")))
W(ul_close())
W(ability("Hotfeet Hustle", slug="largo_song_double_time"))
W(ul_open())
W(li("Move Speed decreased from 16/22/28% to 16/20/24%", b([16, 22, 28], [16, 20, 24])))
W(li("Slow Resistance decreased from 70/80/90% to 70/75/80%", b([70, 80, 90], [70, 75, 80])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Croak of Genius Max Health DPS decreased from 1.5% to 1%", b(1.5, 1)))
W(li("Level 25 Talent Amphibian Rhapsody Song Effects decreased from +35% to +30%", b(35, 30)))
W(ul_close())

# Legion Commander
W(hero_header("Legion Commander"))
W(ul_open())
W(li("Base armor decreased by 1", bstat_h("Legion Commander", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Legion Commander", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
_lc_pill, _lc_table = scale_pill(
    "1 + 0.1 per level",
    lambda L: 1.0 + 0.1 * L,
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Outfight Them!",
        slug="legion_commander_outfight_them",
        innate=True,
        desc=[
            "Passive, levels up with Duel.",
            "When attacking an enemy hero of <b>equal or higher level</b> than Legion Commander, she gains <b>+30/40/50/60% Health Restoration</b> for <b>4s</b>. Always applies when attacking a max-level enemy hero.",
        ],
    ),
    new=dict(
        name="Outfight Them!",
        slug="legion_commander_outfight_them",
        innate=True,
        desc=[
            "Passive.",
            "Passively grants Legion Commander " + _lc_pill + " bonus armor at all times.",
            "Whenever Legion Commander <b>casts an ability</b>, she gains the same amount again as a <b>stacking 6s buff</b> (stacks independently per cast).",
            "Whenever <b>allies within 1200 range</b> cast an ability, they also gain a 6s buff for <b>50% of the value</b>. Ally buffs stack independently.",
        ],
        tables=[_lc_table],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Overwhelming Odds"))
W(ul_open())
W(li("Now also applies 100% movement slow upon dealing damage for 0.3s", t("NEW")))
W(li("Aghanim's Shard reworked: Increases radius by 100. Grants an all damage barrier equal to 50% of the damage dealt with Overwhelming Odds for 6s", t("REWORK")))
W(ul_close())
W(ability("Press The Attack"))
W(ul_open())
W(li("Multiple instances can now stack independently", t("NEW")))
W(li("Aghanim's Scepter: Increases bonus movement speed by 12%. Ability becomes cast-point, affecting all allies within the targeted 500 radius area. Legion Commander is always affected, even when outside of the cast area", t("NEW")))
W(ul_close())
W(ability("Moment of Courage"))
W(ul_open())
W(li("No longer has a 25% proc chance", t("DEL")))
W(li("Now automatically triggers after taking 7/6/5/4 attacks", t("REWORK"),
     extra=inline_note("Will not activate unless Legion Commander is both attacking and being attacked. Until this requirement is met, the 'prepared' state is kept indefinitely")))
W(li("Cooldown decreased from 1.7/1.4/1.1/0.8 to 0.3s", b([1.7, 1.4, 1.1, 0.8], 0.3, l=True)))
W(ul_close())
W(ability("Duel"))
W(ul_open())
W(li("Legion Commander can now use any abilities during Duel", t("NEW"),
     extra=inline_note("Legion Commander will stop attacking as normal during cast animations."
                       "<br>Items can't be used.")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(li("Aghanim's Scepter reworked: When Legion Commander wins a duel, Press the Attack is automatically triggered around her", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +12% Press the Attack Movement Speed replaced with +1 Outfight Them! Armor", t("REWORK")))
W(li("Level 20 Talent +8% Moment of Courage Proc Chance replaced with -1 Moment of Courage Attacks To Trigger", t("REWORK")))
W(li("Level 20 Talent 300 AoE Press The Attack replaced with +1s Duel Duration", t("REWORK")))
W(li("Level 25 Talent Press the Attack grants 1.5s Debuff Immunity replaced with Duel Refreshes Cooldown on Victory", t("REWORK")))
W(ul_close())

# Leshrac
W(hero_header("Leshrac"))
W(ability("Diabolic Edict"))
W(ul_open())
W(li("Duration improved from 10s to 8s", b(10, 8)))
W(ul_close())
W(subnote("Number of explosions (hence, total damage) is unchanged, explosion interval decreased from 0.25s to 0.225s"))

# Lich
W(hero_header("Lich"))
W(ul_open())
W(li("Base Mana Regen decreased from 0.75 to -1", b(0.75, -1)))
W(li("Intelligence gain decreased from 3.8 to 3.4", b(3.8, 3.4)))
W(ul_close())
_lich_mana_pill, _lich_mana_table = scale_pill(
    "42% + 3% per level",
    lambda L: 42.0 + 3.0 * L,
    value_fmt="{:.0f}%",
)
_lich_xp_pill, _lich_xp_table = scale_pill(
    "69% + 6% per level",
    lambda L: 69.0 + 6.0 * L,
    value_fmt="{:.0f}%",
)
W(ability_change(
    old=dict(
        name="Death Charge",
        slug="lich_death_charge",
        innate=True,
        desc=[
            "Passive.",
            "Lich's max mana regeneration is <b>0</b>. Whenever any unit dies nearby, Lich restores a portion of his Max Mana. Dying heroes restore a bigger portion.",
            "<b>Radius:</b> 1200. <b>Max Mana Restored:</b> 2.5% (Creep), 15% (Hero).",
            "Lich can regenerate mana only under effect of a Fountain.",
        ],
    ),
    new=dict(
        name="Sacrifice",
        slug="lich_death_charge",
        innate=True,
        desc=[
            "Active, targets an allied creep within 700 range and instantly kills it.",
            "Lich gains mana equal to " + _lich_mana_pill + " of the creep's <b>current</b> health and experience bounty equal to " + _lich_xp_pill + " of the creep's value.",
            "<b>No Mana Cost. Cooldown: 120s.</b> Starts on extended cooldown with no charges — the first cast is only possible at the 2:00 mark.",
            "Sacrificed creeps count as denies, providing experience to enemy heroes (Lich's experience gain is independent from what enemies receive).",
        ],
        tables=[_lich_mana_table, _lich_xp_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +4s Frost Shield Duration replaced with 2 Frost Shield Charges", t("REWORK")))
W(li("Level 25 Talent +100 Chain Frost Incremental Damage replaced with Chain Frost Unlimited Bounces", t("REWORK")))
W(ul_close())

# Lifestealer
W(hero_header("Lifestealer"))
W(ul_open())
W(li("Base Damage increased by 10",
     bstat_h("Lifestealer", "AttackDamageMin", "7.40c", 10),
     extra=note_box(hero="Lifestealer", field="AttackDamageMin", before_patch="7.40c")))
W(li("Base Attack Speed increased from 100 to 120", b(100, 120)))
W(li("Base Movement Speed increased from 315 to 320", b(315, 320)))
W(li("Damage at level 1 increased from 39–45 to 49–55", br(39, 45, 49, 55)))
W(ul_close())
_lsf_pill, _lsf_table = scale_pill(
    "5 per level",
    lambda L: 5.0 * L,
    value_fmt="{:.0f}",
)
W(ability_change(
    old=dict(
        name="Feast",
        slug="life_stealer_feast",
        innate=True,
        desc=[
            "Passive, levels up with Infest.",
            "Lifestealer's attacks deal bonus magic damage equal to <b>1.25/1.75/2.25/2.75%</b> of target's max health and lifesteal back <b>1.25/1.75/2.25/2.75%</b> of target's max health.",
            "Also allows hitting allied creeps below <b>75%</b> health (default deny threshold is 50%).",
        ],
    ),
    new=dict(
        name="Ghoul Frenzy",
        slug="life_stealer_ghoul_frenzy",
        innate=True,
        desc=[
            "Passive, occupies the slot vacated by Feast (Feast moved back to a regular ability).",
            "Provides Lifestealer with " + _lsf_pill + " bonus Attack Speed at all times.",
        ],
        tables=[_lsf_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Rage"))
W(ul_open())
W(li("Now also provides 9/12/15/18% bonus movement speed while active", t("NEW")))
W(ul_close())
W(ability("Open Wounds"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 90", b(100, 90, l=True)))
W(li("Max Slow increased from 35/40/45/50% to 50%", b([35, 40, 45, 50], 50, l=True)))
W(ul_close())
W(ability("Feast"))
W(ul_open())
W(li("Now is a basic ability", t("REWORK")))
W(li("Heal From Target's Max Health rescaled from 2/2.25/2.5/2.75% to 1.45/2.05/2.65/3.25%", b([2, 2.25, 2.5, 2.75], [1.45, 2.05, 2.65, 3.25])))
W(li("Max Health Damage rescaled from 2/2.25/2.5/2.75% to 1.45/2.05/2.65/3.25%", b([2, 2.25, 2.5, 2.75], [1.45, 2.05, 2.65, 3.25])))
W(li("Max Health per Hero Kill increased from 10 to 10/15/20/25", b(10, [10, 15, 20, 25])))
W(ul_close())
W(subnote("Is not retroactive"))
W(ul_open())
W(li("No longer increases deny health threshold to 75%", t("DEL")))
W(ul_close())
W(ability("Infest"))
W(ul_open())
W(li("Now can be used on Ancient creeps by default", t("NEW")))
W(li("Aghanim's Shard reworked: When consuming a creep, enemies also take damage over time equal to 30% of the creep's remaining health. Damage duration: 3s. Has no effect when bursting out of enemy heroes", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +3% Ghoul Frenzy Movement Speed replaced with +20 Movement Speed", t("REWORK")))
W(li("Level 15 Talent +15% Open Wounds Slow replaced with 50 Attack Speed on Open Wounds Target", t("REWORK")))
W(li("Level 15 Talent +50 Ghoul Frenzy Attack Speed replaced with +175 Infest Damage", t("REWORK")))
W(li("Level 20 Talent Infest Target Movespeed/Health decreased from +15% to +12%", b(15, 12)))
W(ul_close())

# Lina
W(hero_header("Lina"))
W(ability_change(
    old=dict(
        name="Combustion",
        slug="lina_combustion",
        innate=True,
        desc=[
            "Passive, levels up with Laguna Blade.",
            "Lina's fire damage stacks <b>Overheat</b> on enemies. When the target reaches the <b>175 damage threshold</b>, they combust and take additional Overheat damage.",
            "<b>Overheat Damage:</b> 15/35/55/75 (post-7.39).",
        ],
    ),
    new=dict(
        name="Slow Burn",
        innate=True,
        desc=[
            "Passive.",
            "Lina's abilities deal an <b>additional 64%</b> damage as <b>undispellable burn damage over 4s</b>.",
            "Applies on top of the spell's base damage and stacks duration on re-application.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Dragon Slave"))
W(ul_open())
W(li("Damage decreased from 85/165/245/325 to 65/125/185/245", b([85, 165, 245, 325], [65, 125, 185, 245])))
W(ul_close())
W(ability("Light Strike Array"))
W(ul_open())
W(li("Damage decreased from 110/160/210/260 to 80/120/160/200", b([110, 160, 210, 260], [80, 120, 160, 200])))
W(ul_close())
W(ability("Laguna Blade"))
W(ul_open())
W(li("Damage decreased from 500/750/1000 to 380/565/750", b([500, 750, 1000], [380, 565, 750])))
W(li("Aghanim's Shard reworked: Casting Laguna Blade temporarily supercharges Lina, granting her 12 stacks of Fiery Soul. Supercharge duration: 5s", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Light Strike Array Damage decreased from +150 to +110", b(150, 110)))
W(li("Level 25 Talent +150% Crit On Targets Affected By Spells replaced with 150% Attack Crit on Targets Affected by Slow Burn", t("REWORK")))
W(li("Level 25 Talent +60% Combustion Overheat Damage replaced with +1s Slow Burn Duration", t("REWORK"),
     extra=inline_note("This increases additional damage from 64% to 80% — " + b(64, 80))))
W(ul_close())

# Lion
W(hero_header("Lion"))
W(ability_change(
    old=dict(
        name="To Hell and Back",
        innate=True,
        desc=[
            "Passive.",
            "Lion gains <b>20% debuff duration</b> and <b>20% spell amplification</b> for <b>90s</b> after respawning.",
            "Refreshes every time he dies and respawns.",
        ],
    ),
    new=dict(
        name="To Hell and Back",
        innate=True,
        desc=[
            "Passive. Reworked into a two-trigger buff:",
            "<b>Kill / assist trigger:</b> killing or assisting in a Hero kill grants Lion <b>20% debuff duration</b> against that hero <b>while it is dead</b>.",
            "<b>Respawn trigger:</b> whenever Lion respawns or resurrects, he gains <b>20% spell amplification</b> for <b>90s</b>, or until he gets a kill or an assist (whichever comes first).",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Finger of Death"))
W(ul_open())
W(li("Cooldown decreased from 120/80/40s to 110/70/30s", b([120, 80, 40], [110, 70, 30], l=True)))
W(li("Damage per kill decreased from 40 to 30", b(40, 30)))
W(li("Now has empowered melee attacks after the cast by default", t("NEW")))
W(li("After using Finger of Death, Lion's hand becomes empowered, turning him into a melee hero with 250 attack range and 30 bonus movement speed. These melee attacks have 25% cleave and deal 20/30/40 bonus damage which increases with each Finger of Death kill. Enemy heroes that die within 3s after getting hit with these melee attacks (or from them) also provide bonus per kill damage. Melee form duration: 20s",
     t("REWORK"),
     extra=inline_note("Ability can be toggled with right-click to disable the melee form."
                       "<br>Cleave area is a cone with 150 width that increases up to 350 at 650 distance.")))
W(li("Aghanim's Scepter now also increases melee cleave from 25% to 50% and duration from 20s to 30s", t("NEW")))
W(li("Aghanim's Scepter no longer decreases cooldown", t("DEL")))
W(ul_close())

# Lone Druid
W(hero_header("Lone Druid"))
W(ul_open())
W(li("Attack projectile speed increased from 900 to 1125", b(900, 1125)))
W(ul_close())

# Luna
W(hero_header("Luna"))
W(ability("Lunar Blessing"))
W(ul_open())
W(li("Damage for Allies/Self changed from 1/2 + 1/2 per level up to 1/2 per level", t("MISC")))
W(li_formula("Bonus Night Vision changed",
             "250 + 25 per level up", "225 + 25 per level",
             lambda L: 250.0 + 25.0 * L, lambda L: 225.0 + 25.0 * L,
             effective_unchanged=True))
W(ul_close())
W(subnote("Effective values are not changed (formulas re-parametrized with a 1-level shift)"))
W(ability("Lunar Orbit"))
W(ul_open())
W(li("Now applies 8/12/16/20% damage reduction while active", t("NEW")))
W(li("Aghanim's Shard reworked: Increases damage reduction by 10% and provides Luna with 20% bonus movement speed for the duration", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent -2s Lucent Beam Cooldown replaced with 1.5x Lunar Orbit Damage / Speed", t("REWORK")))
W(li("Level 25 Talent Lunar Blessing Allied/Self Damage decreased from +30/60 to +25/50", b([30, 60], [25, 50])))
W(ul_close())

# Lycan
W(hero_header("Lycan"))
W(ability("Apex Predator"))
W(ul_open())
W(li_formula("Damage to neutrals changed",
             "2% per level", "18% + 2% per level",
             lambda L: 2.0 * L, lambda L: 18.0 + 2.0 * L))
W(ul_close())
W(ability("Summon Wolves"))
W(ul_open())
W(li("Aghanim's Shard reworked: Increases the number of wolves by 1 and grants them Hightail ability. Activate it to give them 100% evasion, 20 bonus attack speed, and hasted movement for 6s", t("REWORK")))
W(ul_close())
W(ability("Shapeshift"))
W(ul_open())
W(li("Now grants controlled units movement speed and critical strike bonuses", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +2 Wolves Summoned replaced with -25% Summon Wolves BAT", t("REWORK"),
     extra=inline_note("Improves wolves' BAT from 1.2/1.1/1/0.9s to 0.9/0.825/0.75/0.675s — "
                       + b([1.2, 1.1, 1, 0.9], [0.9, 0.825, 0.75, 0.675], l=True))))
W(ul_close())

# Magnus
W(hero_header("Magnus"))
W(ul_open())
W(li("Base Agility increased from 12 to 14", b(12, 14)))
W(li("Damage at level 1 increased from 55–63 to 56–64", br(55, 63, 56, 64)))
W(ul_close())
W(ability("Solid Core"))
W(ul_open())
W(li("No longer levels with Reverse Polarity", t("REWORK")))
W(li_formula("Slow Resistance rescaled",
             "20/30/40/50%", "24% + 1% per level",
             lambda L: 50.0, lambda L: 24.0 + 1.0 * L))
W(ul_close())
W(ability("Empower"))
W(ul_open())
W(li("Now always affects Magnus with 30% increased values and can't be cast on himself", t("NEW")))
W(ul_close())
W(ability("Skewer"))
W(ul_open())
W(li("Aghanim's Shard bonus distance increased from +275 to +300", b(275, 300)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +10% Empower Damage/Cleave replaced with Shockwave Returns to Magnus", t("REWORK")))
W(ul_close())

# Marci
W(hero_header("Marci"))
_marci_cd_pill, _marci_cd_table = scale_pill(
    "245s − 5s per level",
    lambda L: 245.0 - 5.0 * L,
    value_fmt="{:.0f}s",
)
W(ability_change(
    old=dict(
        name="Special Delivery",
        slug="marci_special_delivery",
        innate=True,
        desc=[
            "Passive + Active.",
            "<b>Passive:</b> permanently increases the level of all allied couriers by <b>3</b> and hero attacks to kill the courier by <b>1</b> (so Marci's team starts with flying couriers).",
            "<b>Active:</b> Marci whistles and instantly teleports her courier to her location. <b>Cast Point:</b> 1s. <b>Cooldown:</b> 240s (flat).",
        ],
    ),
    new=dict(
        name="Special Delivery",
        slug="marci_special_delivery",
        innate=True,
        desc=[
            "Passive + Active.",
            "<b>Passive:</b> permanently increases the level of all allied couriers by <b>3</b> and hero attacks to kill the courier by <b>1</b> (so Marci's team starts with flying couriers).",
            "<b>Active:</b> Marci whistles and instantly teleports her courier to her location. Reworked delivery logic:",
            "If the courier is <b>in the fountain</b> when Special Delivery is cast, it <b>takes all items from the stash</b> before teleporting.",
            "The courier then <b>automatically attempts to transfer items</b> upon arrival, then heads back to the fountain.",
            "If the courier still has any extra items after the transfer attempt — or didn't transfer anything — it <b>stays next to Marci</b> instead of returning.",
            "<b>Cast Point:</b> 1s. <b>Cooldown:</b> " + _marci_cd_pill + " (was a flat 240s).",
        ],
        tables=[_marci_cd_table],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability_change(
    old=dict(
        name="Bodyguard",
        slug="marci_bodyguard",
        desc=[
            "Active. Target an allied hero to become their bodyguard for <b>6s</b>.",
            "<b>Passive:</b> Marci gains <b>12/18/24/30% Lifesteal</b> and <b>+12/18/24/30% bonus base attack damage</b>. Health gained from lifesteal also heals the bodyguarded ally.",
            "<b>Active:</b> the bodyguarded ally receives <b>75%</b> of these bonuses. Whenever the ally attacks or is attacked by an enemy within Marci's attack range + <b>125</b>, Marci attacks that enemy.",
        ],
    ),
    new=dict(
        name="Bodyguard",
        slug="marci_bodyguard",
        desc=[
            "Now has both <b>passive</b> and <b>active</b> components.",
            "<b>Passive:</b> grants Marci <b>12/18/24/30%</b> lifesteal and <b>12/18/24/30%</b> bonus base attack damage.",
            "<b>Active:</b> cast on an ally — they receive <b>75%</b> of the passive bonuses and a <b>shared all-damage barrier</b> that blocks 90/160/230/300 damage. Damaging the barrier on either Marci or the target reduces it for both. As Marci attacks heroes, 30% of the damage dealt restores the barrier. <b>Duration: 7s.</b>",
            "<b>Cast Range:</b> 500. <b>Mana Cost:</b> 60/65/70/75. <b>Cooldown:</b> 20s. <b>Cast Point:</b> 0.2s.",
            "The effect is dispellable. Dispelling Marci removes the barrier; dispelling the target removes both the barrier and passive bonuses (lifesteal + base attack damage).",
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ability("Rebound", slug="marci_companion_run"))
W(ul_open())
W(li("Ability can be set to alt-cast to bring the target ally to the destination. Does not work on rooted or leashed allies", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +10% Rebound Movement Speed Bonus replaced with +12% Bodyguard Damage", t("REWORK")))
W(li("Level 20 Talent Unleash Movement Speed increased from +10% to +15%", b(10, 15)))
W(li("Level 25 Talent +20% Bodyguard Damage replaced with Bodyguard Strong Dispels (Dispels both Marci and the target)", t("REWORK")))
W(ul_close())

# Mars
W(hero_header("Mars"))
W(ability("Dauntless"))
W(ul_open())
W(li("No longer considers Mars's allies when determining if Mars is outnumbered", t("DEL")))
W(li("HP Regen per extra enemy decreased from 70% to 40%", b(70, 40)))
W(ul_close())
W(ability("Bulwark"))
W(ul_open())
W(li("Now a point targeted ability. Mars will face towards the targeted direction when toggled on", t("MISC")))
W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
W(ul_close())
W(ability("Arena Of Blood"))
W(ul_open())
W(li("Aghanim's Scepter: Lowers cooldown by 10s and increases duration from 5.5s to 6.5s. If an enemy is killed in the Arena, Mars and all of his allies inside the Arena restore 35% of their max health and mana and get a 35% attack damage buff for 20s. This effect stacks", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +20% Dauntless Regen Per Enemy replaced with +1.5 Mana Regen", t("REWORK")))
W(li("Level 20 Talent -16s Arena Of Blood Cooldown replaced with +70 Arena of Blood Spear Damage", t("REWORK")))
W(ul_close())

# Medusa
W(hero_header("Medusa"))
W(ability("Gorgon's Grasp", slug="medusa_gorgon_grasp"))
W(ul_open())
W(li("Cooldown decreased from 30/27/24/21s to 30/26/22/18s", b([30, 27, 24, 21], [30, 26, 22, 18], l=True)))
W(li("Now always centers the cast cursor around the second grouping, even if the number of volleys is increased", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Stone Gaze Bonus Physical Damage increased from +10% to +12%", b(10, 12)))
W(li("Level 15 Talent Mystic Snake Cooldown Reduction increased from 3s to 4s", b(3, 4, l=True)))
W(li("Level 15 Talent +8% Split Shot Outgoing Damage replaced with +1 Gorgon's Grasp Volley", t("REWORK")))
W(li("Level 20 Talent +1 Gorgon's Grasp Volley replaced with +12% Split Shot Outgoing Damage", t("REWORK")))
W(li("Level 20 Talent +3 Mystic Snake Bounces replaced with +40% Mystic Snake Damage / Mana Gain", t("REWORK")))
W(li("Level 25 Talent Stone Gaze Duration increased from +2s to +2.5s", b(2, 2.5)))
W(ul_close())

# Meepo
W(hero_header("Meepo"))
W(ul_open())
W(li("Base Movement Speed decreased from 320 to 315", b(320, 315)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Sticky Fingers",
        innate=True,
        desc=[
            "Passive.",
            "Meepo receives an additional choice when activating <b>neutral item tokens</b>.",
        ],
    ),
    new=dict(
        name="Geomancy",
        innate=True,
        desc=[
            "Passive.",
            "Each Meepo (main + clones) grants stacking bonuses to <b>all</b> Meepos based on the terrain it stands on:",
            "<b>Tree within 250 range</b> → +1 Health Regen.",
            "<b>On solid ground</b> → +2% bonus movement speed.",
            "<b>In water</b> → attacks slow the target by 2% for 2s.",
            '<div class="inline-note">Each Meepo can provide only one tree bonus regardless of how many trees are in range. '
            "If there's a tree in the water, that Meepo provides both the water and tree bonuses.</div>",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Ransack"))
W(ul_open())
W(li("Now pierces Debuff Immunity", t("NEW")))
W(li("No longer has separate creep values. Follows global lifesteal rules instead", t("NERF"),
     extra=inline_note("Has a 40% penalty against creeps — " + b(100, 60))))
W(ul_close())
W(ability_change(
    old=dict(
        name="Divided We Stand",
        slug="meepo_divided_we_stand",
        desc=[
            "Ultimate. Passive — at the ult's level-up points, Meepo gains an additional clone.",
            "<b>Max Level:</b> 3 (levels at 4 / 11 / 18).",
            "Passively grants Meepo and all clones bonus <b>Magic Resistance</b>.",
            "Each clone is a separate hero unit but does not copy items.",
        ],
    ),
    new=dict(
        name="Divided We Stand",
        slug="meepo_divided_we_stand",
        desc=[
            "Ultimate. Reworked — adds a 4th level and item sharing:",
            "<b>Max Level:</b> 4 (levels at <b>3 / 10 / 17 / 24</b>).",
            "Each duplicate now <b>copies all of Meepo's items</b>, but they <b>share their cooldowns</b>.",
            "Damage, attack speed, health / mana regeneration, mana burn, and proc-chance bonuses from items are <b>distributed equally</b> across all Meepos — a 50% / 66.6% / 75% / 80% penalty per Meepo at each level.",
            "Clones can't use consumable shared items on the main Meepo.",
            "<b>No longer</b> passively grants Magic Resistance.",
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ul_open())
W(li("Max Level increased from 3 to 4", t("REWORK")))
W(li("Level requirement rescaled from 4/11/18 to 3/10/17/24", t("REWORK")))
W(li("Meepo gains 100% of the experience from Hero Kills or Assists as long as at least one Meepo is in range", t("REWORK"),
     extra=inline_note("Multiple Meepos within experience range does not increase the amount gained")))
W(li("All other experience gained by any Meepo is divided by the number of Meepos", t("REWORK"),
     extra=inline_note("Each Meepo gains experience independently")))
W(li("No longer has a penalty for Strength, Agility, or Intelligence gained from items", t("BUFF")))
W(li("Clones can't use consumable shared items on the main Meepo", t("NERF")))
W(li("Clones no longer gain 30% experience independently", t("DEL")))
W(li("No longer passively grants Magic Resistance", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Health increased from +350 to +400", b(350, 400)))
W(ul_close())

# Mirana
W(hero_header("Mirana"))
_mira_pill, _mira_table = scale_pill(
    "3 per level",
    lambda L: 3.0 * L,
    value_fmt="{:.0f}",
)
W(ability_change(
    old=dict(
        name="Selemene's Faithful",
        innate=True,
        desc=[
            "Passive.",
            "Healing Lotuses are <b>20% more effective</b> on Mirana and her allies — both Lotus pickups and the AoE pulse hand out a larger heal when Mirana is involved.",
        ],
    ),
    new=dict(
        name="Celestial Quiver",
        slug="mirana_celestial_quiver",
        innate=True,
        desc=[
            "Auto-cast attack modifier.",
            "Mirana consumes a charge to empower her next attack with bonus magic damage equal to " + _mira_pill + ".",
            "Starts with <b>2 max charges</b> and gains <b>+1 max charge every 7 levels</b>. <b>Base Charge Restore Time:</b> 6s.",
            aghs_shard_line("Casting Leap provides 3 temporary charges for the duration of the buff. These temporary charges ignore the max-charges cap and stack from each Leap cast."),
        ],
        tables=[_mira_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ul_open())
W(li("Upgraded with Aghanim's Shard", t("NEW")))
W(ul_close())
W(ability("Leap"))
W(ul_open())
W(li("Aghanim's Shard no longer provides crits during the buff", t("DEL")))
W(ul_close())
W(subnote("Still increases max charges by 1"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +35 Base Damage replaced with +35 Celestial Quiver Damage", t("REWORK")))
W(ul_close())

# Monkey King
W(hero_header("Monkey King"))
W(ability("Mischief"))
W(ul_open())
W(li("No longer levels with Wukong's Command", t("REWORK")))
W(li_formula("Cooldown changed",
             "24/20/16/12s", "24.5s - 0.5s per level",
             lambda L: 12.0, lambda L: 24.5 - 0.5 * L, l=True))
W(ul_close())
W(ability("Tree Dance"))
W(ul_open())
W(li("Cast point increased from 0.1s to 0.2s", b(0.1, 0.2, l=True)))
W(li("Cast Range / Perched Tree Cast Range increased from 800 to 900", b(800, 900)))
W(li("Cooldown decreased from 1.4/1.2/1.0/0.8s to 0.9/0.6/0.3/0s", b([1.4, 1.2, 1.0, 0.8], [0.9, 0.6, 0.3, 0], l=True)))
W(li("Leap speed decreased from 700 to 600", b(700, 600)))
W(li("Leaping between trees can now be interrupted by Roots and Leashes", t("MISC"),
     extra=inline_note("Previously it was only interrupted by Stunned, Hidden, or Hexed statuses")))
W(ul_close())
W(ability("Wukong's Command"))
W(ul_open())
W(li("Now has Changing of the Guard sub-ability by default", t("NEW"),
     extra=inline_note("While Wukong's Command is active, Monkey King gains a Changing of the Guard ability which allows him to transform into any one of his soldiers. Upon cast, Monkey King takes the place of the soldier closest to the target location for 1.5s, and leaves another one in his stead. While Transfigured, Monkey King is indistinguishable from other soldiers and invulnerable, but can't issue commands. Cast Point: 0.3s. No Mana Cost. Cooldown: 3s")))
W(ul_close())
W(ability("Changing of the Guard", slug="monkey_king_transfiguration"))
W(ul_open())
W(li("Ability appears in place of Wukong's Command and starts on a 1s cooldown after casting Wukong's Command. Can't be cast while rooted and can't target soldiers created by Aghanim's Scepter effect. Monkey King disjoints projectiles upon transformation.", t("MISC"),
     extra=inline_note("The possessed soldier has a small ring around it which is visible only to Monkey King and his allies. When the effect is over, Monkey King becomes his usual self leaving the overtaken soldier's position empty.")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +90 Primal Spring Max Damage replaced with +350 Tree Dance Cast Range", t("REWORK")))
W(li("Level 15 Talent +450 Tree Dance Cast Range replaced with 0 Cooldown Primal Spring", t("REWORK")))
W(li("Level 20 Talent 0 Cooldown Primal Spring replaced with Jingu Mastery Undispellable", t("REWORK")))
W(ul_close())

# Morphling
W(hero_header("Morphling"))
W(ul_open())
W(li("Hero model size now scales on his Agility/Strength ratio", t("MISC")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Accumulation",
        innate=True,
        desc=[
            "Passive.",
            "Morphling receives <b>50% of Attribute gain bonuses every half level</b> instead of full bonuses at level up.",
            "Also increases <b>All Attributes bonus gained for skill points in the Talent Tree from +2 to +4</b>.",
        ],
    ),
    new=dict(
        name="Ebb and Flow",
        slug="morphling_ebb_and_flow",
        innate=True,
        desc=[
            "Passive.",
            "Strength and Agility now provide Morphling with additional bonuses (also active while replicating, except the extra attack range, which only applies when replicating a ranged unit):",
            "<b>Strength to Cast Range:</b> 20%. <b>Strength to Slow Resistance:</b> 20%.",
            "<b>Agility to Movement Speed:</b> 15%. <b>Agility to Ranged Attack Range:</b> 20%.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Waveform"))
W(ul_open())
W(li("Cast Range decreased from 700/800/900/1000 to 700/775/850/925", b([700, 800, 900, 1000], [700, 775, 850, 925])))
W(ul_close())
W(ability("Adaptive Strike", slug="morphling_adaptive_strike_agi"))
W(ul_open())
W(li("Base Damage increased from 25/50/75/100 to 50/70/90/110", b([25, 50, 75, 100], [50, 70, 90, 110])))
W(ul_close())

# Muerta
W(hero_header("Muerta"))
W(ability_change(
    old=dict(
        name="Supernatural",
        slug="muerta_supernatural",
        innate=True,
        desc=[
            "Passive.",
            "Muerta is permanently endowed with <b>passive ethereal bonuses</b>: she can always attack ethereal targets and can be attacked while ethereal herself.",
            "While either she or her target is ethereal, her attack damage converts to magical and her physical lifesteal is treated as spell lifesteal.",
        ],
    ),
    new=dict(
        name="Supernatural",
        slug="muerta_supernatural",
        innate=True,
        desc=[
            "Passive. Reworked into a hero-kill-driven stacking buff:",
            "Whenever an <b>enemy hero dies within 925 units</b> of Muerta, she gains a stack of <b>1% spell amplification</b>. Max stacks equal her current hero level.",
            "When Muerta dies she <b>loses half the stacks</b>, rounded down.",
            "Passive ethereal bonuses moved to <b>Pierce the Veil</b>.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability_change(
    old=dict(
        name="Pierce the Veil",
        slug="muerta_pierce_the_veil",
        desc=[
            "Active ultimate. <b>Duration:</b> 8s.",
            "Muerta's attacks deal <b>magical damage</b> instead of physical and gain <b>+70/100/130 bonus attack damage</b>.",
            "Grants <b>30% Spell Lifesteal</b> for the duration.",
            aghs_shard_line("Muerta permanently gains <b>+2% Spell Amplification</b> whenever she kills an enemy hero during Pierce the Veil, or any enemy hero dies within 925 units of her. Applies retroactively."),
        ],
    ),
    new=dict(
        name="Pierce the Veil",
        slug="muerta_pierce_the_veil",
        desc=[
            "Now has both <b>passive</b> and <b>active</b> components.",
            "<b>Passive:</b> Muerta can always attack ethereal targets and can attack while ethereal herself. When either she or her target is ethereal, her attack damage is dealt as <b>magical</b>, and her physical lifesteal is treated as <b>spell lifesteal</b>. "
            + inline_note("Lifesteal conversion happens only for attacks — it does not affect her spells."),
            "<b>Active:</b> grants <b>+75% base damage</b> and <b>30% Spell Lifesteal</b>. <b>Duration:</b> 8s.",
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Spectral Slug"))
W(ul_open())
W(li("Aghanim's Shard: New ability — Muerta shoots a spectral bullet at an enemy, dealing damage, knocking them back, and turning them ethereal for 3s, rendering them immune to physical damage and unable to attack. The target is slowed and becomes 20% more vulnerable to magic damage",
     t("NEW"),
     extra=inline_note("Range: 500. Mana Cost: 75. Cooldown: 12s. Damage: 225. Slow: 30%. Knockback Distance: 250")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +55 Gunslinger Damage replaced with +15 Intelligence", t("REWORK")))
W(ul_close())

# Naga Siren
W(hero_header("Naga Siren"))
W(ability("Eelskin"))
W(ul_open())
W(li("Now provides evasion for Naga Siren on her own", t("NEW")))
W(li_formula("Evasion per Naga changed",
             "8%", "4.9% + 0.1% per level",
             lambda L: 8.0, lambda L: 4.9 + 0.1 * L))
W(ul_close())
W(ability("Rip Tide"))
W(ul_open())
W(li("Now always a basic ability for Naga Siren", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Reel In Pull Speed increased from +100 to +125", b(100, 125)))
W(li("Level 15 Talent Mirror Image Illusion Damage Taken Reduction increased from 50% to 75%", b(50, 75)))
W(li("Level 20 Talent Song of the Siren Cooldown Reduction increased from 20s to 25s", b(20, 25, l=True)))
W(ul_close())

# Nature's Prophet
W(hero_header("Nature's Prophet"))
W(ul_open())
W(li("Minimum Base damage increased by 4", bstat_h("Nature's Prophet", "AttackDamageMin", "7.40c", 4), extra=note_box(hero="Nature's Prophet", field="AttackDamageMin", before_patch="7.40c")))
W(li("Damage spread decreased from 10 to 6", b(10, 6)))
W(li("Damage at level 1 increased from 40–50 to 44–50", br(40, 50, 44, 50)))
W(ul_close())
W(ability("Spirit of the Forest"))
W(ul_open())
W(li("No longer levels with Wrath of Nature", t("REWORK")))
W(li_formula("Tree Radius rescaled",
             "300/400/500/600", "300 + 10 per level",
             lambda L: 600.0, lambda L: 300.0 + 10.0 * L))
W(li("Multiplier per treant increased from 1x to 2x", b(1, 2)))
W(li("Treants also have Spirit of the Forest and gain bonus damage for each nearby tree and treant", t("NEW")))
W(ul_close())
W(ability("Sprout"))
W(ul_open())
W(li("Vision increased from 250 to 400", b(250, 400)))
W(ul_close())
W(ability("Nature's Call", slug="furion_force_of_nature"))
W(ul_open())
W(li("Treant Movespeed rescaled from 305/310/315/320 to 300/315/330/345", b([305, 310, 315, 320], [300, 315, 330, 345])))
W(li("Treant Health decreased from 550 to 450", b(550, 450)))
W(li("Treants now have 25% Magic Resistance", t("NEW")))
W(li("Treants now deal 4/8/12/16 bonus damage to enemy Heroes", t("NEW"),
     extra=inline_note("This bonus is also affected by the Treant Damage multiplying talent")))
W(li("Treants now have free pathing through trees", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent changed from facet specific to +100 Teleportation Barrier", t("MISC")))
W(li("Level 25 Talent 3x Treant HP/Damage no longer affects Spirit of the Forest Multiplier", t("NERF")))
W(ul_close())

# Necrophos
W(hero_header("Necrophos"))
W(ability("Sadist"))
W(ul_open())
W(li("No longer levels with Reaper's Scythe", t("REWORK")))
W(li_formula("Health and Mana regen rescaled",
             "3.5/5/6.5/8", "3.7 + 0.3 per level",
             lambda L: 8.0, lambda L: 3.7 + 0.3 * L))
W(ul_close())
W(ability("Ghost Shroud"))
W(ul_open())
W(li("Restoration Amplification increased from 55/60/65/70% to 55/65/75/85%", b([55, 60, 65, 70], [55, 65, 75, 85])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +15% Ghost Shroud Self Restoration Amp replaced with +75 Spell AoE", t("REWORK")))
W(li("Level 25 Talent +0.5% Heartstopper Aura Damage replaced with +0.3 Reaper's Scythe Damage Per Missing HP", t("REWORK")))
W(ul_close())

# Night Stalker
W(hero_header("Night Stalker"))
_ns_ms_pill, _ns_ms_table = scale_pill(
    "24% + 2% per 3 levels",
    lambda L: 24.0 + 2.0 * (L // 3),
    levels=[1, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30],
    value_fmt="{:.0f}%",
)
_ns_as_pill, _ns_as_table = scale_pill(
    "38 + 2 per level",
    lambda L: 38.0 + 2.0 * L,
    value_fmt="{:.0f}",
)
W(ability_change(
    old=dict(
        name="Heart of Darkness",
        innate=True,
        desc=[
            "Passive.",
            "At night, Night Stalker's Health Regen is <b>increased by 40%</b>, but during the day it is <b>decreased by 20%</b>.",
        ],
    ),
    new=dict(
        name="Hunter in the Night",
        slug="night_stalker_hunter_in_the_night",
        innate=True,
        desc=[
            "Passive. Activates only at night.",
            "<b>Bonus Move Speed:</b> " + _ns_ms_pill + ".",
            "<b>Bonus Attack Speed:</b> " + _ns_as_pill + ".",
            aghs_line("Increases bonus Movement Speed by 15% and bonus Attack Speed by 50. Killing an enemy hero resets cooldowns of all basic abilities."),
        ],
        tables=[_ns_ms_table, _ns_as_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ul_open())
W(li_formula("Move Speed bonus changed",
             "22/28/34/40%", "24% + 2% per 3 levels",
             lambda L: 40.0, lambda L: 24.0 + 2.0 * (L // 3)))
W(li_formula("Attack Speed bonus changed",
             "20/40/60/80", "38 + 2 per level",
             lambda L: 80.0, lambda L: 38.0 + 2.0 * L))
W(li("Aghanim's Scepter: Increases bonus Movement Speed by 15% and bonus Attack Speed by 50. Killing an enemy hero resets cooldowns of all basic abilities", t("NEW")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Void"))
W(ul_open())
W(li("Aghanim's Shard: Now affects all units within 400 radius around the target", t("NEW")))
W(ul_close())
W(ability("Crippling Fear"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
W(ul_close())
W(ability("Midnight Feast"))
W(ul_open())
W(li("New basic ability with both passive and active components — passively, Night Stalker heals himself <b>6/8/10/12 health</b> when attacking enemy units. Actively at night, eats a non-ancient creep to restore <b>10/15/20/25% max health</b> and <b>10/12/14/16% mana</b>. <b>Cast Range:</b> 125. <b>No Mana Cost.</b> <b>Cooldown:</b> 39/36/33/30s",
     t("NEW"),
     extra=inline_note("Attacks on allied units and buildings will not heal Night Stalker."
                       "<br>Can't be cast on allies.")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +5s Dark Ascension Duration replaced with +10 Crippling Fear DPS", t("REWORK")))
W(li("Level 20 Talent +40 Crippling Fear DPS replaced with +75 Crippling Fear Radius", t("REWORK")))
W(li("Level 25 Talent +100 Hunter in the Night Attack Speed replaced with +100 Midnight Feast Lifesteal", t("REWORK")))
W(ul_close())

# Nyx Assassin
W(hero_header("Nyx Assassin"))
W(ability_change(
    old=dict(
        name="Nyxth Sense",
        innate=True,
        desc=[
            "Passive.",
            "Nyx Assassin can <b>sense invisible heroes</b> in a <b>400 radius</b> around himself.",
        ],
    ),
    new=dict(
        name="Mana Burn",
        slug="nyx_assassin_neuro_sting",
        innate=True,
        desc=[
            "Passive.",
            "When Nyx Assassin deals damage with attacks or his abilities, he burns the affected unit's mana equal to <b>12% of damage dealt</b>.",
            "Damage reflected with Spiked Carapace also counts.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Mind Flare", slug="nyx_assassin_jolt"))
W(ul_open())
W(li("Now burns 9/12/15/18% of the target's Max Mana", t("NEW")))
W(ul_close())
W(ability("Vendetta"))
W(ul_open())
W(li("Now also applies a 4s Break on hit", t("NEW")))
W(li("Aghanim's Shard reworked: Decreases cooldown by 10s. For the first 15s, Nyx Assassin is hasted and has unobstructed pathing", t("REWORK")))
W(ul_close())

# Ogre Magi
W(hero_header("Ogre Magi"))
W(ability("Fireblast"))
W(ul_open())
W(li("Aghanim's Scepter: Now also upgrades Fireblast — becomes Refined Fireblast, reducing its cooldown by 1s and increasing its cast speed by 25%", t("NEW")))
W(ul_close())
W(ability("Multicast"))
W(ul_open())
W(li("Each point of Strength increases chances of Multicast by 0.0625%, so every 16 Strength points add 1%", t("NEW")))
W(ul_close())
W(ability("Unrefined Fireblast"))
W(ul_open())
W(li("Cooldown increased from 6s to 7s", b(6, 7, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent -1s Fireblast Cooldown replaced with +2/0.01 Dumb Luck Mana / Mana Regen Per Strength", t("REWORK")))
W(li("Level 10 Talent Ignite Burn Damage decreased from +12 to +10", b(12, 10)))
W(li("Level 15 Talent +2/0.01 Dumb Luck Mana / Mana Regen Per Strength replaced with +20/35 Bloodlust / Self Attack Speed", t("REWORK")))
W(li("Level 20 Talent +35 Bloodlust Attack Speed replaced with +175 Fireblast Damage", t("REWORK")))
W(li("Level 25 Talent +220 Fireblast Damage replaced with +10% Multicast Chances (affects all types of multicast)", t("REWORK")))
W(ul_close())

# Omniknight
W(hero_header("Omniknight"))
W(ul_open())
W(li("Base Armor decreased by 1", bstat_h("Omniknight", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Omniknight", field="ArmorPhysical", before_patch="7.40c")))
W(li("Agility gain decreased from 2.0 to 1.7", b(2.0, 1.7)))
W(ul_close())
W(ability("Degen Aura"))
W(ul_open())
W(li("No longer levels with Guardian Angel", t("REWORK")))
W(li_formula("Movement Slow changed",
             "10/20/30/40%", "11% + 1% per level",
             lambda L: 40.0, lambda L: 11.0 + 1.0 * L))
W(ul_close())
W(ability("Purification"))
W(ul_open())
W(li("Now pierces Debuff Immunity on enemies (previously only pierced Debuff Immunity on allies)", t("NEW")))
W(ul_close())
W(ability("Repel", slug="omniknight_martyr"))
W(ul_open())
W(li("Cooldown decreased from 50/45/40/35s to 40/36/32/28s", b([50, 45, 40, 35], [40, 36, 32, 28], l=True)))
W(li("No longer provides bonus Strength", t("DEL")))
W(li("No longer provides bonus Strength / HP Regen per Debuff", t("DEL"),
     extra=inline_note("As a result, provides only Debuff Immunity with 60% magic resistance, and 8/12/16/20 bonus health regen. Has no effects per dispelled debuffs")))
W(ul_close())
W(ability("Hammer of Purity"))
W(ul_open())
W(li("Now pierces Debuff Immunity", t("NEW")))
W(li("Cooldown decreased from 20/15/10/5s to 13/10/7/4s", b([20, 15, 10, 5], [13, 10, 7, 4], l=True)))
W(li("Bonus Base Damage decreased from 55/70/85/100% to 30/50/70/90%", b([55, 70, 85, 100], [30, 50, 70, 90])))
W(li("Damage decreased from 25/50/75/100 to 20/40/60/80", b([25, 50, 75, 100], [20, 40, 60, 80])))
W(li("Now heals Omniknight for 30% of the damage dealt over the next 5s", t("NEW")))
W(ul_close())
W(ability("Guardian Angel"))
W(ul_open())
W(li("Now is a no-target ability. The effect is applied in an aura centered around Omniknight that follows him", t("REWORK"),
     extra=inline_note("Has no linger duration")))
W(li("Duration decreased from 5/6/7s to 4/4.5/5s", b([5, 6, 7], [4, 4.5, 5])))
W(li("Radius increased from 400 to 700", b(400, 700)))
W(li("Aghanim's Scepter reworked: Becomes global, affects buildings, and amplifies health restoration by 100%", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Base Damage decreased from +35 to +30", b(35, 30)))
W(li("Level 10 Talent +1s Repel Duration replaced with +200 Repel Cast Range", t("REWORK")))
W(li("Level 15 Talent +5 Repel Strength/HP Regen Per Debuff replaced with -0.5s Hammer of Purity Cooldown", t("REWORK")))
W(li("Level 20 Talent +2s Guardian Angel Duration replaced with +125 Degen Aura radius", t("REWORK")))
W(ul_close())

# Oracle
W(hero_header("Oracle"))
W(ability("Prognosticate"))
W(ul_open())
W(li("Oracle now also predicts Roshan's exact respawn timer", t("NEW")))
W(ul_close())
W(ability("False Promise"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
W(ul_close())
def _tarot(slug, name, effect):
    return (f'<span class="tarot-card"><img src="../icons/abilities/oracle_diviners_deck_{slug}.png" '
            f'alt="" class="tarot-card-icon"><b>{name}:</b> {effect}</span>')

W(ability("Diviner's Deck"))
W(ul_open())
W(li("Aghanim's Scepter: New passive ability — Oracle receives a Tarot Card Buff now and every 90 seconds. The buff is undispellable and lasts until the next one replaces it. Oracle always knows which buff will be next.",
     t("NEW"),
     extra=inline_note(
         _tarot("death",     "Death",      "+40% Spell Amplification") + "<br>"
         + _tarot("the_fool",   "The Fool",   "+100% Gold Gain") + "<br>"
         + _tarot("the_world",  "The World",  "+150% Intelligence") + "<br>"
         + _tarot("the_lovers", "The Lovers", "+40% Heal Amplification") + "<br>"
         + _tarot("the_tower",  "The Tower",  "Gain a 400 all-damage barrier which regenerates after not taking damage for 7s"))))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Fortune's End Heals/Damages for 80 Per Effect Dispelled replaced with +100 Fortune's End Radius", t("REWORK")))
W(ul_close())

# Outworld Destroyer
W(hero_header("Outworld Destroyer"))
W(ul_open())
W(li("Base Agility decreased from 22 to 17", b(22, 17)))
W(li("Base Armor decreased by 1", bstat_h("Outworld Destroyer", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Outworld Destroyer", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Ominous Discernment",
        innate=True,
        desc=[
            "Passive.",
            "Outworld Destroyer gains <b>2 extra mana per point of Intelligence</b>.",
        ],
    ),
    new=dict(
        name="Essence Flux",
        slug="obsidian_destroyer_equilibrium",
        innate=True,
        desc=[
            "Passive. Max Mana Restore now depends on the ability it procced on:",
            "<b>Regular abilities:</b> Max Mana Restoration is <b>40% + 5% per 5 levels</b>.",
            "<b>Attack modifiers that spend mana:</b> Max Mana Restoration is <b>25% + 5% per 5 levels</b>.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ul_open())
W(li_formula("For regular abilities Max Mana Restoration changed",
             "25/35/45/55%", "40% + 5% per 5 levels",
             lambda L: 55.0, lambda L: 40.0 + 5.0 * (L // 5),
             levels=[1, 5, 10, 15, 20, 25, 30]))
W(li_formula("For attack modifiers that spend mana Max Mana Restoration changed",
             "25/35/45/55%", "25% + 5% per 5 levels",
             lambda L: 55.0, lambda L: 25.0 + 5.0 * (L // 5),
             levels=[1, 5, 10, 15, 20, 25, 30]))
W(ul_close())
W(ability("Objurgation"))
W(ul_open())
W(li("New basic ability with both passive and active components — passively, increases max mana by <b>80/160/240/320</b>. Active: creates an all-damage barrier equal to <b>120/180/240/300 + 12% of Outworld Destroyer's max mana</b>. <b>Duration:</b> 10s. <b>Mana Cost:</b> 250. <b>Cooldown:</b> 36/34/32/30s.",
     t("NEW"),
     extra=inline_note("Barrier can be dispelled. Multiple instances of Objurgation barrier stack.")))
W(li("Aghanim's Scepter: Increases Max Mana to Barrier by 4%. Damage that would bring Outworld Destroyer below 20% is prevented, triggering a strong dispel and an automatic instance of undispellable Objurgation. This effect cannot trigger more than once every 80s, but refreshes on death", t("NEW")))
W(ul_close())
W(ability("Sanity's Eclipse", slug="obsidian_destroyer_sanity_eclipse"))
W(ul_open())
W(li("Cooldown decreased from 150/135/120s to 140/130/120s", b([150, 135, 120], [140, 130, 120], l=True)))
W(li("Radius decreased from 450/525/600 to 450/500/550", b([450, 525, 600], [450, 500, 550])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +8% Astral Imprisonment Mana Capacity Steal replaced with +5% Essence Flux Mana Restored", t("REWORK")))
W(li("Level 20 Talent +0.15 Sanity's Eclipse Mana Difference Multiplier replaced with +10% Astral Imprisonment Mana Capacity Steal", t("REWORK")))
W(li("Level 20 Talent +450 Health replaced with -10s Objurgation Cooldown", t("REWORK")))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ability("Swashbuckle"))
W(ul_open())
W(li("Slow Duration increased from 0.4s to 0.6s", b(0.4, 0.6)))
W(ul_close())
W(ability("Shield Crash"))
W(ul_open())
W(li("Damage increased from 50/100/150/200 to 60/120/180/240", b([50, 100, 150, 200], [60, 120, 180, 240])))
W(ul_close())
W(ability("Lucky Shot"))
W(ul_open())
W(li("Armor Reduction decreased from 3/5/7/9 to 2/4/6/8", b([3, 5, 7, 9], [2, 4, 6, 8])))
W(ul_close())
W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
W(ul_open())
W(li("Stun Duration increased from 0.8/1/1.2s to 1.2s", b([0.8, 1, 1.2], 1.2),
     extra=note_box("Doubles as a soft nerf at lower ranks: a target can't be hit by another Rolling Thunder stun until the previous one expires, so a longer stun also means a longer immune window between procs.")))
W(ul_close())

# Phantom Assassin
W(hero_header("Phantom Assassin"))
W(ability("Blur"))
W(ul_open())
W(li("No longer levels with Coup de Grace", t("REWORK")))
W(li("Vanish Radius rescaled from 625/550/475/400 to 500", b([625, 550, 475, 400], 500)))
W(li("Vanish Buffer rescaled from 0.4/0.6/0.8/1s to 0.8s", b([0.4, 0.6, 0.8, 1], 0.8)))
W(li_formula("Active Movement Speed changed",
             "6/9/12/15%", "9.5% + 0.5% per level",
             lambda L: 15.0, lambda L: 9.5 + 0.5 * L))
W(ul_close())

# Phantom Lancer
W(hero_header("Phantom Lancer"))
W(ability("Illusory Armaments"))
W(ul_open())
W(li_formula("Min Damage increase changed",
             "2% per 3 level ups", "2% per 3 levels",
             lambda L: 2.0 * ((L - 1) // 3), lambda L: 2.0 * (L // 3),
             levels=[1, 3, 4, 6, 7, 9, 12, 15, 18, 21, 24, 27, 30],
             value_fmt="{:.0f}%"))
W(ul_close())
W(subnote("Bonus damage increases 1 level earlier (on levels 3/6/9... instead of 4/7/10...) and Phantom Lancer gains one more damage increase at level 30"))

# Phoenix
W(hero_header("Phoenix"))
W(ability_change(
    old=dict(
        name="Blinding Sun",
        innate=True,
        desc=[
            "Passive.",
            "Debuffs from Icarus Dive, Fire Spirits, Sun Ray, and Supernova apply a stackable <b>2% miss chance per second</b>. Lasts <b>5 seconds</b>. Applying a new stack refreshes the duration.",
        ],
    ),
    new=dict(
        name="Dying Light",
        slug="phoenix_dying_light",
        innate=True,
        desc=[
            "Passive.",
            "Phoenix deals <b>4% of its missing health</b> as magic damage to all enemies in a <b>400 radius</b> every second. Damage tick rate: 0.2s.",
            "The effect is also present <b>during Supernova</b> — damage is calculated as if Phoenix was still present with the same health and health regen it had at the moment of the cast.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.5% Blinding Sun Miss Chance replaced with +1% Dying Light Missing Health as Damage", t("REWORK")))
W(ul_close())

# Primal Beast
W(hero_header("Primal Beast"))
W(ability_change(
    old=dict(
        name="Colossal",
        slug="primal_beast_colossal",
        innate=True,
        desc=[
            "Passive.",
            "Due to his size, Primal Beast does 40% bonus damage to buildings.",
        ],
    ),
    new=dict(
        name="Colossal",
        slug="primal_beast_colossal",
        innate=True,
        desc=[
            "Passive, scales with Max Health.",
            "Has 10% base Slow Resistance.",
            "Gains +0.5% Area of Effect and +1% Slow Resistance per 100 Max Health.",
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Pulverize"))
W(ul_open())
W(li("AoE Radius decreased from 600 to 575", b(600, 575)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Cannot Be Slowed Or Rooted During Trample replaced with Colossal 2x Bonuses During Trample", t("REWORK")))
W(ul_close())

# Puck
W(hero_header("Puck"))
W(ability("Puckish"))
W(ul_open())
W(li("Health/Mana Restore rescaled from 10 + 2% to 3%", t("REWORK")))
W(ul_close())
W(subnote("Also unified into a single value"))
W(ul_open())
W(li("Spell Dodge Multiplier decreased from 3.5x to 3x", b(3.5, 3)))
W(ul_close())
W(ability("Illusory Orb"))
W(ul_open())
W(li("Speed increased from 550 to 750", b(550, 750)))
W(li("Now additionally deals 3% of orb's Impact Damage every 0.5s in its AoE", t("NEW")))
W(li("Now has curved vector targeting by default", t("MISC"),
     extra=inline_note("Can be put on alt-cast to launch the orb straight.")))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(ability("Meat Shield", slug="pudge_flesh_heap"))
W(ul_open())
W(li("Permanent Bonus Strength rescaled from 1.1/1.4/1.7/2.0 to 1.6", b([1.1, 1.4, 1.7, 2.0], 1.6)))
W(li("No longer levels with Dismember", t("REWORK")))
W(ul_close())
W(ability("Rot"))
W(ul_open())
W(li("No longer has a separate value for incoming heal reduction", t("MISC"),
     extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
W(ul_close())

# Pugna
W(hero_header("Pugna"))
W(ul_open())
W(li("Base Movement Speed decreased from 330 to 325", b(330, 325)))
W(ul_close())
W(ability("Oblivion Savant"))
W(ul_open())
W(li("Now also increases Pugna's Spell Amplification by 1.5% per destroyed tower", t("NEW")))
W(ul_close())
W(ability("Nether Ward"))
W(ul_open())
W(li("Damage source changed from Nether Ward to the caster", t("REWORK")))
W(ul_close())

# Queen of Pain
W(hero_header("Queen of Pain"))
W(ability("Scream Of Pain"))
W(ul_open())
W(li("Damage increased from 75/150/225/300 to 90/175/260/345", b([75, 150, 225, 300], [90, 175, 260, 345])))
W(li("25% of the damage dealt to heroes with this ability is reflected back to her", t("NEW")))
W(ul_close())
W(subnote("Does not trigger on damage to illusions. Damage done is nonlethal reflection damage"))
W(ul_open())
W(li("Also applies to Scream of Pain instances cast by Shadow Strike upgraded with Aghanim's Scepter", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Scream of Pain Damage increased from +100 to +115", b(100, 115)))
W(ul_close())

# Razor
W(hero_header("Razor"))
W(ability("Static Link"))
W(ul_open())
W(li("Damage Drain Rate increased from 5/10/15/20 to 6/12/18/24", b([5, 10, 15, 20], [6, 12, 18, 24])))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Storm Surge"))
W(ul_open())
W(li("Aghanim's Shard: While Eye of the Storm is active, Storm Surge's strike chance is 2x as high, strike cooldown is decreased by 2s, and lightning strikes all enemies within Eye of the Storm's radius", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Storm Surge Slow and Damage increased from +25% to +30%", b(25, 30)))
W(li("Level 10 Talent +10% Spell Lifesteal replaced with +4 Armor", t("REWORK")))
W(ul_close())

# Riki
W(hero_header("Riki"))
W(ability("Cloak and Dagger", slug="riki_backstab"))
W(ul_open())
W(li_formula("Agility Multiplier changed",
             "0.6 + 0.05 per level up", "0.55 + 0.05 per level",
             lambda L: 0.6 + (0.05) * L, lambda L: 0.55 + (0.05) * L,
             effective_unchanged=True))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Smoke Screen"))
W(ul_open())
W(li("Mana Cost rescaled from 65/70/75/80 to 75", b([65, 70, 75, 80], 75, l=True)))
W(li("Miss Rate rescaled from 30/45/60/75% to 40/50/60/70%", b([30, 45, 60, 75], [40, 50, 60, 70])))
W(ul_close())
W(ability("Blink Strike"))
W(ul_open())
W(li("Slow Duration increased from 0.5s to 0.75s", b(0.5, 0.75)))
W(ul_close())
W(ability("Tricks of the Trade"))
W(ul_open())
W(li("Aghanim's Scepter bonus Cast Range increased from +300 to +500", b(300, 500)))
W(ul_close())

# Ringmaster
W(hero_header("Ringmaster"))
W(ability("Dark Carnival Barker", slug="ringmaster_dark_carnival_souvenirs"))
W(ul_open())
# 7.41: souvenir pool unified — previously each Dark Carnival facet drew
# from its own 3-souvenir subset (Facet 2: Funhouse Mirror / Strongman Tonic
# / Whoopee Cushion; Facet 3: Crystal Ball / Unicycle / Weighted Pie).
# Now both facets share the same 4-souvenir pool. Crystal Ball and Weighted
# Pie are dropped from the rotation entirely.
_souvenir_tips = {
    "Funhouse Mirror": "Throws a mirror that on impact creates a hostile illusion of the target enemy hero, mimicking its abilities for a few seconds.",
    "Strongman Tonic": "Drinks a tonic granting Ringmaster bonus attack damage and movement speed for the duration.",
    "Unicycle":        "Mounts a unicycle for 10s. Reaches up to 750 speed (turn rate degrades 130→90). Attacking, casting, picking up runes, taking damage, or crashing dismounts.",
    "Whoopee Cushion": "Places a delayed-trigger cushion at target point that deals damage and slows enemies in its AoE on activation.",
    "Crystal Ball":    "Reveals target area, providing vision and True Sight for a duration.",
    "Weighted Pie":    "Throws a heavy pie at target, dealing damage and applying a heavy movement slow.",
}
_souvenirs_kept = ''.join(souvenir_chip(n, s, tooltip=_souvenir_tips[n]) for n, s in [
    ("Funhouse Mirror", "ringmaster_funhouse_mirror"),
    ("Strongman Tonic", "ringmaster_strongman_tonic"),
    ("Unicycle",        "ringmaster_summon_unicycle"),
    ("Whoopee Cushion", "ringmaster_whoopee_cushion"),
])
_souvenirs_removed = ''.join(souvenir_chip(n, s, removed=True, tooltip=_souvenir_tips[n]) for n, s in [
    ("Crystal Ball",  "ringmaster_crystal_ball"),
    ("Weighted Pie",  "ringmaster_weighted_pie"),
])
W(li("Souvenir pool unified across both Dark Carnival facets", t("REWORK"),
     # Visible tag is REWORK, but Crystal Ball + Weighted Pie were dropped
     # from the rotation — surface this row under the DEL filter too so
     # readers tracking removals don't miss it.
     force_tag="rework del",
     extra=inline_note(
         f'<span class="souvenir-group">'
         f'<span class="souvenir-group-label">In pool:</span>{_souvenirs_kept}'
         f'</span>'
         f'<span class="souvenir-group">'
         f'<span class="souvenir-group-label">Removed:</span>{_souvenirs_removed}'
         f'</span>'
     )))
W(ul_close())
W(ability("Escape Act", slug="ringmaster_the_box"))
W(ul_open())
W(li("Radius and Aghanim's Scepter's Explosion Radius now affected by AoE bonuses", t("NEW")))
W(li("Targeted unit is no longer stunned for 0.5 seconds when placed in a box", t("DEL")))
W(ul_close())
W(ability("Impalement Arts", slug="ringmaster_impalement"))
W(ul_open())
W(li("Charges rescaled from 1/2/3/4 to 3", b([1, 2, 3, 4], 3)))
W(li("Mana Cost decreased from 80 to 50", b(80, 50, l=True)))
W(li("Impact damage rescaled from 50 to 20/35/50/65", b(50, [20, 35, 50, 65])))
W(li("Max Health Damage per second (heroes) rescaled from 3.5/4/4.5/5% to 3/4/5/6%", b([3.5, 4, 4.5, 5], [3, 4, 5, 6])))
W(li("Damage per second (creeps) decreased from 100 to 85/90/95/100", b(100, [85, 90, 95, 100])))
W(li("Slow Duration decreased from 0.8s to 0.5/0.6/0.7/0.8s", b(0.8, [0.5, 0.6, 0.7, 0.8])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +85 Impalement Arts Impact Damage replaced with +1 Impalement Arts Charge", t("REWORK")))
W(ul_close())

# Rubick
W(hero_header("Rubick"))
W(ul_open())
W(li("Base Damage increased by 1", bstat_h("Rubick", "AttackDamageMin", "7.40c", 1), extra=note_box(hero="Rubick", field="AttackDamageMin", before_patch="7.40c")))
W(li("Damage at level 1 increased from 49–55 to 50–56", br(49, 55, 50, 56)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Might and Magus",
        innate=True,
        desc=[
            "Passive.",
            "Grants self <b>1% base attack damage</b> bonus per Spell Amplification bonus.",
            "Grants self <b>0.5% Magic Resistance</b> bonus per Spell Amplification bonus.",
        ],
    ),
    new=dict(
        name="Curiosity",
        slug="rubick_curiosity",
        innate=True,
        desc=[
            "Passive.",
            "Rubick gains <b>1 stack of Curiosity per level</b>. Each stack grants <b>+1 base damage</b>, <b>+0.3% Buff/Debuff Duration</b>, and <b>+2 Area of Effect</b> bonus.",
            "If Rubick <b>sees an enemy Hero cast an ability</b> within 1200 distance of him, he gains <b>2 Curiosity for 20s</b>.",
            "If an enemy that currently provides temporary Curiosity dies within 3s after taking damage from Rubick, he gains <b>1 Curiosity permanently</b>.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Telekinesis"))
W(ul_open())
W(li("Aghanim's Shard Land Distance bonus changed from +35% to +225 (flat)",
     b(506, 600),
     extra=inline_note("Computed off base Telekinesis Land Distance of 375. "
                       "Old: 375 × 1.35 = 506. New: 375 + 225 = 600.")))
W(ul_close())
W(ability("Fade Bolt"))
W(ul_open())
W(li("Now reduces both spell and attack damage by default", t("NEW")))
W(li("Damage Reduction rescaled from 5/15/25/35% to 6/12/18/24%", b([5, 15, 25, 35], [6, 12, 18, 24])))
W(ul_close())
W(ability("Spell Steal"))
W(ul_open())
W(li("No longer grants 10/20/30% Debuff Amplification", t("DEL")))
W(li("Stolen spells now have their cooldown decreased by 10/20/30%", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.25% Might and Magus Damage/Resistance replaced with +200 Health", t("REWORK")))
W(li("Level 10 Talent +165 Telekinesis Landing Damage replaced with -2s Telekinesis Cooldown", t("REWORK")))
W(li("Level 15 Talent +20% Fade Bolt Damage Reduction replaced with -3s Fade Bolt Cooldown", t("REWORK")))
W(li("Level 15 Talent -25% Stolen Spells Cooldown replaced with -50% Stolen Spells Mana Cost", t("REWORK")))
W(li("Level 20 Talent -5s Telekinesis Cooldown replaced with Telekinesis Landing Deals 325 Damage (now this talent applies damage to the thrown enemy as well)", t("REWORK"),
     extra=inline_note("It used to deal damage only in AoE, leaving the thrown enemy unharmed. Doesn't deal damage to thrown allies or self.")))
W(li("Level 20 Talent -5s Fade Bolt Cooldown replaced with +12% Fade Bolt Damage Reduction", t("REWORK")))
W(li("Level 25 Talent +400 Telekinesis Land Distance replaced with 2x Curiosity Bonuses", t("REWORK")))
W(ul_close())

# Sand King
W(hero_header("Sand King"))
W(ability("Caustic Finale", slug="sandking_caustic_finale"))
W(ul_open())
W(li("No longer levels with Epicenter", t("REWORK")))
W(li_formula("Base Damage rescaled",
             "20/40/60/80", "17 + 3 per level",
             lambda L: 80.0, lambda L: 17.0 + 3.0 * L))
W(li_formula("Max Health Damage rescaled",
             "3/7/11/15%", "2.5% + 0.5% per level",
             lambda L: 15.0, lambda L: 2.5 + 0.5 * L))
W(li("Duration decreased from 4.5/5/5.5/6s to 4.5s", b([4.5, 5, 5.5, 6], 4.5)))
W(ul_close())
W(ability("Burrowstrike", slug="sandking_burrowstrike"))
W(ul_open())
W(li("Cast Range increased from 525/600/675/750 to 550/625/700/775", b([525, 600, 675, 750], [550, 625, 700, 775])))
W(li("Sand King now immediately re-gains invisibility if the Burrowstrike ends within Sand Storm's AoE", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +75/7 Base/Incremental Radius of Epicenter replaced with +6 Epicenter Pulses", t("REWORK")))
W(li("Level 25 Talent 50% Sand Storm Slow replaced with 35% Sand Storm Slow and Blind", t("REWORK")))
W(li("Level 25 Talent +8 Epicenter Pulses replaced with +125 Stinger Damage", t("REWORK")))
W(ul_close())

# Shadow Demon
W(hero_header("Shadow Demon"))
W(ability("Menace"))
W(ul_open())
W(li_formula("Damage amplification changed",
             "2.5%", "1.9% + 0.1% per level",
             lambda L: 2.5, lambda L: 1.9 + 0.1 * L))
W(ul_close())
W(ability("Disruption"))
W(ul_open())
W(li("Can now target Spirit Bear", t("MISC")))
W(ul_close())
W(ability("Disseminate"))
W(ul_open())
W(li("Shared Damage rescaled from 20/25/30/35% to 16/24/32/40%", b([20, 25, 30, 35], [16, 24, 32, 40])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +150 Demonic Purge Damage replaced with -20s Demonic Purge Cooldown", t("REWORK")))
W(li("Level 25 Talent -30s Demonic Purge Cooldown replaced with Demonic Purge Applies Shadow Poison", t("REWORK"),
     extra=inline_note("1 stack per second over the debuff duration.")))
W(ul_close())

# Shadow Fiend
W(hero_header("Shadow Fiend"))
W(ability("Necromastery"))
W(ul_open())
W(li("No longer levels with Requiem of Souls", t("REWORK")))
W(li_formula("Damage per soul rescaled",
             "1/2/3/4", "1.35 + 0.15 per level",
             lambda L: 4.0, lambda L: 1.35 + 0.15 * L))
W(li("Base Max Souls decreased from 20/22/24/26 to 20", b([20, 22, 24, 26], 20)))
W(ul_close())
W(ability("Shadowraze", slug="nevermore_shadowraze1"))
W(ul_open())
W(li("Damage decreased from 90/160/230/300 to 85/150/215/280", b([90, 160, 230, 300], [85, 150, 215, 280])))
W(li("Now damage is increased by 3 per Necromastery soul", t("NEW")))
W(li("Aghanim's Shard now also applies a stacking 12% slow debuff to enemies hit", t("NEW")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Feast of Souls",
        slug="nevermore_frenzy",
        desc=[
            "Active. Costs <b>5 souls</b> to cast.",
            "Shadow Fiend gains <b>40/55/70/85 Attack Speed</b> and <b>5/7/9/11% Movement Speed</b> for the duration.",
        ],
    ),
    new=dict(
        name="Feast of Souls",
        slug="nevermore_frenzy",
        desc=[
            "Active. No longer requires souls to cast.",
            "Instead, while active, Shadow Fiend gains souls from <b>2 enemies in a 600 radius every 0.5s</b>, prioritizing heroes. Each enemy can provide souls once — creeps give <b>1 soul</b>, heroes give <b>3</b>. Can collect souls from up to <b>4/6/8/10 enemies</b>.",
            "After the effect ends, Shadow Fiend loses souls whose owners are still alive, retaining the rest for <b>8s</b>."
            + inline_note("The enemy threshold limits only the amount of enemies affected, not the total souls collected. At the cap of 10, you can collect souls from 5 heroes and 5 creeps for 20 souls. 10 Dummy Targets in Hero Demo mode yield 30 souls."),
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ul_open())
W(li("Bonus Attack Speed decreased from 40/55/70/85 to 35/50/65/80", b([40, 55, 70, 85], [35, 50, 65, 80])))
W(li("Bonus Move Speed decreased from 5/7/9/11% to 4/6/8/10%", b([5, 7, 9, 11], [4, 6, 8, 10])))
W(ul_close())
W(ability("Requiem of Souls", slug="nevermore_requiem"))
W(ul_open())
W(li("Now can't use more than 20 souls per cast", t("NERF")))
W(li("Aghanim's Scepter no longer has a damage penalty on the returning Requiem of Souls", t("BUFF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +120 Shadowraze Damage replaced with +2 Feast of Souls Souls Collected Per Hero", t("REWORK")))
W(li("Level 20 Talent +2 Damage Per Soul replaced with +5 Necromastery Max Souls", t("REWORK")))
W(ul_close())

# Shadow Shaman
W(hero_header("Shadow Shaman"))
W(ability("Fowl Play"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(li("Now adds a chicken illusion per 5 levels", t("NEW")))
_ss_pill, _ss_table = scale_pill(
    "5% + 5% per 5 levels",
    lambda L: 5.0 + 5.0 * (L // 5),
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}%",
)
W(li("Now also provides bonus movement speed equal to " + _ss_pill,
     t("NEW"), extra=_ss_table))
W(ul_close())
W(ability("Urnaconda"))
W(ul_open())
W(li("Aghanim's Shard: New ability — throws a jar at a location, dealing 275 damage to all enemies in a 225 radius and creating a Massive Serpent Ward that lasts for 15s. The ward has 4× health and damage of the normal Serpent Wards. <b>Cooldown:</b> 50s. <b>Mana Cost:</b> 115. <b>Cast Range:</b> 650",
     t("NEW")))
W(ul_close())

# Silencer
W(hero_header("Silencer"))
W(ul_open())
W(li("Base Movement Speed increased from 290 to 300", b(290, 300)))
W(ul_close())
_sil_pill, _sil_table = scale_pill(
    "5% + 0.5% per level",
    lambda L: 5.0 + 0.5 * L,
    value_fmt="{:.1f}%",
)
W(ability_change(
    old=dict(
        name="Brain Drain",
        slug="silencer_brain_drain",
        innate=True,
        desc=[
            "Passive.",
            "Silencer permanently steals Intelligence from enemy heroes he kills or that die nearby.",
            "<b>Intelligence Stolen:</b> 2. <b>Steal Radius:</b> 925.",
            aghs_shard_line("Increases Intelligence Stolen to 4."),
        ],
    ),
    new=dict(
        name="Suffer In Silence",
        slug="silencer_brain_drain",
        innate=True,
        desc=[
            "Passive.",
            "Silencer takes less damage from and deals more damage to silenced targets. Damage modifier is " + _sil_pill + " for both reduction and amplification.",
            "If an enemy hero dies within <b>925 range</b> of Silencer or was debuffed by Silencer at the time of death, he <b>permanently steals 1 Intelligence</b>. If the victim was silenced, an <b>extra 1 Intelligence</b> is stolen.",
        ],
        tables=[_sil_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Arcane Curse", slug="silencer_curse_of_the_silent"))
W(ul_open())
W(li("No longer has 1.25x slow and damage multiplier against silenced enemies", t("DEL")))
W(ul_close())
W(ability("Glaives of Wisdom"))
W(ul_open())
W(li("Mana Cost decreased from 14/16/18/20 to 12/14/16/18", b([14, 16, 18, 20], [12, 14, 16, 18], l=True)))
W(li("Aghanim's Shard: Increases Int Steal by 1 and causes Glaives to bounce once to a random enemy within 450 range", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.25 Arcane Curse Silenced Multiplier replaced with +7% Suffer In Silence Damage", t("REWORK")))
W(li("Level 25 Talent Glaives of Wisdom Damage increased from +25% to +30%", b(25, 30)))
W(li("Level 25 Talent 2 Arcane Curse charges replaced with +2s Global Silence Duration", t("REWORK")))
W(ul_close())

# Skywrath Mage
W(hero_header("Skywrath Mage"))
_sw_pill, _sw_table = scale_pill(
    "13.5 + 1.5 per level",
    lambda L: 13.5 + 1.5 * L,
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Ruin and Restoration",
        innate=True,
        desc=[
            "Passive, levels up with Mystic Flare.",
            "Passively provides Skywrath Mage with <b>20/30/40/50% Spell Lifesteal</b>.",
            "Has 80% penalty against creeps, similarly to other sources of Spell Lifesteal.",
        ],
    ),
    new=dict(
        name="Shield of the Scion",
        slug="skywrath_mage_shield_of_the_scion",
        innate=True,
        desc=[
            "Passive.",
            "Whenever Skywrath Mage deals magical damage with his abilities to an enemy hero, he gains a magic damage barrier equal to " + _sw_pill + " for <b>12s</b>.",
            "Each instance stacks independently.",
        ],
        tables=[_sw_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Concussive Shot"))
W(ul_open())
W(li("Now considers Spirit Bear as a true hero for prioritization. Creep Heroes are now considered as secondary targets", t("MISC")))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ability("Seaborn Sentinel"))
W(ul_open())
W(li("No longer levels with Corrosive Haze", t("REWORK")))
W(li_formula("Bonus HP Regen changed",
             "2.5/5/7.5/10", "1.75 + 0.25 per level",
             lambda L: 10.0, lambda L: 1.75 + 0.25 * L))
W(li("Aghanim's Scepter Bonus HP Regen decreased from +22 to +20", b(22, 20)))
W(li_formula("Bonus Armor changed",
             "3/4/5/6", "1.8 + 0.2 per level",
             lambda L: 6.0, lambda L: 1.8 + 0.2 * L))
W(li("Aghanim's Scepter Bonus Armor decreased from +10 to +8", b(10, 8)))
_sdr_pill, _sdr_table = scale_pill(
    "11.4% + 0.6% per level",
    lambda L: 11.4 + 0.6 * L,
    value_fmt="{:.1f}%",
)
W(li("Flat 8/16/24/32 bonus damage replaced with " + _sdr_pill + " bonus attack damage",
     t("REWORK"), extra=_sdr_table))
W(ul_close())
W(ability("Guardian Sprint", slug="slardar_sprint"))
W(ul_open())
W(li("Slardar now has 100% slow resistance for the first 2.5s of Guardian Sprint. This bonus fades to 0 over the remaining duration", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +14 Seaborn Sentinel Bonus Attack Damage replaced with +30 Bash of the Deep Damage", t("REWORK")))
W(li("Level 15 Talent +40 Bash of the Deep Damage replaced with -3 Corrosive Haze Armor", t("REWORK")))
W(li("Level 20 Talent -4 Corrosive Haze Armor replaced with +16% Seaborn Sentinel Bonus Attack Damage", t("REWORK")))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(ability("Essence Shift"))
W(ul_open())
W(li_formula("Duration changed",
             "15s + 2.5s per level up", "12.5s + 2.5s per level",
             lambda L: 15.0 + (2.5) * L, lambda L: 12.5 + (2.5) * L,
             effective_unchanged=True))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Saltwater Shiv"))
W(ul_open())
W(li("Stacks now have independent durations and don't refresh previous ones", t("REWORK")))
W(li("Cooldown increased from 10/8/6/4s to 14/12/10/8s", b([10, 8, 6, 4], [14, 12, 10, 8], l=True)))
W(li("Mana Cost increased from 20 to 25/30/35/40", b(20, [25, 30, 35, 40], l=True)))
W(li("Cast Range is now Slark's attack range + 50", t("REWORK")))
W(li("Stack Restoration Steal increased from 2/4/6/8% to 4/8/12/16%", b([2, 4, 6, 8], [4, 8, 12, 16])))
W(li("Stack Regen Steal increased from 2/4/6/8 to 4/8/12/16", b([2, 4, 6, 8], [4, 8, 12, 16])))
W(li("Stack Speed Steal increased from 2/4/6/8 to 4/8/12/16", b([2, 4, 6, 8], [4, 8, 12, 16])))
W(li("Now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())

# Snapfire
W(hero_header("Snapfire"))
_boomstick_min_pill, _boomstick_min_table = scale_pill(
    "495 + 5 per level",
    lambda L: 495.0 + 5.0 * L,
    value_fmt="{:.0f}",
)
_boomstick_max_pill, _boomstick_max_table = scale_pill(
    "50 + 5 per level",
    lambda L: 50.0 + 5.0 * L,
    value_fmt="{:.0f}",
)
W(ability_change(
    old=dict(
        name="Buckshot",
        innate=True,
        desc=[
            "Passive.",
            "Snapfire's attacks deal <b>25% more damage</b>, but they have a <b>25% chance</b> of a glancing shot that will deal <b>50% less damage</b>.",
        ],
    ),
    new=dict(
        name="Boomstick",
        innate=True,
        desc=[
            "Passive.",
            "Snapfire deals more damage with her attacks and abilities, the closer she is to her target.",
            "<b>Min Damage Amp:</b> 0% at a distance of " + _boomstick_min_pill + ".",
            "<b>Max Damage Amp:</b> 35% at a distance of " + _boomstick_max_pill + ".",
        ],
        tables=[_boomstick_min_table, _boomstick_max_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Scatterblast"))
W(ul_open())
W(li("Point-blank damage bonus decreased from 50% to 30%", b(50, 30)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Lil' Shredder Attacks increased from +1 to +2", b(1, 2)))
W(ul_close())

# Sniper
W(hero_header("Sniper"))
W(ability("Keen Scope"))
W(ul_open())
W(li("No longer levels with Assassinate", t("REWORK")))
W(li("No longer increases attack range", t("DEL")))
_sn_pill, _sn_table = scale_pill(
    "1.5% + 0.05% per level",
    lambda L: 1.5 + 0.05 * L,
    value_fmt="{:.2f}%",
)
W(li("Now increases damage from Sniper's attacks by " + _sn_pill + " for every 100 units of distance between him and the target",
     t("NEW"), extra=_sn_table))
W(li("Also affects attack damage from Assassinate", t("NEW")))
W(ul_close())
W(ability("Take Aim"))
W(ul_open())
W(li("Now passively grants 160/240/320/400 attack range", t("NEW")))
W(li("Active Bonus Attack Range rescaled from 100/150/200/250 to 75/150/225/300", b([100, 150, 200, 250], [75, 150, 225, 300])))
W(ul_close())
W(ability("Assassinate"))
W(ul_open())
W(li("No longer amplifies attack damage to 100/110/120%", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +55 Take Aim Attack Range Bonus replaced with +50 Take Aim Passive Attack Range", t("REWORK")))
W(ul_close())

# Spectre
W(hero_header("Spectre"))
W(ul_open())
W(li("Base Movement Speed increased from 290 to 295", b(290, 295)))
W(li("Base Health Regen increased from 1.0 to 1.5", b(1.0, 1.5)))
W(ul_close())
W(ability("Desolate"))
W(ul_open())
W(li_formula("Damage changed",
             "25 + 2 per level up", "23 + 2 per level",
             lambda L: 25.0 + (2.0) * L, lambda L: 23.0 + (2.0) * L,
             effective_unchanged=True))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Shadow Step"))
W(ul_open())
W(li("Cooldown decreased from 30/26/22/18s to 24/21/18/15s", b([30, 26, 22, 18], [24, 21, 18, 15], l=True)))
W(li("Cast Range increased from 750/900/1050/1200 to 825/950/1075/1200", b([750, 900, 1050, 1200], [825, 950, 1075, 1200])))
W(li("Illusion Damage increased from 32/38/44/50% to 35/40/45/50%", b([32, 38, 44, 50], [35, 40, 45, 50])))
W(li("Illusion Damage Taken decreased from 200% to 200/185/170/155%", b(200, [200, 185, 170, 155])))
W(ul_close())
W(ability("Haunt"))
W(ul_open())
W(li("Cooldown decreased from 180/160/140s to 160/150/140s", b([180, 160, 140], [160, 150, 140], l=True)))
W(li("Duration rescaled from 5/6/7s to 6s", b([5, 6, 7], 6)))
W(li("Illusion Damage decreased from 30/55/80% to 30/50/70%", b([30, 55, 80], [30, 50, 70])))
W(ul_close())

# Spirit Breaker
W(hero_header("Spirit Breaker"))
W(ability_change(
    old=dict(
        name="Herd Mentality",
        innate=True,
        desc=[
            "Passive.",
            "Provides the hero on Spirit Breaker's team with the <b>least Experience points</b> a buff that increases their Experience gain by <b>50%</b> until they reach the level of the second-least.",
        ],
    ),
    new=dict(
        name="Empowering Haste",
        slug="spirit_breaker_bull_rush",
        innate=True,
        desc=[
            "Passive.",
            "Spirit Breaker gains bonus Movement Speed whenever he stuns an enemy. Effect depends on unit type: <b>stunning a hero</b> gives <b>+8% for 2s</b>; <b>other units</b> give <b>+2% for 1s</b>.",
            "Multiple stuns stack with <b>independent durations</b>. Bull Rush duration is paused during Charge of Darkness, but it can still gain new stacks.",
            "Bonus allows Spirit Breaker to go <b>over the max movement speed limit</b>.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Charge of Darkness"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Greater Bash"))
W(ul_open())
W(li("Aghanim's Scepter: Increases knockback by roughly 30%. If a knocked-back enemy collides with another enemy, the second enemy is also bashed, and the original target takes 25% of Spirit Breaker's Greater Bash damage again", t("NEW"),
     extra=inline_note(
         "This effect is applied to Charge of Darkness and Nether Strike as well, since those abilities use Greater Bash.<br>"
         "Creeps take 25% damage of repeated damage.<br>"
         "Bodies of killed units keep flying and pushing enemies."
     )))
W(ul_close())
W(ability("Planar Pocket"))
W(ul_open())
W(li("Aghanim's Shard: Now grants Planar Pocket", t("NEW")))
W(li("Cooldown increased from 25s to 30s", b(25, 30, l=True)))
W(li("Self Magic Resistance decreased from 75% to 40%", b(75, 40)))
W(li("Effect now ends if Spirit Breaker is more than 900 units away from the target", t("REWORK")))
W(li("Now can be cast without cancelling Charge of Darkness", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +45 Damage replaced with +60 Charge of Darkness Bonus Speed", t("REWORK")))
W(li("Level 20 Talent -0.3s Greater Bash Cooldown replaced with +8%/+2% Empowering Haste Movespeed Bonus", t("REWORK")))
W(ul_close())

# Storm Spirit
W(hero_header("Storm Spirit"))
W(ability("Galvanized"))
W(ul_open())
W(li("Leveling up Ball Lightning no longer grants 3 Galvanized charges", t("DEL")))
W(ul_close())
W(ability("Static Remnant"))
W(ul_open())
W(li("Remnants now spawn at Storm Spirit's location and move at 300 speed to the target location", t("NEW")))
W(ul_close())

# Sven
W(hero_header("Sven"))
W(ul_open())
W(li("Base strength increased from 23 to 24", b(23, 24)))
W(li("Damage at level 1 increased from 60–62 to 61–63", br(60, 62, 61, 63)))
W(ul_close())
_sv_pill, _sv_table = scale_pill(
    "0.08 + 0.02 per level",
    lambda L: 0.08 + 0.02 * L,
    value_fmt="{:.2f}",
)
W(ability_change(
    old=dict(
        name="Vanquisher",
        innate=True,
        desc=[
            "Passive.",
            "Sven's attacks deal <b>15% more damage</b> to <b>stunned enemies</b>.",
            "Worked off Sven's base attack damage; talent line scaled the bonus.",
        ],
    ),
    new=dict(
        name="Wrath of God",
        slug="sven_wrath_of_god",
        innate=True,
        desc=[
            "Passive.",
            "Increases the attack damage Sven gains per point of Strength by " + _sv_pill + ".",
            "<b>Disabled by Break.</b>",
        ],
        tables=[_sv_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Warcry"))
W(ul_open())
W(li("Aghanim's Shard reworked: makes Warcry undispellable, increases radius from 700 to 900, and grants a <b>300 physical damage barrier</b> + an additional <b>+3% movement speed</b> bonus when active",
     t("NEW"),
     extra=inline_note("No longer provides a passive aura.")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +10% Vanquisher Bonus Damage replaced with +20% God's Strength Slow Resistance", t("REWORK")))
W(li("Level 20 Talent +20% God's Strength Slow Resistance replaced with -25% Storm Hammer Cooldown and Mana Cost", t("REWORK")))
W(ul_close())

# Techies
W(hero_header("Techies"))
_tch_pill, _tch_table = scale_pill(
    "0.08% + 0.02% per level",
    lambda L: 0.08 + 0.02 * L,
    value_fmt="{:.2f}%",
)
W(ability_change(
    old=dict(
        name="Minefield Sign",
        slug="techies_minefield_sign",
        innate=True,
        desc=[
            "Active.",
            "Places a sign that makes mines within a <b>500 radius</b> invulnerable.",
            "<b>Cast Point:</b> 1.5s. <b>Cooldown:</b> 60s. <b>Duration:</b> 60s. Only one sign can exist at a time.",
            aghs_line("Increases radius to 1000 and duration to 4 minutes. When an enemy hero gets within 200 units of the sign, the entire 1000 radius becomes a minefield for 10s — enemy units take 300 damage for every 200 units moved. Minefield area becomes visible to enemies once activated. The sign is destroyed after the minefield expires."),
        ],
    ),
    new=dict(
        name="M.A.D.",
        slug="techies_mutually_assured_destruction",
        innate=True,
        desc=[
            "Passive.",
            "Increases mana regen by a portion of Techies' max mana equal to " + _tch_pill + ".",
            "When Techies die, they leave behind a barrel that explodes after <b>1.5s</b>, dealing magical damage equal to <b>50 + 30% of their max mana</b> to enemies in a <b>400 AoE</b>. The barrel provides 400 obstructed vision until it explodes.",
            aghs_shard_line("Increases mana-to-damage by 10%. Adds an active component — Techies plant the M.A.D. barrel and detonate it later via a sub-ability. The barrel is invisible and can be destroyed before detonation begins. Detonating makes it visible and immortal, then it explodes after the same 1.5s delay. Only one M.A.D. can exist via the active cast at a time. Barrel Health: 200. Cast Range: 450. No Mana Cost. Cooldown: 30s. Cast Point: 1s."),
        ],
        tables=[_tch_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Reactive Tazer"))
W(ul_open())
W(li("Can now always be cast on allies", t("NEW")))
W(li("Cast Range increased from 500 to 600", b(500, 600)))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Blast Off!", slug="techies_suicide"))
W(ul_open())
W(li("Now deals its self damage before damaging enemies", t("MISC")))
W(li("Techies are now rooted and disarmed instead of self-stunned during Blast Off's leap animation", t("MISC")))
W(ul_close())
W(ability("Proximity Mines", slug="techies_land_mines"))
W(ul_open())
W(li("Damage source changed from Proximity Mines to the caster", t("REWORK")))
W(ul_close())
W(ability("Minefield Sign"))
W(ul_open())
W(li("Now only available with Aghanim's Scepter", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +3 Mana Regen replaced with +25% Reactive Tazer Buff and Disarm Duration", t("REWORK")))
W(li("Level 25 Talent Damage increased from +252 to +253", b(252, 253)))
W(ul_close())

# Templar Assassin
W(hero_header("Templar Assassin"))
W(ul_open())
W(li("Base Health Regen decreased from 1 to 0", b(1, 0)))
W(ul_close())
_ta_ramp_pill, _ta_ramp_table = scale_pill(
    "2.05s − 0.05s per level",
    lambda L: 2.05 - 0.05 * L,
    value_fmt="{:.2f}s",
)
_ta_hp_pill, _ta_hp_table = scale_pill(
    "2.7 + 0.3 per level",
    lambda L: 2.7 + 0.3 * L,
    value_fmt="{:.1f}",
)
_ta_mp_pill, _ta_mp_table = scale_pill(
    "2.2 + 0.2 per level",
    lambda L: 2.2 + 0.2 * L,
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Third Eye",
        innate=True,
        desc=[
            "Passive.",
            "Templar Assassin and her teammates can see <b>Roshan's respawn timer</b>. The indicator is displayed above the Scan ability.",
        ],
    ),
    new=dict(
        name="Inner Peace",
        slug="templar_assassin_inner_peace",
        innate=True,
        desc=[
            "Passive.",
            "After remaining stationary for 0.25s, Templar Assassin begins meditating, gaining bonus health regen and mana regen. Bonuses linearly ramp from 0 up to their maximum, reached after " + _ta_ramp_pill + ".",
            "Moving from the current position or taking damage from an enemy <b>resets</b> the regen bonuses.",
            "<b>Max Health Regen:</b> " + _ta_hp_pill + ".  <b>Max Mana Regen:</b> " + _ta_mp_pill + ".",
        ],
        tables=[_ta_ramp_table, _ta_hp_table, _ta_mp_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Refraction"))
W(ul_open())
W(li("Aghanim's Shard: Increases bonus damage by 30 and allows Refraction to be cast while disabled", t("NEW")))
W(ul_close())
W(ability("Meld"))
W(ul_open())
W(li("Now, if the attack that broke Meld splits with Psi Blades, Bonus Damage and Armor Reduction are now applied to all affected enemies", t("NEW")))
W(ul_close())
W(ability("Psionic Trap"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(li("Aghanim's Scepter: When activated, Traps now also silence enemies from 0.25s up to 3s depending on the trap charge", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +3 Meld Armor reduction replaced with +3 Psionic Traps", t("REWORK")))
W(li("Level 15 Talent Refraction Can Be Cast While Disabled replaced with +225 Meld Attack Range", t("REWORK")))
W(li("Level 20 Talent +40 Refraction Damage replaced with +4 Meld Armor Reduction", t("REWORK")))
W(ul_close())

# Terrorblade
W(hero_header("Terrorblade"))
W(ul_open())
W(li("Base Armor increased by 1", bstat_h("Terrorblade", "ArmorPhysical", "7.40c", 1), extra=note_box(hero="Terrorblade", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
W(ability("Conjure Image"))
W(ul_open())
W(li("Illusion Damage increased from 20/25/30/35% to 25/30/35/40%", b([20, 25, 30, 35], [25, 30, 35, 40])))
W(ul_close())
W(ability("Demon Zeal"))
W(ul_open())
W(li("Cooldown decreased from 60s to 45s", b(60, 45, l=True)))
W(li("Duration decreased from 30s to 25s", b(30, 25)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +15% Reflection Slow/Damage replaced with -25% Sunder Minimum HP Swap", t("REWORK")))
W(ul_close())

# Tidehunter
W(hero_header("Tidehunter"))
W(ul_open())
W(li("Strength gain increased from 3.6 to 3.7", b(3.6, 3.7)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Blubber",
        innate=True,
        desc=[
            "Passive.",
            "Tidehunter removes negative status effects (<b>Strong Dispel</b>) if he takes more than <b>500 damage</b> from player-controlled sources. Damage counter resets after <b>7s</b>.",
        ],
    ),
    new=dict(
        name="Leviathan's Catch",
        slug="tidehunter_leviathans_catch",
        innate=True,
        desc=[
            "Passive.",
            "Whenever an enemy hero dies while affected by any of Tidehunter's debuffs or is killed by him, they <b>drop a fish</b>.",
            "Tidehunter can eat the fish to grow in size and <b>permanently gain +3 Max Health, +2 Attack Range, and +1 Bonus Damage Block</b>. Tidehunter also <b>automatically eats a fish on every level-up</b>."
            + inline_note(
                "The fish flies 400 units towards Tidehunter upon spawning, stays in the world indefinitely and can be destroyed by an attack from Tidehunter's enemies.<br>"
                "Bonus Damage Block is only applied if there is a source of damage block being applied to an incoming physical attack."
            ),
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Anchor Smash"))
W(ul_open())
W(li("Radius changed from 375 to 225 + Tidehunter's Attack Range", t("REWORK"),
     extra=inline_note("Tidehunter's base Attack Range is 150, so the effective radius at level 1 is 375 — unchanged before Fish bonuses.")))
W(ul_close())
W(ability("Kraken Shell"))
W(ul_open())
W(li("Now applies a strong dispel to Tidehunter if he takes more than 600/550/500/450 damage within 7 seconds", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Blubber effect triggers Anchor Smash replaced with Kraken Shell Cleanse triggers Anchor Smash", t("REWORK")))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ability("Exposure Therapy"))
W(ul_open())
W(li("No longer levels with Chakram", t("REWORK")))
W(li_formula("Mana gain per tree destroyed changed",
             "4/6/8/10", "3.75 + 0.25 per level",
             lambda L: 10.0, lambda L: 3.75 + 0.25 * L))
W(ul_close())

# Tinker
W(hero_header("Tinker"))
W(ul_open())
W(li("Base health regen increased from 0 to 0.5", b(0, 0.5)))
W(li("Base Movement Speed decreased from 310 to 305", b(310, 305)))
W(ul_close())
W(ability("Laser"))
W(ul_open())
W(li("Aghanim's Scepter no longer adds bounces", t("DEL")))
W(ul_close())
W(ability("March of the Machines"))
W(ul_open())
W(li("Aghanim's Scepter: Robots apply a non-stacking heal over time of 35 health per second to allies they come through. Heal duration: 4 seconds", t("NEW")))
W(ul_close())
W(ability_change(
    summary="New ability.",
    tag="new",
    old=dict(
        name="Defense Matrix",
        slug="tinker_defense_matrix",
        desc=[
            "Surrounds the target ally with an energy field that absorbs <b>100/180/240/320</b> magical damage and grants <b>10/20/30/40%</b> Status Resistance. Lasts 12 seconds.",
            "Cast Range: 700/750/800/850. Mana Cost: 70/80/90/100. Cooldown: 20s.",
        ],
    ),
    new=dict(
        name="Deploy Turrets",
        slug="tinker_deploy_turrets",
        desc=[
            "After a 0.5s delay, airdrops a group of three uncontrollable turrets at the target 250 radius area, dealing <b>40/80/120/160</b> magical damage, destroying trees and pushing away enemies by 100 units and Tinker by 350.",
            "Turrets seek enemy heroes within <b>650/700/750/800</b> range and shoot missiles in their direction every 1.5 seconds. The missile deals <b>20/40/60/80</b> magical damage to the enemy it hits and 50% of the damage to other enemies within 200 AoE. Each turret has <b>40/80/120/160</b> health and exists for 4.5 seconds.",
            "<b>Stats:</b> Gold Bounty 5/10/15/20. XP Bounty 5/10/15/20. Turn Rate 0.55. Missile Speed 1200. Missile Flight Distance 650/700/750/800.",
            "<b>Cast:</b> Cast Range 600. Mana Cost 100/120/140/160. Cooldown 24/22/20/18s. Cast Point 0.1s."
            + inline_note(
                "Each of three turrets activates with a small delay after the previous one (0.1s, 0.6s, and 1.1s after deployment)."
                "<br>The missile flies in a forward direction and can be dodged by moving out of its way."
                "<br>Turrets target heroes only, but missiles can hit creeps on their way."
                "<br>Turrets prioritize the same hero until they are out of reach. Splash damage is not dealt to the hit unit itself."),
            aghs_line("Turrets activate 0.3s faster, and fire missiles 20% faster, which results in firing one additional volley of missiles."),
        ],
    ),
))
W(ability("Rearm"))
W(ul_open())
W(li("Cooldown decreased from 7/6/5s to 5.5/5/4.5s", b([7, 6, 5], [5.5, 5, 4.5], l=True)))
W(ul_close())
W(ability("Warp Flare", slug="tinker_warp_grenade"))
W(ul_open())
W(li("Teleport distance now depends on Warp Flare cast range and scales with distance from Tinker, so that nearby enemies are teleported further than far enemies", t("REWORK"),
     extra=inline_note("Max teleportation distance is 60% of Warp Flare's cast range and decreases down to 0 at the max cast range (700 by default).")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +60 Defense Matrix Damage Barrier replaced with +100 Deploy Turrets Tinker Knockback", t("REWORK")))
W(li("Level 20 Talent +10% Defense Matrix Status Resistance replaced with +60 Deploy Turrets Missile Damage", t("REWORK")))
W(li("Level 25 Talent: +40 Intelligence replaced with -0.25s Time to Rearm", t("REWORK")))
W(li("Level 25 Talent: Laser AoE increased from 200 to 250", b(200, 250)))
W(ul_close())

# Tiny
W(hero_header("Tiny"))
W(ability_change(
    old=dict(
        name="Craggy Exterior",
        slug="tiny_craggy_exterior",
        innate=True,
        desc=[
            "Passive.",
            "Enemies that attack Tiny get a stacking debuff that decreases their attack damage by <b>2/3/4/5%</b> per stack (levels with Grow). <b>Max Stacks:</b> 10. <b>Debuff Duration:</b> 5s (refreshes on each stack).",
        ],
    ),
    new=dict(
        name="Insurmountable",
        slug="tiny_insurmountable",
        innate=True,
        desc=[
            "Passive.",
            "Slow Resistance now also applies to <b>Attack Speed Slows</b>.",
            "Tiny gains <b>Slow Resistance equal to 20% of his Strength</b> and <b>Status Resistance equal to 10% of his Strength</b>.",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Avalanche"))
W(ul_open())
W(li("Mana Cost increased from 95/110/125/140 to 105/120/135/150", b([95, 110, 125, 140], [105, 120, 135, 150], l=True)))
W(li("Damage decreased from 100/190/280/370 to 90/180/270/360", b([100, 190, 280, 370], [90, 180, 270, 360])))
W(ul_close())
W(ability("Toss"))
W(ul_open())
W(li("Mana Cost rescaled from 110/125/140/155 to 125", b([110, 125, 140, 155], 125, l=True)))
W(ul_close())
W(ability("Tree Grab"))
W(ul_open())
W(li("Mana Cost decreased from 40 to 40/35/30/25", b(40, [40, 35, 30, 25], l=True)))
W(li("Cooldown decreased from 16/15/14/13s to 15/12/9/6s", b([16, 15, 14, 13], [15, 12, 9, 6], l=True)))
W(li("Cast Range increased from 165 to 200", b(165, 200)))
W(li("Attacks rescaled from 5 to 4/5/6/7", b(5, [4, 5, 6, 7])))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Tree Throw", slug="tiny_toss_tree"))
W(ul_open())
W(li("No longer applies a slow on the tossed tree by default", t("DEL")))
W(ul_close())
W(ability("Grow"))
W(ul_open())
W(li("Aghanim's Shard: Thrown trees and tossed units deal 20% more damage in their AoE, have +125 radius, and apply a 25% movement slow and a 45 attack speed slow to all units in the AoE of Toss, Tree Throw, and Tree Volley for 2.5s. Damage is not increased for the Tossed unit itself", t("NEW")))
W(ul_close())
W(ability("Tree Volley", slug="tiny_tree_channel"))
W(ul_open())
W(li("Now uses the bonus damage value of Tree Throw and bonuses from Aghanim's Shard", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Avalanche Cast Range decreased from +200 to +150", b(200, 150)))
W(li("Level 15 Talent Avalanche Damage decreased from +100 to +90", b(100, 90)))
W(ul_close())

# Treant Protector
W(hero_header("Treant Protector"))
W(ability("Nature's Guise"))
W(ul_open())
W(li_formula("Cooldown changed",
             "35s - 1s per level up", "36s - 1s per level",
             lambda L: 35.0 + (-1.0) * L, lambda L: 36.0 + (-1.0) * L, l=True,
             effective_unchanged=True))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Living Armor"))
W(ul_open())
W(li("Mana Cost increased from 40/45/50/55 to 65/70/75/80", b([40, 45, 50, 55], [65, 70, 75, 80], l=True)))
W(li("Max Damage Blocked decreased from 120 to 60/80/100/120", b(120, [60, 80, 100, 120])))
W(li("Damage Block Decrease improved from 35/30/25/20 to 20", b([35, 30, 25, 20], 20)))
W(ul_close())
W(ability("Eyes In The Forest"))
W(ul_open())
W(li("Charge Restore Time increased from 55s to 135s", b(55, 135, l=True)))
W(li("Duration increased from 300s to 360s", b(300, 360)))
W(li("Max Charges decreased from 3 to 2", b(3, 2)))
W(ul_close())

# Troll Warlord
W(hero_header("Troll Warlord"))
W(ability("Battle Stance", slug="troll_warlord_switch_stance"))
W(ul_open())
W(li("Troll Warlord gains 1 armor per 30 bonus attack speed", t("NEW")))
W(ul_close())
W(ability("Berserker's Rage"))
W(ul_open())
W(li("No longer provides +3/4/5/6 Bonus Armor while in melee form", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +115 Whirling Axes Damage replaced with +1s Battle Trance Duration", t("REWORK")))
W(li("Level 20 Talent +10 Berserker's Rage Armor replaced with +160 Whirling Axes Damage", t("REWORK")))
W(li("Level 20 Talent +1.5s Battle Trance Duration replaced with Allies Receive Battle Trance Attack Speed", t("REWORK")))
W(ul_close())

# Tusk
W(hero_header("Tusk"))
W(ability("Bitter Chill"))
W(ul_open())
W(li("No longer levels with Walrus Punch!", t("REWORK")))
W(li_formula("Attack Speed Slow rescaled",
             "20/40/60/80", "17 + 3 per level",
             lambda L: 80.0, lambda L: 17.0 + 3.0 * L))
W(li("Now only affects enemy heroes", t("REWORK")))
W(ul_close())
W(ability("Tag Team"))
W(ul_open())
W(li("Now always a basic ability for Tusk", t("REWORK")))
W(ul_close())
W(ability("Ice Shards"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Drinking Buddies"))
W(ul_open())
W(li("Aghanim's Shard: Tusk reaches out to tag an allied unit, pulling them closer. Once tagged, both Tusk and his tagged ally gain 25% bonus movement speed and 10 bonus armor for 6s. Can be put on alt-cast to only pull Tusk towards his ally with 50% reduced cast range. Cast Range: 1000. Mana Cost: 80. Cooldown: 14s", t("NEW")))
W(li("No longer provides 20/50/80/110 bonus attack damage", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent -6s Ice Shards Cooldown replaced with -6s Snowball Cooldown", t("REWORK")))
W(li("Level 25 Talent -8s Snowball Cooldown replaced with Ice Shards Slow by 50% and Deal 110 DPS (only affects enemies trapped inside)", t("REWORK")))
W(ul_close())

# Underlord
W(hero_header("Underlord"))
W(ability("Invading Force", slug="abyssal_underlord_raid_boss"))
W(ul_open())
W(li("No longer levels with Fiend's Gate", t("REWORK")))
W(li_formula("Damage Reduction rescaled",
             "4/6/8/10%", "3.7% + 0.3% per level",
             lambda L: 10.0, lambda L: 3.7 + 0.3 * L))
W(li_formula("Movement Speed bonus rescaled",
             "11/14/17/20%", "9.5% + 0.5% per level",
             lambda L: 20.0, lambda L: 9.5 + 0.5 * L))
W(ul_close())
W(ability("Firestorm"))
W(ul_open())
W(li("Wave Damage increased from 30/50/70/90 to 30/55/80/105", b([30, 50, 70, 90], [30, 55, 80, 105])))
W(ul_close())
W(ability("Atrophy Aura"))
W(ul_open())
W(li("Damage Reduction increased from 6/14/22/30% to 8/16/24/32%", b([6, 14, 22, 30], [8, 16, 24, 32])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Firestorm Cooldown Reduction increased from 4s to 5s", b(4, 5)))
W(li("Level 25 Talent Fiend's Gate DPS increased from 125 to 160", b(125, 160)))
W(ul_close())

# Undying
W(hero_header("Undying"))
W(ul_open())
W(li("Base Agility increased from 10 to 13", b(10, 13)))
W(li("Base Armor decreased by 1", bstat_h("Undying", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Undying", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
W(ability("Flesh Golem"))
W(ul_open())
W(li("Attacks now spawn the current level of Tombstone Zombie", t("NEW")))
W(ul_close())

# Vengeful Spirit
W(hero_header("Vengeful Spirit"))
W(ul_open())
W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
W(li("Base Attack Time improved from 1.7s to 1.5s", b(1.7, 1.5, l=True)))
W(ul_close())
W(ability("Retribution"))
W(ul_open())
W(li("Now also makes Vengeful Spirit to gain benefits of both melee and ranged attacks", t("NEW")))
W(li("Now killer's icon is shown as a buff on Vengeful Spirit to know who to hate", t("MISC")))
W(ul_close())
W(ability("Vengeance Aura", slug="vengefulspirit_command_aura"))
W(ul_open())
W(li("Now provides 1.2x the bonus for Vengeful Spirit herself", b(1.0, 1.2),
     extra=inline_note("Self-bonus values: <b>12/18/24/30%</b> (vs. <b>10/15/20/25%</b> for allies)."
                       "<br>With Level 25 Talent: <b>31.2/37.2/43.2/49.2%</b> (vs. <b>26/31/36/41%</b> for allies).")))
W(li("Aghanim's Scepter upgrade no longer refreshes ability cooldowns on activating", t("DEL")))
W(li("Aghanim's Scepter now increases self-bonus up to 1.3x", t("NEW")))
W(li("Aghanim's Scepter illusion is now fully affected by Vengeance Aura's bonus", t("NEW")))
W(li("Aghanim's Scepter illusion damage taken decreased from 115% to 100%", b(115, 100)))
W(ul_close())

# Venomancer
W(hero_header("Venomancer"))
_ven_dps_pill, _ven_dps_table = scale_pill(
    "9 + 1 per level",
    lambda L: 9.0 + 1.0 * L,
    value_fmt="{:.0f}",
)
_ven_dur_pill, _ven_dur_table = scale_pill(
    "4.5s + 0.5s per level",
    lambda L: 4.5 + 0.5 * L,
    value_fmt="{:.1f}s",
)
W(ability_change(
    old=dict(
        name="Septic Shock",
        innate=True,
        desc=[
            "Passive.",
            "Venomancer's attacks deal extra magical damage based on how many debuffs the target has (only counts debuffs from Venomancer and his Plague Wards). <b>Base Damage per debuff:</b> 10%.",
            aghs_line("Increases damage per debuff from 10% to 20%. Plague Wards also deal Septic Shock damage based on their attack damage."),
        ],
    ),
    new=dict(
        name="Poison Sting",
        slug="venomancer_poison_sting",
        innate=True,
        desc=[
            "Passive.",
            "Imbues Venomancer's attacks with poison: <b>" + _ven_dps_pill + "</b> damage per second and a flat <b>10% movement slow</b>.",
            "<b>Duration:</b> " + _ven_dur_pill + ".",
        ],
        tables=[_ven_dps_table, _ven_dur_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Venomous Gale"))
W(ul_open())
W(li("Aghanim's Shard reworked: Increases cast range and projectile speed by 25%. Creates 2 Plague Wards around every enemy hero hit", t("REWORK")))
W(ul_close())
W(ability("Snakebite"))
W(ul_open())
W(li("New basic ability — Venomancer summons a Spawn of Aktok to sink its fangs into an enemy, dealing <b>40/60/80/100</b> magic damage and applying a deadly toxin which does <b>20/25/30/35</b> magical damage per second for 6 seconds. When the target attacks, they take the initial magic damage again. <b>Cast Range:</b> 600. <b>Mana Cost:</b> 70/80/90/100. <b>Cooldown:</b> 20/18/16/14s",
     t("NEW")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Noxious Plague",
        slug="venomancer_noxious_plague",
        desc=[
            # Source: data/patchnotes_english.txt → DOTA_Patch_7_33_venomancer_venomancer_noxious_plague_2 (introducing patch) + subsequent tweak rows up to 7.40c.
            "Infects an enemy with a deadly plague that does an initial burst of damage and additional damage over time based on the unit's maximum health.",
            "Enemies in a radius around the target are slowed, with values decreasing the farther you are from the affected enemy.",
            "When the target dies or the debuff expires/is absorbed, all nearby enemies are infected with a noncommunicable version of the plague.",
            "<b>Duration:</b> 5s. <b>Initial Damage:</b> 200/300/400. <b>Max HP as Damage:</b> 3/4/5%. <b>Debuff Radius:</b> 800. <b>Min/Max Slow:</b> 15% / 50%. <b>Cooldown:</b> 100/90/80s. <b>Mana Cost:</b> 200/300/400.",
        ],
    ),
    new=dict(
        name="Noxious Plague",
        slug="venomancer_noxious_plague",
        desc=[
            # Source: data/patchnotes_english.txt → DOTA_Patch_7_41_venomancer_venomancer_noxious_plague_{2,3,8,9} verbatim + remaining stat lines derived from 7.40c baseline modified by 7.41 deltas (_5,_6,_7,_10,_11).
            "Infects an enemy with a deadly plague that does an initial burst of damage and additional damage over time based on the unit's maximum health. Initial Damage is now non-lethal.",
            "No longer has AoE effect, now affects only the host.",
            "Now when the plague spreads, it also carries all debuffs placed by Venomancer. Now spreads a second time, but all spreads after the first one deal no initial damage."
            + inline_note("Doesn't stack. Applying plague to an already plague-infected unit will deal projectile damage again, but won't affect the remaining debuff duration. Duration of carried debuffs is fixed and cannot be altered with Status Resistance or Debuff Amplification."),
            "<b>Duration:</b> 4s. <b>Initial Damage:</b> 150/200/250. <b>Max HP as Damage:</b> 2/3/4%. <b>Spread Radius:</b> 700. <b>Cooldown:</b> 100/90/80s. <b>Mana Cost:</b> 200/250/300.",
            aghs_line("Decreases cooldown by 35s. Reduces Magic Resistance of affected units by 20% and allows additional spreads to deal initial damage."),
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ul_open())
W(li("Mana Cost decreased from 200/300/400 to 200/250/300", b([200, 300, 400], [200, 250, 300], l=True)))
W(li("Duration decreased from 5s to 4s", b(5, 4)))
W(li("Initial Damage decreased from 200/300/400 to 150/200/250", b([200, 300, 400], [150, 200, 250])))
W(li("Spread Radius decreased from 800 to 700", b(800, 700)))
W(li("Max HP as damage decreased from 3/4/5% to 2/3/4%", b([3, 4, 5], [2, 3, 4])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Poison Sting Slow increased from +5% to +7%", b(5, 7)))
W(li("Level 15 Talent -1s Plague Ward Cooldown replaced with +75 Noxious Plague Spread Radius", t("REWORK")))
W(li("Level 20 Talent +50 Base Damage replaced with -2s Plague Ward Cooldown", t("REWORK")))
W(li("Level 20 Talent +1% Noxious Plague Max HP Damage replaced with +40% Snakebite Damage (applies to both initial damage and damage per second)", t("REWORK")))
W(li("Level 25 Talent Noxious Plague Aura reduces 200 Attack Speed replaced with Snakebite Undispellable", t("REWORK")))
W(ul_close())

# Viper
W(hero_header("Viper"))
W(ul_open())
W(li("Agility gain increased from 2.7 to 2.9", b(2.7, 2.9)))
W(li("Base Attack Speed decreased from 120 to 110", b(120, 110)))
W(ul_close())
W(ability("Predator"))
W(ul_open())
W(li("Base Damage per Missing Health Percentage increased from 0.15 to 0.25", b(0.15, 0.25)))
W(ul_close())
W(ability("Corrosive Skin"))
W(ul_open())
W(li("Aghanim's Scepter now also gradually increases Corrosive Skin's magic resistance and damage per second while he is in Nethertoxin, up to 50% increased effect after 4s", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +10% Poison Attack slow/damage replaced with +15 Corrosive Skin Damage Per Second", t("REWORK")))
W(li("Level 15 Talent +20 Corrosive Skin Damage Per Second replaced with +15% Poison Attack Slow / Damage", t("REWORK")))
W(li("Level 15 Talent +30 Nethertoxin Min/Max Damage replaced with +20/40 Nethertoxin Min/Max Damage", t("REWORK")))
W(li("Level 20 Talent Predator Damage Per Missing Health increased from +0.3 to +0.35", b(0.3, 0.35)))
W(ul_close())

# Visage
W(hero_header("Visage"))
_visage_satg_pill, _visage_satg_table = scale_pill(
    "45.75s − 0.75s per level",
    lambda L: 45.75 - 0.75 * L,
    value_fmt="{:.2f}s",
)
W(ability_change(
    old=dict(
        name="Lurker",
        innate=True,
        desc=[
            "Passive.",
            "Visage's ability cooldowns are <b>reduced as long as he's not taking damage</b>. Gains a stack every 2s without damage taken. Each stack grants <b>2% cooldown speed</b> (max 10 stacks). Stacks fade after 2s upon taking any damage.",
        ],
    ),
    new=dict(
        name="Silent as the Grave",
        slug="visage_silent_as_the_grave",
        innate=True,
        desc=[
            "Active.",
            "Visage gains <b>flying movement and +12% movement speed for 20s</b>. Upon attacking or casting, he loses both effects, but he and his familiars gain <b>+10% attack damage for 2s</b>.",
            "<b>Mana Cost:</b> 50.  <b>Cooldown:</b> " + _visage_satg_pill + ".",
            aghs_line("Increases bonus movement speed by +12%, bonus damage by +10%, bonus damage duration by +2s, and flight duration by +10s. While flight is active, Silent as the Grave grants <b>invisibility</b> to Visage and his familiars.",
                      inline_note_text="Invisibility for Visage and each familiar are not connected."),
        ],
        tables=[_visage_satg_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ul_open())
W(li("Mana Cost decreased from 115 to 50", b(115, 50, l=True)))
W(li_formula("Cooldown changed",
             "45s", "45.75s − 0.75s per level",
             lambda L: 45.0, lambda L: 45.75 - 0.75 * L,
             l=True, value_fmt="{:.2f}s"))
W(ul_close())
W(ability("Summon Familiars"))
W(ul_open())
W(li("Cooldown decreased from 130/120/110s to 120/110/100s", b([130, 120, 110], [120, 110, 100], l=True)))
W(li("Familiar Health rescaled from 500/600/700 to 450/600/750", b([500, 600, 700], [450, 600, 750], force_overall="buff")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +6 Visage and Familiars Attack Damage replaced with +6 Visage and Familiars Base Damage", t("REWORK")))
W(li("Level 10 Talent +4 Lurker Max Stacks replaced with -1s Soul Assumption Cooldown", t("REWORK")))
W(li("Level 20 Talent Soul Assumption Damage Per Charge increased from +25 to +30", b(25, 30)))
W(ul_close())

# Void Spirit
W(hero_header("Void Spirit"))
W(ul_open())
W(li("Base Damage decreased by 4", t("MISC") + bstat_h("Void Spirit", "AttackDamageMin", "7.40c", -4), extra=note_box(hero="Void Spirit", field="AttackDamageMin", before_patch="7.40c", extra_note="Damage at level 1 unchanged due to innate ability changes")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Intrinsic Edge",
        slug="void_spirit_intrinsic_edge",
        innate=True,
        desc=[
            # Source: data/patchnotes_english.txt → DOTA_Patch_7_36_void_spirit_hero_innate_void_spirit_intrinsic_edge_{1,2,2_info} + 7.36b tweak.
            "Passive.",
            "Void Spirit gains <b>25%</b> more secondary bonuses from Primary Attributes."
            + inline_note("Health Regen from Strength, Armor from Agility, Mana Regen and Magic Resistance from Intelligence."),
        ],
    ),
    new=dict(
        name="Intrinsic Edge",
        slug="void_spirit_intrinsic_edge",
        innate=True,
        desc=[
            # Source: data/patchnotes_english.txt → DOTA_Patch_7_41_void_spirit_void_spirit_intrinsic_edge_{1,7,8,9} folded into a coherent description.
            "Passive.",
            "Void Spirit gains <b>30%</b> more secondary bonuses from Primary Attributes, and his attack damage per point of attribute is multiplicatively increased by <b>15%</b>."
            + inline_note("Health Regen from Strength, Attack Speed from Agility, Mana Regen from Intelligence. No longer provides Armor or Magic Resistance."),
        ],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ul_open())
W(li("Attack damage per attribute multiplier increased from 0.45 to 0.5175", b(0.45, 0.5175)))
W(li("Secondary bonuses increased from 25% to 30%", b(25, 30)))
W(li("The result of these changes:", t("MISC"),
     extra=inline_note(
         "Damage at level 1 is unchanged at 52–56."
         "<br>Damage gain per level increased from 3.6 to 4.1 — " + b(3.6, 4.1) +
         "<br>Damage at level 30 increased from 174–178 to 192–196 — " + br(174, 178, 192, 196)
     )))
W(ul_close())
W(ability("Aether Remnant"))
W(ul_open())
W(li("Aghanim's Shard True Sight no longer reveals wards", t("NERF")))
W(ul_close())
W(ability("Resonant Pulse"))
W(ul_open())
W(li("Barrier Amount per hero hit increased from 35/50/65/80 to 50/70/90/110", b([35, 50, 65, 80], [50, 70, 90, 110])))
W(ul_close())

# Warlock
W(hero_header("Warlock"))
W(ability("Eldritch Summoning"))
W(ul_open())
W(li("No longer levels with Chaotic Offering", t("REWORK")))
W(li_formula("Minor Imp Health rescaled",
             "50/130/210/290", "5 + 15 per level",
             lambda L: 290.0, lambda L: 5.0 + 15.0 * L))
W(li_formula("Minor Imp Explosion Damage rescaled",
             "25/70/115/160", "20 + 20 per 3 hero levels",
             lambda L: 160.0, lambda L: 20.0 + 20.0 * (L // 3)))
W(li_formula("Minor Imp movement speed rescaled",
             "300/315/330/345", "297 + 3 per level",
             lambda L: 345.0, lambda L: 297.0 + 3.0 * L))
W(li("Minor Imp attack damage rescaled from 10-11/14-15/18-19/22-23/26-27 to 20-21", br(26, 27, 20, 21)))
W(li("Aghanim's Shard now increases health of minor imps by 80 and explosion damage by 45", t("MISC"),
     extra=inline_note("Same values as before, but explicitly stated now.")))
W(ul_close())

# Weaver
W(hero_header("Weaver"))
W(ability_change(
    old=dict(
        name="Rewoven",
        innate=True,
        desc=[
            "Passive.",
            "Every time Weaver casts an ability, he gains <b>+50 attack range</b> for <b>7s</b>. Effect stacks independently per cast.",
        ],
    ),
    new=dict(
        name="Threads of Fate",
        innate=True,
        desc=[
            "Passive.",
            "After dealing damage to an enemy hero with an attack or ability, if Weaver remains within <b>700 range</b> of them for <b>1.5s</b>, he establishes a <b>Thread of Fate</b> that slows the enemy's movement by <b>100% for 0.2s</b> and ties them to Weaver.",
            "Each established thread grants <b>+10% bonus damage</b> to Weaver. Threads last up to <b>6s</b> and break if the distance becomes longer than <b>900</b>.",
            "If the enemy dies with a Thread of Fate established, the thread's bonuses linger for an additional <b>5s</b>."
            + inline_note("Effects linger even if the enemy dies just as the thread is about to be established."),
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +60 Shukuchi Damage replaced with +50 Shukuchi Movement Speed", t("REWORK")))
W(li("Level 15 Talent +20 Mana Break replaced with +90 Shukuchi Damage", t("REWORK")))
W(li("Level 20 Talent Bonus Damage on Geminate decreased from +70 to +60", b(70, 60)))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ul_open())
W(li("Base Movement Speed decreased from 290 to 285", b(290, 285)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Easy Breezy",
        innate=True,
        desc=[
            "Passive.",
            "Windranger's movement speed <b>cannot drop below 240</b>. Max Movement Speed cap increased from 550 to <b>600</b>.",
        ],
    ),
    new=dict(
        name="Tailwind",
        slug="windrunner_tailwind",
        innate=True,
        desc=[
            "Passive.",
            "Using an ability conjures a stacking <b>Tailwind</b> that gives Windranger a brief burst of movement speed. The bonus starts gradually fading halfway through the duration.",
            "<b>Movement Speed Bonus per stack:</b> 35%.  <b>Duration:</b> 2s.",
            "Passively increases Windranger's <b>max movement speed cap to 600</b>.",
            aghs_line("Attacks also grant Tailwind effect. Increases Tailwind duration to 3s and makes it undispellable."),
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Windrun"))
W(ul_open())
W(li("Movement Speed Bonus decreased from 60% to 50%", b(60, 50)))
W(li("Cooldown decreased from 15/14/13/12s to 14/13/12/11s", b([15, 14, 13, 12], [14, 13, 12, 11], l=True)))
W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +4 All Attributes replaced with +0.75s Windrun Duration", t("REWORK")))
W(li("Level 15 Talent -2s Windrun Cooldown replaced with +40 Tailwind Max Movespeed", t("REWORK")))
W(li("Level 25 Talent Windrun Cannot be Dispelled replaced with Powershot Executes Enemy Heroes Under 15% Max HP (Execute Threshold ranges from 10-15% Max HP Based on channel time and reduces with each unit the arrow comes through)", t("REWORK")))
W(ul_close())

# Winter Wyvern
W(hero_header("Winter Wyvern"))
W(ability_change(
    old=dict(
        name="Eldwurm Scholar",
        innate=True,
        desc=[
            "Passive.",
            "When an allied hero picks up a <b>Wisdom Rune</b>, the 3 heroes that wouldn't benefit from it gain <b>20% of the experience</b> instead.",
        ],
    ),
    new=dict(
        name="Eldwurm's Edda",
        slug="winter_wyvern_eldwurms_edda",
        innate=True,
        desc=[
            "Item-based.",
            "Winter Wyvern starts the game with the <b>Eldwurm's Edda</b> item. After <b>10 minutes</b> it can be consumed, increasing the <b>current and maximum level of one basic ability by 1</b>.",
            "Also increases Winter Wyvern's <b>Intelligence by 25%</b> of its base value at the time of consumption.",
            "<b>Level-5 values</b> are automatically calculated by applying 50% of the difference in all values between levels 3 and 4 (except mana cost — kept the same as level 4).",
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Arctic Burn"))
W(ul_open())
W(li("No longer has a one debuff per cast restriction on enemy heroes", t("BUFF")))
W(li("Burn Duration decreased from 5s to 3s", b(5, 3)))
W(li("Movement Slow decreased from 16/24/32/40% to 15/20/25/30%", b([16, 24, 32, 40], [15, 20, 25, 30])))
W(ul_close())
W(ability("Cold Embrace"))
W(ul_open())
W(li("Aghanim's Shard reworked: Decreases cooldown by 4s. Allied units gain 60% bonus attack damage for 6s when emerging from the icy cocoon", t("REWORK")))
W(ul_close())
W(ability("Winter's Curse"))
W(ul_open())
W(li("Attack Speed rescaled from 65 to 50/65/80", b(65, [50, 65, 80])))
W(li("Maximum Duration rescaled from 4/5.5/7s to 6s", b([4, 5.5, 7], 6)))
W(li("Bonus Duration per hero decreased from 2s to 1.5s", b(2, 1.5)))
W(li("Bonus duration per hero can now be applied after the cast if an enemy hero becomes affected", t("NEW")))
W(ul_close())
W(subnote("Still can't be longer than the maximum duration"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Splinter Blast Shatter Radius decreased from +250 to +175", b(250, 175)))
W(li("Level 20 Talent Arctic Burn Slow decreased from +17% to +15%", b(17, 15)))
W(ul_close())

# Witch Doctor
W(hero_header("Witch Doctor"))
W(ability("Death Ward"))
W(ul_open())
W(li("Attack Range increased from 600 to 600/625/650", b(600, [600, 625, 650])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +2 Paralyzing Cask bounces replaced with -3s Paralyzing Cask Cooldown", t("REWORK")))
W(li("Level 20 Talent +75 Death Ward Attack Range replaced with Maledict bursts deal 75% damage in a 800 AoE (each burst sends projectiles that deal 75% of its damage at all enemy units within 800 range)", t("REWORK")))
W(li("Level 25 Talent -6s Paralyzing Cask Cooldown replaced with +6 Paralyzing Cask Bounces", t("REWORK")))
W(ul_close())

# Wraith King
W(hero_header("Wraith King"))
W(ul_open())
W(li("Base Armor decreased by 1", bstat_h("Wraith King", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Wraith King", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
W(ability("Vampiric Spirit"))
W(ul_open())
W(li("No longer levels with Reincarnation", t("REWORK")))
W(li_formula("Lifesteal changed",
             "10/20/30/40%", "14% + 1% per level",
             lambda L: 40.0, lambda L: 14.0 + 1.0 * L))
W(li_formula("Wraith Duration changed",
             "3.5/4/4.5/5s", "4.25s + 0.25s per 6 levels",
             lambda L: 5.0, lambda L: 4.25 + 0.25 * (L // 6),
             value_fmt="{:.2f}s",
             inline_note_text="Up to 5.5s at level 30. Also increased by 1s with Aghanim's Scepter."))
W(li("Bonus Attack Speed rescaled from 30/45/60/75 to 55", b([30, 45, 60, 75], 55)))
W(li("Bonus Move Speed rescaled from 10/15/20/25% to 20%", b([10, 15, 20, 25], 20)))
W(ul_close())
W(ability("Bone Guard"))
W(ul_open())
W(li("Now always a basic ability for Wraith King", t("REWORK")))
W(li("Skeleton movespeed increased from 340 to 350", b(340, 350)))
W(ul_close())
W(ability("Mortal Strike"))
W(ul_open())
W(li("Aghanim's Shard reworked: Critical strikes curse their target, dealing 75% of the damage dealt again after a 3 second delay. Vampiric Spirit's lifesteal applies to the curse damage", t("REWORK")))
W(ul_close())
W(ability("Reincarnation"))
W(ul_open())
W(li("Mana Cost decreased from 225 to 220/110/0", b(225, [220, 110, 0], l=True)))
W(li("Now spawns 2/3/4 per enemy hero within slow radius", t("NEW")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())

# Zeus
W(hero_header("Zeus"))
W(ul_open())
W(li("Base Strength increased from 19 to 21", b(19, 21)))
W(li("Base Damage increased by 1–3", bstat_h("Zeus", "AttackDamageMin", "7.40c", 1),
     extra=note_box(hero="Zeus", field="AttackDamageMin", before_patch="7.40c") + inline_note("Damage spread increased from 8 to 10 — " + b(8, 10))))
W(li("Damage at level 1 increased from 52–60 to 53–63", br(52, 60, 53, 63)))
W(li("Base Movement Speed decreased from 315 to 305", b(315, 305)))
W(li("Base Armor decreased by 1", bstat_h("Zeus", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Zeus", field="ArmorPhysical", before_patch="7.40c")))
W(ul_close())
W(ability("Static Field"))
W(ul_open())
W(li("No longer levels with Thundergod's Wrath", t("REWORK")))
W(li_formula("Damage changed",
             "2.5/3/3.5/4%", "3.45% + 0.05% per level",
             lambda L: 4.0, lambda L: 3.45 + 0.05 * L))
W(ul_close())
W(ability("Arc Lightning"))
W(ul_open())
W(li("Mana Cost rescaled from 75/85/95/105 to 85/90/95/100", b([75, 85, 95, 105], [85, 90, 95, 100], l=True)))
W(li("Base Damage increased from 90/120/150/180 to 105/130/155/180", b([90, 120, 150, 180], [105, 130, 155, 180])))
W(ul_close())
W(ability("Lightning Bolt"))
W(ul_open())
W(li("Vision and True Sight radius increased from 500 to 600", b(500, 600)))
W(ul_close())
W(ability("Thundergod's Wrath"))
W(ul_open())
W(li("Now applies the True Sight before the damage and strikes even untargetable and still invisible enemies", t("NEW")))
W(ul_close())
W(subnote("It used to simply reveal invisible heroes without dealing damage to them. Now it will work similarly to Lightning Bolt, dealing damage even to units affected by Smoke of Deceit, Dark Willow's Shadow Realm, Phantom Assassin's Blur, Slark's Shadow Dance or Depth Shroud, etc."))
W(ul_open())
W(li("Vision and True Sight radius increased from 500 to 600", b(500, 600)))
W(ul_close())
W(ability("Nimbus", slug="zuus_cloud"))
W(ul_open())
W(li("Damage source changed from Nimbus to the caster", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent -0.4s Arc Lightning Cooldown replaced with -20% Arc Lightning Mana Cost/Cooldown", t("REWORK")))
W(li("Level 25 Talent +2% Static Field Damage replaced with 3 Heavenly Jump Charges", t("REWORK")))
W(ul_close())

write_footer()
save_html('patches/7.41.html')


# ============================================================
# 7.40c content
# ============================================================
write_head("7.40c", "21.01.2026")

# ===== ITEM UPDATES =====
W(section("Item Updates"))

W(item_header("Khanda"))
W(ul_open())
W(li("Can now be disassembled", t("NEW")))
W(ul_close())

W(item_header("Phylactery"))
W(ul_open())
W(li("All Attributes bonus decreased from 7 to 6", b(7, 6)))
W(li("Mana Regen decreased from 2.5 to 2.25", b(2.5, 2.25)))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))

# Abaddon
W(hero_header("Abaddon"))
W(ability("Curse of Avernus", slug="abaddon_frostmourne"))
W(ul_open())
W(li("No longer applied by illusions", t("DEL")))
W(ul_close())

# Axe
W(hero_header("Axe"))
W(ul_open())
W(li("Strength gain decreased from 2.8 to 2.7", b(2.8, 2.7)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Battle Hunger Damage Per Second decreased from +10 to +8", b(10, 8)))
W(ul_close())

# Batrider
W(hero_header("Batrider"))
W(ul_open())
W(li("Agility gain increased from 1.8 to 2.0", b(1.8, 2.0)))
W(li("Damage gain per level increased from 3.4 to 3.5", b(3.4, 3.5)))
W(ul_close())

# Bloodseeker
W(hero_header("Bloodseeker"))
W(ability("Bloodrage"))
W(ul_open())
W(li("Max Health Damage per second decreased from 1.4% to 1.2%", b(1.4, 1.2)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Health increased from +175 to +200", b(175, 200)))
W(li("Level 20 Talent Agility decreased from +20 to +15", b(20, 15)))
W(li("Level 20 Talent Rupture Cast Range decreased from +425 to +400", b(425, 400)))
W(ul_close())

# Brewmaster
W(hero_header("Brewmaster"))
W(ability("Liquid Courage"))
W(ul_open())
W(li("Aghanim's Shard Max HP Regen per second increased from 2% to 2.5%", b(2, 2.5)))
W(ul_close())
W(ability("Drunken Brawler"))
W(ul_open())
W(li("Earth Brawler Armor increased from 2/4/6/8 to 3/5/7/9", b([2, 4, 6, 8], [3, 5, 7, 9])))
W(ul_close())

# Broodmother
W(hero_header("Broodmother"))
W(facet_header("broodmother_necrotic_webs"))
W(ul_open())
W(li("Spin Web enemy Restoration Reduction decreased from 10/30/50/70% to 10/25/40/55%", b([10, 30, 50, 70], [10, 25, 40, 55])))
W(ul_close())
W(ability("Spin Web"))
W(ul_open())
W(li("Max Charges decreased from 4/6/8/10 to 3/5/7/9", b([4, 6, 8, 10], [3, 5, 7, 9])))
W(ul_close())
W(ability("Incapacitating Bite"))
W(ul_open())
W(li("No longer applied by illusions", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +8 to +6", b(8, 6)))
W(li("Level 25 Talent BAT Reduction during Insatiable Hunger decreased from 0.2s to 0.15s", b(0.2, 0.15)))
W(ul_close())

# Clinkz
W(hero_header("Clinkz"))
W(ability("Skeleton Walk", slug="clinkz_wind_walk"))
W(ul_open())
W(li("Skeleton Building Damage penalty increased from 25% to 75%", b(25, 75, l=True),
     extra=inline_note("Also applies to Burning Army skeletons.")))
W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
W(li("Aghanim's Scepter now only provides Burning Army ability without increasing Skeleton Archer Hits to Kill by 1", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Attack Range decreased from +60 to +50", b(60, 50)))
W(li("Level 25 Talent Searing Arrows Multishot no longer applies to Skeleton Archers", t("NERF")))
W(ul_close())

# Dark Seer
W(hero_header("Dark Seer"))
W(ul_open())
W(li("Base Armor increased by 1", t("BUFF")))
W(ul_close())

# Doom
W(hero_header("Doom"))
W(ability("Infernal Blade"))
W(ul_open())
W(li("Mana Cost decreased from 40 to 35", b(40, 35, l=True)))
W(ul_close())

# Drow Ranger
W(hero_header("Drow Ranger"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Marksmanship Chance decreased from +10% to +8%", b(10, 8)))
W(ul_close())

# Earthshaker
W(hero_header("Earthshaker"))
W(ability("Fissure"))
W(ul_open())
W(li("Mana Cost decreased from 120/125/130/135 to 115/120/125/130", b([120, 125, 130, 135], [115, 120, 125, 130], l=True)))
W(ul_close())

# Ember Spirit
W(hero_header("Ember Spirit"))
W(ability("Searing Chains"))
W(ul_open())
W(li("Duration decreased from 1.5/2/2.5/3s to 1.25/1.75/2.25/2.75s", b([1.5, 2, 2.5, 3], [1.25, 1.75, 2.25, 2.75])))
W(li("Damage Per Second rescaled from 50/70/90/110 to 100", b([50, 70, 90, 110], 100)))
W(ul_close())

# Grimstroke
W(hero_header("Grimstroke"))
W(ul_open())
W(li("Base damage increased by 1", bstat_h("Grimstroke", "AttackDamageMin", "7.40b", 1), extra=note_box(hero="Grimstroke", field="AttackDamageMin", before_patch="7.40b")))
W(li("Damage at level 1 changed from 46–50 to 47–51", br(46, 50, 47, 51)))
W(ul_close())
W(ability("Ink Swell", slug="grimstroke_spirit_walk"))
W(ul_open())
W(li("Cast Range increased from 500/600/700/800 to 650/700/750/800", b([500, 600, 700, 800], [650, 700, 750, 800])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Ink Swell Movement Speed increased from +12% to +15%", b(12, 15)))
W(ul_close())

# Gyrocopter
W(hero_header("Gyrocopter"))
W(ul_open())
W(li("Base Attack Speed decreased from 125 to 115", b(125, 115)))
W(li("Agility gain increased from 3.2 to 3.4", b(3.2, 3.4)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Call Down Cooldown Reduction increased from 30s to 40s", b(30, 40)))
W(ul_close())

# Huskar
W(hero_header("Huskar"))
W(facet_header("huskar_cauterize"))
W(ul_open())
W(li("Berserker's Blood cooldown increased from 50/40/30/20s to 60/50/40/30s", b([50, 40, 30, 20], [60, 50, 40, 30], l=True)))
W(ul_close())

# Jakiro
W(hero_header("Jakiro"))
W(ul_open())
W(li("Base Intelligence decreased from 26 to 25", b(26, 25)))
W(li("Damage at level 1 decreased from 53–61 to 52–60", br(53, 61, 52, 60)))
W(ul_close())
W(ability("Ice Path"))
W(ul_open())
W(li("Path Duration decreased from 3/3.5/4/4.5s to 2.6/3.1/3.6/4.1s", b([3, 3.5, 4, 4.5], [2.6, 3.1, 3.6, 4.1])))
W(ul_close())

# Largo
W(hero_header("Largo"))
W(ul_open())
W(li("Added to Captains Mode", t("NEW")))
W(li("Intelligence gain increased from 2.4 to 2.6", b(2.4, 2.6)))
W(ul_close())
W(ability("Frogstomp"))
W(ul_open())
W(li("Damage per stomp increased from 35/45/55/65 to 36/48/60/72", b([35, 45, 55, 65], [36, 48, 60, 72])))
W(ul_close())
W(ability("Amphibian Rhapsody"))
W(ul_open())
W(li("Now can be toggled while silenced", t("MISC")))
W(li("Radius increased from 750 to 800", b(750, 800)))
W(ul_close())

# Legion Commander
W(hero_header("Legion Commander"))
W(ability("Duel"))
W(ul_open())
W(li("Aghanim's Scepter Duration decreased from 5.5/6/6.5s to 5/5.5/6s", b([5.5, 6, 6.5], [5, 5.5, 6])))
W(ul_close())

# Lone Druid
W(hero_header("Lone Druid"))
W(ul_open())
W(li("Base Agility increased from 20 to 22", b(20, 22)))
W(li("Damage at level 1 increased from 42–46 to 44–48", br(42, 46, 44, 48)))
W(ul_close())
W(ability("Savage Roar"))
W(ul_open())
W(li("Duration increased from 0.8/1.2/1.6/2s to 1.1/1.4/1.7/2s", b([0.8, 1.2, 1.6, 2], [1.1, 1.4, 1.7, 2])))
W(ul_close())
W(subnote("Same change applies to the Spirit Bear's Savage Roar"))
W(ability("Return", slug="lone_druid_spirit_bear_return"))
W(ul_open())
W(li("Roots and leashes will now interrupt Return's channeling", t("NERF"),
     extra=inline_note("Previously they only prevented casting of Return, but had no effect if applied during the channeling.")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Slow Resistance during True Form increased from 60% to 70%", b(60, 70)))
W(ul_close())

# Meepo
W(hero_header("Meepo"))
W(ability("MegaMeepo", slug="meepo_megameepo"))
W(ul_open())
W(li("Poof damage factor per additional Meepo decreased from 75% to 50%", b(75, 50)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Poof Damage decreased from +50 to +40", b(50, 40)))
W(li("Level 20 Talent Ransack Health Steal decreased from +8 to +7", b(8, 7)))
W(ul_close())

# Monkey King
W(hero_header("Monkey King"))
W(ability("Jingu Mastery"))
W(ul_open())
W(li("Bonus Damage increased from 30/75/120/165 to 30/80/130/180", b([30, 75, 120, 165], [30, 80, 130, 180])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Primal Spring Max Damage increased from +85 to +90", b(85, 90)))
W(ul_close())

# Nature's Prophet
W(hero_header("Nature's Prophet"))
W(ability("Nature's Call", slug="furion_force_of_nature"))
W(ul_open())
W(li("Treant Damage increased from 16/24/32/40 to 16/25/34/43", b([16, 24, 32, 40], [16, 25, 34, 43])))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ul_open())
W(li("Base Strength increased from 19 to 20", b(19, 20)))
W(ul_close())
W(ability("Fortune Favors the Bold"))
W(ul_open())
W(li("Chance Reduction increased from 40% to 50%", b(40, 50)))
W(ul_close())
W(ability("Swashbuckle"))
W(ul_open())
W(li("Cooldown decreased from 20/17/14/11s to 19/16/13/10s", b([20, 17, 14, 11], [19, 16, 13, 10], l=True)))
W(ul_close())

# Phantom Assassin
W(hero_header("Phantom Assassin"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Stifling Dagger Cooldown Reduction increased from 1.5s to 2s", b(1.5, 2)))
W(ul_close())

# Phantom Lancer
W(hero_header("Phantom Lancer"))
W(ability("Illusory Armaments"))
W(ul_open())
W(li("Min Damage at level 1 decreased from 18% to 17%", b(18, 17),
     extra=inline_note("Increment value per 3 level-ups is still 2%.")))
W(ul_close())
W(ability("Doppelganger", slug="phantom_lancer_doppelwalk"))
W(ul_open())
W(li("Mana Cost increased from 50 to 70", b(50, 70, l=True)))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(ability("Meat Shield", slug="pudge_flesh_heap"))
W(ul_open())
W(li("Mana Cost increased from 50/60/70/80 to 65/70/75/80", b([50, 60, 70, 80], [65, 70, 75, 80], l=True)))
W(ul_close())

# Ringmaster
W(hero_header("Ringmaster"))
W(ul_open())
W(li("Base Agility decreased from 13 to 11", b(13, 11)))
W(li("Agility gain increased from 1.4 to 1.6", b(1.4, 1.6)))
W(ul_close())
W(facet_header("ringmaster_carny_classics"))
W(ul_open())
W(li("Whoopee Cushion stink cloud radius increased from 200 to 250", b(200, 250)))
W(ul_close())

# Rubick
W(hero_header("Rubick"))
W(ability("Telekinesis"))
W(ul_open())
W(li("Cooldown decreased from 23/20/17/14s to 22/19/16/13s", b([23, 20, 17, 14], [22, 19, 16, 13], l=True)))
W(ul_close())

# Shadow Demon
W(hero_header("Shadow Demon"))
W(facet_header("shadow_demon_promulgate"))
W(ul_open())
W(li("Disseminate health loss decreased from 9/11/13/15% to 9/10/11/12%", b([9, 11, 13, 15], [9, 10, 11, 12], l=True)))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ul_open())
W(li("Strength gain decreased from 3.6 to 3.4", b(3.6, 3.4)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Health decreased from +300 to +250", b(300, 250)))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(ability("Saltwater Shiv"))
W(ul_open())
W(li("Stack Restoration Steal rescaled from 3/4/5/6% to 2/4/6/8%", b([3, 4, 5, 6], [2, 4, 6, 8])))
W(li("Stack Regen Steal increased from 2/3/4/5 to 2/4/6/8", b([2, 3, 4, 5], [2, 4, 6, 8])))
W(li("Stack Speed Steal increased from 2/3/4/5 to 2/4/6/8", b([2, 3, 4, 5], [2, 4, 6, 8])))
W(ul_close())

# Spectre
W(hero_header("Spectre"))
W(ul_open())
W(li("Strength gain decreased from 2.5 to 2.4", b(2.5, 2.4)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Health decreased from +350 to +325", b(350, 325)))
W(li("Level 25 Talent All Spectre Illusion Damage decreased from +20% to +15%", b(20, 15)))
W(ul_close())

# Terrorblade
W(hero_header("Terrorblade"))
W(ability("Conjure Image"))
W(ul_open())
W(li("Mana Cost decreased from 55/65/75/85 to 50/60/70/80", b([55, 65, 75, 85], [50, 60, 70, 80], l=True)))
W(ul_close())
W(ability("Sunder"))
W(ul_open())
W(li("Cooldown decreased from 120/80/40s to 110/75/40s", b([120, 80, 40], [110, 75, 40], l=True)))
W(ul_close())
W(ability("Demon Zeal"))
W(ul_open())
W(li("No longer affects Reflection illusions", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Reflection Slow/Damage increased from +10% to +15%", b(10, 15)))
W(ul_close())

# Tidehunter
W(hero_header("Tidehunter"))
W(ul_open())
W(li("Base Strength decreased from 27 to 26", b(27, 26)))
W(li("Damage at level 1 decreased from 52–58 to 51–57", br(52, 58, 51, 57)))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ul_open())
W(li("Base Strength decreased from 26 to 23", b(26, 23)))
W(li("Strength gain increased from 3.5 to 3.6", b(3.5, 3.6)))
W(li("Damage at level 1 decreased from 49–53 to 46–50", br(49, 53, 46, 50)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Whirling Death Stat Loss decreased from +2.5% to +2%", b(2.5, 2)))
W(ul_close())

# Treant Protector
W(hero_header("Treant Protector"))
W(ability("Eyes In The Forest"))
W(ul_open())
W(li("Eyes now have a 50g bounty when killed", t("NERF")))
W(ul_close())

# Ursa
W(hero_header("Ursa"))
W(ability("Fury Swipes"))
W(ul_open())
W(li("Damage per attack decreased from 13/21/29/37 to 12/20/28/36", b([13, 21, 29, 37], [12, 20, 28, 36])))
W(ul_close())

# Viper
W(hero_header("Viper"))
W(ability("Corrosive Skin"))
W(ul_open())
W(li("Damage per second rescaled from 8/16/24/32 to 10/15/20/25", b([8, 16, 24, 32], [10, 15, 20, 25])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Predator Damage Per Missing Health increased from +0.25 to +0.3", b(0.25, 0.3)))
W(li("Level 20 Talent Viper Strike DPS decreased from +80 to +70", b(80, 70)))
W(ul_close())

write_footer()
save_html('patches/7.40c.html')


# ============================================================
# 7.40b content
# ============================================================
write_head("7.40b", "23.12.2025")

# ===== ITEM UPDATES =====
W(section("Item Updates"))

W(item_header("Mask of Madness"))
W(ul_open())
W(li("Berserk now shows the overhead \"Silenced\" text when active", t("QoL")))
W(ul_close())

W(item_header("Silver Edge"))
W(ul_open())
W(li("Shadow Walk debuff duration decreased from 6s to 5s", b(6, 5)))
W(ul_close())

W(item_header("Spirit Vessel"))
W(ul_open())
W(li("Soul Release will gain charges only for Spirit Vessel if the same hero has both Spirit Vessel and Urn of Shadows", t("MISC")))
W(ul_close())

W(item_header("Urn of Shadows"))
W(ul_open())
W(li("Soul Release can no longer gain charges on multiple copies of this item if the copies are on the same hero", t("MISC")))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))

# Abaddon
W(hero_header("Abaddon"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Aphotic Shield HP Regen decreased from +10 to +8", b(10, 8)))
W(ul_close())

# Axe
W(hero_header("Axe"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Battle Hunger Damage Per Second decreased from +12 to +10", b(12, 10)))
W(ul_close())

# Batrider
W(hero_header("Batrider"))
W(ability("Flamebreak", slug="batrider_flamebreak"))
W(ul_open())
W(li("Mana Cost decreased from 110/115/120/125 to 110", b([110, 115, 120, 125], 110, l=True)))
W(ul_close())

# Beastmaster
W(hero_header("Beastmaster"))
W(ul_open())
W(li("Agility gain increased from 1.9 to 2.0", b(1.9, 2)))
W(li("Damage gain per level increased from 3.0 to 3.1", b(3, 3.1)))
W(ul_close())
W(ability("Wild Axes", slug="beastmaster_wild_axes"))
W(ul_open())
W(li("Damage Amp per stack increased from 6/8/10/12% to 7/9/11/13%", b([6, 8, 10, 12], [7, 9, 11, 13])))
W(ul_close())

# Brewmaster
W(hero_header("Brewmaster"))
W(ul_open())
W(li("Base Strength increased from 23 to 24", b(23, 24)))
W(li("Damage at level 1 increased from 52–59 to 53–60", br(52, 59, 53, 60)))
W(ul_close())
W(ability("Liquid Courage", slug="brewmaster_liquid_courage"))
W(ul_open())
W(li("Max Speed Increase increased from 25% to 30%", b(25, 30)))
W(ul_close())
W(ability("Thunder Clap", slug="brewmaster_thunder_clap"))
W(ul_open())
W(li("Radius increased from 375 to 400", b(375, 400)))
W(ul_close())
W(ability("Drunken Brawler", slug="brewmaster_drunken_brawler"))
W(ul_open())
W(li("Brewed Up extend duration increased from 1s to 2s", b(1, 2)))
W(li("Toggling is no longer disabled by silence", t("MISC")))
W(ul_close())
W(ability("Primal Split", slug="brewmaster_primal_split"))
W(ul_open())
W(li("Earth Brewling's Earth Element now also provides 80% Slow Resistance", t("NEW")))
W(ul_close())

# Bristleback
W(hero_header("Bristleback"))
W(ability("Viscous Nasal Goo", slug="bristleback_viscous_nasal_goo"))
W(ul_open())
W(li("Base Movement Slow increased from 10% to 12%", b(10, 12)))
W(ul_close())

# Broodmother
W(hero_header("Broodmother"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +10 to +8", b(10, 8)))
W(li("Level 20 Talent Incapacitating Bite Slow/Miss Chance decreased from +25% to +20%", b(25, 20)))
W(li("Level 25 Talent Spin Web Move Speed decreased from +14% to +7%", b(14, 7)))
W(li("Level 25 Talent BAT Reduction During Insatiable Hunger decreased from 0.25s to 0.2s", b(0.25, 0.2)))
W(ul_close())

# Centaur Warrunner
W(hero_header("Centaur Warrunner"))
W(ul_open())
W(li("Base Movement Speed decreased from 305 to 300", b(305, 300)))
W(ul_close())
W(ability("Work Horse", slug="centaur_work_horse"))
W(ul_open())
W(li("Total Duration decreased from 7s to 6s", b(7, 6)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Strength decreased from +12 to +10", b(12, 10)))
W(ul_close())

# Clinkz
W(hero_header("Clinkz"))
W(ul_open())
W(li("Base Strength increased from 17 to 18", b(17, 18)))
W(ul_close())
W(ability("Infernal Shred", slug="clinkz_infernal_shred"))
W(ul_open())
W(li("Debuff per Clinkz' attack increased from 2% to 3%", b(2, 3)))
W(ul_close())
W(ability("Strafe", slug="clinkz_strafe"))
W(ul_open())
W(li("Now also applies to skeletons that were created after the cast", t("NEW")))
W(li("Attack Speed Bonus increased from 100/140/180/220 to 120/160/200/240", b([100, 140, 180, 220], [120, 160, 200, 240])))
W(ul_close())
W(ability("Searing Arrows", slug="clinkz_searing_arrows"))
W(ul_open())
W(li("Bonus Damage increased from 18/32/46/60 to 20/35/50/65", b([18, 32, 46, 60], [20, 35, 50, 65])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +1 Death Pact Charge replaced with -10s Death Pact Charge Restore Time", t("REWORK")))
W(ul_close())

# Dazzle
W(hero_header("Dazzle"))
W(ability("Poison Touch", slug="dazzle_poison_touch"))
W(ul_open())
W(li("Slow decreased from 16/18/20/22% to 13/16/19/22%", b([16, 18, 20, 22], [13, 16, 19, 22])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Shallow Grave Cooldown Reduction decreased from 4s to 3s", b(4, 3, l=True)))
W(ul_close())

# Death Prophet
W(hero_header("Death Prophet"))
W(ability("Exorcism", slug="death_prophet_exorcism"))
W(ul_open())
W(li("Spirits increased from 10/17/24 to 10/18/26", b([10, 17, 24], [10, 18, 26])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Spirit Siphon Damage/Heal increased from +25 to +30", b(25, 30)))
W(ul_close())

# Doom
W(hero_header("Doom"))
W(ul_open())
W(li("Strength gain increased from 3.5 to 3.6", b(3.5, 3.6)))
W(ul_close())

# Drow Ranger
W(hero_header("Drow Ranger"))
W(ul_open())
W(li("Agility gain decreased from 2.9 to 2.8", b(2.9, 2.8)))
W(ul_close())
W(facet_header("drow_ranger_sidestep"))
W(ul_open())
W(li("Multishot movement speed penalty increased from 25% to 35%", b(25, 35, l=True)))
W(ul_close())
W(ability("Glacier", slug="drow_ranger_glacier"))
W(ul_open())
W(li("Cooldown increased from 20s to 25s", b(20, 25, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Frost Arrows Mana Cost Reduction decreased from 25% to 18%", b(25, 18, l=True)))
W(ul_close())

# Enigma
W(hero_header("Enigma"))
W(ability("Black Hole", slug="enigma_black_hole"))
W(ul_open())
W(li("Aghanim's Scepter Pull AoE decreased from 1200 to 1000", b(1200, 1000)))
W(ul_close())

# Faceless Void
W(hero_header("Faceless Void"))
W(ul_open())
W(li("Base Damage decreased by 3", t("MISC")))
W(li("Base Agility increased from 21 to 24", b(21, 24), extra=inline_note("Damage at level 1 unchanged (58–64)")))
W(ul_close())

# Huskar
W(hero_header("Huskar"))
W(facet_header("huskar_cauterize"))
W(ul_open())
W(li("Berserker's Blood max HP heal per debuff decreased from 5% to 4%", b(5, 4)))
W(ul_close())
W(ability("Berserker's Blood", slug="huskar_berserkers_blood"))
W(ul_open())
W(li("HP for Max bonus decreased from 12% to 10%", b(12, 10)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Lifesteal decreased from +15% to +12%", b(15, 12)))
W(li("Level 25 Talent Life Break Damage decreased from +25% to +22%", b(25, 22)))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(facet_header("invoker_wex_focus"))
W(ul_open())
_twister_old = [3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0]
_twister_new = [2.7, 2.9, 3.1, 3.3, 3.5, 3.7, 3.9, 4.1, 4.3, 4.5]
W(li_formula(
    "Tornado Aghanim's Scepter Twister Duration decreased by 0.5s",
    "3.2-5.0s", "2.7-4.5s",
    lambda L, o=_twister_old: o[L - 1],
    lambda L, n=_twister_new: n[L - 1],
    levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    level_prefix='W',
    rework_badge=False,
    value_fmt="{:.1f}s",
))
W(li("E.M.P. Aghanim's Shard burn damage decreased from 90% to 80%", b(90, 80)))
W(ul_close())

# Jakiro
W(hero_header("Jakiro"))
W(ability("Liquid Fire", slug="jakiro_liquid_fire"))
W(ul_open())
W(li("Burn Damage decreased from 20/30/40/50 to 15/25/35/45", b([20, 30, 40, 50], [15, 25, 35, 45])))
W(ul_close())
W(ability("Liquid Frost", slug="jakiro_liquid_ice"))
W(ul_open())
W(li("Impact Damage rescaled from 15/20/25/30 to 8/16/24/32", b([15, 20, 25, 30], [8, 16, 24, 32])))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
W(ability("Healing Ward", slug="juggernaut_healing_ward"))
W(ul_open())
W(li("Duration decreased from 25s to 18/20/22/24s", b(25, [18, 20, 22, 24])))
W(ul_close())
W(ability("Omnislash", slug="juggernaut_omni_slash"))
W(ul_open())
W(li("Slashes Rate Multiplier decreased from 1.5 to 1.4", b(1.5, 1.4, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Blade Dance Lifesteal decreased from +50% to +40%", b(50, 40)))
W(ul_close())

# Kez
W(hero_header("Kez"))
W(ability("Switch Discipline", slug="kez_switch_weapons"))
W(ul_open())
W(li("Katana Base Attack Time worsened from 1.8s to 1.9s", b(1.8, 1.9, l=True)))
W(li("Katana Bonus Agility Base Damage increased from 12% to 16%", b(12, 16)))
W(li("Can no longer be disabled by Silence", t("MISC")))
W(ul_close())
W(ability("Falcon Rush", slug="kez_falcon_rush"))
W(ul_open())
W(li("Can no longer rush towards buildings or trigger on them", t("DEL")))
W(li("Echo Attack Damage decreased from 35/40/45/50% to 30/35/40/45%", b([35, 40, 45, 50], [30, 35, 40, 45])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Attack Speed During Falcon Rush decreased from +60 to +40", b(60, 40)))
W(ul_close())

# Kunkka
W(hero_header("Kunkka"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Tidebringer Cleave Damage increased from +120% to +130%", b(120, 130)))
W(ul_close())

# Largo
W(hero_header("Largo"))
W(ability("Catchy Lick", slug="largo_catchy_lick"))
W(ul_open())
W(li("Enemy Pull Distance increased from 210/240/270/300 to 235/265/295/325", b([210, 240, 270, 300], [235, 265, 295, 325])))
W(li("Bonus Health Regen increased from 4/6/8/10 to 4/7/10/13", b([4, 6, 8, 10], [4, 7, 10, 13])))
W(ul_close())
W(ability("Croak of Genius", slug="largo_croak_of_genius"))
W(ul_open())
W(li("Reverberated damage is now only applied if the target is within 2000 range of the caster", t("REWORK")))
W(li("Duration is no longer decreased on Largo from his own abilities", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Catchy Lick Damage increased from +140 to +170", b(140, 170)))
W(ul_close())

# Legion Commander
W(hero_header("Legion Commander"))
W(facet_header("legion_commander_spoils_of_war"))
W(ul_open())
W(li("Press the Attack duration on allies after Duel win decreased from 50% to 25%", b(50, 25),
     extra=inline_note("From 2.5s to 1.25s")))
W(ul_close())
W(ability("Press The Attack", slug="legion_commander_press_the_attack"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 90", b(100, 90, l=True)))
W(li("Bonus Move Speed increased from 10/14/18/22% to 13/16/19/22%", b([10, 14, 18, 22], [13, 16, 19, 22])))
W(ul_close())
W(ability("Duel", slug="legion_commander_duel"))
W(ul_open())
W(li("Aghanim's Scepter duration bonus decreased from +2s to +1.5s", b(2, 1.5),
     extra=inline_note("Total Duration decreased from 6/6.5/7s to 5.5/6/6.5s")))
W(ul_close())

# Lich
W(hero_header("Lich"))
W(ul_open())
W(li("Agility gain decreased from 2.0 to 1.7", b(2, 1.7)))
W(ul_close())

# Lone Druid
W(hero_header("Lone Druid"))
W(ul_open())
W(li("Base Strength increased from 18 to 20", b(18, 20)))
W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
W(ul_close())
W(ability("Entangle", slug="lone_druid_entangle"))
W(ul_open())
W(li("Root Damage per second increased from 60/70/80/90 to 90", b([60, 70, 80, 90], 90)))
W(li("Cooldown decreased from 24/22/20/18s to 20/19/18/17s", b([24, 22, 20, 18], [20, 19, 18, 17], l=True)))
W(ul_close())
W(ability("Savage Roar", slug="lone_druid_savage_roar"))
W(ul_open())
W(li("Cooldown decreased from 38/32/26/20s to 29/26/23/20s", b([38, 32, 26, 20], [29, 26, 23, 20], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Entangle Root Damage Per Second increased from +15 to +20", b(15, 20)))
W(ul_close())
# Spirit Bear (Lone Druid pet — unit, not a hero). Placed inside LD's
# section, mirroring 7.41c convention. Gold + Experience bounty share
# the same formula change, so they merge into one combined row.
W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
W(ul_open())
W(li_formula("Gold/Experience Bounty changed",
             "300", "175 + 8 per Spirit Bear level up",
             lambda L: 300, lambda L: 175 + 8 * L,
             levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30],
             l=True,
             rework_badge=False))
W(ul_close())
W(ability("Entangling Claws", slug="lone_druid_spirit_bear_entangle"))
W(ul_open())
W(li("Root Damage per second increased from 60/70/80/90 to 90", b([60, 70, 80, 90], 90)))
W(ul_close())

# Marci
W(hero_header("Marci"))
W(ul_open())
W(li("Strength gain increased from 3.0 to 3.2", b(3, 3.2)))
W(li("Damage gain per level increased from 3.2 to 3.3", b(3.2, 3.3)))
W(ul_close())
W(ability("Rebound", slug="marci_companion_run"))
W(ul_open())
W(li("Radius increased from 275 to 300", b(275, 300)))
W(ul_close())
W(ability("Unleash", slug="marci_unleash"))
W(ul_open())
W(li("Cooldown decreased from 90/75/60s to 80/70/60s", b([90, 75, 60], [80, 70, 60], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +75 Rebound Landing Radius decreased to +50", t("NERF")))
W(ul_close())

# Mars
W(hero_header("Mars"))
W(ul_open())
W(li("Base Agility decreased from 20 to 18", b(20, 18)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent God's Rebuke Cooldown Reduction increased from 2s to 2.5s", b(2, 2.5, l=True)))
W(li("Level 20 Talent Spear of Mars Stun increased from +0.4 to +0.5s", b(0.4, 0.5)))
W(ul_close())

# Meepo
W(hero_header("Meepo"))
W(ability("Dig", slug="meepo_petrify"))
W(ul_open())
W(li("Now has a 0.3s cast point", t("NEW")))
W(ul_close())
W(ability("MegaMeepo", slug="meepo_megameepo"))
W(ul_open())
W(li("Poof damage factor per additional Meepo decreased from 100% to 75%", b(100, 75)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Poof Cast Duration Reduction decreased from 1s to 0.75s", b(1, 0.75)))
W(ul_close())

# Monkey King
W(hero_header("Monkey King"))
W(ability("Wukong's Command", slug="monkey_king_wukongs_command"))
W(ul_open())
W(li("Duration increased from 13s to 14s", b(13, 14)))
W(li("Aghanim's Scepter Soldier Duration increased from 12s to 15s", b(12, 15)))
W(ul_close())

# Morphling
W(hero_header("Morphling"))
W(ul_open())
W(li("Base armor increased by 1", t("BUFF")))
W(ul_close())

# Muerta
W(hero_header("Muerta"))
W(ability("Gunslinger", slug="muerta_gunslinger"))
W(ul_open())
W(li("Toggling is no longer disabled by silence", t("MISC")))
W(ul_close())

# Necrophos
W(hero_header("Necrophos"))
W(ability("Ghost Shroud", slug="necrolyte_ghost_shroud"))
W(ul_open())
W(li("Restoration Amplification rescaled from 45/55/65/75% to 55/60/65/70%", b([45, 55, 65, 75], [55, 60, 65, 70])))
W(ul_close())

# Omniknight
W(hero_header("Omniknight"))
W(ability("Repel", slug="omniknight_martyr"))
W(ul_open())
W(li("Bonus Strength decreased from 7/14/21/28 to 6/12/18/24", b([7, 14, 21, 28], [6, 12, 18, 24])))
W(ul_close())

# Outworld Destroyer
W(hero_header("Outworld Destroyer"))
W(ability("Sanity's Eclipse", slug="obsidian_destroyer_sanity_eclipse"))
W(ul_open())
W(li("No longer deals bonus damage to illusions", t("DEL")))
W(ul_close())
W(ability("Essence Flux", slug="obsidian_destroyer_equilibrium", innate=False))
W(ul_open())
W(li("Aghanim's Scepter barrier duration decreased from 15s to 12s", b(15, 12)))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ul_open())
W(li("Intelligence gain increased from 2.2 to 2.5", b(2.2, 2.5)))
W(li("Damage gain per level increased from 3.6 to 3.8", b(3.6, 3.8)))
W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
W(ul_close())
W(ability("Swashbuckle", slug="pangolier_swashbuckle"))
W(ul_open())
W(li("Cast Range and Dash Range increased from 400/500/600/700 to 575/650/725/800", b([400, 500, 600, 700], [575, 650, 725, 800])))
W(li("Slash Range increased from 700 to 850", b(700, 850)))
W(li("Damage per Strike increased from 30/60/90/120 to 35/65/95/125", b([30, 60, 90, 120], [35, 65, 95, 125])))
W(ul_close())
W(ability("Shield Crash", slug="pangolier_shield_crash"))
W(ul_open())
W(li("Cooldown decreased from 16/13/10/7s to 15/12/9/6s", b([16, 13, 10, 7], [15, 12, 9, 6], l=True)))
W(ul_close())
W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
W(ul_open())
W(li("Duration increased from 9/10/11s to 10/11/12s", b([9, 10, 11], [10, 11, 12])))
W(li("Damage increased from 75/150/225 to 100/200/300", b([75, 150, 225], [100, 200, 300])))
W(li("Magic Resistance increased from 60% to 80%", b(60, 80)))
W(ul_close())
W(ability("Roll Up", slug="pangolier_rollup"))
W(ul_open())
W(li("Magic Resistance increased from 60% to 80%", b(60, 80)))
W(ul_close())

# Phantom Assassin
W(hero_header("Phantom Assassin"))
W(ability("Fan of Knives", slug="phantom_assassin_fan_of_knives"))
W(ul_open())
W(li("Now pierces Debuff Immunity", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Phantom Strike Duration increased from +0.5s to +0.6s", b(0.5, 0.6)))
W(ul_close())

# Phantom Lancer
W(hero_header("Phantom Lancer"))
W(ability("Spirit Lance", slug="phantom_lancer_spirit_lance"))
W(ul_open())
W(li("Damage increased from 70/140/210/280 to 100/160/220/280", b([70, 140, 210, 280], [100, 160, 220, 280])))
W(ul_close())
W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
W(ul_open())
W(li("Toggling is no longer disabled by silence", t("MISC")))
W(ul_close())

# Primal Beast
W(hero_header("Primal Beast"))
W(ability("Onslaught", slug="primal_beast_onslaught"))
W(ul_open())
W(li("Stun Duration rescaled from 0.8/1/1.2/1.4s to 0.7/1/1.3/1.6s", b([0.8, 1, 1.2, 1.4], [0.7, 1, 1.3, 1.6])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Basic Self-Dispel on Uproar Cast replaced with +6 Uproar Armor Per Stack", t("REWORK")))
W(li("Level 20 Talent +7 Uproar Armor Per Stack replaced with Basic Self-Dispel on Uproar Cast", t("REWORK")))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(facet_header("pudge_fresh_meat"))
W(ul_open())
W(li("Dismember strength increase decreased from 2/4/6 to 2/3/4", b([2, 4, 6], [2, 3, 4])))
W(ul_close())
W(ability("Meat Hook", slug="pudge_meat_hook"))
W(ul_open())
W(li("Mana Cost increased from 110 to 120", b(110, 120, l=True)))
W(ul_close())

# Pugna
W(hero_header("Pugna"))
W(ability("Life Drain", slug="pugna_life_drain"))
W(ul_open())
W(li("Mana Cost increased from 100/150/200 to 115/160/205", b([100, 150, 200], [115, 160, 205], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Health decreased from +300 to +250", b(300, 250)))
W(ul_close())

# Riki
W(hero_header("Riki"))
W(ability("Tricks of the Trade", slug="riki_tricks_of_the_trade"))
W(ul_open())
W(li("Attack Damage rescaled from 30/50/70/90 to 25/50/75/100", b([30, 50, 70, 90], [25, 50, 75, 100])))
W(ul_close())

# Ringmaster
W(hero_header("Ringmaster"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Impalement Arts Impact Damage increased from +75 to +85", b(75, 85)))
W(ul_close())

# Shadow Demon
W(hero_header("Shadow Demon"))
W(ability("Disseminate", slug="shadow_demon_disseminate"))
W(ul_open())
W(li("Cast Range decreased from 700/800/900/1000 to 700/775/850/925", b([700, 800, 900, 1000], [700, 775, 850, 925])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Strength decreased from +10 to +8", b(10, 8)))
W(ul_close())

# Shadow Fiend
W(hero_header("Shadow Fiend"))
W(ability("Necromastery", slug="nevermore_necromastery"))
W(ul_open())
W(li("Base Max Souls increased from 20 to 20/22/24/26", b(20, [20, 22, 24, 26])))
W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
W(ul_close())
W(ability("Requiem of Souls", slug="nevermore_requiem"))
W(ul_open())
W(li("Magic Resist Reduction rescaled from 5/10/15% to 10%", b([5, 10, 15], 10)))
W(ul_close())

# Silencer
W(hero_header("Silencer"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Attack Speed increased from +20 to +25", b(20, 25)))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(ability("Saltwater Shiv", slug="slark_saltwater_shiv"))
W(ul_open())
W(li("Duration increased from 6/8/10/12s to 12s", b([6, 8, 10, 12], 12)))
W(li("Stack Regen Steal rescaled from 3 to 2/3/4/5", b(3, [2, 3, 4, 5])))
W(li("Stack Speed Steal rescaled from 3 to 2/3/4/5", b(3, [2, 3, 4, 5])))
W(ul_close())

# Spectre
W(hero_header("Spectre"))
W(ul_open())
W(li("Base Agility increased from 25 to 26", b(25, 26)))
W(li("Damage at level 1 increased from 48–52 to 49–53", br(48, 52, 49, 53)))
W(li("Agility gain increased from 2.1 to 2.4", b(2.1, 2.4)))
W(ul_close())
W(ability("Shadow Step", slug="spectre_shadow_step"))
W(ul_open())
W(li("Cooldown decreased from 32/28/24/20s to 30/26/22/18s", b([32, 28, 24, 20], [30, 26, 22, 18], l=True)))
W(li("Cast Range increased from 700/850/1000/1150 to 750/900/1050/1200", b([700, 850, 1000, 1150], [750, 900, 1050, 1200])))
W(li("Illusion Damage increased from 20/30/40/50% to 32/38/44/50%", b([20, 30, 40, 50], [32, 38, 44, 50])))
W(ul_close())
W(ability("Dispersion", slug="spectre_dispersion"))
W(ul_open())
W(li("Damage Reflected increased from 7/11/15/19% to 8/12/16/20%", b([7, 11, 15, 19], [8, 12, 16, 20])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Desolate Damage increased from +10 to +12", b(10, 12)))
W(ul_close())

# Techies
W(hero_header("Techies"))
W(ability("Proximity Mines", slug="techies_land_mines"))
W(ul_open())
W(li("Cast range increased from 400 to 450", b(400, 450)))
W(ul_close())

# Terrorblade
W(hero_header("Terrorblade"))
W(ul_open())
W(li("Base agility increased from 22 to 23", b(22, 23)))
W(li("Damage at level 1 increased from 48–54 to 49–55", br(48, 54, 49, 55)))
W(ul_close())
W(ability("Metamorphosis", slug="terrorblade_metamorphosis"))
W(ul_open())
W(li("Cooldown decreased from 155/150/145/140s to 145/140/135/130s", b([155, 150, 145, 140], [145, 140, 135, 130], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Metamorphosis Cooldown Reduction decreased from 20s to 10s", b(20, 10, l=True)))
W(ul_close())

# Tidehunter
W(hero_header("Tidehunter"))
W(ability("Dead in the Water", slug="tidehunter_dead_in_the_water"))
W(ul_open())
W(li("No longer deals 100 damage", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Anchor Smash Damage Reduction decreased from +20% to +10%", b(20, 10)))
W(li("Level 20 Talent Blubber effect triggers Anchor Smash now deals 50% less damage on the triggered Anchor Smash and is now considered reflection damage", t("NERF")))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ability("Whirling Death", slug="shredder_whirling_death"))
W(ul_open())
W(li("Stat Loss Duration decreased from 12/13/14/15s to 11/12/13/14s", b([12, 13, 14, 15], [11, 12, 13, 14])))
W(li("Base Damage decreased from 85/130/175/220 to 75/120/165/210", b([85, 130, 175, 220], [75, 120, 165, 210])))
W(ul_close())
W(ability("Reactive Armor", slug="shredder_reactive_armor"))
W(ul_open())
W(li("Aghanim's Scepter effect radius decreased from 600 to 450", b(600, 450)))
W(ul_close())

# Tinker
W(hero_header("Tinker"))
W(ability("Laser", slug="tinker_laser"))
W(ul_open())
W(li("Now shows the overhead \"Blinded\" text over affected units", t("QoL")))
W(ul_close())

# Tiny
W(hero_header("Tiny"))
W(ability("Tree Grab", slug="tiny_tree_grab"))
W(ul_open())
W(li("Splash Damage increased from 55/70/85/100% to 70/80/90/100%", b([55, 70, 85, 100], [70, 80, 90, 100])))
W(ul_close())

# Treant Protector
W(hero_header("Treant Protector"))
W(ul_open())
W(li("Base Armor increased by 1", t("BUFF")))
W(ul_close())
W(ability("Nature's Guise", slug="treant_natures_guise"))
W(ul_open())
W(li_formula("Cooldown decreased",
             "50s − 3s per 2 level ups", "35s − 1s per level up",
             lambda L: 50 - 3 * ((L - 1) // 2), lambda L: 35 - (L - 1), l=True,
             value_fmt="{:g}s"))
W(ul_close())
W(ability("Living Armor", slug="treant_living_armor"))
W(ul_open())
W(li("Damage Blocked increased from 100 to 120", b(100, 120)))
W(li("Cooldown decreased from 30/25/20/15s to 24/21/18/15s", b([30, 25, 20, 15], [24, 21, 18, 15], l=True)))
W(ul_close())
W(ability("Overgrowth", slug="treant_overgrowth"))
W(ul_open())
W(li("Aghanim's Scepter Cooldown increased from 80/70/60s to 85/75/65s", b([80, 70, 60], [85, 75, 65], l=True)))
W(ul_close())

# Troll Warlord
W(hero_header("Troll Warlord"))
W(ability("Battle Stance", slug="troll_warlord_switch_stance"))
W(ul_open())
W(li("Toggling is no longer disabled by silence", t("MISC")))
W(ul_close())

# Underlord
W(hero_header("Underlord"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Firestorm Cooldown Reduction increased from 3s to 4s", b(3, 4, l=True)))
W(ul_close())

# Ursa
W(hero_header("Ursa"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +5 Fury Swipes Damage replaced with +0.5% Maul Health as Damage", t("REWORK")))
W(li("Level 20 Talent +0.5% Maul Health as Damage replaced with +6 Fury Swipes Damage", t("REWORK")))
W(li("Level 20 Talent Earthshock Radius decreased from +400 to +300", b(400, 300)))
W(ul_close())

# Viper
W(hero_header("Viper"))
W(facet_header("viper_caustic_bath"))
W(ul_open())
W(li("Corrosive Skin max bonus effect decreased from 100% to 75%", b(100, 75)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +20 Corrosive Skin Damage Per Second replaced with +10% Poison Attack Slow/Damage", t("REWORK")))
W(li("Level 15 Talent +15% Poison Attack Slow/Damage replaced with +20 Corrosive Skin Damage Per Second", t("REWORK")))
W(li("Level 15 Talent Nethertoxin Min/Max Damage decreased from +40 to +30", b(40, 30)))
W(ul_close())

# Void Spirit
W(hero_header("Void Spirit"))
W(ability("Aether Remnant", slug="void_spirit_aether_remnant"))
W(ul_open())
W(li("Remnant Lifetime decreased from 20s to 17s", b(20, 17)))
W(ul_close())

# Warlock
W(hero_header("Warlock"))
W(ability("Eldritch Summoning", slug="warlock_eldritch_summoning"))
W(ul_open())
W(li("Imp explosion damage decreased from 25/70/115/160/205 to 20/65/110/155/200", b([25, 70, 115, 160, 205], [20, 65, 110, 155, 200])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Upheaval Damage increased from +40 to +45", b(40, 45)))
W(li("Level 25 Talent Fatal Bonds Targets increased from +3 to +4", b(3, 4)))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(facet_header("windrunner_tangled"))
W(ul_open())
W(li("Shackleshot bonus damage per hero decreased from 40 to 35", b(40, 35)))
W(ul_close())
W(ability("Powershot", slug="windrunner_powershot"))
W(ul_open())
W(li("Slow duration decreased from 4s to 3s", b(4, 3)))
W(ul_close())
W(ability("Windrun", slug="windrunner_windrun"))
W(ul_open())
W(li("Aghanim's Scepter physical damage reduction decreased from 45% to 35%", b(45, 35)))
W(ul_close())

# Winter Wyvern
W(hero_header("Winter Wyvern"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent HP/s Cold Embrace Heal decreased from +25 to +20", b(25, 20)))
W(li("Level 15 Talent Splinter Blast Shatter Radius decreased from +300 to +250", b(300, 250)))
W(li("Level 25 Talent Splinter Blast Stun Duration decreased from +1.25s to +1s", b(1.25, 1)))
W(ul_close())

# Witch Doctor
W(hero_header("Witch Doctor"))
W(facet_header("witch_doctor_cleft_death"))
W(ul_open())
W(li("Death Ward damage decreased from 55/90/125 to 55/85/115", b([55, 90, 125], [55, 85, 115])))
W(ul_close())
W(ability("Death Ward", slug="witch_doctor_death_ward"))
W(ul_open())
W(li("Damage decreased from 60/95/130 to 60/90/120", b([60, 95, 130], [60, 90, 120])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Death Ward Damage decreased from +45 to +40", b(45, 40)))
W(ul_close())

# Wraith King
W(hero_header("Wraith King"))
W(facet_header("skeleton_king_facet_bone_guard"))
W(ul_open())
W(li("Bone Guard skeleton movement speed decreased from 350 to 340", b(350, 340)))
W(ul_close())

# Zeus
W(hero_header("Zeus"))
W(ability("Static Field", slug="zuus_static_field"))
W(ul_open())
W(li("Current HP Damage increased from 2.5/3/3.5/4% to 2.5/3.25/4/4.75%", b([2.5, 3, 3.5, 4], [2.5, 3.25, 4, 4.75])))
W(ul_close())

write_footer()
save_html('patches/7.40b.html')




# ============================================================
# 7.40 content (regenerated by generate_patch_code_v2.py)
# ============================================================
write_head("7.40", "15.12.2025")

# ===== GENERAL UPDATES =====
W(section("General Updates"))

# ---- Captains Mode ----
W(plain_header("Captains Mode"))
W(ul_open())
W(li("Changed order of the first and the third ban phases", t("REWORK")))
W(ul_close())
# Full Captains Mode draft (24 steps), Old over New, rendered as a token board
# (see cm_draft / docs/captains-mode.md). Structure Ban7-Pick2-Ban3-Pick6-Ban4-Pick2
# (esports.gg/gosugamers, 7.34). Only the 1st + 3rd ban phases changed in 7.40;
# bans 3-2-2 / 4-1-2 first/second-pick team, picks alternate 1-3-1.
# F/S = ban by first/second-pick team; f/s = pick by first/second-pick team.
W(cm_draft(
    ("Ban 1",  "FSSFSSF", "FFSSFSS"),   # CHANGED in 7.40
    ("Pick 1", "fs",      "fs"),
    ("Ban 2",  "FFS",     "FFS"),
    ("Pick 2", "sffssf",  "sffssf"),     # snake: 2nd,1st,1st,2nd,2nd,1st pick team
    ("Ban 3",  "FSSF",    "FSFS"),       # CHANGED in 7.40
    ("Pick 3", "fs",      "fs"),
))

W(plain_header("General Changes"))
# One ul so the tag-order sorter ranks across all three (NEW → NEW → REWORK);
# they were split across two uls before, which left REWORK between the two NEWs.
W(ul_open())
W(li("All Facets that used to have 6 All Attributes bonuses now have 7 bonuses again " + info_tip(
        "Batrider's Arsonist", "Magnus' Diminishing Return", "Meepo's More Meepo",
        "Monkey King's Simian Stride", "Night Stalker's Voidbringer", "Silencer's Synaptic Split",
        header="Affected facets:"), t("BUFF")))
W(li("Tier 4 Towers now have a Barracks Reinforcement buff. Each allied barracks that has not been destroyed provides +4 armor to both Tier 4 towers", t("NEW"), extra=inline_note("Bonus is for each individual building, totaling in +24 Armor for 6 Barracks")))
W(li("Talents no longer require a skill point to level", t("REWORK"), extra=inline_note("Now talents are learned by using their own talent points available at levels 10, 15, 20, 25, 27, 28, 29, and 30. This results in all +2 All Attributes bonuses skilled by level 22")))
W(ul_close())
W(formula_change(
    "Assist Gold Formula",
    "60 + ( ( VictimNetworth * 0.037 ) / NumHeroes )",
    "15 + ( ( 50 + ( VictimNetworth * 0.037 ) ) / NumHeroes )",
    vary=("NumHeroes", "Heroes", [1, 2, 3, 4, 5]),
    fixed={"VictimNetworth": 10000},
    unit="Gold",
))
W(ul_open())
W(li("Melee Creep: Gold Bounty now increases by 1 per lane creep upgrade interval (every 7:30)", t("NEW")))
W(li("Flagbearer Creep: Gold Bounty now increases by 1 per lane creep upgrade interval", t("NEW")))
W(li("Flagbearer Creep: AoE Bounty Radius increased from 1200 to 1500", b(1200, 1500)))
W(li("Flagbearer Creep: When killed by a player controlled unit, the Flagbearer Creep always grants Bonus Bounty to the killer's hero regardless of the hero's proximity to the Flagbearer Creep", t("REWORK")))
W(li("Flagbearer Creep: Bonus Gold from killing Flagbearers is now classified as creep gold instead of ability gold", t("QoL"), extra=inline_note("Has no gameplay effect, but makes a post game gold breakdown more accurate")))
W(li("Flagbearer Creep: Inspiration Aura no longer affects heroes", t("DEL")))
W(li("Flagbearer Creep: Inspiration Aura now also provides a magic resistance bonus to affected creeps starting with 0% and improving by 4% with every lane creep upgrade interval, up to a maximum of 15 upgrades", t("NEW")))
W(ul_close())
W(ul_open())
W(li_formula("Courier respawn time decreased",
             "60s + 6s per Hero Level", "45s + 5s per Hero Level",
             lambda L: 60 + 6 * L, lambda L: 45 + 5 * L, l=True))
W(li("Courier no longer has a 15% movement speed penalty while carrying a Clarity, Enchanted Mango, Faerie Fire, Healing Salve, or Tango", t("BUFF")))
W(li("Flying Courier will now go to a more obscure shopping area within range of the Secret Shop when using Go To Secret Shop", t("QoL")))
W(ul_close())
W(ul_open())
W(li("All illusions now have 800 daytime vision and 400 nighttime vision", b([1800, 800], [800, 400], slash=True),
     extra=inline_note("Previously inherited the hero's full vision (typically 1800 daytime / 800 nighttime)")))
W(ul_close())

W(plain_header("Map Objectives"))
W(subgroup("Roshan"))
W(ul_open())
W(li("Roshan is no longer considered a hero for Lifesteal mechanics. As a result, Physical Lifesteal from damage to Roshan is reduced by 40%, and Spell Lifesteal from damage to Roshan is reduced by 80%", t("NEW")))
W(li("Roar of Retribution: Disarm debuff is no longer dispellable", t("NEW")))
W(li("Slam: No longer has double duration against creeps", t("DEL")))
W(li("Slam: Now deals double damage to creeps", t("NEW")))
W(ul_close())
W(subgroup("Tormentor"))
W(ul_open())
W(li("Added a Tormentor Timer near the minimap. Functions similarly to the Roshan Timer. Can be pinged to communicate the current state of Tormentor", t("QoL")))
W(li("Pinging Tormentor's location in world will trigger the same ping as the timer (same behavior the Roshan Timer has)", t("QoL")))
W(li("The minimap now only has one Tormentor icon and reflects where Tormentor is or will spawn", t("QoL")))
W(li("The Shining: Now only starts dealing damage to the surrounding enemies when attacked/damaged", t("REWORK")))
W(ul_close())
W(subgroup("Runes"))
W(ul_open())
W(li("Bounty Rune: Now grants gold based on when it was created, not when it was activated", t("REWORK")))
W(li("Haste Rune: Duration no longer increases by 3s per rune cycle, and is always 22s now", t("DEL")))
W(li("Invisibility Rune: No longer grants incoming damage reduction", t("DEL")))
W(ul_close())

W(plain_header("Terrain Changes", terrain_link="7.40"))
# One ul for the whole category so the tag-order sorter ranks across all rows
# (NEW → BUFF → NERF → DEL → MISC); the source paragraph splits were arbitrary.
W(ul_open())
W(li("Extended the streams into both Radiant and Dire bases and added defender's gate to the outside of the respective safe lanes where the stream flows", t("MISC")))
W(li("Removed some trees inside the base near the new safelane defender's gate positions", t("MISC")))
W(li("The Hard camp nearest to Tier 3 towers where the streams used to start has been demoted to a 'medium' camp", t("NERF")))
W(li("Moved the safelane medium amphibian neutral camp closest to the Tier 2 tower up the stream, slightly closer to the respective bases", t("MISC")))
W(li("Lowered the Wisdom Shrine areas to low ground, compared to the respective offlanes, filled them with water and connected to the water areas by the Tier 1 towers", t("MISC")))
W(li("Moved Wisdom Shrines and Watchers to the low ground and slightly closer to the Tier 1 towers. These Watchers now have vision over the shrines at night", t("MISC")))
W(li("Hard camps nearest to Wisdom Shrines have been moved slightly back towards the bases", t("MISC")))
W(li("Changed the 'bridges' to actual bridges", t("MISC")))
W(li("Slightly expanded the entrance to the bridge by the Lotus pools and adjusted the area within the nearby water areas", t("MISC")))
W(li("The Hard camp in the 'triangle' has been demoted to a 'medium' camp", t("NERF")))
W(li("Twin Gate mana cost decreased from 75 to 30", b(75, 30, l=True)))
W(li("Twin Gates now refund the mana cost if the teleporting channel was interrupted", t("NEW")))
W(li("Cleared up some areas around the Tormentor locations", t("MISC")))
W(li("The watchers nearest to the mid-lane and near the small water camps south/north of the tier 1 tower have been removed", t("DEL")))
W(li("The watchers in the primary jungles have been repositioned from stairs near the small camp to the cliff above the bounty runes", t("MISC")))
W(li("Added additional blocks preventing flying movement around the edges of the map (e.g. the highground areas behind the Tormentors will no longer be accessible by Batrider during Firefly)", t("NEW")))
W(li("Watcher night vision range decreased from 800 to 450", b(800, 450)))
W(li("Watcher capture time decreased from 1.5s to 1s", b(1.5, 1, l=True)))
W(li("Defender's Gate vision radius increased from 525 to 700", b(525, 700)))
W(li("Defender's Gate will now show their vision radius when holding ALT (similarly to Wards, Watchers, etc.)", t("QoL")))
W(li("Removed a tree between Dire Safelane Tier 1 tower and the small pull camp", t("MISC")))
W(li("Very slightly adjusted the paths and spawn points of the Radiant Offlane lane creeps, and the position of the Radiant Offlane Tier 2 tower. This results in creeps pathing to the right of the tier 2 tower instead of sometimes splitting up to go around it", t("MISC")))
W(li("Radiant Secret Shop trigger area moved slightly towards the radiant Tier 1 tower and more centered around the shopkeeper", t("MISC")))
W(ul_close())

W(plain_header("Invulnerability Targeting"))
W(section_intro("Invulnerability targeting rules have been updated — most items and abilities that previously could target and/or affect invulnerable units no longer do so."))
W(subgroup("Items"))
W(ul_open())
W(li("Nullifier's Nullify can no longer target invulnerable units", t("DEL")))
W(ul_close())
W(subgroup("Neutral Creeps"))
W(ul_open())
W(li("Satyr Banisher's Purge can no longer target invulnerable units", t("DEL")))
W(ul_close())
W(subgroup("Heroes"))
W(ul_open())
W(li("Dark Seer's Vacuum no longer affects invulnerable units", t("DEL")))
W(li("Naga Siren's Ensnare can no longer target invulnerable units unless this invulnerability is provided by Song of the Siren", t("REWORK")))
W(li("Ogre Magi's Bloodlust can no longer target invulnerable units", t("DEL"), extra=inline_note("Can still target invulnerable buildings (i.e. Tier 2-4 towers when the previous ones are not destroyed)")))
W(li("Oracle's Fortune's End can no longer target invulnerable units, but does affect invulnerable units in the radius", t("DEL")))
W(li("Shadow Demon's Demonic Purge can no longer target invulnerable units", t("DEL")))
W(li("Shadow Demon's Demonic Cleanse can no longer target invulnerable units", t("DEL")))
W(li("Sniper's Assassinate can no longer target invulnerable units", t("DEL")))
W(li("Sven's Storm Hammer with Aghanim's Scepter can no longer target invulnerable units, but does affect invulnerable units in the radius", t("DEL")))
W(li("Vengeful Spirit's Nether Swap can no longer target invulnerable units", t("DEL")))
W(ul_close())
W(subgroup("Cyclone"))
W(section_intro("Since Cyclone effects also make the unit invulnerable, all changes above apply to them as well — these are the special cases:"))
W(ul_open())
_cyclone_proj_note = "Also dispels Cyclone if the spell projectile was launched (or started channeling) before the target got Cycloned"
W(li("Nullifier's Nullify will dispel Cyclone off the target immediately if Cyclone was cast on a unit already affected by the Nullify debuff", t("MISC"), extra=inline_note(_cyclone_proj_note)))
W(li("Oracle's Fortune's End cannot target Cycloned units, but will dispel Cyclone off the units in AoE around the target", t("MISC"), extra=inline_note(_cyclone_proj_note)))
W(li("Sven's Storm Hammer with Aghanim's Scepter cannot target Cycloned units, but will dispel Cyclone off the units in AoE around the target", t("MISC"), extra=inline_note(_cyclone_proj_note)))
W(ul_close())

# ===== ITEM UPDATES =====
W(section("Item Updates"))
W(item_header("Clarity"))
W(ul_open())
W(li("Initial and maximum stock increased from 4 to 5", b(4, 5)))
W(li("Cost increased from 50 to 60", b(50, 60, l=True)))
W(ul_close())
W(item_header("Healing Salve"))
W(ul_open())
W(li("Initial and maximum stock increased from 4 to 5", b(4, 5)))
W(li("No longer has half duration when cast on an ally", t("DEL")))
W(li("Now heals for half the amount per second when cast on an ally", t("NEW")))
W(ul_close())
W(item_header("Iron Branch"))
W(ul_open())
W(li("Cost increased from 50 to 55", b(50, 55, l=True)))
W(ul_close())
W(item_header("Observer Ward"))
W(ul_open())
W(li("Observer Wards cannot be planted within 300 units of another Observer Ward from the same team that has been planted within the last second", t("QoL")))
W(li("Plant no longer increased by cast range increases", t("DEL")))
W(ul_close())
W(item_header("Sentry Ward"))
W(ul_open())
W(li("Sentry Wards cannot be planted within 300 units of another Sentry Ward from the same team that has been planted within the last second", t("QoL")))
W(li("Plant no longer increased by cast range increases", t("DEL")))
W(ul_close())
W(item_header("Smoke of Deceit"))
W(ul_open())
W(li("Can be used directly from the backpack", t("QoL")))
W(li("Has no cooldown when entering the main inventory from the backpack", t("QoL")))
W(ul_close())
W(item_header("Tango"))
W(ul_open())
W(li("Initial and maximum stock increased from 8 to 10", b(8, 10)))
W(li("Shared Tango now heals for half the amount per second", t("NEW")))
W(ul_close())
W(item_header("Roshan's Banner"))
W(ul_open())
W(li("Now upgrades with each subsequent drop", t("NEW"), extra=inline_note("Effect radius rescaled from 650 to 600/900/1200 " + b(650, [600, 900, 1200]))))
W(li("Hits to kill increased from 6 to 6/8/10", b(6, [6, 8, 10])))
W(ul_close())
W(item_header("Ghost Scepter"))
W(ul_open())
W(li("Ghost Form magic damage vulnerability decreased from 40% to 30%", b(40, 30, l=True)))
W(ul_close())
W(item_header("Ring of Tarrasque"))
W(ul_open())
W(li("Cost decreased from 1800 to 1700", b(1800, 1700, l=True)))
W(ul_close())
W(item_header("Shadow Amulet"))
W(ul_open())
W(li("Cost decreased from 1000 to 900", b(1000, 900, l=True)))
W(ul_close())
W(item_header("Tiara of Selemene"))
W(ul_open())
W(li("Cost decreased from 1800 to 1700", b(1800, 1700, l=True)))
W(ul_close())
W(item_header("Voodoo Mask"))
W(ul_open())
W(li("Cost decreased from 700 to 650", b(700, 650, l=True)))
W(ul_close())
W(item_header("Bloodstone"))
W(ul_open())
W(li("Total cost decreased from 4400 to 4350 due to Voodoo Mask cost decrease", b(4400, 4350, l=True)))
W(li("Spell Lifesteal bonus increased from +20% to +25%", b(20, 25)))
W(li("Bloodpact spell lifesteal multiplier decreased from 4x to 3x", b(4, 3)))
W(ul_close())
W(item_header("Boots of Bearing", changed=True))
W(auto_components_change("Boots of Bearing", "7.40"))
W(properties_change(
    old=[("BUFF", "+15 Health Regen")],
    new=[("",    "+18 Health Regen", b(15, 18))]))
W(item_header("Crimson Guard"))
W(ul_open())
W(li("Guard buff is no longer dispellable", t("NEW")))
W(ul_close())
W(item_header("Dagon"))
W(ul_open())
W(li("Total cost decreased from 2850 to 2800 due to Voodoo Mask cost decrease", b(2850, 2800, l=True), extra=inline_note("Total cost for all levels decreased from 2850/4000/5150/6300/7450 to 2800/3950/5100/6250/7400 " + b([2850,4000,5150,6300,7450], [2800,3950,5100,6250,7400], l=True))))
W(ul_close())
W(item_header("Diffusal Blade"))
W(ul_open())
W(li("Manabreak no longer applied by illusions", t("DEL")))
W(ul_close())
W(item_header("Disperser"))
W(ul_open())
W(li("Suppress now applies basic dispel to any target", t("NEW")))
W(li("Manabreak no longer applied by illusions", t("DEL")))
W(ul_close())
W(item_header("Ethereal Blade", changed=True))
W(auto_components_change("Ethereal Blade", "7.40"))
W(properties_change(
    old=[("BUFF", "+8 All Attributes"),
         ("DEL",  "+300 Mana"),
         ("DEL",  "+3 Mana Regen"),
         ("DEL",  "+250 Cast Range")],
    new=[("",    "+24 All Attributes", b(8, 24))]))
W(ul_open())
W(li("Recipe cost decreased from 1600 to 900. Total cost decreased from 5375 to 5200", b(1600, 900, l=True)))
W(li("Ether Blast magic damage vulnerability decreased from 40% to 30%", b(40, 30)))
W(li("Ether Blast attributes as damage changed from (1.5x the target's primary attribute) to (1x the sum of the caster's attributes)", t("REWORK")))
W(ul_close())
W(item_header("Glimmer Cape"))
W(ul_open())
W(li("Recipe cost increased from 350 to 450", t("MISC") + b(350, 450, l=True), extra=inline_note("Total cost unchanged at 2150 due to Shadow Amulet cost decrease")))
W(ul_close())
W(item_header("Guardian Greaves", changed=True))
W(auto_components_change("Guardian Greaves", "7.40"))
W(properties_change(
    old=[("BUFF", "+4 Armor")],
    new=[("",    "+5 Armor", b(4, 5))]))
W(ul_open())
W(li("Recipe cost decreased from 1450 to 1125. Total cost decreased from 5050 to 4300", b(1450, 1125, l=True)))
W(li("Guardian Aura no longer provides armor", t("DEL")))
W(li("Guardian Aura no longer provides additional bonuses when below 25% health to anyone but the wearer", t("DEL")))
W(li("Guardian Aura no longer provides increased armor and increased mana regeneration when below 25% health", t("DEL"), extra=inline_note("Still provides bonus health regeneration to the wearer when below 25% health")))
W(ul_close())
W(item_header("Hand of Midas"))
W(ul_open())
W(li("Transmute no longer has an experience multiplier", t("DEL")))
W(li("Transmute charge restore time decreased from 110s to 90s", b(110, 90, l=True)))
W(ul_close())
W(item_header("Heart of Tarrasque"))
W(ul_open())
W(li("Total cost decreased from 5200 to 5100 due to Ring of Tarrasque cost decrease", b(5200, 5100, l=True)))
W(li("Max Health Regen bonus decreased from +1.4% to +1%", b(1.4, 1)))
W(li("Now also provides passive Behemoth's Blood", t("NEW")))
W(li("Passive: Wearer's health regen is increased by 1.5% of missing health", "",
     extra=inline_note("Multiple instances of Behemoth's Blood don't stack")))
W(ul_close())
W(item_header("Heaven's Halberd"))
W(ul_open())
W(li("Disarm is now only dispellable by strong dispels", t("BUFF"), extra=inline_note("Still does not pierce debuff immunity")))
W(li("Disarm no longer has separate disarm durations for melee and ranged targets. Duration is always 3 seconds", t("NERF")))
W(li("Disarm cooldown increased from 18s to 20s", b(18, 20, l=True)))
W(ul_close())
W(item_header("Helm of the Dominator"))
W(ul_open())
W(li("Dominate gold and experience bounty when dominating a creep decreased from 100% to 50%", b(100, 50)))
W(ul_close())
W(item_header("Holy Locket", changed=True))
W(auto_components_change("Holy Locket", "7.40"))
W(properties_change(
    old=[("NERF", "+9 All Attributes")],
    new=[("",    "+7 All Attributes", b(9, 7))]))
W(ul_open())
W(li("Recipe cost increased from 800 to 1340", t("MISC") + b(800, 1340, l=True), extra=inline_note("Total cost unchanged at 2250 due to Iron Branch cost increase")))
W(li("Energy Charge automatic charge gain time increased from 8s to 10s", b(8, 10, l=True)))
W(li("Energy Charge max charges increased from 20 to 25", b(20, 25)))
W(li("Energy Charge cast range increased from 500 to 600", b(500, 600)))
W(li("Energy Charge mana restore per charge decreased from 17 to 15", b(17, 15)))
W(li("Energy Charge active now also increases the target's incoming Healing Amplification by 10% for 4s", t("NEW"), extra=inline_note("This occurs before the Energy Charge heal")))
W(ul_close())
W(item_header("Khanda", changed=True))
W(auto_components_change("Khanda", "7.40"))
W(properties_change(
    old=[("NERF", "+8 Mana Regen"),
         ("BUFF", "+200 Health"),
         ("BUFF", "+200 Mana")],
    new=[("",    "+3 Mana Regen",       b(8, 3)),
         ("",    "+450 Health",         b(200, 450)),
         ("",    "+450 Mana",           b(200, 450)),
         ("NEW", "+7 Health Regeneration")]))
W(item_header("Magic Wand"))
W(ul_open())
W(li("Total cost increased from 450 to 460 due to Iron Branch cost increase", b(450, 460, l=True)))
W(ul_close())
W(item_header("Mekansm"))
W(ul_open())
W(li("Armor bonus increased from +4 to +5", b(4, 5)))
W(ul_close())
W(item_header("Meteor Hammer"))
W(ul_open())
W(li("Meteor Hammer stun duration increased from 0.5s to 0.75s", b(0.5, 0.75)))
W(ul_close())
W(item_header("Nullifier"))
W(ul_open())
W(li("Nullify can no longer target invulnerable units", t("DEL")))
W(ul_close())
W(item_header("Octarine Core", changed=True))
W(auto_components_change("Octarine Core", "7.40"))
W(ul_open())
W(li("Total cost increased from 4800 to 4900 due to Tiara of Selemene cost decrease", b(4800, 4900, l=True)))
W(li("Can no longer be disassembled", t("DEL")))
W(ul_close())
W(item_header("Pavise"))
W(ul_open())
W(li("Armor bonus increased from +2 to +3", b(2, 3)))
W(ul_close())
W(item_header("Perseverance"))
W(ul_open())
W(li("Can now be disassembled", t("NEW")))
W(ul_close())
W(item_header("Pipe of Insight"))
W(ul_open())
W(li("Recipe cost increased from 700 to 800", t("MISC") + b(700, 800, l=True), extra=inline_note("Total cost unchanged at 3725 due to Ring of Tarrasque cost decrease")))
W(ul_close())
W(item_header("Phylactery", changed=True))
W(auto_components_change("Phylactery", "7.40"))
W(properties_change(
    old=[("DEL", "+200 Health"),
         ("DEL", "+200 Mana")],
    new=[("NEW", "+6.5 Health Regen"),
         ("NEW", "+2.5 Mana Regen")]))
W(ul_open())
W(li("Recipe cost decreased from 300 to 200 " + b(300, 200, l=True) + ". Total cost increased from 2500 to 2600", b(2500, 2600, l=True)))
W(ul_close())
W(item_header("Radiance"))
W(ul_open())
W(li("Evasion bonus increased from +15% to +25%", b(15, 25)))
W(li("Burn no longer causes enemies to miss 15% of their attacks", t("DEL")))
W(li("Burn no longer does extra damage to illusions", t("DEL")))
W(ul_close())
W(item_header("Refresher Orb", changed=True))
W(auto_components_change("Refresher Orb", "7.40"))
W(properties_change(
    old=[("DEL",  "+10 Damage"),
         ("NERF", "+18 Health Regen"),
         ("NERF", "+8 Mana Regen")],
    new=[("",    "+12 Health Regen", b(18, 12)),
         ("",    "+6 Mana Regen",    b(8, 6))]))
W(ul_open())
W(li("Recipe cost increased from 200 to 1600", t("MISC") + b(200, 1600, l=True), extra=inline_note("Total cost unchanged at 5000 due to Ring of Tarrasque and Tiara of Selemene cost decrease")))
W(ul_close())
W(item_header("Revenant's Brooch"))
W(ul_open())
W(li("Recipe cost increased from 600 to 650", t("MISC") + b(600, 650, l=True), extra=inline_note("Total cost unchanged at 3300 due to Voodoo Mask cost decrease")))
W(ul_close())
W(item_header("Scythe of Vyse"))
W(ul_open())
W(li("Recipe cost increased from 600 to 700", t("MISC") + b(600, 700, l=True), extra=inline_note("Total cost unchanged at 5200 due to Tiara of Selemene cost decrease")))
W(ul_close())
W(item_header("Shadow Blade"))
W(ul_open())
W(li("Total cost decreased from 3350 to 3250 due to Shadow Amulet cost decrease", b(3350, 3250, l=True)))
W(ul_close())
W(item_header("Shiva's Guard"))
W(ul_open())
W(li("Arctic Blast no longer does extra damage to illusions", t("DEL")))
W(ul_close())
W(item_header("Silver Edge"))
W(ul_open())
W(li("Total cost decreased from 5800 to 5700 due to Shadow Amulet cost decrease", b(5800, 5700, l=True)))
W(li("Shadow Walk debuff now caps the target's movement speed to 200. This debuff is not dispellable and does not pierce debuff immunity", t("NEW")))
W(ul_close())
W(item_header("Urn of Shadows"))
W(ul_open())
W(li("Bonus Mana Regen decreased from +1.4 to +1.25", b(1.4, 1.25)))
W(li("Soul Release charge gain radius increased from 1400 to 1500", b(1400, 1500)))
W(li("Soul Release charges can now be gained by all copies of Urn of Shadows item", t("MISC"), extra=inline_note("This change is exclusive to Urn of Shadows and doesn't affect Spirit Vessel")))
W(li("Soul Release charges can now be gained by both Urn of Shadows and Spirit Vessel from the same hero death", t("MISC"), extra=inline_note("Example to show the result of these two changes:<br>Two allied heroes. Both of them have both Urn of Shadows and Spirit Vessel. An enemy hero dies within 1500 range from them. Both Urns of Shadows will gain a charge. Spirit Vessel will also gain a charge as well, but only for the ally that was closer to the dying enemy")))
W(ul_close())
W(item_header("Spirit Vessel"))
W(ul_open())
W(li("Soul Release charge gain radius increased from 1400 to 1500", b(1400, 1500)))
W(li("Soul Release charges can now be gained by both Urn of Shadows and Spirit Vessel from the same hero death", t("MISC")))
W(ul_close())
W(item_header("Veil of Discord", changed=True))
W(auto_components_change("Veil of Discord", "7.40"))
W(properties_change(
    old=[("BUFF", "+4 Health Regen")],
    new=[("",    "+4.5 Health Regen", b(4, 4.5))]))
W(item_header("Wind Waker"))
W(ul_open())
W(li("Cyclone cooldown increased from 16s to 19s", b(16, 19, l=True)))
W(ul_close())
W(item_header("Wraith Band"))
W(ul_open())
W(li("Attack Speed bonus increased from +5 to +6", b(5, 6)))
W(ul_close())

# ===== NEUTRAL CREEP UPDATES =====
W(section("Neutral Creep Updates"))

W(unit_header("Satyr Mindstealer", _NC_CDN + "satyr_soulstealer.png"))
W(ability("Mana Burn", icon_url="../icons/abilities/satyr_soulstealer_mana_burn.png"))
W(ul_open())
W(li("Mana Burn target's intelligence multiplier decreased from 2/2.5/3/4x to 1/1.5/2/2.5x",
     b([2, 2.5, 3, 4], [1, 1.5, 2, 2.5])))
W(ul_close())

W(unit_header("Satyr Banisher", _NC_CDN + "satyr_trickster.png"))
W(ability("Purge", icon_url="../icons/abilities/satyr_trickster_purge.png"))
W(ul_open())
W(li("Purge can no longer target invulnerable units", t("DEL")))
W(ul_close())

# ===== NEUTRAL ITEM UPDATES =====
W(section("Neutral Item Updates"))

W(plain_header("Artifact changes", dynamics=False))
W(item_header("Ripper's Lash"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Sister's Shroud"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Spark of Courage"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Ash Legion Shield", new="New Tier 1 Artifact"))
W(ul_open())
W(li("Active: Shield Wall. Decreases wearer's movement speed by 12 to give all friendly player-controlled units within 800 radius a 140 physical damage barrier. Duration: 6s. No Mana Cost. Cooldown: 40s", t("NEW"), extra=inline_note("Doesn't affect ward units")))
W(ul_close())
W(item_header("Duelist Gloves", new="Returning Tier 1 Artifact"))
W(ul_open())
W(li("Passive: Boldness. Provides 20 attack speed if there are any enemy heroes within 1200 units", t("NEW")))
W(ul_close())
W(item_header("Weighted Dice", new="New Tier 1 Artifact"))
W(ul_open())
W(li("Passive: Loaded. When calculating wearer's base damage or creep bounty from last hits, the value is computed 2 times and the highest value is taken", t("NEW")))
W(ul_close())
W(item_header("Brigand's Blade"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Defiant Shell", new="Returning Tier 2 Artifact"))
W(ul_open())
W(li("Passive: Reciprocity. When attacked, the hero counter-attacks a target within their attack range for 80% of their normal attack damage. Cooldown: 5s. Can't proc attack modifiers", t("NEW"),
     extra=inline_note("Dormant Curio increases counter-attack damage from 80% to 104%")))
W(ul_close())
W(item_header("Searing Signet"))
W(ul_open())
W(li("Burn Through total damage increased from 72 to 90", b(72, 90), extra=inline_note("Dormant Curio Total Damage increased from 93.6 to 117")))
W(li("Burn Through now does 50% less damage to non-hero targets", t("NERF")))
W(ul_close())
W(item_header("Gale Guard"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Jidi Pollen Bag"))
W(ul_open())
W(li("Pollinate Duration decreased from 12s to 9s", b(12, 9)))
W(li("Pollinate Max Health Damage decreased from 12% to 9%", b(12, 9), extra=inline_note("Dormant Curio Max Health Damage decreased from 15.6% to 11.7%")))
W(li("Pollinate Cooldown decreased from 45s to 25s", b(45, 25, l=True)))
W(ul_close())
W(item_header("Psychic Headband"))
W(ul_open())
W(li("Psychic Push can now target allies", t("NEW"), extra=inline_note("Still can't target the wearer themself")))
W(ul_close())
W(item_header("Unrelenting Eye"))
W(ul_open())
W(li("Moved from Tier 5 to Tier 3", t("REWORK")))
W(li("Relentless no longer provides status resistance for nearby enemies", t("DEL")))
W(li("Relentless max slow resistance decreased from 100% to 50%", b(100, 50), extra=inline_note("Dormant Curio Max Slow Resistance decreased from 130% to 65%")))
W(li("Relentless slow resistance loss per enemy hero in range decreased from 20% to 10%", b(20, 10)))
W(li("Relentless search radius changed from 600 to the hero's attack range", t("REWORK")))
W(ul_close())
W(item_header("Magnifying Monocle"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Outworld Staff"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Pyrrhic Cloak"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Flayer's Bota", new="New Tier 4 Artifact"))
W(ul_open())
W(li("Active: Bloodthirst. Increases wearer's base damage by 15% and attack speed by 30 for 6s. No Mana Cost. Cooldown: 65s", t("NEW"),
     extra=inline_note("Dormant Curio increases bonus base damage from 15% to 19.5% and attack speed from 30 to 39")))
W(li("Passive: Bloodrush. The cooldown of Bloodthirst is reset whenever an enemy hero dies with 1200 units", t("NEW")))
W(ul_close())
W(item_header("Giant's Maul"))
W(ul_open())
W(li("Crushing Blow critical damage decreased from 150% to 140%", b(150, 140), extra=inline_note("Dormant Curio critical damage decreased from 195% to 182%")))
W(ul_close())
W(item_header("Idol of Scree'auk", new="New Tier 4 Artifact"))
W(ul_open())
W(li("Active: False Flight. Grants phased movement, 50% slow resistance, and 25% evasion for 5s. No Mana Cost. Cooldown: 30s", t("NEW"),
     extra=inline_note("Dormant Curio increases duration from 5s to 6.5s")))
W(ul_close())
W(item_header("Metamorphic Mandible", new="New Tier 4 Artifact"))
W(ul_open())
W(li("Active: Pupate. The wearer enters an insect form for 4 seconds, increasing magic resistance by 35% and movement speed by 15%, but decreasing size by 20% and armor by 45%. No Mana Cost. Cooldown: 30s. Can be dispelled. Can't be cast while channeling", t("NEW"),
     extra=inline_note("Dormant Curio increases duration from 4s to 5.2s")))
W(ul_close())
W(item_header("Rattlecage", new="Returning Tier 4 Artifact"))
W(ul_open())
W(li("Passive: Reverberate. After taking 180 damage from any source, the wearer fires up to 2 projectiles at random nearby enemies within a 600 unit radius, prioritizing heroes, that deal 110 damage and slows the targets movement and attack speed by 100% for 0.2s", t("NEW"),
     extra=inline_note("Dormant Curio increases damage from 110 to 143")))
W(ul_close())
W(item_header("Helm of the Undying"))
W(ul_open())
W(li("Item cycled out", t("DEL")))
W(ul_close())
W(item_header("Dezun Bloodrite"))
W(ul_open())
W(li("Moved from Tier 4 to Tier 5", t("REWORK")))
W(li("Blood Invocation area of effect bonus increased from 12% to 16%", b(12, 16), extra=inline_note("Dormant Curio Area of Effect bonus increased from 15.6% to 20.8%")))
W(ul_close())
W(item_header("Riftshadow Prism", new="New Tier 5 Artifact"))
W(ul_open())
W(li("Active: Refract. Spends 10% of the wearer's current health to create a full health illusion that lasts for 20s. The illusion has 50% outgoing damage and 240% incoming damage. No Mana Cost. Cooldown: 30s", t("NEW"),
     extra=inline_note("Dormant Curio increases illusion outgoing damage from 50% to 65%")))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))


# Abaddon
W(hero_header("Abaddon"))
W(ul_open())
W(li("Base Strength decreased from 22 to 21", b(22, 21)))
W(li("Base Agility decreased from 23 to 22", b(23, 22)))
W(li("Damage at level 1 decreased by 1 (from 50–60 to 49–59)", br(50, 60, 49, 59)))
W(ul_close())
W(facet_header("abaddon_the_quickening"))
W(ul_open())
W(li("Cooldown reduction on hero death decreased from 6s to 5s", b(6, 5)))
W(ul_close())
W(ability("Mist Coil", slug="abaddon_death_coil"))
W(ul_open())
W(li("Cooldown increased from 6.5/6/5.5/5s to 8/7/6/5s", b([6.5, 6, 5.5, 5], [8, 7, 6, 5], l=True)))
W(li("Damage/Heal increased from 80/150/220/290 to 95/160/225/290", b([80, 150, 220, 290], [95, 160, 225, 290])))
W(ul_close())

# Alchemist
W(hero_header("Alchemist"))
W(ability("Acid Spray", slug="alchemist_acid_spray"))
W(ul_open())
W(li("Mana Cost increased from 105/110/115/120 to 120", b([105, 110, 115, 120], 120, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Damage per Greevil's Greed stack increased from +2 to +2.5", b(2, 2.5)))
W(ul_close())

# Anti-Mage
W(hero_header("Anti-Mage"))
W(ability("Counterspell Ally", slug="antimage_counterspell_ally"))
W(ul_open())
W(li("Ability removed", t("DEL")))
W(ul_close())
W(ability("Counterspell", slug="antimage_counterspell"))
W(ul_open())
W(li("Aghanim's Shard no longer provides Counterspell Ally ability", t("DEL")))
W(li("Aghanim's Shard illusion outgoing damage increased from 75% to 100%", b(75, 100)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Persecutor Min/Max Movement Slow increased from +7.5/15% to +9/18%", b([7.5, 15], [9, 18])))
W(ul_close())

# Arc Warden
W(hero_header("Arc Warden"))
W(ul_open())
W(li("Base attack speed increased from 100 to 110", b(100, 110)))
W(ul_close())
W(ability("Magnetic Field", slug="arc_warden_magnetic_field"))
W(ul_open())
W(li("Mana Cost rescaled from 50/70/90/110 to 60/70/80/90", b([50, 70, 90, 110], [60, 70, 80, 90], l=True)))
W(ul_close())

# Axe
W(hero_header("Axe"))
W(ability("Berserker's Call", slug="axe_berserkers_call"))
W(ul_open())
W(li("Duration increased from 1.8/2.2/2.6/3s to 2.1/2.4/2.7/3s", b([1.8, 2.2, 2.6, 3], [2.1, 2.4, 2.7, 3])))
W(li("Cooldown increased from 17/15/13/11s to 18/16/14/12s", b([17, 15, 13, 11], [18, 16, 14, 12], l=True)))
W(ul_close())
W(ability("Battle Hunger", slug="axe_battle_hunger"))
W(ul_open())
W(li("No longer has an armor-based damage multiplier", t("DEL")))
W(li("Damage type changed from Physical to Pure", t("REWORK")))
W(li("No longer has reduced movement slow against creeps", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +10% Battle Hunger Slow replaced with +12 Battle Hunger Damage Per Second", t("REWORK")))
W(li("Level 20 Talent Counter Helix Damage increased from +30 to +40", b(30, 40)))
W(li("Level 20 Talent +100 Culling Blade Damage replaced with +15 Strength", t("REWORK")))
W(li("Level 25 Talent 2x Battle Hunger Armor Multiplier replaced with +150 Culling Blade Damage", t("REWORK")))
W(ul_close())

# Bane
W(hero_header("Bane"))
W(ability("Nightmare", slug="bane_nightmare"))
W(ul_open())
W(li("Cooldown increased from 24/21/18/15s to 25/22/19/16s", b([24, 21, 18, 15], [25, 22, 19, 16], l=True)))
W(ul_close())
W(ability("Fiend's Grip", slug="bane_fiends_grip"))
W(ul_open())
W(li("Aghanim's Scepter Illusion damage taken increased from 200% to 225%", b(200, 225, l=True)))
W(ul_close())

# Batrider
W(hero_header("Batrider"))
W(ul_open())
W(li("Daytime Vision Range increased from 1600 to 1800", b(1600, 1800)))
W(ul_close())
W(facet_header("batrider_arsonist"))
W(ul_open())
W(li("No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
W(ul_close())
W(ability("Flamebreak", slug="batrider_flamebreak"))
W(ul_open())
W(li("Movement Slow decreased from 8/16/24/32% to 6/12/18/24%", b([8, 16, 24, 32], [6, 12, 18, 24])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Flaming Lasso Cooldown Reduction increased from 7s to 8s", b(7, 8)))
W(ul_close())

# Beastmaster
W(hero_header("Beastmaster"))
W(ul_open())
W(li("Call of the Wild Boar: Boar's Base Attack Time worsened from 1.25s to 1.35s", b(1.25, 1.35, l=True)))
W(ul_close())
W(ability("Wild Axes", slug="beastmaster_wild_axes"))
W(ul_open())
W(li("Damage per axe rescaled from 35/65/95/125 to 30/65/100/135", b([35, 65, 95, 125], [30, 65, 100, 135], force_overall="buff")))
W(ul_close())
W(ability("Inner Beast", slug="beastmaster_inner_beast", innate=False))
W(ul_open())
W(li("Bonus Attack Speed rescaled from 15/30/45/60 to 10/30/50/70", b([15, 30, 45, 60], [10, 30, 50, 70])))
W(ul_close())

# Bloodseeker
W(hero_header("Bloodseeker"))
W(ability("Sanguivore", slug="bloodseeker_sanguivore"))
W(ul_open())
W(li("Base heal increased from 25 to 30", b(25, 30)))
W(li("No longer upgraded with Aghanim's Shard or Aghanim's Scepter", t("DEL")))
W(ul_close())
W(ability("Bloodrage", slug="bloodseeker_bloodrage"))
W(ul_open())
W(li("Aghanim's Scepter effect moved to Aghanim's Shard", t("MISC")))
W(li("Aghanim's Shard target's max health as pure damage decreased from 3% to 2%", b(3, 2)))
W(ul_close())
W(ability("Rupture", slug="bloodseeker_rupture"))
W(ul_open())
W(li("Aghanim's Scepter: Increases current health as initial damage by 3%. Replaces cooldown with 2 charges with the same charge restoration time", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +15% Bloodrage Spell Amplification replaced with +30 Bloodrage Attack Speed", t("REWORK")))
W(li("Level 15 Talent +8% Rupture Initial Damage replaced with -0.7% Bloodrage Max Health DPS For Allies", t("REWORK")))
W(li("Level 20 Talent -0.7% Bloodrage Max Health DPS For Allies replaced with +20 Agility", t("REWORK")))
W(li("Level 25 Talent 2 Rupture Charges replaced with +2.5s Blood Rite Silence Duration", t("REWORK")))
W(ul_close())

# Bounty Hunter
W(hero_header("Bounty Hunter"))
W(facet_header("bounty_hunter_mugging"))
W(ul_open())
W(li("Visual effect of gold flying towards Bounty Hunter is no longer visible to enemies if Bounty Hunter is invisible", t("QoL")))
W(ul_close())
W(ability("Shadow Walk", slug="bounty_hunter_wind_walk"))
W(ul_open())
W(li("Stun Duration increased from 0.8/1/1.2/1.4s to 1/1.2/1.4/1.6s", b([0.8, 1, 1.2, 1.4], [1, 1.2, 1.4, 1.6])))
W(ul_close())

# Brewmaster
W(hero_header("Brewmaster"))
W(ul_open())
W(li("Strength gain decreased from 3.7 to 3.2", b(3.7, 3.2)))
W(li("Intelligence gain increased from 1.6 to 1.9", b(1.6, 1.9)))
W(ul_close())
W(facet_header("brewmaster_roll_out_the_barrel"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("brewmaster_drunken_master"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
_lc_pill, _lc_table = scale_pill("10.5% + 0.5% per level up",
                                 lambda L: 10.5 + 0.5 * L,
                                 levels=[1, 5, 10, 15, 20, 25, 30], value_fmt="{:.1f}%")
W(ability_change(
    old=dict(
        name="Belligerent",
        innate=True,
        desc=[
            "Passive.",
            "Whenever Brewmaster respawns or comes out of Primal Split, he gains <b>25%</b> bonus attack damage. Duration on respawn: 45s. Duration after Primal Split: 15s.",
        ],
    ),
    new=dict(
        name="Liquid Courage",
        slug="brewmaster_liquid_courage",
        innate=True,
        desc=[
            "Passive. Improves with Brewmaster's level.",
            "When Brewmaster drops below 50% Health he gains a Status Resistance buff, and his movement speed alternates every 1 second between faster and slower. The effect grows stronger at lower health, scaling from 0 up to max values at 20% Health.",
            "Max Status Resistance is " + _lc_pill + ", Max Speed Increase is <b>25%</b>, Max Speed Slow is <b>10%</b>.",
            aghs_shard_line("Brewmaster may activate the ability to toss a strong drink to himself or a teammate, granting the max effects of his innate for 5 seconds plus 2% Max HP Regen per second. Cast Range: 800. Mana Cost: 50. Cooldown: 20s."),
        ],
        tables=[_lc_table],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Thunder Clap", slug="brewmaster_thunder_clap"))
W(ul_open())
W(li("Cast point improved from 0.35s to 0.3s", b(0.35, 0.3, l=True)))
W(li("Mana Cost rescaled from 90/100/110/120 to 100", b([90, 100, 110, 120], 100, l=True)))
W(li("Radius rescaled from 325/350/375/400 to 375", b([325, 350, 375, 400], 375)))
W(ul_close())
W(ability("Cinder Brew", slug="brewmaster_cinder_brew"))
W(ul_open())
W(li("Now rolls a barrel of ale that deals 40/70/100/130 physical damage to enemies in its path and drenches enemies along the way and around the target location", t("NEW")))
W(ul_close())
W(ability("Drunken Brawler", slug="brewmaster_drunken_brawler"))
W(ul_open())
W(li("Moved Brewed Up effect from Cinder Brew to Drunken Brawler", t("MISC"), extra=inline_note("When Brewmaster casts any ability, he becomes Brewed Up for 5 seconds, gaining +150% to his stance bonuses. If he is already Brewed Up, the duration is extended by 1s. After Brewed Up ends, Brewmaster is hungover and cannot become Brewed Up again for 9 seconds")))
W(li("Stance visual indicator is now always present around Brewmaster", t("QoL")))
W(li("Stances can now be switched without cancelling channeling or invisibility", t("MISC")))
W(ul_close())

# Each Drunken Brawler stance rendered as a standalone ability block using
# the stance spellicons. A dashed connector (drawStanceConnectors() in
# scripts.js) anchors them as children of Drunken Brawler above — same
# concept as Primal Split → brewlings.
W(ability("Earth Stance", slug="brewmaster_drunken_brawler_earth"))
W(ul_open())
W(li("Magic Resistance increased from 5/10/15/20% to 8/12/16/20%", b([5, 10, 15, 20], [8, 12, 16, 20])))
W(ul_close())
W(ability("Fire Stance", slug="brewmaster_drunken_brawler_fire"))
W(ul_open())
W(li("Attack Speed increased from 10/15/20/25 to 10/20/30/40", b([10, 15, 20, 25], [10, 20, 30, 40])))
W(ul_close())
W(ability("Void Stance", slug="brewmaster_drunken_brawler_void"))
W(ul_open())
W(li("Stance removed", t("DEL")))
W(ul_close())
W(ability("Primal Companion", slug="brewmaster_primal_companion"))
W(ul_open())
W(li("Ability removed", t("DEL")))
W(ul_close())
W(ability("Primal Split", slug="brewmaster_primal_split"))
W(ul_open())
W(li("Duration increased from 16/18/20s to 16/20/24s", b([16, 18, 20], [16, 20, 24])))
W(li("All Brewlings now receive their respective Drunken Brawler stances", t("NEW")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(li("Aghanim's Scepter: Allows Brewmaster to cancel the ability early and provides Brewed Up bonus to all Brewlings on cast. Also increases ability's level to 4, improving Brewlings' stats and abilities", t("NEW")))
W(ul_close())

# Each brewling rendered as an ability_change comparison card. Same
# name on both sides → "in-place" mode hides the duplicate header.
# Each brewling is a standalone ability block. A dashed connector
# (drawn by drawBrewlingConnectors() in scripts.js) visually anchors
# them as children of Primal Split above.
W(ability("Earth Brewling", slug="brewmaster_earth_unit", icon_url="../icons/units/brewmaster_earth_unit.png"))
W(ul_open())
W(li("Debuff Immunity ability renamed to Earth Element. No longer grants Debuff Immunity; now provides 80% Status Resistance and 60% Magic Resistance instead", t("REWORK")))
W(li("Damage increased from 25/60/95 to 35/70/105", b([25, 60, 95], [35, 70, 105]),
     extra=inline_note("From 20–30/55–65/90–100 to 30–40/65–75/100–110")))
W(li("Movement Speed increased from 330/350/370 to 330/355/380", b([330, 350, 370], [330, 355, 380])))
W(li("Demolish Bonus Building Damage decreased from 50/100/150 to 40/80/120", b([50, 100, 150], [40, 80, 120])))
W(li("Aghanim's Scepter increases Brewling level by 1. " + info_tip(
        "4100 HP.", "8 HP Regen.", "135–145 Damage.", "9 Armor.", "",
        "Hurl Boulder: 200 Damage, 2s Stun.", "Demolish: 160 bonus building damage.",
        header="Level 4 stats are:"), t("NEW")))
W(ul_close())
W(ability("Storm Brewling", slug="brewmaster_storm_unit", icon_url="../icons/units/brewmaster_storm_unit.png"))
W(ul_open())
W(li("Damage increased from 20/40/60 to 30/50/70", b([20, 40, 60], [30, 50, 70]),
     extra=inline_note("From 15–25/35–45/55–65 to 25–35/45–55/65–75")))
W(li("Aghanim's Scepter increases Brewling level by 1. " + info_tip(
        "2500 HP.", "8 HP Regen.", "85–95 Damage.", "",
        "Wind Walk: 320 bonus damage, 55% bonus movement speed.",
        "Cyclone: 6s hero duration, 100 damage on landing.",
        header="Level 4 stats are:"), t("NEW")))
W(ul_close())
W(ability("Fire Brewling", slug="brewmaster_fire_unit", icon_url="../icons/units/brewmaster_fire_unit.png"))
W(ul_open())
W(li("Aghanim's Scepter increases Brewling level by 1. " + info_tip(
        "1750 HP.", "8 HP Regen.", "215–225 Damage.", "24 Armor.", "",
        "Permanent Immolation: 100 damage per second.",
        header="Level 4 stats are:"), t("NEW")))
W(ul_close())
W(ability("Void Brewling", slug="brewmaster_void_unit", icon_url="../icons/units/brewmaster_void_unit.png"))
W(ul_open())
W(li("Brewling removed", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +1.5s Thunder Clap Duration replaced with +1s Drunken Brawler Brew Up / Extend Duration", t("REWORK")))
W(li("Level 10 Talent +10 Brewlings Damage replaced with +14 Brewlings Base Damage", t("REWORK")))
W(li("Level 15 Talent Cinder Brew Damage/Duration increased from +30% to 40%", b(30, 40)))
W(li("Level 15 Talent +1x Brewed Up multiplier for Drunken Brawler replaced with +600 Brewlings Health", t("REWORK")))
W(li("Level 20 Talent +1200 Brewlings Health replaced with -15s Primal Split Cooldown", t("REWORK")))
W(li("Level 25 Talent Brewlings Gain Drunken Brawler Passive replaced with 1.5x Drunken Brawler Stance Bonuses", t("REWORK")))
W(ul_close())

# Bristleback
W(hero_header("Bristleback"))
W(ul_open())
W(li("Strength gain increased from 2.7 to 2.8", b(2.7, 2.8)))
W(ul_close())
W(facet_header("bristleback_snot_rocket"))
W(ul_open())
W(li("Viscous Nasal Goo no longer has increased Armor Loss per stack", t("DEL")))
W(ul_close())
W(ability("Viscous Nasal Goo", slug="bristleback_viscous_nasal_goo"))
W(ul_open())
W(li("Armor Loss per stack increased from 1.5/2/2.5/3 to 2/2.5/3/3.5 by default", b([1.5, 2, 2.5, 3], [2, 2.5, 3, 3.5])))
W(ul_close())

# Broodmother
W(hero_header("Broodmother"))
W(ability("Insatiable Hunger", slug="broodmother_insatiable_hunger"))
W(ul_open())
W(li("Aghanim's Shard no longer increases duration", t("DEL")))
W(ul_close())
W(ability("Spin Web", slug="broodmother_spin_web"))
W(ul_open())
W(li("Broodmother's illusions now also benefit from the web", t("NEW")))
W(ul_close())
W(ability("Incapacitating Bite", slug="broodmother_incapacitating_bite"))
W(ul_open())
W(li("Attack Bonus increased from 2/4/6/8 to 3/6/9/12", b([2, 4, 6, 8], [3, 6, 9, 12])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +1.5% Spider's Milk Heal replaced with +20% Insatiable Hunger Lifesteal", t("REWORK")))
W(li("Level 15 Talent Spiderlings Health increased from +125 to +150", b(125, 150)))
W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +12 to +10", b(12, 10)))
W(li("Level 20 Talent +35 Attack Speed replaced with +25% Incapacitating Bite Slow/Miss Chance", t("REWORK")))
W(li("Level 25 Talent +30% Incapacitating Bite Slow/Miss Chance replaced with +14% Spin Web Move Speed and Ignore Speed Limit", t("REWORK")))
W(ul_close())

# Centaur Warrunner
W(hero_header("Centaur Warrunner"))
W(ability("Rawhide", slug="centaur_rawhide"))  # innate (auto-detected)
W(ul_open())
W(li("Bonus Max Health decreased from 30 to 25", b(30, 25)))
W(ul_close())
W(ability("Work Horse", slug="centaur_work_horse"))
W(ul_open())
W(li("Cooldown increased from 24s to 35s", b(24, 35, l=True)))
W(li("Duration decreased from 8s to 7s", b(8, 7)))
W(ul_close())

# Chaos Knight
W(hero_header("Chaos Knight"))
W(ul_open())
W(li("Min Base Damage increased by 5", bstat_h("Chaos Knight", "AttackDamageMin", "7.39e", 5), extra=note_box(hero="Chaos Knight", field="AttackDamageMin", before_patch="7.39e")))
W(li("Max Base Damage decreased by 5", bstat_h("Chaos Knight", "AttackDamageMax", "7.39e", -5), extra=note_box(hero="Chaos Knight", field="AttackDamageMax", before_patch="7.39e")))
W(li("Damage at level 1 changed from 48–78 to 53–73", br(48, 78, 53, 73), extra=inline_note("Damage spread decreased from 30 to 20")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +10s Phantasm Duration replaced with -125% Phantasm Damage Taken", t("REWORK")))
W(ul_close())

# Chen
W(hero_header("Chen"))
W(ability("Penitence", slug="chen_penitence"))
W(ul_open())
W(li("Mana Cost increased from 70/75/80/85 to 80/90/100/110", b([70, 75, 80, 85], [80, 90, 100, 110], l=True)))
W(li("Cooldown increased from 14/13/12/11s to 20/17/14/11s", b([14, 13, 12, 11], [20, 17, 14, 11], l=True)))
W(li("No longer grants bonus attack range", t("DEL")))
W(li("Now deals 50/75/100/125 pure damage by default", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Penitence Deals 175 Damage replaced with +75 Penitence Damage", t("REWORK")))
W(li("Level 20 Talent Divine Favor Heal Amplification decreased from +20% to +15%", b(20, 15)))
W(ul_close())

# Clinkz
W(hero_header("Clinkz"))
W(facet_header("clinkz_suppressive_fire"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("clinkz_engulfing_step"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Bone and Arrow",
        innate=True,
        desc=[
            "Passive.",
            "Clinkz summons a Skeleton Archer when he dies. Tower hits on the archers count as hero hits.",
        ],
    ),
    new=dict(
        name="Infernal Shred",
        slug="clinkz_infernal_shred",
        innate=True,
        desc=[
            "Passive.",
            "Clinkz and his skeletons apply a stacking debuff that causes their attacks to pierce up to <b>20%</b> of the target's armor. Clinkz applies 2% per attack, his skeletons apply 1%. Debuff lasts 5 seconds. " + info_tip("Doesn't affect the target's armor directly — it simply improves attacks for Clinkz and his skeletons."),
        ],
    ),
    summary="New innate ability.",
    tag="new",
))
W(ability("Tar Bomb", slug="clinkz_tar_bomb"))
W(ul_open())
W(li("Ability removed", t("DEL")))
W(ul_close())
W(ability("Strafe", slug="clinkz_strafe"))
W(ul_open())
W(li("Skeleton Archers attack speed factor decreased from 60% to 50%", b(60, 50)))
W(ul_close())
W(ability("Searing Arrows", slug="clinkz_searing_arrows"))
W(ul_open())
W(li("Returning as base ability", t("NEW"), extra=inline_note("Imbues Clinkz's arrows with fire for extra 18/32/46/60 extra damage. Skeleton Archers always fire Searing Arrows with 50% reduced damage. Mana Cost: 10<br><br>Skeleton Archers target the enemy attacked by Clinkz with Searing Arrows effect")))
W(ul_close())
W(ability("Death Pact", slug="clinkz_death_pact"))
W(ul_open())
W(li("No longer creates Skeleton Archers", t("DEL")))
W(ul_close())
W(ability("Skeleton Walk", slug="clinkz_wind_walk"))
W(ul_open())
W(li("Skeleton Archer stats and Aghanim's Scepter upgrade are now part of Skeleton Walk", t("MISC")))
W(li("Skeleton Archer Duration rescaled from 15/20/25/30s to 20/25/30s", t("REWORK"), extra=inline_note("Also applies to Burning Army")))
W(ul_close())
W(ability("Burning Barrage", slug="clinkz_burning_barrage"))
W(ul_open())
W(li("No longer slows the targets", t("DEL")))
W(ul_close())
W(ability("Burning Army", slug="clinkz_burning_army"))
W(ul_open())
W(li("Spawn Interval improved from 0.15s to 0.1s", b(0.15, 0.1, l=True)))
W(li("Skeleton count increased from 5 to 6", b(5, 6)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Tar Bomb Multishot replaced with Searing Arrows Multishot", t("REWORK")))
W(ul_close())

# Clockwerk
W(hero_header("Clockwerk"))
W(ability("Jetpack", slug="rattletrap_jetpack"))
W(ul_open())
W(li("Now can be toggled on and off for the duration of the buff. Toggle cooldown: 1s", t("NEW")))
W(ul_close())
W(ability("Overclocking", slug="rattletrap_overclocking"))
W(ul_open())
W(li("Rocket Flare cooldown increased from 3s to 3.5s", b(3, 3.5, l=True)))
W(ul_close())

# Crystal Maiden
W(hero_header("Crystal Maiden"))
W(ul_open())
W(li("Base Damage decreased by 2", t("MISC") + bstat_h("Crystal Maiden", "AttackDamageMin", "7.39e", -2), extra=note_box(hero="Crystal Maiden", field="AttackDamageMin", before_patch="7.39e", extra_note="Damage at level 1 unchanged at 48–54")))
W(li("Base Intelligence increased from 18 to 20", b(18, 20)))
W(ul_close())

# Dark Seer
W(hero_header("Dark Seer"))
W(ul_open())
W(li("Base Intelligence increased from 21 to 22", b(21, 22)))
W(li("Damage at level 1 increased by 1 (from 52–58 to 53–59)", br(52, 58, 53, 59)))
W(ul_close())
W(ability("Vacuum", slug="dark_seer_vacuum"))
W(ul_open())
W(li("No longer affects invulnerable units", t("DEL")))
W(ul_close())

# Dark Willow
W(hero_header("Dark Willow"))
W(ability("Cursed Crown", slug="dark_willow_cursed_crown"))
W(ul_open())
W(li("Stun Duration increased from 1.2/1.6/2/2.4s to 1.5/1.8/2.1/2.4s", b([1.2, 1.6, 2, 2.4], [1.5, 1.8, 2.1, 2.4])))
W(ul_close())
W(ability("Terrorize", slug="dark_willow_terrorize"))
W(ul_open())
W(li("Jex return speed increased from 600 to 800", b(600, 800)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +150 Cursed Crown AoE replaced with -15s Terrorize Cooldown", t("REWORK")))
W(ul_close())

# Dawnbreaker
W(hero_header("Dawnbreaker"))
W(ul_open())
W(li("Base Damage increased by 1", bstat_h("Dawnbreaker", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Dawnbreaker", field="AttackDamageMin", before_patch="7.39e")))
W(li("Damage at level 1 increased from 49–53 to 50–54", br(49, 53, 50, 54)))
W(ul_close())
W(ability("Solar Guardian", slug="dawnbreaker_solar_guardian"))
W(ul_open())
W(li("Aghanim's Scepter no longer reduces air time or channel time", t("DEL")))
W(li("Aghanim's Scepter Heal per pulse increased from 55/85/115 to 60/90/120", b([55, 85, 115], [60, 90, 120])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +12 Damage replaced with +15% Break of Dawn Max Damage", t("REWORK")))
W(ul_close())

# Dazzle
W(hero_header("Dazzle"))
W(ul_open())
W(li("Base Strength increased from 18 to 19", b(18, 19), extra=inline_note("Damage at level 1 unchanged")))
W(li("Intelligence gain decreased from 3.7 to 3.5", b(3.7, 3.5)))
W(li("Damage gain per level decreased from 3.5 to 3.4", b(3.5, 3.4)))
W(ul_close())
W(ability("Nothl Projection", slug="dazzle_nothl_projection"))
W(ul_open())
W(li("Aghanim's Shard healing amplification decreased from 20% to 15%", b(20, 15)))
W(ul_close())

# Death Prophet
W(hero_header("Death Prophet"))
W(ability("Witchcraft", slug="death_prophet_witchcraft"))
W(ul_open())
_pill1 = scale_pill("0.75% + 0.75% per level up", lambda L: 0.75 + 0.75*L,
                    levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30])
W(li("Movement speed bonus changed from 0.5% per hero level to " + _pill1[0] + "", t("REWORK"), extra=_pill1[1]))
W(ul_close())
W(ability("Exorcism", slug="death_prophet_exorcism"))
W(ul_open())
W(li("No longer provides 4/8/12% bonus movespeed", t("DEL")))
W(li("Aghanim's Scepter spirit bonus damage increased from 50% to 60%", b(50, 60)))
W(ul_close())

# Doom
W(hero_header("Doom"))
W(ul_open())
W(li("Intelligence gain increased from 1.7 to 1.9", b(1.7, 1.9)))
W(ul_close())
W(facet_header("doom_bringer_boost_selling"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Doom", slug="doom_bringer_doom"))
W(ul_open())
W(li("Aghanim's Scepter now also increases damage per second from 25/45/65 to 40/60/80", b([25, 45, 65], [40, 60, 80])))
W(ul_close())

# Dragon Knight
W(hero_header("Dragon Knight"))
W(ul_open())
W(li("Base Agility decreased from 16 to 14", b(16, 14)))
W(ul_close())
W(ability("Elder Dragon Form", slug="dragon_knight_elder_dragon_form"))
W(ul_open())
W(li("Bonus Attack Damage decreased from 20/60/100/140 to 20/50/80/110", b([20, 60, 100, 140], [20, 50, 80, 110])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent 30% Breathe Fire Damage Reduction replaced with -2s Breathe Fire Cooldown", t("REWORK")))
W(li("Level 20 Talent +85% Breathe Fire Damage/Cast Range in Dragon Form replaced with +60% Breathe Fire Damage/Cast Range", t("REWORK")))
W(ul_close())

# Drow Ranger
W(hero_header("Drow Ranger"))
W(ability("Frost Arrows", slug="drow_ranger_frost_arrows"))
W(ul_open())
W(li("Movement Slow increased from 10/20/30/40% to 15/25/35/45%", b([10, 20, 30, 40], [15, 25, 35, 45])))
W(ul_close())
W(ability("Marksmanship", slug="drow_ranger_marksmanship"))
W(ul_open())
W(li("Disable range decreased from 400 to 325", b(400, 325)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Gust Costs No Mana replaced with -25% Frost Arrows Mana Cost", t("REWORK")))
W(ul_close())

# Earth Spirit
W(hero_header("Earth Spirit"))
W(ul_open())
W(li("Base Damage decreased by 6", bstat_h("Earth Spirit", "AttackDamageMin", "7.39e", -6), extra=note_box(hero="Earth Spirit", field="AttackDamageMin", before_patch="7.39e")))
W(li("Damage at level 1 decreased from 53–57 to 47–51", br(53, 57, 47, 51)))
W(ul_close())
W(facet_header("earth_spirit_resonance"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("earth_spirit_stepping_stone"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("earth_spirit_ready_to_roll"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Stone Remnant", slug="earth_spirit_stone_caller"))
W(ul_open())
W(li("Now passively grants +2.5% bonus attack damage per currently unused charge", t("NEW")))
W(li("Whenever Earth Spirit uses another ability on Stone Remnant, he gains +7.5% bonus attack damage for 10s (effect doesn't stack)", t("NEW")))
W(li_formula("Max Ability Charges increased",
             "7 + 1 additional charge at every 5th level",
             "7 + 1 per 4 hero level ups",
             lambda L: 7 + L // 5,
             lambda L: 7 + L // 4,
             levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30]))
W(ul_close())
W(ability("Boulder Smash", slug="earth_spirit_boulder_smash"))
W(ul_open())
W(li("Cooldown rescaled from 22/18/14/10s to 20/17/14/11s", b([22, 18, 14, 10], [20, 17, 14, 11], l=True)))
W(ul_close())
W(ability("Geomagnetic Grip", slug="earth_spirit_geomagnetic_grip"))
W(ul_open())
W(li("Aghanim's Shard reworked. Can now target allied units by default with 550/600/650/700 cast range.", t("NEW"), extra=inline_note("Aghanim's Shard rework: Decreases cooldown by 3s and increases allied unit cast range and speed by 50%<br><br>Can't pull allies that are affected by Leash, Root, Bind, Duel, Chronosphere or Black Hole")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent -3s Geomagnetic Grip Cooldown replaced with -2s Boulder Smash Cooldown", t("REWORK")))
W(li("Level 20 Talent +180 Rolling Boulder Damage replaced with +175% Rolling Boulder Damage from Strength", t("REWORK")))
W(li("Level 25 Talent -3s Boulder Smash Cooldown replaced with +175 Geomagnetic Grip Remnant Damage", t("REWORK")))
W(li("Level 25 Talent Magnetize Undispellable replaced with Earth Spirit Magnetizes Himself", t("REWORK"), extra=inline_note("Applies Magnetize at its current duration to enemy Heroes around Earth Spirit, and can be refreshed with Stone Remnants")))
W(ul_close())

# Earthshaker
W(hero_header("Earthshaker"))
W(ability("Fissure", slug="earthshaker_fissure"))
W(ul_open())
W(li("Damage decreased from 110/170/230/290 to 100/160/220/280", b([110, 170, 230, 290], [100, 160, 220, 280])))
W(li("Aghanim's Shard no longer allows Fissure walking", t("DEL")))
W(ul_close())
W(ability("Echo Slam", slug="earthshaker_echo_slam"))
W(ul_open())
W(li("Echo Damage decreased from 90/100/110 to 70/90/110", b([90, 100, 110], [70, 90, 110])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Enchant Totem Damage increased from +50% to +65%", b(50, 65)))
W(ul_close())

# Elder Titan
W(hero_header("Elder Titan"))
W(ability("Astral Spirit", slug="elder_titan_ancestral_spirit"))
W(ul_open())
W(li("Return Astral Spirit and Move Astral Spirit sub-abilities can now be used while Elder Titan is disabled", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Astral Spirit Move Speed Per Hero increased from +2% to +2.5%", b(2, 2.5)))
W(li("Level 20 Talent Natural Order Radius increased from +100 to +150", b(100, 150)))
W(ul_close())

# Ember Spirit
W(hero_header("Ember Spirit"))
W(ability("Flame Guard", slug="ember_spirit_flame_guard"))
W(ul_open())
W(li("Cooldown decreased from 35s to 32s", b(35, 32, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Searing Chains Duration decreased from +1s to +0.8s", b(1, 0.8)))
W(li("Level 20 Talent Searing Chains Damage decreased from +60 to +50", b(60, 50)))
W(ul_close())

# Enchantress
W(hero_header("Enchantress"))
W(facet_header("enchantress_overprotective_wisps"))
W(ul_open())
W(li("Nature's Attendants Wisp maximum decreased from 4 to 3", b(4, 3)))
W(ul_close())
W(ability("Rabble-Rouser", slug="enchantress_rabblerouser"))
W(ul_open())
W(li_formula("Damage amplification changed",
             "10% + 4% per Enchantress level", "4% + 4% per Enchantress level up",
             lambda L: 10 + 4 * L, lambda L: 4 + 4 * L,
             value_fmt="{:g}%"))
W(li("Now also affects units that come under Enchantress' control", t("NEW")))
W(ul_close())
W(ability("Enchant", slug="enchantress_enchant"))
W(ul_open())
W(li("Creep Attack Damage Bonus decreased from 0/25/50/75 to 0/20/40/60", b([0, 25, 50, 75], [0, 20, 40, 60])))
W(li("Enchanted units may now be bound to a persistent hotkey", t("QoL")))
W(ul_close())
W(ability("Little Friends", slug="enchantress_little_friends"))
W(ul_open())
W(li("Affected creeps now gain damage buff from Rabble-Rouser for the duration in case they did not have it", t("MISC")))
W(li("Bonus Attack Speed decreased from 100 to 70", b(100, 70)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +10 Enchanted Creep Armor replaced with +5 Armor for Enchantress and her units", t("REWORK"), extra=inline_note("Requires at least 1 level of Enchant")))
W(li("Level 20 Talent +60 Untouchable Attack Slow replaced with +9 Nature's Attendants Wisps", t("REWORK")))
W(li("Level 25 Talent +12 Nature's Attendants Wisps replaced with +70 Untouchable Attack Slow", t("REWORK")))
W(ul_close())

# Enigma
W(hero_header("Enigma"))
W(ability("Malefice", slug="enigma_malefice"))
W(ul_open())
W(li("Aghanim's Shard now also spawns an Eidolon if the target dies before the effect expires", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Malefice Instance Damage increased from +50 to +60", b(50, 60)))
W(ul_close())

# Faceless Void
W(hero_header("Faceless Void"))
W(ability("Time Dilation", slug="faceless_void_time_dilation"))
W(ul_open())
W(li("Now always applies one instance of damage and slow in addition to the per cooldown instances", t("NEW")))
W(li("Slow per cooldown decreased from 7/8/9/10% to 4/5/6/7%", b([7, 8, 9, 10], [4, 5, 6, 7], l=True)))
W(li("DPS per cooldown decreased from 7/9/11/13 to 4/6/8/10", b([7, 9, 11, 13], [4, 6, 8, 10], l=True)))
W(li("Duration decreased from 8/9/10/11s to 7/8/9/10s", b([8, 9, 10, 11], [7, 8, 9, 10])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Time Dilation DPS Per Cooldown decreased from +9 to +6", b(9, 6, l=True)))
W(li("Level 15 Talent Time Dilation Slow per Cooldown decreased from +12% to +8%", b(12, 8, l=True)))
W(ul_close())

# Grimstroke
W(hero_header("Grimstroke"))
W(ability("Phantom's Embrace", slug="grimstroke_ink_creature"))
W(ul_open())
W(li("Cooldown is now also refreshed if the phantom's target dies before the phantom latches to it", t("NEW")))
W(ul_close())
W(ability("Soulbind", slug="grimstroke_soul_chain"))
W(ul_open())
W(li("Ability can now be reflected", t("NEW"),
     extra=inline_note("Reflected spells get casted onto both units affected by Soulbind")))
W(ul_close())
W(ability("Dark Portrait", slug="grimstroke_dark_portrait"))
W(ul_open())
W(li("Illusion Outgoing Damage decreased from 150% to 125%", b(150, 125)))
W(li("Illusion Damage Taken decreased from 350% to 275%", b(350, 275, l=True)))
W(ul_close())

# Gyrocopter
W(hero_header("Gyrocopter"))
W(facet_header("gyrocopter_afterburner"))
W(ul_open())
W(li("Rocket Barrage movespeed duration decreased from 4.5s to 4s", b(4.5, 4)))
W(ul_close())
W(ability("Call Down", slug="gyrocopter_call_down"))
W(ul_open())
W(li("Missile Damage decreased from 250/425/600 to 200/350/500", b([250, 425, 600], [200, 350, 500])))
W(ul_close())

# Hoodwink
W(hero_header("Hoodwink"))
W(facet_header("hoodwink_hunter"))
W(ul_open())
W(li("Scurry active cast range decreased from 75/150/225/300 to 50/100/150/200", b([75, 150, 225, 300], [50, 100, 150, 200])))
W(li("Active Attack Range decreased from 75/150/225/300 to 50/100/150/200", b([75, 150, 225, 300], [50, 100, 150, 200])))
W(ul_close())
W(ability("Mistwoods Wayfarer", slug="hoodwink_mistwoods_wayfarer"))
W(ul_open())
W(li("Ability can no longer target trees affecting Acorn Shot or Bushwhack", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +1.5 Mana Regen replaced with +150 Health", t("REWORK")))
W(li("Level 10 Talent +1 Scurry Ability Charge replaced with +50 Bushwhack Damage", t("REWORK")))
W(li("Level 15 Talent +60 Bushwhack Damage replaced with +1 Scurry Ability Charge", t("REWORK")))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(facet_header("invoker_wex_focus"))
W(ul_open())
W(li("E.M.P. Aghanim's Shard drag speed decreased from 150 to 125", b(150, 125)))
W(ul_close())
W(ability("Alacrity", slug="invoker_alacrity"))
W(ul_open())
W(li("Mana Cost decreased from 90 to 75", b(90, 75, l=True)))
W(li("Cast Range increased from 650 to 700", b(650, 700)))
W(ul_close())
W(ability("Ice Wall", slug="invoker_ice_wall"))
W(ul_open())
W(li_formula("Damage increased",
             "25 + 5 × Exort Level", "24 + 6 × Exort Level",
             lambda E: 25 + 5 * E, lambda E: 24 + 6 * E,
             levels=list(range(1, 11)), level_prefix='E',
             value_fmt="{:g}"))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Cold Snap Cooldown Reduction increased from 5s to 6s", b(5, 6)))
W(li("Level 20 Talent +35 Alacrity Damage/Speed changed to +50", t("MISC")))
W(ul_close())

# Io
W(hero_header("Io"))
W(ul_open())
W(li("Base Strength increased from 17 to 19", b(17, 19)))
W(li("Base Intelligence decreased from 23 to 21", b(23, 21), extra=inline_note("Damage at level 1 unchanged (45–51)")))
W(ul_close())
W(ability("Spirits", slug="wisp_spirits"))
W(ul_open())
W(li("Mana Cost decreased from 100/110/120/130 to 90/100/110/120", b([100, 110, 120, 130], [90, 100, 110, 120], l=True)))
W(li("Cooldown decreased from 22/21/20/19s to 15s", b([22, 21, 20, 19], 15, l=True)))
W(li("Duration decreased from 19s to 15s", b(19, 15)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +12 Attack Damage to Tethered Units replaced with +7 Strength", t("REWORK")))
W(li("Level 15 Talent +60 Spirits Hero Damage replaced with +50% Spirits Damage", t("REWORK")))
W(li("Level 25 Talent Unslowable during Overcharge replaced with -1.5s Relocate Cast Delay", t("REWORK")))
W(ul_close())

# Jakiro
W(hero_header("Jakiro"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent -2s Dual Breath Cooldown replaced with +60 Ice Path Base Damage", t("REWORK")))
W(li("Level 10 Talent +150 Attack Range replaced with +30 Liquid Fire Attack Speed Slow", t("REWORK")))
W(li("Level 15 Talent +60 Ice Path Base Damage replaced with -3s Dual Breath Cooldown", t("REWORK")))
W(li("Level 15 Talent +50 Liquid Fire Attack Speed Slow replaced with +175 Attack Range", t("REWORK")))
W(li("Level 25 Talent Liquid Frost and Fire Max Health Damage increased from +2.5% to +3%", b(2.5, 3)))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
W(ul_open())
W(li("Base Agility decreased from 34 to 32", b(34, 32)))
W(li("Damage at level 1 decreased from 56–58 to 54–56", br(56, 58, 54, 56)))
W(ul_close())
W(ability("Blade Fury", slug="juggernaut_blade_fury"))
W(ul_open())
W(li("Mana Cost increased from 105/110/115/120 to 120", b([105, 110, 115, 120], 120, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Healing Ward Hits to Kill decreased from +2 to +1", b(2, 1)))
W(ul_close())

# Keeper of the Light
W(hero_header("Keeper of the Light"))
W(ul_open())
W(li("Base Intelligence increased from 23 to 24", b(23, 24)))
W(li("Damage at level 1 increased from 43–50 to 44–51", br(43, 50, 44, 51)))
W(ul_close())
W(ability("Blinding Light", slug="keeper_of_the_light_blinding_light"))
W(ul_open())
W(li("Damage increased from 85/130/175/220 to 90/140/190/240", b([85, 130, 175, 220], [90, 140, 190, 240])))
W(ul_close())
W(ability("Chakra Magic", slug="keeper_of_the_light_chakra_magic"))
W(ul_open())
W(li("Mana Restore increased from 75/150/225/300 to 90/160/230/300", b([75, 150, 225, 300], [90, 160, 230, 300])))
W(ul_close())
W(ability("Will-O-Wisp", slug="keeper_of_the_light_will_o_wisp"))
W(ul_open())
W(li("Damage increased from 75 to 85", b(75, 85)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent -5s Blinding Light Cooldown replaced with +90 Blinding Light Damage", t("REWORK")))
W(ul_close())

# Kez
W(hero_header("Kez"))
W(ul_open())
W(li("Base Strength increased from 19 to 20", b(19, 20)))
W(ul_close())
W(ability("Switch Discipline", slug="kez_switch_weapons"))
W(ul_open())
W(li_formula("Cooldown reduction per level increased from 0.2s to 0.25s. Cooldown changed",
             "8s − 0.2s per level", "8s − 0.25s per level",
             lambda L: 8 - 0.2 * L, lambda L: 8 - 0.25 * L, l=True,
             value_fmt="{:g}s"))
W(li("Katana Base Attack Time improved from 2.0s to 1.8s", b(2.0, 1.8, l=True)))
W(li("Katana Bonus Agility Base Damage decreased from 20% to 12%", b(20, 12)))
W(ul_close())
W(ability("Kazurai Katana", slug="kez_kazurai_katana"))
W(ul_open())
W(li("Damage per second rescaled from 5/7/9/11 to 3/6/9/12%", b([5, 7, 9, 11], [3, 6, 9, 12])))
W(li("The active effect may only trigger up to a maximum of 500 stacks", t("REWORK")))
W(li("Aghanim's Shard now also increases Max Stacks to 1000 and stack as burst damage from 50% to 100%", t("REWORK")))
W(ul_close())
W(ability("Falcon Rush", slug="kez_falcon_rush"))
W(ul_open())
W(li("No longer causes Kez to have a fixed attack rate or any interaction with attack speed", t("NEW")))
W(li("Echo Attack Damage decreased from 45/55/65/75% to 35/40/45/50%", b([45, 55, 65, 75], [35, 40, 45, 50])))
W(li("Echoes now have 50% reduced chance to proc random effects", t("NERF"), extra=inline_note("Echo with Maelstrom (25% chance) will have a 12.5% chance to proc its passive")))
W(li("Echoes can no longer trigger Marks, but may still create them", t("NERF"), extra=inline_note("However, their chance to mark will be reduced from 18% to 9% due to the proc chance change mentioned before")))
W(li("Rush Speed decreased from 1000 to 850", b(1000, 850)))
W(ul_close())
W(ability("Shodo Sai", slug="kez_shodo_sai"))
W(ul_open())
W(li("Marked Stun Duration decreased from 0.5s to 0.4s", b(0.5, 0.4)))
W(li("Parry Stun Duration decreased from 0.5s to 0.4s", b(0.5, 0.4)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +50% Attack Damage Added to Talon Toss replaced with +60 Attack Speed During Falcon Rush", t("REWORK")))
W(ul_close())

# Kunkka
W(hero_header("Kunkka"))
W(ability("Torrent", slug="kunkka_torrent"))
W(ul_open())
W(li("Damage increased from 80/160/240/320 to 110/180/250/320", b([80, 160, 240, 320], [110, 180, 250, 320])))
W(ul_close())
W(ability("X Marks the Spot", slug="kunkka_x_marks_the_spot"))
W(ul_open())
W(li("Cooldown decreased from 30/24/18/12s to 24/20/16/12s", b([30, 24, 18, 12], [24, 20, 16, 12], l=True)))
W(ul_close())

# Legion Commander
W(hero_header("Legion Commander"))
W(ability("Press The Attack", slug="legion_commander_press_the_attack"))
W(ul_open())
W(li("Mana Cost decreased from 110 to 100", b(110, 100, l=True)))
W(ul_close())
W(ability("Moment of Courage", slug="legion_commander_moment_of_courage"))
W(ul_open())
W(li("Cooldown rescaled from 1.9/1.5/1.1/0.7s to 1.7/1.4/1.1/0.8s", b([1.9, 1.5, 1.1, 0.7], [1.7, 1.4, 1.1, 0.8], l=True, force_overall="buff")))
W(ul_close())

# Leshrac
W(hero_header("Leshrac"))
W(facet_header("leshrac_misanthropy"))
W(ul_open())
W(li("Diabolic Edict duration increased from 6s to 7.5s", b(6, 7.5)))
W(ul_close())
W(ability("Split Earth", slug="leshrac_split_earth"))
W(ul_open())
W(li("Radius increased from 135/160/185/210 to 150/170/190/210", b([135, 160, 185, 210], [150, 170, 190, 210])))
W(ul_close())

# Lina
W(hero_header("Lina"))
W(ul_open())
W(li("Intelligence gain increased from 3.8 to 4.0", b(3.8, 4)))
W(ul_close())
W(ability("Laguna Blade", slug="lina_laguna_blade"))
W(ul_open())
W(li("Cast Range increased from 600 to 750", b(600, 750)))
W(ul_close())

# Lion
W(hero_header("Lion"))
W(ability("Hex", slug="lion_voodoo"))
W(ul_open())
W(li("Mana Cost decreased from 125/150/175/200 to 110/140/170/200", b([125, 150, 175, 200], [110, 140, 170, 200], l=True)))
W(ul_close())
W(ability("Finger of Death", slug="lion_finger_of_death"))
W(ul_open())
W(li("Cooldown decreased from 130/85/40s to 120/80/40s", b([130, 85, 40], [120, 80, 40], l=True)))
W(ul_close())

# Lone Druid
W(hero_header("Lone Druid"))
W(ul_open())
W(li("Base Movement Speed decreased from 325 to 295", b(325, 295)))
W(li("Base Damage increased by 4", bstat_h("Lone Druid", "AttackDamageMin", "7.39e", 4), extra=note_box(hero="Lone Druid", field="AttackDamageMin", before_patch="7.39e")))
W(li("Damage at level 1 increased from 38–42 to 42–46", br(38, 42, 42, 46)))
W(ul_close())
W(facet_header("lone_druid_bear_with_me"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("lone_druid_bear_necessities"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Gift Bearer", innate=True))
W(ul_open())
W(li("Innate ability removed. Its effect is now a part of Summon Spirit Bear ability", t("DEL")))
W(ul_close())
W(ability("Summon Spirit Bear", slug="lone_druid_spirit_bear"))
W(ul_open())
W(li("Moved to an innate ability. Cannot be leveled up", t("REWORK")))
W(li("Ability is moved to the 4th ability slot", t("MISC"), extra=inline_note("D key by default")))
W(li("Spirit Bear now counts as a melee hero for most spells", t("REWORK"), extra=inline_note("Since the bear is now a hero, all unit-related changes moved to a separate Spirit Bear section below. This section is for the summon ability changes only")))
W(li("Cooldown decreased from 150/140/130/120s to 120s", b([150, 140, 130, 120], 120, l=True)))
W(ul_close())
W(ability_change(
    old=None,
    new=dict(
        name="Entangle",
        slug="lone_druid_entangle",
        desc=[
            "New Point Targeted basic ability. Pierces Debuff Immunity.",
            "Allows Lone Druid to Entangle enemies once they gain 5 stacks of this ability. Entangled enemies are unable to move for <b>1.2/1.6/2/2.4s</b> and take <b>60/70/80/90</b> damage per second. On cast, applies 2 stacks to each enemy hero and 5 stacks to enemy creeps in the area, and empowers Lone Druid for 10s (1 stack per attack on enemy heroes). Enemies are protected from gaining new stacks while already Entangled. Radius: 350. Stack Duration: 10s. Cast Range: 700. Mana Cost: 60. Cooldown: 24/22/20/18s.",
            "Spirit Bear's Entangling Claws now levels up with this ability and is permanently empowered."
            + inline_note("The Empowered Buff and the enemy stack-counter debuff are undispellable; the Entangled debuff is dispellable. Creeps gain stacks only on cast (not from attacks); Roshan is affected as a hero."),
            aghs_line("Increases radius to 450 and hero stacks on cast to 5, instantly Entangling them. Also removes stack protection from Entangled enemies."),
        ],
    ),
    summary="New ability.",
    tag="new",
))
W(ability("Spirit Link", slug="lone_druid_spirit_link"))
W(ul_open())
W(li("No longer grants attack speed or shared armor", t("DEL")))
W(li("Now also passively grants +10/20/30/40 movement speed to Lone Druid and +20/40/60/80 to his Spirit Bear", t("NEW")))
W(li("Lone Druid's attacks now heal the Spirit Bear by default", t("NEW")))
W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
W(ul_close())
W(ability("True Form", slug="lone_druid_true_form"))
W(ul_open())
W(li("Mana Cost decreased from 200 to 80", b(200, 80, l=True)))
W(li("Duration decreased from 40s to 25s", b(40, 25)))
W(li("Cooldown decreased from 100s to 60/55/50s", b(100, [60, 55, 50], l=True)))
W(li("No longer grants Entangling Claws and Demolish to Lone Druid", t("DEL")))
W(li("Now also provides 50/90/130 bonus attack damage", t("NEW")))
W(li("Bonus Armor increased from 8/10/12 to 10/15/20", b([8, 10, 12], [10, 15, 20])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +30 Spirit Bear Movement Speed replaced with +15 Entangle Root Damage Per Second", t("REWORK")))
W(li("Level 10 Talent +200 Health replaced with -25s Summon Spirit Bear Cooldown", t("REWORK")))
W(li("Level 15 Talent +7 Spirit Bear Armor replaced with +12 Agility", t("REWORK")))
W(li("Level 20 Talent +30 Entangling Claws DPS replaced with +55 Attack Speed", t("REWORK")))
W(li("Level 25 Talent +45 Spirit Link Attack Speed replaced with +0.6s Entangle Root Duration (also affects Spirit Bear's Entangling Claws)", t("REWORK")))
W(li("Level 25 Talent -50s True Form Cooldown replaced with True Form provides 60% Slow Resistance", t("REWORK")))
W(ul_close())

# Spirit Bear (Lone Druid pet)
W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
# One NEW headline row (stats rescale) → old/new stat panes right under it,
# then ONE umbrella row whose show_list collapses every hero-status
# consequence (deliberate exception to the "info, not show_list" rule —
# 8 separate tagged rows here were pure noise).
W(ul_open())
W(li("Now a Universal melee hero instead of a creep — base stats rescaled accordingly", t("NEW")))
W(ul_close())
# Old creep-Bear stats (per Summon Spirit Bear rank 1-4) → new hero-Bear flat
# stats, side by side with per-rank %-deltas. Row N of the old pane aligns
# with row N of the new pane (properties_change subgrid).
W(properties_change(
    old=[
        ("NERF", "Base Health: 1100/1400/1700/2000"),
        ("NERF", "Base Health Regen: 5/6/7/8"),
        ("BUFF", "Base Attack Time: 1.75/1.65/1.55/1.45s"),
        ("BUFF", "Base Attack Speed: 100"),
        ("NERF", "Base Armor: 0/2/4/6"),
        ("NERF", "Base Movement Speed: 300/330/360/390"),
        ("BUFF", "Base Magic Resistance: 0%"),
        ("BUFF", "Daytime Vision Range: 1400"),
        ("DEL",  "Gains 100 Health and 5 Damage per level"),
    ],
    new=[
        ("", "Base Health: 1500", b([1100, 1400, 1700, 2000], 1500)),
        ("", "Base Health Regen: 3", b([5, 6, 7, 8], 3)),
        ("", "Base Attack Time: 1.5s", b([1.75, 1.65, 1.55, 1.45], 1.5, l=True)),
        ("", "Base Attack Speed: 110", b(100, 110)),
        ("", "Base Armor: 0", b([0, 2, 4, 6], 0)),
        ("", "Base Movement Speed: 310", b([300, 330, 360, 390], 310)),
        ("", "Base Magic Resistance: 25%"
             + inline_note("Demolish ability no longer passively grants 33% magic resistance")),
        ("", "Daytime Vision Range: 1800", b(1400, 1800)),
        ("NEW", "Gains 4.5 Strength, 4.5 Agility and 0.5 Intelligence per level"
                + inline_note("Still has no base attributes, so they are all zeroes at level 1")),
    ],
))
W(ul_open())
W(li("Now interacts with other spells, mechanics and game systems as a hero", t("NEW"),
     extra=show_list(
         "Attacks now count as melee hero attacks against: Roshan's Banner, Clinkz' Skeleton Archers, Lich's Ice Spire, Phoenix's Supernova, Pugna's Nether Ward, Templar Assassin's Psionic Traps, and Undying's Tombstone (already did hero damage to Shadow Shaman's Mass Serpent Wards, Couriers, Observer Wards and Sentry Wards)",
         "Can now be targeted or affected as a hero by: Axe's Culling Blade, Bounty Hunter's Track, Earth Spirit's Petrify, Legion Commander's Duel, Lion's Finger of Death, Mars' Spear of Mars, Necrophos' Reaper's Scythe, Slark's Pounce, Terrorblade's Reflection, Terrorblade's Sunder (only if the Bear is not Debuff Immune), and Underlord's Atrophy Aura",
         "At the same time, Bounty Hunter will not steal Lone Druid's gold anymore by hitting Spirit Bear with Jinada or by using skills with Cutpurse facet on it",
         "Death will not provide charges for: Urn of Shadows and its upgrades, Pudge's permanent Strength from Flesh Heap, Silencer's permanent Int from Brain Drain, Slark's permanent Agility from Essence Shift, and Storm Spirit's stacks for Galvanized (temporary attribute losses from Silencer's, Slark's and other similar spells still work)",
         "Can now capture Watchers and Outposts",
         "Can now break enemy Smoke of Deceit",
         "Starts with a Town Portal Scroll on cooldown the first time it is summoned",
         "Receives a copy of Lone Druid's Neutral Item with an independent cooldown",
         "Has a separate Talent Tree",
         summary="Show all interactions")))
# Ability order, old → new: bare square ability icons in a single flow row
# (hover = name), arrow between the groups. NEW-in-7.40 Spirit Link gets the
# purple ring; the hidden innate Demolish is dimmed.
def _ao_icon(name, slug, new=False, dim=False, note=None):
    cls = "ao-icon" + (" is-new" if new else "") + (" is-dim" if dim else "")
    tip = name + (f" ({note})" if note else "")
    return (f'<span class="{cls}" data-tooltip="{_html.escape(tip, quote=True)}">'
            f'<img src="{ABIL_CDN}{slug}.png" alt="" loading="lazy"></span>')
W(li("Ability order has been changed", t("MISC"), extra=(
    '<div class="ability-order-flow">'
    + '<div class="ao-group">'
    + _ao_icon("Return", "lone_druid_spirit_bear_return")
    + _ao_icon("Demolish", "lone_druid_spirit_bear_demolish")
    + _ao_icon("Savage Roar", "lone_druid_savage_roar")
    + _ao_icon("Entangling Claws", "lone_druid_spirit_bear_entangle")
    + _ao_icon("Fetch", "lone_druid_spirit_bear_fetch")
    + '</div>'
    + '<span class="ao-arrow">→</span>'
    + '<div class="ao-group">'
    + _ao_icon("Demolish", "lone_druid_spirit_bear_demolish", dim=True, note="innate, hidden")
    + _ao_icon("Return", "lone_druid_spirit_bear_return")
    + _ao_icon("Entangling Claws", "lone_druid_spirit_bear_entangle")
    + _ao_icon("Savage Roar", "lone_druid_savage_roar")
    + _ao_icon("Spirit Link", "lone_druid_spirit_link", new=True, note="new")
    + _ao_icon("Fetch", "lone_druid_spirit_bear_fetch")
    + '</div>'
    + '</div>')))
W(ul_close())
W(ability("Demolish", slug="lone_druid_spirit_bear_demolish"))
W(ul_open())
W(li("Ability is now Innate to Spirit Bear", t("NEW")))
W(li("Bonus Building Damage rescaled from 10/20/30/40% to 30%", b([10, 20, 30, 40], 30)))
W(li("No longer passively grants 33% magic resistance", t("DEL")))
W(ul_close())
W(ability("Return", slug="lone_druid_spirit_bear_return"))
W(ul_open())
W(li("Now considered a Teleport for the \"Teleport Requires Hold/Cancel to Stop\" option", t("QoL")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Entangling Claws",
        slug="lone_druid_spirit_bear_entangle",
        desc=[
            "Passive.",
            "Spirit Bear's attacks have a chance to root the target (Entangle), preventing movement for <b>1/1.6/2.2/2.8s</b> and dealing damage over the duration.",
        ],
    ),
    new=dict(
        name="Entangling Claws",
        slug="lone_druid_spirit_bear_entangle",
        desc=[
            "Passive. Pierces Debuff Immunity. Levels up with Lone Druid's Entangle.",
            "Allows Spirit Bear to Entangle enemies once they gain 5 stacks of this ability. Entangled enemies are unable to move for <b>1.2/1.6/2/2.4s</b> and take <b>60/70/80/90</b> damage per second. Spirit Bear's attacks are permanently empowered, applying 1 stack with each attack on enemy heroes. Enemies are protected from gaining new stacks while already Entangled."
            + inline_note("Stacks are applied only to heroes, creep heroes and Roshan."),
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ability("Fetch", slug="lone_druid_spirit_bear_fetch"))
W(ul_open())
W(li("After fetching an enemy, Spirit Bear will now have an attack command issued towards the target", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talents: +10% Magic Resistance OR +20 Movement Speed", t("NEW")))
W(li("Level 15 Talents: +4 Armor OR Return Has No Cooldown and -0.5s Channel Time", t("NEW")))
W(li("Level 20 Talents: +500 Health OR +30 Damage", t("NEW")))
W(li("Level 25 Talents: +15% Damage to Entangled Units OR +20% Demolish Bonus Building Damage", t("NEW")))
W(ul_close())

# Luna
W(hero_header("Luna"))
W(ability("Lunar Orbit", slug="luna_lunar_orbit"))
W(ul_open())
W(li("Collision Damage increased from 22/28/34/40% to 28/32/36/40%", b([22, 28, 34, 40], [28, 32, 36, 40])))
W(li("Formation time decreased from 1.2s to 0.9s", b(1.2, 0.9, l=True)))
W(li("Rotation Radius decreased from 250 to 225", t("BUFF"),
     extra=inline_note("Not a nerf: combined with the Collision Radius increase, the outer reach is unchanged (250+175 = 225+200 = 425), while the dead zone right next to Luna shrinks from 75 to 25 — coverage shifts closer to her")))
W(li("Collision Radius increased from 175 to 200", b(175, 200)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent -40s Eclipse Cooldown replaced with +80 Lucent Beam Damage", t("REWORK")))
W(li("Level 20 Talent +110 Lucent Beam Damage replaced with -40s Eclipse Cooldown", t("REWORK")))
W(li("Level 25 Talent +1 Lunar Blessing Damage per Level replaced with +30 Lunar Blessing Damage", t("REWORK")))
W(ul_close())

# Lycan
W(hero_header("Lycan"))
W(ability("Summon Wolves", slug="lycan_summon_wolves"))
W(ul_open())
W(li("Wolf Damage decreased from 23/29/35/41/47/53 to 22/28/34/40/46/52", b([23, 29, 35, 41, 47, 53], [22, 28, 34, 40, 46, 52])))
W(ul_close())
W(ability("Shapeshift", slug="lycan_shapeshift"))
W(ul_open())
W(li("Health Bonus decreased from 250/350/450 to 225/325/425", b([250, 350, 450], [225, 325, 425])))
W(ul_close())

# Magnus
W(hero_header("Magnus"))
W(ul_open())
W(li("Base Damage increased by 1", bstat_h("Magnus", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Magnus", field="AttackDamageMin", before_patch="7.39e")))
W(li("Damage at level 1 increased from 54–62 to 55–63", br(54, 62, 55, 63)))
W(ul_close())
W(facet_header("magnataur_diminishing_return"))
W(ul_open())
W(li("No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
W(ul_close())
W(ability("Reverse Polarity", slug="magnataur_reverse_polarity"))
W(ul_open())
W(li("Cooldown decreased from 120s to 115s", b(120, 115, l=True)))
W(ul_close())

# Marci
W(hero_header("Marci"))
W(facet_header("marci_fleeting_fury"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())

# Mars
W(hero_header("Mars"))
W(ability("God's Rebuke", slug="mars_gods_rebuke"))
W(ul_open())
W(li("Bonus Damage vs Heroes decreased from 10/15/20/25 to 5/10/15/20", b([10, 15, 20, 25], [5, 10, 15, 20])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Arena of Blood Cooldown Reduction decreased from 20s to 16s", b(20, 16)))
W(ul_close())

# Medusa
W(hero_header("Medusa"))
W(ability("Mana Shield", slug="medusa_mana_shield"))
W(ul_open())
W(li("No longer benefits from mana cost reduction effects", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +1.5s Stone Gaze Duration replaced with +1 Gorgon's Grasp Volley", t("REWORK")))
W(li("Level 25 Talent +1 Gorgon's Grasp Volley replaced with +2s Stone Gaze Duration", t("REWORK")))
W(ul_close())

# Meepo
W(hero_header("Meepo"))
W(facet_header("meepo_more_meepo"))
W(ul_open())
W(li("No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
W(ul_close())

# Mirana
W(hero_header("Mirana"))
W(facet_header("mirana_starstruck"))
W(ul_open())
W(li("Starstorm second meteor damage decreased from 100% to 70/80/90/100%", b(100, [70, 80, 90, 100])))
W(ul_close())
W(ability("Starstorm", slug="mirana_starfall"))
W(ul_open())
W(li("Second Meteor Damage increased from 60% to 70%", b(60, 70)))
W(ul_close())
W(ability("Moonlight Shadow", slug="mirana_invis"))
W(ul_open())
W(li("Cooldown decreased from 140/120/100s to 120/110/100s", b([140, 120, 100], [120, 110, 100], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent -20s Moonlight Shadow Cooldown replaced with +200 Starstorm Damage", t("REWORK")))
W(li("Level 25 Talent +250 Starstorm Damage replaced with -30s Moonlight Shadow Cooldown", t("REWORK")))
W(ul_close())

# Monkey King
W(hero_header("Monkey King"))
W(ul_open())
W(li("Base Armor decreased by 1", bstat_h("Monkey King", "ArmorPhysical", "7.39e", -1), extra=note_box(hero="Monkey King", field="ArmorPhysical", before_patch="7.39e")))
W(li("Base Attack Time improved from 1.7s to 1.6s", b(1.7, 1.6, l=True)))
W(li("Base Attack Speed decreased from 100 to 95", b(100, 95)))
W(ul_close())
W(facet_header("monkey_king_simian_stride"))
W(ul_open())
W(li("No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
W(ul_close())
W(ability("Tree Dance", slug="monkey_king_tree_dance"))
W(ul_open())
W(li("Stun duration from falling off the cut tree decreased from 4s to 3s", b(4, 3)))
W(ul_close())

# Morphling
W(hero_header("Morphling"))
W(facet_header("morphling_str"))
W(ul_open())
W(li("Adaptive Strike stun is no longer exclusive to this facet", t("MISC")))
W(ul_close())
W(ability("Adaptive Strike", slug="morphling_adaptive_strike_agi"))
W(ul_open())
W(li("Cast Range decreased from 600/700/800/900 to 600/675/750/825", b([600, 700, 800, 900], [600, 675, 750, 825])))
W(li("Now stuns the target for 0.5s and up to 1.2/1.6/2.0/2.4s when Morphling's Strength is 50% higher than his Agility", t("NEW")))
W(ul_close())

# Muerta
W(hero_header("Muerta"))
W(ul_open())
W(li("Intelligence gain increased from 3.4 to 3.6", b(3.4, 3.6)))
W(ul_close())
W(ability("The Calling", slug="muerta_the_calling"))
W(ul_open())
W(li("Mana Cost decreased from 140/155/170/185 to 135/150/165/180", b([140, 155, 170, 185], [135, 150, 165, 180], l=True)))
W(li("Cast Range increased from 580 to 600", b(580, 600)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +150 Health replaced with +20 Attack Speed", t("REWORK")))
W(ul_close())

# Naga Siren
W(hero_header("Naga Siren"))
W(ul_open())
W(li("Base Intelligence decreased from 20 to 19", b(20, 19)))
W(li("Agility gain increased from 3.3 to 3.4", b(3.3, 3.4)))
W(ul_close())
W(facet_header("naga_siren_passive_riptide"))
W(ul_open())
W(li("Rip Tide damage increased from 25/35/45/55 to 30/40/50/60", b([25, 35, 45, 55], [30, 40, 50, 60])))
W(ul_close())
W(facet_header("naga_siren_active_riptide"))
W(ul_open())
W(li("Cooldown increased from 10/9/8/7s to 13/11/9/7s", b([10, 9, 8, 7], [13, 11, 9, 7], l=True)))
W(ul_close())
W(ability("Ensnare", slug="naga_siren_ensnare"))
W(ul_open())
W(li("Can no longer target invulnerable units unless this invulnerability is provided by Song of the Siren", t("REWORK")))
W(ul_close())
W(ability("Song of the Siren", slug="naga_siren_song_of_the_siren"))
W(ul_open())
W(li("Max HP Regen per second decreased from 2/3/4% to 1/2/3%", b([2, 3, 4], [1, 2, 3])))
W(li("Aghanim's Shard Max HP Regen per second bonus decreased from 2% to 1%", b(2, 1), extra=inline_note("Total Max HP Regen per second with Aghanim's Shard decreased from 4/5/6% to 2/3/4%")))
W(ul_close())

# Nature's Prophet
W(hero_header("Nature's Prophet"))
W(ul_open())
W(li("Agility gain decreased from 3 to 2.6", b(3, 2.6)))
W(li("Damage gain per level decreased from 4.1 to 3.9", b(4.1, 3.9)))
W(ul_close())
W(ability("Spirit of the Forest", slug="furion_spirit_of_the_forest"))
W(ul_open())
W(li("Bonus damage per tree decreased from 3% to 2%", b(3, 2)))
W(ul_close())
W(ability("Nature's Call", slug="furion_force_of_nature"))
W(ul_open())
W(li("Mana Cost decreased from 120 to 100", b(120, 100, l=True)))
W(li("Treant attack range increased from 100 to 125", b(100, 125)))
W(li("Treant damage increased from 15/23/31/39 to 16/24/32/40", b([15, 23, 31, 39], [16, 24, 32, 40]), extra=inline_note("From 13–17/21–25/29–33/37–41 to 14–18/22–26/30–34/38–42")))
W(li("Treant movement speed increased from 300 to 305/310/315/320", b(300, [305, 310, 315, 320])))
W(ul_close())
W(ability("Curse of the Oldgrowth", slug="furion_curse_of_the_forest"))
W(ul_open())
W(li("Curse radius decreased from 1200 to 900", b(1200, 900)))
W(ul_close())

# Necrophos
W(hero_header("Necrophos"))
W(facet_header("necrolyte_profane_potency"))
W(ul_open())
W(li("Sadist AOE per Kill reduced from 40 to 35", b(40, 35)))
W(ul_close())
W(ability("Reaper's Scythe", slug="necrolyte_reapers_scythe"))
W(ul_open())
W(li("HP Regen per kill decreased from 2/4/6 to 1/2/3", b([2, 4, 6], [1, 2, 3])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Death Pulse Heal increased from +50 to +60", b(50, 60)))
W(li("Level 15 Talent Ghost Shroud Slow decreased from +20% to +15%", b(20, 15)))
W(li("Level 20 Talent Heartstopper Regen Reduction decreased from +25% to +20%", b(25, 20)))
W(ul_close())

# Night Stalker
W(hero_header("Night Stalker"))
W(ability("Heart of Darkness", slug="night_stalker_heart_of_darkness"))  # innate
W(ul_open())
W(li("No longer reduces Night Stalker's health regeneration by 20% during the day", t("BUFF")))
W(ul_close())
W(facet_header("night_stalker_voidbringer"))
W(ul_open())
W(li("No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Crippling Fear DPS increased from +20 to +40", b(20, 40)))
W(ul_close())

# Nyx Assassin
W(hero_header("Nyx Assassin"))
W(ability("Mind Flare", slug="nyx_assassin_jolt"))
W(ul_open())
W(li("Bonus Damage decreased from 20% to 15%", b(20, 15)))
W(ul_close())
W(ability("Spiked Carapace", slug="nyx_assassin_spiked_carapace"))
W(ul_open())
W(li("Stun Duration increased from 0.4/0.8/1.2/1.6s to 0.7/1.0/1.3/1.6s", b([0.4, 0.8, 1.2, 1.6], [0.7, 1.0, 1.3, 1.6])))
W(ul_close())

# Ogre Magi
W(hero_header("Ogre Magi"))
W(ul_open())
W(li("Base Damage increased by 1", bstat_h("Ogre Magi", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Ogre Magi", field="AttackDamageMin", before_patch="7.39e")))
W(li("Damage at level 1 increased from 69–75 to 70–76", br(69, 75, 70, 76)))
W(ul_close())
W(ability("Bloodlust", slug="ogre_magi_bloodlust"))
W(ul_open())
W(li("Cast range increased from 600 to 650", b(600, 650)))
W(li("Can no longer target invulnerable units", t("DEL"), extra=inline_note("Can still target invulnerable buildings (i.e. Tier 2-4 towers when the previous ones are not destroyed)")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Bloodlust Attack Speed increased from +30 to +35", b(30, 35)))
W(ul_close())

# Omniknight
W(hero_header("Omniknight"))
W(ul_open())
W(li("Base Armor increased by 1", bstat_h("Omniknight", "ArmorPhysical", "7.39e", 1), extra=note_box(hero="Omniknight", field="ArmorPhysical", before_patch="7.39e")))
W(ul_close())
W(ability("Repel", slug="omniknight_martyr"))
W(ul_open())
W(li("Cooldown decreased from 55/50/45/40s to 50/45/40/35s", b([55, 50, 45, 40], [50, 45, 40, 35], l=True)))
W(ul_close())
W(ability("Hammer of Purity", slug="omniknight_hammer_of_purity"))
W(ul_open())
W(li("No longer disabled by Silence", t("MISC")))
W(ul_close())
W(ability("Guardian Angel", slug="omniknight_guardian_angel"))
W(ul_open())
W(li("Cooldown decreased from 110/100/90s to 100/90/80s", b([110, 100, 90], [100, 90, 80], l=True)))
W(ul_close())

# Oracle
W(hero_header("Oracle"))
W(ability("Fortune's End", slug="oracle_fortunes_end"))
W(ul_open())
W(li("Can no longer target invulnerable units, but does affect invulnerable units in the AoE", t("MISC")))
W(ul_close())
W(ability("Fate's Edict", slug="oracle_fates_edict"))
W(ul_open())
W(li("No longer has separate effects for allies and enemies", t("REWORK"), extra=inline_note("Always disarms the target and grants them 100% magic damage resistance")))
W(li("Mana Cost decreased from 95/100/105/110 to 70", b([95, 100, 105, 110], 70, l=True)))
W(li("Cooldown decreased from 20/17/14/11s to 17/14/11/8s", b([20, 17, 14, 11], [17, 14, 11, 8], l=True)))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(facet_header("pangolier_double_jump"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("pangolier_thunderbolt"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Swashbuckle", slug="pangolier_swashbuckle"))
W(ul_open())
W(li("Cooldown decreased from 21/18/15/12s to 20/17/14/11s", b([21, 18, 15, 12], [20, 17, 14, 11], l=True)))
W(li("Now briefly slows enemies movespeed on hit by 100% for 0.4s", t("NEW")))
W(ul_close())
W(ability("Shield Crash", slug="pangolier_shield_crash"))
W(ul_open())
W(li("Cooldown decreased from 18/16/14/12s to 16/13/10/7s", b([18, 16, 14, 12], [16, 13, 10, 7], l=True)))
W(li("Mana Cost rescaled from 70/80/90/100 to 75", b([70, 80, 90, 100], 75, l=True)))
W(li("Barrier changed from 50/100/150/200 per enemy hero hit to 60/120/180/240 if any enemy hero is hit", t("REWORK"), extra=inline_note("If no enemy hero was hit, barrier is not provided")))
W(li("Barrier Duration decreased from 10s to 6s", b(10, 6)))
W(li("Damage decreased from 70/130/190/250 to 50/100/150/200", b([70, 130, 190, 250], [50, 100, 150, 200])))
W(li("No longer slows enemies", t("DEL")))
W(li("Aghanim's Scepter Swashbuckle damage decreased from 100% to 75%", b(100, 75)))
W(ul_close())
W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
W(ul_open())
W(li("Duration rescaled from 10s to 9/10/11s", b(10, [9, 10, 11])))
W(li("No longer decreases the cooldown of Shield Crash", t("DEL")))
W(li("Now takes 1 second to reach full Roll Speed", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +90 Shield Crash Barrier Per Hero replaced with +125 Shield Crash Barrier", t("REWORK")))
W(li("Level 15 Talent +15% Attack Damage as Swashbuckle Damage replaced with -2s Swashbuckle Cooldown", t("REWORK")))
W(li("Level 20 Talent +125 Shield Crash Radius and Damage replaced with -1.5s Shield Crash Cooldown", t("REWORK")))
W(li("Level 25 Talent -4s Swashbuckle Cooldown replaced with +20% Attack Damage as Swashbuckle Damage", t("REWORK")))
W(ul_close())

# Phantom Assassin
W(hero_header("Phantom Assassin"))
W(ability("Blur", slug="phantom_assassin_blur"))
W(ul_open())
W(li("Active Movement Speed increased from 3/6/9/12% to 6/9/12/15%", b([3, 6, 9, 12], [6, 9, 12, 15])))
W(ul_close())
W(ability("Phantom Strike", slug="phantom_assassin_phantom_strike"))
W(ul_open())
W(li("11/9/7/5s cooldown replaced with 2 charges with 21/18/15/12s base charge restore time",
     t("REWORK") + b([11, 9, 7, 5], [21, 18, 15, 12], l=True),
     extra=inline_note("% compares time between uses; in exchange Phantom Strike gains a second charge (two casts back-to-back)")))
W(ul_close())

# Phantom Lancer
W(hero_header("Phantom Lancer"))
W(ul_open())
W(li("Agility gain increased from 2.8 to 3.4", b(2.8, 3.4)))
W(ul_close())
W(facet_header("phantom_lancer_divergence"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("phantom_lancer_lancelot"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
_ia_pill, _ia_table = scale_pill("18% + 2% per 3 level ups",
                                 lambda L: 18 + 2 * ((L - 1) // 3),
                                 levels=[1, 5, 10, 15, 20, 25, 30], value_fmt="{:.0f}%")
W(ability_change(
    old=dict(
        name="Illusory Armaments",
        slug="phantom_lancer_illusory_armaments",
        innate=True,
        desc=[
            "Passive.",
            "Bonus attack damage from items is converted into base damage — <b>100%</b> for Phantom Lancer and <b>65%</b> for his illusions — so his illusions benefit from his damage items.",
        ],
    ),
    new=dict(
        name="Illusory Armaments",
        slug="phantom_lancer_illusory_armaments",
        innate=True,
        desc=[
            "Passive.",
            "Whenever an illusion of Phantom Lancer is created, it can't have less than " + _ia_pill + " of Phantom Lancer's damage for 3s.",
        ],
        tables=[_ia_table],
    ),
    summary="Innate reworked.",
    tag="rework",
))
W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
W(ul_open())
W(li("No Longer provides bonus Agility while active", t("DEL")))
W(li("Cooldown rescaled from 13/10/7/4s to 15/11/7/3s", b([13, 10, 7, 4], [15, 11, 7, 3], l=True)))
W(li("Now provides 20/30/40/50% evasion while rushing", t("NEW")))
W(li("No longer has a 2s linger effect", t("DEL"), extra=inline_note("Evasion bonus is lost once the target is reached or the rush is cancelled")))
W(ul_close())
W(ability("Juxtapose", slug="phantom_lancer_juxtapose"))
W(ul_open())
W(li("Illusion Damage decreased from 15/17/19% to 15%", b([15, 17, 19], 15)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +10 Phantom Rush Agility replaced with +3% Juxtapose Illusion Trigger Chance", t("REWORK")))
W(li("Level 15 Talent -1s Spirit Lance Cooldown replaced with +125 Doppelganger Cast Range", t("REWORK")))
W(li("Level 15 Talent +2.5s Phantom Rush Bonus Agility Duration replaced with 50% Illusion Spirit Lance Damage", t("REWORK"), extra=inline_note("Spirit Lances fired from illusions deal 50% of the regular damage, which is then further reduced by the illusion's outgoing damage multiplier")))
W(li("Level 20 Talent +6% Juxtapose Damage replaced with -70% Juxtapose Illusion Damage Taken", t("REWORK")))
W(li("Level 20 Talent +15% Spirit Lance Illusion Damage replaced with +100 Spirit Lance Damage", t("REWORK")))
W(li("Level 25 Talent +20% Illusory Armaments Damage replaced with +2s Illusory Armaments Duration", t("REWORK")))
W(ul_close())

# Phoenix
W(hero_header("Phoenix"))
W(ability("Sun Ray", slug="phoenix_sun_ray"))
W(ul_open())
W(li("Health Cost per second decreased from 6% to 5%", b(6, 5, l=True)))
W(li("Base Damage per second rescaled from 14/20/26/32 to 15/20/25/30", b([14, 20, 26, 32], [15, 20, 25, 30])))
W(li("Max Damage rescaled from 1.25/2.75/4.5/6.75% to 1.5/3/4.5/6%", b([1.25, 2.75, 4.5, 6.75], [1.5, 3, 4.5, 6])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Health Regen increased from +20 to +25", b(20, 25)))
W(ul_close())

# Primal Beast
W(hero_header("Primal Beast"))
W(facet_header("primal_beast_ferocity"))
W(ul_open())
W(li("Pulverize AoE bonus per slam decreased from 25% to 20%", b(25, 20)))
W(ul_close())

# Puck
W(hero_header("Puck"))
W(ability("Puckish", slug="puck_puckish"))
W(ul_open())
W(li("No longer applies when disjointing attacks from buildings", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Waning Rift Cooldown Reduction decreased from 3s to 2.5s", b(3, 2.5)))
W(ul_close())

# Pugna
W(hero_header("Pugna"))
W(facet_header("pugna_siphoning_ward"))
W(ul_open())
W(li("Nether Ward damage to Heal decreased from 25% to 20%", b(25, 20)))
W(li("Nether Ward damage to Mana decreased from 30% to 20%", b(30, 20)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Health decreased from +350 to +300", b(350, 300)))
W(li("Level 20 Talent Life Drain Heal decreased from +20% to +15%", b(20, 15)))
W(li("Level 25 Talent Nether Blast Damage increased from +180 to +200", b(180, 200)))
W(ul_close())

# Queen of Pain
W(hero_header("Queen of Pain"))
W(facet_header("queenofpain_facet_bondage"))
W(ul_open())
W(li("Returning Spell Damage decreased from 20% to 16%", b(20, 16)))
W(ul_close())

# Razor
W(hero_header("Razor"))
W(facet_header("razor_thunderhead"))
W(ul_open())
W(li("Eye of the Storm Storm Surge cooldown reduction decreased from 2.5s to 2s", b(2.5, 2)))
W(ul_close())
W(ability("Storm Surge", slug="razor_storm_surge"))
W(ul_open())
W(li("Chance to Strike increased from 18% to 20%", b(18, 20)))
W(li("Strike Cooldown decreased from 3s to 2.5s", b(3, 2.5, l=True)))
W(ul_close())

# Riki
W(hero_header("Riki"))
W(facet_header("riki_contract_killer"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("riki_exterminator"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Backstab", slug="riki_innate_backstab"))
W(ul_open())
W(li("No longer levels with Cloak and Dagger", t("REWORK")))
W(li_formula("Agility Damage Multiplier rescaled",
             "0.55/0.9/1.25/1.6", "0.6 + 0.05 per Riki's level up",
             lambda L: 1.6, lambda L: 0.6 + 0.05 * L,
             value_fmt="{:g}"))
W(li("Now works on allied units at 25% effectiveness", t("NEW")))
W(li("Damage is now done as a separate instance of damage instead of a part of the attack damage", t("REWORK")))
W(ul_close())
W(ability("Blink Strike", slug="riki_blink_strike"))
W(ul_open())
W(li("2 charges with 25/21/17/13s base restore time replaced with 13/10/7/4s cooldown",
     t("REWORK") + b([25, 21, 17, 13], [13, 10, 7, 4], l=True),
     extra=inline_note("% compares time between uses; note the second charge (burst potential) is gone")))
W(li("Bonus 40/55/70/85 magic damage replaced with 15/30/45/60 bonus physical damage on attack",
     t("REWORK") + b([40, 55, 70, 85], [15, 30, 45, 60]),
     extra=inline_note("% compares raw numbers; physical damage scales differently (reduced by armor instead of magic resistance)")))
W(ul_close())
W(ability("Tricks of the Trade", slug="riki_tricks_of_the_trade"))
W(ul_open())
W(li("Mana Cost rescaled from 45/55/65/75 to 65", b([45, 55, 65, 75], 65, l=True)))
W(li("Cooldown increased from 18/16/14/12s to 21/18/15/12s", b([18, 16, 14, 12], [21, 18, 15, 12], l=True)))
W(li("Radius decreased from 450 to 425", b(450, 425)))
W(li("40% Attack Damage replaced with 30/50/70/90 flat damage", t("REWORK"), extra=inline_note("Still applies bonus damage from Backstab, but as a separate instance of damage now")))
W(li("No longer provides bonus Agility", t("DEL")))
W(li("Now attacks 2 random targets by default", t("NEW")))
W(li("Aghanim's Scepter slightly reworked", t("REWORK"), extra=inline_note("No longer increases the number of targets attacked")))
W(li("Now also allows to hide within allied creeps", t("NEW")))
W(li("Now increases ability duration by 1s and attack count by 2, but only when Riki hides within an ally", t("NEW"), extra=inline_note("No longer increases attack count on non-ally casts")))
W(li("Now provides 15% bonus movement speed to the ally Riki's hiding in", t("NEW")))
W(ul_close())
W(ability("Cloak and Dagger", slug="riki_backstab"))
W(ul_open())
W(li("Now grants 130/260/390 experience when getting a hero kill and 100 experience when getting a hero assist", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +50 Tricks of the Trade Agility replaced with 15% of Riki's Base damage added to Tricks of the Trade", t("REWORK")))
W(li("Level 20 Talent -4s Blink Strike Replenish Time replaced with -1s Blink Strike Cooldown", t("REWORK")))
W(li("Level 25 Talent Tricks of the Trade Applies a Basic Dispel replaced with +500 Blink Strike Cast Range", t("REWORK")))
W(ul_close())

# Ringmaster
W(hero_header("Ringmaster"))
W(ability("Wheel of Wonder", slug="ringmaster_wheel"))
W(ul_open())
W(li("Mana Cost decreased from 175/275/375 to 150/225/300", b([175, 275, 375], [150, 225, 300], l=True)))
W(ul_close())

# Rubick
W(hero_header("Rubick"))
W(ul_open())
W(li("Base damage increased by 1", bstat_h("Rubick", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Rubick", field="AttackDamageMin", before_patch="7.39e")))
W(li("Damage at level 1 increased from 49–55 to 50–56", br(49, 55, 50, 56)))
W(ul_close())
W(ability("Telekinesis", slug="rubick_telekinesis"))
W(ul_open())
W(li("Land sub-ability no longer cancels channeling or interrupts movement", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +0.5s Telekinesis Lift/Stun Duration replaced with +20% Fade Bolt Damage Reduction", t("REWORK")))
W(ul_close())

# Sand King
W(hero_header("Sand King"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Burrowstrike Cooldown Reduction increased from 2s to 3s", b(2, 3)))
W(li("Level 25 Talent Epicenter Pulses decreased from +10 to +8", b(10, 8)))
W(ul_close())

# Shadow Demon
W(hero_header("Shadow Demon"))
W(ability("Disruption", slug="shadow_demon_disruption"))
W(ul_open())
W(li("Bonus Base Damage decreased from 25/40/55/70 to 20/35/50/65", b([25, 40, 55, 70], [20, 35, 50, 65])))
W(ul_close())
W(ability("Demonic Purge", slug="shadow_demon_demonic_purge"))
W(ul_open())
W(li("Can no longer target invulnerable units", t("DEL")))
W(ul_close())
W(ability("Demonic Cleanse", slug="shadow_demon_demonic_cleanse"))
W(ul_open())
W(li("Can no longer target invulnerable units", t("DEL")))
W(ul_close())

# Shadow Fiend
W(hero_header("Shadow Fiend"))
W(ul_open())
W(li("Agility gain increased from 3.5 to 3.6", b(3.5, 3.6)))
W(ul_close())
W(ability("Necromastery", slug="nevermore_necromastery"))
W(ul_open())
W(li("Souls on hero kills increased from 3 to 4", b(3, 4)))
W(ul_close())

# Shadow Shaman
W(hero_header("Shadow Shaman"))
W(facet_header("shadow_shaman_massive_serpent_ward"))
W(ul_open())
W(li("Mass Serpent Ward health and bounty multiplier decreased from 10x to 9x", b(10, 9), extra=inline_note("Hits to destroy decreased from 20 to 18, Gold Bounty decreased from 220–300 to 198–270, XP Bounty decreased from 310 to 279")))
W(ul_close())
W(ability("Shackles", slug="shadow_shaman_shackles"))
W(ul_open())
W(li("Total Damage/Heal increased from 70/140/210/280 to 100/160/220/280", b([70, 140, 210, 280], [100, 160, 220, 280])))
W(ul_close())
W(ability("Mass Serpent Ward", slug="shadow_shaman_mass_serpent_ward"))
W(ul_open())
W(li("Cooldown decreased from 110s to 110/105/100s", b(110, [110, 105, 100], l=True)))
W(ul_close())

# Silencer
W(hero_header("Silencer"))
W(facet_header("silencer_spread_the_knowledge"))
W(ul_open())
W(li("No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
W(ul_close())
W(ability("Arcane Curse", slug="silencer_curse_of_the_silent"))
W(ul_open())
W(li("Silenced Multiplier decreased from 1.5 to 1.25", b(1.5, 1.25)))
W(ul_close())
W(ability("Glaives of Wisdom", slug="silencer_glaives_of_wisdom"))
W(ul_open())
W(li("Int Steal increased from 1/2/3/4 to 2/3/4/5", b([1, 2, 3, 4], [2, 3, 4, 5])))
W(li("Int Steal Duration rescaled from 20/25/30/35s to 10/20/30/40s", b([20, 25, 30, 35], [10, 20, 30, 40])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Arcane Curse Penalty Multiplier decreased from +0.5 to +0.25", b(0.5, 0.25)))
W(ul_close())

# Skywrath Mage
W(hero_header("Skywrath Mage"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Ancient Seal Cooldown Reduction decreased from 7s to 6s", b(7, 6)))
W(li("Level 15 Talent Concussive Shot Slow increased from +15% to +20%", b(15, 20)))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ability("Slithereen Crush", slug="slardar_slithereen_crush"))
W(ul_open())
W(li("Puddle radius increased from 250 to 325", b(250, 325)))
W(li("Aghanim's Scepter Crush puddle radius decreased from 450 to 400", b(450, 400)))
W(ul_close())
W(ability("Bash of the Deep", slug="slardar_bash"))
W(ul_open())
W(li("Bash Duration decreased from 1.1s to 1s", b(1.1, 1)))
W(li("Bonus Damage decreased from 50/100/150/200 to 35/90/145/200", b([50, 100, 150, 200], [35, 90, 145, 200])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Seaborn Sentinel Bonus Damage increased from +12 to +14", b(12, 14)))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(facet_header("slark_leeching_leash"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("slark_dark_reef_renegade"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Barracuda", innate=True))
W(ul_open())
W(li("Innate ability removed", t("DEL"), extra=inline_note("Effect moved to the Ultimate")))
W(ul_close())
W(ability("Essence Shift", slug="slark_essence_shift"))
W(ul_open())
W(li("Now an innate ability. Passive, improves with Slark's level", t("NEW")))
W(li_formula("Duration rescaled",
             "15/35/55/75s", "15s + 2.5s each time Slark levels up",
             lambda L: 75, lambda L: 15 + 2.5 * (L - 1),
             value_fmt="{:g}s"))
W(ul_close())
W(ability("Pounce", slug="slark_pounce"))
W(ul_open())
W(li("Now applies 1/2/3/4 Essence Shift stacks when leashing an enemy hero", t("NEW")))
W(ul_close())
W(ability_change(
    old=None,
    new=dict(
        name="Saltwater Shiv",
        slug="slark_saltwater_shiv",
        desc=[
            "New basic ability — passive, auto-cast attack modifier.",
            "Slark slices the target with his salty shiv, stealing <b>3 Movement Speed</b>, <b>3 Health Regen</b> and <b>3/4/5/6% Health Restoration</b> from them with each attack. Subsequent uses refresh the duration of all shiv stacks. Steal duration: 6/8/10/12s. Mana Cost: 20. Cooldown: 10/8/6/4s."
            + inline_note("Not Breakable. Disabled by Silence. Has no stack limit. Ignores attack backswing. Enemies with Health Restoration below −100% will not lose health from health-restoration sources."),
        ],
    ),
    summary="New ability.",
    tag="new",
))
W(ability("Shadow Dance", slug="slark_shadow_dance"))
W(ul_open())
W(li("Now passively grants 24/36/48% movement speed and 60/90/120 health regen when unseen", t("NEW"), extra=inline_note("Previous Barracuda rules and mechanics unchanged")))
W(ul_close())
W(ability("Depth Shroud", slug="slark_depth_shroud"))
W(ul_open())
W(li("Duration decreased from 3s to 2s", b(3, 2)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Dark Pact Cooldown Reduction increased from 0.5s to 0.75s", b(0.5, 0.75)))
W(li("Level 15 Talent +50 Barracuda Regen replaced with +30 Shadow Dance Regen", t("REWORK")))
W(li("Level 25 Talent Shadow Dance Duration increased from +1.25s to +1.5s", b(1.25, 1.5)))
W(ul_close())

# Snapfire
W(hero_header("Snapfire"))
W(ability("Buckshot", innate=True))
W(ul_open())
W(li("Now affects only attacks made on enemy heroes", t("MISC"), extra=inline_note("Attacks on non-heroes can still ricochet on miss, but they won't have extra damage or glance chance")))
W(ul_close())
W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
W(ul_open())
W(li("Mana Cost increased from 85/90/95/100 to 105", b([85, 90, 95, 100], 105, l=True)))
W(li("Aghanim's Shard Mortimer Kiss damage decreased from 50% to 40%", b(50, 40)))
W(ul_close())
W(ability("Lil' Shredder", slug="snapfire_lil_shredder"))
W(ul_open())
W(li("Base Damage per shot decreased from 25/40/55/70 to 20/35/50/65", b([25, 40, 55, 70], [20, 35, 50, 65])))
W(ul_close())

# Sniper
W(hero_header("Sniper"))
W(ability("Assassinate", slug="sniper_assassinate"))
W(ul_open())
W(li("Can no longer target invulnerable units", t("DEL")))
W(li("Attack Damage increased from 100% to 100/110/120%", b(100, [100, 110, 120])))
W(ul_close())

# Spectre
W(hero_header("Spectre"))
W(ul_open())
W(li("Now an Agility Hero", t("NEW"), extra=inline_note("Base attributes and attribute gains are unchanged")))
W(li("Base Damage increased by 2", t("MISC") + bstat_h("Spectre", "AttackDamageMin", "7.39e", 2), extra=note_box(hero="Spectre", field="AttackDamageMin", before_patch="7.39e", extra_note="Damage at level 1 unchanged (48–52)")))
W(li("Damage gain per level decreased from +2.8 to +2.1", b(2.8, 2.1)))
W(li("Damage at level 30 decreased by 27 (from 149–153 to 122–126)", br(149, 153, 122, 126)))
W(li("Base Attack Time worsened from 1.7s to 1.8s", b(1.7, 1.8, l=True)))
W(li("Base Attack Speed increased from 90 to 110", b(90, 110)))
W(ul_close())
W(facet_header("spectre_forsaken"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("spectre_twist_the_knife"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Spectral", innate=True))
W(ul_open())
W(li("Innate ability removed", t("DEL")))
W(ul_close())
W(ability("Desolate", slug="spectre_desolate"))
W(ul_open())
W(li("Now an innate ability. Passive, improves with Spectre's level", t("NEW")))
W(li_formula("Damage rescaled",
             "25/40/55/70", "25 + 2 every time Spectre levels up",
             lambda L: 70, lambda L: 25 + 2 * (L - 1),
             value_fmt="{:g}"))
W(ul_close())
W(ability("Spectral Dagger", slug="spectre_spectral_dagger"))
W(ul_open())
W(li("Mana Cost decreased from 110/120/130/140 to 100/110/120/130", b([110, 120, 130, 140], [100, 110, 120, 130], l=True)))
W(li("Spectre's illusions now also benefit from the Shadow Path", t("NEW")))
W(ul_close())
W(ability_change(
    old=dict(
        name="Shadow Step",
        slug="spectre_shadow_step",
        desc=[
            "Ultimate.",
            "Spectre performs a single-target Haunt, creating an uncontrollable illusion that attacks the target for <b>40/60/80%</b> of her damage and takes 200% damage. Duration: 5/6/7s. Mana Cost: 150. Cooldown: 80/60/40s.",
            "The Reality sub-ability teleports Spectre to the illusion.",
        ],
    ),
    new=dict(
        name="Shadow Step",
        slug="spectre_shadow_step",
        desc=[
            "Basic ability.",
            "Thrusts an uncontrollable illusion that follows the target and attacks it for <b>20/30/40/50%</b> of Spectre's damage. The illusion exists for <b>3.5/4/4.5/5s</b> and takes 200% damage. On cast it moves at 900 speed, then at 135% of Spectre's movement speed after reaching the target. Cast Range: 700/850/1000/1150. Mana Cost: 60/65/70/75. Cooldown: 32/28/24/20s.",
            "The Reality sub-ability may be used to teleport to the illusion, destroying it.",
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ability("Dispersion", slug="spectre_dispersion"))
W(ul_open())
W(li("Min Radius increased from 300 to 350", b(300, 350)))
W(ul_close())
W(ability("Reality", slug="spectre_reality"))
W(ul_open())
W(li("Can no longer be cast to no effect", t("QoL")))
W(li("Now has a distinct sound between casts on Shadow Step and Haunt illusions", t("QoL")))
W(li("Mana Cost decreased from 40 to 25", b(40, 25, l=True)))
W(li("Now has a 0.2s travel time to reach the target. The illusion and Spectre are invulnerable during this time", t("NEW")))
W(li("Now disabled by roots", t("NEW")))
W(li("Now always destroys the target illusion", t("NEW")))
W(ul_close())
W(ability("Haunt", slug="spectre_haunt"))
W(ul_open())
W(li("Now Spectre's ultimate ability", t("NEW")))
W(li("Mana Cost rescaled from 150 to 125/150/175", b(150, [125, 150, 175], l=True, force_overall="buff")))
W(li("Duration rescaled from 6s to 5/6/7s", b(6, [5, 6, 7])))
W(li("Cooldown rescaled from 160s to 180/160/140s", b(160, [180, 160, 140], l=True)))
W(li("Haunt Outgoing Damage decreased from 80% to 30/55/80%", b(80, [30, 55, 80])))
W(li("Each illusion now spawns from the direction closest to Spectre", t("MISC")))
W(li("Aghanim's Scepter: Reduces Haunt cooldown by 20s. When Reality is used on Haunt illusion for the first time per Haunt cast, enemies are Feared away from Spectre for 1.5s with 50% reduced move speed in a 400 AoE around the targeted illusion", t("NEW")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +5 Health Regen replaced with +10 Desolate Damage", t("REWORK")))
W(li("Level 15 Talent +15 Desolate Damage replaced with +1s Shadow Step Duration", t("REWORK")))
W(li("Level 20 Talent Spectral Dagger Slow/Bonus increased from +12% to +15%", b(12, 15)))
W(li("Level 25 Talent All Spectre Illusion Damage decreased from +25% to +20%", b(25, 20)))
W(ul_close())

# Spirit Breaker
W(hero_header("Spirit Breaker"))
W(ability("Charge of Darkness", slug="spirit_breaker_charge_of_darkness"))
W(ul_open())
W(li("Stun Duration increased from 1.2/1.5/1.8/2.1s to 1.3/1.6/1.9/2.2s", b([1.2, 1.5, 1.8, 2.1], [1.3, 1.6, 1.9, 2.2])))
W(li("Aghanim's Shard bonus speed decreased from +100 to +85", b(100, 85)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Bulldoze barrier decreased from 400 to 375", b(400, 375)))
W(ul_close())

# Storm Spirit
W(hero_header("Storm Spirit"))
W(ability("Galvanized", slug="storm_spirit_galvanized"))
W(ul_open())
W(li("Charge loss on death decreased from 3 to 2", b(3, 2, l=True)))
W(ul_close())
W(ability("Overload", slug="storm_spirit_overload"))
W(ul_open())
W(li("Attack Speed Slow increased from 80 to 90", b(80, 90)))
W(ul_close())

# Sven
W(hero_header("Sven"))
W(ability("Storm Hammer", slug="sven_storm_bolt"))
W(ul_open())
W(li("Aghanim's Scepter no longer allows targeting invulnerable units, but still affects invulnerable units in the radius", t("DEL")))
W(li("Aghanim's Scepter cast range bonus changed from +350 to +25%", b(350, 150), extra=inline_note("Decreased from +350 to +150")))
W(li("Aghanim's Scepter now also increases projectile speed by 25%", b(1000, 1250), extra=inline_note("From 1000 to 1250")))
W(ul_close())
W(ability("Great Cleave", slug="sven_great_cleave"))
W(ul_open())
W(li("Cleave damage rescaled from 50/65/80/95% to 60/70/80/90%", b([50, 65, 80, 95], [60, 70, 80, 90])))
W(ul_close())
W(ability("Warcry", slug="sven_warcry"))
W(ul_open())
W(li("Cooldown decreased from 40/35/30/25 to 36/32/28/24", b([40, 35, 30, 25], [36, 32, 28, 24], l=True)))
W(ul_close())

# Techies
W(hero_header("Techies"))
W(ul_open())
W(li("Base Agility increased from 14 to 16", b(14, 16)))
W(li("Damage at level 1 increased by 1 (from 46–48 to 47–49)", br(46, 48, 47, 49)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +125 Sticky Bomb Latch/Explosion Radius replaced with +160 Sticky Bomb Damage", t("REWORK")))
W(ul_close())

# Templar Assassin
W(hero_header("Templar Assassin"))
W(ability("Meld", slug="templar_assassin_meld"))
W(ul_open())
W(li("Armor Reduction decreased from 3.5/5/6.5/8 to 2/4/6/8", b([3.5, 5, 6.5, 8], [2, 4, 6, 8])))
W(li("Damage decreased from 55/105/155/205 to 50/100/150/200", b([55, 105, 155, 205], [50, 100, 150, 200])))
W(ul_close())
W(ability("Psionic Trap", slug="templar_assassin_psionic_trap"))
W(ul_open())
W(li("Damage rescaled from 225/300/375 to 200/300/400", b([225, 300, 375], [200, 300, 400])))
W(ul_close())
W(ability("Psionic Projection", slug="templar_assassin_trap_teleport"))
W(ul_open())
W(li("Damage increased from 375 to 400", b(375, 400)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Meld Debuff Duration decreased from +2s to +1.5s", b(2, 1.5)))
W(li("Level 10 Talent Psionic Trap Slow increased from +5% to +10%", b(5, 10)))
W(ul_close())

# Terrorblade
W(hero_header("Terrorblade"))
W(ability("Dark Unity", slug="terrorblade_dark_unity"))
W(ul_open())
W(li("Illusions that are outside 1200 radius no longer have a damage penalty", t("NEW")))
W(li("Damage increase for illusions within 1200 radius increased from 25% to 60%", b(25, 60)))
W(ul_close())
W(ability("Reflection", slug="terrorblade_reflection"))
W(ul_open())
W(li("Reflection Damage decreased from 40/60/80/100% to 30/45/60/75%", b([40, 60, 80, 100], [30, 45, 60, 75])))
W(ul_close())
W(ability("Conjure Image", slug="terrorblade_conjure_image"))
W(ul_open())
W(li("Illusion Damage decreased from 30/40/50/60% to 20/25/30/35%", b([30, 40, 50, 60], [20, 25, 30, 35])))
W(ul_close())

# Tidehunter
W(hero_header("Tidehunter"))
W(ability("Gush", slug="tidehunter_gush"))
W(ul_open())
W(li("Damage rescaled from 110/160/210/260 to 100/160/220/280", b([110, 160, 210, 260], [100, 160, 220, 280])))
W(ul_close())
W(ability("Anchor Smash", slug="tidehunter_anchor_smash"))
W(ul_open())
W(li("Attack Bonus Damage increased from 45/90/135/180 to 50/100/150/200", b([45, 90, 135, 180], [50, 100, 150, 200])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Gush Slow increased from +15% to +20%", b(15, 20)))
W(li("Level 10 Talent +40 Anchor Smash Damage replaced with +20% Anchor Smash Damage Reduction", t("REWORK")))
W(li("Level 15 Talent +30% Anchor Smash Damage Reduction replaced with -15s Ravage Cooldown", t("REWORK")))
W(li("Level 20 Talent Anchor Smash affects buildings replaced with Blubber effect triggers Anchor Smash", t("REWORK")))
W(li("Level 25 Talent 50% chance of Anchor Smash on attack replaced with Anchor Smash affects buildings", t("REWORK")))
W(li("Level 25 Talent Ravage Stun Duration increased from +0.8s to +1s", b(0.8, 1)))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ul_open())
W(li("Base Movement Speed decreased from 285 to 280", b(285, 280)))
W(ul_close())
W(ability("Whirling Death", slug="shredder_whirling_death"))
W(ul_open())
W(li("Tree Bonus Damage decreased from 11/18/25/32 to 9/16/23/30", b([11, 18, 25, 32], [9, 16, 23, 30])))
W(ul_close())
W(ability("Reactive Armor", slug="shredder_reactive_armor"))
W(ul_open())
W(li("Max Stacks decreased from 12/22/32/42 to 10/20/30/40", b([12, 22, 32, 42], [10, 20, 30, 40])))
W(li("Aghanim's Scepter base barrier decreased from 200 to 150", b(200, 150)))
W(ul_close())

# Tinker
W(hero_header("Tinker"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Manacost/Manaloss Reduction increased from +8% to +10%", b(8, 10, l=True)))
W(li("Level 25 Talent +10s Defense Matrix Duration replaced with +40 Intelligence", t("REWORK")))
W(ul_close())

# Tiny
W(hero_header("Tiny"))
W(ul_open())
W(li("Strength gain increased from 4.0 to 4.2", b(4, 4.2)))
W(ul_close())
W(ability("Avalanche", slug="tiny_avalanche"))
W(ul_open())
W(li("Stun duration now applies its stun as an aura in the area", t("REWORK"), extra=inline_note("As a result, no longer affected by status resistance")))
W(ul_close())
W(ability("Tree Throw", slug="tiny_toss_tree"))
W(ul_open())
W(li("No longer has separate damage bonus, uses Tree Grab's value instead", t("BUFF"), extra=inline_note("Bonus damage rescaled from 20 to 10/20/30/40 " + b(20, [10, 20, 30, 40]))))
W(ul_close())
W(ability("Grow", slug="tiny_grow"))
W(ul_open())
W(li("Movement Speed Bonus rescaled from 15 to 10/15/20", b(15, [10, 15, 20])))
W(ul_close())

# Treant Protector
W(hero_header("Treant Protector"))
W(facet_header("treant_primeval_power"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(facet_header("treant_sapling"))
W(ul_open())
W(li("Facet removed", t("DEL")))
W(ul_close())
W(ability("Nature's Guise", slug="treant_natures_guise"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(li("Now can be activated while tree walking to make Treant Protector invisible until he attacks or loses the Nature's Guise buff", t("NEW"), extra=inline_note("Linger time: 2s. No Mana Cost. Cooldown: 50s. Cooldown is reduced by 3s per 2 Treant Protector's level ups<br>Cooldown starts when the invisibility ends")))
W(ul_close())
W(ability("Nature's Grasp", slug="treant_natures_grasp"))
W(ul_open())
W(li("No longer does 50% more damage and slow when touching a tree", t("DEL")))
W(li("Damage per second increased from 30/40/50/60 to 35/50/65/80", b([30, 40, 50, 60], [35, 50, 65, 80])))
W(li("Movement Slow increased from 20/25/30/35% to 25/30/35/40%", b([20, 25, 30, 35], [25, 30, 35, 40])))
W(li("Creep penalty decreased from 50% to 35%", b(50, 35)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Leech Seed",
        slug="treant_leech_seed",
        desc=[
            "Active.",
            "Plants a leeching seed in an enemy unit, slowing it (decaying over the duration) and dealing <b>15/30/45/60</b> damage per second for 6 seconds. The leeched life heals nearby allied units (50% effectiveness on creeps).",
        ],
    ),
    new=dict(
        name="Leech Seed",
        slug="treant_leech_seed",
        desc=[
            "Passive, auto-cast attack modifier.",
            "Treant Protector's attack plants a life-sapping seed in an enemy unit, dealing an extra <b>20/40/60/80</b> magic damage. The enemy is bound for <b>0.9/1.1/1.3/1.5s</b> and emits two healing pulses — one upon application and one upon expiration — healing up to 5 allies within 650 units for <b>15/25/35/45</b> + 20% of the damage dealt by the attack. No Mana Cost. Cooldown: 15/12/9/6s. Breakable."
            + inline_note("Now only sends out a maximum of 5 heals per pulse, prioritizing heroes."),
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))
W(ul_open())
W(li("No longer has a creep penalty for healing", t("BUFF")))
W(ul_close())
W(ability("Living Armor", slug="treant_living_armor"))
W(ul_open())
W(li("No longer grants bonus armor", t("DEL")))
W(li("Now grants 100 damage block from player-controlled sources. Each time this spell blocks damage the effect is decreased by 35/30/25/20", t("NEW"), extra=inline_note("Damage block affects any types of damage<br>The heal ends earlier if the damage block is reduced to 0<br>Instances of less than 20 damage are ignored by Living Armor. They are neither blocked nor counted towards block decrease")))
W(li("Duration decreased from 18/22/26/30s to 12s", b([18, 22, 26, 30], 12)))
W(li("Heal per second increased from 3/4/5/6 to 4/7/10/13", b([3, 4, 5, 6], [4, 7, 10, 13])))
W(ul_close())
W(ability("Overgrowth", slug="treant_overgrowth"))
W(ul_open())
W(li("Aghanim's Scepter: Decreases cooldown from 110/100/90 to 80/70/60s. When casting Overgrowth, Treant Protector draws power from the earth, becoming massive for 16 seconds, gaining +100% Strength, Phased Movement, and a Splashing Attack that deals 60% of attack damage in a 300 unit radius. While large, he has a fixed movement speed of 345. Buff is undispellable", t("NEW")))
W(ul_close())
W(ability("Eyes In The Forest", slug="treant_eyes_in_the_forest"))
W(ul_open())
W(li("Now granted by Aghanim's Shard", t("NEW")))
W(li("Mana Cost decreased from 100 to 30", b(100, 30, l=True)))
W(li("Cast Range increased from 160 to 350", b(160, 350)))
W(li("Overgrowth is no longer applied around enchanted trees", t("DEL")))
W(li("Enchanted trees now have the same health as Observer Wards, and they expire after 5 minutes", t("REWORK"), extra=inline_note("Trees can be attacked when revealed by True Sight. Attacks will remove the ability effect from the tree without destroying the tree itself")))
W(li("Charge Restore Time increased from 40s to 55s", b(40, 55, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +2.5% Nature's Guise Movement Speed replaced with +50 Base Damage", t("REWORK")))
W(li("Level 10 Talent Living Armor Heal Per Second increased from +2 to +4", b(2, 4)))
W(li("Level 15 Talent +18% Leech Seed Movement Slow replaced with +10% Leech Seed Damage to Healing", t("REWORK")))
W(li("Level 20 Talent Leech Seed Bonus Damage increased from +45 to +80", b(45, 80)))
W(li("Level 20 Talent +8 Living Armor Bonus Armor replaced with +20 Living Armor Damage Block", t("REWORK")))
W(li("Level 25 Talent -35s Overgrowth Cooldown replaced with -3s Leech Seed Cooldown", t("REWORK")))
W(ul_close())

# Troll Warlord
W(hero_header("Troll Warlord"))
W(ability("Berserker's Rage", slug="troll_warlord_berserkers_rage"))
W(ul_open())
W(li("Bonus Armor increased from 2/3/4/5 to 3/4/5/6", b([2, 3, 4, 5], [3, 4, 5, 6])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Whirling Axes damage increased from +100 to +115", b(100, 115)))
W(li("Level 20 Talent Berserker's Rage Armor increased from +9 to +10", b(9, 10)))
W(ul_close())

# Tusk
W(hero_header("Tusk"))
W(ability("Snowball", slug="tusk_snowball"))
W(ul_open())
W(li("Gather Radius decreased from 350 to 325", b(350, 325)))
W(ul_close())
W(ability("Walrus PUNCH!", slug="tusk_walrus_punch"))
W(ul_open())
W(li("Bonus Damage increased from 50/75/100 to 60/90/120", b([50, 75, 100], [60, 90, 120])))
W(ul_close())

# Underlord
W(hero_header("Underlord"))
W(ul_open())
W(li("Strength gain increased from 3.0 to 3.2", b(3, 3.2)))
W(li("Base Intelligence increased from 17 to 18", b(17, 18)))
W(ul_close())
W(ability("Firestorm", slug="abyssal_underlord_firestorm"))
W(ul_open())
W(li("Cast Range increased from 600/625/650/675 to 675", b([600, 625, 650, 675], 675)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Pit of Malice Slow decreased from +25% to +20%", b(25, 20)))
W(li("Level 25 Talent Fiend's Gate DPS increased from 100 to 125", b(100, 125)))
W(ul_close())

# Undying
W(hero_header("Undying"))
W(ability("Soul Rip", slug="undying_soul_rip"))
W(ul_open())
W(li("Cooldown decreased from 18/14/10/6s to 15/12/9/6s", b([18, 14, 10, 6], [15, 12, 9, 6], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Soul Rip Damage/Heal increased from +10 to +12", b(10, 12)))
W(ul_close())

# Ursa
W(hero_header("Ursa"))
W(ability("Earthshock", slug="ursa_earthshock"))
W(ul_open())
W(li("Aghanim's Shard reworked: Applies 3 Fury Swipe stacks to each affected enemy", t("REWORK")))
W(ul_close())
W(ability("Enrage", slug="ursa_enrage"))
W(ul_open())
W(li("Cooldown decreased from 70/50/30s to 60/45/30s", b([70, 50, 30], [60, 45, 30], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Earthshock applies 2 Fury Swipes replaced with +0.5% Maul Health as Damage", t("REWORK")))
W(ul_close())

# Vengeful Spirit
W(hero_header("Vengeful Spirit"))
W(ability("Magic Missile", slug="vengefulspirit_magic_missile"))
W(ul_open())
W(li("Cooldown rescaled from 16/14/12/10s to 14/13/12/11s", b([16, 14, 12, 10], [14, 13, 12, 11], l=True)))
W(ul_close())
W(ability("Nether Swap", slug="vengefulspirit_nether_swap"))
W(ul_open())
W(li("Can no longer target invulnerable units", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Wave of Terror Armor Reduction decreased from +4 to +3", b(4, 3)))
W(ul_close())

# Venomancer
W(hero_header("Venomancer"))
W(ability("Septic Shock", slug="venomancer_sepsis"))  # innate
W(ul_open())
W(li("Base Damage per Debuff decreased from 10% to 8%", b(10, 8)))
W(ul_close())
W(facet_header("venomancer_plague_carrier"))
W(ul_open())
W(li("Plague Wards created by Venomous Gale have 75% health and damage", t("REWORK")))
W(ul_close())

# Viper
W(hero_header("Viper"))
W(facet_header("viper_caustic_bath"))
W(ul_open())
W(li("Corrosive Skin time to max effect increased from 4s to 5s", b(4, 5, l=True)))
W(ul_close())
W(ability("Poison Attack", slug="viper_poison_attack"))
W(ul_open())
W(li("Mana Cost decreased from 22 to 20", b(22, 20, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Predator Damage Per Missing Health increased from +0.2 to +0.25", b(0.2, 0.25)))
W(ul_close())

# Visage
W(hero_header("Visage"))
W(ability("Grave Chill", slug="visage_grave_chill"))
W(ul_open())
W(li("Move Speed Drain increased from 12/16/20/24% to 12/18/24/30%", b([12, 16, 20, 24], [12, 18, 24, 30])))
W(ul_close())
W(ability("Gravekeeper's Cloak", slug="visage_gravekeepers_cloak"))
W(ul_open())
W(li("Familiars now have their own copy of Gravekeeper's Cloak ability (visual change only)", t("QoL")))
W(ul_close())
W(ability("Summon Familiars", slug="visage_summon_familiars"))
W(ul_open())
W(li("Familiars now have their own ability to independently recall it to Visage", t("MISC"), extra=inline_note("The alt cast behavior on Visage is unchanged")))
W(li("The 3rd Familiar gained by Level 25 Talent is now automatically added to an existing control group when created", t("QoL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +15 Gravekeeper's Cloak Armor replaced with -2s Gravekeeper's Cloak Recovery Time", t("REWORK")))
W(ul_close())

# Void Spirit
W(hero_header("Void Spirit"))
W(ability("Resonant Pulse", slug="void_spirit_resonant_pulse"))
W(ul_open())
W(li("Aghanim's Scepter Silence duration decreased from 2.0 to 1.75s", b(2, 1.75)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Aether Remnant damage increased from +60 to +65", b(60, 65)))
W(ul_close())

# Warlock
W(hero_header("Warlock"))
W(ability("Chaotic Offering", slug="warlock_rain_of_chaos"))
W(ul_open())
W(li("Cooldown increased from 160s to 165s", b(160, 165, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Upheaval Attack Speed per second on Allies decreased from +10 to +8", b(10, 8)))
W(li("Level 20 Talent Summons a Golem on Death replaced with +25% Damage Resistance for Chaotic Offering Golems", t("REWORK")))
W(li("Level 25 Talent +80% Golem Magic Resistance replaced with +3 Fatal Bonds targets", t("REWORK")))
W(li("Level 25 Talent +20 Chaotic Offering Golems Armor replaced with Summons a Golem on Death", t("REWORK")))
W(ul_close())

# Weaver
W(hero_header("Weaver"))
W(ability("The Swarm", slug="weaver_the_swarm"))
W(ul_open())
W(li("Attack Damage increased from 18/22/26/30 to 18/23/28/33", b([18, 22, 26, 30], [18, 23, 28, 33])))
W(ul_close())
W(ability("Time Lapse", slug="weaver_time_lapse"))
W(ul_open())
W(li("Aghanim's Scepter now also reduces Cooldown by 10s", t("NEW")))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ul_open())
W(li("Agility gain increased from 1.9 to 2.1", b(1.9, 2.1)))
W(li("Damage gain per level increased from 3.5 to 3.6", b(3.5, 3.6)))
W(ul_close())
W(ability("Gale Force", slug="windrunner_gale_force"))
W(ul_open())
W(li("Duration decreased from 3.5s to 3s", b(3.5, 3)))
W(ul_close())

# Winter Wyvern
W(hero_header("Winter Wyvern"))
W(ul_open())
W(li("Base damage increased by 1", bstat_h("Winter Wyvern", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Winter Wyvern", field="AttackDamageMin", before_patch="7.39e")))
W(li("Damage at level 1 increased from 41–48 to 42–49", br(41, 48, 42, 49)))
W(li("Base Attack Range increased from 425 to 450", b(425, 450)))
W(ul_close())
W(ability("Arctic Burn", slug="winter_wyvern_arctic_burn"))
W(ul_open())
W(li("Bonus Attack Range decreased from 275/300/325/350 to 250/275/300/325", b([275, 300, 325, 350], [250, 275, 300, 325])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Winter's Curse Attack Speed increased from +55 to +60", b(55, 60)))
W(ul_close())

# Witch Doctor
W(hero_header("Witch Doctor"))
W(facet_header("witch_doctor_malpractice"))
W(ul_open())
W(li("Maledict burst damage does not apply from non-hero units", t("NERF")))
W(ul_close())
W(ability("Voodoo Restoration", slug="witch_doctor_voodoo_restoration"))
W(ul_open())
W(li("Activation mana cost decreased from 35/40/45/50 to 25", b([35, 40, 45, 50], 25, l=True)))
W(li("Mana per second rescaled from 8/12/16/20 to 9/12/15/18", b([8, 12, 16, 20], [9, 12, 15, 18])))
W(ul_close())
W(ability("Maledict", slug="witch_doctor_maledict"))
W(ul_open())
W(li("Now also affects player-controlled creeps", t("NEW")))
W(ul_close())
W(ability("Death Ward", slug="witch_doctor_death_ward"))
W(ul_open())
W(li("Aghanim's Scepter bounce radius decreased from 650 to 575", b(650, 575)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +125 Maledict AoE replaced with +4s Maledict Duration", t("REWORK")))
W(li("Level 25 Talent +8s Maledict Duration replaced with -6s Paralyzing Cask Cooldown", t("REWORK")))
W(ul_close())

# Wraith King
W(hero_header("Wraith King"))
W(ability("Wraithfire Blast", slug="skeleton_king_hellfire_blast"))
W(ul_open())
W(li("Impact Damage increased from 75/90/105/120 to 80/100/120/140", b([75, 90, 105, 120], [80, 100, 120, 140])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Health decreased from +400 to +350", b(400, 350)))
W(li("Level 20 Talent Attack Speed decreased from +60 to +50", b(60, 50)))
W(ul_close())

# Zeus
W(hero_header("Zeus"))
W(ability("Arc Lightning", slug="zuus_arc_lightning"))
W(ul_open())
W(li("Jumps decreased from 5/7/9/15 to 5/7/9/11", b([5, 7, 9, 15], [5, 7, 9, 11])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Static Field Damage increased from +1.5% to +2%", b(1.5, 2)))
W(ul_close())

write_footer()
save_html('patches/7.40.html')


# ============================================================
# 7.08 content
# ============================================================
write_head("7.08", "01.02.2018")

# ===== GENERAL UPDATES =====
W(section("General Updates"))

W(plain_header("General"))
W(ul_open())
W(li("Observer Wards and Sentry Wards now require a constant 2 hits to kill", t("REWORK")))
W(li("Tier 1 Tower armor aura increased from 1 to 2", b(1, 2)))
W(li("Bounty Runes base XP reduced from 25 to 0", b(25, 0)))
W(li_formula(
    "Bounty Runes Gold Growth increased",
    "2/min", "4/min",
    lambda T: 2 * T, lambda T: 4 * T,
    levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
    level_fmt=lambda T: f'{T}:00',
    jump_at=15,
    rework_badge=False,
    value_fmt="{:g}g",
))
W(li("Roshan now has 25% Status Resistance", t("NEW")))
W(li("All Pick drafting time per hero selection reduced from 30s to 25s", b(30, 25)))
W(ul_close())

# ===== ITEM UPDATES =====
W(section("Item Updates"))

W(item_header("Aeon Disk"))
W(ul_open())
W(li("Health threshold reduced from 80% to 70%", b(80, 70)))
W(ul_close())

W(item_header("Battle Fury"))
W(ul_open())
W(li("Creep Bonus damage reduced from 60% to 50%", b(60, 50)))
W(li("Creep Bonus no longer works with illusions", t("DEL")))
W(ul_close())

W(item_header("Black King Bar"))
W(ul_open())
W(li("Cooldown rescaled from 80/75/70/65/60/55 to 70", b([80, 75, 70, 65, 60, 55], 70, l=True)))
W(ul_close())

W(item_header("Blink Dagger"))
W(ul_open())
W(li("Cooldown increased from 12s to 14s", b(12, 14, l=True)))
W(ul_close())

W(item_header("Enchanted Mango"))
W(ul_open())
W(li("Mana restore increased from 150 to 175", b(150, 175)))
W(ul_close())

W(item_header("Faerie Fire"))
W(ul_open())
W(li("Heal increased from 75 to 85", b(75, 85)))
W(ul_close())

W(item_header("Force Staff"))
W(ul_open())
W(li("Time it takes for the full distance to be traveled increased from 0.4s to 0.5s", b(0.4, 0.5, l=True)))
W(ul_close())

W(item_header("Hurricane Pike"))
W(ul_open())
W(li("Time it takes for the full distance to be traveled increased from 0.4s to 0.5s", b(0.4, 0.5, l=True)))
W(li("Cooldown increased from 18s to 23s", b(18, 23, l=True)))
W(ul_close())

W(item_header("Meteor Hammer"))
W(ul_open())
W(li("Cooldown reduced from 40s to 28s", b(40, 28, l=True)))
W(ul_close())

W(item_header("Soul Ring"))
W(ul_open())
W(li("Recipe cost increased from 185 to 200", b(185, 200, l=True)))
W(ul_close())

W(item_header("Spirit Vessel"))
W(ul_open())
W(li("Recipe cost increased from 600 to 750", b(600, 750, l=True)))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))

# Alchemist
W(hero_header("Alchemist"))
W(ability("Chemical Rage", innate=False))
W(ul_open())
W(li("Base attack time improved from 1.4/1.2/1.0 to 1.3/1.15/1.0", b([1.4, 1.2, 1.0], [1.3, 1.15, 1.0], l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent increased from -5s Unstable Concoction Cooldown to -8s", b(5, 8)))
W(li("Level 15 Talent increased from +350 Health to +400", b(350, 400)))
W(li("Level 20 Talent increased from +360 Unstable Concoction Damage to +400", b(360, 400)))
W(ul_close())

# Ember Spirit
W(hero_header("Ember Spirit"))
W(ability("Sleight of Fist", innate=False))
W(ul_open())
W(li("Hero Damage increased from 20/40/60/80 to 25/50/75/100", b([20, 40, 60, 80], [25, 50, 75, 100])))
W(ul_close())

# Enchantress
W(hero_header("Enchantress"))
W(ul_open())
W(li("Base damage reduced by 3", t("NERF")))
W(ul_close())

# Jakiro
W(hero_header("Jakiro"))
W(ul_open())
W(li("Attack backswing reduced from 0.5 to 0.3", b(0.5, 0.3, l=True)))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
W(ability("Blade Dance", innate=False))
W(ul_open())
W(li("Damage reduced from 200% to 180%", b(200, 180)))
W(ul_close())

# Leshrac
W(hero_header("Leshrac"))
W(ability("Split Earth", innate=False))
W(ul_open())
W(li("Manacost reduced from 100/125/140/160 to 80/100/120/140", b([100, 125, 140, 160], [80, 100, 120, 140], l=True)))
W(ul_close())

# Lina
W(hero_header("Lina"))
W(ul_open())
W(li("Base intelligence increased by 3", t("BUFF")))
W(li("Base damage random variance reduced from 18 to 12", t("BUFF"),
     extra=inline_note("Auto-attack damage rolls in a narrower min/max range (spread 12 instead of 18). Average damage is unchanged — only the swing between hits is smaller, so attacks are more consistent")))
W(ul_close())

# Lion
W(hero_header("Lion"))
W(ability("Mana Drain", innate=False))
W(ul_open())
W(li("Now slows the target by 14/16/18/20%", t("NEW")))
W(ul_close())

# Lycan
W(hero_header("Lycan"))
W(ul_open())
W(li("Base armor reduced by 1", t("NERF")))
W(ul_close())
W(ability("Shapeshift", innate=False))
W(ul_open())
W(li("Cooldown increased from 120/90/60 to 130/105/80", b([120, 90, 60], [130, 105, 80], l=True)))
W(ul_close())

# Medusa
W(hero_header("Medusa"))
W(ability("Mystic Snake", innate=False))
W(ul_open())
W(li("Cast range reduced from 800 to 700", b(800, 700)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent increased from 12% Evasion to 15%", b(12, 15)))
W(li("Level 15 Talent increased from +15% Mystic Snake Mana Steal to +20%", b(15, 20)))
W(li("Level 20 Talent reduced from +800 Mana to +700", b(800, 700)))
W(ul_close())

# Morphling
W(hero_header("Morphling"))
W(ability("Morph", slug="morphling_replicate", innate=False))
W(ul_open())
W(li("Cast range increased from 600 to 1000", b(600, 1000)))
W(li("Manacost reduced from 75/100/125 to 50", b([75, 100, 125], 50, l=True)))
W(ul_close())
W(ability("Morph Replicate", innate=False))
W(ul_open())
W(li("Cast point removed", t("NEW")))
W(ul_close())

# Nature's Prophet
W(hero_header("Nature's Prophet"))
W(ability("Wrath of Nature", innate=False))
W(ul_open())
W(li("Cooldown reduced from 90/75/60 to 70/65/60", b([90, 75, 60], [70, 65, 60], l=True)))
W(ul_close())

# Omniknight
W(hero_header("Omniknight"))
W(ability("Purification", innate=False))
W(ul_open())
W(li("Cast range reduced from 450 to 400", b(450, 400)))
W(ul_close())
W(ability("Degen Aura", innate=False))
W(ul_open())
W(li("Range reduced from 300 to 275", b(300, 275)))
W(ul_close())

# Oracle
W(hero_header("Oracle"))
W(ability("Fortune's End", innate=False))
W(ul_open())
W(li("Manacost reduced from 110 to 75", b(110, 75, l=True)))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ability("Rolling Thunder", slug="pangolier_gyroshell", innate=False))
W(ul_open())
W(li("Cooldown increased from 50/45/40 to 70/65/60", b([50, 45, 40], [70, 65, 60], l=True)))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(ability("Rot", innate=False))
W(ul_open())
W(li("Slow rescaled from 30% to 20/24/28/32%", b(30, [20, 24, 28, 32]),
     extra=inline_note("Effectively a nerf at levels 1–2 (20%, 24%) and a buff only at level 4 (32%)")))
W(ul_close())

# Pugna
W(hero_header("Pugna"))
W(ability("Life Drain", innate=False))
W(ul_open())
W(li("Damage increased from 150/200/250 to 150/225/300", b([150, 200, 250], [150, 225, 300])))
W(li("Aghanim's Scepter no longer increases Life Drain damage. Now it only removes the cooldown", t("DEL")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent increased from +1 Nether Ward Health to +2", b(1, 2)))
W(ul_close())

# Shadow Fiend
W(hero_header("Shadow Fiend"))
W(ability("Necromastery", innate=False))
W(ul_open())
W(li("Max souls reduced from 18/24/30/36 to 12/20/28/36", b([18, 24, 30, 36], [12, 20, 28, 36])))
W(ul_close())

# Shadow Shaman
W(hero_header("Shadow Shaman"))
W(ability("Ether Shock", innate=False))
W(ul_open())
W(li("Cooldown increased from 8s to 14/12/10/8s", b(8, [14, 12, 10, 8], l=True)))
W(ul_close())
W(ability("Shackles", innate=False))
W(ul_open())
W(li("Total damage reduced from 120/200/280/360 to 60/160/260/360", b([120, 200, 280, 360], [60, 160, 260, 360])))
W(ul_close())

# Tinker
W(hero_header("Tinker"))
W(ul_open())
W(li("Base movement speed reduced from 305 to 290", b(305, 290)))
W(ul_close())

# Tiny
W(hero_header("Tiny"))
W(ability("Toss", innate=False))
W(ul_open())
W(li("Cooldown increased from 8s to 11s", b(8, 11, l=True)))
W(ul_close())

# Tusk
W(hero_header("Tusk"))
W(ability("Snowball", innate=False))
W(ul_open())
W(li("Can no longer be cast while rooted", t("DEL")))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ability("Windrun", innate=False))
W(ul_open())
W(li("Manacost reduced from 60 to 50", b(60, 50, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent changed from +1 Shackleshot Target to +0.5s Shackleshot Duration", t("REWORK")))
W(li("Level 25 Talent increased from +30% Ministun Focus Fire to +35%", b(30, 35)))
W(ul_close())

write_footer()
save_html('patches/7.08.html')

save_index_html()
save_calendar_html()

# Emit site_meta.json — the cross-builder handoff. build_creeps.py reads
# `latest_patch_filename` from here for its Changelogs nav link, so the
# two builders stay decoupled (no import of build_patch from build_creeps).
_site_meta = {
    "latest_patch_filename": PATCHES[0]["filename"] if PATCHES else "patches/7.41c.html",
    "latest_patch_version": PATCHES[0]["version"] if PATCHES else "",
    "asset_version": _ASSET_VERSION,
    # version → release date (dd.mm.yyyy). build_creeps.py uses this to
    # label per-unit stat changelogs (e.g. HP history tooltips).
    "patch_dates": {r["version"]: r["date"] for r in RELEASE_HISTORY},
}
_os.makedirs("data", exist_ok=True)
with open(_os.path.join("data", "site_meta.json"), "w", encoding="utf-8") as _f:
    _json.dump(_site_meta, _f, ensure_ascii=False, indent=2)
print(f"  -> data/site_meta.json: latest={_site_meta['latest_patch_filename']}")

# Write ability-icon URL list for the validator (check_icons.py)
import json as _json_dump
with open('_ability_icons.txt', 'w', encoding='utf-8') as _f:
    for _u in sorted(_State.ability_icons):
        _f.write(_u + '\n')
print(f"  → _ability_icons.txt: {len(_State.ability_icons)} unique URLs")


# Patch-dynamics manifest: per-entity tag tallies across every patch, plus the
# patches list (newest-first per RELEASE_HISTORY) so the JS widget can window
# the last 12 patches BACKWARD from whichever patch page the user is on.
# Patches missing an HTML page (e.g. 7.39e — no rendered changelog yet) emit
# filename=null; the widget renders them as non-clickable empty cells.
_have_html = {p["version"]: p["filename"].split("/")[-1] for p in PATCHES}
_dyn_patches = [{"version": r["version"],
                 "filename": _have_html.get(r["version"]),
                 "date": r["date"]} for r in RELEASE_HISTORY]
# Full hero roster (every hero, even those untouched in a rendered patch) so the
# heroes_dyn matrix page lists the COMPLETE alphabetical roster. name → icon slug
# + dynamics key. build_heroes_dyn.py reads this without importing this module.
_hero_roster = [{"name": _n, "icon": _s, "key": "hero|" + _slugify(_n)}
                for _n, _s in sorted(HERO_SLUG.items())]
# Spirit Bear — Lone Druid's pet, a creep-hero since 7.40. Tracked under its own
# dynamics key (unit_header in every patch, including pre-hero ones), so the
# heroes_dyn matrix shows its FULL change history, not just 7.40+.
_hero_roster.append({"name": "Spirit Bear", "icon": "spirit_bear",
                     "key": "creep-hero|spirit-bear"})
_hero_roster.sort(key=lambda h: h["name"].lower())
# Item roster for the items_dyn matrix: every item/enchantment that appears in the
# dynamics (touched across tracked patches). Each entry carries its icon slug
# (icons/items/<icon>.png) plus two game-file-derived fields used by the page's
# filters: `class` (regular item / neutral item / enchantment) and `current`
# (still in the game vs removed/obsolete). Classification reads the LATEST patch's
# items.txt — authoritative, no patch-note dependency.
_latest_stats_ver = next(
    (_r["version"] for _r in RELEASE_HISTORY
     if _os.path.exists(_os.path.join(_os.path.dirname(__file__), "data", "stats",
                                      _r["version"], "items.txt"))),
    RELEASE_HISTORY[0]["version"])
_NEUTRAL_SLUGS, _OBSOLETE_SLUGS, _PRESENT_SLUGS = _load_item_classes(_latest_stats_ver)

# Current neutral pool — AUTO-DERIVED from Valve's datafeed (data/itemlist.json),
# field `neutral_item_tier` (>= 0 means it's in the live droppable pool; -1 means
# not / cycled out). This is authoritative and self-updating: refresh itemlist.json
# (`python scripts/fetch_itemlist.py`) when a new patch lands and the added/removed/
# cycled neutrals are picked up automatically — no hand-maintained list.
# Why the datafeed and not items.txt: items.txt keeps every dropped neutral flagged
# `ItemIsNeutralActiveDrop "1"` forever (never IsObsolete), so it can't tell active
# from cycled-out; the datafeed tier can. (Earlier a hand-written Liquipedia list was
# used but it silently missed Cloak of Flames / Dandelion Amulet / Medallion of
# Courage — all re-added as neutrals in 7.41 — which the datafeed has correctly.)
def _load_neutral_pool_current():
    """Set of game slugs currently in the neutral drop pool, from the datafeed's
    `neutral_item_tier` (>= 0). Empty set (with a warning) if the file is missing —
    callers then treat all neutrals as cycled-out, which is visible-wrong but safe."""
    path = _os.path.join(_os.path.dirname(__file__), "data", "itemlist.json")
    try:
        data = _json.load(open(path, encoding="utf-8"))
        items = data["result"]["data"]["itemabilities"]
    except (OSError, KeyError, ValueError) as exc:
        print(f"  ! itemlist.json unreadable ({exc}) — neutral pool empty")
        return set()
    return {it["name"] for it in items
            if it.get("neutral_item_tier", -1) >= 0
            and not it["name"].startswith("item_recipe_")}


_NEUTRAL_POOL_CURRENT = _load_neutral_pool_current()


def _load_neutral_tier_map():
    """{game slug → tier int} from data/itemlist.json. Used to sort neutrals by
    tier 1-5 in the items_dyn default order. Cycled-out neutrals have
    `neutral_item_tier` = -1; we keep them but bucket as tier 99 so they sort
    after the live pool (still ahead of enchants). Empty dict if itemlist is
    missing — neutrals then fall back to alpha within the neutral block."""
    path = _os.path.join(_os.path.dirname(__file__), "data", "itemlist.json")
    try:
        data = _json.load(open(path, encoding="utf-8"))
        items = data["result"]["data"]["itemabilities"]
    except (OSError, KeyError, ValueError):
        return {}
    return {it["name"]: (it.get("neutral_item_tier") if it.get("neutral_item_tier", -1) >= 0
                          else 99)
            for it in items
            if not it["name"].startswith("item_recipe_")}


_NEUTRAL_TIER_BY_SLUG = _load_neutral_tier_map()
# Items that never shipped — excluded from the matrix entirely:
#  • vestigial neutrals flagged BOTH neutral AND SpeciallyBannedFromNeutralSlot
#    (Greater Mango / Greater Faerie Fire);
#  • neutrals "Added to game files, unreleased item" per Liquipedia (Bottomless
#    Chalice / Horizon / Mechanical Arm — never released, no removal patch);
#  • unreleased neutral-item ENCHANTMENTS — the 5 that never appeared in any patch
#    note (Unleashed/curious, Dominant, Fierce, Restorative, Thick; Liquipedia has
#    no page for them → 404). Released-then-removed enchants (Wise/Boundless/Vast)
#    are NOT here — they stay as removed.
_PHANTOM_ITEMS = {
    "item_greater_mango", "item_greater_faerie_fire",
    "item_bottomless_chalice", "item_horizon", "item_mechanical_arm",
    "item_enhancement_curious", "item_enhancement_dominant",
    "item_enhancement_fierce", "item_enhancement_restorative",
    "item_enhancement_thick",
}


def _load_neutral_cycled_versions():
    """icon-slug -> patch version where a neutral was "cycled out" of the pool,
    scraped from the historical patch notes. Dates the lifespan end of cycled-out
    neutrals. Only ~7.33+ used this phrasing; older cycle-outs have no dated event
    (those rows stay hidden with an open-ended lifespan)."""
    out = {}
    path = _os.path.join(_os.path.dirname(__file__), "data", "patchnotes_english.txt")
    try:
        for ln in open(path, encoding="utf-8").read().splitlines():
            if "cycled out" in ln.lower():
                mk = re.search(r'_item_([a-z0-9_]+)"', ln)
                mv = re.search(r'DOTA_Patch_(\d+_\d+[a-z]?)_', ln)
                if mk and mv:
                    out[mk.group(1)] = mv.group(1).replace("_", ".")
    except OSError:
        pass
    return out


_NEUTRAL_CYCLED = _load_neutral_cycled_versions()

# Cycle-out versions for older neutrals (pre-7.33, before the "Item cycled out" wording
# existed) — sourced from each item's Liquipedia /Changelogs page (the latest REMOVED
# entry). Keyed by icon slug. Merged into _NEUTRAL_CYCLED so the matrix blanks their
# cells (n/a) after removal. The big 7.38 cluster = that patch's neutral overhaul.
_NEUTRAL_REMOVED_MANUAL = {
    "ancient_guardian": "7.38", "arcane_ring": "7.38", "force_field": "7.38",
    "ascetic_cap": "7.38", "avianas_feather": "7.38", "ballista": "7.30",
    "book_of_shadows": "7.38", "broom_handle": "7.38", "bullwhip": "7.38",
    "clumsy_net": "7.28", "craggy_coat": "7.38", "doubloon": "7.38",
    "dragon_scale": "7.38", "elixer": "7.23d", "elven_tunic": "7.38",
    "enchanted_quiver": "7.38", "faded_broach": "7.38", "paintball": "7.32",
    "force_boots": "7.38", "fusion_rune": "7.24", "giants_ring": "7.38",
    "grove_bow": "7.38", "havoc_hammer": "7.38", "illusionsts_cape": "7.30",
    "imp_claw": "7.30", "ironwood_tree": "7.30", "keen_optic": "7.32",
    "lance_of_pursuit": "7.38", "light_collector": "7.38", "mirror_shield": "7.38",
    "ocean_heart": "7.32", "phoenix_ash": "7.24", "princes_knife": "7.28",
    "quicksilver_amulet": "7.32", "repair_kit": "7.28", "royal_jelly": "7.38",
    "safety_bubble": "7.38", "seer_stone": "7.38", "spy_gadget": "7.38",
    "the_leveller": "7.32", "third_eye": "7.23c", "tome_of_aghanim": "7.23a",
    "trickster_cloak": "7.38", "trident": "7.28", "unwavering_condition": "7.38",
    "vambrace": "7.38", "vindicators_axe": "7.38", "witless_shako": "7.28",
    "woodland_striders": "7.28",
}
_NEUTRAL_CYCLED.update(_NEUTRAL_REMOVED_MANUAL)   # manual (Liquipedia) wins on conflict

# Shop categories (the player-facing shop tabs) for the items_dyn Category filter.
# Internal section keys from the game's shop layout (data/shops.txt) → display name,
# in shop order. sideshop/pregame/event sections are intentionally excluded (they
# duplicate items). Valve reshuffles these between patches (7.41 "Shop Reshuffle"),
# so refreshing data/shops.txt (scripts/extract_shops.py) updates the filter.
_SHOP_CATEGORY_ORDER = [
    ("consumables", "Consumables"), ("attributes", "Attributes"),
    ("weapons_armor", "Equipment"), ("misc", "Miscellaneous"),
    ("secretshop", "Secret Shop"),
    ("basics", "Accessories"), ("support", "Support"), ("magics", "Magical"),
    ("defense", "Armor"), ("weapons", "Weapons"), ("artifacts", "Armaments"),
]
_SHOP_CATEGORY_OTHER = "Other"  # regular items not in any shop tab (boss rewards,
#                                 collectibles, Aghanim's Blessing, removed items)


def _load_shop_categories():
    """{game_slug: category_display} from data/shops.txt. Each item gets the FIRST
    included section it appears in (sections = shop tabs; an item is normally in
    exactly one). {} if the file is absent — then every regular item is 'Other'."""
    path = _os.path.join(_os.path.dirname(__file__), "data", "shops.txt")
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return {}
    want = dict(_SHOP_CATEGORY_ORDER)
    # Section header = a lone quoted key on its own line. Allow a trailing // comment
    # (shops.txt has `"magics" // Magical`) — without this the section is missed and
    # its items fall through to the previous section.
    sec_re = re.compile(r'^\s*"([a-z0-9_]+)"\s*(?://.*)?$')
    item_re = re.compile(r'^\s*"item"\s*"(item_[a-z0-9_]+)"')
    per_cat = {}
    sections_with_items = set()
    cur = None
    for ln in lines:
        mi = item_re.match(ln)
        if mi:
            if cur:
                sections_with_items.add(cur)
            if cur in want:
                per_cat.setdefault(cur, []).append(mi.group(1))
            continue
        ms = sec_re.match(ln)
        if ms:
            cur = ms.group(1)
    # Self-flag a NEW shop tab Valve might add: a section with items that we don't map
    # AND isn't an intentionally-excluded duplicate (root / sideshop* / *pregame*).
    # Such items silently fall to "Other" until added to _SHOP_CATEGORY_ORDER — warn so
    # we notice instead of mislabelling them.
    def _ignored(s):
        return s == "dota_shops" or s.startswith("sideshop") or "pregame" in s
    unknown = sorted(s for s in sections_with_items
                     if s not in want and not _ignored(s))
    if unknown:
        print(f"  ! shops.txt has UNMAPPED shop section(s): {unknown} — items there "
              f"fall to 'Other'. Add them to _SHOP_CATEGORY_ORDER in build_patch.py.")
    out = {}
    for key, _disp in _SHOP_CATEGORY_ORDER:   # priority = shop order, first wins
        for slug in per_cat.get(key, []):
            out.setdefault(slug, want[key])
    return out


_SHOP_CATEGORIES = _load_shop_categories()


def _item_category(gslug, cls):
    """Display category for the items_dyn filter — only regular items get one
    (neutrals/enchantments aren't shop items → None → exempt from the filter)."""
    if cls != "regular":
        return None
    return _SHOP_CATEGORIES.get(gslug, _SHOP_CATEGORY_OTHER)


def _item_class_and_current(rec):
    """(class, current) for an item/enchant dynamics record. class ∈ {regular,
    neutral, enchant}. current: regular/enchant = in latest items.txt and not
    IsObsolete; neutral = in the live pool (`_NEUTRAL_POOL_CURRENT`) — a cycled-out
    neutral is still flagged in the files but is NOT current."""
    icon = rec.get("icon", rec["name"].lower().replace(" ", "_").replace("'", ""))
    gslug = "item_" + icon
    if rec.get("kind") == "enchant":
        cls = "enchant"
    elif (gslug in _NEUTRAL_SLUGS or rec.get("neutral_section")
          or gslug in _NEUTRAL_POOL_CURRENT):
        cls = "neutral"
    else:
        cls = "regular"
    if cls == "neutral":
        current = gslug in _NEUTRAL_POOL_CURRENT
    else:
        current = (gslug in _PRESENT_SLUGS) and (gslug not in _OBSOLETE_SLUGS)
    return cls, current


# Chronological patch order (oldest → newest) for item lifespan windows.
_CHRON = [_r["version"] for _r in reversed(RELEASE_HISTORY)]
_CHRON_IDX = {_v: _i for _i, _v in enumerate(_CHRON)}


def _added_version(icon):
    """Oldest patch whose items.json contains this item (= the patch it entered the
    game). Authoritative across all 116 patches (every patch has items.json).
    Patches BEFORE this are blanked in the matrix. None if never found."""
    gslug = "item_" + icon
    for _v in _CHRON:
        if gslug in _STATS_I.get(_v, {}):
            return _v
    return None


def _presence_window(icon):
    """(first_present_version, last_present_version_if_gone_else_None) by scanning
    every patch's items.json for `item_<icon>`. Blanks the matrix outside an item's
    real lifespan: columns before it first appears render as faint "n/a" dots, and —
    if it has disappeared from the game files — columns after its last appearance do
    too. If it's still in the latest patch, the second value is None (no after-blank
    from files; a patch-note removal is handled separately for touched items)."""
    gslug = "item_" + icon
    pres = [_v for _v in _CHRON if gslug in _STATS_I.get(_v, {})]
    if not pres:
        return None, None
    removed = None if pres[-1] == _CHRON[-1] else pres[-1]
    return pres[0], removed


# ---- Full game-item roster (parity with heroes_dyn listing every hero) -------
# items_dyn lists EVERY real item, not just the ones touched in tracked patches —
# untouched items render as empty rows, exactly like untouched heroes on heroes_dyn.
# Source = the latest items.txt + datafeed display names (data/itemlist.json; slugs
# are often legacy joke names — item_angels_demise = "Khanda", item_gungir =
# "Gleipnir" — so the datafeed name_english_loc is authoritative, titlecased-slug
# fallback otherwise). Inclusion mirrors Liquipedia's Portal:Items (the reference
# the user gave):
#   • neutral items + enchantments — all of them;
#   • regular shop items with a gold cost (purchasable);
#   • a small allowlist of FREE / boss-reward / collectible items worth tracking
#     (Aegis, Cheese, Refresher Shard, Roshan's Banner, Healing Lotus x3, Block of
#     Cheese, Madstone, Observer Ward, Aghanim's Blessing);
#   • removed items (IsObsolete) — kept too, marked current=False (Deleted toggle).
# Dropped: recipes; numbered/level VARIANTS (Dagon 2-5, Bracer 2, Boots of Travel 2,
#   *_2/_3…, *_roshan, *_broken, tango_single) EXCEPT the distinct named
#   item_ultimate_scepter_2 (Aghanim's Blessing); a blocklist of junk/event dummies
#   (Bag of Gold, River Vials, caster_rapier, pocket_roshan); unreleased FREE items
#   (apex, ofrenda*, grisgris … auto-dropped — free and not in the allowlist); and
#   anything without an icon. Per the user: "all items, no variants / event pickups".
_FREE_ALLOW = {
    "item_aegis", "item_cheese", "item_refresher_shard", "item_roshans_banner",
    "item_famango", "item_great_famango", "item_greater_famango",
    "item_royale_with_cheese", "item_ward_observer",
    # NB: Madstone Bundle is intentionally NOT here — it's a currency, never
    # buffed/nerfed, so it has no place in a balance-change matrix.
    # Aghanim's Blessing — a distinct named item (Roshan drop / hidden shop), NOT a
    # mere level variant, so it's exempt from both the variant and the cost filters.
    "item_ultimate_scepter_2",
}
_ITEM_BLOCK = {"item_furion_gold_bag", "item_caster_rapier", "item_pocket_roshan"}
# Removal patch for obsolete items that items.json keeps keyed forever (so the
# per-patch presence scan can't date the removal). Confirmed from the historical
# patch notes (data/patchnotes_english.txt: "Item removed from the game" /
# "Item cycled out" / Eternal Shroud "No longer requires Hood of Defiance") and
# Liquipedia (Stout Shield 7.23). Used to blank the matrix AFTER the item left the
# game (n/a dots). Touched obsolete items (Cornucopia / Eternal Shroud) already get
# their removal from the patch-note DEL row (`removed_in`), so they're not here.
_OBSOLETE_REMOVED = {
    "item_necronomicon": "7.29",        # "Removed Item"
    "item_hood_of_defiance": "7.33",    # folded into Eternal Shroud
    "item_flicker": "7.33",             # "Item cycled out" (neutral)
    "item_nether_shawl": "7.33",        # "Item cycled out" (neutral)
    "item_wraith_pact": "7.33",         # "Item removed from the game"
    "item_tome_of_knowledge": "7.33",   # "Item removed from the game"
    "item_quarterstaff": "7.35",        # "Item removed from the game"
    "item_stout_shield": "7.23",        # Liquipedia: removed 7.23 (Outlanders)
}


def _load_full_game_items():
    """[(game_slug, icon, display_name, cls, is_removed), ...] for every real item."""
    txt_path = _os.path.join(_os.path.dirname(__file__), "data", "stats",
                             _latest_stats_ver, "items.txt")
    purch, cost = {}, {}
    cur = None
    name_re = re.compile(r'^\s*"(item_[a-z0-9_]+)"\s*$')
    cost_re = re.compile(r'^\s*"ItemCost"\s*"(\d+)"')
    try:
        for ln in open(txt_path, encoding="utf-8").read().splitlines():
            m = name_re.match(ln)
            if m:
                cur = m.group(1)
                purch[cur] = True
                continue
            if not cur:
                continue
            if 'ItemPurchasable' in ln and '"0"' in ln:
                purch[cur] = False
            mc = cost_re.match(ln)
            if mc:
                cost[cur] = int(mc.group(1))
    except OSError:
        return []
    names = {}
    try:
        _il = _json.load(open(_os.path.join(_os.path.dirname(__file__),
                              "data", "itemlist.json"), encoding="utf-8"))
        for _it in _il["result"]["data"]["itemabilities"]:
            names[_it["name"]] = _it.get("name_english_loc")
    except (OSError, KeyError, ValueError):
        pass
    icons_dir = _os.path.join(_os.path.dirname(__file__), "icons", "items")
    try:
        icon_files = set(_os.listdir(icons_dir))
    except OSError:
        icon_files = set()
    variant_re = re.compile(r'(_\d+|_roshan|_broken)$')
    out = []
    for gslug in _PRESENT_SLUGS:
        if gslug.startswith("item_recipe_") or gslug in _PHANTOM_ITEMS:
            continue
        icon = gslug[len("item_"):]
        if icon + ".png" not in icon_files:
            continue
        if gslug in _ITEM_BLOCK or gslug.startswith("item_river_painter"):
            continue
        # Drop numbered/level variants — but keep the ones that are a real distinct
        # item (Aghanim's Blessing) or a current neutral (Stygian Desolator =
        # desolator_2).
        if (variant_re.search(gslug) or gslug == "item_tango_single") \
                and gslug not in _FREE_ALLOW and gslug not in _NEUTRAL_POOL_CURRENT:
            continue
        is_obsolete = gslug in _OBSOLETE_SLUGS
        added, gone = _presence_window(icon)
        if gslug.startswith("item_enhancement_"):
            cls, current, removed = "enchant", True, gone
        elif gslug in _NEUTRAL_SLUGS or gslug in _NEUTRAL_POOL_CURRENT:
            cls = "neutral"
            current = gslug in _NEUTRAL_POOL_CURRENT
            # cycled-out neutral → end its lifespan at the cycle-out patch (n/a after)
            removed = None if current else (_NEUTRAL_CYCLED.get(icon) or gone)
        else:
            cls = "regular"
            # regular: keep purchasable shop items with a gold cost, the free-item
            # allowlist, and removed items; drop free unreleased / event dummies.
            if not (gslug in _FREE_ALLOW or is_obsolete
                    or (purch.get(gslug, True) and (cost.get(gslug) or 0) > 0)):
                continue
            current = not is_obsolete
            removed = (_OBSOLETE_REMOVED.get(gslug) or gone) if is_obsolete else gone
        nm = names.get(gslug) or icon.replace("_", " ").title()
        cost_v = _STATS_I.get(_latest_stats_ver, {}).get(gslug, {}).get("ItemCost", 0)
        # Neutrals / enchantments aren't purchasable → no price (exempt from the
        # price-range filter) even if a residual ItemCost lingers in the files.
        price = None if cls in ("neutral", "enchant") else (
            cost_v if (cost_v and cost_v > 0) else None)
        out.append({"_gslug": gslug, "name": nm, "icon": icon, "class": cls,
                    "current": current, "added": added, "removed": removed,
                    "category": _item_category(gslug, cls),
                    "tier": _NEUTRAL_TIER_BY_SLUG.get(gslug) if cls == "neutral" else None,
                    "price": price})
    return out


_item_roster = []
for _k, _r in _State.dynamics.items():
    if _r.get("kind") not in ("item", "enchant"):
        continue
    _cls, _current_gf = _item_class_and_current(_r)
    _icon = _r.get("icon", _r["name"].lower().replace(" ", "_").replace("'", ""))
    # Removal: a patch-note "Removed" / "Item cycled out" (item or enchant) is
    # AUTHORITATIVE — Valve keeps obsolete enchant + cycled-out neutral definitions
    # in items.txt WITHOUT IsObsolete, so the game-file `current` alone misses them
    # (Wise/Boundless/Vast removed 7.41; Spark of Courage etc. cycled out 7.40).
    _removed = _r.get("removed_in")
    # Returned guard: if the item was touched in a patch strictly NEWER than its
    # removal patch, it came back into the game/pool → no longer removed.
    if _removed:
        _touch = [_CHRON_IDX[_p] for _p in _r.get("patches", {}) if _p in _CHRON_IDX]
        if _touch and max(_touch) > _CHRON_IDX.get(_removed, -1):
            _removed = None
    # Neutral pool membership is authoritative: a neutral in the live pool is current
    # (clear any stale removal); a cycled-out one is NOT current — date its lifespan
    # end from the "cycled out" patch-note event when we have one (else open-ended,
    # but hidden anyway since current=False).
    if _cls == "neutral":
        if _current_gf:
            _removed = None
        elif _removed is None:
            _removed = _NEUTRAL_CYCLED.get(_icon)
    _current = _current_gf and (_removed is None)
    # Lifespan: blank patches before `added`; if removed, also blank after `removed`.
    # Gold cost (latest items.json) for the items_dyn price filter. Neutrals +
    # enchantments are 0 (not purchasable) → store None so they're EXEMPT from the
    # range filter rather than treated as "free" and hidden when a min is set.
    _cost = _STATS_I.get(_latest_stats_ver, {}).get("item_" + _icon, {}).get("ItemCost", 0)
    _item_roster.append({
        "name": _r["name"], "icon": _icon, "key": _k,
        "class": _cls, "current": _current,
        "added": _added_version(_icon), "removed": _removed,
        "category": _item_category("item_" + _icon, _cls),
        "tier": _NEUTRAL_TIER_BY_SLUG.get("item_" + _icon) if _cls == "neutral" else None,
        "price": _cost if (_cost and _cost > 0) else None})
# Add every real game item NOT touched in any tracked patch, so the matrix lists
# ALL items (parity with heroes_dyn). Dedup by the icon's game slug — a touched item
# already carries the richer entry (tallies, removed_in, lifespan). `_load_full_game_items`
# returns ready-made roster dicts (class / current / lifespan already resolved per the
# game files + Liquipedia pool); we only drop the dedup key and add the matrix key.
_touched_gslugs = {"item_" + _d["icon"] for _d in _item_roster}
for _e in _load_full_game_items():
    if _e.pop("_gslug") in _touched_gslugs:
        continue
    _e["key"] = "item|" + _e["icon"]
    _item_roster.append(_e)
# Default (neutral-sort) row order in items_dyn:
#  • regular items first, grouped by category in _SHOP_CATEGORY_ORDER (Consumables,
#    Attributes, Equipment, Miscellaneous, Secret Shop, Accessories, Support, Magical,
#    Armor, Weapons, Armaments), alpha within each category;
#  • neutral items next, by tier 1→5 (then 99 = cycled-out), alpha within each tier;
#  • enchantments last, alpha.
# Clicking the Item header in the UI cycles through name-desc / name-asc; clicking
# back to neutral state restores THIS order via the originalOrder snapshot in
# scripts.js, so the user always returns to a category-grouped view.
_CLASS_ORDER = {"regular": 0, "neutral": 1, "enchant": 2}
_CAT_INDEX = {_disp: _i for _i, (_, _disp) in enumerate(_SHOP_CATEGORY_ORDER)}
_CAT_INDEX[_SHOP_CATEGORY_OTHER] = len(_SHOP_CATEGORY_ORDER)  # Other after the named cats


def _item_default_sort_key(_d):
    _cls_rank = _CLASS_ORDER.get(_d.get("class"), 99)
    _cat_rank = _CAT_INDEX.get(_d.get("category"), len(_CAT_INDEX)) \
        if _d.get("class") == "regular" else 0
    _tier_rank = _d.get("tier") if _d.get("class") == "neutral" else 0
    if _tier_rank is None:
        _tier_rank = 99
    return (_cls_rank, _cat_rank, _tier_rank, _d["name"].lower())


_item_roster.sort(key=_item_default_sort_key)
# Ordered list of categories actually present (for the items_dyn Category dropdown).
_present_cats = {_d.get("category") for _d in _item_roster if _d.get("category")}
_item_cat_list = [_disp for _k, _disp in _SHOP_CATEGORY_ORDER if _disp in _present_cats]
if _SHOP_CATEGORY_OTHER in _present_cats:
    _item_cat_list.append(_SHOP_CATEGORY_OTHER)
_dyn_payload = {"patches": _dyn_patches, "entities": _State.dynamics,
                "heroes": _hero_roster, "items": _item_roster,
                "item_categories": _item_cat_list}
with open('_dynamics.json', 'w', encoding='utf-8') as _f:
    _json_dump.dump(_dyn_payload, _f, separators=(',', ':'))
print(f"  → _dynamics.json: {len(_State.dynamics)} entities × {len(_dyn_patches)} patches in RELEASE_HISTORY")
_cls_counts = {}
for _d in _item_roster:
    _cls_counts[_d["class"]] = _cls_counts.get(_d["class"], 0) + 1
_n_removed = sum(1 for _d in _item_roster if not _d["current"])
print(f"     items_dyn roster: {len(_item_roster)} ({_cls_counts}); "
      f"{_n_removed} not current (class source: {_latest_stats_ver}/items.txt)")
