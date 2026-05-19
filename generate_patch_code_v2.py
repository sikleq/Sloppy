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
# IMPORTANT: BUFF-override patterns must come BEFORE DEL patterns since
# 'no longer has a penalty' should NOT be DEL.
CANONICAL_TAGS = [
    # BUFF first — removing a penalty / restriction is positive (memory rule
    # sloppy_no_longer_penalty_is_buff). Tightly anchored so legitimate DEL
    # phrasings don't accidentally match.
    (re.compile(r'\bno longer has (?:an? |the )?\w+ (?:penalty|restriction|drawback|downside|debuff slow)\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer (?:reduces|decreases) ', re.I),       'BUFF'),
    (re.compile(r'\bno longer requires (?:a |an )?(?:skill point|mana|charge)', re.I), 'BUFF'),
    # NEW — new mechanic / capability added
    (re.compile(r'\bAdded to Captains Mode\b', re.I),               'NEW'),
    (re.compile(r'\bCan now be disassembled\b', re.I),              'NEW'),
    (re.compile(r'^Now (?:also )?(?:passively |actively )?(?:grants|provides|gains?|adds?|applies?|deals?|increases|fires?|spawns?|summons?)', re.I), 'NEW'),
    (re.compile(r'^Added\b', re.I),                                 'NEW'),
    # MISC — mechanic toggle, classification change, polish
    (re.compile(r'\bNow can be toggled while silenced\b', re.I),    'MISC'),
    (re.compile(r'\bClassified as\b', re.I),                        'MISC'),
    # DEL — explicit removal / no-longer-targets / no-longer-applies
    (re.compile(r'\bcan no longer (?:target|be cast|be used|trigger)', re.I), 'NERF'),
    (re.compile(r'\bno longer applied by illusions\b', re.I),       'DEL'),
    (re.compile(r'\bno longer (?:applies?|affects?) ', re.I),       'DEL'),
    (re.compile(r'\bno longer upgraded with Aghanim', re.I),        'DEL'),
    (re.compile(r"\bno longer.*'s? ability\b", re.I),               'DEL'),
    (re.compile(r'\bno longer (?:provides|grants|deals|fires|spawns|summons|adds|increases|works|considered)\b', re.I), 'DEL'),
    (re.compile(r'\bno longer levels with\b', re.I),                'REWORK'),  # memory rule: structural
    (re.compile(r'^No longer has\b', re.I),                         'DEL'),
    (re.compile(r'\bRemoved\b', re.I),                              'DEL'),
    # REWORK
    (re.compile(r'\breplaced with\b', re.I),                        'REWORK'),
    (re.compile(r'\breworked\b', re.I),                             'REWORK'),
    (re.compile(r'\brescaled\b', re.I),                             'REWORK'),
    (re.compile(r'\bchanged from\b', re.I),                         'REWORK'),
    # General "Now ..." → NEW unless context says otherwise
    (re.compile(r'^Now also\b', re.I),                              'NEW'),
    (re.compile(r'^Now ', re.I),                                    'NEW'),
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

        # L2 row with short header-like text AND followed by L3 children
        # → treat as subgroup (e.g. "Items", "Heroes", "Neutral Creeps"
        # inside Invulnerability Targeting). Detection: short text (≤3
        # words, no period) AND next note has lvl > this lvl.
        clean = _strip_html(txt).strip()
        next_lvl = notes[i + 1].get('indent_level', 1) if i + 1 < len(notes) else 0
        is_short_header = (
            lvl >= 2
            and len(clean.split()) <= 3
            and not clean.endswith('.')
            and not clean.endswith(':')
            and next_lvl > lvl
        )
        if is_short_header:
            if open_ul:
                lines.append('W(ul_close())')
                open_ul = False
            lines.append(f'W(subgroup("{clean}"))')
            last_indent = lvl
            pending_parent_text = None
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


def _render_item(item, version, neutral=False):
    """One items[] / neutral_items[] entry. `version` is the current
    patch (e.g. "7.40") — used to emit auto_components_change(item,
    version) for recipe-changed items."""
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
    # Detect "Recipe changed" — first note with "Recipe changed" text →
    # decorate item_header(changed=True), drop that row, and emit an
    # auto_components_change(name, version) call right below the header
    # so the OLD→NEW component diff renders automatically. items.json
    # carries per-patch ItemRequirements + ItemCost, so this lookup is
    # fully data-driven (no manual recipe lists needed).
    notes = list(item.get('ability_notes', []))
    is_recipe_changed = (
        notes and re.search(r'\brecipe changed\b',
                            _strip_html(notes[0].get('note', '')), re.I)
    )
    if is_recipe_changed:
        deco = deco + ', changed=True' if deco else ', changed=True'
        notes = notes[1:]
    out.append(f'W(item_header("{name}"{deco}))')
    if is_recipe_changed:
        out.append(f'W(auto_components_change("{name}", "{version}"))')
    body, _ = _emit_notes(notes)
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
            facet_title = s.get("title", facet_slug)
            out.append(f'W(subgroup("Facet: {facet_title}"))')
            for a in s.get('abilities', []):
                aid = a.get('ability_id')
                aname, aslug = ABILS.get(aid, (f'ability_{aid}', f'ability_{aid}'))
                # Skip ability_header when the ability's display name matches
                # the facet title — the subgroup already names the entity, and
                # Valve often serves identical icons for both, producing a
                # redundant visual (e.g. Naga Siren Deluge facet → Deluge
                # active ability).
                if aname.lower() != facet_title.lower():
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


# ---------- POST-PROCESSING ----------

_AGHS_LINE_RE = re.compile(
    r'^W\(li\("Now upgraded with Aghanim\'s (Scepter|Shard)",\s*'
    r't\("(?:NEW|MISC|REWORK)"\),\s*'
    r'extra=inline_note\("(.+?)"\)\)\)$'
)


def _postprocess_aghs_merge(lines):
    """Collapse the v2-emitted aghs upgrade row +its inline-note description
    into a single canonical "Aghanim's X: <description>" li with the NEW
    tag (per memory rule sloppy_aghs_upgrade_merge). The walker has
    already folded the indent N+1 description into the parent's
    inline_note, so the merge is a one-line text rewrite.
    """
    out = []
    for line in lines:
        m = _AGHS_LINE_RE.match(line)
        if m:
            kind, desc = m.group(1), m.group(2)
            out.append(f'W(li("Aghanim\'s {kind}: {desc}", t("NEW")))')
        else:
            out.append(line)
    return out


_PER_LEVEL_FORMULA_RE = re.compile(
    r'(?P<base>\d+(?:\.\d+)?)(?P<pct>%?)\s*\+\s*(?P<inc>\d+(?:\.\d+)?)\2'
    r'\s+per level(?: up)?\b'
)


def _postprocess_scale_pill(lines):
    """Detect "A% + B% per level" / "A + B per level up" formula patterns
    in W(li(...)) text and emit a scale_pill(...) wrapping. The trigger
    is splice-injected into the li text and the table is attached as
    extra= (or merged into the existing inline_note as a sibling).

    Each match gets a unique module-scoped variable in the generated
    source so the trigger and table share the same _formula_id_counter
    increment (calling scale_pill() twice would mint two ids and break
    the trigger→table linkage).
    """
    out = []
    counter = 0
    for line in lines:
        if not line.startswith('W(li("'):
            out.append(line)
            continue
        m = _PER_LEVEL_FORMULA_RE.search(line)
        if not m:
            out.append(line)
            continue
        base_s = m.group('base')
        inc_s = m.group('inc')
        pct = m.group('pct')
        formula_text = m.group(0)
        # Linear formula L → base + inc * L (per memory rule
        # sloppy_per_level_formula). Build a string lambda that survives
        # round-trip into emitted source code.
        counter += 1
        var = f'_pill{counter}'
        out.append(
            f'{var} = scale_pill('
            f'"{formula_text}", '
            f'lambda L: {base_s} + {inc_s}*L, '
            f'levels=[1,5,10,15,20,25,30])'
        )
        # Replace the formula substring inside the li text with the
        # trigger HTML (formed by an f-string concatenation at runtime).
        # The simplest patch: split the original li at the formula match
        # and rebuild with `f"...{var[0]}..."`.
        replaced = (line[:m.start()] + '" + ' + var + '[0] + "' + line[m.end():])
        # If the line already has extra=inline_note(...), we keep that
        # and ALSO append the formula table via a second extra; but li()
        # only accepts a single extra. Cheapest valid output: concatenate
        # the table into a wrapping <span>:
        if 'extra=inline_note(' in replaced:
            # Wrap existing inline_note with table concatenation.
            replaced = re.sub(
                r'extra=inline_note\("(.+?)"\)',
                lambda mm: f'extra=inline_note("{mm.group(1)}") + {var}[1]',
                replaced, count=1,
            )
        else:
            replaced = re.sub(r'\)\)$', f', extra={var}[1]))', replaced, count=1)
        out.append(replaced)
    return out


_REWORK_TRIGGERS = (
    'Innate ability reworked',
    'Ability reworked',
)


# Stat-grant patterns inside item ability_notes — detected per-item and
# collapsed into properties_change(old=[...], new=[...]) after the
# item_header. Each tuple: (regex, kind, builder).
#   kind="add"     → ("NEW", "+stat") in new column only
#   kind="remove"  → ("DEL", "+stat") in old column only
#   kind="change"  → ("BUFF"/"NERF", "+old stat") in old + ("", "+new stat", b(a,b)) in new

# Match "+stat" tokens. Tolerate slash-lists like "+7/9/11/13/15" and
# percent signs. Stat names are 1-4 words, may include "All Attributes".
_STAT_TOKEN = r'\+([0-9./]+%?\s+[A-Z][a-zA-Z\' ]+?)(?=[.,]|\s+(?:increased|decreased|rescaled|changed|to|from|by)\b|$)'

_PROP_ADD_PREFIX_RE = re.compile(
    r'^Now also (?:provides?|grants?|gives?|deals?|fires?)\s+'
)
_PROP_DEL_PREFIX_RE = re.compile(
    r'^No longer (?:provides?|grants?|gives?)\s+'
)
# Match one "+value stat" token. Stat name continues until next comma/and/end.
_STAT_GRANT_RE = re.compile(
    r'\+([\d./]+%?\s+[A-Z][a-zA-Z\'/ ]+?)(?=\s*(?:,|\sand\s|$))'
)


def _parse_stat_grants(text):
    """Split "+X Stat, +Y Stat, and +Z Stat" into ["+X Stat","+Y Stat","+Z Stat"]."""
    return [f'+{m.group(1).strip().rstrip(",.").strip()}'
            for m in _STAT_GRANT_RE.finditer(text)]
# "Bonus Armor decreased from +6 to +7" or "Mana Regen bonus increased from +1.5 to +1"
# We allow the stat name to come BEFORE the verb ("Bonus Armor decreased")
# OR AFTER ("Armor bonus decreased"); both forms appear in patchnotes.
_PROP_CHANGE_RE = re.compile(
    r'^(?P<stat>[A-Z][a-zA-Z\'/ ]+?)\s+'
    r'(?:bonus\s+)?(?P<verb>increased|decreased|rescaled|changed)\s+'
    r'from\s+\+?(?P<old>[\d./]+%?)\s+to\s+\+?(?P<new>[\d./]+%?)\s*$'
)


def _parse_number_or_list(s):
    """Convert "5", "5.5", "5/6/7", "5%" into a value passable to b()."""
    s = s.rstrip('%').strip()
    if '/' in s:
        parts = []
        for p in s.split('/'):
            try:
                parts.append(int(p) if '.' not in p else float(p))
            except ValueError:
                return None
        return parts
    try:
        return int(s) if '.' not in s else float(s)
    except ValueError:
        return None


def _postprocess_properties_change(lines):
    """Collapse stat-grant note patterns inside item blocks into a single
    properties_change(old=[...], new=[...]) call placed right after the
    item_header. The original li rows that fed the diff are removed from
    the regular ul.

    Triggered when an item_header(name, changed=True) is followed by note
    lines matching add/remove/change stat-grant patterns. Items without
    properties-relevant rows pass through untouched.

    Returns the rewritten line list. Does NOT touch hero/general blocks.
    """
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Find item_header( ... changed=True) start
        m_hdr = re.match(r'W\(item_header\("([^"]+)"[^)]*changed=True[^)]*\)\)', line)
        if not m_hdr:
            out.append(line)
            i += 1
            continue

        item_name = m_hdr.group(1)
        out.append(line)
        i += 1
        # Optionally an auto_components_change line follows the header
        if i < len(lines) and lines[i].startswith('W(auto_components_change('):
            out.append(lines[i])
            i += 1

        # Collect li rows of this item block. The block ends at the next
        # W(item_header(...)) / W(hero_header(...)) / section header.
        old_rows = []
        new_rows = []
        kept_lines = []
        block_end = i
        in_ul = False
        while block_end < len(lines):
            ln = lines[block_end]
            if (ln.startswith('W(item_header(') or ln.startswith('W(hero_header(')
                or ln.startswith('W(section(') or ln.startswith('W(plain_header(')
                or ln.startswith('W(unit_header(')):
                break
            block_end += 1

        for j in range(i, block_end):
            ln = lines[j]
            m_li = re.match(r'^W\(li\("(.+?)",\s*[bt]\(.*$', ln)
            if not m_li:
                kept_lines.append(ln)
                continue
            txt = m_li.group(1)
            # Try add pattern — supports comma-separated multi-stat:
            #   "Now also provides +200 Health, +350 Mana, and +60 Cast Range"
            ma = _PROP_ADD_PREFIX_RE.match(txt)
            if ma:
                grants = _parse_stat_grants(txt[ma.end():])
                if grants:
                    for stat in grants:
                        new_rows.append(('NEW', stat))
                    continue
            # Try remove
            mr = _PROP_DEL_PREFIX_RE.match(txt)
            if mr:
                grants = _parse_stat_grants(txt[mr.end():])
                if grants:
                    for stat in grants:
                        old_rows.append(('DEL', stat))
                    continue
            # Try change "X increased/decreased from A to B"
            mc = _PROP_CHANGE_RE.match(txt)
            if mc:
                stat = mc.group('stat').replace(' bonus', '').strip()
                old_v = mc.group('old')
                new_v = mc.group('new')
                verb = mc.group('verb')
                old_n = _parse_number_or_list(old_v)
                new_n = _parse_number_or_list(new_v)
                tag = 'BUFF' if verb == 'increased' else ('NERF' if verb == 'decreased' else 'REWORK')
                if old_n is not None and new_n is not None:
                    old_rows.append((tag, f'+{old_v} {stat}'))
                    new_rows.append((None, f'+{new_v} {stat}', (old_n, new_n)))
                    continue
            kept_lines.append(ln)

        if old_rows or new_rows:
            old_repr = ', '.join(
                f'("{t}", "{s}")' for (t, s) in old_rows
            ) or ''
            def _fmt_new(row):
                if len(row) == 3:
                    tag, stat, (a, b) = row
                    a_s = _py_repr(a)
                    b_s = _py_repr(b)
                    tag_s = f'"{tag}"' if tag else '""'
                    return f'({tag_s}, "{stat}", b({a_s}, {b_s}))'
                tag, stat = row
                return f'("{tag}", "{stat}")'
            new_repr = ', '.join(_fmt_new(r) for r in new_rows) or ''
            out.append(
                f'W(properties_change(old=[{old_repr}], new=[{new_repr}]))'
            )
        out.extend(kept_lines)
        i = block_end
    return out


def _py_repr(v):
    """Format a number or list-of-numbers for inline emission."""
    if isinstance(v, list):
        return '[' + ', '.join(_py_repr(x) for x in v) + ']'
    return repr(v)


_NOW_REQUIRES_RE = re.compile(
    r'^(?:Now (?:also )?requires .+|No longer requires .+|'
    r'Now requires .+ instead of .+)$'
)


def _postprocess_drop_now_requires(lines):
    """When an item block emits auto_components_change(...), the OLD→NEW
    components panel renders the recipe diff visually. The "Now requires
    X" / "No longer requires X" / "Now also requires X" / "Now requires
    X instead of Y" li rows become redundant text restatements. Drop
    them. Cost-only summary rows ("Recipe cost ...", "Total cost ...")
    stay — those are about amounts, not depicted in the panel.

    Per memory rule sloppy_drop_now_requires_after_auto_components.
    """
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        if not line.startswith('W(auto_components_change('):
            i += 1
            continue
        # Walk the item block — drop matching W(li(...)) rows until the
        # next item_header / hero_header / section.
        i += 1
        while i < len(lines):
            ln = lines[i]
            if (ln.startswith('W(item_header(') or ln.startswith('W(hero_header(')
                or ln.startswith('W(section(') or ln.startswith('W(plain_header(')
                or ln.startswith('W(unit_header(')):
                break
            m_li = re.match(r'^W\(li\("(.+?)",\s*[bt]\(', ln)
            if m_li and _NOW_REQUIRES_RE.match(m_li.group(1)):
                i += 1
                continue
            out.append(ln)
            i += 1
    return out


def _postprocess_rework_marker(lines):
    """Add a TODO breadcrumb above W(ability(...)) blocks whose first li
    matches an "Innate ability reworked" / "Ability reworked" trigger.
    Building the full ability_change() swap card from the datafeed alone
    is unsafe (OLD-pane desc lives in the previous patch's tooltip, not
    in this patch's notes), so we mark the spot for manual conversion
    per memory rule sloppy_innate_rework_pattern.
    """
    out = []
    pending_ability_idx = None
    for line in lines:
        if line.startswith('W(ability('):
            pending_ability_idx = len(out)
            out.append(line)
            continue
        if pending_ability_idx is not None and line.startswith('W(li("'):
            if any(trig in line for trig in _REWORK_TRIGGERS):
                # Inject a comment right above the ability header.
                out.insert(
                    pending_ability_idx,
                    '# v2-todo: convert to ability_change(old=..., new=..., '
                    'summary="Innate reworked." / "Ability reworked.", tag="rework") '
                    '— lift OLD desc from prior patchnotes'
                )
            pending_ability_idx = None
        elif pending_ability_idx is not None and (
            line.startswith('W(ability(') or line.startswith('W(hero_header(')
            or line.startswith('# ')
        ):
            pending_ability_idx = None
        out.append(line)
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
            out.extend(_render_item(item, version))

    # Neutral Items
    if d.get('neutral_items'):
        out.append('\n# ===== NEUTRAL ITEM UPDATES =====')
        out.append('W(section("Neutral Item Updates"))')
        for item in d['neutral_items']:
            out.extend(_render_item(item, version, neutral=True))

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

    # Post-process passes that operate on the full emitted line list:
    # 1. Collapse aghs upgrade-row + description into canonical merged li.
    # 2. Auto-emit scale_pill(...) for per-level formula text.
    # 3. Drop a v2-todo breadcrumb above ability blocks tagged "reworked".
    out = _postprocess_aghs_merge(out)
    out = _postprocess_scale_pill(out)
    out = _postprocess_properties_change(out)
    out = _postprocess_drop_now_requires(out)
    out = _postprocess_rework_marker(out)

    return '\n'.join(out)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python generate_patch_code_v2.py <version>', file=sys.stderr)
        sys.exit(1)
    src = generate(sys.argv[1])
    out_path = os.path.join(_HERE, f'_generated_p_{sys.argv[1]}_v2.py')
    open(out_path, 'w', encoding='utf-8').write(src)
    print(f'Wrote {out_path} ({len(src):,} chars, {src.count(chr(10)):,} lines)')
