"""An item named inside a row's text as a link to its Changes page (owner 2026-10-30, 7.37 Roshan: "Refresher Shard and
Cheese … Aghanim's Blessing — 3 кликабельные ссылки, ведущие на свои изменения").

The page's slug is what builders/entity_changes.py gives it: an item some patch page annotates (an item_header) has
its name's slug (refresher-shard); an item no page annotates has its roster key's (item_ultimate_scepter_2 →
ultimate-scepter-2) — data/itemlist.json names it."""
import functools
import glob
import html
import json
import os
import re

from .state import _State

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HEADER_RE = re.compile(r'item_header\("([^"]+)"')


def _slugify(name):
    s = name.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


@functools.lru_cache(maxsize=1)
def _annotated():
    """Names of the items some patch page has a block of."""
    names = set()
    for path in glob.glob(os.path.join(_ROOT, "content", "p*.py")):
        with open(path, encoding="utf-8") as f:
            names.update(_HEADER_RE.findall(f.read()))
    return names


@functools.lru_cache(maxsize=1)
def _roster():
    """{display name: engine name} of every item (data/itemlist.json), recipes left out."""
    path = os.path.join(_ROOT, "data", "itemlist.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    if isinstance(items, dict):                         # Valve's datafeed envelope: result.data.itemabilities
        items = items.get("result", {}).get("data", {}).get("itemabilities", [])
    return {i["name_english_loc"]: i["name"] for i in items
            if i.get("name_english_loc") and not i["name"].startswith("item_recipe_")}


def item_page(name):
    """The item's Changes page slug, or None for a name that is not an item."""
    if name in _annotated():
        return _slugify(name)
    engine = _roster().get(name)
    return engine[len("item_"):].replace("_", "-") if engine else None


def item_link(name):
    """<a> to the item's Changes page (from this patch, as an item header's link); the name as it was if unknown."""
    slug = item_page(name)
    if not slug:
        return html.escape(name)
    ver = _State.current_patch_version
    href = f"../items/{slug}.html" + (f"?from={ver}" if ver else "")
    return f'<a class="item-mention" href="{href}" title="All changes of {html.escape(name)}">{html.escape(name)}</a>'
