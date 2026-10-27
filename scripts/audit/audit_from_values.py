"""audit_from_values.py — find rows whose "from X" value is not what the game had before the patch.

Valve's notes sometimes quote a value that an earlier patch already changed (7.41 Kinetic Fence:
"Cooldown decreased from 20/18/16/14s" — 7.38 had made it 20/17/14/11s, owner 2026-10-22).

For every row "... from X to Y" on a built patch page, X should be a value of the previous snapshot:
  - a hero ability's row  -> that ability's block in the hero's KV (data/stats/<v>/heroes/npc_dota_hero_*.txt);
  - a hero's own row       -> the hero's base values (data/stats/<v>/heroes_raw.json + heroes.json);
  - an item's row          -> the item's block in items.txt (data/stats/<v>/items.txt, else the items history
                              kept with the weights model, which is not in git: those patches are skipped in CI).
A row is reported only when Y IS in this patch's values (so the row is about a number the KV holds as
written) and X is NOT in the previous one. Values the KV keeps in another unit (0.2 for 20%) never get here.

    python scripts/audit/audit_from_values.py [7.41 7.40 ...]
"""
import html as _html
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from builders.silent import _decode_bytes  # noqa: E402
from tools import game_files  # noqa: E402

STATS = ROOT / "data" / "stats"
PAGES = ROOT / "dist" / "patches"

_NUM = r"-?\d+(?:\.\d+)?"
_VAL = rf"{_NUM}(?:\s*/\s*{_NUM})*"
_FROM_TO = re.compile(rf"\bfrom\s+\+?({_VAL})\s*(?:s|%|°)?\s+to\s+\+?({_VAL})\s*(?:s|%|°)?(?![\w/])", re.I)
_KV_VAL = re.compile(r'"\s*((?:[+=]?-?(?:\d+\.?\d*|\.\d+)\s*)+)"')      # "=40 =60" facet values, ".5"
# rows a reader checked: the KV has no key for the old value (it was a tooltip number or derived)
UNCHECKABLE = {("7.39c", "kunkka_tidal_wave"), ("7.40", "clinkz_wind_walk"), ("7.38", "ethereal_blade"),
               ("7.39c", "crystal_maiden_freezing_field"), ("7.40", "antimage_counterspell"),
               ("7.40", "treant_natures_grasp"),
               ("7.40", "furion_force_of_nature")}    # Valve gave the average of treant_damage_min / _max
# npc_dota_hero_base values a hero's own record leaves out: 100 attack speed, 0 health / mana regen
HERO_DEFAULTS = {(100.0,), (0.0,)}
_ICON = re.compile(r'src="[^"]*/(?:heroes|items)/([a-z0-9_]+)\.(?:webp|png)"')
_MARKS = re.compile(r'id="dyn-(hero|item)-([a-z0-9_-]+)"'
                    r'|class="ability-icon-img"[^>]*data-slug="([a-z0-9_]+)"'
                    r'|<h4 class="subgroup">([^<]*)'
                    r'|<(?:div|section)[^>]*class="(?:[^"]*\s)?(?:entity|cat-panel)[\s"]')   # not "entity-icon"
_ROW = re.compile(r'<span class="row-text">(.*?)</span>(?=<span class="badge|</li>)', re.S)
_TIP = re.compile(r'<span class="info-tip".*', re.S)     # a note sits at the row's end: drop it all
_TAG = re.compile(r"<[^>]+>")


def _vkey(v):
    return tuple(float(x) for x in v)


def _collapse(nums):
    return nums[:1] if len(set(nums)) == 1 else nums


def _norm(text_val):
    """'20/18/16/14' -> (20, 18, 16, 14); a list of equal numbers collapses to one."""
    return _collapse(_vkey(re.split(r"\s*/\s*", text_val.strip())))


def _versions():
    def key(v):
        return [int(x) if x.isdigit() else x for x in re.findall(r"\d+|[a-z]+", v)]
    return sorted((d for d in os.listdir(STATS) if (STATS / d / "heroes").is_dir()), key=key)


_cache = {}


def _cached(key, make):
    if key not in _cache:
        _cache[key] = make()
    return _cache[key]


def _hero_kv(version, hero):
    def make():
        p = STATS / version / "heroes" / f"npc_dota_hero_{hero}.txt"
        return _decode_bytes(p.read_bytes()) if p.exists() else ""
    return _cached(("hero", version, hero), make)


