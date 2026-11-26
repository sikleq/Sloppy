# -*- coding: utf-8 -*-
"""How often pros pick each neutral artifact and enchantment, per patch -> data/rules/neutral_pick_share.json.

Owner 2026-11-26: the weight of a change grows with how often the thing is used ("частота применения",
docs/weights.md). Input: a per-patch export of the pro match database (all parsed Tier 1-2 matches since 7.38):
  {patch: {"tiers": {tier: {"hero_games_reaching": n}},
           "trinkets": [{"item", "tier", "hero_games"}],
           "enhancements": [{"item", "level", "hero_games", "offered_to_hero_games"}]}}
- Artifact share = hero-games that picked it / hero-games that reached its tier, against the mean share of the
  artifacts of the SAME tier (Fable 5.2 review 2026-11-26: tier 1 shares add up to 0.99, tier 4 to 0.58, so a
  mean over all tiers made every tier-2 artifact look 1.7x popular).
- Enchantment share = mean over its levels of picks / hero-games that could take that level. The export's
  "offered_to_hero_games" counts the hero-games that reached the FIRST tier it is offered at; level L is taken at a
  later tier, which fewer games reach, so the denominator is scaled by reach(tier of level L) / reach(first tier).
  The tier of each level comes from neutral_items.txt of the patch (game files). Against the mean of all
  enchantments of the patch.
Each entry: {"ratio", "n"} (n = hero-games it was measured on).

Usage:  python tools/build_neutral_share.py <export.json>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "data", "rules", "neutral_pick_share.json")


def level_tiers(version):
    """{enchantment slug: {level: first tier it is offered at that level}} from neutral_items.txt, {} if missing."""
    from patch import game_files
    from patch.kv import parse_kv
    text = game_files.npc(version, "neutral_items.txt") if game_files.available() else None
    if not text:
        return {}
    root = parse_kv(text)
    out = {}
    for tier, blk in (root.get("neutral_items", root).get("neutral_tiers") or {}).items():
        if not tier.isdigit() or not isinstance(blk, dict):
            continue
        ench = blk.get("enhancements") or {}
        flat = {}
        for k, v in ench.items():
            flat.update(v if isinstance(v, dict) else {k: v})      # 7.41+: grouped by attribute
        for slug, lvl in flat.items():
            if not slug.startswith("item_enhancement_"):
                continue
            try:
                lv = int(str(lvl).split()[0])
            except ValueError:
                continue
            cur = out.setdefault(slug[len("item_enhancement_"):], {})
            cur[lv] = min(cur.get(lv, 99), int(tier))
    return out


def _ratios(shares, group=lambda k: 0):
    """{key: (share, n)} -> {key: {"ratio", "n"}} against the mean share of the key's group."""
    by = {}
    for k, (s, n) in shares.items():
        if n:
            by.setdefault(group(k), []).append(s)
    out = {}
    for k, (s, n) in sorted(shares.items()):
        vals = by.get(group(k))
        if not n or not vals:
            continue
        mean = sum(vals) / len(vals)
        if mean <= 0:
            raise ValueError(f"mean share is 0 for group {group(k)}")
        out[k] = {"ratio": round(s / mean, 3), "n": n}
    return out


def build(export, tiers_of=level_tiers):
    out = {}
    for patch, rec in sorted(export.items()):
        if not patch[:1].isdigit():
            continue
        reach = {int(t): v["hero_games_reaching"] for t, v in rec["tiers"].items()}
        items, item_tier = {}, {}
        for r in rec["trinkets"]:
            n = reach.get(r.get("tier") or 0, 0)
            if n:
                slug = r["item"].removeprefix("item_")
                items[slug] = (r["hero_games"] / n, n)
                item_tier[slug] = r["tier"]
        lt = tiers_of(patch)
        ench = {}
        for r in rec["enhancements"]:
            slug = r["item"].removeprefix("item_enhancement_")
            offered = r.get("offered_to_hero_games") or 0
            lv = lt.get(slug, {})
            t1, tl = min(lv.values()) if lv else None, lv.get(r["level"])
            if offered and t1 and tl and reach.get(t1) and reach.get(tl):
                offered = offered * reach[tl] / reach[t1]
            ench.setdefault(slug, []).append((r["hero_games"], offered))
        ench = {k: (sum(p / o for p, o in rows if o) / len(rows), round(max(o for _, o in rows)))
                for k, rows in ench.items() if any(o for _, o in rows)}
        if not items or not ench:
            raise ValueError(f"{patch}: no artifacts or enchantments in the export")
        out[patch] = {"matches": rec.get("matches"),
                      "items": _ratios(items, group=lambda k: item_tier[k]),
                      "enchants": _ratios(ench)}
    if not out:
        raise ValueError("export has no patches")
    return out


def main(path):
    data = build(json.load(open(path, encoding="utf-8")))
    doc = ("Pro pick share of neutral artifacts (items, against the mean of their tier) and enchantments (against "
           "the mean of all enchantments) per patch, as a ratio; n = hero-games it was measured on "
           "(tools/build_neutral_share.py). Patches with a letter are merged into the patch without one in the "
           "source. Used by patch/weights.py neutral_use_multiplier.")
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"_doc": doc, "versions": data}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, OUT)
    print(f"{len(data)} patches -> {OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
