#!/usr/bin/env python3
"""Generate annotated Dota 2 7.41c patch notes HTML."""

import json as _json
import os as _os

# ---------- STATS DATABASE ----------
# Loads data/stats/{version}/heroes.json + items.json into memory at build time.
# Use stat_h(hero_display, field, version) / stat_i(item_display, field, version)
# to look up values. Use bstat_h() to auto-generate a badge from a delta.

def _load_stats_db():
    db_h, db_i = {}, {}
    base = _os.path.join(_os.path.dirname(__file__), "data", "stats")
    if not _os.path.isdir(base):
        return db_h, db_i
    for ver in _os.listdir(base):
        vdir = _os.path.join(base, ver)
        if not _os.path.isdir(vdir):
            continue
        hf = _os.path.join(vdir, "heroes.json")
        if _os.path.exists(hf):
            with open(hf, encoding="utf-8") as f:
                db_h[ver] = _json.load(f)
        itf = _os.path.join(vdir, "items.json")
        if _os.path.exists(itf):
            with open(itf, encoding="utf-8") as f:
                db_i[ver] = _json.load(f)
    return db_h, db_i

_STATS_H, _STATS_I = _load_stats_db()


def stat_h(hero_display: str, field: str, version: str):
    """
    Возвращает числовое значение стата героя в указанном патче или None.

    hero_display — отображаемое имя (как в HERO_SLUG), например "Doom"
    field        — ключ из npc_heroes.txt, например "ArmorPhysical",
                   "AttackDamageMin", "MovementSpeed", "AttributeBaseStrength"
    version      — патч, в котором ищем, например "7.41"

    Пример:
        # Doom Base Armor в патче 7.41 (ДО изменений 7.41a)
        old = stat_h("Doom", "ArmorPhysical", "7.41")  # → 4
        W(li("Base Armor decreased by 1", b(old, old - 1)))
    """
    # Конвертируем имя → npc slug
    raw_slug = HERO_SLUG.get(hero_display,
                              hero_display.lower().replace(" ", "_").replace("'", ""))
    npc_key = "npc_dota_hero_" + raw_slug
    return _STATS_H.get(version, {}).get(npc_key, {}).get(field)


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


def bstat_i(item_display: str, field: str, patch_before: str, delta,
            l: bool = False):
    """Аналог bstat_h для предметов."""
    old = stat_i(item_display, field, patch_before)
    if old is None:
        return t("NERF") if delta < 0 else t("BUFF")
    new = old + delta
    return b(old, new, l=l)


# ---------- IMAGE URL HELPERS ----------

HERO_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/"
ITEM_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/"
ABIL_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/"

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


def b(old, new, l=False):
    """Generate per-level badges. old/new can be scalar or list.
    l=True means lower-is-buff (cooldowns, mana costs, penalties).
    If all per-level badges turn out identical, collapses to a single badge.
    Determines OVERALL buff/nerf tag for filtering:
      - avg of signed per-level %s; sign decides
      - if avg rounds to 0 → use last non-zero level"""
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
        if o == 0 or n == o:
            parts.append('<span class="badge neutral">0%</span>')
            keys.append(("neutral", "0%"))
            signed_pcts.append(0)
            continue
        raw = (n - o) / o * 100
        pct = round(raw)
        if pct == 0:
            parts.append('<span class="badge neutral">0%</span>')
            keys.append(("neutral", "0%"))
            signed_pcts.append(0)
            continue
        is_buff = (n < o) if l else (n > o)
        magnitude = abs(pct)
        signed_pcts.append(magnitude if is_buff else -magnitude)
        sign = "+" if is_buff else "-"
        cls = gradient_class(magnitude, is_buff)
        display = f"{sign}{magnitude}%"
        parts.append(f'<span class="badge {cls}">{display}</span>')
        keys.append((cls, display))

    # Determine overall tag.
    # Logic: avg of signed per-level %s; sign decides.
    # If avg rounds to 0 → fall back to last non-zero level.
    overall = ""
    if signed_pcts:
        avg = sum(signed_pcts) / len(signed_pcts)
        if round(avg) > 0:
            overall = "buff"
        elif round(avg) < 0:
            overall = "nerf"
        else:
            for v in reversed(signed_pcts):
                if v > 0:
                    overall = "buff"
                    break
                if v < 0:
                    overall = "nerf"
                    break

    # Collapse if every level produced an identical badge
    if len(keys) > 1 and len(set(keys)) == 1:
        parts = [parts[0]]

    overall_attr = f' data-overall="{overall}"' if overall else ""
    return f'<span class="badge-group"{overall_attr}>' + "".join(parts) + "</span>"


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
    sign = "+" if is_buff else "-"
    cls = gradient_class(magnitude, is_buff)
    return (cls, f"{sign}{magnitude}%", magnitude if is_buff else -magnitude,
            "buff" if is_buff else "nerf")


_formula_id_counter = [0]

def fold(text):
    """Wrap an OLD formula in a span with subtle dotted underline (visual reference only)."""
    return f'<span class="formula-old">{text}</span>'


def bf(old_fn, new_fn, formula_text, levels=None, l=False, value_fmt="{:g}",
       level_prefix='L', level_fmt=None, jump_at=20, headline_level=1):
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

    # Headline-level inline badge (used when row is collapsed)
    cls1, disp1, _, overall1 = _compute_pct(old_fn(headline_level), new_fn(headline_level), l)
    overall_attr = f' data-overall="{overall1}"' if overall1 else ""
    badge = f'<span class="badge-group"{overall_attr}><span class="badge {cls1}">{disp1}</span></span>'

    # Trigger
    trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'

    def cls_for(L):
        return ' class="lvl-jump"' if L == jump_at else ''

    head_cells = "".join(f'<th{cls_for(L)}>{level_fmt(L)}</th>' for L in levels)
    old_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(old_fn(L))}</td>' for L in levels)
    new_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(new_fn(L))}</td>' for L in levels)

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

def _open_block():
    s = ('</div>\n' if _State.block_open else '') + '<div class="entity-block">\n'
    _State.block_open = True
    return s

def _close_block():
    if _State.block_open:
        _State.block_open = False
        return '</div>\n'
    return ''


def hero_header(name):
    _State.current_hero = HERO_SLUG.get(name, name.lower().replace(" ", "_").replace("'", "").replace("-", ""))
    return _open_block() + f'''<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="{hero_img(name)}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def unit_header(name, icon_url):
    """Header for a separate summoned unit (e.g. Spirit Bear) with custom icon URL."""
    _State.current_hero = None
    return _open_block() + f'''<div class="entity hero-entity">
  <div class="entity-icon ability-icon"><img src="{icon_url}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def item_header(name, new=False):
    """Item header. If new=True, appends a NEW badge to the entity name."""
    _State.current_hero = None
    new_badge = ' <span class="badge new" data-tag="new" data-overall="buff">NEW</span>' if new else ''
    return _open_block() + f'''<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="{item_img(name)}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}{new_badge}</div>
</div>'''


def plain_header(name):
    _State.current_hero = None
    return _open_block() + f'<div class="entity plain-entity"><div class="entity-name">{name}</div></div>'


def enchant_header(name, slug=None):
    """Header for a Neutral Enchantment with item-style icon.
    slug: short name (e.g. 'crude'); CDN file = items/enhancement_<slug>.png.
    If slug is None, derives from `name` (lowercased)."""
    if slug is None:
        slug = name.lower().replace(" ", "_").replace("'", "")
    icon = f"{ITEM_CDN}enhancement_{slug}.png"
    return _open_block() + f'''<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="{icon}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def section(title):
    _State.current_hero = None
    return _close_block() + f'<h2 class="section">{title}</h2>'


def subgroup(title):
    return f'<h4 class="subgroup">{title}</h4>'


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
    # Pudge
    ("pudge", "Graft Flesh"): "innate_graft_flesh",
    # Storm Spirit
    ("storm_spirit", "Galvanized"): "galvanized",
}


def ability(title, slug=None):
    """Ability heading. Adds an icon when we know the CDN slug.
    The slug is derived from the current hero context + ability title:
      - manual override in ABILITY_DISPLAY_TO_SLUG, OR
      - naive: lowercased + spaces→underscores, with apostrophes/hyphens stripped.
    Image hides itself on 404 via onerror."""
    icon_html = ''
    if slug is None and _State.current_hero:
        hero = _State.current_hero
        key = (hero, title)
        if key in ABILITY_DISPLAY_TO_SLUG:
            ability_part = ABILITY_DISPLAY_TO_SLUG[key]
        else:
            ability_part = (title.lower()
                            .replace("'", "")
                            .replace("-", "_")
                            .replace(" ", "_")
                            .replace(".", ""))
        slug = f"{hero}_{ability_part}"
    if slug:
        icon_html = (f'<img src="{ABIL_CDN}{slug}.png" alt="" '
                     f'class="ability-icon-img" loading="lazy" '
                     f'onerror="this.style.display=\'none\'">')
    return f'<h4 class="ability-title">{icon_html}{title}</h4>'


def ul_open():
    return '<ul class="changes">'


def ul_close():
    return '</ul>'

import os
import re

def li(text, badge="", extra="", force_tag=None):
    """Generate <li>. Layout is: [left-tag] [description] [right percentages] [extra].
    The left tag is either:
      - Extracted from `badge` if it contains a text tag (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL)
      - OR derived from data-overall (numeric badges → BUFF or NERF text tag on left)
      - OR an empty placeholder for visual alignment if neither.
    Auto-extracts data-tag from badges for filtering."""
    if force_tag is not None:
        tag_str = force_tag
    else:
        tags = set()
        overalls = re.findall(r'data-overall="(\w+)"', badge)
        for o in overalls:
            tags.add(o)
        for tag_id in re.findall(r'data-tag="(\w+)"', badge):
            tags.add(tag_id)
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

    attr = f' data-tag="{tag_str}"' if tag_str else ""
    return f'<li{attr}>{left_tag}<span class="row-text">{text}</span>{rest}{extra}</li>'


def subnote(text):
    return f'<ul class="subnotes"><li>{text}</li></ul>'


def note_box(text):
    """Inline NOTE box for content NOT in the original patch (e.g. auto-derived
    base values like 'From 17 to 18'). Use as `extra=note_box(...)` of li()."""
    return f'<div class="correction-note"><span class="correction-label">Note</span>— {text}</div>'


def li_formula(prefix, old_formula, new_formula, old_fn, new_fn, l=False,
               rework_badge=True, **bf_kwargs):
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
    if rework_badge:
        full_badge = ('<span class="badge rework" data-tag="rework">REWORK</span>'
                      + badge)
    else:
        full_badge = badge
    return li(full_text, full_badge, extra=table)


# ---------- CSS ----------

CSS = """

* { box-sizing: border-box; margin: 0; padding: 0; }

/* Always reserve scrollbar space so content doesn't shift when filtering reduces page height */
html { scrollbar-gutter: stable; }

body {
  background: #0a0e13;
  background-image:
    radial-gradient(at 20% 0%, rgba(179, 45, 35, 0.08) 0, transparent 50%),
    radial-gradient(at 80% 100%, rgba(255, 100, 50, 0.05) 0, transparent 50%);
  background-attachment: fixed;
  color: #c9d1d9;
  font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.55;
  font-size: 15px;
  min-height: 100vh;
}

.container {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 28px 80px;
}

/* TOP NAV (full-width, sits above container) */
nav.top-nav {
  background:
    linear-gradient(180deg, rgba(120, 130, 142, 0.18) 0%, rgba(60, 68, 78, 0.18) 100%),
    #2a2f37;
  border-bottom: 1px solid #3a4048;
  width: 100%;
}
.nav-inner {
  width: 100%;
  padding: 10px 24px 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
}
.nav-tabs {
  display: flex;
  gap: 0;
  align-items: flex-end;
}
.nav-tab {
  padding: 7px 14px 10px;
  color: #c9d1d9;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  font-family: inherit;
  transition: background 0.15s, border-color 0.15s;
  display: inline-flex;
  align-items: center;
}
.nav-tab:hover {
  background: rgba(48, 54, 61, 0.4);
}
.nav-tab.active {
  background: rgba(0, 0, 0, 0.22);
  /* keep weight + transparent border identical to inactive — prevents header jump */
}
.nav-context {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

/* RELEASE INFO + VERSION — одна высота */
.nav-context .release-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 1px;
  background: rgba(0, 0, 0, 0.28);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  border: 1px solid transparent;
  padding: 0 12px;
  height: 38px;
  border-radius: 6px;
}
.nav-context .release-date {
  color: #c9d1d9;
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.3px;
  line-height: 1.15;
}
.nav-context .release-version {
  color: #79c0ff;
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
  line-height: 1.1;
  margin-bottom: 2px;
}
/* Calendar variant — no dropdown; .release-info takes its place on the right. */
.nav-context-calendar { margin-left: auto; }
.nav-context-calendar .release-info {
  align-items: center;
  padding: 0 18px;
  min-width: 110px;
}
.nav-context .patch-age {
  color: #a8b3bd;
  font-size: 10.5px;
  font-weight: 400;
  letter-spacing: 0.15px;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
}
.nav-context .version {
  color: #c9d1d9;
  font-size: 20px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
  background: rgba(0, 0, 0, 0.28);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  border: 1px solid transparent;
  padding: 0 14px;
  height: 38px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  font-family: inherit;
  line-height: 1;
  transition: background 0.15s;
}
.nav-context .version:hover {
  background: rgba(0, 0, 0, 0.4);
}
.nav-context .version-chev {
  font-size: 11px;
  color: #a8b3bd;
  line-height: 1;
  margin-top: 2px;
  font-weight: 600;
}

/* VERSION DROPDOWN MENU */
.version-dropdown {
  position: relative;
  display: inline-block;
}
.version-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 180px;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  padding: 6px;
  display: none;
  z-index: 100;
}
.version-menu.open {
  display: block;
}
.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  text-decoration: none;
  color: #c9d1d9;
  font-size: 14px;
  transition: background 0.12s ease;
}
.version-item:hover {
  background: #21262d;
}
.version-item.current {
  background: rgba(88, 166, 255, 0.10);
  color: #58a6ff;
  cursor: default;
  pointer-events: none;
}
.version-item .vi-name {
  font-weight: 700;
  letter-spacing: 0.3px;
}
.version-item .vi-date {
  color: #6e7681;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  margin-left: 14px;
}
.version-item.current .vi-date {
  color: rgba(88, 166, 255, 0.6);
}

/* NAV BACK ARROW — отдельная стрелка слева, как back-to-top, только в другую сторону */
.nav-back-arrow {
  position: fixed;
  top: 82px;
  left: 22px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(22, 27, 34, 0.92);
  border: 1px solid rgba(121, 192, 255, 0.45);
  color: #79c0ff;
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
  text-decoration: none;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
  transition: all 0.18s ease;
  z-index: 100;
  font-family: inherit;
  padding: 0;
  padding-bottom: 3px;
}
.nav-back-arrow:hover {
  background: rgba(121, 192, 255, 0.2);
  border-color: #79c0ff;
  transform: translateX(-2px);
}
.nav-back-arrow.visible {
  display: flex;
}

/* CALENDAR PAGE */
.calendar { margin: 24px 0; }
.cal-toggle-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-left: 0;
  font-size: 13px;
  color: #8b949e;
}
.cal-toggle-bar strong {
  color: #c9d1d9;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.cal-mode-select {
  background: #161b22;
  border: 1px solid #30363d;
  color: #c9d1d9;
  padding: 5px 28px 5px 12px;
  border-radius: 5px;
  font-family: inherit;
  font-size: 12.5px;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path fill='%238b949e' d='M0 0l5 6 5-6z'/></svg>");
  background-repeat: no-repeat;
  background-position: right 10px center;
}
.cal-mode-select:hover {
  border-color: #58a6ff;
}

/* YEAR BLOCK (shared between modes, collapsible) */
.cal-year-block {
  margin-bottom: 12px;
  background: #14191f;
  border: 1px solid #21262d;
  border-radius: 6px;
  overflow: hidden;
}
.cal-year-label {
  color: #c9d1d9;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
  cursor: pointer;
  user-select: none;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.12s;
}
.cal-year-label:hover {
  background: rgba(48, 54, 61, 0.25);
}
.cal-year-label::after {
  content: '▾';
  color: #6e7681;
  font-size: 11px;
  display: inline-block;
  transition: transform 0.15s;
}
.cal-year-block[data-collapsed="true"] .cal-year-label::after {
  transform: rotate(-90deg);
}
.cal-year-block[data-collapsed="true"] .cal-mode-full,
.cal-year-block[data-collapsed="true"] .cal-mode-compact {
  display: none;
}
.cal-mode-full, .cal-mode-compact {
  padding: 0 16px 14px;
}

/* MODE 2: COMPACT */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 4px;
}
.cal-month {
  display: flex;
  flex-direction: column;
}
.cal-month-name {
  text-align: center;
  font-size: 10.5px;
  color: #6e7681;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 6px;
}
.cal-month-cells {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-height: 44px;
  padding: 2px;
  border-left: 1px solid #21262d;
}
.cal-patch {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px 2px;
  border-radius: 4px;
  text-decoration: none;
  font-family: inherit;
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  transition: filter 0.15s, transform 0.13s ease;
  border: 1px solid transparent;
  position: relative;
}
.cal-patch:hover {
  filter: brightness(1.35);
  transform: scale(1.08);
  z-index: 3;
}
.cal-patch .cal-version {
  font-size: 9.5px;
  font-weight: 500;
  color: #b8b8b8;
  line-height: 1.1;
  margin-bottom: 2px;
  white-space: nowrap;
  text-decoration: underline;
  text-underline-offset: 2px;
  text-decoration-thickness: 1px;
  text-decoration-color: rgba(255, 255, 255, 0.30);
}
.cal-patch .cal-day {
  font-size: 13px;
  font-weight: 600;
  color: #c9d1d9;
  line-height: 1;
}
.cal-patch.sub {
  background: rgba(110, 118, 129, 0.22);
}
/* Major patches — unified solid orange (compact) */
.cal-patch.major {
  background: rgba(212, 138, 78, 0.60);
  border-color: rgba(212, 138, 78, 0.75);
}
.cal-patch.major .cal-day {
  color: #fff;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
}
.cal-patch.major .cal-version {
  color: rgba(255, 255, 255, 0.82);
  font-weight: 500;
  text-decoration-color: rgba(255, 255, 255, 0.40);
}

/* CURRENT patch — заранее увеличена (compact mode) */
.cal-patch.current {
  transform: scale(1.10);
  filter: brightness(1.12);
  z-index: 2;
  box-shadow:
    inset 0 1px 0 rgba(255, 235, 205, 0.35),
    0 0 0 2px rgba(121, 192, 255, 0.65),
    0 2px 6px rgba(0, 0, 0, 0.4);
}
.cal-patch.current:hover {
  transform: scale(1.18);
  z-index: 4;
}
span.cal-patch {
  cursor: default;
  opacity: 0.55;
}

/* MODE 1: FULL (every day) */
.cal-full-grid {
  display: grid;
  grid-template-columns: 60px repeat(31, 1fr);
  gap: 2px;
  font-variant-numeric: tabular-nums;
}
.cal-full-month-name {
  color: #8b949e;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 6px;
}
.cal-full-day {
  aspect-ratio: 1;
  min-height: 22px;
  border-radius: 3px;
  background: rgba(110, 118, 129, 0.05);
  font-size: 9.5px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4a5058;
  text-decoration: none;
  position: relative;
  transition: transform 0.13s ease, filter 0.13s, z-index 0s;
}
.cal-full-day.no-day { background: transparent; }
.cal-full-day.has-patch {
  font-weight: 700;
  font-size: 8.5px;
  letter-spacing: -0.2px;
  cursor: pointer;
}
.cal-full-day.has-patch:hover {
  transform: scale(1.6);
  z-index: 5;
  filter: brightness(1.25);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}
.cal-full-day.has-patch.sub {
  background: rgba(110, 118, 129, 0.4);
  color: #c9d1d9;
}
/* Major patches — unified solid orange (full grid) */
.cal-full-day.has-patch.major {
  background: rgba(212, 138, 78, 0.80);
  color: #fff;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.30);
}

/* CURRENT patch — заранее увеличена (full mode) */
.cal-full-day.has-patch.current {
  transform: scale(1.5);
  z-index: 4;
  filter: brightness(1.15);
  box-shadow:
    0 0 0 1.5px rgba(121, 192, 255, 0.55),
    0 2px 8px rgba(0, 0, 0, 0.55);
}
.cal-full-day.has-patch.current:hover {
  transform: scale(1.7);
  z-index: 6;
}

span.cal-full-day.has-patch {
  cursor: default;
  opacity: 0.7;
}

/* Display toggling */
.calendar.mode-compact .cal-mode-full { display: none; }
.calendar.mode-full .cal-mode-compact { display: none; }

/* TOOLBAR (legend tags + search in one row) */
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 6px 0 24px;
  padding: 8px 14px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  font-size: 13px;
  color: #8b949e;
}
.patch-age .age-sep {
  margin: 0 8px;
  opacity: 0.45;
  font-weight: 300;
}
.legend-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex-shrink: 0;
}
.legend-tags strong {
  color: #c9d1d9;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-right: 4px;
}

/* SEARCH BOX */
.search-box {
  position: relative;
  flex: 1 1 auto;
  min-width: 200px;
}
.search-box input {
  width: 100%;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 6px 12px;
  color: #c9d1d9;
  font-family: inherit;
  font-size: 13px;
  transition: border-color 0.15s;
}
.search-box input::placeholder { color: #6e7681; }
.search-box input:focus {
  outline: none;
  border-color: #58a6ff;
  box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.2);
}
.search-results {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  margin-top: 4px;
  max-height: 320px;
  overflow-y: auto;
  z-index: 50;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.5);
}
.search-results.show { display: block; }
.search-results .result-item {
  padding: 6px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #c9d1d9;
  border-bottom: 1px solid #21262d;
}
.search-results .result-item:last-child { border-bottom: none; }
.search-results .result-item:hover,
.search-results .result-item.active {
  background: rgba(88, 166, 255, 0.1);
  color: #fff;
}
.search-results .result-item img {
  width: 32px;
  height: 18px;
  object-fit: cover;
  border-radius: 2px;
  background: #21262d;
  flex-shrink: 0;
}
.search-results .result-item .kind {
  margin-left: auto;
  font-size: 10.5px;
  color: #6e7681;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}
.search-results .empty {
  padding: 10px 12px;
  color: #8b949e;
  font-style: italic;
  font-size: 12.5px;
}
.search-results mark {
  background: rgba(240, 198, 116, 0.25);
  color: inherit;
  padding: 0 1px;
  border-radius: 2px;
}

/* MAJOR SECTION */
h2.section {
  background:
    linear-gradient(90deg, rgba(0, 0, 0, 0.45) 0%, transparent 18%, transparent 82%, rgba(0, 0, 0, 0.45) 100%),
    linear-gradient(180deg, #b53528 0%, #4a120c 100%);
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  padding: 12px 18px;
  margin: 36px 0 20px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.4),
    0 2px 8px rgba(0, 0, 0, 0.4);
  text-shadow:
    1px 1px 0 rgba(0, 0, 0, 0.55),
    -1px 0 0 rgba(0, 0, 0, 0.35),
    0 -1px 0 rgba(0, 0, 0, 0.3),
    0 0 8px rgba(0, 0, 0, 0.5);
}

/* ENTITY (HERO/ITEM HEADER WITH ICON) */
.entity {
  display: flex;
  align-items: center;
  gap: 14px;
  background: linear-gradient(90deg, #1a1f29 0%, #161b22 100%);
  border-radius: 4px;
  padding: 8px 14px;
  margin: 20px 0 8px;
}
.entity-name {
  color: #f0c674;
  font-size: 19px;
  font-weight: 700;
}
.entity-icon img {
  display: block;
  border-radius: 3px;
}
.hero-icon img {
  width: 80px;
  height: 45px;
  object-fit: cover;
}
.item-icon img {
  width: 50px;
  height: 36px;
  object-fit: cover;
}
.ability-icon img {
  width: 45px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
}
.plain-entity .entity-name {
  color: #79c0ff;
}

/* SUBGROUPS */
h4.subgroup {
  color: #79c0ff;
  font-size: 14px;
  font-weight: 700;
  margin: 16px 0 4px 14px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  border-bottom: 1px solid #21262d;
  padding-bottom: 4px;
}
h4.ability-title {
  color: #d2a8ff;
  font-size: 17px;
  font-weight: 600;
  margin: 16px 0 8px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
}
h4.ability-title .ability-icon-img {
  width: 56px;
  height: 56px;
  border-radius: 6px;
  flex-shrink: 0;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(210, 168, 255, 0.18), 0 2px 6px rgba(0, 0, 0, 0.4);
}

/* CHANGES LIST — grid layout: [tag] [text] [percentages] */
ul.changes {
  list-style: none;
  margin: 3px 0 3px 0;
}
ul.changes li {
  display: grid;
  grid-template-columns: 64px 1fr auto;
  column-gap: 12px;
  row-gap: 0;
  align-items: baseline;
  padding: 1px 0;
  line-height: 1.5;
  color: #c9d1d9;
}
/* Left column: text-tag goes here. Sizing inherits from .badge for visual consistency. */
ul.changes li > .badge:first-child,
ul.changes li > .row-tag-empty {
  grid-column: 1;
  align-self: start;
  margin-top: 2px;
}
ul.changes li > .row-tag-empty {
  visibility: hidden;
  /* match .badge dimensions so empty placeholder reserves same space */
  display: inline-block;
  padding: 3px 7px;
  font-size: 11px;
  line-height: 1;
  min-width: 56px;
  box-sizing: border-box;
  border: 1px solid transparent;
}
/* Middle column: description */
ul.changes li > .row-text {
  grid-column: 2;
}
/* Right column: numeric percentages */
ul.changes li > .badge-group {
  grid-column: 3;
  margin-left: 0;
}
/* extras (correction-note, formula-table, NOTE box) span all columns */
ul.changes li > .correction-note,
ul.changes li > .formula-table {
  grid-column: 1 / -1;
}
/* Raw <li> without .row-text wrapper (rare special-case manual rows) — block layout
   with auto-generated left tag from data-tag attribute via ::before. */
ul.changes li:not(:has(> .row-text)) {
  display: block;
  padding-left: 76px;
  position: relative;
  min-height: 22px;
}
ul.changes li:not(:has(> .row-text))::before {
  /* matches .badge dimensions exactly (same padding/line-height/font/min-width) */
  position: absolute;
  left: 0;
  top: 2px;
  display: inline-block;
  padding: 3px 7px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  line-height: 1;
  min-width: 56px;
  text-align: center;
  white-space: nowrap;
  box-sizing: border-box;
  font-variant-numeric: tabular-nums;
  /* default = nerf-text colors (same as .badge.nerf-text) */
  content: "";
  background: rgba(225, 90, 75, 0.10);
  color: #a86158;
  border: 1px solid rgba(225, 90, 75, 0.28);
}
/* Extras inside raw rows (formula-table, correction-note) — extend to left edge */
ul.changes li:not(:has(> .row-text)) > .formula-table,
ul.changes li:not(:has(> .row-text)) > .correction-note {
  margin-left: -76px;
  width: calc(100% + 76px);
}
/* Tag content (most-specific wins by source order; rework beats buff/nerf for hybrid rows) */
ul.changes li:not(:has(> .row-text))[data-tag*="buff"]::before  { content: "BUFF"; background: rgba(85,205,115,0.10); color: #6da375; border-color: rgba(85,205,115,0.28); }
ul.changes li:not(:has(> .row-text))[data-tag*="nerf"]::before  { content: "NERF"; }
ul.changes li:not(:has(> .row-text))[data-tag*="qol"]::before   { content: "QoL"; background: rgba(121,192,255,0.06); color: #87a3bf; border-color: rgba(121,192,255,0.20); }
ul.changes li:not(:has(> .row-text))[data-tag*="misc"]::before  { content: "MISC"; background: rgba(139,148,158,0.06); color: #6e7681; border-color: rgba(139,148,158,0.18); }
ul.changes li:not(:has(> .row-text))[data-tag*="new"]::before   { content: "NEW"; background: rgba(220,175,95,0.06); color: #9a7f4d; border-color: rgba(220,175,95,0.22); }
ul.changes li:not(:has(> .row-text))[data-tag*="del"]::before   { content: "DEL"; background: rgba(180,70,70,0.07); color: #a86060; border-color: rgba(180,70,70,0.25); }
ul.changes li:not(:has(> .row-text))[data-tag*="rework"]::before { content: "REWORK"; background: rgba(180,145,220,0.05); color: #7d6e93; border-color: rgba(180,145,220,0.15); }
/* Hide redundant inline tag spans (since ::before shows them) */
ul.changes li:not(:has(> .row-text)) > .badge.rework,
ul.changes li:not(:has(> .row-text)) > .badge.misc,
ul.changes li:not(:has(> .row-text)) > .badge.qol,
ul.changes li:not(:has(> .row-text)) > .badge.new,
ul.changes li:not(:has(> .row-text)) > .badge.del,
ul.changes li:not(:has(> .row-text)) > .badge.buff-text,
ul.changes li:not(:has(> .row-text)) > .badge.nerf-text {
  display: none;
}

ul.subnotes {
  list-style: none;
  margin: -2px 0 4px 76px;
}
ul.subnotes li {
  color: #8b949e;
  font-size: 13.5px;
  padding: 1px 0;
  line-height: 1.4;
}
ul.subnotes li::before { content: "↳ "; color: #6e7681; }

/* BADGES — flat rectangular tag boxes */
.badge {
  display: inline-block;
  padding: 3px 7px;
  border-radius: 2px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  line-height: 1;
  vertical-align: middle;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  min-width: 56px;
  text-align: center;
  box-sizing: border-box;
}
/* When inside .badge-group → strip the box, become plain colored text */
.badge-group {
  display: inline-flex;
  gap: 0;
  flex-wrap: wrap;
  vertical-align: middle;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 13px;
}
.badge-group .badge {
  background: none !important;
  border: none !important;
  padding: 0 !important;
  text-shadow: none !important;
  margin: 0;
  min-width: 0;
  text-transform: none;
  letter-spacing: 0;
  font-size: inherit;
}
/* Comma separator between multi-level badges */
.badge-group .badge:not(:last-child)::after {
  content: ", ";
  color: #6e7681;
  font-weight: 400;
}

/* NEUTRAL & TEXT TAGS */
.badge.neutral {
  background: rgba(139, 148, 158, 0.06);
  color: #6e7681;
  border: 1px solid rgba(139, 148, 158, 0.18);
}
.badge.rework {
  background: rgba(180, 145, 220, 0.05);
  color: #7d6e93;
  border: 1px solid rgba(180, 145, 220, 0.15);
}
.badge.misc {
  background: rgba(139, 148, 158, 0.06);
  color: #6e7681;
  border: 1px solid rgba(139, 148, 158, 0.18);
}
.badge.qol {
  background: rgba(121, 192, 255, 0.06);
  color: #87a3bf;
  border: 1px solid rgba(121, 192, 255, 0.20);
}
.badge.new {
  background: rgba(220, 175, 95, 0.06);
  color: #9a7f4d;
  border: 1px solid rgba(220, 175, 95, 0.22);
  font-weight: 700;
  letter-spacing: 0.5px;
}
.badge.del {
  background: rgba(180, 70, 70, 0.07);
  color: #a86060;
  border: 1px solid rgba(180, 70, 70, 0.25);
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* BUFF GRADIENT (10 tiers, soft-saturated greens) */
.badge.buff1  { background: rgba(120, 215, 145, 0.10); color: #b2d8b8; border: 1px solid rgba(120, 215, 145, 0.26); }
.badge.buff2  { background: rgba(115, 215, 140, 0.13); color: #b4dab6; border: 1px solid rgba(115, 215, 140, 0.32); }
.badge.buff3  { background: rgba(110, 215, 135, 0.17); color: #b2dab2; border: 1px solid rgba(110, 215, 135, 0.38); }
.badge.buff4  { background: rgba(105, 215, 130, 0.22); color: #aedaa8; border: 1px solid rgba(105, 215, 130, 0.44); }
.badge.buff5  { background: rgba(95, 210, 125, 0.27);  color: #a8d6a0; border: 1px solid rgba(95, 210, 125, 0.50); }
.badge.buff6  { background: rgba(85, 205, 115, 0.32);  color: #a4d496; border: 1px solid rgba(85, 205, 115, 0.55); }
.badge.buff7  { background: rgba(75, 200, 105, 0.36);  color: #9cd28a; border: 1px solid rgba(75, 200, 105, 0.60); }
.badge.buff8  { background: rgba(65, 195, 95, 0.40);   color: #94d07c; border: 1px solid rgba(65, 195, 95, 0.65); }
.badge.buff9  { background: rgba(55, 190, 85, 0.45);   color: #88cc6e; border: 1px solid rgba(55, 190, 85, 0.70); }
.badge.buff10 { background: rgba(50, 175, 80, 0.34);   color: #b8e2a4; border: 1px solid rgba(50, 175, 80, 0.55); }

/* NERF GRADIENT (10 tiers, soft-saturated reds) */
.badge.nerf1  { background: rgba(230, 130, 120, 0.10); color: #d8b0ac; border: 1px solid rgba(230, 130, 120, 0.24); }
.badge.nerf2  { background: rgba(228, 122, 110, 0.13); color: #dcaca8; border: 1px solid rgba(228, 122, 110, 0.30); }
.badge.nerf3  { background: rgba(225, 115, 100, 0.16); color: #dca8a0; border: 1px solid rgba(225, 115, 100, 0.36); }
.badge.nerf4  { background: rgba(225, 108, 92, 0.20);  color: #dca298; border: 1px solid rgba(225, 108, 92, 0.42); }
.badge.nerf5  { background: rgba(225, 100, 85, 0.25);  color: #de9c8e; border: 1px solid rgba(225, 100, 85, 0.50); }
.badge.nerf6  { background: rgba(225, 90, 75, 0.30);   color: #e09484; border: 1px solid rgba(225, 90, 75, 0.56); }
.badge.nerf7  { background: rgba(225, 80, 65, 0.34);   color: #e08c78; border: 1px solid rgba(225, 80, 65, 0.62); }
.badge.nerf8  { background: rgba(225, 70, 55, 0.38);   color: #e08470; border: 1px solid rgba(225, 70, 55, 0.68); }
.badge.nerf9  { background: rgba(225, 60, 45, 0.42);   color: #e07c66; border: 1px solid rgba(225, 60, 45, 0.74); }
.badge.nerf10 { background: rgba(220, 70, 55, 0.32);   color: #f1bcb0; border: 1px solid rgba(220, 70, 55, 0.55); }

/* Make digits readable on saturated backgrounds */
.badge.buff1, .badge.buff2, .badge.buff3, .badge.buff4, .badge.buff5,
.badge.buff6, .badge.buff7, .badge.buff8, .badge.buff9, .badge.buff10,
.badge.nerf1, .badge.nerf2, .badge.nerf3, .badge.nerf4, .badge.nerf5,
.badge.nerf6, .badge.nerf7, .badge.nerf8, .badge.nerf9, .badge.nerf10 {
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55);
}

/* Text-tag versions of BUFF/NERF (used by t() for non-numeric changes; pick mid tier) */
.badge.buff-text { background: rgba(85, 205, 115, 0.10); color: #6da375; border: 1px solid rgba(85, 205, 115, 0.28); }
.badge.nerf-text { background: rgba(225, 90, 75, 0.10);  color: #a86158; border: 1px solid rgba(225, 90, 75, 0.28); }

/* TYPO NOTE */
.typo-note {
  color: #f0c674;
  font-size: 11px;
  font-style: italic;
  margin-left: 6px;
}

/* WRONG-CHANGE LINE + CORRECTION NOTE — subtle gray */
.wrong-line {
  text-decoration: line-through;
  text-decoration-color: rgba(201, 209, 217, 0.5);
  text-decoration-thickness: 1px;
  opacity: 0.55;
}
.correction-note {
  display: block;
  margin: 6px 0 4px 0;
  padding: 6px 12px;
  background: rgba(139, 148, 158, 0.05);
  border-left: 2px solid rgba(139, 148, 158, 0.40);
  border-radius: 0 3px 3px 0;
  color: #7c8590;
  font-size: 12.5px;
  font-style: italic;
  line-height: 1.5;
}
.correction-note .badge {
  font-style: normal;
}
.correction-label {
  display: inline-block;
  font-style: normal;
  font-weight: 700;
  font-size: 10.5px;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: #8b949e;
  margin-right: 4px;
}

/* IMAGE FALLBACK STYLE */
.entity-icon img[alt]:not([src*="//"]) { background: #21262d; }
img { max-width: 100%; }

/* BACK TO TOP — fixed bottom-right */
.back-to-top {
  position: fixed;
  bottom: 22px;
  right: 22px;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(22, 27, 34, 0.92);
  border: 1px solid rgba(121, 192, 255, 0.45);
  color: #79c0ff;
  font-size: 20px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
  transition: all 0.18s ease;
  z-index: 100;
  font-family: inherit;
  padding: 0;
  padding-bottom: 3px;
}
.back-to-top:hover {
  background: rgba(121, 192, 255, 0.2);
  border-color: #79c0ff;
  transform: translateY(-2px);
}
.back-to-top.visible {
  display: flex;
}

/* WRONG-WORD HIGHLIGHT — subtle, neutral marker (no strikethrough) */
.wrong-word {
  background: rgba(139, 148, 158, 0.08);
  color: #8b949e;
  padding: 0 5px;
  border-radius: 3px;
}

/* FORMULA TRIGGER — same neutral, squared-off look as .wrong-word, clickable */
.formula-trigger {
  display: inline-block;
  padding: 0 5px;
  border-radius: 3px;
  background: rgba(139, 148, 158, 0.08);
  color: #8b949e;
  border: 1px solid rgba(139, 148, 158, 0.30);
  font-size: 13.5px;
  cursor: pointer;
  transition: all 0.14s;
  font-variant-numeric: tabular-nums;
  user-select: none;
}
.formula-trigger:hover {
  background: rgba(139, 148, 158, 0.16);
  border-color: rgba(139, 148, 158, 0.50);
  color: #c9d1d9;
}
.formula-trigger.active {
  background: rgba(139, 148, 158, 0.22);
  border-color: rgba(139, 148, 158, 0.60);
  color: #c9d1d9;
}
/* OLD FORMULA — just a subtle dotted underline so it stands out as "the old one" */
.formula-old {
  text-decoration: underline dotted rgba(139, 148, 158, 0.45);
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
}

/* FORMULA COMPARISON TABLE */
.formula-table {
  margin: 8px 0 6px;
  border-collapse: separate;
  border-spacing: 2px;
  font-size: 11px;
  width: 100%;
  table-layout: auto;
  font-variant-numeric: tabular-nums;
}
.formula-table[hidden] { display: none; }
.formula-table thead th {
  background: rgba(48, 54, 61, 0.55);
  color: #79c0ff;
  font-weight: 600;
  font-size: 10.5px;
  padding: 4px 0;
  text-align: center;
  border-radius: 3px;
}
.formula-table tbody th {
  width: 42px;
  text-align: left;
  padding: 4px 8px;
  background: rgba(48, 54, 61, 0.5);
  color: #c9d1d9;
  font-weight: 700;
  font-size: 10.5px;
  border-radius: 3px;
  letter-spacing: 0.3px;
}
.formula-table tbody td {
  padding: 4px 4px;
  text-align: center;
  background: rgba(48, 54, 61, 0.30);
  color: #c9d1d9;
  border-radius: 3px;
  font-size: 11px;
}
.formula-table tbody td .badge {
  margin-left: 0;
  padding: 0;
  font-size: 11px;
  border-radius: 0;
  background: none !important;
  border: none !important;
  text-shadow: none !important;
  display: inline;
  min-width: 0;
  text-transform: none;
  letter-spacing: 0;
}
.formula-table .row-label-old { color: #ff9a8c; }
.formula-table .row-label-new { color: #92c89e; }
/* Visual gap before L20 (after L1-15 sequential block) */
.formula-table .lvl-jump {
  border-left: 6px solid transparent;
  background-clip: padding-box !important;
}

/* FILTER BUTTONS in legend — make tags clickable */
.legend-tags .badge.filter-btn {
  cursor: pointer;
  user-select: none;
  font-family: inherit;
  font-size: 11px;
  padding: 2px 9px;
  transition: filter 0.12s, transform 0.12s;
}
.legend-tags .badge.filter-btn:hover {
  filter: brightness(1.18);
  transform: translateY(-1px);
}
.legend-tags .badge.filter-btn.active {
  outline: 2px solid currentColor;
  outline-offset: 2px;
  filter: brightness(1.35);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.4) inset;
}

/* ENTITY-BLOCK wrapper (used for filtering hide/show) */
.entity-block { margin-bottom: 6px; }

/* === FILTER MODE === */
body.filter-active h2.section { display: none; }
body.filter-active h4.subgroup { display: none; }
body.filter-active ul.subnotes { display: none; }
/* Hide filtered elements via .f-hide class set by JS */
.f-hide { display: none !important; }

/* MOBILE: stack legend label above strip so 10 segments fit */
@media (max-width: 540px) {
  .legend-strip {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
  }
  .legend-label {
    min-width: 0;
    font-size: 10px;
  }
  .gradient-strip { height: 12px; }
  .gradient-strip .seg { font-size: 8px; }
}

"""

# ---------- CONTENT ----------

H = []
def W(s): H.append(s)


# ============================================================
# MULTI-PATCH SUPPORT
# ============================================================

PATCHES = [
    {"version": "7.41c", "date": "06.05.2026", "filename": "patches/7.41c.html"},
    {"version": "7.41b", "date": "07.04.2026", "filename": "patches/7.41b.html"},
    {"version": "7.41a", "date": "28.03.2026", "filename": "patches/7.41a.html"},
    {"version": "7.41",  "date": "24.03.2026", "filename": "patches/7.41.html"},
    {"version": "7.08",  "date": "01.02.2018", "filename": "patches/7.08.html"},
]

# Includes patches without HTML (e.g. 7.41a) — used only for "days between" math.
# Major-patch dates from odota/dotaconstants. Sub-patches sourced from Liquipedia
# and Fandom. Append new entries here when patches release; sorted internally.
RELEASE_HISTORY = [
    # 7.41 cycle
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


def _render_top_nav(active="changelogs", current_version=None, date=None, patch_context=False):
    """Render the top nav. active in ('changelogs', 'calendar').
    patch_context=True when rendering inside a patch page (patches/ folder) —
    hrefs use ../ prefix for root files and plain filenames for sibling patches."""
    if patch_context:
        latest = PATCHES[0]['version'] + ".html" if PATCHES else "#"
        calendar_href = "../calendar.html"
    else:
        latest = PATCHES[0]['filename'] if PATCHES else "#"
        calendar_href = "calendar.html"
    cls_changelogs = "active" if active == "changelogs" else ""
    cls_calendar  = "active" if active == "calendar" else ""

    if current_version is not None and date is not None:
        age_line = _patch_age_line(current_version)
        age_html = f'<span class="patch-age">{age_line}</span>' if age_line else ''
        if active == "calendar":
            # Calendar already lets you pick patches — no dropdown needed.
            # Show only date+age, shifted to the right of where the dropdown would be.
            right_side = f'''
    <div class="nav-context nav-context-calendar">
      <div class="release-info">
        <span class="release-version">{current_version}</span>
        <span class="release-date">{date}</span>
        {age_html}
      </div>
    </div>'''
        else:
            options = _dropdown_options_html(current_version, patch_context=patch_context)
            right_side = f'''
    <div class="nav-context">
      <div class="release-info">
        <span class="release-date">{date}</span>
        {age_html}
      </div>
      <div class="version-dropdown">
        <button class="version" type="button" aria-haspopup="true" aria-expanded="false" aria-label="Select patch version">
          {current_version} <span class="version-chev">▾</span>
        </button>
        <div class="version-menu" role="menu">
          {options}
        </div>
      </div>
    </div>'''
    else:
        right_side = '<div class="nav-context"></div>'

    return f'''<nav class="top-nav">
  <div class="nav-inner">
    <div class="nav-tabs">
      <a class="nav-tab {cls_changelogs}" href="{latest}">Changelogs</a>
      <a class="nav-tab {cls_calendar}" href="{calendar_href}">Calendar</a>
    </div>{right_side}
  </div>
