"""Innate abilities and stances: an ability that became / stopped being innate, new innates, level 0 rows, stance
blocks (split out of post_late.py, Fable review 2026-11-21)."""
import re

from .data import HEROES
from .entities import innate_slugs_of
from .post_facets import _row_values_in_text
from .post_stats import _py_str

_ABILITY_LINE_RE = re.compile(r'^(\s*)W\(ability\("([^"]+)", slug="([^"]+)"(, innate=True)?\)\)\s*$')
_NOW_INNATE_ROW_RE = re.compile(r'^\s*W\(li\("(?:Now is an innate ability|Moved to innate ability)\b')  # 7.37 Lunar Blessing
_INNATE_REWORK_ROW_RE = re.compile(r'^\s*W\(li\("(?:Now levels up with|Instead of )')
# an ability that gains an active or a passive part (owner 2026-11-06, 7.38 Special Delivery: "Now has an active
# component. Marci whistles … — не надо оформить карточкой old > new?")
_GAINED_PART_ROW_RE = re.compile(r'^\s*W\(li\("(?:Now has an? (?:active|passive) component|'
                                 r'Is now an? (?:active|passive) ability)\b')


def _postprocess_innate_cards(lines, version):
    """An ability that became an innate ("Now is an innate ability that improves with …", 7.39 Blur) or an innate
    whose rows rework it ("Now levels up with Duel", "Instead of increasing …", 7.39 Outfight Them!): an old -> new
    card from the game's texts of both patches in place of the plain header (owner 2026-10-27: "Blur — old > new",
    "Outfight Them! — unclear how it works now"). The "Now is an innate ability" row hides under the card (covered);
    the rows an innate rework card shows are for the proofread to hide (TODO[covered])."""
    from patch.aghs_text import ability_text
    from patch.weights import _prev_version
    prev = _prev_version(version) if version else None
    if not prev:
        return lines
    innate_now = innate_slugs_of(version)
    out, i = [], 0
    while i < len(lines):
        m = _ABILITY_LINE_RE.match(lines[i])
        if not m or i + 1 >= len(lines) or lines[i + 1].strip() != "W(ul_open())":
            out.append(lines[i])
            i += 1
            continue
        end = next((k for k in range(i + 2, len(lines)) if lines[k].strip() == "W(ul_close())"), None)
        rows = lines[i + 2:end] if end else []
        ind, name, slug = m.group(1), m.group(2), m.group(3)
        became = any(_NOW_INNATE_ROW_RE.match(r) for r in rows)
        # a MISC row is a renamed mechanic, not a rework (Withering Mist 7.39: Health Restoration, same numbers)
        reworked = (not became and slug in innate_now
                    and any(_INNATE_REWORK_ROW_RE.match(r) and 't("MISC")' not in r for r in rows)
                    and ability_text(slug, prev) and ability_text(slug, version)
                    and ability_text(slug, prev) != ability_text(slug, version))
        gained = (not became and not reworked and any(_GAINED_PART_ROW_RE.match(r) for r in rows)
                  and ability_text(slug, prev) and ability_text(slug, version)
                  and ability_text(slug, prev) != ability_text(slug, version))
        if not (became or reworked or gained):
            out.append(lines[i])
            i += 1
            continue
        # the block's title names the ability (owner 2026-11-06, 7.38 Succubus: "Succubus уже есть в названии")
        summary = ("Now is an innate ability." if became
                   else "Innate reworked." if slug in innate_now else "Ability reworked.")
        out += [f'{ind}W(ability_change(',
                f'{ind}    summary="{summary}",',
                f'{ind}    tag="rework",',
                f'{ind}    old=dict(name="{name}", slug="{slug}", desc=game_ability_desc("{slug}", "{prev}")),',
                f'{ind}    new=dict(name="{name}", slug="{slug}", {"innate=True, " if slug in innate_now or became else ""}'
                f'desc=game_ability_desc("{slug}", "{version}")),',
                f'{ind}))']
        if reworked:
            out.append(f"{ind}# TODO[covered]: the rows the card shows (its texts, the header's level) get covered=True")
        new_text = ability_text(slug, version) or ""
        if became and re.search(r"\d", new_text) and not re.search(r"\d", ability_text(slug, prev) or ""):
            # 7.38 Succubus: the old tooltip names no numbers, so its side would not say what the row's "from" was
            out.append(f"{ind}# TODO[old-values]: the old side gets its numbers from {prev}'s KV, the new side highlights the change")
        out.append(lines[i + 1])
        for r in rows:
            shown = (_NOW_INNATE_ROW_RE.match(r) or _GAINED_PART_ROW_RE.match(r)
                     or (became and _row_values_in_text(r, new_text)))
            out.append(re.sub(r"\)\)\s*$", ", covered=True))", r) if shown else r)
        i += 2 + len(rows)
    return out



