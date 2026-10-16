"""Content strings follow the patch-tags.md typing rules (audit 2026-10-16): arrows only as &rarr; (a literal one is
mangled by PowerShell 5.1 / cp1251 consoles), and every Passive / Active / Toggle / Aura row of a NEW or RETURNING
item card carries t("NEW") (42 rows of 7.38-7.41 had no tag, so the NEW filter missed them)."""
import glob
import io
import os
import re
import tokenize

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = sorted(glob.glob(os.path.join(ROOT, "content", "p*.py")))


@pytest.mark.parametrize("path", FILES, ids=os.path.basename)
def test_no_literal_arrow_in_content_strings(path):
    src = open(path, encoding="utf-8").read()
    bad = [t.start[0] for t in tokenize.generate_tokens(io.StringIO(src).readline)
           if t.type == tokenize.STRING and "→" in t.string]
    assert not bad, f"use &rarr; at lines {bad}"


_ABILITY_ROW = re.compile(r'^\s*W\(li\("(?:Passive|Active|Toggle|Aura|Use)(?: \(\w+\))?: [^"]*"(?:\)\)\s*$|, extra=)')


@pytest.mark.parametrize("path", FILES, ids=os.path.basename)
def test_new_item_ability_rows_are_tagged_new(path):
    new_card, bad = False, []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        m = re.match(r'^\s*W\(item_header\("[^"]+"(.*)\)\)', line)
        if m:
            label = re.search(r'new="([^"]*)"', m.group(1))
            new_card = bool(label) and label.group(1).startswith(("New", "Returning"))
        elif re.match(r'^\s*W\((?:hero_header|unit_header|plain_header|section|subgroup)\(', line):
            new_card = False
        elif new_card and _ABILITY_ROW.match(line):
            bad.append(n)
    assert not bad, f"t(\"NEW\") missing at lines {bad}"
