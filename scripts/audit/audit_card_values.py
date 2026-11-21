"""audit_card_values.py — item stats cards whose "before" number is not what the previous patch's items.txt had.

The row audit (audit_from_values.py) reads only "from X to Y" rows; the item cards (properties_change(old=[…],
new=[…])) went past it, and 7.42 Crimson Guard showed Valve's "+4 → +5 Armor" as a buff while the files had 6 → 5
(owner 2026-11-21: "Везде всё проверь"). A mismatch goes into data/rules/valve_errors.json once checked — the generator
then puts the files' number on the card with a red tag.

    python scripts/audit/audit_card_values.py
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from patch.cards_item_stats import _STAT_LINE, item_stats_pair  # noqa: E402

_BY_NAME = {}
for _k, (_name, _pct, _rx) in _STAT_LINE.items():
    _BY_NAME.setdefault(_name.lower(), []).append(_k)


def _number(text):
    m = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)%?\s+(.+?)\s*$", re.sub(r"<[^>]+>", "", text))
    return (float(m.group(1)), m.group(2).lower()) if m else None


def _call_at(lines, i):
    """The properties_change(...) call that starts on lines[i], parsed (it may span lines)."""
    buf = lines[i][lines[i].index("properties_change("):]
    for j in range(i + 1, min(i + 40, len(lines)) + 1):
        for text in (buf.strip(), buf.strip()[:-1]):
            try:
                node = ast.parse(text).body[0].value
            except SyntaxError:
                continue
            if isinstance(node, ast.Call):
                return node
        if j < len(lines):
            buf += "\n" + lines[j]
    return None


def _rows(node):
    return [e.elts[1].value for e in getattr(node, "elts", [])
            if isinstance(e, ast.Tuple) and len(e.elts) >= 2 and isinstance(e.elts[1], ast.Constant)]


def card_mismatches():
    """([(version, item, card text, files' number)], numbers checked, [(version, item) of cards with no data])."""
    found, checked, nodata = [], 0, []
    for path in sorted((ROOT / "content").glob("p*.py")):
        m = re.match(r"p(\d)(\d+)([a-z]?)$", path.stem)
        version = f"{m.group(1)}.{m.group(2)}{m.group(3)}"
        lines, item = path.read_text(encoding="utf-8").splitlines(), None
        for i, line in enumerate(lines):
            h = re.search(r'item_header\("([^"]+)"', line)
            if h:
                item = h.group(1)
            if "properties_change(" not in line or not item:
                continue
            call = _call_at(lines, i)
            if call is None:
                raise ValueError(f"{path.name}:{i + 1}: a card the audit cannot read")
            old = next((k.value for k in call.keywords if k.arg == "old"), None)
            pair = item_stats_pair(item, version)
            if not pair:
                nodata.append((version, item))
                continue
            for text in _rows(old):
                n = _number(text)
                keys = _BY_NAME.get(n[1]) if n else None
                real = next((pair[0][k] for k in keys or () if k in pair[0]), None)
                if real is None:
                    continue
                checked += 1
                if abs(real - n[0]) > 1e-6:
                    found.append((version, item, text, real))
    return found, checked, nodata


if __name__ == "__main__":
    found, checked, nodata = card_mismatches()
    for f in found:
        print("MISMATCH", *f)
    print(f"checked {checked} numbers; no data for {len(nodata)} cards {nodata}; mismatches {len(found)}")
