"""Aghanim's Scepter / Shard cards: a reworked upgrade (old against new text), granted abilities, the parts cards, the rows under a card, the scale card, and which rows a card already says. Split out of patch/elements.py (audit 2026-10-26 #8)."""

import html as _html
import re

from .state import _State, page_cache
from .elements import _pair_number_tips, hl, sub_ability
from .cards_item_abilities import (_CARD_CONFIRMED, _CARD_SEQ, _bold_numbers_html, _iab_meta_marks,
                                   _iab_meta_numbers, _pane_parts, _pane_values)


# ---- "Aghanim's Shard reworked: …" -> an old -> new card of the upgrade (owner 2026-10-24) ----
# Old = the game's tooltip of the previous patch, new = this patch's, both with their own numbers (patch/aghs_text.py);
# the words that differ are highlighted (removed: del, added: new, rewritten: rework). The row stays, hidden, for the
# weights and filters. No old or new tooltip (or the same text) -> no card, the row shows as before.
_AGHS_REWORK_RE = re.compile(r"^\s*Aghanim's (Scepter|Shard)(?: upgrade)? reworked\s*:", re.I)   # 7.39 Batrider: "upgrade"


_AGHS_WORD_RE = re.compile(r"\S+")


_AGHS_VALUE_RE = re.compile(r"([^:.]+):\s*([^.]+(?:\.\d+[^.]*)?)\.")


def _aghs_values_html(old, new):
    """The numbers line of both sides, compared by label: same value plain, another value rework, a label only the
    old side has del, only the new side new."""
    o = {m.group(1).strip(): m.group(2).strip() for m in _AGHS_VALUE_RE.finditer(old or "")}
    n = {m.group(1).strip(): m.group(2).strip() for m in _AGHS_VALUE_RE.finditer(new or "")}
    esc = lambda s: _html.escape(s, quote=False)
    side = lambda own, other, gone: " ".join(
        f"{esc(k)}: {esc(v)}." if other.get(k) == v
        else (f"{esc(k)}: {hl(esc(v), 'rework')}." if k in other else f"{hl(esc(k) + ': ' + esc(v), gone)}.")
        for k, v in own.items())
    return side(o, n, "del"), side(n, o, "new")


_AGHS_LABEL_SKIP = {"bonus", "max", "the", "of", "per", "a"}


# "Label: value." sentences of a numbers line; a value may hold several decimals ("12.5/15/17.5/20",
# "1.35 + 0.15 per level"): it ends at a full stop before the next capital or the end
_AGHS_VALUE_SENT_RE = re.compile(r"([^:]+?):\s*(.+?)\.(?=\s+[A-Z(]|\s*$)")


def _aghs_inline(text, loose=True):
    """One line: each number goes right after the words it names in the description ("Increases range." + "Range:
    +150." -> "Increases range (+150)."), found as the whole label or its last word said once; the rest follow the
    description on the same line (owner 2026-10-25, 60 upgrade texts of 7.38-7.41: 47 of 103 numbers name a word of
    their description)."""
    desc, _, vals = (text or "").partition("\n")
    said = desc                                 # the game's own words, before any number is put in
    pairs = [(m.group(1).strip(), m.group(2).strip()) for m in _AGHS_VALUE_SENT_RE.finditer(vals)]
    last = lambda label: ([w for w in re.findall(r"[A-Za-z]+", label) if w.lower() not in _AGHS_LABEL_SKIP] or [""])[-1]
    rest, put = [], []
    for label, value in pairs:
        bare = value.lstrip("+-")               # "-10s" and "Lowers cooldown by 10s" say the same (7.41 Arena of Blood)
        if re.search(rf"(?<![\d.]){re.escape(bare)}(?!\d|\.\d)", said):
            continue                            # the description already says it ("grants 6 armor", 7.40 Warcry)
        spot = re.search(rf"\b{re.escape(label)}\b", desc, re.I)
        # an ability's own longer text: the whole label only (7.40 "level (1%)"); a last word two labels share says
        # neither (7.40 Inner Fire: "Hero damage as heal" / "Non-hero damage as heal" -> no "heal (10%)")
        if not spot and loose and last(label) and sum(last(x).lower() == last(label).lower() for x, _ in pairs) == 1:
            hits = list(re.finditer(rf"\b{re.escape(last(label))}\b", desc, re.I))
            spot = hits[0] if len(hits) == 1 else None
        if spot and "(" not in desc[spot.end():spot.end() + 2]:
            desc = f"{desc[:spot.end()]} ({value}){desc[spot.end():]}"
            put.append(value)
        else:
            rest.append(f"{label}: {value}.")
    return " ".join([_drop_said_percent(desc, put)] + rest)


