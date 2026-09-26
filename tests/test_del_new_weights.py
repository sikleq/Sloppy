"""Owner 2026-09-27: DEL / NEW row weights (blind judge 200 rows + devil's advocate + pro adoption)."""
from patch import weights as w

HERO = {"kind": "hero", "version": "7.38", "hero": "dazzle"}


def test_whole_ability_or_facet_removed_weighs_like_a_numberless_nerf():
    net, _ = w.row_scores("Removed Bad Juju ability", {"del"}, ctx=HERO)
    assert net == -round(w.weight_of("other") * w.WHOLE_W, 3)


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
