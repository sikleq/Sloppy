"""More for a deck's values card (owner 2026-11-09, 7.40 Spirit Bear and Entangle's Scepter: "тут тоже можно карточки
справа добавить, забьёт пустое пространство" -> "числа из текста и мана перезарядка"):

  the header's values (mana, cooldown, cast range, radius, health cost) become the card's first rows, the header keeps
  its "Active" / "Passive";
  the numbers the text says in a sentence ("moves 1100 distance", "radius to 450") get a row each, named as the game
  names them: the ability's values in that patch's files (its upgrade's for an Aghanim's part) whose number the text
  says. The text keeps its numbers.

A pane whose values stand in several tables (one per ability it names) gets none of this: there is no one table to
add to. Run by patch/card_deck.py on both sides before the values card is cut out.
"""
import functools
import re
from .html_util import strip_tags

from .html_util import TAG_RE as _TAG_RE, div_end as _div_end      # noqa: E402
from .deck_text import without_tables      # noqa: E402
_META_RE = re.compile(r'<span class="iab-meta">(.*?)</span></div>', re.S)
_META_ITEM = '<span class="iab-m">'
_META_ICON_RE = re.compile(r'icons/ui/ability/([a-z]+)\.png')
META_LABELS = {"manacost": "Mana cost", "cooldown": "Cooldown", "castrange": "Cast range", "aoe": "Radius",
               "healthcost": "Health cost"}
_NUM_RE = re.compile(r'<b class="iab-num">([^<]+)</b>')
# an Aghanim's part names its ability by the icon at its start; a chip further in the text is another ability
_ICON_RE = re.compile(r'<span class="ac-sub"><img[^>]*abilities/([a-z0-9_]+)\.(?:webp|png)')
_ROW_RE = re.compile(r'<div class="ability-change-row(?P<cls>[^"]*)">')
_VT = '<div class="value-table">'
_BODY = '<div class="ability-change-body">'


def _norm(v):
    """A number as a text and a table both may write it: "=450", "+100", "1.5s", "20%", "20.0", "3x" -> "450", "100",
    "1.5", "20", "20", "3"."""
    n = re.sub(r"[=+%sx\s]", "", _TAG_RE.sub("", v)).replace("−", "-").strip()
    return re.sub(r"(?<=\d)\.0+(?=/|$)", "", n)


def _key_label(key, slug):
    """A value the game gives no tooltip of its own, named by its key ("bear_attack_leash_range" -> "Bear attack leash
    range"), as the upgrade tables do (aghs_text._placeholder_lines)."""
    # the words the key shares with the ability's name at its start are the hero's ("lone_druid_counters_applied")
    words = [w for w in key.split("_") if w.lower() not in ("tooltip", "pct")]   # "tooltip_illusion_…": the game's words
    own = slug.split("_")
    n = 0
    while n < min(len(words) - 1, len(own)) and words[n] == own[n]:
        n += 1
    return " ".join(words[n:]).strip().capitalize()


_HOLDER_RE = re.compile(r"%([A-Za-z_]\w*)%")
_STOP = {"the", "and", "of", "to", "by", "for", "with", "his", "her", "its", "their", "per", "from", "in", "on", "at",
         "a", "an", "is", "are", "be", "or", "as", "that", "this", "it", "he", "she", "they", "all", "has", "have"}
_AROUND = 3


def _context(text, start, end, wide=False):
    """The words a number stands among: up to three before it and three after (six with `wide`, for a name to find
    its word: "suffers 20% of his max health as backlash"), small words left out."""
    n = _AROUND * 2 if wide else _AROUND
    before = re.findall(r"[a-z]+", text[:start].lower())[-n:]
    after = re.findall(r"[a-z]+", text[end:].lower())[:n]
    return frozenset(w for w in before + after if len(w) > 2 and w not in _STOP)