def _drop_said_percent(desc, put):
    """"Increases cast range (+200) and projectile speed (+300) by 25%." -> without "by 25%": the flat numbers put in
    already say it (owner 2026-10-25, 7.41 Venomous Gale). Only right after such a bracket ("slows by 25%" is another
    effect) and in a sentence whose every bracket is a flat number put in here."""
    flat = {v for v in put if "%" not in v}

    def one(sent):
        brackets = re.findall(r"\(([^)]*)\)", sent)
        if brackets and all(b in flat for b in brackets):
            return re.sub(r"(\([^)]*\))\s+by\s+\d+(?:\.\d+)?%(?=[.,;]|\s*$)", r"\1", sent, count=1)
        return sent
    return "".join(one(s) for s in re.split(r"(?<=[.!])(?=\s)", desc))


_NUM_TOKEN_RE = re.compile(r"^\(?[+\-]?\d[\d.,/]*(?:%|s|x)?\)?[.,;:]?$")


_LOWER_BETTER_RE = re.compile(r"cooldown|mana|cost|delay|cast point|restore time|channel", re.I)


def _rework_diff_html(old, new):
    """(old html, new html) of a reworked text: only numbers are coloured, and only when the words stayed the same —
    a rewritten meaning stays plain (owner 2026-10-25: "красим только значения, если реворк = изменение значений, а не
    смысл, иначе всё слишком покрашенное"). The new number takes the change's colour, the old the opposite one."""
    a, b_ = list(_AGHS_WORD_RE.finditer(old)), list(_AGHS_WORD_RE.finditer(new))
    esc = lambda s: _html.escape(s, quote=False)
    skeleton = lambda ms: ["#" if _NUM_TOKEN_RE.match(m.group(0)) else m.group(0).lower() for m in ms]
    if skeleton(a) != skeleton(b_):
        return esc(old), esc(new)
    def nums(s):                                # signed: a cooldown "-2s" -> "-3s" goes down, lower is better
        out = []
        for x in re.findall(r"[+\-]?\d[\d.,]*", s):
            try:
                out.append(float(x.replace(",", "").rstrip(".")))
            except ValueError:
                pass
        return out
    marks = {"old": [], "new": []}
    for i, (mo, mn) in enumerate(zip(a, b_)):
        if mo.group(0) == mn.group(0) or not _NUM_TOKEN_RE.match(mn.group(0)):
            continue
        o, n = nums(mo.group(0)), nums(mn.group(0))
        before = " ".join(m.group(0) for m in a[max(0, i - 4):i])
        lower = bool(_LOWER_BETTER_RE.search(before))
        up = (sum(n) / len(n) if n else 0) > (sum(o) / len(o) if o else 0)
        kind = "buff" if up != lower else "nerf"
        marks["old"].append((mo.start(), mo.end(), "nerf" if kind == "buff" else "buff"))
        marks["new"].append((mn.start(), mn.end(), kind))

    def paint(text, spans):
        out, pos = "", 0
        for s, e, mark in spans:
            while e > s and text[e - 1] in ".,;:)":
                e -= 1
            while s < e and text[s] == "(":
                s += 1
            out += esc(text[pos:s]) + hl(esc(text[s:e]), mark)
            pos = e
        return out + esc(text[pos:])
    return paint(old, marks["old"]), paint(new, marks["new"])


# "Aghanim's Shard: <what it does>" (NEW) / "Aghanim's Scepter granting moved from A to B" while the hero had that
# upgrade before on another ability: the upgrade moved — old card = the ability that lost it (icon + name), new = this
# one; an upgrade the hero didn't have, or one only added to another ability, stays a row (owner 2026-10-25, 7.41 Arc
# Warden's Shard Spark Wraith -> Tempest Double)
_AGHS_DEF_RE = re.compile(r"^\s*Aghanim's (Scepter|Shard)\s*:", re.I)


_AGHS_MOVED_RE = re.compile(r"^\s*Aghanim's (Scepter|Shard) (?:granting |upgrade )?moved from\b", re.I)


