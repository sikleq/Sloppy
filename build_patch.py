#!/usr/bin/env python3
"""Generate annotated Dota 2 7.41c patch notes HTML."""

# ---------- IMAGE URL HELPERS ----------

HERO_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/"
ITEM_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/"
ABIL_CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/"

HERO_SLUG = {
    "Abaddon": "abaddon", "Alchemist": "alchemist",
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


def bf(old_fn, new_fn, formula_text, levels=None, l=False, value_fmt="{:g}"):
    """Formula-based change. Returns (trigger_html, badge_html, table_html).
    The trigger wraps formula_text as a clickable pill that toggles the table.
    Tag is determined by LEVEL 1 (per user spec).
    levels: list of int levels to show; defaults to L1-15 + L20, L25, L30.
            Can also pass an int N → range(1, N+1).
    value_fmt: format string for level values (e.g. '{:.2f}%' or '{:g}')."""
    if levels is None:
        levels = list(range(1, 16)) + [20, 25, 30]
    elif isinstance(levels, int):
        levels = list(range(1, levels + 1))

    _formula_id_counter[0] += 1
    fid = f"f{_formula_id_counter[0]}"

    # Level 1 inline badge
    cls1, disp1, _, overall1 = _compute_pct(old_fn(1), new_fn(1), l)
    overall_attr = f' data-overall="{overall1}"' if overall1 else ""
    badge = f'<span class="badge-group"{overall_attr}><span class="badge {cls1}">{disp1}</span></span>'

    # Trigger
    trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'

    # Mark boundary class on first level >= 20 (visual jump from L15 → L20)
    def cls_for(L):
        return ' class="lvl-jump"' if L == 20 else ''

    head_cells = "".join(f'<th{cls_for(L)}>L{L}</th>' for L in levels)
    old_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(old_fn(L))}</td>' for L in levels)
    new_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(new_fn(L))}</td>' for L in levels)
    pct_cells = []
    for L in levels:
        cls, disp, _, _ = _compute_pct(old_fn(L), new_fn(L), l)
        pct_cells.append(f'<td{cls_for(L)}><span class="badge {cls}">{disp}</span></td>')

    table = (
        f'<table class="formula-table" id="{fid}" hidden>'
        f'<thead><tr><th></th>{head_cells}</tr></thead>'
        f'<tbody>'
        f'<tr><th class="row-label-old">old</th>{old_cells}</tr>'
        f'<tr><th class="row-label-new">new</th>{new_cells}</tr>'
        f'<tr><th>Δ %</th>{"".join(pct_cells)}</tr>'
        f'</tbody>'
        f'</table>'
    )

    return trigger, badge, table


def t(tag):
    """Text-only tag for non-numeric changes."""
    cls_map = {
        "BUFF":   ("buff-text", "buff"),
        "NERF":   ("nerf-text", "nerf"),
        "REWORK": ("rework",    "rework"),
        "MISC":   ("misc",      "misc"),
        "QoL":    ("qol",       "qol"),
    }
    color_cls, tag_id = cls_map[tag]
    return f'<span class="badge {color_cls}" data-tag="{tag_id}">{tag}</span>'


# ---------- HTML BUILDING ----------

class _State:
    block_open = False

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
    return _open_block() + f'''<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="{hero_img(name)}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def unit_header(name, icon_url):
    """Header for a separate summoned unit (e.g. Spirit Bear) with custom icon URL."""
    return _open_block() + f'''<div class="entity hero-entity">
  <div class="entity-icon ability-icon"><img src="{icon_url}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def item_header(name):
    return _open_block() + f'''<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="{item_img(name)}" alt="{name}" loading="lazy"></div>
  <div class="entity-name">{name}</div>
</div>'''


def plain_header(name):
    return _open_block() + f'<div class="entity plain-entity"><div class="entity-name">{name}</div></div>'


def section(title):
    return _close_block() + f'<h2 class="section">{title}</h2>'


def subgroup(title):
    return f'<h4 class="subgroup">{title}</h4>'


def ability(title):
    return f'<h4 class="ability-title">{title}</h4>'


def ul_open():
    return '<ul class="changes">'


def ul_close():
    return '</ul>'


import re

def li(text, badge="", extra="", force_tag=None):
    """Generate <li>. Auto-extracts data-tag from badges for filtering.
    Priority: force_tag > data-overall > data-tag (text tags) > buff*/nerf* class scan.
    extra: optional HTML appended inside the li (e.g. correction note)."""
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
    attr = f' data-tag="{tag_str}"' if tag_str else ""
    return f'<li{attr}>{text} {badge}{extra}</li>'


def subnote(text):
    return f'<ul class="subnotes"><li>{text}</li></ul>'


def li_formula(prefix, old_formula, new_formula, old_fn, new_fn, l=False):
    """Convenience: emit <li> with formula table.

    prefix:        text BEFORE 'from' (e.g. 'Max Damage Increase decreased')
    old_formula:   human-readable old-formula string
    new_formula:   human-readable new-formula string
    old_fn/new_fn: callable(level) → value, used to compute per-level table
    l:             lower-is-buff flag (passed through to bf gradient)
    """
    trigger, badge, table = bf(old_fn, new_fn, new_formula, l=l)
    full_text = (f'{prefix} from <span class="formula-old">{old_formula}</span> '
                 f'to {trigger}')
    full_badge = ('<span class="badge rework" data-tag="rework">REWORK</span>'
                  + badge)
    return li(full_text, full_badge, extra=table)


# ---------- CSS ----------

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

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

.nav-back-btn {
  padding: 6px 12px;
  margin-right: 6px;
  color: #c9d1d9;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.18);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.4);
  transition: background 0.15s;
}
.nav-back-btn:hover {
  background: rgba(0, 0, 0, 0.32);
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
  padding: 10px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}