@functools.lru_cache(maxsize=None)
def _pairs(slug, version, kind):
    """[(label, value)] of the values the game's own description of the ability (kind "base") or of its upgrade
    ("scepter" / "shard") puts in its sentence: each "%key%" of that text, its value(s) in that patch's files, named by
    the game's tooltip, else by the header's name, else by the key. Only these: a number the text says matched to any
    value of the ability named it by chance (Sonnet 2026-11-09: "gains 20% bonus attack damage" read "Crit chance",
    "units within 600" read "Cast range")."""
    from .ability_kv import _hero_blocks
    from .aghs_text import _HEADER_LABELS, _KEYS, _num, _total
    from .loc_history import tooltip
    block = _hero_blocks(version).get(slug)
    if not isinstance(block, dict):
        return ()
    names = ([f"DOTA_Tooltip_ability_{slug}_Description"] if kind == "base" else
             [f"DOTA_Tooltip_ability_{slug}_{pre}{k}" for pre in ("", "ad_") for k in _KEYS.get(kind, ())])
    desc = next((d for d in (tooltip(n, version) for n in names) if d), None)
    if not desc:
        return ()
    av = {k.lower(): v for k, v in (block.get("AbilityValues") or {}).items()} if isinstance(
        block.get("AbilityValues"), dict) else {}
    plain = {k.lower(): v for k, v in block.items() if k.startswith("Ability") and isinstance(v, str)}
    out, done = [], set()
    flat = re.sub(r"<[^>]+>", " ", desc)
    for hm in _HOLDER_RE.finditer(flat):
        holder = hm.group(1)
        ctx = _context(flat, hm.start(), hm.end())
        key = re.sub(rf"^(?:bonus_|{kind}_)", "", holder.lower()) if kind != "base" else holder.lower()
        if key in done:
            continue
        done.add(key)
        v = av.get(key, plain.get(key))
        if v is None:
            continue
        base = v.get("value") if isinstance(v, dict) else v
        bonus = next((v[b] for b in (f"special_bonus_{kind}", "special_bonus_aghanim") if b in v), None) if (
            isinstance(v, dict) and kind != "base") else None
        named = tooltip(f"DOTA_Tooltip_ability_{slug}_{key}", version) or _HEADER_LABELS.get(key)
        label = re.sub(r"^[%$+\s]+|[:\s]+$", "", named or _key_label(key, slug)).strip().capitalize()
        if len(label) > 40 or "." in label:
            continue                            # a tooltip that is a sentence, not a name (7.41 Venomancer)
        # a name made of the key must share a word with the sentence round the number ("bear attack leash range" /
        # "if the bear moves 1100"): keys often say something else (Sonnet 2026-11-09, 7.40 Clinkz "Hero stacks" for
        # "applies 2% per attack", 7.41 Marci "Max partner penalty" for "receives 75% of these bonuses")
        need = frozenset() if named else frozenset(w for w in label.lower().split() if len(w) > 2 and w not in _STOP)
        # an upgrade's number said as its total ("to 40%") before its bonus ("by 20%"): one row, the total
        # (7.37 Luna "Rotating glaive damage" twice)
        for value in ((_total(base, bonus), bonus, base) if bonus is not None else (base,)):
            n = _num(str(value)) if value is not None else None
            if n is not None:
                out.append((label, str(n).lstrip("="), ctx, need))
    return tuple(out)


_GENERIC = {"bonus", "base", "total", "value", "amount", "percent", "tooltip"}
_CTX_SAME = {"aoe": "radius", "area": "radius", "evasion": "dodge", "evade": "dodge"}


def _shares(label, ctx):
    """How many words of a value's name stand among the words round the number ("creep damage multiplier" / "3x
    against creeps": 1). The words any value's name may have ("bonus", "total") don't count."""
    words = {w for w in re.findall(r"[a-z]+", label.lower()) if len(w) > 3 and w not in _STOP and w not in _GENERIC}
    ctx = {_CTX_SAME.get(c, c) for c in ctx}             # "in a 66 AoE" speaks of a radius (7.41 Doom)
    return sum(any(w.startswith(c) or c.startswith(w) for c in ctx if len(c) > 3) for w in words)