def _aghs_missing(kind, slug, version, prev, old, new):
    # owner 2026-10-24: "ты всегда должен знать, как было и как стало" — never a row without its card
    raise RuntimeError(f"Aghanim's {kind} under {slug} ({version}): "
                       f"{'no ' + prev + ' text' if not old else 'no ' + version + ' text' if not new else 'same text'}"
                       f" — teach patch/aghs_text.py where this tooltip or its numbers are")


def _aghs_moved_from(slug, kind, version, prev):
    """The hero's abilities that held the upgrade in `prev` and lost it now, when `slug` didn't hold it ([] = no card).
    `slug` must hold it now by the game's flags: a part added to one upgrade text that lives on another ability is
    no move (7.38 Slardar's Corrosive Haze trail; the Scepter text sits on Seaborn Sentinel)."""
    from .aghs_text import holders
    old_h, new_h = holders(_State.current_hero, kind, prev), holders(_State.current_hero, kind, version)
    if slug in old_h:
        return [slug]
    return [a for a in old_h if a not in new_h] if slug in new_h else []


def _aghs_rework_card(text, covered=False) -> bool:
    """A reworked-upgrade row under an ability: queue its old -> new card (ul_close draws it). True when queued."""
    plain = re.sub(r"<[^>]+>", "", text or "")
    m = _AGHS_REWORK_RE.match(plain)
    defn = None if m or covered else (_AGHS_DEF_RE.match(plain) or _AGHS_MOVED_RE.match(plain))
    gone = None if m or defn or covered else _AGHS_REMOVED_RE.match(plain)
    slug, version = _State.current_ability_slug, _State.current_patch_version
    if not (m or defn or gone) or not slug or not version:
        return False
    from .aghs_text import ability_name, aghs_text, holders
    from .meta import _prev_patch_version
    kind = (m or defn or gone).group(1).lower()
    prev = _prev_patch_version(version)
    up = f"Aghanim's {kind.title()}"
    if gone:
        return False                            # a row "Removed Aghanim's Shard." (li), no card
    sources = [slug] if m else _aghs_moved_from(slug, kind, version, prev)
    if not sources:
        # an upgrade this ability didn't have and no other ability lost: a card of its new text alone (owner
        # 2026-10-25: 7.41 Press the Attack's Scepter "не сделано в виде карточки"); no text of its own — the row
        new = aghs_text(slug, kind, version)
        if not new or not (slug in holders(_State.current_hero, kind, version)):
            return False
        pane = (f'<div class="ability-change-pane ability-change-new"><div class="ability-change-body">'
                f'{_bold_numbers_html(aghs_line(_html.escape(_aghs_inline(new), quote=False), kind=kind))}</div></div>')
        _State.aghs_cards.append(_under_rows_single(f"Added {up}.", "new", "aghs-change", pane))
        return True
    new = aghs_text(slug, kind, version)
    olds = [(s, aghs_text(s, kind, prev)) for s in sources]
    for s, old in olds:
        if not old or not new or (s == slug and old == new):
            _aghs_missing(kind, slug, version, prev, old, new)
    new, olds = _aghs_inline(new), [(s, _aghs_inline(old)) for s, old in olds]
    esc = lambda s: _html.escape(s, quote=False)
    if sources == [slug]:
        old_html, new_html = _rework_diff_html(olds[0][1], new)
        old_lines = [aghs_line(old_html, kind=kind)]
        caption = f"{up} reworked."
        # the old upgrade's parts on other abilities that are gone now: on the old side too, each with its icon + name
        # (owner 2026-10-25, 7.41 Wraith King: the Shard was also "Reincarnation has no mana cost")
        lost = [s for s in holders(_State.current_hero, kind, prev)
                if s != slug and s not in holders(_State.current_hero, kind, version)]
        if lost:
            gone_olds = [(s, aghs_text(s, kind, prev)) for s in lost]
            for s, old in gone_olds:
                if not old:
                    _aghs_missing(kind, s, version, prev, old, "-")
            name = lambda s, v: sub_ability(s, ability_name(s, v) or s) + " "
            old_lines = [aghs_line(name(slug, prev) + old_html, kind=kind)] + [
                aghs_line(name(s, prev) + esc(_aghs_inline(old)), kind=kind) for s, old in gone_olds]
            new_html = name(slug, version) + new_html
    else:                                       # another ability's upgrade: no word diff, its icon + name say whose
        old_lines = [aghs_line(sub_ability(s, ability_name(s, prev) or s) + " " + esc(old), kind=kind) for s, old in olds]
        new_html = sub_ability(slug, ability_name(slug, version) or slug) + " " + esc(new)
        caption = f"Added {up}."                # owner 2026-10-25: not "moved from X" — the card says from where
    pane = lambda side, lines: (f'<div class="ability-change-pane ability-change-{side}"><div class="ability-change-body">'
                                f'{_bold_numbers_html("".join(lines))}</div></div>')
    old_pane, new_pane = pane("old", old_lines), pane("new", [aghs_line(new_html, kind=kind)])
    if sources == [slug]:
        new_pane = _pair_number_tips(old_pane, new_pane)
    # no blue Aghanim strip on the caption: the card's lines already carry it (owner 2026-10-25)
    tag = "rework" if sources == [slug] else "new"
    _State.aghs_cards.append(_under_rows_card(caption, tag, "", "aghs-change", old_pane, new_pane))
    _AGHS_SHOWN.add((version, _State.current_hero, kind))     # its old parts are in this card
    return True


