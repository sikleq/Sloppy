"""Unit tests for patch/badges.py.

Covers: gradient_class(), t(), b(), br(), facet_badge(), scale_pill().
Each test follows the Arrange-Act-Assert pattern and is fully independent.
"""
import pytest
from patch.badges import gradient_class, t, b, br, facet_badge, scale_pill, FACETS


# ---------------------------------------------------------------------------
# gradient_class()
# ---------------------------------------------------------------------------

class TestGradientClass:
    def test_zero_magnitude_returns_neutral(self):
        assert gradient_class(0, is_buff=True) == "neutral"

    def test_zero_magnitude_lower_returns_neutral(self):
        assert gradient_class(0, is_buff=False) == "neutral"

    def test_5pct_buff_returns_buff1(self):
        assert gradient_class(5, is_buff=True) == "buff1"

    def test_1pct_buff_returns_buff1(self):
        assert gradient_class(1, is_buff=True) == "buff1"

    def test_6pct_buff_returns_buff2(self):
        assert gradient_class(6, is_buff=True) == "buff2"

    def test_10pct_buff_returns_buff2(self):
        assert gradient_class(10, is_buff=True) == "buff2"

    def test_25pct_buff_returns_buff5(self):
        assert gradient_class(25, is_buff=True) == "buff5"

    def test_26pct_buff_returns_buff6(self):
        assert gradient_class(26, is_buff=True) == "buff6"

    def test_100pct_buff_returns_buff10(self):
        assert gradient_class(100, is_buff=True) == "buff10"

    def test_5pct_nerf_returns_nerf1(self):
        assert gradient_class(5, is_buff=False) == "nerf1"

    def test_10pct_nerf_returns_nerf2(self):
        assert gradient_class(10, is_buff=False) == "nerf2"

    def test_buff_and_nerf_differ_for_same_magnitude(self):
        assert gradient_class(20, is_buff=True) == "buff4"
        assert gradient_class(20, is_buff=False) == "nerf4"

    def test_boundary_33pct_buff_returns_buff6(self):
        assert gradient_class(33, is_buff=True) == "buff6"

    def test_boundary_34pct_buff_returns_buff7(self):
        assert gradient_class(34, is_buff=True) == "buff7"

    def test_large_magnitude_caps_at_tier10(self):
        assert gradient_class(999, is_buff=True) == "buff10"


# ---------------------------------------------------------------------------
# t() — text-only tag badge
# ---------------------------------------------------------------------------

class TestT:
    def test_buff_contains_buff_text_class(self):
        result = t("BUFF")
        assert 'class="badge buff-text"' in result
        assert ">BUFF<" in result

    def test_nerf_contains_nerf_text_class(self):
        result = t("NERF")
        assert 'class="badge nerf-text"' in result
        assert ">NERF<" in result

    def test_new_contains_new_class(self):
        result = t("NEW")
        assert 'class="badge new"' in result
        assert ">NEW<" in result

    def test_new_has_data_overall_buff(self):
        # NEW counts as buff for filter purposes
        result = t("NEW")
        assert 'data-overall="buff"' in result

    def test_del_contains_del_class(self):
        result = t("DEL")
        assert 'class="badge del"' in result
        assert ">DEL<" in result

    def test_del_has_data_overall_nerf(self):
        result = t("DEL")
        assert 'data-overall="nerf"' in result

    def test_misc_contains_misc_class(self):
        result = t("MISC")
        assert 'class="badge misc"' in result
        assert ">MISC<" in result

    def test_rework_contains_rework_class(self):
        result = t("REWORK")
        assert 'class="badge rework"' in result
        assert ">REWORK<" in result

    def test_qol_contains_qol_class(self):
        result = t("QoL")
        assert 'class="badge qol"' in result

    def test_misc_has_no_data_overall(self):
        result = t("MISC")
        assert 'data-overall' not in result

    def test_rework_has_no_data_overall(self):
        result = t("REWORK")
        assert 'data-overall' not in result

    def test_unknown_tag_raises_key_error(self):
        with pytest.raises(KeyError):
            t("BOGUS")

    def test_returns_span_element(self):
        result = t("BUFF")
        assert result.startswith('<span')
        assert result.endswith('</span>')

    def test_all_tags_have_data_tag_attribute(self):
        for tag in ("BUFF", "NERF", "NEW", "DEL", "MISC", "REWORK"):
            result = t(tag)
            assert "data-tag=" in result, f"data-tag missing for {tag}"


