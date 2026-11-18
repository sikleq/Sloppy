"""Passes that turn Valve's lists into tables and cards: a boss's drops, values per death / per use, OLD / NEW lists,
a unit's renamed ability (7.42)."""
import re

from .post_stats import _py_str


_DROP_PART_RE = re.compile(r'^(?:Now always|Starting (?:with|from) (?:the |his |its )?(?P<nth>\w+) death,? (?:now )?always)'
                           r' drops (?P<rest>.+)$', re.I)
_POP_NOTE_RE = re.compile(r'\s*<span class=\\?"pop-note\\?">\((.+?)\)</span>')


def _drop_part(part):
    """One "?" line of a drops row → (when, item, details) or None: "Now always drops Greater Horn of Battle — New
    consumable …" / "Starting with the 2nd death, always drops Aghanim's Shard with the same …"."""
    from patch.item_links import _roster
    pop = _POP_NOTE_RE.search(part)
    m = _DROP_PART_RE.match(_POP_NOTE_RE.sub("", part).strip())
    if not m:
        return None
    rest = m.group("rest")
    item = next((n for n in sorted(_roster(), key=len, reverse=True) if rest.startswith(n)), None)
    if not item:
        return None
    details = re.sub(r"^\s*(?:—|-|–|,)?\s*", "", rest[len(item):]).strip()
    details = (details[:1].upper() + details[1:]) if details else ""
    if pop:
        details = (details.rstrip(".") + ". " if details else "") + pop.group(1).strip()
    when = f"From the {m.group('nth')} death" if m.group("nth") else "Every death"
    return when, item, details


def _postprocess_drop_table(lines):
    """A row whose "?" lists what a boss drops and from which death ("Now drops several items, similarly to Roshan",
    7.42 Tormentor) → a table under the row: when | the item (a link to its page) | details (owner 2026-11-18: "список
    не раскрыт удобной таблицей"). A "?" with any other line stays."""
    out = []
    for ln in lines:
        m = re.match(r'^(\s*W\(li\("[^"]*\bdrops\b[^"]*", t\("\w+"\)), extra=inline_note\("((?:[^"\\]|\\.)*)"\)\)\)\s*$',
                     ln)
        parts = [_drop_part(p) for p in m.group(2).split("<br>")] if m else []
        if len(parts) < 2 or not all(parts):
            out.append(ln)
            continue
        rows = ", ".join(f'[{_py_str(w)}, item_link({_py_str(i)}), {_py_str(d)}]' for w, i, d in parts)
        out.append(f'{m.group(1)}, extra=mech_table(["When", "Drops", "Details"], [{rows}], wide_last=True)))')
    return out


_DASH_NOTE_RE = re.compile(r'^(?P<head>\s*W\(li\("(?:[^"\\]|\\.)*", (?:b\([^)]*\)|t\("\w+"\))), '
                           r'extra=inline_note\("(?P<note>(?:[^"\\]|\\.)*)"\)\)\)\s*$')
_CLOCK_LINE_RE = re.compile(r'^([A-Z][\w\' ]+?) - (\d{1,2}:\d{2})$')
_APPROX_RE = re.compile(r'^(?P<pre>.*?\bformula:\s*)(?P<expr>.+?)(?P<post>\s+where\b.*)?$', re.I)


def _postprocess_dash_table(lines):
    """A "?" that is Valve's table typed as text ("Level -- Old -- New -- Total Increase<br>2 -- 240 -- 250 -- 10<br>…",
    7.42 experience per level) → a real table under the row; Valve's sentence after it stays the table's last line,
    a formula in it in the site's formula look (owner 2026-11-19: "отдельной таблицей, под [?] слишком массивно и не
    читаемо; формулу тоже куда-то записать")."""
    out = []
    for ln in lines:
        m = _DASH_NOTE_RE.match(ln)
        parts = [p.strip() for p in m.group("note").split("<br>")] if m else []
        clock = [_CLOCK_LINE_RE.match(p) for p in parts]
        if len(parts) >= 3 and all(clock):
            # "Tier 1 - 0:00<br>Tier 2 - 15:00<br>…" (7.42 neutral item tiers): what | when, one table
            rows = ", ".join(f'[{_py_str(c.group(1))}, "<b>{c.group(2)}</b>"]' for c in clock)
            out.append(f'{m.group("head")}, extra=mech_table(["", "Available at"], [{rows}])))')
            continue
        cells = [[c.strip() for c in p.split(" -- ")] for p in parts if " -- " in p]
        if len(cells) < 4 or len({len(c) for c in cells}) != 1 or len(cells[0]) < 3:
            out.append(ln)
            continue
        prose = [p for p in parts if p and " -- " not in p]
        tail = []
        for p in prose:
            f = _APPROX_RE.match(p)
            if f:
                post = _py_str(f.group("post").strip()) if f.group("post") else '""'
                tail.append(f'{_py_str(f.group("pre"))} + mech_formula({_py_str(f.group("expr").strip())}) + " " + {post}')
            else:
                tail.append(_py_str(p))
        rows = ", ".join("[" + ", ".join(_py_str(c) for c in r) + "]" for r in cells[1:])
        head = "[" + ", ".join(_py_str(c) for c in cells[0]) + "]"
        rows = rows + "".join(", " + t for t in tail)
        out.append(f'{m.group("head")}, extra=mech_table({head}, [{rows}], labels=False)))')
    return out


