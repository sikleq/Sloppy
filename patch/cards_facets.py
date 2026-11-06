"""Facet cards: a new facet (new_facet), a reworked one (facet_change) and their pane (_facet_pane). Cut out of
patch/elements.py (2026-11-06: it stood at its size limit); elements imports them back at its end."""
import re

from .elements import (  # noqa: E402
    ABIL_CDN,
    MISSING_ICON_URL,
    _SLIM_CACHE,
    _State,
    _close_ability_block,
    _dyn_record_card,
)
from .number_tips import _facet_attr_rows  # noqa: E402
from .cards_item_abilities import _pane_parts  # noqa: E402

def _facet_pane(desc, facet, version):
    """(head, rows) of a facet card pane. A text that says no kind ("Passive: …") gets the kind of the ability the
    facet changes (patch/ability_kv.facet_ability) — 7.39 Transference's card said no Passive (owner 2026-10-27).
    No single ability named for the facet in the files: no kind, as before."""
    from .ability_kv import ability_props, facet_ability
    from .aghs_text import ability_name
    abil = facet_ability(facet, version) if version else None
    if not abil:
        head, rows = _pane_parts(desc, facet=True)
        # no ability, no head: the facet itself is passive (owner 2026-11-06, 7.38 Undulation "опять нет шапки
        # passive"); rows led by abilities' icons get a head each instead (patch/card_sections.py)
        if not head and "acr-lead-chips" not in rows:
            return _pane_parts(desc, props={"kind": "Passive"}, facet=True)
        return head, rows
    # the header names the ability the facet changes, when the text doesn't (owner 2026-10-27, 7.39 Old Blood:
    # "Active" alone didn't say that it changes Bloodrage)
    hint = ability_name(abil, version)
    head, rows = _pane_parts(desc, facet=True, name_hint=hint)
    kind = ability_props(abil, version)["kind"] if 'class="iab-kind"' not in head else ""
    return _pane_parts(desc, props={"kind": kind}, facet=True, name_hint=hint) if kind else (head, rows)


_CARD_LINE = ('<svg class="ability-change-connector" viewBox="0 0 100 100" preserveAspectRatio="none" '
              'aria-hidden="true"><path d="" /></svg>')

def new_facet(slug, desc, summary=None, tag="new"):
    """New or reworked facet — renders like ability_change(old=None, tag=...) but with facet styling."""
    from .badges import FACETS, _FACET_COLOR_GRADIENT, facet_look
    tag_key = tag.lower() if tag else "new"
    _State.current_ability_slug = None
    _State.current_ability_innate = False
    _dyn_record_card({'new'} if tag_key == 'new' else {'rework'}, facet=True, base_stat=False)
    if slug not in FACETS:
        return f'<!-- new_facet: unknown slug {slug} -->'
    name, color, icon_name = facet_look(slug)
    # "X: Made exclusive to <this facet> Facet" in this facet's own card says what the card is (owner 2026-11-06, 7.38
    # Carny Classics: "повтор того, что выше Sets Dark Carnival Souvenirs to …")
    own = re.compile(rf"^[^:]{{1,40}}: Made exclusive to {re.escape(name)} Facet\.?$")
    desc = [d for d in desc if not (isinstance(d, str) and own.match(d))] if isinstance(desc, list) else desc
    gradient = _FACET_COLOR_GRADIENT.get(color, _FACET_COLOR_GRADIENT["Gray0"])
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if _State.current_hero and not _State.seen_facets_subgroup:
        out += '<h4 class="subgroup">Facets</h4>'
        _State.seen_facets_subgroup = True
    _State.ability_block_open = True
    _State.current_block_is_facet = False  # content already in panes — suppress ability() warning
    icon_overlay = (f'<img src="../icons/facets/{icon_name}.png" alt="" '
                    f'class="facet-icon-overlay" loading="lazy" width="72" height="72">') if icon_name else ''
    icon_html = (f'<div class="ability-icon-wrap facet-icon-wrap" '
                 f'style="background-image:{gradient}">{icon_overlay}</div>')
    desc, attr_rows = _facet_attr_rows(desc)
    head_html, desc_html = _facet_pane(desc, slug, _State.current_patch_version)
    default_summary = "New facet" if tag_key == "new" else "Reworked facet"
    summary_text = summary or default_summary
    tag_label = tag_key.upper()
    summary_row = (
        f'<ul class="changes ability-change-summary-ul">'
        f'<li data-tag="{tag_key}">'
        f'<span class="badge {tag_key}" data-tag="{tag_key}">{tag_label}</span>'
        f'<span class="row-text">{summary_text}</span>'
        f'</li>{attr_rows}'
        f'</ul>'
    )
    panes_html = (
        f'<div class="ability-change unified-panes is-single-new" data-tag="{tag_key}">'
        f'<div class="ability-change-pane ability-change-new">'
        f'{head_html}<div class="ability-change-body">{desc_html}</div>'
        f'</div>'
        f'</div>'
    )
    return out + (
        f'<div class="ability-block facet-block ability-change-block">'
        f'{icon_html}'
        f'{_CARD_LINE}'
        f'<h4 class="ability-title">{name}</h4>'
        f'{summary_row}'
        f'{panes_html}'
    )