_GRANTED_CARDS: set = page_cache(set())  # (version, slug) of granted abilities that already have their card


def _granted_flag(slug, version):
    """"shard" / "scepter" when that patch's game files flag the ability IsGrantedByShard / IsGrantedByScepter, else
    None — the flag only: an "enabled 0 -> +1" value is an upgrade of the ability too (7.39 Sticky Napalm, 7.41
    Guardian Angel), not an ability the upgrade grants."""
    if not slug or not version:
        return None
    from .aghs_text import _FLAGS, _blocks
    block = _blocks(version).get(slug)
    for kind in ("shard", "scepter"):
        if isinstance(block, dict) and str(block.get(_FLAGS[kind][1], "0")).strip() == "1":
            return kind
    return None


def _granted_card(tags) -> bool:
    """A REWORK row under an ability an Aghanim's upgrade grants, whose text or header values the game changed: the
    old -> new card of the ability under the rows, once per ability (owner 2026-10-25, 7.41 Warp Flare: "Teleport
    distance now depends on Warp Flare cast range …" had no card). Its sides are ability cards as an ability_change's:
    "Active – granted by Aghanim's Shard" and the game's values in the header, the game's text below (owner 2026-10-26:
    as Kinetic Fence, not the upgrade's "Grants this ability: …" line). The row stays: it says more than the tooltip."""
    slug, version = _State.current_ability_slug, _State.current_patch_version
    if "rework" not in tags or not slug or not version or (version, slug) in _GRANTED_CARDS:
        return False
    from .ability_kv import ability_props
    from .aghs_text import ability_text
    from .meta import _prev_patch_version
    prev = _prev_patch_version(version)
    kind = _granted_flag(slug, version)
    if not kind or _granted_flag(slug, prev) != kind:
        return False
    old_t, new_t = ability_text(slug, prev), ability_text(slug, version)
    if not old_t or not new_t:
        raise RuntimeError(f"{slug} ({version}): no {prev if not old_t else version} description — teach "
                           f"patch/aghs_text.py ability_text where this tooltip or its numbers are")
    old_p, new_p = ability_props(slug, prev), ability_props(slug, version)
    old_sh, new_sh = _shares_level(slug, prev), _shares_level(slug, version)
    if (old_t, old_p, old_sh) == (new_t, new_p, new_sh):
        return False
    old_html, new_html = _rework_diff_html(_aghs_inline(old_t, loose=False), _aghs_inline(new_t, loose=False))
    old_d = ([f"Shares level with {old_sh}."] if old_sh else []) + [old_html]
    new_d = ([f"Shares level with {new_sh}."] if new_sh else []) + [new_html]
    _CARD_SEQ[0] += 1
    card_id = _CARD_SEQ[0]
    old_v, new_v = _pane_values(old_d, old_p), _pane_values(new_d, new_p)
    old_m, new_m = _iab_meta_marks(old_v, new_v)
    # the rows below that say exactly a header change are hidden and confirm its colour, as under an ability_change
    _State.card_meta = {k: (old_v[k], new_v[k], card_id) for k in new_m}
    old_head, old_body = _pane_parts(old_d, old_p, marks={k: (m, card_id) for k, m in old_m.items()}, granted=kind)
    new_head, new_body = _pane_parts(new_d, new_p, marks={k: (m, card_id, old_v[k]) for k, m in new_m.items()},
                                     granted=kind)
    pane = lambda side, head, body: (f'<div class="ability-change-pane ability-change-{side}">{head}'
                                     f'<div class="ability-change-body">{body}</div></div>')
    old_pane = pane("old", old_head, old_body)
    new_pane = _pair_number_tips(old_pane, pane("new", new_head, new_body))
    # the headers say "granted by Aghanim's X": the caption keeps only the stripe (owner 2026-10-26)
    _State.aghs_cards.append(_under_rows_card("Ability reworked.", "rework", f"aghanim-{kind}", "granted-change",
                                              old_pane, new_pane))
    _GRANTED_CARDS.add((version, slug))
    return True


