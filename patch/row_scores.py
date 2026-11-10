"""How a page's rows add up in the patch dynamics (each row scored by patch/weights.py): the tag tallies per entity and
patch (_dyn_record_li, _dyn_record_card), and the rows counted once per block when it ends — a hero's damage rows, its
replacements and REWORK rows (signal R), an item's components panel. Cut out of elements.py (2026-11-07)."""

import html as _html
import re
from .html_util import strip_tags

from .state import _State
from .weights import row_scores as _row_scores


_DYN_TAG_WHITELIST = {"buff", "nerf", "new", "del", "rework", "swap", "misc", "qol"}


def _dyn_record_li(tags, extra_keys=None, scores=(0.0, 0.0)):
    """Tally the row's tags per (entity, patch); `scores` = (net, volume) from
    patch/weights.row_scores, summed into the bucket under "w" and "v"."""
    if _State.dyn_skip_li:
        return
    pv = _State.current_patch_version
    if not pv:
        return
    all_keys = []
    if _State.current_entity_key:
        all_keys.append(_State.current_entity_key)
    if extra_keys:
        for ek in (extra_keys if isinstance(extra_keys, list) else [extra_keys]):
            if ek and ek not in all_keys:
                all_keys.append(ek)
    for ek in all_keys:
        rec = _State.dynamics.get(ek)
        if rec is None:
            parts = ek.split('|', 1)
            if len(parts) == 2:
                kind, slug = parts
                name = slug.replace('-', ' ').title()
                rec = _State.dynamics.setdefault(ek, {"name": name, "kind": kind, "patches": {}})
            else:
                continue
        patch_bucket = rec["patches"].setdefault(pv, {})
        for tag in tags:
            if tag in _DYN_TAG_WHITELIST:
                patch_bucket[tag] = patch_bucket.get(tag, 0) + 1
        net, vol = scores
        if not net and tags & {"rework", "swap"} and ek == _State.current_entity_key                 and ek.startswith(("item|", "hero|")):
            _note_rework(ek, pv)
        if net:
            patch_bucket["w"] = round(patch_bucket.get("w", 0.0) + net, 3)
        if vol:
            patch_bucket["v"] = round(patch_bucket.get("v", 0.0) + vol, 3)


_TALENT_LEVEL_RE = re.compile(r'^\s*Level (\d+)(?: Talent)?\s*:', re.I)


def _row_ctx(text):
    """Where the row lives — drives the weights context multiplier (patch/weights.py)."""
    ek = _State.current_entity_key or ""
    m = _TALENT_LEVEL_RE.match(strip_tags(text))
    return {
        "kind": ek.split("|", 1)[0] if ek else "",
        "item": (_State.dynamics.get(ek) or {}).get("icon") if ek.startswith("item|") else None,
        "version": _State.current_patch_version,
        "hero": _State.current_hero,
        "base_stat": bool(_State.in_stats_ul),
        "facet": bool(_State.current_block_is_facet),
        "ability": _State.current_ability_slug,
        "innate": bool(_State.current_ability_innate),
        "talent": int(m.group(1)) if m else None,
        "scepter": "Aghanim's Scepter" in text,
        "shard": "Aghanim's Shard" in text,
    }


def _dyn_record_card(tags, text="", badge="", **ctx_over):
    """Tally + score a change that is not an li() row (ability/facet cards, item property panes).
    Before 2026-09-25 these were tallied with scores (0, 0): a reworked ability or an item's
    "+6 -> +7 Armor" pane moved neither the net balance nor the volume."""
    ctx = dict(_row_ctx(text), **ctx_over)
    scores = _row_scores(text, tags, badge, ctx=ctx)
    _dyn_record_li(tags, scores=scores)
    _note_cell_row(text, tags, scores, ctx)


