"""A new summon's own abilities as cards of their own (owner 2026-11-19, 7.42 Beastmaster "Summon Ancient Thunderhide
вообще плохо сделано — куча строк misc тега"): Valve retells the summon and each ability of the unit it calls ("Slam:
Active. No Target …", "Thunderhide Drum: Passive. Aura …") in plain rows. The game files have every one of those
abilities: the unit's Ability1… in that patch's npc_units.txt, its text in the tooltips. So each named ability becomes a
"New ability." card under the summon's (ability_change(..., sub=True)), and the rows that only retell the game's text
are covered — hidden, still counted by the filters and the weights."""
import os
import re

from .common import _HERE

_NEW_ABILITY_RE = re.compile(r'^(\s*)W\(new_ability\("([^"]+)", "([a-z0-9_]+)", version="([^"]+)"\)\)\s*$')
_SUB_ROW_RE = re.compile(r'^\s*W\(li\("([A-Z][\w\' ]+?): (?:Active|Passive|Toggle|Aura)\b')
_PLAIN_MISC_RE = re.compile(r'^\s*W\(li\(".*", t\("MISC"\)(?:, extra=inline_note\("[^"]*"\))?(?:, covered=True)?\)\)\s*$')


def _unit_abilities(version):
    """{unit: [ability slugs]} from data/stats/<version>/npc_units.txt."""
    path = os.path.join(_HERE, "data", "stats", version, "npc_units.txt")
    if not os.path.exists(path):
        return {}
    out, unit = {}, None
    for ln in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r'^\t"(npc_[a-z0-9_]+)"\s*$', ln)
        if m:
            unit = m.group(1)
            continue
        a = re.match(r'^\t\t"Ability\d+"\s+"([a-z0-9_]+)"', ln)
        if unit and a:
            out.setdefault(unit, []).append(a.group(1))
    return out


def _sub_slugs(summon_name, version):
    """{shown name: slug} of the abilities of the unit the summon calls: a unit whose key holds the summon's last word
    ("Summon Ancient Thunderhide" -> npc_dota_beastmaster_thunderhide)."""
    from patch import loc_history
    word = summon_name.split()[-1].lower()
    units = {u: a for u, a in _unit_abilities(version).items() if word in u and "neutral" not in u}
    if len(units) != 1:
        return {}
    named = {}
    for slug in next(iter(units.values())):
        name = loc_history.tooltip(f"DOTA_Tooltip_ability_{slug}", version)
        if name:
            named[name.strip()] = slug
    return named


_CARD_END_RE = re.compile(r'^\s*W\((?:hero_header|item_header|unit_header|enchant_header|ability|new_ability|section|'
                          r'subgroup|plain_header|facet_header)\(')
_COVERED_MISC_RE = re.compile(r'^(.*?\bli\(".*?", )t\("MISC"\)(.*covered=True.*)$')


def _postprocess_covered_row_tags(lines):
    """A row hidden under a card takes the card's tag, not MISC (Fable audit 2026-11-19: 40 hidden rows of 7.42's new
    creeps and new abilities counted as MISC in the filters and the weights): under a new ability's card or a new
    unit's header — NEW; under a reworked ability's card — REWORK. A rename row stays MISC."""
    out, ctx = list(lines), None
    for i, ln in enumerate(out):
        s = ln.lstrip()
        if s.startswith("W(new_ability("):
            ctx = "NEW"
            continue
        if s.startswith("W(unit_header(") and re.search(r',\s*new=(?!False)', s):
            ctx = "NEW"
            continue
        if s.startswith("W(ability_change("):
            ctx = "PENDING"
        if ctx == "PENDING" or s.startswith("W(ability_change("):
            if 'tag="new"' in ln or "New ability." in ln or "New innate ability." in ln:
                ctx = "NEW"
            elif 'tag="rework"' in ln or "Ability reworked." in ln:
                ctx = "REWORK"
        if _CARD_END_RE.match(ln) and not s.startswith("W(ability_change("):
            ctx = None
            continue
        m = _COVERED_MISC_RE.match(ln)
        if m and ctx in ("NEW", "REWORK") and "renamed" not in ln.lower():
            out[i] = f'{m.group(1)}t("{ctx}"){m.group(2)}'
    return out


