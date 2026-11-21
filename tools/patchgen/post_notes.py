"""Rows from data and the General section's blocks: ROW_NOTES, hidden rows (data/rules/hidden_rows.json), Valve's
card errors (valve_errors.json), returning items, the Roshan block, mechanic lists (split out of post_late.py,
Fable review 2026-11-21)."""
import re

from .post_facets import _LI_TEXT_RE
from .post_stats import _py_str

_ROSHAN_ROW_RE = re.compile(r"""^\s*W\(li\(["'](?:[^"']*?\bRoshan(?:'s)? (?:now|no longer|will|is|has|gains|drops|"""
                            r"""HP|health|armor|base|attack|damage|magic|respawn|bounty|gold|experience|"""
                            r"""ability)\b)""", re.I)
_SECTION_RE = re.compile(r'^\s*W\(section\("([^"]+)"')
ROSHAN_HEADER = 'W(unit_header("Roshan", "../icons/units/npc_dota_roshan.png", general=False, track=True))'


# a row's "?" with what Valve's words leave out, found from the map or the game files — kept here so a regenerated
# page keeps it (the hand-written note was lost on every rewrap, 2026-10-30)
ROW_NOTES = {
    "Teleport time to Roshan's outposts decreased from 6s to 4s":
        "The two corner outposts next to Roshan's pits (added in 7.33 by the Twin Gates, removed in 7.38). "
        "The jungle outposts got 4s in 7.35",
    # 7.42 Nimble (game files of build 6978, checked in the game code; not yet in a match): the penalty read a value
    # the item did not have, so it was 0 since the enchantment came in
    "Health Regen penalty is now reflected on the health regen bar value, but cannot put your health regeneration "
    "below zero":
        "Not in the patch notes: before 7.42 the penalty did not apply at all (found in the game files)",
}


_RETURNING_HEADER_RE = re.compile(r'^\s*W\(item_header\("[^"]+", new="(?:Returning|New)\b')


_PROVIDES_KIND_RE = re.compile(r'^Provides\s+(?P<stats>\+.+?)\.\s+(?P<kind>Use|Active|Passive|Toggle|Aura):\s+(?P<rest>.+)$')


def _provides_stats(text):
    """"+5 to All Attributes", "+20 Attack Speed and +4 Armor" → "+5 All Attributes", "+20 Attack Speed, +4 Armor"."""
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", text)
    return ", ".join(re.sub(r"^(\+[\d.%/]+)\s+to\s+", r"\1 ", p.strip()) for p in parts if p.strip())


def _postprocess_returning_rows(lines):
    """Under a returning or new item's header (7.37 Ironwood Tree "Returning Tier 1 Neutral Item") the rows are its
    description — NEW, as 7.38's returning artifacts (owner 2026-10-30: "смотри примеры в 7.38"), not MISC. A row
    "Provides +5 to All Attributes. Use: Plant Tree. …" is the item's stats and its ability, as a new item of 7.41:
    provides('+5 All Attributes') under the header and the row "Active: Plant Tree. …" — drawn as the ability's card
    (owner 2026-10-30: "всё ещё неправильно … пример — 7.38 Pyrrhic Cloak, Book of the Dead, Fallen Sky")."""
    out, inside, ul_at = [], False, None
    for ln in lines:
        if re.match(r'^\s*W\((?:item_header|hero_header|unit_header|section|plain_header)\(', ln):
            inside, ul_at = bool(_RETURNING_HEADER_RE.match(ln)), None
        elif inside and ln.strip() == "W(ul_open())":
            ul_at = len(out)
        elif inside and ln.lstrip().startswith("W(li(") and 't("MISC")' in ln:
            ln = ln.replace('t("MISC")', 't("NEW")', 1)
        t = _LI_TEXT_RE.match(ln) if inside else None
        m = _PROVIDES_KIND_RE.match(t.group(1)) if t else None
        if m and ul_at is not None:
            ind = ln[:len(ln) - len(ln.lstrip())]
            out.insert(ul_at, f"{ind}W(provides({_py_str(_provides_stats(m.group('stats')))}))")
            kind = "Active" if m.group("kind") == "Use" else m.group("kind")
            ln = ln.replace(t.group(1), f"{kind}: {m.group('rest')}", 1)
        out.append(ln)
    return out


