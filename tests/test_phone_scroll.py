"""A phone's scroll must not redraw the page's card lines (owner 2026-11-20: "сайт на телефоне очень лагает,
прокрутка — фриз на 3 секунды"). Its address bar hides and shows as it scrolls: a resize of the height only. Each one
redrew every connector of the page (155 ms on a computer for 7.42, seconds on a phone)."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_connectors_redraw_only_on_a_new_width_and_once_it_settles():
    js = (ROOT / "src" / "js" / "patch-page.js").read_text(encoding="utf-8")
    assert not re.search(r"addEventListener\('resize',\s*draw(?:AbilityChange|Brewling)Connectors\)", js)
    assert "window.innerWidth === lastW" in js and "setTimeout(window.sloppyDrawConnectors" in js


def test_a_phone_has_no_blur_under_the_sticky_header():
    css = (ROOT / "src" / "css" / "phones.css").read_text(encoding="utf-8")
    block = css[css.index("@media (max-width: 760px)"):]
    assert "nav.top-nav { backdrop-filter: none;" in block
