"""Build items_dyn.html — the Item Dynamics matrix.

Same matrix as heroes_dyn (ROWS = every item with any tracked change, alphabetical;
COLUMNS = every patch; CELL = that item's patch-dynamics dyn-cell), reusing the
shared renderer in `dyn_matrix_common.save_dyn_matrix`. Only the config differs:
item roster + icons/items/ portraits + an items back-arrow token.

The item roster is every item that appears in the dynamics (`item|<slug>`
entities) — there's no fixed "all items" master list like the hero roster, so the
rows are the items actually touched across tracked patches.

Run AFTER build_patch.py (it needs the fresh _dynamics.json + site_meta.json):
    python build_patch.py
    python build_items_dyn.py
"""
from dyn_matrix_common import save_dyn_matrix


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
        blurb=(
            "Every item down the side, every patch across the top. Each diamond "
            "is that item’s balance-change summary for that patch — hover it for "
            "the buff/nerf/rework breakdown, click to jump to the item on that "
            "patch page. Hover a patch column for its release date. Empty diamonds "
            "mean the item was untouched. <strong>Remove</strong> drops any tag "
            "from the diamonds (it still shows on hover); the <strong>search</strong> "
            "box filters items by name — comma-separate for several (partial names "
            "work: <em>blink, dagon, aghs</em>)."),
    )


if __name__ == "__main__":
    save_items_dyn_html()