# ---- A hero block's replacements (owner 2026-09-27: "a replaced facet can be better or worse") ----
# By text alone a replacement has no direction, so it nets 0 and signal R (the pro pick-share shift the
# hero's other rows don't explain) gives it one where the match database has the patch (7.35c+):
#  - a whole ability / facet / innate removed AND one added in the same block (±WHOLE_W cancel);
#  - an Aghanim's Shard / Scepter upgrade that moved to another ability: the "no longer upgraded with"
#    DEL is cancelled by its NEW partner (or set to 0 next to a REWORK "... reworked" partner);
#  - a DEL row about an ability that the same block removes whole (Anti-Mage 7.40 "Aghanim's Shard no
#    longer provides Counterspell Ally ability" + "Ability removed") counts once.
_AGHS_LOST_RE = re.compile(r"no longer upgraded with aghanim's (shard|scepter)"
                           r"|aghanim's (shard|scepter)(?: upgrade)?\b[^.]*?\bno longer\b", re.I)


def _note_cell_row(text, tags, scores, ctx):
    ek, pv = _State.current_entity_key or "", _State.current_patch_version
    if not (ek.startswith("hero|") and pv and not _State.dyn_skip_li and tags & {"new", "del", "rework"}):
        return
    rows = _State.cell_rows
    if not rows or (rows["ek"], rows["pv"]) != (ek, pv):
        _flush_cell_rows()
        rows = _State.cell_rows = {"ek": ek, "pv": pv, "rows": [], "ctx": _row_ctx("")}
    from . import weights
    plain = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text or '')).strip()
    rows["rows"].append({"text": plain, "tags": set(tags), "net": scores[0], "ability": (ctx or {}).get("ability"),
                         "whole": weights.is_whole_new_del(plain, set(tags), ctx)})


def _ability_names(slug):
    """Words a row may use for an ability slug: its trailing words ("antimage_counterspell_ally" ->
    "counterspell ally"), at least two words or one of 6+ letters."""
    words = (slug or "").split("_")
    out = []
    for i in range(1, len(words)):
        tail = words[i:]
        if len(tail) >= 2 or len(tail[0]) >= 6:
            out.append(" ".join(tail))
    return out


def _flush_cell_rows():
    cell, _State.cell_rows = _State.cell_rows, None
    if not cell or not cell["rows"]:
        return
    rows, delta, replaced = cell["rows"], 0.0, False
    # 1. the same removal twice: a DEL row naming an ability this block removes whole
    gone = [n for r in rows if r["whole"] and "del" in r["tags"] for n in _ability_names(r["ability"])]
    for r in rows:
        if "del" in r["tags"] and not r["whole"] and r["net"]:
            low = r["text"].lower()
            if any(n in low for n in gone if not (r["ability"] or "").endswith(n.replace(" ", "_"))):
                delta -= r["net"]
                r["net"] = 0.0
    # 2. an Aghanim's upgrade that moved to another ability
    used = set()
    for r in rows:
        m = _AGHS_LOST_RE.search(r["text"]) if "del" in r["tags"] else None
        if not m or not r["net"]:
            continue
        item = (m.group(1) or m.group(2)).lower()
        for j, p in enumerate(rows):
            if j in used or p is r or not (p["tags"] & {"new", "rework"}) or p["ability"] == r["ability"]:
                continue
            if f"aghanim's {item}" in p["text"].lower():
                new_net = -p["net"] if "new" in p["tags"] and "rework" not in p["tags"] else 0.0
                delta += new_net - r["net"]
                r["net"] = new_net
                used.add(j)
                replaced = True
                break
    # 3. a whole ability / facet / innate removed and another added: a replacement
    if any(r["whole"] and "del" in r["tags"] for r in rows) and any(r["whole"] and "new" in r["tags"] for r in rows):
        replaced = True
    rec = _State.dynamics.get(cell["ek"])
    if rec is not None and delta:
        bucket = rec["patches"].setdefault(cell["pv"], {})
        bucket["w"] = round(bucket.get("w", 0.0) + delta, 3)
    if replaced:                                             # signal R gives the replacement a direction
        pend = _State.pending_rework
        if not (pend and (pend["ek"], pend["pv"]) == (cell["ek"], cell["pv"])):
            _flush_rework()
            _State.pending_rework = {"ek": cell["ek"], "pv": cell["pv"], "n": 1, "ctx": cell["ctx"]}


