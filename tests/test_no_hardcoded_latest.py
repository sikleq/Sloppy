"""A new patch needs no version typed into code (owner 2026-10-21: «чтобы руками не надо было ничего менять»).

The Terrain link / index tile find the newest Terrain page; fetch / gen scripts take the version as an argument or
read the newest patch from patch/meta.py RELEASE_HISTORY — never a default like "7.41"."""
import glob
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from builders import site_common as site
from builders import terrain


def test_terrain_link_is_the_newest_terrain_page():
    newest = terrain.page_patches()[0][0]
    assert site.latest_terrain_href() == f"terrain_{newest.replace('.', '')}.html"
    html = site.render_materials_subnav("terrain_stats")
    assert f'href="{site.latest_terrain_href()}">Terrain</a>' in html and site.TERRAIN_LATEST not in html


def test_terrain_fallback_shows_the_newest_map_picture():
    img = terrain._newest_map_img()
    assert os.path.exists(os.path.join(_ROOT, img)) and not img.endswith("_2k.webp")


def test_scripts_hold_no_latest_patch_default():
    bad = []
    pats = (re.compile(r'sys\.argv\[[^\]]*\]\s*(?:or|if[^\n]*else)\s*\[?\s*"\d\.\d\d[a-z]?"'),  # argv default "7.41"
            re.compile(r'^PATCH_VERSION\s*=\s*"\d', re.M),                                     # a typed patch
            re.compile(r'"stats"\s*/\s*"\d\.\d\d[a-z]?"'))                                    # data/stats/"7.41c"
    for path in glob.glob(os.path.join(_ROOT, "scripts", "**", "*.py"), recursive=True) + \
            glob.glob(os.path.join(_ROOT, "tools", "*.py")):
        src = open(path, encoding="utf-8", errors="replace").read()
        bad += [f"{os.path.relpath(path, _ROOT)}: {m.group(0)}" for p in pats for m in p.finditer(src)]
    assert not bad, bad


def test_fetch_stats_uses_the_one_release_list():
    src = open(os.path.join(_ROOT, "tools", "fetch_stats.py"), encoding="utf-8").read()
    assert "from patch.meta import RELEASE_HISTORY" in src and '{"version": "7.41c"' not in src