_FROM_TO_LINE_RE = re.compile(r'^(?P<what>[A-Z][^<>]*?) (?:increased|decreased|rescaled|changed) from (?P<a>[^<>]+?) '
                              r'to (?P<b>[^<>]+?)$')


def _postprocess_from_to_list(lines):
    """A "?" that is only a list of "X decreased from A to B" lines (Valve's sub-rows, 7.42 "Building bounty
    decreased": ten tower and barracks values) → a before / after table under the row (owner 2026-11-19, the same
    complaint as the experience table: a list of numbers in a "?" does not read)."""
    out = []
    for ln in lines:
        m = _DASH_NOTE_RE.match(ln)
        parts = [p.strip() for p in m.group("note").split("<br>")] if m else []
        hits = [_FROM_TO_LINE_RE.match(p) for p in parts]
        if len(parts) < 3 or not all(hits):
            out.append(ln)
            continue
        rows = ", ".join(f'({_py_str(h.group("what"))}, {_py_str(h.group("a"))}, {_py_str(h.group("b"))})' for h in hits)
        out.append(f'{m.group("head")}, extra=mech_before_after("Change", [{rows}])))')
    return out


_PER_DEATH_ROW_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<pre>[^"]+?) (?P<verb>changed|decreased|increased|rescaled) from (?P<a>\d+(?:\.\d+)?)'
    r'(?P<pct>%?) to (?P<b>\d+(?:\.\d+)?)%? \+ (?P<c>\d+(?:\.\d+)?)%? per (?P<who>[A-Z]\w+)(?:\'s)? death'
    r'(?:, up to (?P<cap>\d+(?:\.\d+)?)%?)?",\s*(?:b\([^)]*\)|t\("\w+"\))(?:, extra=inline_note\((?P<note>"(?:[^"\\]|\\.)*")\))?'
    r'\)\)\s*$')
_PER_USE_ROW_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<pre>[^"]+?) (?P<verb>changed|decreased|increased|rescaled) from (?P<a>\d+) \+ (?P<b>\d+) '
    r'per subsequent use to (?P<c>\d+) \+ (?P<d>\d+) per subsequent use",\s*(?:b\([^)]*\)|t\("\w+"\))\)\)\s*$')


def _postprocess_per_death(lines):
    """A value that now grows with a boss's deaths, or with each use ("Gold reward per player changed from 175 to 125
    + 50 per Tormentor's death", "Wisdom Shrine experience decreased from 200 + 300 per subsequent use to 200 + 200 per
    subsequent use", 7.42) → li_formula with a table over the deaths (0, 1, 2 …) / the uses (#1, #2 …), as 7.41's
    Wisdom Shrine row (owner 2026-11-18: "нет formula table"). Columns are the boss's number in the match (#1 = the
    first one, no death before it): server.dll of 7.42 build 6978 counts the deaths of the match in one counter and
    pays the N-th kill 125 + 50 × (N − 1), no cap; Reflect reads the deaths so far, min(15 + 5 × deaths, 30), its
    per-minute growth added after that cap (dota2-ida-researcher, 2026-11-19, CONFIRMED_DLL)."""
    out = []
    for ln in lines:
        m = _PER_DEATH_ROW_RE.match(ln)
        if m:
            pct, cap = m.group("pct"), m.group("cap")
            new_fn = f'{m.group("b")} + {m.group("c")} * (N - 1)'
            if cap:
                new_fn = f'min({cap}, {new_fn})'
            new_txt = ln[m.start("b"):ln.index('",', m.start("b"))]
            note = f', inline_note_text={m.group("note")}' if m.group("note") else ""
            fmt = ', value_fmt="{:g}%"' if pct else ""
            out.append(f'{m.group("ind")}W(li_formula("{m.group("pre")} {m.group("verb")}", "{m.group("a")}{pct}", '
                       f'"{new_txt}", lambda N: {m.group("a")}, lambda N: {new_fn}, levels=[1, 2, 3, 4, 5, 6], '
                       f'level_fmt=lambda N: f"#{{N}}", jump_at=None, rework_badge=False{fmt}{note}))')
            continue
        m = _PER_USE_ROW_RE.match(ln)
        if m:
            a, b_, c, d = (m.group(k) for k in "abcd")
            out.append(f'{m.group("ind")}W(li_formula("{m.group("pre")} {m.group("verb")}", "{a} + {b_} per subsequent use", '
                       f'"{c} + {d} per subsequent use", lambda N: {a} + {b_} * (N - 1), lambda N: {c} + {d} * (N - 1), '
                       f'levels=[1, 2, 3, 4, 5, 6, 7], level_fmt=lambda N: f"#{{N}}", rework_badge=False, '
                       f'headline_level=2))')
            continue
        out.append(ln)
    return out


