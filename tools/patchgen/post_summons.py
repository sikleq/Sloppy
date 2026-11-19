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