def facet_change(slug, old_desc, new_desc, summary=None, old_ability=None, new_ability=None):
    """Reworked facet — old→new two-pane layout with facet gradient/icon styling.

    old_ability / new_ability: ability slug shown as a mini-header inside the respective pane.
    """
    from .badges import FACETS, _FACET_COLOR_GRADIENT
    from .images import _FACET_ICONS
    _State.current_ability_slug = None
    _State.current_ability_innate = False
    _dyn_record_card({'rework'}, facet=True, base_stat=False)
    if slug not in FACETS:
        return f'<!-- facet_change: unknown slug {slug} -->'
    name, color = FACETS[slug]
    gradient = _FACET_COLOR_GRADIENT.get(color, _FACET_COLOR_GRADIENT["Gray0"])
    fi = _FACET_ICONS.get(slug)
    icon_name = fi[1] if isinstance(fi, list) and len(fi) > 1 else None
    out = _close_ability_block()
    _State.next_ul_is_hero_stats = False
    if _State.current_hero and not _State.seen_facets_subgroup:
        out += '<h4 class="subgroup">Facets</h4>'
        _State.seen_facets_subgroup = True
    _State.ability_block_open = True
    _State.current_block_is_facet = False

    icon_overlay = (f'<img src="../icons/facets/{icon_name}.png" alt="" '
                    f'class="facet-icon-overlay" loading="lazy" width="72" height="72">') if icon_name else ''
    icon_html = (f'<div class="ability-icon-wrap facet-icon-wrap" '
                 f'style="background-image:{gradient}">{icon_overlay}</div>')

    from .meta import _prev_patch_version

    def _pane_body(desc, version, abil_slug):
        """The pane's strip names the ability ("Active: Tree Dance"): no icon + name block over it as well (owner
        2026-11-06: "зачем тут иконка способности и дублирующее tree dance"); a pane with no strip keeps that block."""
        head, rows = _facet_pane(desc, slug, version)
        top = "" if head else _ability_head(abil_slug)
        return f'{top}{head}<div class="ability-change-body">{rows}</div>'

    def _ability_head(abil_slug):
        if not abil_slug:
            return ''
        icon_url = f'{ABIL_CDN}{abil_slug}.png'
        on_err = f"this.onerror=null;this.src='{MISSING_ICON_URL}';"
        dname = _SLIM_CACHE.get(abil_slug, {}).get('dname', '') if _SLIM_CACHE else ''
        return (
            f'<div class="ability-change-head">'
            f'<div class="ability-change-icon-wrap">'
            f'<img class="ability-change-icon" src="{icon_url}" alt="{dname}" '
            f'loading="lazy" onerror="{on_err}">'
            f'</div>'
            f'<div class="ability-change-name">{dname}</div>'
            f'</div>'
        )

    summary_text = summary or "Facet reworked."
    old_desc, _ = _facet_attr_rows(old_desc)
    new_desc, attr_rows = _facet_attr_rows(new_desc)
    summary_row = (
        f'<ul class="changes ability-change-summary-ul">'
        f'<li data-tag="rework">'
        f'<span class="badge rework" data-tag="rework">REWORK</span>'
        f'<span class="row-text">{summary_text}</span>'
        f'</li>{attr_rows}'
        f'</ul>'
    )
    # two full panes, as every old -> new card: "is-in-place" shrank them to their text (owner 2026-11-06, 7.38 Nyx's
    # Burn Mana: "сама карточка ужатая")
    panes_html = (
        f'<div class="ability-change unified-panes" data-tag="new del rework">'
        f'<div class="ability-change-pane ability-change-old">'
        f'{_pane_body(old_desc, _prev_patch_version(_State.current_patch_version), old_ability)}'
        f'</div>'
        f'<span class="ability-change-arrow">→</span>'
        f'<div class="ability-change-pane ability-change-new">'
        f'{_pane_body(new_desc, _State.current_patch_version, new_ability)}'
        f'</div>'
        f'</div>'
    )
    return out + (
        f'<div class="ability-block facet-block ability-change-block">'
        f'{icon_html}'
        f'<h4 class="ability-title">{name}</h4>'
        f'{summary_row}'
        f'{_CARD_LINE}'
        f'{panes_html}'
    )
