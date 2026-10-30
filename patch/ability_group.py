"""One ability block for several abilities with the very same change (owner 2026-10-30, 7.37b Quas / Wex / Exort /
Invoke "Can now be cast during channeling and does not break invisibility"). Their icons share the usual 48px square,
so the tag and the text stand where every other block has them (owner: "чтобы тег и текст не уезжал вправо"): two
icons overlap on the diagonal, three or more make a grid. Each icon grows on hover with its name above it, as the
ability chips in the rows. The generator makes it (`_postprocess_same_change_abilities`)."""
import html as _html
import math

from .elements import MISSING_ICON_URL, ability
from .images import ABIL_CDN
from .state import _State

ICON_SIZE = 48                # px, as .ability-block > .ability-icon-wrap
GAP = 2                       # px between the tiles of a grid
PAIR_TILE = 34                # px, each icon of a pair on the diagonal


def _tiles(n):
    """[(left, top, size)] of n icons in the 48px square."""
    if n == 2:
        off = ICON_SIZE - PAIR_TILE
        return [(0, 0, PAIR_TILE), (off, off, PAIR_TILE)]
    cols = math.ceil(math.sqrt(n))
    size = (ICON_SIZE - (cols - 1) * GAP) / cols
    return [((i % cols) * (size + GAP), (i // cols) * (size + GAP), size) for i in range(n)]


def _px(v):
    return f"{v:g}px"


def ability_group(*abilities):
    """`abilities`: two or more (title, slug) pairs, in the order Valve lists them."""
    if len(abilities) < 2:
        raise ValueError("ability_group needs two or more (title, slug) pairs")
    names = ", ".join(title for title, _ in abilities)
    out = ability(names, slug=abilities[0][1])
    icons = []
    for i, ((title, slug), (left, top, size)) in enumerate(zip(abilities, _tiles(len(abilities)))):
        src = f"{ABIL_CDN}{slug}.png"
        _State.ability_icons.add(src)
        name = _html.escape(title, quote=True)
        icons.append(
            f'<span class="stack-icon" data-tooltip="{name}" role="img" aria-label="{name}" '
            f'style="left:{_px(left)};top:{_px(top)};width:{_px(size)};height:{_px(size)};z-index:{i + 1}">'
            f'<img src="{src}" alt="" class="ability-icon-img" loading="lazy" width="128" height="128" '
            f'data-slug="{slug}" onerror="this.onerror=function(){{this.style.display=\'none\'}};'
            f'this.src=\'{MISSING_ICON_URL}\';"></span>')
    stack = f'<div class="ability-icon-wrap ability-icon-stack">{"".join(icons)}</div>'
    head, sep, rest = out.rpartition('<div class="ability-icon-wrap">')
    if not sep:
        raise ValueError(f"ability_group: no icon in the block of {names}")
    rest = rest[rest.index('</div>') + len('</div>'):]
    cut = head.rfind('<div class="ability-block')
    block_open = head[cut:].replace('class="ability-block', 'class="ability-block has-icon-stack', 1)
    return head[:cut] + block_open + stack + rest
