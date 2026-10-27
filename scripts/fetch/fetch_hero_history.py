"""fetch_hero_history.py — npc_heroes.txt of every patch from our game-files store (patch/game_files.py: the
patch's own build) → compact per-patch `data/stats/<patch>/heroes_raw.json` carrying the hero stats that the
slim heroes.json scrape DOESN'T have (vision, projectile speed, base attack speed, turn rate, collision hull,
bound radius), plus the core stats. Needed so the Hero Stats table (builders/heroes_stats.py) can show per-patch
change history for those raw-only fields (e.g. Gyrocopter night vision 7.41d).

    python scripts/fetch/fetch_hero_history.py           # backfill missing + refresh latest
    python scripts/fetch/fetch_hero_history.py --force    # rebuild every patch

7.41f+ (per-hero KV layout): npc_heroes.txt is a #base include list; the hero stats are read from the per-hero
files scripts/npc/heroes/*.txt of the same patch (store), or — for a patch not in the store yet — from
data/stats/<patch>/heroes/*.txt with npc_dota_hero_base.txt (carried over from the previous patch with a warning
when missing). Until 2026-10-24 the source was dotabuff/d2vpkr ("the last commit before the next patch": the
end-of-patch state, and 7.41f froze at 7.41e values because d2vpkr's commits predated the release).
"""
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
STATS_DIR = ROOT / "data" / "stats"
sys.path.insert(0, str(ROOT))
from patch.meta import RELEASE_HISTORY  # noqa: E402
from patch import game_files  # noqa: E402

# Hero fields to extract: the raw-only ones and the full core stat set.
HERO_FIELDS = (
    # Raw-only (not in heroes.json):
    "VisionDaytimeRange", "VisionNighttimeRange", "ProjectileSpeed",
    "BaseAttackSpeed", "MovementTurnRate", "BoundsHullName", "RingRadius",
    "AttackAcquisitionRange", "AttackAnimationPoint",
    # Core stats.
    "StatusHealth", "StatusMana", "StatusHealthRegen", "StatusManaRegen",
    "ArmorPhysical", "MagicalResistance",
    "AttackDamageMin", "AttackDamageMax", "AttackRate", "AttackRange",
    "AttackCapabilities",
    "MovementSpeed",
    "AttributePrimary",
    "AttributeBaseStrength", "AttributeStrengthGain",
    "AttributeBaseAgility", "AttributeAgilityGain",
    "AttributeBaseIntelligence", "AttributeIntelligenceGain",
)
FIELD_RE = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s+"([^"]*)"')
KEY_RE = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*$')


def parse_npc_heroes(text):
    """npc_heroes.txt → {npc_dota_hero_x: {field: value}} for HERO_FIELDS.
    Top-level hero blocks live at depth 1 (DOTAHeroes > hero > field = depth
    2). Block-opener brace lines may be bare '{' or share a line; whole-line
    // comments can contain braces, so skip them before any brace counting."""
    out = {}
    depth = 0
    cur = None
    for line in text.splitlines():
        st = line.strip()
        if st.startswith("//"):
            continue
        fm = FIELD_RE.match(line)
        if fm:
            if depth == 2 and cur and fm.group(1) in HERO_FIELDS:
                out[cur][fm.group(1)] = fm.group(2)
            continue
        km = KEY_RE.match(line)
        if km:
            if depth == 1 and km.group(1).startswith("npc_dota_hero_"):
                cur = km.group(1)
                out.setdefault(cur, {})
            continue
        # brace-only (or brace-containing) line. ONLY reset cur on a closing
        # brace that exits the hero block — every empty/comment line between
        # a hero NAME line (depth 1) and its opening `{` would otherwise null
        # out cur, dropping every field in that hero. (Buggy before — caused
        # `heroes_raw.json` to be entirely empty for every hero, every patch.)
        delta = st.count("{") - st.count("}")
        depth += delta
        if delta < 0 and depth < 2:
            cur = None
    return out


def build_from_local(ver_dir, prev_raw_path=None):
    """heroes_raw for a patch that has the local per-hero KV files, else None."""
    # Only the 7.41f+ layout: npc_heroes.txt is a #base include list and the per-hero files
    # carry the hero stats. (Older folders also have heroes/*.txt, but those hold only the
    # abilities — building from them would wipe the hero stats.)
    root_kv = ver_dir / "npc_heroes.txt"
    if not root_kv.exists() or '#base "heroes/' not in root_kv.read_text(encoding="utf-8", errors="ignore"):
        return None
    heroes_dir = ver_dir / "heroes"
    files = sorted(heroes_dir.glob("npc_dota_hero_*.txt")) if heroes_dir.is_dir() else []
    if not files:
        return None
    out = {}
    for f in files:
        out.update(parse_npc_heroes(f.read_text(encoding="utf-8", errors="ignore")))
    base_txt = ver_dir / "npc_dota_hero_base.txt"
    if base_txt.exists():
        out.update(parse_npc_heroes(base_txt.read_text(encoding="utf-8", errors="ignore")))
    elif prev_raw_path and prev_raw_path.exists():
        prev = json.loads(prev_raw_path.read_text(encoding="utf-8"))
        if "npc_dota_hero_base" in prev:
            out["npc_dota_hero_base"] = prev["npc_dota_hero_base"]
            print("  ! {}: npc_dota_hero_base.txt нет — шаблон взят из {}".format(
                ver_dir.name, prev_raw_path.parent.name))
    return out


def _write(out_path, parsed):
    out_path.write_text(
        json.dumps(parsed, ensure_ascii=False, indent=0,
                   separators=(",", ":"), sort_keys=True),
        encoding="utf-8")


def build_from_store(ver):
    """heroes_raw of a patch from the store, else None (patch not in the store)."""
    text = game_files.npc(ver, "npc_heroes.txt")
    if text is None:
        return None
    if "#base" not in text[:4096]:
        return parse_npc_heroes(text)
    out = {}                                     # 7.41f+: include list -> the per-hero files of the same patch
    for rel in game_files.listing(ver, "scripts/npc/heroes"):
        if re.search(r"/npc_dota_hero_[a-z0-9_]+\.txt$", rel):
            out.update(parse_npc_heroes(game_files.read(ver, rel) or ""))
    return out


def main():
    force = "--force" in sys.argv
    patches = [p["version"] for p in reversed(RELEASE_HISTORY) if (STATS_DIR / p["version"]).is_dir()]
    if not patches:
        print("X нет папок data/stats/<patch>/")
        return 1
    written = skipped = missing = 0
    latest = patches[-1]
    for i, ver in enumerate(patches):
        out_path = STATS_DIR / ver / "heroes_raw.json"
        if out_path.exists() and not force and ver != latest:
            skipped += 1
            continue
        parsed, src = build_from_store(ver), "хранилище"
        if parsed is None:                       # a new patch not in the store yet: the repo's own per-hero files
            prev = STATS_DIR / patches[i - 1] / "heroes_raw.json" if i else None
            parsed, src = build_from_local(STATS_DIR / ver, prev), "локальные heroes/*.txt"
        if not parsed:
            print("  - {}: нет данных ни в хранилище, ни локально".format(ver))
            missing += 1
            continue
        _write(out_path, parsed)
        written += 1
        print("  + {} ← {} ({} героев)".format(ver, src, len(parsed)))
    print("Готово: записано {}, пропущено {}, без данных {}".format(
        written, skipped, missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
