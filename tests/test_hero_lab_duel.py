"""Hero Lab Duel (src/js/hero-lab-duel.js): the rules of docs/tables.md "Hero Lab battle rules" and the items' passives
hold in the engine. Run in Node when it is installed (the engine has no DOM), skipped without it; the builder parts run
everywhere (the real items.txt ones only where the game files are laid out)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "src" / "js" / "hero-lab-duel.js"
NODE = shutil.which("node")

# a melee and a ranged hero with round numbers
AXE = {"hp": 660, "hpr": 4, "armor": 3, "dmin": 52, "dmax": 56, "aspd": 120, "bat": 1.7, "attackPoint": 0.4}
SNIPER = {"hp": 540, "hpr": 1.5, "armor": 2, "dmin": 40, "dmax": 46, "aspd": 125, "bat": 1.7, "attackPoint": 0.17,
          "ranged": True, "range": 550, "proj": 3000}
# a target that only soaks: the attacker's damage per second over 60 s of hits (compared as ratios: the first hit at
# the attack point makes the count of hits in the window a whole number)
DUMMY = {"hp": 10 ** 7, "armor": 0, "dmin": 0, "dmax": 0, "aspd": 100, "bat": 1.7, "attackPoint": 0.3}
HITTER = dict(AXE, armor=0, dmin=54, dmax=54)


def node(script):
    if not NODE:
        pytest.skip("node is not installed")
    r = subprocess.run([NODE, "-e", f"const E = require({json.dumps(str(ENGINE))});" + script],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def duel(a, b, **opts):
    return node(f"process.stdout.write(JSON.stringify(E.heroLabDuel({json.dumps(a)}, {json.dumps(b)}, {json.dumps(opts)})));")


def dps(attacker, target=DUMMY, runs=40):
    return duel(attacker, target, runs=runs)["sides"][0]["dps"]


def test_prd_constants_match_the_known_table():
    c = node("process.stdout.write(JSON.stringify([0.25, 0.3, 0.5].map(E.heroLabPrdC)));")
    assert c == pytest.approx([0.084744, 0.118949, 0.302103], abs=2e-5)


def test_a_mirror_match_is_a_coin_flip():
    res = duel(AXE, AXE, runs=4000)
    assert abs(res["sides"][0]["win"] - 0.5) < 0.04


def test_the_same_builds_give_the_same_answer():
    assert duel(AXE, SNIPER) == duel(AXE, SNIPER)


def test_hidden_block_is_16_at_half_the_hits_for_melee_only():
    melee = dps(HITTER)                                   # the dummy is melee: 54 - 0.5 * 16 = 46 a hit
    ranged = dps(HITTER, dict(DUMMY, ranged=True))
    venge = dps(HITTER, dict(DUMMY, noBlock=True))
    assert melee / ranged == pytest.approx(46 / 54, rel=0.03)
    assert venge == pytest.approx(ranged)


def test_only_the_largest_block_counts():
    """Vanguard (50 at 60%) on a melee target: the hidden 16 only matters when Vanguard does not proc."""
    vanguard = {"block": {"melee": 50, "ranged": 25, "chance": 60, "chanceHero": 0}}
    big = dict(HITTER, dmin=100, dmax=100)
    got = dps(big, dict(DUMMY, onHit=[vanguard]), runs=80) / dps(big, dict(DUMMY, ranged=True))
    # P(vanguard) 0.6 -> 50; else P(hidden) 0.5 -> 16 (independent counters): 100 - (0.6*50 + 0.4*0.5*16) = 66.8
    assert got == pytest.approx(0.668, rel=0.04)


def test_crit_multiplies_by_its_chance():
    crystalys = {"crit": {"chance": 30, "mult": 160}}
    plain, crit = dps(HITTER, dict(DUMMY, ranged=True)), dps(dict(HITTER, onHit=[crystalys]), dict(DUMMY, ranged=True))
    assert crit / plain == pytest.approx(1 + 0.3 * 0.6, rel=0.03)


def test_armor_corruption_raises_the_damage():
    blight = {"corrupt": {"armor": 2, "dur": 3}}
    target = dict(DUMMY, armor=5, ranged=True)
    assert dps(dict(HITTER, onHit=[blight]), target) / dps(HITTER, target) == pytest.approx(
        (1 - 0.06 * 3 / 1.18) / (1 - 0.06 * 5 / 1.3), rel=0.01)


def test_a_poison_hurts_through_magic_resistance():
    venom = {"dot": {"dps": 12, "dur": 3, "magic": True, "cd": 0}}
    target = dict(DUMMY, hp=300, mr=25, ranged=True)
    plain, poisoned = duel(HITTER, target), duel(dict(HITTER, onHit=[venom]), target)
    assert poisoned["sides"][0]["time"] < plain["sides"][0]["time"]


def test_a_bash_stun_costs_the_target_its_attacks():
    basher = {"bash": {"melee": 100, "ranged": 100, "dmg": 0, "stun": 1.2, "cd": 2.3}}
    victim = dict(AXE, hp=10 ** 7, armor=0)
    free = duel(dict(DUMMY), victim, runs=20)["sides"][1]["dps"]
    bashed = duel(dict(DUMMY, aspd=300, dmin=1, dmax=1, onHit=[basher]), victim, runs=20)["sides"][1]["dps"]
    assert bashed < free * 0.6


def test_mana_break_needs_mana():
    diffusal = {"manaBreak": {"mana": 40, "dmgPer": 1}}
    with_mana = dps(dict(HITTER, onHit=[diffusal]), dict(DUMMY, mp=10 ** 6, ranged=True))
    no_mana = dps(dict(HITTER, onHit=[diffusal]), dict(DUMMY, mp=0, ranged=True))
    plain = dps(HITTER, dict(DUMMY, ranged=True))
    assert with_mana / plain == pytest.approx(94 / 54) and no_mana == pytest.approx(plain)


def test_full_evasion_is_never_hit_but_a_pierce_proc_goes_through():
    mkb = {"pierce": {"chance": 80, "dmg": 70}}
    target = dict(SNIPER, evasion=100)
    assert duel(AXE, target)["sides"][1]["win"] == 1
    assert duel(dict(AXE, onHit=[mkb]), target)["sides"][0]["dps"] > 0


def test_echo_strike_adds_attacks_for_melee_only():
    echo = {"echo": {"cd": 5}}
    melee = dps(dict(HITTER, onHit=[echo]), dict(DUMMY, ranged=True)) / dps(HITTER, dict(DUMMY, ranged=True))
    ranged = dps(dict(SNIPER, onHit=[echo]), DUMMY) / dps(SNIPER, DUMMY)
    assert melee > 1.15 and ranged == pytest.approx(1)


def test_regen_above_the_damage_is_a_draw():
    res = duel(dict(AXE, dmin=1, dmax=1), dict(SNIPER, dmin=1, dmax=1), maxTime=20)
    assert res["draw"] == 1 and res["sides"][0]["time"] is None


def test_the_typical_fight_ends_with_the_loser_at_zero():
    s = duel(AXE, SNIPER)["sample"]
    assert s["log"][-1][2 - s["winner"]] == 0 and s["log"][0] == [0, AXE["hp"], SNIPER["hp"]]


def test_a_slow_wind_up_loses_a_race_it_would_win_on_paper():
    """Two one-shot builds: the attack point decides who lands first (the 0.00s start is the swing, not the hit)."""
    quick = dict(AXE, hp=100, dmin=500, dmax=500, attackPoint=0.1, armor=0)
    assert duel(quick, dict(quick, attackPoint=0.6))["sides"][0]["win"] == 1


def test_the_builder_hands_the_attack_point_over():
    from builders.hero_lab import _attack_point
    raw = {"npc_dota_hero_axe": {"AttackAnimationPoint": "0.400000"}, "npc_dota_hero_base": {"AttackAnimationPoint": "0.75"},
           "npc_dota_hero_new": {}}
    assert _attack_point("npc_dota_hero_axe", raw) == 0.4
    assert _attack_point("npc_dota_hero_new", raw) == 0.75


def test_the_builder_reads_the_passives_from_the_kv_keys():
    from builders.hero_lab import _item_on_hit
    assert _item_on_hit({"crit_chance": "30", "crit_multiplier": "160", "bonus_damage": "32"}) == {
        "crit": {"chance": 30, "mult": 160}}
    venom = _item_on_hit({"damage": "12", "tick_interval": "1.0", "poison_duration": "3.0", "AbilityCooldown": "9"})
    assert venom == {"dot": {"dps": 12, "dur": 3, "magic": True, "cd": 9}}
    hydra = _item_on_hit({"damage": "25", "poison_duration": "3", "poison_damage_per_second": "2.5"})
    assert hydra["dot"]["dps"] == 2.5                     # its `damage` is attack damage, not the poison
    basher = _item_on_hit({"bash_chance_melee": "25", "bash_chance_ranged": "10", "bash_duration": "1.2",
                           "bash_cooldown": "2.3", "bonus_chance_damage": "100"})
    assert basher == {"bash": {"melee": 25, "ranged": 10, "dmg": 100, "stun": 1.2, "cd": 2.3}}
    assert "pierce" not in basher                         # Skull Basher's bonus_chance_damage is the bash's
    assert _item_on_hit({"bonus_chance": "80", "bonus_chance_damage": "70"}) == {"pierce": {"chance": 80, "dmg": 70}}
    assert _item_on_hit({"corruption_armor": "-6", "corruption_duration": "7.0"}) == {"corrupt": {"armor": 6, "dur": 7}}
    assert _item_on_hit({"block_damage_melee": "50", "block_damage_ranged": "25", "block_chance": "60"})["block"] == {
        "melee": 50, "ranged": 25, "chance": 60, "chanceHero": 0}
    assert _item_on_hit({"AbilityCooldown": "19", "passive_cooldown": "5"}, echo=True) == {"echo": {"cd": 5}}
    assert _item_on_hit({"bonus_damage": "20", "bonus_strength": "15"}) == {}


@pytest.mark.skipif(not any((ROOT / "data" / "stats").glob("*/items.txt")), reason="game files not laid out")
def test_orb_of_venom_is_poison_not_attack_damage():
    """Hero Lab counted Orb of Venom's `damage` (its poison per second) as +12 attack damage."""
    from builders import hero_lab
    try:
        items = {i["id"]: i for i in hero_lab._load_items(hero_lab._versions()[-1])}
    except FileNotFoundError:
        pytest.skip("game files not laid out")
    venom = items.get("item_orb_of_venom")
    if not venom:
        pytest.skip("Orb of Venom is not in this patch's shop")
    assert venom["bonus"]["damage"] == 0 and venom["onHit"]["dot"]["dps"] == 12
