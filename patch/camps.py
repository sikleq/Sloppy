"""Camp compositions as a light table (camp_table) — out of patch/elements.py, which grew past its size."""


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
    # "Camp" above the glyph + name pair: no line before it, as in the rows (camp-label-cell; owner 2026-11-21:
    # "вертикальная линия лишь кусочек перед camp")
    cells = ['<span class="camp-name camp-type-col camp-head"></span>',
             '<span class="camp-cell camp-label-cell camp-head">Camp</span>']
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
                cells.append(f'<span class="camp-cell">{camp_kind(n, icon, name)}</span>')   # its name beside it
            else:
                cells.append('<span class="camp-cell"></span>')
    return (f'<span class="camp-table{" camp-table-sided" if sided else ""}" '
            f'style="--camp-cols:{width + 3 + sided};--camp-kinds:{width}">'
            + "".join(cells) + '</span>')


_CAMP_ICONS = {"small": "../icons/camps/creepcamp_small_22", "medium": "../icons/camps/creepcamp_mid_22",
               "large": "../icons/camps/creepcamp_big_22", "ancient": "../icons/camps/creepcamp_ancient_22"}


def _img(path, cls=""):
    """a crisp pixel picture: the 22 px file and its @2x twin (scripts/gen/gen_camp_icons.py)"""
    klass = f' class="{cls}"' if cls else ""
    return (f'<img{klass} src="{path}.png" srcset="{path}.png 1x, {path}@2x.png 2x" alt="" aria-hidden="true" '
            f'loading="lazy">')


def camp_faces(creeps, gone=False):
    """a camp's creeps as portraits only (a repeat: its portrait again) — a cell of a "before / now" table (7.42 camp
    changes). gone=True: a camp that left the game, its portraits grey like a removed entity's icon (owner 2026-11-19: "просто
    серые иконки, как мы делаем с удаленными предметами")"""
    return camp_crew(creeps, gone)


def camp_ref(name, creeps, new=False):
    """a camp named in a table whose column already says its size (7.42 "home jungle"): the portraits of its creeps (a
    repeat: its portrait again) before its name, no type glyph — camp_ref("Kobold camp", [(2, "Kobold", icon), ...]).
    new=True: a camp new in this patch, its name in the site's gold instead of Valve's "(new!)" (owner 2026-11-19)"""
    faces = camp_crew(creeps)
    cls = "camp-ref-name camp-ref-new" if new else "camp-ref-name"
    return f'<span class="camp-ref">{faces}<span class="{cls}">{name}</span></span>' if faces else name


def camp_glyph(size):
    """the game's camp-type glyph alone (a column of its own, owner 2026-11-20)"""
    glyph = _CAMP_ICONS.get((size or "").lower(), "")
    return f'<span class="camp-type">{_img(glyph)}</span>' if glyph else ""


_NAMES = {}


def _creep_names():
    """the site's creep names (CREEP_DISPLAY_NAMES of builders/creeps.py), read as a literal: patch/ imports nothing
    from builders/ (tests/test_layers.py), and builders/entity_changes.py reads that dict the same way"""
    if not _NAMES:
        import ast
        import os as _os
        path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "builders", "creeps.py")
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", "") == "CREEP_DISPLAY_NAMES" for t in n.targets))
        _NAMES.update(ast.literal_eval(node.value))
    return _NAMES


def _crew(row):
    """[(count, display name, icon)] of a make-up's npc list, in the order the game lists them"""
    from .images import NEUTRAL_CDN
    CREEP_DISPLAY_NAMES = _creep_names()
    counts = {}
    for npc in row:
        counts[npc] = counts.get(npc, 0) + 1
    return [(n, CREEP_DISPLAY_NAMES[npc], NEUTRAL_CDN + npc[len("npc_dota_neutral_"):] + ".png")
            for npc, n in counts.items()]


def home_jungle_table(patch, map_code):
    """The "home jungle" table (7.42) built from the game: the make-ups each side's small / medium / large spawners may
    roll (patch/camp_sides.py: the map's spawn ranges + server.dll's camp table), their creeps as portraits and the
    camp's name from data/rules/camp_names.json (owner 2026-11-22: "научи автоматически"). A make-up the patch before
    did not have is a new camp (gold name). Flooded camps (make-up 7) and ancients (both sides) are left out."""
    import json as _json
    import os as _os
    from .camp_sides import camp_table as _table, spawners
    from .mech_abilities import mech_table
    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    with open(_os.path.join(root, "data", "rules", "camp_names.json"), encoding="utf-8") as f:
        names = _json.load(f)["names"]
    with open(_os.path.join(root, "data", "rules", "camp_table.json"), encoding="utf-8") as f:
        versions = [v for v in _json.load(f) if not v.startswith("_")]
    k = versions.index(patch)
    # new = none of its creeps was in a camp before (7.42 Radigull, Eimermole, Odobenus); a camp whose make-up changed
    # (Kobold 3 -> 2, Large Satyr's Banisher -> Mindstealer) is not new
    old = ({n for rows in _table(versions[k - 1]).values() for r in rows for n in r} if k else None)
    table = _table(patch)
    rolls = {}
    for side, size, first, last in spawners(map_code):
        if size < 3 and (first, last) != (7, 7):
            rolls.setdefault((side, size), set()).update(range(first, last + 1))

    def camp(row):
        key = "|".join(sorted(row))
        if key not in names:
            raise KeyError(f"data/rules/camp_names.json: no name for the camp {key}")
        return camp_ref(names[key], _crew(row), new=old is not None and not old & set(row))
    rows = [[side.title()] + ["".join(camp(table[size][i - 1]) for i in sorted(rolls.get((side, size), ())))
                              for size in range(3)] for side in ("radiant", "dire")]
    return mech_table(["Side", camp_glyph("small") + "Small camps", camp_glyph("medium") + "Medium camps",
                       camp_glyph("large") + "Large camps"], rows, cls="camp-jungle")


def camp_kind(n, icon, name="", tip=""):
    """one kind of a camp's creeps: its portrait once per creep, no "2x" (owner 2026-11-20: "вместо x2 повторяющиеся
    иконки"); with a name only where the camps are new (Added N new neutral camps). tip: the creep's name in gold on
    hover (owner 2026-11-20: "золотым тоже у многих не написано в разных таблицах")"""
    import html as _h
    hint = (f' class="abil-ico-hint" data-tooltip="{_h.escape(f"<b class=\"tip-head\">{_h.escape(tip)}</b>", quote=True)}"'
            if tip else "")
    img = f'<img{hint} src="{icon}" alt="" width="28" height="16">'
    # the name plain, after the portraits, as the home jungle's camp names (owner 2026-11-20: "убрать жирность")
    label = f'<span class="camp-kind-name">{name}</span>' if name else ""
    return f'<span class="creep-ref camp-kind">{img * max(1, n)}{label}</span>'


def camp_crew(creeps, gone=False):
    """a camp's creeps as portraits without names, each repeated per creep (owner 2026-11-20). gone=True: a camp that
    left the game, grey."""
    refs = "".join(camp_kind(n, icon, tip=name) for n, name, icon in creeps)
    return f'<span class="camp-crew{" camp-crew-gone" if gone else ""}">{refs}</span>' if refs else ""
