#!/usr/bin/env python3
"""Generate annotated Dota 2 7.41c patch notes HTML."""

import json as _json
import os as _os
import html as _html

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
    "Mage Slayer": "mage_slayer",
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
        if n == o:
            parts.append('<span class="badge neutral">0%</span>')
            keys.append(("neutral", "0%"))
            signed_pcts.append(0)
            continue
        if o == 0:
            # Old value was 0 → % delta is undefined. Still definitely a
            # buff or nerf — emit a plain text-tag instead of "0%".
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
            sign = "+" if is_buff else "-"
            display = f"{sign}{small}%"
            cls = gradient_class(1, is_buff)  # weakest gradient
            signed_pcts.append(small if is_buff else -small)
            parts.append(f'<span class="badge {cls}">{display}</span>')
            keys.append((cls, display))
            continue
        magnitude = abs(pct)
        signed_pcts.append(magnitude if is_buff else -magnitude)
        sign = "+" if is_buff else "-"
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
    if signed_pcts:
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
    seen_abilities_subgroup = False  # set when first ability() emits "Abilities" subgroup
    current_sections = []            # per-patch list of {slug, label}; reset in save_html()

def _open_block(extra_cls='', extra_attrs=''):
    pre = _close_ability_block()
    cls = 'entity-block' + ((' ' + extra_cls) if extra_cls else '')
    s = (pre + ('</div>\n' if _State.block_open else '')
         + f'<div class="{cls}"{extra_attrs}>\n')
    _State.block_open = True
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


def hero_header(name):
    _State.current_hero = HERO_SLUG.get(name, name.lower().replace(" ", "_").replace("'", "").replace("-", ""))
    _State.next_ul_is_hero_stats = True
    _State.seen_abilities_subgroup = False
    return _open_block() + f'''<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="{hero_img(name)}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def unit_header(name, icon_url):
    """Header for a separate summoned unit / neutral creep (e.g. Spirit Bear,
    Ancient Marshmage) with custom icon URL. Marked `.unit-entity` so the
    search index labels it as a creep/unit, not a hero."""
    _State.current_hero = None
    return _open_block() + f'''<div class="entity unit-entity">
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
    return out + _open_block(extra_cls, block_data_attr) + f'''<div class="entity item-entity">
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
                cells.append(
                    f'<span class="property-tag" style="grid-row:{cur_row};grid-column:1">'
                    f'{_prop_tag(tag)}</span>'
                    f'<span class="property-text" style="grid-row:{cur_row};grid-column:2">'
                    f'{text}</span>'
                    f'<span class="property-badge" style="grid-row:{cur_row};grid-column:3">'
                    f'{badge}</span>'
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
    """Small ↳ note that hangs off the end of a li (pass via `extra=`).
    Renders below the row text inside the same li, indented to match the
    subnote visual style. Use for one-liner info that belongs to a single
    change row (e.g. 'As a result of Health Restoration changes')."""
    return f'<div class="inline-note">{text}</div>'


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


def aghs_line(text, kind="scepter"):
    """Aghanim's Scepter/Shard upgrade row — full-width light-blue stripe
    with the canonical glyph from `icons/stats/aghs_<kind>_icon.png` prepended.
    Visually matches the existing `ul.changes li.aghanim-scepter/shard` rows
    used elsewhere on the site.

    `kind` is "scepter" (default) or "shard". Returns a full row div
    (`.ability-change-row.aghanim-<kind>`) — pass it as one of the `desc=[…]`
    items in `ability_change(...)`."""
    return (f'<div class="ability-change-row aghanim-{kind}">'
            f'<span class="aghanim-marker {kind}"></span>{text}</div>')


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


def ability_change(old, new):
    """Two-pane ability swap visual (one ability removed, another added) —
    same visual idiom as components_change but for abilities. Each side is
    a dict:
      name     : str
      icon_url : optional explicit URL
      slug     : optional CDN slug (used if icon_url not given)
      innate   : optional bool — if no slug/url, falls back to INNATE_ICON_URL
      desc     : list of strings (HTML allowed); each rendered as one row
      tables   : optional list of table-HTML appended to the body (use
                 scale_pill's `table` return value)"""
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
    _old_icon, _ = _resolve_icon(old)
    _new_icon, _ = _resolve_icon(new)
    _old_rows = len(old.get("desc", []))
    _new_rows = len(new.get("desc", []))
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
    if not in_place and abs(_old_rows - _new_rows) >= 2:
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
            f'class="innate-marker" title="Innate ability">'
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
        # In-place rework: skip the right pane's redundant header so only
        # the description body shows on the new side.
        head_html = (
            ''
            if in_place and kind == 'new'
            else (
                f'<div class="ability-change-head">'
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


def plain_header(name):
    out = _close_ability_block()
    _State.current_hero = None
    return out + _open_block() + f'<div class="entity plain-entity"><div class="entity-name">{name}</div></div>'


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
    return _open_block(extra_cls, block_data_attr) + f'''<div class="entity item-entity">
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
    _State.current_sections.append({'slug': slug, 'label': label})
    return (_close_block()
            + f'<h2 class="section" data-section="{slug}">{title}</h2>')


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

# Manual fallback for innates not yet in dotaconstants (rare).
INNATE_ABILITIES = set()

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
        if innate is None:
            # Auto-detect: dotaconstants is_innate flag, or manual override.
            is_innate = (slug in _INNATE_SLUGS) or (key in INNATE_ABILITIES)
        else:
            is_innate = bool(innate)
    elif innate is not None:
        is_innate = bool(innate)
    icon_inner = ''
    # Fallback: if no source for the icon at all, show the missing-placeholder
    # so the row is identifiable rather than text-only.
    if not (icon_url or slug):
        icon_inner = (f'<img src="{MISSING_ICON_URL}" alt="" '
                      f'class="ability-icon-img" loading="lazy" '
                      f'title="missing icon: {title}">')
    if icon_url or slug:
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
        # title in only when the load actually fails.
        if slug:
            on_err += (f"this.title='missing icon: {slug}';")
        icon_inner = (f'<img src="{src}" alt="{title}" '
                      f'class="ability-icon-img" loading="lazy"{slug_attr} '
                      f'onerror="{on_err}">')
        if not icon_url:
            _State.ability_icons.add(src)
    if is_innate:
        # Innate marker overlays bottom-center of the ability icon.
        icon_inner += (f'<img src="{INNATE_ICON_URL}" alt="" '
                       f'class="innate-marker" title="Innate ability">')
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
        out += ('<h4 class="subgroup">Other</h4>'
                '<div class="ability-block other-block">'
                f'<div class="ability-icon-wrap">{icon}</div>')
        _State.ability_block_open = True
        _State.next_ul_is_hero_stats = False
    return out + '<ul class="changes">'


def ul_close():
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

    classes = []
    marker = ""
    # Auto-classify any line that prominently references Aghanim's Scepter /
    # Shard — covers both "Aghanim's Scepter: ..." starters and phrasings like
    # "No longer upgraded with Aghanim's Shard" / "Aghanim's Scepter upgrade reworked".
    if isinstance(text, str) and "Aghanim's Scepter" in text:
        classes.append("aghanim-scepter")
        marker = '<span class="aghanim-marker scepter"></span>'
    elif isinstance(text, str) and "Aghanim's Shard" in text:
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
    # Marker is appended INSIDE .row-text so it sits right after the change
    # text (before the % badge column), matching Valve's visual order.
    text_inner = f'{text}{marker}' if isinstance(text, str) else text
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
    """Render a patch version as a clickable link to its page. Patch HTML
    files live in `patches/<ver>.html` — relative reference works because
    correction-notes are rendered inside those same patch pages."""
    if not version:
        return ''
    return f'<a class="patch-link" href="{version}.html"><b>{version}</b></a>'


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


def note_box(text=None, *, hero=None, item=None, unit=None, field=None, before_patch=None):
    """Inline NOTE box rendered after a row.

    Three usage modes:
      - Legacy free-form:  note_box("any text")
      - Auto-derived from stats DB: provide hero=/item=/unit= + field= +
        before_patch= → emits "was <b>X</b>. Previous change in <b>PATCH</b>".
        `unit` takes the full npc key, e.g. 'npc_dota_beastmaster_boar'.
    """
    if hero or item or unit:
        if hero:
            prev_val = stat_h(hero, field, before_patch)
            prev_patch = prev_change_patch_h(hero, field, before_patch) or before_patch
        elif item:
            prev_val = stat_i(item, field, before_patch)
            prev_patch = prev_change_patch_i(item, field, before_patch) or before_patch
        else:
            prev_val = stat_u(unit, field, before_patch)
            prev_patch = prev_change_patch_u(unit, field, before_patch) or before_patch
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
        return (f'<div class="correction-note">'
                f'<span class="correction-label">Previously:</span>'
                f'<b>{_fmt_val(prev_val)}</b>. {tail}'
                f'</div>')
    return (f'<div class="correction-note">'
            f'<span class="correction-label">Note:</span> {text or ""}'
            f'</div>')


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
/* Calendar variant — no dropdown; .release-info takes its place on the right.
   Override the fixed 38px height (designed for version+date only) so the
   3rd line (.patch-age) doesn't overflow above and below the box. */
