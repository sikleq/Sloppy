"""Badge and percentage-change helpers: b, br, bf, t, gradient_class, facet_badge, scale_pill."""

from .images import _FACET_ICONS


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


def b(old, new, l=False, slash=False, force_overall=None):
    """Generate per-level badges. old/new can be scalar or list.
    l=True means lower-is-buff (cooldowns, mana costs, penalties).
    slash=True separates the badges with " / " instead of ", " — use it for
    PAIRED dimensions (e.g. daytime / nighttime vision), not level progressions.
    If all per-level badges turn out identical, collapses to a single badge.
    Determines OVERALL buff/nerf tag by the MAX-RANK (last non-zero) per-level
    value's direction. Refinement: when max-rank is a SMALL nerf (<=12%) but the
    per-level deltas AVERAGE to a buff (early-level buffs outweigh an
    insignificant late dip), it flips to BUFF — so a front-loaded rescale like
    15/30/45/60->25/35/45/55 (+67/+17/0/-8) reads as a buff. The <=12% cap keeps
    "flattening" rescales (big max-rank nerf, e.g. Drow 4/8/12/16->10 =
    +150/+25/-17/-38) as a max-rank nerf, and the inverse case (early nerf, late
    buff — Disseminate) is already buff via max-rank. Pass force_overall=
    "buff"/"nerf" to override outright. Per-level % badges are never affected.

    Sign convention: the `+`/`-` reflects the RAW numeric direction
    (`+` when new > old, `-` when new < old). The badge COLOUR reflects
    player benefit (`l=True` flips green/red). So a cost going 600 -> 700
    renders as `+17%` red — sign matches the arithmetic, colour matches
    the impact on the player.
    """
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
        if n == o:
            parts.append('<span class="badge neutral">0%</span>')
            keys.append(("neutral", "0%"))
            signed_pcts.append(0)
            continue
        if o == 0:
            # Old value was 0 -> % delta is undefined. Show absolute change
            # as a numeric chip (+N / -N) so all levels are visually present.
            is_buff = (n < o) if l else (n > o)
            delta = n - o
            sign = '+' if delta > 0 else ''
            cls = 'buff' if is_buff else 'nerf'
            label = f'{sign}{delta:g}'
            parts.append(f'<span class="badge {cls}" data-overall="{cls}">{label}</span>')
            keys.append((cls, label))
            signed_pcts.append(1 if is_buff else -1)
            continue
        raw = (n - o) / o * 100
        pct = round(raw)
        # Tiny non-zero deltas (e.g. +252 -> +253 = +0.4%) round to 0 with
        # integer rounding but are still meaningful directional changes.
        # Show one-decimal precision so the buff/nerf direction surfaces.
        is_buff = (n < o) if l else (n > o)
        if pct == 0:
            # Sub-percent delta -> render as "+0.X%" / "-0.X%" with one-decimal
            # rounding (drops to integer-zero only when the raw value is
            # literally 0). Magnitude floored at 1 for gradient/tag purposes.
            small = round(abs(raw), 1)
            if small == 0:
                parts.append('<span class="badge neutral">0%</span>')
                keys.append(("neutral", "0%"))
                signed_pcts.append(0)
                continue
            # Sign follows the RAW numeric direction; colour (via gradient_class)
            # reflects player benefit. See docstring.
            sign = "+" if n > o else "-"
            display = f"{sign}{small}%"
            cls = gradient_class(1, is_buff)  # weakest gradient
            signed_pcts.append(small if is_buff else -small)
            parts.append(f'<span class="badge {cls}">{display}</span>')
            keys.append((cls, display))
            continue
        magnitude = abs(pct)
        signed_pcts.append(magnitude if is_buff else -magnitude)
        sign = "+" if n > o else "-"
        cls = gradient_class(magnitude, is_buff)
        display = f"{sign}{magnitude}%"
        parts.append(f'<span class="badge {cls}">{display}</span>')
        keys.append((cls, display))

    # Determine overall tag.
    # Rule: tag by the MAX-RANK (last) per-level value's direction — that's
    # the level the hero settles at once the ability is maxed, which the
    # player feels for most of the late game. Falls back to scanning
    # backwards if the max-rank delta is neutral.
    #
    # Counter-example that motivated this rule: Disseminate
    # 20/25/30/35% -> 16/24/32/40%. Per-level deltas: -20%, -4%, +7%, +14%.
    # Signed avg ~= -0.75% -> previously tagged NERF. But at L4 (max rank,
    # where the ability lives most of the game) it's 35->40 = +14% buff.
    # Max-rank-based tagging surfaces that correctly.
    #
    # Formula rows (li_formula / bf) intentionally keep their own avg-based
    # logic — they show explicit L1/L_end badges, so the overall tag's
    # role is different there.
    overall = ""
    max_rank = 0
    if signed_pcts:
        for v in reversed(signed_pcts):
            if v != 0:
                max_rank = v
                overall = "buff" if v > 0 else "nerf"
                break
        # Front-loaded rescale: max-rank is a SMALL nerf (<=12%) but the per-level
        # deltas AVERAGE to a buff — the early-level buffs outweigh an
        # insignificant late dip -> BUFF (Riki Blink Strike 15/30/45/60->25/35/45/55
        # = +67/+17/0/-8). Inverse case (early nerf, late buff — Disseminate) is
        # already buff via max-rank, untouched.
        if (overall == "nerf" and abs(max_rank) <= 12
                and sum(signed_pcts) / len(signed_pcts) > 0):
            overall = "buff"
        # Mirror case — BACK-loaded rescale: max-rank is a SMALL buff (<=12%)
        # but the per-level deltas AVERAGE to a nerf (early-level nerfs
        # outweigh an insignificant late gain) -> NERF. Kez Kazurai Katana
        # 5/7/9/11->3/6/9/12% (-40/-14/0/+9, avg -11.25%) reads as a nerf.
        # Disseminate (-20/-4/+7/+14, max +14 > 12) keeps its max-rank BUFF.
        if (overall == "buff" and abs(max_rank) <= 12
                and sum(signed_pcts) / len(signed_pcts) < 0):
            overall = "nerf"
        # "Flatten" rescale (X/Y/Z/W -> ONE flat value): level-scaling removed.
        # Classify by whether the flat value beats the old AVERAGE — ties (mean
        # unchanged) go to BUFF, since the early levels still rose even when the
        # average nets even (Drow Agility 4/8/12/16->10: mean 10=10, but L1/L2
        # jumped up). l=True flips the compare. Supersedes the max-rank tag for
        # flattens (the maxed level isn't the whole story when every other level
        # shifted the other way).
        if len(set(new)) == 1 and len(set(old)) > 1:
            old_mean = sum(old) / len(old)
            flat_v = new[0]
            better = (flat_v <= old_mean) if l else (flat_v >= old_mean)
            overall = "buff" if better else "nerf"
    # Per-row override: when the max-rank heuristic disagrees with the real
    # gameplay impact (e.g. a rescale that buffs early levels and only slightly
    # nerfs max rank), pass force_overall="buff"/"nerf" to set the left tag
    # + filter direction explicitly. Per-level % badges are unaffected.
    if force_overall is not None:
        overall = force_overall

    # Collapse if every level produced an identical badge
    if len(keys) > 1 and len(set(keys)) == 1:
        parts = [parts[0]]

    overall_attr = f' data-overall="{overall}"' if overall else ""
    grp_cls = "badge-group slash-sep" if slash else "badge-group"
    return f'<span class="{grp_cls}"{overall_attr}>' + "".join(parts) + "</span>"


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
    # Sign reflects raw arithmetic direction; colour (via gradient_class)
    # reflects player benefit. See b()'s docstring for the rationale.
    sign = "+" if new_v > old_v else "-"
    cls = gradient_class(magnitude, is_buff)
    return (cls, f"{sign}{magnitude}%", magnitude if is_buff else -magnitude,
            "buff" if is_buff else "nerf")


