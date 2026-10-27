"""A hero's innate ability block comes first, before the basic abilities (docs/agent-rules/entity-rendering.md:
stats > innates > facets > abilities > talents) — owner 2026-10-16, 7.41 Invoke / Feast / Minefield Sign stood after
Quas / Rage / Proximity Mines. Innate = "Innate" "1" in THAT patch's KV, not today's flag."""
import glob
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import tools.generate_patch_code_v2 as g  # noqa: E402


def _ids():
    return {slug: aid for aid, (_name, slug) in g.ABILS.items()}


def test_generator_puts_the_innate_first():
    ids = _ids()
    if "invoker_invoke" not in ids or not g.innate_slugs_of("7.41"):
        pytest.skip("ability ids / 7.41 hero KV not in this checkout")
    hero = {"hero_id": 74, "abilities": [
        {"ability_id": ids["invoker_quas"], "ability_notes": [{"note": "Max Level increased from 7 to 8"}]},
        {"ability_id": ids["invoker_invoke"], "ability_notes": [{"note": "Now X"}]}]}
    blocks = [l for l in g._render_hero(hero, version="7.41") if l.startswith("W(ability(")]
    assert blocks[0].startswith('W(ability("Invoke"')


def test_an_innate_the_patch_demotes_keeps_its_place():
    ids = _ids()
    if "life_stealer_feast" not in ids or not g.innate_slugs_of("7.41"):
        pytest.skip("ability ids / 7.41 hero KV not in this checkout")
    # 2026-10-21: the 7.41 snapshot is now the patch's build (6728) — Feast is no longer innate there, Ghoul Frenzy is
    assert "life_stealer_feast" not in g.innate_slugs_of("7.41")
    assert "life_stealer_ghoul_frenzy" in g.innate_slugs_of("7.41")
    hero = {"hero_id": 54, "abilities": [
        {"ability_id": ids["life_stealer_rage"], "ability_notes": [{"note": "Cooldown decreased"}]},
        {"ability_id": ids["life_stealer_feast"], "ability_notes": [{"note": "Now is a basic ability"}]}]}
    blocks = [l for l in g._render_hero(hero, version="7.41") if l.startswith("W(ability(")]
    assert blocks[0].startswith('W(ability("Rage"')


def test_innate_flag_is_the_patchs_own():
    if not g.innate_slugs_of("7.41d") or not g.innate_slugs_of("7.38"):
        pytest.skip("hero KV not in this checkout")
    assert "brewmaster_liquid_courage" in g.innate_slugs_of("7.41d")
    assert "invoker_quas" not in g.innate_slugs_of("7.41")


_HEADS = re.compile(r'^\s*W\((?:item_header|unit_header|section|plain_header)\(')
_AB = re.compile(r'^\s*W\(ability\("([^"]+)"(.*)\)\)')
_LOC = None


def _names():
    global _LOC
    if _LOC is None:
        path = os.path.join(ROOT, "data", "abilities_english.txt")
        _LOC = dict(re.findall(r'"DOTA_Tooltip_ability_([a-z0-9_]+)"\s+"([^"]+)"',
                               open(path, encoding="utf-8", errors="replace").read())) if os.path.exists(path) else {}
    return _LOC


# 7.38 Drow Ranger: Valve's notes call Vantage Point the innate, the KV flags Precision Aura — left for the owner
_KNOWN = {("p738.py", "Drow Ranger")}


@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(ROOT, "content", "p7*.py"))))
def test_no_innate_after_a_basic_ability(path):
    base = os.path.basename(path)
    inn = g.innate_slugs_of("7." + base[2:-3])
    if not inn:
        pytest.skip("no per-hero KV for this patch")
    by_name = {_names().get(s, ""): s for s in inn}
    hero, seen, bad = None, None, []
    lines = open(path, encoding="utf-8").read().split("\n")

    def demoted(i):
        """The ability block starting at line i says it stops being innate (g.INNATE_DEMOTED)."""
        for line in lines[i + 1:i + 40]:
            if _AB.match(line) or re.match(r'^\s*W\((?:subgroup|hero_header)\(', line):
                return False
            if g.INNATE_DEMOTED.search(line):
                return True
        return False
    for n, line in enumerate(lines, 1):
        m = re.match(r'^\s*W\(hero_header\("([^"]+)"', line)
        if m:
            hero, seen = m.group(1), None
            continue
        if _HEADS.match(line):
            hero = None
            continue
        m = _AB.match(line)
        if not (m and hero) or (base, hero) in _KNOWN:
            continue
        slug = re.search(r'slug="([^"]+)"', m.group(2))
        if ((slug and slug.group(1) in inn) or m.group(1) in by_name) and not demoted(n - 1):
            if seen:
                bad.append(f"{base}:{n} {hero}: {m.group(1)} after {seen}")
        elif not seen:
            seen = m.group(1)
    assert not bad, bad
