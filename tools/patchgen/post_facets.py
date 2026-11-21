"""Removed facets, innates and abilities of a hero as blocks of their own (cut out of post_cards.py, 2026-11-06)."""
import json
import os
import re

from .common import _HERE
from .lines import _FACET_BLOCK_RE, _HERO_NAME_RE, _REMOVED_ABILITY_RE, _REMOVED_FACETS_RE
from .post_cards import _after_innates


def _removed_facet_blocks(hero_slug, names, extra, prev, ind):
    """facet_header + "Removed" row per removed facet, named as the game's files of the patch before name them; None if
    a name has no facet there. A note ("Rage remains as Lifestealer's default basic ability") goes to the facet it
    names, else to the first."""
    from patch.ability_kv import hero_facets
    facets = {n.lower(): s for s, (n, _c, _i) in hero_facets(hero_slug, prev).items() if n}
    slugs = [facets.get(n.lower()) for n in names]
    if not names or None in slugs:
        return None
    note_at = next((k for k, n in enumerate(names) if extra and n.lower() in extra.lower()), 0)
    out = []
    for k, s in enumerate(slugs):
        tail = f', extra={extra}' if extra and k == note_at else ''
        out += [f'{ind}W(facet_header("{s}"))', f'{ind}W(ul_open())', f'{ind}W(li("Removed", t("DEL"){tail}))',
                f'{ind}W(ul_close())']
    return out


def _removed_innate_block(hero_slug, name, extra, prev, ind):
    """ability(...) + "Removed" row for "Removed <ability> ability": an innate (owner 2026-10-29: "Mastermind вообще
    innate"), or any other ability of the hero in the patch before — an upgrade's own ability too (owner 2026-11-06, 7.38
    Bloodseeker's Blood Mist: "это явно не General категория"). None when the hero had no such ability."""
    from patch.ability_kv import _hero_blocks
    from patch.aghs_text import not_in_game
    for slug, block in _hero_blocks(prev).items():
        if not (slug.startswith(f"{hero_slug}_") and isinstance(block, dict) and _slug_dname(slug, prev) == name
                and slug not in not_in_game()):
            continue
        tail = f', extra={extra}' if extra else ''
        innate = ', innate=True' if str(block.get("Innate", "")).strip() == "1" else ''
        return [f'{ind}W(ability("{name}", slug="{slug}"{innate}))', f'{ind}W(ul_open())',
                f'{ind}W(li("Removed", t("DEL"){tail}))', f'{ind}W(ul_close())']
    return None


def _removed_ability_home(hero_slug, name, span, prev):
    """Where a "Removed <name> ability" row belongs when not in a block of its own (owner 2026-11-06):
    "said" — a hidden sub-ability of another (the game's AbilityDraftPreAbility: 7.38 Eject of Dismember) whose block
    already says "No longer upgraded with Aghanim's …" ("можно убрать строку"); the name of another ability's block —
    a variant of it, "Adaptive Strike (Strength)" of Adaptive Strike ("это часть Adaptive Strike способности, а не
    General"); None otherwise."""
    from patch.ability_kv import _hero_blocks
    blocks = _hero_blocks(prev)
    slug = next((s for s, b in blocks.items() if s.startswith(f"{hero_slug}_") and isinstance(b, dict)
                 and _slug_dname(s, prev) == name), None)
    if slug and "HIDDEN" in str(blocks[slug].get("AbilityBehavior", "")):
        parent = next((s for s, b in blocks.items() if isinstance(b, dict) and b.get("AbilityDraftPreAbility") == slug),
                      None)
        at = next((k for k, l in enumerate(span) if parent and f'slug="{parent}"' in l and "W(ability(" in l), None)
        if at is not None:
            end = next((k for k in range(at, len(span)) if span[k].strip() == 'W(ul_close())'), len(span))
            if any("No longer upgraded with Aghanim" in l for l in span[at:end]):
                return "said"
    base = re.match(r"(.+?) \([A-Z][a-z]+\)$", name)
    if base and any(l.lstrip().startswith(f'W(ability("{base.group(1)}"') for l in span):
        return base.group(1)
    return None


_BARE_FACET_RE = re.compile(r'^(\s*)W\(facet_header\("([^"]+)"\)\)\s*$')
_BARE_REMOVED_RE = re.compile(r'^\s*W\(li\("Removed", t\("DEL"\)(, extra=.*)?\)\)\s*$')
_HERO_SPAN_END = ('W(hero_header(', 'W(item_header(', 'W(unit_header(', 'W(plain_header(', 'W(enchant_header(', 'W(section(',
                  'write_footer(', 'save_html(')


