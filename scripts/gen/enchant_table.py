"""data/rules/enchant_tables.json — every enchantment of a patch page as a table by tier, before -> after (owner
2026-10-17, 7.41: "Vital is written as a bare row… a table? a card? Mystical / Crude too" -> variant A: the 7.38
table, a changed cell "was -> now" in colour).

    python scripts/gen/enchant_table.py 7.41 [7.40c]

Where each number comes from:
- values: the two patches' items.txt (AbilityValues, one value per tier the enchantment is offered at, or one for
  all), with enchant_values.CORRECTIONS (the local "7.41" file is the 7.41a build);
- the tiers it is offered at now: the page's own enchant_tier_box() calls; before: the block's "Tiers changed from
  4/5 to 2-4" row, else the same tiers (the old values must then fit them, or the old side is left out);
- the labels: patch/elements.py _ENCHANT_DESC lines matched to the KV keys in order; a key the table doesn't name
  (Mystical's 7.40 "bonus_cast_range") takes EXTRA_LABELS, else it is left out and reported — never guessed.
"""
import ast
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patch.item_ability_text import _items  # noqa: E402
from enchant_values import kv_values, _levels  # noqa: E402
from patch.elements import _ENCHANT_DESC  # noqa: E402

OUT = os.path.join(_ROOT, "data", "rules", "enchant_tables.json")
_NUM = re.compile(r"^([+\-−]?)(\d+(?:\.\d+)?)(%?)\s+(.+)$")
# keys an older patch had and the current table doesn't name: (sign, unit, label)
EXTRA_LABELS = {("Mystical", "bonus_cast_range"): ("+", "", "Cast Range"),
                # _ENCHANT_DESC: "+40 Primary Stat", "(+24 All Attributes for Universal heroes)"
                ("Evolved", "primary_stat"): ("+", "", "Primary Stat"),
                ("Evolved", "primary_stat_universal"): ("+", "", "All Attributes (Universal heroes)")}
# a bonus that hurts its owner (a bigger one is worse); a "−" alone doesn't say it (Manic "−18% Base Attack Time" helps)
PENALTIES = {"Intelligence", "Max Mana", "Attack Damage", "Incoming Damage", "Mana Cost/Loss Increase", "Vision",
             "Health Regen", "Attack Speed"}
PENALTY_OWNERS = {"Health Regen": {"Nimble"}, "Attack Speed": {"Titanic", "Hulking"}, "Attack Damage": {"Greedy"}}


def game_tiers(version):
    """{enchantment name: [tiers]} the game offers it at in `version` (neutral_items.txt "neutral_tiers" ->
    "enhancements"); {} when the patch's file isn't there. The page's tier boxes, where it has them, win; a patch
    page without them (7.39 "Enchantment Changes", owner 2026-10-26: "сделать таблицей как в 7.41") takes these."""
    from patch.kv import parse_kv
    from patch import game_files
    text = game_files.npc(version, "neutral_items.txt") if game_files.available() else None
    if not text:
        return {}
    root = parse_kv(text)
    tiers = (root.get("neutral_items", root).get("neutral_tiers") or {})
    out = {}
    for tier, blk in tiers.items():
        ench = (blk or {}).get("enhancements") or {}
        # from 7.41 by attribute: {"global": {slug: "1"}, "strength": {...}, ...}; before, {slug: "1"}
        slugs = [s for k, v in ench.items() for s in (v if isinstance(v, dict) else {k: v})]
        for slug in slugs:
            if tier.isdigit() and slug.startswith("item_enhancement_"):
                out.setdefault(slug[len("item_enhancement_"):], set()).add(int(tier))
    return {k: sorted(v) for k, v in out.items()}


def game_label(name, key, version):
    """(sign, unit, label) of a KV key as that patch's game text names it ("%+$slow_resistance" -> ("+", "%", "Slow
    Resistance")), else None. The _ENCHANT_DESC lines are today's text, matched by order: in an older patch the keys
    differ (7.39 Mystical's third value is Cast Range, not Mana Cost/Loss Reduction — owner 2026-10-26)."""
    from patch.loc_history import tooltip
    raw = tooltip(f"DOTA_Tooltip_ability_item_enhancement_{_game_name(name)}_{key}", version)
    m = re.fullmatch(r"\s*(%?)([+\-]?)(%?)\s*(.+?)\s*", raw or "")
    if not m:
        return None
    label = m.group(4)
    if label.startswith("$"):
        label = tooltip(f"dota_ability_variable_{label[1:]}", version)
    if not label or not re.search(r"[A-Za-z]", label):
        return None
    return m.group(2) or "+", "%" if (m.group(1) or m.group(3)) else "", label.strip()


def _stems(label):
    return {w[:5] for w in re.findall(r"[a-z]+", label.lower()) if len(w) > 2}


def _game_name(name):
    return name.lower().replace("-", "_").replace(" ", "_").replace("'", "")


def _tiers(spec):
    """'4/5' -> [4, 5], '2-4' -> [2, 3, 4], '5' -> [5]."""
    spec = spec.strip()
    m = re.fullmatch(r"(\d)\s*-\s*(\d)", spec)
    if m:
        return list(range(int(m.group(1)), int(m.group(2)) + 1))
    return [int(x) for x in re.findall(r"\d", spec)]