_AGHS_SHOWN: set = page_cache(set())   # (version, hero, kind) whose old upgrade parts a card already shows


def _aghs_parts_cards() -> str:
    """The whole old upgrade -> the new one, under the ability that holds it now, when a part of it on another ability
    is gone and no card shows that part yet (owner 2026-10-25): A — the upgrade moved to an ability that had none (7.41
    Windrun -> Tailwind), B — a part is gone and the part that stayed changed (7.41f Pit of Malice + Fiend's Gate), C —
    a part gone while the rest stayed the same (7.39 Glaives of Wisdom + Brain Drain): a card without a caption under
    the ability that lost it — its row "Removed …" is the caption — all old parts -> the ones left (owner 2026-10-26;
    till then only the row).
    Each part with its ability's icon + name; drawn once per hero and upgrade, where the open ability block ends."""
    pending, _State.aghs_part_slug = _State.aghs_part_slug, None
    slug, hero = pending if pending else (None, None)
    version = _State.current_patch_version
    if not slug or not hero or not version:
        return ""
    from .aghs_text import ability_name, aghs_text, holders
    from .meta import _prev_patch_version
    prev = _prev_patch_version(version)
    if not prev:
        return ""                               # the first patch: nothing to compare with
    out = []
    for kind in ("shard", "scepter"):
        if (version, hero, kind) in _AGHS_SHOWN:
            continue
        # the parts: abilities the game flags as holding it that have a text of their own (a flag without a text is
        # the same upgrade told on another ability, 7.38 Axe)
        parts = lambda v: {s: t for s in holders(hero, kind, v) if (t := aghs_text(s, kind, v))}
        old_t, new_t = parts(prev), parts(version)
        lost = [s for s in old_t if s not in new_t]
        # this and the other abilities that hold it now and are new to it or changed it: the new side
        moved = [s for s in new_t if old_t.get(s) != new_t[s]]
        # C: the part that stayed is the same — the card under the ability that lost its part, so "Removed …" doesn't
        # read as the hero having no upgrade left (owner 2026-10-26, 7.40b Necromastery: Requiem of Souls keeps it)
        same = not moved and bool(new_t)
        if not lost or (slug not in lost if same else slug not in moved):
            continue
        olds = [(s, t) for s, t in old_t.items() if s in lost or s in moved or same]
        news = [(s, new_t[s]) for s in (new_t if same else moved)]
        esc = lambda s: _html.escape(_aghs_inline(s), quote=False)
        name = lambda s, v: sub_ability(s, ability_name(s, v) or s) + " "
        old_text = dict(olds)
        lines = {"old": [], "new": []}
        for s, t in olds:
            lines["old"].append((s, esc(t)))
        for s, t in news:
            lines["new"].append((s, esc(t)))
        # the same ability on both sides (B): its numbers coloured as in a reworked card
        for s, t in news:
            if s in old_text:
                o, n = _rework_diff_html(_aghs_inline(old_text[s]), _aghs_inline(t))
                lines["old"] = [(x, o if x == s else h) for x, h in lines["old"]]
                lines["new"] = [(x, n if x == s else h) for x, h in lines["new"]]
        pane = lambda side, v: (f'<div class="ability-change-pane ability-change-{side}"><div class="ability-change-body">'
                                + _bold_numbers_html("".join(aghs_line(name(s, v) + h, kind=kind)
                                                             for s, h in lines[side])) + '</div></div>')
        old_pane = pane("old", prev)
        new_pane = _pair_number_tips(old_pane, pane("new", version))
        up = f"Aghanim's {kind.title()}"
        b_case = same or any(s in old_t for s in moved)
        caption, tag = (f"{up} reworked.", "rework") if b_case else (f"Added {up}.", "new")
        if same:
            # no caption: the "Removed Aghanim's X." row right above is it — "reworked" under it told one change in
            # two rows, and the upgrade of the ability that kept it didn't change (owner 2026-10-26, 7.40b)
            caption = None
        out.append(_under_rows_card(caption, tag, "", "aghs-change", old_pane, new_pane))
        _AGHS_SHOWN.add((version, hero, kind))
    return "".join(out)


