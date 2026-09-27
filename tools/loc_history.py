"""Read a tooltip as it was in a given patch (history fetched by tools/fetch_loc_history.py).

    from tools.loc_history import tooltip
    tooltip("DOTA_Tooltip_Ability_item_angels_demise_Description", "7.37e")

Keys are case-insensitive (Valve mixes DOTA_Tooltip_Ability_ / DOTA_Tooltip_ability_). Returns None when the
patch or the key is missing. Numbers stay as %placeholders% — fill them from that patch's KV.
"""
import gzip
import os
import re

LOC = os.path.join(os.path.expanduser("~"), "outputs", "loc_history")
_RX = re.compile(r'^\s*"([^"]+)"\s*"((?:[^"\\]|\\.)*)"', re.M)
_CACHE = {}


def _table(version, name):
    key = (version, name)
    if key not in _CACHE:
        path = os.path.join(LOC, version, f"{name}_english.txt.gz")
        table = {}
        if os.path.exists(path):
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for m in _RX.finditer(f.read()):
                    table.setdefault(m.group(1).lower(), m.group(2))
        _CACHE[key] = table
    return _CACHE[key]


def tooltip(key, version):
    k = key.lower()
    for name in ("abilities", "dota"):
        v = _table(version, name).get(k)
        if v is not None:
            return v
    return None