_OLD_NEW_NOTE_RE = re.compile(r'^(?P<head>\s*W\(li\("[^"]*", t\("\w+"\)), extra=inline_note\("OLD:<br>(?P<old>(?:[^"\\]|\\.)*?)'
                              r'<br>NEW:<br>(?P<new>(?:[^"\\]|\\.)*)"\)(?P<tail>(?:, also_dyn=\[[^\]]*\])?\)\))\s*$')
_KEYED_PART_RE = re.compile(r'^(?:&nbsp;|\s|–|-)*(?P<key>[^:<]{1,24}(?::\d{2}[^:<]{0,12})*): (?P<val>.+)$')


def _keyed_parts(raw):
    """"&nbsp;&nbsp;– 0:00-29:59: Every 5 minutes …<br>…" → [(key, value)] or None when a line has no "key: "."""
    out = []
    for part in raw.split("<br>"):
        m = _KEYED_PART_RE.match(part.strip())
        if not m:
            return None
        out.append((m.group("key").strip(), m.group("val").strip()))
    return out


def _postprocess_old_new_table(lines):
    """A row whose "?" is Valve's "OLD:" list and "NEW:" list over the same keys (7.42 "Reworked Siege creep spawn
    count after the 30:00 mark": three game-time spans each) → a before / after table under the row, a line per key
    (owner 2026-11-18: "тайминги OLD/NEW … нашими таблицами, как принято"). Lists with different keys stay a "?"."""
    out = []
    for ln in lines:
        m = _OLD_NEW_NOTE_RE.match(ln)
        old = _keyed_parts(m.group("old")) if m else None
        new = _keyed_parts(m.group("new")) if m else None
        if not old or not new or [k for k, _ in old] != [k for k, _ in new]:
            out.append(ln)
            continue
        title = "Game time" if all(re.match(r"\d+:\d{2}", k) for k, _ in old) else ""
        rows = ", ".join(f"({_py_str(k)}, {_py_str(a)}, {_py_str(b)})" for (k, a), (_, b) in zip(old, new))
        out.append(f'{m.group("head")}, extra=mech_before_after({_py_str(title)}, [{rows}]){m.group("tail")}')
    return out


_UNIT_ABILITY_RE = re.compile(r'^(?P<ind>\s*)W\(ability\("(?P<new>[^"]+)", icon_url="(?P<icon>[^"]*/(?P<slug>\w+)\.png)"\)\)\s*$')
_RENAMED_ROW_RE = re.compile(r'^\s*W\(li\("(?P<old>[A-Z][\w\' -]+?)(?: ability)? renamed (?:in)?to (?P<new>[A-Z][\w\' -]+?)"')


_REWORKED_ROW_RE = re.compile(r'^\s*W\(li\("Ability [Rr]eworked"')
_REPLACED_ROW_RE = re.compile(r'^\s*W\(li\("(?P<old>[A-Z][\w\' -]+?) ability replaced with (?P<new>[A-Z][\w\' -]+?)"')


