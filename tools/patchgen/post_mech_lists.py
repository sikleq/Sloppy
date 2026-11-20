"""General blocks that only point at other notes ("Specifics … can be found in the corresponding ability notes") get
those notes as a table (owner 2026-11-20, 7.42): Breakability of innates, Spell Power Reduction; and Item Potency's
worked examples as a table, its title a link to the site's Item Potency page."""
import re

_ROW_TEXT_RE = re.compile(r'^\s*W\(li(?:_formula)?\("((?:[^"\\]|\\.)*)"')
_FORMULA_ROW_RE = re.compile(r'^\s*W\(li_formula\("((?:[^"\\]|\\.)*)", "([^"]+)", "([^"]+)"')
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
        f = _FORMULA_ROW_RE.match(out[i])
        if f:              # "Max Damage/Heal Amp decreased" says by how much only in its formulas (owner 2026-11-20)
            text = f"{text} from {f.group(2)} to {f.group(3)}"
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


# ---- Neutral item tiers --------------------------------------------------------------------------------------------

_TIERS_ROW_RE = re.compile(r'^(\s*)W\(li\("(Number of item tiers (?:de|in)creased from \d+ to \d+)", ')
_MADSTONE_ROW_RE = re.compile(r'^(\s*)W\(li\("Madstone cost[^"]*"(.*)\)\)\s*$')
_KV_TIER_RE = re.compile(r'^\t\t"(\d+)"\s*\{(.*?)^\t\t\}', re.S | re.M)


def neutral_tiers(text):
    """neutral_items.txt → ({tier: {"start_time", "craft_cost", "recraft_cost"}}, the infinite Madstone time)."""
    tiers = {}
    for m in _KV_TIER_RE.finditer(text):
        head = m.group(2).split('"item', 1)[0]
        tiers[int(m.group(1))] = dict(re.findall(r'"(start_time|craft_cost|recraft_cost)"\s+"([^"]+)"', head))
    free = re.search(r'"madstone_no_limit_time"\s+"([^"]+)"', text)
    return tiers, free.group(1) if free else None


def _tier_table(old, new):
    """The tiers of both patches side by side, each value "before → after" with its % (owner 2026-11-20: "Number of item
    tiers decreased from 5 to 4 сделать как было до и после, учитывая ещё madstone косты"): a later tier and a dearer
    Madstone are worse (l=True), an earlier infinite Madstone better."""
    (ot, of), (nt, nf) = old, new

    def pair(a, b, lower=True):
        if a is None and b is None:
            return '"", ""'
        return f'*mech_change_cells({a or "—"!r}, {b or "—"!r}, l={lower})'
    rows = []
    for n in sorted(set(ot) | set(nt)):
        o, w = ot.get(n, {}), nt.get(n, {})
        rows.append(f'["Tier {n}", {pair(o.get("start_time"), w.get("start_time"))}, '
                    f'{pair(o.get("craft_cost"), w.get("craft_cost"))}, '
                    f'{pair(o.get("recraft_cost"), w.get("recraft_cost"))}]')
    if of or nf:
        rows.append(f'["Infinite Madstone", {pair(of, nf)}, "", "", "", ""]')
    return ('mech_table(["Tier", "Available at", "", mech_example("Madstone Bundle") + " Madstone cost", "", '
            f'"Recraft cost", ""], [{", ".join(rows)}], cls="mech-grid mech-change-grid")')


def _postprocess_neutral_tiers(lines, version=None):
    """"Number of item tiers decreased from 5 to 4" + its rows of Madstone costs → one row, the tiers of both patches a
    table "before → after" from the game's neutral_items.txt (start time, Madstone cost, recraft cost, infinite
    Madstone); the Madstone rows hidden under it (they stay for the filters). No store of game files (CI): unchanged."""
    out = list(lines)
    i = next((k for k, ln in enumerate(out) if _TIERS_ROW_RE.match(ln)), None)
    if i is None or not version:
        return out
    from patch import game_files
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version)
    texts = [game_files.read(v, "scripts/npc/neutral_items.txt") if game_files.available() else None
             for v in (prev, version)]
    if not all(texts):
        return out
    ind, text = _TIERS_ROW_RE.match(out[i]).groups()
    # a rework of the tiers, not a -20% of a number: what changed is in the table (7.42 page: REWORK)
    out[i] = (f'{ind}W(li("{text}", t("REWORK"), '
              f'extra={_tier_table(neutral_tiers(texts[0]), neutral_tiers(texts[1]))}))')
    k = i + 1
    while k < len(out) and _MADSTONE_ROW_RE.match(out[k]):
        if "covered=True" not in out[k]:
            out[k] = re.sub(r"\)\)\s*$", ", covered=True))", out[k].rstrip())
        k += 1
    return out


# ---- One rule told in several rows -----------------------------------------------------------------------------------

