"""data/rules/enchant_values.json — the Enchantment chips' hover text in each patch, from that patch's items.txt
(owner 2026-10-17, 7.41: the chips took one table for every patch, so their hover said Vital +2.25 while the row
said +2). The labels are patch/elements.py _ENCHANT_DESC's; the numbers are the patch's own, in the KV order, the
tiers it lists. A line whose numbers don't fit is reported and left out of the version (the chip falls back to the
table), never guessed.

    python scripts/gen/enchant_values.py 7.41 [7.42 ...]
"""
import json
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "tools"))
from item_ability_text import _items  # noqa: E402
from patch.elements import _ENCHANT_DESC  # noqa: E402

OUT = os.path.join(_ROOT, "data", "rules", "enchant_values.json")
# {version: {enchantment: {kv key: value}}} where the local items.txt isn't that patch's build. Empty since
# 2026-10-17: the "7.41" file was the 7.41a build (byte-identical; Crude 6/9/12 instead of 8/12/16, owner) and was
# replaced with the real 7.41 build 6728 from the client archive.
CORRECTIONS = {}
_NUM = re.compile(r"(?<![\w.])([+\-−]?)(\d+(?:\.\d+)?)")


def _slug(name):
    return "item_enhancement_" + name.lower().replace("-", "_").replace(" ", "_").replace("'", "")


def _levels(raw):
    """A KV value per tier: "7 15 23 31" -> [7.0, 15.0, 23.0, 31.0]."""
    raw = raw.get("value", "") if isinstance(raw, dict) else raw
    try:
        return [float(x) for x in str(raw).split()]
    except ValueError:
        return None


def _fmt(x):
    return f"{abs(x):g}"


def kv_values(name, kv, version=""):
    """{key: raw value} of an enchantment's AbilityValues in a patch, CORRECTIONS applied, or None."""
    blk = kv.get(_slug(name))
    if not isinstance(blk, dict) or not isinstance(blk.get("AbilityValues"), dict):
        return None
    return {**blk["AbilityValues"], **CORRECTIONS.get(version, {}).get(name, {})}


def enchant(name, tiers, kv, version=""):
    """{tier: lines} of one enchantment in one patch, or (None, why)."""
    vals = kv_values(name, kv, version)
    if vals is None:
        return None, "not in items.txt"
    cols = [lv for lv in (_levels(v) for v in vals.values()) if lv]
    order = sorted(tiers)
    out = {}
    for t in order:
        i = order.index(t)
        vals = [c[i] if len(c) == len(order) else c[0] for c in cols if len(c) in (1, len(order))]
        vals = [v for v in vals if v]                    # a 0 = the line isn't there at this tier
        lines, k = [], 0
        for line in tiers[t]:
            nums = _NUM.findall(line)
            if not nums:
                lines.append(line)
                continue
            if k + len(nums) > len(vals):
                return None, f"tier {t}: more numbers than values ({vals})"
            it = iter(vals[k:k + len(nums)])
            lines.append(_NUM.sub(lambda m: m.group(1) + _fmt(next(it)), line))
            k += len(nums)
        if k != len(vals):
            return None, f"tier {t}: {len(vals)} values for {k} numbers ({vals})"
        out[str(t)] = lines
    return out, ""


def main(versions):
    data = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            data = json.load(f)
    for v in versions:
        kv = _items(v)
        if not kv:
            print(v, "- no items.txt")
            continue
        got = {}
        for name, tiers in _ENCHANT_DESC.items():
            lines, why = enchant(name, tiers, kv, v)
            if lines is None:
                print(f"{v} {name}: left to the table - {why}")
            else:
                got[name] = lines
        data[v] = got
        print(v, len(got), "of", len(_ENCHANT_DESC), "enchantments")
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ["7.41"])
