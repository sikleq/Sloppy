"""Read a tooltip as it was in a given patch (the patch's own build in our game-files store, patch/game_files.py;
until 2026-10-24 a d2vpkr download in outputs/loc_history).

    from patch.loc_history import tooltip
    tooltip("DOTA_Tooltip_Ability_item_angels_demise_Description", "7.37e")

Keys are case-insensitive (Valve mixes DOTA_Tooltip_Ability_ / DOTA_Tooltip_ability_). Returns None when the
patch or the key is missing. Numbers stay as %placeholders% — fill them from that patch's KV.
"""
import re

from patch import game_files

_RX = re.compile(r'^\s*"([^"]+)"\s*"((?:[^"\\]|\\.)*)"', re.M)
_CACHE = {}
FILES = {  # name -> candidate files of a patch, newest layout first (before 7.20 everything sat in dota_english)
    "abilities": ("resource/localization/abilities_english.txt", "resource/dota_english.txt"),
    "dota": ("resource/localization/dota_english.txt", "resource/dota_english.txt"),
}


def _table(version, name):
    key = (version, name)
    if key not in _CACHE:
        table = {}
        text = next((t for t in (game_files.read(version, rel) for rel in FILES[name]) if t), None)
        if text:
            for m in _RX.finditer(text):
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