_formula_id_counter = [0]


def fold(text):
    """Wrap an OLD formula in a span with subtle dotted underline (visual reference only)."""
    return f'<span class="formula-old">{text}</span>'


def bf(old_fn, new_fn, formula_text, levels=None, l=False, value_fmt="{:g}",
       level_prefix='L', level_fmt=None, jump_at=20, headline_level=1,
       effective_unchanged=False, axis_label=None):
    """Formula-based change. Returns (trigger_html, badge_html, table_html).
    The trigger wraps formula_text as a clickable pill that toggles the table.
    Tag is determined by `headline_level` (default L1).
    levels: list of int levels to show; defaults to L1-15 + L20, L25, L30.
            Can also pass an int N -> range(1, N+1).
    value_fmt: format string for level values (e.g. '{:.2f}%' or '{:g}').
    level_prefix: prefix shown before each column header (default 'L').
                  Ignored when level_fmt is provided.
    level_fmt: optional callable(L) -> header label; lets the caller override
               the default 'L1', 'L2'... formatting (e.g. '1:00', '2:00').
    jump_at: level value that gets the visual gap class (default 20).

    The Delta% row is dropped automatically when every level resolves to the same
    delta — in that case the headline badge already conveys the full picture."""
    if levels is None:
        levels = list(range(1, 16)) + [20, 25, 30]
    elif isinstance(levels, int):
        levels = list(range(1, levels + 1))

    if level_fmt is None:
        level_fmt = str if axis_label else lambda L: f'{level_prefix}{L}'

    _formula_id_counter[0] += 1
    fid = f"f{_formula_id_counter[0]}"
    axis_th = '<th></th>'

    # Caller-declared reformulation: Valve's patch note explicitly states
    # "Effective values are not changed" (formula re-parametrized but the
    # final in-game values match across all relevant contexts). The raw
    # per-level Delta% would be misleading here — show a single-row "value"
    # table and an empty badge-group so the left REWORK tag carries the
    # row's meaning.
    if effective_unchanged:
        def _cls(L): return ' class="lvl-jump"' if (jump_at is not None and L == jump_at) else ''
        head_cells = "".join(f'<th{_cls(L)}>{level_fmt(L)}</th>' for L in levels)
        val_cells  = "".join(f'<td{_cls(L)}>{value_fmt.format(new_fn(L))}</td>' for L in levels)
        trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'
        badge   = '<span class="badge-group"></span>'
        table   = (f'<table class="formula-table" id="{fid}" hidden>'
                   f'<thead><tr>{axis_th}{head_cells}</tr></thead>'
                   f'<tbody><tr><th class="row-label-new">value</th>{val_cells}</tr></tbody>'
                   f'</table>')
        return trigger, badge, table

    # Headline-level inline badge (used when row is collapsed).
    # "start" always means L1 (the level the user thinks of as the beginning
    # of the game) — even if L1's delta is 0%. Do NOT shift to a later level
    # just because that level shows a more dramatic delta; the reader can see
    # the per-level breakdown by clicking the formula trigger.
    cls1, disp1, _, overall1 = _compute_pct(old_fn(headline_level), new_fn(headline_level), l)
    # Overall buff/nerf for the filter: average the SIGNED per-level
    # deltas across ALL levels (including 0% ones) — same convention as
    # `b()`. Per-level formulas like "2% -> 1.9% + 0.1% per level" can be
    # 0% at L1 but a clear buff later; the filter still surfaces them.
    signed_pcts = []
    for L in levels:
        ov, nv = old_fn(L), new_fn(L)
        if ov == nv or ov == 0:
            signed_pcts.append(0.0)
            continue
        pct = (nv - ov) / ov * 100
        if round(pct) == 0:
            signed_pcts.append(0.0)
            continue
        is_buff = (nv < ov) if l else (nv > ov)
        signed_pcts.append(abs(pct) if is_buff else -abs(pct))
    avg_signed = sum(signed_pcts) / len(signed_pcts) if signed_pcts else 0.0
    overall_eff = ('buff' if avg_signed > 0 else
                   'nerf' if avg_signed < 0 else
                   overall1)
    overall_attr = f' data-overall="{overall_eff}"' if overall_eff else ""
    # If the headline-level cell is 0% but the formula is a net buff/nerf
    # across other levels (e.g. "2% -> 1.9% + 0.1% per level" — flat at L1,
    # ramps up later), promote the rightmost level's delta to the headline
    # slot so the row shows a meaningful "+X%" instead of "0%". Embed a
    # `data-force-left="buff"|"nerf"` hint on the badge-group so li_formula
    # swaps its default REWORK left tag for a matching BUFF/NERF text tag.
    force_left_attr = ""
    # Per-level formula that visibly differs across levels — show TWO
    # badges (L1 = "start", last level = "end") so the reader sees both
    # the early-game and late-game impact at a glance. Falls back to a
    # single badge when start and end are identical (no per-level
    # variation worth surfacing).
    last_L = levels[-1]
    clsN, dispN, _, _ = _compute_pct(old_fn(last_L), new_fn(last_L), l)
    different_endpoints = (cls1, disp1) != (clsN, dispN)
    # Force start/end pair whenever the formula's per-level impact differs
    # across the table — either the endpoints themselves differ, OR they
    # both read 0% but the overall avg is non-neutral (mid-game levels
    # carry the change). In both cases the reader should see "L1 start /
    # last end" so the row visibly signals "this is a per-level formula".
    needs_pair = different_endpoints or (cls1 == "neutral" and overall_eff in ("buff", "nerf"))
    if needs_pair:
        badge_inner = (
            f'<span class="badge {cls1}">{disp1}</span>'
            f'<span class="formula-endpoint-label">start</span>'
            f'<span class="badge {clsN}">{dispN}</span>'
            f'<span class="formula-endpoint-label">end</span>'
        )
        # Left tag uses the overall avg direction (not L1's), so a row that
        # is a nerf at L1 but a buff at L30 still classifies by net trend.
        if overall_eff in ("buff", "nerf"):
            force_left_attr = f' data-force-left="{overall_eff}"'
    else:
        badge_inner = f'<span class="badge {cls1}">{disp1}</span>'
    badge = f'<span class="badge-group"{overall_attr}{force_left_attr}>{badge_inner}</span>'

    # Trigger
    trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'

    def cls_for(L):
        return ' class="lvl-jump"' if (jump_at is not None and L == jump_at) else ''

    head_cells = "".join(f'<th{cls_for(L)}>{level_fmt(L)}</th>' for L in levels)
    old_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(old_fn(L))}</td>' for L in levels)
    new_cells = "".join(f'<td{cls_for(L)}>{value_fmt.format(new_fn(L))}</td>' for L in levels)

    # Reformulation only (e.g. 7.41 innate notation change with subnote
    # "Effective values are not changed"): both fns produce the same number
    # at every level. Collapse the old/new pair into a single "value" row —
    # the diff table would just show two identical lines otherwise.
    values_unchanged = all(old_fn(L) == new_fn(L) for L in levels)
    if values_unchanged:
        table = (
            f'<table class="formula-table" id="{fid}" hidden>'
            f'<thead><tr>{axis_th}{head_cells}</tr></thead>'
            f'<tbody><tr><th class="row-label-new">value</th>{new_cells}</tr></tbody>'
            f'</table>'
        )
        return trigger, badge, table

    pct_data = [_compute_pct(old_fn(L), new_fn(L), l) for L in levels]
    pct_cells = [
        f'<td{cls_for(L)}><span class="badge {cls}">{disp}</span></td>'
        for L, (cls, disp, _, _) in zip(levels, pct_data)
    ]
    uniform_delta = len({(cls, disp) for cls, disp, _, _ in pct_data}) == 1

    pct_row = "" if uniform_delta else (
        f'<tr><th>Δ%</th>{"".join(pct_cells)}</tr>'
    )

    table = (
        f'<table class="formula-table" id="{fid}" hidden>'
        f'<thead><tr>{axis_th}{head_cells}</tr></thead>'
        f'<tbody>'
        f'<tr><th class="row-label-old">old</th>{old_cells}</tr>'
        f'<tr><th class="row-label-new">new</th>{new_cells}</tr>'
        f'{pct_row}'
        f'</tbody>'
        f'</table>'
    )

    return trigger, badge, table


