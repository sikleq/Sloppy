"""One row the hero's abilities share, each with its own [?] ("Added values for levels 9 and 10", 7.38 Invoker): one block
with all their icons, where the first of them stood; the row leaves every ability's own block, a block it leaves empty
goes (owner 2026-11-06: "все способности можно указать и убрать соответствующую строку у каждой из них. Те способности,
что получали ещё изменения оставить … Поставить строку со всеми способностями после Exort блока")."""
import re

from .notes import _LEVELS_OF_RE, _ROW_NOTE_RE

SHARED_LEAST = 3                   # a row two abilities share stays in each (merging neighbours is notes' own rule)
_HERO_RE = re.compile(r'^\s*W\(hero_header\(')
_ONE_RE = re.compile(r'^(\s*)W\(ability\("([^"]+)", slug="([^"]+)"\)\)\s*$')
_GROUP_RE = re.compile(r'^(\s*)W\(ability_group\((.*)\)\)\s*$')
_PAIR_RE = re.compile(r'\("([^"]+)", "([^"]+)"\)')


def _blocks(lines, start, end):
    """(header index, close index, [(name, slug)], merged) of the plain ability blocks in lines[start:end]."""
    out, k = [], start
    while k < end:
        one, group = _ONE_RE.match(lines[k]), _GROUP_RE.match(lines[k])
        if (one or group) and k + 1 < end and lines[k + 1].strip() == "W(ul_open())":
            close = next((j for j in range(k + 2, end) if lines[j].strip() == "W(ul_close())"), None)
            if close is not None:
                pairs = [(one.group(2), one.group(3))] if one else _PAIR_RE.findall(group.group(2))
                out.append((k, close, pairs, bool(group)))
                k = close + 1
                continue
        k += 1
    return out


def _postprocess_shared_row_group(lines):
    out = list(lines)
    starts = [i for i, line in enumerate(out) if _HERO_RE.match(line)]
    for start, end in reversed(list(zip(starts, starts[1:] + [len(out)]))):
        blocks = _blocks(out, start, end)
        found = {}                                   # the row's words -> [(block, row index, note)]
        for blk in blocks:
            for j in range(blk[0] + 2, blk[1]):
                m = _ROW_NOTE_RE.match(out[j])
                if m:
                    found.setdefault(m.group(1).strip(), []).append((blk, j, m.group(2)))
        base, hits = next(((b, h) for b, h in found.items()
                           if sum(len(blk[2]) for blk, _j, _n in h) >= SHARED_LEAST and len(h) >= 2), (None, None))
        if not base:
            continue
        pairs, notes = [], []
        for blk, _j, note in hits:
            pairs += blk[2]
            notes += (note.split("<br>") if blk[3] else
                      [f"{blk[2][0][0]}: " + _LEVELS_OF_RE.sub(r"\1 (\2) \3", line) for line in note.split("<br>")])
        ind = re.match(r"\s*", out[hits[0][0][0]]).group(0)
        merged = "<br>".join(notes)
        names = ", ".join('("%s", "%s")' % pair for pair in pairs)
        group = [f"{ind}W(ability_group({names}))", f"{ind}W(ul_open())",
                 f'{ind}{base}, extra=inline_note("{merged}")))', f"{ind}W(ul_close())"]
        drop = set()
        for blk, j, _note in hits:
            drop.add(j)
            left = [r for r in range(blk[0] + 2, blk[1]) if r not in drop and out[r].strip().startswith("W(li(")]
            if not left:                             # the block said nothing else: it goes, with its markers
                drop.update(range(blk[0], blk[1] + 1))
        first = hits[0][0][0]
        out = [line for k, line in enumerate(out[:first]) if k not in drop] + group + \
              [line for k, line in enumerate(out[first:], first) if k not in drop]
    return out
