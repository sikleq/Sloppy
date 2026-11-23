"""Owner 2026-11-23: items stand in the game's order and the neutral tiers show the game's unlock times — read from the
game's shops.txt / neutral_items.txt (patch/shop_layout.py), never a hand-kept list."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "builders"))
from patch.shop_layout import neutral_tiers, shop_order  # noqa: E402


def test_tiers_and_times_come_from_neutral_items():
    t = neutral_tiers()
    assert [t[k]["time"] for k in sorted(t)][:4] == ["0:00", "15:00", "30:00", "50:00"]       # 7.42
    assert t[1]["items"][:3] == ["chipped_vest", "ash_legion_shield", "possessed_mask"]


def test_item_changes_uses_the_game_order_and_times():
    import entity_changes as ec
    assert ec._shop_order() == shop_order()
    assert ec._TIER_TIME[3] == "30:00+" and ec._TIER_TIME[4] == "50:00+"
    js = (ROOT / "src" / "js" / "hero-lab.js").read_text(encoding="utf-8")
    assert "var SHOP_ORDER = data.shopOrder" in js and "'clarity','tango'" not in js   # no hand-kept list


def test_hero_lab_page_carries_the_game_order():
    page = ROOT / "dist" / "hero_lab.html"
    if not page.exists():
        import pytest
        pytest.skip("site not built")
    text = page.read_text(encoding="utf-8")
    data = json.loads(text.split('id="hero-lab-data"')[1].split(">", 1)[1].split("</script>")[0])
    assert data["shopOrder"]["Consumables"] == shop_order()["Consumables"]
    assert data["neutralOrder"]["0"] == neutral_tiers()[1]["items"]
