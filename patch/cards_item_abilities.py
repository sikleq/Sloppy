"""Item ability cards: item_abilities_change() and render_iab_card() — the old / new panes of an item's abilities, their meta chips (cooldown, mana, cast range), the marked numbers and the rows a card covers. Split out of patch/elements.py (audit 2026-10-26 #8)."""

import difflib
import html as _html
import re

from .state import _State, page_cache
from .elements import _number_tip, hl


# ---- An item's ability described in a row: a light header like the game's item tooltip ----
# Owner 2026-09-27: "Active: Bottoms Up. Restores 60 Mana ... Cast Range: 650. No Mana Cost. Cooldown: 40s"
# -> header [Active: Bottoms Up ....... (range) 650  (cooldown) 40], the description below with every
# number bold and a bit brighter. Icons are the game's own (pak01 panorama/images/status_icons/
# ability_*_icon_psd -> icons/ui/ability/*.png). Only an item's description rows (no change tag / NEW).
_ITEM_ABILITY_RE = re.compile(r'^\s*(Passive|Active|Toggle|Aura|Ability|Use)\s*:\s*(.*)$', re.S)


_IAB_N = r"\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*"


_IAB_META = (  # (key, icon, pattern of a whole sentence) — header order: radius, then the game's range, cost, cooldown
    ("aoe", "aoe", rf"Radius\s*:?\s*({_IAB_N})"),              # owner 2026-09-27: the radius goes to the header too
    ("castrange", "castrange", rf"(?:Cast )?Range\s*:?\s*({_IAB_N})"),   # 7.38 Boglet: "Range: 275"
    ("manacost", "manacost", rf"Mana Cost\s*:?\s*({_IAB_N}%?)"),
    ("healthcost", "healthcost", rf"Health Cost\s*:?\s*({_IAB_N}%?)"),
    ("cooldown", "cooldown", rf"(?:Cooldown\s*:?\s*({_IAB_N})s?|({_IAB_N})s\s+Cooldown)"),
)


_IAB_DROP = r"No Mana Cost|No Cooldown"


_IAB_BOLD_LABEL_RE = re.compile(r"<b>\s*((?:Cast )?Range|Radius|Mana Cost|Health Cost|Cooldown)\s*:\s*</b>")


_IAB_SMALL = {"of", "the", "a", "an", "and", "to", "in", "on", "for", "with", "from"}


# a multiplier "0.25x" is one number; never stop at its decimal point (7.39 Sister's Shroud showed a bold "0" + ".25x")
_IAB_NUM_RE = re.compile(r"(?<![\w#&.])([+\-]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*%?s?x?)(?![\w%]|\.\d)")


ABILITY_ICON_DIR = "../icons/ui/ability/"


def _iab_name(body):
    """("Bottoms Up", rest) when the body starts with an ability name sentence, else ("", body)."""
    m = re.match(r"^(.{1,40}?)([.!])\s+(?=[A-Z0-9+\--])(.*)$", body, re.S)   # U+E00x: highlight markers
    if not m:
        return "", body
    words = m.group(1).replace(",", " ").split()
    if not words or len(words) > 5 or not all(w[:1].isupper() or w.lower() in _IAB_SMALL for w in words):
        return "", body
    name = m.group(1) + ("!" if m.group(2) == "!" else "")
    return name, m.group(3)


def _iab_bold_numbers(html_text):
    """Every number outside tags / tooltip markers -> <b class="iab-num">."""
    out = []
    for part in re.split(r"(<!--TIP-->.*?<!--/TIP-->|<[^>]+>)", html_text, flags=re.S):
        if part.startswith("<"):
            out.append(part)
        else:
            out.append(_IAB_NUM_RE.sub(r'<b class="iab-num">\1</b>', part))
    return "".join(out)


def iab_attach_tail(html, cluster):
    """Put a (?)/(i) cluster right after the LAST word of the description, in one no-wrap span, so the
    icon never drops alone onto an empty line (owner 2026-09-27, Revenant's Brooch 7.38)."""
    if not cluster:
        return html
    end = html.rfind("</span>")                               # the end of .iab-desc
    body = html[:end]
    mw = re.search(r"(\S+)\s*$", body)
    if mw and "<" not in mw.group(1) and ">" not in mw.group(1):
        body = body[:mw.start(1)] + f'<span class="li-tail">{mw.group(1)}{cluster}</span>'
    else:
        body = body.rstrip() + f' <span class="li-tail">{cluster}</span>'
    return body + html[end:]


def _item_ability_html(text, props=None):
    """The header + description html of an item ability row, or None when the text doesn't fit. `props`: the
    ability's own values from the game files (patch/ability_kv.py) — they fill the header where the text is silent
    (7.38 Riverborn Aura "All allies within a 1200 range" = its 1200 radius)."""
    tips = []
    while isinstance(text, str) and text.rstrip().endswith("<!--/TIP-->"):   # trailing (?) tips ride along
        i = text.rfind("<!--TIP-->")
        if i < 0:
            break
        tips.insert(0, text[i:].strip())
        text = text[:i].rstrip()
    m = _ITEM_ABILITY_RE.match(text)
    if not m or "<!--" in text or "<div" in text:
        return None
    if tips:
        html = _item_ability_html(text, props)
        return iab_attach_tail(html, "".join(tips)) if html and "iab-desc" in html else None
    kind, body = m.group(1), m.group(2).strip()
    name, desc = _iab_name(body)
    values, desc = _iab_take_meta(desc)
    # "Active: Name"; without a name just "Passive", as an ability card's header (owner 2026-09-30)
    title = (f'<b class="iab-kind">{kind}:</b> <span class="iab-name">{name}</span>' if name
             else f'<b class="iab-kind">{kind}</b>')
    head = (f'<span class="iab-head"><span class="iab-title">{title}</span>'
            f'<span class="iab-meta">{_iab_meta_chips(values, props)}</span></span>')
    return head + (f'<span class="iab-desc">{_iab_bold_numbers(desc)}</span>' if desc else "")


def _iab_meta_re(pat):
    # a whole sentence, "." or "," separated ("Cast Range: 550, Mana Cost: 90, Cooldown: 16s" — 7.38 Marshmage)
    # A sentence ended by "." may be followed by a tag: "Radius: 1500. <b>Max Mana Restored:</b> …" (7.41 Death Charge);
    # any may be followed by its (?) note: "Cast Range: 750 (?)" (7.38 Weighted Pie)
    return rf"(?:^|(?<=[.!,]))\s*(?:{pat})(?:\s*[.,]?\s*(?=$|[A-Z]|<!--INLINETIP-->)|\s*\.\s*(?=<))"


# the value of a header sentence highlighted in the text: "Cooldown: <hl nerf>45/40/35/30s</hl>." (7.41 Summon Hawk) —
# the header takes it with its colour
_IAB_HL_LABEL = {"aoe": "Radius", "castrange": "(?:Cast )?Range", "manacost": "Mana Cost", "healthcost": "Health Cost",
                 "cooldown": "Cooldown"}


_IAB_HL_VALUE = rf'(\s*:\s*)<span class="iab-hl iab-hl-(\w+)">({_IAB_N}%?s?)</span>'


_IAB_HL_ANY_RE = re.compile(rf'\b({"|".join(_IAB_HL_LABEL.values())}){_IAB_HL_VALUE}')


_IAB_HL_MARK_RE = re.compile(r'^<span class="iab-hl iab-hl-(\w+)">(.*)</span>$', re.S)


def _iab_unhl(text):
    """The text with the highlight taken off every header sentence's value (to count those sentences)."""
    return _IAB_HL_ANY_RE.sub(r"\1\2\4", text)


