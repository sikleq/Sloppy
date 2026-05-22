"""fetch_ability_history.py — качает исторические npc_abilities.txt из
dotabuff/d2vpkr и сохраняет компактные per-patch JSON
`data/stats/<patch>/npc_abilities.json` с балансными полями способностей
нейтралов (cooldown, manacost, damage, cast range + все AbilityValues).

Нужно для полноценного чейнджлога способностей: build_creeps.py показывает в
ячейке Ability N не только смену самой способности, но и изменения её
значений (перезарядка, манакост, длительности и т.д.) за 7.08→7.41c.

Источник и схема сопоставления патч↔коммит — те же, что в
fetch_npc_history.py (по дате из site_meta.json). Сырьё кэшируется по SHA в
`.cache/d2vpkr_abilities/`. Сет слугов берётся из npc_units.json (только
способности, которые когда-либо были у нейтралов).

Запуск:
    python scripts/fetch_ability_history.py            # добить недостающие
    python scripts/fetch_ability_history.py --force     # перекачать все
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

ROOT = Path(__file__).resolve().parent.parent
STATS_DIR = ROOT / "data" / "stats"
META_PATH = ROOT / "data" / "site_meta.json"
CACHE_DIR = ROOT / ".cache" / "d2vpkr_abilities"

REPO = "dotabuff/d2vpkr"
FILE_PATH = "dota/scripts/npc/npc_abilities.txt"
RAW_TMPL = "https://raw.githubusercontent.com/" + REPO + "/{sha}/" + FILE_PATH

ABILITY_SKIP = {"neutral_upgrade", "creep_piercing"}
# Top-level numeric stats worth a changelog.
TOP_FIELDS = {
    "AbilityCooldown", "AbilityManaCost", "AbilityCastRange", "AbilityCastPoint",
    "AbilityDamage", "AbilityChannelTime", "AbilityDuration",
    # Enum/string fields (no %, shown humanised): damage type, spell immunity,
    # dispellability.
    "AbilityUnitDamageType", "SpellImmunityType", "SpellDispellableType",
}
HEADER_RE = re.compile(r'^\s*"([a-z][a-z0-9_]+)"\s*$')
KV_RE = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s+"([^"]*)"')
BARE_RE = re.compile(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*$')


def neutral_ability_slugs():
    """Union of non-skip ability slugs ever used by neutrals (all patches)."""
    slugs = set()
    for d in STATS_DIR.iterdir():
        p = d / "npc_units.json"
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for e in data.values():
            if not isinstance(e, dict):
                continue
            for i in range(1, 6):
                s = e.get(f"Ability{i}")
                if s and s not in ABILITY_SKIP:
                    slugs.add(s)
    return slugs


def parse_abilities(text, wanted):
    """Parse npc_abilities.txt → {slug: {field: value}} for wanted slugs.
    Captures TOP_FIELDS plus every AbilityValues leaf (simple `k v` and
    `k { value X }` forms)."""
    lines = text.splitlines()
    n = len(lines)
    out = {}
    i = 0
    while i < n:
        m = HEADER_RE.match(lines[i])
        if not m or m.group(1) not in wanted:
            i += 1
            continue
        slug = m.group(1)
        j = i + 1
        while j < n and "{" not in lines[j]:
            j += 1
        if j >= n:
            break
        depth = lines[j].count("{") - lines[j].count("}")
        j += 1
        entry = {}
        mode = None              # None | 'av' (AbilityValues) | 'sp' (AbilitySpecial)
        base_depth = None        # depth at which the special block opened
        entered = False          # have we actually descended into the block?
        pending = None           # AV child key awaiting its { value X }
        while j < n and depth > 0:
            line = lines[j]
            opens = line.count("{")
            closes = line.count("}")
            if mode is None:
                if depth == 1:
                    kv = KV_RE.match(line)
                    bare = BARE_RE.match(line)
                    if kv and kv.group(1) in TOP_FIELDS:
                        entry[kv.group(1)] = kv.group(2)
                    elif bare and bare.group(1) == "AbilityValues":
                        mode, base_depth, entered, pending = "av", depth, False, None
                    elif bare and bare.group(1) == "AbilitySpecial":
                        # legacy (pre-7.36): numbered subblocks with var_type
                        mode, base_depth, entered = "sp", depth, False
            elif mode == "av":
                if depth == base_depth + 1:
                    entered = True
                    kv = KV_RE.match(line)
                    bare = BARE_RE.match(line)
                    if kv:
                        entry["av_" + kv.group(1)] = kv.group(2)
                        pending = None
                    elif bare:
                        pending = bare.group(1)
                    # brace-only lines ({ / }) leave `pending` untouched
                elif depth == base_depth + 2 and pending:
                    kv = KV_RE.match(line)
                    if kv and kv.group(1) == "value":
                        entry["av_" + pending] = kv.group(2)
                        pending = None
            elif mode == "sp":
                if depth >= base_depth + 1:
                    entered = True
                # The real value sits inside the numbered subblock (depth+2),
                # alongside a var_type line we skip.
                if depth == base_depth + 2:
                    kv = KV_RE.match(line)
                    if kv and kv.group(1) != "var_type":
                        entry["av_" + kv.group(1)] = kv.group(2)
            depth += opens - closes
            if mode is not None and entered and depth <= base_depth:
                mode, base_depth, entered, pending = None, None, False, None
            j += 1
        out[slug] = entry
        i = j
    return out


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
        res = subprocess.run(["gh", "api", api], capture_output=True,
                             text=True, check=True)
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
        text = r.read().decode("utf-8", errors="replace")
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
        print("X site_meta.json не найден — сначала build_patch.py")
        return 1
    patch_dates = load_patch_dates()
    patches = sorted((v for v in patch_dates if (STATS_DIR / v).is_dir()),
                     key=lambda v: patch_dates[v])
    if not patches:
        print("X нет папок data/stats/<patch>/")
        return 1
    wanted = neutral_ability_slugs()
    print(f"Слугов способностей нейтралов: {len(wanted)}")
    print("Индексирую коммиты d2vpkr (npc_abilities.txt)…")
    commit_idx = fetch_commit_index()
    if not commit_idx:
        print("X не удалось получить коммиты")
        return 1
    print("  {} коммитов, {}—{}".format(
        len(commit_idx), commit_idx[0][0], commit_idx[-1][0]))

    far = date(9999, 1, 1)
    written = skipped = missing = 0
    latest = patches[-1]
    for i, ver in enumerate(patches):
        out_path = STATS_DIR / ver / "npc_abilities.json"
        if out_path.exists() and not force and ver != latest:
            skipped += 1
            continue
        win_end = patch_dates[patches[i + 1]] if i + 1 < len(patches) else far
        sha = commit_for_window(commit_idx, win_end)
        if not sha:
            missing += 1
            continue
        try:
            parsed = parse_abilities(fetch_raw(sha), wanted)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {ver}: {e}")
            missing += 1
            continue
        out_path.write_text(
            json.dumps(parsed, ensure_ascii=False, separators=(",", ":"),
                       sort_keys=True),
            encoding="utf-8")
        written += 1
        print(f"  + {ver} ← {sha[:7]} ({len(parsed)} способностей)")
    print(f"Готово: записано {written}, пропущено {skipped}, без данных {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