_ABIL_HDR_RE = re.compile(r'^(\s*)W\(ability\("([^"]+)", slug="([a-z0-9_]+)"(, innate=True)?\)\)\s*$')
_REWORKED_ROW_RE = re.compile(r'^\s*W\(li\("Ability Reworked", t\("REWORK"\)\)\)\s*$')
_AGHS_PARENT_RE = re.compile(r"^\s*W\(li\(\"(?:Aghanim's (?:Scepter|Shard) reworked|Now upgraded with Aghanim's "
                             r"(?:Scepter|Shard) instead of Aghanim's (?:Scepter|Shard))\", t\(\"REWORK\"\)")
_STAT_LINE_RE = re.compile(r"^[A-Z][A-Za-z' ]*: [\d./%sx-]+(?:[;.] [A-Z][A-Za-z' ]*: [\d./%sx-]+)*\.?$")
_MISC_ROW_RE = re.compile(r'^\s*W\(li\("((?:[^"\\]|\\.)*)", t\("MISC"\)(?:, extra=inline_note\("((?:[^"\\]|\\.)*)"\))?\)\)\s*$')


def _block_end(out, i):
    return next((k for k in range(i + 2, len(out)) if out[k].strip() == "W(ul_close())"), None)


def _postprocess_reworked_ability_cards(lines, version):
    """Valve's "Ability Reworked" and the new ability retold in MISC rows (Fable audit 2026-11-19, 7.42 Chen Zealot,
    Leshrac Nihilism, Nature's Prophet Curse of the Oldgrowth: 12 visible MISC rows) → the card old → new from the
    game's texts of both patches (game_ability_pair), as 7.42 Kobold Steal Weapon; the retelling rows hidden under it,
    a row with a note of its own stays."""
    from patch import aghs_text
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version)
    out, i, n = list(lines), 0, 0
    while i < len(out):
        m = _ABIL_HDR_RE.match(out[i])
        end = _block_end(out, i) if m and i + 2 < len(out) and out[i + 1].strip() == "W(ul_open())" else None
        if not (end and _REWORKED_ROW_RE.match(out[i + 2]) and aghs_text.ability_text(m.group(3), prev)
                and aghs_text.ability_text(m.group(3), version)):
            i += 1
            continue
        ind, name, slug, innate = m.group(1), m.group(2), m.group(3), bool(m.group(4))
        rows = out[i + 2:end]
        # a row stays when its note says what the card can't: what stopped or stayed ("No longer applies Ethereal…",
        # "Martyrdom is unchanged"); a note of values the card lists anyway goes with its row
        says_more = lambda r: "extra=" in r and re.search(r"\bno longer\b|\bunchanged\b|\bstill\b", r, re.I)
        hidden = [r.strip()[2:-1] for r in rows if not says_more(r)]                    # W(li(..)) -> li(..)
        kept = [r for r in rows if says_more(r)]
        # a kept row that is only values ("Radius: 550; Duration: 4s", owner 2026-11-19 on Nihilism): the card lists
        # them, so it goes under the card and its notes become rows of their own, not a (?) under a stat line
        split = []
        for r in kept:
            sm = _MISC_ROW_RE.match(r)
            if sm and sm.group(2) and _STAT_LINE_RE.match(sm.group(1)):
                hidden.append(f'li("{sm.group(1)}", t("MISC"))')
                split += [f'{ind}W(li("{note.strip()}", t("REWORK")))' for note in sm.group(2).split("<br>") if note.strip()]
            else:
                split.append(r)
        kept = split
        hidden = [re.sub(r"\)\s*$", ", covered=True)", r.replace('t("MISC")', 't("REWORK")')) for r in hidden]
        n += 1
        v = f"_rw{n}"
        inn = ", innate=True" if innate else ""
        card = [f'{ind}{v}_old, {v}_new = game_ability_pair("{slug}", "{version}")',
                f'{ind}W(ability_change(',
                f'{ind}    old=dict(name="{name}", slug="{slug}"{inn}, desc={v}_old),',
                f'{ind}    new=dict(name="{name}", slug="{slug}"{inn}, desc={v}_new),',
                f'{ind}    summary="{"Innate reworked." if innate else "Ability reworked."}",',
                f'{ind}    tag="rework",',
                f'{ind}    rows_first=lambda: [{", ".join(hidden)}]))']
        tail = ([f"{ind}W(ul_open())"] + [re.sub(r't\("MISC"\)', 't("REWORK")', r) for r in kept]
                + [f"{ind}W(ul_close())"]) if kept else []
        out[i:end + 1] = card + tail
        i += len(card) + len(tail)
    return out