.nav-context-calendar {
  margin-left: auto;
  min-height: 38px;          /* match the version-dropdown height on patch pages
                                so the toolbar doesn't shrink when you switch
                                from a patch back to the calendar */
}
.nav-context-calendar .release-info {
  align-items: center;
  padding: 6px 18px;
  min-width: 110px;
  height: auto;
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
.cal-year-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 0;
  margin-top: -8px;
  color: #8b949e;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  border-top: 1px solid #21262d;
  margin-bottom: 8px;
}
.cal-year-summary-key { color: #6e7681; text-transform: uppercase; letter-spacing: 0.4px; font-size: 10.5px; }
.cal-year-summary-val { color: #c9d1d9; font-weight: 600; }
.cal-year-summary-meta { color: #6e7681; font-size: 11px; }
.cal-year-block[data-collapsed="true"] .cal-year-summary { display: none; }
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

/* CURRENT patch (compact mode) — emphasised via shadow only, no scale */
.cal-patch.current {
  filter: brightness(1.20);
  z-index: 2;
  box-shadow:
    inset 0 1px 0 rgba(255, 235, 205, 0.35),
    0 0 0 2px rgba(121, 192, 255, 0.85),
    0 2px 6px rgba(0, 0, 0, 0.4);
}
.cal-patch.current:hover {
  z-index: 4;
  filter: brightness(1.35);
  box-shadow:
    inset 0 1px 0 rgba(255, 235, 205, 0.50),
    0 0 0 2.5px rgba(121, 192, 255, 1),
    0 3px 10px rgba(0, 0, 0, 0.5);
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

/* CURRENT patch — emphasised without scaling so text never overflows the cell. */
.cal-full-day.has-patch.current {
  z-index: 4;
  filter: brightness(1.20);
  box-shadow:
    0 0 0 2px rgba(121, 192, 255, 0.85),
    0 2px 8px rgba(0, 0, 0, 0.55);
}
.cal-full-day.has-patch.current:hover {
  z-index: 6;
  filter: brightness(1.35);
  box-shadow:
    0 0 0 2.5px rgba(121, 192, 255, 1),
    0 4px 12px rgba(0, 0, 0, 0.65);
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
  flex-wrap: nowrap;          /* keep all tag buttons on one line */
  flex-shrink: 0;
  white-space: nowrap;
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
  flex: 0 1 280px;
  min-width: 180px;            /* shrinks so categories/tags fit on one line each */
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

/* NEW-ITEM BLOCK — keeps the standard grid (tag column / text / %).
   Only the FIRST row of the block gets a NEW tag (or RETURNING) in the tag
   column; the original per-row tag is hidden. Subsequent rows show an empty
   placeholder so the text column stays aligned with the rest of the page.
   The tag text comes from data-new-tag on the .entity-block. */
/* Hide the original first-child tag completely (not visibility:hidden) so
   it doesn't occupy cell (1,1) of the grid — otherwise the ::before tag
   gets auto-placed to row 2 and appears below the row content. */
.entity-block.is-new ul.changes li > .badge:first-child,
.entity-block.is-new ul.changes li > .row-tag-empty {
  display: none;
}
/* Per-row NEW tag was removed: the item is now signalled by the type label
   after the name + the components/provides blocks below the header. The
   block-level filter still works because each <li> inside .is-new carries
   data-tag="new" (via t("NEW") on the original li()). */
/* Ability description box — spans one Passive:/Active: starter row plus any
   continuation rows until the next ability starter or end of ul. Post-process
   classifies each li with one of -solo / -start / -cont / -cont-end. */
/* Box hugs the ul width (no overflow). Inside a new-item block the tag column
   is gone, so collapse the grid to [text 1fr][badge auto] and add left padding
   so text sits a few px in from the box border. */
ul.changes li.ability-row-solo,
ul.changes li.ability-row-start,
ul.changes li.ability-row-cont,
ul.changes li.ability-row-end {
  background: rgba(139, 148, 158, 0.04);
  border-left:  1px solid rgba(139, 148, 158, 0.18);
  border-right: 1px solid rgba(139, 148, 158, 0.18);
}
/* Apply Hydras-Breath-style layout (no tag column, text flush-left with 12px
   padding) to ALL ability-row li, not just inside .is-new blocks. Tag column
   collapses; only ability-rows that EXPLICITLY have a non-empty tag will
   show one inline at the front of the row text. */
ul.changes li.ability-row-solo,
ul.changes li.ability-row-start,
ul.changes li.ability-row-cont,
ul.changes li.ability-row-end {
  grid-template-columns: 1fr auto;
  padding-left: 12px;
  padding-right: 12px;
}
ul.changes li.ability-row-solo > .row-tag-empty,
ul.changes li.ability-row-start > .row-tag-empty,
ul.changes li.ability-row-cont > .row-tag-empty,
ul.changes li.ability-row-end > .row-tag-empty {
  display: none;
}
ul.changes li.ability-row-solo > .row-text,
ul.changes li.ability-row-start > .row-text,
ul.changes li.ability-row-cont > .row-text,
ul.changes li.ability-row-end > .row-text {
  grid-column: 1;
  text-align: left;
}
/* Ability-row layout has no left tag — suppress the float-pseudo that
   reserves the tag column. */
ul.changes li.ability-row-solo > .row-text::before,
ul.changes li.ability-row-start > .row-text::before,
ul.changes li.ability-row-cont > .row-text::before,
ul.changes li.ability-row-end > .row-text::before {
  display: none;
}
ul.changes li.ability-row-solo,
ul.changes li.ability-row-start {
  border-top: 1px solid rgba(139, 148, 158, 0.18);
  border-top-left-radius: 6px;
  border-top-right-radius: 6px;
  padding-top: 6px;
  margin-top: 10px;          /* gap between adjacent ability boxes */
}
ul.changes li.ability-row-solo,
ul.changes li.ability-row-end {
  border-bottom: 1px solid rgba(139, 148, 158, 0.18);
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
  padding-bottom: 6px;
  margin-bottom: 4px;
}

/* COMPONENTS BOX — visual assembly recipe shown under a new item's header.
   Layout: [icon1 + icon2 + ... + recipe] = TOTAL — total sits IMMEDIATELY
   after the last component (not pushed to the right edge). */
.components-box {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  margin: 6px 0 4px;
  padding: 8px 14px;
  background: rgba(139, 148, 158, 0.04);
  border: 1px solid rgba(139, 148, 158, 0.18);
  border-radius: 6px;
  font-variant-numeric: tabular-nums;
}
.components-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.component {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}
.component img {
  width: 48px;
  height: 36px;
  border-radius: 3px;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(139, 148, 158, 0.25);
}
.component-price {
  font-size: 11px;
  color: #c9d1d9;
  font-weight: 600;
  background: rgba(0, 0, 0, 0.30);
  padding: 1px 6px;
  border-radius: 2px;
  min-width: 32px;
  text-align: center;
}
.components-plus {
  color: #6e7681;
  font-size: 16px;
  font-weight: 700;
  padding: 0 2px;
}
.components-total {
  color: #c9d1d9;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}
.components-total span {
  font-weight: 700;
  color: #f0c674;
}

/* ENCHANT-BY-ATTRIBUTE GRID — 7.41 Tier-X enchantment selection box.
   Layout: rows of [attr icon][attr name] | [enchant chip] [enchant chip]...
   Shares the muted bordered look of components-box / provides-box. */
.enchant-attr-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 8px 0 10px;
  padding: 8px 14px;
  background: rgba(139, 148, 158, 0.04);
  border: 1px solid rgba(139, 148, 158, 0.18);
  border-radius: 6px;
}
.enchant-attr-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  align-items: center;
  gap: 14px;
  padding: 3px 0;
}
.enchant-attr-row + .enchant-attr-row {
  border-top: 1px dashed rgba(139, 148, 158, 0.18);
}
.enchant-attr-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 13.5px;
}
.enchant-attr-ico {
  width: 22px;
  height: 22px;
  object-fit: contain;
  flex-shrink: 0;
}
/* All-Heroes badge: 4 attribute icons packed into a 2×2 mini-grid that
   fills the same 22×22 footprint as a single attribute icon — so the
   "All Heroes" text aligns horizontally with "Strength" / "Agility" /
   etc. on the rows beneath. */
.enchant-attr-icons.all-attrs {
  display: grid;
  grid-template-columns: 10px 10px;
  grid-template-rows: 10px 10px;
  gap: 2px;
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}
.enchant-attr-icons.all-attrs img {
  width: 10px;
  height: 10px;
  object-fit: contain;
  filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.55));
}
.enchant-attr-name { letter-spacing: 0.2px; }
.enchant-attr-name.is-str { color: #e73c06; }
.enchant-attr-name.is-agi { color: #3dcb37; }
.enchant-attr-name.is-int { color: #00d3e7; }
.enchant-attr-name.is-uni { color: #d3e700; }
.enchant-attr-name.is-all { color: #c9d1d9; }
.enchant-attr-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px 7px;
}
.enchant-chip {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 9px 3px 4px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(139, 148, 158, 0.22);
  border-radius: 14px;
  font-size: 12.5px;
  color: #c9d1d9;
  line-height: 1.2;
  transition: background 0.15s, border-color 0.15s;
  cursor: help;
}
.enchant-chip:hover {
  background: rgba(0, 0, 0, 0.35);
  border-color: rgba(139, 148, 158, 0.4);
}
.enchant-chip img {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.4);
  flex-shrink: 0;
}
/* Tooltip — appears above the chip on hover. Multi-line via pre-line. */
.enchant-chip[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  white-space: pre-line;
  background: rgba(13, 17, 23, 0.97);
  color: #c9d1d9;
  font-size: 12px;
  font-weight: 400;
  padding: 7px 11px;
  border: 1px solid rgba(139, 148, 158, 0.35);
  border-radius: 6px;
  opacity: 0;
  pointer-events: none;
  z-index: 100;
  min-width: 180px;
  max-width: 280px;
  text-align: left;
  line-height: 1.45;
  letter-spacing: 0.1px;
  transition: opacity 0.12s 0.05s;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
}
.enchant-chip[data-tooltip]:hover::after {
  opacity: 1;
}
/* Souvenir pills (Ringmaster Dark Carnival pool change). Reuse the
   `.enchant-chip` box style (border + background + tooltip on hover);
   `removed` modifier dims souvenirs no longer in the pool — no strike.
   Dim the icon + label only, NOT the hover tooltip popup — readability
   of the description text must stay full-strength. */
.enchant-chip.souvenir-chip.removed > img,
.enchant-chip.souvenir-chip.removed > span {
  opacity: 0.55;
}
.enchant-chip.souvenir-chip.removed > img {
  filter: grayscale(0.85);
}
.enchant-chip.souvenir-chip.removed::after {
  /* explicit reset — tooltip popup must NOT inherit the dim */
  opacity: 0;
  filter: none;
}
.enchant-chip.souvenir-chip.removed:hover::after {
  opacity: 1;
}
/* Group wrapper: label + chips on a single horizontal row, wrapping if
   needed. "In pool:" and "Removed:" are separate groups on their own
   lines (each `.souvenir-group` is a block-level flex row). */
.souvenir-group {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin: 4px 0;
}
.souvenir-group-label {
  font-weight: 600;
  font-size: 12.5px;
  color: #7c8590;
  margin-right: 2px;
}
@media (max-width: 640px) {
  .enchant-attr-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}

/* PROPERTIES BOX — single line of comma-separated attributes shown under the
   components box for new items. Soft outlined to match other blocks. */
.provides-box {
  margin: 4px 0;
  padding: 6px 14px;
  background: rgba(139, 148, 158, 0.04);
  border: 1px solid rgba(139, 148, 158, 0.18);
  border-radius: 6px;
  color: #c9d1d9;
  font-size: 13.5px;
}
.provides-box .provides-row {
  padding: 2px 0;
  line-height: 1.5;
}

/* Type label after the item name — small, uppercased, NEW colour family.
   vertical-align: middle so it sits on the item name's optical mid-line
   instead of dropping to the baseline of the larger heading text. */
.entity-name .entity-new-type {
  margin-left: 8px;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #b08c5a;
  opacity: 0.85;
  vertical-align: middle;
}

/* Same position/style as new-type, but neutral colour — used for
   'Recipe changed' on items whose components changed in this patch. */
.entity-name .entity-changed-type {
  margin-left: 8px;
  font-size: 11.5px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #c9d1d9;
  opacity: 0.65;
  vertical-align: middle;
}

/* Recipe-changed visual: two SEPARATE component boxes (old and new), joined
   by a bold arrow between them. Uses the same grid 1fr/auto/1fr layout as
   properties-change so the two side-by-side blocks are exactly the same
   width (pane edges line up vertically). */
.components-change {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  column-gap: 12px;
  align-items: stretch;
  margin: 6px 0 4px;
}
.components-change .components-pane {
  margin: 0;
  min-width: 0;
}
.components-change .components-arrow,
.properties-change .properties-arrow {
  align-self: center;
  justify-self: center;
  font-size: 22px;
  font-weight: 700;
  color: #c9d1d9;
  opacity: 0.85;
  padding: 0 2px;
}
.component.component-added {
  border: 1.5px solid rgba(218, 165, 32, 0.85);
  border-radius: 6px;
  padding: 2px;
  box-shadow: 0 0 6px rgba(218, 165, 32, 0.25);
}
.component.component-removed {
  border: 1.5px solid rgba(220, 80, 80, 0.55);
  border-radius: 6px;
  padding: 2px;
  opacity: 0.85;
}

/* ABILITY-CHANGE — two-pane swap visual (old ability removed → new ability
   added). Same 1fr/auto/1fr grid + arrow as components-change, but each
   pane is a card with [icon + name] header on top and a description body
   below (multiple rows + optional scale_pill table). */
.ability-change {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  column-gap: 12px;
  align-items: stretch;
  margin: 6px 0 8px;
}
.ability-change-arrow {
  align-self: center;
  justify-self: center;
  font-size: 22px;
  font-weight: 700;
  color: #c9d1d9;
  opacity: 0.85;
  padding: 0 2px;
}
.ability-change-pane {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(139, 148, 158, 0.04);
  border: 1px solid rgba(139, 148, 158, 0.18);
  border-radius: 6px;
  min-width: 0;
}
.ability-change-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 6px;
  border-bottom: 1px dashed rgba(139, 148, 158, 0.22);
}
.ability-change-icon-wrap {
  position: relative;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}
.ability-change-icon {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.5);
  display: block;
}
/* Innate marker — matches `.ability-block > .ability-icon-wrap > .innate-marker`
   style (dark circular pad + golden ring), scaled to the 40-px swap-pane icon. */
.ability-change-icon-wrap .innate-marker {
  position: absolute;
  left: 50%;
  bottom: -5px;
  transform: translateX(-50%);
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #0a0e13;
  padding: 1px;
  box-shadow: 0 0 0 1px rgba(220, 175, 95, 0.45);
  pointer-events: none;
  box-sizing: border-box;
}
.ability-change-name {
  font-size: 14.5px;
  font-weight: 600;
  letter-spacing: 0.2px;
  color: #c9d1d9;
}
.ability-change-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13.5px;
  line-height: 1.5;
  color: #c9d1d9;
  min-width: 0;
}
.ability-change-row { padding: 4px 0; line-height: 1.45; }
/* In-place rework (same name + icon on both sides): right pane skips the
   header and only shows the description body — so the box should also be
   visually smaller and centered (vertically + horizontally) relative to
   the full-height left card, not stretched to match it. */
.ability-change.is-in-place {
  grid-template-columns: 1fr auto minmax(0, 1fr);
}
.ability-change.is-in-place .ability-change-new {
  align-self: center;
  justify-self: center;
  width: fit-content;
  max-width: 100%;
  justify-content: center;
  padding: 8px 14px;
}
/* In-place rework where NEW outgrew OLD: centering puts new's first row
   at the Y-level of old's HEADER (since new pane has no head). Switch to
   top-anchored, full-width layout for the new pane, with padding-top
   matching the old head's vertical footprint (47px head + ~8px gap) so
   the new body's first row top-aligns with old's body first row. */
.ability-change.is-in-place.is-new-taller .ability-change-new {
  align-self: start;
  justify-self: stretch;
  width: auto;
  max-width: none;
  justify-content: flex-start;
  padding: 8px 14px;
}
/* Asymmetric content: the pane with fewer description rows shrinks and
   centers in its column, instead of stretching to mirror the taller pane
   and leaving visible empty space below its text. */
.ability-change.compact-old .ability-change-old,
.ability-change.compact-new .ability-change-new {
  align-self: center;
  justify-self: center;
  width: fit-content;
  max-width: 100%;
  padding: 8px 14px;
}
/* Aghanim's Scepter upgrade row inside an ability-change pane — same blue
   gradient stripe + scepter glyph as the canonical `ul.changes li.aghanim-
   scepter` rows, but stretched edge-to-edge of the pane (no tag column to
   skip past inside a swap card). */
.ability-change-row.aghanim-scepter,
.ability-change-row.aghanim-shard {
  position: relative;
  /* Stripe is narrower than its `ul.changes li.aghanim-*` cousin (no tag
     column to skip), so the fade starts earlier — solid head, decays by
     30% across, fully transparent before the right edge. */
  background: linear-gradient(90deg,
    rgba(72, 148, 255, 0.26) 0,
    rgba(72, 148, 255, 0.18) 30%,
    rgba(72, 148, 255, 0.06) 70%,
    rgba(72, 148, 255, 0) 100%);
  border-radius: 3px;
  padding: 4px 8px 4px 6px;
}
.ability-change-row.aghanim-scepter .aghanim-marker,
.ability-change-row.aghanim-shard .aghanim-marker {
  margin-left: 0;
  margin-right: 6px;
  vertical-align: -3px;
}
/* Formula table inside a pane: compact + horizontally scrollable when it
   overflows the pane width. */
.ability-change-body .formula-table-wrap {
  margin-top: 6px;
  overflow-x: auto;
  max-width: 100%;
  -webkit-overflow-scrolling: touch;
}
/* Formula tables embedded inside an ability_change new-pane must fit the
   half-width pane without a horizontal scroll bar. Fixed layout shrinks
   columns to the available width; tabular-nums keeps digits aligned even
   when each column is barely wider than a 3-char value like "11.5". */
.ability-change-body .formula-table {
  font-size: 10.5px;
  margin: 0;
  width: 100%;
  table-layout: fixed;
  font-variant-numeric: tabular-nums;
}
.ability-change-body .formula-table th,
.ability-change-body .formula-table td {
  padding: 2px 2px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* Row labels (first column: "old" / "new" / "Δ %" / "value") still need
   room for the text — force them just-wide-enough so the level cells share
   the rest. 44px fits "value" without ellipsis truncation. Centered to
   match the level cells' centered alignment (was right-aligned, which
   looked off-axis next to the centered numbers). */
.ability-change-body .formula-table th:first-child,
.ability-change-body .formula-table td:first-child {
  width: 44px;
  text-align: center;
  overflow: visible;
}
@media (max-width: 720px) {
  .ability-change { grid-template-columns: 1fr; row-gap: 6px; }
  .ability-change-arrow { transform: rotate(90deg); }
}
/* When discrete change rows follow an ability_change card (numerical
   tweaks that complement the prose swap), give the ul.changes the same
   left indent the ability-block's content column would have — otherwise
   its tag column sits flush with the entity-block edge, visually
   detached from the swap card above. Higher specificity than the generic
   `.entity-block > ul.changes { padding-left: 0 }` rule. */
.entity-block > .ability-change + ul.changes {
  padding-left: 60px;
}
/* (is-changed visual blocks inherit the +14px indent from the generic
   .entity-block > * rules above — no special override needed.) */
/* (removed: is-changed ul.changes padding-left: 0 — that made the tag column
   shift 40px left of the default ul padding, misaligning is-changed item tags
   relative to regular items below them. Now is-changed inherits default
   ul.changes padding so tags line up vertically across the whole page.) */

/* Two-pane property diff (old grant set → new grant set).
   ONE grid for both panes so row N on the left lines up with row N on the
   right. Pane "boxes" are drawn by two background divs that span cols 1-3
   and 5-7 respectively, sitting behind content via z-index. */
/* Two equal-width panes joined by a centred bold arrow. Each pane is a
   subgrid for ROWS, so row N on the left vertically aligns with row N on
   the right — no matter which side has taller cells. Each pane has its own
   3-col grid inside (tag | text 1fr | badge auto-pinned right). */
.properties-change {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  column-gap: 12px;
  margin: 6px 0 4px;
}
.properties-change .properties-pane {
  display: grid;
  grid-template-columns: auto 1fr auto;
  grid-template-rows: subgrid;
  grid-row: 1 / -1;
  column-gap: 8px;
  row-gap: 4px;
  align-items: center;
  padding: 8px 14px;
  background: rgba(139, 148, 158, 0.04);
  border: 1px solid rgba(139, 148, 158, 0.18);
  border-radius: 6px;
}
.properties-change .pane-old { grid-column: 1; }
.properties-change .pane-new { grid-column: 3; }
.properties-change .properties-arrow {
  grid-column: 2;
  grid-row: 1 / -1;
}
/* Single-pane mode: only one side changed → render just that pane in its
   column position from the 2-pane layout (left = col 1, right = col 3) so
   the visible pane lands in the same horizontal area as it would when both
   panes are present. */
.properties-change.new-only,
.properties-change.old-only {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
}
.properties-change.new-only .pane-new { grid-column: 3; }
.properties-change.old-only .pane-old { grid-column: 1; }
.properties-change .property-text {
  min-width: 0;
  color: #c9d1d9;
  font-size: 13.5px;
  line-height: 1.5;
}
.properties-change .property-badge {
  justify-self: end;
  white-space: nowrap;
  /* Pane has padding-right: 14px. Pull the badge cell 12px outside that
     padding so the b() % bands sit only 2px from the pane's right border. */
  margin-right: -12px;
}
.properties-change .property-row-empty {
  min-height: 1.5em;
}
.properties-change .property-extra {
  margin-top: -2px;             /* sit close to the row above; subgrid row-gap
                                   already provides a small natural separation */
}

/* SUBGROUPS — same colour as body text / ability titles, not blue.
   Tormentor / Roshan / Wisdom Shrines / Health Restoration / Lifesteal /
   Miscellaneous / Talents etc. all read as section dividers, not links. */
h4.subgroup {
  color: #c9d1d9;
  font-size: 14px;
  font-weight: 700;
  margin: 16px 0 4px 0;      /* aligned with entity-block left edge */
  text-transform: uppercase;
  letter-spacing: 0.6px;
  border-bottom: 1px solid #21262d;
  padding-bottom: 4px;
}
/* ABILITY BLOCK — icon (left, full-height) + title (top-right) + changes (below title) */
.ability-block {
  display: grid;
  grid-template-columns: 48px 1fr;
  column-gap: 12px;
  align-items: start;
  margin: 12px 0 8px 0;
}
.ability-block > .ability-icon-wrap {
  grid-column: 1;
  grid-row: 1 / span 99;
  position: relative;
  width: 48px;
  height: 48px;
  align-self: start;
}
.ability-block > .ability-icon-wrap > .ability-icon-img {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  object-fit: cover;
  box-shadow: 0 0 0 1px rgba(210, 168, 255, 0.18), 0 2px 6px rgba(0, 0, 0, 0.4);
}
/* Innate-icon overlay: bottom-center of the ability icon */
.ability-block > .ability-icon-wrap > .innate-marker {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #0a0e13;
  padding: 1px;
  box-shadow: 0 0 0 1px rgba(220, 175, 95, 0.45);
}
.ability-block > .ability-title {
  grid-column: 2;
  margin: 0;
  padding: 0 0 4px 0;       /* no top padding so title-top aligns with icon-top */
  color: #c9d1d9;            /* same as body text — not coloured */
  font-size: 17px;
  font-weight: 600;
  line-height: 1;            /* tight line-height — text top = box top */
  align-self: start;
}
.ability-block > ul.changes {
  grid-column: 2;
  margin-top: 0;
}
.ability-block > ul.subnotes {
  grid-column: 2;
  /* margin-left: 76px (inherited from base ul.subnotes) shifts it under the
     row-text column inside ul.changes — same alignment as subnotes outside
     ability-block. Do NOT override to 0; that puts the ↳ under the tag. */
}
/* Talents-block: same .ability-block layout, but talents.svg gets translucent framing */
.ability-block.talents-block > .ability-icon-wrap > .ability-icon-img {
  background: rgba(121, 192, 255, 0.05);
  padding: 6px;
  box-shadow: 0 0 0 1px rgba(121, 192, 255, 0.18), 0 2px 6px rgba(0, 0, 0, 0.4);
}
/* Other-block: neutral grey framing for the inline-SVG sliders icon */
.ability-block.other-block > .ability-icon-wrap > .ability-icon-img {
  background: rgba(139, 148, 158, 0.05);
  padding: 6px;
  box-shadow: 0 0 0 1px rgba(139, 148, 158, 0.18), 0 2px 6px rgba(0, 0, 0, 0.4);
}
/* Formula tables INSIDE .ability-block — extend back to entity-block left edge,
   not just within content column (else they look right-aligned past the icon). */
.ability-block ul.changes li > .formula-table {
  margin-left: -60px;          /* counter ability-block icon column (48 + 12 gap) */
  width: calc(100% + 60px);
}
/* Raw <li> (no .row-text wrapper) inside ability-block — TWO offsets stack:
   76px to cancel the raw-li padding, plus 60px to clear the ability-block icon. */
.ability-block ul.changes li:not(:has(> .row-text)) > .formula-table,
.ability-block ul.changes li:not(:has(> .row-text)) > .correction-note {
  margin-left: -136px;
  width: calc(100% + 136px);
}

/* CHANGES LIST — grid layout: [tag] [text] [percentages] */
ul.changes {
  list-style: none;
  margin: 3px 0 3px 0;
  padding-left: 0;          /* per-context indent applied via .entity-block,
                               .ability-block etc. (14px to align with icon) */
  padding-right: 2px;       /* keep right-edge % bands 2px in from the
                               container border (entity-block / ability-block) */
}
ul.changes li {
  display: grid;
  /* 2-column grid (text | badge). The text-tag is absolutely positioned over
     the top-left of the text area, with row-text using text-indent to push
     the first line past the tag. When the text wraps, subsequent lines flow
     full-width — reusing the empty space below the tag instead of leaving an
     awkward visual gap on the left. */
  grid-template-columns: 1fr auto;
  column-gap: 12px;
  row-gap: 0;
  align-items: baseline;
  padding: 1px 0;
  line-height: 1.5;
  color: #c9d1d9;
  position: relative;
}
/* Hover ruler: dashed line spanning from text toward the % so the eye can
   trace the row. Anchored at the bottom of the FIRST grid row (i.e. just
   under the change-text baseline), not at the bottom of the whole li —
   that way it stays put even when correction-notes/formula-tables span
   full-width below. */
ul.changes li:has(> .badge-group):hover::after {
  content: "";
  position: absolute;
  left: 76px;
  right: 0;
  top: calc(1px + 1.5em);     /* li padding-top + line-height of first row */
  border-bottom: 1px dashed rgba(139, 148, 158, 0.32);
  pointer-events: none;
}
/* Text-tag: absolutely positioned over the top-left of the row, taking it
   out of grid flow so the wrapped text of .row-text can flow under it.
   Fixed 64px width keeps every tag aligned to the same column visually. */
ul.changes li > .badge:first-child,
ul.changes li > .row-tag-empty {
  position: absolute;
  left: 0;
  top: 3px;
  width: 64px;
  min-width: 64px;
}
ul.changes li > .row-tag-empty {
  visibility: hidden;
  display: inline-block;
  padding: 3px 7px;
  font-size: 11px;
  line-height: 1;
  box-sizing: border-box;
  border: 1px solid transparent;
}
/* Description column. A float pseudo reserves the 76px tag area at the start
   of the first line; text wraps AROUND it, with line 2+ flowing under the
   reserved area. Cleaner than text-indent because inline-block triggers like
   .formula-trigger don't get artificially pushed past the indent column. */
ul.changes li > .row-text {
  grid-column: 1;
}
ul.changes li > .row-text::before {
  content: "";
  float: left;
  width: 76px;
  height: 1.4em;
}
/* Right column: numeric percentages — sits in the second grid column. */
ul.changes li > .badge-group {
  grid-column: 2;
  margin-left: 0;
}
/* extras (correction-note, formula-table, NOTE box) span all columns */
/* correction-note + formula-table span the full li width (under the tag
   column too) — for hero-stat rows there's a lot of empty space on the
   left, and stretching the note across uses it instead of leaving an
   awkward gap. The note's own padding-left (12px) keeps the text from
   running flush against the entity-block edge. */
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
  /* matches .badge:first-child dimensions exactly (width: 64px) */
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
  width: 64px;
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
  margin: -2px 0 4px 0;        /* flush with parent left edge (was 76px under
                                  text column — but pairs better with the
                                  full-width correction-note that lives just
                                  above it in the same hero row). */
}
ul.subnotes li {
  color: #8b949e;
  font-size: 13.5px;
  padding: 1px 0;
  line-height: 1.4;
}
ul.subnotes li::before { content: "↳ "; color: #6e7681; }
/* When the subnote is collapsible, drop the ↳ arrow — the rotating ▶ chevron
   on <summary> already serves as the indicator, putting both side-by-side
   reads as visual noise. */
ul.subnotes li:has(> .subnote-collapse)::before { content: ""; }

/* Collapsible subnote — long bullet lists hidden behind a "▶ summary (N)"
   click target. Native <details>/<summary> preserves keyboard and SR support. */
.subnote-collapse > summary {
  cursor: pointer;
  list-style: none;
  display: inline;
  user-select: none;
}
.subnote-collapse > summary::-webkit-details-marker { display: none; }
.subnote-collapse > summary::before {
  content: "▶";
  display: inline-block;
  width: 10px;
  margin-right: 4px;
  font-size: 9px;
  color: #6e7681;
  transition: transform 0.15s;
}
.subnote-collapse[open] > summary::before { transform: rotate(90deg); }
.subnote-collapse > summary:hover { color: #c9d1d9; }
.subnote-count {
  color: #6e7681;
  font-weight: 500;
  font-size: 12px;
}
ul.subnote-items {
  margin: 4px 0 4px 18px;
  list-style: none;
}
ul.subnote-items > li {
  padding: 1px 0;
  line-height: 1.45;
  color: #8b949e;
  font-size: 13px;
}
ul.subnote-items > li::before {
  content: "•  ";
  color: #6e7681;
}

/* Block-level 'Show list (N)' info row that drops to a new line below the
   sentence inside an ability box. Matches the visual language of
   subnote-collapse (rotating triangle arrow) but lives inside the box. */
.show-list-inline {
  display: block;
  grid-column: 1 / -1;        /* span full li width inside the row grid */
  margin-top: 0;
}
.show-list-inline > summary {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  list-style: none;
  cursor: pointer;
  color: #8b949e;
  font-size: 12.5px;
  user-select: none;
}
.show-list-inline > summary::-webkit-details-marker { display: none; }
/* ↳ corner arrow (matches the subnote-style indent marker) followed by the
   rotating ▸ chevron. Both rendered via a single ::before so they animate
   together. */
.show-list-inline > summary::before {
  content: '\\21B3';           /* ↳ */
  display: inline-block;
  color: #6e7681;
  font-size: 12.5px;
  margin-right: 2px;
}
.show-list-inline > summary > .show-list-chevron {
  display: inline-block;
  color: #6e7681;
  font-size: 11px;
  transition: transform 0.15s ease;
}
.show-list-inline[open] > summary > .show-list-chevron { transform: rotate(90deg); }
.show-list-inline > summary:hover { color: #c9d1d9; }
.show-list-inline[open] > summary { color: #c9d1d9; }
.show-list-inline > .show-list-body {
  display: block;
  margin: 6px 0 2px 6px;
  padding: 0;
}
.show-list-inline > .show-list-body > .show-list-item {
  display: block;
  padding: 1px 0;
  color: #8b949e;
  font-size: 13px;
  line-height: 1.45;
}
.show-list-inline > .show-list-body > .show-list-item::before {
  content: "•  ";
  color: #6e7681;
}

/* One-liner ↳ note hanging off a li (passed via extra= on li()). Drops to a
   new visual line below the row text. Spans the FULL li width (col 1 / -1)
   like correction-note, formula-table, subnote — using the tag column's
   empty space below the tag rather than leaving it blank. The ↳ glyph
   provides the visual indent so the note still reads as a child of the row. */
.inline-note {
  display: block;
  grid-column: 1 / -1;
  margin-top: 4px;
  font-size: 12.5px;
  color: #8b949e;
  line-height: 1.45;
  /* ↳ pseudo is absolute-positioned so the note's body content (including
     wrapping lines and <br>-separated entries) all share the same left
     indent — first line isn't offset by the arrow's inline width. */
  position: relative;
  padding-left: 16px;
}
.inline-note::before {
  content: "↳";
  position: absolute;
  left: 0;
  top: 1px;
  color: #6e7681;
}
/* Tarot-card sub-list entries (Oracle Diviner's Deck): small icon + bold card
   name + effect. Each entry is its own inline-flex row so wrapping reads as
   a checklist instead of a wall of text. */
.tarot-card {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.tarot-card-icon {
  width: 22px;
  height: 22px;
  border-radius: 3px;
  vertical-align: middle;
  flex-shrink: 0;
}
/* (ability-row li no longer needs a special override — base rule already
   spans col 1 / -1, which is the full width in both layouts.) */

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
/* When inside .badge-group → strip the box, become plain colored text.
   `display: inline` ensures baseline-alignment with surrounding text (was inline-flex
   which sat below the text baseline in raw rows like Bloodstone wrong-line). */
.badge-group {
  display: inline;
  vertical-align: baseline;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  font-size: 13px;
}
/* Inside a li's right grid cell, the badge-group becomes a grid item (column 2).
   Keep it as an inline-block so its content (start/end pairs, % chips) doesn't
   wrap across multiple lines and pad the row height. */
ul.changes li > .badge-group {
  display: inline-block;
  white-space: nowrap;
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
  display: inline;            /* override .badge's inline-block — proper baseline align */
  vertical-align: baseline;   /* override .badge's middle */
}
/* Comma separator between multi-level badges */
.badge-group .badge:not(:last-child)::after {
  content: ", ";
  color: #6e7681;
  font-weight: 400;
}
/* Extra leading space before 0% (neutral) — without +/- prefix it visually crowds the comma */
.badge-group .badge.neutral:not(:first-child) {
  margin-left: 0.25em;
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
/* Bold values inside the note (prev value, prev patch) — same size as surrounding
   text, just bold; drop the inherited italic so they don't visually pop out. */
.correction-note b {
  font-size: inherit;
  font-style: normal;
  font-weight: 700;
}
/* "(N days ago)" annotation — fainter so it reads as a side-note. */
.correction-note .days-ago {
  font-style: normal;
  color: #6e7681;
  font-size: 11.5px;
  font-weight: 500;
}
/* Patch version chip-link inside correction-note ("changed in <ver>"). */
.patch-link {
  color: inherit;
  text-decoration: none;
  border-bottom: 1px dotted currentColor;
  transition: color 120ms ease, border-color 120ms ease;
}
.patch-link:hover,
.patch-link:focus-visible {
  color: #4894ff;
  border-bottom-color: #4894ff;
  outline: none;
}
/* Badge-group inside correction-note: float to the right edge of the note
   so it visually mirrors the row's main % (which sits in the right grid column). */
.correction-note > .badge-group {
  float: right;
  /* Negative right margin compensates the .correction-note padding-right (12px)
     so the badge sits flush with the right edge — aligns with the row's main %
     above/below the note. */
  margin: 0 -12px 0 12px;
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

/* AGHANIM'S SCEPTER / SHARD ROWS — light blue stripe (begins AT the icon, never
   covers the tag column) + small icon prefix sitting in the gap between tag
   and text columns (absolutely positioned so the row's text stays aligned
   with all other rows in the list). */
ul.changes li.aghanim-scepter,
ul.changes li.aghanim-shard {
  /* Stripe begins ~70px from li edge (just before the text column starts at
     76, leaves a small breathing-room before the first letter). Height is
     constrained to the tag-block height (~19px from top:3px) so the stripe
     never grows with multi-line rows or correction-notes below. */
  background: linear-gradient(90deg, transparent 0 70px, rgba(72, 148, 255, 0.22) 70px, rgba(72, 148, 255, 0.10) 60%, transparent 100%) no-repeat 0 3px / 100% 19px;
  border-radius: 3px;
}
/* Aghanim marker — inline icon appended to the change-text inside .row-text,
   so it sits right after the last character of the change description and
   before the % badge column. */
.aghanim-marker {
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-left: 6px;
  vertical-align: -2px;
  background-position: center;
  background-size: contain;
  background-repeat: no-repeat;
}
.aghanim-marker.scepter {
  background-image: url('icons/stats/aghs_scepter_icon.png');
}
.aghanim-marker.shard {
  background-image: url('icons/stats/aghs_shard_icon.png');
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
  white-space: nowrap;
  padding: 0 5px;
  border-radius: 3px;
  background: rgba(139, 148, 158, 0.08);
  color: #8b949e;
  border: 1px solid rgba(139, 148, 158, 0.30);
  font-size: inherit;
  cursor: pointer;
  transition: all 0.14s;
  font-variant-numeric: tabular-nums;
  user-select: none;
}
/* Small "start" / "end" labels next to per-level formula badges
   (Δ% at L1 vs Δ% at L30) — visually subtle, sits inline after each
   badge to clarify which hero-level its number represents. */
.formula-endpoint-label {
  display: inline-block;
  font-size: 10px;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #6e7681;
  margin: 0 4px 0 -2px;
  font-weight: 500;
}
/* Trailing 'end' label sits flush with the right edge of the badge column —
   the inherited 4px right margin would otherwise push the whole start/end
   pair leftward and visually misalign with adjacent single-badge rows. */
.badge-group .formula-endpoint-label:last-child {
  margin-right: 0;
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

/* Tags row + Categories row stacked vertically inside the toolbar; both rows
   share the same horizontal-button rhythm so labels align under each other. */
.legend-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.legend-categories {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  white-space: nowrap;
}
.legend-categories strong {
  color: #c9d1d9;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-right: 4px;
}
.cat-filter-btn {
  cursor: pointer;
  user-select: none;
  font-family: inherit;
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 3px;
  background: rgba(121, 192, 255, 0.05);
  color: #87a3bf;
  border: 1px solid rgba(121, 192, 255, 0.22);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  transition: filter 0.12s, background 0.12s, border-color 0.12s;
}
.cat-filter-btn:hover {
  background: rgba(121, 192, 255, 0.10);
  border-color: rgba(121, 192, 255, 0.40);
  color: #c9d1d9;
}
.cat-filter-btn.active {
  background: rgba(121, 192, 255, 0.22);
  border-color: rgba(121, 192, 255, 0.60);
  color: #c9d1d9;
}
body.cat-filter-active .cat-hide { display: none !important; }

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
/* All entity-block children flush against the entity-block left edge (margin
   not padding — padding-left controls INTERNAL content inset, which the
   visual boxes need to keep at 14px so their content aligns with the entity
   icon above). */
.entity-block > h4.subgroup,
.entity-block > ul.changes,
.entity-block > .ability-block,
.entity-block > .components-box,
.entity-block > .components-change,
.entity-block > .provides-box,
.entity-block > .properties-change {
  margin-left: 0;
}
/* Tag column inside ul.changes also flush at entity-block left edge — these
   lists have no inner box border to inset from. */
.entity-block > ul.changes,
.entity-block > .ability-block {
  padding-left: 0;
}
/* ul.subnotes is NOT touched here — it keeps its base margin-left: 76px so
   the ↳ arrow lines up under the row text column (after the 64px tag column
   + 12px gap). Resetting it to 0 here would flush subnotes against the
   entity-block left edge, misaligning every "Damage at level 1 ..." note. */
.entity-block.is-new > ul.changes {
  padding-left: 0;
}

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
            # Calendar page — no release-info widget (the calendar itself shows
            # date+version), but we still emit an empty nav-context-calendar
            # div so the toolbar reserves the same vertical space as on patch
            # pages and the header doesn't jump on tab switch.
            right_side = '\n    <div class="nav-context nav-context-calendar"></div>'
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
  // Recipe-changed items count as REWORK even if none of their explicit rows
  // carry t("REWORK") — keep the filter button discoverable on those pages.
  if (document.querySelector('.entity-block.is-changed')) presentTags.add('rework');
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
      // Items whose recipe changed (entity-block.is-changed) count as REWORK
      // so the REWORK filter keeps their rows visible too.
      if (li.closest('.entity-block.is-changed')) tags.push('rework');
      const matches = tags.some(t => activeFilters.has(t));
      if (!matches) li.classList.add('f-hide');
    });
    // Block-level swap visuals (ability_change) carry their own data-tag and
    // sit outside ul.changes — hide them when none of their tags is active.
    document.querySelectorAll('.ability-change[data-tag]').forEach(block => {
      const tags = (block.dataset.tag || '').split(' ').filter(Boolean);
      if (!tags.some(t => activeFilters.has(t))) block.classList.add('f-hide');
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
    // Hide the entire ability-block (icon + title + ul) if its ul is hidden,
    // otherwise the floating icon stays visible without any text.
    document.querySelectorAll('.ability-block').forEach(block => {
      const ul = block.querySelector('ul.changes');
      if (!ul || ul.classList.contains('f-hide')) {
        block.classList.add('f-hide');
      }
    });
    document.querySelectorAll('.entity-block').forEach(block => {
      const visibleLi    = block.querySelectorAll('ul.changes > li:not(.f-hide)').length;
      const visibleSwaps = block.querySelectorAll('.ability-change:not(.f-hide)').length;
      if (!visibleLi && !visibleSwaps) block.classList.add('f-hide');
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

  // ---- CATEGORIES FILTER ----
  // Tag every element between adjacent <h2 class="section"> headers with the
  // preceding section's slug so the buttons can hide non-matching siblings.
  (function indexSections() {
    const headers = document.querySelectorAll('h2.section[data-section]');
    headers.forEach(h => {
      const slug = h.dataset.section;
      let nx = h.nextElementSibling;
      while (nx && !(nx.tagName === 'H2' && nx.classList.contains('section'))) {
        if (!nx.dataset.section) nx.dataset.section = slug;
        nx = nx.nextElementSibling;
      }
    });
  })();
  const catButtons = document.querySelectorAll('.cat-filter-btn');
  const activeCats = new Set();
  function applyCatFilter() {
    const on = activeCats.size > 0;
    document.body.classList.toggle('cat-filter-active', on);
    document.querySelectorAll('[data-section]').forEach(el => {
      el.classList.remove('cat-hide');
      if (on && !activeCats.has(el.dataset.section)) el.classList.add('cat-hide');
    });
  }
  catButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const cat = btn.dataset.category;
      if (activeCats.has(cat)) { activeCats.delete(cat); btn.classList.remove('active'); }
      else { activeCats.add(cat); btn.classList.add('active'); }
      applyCatFilter();
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
    // Strip the "New X Item" / "Returning Tier N Artifact" / "Recipe changed"
    // labels so the search index uses just the entity name itself.
    const nameClone = nameEl.cloneNode(true);
    nameClone.querySelectorAll('.entity-new-type, .entity-changed-type').forEach(n => n.remove());
    let kind = 'mechanic';
    if (entity.classList.contains('hero-entity')) kind = 'hero';
    else if (entity.classList.contains('unit-entity')) kind = 'creep';
    else if (entity.classList.contains('item-entity')) kind = 'item';
    entities.push({
      name: nameClone.textContent.trim().replace(/\s+/g, ' '),
      element: entity,
      icon: imgEl ? imgEl.src : null,
      kind: kind
    });
  });
  // Also index ability titles (h4.ability-title) — pull icon from the .ability-block
  // wrapper so search results show the same picture as the ability heading.
  // For innate abilities, Valve doesn't expose icons on the React CDN; the
  // canonical image is the innate marker, so use that directly in search.
  document.querySelectorAll('h4.ability-title').forEach(h => {
    const block = h.closest('.ability-block');
    const imgEl = block ? block.querySelector('.ability-icon-img') : null;
    const isInnate = block ? block.classList.contains('is-innate') : false;
    const innateUrl = '../icons/misc/innate_icon.png';
    entities.push({
      name: h.textContent.trim(),
      element: h,
      icon: isInnate ? innateUrl : (imgEl ? imgEl.src : null),
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
        m.icon
          ? `<img src="${m.icon}" alt="" onerror="this.onerror=null;this.src='../icons/misc/missing.svg';">`
          : '<span style="width:32px;display:inline-block"></span>'
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
       6 MISC / QoL
       7 untagged (kept at end so they don't displace tagged rows).

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
            'misc': 6, 'qol': 6,
        }[kind]
    # No explicit left text-tag — numeric-only rows always synthesize a
    # BUFF/NERF left-tag in li() based on data-overall, so the above regex
    # catches them. Reaching here means the row is untagged (ability
    # description, structural intro, etc.) → keep at the bottom.
    if 'class="badge-group"' in li_html:
        # Safety net for any badge-group row that escaped the left-tag
        # synth path — fall into BUFF rank as a neutral default.
        return 3
    return 7


def _sort_changes_li(html):
    """Enforce the canonical row order inside every <ul class="changes"> block:
       NEW → REWORK → BUFF → NERF → DEL → MISC/QoL → untagged.
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
    return '<strong>Categories:</strong>' + ''.join(btns)


def save_html(filename):
    """Write current accumulator to ./{filename} and reset state."""
    out = "\n".join(H)
    out = out.replace('<!--CATEGORIES_BAR-->', _categories_bar_html())
    out = _swap_single_row_other_icons(out)
    out = _sort_changes_li(out)
    out = _wrap_ability_boxes(out)
    path = filename
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  → {filename}: {len(out):,} bytes")
    H.clear()
    _State.block_open = False
    _State.current_sections = []


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
        shortest = ranked[0]
        longest = ranked[-1]
        return {
            'total': len(year_patches),
            'shortest': (shortest['version'], spans[shortest['version']]),
            'longest':  (longest['version'],  spans[longest['version']]),
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

        # ---- YEAR SUMMARY (Total / Longest / Shortest running patch) ----
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
                f'<span class="cal-year-summary-val">{ys["longest"][0]}</span>'
                f' <span class="cal-year-summary-meta">({ys["longest"][1]} days)</span>'
                f' &middot; '
                f'<span class="cal-year-summary-key">Shortest:</span> '
                f'<span class="cal-year-summary-val">{ys["shortest"][0]}</span>'
                f' <span class="cal-year-summary-meta">({ys["shortest"][1]} days)</span>'
                '</div>'
                '</div>'
            )

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
W(li(
    '<span class="wrong-word">Health bonus increased from +600 to +625</span>',
    '<span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span>',
    extra='<div class="correction-note"><span class="correction-label">Note:</span> This change is wrongly stated. The real change is 650 → 625 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span></span></div>',
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
W(li("Base Intelligence increased by 1", bstat_h("Abaddon", "AttributeBaseIntelligence", "7.41b", 1), extra=note_box(hero="Abaddon", field="AttributeBaseIntelligence", before_patch="7.41b")))
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
W(ul_close())
W(subnote("Damage at level 1 increased from 51-57 to 52-58"))
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
W(ul_close())
W(subnote("Damage at level 1 decreased from 50-54 to 49-53"))
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
W(ul_close())
W(subnote("Damage at level 1 increased from 53-59 to 54-60"))
W(hero_header("Dark Willow"))
W(subgroup("Abilities"))
W(ability("Terrorize"))
W(ul_open())
W(li("Radius increased from 400/450/500 to 450/500/550", b([400, 450, 500], [450, 500, 550])))
W(ul_close())
W(hero_header("Dawnbreaker"))
W(ul_open())
W(li("Base Damage decreased by 1", bstat_h("Dawnbreaker", "AttackDamageMin", "7.41b", -1), extra=note_box(hero="Dawnbreaker", field="AttackDamageMin", before_patch="7.41b")))
W(ul_close())
W(subnote("Damage at level 1 decreased from 56-60 to 55-59"))
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
W(ul_close())
W(subnote("Damage at level 1 increased from 47-51 to 48-52"))
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
W(li("Base Damage increased by 3", bstat_h("Hoodwink", "AttackDamageMin", "7.41b", 3), extra=note_box(hero="Hoodwink", field="AttackDamageMin", before_patch="7.41b")))
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
W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png"))
W(ul_open())
W(li(
    'Gold/Experience Bounty changed from <span class="formula-old">175 + 8 per Spirit Bear level</span> up to <span class="formula-trigger" data-formula="fsb">165 + 10 per Spirit Bear level</span>',
    '<span class="badge rework" data-tag="rework">REWORK</span><span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span>',
    extra='<table class="formula-table" id="fsb" hidden><thead><tr><th></th><th>L1</th><th>L2</th><th>L3</th><th>L4</th><th>L5</th><th>L6</th><th>L7</th><th>L8</th><th>L9</th><th>L10</th><th>L11</th><th>L12</th><th>L13</th><th>L14</th><th>L15</th><th class="lvl-jump">L20</th><th>L25</th><th>L30</th></tr></thead><tbody><tr><th class="row-label-old">old</th><td>183</td><td>191</td><td>199</td><td>207</td><td>215</td><td>223</td><td>231</td><td>239</td><td>247</td><td>255</td><td>263</td><td>271</td><td>279</td><td>287</td><td>295</td><td class="lvl-jump">335</td><td>375</td><td>415</td></tr><tr><th class="row-label-new">new</th><td>175</td><td>185</td><td>195</td><td>205</td><td>215</td><td>225</td><td>235</td><td>245</td><td>255</td><td>265</td><td>275</td><td>285</td><td>295</td><td>305</td><td>315</td><td class="lvl-jump">365</td><td>415</td><td>465</td></tr><tr><th>Δ %</th><td><span class="badge buff1">+4%</span></td><td><span class="badge buff1">+3%</span></td><td><span class="badge buff1">+2%</span></td><td><span class="badge buff1">+1%</span></td><td><span class="badge neutral">0%</span></td><td><span class="badge nerf1">-1%</span></td><td><span class="badge nerf1">-2%</span></td><td><span class="badge nerf1">-3%</span></td><td><span class="badge nerf1">-3%</span></td><td><span class="badge nerf1">-4%</span></td><td><span class="badge nerf1">-5%</span></td><td><span class="badge nerf1">-5%</span></td><td><span class="badge nerf2">-6%</span></td><td><span class="badge nerf2">-6%</span></td><td><span class="badge nerf2">-7%</span></td><td class="lvl-jump"><span class="badge nerf2">-9%</span></td><td><span class="badge nerf3">-11%</span></td><td><span class="badge nerf3">-12%</span></td></tr></tbody></table>'
))
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
W(ul_close())
W(subnote("Damage at level 1 decreased from 53-57 to 52-56"))
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
W(li("Base Health Regen decreased by 1.0", bstat_h("Pangolier", "StatusHealthRegen", "7.41b", -1), extra=note_box(hero="Pangolier", field="StatusHealthRegen", before_patch="7.41b")))
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
W(ul_close())
W(subnote("Damage at level 1 increased from 56-58 to 57-59"))
W(subgroup("Talents"))
W(ul_open())
W(li("Level 10: Phantom Strike Duration increased from +0.6 to +0.8s", b(0.6, 0.8)))
W(ul_close())
W(hero_header("Phantom Lancer"))
W(subgroup("Abilities"))
W(ability("Phantom Rush"))
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
W(li("Base Damage increased by 2", bstat_h("Snapfire", "AttackDamageMin", "7.41b", 2), extra=note_box(hero="Snapfire", field="AttackDamageMin", before_patch="7.41b")))
W(ul_close())
W(subnote("Damage at level 1 increased from 51-57 to 53-59"))
W(hero_header("Spectre"))
W(ul_open())
W(li("Base Agility increased from 26 to 29", b(26, 29)))
W(ul_close())
W(subnote("Damage at level 1 increased from 49-53 to 52-56"))
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
W(ability("Storm Hammer"))
W(ul_open())
W(li("Mana Cost decreased from 110/115/120/125 to 110", b([110, 115, 120, 125], 110, l=True)))
W(ul_close())
W(hero_header("Techies"))
W(ul_open())
W(li("Base Mana Regen decreased by 0.5", bstat_h("Techies", "StatusManaRegen", "7.41b", -0.5), extra=note_box(hero="Techies", field="StatusManaRegen", before_patch="7.41b")))
W(li("Intelligence gain decreased from 3.0 to 2.7", b(3, 2.7),
     extra=inline_note("Damage gain per level decreased from 3.3 to 3.2 as a result")))
W(ul_close())
W(subgroup("Abilities"))
W(ability("M.A.D."))
W(ul_open())
W(li(
    'Mana Pool as Regen rescaled from <span class="formula-old">0.08% + 0.02% per level</span> to <span class="formula-trigger" data-formula="fld">0.1% + 0.01% per level</span>',
    '<span class="badge rework" data-tag="rework">REWORK</span><span class="badge-group" data-overall="buff"><span class="badge buff2">+10%</span></span>',
    extra='<table class="formula-table" id="fld" hidden><thead><tr><th></th><th>L1</th><th>L2</th><th>L3</th><th>L4</th><th>L5</th><th>L6</th><th>L7</th><th>L8</th><th>L9</th><th>L10</th><th>L11</th><th>L12</th><th>L13</th><th>L14</th><th>L15</th><th class="lvl-jump">L20</th><th>L25</th><th>L30</th></tr></thead><tbody><tr><th class="row-label-old">old</th><td>0.10%</td><td>0.12%</td><td>0.14%</td><td>0.16%</td><td>0.18%</td><td>0.20%</td><td>0.22%</td><td>0.24%</td><td>0.26%</td><td>0.28%</td><td>0.30%</td><td>0.32%</td><td>0.34%</td><td>0.36%</td><td>0.38%</td><td class="lvl-jump">0.48%</td><td>0.58%</td><td>0.68%</td></tr><tr><th class="row-label-new">new</th><td>0.11%</td><td>0.12%</td><td>0.13%</td><td>0.14%</td><td>0.15%</td><td>0.16%</td><td>0.17%</td><td>0.18%</td><td>0.19%</td><td>0.20%</td><td>0.21%</td><td>0.22%</td><td>0.23%</td><td>0.24%</td><td>0.25%</td><td class="lvl-jump">0.30%</td><td>0.35%</td><td>0.40%</td></tr><tr><th>Δ %</th><td><span class="badge buff2">+10%</span></td><td><span class="badge neutral">0%</span></td><td><span class="badge nerf2">-7%</span></td><td><span class="badge nerf3">-12%</span></td><td><span class="badge nerf4">-17%</span></td><td><span class="badge nerf4">-20%</span></td><td><span class="badge nerf5">-23%</span></td><td><span class="badge nerf5">-25%</span></td><td><span class="badge nerf6">-27%</span></td><td><span class="badge nerf6">-29%</span></td><td><span class="badge nerf6">-30%</span></td><td><span class="badge nerf6">-31%</span></td><td><span class="badge nerf6">-32%</span></td><td><span class="badge nerf6">-33%</span></td><td><span class="badge nerf7">-34%</span></td><td class="lvl-jump"><span class="badge nerf7">-37%</span></td><td><span class="badge nerf7">-40%</span></td><td><span class="badge nerf7">-41%</span></td></tr></tbody></table>'
))
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
    extra='<div class="correction-note"><span class="correction-label">Note:</span> The patch text says "decreased", but the values actually went up.</div>',
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
W(subgroup("Enchantment changes"))
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
W(ul_close())
W(subnote("Damage at level 1 increased from 45-51 to 47-53"))

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
W(ul_close())
W(subnote("Damage at level 1 increased from 49-56 to 51-58"))
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
W(ul_close())
W(subnote("Damage at level 1 decreased from 55-59 to 52-56"))
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
W(ability("Demonic Summoning"))
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
W(ability("Bullbelly Blitz"))
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
W(li("Agility gain increased from 2.0 to 2.2", b(2.0, 2.2),
     extra=inline_note("Damage gain per level increased from 3.2 to 3.3 as a result")))
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
W(ability("Changing of the Guard"))
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
W(ability("Rolling Thunder"))
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
W(ability("Flesh Heap"))
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
W(li("Base Mana Regen increased by 0.25", bstat_h("Skywrath Mage", "StatusManaRegen", "7.41a", 0.25), extra=note_box(hero="Skywrath Mage", field="StatusManaRegen", before_patch="7.41a")))
W(ul_close())

# Slardar
W(hero_header("Slardar"))
W(ability("Guardian Sprint"))
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
W(ul_close())
W(subnote("Damage at level 1 decreased from 51-57 to 50-56"))
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
W(ability("Tree Volley"))
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
W(ul_close())
W(subnote("Damage at level 1 increased from 53–73 to 56–76"))

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
W(ability("Lvl ? Pain"))
W(ul_open())
W(li("Curse Damage decreased from 15% to 10%", b(15, 10)))
W(ul_close())

# Invoker
W(hero_header("Invoker"))
W(ul_open())
W(li("Base Intelligence increased from 20 to 22", b(20, 22)))
W(ul_close())
W(subnote("Damage at level 1 increased from 39–45 to 41–47"))
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
W(ability("Outfight Them!"))
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
W(ul_close())
W(subnote("Damage at level 1 decreased from 49–55 to 46–52"))
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
W(ability("Rolling Thunder"))
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
W(ability("Proximity Mines"))
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
W(li("Base Mana Regen decreased by 0.6", bstat_h("Void Spirit", "StatusManaRegen", "7.41", -0.6), extra=note_box(hero="Void Spirit", field="StatusManaRegen", before_patch="7.41")))
W(ul_close())

# Windranger
W(hero_header("Windranger"))
W(ul_open())
W(li("Base Agility increased from 17 to 20", b(17, 20)))
W(ul_close())
W(subnote("Damage at level 1 increased from 47–59 to 49–61"))
W(ability("Tailwind"))
W(ul_open())
W(li("Duration increased from 2s to 2.5s", b(2, 2.5)))
W(li("Aghanim's Scepter bonus is still +1s, so it's increased to 3.5s", t("BUFF")))
W(ul_close())
W(ability("Focus Fire"))
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
W(li("Abilities that had 'per level up' scaling changed to be 'per level'", t("MISC")))
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
W(li("All sections of currents now give a max movement speed bonus of 150 ", t("BUFF")))
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
W(li_formula("Unyielding Shield Barrier regen upgrade increased",
             "3.5 per minute", "5 per minute",
             lambda M: 3.5 * M, lambda M: 5.0 * M,
             levels=[0, 5, 10, 15, 20, 25, 30, 40, 50, 60],
             level_prefix='M', rework_badge=False))
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
W(li("No longer deals damage to neutral units", t("DEL")))
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
W(li("Ancient neutral camps near stream ends demoted to medium camps and moved slightly towards bases", t("NERF")))
W(li("Medium neutral camp near offlane defender's gate has been demoted to a small neutral camp", t("NERF")))
W(li("The tier 1 safe lane towers have been moved slightly away from their pull camps and where the creeps meet", t("BUFF")))
W(li("Radiant safe lane small camp has been slightly moved north away from the lane", t("MISC")))
W(li("Radiant safe lane hard camp's spawn box has been moved towards the offlane to remove a bad ward location", t("MISC")))
W(li("Radiant offlane tier 2 tower has been adjusted slightly to the left, such that creeps do not path on both sides of the tower", t("BUFF")))
W(li("The ramp leading from the Radiant tier 1 tower to the stream has been decreased in width and moved away from the tower", t("NERF")))
W(li("The medium flooded camp near the safe lane tier 2 towers moved closer to the middle of the stream (substantially more for Dire than for Radiant)", t("MISC")))
W(li("The medium flooded camp near the safe lane tier 2 towers can now only evolve once into a hard camp, rather than into an Ancient Camp", t("NERF")))
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
W(li("Historically, Lifesteal was calculated before some damage reductions or amplifications were applied. As a result, you could gain health from attacks that dealt no damage (like attacks against a hero affected by Aeon Disk's Combo Breaker). This will not happen anymore", t("REWORK")))
W(ul_close())
W(subnote("The only amplification that is not taken into account is increased damage against illusions"))

W(subgroup("Miscellaneous"))
W(ul_open())
W(li("All sources of reflection damage now have an ALT-note detailing mechanics of reflected damage", t("MISC")))
W(ul_close())
W(subnote("The following items and abilities deal reflected damage:<br>* Tormentor's Reflect ability<br>* Blade Mail (both active and passive)<br>* Chipped Vest<br>* Rattlecage<br>* Axe's Counter Helix<br>* Bristleback's Quill Spray triggered by Bristleback passive<br>* Centaur Warrunner's Retaliate<br>* Nyx Assassin's Spiked Carapace<br>* Queen of Pain's Scream of Pain<br>* Razor's Storm Surge<br>* Shadow Demon's Disseminate<br>* Spectre's Dispersion<br>* Tidehunter's Anchor Smash triggered by Kraken Shell passive<br>* Viper's Corrosive Skin<br>* Warlock's Fatal Bonds"))
W(ul_open())
W(li("Reflected damage cannot be reflected back", t("NERF")))
W(li("Lifesteal and Spell Lifesteal don't apply to reflected damage", t("NERF")))
W(li("Reflected damage doesn't affect Debuff Immune units", t("NERF")))
W(li("Units with free movement now can miss their attacks when attacking uphill targets", t("NERF")))
W(ul_close())
W(subnote("Affected units:<br>* Batrider during Firefly<br>* Dragon Knight during Elder Dragon Form with Aghanim's Scepter<br>* Lina during Flame Cloak<br>* Terrorblade's Reflection illusions"))

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
W(unit_header("Ghost", _NC_CDN + "ghost.png"))
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

W(plain_header("Shop Reshuffle"))
W(ul_open())
W(li("Items in all shop categories except for Consumables have been rearranged to accommodate new items", t("MISC")))
W(li("Consumables now includes Infused Raindrops", t("MISC")))
W(ul_close())

W(plain_header("Basic Items"))
W(item_header("Chasm Stone", new="New Miscellaneous Item"))
W(ul_open())
W(li("Costs 800 gold", t("NEW")))
W(li("+40 Area of Effect", t("NEW")))
W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("NEW")))
W(ul_close())
W(item_header("Shawl", new="New Miscellaneous Item"))
W(ul_open())
W(li("Costs 450 gold", t("NEW")))
W(li("+10% Magic Resistance", t("NEW")))
W(ul_close())
W(item_header("Splintmail", new="New Equipment Item"))
W(ul_open())
W(li("Costs 950 gold", t("NEW")))
W(li("+7 Armor", t("NEW")))
W(ul_close())
W(item_header("Wizard Hat", new="New Miscellaneous Item"))
W(ul_open())
W(li("Costs 250 gold", t("NEW")))
W(li("+125 Mana", t("NEW")))
W(ul_close())
W(item_header("Chainmail"))
W(ul_open())
W(li("Cost decreased from 550g to 500g", b(550, 500, l=True)))
W(ul_close())
W(item_header("Cloak"))
W(ul_open())
W(li("Cost increased from 800g to 900g", b(800, 900, l=True)))
W(li("Magic Resistance bonus decreased from +20% to +18%", b(20, 18)))
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
W(li("Reset Cooldowns no longer refreshes items", t("NERF")))
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

W(plain_header("Upgrades"))
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
W(li("Doesn't work with other sources of secondary projectiles from hero abilities",
     t("NEW"),
     extra=show_list("Gyrocopter's Flak Cannon", "Medusa's Split Shot", "Muerta's Gunslinger")))
W(ul_close())
W(item_header("Hydras Breath", new="New Armaments Item"))
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
         ("NEW", "+60/90/120/150/180 Cast Range")],
    new_extras={3: show_list("Cast Range Bonus does not stack with Aether Lens or multiple Dagons",
                              summary="Stacking rules")}))
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
W(li("Recipe cost increased from 800 to 850 " + b(800, 850, l=True) + ". Total cost unchanged at 1775g (due to Chainmail cost decrease)", t("MISC")))
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
W(properties_change(
    old=[("DEL", "+6 Health Regen")],
    new=[]))
W(ul_open())
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
W(item_header("Skadi"))
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
W(li("Recipe Cost decreased from 800 to 675. Total cost unchanged at 3725g (due to Cloak cost increase)", b(800, 675, l=True)))
W(li("Barrier no longer affects units that have been affected by Barrier within Pipe of Insight's cooldown", t("NERF")))
W(li("Insight Aura no longer provides 2.5 health regen", t("DEL")))
W(ul_close())
W(item_header("Radiance"))
W(ul_open())
W(li("Burn toggling no longer breaks invisibility nor stops channels", t("MISC")))
W(ul_close())
W(item_header("Refresher"))
W(ul_open())
W(li("Health Regen bonus increased from +12 to +14", b(12, 14)))
W(li("Mana Regen bonus increased from +6 to +7", b(6, 7)))
W(li("Reset Cooldowns cooldown decreased from 180/190/200/210s to 180s", b([180, 190, 200, 210], 180, l=True),
     extra=inline_note("No longer scales with uses")))
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
W(li("Freezing Aura now pierces debuff immunity", t("BUFF")))
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
W(li("Recipe cost increased from 250 to 300 " + b(250, 300, l=True) + ". Total cost unchanged at 2775g (due to Chainmail cost decrease)", t("MISC")))
W(ul_close())
# ===== NEUTRAL ITEM UPDATES =====
W(section("Neutral Item Updates"))
W(subgroup("General changes"))
W(ul_open())
W(li("Tier 1 availability changed from 5:00 to 0:00", t("REWORK")))
W(li("Madstone crafting cost for Tier 1 items increased from 5 to 6", t("REWORK")))
W(ul_close())
W(subgroup("Artifact changes"))
W(ul_open())
W(li("Number of artifact choices increased from 4 to 5 for Tiers 2-5", t("REWORK")))
W(ul_close())
W(item_header("Ash Legion Shield"))
W(ul_open())
W(li("Shield Wall damage barrier increased from 140 to 160", b(140, 160)))
W(li("Shield Wall movement speed reduction increased from 12 to 20", t("NERF")))
W(ul_close())
W(item_header("Chipped Vest"))
W(ul_open())
W(li("Chipper damage returned to attacking creeps decreased from 20 to 15", b(20, 15)))
W(ul_close())
W(item_header("Dagger of Ristul", new="Returning Tier 1 Artifact"))
W(ul_open())
W(li("Active: Imbrue. Increase attack damage by 25 for 8s. Health Cost: 100. Cooldown: 30s", t("NEW")))
W(ul_close())
W(item_header("Foragers Kit", new="New Tier 1 Artifact"))
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
W(li("Burn Through: Total Damage decreased from 90 to 80 ", b(90, 80)))
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
W(item_header("Gunpowder Gauntlets"))
W(ul_open())
W(li("Beat the Crowd cooldown increased from 6s to 10s", b(6, 10, l=True)))
W(ul_close())
W(item_header("Jidi Pollen Bag"))
W(ul_open())
W(li("Pollinate health restoration loss increased from 30% to 50%", b(30, 50)))
W(li("Pollinate now also modifies incoming healing", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(item_header("Partisans Brand", new="New Tier 3 Artifact"))
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
W(li("Pupate duration increased from 4s to 5s ", b(4, 5)))
W(ul_close())
W(subnote("From 5.2s to 6.5s with Dormant Curio"))
W(ul_open())
W(li("Pupate bonus magic resistance increased from 35% to 50%", b(35, 50)))
W(ul_close())
W(item_header("Prophets Pendulum", new="New Tier 4 Artifact"))
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
W(item_header("Heavy Blade", new="Returning Tier 5 Artifact"))
W(ul_open())
W(li("Active: Cleanse. Apply basic dispel on all units in a 300 unit radius area. Cast Range: 500. Mana Cost: 150. Cooldown: 40s", t("NEW")))
W(li("Passive: Subjugate. Your attacks deal bonus magical damage equal to 4% of target's Max Mana", t("NEW"),
     extra=inline_note("Dormant Curio increases damage from 4% to 5.2%")))
W(ul_close())
W(plain_header("Enchantment Changes"))
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
W(li("Tiers changed from 2-4 to 5", t("MISC")))
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
W(ability("Mist Coil"))
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
_bc_pill, _bc_table = scale_pill(
    "0.1 + 0.1 per 3 levels",
    lambda L: 0.1 + 0.1 * (L // 3),
    levels=[1, 3, 6, 9, 12, 15, 20, 25, 30],
    value_fmt="{:.2f}",
)
W(ability_change(
    old=dict(
        name="Death Rime",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Ancient Apparition's abilities apply frost stacks that deal <b>10 damage per second</b> and <b>1.5% movement slow</b> for each stack on the enemy.",
        ],
    ),
    new=dict(
        name="Bone Chill",
        slug="ancient_apparition_bone_chill",
        innate=True,
        desc=[
            "Innate. Passive, improves with Ancient Apparition's level.",
            "When Ancient Apparition deals magic damage with his abilities, affected enemies are chilled for 4s, reducing their movement speed by 2% per stack. Each instance stacks and has independent duration.",
            "If the target is an enemy hero, the debuff also reduces their Strength by "
            + _bc_pill
            + ".",
            aghs_line("Increases Base Strength Reduction by 0.3."),
        ],
        tables=[_bc_table],
    ),
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
W(ability("Persecutor"))
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
W(li("Agility gain decreased from 3.0 to 2.7", b(3.0, 2.7),
     extra=inline_note("Damage gain per level decreased from 3.6 to 3.4 as a result")))
W(li("Base Movement Speed increased from 285 to 300", b(285, 300)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Runic Infusion",
        slug="arc_warden_runic_infusion",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Upon activating any rune, Arc Warden gains the Regeneration Rune buff for 4s. Duration is reduced by 34% for activating Bounty or Water Runes.",
            "Activating a Wisdom Rune provides a full 4s buff. Activating a Regeneration Rune creates a stackable second effect.",
        ],
    ),
    new=dict(
        name="Runic Infusion",
        slug="arc_warden_runic_infusion",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Whenever Arc Warden or the Tempest Double activates a Power Rune, Arc Warden permanently gains +1.5 all attributes.",
        ],
    ),
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
            "Innate. Passive, can't be leveled up.",
            "Whenever Axe kills an enemy, he gains <b>+1 permanent armor</b>. Kills with Culling Blade give <b>2×</b> that amount.",
        ],
    ),
    new=dict(
        name="One Man Army",        innate=True,
        desc=[
            "Innate. Passive.",
            "Increases Axe's Strength by 50% of his armor, as long as there are no allied heroes within a 700 unit radius of him.",
            "The effect fades over 3s after an ally walks within range. Bonus Strength can be broken.",
        ],
    ),
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
W(li("Intelligence gain decreased from 2.7 to 2.5", b(2.7, 2.5),
     extra=inline_note("Damage gain per level decreased from 3.6 to 3.4 as a result (Bane is Universal — all three attribute decreases contribute)")))
W(li("Attack Range increased from 400 to 425", b(400, 425)))
W(ul_close())
W(ability_change(
    old=dict(
        name="Ichor of Nyctasha",
        slug="bane_ichor_of_nyctasha",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Bane's attribute gains are always evenly distributed across all three attributes.",
            "Example: Belt of Strength that provides +6 Strength will instead increase all three attributes by 2.",
        ],
    ),
    new=dict(
        name="Ichor of Nyctasha",
        slug="bane_ichor_of_nyctasha",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Every time Bane kills an enemy hero or they die under the effect of any debuff applied by Bane, they receive a Terror for the rest of the game.",
            "Each Terror stack decreases the enemy's status resistance to all Bane's debuffs by 5%. Max Terror stacks per hero: 5.",
        ],
    ),
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
    levels=[1, 5, 10, 15, 20, 25, 30],
)
W(ability_change(
    old=dict(
        name="Rugged",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Passive damage block: Beastmaster has a chance to block incoming attack damage from non-hero units.",
            "Per 7.39b, no longer increased block chance against towers — applied only to creep-source attacks.",
        ],
    ),
    new=dict(
        name="Inner Beast",
        slug="beastmaster_inner_beast",
        innate=True,
        desc=[
            "Innate. Passive, can be leveled up with skill points.",
            "Provides bonus Attack Speed to Beastmaster and units under his control: " + _ib_pill + ".",
        ],
        tables=[_ib_table],
    ),
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
))
W(ul_open())
W(li("Cooldown decreased from 45/40/35/30s to 30s", b([45, 40, 35, 30], 30, l=True)))
W(li("Dive Damage increased from 50/80/110/140 to 60/95/130/165", b([50, 80, 110, 140], [60, 95, 130, 165])))
W(li("Root Duration increased from 0.25/0.5/0.75/1s to 0.4/0.6/0.8/1s", b([0.25, 0.5, 0.75, 1], [0.4, 0.6, 0.8, 1])))
W(li("Hawk armor increased by 1",
     bstat_u("npc_dota_beastmaster_hawk", "ArmorPhysical", "7.40c", 1),
     extra=note_box(unit="npc_dota_beastmaster_hawk", field="ArmorPhysical", before_patch="7.40c")))
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
            "Innate. Passive, can't be leveled up.",
            "When getting a kill or assist on an enemy with a kill streak, Bounty Hunter gains <b>10% extra gold</b>.",
        ],
    ),
    new=dict(
        name="Big Game Hunter",        innate=True,
        desc=[
            "Innate. Passive.",
            "Bounty Hunter receives 15% more kill and assist gold if the dying enemy hero is Big Game. An enemy hero is considered Big Game if they are one of the top 3 net worth heroes on the enemy team.",
            "Bounty Hunter has a list of heroes that are currently considered Big Game, accessible by pressing a special button over the innate.",
            "These heroes also have a debuff pointing out that they're among the three Big Game targets. Debuff is visible only to Bounty Hunter and his allies.",
        ],
    ),
))
W(ability("Jinada"))
W(ul_open())
W(li("Gold Steal increased from 12/20/28/36 to 15/22/29/36", b([12, 20, 28, 36], [15, 22, 29, 36])))
W(ul_close())
W(ability("Shadow Walk"))
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
            "Innate. Passive, can't be leveled up.",
            "Centaur Warrunner permanently gains <b>+40 max health</b> every <b>120s</b>.",
        ],
    ),
    new=dict(
        name="Horsepower",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Centaur Warrunner gains 30% of his Strength as bonus movement speed.",
            "This movement speed bonus does not stack with bonuses from boots.",
        ],
    ),
))

# Chaos Knight
W(hero_header("Chaos Knight"))
W(ability_change(
    old=dict(
        name="Reins of Chaos",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Whenever illusions of Chaos Knight are created, there is a 50% chance that an additional 1 illusion will spawn.",
        ],
    ),
    new=dict(
        name="Fundamental Forging",        innate=True,
        desc=[
            "Innate. Passive.",
            "When Chaos Knight crafts a neutral item, it gets an additional random enchantment that doesn't provide negative stats.",
            "The random enchantment is selected from all available enchantments in that tier, including ones that are normally not available for Strength heroes. The random enchantment is different from the one used in crafting.",
            "Due to negative stats, Chaos Knight can't randomly get Crude, Nimble, Keen-Eyed, Titanic, Greedy, Hulking, Audacious, Feverish, or Manic enchantments.",
        ],
    ),
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
            "Innate. Active, levels with Holy Persuasion and improves with Chen's level.",
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
            "Innate. Passive and active components. Improves with game's time.",
            "When Chen respawns, he is joined in battle by a Zealot — a melee creep warrior with the Martyrdom ability. Zealot has the same stats as the current melee creeps on his team (including super or mega form), but has 125 attack range, base damage increased by 2 per Chen's level, base health regen increased from 0.5 to 2.5, and doesn't have Runty attack type. Zealot respawns after 60s dead.",
            "<b>Martyrdom:</b> 500-range unit-targeted ability on the Zealot creep, targeting either an enemy or ally. When cast, the Zealot sacrifices itself, firing a projectile at 1000 speed dealing damage to enemies or healing allies. Damage = 25 + 20% of the Zealot's current health; healing = 50% of these values.",
            "Can also be cast on a controlled unit to teleport it to Chen after a 6s delay. Self-targeting teleports all controlled units. Mana Cost: 50. Cooldown: 10s.",
            "Mechanics moved from Divine Favor without any changes.",
        ],
    ),
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
            "Innate. Passive.",
            "Clockwerk's outgoing damage is increased by 0.25% per point of armor.",
        ],
    ),
    new=dict(
        name="Armor Power",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Clockwerk's outgoing damage is increased by 0.25% per point of armor.",
            "Clockwerk can self-cast a Chainmail item to consume it, gaining +4 Armor per Chainmail consumed. Number of stacks is unlimited.",
        ],
    ),
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
    levels=[1, 5, 10, 15, 20, 25, 30],
)
W(ability_change(
    old=dict(
        name="Blueheart Floe",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Crystal Maiden has <b>50% Mana Regen Amplification</b>.",
        ],
    ),
    new=dict(
        name="Glacial Guard",
        slug="crystal_maiden_glacial_guard",
        innate=True,
        desc=[
            "Innate. Passive.",
            "A portion of the mana Crystal Maiden spends on her abilities is converted into a physical barrier for 8s. Barriers stack, but each instance has independent duration.",
            "Mana Spent to Barrier: " + _cm_pill + ".",
        ],
        tables=[_cm_table],
    ),
))
W(ability("Arcane Aura"))
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
            "Innate. Passive, improves with Dark Seer's level.",
            "When Dark Seer levels up, he restores a percentage of his max Health and Mana. Restore percentage = <b>10% + 2% per hero level</b>. Disabled by Break.",
            "Also passively grants <b>1 Attack Speed per point of Intelligence</b>.",
        ],
    ),
    new=dict(
        name="Quick Wit",
        innate=True,
        desc=[
            "Innate. Passive, improves with Dark Seer's level.",
            "Whenever Dark Seer casts an ability, he restores 8.5% of Max Health and 8.5% of Max Mana, plus 1.5% per Dark Seer level.",
            "Also provides Dark Seer with +1 attack speed for each point of Intelligence.",
        ],
    ),
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
            "Innate. Passive.",
            "Whenever a hero ability makes Dark Willow untargetable or hidden, she gains <b>+100% Health Regen</b> and <b>+100% Mana Regen</b> while in that state.",
        ],
    ),
    new=dict(
        name="Pixie Dust",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Dark Willow's Health Regen and Mana Regen always have 20% Amplification.",
            "Amplification increases to 100% whenever she becomes untargetable or invulnerable.",
        ],
    ),
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
W(ul_close())
W(subnote("Damage at level 1 increased from 50–54 to 56–60"))
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
W(ability("Weave"))
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
            "Innate. Passive, can't be leveled up.",
            "Doom's attacks deal <b>25% more damage</b> to enemies whose level is lower than his.",
            "Per 7.36b: also works at level 30. Per 7.37d: only Doom's attacks (not allied sources).",
        ],
    ),
    new=dict(
        name="Lvl ? Pain",
        slug="doom_bringer_lvl_pain",
        innate=True,
        desc=[
            "Innate. Passive.",
            "When Doom attacks enemy heroes, he applies a curse upon them. After 2.5s, the cursed hero bursts with a pillar of fire, damaging itself and all enemy units in a 66 AoE for 15% of the damage taken from Doom (the hero) over this duration, including damage from the attack that applied the curse.",
            "If the cursed hero's level is a multiple of 6, the curse damage and radius will be increased by 66%.",
        ],
    ),
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
W(li("Fixed the cast indicator not matching the actual damage range of the ability, and also to properly reflect cast range bonuses", t("MISC")))
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
W(ul_close())
W(subnote("Damage at level 1 decreased from 51–58 to 49–56"))
W(ability("Precision Aura"))
W(ul_open())
W(li("No longer levels with Marksmanship", t("REWORK")))
W(li("Agility Base Bonus rescaled from 4/8/12/16% to 10%", b([4, 8, 12, 16], 10)))
W(ul_close())
W(ability("Frost Arrows"))
W(ul_open())
W(li("Now also modifies incoming healing with Aghanim's Scepter", t("NEW"),
     extra=inline_note("As a result of Health Restoration changes")))
W(ul_close())
W(ability("Gust"))
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
W(ability("Stone Remnant"))
W(ul_open())
W(li_formula("Max Charges changed",
             "7 + 1 per 4 level ups", "7 + 1 per 4 levels",
             lambda L: 7 + (L - 1) // 4, lambda L: 7 + L // 4,
             levels=[1, 4, 5, 8, 12, 16, 20, 25, 30],
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Tip The Scales",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "(7.37 introduction did not include a mechanic line in the patchnote — needs canonical in-game text.)",
        ],
    ),
    new=dict(
        name="Momentum",        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Elder Titan's armor increases by " + _et_pill + " of his bonus movement speed."
            '<div class="inline-note">Only counts movement speed he has above his base (305) value. '
            'Cannot reduce armor when he is slowed below base movement speed.</div>',
        ],
        tables=[_et_table],
    ),
))
W(ability("Astral Spirit"))
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
W(ability("Rabble-Rouser"))
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
W(li("Added a tooltip to display the total max possible heal", t("MISC")))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
)
W(ability_change(
    old=dict(
        name="Gravity Well",
        innate=True,
        desc=[
            "Innate. Passive, scales with Black Hole.",
            "Allies in a 500 unit radius around Enigma have an Incoming Damage Reduction buff that gradually increases with proximity: 0% at 500 distance, up to 9/11/13/15% at 200 distance.",
            "Doesn't affect Enigma itself.",
        ],
    ),
    new=dict(
        name="Event Horizon",        innate=True,
        desc=[
            "Innate. Passive, improves with Enigma's level.",
            "Units in a 600 radius moving away from Enigma have a movespeed penalty equal to " + _en_pill + ".",
        ],
        tables=[_en_table],
    ),
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
            "Innate. Passive, levels up with Chronosphere.",
            "Enemy attack projectiles are slowed when they fly near Faceless Void. Affects projectiles even if Faceless Void isn't the target.",
            "<b>Projectile Slow:</b> 25/30/35/40%. <b>Radius:</b> 500.",
        ],
    ),
    new=dict(
        name="Distortion Field",
        innate=True,
        desc=[
            "Innate. Passive, no longer levels with Chronosphere.",
            "Now only applies to projectiles targeting Faceless Void or an allied hero within a 1200 radius of him.",
            "Slows enemy attack projectile speed by a flat 40% within a 500 radius around the targeted hero.",
        ],
    ),
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
W(ability("Stroke of Fate"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Chop Shop",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Gyrocopter can disassemble most items at all times and sells any Recipe he has for a full cost.",
            "Cannot disassemble Divine Rapier or Hand of Midas.",
        ],
    ),
    new=dict(
        name="Afterburner",
        slug="gyrocopter_afterburner",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Whenever Gyrocopter damages an enemy with attacks or abilities, he gains +1 movement speed per hero damaged and +0.5 per creep. Effects stack independently.",
            "Buff duration: " + _gy_pill + ".",
        ],
        tables=[_gy_table],
    ),
))
W(ability("Flak Cannon"))
W(ul_open())
W(li("Aghanim's Scepter upgrade moved into a separate ability", t("MISC")))
W(ul_close())
W(ability("Side Gunner"))
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
             value_fmt="{:g}", jump_at=7))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Wellspring",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
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
            "Innate. Passive.",
            "Io always has bonus Outgoing Damage Amp that linearly scales with its health, reaching maximum " + _io_pill + " at 100% Health.",
            "At the same time, Io has Health Restoration and Healing Amplifications that also linearly scale with its health, reaching the same maximum at 0% Health.",
        ],
        tables=[_io_table],
    ),
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
W(ability("Liquid Frost"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.2f}",
)
W(ability_change(
    old=dict(
        name="Duelist",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Juggernaut deals <b>10% more damage</b> to targets that are facing him. Damage bonus is always applied during Omnislash.",
        ],
    ),
    new=dict(
        name="Bladeform",        innate=True,
        desc=[
            "Innate. Passive.",
            "Juggernaut receives a stack of Bladeform every 2s he does not take damage. Maximum 10 stacks. Stacks fade after 2s upon taking any damage.",
            "Each stack grants " + _jg_pill + " base Agility bonus and 1% movement bonus.",
        ],
        tables=[_jg_table],
    ),
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
            "Innate. Passive, can't be leveled up.",
            "Keeper of the Light's mana <b>cannot go below 75</b>.",
        ],
    ),
    new=dict(
        name="Bright Speed",
        slug="keeper_of_the_light_bright_speed",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Keeper of the Light gains +1 movement speed for every 2.5 Intelligence.",
            "Whenever Keeper of the Light moves 300 distance, he leaves behind light that allows him to see in 400 range for 3 seconds.",
        ],
    ),
))
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
W(ability("Switch Discipline"))
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
W(li("Cast Range decreased from 1200 to 650/750/850/950 ", b(1200, [650, 750, 850, 950])))
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
W(ability("Bullbelly Blitz"))
W(ul_open())
W(li("Now also deals 20/30/40 magical damage by default", t("NEW")))
W(li("Aghanim's Scepter: Increases magic damage by 6/12/18 per Groovin' stack when this song is used in double-strumming", t("NEW")))
W(ul_close())
W(ability("Hotfeet Hustle"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Outfight Them!",
        slug="legion_commander_outfight_them",
        innate=True,
        desc=[
            "Innate. Passive, levels up with Duel.",
            "When attacking an enemy hero of <b>equal or higher level</b> than Legion Commander, she gains <b>+30/40/50/60% Health Restoration</b> for <b>4s</b>. Always applies when attacking a max-level enemy hero.",
        ],
    ),
    new=dict(
        name="Outfight Them!",
        slug="legion_commander_outfight_them",
        innate=True,
        desc=[
            "Innate. Passive, improves with Legion Commander's level.",
            "Passively grants Legion Commander " + _lc_pill + " bonus armor at all times.",
            "Whenever Legion Commander <b>casts an ability</b>, she gains the same amount again as a <b>stacking 6s buff</b> (stacks independently per cast).",
            "Whenever <b>allies within 1200 range</b> cast an ability, they also gain a 6s buff for <b>50% of the value</b>. Ally buffs stack independently.",
        ],
        tables=[_lc_table],
    ),
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
W(li("Duration improved from 10s to 8s ", b(10, 8)))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}%",
)
_lich_xp_pill, _lich_xp_table = scale_pill(
    "69% + 6% per level",
    lambda L: 69.0 + 6.0 * L,
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}%",
)
W(ability_change(
    old=dict(
        name="Death Charge",
        slug="lich_death_charge",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
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
            "Innate. Active, targets an allied creep within 700 range and instantly kills it.",
            "Lich gains mana equal to " + _lich_mana_pill + " of the creep's <b>current</b> health and experience bounty equal to " + _lich_xp_pill + " of the creep's value.",
            "<b>No Mana Cost. Cooldown: 120s.</b> Starts on extended cooldown with no charges — the first cast is only possible at the 2:00 mark.",
            "Sacrificed creeps count as denies, providing experience to enemy heroes (Lich's experience gain is independent from what enemies receive).",
        ],
        tables=[_lich_mana_table, _lich_xp_table],
    ),
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
W(ul_close())
W(subnote("Damage at level 1 increased from 39–45 to 49–55"))
_lsf_pill, _lsf_table = scale_pill(
    "5 per level",
    lambda L: 5.0 * L,
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}",
)
W(ability_change(
    old=dict(
        name="Feast",
        slug="life_stealer_feast",
        innate=True,
        desc=[
            "Innate. Passive, levels up with Infest.",
            "Lifestealer's attacks deal bonus magic damage equal to <b>1.25/1.75/2.25/2.75%</b> of target's max health and lifesteal back <b>1.25/1.75/2.25/2.75%</b> of target's max health.",
            "Also allows hitting allied creeps below <b>75%</b> health (default deny threshold is 50%).",
        ],
    ),
    new=dict(
        name="Ghoul Frenzy",
        slug="life_stealer_ghoul_frenzy",
        innate=True,
        desc=[
            "Innate. Passive, occupies the slot vacated by Feast (Feast moved back to a regular ability).",
            "Provides Lifestealer with " + _lsf_pill + " bonus Attack Speed at all times.",
        ],
        tables=[_lsf_table],
    ),
))
W(ability("Rage"))
W(ul_open())
W(li("Now also provides 9/12/15/18% bonus movement speed while active", t("NEW")))
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
            "Innate. Passive, levels up with Laguna Blade.",
            "Lina's fire damage stacks <b>Overheat</b> on enemies. When the target reaches the <b>175 damage threshold</b>, they combust and take additional Overheat damage.",
            "<b>Overheat Damage:</b> 15/35/55/75 (post-7.39).",
        ],
    ),
    new=dict(
        name="Slow Burn",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Lina's abilities deal an <b>additional 64%</b> damage as <b>undispellable burn damage over 4s</b>.",
            "Applies on top of the spell's base damage and stacks duration on re-application.",
        ],
    ),
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
            "Innate. Passive, can't be leveled up.",
            "Lion gains <b>20% debuff duration</b> and <b>20% spell amplification</b> for <b>90s</b> after respawning.",
            "Refreshes every time he dies and respawns.",
        ],
    ),
    new=dict(
        name="To Hell and Back",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up. Reworked into a two-trigger buff:",
            "<b>Kill / assist trigger:</b> killing or assisting in a Hero kill grants Lion <b>20% debuff duration</b> against that hero <b>while it is dead</b>.",
            "<b>Respawn trigger:</b> whenever Lion respawns or resurrects, he gains <b>20% spell amplification</b> for <b>90s</b>, or until he gets a kill or an assist (whichever comes first).",
        ],
    ),
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
W(ul_close())
W(subnote("Damage at level 1 increased from 55–63 to 56–64"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}s",
)
W(ability_change(
    old=dict(
        name="Special Delivery",
        slug="marci_special_delivery",
        innate=True,
        desc=[
            "Innate. Passive + Active.",
            "<b>Passive:</b> permanently increases the level of all allied couriers by <b>3</b> and hero attacks to kill the courier by <b>1</b> (so Marci's team starts with flying couriers).",
            "<b>Active</b> (added in 7.38): Marci whistles and instantly teleports her courier to her location. <b>Cast Point:</b> 1s. <b>Cooldown:</b> 240s (flat).",
        ],
    ),
    new=dict(
        name="Special Delivery",
        slug="marci_special_delivery",
        innate=True,
        desc=[
            "Innate. Active. Reworked delivery logic:",
            "If Marci's courier is <b>in the fountain</b> when Special Delivery is cast, the courier <b>takes all items from the stash</b> before teleporting.",
            "The courier now <b>automatically attempts to transfer items</b> upon arrival, then heads back to the fountain.",
            "If the courier still has any extra items after the transfer attempt — or didn't transfer anything — it <b>stays next to Marci</b> instead of returning.",
            "<b>Cooldown:</b> " + _marci_cd_pill + " (was a flat 240s).",
        ],
        tables=[_marci_cd_table],
    ),
))
W(ability_change(
    old=dict(
        name="Bodyguard",
        slug="marci_bodyguard",
        desc=[
            "Active. Cast on an ally to bind a protective bond between Marci and the target — the ally receives a temporary defensive effect that scales with ability rank.",
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
))
W(ability("Rebound"))
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
W(ability("Gorgon's Grasp"))
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
            "Innate. Passive, can't be leveled up.",
            "Meepo receives an additional choice when activating <b>neutral item tokens</b>.",
        ],
    ),
    new=dict(
        name="Geomancy",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Each Meepo (main + clones) grants stacking bonuses to <b>all</b> Meepos based on the terrain it stands on:",
            "<b>Tree within 250 range</b> → +1 Health Regen.",
            "<b>On solid ground</b> → +2% bonus movement speed.",
            "<b>In water</b> → attacks slow the target by 2% for 2s.",
            '<div class="inline-note">Each Meepo can provide only one tree bonus regardless of how many trees are in range. '
            "If there's a tree in the water, that Meepo provides both the water and tree bonuses.</div>",
        ],
    ),
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}",
)
W(ability_change(
    old=dict(
        name="Selemene's Faithful",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Healing Lotuses are <b>20% more effective</b> on Mirana and her allies — both Lotus pickups and the AoE pulse hand out a larger heal when Mirana is involved.",
        ],
    ),
    new=dict(
        name="Celestial Quiver",
        slug="mirana_celestial_quiver",
        innate=True,
        desc=[
            "Innate. Auto-cast attack modifier, can't be leveled up.",
            "Mirana consumes a charge to empower her next attack with bonus magic damage equal to " + _mira_pill + ".",
            "Starts with <b>2 max charges</b> and gains <b>+1 max charge every 7 levels</b>. <b>Base Charge Restore Time:</b> 6s.",
            aghs_shard_line("Casting Leap provides 3 temporary charges for the duration of the buff. These temporary charges ignore the max-charges cap and stack from each Leap cast."),
        ],
        tables=[_mira_table],
    ),
))
W(ul_open())
W(li("Upgraded with Aghanim's Shard", t("NEW"),
     extra=inline_note("Casting Leap provides 3 temporary charges for the duration of the buff."
                       "<br>These temporary charges ignore the max charges count and stack from each Leap cast.")))
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
W(ability("Changing of the Guard"))
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
            "Innate. Passive, can't be leveled up.",
            "Morphling receives <b>50% of Attribute gain bonuses every half level</b> instead of full bonuses at level up.",
            "Also increases <b>All Attributes bonus gained for skill points in the Talent Tree from +2 to +4</b>.",
        ],
    ),
    new=dict(
        name="Ebb and Flow",
        slug="morphling_ebb_and_flow",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Strength and Agility now provide Morphling with additional bonuses (also active while replicating, except the extra attack range, which only applies when replicating a ranged unit):",
            "<b>Strength to Cast Range:</b> 20%. <b>Strength to Slow Resistance:</b> 20%.",
            "<b>Agility to Movement Speed:</b> 15%. <b>Agility to Ranged Attack Range:</b> 20%.",
        ],
    ),
))
W(ability("Waveform"))
W(ul_open())
W(li("Cast Range decreased from 700/800/900/1000 to 700/775/850/925", b([700, 800, 900, 1000], [700, 775, 850, 925])))
W(ul_close())
W(ability("Adaptive Strike"))
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
            "Innate. Passive.",
            "Muerta is permanently endowed with <b>passive ethereal bonuses</b>: she can always attack ethereal targets and can be attacked while ethereal herself.",
            "While either she or her target is ethereal, her attack damage converts to magical and her physical lifesteal is treated as spell lifesteal.",
        ],
    ),
    new=dict(
        name="Supernatural",
        slug="muerta_supernatural",
        innate=True,
        desc=[
            "Innate. Passive. Reworked into a hero-kill-driven stacking buff:",
            "Whenever an <b>enemy hero dies within 925 units</b> of Muerta, she gains a stack of <b>1% spell amplification</b>. Max stacks equal her current hero level.",
            "When Muerta dies she <b>loses half the stacks</b>, rounded down.",
            "Passive ethereal bonuses moved to <b>Pierce the Veil</b>.",
        ],
    ),
))
W(ability("Pierce the Veil"))
W(ul_open())
W(li("Now grants +75% base damage", t("NEW")))
W(li("Now has a passive component", t("NEW"),
     extra=inline_note("Muerta can always attack ethereal targets and can attack when she is ethereal. When either she or her target is ethereal, all of her attack damage is dealt as magical damage and her physical lifesteal is treated as spell lifesteal."
                       "<br>Lifesteal conversion happens only for attacks and won't affect her spells.")))
W(li("No longer provides 70/100/130 bonus damage", t("DEL")))
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
W(li("Minimum Base damage increased by 4 ", bstat_h("Nature's Prophet", "AttackDamageMin", "7.40c", 4), extra=note_box(hero="Nature's Prophet", field="AttackDamageMin", before_patch="7.40c")))
W(li("Damage spread decreased from 10 to 6", b(10, 6)))
W(ul_close())
W(subnote("Damage at level 1 increased from 40–50 to 44–50"))
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
W(ability("Nature's Call"))
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
W(ability_change(
    old=dict(
        name="Heart of Darkness",
        innate=True,
        desc=[
            "Innate. Passive.",
            "At night, Night Stalker's Health Regen is <b>increased by 40%</b>, but during the day it is <b>decreased by 20%</b>.",
        ],
    ),
    new=dict(
        name="Hunter in the Night",
        slug="night_stalker_hunter_in_the_night",
        innate=True,
        desc=[
            "Innate. Promoted from a regular passive. Activates only at night.",
            "Move Speed bonus rescaled from <b>22/28/34/40%</b> (per ability rank) to <b>24% + 2% per 3 hero levels</b>.",
            "Attack Speed bonus rescaled from <b>20/40/60/80</b> to <b>38 + 2 per hero level</b>.",
            aghs_line("Increases bonus Movement Speed by 15% and bonus Attack Speed by 50. Killing an enemy hero resets cooldowns of all basic abilities."),
        ],
    ),
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
            "Innate. Passive.",
            "Nyx Assassin can <b>sense invisible heroes</b> in a <b>400 radius</b> around himself.",
        ],
    ),
    new=dict(
        name="Mana Burn",
        slug="nyx_assassin_jolt",
        innate=True,
        desc=[
            "Innate. Passive.",
            "When Nyx Assassin deals damage with attacks or his abilities, he burns the affected unit's mana equal to <b>12% of damage dealt</b>.",
            "Damage reflected with Spiked Carapace also counts.",
        ],
    ),
))
W(ability("Mind Flare"))
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
W(ability("Repel"))
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
            "Innate. Passive, can't be leveled up.",
            "Outworld Destroyer gains <b>2 extra mana per point of Intelligence</b>.",
        ],
    ),
    new=dict(
        name="Essence Flux",
        slug="obsidian_destroyer_equilibrium",
        innate=True,
        desc=[
            "Innate. Passive (promoted from a regular ability). Max Mana Restore now depends on the ability it procced on:",
            "<b>Regular abilities:</b> Max Mana Restoration is <b>40% + 5% per 5 levels</b>.",
            "<b>Attack modifiers that spend mana:</b> Max Mana Restoration is <b>25% + 5% per 5 levels</b>.",
        ],
    ),
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
W(ability("Rolling Thunder"))
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
            "Innate. Passive, can't be leveled up.",
            "Debuffs from Icarus Dive, Fire Spirits, Sun Ray, and Supernova apply a stackable <b>2% miss chance per second</b>. Lasts <b>5 seconds</b>. Applying a new stack refreshes the duration.",
        ],
    ),
    new=dict(
        name="Dying Light",
        slug="phoenix_dying_light",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Phoenix deals <b>4% of its missing health</b> as magic damage to all enemies in a <b>400 radius</b> every second. Damage tick rate: 0.2s.",
            "The effect is also present <b>during Supernova</b> — damage is calculated as if Phoenix was still present with the same health and health regen it had at the moment of the cast.",
        ],
    ),
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
            "Innate. Passive.",
            "Due to his size, Primal Beast does 40% bonus damage to buildings.",
        ],
    ),
    new=dict(
        name="Colossal",
        slug="primal_beast_colossal",
        innate=True,
        desc=[
            "Innate. Passive, scales with Max Health.",
            "Has 10% base Slow Resistance.",
            "Gains +0.5% Area of Effect and +1% Slow Resistance per 100 Max Health.",
        ],
    ),
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
W(li("Health/Mana Restore rescaled from 10 + 2% to 3% ", t("REWORK")))
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
W(ability("Flesh Heap"))
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
W(ability("Backstab"))
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
W(ability("Dark Carnival Barker"))
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
W(ability("Escape Act"))
W(ul_open())
W(li("Radius and Aghanim's Scepter's Explosion Radius now affected by AoE bonuses", t("NEW")))
W(li("Targeted unit is no longer stunned for 0.5 seconds when placed in a box", t("DEL")))
W(ul_close())
W(ability("Impalement Arts"))
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
W(ul_close())
W(subnote("Damage at level 1 increased from 49–55 to 50–56"))
W(ability_change(
    old=dict(
        name="Might and Magus",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Grants self <b>1% base attack damage</b> bonus per Spell Amplification bonus.",
            "Grants self <b>0.5% Magic Resistance</b> bonus per Spell Amplification bonus.",
        ],
    ),
    new=dict(
        name="Curiosity",
        slug="rubick_curiosity",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Rubick gains <b>1 stack of Curiosity per level</b>. Each stack grants <b>+1 base damage</b>, <b>+0.3% Buff/Debuff Duration</b>, and <b>+2 Area of Effect</b> bonus.",
            "If Rubick <b>sees an enemy Hero cast an ability</b> within 1200 distance of him, he gains <b>2 Curiosity for 20s</b>.",
            "If an enemy that currently provides temporary Curiosity dies within 3s after taking damage from Rubick, he gains <b>1 Curiosity permanently</b>.",
        ],
    ),
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
W(ability("Caustic Finale"))
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
W(ability("Burrowstrike"))
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
W(ability("Shadowraze"))
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
            "Grants Shadow Fiend a self-buff for the duration: bonus Attack Speed and bonus Movement Speed (scales with ability rank).",
        ],
    ),
    new=dict(
        name="Feast of Souls",
        slug="nevermore_frenzy",
        desc=[
            "Active. No longer requires souls to cast.",
            "Instead, while active, Shadow Fiend gains souls from <b>2 enemies in a 600 radius every 0.5s</b>, prioritizing heroes. Each enemy can provide souls once — creeps give <b>1 soul</b>, heroes give <b>3</b>. Can collect souls from up to <b>4/6/8/10 enemies</b>.",
            "After the effect ends, Shadow Fiend loses souls whose owners are still alive, retaining the rest for <b>8s</b>.",
            inline_note("The enemy threshold limits only the amount of enemies affected, not the total souls collected. At the cap of 10, you can collect souls from 5 heroes and 5 creeps for 20 souls. 10 Dummy Targets in Hero Demo mode yield 30 souls."),
        ],
    ),
))
W(ul_open())
W(li("Bonus Attack Speed decreased from 40/55/70/85 to 35/50/65/80", b([40, 55, 70, 85], [35, 50, 65, 80])))
W(li("Bonus Move Speed decreased from 5/7/9/11% to 4/6/8/10%", b([5, 7, 9, 11], [4, 6, 8, 10])))
W(ul_close())
W(ability("Requiem of Souls"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}%",
)
W(ability_change(
    old=dict(
        name="Brain Drain",
        slug="silencer_brain_drain",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
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
            "Innate. Passive (reworked from the previous Brain Drain).",
            "Silencer takes less damage from and deals more damage to silenced targets. Damage modifier is " + _sil_pill + " for both reduction and amplification.",
            "If an enemy hero dies within <b>925 range</b> of Silencer or was debuffed by Silencer at the time of death, he <b>permanently steals 1 Intelligence</b>. If the victim was silenced, an <b>extra 1 Intelligence</b> is stolen.",
        ],
        tables=[_sil_table],
    ),
))
W(ability("Arcane Curse"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Ruin and Restoration",
        innate=True,
        desc=[
            "Innate. Passive, levels up with Mystic Flare.",
            "Passively provides Skywrath Mage with <b>20/30/40/50% Spell Lifesteal</b>.",
            "Has 80% penalty against creeps, similarly to other sources of Spell Lifesteal.",
        ],
    ),
    new=dict(
        name="Shield of the Scion",
        slug="skywrath_mage_shield_of_the_scion",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Whenever Skywrath Mage deals magical damage with his abilities to an enemy hero, he gains a magic damage barrier equal to " + _sw_pill + " for <b>12s</b>.",
            "Each instance stacks independently.",
        ],
        tables=[_sw_table],
    ),
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}%",
)
W(li("Flat 8/16/24/32 bonus damage replaced with " + _sdr_pill + " bonus attack damage",
     t("REWORK"), extra=_sdr_table))
W(ul_close())
W(ability("Guardian Sprint"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}",
)
_boomstick_max_pill, _boomstick_max_table = scale_pill(
    "50 + 5 per level",
    lambda L: 50.0 + 5.0 * L,
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}",
)
W(ability_change(
    old=dict(
        name="Buckshot",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Snapfire's attacks deal <b>25% more damage</b>, but they have a <b>25% chance</b> of a glancing shot that will deal <b>50% less damage</b>.",
        ],
    ),
    new=dict(
        name="Boomstick",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Snapfire deals more damage with her attacks and abilities, the closer she is to her target.",
            "<b>Min Damage Amp:</b> 0% at a distance of " + _boomstick_min_pill + ".",
            "<b>Max Damage Amp:</b> 35% at a distance of " + _boomstick_max_pill + ".",
        ],
        tables=[_boomstick_min_table, _boomstick_max_table],
    ),
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
    levels=[1, 5, 10, 15, 20, 25, 30],
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
            "Innate. Passive.",
            "Provides the hero on Spirit Breaker's team with the <b>least Experience points</b> a buff that increases their Experience gain by <b>50%</b> until they reach the level of the second-least.",
        ],
    ),
    new=dict(
        name="Empowering Haste",
        slug="spirit_breaker_empowering_haste",
        innate=True,
        desc=[
            "Innate. Passive (promoted from regular ability).",
            "Spirit Breaker gains bonus Movement Speed whenever he stuns an enemy. Effect depends on unit type: <b>stunning a hero</b> gives <b>+8% for 2s</b>; <b>other units</b> give <b>+2% for 1s</b>.",
            "Multiple stuns stack with <b>independent durations</b>. Bull Rush duration is paused during Charge of Darkness, but it can still gain new stacks.",
            "Bonus allows Spirit Breaker to go <b>over the max movement speed limit</b>.",
        ],
    ),
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
W(ul_close())
W(subnote("Damage at level 1 increased from 60–62 to 61–63"))
_sv_pill, _sv_table = scale_pill(
    "0.08 + 0.02 per level",
    lambda L: 0.08 + 0.02 * L,
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.2f}",
)
W(ability_change(
    old=dict(
        name="Vanquisher",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Sven's attacks deal <b>15% more damage</b> to <b>stunned enemies</b>.",
            "Worked off Sven's base attack damage; talent line scaled the bonus.",
        ],
    ),
    new=dict(
        name="Wrath of God",
        slug="sven_wrath_of_god",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Increases the attack damage Sven gains per point of Strength by " + _sv_pill + ".",
            "<b>Disabled by Break.</b>",
        ],
        tables=[_sv_table],
    ),
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.2f}%",
)
W(ability_change(
    old=dict(
        name="Minefield Sign",
        slug="techies_minefield_sign",
        innate=True,
        desc=[
            "Innate. Active, can't be leveled up.",
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
            "Innate. Passive.",
            "Increases mana regen by a portion of Techies' max mana equal to " + _tch_pill + ".",
            "When Techies die, they leave behind a barrel that explodes after <b>1.5s</b>, dealing magical damage equal to <b>50 + 30% of their max mana</b> to enemies in a <b>400 AoE</b>. The barrel provides 400 obstructed vision until it explodes.",
            aghs_shard_line("Increases mana-to-damage by 10%. Adds an active component — Techies plant the M.A.D. barrel and detonate it later via a sub-ability. The barrel is invisible and can be destroyed before detonation begins. Detonating makes it visible and immortal, then it explodes after the same 1.5s delay. Only one M.A.D. can exist via the active cast at a time. Barrel Health: 200. Cast Range: 450. No Mana Cost. Cooldown: 30s. Cast Point: 1s."),
        ],
        tables=[_tch_table],
    ),
))
W(ability("Reactive Tazer"))
W(ul_open())
W(li("Can now always be cast on allies", t("NEW")))
W(li("Cast Range increased from 500 to 600", b(500, 600)))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())
W(ability("Blast Off!"))
W(ul_open())
W(li("Now deals its self damage before damaging enemies", t("MISC")))
W(li("Techies are now rooted and disarmed instead of self-stunned during Blast Off's leap animation", t("MISC")))
W(ul_close())
W(ability("Proximity Mines"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.2f}s",
)
_ta_hp_pill, _ta_hp_table = scale_pill(
    "2.7 + 0.3 per level",
    lambda L: 2.7 + 0.3 * L,
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}",
)
_ta_mp_pill, _ta_mp_table = scale_pill(
    "2.2 + 0.2 per level",
    lambda L: 2.2 + 0.2 * L,
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}",
)
W(ability_change(
    old=dict(
        name="Third Eye",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Templar Assassin and her teammates can see <b>Roshan's respawn timer</b>. The indicator is displayed above the Scan ability.",
        ],
    ),
    new=dict(
        name="Inner Peace",
        slug="templar_assassin_inner_peace",
        innate=True,
        desc=[
            "Innate. Passive, improves with Templar Assassin's level.",
            "After remaining stationary for 0.25s, Templar Assassin begins meditating, gaining bonus health regen and mana regen. Bonuses linearly ramp from 0 up to their maximum, reached after " + _ta_ramp_pill + ".",
            "Moving from the current position or taking damage from an enemy <b>resets</b> the regen bonuses.",
            "<b>Max Health Regen:</b> " + _ta_hp_pill + ".  <b>Max Mana Regen:</b> " + _ta_mp_pill + ".",
        ],
        tables=[_ta_ramp_table, _ta_hp_table, _ta_mp_table],
    ),
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
            "Innate. Passive.",
            "Tidehunter removes negative status effects (<b>Strong Dispel</b>) if he takes more than <b>500 damage</b> from player-controlled sources. Damage counter resets after <b>7s</b>.",
        ],
    ),
    new=dict(
        name="Leviathan's Catch",
        slug="tidehunter_leviathans_catch",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Whenever an enemy hero dies while affected by any of Tidehunter's debuffs or is killed by him, they <b>drop a fish</b>.",
            "Tidehunter can eat the fish to grow in size and <b>permanently gain +3 Max Health, +2 Attack Range, and +1 Bonus Damage Block</b>. Tidehunter also <b>automatically eats a fish on every level-up</b>.",
            inline_note(
                "The fish flies 400 units towards Tidehunter upon spawning, stays in the world indefinitely and can be destroyed by an attack from Tidehunter's enemies.<br>"
                "Bonus Damage Block is only applied if there is a source of damage block being applied to an incoming physical attack."
            ),
        ],
    ),
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
            "<b>Cast:</b> Cast Range 600. Mana Cost 100/120/140/160. Cooldown 24/22/20/18s. Cast Point 0.1s.",
            inline_note(
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
W(ability("Warp Flare"))
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
            "Innate. Passive.",
            "Enemies that attack Tiny get a stacking debuff that decreases their attack damage by <b>2/3/4/5%</b> per stack (levels with Grow). <b>Max Stacks:</b> 10. <b>Debuff Duration:</b> 5s (refreshes on each stack).",
        ],
    ),
    new=dict(
        name="Insurmountable",
        slug="tiny_insurmountable",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Slow Resistance now also applies to <b>Attack Speed Slows</b>.",
            "Tiny gains <b>Slow Resistance equal to 20% of his Strength</b> and <b>Status Resistance equal to 10% of his Strength</b>.",
        ],
    ),
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
W(ability("Tree Throw"))
W(ul_open())
W(li("No longer applies a slow on the tossed tree by default", t("DEL")))
W(ul_close())
W(ability("Grow"))
W(ul_open())
W(li("Aghanim's Shard: Thrown trees and tossed units deal 20% more damage in their AoE, have +125 radius, and apply a 25% movement slow and a 45 attack speed slow to all units in the AoE of Toss, Tree Throw, and Tree Volley for 2.5s. Damage is not increased for the Tossed unit itself", t("NEW")))
W(ul_close())
W(ability("Tree Volley"))
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
W(ability("Battle Stance"))
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
W(ability("Invading Force"))
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
W(ability("Vengeance Aura"))
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.0f}",
)
_ven_dur_pill, _ven_dur_table = scale_pill(
    "4.5s + 0.5s per level",
    lambda L: 4.5 + 0.5 * L,
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.1f}s",
)
W(ability_change(
    old=dict(
        name="Septic Shock",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Venomancer's attacks deal extra magical damage based on how many debuffs the target has (only counts debuffs from Venomancer and his Plague Wards). <b>Base Damage per debuff:</b> 10%.",
            aghs_line("Increases damage per debuff from 10% to 20%. Plague Wards also deal Septic Shock damage based on their attack damage."),
        ],
    ),
    new=dict(
        name="Poison Sting",
        slug="venomancer_poison_sting",
        innate=True,
        desc=[
            "Innate. Passive (promoted from a regular ability).",
            "Imbues Venomancer's attacks with poison: <b>" + _ven_dps_pill + "</b> damage per second and a flat <b>10% movement slow</b>.",
            "<b>Duration:</b> " + _ven_dur_pill + ".",
        ],
        tables=[_ven_dps_table, _ven_dur_table],
    ),
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
            "Now when the plague spreads, it also carries all debuffs placed by Venomancer. Now spreads a second time, but all spreads after the first one deal no initial damage.",
            inline_note("Doesn't stack. Applying plague to an already plague-infected unit will deal projectile damage again, but won't affect the remaining debuff duration. Duration of carried debuffs is fixed and cannot be altered with Status Resistance or Debuff Amplification."),
            "<b>Duration:</b> 4s. <b>Initial Damage:</b> 150/200/250. <b>Max HP as Damage:</b> 2/3/4%. <b>Spread Radius:</b> 700. <b>Cooldown:</b> 100/90/80s. <b>Mana Cost:</b> 200/250/300.",
            aghs_line("Decreases cooldown by 35s. Reduces Magic Resistance of affected units by 20% and allows additional spreads to deal initial damage."),
        ],
    ),
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
    levels=[1, 5, 10, 15, 20, 25, 30],
    value_fmt="{:.2f}s",
)
W(ability_change(
    old=dict(
        name="Lurker",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Visage's ability cooldowns are <b>reduced as long as he's not taking damage</b>. Gains a stack every 2s without damage taken. Each stack grants <b>2% cooldown speed</b> (max 10 stacks). Stacks fade after 2s upon taking any damage.",
        ],
    ),
    new=dict(
        name="Silent as the Grave",
        slug="visage_silent_as_the_grave",
        innate=True,
        desc=[
            "Innate. Active (promoted from the Aghanim's Scepter ability).",
            "Visage gains <b>flying movement and +12% movement speed for 20s</b>. Upon attacking or casting, he loses both effects, but he and his familiars gain <b>+10% attack damage for 2s</b>.",
            "<b>Mana Cost:</b> 50.  <b>Cooldown:</b> " + _visage_satg_pill + ".",
            aghs_line("Increases bonus movement speed by +12%, bonus damage by +10%, bonus damage duration by +2s, and flight duration by +10s. While flight is active, Silent as the Grave grants <b>invisibility</b> to Visage and his familiars. Invisibility for Visage and each familiar are not connected."),
        ],
        tables=[_visage_satg_table],
    ),
))
W(ul_open())
W(li("Mana Cost decreased from 115 to 50", b(115, 50, l=True)))
W(li("Cooldown changed from 45s to 45.75s − 0.75s per level", t("BUFF")))
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
W(li("Base Damage decreased by 4", bstat_h("Void Spirit", "AttackDamageMin", "7.40c", -4), extra=note_box(hero="Void Spirit", field="AttackDamageMin", before_patch="7.40c")))
W(ul_close())
W(subnote("Damage at level 1 unchanged due to innate ability changes"))
W(ability("Intrinsic Edge"))
W(ul_open())
W(li("Now also increases Void Spirit's attack damage per point of attribute by 15%", t("REWORK")))
W(li("Increase is multiplicative, so it's increased from 0.45 to 0.5175", b(0.45, 0.5175)))
W(li("The result of these changes:", t("MISC")))
W(li("Damage at level 1 is unchanged at 52–56", t("MISC")))
W(li("Damage gain per level increased from 3.6 to 4.1", b(3.6, 4.1)))
W(li("Damage at level 30 increased from 174–178 to 192–196", t("BUFF")))
W(li("Secondary bonuses increased from 25% to 30%", b(25, 30)))
W(li("No longer provides increased Armor or Magic Resistance", t("DEL")))
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
W(li("Minor Imp attack damage rescaled from 10-11/14-15/18-19/22-23/26-27 to 20-21", t("REWORK")))
W(li("Aghanim's Shard now increases health of minor imps by 80 and explosion damage by 45 ", t("REWORK")))
W(ul_close())
W(subnote("Same values as before, but explicitly stated now"))

# Weaver
W(hero_header("Weaver"))
W(ability_change(
    old=dict(
        name="Rewoven",
        innate=True,
        desc=[
            "Innate. Passive, can't be leveled up.",
            "Every time Weaver casts an ability, he gains <b>+50 attack range</b> for <b>7s</b>. Effect stacks independently per cast.",
        ],
    ),
    new=dict(
        name="Threads of Fate",
        innate=True,
        desc=[
            "Innate. Passive.",
            "After dealing damage to an enemy hero with an attack or ability, if Weaver remains within <b>700 range</b> of them for <b>1.5s</b>, he establishes a <b>Thread of Fate</b> that briefly slows the enemy's movement and ties them to Weaver.",
            "Each established thread grants <b>+10% bonus damage</b> to Weaver. Threads last up to <b>6s</b> and break if the distance becomes longer than <b>900</b>.",
            "If the enemy dies with a Thread of Fate established, the thread's bonuses linger for an additional <b>5s</b>.",
        ],
    ),
))
W(subnote("Effects linger even if the enemy dies just as the thread is about to be established. Movement slow is 100% for 0.2s."))
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
            "Innate. Passive.",
            "Windranger's movement speed <b>cannot drop below 240</b>. Max Movement Speed cap increased from 550 to <b>600</b>.",
        ],
    ),
    new=dict(
        name="Tailwind",
        slug="windrunner_tailwind",
        innate=True,
        desc=[
            "Innate. Passive.",
            "Using an ability conjures a stacking <b>Tailwind</b> that gives Windranger a brief burst of movement speed. The bonus starts gradually fading halfway through the duration.",
            "<b>Movement Speed Bonus per stack:</b> 35%.  <b>Duration:</b> 2s.",
            "Passively increases Windranger's <b>max movement speed cap to 600</b>.",
            aghs_line("Attacks also grant Tailwind effect. Increases Tailwind duration to 3s and makes it undispellable."),
        ],
    ),
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
            "Innate. Passive.",
            "When an allied hero picks up a <b>Wisdom Rune</b>, the 3 heroes that wouldn't benefit from it gain <b>20% of the experience</b> instead.",
        ],
    ),
    new=dict(
        name="Eldwurm's Edda",
        slug="winter_wyvern_eldwurms_edda",
        innate=True,
        desc=[
            "Innate. Item-based.",
            "Winter Wyvern starts the game with the <b>Eldwurm's Edda</b> item. After <b>10 minutes</b> it can be consumed, increasing the <b>current and maximum level of one basic ability by 1</b>.",
            "Also increases Winter Wyvern's <b>Intelligence by 25%</b> of its base value at the time of consumption.",
            "<b>Level-5 values</b> are automatically calculated by applying 50% of the difference in all values between levels 3 and 4 (except mana cost — kept the same as level 4).",
        ],
    ),
))
W(ability("Arctic Burn"))
W(ul_open())
W(li("No longer has a one debuff per cast restriction on enemy heroes", t("DEL")))
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
W(li("Now spawns 2/3/4 per enemy hero within slow radius", t("REWORK")))
W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
W(ul_close())

# Zeus
W(hero_header("Zeus"))
W(ul_open())
W(li("Base Strength increased from 19 to 21", b(19, 21)))
W(li("Base Damage increased by 1–3 ", bstat_h("Zeus", "AttackDamageMin", "7.40c", 1), extra=note_box(hero="Zeus", field="AttackDamageMin", before_patch="7.40c")))
W(li("Damage spread increased from 8 to 10", b(8, 10)))
W(li("Damage at level 1 increased from 52–60 to 53–63", t("BUFF")))
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
W(li("Now applies the True Sight before the damage and strikes even untargetable and still invisible enemies ", t("REWORK")))
W(ul_close())
W(subnote("It used to simply reveal invisible heroes without dealing damage to them. Now it will work similarly to Lightning Bolt, dealing damage even to units affected by Smoke of Deceit, Dark Willow's Shadow Realm, Phantom Assassin's Blur, Slark's Shadow Dance or Depth Shroud, etc."))
W(ul_open())
W(li("Vision and True Sight radius increased from 500 to 600", b(500, 600)))
W(ul_close())
W(ability("Nimbus"))
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
W(ability("Morph"))
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

# Write ability-icon URL list for the validator (check_icons.py)
import json as _json_dump
with open('_ability_icons.txt', 'w', encoding='utf-8') as _f:
    for _u in sorted(_State.ability_icons):
        _f.write(_u + '\n')
print(f"  → _ability_icons.txt: {len(_State.ability_icons)} unique URLs")
