"""Passes over the scaffold's lines (removed facets: post_facets.py): hero stat card, hidden stat rows, recipe cost."""
import json
import re

from .lines import (
    _ENTITY_START_RE,
    _HERO_DMG_ROW_RE,
    _PROP_CHANGE_RE,
    _py_repr,
)


_SAME_EFFECT_ROW_RE = re.compile(
    r'^\s*W\(li\("Now has the same effect for both Arc Warden and Tempest Double", t\("REWORK"\), extra=inline_note\("'
    r'(?P<both>.*?)\s*<span class=\\"pop-note\\">\(Previous values: Arc Warden: (?P<hero>.*?)\.\s*Tempest Double: (?P<double>.*?)\)</span>"\)\)\)\s*$')
_ABILITY_LINE_RE = re.compile(r'^(\s*)W\(ability\("([^"]+)", slug="([^"]+)"\)\)\s*$')
_UPGRADE_ROW_RE = re.compile(r'^\s*W\(li\("Aghanim\'s (?:Shard|Scepter):')


_NOTE_NUM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*)(\s*seconds?\b|s\b|%)?")
_KV_LINE_RE = re.compile(r"([A-Z][^:.]*):\s*([\d./%]+?)\.(?=\s|$)")


def _note_values(text):
    """The numbers of a Valve note in their order, with the unit: "activates in 2 seconds" -> "2s"."""
    return [n + ("s" if u and u.strip().startswith("s") else (u or "")) for n, u in _NOTE_NUM_RE.findall(text)]


def _selves_columns(ability, kv_text, hero, double, both):
    """Columns of Arc Warden's two-selves table (owner 2026-11-06: "научиться пока что у Arc Warden это определять",
    7.38 Spark Wraith): each number of Valve's note named by the game's own label of the value that has it in the patch
    before ("Activation delay: 2." -> "Activation delay"; the ability's own name left out: "Wraith speed" -> "Speed").
    (columns, hero, double, both) as tuples, or None when the three notes don't list the same count of numbers or a
    number has no label of its own."""
    vals = [_note_values(x) for x in (hero, double, both)]
    if len({len(v) for v in vals}) != 1 or len(vals[0]) < 2:
        return None
    pairs = [(label, value.rstrip("%")) for label, value in _KV_LINE_RE.findall(kv_text.partition("\n")[2])]
    labels = {}
    for label, value in pairs:
        labels.setdefault(value, label)                      # the first one: the hero's (the double's values follow)
    own = {w.lower() for w in ability.split()}
    bare = lambda v: re.sub(r"[s%]$", "", v)
    cols = []
    for v, d in zip(vals[0], vals[1]):
        label = labels.get(bare(v))
        # the double's number in this column is the same value of the game (7.38 Magnetic Field: the hero's evasion,
        # the double's attack range — two different things, no shared columns)
        if not label or (label, bare(d)) not in pairs:
            return None
        words = [w for w in label.split() if w.lower() not in own] or label.split()
        cols.append(" ".join(words).capitalize())
    return tuple(cols), *(tuple(v) for v in vals)


