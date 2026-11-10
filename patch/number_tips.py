"""The % a changed number shows on hover in a card (the old pane's number against the new one), and a facet's
"+2 All Attributes" rows; split out of patch/elements.py (2026-11-06), which imports them back."""
import re
from .html_util import strip_tags


def _hl_numbers(text: str) -> list:
    """[(start, end, kind, plain number)] of the number highlights in a pane's html."""
    return [(m.start(), m.end(), m.group(1)[7:], strip_tags(m.group(3)))
            for m in __import__("patch.elements", fromlist=["_HL_NUM_RE"])._HL_NUM_RE.finditer(text)]


def _pair_number_tips(old_html: str, new_html: str) -> str:
    """The new pane's changed numbers get the item cards' % on hover, paired in order with the old pane's (the
    same count on both sides, else none: no guessing which was which)."""
    olds, news = _hl_numbers(old_html), _hl_numbers(new_html)
    if not news:
        return new_html
    if len(olds) == len(news):
        pairs = [(o[3], n) for o, n in zip(olds, news)]
    else:
        # the old side's numbers not marked: each new number finds the old one by its label, "Minimum lifesteal: 12%"
        # -> "Minimum lifesteal: 2%" (owner 2026-11-06, 7.38 Succubus: "при наведении на 2/14% не показывает %")
        old_plain = strip_tags(old_html)
        pairs = []
        for n in news:
            label = re.search(r"([A-Z][\w' ]{2,40}):\s*$", strip_tags(new_html[:n[0]]))
            m = label and re.search(rf"\b{re.escape(label.group(1))}:\s*([+\-−]?\d[\d.,/%s]*)", old_plain)
            if m:
                pairs.append((m.group(1).rstrip(".,"), n))
    for ov, (s, e, kind, nv) in reversed(pairs):
        span = new_html[s:e]
        inner = span[span.index(">") + 1:-len("</span>")]
        tipped = _number_tip(ov, inner, kind)
        if not tipped:
            continue
        opener = re.sub(r'class="iab-hl (iab-hl-\w+)"', r'class="iab-hl \1 iab-hl-num"', span[:span.index(">") + 1])
        new_html = new_html[:s] + opener + tipped + "</span>" + new_html[e:]
    return new_html


def _number_tip(old_plain, new_inner, kind):
    """The new number's html with the item cards' % on hover ("200/300/400" -> "200/250/300": 0% / -17% / -25%), or
    None when there is no % to say. kind: the new side's colour (buff / nerf) says which way is better."""
    from .badges import b
    from .cards_item_abilities import _iab_hint
    num = lambda s: [float(x.replace(",", "").replace("−", "-")) for x in re.findall(r"[+\-−]?\d[\d.,]*", s)]
    o, n = num(old_plain), num(strip_tags(new_inner))
    if not o or not n or (len(o) > 1 and len(n) > 1 and len(o) != len(n)) or o == n:
        return None
    mean = lambda xs: sum(xs) / len(xs)
    lower_better = (kind == "buff") == (mean(n) < mean(o)) if kind in ("buff", "nerf") else False
    pct = b(o if len(o) > 1 else o[0], n if len(n) > 1 else n[0], l=lower_better)
    return _iab_hint(new_inner, f'<span class="iab-tip-pct">{pct}</span>') if "badge" in pct else None


# A facet that takes an attribute level ("Number of times +2 All Attributes can be skilled decreased from 7 to 6") says
# it as its own row under the facet, as 7.38 Meepo's More Meepo — never inside the card's text (owner 2026-11-06:
# "у Meepo это в отдельной строке, а у Night Stalker ты вставил внутрь карточки … Надо единую систему")
_ATTR_SKILL_RE = re.compile(r"^\s*(Number of times \+2 All Attributes can be skilled [^<]*?)\s*(<.*)?$", re.S)


def _facet_attr_rows(desc):
    """(desc without its "+2 All Attributes" lines, those lines as rows' html). A desc of one string is one text, not
    a list: walking it gave one card row per letter (2026-11-07, 7.39 Malignant Mist "M / i / s / t …")."""
    if isinstance(desc, str):
        return desc, ""
    keep, rows = [], []
    for d in desc or []:
        m = _ATTR_SKILL_RE.match(d) if isinstance(d, str) else None
        if m:
            from .badges import b, t
            from .elements import li
            nums = re.search(r"from (\d+) to (\d+)", m.group(1))
            badge = m.group(2) or (b(int(nums.group(1)), int(nums.group(2))) if nums else t("MISC"))
            rows.append(li(m.group(1), badge))
        else:
            keep.append(d)
    return keep, "".join(rows)
