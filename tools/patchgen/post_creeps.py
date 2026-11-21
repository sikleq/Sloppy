"""Neutral creeps and units: new camps, a unit's renamed / replaced ability, renames, new creeps' abilities (split out
of post_tables.py, Fable review 2026-11-21)."""
import re

from .post_stats import _py_str

_NEW_CAMP_RE = re.compile(r'^(?P<ind>\s*)W\(li\("Added an? (?P<name>[A-Z][\w\' ]+?) camp: New (?P<size>Small|Medium|Large|'
                          r'Ancient) camp(?: for (?P<side>Radiant|Dire))?", t\("\w+"\), extra=inline_note\("\s*Each camp '
                          r'consists of (?P<units>[^"]+)"\)\)\)\s*$')
_CAMP_UNIT_RE = re.compile(r'(\d+) ([A-Z][\w\' ]+?)(?= and |, |$)')


def _creep_slug(name, version):
    """"Odobenus Footmen" → "odobenus_footman" (npc_dota_neutral_<slug>), by the game's own names, or None."""
    from builders.creeps import CREEP_DISPLAY_NAMES as _NPC_DISPLAY_NAME
    singular = re.sub(r"men$", "man", name)
    singular = re.sub(r"s$", "", singular) if singular == name else singular
    for npc, shown in _NPC_DISPLAY_NAME.items():
        if shown in (name, singular) and npc.startswith("npc_dota_neutral_"):
            return npc[len("npc_dota_neutral_"):], shown
    return None


def _camp_numbers(units, version):
    """(average gold, average xp) of a camp from its units' bounties in the game files of `version`, or ("", "")."""
    from patch import game_files
    from patch.unit_numbers import _UNITS_FILE, numbers
    text = game_files.read(version, _UNITS_FILE) if version else None
    if not text:
        return "", ""
    gold = xp = 0.0
    for n, slug, _shown in units:
        nums = numbers(text, f"npc_dota_neutral_{slug}")
        lo, hi = (float(x) for x in nums["Gold"].split("-"))
        gold += n * (lo + hi) / 2
        xp += n * float(nums["XP"])
    return f"{gold:g}", f"{xp:g}"


def _postprocess_new_camps(lines, version=None):
    """Valve's "Added a Radigull camp: New Medium camp for Radiant" rows, one after another, each with "Each camp consists
    of …" behind a "?" (7.42: four of them) → one row "New neutral camps" with a table of the camps (owner 2026-11-19:
    "не сделал таблицей какие крипы появились новые/лагеря"): the camp, its size and side, its average gold and xp
    from the game files, its creeps with their portraits — as 7.38's flooded camps (camp_table). Valve's rows stay hidden
    for the weights. A row whose creeps the files do not name leaves the run as it is."""
    out, run, pending = [], [], []

    def flush():
        if len(run) < 2:
            out.extend(r[0] for r in run)
        else:
            ind = run[0][1].group("ind")
            rows = []
            for _ln, m, units in run:
                gold, xp = _camp_numbers(units, version)
                creeps = ", ".join(f'({n}, {_py_str(shown)}, NEUTRAL_CDN + "{slug}.png")' for n, slug, shown in units)
                # the size as its icon, the side a column (owner 2026-11-19: "новый столбец side … иконку типа кэмпа")
                rows.append(f'({_py_str(m.group("name") + " camp")}, [{creeps}], {_py_str(gold)}, {_py_str(xp)}, '
                            f'{_py_str(m.group("size"))}, {_py_str(m.group("side") or "")})')
            # the count alone: which camps, their size and side are the table's (owner 2026-11-19: "убрать … потому что
            # список мы уже перенесли в таблицу")
            story = f"Added {len(run)} new neutral camps"
            # a block of its own after the list, as 7.38's Flooded Camps (owner 2026-11-19: "New neutral camps сделаны
            # не так, как мы делали … с новыми нейтралами"): its label, the story, the camps' table; Valve's rows hidden
            pending.extend([f'{ind}W(plain_header("New Neutral Camps", dynamics=False, new="New camps"))',
                            f'{ind}W(ul_open())',
                            f'{ind}W(mech_story({_py_str(story)}, table=camp_table([{", ".join(rows)}])))'])
            pending.extend(ln[:-2] + ", covered=True))" for ln, _m, _u in run)
            pending.append(f'{ind}W(ul_close())')
        run.clear()

    for ln in lines:
        if pending and ln.strip() == "W(ul_close())":
            flush()
            out.append(ln)
            out.extend(pending)
            pending.clear()
            continue
        m = _NEW_CAMP_RE.match(ln)
        units = []
        if m:
            for n, name in _CAMP_UNIT_RE.findall(m.group("units")):
                found = _creep_slug(name.strip(), version)
                if not found:
                    units = []
                    break
                units.append((int(n), *found))
        if m and units:
            run.append((ln, m, units))
            continue
        flush()
        out.append(ln)
    flush()
    return out



