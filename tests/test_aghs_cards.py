"""Guards Aghanim's Scepter / Shard cards and rows: stripes, headers, granted abilities, rework cards.
"""

import pathlib
import pytest
import re
import sys
from patch import cards_ability_change, cards_aghs, cards_item_abilities, elements as el
from patch.cards_aghs import _AGHS_REWORK_RE
from patch.state import _State

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


# ---- second review of 2026-11-08 (audit before 7.42) ----

def _page(v):
    html = ROOT / "dist" / "patches" / f"{v}.html"
    if not html.exists():
        pytest.skip("no build")
    return html.read_text(encoding="utf-8")


def _as_hero(hero, fn, *args):
    from patch.state import _State
    keep = _State.current_hero
    _State.current_hero = hero
    try:
        return fn(*args)
    finally:
        _State.current_hero = keep


def _title(head):
    """The header's words; the Aghanim's icon (2026-10-27: an icon, not the word, so the header stays one line) reads
    as its aria-label."""
    t = re.search(r'<span class="iab-title">(.*?)</span><span class="iab-meta">', head).group(1)
    t = re.sub(r'<span class="aghanim-marker [a-z]+" role="img" aria-label="([^"]*)"></span>', r"\1 ", t)
    return re.sub(r"<[^>]+>", "", t)


def test_a_removed_upgrade_ability_gets_its_own_block():
    from tools.patchgen.post_facets import _removed_innate_block
    out = _removed_innate_block("bloodseeker", "Blood Mist", None, "7.37e", "    ")
    assert out[0] == '    W(ability("Blood Mist", slug="bloodseeker_blood_mist"))' and 'li("Removed", t("DEL"))' in out[2]
    text = (ROOT / "content" / "p738.py").read_text(encoding="utf-8")
    assert "Removed Blood Mist ability" not in text and 'W(ability("Blood Mist", slug="bloodseeker_blood_mist"))' in text


def test_aghanim_rows_stay_by_their_ability_without_saying_so():
    # owner 2026-11-06, 7.38 Invoker: the "Aghanim's Scepter" / "Aghanim's Shard" heads over the upgrade rows were
    # "лишнее, надо сделать как везде с подсветкой скипетра/шарда, ну как до этого"
    import patch.cards_rows as cards_rows
    from patch.cards_rows import _card_row, _row_html
    assert not hasattr(cards_rows, "group_aghs_rows")
    row = _card_row(("<g>",), "Can be upgraded with Aghanim's Scepter. Applies to allies.")
    html = _row_html(row)
    assert "Can be upgraded" not in html and '</span>Applies to <span class="li-tail">allies.' in html
    assert 'class="ability-change-row aghanim-scepter acr-aghs"' in html and "aghanim-marker scepter" in html


def test_an_aghanim_row_its_card_shows_is_hidden():
    from patch.card_sections import hide_rows_the_aghs_card_says
    row = ('<ul class="changes"><li data-tag="buff" class="aghanim-scepter li-bg"><span class="badge">BUFF</span><span '
           'class="row-text">Aghanim\'s Scepter Cooldown decreased from 100/95/90s to 90/85/80s</span></li></ul>')
    card = ('<div class="ability-change unified-panes aghs-change"><div class="ability-change-pane ability-change-old">'
            'Reduces cooldown to <b>100/95/90s</b>.</div><div class="ability-change-pane ability-change-new">Reduces '
            'cooldown to <b>90/85/80s</b>.</div></div>')
    assert 'class="iab-covered covered-card aghanim-scepter li-bg"' in hide_rows_the_aghs_card_says(row + card)
    other = card.replace("90/85/80s", "70s")
    assert "iab-covered" not in hide_rows_the_aghs_card_says(row + other)


def test_a_cards_upgrade_row_the_aghanim_card_below_shows_goes():
    from patch.card_sections import drop_upgrade_rows_said_below
    html = ('<div class="ability-block"><div class="ability-change unified-panes is-single-new"><div class="ability-change-'
            'pane ability-change-new"><div class="ability-change-body"><div class="ability-change-row">Text.</div>'
            '<div class="ability-change-row aghanim-shard">Allows casting while disabled.</div></div></div></div>'
            '<div class="ability-change unified-panes aghs-change"><div class="ability-change-pane ability-change-new">'
            '<div class="ability-change-row aghanim-shard">Can be cast while disabled.</div></div></div></div>')
    out = drop_upgrade_rows_said_below(html)
    assert "Allows casting while disabled" not in out and "Can be cast while disabled" in out and "Text." in out


