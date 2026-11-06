"""An ability Arc Warden and his Tempest Double had in two versions, and now share (owner 2026-11-05, 7.38 Flux, Magnetic Field,
Spark Wraith). From 7.33 to 7.37e the two had different values: by the map side, from 7.36 by the facet (Order: each his own,
Disorder: swapped). The card shows each self's numbers on the left, their one line on the right, with the selves' icons before
the numbers; the game's own description above them on each side."""
from .cards_ability_change import ability_change
from .images import ABIL_CDN
from .mech_abilities import ability_chip

SAME_EFFECT = "Now has the same effect for both Arc Warden and Tempest Double"
_SWAP_NOTE = "With the Disorder facet the two swapped: Arc Warden had the Tempest Double's values and the other way round"


def _selves_table(columns, rows):
    """`columns`: the stats' names; `rows`: (chips, [values]). Same columns on both sides, so nothing wraps under an icon
    (owner 2026-11-05, Spark Wraith: four numbers in a line broke badly)."""
    cells = ['<span class="selves-corner"></span>'] + [f'<span class="selves-head">{c}</span>' for c in columns]
    for chips, values in rows:
        cells += [f'<span class="selves-chips">{chips}</span>'] + [f'<span>{v}</span>' for v in values]
    return f'<span class="selves-table" style="--cols:{len(columns)}">{"".join(cells)}</span>'


def two_selves_change(name, slug, old_desc, hero, double, new_desc, both, columns=None, rows_first=None):
    """`hero`, `double`: the two versions' numbers before the patch; `both`: the numbers they share after it. With `columns`
    each is a list of values, one per column, in a small table."""
    from .elements import inline_note
    hero_chip = ability_chip("Arc Warden", "../icons/heroes/arc_warden.png")
    double_chip = ability_chip("Tempest Double", f"{ABIL_CDN}arc_warden_tempest_double.png")
    note = inline_note(_SWAP_NOTE)
    if columns:
        old_lines = [_selves_table(columns, [(hero_chip, hero), (double_chip, [*double[:-1], double[-1] + note])])]
        new_lines = [_selves_table(columns, [(hero_chip + double_chip, both)])]
    else:
        old_lines = [hero_chip + hero, double_chip + double + note]
        new_lines = [hero_chip + double_chip + both]
    return ability_change(
        old=dict(name=name, slug=slug, desc=[old_desc, *old_lines]),
        new=dict(name=name, slug=slug, desc=[new_desc, *new_lines]),
        summary=SAME_EFFECT, tag="rework", rows_first=rows_first)
