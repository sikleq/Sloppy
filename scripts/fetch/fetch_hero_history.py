"""fetch_hero_history.py — historical npc_heroes.txt from dotabuff/d2vpkr →
compact per-patch `data/stats/<patch>/heroes_raw.json` carrying the hero
stats that the slim heroes.json scrape DOESN'T have (vision, projectile
speed, base attack speed, turn rate, collision hull, bound radius).

Mirrors scripts/fetch/fetch_npc_history.py exactly (same d2vpkr commit-by-date
matching, same SHA disk cache), just a different file + parser. Needed so
the Hero Stats table (builders/heroes_stats.py) can show per-patch change
history for those raw-only fields (e.g. Gyrocopter night vision 7.41d).

    python scripts/fetch/fetch_hero_history.py           # backfill missing + refresh latest
    python scripts/fetch/fetch_hero_history.py --force    # re-fetch every patch

After a new patch ships: create data/stats/<patch>/ and run — it fills in
heroes_raw.json for the newcomer.

7.41f+ (per-hero KV layout): a patch folder that has the local per-hero files
(data/stats/<patch>/heroes/*.txt) is built FROM THEM, not from d2vpkr. d2vpkr's
npc_heroes.txt became a #base include list in 7.41f and its commits can predate the
release, which silently froze 7.41f at the 7.41e values (Earth Spirit / KotL / Warlock
base attack speed). The parent template npc_dota_hero_base comes from
data/stats/<patch>/npc_dota_hero_base.txt when present (extract it from the game VPK),
otherwise it is carried over from the previous patch with a warning.
"""
import json
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
STATS_DIR = ROOT / "data" / "stats"
META_PATH = ROOT / "data" / "site_meta.json"
CACHE_DIR = ROOT / ".cache" / "d2vpkr_heroes"

REPO = "dotabuff/d2vpkr"
FILE_PATH = "dota/scripts/npc/npc_heroes.txt"
RAW_TMPL = "https://raw.githubusercontent.com/" + REPO + "/{sha}/" + FILE_PATH

# Hero fields to extract. We carry the FULL stat set (not just raw-only
# fields) so build_heroes_stats can use d2vpkr as the AUTHORITATIVE history
# source — the muk-as/DOTA2_CLIENT slim scrape (heroes.json) was found to
# be one-patch-late for some balance changes (e.g. Treant 7.34d Base
# Damage decrease shows up at 7.34e in muk-as data, but at 7.34d in
# d2vpkr, which matches the Valve patch notes).
HERO_FIELDS = (
    # Raw-only (not in heroes.json):
    "VisionDaytimeRange", "VisionNighttimeRange", "ProjectileSpeed",
    "BaseAttackSpeed", "MovementTurnRate", "BoundsHullName", "RingRadius",
    "AttackAcquisitionRange", "AttackAnimationPoint",
    # Core stats — d2vpkr is the authoritative timing source.
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


def load_patch_dates():
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    out = {}
    for ver, ds in meta.get("patch_dates", {}).items():
        try:
            d, mth, y = (int(x) for x in ds.split("."))
            out[ver] = date(y, mth, d)
        except (ValueError, AttributeError):
            continue
    return out


def _fetch_page(page):
    api = "repos/{}/commits?path={}&per_page=100&page={}".format(
        REPO, FILE_PATH, page)
    try:
        res = subprocess.run(["gh", "api", api],
                             capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except (FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError):
        pass
    with urllib.request.urlopen("https://api.github.com/" + api) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_commit_index():
    data, page = [], 1
    while True:
        chunk = _fetch_page(page)
        if not chunk:
            break
        data.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    idx = []
    for c in data:
        sha = c.get("sha")
        ds = c.get("commit", {}).get("author", {}).get("date", "")[:10]
        if not sha or not ds:
            continue
        y, mth, d = (int(x) for x in ds.split("-"))
        idx.append((date(y, mth, d), sha))
    idx.sort()
    return idx


def fetch_raw(sha):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / (sha + ".txt")
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    with urllib.request.urlopen(RAW_TMPL.format(sha=sha)) as r:
        text = r.read().decode("utf-8")
    cached.write_text(text, encoding="utf-8")
    return text


def commit_for_window(commit_idx, win_end):
    chosen = None
    for cdate, sha in commit_idx:
        if cdate < win_end:
            chosen = sha
        else:
            break
    return chosen


def main():
    force = "--force" in sys.argv
    if not META_PATH.exists():
        print("X data/site_meta.json не найден — сначала запусти builders/patch.py")
        return 1
    patch_dates = load_patch_dates()
    patches = sorted((v for v in patch_dates if (STATS_DIR / v).is_dir()),
                     key=lambda v: patch_dates[v])
    if not patches:
        print("X нет папок data/stats/<patch>/")
        return 1
    # Local per-hero KV first (7.41f+): no network, always rebuilt (cheap, exact).
    local_done = set()
    for i, ver in enumerate(patches):
        prev = STATS_DIR / patches[i - 1] / "heroes_raw.json" if i else None
        parsed = build_from_local(STATS_DIR / ver, prev)
        if parsed is not None:
            _write(STATS_DIR / ver / "heroes_raw.json", parsed)
            local_done.add(ver)
            print("  + {} ← локальные heroes/*.txt ({} героев)".format(ver, len(parsed)))
    if all(v in local_done or ((STATS_DIR / v / "heroes_raw.json").exists() and not force)
           for v in patches[:-1]) and patches[-1] in local_done:
        print("Готово: всё из локальных файлов / кэша")
        return 0
    print("Индексирую коммиты d2vpkr (npc_heroes.txt)…")
    commit_idx = fetch_commit_index()
    if not commit_idx:
        print("X не удалось получить список коммитов")
        return 1
    print("  {} коммитов, {}—{}".format(len(commit_idx), commit_idx[0][0], commit_idx[-1][0]))

    far_future = date(9999, 1, 1)
    written = skipped = missing = 0
    latest = patches[-1]
    for i, ver in enumerate(patches):
        out_path = STATS_DIR / ver / "heroes_raw.json"
        if ver in local_done:
            continue
        if out_path.exists() and not force and ver != latest:
            skipped += 1
            continue
        win_end = patch_dates[patches[i + 1]] if i + 1 < len(patches) else far_future
        sha = commit_for_window(commit_idx, win_end)
        if not sha:
            print("  - {}: нет коммита до {}".format(ver, win_end))
            missing += 1
            continue
        try:
            parsed = parse_npc_heroes(fetch_raw(sha))
        except Exception as e:  # noqa: BLE001
            print("  ! {}: ошибка {}".format(ver, e))
            missing += 1
            continue
        out_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=0,
                       separators=(",", ":"), sort_keys=True),
            encoding="utf-8")
        written += 1
        print("  + {} ← d2vpkr {} ({} героев)".format(ver, sha[:7], len(parsed)))
    print("Готово: записано {}, пропущено {}, без данных {}".format(
        written, skipped, missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