def _group_removed_facets(span):
    """One hero's lines with his bare "Removed" facet blocks made one block, where the first of them stood. Two notes
    would not fit one row: such a hero stays as written."""
    blocks = [k for k in range(len(span) - 3)
              if _BARE_FACET_RE.match(span[k]) and span[k + 1].strip() == 'W(ul_open())'
              and _BARE_REMOVED_RE.match(span[k + 2]) and span[k + 3].strip() == 'W(ul_close())']
    notes = [span[k + 2] for k in blocks if _BARE_REMOVED_RE.match(span[k + 2]).group(1)]
    if len(blocks) < 2 or len(notes) > 1:
        return span
    ind, _ = _BARE_FACET_RE.match(span[blocks[0]]).groups()
    slugs = ", ".join(f'"{_BARE_FACET_RE.match(span[k]).group(2)}"' for k in blocks)
    row = notes[0] if notes else span[blocks[0] + 2]
    gone = {k + d for k in blocks for d in range(4)}
    out = []
    for k, line in enumerate(span):
        if k == blocks[0]:
            out += [f'{ind}W(facet_group({slugs}))', f'{ind}W(ul_open())', row, f'{ind}W(ul_close())']
        elif k not in gone:
            out.append(line)
    return out


def _postprocess_removed_facet_groups(lines):
    """A hero who lost two or more facets in one patch: one block with their icons side by side and their names in one
    title, as ability_group (owner 2026-11-05, 7.38 Arc Warden Order and Disorder: "экономит место"). Works on generator
    output and indented content."""
    out, i = [], 0
    while i < len(lines):
        if not lines[i].lstrip().startswith('W(hero_header('):
            out.append(lines[i])
            i += 1
            continue
        end = next((k for k in range(i + 1, len(lines)) if lines[k].lstrip().startswith(_HERO_SPAN_END)), len(lines))
        out += [lines[i]] + _group_removed_facets(lines[i + 1:end])
        i = end
    return out


def _slug_dname(slug, version=None):
    """An ability's name: today's list, else the game's texts of `version` — an ability gone from the game has its
    name only there (7.38 Bad Juju, Parting Shot stayed in GENERAL: owner 2026-11-06 "Найди все такие случаи")."""
    try:
        with open(os.path.join(_HERE, 'data', 'abilities_slim.json'), encoding='utf-8') as f:
            name = (json.load(f).get(slug) or {}).get('dname')
    except (OSError, ValueError):
        name = None
    if not name and version:
        from patch import loc_history
        name = loc_history.tooltip(f"DOTA_Tooltip_Ability_{slug}", version) or None
    return name


