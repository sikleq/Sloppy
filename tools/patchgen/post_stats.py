"""Passes over the scaffold's lines: Aghanim merges, per-level pills, stat cards, cost, level-1 damage."""
import re

from .entities import _AGHS_LINE_RE
from .lines import _ENTITY_START_RE, _PROP_CHANGE_RE, _py_repr
from .names import _py_str  # noqa: F401  (post_late, post_tables import it from here)


def _postprocess_aghs_merge(lines):
    """Collapse the v2-emitted aghs upgrade row +its inline-note description
    into a single canonical "Aghanim's X: <description>" li with the NEW
    tag (per memory rule sloppy_aghs_upgrade_merge). The walker has
    already folded the indent N+1 description into the parent's
    inline_note, so the merge is a one-line text rewrite.
    """
    out = []
    for line in lines:
        m = _AGHS_LINE_RE.match(line)
        if m:
            kind, desc = m.group(1), m.group(2)
            out.append(f'W(li("Aghanim\'s {kind}: {desc}", t("NEW")))')
        else:
            out.append(line)
    return out


_PER_LEVEL_FORMULA_RE = re.compile(
    # "per level", "per level up" AND "per <Hero> level (up)" — Valve often
    # interpolates the hero name ("4% per Enchantress level"), which the old
    # bare "per level" pattern silently missed (7.40 Rabble-Rouser bug).
    r'(?P<base>\d+(?:\.\d+)?)(?P<pct>%?)\s*\+\s*(?P<inc>\d+(?:\.\d+)?)\2'
    # ... and a step every N levels: "10% + 10% per 15 hero levels" (7.42 Riki's Backstab, owner 2026-11-20:
    # "генератор упустил и не показывает formula table")
    r"\s+per(?:\s+(?P<every>\d+))?(?:\s+[A-Z][\w'-]*|\s+hero)?\s+levels?(?: up)?\b"
)


def _level_fn(m):
    """The lambda's body of a matched formula: base + inc per level, or per a step of N levels."""
    every = m.group("every")
    step = f"(L // {every})" if every else "L"
    return f"{m.group('base')} + {m.group('inc')}*{step}"

