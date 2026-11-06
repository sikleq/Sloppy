"""The site's name and logo (owner 2026-11-05): s/kle, the avatar at the header's left edge, the tab icons."""
import pathlib
import re

from patch import site_common

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_the_header_says_s_kle_with_the_avatar():
    html = site_common.nav_html("main") if hasattr(site_common, "nav_html") else ""
    src = (ROOT / "patch" / "site_common.py").read_text(encoding="utf-8")
    assert src.count("{BRAND_HTML}") == 2 and src.count("icons/logo_sikle.png") == 2 and "dota.vpk" not in src
    assert re.sub(r"<[^>]+>", "", site_common.BRAND_HTML) == "s/kle"
    assert (ROOT / "icons" / "logo_sikle.png").exists()
    del html


def test_no_page_title_keeps_the_old_name():
    for folder in ("patch", "builders"):
        for f in (ROOT / folder).glob("*.py"):
            assert "<title>SIKLE" not in f.read_text(encoding="utf-8"), f.name


def test_the_logo_meets_the_header_edges():
    css = (ROOT / "src" / "css" / "nav.css").read_text(encoding="utf-8")
    assert "height: var(--site-nav-h, 76px);" in css and "margin: -7px 0 -3px -10px;" in css


def test_the_tab_icons_are_the_new_ones():
    import pytest
    pytest.importorskip("PIL")                            # CI has no Pillow
    from PIL import Image
    fav = ROOT / "icons" / "favicon"
    for name, size in (("favicon-32x32.png", 32), ("apple-touch-icon.png", 180), ("web-app-manifest-512x512.png", 512)):
        assert Image.open(fav / name).size == (size, size)
    assert '"name": "s/kle"' in (fav / "site.webmanifest").read_text(encoding="utf-8")


def test_a_title_joins_the_name_with_a_dash():
    for folder in ("patch", "builders"):
        for f in (ROOT / folder).glob("*.py"):
            text = f.read_text(encoding="utf-8")
            assert "<title>s/kle | " not in text, f.name
    assert "<title>s/kle - Patch {version}</title>" in (ROOT / "patch" / "page.py").read_text(encoding="utf-8")
