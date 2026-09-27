"""Owner 2026-09-27: a hero block's replacements net 0 by text (signal R gives the direction);
an Aghanim's upgrade that moved to another ability is not a loss; one removal counts once."""
from patch import elements as el
from patch.state import _State


def _cell(rows):
    saved = (_State.dynamics, _State.pending_rework, _State.cell_rows)
    try:
        _State.dynamics = {"hero|x": {"name": "X", "kind": "hero", "patches": {"7.41": {"w": sum(r[2] for r in rows)}}}}
        _State.pending_rework = None
        _State.cell_rows = {"ek": "hero|x", "pv": "7.41", "ctx": {"kind": "hero", "version": "7.41", "hero": "x"},
                            "rows": [{"text": t, "tags": set(g), "net": n, "ability": a, "whole": wh}
                                     for t, g, n, a, wh in rows]}
        el._flush_cell_rows()
        return _State.dynamics["hero|x"]["patches"]["7.41"]["w"], _State.pending_rework
    finally:
        _State.dynamics, _State.pending_rework, _State.cell_rows = saved


def test_aghs_upgrade_moved_to_a_reworked_ability_is_not_a_loss():
    w, pend = _cell([("No longer upgraded with Aghanim's Shard", {"del"}, -0.36, "x_duel", False),
                     ("Aghanim's Shard reworked: Increases radius by 100", {"rework"}, 0.0, "x_odds", False)])
    assert w == 0.0 and pend and pend["ek"] == "hero|x"


def test_a_removal_named_twice_counts_once():
    w, _ = _cell([("Ability removed", {"del"}, -0.8, "antimage_counterspell_ally", True),
                  ("Aghanim's Shard no longer provides Counterspell Ally ability", {"del"}, -0.36, "antimage_counterspell", False)])
    assert w == -0.8


def test_a_replaced_facet_asks_signal_r_for_the_direction():
    w, pend = _cell([("Removed Old Facet", {"del"}, -0.64, None, True), ("", {"new"}, 0.64, None, True)])
    assert w == 0.0 and pend is not None
