"""Owner 2026-09-27: DEL / NEW row weights (blind judge 200 rows + devil's advocate + pro adoption)."""
from patch import weights as w

HERO = {"kind": "hero", "version": "7.38", "hero": "dazzle"}


def test_whole_ability_or_facet_removed_weighs_like_a_numberless_nerf():
    net, _ = w.row_scores("Removed Bad Juju ability", {"del"}, ctx=HERO)
    assert net == -round(w.weight_of("other") * w.WHOLE_W, 3)


def test_a_bare_removed_under_a_facet_header_is_a_whole_facet():
    """Owner 2026-10-09: the row under a removed facet's header is just "Removed" (was "X: Facet removed")."""
    facet = dict(HERO, facet=True)                                  # the row sits in a facet block
    assert w.row_scores("Removed", {"del"}, ctx=facet) == w.row_scores("Resonance: Facet removed", {"del"}, ctx=facet)


def test_generator_writes_a_bare_removed_for_a_removed_facet():
    import pathlib
    src = (pathlib.Path(__file__).resolve().parents[1] / "generate_patch_code_v2.py").read_text(encoding="utf-8")
    assert 'W(li("Removed", t("DEL")))' in src and 'li("Facet removed"' not in src


def test_a_replaced_facet_nets_zero():
    gone, _ = w.row_scores("Removed Flayer's Hook Facet", {"del"}, ctx=dict(HERO, base_stat=True))
    came, _ = w.row_scores("", {"new"}, ctx=dict(HERO, facet=True))          # the new facet's card
    assert abs(gone + came) < 1e-9 and came > 0


def test_hero_del_is_doubled_but_a_lost_niche_target_is_halved():
    part, _ = w.row_scores("No longer has lifesteal", {"del"}, ctx=HERO)
    creeps, _ = w.row_scores("No longer deals bonus damage to creeps", {"del"}, ctx=HERO)
    assert part == -round(w.weight_of(w.classify("No longer has lifesteal")) * w.DELNEW_HERO_W, 3)
    assert abs(creeps) < abs(part) * 1.01


def test_an_item_leaving_the_game_is_not_a_nerf_and_items_keep_half():
    net, vol = w.row_scores("Item cycled out", {"del"}, ctx={"kind": "item", "version": "7.40", "item": "x"})
    assert net == 0.0 and vol > 0
    net, vol = w.row_scores("Eternal Chains no longer deals damage", {"del"},
                            ctx={"kind": "item", "version": "7.38", "item": "gungir"})
    assert net == -round(vol * 0.5, 3)


def test_a_number_in_a_del_row_does_not_turn_it_into_minus_100_percent():
    """Rejected: "a number -> 0 = -100%" put 38 of 50 rows above the 95th percentile of hero nerfs."""
    a, _ = w.row_scores("Aghanim's Shard no longer decreases cooldown by 10s", {"del"}, ctx=dict(HERO, shard=True))
    assert abs(a) < 1.0


def test_a_neutral_item_entering_the_pool_is_not_a_buff():
    net, vol = w.row_scores("Now is a Tier 1 Neutral Artifact", {"new"},
                            ctx={"kind": "item", "version": "7.38", "item": "occult_bracelet"})
    assert net == 0.0 and vol > 0


def test_an_item_debut_scores_zero_net():
    net, vol = w.row_scores("+10 Strength", {"new"}, ctx={"kind": "item", "version": "7.38", "item": "orb_of_frost"})
    assert net == 0.0 and vol > 0
