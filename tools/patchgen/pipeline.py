"""generate(version): the order of every step, from the datafeed to the finished scaffold."""
from .data import ABILS, ABILS_SLIM, HEROES, ITEMS, _CANONICAL_SECTION_ORDER, _load_patchnotes_loc
from .entities import _render_hero, _render_item, _render_neutral_creep
from .general import _render_general_note
from .lines import _drop_empty_ul
from .normalize import fetch_datafeed
from .notes import _postprocess_group_rows_home, _postprocess_same_change_abilities
from .post_facets import _postprocess_removed_facet_groups, _postprocess_removed_facets
from .post_shared import _postprocess_shared_row_group
from .post_hero import _postprocess_attr_change_first, _postprocess_facets_summary_covered
from .post_cards import (
    _postprocess_card_stat_notes,
    _postprocess_drop_now_requires,
    _postprocess_hero_stat_card,
    _postprocess_recipe_cost_zero_net,
    _postprocess_rows_first,
    _postprocess_two_selves_cards,
    _postprocess_removed_label,
    _postprocess_silent_stats,
    _postprocess_stack_note_into_ability,
)
from .post_general import (
    _postprocess_before_after,
    _postprocess_boss_rows_home,
    _postprocess_mechanic_rules_row,
    _postprocess_merge_twin_rows,
    _postprocess_minute_formula,
    _postprocess_neutral_cast_notes,
    _postprocess_umbrella_stat_rows,
    _postprocess_lost_heal_cut_rows,
    _postprocess_same_change_rows,
    _postprocess_misc_topics,
    _postprocess_new_block_label,
    _postprocess_new_units,
    _postprocess_per_minute,
    _postprocess_switched_note,
    _postprocess_rework_continuation,
    _postprocess_courier_rows,
    _postprocess_example_icons,
    _postprocess_rune_rows,
    _postprocess_team_abilities,
    _postprocess_unit_possessive,
)
from .post_items import (
    _postprocess_boss_blocks,
    _postprocess_innate_rows_out_of_stats,
    _postprocess_new_item_card,
    _postprocess_rework_marker,
    _postprocess_unstated_total_cost,
)
from .post_late import (
    _merge_adjacent_lists,
    _merge_no_longer_innate,
    _postprocess_ability_level_formula,
    _postprocess_facet_improves_row,
    _postprocess_facets_first,
    _postprocess_innate_cards,
    _postprocess_innate_level0,
    _postprocess_mechanic_lists,
    _postprocess_new_facet_rows,
    _postprocess_new_innate_cards,
    _postprocess_returning_rows,
    _postprocess_roshan_block,
    _postprocess_row_notes,
    _postprocess_stance_blocks,
)
from .post_stats import (
    _postprocess_aghs_merge,
    _postprocess_cost_components,
    _postprocess_fold_damage_l1,
    _postprocess_properties_change,
    _postprocess_scale_pill,
)
from .rows import _HERO_SIDE

def _build_prev_hero_abils(version):
    """Load the previous patch's datafeed and return a per-hero ability snapshot.

    Returns {hero_id: {slug: {'dname': str, 'is_innate': bool}}} so that
    _render_hero() can diff current vs previous abilities and correctly route
    hero_notes with "AbilityName: ..." prefixes to the right ability() block.
    """
    from patch.meta import _prev_patch_version
    prev_ver = _prev_patch_version(version)
    if not prev_ver:
        return {}
    try:
        prev_d = fetch_datafeed(prev_ver)
    except Exception:
        return {}
    result = {}
    for hero in prev_d.get('heroes', []):
        hid = hero.get('hero_id')
        abils = {}
        for a in hero.get('abilities', []):
            aid = a.get('ability_id')
            resolved = ABILS.get(aid)
            if not resolved:
                continue
            aname, aslug = resolved
            abils[aslug] = {
                'dname': aname,
                'is_innate': ABILS_SLIM.get(aslug, {}).get('is_innate', False),
            }
        result[hid] = abils
    return result


def _postprocess_item_ability_cards(lines, version):
    """Owner 2026-09-27: an item whose ability changed gets its abilities before -> after card
    (item_abilities_change) from the game's tooltips of both patches. Needs the local tooltip history
    (the game-files store, patch/game_files.py via patch/loc_history.py); without it the pass is skipped."""
    try:
        from patch.item_ability_text import insert_cards
        from patch.weights import _prev_version
    except Exception as e:                                   # pragma: no cover — optional local data
        print(f"  [note] item ability cards skipped: {e}")
        return lines
    prev = _prev_version(version)
    if not prev:
        return lines
    name_to_slug = {n: s for n, s in ITEMS.values() if not str(s).startswith("enhancement_")}
    try:
        return insert_cards(lines, version, prev, name_to_slug)
    except Exception as e:                                   # pragma: no cover
        print(f"  [note] item ability cards skipped: {e}")
        return lines


