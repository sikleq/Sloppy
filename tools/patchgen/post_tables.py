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
    Wisdom Shrine row (owner 2026-11-18: "нет formula table"). The deaths are counted as Valve words them: the column
    is the number of deaths, not the number of the kill."""
    out = []
    for ln in lines:
        m = _PER_DEATH_ROW_RE.match(ln)
        if m:
            pct, cap = m.group("pct"), m.group("cap")
            new_fn = f'{m.group("b")} + {m.group("c")} * N'
            if cap:
                new_fn = f'min({cap}, {new_fn})'
            new_txt = ln[m.start("b"):ln.index('",', m.start("b"))]
            note = f', inline_note_text={m.group("note")}' if m.group("note") else ""
            fmt = ', value_fmt="{:g}%"' if pct else ""
            out.append(f'{m.group("ind")}W(li_formula("{m.group("pre")} {m.group("verb")}", "{m.group("a")}{pct}", '
                       f'"{new_txt}", lambda N: {m.group("a")}, lambda N: {new_fn}, levels=[0, 1, 2, 3, 4, 5], '
                       f'label="{m.group("who")} deaths", rework_badge=False{fmt}{note}))')
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


def _postprocess_renamed_unit_ability(lines, version=None):
    """A unit's ability that the patch reworks and renames ("Fireball ability renamed into Searing Swoop" among the
    rows of Searing Swoop, 7.42 Ancient Black Dragon) → the old → new card with both patches' game texts
    (game_ability_pair: the old side only from the files of the patch before), the rows above it; the rename row and
    the word rows the card already says stay hidden (owner 2026-11-18: "переделанная способность: карточки old →
    new"). Left alone when the files of either patch have no text for it."""
    from patch.aghs_text import ability_text
    from patch.meta import _prev_patch_version
    out, i = [], 0
    while i < len(lines):
        m = _UNIT_ABILITY_RE.match(lines[i])
        end = next((k for k in range(i + 2, len(lines)) if lines[k].strip() == "W(ul_close())"), None) \
            if m and i + 1 < len(lines) and lines[i + 1].strip() == "W(ul_open())" else None
        rows = lines[i + 2:end] if end else []
        ren = next((r for r in map(_RENAMED_ROW_RE.match, rows) if r and r.group("new") == m.group("new")), None)
        if not ren or not version or not all(ln.lstrip().startswith("W(li") for ln in rows):
            out.append(lines[i])
            i += 1
            continue
        slug, ind, icon = m.group("slug"), m.group("ind"), m.group("icon")
        prev = _prev_patch_version(version)
        if not (prev and ability_text(slug, prev) and ability_text(slug, version)):
            out.append(lines[i])
            i += 1
            continue

        def inner(row):
            row = row.strip()[2:-1]                                           # W(li(…)) -> li(…)
            if re.search(r', t\("(?:NEW|MISC)"\)', row) and "covered=" not in row:
                row = row[:-1] + ", covered=True)"
            return f"{ind}        {row},"
        out += [f'{ind}_{slug}_old, _{slug}_new = game_ability_pair("{slug}", "{version}")',
                f'{ind}W(ability_change(',
                f'{ind}    old=dict(name="{ren.group("old")}", icon_url="{icon}", desc=_{slug}_old),',
                f'{ind}    new=dict(name="{m.group("new")}", icon_url="{icon}", desc=_{slug}_new),',
                f'{ind}    summary="Ability reworked.",', f'{ind}    tag="rework",', f'{ind}    rows_first=lambda: [',
                *map(inner, rows), f'{ind}    ]))']
        i = end + 1
    return out
