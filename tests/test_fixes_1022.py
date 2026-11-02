"""Content fixes of 2026-10-22 (owner's 7.41 review): the old -> new arrow already names the replaced ability."""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _calls(path, name):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.split("\n")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
            yield node, lines


def _kw(node, name):
    return next((k.value for k in node.keywords if k.arg == name), None)


def _rows_after(node, lines):
    """The li() lines of the list right under a card."""
    k = node.end_lineno
    while k < len(lines) and lines[k].strip() in ("))", ")", ""):
        k += 1
    if k >= len(lines) or "ul_open" not in lines[k]:
        return []
    out = []
    k += 1
    while k < len(lines) and "ul_close" not in lines[k]:
        out.append(lines[k])
        k += 1
    return out


def _name(side):
    if isinstance(side, ast.Call):
        v = _kw(side, "name")
        if isinstance(v, ast.Constant):
            return v.value
    return None


def test_no_summary_names_the_replaced_ability():
    # Beastmaster 7.41 "Inner Beast is now the innate ability (replaces Rugged)."
    bad = []
    for f in sorted((ROOT / "content").glob("p*.py")):
        for node, _ in _calls(f, "ability_change"):
            s = _kw(node, "summary")
            if isinstance(s, ast.Constant) and ("replaces" in s.value or "removed;" in s.value):
                bad.append(f"{f.name}:{node.lineno} {s.value}")
    assert not bad, bad


def test_no_rename_row_under_an_arrow_header():
    # Dark Seer 7.41 "Aggrandize renamed to Quick Wit" under the Aggrandize -> Quick Wit card
    bad = []
    for f in sorted((ROOT / "content").glob("p*.py")):
        for node, lines in _calls(f, "ability_change"):
            old, new = _name(_kw(node, "old")), _name(_kw(node, "new"))
            if old and new and old != new:
                bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if "renamed to" in r]
        for node, lines in _calls(f, "ability"):
            if _kw(node, "old_title") is not None:
                bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if "renamed to" in r]
        # a renamed item gets the arrow too (owner 2026-10-22, Blight Stone -> Orb of Blight 7.38)
        for node, lines in _calls(f, "item_header"):
            name = node.args[0].value if node.args and isinstance(node.args[0], ast.Constant) else None
            bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if name and f"renamed to {name}" in r]
    assert not bad, bad


def test_renamed_item_header_shows_old_arrow_new():
    from patch import elements as el
    html = el.item_header("Orb of Blight", old_title="Blight Stone")
    assert ('<span class="ability-title-old">Blight Stone</span><span class="ability-title-arrow">→</span>'
            '<a class="entity-link"') in html


def _ability_audit():
    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_abilities", ROOT / "scripts" / "audit" / "audit_abilities.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ability_audit_ignores_sub_ability_slugs():
    # audit-live 2026-10-22 failed: sub_ability("rattletrap_jetpack", "Jetpack") was read as ability("rattletrap_jetpack").
    # A stub of Valve's answer: this test ran the live audit, so it failed offline and on any rename on Valve's side
    # (.github/workflows/audit-live.yml runs that one)
    a = _ability_audit()
    src = 'W(hero_header("Clockwerk"))\nW(sub_ability("rattletrap_jetpack", "Jetpack"))\nW(ability("Cogs"))\n'
    calls = a.find_calls([("p9.py", src)])
    assert [c[:2] for c in calls] == [("Clockwerk", "Cogs")]
    assert a.find_problems(calls, {"Clockwerk": {"rattletrap_cogs": "Cogs"}}) == []
    assert a.report([]) == 0


def test_ability_audit_still_reports_a_renamed_ability_and_a_bad_slug(capsys):
    a = _ability_audit()
    src = 'W(hero_header("Axe"))\nW(ability("Old Name", slug="axe_x"))\nW(ability("Lost", slug="axe_lost"))\n'
    problems = a.find_problems(a.find_calls([("p9.py", src)]), {"Axe": {"axe_x": "New Name"}})
    assert [p[6] for p in problems] == ["renamed -> 'New Name'", "slug not in hero's ability list"]
    assert a.report(problems) == 1
    assert "[Axe] 'Old Name' -> 'New Name'" in capsys.readouterr().out


