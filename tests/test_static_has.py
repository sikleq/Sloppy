"""Perf guard: patch pages must not depend on CSS :has() (12-20k elements; each lazily
inserted row re-matched every :has() -> 4-5 s of style recalc per scroll of 7.38/7.41).
The facts are written as classes at build time by patch/static_has.py."""
import os
import re

from patch.static_has import add_static_has_classes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# :has() left on purpose: anchored on pages that are NOT patch / Changes pages
_ALLOWED = ("body:has(.creeps", "html:has(.main-page)", ".back-to-top:has(+ .dyn-w-fab)",
            ".cal-year-block:has(", ".creeps-scroll:has(", ".aoe-table", "(body:has(.creeps-scroll)",
            ".aoe-ico-wrap:hover")


def test_no_has_selectors_on_patch_page_elements():
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    bad = [ln.strip()[:100] for ln in css.splitlines()
           if ":has(" in ln and not any(a in ln for a in _ALLOWED)]
    assert not bad, "move these :has() facts to patch/static_has.py classes: " + "; ".join(bad)


def test_static_classes():
    html = ('<ul class="changes"><li data-tag="buff"><span class="row-tag-empty"></span>'
            '<span class="row-text">x <span class="badge-group">+1</span></span></li>'
            '<li><span class="badge-group">1</span><div class="formula-table"></div></li></ul>'
            '<div class="ability-block"><h4>t</h4></div>'
            '<div class="ability-block"><ul class="changes"><li><span class="row-text">y</span></li></ul></div>'
            '<div class="ability-change unified-panes"><div><div class="formula-table-wrap"></div></div></div>')
    out = add_static_has_classes(html)
    lis = re.findall(r"<li([^>]*)>", out)
    assert 'class="li-notag"' in lis[0] and "li-bg" not in lis[0]      # badge-group only nested there
    assert all(c in lis[1] for c in ("li-notext", "li-bg", "li-formula"))
    assert out.count("ab-empty") == 1
    assert "has-formula-wrap" in out


def test_new_mechanic_rows_drop_only_the_new_chip():
    from patch.page import _new_mech_rows
    html = ('<ul class="changes"><!--NEWMECH--><li data-tag="buff new"><span class="badge new" data-tag="new">NEW</span>'
            '<span class="row-text">a</span></li><li data-tag="misc"><span class="badge misc" data-tag="misc">MISC</span>'
            '<span class="row-text">b</span></li></ul><ul class="changes"><li data-tag="new"><span class="badge new">NEW</span></li></ul>')
    out = _new_mech_rows(html)
    assert "<!--NEWMECH-->" not in out
    assert out.count('<span class="row-tag-empty"></span>') == 1        # only the NEW row in the marked list
    assert 'class="mech-desc mech-first mech-last"' in out               # one-row description box
    assert ">MISC<" in out and out.count(">NEW<") == 1                  # unmarked list keeps its chip