def test_an_aghanims_card_row_reaches_alike_both_ways_and_says_no_label():
    # owner 2026-11-06: "Найди подобные проблемы в других местах, может ещё где подводку скипетра/шарда не так строится"
    # — the stripe reached 6px left only (7.38 Dark Willow, 7.39 Invoker: -1px left, 5px right), past a narrow card's
    # edge; 7.39 Invoker's rows said "Aghanim's Shard:" beside the glyph
    from patch.cards_rows import _card_row, _row_html
    from patch.css_bundle import read_css
    css = read_css()
    assert (".ability-change-row.acr-aghs { --agr: min(6px, var(--px, 6px)); margin-left: calc(-1 * var(--agr));\n"
            "  margin-right: calc(-1 * var(--agr)); padding-left: var(--agr); padding-right: calc(8px + var(--agr)); }") in css
    html = _row_html(_card_row((), "Aghanim's Shard: Enemy heroes that stay in Ice Wall freeze"))
    assert "Aghanim's Shard:" not in html and ">Enemy heroes" in html and "aghanim-marker shard" in html


def test_a_shard_row_after_the_same_abilitys_scepter_row_gets_its_own_head():
    # 7.38 Agent of Gallaron: Sun Strike's Scepter (Cataclysm) and Shard (Forge Spirit) are two parts of the trio
    from patch.card_sections import card_sections
    chip = ('<span class="acr-lead-chips"><span class="ability-chip" data-tooltip="{0}" role="img">'
            '<img src="../icons/_t/abilities/{1}.webp" alt=""></span></span>')
    row = '<div class="ability-change-row{0}">{1}{2}</div>'
    pane = ('<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
            + row.format("", chip.format("Exort", "invoker_exort"), "Bonus level.")
            + row.format(" aghanim-scepter acr-aghs", chip.format("Sun Strike", "invoker_sun_strike"), "Cataclysm.")
            + row.format(" aghanim-shard acr-aghs", chip.format("Sun Strike", "invoker_sun_strike"), "Forge Spirit.")
            + "</div></div>")
    out = card_sections(pane, "7.38")
    assert out.count('<span class="iab-name">Sun Strike</span>') == 2


def test_a_slightly_reworked_upgrade_gets_its_card_and_hides_its_rows():
    # 7.40 Tricks of the Trade: "разве old > new карточкой не надо сделать"
    text = _page("7.40")
    block = text[text.index('alt="Tricks of the Trade"'):]
    block = block[:block.index('alt="Cloak and Dagger"')]
    assert "aghs-change" in block
    for row in ("Scepter now also allows to hide within allied",
                "bonus movement speed to the ally"):
        i = block.index(row)
        assert "iab-covered" in block[block.rfind("<li", 0, i):i]
    i = block.index("Radius decreased from 450 to 425")
    assert "iab-covered" not in block[block.rfind("<li", 0, i):i]


def test_an_aghanims_rework_with_a_full_stop_is_a_card():
    """7.37 Anti-Mage "Aghanim's Scepter upgrade reworked. Reduces cooldown by 1s. …" — a full stop, not a colon; the
    old side is 7.36c's Scepter, which granted Blink Fragment (Mana Overload); the caption says "reworked"."""
    from pathlib import Path
    from patch.cards_aghs import _AGHS_REWORK_RE
    assert _AGHS_REWORK_RE.match("Aghanim's Scepter upgrade reworked. Reduces cooldown by 1s.")
    assert _AGHS_REWORK_RE.match("Aghanim's Shard reworked: Vendetta applies Break")
    page = Path(__file__).resolve().parents[1] / "dist" / "patches" / "7.37.html"
    if page.exists():
        html = page.read_text(encoding="utf-8")
        i = html.find("Blink Fragment")
        assert i > 0 and "Aghanim's Scepter reworked." in html[i - 700:i]


