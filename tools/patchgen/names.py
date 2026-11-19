"""Names in a row's words: the items and abilities with an icon, a summon's owner (7.42 proofread)."""
import re

def _py_str(s):
    """A Python string literal of s (as post_stats._py_str; here so general.py needs no import of post_stats)."""
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


_NAME_RUN_RE = re.compile(r"[A-Z][\w'’-]*(?: (?:of|the|[A-Z0-9][\w'’-]*))*")


def _named_icons(text):
    """{words of the row: the item / ability they name} for every name with an icon (a plural "Voodoo Masks" as its
    item; the longest run of capitalised words first, then shorter ones from its start)."""
    from patch.mech_abilities import mech_example
    found = {}
    for run in _NAME_RUN_RE.findall(text):
        words, start = run.split(), 0
        while start < len(words):                     # "Tier 4 Evolved Enchantment": the name may start inside
            hit = None
            # a name inside a run is two words or more: "Spell Lifesteal" is a stat, not the Lifesteal icon
            shortest = start + (2 if start else 1)
            for n in range(len(words), shortest - 1, -1):
                phrase = " ".join(words[start:n])
                for name in (phrase, phrase[:-1] if phrase.endswith("s") else None):
                    if not name or len(name) < 4:
                        continue
                    try:
                        mech_example(name)
                    except ValueError:
                        continue
                    hit = (phrase, name, n)
                    break
                if hit:
                    break
            if hit:
                found[hit[0]] = hit[1]
                start = hit[2]
            else:
                start += 1
    return found


_POSSESSIVE_RE = re.compile(r"^(?P<owner>[A-Z][\w .'-]*?)(?:'s|’s|'|’) (?P<what>[A-Z].*)$")


def _owner_form(line):
    """"Gyrocopter's Homing Missile" → "Gyrocopter: Homing Missile", the form the lists' table reads as hero | ability
    with their icons (owner 2026-11-19: the Pip Health list was a column of words, "не как другие — иконками и ряды
    столбцов"); a creep's too ("Radigull's Eggstremism"). An item's own name ("Roshan's Banner") stays."""
    from patch.images import HERO_SLUG
    from patch.mech_abilities import _creep_prefix, _item_icon
    m = _POSSESSIVE_RE.match(line)
    if not m or _item_icon(line):
        return line
    owner = m.group("owner")
    return f"{owner}: {m.group('what')}" if owner in HERO_SLUG or _creep_prefix(owner) else line
