"""A brand-new ability is a "New ability." card (new_ability / ability_change(None, …)), never a visible row (owner
2026-10-25: «разве мы так оформляем появление новой способности?» — 7.41 Objurgation, Midnight Feast, Snakebite)."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROW = re.compile(r'W\(li\("New (?:basic |innate |ultimate |passive |active )?ability\b')


def test_no_visible_new_ability_row():
    bad = []
    content = os.path.join(ROOT, "content")
    for name in sorted(os.listdir(content)):
        if not re.match(r"p\d{3}[a-z]?\.py$", name):
            continue
        src = open(os.path.join(content, name), encoding="utf-8").read()
        for m in _ROW.finditer(src):
            call = src[m.start():src.find("\n    W(", m.end()) if "\n    W(" in src[m.end():] else len(src)]
            if "covered=True" not in call:
                bad.append(f"{name}:{src.count(chr(10), 0, m.start()) + 1}")
    assert not bad, bad
