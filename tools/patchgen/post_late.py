"""Passes run last: innate and facet cards, Roshan, mechanic lists, stances, new facet rows."""
import re

from .data import ABILS, HEROES
from .entities import innate_slugs_of
from .post_stats import _py_str

_LEVEL_OF_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<pre>[^"]*?) rescaled from \(\+(?P<a>\d+(?:\.\d+)?) with every (?P<n>\d+) hero levels\) '
    r'to \(\+(?P<b>\d+(?:\.\d+)?) with every level of (?P<abil>[^)"]+)\)", t\("[A-Za-z]+"\)\)\)\s*$')


_PCT_LEVEL_PILL_RE = re.compile(r'^\s*(_pill\d+) = scale_pill\("(?P<last>\d+(?:\.\d+)?)% \+ (?P<per>\d+(?:\.\d+)?)% per level"')
_PCT_LEVEL_ROW_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<pre>[^"]*?) rescaled from (?P<a>\d+(?:\.\d+)?)% per hero level to (?P<vals>(?:\d+(?:\.\d+)?%?/)+)" '
    r'\+ _pill\d+\[0\] \+ "", t\("[A-Za-z]+"\)(?:, extra=inline_note\("(?P<note>[^"]*)"\) \+ _pill\d+\[1\])?\)\)\s*$')
_ANY_SLUG_RE = re.compile(r'^\s*W\(ability\("[^"]+", slug="([^"]+)"')


def _pct_level_formula(pill, row, slug, version):
    """"… rescaled from 2% per hero level to 4/8/12/16% + 1% per level" (7.38 Precision Aura) -> a formula table by hero
    level, as the rule above (owner 2026-11-02): the levels come from the ability it depends on, or its own."""
    from patch.ability_kv import _hero_blocks
    p, m = _PCT_LEVEL_PILL_RE.match(pill), _PCT_LEVEL_ROW_RE.match(row)
    if not (p and m):
        return None
    vals = [v.rstrip("%") for v in m.group("vals").split("/") if v] + [p.group("last")]
    blocks = _hero_blocks(version) if version else {}
    parent = str((blocks.get(slug) or {}).get("DependentOnAbility", ""))
    ult = "ULTIMATE" in str((blocks.get(parent) or blocks.get(slug) or {}).get("AbilityType", "")).upper() or bool(parent)
    if ult:
        at, levels = "6, 12 and 18", "[1, 5, 6, 11, 12, 17, 18, 25, 30]"
        idx = "0 if L < 6 else min(3, (L - 6) // 6 + 1)"
    else:
        at, levels = "1, 3, 5 and 7", "[1, 3, 5, 7, 10, 20, 30]"
        idx = "min(3, (L - 1) // 2)"
    who = f"{parent} taken at hero levels {at}" if parent else f"Taken at hero levels {at}"
    note = f'{m.group("note")}. {who}' if m.group("note") else who
    ind = m.group("ind")
    return (f'{ind}W(li_formula("{m.group("pre")} rescaled", "{m.group("a")}% per hero level", '
            f'"{"/".join(vals)}% + {p.group("per")}% per level",\n'
            f'{ind}             lambda L: {m.group("a")} * L, lambda L: [{", ".join(vals)}][{idx}] + {p.group("per")} * L,\n'
            f'{ind}             levels={levels}, tag_levels=range(1, 31), label="Hero level", value_fmt="{{:g}}%",\n'
            f'{ind}             inline_note_text="{note}"))')


