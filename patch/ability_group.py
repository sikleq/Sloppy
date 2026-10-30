"""One ability block for several abilities with the very same change (owner 2026-10-30, 7.37b Quas / Wex / Exort /
Invoke "Can now be cast during channeling and does not break invisibility"): their icons overlap left to right, the
last one whole, and the title lists the names. The generator makes it (`_postprocess_same_change_abilities`)."""
from .elements import MISSING_ICON_URL, ability
from .images import ABIL_CDN
from .state import _State

ICON_STACK_STEP = 20          # px between the icons of the stack
ICON_SIZE = 48                # px, as .ability-block > .ability-icon-wrap


def ability_group(*abilities):
    """`abilities`: two or more (title, slug) pairs, in the order Valve lists them."""
    if len(abilities) < 2:
        raise ValueError("ability_group needs two or more (title, slug) pairs")
    names = ", ".join(title for title, _ in abilities)
    out = ability(names, slug=abilities[0][1])
    icons = []
    for i, (title, slug) in enumerate(abilities):
        src = f"{ABIL_CDN}{slug}.png"
        _State.ability_icons.add(src)
        icons.append(f'<img src="{src}" alt="{title}" title="{title}" class="ability-icon-img" loading="lazy" '
                     f'width="128" height="128" data-slug="{slug}" style="left:{i * ICON_STACK_STEP}px;z-index:{i + 1}" '
                     f'onerror="this.onerror=function(){{this.style.display=\'none\'}};this.src=\'{MISSING_ICON_URL}\';">')
    width = ICON_SIZE + (len(abilities) - 1) * ICON_STACK_STEP
    stack = f'<div class="ability-icon-wrap ability-icon-stack" style="width:{width}px">{"".join(icons)}</div>'
    head, sep, rest = out.rpartition('<div class="ability-icon-wrap">')
    if not sep:
        raise ValueError(f"ability_group: no icon in the block of {names}")
    rest = rest[rest.index('</div>') + len('</div>'):]
    cut = head.rfind('<div class="ability-block')
    block_open = head[cut:].replace('class="ability-block', 'class="ability-block has-icon-stack', 1)
    return head[:cut] + block_open + stack + rest