@pytest.mark.parametrize("text, kind", [
    ("E.M.P.: Can be upgraded with Aghanim's Shard. Increases Burn Damage from 60% to 90%", "shard"),
    ("Wex: Aghanim's Scepter grants 1 additional current level, and increases max level to 10", "scepter"),
    ("Sun Strike: Now Aghanim's Scepter grants Cataclysm exclusively with this facet", "scepter"),
])
def test_a_card_row_about_an_aghanims_upgrade_gets_its_stripe(text, kind):
    """Owner 2026-10-30, 7.38 Invoker's facets: "не подсвечено аганимной подложкой, как и шард — шардовой"; the glyph at
    the END of the text, glued to its last word, as on every list row ("по правилам в конце строки")."""
    from patch.cards_item_abilities import _pane_parts
    _, body = _as_hero("invoker", _pane_parts, [text, "Alacrity: Grants bonus attack range"])
    assert body.count(f'<div class="ability-change-row aghanim-{kind} acr-aghs"><span class="acr-lead-chips">') == 1
    # the upgrade's row stays where it is, its own glyph at its end, no "Aghanim's X" head over it (owner 2026-11-06:
    # the heads were "лишнее … как до этого"); "Can be upgraded with Aghanim's X." is not said
    assert "acr-aghs-head" not in body and "Can be upgraded" not in body
    assert body.count(f'<span class="aghanim-marker {kind}"></span>') == 1


def test_an_added_upgrade_card_has_the_ability_header_and_charges_take_the_cooldown():
    """Owner 2026-10-28 (7.37e Escape Act): an "Added Aghanim's Scepter." card has its ability's header (Active, range,
    mana, cooldown); an upgrade that swaps the cooldown for charges shows the charge restore time there instead."""
    from patch.cards_aghs import _added_upgrade_head
    text = ("Escape Act has 2 charges. When the box pops open, Impalement Art daggers are thrown in all directions, and "
            "all enemies in an 225 radius take 300 damage. Cooldown: -100%. Charge restore time: 38/32/26/20s.")
    body, head = _added_upgrade_head("ringmaster_the_box", "7.37e", text)
    assert "Cooldown" not in body and "Charge restore" not in body and body.endswith("300 damage.")
    assert '<b class="iab-kind">Active</b>' in head
    assert all(v in head for v in (">600<", ">80<", ">38/32/26/20<"))


def test_now_granted_by_aghanims_hides_under_its_card(monkeypatch):
    """7.39 Fan of Knives: "Now granted by Aghanim's Scepter" + the card "Added Aghanim's Scepter." said it twice."""
    from patch import cards_aghs
    from patch.state import _State
    flags = {("phantom_assassin_fan_of_knives", "7.39"): "scepter", ("phantom_assassin_fan_of_knives", "7.38c"): "shard"}
    monkeypatch.setattr(cards_aghs, "_granted_flag", lambda s, v: flags.get((s, v)))
    monkeypatch.setattr(_State, "current_ability_slug", "phantom_assassin_fan_of_knives")
    monkeypatch.setattr(_State, "current_patch_version", "7.39")
    assert cards_aghs._granted_now_covered("Now granted by Aghanim's Scepter")
    assert not cards_aghs._granted_now_covered("Now granted by Aghanim's Shard")     # the files say Scepter
    flags[("phantom_assassin_fan_of_knives", "7.38c")] = "scepter"                  # nothing moved: the row stays
    assert not cards_aghs._granted_now_covered("Now granted by Aghanim's Scepter")


def test_aghanims_upgrade_reworked_makes_a_card_too():
    assert _AGHS_REWORK_RE.match("Aghanim's Shard upgrade reworked: Removes the 20 stack limit")   # Batrider 7.39
    assert _AGHS_REWORK_RE.match("Aghanim's Scepter reworked: Silences when the target is alone")


def test_by_percent_goes_after_flat_aghanim_numbers():
    text = ("Increases cast range and projectile speed by 25%. When it impacts heroes, 2 wards are created.\n"
            "Cast range: +200. Projectile speed: +300.")
    out = cards_aghs._aghs_inline(text)
    assert out.startswith("Increases cast range (+200) and projectile speed (+300).") and "25%" not in out
    # another effect's "by 25%" stays
    out = cards_aghs._aghs_inline("Reduces armor and slows by 25%.\nArmor: -5.")
    assert "slows by 25%" in out


def test_the_aghanim_word_is_its_icon_in_the_header():
    head, _ = cards_item_abilities._pane_parts(["Active. Creates a wall."], granted="shard")
    assert '<span class="aghanim-marker shard" role="img" aria-label="Aghanim\'s"></span>Shard' in head
    assert "Aghanim's Shard" not in re.sub(r'aria-label="[^"]*"', "", head)