def _postprocess_hidden_rows(lines, version):
    """Rows the notes leave out (data/rules/hidden_rows.json): each after the line holding its anchor; an ability's
    slug puts it at the end of that ability's rows. A row already there is not added twice (owner 2026-11-21)."""
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "rules", "hidden_rows.json")
    with open(path, encoding="utf-8") as f:
        rows = json.load(f).get(version or "", [])
    out = list(lines)
    for r in rows:
        if any(ln.strip() == r["row"] for ln in out):
            continue
        at = next((i for i, ln in enumerate(out) if r["anchor"] in ln), None)
        if at is None:
            raise ValueError(f"hidden_rows.json {version}: no line holds the anchor {r['anchor']!r}")
        ind = out[at][:len(out[at]) - len(out[at].lstrip())]
        if f'slug="{r["anchor"]}"' in out[at]:              # an ability: before its ul_close
            at = next(i for i in range(at, len(out)) if out[i].strip() == "W(ul_close())") - 1
        out.insert(at + 1, ind + r["row"])
    return out


def _postprocess_valve_card_errors(lines, version):
    """An item card whose "from" in Valve's notes is not what the files had (data/rules/valve_errors.json, owner
    2026-11-21; 7.42 Crimson Guard "+4 → +5 Armor", the files 6 → 5): the card shows the files' number, its badge
    counts from it, the tag turns by it (more is better for every card stat) and glows red with Valve's words."""
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "rules", "valve_errors.json")
    with open(path, encoding="utf-8") as f:
        errors = json.load(f).get(version or "", [])
    out = list(lines)
    for e in errors:
        start = next((i for i, ln in enumerate(out) if f'item_header("{e["item"]}"' in ln), None)
        if start is None:
            raise ValueError(f"valve_errors.json {version}: no item {e['item']!r} on the page")
        end = next((i for i in range(start + 1, len(out)) if re.match(r"\s*W\((?:item|hero|unit|plain)_header\(", out[i])),
                   len(out))
        vm = re.match(r"^([+-]?)([\d.]+)(%?) (.+)$", e["valve"])
        real = float(re.match(r"^[+-]?([\d.]+)", e["real"]).group(1))
        stat = re.escape(vm.group(4))
        old_rx = re.compile(r'\("(?:BUFF|NERF|REWORK|MISC|)",\s*"' + re.escape(e["valve"]) + r'"\)')
        new_rx = re.compile(r'\("",\s*"([+-]?)([\d.]+)(%?) ' + stat + r'",\s*b\(([\d.]+),\s*([\d.]+)\)\)')
        done = 0
        for i in range(start, end):
            ln, n0 = out[i], done
            ln, k = old_rx.subn(f'("", "{e["real"]}")', ln)
            done += k

            def fix(m):
                new = float(m.group(2))
                tag = "NERF" if new < real else "BUFF"
                now = f"{m.group(1)}{m.group(2)}{m.group(3)} {vm.group(4)}"
                tip = f"Patch notes state: {e['valve']} &rarr; {now}<br>Game files: {e['real']} &rarr; {now}"
                return f'("{tag}|{tip}", "{m.group(1)}{m.group(2)}{m.group(3)} {vm.group(4)}", b({real:g}, {m.group(2)}))'
            ln, k = new_rx.subn(fix, ln)
            done += k
            if done != n0:
                out[i] = ln
        if done == 0:
            continue                                   # already rewritten (the content keeps the files' number)
        if done != 2:
            raise ValueError(f"valve_errors.json {version} {e['item']}: the card's rows for {e['valve']} not found")
    return out


def _postprocess_row_notes(lines):
    out = []
    for ln in lines:
        t = _LI_TEXT_RE.match(ln)
        note = ROW_NOTES.get(t.group(1)) if t else None
        if note and "extra=" not in ln:
            ln = re.sub(r"\)\)\s*$", f", extra=inline_note({_py_str(note)})))", ln)
        out.append(ln)
    return out