def _replacement_slug(old_slug, new_name, version):
    """The unit ability called <new_name> in `version` that shares the longest prefix with <old_slug> (7.42 Mud Golem:
    mud_golem_hurl_boulder -> mud_golem_hurl_big_boulder), else None."""
    from patch.ability_kv import _unit_blocks
    from patch.aghs_text import tooltip
    hits = [k for k in _unit_blocks(version) if tooltip(f"DOTA_Tooltip_ability_{k}", version) == new_name]
    prefix = lambda k: next((n for n, (x, y) in enumerate(zip(k, old_slug)) if x != y), min(len(k), len(old_slug)))
    return max(hits, key=prefix) if hits else None


def _unit_card(rows, m, version):
    """(old name, old slug, new name, new slug, summary, tag) of the card a unit's ability block asks for, or None."""
    slug, name = m.group("slug"), m.group("new")
    for r in rows:
        ren = _RENAMED_ROW_RE.match(r)
        if ren and ren.group("new") == name:
            return ren.group("old"), slug, name, slug, "Ability reworked.", "rework"
        if _REWORKED_ROW_RE.match(r):
            return name, slug, name, slug, "Ability reworked.", "rework"
        rep = _REPLACED_ROW_RE.match(r)
        if rep and rep.group("old") == name:
            new_slug = _replacement_slug(slug, rep.group("new"), version)
            if new_slug and new_slug != slug:
                return name, slug, rep.group("new"), new_slug, "New ability.", "new"
    return None


def _postprocess_renamed_unit_ability(lines, version=None):
    """A unit's ability the patch reworks → the old → new card with both patches' game texts (the old side only from
    the files of the patch before), the rows above it, the word rows the card already says hidden (owner 2026-11-18:
    "переделанная способность: карточки old → new"). Three cases, all 7.42: renamed and reworked ("Fireball ability
    renamed into Searing Swoop", Ancient Black Dragon), reworked under its name ("Ability Reworked", Kobold Soldier's
    Steal Weapon), replaced by another ability ("Hurl Boulder ability replaced with Hurl Big Boulder", Mud Golem —
    owner 2026-11-19: "все ренеймы оформляем по одному типу"). Left alone when the files have no text for a side."""
    from patch.ability_kv import _unit_blocks
    from patch.aghs_text import ability_text
    from patch.meta import _prev_patch_version
    out, i = [], 0
    while i < len(lines):
        m = _UNIT_ABILITY_RE.match(lines[i])
        end = next((k for k in range(i + 2, len(lines)) if lines[k].strip() == "W(ul_close())"), None) \
            if m and i + 1 < len(lines) and lines[i + 1].strip() == "W(ul_open())" else None
        rows = lines[i + 2:end] if end else []
        card = _unit_card(rows, m, version) if rows and version else None
        prev = _prev_patch_version(version) if card else None
        if not card or not all(ln.lstrip().startswith(("W(li", "#")) for ln in rows) \
                or not (prev and ability_text(card[1], prev) and ability_text(card[3], version)):
            out.append(lines[i])
            i += 1
            continue
        old_name, old_slug, new_name, new_slug, summary, tag = card
        ind, icon = m.group("ind"), m.group("icon")
        texture = (_unit_blocks(version).get(new_slug) or {}).get("AbilityTextureName") or new_slug
        new_icon = icon if new_slug == old_slug else f"../icons/abilities/{texture}.png"

        def inner(row):
            if row.lstrip().startswith("#"):
                return f"{ind}        {row.strip()}"
            row = row.strip()[2:-1]                                           # W(li(…)) -> li(…)
            if re.search(r', t\("(?:NEW|MISC|REWORK)"\)', row) and "covered=" not in row \
                    and ("wrong-word" not in row):
                row = row[:-1] + ", covered=True)"
            return f"{ind}        {row},"
        if new_slug == old_slug:
            descs = [f'{ind}_{old_slug}_old, _{old_slug}_new = game_ability_pair("{old_slug}", "{version}")']
            old_desc, new_desc = f"_{old_slug}_old", f"_{old_slug}_new"
        else:
            descs = []
            old_desc = f'game_ability_desc("{old_slug}", "{prev}")'
            new_desc = f'game_ability_desc("{new_slug}", "{version}")'
        out += [*descs, f'{ind}W(ability_change(',
                f'{ind}    old=dict(name={_py_str(old_name)}, icon_url="{icon}", desc={old_desc}),',
                f'{ind}    new=dict(name={_py_str(new_name)}, icon_url="{new_icon}", desc={new_desc}),',
                f'{ind}    summary="{summary}",', f'{ind}    tag="{tag}",', f'{ind}    rows_first=lambda: [',
                *map(inner, rows), f'{ind}    ]))']
        i = end + 1
    return out


