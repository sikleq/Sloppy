"""Regenerate data/creep_abilities.json from the latest npc_units.txt KV file.

Run after a new patch drops (once fetch_npc_history.py has updated the stats):

    python scripts/build_creep_abilities.py

Or specify a patch explicitly:

    python scripts/build_creep_abilities.py 7.42

Reads:  data/stats/<patch>/npc_units.txt
Writes: data/creep_abilities.json

The output maps npc slug -> list of ability slugs, filtering out generic
non-informative entries (neutral_upgrade, creep_piercing, ability_hidden,
ability_deward). Used by generate_patch_code_v2.py to auto-split neutral
creep patch notes into per-ability ability() blocks.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_DIR = os.path.join(HERE, 'data', 'stats')
OUT_PATH = os.path.join(HERE, 'data', 'creep_abilities.json')

ABIL_FIELDS = ['Ability1', 'Ability2', 'Ability3', 'Ability4', 'Ability5']
SKIP_SLUGS = {'ability_hidden', 'ability_deward', 'neutral_upgrade', 'creep_piercing'}


def _latest_patch():
    """Return the lexicographically latest patch folder under data/stats/."""
    def _ver_key(v):
        return tuple(int(p) if p.isdigit() else p for p in re.split(r'(\d+)', v))

    folders = [
        d for d in os.listdir(STATS_DIR)
        if os.path.isdir(os.path.join(STATS_DIR, d))
    ]
    if not folders:
        return None
    return sorted(folders, key=_ver_key)[-1]


def build(patch=None):
    if patch is None:
        patch = _latest_patch()
    if patch is None:
        print('No patch folders found under data/stats/')
        return

    kv_path = os.path.join(STATS_DIR, patch, 'npc_units.txt')
    if not os.path.exists(kv_path):
        print(f'Not found: {kv_path}')
        return

    print(f'Reading {kv_path} ...')
    kv_lines = open(kv_path, encoding='utf-8').read().splitlines()
    n_lines = len(kv_lines)

    head_re = re.compile(
        r'^\s*"(npc_dota_(?:neutral_[a-z0-9_]+|dark_troll_warlord_skeleton_warrior))"\s*$'
    )
    field_re = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s+"([^"]+)"')

    result = {}
    i = 0
    while i < n_lines:
        m = head_re.match(kv_lines[i])
        if not m:
            i += 1
            continue
        name = m.group(1)
        j = i + 1
        while j < n_lines and '{' not in kv_lines[j]:
            j += 1
        if j >= n_lines:
            break
        depth = kv_lines[j].count('{') - kv_lines[j].count('}')
        j += 1
        abilities_raw = {}
        while j < n_lines and depth > 0:
            line = kv_lines[j]
            if depth == 1:
                fm = field_re.match(line)
                if fm and fm.group(1) in ABIL_FIELDS:
                    abilities_raw[fm.group(1)] = fm.group(2)
            depth += line.count('{') - line.count('}')
            j += 1
        slugs = [
            abilities_raw[f] for f in ABIL_FIELDS
            if f in abilities_raw and abilities_raw[f] not in SKIP_SLUGS
        ]
        result[name] = slugs
        i = j

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    non_empty = sum(1 for v in result.values() if v)
    print(f'Written {len(result)} creeps ({non_empty} with abilities) -> {OUT_PATH}')
    print(f'Source patch: {patch}')


if __name__ == '__main__':
    patch_arg = sys.argv[1] if len(sys.argv) > 1 else None
    build(patch_arg)
