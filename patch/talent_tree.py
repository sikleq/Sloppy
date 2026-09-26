"""Talent tree icon with the changed branches in gold (owner 2026-09-26).

In the game the talent tree lights the left or right twig of every level (10/15/20/25) that was
taken. Here the same twigs light up for the talents a patch changed. The side comes from the
hero's KV of that patch: first 8 talent slots go in pairs per level, and the first of each pair
is the RIGHT twig (data/rules/talent_slots.json, built by tools/build_talent_slots.py).

A row is placed by matching its words against the two talents of its level (tooltip names from
data/abilities_english.txt); a row that matches neither side clearly lights nothing.
"""
import html as _html
import json
import os
import re

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = (10, 15, 20, 25)

# Clip polygons of the 8 twigs in talents.svg's 73x77 viewBox (checked on a 10x render).
BRANCH_POLYS = {
    "10l": "10,53 25,53 34.4,59.5 34.4,66 10,59",
    "10r": "63,53 48,53 38.6,59.5 38.6,66 63,59",
    "15l": "6,36 20,40 34.4,43 34.4,49.5 16,49.5 5,40",
    "15r": "67,36 53,40 38.6,43 38.6,49.5 57,49.5 68,40",
    "20l": "11,21 20,24 34.4,31 34.4,38 15,35.5 9.5,27",
    "20r": "62,21 53,24 38.6,31 38.6,38 58,35.5 63.5,27",
    "25l": "21,8 27,8 33,19 36.5,21 36.5,24.5 27,24.5 20.5,16",
    "25r": "52,8 46,8 40,19 36.5,21 36.5,24.5 46,24.5 52.5,16",
}

_STOP = {"talent", "level", "bonus", "the", "and", "with", "per", "for", "from", "now", "replaced",
         "increased", "decreased", "reduced", "rescaled", "changed", "swapped", "also", "its", "has",
         "when", "that", "this", "into", "longer", "instead", "seconds", "second"}
_WORD_RE = re.compile(r"[a-z][a-z']{2,}")
_LEVEL_RE = re.compile(r"\bLevel\s+(10|15|20|25)(?:\s+Talent)?\s*:?", re.I)
_TAG_RE = re.compile(r"<[^>]+>")

_slots_doc = None
_tooltips = None
_slots_cache = {}


def _data():
    global _slots_doc
    if _slots_doc is None:
        with open(os.path.join(_HERE, "data", "rules", "talent_slots.json"), encoding="utf-8") as f:
            _slots_doc = json.load(f)
    return _slots_doc


def _all_versions():
    return _data()["versions"]


def _tooltip_words():
    global _tooltips
    if _tooltips is None:
        _tooltips = {}
        path = os.path.join(_HERE, "data", "abilities_english.txt")
        rx = re.compile(r'"DOTA_Tooltip_ability_(special_bonus_[a-z0-9_]+)"\s*"([^"]*)"', re.I)
        with open(path, encoding="utf-8", errors="replace") as f:
            for m in rx.finditer(f.read()):
                _tooltips[m.group(1).lower()] = _words(re.sub(r"\{[^}]*\}", " ", m.group(2)))
    return _tooltips


def _words(text):
    return {w.strip("'") for w in _WORD_RE.findall((text or "").lower())} - _STOP


def talent_slots(version, hero):
    """{level: (right_words, left_words)} of that version, or {}. A talent's words = today's tooltip
    name + the hint of its own patch (ability it changes + value key), because a reused slug can
    mean something else today."""
    key = (version, hero)
    if key not in _slots_cache:
        vers = _all_versions()
        idx = vers.index(version) if version in vers else -1
        run = None
        for r in _data()["heroes"].get(hero, []):
            if idx >= 0 and vers.index(r[0]) <= idx:
                run = r
        slots = {}
        if run:
            words = [_slug_words(s) | _words(h) for s, h in zip(run[1], run[2])]
            slots = {lvl: (words[2 * i], words[2 * i + 1]) for i, lvl in enumerate(LEVELS)}
        _slots_cache[key] = slots
    return _slots_cache[key]


def _slug_words(slug):
    tips = _tooltip_words()
    if slug in tips:
        return tips[slug]
    base = re.sub(r"_\d+$", "", slug)                        # special_bonus_strength_15 -> _strength
    for k, w in tips.items():
        if k == base or re.sub(r"_\d+$", "", k) == base:
            return w
    return set()


def _pick_side(words, pair):
    """'r' / 'l' when the row shares more words with one talent of the pair, else None."""
    if not words:
        return None
    r, l = (len(words & tw) for tw in pair)
    if r == l:
        return None
    return "r" if r > l else "l"


