"""Index page generator (index.html)."""

import os as _os
import html as _html
import re

import site_common as _site

from .meta import PATCHES, RELEASE_HISTORY, _render_top_nav
from .page import _ASSET_VERSION

# Manual "page" entries in the What's New popup.
# Date = when the page was added to the site (not Valve's release date).
_WHATSNEW_PAGES = [
    ("page",  "Hero Lab",       "Jun 13", "hero_lab.html"),
    ("page",  "Item Dynamics",  "Jun 5",  "items_dyn.html"),
    ("page",  "Hero Dynamics",  "Jun 3",  "heroes_dyn.html"),
    ("page",  "Neutral Creeps", "May 19", "neutral_stats.html"),
]

# "Added to site" dates for patch pages.
# Date = when the patch page was published on this site (not Valve's release date).
# Add a new entry here when a new patch page is published.
_PATCH_SITE_DATES = {
    "7.41d": "Jun 5",
    "7.39e": "Jun 14",
}

_WHATSNEW_MAX = 10


def _build_whatsnew():
    """Merge manual page entries with patch entries from PATCHES,
    sorted newest first. Patch dates come from _PATCH_SITE_DATES;
    patches not in that dict are omitted from the popup.
    Total capped at _WHATSNEW_MAX entries."""
    import datetime

    def _sort_key(entry):
        _, _, date_str, _ = entry
        try:
            dt = datetime.datetime.strptime(f"{date_str} 2026", "%b %d %Y")
            ref = datetime.datetime(2026, 6, 14)
            if dt > ref:
                dt = dt.replace(year=2025)
            return dt
        except ValueError:
            return datetime.datetime.min

    patch_entries = []
    for p in PATCHES:
        site_date = _PATCH_SITE_DATES.get(p["version"])
        if site_date:
            patch_entries.append(("patch", p["version"], site_date, p["filename"]))

    combined = list(_WHATSNEW_PAGES) + patch_entries
    combined.sort(key=_sort_key, reverse=True)
    return combined[:_WHATSNEW_MAX]

# Pixel "!" SVG (crispEdges rects, same style as nav-back-arrow).
# ViewBox 4x12: body 4×8, gap 2, dot 4×2.
_WN_EXCL_SVG = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 4 12' shape-rendering='crispEdges'>"
    "<rect x='0' y='0' width='4' height='8' fill='%23e3c46a'/>"
    "<rect x='0' y='10' width='4' height='2' fill='%23e3c46a'/>"
    "</svg>"
)


def _whatsnew_html():
    rows = []
    for kind, label, date, href in _build_whatsnew():
        tag = f'<span class="whatsnew-tag whatsnew-tag-{kind}">{kind}</span>'
        date_span = f'<span class="whatsnew-date">{date}</span>'
        rows.append(
            f'<a class="whatsnew-row" href="{href}">'
            f'{tag}{_html.escape(label)}{date_span}</a>'
        )
    items = '\n'.join(rows)
    # The badge sits inside .version-beta-wrap (in site_common.py) so it's
    # positioned at the bottom-right corner of the BETA label.
    # The popup is body-level so it isn't clipped by the nav overflow.
    return (
        '<div class="whatsnew-popup" role="dialog" aria-label="What\'s new">\n'
        f'  <div class="whatsnew-list">{items}</div>\n'
        '</div>'
    )


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
        '<a class="support-btn support-donation" '
        'href="https://www.donationalerts.com/r/sikleq" target="_blank" rel="noopener">'
        '<span class="inv-slot">'
        '<img class="inv-icon" src="icons/ui/gothic/icon_donation.png" alt="">'
        '<span class="don-coin" aria-hidden="true"></span>'
        '<span class="support-ru-tag">RU</span></span>'
        '<span class="inv-cap">Donation</span></a>'
        '<a class="support-btn support-kofi" '
        'href="https://ko-fi.com/sikle" target="_blank" rel="noopener">'
        '<span class="inv-slot">'
        '<img class="inv-icon" src="icons/ui/gothic/gold_stack.png" alt="">'
        '<span class="support-eng-tag">ENG</span></span>'
        '<span class="inv-cap">Ko-Fi</span></a>'
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
    _names: list = []
    _hidden = 0
    _sig_path = _os.path.join(_os.path.dirname(__file__), '..', 'data', 'signatures.json')
    try:
        import json as _json
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
        f'{_whatsnew_html()}\n'
        f'<script src="src/scripts.js?v={_ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  → index.html: {len(html):,} bytes")