def _iab_meta_chips(values, props=None, marks=None):
    """The header's icon + value chips in the game's order; the game files' value wins over the text's. marks:
    {key: "buff" / "nerf"} — a value the old / new card pair changed is coloured like the cards' text (owner 2026-10-24)."""
    out = []
    for key, icon, _ in _IAB_META:
        val = (props or {}).get(key) or values.get(key)
        own = _IAB_HL_MARK_RE.match(values.get(key) or "")
        if val and own:                        # the text's own highlight on the value wins (it says the change)
            val = hl(_IAB_HL_MARK_RE.sub(r"\2", str(val)), own.group(1))
        elif val and marks and key in marks:
            # coloured only if a row under the card says exactly this change (page.save_html, _CARD_CONFIRMED):
            # a header difference no row names (Kinetic Fence 7.41 mana 50 -> 70) stays plain
            mark, card, old = (tuple(marks[key]) + (None,))[:3]
            # the new side's value carries the old one: the % on hover, as the cards' numbers (owner 2026-10-25,
            # 7.41 Noxious Plague mana 200/300/400 -> 200/250/300 was dotted with no %)
            old = re.sub(r"[^\d./%+\-]", "", re.sub(r"<[^>]+>", "", str(old))) if old else ""
            val = f"<!--CHIPMARK:{card}:{key}:{mark}:{old}-->{val}<!--/CHIPMARK-->"
        if val:
            out.append(f'<span class="iab-m"><img class="iab-ico" src="{ABILITY_ICON_DIR}{icon}.png" alt="">{val}</span>')
    return "".join(out)


_CARD_CONFIRMED: set = page_cache(set())  # (card id, header key) a row under the card confirmed


_CARD_SEQ = page_cache([0])


_CHIPMARK_RE = re.compile(r"<!--CHIPMARK:(\d+):(\w+):(\w+):([^-]*(?:-(?!->)[^-]*)*)-->(.*?)<!--/CHIPMARK-->", re.S)


def resolve_chip_marks(html_text: str) -> str:
    """page.save_html: a confirmed header value gets its colour (the new side's also its % on hover), any other is
    left plain."""
    def one(m):
        card, key, mark, old, val = int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)
        if (card, key) not in _CARD_CONFIRMED:
            return val
        tipped = _number_tip(old, val, mark) if old else None
        return (f'<span class="iab-hl iab-hl-{mark} iab-hl-num">{tipped}</span>' if tipped else hl(val, mark))
    return _CHIPMARK_RE.sub(one, html_text)


# header values where a bigger number is better; for the costs and the cooldown a smaller one is
_IAB_META_BIGGER_BETTER = {"aoe", "castrange"}


def _iab_meta_numbers(val) -> tuple:
    return tuple(float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(val or "")))


def _iab_meta_marks(old_vals, new_vals):
    """({key: mark} of the old pane, {key: mark} of the new one) for header values that differ: the new value takes the
    change's colour, the old one the opposite (as Kinetic Fence 7.41: old 1050 nerf-red, new 1200 buff-green)."""
    old_m, new_m = {}, {}
    for key, _, _ in _IAB_META:
        a, b = _iab_meta_numbers(old_vals.get(key)), _iab_meta_numbers(new_vals.get(key))
        if not a or not b or a == b:
            continue
        better = (sum(b) / len(b) > sum(a) / len(a)) == (key in _IAB_META_BIGGER_BETTER)
        new_m[key], old_m[key] = ("buff", "nerf") if better else ("nerf", "buff")
    return old_m, new_m


_IAB_BOLD_META_RE = re.compile(r"<b>([^<]*)</b>")


def _iab_only_meta(text) -> bool:
    """True when the text is only header sentences ("No Mana Cost. Cooldown: 120s.") and nothing else."""
    for _, _, pat in _IAB_META:
        text = re.sub(_iab_meta_re(pat), " ", text)
    text = re.sub(rf"(?:^|(?<=[.!,]))\s*(?:{_IAB_DROP})\s*[.,]?", " ", text)
    return not text.strip()


def _iab_take_meta(desc, only=None):
    """({key: value} of the header sentences, the text without them and without "No Mana Cost" / "No Cooldown")."""
    values = {}
    # "<b>Mana Cost:</b> 50." is the same header sentence as "Mana Cost: 50." (7.41 Zealot / Bane shard: the bold
    # label kept it in the text under a head that already shows it — owner 2026-10-21)
    desc = _IAB_BOLD_LABEL_RE.sub(r"\1:", desc)
    # so is a bold run of nothing but header sentences: "<b>No Mana Cost. Cooldown: 120s.</b>" (7.41 Sacrifice)
    desc = _IAB_BOLD_META_RE.sub(lambda m: m.group(1) if _iab_only_meta(m.group(1)) else m.group(0), desc)
    for key, icon, pat in _IAB_META:
        if only is not None and key not in only:
            continue
        hm = re.search(rf"\b({_IAB_HL_LABEL[key]}){_IAB_HL_VALUE}", desc)
        cand = desc[:hm.start()] + hm.group(1) + hm.group(2) + hm.group(4) + desc[hm.end():] if hm else desc
        mm = re.search(_iab_meta_re(pat), cand)
        if hm and not (mm and mm.start() <= hm.start() < mm.end()):
            cand, hm = desc, None                       # the highlighted one isn't the sentence taken
            mm = re.search(_iab_meta_re(pat), cand)
        if mm:
            val = next(g for g in mm.groups() if g)
            values[key] = hl(val, hm.group(3)) if hm else val
            desc = (cand[:mm.start()] + " " + cand[mm.end():]).strip()
    desc = re.sub(rf"(?:^|(?<=[.!,]))\s*(?:{_IAB_DROP})\s*[.,]?", " ", desc).strip()
    return values, re.sub(r"\s{2,}", " ", desc).strip()


# ---- The description of a new / reworked ability, facet or innate card, like an item ability's (owner 2026-09-30,
# 7.38 Tormentor's Alleviation "... Radius: 900. Duration: 15s.") ----
# The same low header strip as an item ability, on top of the pane: left "Passive" / "Active" / "Toggle" from the
# game files (the name is the title above the card), right the radius / cast range / mana / health cost / cooldown
# with the game's icons — from the files, else from the text's own "Radius: 900." sentences, which leave the text.
# Every other number is bold and a step brighter. Nothing inside a (?) popup, a % badge or a table is touched.
_PANE_SKIP_RE = re.compile(r'class="[^"]*\b(?:badge|info-tip|info-pop|formula-table)', re.I)


_VOID_TAGS = {"img", "br", "hr", "input", "wbr", "source", "col", "path"}


def _bold_numbers_html(html_text):
    """_iab_bold_numbers for card html: numbers inside a badge, a (?) popup, a table or an svg stay as they are."""
    out, stack = [], []
    for part in re.split(r"(<!--.*?-->|<[^>]+>)", html_text, flags=re.S):
        if not part or part.startswith("<!--"):
            out.append(part)
        elif part.startswith("</"):
            if stack:
                stack.pop()
            out.append(part)
        elif part.startswith("<"):
            tag = (re.match(r"<\s*(\w+)", part) or [None, ""])[1].lower()
            if tag not in _VOID_TAGS and not part.endswith("/>"):
                stack.append(bool(_PANE_SKIP_RE.search(part)) or tag in ("table", "svg", "details"))
            out.append(part)
        else:
            out.append(part if any(stack) else _IAB_NUM_RE.sub(r'<b class="iab-num">\1</b>', part))
    return "".join(out)


# "Ultimate. Passive — at the ult's level-up points …" (7.41 Divided We Stand): the header says the kind, the text not
_PANE_KIND_RE = re.compile(r"^\s*(?:Ultimate[.,]\s*)?(Active|Passive|Toggle|Aura)(?:([.,])|\s+([—–-]))\s*")


# What the ability levels / scales with leaves the text for the header, after the kind: "Passive, levels up with
# Duel." -> "Passive – scales with Duel" (owner 2026-10-24, 7.41 Gravity Well / Distortion Field / Outfight Them!;
# brackets -> a dash 10-25); a value growing with hero level in the game files -> "Passive – scales with level". A
# highlight on the phrase (Distortion Field 7.41: "del") stays on it in the header.
# "Shares level with Kinetic Field." goes there too (owner 2026-10-26, 7.41 Kinetic Fence: "в шапку, как scales with").
_PANE_SCALE_RE = re.compile(r"(?:^|(?<=[.!]))\s*(<span[^>]*>)?((?:[Ll]evels(?: up)?|[Ss]cales|[Ii]mproves)|"
                            r"[Ss]hares (?:its )?level) with ([^.<]+?)(</span>)?\.(?=\s|$)")


