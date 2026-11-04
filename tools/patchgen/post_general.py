"""Passes over the scaffold's lines in General Updates: bosses, per-minute values, mechanic rows, new units, team abilities."""
import ast
import json
import re

from .lines import _BOSSES, _ROW_RE, _drop_empty_ul, _li_parts, _row
from .post_cards import _MINUTE_GRID, _PER_MINUTES_FORMULA_RE
from .post_stats import _FORMULA_DIFF_LINE_RE

def _minute_lambda(m):
    base, inc, n = m.group('base'), m.group('inc'), m.group('n')
    return (f'lambda M: {base} + {inc} * (M // {n})' if n and n != '1'
            else f'lambda M: {base} + {inc} * M')


_PER_MINUTE_ROW = re.compile(r'^W\(li\("(?P<name>[^"]*?\b(?:upgrade|growth|gain)) per minute '
                             r'(?P<dir>increased|decreased) from (?P<a>\d+(?:\.\d+)?) to (?P<b>\d+(?:\.\d+)?)"')
_MINUTE_LEVELS = "[0, 5, 10, 15, 20, 25, 30, 40, 50, 60]"


_UNIT_HEAD_RE = re.compile(r'^W\(unit_header\("(?P<name>[^"]+)"')


def _postprocess_boss_rows_home(lines):
    """A row "Roshan's …" / "Tormentor's …" outside that boss's card (7.41: "Roshan's pit preference has switched" sat
    in the flat Map Objectives list) moves to the card — the one already on the page, or a new one right after the
    list it came from (owner 2026-10-16)."""
    out = list(lines)
    for boss, (icon, _prefix) in _BOSSES.items():
        head = f'W(unit_header("{boss}", "{icon}", general=False, track=True))'
        unit, stray = None, []
        for i, line in enumerate(out):
            m = _UNIT_HEAD_RE.match(line)
            if m:
                unit = m.group("name")
            elif re.match(r'^W\((?:hero_header|item_header|plain_header|section|subgroup)\(', line):
                unit = None
            elif unit != boss and line.startswith(f'W(li("{boss}\'s '):
                stray.append(i)
        if not stray:
            continue
        rows = [out[i] for i in stray]
        for i in reversed(stray):
            del out[i]
        out = _drop_empty_ul(out)
        card = next((i for i, l in enumerate(out) if l.startswith(f'W(unit_header("{boss}"')), None)
        if card is not None:
            close = next(i for i in range(card, len(out)) if out[i] == 'W(ul_close())')
            out[close:close] = rows
        else:
            at = next((i + 1 for i in range(min(stray[0], len(out) - 1), len(out)) if out[i] == 'W(ul_close())'),
                      len(out))
            out[at:at] = [head, 'W(ul_open())'] + rows + ['W(ul_close())']
    return out


def _postprocess_unit_possessive(lines):
    """Under a unit's card the unit's name off the front of its rows: "Tormentor's spawn preference has switched" ->
    "Spawn preference has switched" (owner 2026-10-16: the card already says whose it is)."""
    out, unit = [], None
    for line in lines:
        m = _UNIT_HEAD_RE.match(line)
        if m:
            unit = m.group("name")
        elif re.match(r'^W\((?:hero_header|item_header|plain_header|section)\(', line):
            unit = None
        elif unit:
            m2 = re.match(r'^(W\(li(?:_formula)?\(")' + re.escape(unit) + r"'s? ([a-z])", line)
            if m2:
                line = m2.group(1) + m2.group(2).upper() + line[m2.end():]
        out.append(line)
    return out


_SWITCHED_NOTE_RE = re.compile(r'^(W\(li\("[^"]*\bhas switched)(", t\("\w+"\)), extra=inline_note\("Now ([^".<]{3,60})\.?"\)\)\)$')


def _postprocess_switched_note(lines):
    """"Spawn preference has switched" + "?" "Now begins in the Bottom Chasm" -> one line "… has switched — now begins
    in the Bottom Chasm": the row says nothing without its note (owner 2026-10-16, 7.41 Tormentor / Roshan)."""
    out = []
    for line in lines:
        m = _SWITCHED_NOTE_RE.match(line)
        out.append(f"{m.group(1)} — now {m.group(3)}{m.group(2)}))" if m else line)
    return out


