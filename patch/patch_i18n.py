"""Build-time English→Russian map for patch-note body text.

Valve ships the patch notes as two parallel KV files keyed by a stable token
(e.g. `DOTA_Patch_7_41c_item_bloodstone`):
    data/patchnotes_english.txt   data/patchnotes_russian.txt
Joining them on that shared key gives an exact `english_text → russian_text`
map. `patch/elements.py::li()` looks up each row's source text and, when found,
emits the Russian inline as `data-i18n-ru` on the row-text span; the client
toggle (src/scripts.js i18n runtime) swaps it in for RU and restores the English
baseline for EN. ~88% of rows match; handcrafted / reworded rows simply fall
back to English.

Only the patch BODY is covered here — proper nouns (hero/item names), structural
section titles and the tag tokens stay as the rest of the i18n system leaves
them. The map is built once per process (lazily) and cached.
"""
import os as _os
import re as _re

_HERE = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_EN_PATH = _os.path.join(_HERE, "data", "patchnotes_english.txt")
_RU_PATH = _os.path.join(_HERE, "data", "patchnotes_russian.txt")

_KV_RE = _re.compile(r'\s*"([^"]+)"\s+"(.*)"\s*$')

_map = None  # {english_text: russian_text}, built lazily

# Structural headers we author ourselves (not in Valve's KV). Small, finite set;
# anything not listed falls back to English. Keyed by the exact title string.
_STRUCTURAL = {
    "General Updates": "Общие изменения",
    "Hero Updates": "Изменения героев",
    "Item Updates": "Изменения предметов",
    "Neutral Item Updates": "Изменения нейтральных предметов",
    "Neutral Creep Updates": "Изменения нейтральных крипов",
    "Map Objectives": "Цели на карте",
    "Mechanics": "Механики",
    "Mechanics Changes": "Изменения механик",
    "Terrain Changes": "Изменения местности",
    "General": "Общее",
    "General Changes": "Общие изменения",
    "General changes": "Общие изменения",
    "Global Changes": "Глобальные изменения",
    "Enchantments": "Зачарования",
    "Enchantment Changes": "Изменения зачарований",
    "Enchantment changes": "Изменения зачарований",
    "Upgrades": "Улучшения",
    "Shop Reshuffle": "Перестановка в магазине",
    # Category-filter chip labels (derived from the section titles in
    # _section_slug → "Heroes"/"Items"/… ), so the "Group:" bar matches.
    "Heroes": "Герои",
    "Items": "Предметы",
    "Neutral Items": "Нейтральные предметы",
    "Neutral Creeps": "Нейтральные крипы",
}


def _parse_kv(path):
    out = {}
    try:
        # utf-8-sig: the Russian file carries a BOM.
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                m = _KV_RE.match(line)
                if m:
                    out[m.group(1)] = m.group(2)
    except OSError:
        pass
    return out


def _build_map():
    en = _parse_kv(_EN_PATH)
    ru = _parse_kv(_RU_PATH)
    m = {}
    for key, en_text in en.items():
        ru_text = ru.get(key)
        if ru_text and ru_text != en_text:
            # First mapping wins — identical English strings across patches map
            # to the same translation in practice.
            m.setdefault(en_text, ru_text)
    return m


def ru_for(text):
    """Return the official Russian translation for a patch-note row's English
    source text, or None when there's no exact match (handcrafted/reworded rows,
    or rows whose source carries inline HTML)."""
    global _map
    if not isinstance(text, str):
        return None
    if _map is None:
        _map = _build_map()
    return _map.get(text)


def ru_for_header(text):
    """Russian for one of our own structural headers (section/plain_header),
    or None. Kept separate from the KV body map — these are authored titles."""
    if not isinstance(text, str):
        return None
    return _STRUCTURAL.get(text)
