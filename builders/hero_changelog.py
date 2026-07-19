"""Build hero_changelog.html — per-hero chronological change history.

Reads every normalized JSON in data/normalized/patches/, groups changes by
hero (entity_type == "hero"), and emits a single static HTML page with all
data embedded as a JSON blob. Client-side JS handles hero selection and
change-list rendering matching the patch-page visual style.

Auto-extends: adding a new .json to data/normalized/patches/ and rebuilding
picks it up automatically (no code changes needed).

Run AFTER build_patches.py (needs _dynamics.json for the hero roster + icons):
    python build_site.py patch hcl
"""
from __future__ import annotations

import html as _html
import json as _json
import os as _os
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent

import sys as _sys
_sys.path.insert(0, str(_HERE))
_sys.path.insert(0, str(_HERE / "builders"))

import builders.site_common as _site

_esc = lambda s: _html.escape(str(s), quote=True)

NORM_DIR = _HERE / "data" / "normalized" / "patches"


def _ver_key(version_str: str) -> tuple:
    """Sort key for Dota 2 patch versions (e.g. '7.41d' → (7, 41, 100))."""
    v = version_str
    suffix_ord = 0
    if v and v[-1].isalpha():
        suffix_ord = ord(v[-1])
        v = v[:-1]
    parts = v.split(".")
    nums = []
    for part in parts:
        try:
            nums.append(int(part))
        except ValueError:
            nums.append(0)
    return tuple(nums) + (suffix_ord,)


def _load_hero_roster() -> dict[str, dict]:
    """Build hero lookup: slug → {name, icon, key} from _dynamics.json.
    Falls back to normalized-JSON-only if dynamics isn't available."""
    roster = {}
    dyn_path = _HERE / "_dynamics.json"
    if dyn_path.exists():
        dyn = _json.loads(dyn_path.read_text(encoding="utf-8"))
        for rec in dyn.get("heroes", []):
            key = rec.get("key", "")
            if not key.startswith("hero|"):
                continue
            slug = key.split("|", 1)[-1]
            roster[slug] = {
                "name": rec["name"],
                "icon": rec.get("icon", slug),
                "key": key,
            }
    return roster


def _load_all_patches() -> list[dict]:
    """Load all normalized JSONs, return list of {patch, date, entities} sorted
    oldest-first."""
    patches = []
    if not NORM_DIR.exists():
        return patches
    for fn in sorted(NORM_DIR.iterdir()):
        if not fn.suffix == ".json":
            continue
        try:
            data = _json.loads(fn.read_text(encoding="utf-8"))
        except Exception:
            continue
        patches.append({
            "patch": data.get("patch", fn.stem),
            "entities": data.get("entities", []),
        })
    patches.sort(key=lambda p: _ver_key(p["patch"]))
    return patches


def _load_patch_dates() -> dict[str, str]:
    """patch version → release date from patch/meta.py."""
    dates = {}
    try:
        import patch.meta as meta
        for rec in meta.RELEASE_HISTORY:
            dates[rec["version"]] = rec.get("date", "")
    except Exception:
        pass
    return dates


def _build_hero_data(patches: list[dict], roster: dict[str, dict]) -> dict:
    """Build the per-hero data structure:
    {
      heroes: [{slug, name, icon, patches: [{patch, date, changes: [...]}]}],
      patches: [{patch, date}],   # all patches with at least one hero change
      total_heroes: N,
    }
    """
    dates = _load_patch_dates()
    hero_patches: dict[str, list[dict]] = {}  # slug → [{patch, changes}]
    all_patches_seen = set()

    for pdata in patches:
        ver = pdata["patch"]
        for entity in pdata["entities"]:
            if entity.get("entity_type") != "hero":
                continue
            slug = entity.get("id", "")
            if not slug:
                continue
            changes = entity.get("changes", [])
            if not changes:
                continue
            all_patches_seen.add(ver)
            if slug not in hero_patches:
                hero_patches[slug] = []
            hero_patches[slug].append({
                "patch": ver,
                "date": dates.get(ver, ""),
                "changes": changes,
            })

    # Build hero list, using roster for name/icon when available
    heroes = []
    all_slugs = sorted(
        set(hero_patches.keys()) | set(roster.keys()),
        key=lambda s: (roster.get(s, {}).get("name", s)).lower()
    )
    for slug in all_slugs:
        info = roster.get(slug, {})
        name = info.get("name", slug.replace("_", " ").replace("-", " ").title())
        icon = info.get("icon", slug)
        patches_for_hero = hero_patches.get(slug, [])
        patches_for_hero.sort(key=lambda p: _ver_key(p["patch"]))
        heroes.append({
            "slug": slug,
            "name": name,
            "icon": icon,
            "patches": patches_for_hero,
            "total_changes": sum(len(p["changes"]) for p in patches_for_hero),
        })

    # Sort heroes: those with changes first (by total_changes desc), then untouched
    heroes.sort(key=lambda h: (-h["total_changes"], h["name"].lower()))

    patch_list = sorted(
        [{"patch": p["patch"], "date": dates.get(p["patch"], "")} for p in patches],
        key=lambda x: _ver_key(x["patch"])
    )

    return {
        "heroes": heroes,
        "patches": patch_list,
        "total_heroes": len(heroes),
    }