# ---------------------------------------------------------------------------
# b() — per-level percentage change badge
# ---------------------------------------------------------------------------

class TestB:
    def test_scalar_buff_contains_plus_pct(self):
        result = b(100, 120)
        assert "+20%" in result

    def test_scalar_buff_has_buff_class(self):
        result = b(100, 120)
        assert "buff" in result

    def test_scalar_nerf_contains_minus_pct(self):
        result = b(100, 80)
        assert "-20%" in result

    def test_scalar_nerf_has_nerf_class(self):
        result = b(100, 80)
        assert "nerf" in result

    def test_no_change_returns_neutral_badge(self):
        result = b(100, 100)
        assert "neutral" in result
        assert "0%" in result

    def test_lower_is_buff_increase_is_nerf(self):
        # cooldown going 1s -> 2s should be a nerf despite being numerically larger
        result = b(1, 2, l=True)
        assert "nerf" in result

    def test_lower_is_buff_decrease_is_buff(self):
        result = b(100, 80, l=True)
        assert "buff" in result

    def test_list_values_all_buffs(self):
        result = b([10, 20], [12, 24])
        assert "buff" in result

    def test_list_values_shows_multiple_badges_or_collapses(self):
        # When all per-level changes are identical they collapse to one badge.
        result = b([10, 20], [12, 24])
        # Both are +20%, so it should collapse to a single badge
        assert result.count("+20%") == 1

    def test_list_values_mixed_directions(self):
        # First level buff (+50%), last level nerf (-50%) — max-rank wins: NERF
        result = b([10, 20], [15, 10])
        # per-level badges are present for both
        assert "+50%" in result
        assert "-50%" in result

    def test_old_zero_emits_absolute_chip(self):
        result = b(0, 10)
        # When old==0 we emit an absolute "+N" chip, not a BUFF text badge
        assert "+10" in result
        assert 'class="badge buff"' in result

    def test_old_zero_nerf_emits_absolute_chip(self):
        result = b(0, -10)
        # 0 -> negative: emit absolute "-N" nerf chip
        assert "-10" in result
        assert 'class="badge nerf"' in result

    def test_returns_badge_group_span(self):
        result = b(100, 110)
        assert 'class="badge-group' in result

    def test_data_overall_attribute_present_for_buff(self):
        result = b(100, 200)
        assert 'data-overall="buff"' in result

    def test_data_overall_attribute_present_for_nerf(self):
        result = b(200, 100)
        assert 'data-overall="nerf"' in result

    def test_slash_kwarg_adds_slash_sep_class(self):
        result = b(100, 110, slash=True)
        assert "slash-sep" in result

    def test_force_overall_overrides_direction(self):
        # Natural direction is buff (+20%) but force to nerf
        result = b(100, 120, force_overall="nerf")
        assert 'data-overall="nerf"' in result

    def test_front_loaded_rescale_reads_as_buff(self):
        # [15,30,45,60] -> [25,35,45,55]: +67/+17/0/-8 avg pos, max-rank -8 (<=12%) -> BUFF
        result = b([15, 30, 45, 60], [25, 35, 45, 55])
        assert 'data-overall="buff"' in result

    def test_back_loaded_rescale_reads_as_nerf(self):
        # [5,7,9,11] -> [3,6,9,12]: -40/-14/0/+9 avg neg, max-rank +9 (<=12%) -> NERF
        result = b([5, 7, 9, 11], [3, 6, 9, 12])
        assert 'data-overall="nerf"' in result

    def test_sub_percent_delta_shows_decimal(self):
        # 1000 -> 1001 = +0.1%: rounds to 0 as integer but should show decimal
        result = b(1000, 1001)
        assert "0.1%" in result

    def test_flat_rescale_classified_by_mean(self):
        # [4,8,12,16] -> [10]: old mean=10, flat=10 -> tie goes to buff
        result = b([4, 8, 12, 16], [10, 10, 10, 10])
        assert 'data-overall="buff"' in result