</nav>
'''


def write_head(version, date):
    """Render head + top nav (Changelogs+Calendar tabs + version) + container + toolbar."""
    nav = _render_top_nav(active="changelogs", current_version=version, date=date, patch_context=True)
    W(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Dota Patch Notes - {version}</title>
<link rel="stylesheet" href="../styles.css">
</head>
<body>

{nav}
<a class="nav-back-arrow" href="../calendar.html" aria-label="Back to calendar" title="Back to calendar">←</a>
<div class="container">

<div class="toolbar">
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
  <div class="search-box">
    <input type="text" id="entity-search" placeholder="Search heroes, items, abilities…" autocomplete="off" spellcheck="false">
    <div class="search-results" id="search-results"></div>
  </div>
</div>
''')


JS_TEXT = '''
(function() {
  // ---- BACK-FROM-CALENDAR ----
  const params = new URLSearchParams(window.location.search);
  const back = document.querySelector('.nav-back-arrow');
  if (params.get('from') === 'calendar' && back) {
    back.classList.add('visible');
  }
  // Vertically center the back-arrow on the toolbar
  function alignBackArrow() {
    if (!back) return;
    const tb = document.querySelector('.toolbar');
    if (!tb) return;
    const r = tb.getBoundingClientRect();
    const center = r.top + r.height / 2;
    const top = Math.round(center - back.offsetHeight / 2);
    back.style.top = top + 'px';
  }
  alignBackArrow();
  window.addEventListener('resize', alignBackArrow, { passive: true });

  // ---- BACK TO TOP visibility ----
  const btt = document.querySelector('.back-to-top');
  function updateBtt() {
    btt.classList.toggle('visible', window.scrollY > 400);
  }
  window.addEventListener('scroll', updateBtt, { passive: true });
  updateBtt();

  // ---- VERSION DROPDOWN toggle ----
  const dropdownBtn = document.querySelector('.version-dropdown .version');
  const dropdownMenu = document.querySelector('.version-dropdown .version-menu');
  if (dropdownBtn && dropdownMenu) {
    dropdownBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const open = dropdownMenu.classList.toggle('open');
      dropdownBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('click', (e) => {
      if (!dropdownMenu.contains(e.target) && !dropdownBtn.contains(e.target)) {
        dropdownMenu.classList.remove('open');
        dropdownBtn.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        dropdownMenu.classList.remove('open');
        dropdownBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ---- HIDE ABSENT TAGS from toolbar ----
  const presentTags = new Set();
  document.querySelectorAll('[data-tag]').forEach(el => {
    (el.dataset.tag || '').split(' ').filter(Boolean).forEach(t => presentTags.add(t));
  });
  document.querySelectorAll('.filter-btn').forEach(btn => {
    if (!presentTags.has(btn.dataset.filter)) {
      btn.style.display = 'none';
    }
  });

  // ---- BOLD NUMBERS AND VERSION IN PATCH-AGE ----
  const ageEl = document.querySelector('.patch-age');
  if (ageEl) {
    const text = ageEl.textContent;
    const html = text
      .replace(/\b(\d+\.\d+[a-z]?)\b/g, '<strong>$1</strong>')   // version like 7.41b
      .replace(/\b(\d+)\b(?=\s+days?)/g, '<strong>$1</strong>')   // numbers before "days"
      .replace(/·/g, '<span class="age-sep">·</span>');
    ageEl.innerHTML = html;
  }

  // ---- TAG FILTERING (multi-select, OR semantics) ----
  const buttons = document.querySelectorAll('.filter-btn');
  const activeFilters = new Set();
  function applyFilter() {
    const isActive = activeFilters.size > 0;
    document.body.classList.toggle('filter-active', isActive);
    document.querySelectorAll('.f-hide').forEach(el => el.classList.remove('f-hide'));
    if (!isActive) return;
    document.querySelectorAll('ul.changes > li').forEach(li => {
      const tags = (li.dataset.tag || '').split(' ').filter(Boolean);
      const matches = tags.some(t => activeFilters.has(t));
      if (!matches) li.classList.add('f-hide');
    });
    document.querySelectorAll('ul.changes').forEach(ul => {
      const hasVisible = Array.from(ul.children).some(c => !c.classList.contains('f-hide'));
      if (!hasVisible) ul.classList.add('f-hide');
    });
    document.querySelectorAll('h4.ability-title').forEach(h => {
      let nx = h.nextElementSibling;
      while (nx && nx.tagName !== 'UL') nx = nx.nextElementSibling;
      if (!nx || nx.classList.contains('f-hide')) h.classList.add('f-hide');
    });
    document.querySelectorAll('.entity-block').forEach(block => {
      const visible = block.querySelectorAll('ul.changes > li:not(.f-hide)').length;
      if (!visible) block.classList.add('f-hide');
    });
  }
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tag = btn.dataset.filter;
      if (activeFilters.has(tag)) {
        activeFilters.delete(tag);
        btn.classList.remove('active');
      } else {
        activeFilters.add(tag);
        btn.classList.add('active');
      }
      applyFilter();
    });
  });

  // ---- FORMULA TABLES (click pill to toggle table) ----
  document.querySelectorAll('.formula-trigger').forEach(trig => {
    trig.addEventListener('click', () => {
      const id = trig.dataset.formula;
      const table = document.getElementById(id);
      if (!table) return;
      const wasHidden = table.hasAttribute('hidden');
      if (wasHidden) {
        table.removeAttribute('hidden');
        trig.classList.add('active');
      } else {
        table.setAttribute('hidden', '');
        trig.classList.remove('active');
      }
    });
  });

  // ---- ENTITY SEARCH ----
  const searchInput = document.getElementById('entity-search');
  const resultsBox = document.getElementById('search-results');
  const entities = [];
  document.querySelectorAll('.entity').forEach(entity => {
    const nameEl = entity.querySelector('.entity-name');
    const imgEl = entity.querySelector('.entity-icon img');
    if (!nameEl) return;
    let kind = 'mechanic';
    if (entity.classList.contains('hero-entity')) kind = 'hero';
    else if (entity.classList.contains('item-entity')) kind = 'item';
    entities.push({
      name: nameEl.textContent.trim(),
      element: entity,
      icon: imgEl ? imgEl.src : null,
      kind: kind
    });
  });
  // Also index ability titles (h4.ability-title)
  document.querySelectorAll('h4.ability-title').forEach(h => {
    entities.push({
      name: h.textContent.trim(),
      element: h,
      icon: null,
      kind: 'ability'
    });
  });

  function escapeHtml(s) { return s.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
  function highlight(name, q) {
    const idx = name.toLowerCase().indexOf(q.toLowerCase());
    if (idx === -1) return escapeHtml(name);
    return escapeHtml(name.slice(0, idx)) +
           '<mark>' + escapeHtml(name.slice(idx, idx + q.length)) + '</mark>' +
           escapeHtml(name.slice(idx + q.length));
  }

  let activeIdx = -1;

  function render(query) {
    if (!query) {
      resultsBox.classList.remove('show');
      resultsBox.innerHTML = '';
      activeIdx = -1;
      return;
    }
    const q = query.toLowerCase();
    const matches = entities.filter(e => e.name.toLowerCase().includes(q)).slice(0, 12);
    if (matches.length === 0) {
      resultsBox.innerHTML = '<div class="empty">no matches</div>';
      resultsBox.classList.add('show');
      activeIdx = -1;
      return;
    }
    resultsBox.innerHTML = matches.map((m, i) =>
      `<div class="result-item" data-idx="${i}">${
        m.icon ? `<img src="${m.icon}" alt="">` : '<span style="width:32px;display:inline-block"></span>'
      }<span>${highlight(m.name, query)}</span><span class="kind">${m.kind}</span></div>`
    ).join('');
    resultsBox.classList.add('show');
    activeIdx = -1;

    resultsBox.querySelectorAll('.result-item').forEach((el, i) => {
      el.addEventListener('mouseenter', () => { setActive(i); });
      el.addEventListener('click', () => { jumpTo(matches[i]); });
    });
    window._currentMatches = matches;
  }

  function setActive(i) {
    activeIdx = i;
    resultsBox.querySelectorAll('.result-item').forEach((el, idx) => {
      el.classList.toggle('active', idx === i);
    });
  }

  function jumpTo(target) {
    if (!target) return;
    target.element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    target.element.style.transition = 'box-shadow 0.4s';
    target.element.style.boxShadow = '0 0 0 2px #58a6ff';
    setTimeout(() => target.element.style.boxShadow = '', 1400);
    searchInput.value = '';
    resultsBox.classList.remove('show');
    resultsBox.innerHTML = '';
  }

  searchInput.addEventListener('input', () => render(searchInput.value));
  searchInput.addEventListener('keydown', (e) => {
    const items = resultsBox.querySelectorAll('.result-item');
    if (!items.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((activeIdx + 1) % items.length); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((activeIdx - 1 + items.length) % items.length); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      const idx = activeIdx >= 0 ? activeIdx : 0;
      if (window._currentMatches && window._currentMatches[idx]) jumpTo(window._currentMatches[idx]);
    }
    else if (e.key === 'Escape') {
      searchInput.value = '';
      render('');
    }
  });
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
      resultsBox.classList.remove('show');
    }
  });
})();

'''

def write_footer():
    """Render close-block + back-to-top button + script tag + closing tags."""
    W(_close_block())
    W('<button class="back-to-top" aria-label="Back to top" onclick="window.scrollTo({top:0, behavior:\'smooth\'})">↑</button>')
    W('<script src="../scripts.js"></script>')
    W('</div></body></html>')


def save_assets():
    """Write styles.css and scripts.js once. Called before any save_html()."""
    with open('styles.css', 'w', encoding='utf-8') as f:
        f.write(CSS)
    with open('scripts.js', 'w', encoding='utf-8') as f:
        f.write(JS_TEXT)
    print(f"  → styles.css: {len(CSS):,} bytes")
    print(f"  → scripts.js: {len(JS_TEXT):,} bytes")


