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