_UNIT_ABILITY_RE = re.compile(r'^(?P<ind>\s*)W\(ability\("(?P<new>[^"]+)", icon_url="(?P<icon>[^"]*/(?P<slug>\w+)\.png)"\)\)\s*$')
_RENAMED_ROW_RE = re.compile(r'^\s*W\(li\("(?P<old>[A-Z][\w\' -]+?)(?: ability)? renamed (?:in)?to (?P<new>[A-Z][\w\' -]+?)"')


_REWORKED_ROW_RE_TABLES = re.compile(r'^\s*W\(li\("Ability [Rr]eworked"')
_REPLACED_ROW_RE = re.compile(r'^\s*W\(li\("(?P<old>[A-Z][\w\' -]+?) ability replaced with (?P<new>[A-Z][\w\' -]+?)"')


def _replacement_slug(old_slug, new_name, version):
    """The unit ability called <new_name> in `version` that shares the longest prefix with <old_slug> (7.42 Mud Golem:
    mud_golem_hurl_boulder -> mud_golem_hurl_big_boulder), else None."""
    from patch.ability_kv import _unit_blocks
    from patch.aghs_text import tooltip
    hits = [k for k in _unit_blocks(version) if tooltip(f"DOTA_Tooltip_ability_{k}", version) == new_name]
    prefix = lambda k: next((n for n, (x, y) in enumerate(zip(k, old_slug)) if x != y), min(len(k), len(old_slug)))
    return max(hits, key=prefix) if hits else None


def _unit_card(rows, m, version):
    """(old name, old slug, new name, new slug, summary, tag) of the card a unit's ability block asks for, or None."""
    slug, name = m.group("slug"), m.group("new")
    for r in rows:
        ren = _RENAMED_ROW_RE.match(r)
        if ren and ren.group("new") == name:
            return ren.group("old"), slug, name, slug, "Ability reworked.", "rework"
        if _REWORKED_ROW_RE_TABLES.match(r):
            return name, slug, name, slug, "Ability reworked.", "rework"
        rep = _REPLACED_ROW_RE.match(r)
        if rep and rep.group("old") == name:
            new_slug = _replacement_slug(slug, rep.group("new"), version)
            if new_slug and new_slug != slug:
                return name, slug, rep.group("new"), new_slug, "New ability.", "new"
    return None


