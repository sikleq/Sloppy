"""The changes a General block sums up, as a table of icons (owner 2026-11-20, 7.42 Spell Power Reduction: Valve's three
sentences and "Specifics … can be found in the corresponding ability or item notes"; the rows they mean are the ones
marked "As a part of the comprehensive Spell Power Reduction"). Each icon names its change on hover and jumps to its
hero or item."""
import re

from .mech_abilities import _icon, _item_icon, ability_chip, mech_table

_TALENT_RE = re.compile(r"^Level \d+ Talent (.+)$")


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


def _chip(kind, owner, abil, text):
    from .elements import _slugify
    if kind == "item":
        src, name = _item_icon(owner), owner
    else:
        name = abil if abil and abil != "Talents" else _talent_ability(owner, text)
        src = _icon(owner, name) if name else None
        if not src and abil == "Talents":     # a talent of no one ability ("Spell Area of Effect"): the talent tree
            from .elements import TALENT_ICON_URL
            src, name = TALENT_ICON_URL, "Talent"
    if not src:
        # a change without its icon would silently drop out of the count the row shows
        raise ValueError(f"marked_changes: no icon for {owner} / {abil}: {text[:60]!r}")
    return (f'<a class="mech-jump" href="#dyn-{kind}-{_slugify(owner)}">'
            f'{ability_chip(f"{owner}, {name}: {text}" if kind == "hero" else f"{owner}: {text}", src)}</a>')


def marked_changes(groups):
    """groups: [(what changes, [(kind "hero" / "item", hero or item, ability or "Talents" or None, row text), …])] →
    a table: the kind of change with its count, the icons of its changes."""
    rows = [[f"{title} <b>{len(items)}</b>", "".join(_chip(*it) for it in items)] for title, items in groups if items]
    if not rows:
        raise ValueError("marked_changes: no changes")
    return mech_table(["Change", "Abilities and items"], rows, wide_last=True)