def _postprocess_per_minute(lines):
    """"<X> upgrade per minute increased from A to B" (a value that grows with game time, 7.41 Tormentor "Barrier
    upgrade per minute increased from 20 to 50") -> a minute table li_formula, as the barrier regen row (owner
    2026-10-16: "formula table")."""
    out = []
    for line in lines:
        m = _PER_MINUTE_ROW.match(line)
        if not m:
            out.append(line)
            continue
        a, b_ = m.group("a"), m.group("b")
        out.append(f'W(li_formula("{m.group("name")} {m.group("dir")}", "{a} per minute", "{b_} per minute", '
                   f'lambda M: {a} * M, lambda M: {b_} * M, levels={_MINUTE_LEVELS}, level_prefix=\'M\', '
                   f'rework_badge=False))')
    return out


def _postprocess_minute_formula(lines):
    """W(li("X from A + (B per N minutes) to C + (D per K minutes)", t(..)))
    -> W(li_formula(...)) with a minute table (5:00 … 60:00)."""
    out = []
    for line in lines:
        diff = _FORMULA_DIFF_LINE_RE.match(line)
        mo = mn = None
        if diff:
            mo = _PER_MINUTES_FORMULA_RE.match(diff.group('old').strip())
            mn = _PER_MINUTES_FORMULA_RE.match(diff.group('new').strip())
        if not (mo and mn):
            out.append(line)
            continue
        out.append(
            f'W(li_formula("{diff.group("prefix")}", "{diff.group("old")}", "{diff.group("new")}", '
            f'{_minute_lambda(mo)}, {_minute_lambda(mn)}, levels={_MINUTE_GRID}, '
            f'level_fmt=lambda M: f"{{M}}:00", headline_level=5, jump_at=None))'
        )
    return out


# A block (plain_header / subgroup) that introduces something brand new gets a
# label after its title: "New objective" for map objectives (buildings, shrines,
# runes, bosses), "New mechanic" otherwise. Its MISC rows become NEW.
_NEW_BLOCK_RE = re.compile(
    r'\breplaced with (?:a )?new\b|\bnew (?:buildings?|objectives?|structures?|mechanics?)\b'
    r'|\b(?:has|have) been added to the map\b', re.I)
_NEW_OBJECTIVE_RE = re.compile(
    r'\b(?:buildings?|objectives?|structures?|shrines?|runes?|outposts?|pools?|boss(?:es)?)\b', re.I)
_BLOCK_HEAD_RE = re.compile(r'^W\((?P<fn>plain_header|subgroup)\("(?P<title>[^"]+)"(?P<rest>.*)\)\)$')


_GONE_RE = re.compile(r'^W\(li\("(?P<old>[A-Z][\w ]+?) (?:have been |has been |were |was )?removed and replaced with (?:a )?new\b')


def _block_boundary(line):
    """Any heading call (section / plain_header / subgroup / unit / item / ability …) ends a block."""
    line = line.lstrip('\n')
    return line.startswith('W(') and not line.startswith(('W(li(', 'W(li_formula(', 'W(ul_open(', 'W(ul_close('))


def _postprocess_mechanic_rules_row(lines, after_label=False):
    """A reworked mechanic like 7.38 Lifesteal (owner 2026-10-27, 7.40 Invulnerability Targeting). Before the label
    pass: a row that only restates its header ("Invulnerability targeting rules of certain items and abilities have
    been updated" under "Invulnerability Targeting") goes — the header says it. After it: the rows of a "Reworked
    mechanic" block in ONE list (Valve's blank line between them had split it in two)."""
    out, title, mech, general = [], "", False, True
    for line in lines:
        if line.lstrip('\n').startswith('W(section('):
            # mechanics live in General Updates: the rules stay there (owner 2026-10-28)
            general = 'General' in line
        head = _BLOCK_HEAD_RE.match(line.lstrip('\n'))
        if head:
            title = head.group('title') if head.group('fn') == 'plain_header' else ""
            mech = 'new="Reworked mechanic"' in head.group('rest')
        elif _block_boundary(line):           # a section / hero / item heading ends the mechanic's block
            title, mech = "", False
        parts = _li_parts(line) if title and line.startswith('W(li(') else None
        if (not after_label and parts and re.match(rf'{re.escape(title)} rules\b.*\bhave been (?:updated|changed)\.?$',
                                                   parts[0], re.I)):
            continue
        if after_label and mech and line == 'W(ul_open())' and out and out[-1] == 'W(ul_close())':
            out.pop()
            continue
        if after_label and mech and general and out and _join_following_list(out, line):
            continue
        out.append(line)
    return out


