"""A list of new level values under one row's [?] becomes one table of every level (owner 2026-11-08, 7.38 Invoker
"Added values for levels 9 and 10": the 21-line list was "массивный", variant B chosen — all levels, the new ones
gold). The full levels come from the hero's file of that patch; a line the file does not confirm leaves the row as it
was."""
import re

_ROW_RE = re.compile(r'^(?P<ind>\s*)W\(li\("Added values for (?P<trig>levels? (?P<lv>[\d, and]+))", t\("NEW"\), '
                     r'extra=inline_note\("(?P<note>[^"]+)"\)\)\)\s*$')
_ITEM_RE = re.compile(r'^(?P<ab>[^:]+): (?P<label>.+?)(?: \((?P<scale>[^)]+)\))? (?P<vals>[\d.]+(?:/[\d.]+)+)'
                      r'(?P<unit>%|s)?$')
_NAMED_RE = re.compile(r'\("([^"]+)", (?:slug=)?"([a-z0-9_]+)"\)')
_HERO_RE = re.compile(r'W\(hero_header\(')


def _hero_file(version, slugs):
    from patch import game_files
    for slug in slugs:
        parts = slug.split("_")
        for n in range(len(parts) - 1, 0, -1):
            text = game_files.npc(version, f"heroes/npc_dota_hero_{'_'.join(parts[:n])}.txt")
            if text:
                return text
    return None


def _field_levels(kv_ability, tail):
    """(key, values string) of the field whose last len(tail) levels are `tail` (sign dropped: slows are negative)."""
    num = lambda s: abs(float(s))
    for key, field in (kv_ability.get("AbilityValues") or {}).items():
        raw = field.get("value") if isinstance(field, dict) else field
        vals = str(raw or "").split()
        if len(vals) > len(tail) and [num(v) for v in vals[-len(tail):]] == [num(v) for v in tail]:
            return key, " ".join(v.lstrip("-") for v in vals)
    return None, None


_TIP_SCALE_RE = re.compile(r"\s*\(<font[^>]*>(\w+)</font>\)")


def _unlisted(slug, name, kv_ability, used, count, version, seen):
    """The ability's other values of `count` levels the notes' list left out (owner 2026-11-08, 7.38 Ice Wall: "нет строки
    damage per second" — the game file has it, the notes don't): label and orb from the game's own tooltip."""
    from patch.aghs_text import tooltip
    rows = []
    for key, field in (kv_ability.get("AbilityValues") or {}).items():
        if key in used or not isinstance(field, dict) or not field.get("levelkey"):
            continue
        vals = str(field.get("value") or "").split()
        tip = tooltip(f"DOTA_Tooltip_ability_{slug}_{key}", version) or ""
        if len(vals) != count or not tip:
            continue
        orb = _TIP_SCALE_RE.search(tip)
        label = _TIP_SCALE_RE.sub("", tip).replace("\\n", "").strip().rstrip(":").strip()
        pct = label.startswith("%")
        label = label.lstrip("%").strip().capitalize()
        scale = f"{slug.split('_')[0]}_{orb.group(1).lower()}" if orb else None
        unit = "%" if pct else "s" if "duration" in key or "time" in key else ""
        # a slow is negative in the file and positive in the notes; a value going through zero keeps its signs
        # (Ghost Walk's self speed -20 … 25)
        nums = [float(v) for v in vals]
        shown = " ".join(v.lstrip("-") for v in vals) if all(x <= 0 for x in nums) else " ".join(vals)
        if shown in seen:
            continue                     # the same numbers under another key (a facet's copy): once
        seen.add(shown)
        rows.append((slug, name, label, scale, shown, unit))
    return rows


def _rows(note, names, kv, version=None):
    rows, used = [], {}
    for item in note.split("<br>"):
        m = _ITEM_RE.match(item.strip())
        slug = names.get(m.group("ab")) if m else None
        key, levels = _field_levels(kv.get(slug) or {}, m.group("vals").split("/")) if slug else (None, None)
        if not levels:
            return None
        used.setdefault(slug, set()).add(key)
        scale = names.get(m.group("scale")) if m.group("scale") else None
        rows.append((slug, m.group("ab"), m.group("label"), scale, levels, m.group("unit") or ""))
    if version:
        count = max(len(r[4].split()) for r in rows)
        out = []
        for i, r in enumerate(rows):
            out.append(r)
            last_of_ability = i + 1 == len(rows) or rows[i + 1][0] != r[0]
            if last_of_ability and r[0] in used:
                seen = {x[4] for x in rows if x[0] == r[0]}
                out += _unlisted(r[0], r[1], kv.get(r[0]) or {}, used.pop(r[0]), count, version, seen)
        rows = out
    return rows


def _postprocess_level_values(lines, version):
    from patch.ability_kv import parse_kv
    out, names, kv_cache = [], {}, {}
    for line in lines:
        if _HERO_RE.search(line):
            names = {}
        names.update(dict(_NAMED_RE.findall(line)))
        m = _ROW_RE.match(line)
        if not m or not names:
            out.append(line)
            continue
        key = tuple(sorted(names.values()))
        if key not in kv_cache:
            text = _hero_file(version, names.values())
            root = next(iter(parse_kv(text).values()), {}) if text else {}
            kv_cache[key] = root if isinstance(root, dict) else {}
        rows = _rows(m.group("note"), names, kv_cache[key], version)
        new_from = min(int(x) for x in re.findall(r"\d+", m.group("lv")))
        if not rows:
            out.append(line)
            continue
        out.append(f'{m.group("ind")}W(li_level_values("Added values for ", "{m.group("trig")}", {rows!r}, '
                   f'new_from={new_from}, tag=t("NEW")))')
    return out
