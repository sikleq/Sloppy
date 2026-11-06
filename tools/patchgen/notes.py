"""A list of patch notes as rows: folding sub-notes into a row, grouping and sorting them."""
import re

from .data import _strip_html
from .rows import _AGHS_NOW_RE, _DMG_L1_RE, _KIDS_ARE_BODY, _NOT_AGHS_DESC, _emit_li, _sort_source_ul_blocks

def _merge_aghs_description(notes):
    """"Now upgraded with Aghanim's Shard" with its description nested under it (Valve, 7.39 Aphotic Shield: "Deals
    75% of absorbed damage to nearby enemies" one level deeper) -> one note "Aghanim's Shard: <description>": the card
    under the ability is drawn from that row (owner 2026-10-27: the draft had two rows, NEW + a MISC description, and
    the proofread merged them by hand). Before the rows are sorted by tag. A kid that is a row of its own ("No
    longer …", another Aghanim's line) keeps the rows apart."""
    out, i = [], 0
    while i < len(notes):
        n = notes[i]
        m = _AGHS_NOW_RE.fullmatch((n.get('note') or '').strip())
        level = n.get('indent_level', 0)
        kids = []
        j = i + 1
        while m and j < len(notes) and notes[j].get('indent_level', 0) > level:
            kids.append((notes[j].get('note') or '').strip())
            j += 1
        if kids and all(k and not _NOT_AGHS_DESC.search(k) for k in kids):
            desc = " ".join(k if k.endswith(".") or k is kids[-1] else k + "." for k in kids)
            out.append(dict(n, note=f"Aghanim's {m.group(1).title()}: {desc}"))
            i = j
            continue
        out.append(n)
        i += 1
    return out


def _descendants(notes, i):
    """Indices of every note nested under notes[i] (deeper indent, contiguous)."""
    lvl = notes[i].get('indent_level', 1)
    out = []
    for j in range(i + 1, len(notes)):
        if notes[j].get('indent_level', 1) <= lvl:
            break
        out.append(j)
    return out


def _nested_info_text(notes, lvl, desc):
    """Nested notes → one popup text: each direct child on its own line; a
    single deeper note is appended to its line after " — ", several deeper
    notes follow on their own indented "– " lines."""
    groups = []                                  # [direct child text, [deeper texts], [their levels]]
    for j in desc:
        t = (notes[j].get('note') or '').strip()
        if (notes[j].get('info') or '').strip():
            t += f' <span class="pop-note">({notes[j]["info"].strip()})</span>'
        level = notes[j].get('indent_level', 1)
        if level == lvl + 1 or not groups:
            groups.append([t, [], []])
        elif groups[-1][2] and level > groups[-1][2][0]:
            # a note on a deeper item, not an item of its own: in brackets after it (owner 2026-10-27, 7.40
            # Invulnerability Targeting: Ogre Magi's "Can still target invulnerable buildings" was a list item);
            # its own "(i.e. …)" becomes ", i.e. …" — no brackets in brackets
            t = re.sub(r'\s*\(([^()]*)\)', r', \1', t)
            groups[-1][1][-1] += f' <span class="pop-note">({t})</span>'
        else:
            groups[-1][1].append(t)
            groups[-1][2].append(level)
    lines, after = [], []
    for head, deeper, _levels in groups:
        # "All three of these will also …": about the whole list, a line of its own after it (7.40 Cyclone cases)
        deeper, whole = ([d for d in deeper if not _ABOUT_ALL_RE.match(d)],
                         [d for d in deeper if _ABOUT_ALL_RE.match(d)])
        after += whole
        if len(deeper) == 1:
            lines.append(f'{head} — {deeper[0]}')
        else:
            lines.append(head)
            lines.extend(f'&nbsp;&nbsp;– {d}' for d in deeper)
    lines += [f'<span class="pop-note">{a}</span>' for a in after]
    return '<br>'.join(lines)


_ABOUT_ALL_RE = re.compile(r'^(?:All|Both|Each) (?:\w+ )?of (?:these|them)\b', re.I)
_FOLD_INTO_PREV_RE = re.compile(r'^(?:[^:]{2,40}:\s+)?Damage to (?:the )?secondary target is equal to\b', re.I)