_NEW_INNATE_ROW_RE = re.compile(r'^\s*W\(li\("New innate ability\b', re.I)
# 7.42 "New ability granted with Aghanim's Scepter" (Summon Lone Druid, Summon Ancient Thunderhide): a "New ability." card
# ... and "New Nothl Projection Sub-Ability granted with Aghanim's Shard" (7.42 Dazzle Through the Realm: 6 MISC rows,
# Fable audit 2026-11-19)
_NEW_BASIC_ROW_RE = re.compile(r'^\s*W\(li\("New (?:basic ability\b|(?:[\w\' ]+ )?(?:sub-)?ability granted (?:with|by) '
                               r'Aghanim)', re.I)
_ANY_ABILITY_LINE_RE = re.compile(r'^(\s*)W\(ability\("([^"]+)", slug="([^"]+)"(?:, innate=True)?\)\)\s*$')
_HERO_LINE_RE = re.compile(r'^\s*W\(hero_header\("([^"]+)"')


def _postprocess_new_innate_cards(lines, version):
    """A block whose first row is "New innate ability. …" (7.37: every hero got a new innate, the old one became a
    basic ability) → an old -> new card: the hero's innate of the patch before → the new one, both from the game's
    texts, summary "New innate ability.", tag NEW — as 7.38's Aggrandize. The rows the card shows are covered; a row
    with a note of its own ("Illusions cause full effect") stays."""
    from patch import loc_history
    from patch.aghs_text import ability_text
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version) if version else None
    if not prev:
        return lines
    old_innates = {s for s in innate_slugs_of(prev) if ability_text(s, prev)}
    hero_slug_of = {name: slug for name, slug in HEROES.values()}
    out, i, hero = [], 0, None
    while i < len(lines):
        h = _HERO_LINE_RE.match(lines[i])
        if h:
            hero = hero_slug_of.get(h.group(1))
        m = _ANY_ABILITY_LINE_RE.match(lines[i])
        end = (next((k for k in range(i + 2, len(lines)) if lines[k].strip() == "W(ul_close())"), len(lines))
               if m and i + 1 < len(lines) and lines[i + 1].strip() == "W(ul_open())" else None)
        # the "New innate ability" row anywhere in the block (7.37 Venomancer: the Scepter row came first); a card
        # only when the game files describe the ability (7.41 Leviathan's Catch, 7.31 have none) — else as it was
        has_text = end is not None and bool(ability_text(m.group(3), version))
        if not has_text or not any(_NEW_INNATE_ROW_RE.match(r) for r in lines[i + 2:end]):
            if has_text and any(_NEW_BASIC_ROW_RE.match(r) for r in lines[i + 2:end]):
                # "New basic ability." (7.37 Medusa Gorgon's Grasp, Luna Lunar Orbit): the "New ability." card, as 7.41
                if out and out[-1].lstrip().startswith("# v2-todo: convert to ability_change"):
                    out.pop()
                out.append(f'{m.group(1)}W(new_ability("{m.group(2)}", "{m.group(3)}", version="{version}"))')
                out.append(lines[i + 1])
                for r in lines[i + 2:end]:
                    # the "New … granted with Aghanim's" row itself too, its (?) only retells the card (7.42 Dazzle)
                    plain = (r.lstrip().startswith("W(li(") and ("extra=" not in r or bool(_NEW_BASIC_ROW_RE.match(r)))
                             and ("Aghanim" not in r or bool(_NEW_BASIC_ROW_RE.match(r))))
                    out.append(re.sub(r"\)\)\s*$", ", covered=True))", r) if plain else r)
                out.append(lines[end] if end < len(lines) else "")
                i = end + 1
                continue
            out.append(lines[i])
            i += 1
            continue
        ind, name, slug = m.group(1), m.group(2), m.group(3)
        moved = _take_innate_text_rows(out, slug, version)
        if out and out[-1].lstrip().startswith("# v2-todo: convert to ability_change"):
            out.pop()                                   # the card is made: no todo
        olds = sorted(s for s in old_innates if hero and s.startswith(f"{hero}_") and s != slug)
        out.append(f'{ind}W(ability_change(')
        if olds:
            # several innates last patch (7.41f Nyx: Mana Burn + Nyxth Sense): the one the notes say was removed
            hero_part = "\n".join(out[max((k for k, ln in enumerate(out) if _HERO_LINE_RE.match(ln)), default=0):])
            named = [s for s in olds if re.search(
                rf'Removed {re.escape(loc_history.tooltip(f"DOTA_Tooltip_Ability_{s}", prev) or s)} innate',
                hero_part, re.I)]
            old = (named or olds)[0]
            old_name = loc_history.tooltip(f"DOTA_Tooltip_Ability_{old}", prev) or old
            _drop_removed_block(out, old)               # the card's old side shows it: no "Ability removed" twice
            out.append(f'{ind}    old=dict(name="{old_name}", slug="{old}", innate=True, '
                       f'desc=game_ability_desc("{old}", "{prev}")),')
        else:
            out.append(f'{ind}    old=None,')
        rows = [*moved, *lines[i + 2:end]]
        # every row the card's text says is under it, hidden — a row's own note goes into the card's "?" (owner
        # 2026-10-30, 7.37 Persecutor: "Attacks slow enemies … — дубль того, что уже в карточке"); an Aghanim row is a
        # change of its own and stays
        notes = [n.group(1) for r in rows for n in [re.search(r'extra=inline_note\("((?:[^"\\]|\\.)*)"\)', r)]
                 if n and r.lstrip().startswith("W(li(") and "Aghanim" not in r]
        note_arg = f', note={_py_str("<br>".join(notes))}' if notes else ""
        out += [f'{ind}    new=dict(name="{name}", slug="{slug}", innate=True, '
                f'desc=game_ability_desc("{slug}", "{version}"{note_arg})),',
                f'{ind}    summary="New innate ability.",',
                f'{ind}    tag="new",',
                f'{ind}))', lines[i + 1]]
        for r in rows:
            covered = r.lstrip().startswith("W(li(") and "Aghanim" not in r and "covered=True" not in r
            out.append(re.sub(r"\)\)\s*$", ", covered=True))", r) if covered else r)
        out.append(lines[end] if end < len(lines) else "")
        i = end + 1
    return out


