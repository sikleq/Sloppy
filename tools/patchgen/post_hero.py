"""A hero's General list: the rows that say what the hero is first, a summary the cards below already show hidden."""
import re

_HERO_RE = re.compile(r'^\s*W\(hero_header\(')
_ATTR_ROW_RE = re.compile(r'^\s*W\(li\(attr_change\(')
_STAT_CARD_RE = re.compile(r'^\s*W\(hero_stat_card\(')
# ... and a row of what the chosen facet adds ("Aghanim's Scepter … also provides an additional level to the orb of the
# chosen facet …", 7.38 Invoker: "тоже можно убрать, в карточках это есть")
_FACETS_SUMMARY_RE = re.compile(r'^\s*W\(li\("(?:Added (?:two|three|four|five|\d+) [^"]*\bfacets\b|[^"]*\bthe chosen facet\b)')
_NEW_FACET_RE = re.compile(r'^\s*W\(new_facet\(')


def _hero_spans(lines):
    """(start, end) of each hero's lines: from its header to the next one."""
    starts = [i for i, line in enumerate(lines) if _HERO_RE.match(line)]
    return list(zip(starts, starts[1:] + [len(lines)]))


def _postprocess_attr_change_first(lines):
    """A hero's main attribute change is the first row of his General list, under the stats card that must open it
    (owner 2026-11-06: "Если герой меняет атрибут … всегда ставим вверху списка general")."""
    out = list(lines)
    for start, end in _hero_spans(lines):
        ul = next((k for k in range(start, end) if out[k].strip() == "W(ul_open())"), None)
        if ul is None:
            continue
        close = next((k for k in range(ul, end) if out[k].strip() == "W(ul_close())"), end)
        attr = next((k for k in range(ul + 1, close) if _ATTR_ROW_RE.match(out[k])), None)
        if attr is None:
            continue
        top = ul + 1 + (1 if ul + 1 < close and _STAT_CARD_RE.match(out[ul + 1]) else 0)
        if attr != top:
            out.insert(top, out.pop(attr))
    return out


def _postprocess_facets_summary_covered(lines):
    """"Added three orb-centered facets. Each provides …" says what the hero's new facet cards below show one by one:
    the row hides under them, its tag kept for the filters (owner 2026-11-06, 7.38 Invoker: "эта строка тогда не нужна,
    т.к мы всё карточками показали")."""
    out = list(lines)
    for start, end in _hero_spans(lines):
        facets = [k for k in range(start, end) if _NEW_FACET_RE.match(out[k])]
        if len(facets) < 2:
            continue
        for k in range(start, facets[0]):              # the General rows, above the facets
            if _FACETS_SUMMARY_RE.match(out[k]) and "covered=True" not in out[k]:
                out[k] = re.sub(r"\)\)\s*$", ", covered=True))", out[k])
    return out