def _postprocess_ability_level_formula(lines, version):
    """"Radius increase rescaled from (+50 with every 10 hero levels) to (+40 with every level of Echo Slam)" -> a
    formula table by hero level with its BUFF / NERF, not a REWORK row (owner 2026-10-27, 7.39 Aftershock). The
    ability's levels: an ultimate at 6 / 12 / 18, a basic ability at 1 / 3 / 5 / 7 (as soon as it can be taken)."""
    from patch.ability_kv import _hero_blocks
    by_name = {name.lower(): slug for name, slug in ABILS.values()}
    out, slug_here = [], ""
    for line in lines:
        s = _ANY_SLUG_RE.match(line)
        slug_here = s.group(1) if s else slug_here
        formula = _pct_level_formula(out[-1], line, slug_here, version) if out else None
        if formula:
            out[-1] = formula
            continue
        m = _LEVEL_OF_RE.match(line)
        if not m:
            out.append(line)
            continue
        slug = by_name.get(m.group("abil").strip().lower())
        block = _hero_blocks(version).get(slug) if slug and version else None
        ult = "ULTIMATE" in str((block or {}).get("AbilityType", "")).upper()
        a, n, b, abil = m.group("a"), m.group("n"), m.group("b"), m.group("abil").strip()
        if ult:
            new_fn, levels, at = f"lambda L: {b} * (0 if L < 6 else min(3, (L - 6) // 6 + 1))", "[1, 6, 10, 12, 18, 20, 30]", "6, 12 and 18"
        else:
            new_fn, levels, at = f"lambda L: {b} * min(4, (L + 1) // 2)", "[1, 3, 5, 7, 10, 20, 30]", "1, 3, 5 and 7"
        ind = m.group("ind")
        out.append(f'{ind}W(li_formula("{m.group("pre")} rescaled", "+{a} with every {n} hero levels", '
                   f'"+{b} with every level of {abil}",\n{ind}             lambda L: {a} * (L // {n}), {new_fn},\n'
                   f'{ind}             levels={levels}, label="Hero level", value_fmt="+{{:g}}",\n'
                   f'{ind}             inline_note_text="{abil} taken at hero levels {at}"))')
    return out


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


_BLOCK_START_RE = re.compile(r'^\s*W\((ability|ability_change|ability_group|two_selves_change|new_ability|facet_header|facet_group|new_facet|facet_change)\(')
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
    starts = [k for k in range(stop) if _BLOCK_START_RE.match(span[k])]
    if not starts or any("sub=True" in ln for ln in span[:stop]):
        return span
    blocks = [span[a:b] for a, b in zip(starts, starts[1:] + [stop])]
    kinds = [_BLOCK_START_RE.match(b[0]).group(1) in _FACET_KINDS for b in blocks]
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


_NEW_INNATE_ROW_RE = re.compile(r'^\s*W\(li\("New innate ability\b', re.I)
_NEW_BASIC_ROW_RE = re.compile(r'^\s*W\(li\("New basic ability\b', re.I)
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
                    plain = r.lstrip().startswith("W(li(") and "extra=" not in r and "Aghanim" not in r
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
            old = olds[0]
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
    for k in range(start, len(out) - 3):
        if (f'slug="{slug}"' in out[k] and out[k].lstrip().startswith("W(ability(")
                and out[k + 1].strip() == "W(ul_open())" and out[k + 2].lstrip().startswith('W(li("Ability removed"')
                and out[k + 3].strip() == "W(ul_close())"):
            del out[k:k + 4]
            return True
    return False


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
_ROSHAN_ROW_RE = re.compile(r"""^\s*W\(li\(["'](?:[^"']*?\bRoshan(?:'s)? (?:now|no longer|will|is|has|gains|drops|"""
                            r"""HP|health|armor|base|attack|damage|magic|respawn|bounty|ability)\b)""", re.I)
_SECTION_RE = re.compile(r'^\s*W\(section\("([^"]+)"')
ROSHAN_HEADER = 'W(unit_header("Roshan", "../icons/units/npc_dota_roshan.png", general=False, track=True))'


# a row's "?" with what Valve's words leave out, found from the map or the game files — kept here so a regenerated
# page keeps it (the hand-written note was lost on every rewrap, 2026-10-30)
ROW_NOTES = {
    "Teleport time to Roshan's outposts decreased from 6s to 4s":
        "The two corner outposts next to Roshan's pits (added in 7.33 by the Twin Gates, removed in 7.38). "
        "The jungle outposts got 4s in 7.35",
}


