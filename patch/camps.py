"""Camp compositions as a light table (camp_table) — out of patch/elements.py, which grew past its size."""


def camp_table(rows):
    """Camp compositions as a light table so the creep names line up in columns, each camp's average bounty in its own
    columns after the name (owner 2026-11-04, it was Valve's "?" on the camp):
    camp_table([("Small camp", [(3, "Pollywog", icon)], 54, 90),
                ("Medium camp", [(2, "Boglet", icon), (1, "Marshmage Apprentice", icon)], 81, 126)])
    A number that changed is (new, old, the % badge): coloured and dotted, the old one on hover (7.38 Ancient Prowlers)."""
    from .unit_numbers import changed_value
    from .elements import creep_ref

    def num(value):
        return changed_value("camp-v", value[0], value[1], value[2]) if isinstance(value, tuple) else value
    width = max(len(row[1]) for row in rows)
    # a row may also say the camp's size and side (7.42: creeps differ by side now): the size's icon before the name,
    # its words on hover, and a Side column (owner 2026-11-19)
    sided = any(len(row) > 4 for row in rows)
    cells = ['<span class="camp-name camp-head">Camp</span>']
    if sided:
        cells.append('<span class="camp-cell camp-head">Side</span>')
    cells += ['<span class="camp-cell camp-num camp-head">Average Gold</span>',
              '<span class="camp-cell camp-num camp-head">Average XP</span>',
              f'<span class="camp-cell camp-head" style="grid-column: span {width}">Creeps</span>']
    for row in rows:
        camp, creeps, gold, xp = row[:4]
        size, side = (row[4], row[5]) if len(row) > 5 else (row[4] if len(row) > 4 else "", "")
        icon = _CAMP_ICONS.get(size.lower(), "")
        mark = (f'<span class="camp-type iab-hint abil-ico-hint" data-tooltip="{size} camp"><img src="{icon}" alt="{size}" '
                f'width="22" height="22" loading="lazy"></span>') if icon else ""
        cells.append(f'<span class="camp-name">{mark}{camp}</span>')
        if sided:
            cls = f" camp-side-{side.lower()}" if side else ""
            cells.append(f'<span class="camp-cell camp-side{cls}">{side or "Both"}</span>')
        cells.append(f'<span class="camp-cell camp-num camp-gold">{num(gold)}</span>')
        cells.append(f'<span class="camp-cell camp-num camp-xp">{num(xp)}</span>')
        for i in range(width):
            if i < len(creeps):
                n, name, icon = creeps[i]
                cells.append(f'<span class="camp-cell">{creep_ref(name, icon, n)}</span>')
            else:
                cells.append('<span class="camp-cell"></span>')
    return (f'<span class="camp-table{" camp-table-sided" if sided else ""}" style="--camp-cols:{width + 2 + sided}">'
            + "".join(cells) + '</span>')


_CAMP_ICONS = {"small": "../icons/camps/creepcamp_small.png", "medium": "../icons/camps/creepcamp_mid.png",
               "large": "../icons/camps/creepcamp_big.png", "ancient": "../icons/camps/creepcamp_ancient.png"}
