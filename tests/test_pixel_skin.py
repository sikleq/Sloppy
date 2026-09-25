"""Warm pixel skin: controls use the pixel icons and the shared --px-* tokens, not the old cold ones."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def test_attack_and_talent_icons_are_the_pixel_ones():
    for rel in ("builders/creeps.py", "builders/heroes_stats.py", "builders/dyn_matrix_common.py", "builders/aoe_increase.py"):
        src = _read(rel)
        assert not re.search(r"icons/ui/atk_", src), rel
        assert "icons/misc/talents.svg" not in src, rel
    for name in ("atk_melee", "atk_ranged", "icon_talents"):
        assert os.path.exists(os.path.join(ROOT, "icons", "ui", "gothic", f"{name}.png")), name


def test_skin_covers_menus_and_toolbar_controls():
    css = _read("styles.css")
    skin = css[css.index("WARM PIXEL SKIN"):]
    for sel in (".nav-submenu", ".hd-dd-menu", ".toolbar-panel", ".hs-attack-filter", ".cal-mode-select",
                ".search-box input", ".ua-switch", ".cat-filter-btn"):
        assert sel in skin, sel


def test_mana_items_per_int_block_uses_the_latest_constants():
    from builders import mana_items as m
    assert m.INT_TO_MAX_MANA == m._INT_MANA_HIST[-1][3]
    assert m.INT_TO_REGEN == m._INT_REGEN_HIST[-1][3]
    html = m._int_group()
    assert 'class="mr-int-group"' in html and html.count('data-hist="') == 2
    assert f"+{m._short(m.INT_TO_MAX_MANA)} mana" in html