def _postprocess_two_selves_cards(lines, version=None):
    """Arc Warden's "same effect for both" row with Valve's previous values: an old -> new card with the two selves' numbers
    (owner 2026-11-05, 7.38). The descriptions are the game's of both patches; without them the row stays."""
    from patch.aghs_text import ability_text
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version) if version else None
    out = []
    i = 0
    while i < len(lines):
        at = _ABILITY_LINE_RE.match(lines[i])
        if not at or i + 1 >= len(lines) or lines[i + 1].strip() != 'W(ul_open())':
            out.append(lines[i])
            i += 1
            continue
        end = next((k for k in range(i + 2, len(lines)) if lines[k].strip() == 'W(ul_close())'), None)
        rows = lines[i + 2:end] if end else []
        same = next((m for m in map(_SAME_EFFECT_ROW_RE.match, rows) if m), None)
        texts = (ability_text(at.group(3), prev), ability_text(at.group(3), version)) if same and prev else (None, None)
        if not all(texts):
            out.append(lines[i])
            i += 1
            continue
        rest = [r for r in rows if not _SAME_EFFECT_ROW_RE.match(r)]
        # plain rows go above the card (owner 2026-11-05); an upgrade's "Aghanim's X: ..." has its own card below it
        plain = [r for r in rest if not _UPGRADE_ROW_RE.match(r)]
        below = [r for r in rest if _UPGRADE_ROW_RE.match(r)]
        first = (', rows_first=lambda: [' + ', '.join(r.strip()[2:-1] for r in plain) + ']') if plain else ''
        # the description only: the numbers stand in the two selves' lines or table (as content/p738.py)
        old_desc, new_desc = (json.dumps(t.partition("\n")[0], ensure_ascii=False) for t in texts)
        table = _selves_columns(at.group(2), texts[0], same.group("hero"), same.group("double"), same.group("both"))
        if table:
            cols, hero, double, both = (_py_repr(x) for x in table)
            nums = f'columns={cols}, hero={hero}, double={double}, '
            tail = f'both={both}'
        else:
            nums = f'hero="{same.group("hero")}", double="{same.group("double")}", '
            tail = f'both="{same.group("both")}"'
        out.append(f'{at.group(1)}W(two_selves_change("{at.group(2)}", "{at.group(3)}", old_desc={old_desc}, '
                   f'{nums}new_desc={new_desc}, {tail}{first}))')
        if below:
            out += [lines[i + 1], *below, lines[end]]
        i = end + 1
    return out


_CARD_CALL_RE = re.compile(r'^(\s*)W\((?:ability_change|two_selves_change)\(')
_UPGRADE_WORDS_RE = re.compile(r"Aghanim's (?:Shard|Scepter)", re.I)


def _statements(lines, start):
    """[(first, last)] line spans of whole statements from `start` to the line before W(ul_close()), and that line's
    index; None when the list does not close."""
    spans, k = [], start
    while k < len(lines):
        if lines[k].strip() == 'W(ul_close())':
            return spans, k
        depth, j = 0, k
        while j < len(lines):
            code = re.sub(r'"(?:[^"\\]|\\.)*"', '""', lines[j])
            depth += code.count("(") - code.count(")")
            if depth <= 0:
                break
            j += 1
        spans.append((k, j))
        k = j + 1
    return None


def _split_comment(stmt):
    """(code, "# comment") of a statement whose last line ends in a comment outside the strings, else (stmt, "")."""
    last = stmt.split("\n")[-1]
    code = re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: "x" * len(m.group(0)), last)
    at = code.find("#")
    if at < 0:
        return stmt, ""
    head = stmt[:len(stmt) - len(last)]
    return (head + last[:at]).rstrip(), last[at:].strip()


def _postprocess_rows_first(lines):
    """A card's plain rows stand above its caption, so all the ability's tagged rows are together under its name (owner
    2026-11-05, "Да, переноси" after Arc Warden 7.38). A row about an Aghanim's upgrade has a card of its own and stays
    under the card; a list holding anything but rows stays as written. Works on generator output and indented content."""
    out, i = [], 0
    while i < len(lines):
        m = _CARD_CALL_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        spans = _statements(lines, i)
        card_end = spans[0][0][1] if spans and spans[0] else i
        card = lines[i:card_end + 1]
        after = card_end + 1
        if "rows_first" in "\n".join(card) or after >= len(lines) or lines[after].strip() != 'W(ul_open())':
            out += card
            i = after
            continue
        listed = _statements(lines, after + 1)
        if not listed:
            out += card
            i = after
            continue
        rows, close = listed
        stmts = ["\n".join(lines[a:b + 1]) for a, b in rows]
        is_row = lambda s: s.lstrip().startswith(("W(li(", "W(li_formula("))
        is_note = lambda s: s.lstrip().startswith("#") or not s.strip()
        if not stmts or any(not is_row(s) and not is_note(s) for s in stmts):
            out += card
            i = after
            continue
        # a comment line goes with the row after it (or with the plain rows when nothing follows)
        plain, below, notes = [], [], []
        for s in stmts:
            if is_note(s):
                notes.append(s)
                continue
            group = below if _UPGRADE_WORDS_RE.search(s) else plain
            group += notes + [s]
            notes = []
        plain += notes
        if not any(is_row(s) for s in plain):
            out += card
            i = after
            continue
        ind = m.group(1)
        body = "\n".join(card).rstrip()
        assert body.endswith("))"), body[-40:]
        body = body[:-2].rstrip()
        body = body[:-1] if body.endswith(",") else body
        inner = []
        for s in plain:
            if is_note(s):
                inner += [f"{ind}        {s.strip()}"] if s.strip() else []
                continue
            s, note = _split_comment(s.strip())
            s = s.rstrip()[2:-1]                               # W(li(...)) -> li(...)
            inner += [f"{ind}        {ln.strip() if n == 0 else ln}" for n, ln in enumerate(s.split("\n"))]
            inner[-1] += "," + (f"  {note}" if note else "")
        out += (body + ",\n" + f"{ind}    rows_first=lambda: [\n" + "\n".join(inner) + f"\n{ind}    ]))").split("\n")
        if below:
            out += [lines[after]] + "\n".join(below).split("\n") + [lines[close]]
        i = close + 1
    return out




