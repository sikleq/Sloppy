"""Page-level writers: write_head, write_footer, save_html, save_assets, and post-processing helpers."""

import os
import re

import patch.site_common as _site

from .output import H, W
from .state import _State, reset_page_state
from .meta import _render_top_nav, _patch_meta_parts
from .elements import _close_block, STAT_ICONS, STAT_DETECT_RULES
from .static_has import add_static_has_classes
from .talent_tree import light_talent_trees

_ASSET_VERSION = _site.compute_asset_version()


def write_head(version, date):
    """Render head + top nav (Patches+Calendar tabs + version) + container + toolbar."""
    if H:
        # rows written after the previous page's save_html would open this page, above its header (2026-10-27: 7.38c's
        # last talent block sat after save_html — 7.39 began with it and lost its layout)
        raise RuntimeError(f"{version}: {len(H)} fragment(s) written after the previous page was saved: "
                           f"{''.join(H)[:200]!r}")
    _State.current_patch_version = version
    _State.current_entity_key = None
    _State.current_section_slug = None
    _State.terrain_anchor = False
    nav = _render_top_nav(active="changelogs", current_version=version, date=date, patch_context=True)
    _State.patch_info = patch_info_html(version, date)
    W(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>s/kle - Patch {version}</title>
{_site.head_common(prefix="../")}
<link rel="stylesheet" href="../styles.css?v={_ASSET_VERSION}">
</head>
<body class="patch-page">

{nav}
<a class="nav-back-arrow" href="../calendar.html" aria-label="Back to calendar" title="Back to calendar"></a>
<div class="container">
''')


def patch_info_html(version, date):
    """The patch's official notes link, release date, how long it ran (or is live) and how long after the previous one,
    in a card like the filters' above them, folded at first; a tab with a pixel arrow in the middle of the filters'
    top edge opens it (owner 2026-11-07, mock "Вариант 1": "Official notes и другую инфу сделать в таком же блоке,
    только выше панели фильтров тегов и тоже добавить кнопку, только в центр верхней кромки панели тегов-фильтров").
    It stood on a plate in the first section's header before."""
    prev_part, age_part = _patch_meta_parts(version)
    rows = [f'<a class="pi-official" href="https://www.dota2.com/patches/{version}" target="_blank" rel="noopener">'
            f'Official notes<i class="pi-out" aria-hidden="true"></i></a>',
            f'<div class="pi-row"><span>Released</span><span class="pi-val"><b>{date}</b></span></div>']
    if age_part:
        key, value = age_part.split(":", 1)
        rows.append(f'<div class="pi-row"><span>{key}</span><span class="pi-val">{value.strip()}</span></div>')
    if prev_part:
        days, after = prev_part.split(" after ", 1)          # "<b>55</b> days", "<b>7.38c</b>"
        rows.append(f'<div class="pi-row"><span>After {re.sub(r"</?b>", "", after)}</span>'
                    f'<span class="pi-val">{days}</span></div>')
    # open at first (owner 2026-11-07: "official notes блок пусть тоже по умолчанию включен"); the tab folds it
    return '<div class="pinfo-card" id="pinfo-card">' + "".join(rows) + '</div>'


# the tags of the filter window: (data-filter, the badge's colour class, the word)
FILTER_TAGS = (("buff", "buff-text", "BUFF"), ("nerf", "nerf-text", "NERF"), ("new", "new", "NEW"), ("del", "del", "DEL"),
               ("rework", "rework", "REWORK"), ("swap", "swap", "SWAP"), ("misc", "misc", "MISC"), ("qol", "qol", "QoL"))


# the filters' switch: a round button of the corner stack, above the search, in its look (owner 2026-11-07: "иконку
# фильтров всё же вынеси сюда и адаптируй"; it stood in the header beside the colour-blind one; icon:
# tools/pixel_icons/filter_icon.py)
FILTER_FAB = ('<button class="filter-fab" id="filter-fab" type="button" aria-expanded="true" aria-controls="filter-pop" '
              'aria-label="Filters"></button>')


def filter_pop_html():
    """The filters in a window of their own behind a round button of the corner stack (owner 2026-11-07, mock "Вариант
    3", "без слова Filters, иконки-закладки, рамка в стиле нашего сайта, панель появляется при нажатии на кнопку"):
    a narrow column at the page's right edge, apart from the button ("панель должна появляться отдельно от кнопки …
    списком, чтобы было узко … по правому краю лаконично"): each tag its tile (as in the rows) and its word, then the
    sections' words."""
    # a box to tick before each word, in the tag's colour (owner 2026-11-07, look 6 "галочки в рамке": the CSS draws it)
    tags = "".join(f'<button class="badge {cls} filter-btn" data-filter="{key}" type="button">'
                   f'<span class="fp-word">{word}</span></button>' for key, cls, word in FILTER_TAGS)
    # a card at the page's right edge, out from the start (owner 2026-11-07: "фильтры включены по умолчанию и давай
    # их по правому краю"); filter-fab.js puts it away when it would cover the text. Above it the patch's own card
    # (patch_info_html) behind the tab on its top edge.
    info, _State.patch_info = _State.patch_info, ""
    tab = ('<button type="button" class="pinfo-tab" aria-expanded="true" aria-controls="pinfo-card" '
           'aria-label="Patch info"><i aria-hidden="true"></i></button>') if info else ""
    return ('<div class="filter-pop" id="filter-pop">' + info + tab + '<div class="filter-rail"><div class="legend-tags">'
            + tags + '</div><div class="legend-categories"><!--CATEGORIES_BAR--></div></div></div>')


def write_footer():
    """Render close-block + back-to-top button + script tag + closing tags."""
    W(_close_block())
    if _State.section_panel_open:
        W('</section>')
        _State.section_panel_open = False
    # The corner buttons in one framed panel, bottom right, filters open or not (owner 2026-11-07, mock "Вариант A"):
    # top, filters, search, weights. No hover tips on them (owner 2026-09-28) — the loupe keeps only its key.
    # "Top" jumps at once, no ride up ("чтобы телепортировало наверх, а не везло").
    W('<div class="corner-dock">'
      '<button class="back-to-top at-top btt-wait" aria-label="Back to top" onclick="window.scrollTo({top:0, behavior:\'instant\'})">'
      '</button>' + FILTER_FAB +
      '<button class="search-fab" id="search-fab" type="button" aria-label="Search heroes, items, abilities" '
      'aria-expanded="false" aria-controls="search-pop" title="Search (\\ or /)" aria-keyshortcuts="Backslash Slash">'
      '</button><button class="dyn-w-fab" id="dyn-weights-btn" type="button" aria-label="Weighted scores"></button>'
      '</div>')
    # the search field opens above the panel ("/" opens it, Esc closes)
    W('<div class="search-pop" id="search-pop" hidden><div class="search-box">'
      '<input type="text" id="entity-search" placeholder="Search heroes, items, abilities…" autocomplete="off" spellcheck="false">'
      '<div class="search-results" id="search-results"></div></div></div>')
    # the filters' card at the right edge, middle of the screen; the panel's filter button hides it
    W(filter_pop_html())
    W(f'<script defer src="../src/scripts-base.js?v={_ASSET_VERSION}"></script>')
    W('</div></body></html>')


def save_assets():
    """No-op kept for backward compatibility.
    styles.css and scripts.js are source files (read at module load),
    not generated artefacts. Nothing to write."""


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
        items = list(_LI_RE.finditer(body))
        if not items:
            return m.group(0)

        # First pass: classify each li as "starter" (has ability-row class)
        # or "continuation" while inside a box.
        is_starter = []
        # A row carrying its own change tag (BUFF / NERF / REWORK …) is a separate change,
        # not part of the ability's description: it must not continue the box, or its tag
        # lands in the box's collapsed tag column over the text (7.38 Heaven's Halberd:
        # "Disarm Mana Cost decreased" after "Active: Disarm can now be dispelled").
        # NEW rows still continue — a NEW entity's description rows are all tagged NEW.
        breaks_box = []
        for it in items:
            is_starter.append(' ability-row' in it.group(1) or 'class="ability-row' in it.group(1))
            tag = re.search(r'data-tag="([^"]*)"', it.group(1))
            own_badge = it.group(2).lstrip().startswith('<span class="badge')
            breaks_box.append(own_badge and not (tag and 'new' in tag.group(1).split()))

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
            elif in_box and breaks_box[i]:
                roles[i - 1] = 'solo' if box_start_idx == i - 1 else 'cont-end'
                in_box = False
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

        # boxes whose starter has its own chip are shifted right by the tag column (CSS)
        tagged = [False] * len(items)
        cur = False
        for i, role in enumerate(roles):
            if role in ('start', 'solo'):
                cur = items[i].group(2).lstrip().startswith('<span class="badge')
            tagged[i] = cur and role is not None
            if role in ('solo', 'cont-end'):
                cur = False

        # An ability described only by its boxes (a new creep's, 7.38 Riverborn Aura) stands beside the icon under its
        # name, as one with a row below its box (owner 2026-11-07: "не лучше Riverborn Aura расположить также, как
        # Water Bubble (Large)?"; from 2026-11-04 such a card stood under the icon with a line from it).

        def aug_role(it, i, cls):
            return aug_class(it, cls + (' ability-box-tagged' if tagged[i] else ''))

        out_lis = []
        for i, (it, role) in enumerate(zip(items, roles)):
            if role is None:
                out_lis.append(it.group(0))
            elif role == 'solo':
                out_lis.append(aug_role(it, i, 'ability-row-solo'))
            elif role == 'start':
                out_lis.append(aug_role(it, i, 'ability-row-start'))
            elif role == 'cont':
                out_lis.append(aug_role(it, i, 'ability-row-cont'))
            elif role == 'cont-end':
                out_lis.append(aug_role(it, i, 'ability-row-cont ability-row-end'))

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


# Rows' tags as small tiles with an icon where the tags stood (owner 2026-11-06, mock "Плитка 22x18"; the bookmarks on
# the panel's left line before them are gone) — the pages it runs on; None = every page. CSS src/css/patch-tag-marks.css
TAG_MARK_PAGES = None   # every page (owner 2026-11-07: "Плитки тегов на все патчи разворачивай"; trial was 7.41f + 7.38)

# tiles in a GENERAL block's icon; more stats changed: the General icon as before (owner 2026-11-06: "Если изменённых
# характеристик >4 (не =4), то ставим иконку General как раньше стояла. Если <=4, то показываем те 4")
MOSAIC_MAX = 4
_LI_TEXT_RE = re.compile(r'<li\b[^>]*>(.*?)</li>', re.S)


def _row_stat(li_html):
    """The stat a GENERAL row changes ("other" for a row naming none, or only mentioning one: "model size")."""
    text = re.sub(r'<[^>]+>', ' ', re.sub(r'<span class="info-pop">.*?</span>', '', li_html, flags=re.S)).lower()
    if any(skip in text for skip in _STAT_DETECT_SKIP_PHRASES):
        return "other"
    return next((key for key, phrases in STAT_DETECT_RULES if any(p in text for p in phrases)), "other")


def _stat_mosaic(stats, other_src):
    """Variant C (owner 2026-11-06): the stats' own icons whole and small in the 48px square, two to four of them."""
    # each icon in a cell of its own, the cells parted by lines (owner 2026-11-06: "слишком мелкие значки внутри, а
    # также не хватает разделителей между ними")
    tiles = "".join(f'<span class="sm-cell"><img src="{STAT_ICONS.get(s, other_src)}" alt="" loading="lazy"></span>'
                    for s in stats)
    return f'<div class="ability-icon-img stat-mosaic n{len(stats)}" role="img" aria-label="{", ".join(stats)}">{tiles}</div>'


def _swap_single_row_other_icons(html):
    """A hero's GENERAL block shows the icons of the stats its rows change: one stat -> its icon (rows naming another
    thing too add the generic one), two or more -> those icons small in one square (owner 2026-11-06, 7.41 Arc Warden:
    movement speed, strength, agility). Rows only mentioning a stat (_STAT_DETECT_SKIP_PHRASES) count as "other"."""
    def repl(m):
        head, src, mid, ul_inner, ul_close = m.groups()
        stats = []
        for li in _LI_TEXT_RE.findall(ul_inner):
            stat = _row_stat(li)
            if stat not in stats:
                stats.append(stat)
        known = [s for s in stats if s != "other"]
        if not known:
            return m.group(0)
        if len(stats) == 1:
            return head + STAT_ICONS[known[0]] + mid + ul_inner + ul_close
        if len(stats) > MOSAIC_MAX:
            return m.group(0)        # more than four: the General icon, as before (owner 2026-11-06)
        img_start = head.rfind("<img")
        img_end = mid.index(">") + 1
        return (head[:img_start] + _stat_mosaic(stats, src) + mid[img_end:] + ul_inner + ul_close)
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
    if li_html.startswith('<li') and 'terrain-row' in li_html[:200]:
        return 8          # terrain rows show a Show button, not a tag: they keep Valve's order (2026-10-03)
    m = re.search(r'<span class="badge (buff-text|nerf-text|rework|swap|misc|qol|new|del)"', li_html)
    if m:
        kind = m.group(1)
        return {
            'new': 1, 'rework': 2, 'swap': 2,
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


_IABCARD_RE = re.compile(r'<!--IABCARD:.*?-->')


def drop_cards_hiding_nothing(html):
    """An item's abilities card whose item rows all stay shown repeats them: no card (owner 2026-11-07, 7.38 Bloodthorn:
    "излишне тут карточки, т.к предмет особо не менялся" — one True Strike line with its note, and a QoL row)."""
    def keep(m):
        nxt = html.find('<div class="entity-block', m.end())
        block = html[m.end():len(html) if nxt < 0 else nxt]
        return m.group(0) if "iab-covered" in block or "<li" not in block else ""
    return _IABCARD_RE.sub(keep, html)


def _story_rank(li_html):
    """A unit's numbers and a mech_story open their list, before the rows of every tag (owner 2026-11-07, 7.38 Roshan:
    "Now has +25% base Slow Resistance" stood above the REWORK story, "должна быть там, где и другие")."""
    head = li_html[:li_html.index(">")]
    if 'class="unit-sheet"' in head or " mech-story" in head:
        return 0.5        # 0 would read as "no rank" in the sort's `or`
    return None


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
        ranked = sorted(enumerate(lis), key=lambda iv: (_story_rank(iv[1]) or _li_rank(iv[1]), iv[0]))
        ordered = [li for _, li in ranked]
        return open_tag + prefix + ''.join(ordered) + suffix + close_tag
    return _CHANGES_UL_RE.sub(repl, html)


def _categories_bar_html():
    """Render the Categories filter buttons for the currently-accumulated patch."""
    if not _State.current_sections:
        return ''
    btns = []
    for s in _State.current_sections:
        # words only (owner 2026-11-07: "иконки у категорий категорически не нужны")
        btns.append(
            f'<button class="cat-filter-btn" data-category="{s["slug"]}" type="button">'
            f'<span class="fp-word">{s["label"]}</span></button>'
        )
    return ''.join(btns)


_THUMB_RE = re.compile(r'src="\.\./icons/(heroes|items|abilities)/([^"?/]+)\.png"')
_THUMB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons", "_t")


def _thumb_srcs(html):
    """Point hero / item / ability icons at their small WebP copy (icons/_t/<dir>/<name>.webp,
    made by tools/make_thumbs.py) when one exists; otherwise keep the PNG."""
    def repl(m):
        if os.path.exists(os.path.join(_THUMB_DIR, m.group(1), m.group(2) + ".webp")):
            return f'src="../icons/_t/{m.group(1)}/{m.group(2)}.webp"'
        return m.group(0)
    return _THUMB_RE.sub(repl, html)


_NEWMECH_UL_RE = re.compile(r'<ul class="changes"><!--NEWMECH(?::(\w+))?(:all)?-->(.*?)</ul>', re.S)
# any row's chip, for a block drawn as one box (the row's data-tag stays)
_ANY_CHIP_RE = re.compile(r'(<li\b[^>]*>)<span class="badge [\w-]+"[^>]*>[^<]*</span>')
_NEW_CHIP_RE = re.compile(r'(<li\b[^>]*data-tag="[^"]*\bnew\b[^"]*"[^>]*>)<span class="badge new"[^>]*>NEW</span>')


def _mech_chip_re(tag):
    return re.compile(rf'(<li\b[^>]*data-tag="[^"]*\b{tag}\b[^"]*"[^>]*>)<span class="badge {tag}"[^>]*>{tag.upper()}</span>')


def _new_mech_rows(html):
    """Lists under a "new mechanic" header (plain_header/subgroup/unit_header new=…) describe how
    the thing works — prose, not a changelog. Rows of the block's tag (NEW; REWORK under a
    "Reworked …" label) become one description box at the top of the list: no chip, no bullet
    (classes mech-desc / mech-first / mech-last); data-tag stays for the filters and dynamics.
    Rows with other tags stay normal change rows below it."""
    def fix(m):
        one_box = bool(m.group(2))
        chip_re = _ANY_CHIP_RE if one_box else _mech_chip_re(m.group(1) or "new")
        body = m.group(3)
        items = list(_LI_RE.finditer(body))
        # a covered row is hidden (mech_story retells it): it opens and closes no box
        box_idx = [i for i, it in enumerate(items) if (one_box or chip_re.match(it.group(0)))
                   and "iab-covered" not in it.group(0)[:it.group(0).index(">")]]
        # a mech_story before the box rows (or with none) leads the list, whatever the sort by tag did
        lead = [i for i, it in enumerate(items) if ' mech-story' in it.group(0)[:it.group(0).index(">")]
                and (not box_idx or i < box_idx[0])]
        if not box_idx and not lead:
            return '<ul class="changes">' + body + '</ul>'
        box, rest, last = [], [], 0
        for i in lead:
            box.append(items[i].group(0))
            rest.append(body[last:items[i].start()])
            last = items[i].end()
        # a row with its table (7.38 Lifesteal, 7.40 Cyclone cases) is a box of its own, apart from the rows around
        # it (owner 2026-10-28: "в отдельном блоке, с отступом от предыдущего") — unless the block is one box
        # (subgroup(one_box=True): 7.41 Reflected Damage, its sources' table under the last line)
        # … a table its row's words lead (7.37 Breakability, mech-captioned) is a box of its own even then: 10px apart,
        # as the tables of 7.38–7.41 (owner 2026-10-30: "посмотри как в других патчах похожие категории строятся")
        tabled = ({i for i in box_idx if 'mech-captioned' in items[i].group(0)} if one_box
                  else {i for i in box_idx if 'class="mech-abils' in items[i].group(0)})
        for n, i in enumerate(box_idx):
            first = n == 0 or i in tabled or box_idx[n - 1] in tabled
            end = n == len(box_idx) - 1 or i in tabled or box_idx[n + 1] in tabled
            it = items[i]
            cls = "mech-desc" + (" mech-first" if first else "") + (" mech-last" if end else "")
            li = chip_re.sub(r'\1<span class="row-tag-empty"></span>', it.group(0), count=1)
            li = (re.sub(r'class="([^"]*)"', lambda mm: f'class="{mm.group(1)} {cls}"', li, count=1)
                  if re.match(r'<li\b[^>]*\bclass="', li) else li.replace('<li', f'<li class="{cls}"', 1))
            box.append(li)
            rest.append(body[last:it.start()])
            last = it.end()
        rest.append(body[last:])
        if one_box and len(box) > 1 and not tabled:      # led tables stay boxes of their own (7.37)
            box = [_one_paragraph(box)]
        return '<ul class="changes">' + "".join(box) + "".join(rest) + '</ul>'
    return _NEWMECH_UL_RE.sub(fix, html)


_ROW_TEXT_RE = re.compile(r'^(<li\b[^>]*>)(.*?)<span class="row-text">(.*)</span></li>$', re.S)
_TABLE_START_RE = re.compile(r'<span class="mech-(?:abils|pair)\b')


def _one_paragraph(lis):
    """A one_box block's rows as one paragraph, the sentences one after another with a full stop (owner 2026-10-28,
    7.41 Reflected Damage: "не по одной строчке, а через точку в одну строку"); their tables after it, the row's
    data-tag the union of theirs (each tag's filter still finds it)."""
    parts, tables, tags, head = [], "", [], None
    for li in lis:
        m = _ROW_TEXT_RE.match(li)
        if not m:
            return "".join(lis)                       # a row of another shape: leave the lines as they are
        open_tag, lead, inner = m.groups()
        head = head or (open_tag, lead)
        t = _TABLE_START_RE.search(inner)
        text, table = (inner[:t.start()], inner[t.start():]) if t else (inner, "")
        text = text.rstrip()
        if text:
            parts.append(text)
        tables += table
        tag = re.search(r'data-tag="([^"]*)"', open_tag)
        tags += [x for x in (tag.group(1).split() if tag else []) if x not in tags]
    open_tag, lead = head
    open_tag = re.sub(r'data-tag="[^"]*"', f'data-tag="{" ".join(tags)}"', open_tag, count=1)
    open_tag = re.sub(r'\bmech-desc[^"]*', "mech-desc mech-first mech-last", open_tag, count=1)
    # a full stop between the sentences; the last one ends as every row of the site does, without one
    text = " ".join(p if _plain_end(p).endswith((".", "!", "?", ":")) or n == len(parts) - 1 else p + "."
                    for n, p in enumerate(parts))
    return f'{open_tag}{lead}<span class="row-text">{text}{tables}</span></li>'


def _plain_end(html_text):
    return re.sub(r"<[^>]+>", "", re.sub(r"<!--TIP-->.*?<!--/TIP-->", "", html_text, flags=re.S)).rstrip()


def save_html(filename):
    """Write current accumulator to ./{filename} and reset state."""
    out = "\n".join(H)
    out = out.replace('<!--CATEGORIES_BAR-->', _categories_bar_html())
    out = _swap_single_row_other_icons(out)
    out = _sort_changes_li(out)
    out = _wrap_ability_boxes(out)
    out = _new_mech_rows(out)
    # Talent tree with the changed twigs in gold (patch/talent_tree.py)
    out = light_talent_trees(out, os.path.splitext(os.path.basename(filename))[0])
    # Perf: :has() facts as build-time classes (patch/static_has.py)
    out = add_static_has_classes(out)
    # Perf: 2x-size WebP icons instead of the full PNGs (tools/make_thumbs.py)
    out = _thumb_srcs(out)
    # Safety net: any inline_note (i)-tip sentinel that wasn't lifted into a
    # row by li() (e.g. used outside an `extra=`) ships without its markers —
    # the (i) bubble still renders in place; only the comments are stripped.
    # (?) notes of hidden duplicate item-ability rows, moved into the abilities card (elements._IAB_NOTES)
    from .cards_item_abilities import raise_abilities_beside_gone_stats, _IAB_NOTES, render_iab_card, resolve_chip_marks
    from .cards_item_stats import render_cost_card
    from .cards_hero_stats import render_hs_card
    out = resolve_chip_marks(out)          # ability card headers: colour only what a row under the card names
    from .elements import mark_number_highlights
    out = mark_number_highlights(out)      # a highlighted number: text colour + dotted, not a strip (2026-10-25)
    out = re.sub(r'<!--HSCARD:(.*?)-->', lambda m: render_hs_card(m.group(1)), out)
    from .general_rows import attr_row_first
    out = attr_row_first(out)              # a new main attribute first in General, over the stats card's rows (11-06)
    out = re.sub(r'<!--COSTCARD:(.*?)-->', lambda m: render_cost_card(m.group(1)), out)
    out = drop_cards_hiding_nothing(out)
    out = re.sub(r'<!--IABCARD:(.*?)-->', lambda m: render_iab_card(m.group(1)), out)
    out = raise_abilities_beside_gone_stats(out)
    from .value_tables import value_tables
    out = value_tables(out)                # a card's values as a table (owner 2026-11-05)
    from .card_pairs import pair_new_cards, single_cards_right
    _stem = os.path.splitext(os.path.basename(filename))[0]
    from .card_sections import card_sections, drop_upgrade_rows_said_below, hide_rows_the_aghs_card_says
    out = hide_rows_the_aghs_card_says(out)   # an Aghanim's row its old -> new card shows already (2026-11-06)
    out = drop_upgrade_rows_said_below(out)   # a card's upgrade row the Aghanim's card below shows (2026-11-06)
    out = card_sections(out, _stem)        # rows led by an ability's icon: lines between, a head each (2026-11-06)
    out = pair_new_cards(out, _stem)       # two new cards side by side (2026-11-06)
    from .card_pairs import pair_replaced_facets
    out = pair_replaced_facets(out, _stem)  # a lost facet left, the new one with its card right (2026-11-06)
    out = single_cards_right(out, _stem)   # a lone one to the right of its block, a line to it (2026-11-06)
    if TAG_MARK_PAGES is None or _stem in TAG_MARK_PAGES:
        from .tag_marks import terrain_rows_tagged
        out = terrain_rows_tagged(out)     # a terrain row: its tag as a tile, no number
        out = out.replace('<body class="patch-page">', '<body class="patch-page tag-marks">', 1)
    out = re.sub(r'<!--IABNOTE:(.*?)-->', lambda m: _IAB_NOTES.get(m.group(1), ''), out)
    out = out.replace('<!--INLINETIP-->', '').replace('<!--/INLINETIP-->', '')
    out = out.replace('<!--TIP-->', '').replace('<!--/TIP-->', '')
    # Perf: let the browser decode images off the main thread (smoother render
    # on icon-heavy pages — 600+ icons). Safe + universal; no visual change. An <img> that already says
    # decoding= keeps its own (terrain micro-screenshots had it twice, 2026-10-03).
    out = re.sub(r'<img (?![^>]*\bdecoding=)', '<img decoding="async" ', out)
    path = os.path.join(_site.DIST_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"  → dist/{filename}: {len(out):,} bytes")
    H.clear()
    reset_page_state()                 # nothing of this page reaches the next one (audit 2026-10-26)