# Valve's rows of one block that tell one rule in pieces, each a row with its own tag → one sentence, one tag, the
# block's table and note kept (owner 2026-11-20, 7.42 Artifact Pools: "совместить в одно предложение … нет смысла в 3
# разных предложения с 3 тегами", as Spell Power Reduction above: one sentence, the table under it)
_ONE_SENTENCE = {
    ("Options for a tier are no longer randomly rolled amongst all the items available for a tier",
     "Each tier is now separated into multiple pools of Artifacts, and 1 Artifact is chosen per pool",
     "All options for every tier are now decided at the beginning of the game"):
    ("Each tier is now separated into multiple pools of Artifacts and 1 Artifact is chosen per pool, instead of a "
     "random roll amongst all the tier's items; all options for every tier are decided at the beginning of the game",
     "REWORK"),
}
_EXTRA_RE = re.compile(r', extra=(.*)\)\)\s*$')


def _postprocess_one_sentence_blocks(lines):
    out, i = list(lines), 0
    while i < len(out):
        texts, k = [], i
        while k < len(out) and _ROW_TEXT_RE.match(out[k]) and out[k].lstrip().startswith("W(li(\""):
            texts.append(_ROW_TEXT_RE.match(out[k]).group(1))
            k += 1
        found = _ONE_SENTENCE.get(tuple(texts))
        if not found:
            i = max(k, i + 1)
            continue
        sentence, tag = found
        extras = [m.group(1) for m in (_EXTRA_RE.search(out[j]) for j in range(i, k)) if m]
        extra = " + ".join(extras)
        ind = re.match(r"^\s*", out[i]).group(0)
        out[i:k] = [f'{ind}W(li("{sentence}", t("{tag}"){", extra=" + extra if extra else ""}))']
        i += 1
    return out


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
    shown = re.sub(r"^[^']+'s ", "", name)          # "Swashbuckle": the icon says whose (owner 2026-11-20)
    return f'mech_example("{name}") + " {shown}"'


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


def _adds_up_rule():
    """(formula, its example) of "An attack with its own potency" from the Item Potency page's rules
    (data/rules/item_potency_abilities.json), or None."""
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "rules", "item_potency_abilities.json")
    with open(path, encoding="utf-8") as f:
        rules = json.load(f).get("rules", [])
    for _title, formula, (a, b, what) in rules:
        if formula.startswith("Own"):
            return formula, f" ({what}: {a} &rarr; {b})"     # never a literal arrow in content (hygiene test)
    return None


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
    # the defaults first (any hero, an illusion), then the attacks with their own potency, then the bonuses (owner
    # 2026-11-20: "Any Hero и Standard Illusion пусть идут сначала, потом уже Swashbuckle / Evolved")
    rows = [(default, '"Any Hero"', _fmt(base * default / 100))]
    ill = next((int(m.group(1)) for m in map(_ILLUSION_RE.search, block) if m), None)
    if ill is not None:
        rows.append((ill, '"Standard Illusion"', _fmt(base * ill / 100)))
    for e in sorted(examples, key=lambda e: bool(e.group("plus"))):   # own potency before a bonus
        pct = default + int(e.group("pct")) if e.group("plus") else int(e.group("pct"))  # "+20%" on top of default
        rows.append((pct, _example_label(e.group("who")), e.group("val")))
    top = max(p for p, _w, _v in rows)
    cells = ", ".join(f'[{who}, {_potency_cell(p, top)}, "{val}"]' for p, who, val in rows)
    # the head names the item alone, no icon, no link: the table is about the attack (owner 2026-11-20)
    table = f'mech_table(["Attack", "Item Potency", "{item} armor reduction"], [{cells}], cls="mech-grid")'
    # Valve's "(excluding Skull Basher and a few other items)": all of them, a table of items and neutral items under
    # it (owner 2026-11-20: "указать отдельной строкой", "в столбце … items и neutral items"); then how the potencies
    # add up, as the Item Potency page says it
    excluded = _illusion_excluded(version) if version else []
    if excluded:
        table += f' + illusion_excluded_table({[tuple(x) for x in excluded]!r})'
    rule = _adds_up_rule()
    if rule:
        # the formula alone, no worked example after it (owner 2026-11-20: "(Swashbuckle with Evolved: 60 → 72) убрать")
        table += f' + mech_table(["How Item Potency adds up"], [mech_formula({rule[0]!r})])'
    s = _STORY_EXAMPLE_RE.sub("", out[story])
    s = _STORY_FILLER_RE.sub(")", s)
    if excluded:                                 # the table's last line names them all
        s = _EXCLUDING_RE.sub("", s)
    if "table=" in s:
        return out
    out[story] = re.sub(r"\)\)\s*$", f", table={table}))", s.rstrip())
    return out