def _link_items(row):
    """The items a row's text names → links to their Changes pages (owner 2026-10-30, Roshan's drops: "кликабельные
    ссылки, ведущие на свои изменения"): '"… drops " + item_link("Refresher Shard") + " and …"'. Longest name first
    (Block of Cheese before Cheese); a row not in plain double quotes stays."""
    from patch.item_links import _roster
    m = re.match(r'^(\s*W\(li\()"((?:[^"\\]|\\.)*)"(.*)$', row)
    if not m:
        return row
    text = m.group(2)
    names = sorted((n for n in _roster() if len(n) > 3 and n in text), key=len, reverse=True)
    if not names:
        return row
    rx = re.compile(r"(?<![\w'])(" + "|".join(re.escape(n) for n in names) + r")(?![\w])")
    linked = rx.sub(lambda mm: f'" + item_link("{mm.group(1)}") + "', text)
    return f'{m.group(1)}"{linked}"{m.group(3)}'.replace('"" + ', "").replace(' + ""', "")


def _drop_empty_lists(body):
    """A list left empty goes: its ul_open / ul_close pair."""
    body = [ln for k, ln in enumerate(body) if not (ln.strip() == "W(ul_open())" and k + 1 < len(body)
                                                     and body[k + 1].strip() == "W(ul_close())")
            and not (ln.strip() == "W(ul_close())" and k > 0 and body[k - 1].strip() == "W(ul_open())")]
    return body


def _postprocess_roshan_block(lines):
    """General Updates rows about Roshan himself → a Roshan block at the end of the section, as 7.38–7.41's pages
    (owner 2026-10-30, 7.37: "Starting from his second death, Roshan now always drops Roshan's Banner" — "надо в
    блок к Roshan определять")."""
    start = next((k for k, ln in enumerate(lines) if _SECTION_RE.match(ln) and "General" in ln), None)
    head = next((k for k, ln in enumerate(lines) if ROSHAN_HEADER in ln), None)
    if head is not None:
        # a Roshan block already there (Valve's "Roshan" Subtitle, 7.42): General rows about him join it — "Roshan
        # gold per player" stood in Gold and Experience (owner 2026-11-18) — and its rows' items link too (owner
        # 2026-10-30, 7.38 "Roshan no longer drops Aghanim's Blessing": "подчеркнуть с ссылкой")
        stop = next((k for k in range(head + 1, len(lines)) if "W(ul_close())" in lines[k]), len(lines))
        own = lines[head + 1:stop]
        moved = {k for k in range(start + 1 if start is not None else head, head) if _ROSHAN_ROW_RE.match(lines[k])}
        before = _drop_empty_lists([ln for k, ln in enumerate(lines[:head]) if k not in moved])
        return before + [lines[head]] + [_link_items(ln) for ln in own + [lines[k] for k in sorted(moved)]] \
            + lines[stop:]
    if start is None:
        return lines
    end = next((k for k in range(start + 1, len(lines)) if _SECTION_RE.match(lines[k])), len(lines))
    while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].lstrip().startswith("#")):
        end -= 1                                        # the next section's "# =====" comment stays with it
    body = lines[start + 1:end]
    rows = [ln for ln in body if _ROSHAN_ROW_RE.match(ln)]
    if not rows:
        return lines
    body = _drop_empty_lists(_merge_adjacent_lists([ln for ln in body if ln not in rows]))
    while body and not body[-1].strip():
        body.pop()
    ind = rows[0][:len(rows[0]) - len(rows[0].lstrip())]
    block = [f"{ind}{ROSHAN_HEADER}", f"{ind}W(ul_open())", *map(_link_items, rows), f"{ind}W(ul_close())", ""]
    return lines[:start + 1] + body + block + lines[end:]


_SUBGROUP_LINE_RE = re.compile(r'^(\s*)W\(subgroup\("([^"]+)"\)\)\s*$')
_NEW_TERM_RE = re.compile(r'\bClassification\b|\bare considered\b', re.I)