_RETURNING_HEADER_RE = re.compile(r'^\s*W\(item_header\("[^"]+", new="(?:Returning|New)\b')


_PROVIDES_KIND_RE = re.compile(r'^Provides\s+(?P<stats>\+.+?)\.\s+(?P<kind>Use|Active|Passive|Toggle|Aura):\s+(?P<rest>.+)$')


def _provides_stats(text):
    """"+5 to All Attributes", "+20 Attack Speed and +4 Armor" → "+5 All Attributes", "+20 Attack Speed, +4 Armor"."""
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", text)
    return ", ".join(re.sub(r"^(\+[\d.%/]+)\s+to\s+", r"\1 ", p.strip()) for p in parts if p.strip())


def _postprocess_returning_rows(lines):
    """Under a returning or new item's header (7.37 Ironwood Tree "Returning Tier 1 Neutral Item") the rows are its
    description — NEW, as 7.38's returning artifacts (owner 2026-10-30: "смотри примеры в 7.38"), not MISC. A row
    "Provides +5 to All Attributes. Use: Plant Tree. …" is the item's stats and its ability, as a new item of 7.41:
    provides('+5 All Attributes') under the header and the row "Active: Plant Tree. …" — drawn as the ability's card
    (owner 2026-10-30: "всё ещё неправильно … пример — 7.38 Pyrrhic Cloak, Book of the Dead, Fallen Sky")."""
    out, inside, ul_at = [], False, None
    for ln in lines:
        if re.match(r'^\s*W\((?:item_header|hero_header|unit_header|section|plain_header)\(', ln):
            inside, ul_at = bool(_RETURNING_HEADER_RE.match(ln)), None
        elif inside and ln.strip() == "W(ul_open())":
            ul_at = len(out)
        elif inside and ln.lstrip().startswith("W(li(") and 't("MISC")' in ln:
            ln = ln.replace('t("MISC")', 't("NEW")', 1)
        t = _LI_TEXT_RE.match(ln) if inside else None
        m = _PROVIDES_KIND_RE.match(t.group(1)) if t else None
        if m and ul_at is not None:
            ind = ln[:len(ln) - len(ln.lstrip())]
            out.insert(ul_at, f"{ind}W(provides({_py_str(_provides_stats(m.group('stats')))}))")
            kind = "Active" if m.group("kind") == "Use" else m.group("kind")
            ln = ln.replace(t.group(1), f"{kind}: {m.group('rest')}", 1)
        out.append(ln)
    return out


def _postprocess_row_notes(lines):
    out = []
    for ln in lines:
        t = _LI_TEXT_RE.match(ln)
        note = ROW_NOTES.get(t.group(1)) if t else None
        if note and "extra=" not in ln:
            ln = re.sub(r"\)\)\s*$", f", extra=inline_note({_py_str(note)})))", ln)
        out.append(ln)
    return out


def _link_items(row):
    """The items a row's text names → links to their Changes pages (owner 2026-10-30, Roshan's drops: "кликабельные
    ссылки, ведущие на свои изменения"): '"… drops " + item_link("Refresher Shard") + " and …"'. Longest name first
    (Block of Cheese before Cheese); a row not in plain double quotes stays."""
    from patch.item_links import _roster
    m = re.match(r'^(\s*W\(li\()"((?:[^"\\]|\\.)*)"(.*)$', row)
    if not m:
        return row
    text = m.group(2)
    names = sorted((n for n in _roster() if len(n) > 3 and n in text), key=len, reverse=True)
    if not names:
        return row
    rx = re.compile(r"(?<![\w'])(" + "|".join(re.escape(n) for n in names) + r")(?![\w])")
    linked = rx.sub(lambda mm: f'" + item_link("{mm.group(1)}") + "', text)
    return f'{m.group(1)}"{linked}"{m.group(3)}'.replace('"" + ', "").replace(' + ""', "")


