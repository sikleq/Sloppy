"""General Updates: its topics and mechanic blocks, and the lane creeps in them."""
import re

from .data import _strip_html
from .lines import _BOSSES, _boss_abilities, _drop_empty_ul, _li_parts
from .notes import _emit_notes

# ---------- ENTITY RENDERERS ----------

def _entity_title_decoration(entity):
    """Map raw `title` HTML (e.g. '<span class="New">New Tier 1 Artifact</span>')
    to item_header() decoration args."""
    title = entity.get('title')
    if not title:
        return ''
    txt = _strip_html(title).strip()
    if 'New' in txt or 'Returning' in txt:
        return f', new="{txt}"'
    if 'Rework' in txt:
        return f', changed="{txt}"'
    return ''


def _render_general_note(note):
    """One general_notes[] entry → section title + walked content."""
    out = []
    title = note.get('title', '').strip()
    if title in _BOSSES:          # 7.41e "Tormentor": the boss's card (link, patch strip), not a plain header
        out += ['', f'W(subgroup("{title}"))']      # a line of its own: _postprocess_boss_blocks matches it
    notes = note.get('generic', [])
    mech = []
    if title not in _BOSSES and not _MAP_SECTION.search(title):
        notes, mech = _mechanic_blocks(notes)
    elif title:
        out.append(f'\nW(plain_header("{title}"))')
    if mech:
        out += mech
    if title and title not in _BOSSES and not _MAP_SECTION.search(title) and _has_rows(notes):
        out.append(f'\nW(plain_header("{title}"))')
    if not _has_rows(notes):
        return out
    body, _ = _emit_notes(notes, general=True)
    out.extend(_general_topics(_bonus_from_note(_merge_all_followup(_link_lane_creeps(body))), title))
    return out


def _has_rows(notes):
    return any(not n.get('hide_dot') and _strip_html(n.get('note', '')).strip() for n in notes)


