"""Guard: lists inside a li() extra use inline_note (the "?" popup), never
show_list (a chevron collapsible). Denis' convention — see memory
sloppy_show_list_for_enumerations. show_list inside extra= renders differently
from the rest of the site's info popups, so it must not appear in patch content.
"""
import glob
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXTRA_SHOWLIST = re.compile(r"extra\s*=\s*show_list\(")


def test_no_show_list_in_li_extra():
    offenders = []
    for f in glob.glob(os.path.join(_ROOT, "content", "p*.py")):
        src = open(f, encoding="utf-8").read()
        if _EXTRA_SHOWLIST.search(src):
            offenders.append(os.path.basename(f))
    assert not offenders, (
        "use inline_note(...) with <br>, not extra=show_list(...), for lists in a "
        f"li() extra (the '?' popup): {offenders}"
    )