def test_shares_level_goes_to_the_header():
    head, body = cards_item_abilities._pane_parts([el.hl("Shares level with Kinetic Field", "del") + ".", "Creates a wall."],
                                {"kind": "Active"})
    assert _title(head) == "Active – levels with Kinetic Field"
    assert "Shares level" not in body and "Creates a wall." in body


def test_only_one_level_is_never_said_and_granted_is_in_the_header():
    head, body = cards_item_abilities._pane_parts([el.hl("Has only one level", "new") + ".", "Creates a wall."], {"kind": "Active"},
                                granted="shard")
    assert _title(head) == "Active – granted by Aghanim's Shard"
    assert "one level" not in body


def test_granted_and_shares_level_together():
    head, _ = cards_item_abilities._pane_parts(["Shares level with Demonic Purge.", "Cleanses."], {"kind": "Active"}, granted="shard")
    assert _title(head) == "Active – granted by Aghanim's Shard, levels with Demonic Purge"


def test_kinetic_fence_card_says_it_in_the_headers_not_the_summary():
    _State.current_patch_version = "7.41"
    try:
        html = cards_ability_change.ability_change(
            old=dict(name="Kinetic Fence", slug="disruptor_kinetic_fence",
                     desc=[el.hl("Shares level with Kinetic Field", "del") + ".", "Wall."]),
            new=dict(name="Kinetic Fence", slug="disruptor_kinetic_fence",
                     desc=["Granted by Aghanim's Shard. " + el.hl("Has only one level", "new") + ".", "Wall."]),
            summary="Ability reworked.", tag="rework")
    finally:
        el._close_ability_block()
        _State.current_patch_version = None
    titles = [_title(h) for h in re.findall(r'<div class="iab-head pane-head">.*?</div>', html)]
    assert titles == ["Active – levels with Kinetic Field", "Active – granted by Aghanim's Shard"]
    assert "(Aghanim's Shard upgrade)" not in html and 'aghanim-marker shard' in html
    assert "one level" not in html


def test_shares_level_comes_from_the_game_files():
    assert cards_aghs._shares_level("shadow_demon_demonic_cleanse", "7.37e") == "Demonic Purge"
    assert cards_aghs._shares_level("shadow_demon_demonic_cleanse", "7.38") is None      # one level since 7.38


def test_game_ability_pair_colours_numbers_and_says_the_shared_level():
    old, new = cards_ability_change.game_ability_pair("shadow_demon_demonic_cleanse", "7.38")
    assert old[0] == "Shares level with Demonic Purge." and len(new) == 1
    assert "300/450/600" in old[-1] and "450" in new[-1]


def test_base_text_lists_no_aghanims_only_value():
    from patch.aghs_text import ability_text
    text = ability_text("shadow_demon_demonic_cleanse", "7.37e")
    assert "Max charges" not in text and "charge restore" not in text.lower()
    assert "Cleanse heal: 300/450/600." in text
    # the Scepter's own text still has them
    assert "Max charges: 2" in ability_text("shadow_demon_demonic_cleanse", "7.37e", kind="scepter")


def test_granted_card_is_an_ability_card_with_headers():
    _State.current_patch_version, _State.current_ability_slug = "7.41", "tinker_warp_grenade"
    _State.aghs_cards = []
    cards_aghs._GRANTED_CARDS.discard(("7.41", "tinker_warp_grenade"))
    try:
        assert cards_aghs._granted_card({"rework"})
        card = _State.aghs_cards[-1]
    finally:
        _State.aghs_cards, _State.card_meta = [], {}
        _State.current_patch_version = _State.current_ability_slug = None
    assert "Ability reworked.<span class=\"aghanim-marker shard\"></span>" in card
    titles = [_title(h) for h in re.findall(r'<div class="iab-head pane-head">.*?</div>', card)]
    assert titles == ["Active – granted by Aghanim's Shard"] * 2
    assert "Grants this ability" not in card and "teleported further the closer" in card


def test_talents_after_a_scepter_ability_get_no_aghanim_stripe():
    # Clockwerk 7.41: the talents under Overclocking (granted by Aghanim's Scepter) were marked as Scepter rows
    from patch.state import _State
    _State.current_ability_slug = "rattletrap_overclocking"
    el.subgroup("Talents")
    assert _State.current_ability_slug is None