_PLAIN_ABILITY_RE = re.compile(r'^W\(ability\("([^"]+)"(?:, slug="([^"]+)")?\)\)$')
_STALE_NOTE_RE = re.compile(r'^# \[patchnotes: belongs to ')      # a pre-2026-10-29 marker: the same text, two abilities
# Sibling abilities — parts of one mechanic — that may share a block (owner 2026-10-30): Invoker's orbs and Invoke,
# Morphling's two Attribute Shifts, Jakiro's Liquid Fire / Frost, Shadow Demon's Demonic Purge / Cleanse. Different
# abilities of a hero with the same row by chance (Omniknight's mana, Skywrath's Scepter range) stay apart.
# slug -> name: a page may name the ability without its slug (7.41 `ability("Quas")`).
SIBLING_ABILITIES = (
    {"invoker_quas": "Quas", "invoker_wex": "Wex", "invoker_exort": "Exort", "invoker_invoke": "Invoke"},
    {"morphling_morph_agi": "Attribute Shift (Agility Gain)", "morphling_morph_str": "Attribute Shift (Strength Gain)"},
    {"jakiro_liquid_fire": "Liquid Fire", "jakiro_liquid_ice": "Liquid Frost"},
    {"shadow_demon_demonic_purge": "Demonic Purge", "shadow_demon_demonic_cleanse": "Demonic Cleanse"},
)
_SIBLING_SLUG_OF = {name: slug for family in SIBLING_ABILITIES for slug, name in family.items()}


def _siblings(a, b):
    return any(a in family and b in family for family in SIBLING_ABILITIES)


def _postprocess_same_change_abilities(lines):
    """Consecutive blocks of sibling abilities whose rows are the very same → one ability_group block with their icons
    stacked (owner 2026-10-30, 7.37b Quas / Wex / Exort / Invoke "Can now be cast during channeling …"). Innates,
    abilities that are not SIBLING_ABILITIES and blocks with anything but one ul of rows are left alone; a stale
    "belongs to" marker inside a block goes."""
    def block_at(i):
        m = _PLAIN_ABILITY_RE.match(lines[i].strip()) if i < len(lines) else None
        if not m or i + 1 >= len(lines) or lines[i + 1].strip() != 'W(ul_open())':
            return None
        slug = m.group(2) or _SIBLING_SLUG_OF.get(m.group(1))
        if not slug:
            return None
        j, rows = i + 2, []
        while j < len(lines) and (lines[j].strip().startswith('W(li(') or _STALE_NOTE_RE.match(lines[j].strip())):
            if lines[j].strip().startswith('W(li('):
                rows.append(lines[j])
            j += 1
        if not rows or j >= len(lines) or lines[j].strip() != 'W(ul_close())':
            return None
        return (m.group(1), slug), rows, j + 1
    out, i = [], 0
    while i < len(lines):
        first = block_at(i)
        if not first:
            out.append(lines[i])
            i += 1
            continue
        group, rows, end = [first[0]], first[1], first[2]
        notes = [_note_of(rows)]
        nxt = block_at(end)
        while nxt and (([r.strip() for r in nxt[1]] == [r.strip() for r in rows] and _siblings(group[0][1], nxt[0][1]))
                       or _same_row_own_notes(rows, nxt[1], group[0][1], nxt[0][1])):
            group.append(nxt[0])
            notes.append(_note_of(nxt[1]))
            end = nxt[2]
            nxt = block_at(end)
        if len(group) < 2:
            out.extend(lines[i:end])
        else:
            ind = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            pairs = ", ".join(f'("{t}", "{s}")' for t, s in group)
            if len(set(notes)) > 1:              # each ability's own [?] in one, under its name
                merged = "<br>".join(name + ": " + _LEVELS_OF_RE.sub(r"\1 (\2) \3", line)
                                     for (name, _s), note in zip(group, notes) for line in note.split("<br>"))
                rows = [_ROW_NOTE_RE.sub(lambda m: f'{m.group(1)}, extra=inline_note("{merged}")))', rows[0])]
            out += [f'{ind}W(ability_group({pairs}))', lines[i + 1], *rows, f'{ind}W(ul_close())']
        i = end
    return out


# "Travel Distance for levels 9 and 10 of Wex is 3900/4200" -> "Travel Distance (Wex) 3900/4200": the row says the levels
_LEVELS_OF_RE = re.compile(r"^(.+?) for levels \d+ and \d+ of (\w+) is (.+)$")
_ROW_NOTE_RE = re.compile(r'^(\s*W\(li\(.*?), extra=inline_note\("((?:[^"\\]|\\.)*)"\)\)\)\s*$')