def _drop_removed_block(out, slug):
    """Take out of `out` (this hero's part) the block `ability(…, slug)` + "Ability removed" — 7.37 Abaddon's Font of
    Avernus, Enchantress's Forest Freebie: the new innate's card shows the old one on its left side."""
    start = max((k for k, ln in enumerate(out) if _HERO_LINE_RE.match(ln)), default=0)
    removed_row = re.compile(r'^\s*W\(li\("(?:Ability removed|Removed [^"]+ innate ability)"', re.I)
    for k in range(start, len(out) - 3):
        if (f'slug="{slug}"' in out[k] and out[k].lstrip().startswith("W(ability(")
                and out[k + 1].strip() == "W(ul_open())" and removed_row.match(out[k + 2])
                and out[k + 3].strip() == "W(ul_close())"):
            # 7.42 Lycan: "Removed Apex Predator innate ability" had its own block under a TODO[innate-swap]
            first = k - 1 if k > start and out[k - 1].lstrip().startswith("# TODO[innate-swap]") else k
            del out[first:k + 4]
            return True
    # 7.42 Chaos Knight, Nyx: "Removed <old> Innate Ability" sits in the hero's list; the card says it
    old_name = None
    for k in range(start, len(out)):
        m = re.match(r'^(\s*W\(li\("Removed ([^"]+?) Innate Ability", t\("DEL"\))\)\)\s*$', out[k], re.I)
        if m:
            out[k] = f'{m.group(1)}, covered=True))'
            old_name = m.group(2)
    return bool(old_name)