def _postprocess_roshan_block(lines):
    """General Updates rows about Roshan himself → a Roshan block at the end of the section, as 7.38–7.41's pages
    (owner 2026-10-30, 7.37: "Starting from his second death, Roshan now always drops Roshan's Banner" — "надо в
    блок к Roshan определять")."""
    start = next((k for k, ln in enumerate(lines) if _SECTION_RE.match(ln) and "General" in ln), None)
    head = next((k for k, ln in enumerate(lines) if ROSHAN_HEADER in ln), None)
    if head is not None:
        # a Roshan block already there: its rows' items link too (owner 2026-10-30, 7.38 "Roshan no longer drops
        # Aghanim's Blessing": "подчеркнуть с ссылкой … научить генератор такое сразу подчеркивать")
        stop = next((k for k in range(head + 1, len(lines)) if "W(ul_close())" in lines[k]), len(lines))
        return lines[:head + 1] + [_link_items(ln) for ln in lines[head + 1:stop]] + lines[stop:]
    if start is None:
        return lines
    end = next((k for k in range(start + 1, len(lines)) if _SECTION_RE.match(lines[k])), len(lines))
    while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].lstrip().startswith("#")):
        end -= 1                                        # the next section's "# =====" comment stays with it
    body = lines[start + 1:end]
    rows = [ln for ln in body if _ROSHAN_ROW_RE.match(ln)]
    if not rows:
        return lines
    body = _merge_adjacent_lists([ln for ln in body if ln not in rows])
    # a list left empty goes
    body = [ln for k, ln in enumerate(body) if not (ln.strip() == "W(ul_open())" and k + 1 < len(body)
                                                     and body[k + 1].strip() == "W(ul_close())")
            and not (ln.strip() == "W(ul_close())" and k > 0 and body[k - 1].strip() == "W(ul_open())")]
    while body and not body[-1].strip():
        body.pop()
    ind = rows[0][:len(rows[0]) - len(rows[0].lstrip())]
    block = [f"{ind}{ROSHAN_HEADER}", f"{ind}W(ul_open())", *map(_link_items, rows), f"{ind}W(ul_close())", ""]
    return lines[:start + 1] + body + block + lines[end:]


_SUBGROUP_LINE_RE = re.compile(r'^(\s*)W\(subgroup\("([^"]+)"\)\)\s*$')
_NEW_TERM_RE = re.compile(r'\bClassification\b|\bare considered\b', re.I)


def _postprocess_mechanic_lists(lines):
    """A General subgroup whose rows introduce lists of abilities / items (7.37 Teleport Classification, Breakability
    Update, Ability blocking and reflection) → a mechanic block, plain_header(title, new=…): its lists open as tables
    of icons under the rows, as 7.38 Lifesteal (owner 2026-10-30: "сделать в виде таблиц, мы умеем; научить
    генератор"). A classification of things that had none is a "New mechanic", the rest "Reworked mechanic"."""
    start = next((k for k, ln in enumerate(lines) if _SECTION_RE.match(ln) and "General" in ln), None)
    if start is None:
        return lines
    end = next((k for k in range(start + 1, len(lines)) if _SECTION_RE.match(lines[k])), len(lines))
    out = list(lines)
    for k in range(start + 1, end):
        m = _SUBGROUP_LINE_RE.match(out[k] or "")
        if not m:
            continue
        stop = next((j for j in range(k + 1, end)
                     if out[j] and (_SUBGROUP_LINE_RE.match(out[j]) or ROSHAN_HEADER in out[j])), end)
        rows = [ln for ln in out[k + 1:stop] if ln and ln.lstrip().startswith("W(li(")]
        if not any("extra=inline_list(" in r for r in rows):
            continue
        kind = "New mechanic" if _NEW_TERM_RE.search(m.group(2)) or any(_NEW_TERM_RE.search(r) for r in rows) \
            else "Reworked mechanic"
        # no tags in the block (owner 2026-10-30: "везде убрать теги")
        out[k] = f'{m.group(1)}W(plain_header("{m.group(2)}", new="{kind}", one_box=True))'
        _fold_sentences_into_tables(out, k + 1, stop)
    return [ln for ln in out if ln is not None]


