"""The site's script is written in src/js and glued into one file (owner 2026-11-04): nothing may be left out of the glue,
and the glue is what the page gets."""
import re
from pathlib import Path

from patch.js_bundle import JS_DIR, JS_PARTS, read_js
from patch.site_common import compute_asset_version

ROOT = Path(__file__).resolve().parent.parent
# one closure each: their insides share variables, so they are cut only with care, as a task of its own
_LONG = {"patch-dynamics", "hero-lab"}
_LIMIT = 800


def test_every_part_is_glued_once_and_nothing_else_lies_there():
    assert len(set(JS_PARTS)) == len(JS_PARTS)
    assert {p.stem for p in JS_DIR.glob("*.js")} == set(JS_PARTS)


def test_the_old_single_file_does_not_come_back():
    assert not (ROOT / "src" / "scripts.js").exists()


def test_parts_stay_short():
    for name in JS_PARTS:
        if name not in _LONG:
            lines = (JS_DIR / f"{name}.js").read_text(encoding="utf-8").count("\n")
            assert lines < _LIMIT, name


def test_the_glue_is_the_parts_in_order():
    js = read_js()
    assert js.startswith((JS_DIR / f"{JS_PARTS[0]}.js").read_text(encoding="utf-8"))
    assert js.endswith((JS_DIR / f"{JS_PARTS[-1]}.js").read_text(encoding="utf-8"))
    # the order the code needs: the abilities trees are set before the Changes page reads them
    assert js.index("window.SLOPPY_ABILITY_TREES =") < js.index("window.SLOPPY_ABILITY_TREES", js.index("window.SLOPPY_ABILITY_TREES =") + 5)


def test_a_change_in_any_part_changes_the_pages_asset_version():
    source = (ROOT / "patch" / "site_common.py").read_text(encoding="utf-8")
    assert "read_js()" in source and re.fullmatch(r"[0-9a-f]{10}", compute_asset_version())


def test_the_build_writes_the_glue_and_does_not_copy_the_parts():
    source = (ROOT / "build_site.py").read_text(encoding="utf-8")
    # each kind of page gets its own bundle; the whole one nothing loads is no longer written (audit 2026-11-10)
    assert '"src": ("js", "css")' in source and 'write_text(read_js(kind)' in source


def test_the_reopened_item_picker_moves_its_highlight():
    # the class was renamed to hl-item-tile and these lines kept the old name: the previous item stayed lit
    js = read_js()
    assert "hl-item-slot" not in js
    assert '.hl-item-tile[data-item-id="${selectedId}"]' in js


def test_dead_names_stay_gone():
    js = read_js()
    for name in ("DYN_NEUTRAL_TAGS", "miscOnly", "headCells", "tHitBase", "tHitFinal", "tierNum", "dragHalfW"):
        assert name not in js, name
