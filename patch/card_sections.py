"""Rows of a card that each start with an ability's icon stand like a table's rows, a line between them (owner 2026-11-06,
7.41 Overclocking: "есть иконки способности и строки пояснений к ним … разделителями таблицы"). A card side with no header
whose rows lead with the icons of different abilities (a facet changing two of them, 7.38 Power Capture: "нет шапки
active/passive") gives each such row a head of its own: the icon, Active / Passive, the name. Applied to the saved page
(patch/page.py), after the value tables."""
import html as _html
import re

from .value_tables import _div_end

_PANE_RE = re.compile(r'<div class="ability-change-pane[ "]')
_ROW = '<div class="ability-change-row">'
_LEAD = '<span class="acr-lead-chips">'
_SUB = '<span class="ac-sub">'
# one ability's icon leading a row: its name, its slug, the whole chips span
_ONE_CHIP_RE = re.compile(r'<span class="acr-lead-chips">(<span class="ability-chip" data-tooltip="([^"]+)"[^>]*>'
                          r'<img [^>]*?src="[^"]*/abilities/([a-z0-9_]+)\.(?:webp|png)"[^>]*>(?:<img[^>]*>)?</span>)</span>')


def _kind(slug, version):
    from .ability_kv import ability_props
    try:
        return ability_props(slug, version).get("kind") or ""
    except Exception:                           # an ability the files of that patch don't have: no kind, the name only
        return ""


# a row that opens with a bold name the side named as an ability before ("… with the Martyrdom ability" … "<b>Martyrdom:</b>
# …"): the description of a sub-ability, a line above it (owner 2026-11-06, 7.41 Zealot: "Перед Martyrdom: нужна
# разделяющая линия, т.к это уже описание под-способности")
_BOLD_ROW_RE = re.compile(r'<div class="ability-change-row"><b>([A-Z][\w\' -]{1,30}):</b>')


def _sub_ability_rows(pane):
    out, pos = [], 0
    for m in _BOLD_ROW_RE.finditer(pane):
        if re.search(rf"\b{re.escape(m.group(1))} ability\b", re.sub(r"<[^>]+>", "", pane[:m.start()])):
            out.append(pane[pos:m.start()] + '<div class="ability-change-row acr-sec">')
            pos = m.start() + len(_ROW)
    out.append(pane[pos:])
    return "".join(out)


# a plain row or one with the % badges' background (7.38 Fleshfeast's "acr-bg": its two rows stayed without heads), or
# an Aghanim's row (7.38 Invoker: Ghost Walk's Scepter row stood under Cold Snap's head)
_ROW_START_RE = re.compile(r'<div class="ability-change-row( acr-bg| aghanim-(?:scepter|shard) acr-aghs)?">')


def _pane(pane, version):
    pane = _sub_ability_rows(pane)
    starts = {m.start(): m for m in _ROW_START_RE.finditer(pane)}
    lead = [s for s, r in starts.items() if pane.startswith((_LEAD, _SUB), r.end())]
    # one ability's row among the side's other rows is a section too: a line above it (owner 2026-11-06, 7.38 Morphling's
    # facet: "Changes Morphling's Primary Attribute…" then "[Adaptive Strike] Stuns…" — "должна быть разделяющая линия")
    if not lead or (len(lead) < 2 and len(starts) < 2):
        return pane
    chips = {s: _ONE_CHIP_RE.match(pane, starts[s].end()) for s in lead}
    # the side's own head only (class "iab-head pane-head"), not another strip with the iab-head look
    heads = 'class="iab-head pane-head' not in pane and len({m.group(2) for m in chips.values() if m}) >= 2
    out, pos, last, last_kind = [], 0, None, ""
    for s in lead:
        m = chips[s]
        bg = starts[s].group(1) or ""
        aghs = "acr-aghs" in bg
        kind_now = "shard" if "aghanim-shard" in bg else "scepter" if aghs else ""
        # an Aghanim's row of the ability whose head is above it stays as it is, under that head; one of another
        # ability gets its own head (7.38 Invoker's Ghost Walk / Ice Wall rows under Cold Snap's), and so does a Shard
        # row right after the same ability's Scepter row (7.38 Agent of Gallaron's two Sun Strike upgrades)
        fresh = m and (m.group(2) != last or (last_kind and kind_now != last_kind))
        last_kind = kind_now if aghs else ""
        if aghs and not (heads and fresh):
            continue
        row = f'<div class="ability-change-row acr-sec{bg}">'
        if heads and m:
            top = pane[:s].endswith('<div class="ability-change-body">')    # the first head sits on the pane's top
            # a little room before each ability's head (owner 2026-11-06, Invoker: "небольшой отступ внутри карточки
            # перед каждой способностью")
            sec = "acr-sec acr-sec-top" if top else "acr-sec acr-sec-headed"
            row = f'<div class="ability-change-row {sec}{bg}">'
            kind = _kind(m.group(3), version)
            kind_html = f'<b class="iab-kind">{_html.escape(kind)}:</b> ' if kind else ""
            # the same strip as a card's own head (Tempest Double's "Active: Tempest Double"), words only: no other head
            # carries an icon (owner 2026-11-06: "Шапка Power Capture не такая, как везде"; then 7.38 Fleshfeast
            # "почему у нас иконки в шапках … может уберём"); the row's own icon goes with the head
            head = (f'<div class="iab-head acr-sec-head"><span class="iab-title">{kind_html}'
                    f'<span class="iab-name">{m.group(2)}</span></span></div>')
            if aghs:                     # the head on its own, the Aghanim's row with its stripe right under it
                head = (f'<div class="ability-change-row {sec} acr-sec-only">{head}</div>'
                        f'<div class="ability-change-row{bg}">')
                row = ""
            out.append(pane[pos:s] + row + head)
            pos = m.end()
            last = m.group(2)
        else:
            out.append(pane[pos:s] + row)
            pos = starts[s].end()
            last = m.group(2) if m else last
    out.append(pane[pos:])
    done = "".join(out)
    if heads:
        # every Aghanim's row of a side with heads edge to edge, a line over it: the fold's wrapper (acr-fold) parts a
        # row from its section's row, and the CSS of a row after a section missed it (owner 2026-11-06, 7.38 Quas'
        # Scepter row: "с зазором подсветки скипетра справа, в то время как ниже таких зазоров нет")
        done = _AGHS_ROW_RE.sub(r'<div class="ability-change-row\1 acr-wide">', done)
    return done