# never said in a card: "can't be leveled up", and "Has only one level" (the header's "granted by Aghanim's X" says it,
# owner 2026-10-26) — with its highlight, if any
_PANE_NOLEVEL_RE = re.compile(r"(?:^|(?<=[.!]))\s*(?:<span[^>]*>)?(?:(?:Innate, )?[Cc]an(?:'t|not) be leveled up|"
                              r"Has only one level)(?:</span>)?\.(?=\s|$)")


_PANE_NAME_RE = re.compile(r"^\s*([A-Z][\w'’-]*(?: [A-Za-z][\w'’-]*){0,4}):\s+")


# "Base damage: 17 + 3 per level." in a card's text (the game files' hero_levelup, aghs_text.ability_text): a formula
# pill with its level table, as every row's "X + Y per level" (owner 2026-10-25: 7.41 Caustic Finale, Necromastery,
# Keen Scope, Bitter Chill, Fiend's Gate — 33 cards of 7.38-7.41 had it as bare text). A pill already there (its
# number right after the trigger's ">") is left alone.
# "<b>10% + 2%</b> per hero level" (7.38 Dark Seer, hand-written) is one too: the bold closes after the pill
_PER_LEVEL_RE = re.compile(r'(?<![\w.])(?<!">)(\d+(?:\.\d+)?)(%|s)?( [+\-] )(\d+(?:\.\d+)?)(%|s)?(</b>)?'
                           r'( per (?:hero )?level)\b(?! up)')


def _pill_formulas(html_text):
    """(html with each bare "A + B per level" as a formula pill, the pills' tables html)."""
    from .badges import scale_pill
    tables = []

    def pill(m):
        base, unit, sign, inc = float(m.group(1)), m.group(2) or m.group(5) or "", m.group(3).strip(), float(m.group(4))
        step = inc if sign == "+" else -inc
        places = max(len((x.split(".") + [""])[1]) for x in (m.group(1), m.group(4)))
        trigger, table = scale_pill(m.group(0).replace("</b>", ""), lambda L: base + step * L,
                                    value_fmt=f"{{:.{places}f}}{unit}")
        tables.append(f'<div class="formula-table-wrap">{table}</div>')
        return trigger + (m.group(6) or "")
    return _PER_LEVEL_RE.sub(pill, html_text), "".join(tables)


# A header radius / cast range the text already names with its own words ("Vanish radius: 625/550/475/400", 7.41
# Blur) or the same as the radius (a self-centred ability's cast range = its radius: Crimson Guard, Blur, Frost
# Shield) is not said twice: the header keeps one line (owner 2026-10-25, Blur's "scales with Coup de Grace" wrapped).
_HEAD_SAID_LABEL = {"aoe": r"radius", "castrange": r"range"}


def _head_said_twice(key, val, text, props) -> bool:
    if not val or key not in _HEAD_SAID_LABEL:
        return False
    if key == "castrange" and str(val) == str((props or {}).get("aoe") or ""):
        return True
    plain = re.sub(r"<[^>]+>", "", text)
    return bool(re.search(rf"\b{_HEAD_SAID_LABEL[key]}\s*:\s*{re.escape(str(val))}(?![\d/]|\.\d)", plain, re.I))


def _pane_values(desc, props=None) -> dict:
    """The header values a pane would show: the game files' over the text's own "Cooldown: 20s." sentences."""
    text = " ".join(d for d in (desc if isinstance(desc, list) else [desc]) if isinstance(d, str)
                    and not d.lstrip().startswith("<div"))
    found, _ = _iab_take_meta(text)
    return {key: (props or {}).get(key) or found.get(key) for key, _, _ in _IAB_META
            if (props or {}).get(key) or found.get(key)}


def _pane_parts(desc, props=None, facet=False, marks=None, granted=None):
    """(header strip html or "", body rows html) of an ability / facet card pane. The text's own leading "Active." goes
    to the header (7.41 Summon Raptors said it twice); a facet's rows that all start with the ability they change
    ("Arcane Aura: …", 7.38 Arcane Overflow) give the header its name. marks: see _iab_meta_chips. granted: "shard" /
    "scepter" — the header says "Active – granted by Aghanim's Shard" (owner 2026-10-26)."""
    items = [d for d in (desc if isinstance(desc, list) else [desc]) if d is not None]
    plain = [i for i, d in enumerate(items) if isinstance(d, str) and not d.lstrip().startswith("<div")]
    kind = (props or {}).get("kind", "")
    if plain:
        mk = _PANE_KIND_RE.match(items[plain[0]])
        if mk:
            kind = kind or mk.group(1)
            rest = items[plain[0]][mk.end():]
            # "Active, targets an allied creep …" (7.41 Sacrifice): the clause after the comma starts the text
            items[plain[0]] = rest[:1].upper() + rest[1:] if mk.group(2) == "," or mk.group(3) else rest
    scale = ""
    if kind:
        found = [m for i in plain for m in _PANE_SCALE_RE.finditer(items[i])]
        if len(found) == 1:                     # two of them (two sub-abilities) can't say whose: they stay
            o, verb, what, c = found[0].group(1, 2, 3, 4)
            verb = "shares level" if verb.lower().startswith("shares") else "scales"
            scale = f'{o or ""}{verb} with {what.strip()}{c if o else ""}'
        for i in plain:
            cut = _PANE_NOLEVEL_RE.sub("", _PANE_SCALE_RE.sub("", items[i], count=1) if scale else items[i]).strip()
            if cut != items[i]:                 # rule of 2026-05-16: "can't be leveled up" is never said in a card
                items[i] = cut[:1].upper() + cut[1:]
    name = ""
    names = {(_PANE_NAME_RE.match(items[i]) or [None, None])[1] for i in plain if items[i]}
    if facet and len(names) == 1 and None not in names:
        name = names.pop()
        for i in plain:
            items[i] = _PANE_NAME_RE.sub("", items[i], count=1)
            items[i] = items[i][:1].upper() + items[i][1:]
    for i in plain:
        items[i] = _IAB_BOLD_LABEL_RE.sub(r"\1:", items[i])
    # a value said twice in one pane (two cooldowns of two sub-abilities) stays in the text: the header can't say whose;
    # so does one in a row of a named sub-ability among several ("Crystal Ball: …", "Weighted Pie: … Cast Range: 750",
    # 7.38 Dark Carnival Barker)
    subs = {i: m.group(1) for i in plain if (m := _PANE_NAME_RE.match(items[i]))
            and m.group(1) not in ("Active", "Passive", "Toggle", "Aura")
            and re.match(r"[A-Z][a-z]+ [a-z]", items[i][m.end():])}      # a sentence follows, not a value
    own = [i for i in plain if len(set(subs.values())) < 2 or i not in subs]
    once = {key for key, _, pat in _IAB_META
            if sum(len(re.findall(_iab_meta_re(pat), _iab_unhl(items[i]))) for i in plain) == 1}
    values = {}
    for i in own:
        found, items[i] = _iab_take_meta(items[i], only=once)
        values.update(found)
    rows, tables = [], []
    for i, d in enumerate(items):
        if i in plain and not d:
            continue                                     # the row was only "Radius: 900."
        if i in plain:
            d, tbl = _pill_formulas(d)
            tables.append(tbl)
        html = d if not isinstance(d, str) or d.lstrip().startswith("<div") else f'<div class="ability-change-row">{d}</div>'
        rows.append(_bold_numbers_html(html) if isinstance(html, str) else html)
    rows += tables
    said = " ".join(items[i] for i in plain)
    head_props = {k: v for k, v in (props or {}).items()
                  if not (_head_said_twice(k, v, said, props) and k not in (marks or {}))}
    head_values = {k: v for k, v in values.items()
                   if not (_head_said_twice(k, v, said, props) and k not in (marks or {}))}
    chips = _iab_meta_chips(head_values, head_props, marks)   # never folded: a hero's old / new panes have no marks to keep a level
    title = (f'<b class="iab-kind">{kind}:</b> <span class="iab-name">{name}</span>' if kind and name
             else f'<b class="iab-kind">{kind}</b>' if kind
             else f'<span class="iab-name">{name}</span>' if name else "")
    if kind and not scale and (props or {}).get("level_scaled"):
        scale = "scales with level"             # the game files: a value grows with hero level (7.41 innates)
    scale = re.sub(r"<[^>]+>", "", scale)      # never coloured in the header (owner 2026-10-25: "не крась scales with")
    says = ", ".join(([f"granted by Aghanim's {granted.title()}"] if granted else []) + ([scale] if scale else []))
    if says and title:
        title += f' <span class="iab-scale">– {says}</span>'
    elif says:
        title = f'<span class="iab-scale">{says[:1].upper() + says[1:]}</span>'
    head = (f'<div class="iab-head pane-head"><span class="iab-title">{title}</span>'
            f'<span class="iab-meta">{chips}</span></div>') if chips or title else ""
    return head, "".join(rows)


