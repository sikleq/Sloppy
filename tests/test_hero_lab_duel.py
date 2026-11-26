"""Hero Lab Duel (src/js/hero-lab-duel.js): the rules of docs/tables.md "Hero Lab battle rules" hold in the engine.
Run in Node when it is installed (the engine has no DOM), skipped without it; the builder part runs everywhere."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src" / "js" / "hero-lab-duel.js"
NODE = shutil.which("node")

AXE = {"hp": 660, "hpr": 4, "armor": 3, "dmin": 52, "dmax": 56, "aspd": 120, "bat": 1.7, "attackPoint": 0.4,
       "melee": True}
SNIPER = {"hp": 540, "hpr": 1.5, "armor": 2, "dmin": 40, "dmax": 46, "aspd": 125, "bat": 1.7, "attackPoint": 0.17,
          "ranged": True, "range": 550, "proj": 3000}


def duel(a, b, **opts):
    if not NODE:
        pytest.skip("node is not installed")
    script = (f"const {{heroLabDuel}} = require({json.dumps(str(ENGINE))});"
              f"process.stdout.write(JSON.stringify(heroLabDuel({json.dumps(a)}, {json.dumps(b)}, {json.dumps(opts)})));")
    r = subprocess.run([NODE, "-e", script], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_a_mirror_match_is_a_coin_flip():
    res = duel(AXE, AXE, runs=4000)
    assert abs(res["sides"][0]["win"] - 0.5) < 0.04


def test_the_same_builds_give_the_same_answer():
    assert duel(AXE, SNIPER) == duel(AXE, SNIPER)


def test_block_is_16_at_half_the_hits_for_melee_only():
    """Expected hit on a melee target: 54 - 0.5 * 16 = 46 before armor; a ranged target takes the full 54."""
    bare = dict(AXE, armor=0, evasion=0)
    melee = duel(bare, dict(bare, melee=True))["sides"][0]
    ranged = duel(bare, dict(bare, melee=False, ranged=True))["sides"][0]
    venge = duel(bare, dict(bare, melee=True, noBlock=True))["sides"][0]
    tHit = 1.7 * 100 / 120
    assert melee["dps"] == pytest.approx(46 / tHit)
    assert ranged["dps"] == pytest.approx(54 / tHit) == pytest.approx(venge["dps"])


def test_full_evasion_is_never_hit():
    res = duel(AXE, dict(SNIPER, evasion=100))
    assert res["sides"][1]["win"] == 1 and res["sides"][0]["dps"] == 0


def test_regen_above_the_damage_is_a_draw():
    res = duel(dict(AXE, dmin=1, dmax=1), dict(SNIPER, dmin=1, dmax=1), maxTime=20)
    assert res["draw"] == 1 and res["sides"][0]["time"] is None


def test_the_typical_fight_ends_with_the_loser_at_zero():
    res = duel(AXE, SNIPER)
    s = res["sample"]
    loser = 1 - s["winner"]
    assert s["log"][-1][1 + loser] == 0 and s["log"][0] == [0, AXE["hp"], SNIPER["hp"]]


def test_a_slow_wind_up_loses_a_race_it_would_win_on_paper():
    """Two one-shot builds: the attack point decides who lands first (the 0.00s start is the swing, not the hit)."""
    quick = dict(AXE, hp=100, dmin=500, dmax=500, attackPoint=0.1, armor=0)
    slow = dict(quick, attackPoint=0.6)
    assert duel(quick, slow)["sides"][0]["win"] == 1


def test_the_builder_hands_the_attack_point_over():
    from builders.hero_lab import _attack_point
    raw = {"npc_dota_hero_axe": {"AttackAnimationPoint": "0.400000"}, "npc_dota_hero_base": {"AttackAnimationPoint": "0.75"},
           "npc_dota_hero_new": {}}
    assert _attack_point("npc_dota_hero_axe", raw) == 0.4
    assert _attack_point("npc_dota_hero_new", raw) == 0.75
