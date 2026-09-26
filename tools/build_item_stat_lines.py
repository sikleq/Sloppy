r"""Every item's stat lines in every patch -> data/rules/item_stat_lines.json (read by
patch/elements.py properties_change).

Why (owner 2026-09-27, Mage Slayer 7.38): a "before -> after" stats card must list ALL the item's
stats, also the ones the patch did not touch (+20% Magic Resistance, +2 Mana Regen). Patch notes
never mention them, so they come from the game's own items.txt of the two patches.

Which KV fields are stat lines, and which stat they are, is read exactly as tools/fit_item_prices.py
does (Valve's tooltips). Stored compactly: per item, [first version, {stat: value}] only when the
stats change.

Usage: python tools/build_item_stat_lines.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fit_item_prices as fp  # noqa: E402

OUT = os.path.join(fp.HERE, "data", "rules", "item_stat_lines.json")


def main():
    loc = fp.load_loc()
    versions = sorted({r["version"] for r in fp.RELEASE_HISTORY if fp.kv_path(r["version"])}, key=fp.vkey)
    names = set()
    for v in versions:
        names |= set(re.findall(r'^\t"(item_[a-z0-9_]+)"', open(fp.kv_path(v), encoding="utf-8",
                                                                  errors="replace").read(), re.M))
    # A field without its own stat tooltip counts only when it is a "bonus_*" field: the learned map
    # would read Dagon's nuke "damage" or Ethereal Blade's "projectile_speed" as +stats.
    fmap = {f: s for f, s in fp.learn_field_map(loc, names).items() if f.startswith("bonus_")}
    runs = {}
    for v in versions:
        for name, it in fp.parse_version(v, loc, fmap).items():
            stats = {k: round(x, 3) for k, x in sorted(it["stats"].items()) if k != "damage_block"}
            r = runs.setdefault(name[5:], [])
            if not r or r[-1][1] != stats:
                r.append([v, stats])
    doc = {"_doc": "Per item: [first version, {stat: value}] whenever its stat lines change (stat keys as in "
                   "item_stat_prices.json; %-stats in %). Built by tools/build_item_stat_lines.py from the "
                   "d2vpkr items.txt history + data/stats/<v>/items.txt.",
           "versions": versions, "items": runs}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(versions)} versions, {len(runs)} items, {os.path.getsize(OUT):,} bytes")


if __name__ == "__main__":
    main()