@functools.lru_cache(maxsize=None)
def _game_values(slug, version):
    """[(label, value, named by the game)] of the ability's own values in that patch's files, as the game lists them
    under its description ("DAMAGE PER SECOND: 30/40/50/60"): each value with a tooltip of its own, and the ones without
    under their key's name. Not the values an upgrade or a facet alone gives. The card's values are these, whether or not
    the game's description has a placeholder for them (owner 2026-11-10, 7.39e Entangling Claws: its text is all numbers,
    its description none — "только cooldown добавило, хотя можно все значения (и нужно)")."""
    from .ability_kv import _hero_blocks
    from .aghs_text import _num
    from .loc_history import tooltip
    block = _hero_blocks(version).get(slug)
    av = block.get("AbilityValues") if isinstance(block, dict) else None
    out = []
    for key, v in (av.items() if isinstance(av, dict) else ()):
        if isinstance(v, dict) and any(k.startswith("Requires") for k in v):
            continue
        n = _num(str(v.get("value", "") if isinstance(v, dict) else v))
        if n is None:
            continue
        named = tooltip(f"DOTA_Tooltip_ability_{slug}_{key}", version)
        label = re.sub(r"^[%$+\s]+|[:\s]+$", "", named or _key_label(key.lower(), slug)).strip().capitalize()
        if label and len(label) <= 40 and "." not in label and re.search(r"[A-Za-z]", label):
            out.append((label, n.lstrip("="), bool(named)))
    return tuple(out)


def _meta_rows(inner):
    """(inner without the header's values, [(label html, value html)])."""
    m = _META_RE.search(inner)
    if not m or _META_ITEM not in m.group(1):
        return inner, []
    body, rows = m.group(1), []
    # the last value ends with the header's text, its own "</span>" the last thing in it (a sentinel past the end left
    # that tag in the cell: "60/55/50</span>", which also kept the number thin and without its % — owner 2026-11-10)
    starts = [i.start() for i in re.finditer(re.escape(_META_ITEM), body)] + [len(body)]
    for a, b in zip(starts, starts[1:]):
        item = body[a + len(_META_ITEM):b - len("</span>")]
        icon = _META_ICON_RE.search(item)
        img = re.match(r"<img[^>]*>", item)
        if not icon or icon.group(1) not in META_LABELS or not img:
            return inner, []                    # a header value of a kind not known: the header stays as it is
        value = item[img.end():]
        # a bare number reads as the table's numbers do, bold (owner 2026-11-09: "Mana cost 75" stood thin)
        value = f'<b class="iab-num">{value}</b>' if "<" not in value else value
        rows.append((img.group(0) + META_LABELS[icon.group(1)], value))
    return inner[:m.start()] + '<span class="iab-meta"></span></div>' + inner[m.end():], rows


def _flat_numbers(row):
    """(the row's plain text, [(number normalised, as written, the words around it, the words further around it,
    whether it stands after "from": the value before)])."""
    parts, marks, pos, flat = [], [], 0, ""
    for m in _NUM_RE.finditer(row):
        flat += re.sub(r"\s+", " ", _TAG_RE.sub(" ", row[pos:m.start()]))
        a = len(flat)
        flat += m.group(1)
        parts.append((a, len(flat), m.group(1)))
        pos = m.end()
    flat += re.sub(r"\s+", " ", _TAG_RE.sub(" ", row[pos:]))
    for a, b, text in parts:
        marks.append((_norm(text), text, _context(flat, a, b), _context(flat, a, b, wide=True),
                      bool(re.search(r"\bfrom\s*$", flat[:a]))))
    return flat, marks


_TIME_RE = re.compile(r"\b(?:duration|cooldown|delay|interval|time)\b")


