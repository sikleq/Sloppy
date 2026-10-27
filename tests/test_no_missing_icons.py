"""No page of the built site shows the "?" placeholder or points at an image that isn't there (owner 2026-10-27: 7.38b
Venomous Volley had no icon — a facet's hidden passive without art of its own, drawn now as its facet; three innates
without art inside Aghanim's cards pointed at absent files). CI builds dist/ before the tests; without it: skip."""
import os
import re

import pytest

from patch.elements import sub_ability

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
REF = re.compile(r'(?:src|data-full|data-small)="([^"#?:]+\.(?:png|webp|jpg|svg|gif))(?:\?[^"]*)?"')


def _pages():
    if not os.path.isdir(os.path.join(DIST, "patches")):
        pytest.skip("no built site (python build_site.py)")
    for sub in ("patches", "heroes", "items", "units"):
        d = os.path.join(DIST, sub)
        for name in (os.listdir(d) if os.path.isdir(d) else []):
            if name.endswith(".html"):
                yield os.path.join(d, name)


def test_no_page_points_at_an_absent_image_or_draws_the_placeholder():
    absent, placeholder = set(), set()
    for page in _pages():
        with open(page, encoding="utf-8", errors="replace") as f:
            t = f.read()
        for ref in REF.findall(t):
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(page), ref))):
                absent.add(f"{os.path.basename(page)}: {ref}")
        placeholder |= {f"{os.path.basename(page)}: {s}"
                        for s in re.findall(r'icons/misc/missing\.svg"[^>]*data-slug="([^"]+)"', t)}
    assert not absent, sorted(absent)[:20]
    assert not placeholder, sorted(placeholder)[:20]


def test_an_ability_without_art_in_a_card_gets_the_innate_icon_at_once():
    html = sub_ability("silencer_brain_drain", "Brain Drain")
    assert 'src="../icons/misc/innate_icon.png"' in html
