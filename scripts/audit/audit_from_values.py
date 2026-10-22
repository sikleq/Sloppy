"""audit_from_values.py — find hero rows whose "from X" value is not what the game had before the patch.

Valve's notes sometimes quote a value that an earlier patch already changed (7.41 Kinetic Fence:
"Cooldown decreased from 20/18/16/14s" — 7.38 had made it 20/17/14/11s, owner 2026-10-22).

For every row "... from X to Y" under a hero on a built patch page: X should be a value in that hero's
KV of the previous snapshot. A row is reported only when Y IS in this patch's KV (so the row is about a
number the KV holds as written) and X is NOT in the previous one. A candidate list for a human, not a gate:
values the KV keeps in another unit (0.2 for 20%) never get here because Y would not match either.

    python scripts/audit/audit_from_values.py [7.41 7.40 ...]
"""
import html as _html
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from builders.silent import _decode_bytes  # noqa: E402

STATS = ROOT / "data" / "stats"
PAGES = ROOT / "dist" / "patches"

_NUM = r"-?\d+(?:\.\d+)?"
_VAL = rf"{_NUM}(?:\s*/\s*{_NUM})*"
_FROM_TO = re.compile(rf"\bfrom\s+\+?({_VAL})\s*(?:s|%|°)?\s+to\s+\+?({_VAL})\s*(?:s|%|°)?(?![\w/])", re.I)
_KV_VAL = re.compile(r'"\s*((?:[+=]?-?(?:\d+\.?\d*|\.\d+)\s*)+)"')      # "=40 =60" facet values, ".5"
# rows a reader checked: the KV has no key for the old value (it was a tooltip number or derived)
UNCHECKABLE = {("7.39c", "kunkka_tidal_wave"), ("7.40", "clinkz_wind_walk")}
_HERO = re.compile(r'id="dyn-hero-([a-z0-9_]+)"')
_ABIL = re.compile(r'class="ability-icon-img"[^>]*data-slug="([a-z0-9_]+)"|data-slug="([a-z0-9_]+)"[^>]*class="ability-icon-img')
_TALENTS = re.compile(r'<h4 class="subgroup">')
_ROW = re.compile(r'<span class="row-text">(.*?)</span>(?=<span class="badge|</li>)', re.S)
_TIP = re.compile(r'<span class="info-tip".*', re.S)     # a note sits at the row's end: drop it all
_TAG = re.compile(r"<[^>]+>")


def _vkey(v):
    return tuple(float(x) for x in v)


def _norm(text_val):
    """'20/18/16/14' -> (20, 18, 16, 14); a list of equal numbers collapses to one."""
    vals = _vkey(re.split(r"\s*/\s*", text_val.strip()))
    return vals[:1] if len(set(vals)) == 1 else vals


def _versions():
    def key(v):
        return [int(x) if x.isdigit() else x for x in re.findall(r"\d+|[a-z]+", v)]
    return sorted((d for d in os.listdir(STATS) if (STATS / d / "heroes").is_dir()), key=key)


_file_cache = {}


def _hero_kv(version, hero):
    k = (version, hero)
    if k not in _file_cache:
        p = STATS / version / "heroes" / f"npc_dota_hero_{hero}.txt"
        _file_cache[k] = _decode_bytes(p.read_bytes()) if p.exists() else ""
    return _file_cache[k]


def _block(txt, slug):
    """The {...} body of ability `slug` in a hero KV file, or ''."""
    m = re.search(rf'^\s*"{re.escape(slug)}"\s*$', txt, re.M)
    if not m:
        return ""
    i = txt.find("{", m.end())
    depth = 0
    for j in range(i, len(txt)):
        depth += {"{": 1, "}": -1}.get(txt[j], 0)
        if depth == 0:
            return txt[i:j]
    return ""


def kv_values(version, hero, slug):
    """Every numeric value string of that ability's KV in that snapshot, normalised like _norm."""
    vals = set()
    for m in _KV_VAL.finditer(_block(_hero_kv(version, hero), slug)):
        nums = _vkey(t.lstrip("+=") for t in m.group(1).split())
        vals.add(nums[:1] if len(set(nums)) == 1 else nums)
    return vals


def _last_before(marks, pos):
    best = None
    for p, v in marks:
        if p > pos:
            break
        best = v
    return best


def audit_page(version, prev):
    page = PAGES / f"{version}.html"
    if not page.exists():
        return []
    doc = page.read_text(encoding="utf-8")
    # a row belongs to the last hero header and the last ability icon above it; a hero header or a
    # "Talents"-like subgroup in between resets the ability
    marks = sorted([(m.start(), ("hero", m.group(1))) for m in _HERO.finditer(doc)]
                   + [(m.start(), ("abil", m.group(1) or m.group(2))) for m in _ABIL.finditer(doc)]
                   + [(m.start(), ("sub", None)) for m in _TALENTS.finditer(doc)], key=lambda x: x[0])
    out = []
    hero = slug = None
    k = 0
    for m in _ROW.finditer(doc):
        while k < len(marks) and marks[k][0] < m.start():
            kind, val = marks[k][1]
            if kind == "hero":
                hero, slug = val, None
            elif kind == "abil":
                slug = val
            else:
                slug = None
            k += 1
        if not (hero and slug) or (version, slug) in UNCHECKABLE or "wrong-word" in m.group(1):
            continue                                     # wrong-word: already marked as Valve's mistake
        text = _html.unescape(_TAG.sub("", _TIP.sub("", m.group(1)))).strip()
        old_kv, new_kv = kv_values(prev, hero, slug), kv_values(version, hero, slug)
        if not old_kv or not new_kv:
            continue
        for ft in _FROM_TO.finditer(text):
            if re.match(r"\s*(?:[+*(]|per\b)", text[ft.end():]):
                continue                                 # "to 70 + 10 per level": a formula, not a value
            x, y = _norm(ft.group(1)), _norm(ft.group(2))
            if x == (100.0,) and ft.group(0).rstrip().endswith("%"):
                continue                                 # "from 100%": the implicit whole, no KV key
            if y in new_kv and not _known(x, old_kv):
                out.append((version, hero, slug, text))
    return out


def _known(x, kv):
    """x is in the KV — or is its head: Valve lists 7 Quas levels of an 8-value list, 4 of a 5-value one."""
    return x in kv or any(len(v) > len(x) > 1 and v[:len(x)] == x for v in kv)


def main(argv):
    vers = _versions()
    wanted = argv or [v for v in vers if (PAGES / f"{v}.html").exists()]
    found = []
    for v in wanted:
        if v not in vers or vers.index(v) == 0:
            continue
        found += audit_page(v, vers[vers.index(v) - 1])
    for v, hero, slug, text in found:
        print(f"{v}  {slug}: {text}")
    print(f"{len(found)} row(s) whose 'from' value is not in the previous snapshot")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