def render_html() -> str:
    roster = _load_hero_roster()
    patches = _load_all_patches()
    hero_data = _build_hero_data(patches, roster)

    nav = _site.render_top_nav(
        "materials", _site.get_latest_version(),
        patch_context=False, subtabs_active="hero_changelog",
        subnav_in_header=False,
    )
    subnav = _site.render_materials_subnav("hero_changelog")
    asset_version = _site.compute_asset_version()

    data_json = _json.dumps(hero_data, ensure_ascii=False, separators=(",", ":"))
    heroes_with_changes = sum(1 for h in hero_data["heroes"] if h["total_changes"] > 0)
    total_changes = sum(h["total_changes"] for h in hero_data["heroes"])

    page = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<title>SIKLE | Hero Changelog</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={asset_version}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page hc-page">\n'
        '<div class="creeps-scroll">\n'
        f'{subnav}'
        # Hero list panel (left sidebar)
        '<div class="hc-layout">'
        '<div class="hc-sidebar">'
        '<div class="hc-search-wrap">'
        '<input type="text" id="hc-search" class="hc-search" '
        'autocomplete="off" spellcheck="false" '
        'placeholder="Search heroes — axe, am, crystal…">'
        '</div>'
        '<div class="hc-hero-list" id="hc-hero-list"></div>'
        '</div>'
        # Change log panel (main content)
        '<div class="hc-main" id="hc-main">'
        '<div class="hc-empty" id="hc-empty">'
        '<div class="hc-empty-icon">⚔</div>'
        '<div class="hc-empty-text">Select a hero to view their change history</div>'
        '<div class="hc-empty-sub">Click any hero on the left, or start typing to search</div>'
        '</div>'
        '<div class="hc-changes" id="hc-changes" hidden></div>'
        '</div>'
        '</div>'  # .hc-layout
        '</div>\n'  # .creeps-scroll
        '</div>\n'  # .container
        # Embed data as JSON
        f'<script id="hc-data" type="application/json">{data_json}</script>\n'
        f'<script defer src="src/scripts.js?v={asset_version}"></script>\n'
        f'<script defer src="src/hero_changelog.js?v={asset_version}"></script>\n'
        '</body>\n</html>\n'
    )
    return page


def main() -> int:
    html = render_html()
    dist = _HERE / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / "hero_changelog.html"
    out.write_text(html, encoding="utf-8")
    # Count stats
    data = _json.loads(
        (dist / "hero_changelog.html").read_text(encoding="utf-8")
    ) if False else None  # don't re-parse
    # Quick parse from the embedded JSON
    import re
    m = re.search(r'<script id="hc-data" type="application/json">(.*?)</script>', html)
    if m:
        blob = _json.loads(m.group(1))
        n_heroes = len(blob.get("heroes", []))
        n_patches = len(blob.get("patches", []))
        n_changes = sum(h.get("total_changes", 0) for h in blob.get("heroes", []))
        print(f"  -> dist/hero_changelog.html: {len(html):,} bytes "
              f"({n_heroes} heroes, {n_patches} patches, {n_changes} changes)")
    else:
        print(f"  -> dist/hero_changelog.html: {len(html):,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