# Facet metadata keyed by facet slug (e.g. "broodmother_necrotic_webs").
# Sourced from Valve's live patchnotes datafeed:
#   /datafeed/patchnotes?version=<X>&language=english -> heroes[].subsections[]
#     {title, facet, facet_color, facet_icon, abilities: [...]}
# Run scripts/fetch/fetch_facets.py to regenerate this dict for a given patch.
# Value tuple: (display_title, valve_color_key).
FACETS = {
    # 7.39d — names from abilities_english.txt, colours from facets_icons.json
    "dawnbreaker_solar_charged":      ("Solar Charged",        "Gray3"),
    "faceless_void_chronosphere":     ("Chronosphere",         "Green0"),
    "faceless_void_time_zone":        ("Time Zone",            "Purple1"),
    "furion_soothing_saplings":       ("Soothing Saplings",    "Green0"),
    "monkey_king_transfiguration":    ("Changing of the Guard","Red2"),
    "undying_rotting_mitts":          ("Rotting Mitts",        "Green4"),
    # 7.39e — fetched 2026-06-14 from /datafeed/patchnotes?version=7.39e
    "crystal_maiden_arcane_overflow": ("Arcane Overflow", "Blue2"),
    "disruptor_thunderstorm":         ("Thunderstorm",    "Red1"),
    "earthshaker_tectonic_buildup":   ("Tectonic Buildup","Red1"),
    "naga_siren_active_riptide":      ("Deluge",          "Green2"),
    "puck_curveball":                 ("Curveball",       "Blue2"),
    "pugna_siphoning_ward":           ("Siphoning Ward",  "Green0"),
    "sand_king_obscurity":            ("Sandblast",       "Yellow3"),
    "snapfire_full_bore":             ("Full Bore",       "Red0"),
    # 7.40 — fetched 2026-05-19 from /datafeed/patchnotes?version=7.40
    "batrider_arsonist":                ("Arsonist",             "Yellow1"),
    "bounty_hunter_mugging":            ("Cutpurse",             "Yellow0"),
    "bristleback_snot_rocket":          ("Snot Rocket",          "Green0"),
    "enchantress_overprotective_wisps": ("Overprotective Wisps", "Green0"),
    "gyrocopter_afterburner":           ("Afterburner",          "Yellow1"),
    "hoodwink_hunter":                  ("Go Nuts",              "Yellow0"),
    "leshrac_misanthropy":              ("Misanthropy",          "Purple0"),
    "magnataur_diminishing_return":     ("Diminishing Return",   "Blue2"),
    "meepo_more_meepo":                 ("More Meepo",           "Blue2"),
    "mirana_starstruck":                ("Starstruck",           "Blue1"),
    "monkey_king_simian_stride":        ("Simian Stride",        "Green4"),
    "morphling_str":                    ("Flow",                 "Red0"),
    "naga_siren_active_riptide":        ("Deluge",               "Green2"),
    "naga_siren_passive_riptide":       ("Rip Tide",             "Yellow2"),
    "necrolyte_profane_potency":        ("Profane Potency",      "Yellow2"),
    "night_stalker_voidbringer":        ("Voidbringer",          "Blue0"),
    "primal_beast_ferocity":            ("Ferocity",             "Yellow3"),
    "pugna_siphoning_ward":             ("Siphoning Ward",       "Green0"),
    "queenofpain_facet_bondage":        ("Bondage",              "Blue0"),
    "razor_thunderhead":                ("Thunderhead",          "Gray0"),
    "shadow_shaman_massive_serpent_ward":("Massive Serpent Ward","Red1"),
    "silencer_spread_the_knowledge":    ("Synaptic Split",       "Purple1"),
    "venomancer_plague_carrier":        ("Plague Carrier",       "Yellow0"),
    "witch_doctor_malpractice":         ("Malpractice",          "Red2"),
    # 7.40c — fetched 2026-05-16 from /datafeed/patchnotes?version=7.40c
    "huskar_cauterize":         ("Cauterize",      "Red0"),
    "broodmother_necrotic_webs":("Necrotic Webs",  "Gray0"),
    "shadow_demon_promulgate":  ("Promulgate",     "Gray0"),
    "ringmaster_carny_classics":("Carny Classics", "Yellow1"),
    # 7.40b — fetched 2026-05-16 from /datafeed/patchnotes?version=7.40b
    "drow_ranger_sidestep":          ("Sidestep",         "Blue1"),
    "invoker_wex_focus":             ("Mind of Tornarus", "Purple0"),
    "kez_flutter":                   ("Flutter",          "Yellow1"),
    "kez_shadowhawk":                ("Shadowhawk",       "Blue2"),
    "legion_commander_spoils_of_war":("Spoils of War",    "Red0"),
    "pudge_fresh_meat":              ("Fresh Meat",       "Red0"),
    "skeleton_king_facet_bone_guard":("Bone Guard",       "Yellow0"),
    "tidehunter_sizescale":          ("Krill Eater",      "Green0"),
    "ursa_debuff_reduce":            ("Bear Down",        "Blue0"),
    "viper_caustic_bath":            ("Caustic Bath",     "Yellow2"),
    "windrunner_tangled":            ("Tangled",          "Yellow2"),
    "witch_doctor_cleft_death":      ("Cleft Death",      "Purple0"),
    # --- Removed in 7.40 — colours lifted from the pre-7.40 datafeed
    #     (scripts/fetch/fetch_facets.py over 7.36..7.39e). Kept here manually so a
    #     future fetch_facets regen for a current patch doesn't drop them. ---
    "brewmaster_roll_out_the_barrel":   ("Roll Out the Barrel", "Red1"),
    "brewmaster_drunken_master":        ("Drunken Master",      "Yellow1"),
    "clinkz_suppressive_fire":          ("Suppressive Fire",    "Gray3"),
    "clinkz_engulfing_step":            ("Engulfing Step",      "Yellow0"),
    "doom_bringer_boost_selling":       ("Devil's Bargain",     "Yellow0"),
    "earth_spirit_resonance":           ("Resonance",           "Green0"),
    "earth_spirit_stepping_stone":      ("Stepping Stone",      "Gray2"),
    "earth_spirit_ready_to_roll":       ("Ready to Roll",       "Yellow1"),
    "lone_druid_bear_with_me":          ("Bear with Me",        "Green1"),
    "lone_druid_bear_necessities":      ("Bear Necessities",    "Gray1"),
    "pangolier_double_jump":            ("Double Jump",         "Red1"),
    "pangolier_thunderbolt":            ("Thunderbolt",         "Yellow1"),
    "phantom_lancer_divergence":        ("Divergence",          "Blue2"),
    "phantom_lancer_lancelot":          ("Lancelot",            "Yellow0"),   # = renamed Convergence
    "riki_contract_killer":             ("Contract Killer",     "Gray3"),
    "riki_exterminator":                ("Exterminator",        "Purple2"),
    "slark_leeching_leash":             ("Leeching Leash",      "Green2"),
    "slark_dark_reef_renegade":         ("Dark Reef Renegade",  "Blue2"),
    "spectre_forsaken":                 ("Forsaken",            "Gray0"),
    "spectre_twist_the_knife":          ("Twist the Knife",     "Purple2"),
    "treant_primeval_power":            ("Primeval Power",      "Yellow2"),
    "treant_sapling":                   ("Sapling",             "Green2"),
    "marci_fleeting_fury":              ("Fleeting Fury",       "Red1"),      # COLOUR GUESSED
    # --- Other current facets referenced in patch text but never emitted as a
    #     standalone hero_facet subsection in the datafeed (so fetch_facets
    #     can't see them). Colours pulled from prior-name datafeed snapshots
    #     when the slug was renamed. ---
    "abaddon_the_quickening":           ("The Quickening",      "Gray0"),     # = renamed abaddon_death_dude (7.36 datafeed Gray0)
    "lich_cryophobia":                  ("Evil Eye",            "Red0"),
    "primal_beast_provoke_the_beast":   ("Provoke the Beast",   "Red0"),
    # 7.39b
    "antimage_magebanes_mirror":        ("Magebane's Mirror",   "Purple1"),
    "bloodseeker_old_blood":            ("Old Blood",           "Gray1"),
    "lina_dot":                         ("Slow Burn",           "Red0"),
    "enigma_fragment":                  ("Splitting Image",     "Purple0"),
    "tinker_translocator":              ("Translocator",        "Yellow2"),
    "dazzle_facet_nothl_boon":          ("Nothl Boon",          "Red1"),
    "furion_natures_profit":            ("Nature's Profit",     "Yellow2"),
    "life_stealer_gorestorm":           ("Gorestorm",           "Red0"),
    "silencer_oppressive_silence":      ("Suffer In Silence",   "Gray3"),
    "visage_sepulchre":                 ("Sepulchre",           "Gray0"),
    "troll_warlord_bad_influence":      ("Bad Influence",       "Red1"),
    "ringmaster_sideshow_secrets":      ("Sideshow Secrets",    "Red0"),
    # 7.39 — removed facets (not in auto-registration, slugs from abilities_english.txt)
    "abaddon_mephitic_shroud":          ("Mephitic Shroud",      "Blue1"),
    "bloodseeker_bloodrush":            ("Bloodrush",            "Gray1"),
    "lich_frostbound":                  ("Frostbound",           "Blue0"),
    "muerta_ofrenda":                   ("Ofrenda",              "Yellow0"),
    "sand_king_sandshroud":             ("Sandshroud",           "Gray3"),
    "sand_king_dust_devil":             ("Dust Devil",           "Yellow1"),
    "witch_doctor_headhunter":          ("Headhunter",           "Gray3"),
    "batrider_buff_on_displacement":    ("Stoked",               "Red0"),
    "furion_ironwood_treant":           ("Ironwood Treant",       "Blue2"),
    "monkey_king_wukongs_faithful":     ("Wukong's Faithful",    "Red2"),
    "silencer_irrepressible":           ("Irrepressible",         "Purple1"),
    "silencer_reverberating_silence":   ("Reverberating Silence", "Gray3"),
    # 7.39 — auto-registered by generate_patch_code_v2.py
    "axe_call_out": ("Call Out", "Red2"),
    "mirana_leaps_and_bounds": ("Leaps and Bounds", "Gray3"),
    "nevermore_shadowmire": ("Shadowmire", "Red0"),
    "razor_spellamp": ("Dynamo", "Blue0"),
    "kunkka_grog": ("Grog Blossom", "Yellow2"),
    "pugna_rewards_of_ruin": ("Rewards of Ruin", "Purple2"),
    "dragon_knight_frost_dragon": ("Frost Dragon", "Blue0"),
    "leshrac_attacks_mana": ("Chronoptic Nourishment", "Blue1"),
    "enchantress_spellbound": ("Spellbound", "Yellow2"),
    "alchemist_dividends": ("Dividends", "Green2"),
    "invoker_quas_focus": ("Scholar of Koryx", "Blue0"),
    "invoker_exort_focus": ("Agent of Gallaron", "Yellow0"),
    "lycan_spirit_wolves": ("Spirit Wolves", "Red0"),
    "chaos_knight_cloven_chaos": ("Cloven Chaos", "Red0"),
    "disruptor_line_walls": ("Kinetic Fence", "Blue1"),
    "keeper_of_the_light_facet_recall": ("Recall", "Gray3"),
    "centaur_counter_strike": ("Counter-Strike", "Red1"),
    "bristleback_seeing_red": ("Seeing Red", "Red0"),
    "elder_titan_deconstruction": ("Deconstruction", "Blue2"),
    "ember_spirit_chain_gang": ("Chain Gang", "Yellow1"),
    "abyssal_underlord_demons_reach": ("Demon's Reach", "Green0"),
    "abyssal_underlord_summons": ("Abyssal Horde", "Yellow3"),
    "phoenix_hotspot": ("Hotspot", "Red1"),
    "arc_warden_runed_replica": ("Runed Replica", "Blue1"),
    "dawnbreaker_blaze": ("Starsurge", "Red1"),
}

