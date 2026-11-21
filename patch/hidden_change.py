"""A change the game files show and Valve's notes don't: its tag glows gold and says "Hidden change" on hover (owner
2026-11-21, of the mock's variants "Свечение 3, при наведении показывает Hidden Change подсказку"; the [?] alone was
not seen: "на твоих примерах не вижу, где тихие правки").

Content marks such a row with an inline note starting "Not in the patch notes" (tools/patchgen: post_cards, post_late).
The stock sentence goes away with its [?]; words of its own stay in the [?] ("It gave +35 Movement Speed before it was
cycled out.").

    from patch.hidden_change import hidden_change_tags
    html = hidden_change_tags(html)
"""
import re

TIP = "Hidden change"
_TIP = re.compile(r'<span class="info-tip" tabindex="0">\?<span class="info-pop">((?:(?!</span>).)*?Not in the patch '
                  r'notes(?:(?!</span>).)*?)</span></span>', re.S)
_STOCK = re.compile(r"\s*Not in the patch notes:\s*(?:found in the game files\.?)?\s*", re.I)


def _rest(text):
    """The note without the stock words: '' when nothing else was said."""
    rest = _STOCK.sub(" ", text).strip()
    rest = re.sub(r"^\((found in the game files)\)$|\s*\(found in the game files\)", "", rest).strip()
    return rest[:1].upper() + rest[1:] if rest else ""


def _one(li):
    m = _TIP.search(li)
    if not m or '<span class="badge ' not in li:
        return li
    rest = _rest(m.group(1))
    tip = (f'<span class="info-tip" tabindex="0">?<span class="info-pop">{rest}</span></span>' if rest else "")
    li = li[:m.start()] + tip + li[m.end():]
    return li.replace('<span class="badge ', f'<span data-tooltip="{TIP}" class="tb-tip-target hidden-change badge ', 1)


def hidden_change_tags(html):
    out, pos = [], 0
    for i in [m.start() for m in re.finditer("Not in the patch notes", html)]:
        a, b = max(html.rfind("<li ", 0, i), html.rfind("<li>", 0, i)), html.find("</li>", i)
        if a < pos or b < 0:                     # a second note in a row already done, or no row around it
            continue
        out += [html[pos:a], _one(html[a:b + 5])]
        pos = b + 5
    return "".join(out) + html[pos:]