class TestBEarlyGameCut:
    """Max-rank is a real buff (>12%) but >=2 earlier levels got worse and the
    per-level deltas average <= -10% -> NERF (decided 2026-09-15)."""

    def test_impact_damage_flat_to_ladder_is_nerf(self):
        # 50 -> 20/35/50/65 = -60/-30/0/+30, avg -15
        assert 'data-overall="nerf"' in b(50, [20, 35, 50, 65])

    def test_damage_to_healing_is_nerf(self):
        # 20 -> 10/15/20/25 = -50/-25/0/+25, avg -12.5
        assert 'data-overall="nerf"' in b(20, [10, 15, 20, 25])

    def test_disseminate_canon_stays_buff(self):
        # -20/-4/+7/+14, avg -0.75 > -10
        assert 'data-overall="buff"' in b([20, 25, 30, 35], [16, 24, 32, 40])

    def test_single_early_dip_stays_buff(self):
        # 100 -> 80/95/110/125 = -20/-5/+10/+25, avg +2.5
        assert 'data-overall="buff"' in b(100, [80, 95, 110, 125])

    def test_lower_is_better_cooldown_early_cut_is_nerf(self):
        # l=True: 10 -> 14/13/10/8 = worse/worse/0/better(+20%), avg (-40-30+0+20)/4 = -12.5
        assert 'data-overall="nerf"' in b(10, [14, 13, 10, 8], l=True)


# ---------------------------------------------------------------------------
# br() — damage range badge
# ---------------------------------------------------------------------------

class TestBr:
    def test_br_returns_badge_group(self):
        result = br(100, 120, 110, 130)
        assert 'class="badge-group' in result

    def test_br_buff_detected_from_midpoint(self):
        # old midpoint 110, new midpoint 120 -> buff
        result = br(100, 120, 110, 130)
        assert "buff" in result

    def test_br_nerf_detected_from_midpoint(self):
        # old midpoint 110, new midpoint 100 -> nerf
        result = br(100, 120, 90, 110)
        assert "nerf" in result

    def test_br_no_change(self):
        result = br(100, 120, 100, 120)
        assert "neutral" in result

    def test_br_lower_is_buff(self):
        # cooldown range goes up -> nerf with l=True
        result = br(1, 2, 2, 3, l=True)
        assert "nerf" in result


# ---------------------------------------------------------------------------
# facet_badge()
# ---------------------------------------------------------------------------

class TestFacetBadge:
    def test_known_slug_returns_span(self):
        result = facet_badge("huskar_cauterize")
        assert result.startswith("<span")
        assert "Cauterize" in result

    def test_known_slug_contains_gradient_style(self):
        result = facet_badge("huskar_cauterize")
        assert "background-image" in result
        assert "linear-gradient" in result

    def test_known_slug_has_facet_badge_class(self):
        result = facet_badge("huskar_cauterize")
        assert 'class="badge facet-badge"' in result

    def test_unknown_slug_raises_key_error(self):
        with pytest.raises(KeyError):
            facet_badge("nonexistent_hero_facet_xyz")

    def test_all_facets_in_dict_renderable(self):
        for slug in FACETS:
            result = facet_badge(slug)
            assert "badge facet-badge" in result, f"facet_badge failed for {slug}"

    def test_facet_name_appears_in_output(self):
        slug = "broodmother_necrotic_webs"
        name, _ = FACETS[slug]
        result = facet_badge(slug)
        assert name in result


# ---------------------------------------------------------------------------
# scale_pill()
# ---------------------------------------------------------------------------

class TestScalePill:
    def test_returns_tuple_of_two(self):
        trigger, table = scale_pill("3% per level", lambda L: L * 3)
        assert trigger is not None
        assert table is not None

    def test_trigger_contains_formula_text(self):
        trigger, _ = scale_pill("5 per level", lambda L: L * 5)
        assert "5 per level" in trigger

    def test_trigger_is_formula_trigger_span(self):
        trigger, _ = scale_pill("X", lambda L: L)
        assert 'class="formula-trigger"' in trigger

    def test_table_contains_level_headers(self):
        _, table = scale_pill("X", lambda L: L)
        assert "L1" in table
        assert "L15" in table

    def test_table_contains_correct_values(self):
        _, table = scale_pill("3 per level", lambda L: L * 3)
        assert ">3<" in table   # L1 value
        assert ">15<" in table  # L5 value

    def test_custom_levels(self):
        _, table = scale_pill("X", lambda L: L * 2, levels=4)
        assert "L1" in table
        assert "L4" in table
        # L5 should not appear if only 4 levels requested
        assert "L5" not in table

    def test_table_is_hidden_by_default(self):
        _, table = scale_pill("X", lambda L: L)
        assert "hidden" in table

    def test_trigger_and_table_share_same_id(self):
        trigger, table = scale_pill("formula", lambda L: L)
        import re
        fid_trigger = re.search(r'data-formula="(f\d+)"', trigger)
        fid_table = re.search(r'id="(f\d+)"', table)
        assert fid_trigger is not None
        assert fid_table is not None
        assert fid_trigger.group(1) == fid_table.group(1)