_INLINE_LIST_END_RE = re.compile(r'(extra=inline_list\("(?:[^"\\]|\\.)*)("\))')


def _fold_sentences_into_tables(out, lo, hi):
    """A mechanic block's MISC rows without a list of their own are sentences of its tables (owner 2026-10-30,
    7.37 Breakability: "The breakability rules … have been updated", '"Breakable: Yes" has been added …', "… have an
    alt+tooltip line …" — "гармонично в таблицу встроить предложениями"): a line under the table of the row they
    speak of — "partially" → the Partially row, "fully" → the Fully row, else the block's first list. The rows go."""
    lists = [j for j in range(lo, hi) if out[j] and "extra=inline_list(" in out[j]]
    if not lists:
        return
    for j in range(lo, hi):
        ln = out[j]
        if not (ln and ln.lstrip().startswith("W(li(") and 't("MISC")' in ln and "extra=" not in ln):
            continue
        t = _LI_TEXT_RE.match(ln)
        if not t:
            continue
        text = t.group(1)
        low = text.lower()
        pick = lambda word: next((x for x in lists if word in out[x].lower().split("extra=")[0]), None)
        # owner 2026-10-30: the general sentence ("rules … have been updated") goes with the Fully table, not the first
        target = (pick("partially") if "partially" in low and "fully" not in low else None) or \
                 pick("fully") or lists[0]
        # a sentence about the game's tooltips ('"Breakable: Yes" has been added …', "… an alt+tooltip line …") is a
        # "?" on the table's leading words; any other sentence goes before them ("The breakability rules … have been
        # updated. The following are now Fully Disabled by Break:", owner 2026-10-30)
        kind = "pop-tip" if "tooltip" in low or "has been added" in low else "pop-lead"
        out[target] = _INLINE_LIST_END_RE.sub(
            lambda mm: f'{mm.group(1)}<br><span class=\\"{kind}\\">{text}</span>{mm.group(2)}', out[target], count=1)
        out[j] = None


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


def _merge_adjacent_lists(lines):
    """A list closed and the next opened right away — the rows of one block split in two (7.37 Faceless Void: the
    facet's "Renamed from Temporal Impunity" and its "Time Walk: …" row, from two parts of Valve's notes): one list."""
    out = []
    for ln in lines:
        if ln.strip() == "W(ul_open())" and out and out[-1].strip() == "W(ul_close())":
            out.pop()
            continue
        out.append(ln)
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


_WORD_RE = re.compile(r"[a-z]{4,}")


def _take_innate_text_rows(out, slug, version):
    """Rows in the hero's general list (already in `out`, after the hero's header) that only describe the new innate
    — 7.37 Visage: "Visage's ability cooldown durations are reduced as long as he's not taking damage …" stood among
    the hero's rows, Lurker's text: most of its words are in the game's description. Taken out of `out` and returned."""
    from patch.aghs_text import ability_text
    desc = set(_WORD_RE.findall((ability_text(slug, version) or "").lower()))
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
        words = set(_WORD_RE.findall(ln.lower()))
        if len(words) >= 8 and len(words & desc) / len(words) >= least:
            taken.insert(0, out.pop(k))
    # a general list left empty goes
    for k in range(len(out) - 2, start, -1):
        if out[k].strip() == "W(ul_open())" and out[k + 1].strip() == "W(ul_close())":
            del out[k:k + 2]
    return taken
