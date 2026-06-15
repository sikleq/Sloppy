"""Page-level writers: write_head, write_footer, save_html, save_assets, and post-processing helpers."""

import os
import re
import html as _html

import site_common as _site

from .output import H, W, reset_output, get_output
from .state import _State
from .meta import PATCHES, _render_top_nav, _patch_age_line, _patch_meta_parts, _dropdown_options_html
from .images import HERO_SLUG
from .elements import _close_block, STAT_ICONS, STAT_DETECT_RULES

_ASSET_VERSION = _site.compute_asset_version()


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
    parts = [f'<span class="ti-released"><span data-i18n="patch.released">Released:</span> <b>{date}</b></span>']
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
<a class="nav-back-arrow" href="../calendar.html" aria-label="Back to calendar" title="Back to calendar" data-i18n-aria-label="patch.back_calendar" data-i18n-title="patch.back_calendar"></a>
<div class="toolbar">
  <div class="toolbar-inner">
    <div class="legend-stack">
      <div class="legend-tags">
        <strong data-i18n="patch.tags_label">Tags:</strong>
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
      <input type="text" id="entity-search" placeholder="Search heroes, items, abilities…" data-i18n-placeholder="patch.search_ph" autocomplete="off" spellcheck="false">
      <div class="search-results" id="search-results"></div>
    </div>
    {patch_info_html}
  </div>
</div>
<div class="container">
''')


def write_footer():
    """Render close-block + back-to-top button + script tag + closing tags."""
    W(_close_block())
    if _State.section_panel_open:
        W('</section>')
        _State.section_panel_open = False
    W('<button class="back-to-top" aria-label="Back to top" title="Back to top" data-i18n-aria-label="ui.back_to_top" data-i18n-title="ui.back_to_top" onclick="window.scrollTo({top:0, behavior:\'smooth\'})"></button>')
    W(f'<script src="../src/scripts.js?v={_ASSET_VERSION}"></script>')
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
    from .patch_i18n import ru_for_header as _ru_hdr
    btns = []
    for s in _State.current_sections:
        _ru = _ru_hdr(s["label"])
        ru_attr = f' data-i18n-ru="{_html.escape(_ru, quote=True)}"' if _ru else ""
        btns.append(
            f'<button class="badge cat-filter-btn" data-category="{s["slug"]}"{ru_attr}>'
            f'{s["label"]}</button>'
        )
    return '<strong data-i18n="patch.group_label">Group:</strong>' + ''.join(btns)


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
