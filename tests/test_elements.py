"""Unit tests for patch/elements.py.

Functions that call W() internally are tested by inspecting the H list via
get_output(). Functions that return strings are tested directly.

All tests follow Arrange-Act-Assert and are isolated via the autouse fixtures
in conftest.py (reset_output, reset_state).
"""
import pytest
from patch.output import get_output
from patch.badges import t, b


# ---------------------------------------------------------------------------
# li()
# ---------------------------------------------------------------------------

class TestLi:
    def test_basic_text_is_wrapped_in_li(self):
        from patch.elements import li
        result = li("Some change")
        assert "<li" in result
        assert "Some change" in result
        assert "</li>" in result

    def test_text_placed_inside_row_text_span(self):
        from patch.elements import li
        result = li("Hello world")
        assert 'class="row-text"' in result
        assert "Hello world" in result

    def test_li_with_badge_includes_badge_html(self):
        from patch.elements import li
        badge_html = t("BUFF")
        result = li("Damage increased", badge_html)
        assert "Damage increased" in result
        assert "BUFF" in result

    def test_li_with_numeric_badge(self):
        from patch.elements import li
        badge_html = b(100, 120)
        result = li("Health increased", badge_html)
        assert "Health increased" in result
        assert "+20%" in result

    def test_li_with_nerf_badge_has_nerf_data_tag(self):
        from patch.elements import li
        badge_html = b(100, 80)
        result = li("Damage reduced", badge_html)
        assert 'data-tag=' in result

    def test_li_with_new_tag_inherits_buff_filter(self):
        from patch.elements import li
        badge_html = t("NEW")
        result = li("New mechanic", badge_html)
        # NEW is a buff for filter purposes — data-tag should contain "new"
        assert "new" in result

    def test_li_with_del_tag_inherits_nerf_filter(self):
        from patch.elements import li
        badge_html = t("DEL")
        result = li("Feature removed", badge_html)
        assert "del" in result

    def test_li_ability_row_prefix_bolded(self):
        from patch.elements import li
        result = li("Active: Does something")
        assert "<b>Active:</b>" in result
        assert "ability-row" in result

    def test_li_passive_row_prefix_bolded(self):
        from patch.elements import li
        result = li("Passive: Aura effect")
        assert "<b>Passive:</b>" in result

    def test_li_aghs_scepter_text_adds_scepter_class(self):
        from patch.elements import li
        result = li("Aghanim's Scepter upgrade")
        assert "aghanim-scepter" in result

    def test_li_aghs_shard_text_adds_shard_class(self):
        from patch.elements import li
        result = li("Aghanim's Shard upgrade")
        assert "aghanim-shard" in result

    def test_li_force_tag_overrides_badge_tag(self):
        from patch.elements import li
        result = li("Change", force_tag="misc")
        assert 'data-tag="misc"' in result

    def test_li_extra_appended_inside_element(self):
        from patch.elements import li
        result = li("Base text", extra='<div class="note">note</div>')
        assert '<div class="note">note</div>' in result
        assert result.endswith("</li>")

    def test_li_empty_badge_gives_empty_row_tag(self):
        from patch.elements import li
        result = li("Plain change")
        assert 'row-tag-empty' in result

    def test_li_with_misc_badge_tag(self):
        from patch.elements import li
        result = li("Minor tweak", t("MISC"))
        assert "MISC" in result

    def test_li_talent_prefix_colon_normalised(self):
        from patch.elements import li
        # "Level 25 Talent Foo" -> "Level 25 Talent: Foo"
        result = li("Level 25 Talent Foo")
        assert "Level 25 Talent: Foo" in result

    def test_li_ability_row_kwarg(self):
        from patch.elements import li
        result = li("Some line", ability_row=True)
        assert "ability-row" in result

    def test_li_returns_string_not_none(self):
        from patch.elements import li
        assert li("test") is not None


# ---------------------------------------------------------------------------
# ul_open() / ul_close() — called via W(), check H
# ---------------------------------------------------------------------------

class TestUlOpenClose:
    def _emit(self, fn):
        from patch.output import W
        W(fn())

    def test_ul_open_emits_ul_element(self):
        from patch.elements import ul_open
        self._emit(ul_open)
        assert '<ul class="changes">' in get_output()

    def test_ul_close_emits_closing_tag(self):
        from patch.elements import ul_open, ul_close
        self._emit(ul_open)
        self._emit(ul_close)
        assert "</ul>" in get_output()

    def test_ul_open_and_close_produce_valid_pair(self):
        from patch.elements import ul_open, ul_close
        self._emit(ul_open)
        self._emit(ul_close)
        out = get_output()
        assert '<ul class="changes">' in out
        assert "</ul>" in out