def _note_of(rows):
    m = _ROW_NOTE_RE.match(rows[0]) if len(rows) == 1 else None
    return m.group(2) if m else ""


def _same_row_own_notes(rows, other, slug, other_slug):
    """One row each, the same words and tag, each its own [?] (owner 2026-11-06, 7.38 Tornado, E.M.P., Alacrity, Chaos
    Meteor, Sun Strike: "Added values for levels 9 and 10" — "имеют общий текст, поэтому их можно в одну строку, а
    иконки по аналогии с Attribute Shift"); the hero's abilities, not only the sibling ones."""
    if len(rows) != 1 or len(other) != 1 or slug.split("_")[0] != other_slug.split("_")[0]:
        return False
    a, b = _ROW_NOTE_RE.match(rows[0]), _ROW_NOTE_RE.match(other[0])
    return bool(a and b and a.group(1).strip() == b.group(1).strip())


_GROUP_NAMES_RE = re.compile(r'\("([^"]+)", "[^"]+"\)')


def _postprocess_group_rows_home(lines):
    """A row of the hero's own list that names every ability of a block of several (7.38 Jakiro "Both Liquid Fire and
    Liquid Frost abilities are now available …", "Liquid Frost is always applied with the first attack, Liquid Fire -
    with the second") goes to the top of that block's list, next to its "Aghanim's Shard reworked" (owner
    2026-10-30: "надо поставить к Liquid Fire/Frost"); a hero list left empty goes."""
    out = list(lines)
    for g, ln in enumerate(lines):
        if "W(ability_group(" not in ln:
            continue
        names = _GROUP_NAMES_RE.findall(ln)
        head = next((k for k in range(g - 1, -1, -1) if "W(hero_header(" in out[k]), None)
        if len(names) < 2 or head is None or g + 1 >= len(out) or out[g + 1].strip() != "W(ul_open())" \
                or out[head + 1].strip() != "W(ul_open())":
            continue
        stop = next((k for k in range(head + 2, g) if out[k].strip() == "W(ul_close())"), None)
        if stop is None:
            continue
        moved = [k for k in range(head + 2, stop)
                 if out[k].strip().startswith("W(li(") and all(n in out[k] for n in names)]
        if not moved:
            continue
        rows = [out[k] for k in moved]
        gi = g - len(moved)                                    # the group's line once the rows are out
        out = [x for k, x in enumerate(out) if k not in moved]
        out[gi + 2:gi + 2] = rows
        if out[head + 2].strip() == "W(ul_close())":
            del out[head + 1:head + 3]
        return _postprocess_group_rows_home(out)
    return out


def _fold_into_row(lines, idx, text):
    """Append `text` to the "?" popup of the W(li(…)) at lines[idx]: extend an
    existing inline_note with <br>, otherwise add one. A row that already has
    another extra= (e.g. note_box on a "Base X increased" row) is concatenated,
    never given a second `extra=` kwarg (SyntaxError)."""
    esc = text.replace('"', '\\"')
    old_line = lines[idx]
    if 'extra=inline_note' in old_line:
        lines[idx] = re.sub(
            r'(extra=inline_note\(")(.*?)("\)+)$',
            lambda m: f'{m.group(1)}{m.group(2)}<br>{esc}{m.group(3)}',
            old_line, count=1,
        )
        return
    k = old_line.rfind('))')
    if k >= 0:
        joiner = (f' + inline_note("{esc}")))' if 'extra=' in old_line
                  else f', extra=inline_note("{esc}")))')
        lines[idx] = old_line[:k] + joiner

