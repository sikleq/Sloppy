"""Hero Changes / Item Changes — every change of one hero or item across all annotated patches.

Single source of truth: the ALREADY RENDERED patch pages (dist/patches/<ver>.html). Each entity
block is lifted verbatim (badges, formula tables, note boxes, icons, Aghanim markers, facets), so a
change looks exactly as it does on its patch page and nothing is re-derived.

Output:
  dist/heroes/<slug>.html, dist/items/<slug>.html   one page per entity, newest patch first
  dist/hero_changes.html, dist/item_changes.html    searchable index grids (Materials > Heroes / Items)
Patch pages link their entity headers here (patch/elements.py: _entity_link).

Run AFTER the patch step:  python build_site.py patch echg
"""
from __future__ import annotations

import html as _html
import json as _json
import re as _re
import sys as _sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))
_sys.path.insert(0, str(_HERE / "builders"))

import builders.site_common as _site          # noqa: E402
from patch.meta import RELEASE_HISTORY        # noqa: E402

DIST = _HERE / "dist"
KINDS = {"hero": ("heroes", "Hero Changes", "hero_changes", "heroes"),
         "item": ("items", "Item Changes", "item_changes", "items")}
_BLOCK_OPEN_RE = _re.compile(r'<div class="entity-block[^"]*"[^>]*>')
_HEADER_RE = _re.compile(r'<div class="entity (hero|item)-entity"[^>]*\bid="dyn-(?:hero|item)-([a-z0-9-]+)"[^>]*>')
_DIV_RE = _re.compile(r"<(/?)div\b[^>]*>")
_esc = lambda s: _html.escape(str(s), quote=True)


def _balanced_div(html: str, start: int) -> int:
    """Index just past the </div> matching the <div ...> that starts at `start`."""
    depth = 0
    for m in _DIV_RE.finditer(html, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return m.end()
    return len(html)


def _blocks(page: str):
    """Yield (kind, slug, name, icon_src, body_html) for every hero/item block of a patch page."""
    for m in _BLOCK_OPEN_RE.finditer(page):
        end = _balanced_div(page, m.start())
        block = page[m.start():end]
        h = _HEADER_RE.search(block)
        if not h:
            continue
        h_end = _balanced_div(block, h.start())
        header = block[h.start():h_end]
        name = _re.search(r'<div class="entity-name">(.*?)</div>', header, _re.S)
        icon = _re.search(r'<img[^>]*\bsrc="([^"]+)"', header)
        label = _re.search(r'<span class="entity-(?:new|changed)-type">.*?</span>', header, _re.S)
        body = block[:h.start()] + (f'<div class="ec-entity-note">{label.group(0)}</div>' if label else "") + block[h_end:]
        # the header may carry labels ("Returning Tier 4 Artifact", "NEW", "Recipe changed") —
        # the icon's alt text is the clean display name
        alt = _re.search(r'<img[^>]*\balt="([^"]+)"', header)
        clean_name = _html.unescape(alt.group(1)) if alt else (
            _re.sub(r"<[^>]+>", "", name.group(1)).strip() if name else h.group(2))
        yield h.group(1), h.group(2), clean_name, (icon.group(1) if icon else ""), body


def _collect():
    dates = {r["version"]: r["date"] for r in RELEASE_HISTORY}
    order = [r["version"] for r in RELEASE_HISTORY]           # newest first
    ents: dict[tuple, dict] = {}
    for ver in order:
        f = DIST / "patches" / f"{ver}.html"
        if not f.exists():
            continue
        page = f.read_text(encoding="utf-8")
        for kind, slug, name, icon, body in _blocks(page):
            e = ents.setdefault((kind, slug), {"kind": kind, "slug": slug, "name": name, "icon": icon, "patches": []})
            if e["patches"] and e["patches"][-1]["version"] == ver:      # same entity twice on one page
                e["patches"][-1]["body"] += body
            else:
                e["patches"].append({"version": ver, "date": dates.get(ver, ""), "body": body})
    return ents


def _head(title: str, asset: str, prefix: str, body_cls: str) -> str:
    return ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
            f'<title>SIKLE | {_esc(title)}</title>\n' + _site.favicon_links(prefix=prefix) +
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
            f'<link rel="stylesheet" href="{prefix}styles.css?v={asset}">\n</head>\n<body class="{body_cls}"')


_TOOLBAR = '''<div class="toolbar">
  <div class="toolbar-inner">
    <div class="legend-stack">
      <div class="legend-tags">
        <strong>Tags:</strong>
        <button class="badge buff-text filter-btn" data-filter="buff">BUFF</button>
        <button class="badge nerf-text filter-btn" data-filter="nerf">NERF</button>
        <button class="badge new filter-btn" data-filter="new">NEW</button>
        <button class="badge del filter-btn" data-filter="del">DEL</button>
        <button class="badge rework filter-btn" data-filter="rework">REWORK</button>
        <button class="badge misc filter-btn" data-filter="misc">MISC</button>
        <button class="badge qol filter-btn" data-filter="qol">QoL</button>
      </div>
      {scopes}
    </div>
    <div class="toolbar-patch-info">{info}</div>
  </div>
</div>
'''


