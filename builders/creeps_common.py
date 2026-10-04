"""Helpers shared by the Neutral Stats page (builders/creeps.py), its per-patch
history (builders/creeps_history.py) and the Neutral Abilities page
(builders/creeps_abilities.py): value formatting, HTML escaping, ability
names / icons, hull sizes and the common page shell.

Leaf module — imports nothing from the other creeps modules.
"""
import os as _os

import builders.site_common as _site

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_ABIL_ICON_DIR = _os.path.join(_HERE, 'icons', 'abilities')

# Empty-cell marker used by both tables.
DASH = '<span class="ua-dash">—</span>'

# Neutral Stats ability columns (slot order).
ABILITY_COLS = ('ability1', 'ability2', 'ability3')

# Hidden marker abilities — not real spells, suppressed from output.
# `neutral_upgrade`: every neutral has this; auto-buff tracker.
# `creep_piercing`: tags the unit with pierce attack-class. The info
# already lives in the Тип атаки column, so showing it as an ability
# is redundant.
ABILITY_SKIP = {'neutral_upgrade', 'creep_piercing'}

# Autocast abilities — get the animated golden ring marker on their icon
# (mirrors the in-game autocast toggle visual). The data feed carries no
# AbilityBehavior/autocast flag, so this list is maintained by hand.
AUTOCAST_ABILITIES = {
    'forest_troll_high_priest_heal',   # Heal (Forest Troll High Priest)
    'ogre_magi_frost_armor',           # Ice Armor (Ogre Frostmage)
    'spawnlord_master_freeze',         # Petrify (Prowler Shaman)
}

# Display-name overrides — when Valve's canonical dname diverges from the
# team's preferred terminology (e.g. Valve calls it "Ice Armor", we use
# "Frost Armor" to match the creep's "Frostmage" name).
ABILITY_NAME_OVERRIDES = {
    'ogre_magi_frost_armor': 'Frost Armor',
}

# Hull → (collision size, bound radius). Values per Liquipedia/Unit_Size,
# cross-checked in-game via cl_dumpentity (CCollisionProperty m_vecMaxs):
# a neutral with no explicit BoundsHullName reports ±24 → DOTA_HULL_SIZE_HERO.
HULL_BOUNDS = {
    'DOTA_HULL_SIZE_HERO':      (27, 24),
    'DOTA_HULL_SIZE_BIG_HERO':  (43, 40),
    'DOTA_HULL_SIZE_LARGE':     (41, 40),
    'DOTA_HULL_SIZE_REGULAR':   (36, 16),
    'DOTA_HULL_SIZE_SIEGE':     (40, 16),
    'DOTA_HULL_SIZE_SMALL':     (18, 8),
    'DOTA_HULL_SIZE_SMALLEST':  (4, 2),
    'DOTA_HULL_SIZE_HUGE':      (80, 80),
    'DOTA_HULL_SIZE_FILLER':    (112, 96),
    'DOTA_HULL_SIZE_TOWER':     (144, 144),
    'DOTA_HULL_SIZE_BARRACKS':  (160, 144),
}
# npc_dota_creep_neutral inherits HERO from npc_dota_units_base (the base
# class is engine-internal / absent from npc_units.txt), so neutrals
# without an explicit hull resolve to HERO. Verified in-game via
# cl_dumpentity (CCollisionProperty m_vecMaxs) across 5 units: Kobold,
# Ogre, Granite Golem, Black Dragon all = ±24 (HERO) regardless of model
# scale; only skeleton_warrior overrides to SMALL (±8).
# NOTE: HERO default is NEUTRAL-ONLY. Summons / non-neutral units have
# different hulls — a future summons table must NOT reuse this default;
# resolve their hull explicitly or per-unit.
NEUTRAL_DEFAULT_HULL = 'DOTA_HULL_SIZE_HERO'
# MovementTurnRate default from npc_dota_units_base = 0.5. 35/49 neutrals
# explicitly override to 0.9 (so base ≠ 0.9); the 14 that don't are the
# heavy/slow creeps (golems, frogs, ancients, thunder lizard, warpine) →
# they inherit 0.5. Inferred (turn rate isn't readable via cl_dumpentity),
# but the explicit-0.9 pattern + slow-creep grouping make it solid.
NEUTRAL_DEFAULT_TURN_RATE = 0.5


# ---- Values ----

def fmt_num(x):
    if isinstance(x, str):
        try:
            x = float(x) if '.' in x else int(x)
        except ValueError:
            return x
    if isinstance(x, float):
        return f'{x:g}'.replace('.', ',')
    return str(x)