def generate(version):
    d = fetch_datafeed(version)
    patchnotes_loc = _load_patchnotes_loc(version)
    prev_hero_abils = _build_prev_hero_abils(version)

    out = [f'# Auto-generated v2 scaffold for {version}',
           f'# Source: data/{version}_datafeed.json',
           '']

    # Determine section order: prefer patchnotes_english.txt (matches the
    # official patch page order); fall back to datafeed JSON key order.
    # patchnotes_english.txt groups items + neutral_items under 'items'.
    # We expand 'items' into ('items', 'neutral_items') so both sections are
    # emitted together in sequence.
    # Use the canonical section order. The official Dota 2 patch page ordering
    # cannot be reliably derived from the datafeed or patchnotes_english.txt —
    # after generation, reorder sections manually if needed.
    section_order = _CANONICAL_SECTION_ORDER

    _SECTION_KEYS = {
        'general_notes':  ('GENERAL UPDATES',        'General Updates'),
        'items':          ('ITEM UPDATES',            'Item Updates'),
        'neutral_creeps': ('NEUTRAL CREEP UPDATES',   'Neutral Creep Updates'),
        'neutral_items':  ('NEUTRAL ITEM UPDATES',    'Neutral Item Updates'),
        'heroes':         ('HERO UPDATES',            'Hero Updates'),
    }
    _first = True
    for key in section_order:
        if key not in _SECTION_KEYS or not d.get(key):
            continue
        cap_title, section_title = _SECTION_KEYS[key]
        prefix = '# =====' if _first else '\n# ====='
        out.append(f'{prefix} {cap_title} =====')
        out.append(f'W(section("{section_title}"))')
        _first = False
        if key == 'general_notes':
            for note in d['general_notes']:
                out.extend(_render_general_note(note))
        elif key == 'items':
            for item in d['items']:
                out.extend(_render_item(item, version))
        elif key == 'neutral_creeps':
            for creep in d['neutral_creeps']:
                out.extend(_render_neutral_creep(creep))
        elif key == 'neutral_items':
            for item in d['neutral_items']:
                out.extend(_render_item(item, version, neutral=True))
        elif key == 'heroes':
            _HERO_SIDE[0] = True               # every row below sits under a hero (see _emit_badge hero_side)
            try:
                for hero in sorted(d['heroes'], key=lambda h: HEROES.get(h['hero_id'], ('', ''))[0]):
                    out.extend(_render_hero(hero, version=version, patchnotes_loc=patchnotes_loc,
                                            prev_hero_abils=prev_hero_abils))
            finally:
                _HERO_SIDE[0] = False

    # Post-process passes that operate on the full emitted line list:
    # 1. Collapse aghs upgrade-row + description into canonical merged li.
    # 2. Auto-emit scale_pill(...) for per-level formula text.
    # 3. Drop a v2-todo breadcrumb above ability blocks tagged "reworked".
    out = _postprocess_aghs_merge(out)
    out = _postprocess_boss_blocks(out, version)
    out = _postprocess_boss_rows_home(out)            # "Roshan's X" in a flat list -> Roshan's card
    out = _postprocess_unit_possessive(out)           # "Tormentor's X" on its card -> "X"
    out = _postprocess_switched_note(out)             # "has switched" + "Now …" note -> one line
    out = _postprocess_rework_continuation(out)       # "This results in …" goes on the REWORK row above (11-06)
    out = _postprocess_per_minute(out)                # "… upgrade per minute …" -> minute table
    out = _postprocess_merge_twin_rows(out)
    out = _postprocess_same_change_rows(out)          # one change to 3+ abilities -> one row, their icons (11-07)
    out = _postprocess_new_units(out, version)        # a creep new in the game's files: its header and numbers
    out = _postprocess_neutral_cast_notes(out)        # "Neutrals will cast …" -> [?] of the ability (owner 11-07)
    out = _postprocess_umbrella_stat_rows(out)        # "+25% … Amplifications replaced with +20% HR" -> NERF (11-07)
    out = _postprocess_lost_heal_cut_rows(out)        # a healing cut turned into a 7.39 HR cut -> NERF (11-07)
    out = _postprocess_rune_rows(out)                 # a rune reads as an ability: icon, name, rows (owner 2026-11-04)
    out = _postprocess_example_icons(out)             # an example named in a row carries its icon (owner 2026-11-04)
    out = _postprocess_courier_rows(out)              # Courier rows -> the unit's own category (owner 2026-11-04)
    out = _postprocess_team_abilities(out)            # Glyph, Scan rows -> an ability's header (owner 2026-11-04)
    out = _postprocess_minute_formula(out)
    out = _postprocess_scale_pill(out)
    out = _postprocess_mechanic_rules_row(out)        # a row restating its header goes (owner 2026-10-27)
    out = _postprocess_misc_topics(out)               # rows on one topic -> a mechanic block (owner 2026-10-28)
    out = _postprocess_new_block_label(out)
    out = _postprocess_before_after(out)              # "now … instead of …" rows -> before / after table
    out = _postprocess_mechanic_rules_row(out, after_label=True)   # a reworked mechanic in one list
    out = _postprocess_new_item_card(out, version)
    out = _postprocess_cost_components(out, version)
    out = _postprocess_properties_change(out, version=version)
    out = _postprocess_silent_stats(out, version)
    out = _postprocess_card_stat_notes(out)
    out = _postprocess_hero_stat_card(out, version)   # approved by the owner 2026-09-28
    out = _postprocess_fold_damage_l1(out)            # "Damage at level 1" into the (?) — owner 2026-10-04
    out = _postprocess_unstated_total_cost(out)
    out = _postprocess_item_ability_cards(out, version)
    out = _postprocess_properties_change(out, with_abilities=True, version=version)   # an abilities card brings it
    out = _drop_empty_ul(out)
    out = _postprocess_innate_rows_out_of_stats(out)
    out = _postprocess_stack_note_into_ability(out)
    out = _postprocess_drop_now_requires(out)
    out = _postprocess_recipe_cost_zero_net(out)
    out = _postprocess_rework_marker(out)
    out = _postprocess_removed_label(out)             # "Neutral Item cycled out" label — owner 2026-10-17
    out = _postprocess_ability_level_formula(out, version)   # "+X with every level of Y" -> table (owner 2026-10-27)
    out = _postprocess_innate_cards(out, version)     # innate old -> new from the game's texts (owner 2026-10-27)
    out = _postprocess_new_innate_cards(out, version)  # "New innate ability" -> the hero's old innate -> new (7.37)
    out = _postprocess_new_facet_rows(out)             # a "New Facet" row -> the new facet card (7.37 Medusa)
    out = _merge_adjacent_lists(out)                   # ul_close + ul_open back to back -> one list (7.37 Chronosphere)
    out = _postprocess_innate_level0(out, version)     # a 7.36 innate's level-0 value out of the comparison (7.37)
    out = _postprocess_stance_blocks(out)              # "Earth Brawler …" rows -> stance blocks, as 7.40 (10-30)
    out = _merge_no_longer_innate(out)                 # "No longer an innate ability" leads its level-0 row (10-30)
    out = _postprocess_roshan_block(out)               # General rows about Roshan himself -> his block (owner 2026-10-30)
    out = _postprocess_row_notes(out)                  # facts a row needs that Valve left out (ROW_NOTES)
    out = _postprocess_returning_rows(out)             # a returning / new item's description rows are NEW (as 7.38)
    out = _postprocess_mechanic_lists(out)             # General subgroups of lists -> mechanic blocks, tables (10-30)
    out = _postprocess_removed_facets(out, version)   # "Removed X Facets" -> facet blocks (owner 2026-10-29)
    out = _postprocess_same_change_abilities(out)     # one block, stacked icons (owner 2026-10-30)
    out = _postprocess_shared_row_group(out)          # one row of 3+ abilities, all their icons (owner 2026-11-06)
    out = _postprocess_group_rows_home(out)           # a hero row about all of a block's abilities -> that block
    out = _postprocess_facet_improves_row(out)        # "Now is a facet that improves X" + "X: …" -> one row (owner)
    out = _postprocess_facets_first(out)              # a hero's facets, then his abilities (owner 2026-11-02)
    out = _postprocess_removed_facet_groups(out)      # lost facets side by side (owner 2026-11-05)
    out = _postprocess_two_selves_cards(out, version)  # Arc Warden's two selves -> old / new cards (owner 2026-11-05)
    out = _postprocess_rows_first(out)                # a card's plain rows above its caption (owner 2026-11-05)
    out = _postprocess_attr_change_first(out)         # a new main attribute first in General (owner 2026-11-06)
    out = _postprocess_facets_summary_covered(out)    # "Added three … facets" under the facet cards (owner 2026-11-06)

    # Close the page: footer + save. Emitted so the wrapped content/pXXX.py is
    # complete — without these the site build runs green but the patch HTML is
    # never written to dist/ (save_html is what flushes the page to disk). Match
    # the two trailing lines every content/p*.py ends with.
    out.append('')
    out.append('write_footer()')
    out.append(f"save_html('patches/{version}.html')")

    return '\n'.join(out)
