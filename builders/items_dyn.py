"""Build items_dyn.html — the Item Dynamics matrix.

Same matrix as heroes_dyn (ROWS = every item with any tracked change, alphabetical;
COLUMNS = every patch; CELL = that item's patch-dynamics dyn-cell), reusing the
shared renderer in `dyn_matrix_common.save_dyn_matrix`. Only the config differs:
item roster + icons/items/ portraits + an items back-arrow token.

The item roster is EVERY real game item (parity with heroes_dyn listing every
hero), not just touched ones — untouched items render as empty rows. build_patch.py
builds it: touched items (from the dynamics) merged with every other real item from
items.txt + datafeed names (see `_load_full_game_items`), deduped by icon game slug.

Run AFTER build_patch.py (it needs the fresh _dynamics.json + site_meta.json):
    python build_patch.py
    python build_items_dyn.py
"""
import sys as _sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))

from builders.dyn_matrix_common import save_dyn_matrix


def save_items_dyn_html():
    save_dyn_matrix(
        kind="item",
        roster_key="items",
        out_file="items_dyn.html",
        page_title="Item Dynamics",
        subtab="items_dyn",
        noun="Item",
        icon_dir="icons/items",
        from_token="items_dyn",
        search_ph="Search items — blink, dagon, aghs…",
        current_toggle=True,
        class_filter=True,
        price_filter=True,
        category_filter=True,
        preserve_roster_order=True,
        blurb=(
            "Every item down the side, every patch across the top — regular items, "
            "neutral items and enchantments together. Each diamond is that item’s "
            "balance-change summary for that patch — hover it for the "
            "buff/nerf/rework breakdown, click to jump to the item on that patch "
            "page. Hover a patch column for its release date. Empty diamonds mean "
            "the item was untouched. <strong>Deleted</strong> reveals items "
            "removed from the game; the <strong>class chips</strong> (Items / "
            "Neutral Items / Enchantments) toggle which types show; <strong>Price"
            "</strong> filters by gold cost (neutrals + enchantments are free, so "
            "they ignore it); the coloured <strong>tag chips</strong> drop a tag "
            "from the diamonds (it still shows on hover); the <strong>search</strong> "
            "box filters by name (comma-separate: <em>blink, dagon, aghs</em>)."),
    )


if __name__ == "__main__":
    save_items_dyn_html()
