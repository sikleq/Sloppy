"""The dictionary of names for the numbers of the cards' text (data/rules/value_names.json, patch/deck_text.py).

    python tools/value_names.py missing            # the numbers of the built patch pages that have no name written yet
    python tools/value_names.py dump OUT.json      # every number with its sentence, key and current name, to draft names

Run after `python build_site.py`. A name is the value's short name as a reader would call it ("Root duration", "Damage
per second"); "" means no row for that number (an example in brackets, a count that names nothing)."""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from patch.deck_text import _ROW_RE, _spans, name_key, names, without_tables  # noqa: E402
from patch.html_util import div_end, plain  # noqa: E402

_PANE_RE = re.compile(r'<div class="ability-change-pane ability-change-(old|new)[^"]*"')
_TITLE_RE = re.compile(r'<h4 class="ability-title">(.*?)</h4>', re.S)
_VALUES_RE = re.compile(r'<div class="vt-l[^"]*">(.*?)</div><div class="vt-v[^"]*">(.*?)</div>', re.S)


def numbers(page_html, page):
    """[{key, page, ability, side, sentence, number, shown}] of every number a card's text says."""
    out = []
    for m in _PANE_RE.finditer(page_html):
        pane = page_html[m.start():div_end(page_html, m.start())]
        block = page_html.rfind('<div class="ability-block', 0, m.start())
        title = _TITLE_RE.search(page_html, block, m.start()) if block >= 0 else None
        card = page_html.rfind('<div class="ability-change unified-panes', 0, m.start())
        card_html = page_html[card:div_end(page_html, card)] if card >= 0 else pane
        shown = {}
        for label, value in _VALUES_RE.findall(card_html):
            shown.setdefault(plain(re.sub(r'<span class="iab-tip-pct">.*?</span></span>', "", value)), plain(label))
        for r in _ROW_RE.finditer(pane):
            row = without_tables(pane[r.start():div_end(pane, r.start())])
            flat, spans = _spans(row)
            for a, b, text in spans:
                if re.search(r"\bfrom\s*$", flat[:a]) or text.strip("+-%s") in ("0",):
                    continue
                clause = re.split(r"(?<=[.!?])\s", flat)
                sentence = next((c for c in clause if text in c), flat)
                out.append({"key": name_key(flat, a, b), "page": page, "side": m.group(1),
                            "ability": plain(title.group(1)) if title else "?", "sentence": sentence.strip()[:300],
                            "number": text, "shown": next((l for v, l in shown.items() if text.strip("+") in v), None)})
    return out


def main(argv):
    mode = argv[1] if len(argv) > 1 else "missing"
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "dist", "patches", "7.*.html"))):
        page = os.path.basename(path)[:-5]
        rows += numbers(open(path, encoding="utf-8").read(), page)
    if mode == "dump":
        with open(argv[2], "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print(len(rows), "numbers,", len({r["key"] for r in rows}), "keys ->", argv[2])
        return 0
    known = names()
    missing = [r for r in rows if r["key"] not in known]
    for r in missing[:200]:
        print(f'{r["page"]} | {r["ability"]} [{r["side"]}] | {r["number"]} | {r["key"]}')
    print(len(missing), "of", len(rows), "numbers have no name written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