def test_aghanim_upgrade_goes_to_the_header_and_the_summary_keeps_the_stripe(monkeypatch):
    # 2026-10-21 the words went in brackets into the summary; 2026-10-26 the header says "granted by Aghanim's X" and
    # the summary keeps only the stripe (owner, 7.41 Kinetic Fence). The panes need the page's patch: until the
    # 2026-10-26 state reset the test got it from whichever test ran before.
    monkeypatch.setattr(el._State, "current_patch_version", "7.41")
    html = cards_ability_change.ability_change(old=dict(name="X", slug="rattletrap_overclocking", desc=["Active (Aghanim's Scepter upgrade). A."]),
                             new=dict(name="X", slug="rattletrap_overclocking", desc=["B."]),
                             summary="Ability reworked.", tag="rework")
    assert '<span class="row-text">Ability reworked.<span class="aghanim-marker scepter"></span>' in html
    assert "ac-aghs" not in html and "Active (Aghanim" not in html
    # both sides granted by the Scepter (7.40 and 7.41 Overclocking): the summary's glyph says it once, the headers don't
    # (owner 2026-11-06)
    assert "granted by" not in html
    # one side only: its header says so, "Aghanim's" as the upgrade's icon (2026-10-27: one line)
    one = cards_ability_change.ability_change(old=dict(name="X", slug="rattletrap_overclocking", desc=["Active (Aghanim's Scepter upgrade). A."]),
                            new=dict(name="Y", slug="rattletrap_battery_assault", desc=["B."]),
                            summary="Ability reworked.", tag="rework")
    assert ('– granted by <span class="aghanim-marker scepter" role="img" aria-label="Aghanim\'s"></span>Scepter'
            in one)


def test_aghanim_upgrade_words_move_from_card_text_to_its_summary():
    spec, kind = cards_ability_change._take_aghs({"desc": ["Active (Aghanim's Scepter upgrade). All abilities are supercharged:"]})
    assert kind == "scepter" and spec["desc"] == ["All abilities are supercharged:"]
    spec, kind = cards_ability_change._take_aghs({"desc": ["Granted by Aghanim's Scepter. Unit-targeted.", "x"]})
    assert kind == "scepter" and spec["desc"] == ["Unit-targeted.", "x"]


def test_card_of_an_ability_granted_by_aghanims_gets_the_stripe_of_that_patch_only():
    # owner 2026-10-22: Kinetic Fence's card "forgot the Shard stripe"; Visage's Silent as the Grave was a Scepter
    # ability before 7.41 but is innate in it — no stripe
    from patch.aghs_granted import kind_of
    assert kind_of("disruptor_kinetic_fence", "7.41") == "shard"
    assert kind_of("visage_silent_as_the_grave", "7.41") == ""
    assert kind_of("visage_silent_as_the_grave") == "scepter"        # some older patch granted it


def test_row_stripe_follows_the_patchs_own_aghanim_flag():
    # owner 2026-10-22: a row is an Aghanim row only if that patch's game grants the ability
    from patch.aghs_granted import kind_of
    assert kind_of("jakiro_liquid_ice", "7.41") == ""             # Shard only in 7.34e–7.35d
    assert kind_of("spectre_haunt", "7.40") == ""                 # the ultimate since 7.40
    assert kind_of("techies_minefield_sign", "7.38") == ""        # an innate active then, no Scepter needed
    assert kind_of("centaur_mount", "7.41f") == "scepter"         # flag gone after 7.35, still hidden + 1 level
    assert kind_of("antimage_counterspell_ally", "7.40") == "shard"   # removed in 7.40: no hero slot has it
    # 7.08 keeps only slim JSON in data/stats: its flags come from data/rules/aghs_granted_old.json
    assert kind_of("zuus_cloud", "7.08") == "scepter"
    assert kind_of("omniknight_degen_aura", "7.08") == ""          # a plain ability then (Shard in 7.34e–7.35d)


def test_kinetic_fence_741_is_a_shard_card_like_overclocking():
    # owner 2026-10-22: Kinetic Fence became an Aghanim's Shard ability — a before/after card, rows covered
    src = (ROOT / "content" / "p741.py").read_text(encoding="utf-8")
    block = src[src.index('W(hero_header("Disruptor"))'):src.index('W(hero_header("Doom"))')]
    assert 'name="Kinetic Fence"' in block and "Granted by Aghanim's Shard. " in block
    assert 'W(ability("Kinetic Fence"))' not in block
    assert 'Has only one level instead", t("NEW"), covered=True' in block