_ABILITY_SLUG_RE = re.compile(r'^\s*W\(ability\("([^"]+)", slug="([a-z0-9_]+)"')


def _after_innates(lines, version):
    """A removed ability that was no innate stands after the hero's innate blocks (7.38 Blood Mist came before Sanguivore:
    innates go first, tests/test_innate_first.py)."""
    from patch.ability_kv import _hero_blocks
    blocks = _hero_blocks(version) if version else {}
    innate = lambda slug: str((blocks.get(slug) or {}).get("Innate", "")).strip() == "1"

    def span(k):                                # the block's lines: its header to its list's close
        end = next((j for j in range(k, len(lines)) if lines[j].strip() == 'W(ul_close())'), k)
        return k, end + 1
    for k, line in enumerate(lines):
        m = _ABILITY_SLUG_RE.match(line)
        if not m or "innate=True" in line or innate(m.group(2)) or 'li("Removed", t("DEL")' not in "".join(lines[k:k + 3]):
            continue
        a, b = span(k)
        j = b
        while j < len(lines) and (m2 := _ABILITY_SLUG_RE.match(lines[j])) and ("innate=True" in lines[j] or innate(m2.group(2))):
            j = span(j)[1]
        if j > b:
            return _after_innates(lines[:a] + lines[b:j] + lines[a:b] + lines[j:], version)
    return lines


def _postprocess_hero_stat_card(lines, version=None):
    """Owner 2026-09-28 (Abaddon 7.38): a hero whose GENERAL rows describe its damage growth as rescaled
    ("Damage gain per level …" / "Damage at level 30 …") and whose attributes changed gets ONE row "Starting
    damage … and damage gain per level … rescaled" (hero_stat_card) first in that list; the damage rows are
    hidden at render time. Works on generator output and indented content."""
    from patch.hero_stats import attrs_changed
    from patch.weights import _prev_version
    out, i = [], 0
    while i < len(lines):
        out.append(lines[i])
        if not re.match(r'^\s*W\(hero_header\(', lines[i]):
            i += 1
            continue
        j = i + 1
        if j < len(lines) and lines[j].strip() == "W(ul_open())":
            k = j + 1
            while k < len(lines) and lines[k].strip() != "W(ul_close())":
                k += 1
            general = lines[j:k]
            hero = re.match(r'^\s*W\(hero_header\("([^"]+)"', lines[i]).group(1)
            changed = version is None or attrs_changed(hero, _prev_version(version) or "", version)
            if (changed and any(_HERO_DMG_ROW_RE.search(x) for x in general)
                    and not any("hero_stat_card(" in x for x in general)):
                ind = re.match(r'^(\s*)', lines[j]).group(1)
                out.append(lines[j])
                out.append(f"{ind}W(hero_stat_card())")
                i = j + 1
                continue
        i += 1
    return out


_CARD_NOTE_ROW_RE = re.compile(r'^\s*W\(li\("([^"\d]*)", t\("(?:MISC|QoL)"\)\)\)\s*$')


