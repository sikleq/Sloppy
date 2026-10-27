"""Ability replacement / rework blocks: aghs_line(), game_ability_desc() / game_ability_pair(), new_ability() and ability_change(), the two-pane old / new card. Split out of patch/elements.py (audit 2026-10-26 #8)."""

import html as _html
import re

from .images import ABIL_CDN, _LOCAL_ABIL_ICONS
from .state import _State
from .elements import (INNATE_ICON_URL, MISSING_ICON_URL, _close_ability_block, _dyn_record_card, _pair_number_tips,
                       inline_note)
from .cards_item_abilities import _CARD_SEQ, _iab_meta_marks, _pane_parts, _pane_props, _pane_values
from .cards_aghs import _GRANTED_CARDS, _aghs_inline, _granted_flag, _rework_diff_html, _shares_level


_AC_AGHS_RE = re.compile(r"^(?:(?:Active|Passive)\s*)?\(Aghanim's (Scepter|Shard) upgrade\)\.?\s*"
                         r"|^Granted by Aghanim's (Scepter|Shard)\.\s*")


def _take_aghs(spec):
    """A card whose text opens with "Active (Aghanim's Scepter upgrade)." / "Granted by Aghanim's Scepter.": the
    words leave the text (the head shows Active / Passive) and the card's summary row says it with the Aghanim
    stripe instead (owner 2026-10-21, Clockwerk 7.41 Overclocking). -> (spec, "scepter" / "shard" / None)."""
    desc = list((spec or {}).get("desc") or [])
    if not desc or not isinstance(desc[0], str):
        return spec, None
    m = _AC_AGHS_RE.match(desc[0])
    if not m:
        return spec, None
    rest = desc[0][m.end():]
    desc = ([rest] if rest.strip() else []) + desc[1:]
    return dict(spec, desc=desc), (m.group(1) or m.group(2)).lower()


def game_ability_desc(slug, version=None, note=None):
    """A card side's desc from the game files: the ability's own text and the numbers the game lists under it, one
    line (patch/aghs_text.ability_text); note: a (?) after it. Never empty: no text stops the build."""
    from .aghs_text import ability_text
    version = version or _State.current_patch_version
    text = ability_text(slug, version)
    if not text:
        raise RuntimeError(f"{slug} ({version}): no description in the game files — teach patch/aghs_text.ability_text")
    line = _html.escape(_aghs_inline(text, loose=False), quote=False)
    shares = _shares_level(slug, version)
    return ([f"Shares level with {shares}."] if shares else []) + [line + (" " + inline_note(note) if note else "")]


def game_ability_pair(slug, version=None):
    """(old desc, new desc) of an ability_change from the game files of the patch before and this one: the texts with
    their changed numbers coloured (_rework_diff_html), and "Shares level with X." for the header (owner 2026-10-26,
    7.38 Demonic Cleanse "надо сделать old>new карточками"). Never empty: no text stops the build."""
    from .aghs_text import ability_text
    from .meta import _prev_patch_version
    version = version or _State.current_patch_version
    prev = _prev_patch_version(version)
    old_t, new_t = ability_text(slug, prev), ability_text(slug, version)
    if not old_t or not new_t:
        raise RuntimeError(f"{slug} ({version}): no {prev if not old_t else version} description — teach "
                           f"patch/aghs_text.ability_text")
    old_html, new_html = _rework_diff_html(_aghs_inline(old_t, loose=False), _aghs_inline(new_t, loose=False))
    side = lambda v, html: ([f"Shares level with {s}."] if (s := _shares_level(slug, v)) else []) + [html]
    return side(prev, old_html), side(version, new_html)


def new_ability(name, slug, note=None, innate=False):
    """A brand-new ability: the "New ability." card with its game text, as every new ability on the site (owner
    2026-10-25: «разве мы так оформляем появление новой способности?» — 7.41 Objurgation / Midnight Feast / Snakebite
    were rows). The patch-note row goes under it covered, for the weights and filters."""
    spec = {"name": name, "slug": slug, "desc": game_ability_desc(slug, note=note)}
    if innate:
        spec["innate"] = True
    return ability_change(None, spec, summary="New ability.", tag="new")


