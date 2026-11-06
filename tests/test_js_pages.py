"""Each kind of page loads only its script parts: nothing a page needs may be left out (2026-11-05)."""
import re
from pathlib import Path

import pytest

from patch.js_bundle import JS_DIR, JS_PAGES, JS_PARTS, PART_MARKERS, parts_of, read_js

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
_SCRIPT = re.compile(r'<script[^>]+src="[^"]*src/scripts(?:-([a-z]+))?\.js')


def test_every_marked_part_is_a_part_and_belongs_to_some_kind():
    assert set(PART_MARKERS) <= set(JS_PARTS)
    assert set(PART_MARKERS) == {p for parts in JS_PAGES.values() for p in parts}


def test_a_kind_keeps_the_order_of_execution():
    for kind in JS_PAGES:
        parts = parts_of(kind)
        assert list(parts) == sorted(parts, key=JS_PARTS.index), kind


def test_a_part_finds_what_it_reads_from_another_part():
    defined = {}
    for name in JS_PARTS:
        text = (JS_DIR / f"{name}.js").read_text(encoding="utf-8")
        for found in re.findall(r"^(?:function|var|let|const)\s+([A-Za-z_$][\w$]*)", text, re.M) + re.findall(r"window\.([A-Za-z_$][\w$]*)\s*=[^=]", text):
            defined.setdefault(found, name)
    for kind in JS_PAGES:
        parts = parts_of(kind)
        for name in parts:
            text = (JS_DIR / f"{name}.js").read_text(encoding="utf-8")
            for shared, owner in defined.items():
                if owner != name and re.search(r"(?<![\w$.])" + re.escape(shared) + r"(?![\w$])", text):
                    assert owner in parts, f"{kind}: {name} reads {shared} of {owner}"


def test_the_whole_script_stays_for_pages_cached_from_before():
    assert len(read_js()) > len(read_js("base"))


def _built_pages():
    return sorted(DIST.rglob("*.html")) if DIST.exists() else []


@pytest.mark.skipif(not _built_pages(), reason="the site is not built")
def test_every_built_page_loads_the_parts_its_html_asks_for():
    markers = {name: re.compile(rx) for name, rx in PART_MARKERS.items()}
    missing, whole = [], []
    for path in _built_pages():
        html = path.read_text(encoding="utf-8")
        script = _SCRIPT.search(html)
        if not script:
            continue
        kind = script.group(1)
        if not kind:
            whole.append(path.name)
            continue
        parts = parts_of(kind)
        for name, rx in markers.items():
            if name not in parts and rx.search(html):
                missing.append(f"{path.relative_to(DIST)} ({kind}) needs {name}")
    assert not missing, missing[:20]
    assert not whole, whole[:20]
