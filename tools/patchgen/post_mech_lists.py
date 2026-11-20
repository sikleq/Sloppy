"""General blocks that only point at other notes ("Specifics … can be found in the corresponding ability notes") get
those notes as a table (owner 2026-11-20, 7.42): Breakability of innates, Spell Power Reduction; and Item Potency's
worked examples as a table, its title a link to the site's Item Potency page."""
import re

_ROW_TEXT_RE = re.compile(r'^\s*W\(li(?:_formula)?\("((?:[^"\\]|\\.)*)"')
_HERO_RE = re.compile(r'^\s*W\(hero_header\("([^"]+)"')
_ITEM_RE = re.compile(r'^\s*W\(item_header\("([^"]+)"')
_ABIL_RE = re.compile(r'^\s*W\(ability\("([^"]+)"')
_TALENTS_RE = re.compile(r'^\s*W\(subgroup\("Talents"')
_SPECIFICS_RE = re.compile(r'^\s*W\(li\("Specifics for (?:this|these|any of these) changes? can be found in the '
                           r'corresponding [a-z ]*notes"')


def _entity_walk(lines):
    """(index, kind, owner, ability) of every line: whose block it is in."""
    kind = owner = abil = None
    for i, ln in enumerate(lines):
        m = _HERO_RE.match(ln) or _ITEM_RE.match(ln)
        if m:
            kind, owner, abil = ("hero" if _HERO_RE.match(ln) else "item"), m.group(1), None
        elif _ABIL_RE.match(ln):
            abil = _ABIL_RE.match(ln).group(1)
        elif _TALENTS_RE.match(ln):
            abil = "Talents"
        elif re.match(r'^\s*W\((?:section|plain_header)\(', ln):
            kind = owner = abil = None
        yield i, kind, owner, abil


# ---- Breakability of innates ----------------------------------------------------------------------------------------

_BREAK_HEAD_RE = re.compile(r'^(\s*)W\(li\("(Breakability rules of many innates updated)"')
_BREAK_ROW_RE = re.compile(r'li\("Now (fully|partially) disabled by Break(?:: ([^"]+))?"')


def _postprocess_breakability_list(lines):
    """"Breakability rules of many innates updated" + "Specifics … in the corresponding ability notes" → one row, the
    innates of the patch's "Now fully / partially disabled by Break" rows a table under it, as 7.37 Breakability (the
    partial ones say what Break stops in the "?"). No chip: the block has none, the tag stays hidden for the filters."""
    out = list(lines)
    head = next((i for i, ln in enumerate(out) if _BREAK_HEAD_RE.match(out[i])), None)
    if head is None:
        return out
    found = []
    for i, kind, owner, abil in _entity_walk(out):
        m = _BREAK_ROW_RE.search(out[i])
        if m and kind == "hero" and 'innate=True' in next((out[k] for k in range(i, -1, -1) if _ABIL_RE.match(out[k])), ""):
            how = "Fully" if m.group(1) == "fully" else "Partially"
            note = f" ({m.group(2)})" if m.group(2) else ""
            # "Hero's Ability how …": the grouped table (how | icons), not the flat one of "Hero: Ability" lines where
            # every icon hid its "how" behind a "?" (owner 2026-11-20)
            found.append(f"{owner}'s {abil} {how} disabled by Break{note}")
    if not found:
        raise ValueError("breakability list: the row is there, no innate says how Break now treats it")
    ind, text = _BREAK_HEAD_RE.match(out[head]).groups()
    found.sort(key=lambda s: ("Partially" in s, s))
    out[head] = f'{ind}W(li("{text}", t("REWORK"), force_tag="rework nerf", extra=inline_list("{"<br>".join(found)}")))'
    if head + 1 < len(out) and _SPECIFICS_RE.match(out[head + 1]):
        del out[head + 1]
    return out


# ---- Spell Power Reduction --------------------------------------------------------------------------------------------