_AGHS_ROW_RE = re.compile(r'<div class="ability-change-row( aghanim-(?:scepter|shard) acr-aghs)">')


# an Aghanim's row "… from A to B" over its upgrade's old -> new card that shows A on the old side and B on the new one
# says it twice: the row is hidden, its tag kept for the filters (owner 2026-11-06, 7.41f Fiend's Gate "Aghanim's
# Scepter Cooldown decreased from 100/95/90s to 90/85/80s — дублирует то, что в карточке уже есть")
_AGHS_LI_RE = re.compile(r'<li data-tag="[^"]*" class="(aghanim-(?:scepter|shard)[^"]*)">(.*?)</li>', re.S)
_FROM_TO_RE = re.compile(r"\bfrom ([^ ]*\d[^ ]*) to ([^ ]*\d[^ ]*?)\.?$")
_PLAIN = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.sub(r'<span class="badge-group.*', "", h, flags=re.S))).strip()


def hide_rows_the_aghs_card_says(html):
    out, pos = [], 0
    for m in _AGHS_LI_RE.finditer(html):
        if "iab-covered" in m.group(1):
            continue
        ft = _FROM_TO_RE.search(_PLAIN(m.group(2)))
        if not ft:
            continue
        nxt = html.find('<div class="ability-block', m.end())
        nxt = len(html) if nxt < 0 else nxt
        card = html.find('aghs-change"', m.end(), nxt)
        if card < 0:
            continue
        new_at = html.find('ability-change-pane ability-change-new', card, nxt)
        old_side, new_side = _PLAIN(html[card:new_at]), _PLAIN(html[new_at:nxt])
        if new_at < 0 or ft.group(1) not in old_side or ft.group(2) not in new_side:
            continue
        cls_at = m.start(1)
        out.append(html[pos:cls_at] + "iab-covered covered-card ")
        pos = cls_at
    out.append(html[pos:])
    return "".join(out)


# an ability's own card row of an upgrade ("Allows to cast Nothl Projection while disabled …", 7.38) when the same
# block's Aghanim's card below shows that upgrade on its new side: the row goes, the Aghanim's card says it (owner
# 2026-11-06: "Если у героя изменения есть ещё и дополнительные от шарда/скипетра, то не дублировать внутри карточки")
_BLOCK_START = '<div class="ability-block'


def drop_upgrade_rows_said_below(html):
    out, pos = [], 0
    starts = [m.start() for m in re.finditer(re.escape(_BLOCK_START), html)] + [len(html)]
    for a, b in zip(starts, starts[1:]):
        seg = html[a:b]
        card = seg.find('aghs-change"')
        if card < 0:
            continue
        new_side = seg[seg.find("ability-change-pane ability-change-new", card):]
        cut, k = [], 0
        for m in re.finditer(r'<div class="ability-change-row aghanim-(scepter|shard)[^"]*">', seg[:card]):
            if f'ability-change-row aghanim-{m.group(1)}' in new_side and m.start() >= k:
                end = _div_end(seg, m.start())
                cut.append((m.start(), end))
                k = end
        if cut:
            for s, e in cut:
                out.append(html[pos:a + s])
                pos = a + e
    out.append(html[pos:])
    return "".join(out)


def card_sections(html, version=None):
    out, pos = [], 0
    for p in _PANE_RE.finditer(html):
        if p.start() < pos:
            continue
        end = _div_end(html, p.start())
        out.append(html[pos:p.start()] + _pane(html[p.start():end], version))
        pos = end
    out.append(html[pos:])
    return "".join(out)