_FOLLOWING_LIST_RE = re.compile(r"^The following (?:spells|abilities|items)\b", re.I)


def _join_following_list(out, line):
    """"The following spells have been changed" (+ its list) goes in one line with the row above it when that row has
    no note of its own (owner 2026-10-28, 7.40 Invulnerability Targeting). True when joined into out[-1]."""
    cur, prev = _li_parts(line), _li_parts(out[-1])
    if not (cur and prev and _FOLLOWING_LIST_RE.match(cur[0]) and "extra" not in prev[1]):
        return False
    src = out[-1].strip()
    badge = ast.get_source_segment(src, prev[2].args[1]) if len(prev[2].args) > 1 else '""'
    text = prev[0].rstrip().rstrip(".") + ". " + cur[0]
    keys = "".join(f", {k}={v}" for k, v in {**prev[1], **cur[1]}.items())
    out[-1] = f"W(li({json.dumps(text, ensure_ascii=False)}, {badge}{keys}))"
    return True


# a topic several rows of a mechanics section's "Miscellaneous" share: those rows are a mechanic of their own (owner
# 2026-10-28, 7.41 reflected damage: four rows, the last one's [?] the sources, drawn as a table of icons)
_MISC_TOPICS = [(re.compile(r"\breflect(?:ed|ion) damage\b", re.I), "Reflected Damage")]
_MISC_TOPIC_MIN = 3


def _postprocess_misc_topics(lines):
    out = list(lines)
    section = ''
    i = 0
    while i < len(out):
        head = _BLOCK_HEAD_RE.match(out[i].lstrip('\n'))
        if head and head.group('fn') == 'plain_header':
            section = head.group('title')
        if not (head and head.group('fn') == 'subgroup' and head.group('title') == 'Miscellaneous'
                and 'mechanic' in section.lower()):
            i += 1
            continue
        j = i + 1
        while j < len(out) and not _block_boundary(out[j]):
            j += 1
        for rx, title in _MISC_TOPICS:
            rows = [k for k in range(i + 1, j) if out[k].startswith('W(li(') and rx.search(out[k])]
            if len(rows) < _MISC_TOPIC_MIN:
                continue
            moved = [out[k] for k in rows]
            rest = [out[k] for k in range(i + 1, j) if k not in rows]
            # one box, no chips: the rows read as one description, the last one's table inside it (owner 2026-10-28)
            block = [f'W(subgroup("{title}", new="Reworked mechanic", one_box=True))', 'W(ul_open())', *moved,
                     'W(ul_close())', '']
            if not any(x.startswith('W(li(') for x in rest):
                out[i:j] = block                      # nothing else left in Miscellaneous
            else:
                out[i:j] = block + [out[i]] + rest
            j = i + len(block)
            break
        i = j
    return out


# Valve's "X now <verb> <new> instead of <old>" / "X now <verb> <new> — before, it <old>" rows of a reworked mechanic
# (7.41 Health Restoration): together one table, before and after the patch (owner 2026-10-28)
_BA_ROW_RE = re.compile(r'^W\(li\("(?P<text>[^"]+)", t\("REWORK"\)\)\)$')
_BA_TEXT_RES = (re.compile(r"^(?P<what>[A-Z][\w' ]+?) now (?P<verb>[a-z]+) (?P<new>.+?) instead of (?P<old>.+)$"),
                re.compile(r"^(?P<what>[A-Z][\w' ]+?) now (?P<verb>[a-z]+) (?P<new>.+?) — before, it (?P<old>.+)$"))


def _before_after(text):
    """(what, before, after) of one such row, else None."""
    for n, rx in enumerate(_BA_TEXT_RES):
        m = rx.match(text)
        if m:
            verb = m.group("verb")
            before = f"{verb} {m.group('old')}" if n == 0 else m.group("old")
            return m.group("what"), before[:1].upper() + before[1:], f"{verb[:1].upper()}{verb[1:]} {m.group('new')}"
    return None


def _postprocess_before_after(lines):
    out, i, in_mech = [], 0, False
    while i < len(lines):
        if _block_boundary(lines[i]):                 # only inside a "Reworked mechanic" block
            in_mech = 'new="Reworked mechanic"' in lines[i]
        run = []
        while in_mech and i + len(run) < len(lines):
            m = _BA_ROW_RE.match(lines[i + len(run)])
            parts = m and _before_after(m.group("text"))
            if not parts:
                break
            run.append(parts)
        if len(run) >= 2:
            rows = ", ".join(repr(r) for r in run)
            out.append(f'W(li("", t("REWORK"), extra=mech_before_after("Mechanic", [{rows}])))')
            i += len(run)
        else:
            out.append(lines[i])
            i += 1
    return out