def _items_kv(version):
    def make():
        p = STATS / version / "items.txt"
        if p.exists():
            return _decode_bytes(p.read_bytes())
        data = game_files.read_bytes(version, "scripts/npc/items.txt")
        return _decode_bytes(data) if data is not None else ""
    return _cached(("items", version), make)


def _block(txt, slug):
    """The {...} body of ability / item `slug` in a KV file, or ''."""
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


def _kv_set(text):
    """Values as written and without their sign (Breathe Fire keeps its damage reduction as "-30")."""
    out = set()
    for m in _KV_VAL.finditer(text):
        nums = _collapse(_vkey(t.lstrip("+=") for t in m.group(1).split()))
        out |= {nums, tuple(abs(n) for n in nums)}
    return out


def _base_values(version, hero):
    def make():
        vals = set()
        for name in ("heroes_raw.json", "heroes.json"):
            p = STATS / version / name
            if p.exists():
                rec = json.loads(p.read_text(encoding="utf-8")).get(f"npc_dota_hero_{hero}") or {}
                for v in rec.values():
                    if isinstance(v, (int, float)) or (isinstance(v, str) and re.fullmatch(r"\s*-?[\d.]+\s*", v)):
                        vals.add((float(v),))
        return vals
    return _cached(("base", version, hero), make)


def values(version, ctx):
    """The previous / current value set of a row's context ("ability", hero, slug) / ("hero", hero) / ("item", slug)."""
    kind = ctx[0]
    if kind == "ability":
        return _kv_set(_block(_hero_kv(version, ctx[1]), ctx[2]))
    if kind == "hero":
        return _base_values(version, ctx[1])
    kv = _items_kv(version)                              # "Recipe cost" lives in the recipe's own block
    return _kv_set(_block(kv, f"item_{ctx[1]}") + _block(kv, f"item_recipe_{ctx[1]}"))


def _contexts(doc):
    """[(pos, ctx or None)] — the context every row after pos belongs to."""
    out = []
    hero = None
    for m in _MARKS.finditer(doc):
        if m.group(1):
            # the page id is the display name (battle-fury); the header icon's file is the game's (bfury)
            icon = _ICON.search(doc, m.end(), m.end() + 600)
            name = icon.group(1) if icon else m.group(2).replace("-", "_")
            hero = name if m.group(1) == "hero" else None
            out.append((m.start(), (m.group(1), name)))
        elif m.group(3) and hero:
            out.append((m.start(), ("ability", hero, m.group(3))))
        elif m.group(4) is not None:
            title = m.group(4).strip().lower()
            # "Abilities" waits for the first icon; Talents / Facets / anything else: no context
            out.append((m.start(), ("hero", hero) if hero and title == "general" else None))
        elif m.group(0).startswith("<"):
            hero = None                                  # a new block: its own id (if any) follows in the tag
            out.append((m.start(), None))
    return out


def audit_page(version, prev):
    page = PAGES / f"{version}.html"
    if not page.exists():
        return []
    doc = page.read_text(encoding="utf-8")
    marks = _contexts(doc)
    out = []
    ctx, k = None, 0
    for m in _ROW.finditer(doc):
        while k < len(marks) and marks[k][0] < m.start():
            ctx = marks[k][1]
            k += 1
        if ctx is None or "wrong-word" in m.group(1):
            continue                                     # wrong-word: already marked as Valve's mistake
        name = ctx[-1]
        if (version, name) in UNCHECKABLE:
            continue
        text = _html.unescape(_TAG.sub("", _TIP.sub("", m.group(1)))).strip()
        found = list(_FROM_TO.finditer(text))
        if not found:
            continue
        old_kv, new_kv = values(prev, ctx), values(version, ctx)
        if not old_kv or not new_kv:
            continue
        for ft in found:
            if re.match(r"\s*(?:[+*(]|per\b)", text[ft.end():]):
                continue                                 # "to 70 + 10 per level": a formula, not a value
            x, y = _norm(ft.group(1)), _norm(ft.group(2))
            if x == (100.0,) and ft.group(0).rstrip().endswith("%"):
                continue                                 # "from 100%": the implicit whole, no KV key
            if ctx[0] == "hero" and (x in HERO_DEFAULTS or re.match(r"Damage gain", text, re.I)):
                continue                                 # a default the hero's KV leaves out / a derived number
            if y in new_kv and not _known(x, old_kv):
                out.append((version, ctx[0], name, text))
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
    for v, kind, name, text in found:
        print(f"{v}  {kind} {name}: {text}")
    print(f"{len(found)} row(s) whose 'from' value is not in the previous snapshot")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