def _written(label, text):
    """The number as the text writes it; a time the text left bare gets its "s" ("for a short duration (6)" under
    "Debuff duration": "6s" — owner 2026-11-10, 7.37 Blink: "длительность слева 6, справа 5s")."""
    return text + "s" if _TIME_RE.search(label.lower()) and re.fullmatch(r"[\d./]+", text) else text


# the words of a value's name that say WHAT it is: a name made of a key must not say a thing the text does not
_STAT_WORDS = {"movespeed", "move", "movement", "attack", "damage", "health", "mana", "armor", "heal", "magic",
               "physical", "spell", "slow", "stun", "vision", "regen", "evasion", "stacks", "stack", "gold", "experience"}
_STAT_SAME = {"movespeed": "move", "movement": "move", "stacks": "stack", "hp": "health", "dps": "damage"}


def _foreign_stat(label, ctx):
    """A name made of a key that names a thing the words round the number don't (Sonnet 2026-11-10, 7.38 Starsurge:
    "Movespeed bonus radius" for "allies within 700 radius gain bonus attack speed"; Eternal Empowerment "Self
    multiplier bonus max stacks" for a %)."""
    near = {_STAT_SAME.get(c, c) for c in ctx}
    return any(_STAT_SAME.get(w, w) not in near for w in re.findall(r"[a-z]+", label.lower()) if w in _STAT_WORDS)


def _named_rows(values, marks, seen):
    """([(label, value html)], the numbers they took) of the game's values `values` the text says (`marks`, the numbers
    of all the rows that speak of that ability). A number equal by chance is not it (Sonnet 2026-11-10: 7.38 Special
    Delivery "3 bonus levels" read "Bonus hp", 7.41 Tiny "10% of Strength" read "Max stacks", Overclocking's "from 20%"
    read as the value now): a single number needs a word of the name near it, a number after "from" is the old one, and
    of several values at one place in the text the one with the most words near it is it. A list of levels the game
    names is not there by chance. Each value is read where the text speaks of it: of two equal lists the one among its
    own words (7.37 Brewmaster: "10/15/20/25/30% evasion" and "10/15/20/25/30 Attack Speed")."""
    occ = [(norm, text, wide, near) for norm, text, near, wide, was in marks if norm not in ("0", "1") and not was]
    found = {}
    bases, signed = {}, set()
    for label, value, named, *more in values:
        norm = _norm(value)
        bases[(label, norm)] = more[0] if more else None
        if len(more) > 1 and more[1]:
            signed.add((label, norm))
        cands = [(i, o) for i, o in enumerate(occ) if o[0] == norm]
        if not cands or label.lower() in seen:
            continue
        i, o = max(cands, key=lambda c: (_shares(label, c[1][2]), _shares(label, c[1][3])))
        n = _shares(label, o[2])
        if not named and _foreign_stat(label, o[2]):
            continue
        if n or (named and "/" in norm):
            found.setdefault(i, []).append((n, label, o[1], norm))
    out, used = [], set()
    for i, hits in found.items():
        top = max(h[0] for h in hits)
        for n, label, text, norm in hits:
            if n == top and label.lower() not in seen:
                seen.add(label.lower())
                used.add(occ[i][0])
                # a bonus the text says as "by 100" is written as one ("+100"), not as the value itself
                if (label, norm) in signed and not text.startswith(("+", "-", "−")):
                    text = "+" + text
                out.append((label, _against_base(label, f'<b class="iab-num">{_written(label, text)}</b>',
                                                 bases[(label, norm)])))
    return out, used


