"""Enchantments as tier tables, before -> after (owner 2026-10-17, 7.41: "Vital is written as a bare row… a table? a
card? Mystical / Crude too" -> variant A: the 7.38 table under each enchantment, a changed cell "was → now")."""
import glob
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts", "gen"))
from patch import elements as e  # noqa: E402


def test_tier_specs_and_cells():
    import enchant_table as et
    assert et._tiers("4/5") == [4, 5] and et._tiers("2-4") == [2, 3, 4] and et._tiers("5") == [5]
    up = e._ench_cell("+12%", "+16%", False, False)
    assert 'class="iab-lv iab-buff badge buff' in up and '+33%' in up and '">+16%</span>' in up
    worse = e._ench_cell("−5%", "−6%", True, False)                                          # a bigger penalty
    assert 'class="iab-lv iab-nerf badge nerf' in worse and '">−6%</span>' in worse
    assert 'class="iab-lv iab-new">+10%' in e._ench_cell(None, "+10%", False, False)          # a tier it has now
    assert 'class="iab-lv iab-nerf">−10%' in e._ench_cell(None, "−10%", True, False, True)    # a whole new penalty
    assert 'class="iab-lv iab-del">+40%' in e._ench_cell("+40%", None, False, False)          # a tier it lost
    assert "ench-zero" in e._ench_cell(None, "0", False, False) and "ench-off" in e._ench_cell(None, None, False, False)
    assert e._ench_cell(None, "+2", False, True) == '<span class="ench-v">+2</span>'          # a new enchantment


def test_every_patch_with_enchant_changes_has_its_tables():
    # every patch, not only the ones with tier boxes: the tiers come from the game's neutral_items.txt (owner
    # 2026-10-26: 7.39 "Enchantment Changes" as tables like 7.41, "сделать везде так")
    with open(os.path.join(ROOT, "data", "rules", "enchant_tables.json"), encoding="utf-8") as f:
        have = json.load(f)
    for path in glob.glob(os.path.join(ROOT, "content", "p*.py")):
        src = open(path, encoding="utf-8").read()
        changed = [m for m in re.findall(r'enchant_header\("([^"]+)"([^)]*)\)', src) if "removed=" not in m[1]]
        if "enchant_tier_box(" in src or changed:
            code = os.path.basename(path)[1:-3]
            ver = f"{code[0]}.{code[1:3]}{code[3:]}"
            assert ver in have, f"run: python scripts/gen/enchant_table.py {ver}"
            for name, _ in changed:
                assert have[ver].get(name, {}).get("stats"), f"{ver} {name}: no table"
    crude = have["7.41"]["Crude"]
    assert crude["tiers_old"] == [4, 5] and crude["tiers_new"] == [2, 3, 4]
    bat = next(s for s in crude["stats"] if s["key"] == "bat_reduce")
    assert bat["new"] == {"2": "+8%", "3": "+12%", "4": "+16%"}          # 7.41, not the 7.41a 6/9/12 (CORRECTIONS)


def _page():
    p = os.path.join(ROOT, "dist", "patches", "7.41.html")
    if not os.path.exists(p):
        pytest.skip("site not built")
    return open(p, encoding="utf-8").read()


def _block(html, slug):
    i = html.index(f'id="dyn-enchant-{slug}"')
    return html[i:html.find('class="entity ', i + 50)]


def test_7_41_enchantments_show_tables_and_keep_only_word_rows():
    html = _page()
    assert html.count('class="ench-tiers ench-change"') == 19
    crude = _block(html, "crude")
    # the new value dotted with its % on hover / tap, in that %'s shade (owner 2026-10-17)
    assert re.search(r'<span class="ench-was">\+30%</span><span class="ench-arrow">→</span><span class="iab-lv iab-nerf '
                     r'badge nerf\d tone"><span class="iab-hint abil-ico-hint" data-tooltip="[^"]*-33%[^"]*">\+20%</span>',
                     crude)
    assert '<span class="iab-lv iab-del">+40%</span>' in crude and '<span class="iab-lv iab-new">+10%</span>' in crude
    shown = [re.sub(r"<[^>]+>", "", m.group(2)) for m in re.finditer(r"<li\b([^>]*)>(.*?)</li>", crude, re.S)
             if "iab-covered" not in m.group(1)]
    assert len(shown) == 2 and any("guaranteed" in s for s in shown) and any("incoming healing" in s for s in shown)
    vital = _block(html, "vital")
    assert '<span class="ench-v">+2</span>' in vital and 'class="iab-covered covered-ench"' in vital
    mystical = _block(html, "mystical")
    assert 'class="ench-stat ench-gone">Cast Range' in mystical and "None" not in mystical


def test_tables_have_lines_between_cells_and_centred_values():
    # owner 2026-10-17: "все таблицы оформляются с вертикальными линиями-разделителями между ячейками, а значения
    # стоят центрировано"
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    rule = css.split(".ench-change .ench-v, .ench-change .ench-tier-h {", 1)[1].split("}", 1)[0]
    assert "border-left: 1px solid" in rule and "justify-content: center" in rule
    assert "row-gap: 0" in css.split(".ench-tiers.ench-change {", 1)[1].split("}", 1)[0]


def test_the_filters_know_the_table():
    js = open(os.path.join(ROOT, "src", "scripts.js"), encoding="utf-8").read()
    assert "el.classList.contains('ench-change') ? 'covered-ench'" in js
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    assert "html.cb-mode .iab-lv.iab-del" in css or "html.cb-mode" in css and ".iab-lv.iab-del" in css