def _pane_props(spec, version):
    """The game files' values of a card side's ability ({"slug"} or its icon's file name) in `version`."""
    from .ability_kv import ability_props, slug_of
    return ability_props(slug_of(spec), version) if isinstance(spec, dict) else None


_IAB_NOTES = page_cache({})  # "<ek>|<pv>|<ability>" -> (?) html moved from a hidden duplicate row into the card


def _iab_shown_in_card(text, extra):
    """A full "Passive: Name. ..." description row of an item whose abilities card (this block) already
    shows that ability on its right side. Its (?) notes move into the card (page.save_html fills the
    <!--IABNOTE:key--> slot), so nothing is lost (owner 2026-09-27, Revenant's Brooch 7.38)."""
    card = getattr(_State, "iab_card", None)
    if not card or (card["ek"], card["pv"]) != (_State.current_entity_key, _State.current_patch_version):
        return False
    base = re.sub(r"<!--TIP-->.*?<!--/TIP-->", "", text, flags=re.S).strip()
    m = _ITEM_ABILITY_RE.match(base)
    name = _iab_name(m.group(2).strip())[0].lower() if m else ""
    if not name or name not in card["names"]:
        return False
    tips = re.findall(r"<!--TIP-->.*?<!--/TIP-->", text, flags=re.S)
    if isinstance(extra, str):
        tips += re.findall(r"<!--INLINETIP-->(.*?)<!--/INLINETIP-->", extra, flags=re.S)
        rest = re.sub(r"<!--INLINETIP-->.*?<!--/INLINETIP-->", "", extra, flags=re.S).strip()
        if rest:
            return False                                    # a visible note under the row: keep the row
    if tips:
        _IAB_NOTES[f"{card['ek']}|{card['pv']}|{name}"] = "".join(tips)
    return True


def item_abilities_change(old, new):
    """An item's abilities before -> after (owner 2026-09-27, Khanda 7.38 pilot): two panes like the
    stats card, each ability in the game-tooltip style (_item_ability_html). `old` / `new` are lists of
    one-line ability texts ("Passive: Empower Spell. The next ... Cooldown: 6s"); the old ones are the
    game's tooltips of the previous patch (patch/loc_history.py), never invented. The card is not scored — the tagged
    rows under it keep the weights. It is drawn when the page is saved (render_iab_card), after the rows
    under it have marked the numbers they change."""
    names = {_iab_ability_key(t) for t in new if _ITEM_ABILITY_RE.match(t)}
    old_names = {_iab_ability_key(t) for t in old if _ITEM_ABILITY_RE.match(t)}
    key = f"{_State.current_entity_key}|{_State.current_patch_version}"
    _IAB_CARDS[key] = (list(old), list(new))
    # the same ability on both sides (a replacement pair's two texts aren't one ability rewritten)
    pairs = [(o, n) for o, n in _iab_pair_rows(old, new) if _iab_same_ability(o, n)]
    segs = {_iab_ability_key(n): _iab_text_diff(o, n) for o, n in pairs}
    pairs_by = {}
    for o, n in pairs:
        pairs_by[(_iab_ability_key(n), "old")], pairs_by[(_iab_ability_key(n), "new")] = o, n
    _State.iab_card = {"ek": _State.current_entity_key, "pv": _State.current_patch_version, "names": names,
                       "old_names": old_names, "old": " ".join(old), "new": " ".join(new), "key": key,
                       "segs": segs, "pairs": pairs, "pairs_by": pairs_by}
    return f"<!--IABCARD:{key}-->"


_IAB_WORD_RE = re.compile(r"\S+")


_IAB_NUMTOK_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*[%sx]?")


_IAB_META_SEG_RE = re.compile(r"\b(?:cast range|mana cost|health cost|cooldown|radius)\b", re.I)