def _against_base(label, html, base):
    """An upgrade's value lit by its way against the ability's own, with the % on hover: Blink's cooldown with the
    Scepter, 12.5/10/7.5/5s, is a buff of its 13.5/11/8.5/6 — not a value new to the card (owner 2026-11-10)."""
    if not base:
        return html
    from .deck_values import _lit, _nums, _tip, _way
    # levels that do not match one to one ("to 13%" against 10/12/14%): which way it went can't be said by the
    # numbers alone (Sonnet 2026-11-10, 7.40 Rupture "Increases initial damage to 13%" lit red)
    if len(_nums(base)) != len(_nums(html)):
        return html
    kind = _way(base, html, label.lower())
    return _lit(kind, _tip(base, html, kind, label.lower()) or html) if kind else html


@functools.lru_cache(maxsize=None)
def _upgrade_values(slug, version, kind):
    """[(label, value, named by the game, the ability's own value or None)] of the values an upgrade ("scepter" /
    "shard") sets on the ability, each as
    it is with the upgrade: "AbilityCooldown" 13.5/11/8.5/6 with "special_bonus_scepter" -1 -> "Cooldown" 12.5/10/7.5/5;
    a value only the upgrade has, as it is (owner 2026-11-10, 7.37 Blink's Scepter: "перезарядку не пишем?" — its
    cooldown and its debuff's duration had no row, the game's description has no placeholder for them)."""
    from .ability_kv import _hero_blocks
    from .aghs_text import _HEADER_LABELS, _num, _total
    from .loc_history import tooltip
    block = _hero_blocks(version).get(slug)
    av = block.get("AbilityValues") if isinstance(block, dict) else None
    req = "RequiresScepter" if kind == "scepter" else "RequiresShard"
    facet = kind[len("facet:"):] if kind.startswith("facet:") else None
    out = []
    for key, v in (av.items() if isinstance(av, dict) else ()):
        if not isinstance(v, dict):
            continue
        if facet:
            # a facet's own key: "special_bonus_facet_<hero>_<facet>" (7.38 Glacial Guard on Crystal Nova)
            bonus = next((x for k, x in v.items() if k.startswith("special_bonus_facet_") and k.endswith("_" + facet)),
                         None)
        else:
            bonus = next((v[b] for b in (f"special_bonus_{kind}", "special_bonus_aghanim" if kind == "scepter" else "")
                          if b and b in v), None)
        own = None
        if bonus is not None:
            n = _total(v.get("value"), bonus) or _num(bonus)
            own = _num(str(v.get("value", "")))
            own = own if own and any(float(x) for x in own.replace("%", "").split("/")) else None
        elif str(v.get(req, "0")).strip() == "1":
            n = _num(str(v.get("value", "")))
        else:
            continue
        if n is None:
            continue
        named = tooltip(f"DOTA_Tooltip_ability_{slug}_{key}", version) or _HEADER_LABELS.get(key.lower())
        label = re.sub(r"^[%$+\s]+|[:\s]+$", "", named or _key_label(key.lower(), slug)).strip().capitalize()
        if label and len(label) <= 40 and "." not in label and re.search(r"[A-Za-z]", label):
            out.append((label, n.lstrip("=+"), bool(named), own))
            # the bonus too, as the text may say it ("Increases radius by 100": the value is 525, the text says 100)
            if own and bonus is not None and str(bonus).strip()[:1] in "+-" and _num(bonus) not in (None, n):
                out.append((label, _num(bonus).lstrip("+-"), bool(named), None, True))
    return tuple(out)


@functools.lru_cache(maxsize=None)
def facet_ability(hero_slugs, facet, version):
    """The ability a facet changes: the one whose values carry the facet's own key; None when none or several do."""
    from .ability_kv import _hero_blocks
    found = []
    for slug in hero_slugs:
        av = (_hero_blocks(version).get(slug) or {}).get("AbilityValues")
        if isinstance(av, dict) and any(isinstance(v, dict) and any(
                k.startswith("special_bonus_facet_") and k.endswith("_" + facet) for k in v) for v in av.values()):
            found.append(slug)
    return found[0] if len(found) == 1 else None