def _postprocess_card_stat_notes(lines):
    """Owner 2026-09-28 (Shiva's Guard 7.41): a MISC / QoL remark without numbers about a stat the stats card
    lists ("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack") becomes that
    stat's info (?) in the card — the row goes (MISC / QoL weigh 0). Works on generator output and on
    indented content lines alike."""
    out, i = [], 0
    while i < len(lines):
        if not re.match(r'^\s*W\(item_header\(', lines[i]):
            out.append(lines[i])
            i += 1
            continue
        end = i + 1
        while end < len(lines) and not _ENTITY_START_RE.match(lines[end]):
            end += 1
        out.extend(_card_notes_in_block(lines[i:end]))
        i = end
    return out


def _card_notes_in_block(block):
    notes = [(ln, m.group(1)) for ln in block for m in [_CARD_NOTE_ROW_RE.match(ln)] if m]
    text = "\n".join(block)
    for row, note in notes:
        c0 = text.find("properties_change(")
        new_at = text.find("new=[", c0) if c0 >= 0 else -1
        close = text.find("]))", new_at) if new_at >= 0 else -1
        if close < 0:
            break
        hit = None
        for m in re.finditer(r'"(\+[^"]*)"', text[new_at:close]):
            stat = re.sub(r"^[+\-]?[\d./]+%?\s+", "", m.group(1)).lower()
            if len(stat) > 3 and stat in note.lower():
                hit = m
                break
        if not hit:
            continue
        pos = new_at + hit.start()
        text = text[:pos] + f'{hit.group(0)} + info_tip("{note}")' + text[pos + len(hit.group(0)):]
        kept = text.split("\n")
        kept.remove(row)                                   # the remark lives in the card now
        text = "\n".join(kept)
    return text.split("\n")


_CARD_LINE_RE = re.compile(r'^(W\(properties_change\(old=\[)(.*?)(\], new=\[)(.*)(\]\)\))$')
_GRANT_TOKEN_RE = re.compile(r"\+[\d./]+%?\s+[A-Za-z' ]+")


def _postprocess_silent_stats(lines, version):
    """Owner 2026-09-27 (Gleipnir 7.38 lost +25 Damage and +25 Attack Speed without a word in the notes):
    the stats card also gets what the game's items.txt shows changed between the previous patch and this
    one but the block never mentions — removed -> DEL on the old side, added -> NEW, changed -> old / new
    with its b() badge. Guarded by tests/test_item_card_rows.py."""
    from patch.cards_item_stats import silent_stat_changes, _stat_text
    out, i = [], 0
    while i < len(lines):
        m_hdr = re.match(r'W\(item_header\("([^"]+)"(?![^)]*new=)[^)]*\)\)', lines[i])
        if not m_hdr:
            out.append(lines[i])
            i += 1
            continue
        end = i + 1
        while end < len(lines) and not re.match(r'W\((?:item|hero|unit|plain)_header\(|W\(section\(', lines[end]):
            end += 1
        block = lines[i:end]
        card_at = next((k for k, ln in enumerate(block) if _CARD_LINE_RE.match(ln)), None)
        card_rows = " ".join(re.findall(r'\(\s*"[^"]*"\s*,\s*"([^"]*)"', block[card_at])) if card_at is not None else ""
        li_texts = re.findall(r'li\(\s*"([^"]*)"', "\n".join(block))
        grants = " ".join(_GRANT_TOKEN_RE.findall(" ".join(li_texts)))
        changes = " ".join(m.group(1) for t in li_texts for m in [_PROP_CHANGE_RE.match(t)] if m)
        removed, added, changed = silent_stat_changes(m_hdr.group(1), version,
                                                      (card_rows + " " + grants + " " + changes).lower())
        has_build = any(ln.startswith('W(auto_components_change(') for ln in block)
        if (removed or added or changed) and not has_build and card_at is None:
            # no build change -> no stats card (owner 2026-09-28): plain rows, like the notes' own
            rows = [f'W(li("No longer provides {_stat_text(s, a)}", t("DEL")))' for s, a, _ in removed]
            rows += [f'W(li("Now also provides {_stat_text(s, b)}", t("NEW")))' for s, _, b in added]
            rows += [f'W(li("{_stat_line_name(s)} bonus {"increased" if b > a else "decreased"} from '
                     f'{_stat_text(s, a).split(" ")[0]} to {_stat_text(s, b).split(" ")[0]}", b({_py_repr(a)}, {_py_repr(b)})))'
                     for s, a, b in changed]
            k = next((j for j, ln in enumerate(block) if ln.strip() == "W(ul_open())"), None)
            block = (block[:k + 1] + rows + block[k + 1:]) if k is not None else block + ["W(ul_open())"] + rows + ["W(ul_close())"]
        elif removed or added or changed:
            olds = [f'("DEL", "{_stat_text(s, a)}")' for s, a, _ in removed]
            olds += [f'("", "{_stat_text(s, a)}")' for s, a, _ in changed]
            news = [f'("", "{_stat_text(s, b)}", b({_py_repr(a)}, {_py_repr(b)}))' for s, a, b in changed]
            news += [f'("NEW", "{_stat_text(s, b)}")' for s, _, b in added]
            if card_at is None:
                at = 2 if len(block) > 1 and block[1].startswith('W(auto_components_change(') else 1
                block.insert(at, f'W(properties_change(old=[{", ".join(olds)}], new=[{", ".join(news)}]))')
            else:
                mc = _CARD_LINE_RE.match(block[card_at])
                o = ", ".join(x for x in [mc.group(2)] + olds if x)
                n = ", ".join(x for x in [mc.group(4)] + news if x)
                block[card_at] = f'{mc.group(1)}{o}{mc.group(3)}{n}{mc.group(5)}'
        out.extend(block)
        i = end
    return out


