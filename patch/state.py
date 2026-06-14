"""Global build state singleton."""


class _State:
    block_open = False
    current_hero = None  # internal slug of current hero block (for ability icon derivation)
    ability_icons = set()  # all ability-icon URLs emitted during build (for icon-validator)
    ability_block_open = False  # tracks <div class="ability-block"> wrapper
    # Auto-categorize hero block contents (Stats / Abilities / Talents subgroups):
    next_ul_is_hero_stats = False    # set by hero_header(), consumed by ul_open()
    in_stats_ul = False              # True while inside the auto-"STATS" ul (sanity-check facet/innate rows)
    section_panel_open = False       # True while inside a <section class="cat-panel"> wrapper
    seen_abilities_subgroup = False  # set when first ability() emits "Abilities" subgroup
    seen_facets_subgroup = False     # set when first facet_header() emits "Facets" subgroup
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


state = _State()