_COST_STATED_RE = re.compile(r'total cost|^\s*(?:recipe\s+)?cost\b', re.I)


def _note_cost_panel(total_old, total_new):
    """An item's components panel (components_change / auto_components_change) changes its total
    cost. It is scored once, as a "Total cost A -> B" row, when the item block ends — unless an
    li() row of the block states the cost itself ("Total cost A -> B", "Total cost unchanged",
    a basic item's "Cost A -> B"), which then wins (no double count). Not tallied as a tag."""
    _flush_cost_panel()
    ek = _State.current_entity_key or ""
    if not ek.startswith("item|") or _State.dyn_skip_li or not _State.current_patch_version:
        return
    try:
        old, new = float(total_old), float(total_new)
    except (TypeError, ValueError):
        return                                   # "2800/3950/..." (Dagon levels): no single total
    if old != new:
        _State.pending_cost_panel = {"ek": ek, "pv": _State.current_patch_version,
                                     "old": old, "new": new, "ctx": _row_ctx("")}


def _cost_panel_covered(score_text):
    pend = _State.pending_cost_panel
    if pend and pend["ek"] == _State.current_entity_key \
            and _COST_STATED_RE.search(re.sub(r'<[^>]+>', ' ', score_text or '')):
        _State.pending_cost_panel = None


_DMG_ROW_RE = re.compile(r'^\s*(?:(base damage)|(damage (?:at|on) level 1(?!\d))|(damage gain per level)'
                         r'|(damage at level 30))', re.I)


def _note_damage_row(text, scores):
    """Hero damage rows of one block, scored once (owner 2026-09-26, Dark Seer 7.38). "Damage at level 1"
    / "at level 30" are the damage the hero really has (base + attributes x multiplier); a "Base Damage
    increased by 26" next to them is one of their parts — 7.38 lowered the Universal multiplier 0.7 -> 0.45
    and raised base damage to make up for it, so alone it means nothing. "Damage gain per level" is
    (L30 - L1) / 29, i.e. the L30 row again. Such rows are taken back out at the end of the block."""
    ek, pv = _State.current_entity_key or "", _State.current_patch_version
    m = _DMG_ROW_RE.match(re.sub(r'<[^>]+>', ' ', text or ''))
    if not (m and ek.startswith("hero|") and pv and not _State.dyn_skip_li):
        return
    rows = _State.damage_rows
    if not rows or (rows["ek"], rows["pv"]) != (ek, pv):
        _flush_damage_rows()
        rows = _State.damage_rows = {"ek": ek, "pv": pv, "rows": []}
    kind = ("base", "l1", "gain", "l30")[[i for i in range(4) if m.group(i + 1)][0]]
    rows["rows"].append((kind, scores[0], scores[1]))


_FOLDED_L1_RE = re.compile(r"Damage at level 1 (?:increased|decreased|changed|rescaled)(?:\s+by\s+[\d.\-–]+\s*\()?"
                           r"\s*from\s+(\d+)[–\-](\d+)\s+to\s+(\d+)[–\-](\d+)", re.I)


def _score_folded_damage(extra):
    """A "Damage at level 1 …" line folded into its base attribute / base damage row's (?) (owner 2026-10-04,
    generate_patch_code_v2.fold_damage_l1_src) still weighs what it weighed as its own row: the same br() score,
    recorded with no tag (it is no row any more, so the tag tallies do not count it), and noted as the block's
    level-1 damage, so a "Base Damage" row next to it drops out as before (damage rows counted once, 2026-09-26)."""
    if not isinstance(extra, str) or "INLINETIP" not in extra:
        return
    from .badges import br as _br
    for tip in re.findall(r"<!--INLINETIP-->(.*?)<!--/INLINETIP-->", extra, re.S):
        plain = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", tip)))
        m = _FOLDED_L1_RE.search(plain)
        if not m:
            continue
        badge = _br(*(int(x) for x in m.groups()))
        text = m.group(0)
        tags = set(re.findall(r'data-tag="(\w+)"', badge)) or set(re.findall(r'data-overall="(\w+)"', badge))
        scores = _row_scores(text, tags, badge, ctx=_row_ctx(text))
        _dyn_record_li(set(), scores=scores)
        _note_damage_row(text, scores)