def _stat_line_name(stat):
    from patch.cards_item_stats import _STAT_LINE
    return _STAT_LINE[stat][0]


_NOW_REQUIRES_RE = re.compile(
    r'^(?:Now (?:also )?requires .+|No longer requires .+|'
    r'Now requires .+ instead of .+)$'
)


# NOTE: These regexes are tightly coupled to _emit_li() output format.
# Two emission shapes for the same semantic case (net cost zero):
#   A) "Recipe cost X from A to B. Total cost unchanged at C ..." — single string
#   B) "Recipe cost X from A to B"  +  inline_note("Total cost unchanged ...")
# A cheaper recipe with an unchanged total is a BUFF (component stats arrive
# earlier and the final combine is cheaper); a pricier recipe is a NERF. So the
# recipe b() badge drives the row tag — NOT t("MISC").
# "Recipe cost X→Y. Total cost decreased/increased X→Y" — both changed.
# Badge by total cost; recipe % goes inline in the text.
_RECIPE_COST_BOTH_CHANGED_RE = re.compile(
    r'^W\(li\("(Recipe cost (?:increased|decreased) from )(\d+)( to )(\d+)'
    r'(\. Total [Cc]ost (?:increased|decreased) from )(\d+)( to )(\d+)",\s*'
    r'b\(\d+,\s*\d+,\s*l=True\)\)\)$'
)

_RECIPE_COST_UNCHANGED_INLINE_RE = re.compile(
    r'^W\(li\("(Recipe cost (?:increased|decreased) from )(\d+)( to )(\d+)'
    r'(\. Total cost unchanged[^"]*)",\s*'
    r'b\(\d+,\s*\d+,\s*l=True\)\)\)$'
)
_RECIPE_SAME_TOTAL_SAME_RE = re.compile(
    r'^W\(li\("(Recipe [Cc]ost unchanged at \d+g?)\. (Total cost unchanged[^"]*)",\s*(t\("\w+"\))\)\)$'
)
_RECIPE_COST_UNCHANGED_SPLIT_RE = re.compile(
    r'^W\(li\("(Recipe cost (?:increased|decreased) from )(\d+)( to )(\d+)",\s*'
    r'b\(\d+,\s*\d+,\s*l=True\),\s*'
    r'extra=inline_note\("(Total cost unchanged[^"]*)"\)\)\)$'
)