def _postprocess_innate_level0(lines, version):
    """7.37: a 7.36 innate that became a basic ability had a value at level 0 too (5 values) — the new one has 4
    levels. "Mana Burned per hit rescaled from 16/23/30/37/44 to 25/30/35/40": compare level 1–4 with level 1–4, the
    old level 0 dropped (the b() lists were of different length on 51 rows)."""
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version) if version else None
    if not prev:
        return lines
    from patch.ability_kv import hero_abilities
    was = innate_slugs_of(prev) - innate_slugs_of(version)
    hero_slug_of = {name: s for name, s in HEROES.values()}
    out, slug, hero = [], None, None
    rx = re.compile(r'b\(\[([^\]]+)\], \[([^\]]+)\]')
    for ln in lines:
        m = _ANY_ABILITY_LINE_RE.match(ln)
        h = _HERO_LINE_RE.match(ln)
        if h:
            hero = hero_slug_of.get(h.group(1))
        if m or h or ln.lstrip().startswith(("W(facet_header(", "W(subgroup(")):
            slug = m.group(3) if m else None
        row_slug = slug
        p = re.match(r'\s*W\(li\("([^":]{2,40}):\s', ln)
        if p and hero:                                  # a facet's row about the old innate (7.37 "Inner Beast: …")
            row_slug = (hero_abilities(hero, prev).get(p.group(1).lower()) or (slug,))[0]
        if row_slug in was and ln.lstrip().startswith("W(li("):
            def cut(mm):
                old, new = mm.group(1).split(", "), mm.group(2).split(", ")
                return f"b([{', '.join(old[1:])}], [{mm.group(2)}]" if len(old) == len(new) + 1 else mm.group(0)
            was_l0 = rx.search(ln)
            ln = rx.sub(cut, ln, count=1)
            same = re.search(r'b\(\[([^\]]+)\], \[\1\](?:, l=True)?\)', ln)
            if same and was_l0:
                # levels 1–4 the same: only the level-0 value went — a row with a tag and its why, not an empty
                # badge (owner 2026-10-30: "нет тега, кружок какой-то в начале вместо тега", Mana Break 7.37)
                lvl0 = was_l0.group(1).split(", ")[0]
                levels = len(same.group(1).split(", "))
                # NERF: what the hero had before the first point is gone, as Night Stalker 7.38's free level read by
                # points spent (owner 2026-10-30: "Warpath почему-то rework везде вместо buff/nerf"); a 0 at level 0
                # lost nothing — MISC, unless the row also says "No longer an innate ability" (_merge_no_longer_innate)
                lost = float(lvl0) != 0
                note = (f"Levels 1-{levels} unchanged; the {lvl0} it had at level 0 as an innate is gone (now a "
                        f"basic ability)" if lost else
                        f"Levels 1-{levels} unchanged; it had 0 at level 0 as an innate, so nothing is lost")
                tag = 't("NERF")' if lost else 't("MISC")'
                ln = ln.replace(same.group(0), f'{tag}, extra=inline_note({_py_str(note)})', 1) \
                    if "extra=" not in ln else ln.replace(same.group(0), tag, 1)
        out.append(ln)
    return out


# a General row about Roshan himself: "Roshan now …", "… death, Roshan now drops …", "Roshan's HP / armor / Base …";
# not his outposts, pit or banner item (7.37 "Teleport time to Roshan's outposts" stays a map row)

_NO_LONGER_INNATE_ROW_RE = re.compile(r'^\s*W\(li\("No longer an innate ability", t\("REWORK"\)\)\)\s*$')
_LEVEL0_NOTE = "level 0 as an innate"


# an ability whose rows name its parts ("Earth Brawler bonus armor …"): each part a block of its own with its icon,
# dashed to the parent (ABILITY_TREES in src/scripts.js) — as 7.40's Earth / Fire / Void Stance (owner 2026-10-30, 7.37:
# "у нас вроде для drunken brawler stances есть отдельное оформление")
STANCE_ABILITIES = {
    "brewmaster_drunken_brawler": (("Earth Brawler", "brewmaster_drunken_brawler_earth"),
                                   ("Storm Brawler", "brewmaster_drunken_brawler_storm"),
                                   ("Fire Brawler", "brewmaster_drunken_brawler_fire"),
                                   ("Void Brawler", "brewmaster_drunken_brawler_void")),
}