def test_ability_audit_owner_of_a_card_is_the_header_of_its_own_file():
    # Tormentor's cards at the top of p738.py were blamed on the previous file's last hero, Windranger
    a = _ability_audit()
    calls = a.find_calls([("p1.py", 'W(hero_header("Windranger"))\n'),
                          ("p2.py", 'W(ability_change(old=dict(name="A"), new=dict(name="B")))\n')])
    assert calls == []


def test_the_ability_audit_imports_without_the_network():
    assert _ability_audit().HEROLIST.startswith("https://")


def test_a_test_cannot_reach_the_network(no_network):
    from urllib.request import urlopen
    with pytest.raises(OSError):
        urlopen("https://www.dota2.com/", timeout=1)
    assert no_network == ["www.dota2.com"]
    no_network.clear()          # the guard's teardown would fail this test


def test_audit_live_still_runs_the_ability_audit():
    assert "audit_all.py" in (ROOT / ".github" / "workflows" / "audit-live.yml").read_text(encoding="utf-8")
    assert "audit_abilities.py" in (ROOT / "scripts" / "audit" / "audit_all.py").read_text(encoding="utf-8")


def test_quick_wit_card_highlights_the_new_attack_speed():
    import pytest
    page = ROOT / "dist" / "patches" / "7.41.html"
    if not page.exists():
        pytest.skip("site not built")
    html = page.read_text(encoding="utf-8")
    assert '<span class="iab-hl iab-hl-new">Also provides Dark Seer with' in html
    assert "Aggrandize renamed to Quick Wit" not in html


def _from_audit():
    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_from_values", ROOT / "scripts" / "audit" / "audit_from_values.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_from_value_audit_reads_heads_and_facet_values():
    a = _from_audit()
    assert a._norm("20/18/16/14") == (20, 18, 16, 14) and a._norm("14/14/14") == (14,)
    assert a._known((14, 16, 18, 20), {(14, 16, 18, 20, 20)})         # Valve lists 4 of the KV's 5 levels
    assert not a._known((20, 18, 16, 14), {(20, 17, 14, 11)})


def test_from_value_audit_catches_a_stale_value_and_reads_game_names(tmp_path, monkeypatch):
    # Valve's 7.41 Kinetic Fence row without the wrong-word mark; the hero's page id has a hyphen
    # (ancient-apparition) and an item's differs from the game's name (battle-fury = bfury): the header icon names it
    a = _from_audit()
    row = ('<li><span class="row-text">Cooldown decreased from 20/18/16/14s to 14s</span></li>')
    page = ('<div class="entity hero-entity" id="dyn-hero-disruptor"><div class="entity-icon hero-icon">'
            '<img src="../icons/_t/heroes/disruptor.webp"></div></div><h4 class="subgroup">Abilities</h4>'
            '<div class="ability-block"><div class="ability-icon-wrap"><img alt="Kinetic Fence" '
            'class="ability-icon-img" data-slug="disruptor_kinetic_fence"></div><ul class="changes">' + row + '</ul></div>')
    (tmp_path / "7.41.html").write_text(page, encoding="utf-8")
    monkeypatch.setattr(a, "PAGES", tmp_path)
    assert [r[2] for r in a.audit_page("7.41", "7.40c")] == ["disruptor_kinetic_fence"]
    ctx = a._contexts('<div class="entity item-entity" id="dyn-item-battle-fury"><div class="entity-icon item-icon">'
                      '<img src="../icons/_t/items/bfury.webp"></div></div>')
    assert ctx[-1][1] == ("item", "bfury")


@pytest.mark.slow
def test_every_from_value_matches_the_previous_patch():
    # owner 2026-10-22: Valve's "from" can be stale (7.41 Kinetic Fence quoted pre-7.38 20/18/16/14s);
    # such rows carry wrong-word + the real change in a note
    import pytest
    if not (ROOT / "dist" / "patches" / "7.41.html").exists():
        pytest.skip("site not built")
    a = _from_audit()
    vers = a._versions()
    found = [r for v in vers[1:] for r in a.audit_page(v, vers[vers.index(v) - 1])]
    assert found == []


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