_AGHS_REMOVED_RE = re.compile(r"^\s*No longer upgraded with Aghanim's (Scepter|Shard)\b", re.I)


def _aghs_removed_row(plain):
    """"No longer upgraded with Aghanim's Shard" -> the row reads "Removed Aghanim's Shard.", no card of the old text
    (owner 2026-10-25, 7.41 Reincarnation: "Хватит просто строки Removed Aghanim's Shard"); None for any other row."""
    m = re.fullmatch(r"\s*No longer upgraded with Aghanim's (Scepter|Shard)\.?\s*", plain or "", re.I)
    if not m:
        return None
    up = f"Aghanim's {m.group(1).title()}"
    # the hero keeps the upgrade on another ability: only this ability's part is gone (owner 2026-10-26, 7.40b
    # Necromastery: "кажется, что удалили весь аганим, а не часть")
    return f"Removed {up} bonus from this ability." if _aghs_kept_elsewhere(m.group(1).lower()) else f"Removed {up}."


def _aghs_kept_elsewhere(kind) -> bool:
    """True when another ability of the current hero holds the upgrade in this patch, with a text of its own."""
    hero, slug, version = _State.current_hero, _State.current_ability_slug, _State.current_patch_version
    if not hero or not version:
        return False
    from .aghs_text import aghs_text, holders
    return any(s != slug and aghs_text(s, kind, version) for s in holders(hero, kind, version))


def _under_rows_single(caption, tag, card_cls, pane):
    """A one-sided card under an ability's rows: an upgrade added (its new text) or removed (its old text)."""
    return _under_rows_card(caption, tag, "", f"{card_cls} is-single-new", pane, None)


def _under_rows_card(caption, tag, li_cls, card_cls, old_pane, new_pane):
    """An old -> new card under an ability's rows (Aghanim's upgrade, what it scales with): its own caption row with
    the tag, like an ability_change's summary, and a dashed line from the ability's icon to the old pane (scripts.js
    drawAbilityChangeConnectors) — owner 2026-10-25."""
    marker = (f'<span class="aghanim-marker {li_cls[len("aghanim-"):]}"></span>' if li_cls.startswith("aghanim-")
              else "")
    li_attr = f' class="{li_cls}"' if li_cls else ""
    # caption None: the card says it all (what it scales with — "No longer levels with X." repeated its headers)
    head = (f'<ul class="changes ability-change-summary-ul under-rows-caption"><li data-tag="{tag}"{li_attr}>'
            f'<span class="badge {tag}" data-tag="{tag}">{tag.upper()}</span>'
            f'<span class="row-text">{caption}{marker}</span></li></ul>') if caption else ""
    return ('<svg class="ability-change-connector under-rows-connector" viewBox="0 0 100 100" preserveAspectRatio="none" '
            'aria-hidden="true"><path d="" fill="none" stroke="rgba(150, 146, 137, 0.45)" stroke-width="1.3" '
            'stroke-dasharray="3 3" stroke-linecap="round" /></svg>'
            + head +
            f'<div class="ability-change unified-panes {card_cls}">{old_pane}'
            + (f'<span class="ability-change-arrow">→</span>{new_pane}' if new_pane else '') + '</div>')


# "No longer levels with Marksmanship" under an ability without a card: an old -> new pair of its header strips,
# "Passive – scales with Marksmanship" (del) -> "Passive – scales with level" (new) or just "Passive" for a fixed value
# (owner 2026-10-25: Distortion Field was marked, the other 7.41 innates weren't). The game files say the kind and
# whether a value grows with hero level (hero_levelup).
_NO_LONGER_SCALES_RE = re.compile(r"^\s*No longer (?:levels(?: up)?|scales|improves) with (.+?)(?:'s level)?\.?\s*$")