_GROUP_HEAD_RE = re.compile(r"^([A-Z][\w' ]+)$")
_GROUP_ITEM_RE = re.compile(r"^(?:&nbsp;)*(?:–|-)?\s*([A-Z][\w' ]+): (.+)$")


def _postprocess_grouped_lists(lines):
    """A "?" of groups, each "<Group>" then its "<Kind>: a; b; c" lines with the same kinds (7.42 home jungles:
    "Radiant Jungle" / "Dire Jungle", each with Small / Medium / Large camps) → one table, a row per group, a column
    per kind, the items one per line (owner 2026-11-19: no long lists in a "?"; the table was made by hand first)."""
    out = []
    for ln in lines:
        m = _DASH_NOTE_RE.match(ln)
        parts = [p.strip() for p in m.group("note").split("<br>")] if m else []
        groups, kinds = [], None
        for p in parts:
            item = _GROUP_ITEM_RE.match(p)
            if item and groups:
                groups[-1][1].append((item.group(1), item.group(2)))
            elif _GROUP_HEAD_RE.match(p):
                groups.append((p, []))
            else:
                groups = []
                break
        ok = len(groups) >= 2 and all(g[1] for g in groups)
        if ok:
            kinds = [k for k, _ in groups[0][1]]
            ok = all([k for k, _ in g[1]] == kinds for g in groups)
        if not ok:
            out.append(ln)
            continue
        head_word = groups[0][0].split()[-1]
        same_word = all(g[0].split()[-1] == head_word for g in groups)
        name = (lambda g: g[0].rsplit(" ", 1)[0]) if same_word else (lambda g: g[0])
        rows = ", ".join("[" + ", ".join([_py_str(name(g))] + [_py_str("<br>".join(x.strip() for x in v.split(";")))
                                                               for _, v in g[1]]) + "]" for g in groups)
        head = "[" + ", ".join(_py_str(x) for x in ([head_word if same_word else ""] + kinds)) + "]"
        out.append(f'{m.group("head")}, extra=mech_table({head}, [{rows}])))')
    return out


_STAR_NOTE_RE = re.compile(r'extra=inline_note\("(?P<body>\s*\*\s(?:[^"\\]|\\.)*)"\)')


def _postprocess_star_lists(lines):
    """Valve's "* A<br>* B<br>…" in a "?" is a list the row introduces (7.42 Pip Health: 25 units with pips; Spell
    Mechanics: 24 "Hero: Ability" lines) → inline_list without the stars, so a mechanic block opens it as a table of
    icons (hero_ability_rows) or of lines (text_list_rows) under the row instead of a 25-line "?" (owner 2026-11-19:
    "под [?] слишком массивно и не читаемо"). Lines after the list that are not starred stay its last lines."""
    def repl(m):
        parts = [re.sub(r'^\s*\*\s*', '', p).strip() for p in m.group("body").split("<br>")]
        return 'extra=inline_list("' + "<br>".join(p for p in parts if p) + '")'
    return [_STAR_NOTE_RE.sub(repl, ln) for ln in lines]


_UNIT_HEAD_RE = re.compile(r'^(?P<ind>\s*)W\(unit_header\("(?P<name>[^"]+)"(?P<rest>.*)\)\)\s*$')
_ANY_RENAME_RE = re.compile(r'^\s*W\(li\("(?P<old>[A-Z][\w\' -]+?)(?: \([^)"]*\))?(?: ability)? renamed (?:in)?to '
                            r'(?P<new>[A-Z][\w\' -]+?)"')