def _postprocess_aghs_rework_rows(lines):
    """"Aghanim's Scepter reworked" / "Now upgraded with Aghanim's Scepter instead of Aghanim's Shard" and the upgrade
    retold in MISC rows after it (Fable audit 2026-11-19, 7.42 Morphling Morph, Death Prophet Spirit Siphon) → one row,
    the upgrade in its (?) — the rule "суть реворка Aghanim не прятать и не разносить"."""
    out, i = list(lines), 0
    while i < len(out):
        if not _AGHS_PARENT_RE.match(out[i]):
            i += 1
            continue
        j, texts = i + 1, []
        while j < len(out) and out[j].lstrip().startswith("W(li("):
            mm = _MISC_ROW_RE.match(out[j])
            if mm:
                texts.append(mm.group(1) + (f"<br>{mm.group(2)}" if mm.group(2) else ""))
                del out[j]
                continue
            j += 1
        if texts and "extra=" not in out[i]:
            note = "<br>".join(texts)
            out[i] = re.sub(r'(t\("REWORK"\))\)\)\s*$', lambda mm: f'{mm.group(1)}, extra=inline_note("{note}")))', out[i])
        i += 1
    return out


_META_ROW_RE = re.compile(r'^\s*W\(li\("((?:Global )?Cast Range|Mana Cost|Cooldown|Cast Point)\b[^"]*"')


def _postprocess_card_tail_rows(lines):
    """A card's own meta line ("Global Cast Range. Mana Cost: 50. Cooldown: 30s …") that Valve wrote after the ability's
    description fell out of the card into a list of its own under it (Fable audit 2026-11-19, 7.42 Chaos Knight Ahead,
    Armageddon): into the card's rows_first, hidden, as its siblings."""
    out, i = list(lines), 0
    while i < len(out) - 3:
        if (out[i].rstrip().endswith("]))") and out[i + 1].strip() == "W(ul_open())"
                and _META_ROW_RE.match(out[i + 2]) and out[i + 3].strip() == "W(ul_close())"
                and any("rows_first=lambda: [" in out[k] for k in range(max(0, i - 12), i))):
            row = out[i + 2].strip()[2:-1]                       # W(li(...)) -> li(...)
            row = re.sub(r"\)\s*$", ", covered=True)", row) if "covered=True" not in row else row
            ind = re.match(r"\s*", out[i - 1]).group(0)
            out[i:i + 4] = [f"{ind}{row},", out[i]]
            i += 2
            continue
        i += 1
    return out


def _postprocess_summon_sub_cards(lines):
    out, i = list(lines), 0
    while i < len(out):
        m = _NEW_ABILITY_RE.match(out[i])
        if not m or i + 1 >= len(out) or out[i + 1].strip() != "W(ul_open())":
            i += 1
            continue
        ind, name, _slug, version = m.groups()
        end = next((k for k in range(i + 2, len(out)) if out[k].strip() == "W(ul_close())"), None)
        if end is None:
            break
        subs = _sub_slugs(name, version)
        found = [(k, _SUB_ROW_RE.match(out[k]).group(1)) for k in range(i + 2, end) if _SUB_ROW_RE.match(out[k])]
        found = [(k, n) for k, n in found if n in subs]
        if not found:
            i = end + 1
            continue
        for k in range(i + 2, end):          # the retold game text: hidden under the cards
            if _PLAIN_MISC_RE.match(out[k]) and "covered=True" not in out[k]:
                out[k] = re.sub(r"\)\)\s*$", ", covered=True))", out[k])
        cards = [f'{ind}W(ability_change(None, dict(name={n!r}, slug="{subs[n]}", '
                 f'desc=game_ability_desc("{subs[n]}", "{version}")), summary="New ability.", tag="new", sub=True))'
                 for _k, n in found]
        out[end + 1:end + 1] = cards
        i = end + 1 + len(cards)
    return out