# ---------------------------------------------------------------------------
# section()
# ---------------------------------------------------------------------------

class TestSection:
    def test_section_returns_string(self):
        from patch.elements import section
        result = section("General")
        assert isinstance(result, str)

    def test_section_contains_title(self):
        from patch.elements import section
        result = section("General Updates")
        assert "General Updates" in result

    def test_section_contains_h2(self):
        from patch.elements import section
        result = section("Heroes")
        assert "<h2" in result

    def test_section_contains_cat_panel_class(self):
        from patch.elements import section
        result = section("Items")
        assert 'class="cat-panel"' in result

    def test_section_includes_data_section_slug(self):
        from patch.elements import section
        result = section("General")
        assert 'data-section=' in result

    def test_consecutive_sections_close_previous(self):
        from patch.elements import section
        section("First")   # sets section_panel_open = True
        result = section("Second")
        assert "</section>" in result

    def test_section_updates_state_current_sections(self):
        from patch.elements import section
        from patch.state import _State
        section("Alpha")
        assert len(_State.current_sections) == 1
        assert _State.current_sections[0]["label"] == "Alpha"


# ---------------------------------------------------------------------------
# subgroup()
# ---------------------------------------------------------------------------

class TestSubgroup:
    def test_subgroup_returns_string(self):
        from patch.elements import subgroup
        result = subgroup("Abilities")
        assert isinstance(result, str)

    def test_subgroup_contains_h4(self):
        from patch.elements import subgroup
        result = subgroup("Abilities")
        assert "<h4" in result

    def test_subgroup_contains_title(self):
        from patch.elements import subgroup
        result = subgroup("STATS")
        assert "STATS" in result

    def test_talents_subgroup_adds_ability_block(self):
        from patch.elements import subgroup
        result = subgroup("Talents")
        assert "ability-block" in result

    def test_abilities_subgroup_marks_state(self):
        from patch.elements import subgroup
        from patch.state import _State
        subgroup("Abilities")
        assert _State.seen_abilities_subgroup is True


# ---------------------------------------------------------------------------
# inline_note()
# ---------------------------------------------------------------------------

class TestInlineNote:
    def test_returns_string(self):
        from patch.elements import inline_note
        result = inline_note("This is a note")
        assert isinstance(result, str)

    def test_contains_note_text(self):
        from patch.elements import inline_note
        result = inline_note("Some detail")
        assert "Some detail" in result

    def test_wraps_in_inlinetip_comments(self):
        from patch.elements import inline_note
        result = inline_note("hint")
        assert "<!--INLINETIP-->" in result
        assert "<!--/INLINETIP-->" in result

    def test_contains_info_tip_markup(self):
        from patch.elements import inline_note
        result = inline_note("detail")
        assert "info-tip" in result


# ---------------------------------------------------------------------------
# info_tip()
# ---------------------------------------------------------------------------

class TestInfoTip:
    def test_single_line(self):
        from patch.elements import info_tip
        result = info_tip("Line 1")
        assert "Line 1" in result

    def test_multiple_lines_become_bullets(self):
        from patch.elements import info_tip
        result = info_tip("Line 1", "Line 2")
        assert '<span class="pop-li">Line 1</span><span class="pop-li">Line 2</span>' in result

    def test_returns_span_with_info_tip_class(self):
        from patch.elements import info_tip
        result = info_tip("text")
        assert 'class="info-tip"' in result

    def test_header_option(self):
        from patch.elements import info_tip
        result = info_tip("body", header="Title")
        assert "Title" in result
        assert 'class="info-pop-h"' in result

    def test_no_header_by_default(self):
        from patch.elements import info_tip
        result = info_tip("body")
        assert "info-pop-h" not in result

    def test_wrapped_in_tip_comments(self):
        from patch.elements import info_tip
        result = info_tip("x")
        assert result.startswith("<!--TIP-->")
        assert result.endswith("<!--/TIP-->")


# ---------------------------------------------------------------------------
# show_list()
# ---------------------------------------------------------------------------