.nav-tabs {
  display: flex;
  gap: 2px;
}
.nav-tab {
  padding: 8px 16px;
  color: #c9d1d9;
  border-radius: 6px;
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  background: transparent;
  border: none;
  font-family: inherit;
  transition: background 0.15s, box-shadow 0.15s;
  display: inline-flex;
  align-items: center;
}
.nav-tab:hover {
  background: rgba(48, 54, 61, 0.5);
}
.nav-tab.active {
  background: rgba(0, 0, 0, 0.28);
  font-weight: 600;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
}
.nav-context {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nav-context .release-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
  background: rgba(0, 0, 0, 0.28);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  padding: 4px 11px;
  border-radius: 6px;
}
.nav-context .release-date {
  color: #c9d1d9;
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.3px;
}
.nav-context .patch-age {
  color: #a8b3bd;
  font-size: 10.5px;
  font-weight: 400;
  letter-spacing: 0.15px;
  font-variant-numeric: tabular-nums;
}
.nav-context .version {
  color: #c9d1d9;
  font-size: 18px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.5px;
  background: rgba(0, 0, 0, 0.28);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  border: 1px solid transparent;
  padding: 5px 12px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-family: inherit;
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

/* LEGEND */
/* CALENDAR PAGE */
.calendar { margin: 24px 0; }
.cal-toggle-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
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
.cal-year-label::before {
  content: '▾';
  color: #6e7681;
  font-size: 11px;
  display: inline-block;
  width: 10px;
  transition: transform 0.15s;
}
.cal-year-block[data-collapsed="true"] .cal-year-label::before {
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
  transition: filter 0.15s, transform 0.1s;
  border: 1px solid transparent;
}
.cal-patch:hover {
  filter: brightness(1.35);
  transform: scale(1.08);
}
.cal-patch .cal-version {
  font-size: 9.5px;
  font-weight: 500;
  color: #b8b8b8;
  line-height: 1.1;
  margin-bottom: 2px;
  white-space: nowrap;
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
.cal-patch.major {
  background: rgba(212, 138, 78, 0.22);
  border-color: rgba(212, 138, 78, 0.32);
}
.cal-patch.major-big {
  background: rgba(212, 138, 78, 0.55);
  border-color: rgba(212, 138, 78, 0.75);
}
.cal-patch.major-big .cal-day { color: #fff; }
.cal-patch.major-big .cal-version { color: #f0e0c8; }
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
.cal-full-day-header {
  font-size: 9px;
  color: #6e7681;
  text-align: center;
  padding: 2px 0;
  font-weight: 500;
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
.cal-full-day.has-patch.major {
  background: rgba(212, 138, 78, 0.45);
  color: #fff;
}
.cal-full-day.has-patch.major-big {
  background: rgba(212, 138, 78, 0.85);
  color: #fff;
  box-shadow: 0 0 0 1px rgba(212, 138, 78, 0.5);
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
  margin: 18px 0 24px;
  padding: 8px 14px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 6px;
  font-size: 13px;
  color: #8b949e;
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
  font-size: 15px;
  font-weight: 600;
  margin: 12px 0 4px 14px;
}

/* CHANGES LIST */
ul.changes {
  list-style: none;
  margin: 4px 0 4px 30px;
}
ul.changes li {
  padding: 2px 0;
  color: #c9d1d9;
}
ul.subnotes {
  list-style: none;
  margin: -2px 0 6px 50px;
}
ul.subnotes li {
  color: #8b949e;
  font-size: 13.5px;
  padding: 2px 0;
}
ul.subnotes li::before { content: "↳ "; color: #6e7681; }

/* BADGES */
.badge-group {
  display: inline-flex;
  gap: 3px;
  margin-left: 6px;
  flex-wrap: wrap;
  vertical-align: middle;
}
.badge {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.3px;
  vertical-align: middle;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  margin-left: 4px;
}
.badge-group .badge { margin-left: 0; }

/* NEUTRAL & TEXT TAGS */
.badge.neutral {
  background: rgba(139, 148, 158, 0.12);
  color: #8b949e;
  border: 1px solid rgba(139, 148, 158, 0.3);
}
.badge.rework {
  background: rgba(180, 145, 220, 0.07);
  color: #9988aa;
  border: 1px solid rgba(180, 145, 220, 0.22);
}
.badge.misc {
  background: rgba(139, 148, 158, 0.10);
  color: #8b949e;
  border: 1px solid rgba(139, 148, 158, 0.28);
}
.badge.qol {
  background: rgba(121, 192, 255, 0.10);
  color: #a8c0d8;
  border: 1px solid rgba(121, 192, 255, 0.32);
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
.badge.buff10 { background: rgba(45, 185, 75, 0.50);   color: #7ec862; border: 1px solid rgba(45, 185, 75, 0.78); }

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
.badge.nerf10 { background: rgba(225, 50, 35, 0.46);   color: #e0745c; border: 1px solid rgba(225, 50, 35, 0.80); }

/* Make digits readable on saturated backgrounds */
.badge.buff1, .badge.buff2, .badge.buff3, .badge.buff4, .badge.buff5,
.badge.buff6, .badge.buff7, .badge.buff8, .badge.buff9, .badge.buff10,
.badge.nerf1, .badge.nerf2, .badge.nerf3, .badge.nerf4, .badge.nerf5,
.badge.nerf6, .badge.nerf7, .badge.nerf8, .badge.nerf9, .badge.nerf10 {
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55);
}

/* Text-tag versions of BUFF/NERF (used by t() for non-numeric changes; pick mid tier) */
.badge.buff-text { background: rgba(85, 205, 115, 0.22); color: #74bd80; border: 1px solid rgba(85, 205, 115, 0.50); }
.badge.nerf-text { background: rgba(225, 90, 75, 0.22);  color: #b87468; border: 1px solid rgba(225, 90, 75, 0.50); }

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

/* WRONG-WORD HIGHLIGHT — subtle, just to mark it (no italic, gray) */
.wrong-word {
  background: rgba(139, 148, 158, 0.08);
  color: #8b949e;
  padding: 0 5px;
  border-radius: 3px;
  text-decoration: line-through;
  text-decoration-color: rgba(139, 148, 158, 0.45);
  text-decoration-thickness: 1px;
}

/* FORMULA TRIGGER (clickable pill on the formula text itself) */
.formula-trigger {
  display: inline-block;
  padding: 0 8px;
  border-radius: 10px;
  background: rgba(200, 130, 60, 0.07);
  color: #d4a070;
  border: 1px solid rgba(200, 130, 60, 0.22);
  font-size: 13.5px;
  cursor: pointer;
  text-decoration: underline dotted rgba(212, 160, 112, 0.55);
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
  transition: all 0.14s;
  font-variant-numeric: tabular-nums;
  user-select: none;
}
.formula-trigger:hover {
  background: rgba(200, 130, 60, 0.14);
  border-color: rgba(200, 130, 60, 0.42);
  color: #e0b080;
}
.formula-trigger.active {
  background: rgba(200, 130, 60, 0.20);
  border-color: rgba(200, 130, 60, 0.55);
  color: #ecbe8a;
}
/* OLD FORMULA — just a subtle dotted underline so it stands out as "the old one" */
.formula-old {
  text-decoration: underline dotted rgba(139, 148, 158, 0.45);
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
}

/* FORMULA COMPARISON TABLE */
.formula-table {
  margin: 10px 0 6px 4px;
  border-collapse: separate;
  border-spacing: 2px;
  font-size: 11px;
  width: 100%;
  max-width: 1020px;
  table-layout: fixed;
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
  padding: 1px 4px;
  font-size: 10.5px;
  border-radius: 8px;
  display: inline-block;
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
    {"version": "7.41c", "date": "06.05.2026", "filename": "7.41c.html"},
    {"version": "7.41b", "date": "07.04.2026", "filename": "7.41b.html"},
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


def _dropdown_options_html(current_version):
    """Render menu items list for the version dropdown."""
    items = []
    for p in PATCHES:
        cls = "version-item current" if p["version"] == current_version else "version-item"
        href = "#" if p["version"] == current_version else p["filename"]
        items.append(
            f'<a class="{cls}" href="{href}">'
            f'<span class="vi-name">{p["version"]}</span>'
            f'<span class="vi-date">{p["date"]}</span>'
            f'</a>'
        )
    return "".join(items)


def _render_top_nav(active="changelogs", current_version=None, date=None):
    """Render the top nav. active in ('changelogs', 'calendar').
    If current_version is set, adds the right-side context (date + version dropdown)."""
    latest = PATCHES[0]['filename'] if PATCHES else "#"
    cls_changelogs = "active" if active == "changelogs" else ""
    cls_calendar  = "active" if active == "calendar" else ""

    if current_version is not None and date is not None:
        options = _dropdown_options_html(current_version)
        age_line = _patch_age_line(current_version)
        age_html = f'<span class="patch-age">{age_line}</span>' if age_line else ''
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
    <a class="nav-back-btn" href="calendar.html" style="display:none;">← Calendar</a>
    <div class="nav-tabs">
      <a class="nav-tab {cls_changelogs}" href="{latest}">Changelogs</a>
      <a class="nav-tab {cls_calendar}" href="calendar.html">Calendar</a>
    </div>{right_side}
  </div>
</nav>
'''


def write_head(version, date):
    """Render head + top nav (Changelogs+Calendar tabs + version) + container + toolbar."""
    nav = _render_top_nav(active="changelogs", current_version=version, date=date)
    W(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Dota Patch Notes - {version}</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>

{nav}
<div class="container">

<div class="toolbar">
  <div class="legend-tags">
    <strong>Tags:</strong>
    <button class="badge buff-text filter-btn" data-filter="buff">BUFF</button>
    <button class="badge nerf-text filter-btn" data-filter="nerf">NERF</button>
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


JS_TEXT = '''(function() {
  // ---- BACK-FROM-CALENDAR ----
  const params = new URLSearchParams(window.location.search);
  if (params.get('from') === 'calendar') {
    const back = document.querySelector('.nav-back-btn');
    if (back) back.style.display = 'inline-flex';
  }

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
    W('<script src="scripts.js"></script>')
    W('</div></body></html>')


def save_assets():
    """Write styles.css and scripts.js once. Called before any save_html()."""
    with open('/home/claude/styles.css', 'w', encoding='utf-8') as f:
        f.write(CSS)
    with open('/home/claude/scripts.js', 'w', encoding='utf-8') as f:
        f.write(JS_TEXT)
    print(f"  → styles.css: {len(CSS):,} bytes")
    print(f"  → scripts.js: {len(JS_TEXT):,} bytes")


def save_html(filename):
    """Write current accumulator to /home/claude/{filename} and reset state."""
    out = "\n".join(H)
    path = f"/home/claude/{filename}"
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
    years = sorted({p['year'] for p in patches}, reverse=True)
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    has_html = {p['version'] for p in PATCHES}
    expanded_years = set(years[:2])  # newest 2 expanded by default

    def patch_class(v):
        if _re.search(r'[a-z]$', v):
            return 'sub'
        return 'major-big' if PATCH_ENTRY_COUNTS.get(v, 0) >= 500 else 'major'

    def chip_tag(v):
        if v in has_html:
            return ('a', f' href="{v}.html?from=calendar"')
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
        body.append('<div class="cal-full-month-name"></div>')
        for d in range(1, 32):
            body.append(f'<div class="cal-full-day-header">{d}</div>')
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
                    body.append(f'<{tag} class="cal-full-day has-patch {cls}"{href}>{p["version"]}</{tag}>')
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
                body.append(
                    f'<{tag} class="cal-patch {cls}"{href}>'
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

    nav = _render_top_nav(active="calendar")
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
    with open('/home/claude/calendar.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → calendar.html: {len(html):,} bytes")


# ============================================================
# 7.41c content
# ============================================================
save_assets()
write_head("7.41c", "06.05.2026")

# 7.41c content is HANDCRAFTED — preserves manual corrections, formula tables,
# wrong-line/wrong-word annotations and subnotes that auto-gen can't produce.
HANDCRAFTED_7_41C_BODY = '''<h2 class="section">General Updates</h2>
<div class="entity-block">
<div class="entity plain-entity"><div class="entity-name">Mechanics</div></div>
<ul class="changes">
<li data-tag="nerf">Units with flying vision no longer ignore vision restrictions of Roshan's pits. They can no longer see into them from outside and vice versa <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
<ul class="subnotes"><li>Affects Clockwerk during Jetpack, Drow Ranger's Glacier, Monkey King during Tree Dance, Night Stalker during Dark Ascension, Treant Protector's Eyes in the Forest, and Visage's Familiars</li></ul>
</div>
<div class="entity-block">
<div class="entity plain-entity"><div class="entity-name">Tormentor</div></div>
<ul class="changes">
<li data-tag="buff">Alleviation: Max health regen increased from 2% to 2.25% <span class="badge-group" data-overall="buff"><span class="badge buff3">+12%</span></span></li>
<li data-tag="buff">Alleviation: Duration increased from 10s to 15s <span class="badge-group" data-overall="buff"><span class="badge buff8">+50%</span></span></li>
</ul>
</div>
<h2 class="section">Item Updates</h2>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/bloodstone.png" alt="Bloodstone" loading="lazy"></div>
  <div class="entity-name">Bloodstone</div>
</div>
<ul class="changes">
<li data-tag="nerf"><span class="wrong-line">Health bonus increased from +600 to +625 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span></span> <div class="correction-note"><span class="correction-label">Note</span>— This change is wrongly stated. The real change is 650 → 625 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span></span></div></li>
<li data-tag="nerf">Bloodpact cooldown increased from 30s to 35s <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-17%</span></span></li>
<li data-tag="nerf">Spell Weakness Aura damage from spells taken decreased from 12% to 10% <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-17%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/boots_of_bearing.png" alt="Boots of Bearing" loading="lazy"></div>
  <div class="entity-name">Boots of Bearing</div>
</div>
<ul class="changes">
<li data-tag="nerf">Swiftness Aura allied movement speed decreased from 20 to 15 <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/crellas_crozier.png" alt="Crella's Crozier" loading="lazy"></div>
  <div class="entity-name">Crella's Crozier</div>
</div>
<ul class="changes">
<li data-tag="buff">Rite of Rumusque movement speed steal increased from 5% to 6% <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/disperser.png" alt="Disperser" loading="lazy"></div>
  <div class="entity-name">Disperser</div>
</div>
<ul class="changes">
<li data-tag="nerf">Suppress duration decreased from 5s to 4s <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/essence_distiller.png" alt="Essence Distiller" loading="lazy"></div>
  <div class="entity-name">Essence Distiller</div>
</div>
<ul class="changes">
<li data-tag="buff">Soul Release radius when ground targeted increased from 400 to 450 <span class="badge-group" data-overall="buff"><span class="badge buff3">+12%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/harpoon.png" alt="Harpoon" loading="lazy"></div>
  <div class="entity-name">Harpoon</div>
</div>
<ul class="changes">
<li data-tag="nerf">Draw Forth can no longer move the Harpoon caster if they are rooted/leashed/bound <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
<ul class="subnotes"><li>Still affects rooted/leashed/bound targets</li></ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/heart.png" alt="Heart of Tarrasque" loading="lazy"></div>
  <div class="entity-name">Heart of Tarrasque</div>
</div>
<ul class="changes">
<li data-tag="nerf">Recipe cost increased from 600 to 700 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-17%</span></span></li>
<li data-tag="nerf">Total cost increased from 5100g to 5200g <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/mage_slayer.png" alt="Mage Slayer" loading="lazy"></div>
  <div class="entity-name">Mage Slayer</div>
</div>
<ul class="changes">
<li data-tag="nerf">Mage Slayer damage per second decreased from 40 to 35 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-12%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/silver_edge.png" alt="Silver Edge" loading="lazy"></div>
  <div class="entity-name">Silver Edge</div>
</div>
<ul class="changes">
<li data-tag="nerf">Shadow Walk bonus movement speed decreased from 25% to 22% <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-12%</span></span></li>
<li data-tag="nerf">Shadow Walk cooldown increased from 20s to 22s <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-10%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/shivas_guard.png" alt="Shiva's Guard" loading="lazy"></div>
  <div class="entity-name">Shiva's Guard</div>
</div>
<ul class="changes">
<li data-tag="nerf">Freezing Aura attack speed reduction decreased from 45 to 40 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-11%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/soul_ring.png" alt="Soul Ring" loading="lazy"></div>
  <div class="entity-name">Soul Ring</div>
</div>
<ul class="changes">
<li data-tag="nerf">Cooldown increased from 25s to 30s <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity item-entity">
  <div class="entity-icon item-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/specialists_array.png" alt="Specialist's Array" loading="lazy"></div>
  <div class="entity-name">Specialist's Array</div>
</div>
<ul class="changes">
<li data-tag="buff">Agility bonus increased from +12 to +15 <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<h2 class="section">Neutral Item Updates</h2>
<div class="entity-block">
<div class="entity plain-entity"><div class="entity-name">Crude</div></div>
<ul class="changes">
<li data-tag="nerf">Intelligence penalty increased from 6% to 9% <span class="badge-group" data-overall="nerf"><span class="badge nerf8">-50%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity plain-entity"><div class="entity-name">Greedy</div></div>
<ul class="changes">
<li data-tag="nerf">Mana bonus decreased from 200/250 to 150/200 <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span><span class="badge nerf4">-20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity plain-entity"><div class="entity-name">Tough</div></div>
<ul class="changes">
<li data-tag="nerf">Damage bonus decreased from +7/10/13/16 to +6/9/12/15 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-14%</span><span class="badge nerf2">-10%</span><span class="badge nerf2">-8%</span><span class="badge nerf2">-6%</span></span></li>
</ul>
</div>
<h2 class="section">Hero Updates</h2>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/abaddon.png" alt="Abaddon" loading="lazy"></div>
  <div class="entity-name">Abaddon</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Intelligence increased by 1 <span class="badge buff-text" data-tag="buff">BUFF</span></li>
<li>Damage at level 1 unchanged at 49-59 </li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 10 — Curse of Avernus DPS increased from +25 to +30 <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/alchemist.png" alt="Alchemist" loading="lazy"></div>
  <div class="entity-name">Alchemist</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Greevil's Greed</h4>
<ul class="changes">
<li data-tag="nerf">Bonus base/max Extra Gold per melted Scepter decreased from +6 to +3 <span class="badge-group" data-overall="nerf"><span class="badge nerf8">-50%</span></span></li>
</ul>
<h4 class="ability-title">Acid Spray</h4>
<ul class="changes">
<li data-tag="nerf">Cooldown rescaled from 22/21/20/19s to 21s <span class="badge-group" data-overall="nerf"><span class="badge buff1">+5%</span><span class="badge neutral">0%</span><span class="badge nerf1">-5%</span><span class="badge nerf3">-11%</span></span></li>
</ul>
<h4 class="ability-title">Chemical Rage</h4>
<ul class="changes">
<li data-tag="nerf">Bonus Health Regen decreased from 60/90/120 to 50/85/120 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-17%</span><span class="badge nerf2">-6%</span><span class="badge neutral">0%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/ancient_apparition.png" alt="Ancient Apparition" loading="lazy"></div>
  <div class="entity-name">Ancient Apparition</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Ice Blast</h4>
<ul class="changes">
<li data-tag="buff">Path Radius increased from 275 to 300 <span class="badge-group" data-overall="buff"><span class="badge buff2">+9%</span></span></li>
<li data-tag="buff">Base Area of Effect Radius increased from 275 to 300 <span class="badge-group" data-overall="buff"><span class="badge buff2">+9%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 20 — Chilling Touch Damage increased from +80 to +100 <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/antimage.png" alt="Anti-Mage" loading="lazy"></div>
  <div class="entity-name">Anti-Mage</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Persecutor</h4>
<ul class="changes">
<li data-tag="buff">Minimum mana threshold for slow improved from 50% to 60% <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/arc_warden.png" alt="Arc Warden" loading="lazy"></div>
  <div class="entity-name">Arc Warden</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Agility increased from 20 to 22 <span class="badge-group" data-overall="buff"><span class="badge buff2">+10%</span></span></li>
<li data-tag="buff">Damage at level 1 increased from 51-57 to 52-58 <span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/bane.png" alt="Bane" loading="lazy"></div>
  <div class="entity-name">Bane</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Brain Sap</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 120/130/140/150 to 105/120/135/150 <span class="badge-group" data-overall="buff"><span class="badge buff3">+12%</span><span class="badge buff2">+8%</span><span class="badge buff1">+4%</span><span class="badge neutral">0%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/batrider.png" alt="Batrider" loading="lazy"></div>
  <div class="entity-name">Batrider</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Movement Speed decreased from 320 to 310 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-3%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Sticky Napalm</h4>
<ul class="changes">
<li data-tag="nerf">Aghanim's Shard building damage decreased from 25% to 20% <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
<h4 class="ability-title">Firefly</h4>
<ul class="changes">
<li data-tag="nerf">Damage per second decreased from 25/50/75/100 to 20/40/60/80 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
<h4 class="ability-title">Flaming Lasso</h4>
<ul class="changes">
<li data-tag="nerf">Total Damage decreased from 200/350/500 to 125/250/375 <span class="badge-group" data-overall="nerf"><span class="badge nerf7">-38%</span><span class="badge nerf6">-29%</span><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/beastmaster.png" alt="Beastmaster" loading="lazy"></div>
  <div class="entity-name">Beastmaster</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Strength decreased from 25 to 24 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span></span></li>
<li data-tag="nerf">Damage at level 1 decreased from 50-54 to 49-53 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Wild Axes</h4>
<ul class="changes">
<li data-tag="nerf">Mana Cost increased from 50/55/60/65 to 65 <span class="badge-group" data-overall="nerf"><span class="badge nerf6">-30%</span><span class="badge nerf4">-18%</span><span class="badge nerf2">-8%</span><span class="badge neutral">0%</span></span></li>
</ul>
<h4 class="ability-title">Summon Razorback</h4>
<ul class="changes">
<li data-tag="nerf">Boar Attack Damage decreased from 30/45/60/75 to 24/41/58/75 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span><span class="badge nerf2">-9%</span><span class="badge nerf1">-3%</span><span class="badge neutral">0%</span></span></li>
</ul>
<h4 class="ability-title">Drums of Slom</h4>
<ul class="changes">
<li data-tag="nerf">Damage Radius decreased from 600 to 525 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-12%</span></span></li>
<li data-tag="nerf">Drum Hit Damage decreased from 80 to 70 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-12%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/bounty_hunter.png" alt="Bounty Hunter" loading="lazy"></div>
  <div class="entity-name">Bounty Hunter</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Shuriken Toss</h4>
<ul class="changes">
<li data-tag="nerf">Mana Cost increased from 75/80/85/90 to 75/85/95/105 <span class="badge-group" data-overall="nerf"><span class="badge neutral">0%</span><span class="badge nerf2">-6%</span><span class="badge nerf3">-12%</span><span class="badge nerf4">-17%</span></span></li>
</ul>
<h4 class="ability-title">Shadow Walk</h4>
<ul class="changes">
<li data-tag="buff">Bonus Speed increased from 8/12/16/20% to 11/14/17/20% <span class="badge-group" data-overall="buff"><span class="badge buff7">+38%</span><span class="badge buff4">+17%</span><span class="badge buff2">+6%</span><span class="badge neutral">0%</span></span></li>
</ul>
<h4 class="ability-title">Track</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 60 to 50 <span class="badge-group" data-overall="buff"><span class="badge buff4">+17%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/brewmaster.png" alt="Brewmaster" loading="lazy"></div>
  <div class="entity-name">Brewmaster</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Primal Split</h4>
<ul class="changes">
<li data-tag="qol">Cancel Split now has a 3s initial cooldown <span class="badge qol" data-tag="qol">QoL</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/bristleback.png" alt="Bristleback" loading="lazy"></div>
  <div class="entity-name">Bristleback</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Warpath</h4>
<ul class="changes">
<li data-tag="nerf">Damage per stack decreased from 15/20/25 to 12/16/20 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
<h4 class="ability-title">Hairball</h4>
<ul class="changes">
<li data-tag="nerf">Cooldown increased from 13s to 15s <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-15%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 25 — Bristleback Damage Threshold Reduction increased from 25 to 30 <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/broodmother.png" alt="Broodmother" loading="lazy"></div>
  <div class="entity-name">Broodmother</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Insatiable Hunger</h4>
<ul class="changes">
<li data-tag="buff">Spiderling Radius increased from 800 to 1200 <span class="badge-group" data-overall="buff"><span class="badge buff8">+50%</span></span></li>
</ul>
<h4 class="ability-title">Spinner's Snare</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 100 to 70 <span class="badge-group" data-overall="buff"><span class="badge buff6">+30%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/centaur.png" alt="Centaur Warrunner" loading="lazy"></div>
  <div class="entity-name">Centaur Warrunner</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Strength increased from 27 to 28 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span></li>
<li data-tag="buff">Damage at level 1 increased from 63-65 to 64-66 <span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span></li>
<li data-tag="buff">Strength gain increased from 4.2 to 4.3 <span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 25 — Hoof Stomp Duration increased from +0.8s to +1.0s <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/chaos_knight.png" alt="Chaos Knight" loading="lazy"></div>
  <div class="entity-name">Chaos Knight</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Chaos Strike</h4>
<ul class="changes">
<li data-tag="buff">Critical Max increased from 140/180/220/260% to 150/190/230/270% <span class="badge-group" data-overall="buff"><span class="badge buff2">+7%</span><span class="badge buff2">+6%</span><span class="badge buff1">+5%</span><span class="badge buff1">+4%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/dark_seer.png" alt="Dark Seer" loading="lazy"></div>
  <div class="entity-name">Dark Seer</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Intelligence increased from 22 to 23 <span class="badge-group" data-overall="buff"><span class="badge buff1">+5%</span></span></li>
<li data-tag="buff">Damage at level 1 increased from 53-59 to 54-60 <span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/dark_willow.png" alt="Dark Willow" loading="lazy"></div>
  <div class="entity-name">Dark Willow</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Terrorize</h4>
<ul class="changes">
<li data-tag="buff">Radius increased from 400/450/500 to 450/500/550 <span class="badge-group" data-overall="buff"><span class="badge buff3">+12%</span><span class="badge buff3">+11%</span><span class="badge buff2">+10%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/dawnbreaker.png" alt="Dawnbreaker" loading="lazy"></div>
  <div class="entity-name">Dawnbreaker</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Damage decreased by 1 <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
<li data-tag="nerf">Damage at level 1 decreased from 56-60 to 55-59 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Solar Guardian</h4>
<ul class="changes">
<li data-tag="nerf">Landing Stun Duration decreased from 1.4/1.6/1.8s to 1.2/1.4/1.6s <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-14%</span><span class="badge nerf3">-13%</span><span class="badge nerf3">-11%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/doom_bringer.png" alt="Doom" loading="lazy"></div>
  <div class="entity-name">Doom</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Scorched Earth</h4>
<ul class="changes">
<li data-tag="nerf">Bonus HP Regen decreased from 7/8/9/10 to 6.66 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-5%</span><span class="badge nerf4">-17%</span><span class="badge nerf6">-26%</span><span class="badge nerf6">-33%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/drow_ranger.png" alt="Drow Ranger" loading="lazy"></div>
  <div class="entity-name">Drow Ranger</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Frost Arrows</h4>
<ul class="changes">
<li data-tag="buff">Bonus Damage increased from 10/15/20/25 to 12/18/24/30 <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
</ul>
<h4 class="ability-title">Gust</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 70 to 55 <span class="badge-group" data-overall="buff"><span class="badge buff5">+21%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/earth_spirit.png" alt="Earth Spirit" loading="lazy"></div>
  <div class="entity-name">Earth Spirit</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Strength increased from 22 to 23 <span class="badge-group" data-overall="buff"><span class="badge buff1">+5%</span></span></li>
<li data-tag="buff">Damage at level 1 increased from 47-51 to 48-52 <span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/elder_titan.png" alt="Elder Titan" loading="lazy"></div>
  <div class="entity-name">Elder Titan</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Echo Stomp</h4>
<ul class="changes">
<li data-tag="buff">Damage increased from 60/100/140/180 to 65/110/155/200 <span class="badge-group" data-overall="buff"><span class="badge buff2">+8%</span><span class="badge buff2">+10%</span><span class="badge buff3">+11%</span><span class="badge buff3">+11%</span></span></li>
<li data-tag="nerf">Aghanim's Shard with alt-cast no longer swaps the position if Elder Titan is rooted <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/ember_spirit.png" alt="Ember Spirit" loading="lazy"></div>
  <div class="entity-name">Ember Spirit</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Strength decreased from 22 to 21 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-5%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/faceless_void.png" alt="Faceless Void" loading="lazy"></div>
  <div class="entity-name">Faceless Void</div>
</div>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="nerf">Level 20 — Time Walk Cooldown Reduction decreased from 1.25s to 1s <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
<li data-tag="nerf">Level 20 — Attack Speed during Chronosphere decreased from +100 to +80 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/gyrocopter.png" alt="Gyrocopter" loading="lazy"></div>
  <div class="entity-name">Gyrocopter</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Afterburner</h4>
<ul class="changes">
<li data-tag="buff">Duration increased from 4s to 5s <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/hoodwink.png" alt="Hoodwink" loading="lazy"></div>
  <div class="entity-name">Hoodwink</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Damage increased by 3 <span class="badge buff-text" data-tag="buff">BUFF</span></li>
<li data-tag="nerf">Base Agility decreased from 25 to 22 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-12%</span></span></li>
<li>Damage at level 1 unchanged at 47-54 </li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Sharpshooter</h4>
<ul class="changes">
<li data-tag="nerf">Knockback to Hoodwink won't be applied if Hoodwink is rooted <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/huskar.png" alt="Huskar" loading="lazy"></div>
  <div class="entity-name">Huskar</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Health Regen decreased by 0.25 <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/invoker.png" alt="Invoker" loading="lazy"></div>
  <div class="entity-name">Invoker</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Movement Speed decreased from 285 to 280 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/wisp.png" alt="Io" loading="lazy"></div>
  <div class="entity-name">Io</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Tether</h4>
<ul class="changes">
<li data-tag="nerf">HP/Mana Transfer decreased from 60/80/100/120% to 55/75/95/115% <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-8%</span><span class="badge nerf2">-6%</span><span class="badge nerf1">-5%</span><span class="badge nerf1">-4%</span></span></li>
</ul>
<h4 class="ability-title">Spirits</h4>
<ul class="changes">
<li data-tag="qol">Now remembers the radius of the spirits between casts <span class="badge qol" data-tag="qol">QoL</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/jakiro.png" alt="Jakiro" loading="lazy"></div>
  <div class="entity-name">Jakiro</div>
</div>
<ul class="changes">
<li data-tag="buff">Strength gain increased from 2.5 to 2.6 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Macropyre</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 250/350/450 to 225/325/425 <span class="badge-group" data-overall="buff"><span class="badge buff2">+10%</span><span class="badge buff2">+7%</span><span class="badge buff2">+6%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/juggernaut.png" alt="Juggernaut" loading="lazy"></div>
  <div class="entity-name">Juggernaut</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Blade Fury</h4>
<ul class="changes">
<li data-tag="buff">Damage per second increased from 80/110/140/170 to 85/115/145/175 <span class="badge-group" data-overall="buff"><span class="badge buff2">+6%</span><span class="badge buff1">+5%</span><span class="badge buff1">+4%</span><span class="badge buff1">+3%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/keeper_of_the_light.png" alt="Keeper of the Light" loading="lazy"></div>
  <div class="entity-name">Keeper of the Light</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Movement Speed decreased from 315 to 310 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/kunkka.png" alt="Kunkka" loading="lazy"></div>
  <div class="entity-name">Kunkka</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Admiral's Rum</h4>
<ul class="changes">
<li data-tag="buff">Cooldown decreased from 60.5s − 0.5s per level to 50.5s − 0.5s per level <span class="badge-group" data-overall="buff"><span class="badge buff4">+17%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/largo.png" alt="Largo" loading="lazy"></div>
  <div class="entity-name">Largo</div>
</div>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="rework">Level 20 — +200 Catchy Lick Damage replaced with 2× Catchy Lick Charges <span class="badge rework" data-tag="rework">REWORK</span></li>
<li data-tag="rework">Level 25 — 2× Catchy Lick Charges replaced with 2× Frogstomp Stomps / Interval <span class="badge rework" data-tag="rework">REWORK</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/lich.png" alt="Lich" loading="lazy"></div>
  <div class="entity-name">Lich</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Sinister Gaze</h4>
<ul class="changes">
<li data-tag="buff">Mana Drain per second increased from 20% to 25% <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/lina.png" alt="Lina" loading="lazy"></div>
  <div class="entity-name">Lina</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Light Strike Array</h4>
<ul class="changes">
<li data-tag="buff">Damage increased from 80/120/160/200 to 80/125/170/215 <span class="badge-group" data-overall="buff"><span class="badge neutral">0%</span><span class="badge buff1">+4%</span><span class="badge buff2">+6%</span><span class="badge buff2">+8%</span></span></li>
</ul>
<h4 class="ability-title">Laguna Blade</h4>
<ul class="changes">
<li data-tag="buff">Damage increased from 380/565/750 to 400/580/760 <span class="badge-group" data-overall="buff"><span class="badge buff1">+5%</span><span class="badge buff1">+3%</span><span class="badge buff1">+1%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/lone_druid.png" alt="Lone Druid" loading="lazy"></div>
  <div class="entity-name">Lone Druid</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Summon Spirit Bear</h4>
<ul class="changes">
<li data-tag="nerf">Mana Cost increased from 75 to 100 <span class="badge-group" data-overall="nerf"><span class="badge nerf6">-33%</span></span></li>
</ul>
<h4 class="ability-title">Spirit Link</h4>
<ul class="changes">
<li data-tag="nerf">Shared Lifesteal now follows general lifesteal rules and has a creep penalty of 40% <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
<h4 class="ability-title">Savage Roar</h4>
<ul class="changes">
<li data-tag="nerf">Aghanim's Shard buff duration decreased from 5s to 4s <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
<ul class="changes">
<li data-tag="nerf">Aghanim's Shard bonus movement speed decreased from 15% to 10% <span class="badge-group" data-overall="nerf"><span class="badge nerf6">-33%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="rework">Level 10 — −25s Summon Spirit Bear Cooldown replaced with +5s True Form Duration <span class="badge rework" data-tag="rework">REWORK</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon ability-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/lone_druid_spirit_bear.png" alt="Spirit Bear" loading="lazy"></div>
  <div class="entity-name">Spirit Bear</div>
</div>
<ul class="changes">
<li data-tag="buff rework">Gold/Experience Bounty changed from <span class="formula-old">175 + 8 per Spirit Bear level</span> up to <span class="formula-trigger" data-formula="f1">165 + 10 per Spirit Bear level</span> <span class="badge rework" data-tag="rework">REWORK</span><span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span><table class="formula-table" id="f1" hidden><thead><tr><th></th><th>L1</th><th>L2</th><th>L3</th><th>L4</th><th>L5</th><th>L6</th><th>L7</th><th>L8</th><th>L9</th><th>L10</th><th>L11</th><th>L12</th><th>L13</th><th>L14</th><th>L15</th><th class="lvl-jump">L20</th><th>L25</th><th>L30</th></tr></thead><tbody><tr><th class="row-label-old">old</th><td>183</td><td>191</td><td>199</td><td>207</td><td>215</td><td>223</td><td>231</td><td>239</td><td>247</td><td>255</td><td>263</td><td>271</td><td>279</td><td>287</td><td>295</td><td class="lvl-jump">335</td><td>375</td><td>415</td></tr><tr><th class="row-label-new">new</th><td>175</td><td>185</td><td>195</td><td>205</td><td>215</td><td>225</td><td>235</td><td>245</td><td>255</td><td>265</td><td>275</td><td>285</td><td>295</td><td>305</td><td>315</td><td class="lvl-jump">365</td><td>415</td><td>465</td></tr><tr><th>Δ %</th><td><span class="badge buff1">+4%</span></td><td><span class="badge buff1">+3%</span></td><td><span class="badge buff1">+2%</span></td><td><span class="badge buff1">+1%</span></td><td><span class="badge neutral">0%</span></td><td><span class="badge nerf1">-1%</span></td><td><span class="badge nerf1">-2%</span></td><td><span class="badge nerf1">-3%</span></td><td><span class="badge nerf1">-3%</span></td><td><span class="badge nerf1">-4%</span></td><td><span class="badge nerf1">-5%</span></td><td><span class="badge nerf1">-5%</span></td><td><span class="badge nerf2">-6%</span></td><td><span class="badge nerf2">-6%</span></td><td><span class="badge nerf2">-7%</span></td><td class="lvl-jump"><span class="badge nerf2">-9%</span></td><td><span class="badge nerf3">-11%</span></td><td><span class="badge nerf3">-12%</span></td></tr></tbody></table></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="nerf">Level 25 — Demolish Bonus Building Damage decreased from +20% to +15% <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/lycan.png" alt="Lycan" loading="lazy"></div>
  <div class="entity-name">Lycan</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Feral Impulse</h4>
<ul class="changes">
<li data-tag="buff">Health Regen increased from 1/3/5/7 to 2/4/6/8 <span class="badge-group" data-overall="buff"><span class="badge buff10">+100%</span><span class="badge buff6">+33%</span><span class="badge buff4">+20%</span><span class="badge buff3">+14%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 10 — Wolves Damage increased from +10 to +14 <span class="badge-group" data-overall="buff"><span class="badge buff7">+40%</span></span></li>
<li data-tag="buff">Level 15 — Summon Wolves Health increased from +350 to +375 <span class="badge-group" data-overall="buff"><span class="badge buff2">+7%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/magnataur.png" alt="Magnus" loading="lazy"></div>
  <div class="entity-name">Magnus</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Shockwave</h4>
<ul class="changes">
<li data-tag="buff">Slow Duration increased from 0.4/0.6/0.8/1.0s to 0.55/0.7/0.85/1.0s <span class="badge-group" data-overall="buff"><span class="badge buff7">+38%</span><span class="badge buff4">+17%</span><span class="badge buff2">+6%</span><span class="badge neutral">0%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 15 — All Attributes per hero hit with Reverse Polarity increased from +12 to +14 <span class="badge-group" data-overall="buff"><span class="badge buff4">+17%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/marci.png" alt="Marci" loading="lazy"></div>
  <div class="entity-name">Marci</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Bodyguard</h4>
<ul class="changes">
<li data-tag="buff">Cast Range increased from 500 to 600 <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 15 — Dispose Damage increased from +100 to +115 <span class="badge-group" data-overall="buff"><span class="badge buff3">+15%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/mars.png" alt="Mars" loading="lazy"></div>
  <div class="entity-name">Mars</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Dauntless</h4>
<ul class="changes">
<li data-tag="buff">HP Regen per extra enemy increased from 40% to 50% <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
<h4 class="ability-title">Spear of Mars</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 100/110/120/130 to 90/100/110/120 <span class="badge-group" data-overall="buff"><span class="badge buff2">+10%</span><span class="badge buff2">+9%</span><span class="badge buff2">+8%</span><span class="badge buff2">+8%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/mirana.png" alt="Mirana" loading="lazy"></div>
  <div class="entity-name">Mirana</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Sacred Arrow</h4>
<ul class="changes">
<li data-tag="buff">Damage increased from 60/150/240/330 to 60/160/260/360 <span class="badge-group" data-overall="buff"><span class="badge neutral">0%</span><span class="badge buff2">+7%</span><span class="badge buff2">+8%</span><span class="badge buff2">+9%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 15 — Leap Attack Speed increased from +90 to +100 <span class="badge-group" data-overall="buff"><span class="badge buff3">+11%</span></span></li>
<li data-tag="buff">Level 20 — Celestial Quiver Damage increased from +40 to +50 <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/monkey_king.png" alt="Monkey King" loading="lazy"></div>
  <div class="entity-name">Monkey King</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Agility decreased from 24 to 23 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span></span></li>
<li data-tag="nerf">Damage at level 1 decreased from 53-57 to 52-56 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-2%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Primal Spring</h4>
<ul class="changes">
<li data-tag="nerf">Movement Slow decreased from 35/50/65/80% to 30/40/50/60% <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-14%</span><span class="badge nerf4">-20%</span><span class="badge nerf5">-23%</span><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/morphling.png" alt="Morphling" loading="lazy"></div>
  <div class="entity-name">Morphling</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Waveform</h4>
<ul class="changes">
<li data-tag="qol">Will now be cast in the desired direction, if the target location is further than the cast range <span class="badge qol" data-tag="qol">QoL</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/muerta.png" alt="Muerta" loading="lazy"></div>
  <div class="entity-name">Muerta</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Attack Speed decreased from 115 to 110 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Supernatural</h4>
<ul class="changes">
<li data-tag="buff">Maximum Stack Count increased from 1 per hero level to 5 + 1 per hero level <span class="badge buff-text" data-tag="buff">BUFF</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/furion.png" alt="Nature's Prophet" loading="lazy"></div>
  <div class="entity-name">Nature's Prophet</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Nature's Call</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 100 to 85/90/95/100 <span class="badge-group" data-overall="buff"><span class="badge buff3">+15%</span><span class="badge buff2">+10%</span><span class="badge buff1">+5%</span><span class="badge neutral">0%</span></span></li>
<li data-tag="buff">Treant Bonus Hero Damage increased from 4/8/12/16 to 6/10/14/18 <span class="badge-group" data-overall="buff"><span class="badge buff8">+50%</span><span class="badge buff5">+25%</span><span class="badge buff4">+17%</span><span class="badge buff3">+12%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 20 — Sprout Damage increased from +170 to +220 <span class="badge-group" data-overall="buff"><span class="badge buff6">+29%</span></span></li>
<li data-tag="buff">Level 20 — Wrath of Nature Cooldown Reduction increased from 15s to 20s <span class="badge-group" data-overall="buff"><span class="badge buff6">+33%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/ogre_magi.png" alt="Ogre Magi" loading="lazy"></div>
  <div class="entity-name">Ogre Magi</div>
</div>
<ul class="changes">
<li data-tag="nerf">Strength gain decreased from 4.2 to 4.0 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-5%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/omniknight.png" alt="Omniknight" loading="lazy"></div>
  <div class="entity-name">Omniknight</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Repel</h4>
<ul class="changes">
<li data-tag="buff">Cooldown decreased from 40/36/32/28s to 40/35/30/25s <span class="badge-group" data-overall="buff"><span class="badge neutral">0%</span><span class="badge buff1">+3%</span><span class="badge buff2">+6%</span><span class="badge buff3">+11%</span></span></li>
</ul>
<h4 class="ability-title">Hammer of Purity</h4>
<ul class="changes">
<li data-tag="buff">Damage increased from 20/40/60/80 to 25/45/65/85 <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span><span class="badge buff3">+12%</span><span class="badge buff2">+8%</span><span class="badge buff2">+6%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/obsidian_destroyer.png" alt="Outworld Destroyer" loading="lazy"></div>
  <div class="entity-name">Outworld Destroyer</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Objurgation</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 250 to 175 <span class="badge-group" data-overall="buff"><span class="badge buff6">+30%</span></span></li>
</ul>
<h4 class="ability-title">Sanity's Eclipse</h4>
<ul class="changes">
<li data-tag="buff">Radius increased from 450/500/550 to 500/525/550 <span class="badge-group" data-overall="buff"><span class="badge buff3">+11%</span><span class="badge buff1">+5%</span><span class="badge neutral">0%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 20 — Astral Imprisonment Mana Capacity Steal increased from 10% to 12% <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/pangolier.png" alt="Pangolier" loading="lazy"></div>
  <div class="entity-name">Pangolier</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Health Regen decreased by 1.0 <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Swashbuckle</h4>
<ul class="changes">
<li data-tag="nerf">Mana Cost increased from 75/80/85/90 to 85/90/95/100 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-13%</span><span class="badge nerf3">-12%</span><span class="badge nerf3">-12%</span><span class="badge nerf3">-11%</span></span></li>
</ul>
<h4 class="ability-title">Roll Up</h4>
<ul class="changes">
<li data-tag="nerf">Mana Cost increased from 50 to 75 <span class="badge-group" data-overall="nerf"><span class="badge nerf8">-50%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="nerf">Level 10 — Lucky Shot Armor Reduction decreased from +3 to +2 <span class="badge-group" data-overall="nerf"><span class="badge nerf6">-33%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/phantom_assassin.png" alt="Phantom Assassin" loading="lazy"></div>
  <div class="entity-name">Phantom Assassin</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Agility increased from 21 to 22 <span class="badge-group" data-overall="buff"><span class="badge buff1">+5%</span></span></li>
<li data-tag="buff">Damage at level 1 increased from 56-58 to 57-59 <span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 10 — Phantom Strike Duration increased from +0.6 to +0.8s <span class="badge-group" data-overall="buff"><span class="badge buff6">+33%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/phantom_lancer.png" alt="Phantom Lancer" loading="lazy"></div>
  <div class="entity-name">Phantom Lancer</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Phantom Rush</h4>
<ul class="changes">
<li data-tag="nerf">Aghanim's Scepter bonus max rush distance decreased from +625 to +575 <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-8%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/phoenix.png" alt="Phoenix" loading="lazy"></div>
  <div class="entity-name">Phoenix</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Dying Light</h4>
<ul class="changes">
<li data-tag="nerf">Missing Health as Damage decreased from 4% to 3.5% <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-12%</span></span></li>
</ul>
<h4 class="ability-title">Sun Ray</h4>
<ul class="changes">
<li data-tag="nerf">Max Health as Heal per second decreased from 0.5/1/1.5/2% to 0.4/0.8/1.2/1.6% <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
<h4 class="ability-title">Supernova</h4>
<ul class="changes">
<li data-tag="nerf">Damage per second decreased from 60/90/120 to 50/80/110 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-17%</span><span class="badge nerf3">-11%</span><span class="badge nerf2">-8%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/primal_beast.png" alt="Primal Beast" loading="lazy"></div>
  <div class="entity-name">Primal Beast</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Trample</h4>
<ul class="changes">
<li data-tag="nerf">Damage AoE decreased from 230 to 200 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-13%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/puck.png" alt="Puck" loading="lazy"></div>
  <div class="entity-name">Puck</div>
</div>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="rework">Level 15 — −15s Dream Coil Cooldown replaced with +2% Puckish Health and Mana Restoration <span class="badge rework" data-tag="rework">REWORK</span></li>
<li data-tag="rework">Level 25 — Dream Coil Pierces Debuff Immunity replaced with −30s Dream Coil Cooldown <span class="badge rework" data-tag="rework">REWORK</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/queenofpain.png" alt="Queen of Pain" loading="lazy"></div>
  <div class="entity-name">Queen of Pain</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Agility decreased from 22 to 20 <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-9%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Shadow Strike</h4>
<ul class="changes">
<li data-tag="nerf">Cooldown rescaled from 13/10/7/4s to 11/9/7/5s <span class="badge-group" data-overall="nerf"><span class="badge buff3">+15%</span><span class="badge buff2">+10%</span><span class="badge neutral">0%</span><span class="badge nerf5">-25%</span></span></li>
<li data-tag="nerf">Aghanim's Scepter AoE decreased from 375 to 300 <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/razor.png" alt="Razor" loading="lazy"></div>
  <div class="entity-name">Razor</div>
</div>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 15 — Static Link Damage Steal increased from +5 to +6 <span class="badge-group" data-overall="buff"><span class="badge buff4">+20%</span></span></li>
<li data-tag="buff">Level 20 — Storm Surge Slow and Damage increased from +30% to +35% <span class="badge-group" data-overall="buff"><span class="badge buff4">+17%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/rubick.png" alt="Rubick" loading="lazy"></div>
  <div class="entity-name">Rubick</div>
</div>
<ul class="changes">
<li data-tag="nerf">Agility gain decreased from 2.5 to 2.2 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-12%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 15 — Fade Bolt Cooldown Reduction increased from 3s to 4s <span class="badge-group" data-overall="buff"><span class="badge buff6">+33%</span></span></li>
<li data-tag="nerf">Level 15 — Stolen Spells Mana Cost Reduction decreased from 50% to 40% <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
<li data-tag="nerf">Level 25 — Curiosity Bonuses decreased from 2× to 1.5× <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/sand_king.png" alt="Sand King" loading="lazy"></div>
  <div class="entity-name">Sand King</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Attack Speed decreased from 110 to 100 <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-9%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Stinger</h4>
<ul class="changes">
<li data-tag="nerf">Slow Duration rescaled from 4/5/6/7s to 5s <span class="badge-group" data-overall="nerf"><span class="badge buff5">+25%</span><span class="badge neutral">0%</span><span class="badge nerf4">-17%</span><span class="badge nerf6">-29%</span></span></li>
</ul>
<h4 class="ability-title">Epicenter</h4>
<ul class="changes">
<li data-tag="nerf">Base Radius decreased from 500 to 450 <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-10%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/nevermore.png" alt="Shadow Fiend" loading="lazy"></div>
  <div class="entity-name">Shadow Fiend</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Shadowraze</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 80 to 75 <span class="badge-group" data-overall="buff"><span class="badge buff2">+6%</span></span></li>
</ul>
<h4 class="ability-title">Presence of the Dark Lord</h4>
<ul class="changes">
<li data-tag="buff">Armor Reduction rescaled from 3/4/5/6 to 2.5/4/5.5/7 <span class="badge-group" data-overall="buff"><span class="badge nerf4">-17%</span><span class="badge neutral">0%</span><span class="badge buff2">+10%</span><span class="badge buff4">+17%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/skywrath_mage.png" alt="Skywrath Mage" loading="lazy"></div>
  <div class="entity-name">Skywrath Mage</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Mystic Flare</h4>
<ul class="changes">
<li data-tag="buff">Cooldown decreased from 60/40/20s to 55/35/15s <span class="badge-group" data-overall="buff"><span class="badge buff2">+8%</span><span class="badge buff3">+12%</span><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/slardar.png" alt="Slardar" loading="lazy"></div>
  <div class="entity-name">Slardar</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Slithereen Crush</h4>
<ul class="changes">
<li data-tag="nerf">Cooldown increased from 7s to 8.5/8/7.5/7s <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-21%</span><span class="badge nerf3">-14%</span><span class="badge nerf2">-7%</span><span class="badge neutral">0%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/snapfire.png" alt="Snapfire" loading="lazy"></div>
  <div class="entity-name">Snapfire</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Damage increased by 2 <span class="badge buff-text" data-tag="buff">BUFF</span></li>
<li data-tag="buff">Damage at level 1 increased from 51-57 to 53-59 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/spectre.png" alt="Spectre" loading="lazy"></div>
  <div class="entity-name">Spectre</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Agility increased from 26 to 29 <span class="badge-group" data-overall="buff"><span class="badge buff3">+12%</span></span></li>
<li data-tag="buff">Damage at level 1 increased from 49-53 to 52-56 <span class="badge-group" data-overall="buff"><span class="badge buff2">+6%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Dispersion</h4>
<ul class="changes">
<li data-tag="nerf">Damage rescaled from 8/12/16/20% to 9/12/15/18% <span class="badge-group" data-overall="nerf"><span class="badge buff3">+12%</span><span class="badge neutral">0%</span><span class="badge nerf2">-6%</span><span class="badge nerf2">-10%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/storm_spirit.png" alt="Storm Spirit" loading="lazy"></div>
  <div class="entity-name">Storm Spirit</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Galvanized</h4>
<ul class="changes">
<li data-tag="buff">Now gains a charge every 3 levels <span class="badge buff-text" data-tag="buff">BUFF</span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 10 — Overload Attack/Movement Speed Slow increased from +20/20% to +25/25% <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/sven.png" alt="Sven" loading="lazy"></div>
  <div class="entity-name">Sven</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Storm Hammer</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 110/115/120/125 to 110 <span class="badge-group" data-overall="buff"><span class="badge neutral">0%</span><span class="badge buff1">+4%</span><span class="badge buff2">+8%</span><span class="badge buff3">+12%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/techies.png" alt="Techies" loading="lazy"></div>
  <div class="entity-name">Techies</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Mana Regen decreased by 0.5 <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
<li data-tag="nerf">Intelligence gain decreased from 3.0 to 2.7 <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-10%</span></span></li>
<li data-tag="nerf">Damage gain per level decreased from 3.3 to 3.2 <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-3%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">M.A.D.</h4>
<ul class="changes">
<li data-tag="buff rework">Mana Pool as Regen rescaled from <span class="formula-old">0.08% + 0.02% per level</span> to <span class="formula-trigger" data-formula="f2">0.1% + 0.01% per level</span> <span class="badge rework" data-tag="rework">REWORK</span><span class="badge-group" data-overall="buff"><span class="badge buff2">+10%</span></span><table class="formula-table" id="f2" hidden><thead><tr><th></th><th>L1</th><th>L2</th><th>L3</th><th>L4</th><th>L5</th><th>L6</th><th>L7</th><th>L8</th><th>L9</th><th>L10</th><th>L11</th><th>L12</th><th>L13</th><th>L14</th><th>L15</th><th class="lvl-jump">L20</th><th>L25</th><th>L30</th></tr></thead><tbody><tr><th class="row-label-old">old</th><td>0.10%</td><td>0.12%</td><td>0.14%</td><td>0.16%</td><td>0.18%</td><td>0.20%</td><td>0.22%</td><td>0.24%</td><td>0.26%</td><td>0.28%</td><td>0.30%</td><td>0.32%</td><td>0.34%</td><td>0.36%</td><td>0.38%</td><td class="lvl-jump">0.48%</td><td>0.58%</td><td>0.68%</td></tr><tr><th class="row-label-new">new</th><td>0.11%</td><td>0.12%</td><td>0.13%</td><td>0.14%</td><td>0.15%</td><td>0.16%</td><td>0.17%</td><td>0.18%</td><td>0.19%</td><td>0.20%</td><td>0.21%</td><td>0.22%</td><td>0.23%</td><td>0.24%</td><td>0.25%</td><td class="lvl-jump">0.30%</td><td>0.35%</td><td>0.40%</td></tr><tr><th>Δ %</th><td><span class="badge buff2">+10%</span></td><td><span class="badge neutral">0%</span></td><td><span class="badge nerf2">-7%</span></td><td><span class="badge nerf3">-12%</span></td><td><span class="badge nerf4">-17%</span></td><td><span class="badge nerf4">-20%</span></td><td><span class="badge nerf5">-23%</span></td><td><span class="badge nerf5">-25%</span></td><td><span class="badge nerf6">-27%</span></td><td><span class="badge nerf6">-29%</span></td><td><span class="badge nerf6">-30%</span></td><td><span class="badge nerf6">-31%</span></td><td><span class="badge nerf6">-32%</span></td><td><span class="badge nerf6">-33%</span></td><td><span class="badge nerf7">-34%</span></td><td class="lvl-jump"><span class="badge nerf7">-37%</span></td><td><span class="badge nerf7">-40%</span></td><td><span class="badge nerf7">-41%</span></td></tr></tbody></table></li>
</ul>
<h4 class="ability-title">Reactive Tazer</h4>
<ul class="changes">
<li data-tag="nerf">Explosion Radius decreased from 450 to 400 <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-11%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/templar_assassin.png" alt="Templar Assassin" loading="lazy"></div>
  <div class="entity-name">Templar Assassin</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Movement Speed increased from 310 to 315 <span class="badge-group" data-overall="buff"><span class="badge buff1">+2%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/tidehunter.png" alt="Tidehunter" loading="lazy"></div>
  <div class="entity-name">Tidehunter</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Mana Regen decreased by 0.5 <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/shredder.png" alt="Timbersaw" loading="lazy"></div>
  <div class="entity-name">Timbersaw</div>
</div>
<ul class="changes">
<li data-tag="buff">Base Damage increased by 2 <span class="badge buff-text" data-tag="buff">BUFF</span></li>
<li data-tag="buff">Damage at level 1 <span class="wrong-word">decreased</span> from 46-50 to 48-52 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span><div class="correction-note"><span class="correction-label">Note</span>— The patch text says "decreased", but the values actually went up.</div></li>
<li data-tag="buff">Base Intelligence increased from 23 to 24 <span class="badge-group" data-overall="buff"><span class="badge buff1">+4%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Reactive Armor</h4>
<ul class="changes">
<li data-tag="buff">Bonus HP Regen increased from 0.4/0.5/0.6/0.7 to 0.5/0.6/0.7/0.8 <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span><span class="badge buff4">+20%</span><span class="badge buff4">+17%</span><span class="badge buff3">+14%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/tinker.png" alt="Tinker" loading="lazy"></div>
  <div class="entity-name">Tinker</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Deploy Turrets</h4>
<ul class="changes">
<li data-tag="misc">Updated sound effects <span class="badge misc" data-tag="misc">MISC</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/tiny.png" alt="Tiny" loading="lazy"></div>
  <div class="entity-name">Tiny</div>
</div>
<ul class="changes">
<li data-tag="nerf">Base Attack Speed decreased from 90 to 85 <span class="badge-group" data-overall="nerf"><span class="badge nerf2">-6%</span></span></li>
</ul>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Grow</h4>
<ul class="changes">
<li data-tag="buff">Toss Bonus Damage increased from 50/175/300 to 50/200/350 <span class="badge-group" data-overall="buff"><span class="badge neutral">0%</span><span class="badge buff3">+14%</span><span class="badge buff4">+17%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="rework">Level 10 — +8 Strength replaced with +2 Tree Grab Attacks <span class="badge rework" data-tag="rework">REWORK</span></li>
<li data-tag="rework">Level 15 — −8% Grow Attack Speed Reduction replaced with +10 Strength <span class="badge rework" data-tag="rework">REWORK</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/treant.png" alt="Treant Protector" loading="lazy"></div>
  <div class="entity-name">Treant Protector</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Eyes In The Forest</h4>
<ul class="changes">
<li data-tag="qol">Added AoE indicator to cast <span class="badge qol" data-tag="qol">QoL</span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="nerf">Level 10 — Living Armor Heal Per Second decreased from +4 to +3 <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/troll_warlord.png" alt="Troll Warlord" loading="lazy"></div>
  <div class="entity-name">Troll Warlord</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Whirling Axes (Ranged)</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 60 to 50 <span class="badge-group" data-overall="buff"><span class="badge buff4">+17%</span></span></li>
</ul>
<h4 class="ability-title">Whirling Axes (Melee)</h4>
<ul class="changes">
<li data-tag="buff">Damage increased from 50/100/150/200 to 75/120/165/210 <span class="badge-group" data-overall="buff"><span class="badge buff8">+50%</span><span class="badge buff4">+20%</span><span class="badge buff2">+10%</span><span class="badge buff1">+5%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/tusk.png" alt="Tusk" loading="lazy"></div>
  <div class="entity-name">Tusk</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Drinking Buddies</h4>
<ul class="changes">
<li data-tag="nerf">No longer castable while rooted <span class="badge nerf-text" data-tag="nerf">NERF</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/vengefulspirit.png" alt="Vengeful Spirit" loading="lazy"></div>
  <div class="entity-name">Vengeful Spirit</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Vengeance Aura</h4>
<ul class="changes">
<li data-tag="buff">Self Bonus increased from 20% to 25% <span class="badge-group" data-overall="buff"><span class="badge buff5">+25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/venomancer.png" alt="Venomancer" loading="lazy"></div>
  <div class="entity-name">Venomancer</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Poison Sting</h4>
<ul class="changes">
<li data-tag="nerf">Movement Slow decreased from 10% to 8% <span class="badge-group" data-overall="nerf"><span class="badge nerf4">-20%</span></span></li>
</ul>
<h4 class="ability-title">Snakebite</h4>
<ul class="changes">
<li data-tag="nerf">Damage per second rescaled from 20/25/30/35 to 10/20/30/40 <span class="badge-group" data-overall="nerf"><span class="badge nerf8">-50%</span><span class="badge nerf4">-20%</span><span class="badge neutral">0%</span><span class="badge buff3">+14%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="buff">Level 15 — Poison Sting Slow increased from +7% to +10% <span class="badge-group" data-overall="buff"><span class="badge buff7">+43%</span></span></li>
<li data-tag="rework">Level 20 — +40% Snakebite Damage replaced with +100 Snakebite Initial Damage <span class="badge rework" data-tag="rework">REWORK</span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/viper.png" alt="Viper" loading="lazy"></div>
  <div class="entity-name">Viper</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Nosedive</h4>
<ul class="changes">
<li data-tag="nerf">Cooldown increased from 20s to 25s <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/weaver.png" alt="Weaver" loading="lazy"></div>
  <div class="entity-name">Weaver</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">The Swarm</h4>
<ul class="changes">
<li data-tag="buff">Mana Cost decreased from 110 to 110/105/100/95 <span class="badge-group" data-overall="buff"><span class="badge neutral">0%</span><span class="badge buff1">+5%</span><span class="badge buff2">+9%</span><span class="badge buff3">+14%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/windrunner.png" alt="Windranger" loading="lazy"></div>
  <div class="entity-name">Windranger</div>
</div>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="nerf">Level 25 — Focus Fire Cooldown Advance on Kills decreased from 18s to 16s <span class="badge-group" data-overall="nerf"><span class="badge nerf3">-11%</span></span></li>
<li data-tag="buff">Level 25 — Powershot Max HP Execution Threshold increased from 15% to 16% <span class="badge-group" data-overall="buff"><span class="badge buff2">+7%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/winter_wyvern.png" alt="Winter Wyvern" loading="lazy"></div>
  <div class="entity-name">Winter Wyvern</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Splinter Blast</h4>
<ul class="changes">
<li data-tag="nerf">Movement Slow decreased from 28/32/36/40% to 27/30/33/36% <span class="badge-group" data-overall="nerf"><span class="badge nerf1">-4%</span><span class="badge nerf2">-6%</span><span class="badge nerf2">-8%</span><span class="badge nerf2">-10%</span></span></li>
</ul>
<h4 class="subgroup">Talents</h4>
<ul class="changes">
<li data-tag="nerf">Level 10 — Cold Embrace Base Heal per Second decreased from +20 to +15 <span class="badge-group" data-overall="nerf"><span class="badge nerf5">-25%</span></span></li>
</ul>
</div>
<div class="entity-block">
<div class="entity hero-entity">
  <div class="entity-icon hero-icon"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/witch_doctor.png" alt="Witch Doctor" loading="lazy"></div>
  <div class="entity-name">Witch Doctor</div>
</div>
<h4 class="subgroup">Abilities</h4>
<h4 class="ability-title">Voodoo Restoration</h4>
<ul class="changes">
<li data-tag="buff">Radius increased from 500/550/600/650 to 650 <span class="badge-group" data-overall="buff"><span class="badge buff6">+30%</span><span class="badge buff4">+18%</span><span class="badge buff2">+8%</span><span class="badge neutral">0%</span></span></li>
</ul>
</div>'''
W(HANDCRAFTED_7_41C_BODY)

write_footer()
save_html('7.41c.html')

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
W(plain_header("Crude"))
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
W(li("Base Armor decreased by 1", t("NERF")))
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
W(li("Base Damage decreased by 3", t("NERF")))
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
W(li("Now grants Invoker an additional Ability Point at hero levels 6, 12, and 18", t("BUFF")))
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
W(li("Base Health Regen decreased by 1.25", t("NERF")))
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
W(li("Base Mana Regen increased by 0.25", t("BUFF")))
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
save_html('7.41b.html')
save_calendar_html()