# a summoning ability → the name the game shows for its unit and the icon of its look (the summon has no icon of its
# own; the Thunderhide is a big Thunderhide). Not Chen's Zealot: in 7.42 any unit of his is anointed, the innate's
# bonuses ("damage_bonus" 5% + 2%) are for all his creeps — a sheet of one "Zealot" would add them as flat numbers
_SUMMON_UNITS = {"beastmaster_summon_thunderhide": ("Ancient Thunderhide", "npc_dota_neutral_big_thunder_lizard")}
_CARD_OF_RE = re.compile(r'^(\s*)(?:W\(new_ability\("[^"]+", "([a-z0-9_]+)"|.*\bslug="([a-z0-9_]+)"[^)]*desc=_rw\d+_new\))')
_NEXT_PART_RE = re.compile(r'^\s*(?:W\((?:ability|new_ability|subgroup|hero_header|unit_header|item_header|section)\(|'
                           r'W\(ability_change\(None,|_rw\d+_old|# )')


def _postprocess_summon_units(lines, version):
    """A new or reworked ability that summons a unit of its own (7.42 Ancient Thunderhide, Chen's Zealot): the unit as a
    block under the card — its icon and name, its sheet with the numbers the ability gives it (summon_sheet) — before
    the cards of the unit's abilities (owner 2026-11-20: "раз это отдельный юнит, а не просто новая способность")."""
    out, i, done = list(lines), 0, set()
    while i < len(out):
        m = _CARD_OF_RE.match(out[i])
        slug = m and (m.group(2) or m.group(3))
        if not slug or slug not in _SUMMON_UNITS or slug in done:
            i += 1
            continue
        done.add(slug)
        k = next((j for j in range(i + 1, len(out)) if _NEXT_PART_RE.match(out[j])), len(out))
        # the indent of what comes next: a reworked card's slug sits on a line inside its call, deeper
        ind = re.match(r"^\s*", out[k]).group(0) if k < len(out) else m.group(1)
        name, icon = _SUMMON_UNITS[slug]
        # a pseudo-slug "<hero>_<unit>_unit" (known_exceptions): the page's dashed line from the ability finds it
        unit = slug.replace("_summon_", "_") + "_unit"
        block = [f'{ind}W(ability("{name}", slug="{unit}", icon_url="../icons/units/{icon}.png"))', f"{ind}W(ul_open())",
                 f'{ind}W(summon_sheet("{slug}", version="{version}"))', f"{ind}W(ul_close())"]
        out[k:k] = block
        i = k + len(block)
    return out


_INNATE_HDR_RE = re.compile(r'^(\s*)W\(ability\("([^"]+)", slug="([a-z0-9_]+)", innate=True\)\)\s*$')
_GAINS_RE = re.compile(r'^\s*W\(li\("Now also [^"]*", t\("NEW"\)')
_LOSES_RE = re.compile(r'^\s*W\(li\("No longer [^"]*", t\("DEL"\)')


def _postprocess_reworked_innates(lines, version):
    """An innate that both gains a part ("Now also creates a ghost …", NEW) and loses one ("No longer provides …", DEL)
    is reworked (owner 2026-11-20, 7.42 Death Prophet's Witchcraft: "похоже на реворк, поэтому old > new карточки
    нужны"): the card old -> new from the game's texts of both patches, Valve's rows in sight above it."""
    from patch import aghs_text
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version) if version else None
    out, i, n = list(lines), 0, 0
    while i < len(out):
        m = _INNATE_HDR_RE.match(out[i])
        if not (m and prev and i + 1 < len(out) and out[i + 1].strip() == "W(ul_open())"):
            i += 1
            continue
        end = next((k for k in range(i + 2, len(out)) if out[k].strip() == "W(ul_close())"), None)
        body = out[i + 2:end] if end else []
        if not (end and any(_GAINS_RE.match(r) for r in body) and any(_LOSES_RE.match(r) for r in body)
                and aghs_text.ability_text(m.group(3), prev) and aghs_text.ability_text(m.group(3), version)):
            i += 1
            continue
        ind, name, slug = m.groups()
        n += 1
        v = f"_ri{n}"
        setup = [r for r in body if not r.strip().startswith("W(")]       # "_pill1 = scale_pill(…)": before the card
        rows = [r.strip()[2:-1] for r in body if r.strip().startswith("W(")]
        card = setup + [f'{ind}{v}_old, {v}_new = game_ability_pair("{slug}", "{version}")',
                        f'{ind}W(ability_change(',
                        f'{ind}    old=dict(name="{name}", slug="{slug}", innate=True, desc={v}_old),',
                        f'{ind}    new=dict(name="{name}", slug="{slug}", innate=True, desc={v}_new),',
                        f'{ind}    summary="Innate reworked.",',
                        f'{ind}    tag="rework",',
                        f'{ind}    rows_first=lambda: [{", ".join(rows)}]))']
        out[i:end + 1] = card
        i += len(card)
    return out