def page_blocks(version):
    """{enchantment: {"tiers": [...] from the tier boxes, "rows": [row texts]}} of content/p<code>.py."""
    code = version.replace(".", "")
    src = open(os.path.join(_ROOT, "content", f"p{code}.py"), encoding="utf-8").read()
    tiers = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "enchant_tier_box":
            rows = ast.literal_eval(node.args[0])
            ts = ast.literal_eval(next(k.value for k in node.keywords if k.arg == "tiers"))
            ts = [ts] if isinstance(ts, int) else list(ts)
            for _attr, names in rows:
                for n in names:
                    tiers.setdefault(n, set()).update(ts)
    blocks, cur = {}, None
    for ln in src.split("\n"):
        m = re.match(r'\s*W\(enchant_header\("([^"]+)"', ln)
        if m:
            cur = m.group(1)
            blocks[cur] = {"tiers": sorted(tiers.get(cur, [])), "rows": []}
            continue
        if re.match(r'\s*W\((?:item_header|plain_header|subgroup|section|enchant_tier_box)\(', ln):
            cur = None
        r = re.match(r'\s*W\(li\("((?:[^"\\]|\\.)*)"', ln)
        if cur and r:
            blocks[cur]["rows"].append(r.group(1))
    return blocks


def labels(name, keys_by_tier, tiers):
    """{kv key: (sign, unit, label)} from the _ENCHANT_DESC lines, matched in KV order at each tier."""
    out = {}
    desc = _ENCHANT_DESC.get(name, {})
    for t in tiers:
        lines = [ln for ln in desc.get(t, []) if _NUM.match(ln)]
        keys = keys_by_tier.get(t, [])
        if len(lines) != len(keys):
            continue
        for k, ln in zip(keys, lines):
            m = _NUM.match(ln)
            out.setdefault(k, (m.group(1).replace("−", "-") or "+", m.group(3), m.group(4).strip()))
    return out


def side(name, kv, version, tiers):
    """({key: {tier: value}}, {tier: [keys with a value]}) of one patch, or None when the values don't fit the tiers."""
    vals = kv_values(name, kv, version)
    if vals is None or not tiers:
        return None
    per, keys_by_tier = {}, {}
    for k, raw in vals.items():
        lv = _levels(raw)
        if not lv:
            continue
        if len(lv) == 1:
            lv = lv * len(tiers)
        if len(lv) != len(tiers):
            return None
        per[k] = {t: v for t, v in zip(tiers, lv)}
        for t, v in zip(tiers, lv):
            if v:
                keys_by_tier.setdefault(t, []).append(k)
    return per, keys_by_tier


def build(version, prev):
    kv_new, kv_old = _items(version), _items(prev)
    game_new, game_old = game_tiers(version), game_tiers(prev)
    out = {}
    for name, blk in page_blocks(version).items():
        tiers_new = blk["tiers"] or game_new.get(_game_name(name), [])
        moved = next((re.search(r"Tiers changed from (\S+) to (\S+)", r) for r in blk["rows"]
                      if re.search(r"Tiers changed from", r)), None)
        tiers_old = (_tiers(moved.group(1)) if moved
                     else game_old.get(_game_name(name)) if not blk["tiers"] and game_old.get(_game_name(name))
                     else list(tiers_new))
        new = side(name, kv_new, version, tiers_new)
        if new is None:
            print(f"{version} {name}: new values don't fit tiers {tiers_new} — left out")
            continue
        old = side(name, kv_old, prev, tiers_old) if _items(prev) and kv_values(name, kv_old) else None
        if kv_values(name, kv_old) and old is None:
            print(f"{version} {name}: {prev} values don't fit tiers {tiers_old} — old side left out")
        lab = labels(name, new[1], tiers_new)
        stats = []
        for k in list(new[0]) + [k for k in (old[0] if old else {}) if k not in new[0]]:
            game = game_label(name, k, version) or game_label(name, k, prev)
            info = lab.get(k) or EXTRA_LABELS.get((name, k))
            # today's line that names another key (its words not in the key's, nor in the game's label): the patch's
            # own text wins; one about this key keeps its wording ("BAT Reduction" for bat_reduce, 7.41)
            if game and not (info and _stems(info[2]) & (_stems(k.replace("_", " ")) | _stems(game[2]))):
                info = game
            if not info:
                if any((new[0].get(k) or {}).values()) or any(((old[0] if old else {}).get(k) or {}).values()):
                    print(f"{version} {name}: no label for {k} — left out")
                continue
            sign, unit, label = info
            penalty = label in PENALTIES and (label not in PENALTY_OWNERS or name in PENALTY_OWNERS[label])
            fmt = lambda v: f"{sign if sign == '+' else '−'}{abs(v):g}{unit}" if v else "0"
            stats.append({"key": k, "label": label, "penalty": penalty,
                          "new": {str(t): fmt(v) for t, v in new[0].get(k, {}).items()},
                          "old": {str(t): fmt(v) for t, v in (old[0].get(k, {}) if old else {}).items()}})
        out[name] = {"tiers_old": tiers_old if old else [], "tiers_new": tiers_new, "stats": stats,
                     "brand_new": old is None}
    return out


def main(version, prev):
    data = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            data = json.load(f)
    data[version] = build(version, prev)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    print(version, len(data[version]), "enchantments ->", os.path.relpath(OUT, _ROOT))


if __name__ == "__main__":
    from patch.weights import _prev_version
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/gen/enchant_table.py <version> [<previous>] <version> - the patch to build (no default: a new patch passes its own)")
    v = sys.argv[1]
    main(v, sys.argv[2] if len(sys.argv) > 2 else _prev_version(v))