_SPR_HEAD_RE = re.compile(r'^\s*W\(plain_header\("Spell Power Reduction"')
_SPR_MARK = "As a part of the comprehensive Spell Power Reduction"
# what a marked row changes, by its own words; the first that matches wins ("Damage Amplification" is amplification)
_SPR_KINDS = (("Spell and damage amplification", r"Amp\b|Amplification|extra spell damage|Damage Reverb|"
                                                 r"[Mm]agic [Rr]esistance [Rr]eduction"),
              ("Area of effect and cast range", r"\bAoE\b|Area of Effect|Cast Range"),
              ("Slows and durations", r"[Ss]low|Duration"),
              ("Damage", r"[Dd]amage|Multiplier"),
              ("Other", r""))


# Valve's rows of the block, said in one sentence (owner 2026-11-20: "в одно предложение переписать")
_SPR_SENTENCES = {
    ("Decreased most item contributions to ability scaling, including Spell Amplification, Area of Effect, and Cast Range",
     "Decreased damage of the majority of Magic and Pure damage spells",
     "Decreased duration of some long duration slows"):
    "Decreased most item contributions to ability scaling (Spell Amplification, Area of Effect and Cast Range), the "
    "damage of most Magic and Pure damage spells and the duration of some long slows",
}


def _postprocess_spell_power_list(lines):
    """Spell Power Reduction: Valve's rows and their "Specifics for any of these changes can be found in the
    corresponding ability or item notes" → one row, one sentence, the changes marked as a part of it a table of icons
    under it, by what each changes."""
    out = list(lines)
    head = next((i for i, ln in enumerate(out) if _SPR_HEAD_RE.match(ln)), None)
    if head is None:
        return out
    end = next((k for k in range(head + 1, len(out)) if out[k].strip() == "W(ul_close())"), None)
    spec = next((i for i in range(head + 1, end or head + 1) if _SPECIFICS_RE.match(out[i])), None)
    if spec is None:
        return out
    groups = {k: [] for k, _ in _SPR_KINDS}
    for i, kind, owner, abil in _entity_walk(out):
        if _SPR_MARK not in out[i] or not owner:
            continue
        m = _ROW_TEXT_RE.match(out[i])
        if not m:
            continue
        text = m.group(1)
        title = next(k for k, rx in _SPR_KINDS if not rx or re.search(rx, text))
        groups[title].append((kind, owner, abil, text))
    if not any(groups.values()):
        raise ValueError("spell power list: the block is there, no row is marked as a part of it")
    ind = re.match(r"^\s*", out[spec]).group(0)
    rows = [i for i in range(head + 1, end) if i != spec and _ROW_TEXT_RE.match(out[i])]
    texts = tuple(_ROW_TEXT_RE.match(out[i]).group(1) for i in rows)
    sentence = _SPR_SENTENCES.get(texts)
    if sentence is None:                         # Valve's rows unknown: they stay, the table is a row of its own
        sentence, rows = "Changes marked as a part of it in this patch", []
    table = f'{ind}W(li("{sentence}", t("REWORK"), force_tag="rework nerf", ' \
            f'extra=marked_changes({[(k, v) for k, v in groups.items() if v]!r})))'
    keep = [ln for i, ln in enumerate(out[head + 1:end], head + 1) if i not in rows and i != spec]
    return out[:head + 1] + keep + [table] + out[end:]


# ---- Item Potency -----------------------------------------------------------------------------------------------------

_MECH_PAGES = {"Item Potency": "item_potency.html"}
_MECH_HEAD_RE = re.compile(r'^(\s*W\(plain_header\("([^"]+)")(.*)\)\)\s*$')
_EXAMPLE_RE = re.compile(r'^\s*W\(li\("(?P<who>[^"]+?) (?:has|have|now have) (?P<plus>\+)?(?P<pct>\d+)% Item Potency, so if '
                         r'(?:they have|he has|she has|it has) an? (?P<item>[^"]+?) the \w+ would reduce armor by '
                         r'(?P<val>[\d.]+)".*inline_note\("(?P<base>[\d.]+) \* \d+%"\)')
_ILLUSION_RE = re.compile(r'Illusions have a default Item Potency of (\d+)%')
_DEFAULT_RE = re.compile(r'default Item Potency value for an attack is (\d+)%')
_STORY_EXAMPLE_RE = re.compile(r' For example: .*?\(\d+ × \d+%\)\.')
_STORY_FILLER_RE = re.compile(r'\. Specific details can be found in the associated item and ability changes\)')


def _fmt(x):
    return f"{x:g}"