_SUBGROUP_RE = _re.compile(r'<h4 class="subgroup">([^<]+)</h4>')
_SCOPE_ORDER = ["general", "abilities", "talents", "facets", "other"]
_SCOPE_LABEL = {"general": "General", "abilities": "Abilities", "talents": "Talents",
                "facets": "Facets", "other": "Other"}


def _scope_key(title: str) -> str:
    k = title.strip().lower()
    return k if k in ("general", "abilities", "talents", "facets") else "other"


def _wrap_scopes(body: str):
    """Wrap every subgroup of a hero block (GENERAL / Abilities / Talents / Facets / …) in
    <div class="ec-scope" data-scope="…"> so the page can filter by it. Returns (html, scopes)."""
    ms = list(_SUBGROUP_RE.finditer(body))
    if not ms:
        return body, []
    tail = body.rfind("</div>")                       # the entity-block's own closing tag
    out, scopes = [body[:ms[0].start()]], []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else tail
        key = _scope_key(m.group(1))
        scopes.append(key)
        out.append(f'<div class="ec-scope" data-scope="{key}">{body[m.start():end]}</div>')
    out.append(body[tail:])
    return "".join(out), scopes


def _entity_page(e: dict, asset: str, latest: str, dyn: dict) -> str:
    folder, label, key, _ = KINDS[e["kind"]]
    nav = _site.render_top_nav("materials", f"../patches/{latest}.html", patch_context=True, subtabs_active=key)
    rec = dyn.get("entities", {}).get(f'{e["kind"]}|{e["slug"]}', {})
    eid = f'dyn-{e["kind"]}-{e["slug"]}'
    icon_cls = "hero-icon" if e["kind"] == "hero" else "item-icon"
    n = len(e["patches"])
    info = (f'<span class="ti-released">Changed in <b>{n}</b> of {len(_annotated())} annotated patches</span>'
            f'<span class="ti-after">latest: <b>{_esc(e["patches"][0]["version"])}</b></span>')
    sections, seen = [], []
    for p in e["patches"]:
        body, sc = _wrap_scopes(p["body"])
        p["_body"] = body
        seen += [s for s in sc if s not in seen]
    scopes_html = ""
    if len(seen) > 1:
        scopes_html = ('<div class="legend-categories ec-scopes"><strong>Show:</strong>' + "".join(
            f'<button type="button" class="badge ec-scope-btn" data-ec-scope="{s}">{_SCOPE_LABEL[s]}</button>'
            for s in _SCOPE_ORDER if s in seen) + '</div>')
    out = [_head(f'{e["name"]} — changes', asset, "../", "patch-page entity-page"),
           ' data-dyn-prefix="../patches/">\n\n', nav,
           f'\n<a class="nav-back-arrow" href="../{key}.html" aria-label="All {label.lower()}" title="All {label.lower()}"></a>\n',
           _TOOLBAR.format(info=info, scopes=scopes_html), '<div class="container">\n',
           '<section class="cat-panel ec-head-panel"><div class="entity-block ec-head">'
           f'<div class="entity {e["kind"]}-entity" id="{eid}">'
           f'<div class="entity-icon {icon_cls}"><img src="{_esc(e["icon"])}" alt="{_esc(e["name"])}"></div>'
           f'<div class="entity-name">{_esc(e["name"])}</div></div></div></section>\n']
    for p in e["patches"]:
        bucket = rec.get("patches", {}).get(p["version"], {})
        score = ""
        if "w" in bucket or "v" in bucket:
            w = bucket.get("w", 0.0)
            cls = "pos" if w > 0 else ("neg" if w < 0 else "zero")
            score = (f'<span class="ec-score {cls}" title="weighted score: net / volume">'
                     f'{"+" if w > 0 else ""}{w:.2f}<i> / {bucket.get("v", 0.0):.2f}</i></span>')
        body = _re.sub(r'href="(7\.\d+[a-z]?\.html)', r'href="../patches/\1', p["_body"])
        # same panel + banner as a category section on the patch page; the banner IS the patch
        out.append(f'<section class="cat-panel ec-patch" id="p-{_esc(p["version"])}">'
                   f'<h2 class="section ec-ver"><a href="../patches/{_esc(p["version"])}.html#{eid}" '
                   f'title="Open {_esc(e["name"])} in patch {_esc(p["version"])}">Patch {_esc(p["version"])}</a>'
                   f'<span class="ec-date">{_esc(p["date"])}</span>{score}</h2>\n{body}\n</section>\n')
    out.append('<button class="back-to-top" aria-label="Back to top" title="Back to top" '
               'onclick="window.scrollTo({top:0, behavior:\'smooth\'})"></button>'
               '<button class="dyn-w-fab" id="dyn-weights-btn" type="button" aria-label="Weighted scores" '
               'title="Dynamics: weighted scores (Valve revealed-preference weights)"></button>'
               f'<script defer src="../src/scripts.js?v={asset}"></script>\n</div></body></html>\n')
    return "".join(out)