@functools.lru_cache(maxsize=None)
def _facet_key(hero_slugs, title, version):
    """The game's own name of a facet, as its values' keys carry it ("special_bonus_facet_dawnbreaker_blaze" for
    Starsurge): the facet whose tooltip name is the card's title; the title itself when the game names it so."""
    from .ability_kv import _hero_blocks
    from .loc_history import tooltip
    keys = set()
    for slug in hero_slugs:
        av = (_hero_blocks(version).get(slug) or {}).get("AbilityValues")
        for v in (av.values() if isinstance(av, dict) else ()):
            if isinstance(v, dict):
                keys |= {k[len("special_bonus_facet_"):] for k in v if k.startswith("special_bonus_facet_")}
    want = title.replace("_", " ").strip().lower()
    by_name = [k for k in keys if (tooltip(f"DOTA_Tooltip_Facet_{k}", version) or "").strip().lower().replace("'", "")
               == want.replace("'", "")]
    if len(by_name) == 1:
        return by_name[0]
    own = [k for k in keys if k.endswith("_" + title)]
    return own[0] if len(own) == 1 else None


def facet_values(inner, facet, version, have=()):
    """[(label, value html)] of the numbers a facet card's text says, named as the values the facet sets: a facet card
    has no ability of its own, its numbers are its ability's (owner 2026-11-10, 7.41 Ready to Roll)."""
    from .ability_kv import _hero_blocks
    name = re.search(r'<span class="iab-name">([^<]+)</span>', inner)
    if not name:
        return []
    from .loc_history import tooltip
    want = name.group(1).strip().lower()
    slugs = tuple(s for s in _hero_blocks(version)
                  if (tooltip(f"DOTA_Tooltip_ability_{s}", version) or "").strip().lower() == want)
    facet = _facet_key(slugs, facet, version)
    slug = facet_ability(slugs, facet, version) if slugs and facet else None
    if not slug:
        return []
    marks = []
    for m in _ROW_RE.finditer(inner):
        row = inner[m.start():_div_end(inner, m.start())]
        marks += _flat_numbers(without_tables(row))[1]
    return _named_rows(_upgrade_values(slug, version, "facet:" + facet), marks, set(have))[0]


def _text_rows(inner, slug, version, have):
    """[(label, value html)] of the numbers the pane's rows say in a sentence, named by the game."""
    out, seen = [], set(have)
    base, parts = {}, []
    for m in _ROW_RE.finditer(inner):
        row = inner[m.start():_div_end(inner, m.start())]
        row = without_tables(row)               # a row holding the table still says numbers in its text
        cls = m.group("cls")
        kind = "scepter" if "aghanim-scepter" in cls else "shard" if "aghanim-shard" in cls else "base"
        own = _ICON_RE.search(row)
        ability = own.group(1) if own else slug
        if not ability:
            continue
        # each number the row says, with the words it stands among; a 0 or 1 is a flag as often as a number
        _, marks = _flat_numbers(row)
        if kind == "base":
            base.setdefault(ability, []).extend(marks)      # the ability's rows read together
        else:
            parts.append((ability, kind, marks))
    # the ability's own values the text says: a row each, under the game's name
    for ability, marks in base.items():
        out += _named_rows(_game_values(ability, version), marks, seen)[0]
    for ability, kind, marks in parts:
        # the values the upgrade sets, then what its description's placeholders name
        rows, used = _named_rows(_upgrade_values(ability, version, kind), marks, seen)
        out += rows
        # each number with every place the text says it: of "2x as high" and "reduced by 2s" the row takes the one
        # among its name's words (Sonnet 2026-11-10, 7.41 Storm Surge "Strike cd reduction = 2x")
        said = {}
        for norm, text, ctx, wide, _ in marks:
            if norm not in ("0", "1") and norm not in used:
                entry = said.setdefault(norm, ([], set(), set()))
                entry[0].append((text, wide))
                entry[1].update(ctx)
                entry[2].update(wide)
        # a number a row of this card names already is not named again by another value (7.38 Skewer: "range to 1600"
        # read "Cast range" and "Shock speed")
        named_norms = {_row_norm(v) for _, v in out}
        # an upgrade's part says its own numbers and the ability's ("applies 5 stacks" is Entangle's own 5)
        pairs = _pairs(ability, version, kind) + _pairs(ability, version, "base")
        hits, labels = {}, set()
        for label, value, ctx, need in pairs:
            norm = _norm(value)
            # the same number among the same words as in the game's sentence ("bear moves … distance away"): a number
            # equal by chance elsewhere ("decays by 1.5% per second" vs "1.5% of the units max health") is not it
            if (norm in said and norm not in named_norms and ctx & said[norm][1] and (not need or need & said[norm][2])
                    and label.lower() not in seen and label.lower() not in labels):
                # the header's "Cast range" for a number the text calls a radius (Sonnet 2026-11-10, 7.41 Side Gunner
                # "attacks enemy units in a 700 unit radius")
                if label == "Cast range" and "radius" in said[norm][2] and "range" not in said[norm][2]:
                    label = "Radius"
                labels.add(label.lower())
                hits.setdefault(norm, []).append((label, value))
        for norm, found in hits.items():
            names = {label.lower() for label, _ in found}
            if len(names) != 1:
                continue                          # one number, several values it may be: none named, no guess
            seen.add(found[0][0].lower())
            # written as the text writes it: "20%" (the file's 20 has no sign), "450" (its "=450" a total)
            label = found[0][0]
            text = max(said[norm][0], key=lambda o: _shares(label, o[1]))[0]
            # a time the text says as "4 seconds" gets its "s" (7.38 Parting Shot "Duration = 4")
            out.append((label, f'<b class="iab-num">{_written(label, text)}</b>'))
    return out


