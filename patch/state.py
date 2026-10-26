"""Global build state singleton."""


class _State:
    block_open = False
    # not None inside a terrain block (plain_header(terrain_link=…)): its rows are numbered in their category instead
    # of tagged (2026-10-03)
    terrain_rows = None
    terrain_anchor = False           # the page's first terrain block got id="terrain" (the Terrain page links to it)
    current_hero = None  # internal slug of current hero block (for ability icon derivation)
    current_hero_title = None   # hero_header()'s own text: talent_marks groups a hero's talent swaps by it
    ability_icons = set()  # all ability-icon URLs emitted during build (for icon-validator)
    ability_block_open = False  # tracks <div class="ability-block"> wrapper
    current_block_is_facet = False  # True when ability_block_open was set by facet_header()
    facet_block_had_ul = False      # True once ul_open() was called inside a facet block
    # Auto-categorize hero block contents (Stats / Abilities / Talents subgroups):
    next_ul_is_hero_stats = False    # set by hero_header()/unit_header(), consumed by ul_open()
    current_unit = None              # display name of the current unit_header() block
                                     # (units have no HERO_SLUG, but their base-stat
                                     # ul must still get the GENERAL block)
    in_stats_ul = False              # True while inside the auto-"STATS" ul (sanity-check facet/innate rows)
    current_ability_slug = None      # engine slug of the ability() block a row sits in (weights context)
    current_ability_innate = False   # that block is an innate
    current_ability_kv = None        # that block's ability for its game-file values (slug, or its icon's file name)
    aghs_cards = []                  # old -> new Aghanim's upgrade cards of the open ul (li queues, ul_close draws)
    card_meta = {}                 # {header key: (old, new)} the ability_change card above coloured; ul_close clears
    card_innate = None             # the ability_change card above shows this innate (its rows' "X is now innate")
    aghs_part_slug = None          # the open ability block's slug: its "whole old upgrade" card is still to draw
    section_panel_open = False       # True while inside a <section class="cat-panel"> wrapper
    seen_abilities_subgroup = False  # set when first ability() emits "Abilities" subgroup
    seen_facets_subgroup = False     # set when first facet_header() emits "Facets" subgroup
    new_mech_header = False          # plain_header(new=…): the whole block is a new mechanic
    new_mech = False                 # current ul lists a new mechanic → its NEW rows lose the chip
    new_mech_tag = "new"             # rows of this tag form the description box ("rework" for a Reworked … label)
    current_sections = []            # per-patch list of {slug, label}; reset in save_html()
    current_section_slug = None      # slug of the active section(); "general" suppresses dyn-cells
    # Patch-dynamics widget: tag tallies per (entity, patch). Populated by
    # headers (set current entity key) + li() (increment tag count). Dumped
    # as _dynamics.json at end of build for the JS widget to consume.
    current_patch_version = None     # set by write_head()
    current_entity_key = None        # "<kind>|<slug>" — set by hero/item/unit/plain_header
    current_entity_display = None    # human name for hover tooltip
    dynamics = {}                    # {entity_key: {"name":..., "kind":..., "patches":{ver:{tag:count}}}}
    dyn_skip_li = False              # set by _open_block when block is .is-new —
                                     # whole entity is conceptually a single NEW
                                     # tally; per-li tags inside are stat/property
                                     # rows that shouldn't inflate the dynamics.
    pending_cost_panel = None        # an item's components panel total A -> B, scored at the end
    pending_rework = None            # an item's unscored REWORK rows, scored at the end (signal R)
    damage_rows = None               # hero damage rows of the block: base / L1 / gain / L30 (no double count)
    iab_card = None                  # the item abilities card of the current block (hides duplicate rows)
    cost_card = None                 # the item components card of the current block (hides its cost rows)
    hs_card = None                   # the hero attributes card of the current block (hides its attribute rows)
    cell_rows = None                 # a hero block's NEW / DEL / REWORK rows: replacements, moves (weights)
                                     # of the block unless an li() row states the cost itself


state = _State()


# ---- One reset for the whole build state (audit 2026-10-26) ----
# A patch page leaves nothing for the next one: every _State field goes back to its default and every per-page cache
# of the card code (registered with page_cache) is emptied. Only the build's totals stay — the patch-dynamics tallies
# and the icon list rosters.py dumps after the last page. Tests reset those too.
def _copy(value):
    return type(value)(value) if isinstance(value, (list, dict, set)) else value


_BUILD_TOTALS = ("dynamics", "ability_icons")
_DEFAULTS = {k: _copy(v) for k, v in vars(_State).items() if not k.startswith("__")}
_PAGE_CACHES = []                # [(container, its starting contents)]


def page_cache(container):
    """Register a module-level dict / set / list that holds one page's cards: reset_page_state empties it."""
    _PAGE_CACHES.append((container, _copy(container)))
    return container


def _refill(container, start):
    """Back to `start` in place: modules keep their reference to the container."""
    container.clear()
    if isinstance(container, list):
        container.extend(start)
    else:
        container.update(start)


def reset_page_state():
    """After a page is written (page.save_html): defaults everywhere except the build's totals."""
    state.__dict__.clear()                       # instance attributes would hide the class ones
    for key, default in _DEFAULTS.items():
        if key in _BUILD_TOTALS:
            continue
        cur = getattr(_State, key)
        if isinstance(cur, (list, dict, set)) and type(cur) is type(default):
            _refill(cur, default)
        else:
            setattr(_State, key, _copy(default))
    for container, start in _PAGE_CACHES:
        _refill(container, start)


def reset_build_state():
    """Everything, the build's totals too (tests: no test sees another one's state)."""
    reset_page_state()
    for key in _BUILD_TOTALS:
        getattr(_State, key).clear()