def _postprocess_renamed_unit_ability(lines, version=None):
    """A unit's ability the patch reworks → the old → new card with both patches' game texts (the old side only from
    the files of the patch before), the rows above it, the word rows the card already says hidden (owner 2026-11-18:
    "переделанная способность: карточки old → new"). Three cases, all 7.42: renamed and reworked ("Fireball ability
    renamed into Searing Swoop", Ancient Black Dragon), reworked under its name ("Ability Reworked", Kobold Soldier's
    Steal Weapon), replaced by another ability ("Hurl Boulder ability replaced with Hurl Big Boulder", Mud Golem —
    owner 2026-11-19: "все ренеймы оформляем по одному типу"). Left alone when the files have no text for a side."""
    from patch.ability_kv import _unit_blocks
    from patch.aghs_text import ability_text
    from patch.meta import _prev_patch_version
    out, i = [], 0
    while i < len(lines):
        m = _UNIT_ABILITY_RE.match(lines[i])
        end = next((k for k in range(i + 2, len(lines)) if lines[k].strip() == "W(ul_close())"), None) \
            if m and i + 1 < len(lines) and lines[i + 1].strip() == "W(ul_open())" else None
        rows = lines[i + 2:end] if end else []
        card = _unit_card(rows, m, version) if rows and version else None
        prev = _prev_patch_version(version) if card else None
        if not card or not all(ln.lstrip().startswith(("W(li", "#")) for ln in rows) \
                or not (prev and ability_text(card[1], prev) and ability_text(card[3], version)):
            out.append(lines[i])
            i += 1
            continue
        old_name, old_slug, new_name, new_slug, summary, tag = card
        ind, icon = m.group("ind"), m.group("icon")
        texture = (_unit_blocks(version).get(new_slug) or {}).get("AbilityTextureName") or new_slug
        new_icon = icon if new_slug == old_slug else f"../icons/abilities/{texture}.png"

        def inner(row):
            if row.lstrip().startswith("#"):
                return f"{ind}        {row.strip()}"
            row = row.strip()[2:-1]                                           # W(li(…)) -> li(…)
            if re.search(r', t\("(?:NEW|MISC|REWORK)"\)', row) and "covered=" not in row \
                    and ("wrong-word" not in row):
                row = row[:-1] + ", covered=True)"
            return f"{ind}        {row},"
        if new_slug == old_slug:
            descs = [f'{ind}_{old_slug}_old, _{old_slug}_new = game_ability_pair("{old_slug}", "{version}")']
            old_desc, new_desc = f"_{old_slug}_old", f"_{old_slug}_new"
        else:
            descs = []
            old_desc = f'game_ability_desc("{old_slug}", "{prev}")'
            new_desc = f'game_ability_desc("{new_slug}", "{version}")'
        out += [*descs, f'{ind}W(ability_change(',
                f'{ind}    old=dict(name={_py_str(old_name)}, icon_url="{icon}", desc={old_desc}),',
                f'{ind}    new=dict(name={_py_str(new_name)}, icon_url="{new_icon}", desc={new_desc}),',
                f'{ind}    summary="{summary}",', f'{ind}    tag="{tag}",', f'{ind}    rows_first=lambda: [',
                *map(inner, rows), f'{ind}    ]))']
        i = end + 1
    return out



_UNIT_HEAD_RE = re.compile(r'^(?P<ind>\s*)W\(unit_header\("(?P<name>[^"]+)"(?P<rest>.*)\)\)\s*$')
_ANY_RENAME_RE = re.compile(r'^\s*W\(li\("(?P<old>[A-Z][\w\' -]+?)(?: \([^)"]*\))?(?: ability)? renamed (?:in)?to '
                            r'(?P<new>[A-Z][\w\' -]+?)"')


def _postprocess_renames(lines):
    """Every rename in one form, as abilities, items and facets have had it (owner 2026-11-19: "все ренеймы оформляем
    по одному типу"): the header says "Old → New" and the rename row goes. A unit ("Hill Troll (from Dark Troll camp)
    renamed to Dark Troll Trapper", 7.42) gets unit_header(old_title=); an item's ability that the item's card already
    shows under its new name ("Break renamed to Respite", Tranquil Boots — "Passive: Respite" on the card) keeps its
    row only for the weights (covered=True)."""
    out = list(lines)
    unit, card = None, ""
    for i, ln in enumerate(out):
        head = _UNIT_HEAD_RE.match(ln)
        if head:
            unit, card = (i, head), ""
            continue
        if _BLOCK_START_RE.match(ln):
            unit, card = None, ""
        if "item_abilities_change(" in ln or (card and ln.lstrip().startswith(('old=', 'new=', '"'))):
            card += ln
        ren = _ANY_RENAME_RE.match(ln)
        if not ren:
            continue
        if unit and unit[1].group("name") == ren.group("new") and "old_title=" not in out[unit[0]]:
            h = unit[1]
            out[unit[0]] = f'{h.group("ind")}W(unit_header("{h.group("name")}"{h.group("rest")}, old_title={_py_str(ren.group("old"))}))'
            out[i] = None
        elif card and re.search(r'(?:Active|Passive|Toggle|Use): ' + re.escape(ren.group("new")) + r'\b', card) \
                and "covered=" not in ln:
            out[i] = ln[:-2] + ", covered=True))"
    out = [x for x in out if x is not None]
    # a unit list left with nothing in it goes (Dark Troll Trapper had only its rename row)
    return [x for k, x in enumerate(out) if not (x.strip() == "W(ul_open())" and k + 1 < len(out)
                                                  and out[k + 1].strip() == "W(ul_close())")
            and not (x.strip() == "W(ul_close())" and k > 0 and out[k - 1].strip() == "W(ul_open())")]


