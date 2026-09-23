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
from urllib.parse import quote as _quote

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))
_sys.path.insert(0, str(_HERE / "builders"))

import builders.site_common as _site          # noqa: E402
from patch.meta import RELEASE_HISTORY        # noqa: E402

DIST = _HERE / "dist"
KINDS = {"hero": ("heroes", "Hero Changes", "hero_changes", "heroes"),
         "item": ("items", "Item Changes", "item_changes", "items"),
         # enchantments live with the items (file enchantment-<slug>.html, same index page)
         "enchant": ("items", "Item Changes", "item_changes", "items"),
         # neutral creeps / summoned units get their own pages + Unit Changes index
         "unit": ("units", "Unit Changes", "unit_changes", "units"),
         # a creep-hero (Spirit Bear) is hero-side — merges into the Hero Changes index
         "creep-hero": ("heroes", "Hero Changes", "hero_changes", "heroes"),
         # buildings / map objectives — a static reference catalogue, no change pages
         "structure": ("structures", "Structures", "structures", "structures")}


def _file_slug(e: dict) -> str:
    return ("enchantment-" if e["kind"] == "enchant" else "") + e["slug"]
_BLOCK_OPEN_RE = _re.compile(r'<div class="entity-block[^"]*"[^>]*>')
_HEADER_RE = _re.compile(r'<div class="entity (?:hero|item|unit)-entity"[^>]*\bid="dyn-(creep-hero|hero|item|enchant|unit)-([a-z0-9-]+)"[^>]*>')
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
      <div class="legend-tags ec-filters">
        <strong>Tags:</strong>
        <button class="badge buff-text filter-btn" data-filter="buff">BUFF</button>
        <button class="badge nerf-text filter-btn" data-filter="nerf">NERF</button>
        <button class="badge new filter-btn" data-filter="new">NEW</button>
        <button class="badge del filter-btn" data-filter="del">DEL</button>
        <button class="badge rework filter-btn" data-filter="rework">REWORK</button>
        <button class="badge misc filter-btn" data-filter="misc">MISC</button>
        <button class="badge qol filter-btn" data-filter="qol">QoL</button>
        {scopes}{abilities}
      </div>
    </div>
{info}  </div>
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
    <div class="ec-scope" data-scope="…"> so the page can filter by it.
    Returns (html, scopes, ability_titles, facet_titles). Facet titles are kept
    apart so a facet never becomes an ability chip (the FACETS scope filters them)."""
    ms = list(_SUBGROUP_RE.finditer(body))
    if not ms:
        return body, [], _titles(body), []
    tail = body.rfind("</div>")                       # the entity-block's own closing tag
    out, scopes, titles, facet_titles = [body[:ms[0].start()]], [], [], []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else tail
        key = _scope_key(m.group(1))
        scopes.append(key)
        seg = body[m.start():end]
        if key == "facets":
            facet_titles += _titles(seg)              # not ability chips
        else:
            titles += _titles(seg)
        out.append(f'<div class="ec-scope" data-scope="{key}">{seg}</div>')
    out.append(body[tail:])
    return "".join(out), scopes, titles, facet_titles


_AB_BLOCK_RE = _re.compile(r'<div class="ability-block([^"]*)">(?:(?!<div class="ability-block).)*?'
                           r'<h4 class="ability-title">(.*?)</h4>', _re.S)


def _titles(html: str) -> list[str]:
    """Ability names of the NON-innate ability blocks (innates have their own Show filter).
    A renamed block "Old→New" counts as "New"."""
    out = []
    for m in _AB_BLOCK_RE.finditer(html):
        cls, t = m.group(1), m.group(2)
        if "is-innate" in cls:
            continue
        t = _re.sub(r"<[^>]+>", "", t).strip().split("→")[-1].strip()
        slug = _re.search(r'data-slug="([a-z_0-9]+)"', m.group(0))
        if t:
            _TITLE_SLUG.setdefault(t, slug.group(1) if slug else "")
            out.append(t)
    return out


_TITLE_SLUG: dict[str, str] = {}      # ability display name -> engine slug seen on the pages


_KIT_CACHE: dict[str, list[str]] = {}
_KIT_EXTRA: dict[str, tuple] = {}      # npc -> (current innate names, slugs defined in the KV, all known slugs)


def _hero_kit(npc: str) -> list[str]:
    """Display names of the hero's CURRENT non-innate abilities in in-game order: basic abilities
    by slot, the ultimate(s), then abilities granted by Aghanim's Scepter / Shard. Every ability
    DEFINED in the hero's KV file counts as current even when it has no slot (granted ones often
    do not), so Aghanim abilities never land in the "old" group. Source: latest KV + abilities_slim."""
    if npc in _KIT_CACHE:
        return _KIT_CACHE[npc]
    from patch.meta import latest_stats_version
    from patch.weights import ultimates
    kv = _HERE / "data" / "stats" / latest_stats_version() / "heroes" / f"npc_dota_hero_{npc}.txt"
    slim = _json.loads((_HERE / "data" / "abilities_slim.json").read_text(encoding="utf-8"))
    basics, ults, aghs, seen = [], [], [], set()
    if kv.exists():
        txt = kv.read_text(encoding="utf-8", errors="replace")
        defs = {}                                   # slug -> its KV block text
        parts = _re.split(r'(?m)^\t\t\t"([a-z_0-9]+)"\s*$', txt)
        for i in range(1, len(parts) - 1, 2):
            defs[parts[i]] = parts[i + 1]
        slotted = [a for _, a in sorted(((int(n), a) for n, a in _re.findall(r'"Ability(\d+)"\s+"([a-z_0-9]+)"', txt)),
                                        key=lambda x: x[0])]
        for slug in slotted + [d for d in defs if d not in slotted]:
            info = slim.get(slug) or {}
            name = info.get("dname")
            if (not name or slug in seen or slug.startswith("special_bonus") or "hidden" in slug
                    or slug.endswith("_empty") or info.get("is_innate")):
                continue
            seen.add(slug)
            granted = bool(_re.search(r'"IsGrantedBy(?:Scepter|Shard)"\s+"1"', defs.get(slug, "")))
            (aghs if granted else ults if slug in ultimates() else basics).append(name)
    innates = [(slim.get(d) or {}).get("dname") for d in (slotted + list(defs)) if (slim.get(d) or {}).get("is_innate")]
    _KIT_CACHE[npc] = basics + ults + aghs
    _KIT_EXTRA[npc] = ([n for n in dict.fromkeys(innates) if n], set(defs) | set(slotted), set(slim))
    return _KIT_CACHE[npc]


_TALENT_BLOCK_RE = _re.compile(r'<div class="ability-block talents-block">')
_LI_RE = _re.compile(r'<li\b([^>]*)>(.*?)</li>', _re.S)
_TALENT_MARK_RE = _re.compile(r'Level\s+\d+\s+Talent', _re.I)


def _load_talent_aliases() -> dict:
    """slug -> {keyword: 'Ability Chip Name'} for talents that reference an
    ability by a summoned unit / effect name (Eidolon -> Demonic Summoning)."""
    p = Path(__file__).resolve().parent.parent / "data" / "talent_ability_aliases.json"
    try:
        with open(p, encoding="utf-8") as f:
            d = _json.load(f)
        return {k: v for k, v in d.items() if not k.startswith("_")}
    except Exception:
        return {}


_TALENT_ALIASES = _load_talent_aliases()


def _tag_talent_rows(body: str, names: list[str], hero_slug: str | None = None) -> str:
    """Mark every talent row that names one of the hero's abilities with
    data-ec-ab="Name|Name" so the ability chips can pull it in: clicking Decrepify then
    shows the talents that upgrade Decrepify next to the direct changes. Longest name wins
    when one ability name contains another (e.g. "Nether Ward" vs "Ward").

    Three ways a talent gets linked to an ability:
      1. the ability's display name appears in the text (plural tolerated: a
         "Plague Wards" talent answers the "Plague Ward" chip);
      2. an alias keyword appears — a summoned unit / effect whose name differs
         from the ability (Eidolon -> Demonic Summoning), from
         data/talent_ability_aliases.json, applied only when that ability is a
         real chip on this hero;
      3. the talent lives OUTSIDE the talents block (folded into a facet/ability
         block) — a second pass catches any "Level N Talent" row anywhere."""
    names_set = set(names)
    pats = sorted(names, key=len, reverse=True)
    # plural-tolerant word match: "Plague Ward" also matches "Plague Wards"
    rx = [(n, _re.compile(r"(?<![A-Za-z'])" + _re.escape(n) + r"(?:s|es)?(?![A-Za-z'])", _re.I))
          for n in pats]
    arx = []
    for kw, canon in (_TALENT_ALIASES.get(hero_slug or "", {}) or {}).items():
        if canon in names_set:
            arx.append((canon, _re.compile(r"(?<![A-Za-z'])" + _re.escape(kw) + r"(?:s|es)?(?![A-Za-z'])", _re.I)))
    if not rx and not arx:
        return body

    def tag_li(m, require_talent=False):
        attrs, inner = m.group(1), m.group(2)
        if "data-ec-ab=" in attrs:
            return m.group(0)
        text = _re.sub(r"<[^>]+>", " ", inner)
        if require_talent and not _TALENT_MARK_RE.search(text):
            return m.group(0)
        hits, covered = [], []
        for n, r in rx:
            for h in r.finditer(text):
                if not any(a <= h.start() and h.end() <= b for a, b in covered):
                    covered.append((h.start(), h.end()))
                    if n not in hits:
                        hits.append(n)
        for canon, r in arx:
            if canon not in hits and r.search(text):
                hits.append(canon)
        if not hits:
            return m.group(0)
        return f'<li{attrs} data-ec-ab="{_esc("|".join(hits))}">{inner}</li>'

    # pass 1: everything inside a talents block (original coverage)
    out, pos = [], 0
    for m in _TALENT_BLOCK_RE.finditer(body):
        if m.start() < pos:
            continue
        end = _balanced_div(body, m.start())
        out.append(body[pos:m.start()])
        out.append(_LI_RE.sub(tag_li, body[m.start():end]))
        pos = end
    out.append(body[pos:])
    body = "".join(out)
    # pass 2: talent rows folded into a facet/ability block (a "Level N Talent"
    # <li> that pass 1 never saw). Only rows that look like a talent are touched.
    body = _LI_RE.sub(lambda mm: tag_li(mm, require_talent=True), body)
    return body


def _entity_page(e: dict, asset: str, latest: str, dyn: dict) -> str:
    folder, label, key, _ = KINDS[e["kind"]]
    nav = _site.render_top_nav("materials", f"../patches/{latest}.html", patch_context=True, subtabs_active=key)
    rec = dyn.get("entities", {}).get(f'{e["kind"]}|{e["slug"]}', {})
    eid = f'dyn-{e["kind"]}-{e["slug"]}'
    icon_cls = "item-icon" if e["kind"] in ("item", "enchant") else "hero-icon"
    ent_cls = "hero" if e["kind"] == "hero" else ("item" if e["kind"] in ("item", "enchant") else "unit")
    n = len(e["patches"])
    info = ""
    sections, seen = [], []
    for p in e["patches"]:
        body, sc, tt, _ = _wrap_scopes(p["body"])
        p["_body"] = body
        p["_titles"] = tt
        seen += [s for s in sc if s not in seen]
    scopes_html = ""
    if len(seen) > 1:
        has_innate = any('class="ability-block is-innate' in p["_body"] or "is-innate" in p["_body"] for p in e["patches"])
        scopes_html = ('<span class="ec-vsep" aria-hidden="true"></span>' + "".join(
            f'<button type="button" class="badge ec-scope-btn" data-ec-scope="{s}">{_SCOPE_LABEL[s]}</button>'
            for s in _SCOPE_ORDER if s in seen)
            + ('<button type="button" class="badge ec-scope-btn" data-ec-scope="innate">Innate</button>' if has_innate else ""))
    # every ability that was ever changed (most often changed first) -> one-click filter
    ab_count: dict[str, int] = {}
    for p in e["patches"]:
        for t in set(p["_titles"]):
            ab_count[t] = ab_count.get(t, 0) + 1
    abilities_html = ""
    if ab_count:
        npc = _re.sub(r"^.*/|\.(?:png|webp)$", "", e["icon"]) if e["kind"] == "hero" else ""
        kit = _hero_kit(npc) if npc else []
        low = {k.lower(): i for i, k in enumerate(kit)}
        current = sorted((t for t in ab_count if t.lower() in low), key=lambda t: low[t.lower()])
        rest = [t for t in ab_count if t.lower() not in low]
        innate_now, defined, known = _KIT_EXTRA.get(npc, ([], set(), set()))
        inn = {n.lower() for n in innate_now}
        # OLD = a real engine ability (known slug) that the hero's current KV no longer defines.
        # Anything else stays current: a former ability that is the innate now (Inner Beast,
        # Necromastery), unit / synthetic sub-blocks (Brewlings, Drunken Brawler stances).
        old = sorted(t for t in rest if t.lower() not in inn
                     and _TITLE_SLUG.get(t) in known and _TITLE_SLUG.get(t) not in defined)
        current += sorted(t for t in rest if t not in old)
        if not kit:                                    # items: no kit, keep everything visible
            current, old = sorted(ab_count), []
        # talents that upgrade an ability answer to its chip; a current ability changed ONLY through
        # talents (Nether Blast for Pugna) gets a chip too, sorted into the kit order
        for p in e["patches"]:
            p["_body"] = _tag_talent_rows(p["_body"], list(dict.fromkeys(current + old + kit)), hero_slug=e["slug"])
        via_talent = {a for p in e["patches"] for m in _re.finditer(r'data-ec-ab="([^"]*)"', p["_body"])
                      for a in _html.unescape(m.group(1)).split("|")}
        extra = [k for k in kit if k in via_talent and k not in current and k not in old]
        if extra:
            current = sorted(dict.fromkeys(current + extra), key=lambda t: low.get(t.lower(), 10_000))

        # Facets get no chips: the FACETS scope button already filters them, and a
        # facet mostly changes an existing ability (which has its own chip).
        def chip(t, hidden=False):
            cls = "badge ec-ab-btn" + (" ec-ab-old" if hidden else "")
            return (f'<button type="button" class="{cls}" data-ec-ability="{_esc(t)}"'
                    f'{" hidden" if hidden else ""}>{_esc(t)}</button>')
        ability_chips = ("".join(chip(t) for t in current) + "".join(chip(t, True) for t in old)
                         + (f'<button type="button" class="badge ec-ab-more" data-ec-more>+{len(old)}</button>' if old else ""))
        abilities_html = '<span class="ec-vsep" aria-hidden="true"></span>' + ability_chips
    _from_kind = {"hero": "hero", "item": "item", "enchant": "item"}.get(e["kind"], "unit")
    from_tok = f'{_from_kind}:{_file_slug(e)}'
    out = [_head(e["name"], asset, "../", "patch-page entity-page"),
           f' data-dyn-prefix="../patches/" data-dyn-from="{from_tok}" data-ec-eid="{eid}">\n\n', nav,
           f'\n<a class="nav-back-arrow visible" href="../{key}.html" aria-label="All {label.lower()}" title="All {label.lower()}"></a>\n',
           _TOOLBAR.format(info=info, scopes=scopes_html, abilities=abilities_html), '<div class="container">\n',
           '<section class="cat-panel ec-head-panel"><div class="entity-block ec-head">'
           f'<div class="entity {ent_cls}-entity" id="{eid}">'
           f'<div class="entity-icon {icon_cls}"><img src="{_esc(e["icon"])}" alt="{_esc(e["name"])}"></div>'
           f'{_name_block(e)}</div></div></section>\n']
    for p in e["patches"]:
        bucket = rec.get("patches", {}).get(p["version"], {})
        score = ""
        if "w" in bucket or "v" in bucket:
            w = bucket.get("w", 0.0)
            cls = "pos" if w > 0 else ("neg" if w < 0 else "zero")
            score = (f'<span class="ec-score {cls}" title="weighted score: net (volume)">'
                     f'{"+" if w > 0 else ""}{w:.2f}<i> ({bucket.get("v", 0.0):.2f})</i></span>')
        body = _re.sub(r'href="(7\.\d+[a-z]?\.html)(?:\?[^"#]*)?', rf'href="../patches/\1?from={from_tok}', p["_body"])
        # the header label ("New Tier 1 Artifact", "Recipe changed") sits in the banner, styled as on the patch page
        note = _re.search(r'<div class="ec-entity-note">(.*?)</div>', body, _re.S)
        label = ""
        if note:
            body = body.replace(note.group(0), "", 1)
            label = f'<span class="ec-ver-label">{note.group(1)}</span>'
        # same panel + banner as a category section on the patch page; the banner IS the patch
        out.append(f'<section class="cat-panel ec-patch" id="p-{_esc(p["version"])}">'
                   f'<h2 class="section ec-ver"><a href="../patches/{_esc(p["version"])}.html?from={from_tok}#{eid}" '
                   f'title="Open {_esc(e["name"])} in patch {_esc(p["version"])}">Patch {_esc(p["version"])}</a>'
                   f'<span class="ec-date">{_esc(p["date"])}</span>{label}{score}</h2>\n{body}\n</section>\n')
    out.append('<button class="back-to-top" aria-label="Back to top" title="Back to top" '
               'onclick="window.scrollTo({top:0, behavior:\'smooth\'})"></button>'
               '<button class="dyn-w-fab" id="dyn-weights-btn" type="button" aria-label="Weighted scores" '
               'title="Dynamics: weighted scores (Valve revealed-preference weights)"></button>'
               f'<script defer src="../src/scripts.js?v={asset}"></script>\n</div></body></html>\n')
    return "".join(out)


# Hero pages: 6 small item slots between the name and the patch-dynamics row. The picked items' own change blocks are
# pulled from items/<slug>.html into the matching patch sections (scripts.js).
_ITEM_SLOTS = 6


def _name_block(e: dict) -> str:
    if e["kind"] != "hero":
        return f'<div class="entity-name">{_esc(e["name"])}</div>'
    # class, not CSS `:has(+ .ec-islots)`: a sibling :has on every .entity-name made each
    # lazily inserted dynamics row re-match styles all over the patch pages (perf)
    name = f'<div class="entity-name ec-name-slots">{_esc(e["name"])}</div>'
    slots = "".join(
        f'<button type="button" class="ec-islot is-empty" data-ec-islot="{i}" '
        f'aria-label="Choose item {i + 1}"></button>'
        for i in range(_ITEM_SLOTS))
    # a sibling of the name, so it sits on the same line as the patch-dynamics row
    return name + f'<div class="ec-islots" data-ec-hero="{_esc(_file_slug(e))}">{slots}</div>'


def _write_item_picker(items: list[dict], dyn: dict) -> None:
    """dist/items/picker.json — every item that has a Changes page, laid out exactly like
    item_changes.html (Basics | Upgrades | Neutral Items panels, titled categories) — the whole
    roster, an item without a Changes page flagged has_page=0 (shown greyed, not pickable):
    {"panels": [{"title", "one"?, "neutral"?, "groups": [{"title", "extra"?,
                 "items": [[slug, name, icon, current, has_page], …]}]}]}"""
    by = {g: lst for g, _, lst in _item_groups(items, dyn)}

    def group(title, lst, extra=None):
        row = [[_file_slug(e), e["name"], e["icon"].replace("../", "", 1), 1 if e["_current"] else 0,
                0 if e.get("_nopage") else 1] for e in lst]
        return {"title": title, "items": row, **({"extra": extra} if extra else {})} if row else None

    panels = [{"title": name, "groups": [x for c in cats if (x := group(c, by.get(c, [])))]}
              for name, cats in _SHOP_PANELS]
    neutral = [group(f"Tier {t}", by.get(f"Neutral · Tier {t}", []), _TIER_TIME[t]) for t in range(1, 6)]
    neutral += [group("Removed neutrals", by.get("Neutral · Other", [])),
                group("Neutral Enchantments", by.get("Enchantments", []))]
    panels.append({"title": "Neutral Items", "one": True, "neutral": True, "groups": [x for x in neutral if x]})
    (DIST / "items" / "picker.json").write_text(
        _json.dumps({"panels": panels}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


_ANN = None


def _annotated():
    global _ANN
    if _ANN is None:
        _ANN = [r["version"] for r in RELEASE_HISTORY if (DIST / "patches" / f'{r["version"]}.html').exists()]
    return _ANN


_ATTR = [("DOTA_ATTRIBUTE_STRENGTH", "Strength", "icons/strength.webp"),
         ("DOTA_ATTRIBUTE_AGILITY", "Agility", "icons/agility.webp"),
         ("DOTA_ATTRIBUTE_INTELLECT", "Intelligence", "icons/intelligence.webp"),
         ("DOTA_ATTRIBUTE_ALL", "Universal", "icons/universal.webp")]


def _hero_groups(ents):
    """Heroes as in the in-game grid: Strength / Agility / Intelligence / Universal by the primary
    attribute in the LATEST stats snapshot, alphabetical inside a group."""
    from patch.meta import latest_stats_version
    hs = _json.loads((_HERE / "data" / "stats" / latest_stats_version() / "heroes.json").read_text(encoding="utf-8"))
    groups = {k: [] for k, _, _ in _ATTR}
    for e in ents:
        npc = _re.sub(r"^.*/|\.(?:png|webp)$", "", e["icon"])
        attr = (hs.get(f"npc_dota_hero_{npc}") or {}).get("AttributePrimary", "DOTA_ATTRIBUTE_ALL")
        groups.setdefault(attr, groups["DOTA_ATTRIBUTE_ALL"]).append(e)
    return [(label, icon, sorted(groups[k], key=lambda x: x["name"].lower())) for k, label, icon in _ATTR if groups[k]]


def _shop_order() -> dict[str, list[str]]:
    """Item order of the Hero Lab picker (src/scripts.js SHOP_ORDER) — the in-game shop order."""
    js = (_HERE / "src" / "scripts.js").read_text(encoding="utf-8")
    m = _re.search(r"var SHOP_ORDER = \{(.*?)\n  \};", js, _re.S)
    out = {}
    if m:
        for key, arr in _re.findall(r"(?m)^\s*'?([A-Za-z ]+)'?:\s*\[(.*?)\],?\s*$", m.group(1)):
            out[key.strip()] = _re.findall(r"'([a-z0-9_]+)'", arr)
    return out


def _item_groups(ents, dyn):
    """Items as in the shop: category order of Item Dynamics, item order of the Hero Lab picker;
    then neutral tiers and enchantments. Same roster flags as Item Dynamics: `class`
    (regular / neutral / enchant) and `current` (removed / cycled-out items sit behind
    "Show deleted")."""
    meta = {}
    for i in (dyn or {}).get("items", []):
        kind, slug = i["key"].split("|", 1)
        meta[(kind, slug.replace("_", "-"))] = i
    order = list((dyn or {}).get("item_categories", []))
    shop = _shop_order()
    # the full roster (Item Dynamics manifest): items without a Changes page yet are shown greyed
    have = {(e["kind"], e["slug"]) for e in ents}
    ents = list(ents)
    for (kind, slug), m in meta.items():
        if (kind, slug) in have or ("item" if kind == "enchant" else kind, slug) in have:
            continue
        ents.append({"kind": kind, "slug": slug, "name": m["name"], "icon": f'../icons/items/{m["icon"]}.png',
                     "patches": [], "_nopage": True})
    buckets: dict[str, list] = {}
    for e in ents:
        m = meta.get((e["kind"], e["slug"])) or meta.get(("item", e["slug"])) or {}
        e["_current"] = bool(m.get("current", True))
        cls = "enchant" if e["kind"] == "enchant" else (m.get("class") or "regular")
        e["_class"] = cls
        if cls == "neutral":
            t = m.get("tier")                          # manifest tier is the KV index: 0..4 = Tier 1..5
            g = f"Neutral · Tier {int(t) + 1}" if t is not None and 0 <= int(t) <= 4 else "Neutral · Other"
        elif cls == "enchant":
            g = "Enchantments"
        else:
            g = m.get("category") or "Removed"
        e["_icon_slug"] = m.get("icon") or _re.sub(r"^.*/|\.(?:png|webp)$", "", e["icon"])
        buckets.setdefault(g, []).append(e)
    names = ([c for c in order if c in buckets]
             + sorted(g for g in buckets if g.startswith("Neutral"))
             + [g for g in ("Enchantments",) if g in buckets]
             + sorted(g for g in buckets if g not in order and not g.startswith("Neutral") and g != "Enchantments"))

    kv = _kv_rank()

    def key(g):
        rank = {s: i for i, s in enumerate(shop.get(g, []))}
        if g.startswith("Neutral") or g == "Enchantments":            # the game lists these in KV order
            rank = kv
        return lambda e: (0 if e["_current"] else 1, rank.get(e["_icon_slug"], 10_000), e["name"].lower())
    return [(g, None, sorted(buckets[g], key=key(g))) for g in names]


# In-game shop layout (screenshot of the shop, 7.41f): three panels, categories in this order,
# icons 4 per row; neutral tiers with their unlock times; enchantments last.
_SHOP_PANELS = [
    ("Basics",   ["Consumables", "Attributes", "Equipment", "Miscellaneous", "Secret Shop", "Other"]),
    ("Upgrades", ["Accessories", "Support", "Magical", "Armor", "Weapons", "Armaments"]),
]
_TIER_TIME = {1: "0:00+", 2: "15:00+", 3: "25:00+", 4: "35:00+", 5: "60:00+"}


def _kv_rank() -> dict[str, int]:
    """Position of every item in the latest items KV — the order the game uses for neutral
    tiers and enchantments (shops.txt only covers the regular shop)."""
    from patch.meta import latest_stats_version
    ks = list(_json.loads((_HERE / "data" / "stats" / latest_stats_version() / "items.json").read_text(encoding="utf-8")))
    return {k[5:]: i for i, k in enumerate(ks)}                    # strip "item_"


def _hero_card(e: dict) -> str:
    return (f'<a class="ec-card ec-card-hero" data-current="1" href="heroes/{_file_slug(e)}.html" '
            f'data-name="{_esc(e["name"].lower())} {_esc(e["slug"].replace("-", " "))}">'
            f'<img src="{_esc(e["icon"].replace("../", "", 1))}" alt="{_esc(e["name"])}" loading="lazy"></a>')


_UNIT_CAMP_CACHE = None
_UNIT_ORDER = ["Easy", "Medium", "Large", "Ancient", "Lane Creeps", "Summons"]

# Summoned / split units that have a portrait icon in icons/units/ but belong to
# no neutral camp, so the camp-roster loop never adds them. Listed here as
# (icon basename without .png, display name) and shown greyed in the Summons
# column — same reference treatment as unchanged camp creeps.
_SUMMON_UNITS = [
    ("npc_dota_warlock_golem", "Golem (Warlock)"),
    ("npc_dota_lycan_wolf", "Wolf (Lycan)"),
    ("npc_dota_furion_treant", "Treant (Nature's Prophet)"),
    ("npc_dota_broodmother_spiderling", "Spiderling (Broodmother)"),
    ("npc_dota_venomancer_plague_ward", "Plague Ward (Venomancer)"),
    ("npc_dota_shadow_shaman_ward", "Serpent Ward (Shadow Shaman)"),
    ("npc_dota_visage_familiar", "Familiar (Visage)"),
    ("npc_dota_eidolon", "Eidolon (Enigma)"),
    ("npc_dota_invoker_forged_spirit", "Forged Spirit (Invoker)"),
    ("npc_dota_beastmaster_boar", "Boar (Beastmaster)"),
    ("npc_dota_unit_undying_zombie", "Zombie (Undying)"),
    ("npc_dota_dark_troll_warlord_skeleton_warrior", "Skeleton Warrior"),
    ("brewmaster_fire_unit", "Brewmaster: Fire"),
    ("brewmaster_earth_unit", "Brewmaster: Earth"),
    ("brewmaster_storm_unit", "Brewmaster: Storm"),
    ("brewmaster_void_unit", "Brewmaster: Void"),
]

# A summon has no change page of its own — its balance changes are documented on
# its parent's change page (the hero's ability section, or the neutral that
# spawns it), under a specific ability. Map its icon to (parent page, ability
# chip name) so the card links there with ?from=unit_changes (back arrow) and
# &ability=<name> (pre-applies that ability filter, showing only its changes).
# ability=None → link without a filter (no matching chip / neutral page).
_SUMMON_PARENT = {
    "npc_dota_warlock_golem": ("heroes/warlock.html", "Chaotic Offering"),
    "npc_dota_lycan_wolf": ("heroes/lycan.html", "Summon Wolves"),
    "npc_dota_furion_treant": ("heroes/natures-prophet.html", "Nature's Call"),
    "npc_dota_broodmother_spiderling": ("heroes/broodmother.html", "Spawn Spiderlings"),
    "npc_dota_venomancer_plague_ward": ("heroes/venomancer.html", "Plague Ward"),
    "npc_dota_shadow_shaman_ward": ("heroes/shadow-shaman.html", "Mass Serpent Ward"),
    "npc_dota_visage_familiar": ("heroes/visage.html", "Summon Familiars"),
    "npc_dota_eidolon": ("heroes/enigma.html", "Demonic Summoning"),
    "npc_dota_invoker_forged_spirit": ("heroes/invoker.html", "Forge Spirit"),
    "npc_dota_beastmaster_boar": ("heroes/beastmaster.html", None),
    "npc_dota_unit_undying_zombie": ("heroes/undying.html", "Tombstone"),
    "npc_dota_dark_troll_warlord_skeleton_warrior": ("units/dark-troll-summoner.html", None),
    "brewmaster_fire_unit": ("heroes/brewmaster.html", "Fire Brewling"),
    "brewmaster_earth_unit": ("heroes/brewmaster.html", "Earth Brewling"),
    "brewmaster_storm_unit": ("heroes/brewmaster.html", "Storm Brewling"),
    "brewmaster_void_unit": ("heroes/brewmaster.html", "Void Brewling"),
}

# Lane creeps (Radiant portraits are the shared reference art for both teams).
_LANE_UNITS = [
    ("npc_dota_creep_goodguys_melee", "Melee Creep"),
    ("npc_dota_creep_goodguys_ranged", "Ranged Creep"),
    ("npc_dota_creep_goodguys_flagbearer", "Flagbearer Creep"),
    ("npc_dota_goodguys_siege", "Siege Creep"),
]

# Units removed from the game — shown only under the "Show deleted" toggle,
# as (icon basename, display name, column bucket).
_REMOVED_UNITS = [
    ("npc_dota_necronomicon_warrior", "Necronomicon Warrior", "Summons"),
    ("npc_dota_necronomicon_archer", "Necronomicon Archer", "Summons"),
]


def _unit_slug(basename: str) -> str:
    return basename.replace("npc_dota_neutral_", "").replace("npc_dota_", "").replace("_", "-")


# Small camp-difficulty badge shown beside a column title (icons/camps/creepcamp_*).
_CAMP_TITLE_ICON = {"Easy": "small", "Medium": "mid", "Large": "big", "Ancient": "ancient"}

# Structures page — a static catalogue of buildings / map objectives, grouped by
# type, as (icon basename in icons/structures/, display name).
_STRUCTURE_DEF = [
    ("Towers", [("tower_radiant", "Tower (Radiant)"), ("tower_dire", "Tower (Dire)")]),
    ("Barracks", [("barracks", "Barracks")]),
    ("Tormentors", [("tormentor_radiant", "Tormentor (Radiant)"),
                    ("tormentor_dire", "Tormentor (Dire)")]),
]


def _structure_groups():
    """Static building catalogue → [(label, [card dict, …])]. Full-colour,
    non-clickable reference cards (no per-structure change pages)."""
    out = []
    for label, items in _STRUCTURE_DEF:
        lst = [{"kind": "structure", "slug": b.replace("_", "-"), "name": n,
                "icon": f"../icons/structures/{b}.png", "patches": [],
                "_current": True, "_static": True} for b, n in items]
        out.append((label, lst))
    return out


# Creeps with no createhero token of their own (split/sub-spawns) — assigned to
# the camp of their parent creep by hand.
_CAMP_OVERRIDE = {
    "npc_dota_neutral_mud_golem_split": "Medium",   # Mud Golem's splinters
    "npc_dota_neutral_centaur_khan": "Large",        # Centaur Conqueror leads the Large camp
}
_CAMP_SIZE_DIFF = {"small": "Easy", "mid": "Medium", "big": "Large", "ancient": "Ancient"}
_CAMP_SIZE_RANK = {"small": 0, "mid": 1, "big": 2, "ancient": 3}


_CREEP_NAMES_CACHE = None


def _creep_display_names() -> dict:
    """{npc_dota_neutral_* : in-game display name} from CREEP_DISPLAY_NAMES in
    builders/creeps.py — the same names shown on Neutral Stats (e.g. Hellbear,
    Centaur Conqueror), instead of a title-cased engine name."""
    global _CREEP_NAMES_CACHE
    if _CREEP_NAMES_CACHE is None:
        src = (_HERE / "builders" / "creeps.py").read_text(encoding="utf-8")
        _CREEP_NAMES_CACHE = dict(_re.findall(
            r"'(npc_dota_neutral_[a-z0-9_]+)':\s*'([^']*)'", src))
    return _CREEP_NAMES_CACHE


def _unit_camp_map() -> dict:
    """npc_dota_neutral_* -> neutral-camp difficulty (Easy/Medium/Hard/Ancient).
    Authoritative source: the hand-maintained CREEP_CAMP table in
    builders/creeps.py (createhero shortname -> in-game camp size[s]), the same
    data that drives the camp badges on Neutral Stats. When a creep spawns in
    several camp sizes, the SMALLEST is used so it shows at the level it first
    appears (e.g. Centaur Outrunner / Satyr Trickster -> Medium).
    (The old ⬤-column of creeps_raw.csv mis-filed the secondary members of a
    camp, e.g. Prowler Acolyte in Easy — CREEP_CAMP fixes that.)"""
    global _UNIT_CAMP_CACHE
    if _UNIT_CAMP_CACHE is not None:
        return _UNIT_CAMP_CACHE
    src = (_HERE / "builders" / "creeps.py").read_text(encoding="utf-8")
    createhero = dict(_re.findall(r"'([a-z0-9_]+)':\s*'(npc_dota_neutral_[a-z0-9_]+)'", src))
    block = _re.search(r"CREEP_CAMP\s*=\s*\{(.*?)\n    \}", src, _re.S)
    out = {}
    if block:
        for short, sizes in _re.findall(r"'([a-z0-9_]+)':\s*\[([^\]]+)\]", block.group(1)):
            npc = createhero.get(short)
            szs = _re.findall(r"'([a-z]+)'", sizes)
            if npc and szs:
                out[npc] = _CAMP_SIZE_DIFF[min(szs, key=lambda s: _CAMP_SIZE_RANK.get(s, 99))]
    out.update(_CAMP_OVERRIDE)
    _UNIT_CAMP_CACHE = out
    return out


def _npc_of(icon: str) -> str:
    m = _re.search(r"(npc_dota_[a-z0-9_]+)\.png", icon or "")
    return m.group(1) if m else ""


def unit_page_slugs() -> dict:
    """{npc_dota_* : unit-page slug} for every neutral/unit that has a change
    page under dist/units/. The Neutral Stats builder uses this to turn creep
    names into links. Empty until the patch pages exist (patch step runs first,
    before this and the Neutral Stats build)."""
    out = {}
    for (kind, _slug), e in _collect().items():
        if kind == "unit":
            npc = _npc_of(e["icon"])
            if npc:
                out[npc] = _file_slug(e)
    return out


def _unit_groups(ents: list[dict]):
    """Group units by neutral-camp difficulty and append the rest of the neutral
    roster (creeps unchanged this cycle) as greyed, non-clickable cards."""
    camp = _unit_camp_map()
    have = set()
    for e in ents:
        e.setdefault("_current", True)
        e["_npc"] = _npc_of(e["icon"])
        have.add(e["_npc"])
    names = _creep_display_names()
    roster = list(ents)
    for npc, _diff in camp.items():
        if npc in have:
            continue
        name = names.get(npc) or _re.sub(r"^npc_dota_neutral_", "", npc).replace("_", " ").title()
        roster.append({"kind": "unit", "slug": npc.replace("npc_dota_neutral_", "").replace("_", "-"),
                       "name": name, "icon": f"../icons/units/{npc}.png", "patches": [],
                       "_nopage": True, "_current": True, "_npc": npc})
    # Summoned / split units — no camp, so add them explicitly to the Summons
    # column (skip any already present as a tracked change this cycle). Their
    # changes live on the parent's page, so link there when it exists.
    have_icons = {e["icon"].rsplit("/", 1)[-1] for e in ents}
    for basename, name in _SUMMON_UNITS:
        if f"{basename}.png" in have_icons:
            continue
        parent = _SUMMON_PARENT.get(basename)
        clickable = bool(parent and (DIST / parent[0]).exists())
        href = None
        if clickable:
            page, ability = parent
            href = f"{page}?from=unit_changes"
            if ability:
                href += "&ability=" + _quote(ability)
        roster.append({"kind": "unit", "slug": _unit_slug(basename),
                       "name": name, "icon": f"../icons/units/{basename}.png", "patches": [],
                       "_nopage": not clickable, "_href": href,
                       "_current": True, "_npc": _npc_of(f"{basename}.png"), "_bucket": "Summons"})
    # Lane creeps — greyed reference cards in their own column.
    for basename, name in _LANE_UNITS:
        if f"{basename}.png" in have_icons:
            continue
        roster.append({"kind": "unit", "slug": _unit_slug(basename),
                       "name": name, "icon": f"../icons/units/{basename}.png", "patches": [],
                       "_nopage": True, "_current": True, "_npc": _npc_of(f"{basename}.png"),
                       "_bucket": "Lane Creeps"})
    # Removed units (e.g. Necronomicon) — hidden until the "Show deleted" toggle.
    for basename, name, bucket in _REMOVED_UNITS:
        if f"{basename}.png" in have_icons:
            continue
        roster.append({"kind": "unit", "slug": _unit_slug(basename),
                       "name": name, "icon": f"../icons/units/{basename}.png", "patches": [],
                       "_nopage": True, "_current": False, "_npc": _npc_of(f"{basename}.png"),
                       "_bucket": bucket})
    buckets = {k: [] for k in _UNIT_ORDER}
    for e in roster:
        buckets[e.get("_bucket") or camp.get(e["_npc"], "Summons")].append(e)
    return [(k, buckets[k]) for k in _UNIT_ORDER if buckets[k]]


def _unit_card(e: dict) -> str:
    cur = e.get("_current", True)
    nop = e.get("_nopage")
    static = e.get("_static")                          # full-colour, non-clickable (catalogue)
    cls = ("ec-card ec-card-unit" + ("" if cur else " ec-old")
           + (" ec-nopage" if nop and not static else "") + (" ec-static" if static else ""))
    attrs = (f'class="{cls}" data-current="{1 if cur else 0}"{"" if cur else " hidden"} '
             f'data-name="{_esc(e["name"].lower())} {_esc(e["slug"].replace("-", " "))}"')
    img = f'<img src="{_esc(e["icon"].replace("../", "", 1))}" alt="{_esc(e["name"])}" title="{_esc(e["name"])}" loading="lazy">'
    if static or nop:                                  # no change page — shown, not clickable
        return f'<span {attrs}>{img}</span>'
    href = e.get("_href") or f"units/{_file_slug(e)}.html"
    return f'<a {attrs} href="{_esc(href)}">{img}</a>'


def _unit_grid(groups) -> str:
    """Category columns (camps / Lane Creeps / Summons, or Structures), icon-only
    cards row by row — mirrors the hero picker. Camp columns get a small
    difficulty badge beside the title."""
    cols = []
    for label, lst in groups:
        if not lst:
            continue
        cards = "".join(_unit_card(e) for e in sorted(lst, key=lambda e: (0 if e.get("_current", True) else 1, e["name"].lower())))
        camp = _CAMP_TITLE_ICON.get(label)
        badge = (f'<img class="ec-camp-ico" src="icons/camps/creepcamp_{camp}.png" alt="" aria-hidden="true">'
                 if camp else '')
        cols.append(f'<section class="ec-ucol"><h3 class="ec-group-title">{badge}{_esc(label)}</h3>'
                    f'<div class="ec-ucards">{cards}</div></section>')
    return f'<div class="ec-ugrid">{"".join(cols)}</div>'


def _item_card(e: dict) -> str:
    cls = "ec-card ec-card-item" + ("" if e["_current"] else " ec-old") + (" ec-nopage" if e.get("_nopage") else "")
    attrs = (f'class="{cls}" data-current="{1 if e["_current"] else 0}"{"" if e["_current"] else " hidden"} '
             f'data-name="{_esc(e["name"].lower())} {_esc(e["slug"].replace("-", " "))}"')
    img = f'<img src="{_esc(e["icon"].replace("../", "", 1))}" alt="{_esc(e["name"])}" loading="lazy">'
    if e.get("_nopage"):                               # no annotated change yet — shown, not clickable
        return f'<span {attrs}>{img}</span>'
    return f'<a {attrs} href="items/{_file_slug(e)}.html">{img}</a>'



_HERO_STAT_CACHE = None


def _hero_stat_data():
    """(slim heroes.json, raw heroes_raw.json) for the latest stats snapshot — base attributes,
    gains, movement speed (slim) and melee/ranged (raw AttackCapabilities, #base-inherited)."""
    global _HERO_STAT_CACHE
    if _HERO_STAT_CACHE is None:
        from patch.meta import latest_stats_version
        v = latest_stats_version()
        slim = _json.loads((_HERE / "data" / "stats" / v / "heroes.json").read_text(encoding="utf-8"))
        raw = _json.loads((_HERE / "data" / "stats" / v / "heroes_raw.json").read_text(encoding="utf-8"))
        _HERO_STAT_CACHE = (slim, raw)
    return _HERO_STAT_CACHE


# level-1 HP / mana constants (same as builders/heroes_stats.py: 120 + 22·Str, 75 + 12·Int)
_HP_BASE, _HP_PER_STR, _MP_BASE, _MP_PER_INT = 120.0, 22.0, 75.0, 12.0
# which base-attribute / gain field the category's "starting stat" refers to
_CAT_ATTR = {"Strength": "Strength", "Agility": "Agility", "Intelligence": "Intelligence"}


def _raw_cap(raw, npc):
    """AttackCapabilities with #base inheritance (matches heroes_stats._raw_field)."""
    d = raw.get(f"npc_dota_hero_{npc}", {})
    cap = d.get("AttackCapabilities")
    if cap is None:
        cap = raw.get("npc_dota_hero_base", {}).get("AttackCapabilities")
    return cap or ""


def _hero_group_stats(label, lst):
    """Summary shown under a category column: melee/ranged split, category-attribute extremes
    (highest/lowest base and gain + the hero), and averages (move speed, level-1 HP/mana, STR/AGI/INT)."""
    slim, raw = _hero_stat_data()
    rows = []
    for e in lst:
        npc = _re.sub(r"^.*/|\.(?:png|webp)$", "", e["icon"])
        d = slim.get(f"npc_dota_hero_{npc}")
        if not d:
            continue
        g = lambda k: float(d.get(k) or 0)
        rows.append({
            "name": e["name"], "melee": "MELEE" in _raw_cap(raw, npc),
            "str": g("AttributeBaseStrength"), "agi": g("AttributeBaseAgility"), "int": g("AttributeBaseIntelligence"),
            "strg": g("AttributeStrengthGain"), "agig": g("AttributeAgilityGain"), "intg": g("AttributeIntelligenceGain"),
            "ms": g("MovementSpeed"),
        })
    if not rows:
        return ""
    n = len(rows)
    melee = sum(1 for r in rows if r["melee"])
    avg = lambda f: sum(f(r) for r in rows) / n
    hp = lambda r: _HP_BASE + _HP_PER_STR * r["str"]
    mp = lambda r: _MP_BASE + _MP_PER_INT * r["int"]
    # category attribute: primary for STR/AGI/INT, the sum of all three for Universal
    if label in _CAT_ATTR:
        a = {"strength": "str", "agility": "agi", "intelligence": "int"}[label.lower()]
        base_of, gain_of, attr_label = (lambda r: r[a]), (lambda r: r[a + "g"]), label
    else:
        base_of = lambda r: r["str"] + r["agi"] + r["int"]
        gain_of = lambda r: r["strg"] + r["agig"] + r["intg"]
        attr_label = "Attributes"
    hi_base = max(rows, key=base_of); lo_base = min(rows, key=base_of)
    hi_gain = max(rows, key=gain_of); lo_gain = min(rows, key=gain_of)

    def num(x):
        return f"{x:.1f}".rstrip("0").rstrip(".")

    def row(lbl, val):
        return f'<div class="ec-hstat-row"><span>{lbl}</span><b>{val}</b></div>'

    def ext(who, val):
        return f'{num(val)} <span class="ec-hstat-who">{_esc(who["name"])}</span>'

    out = [
        row("Melee / Ranged", f'{melee} / {n - melee}'),
        row("Avg move speed", f'{round(avg(lambda r: r["ms"]))}'),
        row("Avg HP / mana (lvl 1)", f'{round(avg(hp))} / {round(avg(mp))}'),
        row("Avg STR / AGI / INT", f'{num(avg(lambda r: r["str"]))} / {num(avg(lambda r: r["agi"]))} / {num(avg(lambda r: r["int"]))}'),
        f'<div class="ec-hstat-head">{_esc(attr_label)}</div>',
        row("Highest base", ext(hi_base, base_of(hi_base))),
        row("Lowest base", ext(lo_base, base_of(lo_base))),
        row("Highest gain", ext(hi_gain, gain_of(hi_gain))),
        row("Lowest gain", ext(lo_gain, gain_of(lo_gain))),
    ]
    return f'<div class="ec-hstats">{"".join(out)}</div>'


def _hero_grid(groups) -> str:
    """Four attribute columns side by side, portraits alphabetical row by row — the hero picker."""
    cols = []
    for label, icon, lst in groups:
        cols.append(f'<section class="ec-hcol ec-hcol-{label.lower()}">'
                    f'<h3 class="ec-group-title"><img class="ec-group-icon" src="{icon}" alt="">{_esc(label)}</h3>'
                    f'<div class="ec-hcards">{"".join(_hero_card(e) for e in lst)}</div>'
                    f'{_hero_group_stats(label, lst)}</section>')
    return f'<div class="ec-hgrid">{"".join(cols)}</div>'


def _item_grid(groups) -> str:
    """Basics | Upgrades | Neutral Items panels, categories as 4-per-row icon blocks — the shop."""
    by = {g: lst for g, _, lst in groups}

    def block(title, lst, extra=""):
        if not lst:
            return ""
        return (f'<section class="ec-group ec-igroup"><h4 class="ec-igroup-title">{_esc(title)}{extra}</h4>'
                f'<div class="ec-icards">{"".join(_item_card(e) for e in lst)}</div></section>')

    panels = []
    for name, cats in _SHOP_PANELS:
        body = "".join(block(c, by.get(c, [])) for c in cats)
        panels.append(f'<section class="ec-ipanel"><h3 class="ec-group-title ec-ipanel-title">{_esc(name)}</h3>'
                      f'<div class="ec-ipanel-body">{body}</div></section>')
    tiers = "".join(block(f"Tier {t}", by.get(f"Neutral · Tier {t}", []),
                          f'<span class="ec-tier-time">{_TIER_TIME[t]}</span>') for t in range(1, 6))
    tiers += block("Removed neutrals", by.get("Neutral · Other", []))
    ench = block("Neutral Enchantments", by.get("Enchantments", []))
    panels.append('<section class="ec-ipanel ec-ipanel-neutral"><h3 class="ec-group-title ec-ipanel-title">Neutral Items</h3>'
                  f'<div class="ec-ipanel-body ec-ipanel-body-1">{tiers}{ench}</div></section>')
    return f'<div class="ec-igrid">{"".join(panels)}</div>'


def _index_page(kind: str, ents: list[dict], asset: str, latest: str, dyn: dict | None = None) -> str:
    folder, label, key, icon_dir = KINDS[kind]
    nav = _site.render_top_nav("materials", f"patches/{latest}.html", patch_context=False,
                               subtabs_active=key, subnav_in_header=False)
    subnav = _site.render_materials_subnav(key)
    for e in ents:
        e.setdefault("_current", True)
    if kind == "structure":
        groups = _structure_groups()
        grid = _unit_grid(groups)
        n_old = 0
        plural = "structures"
    elif kind == "unit":
        groups = _unit_groups(ents)
        grid = _unit_grid(groups)
        n_old = sum(1 for _, lst in groups for e in lst if not e["_current"])
        plural = "units"
    else:
        groups = _hero_groups(ents) if kind == "hero" else _item_groups(ents, dyn)
        n_old = sum(1 for _, _, lst in groups for e in lst if not e["_current"])
        grid = _hero_grid(groups) if kind == "hero" else _item_grid(groups)
        plural = "heroes" if kind == "hero" else "items"
    return (_head(label, asset, "", "") + '>\n' + nav +
            '\n<div class="container creeps-page ec-index">\n<div class="creeps-scroll">\n' + subnav +
            '<div class="ec-index-body">'
            '<div class="cal-toggle-bar inbox-bar hd-toolbar"><div class="toolbar-panel">'
            '<span class="search-box hd-search">'
            f'<input type="text" data-ec-search placeholder="Search {plural} — comma-separate for several" '
            'autocomplete="off" spellcheck="false"></span>'
            + (f'<label class="ua-upgrades-toggle"><span class="ua-upgrades-label">Show deleted ({n_old})</span>'
               '<input type="checkbox" id="ec-show-old" class="ua-switch-input">'
               '<span class="ua-switch" aria-hidden="true"></span></label>' if n_old else '')
            + '</div></div>' + grid + '</div>\n</div>\n</div>\n'
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
        if kind in ("enchant", "creep-hero"):
            continue                                   # merged into item / hero index
        lst = [e for (k, _), e in ents.items()
               if k == kind or (kind == "item" and k == "enchant") or (kind == "hero" and k == "creep-hero")]
        for e in lst:
            (DIST / folder / f'{_file_slug(e)}.html').write_text(_entity_page(e, asset, latest, dyn), encoding="utf-8")
        (DIST / f"{KINDS[kind][2]}.html").write_text(_index_page(kind, lst, asset, latest, dyn), encoding="utf-8")
        if kind == "item":
            _write_item_picker(lst, dyn)
        counts[kind] = (len(lst), sum(len(e["patches"]) for e in lst))
    print(f"  -> dist/heroes/*.html: {counts['hero'][0]} heroes ({counts['hero'][1]} patch sections); "
          f"dist/items/*.html: {counts['item'][0]} items ({counts['item'][1]} sections); "
          f"dist/units/*.html: {counts.get('unit', (0, 0))[0]} units; "
          f"hero_changes.html, item_changes.html, unit_changes.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
