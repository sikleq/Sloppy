"""
Main build orchestrator — runs all patch + support page generators.
Split into modules under patch/ and content/. See patch/ directory.
"""
import sys, io

import content.p708
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
    # Build patches oldest-first (dynamics accumulate chronologically)
    content.p708.build()
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