# Mapping from Valve's facet_color name -> CSS gradient that EXACTLY matches
# the in-game / dota2.com patch-page facet pill. Each pill is a simple
# 2-stop `linear-gradient(to right, light, dark)` — the LEFT end is the
# tinted (themed) tone, the RIGHT end is a near-black version of the same
# hue. dota2.com positions the facet icon on the lighter LEFT side and
# the facet name text on the darker RIGHT side, so the text always lands
# on a high-contrast surface regardless of hue.
#
# Source: extracted from dota2.com/public/css/dota_react/main.css by
# resolving the hashed CSS-Module classnames in main.js (FacetColorXxx ->
# class hash -> .Background -> gradient).
_FACET_COLOR_GRADIENT = {
    "Gray0":   "linear-gradient(to right, #565C61, #1B1B21)",
    "Gray1":   "linear-gradient(to right, #6A6D73, #29272C)",
    "Gray2":   "linear-gradient(to right, #95A9B1, #3E464F)",
    "Gray3":   "linear-gradient(to right, #ADB6BE, #4E5557)",
    "Red0":    "linear-gradient(to right, #9F3C3C, #4A2040)",
    "Red1":    "linear-gradient(to right, #954533, #452732)",
    "Red2":    "linear-gradient(to right, #A3735E, #4F2A25)",
    "Yellow0": "linear-gradient(to right, #C8A45C, #6F3D21)",
    "Yellow1": "linear-gradient(to right, #C6A158, #604928)",
    "Yellow2": "linear-gradient(to right, #CAC194, #433828)",
    "Yellow3": "linear-gradient(to right, #C3A99A, #4D352B)",
    "Green0":  "linear-gradient(to right, #A2B23E, #2D5A18)",
    "Green1":  "linear-gradient(to right, #7EC2B2, #29493A)",
    "Green2":  "linear-gradient(to right, #538564, #1C3D3F)",
    "Green3":  "linear-gradient(to right, #9A9F6A, #223824)",
    "Green4":  "linear-gradient(to right, #9FAD8E, #3F4129)",
    "Blue0":   "linear-gradient(to right, #727CB2, #342D5B)",
    "Blue1":   "linear-gradient(to right, #547EA6, #2A385E)",
    "Blue2":   "linear-gradient(to right, #6BAEBC, #135459)",
    "Blue3":   "linear-gradient(to right, #94B5BA, #385B59)",
    "Purple0": "linear-gradient(to right, #B57789, #412755)",
    "Purple1": "linear-gradient(to right, #9C70A4, #282752)",
    "Purple2": "linear-gradient(to right, #675CAE, #261C44)",
}


