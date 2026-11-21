"""A change the game files show and Valve's notes don't: its tag glows gold and says "Hidden change" on hover (owner
2026-11-21, of the mock's variants "Свечение 3, при наведении показывает Hidden Change подсказку"; the [?] alone was
not seen: "на твоих примерах не вижу, где тихие правки").

Content marks such a row with an inline note starting "Not in the patch notes" (tools/patchgen: post_cards, post_late,
data/rules/hidden_rows.json). The stock sentence leaves the [?]; words of its own stay there ("It gave +35 Movement
Speed before it was cycled out."). A row a card covers keeps its note (a mark there would never be seen).

    from patch.hidden_change import hidden_change_tags
    html = hidden_change_tags(html)
"""
import re

from .tag_glow import cut_note, each_row, has_tag, mark_tag

TIP = "Hidden change"
MARK = r"Not in the patch notes"
_STOCK = re.compile(r"\s*Not in the patch notes:\s*(?:found in the game files\.?)?\s*", re.I)


def _rest(text):
    """The note without the stock words: '' when nothing else was said."""
    rest = _STOCK.sub(" ", text).strip()
    rest = re.sub(r"\s*\(found in the game files\)", "", rest).strip()
    return rest[:1].upper() + rest[1:] if rest else ""


def _one(li):
    if re.match(r'<li[^>]*class="[^"]*\bcovered', li) or not has_tag(li):
        return li
    li2, note = cut_note(li, MARK, keep=_rest)          # its own words stay in the [?]
    return mark_tag(li2, "hidden-change", TIP) if note is not None else li


def hidden_change_tags(html):
    return each_row(html, MARK, _one)
