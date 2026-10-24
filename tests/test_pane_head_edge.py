"""The header strip of a card pane spans the pane edge to edge through --pt / --px: every rule that sets a pane's
padding sets them too (the new pane of an in-place card had padding 8px 14px but kept 0 / 4px, so its header stood
inset while the old one didn't — owner 2026-10-24, 7.41 Elder Dragon Form)."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANE_RE = re.compile(r"\.ability-change-(?:pane|new|old)\s*$")


def test_every_pane_padding_rule_sets_the_header_vars():
    css = open(os.path.join(ROOT, "styles.css"), encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    bad = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        sels = [s.strip() for s in sel.split(",")]
        if any(PANE_RE.search(s) for s in sels) and re.search(r"(?<![-\w])padding\s*:", body):
            if "--px" not in body or "--pt" not in body:
                bad.append(" ".join(sel.split())[:90])
    assert not bad, "set --pt / --px with the padding: " + "; ".join(bad)
