"""
apply_stats_to_build.py — Патчит build_patch.py на месте: меняет
W(li("...", t("BUFF"/"NERF"))) на bstat_h(...) / b(...) везде, где:
  • описание содержит паттерн "increased/decreased by N"
  • герой/предмет известен из контекста (после W(hero_header(...)))
  • стат есть в data/stats/{prev_version}/heroes.json или items.json

Запускать ПОСЛЕ того как data/stats/{version}/ уже есть в репо.

Workflow:
    python fetch_stats.py        (один раз — качает стоты)
    python upload_stats.py       (заливает в репо)
    python apply_stats_to_build.py    ← этот скрипт
    python build_patch.py        (пересобрать HTML)
    git add -A && git commit && git push
"""

import re
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from generate_patch_code import (
    _hero_stat_lookup, _item_stat_lookup, HERO_MAP,
)


# Reverse map: display name → internal slug
DISPLAY_TO_INTERNAL = {v: k for k, v in HERO_MAP.items()}

# ITEM_SLUG: display → slug, parsed from build_patch.py
def _load_item_slugs():
    bp = (_HERE / "build_patch.py").read_text(encoding="utf-8")
    m = re.search(r"ITEM_SLUG\s*=\s*\{(.+?)\}", bp, re.DOTALL)
    out = {}
    if m:
        for name, slug in re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1)):
            out[name] = slug
    return out

ITEM_DISPLAY_TO_INTERNAL = _load_item_slugs()


# Patterns
SAVE_HTML_RE  = re.compile(r"save_html\('patches/([^']+)\.html'\)")
WRITE_HEAD_RE = re.compile(r'write_head\("([^"]+)",')
HERO_HDR_RE   = re.compile(r'W\(hero_header\("((?:[^"\\]|\\.)+)"\)\)')
ITEM_HDR_RE   = re.compile(r'W\(item_header\("((?:[^"\\]|\\.)+)"\)\)')
PLAIN_HDR_RE  = re.compile(r'W\(plain_header\(')
UNIT_HDR_RE   = re.compile(r'W\(unit_header\(')
ABILITY_RE    = re.compile(r'W\(ability\(')
SUBGROUP_RE   = re.compile(r'W\(subgroup\(')
SECTION_RE    = re.compile(r'W\(section\(')

# W(li("desc", t("BUFF"/"NERF")))
LI_TAG_RE = re.compile(
    r'^(\s*)W\(li\("((?:[^"\\]|\\.)+)", t\("(BUFF|NERF)"\)\)\)\s*$'
)


def main():
    bp_path = _HERE / "build_patch.py"
    text = bp_path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Build line→version map.
    # Scan: for each section "write_head(version, ...) ... save_html(...)",
    # all lines BETWEEN those markers get that version.
    line_versions = [None] * len(lines)
    current_v = None
    for i, line in enumerate(lines):
        m = WRITE_HEAD_RE.search(line)
        if m:
            current_v = m.group(1)
        line_versions[i] = current_v
        m_save = SAVE_HTML_RE.search(line)
        if m_save:
            # End of section
            current_v = None

    # Walk forward, tracking hero/item context
    current_hero = None
    current_item = None
    in_hero_base = False
    in_item_base = False

    replaced = 0
    skipped_no_match = 0
    skipped_no_data = 0
    examples = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Reset/update context
        if (m := HERO_HDR_RE.search(stripped)):
            current_hero = m.group(1)
            current_item = None
            in_hero_base = True
            in_item_base = False
            continue
        if (m := ITEM_HDR_RE.search(stripped)):
            current_item = m.group(1)
            current_hero = None
            in_item_base = True
            in_hero_base = False
            continue
        if ABILITY_RE.search(stripped) or SUBGROUP_RE.search(stripped):
            in_hero_base = False
            in_item_base = False
            continue
        if (SECTION_RE.search(stripped) or PLAIN_HDR_RE.search(stripped)
                or UNIT_HDR_RE.search(stripped)):
            current_hero = None
            current_item = None
            in_hero_base = False
            in_item_base = False
            continue

        # Try to upgrade t() → bstat_h/b
        m = LI_TAG_RE.match(line)
        if not m:
            continue

        indent = m.group(1)
        desc = m.group(2)
        version = line_versions[i]
        if version is None:
            continue

        new_call = None
        ctx_label = None
        old_val = new_val = None

        if in_hero_base and current_hero and current_hero in DISPLAY_TO_INTERNAL:
            hero_internal = DISPLAY_TO_INTERNAL[current_hero]
            call, old_val, new_val = _hero_stat_lookup(desc, hero_internal, version)
            if call:
                new_call = call
                ctx_label = current_hero
        elif in_item_base and current_item and current_item in ITEM_DISPLAY_TO_INTERNAL:
            item_internal = ITEM_DISPLAY_TO_INTERNAL[current_item]
            call, old_val, new_val = _item_stat_lookup(desc, item_internal, version)
            if call:
                new_call = call
                ctx_label = current_item

        if new_call:
            # NOTE-бокс прямо внутри <li> с явными значениями (наш доп. контекст,
            # которого в патчноуте нет): "From X to Y"
            new_line = (f'{indent}W(li("{desc}", {new_call}, '
                        f'extra=note_box("From {old_val} to {new_val}")))')
            lines[i] = new_line
            replaced += 1
            if len(examples) < 10:
                examples.append(f"  [{version}] {ctx_label}: {desc[:60]} -> from {old_val} to {new_val}")
        else:
            # Could it have matched? Track for stats
            if 'by ' in desc.lower():
                if (in_hero_base and current_hero) or (in_item_base and current_item):
                    skipped_no_data += 1
                else:
                    skipped_no_match += 1

    print(f"Заменено:                {replaced}")
    print(f"Пропущено (нет в БД):    {skipped_no_data}")
    print(f"Пропущено (нет контекста): {skipped_no_match}")
    if examples:
        print(f"\nПримеры замен:")
        for e in examples:
            print(e)

    if replaced:
        bp_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\n[OK] build_patch.py updated ({replaced} replacements).")
        print("   Next: python build_patch.py && git add -A && git commit")
    else:
        print("\n[--] No replacements. Make sure data/stats/{version}/ are populated.")


if __name__ == "__main__":
    main()