# "X changed from <formula> to <formula>" — a DIFF of two per-level formulas
# must become li_formula(...) (old vs new table), not a scale_pill around one
# of them. Plain li lines only (no extra=), single t(...) tag.
_FORMULA_DIFF_LINE_RE = re.compile(
    r'^W\(li\("(?P<prefix>[^"]+?) from (?P<old>[^"]+?) to (?P<new>[^"]+?)",\s*'
    r't\("(?:REWORK|MISC|BUFF|NERF)"\)\)\)$'
)
# … and with Valve's "?" behind it ("From 15-36.75% to 11-40%"), which goes under the table as inline_note_text
_FORMULA_DIFF_NOTE_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<prefix>[^"]+?) from (?P<old>[^"]+?) to (?P<new>[^"]+?)",\s*'
    r't\("(?:REWORK|MISC|BUFF|NERF)"\)(?:, extra=inline_note\((?P<note>"(?:[^"\\]|\\.)*")\))?\)\)$'
)
# one side of such a row, whole: "29.5% + 0.5% per hero level", "14.25 + 0.75% per level", "51% - 1% per level",
# "215s - 5s per level", "0.5% per level"
_SIDE_FORMULA_RE = re.compile(
    r"^(?:(?P<base>\d+(?:\.\d+)?)(?P<u1>%|s)?\s*(?P<sign>[+-])\s*)?(?P<inc>\d+(?:\.\d+)?)(?P<u2>%|s)?"
    r"\s+per(?:\s+(?:hero|[A-Z][\w'-]*))?\s+level(?: up)?$")


_SIDE_STEP_RE = re.compile(r"^(?P<base>\d+(?:\.\d+)?)(?P<u>%|s)?\s*\+\s*(?P<inc>\d+(?:\.\d+)?)(?P=u)?\s+per\s+"
                           r"(?P<n>\d+)\s+(?:hero\s+)?levels$")
_SIDE_FLAT_RE = re.compile(r"^(?P<v>\d+(?:\.\d+)?)(?P<u>%|s)?\s+at all times$")


def _side_formula(text):
    """(the lambda's body over L, the unit "%" / "s" / "") of one side of a per-level row, or None. Also "A + B per N
    levels" (a step every N levels) and "N at all times" (7.42 Shadow Shaman Fowl Play: "1 + 1 per 5 levels to 3 at
    all times", "5% + 5% per 5 levels to 5% + 1% per level" — made by hand first)."""
    s = _SIDE_STEP_RE.match(text.strip())
    if s:
        return f'{s.group("base")} + {s.group("inc")} * (L // {s.group("n")})', s.group("u") or ""
    f = _SIDE_FLAT_RE.match(text.strip())
    if f:
        return f.group("v"), f.group("u") or ""
    m = _SIDE_FORMULA_RE.match(text.strip())
    if not m:
        return None
    body = f'{m.group("inc")}*L' if m.group("base") is None else f'{m.group("base")} {m.group("sign")} {m.group("inc")}*L'
    return body, m.group("u1") or m.group("u2") or ""


def _formula_diff_row(line):
    """"X from <formula> to <formula>" with both sides per-level formulas → the li_formula line, else None. Reads the
    forms the first rule (_PER_LEVEL_FORMULA_RE: "A + B per level" on both sides, no "?") did not — 7.42 proofread
    2026-11-18: "per hero level" with a "?" (Abaddon, Broodmother), a formula that falls with level (Jakiro "51% - 1%
    per level", Marci "215s - 5s per level"), a "%" on one number only (Hoodwink) and a side with no base (Death
    Prophet "0.5% per level") all stayed plain rows or a pill round one side. A cost / cooldown / penalty row
    (_is_lower_better) gets l=True, so the tag follows the reader's gain."""
    from .tags import _is_lower_better
    m = _FORMULA_DIFF_NOTE_RE.match(line)
    if not m:
        return None
    old, new = _side_formula(m.group("old")), _side_formula(m.group("new"))
    if not old or not new:
        return None
    unit = old[1] or new[1]
    fmt = f', value_fmt="{{:g}}{unit}"' if unit else ', value_fmt="{:g}"'
    lower = ", l=True" if _is_lower_better(m.group("prefix")) else ""
    note = f', inline_note_text={m.group("note")}' if m.group("note") else ""
    return (f'{m.group("ind")}W(li_formula("{m.group("prefix")}", "{m.group("old")}", "{m.group("new")}", '
            f'lambda L: {old[0]}, lambda L: {new[0]}{lower}{fmt}{note}))')


def _postprocess_scale_pill(lines):
    """Detect "A% + B% per level" / "A + B per level up" formula patterns
    in W(li(...)) text and emit a scale_pill(...) wrapping. The trigger
    is splice-injected into the li text and the table is attached as
    extra= (or merged into the existing inline_note as a sibling).

    Each match gets a unique module-scoped variable in the generated
    source so the trigger and table share the same _formula_id_counter
    increment (calling scale_pill() twice would mint two ids and break
    the trigger→table linkage).
    """
    out = []
    counter = 0
    for line in lines:
        if not line.startswith('W(li("'):
            out.append(line)
            continue
        whole = _formula_diff_row(line)
        if whole:
            out.append(whole)
            continue
        m = _PER_LEVEL_FORMULA_RE.search(line)
        if not m:
            out.append(line)
            continue
        # TWO formulas in a "changed from X to Y" line → emit li_formula
        # (old/new diff table), NOT a scale_pill around just one of them.
        diff = _FORMULA_DIFF_LINE_RE.match(line)
        if diff:
            mo = _PER_LEVEL_FORMULA_RE.search(diff.group('old'))
            mn = _PER_LEVEL_FORMULA_RE.search(diff.group('new'))
            if mo and mn:
                fmt = '"{:g}%"' if mo.group('pct') else '"{:g}"'
                out.append(
                    f'W(li_formula("{diff.group("prefix")}", '
                    f'"{diff.group("old")}", "{diff.group("new")}", '
                    f'lambda L: {_level_fn(mo)}, '
                    f'lambda L: {_level_fn(mn)}, '
                    f'value_fmt={fmt}))'
                )
                continue
        formula_text = m.group(0)
        # Linear formula L → base + inc * L (per memory rule
        # sloppy_per_level_formula). Build a string lambda that survives
        # round-trip into emitted source code.
        counter += 1
        var = f'_pill{counter}'
        out.append(
            # No levels= override: the FULL default grid (L1-15, 20, 25, 30)
            # is the site standard for formula tables. Only abilities that
            # scale every X>1 levels get a custom step-X grid (manual).
            f'{var} = scale_pill('
            f'"{formula_text}", '
            f'lambda L: {_level_fn(m)})'
        )
        # Replace the formula substring inside the li text with the
        # trigger HTML (formed by an f-string concatenation at runtime).
        # The simplest patch: split the original li at the formula match
        # and rebuild with `f"...{var[0]}..."`.
        replaced = (line[:m.start()] + '" + ' + var + '[0] + "' + line[m.end():])
        # If the line already has extra=inline_note(...), we keep that
        # and ALSO append the formula table via a second extra; but li()
        # only accepts a single extra. Cheapest valid output: concatenate
        # the table into a wrapping <span>:
        if 'extra=inline_note(' in replaced:
            # Wrap existing inline_note with table concatenation.
            replaced = re.sub(
                r'extra=inline_note\("(.+?)"\)',
                lambda mm: f'extra=inline_note("{mm.group(1)}") + {var}[1]',
                replaced, count=1,
            )
        else:
            replaced = re.sub(r'\)\)$', f', extra={var}[1]))', replaced, count=1)
        out.append(replaced)
    return out


_REWORK_TRIGGERS = (
    'Innate ability reworked',
    'Ability reworked',
    'Reworked into',          # "Reworked into a basic ability" (Spectre Shadow Step)
)

# A brand-new / introduced ability — needs an ability_change(..., tag="new")
# card whose OLD pane is the ability it replaces (lifted from prior patchnotes).
_NEW_ABILITY_TRIGGERS = (
    'New innate ability',
    'New basic ability',
    'New ability',
    'New Point Targeted',     # "New Point Targeted basic ability"
)


# Stat-grant patterns inside item ability_notes — detected per-item and
# collapsed into properties_change(old=[...], new=[...]) after the
# item_header. Each tuple: (regex, kind, builder).
#   kind="add"     → ("NEW", "+stat") in new column only
#   kind="remove"  → ("DEL", "+stat") in old column only
#   kind="change"  → ("BUFF"/"NERF", "+old stat") in old + ("", "+new stat", b(a,b)) in new


_PROP_ADD_PREFIX_RE = re.compile(
    r'^Now also (?:provides?|grants?|gives?|deals?|fires?)\s+'
)
_PROP_DEL_PREFIX_RE = re.compile(
    r'^No longer (?:provides?|grants?|gives?)\s+'
)
# Match one "+value stat" token. Stat name continues until next comma/and/end.
_STAT_GRANT_RE = re.compile(
    r'\+([\d./]+%?\s+[A-Z][a-zA-Z\'/ ]+?)(?=\s*(?:,|\sand\s|$))'
)


_PROP_INSTEAD_RE = re.compile(r'^Now (?:provides?|grants?|gives?)\s+(\+.+?)\s+instead of\s+(\+.+)$')
_PROP_PROVIDES_RE = re.compile(r'^Provides\s+(\+.+)$')
_PROP_NOW_PROVIDES_RE = re.compile(r'^Now (?:provides?|grants?|gives?)\s+(?=\+)')


def _parse_stat_grants(text):
    """Split "+X Stat, +Y Stat, and +Z Stat" into ["+X Stat","+Y Stat","+Z Stat"]."""
    return [f'+{m.group(1).strip().rstrip(",.").strip()}'
            for m in _STAT_GRANT_RE.finditer(text)]


# Numbers of an item's ability, not item stats — never folded into properties_change cards.
_ABILITY_NUMBER_RE = re.compile(r'\b(?:mana ?cost|cooldown|cast (?:point|range)|duration|radius)\b', re.I)
# The whole stat name must be a real item stat ("Damage", "Mana Regen", "Spell Lifesteal"…).
# "Empower Spell damage" / "Empower Spell movement Slow" (Khanda 7.38) are the active's numbers → rows.
_ITEM_STAT_NAME_RE = re.compile(
    r'^(?:bonus\s+)?(?:all attributes|strength|agility|intelligence|health|max health|mana|max mana|'
    r'health regen(?:eration)?|mana regen(?:eration)?|health restoration|mana regen(?:eration)? amplification|'
    r'armor|magic(?:al)? resistance|damage|attack damage|attack speed|movement speed|move speed|evasion|'
    r'spell amp(?:lification)?|lifesteal|spell lifesteal|(?:spell )?lifesteal amplification|cast range|'
    r'attack range|status resistance|slow resistance|aoe bonus|cooldown reduction|'
    # Vambrace (7.37): its attribute bonuses and the one each chosen attribute gives
    r'main attribute|other attributes|(?:strength|agility|intelligence) (?:magic resistance|attack speed|spell amp))'
    r'(?:\s+bonus)?$', re.I)


def _parse_number_or_list(s):
    """Convert "5", "5.5", "5/6/7", "5%" into a value passable to b()."""
    s = s.rstrip('%').strip()
    if '/' in s:
        parts = []
        for p in s.split('/'):
            try:
                parts.append(int(p) if '.' not in p else float(p))
            except ValueError:
                return None
        return parts
    try:
        return int(s) if '.' not in s else float(s)
    except ValueError:
        return None


def _block_lines(lines, i):
    """The lines of the item block that starts after lines[i - 1] (its header), up to the next entity header."""
    j = i
    while j < len(lines) and not re.match(r'\s*W\((?:item_header|hero_header|section|plain_header|unit_header|enchant_header)\(',
                                          lines[j]):
        j += 1
    return lines[i:j]


_PROP_SPLIT_RE = re.compile(
    r'^(?P<stat>[A-Z][\w ]+?) bonus changed from \+(?P<old>\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)(?: for (?P<oldw>[\w/ ]+?))?'
    r' to \+(?P<new>\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)(?: for (?P<neww>[\w/ ]+?))?$')


def _split_side(value, who):
    """"18/12" for "melee/ranged heroes" -> ("+18/12", " (Melee/Ranged)", [18, 12]); "Ranged/Melee" turned to the
    Melee/Ranged order; one value -> ("+15", "", 15)."""
    parts = [float(x) if "." in x else int(x) for x in value.split("/")]
    if len(parts) == 1:
        return f"+{value}", "", parts[0]
    if who and re.match(r'ranged/melee', who, re.I):
        parts = parts[::-1]
    return "+" + "/".join(str(p) for p in parts), " (Melee/Ranged)", parts


def _row_texts(block):
    return [m.group(1) for m in (re.match(r'^\s*W\(li\("(.+?)",', ln) for ln in block) if m]


def _split_stat_rows(text):
    """"Damage bonus changed from +18/12 for melee/ranged heroes to +15 for any wearer", "Movement Speed bonus changed
    from +50 to +45/55 for Ranged/Melee Heroes" (7.42 Phase Boots) -> (old card row, new card row), or None (owner
    2026-11-19: "не лучше ли показать вместо строк карточками old/new?")."""
    m = _PROP_SPLIT_RE.match(text)
    if not m or "/" not in m.group("old") + m.group("new"):
        return None
    ov, osuf, on = _split_side(m.group("old"), m.group("oldw"))
    nv, nsuf, nn = _split_side(m.group("new"), m.group("neww"))
    stat = m.group("stat").strip()
    return ("REWORK", f"{ov} {stat}{osuf}"), (None, f"{nv} {stat}{nsuf}", (on, nn))


def _swaps_stats(block):
    """The block's rows add a stat the item did not have and take one it had ("Now provides +50/100 Health" + "No
    longer provides +3/6 Damage") — its stats card, though its build did not change."""
    texts = [m.group(1) for m in (re.match(r'^\s*W\(li\("(.+?)",', ln) for ln in _split_stat_sentences(block)) if m]
    adds = any((m := (_PROP_ADD_PREFIX_RE.match(t) or _PROP_NOW_PROVIDES_RE.match(t))) and _parse_stat_grants(t[m.end():])
               for t in texts)
    dels = any((m := _PROP_DEL_PREFIX_RE.match(t)) and _parse_stat_grants(t[m.end():]) for t in texts)
    return adds and dels


_STAT_SENTENCE_RE = re.compile(r'^(\s*W\(li\(")(.+?)\.\s+((?:Now|No longer) (?:also )?(?:provides?|grants?|gives?)\s.+?)'
                               r'(",\s*[bt]\(.*)$')


def _split_stat_sentences(rows):
    """"No longer provides +6 All Attributes. Now provides +375 Health" (7.37 Spirit Vessel): two stat rows, each with
    the row's tag — the whole line was read as two stats gone (owner 2026-10-30: "не хватает других ха-к")."""
    out = []
    for ln in rows:
        m = _STAT_SENTENCE_RE.match(ln)
        if m and re.match(r'(?:Now|No longer) (?:also )?(?:provides?|grants?|gives?)\s', m.group(2)):
            out += [f'{m.group(1)}{m.group(2)}{m.group(4)}', f'{m.group(1)}{m.group(3)}{m.group(4)}']
        else:
            out.append(ln)
    return out


def _new_stat_that_was_there(item_name, version, old_rows, new_rows):
    """A "new" stat the item had before with another number (7.37 Spirit Vessel "Now provides +375 Health": it had +125)
    is a change — "+125 Health" → "+375 Health" with its %, from the game files of both patches."""
    if not version or not new_rows:
        return old_rows, new_rows
    from patch.cards_item_stats import _STAT_LINE, _stat_text, item_stats_pair
    pair = item_stats_pair(item_name, version)
    if not pair:
        return old_rows, new_rows
    before = pair[0]
    olds, news, changed = list(old_rows), [], []
    for row in new_rows:
        m = re.match(r'^\+([\d.]+)%?\s+(.+)$', row[1]) if len(row) == 2 and row[0] == 'NEW' else None
        key = next((k for k, spec in _STAT_LINE.items() if m and spec[0].lower() == m.group(2).strip().lower()), None)
        was = before.get(key) if key else None
        now = float(m.group(1)) if m else None
        if was and now is not None and abs(was - now) > 1e-9:
            num = lambda x: int(x) if x == int(x) else x
            changed.append((('BUFF' if now > was else 'NERF', _stat_text(key, was)), (None, row[1], (num(was), num(now)))))
        else:
            news.append(row)
    return [o for o, _n in changed] + olds, [n for _o, n in changed] + news


def _prop_key(stat_text):
    """'+30% Evasion' -> 'evasion' (the stat's name, as tests/test_properties_order.py reads it)."""
    t = re.sub(r"<[^>]+>", "", stat_text).strip()
    t = re.sub(r"^[+\-−x×]?[\d.,/%\s]+%?\s*", "", t)
    return re.sub(r"\s*\(.*?\)\s*$", "", t).lower().strip()


def _shared_props_first(old_rows, new_rows):
    """Stats on BOTH sides first, in the old side's order, then each side's own (7.42 Butterfly put the new
    +30 Attack Speed above the shared Evasion: the two Evasion lines did not face each other)."""
    old_keys = [_prop_key(r[1]) for r in old_rows]
    new_keys = [_prop_key(r[1]) for r in new_rows]
    shared = [k for k in old_keys if k in new_keys]
    def order(rows, keys):
        first = [rows[keys.index(k)] for k in shared]
        rest = [r for r, k in zip(rows, keys) if k not in shared]
        return first + rest
    return order(old_rows, old_keys), order(new_rows, new_keys)


def _postprocess_properties_change(lines, with_abilities=False, version=None):
    """Collapse stat-grant note patterns inside item blocks into a single
    properties_change(old=[...], new=[...]) call placed right after the
    item_header. The original li rows that fed the diff are removed from
    the regular ul.

    Triggered when an item_header(name, changed=True) is followed by note
    lines matching add/remove/change stat-grant patterns. Items without
    properties-relevant rows pass through untouched.

    Returns the rewritten line list. Does NOT touch hero/general blocks.
    """
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Any item header except a new / returning item (owner 2026-09-27, Bloodstone 7.38: "No longer
        # provides +75 AoE radius" stayed a row because only changed=True items got the stats card)
        # (an item only moved to another neutral tier, "Now a Tier 3 Neutral Item", is no new item: its card too —
        # owner 2026-10-30, 7.37 Vambrace / Ogre Seal Totem "по аналогии с обычными предметами")
        m_hdr = re.match(r'W\(item_header\("([^"]+)"(?![^)]*new="(?:New|Returning)\b)[^)]*\)\)', line)
        if not m_hdr:
            out.append(line)
            i += 1
            continue
        tier_move = 'new="Now a Tier' in line

        item_name = m_hdr.group(1)
        out.append(line)
        i += 1
        # Owner 2026-09-28 (Sange and Yasha: one changed stat drawn as a whole card): the stats card only
        # comes with a changed BUILD — an auto_components_change right under the header. Otherwise the stat
        # rows stay plain rows ("Status Resistance bonus decreased from +25% to +20%").
        # ... or with an abilities card (owner 2026-10-17, Refresher Orb 7.41: "no stats card"): a block of cards
        # shows its stats in one too. That card comes later (_postprocess_item_ability_cards), so a second pass
        # (with_abilities) takes the blocks that have one and no stats card yet.
        if with_abilities:
            block = _block_lines(lines, i)
            if (not any(ln.lstrip().startswith('W(item_abilities_change(') for ln in block)
                    or any(ln.lstrip().startswith(('W(properties_change(', 'W(auto_components_change('))
                           for ln in block)):
                continue
        else:
            if i < len(lines) and lines[i].startswith('W(auto_components_change('):
                out.append(lines[i])
                i += 1
            elif not (_swaps_stats(_block_lines(lines, i)) or tier_move   # a tier move counts as a build change
                      or any(_split_stat_rows(t) for t in _row_texts(_block_lines(lines, i)))):
                continue                                  # ... and a stat split by melee / ranged (2026-11-19)
            # … or the item's stats themselves change in kind: one added, one gone (owner 2026-10-30, 7.37 Bracer
            # "Now provides +50/100 Health" / "No longer provides +3/6 Damage": "тут разве не карточкой надо?")

        # Collect li rows of this item block. The block ends at the next
        # W(item_header(...)) / W(hero_header(...)) / section header.
        old_rows = []
        new_rows = []
        kept_lines = []
        needs_old = False
        block_end = i
        while block_end < len(lines):
            # a header line may come with a leading blank line in it ("\nW(plain_header(\"Artifact Pools\"…") — read
            # without it, or the block runs on into the enchantments and their stats land in the item's card (owner
            # 2026-11-19, 7.42 Witchbane: "в игре совсем другое" — 18 enchantment stats in a neutral item's card)
            ln = lines[block_end].lstrip()
            if ln.startswith(('W(item_header(', 'W(hero_header(', 'W(section(', 'W(plain_header(', 'W(unit_header(',
                              'W(enchant_header(')):
                break
            block_end += 1

        for ln in _split_stat_sentences(lines[i:block_end]):
            m_li = re.match(r'^W\(li\("(.+?)",\s*[bt]\(.*$', ln)
            if not m_li:
                kept_lines.append(ln)
                continue
            txt = m_li.group(1)
            split = _split_stat_rows(txt)
            if split:
                old_rows.append(split[0])
                new_rows.append(split[1])
                continue
            # Try add pattern — supports comma-separated multi-stat:
            #   "Now also provides +200 Health, +350 Mana, and +60 Cast Range"
            ma = _PROP_ADD_PREFIX_RE.match(txt)
            if ma:
                grants = _parse_stat_grants(txt[ma.end():])
                if grants:
                    for stat in grants:
                        new_rows.append(('NEW', stat))
                    continue
            # "Now provides +8 Mana Regen instead of +50 Damage" (Khanda 7.38): old stat -> new stat
            mi = _PROP_INSTEAD_RE.match(txt)
            if mi:
                news, olds = _parse_stat_grants(mi.group(1)), _parse_stat_grants(mi.group(2))
                if news and olds:
                    new_rows.extend(('NEW', st) for st in news)
                    old_rows.extend(('DEL', st) for st in olds)
                    continue
            # "Now provides +50/100 Health" (7.37 Bracer, without "also"): a stat the item did not have
            mn = _PROP_NOW_PROVIDES_RE.match(txt)
            if mn:
                grants = _parse_stat_grants(txt[mn.end():])
                if grants:
                    new_rows.extend(('NEW', st) for st in grants)
                    continue
            # a reworked item's own stat list "Provides +35 Damage and +16% Spell Lifesteal"
            # (Revenant's Brooch 7.38): the new side; the old side must come from the previous
            # patch's tooltips (patch/loc_history.py, the game-files store) — flagged with a TODO comment
            mp = _PROP_PROVIDES_RE.match(txt)
            if mp:
                grants = _parse_stat_grants(mp.group(1))
                if grants:
                    new_rows.extend(('NEW', st) for st in grants)
                    needs_old = True
                    continue
            # Try remove
            mr = _PROP_DEL_PREFIX_RE.match(txt)
            if mr:
                grants = _parse_stat_grants(txt[mr.end():])
                if grants:
                    for stat in grants:
                        old_rows.append(('DEL', stat))
                    continue
            # Try change "X increased/decreased from A to B"
            mc = _PROP_CHANGE_RE.match(txt)
            if mc and (_ABILITY_NUMBER_RE.search(mc.group('stat'))
                       or not _ITEM_STAT_NAME_RE.match(mc.group('stat').strip())):
                # "Eternal Chains mana cost decreased from 200 to 100" is an ACTIVE's number,
                # not a stat of the item: it stays a plain row (owner, 2026-09-25), never a card line
                mc = None
            if mc:
                stat = mc.group('stat').replace(' bonus', '').strip()
                old_v = mc.group('old')
                new_v = mc.group('new')
                verb = mc.group('verb')
                old_n = _parse_number_or_list(old_v)
                new_n = _parse_number_or_list(new_v)
                tag = 'BUFF' if verb == 'increased' else ('NERF' if verb == 'decreased' else 'REWORK')
                if old_n is not None and new_n is not None:
                    old_rows.append((tag, f'+{old_v} {stat}'))
                    new_rows.append((None, f'+{new_v} {stat}', (old_n, new_n)))
                    continue
            kept_lines.append(ln)

        old_rows, new_rows = _new_stat_that_was_there(item_name, version, old_rows, new_rows)
        old_rows, new_rows = _shared_props_first(old_rows, new_rows)
        if old_rows or new_rows:
            old_repr = ', '.join(
                f'("{t}", "{s}")' for (t, s) in old_rows
            ) or ''
            def _fmt_new(row):
                if len(row) == 3:
                    tag, stat, (a, b) = row
                    a_s = _py_repr(a)
                    b_s = _py_repr(b)
                    tag_s = f'"{tag}"' if tag else '""'
                    return f'({tag_s}, "{stat}", b({a_s}, {b_s}))'
                tag, stat = row
                return f'("{tag}", "{stat}")'
            new_repr = ', '.join(_fmt_new(r) for r in new_rows) or ''
            if needs_old and not old_rows:
                out.append(f'    # TODO {item_name}: old bonus stats — take them from the previous patch\'s '
                           f'tooltips (patch/loc_history.py), never invent them')
            out.append(
                f'W(properties_change(old=[{old_repr}], new=[{new_repr}]))'
            )
        out.extend(kept_lines)
        i = block_end
    return out


_ITEM_PRICE_LI_RE = re.compile(r'^\s*W\(li\(\s*"(?:Recipe [Cc]ost|Total [Cc]ost|No longer requires an? \d+ gold recipe)')


def _postprocess_cost_components(lines, version):
    """Owner 2026-09-27 ("if the item has other changes, put its price into the cards"): an item whose
    recipe / total cost changed AND that has other changes gets the components card
    (auto_components_change) even when only the recipe price moved; the card shows the recipe chip and
    the total old -> new with its %, and the cost row under it is hidden (elements._cost_covered). An
    item whose only change is its price keeps the plain row."""
    out, i = [], 0
    while i < len(lines):
        m_hdr = re.match(r'^(\s*)W\(item_header\("([^"]+)"(?![^)]*new=)[^)]*\)\)', lines[i])
        if not m_hdr:
            out.append(lines[i])
            i += 1
            continue
        end = i + 1
        while end < len(lines) and not _ENTITY_START_RE.match(lines[end]):
            end += 1
        block = lines[i:end]
        has_card = any('auto_components_change(' in ln for ln in block)
        cost_rows = [ln for ln in block if _ITEM_PRICE_LI_RE.match(ln)]
        others = [ln for ln in block[1:] if re.match(r'^\s*W\((?:li|properties_change|item_abilities_change)\(', ln)
                  and not _ITEM_PRICE_LI_RE.match(ln)]
        if cost_rows and others and not has_card:
            block.insert(1, f'{m_hdr.group(1)}W(auto_components_change("{m_hdr.group(2)}", "{version}"))')
        out.extend(block)
        i = end
    return out


# ---- "Damage at level 1" goes into the (?) of the row it follows from ----
# The owner 2026-10-04, shown both forms side by side (Magnus 7.41 = its own row, Broodmother 7.41b = in the "?"):
# "сделай с ?". A "Damage at level 1 …" line is the consequence of a base attribute / base damage change, so it
# becomes a note on that row: the last such row before it in its list, else the first one after it (Invoker 7.39
# lists it first). Kept as rows: heroes with a hero_stat_card (those rows are hidden and feed the card), a line Valve
# worded wrongly (wrong-word span + its correction, the tag's red glow on the page, must stay in sight), and a list with no base attribute /
# base damage row (then the line is the change itself). Weights do not move: patch/elements.li scores a folded
# note exactly like the row it was (_score_folded_damage).
_DMG_FOLD_PARENT_RE = re.compile(r"^(?:Base (?:damage|strength|agility|intelligence)"
                                 r"|(?:min(?:imum)?|max(?:imum)?) base damage)\b", re.I)
_DMG_FOLD_ROW_RE = re.compile(r"^Damage at level 1 ")


def _w_inner(st, name=None):
    """`W(name(...))` statement -> the inner Call node (any name when name is None), else None."""
    import ast as _ast
    if not (isinstance(st, _ast.Expr) and isinstance(st.value, _ast.Call) and isinstance(st.value.func, _ast.Name)
            and st.value.func.id == "W" and st.value.args and isinstance(st.value.args[0], _ast.Call)
            and isinstance(st.value.args[0].func, _ast.Name)):
        return None
    inner = st.value.args[0]
    return inner if name is None or inner.func.id == name else None


def _dmg_fold_plan(body):
    """[(L1 statement, parent li Call, its li Call)] for one statement list."""
    import ast as _ast
    plan, card, ul = [], False, None
    for i, st in enumerate(body):
        inner = _w_inner(st)
        name = inner.func.id if inner is not None else ""
        if name in ("hero_header", "item_header", "unit_header", "plain_header"):
            card = False
            for st2 in body[i + 1:]:
                n2 = _w_inner(st2)
                if n2 is not None and n2.func.id in ("hero_header", "item_header", "unit_header", "plain_header"):
                    break
                if n2 is not None and n2.func.id == "hero_stat_card":
                    card = True
                    break
        elif name == "ul_open":
            ul = []
        elif name == "ul_close" and ul is not None:
            for j, (st_l, call) in enumerate(ul):
                a0 = call.args[0] if call.args else None
                if not (isinstance(a0, _ast.Constant) and isinstance(a0.value, str) and _DMG_FOLD_ROW_RE.match(a0.value)):
                    continue
                if card or "wrong-word" in a0.value or len(call.args) != 2:
                    continue
                if any(k.arg != "extra" for k in call.keywords):
                    continue
                parents = [c for _, c in ul if c is not call and _dmg_fold_is_parent(c)]
                before = [c for _, c in ul[:j] if _dmg_fold_is_parent(c)]
                parent = before[-1] if before else (parents[0] if parents else None)
                if parent is not None:
                    plan.append((st_l, parent, call))
            ul = None
        elif name == "li" and ul is not None:
            ul.append((st, inner))
    return plan


def _dmg_fold_is_parent(call):
    import ast as _ast
    a0 = call.args[0] if call.args else None
    if isinstance(a0, _ast.Constant) and isinstance(a0.value, str):
        return bool(_DMG_FOLD_PARENT_RE.match(a0.value))
    return isinstance(a0, _ast.Call) and isinstance(a0.func, _ast.Name) and a0.func.id == "attr_change"



def fold_damage_l1_src(src):
    """Python source -> the same source with every foldable "Damage at level 1" row moved into its parent's (?).
    Works on generator output and on hand-edited content/p*.py (multi-line statements included)."""
    import ast as _ast
    tree = _ast.parse(src)
    plan = []
    for node in _ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list):
            plan.extend(_dmg_fold_plan(body))
    if not plan:
        return src
    lines = [ln.encode("utf-8") for ln in src.split("\n")]      # ast columns are utf-8 byte offsets

    def seg(n):
        if n.lineno == n.end_lineno:
            return lines[n.lineno - 1][n.col_offset:n.end_col_offset].decode("utf-8")
        parts = [lines[n.lineno - 1][n.col_offset:]] + lines[n.lineno:n.end_lineno - 1] + \
                [lines[n.end_lineno - 1][:n.end_col_offset]]
        return b"\n".join(parts).decode("utf-8")

    notes = {}                      # parent node id -> (parent Call, [note texts in page order])
    drops = []
    for st_l, parent, call in plan:
        text = call.args[0].value
        own = [k for k in call.keywords if k.arg == "extra"]
        if own:
            v = own[0].value
            if not (isinstance(v, _ast.Call) and getattr(v.func, "id", "") == "inline_note" and v.args
                    and isinstance(v.args[0], _ast.Constant)):
                continue                                         # an extra we cannot merge as text: keep the row
            text += "<br>" + v.args[0].value
        notes.setdefault(id(parent), (parent, []))[1].append(text)
        drops.append(st_l)

    edits = []                      # (lineno, col, end_lineno, end_col, replacement)
    for parent, texts in notes.values():
        note = "<br>".join(texts)
        ex = [k for k in parent.keywords if k.arg == "extra"]
        if not ex:
            # insert ", extra=inline_note(...)" before li(...)'s closing paren
            edits.append((parent.end_lineno, parent.end_col_offset - 1, parent.end_lineno, parent.end_col_offset - 1,
                          f", extra=inline_note({_py_str(note)})"))
            continue
        v = ex[0].value
        if isinstance(v, _ast.Call) and getattr(v.func, "id", "") == "inline_note" and v.args \
                and isinstance(v.args[0], _ast.Constant):
            new = f"inline_note({_py_str(note + '<br>' + v.args[0].value)})"
        elif isinstance(v, _ast.BinOp) and isinstance(v.right, _ast.Call) \
                and getattr(v.right.func, "id", "") == "inline_note" and v.right.args \
                and isinstance(v.right.args[0], _ast.Constant):
            new = f"{seg(v.left)} + inline_note({_py_str(note + '<br>' + v.right.args[0].value)})"
        else:
            new = f"{seg(v)} + inline_note({_py_str(note)})"
        edits.append((v.lineno, v.col_offset, v.end_lineno, v.end_col_offset, new))

    for st in drops:                # a dropped row must own its lines
        first, last = lines[st.lineno - 1], lines[st.end_lineno - 1]
        if first[:st.col_offset].strip() or last[st.end_col_offset:].strip():
            raise ValueError(f"line {st.lineno}: a Damage at level 1 row shares its line with other code")
    # edits and drops never overlap (different statements); applied bottom-up, the earlier positions stay valid
    ops = [(ln, col, "edit", (eln, ecol, rep)) for ln, col, eln, ecol, rep in edits] + \
          [(st.lineno, 0, "drop", st.end_lineno) for st in drops]
    for ln, col, kind, rest in sorted(ops, key=lambda o: (o[0], o[1]), reverse=True):
        if kind == "drop":
            del lines[ln - 1:rest]
            continue
        eln, ecol, rep = rest
        head, tail = lines[ln - 1][:col], lines[eln - 1][ecol:]
        lines[ln - 1:eln] = (head + rep.encode("utf-8") + tail).split(b"\n")
    out = b"\n".join(lines).decode("utf-8")
    _ast.parse(out)                 # never hand back broken code (raises SyntaxError)
    return out


def _postprocess_fold_damage_l1(lines):
    src = "\n".join(lines)
    try:
        return fold_damage_l1_src(src).split("\n")
    except (SyntaxError, ValueError) as e:
        print(f"  [warn] Damage at level 1 fold skipped: {e}")
        return lines