def _row_norm(value_html):
    """The number of a row's value as _norm writes it, its % tip left out."""
    m = re.search(r'<b class="iab-num">([^<]+)</b>', value_html)
    return _norm(m.group(1) if m else value_html)


def _core_words(label):
    """A value's name without the words any name may have: "Base charge restore time" and "Charge restore time" are
    one name."""
    return {w for w in re.findall(r"[a-z]+", label.lower()) if len(w) > 2 and w not in _STOP and w not in _GENERIC}


def _dedupe(rows):
    """Rows without a second one of the same number under the same name (Sonnet 2026-11-10, 7.38 Demonic Cleanse
    "Charge restore time" and "Base charge restore time", both 70/65/60s)."""
    kept = []
    for label, value in rows:
        n, words = _row_norm(value), _core_words(_TAG_RE.sub("", label))
        if not any(n == _row_norm(v) and (words <= _core_words(_TAG_RE.sub("", l)) or _core_words(_TAG_RE.sub("", l)) <= words)
                   for l, v in kept):
            kept.append((label, value))
    return kept


def _cells(rows, first, said=False):
    """Table cells; `said`: rows named from the text's numbers carry "vt-said", so a check can tell them from the
    card's own (no style of their own)."""
    mark = " vt-said" if said else ""
    return "".join(f'<div class="vt-l{" vt-first" if first and n == 0 else ""}{mark}">{label}</div>'
                   f'<div class="vt-v{" vt-first" if first and n == 0 else ""}">{value}</div>'
                   for n, (label, value) in enumerate(rows))


