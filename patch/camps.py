"""Camp compositions as a light table (camp_table) — out of patch/elements.py, which grew past its size."""
from pathlib import Path


def camp_table(rows):
    """Camp compositions as a light table so the creep names line up in columns, each camp's average bounty in its own
    columns after the name (owner 2026-11-04, it was Valve's "?" on the camp):
    camp_table([("Small camp", [(3, "Pollywog", icon)], 54, 90),
                ("Medium camp", [(2, "Boglet", icon), (1, "Marshmage Apprentice", icon)], 81, 126)])
    A number that changed is (new, old, the % badge): coloured and dotted, the old one on hover (7.38 Ancient Prowlers)."""
    from .unit_numbers import changed_value

    def num(value):
        return changed_value("camp-v", value[0], value[1], value[2]) if isinstance(value, tuple) else value
    width = max(len(row[1]) for row in rows)
    # a row may also say the camp's size and side (7.42: creeps differ by side now): the size's icon before the name,
    # its words on hover, and a Side column (owner 2026-11-19)
    sided = any(len(row) > 4 for row in rows)
    cells = ['<span class="camp-name camp-type-col camp-head"></span>', '<span class="camp-cell camp-head">Camp</span>']
    if sided:
        cells.append('<span class="camp-cell camp-head">Side</span>')
    cells += ['<span class="camp-cell camp-num camp-head">Average Gold</span>',
              '<span class="camp-cell camp-num camp-head">Average XP</span>',
              f'<span class="camp-cell camp-head" style="grid-column: span {width}">Creeps</span>']
    for row in rows:
        camp, creeps, gold, xp = row[:4]
        size, side = (row[4], row[5]) if len(row) > 5 else (row[4] if len(row) > 4 else "", "")
        size = size or camp.split(" ")[0]
        name = camp   # no hint on the name: the type glyph says the size (owner 2026-11-20)
        cells.append(f'<span class="camp-name camp-type-col">{camp_glyph(size)}</span>')
        cells.append(f'<span class="camp-cell camp-label-cell">{name}</span>')
        if sided:
            cls = f" camp-side-{side.lower()}" if side else ""
            cells.append(f'<span class="camp-cell camp-side{cls}">{side or "Both"}</span>')
        cells.append(f'<span class="camp-cell camp-num camp-gold">{num(gold)}</span>')
        cells.append(f'<span class="camp-cell camp-num camp-xp">{num(xp)}</span>')
        for i in range(width):
            if i < len(creeps):
                n, name, icon = creeps[i]
                cells.append(f'<span class="camp-cell">{camp_kind(n, icon, name)}</span>')
            else:
                cells.append('<span class="camp-cell"></span>')
    return (f'<span class="camp-table{" camp-table-sided" if sided else ""}" '
            f'style="--camp-cols:{width + 3 + sided};--camp-kinds:{width}">'
            + "".join(cells) + '</span>')


_CAMP_ICONS = {"small": "../icons/camps/creepcamp_small_22", "medium": "../icons/camps/creepcamp_mid_22",
               "large": "../icons/camps/creepcamp_big_22", "ancient": "../icons/camps/creepcamp_ancient_22"}
_FACES = Path(__file__).resolve().parents[1] / "icons" / "camps" / "faces"
_UNIT_PREFIX = "npc_dota_neutral_"


def _img(path, cls=""):
    """a crisp pixel picture: the 22 px file and its @2x twin (scripts/gen/gen_camp_icons.py)"""
    klass = f' class="{cls}"' if cls else ""
    return (f'<img{klass} src="{path}.png" srcset="{path}.png 1x, {path}@2x.png 2x" alt="" aria-hidden="true" '
            f'loading="lazy">')


def camp_faces(creeps, gone=False):
    """a camp's creeps as faces only (a repeat with its count) — a cell of a "before / now" table (7.42 camp changes).
    gone=True: a camp that left the game, its faces grey like a removed entity's icon (owner 2026-11-19: "просто
    серые иконки, как мы делаем с удаленными предметами")"""
    return camp_crew(creeps, gone)


def camp_ref(name, creeps, new=False):
    """a camp named in a table whose column already says its size (7.42 "home jungle"): the faces of its creeps (a
    repeat with its count) before its name, no type glyph — camp_ref("Kobold camp", [(2, "Kobold", icon), ...]).
    new=True: a camp new in this patch, its name in the site's gold instead of Valve's "(new!)" (owner 2026-11-19)"""
    faces = camp_crew(creeps)
    cls = "camp-ref-name camp-ref-new" if new else "camp-ref-name"
    return f'<span class="camp-ref">{faces}<span class="{cls}">{name}</span></span>' if faces else name


def camp_icon(size, creeps):
    """the camp's own icon (owner 2026-11-19): the game's camp-type glyph, then each kind of
    creep's whole face, a repeated creep with its count in the corner. A creep without a face (not in
    gen_camp_icons.FACE_CX) is left out; with no faces at all the type glyph alone stays."""
    glyph = _CAMP_ICONS.get(size.lower(), "")
    parts = []
    if glyph:
        parts.append(f'<span class="camp-type">{_img(glyph)}</span>')
    for n, _name, icon in creeps:
        slug = Path(icon).stem
        slug = slug[len(_UNIT_PREFIX):] if slug.startswith(_UNIT_PREFIX) else slug
        if not (_FACES / f"{slug}.png").exists():
            continue
        count = _img(f"../icons/camps/count_{n}", "camp-count") if 1 < n < 10 else ""
        parts.append(f'<span class="camp-face">{_img(f"../icons/camps/faces/{slug}")}{count}</span>')
    return f'<span class="camp-ico">{"".join(parts)}</span>' if parts else ""


def camp_glyph(size):
    """the game's camp-type glyph alone (a column of its own, owner 2026-11-20)"""
    glyph = _CAMP_ICONS.get((size or "").lower(), "")
    return f'<span class="camp-type">{_img(glyph)}</span>' if glyph else ""


def camp_kind(n, icon, name=""):
    """one kind of a camp's creeps: its portrait once per creep, no "2x" (owner 2026-11-20: "вместо x2 повторяющиеся
    иконки"); with a name only where the camps are new (Added N new neutral camps)"""
    img = f'<img src="{icon}" alt="" width="28" height="16">'
    label = f"<b>{name}</b>" if name else ""
    return f'<span class="creep-ref camp-kind">{img * max(1, n)}{label}</span>'


def camp_crew(creeps, gone=False):
    """a camp's creeps as portraits without names, each repeated per creep (owner 2026-11-20). gone=True: a camp that
    left the game, grey."""
    refs = "".join(camp_kind(n, icon) for n, _name, icon in creeps)
    return f'<span class="camp-crew{" camp-crew-gone" if gone else ""}">{refs}</span>' if refs else ""