def _example_label(who):
    """"Any hero attacking with a Tier 4 Evolved Enchantment" → a cell with its icon; "Attacks from Pangolier’s
    Swashbuckle" → Pangolier's Swashbuckle's icon and name."""
    who = who.replace("’", "'")
    # the source alone, with its icon: "Hero with Tier 4 Evolved Enchantment" was long (owner 2026-11-20)
    m = re.match(r"(?:Any hero attacking with a (?:Tier \d+ )?|Attacks from )(.+)$", who)
    name = m.group(1) if m else who
    return f'mech_example("{name}") + " {name}"'


def _potency_cell(pct, top):
    """The potency as a bar of its strength under the number (owner 2026-11-20: "Potency по силе выделить")."""
    return f'\'<span class="pot-bar" style="--pot:{pct / top * 100:.0f}%">{pct}%</span>\''


_EXCLUDING_RE = re.compile(r' \(excluding " \+ mech_example\("[^"]+"(?:, label="[^"]+")?\) \+ " and a few other items\)')


def _illusion_excluded(version):
    """The items illusions still don't apply, from data/rules/illusion_onhit_excluded.json (found in the game's code:
    Valve names only Skull Basher "and a few other items")."""
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "rules", "illusion_onhit_excluded.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f).get(version, {}).get("items", [])


def _postprocess_item_potency(lines, version=None):
    """Item Potency: the title links to its page; Valve's worked examples ("… so if they have a Desolator the attack
    would reduce armor by 7.2 (6 × 120%)") leave the paragraph for a table, the illusions' 20% one more line of it."""
    out = list(lines)
    for i, ln in enumerate(out):
        m = _MECH_HEAD_RE.match(ln)
        if m and m.group(2) in _MECH_PAGES and "page=" not in ln:
            out[i] = f'{m.group(1)}{m.group(3)}, page="{_MECH_PAGES[m.group(2)]}"))'
    story = next((i for i, ln in enumerate(out) if "W(mech_story(" in ln and "attribute called Item Potency" in ln), None)
    if story is None:
        return out
    end = next((k for k in range(story, len(out)) if out[k].strip() == "W(ul_close())"), len(out))
    block = out[story:end]
    examples = [m for m in (_EXAMPLE_RE.match(r) for r in block) if m]
    if not examples:
        return out
    base = float(examples[0].group("base"))
    item = examples[0].group("item")
    default = next((int(m.group(1)) for m in map(_DEFAULT_RE.search, block) if m), 100)
    rows = [(default, '"Any Hero"', _fmt(base * default / 100))]
    for e in examples:                       # "+20% Item Potency" is on top of the default
        pct = default + int(e.group("pct")) if e.group("plus") else int(e.group("pct"))
        rows.append((pct, _example_label(e.group("who")), e.group("val")))
    ill = next((int(m.group(1)) for m in map(_ILLUSION_RE.search, block) if m), None)
    if ill is not None:
        rows.append((ill, '"Standard Illusion"', _fmt(base * ill / 100)))
    rows.sort(key=lambda r: -r[0])                                    # strongest first
    top = rows[0][0]
    cells = ", ".join(f'[{who}, {_potency_cell(p, top)}, "{val}"]' for p, who, val in rows)
    # Valve's "(excluding Skull Basher and a few other items)": a line of the table with all of them (owner
    # 2026-11-20: "указать отдельной строкой … выяснить какие все эти excluded items")
    excluded = _illusion_excluded(version) if version else []
    if excluded:
        cells += f', "Illusions still don\'t apply: " + icons_with_notes({[tuple(x) for x in excluded]!r})'
    # the item in the head is an icon and its name, no link: the table is about the attack, not the item (11-20)
    table = (f'mech_table(["Attack", "Item Potency", mech_example("{item}") + " {item} armor reduction"], '
             f'[{cells}], cls="mech-grid")')
    s = _STORY_EXAMPLE_RE.sub("", out[story])
    s = _STORY_FILLER_RE.sub(")", s)
    if excluded:                                 # the table's last line names them all
        s = _EXCLUDING_RE.sub("", s)
    if "table=" in s:
        return out
    out[story] = re.sub(r"\)\)\s*$", f", table={table}))", s.rstrip())
    return out
