"""A hero's GENERAL whose only rows a card below already shows is hidden, not an empty box (owner 2026-11-27,
7.42 Nyx Assassin: "в General пустота")."""
from patch.general_rows import hide_general_all_covered

_HEAD = ('<h4 class="subgroup">GENERAL</h4><div class="ability-block other-block"><div class="ability-icon-wrap">'
         '<img src="../icons/other.svg" alt=""></div><ul class="changes">\n')


def test_general_with_only_covered_rows_is_hidden():
    html = (_HEAD + '<li data-tag="del nerf" class="iab-covered covered-card"><span class="badge del">DEL</span>'
            '<span class="row-text">Removed Mana Burn Innate ability</span></li>\n</ul>\n</div>')
    out = hide_general_all_covered(html)
    assert '<h4 class="subgroup all-covered">GENERAL</h4>' in out
    assert 'other-block all-covered' in out
    assert 'Removed Mana Burn Innate ability' in out      # kept for tag filters and weights


def test_general_with_a_shown_row_stays():
    html = (_HEAD + '<li data-tag="del nerf" class="iab-covered covered-card">x</li>\n'
            '<li data-tag="buff">Base Armor increased</li>\n</ul>\n</div>')
    assert hide_general_all_covered(html) == html


def test_css_hides_the_marked_general():
    from pathlib import Path
    css = (Path(__file__).resolve().parent.parent / "src" / "css" / "pixel-skin-filters.css").read_text(encoding="utf-8")
    assert "h4.subgroup.all-covered, .ability-block.other-block.all-covered { display: none !important; }" in css