class TestShowList:
    def test_returns_details_element(self):
        from patch.elements import show_list
        result = show_list("Alpha", "Beta", "Gamma")
        assert "<details" in result
        assert "</details>" in result

    def test_contains_all_items(self):
        from patch.elements import show_list
        result = show_list("Alpha", "Beta")
        assert "Alpha" in result
        assert "Beta" in result

    def test_count_shown_in_summary(self):
        from patch.elements import show_list
        result = show_list("A", "B", "C")
        assert "(3)" in result

    def test_custom_summary_label(self):
        from patch.elements import show_list
        result = show_list("X", summary="View items")
        assert "View items" in result

    def test_default_summary_label(self):
        from patch.elements import show_list
        result = show_list("X")
        assert "Show list" in result

    def test_items_have_show_list_item_class(self):
        from patch.elements import show_list
        result = show_list("Item A")
        assert 'class="show-list-item"' in result


# ---------------------------------------------------------------------------
# item_cost()
# ---------------------------------------------------------------------------

class TestItemCost:
    def test_returns_string(self):
        from patch.elements import item_cost
        result = item_cost(4200)
        assert isinstance(result, str)

    def test_contains_gold_value(self):
        from patch.elements import item_cost
        result = item_cost(4200)
        assert "4200" in result

    def test_contains_cost_label(self):
        from patch.elements import item_cost
        result = item_cost(100)
        assert "Cost" in result

    def test_wrapped_in_item_cost_box(self):
        from patch.elements import item_cost
        result = item_cost(500)
        assert 'class="item-cost-box"' in result

    def test_zero_cost(self):
        from patch.elements import item_cost
        result = item_cost(0)
        assert "0" in result

    def test_large_cost(self):
        from patch.elements import item_cost
        result = item_cost(99999)
        assert "99999" in result


# ---------------------------------------------------------------------------
# aghs_line()
# ---------------------------------------------------------------------------

class TestAghsLine:
    def test_returns_string(self):
        from patch.elements import aghs_line
        result = aghs_line("Adds new ability")
        assert isinstance(result, str)

    def test_contains_text(self):
        from patch.elements import aghs_line
        result = aghs_line("Adds new ability")
        assert "Adds new ability" in result

    def test_default_kind_is_scepter(self):
        from patch.elements import aghs_line
        result = aghs_line("text")
        assert "aghanim-scepter" in result
        assert "scepter" in result

    def test_shard_kind(self):
        from patch.elements import aghs_line
        result = aghs_line("Shard effect", kind="shard")
        assert "aghanim-shard" in result
        assert "shard" in result

    def test_wrapped_in_ability_change_row(self):
        from patch.elements import aghs_line
        result = aghs_line("text")
        assert 'class="ability-change-row' in result

    def test_aghanim_marker_span_present(self):
        from patch.elements import aghs_line
        result = aghs_line("text")
        assert 'class="aghanim-marker' in result

    def test_inline_note_text_included_when_provided(self):
        from patch.elements import aghs_line
        result = aghs_line("text", inline_note_text="Extra detail")
        assert "Extra detail" in result
        assert 'class="inline-note"' in result

    def test_no_inline_note_by_default(self):
        from patch.elements import aghs_line
        result = aghs_line("text")
        assert "inline-note" not in result


# ---------------------------------------------------------------------------
# note_box() — quick smoke test
# ---------------------------------------------------------------------------

class TestNoteBox:
    def test_plain_text_note(self):
        from patch.elements import note_box
        result = note_box("Some note text")
        assert "Some note text" in result

    def test_returns_string(self):
        from patch.elements import note_box
        result = note_box("Note")
        assert isinstance(result, str)

    def test_plain_text_wrapped_in_inlinetip(self):
        from patch.elements import note_box
        result = note_box("Correction text")
        assert "<!--INLINETIP-->" in result

    def test_note_header_present(self):
        from patch.elements import note_box
        result = note_box("text")
        assert "Note:" in result


def test_properties_change_puts_change_chip_on_new_side():
    from patch.elements import properties_change
    html = properties_change(old=[("BUFF", "+10 Strength"), ("DEL", "+250 Health")],
                             new=[("", "+26 Strength", "<b>+160%</b>"), ("NEW", "+25% Slow Resistance")])
    old_pane, new_pane = html.split("→", 1) if "→" in html else html.split("properties-pane", 2)[1:3]
    assert 'data-tag="buff"' not in old_pane and 'data-tag="buff"' in new_pane
    assert 'data-tag="del"' in old_pane
