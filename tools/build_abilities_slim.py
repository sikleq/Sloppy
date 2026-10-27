"""data/abilities_slim.json from the game files of the newest snapshot — ability slug -> {"dname", "is_innate"}.

Until 2026-10-21 the file had no writer (a one-off copy of a community dump, May 2026), so a new or renamed
ability never reached it: the slug audit failed and the innate marker went missing. This rebuilds it from

  data/stats/<latest>/npc_abilities.txt + heroes/npc_dota_hero_*.txt   (the abilities, `"Innate" "1"`)
  data/abilities_english.txt                                            (`DOTA_Tooltip_ability_<slug>` = dname)

  dname      the tooltip name; `{s:<value>}` placeholders filled from the ability's AbilityValues (talents:
             "+{s:value} Health" -> "+100 Health"); no tooltip name -> no key
  is_innate  only when the KV says `"Innate" "1"`

MERGE, never prune: an ability gone from the game keeps its row, because old patch pages still name it (a page of
7.36 shows abilities removed since). An existing row is only replaced when the newest game files say something
else about that slug.

    python tools/build_abilities_slim.py            # write data/abilities_slim.json
    python tools/build_abilities_slim.py --check    # exit 1 when it is stale (what would change is printed)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "data", "abilities_slim.json")
# ability names: abilities_english.txt only (dota_english.txt also names old event abilities — seasonal_ti11_duel
# "The Gauntlet" — which the table never carried)
LOC_FILES = ("abilities_english.txt",)
_LOC_LINE = re.compile(r'^\s*"([^"]+)"\s*"((?:[^"\\]|\\.)*)"', re.M)  # Valve sometimes writes "key""text"
_PLACEHOLDER = re.compile(r"\{s:([A-Za-z0-9_]+)\}")


def load_loc(data_dir=None):
    """{lower-case key: text} of the game's English localisation files (data/)."""
    data_dir = data_dir or os.path.join(ROOT, "data")
    out = {}
    for name in LOC_FILES:
        path = os.path.join(data_dir, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            for m in _LOC_LINE.finditer(f.read()):
                out.setdefault(m.group(1).lower(), m.group(2))
    return out


def ability_blocks(stats_dir):
    """{slug: KV block} of npc_abilities.txt + every per-hero file, in file order."""
    from patch.kv import parse_kv
    from patch.kv import hero_ability_blocks
    blocks = {}
    path = os.path.join(stats_dir, "npc_abilities.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            kv = parse_kv(f.read())
        blocks.update(next(iter(kv.values()), {}) if kv else {})
    for path in sorted(glob.glob(os.path.join(stats_dir, "heroes", "npc_dota_hero_*.txt"))):
        with open(path, encoding="utf-8", errors="replace") as f:
            blocks.update(hero_ability_blocks(parse_kv(f.read())))
    return {k: v for k, v in blocks.items() if isinstance(v, dict) and k != "Version"}


def _values(block):
    """{name: first number} of an ability's AbilityValues / AbilitySpecial."""
    out = {}
    for name, val in (block.get("AbilityValues") or {}).items():
        if isinstance(val, dict):
            val = val.get("value", "")
        out[name] = str(val)
    for entry in (block.get("AbilitySpecial") or {}).values():
        if isinstance(entry, dict):
            for name, val in entry.items():
                if name not in ("var_type",) and isinstance(val, str):
                    out.setdefault(name, val)
    return out


def talent_values(blocks):
    """{talent slug: {value name: raw}} — a talent's numbers live in the abilities it changes
    ("arrow_damage_pct" { "value" "80 100", "special_bonus_unique_drow_ranger_1" "+25" })."""
    out = {}
    for block in blocks.values():
        for name, val in (block.get("AbilityValues") or {}).items():
            if not isinstance(val, dict):
                continue
            for key, raw in val.items():
                if key.startswith("special_bonus_") and isinstance(raw, str):
                    out.setdefault(key, {}).setdefault(name, raw)
    return out


def _fmt(raw):
    """'+25' / '-18%' / '-1.0' / '80 100 120' -> '25' / '18' / '1.0' / '80' (the sign and % are in the text;
    the number is kept as the game writes it)."""
    first = raw.split()[0] if raw.split() else raw
    return first.lstrip("+-xX").rstrip("%")


def dname(slug, block, loc, talents=None):
    """The tooltip name of an ability with its {s:...} placeholders filled, or None."""
    text = loc.get(("DOTA_Tooltip_ability_" + slug).lower())
    if text is None:
        return None
    vals = _values(block)
    own = (talents or {}).get(slug, {})

    def fill(m):
        name = m.group(1)
        if name in vals:
            return _fmt(vals[name])
        bare = name[len("bonus_"):] if name.startswith("bonus_") else name
        for key in (bare, name):
            if key in own:
                return _fmt(own[key])
        return m.group(0)
    return _PLACEHOLDER.sub(fill, text)


def entry(slug, block, loc, talents=None):
    out = {}
    name = dname(slug, block, loc, talents)
    if name is not None:
        out["dname"] = name
    if str(block.get("Innate", "")).strip() == "1":
        out["is_innate"] = True
    return out


def build(stats_dir, loc, current):
    """The merged table: every current row kept, every ability of the snapshot (re)computed."""
    merged = dict(current)
    blocks = ability_blocks(stats_dir)
    talents = talent_values(blocks)
    for slug, block in blocks.items():
        merged[slug] = entry(slug, block, loc, talents)
    return merged


def changes(current, merged):
    """[(slug, old row or None, new row)] — what a write would change."""
    return [(k, current.get(k), v) for k, v in merged.items() if current.get(k) != v]


def dumps(table):
    return json.dumps(table, ensure_ascii=False, separators=(",", ":"))


def main(argv):
    from patch.meta import latest_stats_version
    check = "--check" in argv
    ver = latest_stats_version()
    with open(OUT, encoding="utf-8") as f:
        current = json.load(f)
    merged = build(os.path.join(ROOT, "data", "stats", ver), load_loc(), current)
    diff = changes(current, merged)
    for slug, old, new in diff:
        print(f"  {slug}: {old} -> {new}")
    print(f"abilities_slim.json vs data/stats/{ver}: {len(diff)} row(s) {'would change' if check else 'changed'}")
    if check:
        return 1 if diff else 0
    if diff:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(dumps(merged))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