_TEAM_ABILITIES = {"Glyph of Fortification": "hud_glyph", "Scan": "hud_scan"}
_TEAM_ABILITIES_HEADER = "Team Abilities"
_TEAM_ABILITY_ROW_RE = re.compile(r'W\(li\("(?:The )?(Glyph of Fortification|Glyph|Scan)(?::)? (.+)$', re.S)


_NEUTRAL_HEADER_RE = re.compile(r'^W\(unit_header\("(?P<name>[^"]+)", NEUTRAL_CDN \+ "(?P<slug>[^"]+)\.png"\)\)$')


def _postprocess_new_units(lines, version):
    """A neutral creep the game's files of the previous patch do not have is a new unit: its header says what it is and
    its numbers come as a unit_sheet (owner 2026-11-04, 7.38 amphibians). A unit that returns is still in the files, its
    sheet with the changes is written by hand (7.38 Ancient Prowlers)."""
    from patch import game_files
    from patch.unit_numbers import _block
    from patch.weights import _prev_version
    prev = _prev_version(version) if version else None
    units = "scripts/npc/npc_units.txt"
    now_text, prev_text = game_files.read(version, units), game_files.read(prev, units) if prev else None
    if not now_text or not prev_text:
        print(f"[WARN] new creeps not checked: {version} or {prev} is not in the game-files store")
        return lines
    out = []
    for line in lines:
        m = _NEUTRAL_HEADER_RE.match(line)
        npc = f'npc_dota_neutral_{m.group("slug")}' if m else None
        kv = _block(now_text, npc) if m else None
        if not kv or _block(prev_text, npc) is not None:
            out.append(line)
            continue
        ancient = "Ancient " if kv.get("IsAncient") == "1" else ""
        kind = "Ranged" if "RANGED" in kv.get("AttackCapabilities", "") else "Melee"
        label = f'New Level {kv.get("Level", "1")} {ancient}{kind} Creep'
        out.append(line[:-2] + f', new="{label}"))')
        out += ["W(ul_open())", f'W(unit_sheet("{m.group("slug")}", version="{version}"))', "W(ul_close())"]
    return out


def _postprocess_team_abilities(lines):
    """Glyph of Fortification and Scan are abilities every team has (owner 2026-11-04: "определять в патче и выносить в
    отдельную подкатегорию"): wherever a patch names them at the start of a row, the rows leave their lists for a
    category of their own, right after the first such list, an ability's header with the game's icon over each one's
    rows. A list left empty goes, with its header when nothing else is under it."""
    rows, first, anchor = {}, None, None
    keep = []
    for i, raw in enumerate(lines):
        m = _TEAM_ABILITY_ROW_RE.match(raw)
        if m:
            name = "Glyph of Fortification" if m.group(1) == "Glyph" else m.group(1)
            rest = m.group(2)
            rows.setdefault(name, []).append(f'W(li("{rest[0].upper()}{rest[1:]}')
            first = i if first is None else first
            continue
        keep.append(raw)
        if first is not None and anchor is None and raw.startswith('W(ul_close())'):
            anchor = len(keep)                         # right after the list the first row left
    if not rows:
        return lines
    block = [f'W(plain_header("{_TEAM_ABILITIES_HEADER}"))']
    for name in sorted(rows):                          # Glyph before Scan, whatever the order in the notes
        block += [f'W(ability("{name}", icon_url="../icons/abilities/{_TEAM_ABILITIES[name]}.png", innate=False))',
                  'W(ul_open())', *rows[name], 'W(ul_close())']
    if anchor is None:                                 # no list closes after the row: the block goes last
        anchor = len(keep)
    out = keep[:anchor] + block + keep[anchor:]
    i = 0
    while i + 1 < len(out):                            # the lists left empty
        if out[i].startswith('W(ul_open())') and out[i + 1].startswith('W(ul_close())'):
            del out[i:i + 2]
            if i and out[i - 1].startswith(('W(plain_header(', 'W(subgroup(')) \
                    and (i == len(out) or out[i].startswith(('W(plain_header(', 'W(section(', 'W(subgroup('))):
                del out[i - 1]
                i -= 1
            continue
        i += 1
    return out