def facet_badge(facet_slug):
    """Render the facet pill for a Valve facet slug like
    "broodmother_necrotic_webs". Looks up name + color in FACETS and emits
    a gradient-styled square chip matching the tag-badge geometry.

    Usage:
        W(li(facet_badge("broodmother_necrotic_webs") +
             " Max Charges decreased from 4/6/8/10 to 3/5/7/9",
             b([4,6,8,10], [3,5,7,9])))
    """
    if facet_slug not in FACETS:
        raise KeyError(
            f"Unknown facet slug {facet_slug!r}. Add it to FACETS — "
            f"run scripts/fetch/fetch_facets.py <patch> to grab the live data."
        )
    name, color = FACETS[facet_slug]
    grad = _FACET_COLOR_GRADIENT.get(color, _FACET_COLOR_GRADIENT["Gray1"])
    return (f'<span class="badge facet-badge" '
            f'style="background-image:{grad}">{name}</span>')


def t(tag):
    """Text-only tag for non-numeric changes.
    NEW (mechanic/property the entity didn't have before) is treated as a buff
    for filter purposes — data-overall='buff' so the BUFF filter also catches it."""
    cls_map = {
        "BUFF":   ("buff-text", "buff"),
        "NERF":   ("nerf-text", "nerf"),
        "REWORK": ("rework",    "rework"),
        "MISC":   ("misc",      "misc"),
        "QoL":    ("qol",       "qol"),
        "NEW":    ("new",       "new"),
        "DEL":    ("del",       "del"),
    }
    color_cls, tag_id = cls_map[tag]
    if tag == "NEW":
        extra = ' data-overall="buff"'   # NEW counts as buff for filtering
    elif tag == "DEL":
        extra = ' data-overall="nerf"'   # DEL (removed) counts as nerf
    else:
        extra = ''
    return f'<span class="badge {color_cls}" data-tag="{tag_id}"{extra}>{tag}</span>'


