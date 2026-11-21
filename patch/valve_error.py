"""A mistake in Valve's notes (a wrong "from" number, "decreased" for a value that went up): its tag glows red and
the hover says what the game files have (owner 2026-11-21: "тогда мы также свечением тег подсвечиваем только не
золотым, а красным. раньше мы писали ошибки под [?], а теперь так переделаем"). The wrong word keeps its
<span class="wrong-word">; the note leaves the [?] — its words move to the tag's hover.

Content marks such a row with note_box('This change is wrongly stated. …') / note_box('The patch text says …').
A row a card covers (class "covered", hidden under the card) keeps its note: a mark there would never be seen.

    from patch.valve_error import valve_error_tags
    html = valve_error_tags(html)
"""
import re

from .tag_glow import cut_note, each_row, has_tag, mark_tag

HEAD = "Error in the patch notes"
MARK = r"This (?:change|value) is wrongly stated|The patch text says"


def tip_text(note):
    """'This change is wrongly stated. The real change is 650 → 525' → 'Error in the patch notes. The real change is
    650 → 525'; 'The patch text says "decreased", but …' stays whole after the head."""
    text = re.sub(r"^This (?:change|value) is wrongly stated\.?\s*", "", note).strip()
    return f"{HEAD}. {text}" if text else HEAD


def _one(li):
    if re.match(r'<li[^>]*class="[^"]*\bcovered', li) or not has_tag(li):
        return li
    li2, note = cut_note(li, MARK)
    return mark_tag(li2, "valve-error", tip_text(note)) if note else li


def valve_error_tags(html):
    return each_row(html, MARK, _one)