def _postprocess_new_block_label(lines):
    out = list(lines)
    moves = []
    section = ''
    for i, raw_line in enumerate(out):
        line = raw_line.lstrip('\n')          # section spacing: a heading may carry leading blank lines
        pre = raw_line[:len(raw_line) - len(line)]
        head = _BLOCK_HEAD_RE.match(line)
        if not head:
            continue
        if head.group('fn') == 'plain_header':
            section = head.group('title')
        if 'new=' in head.group('rest'):
            continue
        j = i + 1
        rows = []
        while j < len(out) and not _block_boundary(out[j]):
            if out[j].startswith('W(li("'):
                rows.append(j)
            j += 1
        # a plain_header whose rows are all REWORK (≥3; QoL/NEW rows allowed) describes how a
        # REWORKED mechanic works now (7.38 Lifesteal): REWORK rows become the description box
        row_tags = [re.search(r't\("([A-Za-z]+)"\)', out[r]) for r in rows]
        row_tags = [m_.group(1) if m_ else None for m_ in row_tags]
        # ... and a subgroup of a mechanics section the same way from 2 rows (owner 2026-10-16, 7.41 "Health
        # Restoration", "Lifesteal and Damage Manipulations": like "Scaling with Hero Level")
        mech_sub = (head.group('fn') == 'subgroup' and 'mechanic' in (section or '').lower()
                    and row_tags.count('REWORK') >= 2)
        if ((head.group('fn') == 'plain_header' and row_tags.count('REWORK') >= 3 or mech_sub)
                and all(t_ in ('REWORK', 'QoL', 'NEW') for t_ in row_tags)):
            label = 'Reworked objective' if section.lower() == 'map objectives' else 'Reworked mechanic'
            out[i] = pre + line[:-2] + f', new="{label}"))'
            continue
        # the announcing row must be the block's FIRST row — a later "replaced
        # with new …" line inside an old block is an ordinary change
        if not rows or not _NEW_BLOCK_RE.search(out[rows[0]]):
            continue
        objective = (section.lower() == 'map objectives'
                     or _NEW_OBJECTIVE_RE.search(out[rows[0]]))
        label = 'New objective' if objective else 'New mechanic'
        out[i] = pre + line[:-2] + f', new="{label}"))'
        for r in rows:
            out[r] = out[r].replace('t("MISC")', 't("NEW")')
        # "Wisdom Runes removed and replaced with new buildings: Shrines of Wisdom" (7.38) is a
        # change of the OLD thing: it goes under its own "Wisdom Runes" subgroup above the new block.
        gone = _GONE_RE.match(out[rows[0]])
        if gone and 't("DEL")' in out[rows[0]] and head.group('fn') == 'subgroup' and out[i + 1] == 'W(ul_open())':
            moves.append((i, rows[0], gone.group('old')))
    for i, r, old in reversed(moves):
        row = out.pop(r)
        out[i:i] = [f'W(subgroup("{old}"))', 'W(ul_open())', row, 'W(ul_close())']
    return out


def _postprocess_merge_twin_rows(lines):
    """Two neighbouring rows that say the same thing about two values (7.38 "Lotus Pools will now
    spawn Great Lotuses after Tier 4 …" / "… Greater Lotuses after Tier 5 …", both with the same
    kind of info) are ONE change: "<shared start> A, and B" with a single info.
    Only tag-rows (no b()) with the same tag, ≥4 shared leading words and near-identical infos."""
    import difflib
    out = []
    i = 0
    while i < len(lines):
        a = _ROW_RE.match(lines[i])
        b = _ROW_RE.match(lines[i + 1]) if i + 1 < len(lines) else None
        if a and b and a.group('tag') == b.group('tag') and a.group('note') and b.group('note'):
            wa, wb = a.group('text').split(' '), b.group('text').split(' ')
            k = 0
            while k < min(len(wa), len(wb)) and wa[k] == wb[k]:
                k += 1
            ratio = difflib.SequenceMatcher(None, a.group('note'), b.group('note')).ratio()
            if k >= 4 and k < len(wb) and ratio >= 0.85:
                text = a.group('text') + ', and ' + ' '.join(wb[k:])
                out.append(_row(text, a.group('tag'), a.group('note')))
                i += 2
                continue
        out.append(lines[i])
        i += 1
    return out