_ANN = None


def _annotated():
    global _ANN
    if _ANN is None:
        _ANN = [r["version"] for r in RELEASE_HISTORY if (DIST / "patches" / f'{r["version"]}.html').exists()]
    return _ANN


def _index_page(kind: str, ents: list[dict], asset: str, latest: str, dyn: dict | None = None) -> str:
    folder, label, key, icon_dir = KINDS[kind]
    nav = _site.render_top_nav("materials", f"patches/{latest}.html", patch_context=False,
                               subtabs_active=key, subnav_in_header=False)
    subnav = _site.render_materials_subnav(key)
    # items: only what is in the game NOW is shown by default (same "current" flag as Item
    # Dynamics — removed / cycled-out items sit behind the "Show deleted" switch)
    current = {}
    if kind == "item" and dyn:
        current = {i["key"].split("|", 1)[1].replace("_", "-"): bool(i.get("current", True)) for i in dyn.get("items", [])}
    cards, n_old = [], 0
    for e in sorted(ents, key=lambda x: x["name"].lower()):
        icon = e["icon"].replace("../", "", 1)
        vers = [p["version"] for p in e["patches"]]
        is_cur = current.get(e["slug"], True)
        n_old += 0 if is_cur else 1
        cards.append(f'<a class="ec-card ec-card-{kind}{"" if is_cur else " ec-old"}" data-current="{1 if is_cur else 0}"'
                     f'{"" if is_cur else " hidden"} href="{folder}/{e["slug"]}.html" '
                     f'data-name="{_esc(e["name"].lower())} {_esc(e["slug"].replace("-", " "))}">'
                     f'<img src="{_esc(icon)}" alt="" loading="lazy">'
                     f'<span class="ec-card-name">{_esc(e["name"])}</span>'
                     f'<span class="ec-card-meta">{len(vers)} patch{"es" if len(vers) != 1 else ""} · last {_esc(vers[0])}</span></a>')
    noun = "hero" if kind == "hero" else "item"
    plural = "heroes" if kind == "hero" else "items"
    return (_head(label, asset, "", "") + '>\n' + nav +
            '\n<div class="container creeps-page ec-index">\n<div class="creeps-scroll">\n' + subnav +
            f'<p class="ec-intro">Every {noun} that was touched in the annotated patches. Open one to read all of its '
            f'changes patch by patch, exactly as they appear on the patch pages. Clicking a {noun} header on any patch '
            f'page leads here too.</p>'
            '<div class="cal-toggle-bar inbox-bar hd-toolbar"><div class="toolbar-panel">'
            '<span class="search-box hd-search">'
            f'<input type="text" data-ec-search placeholder="Search {plural} — comma-separate for several" '
            'autocomplete="off" spellcheck="false"></span>'
            + (f'<label class="ua-upgrades-toggle"><span class="ua-upgrades-label">Show deleted ({n_old})</span>'
               '<input type="checkbox" id="ec-show-old" class="ua-switch-input">'
               '<span class="ua-switch" aria-hidden="true"></span></label>' if n_old else '')
            + '</div></div>'
            f'<div class="ec-grid ec-grid-{kind}">' + "".join(cards) + '</div>\n</div>\n</div>\n'
            f'<script defer src="src/scripts.js?v={asset}"></script>\n</body>\n</html>\n')


def main() -> int:
    ents = _collect()
    if not ents:
        print("  no patch pages found in dist/patches — run the patch step first")
        return 1
    asset = _site.compute_asset_version()
    latest = _annotated()[0]
    dyn_path = _HERE / "_dynamics.json"
    dyn = _json.loads(dyn_path.read_text(encoding="utf-8")) if dyn_path.exists() else {}
    counts = {}
    for kind, (folder, *_rest) in KINDS.items():
        (DIST / folder).mkdir(exist_ok=True)
        lst = [e for (k, _), e in ents.items() if k == kind]
        for e in lst:
            (DIST / folder / f'{e["slug"]}.html').write_text(_entity_page(e, asset, latest, dyn), encoding="utf-8")
        (DIST / f"{KINDS[kind][2]}.html").write_text(_index_page(kind, lst, asset, latest, dyn), encoding="utf-8")
        counts[kind] = (len(lst), sum(len(e["patches"]) for e in lst))
    print(f"  -> dist/heroes/*.html: {counts['hero'][0]} heroes ({counts['hero'][1]} patch sections); "
          f"dist/items/*.html: {counts['item'][0]} items ({counts['item'][1]} sections); "
          f"hero_changes.html, item_changes.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