_BREWLINGS = ("Earth", "Storm", "Fire", "Void")
_BREW_ROW_RE = re.compile(r'^(\s*)W\(li\("(Earth|Storm|Fire|Void)(?:\'s (\w)| now )')


def _brewling_row(line):
    """"Earth's Health decreased …" -> "Health decreased …"; "Fire now has Cinder Dash ability" -> "Now has …"."""
    m = _BREW_ROW_RE.match(line)
    rest = line[m.end():]
    head = m.group(3).upper() if m.group(3) else "Now "
    return f'{m.group(1)}W(li("{head}{rest}'


_NOW_HAS_RE = re.compile(r'^(\s*)W\(li\("Now has ([A-Z][\w\' ]+?) ability", t\("NEW"\)(.*)\)\)\s*$')


def _slug_of_name(prefix, name, version):
    """The slug of the one ability of these files ("brewmaster_…") the game names so, or None."""
    from patch.ability_kv import _hero_blocks
    from patch.aghs_text import ability_name
    hits = [s for s in _hero_blocks(version) if s.startswith(prefix) and ability_name(s, version) == name]
    return hits[0] if len(hits) == 1 else None


def _brewling_new_abilities(block, version):
    """A Brewling's "Now has Cinder Dash ability" with the ability retold in its "?" → the row hidden, the ability a
    card under the Brewling, its text from the game (owner 2026-11-20: "забыл оформить как новой способностью, убрав
    всё из [?]")."""
    out, cards = [], []
    for ln in block:
        m = _NOW_HAS_RE.match(ln)
        slug = m and version and _slug_of_name("brewmaster_", m.group(2), version)
        if not slug:
            out.append(ln)
            continue
        out.append(f'{m.group(1)}W(li("Now has {m.group(2)} ability", t("NEW"), covered=True))')
        cards.append(f'{m.group(1)}W(ability_change(None, dict(name={m.group(2)!r}, slug="{slug}", '
                     f'desc=game_ability_desc("{slug}", "{version}")), summary="New ability.", tag="new", sub=True))')
    return out, cards


def _postprocess_brewlings(lines, version=None):
    """Primal Split's rows about one Brewling ("Earth's Health decreased …", "Fire now has Cinder Dash ability") -> a
    block of that Brewling under Primal Split, its unit icon, the rows without its name, as 7.40 / 7.41 have them (owner
    2026-11-20: "ты не определил, что это Fire Brewling, Earth Brewling … их мы оформляем по-особенному")."""
    out, i = list(lines), 0
    while i < len(out):
        m = _ABIL_HDR_RE.match(out[i])
        if not (m and m.group(3) == "brewmaster_primal_split" and i + 1 < len(out)
                and out[i + 1].strip() == "W(ul_open())"):
            i += 1
            continue
        ind = m.group(1)
        end = next((k for k in range(i + 2, len(out)) if out[k].strip() == "W(ul_close())"), None)
        if end is None:
            break
        rows = out[i + 2:end]
        own = [r for r in rows if not _BREW_ROW_RE.match(r)]
        by = {}
        for r in rows:
            b = _BREW_ROW_RE.match(r)
            if b:
                by.setdefault(b.group(2), []).append(_brewling_row(r))
        if not by:
            i = end + 1
            continue
        block = [out[i]] + ([f"{ind}W(ul_open())"] + own + [f"{ind}W(ul_close())"] if own else [])
        for name in _BREWLINGS:
            if name in by:
                slug = f"brewmaster_{name.lower()}_unit"
                rows, cards = _brewling_new_abilities(by[name], version)
                block += [f'{ind}W(ability("{name} Brewling", slug="{slug}", icon_url="../icons/units/{slug}.png"))',
                          f"{ind}W(ul_open())", *rows, f"{ind}W(ul_close())", *cards]
        out[i:end + 1] = block
        i += len(block)
    return out