def _segments(text):
    """(level, words of the talent this row is about) for every 'Level N Talent' in the row.
    For 'A replaced with B' the NEW talent B is the one in this patch's KV."""
    marks = list(_LEVEL_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        seg = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        now = re.split(r"\breplaced (?:with|by)\b", seg, flags=re.I)
        ch = re.search(r"\bchanged from\b(.*)\bto\b(.*)$", seg, re.I)
        if len(now) == 1 and ch and _words(ch.group(2)):      # "changed from X to Y" = replaced
            now = [ch.group(1), ch.group(2)]
        out.append((int(m.group(1)), _words(now[-1]), _words(now[0]) if len(now) > 1 else None))
    return out


def changed_branches(version, hero, row_texts):
    """Set like {'10r', '15r'} of the twigs these talent rows changed."""
    vers = _all_versions()
    if version not in vers:
        return set()
    slots = talent_slots(version, hero)
    prev = vers[vers.index(version) - 1] if vers.index(version) > 0 else None
    old_slots = talent_slots(prev, hero) if prev else {}
    lit = set()
    for text in row_texts:
        for lvl, now_words, old_words in _segments(_TAG_RE.sub(" ", _html.unescape(text))):
            side = _pick_side(now_words, slots[lvl]) if lvl in slots else None
            if side is None and old_words is not None and lvl in old_slots:
                side = _pick_side(old_words, old_slots[lvl])          # the replaced talent's slot
            if side is None and lvl in old_slots and old_words is None:
                side = _pick_side(now_words, old_slots[lvl])          # a removed talent
            if side:
                lit.add(f"{lvl}{side}")
    return lit


def tree_svg(icon_url, gold_url, lit, uid):
    """Inline SVG: the official icon (dimmed) with each changed twig overlaid from its gold copy.
    One gold layer per twig (data-b), so scripts.js can light only the twigs of the rows a filter
    leaves visible (owner 2026-09-26: with SWAP on, a hidden NERF row's twig still glowed)."""
    title = ", ".join(f"level {k[:2]} {'left' if k[2] == 'l' else 'right'}" for k in sorted(lit))
    clips = "".join(f'<clipPath id="{uid}-{k}"><polygon points="{BRANCH_POLYS[k]}"/></clipPath>' for k in sorted(lit))
    golds = "".join(f'<image class="ttree-on" data-b="{k}" href="{gold_url}" width="73" height="77" '
                    f'clip-path="url(#{uid}-{k})"/>' for k in sorted(lit))
    return (f'<svg class="ability-icon-img ttree" viewBox="0 0 73 77" width="128" height="128" role="img" '
            f'aria-label="Talent tree, changed: {title}"><defs>{clips}</defs>'
            f'<image class="ttree-base" href="{icon_url}" width="73" height="77"/>{golds}</svg>')


_BLOCK_RE = re.compile(
    r'(<div class="ability-block talents-block"><div class="ability-icon-wrap">)(<img [^>]*src="([^"]*talents\.svg)"[^>]*>)'
    r'(</div>\s*<ul class="changes">)(.*?)(</ul>)', re.S)
_HERO_RE = re.compile(r'class="entity hero-entity"[^>]*>\s*<div class="entity-icon hero-icon">.*?/heroes/([a-z0-9_]+)\.(?:webp|png)"', re.S)
_ROW_RE = re.compile(r'<span class="row-text">(.*?)</span>', re.S)
_LI_RE = re.compile(r'<li\b([^>]*)>(.*?)</li>', re.S)


def light_talent_trees(html, version):
    """Patch page post-pass: every Talents block whose rows changed a known twig gets the tree
    with those twigs in gold. Blocks with nothing placed keep the plain icon."""
    heroes = [(m.start(), m.group(1)) for m in _HERO_RE.finditer(html)]
    n = [0]

    def repl(m):
        hero = None
        for pos, h in heroes:
            if pos > m.start():
                break
            hero = h
        if not hero:
            return m.group(0)
        lit = set()

        def tag_li(li):
            row = _ROW_RE.search(li.group(2))
            own = changed_branches(version, hero, [row.group(1)]) if row else set()
            if not own:
                return li.group(0)
            lit.update(own)
            return f'<li{li.group(1)} data-tt="{" ".join(sorted(own))}">{li.group(2)}</li>'

        rows = _LI_RE.sub(tag_li, m.group(5))
        if not lit:
            return m.group(0)
        n[0] += 1
        icon = m.group(3)
        gold = icon.replace("talents.svg", "talents_gold.svg")
        uid = f"tt-{version.replace('.', '_')}-{hero}-{n[0]}"
        return m.group(1) + tree_svg(icon, gold, lit, uid) + m.group(4) + rows + m.group(6)

    return _BLOCK_RE.sub(repl, html)