_STACK_NOTE_RE = re.compile(r'^W\(li\("([^"]*\bdoes not stack with\b[^"]*)",\s*t\("(?:MISC|INFO)"\)\)\)$')
_ABILITY_ROW_RE = re.compile(r'^(\s*W\(li\("(?:Passive|Active)\b[^"]*)(",\s*(?:t|b)\(.*\)\)\))$')


def _postprocess_stack_note_into_ability(lines):
    """A "... does not stack with ..." clarification right after an item's "Passive:/Active: ..." row
    is that ability's footnote: it goes into the row's "?" popup (info_tip) instead of standing as a
    separate MISC row (Orb of Corrosion 7.38 — owner, 2026-09-25)."""
    out = []
    for line in lines:
        m = _STACK_NOTE_RE.match(line.strip())
        if m and out:
            prev = _ABILITY_ROW_RE.match(out[-1])
            if prev:
                note = m.group(1).rstrip(".") + "."
                out[-1] = f'{prev.group(1)} " + info_tip("{note}") + "{prev.group(2)}'.replace(' + ""', '', 1)
                continue
        out.append(line)
    return out


def _recipe_total_badge(ra, rb, ta, tb):
    """One badge for "Recipe cost A -> B. Total cost C -> D": both % at the END of the row, "+100% / +4%"
    (owner 2026-09-26, Octarine Core 7.41f). The tag follows the TOTAL (what the buyer pays): a pricier
    recipe with a cheaper total is a BUFF. Said only when the two directions differ."""
    tag = "" if (int(rb) > int(ra)) == (int(tb) > int(ta)) else         (', force_overall="buff"' if int(tb) < int(ta) else ', force_overall="nerf"')
    return f"b([{ra}, {ta}], [{rb}, {tb}], l=True, slash=True{tag})"


_UNCHANGED_TOTAL_RE = re.compile(r"Total cost unchanged at (\d+)")


def _recipe_unchanged_total_badge(a, b_val, tail):
    """Recipe changed, total unchanged: "-9% / 0%" (owner 2026-10-05, Hydra's Breath 7.41f) — the recipe %
    (green or red, it drives the tag) and a grey 0% for the total, so the row doesn't read as a cheaper item.
    Valve's text without the total ("Total cost unchanged", 7.38b) keeps the recipe badge alone."""
    m = _UNCHANGED_TOTAL_RE.search(tail)
    if not m:
        return f"b({a}, {b_val}, l=True)"
    return f"b([{a}, {m.group(1)}], [{b_val}, {m.group(1)}], l=True, slash=True)"


_REMOVED_ROW_RE = re.compile(r'^\s*W\(li\("(Item [Cc]ycled [Oo]ut|Item removed from the game|Removed)", t\("DEL"\)\)\)\s*$')
_REMOVED_HDR_RE = re.compile(r'^(\s*)W\((item_header|enchant_header)\(("(?:[^"\\]|\\.)*")\)\)\s*$')


def _postprocess_removed_label(lines):
    """An item / enchantment whose one row says it was taken out gets its label where "Returning Tier 2 Artifact"
    stands, in the DEL colour (owner 2026-10-17): "Neutral Item cycled out" / "Neutral Item removed" in the neutral
    items' section, else "Item cycled out" / "Item removed", "Enchantment removed". The row stays (hidden by CSS,
    still counted by the tag filters)."""
    out = list(lines)
    neutral = False
    for i, ln in enumerate(out):
        if re.match(r'\s*W\(section\(', ln):
            neutral = "Neutral Item" in ln
        m = _REMOVED_HDR_RE.match(ln)
        if not m or i + 3 >= len(out) or out[i + 1].strip() != "W(ul_open())" or out[i + 3].strip() != "W(ul_close())":
            continue
        r = _REMOVED_ROW_RE.match(out[i + 2])
        if not r:
            continue
        if m.group(2) == "enchant_header":
            label = "Enchantment removed"
        else:
            label = (("Neutral Item " if neutral else "Item ")
                     + ("cycled out" if "cycled out" in r.group(1).lower() else "removed"))
        out[i] = f'{m.group(1)}W({m.group(2)}({m.group(3)}, removed="{label}"))'
    return out