def _postprocess_removed_facets(lines, version=None):
    """Owner 2026-10-29 (7.38 Invoker): "Removed Agnostic and Elitist Facets" is not a GENERAL row — each removed facet
    is its own block in the hero's Facets category, with its icon and name and a "Removed" row, as 7.39 does
    (Mephitic Shroud), before the hero's new facets; "Removed Mastermind ability" of an innate goes the same way into
    Abilities, as the innate's own block first there. The names are read from the game files of the patch before. A
    GENERAL list left empty goes. Works on generator output and indented content."""
    from patch.images import HERO_SLUG
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version) if version else None
    if not prev:
        return lines
    out, i = [], 0
    while i < len(lines):
        m = _HERO_NAME_RE.match(lines[i].lstrip())
        if not m:
            out.append(lines[i])
            i += 1
            continue
        hero_slug = HERO_SLUG.get(m.group(1), m.group(1).lower().replace(" ", "_").replace("'", ""))
        end = next((j for j in range(i + 1, len(lines))
                    if lines[j].lstrip().startswith(('W(hero_header(', 'W(item_header(', 'W(section(', 'write_footer('))),
                   len(lines))
        block, facets, innates, gone, into = lines[i:end], [], [], set(), []
        for k, l in enumerate(block):
            ind = l[:len(l) - len(l.lstrip())]
            fm, am = _REMOVED_FACETS_RE.match(l.lstrip()), _REMOVED_ABILITY_RE.match(l.lstrip())
            if fm:
                names = [n.strip() for n in re.split(r',\s*|\s+and\s+', fm.group(1)) if n.strip()]
                new = _removed_facet_blocks(hero_slug, names, fm.group(2), prev, ind)
                if new:
                    facets += new
                    gone.add(k)
            elif am:
                home = _removed_ability_home(hero_slug, am.group(1), block, prev)
                if home == "said":                  # a sub-ability its parent's "No longer upgraded" row covers
                    gone.add(k)
                    continue
                if home:                            # a part of another ability: its row goes into that block
                    into.append((home, l.lstrip()))
                    gone.add(k)
                    continue
                new = _removed_innate_block(hero_slug, am.group(1), am.group(2), prev, ind)
                if new:
                    innates += new
                    gone.add(k)
        if not gone:
            out.extend(block)
            i = end
            continue
        rest = [l for k, l in enumerate(block) if k not in gone]
        for k in range(len(rest) - 1):          # a GENERAL list with nothing left in it goes
            if rest[k].strip() == 'W(ul_open())' and rest[k + 1].strip() == 'W(ul_close())':
                del rest[k:k + 2]
                break
        starts = lambda pfx: next((k for k, l in enumerate(rest) if l.lstrip().startswith(pfx)), None)
        at_abil = starts(('W(ability(', 'W(subgroup("Talents"', 'W(subgroup("Abilities"'))
        at_abil = len(rest) if at_abil is None else at_abil
        # with the hero's other facets (Meepo 7.38: its innate block stands before them), else before the abilities
        at_facet = next((k for k, l in enumerate(rest) if _FACET_BLOCK_RE.match(l.lstrip())), at_abil)
        if at_facet <= at_abil:
            rest = rest[:at_abil] + innates + rest[at_abil:]
            rest = rest[:at_facet] + facets + rest[at_facet:]
        else:
            rest = rest[:at_facet] + facets + rest[at_facet:]
            rest = rest[:at_abil] + innates + rest[at_abil:]
        for name, row in into:                  # first in that ability's list
            at = next(j for j, l in enumerate(rest) if l.lstrip().startswith(f'W(ability("{name}"'))
            op = next(j for j in range(at, len(rest)) if rest[j].strip() == 'W(ul_open())')
            rest.insert(op + 1, rest[op][:len(rest[op]) - len(rest[op].lstrip())] + row)
        out.extend(_after_innates(rest, version))
        i = end
    return out


_RENAMED_RE = re.compile(r'^(\s*)W\(li\("Renamed from (.+?) to (.+?)"(?:, t\("[A-Z]+"\))?\)\)\s*$')
_FACET_HEAD_RE = re.compile(r'^(\s*)W\(facet_header\("([^"]+)"\)\)\s*$')


def _postprocess_renamed_facets(lines):
    """A facet whose first row is "Renamed from Old to New": the old name goes into its header, "Old → New", and
    the row goes, as for a renamed ability (owner 2026-11-10, 7.37 Corpse Eater -> Rage)."""
    out = list(lines)
    for i, line in enumerate(out):
        head = _FACET_HEAD_RE.match(line) if line is not None else None
        if not head:
            continue
        j = i + 1
        while j < len(out) and out[j].strip() in ("", "W(ul_open())"):
            j += 1
        row = _RENAMED_RE.match(out[j]) if j < len(out) else None
        if row:
            out[i] = f'{head.group(1)}W(facet_header("{head.group(2)}", old_title="{row.group(2)}"))'
            out[j] = None
    return [x for x in out if x is not None]


# ---- facet passes moved from post_late.py (Fable review 2026-11-21) ----
_ROW_TO_VALUES_RE = re.compile(r'^\s*W\(li\("[^"]* (?:decreased|increased|rescaled) from [^"]* to ([^"]+)"')


def _row_values_in_text(row, text):
    """A "… from A to B" row whose every B is in the card's new text says what the card says (owner 2026-11-02: "Spell
    Lifesteal decreased from 12-18% to 2-14%" goes in the new side of Succubus' card)."""
    m = _ROW_TO_VALUES_RE.match(row)
    values = set(re.findall(r"\d+(?:\.\d+)?", m.group(1))) if m else set()
    return bool(values) and values <= set(re.findall(r"\d+(?:\.\d+)?", text))


_FACET_IMPROVES_RE = re.compile(r'^(\s*)W\(li\("Now is a facet that improves ([^"]+)", t\("[A-Za-z]+"\)\)\)\s*$')