def _iab_text_diff(old, new):
    """Word spans that differ between an ability's old and new text, numbers ignored (the numeric rows colour
    those): {"old": [(start, end, text, op)] removed, "new": [...] added}; op is difflib's "delete" / "insert"
    (gone / added outright) or "replace" (rewritten). Meta sentences (range, cost, cooldown, radius) are left
    out — the header shows them."""
    def toks(t):
        return [(m.start(), m.end(), _IAB_NUMTOK_RE.sub("#", m.group(0).lower().strip(".,;:"))) for m in _IAB_WORD_RE.finditer(t)]
    a, b_ = toks(old), toks(new)
    out = {"old": [], "new": []}
    sm = difflib.SequenceMatcher(a=[x[2] for x in a], b=[x[2] for x in b_], autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        for side, src, lo, hi in (("old", a, i1, i2), ("new", b_, j1, j2)):
            if op == "equal" or lo >= hi:
                continue
            full, s0 = (old if side == "old" else new), src[lo][0]
            # clause by clause (". ", ", ", " and "): a row about armor colours "and 8 armor", not the
            # whole "health regeneration, 5 mana regeneration and 8 armor" (Guardian Greaves 7.40)
            cuts = [s0] + [s0 + m.end() for m in re.finditer(r"[.,;]\s+|\s+(?=and\s)", full[s0:src[hi - 1][1]])]
            for a0, a1 in zip(cuts, cuts[1:] + [src[hi - 1][1]]):
                text = full[a0:a1].strip()
                a0 += len(full[a0:a1]) - len(full[a0:a1].lstrip())
                if not text or _IAB_META_SEG_RE.search(text) or not re.search(r"[A-Za-z]{3}", _IAB_NUMTOK_RE.sub("", text)):
                    continue
                out[side].append((a0, a0 + len(text), text, op))
    return out


_IAB_CARDS = page_cache({})  # "<ek>|<pv>" -> (old texts, new texts)


_IAB_MARKS = page_cache({})  # "<ek>|<pv>" -> [(target, value, direction)] from the hidden rows under the card


_IAB_META_WORDS = {"cooldown": "cooldown", "mana cost": "manacost", "cast range": "castrange", "health cost": "healthcost"}


_IAB_FROMTO_RE = re.compile(r"from\s+[+\-]?(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*)\S*\s+to\s+[+\-]?(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*)", re.I)


_IAB_NOWHAS_RE = re.compile(r"now has an?\s+(\d+(?:\.\d+)?)s?\s+(cooldown|mana cost)", re.I)


def _iab_has(num, text):
    return re.search(rf"(?<![\d./]){re.escape(num)}(?![\d/]|\.\d)", text) is not None


def _iab_note(text, extra):
    """The row's own clarification — a trailing "(…)" or the popup of its inline note / (?) — as tooltip
    HTML (badges kept), or ''."""
    notes = []
    m = re.search(r"\(([^()]{8,})\)\s*$", re.sub(r"<!--TIP-->.*?<!--/TIP-->", "", text, flags=re.S))
    if m:
        notes.append(_html.escape(m.group(1).strip(), quote=False))
    blobs = re.findall(r"<!--TIP-->.*?<!--/TIP-->", text, flags=re.S)
    if isinstance(extra, str):
        blobs += re.findall(r"<!--TIP-->.*?<!--/TIP-->", extra, flags=re.S)
    for blob in blobs:
        pop = re.search(r'<span class="info-pop">(.*)</span></span><!--/TIP-->', blob, flags=re.S)
        if pop and pop.group(1).strip():
            notes.append(pop.group(1).strip())
    note = "<br>".join(notes)
    return note[:1].upper() + note[1:]


def _iab_covered_change(text, tags, extra="", badge=""):
    """A numeric change row the card can show (owner 2026-09-27: "don't repeat what the card shows"):
    old and new value both in the card, or an AoE radius (it gets its own header value). Records what to
    colour — and the row's % badge + note, shown as a dotted underline + hover text on that value (owner
    2026-09-27: "20 > 15 — by how many %?") — returns True."""
    card = getattr(_State, "iab_card", None)
    if not card or (card["ek"], card["pv"]) != (_State.current_entity_key, _State.current_patch_version):
        return False
    plain = re.sub(r"<!--TIP-->.*?<!--/TIP-->", " ", text, flags=re.S)
    plain = re.sub(r"<[^>]+>", " ", plain)
    direction = ("buff" if "buff" in tags else "nerf" if "nerf" in tags else "new" if "new" in tags
                 else "rework" if "rework" in tags else "misc" if "misc" in tags else "")
    if not direction:
        return False
    low = plain.lower()
    note = _iab_note(text, extra)
    if isinstance(badge, str) and "badge-group" in badge:
        note = "<br>".join(x for x in (f'<span class="iab-tip-pct">{badge}</span>', note) if x)
        # the number takes the very shade of its % (owner 2026-09-28): "iab-nerf badge nerf3 tone"
        direction = f"{direction} {_tone_cls(badge)}".strip()
    m = _IAB_FROMTO_RE.search(plain)
    if m and re.search(r"\bradius\b", low) and "cast range" not in low:
        ability = next((n for n in card["names"] if n and low.startswith(n)), "")
        if not ability and len(card["names"]) == 1 and low.startswith("radius"):
            ability = next(iter(card["names"]))
        if not ability:                                       # an ability the card doesn't show: keep the row
            return False
        _IAB_MARKS.setdefault(card["key"], []).append(("aoe", m.group(2), direction, note, ability, m.group(1)))
        return True
    # which header value: read after the ability's own name — "Reset Cooldowns mana cost decreased" is the mana cost
    # (owner 2026-10-17, Refresher Orb 7.41: the new 325 wasn't marked; "cooldown" was found in the name)
    lead = next((n for n in sorted(card["names"], key=len, reverse=True) if n and low.startswith(n)), "")
    target = next((v for k, v in _IAB_META_WORDS.items() if k in low[len(lead):]), "num")
    if m and _iab_has(m.group(2), card["new"]) and _iab_has(m.group(1), card["old"]):
        _IAB_MARKS.setdefault(card["key"], []).append((target, m.group(2), direction, note, "", m.group(1)))
        return True
    m = _IAB_NOWHAS_RE.search(plain)
    if m and _iab_has(m.group(1), card["new"]):
        _IAB_MARKS.setdefault(card["key"], []).append((_IAB_META_WORDS[m.group(2).lower()], m.group(1), direction, note, "", ""))
        return True
    return False


_IAB_HL = page_cache({})  # "<ek>|<pv>" -> [(ability, side, span index, direction)] text a hidden row describes


_IAB_TAG_ORDER = ("new", "del", "buff", "nerf", "rework", "swap", "qol", "misc")


_IAB_STOP = {"now", "longer", "also", "with", "from", "that", "this", "when", "into", "than", "have", "been",
             "will", "your", "their", "them", "only", "each", "item", "items", "ability", "abilities"}


def _iab_row_ability(low, card, names):
    """The ability (lower-case name) a row speaks of: its name in the row, or the card's only one."""
    hit = [n for n in names if n and re.search(rf"\b{re.escape(n)}\b", low)]
    # the name the row starts with wins: "Guard base damage block rescaled …" is Guard, not Damage Block
    # (Crimson Guard 7.41)
    lead = [n for n in hit if re.match(rf"{re.escape(n)}\b", low)]
    if lead:
        return max(lead, key=len)
    if hit:
        return max(hit, key=len)
    return next(iter(names)) if len(names) == 1 else ""


def _iab_stem(w):
    # a plural is its word ("trees" = "tree", "pulls" = "pull" — Harpoon 7.41: "can now target trees and will pull")
    return (w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith(("ss", "us", "is", "os")) else w)[:5]


def _iab_stems(text, drop=()):
    return {_iab_stem(w) for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _IAB_STOP and w not in drop}


def _iab_grow(full, s, segs):
    """A span (start, end, …) joined with the changed pieces right before / after it (only spaces between), a
    trailing "and" dropped: "Restores 3000 health" + "and 2000 mana and" -> "Restores 3000 health and 2000 mana"."""
    a, b = s[0], s[1]
    grew = True
    while grew:
        grew = False
        for seg in segs:
            if seg[0] >= b and not full[b:seg[0]].strip():
                b, grew = seg[1], True
            elif seg[1] <= a and not full[seg[1]:a].strip():
                a, grew = seg[0], True
    m = re.search(r"[\s,;]+and$", full[a:b])
    return (a, b - (len(m.group(0)) if m else 0), *s[2:])


def _iab_with_number(full, s, nums):
    """A coloured span (start, end, …) grown back, within its clause, to the first of the row's numbers before it
    ("2.5 health regeneration"; Mask of Madness 7.41 "8% / 12% movement speed (ranged/melee)", where the diff, numbers
    aside, saw only "(ranged/melee)" added)."""
    if re.match(r"and\b", full[s[0]:]):       # the span opens its own clause: what's before belongs to another
        return s
    head = full[:s[0]]
    seps = list(re.finditer(r"[,.;:]\s+|\band\s+", head))
    start = seps[-1].end() if seps else 0
    first = next((m.start() for m in re.finditer(r"[+\-]?(\d+(?:\.\d+)?)", head[start:]) if m.group(1) in nums), None)
    return (start + first, *s[1:]) if first is not None else s


def _iab_text_change(text, tags):
    """A change row WITHOUT numbers whose words the card shows as added / removed text of that ability
    (owner 2026-09-27, Bloodstone 7.38: "Bloodpact now applies a basic dispel on cast" = the new
    "Dispel Type: Basic Dispel."): that text is coloured by the row's tag, the row hidden (still counted)."""
    card = getattr(_State, "iab_card", None)
    if not card or (card["ek"], card["pv"]) != (_State.current_entity_key, _State.current_patch_version):
        return False
    plain = re.sub(r"<[^>]+>", " ", re.sub(r"<!--TIP-->.*?<!--/TIP-->", " ", text, flags=re.S)).strip()
    direction = next((t for t in _IAB_TAG_ORDER if t in tags), "")
    low = plain.lower()
    # numbers: only a "no longer …" row whose numbers the removed text shows (checked below)
    nums = re.findall(r"\d+(?:\.\d+)?", plain)
    if not direction:
        return False
    ability = _iab_row_ability(low, card, set(card.get("segs", {})))
    diff = card.get("segs", {}).get(ability)
    if not diff:
        return False
    tailed = False
    for rx, tail, *also in _IAB_TAILS:
        # a property the game's tooltip doesn't spell out: the new description gets it at its end, in the
        # row's colour ("Disarm can now be dispelled" -> "Dispellable.", Heaven's Halberd 7.38; "Freezing Aura
        # now pierces debuff immunity" -> "Pierces Debuff Immunity.", Shiva's Guard 7.41) — or, when the
        # tooltip already says it, that sentence is coloured. Matched on the row as written, so a name it
        # carries keeps its capitals ("Shares a cooldown with Boots of Bearing.")
        hit = re.match(rf"^{re.escape(ability)}'?s? {rx}$", plain, re.I)
        if hit:
            tail = tail.format(*hit.groups())
            new_text = card.get("pairs_by", {}).get((ability, "new"), "")
            at = new_text.lower().find(tail.lower().rstrip("."))
            entry = ({"ability": ability, "side": "new", "span": (at, at + len(tail.rstrip("."))), "dir": direction}
                     if at >= 0 else {"ability": ability, "side": "new", "append": tail, "dir": direction})
            _IAB_HL.setdefault(card["key"], []).append(entry)
            if not also:
                return True
            tailed = True                 # …and the text the tooltip does add is coloured too (Harpoon 7.41)
            break
    # a row with numbers: "no longer …", a new property with its value ("now also grants 30% Slow Resistance",
    # Mask of Madness 7.41) or a rewrite ("changed from +25 … to +8%/12% …") — checked below against the text
    if nums and not re.search(r"\bno longer\b|\bnow (?:also )?(?:provides?|grants?|gives?|increases?|has|restores?)\b"
                              r"|\bchanged from\b", low):
        return tailed
    ch = re.search(r"\bchanged from .*? to (.*)", low)
    if ch:          # the new text shows what follows the first "to" — values, or words ("600 to the hero's attack range")
        nums = re.findall(r"\d+(?:\.\d+)?", ch.group(1))
    words = _iab_stems(low, drop=set(ability.split()) | _IAB_VERBS)
    if not words:
        return tailed
    # "no longer …" / DEL speaks of the OLD text, anything else of the NEW one — never the other side (a NEW
    # row must not colour old text: Disperser 7.40)
    side = "old" if ("no longer" in low or direction == "del") else "new"
    wordy = lambda seg: len(re.findall(r"[A-Za-z]{2,}", seg)) >= 2
    got = lambda seg: len(words & _iab_stems(seg))
    # the old side: only text removed outright — a rewritten "Consumes a charge and gives" isn't what "no
    # longer uses charges" means, "Comes with 8 charges." is (Drum of Endurance 7.38)
    pool = [s for s in diff[side] if wordy(s[2]) and (side == "new" or s[3] == "delete")]
    strong = [s for s in pool if got(s[2]) >= min(2, len(words))]
    full = card.get("pairs_by", {}).get((ability, side), "")
    sentence = lambda s: re.search(r"[.!]$", s[2]) and re.search(r"(?:^|[.!:])\s*$", full[:s[0]])
    hits = [s for s in strong if sentence(s)] or strong          # a whole sentence beats a fragment
    if not hits:
        # no single piece holds two of the row's words: the shortest phrase that does ("your attack damage")
        span = _iab_phrase(card, ability, side, words)
        hits = [span] if span else [s for s in pool if got(s[2]) * 2 >= len(words)]
    # "no longer X": what stopped is X — the text must hold one of the first two words after "no longer"
    # ("no longer stack with Orb of Corrosion" is not "reduces heals, health", Orb of Frost 7.39)
    after = re.search(r"no longer (.*)", low)
    if after:
        obj = [_iab_stem(w) for w in re.findall(r"[a-z]{4,}", after.group(1)) if w not in _IAB_STOP and w not in _IAB_VERBS][:2]
        if not any(set(obj) & _iab_stems(full[s[0]:s[1]]) for s in hits):
            hits = []
    # a number right before the coloured words is theirs: the diff, numbers aside, paired "2.5" with the "8%" after
    # it and gave only "health regeneration" (Pipe of Insight 7.41 "no longer provides 2.5 health regen")
    if nums:
        hits = [_iab_with_number(full, s, nums) for s in hits]
    # a row with numbers ("…by 25%", Shiva's Guard 7.41) only when the coloured text shows every one of them — a
    # level of a "15%/30%" counts (Mask of Madness 7.41e "15% … for ranged heroes and 30% for melee heroes")
    def shown(n, seg):
        if _iab_has(n, seg):
            return True
        # a level counts only when the row names every level of that value ("20/30/40" doesn't show a lone "30")
        return any(n in lv and set(lv) <= set(nums) for lv in
                   (re.findall(r"\d+(?:\.\d+)?", g) for g in re.findall(r"\d+(?:\.\d+)?%?(?:\s*/\s*\d+(?:\.\d+)?%?)+", seg)))
    if nums and not all(any(shown(n, full[s[0]:s[1]]) for s in hits) for n in nums):
        # a clause the diff cut at "and" ("Restores 3000 health" | "and 2000 mana and", Block of Cheese 7.38): the
        # pieces right next to a hit join it, then the numbers are checked again
        grown = [_iab_grow(full, s, diff[side]) for s in hits]
        hits = grown if grown and all(any(shown(n, full[g[0]:g[1]]) for g in grown) for n in nums) else []
    if not hits and side == "old" and after and not nums:
        # "no longer refreshes items" and the old text lost "items and" ("all your items and abilities" -> "all your
        # abilities", Refresher Shard 7.41 — owner 2026-10-16: it wasn't coloured): the word itself, even one the
        # stem lists skip as too common in item tooltips
        said = set(re.findall(r"[a-z]{4,}", after.group(1)))
        hits = [(s[0], s[1] - (4 if s[2].endswith(" and") else 0)) + s[2:] for s in diff["old"]
                if s[3] == "delete" and set(re.findall(r"[a-z]{4,}", s[2].lower())) & said]
    if not hits and side == "old" and not nums:
        # what the ability did that its old tooltip never said, now gone: written after the old description, red
        # (owner 2026-10-17, Pipe of Insight 7.41 "Barrier no longer affects units that have been affected by Barrier
        # within Pipe of Insight's cooldown"; Dagon "Energy Burst no longer instantly kills non-ancient creeps")
        gone = re.match(rf"^{re.escape(ability)}'?s? no longer ([^.;()]+?)\.?$", plain, re.I)
        if gone:
            _IAB_HL.setdefault(card["key"], []).append(
                {"ability": ability, "side": "old", "append": gone.group(1)[:1].upper() + gone.group(1)[1:] + ".",
                 "dir": "del"})
            return True
    if not hits:
        return tailed
    # removed text is red whatever the row's tag (owner 2026-09-27); added text takes the tag's colour
    d = "del" if side == "old" else direction
    _IAB_HL.setdefault(card["key"], []).extend(            # a clause's trailing comma stays white
        {"ability": ability, "side": side, "span": (s[0], s[1] - (full[s[1] - 1:s[1]] in (",", ";"))), "dir": d}
        for s in hits)
    return True


_IAB_VERBS = {"deal", "deals", "apply", "applies", "gives", "grants", "provides", "uses", "does"}


_IAB_TAILS = (   # (the row after the ability's name, the sentence the new description gets)
    (r"can now be dispelled", "Dispellable."),
    (r"can no longer be dispelled", "Not dispellable."),
    (r"now pierces debuff immunity", "Pierces Debuff Immunity."),
    (r"no longer pierces debuff immunity", "Does not pierce Debuff Immunity."),
    # a value the tooltip keeps for one kind of unit only (owner 2026-10-16, Crimson Guard 7.41: "Guard base damage
    # block rescaled from 70 for all units to 70 on melee heroes and buildings and 45 on ranged heroes" — the new
    # tooltip still says "70"); {0} = the row's number
    (r"base damage block rescaled from \d+ for all units to \d+ on melee heroes(?: and buildings)? and (\d+) on "
     r"ranged heroes", "{0} base damage block on ranged heroes."),
    # the game's own wording for a shared cooldown (Refresher Orb: "Shares a cooldown with Refresher Shard."); owner
    # 2026-10-17, Drum of Endurance / Boots of Bearing 7.41: rows the card can carry go into it
    (r"now shares (?:a |its )?cooldown with ([^.,;()\d]+?)\.?", "Shares a cooldown with {0}."),
    # what the tooltip leaves out of a new effect it does describe: added after it, and the tooltip's own new
    # sentence coloured too (Harpoon 7.41 "…can now target trees and will pull the caster to it, destroying all trees
    # on the way" — the tooltip says only "Targeting a tree always pulls you all the way to that tree.")
    (r"can now target trees and will pull the caster to it, destroying all trees on the way",
     "Destroys all trees on the way.", True),
)


_IAB_DETERMINERS = ("your ", "their ", "its ", "the ")


def _iab_phrase(card, ability, side, words):
    """The shortest run of words on one side that holds two of the row's words and doesn't appear on the
    other side ("Empower Spell no longer deals attack damage" = the old "your attack damage", Khanda 7.38),
    a determiner before it included; (start, end) or None."""
    pair = next(((o, n) for o, n in card.get("pairs", []) if _iab_ability_key(n) == ability), None)
    if not pair or len(words) < 2:
        return None
    text, other = (pair[0], pair[1]) if side == "old" else (pair[1], pair[0])
    toks = [(m.start(), m.end(), _iab_stems(m.group(0)))
            for m in _IAB_WORD_RE.finditer(text)]
    found = []
    for i in range(len(toks)):
        if not toks[i][2] & words:           # a phrase opens on one of the row's words ("you Savory Shield" doesn't)
            continue
        got = set()
        for j in range(i, min(i + 6, len(toks))):
            got |= toks[j][2] & words
            if len(got) >= 2:
                found.append((toks[i][0], toks[j][1]))
                break
    # the shortest that the other side doesn't also say ("Savory Shield" is on both sides of Block of Cheese 7.38,
    # "Duration: 5 minutes" only on the new one)
    for best in sorted(found, key=lambda s: s[1] - s[0]):
        phrase = text[best[0]:best[1]].strip(".,;: ")
        if phrase.lower() in other.lower():
            continue
        before = text[:best[0]].lower()
        det = next((d for d in _IAB_DETERMINERS if before.endswith(d)), "")
        return (best[0] - len(det), best[0] + len(phrase))
    return None


def _iab_unpaired_row(text, tags, extra=""):
    """"Removed Damage Block ability" when the card shows Damage Block on the old side only (or a NEW row of
    an ability only the new side has): the card says it, the row is hidden (owner 2026-09-27). An inline
    note ("Blocked 70 damage from melee…", Abyssal Blade 7.38) only repeats the card's text; any other
    note under the row keeps it."""
    card = getattr(_State, "iab_card", None)
    if not card or (card["ek"], card["pv"]) != (_State.current_entity_key, _State.current_patch_version):
        return False
    if isinstance(extra, str) and re.sub(r"<!--INLINETIP-->.*?<!--/INLINETIP-->", "", extra, flags=re.S).strip():
        return False
    low = re.sub(r"<[^>]+>", " ", re.sub(r"<!--TIP-->.*?<!--/TIP-->", " ", text, flags=re.S)).lower()
    old_only = card.get("old_names", set()) - card["names"]
    new_only = card["names"] - card.get("old_names", set())
    if "del" in tags and re.search(r"\bremoved\b|\bno longer has\b", low):
        return any(n and re.search(rf"\b{re.escape(n)}\b", low) for n in old_only)
    if "new" in tags and not re.search(r"\d", low):
        return any(n and re.search(rf"\b{re.escape(n)}\b", low) for n in new_only)
    return False


_IAB_HL_OPEN, _IAB_HL_CLOSE = 0xE000, ""   # private-use characters: never a word, a number or a tag


def _iab_mark_text(text, spans):
    """Wrap (start, end, direction) spans of a plain ability text in private-use marker characters (the
    trailing full stop stays outside, so the header's meta sentences are still found); _iab_markers_html
    turns them into coloured spans once the text is html."""
    for start, end, direction in sorted(spans, reverse=True):
        while end > start and text[end - 1] in ".,;:":
            end -= 1
        opener = chr(_IAB_HL_OPEN + _IAB_TAG_ORDER.index(direction))
        text = text[:start] + opener + text[start:end] + _IAB_HL_CLOSE + text[end:]
    return text


def _iab_markers_html(html_text):
    # data-tag: the tag filters find the card by its coloured text too (owner 2026-09-28: Drum of Endurance
    # 7.38 under DEL — its "Comes with 8 charges." is removed text, its row is REWORK)
    for i, direction in enumerate(_IAB_TAG_ORDER):
        html_text = html_text.replace(chr(_IAB_HL_OPEN + i),
                                      f'<span class="iab-hl iab-hl-{direction}" data-tag="{direction}">')
    return html_text.replace(_IAB_HL_CLOSE, "</span>")


def _iab_hint(inner, note):
    """A value with a note: light dotted underline, the note on hover (site tooltip, data-tooltip)."""
    return (f'<span class="iab-hint abil-ico-hint" data-tooltip="{_html.escape(note, quote=True)}">{inner}</span>'
            if note else inner)


_IAB_AOE_SPAN = r'<span class="iab-m">(<img class="iab-ico" src="[^"]*aoe\.png" alt="">)({num})</span>'


def _iab_set_radius(pane_html, ability, value, cls="", note=""):
    """The ability's radius in its card header (by name): colour the radius value the tooltip already
    gives ("Radius: 825"), or add one when the radius is only in the prose ("in a 350 radius")."""
    cards = pane_html.split('<div class="iab-card">')
    idx = next((i for i, c in enumerate(cards[1:], 1)
                if re.search(rf'<span class="iab-name">{re.escape(ability)}</span>', c, re.I)), None)
    if idx is None:
        return pane_html
    card = cards[idx]
    ico = f'<img class="iab-ico" src="{ABILITY_ICON_DIR}aoe.png" alt="">'
    cls_attr = f"iab-m {cls}".strip()
    if re.search(_IAB_AOE_SPAN.format(num=r"[^<]*"), card):
        card = re.sub(_IAB_AOE_SPAN.format(num=re.escape(value)),
                      lambda m: f'<span class="{cls_attr}">{m.group(1)}{_iab_hint(m.group(2), note)}</span>', card, count=1)
    else:
        card = card.replace('<span class="iab-meta">',
                            f'<span class="iab-meta"><span class="{cls_attr}">{ico}{_iab_hint(value, note)}</span>', 1)
    cards[idx] = card
    return '<div class="iab-card">'.join(cards)


def _iab_ability_key(text):
    """The ability's name, lower-case; the whole text when no name can be read (two nameless abilities are
    not one ability)."""
    m = _ITEM_ABILITY_RE.match(text)
    name = _iab_name(m.group(2).strip())[0] if m else ""
    return (name or text).lower()


def _iab_pair_rows(old, new):
    """Old and new abilities side by side, paired by name (owner 2026-09-27, Heaven's Halberd 7.38: an
    arrow next to an ability that has no counterpart points at nothing). Both sides keep their order; an
    ability only one side has gets a row of its own with an empty cell on the other side."""
    new_keys = [_iab_ability_key(t) for t in new]
    rows, used = [], set()
    for t in old:
        j = next((j for j, k in enumerate(new_keys) if k == _iab_ability_key(t) and j not in used), None)
        if j is not None:
            rows += [(None, new[i]) for i in range(j) if i not in used]
            used.update(range(j + 1))
        rows.append((t, new[j] if j is not None else None))
    rows += [(None, new[i]) for i in range(len(new)) if i not in used]
    # an ability removed and another added in the same patch is a REPLACEMENT: one row, old -> new
    # (owner 2026-09-28, Revenant's Brooch 7.38: Toggle: Phantom Province -> Passive: Phantom Critical);
    # the n-th removed one faces the n-th added one
    gone = [i for i, (o, n) in enumerate(rows) if n is None]
    came = [i for i, (o, n) in enumerate(rows) if o is None]
    for gi, ci in zip(gone, came):
        rows[min(gi, ci)] = (rows[gi][0], rows[ci][1])
        rows[max(gi, ci)] = None
    return [r for r in rows if r is not None]


def _iab_same_ability(o, n):
    return bool(o and n) and _iab_ability_key(o) == _iab_ability_key(n)


def _iab_first_level(levels):
    """The level-1 value with the unit the last level carries ("10/20/30/40/50%" -> "10%")."""
    unit = re.sub(r"^[+\-]?[\d.]+", "", levels[-1])
    return levels[0] if levels[0].endswith(unit) else levels[0] + unit


def _iab_levels_note(levels, was=None, direction=""):
    """"Levels 1–5: 120 / 140 / 160 / 180 / 200" — a level that changed in its colour."""
    shown = [lv if not was or lv == w else f'<span class="iab-lv iab-{direction}">{lv}</span>'
             for lv, w in zip(levels, was or levels)]
    return f"Levels 1–{len(levels)}: " + " / ".join(shown)


def _iab_chip_mark(ico, value, was, direction, note):
    """A changed header value: coloured whole, or — the same number of levels before and after — only the levels
    that changed (owner 2026-10-17, Dagon 7.41: "for the future, when something changes at one level"). 5+ levels:
    the level-1 value, dotted, every level in the hover (owner 2026-10-17: "the level-1 value, underlined dotted —
    the popup has all levels")."""
    from .badges import RANGE_FROM_LEVELS
    new, old = value.split("/"), (was or "").split("/")
    same = len(new) == len(old) and new != old
    if len(new) >= RANGE_FROM_LEVELS:
        full = "<br>".join(x for x in (_iab_levels_note(new, old if same else None, direction), note) if x)
        return f'<span class="iab-m iab-{direction}">{ico}{_iab_hint(_iab_first_level(new), full)}</span>'
    if len(new) > 1 and same:
        lv = "/".join(n if n == o else f'<span class="iab-lv iab-{direction}">{n}</span>' for n, o in zip(new, old))
        return f'<span class="iab-m">{ico}{_iab_hint(lv, note)}</span>'
    return f'<span class="iab-m iab-{direction}">{ico}{_iab_hint(value, note)}</span>'


_IAB_CHIP_RE = re.compile(r'<span class="iab-m">(<img class="iab-ico" src="[^"]*?(\w+)\.png" alt="">)([^<]+)</span>')


def _iab_compact_levels(html):
    """A header value of 5+ levels as its level-1 value, dotted, every level in the hover, on both sides (owner
    2026-10-17, Dagon 7.41: "show the active's level-1 value in the header, underline it dotted — the popup will have
    all levels; for the old and the new cards"). A changed value is drawn so by _iab_chip_mark."""
    from .badges import RANGE_FROM_LEVELS

    def one(m):
        lv = m.group(3).split("/")
        if len(lv) < RANGE_FROM_LEVELS:
            return m.group(0)
        return f'<span class="iab-m">{m.group(1)}{_iab_hint(_iab_first_level(lv), _iab_levels_note(lv))}</span>'
    return _IAB_CHIP_RE.sub(one, html)


def render_iab_card(key):
    """The abilities card html (page.save_html fills <!--IABCARD:key-->): the abilities in rows, old left /
    new right, an arrow only between an ability and its counterpart; the numbers the hidden rows change
    coloured by their tag (green better / red worse / gold new)."""
    if key not in _IAB_CARDS:
        return ""
    rows = _iab_pair_rows(*_IAB_CARDS[key])
    spans, tails = {}, {}                                     # (ability, side) -> [(start, end, dir)] / [(text, dir)]
    for mark in _IAB_HL.get(key, []):
        k = (mark["ability"], mark["side"])
        if mark.get("append"):
            tails.setdefault(k, []).append((mark["append"], mark["dir"]))
        elif mark["span"] not in [s[:2] for s in spans.get(k, [])]:
            spans.setdefault(k, []).append((*mark["span"], mark["dir"]))
    # only the abilities that changed (owner 2026-10-17, Harpoon / Mask of Madness 7.41: "why the passive, when only
    # Draw Forth changed"): the same text on both sides, nothing coloured, no moved note, no radius mark — left out;
    # a card where nothing would stay keeps everything
    aoe = {mk[4] for mk in _IAB_MARKS.get(key, []) if mk[0] == "aoe"}

    def changed(o, n):
        k = _iab_ability_key(n or o)
        return (o != n or any((k, side) in spans or (k, side) in tails for side in ("old", "new")) or k in aoe
                or _IAB_NOTES.get(f"{key}|{_iab_name(_ITEM_ABILITY_RE.match(n).group(2).strip())[0].lower()}"
                                  if n and _ITEM_ABILITY_RE.match(n) else ""))
    rows = [r for r in rows if changed(*r)] or rows

    def with_tails(t, k):
        """A sentence the row adds (\"Dispellable.\") at the end of the description, before the header
        values, plus its colour span."""
        extra = [s for s in spans.get(k, [])]
        for tail, d in tails.get(k, []):
            mm = re.search(r"(?:(?<=[.!])|^)\s*(?:Cast Range|Mana Cost|Health Cost|Cooldown|Radius|No Mana Cost|No Cooldown)\b", t)
            p = mm.start() if mm else len(t)
            ins = (" " if p and t[p - 1] != " " else "") + tail + (" " if mm else "")
            t = t[:p] + ins + t[p:]
            extra = [(a + len(ins), b + len(ins), dd) if a >= p else (a, b, dd) for a, b, dd in extra]
            start = p + (1 if ins.startswith(" ") else 0)
            extra.append((start, start + len(tail), d))
        return t, extra

    def pane(texts, side, slots=False, others=()):
        cards = []
        for i, t in enumerate(texts):
            if t is None:
                # the other side's ability has no counterpart: an empty cell that keeps the rows aligned, no frame
                # (owner 2026-09-30: the added / removed card itself carries a light green / red dashed frame)
                cards.append('<div class="iab-none"></div>')
                continue
            alone = i < len(others) and others[i] is None
            frame = (" iab-added" if side == "new" else " iab-removed") if alone else ""
            t, marks = with_tails(t, (_iab_ability_key(t), side))
            h = _item_ability_html(_iab_mark_text(t, marks)) if marks else None
            h = _iab_markers_html(h) if h else (_item_ability_html(t) or _html.escape(t))
            m = _ITEM_ABILITY_RE.match(t)
            if slots and m and "iab-desc" in h:                 # a slot for a moved (?) note
                h = iab_attach_tail(h, f"<!--IABNOTE:{key}|{_iab_name(m.group(2).strip())[0].lower()}-->")
            cards.append(f'<div class="iab-card{frame}">{h}</div>')
        return "".join(cards)

    olds, news = [o for o, _ in rows], [n for _, n in rows]
    right, left = pane(news, "new", slots=True, others=olds), pane(olds, "old", others=news)
    for target, value, direction, note, ability, was in _IAB_MARKS.get(key, []):
        num = re.escape(value)
        if target == "aoe":                                   # a radius: a header value on both sides
            right = _iab_set_radius(right, ability, value, f"iab-{direction}", note)
            left = _iab_set_radius(left, ability, was)
        elif target == "num":
            right = re.sub(rf'<b class="iab-num">([+\-]?{num}(?:%|s)?)</b>',
                           lambda m: _iab_hint(f'<b class="iab-num iab-{direction}">{m.group(1)}</b>', note), right, count=1)
        else:
            right = re.sub(rf'<span class="iab-m">(<img class="iab-ico" src="[^"]*{target}\.png" alt="">)({num})</span>',
                           lambda m: _iab_chip_mark(m.group(1), m.group(2), was, direction, note), right, count=1)
    right, left = _iab_compact_levels(right), _iab_compact_levels(left)
    # one arrow for the whole card, between the two columns (owner 2026-09-27: not one per ability), centred on
    # the rows that have both sides — beside an ability alone on one side it pointed at nothing (owner 2026-09-30,
    # Gleipnir / Heaven's Halberd 7.38); no pair at all: the whole card
    paired = [i for i, (o, n) in enumerate(rows, 1) if o and n] or [1, len(rows)]
    span = f"{paired[0]} / {paired[-1] + 1}"
    return (f'<div class="properties-change iab-change" style="grid-template-rows:repeat({len(rows)},auto)">'
            f'<div class="properties-pane pane-old">{left}</div>'
            f'<span class="properties-arrow" style="grid-row:{span}">→</span>'
            f'<div class="properties-pane pane-new">{right}</div></div>')


def _tone_cls(badge_html, fallback=""):
    """The shade class of a b() badge ("badge nerf3 tone"): a changed value painted with it looks exactly like
    its % (owner 2026-09-28: "1000" and "+14%" in two reds); `.badge.tone` drops the chip's box."""
    m = re.search(r'class="badge ((?:buff|nerf)\d+)[" ]', badge_html or "")   # "badge nerf3 rng-start": 5+ levels
    return f"badge {m.group(1)} tone" if m else fallback
