"""The site changelog data must stay loadable: valid dates, known categories, existing shots."""
import os

from builders import changelog as clog


def test_changelog_entries_are_valid_and_newest_first():
    entries = clog.load_entries()
    assert entries, "data/changelog.json has no entries"
    dates = [e["date"] for e in entries]
    assert dates == sorted(dates, reverse=True)
    for e in entries:
        assert e["title"], e
        if not e.get("minor"):
            assert e.get("items"), e                        # a feature entry says what it gives
        for shot in e.get("shots", []):
            assert os.path.exists(os.path.join(clog._HERE, shot)), shot


def test_changelog_renders_features_and_small_changes():
    entries = clog.load_entries()
    html = clog.render(entries)
    assert 'class="clog-rail"' in html and 'class="clog-chip active"' in html
    assert html.count('<article class="clog-entry') == sum(1 for e in entries if not e.get("minor"))
    assert html.count('<li data-cat=') >= sum(1 for e in entries if e.get("minor"))


def test_many_small_changes_fold_under_a_toggle():
    few = [{"date": "2026-01-01", "category": "Site", "title": f"x{i}", "minor": True} for i in range(3)]
    many = few + [{"date": "2026-01-01", "category": "Site", "title": "x9", "minor": True}]
    assert "<details" not in clog._minor_html("2026-01-01", few)
    assert "<details" in clog._minor_html("2026-01-01", many)


def test_fixes_carry_the_bug_marker_and_the_rail_lists_only_features():
    entries = [{"date": "2026-01-02", "category": "Site", "title": "Thing", "items": ["x"], "fix": True},
               {"date": "2026-01-02", "category": "Site", "title": "Small", "minor": True, "fix": True},
               {"date": "2026-01-02", "category": "Site", "title": "Other", "minor": True}]
    html = clog.render(entries)
    assert html.count('class="clog-bug"') == 2
    rail = html[html.index('class="clog-rail"'):html.index("</nav>")]
    assert "Thing" in rail and "Small" not in rail and "Smaller changes" not in rail


def test_every_roster_item_gets_a_page_even_without_changes():
    from builders import entity_changes as ec
    dyn = {"items": [{"key": "item|circlet", "name": "Circlet", "icon": "circlet"},
                     {"key": "item|blink", "name": "Blink Dagger", "icon": "blink"}]}
    have = [{"kind": "item", "slug": "blink", "name": "Blink Dagger", "icon": "", "patches": [{"version": "7.41"}]}]
    extra = ec._unchanged_items(have, dyn)
    assert [e["slug"] for e in extra] == ["circlet"] and extra[0]["patches"] == []


def test_a_day_links_to_the_same_page_only_once():
    """Owner 2026-09-26: five entries of one day all linked patches/7.38.html — only the first keeps it."""
    from builders.changelog import _one_link_per_patch
    g = [{"title": "a", "link": "patches/7.38.html"}, {"title": "b", "link": "patches/7.38.html"},
         {"title": "c", "link": "patches/7.39.html"}, {"title": "d"}]
    out = _one_link_per_patch(g)
    assert [e.get("link") for e in out] == ["patches/7.38.html", None, "patches/7.39.html", None]
    assert g[1]["link"] == "patches/7.38.html"          # the data itself is not changed


def test_hero_page_filters_are_icons_and_aghanim_scopes():
    """Owner 2026-09-26: ability chips are the ability icons (long names widened the row); Shard / Scepter
    chips after Innate filter the rows an Aghanim upgrade changes."""
    from builders.entity_changes import _AB_ICON_RE, _aghs_btn
    body = ('<div class="ability-icon-wrap"><img decoding="async" src="../icons/_t/abilities/x_cold_feet.webp" '
            'alt="Cold Feet"></div><h4 class="ability-title">Cold Feet</h4>')
    m = _AB_ICON_RE.search(body)
    assert m and m.group(1).endswith("x_cold_feet.webp") and m.group(2) == "Cold Feet"
    btn = _aghs_btn("shard")
    assert 'data-ec-scope="shard"' in btn and "aghs_shard_icon" in btn and "ec-aghs-btn" in btn


def test_an_ability_left_in_the_kv_only_in_comments_is_old():
    """Owner 2026-09-26: Anti-Mage's Counterspell Ally (7.41f KV: block kept, "IsGrantedByShard" and the
    facet line commented out) is a removed ability; Spirit Bear's Return (named by a unit) is not."""
    from builders.entity_changes import _live_abilities
    txt = ('"Ability1" "antimage_mana_break"\n'
           '//\t"antimage_counterspell_ally" "shard"\n')
    defs = {"antimage_mana_break": "", "antimage_counterspell_ally": '//"IsGrantedByShard" "1"\n',
            "antimage_persectur": '"IsGrantedByScepter" "1"\n'}
    live = _live_abilities(txt, defs, ["antimage_mana_break"])
    assert "antimage_counterspell_ally" not in live
    assert {"antimage_mana_break", "antimage_persectur"} <= live


