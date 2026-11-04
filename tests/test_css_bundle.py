"""The stylesheet is written in src/css and glued into one file (owner 2026-11-04). The order of the parts is the cascade, so
nothing may be left out of the glue, the generated block keeps its place, and a part stays short enough to find a rule in."""
from pathlib import Path

from patch.css_bundle import CSS_DIR, CSS_PARTS, read_css
from patch.site_common import compute_asset_version

ROOT = Path(__file__).resolve().parent.parent
_LIMIT = 800


def test_every_part_is_glued_once_and_nothing_else_lies_there():
    assert len(set(CSS_PARTS)) == len(CSS_PARTS)
    assert {p.name[:-4] for p in CSS_DIR.glob("*.css")} == set(CSS_PARTS)


def test_the_old_single_file_does_not_come_back():
    assert not (ROOT / "styles.css").exists()


def test_parts_stay_short():
    for name in CSS_PARTS:
        assert (CSS_DIR / f"{name}.css").read_text(encoding="utf-8").count("\n") < _LIMIT, name


def test_the_generated_block_and_the_phones_block_close_the_sheet():
    assert CSS_PARTS[-2:] == ("colorblind.generated", "phones")
    assert (CSS_DIR / "colorblind.generated.css").read_text(encoding="utf-8").startswith("/* === COLOUR-BLIND MODE: generated")


def test_no_part_cuts_a_rule_or_a_comment_in_two():
    for name in CSS_PARTS:
        text = (CSS_DIR / f"{name}.css").read_text(encoding="utf-8")
        depth, i, n = 0, 0, len(text)
        while i < n:
            if text.startswith("/*", i):
                i = text.find("*/", i)
                assert i >= 0, f"{name}: a comment runs out of the part"
                i += 2
                continue
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            assert depth >= 0, f"{name}: a block closes that was opened in another part"
            i += 1
        assert depth == 0, f"{name}: a block runs out of the part"


def test_a_change_in_any_part_changes_the_pages_asset_version():
    source = (ROOT / "patch" / "site_common.py").read_text(encoding="utf-8")
    assert "read_css()" in source and "read_js()" in source and len(compute_asset_version()) == 10


def test_the_build_writes_the_glue_and_does_not_copy_the_parts():
    source = (ROOT / "build_site.py").read_text(encoding="utf-8")
    assert '"src": ("js", "css")' in source and "write_text(read_css()" in source


def test_paths_in_the_sheet_still_start_at_the_site_root():
    # dist/styles.css stands at the root: url() of a part must not be relative to src/css
    assert "url('../" not in read_css() and "url(../" not in read_css()