def _flush_damage_rows():
    rows, _State.damage_rows = _State.damage_rows, None
    if not rows:
        return
    kinds = {k for k, _, _ in rows["rows"]}
    drop = set()
    if kinds & {"l1", "l30"}:
        drop.add("base")
    if "l30" in kinds:
        drop.add("gain")
    rec = _State.dynamics.get(rows["ek"])
    if rec is None or not drop:
        return
    bucket = rec["patches"].setdefault(rows["pv"], {})
    for k, net, vol in rows["rows"]:
        if k in drop:
            bucket["w"] = round(bucket.get("w", 0.0) - net, 3)
            bucket["v"] = round(bucket.get("v", 0.0) - vol, 3)


def _note_rework(ek, pv):
    pend = _State.pending_rework
    if pend and (pend["ek"], pend["pv"]) == (ek, pv):
        pend["n"] += 1
        return
    _flush_rework()
    _State.pending_rework = {"ek": ek, "pv": pv, "n": 1, "ctx": _row_ctx("")}


def _flush_rework():
    """Signal R: an item's / hero's REWORK rows get the pro adoption shift its other rows do not explain.
    Runs after _flush_cost_panel, so the bucket's net already holds every other row of the item."""
    pend, _State.pending_rework = _State.pending_rework, None
    if not pend:
        return
    rec = _State.dynamics.get(pend["ek"])
    if rec is None:
        return
    from . import weights
    bucket = rec["patches"].setdefault(pend["pv"], {})
    net = weights.rework_adoption_net(pend["ctx"], bucket.get("w", 0.0))
    if net:
        bucket["w"] = round(bucket.get("w", 0.0) + net, 3)
        bucket["v"] = round(bucket.get("v", 0.0) + abs(net), 3)


def _flush_cost_panel():
    pend, _State.pending_cost_panel = _State.pending_cost_panel, None
    if not pend:
        return
    verb = "decreased" if pend["new"] < pend["old"] else "increased"
    text = f"Total cost {verb} from {pend['old']:g} to {pend['new']:g} (components panel)"
    tags = {"buff"} if pend["new"] < pend["old"] else {"nerf"}
    cur = _State.current_entity_key
    _State.current_entity_key = pend["ek"]       # the next header already moved on; score as the item
    try:
        net, vol = _row_scores(text, tags, "", ctx=pend["ctx"])
    finally:
        _State.current_entity_key = cur
    rec = _State.dynamics.get(pend["ek"])
    if rec is None or not (net or vol):
        return
    bucket = rec["patches"].setdefault(pend["pv"], {})
    if net:
        bucket["w"] = round(bucket.get("w", 0.0) + net, 3)
    if vol:
        bucket["v"] = round(bucket.get("v", 0.0) + vol, 3)


_TOTAL_UNCHANGED_RE = re.compile(r'total cost (?:is )?unchanged', re.I)


_PROP_VALUE_RE = re.compile(r'^\s*([+\-]?\d[\d./]*%?)\s+(.+?)\s*$')


def _prop_row_text(o, nw):
    """Item property pane pair ("+10 Strength" -> "+26 Strength") as a patch-note sentence the
    weights scorer understands: "Strength bonus changed from +10 to +26"."""
    ot = re.sub(r'<[^>]+>', ' ', (o or ('', ''))[1] or '')
    nt = re.sub(r'<[^>]+>', ' ', (nw or ('', ''))[1] or '')
    mo, mn = _PROP_VALUE_RE.match(ot), _PROP_VALUE_RE.match(nt)
    if mo and mn:
        return f"{mn.group(2)} bonus changed from {mo.group(1)} to {mn.group(1)}"
    return nt or ot
