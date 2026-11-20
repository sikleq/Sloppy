"""The changes a General block sums up, as a table of icons (owner 2026-11-20, 7.42 Spell Power Reduction: Valve's three
sentences and "Specifics … can be found in the corresponding ability or item notes"; the rows they mean are the ones
marked "As a part of the comprehensive Spell Power Reduction"). One icon per ability or item; its hover lists its
changes with their % in the colour of the change, as the cards do; a click jumps to its hero or item."""
import html as _html
import re

from .mech_abilities import _icon, _item_icon, ability_chip, mech_table

_TALENT_RE = re.compile(r"^Level \d+ Talent (.+)$")
_FROM_TO_RE = re.compile(r"\bfrom (.+?) to (.+)$")
_PER_LEVEL_RE = re.compile(r"^\d+(?:\.\d+)?% \+ (\d+(?:\.\d+)?)% per level$")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def _talent_ability(hero, text):
    """The hero's ability a talent row is about ("Level 25 Talent Berserker's Call AoE decreased …" → Berserker's
    Call): the longest run of words after "Talent" that has an icon."""
    m = _TALENT_RE.match(text)
    words = (m.group(1) if m else text).split(" ")
    for n in range(min(len(words), 6), 0, -1):
        for s in range(0, len(words) - n + 1):
            name = " ".join(words[s:s + n])
            if _icon(hero, name):
                return name
    return None


def _pct_html(text):
    """"… from 80/135/180 to 80/130/180" → " 0% / −4% / 0%" coloured by sign (one value when every level moves alike);
    "" when the row has no "from … to …"."""
    m = _FROM_TO_RE.search(text)
    if not m:
        return ""
    a, b = _PER_LEVEL_RE.match(m.group(1)), _PER_LEVEL_RE.match(m.group(2))
    if a and b:          # "4% + 0.4% per level → 4% + 0.3% per level" (Io Equilibrium): the part that moved
        pa, pb = float(a.group(1)), float(b.group(1))
        p = round((pb - pa) / pa * 100) if pa else 0
        tone = " iab-buff" if p > 0 else " iab-nerf" if p < 0 else ""
        return f' <span class="iab-num{tone}">{"+" if p > 0 else "−" if p < 0 else ""}{abs(p)}% per level</span>'
    old, new = [float(x) for x in _NUM_RE.findall(m.group(1))], [float(x) for x in _NUM_RE.findall(m.group(2))]
    if not old or not new:
        return ""
    if len(old) != len(new):            # "from 11s to 8/9/10/11s": the one old value against each new one
        old = old * len(new) if len(old) == 1 else old
        new = new * len(old) if len(new) == 1 else new
        if len(old) != len(new):
            return ""
    pcts = [round((b - a) / a * 100) if a else 0 for a, b in zip(old, new)]

    def one(p):
        tone = " iab-buff" if p > 0 else " iab-nerf" if p < 0 else ""
        return f'<span class="iab-num{tone}">{"+" if p > 0 else "−" if p < 0 else ""}{abs(p)}%</span>'
    return " " + (one(pcts[0]) if len(set(pcts)) == 1 else " / ".join(one(p) for p in pcts))


def _resolve(kind, owner, abil, text):
    """(name shown, icon) of one change; a change without its icon stops the build — it would silently drop out."""
    if kind == "item":
        src, name = _item_icon(owner), owner
    else:
        name = abil if abil and abil != "Talents" else _talent_ability(owner, text)
        src = _icon(owner, name) if name else None
        if not src and abil == "Talents":     # a talent of no one ability ("Spell Area of Effect"): the talent tree
            from .elements import TALENT_ICON_URL
            src, name = TALENT_ICON_URL, "Talents"
    if not src:
        raise ValueError(f"marked_changes: no icon for {owner} / {abil}: {text[:60]!r}")
    return name, src


def _chip(kind, owner, name, src, texts):
    from .elements import _slugify
    # the ability's name alone, no hero (owner 2026-11-20: "не надо писать героев — только название способности");
    # a talent of no one ability keeps its hero ("Kunkka: Talents"), the tree icon says nothing of whose
    head = _html.escape(name if kind == "hero" and name != "Talents" else f"{owner}: {name}" if kind == "hero"
                        else owner)
    # a little table, as the site's other tooltips with numbers (calendar's tb-tip-table): the change on the left, its
    # % on the right; the name over it stands out (owner 2026-11-20: "в табличном виде … название … выделять")
    rows = "".join(f"<tr><td>{_html.escape(t)}</td><td>{_pct_html(t).strip()}</td></tr>" for t in texts)
    tip = f'<b class="tip-head">{head}</b><table class="tb-tip-table">{rows}</table>'
    return (f'<a class="mech-jump" href="#dyn-{kind}-{_slugify(owner)}">'
            f'{ability_chip(name, src, owner=owner if kind == "hero" else None, tip=tip)}</a>')


def icons_with_notes(pairs):
    """[(item or "Hero's Ability", what of it), …] → their icons, each naming itself and its note on hover (7.42 Item
    Potency: the items illusions still don't apply, owner 2026-11-20). A name with no icon stops the build."""
    from .mech_abilities import _parse_line
    out = []
    for name, note in pairs:
        parsed = _parse_line(name)
        if not parsed or not parsed[1] or parsed[1].startswith("facet:"):
            raise ValueError(f"icons_with_notes: no icon for {name!r}")
        # the item's name in gold over its note, as the changes' tooltips (owner 2026-11-20)
        tip = f'<b class="tip-head">{_html.escape(name)}</b>{_html.escape(note)}'
        out.append(ability_chip(name, parsed[1], tip=tip))
    return "".join(out)


def illusion_excluded_table(entries):
    """[(item, what of it illusions don't apply, "item" / "neutral"), …] → a table under "Illusions still don't apply":
    an Items column and a Neutral items column, each item its icon and name, what of it on hover (owner 2026-11-20,
    7.42 Item Potency: "в столбце, а не просто через «:» … мини таблицей с двумя столбцами")."""
    # icons only, the name and what of it on hover, one row (owner 2026-11-20: "без названий … в одну строку")
    cols = {"item": [], "neutral": []}
    for name, note, kind in entries:
        cols[kind].append(icons_with_notes([(name, note)]))
    rows = [["".join(cols["item"]), "".join(cols["neutral"])]]
    html = mech_table(["Items", "Neutral items"], rows, labels=False, cls="mech-grid")
    # the table's caption over its column titles, as a list a row leads (mech-table-lead)
    lead = ('<span class="mech-abil-row"><span class="mech-cell mech-abil-line mech-table-lead">'
            "Illusions still don't apply:</span></span>")
    return re.sub(r'(<span class="mech-abils[^"]*">)', lambda m: m.group(1) + lead, html, count=1)


def marked_changes(groups):
    """groups: [(what changes, [(kind "hero" / "item", hero or item, ability or "Talents" or None, row text), …])] →
    a table: the kind of change, the icons of its abilities and items (two changes of one ability: one icon, two lines
    in its hover — owner 2026-11-20 "Chakram, Chakram Pass двумя строками в подсказке, а не двумя иконками")."""
    rows = []
    for title, items in groups:
        merged = {}
        for kind, owner, abil, text in items:
            name, src = _resolve(kind, owner, abil, text)
            merged.setdefault((kind, owner, name, src), []).append(text)
        if merged:
            rows.append([title, "".join(_chip(*k, texts) for k, texts in merged.items())])
    if not rows:
        raise ValueError("marked_changes: no changes")
    return mech_table(["Change", "Abilities and items"], rows, wide_last=True)
