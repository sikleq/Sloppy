"""Hero Changes pages: 3 item slots under the hero name; no facet filter chips."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.entity_changes import _name_block, _ITEM_SLOTS


def test_hero_name_block_has_item_slots():
    html = _name_block({"kind": "hero", "name": "Anti-Mage", "slug": "anti-mage"})
    assert html.count('data-ec-islot="') == _ITEM_SLOTS == 3
    assert 'data-ec-hero="anti-mage"' in html
    assert '<div class="entity-name">Anti-Mage</div>' in html


def test_item_and_unit_pages_have_no_item_slots():
    for kind in ("item", "enchant", "unit"):
        html = _name_block({"kind": kind, "name": "Battle Fury", "slug": "battle-fury"})
        assert "ec-islot" not in html


def test_built_hero_page_has_no_facet_chips():
    page = Path(__file__).resolve().parent.parent / "dist" / "heroes" / "anti-mage.html"
    if not page.exists():
        import pytest
        pytest.skip("dist not built")
    html = page.read_text(encoding="utf-8")
    assert "ec-ab-facet" not in html
    assert "Magebane" not in html.split('<div class="container">')[0]      # toolbar chips sit before the container
