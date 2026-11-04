"""Valve's patch-note strings and the game's lists the generator reads once at import."""
import json
import os
import re

from .common import _HERE

# ---------- PATCHNOTES LOC LOADER ----------

def _load_patchnotes_loc(version):
    """Parse data/patchnotes_english.txt and return a per-hero lookup.

    Returns dict: hero_slug → {normalized_text → ability_slug}
    where ability_slug is the slug extracted from the key, or None for
    hero-level (stat) notes.

    Key format: DOTA_Patch_{ver}_{hero}[_{ability_slug}[_{N}[_info]]]
    Example: DOTA_Patch_7_39_kez_kez_kazurai_katana_4
    """
    p = os.path.join(_HERE, 'data', 'patchnotes_english.txt')
    if not os.path.exists(p):
        return {}
    ver_key = version.replace('.', '_')
    prefix = f'DOTA_Patch_{ver_key}_'
    result = {}  # hero_slug -> {text_norm -> ability_slug or None}
    # Regex to parse KV lines: "KEY"\t\t"VALUE"
    _KV = re.compile(r'^"([^"]+)"\s+"([^"]*)"')
    with open(p, encoding='utf-8') as f:
        for line in f:
            m = _KV.match(line.strip())
            if not m:
                continue
            key, text = m.group(1), m.group(2).strip()
            if not key.startswith(prefix):
                continue
            rest = key[len(prefix):]  # e.g. "kez_kez_kazurai_katana_4" or "kez_3"
            # Split to identify hero slug (first token) vs ability slug
            parts = rest.split('_')
            if not parts:
                continue
            hero_slug = parts[0]
            # The ability slug follows the hero slug. Hero slugs can be
            # multi-word (e.g. "ancient_apparition"), so we match greedily:
            # look for the longest prefix of parts that is a known hero slug,
            # then the next segment(s) before a trailing _N or _info form the
            # ability slug.  We approximate: if parts[1] == hero_slug_part[0]
            # (i.e. the ability slug also starts with the hero slug), then the
            # ability slug starts at parts[0] and extends until we hit a
            # pure-numeric suffix or "_info".
            # Simpler heuristic: strip trailing _N and _info suffixes, then
            # if what remains has more tokens than the hero part, the extras
            # are the ability slug.
            tail = parts[1:]  # everything after hero_slug
            # Strip trailing _info
            if tail and tail[-1] == 'info':
                tail = tail[:-1]
            # Strip trailing pure-numeric token
            if tail and tail[-1].isdigit():
                tail = tail[:-1]
            # Remaining tail: if non-empty AND starts with hero_slug (ability
            # slugs typically start with hero slug, e.g. kez_kazurai_katana),
            # reconstruct ability slug as hero_slug + _ + '_'.join(tail).
            if tail and tail[0] == hero_slug:
                ability_slug = '_'.join([hero_slug] + tail[1:]) if len(tail) > 1 else None
            elif tail:
                # ability slug doesn't share hero prefix (rare) — use as-is
                ability_slug = '_'.join([hero_slug] + tail)
            else:
                ability_slug = None  # hero-level note
            text_norm = re.sub(r'\s+', ' ', text).lower().strip()
            # a set: the same text can belong to two abilities (7.37d Omniknight: Purification and Repel both "Mana
            # Cost increased from 80/95/110/125 to 90/105/120/135") — the last key won and the first row read as misplaced
            if text_norm:
                result.setdefault(hero_slug, {}).setdefault(text_norm, set()).add(ability_slug)
    return result


# ---------- LOOKUP TABLES ----------

def _load_itemlist():
    """Item id → (display_name, engine_slug). Loaded from
    /datafeed/itemlist (cached at data/itemlist.json)."""
    p = os.path.join(_HERE, 'data', 'itemlist.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    out = {}
    for it in d.get('result', {}).get('data', {}).get('itemabilities', []):
        out[it['id']] = (it.get('name_loc') or it.get('name'),
                         (it.get('name') or '').replace('item_', ''))
    return out


def _load_herolist():
    """Hero id → (display_name, engine_slug)."""
    p = os.path.join(_HERE, 'data', 'herolist.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    out = {}
    for h in d.get('result', {}).get('data', {}).get('heroes', []):
        out[h['id']] = (h.get('name_loc') or h.get('name'),
                        (h.get('name') or '').replace('npc_dota_hero_', ''))
    return out


def _load_abilities():
    """Ability id → (display_name, engine_slug). Loaded from
    data/abilities_by_id.json which is fetched per-hero from
    /datafeed/herodata?hero_id=X. Regenerate via:

        python -c "from generate_patch_code_v2 import _refresh_abilities; _refresh_abilities()"
    """
    p = os.path.join(_HERE, 'data', 'abilities_by_id.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    out = {}
    for aid_str, meta in d.items():
        aid = int(aid_str)
        out[aid] = (meta.get('dname'), meta.get('slug'))
    return out


ITEMS = _load_itemlist()
HEROES = _load_herolist()
ABILS = _load_abilities()


def _load_creep_abilities():
    """npc slug → [ability slugs] (from data/creep_abilities.json)."""
    p = os.path.join(_HERE, 'data', 'creep_abilities.json')
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding='utf-8'))


def _load_abilities_slim():
    """ability slug → {'dname': ...} (from data/abilities_slim.json)."""
    p = os.path.join(_HERE, 'data', 'abilities_slim.json')
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding='utf-8'))


CREEP_ABILS = _load_creep_abilities()
ABILS_SLIM = _load_abilities_slim()

# Section order used when emitting the scaffold.
# Neither the datafeed JSON key order nor patchnotes_english.txt reliably
# encodes the official patch-page ordering — Valve's internal order can differ
# from what dota2.com displays. After generation, reorder sections manually
# to match the official page if needed.
_CANONICAL_SECTION_ORDER = [
    'general_notes',
    'neutral_creeps',
    'items',
    'neutral_items',
    'heroes',
]


# ---------- TAG HEURISTICS ----------

def _strip_html(s):
    """Drop HTML markup so heuristics see only the plain text."""
    return re.sub(r'<[^>]+>', '', s or '')