def _scale_card(text) -> bool:
    m = _NO_LONGER_SCALES_RE.match(re.sub(r"<[^>]+>", "", text or ""))
    slug, version = _State.current_ability_slug, _State.current_patch_version
    if not m or not slug or not version:
        return False
    from .ability_kv import ability_props
    from .meta import _prev_patch_version
    old_p, new_p = ability_props(slug, _prev_patch_version(version)), ability_props(slug, version)
    kind_old, kind_new = old_p.get("kind") or new_p.get("kind"), new_p.get("kind") or old_p.get("kind")
    if not kind_new:
        return False                            # the files don't know the ability: the row says it
    from .aghs_text import ability_text
    prev = _prev_patch_version(version)
    old_t, new_t = ability_text(slug, prev), ability_text(slug, version)
    if not old_t or not new_t:
        # the card shows the ability's own text on both sides (owner 2026-10-25: "нет описаний"); never an empty one
        raise RuntimeError(f"{slug} ({version}): no {prev if not old_t else version} description — teach "
                           f"patch/aghs_text.py ability_text where this tooltip or its numbers are")
    old_html, new_html = _rework_diff_html(_aghs_inline(old_t, loose=False), _aghs_inline(new_t, loose=False))
    old_head, old_body = _pane_parts([f"{kind_old}, levels with {m.group(1).strip()}.", old_html], old_p)
    new_head, new_body = _pane_parts([f"{kind_new}.", new_html], new_p)
    pane = lambda side, head, body: (f'<div class="ability-change-pane ability-change-{side}">{head}'
                                     f'<div class="ability-change-body">{body}</div></div>')
    old_pane = pane("old", old_head, old_body)
    new_pane = _pair_number_tips(old_pane, pane("new", new_head, new_body))
    # no caption: "No longer levels with X." only repeats the headers (owner 2026-10-25); the row stays hidden
    _State.aghs_cards.append(_under_rows_card(None, "rework", "", "scale-change", old_pane, new_pane))
    return True


_CARD_META_ROW_RE = re.compile(
    r"^(Cooldown|Mana Cost|Health Cost|Cast Range|Radius)\s+(?:increased|decreased|changed|rescaled|reduced)\s+"
    r"from\s+(.+?)\s+to\s+([^\s,;]+)\s*$", re.I)


_CARD_META_KEY = {"cooldown": "cooldown", "mana cost": "manacost", "health cost": "healthcost",
                  "cast range": "castrange", "radius": "aoe"}


def _card_meta_covered(text) -> bool:
    """A "Cooldown increased from 20s to 25s" row whose both values the card's headers show: the row is hidden and the
    headers' values get their colour (_CARD_CONFIRMED)."""
    m = _CARD_META_ROW_RE.match(re.sub(r"<[^>]+>", "", text or ""))
    key = _CARD_META_KEY[m.group(1).lower()] if m else None
    pair = _State.card_meta.get(key) if key else None
    hit = bool(pair) and (_iab_meta_numbers(m.group(2)), _iab_meta_numbers(m.group(3))) == \
        (_iab_meta_numbers(pair[0]), _iab_meta_numbers(pair[1]))
    if hit:
        _CARD_CONFIRMED.add((pair[2], key))
    return hit


def aghs_line(text, kind="scepter", inline_note_text=None):
    note = (f'<div class="inline-note">{inline_note_text}</div>'
            if inline_note_text else '')
    return (f'<div class="ability-change-row aghanim-{kind}">'
            f'<span class="aghanim-marker {kind}"></span>{text}{note}</div>')


def aghs_shard_line(text):
    return aghs_line(text, kind="shard")


def _shares_level(slug, version):
    """The ability whose levels this one takes, as the game files say (DependentOnAbility on a many-level ability,
    7.37e Demonic Cleanse -> Demonic Purge) — the card's header says it; None for a one-level one."""
    from .aghs_text import _blocks, ability_name
    block = _blocks(version).get(slug)
    dep = block.get("DependentOnAbility") if isinstance(block, dict) else None
    if not dep or str(block.get("MaxLevel", "")).strip() == "1":
        return None
    return ability_name(dep, version) or None
