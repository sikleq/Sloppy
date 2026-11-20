"""The neutral creeps' abilities for fetch_icons.py (owner 2026-11-20 "научи").

The script finds the icons it needs in the built pages. Neutral Stats / Neutral Abilities show an ability's name as
text when its icon file is missing, so a missing creep icon was never named there. 7.42's Odobenus Blight and Hurl Big
Boulder stayed iconless: the game draws them from another file (KV AbilityTextureName
odobenus_footman_odobenus_blight / mud_golem_hurl_boulder), and fetch_icons.py read that key for heroes only.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def creep_ability_slugs():
    """every ability slug a neutral creep row shows (the rows Neutral Stats and Neutral Abilities are built from)"""
    import csv
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from builders import creeps
    with open(ROOT / "data" / "creeps_raw.csv", encoding="utf-8") as f:
        rows = creeps.build_rows(list(csv.reader(f)), creeps.load_sources())
    slugs = {r["data"].get(k + "_slug") for r in rows for k in creeps.ABILITY_COLS if r["data"].get(k)}
    slugs.discard(None)
    slugs.discard("")
    if not slugs:
        raise RuntimeError("no neutral creep abilities found: data/creeps_raw.csv or the stats snapshot is missing")
    return slugs


_KEY = re.compile(r'^\s*"([^"]+)"\s*(?:"([^"]*)")?\s*(?://.*)?$')


def kv_texture_names(text):
    """{top-level ability: its AbilityTextureName} of an npc_abilities.txt (KeyValues) text"""
    out, depth, current, pending = {}, 0, None, None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("{"):
            depth += 1
            if depth == 2:
                current = pending
            continue
        if stripped.startswith("}"):
            depth -= 1
            if depth < 2:
                current = None
            continue
        m = _KEY.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if value is None:
            pending = key
        elif depth == 2 and current and key == "AbilityTextureName":
            out[current] = value
    return out


def creep_texture_name(slug):
    """the file the game draws a neutral ability with when it is not <slug>.png, from the newest stats snapshot"""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from patch.meta import latest_stats_version
    path = ROOT / "data" / "stats" / latest_stats_version() / "npc_abilities.txt"
    return kv_texture_names(path.read_text(encoding="utf-8", errors="ignore")).get(slug)