# Two Title Case words — the name of the thing a group of general rows is about ("Health Restoration")
_MECH_NAME_RE = re.compile(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b")
_NEW_MECH_RE = re.compile(r"\bnew\b[^.]*\b(?:stat|mechanic|created|system)\b", re.I)


def _mechanic_name(texts):
    """The name a group of general rows shares: the two-word Title Case term of its first row that the most rows of
    the group say (at least 2), else None."""
    rows = {}
    for i, text in enumerate(texts):
        for m in _MECH_NAME_RE.finditer(_strip_html(text)):
            rows.setdefault(m.group(1), set()).add(i)
    best = sorted(((len(r), n) for n, r in rows.items() if 0 in r and len(r) >= 2), reverse=True)
    return best[0][1] if best else None


def _mechanic_blocks(notes):
    """(the notes left, lines of mechanic blocks): a general section's group of rows (Valve splits them with a "<br>"
    row) about one named thing becomes its own block — plain_header(<name>, new="New mechanic" / "Reworked
    mechanic") — with every Valve row a row of its own (its "info" its "?"), as 7.38 Lifesteal (owner 2026-10-26, 7.39
    General Changes: Health Restoration's sub-rows had been folded into one row's "?" and an intro). A group of one
    row, or without a shared name, stays in the section."""
    groups, cur = [], []
    for n in notes:
        if n.get('hide_dot') and _strip_html(n.get('note', '')).strip() in ('', ):
            groups.append(cur)
            cur = []
        else:
            cur.append(n)
    groups.append(cur)
    left, out = [], []
    for group in groups:
        texts = [n.get('note', '') for n in group if not n.get('hide_dot')]
        name = _mechanic_name(texts) if len(texts) >= 2 else None
        if not name:
            if left and group:
                left.append({'indent_level': 1, 'hide_dot': True, 'note': '<br>'})
            left += group
            continue
        label = "New mechanic" if _NEW_MECH_RE.search(_strip_html(texts[0])) else "Reworked mechanic"
        body, _ = _emit_notes([dict(n, indent_level=1) for n in group])     # each Valve row a row: no folding
        tag = "NEW" if label == "New mechanic" else "REWORK"
        out += ['', f'W(plain_header("{name}", new="{label}"))']
        out += [_as_mech_row(l, tag) if l.startswith('W(li(') else l for l in body]
    return left, out


def _merge_all_followup(lines):
    """Valve's follow-up sentence "All <same subject> that …" goes into the row before it, as its "?" (owner
    2026-10-16, 7.41: "Innate abilities no longer scale with other abilities' level" + "All innate abilities that
    used to scale … now either provide unchangeable bonuses or improve on 'per level' basis" → one row). The
    follow-up's own note follows it in the same "?" (merge_tips joins them)."""
    out = []
    for line in lines:
        prev = _li_parts(out[-1]) if out else None
        cur = _li_parts(line)
        if prev and cur:
            subject = " ".join(prev[0].split()[:2]).lower()
            if len(subject.split()) == 2 and cur[0].lower().startswith(f"all {subject} "):
                notes = [s for s in (prev[1].get("extra"), f"inline_note({cur[0]!r})", cur[1].get("extra")) if s]
                head = out[-1].rstrip()
                if prev[1].get("extra"):
                    head = head.replace(f"extra={prev[1]['extra']}", "", 1).replace(", ))", "))").replace(", , ", ", ")
                out[-1] = head[:-2] + f", extra={' + '.join(notes)}))"
                continue
        out.append(line)
    return out


_LANE_ROW = re.compile(r"also_dyn=\[[^\]]*'unit\|(?:melee|ranged|flagbearer|siege)-creep")


# Topics of a general section, in the order their subgroups follow (owner 2026-10-16, 7.41 Global Changes: the
# rows stood mixed — innate scaling, currents, lane creeps). A lane creep row is the one _link_lane_creeps linked.
_GENERAL_TOPICS = (
    ("Scaling with Hero Level", re.compile(r"\bper level\b|\bhero level\b|\binnate abilit", re.I)),
    ("Lane Creeps", None),
)
_MAP_SECTION = re.compile(r"\bmap\b|terrain|objective", re.I)      # map notes keep Valve's order (terrain rows)
_GONE_FROM_GAME = re.compile(r"^[A-Z][\w' -]{2,40} removed from the game\.?$")
# a row about ONE lane creep goes under that creep's card, as a unit's rows do (owner 2026-10-16: "разделить на
# категории: Flagbearer, Siege, как с героями/юнитами"); its name prefix goes ("Flagbearer Creep: X" -> "X")
_LANE_CARDS = {
    "unit|melee-creep": ("Melee Creep", "npc_dota_creep_goodguys_melee"),
    "unit|ranged-creep": ("Ranged Creep", "npc_dota_creep_goodguys_ranged"),
    "unit|flagbearer-creep": ("Flagbearer Creep", "npc_dota_creep_goodguys_flagbearer"),
    "unit|siege-creep": ("Siege Creep", "npc_dota_goodguys_siege"),
}


_LANE_ABIL_PREFIX = {"unit|flagbearer-creep": "flagbearer_creep_"}


def _lane_card_abilities(key, rows):
    """(rows of the creep itself, {ability: (icon url, its rows, name off)}): a lane creep's row that starts with
    one of its abilities ("Inspiration Aura no longer affects heroes", 7.40) goes to that ability's block, as any
    unit's ability (owner 2026-10-16)."""
    prefix = _LANE_ABIL_PREFIX.get(key)
    abilities = _boss_abilities(prefix) if prefix else {}
    plain, per_abil = [], {}
    for line in rows:
        hit = next((a for a in sorted(abilities, key=len, reverse=True)
                    if re.match(r'^W\(li(?:_formula)?\("' + re.escape(a) + r':? [A-Za-z]', line)), None)
        if not hit:
            plain.append(line)
            continue
        m = re.match(r'^(W\(li(?:_formula)?\(")' + re.escape(hit) + r':? ([A-Za-z])', line)
        per_abil.setdefault(hit, (abilities[hit], []))[1].append(m.group(1) + m.group(2).upper() + line[m.end():])
    return plain, per_abil


def _lane_card(line):
    """The card a lane creep row belongs to: the one creep its also_dyn names, else None (a row about several)."""
    parts = _li_parts(line)
    keys = re.findall(r"'(unit\|[a-z-]+)'", (parts[1].get("also_dyn") or "") if parts else "")
    return keys[0] if len(keys) == 1 and keys[0] in _LANE_CARDS else None


def _strip_creep_name(line, key):
    name = _LANE_CARDS[key][0]
    m = re.match(rf'^(W\(li\("){re.escape(name)}:? ([a-z])', line, re.I)
    return f"{m.group(1)}{m.group(2).upper()}{line[m.end():]}" if m else line


def _general_topics(lines, title=""):
    """A general section's rows sorted into topic subgroups (_GENERAL_TOPICS): a topic with two rows or more gets its
    subgroup at the end, everything else stays on top. Lane creep rows about one creep go under that creep's card
    (unit_header, after the subgroups); the shared ones stay in "Lane Creeps". "<X> removed from the game" — the kind
    of change that sums up a patch (7.41 Facets) — leads the section as a stand-out row (li(major=True)), its tag
    kept. Map sections are left alone."""
    if _MAP_SECTION.search(title or ""):
        return lines
    rows = [l for l in lines if l.startswith("W(li(")]

    def topic(line):
        if _LANE_ROW.search(line):
            return "Lane Creeps"
        text = (_li_parts(line) or ("",))[0]
        return next((name for name, rx in _GENERAL_TOPICS if rx and rx.search(text)), None)

    lead = [l for l in rows if _GONE_FROM_GAME.match((_li_parts(l) or ("",))[0]) and len(rows) > 1]
    tops = {l: topic(l) for l in rows if l not in lead}
    counts = {}
    for t in tops.values():
        if t:
            counts[t] = counts.get(t, 0) + 1
    groups = [name for name, _rx in _GENERAL_TOPICS if counts.get(name, 0) >= 2]
    if not groups and not lead:
        return lines
    moved = set(lead) | {l for l, t in tops.items() if t in groups}
    out = []
    for l in lead:
        out += ['W(ul_open())', l[:-2] + ", major=True))", 'W(ul_close())']
    out += _drop_empty_ul([l for l in lines if l not in moved])
    cards = {}
    mech = []
    for name in groups:
        these = [l for l, t in tops.items() if t == name]
        if name in _MECH_TOPICS:          # a system that changed as a whole: its own "Reworked mechanic" section
            mech += ['', f'W(plain_header("{name}", new="Reworked mechanic"))', 'W(ul_open())']
            mech += [_as_mech_row(l) for l in these] + ['W(ul_close())']
            continue
        if name == "Lane Creeps":
            for l in these:
                key = _lane_card(l)
                if key:
                    cards.setdefault(key, []).append(_strip_creep_name(l, key))
            these = [l for l in these if not _lane_card(l)]
        if these:
            out += [f'W(subgroup("{name}"))', 'W(ul_open())'] + these + ['W(ul_close())']
    for key in _LANE_CARDS:
        if key in cards:
            name, icon = _LANE_CARDS[key]
            # page=: the card links to the creep's unit page and gets its patch strip (owner 2026-10-16: "should be
            # clickable, as a rule")
            out += [f'W(unit_header("{name}", "../icons/units/{icon}.png", general=False, page="{key.split("|")[1]}"))',
                    'W(ul_open())']
            plain, per_abil = _lane_card_abilities(key, cards[key])
            out += plain + ['W(ul_close())']
            for ab, (icon_url, ab_rows) in per_abil.items():
                out += [f'W(ability("{ab}", icon_url="{icon_url}"))', 'W(ul_open())'] + ab_rows + ['W(ul_close())']
    return out + mech


# topics that are one system changed as a whole (7.41 "Scaling with Hero Level"): a section of their own after the
# general block, its rows the description box — like 7.38 Lifesteal (owner 2026-10-16: "суммируем, показывая, что
# изменилось"; the rows' QoL / MISC chips read like continuations of the row above). Review: sum the rows and their
# "?" up into a few description lines.
_MECH_TOPICS = {"Scaling with Hero Level"}


def _as_mech_row(line, tag="REWORK"):
    """A row of a reworked- (or new-) mechanic section: REWORK (NEW), so it joins the description box; its own tag
    stays hidden in force_tag (filters, weights)."""
    m = re.search(r't\("(\w+)"\)', line)
    if not m or m.group(1).upper() == tag:
        return line
    own = m.group(1).lower()
    return line[:m.start()] + f't("{tag}")' + line[m.end():-2] + f', force_tag="{tag.lower()} {own}"))'


_BONUS_WAS = re.compile(r'\bbonus of (\d+)\b', re.I)


def _bonus_from_note(lines):
    """A row "… now give(s) … of N" whose "?" says the others gave M ("other sections provided max bonus of 100",
    7.41 currents) gets the number badge b(M, N) instead of a bare tag (owner 2026-10-16: "указать на сколько %")."""
    out = []
    for line in lines:
        parts = _li_parts(line)
        tag = re.search(r', t\("(?:BUFF|NERF|MISC)"\)', line)
        new = re.search(r'\bnow gives? .* of (\d+)$', parts[0]) if parts and tag else None
        was = _BONUS_WAS.search(parts[1].get("extra") or "") if new else None
        if was and was.group(1) != new.group(1):
            line = line[:tag.start()] + f", b({was.group(1)}, {new.group(1)})" + line[tag.end():]
        out.append(line)
    return out


_MELEE, _RANGED, _FLAG, _SIEGE = ("unit|melee-creep", "unit|ranged-creep",
                                  "unit|flagbearer-creep", "unit|siege-creep")
_LANE_LINKS = [
    (re.compile(r'\bFlagbearer', re.I), [_FLAG]),
    (re.compile(r'\bsiege creeps?\b|\bsiege units?\b|\bcatapults?\b', re.I), [_SIEGE]),
    (re.compile(r'^Melee Creeps?\b', re.I), [_MELEE]),
    (re.compile(r'^Ranged Creeps?\b', re.I), [_RANGED]),
    # paths and spawn points: every lane creep walks them (checked before "meet": 7.38c "creep paths … so the
    # creeps meet closer" is a path change)
    (re.compile(r'\blane creeps?\b.*\b(?:paths?|spawn)|\b(?:paths?|spawn points?)\b.*\blane creeps?\b|'
                r'\blane creep paths?\b', re.I), [_MELEE, _RANGED, _FLAG, _SIEGE]),
    # where the first waves meet — no Siege Creep in them (owner 2026-10-06, 7.41 "meeting point")
    (re.compile(r'\b(?:lane )?creeps? meet|\bmeeting point\b', re.I), [_MELEE, _RANGED, _FLAG]),
]


def _link_lane_creeps(lines):
    """General Updates rows about lane creeps → li(..., also_dyn=[...]): the row then counts on the creep's
    squares and shows on its own page (builders/entity_changes._add_also_rows; owner 2026-10-06 — the 7.41
    Flagbearer / siege / meeting-point rows sat only in General Updates and the creep cards had no page)."""
    out = []
    for line in lines:
        m = re.match(r'W\(li\("((?:[^"\\]|\\.)*)"', line)
        if m and line.endswith("))") and "also_dyn=" not in line:
            text = m.group(1)
            keys = next((k for rx, k in _LANE_LINKS if rx.search(text)), None)
            if keys:
                line = line[:-2] + f", also_dyn={keys!r}))"
        out.append(line)
    return out