def _postprocess_stance_blocks(lines):
    """The parent's rows "Earth Brawler bonus armor rescaled …" → a block "Earth Brawler" (its own slug) right after the
    parent, the row without the name: "Bonus armor rescaled …"; the parent keeps its other rows."""
    out, i = [], 0
    while i < len(lines):
        m = re.match(r'^(\s*)W\(ability\("[^"]+", slug="([^"]+)"\)\)\s*$', lines[i])
        parts = STANCE_ABILITIES.get(m.group(2)) if m else None
        if not (parts and i + 1 < len(lines) and lines[i + 1].strip() == "W(ul_open())"):
            out.append(lines[i])
            i += 1
            continue
        ind = m.group(1)
        end = next((k for k in range(i + 2, len(lines)) if lines[k].strip() == "W(ul_close())"), len(lines))
        keep, by_part = [], {name: [] for name, _ in parts}
        for r in lines[i + 2:end]:
            pm = re.match(r'^(\s*W\(li\(")(' + "|".join(re.escape(n) for n, _ in parts) + r')(?: stance)? (\w)', r)
            if pm:
                by_part[pm.group(2)].append(pm.group(1) + pm.group(3).upper() + r[pm.end():])
            else:
                keep.append(r)
        out.append(lines[i])
        if keep:
            out += [lines[i + 1], *keep, lines[end]]
        for name, slug in parts:
            if by_part[name]:
                out += [f'{ind}W(ability("{name}", slug="{slug}"))', f"{ind}W(ul_open())", *by_part[name],
                        f"{ind}W(ul_close())"]
        i = end + 1
    return out


def _merge_no_longer_innate(lines):
    """A list with "No longer an innate ability" and a row whose levels 1-4 kept their values (only the level-0 value
    went): one row, "No longer an innate ability. Max Mana Burned per hit rescaled from …" (owner 2026-10-30, 7.37
    Mana Break: "сделав не 2 строки, а одну")."""
    out, i = [], 0
    while i < len(lines):
        if lines[i].strip() != "W(ul_open())":
            out.append(lines[i])
            i += 1
            continue
        end = next((k for k in range(i + 1, len(lines)) if lines[k].strip() == "W(ul_close())"), len(lines))
        block = lines[i:end + 1]
        lone = next((k for k, ln in enumerate(block) if _NO_LONGER_INNATE_ROW_RE.match(ln)), None)
        lvl0 = next((k for k, ln in enumerate(block) if _LEVEL0_NOTE in ln and ln.lstrip().startswith('W(li("')), None)
        if lone is not None and lvl0 is not None:
            # the ability is gone before its first point: NERF even where the level-0 value was 0
            block[lvl0] = block[lvl0].replace('W(li("', 'W(li("No longer an innate ability. ', 1).replace(
                't("MISC")', 't("NERF")', 1).replace(", so nothing is lost", " (now a basic ability)", 1)
            del block[lone]
        out += block
        i = end + 1
    return out



_WORD_RE_LATE = re.compile(r"[a-z]{4,}")


def _take_innate_text_rows(out, slug, version):
    """Rows in the hero's general list (already in `out`, after the hero's header) that only describe the new innate
    — 7.37 Visage: "Visage's ability cooldown durations are reduced as long as he's not taking damage …" stood among
    the hero's rows, Lurker's text: most of its words are in the game's description. Taken out of `out` and returned."""
    from patch.aghs_text import ability_text
    desc = set(_WORD_RE_LATE.findall((ability_text(slug, version) or "").lower()))
    if not desc:
        return []
    start = max((k for k, ln in enumerate(out) if _HERO_LINE_RE.match(ln)), default=None)
    if start is None:
        return []
    taken = []
    for k in range(len(out) - 1, start, -1):
        ln = out[k]
        if not ln.lstrip().startswith('W(li("'):
            continue
        # a "from … to" row is a change of values — unless it is the description itself, word for word (owner
        # 2026-10-30, 7.37 Beastmaster: "melee hero damage block chance is increased from 50% to 100% versus non-hero
        # units" is Rugged's whole text: "это разве не innate?")
        least = 0.6 if ', t("' in ln and " from " not in ln else 0.9
        words = set(_WORD_RE_LATE.findall(ln.lower()))
        if len(words) >= 8 and len(words & desc) / len(words) >= least:
            taken.insert(0, out.pop(k))
    # a general list left empty goes
    for k in range(len(out) - 2, start, -1):
        if out[k].strip() == "W(ul_open())" and out[k + 1].strip() == "W(ul_close())":
            del out[k:k + 2]
    return taken
