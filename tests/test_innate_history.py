"""Which ability was each hero's innate in every patch (tools/build_innate_history.py, owner 2026-10-21)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import build_innate_history as bih  # noqa: E402
from builders import innate_rules as ir  # noqa: E402

# snapshots taken from a build before their own patch (7.41: build 6726, the patch is 6728). Refetching them from
# the patch's build shrinks this list; a NEW one means a fresh snapshot came from a build before its patch.
KNOWN_LAGGED = {"7.35b", "7.36b", "7.37c", "7.39b", "7.41", "7.41b"}


def _history():
    with open(bih.OUT, encoding="utf-8") as f:
        return json.load(f)


def _innates_at(rows, v):
    cur = None
    for r in rows:
        if ir._vkey(r["since"]) <= ir._vkey(v):
            cur = set(r["innates"])
    return cur


def test_the_history_file_is_fresh():
    assert bih.main(["--check"]) == 0, "python tools/build_innate_history.py"


def test_no_new_snapshot_was_taken_before_its_patch():
    lag = set(_history()["lagged"])
    assert lag <= KNOWN_LAGGED, f"taken before their patch (refetch from the patch's build): {sorted(lag - KNOWN_LAGGED)}"


def test_the_early_innates_and_known_changes():
    h = _history()["heroes"]
    assert h["ogre_magi"][0] == {"since": "7.33", "innates": ["ogre_magi_dumb_luck"], "source": "notes"}
    assert h["treant"][0]["since"] == "7.23c"
    assert _innates_at(h["luna"], "7.36") == {"luna_selemenes_favor"}
    assert _innates_at(h["luna"], "7.37") == {"luna_lunar_blessing"}
    assert "axe_one_man_army" in _innates_at(h["axe"], "7.41")            # 7.41 read past its lagged snapshot
    assert "axe_one_man_army" not in _innates_at(h["axe"], "7.40c")
    assert "beastmaster_inner_beast" not in _innates_at(h["beastmaster"], "7.40c")


def test_every_rule_starts_when_its_ability_is_innate():
    hist = _history()["heroes"]
    rules = ir.load()["heroes"]
    bad = []
    for slug, rule in rules.items():
        since, name = rule.get("since"), rule["innate"]
        at = _innates_at(hist.get(slug, []), since) if since else None
        if at is None or name not in at:
            bad.append(f"{slug}: {name} is not innate at the rule's since {since} (innates then: {at})")
    assert not bad, "\n".join(bad)


def test_no_effect_counts_before_its_hero_innate():
    # 2026-10-21: an effect without its own "since" counted in every patch since 7.08 (Luna's Lunar Blessing,
    # innate since 7.37); load() now starts it with the hero's innate
    from builders.heroes_stats import _active_entry
    luna = {e["target"]: e for e in ir.load()["heroes"]["luna"]["effects"]}
    assert _active_entry(luna["nvision"], "7.36") is None and _active_entry(luna["dmg"], "7.36") is None
    assert _active_entry(luna["nvision"], "7.37")["base"] == 380
    axe = ir.load()["heroes"]["axe"]["effects"][0]
    assert _active_entry(axe, "7.40c") is None and _active_entry(axe, "7.41")["factor"] == 0.5
