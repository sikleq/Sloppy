"""
Main build orchestrator — runs all patch + support page generators.
Split into modules under patch/ and content/. See patch/ directory.
"""
import sys, io
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

import content.p708
import content.p739b
import content.p739c
import content.p739d
import content.p739e
import content.p740
import content.p740b
import content.p740c
import content.p741
import content.p741a
import content.p741b
import content.p741c
import content.p741d

from patch.rosters import build_rosters
from patch.calendar import save_calendar_html
from patch.index_page import save_index_html

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if "--latest" in sys.argv:
        # Local dev shortcut: only the newest patch, skip calendar/index/rosters
        content.p741d.build()
    else:
        # Build oldest-first (dynamics accumulate chronologically)
        content.p708.build()
        content.p739b.build()
        content.p739c.build()
        content.p739d.build()
        content.p739e.build()
        content.p740.build()
        content.p740b.build()
        content.p740c.build()
        content.p741.build()
        content.p741a.build()
        content.p741b.build()
        content.p741c.build()
        content.p741d.build()

        build_rosters()
        save_calendar_html()
        save_index_html()