def _postprocess_facet_improves_row(lines):
    """"Now is a facet that improves Succubus" + "Succubus: Now also makes …" -> one row, tagged NEW (owner 2026-11-02)."""
    out, i = [], 0
    while i < len(lines):
        m = _FACET_IMPROVES_RE.match(lines[i])
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        rest = m and re.match(r'^\s*W\(li\("' + re.escape(m.group(2)) + r': (?:Now )?(.)(.*)$', nxt)
        if not rest:
            out.append(lines[i])
            i += 1
            continue
        tail = re.sub(r't\("[A-Za-z]+"\)', 't("NEW")', rest.group(2), count=1)
        out.append(f'{m.group(1)}W(li("Now is a facet that improves {m.group(2)}: {rest.group(1).lower()}{tail}')
        i += 2
    return out


_BLOCK_START_RE_LATE = re.compile(r'^\s*W\((ability|ability_change|ability_group|two_selves_change|new_ability|facet_header|facet_group|new_facet|facet_change)\(')
_FACET_KINDS = ("facet_header", "facet_group", "new_facet", "facet_change")
_HERO_END_RE = re.compile(r'^\s*(?:W\((?:hero_header|section|unit_header|item_header|plain_header|enchant_header)\(|write_footer\(|save_html\()')


def _facets_first(span):
    """One hero's lines with his facet blocks before his ability blocks, each kind in its order (entity-rendering.md). A
    hero whose facets own the abilities that follow them (sub=True, 7.39 Invoker) stays as written."""
    stop = next((k for k, ln in enumerate(span) if "W(subgroup(" in ln), None)
    if stop is None:
        stop = len(span)
        while stop and (not span[stop - 1].strip() or span[stop - 1].lstrip().startswith("#")):
            stop -= 1
    starts = [k for k in range(stop) if _BLOCK_START_RE_LATE.match(span[k])]
    if not starts or any("sub=True" in ln for ln in span[:stop]):
        return span
    blocks = [span[a:b] for a, b in zip(starts, starts[1:] + [stop])]
    kinds = [_BLOCK_START_RE_LATE.match(b[0]).group(1) in _FACET_KINDS for b in blocks]
    if kinds == sorted(kinds, reverse=True):
        return span
    facets = [b for b, f in zip(blocks, kinds) if f]
    others = [b for b, f in zip(blocks, kinds) if not f]
    return span[:starts[0]] + [ln for b in facets + others for ln in b] + span[stop:]


def _postprocess_facets_first(lines):
    """A hero's rows, his facets, then his abilities: an innate block written before the facets put a second run of
    abilities after them (owner 2026-11-02, 7.38 Morphling: "сначала способность, потом фасеты, потом опять способности")."""
    out, i = [], 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("W(hero_header("):
            out.append(lines[i])
            i += 1
            continue
        end = next((k for k in range(i + 1, len(lines)) if _HERO_END_RE.match(lines[k])), len(lines))
        out += [lines[i]] + _facets_first(lines[i + 1:end])
        i = end
    return out



_FACET_LINE_RE = re.compile(r'^(\s*)W\(facet_header\("([^"]+)"\)\)\s*$')
_NEW_FACET_ROW_RE = re.compile(r'^\s*W\(li\("New Facet"', re.I)
_LI_TEXT_RE = re.compile(r'^\s*W\(li\("((?:[^"\\]|\\.)*)"')


def _postprocess_new_facet_rows(lines):
    """facet_header + a "New Facet" row + its description rows (7.37 Medusa: Valve wrote them as rows) → the new
    facet card new_facet(slug, desc=[…]), as 7.38's new facets."""
    out, i = [], 0
    while i < len(lines):
        m = _FACET_LINE_RE.match(lines[i])
        if not (m and i + 2 < len(lines) and lines[i + 1].strip() == "W(ul_open())"
                and _NEW_FACET_ROW_RE.match(lines[i + 2])):
            out.append(lines[i])
            i += 1
            continue
        end = next((k for k in range(i + 3, len(lines)) if lines[k].strip() == "W(ul_close())"), len(lines))
        desc = [t.group(1) for t in (_LI_TEXT_RE.match(r) for r in lines[i + 3:end]) if t]
        items = ", ".join(f'"{d}"' for d in desc)
        out.append(f'{m.group(1)}W(new_facet("{m.group(2)}", desc=[{items}]))')
        i = end + 1
    return out