_NEW_UNIT_HEAD_RE = re.compile(r'^(?P<ind>\s*)W\(unit_header\("(?P<name>[^"]+)", NEUTRAL_CDN \+ "(?P<npc>\w+)\.png", '
                               r'new="New Level[^"]*"\)\)\s*$')
_NEW_ABIL_ROW_RE = re.compile(r'^\s*W\(li\("(?P<abil>[A-Z][\w\' -]+?): (?:Active|Passive)\b[^"]*", t\("\w+"\)')
_STATS_ROW_RE = re.compile(r'^\s*W\(li\("New Level \d+ [\w ]+Creep", t\("\w+"\)')
_BLOCK_START_RE = re.compile(r'^\s*W\((?:unit_header|hero_header|item_header|section|plain_header)\(')


def _unit_abilities_tables(npc, version):
    """{tooltip name: (slug, icon file)} of npc_dota_neutral_<npc>'s abilities in the files of `version`."""
    import os
    from patch import game_files
    from patch.ability_kv import _unit_blocks
    from patch.aghs_text import tooltip
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "stats", version, "npc_units.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    else:
        text = game_files.npc(version, "npc_units.txt") or ""
    m = re.search(r'^\t"npc_dota_neutral_' + re.escape(npc) + r'"\s*\n\t\{(.*?)^\t\}', text, re.S | re.M)
    out = {}
    for slug in (re.findall(r'"Ability\d+"\s+"(\w+)"', m.group(1)) if m else []):
        name = tooltip(f"DOTA_Tooltip_ability_{slug}", version)
        if name:
            block = _unit_blocks(version).get(slug) or {}
            out[name] = (slug, block.get("AbilityTextureName") or slug)
    return out


def _postprocess_new_creep_abilities(lines, version=None):
    """A new neutral creep's abilities → "New ability" cards with the game's text, as every new ability on the site
    (owner 2026-11-19, 7.42 "Odobenus Blight: Passive Ability и др. … сделано строкой с [?]"); Valve's row stays under
    the card, hidden for the weights (covered=True), and so does the row of the creep's numbers that the sheet above
    shows ("New Level 4 Ranged Creep" + its "?"). The icon is the one the game draws (AbilityTextureName: Snowball Shot
    lives on warpine_raider_seed_shot). A row whose ability the files do not name stays as it is."""
    from patch.aghs_text import ability_text
    out, abilities, ind = [], {}, ""
    for ln in lines:
        head = _NEW_UNIT_HEAD_RE.match(ln)
        if head:
            abilities = _unit_abilities_tables(head.group("npc"), version) if version else {}
            ind = head.group("ind")
            out.append(ln)
            continue
        if _BLOCK_START_RE.match(ln):
            abilities = {}
        if abilities and _STATS_ROW_RE.match(ln) and "covered=" not in ln:
            out.append(ln[:-2] + ", covered=True))")
            continue
        row = _NEW_ABIL_ROW_RE.match(ln) if abilities else None
        hit = abilities.get(row.group("abil")) if row else None
        if not hit or not ability_text(hit[0], version):
            out.append(ln)
            continue
        slug, icon = hit
        out += [f'{ind}W(ul_close())',
                f'{ind}W(new_ability({_py_str(row.group("abil"))}, "{slug}", version="{version}", '
                f'icon_url="../icons/abilities/{icon}.png"))',
                f'{ind}W(ul_open())', ln[:-2] + ", covered=True))"]
    return out