def _emit_notes(notes, ul_open_called=False, hero_name=None, version=None,
                loc_map=None, current_ability_slug=None, general=False):
    """Walk notes array, respecting indent_level hierarchy and special
    fields (hide_dot, info, aghanims). Returns list of source lines.

    Algorithm:
    - indent_level 1 rows → top-level li in the current ul.
    - indent_level N+1 row immediately following an N-level row → fold its
      text into the parent's `info` (inline_note).
    - hide_dot:true rows act as subgroup separators or category headers.
    - `info` field on a row → append as inline_note to that row's li.

    Returns (lines, has_content) — has_content false if all notes were
    hide_dot/empty.
    """
    lines = []
    open_ul = ul_open_called
    has_content = False

    def open_ul_if_needed():
        nonlocal open_ul
        if not open_ul:
            lines.append('W(ul_open())')
            open_ul = True

    notes = _merge_aghs_description(notes)
    consumed = set()                # sub-note indices already folded into a parent row

    for i, n in enumerate(notes):
        if i in consumed:
            continue
        txt = (n.get('note') or '').strip()
        lvl = n.get('indent_level', 1)
        hide = n.get('hide_dot', False)
        info = n.get('info')
        aghs = n.get('aghanims')

        if hide:
            # Section/category marker. Close current ul and emit subgroup.
            stripped = _strip_html(txt).strip()
            if open_ul:
                lines.append('W(ul_close())')
                open_ul = False
            if stripped and stripped not in ('<br>', ''):
                lines.append(f'W(subgroup("{stripped}"))')
            continue

        # L2 row with short header-like text AND followed by L3 children
        # → treat as subgroup (e.g. "Items", "Heroes", "Neutral Creeps"
        # inside Invulnerability Targeting). Detection: short text (≤3
        # words, no period) AND next note has lvl > this lvl.
        clean = _strip_html(txt).strip()
        next_lvl = notes[i + 1].get('indent_level', 1) if i + 1 < len(notes) else 0
        is_short_header = (
            lvl >= 2
            and len(clean.split()) <= 3
            and not clean.endswith('.')
            and not clean.endswith(':')
            and next_lvl > lvl
        )
        if is_short_header:
            if open_ul:
                lines.append('W(ul_close())')
                open_ul = False
            lines.append(f'W(subgroup("{clean}"))')
            continue

        # a row that only gives a value of the row before (owner 2026-10-30, 7.37b Death Ward: "Damage to secondary target
        # is equal to 65% of the primary" goes in the "?" of "Now has a primary and secondary target")
        if _FOLD_INTO_PREV_RE.match(clean) and lines and lines[-1].startswith('W(li('):
            # into the row of this list that brings the secondary target in, else the row right before
            k = len(lines) - 1
            while k >= 0 and lines[k].startswith('W(li(') and 'secondary target' not in lines[k]:
                k -= 1
            if k < 0 or not lines[k].startswith('W(li('):
                k = len(lines) - 1
            _fold_into_row(lines, k, re.sub(r'^[^:]{2,40}:\s+', '', clean, count=1))
            continue
        open_ul_if_needed()
        # Check patchnotes_english: warn if this text belongs to a different ability.
        if loc_map is not None and current_ability_slug is not None:
            txt_norm = re.sub(r'\s+', ' ', _strip_html(txt)).lower().strip()
            expected = loc_map.get(txt_norm, set()) - {None}
            if expected and current_ability_slug not in expected:
                lines.append(f'# [patchnotes: belongs to {", ".join(sorted(expected))}]')
        lines.append(_emit_li(txt, info=info, aghs=aghs, hero_name=hero_name, version=version))
        has_content = True

        # Nested notes (the official patch page indents them under this bullet)
        # go into this row's "?" popup — all of them, lists and sub-changes
        # alike, the trailing ":" dropped. Kept as rows: "Damage at level N"
        # consequences (a visible row by rule) and the body of card-type
        # parents (_KIDS_ARE_BODY).
        desc = _descendants(notes, i)
        if (desc and lines[-1].startswith('W(li(') and not aghs
                and not _KIDS_ARE_BODY.match(clean)
                and not any(notes[j].get('hide_dot') for j in desc)):
            folded = [j for j in desc
                      if not _DMG_L1_RE.search(_strip_html(notes[j].get('note') or ''))]
            if folded:
                # a list the row introduces ("…every ability:", "The following …"): inline_list, a table open under
                # the row in a Reworked mechanic (owner 2026-10-28, 7.38 Lifesteal); clarifications stay a "?". Only
                # in General Updates, where the mechanics are — heroes / items keep their "?" (owner 2026-10-28)
                is_list = general and (bool(re.search(r':\s*(?=")', lines[-1]))
                                       or clean.lower().startswith("the following ")) and 'extra=' not in lines[-1]
                lines[-1] = re.sub(r':(?=")', '', lines[-1], count=1)   # "…the following:" → "…the following"
                _fold_into_row(lines, len(lines) - 1, _nested_info_text(notes, lvl, folded))
                if is_list:
                    lines[-1] = lines[-1].replace('extra=inline_note(', 'extra=inline_list(', 1)
                consumed.update(folded)

    if open_ul:
        lines.append('W(ul_close())')
    lines = _sort_source_ul_blocks(lines)
    return lines, has_content