def ability_change(old, new, summary=None, tag=None, sub=False):
    new, _aghs_new = _take_aghs(new)
    old, _aghs_old = _take_aghs(old) if old is not None else (None, None)
    from .meta import _prev_patch_version
    # each side's header says "granted by Aghanim's X" (owner 2026-10-26): its text said so, or that patch's game flag
    _granted_by = {"new": _aghs_new or _granted_flag(new.get("slug"), _State.current_patch_version),
                   "old": (_aghs_old or _granted_flag(old.get("slug"), _prev_patch_version(_State.current_patch_version)))
                   if old else None}
    _aghs = _aghs_new or _aghs_old
    if not _aghs and new.get("slug"):
        # an ability the game grants by Aghanim's (KV IsGrantedByShard) gets the stripe without the words too
        # (owner 2026-10-22, Disruptor 7.41 Kinetic Fence)
        from .aghs_granted import kind_of
        _aghs = kind_of(new["slug"], _State.current_patch_version or "*") or None
    _State.current_ability_slug = new.get("slug")          # rows below belong to this ability
    _GRANTED_CARDS.add((_State.current_patch_version, new.get("slug")))   # this card shows its text already
    _State.card_innate = new.get("name") if new.get("innate") else None
    _State.current_ability_innate = bool(new.get("innate"))
    _card_ctx = {"ability": _State.current_ability_slug, "innate": _State.current_ability_innate,
                 "facet": False, "base_stat": False}
    if tag == 'new':
        _dyn_record_card({'new'}, **_card_ctx)
    elif tag == 'rework':
        _dyn_record_card({'rework'}, **_card_ctx)
    else:
        _dyn_record_card({'new', 'del', 'rework'}, **_card_ctx)
    out = _close_ability_block()
    _State.aghs_part_slug = (new.get("slug"), _State.current_hero)
    _State.next_ul_is_hero_stats = False
    if not sub and (_State.current_hero or _State.current_unit) and not _State.seen_abilities_subgroup:
        out += '<h4 class="subgroup">Abilities</h4>'
        _State.seen_abilities_subgroup = True

    def _resolve_icon(spec):
        icon_url = spec.get("icon_url")
        used_innate_fallback = False
        if not icon_url:
            slug = spec.get("slug")
            if slug and slug not in _LOCAL_ABIL_ICONS and spec.get("innate"):
                # a removed innate has no icon left in the game (14 of them: Aggrandize, Gift Bearer, Sight Seer…):
                # the fallback goes in directly, not as a 404 that onerror swaps (audit 2026-10-05)
                icon_url = INNATE_ICON_URL
                used_innate_fallback = True
            elif slug and slug not in _LOCAL_ABIL_ICONS:
                icon_url = MISSING_ICON_URL
            elif slug:
                icon_url = f"{ABIL_CDN}{slug}.png"
            elif spec.get("innate"):
                icon_url = INNATE_ICON_URL
                used_innate_fallback = True
            else:
                icon_url = MISSING_ICON_URL
        return icon_url, used_innate_fallback

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
        new_taller_inplace = in_place and (_new_rows > _old_rows)

    unified = (summary is not None) or (tag is not None) or single_new
    if not in_place and not unified and abs(_old_rows - _new_rows) >= 2:
        compact_side = 'old' if _old_rows < _new_rows else 'new'
    else:
        compact_side = None

    from .weights import _prev_version
    _pv = _State.current_patch_version
    _props = {"new": _pane_props(new, _pv), "old": _pane_props(old, _prev_version(_pv)) if old else None}
    # header values the pair changed are coloured, and the rows below that say exactly that change are hidden
    # (owner 2026-10-24: "всё в карточку"; li() reads card_meta, ul_close() clears it)
    _vals = {"new": _pane_values(new.get("desc", []), _props["new"]),
             "old": _pane_values(old.get("desc", []), _props["old"]) if old else {}}
    # only for the same ability on both sides: Tinker's Defense Matrix -> Deploy Turrets (7.41) are two abilities whose
    # headers differ, not a change; Lich's Sacrifice even kept Death Charge's slug
    _same = bool(old) and old.get("name") == new.get("name") and old.get("slug") == new.get("slug")
    _CARD_SEQ[0] += 1
    _card_id = _CARD_SEQ[0]
    _marks = {side: {k: (mark, _card_id) + ((_vals["old"][k],) if side == "new" else ()) for k, mark in m.items()}
              for side, m in zip(("old", "new"), _iab_meta_marks(_vals["old"], _vals["new"]))} if _same else {}
    _State.card_meta = {k: (_vals["old"][k], _vals["new"][k], _card_id) for k in _marks.get("new", {})}

    def _side(spec, kind):
        name = spec["name"]
        icon_url, used_innate_fallback = _resolve_icon(spec)
        innate_cls = ' is-innate' if spec.get("innate") else ''
        innate_marker = (
            f'<img src="{INNATE_ICON_URL}" alt="" '
            f'class="innate-marker">'
            if spec.get("innate") and not used_innate_fallback else ''
        )
        strip_html, desc_html = _pane_parts(spec.get("desc", []), _props[kind], marks=_marks.get(kind),
                                            granted=_granted_by[kind])
        tables_html = ''.join(
            f'<div class="formula-table-wrap">{tbl}</div>'
            for tbl in (spec.get("tables", []) or [])
        )
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
            f'{head_html}{strip_html}'
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

    if unified:
        _State.next_ul_is_hero_stats = False
        if not sub and (_State.current_hero or _State.current_unit) and not _State.seen_abilities_subgroup:
            out = ''
            out += '<h4 class="subgroup">Abilities</h4>'
            _State.seen_abilities_subgroup = True
        unified_icon = _new_icon
        is_innate = bool(new.get("innate"))
        old_is_innate = (not single_new) and bool(old.get("innate"))
        has_old_underlay = (not single_new) and (_old_icon != _new_icon)
        new_marker_html = (
            f'<img src="{INNATE_ICON_URL}" alt="" '
            f'class="innate-marker innate-marker-new">'
            if is_innate and _new_icon != INNATE_ICON_URL else ''
        )
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
        _new_slug = new.get("slug", "")
        _slug_attr = f' data-slug="{_new_slug}"' if _new_slug else ''
        icon_html = (
            f'<div class="{wrap_cls}">'
            f'{old_underlay_html}'
            f'<img src="{unified_icon}" alt="{new["name"]}" '
            f'class="ability-icon-img" loading="lazy" width="128" height="128"{_slug_attr} onerror="{on_err}">'
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
        tag_key = (tag or '').lower()
        if tag_key not in ('new', 'rework'):
            tag_key = 'new'
        tag_label = tag_key.upper()
        aghs_cls = f' class="aghanim-{_aghs}"' if _aghs else ''
        # "Ability reworked (Aghanim's Scepter upgrade)." — in brackets before the full stop (owner 2026-10-21)
        summary_txt = summary or ""
        if _aghs and _aghs in (_granted_by["new"], _granted_by["old"]):
            # the headers say "granted by Aghanim's X": the summary keeps only the stripe (owner 2026-10-26, 7.41
            # Kinetic Fence: "убрать (Aghanim's Shard upgrade) из строки")
            summary_txt += f'<span class="aghanim-marker {_aghs}"></span>'
        elif _aghs:
            body = summary_txt[:-1] if summary_txt.endswith(".") else summary_txt
            summary_txt = (f'{body} <span class="ac-aghs">(Aghanim\'s {_aghs.title()} upgrade)</span>.'
                           f'<span class="aghanim-marker {_aghs}"></span>')
        summary_row = (
            f'<ul class="changes ability-change-summary-ul">'
            f'<li data-tag="{tag_key}"{aghs_cls}>'
            f'<span class="badge {tag_key}" data-tag="{tag_key}">{tag_label}</span>'
            f'<span class="row-text">{summary_txt}</span>'
            f'</li>'
            f'</ul>'
        )
        _State.ability_block_open = True
        block_cls = 'ability-block ability-change-block'
        if is_innate:
            block_cls += ' is-innate'
        connector_html = '' if single_new else (
            '<svg class="ability-change-connector" '
            'viewBox="0 0 100 100" preserveAspectRatio="none" '
            'aria-hidden="true">'
            '<path d="" fill="none" '
            'stroke="rgba(150, 146, 137, 0.45)" stroke-width="1.3" '
            'stroke-dasharray="3 3" stroke-linecap="round" />'
            '</svg>'
        )
        if single_new:
            panes_html = (
                f'<div class="ability-change unified-panes is-single-new" '
                f'data-tag="new">'
                f'{_side(new, "new")}'
                f'</div>'
            )
        else:
            _old_html = _side(old, "old")
            _new_html = _side(new, "new")
            if _same:                           # the new numbers' % on hover, as the item cards' (2026-10-25)
                _new_html = _pair_number_tips(_old_html, _new_html)
            panes_html = (
                f'<div class="ability-change unified-panes{extra_cls}" '
                f'data-tag="new del rework">'
                f'{_old_html}'
                f'<span class="ability-change-arrow">→</span>'
                f'{_new_html}'
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

    _old_html = _side(old, "old")
    _new_html = _side(new, "new")
    if _same:
        _new_html = _pair_number_tips(_old_html, _new_html)
    return out + (
        f'<div class="ability-change{extra_cls}" data-tag="new del rework">'
        f'{_old_html}'
        f'<span class="ability-change-arrow">→</span>'
        f'{_new_html}'
        f'</div>'
    )