def merge_parts(inner):
    """A pane of several parts, each with its own table ("Burning Army: …", "Bone and Arrow: …"): every number of a
    part's text gets a row in that part's table, named by its sentence (owner 2026-11-10: "в чём проблема, что ты не
    выносишь все значения из карточек в правую карточку значений?")."""
    from .deck_text import free_rows, merge_unit_pairs
    out, pos = [], 0
    for m in _ROW_RE.finditer(inner):
        if m.start() < pos:
            continue
        end = _div_end(inner, m.start())
        row = inner[m.start():end]
        if _VT not in row:
            continue
        i = row.index(_VT)
        j = _div_end(row, i) - len("</div>")
        table = row[i:j]
        shown = {_norm(v) for v in re.findall(r'<div class="vt-v[^"]*">(.*?)</div>', table)}
        labels = {strip_tags(l).strip().lower() for l in re.findall(r'<div class="vt-l[^"]*">(.*?)</div>', table)}
        rows = free_rows(row, shown, labels, _norm)
        out.append(inner[pos:m.start()] + row[:j] + _cells(rows, False, True) + row[j:])
        pos = end
    out.append(inner[pos:])
    return merge_unit_pairs("".join(out))


def enrich(inner, slug, version, facet=None):
    """A pane's markup with the header's values and the text's numbers in its value table (a new one if it had none),
    its rows written the one way (patch/value_tidy.py). `facet`: a facet card's facet ("glacial_guard"), whose numbers
    are the values it sets on its ability."""
    from .value_tidy import tidy
    return tidy(_enrich(inner, slug, version, facet), strip_tags(without_tables(inner)))


def _enrich(inner, slug, version, facet=None):
    if _BODY not in inner:
        return inner
    if inner.count(_VT) > 1:
        return merge_parts(inner)
    have = {re.sub(r"\s+", " ", _TAG_RE.sub("", m)).strip().lower()
            for m in re.findall(r'<div class="vt-l[^"]*">(.*?)</div>', inner)}
    inner, meta = _meta_rows(inner)
    # the card's own row of a header value says more ("245s - 5s per level, was a flat 240s"): no second one (Sonnet
    # 2026-11-09, 7.41 Marci Special Delivery "Cooldown 245" over "Cooldown 245s - 5s per level")
    meta = [(l, v) for l, v in meta if _TAG_RE.sub("", l).strip().lower() not in have]
    # a number the table shows already is not said twice (Sonnet: 7.40 Leech Seed "Radius 650" and "Heal radius 650")
    shown = {_norm(v) for v in re.findall(r'<div class="vt-v[^"]*">(.*?)</div>', inner)} | {_norm(v) for _, v in meta}
    named = have | {strip_tags(l).lower() for l, _ in meta}
    said = [r for r in (facet_values(inner, facet, version, named) if facet else _text_rows(inner, slug, version, named))
            if _row_norm(r[1]) not in shown]
    # ... and every other number of the text, named by its sentence (patch/deck_text.py); a number the dictionary of
    # names has is named there, the game's name left (owner 2026-11-10: "словарь подписей")
    from .deck_text import free_rows, merge_unit_pairs, written_numbers
    written = written_numbers(inner, _norm)
    said = [r for r in said if _row_norm(r[1]) not in written]
    free = free_rows(inner, shown | {_row_norm(v) for _, v in said}, named | {strip_tags(l).lower() for l, _ in said},
                     _norm)
    rows = meta + _dedupe(said + free)
    if not rows:
        return merge_unit_pairs(inner)
    return merge_unit_pairs(_with_rows(inner, meta, rows))


def _with_rows(inner, meta, rows):
    """The pane's markup with `rows` in its value table, the header's values (`meta`) first; a new table if none."""
    if _VT in inner:
        i = inner.index(_VT)
        j = _div_end(inner, i) - len("</div>")
        own = inner[i + len(_VT):j]
        if meta:                                 # the header's values first: theirs is the first row, no line over it
            own = own.replace('vt-l vt-first"', 'vt-l"').replace('vt-v vt-first"', 'vt-v"')
        return inner[:i] + _VT + _cells(meta, True) + own + _cells(rows[len(meta):], False, True) + inner[j:]
    b = inner.index(_BODY)
    end = _div_end(inner, b) - len("</div>")
    table = (f'<div class="ability-change-row">{_VT}{_cells(meta, True)}'
             f'{_cells(rows[len(meta):], not meta, True)}</div></div>')
    return inner[:end] + table + inner[end:]