def save_html(filename):
    """Write current accumulator to ./{filename} and reset state."""
    out = "\n".join(H)
    path = filename
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  → {filename}: {len(out):,} bytes")
    H.clear()
    _State.block_open = False


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
    "7.40c":  152, "7.41":  1795, "7.41a":   60, "7.41b":  191, "7.41c":  204,
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
    body.append('<div class="cal-toggle-bar">')
    body.append('<strong>View:</strong>')
    body.append('<select class="cal-mode-select">')
    body.append('<option value="full" selected>Expanded</option>')
    body.append('<option value="compact">Compact</option>')
    body.append('</select>')
    body.append('</div>')

    body.append('<div class="calendar mode-full">')

    for year in years:
        collapsed = "false" if year in expanded_years else "true"
        body.append(f'<div class="cal-year-block" data-collapsed="{collapsed}">')
        body.append(f'<h2 class="cal-year-label">{year}</h2>')

        # ---- MODE FULL ----
        body.append('<div class="cal-mode-full">')
        body.append('<div class="cal-full-grid">')
        for month in range(1, 13):
            body.append(f'<div class="cal-full-month-name">{months[month-1]}</div>')
            days_in_m = monthrange(year, month)[1]
            for d in range(1, 32):
                if d > days_in_m:
                    body.append('<div class="cal-full-day no-day"></div>')
                    continue
                p = by_day.get((year, month, d))
                if p:
                    cls = patch_class(p['version'])
                    tag, href = chip_tag(p['version'])
                    cur = " current" if p['version'] == current_v else ""
                    body.append(f'<{tag} class="cal-full-day has-patch {cls}{cur}"{href}>{p["version"]}</{tag}>')
                else:
                    body.append(f'<div class="cal-full-day">{d}</div>')
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

        body.append('</div>')

    body.append('</div>')

    toggle_script = '''<script>
(function() {
  const cal = document.querySelector('.calendar');
  const select = document.querySelector('.cal-mode-select');
  if (select) {
    select.addEventListener('change', () => {
      cal.classList.remove('mode-full', 'mode-compact');
      cal.classList.add('mode-' + select.value);
    });
  }
  document.querySelectorAll('.cal-year-label').forEach(label => {
    label.addEventListener('click', () => {
      const block = label.parentElement;
      const c = block.dataset.collapsed === 'true';
      block.dataset.collapsed = c ? 'false' : 'true';
    });
  });
})();
</script>'''

    cur_v = _current_version()
    cur_date = next((r["date"] for r in RELEASE_HISTORY if r["version"] == cur_v), None)
    nav = _render_top_nav(active="calendar", current_version=cur_v, date=cur_date)
    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<title>Dota Patch Calendar</title>\n'
        '<link rel="stylesheet" href="styles.css">\n'
        '</head>\n<body>\n\n'
        + nav
        + '\n<div class="container">\n'
        + '\n'.join(body)
        + '\n</div>\n\n'
        + '<script src="scripts.js"></script>\n'
        + toggle_script + '\n'
        + '</body>\n</html>\n'
    )
    with open('calendar.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → calendar.html: {len(html):,} bytes")


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
W(plain_header("Tormentor"))
W(ul_open())
W(li("Alleviation: Max health regen increased from 2% to 2.25%", b(2, 2.25)))
W(li("Alleviation: Duration increased from 10s to 15s", b(10, 15)))
W(ul_close())
W(section("Item Updates"))
W(item_header("Bloodstone"))
W(ul_open())
W('''<li data-tag="nerf"><span class="wrong-line">Health bonus increased from +600 to +625 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span></span> <div class="correction-note"><span class="correction-label">Note</span>— This change is wrongly stated. The real change is 650 → 625 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span></span></div></li>''')
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
W(li("Base Intelligence increased by 1", bstat_h("Abaddon", "AttributeBaseIntelligence", "7.41b", 1), extra=note_box("From 18 to 19")))
W(ul_close())
W(subnote("Damage at level 1 unchanged at 49-59"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Curse of Avernus DPS increased from +25 to +30", b(25, 30)))
W(ul_close())
W(hero_header("Alchemist"))
W(subgroup("Abilities"))
W(ability("Greevil's Greed"))
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
W(ability("Persecutor"))
W(ul_open())
W(li("Minimum mana threshold for slow improved from 50% to 60%", b(50, 60)))
W(ul_close())
W(hero_header("Arc Warden"))
W(ul_open())
W(li("Base Agility increased from 20 to 22", b(20, 22)))
W(li("Damage at level 1 increased from 51-57 to 52-58", '<span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span>'))
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
W(li("Damage at level 1 decreased from 50-54 to 49-53", '<span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span>'))
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
W(ability("Shadow Walk"))
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
W(ability("Spinner's Snare"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 70", b(100, 70, l=True)))
W(ul_close())
W(hero_header("Centaur Warrunner"))
W(ul_open())
W(li("Base Strength increased from 27 to 28", b(27, 28)))
W(li("Damage at level 1 increased from 63-65 to 64-66", '<span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span>'))
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
W(li("Damage at level 1 increased from 53-59 to 54-60", '<span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span>'))
W(ul_close())
W(hero_header("Dark Willow"))
W(subgroup("Abilities"))
W(ability("Terrorize"))
W(ul_open())
W(li("Radius increased from 400/450/500 to 450/500/550", b([400, 450, 500], [450, 500, 550])))
W(ul_close())
W(hero_header("Dawnbreaker"))
W(ul_open())
W(li("Base Damage decreased by 1", bstat_h("Dawnbreaker", "AttackDamageMin", "7.41b", -1), extra=note_box("From 33 to 32")))
W(li("Damage at level 1 decreased from 56-60 to 55-59", '<span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span>'))
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
W(ability("Gust"))
W(ul_open())
W(li("Mana Cost decreased from 70 to 55", b(70, 55, l=True)))
W(ul_close())
W(hero_header("Earth Spirit"))
W(ul_open())
W(li("Base Strength increased from 22 to 23", b(22, 23)))
W(li("Damage at level 1 increased from 47-51 to 48-52", '<span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span>'))
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
W(li("Base Damage increased by 3", bstat_h("Hoodwink", "AttackDamageMin", "7.41b", 3), extra=note_box("From 25.5 to 28.5")))
W(li("Base Agility decreased from 25 to 22", b(25, 22)))
W(ul_close())
W(subnote("Damage at level 1 unchanged at 47-54"))
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
W(li("Cooldown decreased from 60.5s − 0.5s per level to 50.5s − 0.5s per level", '<span class="badge-group" data-overall="buff"><span class="badge buff4">+17%</span></span>'))
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
W(ability("Summon Spirit Bear"))
W(ul_open())
W(li("Mana Cost increased from 75 to 100", b(75, 100, l=True)))
W(ul_close())
W(ability("Spirit Link"))
W(ul_open())
W(li("Shared Lifesteal now follows general lifesteal rules and has a creep penalty of 40%", t("NERF")))
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
W(unit_header("Spirit Bear", "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/lone_druid_spirit_bear.png"))
W(ul_open())
W('''<li data-tag="buff rework">Gold/Experience Bounty changed from <span class="formula-old">175 + 8 per Spirit Bear level</span> up to <span class="formula-trigger" data-formula="fsb">165 + 10 per Spirit Bear level</span> <span class="badge rework" data-tag="rework">REWORK</span><span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span><table class="formula-table" id="fsb" hidden><thead><tr><th></th><th>L1</th><th>L2</th><th>L3</th><th>L4</th><th>L5</th><th>L6</th><th>L7</th><th>L8</th><th>L9</th><th>L10</th><th>L11</th><th>L12</th><th>L13</th><th>L14</th><th>L15</th><th class="lvl-jump">L20</th><th>L25</th><th>L30</th></tr></thead><tbody><tr><th class="row-label-old">old</th><td>183</td><td>191</td><td>199</td><td>207</td><td>215</td><td>223</td><td>231</td><td>239</td><td>247</td><td>255</td><td>263</td><td>271</td><td>279</td><td>287</td><td>295</td><td class="lvl-jump">335</td><td>375</td><td>415</td></tr><tr><th class="row-label-new">new</th><td>175</td><td>185</td><td>195</td><td>205</td><td>215</td><td>225</td><td>235</td><td>245</td><td>255</td><td>265</td><td>275</td><td>285</td><td>295</td><td>305</td><td>315</td><td class="lvl-jump">365</td><td>415</td><td>465</td></tr><tr><th>Δ %</th><td><span class="badge buff1">+4%</span></td><td><span class="badge buff1">+3%</span></td><td><span class="badge buff1">+2%</span></td><td><span class="badge buff1">+1%</span></td><td><span class="badge neutral">0%</span></td><td><span class="badge nerf1">-1%</span></td><td><span class="badge nerf1">-2%</span></td><td><span class="badge nerf1">-3%</span></td><td><span class="badge nerf1">-3%</span></td><td><span class="badge nerf1">-4%</span></td><td><span class="badge nerf1">-5%</span></td><td><span class="badge nerf1">-5%</span></td><td><span class="badge nerf2">-6%</span></td><td><span class="badge nerf2">-6%</span></td><td><span class="badge nerf2">-7%</span></td><td class="lvl-jump"><span class="badge nerf2">-9%</span></td><td><span class="badge nerf3">-11%</span></td><td><span class="badge nerf3">-12%</span></td></tr></tbody></table></li>''')
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
W(ability("Spear of Mars"))
W(ul_open())
W(li("Mana Cost decreased from 100/110/120/130 to 90/100/110/120", b([100, 110, 120, 130], [90, 100, 110, 120], l=True)))
W(ul_close())
W(hero_header("Mirana"))
W(subgroup("Abilities"))
W(ability("Sacred Arrow"))
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
W(li("Damage at level 1 decreased from 53-57 to 52-56", '<span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span>'))
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
W(ability("Nature's Call"))
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
W(ability("Repel"))
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
W(ability("Sanity's Eclipse"))
W(ul_open())
W(li("Radius increased from 450/500/550 to 500/525/550", b([450, 500, 550], [500, 525, 550])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20: Astral Imprisonment Mana Capacity Steal increased from 10% to 12%", b(10, 12)))
W(ul_close())
W(hero_header("Pangolier"))
W(ul_open())
W(li("Base Health Regen decreased by 1.0", bstat_h("Pangolier", "StatusHealthRegen", "7.41b", -1), extra=note_box("From 1.25 to 0.25")))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Swashbuckle"))
W(ul_open())
W(li("Mana Cost increased from 75/80/85/90 to 85/90/95/100", b([75, 80, 85, 90], [85, 90, 95, 100], l=True)))
W(ul_close())
W(ability("Roll Up"))
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
W(li("Damage at level 1 increased from 56-58 to 57-59", '<span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span>'))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Phantom Strike Duration increased from +0.6 to +0.8s", b(0.6, 0.8)))
W(ul_close())
W(hero_header("Phantom Lancer"))
W(subgroup("Abilities"))
W(ability("Phantom Rush"))
W(ul_open())
W(li("Aghanim's Scepter bonus max rush distance decreased from +625 to +575", b(625, 575)))
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
W(li("Level 25: Curiosity Bonuses decreased from 2× to 1.5×", '<span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span></span>'))
W(ul_close())
W(hero_header("Sand King"))
W(ul_open())
W(li("Base Attack Speed decreased from 110 to 100", b(110, 100)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("Stinger"))
W(ul_open())
W(li("Slow Duration rescaled from 4/5/6/7s to 5s", b([4, 5, 6, 7], 5)))
W(ul_close())
W(ability("Epicenter"))
W(ul_open())
W(li("Base Radius decreased from 500 to 450", b(500, 450)))
W(ul_close())
W(hero_header("Shadow Fiend"))
W(subgroup("Abilities"))
W(ability("Shadowraze"))
W(ul_open())
W(li("Mana Cost decreased from 80 to 75", b(80, 75, l=True)))
W(ul_close())
W(ability("Presence of the Dark Lord"))
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
W(li("Base Damage increased by 2", bstat_h("Snapfire", "AttackDamageMin", "7.41b", 2), extra=note_box("From 28 to 30")))
W(li("Damage at level 1 increased from 51-57 to 53-59", '<span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span>'))
W(ul_close())
W(hero_header("Spectre"))
W(ul_open())
W(li("Base Agility increased from 26 to 29", b(26, 29)))
W(li("Damage at level 1 increased from 49-53 to 52-56", '<span class="badge-group" data-overall="buff"><span class="badge buff2">+6%</span></span>'))
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
W('''<li data-tag="buff new">Now gains a charge every 3 levels <span class="badge new" data-tag="new" data-overall="buff">NEW</span></li>''')
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Overload Attack/Movement Speed Slow increased from +20/20% to +25/25%", b([20, 20], [25, 25])))
W(ul_close())
W(hero_header("Sven"))
W(subgroup("Abilities"))
W(ability("Storm Hammer"))
W(ul_open())
W(li("Mana Cost decreased from 110/115/120/125 to 110", b([110, 115, 120, 125], 110, l=True)))
W(ul_close())
W(hero_header("Techies"))
W(ul_open())
W(li("Base Mana Regen decreased by 0.5", bstat_h("Techies", "StatusManaRegen", "7.41b", -0.5), extra=note_box("From 1.0 to 0.5")))
W(li("Intelligence gain decreased from 3.0 to 2.7", b(3, 2.7)))
W(li("Damage gain per level decreased from 3.3 to 3.2", b(3.3, 3.2)))
W(ul_close())
W(subgroup("Abilities"))
W(ability("M.A.D."))
W(ul_open())
W('''<li data-tag="buff rework">Mana Pool as Regen rescaled from <span class="formula-old">0.08% + 0.02% per level</span> to <span class="formula-trigger" data-formula="fld">0.1% + 0.01% per level</span> <span class="badge rework" data-tag="rework">REWORK</span><span class="badge-group" data-overall="buff"><span class="badge buff2">+10%</span></span><table class="formula-table" id="fld" hidden><thead><tr><th></th><th>L1</th><th>L2</th><th>L3</th><th>L4</th><th>L5</th><th>L6</th><th>L7</th><th>L8</th><th>L9</th><th>L10</th><th>L11</th><th>L12</th><th>L13</th><th>L14</th><th>L15</th><th class="lvl-jump">L20</th><th>L25</th><th>L30</th></tr></thead><tbody><tr><th class="row-label-old">old</th><td>0.10%</td><td>0.12%</td><td>0.14%</td><td>0.16%</td><td>0.18%</td><td>0.20%</td><td>0.22%</td><td>0.24%</td><td>0.26%</td><td>0.28%</td><td>0.30%</td><td>0.32%</td><td>0.34%</td><td>0.36%</td><td>0.38%</td><td class="lvl-jump">0.48%</td><td>0.58%</td><td>0.68%</td></tr><tr><th class="row-label-new">new</th><td>0.11%</td><td>0.12%</td><td>0.13%</td><td>0.14%</td><td>0.15%</td><td>0.16%</td><td>0.17%</td><td>0.18%</td><td>0.19%</td><td>0.20%</td><td>0.21%</td><td>0.22%</td><td>0.23%</td><td>0.24%</td><td>0.25%</td><td class="lvl-jump">0.30%</td><td>0.35%</td><td>0.40%</td></tr><tr><th>Δ %</th><td><span class="badge buff2">+10%</span></td><td><span class="badge neutral">0%</span></td><td><span class="badge nerf2">-7%</span></td><td><span class="badge nerf3">-12%</span></td><td><span class="badge nerf4">-17%</span></td><td><span class="badge nerf4">-20%</span></td><td><span class="badge nerf5">-23%</span></td><td><span class="badge nerf5">-25%</span></td><td><span class="badge nerf6">-27%</span></td><td><span class="badge nerf6">-29%</span></td><td><span class="badge nerf6">-30%</span></td><td><span class="badge nerf6">-31%</span></td><td><span class="badge nerf6">-32%</span></td><td><span class="badge nerf6">-33%</span></td><td><span class="badge nerf7">-34%</span></td><td class="lvl-jump"><span class="badge nerf7">-37%</span></td><td><span class="badge nerf7">-40%</span></td><td><span class="badge nerf7">-41%</span></td></tr></tbody></table></li>''')
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
W(li("Base Mana Regen decreased by 0.5", bstat_h("Tidehunter", "StatusManaRegen", "7.41b", -0.5), extra=note_box("From 0.5 to 0")))
W(ul_close())
W(hero_header("Timbersaw"))
W(ul_open())
W(li("Base Damage increased by 2", bstat_h("Timbersaw", "AttackDamageMin", "7.41b", 2), extra=note_box("From 25 to 27")))
W('''<li data-tag="buff">Damage at level 1 <span class="wrong-word">decreased</span> from 46-50 to 48-52 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span><div class="correction-note"><span class="correction-label">Note</span>— The patch text says "decreased", but the values actually went up.</div></li>''')
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
W(li("No longer castable while rooted", t("NERF")))
W(ul_close())
W(hero_header("Vengeful Spirit"))
W(subgroup("Abilities"))
W(ability("Vengeance Aura"))
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
W(ability("Nosedive"))
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

W(plain_header("Tormentor"))
W(ul_open())
W(li("Reflect Damage reflection per minute decreased from 2% to 1.5%", b(2, 1.5)))
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
W(item_header("Gungir"))
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
W(subgroup("Artifact changes"))
W(item_header("Jidi Pollen Bag"))
W(ul_open())
W(li("Pollinate radius increased from 700 to 900", b(700, 900)))
W(ul_close())
W(item_header("Conjurer's Catalyst"))
W(ul_open())
W(li("Spellover now has a 0.1s internal cooldown ", t("REWORK")))
W(ul_close())
W(subnote("Still can proc multiple times from a single instance of high damage"))
W(ul_open())
W(li("Spellover damage threshold increased from 100 to 200", b(100, 200)))
W(li("Spellover damage from hero targets increased from 40 to 80 ", b(40, 80)))
W(ul_close())
W(subnote("From 52 to 104 with Dormant Curio"))
W(ul_open())
W(li("Spellover damage from creep targets increased from 15 to 30 ", b(15, 30)))
W(ul_close())
W(subnote("From 19.5 to 39 with Dormant Curio"))
W(item_header("Enchanter's Bauble"))
W(ul_open())
W(li("Enchant base Neutral Enchantment bonus decreased from 15% to 10%", b(15, 10)))
W(ul_close())
W(item_header("Idol of Screeauk"))
W(ul_open())
W(li("False Flight duration increased from 5s to 6.5s ", b(5, 6.5)))
W(ul_close())
W(subnote("From 6.5s to 8.45s with Dormant Curio"))
W(item_header("Metamorphic Mandible"))
W(ul_open())
W(li("Pupate movement speed bonus increased from 15% to 20%", b(15, 20)))
W(ul_close())
W(item_header("Rattlecage"))
W(ul_open())
W(li("Reverberate projectile physical damage decreased from 110 to 90 ", b(110, 90)))
W(ul_close())
W(subnote("From 143 to 117 with Dormant Curio"))
W(item_header("Demonicon"))
W(ul_open())
W(li("Demonic Warrior no longer has True Sight ability", t("NERF")))
W(ul_close())
W(item_header("Minotaur Horn"))
W(ul_open())
W(li("Lesser Avatar bonus magic resistance increased from 50% to 60%", b(50, 60)))
W(ul_close())
W(item_header("Riftshadow Prism"))
W(ul_open())
W(li("Refract cooldown decreased from 30s to 27s", b(30, 27, l=True)))
W(ul_close())
W(subgroup("Enchantment changes"))
W(enchant_header("Crude", "crude"))
W(ul_open())
W(li("Health Restoration bonus decreased from +10/15/20% to +9/12/15%", b([10, 15, 20], [9, 12, 15])))
W(ul_close())
W(plain_header("Frostbitten Golem"))
W(ul_open())
W(li("Time Warp Aura: Cooldown Reduction decreased from 10/11/12/14% to 8/9/10/11%", b([10, 11, 12, 14], [8, 9, 10, 11], l=True)))
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
W(li("Base Armor decreased by 1", bstat_h("Batrider", "ArmorPhysical", "7.41a", -1), extra=note_box("From 2 to 1")))
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
W(li("Damage at level 1 increased from 45-51 to 47-53", b(48, 50)))
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
W(li("Spirit Damage increased from 64 to 65/68/71 ", b(64, [65, 68, 71])))
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
W(li("Damage at level 1 increased from 49-56 to 51-58", b(52.5, 54.5)))
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
W(li("Base Damage decreased by 3", bstat_h("Ember Spirit", "AttackDamageMin", "7.41a", -3), extra=note_box("From 35 to 32")))
W(li("Damage at level 1 decreased from 55-59 to 52-56", b(57, 54)))
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
W(ability("Demonic Conversion"))
W(ul_open())
W(li("Fixed Eidolons not having an 8 attack damage spread", t("MISC")))
W(li("Eidolon Damage increased from 16/27/38/49 to 16/28/40/52", b([16, 27, 38, 49], [16, 28, 40, 52])))
W(li("As a result, damage changed from 16/27/38/49 to 12-20/24-32/36-44/48-56", b([16, 27, 38, 49], 12)))
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
W(ability("Fight Song"))
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
W(li("Damage gain per level increased from 3.2 to 3.3", b(3.2, 3.3)))
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
W(ability("Transfiguration"))
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
W(li("Base Health Regen decreased by 1.25", bstat_h("Night Stalker", "StatusHealthRegen", "7.41a", -1.25), extra=note_box("From 1.5 to 0.25")))
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
W(ability("Gyroshell"))
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
W(ability("Graft Flesh"))
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
W(ability("Epicenter"))
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
W(li("Base Mana Regen increased by 0.25", bstat_h("Skywrath Mage", "StatusManaRegen", "7.41a", 0.25), extra=note_box("From 0.25 to 0.5")))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ability("Sprint"))
W(ul_open())
W(li("Cooldown increased from 29/25/21/17s to 33/28/23/18s", b([29, 25, 21, 17], [33, 28, 23, 18], l=True)))
W(ul_close())

# Slark
W(hero_header("Slark"))
W(ability("Essence Shift"))
W(ul_open())
W(li("Duration decreased from 12.5s + 2.5s per level to 10s + 2.5s per level", t("NERF")))
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
W(li("Damage at level 1 decreased from 51-57 to 50-56", b(54, 53)))
W(ul_close())
W(ability("Leviathan's Catch"))
W(ul_open())
W(li("Now gains fish on every even level instead of every level", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Gush Damage decreased from +100 to +90", b(100, 90)))
W(li("Level 25 Talent Anchor Smash affects buildings now deals 50% damage to buildings", t("NERF")))
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
W(ability("Tree Channel"))
W(ul_open())
W(li("No longer applies cleave", t("NERF")))
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
W(li("Base Health Regen increased by 0.5", t("BUFF")))
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
W(subgroup("Enchantment changes"))
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
W(ability("Greevil's Greed"))
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
W(li("Base Health Regen increased by 0.5", bstat_h("Anti-Mage", "StatusHealthRegen", "7.41", 0.5), extra=note_box("From 1.0 to 1.5")))
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
W(li("Base Damage increased by 3", bstat_h("Chaos Knight", "AttackDamageMin", "7.41", 3), extra=note_box("From 39 to 42")))
W(li("Damage on level 1 increased from 53–73 to 56–76", t("BUFF")))
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
W(li("Base Armor decreased by 1", bstat_h("Doom", "ArmorPhysical", "7.41", -1), extra=note_box("From 2 to 1")))
W(ul_close())
W(ability("Lvl Pain"))
W(ul_open())
W(li("Curse Damage decreased from 15% to 10%", b(15, 10)))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(ul_open())
W(li("Base Intelligence increased from 20 to 22", b(20, 22)))
W(li("Damage on level 1 increased from 39–45 to 41–47", t("BUFF")))
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
W(ability("Ravens Veil"))
W(ul_open())
W(li("Buff Duration increased from 7/8/9s to 8/10/12s", b([7, 8, 9], [8, 10, 12])))
W(ul_close())

# Legion Commander
W(hero_header("Legion Commander"))
W(ability("Outfight Them"))
W(ul_open())
W(li("No longer grants a passive armor bonus before casting abilities", t("NERF")))
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
W(li("Base Damage decreased by 3", bstat_h("Lifestealer", "AttackDamageMin", "7.41", -3), extra=note_box("From 19 to 16")))
W(li("Damage on level 1 decreased from 49–55 to 46–52", t("NERF")))
W(ul_close())
W(ability("Ghoul Frenzy"))
W(ul_open())
W(li("Bonus Attack Speed decreased from 5 per level to 4 per level", t("NERF")))
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
W(li("Evasion no longer diminishes when shared between Meepos and has full strength on each", t("NERF")))
W(li("Clones can no longer copy Bottle", t("NERF")))
W(ul_close())

# Mirana
W(hero_header("Mirana"))
W(ability("Celestial Quiver"))
W(ul_open())
W(li("Bonus Damage changed from 3 per level to 5 + 3 per level", t("MISC")))
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
W(ability("Pierce The Veil"))
W(ul_open())
W(li("Base Damage Bonus rescaled from 75% to 70/85/100%", b(75, [70, 85, 100])))
W(ul_close())

# Oracle
W(hero_header("Oracle"))
W(ability("Fortunes End"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 80", b(100, 80, l=True)))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ability("Gyroshell"))
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
W(li("Now slightly grows in size when crossing an HP threshold", t("REWORK")))
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
W(ability("Land Mines"))
W(ul_open())
W(li("Damage decreased from 450/575/750 to 400/550/700", b([450, 575, 750], [400, 550, 700])))
W(li("Portion of damage dealt on the edge of AoE decreased from 60% to 50%", b(60, 50)))
W(li("Minimum Damage decreased from 240/345/450 to 200/225/350", b([240, 345, 450], [200, 225, 350], l=True)))
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
W(li("Base Mana Regen decreased by 0.6", bstat_h("Void Spirit", "StatusManaRegen", "7.41", -0.6), extra=note_box("From 0.6 to 0")))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ul_open())
W(li("Base Agility increased from 17 to 20", b(17, 20)))
W(li("Damage on level 1 increased from 47–59 to 49–61", t("BUFF")))
W(ul_close())
W(ability("Tailwind"))
W(ul_open())
W(li("Duration increased from 2s to 2.5s", b(2, 2.5)))
W(li("Aghanim's Scepter bonus is still +1s, so it's increased to 3.5s", t("BUFF")))
W(ul_close())
W(ability("Focusfire"))
W(ul_open())
W(li("Cooldown decreased from 70/50/30s to 50/40/30s", b([70, 50, 30], [50, 40, 30], l=True)))
W(ul_close())

# Wraith King
W(hero_header("Wraith King"))
W(ul_open())
W(li("Base Attack Time worsened from 1.7s to 1.8s", b(1.7, 1.8)))
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
W(li("Innate abilities no longer scale with other abilities' level", t("NERF")))
W(li("All innate abilities that used to scale with other abilities now either provide unchangeable bonuses or improve on 'per level' basis. Abilities that improve with hero level have base value and increment value. Some also have amount of levels required for increment", t("REWORK")))
W(ul_close())
W(subnote("Abilities that improve each level provide their increment value at level 1"))
W(ul_open())
W(li("Added UI icon that shows you which parameters increase with hero level and what is the current value. Some non-innate ability might have this per level UI as well", t("MISC")))
W(ul_close())
W(subnote("Pressing ALT key will show base value and increment of the ability"))
W(ul_open())
W(li("Abilities that had 'per level up' scaling changed to be 'per level'", t("REWORK")))
W(ul_close())
W(subnote("This mostly affects heroes reworked in update 7.40 and Largo"))
W(ul_open())
W(li("Flagbearer Creep Experience Bounty increased from 57 to 60", b(57, 60)))
W(li("First +1 siege creep timing decreased from 35:00 to 30:00", b(35, 30, l=True)))
W(li("Second +1 siege creep timing now occurs at 60:00", t("NEW")))
W(li("Adjusted the meeting point of the lane creeps toward the offlane", t("MISC")))
W(ul_close())
W(subnote("Now offlane creeps are slightly slowed upon leaving the base for a couple of seconds. Safe lane creeps are slightly accelerated upon leaving the base for a couple of seconds. Both of these changes are effective until the 7:30 mark."))
W(ul_open())
W(li("All sections of currents now give a max movement speed bonus of 150 ", t("REWORK")))
W(ul_close())
W(subnote("Previously was only provided by sections on the base and near it, while other sections provided max bonus of 100"))
W(plain_header("Map Objectives"))

W(subgroup("Tormentor"))
W(ul_open())
W(li("Tormentor's spawn preference has switched", t("MISC")))
W(ul_close())
W(subnote("Now begins in the Bottom Chasm"))
W(ul_open())
W(li("Unyielding Shield Base barrier increased from 2000 to 3000", b(2000, 3000)))
W(li("Unyielding Shield Barrier upgrade per minute increased from 20 to 50", b(20, 50)))
W(li("Unyielding Shield Base barrier regen decreased from 40 to 20", b(40, 20)))
W(li("Unyielding Shield Barrier regen upgrade per minute increased from 3.5 to 5", b(3.5, 5)))
W(li("Reflect Base damage reflection percentage decreased from 50% to 30%", b(50, 30)))
W(li("Reflect radius can now be seen by holding ALT key", t("MISC")))
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
W(li("No longer deals damage to neutral units", t("NERF")))
W(li("Player that got Aghanim's Shard will no longer receive 175 gold", t("NERF")))
W(ul_close())
W(subnote(f'Total team gold reward decreased from 875 to 700 {b(875, 700)} (total networth change decreased from 2275 to 2100 {b(2275, 2100)})'))
W(ul_open())
W(li("Reward if all players have Aghanim's Shard decreased from 455 gold to 415 gold", b(455, 415)))
W(ul_close())

W(subgroup("Roshan"))
W(ul_open())
W(li("Roshan's pit preference has switched", t("MISC")))
W(ul_close())
W(subnote("Now begins in the Top Pit"))

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
W(plain_header("Terrain Changes"))
W(ul_open())
W(li("Tormentor spawns have been positioned closer towards Lotus Pools", t("MISC")))
W(li("Tormentor spawn areas have been reduced to low ground relative to the lane's level", t("MISC")))
W(li("Lotus Pools have been moved slightly closer to their respective offlane tower", t("MISC")))
W(li("Twin Gates slightly moved away from the stairs towards the map border", t("MISC")))
W(li("The watcher between the safe lane tier 1 tower and the tormentor has been repositioned. Result:", t("MISC")))
W(ul_close())
W(subnote("Tormentor is on the low ground which has three stairs: one leading to the Lotus Pool, one leading to the lane, and one leading to even higher ground area with the Twin Gate"))
W(subnote("Twin Gate highground area is now smaller and has three stairs: one that leads to new Tormentor area, one that leads back to the lane, and one that goes two levels down straight to the end of the stream"))
W(subnote("Watcher is now between two stairs: one that goes down to the Tormentor and one that goes up to the Twin Gate"))
W(ul_open())
W(li("Ancient neutral camps near stream ends demoted to medium camps and moved slightly towards bases", t("MISC")))
W(li("Medium neutral camp near offlane defender's gate has been demoted to a small neutral camp", t("MISC")))
W(li("The tier 1 safe lane towers have been moved slightly away from their pull camps and where the creeps meet", t("MISC")))
W(li("Radiant safe lane small camp has been slightly moved north away from the lane", t("MISC")))
W(li("Radiant safe lane hard camp's spawn box has been moved towards the offlane to remove a bad ward location", t("MISC")))
W(li("Radiant offlane tier 2 tower has been adjusted slightly to the left, such that creeps do not path on both sides of the tower", t("MISC")))
W(li("The ramp leading from the Radiant tier 1 tower to the stream has been decreased in width and moved away from the tower", t("NERF")))
W(li("The medium flooded camp near the safe lane tier 2 towers moved closer to the middle of the stream (substantially more for Dire than for Radiant)", t("MISC")))
W(li("The medium flooded camp near the safe lane tier 2 towers can now only evolve once into a hard camp, rather than into an Ancient Camp", t("REWORK")))
W(li("The medium flooded camp near the bounty runes can now evolve twice into an Ancient Camp", t("REWORK")))
W(li("Removed several trees from Dire Safelane easy pull camp and Radiant Safelane hard pull camp", t("MISC")))
W(ul_close())
W(plain_header("Mechanics Changes"))

W(subgroup("Health Restoration"))
W(ul_open())
W(li("Health Restoration now applies to all forms of life gain", t("REWORK")))
W(ul_close())
W(subnote("Previously, it did not apply to incoming heals"))
W(ul_open())
W(li("Incoming Heal Amplification now stacks diminishingly with Health Restoration instead of additively with Outgoing Heal Amplification", t("REWORK")))
W(li("Spells that previously had a separate value for incoming heal reduction now only modify Health Restoration", t("REWORK")))
W(ul_close())
W(subnote("* Eye of Skadi's Cold Attack<br>* Spirit Vessel's Soul Release<br>* Omniknight's Guardian Angel with Aghanim's Scepter<br>* Pudge's Rot with Aghanim's Scepter"))
W(ul_open())
W(li("As a result of the changes, spells that only modified Health Restoration will now additionally affect incoming heals", t("REWORK")))
W(ul_close())
W(subnote("* Sange<br>* Kaya and Sange<br>* Sange and Yasha<br>* Abyssal Blade<br>* Orb of Frost's Frost<br>* Orb of Corrosion's Corrosion<br>* Crippling Crossbow's Hobble<br>* Jidi Pollen Bag's Pollinate<br>* Item bonus from Crude enchantment<br>* Abaddon’s Withering Mist<br>* Drow Ranger’s Frost Arrows with Aghanim’s Scepter<br>* Slark's Saltwater Shiv"))

W(subgroup("Lifesteal and Damage Manipulations"))
W(ul_open())
W(li("Physical and Magical Lifesteal will now take into account overall damage reductions/amplifications when computing how much to lifesteal", t("REWORK")))
W(ul_close())
W(subnote("This affects the following:<br><br>* Aeon Disk<br>* Bloodstone<br>* Consecrated Wraps<br>* Veil of Discord<br>* Prophet's Pendulum<br>* Audacious Enchantment<br>* Abaddon's Borrowed Time with Aghanim's Scepter<br>* Beastmaster's Wild Axes<br>* Bounty Hunter's Shadow Walk with talent<br>* Bristleback's Bristleback<br>* Centaur Warrunner's Stampede<br>* Grimstroke's Ink Trail<br>* Grimstroke's Soulbind with talent<br>* Hoodwink's Hunter's Boomerang<br>* Leshrac's Pulse Nova with talent<br>* Lich's Frost Shield<br>* Luna's Lunar Orbit<br>* Kunkka's Admiral's Rum<br>* Mars' Bulwark<br>* Nyx Assassin's Burrow<br>* Ogre Magi's Fire Shield<br>* Oracle's False Promise<br>* Pudge's Flesh Heap<br>* Shadow Demon's Menace<br>* Spectre's Dispersion<br>* Treant Protector's Living Armor<br>* Underlord's Invading Force<br>* Undying's Flesh Golem<br>* Ursa's Enrage<br>* Visage's Gravekeeper's Cloak<br>* Warlock's Golem with talent"))
W(ul_open())
W(li("Historically, Lifesteal was calculated before some damage reductions or amplifications were applied. As a result, you could gain health from attacks that dealt no damage (like attacks against a hero affected by Aeon Disk's Combo Breaker). This will not happen anymore", t("MISC")))
W(li("The only amplification that is not taken into account is increased damage against illusions", t("BUFF")))
W(ul_close())

W(subgroup("Miscellaneous"))
W(ul_open())
W(li("All sources of reflection damage now have an ALT-note detailing mechanics of reflected damage", t("MISC")))
W(ul_close())
W(subnote("The following items and abilities deal reflected damage:<br>* Tormentor's Reflect ability<br>* Blade Mail (both active and passive)<br>* Chipped Vest<br>* Rattlecage<br>* Axe's Counter Helix<br>* Bristleback's Quill Spray triggered by Bristleback passive<br>* Centaur Warrunner's Retaliate<br>* Nyx Assassin's Spiked Carapace<br>* Queen of Pain's Scream of Pain<br>* Razor's Storm Surge<br>* Shadow Demon's Disseminate<br>* Spectre's Dispersion<br>* Tidehunter's Anchor Smash triggered by Kraken Shell passive<br>* Viper's Corrosive Skin<br>* Warlock's Fatal Bonds"))
W(ul_open())
W(li("Reflected damage cannot be reflected back", t("NERF")))
W(li("Lifesteal and Spell Lifesteal don't apply to reflected damage", t("MISC")))
W(li("Reflected damage doesn't affect Debuff Immune units", t("MISC")))
W(li("Units with free movement now can miss their attacks when attacking uphill targets", t("REWORK")))
W(ul_close())
W(subnote("Affected units:<br>* Batrider during Firefly<br>* Dragon Knight during Elder Dragon Form with Aghanim's Scepter<br>* Lina during Flame Cloak<br>* Terrorblade's Reflection illusions"))

W(plain_header("Shop Reshuffle"))
W(ul_open())
W(li("Items in all shop categories except for Consumables have been rearranged to accommodate new items", t("MISC")))
W(li("Consumables now includes Infused Raindrops", t("MISC")))
W(ul_close())

# ===== ITEM UPDATES =====
W(section("Item Updates"))

W(item_header("Chasm Stone", new=True))
W(ul_open())
W(li("Costs 800 gold", t("MISC")))
W(li("Provides +40 Area of Effect", t("MISC")))
W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))
W(ul_close())
W(item_header("Shawl", new=True))
W(ul_open())
W(li("Costs 450 gold", t("MISC")))
W(li("Provides +10% Magic Resistance", t("MISC")))
W(ul_close())
W(item_header("Splintmail", new=True))
W(ul_open())
W(li("Costs 950 gold", t("MISC")))
W(li("Provides +7 Armor", t("MISC")))
W(ul_close())
W(item_header("Wizard Hat", new=True))
W(ul_open())
W(li("Costs 250 gold", t("MISC")))
W(li("Provides +125 Mana", t("MISC")))
W(ul_close())
W(item_header("Chainmail"))
W(ul_open())
W(li("Cost decreased from 550g to 500g", b(550, 500)))
W(ul_close())
W(item_header("Cloak"))
W(ul_open())
W(li("Cost increased from 800g to 900g", b(800, 900)))
W(li("Magic Resistance bonus decreased from +20% to +18%", b(20, 18)))
W(ul_close())
W(item_header("Cornucopia"))
W(ul_open())
W(li("Item removed from the game", t("DEL")))
W(ul_close())
W(item_header("Orb Of Frost"))
W(ul_open())
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Refresher Shard"))
W(ul_open())
W(li("Reset Cooldowns no longer refreshes items", t("NERF")))
W(ul_close())
W(item_header("Ring Of Health"))
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

W(subgroup("Upgrades"))
W(item_header("Consecrated Wraps", new=True))
W(ul_open())
W(li("Requires Vitality Booster (1000), Shawl (450), Crown (450), and a recipe (700). Total cost: 2600g", t("MISC")))
W(li("Provides +15% Magic Resistance, +250 Health, and +6 All Attributes", t("MISC")))
W(li("Passive: Hallowed. Gain a stack every 3s, up to a maximum of 3 stacks. Whenever the wearer takes damage from a player-controlled unit or Roshan, all stacks are removed to create an all-damage barrier for 7s that absorbs 120 damage per removed stack (up to 360). If the wearer reached a max amount of stacks at least once in a game, regaining a stack provides a non-stacking buff that increases movespeed by 20% for 7s", t("MISC")))
W(li("Has no damage threshold, but doesn't proc from Health Loss damage (like Heartstopper Aura)", t("MISC")))
W(li("Can't gain stacks for 3s after taking damage from Roshan or player-controlled sources", t("NERF")))
W(ul_close())
W(item_header("Crella's Crozier", new=True))
W(ul_open())
W(li("Requires Ghost Scepter (1500), Soul Booster (3000), and a recipe (300). Total cost: 4800g", t("MISC")))
W(li("Provides +6 All Attributes, +450 Health, +450 Mana", t("MISC")))
W(li("Active: Rite of Rumusque. The wearer enters ghost form for 4 seconds, becoming immune to physical damage, but is unable to attack and 30% more vulnerable to magic damage. Steals 5% movement speed from enemy heroes in a 900 radius every second. Movement speed steal lasts 1.5s. Bonuses stack and have duration refreshed on gaining new stacks. No Mana Cost. Cooldown: 20s", t("MISC")))
W(li("The ghost form and stolen speed can be dispelled off the wearer, but the stealing debuff that provides new stacks can't", t("NERF")))
W(li("Passive: Putrefaction Aura. Reduces health restoration of nearby enemy heroes by 30%. While Rite of Rumusque is active, the effect is increased to 75% and all of the lost Health Restoration is redirected to the wearer every second. Radius: 900", t("BUFF")))
W(ul_close())
W(item_header("Essence Distiller", new=True))
W(ul_open())
W(li("Requires Urn of Shadows (825), Chainmail (500), Wizard Hat (250), and a recipe (200). Total cost: 1775g", t("MISC")))
W(li("Provides +1.75 Mana Regen, +3 All Attributes, +6 Armor, and +150 Mana", t("MISC")))
W(li("Active: Soul Release. When cast on an ally, provides 40 health regeneration. If the ally is attacked by an enemy hero or Roshan, the effect is lost. When cast on an enemy, deals 25 damage per second, provides True Sight over them and shares their vision with the wearer's team. Both effects last 8 seconds. Can be cast on the ground to put a dormant effect that will latch to the first enemy hero that comes within 400 range from it. The effect waits for 15s and provides 400 vision until it disappears. Gains charges every time an enemy hero dies within 1500 units. Cast Range: 1000. No Mana Cost. Cooldown: 10s", t("MISC")))
W(li("Gains one charge if the wearer dies with an empty Essence Distiller", t("MISC")))
W(li("Gains two charges if Essence Distiller had no charges and an enemy hero dies within radius", t("MISC")))
W(ul_close())
W(item_header("Specialist's Array"))
W(ul_open())
W(li("Requires Blade of Alacrity (1000), Broadsword (1000), and a recipe (550). Total cost: 2550g", t("MISC")))
W(li("Provides +20 Damage and +12 Agility", t("MISC")))
W(li("Passive: Splitshot. Ranged Only. Ranged attacks have a 30% chance to fire additional projectiles at up to 2 nearby enemies that aren't the original attack target within 120 degree angle in front of the wearer and within attack range + 150. The additional projectiles deal 20 + 75% damage of a normal attack and do not trigger on hit effects. The primary attack deals 20 + full damage of a normal attack when the ability procs", t("MISC")))
W(li("Doesn't work with other sources of secondary projectiles from hero abilities", t("MISC")))
W(li("Gyrocopter's Flak Cannon", t("MISC")))
W(li("Medusa's Split Shot", t("MISC")))
W(li("Muerta's Gunslinger", t("MISC")))
W(ul_close())
W(item_header("Hydras Breath", new=True))
W(ul_open())
W(li("Requires Specialist's Array (2550), Dragon Lance (1900), Orb of Venom (350) and a recipe (1100). Total cost: 5900g", t("MISC")))
W(li("Provides +25 Damage, +30 Agility, +15 Strength, and +150 Attack Range (Ranged Only)", t("MISC")))
W(li("Passive: Miasma. Attacks poison the target for 3 seconds, dealing magical damage equal to 2.5% of the target's max health every second. If the debuff is reapplied, the duration is refreshed. Can't be applied by illusions or to Roshan", t("NERF")))
W(li("Passive: Polycephaly. Ranged attacks have a 30% chance to fire at up to 3 nearby enemies that aren't the original attack target within 120 degree angle in front of the wearer and within attack range + 150. The additional projectiles deal 20 + 75% damage of a normal attack and do not trigger on hit effects except for Miasma. The primary attack deals 20 + full damage of a normal attack when the ability procs", t("MISC")))
W(li("Similarly to Specialist's Array, doesn't work with other sources of secondary projectiles from hero abilities", t("MISC")))
W(ul_close())
W(item_header("Arcane Boots"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now also requires a Wizard Hat (250g)", t("REWORK")))
W(li("Recipe cost decreased from 475 to 325. Total cost increased from 1400g to 1500g", b(475, 325, l=True)))
W(li("Now also provides +125 Mana", t("REWORK")))
W(ul_close())
W(item_header("Guardian Greaves"))
W(ul_open())
W(li("Recipe cost increased from 1125 to 1175. Total cost increased from 4300g to 4450g (due to Arcane Boots cost increase)", b(1125, 1175, l=True)))
W(li("Now also provides +150 Mana", t("REWORK")))
W(li("Mana Regen bonus decreased from +1.5 to +1", b(1.5, 1)))
W(ul_close())
W(item_header("Battle Fury"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Perseverance (1400) instead of Cornucopia (1200)", t("REWORK")))
W(li("Recipe cost decreased from 600 to 400. Total cost unchanged at 3900g", b(600, 400, l=True)))
W(ul_close())
W(item_header("Black King Bar"))
W(ul_open())
W(li("Avatar duration changed from 9/8/7/6s to 9/8/7s", b([9, 8, 7, 6], [9, 8, 7])))
W(ul_close())
W(item_header("Blade Mail"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Splintmail (950) instead of Chainmail (550)", t("REWORK")))
W(li("Recipe cost decreased from 750 to 450. Total cost increased from 2300g to 2400g", b(750, 450, l=True)))
W(li("Armor bonus increased from +6 to +7", b(6, 7)))
W(ul_close())
W(item_header("Crimson Guard"))
W(ul_open())
W(li("Armor bonus decreased from +8 to +6", b(8, 6)))
W(li("Guard base damage block rescaled from 70 for all units to 70 on melee heroes and buildings and 45 on ranged heroes", t("REWORK")))
W(li("Guard max health damage block decreased from 2.2% to 2%", b(2.2, 2)))
W(ul_close())
W(item_header("Dagon"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Point Booster (1200), Wizard Hat (250) and Crown (450) instead of Diadem (1000) and Voodoo Mask (650)", t("REWORK")))
W(li("Recipe cost unchanged at 1150. Total cost increased from 2800/3950/5100/6250/7400g to 3050/4200/5350/6500/7650g", b([2800, 3950, 5100, 6250, 7400], [3050, 4200, 5350, 6500, 7650], l=True)))
W(li("No longer provides +15/16/17/18/19% Spell Lifesteal", t("NERF")))
W(li("All Attributes bonus decreased from +7/9/11/13/15 to +6/7/8/9/10", b([7, 9, 11, 13, 15], [6, 7, 8, 9, 10])))
W(li("Now also provides +200/210/220/230/240 Health, +350/375/400/425/450 Mana, and +60/90/120/150/180 Cast Range", t("REWORK")))
W(li("Cast Range Bonus does not stack with Aether Lens or multiple Dagons", t("MISC")))
W(li("Energy Burst cast range decreased from 700/750/800/850/900 to 640", b([700, 750, 800, 850, 900], 640)))
W(li("Effective cast range with item's built-in Cast Range bonus decreased from 700/750/800/850/900 to 700/730/760/790/820", b([700, 750, 800, 850, 900], [700, 730, 760, 790, 820])))
W(li("Energy Burst no longer instantly kills non-ancient creeps", t("NERF")))
W(li("Energy Burst no longer heals for 75% of damage dealt", t("NERF")))
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
W(item_header("Ancient Janggo"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Headdress (425) instead of Robe of the Magi (450)", t("REWORK")))
W(li("Recipe cost increased from 500 to 525. Total cost unchanged at 1625g", b(500, 525, l=True)))
W(li("No longer provides +7 Intelligence", t("NERF")))
W(li("Strength bonus increased from +7 to +8", b(7, 8)))
W(li("Swiftness Aura now also provides +2.5 Health Regen", t("REWORK")))
W(li("Endurance now shares cooldown with Boots of Bearing", t("REWORK")))
W(ul_close())
W(item_header("Boots of Bearing"))
W(ul_open())
W(li("No longer provides +8 Intelligence", t("NERF")))
W(li("Swiftness Aura now also provides +2.5 Health Regen", t("REWORK")))
W(li("Endurance now shares cooldown with Drum of Endurance", t("REWORK")))
W(ul_close())
W(item_header("Eternal Shroud"))
W(ul_open())
W(li("Item removed from the game", t("DEL")))
W(ul_close())
W(item_header("Ethereal Blade"))
W(ul_open())
W(li("Can no longer be disassembled", t("NERF")))
W(ul_close())
W(item_header("Gungir"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now also requires Chasm Stone (800)", t("REWORK")))
W(li("Recipe cost decreased from 1100 to 400. Total cost increased from 4550g to 4650g", b(1100, 400, l=True)))
W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))
W(ul_close())
W(item_header("Glimmer Cape"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Shawl (450) instead of Cloak (800)", t("REWORK")))
W(li("Recipe cost increased from 450 to 800. Total cost unchanged at 2150g", b(450, 800, l=True)))
W(ul_close())
W(item_header("Hand Of Midas"))
W(ul_open())
W(li("Transmute no longer prevents camp-clearing Madstone Bundles from spawning if it was used on the last creep in neutral camp", t("NERF")))
W(li("Getting guaranteed Madstone Bundle from Transmute used to prevent the camp-clearing bundle from spawning", t("MISC")))
W(ul_close())
W(item_header("Harpoon"))
W(ul_open())
W(li("Draw Forth can now target trees and will pull the caster to it, destroying all trees on the way", t("REWORK")))
W(ul_close())
W(item_header("Heaven's Halberd"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Talisman of Evasion (1300), Splintmail (950), Ring of Health (700), and a recipe (450). Total cost: 3400g", t("REWORK")))
W(li("Used to require Vanguard (1700), Crown (450) and a recipe (450). Total cost: 2600g", t("MISC")))
W(li("Can no longer be disassembled", t("NERF")))
W(li("No longer provides +275 Health", t("NERF")))
W(li("Now also provides +9 Armor and +25% Evasion", t("REWORK")))
W(li("No longer has Damage Block passive", t("NERF")))
W(li("Disarm cooldown decreased from 20s to 16s", b(20, 16, l=True)))
W(li("Disarm cast range increased from 650 to 750", b(650, 750)))
W(li("Disarm duration increased from 3s to 3.5s", b(3, 3.5)))
W(ul_close())
W(item_header("Kaya"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +40% to +30%", b(40, 30)))
W(ul_close())
W(item_header("Kaya and Sange"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +50% to +40%", b(50, 40)))
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Meteor Hammer"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +40% to +35%", b(40, 35)))
W(ul_close())
W(item_header("Yasha And Kaya"))
W(ul_open())
W(li("Mana Regen Amplification bonus decreased from +50% to +40%", b(50, 40)))
W(ul_close())
W(item_header("Lotus Orb"))
W(ul_open())
W(li("Can no longer be disassembled", t("NERF")))
W(ul_close())
W(item_header("Mage Slayer"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Perseverance (1400) instead of Cornucopia (1200)", t("REWORK")))
W(li("Now requires Blades of Attack (450) instead of Gloves of Haste (450)", t("REWORK")))
W(li("Total cost increased from 2800g to 3100g (change is bigger due to Cloak cost increase)", b(2800, 3100, l=True)))
W(li("No longer provides +30 Attack Speed", t("NERF")))
W(li("Health Regen bonus increased from +5 to +6", b(5, 6)))
W(li("Mana Regen bonus increased from +2 to +2.5", b(2, 2.5)))
W(li("Damage bonus increased from +8 to +15", b(8, 15)))
W(li("Mage Slayer damage type changed from magical to physical", t("MISC")))
W(li("Mage Slayer damage per second increased from 20 to 40", b(20, 40)))
W(ul_close())
W(item_header("Mask Of Madness"))
W(ul_open())
W(li("Berserk now also grants 30% Slow Resistance for the duration", t("REWORK")))
W(li("Berserk bonus Movement Speed changed from +25 for all heroes to +8%/12% for Ranged/Melee", t("MISC")))
W(li("Berserk armor reduction decreased from 8 to 7", b(8, 7)))
W(ul_close())
W(item_header("Mekansm"))
W(ul_open())
W(li("Recipe cost increased from 800 to 850. Total cost unchanged at 1775g (due to Chainmail cost decrease)", b(800, 850, l=True)))
W(ul_close())
W(item_header("Monkey King Bar"))
W(ul_open())
W(li("Recipe cost increased from 600 to 900. Total cost increased from 4700g to 5000g", b(600, 900, l=True)))
W(li("Now also provides +50 Attack Range to melee heroes only", t("REWORK")))
W(li("Damage bonus increased from +40 to +50", b(40, 50)))
W(li("Attack Speed bonus increased from +45 to +50", b(45, 50)))
W(ul_close())
W(item_header("Nullifier"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Splintmail (950) instead of Helm of Iron Will (975)", t("REWORK")))
W(li("Total cost decreased from 4375g to 4350g", b(4375, 4350, l=True)))
W(li("No longer provides +6 Health Regen", t("NERF")))
W(ul_close())
W(item_header("Oblivion Staff"))
W(ul_open())
W(li("Mana Regen bonus increased from +1 to +1.25", b(1, 1.25)))
W(ul_close())
W(item_header("Orchid"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Claymore (1350) instead of Cornucopia (1200)", t("REWORK")))
W(li("Recipe cost decreased from 450 to 300. Total cost unchanged at 3275g", b(450, 300, l=True)))
W(li("No longer provides +6 Health Regen", t("NERF")))
W(li("Damage bonus increased from +10 to +20", b(10, 20)))
W(li("Mana Regen bonus decreased from +3 to +2.5", b(3, 2.5)))
W(li("Intelligence bonus increased from +10 to +12", b(10, 12)))
W(ul_close())
W(item_header("Bloodthorn"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Oblivion Staff (1625) instead of Hyperstone (2000)", t("REWORK")))
W(li("Recipe cost increased from 450 to 600. Total cost decreased from 6625g to 6400g", b(450, 600, l=True)))
W(li("No longer provides +6.5 Health Regen", t("NERF")))
W(li("Intelligence bonus increased from +10 to +25", b(10, 25)))
W(li("Attack Speed bonus decreased from +95 to +70", b(95, 70)))
W(li("Mana Regen bonus increased from +3.25 to +4", b(3.25, 4)))
W(li("Damage bonus increased from +10 to +20", b(10, 20)))
W(li("Soul Rend Mana Cost increased from 125 to 150", b(125, 150, l=True)))
W(ul_close())
W(item_header("Orb Of Corrosion"))
W(ul_open())
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Skadi"))
W(ul_open())
W(li("Cold Attack no longer has a separate value for incoming heal reduction ", t("NERF")))
W(ul_close())
W(subnote("Still reduces incoming heals due to Health Restoration changes"))
W(ul_open())
W(li("Cold Attack health restoration reduction increased from 40% to 50%", b(40, 50)))
W(ul_close())
W(item_header("Pavise"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Wizard Hat (250) instead of Energy Booster (800)", t("REWORK")))
W(li("Recipe cost increased from 175 to 675. Total cost decreased from 1400g to 1350g", b(175, 675, l=True)))
W(li("Mana bonus decreased from +250 to +175", b(250, 175)))
W(ul_close())
W(item_header("Solar Crest"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Chainmail (500) instead of Crown (450)", t("REWORK")))
W(li("Recipe cost unchanged at 500. Total cost unchanged at 2575g (due to Pavise cost decrease)", t("MISC")))
W(li("No longer provides +4 All Attributes", t("NERF")))
W(li("Armor bonus increased from +4 to +7", b(4, 7)))
W(li("Mana bonus decreased from +300 to +200", b(300, 200)))
W(li("Health bonus increased from +175 to +200", b(175, 200)))
W(ul_close())
W(item_header("Pers"))
W(ul_open())
W(li("Health Regen bonus decreased from +6.5 to +5.5", b(6.5, 5.5)))
W(ul_close())
W(item_header("Phase Boots"))
W(ul_open())
W(li("Cost decreased from 1500g to 1450g (due to Chainmail cost decrease)", b(1500, 1450)))
W(ul_close())
W(item_header("Phylactery"))
W(ul_open())
W(li("Health Regen bonus decreased from +6.5 to +5.5", b(6.5, 5.5)))
W(ul_close())
W(item_header("Pipe"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Shawl (450) instead of Headdress (425)", t("REWORK")))
W(li("Recipe Cost decreased from 800 to 675. Total cost unchanged at 3725g (due to Cloak cost increase)", b(800, 675, l=True)))
W(li("Barrier no longer affects units that have been affected by Barrier within Pipe of Insight's cooldown", t("NERF")))
W(li("Insight Aura no longer provides 2.5 health regen", t("NERF")))
W(ul_close())
W(item_header("Radiance"))
W(ul_open())
W(li("Burn toggling no longer breaks invisibility nor stops channels", t("NERF")))
W(ul_close())
W(item_header("Refresher"))
W(ul_open())
W(li("Health Regen bonus increased from +12 to +14", b(12, 14)))
W(li("Mana Regen bonus increased from +6 to +7", b(6, 7)))
W(li("Reset Cooldowns cooldown decreased from 180/190/200/210s to 180s ", b([180, 190, 200, 210], 180, l=True)))
W(ul_close())
W(subnote("No longer scales with uses"))
W(ul_open())
W(li("Reset Cooldowns mana cost decreased from 400 to 325", b(400, 325, l=True)))
W(li("Reset Cooldowns no longer refreshes items", t("NERF")))
W(ul_close())
W(item_header("Revenants Brooch"))
W(ul_open())
W(li("Spell Lifesteal bonus increased from +14% to +15%", b(14, 15)))
W(ul_close())
W(item_header("Sange"))
W(ul_open())
W(li("Slow Resistance bonus increased from +20% to +25%", b(20, 25)))
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Abyssal Blade"))
W(ul_open())
W(li("Slow Resistance bonus increased from +25% to +30%", b(25, 30)))
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Sange and Yasha"))
W(ul_open())
W(li("Status Resistance bonus increased from +15% to +16%", b(15, 16)))
W(li("Slow Resistance bonus increased from +25% to +30%", b(25, 30)))
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Shiva's Guard"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Splintmail (950) and Chasm Stone (800) instead of Veil of Discord (1725)", t("REWORK")))
W(li("Recipe cost decreased from 2050 to 1350. Total cost decreased from 5175g to 4500g", b(2050, 1350, l=True)))
W(li("No longer provides +5 Strength, +5 Agility, +5 Intelligence, or +5 Health Regen", t("NERF")))
W(li("Armor bonus increased from +15 to +17", b(15, 17)))
W(li("Now also provides +75 Area of Effect", t("REWORK")))
W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))
W(li("Arctic Blast damage increased from 200 to 260", b(200, 260)))
W(li("Arctic Blast radius decreased from 900 to 825 ", b(900, 825)))
W(ul_close())
W(subnote("Effective spell radius unchanged due to item's built-in Area of Effect bonus"))
W(ul_open())
W(li("Arctic Blast no longer increases damage taken from spells", t("NERF")))
W(li("Freezing Aura no longer reduces Health Restoration and Incoming Heal Amplification by 25%", t("NERF")))
W(li("Freezing Aura now pierces debuff immunity", t("REWORK")))
W(ul_close())
W(item_header("Spirit Vessel"))
W(ul_open())
W(li("Soul Release no longer has a separate value for incoming heal reduction ", t("NERF")))
W(ul_close())
W(subnote("Still reduces incoming heals due to Health Restoration changes"))
W(item_header("Tranquil Boots"))
W(ul_open())
W(li("Break now also goes on cooldown when the item is disassembled. Reassembling the item will remember the time remaining", t("REWORK")))
W(ul_close())
W(item_header("Veil Of Discord"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Voodoo Mask (650), Robe of the Magi (450), Fluffy Hat (250), and a recipe (350). Total cost: 1700g", t("REWORK")))
W(li("Used to require Ring of Health (700), Chainmail (550), Circlet (155), and a recipe (320). Total cost: 1725g", t("MISC")))
W(li("No longer provides +4 Armor, +4 All Attributes or +4.5 Health Regen", t("NERF")))
W(li("Now provides +10 Intelligence, +175 Health and +18% Spell Lifesteal", t("REWORK")))
W(li("Magic Weakness renamed to Spell Weakness", t("MISC")))
W(ul_close())
W(item_header("Bloodstone"))
W(ul_open())
W(li("Recipe changed", t("MISC")))
W(li("Now requires Veil of Discord (1700) instead of Void Stone (700) and Voodoo Mask (650). Total cost increased from 4350g to 4700g", b(4350, 4700, l=True)))
W(li("No longer provides +3 Mana Regen", t("NERF")))
W(li("Spell Lifesteal bonus decreased from +25% to +20%", b(25, 20)))
W(li("Health bonus increased from +450 to +650", b(450, 650)))
W(li("Now also provides +15 Intelligence", t("REWORK")))
W(li("Bloodpact no longer applies a basic dispel", t("NERF")))
W(li("Bloodpact no longer multiplies spell lifesteal bonus by 3. Now increases spell lifesteal to 60% instead ", t("NERF")))
W(ul_close())
W(subnote("Spell Lifesteal during Bloodpact decreased from 75% to 60%"))
W(ul_open())
W(li("Bloodpact no longer has a 30s self debuff preventing repeated usage of Bloodpact", t("NERF")))
W(li("Now also provides passive Spell Weakness Aura", t("REWORK")))
W(li("Enemy units within 1200 radius take 12% increased damage from spells", t("BUFF")))
W(li("Effect does not stack with Veil of Discord's Spell Weakness", t("MISC")))
W(ul_close())
W(item_header("Witch Blade"))
W(ul_open())
W(li("Recipe cost increased from 250 to 300. Total cost unchanged at 2775g (due to Chainmail cost decrease)", b(250, 300, l=True)))
W(ul_close())
W(plain_header("Neutral Artifact Changes"))
W(subgroup("General changes"))
W(ul_open())
W(li("Tier 1 availability changed from 5:00 to 0:00", t("BUFF")))
W(li("Madstone crafting cost for Tier 1 items increased from 5 to 6", b(5, 6)))
W(ul_close())
W(subgroup("Artifact changes"))
W(ul_open())
W(li("Number of artifact choices increased from 4 to 5 for Tiers 2-5", b(4, 5)))
W(ul_close())
W(item_header("Ash Legion Shield"))
W(ul_open())
W(li("Shield Wall damage barrier increased from 140 to 160", b(140, 160)))
W(li("Shield Wall movement speed reduction increased from 12 to 20", b(12, 20)))
W(ul_close())
W(item_header("Chipped Vest"))
W(ul_open())
W(li("Chipper damage returned to attacking creeps decreased from 20 to 15", b(20, 15)))
W(ul_close())
W(item_header("Dagger Of Ristul"))
W(ul_open())
W(li("Returning as a Tier 1 Neutral Artifact", t("MISC")))
W(li("Active: Imbrue. Increase attack damage by 25 for 8s. Health Cost: 100. Cooldown: 30s", t("MISC")))
W(ul_close())
W(item_header("Foragers Kit", new=True))
W(ul_open())
W(li("When this item is off cooldown, the wearer can see trees that can be foraged. Standing next to one of those trees for 1s will give the wearer one of the following items. Cooldown: 60s. Tree reveal radius: 1200", t("MISC")))
W(li("All items except for bag of gold are placed in inventory (if there are slots available) and can stack up to 5 times per slot", t("MISC")))
W(li("Possible items:", t("MISC")))
W(li("Ironwood Nut: Passively provides +3 Movement Speed. Grants +1 Primary Stat when consumed (+.4 all stats for universal heroes)", t("MISC")))
W(li("Tomo'kan Ringcap: Passively Provides +2 Intelligence. Can be consumed to instantly grant a target 50 + 5% of their maximum mana", t("MISC")))
W(li("Vital Toadstool: Passively Provides +2 Damage. Can be consumed to grant a target +1% Max Health Regeneration for 10s. If the unit is attacked by an enemy hero or Roshan the bonus is lost", t("MISC")))
W(li("Bag of Gold: Provides 30 gold to the wearer. Don't need to be picked up", t("MISC")))
W(ul_close())
W(item_header("Possessed Mask"))
W(ul_open())
W(li("Returning as a Tier 1 Neutral Artifact", t("MISC")))
W(li("Passive: Lifesteal. Attacks heal for 5 health ", t("MISC")))
W(ul_close())
W(subnote("This counts as lifesteal and is manipulated by Health Restoration"))
W(item_header("Stonefeather Satchel", new=True))
W(ul_open())
W(li("Toggle: Transmogrify. Activate to switch the contents of the satchel between Feathers or Rocks. No Mana Cost. Cooldown: 6s.", t("MISC")))
W(li("Pound of Feathers: Increases movement speed by 12 and distance of forced movement effects on yourself by 30%", t("MISC")))
W(li("Pound of Rocks: Increases armor by 3 and decreases distance of forced movement effects by 30%", t("MISC")))
W(ul_close())
W(item_header("Weighted Dice"))
W(ul_open())
W(li("Loaded now also increases max base damage by 6", t("REWORK")))
W(ul_close())
W(item_header("Crippling Crossbow"))
W(ul_open())
W(li("Moved from Tier 4 to Tier 2", t("MISC")))
W(li("Hobble initial damage decreased from 75 to 25", b(75, 25)))
W(li("Hobble Max slow decreased from 80% to 50%", b(80, 50)))
W(li("Hobble Cast Range decreased from 800 to 650", b(800, 650)))
W(li("Hobble now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Medallion Of Courage"))
W(ul_open())
W(li("Returning as a Tier 2 Neutral Artifact", t("MISC")))
W(li("Active: Valor. If cast on an ally, increases their armor by 7 for 8s. If cast on an enemy, decreases their armor by 4 for 8s. Cannot be cast on self. Cast Range: 1000. Mana Cost: 30. Cooldown: 18s ", t("NERF")))
W(ul_close())
W(subnote("Dormant Curio increases duration from 8s to 10.4s"))
W(item_header("Searing Signet"))
W(ul_open())
W(li("Burn Through: Total Damage decreased from 90 to 80 ", b(90, 80)))
W(ul_close())
W(subnote("From 117 to 104 with Dormant Curio"))
W(ul_open())
W(li("Burn Through: Damage Threshold increased from 55 to 60", b(55, 60)))
W(ul_close())
W(item_header("Seeds Of Serenity"))
W(ul_open())
W(li("Returning as a Tier 2 Neutral Artifact", t("MISC")))
W(li("Active: Verdurous Dale. Place a 400 unit circle on the ground for 8s that increases health regeneration of allies inside by 8 + 25% of the caster's health regeneration. Cast Range: 350. No Mana Cost. Cooldown: 35s ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases health regeneration from 8 to 10.4 and from 25% to 32.5%"))
W(item_header("Whisper Of The Dread"))
W(ul_open())
W(li("Item cycled out", t("MISC")))
W(ul_close())
W(item_header("Cloak Of Flames"))
W(ul_open())
W(li("Returning as a Tier 3 Neutral Artifact", t("MISC")))
W(li("Passive: Immolate. Burns enemy units in a 375 unit radius for 40 damage per second. Illusions deal 25 damage per second ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases damage from 40 to 52 and illusion damage from 25 to 32.5"))
W(item_header("Gunpowder Gauntlets"))
W(ul_open())
W(li("Beat the Crowd cooldown increased from 6s to 10s", b(6, 10, l=True)))
W(ul_close())
W(item_header("Jidi Pollen Bag"))
W(ul_open())
W(li("Pollinate health restoration loss increased from 30% to 50%", b(30, 50)))
W(li("Pollinate now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(item_header("Partisans Brand", new=True))
W(ul_open())
W(li("Passive: Brand. Increases spell damage against player controlled units by 9% ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases bonus spell damage from 9% to 11.7%"))
W(ul_open())
W(li("Player controlled units includes heroes and any creep summoned or converted by them", t("MISC")))
W(ul_close())
W(item_header("Serrated Shiv"))
W(ul_open())
W(li("Gut 'Em cooldown increased from 1s to 1.5s", b(1, 1.5, l=True)))
W(ul_close())
W(item_header("Spellslinger", new=True))
W(ul_open())
W(li("Passive: Salvo. Whenever you cast a spell, 20% of the spell's mana cost is restored over 10s. Tick rate: 2s ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases mana restored from 20% to 26%"))
W(ul_open())
W(li("Mana recovery duration cannot be modified", t("NERF")))
W(ul_close())
W(item_header("Stormcrafter"))
W(ul_open())
W(li("Returning as a Tier 3 Neutral Artifact", t("MISC")))
W(li("Passive: Bottled Lightning. Every 6s, zaps up to 2 enemies within 700 units, slowing them by 40% for 0.4s and dealing 70 magic damage ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases damage from 70 to 91"))
W(item_header("Conjurer's Catalyst"))
W(ul_open())
W(li("Passive: Spellover. Every 100 spell damage dealt to an enemy deals damage to their surrounding allies in a 300 unit radius. Hero targets deal 40 damage to their allies, other targets deal 15 damage ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases hero damage from 40 to 52 and non-hero damage from 15 to 19.5"))
W(item_header("Dandelion Amulet"))
W(ul_open())
W(li("Returning as a Tier 4 Neutral Artifact", t("MISC")))
W(li("Passive: Magical Damage Block. Blocks 300 magic damage from instances over 75 damage. Cooldown: 12s ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases blocked damage from 300 to 390"))
W(item_header("Enchanter's Bauble"))
W(ul_open())
W(li("Passive: Enchant. Increases bonuses of the item's Neutral Enchantment by 15%. Every time you craft this item again the bonus is increased by 40% ", t("BUFF")))
W(ul_close())
W(subnote("Dormant Curio increases recraft stat bonus from 40% to 52%"))
W(ul_open())
W(li("You can select any Enchantments during re-craft and bonus will still keep increasing as long as you keep Enchanter's Bauble", t("MISC")))
W(ul_close())
W(item_header("Metamorphic Mandible"))
W(ul_open())
W(li("Pupate duration increased from 4s to 5s ", b(4, 5)))
W(ul_close())
W(subnote("From 5.2s to 6.5s with Dormant Curio"))
W(ul_open())
W(li("Pupate bonus magic resistance increased from 35% to 50%", b(35, 50)))
W(ul_close())
W(item_header("Prophets Pendulum", new=True))
W(ul_open())
W(li("Passive: Linger. 30% of damage taken is delayed over 5 seconds. Damage Ticks every 1 second and is lethal ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases damage delayed from 30% to 39%"))
W(item_header("Rattlecage"))
W(ul_open())
W(li("Reverberate damage threshold increased from 180 to 220", b(180, 220)))
W(ul_close())
W(item_header("Harmonizer", new=True))
W(ul_open())
W(li("Passive: Balance. Grants 5% mana cost reduction for every hero ability off cooldown and 6% spell amplification for every spell on cooldown ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases mana cost reduction from 5% to 6.5% and spell amplification from 6% to 7.8%"))
W(ul_open())
W(li("Item spells are affected by both effects, however item cooldowns don't affect the Harmonizer buff", t("MISC")))
W(li("The buff counts only current abilities that have cooldown, even if it's passive", t("MISC")))
W(li("Invoked abilities and sub-abilities don't count when they're hidden", t("MISC")))
W(ul_close())
W(item_header("Riftshadow Prism"))
W(ul_open())
W(li("Refract health cost decreased from 10% to 8%", b(10, 8)))
W(li("Refract incoming damage decreased from 240% to 200%", b(240, 200)))
W(ul_close())
W(item_header("Spider Legs"))
W(ul_open())
W(li("Skitter: Duration increased from 10s to 14s", b(10, 14)))
W(ul_close())
W(item_header("Heavy Blade"))
W(ul_open())
W(li("Returning as a Tier 5 Neutral Artifact", t("MISC")))
W(li("Active: Cleanse. Apply basic dispel on all units in a 300 unit radius area. Cast Range: 500. Mana Cost: 150. Cooldown: 40s", t("MISC")))
W(li("Passive: Subjugate. Your attacks deal bonus magical damage equal to 4% of target's Max Mana ", t("MISC")))
W(ul_close())
W(subnote("Dormant Curio increases damage from 4% to 5.2%"))
W(plain_header("Enchantment Changes"))
W(ul_open())
W(li("Number of Enchantment choices increased from 4 to 5 for Tiers 2-5", b(4, 5)))
W(li("Enchantments are no longer randomized. Now options are based on your hero's primary attribute, with some enchantments available to all heroes", t("REWORK")))
W(ul_close())

W(subgroup("Tier 1"))
W(ul_open())
W(li("All Heroes: Quickened, Vital", t("MISC")))
W(li("Strength: Brawny, Tough", t("MISC")))
W(li("Agility: Alert, Brawny", t("MISC")))
W(li("Intelligence: Mystical, Tough", t("MISC")))
W(li("Universal: Alert, Mystical", t("MISC")))
W(ul_close())

W(subgroup("Tiers 2-3"))
W(ul_open())
W(li("All Heroes: Quickened, Greedy", t("MISC")))
W(li("Strength: Brawny, Tough, Crude", t("MISC")))
W(li("Agility: Alert, Brawny, Nimble", t("MISC")))
W(li("Intelligence: Mystical, Tough, Keen-Eyed", t("MISC")))
W(li("Universal: Alert, Mystical, Titanic", t("MISC")))
W(ul_close())

W(subgroup("Tier 4"))
W(ul_open())
W(li("All Heroes: Quickened, Timeless", t("MISC")))
W(li("Attribute-exclusive Enchantments are the same as Tiers 2-3", t("MISC")))
W(ul_close())

W(subgroup("Tier 5"))
W(ul_open())
W(li("All Heroes: Evolved, Fleetfooted, Timeless, Vampiric", t("MISC")))
W(li("Strength: Hulking", t("MISC")))
W(li("Agility: Audacious", t("MISC")))
W(li("Intelligence: Feverish", t("MISC")))
W(li("Universal: Manic", t("MISC")))
W(ul_close())
W(plain_header("Enhancement Boundless"))
W(ul_open())
W(li("Removed", t("MISC")))
W(ul_close())
W(plain_header("Enhancement Vast"))
W(ul_open())
W(li("Removed", t("MISC")))
W(ul_close())
W(plain_header("Enhancement Wise"))
W(ul_open())
W(li("Removed", t("MISC")))
W(ul_close())
W(plain_header("Enhancement Quickened"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for all heroes", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Vital"))
W(ul_open())
W(li("New guaranteed Tier 1 option for all heroes", t("MISC")))
W(li("Provides +2 Health Regen", t("MISC")))
W(ul_close())
W(plain_header("Enhancement Brawny"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Strength and Agility heroes", t("REWORK")))
W(ul_close())
W(enchant_header("Tough", "tough"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Strength and Intelligence heroes", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Alert"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Agility and Universal heroes", t("REWORK")))
W(li("Attack Speed bonus decreased from +10/17/24/31 to +7/15/23/31", b([10, 17, 24, 31], [7, 15, 23, 31])))
W(ul_close())
W(plain_header("Enhancement Mystical"))
W(ul_open())
W(li("Now is a guaranteed Tiers 1-4 option for Intelligence and Universal heroes", t("REWORK")))
W(li("No longer provides +100 Cast Range bonus at Tier 4", t("NERF")))
W(li("Now provides +15% Mana Cost/Mana Loss Reduction at Tier 4", t("REWORK")))
W(ul_close())
W(enchant_header("Greedy", "greedy"))
W(ul_open())
W(li("Now is a guaranteed option for all heroes on Tiers 2-3", t("REWORK")))
W(ul_close())
W(enchant_header("Crude", "crude"))
W(ul_open())
W(li("Now is a guaranteed option for Strength heroes only", t("REWORK")))
W(li("Tiers changed from 4/5 to 2-4", b([4, 5], 2)))
W(li("Health Restoration bonus rescaled from +30/40% to +10/15/20%", b([30, 40], [10, 15, 20])))
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(ul_open())
W(li("Base Attack Time Reduction bonus rescaled from 12/18% to 8/12/16%", b([12, 18], [8, 12, 16])))
W(li("<font color='#e03e2e'>Intelligence Penalty</font> increased from <font color='#e03e2e'>5%</font> to <font color='#e03e2e'>6%</font>", t("BUFF")))
W(ul_close())
W(plain_header("Enhancement Nimble"))
W(ul_open())
W(li("New guaranteed Tiers 2-4 option for Agility heroes only", t("MISC")))
W(li("Provides +6/8/10% Movement Speed, +10/15/20 Damage, and <font color='#e03e2e'>-1.5/2.25/3 Health Regen</font>", t("MISC")))
W(ul_close())
W(plain_header("Enhancement Keen Eyed"))
W(ul_open())
W(li("Now is a guaranteed option for Intelligence heroes only", t("REWORK")))
W(li("Tiers changed from 2/3 to 2-4", b([2, 3], 2)))
W(li("Cast Range bonus rescaled from +125/135 to +125/135/145", b([125, 135], [125, 135, 145])))
W(li("Mana Regen bonus rescaled from 1/1.5 to 1/1.5/2", b([1, 1.5], [1, 1.5, 2])))
W(li("<font color='#e03e2e'>Max Mana Penalty</font> increased from <font color='#e03e2e'>10%</font> to <font color='#e03e2e'>10/12/14%</font>", t("BUFF")))
W(ul_close())
W(plain_header("Enhancement Titanic"))
W(ul_open())
W(li("Now is a guaranteed option for Universal heroes only", t("REWORK")))
W(li("Tiers changed from 4/5 to 2-4", b([4, 5], 2)))
W(li("Attack Damage bonus rescaled from +10/20% to +8/12/16%", b([10, 20], [8, 12, 16])))
W(li("Status Resistance rescaled from 10/15% to +10/12/14%", b([10, 15], [10, 12, 14])))
W(li("Now also provides <font color='#e03e2e'>-10/12/14% Attack Speed</font>", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Timeless"))
W(ul_open())
W(li("Now is a guaranteed Tiers 4-5 option for all heroes", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Evolved"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for all heroes", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Fleetfooted"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for all heroes", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Vampiric"))
W(ul_open())
W(li("Now is a guaranteed option for all heroes", t("REWORK")))
W(li("Tiers changed from 2-4 to 5", t("MISC")))
W(li("Lifesteal bonus increased from +12/14/16% to +30%", b([12, 14, 16], 30)))
W(li("Spell Lifesteal increased from +6/8/10% to +20%", b([6, 8, 10], 20)))
W(li("Bonus Night Vision increased from +0/0/200 to +300", b([0, 0, 200], 300)))
W(ul_close())
W(plain_header("Enhancement Hulking"))
W(ul_open())
W(li("New guaranteed Tier 5 option for Strength heroes only", t("MISC")))
W(li("Provides +5% Max Health, +1.5% Max Health Regen, <font color='#e03e2e'>-30% Attack Speed</font>", t("MISC")))
W(ul_close())
W(plain_header("Enhancement Audacious"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for Agility heroes only", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Feverish"))
W(ul_open())
W(li("Now is a guaranteed Tier 5 option for Intelligence heroes only", t("REWORK")))
W(ul_close())
W(plain_header("Enhancement Manic"))
W(ul_open())
W(li("New guaranteed Tier 5 option for Universal heroes only", t("MISC")))
W(li("Provides -18% Base Attack Time, +20% Cast Speed, <font color='#e03e2e'>-20% Vision</font>", t("MISC")))
W(ul_close())
W(plain_header("Kobold Taskmaster"))
W(ul_open())
W(li("Damage increased from 22–24 to 24–26", t("BUFF")))
W(ul_close())
W(plain_header("Kobold Tunneler"))
W(ul_open())
W(li("Damage increased from 20–21 to 22–23", t("BUFF")))
W(ul_close())
W(plain_header("Kobold"))
W(ul_open())
W(li("Damage increased from 13–14 to 15–16", t("BUFF")))
W(ul_close())
W(plain_header("Gnoll Assassin"))
W(ul_open())
W(li("Damage decreased from 30–32 to 25–27", t("NERF")))
W(ul_close())
W(plain_header("Ghost"))
W(ul_open())
W(li("Damage decreased from 45–50 to 38–43", t("NERF")))
W(ul_close())
W(plain_header("Harpy Storm"))
W(ul_open())
W(li("Chain Lightning: Damage rescaled from 140/180/220/260 to 120/170/220/270", b([140, 180, 220, 260], [120, 170, 220, 270])))
W(ul_close())
W(plain_header("Satyr Hellcaller"))
W(ul_open())
W(li("Shockwave: Damage rescaled from 160 to 140/160/180/200", b(160, [140, 160, 180, 200])))
W(ul_close())
W(plain_header("Warpine Raider"))
W(ul_open())
W(li("Seed Shot: Damage rescaled from 100 to 80/95/110/125", b(100, [80, 95, 110, 125])))
W(ul_close())
W(plain_header("Froglet"))
W(ul_open())
W(li("Arm of the Deep: After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown ", t("MISC")))
W(li("Previously affected other copies of this ability", t("MISC")))
W(ul_close())
W(plain_header("Grown Frog"))
W(ul_open())
W(li("Tendrils of the Deep: After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown ", t("MISC")))
W(li("Previously affected other copies of this ability", t("MISC")))
W(ul_close())
W(plain_header("Ancient Frog"))
W(ul_open())
W(li("Congregations of the Deep: After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown ", t("MISC")))
W(li("Previously affected other copies of this ability", t("MISC")))
W(li("Congregations of the Deep: Radius is now affected by Area of Effect bonuses", t("REWORK")))
W(ul_close())
W(plain_header("Ancient Frog Mage"))
W(ul_open())
W(li("Water Bubble (Large): Radius is now affected by Area of Effect bonuses", t("REWORK")))
W(ul_close())

# ===== HERO UPDATES =====
W(section("Hero Updates"))


# Abaddon
W(hero_header("Abaddon"))
W(ability("Withering Mist"))
W(ul_open())
W(li("Health Restoration Reduction changed from 35% to 24.5% + 0.5% per level", b(35, 24.5)))
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(ability("Death Coil"))
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
W(ability("Greevil's Greed"))
W(ul_open())
W(li("Aghanim's Scepter now also increases Base Bonus Gold and Max Bonus Gold per kill by 6 per melted Aghanim's Scepter", t("REWORK")))
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
W(ul_open())
W(li("Removed Death Rime innate ability", t("MISC")))
W(ul_close())
W(ability("Bone Chill"))
W(ul_open())
W(li("New innate ability. Passive, improves with Ancient Apparition's level", t("MISC")))
W(li("When Ancient Apparition deals magic damage with his abilities, affected enemies are chilled for 4s, reducing their movespeed by 2% per stack. If the target is an enemy hero, debuff also reduces their Strength by 0.1 + 0.1 per 3 levels. Each instance stacks and has independent duration", t("MISC")))
W(li("Upgraded with Aghanim's Scepter", t("MISC")))
W(li("Increases Base Strength Reduction by 0.3", t("MISC")))
W(ul_close())
W(ability("Cold Feet"))
W(ul_open())
W(li("Now deals 20/40/60/80 damage per second", t("REWORK")))
W(ul_close())
W(ability("Ice Vortex"))
W(ul_open())
W(li("Now deals 10/20/30/40 damage per second", t("REWORK")))
W(li("Now slows movement by 8%", t("REWORK")))
W(ul_close())
W(ability("Chilling Touch"))
W(ul_open())
W(li("Mana Cost decreased from 45/50/55/60 to 35", b([45, 50, 55, 60], 35, l=True)))
W(li("Aghanim's Scepter no longer reduces mana cost", t("NERF")))
W(ul_close())
W(ability("Ice Blast"))
W(ul_open())
W(li("Now deals 12/24/36 damage per second", t("REWORK")))
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
W(li("Base Armor increased by 1", bstat_h("Anti-Mage", "ArmorPhysical", "7.40c", 1), extra=note_box("From 1 to 2")))
W(ul_close())
W(ability("Persecutor"))
W(ul_open())
W(li("No longer levels with Mana Void", t("NERF")))
W(li("Min Movement Slow rescaled from 12.5/15/17.5/20% to 12% + 0.5% per level", b([12.5, 15, 17.5, 20], 12)))
W(li("Max Movement Slow rescaled from 25/30/35/40% to 24% + 1% per level", b([25, 30, 35, 40], 24)))
W(ul_close())
W(ability("Mana Break"))
W(ul_open())
W(li("Effectiveness when applied by illusions decreased from 50% to 25%", b(50, 25)))
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Increases Max Mana Burned per hit by an additional 1.5%", t("MISC")))
W(ul_close())
W(ability("Blink"))
W(ul_open())
W(li("Cast Range rescaled from 750/900/1050/1200 to 875/950/1025/1100", b([750, 900, 1050, 1200], [875, 950, 1025, 1100])))
W(li("Cooldown decreased from 12/10/8/6s to 10.5/9/7.5/6s", b([12, 10, 8, 6], [10.5, 9, 7.5, 6], l=True)))
W(li("Mana Cost increased from 50 to 65/60/55/50", b(50, [65, 60, 55, 50], l=True)))
W(li("Aghanim's Scepter no longer decreases cooldown by 1s", t("NERF")))
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
W(li("Damage gain per level decreased from 3.6 to 3.4", b(3.6, 3.4)))
W(li("Base Movement Speed increased from 285 to 300", b(285, 300)))
W(ul_close())
W(ability("Runic Infusion"))
W(ul_open())
W(li("No longer grants the Regeneration Rune buff upon activating any rune", t("NERF")))
W(li("Now provides Arc Warden with +1.5 all attributes permanently whenever Arc Warden or the Tempest Double activates a Power Rune", t("REWORK")))
W(ul_close())
W(ability("Magnetic Field"))
W(ul_open())
W(li("The field now also pulls runes, and automatically activates ones that are inside. Rune Pull Force: 100. Rune Pull Radius: 800/1200/1600/2000", t("REWORK")))
W(ul_close())
W(ability("Spark Wraith"))
W(ul_open())
W(li("Slow Duration increased from 0.5/0.6/0.7/0.8s to 0.7/0.8/0.9/1s", b([0.5, 0.6, 0.7, 0.8], [0.7, 0.8, 0.9, 1])))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Tempest Double"))
W(ul_open())
W(li("Gold and XP Bounty rescaled from 180/240/300 to 70 + 10 per level", b([180, 240, 300], 70)))
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("The Tempest Double is infused with the bonuses of Arcane, Invisibility, and Haste Runes for 12s. These bonuses don't provide Runic Infusion stacks", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +50% Spark Wraith Damage replaced with +200 Spark Wraith Damage", t("REWORK")))
W(li("Level 25 Talent -1.1s Spark Wraith Activation Delay replaced with +30s Spark Wraith Duration", t("REWORK")))
W(li("Level 25 Talent Tempest Double Has No Penalties replaced with +1.5 Runic Infusion All Attributes Bonus (applies retroactively)", t("REWORK")))
W(ul_close())

# Axe
W(hero_header("Axe"))
W(ul_open())
W(li("Removed Coat of Blood innate ability", t("MISC")))
W(ul_close())
W(ability("One Man Army"))
W(ul_open())
W(li("Now Axe's innate ability", t("REWORK")))
W(li("Increases Axe's Strength by 50% of his armor, as long as there are no allied heroes within a 700 radius of him. The effect fades over 3s after an ally walks within range", t("MISC")))
W(ul_close())
W(ability("Culling Blade"))
W(ul_open())
W(li("Now each hero kill made with Culling Blade provides a permanent stack, which provides 1/1.5/2 armor depending on the current level of Culling Blade", t("REWORK")))
W(ul_close())

# Bane
W(hero_header("Bane"))
W(ul_open())
W(li("Strength gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
W(li("Agility gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
W(li("Intelligence gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
W(li("Damage gain per level decreased from 3.6 to 3.4", b(3.6, 3.4)))
W(li("Attack Range increased from 400 to 425", b(400, 425)))
W(ul_close())
W(ability("Ichor Of Nyctasha"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("Every time Bane kills an enemy hero or they die under the effect of any debuff applied by Bane, they receive a Terror for the rest of the game. Each Terror stack decreases the enemy's status resistance to all Bane's debuffs by 5%. Max Terror stacks per hero: 5", t("MISC")))
W(ul_close())
W(ability("Nightmare"))
W(ul_open())
W(li("Now a Unit Vector Target Spell", t("REWORK")))
W(li("Sleeping units walk in Bane's chosen direction at a speed of 110", t("MISC")))
W(li("Can be put on alt-cast to disable sleepwalking behavior", t("MISC")))
W(ul_close())

# Batrider
W(hero_header("Batrider"))
W(ability("Firefly"))
W(ul_open())
W(li("Now also provides an increasing movement speed bonus that reaches its maximum of 12/18/24/30% at the end of Firefly's duration", t("REWORK")))
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
W(ul_open())
W(li("Removed Rugged innate ability", t("MISC")))
W(ul_close())
W(ability("Inner Beast"))
W(ul_open())
W(li("Now an innate ability", t("REWORK")))
W(li("Bonus Attack Speed changed from 10/30/50/70 to 7 + 3 per level", b([10, 30, 50, 70], 7)))
W(ul_close())
W(ability("Wild Axes"))
W(ul_open())
W(li("Damage per axe increased from 30/65/100/135 to 40/80/120/160", b([30, 65, 100, 135], [40, 80, 120, 160])))
W(li("Damage Amp per stack decreased from 6/9/11/13% to 5/6/7/8%", b([6, 9, 11, 13], [5, 6, 7, 8])))
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Beastmaster's attacks on enemy heroes also apply the Wild Axes debuff of its corresponding level", t("MISC")))
W(li("Illusions of Beastmaster don't apply Wild Axes stacks", t("MISC")))
W(ul_close())
W(ability("Summon Razorback"))
W(ul_open())
W(li("Call of the Wild Boar renamed to Summon Razorback", t("MISC")))
W(li("Boar's armor increased by 1", t("BUFF")))
W(li("Boar Attack Damage increased from 25/40/55/70 to 30/45/60/75", b([25, 40, 55, 70], [30, 45, 60, 75])))
W(ul_close())
W(ability("Summon Raptor"))
W(ul_open())
W(li("Call of the Wild Hawk renamed to Summon Raptors", t("MISC")))
W(li("Now is a separately leveled ability", t("REWORK")))
W(li("Hawk's armor increased by 1", t("BUFF")))
W(li("Cooldown decreased from 45/40/35/30s to 30s", b([45, 40, 35, 30], 30, l=True)))
W(li("Dive Damage increased from 50/80/110/140 to 60/95/130/165", b([50, 80, 110, 140], [60, 95, 130, 165])))
W(li("Root Duration increased from 0.25/0.5/0.75/1s to 0.4/0.6/0.8/1s", b([0.25, 0.5, 0.75, 1], [0.4, 0.6, 0.8, 1])))
W(li("Hawks are now invisible whenever Beastmaster is invisible or affected by Smoke of Deceit. They do not attack while invisible", t("REWORK")))
W(li("Now summons 2 hawks by default with 0.75s delay between them", t("REWORK")))
W(li("Hawks will now prioritize Beastmaster's current attack target when selecting their Dive target", t("REWORK")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
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
W(li("Max Health Heal changed from 1.5% + 1.5% per level up to 1.5% per level ", t("MISC")))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Bloodrage"))
W(ul_open())
W(li("Now a no target ability that affects only Bloodseeker", t("REWORK")))
W(li("Pure damage based on target's max health with Aghanim's Shard now pierces Debuff Immunity", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Blood Rite Silence Duration increased from +2.5s to +3s", b(2.5, 3)))
W(ul_close())

# Bounty Hunter
W(hero_header("Bounty Hunter"))
W(ability("Big Game Hunter"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("Bounty Hunter receives 15% more kill and assist gold if the dying enemy hero is Big Game. An enemy hero is considered Big Game if they are one of the top 3 net worth heroes on the enemy team", t("MISC")))
W(li("Bounty Hunter has a list of heroes that are currently considered a big game, accessible by pressing special button over the innate", t("MISC")))
W(li("These heroes will also have a debuff, that points out that they're among these three heroes. Debuff is visible only to Bounty Hunter and his allies", t("MISC")))
W(ul_close())
W(ability("Jinada"))
W(ul_open())
W(li("Gold Steal increased from 12/20/28/36 to 15/22/29/36", b([12, 20, 28, 36], [15, 22, 29, 36])))
W(ul_close())
W(ability("Shadow Walk"))
W(ul_open())
W(li("Now grants 8/12/16/20% bonus movement speed when active", t("REWORK")))
W(li("Also applies to Friendly Shadow", t("MISC")))
W(ul_close())
W(ability("Track"))
W(ul_open())
W(li("No longer grants 12/16/20% bonus movement speed to Bounty Hunter", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Damage increased from +25 to +30", b(25, 30)))
W(ul_close())

# Brewmaster
W(hero_header("Brewmaster"))
W(ability("Liquid Courage"))
W(ul_open())
W(li("Max Status Resist changed from 10.5% + 0.5% per level up to 10% + 0.5% per level ", t("MISC")))
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
W(li("Damage and debuff duration amplification changed from 10% to 4.5% + 0.5% per level", b(10, 4.5)))
W(ul_close())
W(ability("Viscous Nasal Goo"))
W(ul_open())
W(li("Stack Limit increased from 4 to 6", b(4, 6)))
W(li("Now has the same duration on all units", t("REWORK")))
W(li("Used to have double duration on creeps", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +12% Spell Lifesteal replaced with -25 Bristleback Damage Threshold", t("REWORK")))
W(ul_close())

# Broodmother
W(hero_header("Broodmother"))
W(ability("Spiders Milk"))
W(ul_open())
W(li("Hero Health as Heal changed from 2% to 1.9% + 0.1% per level", b(2, 1.9)))
W(ul_close())
W(ability("Insatiable Hunger"))
W(ul_open())
W(li("Now also applies lifesteal to Spiderlings within 800 range of Broodmother", t("REWORK")))
W(ul_close())
W(ability("Spin Web"))
W(ul_open())
W(li("Movespeed Bonus decreased from 10/22/34/46% to 10/20/30/40%", b([10, 22, 34, 46], [10, 20, 30, 40])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Spiderlings Health increased from +150 to +175", b(150, 175)))
W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +6 to +5", b(6, 5)))
W(li("Level 25 Talent -0.15s BAT during Insatiable Hunger now also affects Spiderlings within 800 range", t("REWORK")))
W(ul_close())

# Centaur Warrunner
W(hero_header("Centaur Warrunner"))
W(ul_open())
W(li("Strength gain increased from 4.0 to 4.2", b(4.0, 4.2)))
W(li("Removed Rawhide innate ability", t("MISC")))
W(ul_close())
W(ability("Horsepower"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Centaur Warrunner gains 30% of his strength as bonus movement speed. This movement speed bonus does not stack with bonuses from boots", t("MISC")))
W(ul_close())

# Chaos Knight
W(hero_header("Chaos Knight"))
W(ul_open())
W(li("Removed Reins of Chaos innate ability", t("MISC")))
W(ul_close())
W(ability("Fundamental Forging"))
W(ul_open())
W(li("New reworked innate ability. Passive", t("MISC")))
W(li("When Chaos Knight crafts a neutral item, it gets an additional random enchantment that doesn't provide negative stats", t("MISC")))
W(li("The random enchantment is selected from all available enchantments in that tier, including ones that are normally not available for Strength heroes", t("MISC")))
W(li("Due to negative stats, Chaos Knight can't randomly get Crude, Nimble, Keen-Eyed, Titanic, Greedy, Hulking, Audacious, Feverish, and Manic Enchantments", t("NERF")))
W(li("The random enchantment is different from the one used in crafting", t("MISC")))
W(ul_close())
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
W(li("Aghanim's Scepter no longer guarantees to create an additional illusion on cast", t("NERF")))
W(li("Aghanim's Scepter now provides a passive component to this ability", t("REWORK")))
W(li("Whenever an illusion of Chaos Knight is created, there is a 50% chance to create an additional illusion under Chaos Knight's control", t("MISC")))
W(li("Bonus illusion will be under Chaos Knight's control even if other illusions were made by an enemy", t("MISC")))
W(ul_close())

# Chen
W(hero_header("Chen"))
W(ul_open())
W(li("Removed Summon Convert innate ability", t("MISC")))
W(ul_close())
W(ability("Zealot"))
W(ul_open())
W(li("New innate ability, has both passive and active components. Improves with game's time", t("MISC")))
W(li("When Chen respawns, he is joined in battle by a Zealot, a melee creep warrior with the Martyrdom ability which allows him to sacrifice himself to deal damage or heal an ally. Zealot has the same stats as the current melee creeps on his team, including super or mega form, but has 125 attack range, base damage increased by 2 per Chen's level, base health regen increased from 0.5 to 2.5, and doesn't have Runty attack type. Zealot respawns after 60s dead", b(0.5, 2.5)))
W(li("Martyrdom ability: 500 range unit-targeted ability on the Zealot creep, targeting either an enemy or ally unit. When cast, the creep sacrifices itself, firing a projectile at 1000 speed at the target unit, dealing damage if it's an enemy or healing if it's an ally. Damage is 25 + 20% of the Zealot's health at the moment of the cast, and healing is 50% of these values", t("MISC")))
W(li("This ability can be cast on a controlled unit to teleport it to Chen after a 6 second delay. Self-targeting will teleport all controlled units. Mana Cost: 50. Cooldown: 10s", t("MISC")))
W(li("Mechanics moved from Divine Favor without any changes", t("MISC")))
W(ul_close())
W(ability("Holy Persuasion"))
W(ul_open())
W(li("Zealots receive the benefits from Holy Persuasion", t("MISC")))
W(li("Now may be cast on existing persuaded creeps that have not been damaged in the last 3 seconds to unsummon them", t("REWORK")))
W(li("Unsummoning a unit has a global cast range, costs no mana and sets ability to a 3s cooldown", t("MISC")))
W(li("Now increases all of creature's outgoing damage by 0/6/12/18% instead of only increasing attack damage by 4/8/12/16", t("REWORK")))
W(ul_close())
W(ability("Divine Favor"))
W(ul_open())
W(li("Self-casting no longer teleports Chen's creeps to him ", t("NERF")))
W(ul_close())
W(subnote("Still applies the Divine Favor buff to all of them"))
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
W(ability("Armor Power"))
W(ul_open())
W(li("Now also allows Clockwerk to consume Chainmails to gain +4 armor per Chainmail consumed", t("REWORK")))
W(ul_close())
W(ability("Battery Assault"))
W(ul_open())
W(li("Mana Cost decreased from 90 to 75/80/85/90", b(90, [75, 80, 85, 90], l=True)))
W(ul_close())
W(ability("Power Cogs"))
W(ul_open())
W(li("Clockwerk can now move freely through the cogs, sinking them down while walking over them. Other units can also walk over sunken Power Cogs", t("REWORK")))
W(li("Mana Cost rescaled from 70 to 60/65/70/75", b(70, [60, 65, 70, 75], l=True)))
W(li("Mana Burn increased from 35/70/105/140 to 35/75/115/155", b([35, 70, 105, 140], [35, 75, 115, 155])))
W(ul_close())
W(ability("Overclocking"))
W(ul_open())
W(li("Duration increased from 13s to 18s", b(13, 18)))
W(li("Now also increases Battery Assault radius to 330", t("REWORK")))
W(li("Now also increases Power Cogs radius to 330 and provides 25% bonus armor to Clockwerk while he is near cogs", t("REWORK")))
W(li("No longer increases Clockwerk's attack speed while inside Power Cogs", t("NERF")))
W(li("Now increases Rocket Flare damage, vision and slow duration by 35%", t("REWORK")))
W(li("No longer decreases Rocket Flare cooldown to 3.5s", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.4s Rocket Flare Slow Duration replaced with +1.5 Mana Regen", t("REWORK")))
W(li("Level 15 Talent +2 Power Cogs Hits To Kill replaced with -10s Hookshot Cooldown", t("REWORK")))
W(li("Level 25 Talent Debuff Immunity Inside Power Cogs replaced with 3 Rocket Flare Charges", t("REWORK")))
W(ul_close())

# Crystal Maiden
W(hero_header("Crystal Maiden"))
W(ul_open())
W(li("Removed Blueheart Floe innate ability", t("MISC")))
W(ul_close())
W(ability("Glacial Guard"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("A portion of the mana Crystal Maiden spends on her abilities is converted into a physical barrier for 8s. Barriers stack, but each instance has independent duration", t("MISC")))
W(li("Mana Spent to Barrier is 30% + 2% per level", t("MISC")))
W(ul_close())
W(ability("Brilliance Aura"))
W(ul_open())
W(li("Now also passively provides Crystal Maiden with 20/40/60/80% mana regen amplification", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +225 Attack Speed replaced with +20% Glacial Guard Mana Spent To Barrier", t("REWORK")))
W(ul_close())

# Dark Seer
W(hero_header("Dark Seer"))
W(ability("Aggrandize"))
W(ul_open())
W(li("Aggrandize renamed to Quick Wit", t("MISC")))
W(li("Now also provides Dark Seer +1 attack speed from each point of Intelligence", t("REWORK")))
W(li("Max Health and Mana Restore base value decreased from 10% to 8.5%", b(10, 8.5)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Ion Shell Provides +250 Max Health replaced with -1.5s Surge Cooldown", t("REWORK")))
W(ul_close())

# Dark Willow
W(hero_header("Dark Willow"))
W(ability("Pixie Dust"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("Dark Willow's Health Regen and Mana Regen always have 20% Amplification, which increases to 100% whenever she becomes untargetable or invulnerable", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Intelligence increased from +10 to +12", b(10, 12)))
W(li("Level 15 Talent Terrorize Cooldown Reduction increased from 15s to 20s", b(15, 20, l=True)))
W(ul_close())

# Dawnbreaker
W(hero_header("Dawnbreaker"))
W(ul_open())
W(li("Base damage increased by 6", bstat_h("Dawnbreaker", "AttackDamageMin", "7.40c", 6), extra=note_box("From 27 to 33")))
W(li("Damage at level 1 increased from 50–54 to 56–60", t("BUFF")))
W(ul_close())
W(ability("Break of Dawn"))
W(ul_open())
W(li("Max Damage Increase changed from 25% to 10% + 1% per level", b(25, 10)))
W(li("Bonuses granted are now at their maximum for any daytime caused by Dawnbreaker's abilities for the entirety of that daytime", t("REWORK")))
W(li("Now also upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Amplifies heals Dawnbreaker provides by Break of Dawn's current damage increase value", t("MISC")))
W(ul_close())
W(ability("Solar Guardian"))
W(ul_open())
W(li("Cooldown decreased from 120/105/90s to 110/100/90s", b([120, 105, 90], [110, 100, 90], l=True)))
W(li("Now causes a 6 second temporary daytime when the cast starts", t("REWORK")))
W(li("Aghanim's Scepter no longer increases heal per pulse", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +15% Celestial Hammer Slow replaced with Celestial Hammer Trail Grants Movement Speed to Allies", t("REWORK")))
W(li("Level 10 Talent +15% Break of Dawn Max Damage replaced with +25% Luminosity Critical Strike Damage", t("REWORK")))
W(li("Level 15 Talent Solar Guardian Cooldown Reduction increased from 15s to 20s", b(15, 20, l=True)))
W(li("Level 15 Talent +40% Luminosity Critical Strike Damage replaced with +40% Celestial Hammer Trail/Hammer Damage", t("REWORK")))
W(ul_close())

# Dazzle
W(hero_header("Dazzle"))
W(ability("Innate Weave"))
W(ul_open())
W(li("No longer levels with Nothl Projection", t("NERF")))
W(li("Armor Change per stack rescaled from 0.5/0.75/1/1.25 to 1", b([0.5, 0.75, 1, 1.25], 1)))
W(li("Duration changed from 8s to 6.9s + 0.1s per level", b(8, 6.9)))
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Applying a stack of Weave on an ally heals them for 60 per stack of Weave, including the stack that was just applied", t("MISC")))
W(ul_close())
W(ability("Nothl Projection"))
W(ul_open())
W(li("No longer does a hard dispel on Dazzle when projection ends", t("NERF")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())

# Death Prophet
W(hero_header("Death Prophet"))
W(ul_open())
W(li("Base Armor increased by 1", bstat_h("Death Prophet", "ArmorPhysical", "7.40c", 1), extra=note_box("From 0 to 1")))
W(ul_close())
W(ability("Witchcraft"))
W(ul_open())
W(li("Movement speed bonus changed from 0.75% + 0.75% per level up to 0.5% + 0.75% per level", t("MISC")))
W(li("Cooldown Reduction changed from 0.75% + 0.75% per level up to 0.75% per level ", t("MISC")))
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
W(li("Now deals damage equal to 1.5x of Disruptor's Intelligence", t("REWORK")))
W(ul_close())
W(ability("Thunder Strike"))
W(ul_open())
W(li("Strike Damage increased from 25/55/85/115 to 30/60/90/120", b([25, 55, 85, 115], [30, 60, 90, 120])))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Kinetic Fence"))
W(ul_open())
W(li("Now granted by Aghanim's Shard", t("REWORK")))
W(li("No longer shares level with Kinetic Field. Has only one level instead", t("NERF")))
W(li("Cast Range increased from 1050 to 1200", b(1050, 1200)))
W(li("Cooldown decreased from 20/18/16/14s to 14s", b([20, 18, 16, 14], 14, l=True)))
W(li("Duration increased from 2.6/3.2/3.8/4.4s to 4.4s", b([2.6, 3.2, 3.8, 4.4], 4.4)))
W(li("Can be increased with Kinetic Field Duration talent", t("BUFF")))
W(li("Formation Delay increased from 0.4s to 1s", b(0.4, 1)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +10%/300 Glimpse Distance To Damage/Max increased to +15%/300", t("BUFF")))
W(li("Level 20 Talent +150 Electromagnetic Repulsion Radius/Knockback replaced with +75 Static Storm Radius", t("REWORK")))
W(li("Level 25 Talent +150 Static Storm Radius replaced with +6 Thunder Strike Strikes (also decreases Strike Interval by 50%) ", t("REWORK")))
W(li("As a result, increases overall duration from 6s to 9s", b(6, 9)))
W(li("Level 25 Talent -12s Glimpse Cooldown replaced with 2 Glimpse Charges", t("REWORK")))
W(ul_close())

# Doom
W(hero_header("Doom"))
W(ability("Lvl Pain"))
W(ul_open())
W(li("Ability slightly reworked", t("MISC")))
W(li("When Doom attacks enemy heroes, he applies a curse upon them. After 2.5s, the cursed hero bursts with a pillar of fire, damaging itself and all enemy units in a 66 AoE for 15% of the damage taken from Doom (the hero) over this duration, including damage from the attack that applied the curse. If the cursed hero's level is a multiple of 6, the curse damage and radius will be increased by 66%", t("BUFF")))
W(ul_close())
W(ability("Devour"))
W(ul_open())
W(li("Now the default cast gained on learning Devour is the one that grants abilities of devoured creeps, and alt-cast state keeps the ones that Doom currently has", t("REWORK")))
W(li("Cooldown decreased from 70s to 66s", b(70, 66, l=True)))
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Replaces cooldown with 2 charges with 66s restore time. Allows to devour Ancient Neutral Creeps. Gained spells also have 20% bonus AoE and 40% Spell Amplification", t("MISC")))
W(ul_close())
W(ability("Scorched Earth"))
W(ul_open())
W(li("Radius increased from 600 to 666", b(600, 666)))
W(li("Now also provides Doom with 7/8/9/10 bonus health regen", t("REWORK")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Infernal Blade"))
W(ul_open())
W(li("Stun Duration increased from 0.6s to 0.66s", b(0.6, 0.66)))
W(ul_close())
W(ability("Doom"))
W(ul_open())
W(li("Damage per second increased from 25/45/65 to 25/45/66", b([25, 45, 65], [25, 45, 66])))
W(li("Aghanim's Scepter now also applies Break to affected enemies", t("REWORK")))
W(li("Aghanim's Scepter no longer increases damage per second by 15", t("NERF")))
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
W(li("Fixed the cast indicator not matching the actual damage range of the ability, and also to properly reflect cast range bonuses", t("MISC")))
W(ul_close())
W(ability("Dragon Tail"))
W(ul_open())
W(li("No longer has an Elder Dragon specific cast range", t("NERF")))
W(li("Now has 25 radius AoE by default", t("REWORK")))
W(ul_close())
W(ability("Wyrms Wrath"))
W(ul_open())
W(li("Now always grants the 10/20/30/40 bonus magic damage on attack, and 25/50/75/100 Area of Effect bonus", t("REWORK")))
W(ul_close())
W(ability("Elder Dragon Form"))
W(ul_open())
W(li("Now evolves per level. The bonuses are cumulative", t("REWORK")))
W(li("Level 1: Green Dragon: Attacks apply a Corrosive poison that deals 25 magical damage per second for 3 seconds. Affects buildings", t("MISC")))
W(li("Level 2: Red Dragon: Attacks have splash damage that deals 75% of attack damage to all enemies within 275 AoE range", t("MISC")))
W(li("Applies Corrosive poison to all affected units. Other attack modifiers will affect only the primary target", t("MISC")))
W(li("Level 3: Blue Dragon: Attacks also apply a Frost debuff, which pierces Debuff Immunity and slows attack by 50 and movement by 30%", t("MISC")))
W(li("Splash attacks apply Corrosive poison and Frost slow to all affected units. Other attack modifiers will affect only the primary target", t("MISC")))
W(li("Bonus Move Speed increased from 20 to 25/30/35", b(20, [25, 30, 35])))
W(li("No longer provides bonus attack damage", t("NERF")))
W(li("Now also increases cast range of all abilities by 350 ", t("REWORK")))
W(ul_close())
W(subnote("Doesn't affect items"))
W(ul_open())
W(li("Aghanim's Scepter no longer improves Wyrm's Wrath effectiveness while in Dragon Form", t("NERF")))
W(li("Aghanim's Scepter Black Dragon stats slightly rescaled", t("REWORK")))
W(li("Level 4 Black Dragon has the following stats: 40 Bonus Move Speed, 35 Corrosive Damage, 100% Splash Damage, 350 Splash Radius, 65 Attack Slow, 45% Movement Slow, and also provides +20% Magic Resistance and free pathing", t("MISC")))
W(ul_close())
W(ability("Fireball"))
W(ul_open())
W(li("No longer has an Elder Dragon specific cast range", t("NERF")))
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
W(li("Base Damage decreased by 2", bstat_h("Drow Ranger", "AttackDamageMin", "7.40c", -2), extra=note_box("From 32.5 to 30.5")))
W(li("Damage at level 1 decreased from 51–58 to 49–56", t("NERF")))
W(ul_close())
W(ability("Trueshot"))
W(ul_open())
W(li("No longer levels with Marksmanship", t("NERF")))
W(li("Agility Base Bonus rescaled from 4/8/12/16% to 10%", b([4, 8, 12, 16], 10)))
W(ul_close())
W(ability("Frost Arrows"))
W(ul_open())
W(li("Now also modifies incoming healing with Aghanim's Scepter ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))
W(ability("Gust"))
W(ul_open())
W(li("Knockback duration now scales inversely with distance from the target, similar to knockback distance. Minimum knockback duration is 0.4 seconds", t("REWORK")))
W(ul_close())
W(ability("Multishot"))
W(ul_open())
W(li("Now allows Drow Ranger to move with a 35% penalty and use items while casting Multishot", t("REWORK")))
W(ul_close())
W(ability("Glacier"))
W(ul_open())
W(li("No longer increases the number of Multishot arrows", t("NERF")))
W(li("No longer grants True Strike on the hill", t("NERF")))
W(li("Now Drow Ranger deals 25% more damage when attacking from high ground while on the Glacier", t("REWORK")))
W(ul_close())

# Earth Spirit
W(hero_header("Earth Spirit"))
W(ability("Stone Caller"))
W(ul_open())
W(li("Max Charges changed from 7 + 1 per 4 level ups to 7 + 1 per 4 levels ", t("MISC")))
W(ul_close())
W(subnote("This means bonus charges are gained 1 level earlier (on levels 4/8/12... instead of 5/9/13...)"))
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
W(li("No longer levels with Echo Slam", t("NERF")))
W(li("Damage (Creep Death) changed from 30/45/60/75 to 27 + 3 per level", b([30, 45, 60, 75], 27)))
W(li("Damage (Hero Death) changed from 150/250/350/450 to 135 + 15 per level", b([150, 250, 350, 450], 135)))
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
W(ul_open())
W(li("Removed Tip The Scales innate ability", t("MISC")))
W(ul_close())
W(ability("Momentum"))
W(ul_open())
W(li("New innate ability. Passive, can't be leveled up", t("NERF")))
W(li("Elder Titan's armor increases by 3.6% + 0.4% per level of his bonus movement speed", t("MISC")))
W(li("Only counts movement speed that he has above his base (305) value", t("MISC")))
W(li("This ability can't reduce Elder Titan's armor when he is slowed below the base movement speed value", t("NERF")))
W(ul_close())
W(ability("Ancestral Spirit"))
W(ul_open())
W(li("No longer provides armor on return", t("NERF")))
W(li("Still grants movement speed, which is then used by the innate ability to provide armor", t("MISC")))
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
W(li("No longer levels with Fire Remnant", t("NERF")))
W(li("Damage per second changed from 10/18/26/34 to 10 + 1 per level", b([10, 18, 26, 34], 10)))
W(li("Radius increased from 175 to 200", b(175, 200)))
W(li("Aghanim's Shard bonus radius decreased from 175 to 150 ", b(175, 150)))
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
W(ability("Rabblerouser"))
W(ul_open())
W(li("Damage Increase changed from 4% + 4% per level up to 4% per level ", t("MISC")))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Enchant"))
W(ul_open())
W(li("Cast Range increased from 500/550/600/650 to 500/600/700/800", b([500, 550, 600, 650], [500, 600, 700, 800])))
W(li("Now enchanting enemy heroes increases attack range against them by 50/100/150/200 for Enchantress and units under her control", t("REWORK")))
W(ul_close())
W(ability("Natures Attendants"))
W(ul_open())
W(li("Added a tooltip to display the total max possible heal", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Untouchable Attack Slow increased from +70 to +80", b(70, 80)))
W(ul_close())

# Enigma
W(hero_header("Enigma"))
W(ul_open())
W(li("Removed Gravity Well innate ability", t("MISC")))
W(ul_close())
W(ability("Event Horizon"))
W(ul_open())
W(li("New innate ability. Passive, improves with Enigma's level", t("MISC")))
W(li("Units in a 600 radius moving away from Enigma have a movespeed penalty equal to 4% + 1% per level", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +60 Malefice Instance Damage replaced with +100 Event Horizon Radius", t("REWORK")))
W(ul_close())

# Faceless Void
W(hero_header("Faceless Void"))
W(ability("Distortion Field"))
W(ul_open())
W(li("No longer levels with Chronosphere", t("NERF")))
W(li("Now only applies to projectiles targeting Faceless Void or an allied hero within a 1200 radius of him", t("REWORK")))
W(li("Max slow distance rescaled from 600 around Faceless Void to 500 around the targeted hero", t("REWORK")))
W(li("Enemy attack projectile speed slow rescaled from 35/40/45/50% to 40%", b([35, 40, 45, 50], 40)))
W(ul_close())
W(ability("Time Walk"))
W(ul_open())
W(li("Aghanim's Scepter now also provides Reverse Time Walk sub-ability", t("REWORK")))
W(li("Aghanim's Scepter Time Lock attacks will no longer miss if Reverse Time Walk is used too quickly after Time Walk", t("NERF")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Time Dilation"))
W(ul_open())
W(li("Duration no longer counts down while under effect of Chronosphere", t("NERF")))
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Increases Attack/Movement Slow per cooldown by 5/5%. Provides Faceless Void with bonus movement and attack speed by the same values per each enemy cooldown extended. The bonus degrades over the duration of the buff", t("MISC")))
W(li("9/10/11/12 Attack Speed + the same value per affected cooldown, 9/10/11/12% Movement Speed + the same value per affected cooldown", t("MISC")))
W(li("This buff also doesn't count down under effect of Chronosphere", t("MISC")))
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
W(li("Now also applied when an enemy hero is affected by any of Grimstroke's abilities", t("REWORK")))
W(li("Now also applied by attacks from Grimstroke's illusions (including Dark Portrait)", t("REWORK")))
W(li("Grimstroke now takes 5% + 0.5% per level less damage from enemies affected by Ink Trail", t("REWORK")))
W(ul_close())
W(ability("Dark Artistry"))
W(ul_open())
W(li("Can now be put on alt-cast to send the stroke straight", t("REWORK")))
W(ul_close())

# Gyrocopter
W(hero_header("Gyrocopter"))
W(ul_open())
W(li("Base Movement Speed decreased from 320 to 315", b(320, 315)))
W(li("Removed Chop Shop innate ability", t("MISC")))
W(ul_close())
W(ability("Afterburner"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Whenever Gyrocopter damages an enemy with attacks or abilities, he gains + 1 movement speed per hero and + 0.5 per creep. Duration is 3.9s + 0.1s per level. Effects stack independently", t("MISC")))
W(ul_close())
W(ability("Flak Cannon"))
W(ul_open())
W(li("Aghanim's Scepter upgrade moved into a separate ability", t("MISC")))
W(ul_close())
W(ability("Side Gunner Spawn Ability"))
W(ul_open())
W(li("New ability granted by Aghanim's Scepter, effect is unchanged", t("MISC")))
W(ul_close())

# Hoodwink
W(hero_header("Hoodwink"))
W(ability("Mistwoods Wayfarer"))
W(ul_open())
W(li("No longer levels with Sharpshooter", t("NERF")))
W(li("Redirect Chance changed from 14/21/28/35% to 14% + 1% per level", b([14, 21, 28, 35], 14)))
W(ul_close())
W(ability("Acorn Shot"))
W(ul_open())
W(li("Cast Range rescaled from (Hoodwink's attack range + 100) to 675/700/725/750 ", t("REWORK")))
W(ul_close())
W(subnote("As a result, Cast Range increased from 675 to 675/700/725/750"))
W(ability("Bushwhack"))
W(ul_open())
W(li("Cast Range increased from 1000 to 1100", b(1000, 1100)))
W(ul_close())
W(ability("Scurry"))
W(ul_open())
W(li("No longer doubles all sources of evasion for the duration", t("NERF")))
W(li("Now doubles redirect chance of Mistwoods Wayfarer for the duration", t("REWORK")))
W(ul_close())
W(ability("Sharpshooter"))
W(ul_open())
W(li("Now treats creep heroes as creeps", t("REWORK")))
W(li("The projectile flies through creeps, dealing them damage for half value, but still applying Slow and Break at full force and duration", t("MISC")))
W(li("Since Spirit Bear is considered a true hero, the projectile will stop on impact with it", t("MISC")))
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
W(li("Intelligence gain decreased from 1.5 to 0", b(1.5, 0)))
W(li("Base Movement Speed decreased from 295 to 290", b(295, 290)))
W(ul_close())
W(ability("Inner Fire"))
W(ul_open())
W(li("Damage increased from 105/170/235/300 to 110/180/250/320", b([105, 170, 235, 300], [110, 180, 250, 320])))
W(li("Knockback Duration now scales based on Knockback Distance to a minimum of 0.4s", t("REWORK")))
W(li("Enemies which are 375 units or farther now receive a flat knockback of 25 units", t("REWORK")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Burning Spear"))
W(ul_open())
W(li("Health Cost changed from 4% of current health to 2% of max health ", t("MISC")))
W(ul_close())
W(subnote("Huskar can use this ability even if he has less health than the health cost requires"))
W(ul_open())
W(li("Now also burns enemies for 0.5% of their max health", t("REWORK")))
W(ul_close())
W(ability("Berserkers Blood"))
W(ul_open())
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Can be activated for a health cost. Applies basic dispel to Huskar, then after a delay, heals for the amount of health consumed plus an additional bonus per debuff dispelled. Current HP Cost: 30%. Cooldown: 20s. Cauterize Delay: 3s. Max HP Heal per debuff: 3%", t("MISC")))
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
W(li("Aghanim's Scepter twister damage decreased from 40 + 10 * Wex Level to 30 + 10 * Wex Level ", t("NERF")))
W(ul_close())
W(subnote("60/70/80/90/100/110/120/130/140/150 to 50/60/70/80/90/100/110/120/130/140"))
W(ability("Invoke"))
W(ul_open())
W(li("Now whenever Invoker gets Aghanim's Scepter or Aghanim's Shard, these items are inert in the inventory until Invoker activates them manually. Upon activation, he will be presented with three upgrades to choose from. Upgrades themselves for both Aghanim's Scepter and Aghanim's Shard are unchanged", t("REWORK")))
W(li("You can't change selected upgrades. Selling Aghanim's Scepter and buying it again will provide the same upgrade you chose the first time", t("NERF")))
W(li("Aghanim's Scepter no longer provides +1 level to all three orbs. Now it provides +1 level only to a single orb you choose", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +1 Facet Orb Level replaced with +25 Alacrity Speed/Damage", t("REWORK")))
W(li("Level 20 Talent +50 Alacrity Speed/Damage replaced with +1 Orb Levels", t("REWORK")))
W(ul_close())

# Io
W(hero_header("Io"))
W(ul_open())
W(li("Removed Wellspring innate ability", t("MISC")))
W(ul_close())
W(ability("Equilibrium"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Io always has bonus Outgoing Damage Amp which linearly scales with its health, reaching a maximum of 5% + 0.5% per level at 100% Health. At the same time, Io has Health Restoration and Healing Amplifications which also linearly scale with its health, but reach a maximum of 5% + 0.5% per level at zero Health", t("MISC")))
W(ul_close())
W(ability("Overcharge"))
W(ul_open())
W(li("Now also provides 35/60/85/110 Attack Speed and 8/10/12/14% Spell Amplification to Io and any tethered Allies", t("REWORK")))
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
W(li("Attack Damage Reduction changed from 50% to 51% - 1% per level", b(50, 51)))
W(ul_close())
W(ability("Liquid Fire"))
W(ul_open())
W(li("Now has a 20 mana cost", t("REWORK")))
W(li("Aghanim's Shard now also reduces mana cost to 0", t("REWORK")))
W(ul_close())
W(ability("Liquid Ice"))
W(ul_open())
W(li("Now has a 20 mana cost", t("REWORK")))
W(li("Aghanim's Shard now also reduces mana cost to 0", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Ice Path Damage increased +60 to +75", t("BUFF")))
W(li("Level 15 Talent Dual Breath Cooldown Reduction increased from 3s to 3.5s", b(3, 3.5, l=True)))
W(ul_close())

# Juggernaut
W(hero_header("Juggernaut"))
W(ul_open())
W(li("Removed Duelist innate ability", t("MISC")))
W(ul_close())
W(ability("Bladeform"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Juggernaut receives a stack of Bladeform every 2s that he does not take damage. Each stack grants 2.5% + 0.05% per level base Agility bonus and 1% movement bonus and there is a maximum of 10 stacks. Stacks fade after 2s upon taking any damage", t("MISC")))
W(ul_close())
W(ability("Blade Fury"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Healing Ward"))
W(ul_open())
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Increases healing by 1.5% and hits to destroy by 1", t("MISC")))
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
W(li("Removed Special Reserve innate ability", t("MISC")))
W(ul_close())
W(ability("Bright Speed"))
W(ul_open())
W(li("New innate ability. Passive, can't be leveled up", t("NERF")))
W(li("Keeper of the Light gains +1 movement speed for every 2.5 Intelligence. Whenever Keeper of the Light moves 300 distance, he leaves behind light that allows him to see in 400 range for 3 seconds", t("MISC")))
W(ul_close())
W(ability("Chakra Magic"))
W(ul_open())
W(li("Cooldown rescaled from 18/16/14/12s to 19/16/13/10s", b([18, 16, 14, 12], [19, 16, 13, 10], l=True)))
W(li("Mana Restore increased from 90/160/230/300 to 105/170/235/300", b([90, 160, 230, 300], [105, 170, 235, 300])))
W(ul_close())
W(ability("Blinding Light"))
W(ul_open())
W(li("Cast Range increased from 400/500/600/700 to 500/575/650/725", b([400, 500, 600, 700], [500, 575, 650, 725])))
W(li("Knockback distance changed from 400 to knocking back to the edges of the effect radius, but a minimum knockback distance is 175 ", t("MISC")))
W(ul_close())
W(subnote("Min distance is used for enemies near the edge of AoE"))
W(ability("Spirit Form"))
W(ul_open())
W(li("No longer grants bonus movement speed percentage", t("NERF")))
W(li("Now increases movement speed bonus of Bright Speed by 50% while active", t("REWORK")))
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
W(ability("Switch Weapons"))
W(ul_open())
W(li("Cooldown changed from 7.75s - 0.25s per level up to 8s - 0.25s per level ", t("MISC")))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ul_open())
W(li("Now the first katana hit or ability will deal 12% bonus damage after switching to Katana, and after switching to Sai Kez gains +12% movement speed for 2 seconds", t("REWORK")))
W(li("Aghanim's Scepter no longer restarts the alternate ability cooldown if it was already on cooldown", t("NERF")))
W(ul_close())
W(ability("Grappling Claw"))
W(ul_open())
W(li("When targeting a tree, now always destroys the targeted tree and ends in the tree's position", t("REWORK")))
W(ul_close())
W(ability("Talon Toss"))
W(ul_open())
W(li("Cast Range decreased from 1200 to 650/750/850/950 ", b(1200, [650, 750, 850, 950])))
W(ul_close())
W(subnote("Now matches Grappling Claw"))
W(ability("Shodo Sai"))
W(ul_open())
W(li("The proc effect now triggers a critical strike only instead of creating a Mark", t("REWORK")))
W(li("18% Chance to Mark replaced with 20% Critical Strike Chance", t("REWORK")))
W(li("As a result, marks are applied only by parrying and casting Raven's Veil", t("MISC")))
W(li("No longer restricts Kez from proccing passive Bash spells of Skull Basher and Abyssal Blade", t("NERF")))
W(li("Mark Stun Duration increased from 0.4s to 0.5/0.6/0.7/0.8s", b(0.4, [0.5, 0.6, 0.7, 0.8])))
W(li("No longer has a parry bonus by default", t("NERF")))
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Parrying creates a stronger mark that will stun the target for an additional 0.2s and an a crit bonus of 50%", t("MISC")))
W(ul_close())
W(ability("Raptor Dance"))
W(ul_open())
W(li("No longer provides magic damage immunity", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +100% Shodo Sai Mark Critical Strike replaced with +80% Shodo Sai Critical Strike", t("REWORK")))
W(ul_close())

# Kunkka
W(hero_header("Kunkka"))
W(ability("Admiral's Rum"))
W(ul_open())
W(li("Can no longer be applied by multiple sources, and will no longer trigger passively if Ghostship already applied the buff", t("NERF")))
W(li("Cooldown changed from 60s to 60.5s - 0.5s per level", b(60, 60.5, l=True)))
W(li("Bonus Movement Speed rescaled from 10% to 7.75% + 0.25% per level", b(10, 7.75)))
W(li("Duration decreased from 6s to 5s", b(6, 5)))
W(li("Delayed Damage decreased from 20% to 18%", b(20, 18)))
W(ul_close())
W(ability("Ghostship"))
W(ul_open())
W(li("Now applies Admiral's Rum at a 2x factor", t("REWORK")))
W(li("Multiplication applies to duration, delayed damage and movement speed bonus", t("MISC")))
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
W(li("Bonus Duration changed from 10% + 1% per level up to 9% + 1% per level ", t("MISC")))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Catchy Lick"))
W(ul_open())
W(li("Now can lick runes to pull them. Rune-licking refunds spent mana", t("REWORK")))
W(li("Health Regen Duration decreased from 10s to 8s", b(10, 8)))
W(li("Bonus health regen is now also provided if the target is killed by Catchy Lick", t("REWORK")))
W(ul_close())
W(ability("Amphibian Rhapsody"))
W(ul_open())
W(li("Aghanim's Scepter no longer adds damage to double-strumming", t("NERF")))
W(ul_close())
W(ability("Fight Song"))
W(ul_open())
W(li("Now also deals 20/30/40 magical damage by default", t("REWORK")))
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Increases magic damage by 6/12/18 per Groovin' stack when this song is used in double-strumming", t("MISC")))
W(ul_close())
W(ability("Song Double Time"))
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
W(li("Base armor decreased by 1", bstat_h("Legion Commander", "ArmorPhysical", "7.40c", -1), extra=note_box("From 0.0 to -1")))
W(ul_close())
W(ability("Outfight Them"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("Passively grants Legion Commander bonus armor, equal to 1 + 0.1 per level. Whenever Legion Commander casts an ability, she gains the same amount as a stacking bonus for 6s. Whenever allies within 1200 range cast an ability, they also gain a 6s buff with 50% of the value. This bonus stacks independently", t("MISC")))
W(ul_close())
W(ability("Overwhelming Odds"))
W(ul_open())
W(li("Now also applies 100% movement slow upon dealing damage for 0.3s", t("REWORK")))
W(li("Aghanim's Shard upgrade reworked", t("MISC")))
W(li("Increases radius by 100. Grants an all damage barrier equal to 50% of the damage dealt with Overwhelming Odds for 6s", t("MISC")))
W(ul_close())
W(ability("Press The Attack"))
W(ul_open())
W(li("Multiple instances can now stack independently", t("REWORK")))
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Increases bonus movement speed by 12%. Ability becomes cast-point, affecting all allies within the targeted 500 radius area. Legion Commander is always affected, even when outside of the cast area", t("MISC")))
W(ul_close())
W(ability("Moment Of Courage"))
W(ul_open())
W(li("No longer has a 25% proc chance", t("NERF")))
W(li("Now automatically triggers after taking 7/6/5/4 attacks", t("REWORK")))
W(li("Will not activate unless Legion Commander is both attacking and being attacked. Until this requirement is met, the 'prepared' state is kept indefinitely", t("MISC")))
W(li("Cooldown decreased from 1.7/1.4/1.1/0.8 to 0.3s", b([1.7, 1.4, 1.1, 0.8], 0.3, l=True)))
W(ul_close())
W(ability("Duel"))
W(ul_open())
W(li("Legion Commander can now use any abilities during Duel", t("REWORK")))
W(li("Legion Commander will stop attacking as normal during cast animations", t("MISC")))
W(li("Items can't be used", t("NERF")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(li("Aghanim's Scepter upgrade reworked", t("MISC")))
W(li("When Legion Commander wins a duel, Press the Attack is automatically triggered around her", t("MISC")))
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
W(li("Duration improved from 10s to 8s ", b(10, 8)))
W(ul_close())
W(subnote("Number of explosions (hence, total damage) is unchanged, explosion interval decreased from 0.25s to 0.225s"))

# Lich
W(hero_header("Lich"))
W(ul_open())
W(li("Base Mana Regen decreased from 0.75 to -1", b(0.75, -1)))
W(li("Intelligence gain decreased from 3.8 to 3.4", b(3.8, 3.4)))
W(li("Removed Death Charge innate ability", t("MISC")))
W(ul_close())
W(ability("Death Charge"))
W(ul_open())
W(li("New Innate ability. Active", t("MISC")))
W(li("Lich can instantly kill an allied creep to gain mana relative to its current health and earn experience bounty for it. Health to Mana: 42% + 3% per level. Experience Bounty: 69% + 6% per level. Cast Range: 700. No Mana Cost. Cooldown: 120s", t("MISC")))
W(li("This ability starts on extended cooldown and with no charges, making the first cast possible only at 2:00 mark", t("MISC")))
W(li("Sacrificed creeps count as denies, providing experience to enemy heroes. Lich's experience gain is independent from experience enemies gain", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +4s Frost Shield Duration replaced with 2 Frost Shield Charges", t("REWORK")))
W(li("Level 25 Talent +100 Chain Frost Incremental Damage replaced with Chain Frost Unlimited Bounces", t("REWORK")))
W(ul_close())

# Lifestealer
W(hero_header("Lifestealer"))
W(ul_open())
W(li("Base Damage increased by 10", bstat_h("Lifestealer", "AttackDamageMin", "7.40c", 10), extra=note_box("From 19 to 29")))
W(li("Damage at level 1 increased from 39–45 to 49–55", t("BUFF")))
W(li("Base Attack Speed increased from 100 to 120", b(100, 120)))
W(li("Base Movement Speed increased from 315 to 320", b(315, 320)))
W(ul_close())
W(ability("Ghoul Frenzy"))
W(ul_open())
W(li("Reworked into Innate ability. Passive", t("MISC")))
W(li("Provides Lifestealer with 5 bonus Attack Speed per level", t("MISC")))
W(ul_close())
W(ability("Rage"))
W(ul_open())
W(li("Now also provides 9/12/15/18% bonus movement speed while active", t("REWORK")))
W(ul_close())
W(ability("Open Wounds"))
W(ul_open())
W(li("Mana Cost decreased from 100 to 90", b(100, 90, l=True)))
W(li("Max Slow increased from 35/40/45/50% to 50%", b([35, 40, 45, 50], 50)))
W(ul_close())
W(ability("Feast"))
W(ul_open())
W(li("Now is a basic ability", t("REWORK")))
W(li("Heal From Target's Max Health rescaled from 2/2.25/2.5/2.75% to 1.45/2.05/2.65/3.25%", b([2, 2.25, 2.5, 2.75], [1.45, 2.05, 2.65, 3.25])))
W(li("Max Health Damage rescaled from 2/2.25/2.5/2.75% to 1.45/2.05/2.65/3.25%", b([2, 2.25, 2.5, 2.75], [1.45, 2.05, 2.65, 3.25])))
W(li("Max Health per Hero Kill increased from 10 to 10/15/20/25 ", b(10, [10, 15, 20, 25])))
W(ul_close())
W(subnote("Is not retroactive"))
W(ul_open())
W(li("No longer increases deny health threshold to 75%", t("NERF")))
W(ul_close())
W(ability("Infest"))
W(ul_open())
W(li("Now can be used on Ancient creeps by default", t("REWORK")))
W(li("Aghanim's Shard upgrade reworked", t("MISC")))
W(li("When consuming a creep, enemies also take damage over time equal to 30% of the creep's remaining health. Damage duration: 3s. Has no effect when bursting out of enemy heroes", t("MISC")))
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
W(ul_open())
W(li("Removed Combustion innate ability", t("MISC")))
W(ul_close())
W(ability("Slow Burn"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Lina's abilities deal an additional 64% damage as undispellable burn damage over 4s", t("MISC")))
W(ul_close())
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
W(li("Aghanim's Shard upgrade reworked", t("MISC")))
W(li("Casting Laguna Blade temporarily supercharges Lina, granting her 12 stacks of Fiery Soul. Supercharge duration: 5s", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Light Strike Array Damage decreased from +150 to +110", b(150, 110)))
W(li("Level 25 Talent +150% Crit On Targets Affected By Spells replaced with 150% Attack Crit on Targets Affected by Slow Burn", t("REWORK")))
W(li("Level 25 Talent +60% Combustion Overheat Damage replaced with +1s Slow Burn Duration ", t("REWORK")))
W(li("This increases additional damage from 64% to 80%", b(64, 80)))
W(ul_close())

# Lion
W(hero_header("Lion"))
W(ability("To Hell And Back"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("Killing or assisting in a Hero kill provides Lion with 20% debuff duration while that hero is dead. Whenever Lion respawns or resurrects, he gains 20% spell amplification for 90s or until he gets a kill or an assist", t("MISC")))
W(ul_close())
W(ability("Finger Of Death"))
W(ul_open())
W(li("Cooldown decreased from 120/80/40s to 110/70/30s", b([120, 80, 40], [110, 70, 30], l=True)))
W(li("Damage per kill decreased from 40 to 30", b(40, 30)))
W(li("Now has empowered melee attacks after the cast by default", t("REWORK")))
W(li("After using Finger of Death, Lion's hand becomes empowered, turning him into a melee hero with 250 attack range and 30 bonus movement speed. These melee attacks have 25% cleave and deal 20/30/40 bonus damage which increases with each Finger of Death kill. Enemy heroes that die within 3s after getting hit with these melee attacks (or from them) also provide bonus per kill damage. Melee form duration: 20s", t("MISC")))
W(li("Ability can be toggled with right-click to disable the melee form", t("MISC")))
W(li("Cleave area is a cone with 150 width that increases up to 350 at 650 distance", t("MISC")))
W(li("Aghanim's Scepter now also increases melee cleave from 25% to 50% and duration from 20s to 30s", b(25, 50)))
W(li("Aghanim's Scepter no longer decreases cooldown", t("NERF")))
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
W(li("Damage for Allies/Self changed from 1/2 + 1/2 per level up to 1/2 per level ", t("MISC")))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ul_open())
W(li("Bonus Night Vision changed from 250 + 25 per level up to 225 + 25 per level ", t("MISC")))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Lunar Orbit"))
W(ul_open())
W(li("Now applies 8/12/16/20% damage reduction while active", t("REWORK")))
W(li("Aghanim's Shard upgrade reworked", t("MISC")))
W(li("Increases damage reduction by 10% and provides Luna with 20% bonus movement speed for the duration", t("MISC")))
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
W(li("Damage to neutrals changed from 2% per level to 18% + 2% per level", t("MISC")))
W(ul_close())
W(ability("Summon Wolves"))
W(ul_open())
W(li("Aghanim's Shard upgrade reworked", t("MISC")))
W(li("Increases the number of wolves by 1 and grants them Hightail ability. Activate it to give them 100% evasion, 20 bonus attack speed, and hasted movement for 6s", t("MISC")))
W(ul_close())
W(ability("Shapeshift"))
W(ul_open())
W(li("Now grants controlled units movement speed and critical strike bonuses", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent +2 Wolves Summoned replaced with -25% Summon Wolves BAT ", t("REWORK")))
W(li("Improves wolves' BAT from 1.2/1.1/1/0.9s to 0.9/0.825/0.75/0.675s", b([1.2, 1.1, 1, 0.9], [0.9, 0.825, 0.75, 0.675])))
W(ul_close())

# Magnus
W(hero_header("Magnus"))
W(ul_open())
W(li("Base Agility increased from 12 to 14", b(12, 14)))
W(li("Damage at level 1 increased from 55–63 to 56–64", t("BUFF")))
W(ul_close())
W(ability("Solid Core"))
W(ul_open())
W(li("No longer levels with Reverse Polarity", t("NERF")))
W(li("Slow Resistance rescaled from 20/30/40/50% to 24% + 1% per level", b([20, 30, 40, 50], 24)))
W(ul_close())
W(ability("Empower"))
W(ul_open())
W(li("Now always affects Magnus with 30% increased values and can't be cast on himself", t("NERF")))
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
W(ability("Special Delivery"))
W(ul_open())
W(li("If Marci's courier is in the fountain when Special Delivery is cast, the courier will take all items from the stash before teleporting. The courier will now automatically attempt to transfer items upon teleporting and head back to the fountain. If the courier has any extra items after trying to transfer or didn't transfer any items, it will stay next to Marci", t("REWORK")))
W(li("Cooldown changed from 240s to 245s - 5s per level", b(240, 245, l=True)))
W(ul_close())
W(ability("Bodyguard"))
W(ul_open())
W(li("Ability Reworked", t("MISC")))
W(li("Has both passive and active components", t("MISC")))
W(li("Passively grants Marci 12/18/24/30% lifesteal and 12/18/24/30% bonus base attack damage", t("MISC")))
W(li("When cast on an ally, she provides them with 75% of passive bonuses and a shared all damage barrier that blocks 90/160/230/300 damage. Damaging the barrier on either Marci or the target will reduce it for both. As Marci attacks heroes, 30% of the damage dealt restores the barrier. Duration: 7s", t("MISC")))
W(li("Cast Range: 500. Mana Cost: 60/65/70/75. Cooldown: 20s. Cast Point: 0.2s", t("MISC")))
W(li("The effect is dispellable. Dispelling Marci will remove the barrier. Dispelling the target will remove both the barrier and passive bonuses (lifesteal and base attack damage)", t("MISC")))
W(ul_close())
W(ability("Companion Run"))
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
W(li("No longer considers Mars's allies when determining if Mars is outnumbered", t("NERF")))
W(li("HP Regen per extra enemy decreased from 70% to 40%", b(70, 40)))
W(ul_close())
W(ability("Bulwark"))
W(ul_open())
W(li("Now a point targeted ability. Mars will face towards the targeted direction when toggled on", t("REWORK")))
W(li("No longer upgraded with Aghanim's Scepter", t("NERF")))
W(ul_close())
W(ability("Arena Of Blood"))
W(ul_open())
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Lowers cooldown by 10s and increases duration from 5.5s to 6.5s. If an enemy is killed in the Arena, Mars and all of his allies inside the Arena restore 35% of their max health and mana and get a 35% attack damage buff for 20s. This effect stacks", b(5.5, 6.5, l=True)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +20% Dauntless Regen Per Enemy replaced with +1.5 Mana Regen", t("REWORK")))
W(li("Level 20 Talent -16s Arena Of Blood Cooldown replaced with +70 Arena of Blood Spear Damage", t("REWORK")))
W(ul_close())

# Medusa
W(hero_header("Medusa"))
W(ability("Gorgon Grasp"))
W(ul_open())
W(li("Cooldown decreased from 30/27/24/21s to 30/26/22/18s", b([30, 27, 24, 21], [30, 26, 22, 18], l=True)))
W(li("Now always centers the cast cursor around the second grouping, even if the number of volleys is increased", t("REWORK")))
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
W(li("Removed Sticky Fingers innate ability", t("MISC")))
W(ul_close())
W(ability("Geomancy"))
W(ul_open())
W(li("New innate ability. Passive, can't be leveled up", t("NERF")))
W(li("Meepo grants stacking bonuses to himself and his clones based on their terrain. Each Meepo grants its bonus to other Meepos. If there is a tree within 250 range, he receives +1 Health Regen. If he is standing on solid ground, he receives 2% bonus movement speed. If he is in the water, his attacks slow the target by 2% for 2 seconds", t("MISC")))
W(li("Each Meepo can provide only one tree bonus, no matter how many trees are within the radius", t("MISC")))
W(li("If there's a tree in the water, Meepo will provide both water and tree bonus", t("MISC")))
W(ul_close())
W(ability("Ransack"))
W(ul_open())
W(li("Now pierces Debuff Immunity", t("REWORK")))
W(li("No longer has separate creep values. Follows global lifesteal rules instead ", t("NERF")))
W(ul_close())
W(subnote("Has a 40% penalty against creeps"))
W(ability("Divided We Stand"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("Max Level increased from 3 to 4", b(3, 4)))
W(li("Level requirement rescaled from 4/11/18 to 3/10/17/24", b([4, 11, 18], [3, 10, 17, 24], l=True)))
W(li("No longer passively grants Magic Resistance", t("NERF")))
W(li("Now each duplicate copies all of Meepo's items, but they share their cooldowns. Damage, attack speed, health / mana regeneration, mana burn, and proc chance bonuses from items are distributed equally among the amount of Meepos  ", t("REWORK")))
W(ul_close())
W(subnote("Amounting to a 50/66.6/75/80% penalty on each Meepo"))
W(ul_open())
W(li("Clones can't use consumable shared items on the main Meepo", t("NERF")))
W(li("No longer has a penalty for Strength, Agility, or Intelligence gained from items", t("NERF")))
W(li("Clones no longer gain 30% experience independently", t("NERF")))
W(li("Meepo gains 100% of the experience from Hero Kills or Assists as long as at least one Meepo is in range ", t("MISC")))
W(ul_close())
W(subnote("Multiple Meepos within experience range does not increase the amount gained"))
W(ul_open())
W(li("All other experience gained by any Meepo is divided by the number of Meepos ", t("MISC")))
W(ul_close())
W(subnote("Each Meepo gains experience independently"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Health increased from +350 to +400", b(350, 400)))
W(ul_close())

# Mirana
W(hero_header("Mirana"))
W(ul_open())
W(li("Removed Selemene's Faithful innate ability", t("MISC")))
W(ul_close())
W(ability("Celestial Quiver"))
W(ul_open())
W(li("New innate ability. Auto-cast attack modifier, can't be leveled up", t("NERF")))
W(li("Mirana consumes a charge to empower her next attack with bonus magic damage equal to 3 per Mirana's level. At the start she has 2 max charges but gains 1 more every 7 levels. Base Charge Restore Time: 6s", t("MISC")))
W(li("Upgraded with Aghanim's Shard", t("MISC")))
W(li("Casting Leap provides 3 temporary charges for the duration of the buff", t("MISC")))
W(li("These temporary charges ignore the max charges count and stack from each Leap cast", t("MISC")))
W(ul_close())
W(ability("Leap"))
W(ul_open())
W(li("Aghanim's Shard no longer provides crits during the buff ", t("NERF")))
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
W(li("No longer levels with Wukong's Command", t("NERF")))
W(li("Cooldown changed from 24/20/16/12s to 24.5s - 0.5s per level", b([24, 20, 16, 12], 24.5, l=True)))
W(ul_close())
W(ability("Tree Dance"))
W(ul_open())
W(li("Cast point increased from 0.1s to 0.2s", b(0.1, 0.2, l=True)))
W(li("Cast Range / Perched Tree Cast Range increased from 800 to 900", b(800, 900)))
W(li("Cooldown decreased from 1.4/1.2/1.0/0.8s to 0.9/0.6/0.3/0s", b([1.4, 1.2, 1.0, 0.8], [0.9, 0.6, 0.3, 0], l=True)))
W(li("Leap speed decreased from 700 to 600", b(700, 600)))
W(li("Leaping between trees can now be interrupted by Roots and Leashes", t("REWORK")))
W(li("Previously it was only interrupted by Stunned, Hidden, or Hexed statuses", t("MISC")))
W(ul_close())
W(ability("Wukongs Command"))
W(ul_open())
W(li("Now has Changing of the Guard sub-ability by default", t("REWORK")))
W(li("While Wukong's Command is active, Monkey King gains a Changing of the Guard ability which allows him to transform into any one of his soldiers. Upon cast, Monkey King takes the place of the soldier closest to the target location for 1.5s, and leaves another one in his stead. While Transfigured, Monkey King is indistinguishable from other soldiers and invulnerable, but can't issue commands. Cast Point: 0.3s. No Mana Cost. Cooldown: 3s", t("NERF")))
W(ul_close())
W(ability("Transfiguration"))
W(ul_open())
W(li("Ability appears in place of Wukong's Command and starts on a 1s cooldown after casting Wukong's Command. Can't be cast while rooted and can't target soldiers created by Aghanim's Scepter effect. Monkey King disjoints projectiles upon transformation.", t("NERF")))
W(li("The possessed soldier has a small ring around it which is visible only to Monkey King and his allies. When the effect is over, Monkey King becomes his usual self leaving the overtaken soldier's position empty.", t("MISC")))
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
W(li("Hero model size now scales on his Agility/Strength ratio", t("REWORK")))
W(li("Removed Accumulation innate ability", t("MISC")))
W(ul_close())
W(ability("Ebb And Flow"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("Strength and Agility provide Morphling with additional bonuses. His cast range and Slow Resistance are increased by a portion of his Strength. His attack range and movement speed are increased by a portion of his Agility. These bonuses are provided even while replicating, except for the extra attack range which is not provided when replicating a melee unit", t("BUFF")))
W(li("Strength to Cast Range: 20%. Strength to Slow Resistance: 20%. Agility to Movement Speed: 15%. Agility to Ranged Attack Range: 20%", t("MISC")))
W(ul_close())
W(ability("Waveform"))
W(ul_open())
W(li("Cast Range decreased from 700/800/900/1000 to 700/775/850/925", b([700, 800, 900, 1000], [700, 775, 850, 925])))
W(ul_close())
W(ability("Adaptive Strike Agi"))
W(ul_open())
W(li("Base Damage increased from 25/50/75/100 to 50/70/90/110", b([25, 50, 75, 100], [50, 70, 90, 110])))
W(ul_close())

# Muerta
W(hero_header("Muerta"))
W(ability("Supernatural"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("Whenever an enemy hero dies within 925 units of Muerta, she gains a stack of 1% spell amplification up to a maximum equal to her current level. When Muerta dies she loses half the stacks, rounded down", t("MISC")))
W(li("Passive ethereal bonuses moved to Pierce the Veil", t("MISC")))
W(ul_close())
W(ability("Pierce The Veil"))
W(ul_open())
W(li("No longer provides 70/100/130 bonus damage", t("NERF")))
W(li("Now grants +75% base damage", t("REWORK")))
W(li("Now has a passive component", t("REWORK")))
W(li("Muerta can always attack ethereal targets and can attack when she is ethereal. When either she or her target is ethereal, all of her attack damage is dealt as magical damage and her physical lifesteal is treated as spell lifesteal", t("MISC")))
W(li("Lifesteal conversion happens only for attacks and won't affect her spells", t("MISC")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Spectral Slug"))
W(ul_open())
W(li("New ability granted by Aghanim's Shard", t("MISC")))
W(li("Muerta shoots a spectral bullet at an enemy, dealing damage, knocking them back, and turning them ethereal for 3s, rendering them immune to physical damage and unable to attack. The target is slowed and becomes 20% more vulnerable to magic damage", t("MISC")))
W(li("Range: 500. Mana Cost: 75. Cooldown: 12s. Damage: 225. Slow: 30%. Knockback Distance: 250", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent +55 Gunslinger Damage replaced with +15 Intelligence", t("REWORK")))
W(ul_close())

# Naga Siren
W(hero_header("Naga Siren"))
W(ability("Eelskin"))
W(ul_open())
W(li("Now provides evasion for Naga Siren on her own", t("REWORK")))
W(li("Evasion per Naga changed from 8% to 4.9% + 0.1% per level", b(8, 4.9)))
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
W(li("Minimum Base damage increased by 4 ", bstat_h("Nature's Prophet", "AttackDamageMin", "7.40c", 4), extra=note_box("From 21 to 25")))
W(li("Damage spread decreased from 10 to 6", b(10, 6)))
W(li("Damage at level 1 increased from 40–50 to 44–50", t("BUFF")))
W(ul_close())
W(ability("Spirit Of The Forest"))
W(ul_open())
W(li("No longer levels with Wrath of Nature", t("NERF")))
W(li("Tree Radius rescaled from 300/400/500/600 to 300 + 10 per level", b([300, 400, 500, 600], 300)))
W(li("Multiplier per treant increased from 1x to 2x", t("BUFF")))
W(li("Treants also have Spirit of the Forest and gain bonus damage for each nearby tree and treant", t("MISC")))
W(ul_close())
W(ability("Sprout"))
W(ul_open())
W(li("Vision increased from 250 to 400", b(250, 400)))
W(ul_close())
W(ability("Nature's Call"))
W(ul_open())
W(li("Treant Movespeed rescaled from 305/310/315/320 to 300/315/330/345", b([305, 310, 315, 320], [300, 315, 330, 345])))
W(li("Treant Health decreased from 550 to 450", b(550, 450)))
W(li("Treants now have 25% Magic Resistance", t("REWORK")))
W(li("Treants now deal 4/8/12/16 bonus damage to enemy Heroes", t("REWORK")))
W(li("This bonus is also affected by the Treant Damage multiplying talent", t("MISC")))
W(li("Treants now have free pathing through trees", t("REWORK")))
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
W(li("No longer levels with Reaper's Scythe", t("NERF")))
W(li("Health and Mana regen rescaled from 3.5/5/6.5/8 to 3.7 + 0.3 per level", b([3.5, 5, 6.5, 8], 3.7)))
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
W(ul_open())
W(li("Removed Heart of Darkness innate ability", t("MISC")))
W(ul_close())
W(ability("Hunter In The Night"))
W(ul_open())
W(li("Now an innate ability", t("REWORK")))
W(li("Move Speed bonus changed from 22/28/34/40% to 24% + 2% per 3 levels", b([22, 28, 34, 40], 24)))
W(li("Attack Speed bonus changed from 20/40/60/80 to 38 + 2 per level", b([20, 40, 60, 80], 38)))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Increases bonus Movement Speed by 15% and bonus Attack Speed by 50. Killing an enemy hero resets cooldowns of all basic abilities", t("MISC")))
W(ul_close())
W(ability("Void"))
W(ul_open())
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Now affects all units within 400 radius around the target", t("REWORK")))
W(ul_close())
W(ability("Crippling Fear"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Scepter", t("NERF")))
W(ul_close())
W(ability("Midnight Feast"))
W(ul_open())
W(li("New basic ability. Has both passive and active components", t("MISC")))
W(li("Night Stalker heals himself 6/8/10/12 health when attacking enemy units", t("MISC")))
W(li("Attacks on allied units and buildings will not heal Night Stalker", t("MISC")))
W(li("Can be cast at night to eat a non-ancient creep and restore 10/15/20/25% of Night Stalker's maximum health and 10/12/14/16% of his mana. Cast Range: 125. No Mana Cost. Cooldown: 39/36/33/30s", t("MISC")))
W(li("Can't be cast on allies", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +5s Dark Ascension Duration replaced with +10 Crippling Fear DPS", t("REWORK")))
W(li("Level 20 Talent +40 Crippling Fear DPS replaced with +75 Crippling Fear Radius", t("REWORK")))
W(li("Level 25 Talent +100 Hunter in the Night Attack Speed replaced with +100 Midnight Feast Lifesteal", t("REWORK")))
W(ul_close())

# Nyx Assassin
W(hero_header("Nyx Assassin"))
W(ul_open())
W(li("Removed Nyxth Sense innate ability", t("MISC")))
W(ul_close())
W(ability("Neuro Sting"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("When Nyx Assassin deals damage with attacks or his abilities, he burns affected unit's mana equal to 12% of damage dealt", t("MISC")))
W(li("Damage reflected with Spiked Carapace also counts", t("MISC")))
W(ul_close())
W(ability("Jolt"))
W(ul_open())
W(li("Now burns 9/12/15/18% of the target's Max Mana", t("REWORK")))
W(ul_close())
W(ability("Vendetta"))
W(ul_open())
W(li("Now also applies a 4s Break on hit", t("REWORK")))
W(li("Aghanim's Shard reworked", t("MISC")))
W(li("Decreases cooldown by 10s. For the first 15s, Nyx Assassin is hasted and has unobstructed pathing", t("MISC")))
W(ul_close())

# Ogre Magi
W(hero_header("Ogre Magi"))
W(ability("Fireblast"))
W(ul_open())
W(li("Now also upgraded by Aghanim's Scepter", t("REWORK")))
W(li("Becomes Refined Fireblast, reducing its cooldown by 1s and increasing its cast speed by 25%", t("MISC")))
W(ul_close())
W(ability("Multicast"))
W(ul_open())
W(li("Each point of Strength increases chances of Multicast by 0.0625%, so every 16 Strength points add 1%", t("MISC")))
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
W(li("Base Armor decreased by 1", bstat_h("Omniknight", "ArmorPhysical", "7.40c", -1), extra=note_box("From 3 to 2")))
W(li("Agility gain decreased from 2.0 to 1.7", b(2.0, 1.7)))
W(ul_close())
W(ability("Degen Aura"))
W(ul_open())
W(li("No longer levels with Guardian Angel", t("NERF")))
W(li("Movement Slow changed from 10/20/30/40% to 11% + 1% per level", b([10, 20, 30, 40], 11)))
W(ul_close())
W(ability("Purification"))
W(ul_open())
W(li("Now pierces Debuff Immunity on enemies (previously only pierced Debuff Immunity on allies)", t("REWORK")))
W(ul_close())
W(ability("Repel"))
W(ul_open())
W(li("Cooldown decreased from 50/45/40/35s to 40/36/32/28s", b([50, 45, 40, 35], [40, 36, 32, 28], l=True)))
W(li("No longer provides bonus Strength", t("NERF")))
W(li("No longer provides bonus Strength / HP Regen per Debuff", t("NERF")))
W(li("As a result, provides only Debuff Immunity with 60% magic resistance, and 8/12/16/20 bonus health regen. Has no effects per dispelled debuffs", t("MISC")))
W(ul_close())
W(ability("Hammer of Purity"))
W(ul_open())
W(li("Now pierces Debuff Immunity", t("REWORK")))
W(li("Cooldown decreased from 20/15/10/5s to 13/10/7/4s", b([20, 15, 10, 5], [13, 10, 7, 4], l=True)))
W(li("Bonus Base Damage decreased from 55/70/85/100% to 30/50/70/90%", b([55, 70, 85, 100], [30, 50, 70, 90])))
W(li("Damage decreased from 25/50/75/100 to 20/40/60/80", b([25, 50, 75, 100], [20, 40, 60, 80])))
W(li("Now heals Omniknight for 30% of the damage dealt over the next 5s", t("REWORK")))
W(ul_close())
W(ability("Guardian Angel"))
W(ul_open())
W(li("Now is a no-target ability. The effect is applied in an aura centered around Omniknight that follows him", t("REWORK")))
W(li("Has no linger duration", t("MISC")))
W(li("Duration decreased from 5/6/7s to 4/4.5/5s", b([5, 6, 7], [4, 4.5, 5])))
W(li("Radius increased from 400 to 700", b(400, 700)))
W(li("Aghanim's Scepter reworked", t("MISC")))
W(li("Becomes global, affects buildings, and amplifies health restoration by 100%", t("MISC")))
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
W(li("Oracle now also predicts Roshan's exact respawn timer", t("REWORK")))
W(ul_close())
W(ability("False Promise"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Scepter", t("NERF")))
W(ul_close())
W(ability("Diviners Deck"))
W(ul_open())
W(li("New passive ability granted by Aghanim's Scepter", t("MISC")))
W(li("Oracle receives a Tarot Card Buff now and every 90 seconds. This buff is undispellable and lasts until the next one replaces it. Oracle knows which buff will be next.", t("REWORK")))
W(li("Death: +40% Spell Amplification", t("MISC")))
W(li("The Fool: +100% Gold Gain", t("MISC")))
W(li("The World: +150% Intelligence", t("MISC")))
W(li("The Lovers: +40% Heal Amplification", t("MISC")))
W(li("The Tower: Gain a 400 all-damage barrier which regenerates after not taking damage for 7s", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent Fortune's End Heals/Damages for 80 Per Effect Dispelled replaced with +100 Fortune's End Radius", t("REWORK")))
W(ul_close())

# Outworld Destroyer
W(hero_header("Outworld Destroyer"))
W(ul_open())
W(li("Base Agility decreased from 22 to 17", b(22, 17)))
W(li("Base Armor decreased by 1", bstat_h("Outworld Destroyer", "ArmorPhysical", "7.40c", -1), extra=note_box("From 1 to 0")))
W(li("Removed OD innate ", t("MISC")))
W(li("Aka Ominous Discernment, aka Obstreperous Dissimilator, aka Obnoxious Determinator, aka Obsequious Deliberator, aka Ornery Deconstructor, aka Obnubilated Delineator, aka Omniscient Desiderator", t("MISC")))
W(ul_close())
W(ability("Equilibrium"))
W(ul_open())
W(li("Now an innate ability", t("REWORK")))
W(li("Max Mana Restore now depends on the ability it procced on", t("REWORK")))
W(li("For regular abilities Max Mana Restoration changed from 25/35/45/55% to 40% + 5% per 5 levels", b([25, 35, 45, 55], 40)))
W(li("For attack modifiers that spend mana Max Mana Restoration changed from 25/35/45/55% to 25% + 5% per 5 levels", b([25, 35, 45, 55], 25)))
W(ul_close())
W(ability("Objurgation"))
W(ul_open())
W(li("New basic ability. Has both passive and active components", t("MISC")))
W(li("Increases maximum mana by 80/160/240/320", t("MISC")))
W(li("Can be activated to create an all damage barrier equal to 120/180/240/300 + 12% of Outworld Destroyer's max mana. Duration: 10s. Mana Cost: 250. Cooldown: 36/34/32/30s", t("MISC")))
W(li("Barrier can be dispelled", t("MISC")))
W(li("Multiple instances of Objurgation barrier stack", t("MISC")))
W(li("Upgraded with Aghanim's Scepter", t("MISC")))
W(li("Increases Max Mana to Barrier by 4%. Damage that would bring Outworld Destroyer below 20% is prevented, triggering a strong dispel and an automatic instance of undispellable Objurgation. This effect cannot trigger more than once every 80s, but refreshes on death", t("NERF")))
W(ul_close())
W(ability("Sanity's Eclipse"))
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
W(ability("Gyroshell"))
W(ul_open())
W(li("Stun Duration increased from 0.8/1/1.2s to 1.2s", b([0.8, 1, 1.2], 1.2)))
W(ul_close())

# Phantom Assassin
W(hero_header("Phantom Assassin"))
W(ability("Blur"))
W(ul_open())
W(li("No longer levels with Coup de Grace", t("NERF")))
W(li("Vanish Radius rescaled from 625/550/475/400 to 500", b([625, 550, 475, 400], 500)))
W(li("Vanish Buffer rescaled from 0.4/0.6/0.8/1s to 0.8s", b([0.4, 0.6, 0.8, 1], 0.8)))
W(li("Active Movement Speed changed from 6/9/12/15% to 9.5% + 0.5% per level", b([6, 9, 12, 15], 9.5)))
W(ul_close())

# Phantom Lancer
W(hero_header("Phantom Lancer"))
W(ability("Illusory Armaments"))
W(ul_open())
W(li("Min Damage increase changed from 2% per 3 level ups to 2% per 3 levels ", t("MISC")))
W(ul_close())
W(subnote("This means two things: bonus damage increases 1 level earlier (on levels 3/6/9... instead of 4/7/10...) and Phantom Lancer will gain one more damage increase on level 30"))

# Phoenix
W(hero_header("Phoenix"))
W(ul_open())
W(li("Removed Blinding Sun innate ability", t("MISC")))
W(ul_close())
W(ability("Dying Light"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Phoenix deals 4% of its missing health as magic damage to all enemies in a 400 radius every second. Damage tick rate: 0.2s", t("MISC")))
W(li("This effect is also present during Supernova", t("MISC")))
W(li("Damage is calculated as if Phoenix was still present with the same health and health regen it had at the moment of the cast", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.5% Blinding Sun Miss Chance replaced with +1% Dying Light Missing Health as Damage", t("REWORK")))
W(ul_close())

# Primal Beast
W(hero_header("Primal Beast"))
W(ability("Colossal"))
W(ul_open())
W(li("Innate ability reworked", t("MISC")))
W(li("Primal Beast has 10% base Slow Resistance and gains +0.5% Area of Effect and +1% Slow Resistance for every 100 Max Health", t("MISC")))
W(ul_close())
W(ability("Pulverize"))
W(ul_open())
W(li("AoE Radius decreased from 600 to 575", b(600, 575)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 25 Talent Cannot Be Slowed Or Rooted During Trample replaced with Colossal 2x Bonuses During Trample", t("NERF")))
W(ul_close())

# Puck
W(hero_header("Puck"))
W(ability("Puckish"))
W(ul_open())
W(li("Health/Mana Restore rescaled from 10 + 2% to 3% ", t("REWORK")))
W(ul_close())
W(subnote("Also unified into a single value"))
W(ul_open())
W(li("Spell Dodge Multiplier decreased from 3.5x to 3x", t("NERF")))
W(ul_close())
W(ability("Illusory Orb"))
W(ul_open())
W(li("Now has curved vector targeting by default", t("REWORK")))
W(li("Can be put on alt-cast to to launch the orb straight", t("MISC")))
W(li("Speed increased from 550 to 750", b(550, 750)))
W(li("Now additionally deals 3% of orb's Impact Damage every 0.5s in its AoE", t("REWORK")))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(ability("Graft Flesh"))
W(ul_open())
W(li("No longer levels with Dismember", t("NERF")))
W(li("Permanent Bonus Strength rescaled from 1.1/1.4/1.7/2.0 to 1.6", b([1.1, 1.4, 1.7, 2.0], 1.6)))
W(ul_close())
W(ability("Rot"))
W(ul_open())
W(li("No longer has a separate value for incoming heal reduction ", t("NERF")))
W(ul_close())
W(subnote("Still reduces incoming heals due to Health Restoration changes"))

# Pugna
W(hero_header("Pugna"))
W(ul_open())
W(li("Base Movement Speed decreased from 330 to 325", b(330, 325)))
W(ul_close())
W(ability("Oblivion Savant"))
W(ul_open())
W(li("Now also increases Pugna's Spell Amplification by 1.5% per destroyed tower", t("REWORK")))
W(ul_close())
W(ability("Nether Ward"))
W(ul_open())
W(li("Damage source changed from Nether Ward to the caster", t("MISC")))
W(ul_close())

# Queen of Pain
W(hero_header("Queen of Pain"))
W(ability("Scream Of Pain"))
W(ul_open())
W(li("Damage increased from 75/150/225/300 to 90/175/260/345", b([75, 150, 225, 300], [90, 175, 260, 345])))
W(li("25% of the damage dealt to heroes with this ability is reflected back to her ", t("MISC")))
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
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Storm Surge"))
W(ul_open())
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("While Eye of the Storm is active, Storm Surge's strike chance is 2x as high, strike cooldown is decreased by 2s, and lightning strikes all enemies within Eye of the Storm's radius", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +10% Spell Lifesteal replaced with +4 Armor", t("REWORK")))
W(li("Level 20 Talent Storm Surge Slow and Damage increased from +25% to +30%", b(25, 30)))
W(ul_close())

# Riki
W(hero_header("Riki"))
W(ability("Innate Backstab"))
W(ul_open())
W(li("Agility Multiplier changed from 0.6 + 0.05 per level up to 0.55 + 0.05 per level ", t("MISC")))
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
W(ability("Tricks Of The Trade"))
W(ul_open())
W(li("Aghanim's Scepter bonus Cast Range increased from +300 to +500", b(300, 500)))
W(ul_close())

# Ringmaster
W(hero_header("Ringmaster"))
W(ability("Dark Carnival Souvenirs"))
W(ul_open())
W(li("Pool of souvenirs now always consists of Funhouse Mirror, Strongman Tonic, Unicycle and Whoopee Cushion", t("REWORK")))
W(ul_close())
W(ability("The Box"))
W(ul_open())
W(li("Targeted unit is no longer stunned for 0.5 seconds when placed in a box", t("NERF")))
W(li("Radius and Aghanim's Scepter's Explosion Radius now affected by AoE bonuses", t("REWORK")))
W(ul_close())
W(ability("Impalement"))
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
W(li("Base Damage increased by 1", bstat_h("Rubick", "AttackDamageMin", "7.40c", 1), extra=note_box("From 29 to 30")))
W(li("Damage at level 1 increased from 49–55 to 50–56", t("BUFF")))
W(li("Removed Might and Magus innate ability", t("MISC")))
W(ul_close())
W(ability("Curiosity"))
W(ul_open())
W(li("New innate ability. Passive, can't be leveled up", t("NERF")))
W(li("Rubick gains 1 stack of Curiosity per level, each granting him +1 base damage, +0.3% Buff/Debuff Duration, and +2 Area of Effect bonus. If Rubick sees an enemy Hero cast an ability within 1200 distance of him, he gains 2 Curiosity for 20 seconds. If an enemy that currently provides temporary Curiosity dies within 3s after taking damage from Rubick, he gains 1 Curiosity permanently", t("MISC")))
W(ul_close())
W(ability("Telekinesis"))
W(ul_open())
W(li("Aghanim's Shard throw distance bonus changed from 35% to 225", b(35, 225)))
W(ul_close())
W(ability("Fade Bolt"))
W(ul_open())
W(li("Now reduces both spell and attack damage by default", t("REWORK")))
W(li("Damage Reduction rescaled from 5/15/25/35% to 6/12/18/24%", b([5, 15, 25, 35], [6, 12, 18, 24])))
W(ul_close())
W(ability("Spell Steal"))
W(ul_open())
W(li("No longer grants 10/20/30% Debuff Amplification", t("NERF")))
W(li("Stolen spells now have their cooldown decreased by 10/20/30%", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.25% Might and Magus Damage/Resistance replaced with +200 Health", t("REWORK")))
W(li("Level 10 Talent +165 Telekinesis Landing Damage replaced with -2s Telekinesis Cooldown", t("REWORK")))
W(li("Level 15 Talent +20% Fade Bolt Damage Reduction replaced with -3s Fade Bolt Cooldown", t("REWORK")))
W(li("Level 15 Talent -25% Stolen Spells Cooldown replaced with -50% Stolen Spells Mana Cost", t("REWORK")))
W(li("Level 20 Talent -5s Telekinesis Cooldown replaced with Telekinesis Landing Deals 325 Damage (now this talent applies damage to the thrown enemy as well) ", t("REWORK")))
W(li("It used to deal damage only in AoE, leaving the thrown enemy unharmed. Doesn't deal damage to thrown allies or self", t("MISC")))
W(li("Level 20 Talent -5s Fade Bolt Cooldown replaced with +12% Fade Bolt Damage Reduction", t("REWORK")))
W(li("Level 25 Talent +400 Telekinesis Land Distance replaced with 2x Curiosity Bonuses", t("REWORK")))
W(ul_close())

# Sand King
W(hero_header("Sand King"))
W(ability("Sandking Caustic Finale"))
W(ul_open())
W(li("No longer levels with Epicenter", t("NERF")))
W(li("Base Damage rescaled from 20/40/60/80 to 17 + 3 per level", b([20, 40, 60, 80], 17)))
W(li("Max Health Damage rescaled from 3/7/11/15% to 2.5% + 0.5% per level", b([3, 7, 11, 15], 2.5)))
W(li("Duration decreased from 4.5/5/5.5/6s to 4.5s", b([4.5, 5, 5.5, 6], 4.5)))
W(ul_close())
W(ability("Sandking Burrowstrike"))
W(ul_open())
W(li("Cast Range increased from 525/600/675/750 to 550/625/700/775", b([525, 600, 675, 750], [550, 625, 700, 775])))
W(li("Sand King now immediately re-gains invisibility if the Burrowstrike ends within Sand Storm's AoE", t("REWORK")))
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
W(li("Damage amplification changed from 2.5% to 1.9% + 0.1% per level", b(2.5, 1.9)))
W(ul_close())
W(ability("Disruption"))
W(ul_open())
W(li("Can now target Spirit Bear", t("REWORK")))
W(ul_close())
W(ability("Disseminate"))
W(ul_open())
W(li("Shared Damage rescaled from 20/25/30/35% to 16/24/32/40%", b([20, 25, 30, 35], [16, 24, 32, 40])))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent +150 Demonic Purge Damage replaced with -20s Demonic Purge Cooldown", t("REWORK")))
W(li("Level 25 Talent -30s Demonic Purge Cooldown replaced with Demonic Purge Applies Shadow Poison ", t("REWORK")))
W(li("1 stack per second over the debuff duration", t("MISC")))
W(ul_close())

# Shadow Fiend
W(hero_header("Shadow Fiend"))
W(ability("Necromastery"))
W(ul_open())
W(li("No longer levels with Requiem of Souls", t("NERF")))
W(li("Damage per soul rescaled from 1/2/3/4 to 1.35 + 0.15 damage per level", b([1, 2, 3, 4], 1.35)))
W(li("Base Max Souls decreased from 20/22/24/26 to 20", b([20, 22, 24, 26], 20)))
W(ul_close())
W(ability("Shadowraze"))
W(ul_open())
W(li("Damage decreased from 90/160/230/300 to 85/150/215/280", b([90, 160, 230, 300], [85, 150, 215, 280])))
W(li("Now damage is increased by 3 per Necromastery soul", t("REWORK")))
W(li("Aghanim's Shard now also applies a stacking 12% slow debuff to enemies hit", t("REWORK")))
W(ul_close())
W(ability("Frenzy"))
W(ul_open())
W(li("No longer requires 5 souls to cast", t("NERF")))
W(li("Instead, Shadow Fiend gains souls from surrounding enemies", t("MISC")))
W(li("Shadow Fiend gains souls from 2 enemies in a 600 radius every 0.5s, prioritizing heroes. Each individual enemy can provide souls once, with creeps giving 1 soul and heroes providing 3. Can collect souls from up to 4/6/8/10 enemies. After the effect is over, Shadow Fiend loses the souls whose owners are still alive, retaining the rest for 8s ", t("MISC")))
W(ul_close())
W(subnote("The enemy threshold doesn't limit an amount of souls collected, and limits only the amount of enemies affected. So, at the limit of 10, you can collect souls from 5 heroes and 5 creeps gaining 20 souls. 10 Dummy Targets in Hero Demo mode will provide 30 souls"))
W(ul_open())
W(li("Bonus Attack Speed decreased from 40/55/70/85 to 35/50/65/80", b([40, 55, 70, 85], [35, 50, 65, 80])))
W(li("Bonus Move Speed decreased from 5/7/9/11% to 4/6/8/10%", b([5, 7, 9, 11], [4, 6, 8, 10])))
W(ul_close())
W(ability("Requiem"))
W(ul_open())
W(li("Now can't use more than 20 souls per cast", t("NERF")))
W(li("Aghanim's Scepter no longer has a damage penalty on the returning Requiem of Souls", t("NERF")))
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
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(li("Now adds a chicken illusion per 5 levels", t("REWORK")))
W(li("Now also provides bonus movement speed equal to 5% + 5% per 5 levels", t("REWORK")))
W(ul_close())
W(ability("Urnaconda"))
W(ul_open())
W(li("New ability granted by Aghanim's Shard", t("MISC")))
W(li("Throws a jar at a location, dealing 275 damage to all enemies in a 225 radius and creating a Massive Serpent Ward that lasts for 15s. The ward has 4x health and damage of the normal Serpent Wards. Cooldown: 50s. Mana Cost: 115. Cast Range: 650", t("MISC")))
W(ul_close())

# Silencer
W(hero_header("Silencer"))
W(ul_open())
W(li("Base Movement Speed increased from 290 to 300", b(290, 300)))
W(li("Reworked Brain Drain ability into a new innate", t("MISC")))
W(ul_close())
W(ability("Brain Drain"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("Silencer takes less damage from and deals more damage to silenced targets. Damage modifier is 5% + 0.5% per level for both reduction and amplification", t("MISC")))
W(li("If an enemy hero dies within 925 range of Silencer or was debuffed by Silencer at the time of death, Silencer permanently steals 1 Intelligence from them. If the victim was silenced, an extra 1 point of Intelligence will be stolen", t("MISC")))
W(ul_close())
W(ability("Curse Of The Silent"))
W(ul_open())
W(li("No longer has 1.25x slow and damage multiplier against silenced enemies", t("NERF")))
W(ul_close())
W(ability("Glaives Of Wisdom"))
W(ul_open())
W(li("Mana Cost decreased from 14/16/18/20 to 12/14/16/18", b([14, 16, 18, 20], [12, 14, 16, 18], l=True)))
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Increases Int Steal by 1 and causes Glaives to bounce once to a random enemy within 450 range", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +0.25 Arcane Curse Silenced Multiplier replaced with +7% Suffer In Silence Damage", t("REWORK")))
W(li("Level 25 Talent Glaives of Wisdom Damage increased from +25% to +30%", b(25, 30)))
W(li("Level 25 Talent 2 Arcane Curse charges replaced with +2s Global Silence Duration", t("REWORK")))
W(ul_close())

# Skywrath Mage
W(hero_header("Skywrath Mage"))
W(ul_open())
W(li("Removed Ruin and Restoration innate ability", t("MISC")))
W(ul_close())
W(ability("Shield Of The Scion"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("Whenever Skywrath Mage deals magical damage with his abilities to an enemy hero, he gains a magic damage barrier equal to 13.5 + 1.5 per level for 12s. Each instance stacks independently", t("MISC")))
W(ul_close())
W(ability("Concussive Shot"))
W(ul_open())
W(li("Now considers Spirit Bear as a true hero for prioritization. Creep Heroes are now considered as secondary targets", t("REWORK")))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ability("Seaborn Sentinel"))
W(ul_open())
W(li("No longer levels with Corrosive Haze", t("NERF")))
W(li("Bonus HP Regen changed from 2.5/5/7.5/10 to 1.75 + 0.25 per level", b([2.5, 5, 7.5, 10], 1.75)))
W(li("Aghanim's Scepter Bonus HP Regen decreased from +22 to +20", b(22, 20)))
W(li("Bonus Armor changed from 3/4/5/6 to 1.8 + 0.2 per level", b([3, 4, 5, 6], 1.8)))
W(li("Aghanim's Scepter Bonus Armor decreased from +10 to +8", b(10, 8)))
W(li("Flat 8/16/24/32 bonus damage replaced with 11.4% bonus attack damage + 0.6% per level", t("REWORK")))
W(ul_close())
W(ability("Sprint"))
W(ul_open())
W(li("Slardar now has 100% slow resistance for the first 2.5s of Guardian Sprint. This bonus fades to 0 over the remaining duration", t("REWORK")))
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
W(li("Duration changed from 15s + 2.5s per level up to 12.5s + 2.5s per level ", t("MISC")))
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
W(li("Now also modifies incoming healing ", t("REWORK")))
W(ul_close())
W(subnote("As a result of Health Restoration changes"))

# Snapfire
W(hero_header("Snapfire"))
W(ul_open())
W(li("Removed Buckshot innate ability", t("MISC")))
W(ul_close())
W(ability("Boomstick"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("Snapfire deals more damage with her attacks and abilities, the closer she is to her target. Min Damage Amp is 0% at a distance of 495 + 5 per level. Max Damage Amp is 35% damage amp at a distance of 50 + 5 per level", t("MISC")))
W(ul_close())
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
W(li("No longer levels with Assassinate", t("NERF")))
W(li("No longer increases attack range", t("NERF")))
W(li("Now increases damage from Sniper's attacks by 1.5% + 0.05% per level for every 100 units of distance between him and the target", t("REWORK")))
W(li("Also affects attack damage from Assassinate", t("MISC")))
W(ul_close())
W(ability("Take Aim"))
W(ul_open())
W(li("Now passively grants 160/240/320/400 attack range", t("REWORK")))
W(li("Active Bonus Attack Range rescaled from 100/150/200/250 to 75/150/225/300", b([100, 150, 200, 250], [75, 150, 225, 300])))
W(ul_close())
W(ability("Assassinate"))
W(ul_open())
W(li("No longer amplifies attack damage to 100/110/120%", t("NERF")))
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
W(li("Damage changed from 25 + 2 per level up to 23 + 2 per level ", t("MISC")))
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
W(ul_open())
W(li("Removed Herd Mentality innate ability", t("MISC")))
W(ul_close())
W(ability("Bull Rush"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("Spirit Breaker gains bonus Movement Speed whenever he stuns an enemy. Effect depends on the unit type: stunning a hero will provide a 8% bonus for 2s, while other units provide 2% for 1s", t("MISC")))
W(li("Effects from multiple stuns stack and have independent durations. Bull Rush duration is paused during Charge of Darkness, but it can still gain new stacks. This effect allows Spirit Breaker to go over the max movement speed limit", t("MISC")))
W(ul_close())
W(ability("Charge Of Darkness"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Greater Bash"))
W(ul_open())
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Increases knockback by roughly 30%. If a knocked-back enemy collides with another enemy, the second enemy is also bashed, and the original target takes 25% of Spirit Breaker's Greater Bash damage again", t("MISC")))
W(li("This effect is applied to Charge of Darkness and Nether Strike as well, since those abilities use Greater Bash", t("MISC")))
W(li("Creeps take 25% damage of repeated damage", t("MISC")))
W(li("Bodies of killed units keep flying and pushing enemies", t("MISC")))
W(ul_close())
W(ability("Planar Pocket"))
W(ul_open())
W(li("Now granted by Aghanim's Shard", t("REWORK")))
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
W(li("Leveling up Ball Lightning no longer grants 3 Galvanized charges", t("NERF")))
W(ul_close())
W(ability("Static Remnant"))
W(ul_open())
W(li("Remnants now spawn at Storm Spirit's location and move at 300 speed to the target location", t("REWORK")))
W(ul_close())

# Sven
W(hero_header("Sven"))
W(ul_open())
W(li("Base strength increased from 23 to 24", b(23, 24)))
W(li("Damage at level 1 increased from 60–62 to 61–63", t("BUFF")))
W(li("Removed Vanquisher innate ability", t("MISC")))
W(ul_close())
W(ability("Wrath Of God"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Increases attack damage Sven gains per point of Strength by 0.08 + 0.02 per level. Disabled by Break", t("MISC")))
W(ul_close())
W(ability("Warcry"))
W(ul_open())
W(li("Aghanim's Shard reworked ", t("MISC")))
W(ul_close())
W(subnote("No longer provides a passive aura"))
W(ul_open())
W(li("Makes Warcry undispellable and increases radius from 700 to 900. Warcry provides a 300 physical damage barrier and an additional +3% movespeed bonus when active", b(700, 900)))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +10% Vanquisher Bonus Damage replaced with +20% God's Strength Slow Resistance", t("REWORK")))
W(li("Level 20 Talent +20% God's Strength Slow Resistance replaced with -25% Storm Hammer Cooldown and Mana Cost", t("REWORK")))
W(ul_close())

# Techies
W(hero_header("Techies"))
W(ability("M.A.D."))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("Increases mana regen by a portion of Techies' max mana equal to 0.08% + 0.02% per level", t("MISC")))
W(li("When Techies die, they leave behind a barrel that explodes after 1.5s, dealing magical damage equal to 50 + 30% of their max mana to enemies in a 400 area of effect. The barrel provides 400 obstructed vision until it explodes", t("MISC")))
W(li("Upgraded with Aghanim's Shard", t("MISC")))
W(li("Increases mana to damage by 10%. Adds an active component. Techies plant the M.A.D. barrel, and detonate it later by using a sub-ability. The M.A.D. barrel is invisible and can be destroyed before the detonation process begins. Detonating the barrel makes it visible and immortal, and then it explodes after the same 1.5s delay. Only one M.A.D. can exist via the active cast at one time. Barrel Health: 200. Cast Range: 450. No Mana Cost. Cooldown: 30s. Cast Point: 1s", t("MISC")))
W(ul_close())
W(ability("Reactive Tazer"))
W(ul_open())
W(li("Can now always be cast on allies", t("REWORK")))
W(li("Cast Range increased from 500 to 600", b(500, 600)))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Suicide"))
W(ul_open())
W(li("Now deals its self damage before damaging enemies", t("REWORK")))
W(li("Techies are now rooted and disarmed instead of self-stunned during Blast Off's leap animation", t("REWORK")))
W(ul_close())
W(ability("Land Mines"))
W(ul_open())
W(li("Damage source changed from Proximity Mines to the caster", t("MISC")))
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
W(li("Removed Third Eye innate ability", t("MISC")))
W(ul_close())
W(ability("Inner Peace"))
W(ul_open())
W(li("New innate ability, improves with Templar Assassin's level", t("MISC")))
W(li("After remaining stationary for 0.25s, Templar Assassin begins meditating, gaining bonus health regen and mana regen. Bonuses linearly increase from 0 up to their maximum, which is reached after 2.05s - 0.05s per level. Moving from the current position or taking damage from an enemy resets regen bonuses. Max Health Regen is 2.7 + 0.3 per level. Max Mana Regen is 2.2 + 0.2 per level", t("MISC")))
W(ul_close())
W(ability("Refraction"))
W(ul_open())
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Increases bonus damage by 30 and allows Refraction to be cast while disabled", t("MISC")))
W(ul_close())
W(ability("Meld"))
W(ul_open())
W(li("Now, if the attack that broke Meld splits with Psi Blades, Bonus Damage and Armor Reduction are now applied to all affected enemies", t("REWORK")))
W(ul_close())
W(ability("Psionic Trap"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("When activated, Traps now also silence enemies from 0.25s up to 3s depending on the trap charge", t("REWORK")))
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
W(li("Base Armor increased by 1", bstat_h("Terrorblade", "ArmorPhysical", "7.40c", 1), extra=note_box("From 5 to 6")))
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
W(li("Removed Blubber innate ability", t("MISC")))
W(ul_close())
W(ability("Leviathan's Catch"))
W(ul_open())
W(li("New Innate Ability. Passive", t("MISC")))
W(li("Whenever an enemy hero dies while affected by any Tidehunter's debuff or is killed by him, they drop a fish. Tidehunter can eat the fish to grow in size and permanently gain 3 Max Health, 2 Attack Range and 1 Bonus Damage Block. Tidehunter automatically eats a fish on every level up", t("MISC")))
W(li("Bonus Damage Block is only applied if there is a source of damage block being applied to an incoming physical attack", t("MISC")))
W(li("The fish flies 400 units towards Tidehunter upon spawning, stays in the world indefinitely and can be destroyed by an attack from Tidehunter's enemies", t("MISC")))
W(ul_close())
W(ability("Anchor Smash"))
W(ul_open())
W(li("Radius changed from 375 to 225 + Tidehunter's Attack Range", b(375, 225)))
W(ul_close())
W(ability("Kraken Shell"))
W(ul_open())
W(li("Now applies a strong dispel to Tidehunter if he takes more than 600/550/500/450 damage within 7 seconds", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent Blubber effect triggers Anchor Smash replaced with Kraken Shell Cleanse triggers Anchor Smash", t("REWORK")))
W(ul_close())

# Timbersaw
W(hero_header("Timbersaw"))
W(ability("Exposure Therapy"))
W(ul_open())
W(li("No longer levels with Chakram", t("NERF")))
W(li("Mana gain per tree destroyed changed from 4/6/8/10 to 3.75 + 0.25 per level", b([4, 6, 8, 10], 3.75)))
W(ul_close())

# Tinker
W(hero_header("Tinker"))
W(ul_open())
W(li("Base health regen increased from 0 to 0.5", b(0, 0.5)))
W(li("Base Movement Speed decreased from 310 to 305", b(310, 305)))
W(li("Removed Defense Matrix ability", t("MISC")))
W(ul_close())
W(ability("Laser"))
W(ul_open())
W(li("Aghanim's Scepter no longer adds bounces", t("NERF")))
W(ul_close())
W(ability("March Of The Machines"))
W(ul_open())
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Robots apply a non-stacking heal over time of 35 health per second to allies they come through. Heal duration: 4 seconds", t("MISC")))
W(ul_close())
W(ability("Deploy Turrets"))
W(ul_open())
W(li("New ability that replaces Defense Matrix", t("MISC")))
W(li("After a 0.5s delay, airdrops a group of three uncontrollable turrets at the target 250 radius area, dealing 40/80/120/160 magical damage, destroying trees and pushing away enemies by 100 units and Tinker by 350. Turrets seek enemy heroes within 650/700/750/800 range and shoot missiles in their direction every 1.5 seconds. The missile deals 20/40/60/80 magical damage to the enemy it hits and 50% of the damage to other enemies within 200 AoE. Each turret has 40/80/120/160 health and exists for 4.5 seconds", t("MISC")))
W(li("Each of three turrets activates with a small delay after the previous one, activating 0.1s, 0.6s, and 1.1s after deployment", t("MISC")))
W(li("The missile flies in a forward direction and can be dodged by moving out of its way", t("MISC")))
W(li("Turrets target heroes only, but missiles can hit creeps on their way", t("MISC")))
W(li("Turrets prioritize the same hero until they are out of reach", t("MISC")))
W(li("Splash damage is not dealt to the hit unit itself", t("MISC")))
W(li("Gold Bounty: 5/10/15/20. XP Bounty: 5/10/15/20. Turn Rate: 0.55. Missile Speed: 1200. Missile Flight Distance: 650/700/750/800", t("MISC")))
W(li("Cast Range: 600. Mana Cost: 100/120/140/160. Cooldown: 24/22/20/18s. Cast Point: 0.1s", t("MISC")))
W(li("Upgraded with Aghanim's Scepter", t("MISC")))
W(li("Turrets activate 0.3s faster, and fire missiles 20% faster, which results in firing one additional volley of missiles", t("MISC")))
W(ul_close())
W(ability("Rearm"))
W(ul_open())
W(li("Cooldown decreased from 7/6/5s to 5.5/5/4.5s", b([7, 6, 5], [5.5, 5, 4.5], l=True)))
W(ul_close())
W(ability("Warp Grenade"))
W(ul_open())
W(li("Teleport distance now depends on Warp Flare cast range and scales with distance from Tinker, so that nearby enemies are teleported further than far enemies", t("REWORK")))
W(li("Max teleportation distance is 60% of Warp Flare's cast range which decreases down to 0 at the max cast range (700 by default)", t("MISC")))
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
W(ul_open())
W(li("Removed Craggy Exterior innate ability", t("MISC")))
W(ul_close())
W(ability("Insurmountable"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Slow Resistance now also applies to Attack Speed Slows. Tiny gains Slow Resistance equal to 20% of his Strength and Status Resistance equal to 10% of his Strength", t("REWORK")))
W(ul_close())
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
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Toss Tree"))
W(ul_open())
W(li("No longer applies a slow on the tossed tree by default", t("NERF")))
W(ul_close())
W(ability("Grow"))
W(ul_open())
W(li("Now upgraded with Aghanim's Shard", t("REWORK")))
W(li("Thrown trees and tossed units deal 20% more damage in their AoE, have +125 radius, and apply a 25% movement slow and a 45 attack speed slow to all units in the AoE of Toss, Tree Throw, and Tree Volley for 2.5s", t("MISC")))
W(li("Damage is not increased for the Tossed unit itself", t("BUFF")))
W(ul_close())
W(ability("Tree Channel"))
W(ul_open())
W(li("Now uses the bonus damage value of Tree Throw and bonuses from Aghanim's Shard", t("REWORK")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent Avalanche Cast Range decreased from +200 to +150", b(200, 150)))
W(li("Level 15 Talent Avalanche Damage decreased from +100 to +90", b(100, 90)))
W(ul_close())

# Treant Protector
W(hero_header("Treant Protector"))
W(ability("Natures Guise"))
W(ul_open())
W(li("Cooldown changed from 35s - 1s per level up to 36s -1s per level ", t("MISC")))
W(ul_close())
W(subnote("Effective values are not changed"))
W(ability("Living Armor"))
W(ul_open())
W(li("Mana Cost increased from 40/45/50/55 to 65/70/75/80", b([40, 45, 50, 55], [65, 70, 75, 80], l=True)))
W(li("Max Damage Blocked decreased from 120 to 60/80/100/120", b(120, [60, 80, 100, 120])))
W(li("Damage Block Decrease improved from 35/30/25/20 to 20", b([35, 30, 25, 20], 20)))
W(ul_close())
W(ability("Eyes in the Forest"))
W(ul_open())
W(li("Charge Restore Time increased from 55s to 135s", b(55, 135, l=True)))
W(li("Duration increased from 300s to 360s", b(300, 360)))
W(li("Max Charges decreased from 3 to 2", b(3, 2)))
W(ul_close())

# Troll Warlord
W(hero_header("Troll Warlord"))
W(ability("Switch Stance"))
W(ul_open())
W(li("Troll Warlord gains 1 armor per 30 bonus attack speed", t("MISC")))
W(ul_close())
W(ability("Berserkers Rage"))
W(ul_open())
W(li("No longer provides +3/4/5/6 Bonus Armor while in melee form", t("NERF")))
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
W(li("No longer levels with Walrus Punch!", t("NERF")))
W(li("Attack Speed Slow rescaled from 20/40/60/80 to 17 + 3 per level", b([20, 40, 60, 80], 17)))
W(li("Now only affects enemy heroes", t("REWORK")))
W(ul_close())
W(ability("Tag Team"))
W(ul_open())
W(li("Now always a basic ability for Tusk", t("REWORK")))
W(ul_close())
W(ability("Ice Shards"))
W(ul_open())
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())
W(ability("Drinking Buddies"))
W(ul_open())
W(li("Now granted by Aghanim's Shard", t("REWORK")))
W(li("Tusk reaches out to tag an allied unit, pulling them closer. Once tagged, both Tusk and his tagged ally gain 25% bonus movement speed and 10 bonus armor for 6s. Can be put on alt-cast to only pull Tusk towards his ally with 50% reduced cast range. Cast Range: 1000. Mana Cost: 80. Cooldown: 14s", t("MISC")))
W(li("No longer provides 20/50/80/110 bonus attack damage", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 20 Talent -6s Ice Shards Cooldown replaced with -6s Snowball Cooldown", t("REWORK")))
W(li("Level 25 Talent -8s Snowball Cooldown replaced with Ice Shards Slow by 50% and Deal 110 DPS (only affects enemies trapped inside)", t("REWORK")))
# Underlord
W(hero_header("Underlord"))
W(ability("Raid Boss"))
W(ul_open())
W(li("No longer levels with Fiend's Gate", t("NERF")))
W(li("Damage Reduction rescaled from 4/6/8/10% to 3.7% + 0.3% per level", t("REWORK")))
W(li("Movement Speed bonus rescaled from 11/14/17/20% to 9.5% + 0.5% per level", t("REWORK")))
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
W(ul_close())

# Undying
W(hero_header("Undying"))
W(ul_open())
W(li("Base Agility increased from 10 to 13", b(10, 13)))
W(li("Base Armor decreased by 1", bstat_h("Undying", "ArmorPhysical", "7.40c", -1), extra=note_box("From 1 to 0")))
W(ul_close())
W(ability("Flesh Golem"))
W(ul_open())
W(li("Attacks now spawn the current level of Tombstone Zombie", t("REWORK")))
W(ul_close())

# Vengeful Spirit
W(hero_header("Vengeful Spirit"))
W(ul_open())
W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
W(li("Base Attack Time improved from 1.7s to 1.5s", b(1.7, 1.5)))
W(ul_close())
W(ability("Retribution"))
W(ul_open())
W(li("Now also makes Vengeful Spirit to gain benefits of both melee and ranged attacks", t("REWORK")))
W(li("Now killer's icon is shown as a buff on Vengeful Spirit to know who to hate", t("REWORK")))
W(ul_close())
W(ability("Vengeance Aura"))
W(ul_open())
W(li("Now provides 1.2x the bonus for Vengeful Spirit herself", t("REWORK")))
W(li("Aghanim's Scepter upgrade no longer refreshes ability cooldowns on activating", t("NERF")))
W(li("Aghanim's Scepter now increases self-bonus up to 1.3x", t("REWORK")))
W(li("Aghanim's Scepter illusion is now fully affected by Vengeance Aura's bonus", t("REWORK")))
W(li("Aghanim's Scepter illusion damage taken decreased from 115% to 100%", b(115, 100)))
W(ul_close())

# Venomancer
W(hero_header("Venomancer"))
W(ul_open())
W(li("Removed Septic Shock innate ability", t("MISC")))
W(ul_close())
W(ability("Poison Sting"))
W(ul_open())
W(li("Now an innate ability", t("REWORK")))
W(li("Imbues Venomancer's attack with poison, which deals damage per second equal to 9 + 1 per level and slows movement by 10%. Duration: 4.5s + 0.5s per level", t("MISC")))
W(ul_close())
W(ability("Venomous Gale"))
W(ul_open())
W(li("Aghanim's Shard upgrade reworked", t("MISC")))
W(li("Increases cast range and projectile speed by 25%. Creates 2 Plague Wards around every enemy hero hit", t("MISC")))
W(ul_close())
W(ability("Snakebite"))
W(ul_open())
W(li("New Basic Ability", t("MISC")))
W(li("Venomancer summons a Spawn of Aktok to sink its fangs into an enemy, dealing 40/60/80/100 magic damage and applying a deadly toxin which does 20/25/30/35 magical damage per second for 6 seconds. When the target attacks, they take the initial magic damage again. Cast Range: 600. Mana Cost: 70/80/90/100. Cooldown: 20/18/16/14s", t("MISC")))
W(ul_close())
W(ability("Noxious Plague"))
W(ul_open())
W(li("Ability reworked", t("MISC")))
W(li("No longer has AoE effect, now affects only the host", t("NERF")))
W(li("Now when the plague spreads, it also carries all debuffs placed by Venomancer", t("REWORK")))
W(li("Doesn't stack. Applying plague to an already plague-infected unit will deal projectile damage again, but won't affect the remaining debuff duration. Duration of carried debuffs is fixed and cannot be altered with Status Resistance or Debuff Amplification", t("NERF")))
W(li("Mana Cost decreased from 200/300/400 to 200/250/300", b([200, 300, 400], [200, 250, 300], l=True)))
W(li("Duration decreased from 5s to 4s", b(5, 4)))
W(li("Initial Damage decreased from 200/300/400 to 150/200/250", b([200, 300, 400], [150, 200, 250])))
W(li("Initial Damage is now non-lethal", t("REWORK")))
W(li("Now spreads a second time, but all spreads after the first one deal no initial damage", t("REWORK")))
W(li("Spread Radius decreased from 800 to 700", b(800, 700)))
W(li("Max HP as damage decreased from 3/4/5% to 2/3/4%", b([3, 4, 5], [2, 3, 4])))
W(li("Now upgraded with Aghanim's Scepter", t("REWORK")))
W(li("Decreases cooldown by 35s. Reduces Magic Resistance of affected units by 20% and allows additional spreads to deal initial damage", t("MISC")))
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
W(li("Aghanim's Scepter now also gradually increases Corrosive Skin's magic resistance and damage per second while he is in Nethertoxin, up to 50% increased effect after 4s", t("REWORK")))
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
W(ul_open())
W(li("Removed Lurker innate ability", t("MISC")))
W(ul_close())
W(ability("Silent As The Grave"))
W(ul_open())
W(li("Now innate ability. Active", t("REWORK")))
W(li("Visage gains flying movement and 12% bonus movement speed for 20s. Upon attacking or casting, he loses both effects, but he and his familiars gain 10% attack damage bonus for 2 seconds", t("MISC")))
W(li("Mana Cost decreased from 115 to 50", b(115, 50, l=True)))
W(li("Cooldown changed from 45s to 45.75s - 0.75s per level", b(45, 45.75, l=True)))
W(li("Upgraded with Aghanim's Scepter", t("MISC")))
W(li("Increases bonus movement speed by 12%, bonus damage by 10%, bonus damage duration by 2s, and flight duration by 10s. While flight is active, Silent as the Grave grants invisibility to Visage and his familiars", t("MISC")))
W(li("Invisibility for Visage and each familiar are not connected", t("MISC")))
W(ul_close())
W(ability("Summon Familiars"))
W(ul_open())
W(li("Cooldown decreased from 130/120/110s to 120/110/100s", b([130, 120, 110], [120, 110, 100], l=True)))
W(li("Familiar Health rescaled from 500/600/700 to 450/600/750", b([500, 600, 700], [450, 600, 750])))
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
W(li("Base Damage decreased by 4", bstat_h("Void Spirit", "AttackDamageMin", "7.40c", -4), extra=note_box("From 24 to 20")))
W(li("Damage at level 1 unchanged due to innate ability changes", t("MISC")))
W(ul_close())
W(ability("Intrinsic Edge"))
W(ul_open())
W(li("Now also increases Void Spirit's attack damage per point of attribute by 15%", t("REWORK")))
W(li("Increase is multiplicative, so it's increased from 0.45 to 0.5175", b(0.45, 0.5175)))
W(li("The result of these changes:", t("MISC")))
W(li("Damage at level 1 is unchanged at 52–56", t("MISC")))
W(li("Damage gain per level increased from 3.6 to 4.1", b(3.6, 4.1)))
W(li("Damage at level 30 increased from 174–178 to 192–196", t("BUFF")))
W(li("Secondary bonuses increased from 25% to 30%", b(25, 30)))
W(li("No longer provides increased Armor or Magic Resistance", t("NERF")))
W(li("Now provides increased Attack Speed per point of Agility", t("REWORK")))
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
W(li("No longer levels with Chaotic Offering", t("NERF")))
W(li("Minor Imp Health rescaled from 50/130/210/290 to 5 + 15 per level", b([50, 130, 210, 290], 5)))
W(li("Minor Imp Explosion Damage rescaled from 25/70/115/160 to 20 + 20 per 3 hero levels", b([25, 70, 115, 160], 20)))
W(li("Minor Imp movement speed rescaled from 300/315/330/345 to 297 + 3 per level", b([300, 315, 330, 345], 297)))
W(li("Minor Imp attack damage rescaled from 10-11/14-15/18-19/22-23/26-27 to 20-21", t("REWORK")))
W(li("Aghanim's Shard now increases health of minor imps by 80 and explosion damage by 45 ", t("REWORK")))
W(ul_close())
W(subnote("Same values as before, but explicitly stated now"))

# Weaver
W(hero_header("Weaver"))
W(ul_open())
W(li("Removed Rewoven innate ability", t("MISC")))
W(ul_close())
W(ability("Threads Of Fate"))
W(ul_open())
W(li("New innate ability. Passive", t("MISC")))
W(li("After dealing damage to an enemy hero with an attack or ability, if Weaver remains within 700 range of them for 1.5s, he establishes a Thread of Fate that briefly slows movement of the enemy and ties them to Weaver. Each established thread of fate grants 10% bonus damage to Weaver. Threads last up to 6s and break if the distance is longer than 900. If the enemy dies with Thread of Fate established, the thread's bonuses linger for an additional 5s", t("MISC")))
W(li("Effects linger even if the enemy dies when the thread is about to be established", t("MISC")))
W(li("Movement slow is 100% for 0.2s", t("MISC")))
W(ul_close())
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
W(li("Removed Easy Breezy innate ability", t("MISC")))
W(ul_close())
W(ability("Tailwind"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Using an ability conjures a stacking Tailwind that gives Windranger a brief burst of movement speed. Movement speed bonus starts gradually fading halfway through Tailwind's duration. Movement Speed Bonus per stack: 35%. Duration: 2s", t("MISC")))
W(li("Passively increases Windranger's max movement speed to 600", t("MISC")))
W(li("Upgraded with Aghanim's Scepter", t("MISC")))
W(li("Attacks also grant Tailwind effect. Increases Tailwind duration to 3s and makes it undispellable", t("MISC")))
W(ul_close())
W(ability("Windrun"))
W(ul_open())
W(li("Movement Speed Bonus decreased from 60% to 50%", b(60, 50)))
W(li("Cooldown decreased from 15/14/13/12s to 14/13/12/11s", b([15, 14, 13, 12], [14, 13, 12, 11], l=True)))
W(li("No longer upgraded with Aghanim's Scepter", t("NERF")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10 Talent +4 All Attributes replaced with +0.75s Windrun Duration", t("REWORK")))
W(li("Level 15 Talent -2s Windrun Cooldown replaced with +40 Tailwind Max Movespeed", t("REWORK")))
W(li("Level 25 Talent Windrun Cannot be Dispelled replaced with Powershot Executes Enemy Heroes Under 15% Max HP (Execute Threshold ranges from 10-15% Max HP Based on channel time and reduces with each unit the arrow comes through)", t("NERF")))
W(ul_close())

# Winter Wyvern
W(hero_header("Winter Wyvern"))
W(ul_open())
W(li("Removed Eldwurm Scholar innate ability", t("MISC")))
W(ul_close())
W(ability("Eldwurms Edda"))
W(ul_open())
W(li("New innate ability", t("MISC")))
W(li("Winter Wyvern starts the game with Eldwurm's Edda item. After 10 minutes it can be consumed, increasing the current and maximum level of a basic ability by one. Also increases Winter Wyvern's Intelligence by 25% of its base value at the time of consumption", t("MISC")))
W(li("Level 5 values are automatically calculated by applying 50% of the difference in all values between levels 3 and 4, except for the mana cost. Mana cost is kept the same as level 4", t("MISC")))
W(ul_close())
W(ability("Arctic Burn"))
W(ul_open())
W(li("No longer has a one debuff per cast restriction on enemy heroes", t("NERF")))
W(li("Burn Duration decreased from 5s to 3s", b(5, 3)))
W(li("Movement Slow decreased from 16/24/32/40% to 15/20/25/30%", b([16, 24, 32, 40], [15, 20, 25, 30])))
W(ul_close())
W(ability("Cold Embrace"))
W(ul_open())
W(li("Aghanim's Shard reworked", t("MISC")))
W(li("Decreases cooldown by 4s. Allied units gain 60% bonus attack damage for 6s when emerging from the icy cocoon", t("MISC")))
W(ul_close())
W(ability("Winters Curse"))
W(ul_open())
W(li("Attack Speed rescaled from 65 to 50/65/80", b(65, [50, 65, 80])))
W(li("Maximum Duration rescaled from 4/5.5/7s to 6s", b([4, 5.5, 7], 6)))
W(li("Bonus Duration per hero decreased from 2s to 1.5s", b(2, 1.5)))
W(li("Bonus duration per hero can now be applied after the cast if an enemy hero becomes affected ", t("REWORK")))
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
W(li("Base Armor decreased by 1", bstat_h("Wraith King", "ArmorPhysical", "7.40c", -1), extra=note_box("From 1 to 0")))
W(ul_close())
W(ability("Vampiric Spirit"))
W(ul_open())
W(li("No longer levels with Reincarnation", t("NERF")))
W(li("Lifesteal changed from 10/20/30/40% to 14% + 1% per level", b([10, 20, 30, 40], 14)))
W(li("Wraith Duration changed from 3.5/4/4.5/5s to 4.25s + 0.25s per 6 levels ", b([3.5, 4, 4.5, 5], 4.25)))
W(ul_close())
W(subnote("Up to 5.5s at level 30. Also increased by 1s with Aghanim's Scepter"))
W(ul_open())
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
W(li("Aghanim's Shard reworked", t("MISC")))
W(li("Critical strikes curse their target, dealing 75% of the damage dealt again after a 3 second delay. Vampiric Spirit's lifesteal applies to the curse damage", t("MISC")))
W(ul_close())
W(ability("Reincarnation"))
W(ul_open())
W(li("Mana Cost decreased from 225 to 220/110/0", b(225, [220, 110, 0], l=True)))
W(li("Now spawns 2/3/4 per enemy hero within slow radius", t("REWORK")))
W(li("No longer upgraded with Aghanim's Shard", t("NERF")))
W(ul_close())

# Zeus
W(hero_header("Zeus"))
W(ul_open())
W(li("Base Strength increased from 19 to 21", b(19, 21)))
W(li("Base Damage increased by 1–3 ", bstat_h("Zeus", "AttackDamageMin", "7.40c", 1), extra=note_box("From 33 to 34")))
W(li("Damage spread increased from 8 to 10", b(8, 10)))
W(li("Damage at level 1 increased from 52–60 to 53–63", t("BUFF")))
W(li("Base Movement Speed decreased from 315 to 305", b(315, 305)))
W(li("Base Armor decreased by 1", bstat_h("Zeus", "ArmorPhysical", "7.40c", -1), extra=note_box("From 2 to 1")))
W(ul_close())
W(ability("Static Field"))
W(ul_open())
W(li("No longer levels with Thundergod's Wrath", t("NERF")))
W(li("Damage changed from 2.5/3/3.5/4% to 3.45% + 0.05% per level", b([2.5, 3, 3.5, 4], 3.45)))
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
W(ability("Thundergods Wrath"))
W(ul_open())
W(li("Now applies the True Sight before the damage and strikes even untargetable and still invisible enemies ", t("REWORK")))
W(ul_close())
W(subnote("It used to simply reveal invisible heroes without dealing damage to them. Now it will work similarly to Lightning Bolt, dealing damage even to units affected by Smoke of Deceit, Dark Willow's Shadow Realm, Phantom Assassin's Blur, Slark's Shadow Dance or Depth Shroud, etc."))
W(ul_open())
W(li("Vision and True Sight radius increased from 500 to 600", b(500, 600)))
W(ul_close())
W(ability("Cloud"))
W(ul_open())
W(li("Damage source changed from Nimbus to the caster", t("MISC")))
W(ul_close())
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent -0.4s Arc Lightning Cooldown replaced with -20% Arc Lightning Mana Cost/Cooldown", t("REWORK")))
W(li("Level 25 Talent +2% Static Field Damage replaced with 3 Heavenly Jump Charges", t("REWORK")))
W(ul_close())

write_footer()
save_html('patches/7.41.html')


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
W(li("Creep Bonus no longer works with illusions", t("NERF")))
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
W(ability("Chemical Rage"))
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
W(ability("Sleight of Fist"))
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
W(ability("Blade Dance"))
W(ul_open())
W(li("Damage reduced from 200% to 180%", b(200, 180)))
W(ul_close())

# Leshrac
W(hero_header("Leshrac"))
W(ability("Split Earth"))
W(ul_open())
W(li("Manacost reduced from 100/125/140/160 to 80/100/120/140", b([100, 125, 140, 160], [80, 100, 120, 140], l=True)))
W(ul_close())

# Lina
W(hero_header("Lina"))
W(ul_open())
W(li("Base intelligence increased by 3", t("BUFF")))
W(li("Base damage random variance reduced from 18 to 12", t("BUFF")))
W(ul_close())
W(subnote("Lina's auto-attack damage rolls in a narrower min/max range now (spread 12 instead of 18). Average damage is unchanged — only the swing between hits is smaller, so attacks are more consistent."))

# Lion
W(hero_header("Lion"))
W(ability("Mana Drain"))
W(ul_open())
W(li("Now slows the target by 14/16/18/20%", t("NEW")))
W(ul_close())

# Lycan
W(hero_header("Lycan"))
W(ul_open())
W(li("Base armor reduced by 1", t("NERF")))
W(ul_close())
W(ability("Shapeshift"))
W(ul_open())
W(li("Cooldown increased from 120/90/60 to 130/105/80", b([120, 90, 60], [130, 105, 80], l=True)))
W(ul_close())

# Medusa
W(hero_header("Medusa"))
W(ability("Mystic Snake"))
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
W(ability("Replicate"))
W(ul_open())
W(li("Cast range increased from 600 to 1000", b(600, 1000)))
W(li("Manacost reduced from 75/100/125 to 50", b([75, 100, 125], 50, l=True)))
W(ul_close())
W(ability("Morph Replicate"))
W(ul_open())
W(li("Cast point removed", t("BUFF")))
W(ul_close())

# Nature's Prophet
W(hero_header("Nature's Prophet"))
W(ability("Wrath of Nature"))
W(ul_open())
W(li("Cooldown reduced from 90/75/60 to 70/65/60", b([90, 75, 60], [70, 65, 60], l=True)))
W(ul_close())

# Omniknight
W(hero_header("Omniknight"))
W(ability("Purification"))
W(ul_open())
W(li("Cast range reduced from 450 to 400", b(450, 400)))
W(ul_close())
W(ability("Degen Aura"))
W(ul_open())
W(li("Range reduced from 300 to 275", b(300, 275)))
W(ul_close())

# Oracle
W(hero_header("Oracle"))
W(ability("Fortune's End"))
W(ul_open())
W(li("Manacost reduced from 110 to 75", b(110, 75, l=True)))
W(ul_close())

# Pangolier
W(hero_header("Pangolier"))
W(ability("Rolling Thunder"))
W(ul_open())
W(li("Cooldown increased from 50/45/40 to 70/65/60", b([50, 45, 40], [70, 65, 60], l=True)))
W(ul_close())

# Pudge
W(hero_header("Pudge"))
W(ability("Rot"))
W(ul_open())
W(li("Slow rescaled from 30% to 20/24/28/32%", b(30, [20, 24, 28, 32])))
W(ul_close())
W(subnote("Effectively a nerf at levels 1–2 (20%, 24%) and a buff only at level 4 (32%)"))

# Pugna
W(hero_header("Pugna"))
W(ability("Life Drain"))
W(ul_open())
W(li("Damage increased from 150/200/250 to 150/225/300", b([150, 200, 250], [150, 225, 300])))
W(ul_close())
W(subnote("Aghanim's Scepter no longer increases Life Drain damage — it now only removes the cooldown"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 15 Talent increased from +1 Nether Ward Health to +2", b(1, 2)))
W(ul_close())

# Shadow Fiend
W(hero_header("Shadow Fiend"))
W(ability("Necromastery"))
W(ul_open())
W(li("Max souls reduced from 18/24/30/36 to 12/20/28/36", b([18, 24, 30, 36], [12, 20, 28, 36])))
W(ul_close())

# Shadow Shaman
W(hero_header("Shadow Shaman"))
W(ability("Ether Shock"))
W(ul_open())
W(li("Cooldown increased from 8s to 14/12/10/8s", b(8, [14, 12, 10, 8], l=True)))
W(ul_close())
W(ability("Shackles"))
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
W(ability("Toss"))
W(ul_open())
W(li("Cooldown increased from 8s to 11s", b(8, 11, l=True)))
W(ul_close())

# Tusk
W(hero_header("Tusk"))
W(ability("Snowball"))
W(ul_open())
W(li("Can no longer be cast while rooted", t("NERF")))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ability("Windrun"))
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

save_calendar_html()