def _postprocess_renames(lines):
    """Every rename in one form, as abilities, items and facets have had it (owner 2026-11-19: "все ренеймы оформляем
    по одному типу"): the header says "Old → New" and the rename row goes. A unit ("Hill Troll (from Dark Troll camp)
    renamed to Dark Troll Trapper", 7.42) gets unit_header(old_title=); an item's ability that the item's card already
    shows under its new name ("Break renamed to Respite", Tranquil Boots — "Passive: Respite" on the card) keeps its
    row only for the weights (covered=True)."""
    out = list(lines)
    unit, card = None, ""
    for i, ln in enumerate(out):
        head = _UNIT_HEAD_RE.match(ln)
        if head:
            unit, card = (i, head), ""
            continue
        if _BLOCK_START_RE.match(ln):
            unit, card = None, ""
        if "item_abilities_change(" in ln or (card and ln.lstrip().startswith(('old=', 'new=', '"'))):
            card += ln
        ren = _ANY_RENAME_RE.match(ln)
        if not ren:
            continue
        if unit and unit[1].group("name") == ren.group("new") and "old_title=" not in out[unit[0]]:
            h = unit[1]
            out[unit[0]] = f'{h.group("ind")}W(unit_header("{h.group("name")}"{h.group("rest")}, old_title={_py_str(ren.group("old"))}))'
            out[i] = None
        elif card and re.search(r'(?:Active|Passive|Toggle|Use): ' + re.escape(ren.group("new")) + r'\b', card) \
                and "covered=" not in ln:
            out[i] = ln[:-2] + ", covered=True))"
    out = [x for x in out if x is not None]
    # a unit list left with nothing in it goes (Dark Troll Trapper had only its rename row)
    return [x for k, x in enumerate(out) if not (x.strip() == "W(ul_open())" and k + 1 < len(out)
                                                  and out[k + 1].strip() == "W(ul_close())")
            and not (x.strip() == "W(ul_close())" and k > 0 and out[k - 1].strip() == "W(ul_open())")]


_NEW_UNIT_HEAD_RE = re.compile(r'^(?P<ind>\s*)W\(unit_header\("(?P<name>[^"]+)", NEUTRAL_CDN \+ "(?P<npc>\w+)\.png", '
                               r'new="New Level[^"]*"\)\)\s*$')
_NEW_ABIL_ROW_RE = re.compile(r'^\s*W\(li\("(?P<abil>[A-Z][\w\' -]+?): (?:Active|Passive)\b[^"]*", t\("\w+"\)')
_STATS_ROW_RE = re.compile(r'^\s*W\(li\("New Level \d+ [\w ]+Creep", t\("\w+"\)')
_BLOCK_START_RE = re.compile(r'^\s*W\((?:unit_header|hero_header|item_header|section|plain_header)\(')


def _unit_abilities(npc, version):
    """{tooltip name: (slug, icon file)} of npc_dota_neutral_<npc>'s abilities in the files of `version`."""
    import os
    from patch import game_files
    from patch.ability_kv import _unit_blocks
    from patch.aghs_text import tooltip
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "stats", version, "npc_units.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = game_files.npc(version, "npc_units.txt") or ""
    m = re.search(r'^\t"npc_dota_neutral_' + re.escape(npc) + r'"\s*\n\t\{(.*?)^\t\}', text, re.S | re.M)
    out = {}
    for slug in (re.findall(r'"Ability\d+"\s+"(\w+)"', m.group(1)) if m else []):
        name = tooltip(f"DOTA_Tooltip_ability_{slug}", version)
        if name:
            block = _unit_blocks(version).get(slug) or {}
            out[name] = (slug, block.get("AbilityTextureName") or slug)
    return out


def _postprocess_new_creep_abilities(lines, version=None):
    """A new neutral creep's abilities → "New ability" cards with the game's text, as every new ability on the site
    (owner 2026-11-19, 7.42 "Odobenus Blight: Passive Ability и др. … сделано строкой с [?]"); Valve's row stays under
    the card, hidden for the weights (covered=True), and so does the row of the creep's numbers that the sheet above
    shows ("New Level 4 Ranged Creep" + its "?"). The icon is the one the game draws (AbilityTextureName: Snowball Shot
    lives on warpine_raider_seed_shot). A row whose ability the files do not name stays as it is."""
    from patch.aghs_text import ability_text
    out, abilities, ind = [], {}, ""
    for ln in lines:
        head = _NEW_UNIT_HEAD_RE.match(ln)
        if head:
            abilities = _unit_abilities(head.group("npc"), version) if version else {}
            ind = head.group("ind")
            out.append(ln)
            continue
        if _BLOCK_START_RE.match(ln):
            abilities = {}
        if abilities and _STATS_ROW_RE.match(ln) and "covered=" not in ln:
            out.append(ln[:-2] + ", covered=True))")
            continue
        row = _NEW_ABIL_ROW_RE.match(ln) if abilities else None
        hit = abilities.get(row.group("abil")) if row else None
        if not hit or not ability_text(hit[0], version):
            out.append(ln)
            continue
        slug, icon = hit
        out += [f'{ind}W(ul_close())',
                f'{ind}W(new_ability({_py_str(row.group("abil"))}, "{slug}", version="{version}", '
                f'icon_url="../icons/abilities/{icon}.png"))',
                f'{ind}W(ul_open())', ln[:-2] + ", covered=True))"]
    return out