def test_a_deprecated_facet_does_not_keep_its_ability_alive():
    """Nature's Prophet 7.41f: the removed facet furion_natures_profit ("Deprecated" "true") still names
    Nature's Profit -> not a current ability; a chip without an icon of its own gets the game's empty slot."""
    from builders.entity_changes import _drop_deprecated, EMPTY_ABILITY_ICON
    kv = ('\t\t"Facets"\n\t\t{\n\t\t\t"furion_natures_profit"\n\t\t\t{\n\t\t\t\t"Abilities"\n\t\t\t\t{\n'
          '\t\t\t\t\t"AbilityName"\t"furion_natures_profit"\n\t\t\t\t}\n\t\t\t\t"Deprecated"\t"true"\n\t\t\t}\n'
          '\t\t\t"furion_spirit"\n\t\t\t{\n\t\t\t\t"Icon"\t"tree"\n\t\t\t}\n\t\t}')
    out = _drop_deprecated(kv)
    assert "furion_natures_profit" not in out and "furion_spirit" in out
    assert EMPTY_ABILITY_ICON.endswith("doom_bringer_empty1.webp")


def test_a_former_innate_title_is_read_from_a_renamed_pane():
    """Juggernaut 7.41 "Duelist -> Bladeform" (an innate pane): both names are innate, so neither gets
    an ability chip — the INNATE filter covers them (owner 2026-09-26)."""
    import html, re
    from builders.entity_changes import _INNATE_TITLE_RE
    body = ('<div class="ability-block ability-change-block is-innate"><div class="ability-icon-wrap"></div>'
            '<h4 class="ability-title"><span class="ability-title-old">Duelist</span><span>→</span>'
            '<span class="ability-title-new">Bladeform</span></h4>')
    names = {p.strip() for m in _INNATE_TITLE_RE.finditer(body)
             for p in html.unescape(re.sub(r"<[^>]+>", "→", m.group(1))).split("→") if p.strip()}
    assert names == {"Duelist", "Bladeform"}


def test_active_innates_get_an_ability_chip():
    """Owner 2026-09-26: Invoke was missing from Invoker's ability filters (it is an innate in the KV);
    a slotted, cast innate is a spell like any other. Passive innates stay under INNATE only."""
    from builders.entity_changes import _active_innates
    act = _active_innates()
    assert {"Invoke", "Stone Remnant", "Summon Spirit Bear"} <= act
    assert "Inner Beast" not in act


def test_no_unofficial_icon_for_an_innate_without_game_art():
    """Owner 2026-09-26: storm_spirit_galvanized.webp was not a game icon. 13 such PNGs (not in the client
    VPK spellicons, not on Valve's CDN) deleted (owner: yes); those innates show innate_icon.png."""
    from patch.known_exceptions import KNOWN_INNATE_NO_CDN_ICON
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    back = [s for s in KNOWN_INNATE_NO_CDN_ICON
            if os.path.exists(os.path.join(here, "icons", "abilities", f"{s}.png"))
            or os.path.exists(os.path.join(here, "icons", "_t", "abilities", f"{s}.webp"))]
    assert back == []


def test_aghanim_granted_abilities_are_aghanim_rows_and_get_no_chip():
    """Owner 2026-09-26, Medusa 7.38 Cold Blooded: a Shard-granted ability. Its rows are Shard rows even
    without the words, and the SHARD filter covers it (no chip of its own)."""
    from patch.aghs_granted import kind_of
    assert kind_of("medusa_cold_blooded") == "shard"
    assert kind_of("tiny_tree_channel") == "scepter"
    assert kind_of("medusa_mystic_snake") == ""


def test_hero_slots_ignore_the_ability_draft_list():
    """Invoker's nested AbilityDraftAbilities put Deafening Blast third; Elder Titan's repeated Echo Stomp
    (Astral Spirit) sorted it last. Slot order = the hero's own two-tab slots, first occurrence wins."""
    from builders.entity_changes import _hero_kit
    inv = _hero_kit("invoker")
    assert inv.index("Invoke") < inv.index("Deafening Blast") and inv.index("Exort") < inv.index("Invoke")
    et = _hero_kit("elder_titan")
    assert et.index("Echo Stomp") < et.index("Astral Spirit") < et.index("Natural Order") < et.index("Earth Splitter")