def _postprocess_mechanic_lists(lines):
    """A General subgroup whose rows introduce lists of abilities / items (7.37 Teleport Classification, Breakability
    Update, Ability blocking and reflection) → a mechanic block, plain_header(title, new=…): its lists open as tables
    of icons under the rows, as 7.38 Lifesteal (owner 2026-10-30: "сделать в виде таблиц, мы умеем; научить
    генератор"). A classification of things that had none is a "New mechanic", the rest "Reworked mechanic"."""
    start = next((k for k, ln in enumerate(lines) if _SECTION_RE.match(ln) and "General" in ln), None)
    if start is None:
        return lines
    end = next((k for k in range(start + 1, len(lines)) if _SECTION_RE.match(lines[k])), len(lines))
    out = list(lines)
    for k in range(start + 1, end):
        m = _SUBGROUP_LINE_RE.match(out[k] or "")
        if not m:
            continue
        stop = next((j for j in range(k + 1, end)
                     if out[j] and (_SUBGROUP_LINE_RE.match(out[j]) or ROSHAN_HEADER in out[j])), end)
        rows = [ln for ln in out[k + 1:stop] if ln and ln.lstrip().startswith("W(li(")]
        if not any("extra=inline_list(" in r for r in rows):
            continue
        kind = "New mechanic" if _NEW_TERM_RE.search(m.group(2)) or any(_NEW_TERM_RE.search(r) for r in rows) \
            else "Reworked mechanic"
        # no tags in the block (owner 2026-10-30: "везде убрать теги")
        out[k] = f'{m.group(1)}W(plain_header("{m.group(2)}", new="{kind}", one_box=True))'
        _fold_sentences_into_tables(out, k + 1, stop)
    return [ln for ln in out if ln is not None]


_INLINE_LIST_END_RE = re.compile(r'(extra=inline_list\("(?:[^"\\]|\\.)*)("\))')


def _fold_sentences_into_tables(out, lo, hi):
    """A mechanic block's MISC rows without a list of their own are sentences of its tables (owner 2026-10-30,
    7.37 Breakability: "The breakability rules … have been updated", '"Breakable: Yes" has been added …', "… have an
    alt+tooltip line …" — "гармонично в таблицу встроить предложениями"): a line under the table of the row they
    speak of — "partially" → the Partially row, "fully" → the Fully row, else the block's first list. The rows go."""
    lists = [j for j in range(lo, hi) if out[j] and "extra=inline_list(" in out[j]]
    if not lists:
        return
    for j in range(lo, hi):
        ln = out[j]
        if not (ln and ln.lstrip().startswith("W(li(") and 't("MISC")' in ln and "extra=" not in ln):
            continue
        t = _LI_TEXT_RE.match(ln)
        if not t:
            continue
        text = t.group(1)
        low = text.lower()
        pick = lambda word: next((x for x in lists if word in out[x].lower().split("extra=")[0]), None)
        # owner 2026-10-30: the general sentence ("rules … have been updated") goes with the Fully table, not the first
        target = (pick("partially") if "partially" in low and "fully" not in low else None) or \
                 pick("fully") or lists[0]
        # a sentence about the game's tooltips ('"Breakable: Yes" has been added …', "… an alt+tooltip line …") is a
        # "?" on the table's leading words; any other sentence goes before them ("The breakability rules … have been
        # updated. The following are now Fully Disabled by Break:", owner 2026-10-30)
        kind = "pop-tip" if "tooltip" in low or "has been added" in low else "pop-lead"
        out[target] = _INLINE_LIST_END_RE.sub(
            lambda mm: f'{mm.group(1)}<br><span class=\\"{kind}\\">{text}</span>{mm.group(2)}', out[target], count=1)
        out[j] = None



def _merge_adjacent_lists(lines):
    """A list closed and the next opened right away — the rows of one block split in two (7.37 Faceless Void: the
    facet's "Renamed from Temporal Impunity" and its "Time Walk: …" row, from two parts of Valve's notes): one list."""
    out = []
    for ln in lines:
        if ln.strip() == "W(ul_open())" and out and out[-1].strip() == "W(ul_close())":
            out.pop()
            continue
        out.append(ln)
    return out