def fmt_regen(x):
    x = float(x or 0)
    return '0' if abs(x) < 1e-9 else f'{x:.2f}'.replace('.', ',')


def safe_int(v, default=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def armor_factor(a):
    return (0.06 * a) / (1 + 0.06 * abs(a))


def ehp_phys_val(hp, a):
    return round(hp / max(0.01, 1 - armor_factor(a))) if hp else 0


def ehp_mag_val(hp, mr):
    return round(hp / max(0.01, 1 - mr / 100)) if hp else 0


# ---- HTML ----

def esc(s):
    return (str(s).replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;'))


def attr_esc(s):
    """esc + quote escape — safe to drop into a double-quoted attribute."""
    return esc(s).replace('"', '&quot;')


# ---- Abilities ----

def ability_dname(slug, abil_slim):
    """Display name for an ability slug ('' for hidden markers / blanks).
    `abil_slim` is data/abilities_slim.json (slug → {'dname': …})."""
    if not slug or slug in ABILITY_SKIP:
        return ''
    if slug in ABILITY_NAME_OVERRIDES:
        return ABILITY_NAME_OVERRIDES[slug]
    entry = abil_slim.get(slug)
    if entry and entry.get('dname'):
        return entry['dname']
    return slug.replace('_', ' ').title()


def autocast_fx() -> str:
    """The in-game autocast ring: Dota's own particle system (autocasting_square.vpcf —
    glow crackle + embers on the 40-point square) baked into a looping WebP by
    tools/autocast/build_autocast.py. One shared image, no per-frame CPU."""
    return ('<img class="autocast-fx" src="icons/ui/autocast.webp" alt="" '
            'aria-hidden="true" width="100" height="100">')


def has_abil_icon(slug):
    return bool(slug) and _os.path.exists(
        _os.path.join(_ABIL_ICON_DIR, slug + '.png'))


def abil_icon_html(slug, name):
    """The ability icon (changelog style, smaller); autocast abilities get the
    animated ring overlay. Callers check has_abil_icon() first."""
    img = (f'<img class="abil-ico" src="icons/abilities/{slug}.png" '
           f'alt="{esc(name)}" loading="lazy" width="128" height="128">')
    if slug in AUTOCAST_ABILITIES:
        # Thin "snake" stroke that crawls along the icon's rounded
        # frame at constant speed (incl. corners) — SVG dash offset
        # animation. pathLength=100 normalises the perimeter so the
        # dash gap loops seamlessly.
        # Phase-locked strokes (shared offset animation) forming one
        # fuzzy comet: a wide blurred aura (fluff), a bright body,
        # stepped tail segments that fade toward the tail tip, and a
        # cluster of tiny dots riding along (pollen). Head leads at
        # the high end of the painted range; the tail (low end)
        # fades out near its tip.
        return (f'<span class="abil-ico-wrap abil-autocast">'
                f'{img}{autocast_fx()}</span>')
    return img


# ---- Page ----

def page_shell(title, nav, inner, asset_version):
    """Full HTML of a creeps table page. `inner` is everything inside the
    scroll box: sub-tab bar, toolbar and the <table>…</table>."""
    return (
        '<!DOCTYPE html>\n'
        '<html lang="ru">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        f'<title>SIKLE | {title}</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={asset_version}">\n'
        '</head>\n'
        '<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page">\n'
        # Overlay frame outlining the pinned identity block during scroll.
        # Lives OUTSIDE .creeps-scroll (which scrolls) so it never hits the
        # Chrome bug where box-shadow/border on position:sticky cells fails
        # to repaint mid-scroll. scripts.js positions + toggles it.
        '<div class="sticky-frame" aria-hidden="true"></div>\n'
        '<div class="sticky-frame-top" aria-hidden="true"></div>\n'
        '<div class="creeps-scroll">\n'
        # Sub-tab bar + blurb + toolbar all live INSIDE the scroll box (above
        # the table) so they scroll away with the page just like the Mana Items
        # layout — only the site nav and the sticky table headers remain pinned.
        # They're sticky-left so they stay put during horizontal scroll.
        f'{inner}'
        '</div>\n'
        '</div>\n'
        f'<script defer src="src/scripts.js?v={asset_version}"></script>\n'
        '</body>\n</html>\n'
    )


def write_dist(name, text):
    """Write `text` to dist/<name> (text mode, UTF-8)."""
    _os.makedirs(_site.DIST_DIR, exist_ok=True)
    with open(_os.path.join(_site.DIST_DIR, name), 'w', encoding='utf-8') as f:
        f.write(text)