def scale_pill(formula_text, fn, levels=None, value_fmt="{:g}",
               level_prefix='L', jump_at=20):
    """Single-formula scaling pill (no old<->new comparison).
    Returns (trigger_html, table_html). Caller embeds `trigger` inline in
    description text where the formula appears; appends `table` after the
    description rows. Use for brand-new abilities whose scaling shouldn't
    be diffed against a previous version."""
    if levels is None:
        levels = list(range(1, 16)) + [20, 25, 30]
    elif isinstance(levels, int):
        levels = list(range(1, levels + 1))
    _formula_id_counter[0] += 1
    fid = f"f{_formula_id_counter[0]}"
    trigger = f'<span class="formula-trigger" data-formula="{fid}">{formula_text}</span>'

    def cls_for(L):
        return ' class="lvl-jump"' if L == jump_at else ''

    head_cells = "".join(f'<th{cls_for(L)}>{level_prefix}{L}</th>' for L in levels)
    val_cells  = "".join(f'<td{cls_for(L)}>{value_fmt.format(fn(L))}</td>' for L in levels)
    table = (
        f'<table class="formula-table" id="{fid}" hidden>'
        f'<thead><tr><th></th>{head_cells}</tr></thead>'
        f'<tbody><tr><th class="row-label-new">value</th>{val_cells}</tr></tbody>'
        f'</table>'
    )
    return trigger, table
