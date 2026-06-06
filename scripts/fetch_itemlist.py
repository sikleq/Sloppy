"""fetch_itemlist.py — Refresh data/itemlist.json from Valve's live datafeed.

This file is the source of truth for two things in build_patch.py:
  1. Item display names (slugs are legacy joke names: item_angels_demise = "Khanda",
     item_gungir = "Gleipnir", …) → used for the items_dyn roster labels.
  2. The CURRENT neutral pool — field `neutral_item_tier` (>= 0 = in the live drop
     pool). build_patch.py derives `_NEUTRAL_POOL_CURRENT` from it, so the items_dyn
     matrix auto-knows which neutrals are active vs cycled-out.

Run this whenever a new patch lands (it changes the neutral pool / adds items), then
rebuild:

    python scripts/fetch_itemlist.py
    python build_patch.py

No hand-maintained neutral list — refreshing this file is the whole update.
"""
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "itemlist.json"
DATAFEED = "https://www.dota2.com/datafeed/itemlist?language=english"


def main() -> int:
    print(f"Fetching {DATAFEED} ...")
    try:
        req = Request(DATAFEED, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8")
        data = json.loads(raw)
        items = data["result"]["data"]["itemabilities"]
    except Exception as exc:  # noqa: BLE001 — surface any fetch/parse failure
        print(f"X cannot fetch datafeed: {exc}")
        return 1

    pool = sorted(it["name"] for it in items
                  if it.get("neutral_item_tier", -1) >= 0
                  and not it["name"].startswith("item_recipe_"))
    OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"-> wrote {OUT.relative_to(ROOT)} ({len(items)} item entries)")
    print(f"   current neutral pool: {len(pool)} items (neutral_item_tier >= 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
