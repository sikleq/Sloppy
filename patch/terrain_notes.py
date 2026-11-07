"""What a terrain note is about, in its own words — shared by the site (patch/elements.py, builders/terrain.py) and
the picture maker (scripts/gen/terrain_shots.py).

- show_keys(text): the map-object keys a note's pictures outline — its FIRST object word.
- note_phrase(text): the words naming that object ("tier 1 safe lane towers", "several trees", "medium flooded
  camp", "Tormentor spawn areas"); the row shows them as the button that opens its pictures (the owner 2026-10-03:
  "no Show buttons in the tags' place — the screenshot opens from the name of the objective that moved, and the rows
  are just numbered instead of tag chips").
- wrap_phrase(html, phrase, button): the row's html with the first plain-text occurrence of the phrase made a button.
- terrain_note / terrain_button / terrain_num_chip: a terrain row's pictures, its button and its number chip (cut out
  of elements.py, 2026-11-07).
"""
import json as _json
import os as _os
import re

from .state import page_cache

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


_TERRAIN_SPOTS = None


# (patch, row text) -> [how many such rows this page drew]: the n-th of two same-worded rows takes the n-th spot
_TSPOT_SEEN: dict = page_cache({})


def _terrain_spot_index():
    """{patch: [(match, [picture file names])]} from data/terrain_spots.json, the pictures numbered in file order the
    way scripts/gen/terrain_shots.py writes them (icons/terrain/<code>_<i>.webp)."""
    global _TERRAIN_SPOTS
    if _TERRAIN_SPOTS is None:
        root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        try:
            with open(_os.path.join(root, "data", "terrain_spots.json"), encoding="utf-8") as f:
                raw = _json.load(f)
        except (OSError, ValueError):
            raw = {}
        _TERRAIN_SPOTS = {}
        for patch, entries in raw.items():
            if patch.startswith("_"):
                continue
            code, i, rows = patch.replace(".", ""), 0, []
            for e in entries:
                n = len(e.get("spots", []))
                names = [f"{code}_{k}.webp" for k in range(i, i + n)
                         if _os.path.exists(_os.path.join(root, "icons", "terrain", f"{code}_{k}.webp"))]
                rows.append((e["match"], names, e.get("phrase") or note_phrase(e["match"]), bool(e.get("part"))))
                i += n
            _TERRAIN_SPOTS[patch] = rows
    return _TERRAIN_SPOTS


TSHOT_W, TSHOT_H = 480, 238        # a note picture's css size (files: 360-px halves + a 6-px gap, 726 x 360)


def terrain_note(patch, text, prefix="../"):
    """(phrase, pictures) of a terrain note (the owner 2026-10-03: the terrain rows were "all under one tag, mush —
    maybe micro-screenshots"): the old | new map squares around the change, only the note's own objects outlined,
    in their own rounded, centred box under the row (hidden, so the lazy pictures load only when opened); a click on
    one opens its large copy (<name>_lg.webp, data-large) over the page — the section's "View on map" button is the
    way to the Terrain page. The phrase — the words naming the note's object ("tier 1 safe lane towers", spot
    "phrase" or patch.terrain_notes.note_phrase) — becomes the button that opens them (terrain_button; the owner
    2026-10-03: "no Show buttons in the tags' place: the screenshot opens from the name of the objective that
    moved"). ('', '') for any other row."""
    if not patch or not isinstance(text, str):
        return "", ""
    plain = re.sub(r"<[^>]+>", "", text).strip()

    def imgs(names):
        return "".join(
            f'<img src="{prefix}icons/terrain/{n}" data-large="{prefix}icons/terrain/{n[:-5]}_lg.webp" '
            f'width="{TSHOT_W}" height="{TSHOT_H}" alt="The old and the new map here" loading="lazy" '
            f'decoding="async">' for n in names)
    every = [s for s in _terrain_spot_index().get(patch, []) if plain.startswith(s[0])]
    # one row, a picture under each of its words (owner 2026-10-28, 7.38 "Touched up the map in general. Slightly
    # adjusted neutral camps, trees, and cliffs"): entries with "part" — a tuple of phrases, a box per phrase
    parts = {}                                     # phrase -> its pictures, in file order (one entry per spot / scale)
    every = [tuple(s) + (False,) * (4 - len(s)) for s in every]     # (match, names, phrase, part)
    for s in every:
        if s[3] and s[1]:
            parts.setdefault(s[2], []).extend(s[1])
    if parts:
        return (tuple(parts),
                "".join(f'<span class="tshots" data-part="{k}" hidden>{imgs(names)}</span>'
                        for k, names in enumerate(parts.values())))
    # the same words in two sections of a patch (7.38c "Several additional tree and visual adjustments have been made
    # to this area", Dire Safe Lane Jungle and Bottom Lane): the n-th such row takes the n-th spot that matches
    seen = _TSPOT_SEEN.setdefault((patch, plain), [0])
    nth, seen[0] = seen[0], seen[0] + 1
    hits = [s for s in every if not s[3]]
    for _match, names, phrase, _part in hits[nth:nth + 1] if len(hits) > 1 or nth == 0 else []:
        if names:
            return phrase, f'<span class="tshots" hidden>{imgs(names)}</span>'
    return "", ""


def terrain_button(html, phrase):
    """The row's html with its phrase as the pictures' button (unchanged, with a warning, when markup splits it).
    A tuple of phrases (terrain_note "part" entries): each its own button, opening the box of its own number."""
    if isinstance(phrase, tuple):
        for k, p in enumerate(phrase):
            out = wrap_phrase(html, p, lambda w, k=k: f'<button type="button" class="tshots-btn" data-part="{k}" '
                                                      f'aria-expanded="false">{w}</button>')
            if out is None:
                print(f"  [warn] terrain note: {p!r} not found in its row — its pictures have no button")
            else:
                html = out
        return html
    out = wrap_phrase(html, phrase,
                      lambda p: f'<button type="button" class="tshots-btn" aria-expanded="false">{p}</button>')
    if out is None:
        print(f"  [warn] terrain note: {phrase!r} not found in its row — its pictures have no button")
        return html
    return out


def terrain_num_chip(n, badge=""):
    """A terrain row's chip: its number in its category, in the tag chip's frame (the owner 2026-10-03: "the rows
    are just numbered instead of tag chips"). A row with a % (its b() badge: buff / nerf) tints the chip lightly in
    that colour (owner 2026-10-27, 7.40 "Watcher night vision range decreased from 800 to 450")."""
    m = re.search(r'class="badge (buff|nerf)\d', badge or "")      # a b() badge's % tier, not a t() tag
    tone = f" tnum-{m.group(1)}" if m else ""
    return f'<span class="badge tnum{tone}">{n}</span>'