def _postprocess_recipe_cost_zero_net(lines):
    """Rewrite recipe-cost rows to the one badge form (owner 2026-09-26): every % at the end of the row.
    - Both recipe and total changed: "... A to B. Total cost ... C to D", badge "+x% / +y%" (recipe / total),
      tag by the total.
    - Recipe changed, total unchanged: "recipe% / 0%" at the end (the 0% grey), tag by the recipe — a
      cheaper recipe is a real player benefit.
    """
    out = []
    for line in lines:
        m = _RECIPE_COST_BOTH_CHANGED_RE.match(line)
        if m:
            rpre, ra, rmid, rb, tpre, ta, tmid, tb = m.groups()
            out.append(f'W(li("{rpre}{ra}{rmid}{rb}{tpre}{ta}{tmid}{tb}", {_recipe_total_badge(ra, rb, ta, tb)}))')
            continue
        m = _RECIPE_COST_UNCHANGED_INLINE_RE.match(line)
        if m:
            # one form for the unchanged total (owner 2026-10-17, the majority of 7.38-7.41: 11 rows in the note, 9
            # in the text): the recipe in the row, "Total cost unchanged at X (due to …)" in its (?) note
            prefix, a, mid, b_val, tail = m.groups()
            note_text = tail.lstrip(". ")
            out.append(f'W(li("{prefix}{a}{mid}{b_val}", {_recipe_unchanged_total_badge(a, b_val, tail)}, '
                       f'extra=inline_note("{note_text}")))')
            continue
        m = _RECIPE_SAME_TOTAL_SAME_RE.match(line)
        if m:                                       # both unchanged (Solar Crest 7.41): the same split, its own tag
            out.append(f'W(li("{m.group(1)}", {m.group(3)}, extra=inline_note("{m.group(2)}")))')
            continue
        m = _RECIPE_COST_UNCHANGED_SPLIT_RE.match(line)
        if m:
            prefix, a, mid, b_val, note_text = m.groups()
            out.append(f'W(li("{prefix}{a}{mid}{b_val}", {_recipe_unchanged_total_badge(a, b_val, note_text)}, '
                       f'extra=inline_note("{note_text}")))')
            continue
        out.append(line)
    return out


def _postprocess_drop_now_requires(lines):
    """When an item block emits auto_components_change(...), the OLD→NEW
    components panel renders the recipe diff visually. The "Now requires
    X" / "No longer requires X" / "Now also requires X" / "Now requires
    X instead of Y" li rows become redundant text restatements. Drop
    them. Cost-only summary rows ("Recipe cost ...", "Total cost ...")
    stay — those are about amounts, not depicted in the panel.

    Per memory rule sloppy_drop_now_requires_after_auto_components.
    """
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if not line.startswith('W(auto_components_change('):
            i += 1
            continue
        # Walk the item block — drop matching W(li(...)) rows until the
        # next item_header / hero_header / section.
        i += 1
        while i < len(lines):
            ln = lines[i]
            if (ln.startswith('W(item_header(') or ln.startswith('W(hero_header(')
                or ln.startswith('W(section(') or ln.startswith('W(plain_header(')
                or ln.startswith('W(unit_header(')):
                break
            m_li = re.match(r'^W\(li\("(.+?)",\s*[bt]\(', ln)
            if m_li and _NOW_REQUIRES_RE.match(m_li.group(1)):
                i += 1
                continue
            out.append(ln)
            i += 1
    return out


# "36 + (9 per 5 minutes)" / "40 + 6 per minute" — a value that grows with GAME
# TIME. A "from <formula> to <formula>" line of two such formulas becomes a
# li_formula with a minute table (memory sloppy_per_minute_formula_table).
_PER_MINUTES_FORMULA_RE = re.compile(
    r'^(?P<base>\d+(?:\.\d+)?)\s*\+\s*\(?\s*(?P<inc>\d+(?:\.\d+)?)\s+(?:\w+\s+)?'
    r'(?:per|every)\s+(?:(?P<n>\d+)\s+)?min(?:ute)?s?\s*\)?$'
)
_MINUTE_GRID = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]

