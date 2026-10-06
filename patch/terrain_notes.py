"""What a terrain note is about, in its own words — shared by the site (patch/elements.py, builders/terrain.py) and
the picture maker (scripts/gen/terrain_shots.py).

- show_keys(text): the map-object keys a note's pictures outline — its FIRST object word.
- note_phrase(text): the words naming that object ("tier 1 safe lane towers", "several trees", "medium flooded
  camp", "Tormentor spawn areas"); the row shows them as the button that opens its pictures (the owner 2026-10-03:
  "no Show buttons in the tags' place — the screenshot opens from the name of the objective that moved, and the rows
  are just numbered instead of tag chips").
- wrap_phrase(html, phrase, button): the row's html with the first plain-text occurrence of the phrase made a button.
"""
import re

# the note's subject = its FIRST object word; ground words (cliff, ramp, stream…) name no object to outline
SUBJECTS = (
    (r"\bcamps?\b|\bspawn ?box", ("camps", "camptiers", "boxes")),
    (r"\btrees?\b|\bjuke paths?\b", ("trees",)),
    (r"\bwatchers?\b", ("watchers",)),
    (r"\btowers?\b|\btier [1-4]\b", ("towers",)),
    (r"\blotus", ("lotus",)),
    (r"\btwin gates?\b", ("twinGates",)),
    (r"\btormentors?\b", ("tormentors",)),
    (r"\bbounty runes?\b", ("bounty",)),
    (r"\broshan pits?\b", ("roshan",)),
    (r"\bwisdom shrines?\b", ("wisdom",)),
    (r"\boutposts?\b", ("outposts",)),
    # the lane creeps' walk (2026-10-06, map file path_corner chains): 7.38c "The Top Lane creep paths have been
    # slightly adjusted", 7.40 "… paths and spawn points of the Radiant Offlane lane creeps"
    (r"\b(?:lane )?creep paths?\b|\blane creeps?\b", ("lanes",)),
    # the ground itself as the subject: no outlines, the two pictures show it ("The ramp … Roshan Pit", "The cliff
    # above the … camp", "the entrance to the bridge by the Lotus pools")
    (r"\b(?:cliffs?|ramps?|streams?|paths?|entrances?|areas?|rim|bridge|high ground|low ground)\b", ()),
)

# words a phrase never takes in: articles, sides, verbs, prepositions, conjunctions ("Removed | several trees |
# from", "The | medium flooded camp | near", "Radiant | safe lane small camp | has")
_STOP = set("""
a an the this that these those its their it radiant dire
has have had been be being is are was were now no longer can could will would may might should must also only
removed added moved adjusted rotated increased decreased reduced extended shifted lowered raised replaced made
changed demoted promoted swapped relocated repositioned reworked converted turned opened closed blocked
from to of near nearest closest closer next between by at in on with for behind above below under into onto
toward towards around across along beside inside outside over through and or but which so such than as
very much more less further again away back up down north south east west
""".split())
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’-]*")
_MAX_LEFT, _MAX_RIGHT = 5, 3


def _subject(text):
    """(start, end, keys) of the earliest subject word, or None."""
    best = None
    for rx, keys in SUBJECTS:
        m = re.search(rx, text, re.I)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), m.end(), keys)
    return best


def show_keys(text):
    """The map-object keys a note is about: those of its first object word ('Removed several trees from the …
    pull camp' -> trees only; 'The Large camp nearest to Tier 3 towers …' -> camps only); none for a ground note."""
    best = _subject(text)
    return set(best[2]) if best else set()


def note_phrase(text):
    """The words naming what the note is about: the subject word with the words around it that describe it — to the
    left back to an article, a side, a verb or a preposition, to the right up to one ("Tormentor | spawn areas |
    have"; a participle — "leading", "moved" — ends it too). '' when the note names nothing."""
    best = _subject(text)
    if not best:
        return ""
    words = list(_WORD.finditer(text))
    first = next((i for i, w in enumerate(words) if w.end() > best[0]), None)
    last = next((i for i, w in reversed(list(enumerate(words))) if w.start() < best[1]), None)
    if first is None or last is None:
        return ""

    def joined(a, b):        # nothing but spaces between the words (a comma or a bracket ends the phrase)
        return text[words[a].end():words[b].start()].strip() == ""
    def stop(w):             # "slightly", "now" … end it on both sides
        return w in _STOP or w.endswith("ly")
    lo = first
    while lo > 0 and first - lo < _MAX_LEFT and not stop(words[lo - 1].group().lower()) and joined(lo - 1, lo):
        lo -= 1
    hi = last
    while hi + 1 < len(words) and hi - last < _MAX_RIGHT and joined(hi, hi + 1):
        w = words[hi + 1].group().lower()
        if stop(w) or w.endswith(("ed", "ing")):
            break
        hi += 1
    return text[words[lo].start():words[hi].end()]


def wrap_phrase(html, phrase, button):
    """html with the first occurrence of `phrase` in its text (not inside a tag) replaced by button(phrase); None
    when the text doesn't hold it as one run (split by markup)."""
    if not phrase:
        return None
    for m in re.finditer(r"(?<![\w'’-])" + re.escape(phrase) + r"(?![\w'’-])", html):
        before = html[:m.start()]
        if before.rfind("<") <= before.rfind(">"):          # not inside a tag's attributes
            return html[:m.start()] + button(phrase) + html[m.end():]
    return None
