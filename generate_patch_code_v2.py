"""
Datafeed-aware patch-scaffold generator (v2).

Reads `/datafeed/patchnotes?version=X` JSON (cached under data/) and emits
Python source compatible with build_patch.py — preserving the full
indent_level hierarchy, facet subsections, entity titles ("New Tier 1
Artifact"), aghanims markers, and info clarifications that v1 dropped.

Usage:
    python3 generate_patch_code_v2.py <version>

E.g.: python3 generate_patch_code_v2.py 7.40

Output: /tmp/p_<version>_v2.py (or _generated_p_<version>_v2.py in repo).

Pipeline:
1. Load datafeed JSON (data/<version>_datafeed.json) + itemlist + herolist
2. Walk each top-level section:
   - general_notes[]      → section("General Updates") + plain_header per note
   - items[]              → section("Item Updates")     + item_header per item
   - neutral_items[]      → section("Neutral Item Updates") + per artifact
   - heroes[]             → section("Hero Updates") + hero_header +
                            abilities + facet subsections
   - neutral_creeps[]     → section("Neutral Creep Updates") + per creep
3. For each entity, walk notes tree:
   - indent_level == 1 → top-level li
   - indent_level == N+1 immediately after N → inline_note on parent
   - hide_dot:true row → subgroup() or <br> spacer
   - info field → inline_note attached to current row
   - aghanims field → ensure text mentions "Aghanim's Scepter"/"Aghanim's Shard"
                      so build_patch.py's li() auto-tags the aghs marker
4. Apply text-heuristic tag inference (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL)
   + l=True for cost/BAT/cooldown/manacost/cast-point keywords
   + canonical-phrase tags (Added to CM=NEW, No longer applied by
     illusions=DEL, etc.) per Sloppy memory rules.
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


# ---------- LOOKUP TABLES ----------

def _load_itemlist():
    """Item id → (display_name, engine_slug). Loaded from
    /datafeed/itemlist (cached at data/itemlist.json)."""
    p = os.path.join(_HERE, 'data', 'itemlist.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    out = {}
    for it in d.get('result', {}).get('data', {}).get('itemabilities', []):
        out[it['id']] = (it.get('name_loc') or it.get('name'),
                         (it.get('name') or '').replace('item_', ''))
    return out


def _load_herolist():
    """Hero id → (display_name, engine_slug)."""
    p = os.path.join(_HERE, 'data', 'herolist.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    out = {}
    for h in d.get('result', {}).get('data', {}).get('heroes', []):
        out[h['id']] = (h.get('name_loc') or h.get('name'),
                        (h.get('name') or '').replace('npc_dota_hero_', ''))
    return out


def _load_abilities():
    """Ability id → (display_name, engine_slug). Loaded from
    data/abilities_by_id.json which is fetched per-hero from
    /datafeed/herodata?hero_id=X. Regenerate via:

        python -c "from generate_patch_code_v2 import _refresh_abilities; _refresh_abilities()"
    """
    p = os.path.join(_HERE, 'data', 'abilities_by_id.json')
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding='utf-8'))
    out = {}
    for aid_str, meta in d.items():
        aid = int(aid_str)
        out[aid] = (meta.get('dname'), meta.get('slug'))
    return out


ITEMS = _load_itemlist()
HEROES = _load_herolist()
ABILS = _load_abilities()


# ---------- TAG HEURISTICS ----------

def _strip_html(s):
    """Drop HTML markup so heuristics see only the plain text."""
    return re.sub(r'<[^>]+>', '', s or '')


# Phrases that LOCK the tag regardless of other signals (Sloppy memory rules).
# Order: longer / more specific patterns first.
CANONICAL_TAGS = [
    (re.compile(r'\bAdded to Captains Mode\b', re.I),               'NEW'),
    (re.compile(r'\bNow can be toggled while silenced\b', re.I),    'MISC'),
    (re.compile(r'\bCan now be disassembled\b', re.I),              'NEW'),
    (re.compile(r'\bNo longer applied by illusions\b', re.I),       'DEL'),
    (re.compile(r'\bNo longer affects? ', re.I),                    'DEL'),
    (re.compile(r'\bNo longer upgraded with Aghanim', re.I),        'DEL'),
    (re.compile(r"\bNo longer.*'s? ability\b", re.I),               'DEL'),
    (re.compile(r'\bNo longer has', re.I),                          'DEL'),
    (re.compile(r'\bRemoved ', re.I),                               'DEL'),
    (re.compile(r'\bReplaced with\b', re.I),                        'REWORK'),
    (re.compile(r'\breworked\b', re.I),                             'REWORK'),
    (re.compile(r'\brescaled\b', re.I),                             'REWORK'),
    (re.compile(r'\bchanged from\b', re.I),                         'REWORK'),
    (re.compile(r'^Now ', re.I),                                    'NEW'),
    (re.compile(r'^Now also ', re.I),                               'NEW'),
]

# Cost / regen-style "lower-is-buff" keywords. When the row text matches one
# of these AND `b()` is the badge, set l=True.
LOWER_IS_BUFF = re.compile(
    r'\b('
    r'cooldown|mana ?cost|mana cost|cast (?:point|time)|cast point|cast time'
    r'|gold cost|item cost|recipe cost|total cost|cost'
    r'|base attack time|\bBAT\b'
    r'|incoming damage|damage taken|status duration|stun resistance'
    r'|magic resistance|attack point|projectile speed.*incoming'
    r')\b',
    re.I,
)


def _guess_tag(text):
    """Heuristic tag from row text. Returns 'BUFF'/'NERF'/'REWORK'/'NEW'/'DEL'/
    'MISC'/'QoL'/None. None means caller should derive from b()/badge."""
    clean = _strip_html(text)
    for rx, tag in CANONICAL_TAGS:
        if rx.search(clean):
            return tag
    # "increased/decreased by N" → leave to b() if numeric, else NERF/BUFF
    if re.search(r'\b(increased|raised)\b', clean, re.I):
        return None  # numeric badge will decide
    if re.search(r'\b(decreased|reduced|lowered|worsened)\b', clean, re.I):
        return None
    if re.search(r'\bimproved\b', clean, re.I):
        return None
    return 'MISC'


def _is_lower_better(text):
    return bool(LOWER_IS_BUFF.search(_strip_html(text)))


# ---------- B() / TEXT-TAG EMITTERS ----------

_FROM_TO_RE = re.compile(
    r'\bfrom\s+'                                # 'from '
    r'([-+]?\d+(?:\.\d+)?(?:/[-+]?\d+(?:\.\d+)?)*%?)\s+'  # OLD value(s)
    r'to\s+'                                    # 'to '
    r'([-+]?\d+(?:\.\d+)?(?:/[-+]?\d+(?:\.\d+)?)*%?)',    # NEW value(s)
)


def _split_levels(s):
    """'5/7/9/11' or '5' → [5, 7, 9, 11] or 5. Strips trailing %."""
    s = s.rstrip('%')
    parts = s.split('/')
    nums = []
    for p in parts:
        try:
            v = float(p)
            nums.append(int(v) if v == int(v) else v)
        except ValueError:
            return None
    return nums[0] if len(nums) == 1 else nums


def _emit_badge(text):
    """Try to extract from-N-to-M and emit b(...). Returns badge code str
    (e.g. 'b([5,7,9,15], [5,7,9,11])') or None if no numeric change."""
    m = _FROM_TO_RE.search(text)
    if not m:
        return None
    old = _split_levels(m.group(1))
    new = _split_levels(m.group(2))
    if old is None or new is None:
        return None
    l_arg = ', l=True' if _is_lower_better(text) else ''
    return f'b({old!r}, {new!r}{l_arg})'


def _emit_li(text, tag_override=None, aghs=None, info=None):
    """Render one W(li(...)) call. tag_override overrides heuristic; aghs is
    'scepter'/'shard' (already encoded in text if from datafeed); info is
    optional inline_note text appended."""
    txt = text.strip()
    badge_call = _emit_badge(txt)
    tag = tag_override or _guess_tag(txt)
    if badge_call:
        # Numeric change — let b() drive the tag (BUFF/NERF inferred from
        # value direction + l=True flag). Tag-text only if explicit.
        badge_str = badge_call
    else:
        badge_str = f't("{tag or "MISC"}")'
    extras = []
    if info:
        info_esc = info.replace('"', '\\"')
        extras.append(f'extra=inline_note("{info_esc}")')
    extras_str = (', ' + ', '.join(extras)) if extras else ''
    txt_esc = txt.replace('"', '\\"')
    return f'W(li("{txt_esc}", {badge_str}{extras_str}))'


# ---------- INDENT-TREE WALKER ----------

def _emit_notes(notes, ul_open_called=False):
    """Walk notes array, respecting indent_level hierarchy and special
    fields (hide_dot, info, aghanims). Returns list of source lines.

    Algorithm:
    - indent_level 1 rows → top-level li in the current ul.
    - indent_level N+1 row immediately following an N-level row → fold its
      text into the parent's `info` (inline_note).
    - hide_dot:true rows act as subgroup separators or category headers.
    - `info` field on a row → append as inline_note to that row's li.

    Returns (lines, has_content) — has_content false if all notes were
    hide_dot/empty.
    """
    lines = []
    pending_parent_text = None      # last emitted li-text (so we can patch info)
    last_indent = 0
    open_ul = ul_open_called
    has_content = False

    def open_ul_if_needed():
        nonlocal open_ul
        if not open_ul:
            lines.append('W(ul_open())')
            open_ul = True

    for i, n in enumerate(notes):
        txt = (n.get('note') or '').strip()
        lvl = n.get('indent_level', 1)
        hide = n.get('hide_dot', False)
        info = n.get('info')
        aghs = n.get('aghanims')

        if hide:
            # Section/category marker. Close current ul and emit subgroup.
            stripped = _strip_html(txt).strip()
            if open_ul:
                lines.append('W(ul_close())')
                open_ul = False
            if stripped and stripped not in ('<br>', ''):
                lines.append(f'W(subgroup("{stripped}"))')
            continue

        # Indent N+1 with previous N row → fold as inline_note on previous.
        if lvl > last_indent and lvl > 1 and lines and pending_parent_text:
            esc = txt.replace('"', '\\"')
            # Find LAST emitted W(li(...)) line index.
            li_indices = [k for k, ln in enumerate(lines) if ln.startswith('W(li(')]
            if not li_indices:
                last_indent = lvl
                continue
            last_idx = li_indices[-1]
            old_line = lines[last_idx]
            if 'extra=inline_note' in old_line:
                # Already has inline_note — append <br> to the existing text.
                lines[last_idx] = re.sub(
                    r'(extra=inline_note\(")(.+?)(")(\)+)(\)+)$',
                    lambda m: f'{m.group(1)}{m.group(2)}<br>{esc}{m.group(3)}{m.group(4)}{m.group(5)}',
                    old_line, count=1,
                )
            else:
                # Insert `, extra=inline_note("text")` BEFORE the final )) of W(li(...)).
                # Match line tail: `\)\)$` (the closing of inner badge/t() and outer li).
                lines[last_idx] = re.sub(
                    r'\)\)$',
                    lambda m: f', extra=inline_note("{esc}")))',
                    old_line, count=1,
                )
            last_indent = lvl
            continue

        open_ul_if_needed()
        lines.append(_emit_li(txt, info=info, aghs=aghs))
        pending_parent_text = txt
        last_indent = lvl
        has_content = True

    if open_ul:
        lines.append('W(ul_close())')
    return lines, has_content


# ---------- ENTITY RENDERERS ----------

def _entity_title_decoration(entity):
    """Map raw `title` HTML (e.g. '<span class="New">New Tier 1 Artifact</span>')
    to item_header() decoration args."""
    title = entity.get('title')
    if not title:
        return ''
    txt = _strip_html(title).strip()
    if 'New' in txt:
        return f', new="{txt.replace("New ", "")}"' if 'New ' in txt else ', new=True'
    return ''


def _render_general_note(note):
    """One general_notes[] entry → section title + walked content."""
    out = []
    title = note.get('title', '').strip()
    if title:
        out.append(f'\nW(plain_header("{title}"))')
    body, _ = _emit_notes(note.get('generic', []))
    out.extend(body)
    return out


def _render_item(item, neutral=False):
    """One items[] / neutral_items[] entry."""
    out = []
    aid = item.get('ability_id')
    if aid == -1:
        # Section-header style entry like "Artifact changes"
        if item.get('title'):
            out.append(f'\nW(plain_header("{_strip_html(item["title"]).strip()}"))')
        body, _ = _emit_notes(item.get('ability_notes', []))
        out.extend(body)
        return out
    name, slug = ITEMS.get(aid, (f'item_{aid}', f'item_{aid}'))
    deco = _entity_title_decoration(item)
    out.append(f'W(item_header("{name}"{deco}))')
    body, _ = _emit_notes(item.get('ability_notes', []))
    out.extend(body)
    return out


def _render_hero(hero):
    """One heroes[] entry: hero_header + hero_notes + abilities + subsections."""
    out = []
    hid = hero.get('hero_id')
    name, slug = HEROES.get(hid, (f'hero_{hid}', f'hero_{hid}'))
    out.append(f'\n# {name}')
    out.append(f'W(hero_header("{name}"))')
    # Top-level hero notes (stat changes etc.)
    hero_notes = hero.get('hero_notes', [])
    if hero_notes:
        body, _ = _emit_notes(hero_notes)
        out.extend(body)
    # Abilities
    for a in hero.get('abilities', []):
        aid = a.get('ability_id')
        aname, aslug = ABILS.get(aid, (f'ability_{aid}', f'ability_{aid}'))
        out.append(f'W(ability("{aname}", slug="{aslug}"))')
        body, _ = _emit_notes(a.get('ability_notes', []))
        out.extend(body)
    # Talents
    talents = hero.get('talent_notes', [])
    if talents:
        out.append('W(subgroup("Talents"))')
        body, _ = _emit_notes(talents)
        out.extend(body)
    # Facet subsections
    for s in hero.get('subsections', []):
        if s.get('style') == 'hero_facet':
            facet_slug = s.get('facet')
            out.append(f'W(subgroup("Facet: {s.get("title", facet_slug)}"))')
            for a in s.get('abilities', []):
                aid = a.get('ability_id')
                aname, aslug = ABILS.get(aid, (f'ability_{aid}', f'ability_{aid}'))
                out.append(f'W(ability("{aname}", slug="{aslug}"))')
                # Each row gets facet_badge() prefix
                body, _ = _emit_notes(a.get('ability_notes', []))
                # Decorate first li with facet_badge
                for j, ln in enumerate(body):
                    if ln.startswith('W(li("'):
                        body[j] = ln.replace(
                            'W(li("',
                            f'W(li(facet_badge("{facet_slug}") + " " + "',
                            1,
                        )
                        break
                out.extend(body)
    return out


def _render_neutral_creep(creep):
    """One neutral_creeps[] entry."""
    out = []
    # Creep id maps to a unit, not in herolist/itemlist. Skip slug lookup.
    cid = creep.get('npc_name') or f'creep_{creep.get("ability_id", "?")}'
    out.append(f'\n# {cid}')
    out.append(f'W(unit_header("{cid}", ""))')
    body, _ = _emit_notes(creep.get('notes', []))
    out.extend(body)
    return out


# ---------- TOP-LEVEL ----------

def generate(version):
    p = os.path.join(_HERE, 'data', f'{version}_datafeed.json')
    if not os.path.exists(p):
        print(f'No cached datafeed at {p}. Fetch first.', file=sys.stderr)
        sys.exit(2)
    d = json.load(open(p, encoding='utf-8'))

    out = [f'# Auto-generated v2 scaffold for {version}',
           f'# Source: data/{version}_datafeed.json',
           '']

    # General Updates
    if d.get('general_notes'):
        out.append('# ===== GENERAL UPDATES =====')
        out.append('W(section("General Updates"))')
        for note in d['general_notes']:
            out.extend(_render_general_note(note))

    # Item Updates
    if d.get('items'):
        out.append('\n# ===== ITEM UPDATES =====')
        out.append('W(section("Item Updates"))')
        for item in d['items']:
            out.extend(_render_item(item))

    # Neutral Items
    if d.get('neutral_items'):
        out.append('\n# ===== NEUTRAL ITEM UPDATES =====')
        out.append('W(section("Neutral Item Updates"))')
        for item in d['neutral_items']:
            out.extend(_render_item(item, neutral=True))

    # Neutral Creeps
    if d.get('neutral_creeps'):
        out.append('\n# ===== NEUTRAL CREEP UPDATES =====')
        out.append('W(section("Neutral Creep Updates"))')
        for creep in d['neutral_creeps']:
            out.extend(_render_neutral_creep(creep))

    # Hero Updates
    if d.get('heroes'):
        out.append('\n# ===== HERO UPDATES =====')
        out.append('W(section("Hero Updates"))')
        for hero in sorted(d['heroes'], key=lambda h: HEROES.get(h['hero_id'], ('', ''))[0]):
            out.extend(_render_hero(hero))

    return '\n'.join(out)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python generate_patch_code_v2.py <version>', file=sys.stderr)
        sys.exit(1)
    src = generate(sys.argv[1])
    out_path = os.path.join(_HERE, f'_generated_p_{sys.argv[1]}_v2.py')
    open(out_path, 'w', encoding='utf-8').write(src)
    print(f'Wrote {out_path} ({len(src):,} chars, {src.count(chr(10)):,} lines)')
