"""
Datafeed-aware patch-scaffold generator (the canonical generator).

Reads `/datafeed/patchnotes?version=X` JSON (cached under data/) and emits
Python source built on the `patch/` helper API (`b()`, `li()`, `hero_header()`,
…) — the same calls used by `content/pXXX.py`. Preserves the full indent_level
hierarchy, facet subsections, entity titles ("New Tier 1 Artifact"), aghanims
markers, and info clarifications.

Usage:
    python generate_patch_code_v2.py <version>

E.g.: python generate_patch_code_v2.py 7.40

Output: `_generated_p_<version>_v2.py` in the repo root — review it, then save the
reviewed block as `content/p<version>.py` wrapped in `def build():` and register
it in `builders/patch.py`.

Pipeline:
1. Load datafeed JSON (data/<version>_datafeed.json) + itemlist + herolist
2. Walk each top-level section:
   - general_notes[]      → section("General Updates") + plain_header per note
   - items[]              → section("Item Updates")     + item_header per item
   - neutral_creeps[]     → section("Neutral Creep Updates") + per creep
   - neutral_items[]      → section("Neutral Item Updates") + per artifact
   - heroes[]             → section("Hero Updates") + hero_header +
                            abilities + facet subsections
   (Section order matches the official patch page: General → Items →
    Neutral Creeps → Neutral Items → Heroes.)
3. For each entity, walk notes tree:
   - indent_level == 1 → top-level li
   - indent_level == N+1 immediately after N → inline_note on parent
   - hide_dot:true row → subgroup() or <br> spacer
   - info field → inline_note attached to current row
   - aghanims field → ensure text mentions "Aghanim's Scepter"/"Aghanim's Shard"
                      so patch/elements.li() auto-tags the aghs marker
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
sys.path.insert(0, _HERE)
try:
    from patch.images import ITEM_SLUG as _KNOWN_ITEM_SLUGS
except Exception:
    _KNOWN_ITEM_SLUGS = {}


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


def _load_creep_abilities():
    """npc slug → [ability slugs] (from data/creep_abilities.json)."""
    p = os.path.join(_HERE, 'data', 'creep_abilities.json')
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding='utf-8'))


def _load_abilities_slim():
    """ability slug → {'dname': ...} (from data/abilities_slim.json)."""
    p = os.path.join(_HERE, 'data', 'abilities_slim.json')
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding='utf-8'))


CREEP_ABILS = _load_creep_abilities()
ABILS_SLIM = _load_abilities_slim()

# Section order used when emitting the scaffold.
# Neither the datafeed JSON key order nor patchnotes_english.txt reliably
# encodes the official patch-page ordering — Valve's internal order can differ
# from what dota2.com displays. After generation, reorder sections manually
# to match the official page if needed.
_CANONICAL_SECTION_ORDER = [
    'general_notes',
    'neutral_creeps',
    'items',
    'neutral_items',
    'heroes',
]


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
    # MISC — mechanic toggle, classification change, polish, fix, no effective change
    (re.compile(r'\bNow can be toggled while silenced\b', re.I),    'MISC'),
    (re.compile(r'\bClassified as\b', re.I),                        'MISC'),
    (re.compile(r'^\s*Fixed\s+(?:item\s+|ability\s+|spell\s+)?(?:description|tooltip|text)\b', re.I), 'QoL'),  # "Fixed description stating..." — tooltip fix
    (re.compile(r'^\s*Fixed\b', re.I),                              'MISC'),  # "Fixed X" — gameplay bug fix
    (re.compile(r'\bunchanged\b', re.I),                            'MISC'),  # "X is unchanged"
    # DEL — explicit removal / no-longer-targets / no-longer-applies
    (re.compile(r'\bcan no longer (?:target|be cast|be used|trigger|attack|move|stack|proc|crit|bash|leap|fly|deny|sell|disassemble)', re.I), 'DEL'),
    (re.compile(r'\bno longer applied by illusions\b', re.I),       'DEL'),
    (re.compile(r'\bno longer (?:applies?|affects?) ', re.I),       'DEL'),
    (re.compile(r'\bis not applied if\b', re.I),                    'DEL'),   # "X is not applied if Debuff Immune"
    (re.compile(r'\bno longer upgraded with Aghanim', re.I),        'DEL'),
    (re.compile(r"\bno longer.*'s? ability\b", re.I),               'DEL'),
    (re.compile(r'\bno longer (?:provides|grants|deals|fires|spawns|summons|adds|increases|works|considered|active|applied)\b', re.I), 'DEL'),
    (re.compile(r'\bno longer levels with\b', re.I),                'REWORK'),  # memory rule: structural
    (re.compile(r'^No longer has\b', re.I),                         'DEL'),
    (re.compile(r'\bno longer counts? as\b', re.I),                 'DEL'),    # "Hero Creeps no longer count as heroes"
    (re.compile(r'\bRemoved\b', re.I),                              'DEL'),
    # REWORK
    (re.compile(r'\breplaced with\b', re.I),                        'REWORK'),
    (re.compile(r'\breworked\b', re.I),                             'REWORK'),
    (re.compile(r'\brescaled\b', re.I),                             'REWORK'),
    (re.compile(r'\bchanged from\b', re.I),                         'REWORK'),
    (re.compile(r'\bis now cancelled if.*interrupted\b', re.I),     'REWORK'),  # movement/channel cancellation behaviour change
    # General "Now ..." → NEW unless context says otherwise
    (re.compile(r'^Now also\b', re.I),                              'NEW'),
    (re.compile(r'^Now ', re.I),                                    'NEW'),
]

# Cost / regen-style "lower-is-buff" keywords. When the row text matches one
# of these AND `b()` is the badge, set l=True.
LOWER_IS_BUFF = re.compile(
    r'(?<!reduction\s)(?<!resist\s)\b('
    r'cooldown|mana ?cost|mana cost|cast (?:point|time)|cast point|cast time'
    r'|gold cost|item cost|recipe cost|total cost|cost'
    r'|base attack time|\bBAT\b'
    r'|incoming damage|damage taken|status duration|stun resistance'
    r'|magic resistance|attack point|projectile speed.*incoming'
    r'|penalty'  # higher penalty value = worse for player (memory: sloppy_b_l_flag_direction_audit)
    r'|(?:intelligence|agility|strength)\s+required'  # attribute requirements on items
    r'|recharge\s+(?:time|cooldown)'   # charge-based item recharge
    r'|channel\s+time'                 # channeling cast time
    r'|activation\s+time'             # activation delay
    r'|restore\s+time'                # restore/respawn time
    r')\b',
    re.I,
)
# Stats that CONTAIN a lower-is-buff keyword but are actually higher=better
_NOT_LOWER_IS_BUFF = re.compile(
    r'\bcooldown\s+reduction\b'   # CDR: higher = faster cooldowns = better
    r'|\bpenalty\s+reduction\b',  # reducing a penalty = good, but the VALUE is still directional
    re.I,
)


# Exact-substring overrides for cases where heuristics give the wrong tag.
# Key = substring to look for (case-insensitive), Value = forced tag.
# Add here when a generated scaffold consistently gets the wrong tag.
TAG_OVERRIDES = {
    "starts with all":          "MISC",   # "Hallowed now starts with all 3 charges" — REWORK heuristic fires on "now"
    "separate heal reduction":  "MISC",   # "No longer has a separate heal reduction" — consolidation, not removal
    "health restoration":       "MISC",   # health restore consolidation entries
    "now shares cooldown":      "MISC",   # shared cooldown = mechanic change, not pure NERF
    "now has a shared cooldown":"MISC",
}


def _guess_tag(text):
    """Heuristic tag from row text. Returns 'BUFF'/'NERF'/'REWORK'/'NEW'/'DEL'/
    'MISC'/'QoL'/None. None means caller should derive from b()/badge."""
    clean = _strip_html(text)
    # Manual overrides checked first — highest priority
    clean_lower = clean.lower()
    for substr, tag in TAG_OVERRIDES.items():
        if substr.lower() in clean_lower:
            return tag
    for rx, tag in CANONICAL_TAGS:
        if rx.search(clean):
            return tag
    # "increased/decreased by N" without from/to → can't make b(), emit tag
    # has_from_to: "from X to Y" where X/Y are slash-separated levels (parseable)
    has_parseable_from_to = bool(re.search(
        r'\bfrom\s+[-+]?\d[\d./]*\s+to\s+[-+]?\d[\d./]*', clean, re.I
    )) and not re.search(r'\bfrom\s+[-+]?\d+[^0-9\s./]*[–]', clean)
    if re.search(r'\b(increased|raised)\b', clean, re.I):
        return None if has_parseable_from_to else 'BUFF'
    if re.search(r'\b(decreased|reduced|lowered|worsened)\b', clean, re.I):
        return None if has_parseable_from_to else 'NERF'
    if re.search(r'\bimproved\b', clean, re.I):
        return None if has_parseable_from_to else 'BUFF'
    return 'MISC'


def _is_lower_better(text):
    clean = _strip_html(text)
    if _NOT_LOWER_IS_BUFF.search(clean):
        return False
    return bool(LOWER_IS_BUFF.search(clean))


# ---------- B() / TEXT-TAG EMITTERS ----------

_FROM_TO_RE = re.compile(
    r'\bfrom\s+'                                # 'from '
    r'([-+]?\d+(?:\.\d+)?(?:[/–][-+]?\d+(?:\.\d+)?)*[%sx]?)\s+'  # OLD value(s), optional unit suffix
    r'to\s+'                                    # 'to '
    r'([-+]?\d+(?:\.\d+)?(?:[/–][-+]?\d+(?:\.\d+)?)*[%sx]?)',    # NEW value(s)
)
# For "from X–Y to A–B" style (en-dash range): take first number of range as the value
_RANGE_FIRST_RE = re.compile(r'^([-+]?\d+(?:\.\d+)?)–')


def _split_levels(s):
    """'5/7/9/11' or '5' or '52–56' → list or scalar. Strips trailing unit suffix (%/s/x).
    En-dash ranges (52–56) are kept as-is (string); / separates levels."""
    s = s.rstrip('%sx')
    parts = s.split('/')
    nums = []
    for p in parts:
        # En-dash range like "52–56": not a level progression, return None
        # so the caller falls back to a non-numeric tag for "Damage at L1" rows.
        if '–' in p:
            return None
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


_BSTAT_RE = re.compile(
    r'\bBase\s+(?P<stat>Damage|Armor|Strength|Agility|Intelligence|Attack Speed|Health Regen|Mana Regen|Move(?:ment)? Speed)\s+'
    r'(?P<dir>increased|decreased)\s+by\s+(?P<delta>\d+(?:\.\d+)?)\b',
    re.I,
)
_BSTAT_FIELD = {
    'damage':           'AttackDamageMin',
    'armor':            'ArmorPhysical',
    'strength':         'AttributeBaseStrength',
    'agility':          'AttributeBaseAgility',
    'intelligence':     'AttributeBaseIntelligence',
    'attack speed':     'AttackSpeedBase',
    'health regen':     'StatusHealthRegen',
    'mana regen':       'StatusManaRegen',
    'move speed':       'MovementSpeed',
    'movement speed':   'MovementSpeed',
}


def _prev_version_in_stats(version):
    """Return the version key in _STATS_H that immediately precedes `version`.
    Used so bstat_h/note_box get the state BEFORE the current patch changes."""
    from patch.stats import _STATS_H
    keys = sorted(_STATS_H.keys())
    try:
        idx = keys.index(version)
        return keys[idx - 1] if idx > 0 else version
    except ValueError:
        return version


def _emit_li(text, tag_override=None, aghs=None, info=None, hero_name=None, version=None):
    """Render one W(li(...)) call. tag_override overrides heuristic; aghs is
    'scepter'/'shard' (already encoded in text if from datafeed); info is
    optional inline_note text appended. hero_name+version enable bstat_h."""
    txt = text.strip()
    clean = _strip_html(txt)

    # Base-stat "by N" pattern → bstat_h + note_box
    bstat_m = _BSTAT_RE.search(clean) if hero_name and version else None
    if bstat_m:
        stat_key = bstat_m.group('stat').lower()
        field = _BSTAT_FIELD.get(stat_key, 'AttackDamageMin')
        delta = float(bstat_m.group('delta'))
        if bstat_m.group('dir').lower() == 'decreased':
            delta = -delta
        delta_repr = int(delta) if delta == int(delta) else delta
        txt_esc = txt.replace('"', '\\"')
        h = hero_name.replace('"', '\\"')
        prev_v = _prev_version_in_stats(version)
        return (f'W(li("{txt_esc}", bstat_h("{h}", "{field}", "{prev_v}", {delta_repr}),'
                f' extra=note_box(hero="{h}", field="{field}", before_patch="{prev_v}")))')

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
        info_badge = _emit_badge(_strip_html(info))
        if info_badge:
            extras.append(f'extra=inline_note("{info_esc} — " + {info_badge})')
        else:
            extras.append(f'extra=inline_note("{info_esc}")')
    extras_str = (', ' + ', '.join(extras)) if extras else ''
    txt_esc = txt.replace('"', '\\"')
    return f'W(li("{txt_esc}", {badge_str}{extras_str}))'


# ---------- INDENT-TREE WALKER ----------

def _emit_notes(notes, ul_open_called=False, hero_name=None, version=None):
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
        lines.append(_emit_li(txt, info=info, aghs=aghs, hero_name=hero_name, version=version))
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
        # Section-header style entry like "Artifact Changes" / "Enchantment Changes"
        if item.get('title'):
            out.append(f'\nW(plain_header("{_strip_html(item["title"]).strip()}", dynamics=False, sublabel=True))')
        body, _ = _emit_notes(item.get('ability_notes', []))
        out.extend(body)
        return out
    name, slug = ITEMS.get(aid, (f'item_{aid}', f'item_{aid}'))
    is_enchantment = slug.startswith("enhancement_")
    # Warn if the engine slug won't be found by item_img's naive derivation
    # (lowercase + spaces→underscores). If so, ITEM_SLUG needs an entry.
    if not is_enchantment:
        naive = name.lower().replace(" ", "_").replace("'", "")
        if slug and naive != slug and name not in _KNOWN_ITEM_SLUGS:
            print(f"  [WARN] item_img(\"{name}\") uses \"{naive}.png\" but engine slug is \"{slug}.png\" -- add to ITEM_SLUG in patch/images.py")
    deco = _entity_title_decoration(item)
    # Detect "Recipe changed" — first note with "Recipe changed" text →
    # decorate item_header(changed=True), drop that row, and emit an
    # auto_components_change(name, version) call right below the header
    # so the OLD→NEW component diff renders automatically. items.json
    # carries per-patch ItemRequirements + ItemCost, so this lookup is
    # fully data-driven (no manual recipe lists needed).
    notes = list(item.get('ability_notes', []))
    is_recipe_changed = (
        not is_enchantment and
        notes and re.search(r'\brecipe changed\b',
                            _strip_html(notes[0].get('note', '')), re.I)
    )
    if is_recipe_changed:
        deco = deco + ', changed=True' if deco else ', changed=True'
        notes = notes[1:]
    if is_enchantment:
        out.append(f'W(enchant_header("{name}"))')
    else:
        out.append(f'W(item_header("{name}"{deco}))')
    if is_recipe_changed:
        out.append(f'W(auto_components_change("{name}", "{version}"))')
    body, _ = _emit_notes(notes)
    out.extend(body)
    return out


def _render_hero(hero, version=None):
    """One heroes[] entry: hero_header + hero_notes + abilities + subsections."""
    out = []
    hid = hero.get('hero_id')
    name, slug = HEROES.get(hid, (f'hero_{hid}', f'hero_{hid}'))
    out.append(f'\n# {name}')
    out.append(f'W(hero_header("{name}"))')
    # Top-level hero notes (stat changes etc.) — pass hero_name+version for bstat_h.
    # Some notes carry a "FacetName: ..." prefix (Valve places facet-specific changes
    # in hero_notes instead of a dedicated subsection). Split those out so they render
    # under facet_header() instead of a plain li in the hero block.
    hero_notes = hero.get('hero_notes', [])
    if hero_notes:
        # Build display-name → slug reverse map for all known facets
        from patch.badges import FACETS
        _facet_name_to_slug = {n.lower(): s for s, (n, _) in FACETS.items()}
        # Partition notes: bucket by facet name prefix, or keep as general
        _general_notes = []
        _facet_buckets = {}   # facet_slug -> [notes]
        _facet_removed = []   # (slug, display_name) for "Removed X facet" notes
        _FACET_PREFIX_RE = re.compile(r'^([^:]{2,40}):\s+(.+)$', re.DOTALL)
        # "Removed X[, Y] and Z facets" — captures comma/and-separated list
        _REMOVED_FACETS_RE = re.compile(
            r'^Removed\s+(.+?)\s+facets?$', re.IGNORECASE
        )
        for n in hero_notes:
            raw = (n.get('note') or '').strip()
            clean = _strip_html(raw).strip()
            # Check for "Removed X and Y facets" pattern first
            rm = _REMOVED_FACETS_RE.match(clean)
            if rm:
                names_str = rm.group(1)
                # Split on ", " and " and " to get individual facet names
                parts = re.split(r',\s*|\s+and\s+', names_str)
                matched_any = False
                for part in parts:
                    part = part.strip()
                    facet_slug = _facet_name_to_slug.get(part.lower())
                    if facet_slug:
                        _facet_removed.append((facet_slug, part))
                        matched_any = True
                if matched_any:
                    continue  # consumed — don't add to _general_notes
            # Check for "FacetName: change text" prefix
            m = _FACET_PREFIX_RE.match(clean)
            if m:
                prefix = m.group(1).strip()
                facet_slug = _facet_name_to_slug.get(prefix.lower())
                if facet_slug:
                    stripped_note = dict(n)
                    stripped_note['note'] = re.sub(
                        re.escape(prefix) + r':\s*', '', n.get('note', ''), count=1, flags=re.I
                    )
                    _facet_buckets.setdefault(facet_slug, []).append(stripped_note)
                    continue
            _general_notes.append(n)
        if _general_notes:
            body, _ = _emit_notes(_general_notes, hero_name=name, version=version)
            out.extend(body)
        # Emit "Facet removed" blocks (one facet_header per removed facet)
        for facet_slug, _dname in _facet_removed:
            out.append(f'W(facet_header("{facet_slug}"))')
            out.append('W(ul_open())')
            out.append('W(li("Facet removed", t("DEL")))')
            out.append('W(ul_close())')
        # Emit inline facet sections from "FacetName: ..." hero_notes
        for facet_slug, fnotes in _facet_buckets.items():
            out.append(f'W(facet_header("{facet_slug}"))')
            body, _ = _emit_notes(fnotes)
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
    # Facet subsections — new template: facet_header(slug) + ul_open/li/ul_close.
    # No subgroup(), no facet_badge() prefix on individual li rows.
    for s in hero.get('subsections', []):
        if s.get('style') == 'hero_facet':
            facet_slug = s.get('facet')
            out.append(f'W(facet_header("{facet_slug}"))')
            for a in s.get('abilities', []):
                body, _ = _emit_notes(a.get('ability_notes', []))
                out.extend(body)
    return out


def _render_neutral_creep(creep):
    """One neutral_creeps[] entry.

    Datafeed shape:
        {"name": "npc_dota_neutral_satyr_soulstealer",
         "localized_name": "Satyr Mindstealer",
         "neutral_creep_notes": [{"indent_level": 1, "note": "..."}, ...]}

    Renders unit_header followed by per-ability ability() blocks when the
    creep has known abilities in CREEP_ABILS. Notes are matched to abilities
    by checking if the ability's display name appears in the note text
    (case-insensitive). Unmatched notes go into a general bucket emitted
    first as a flat ul.
    """
    out = []
    name = creep.get('name', '') or ''
    display = creep.get('localized_name') or name or 'Unknown Creep'
    notes = creep.get('neutral_creep_notes') or creep.get('notes') or []

    # is_general_note=True means this entry is just a grouping label (no own
    # changes). Its `name` field is a loc key like "#DOTA_Patch_7_39e_...",
    # not a unit slug. Emit plain_header so it renders as a text label only.
    if creep.get('is_general_note'):
        out.append(f'\n# {display} (label — no own changes; sub-units follow)')
        out.append(f'W(plain_header("{display}", dynamics=False))')
        return out

    # Strip the npc_dota_neutral_ prefix to get the icon slug.
    slug = name.replace('npc_dota_neutral_', '', 1) if name else ''
    # Some summoned units (e.g. Skeleton Warrior) use npc_dota_ prefix, not neutral.
    if not slug or slug == name:
        slug = name.replace('npc_dota_', '', 1) if name.startswith('npc_dota_') else name
    icon = f'_NC_CDN + "{slug}.png"' if slug else '""'
    out.append(f'\n# {display}')
    out.append(f'W(unit_header("{display}", {icon}))')

    if not notes:
        return out

    # Build (ability_slug, display_name) pairs for this creep.
    abil_slugs = CREEP_ABILS.get(name, [])
    abil_pairs = []
    for a_slug in abil_slugs:
        dname = (ABILS_SLIM.get(a_slug) or {}).get('dname') or ''
        if dname:
            abil_pairs.append((a_slug, dname))

    if not abil_pairs:
        # No known abilities — emit all notes flat.
        body, _ = _emit_notes(notes)
        out.extend(body)
        return out

    # Match each note to an ability by display-name substring (case-insensitive).
    buckets = {a_slug: [] for a_slug, _ in abil_pairs}
    general = []
    for n in notes:
        txt = _strip_html(n.get('note') or '').lower()
        matched = None
        for a_slug, dname in abil_pairs:
            if dname.lower() in txt:
                matched = a_slug
                break
        if matched:
            buckets[matched].append(n)
        else:
            general.append(n)

    # General (unmatched) notes first.
    if general:
        body, _ = _emit_notes(general)
        out.extend(body)

    # Per-ability blocks — only emit ability() when there are notes for it.
    for a_slug, dname in abil_pairs:
        bucket = buckets[a_slug]
        if not bucket:
            continue
        a_icon = f'"../icons/abilities/{a_slug}.png"'
        dname_esc = dname.replace('"', '\\"')
        out.append(f'W(ability("{dname_esc}", icon_url={a_icon}))')
        body, _ = _emit_notes(bucket)
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
    # "per level", "per level up" AND "per <Hero> level (up)" — Valve often
    # interpolates the hero name ("4% per Enchantress level"), which the old
    # bare "per level" pattern silently missed (7.40 Rabble-Rouser bug).
    r'(?P<base>\d+(?:\.\d+)?)(?P<pct>%?)\s*\+\s*(?P<inc>\d+(?:\.\d+)?)\2'
    r"\s+per(?:\s+[A-Z][\w'-]*)?\s+level(?: up)?\b"
)

# "X changed from <formula> to <formula>" — a DIFF of two per-level formulas
# must become li_formula(...) (old vs new table), not a scale_pill around one
# of them. Plain li lines only (no extra=), single t(...) tag.
_FORMULA_DIFF_LINE_RE = re.compile(
    r'^W\(li\("(?P<prefix>[^"]+?) from (?P<old>[^"]+?) to (?P<new>[^"]+?)",\s*'
    r't\("(?:REWORK|MISC|BUFF|NERF)"\)\)\)$'
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
        # TWO formulas in a "changed from X to Y" line → emit li_formula
        # (old/new diff table), NOT a scale_pill around just one of them.
        diff = _FORMULA_DIFF_LINE_RE.match(line)
        if diff:
            mo = _PER_LEVEL_FORMULA_RE.search(diff.group('old'))
            mn = _PER_LEVEL_FORMULA_RE.search(diff.group('new'))
            if mo and mn:
                fmt = '"{:g}%"' if mo.group('pct') else '"{:g}"'
                out.append(
                    f'W(li_formula("{diff.group("prefix")}", '
                    f'"{diff.group("old")}", "{diff.group("new")}", '
                    f'lambda L: {mo.group("base")} + {mo.group("inc")}*L, '
                    f'lambda L: {mn.group("base")} + {mn.group("inc")}*L, '
                    f'value_fmt={fmt}))'
                )
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
            # No levels= override: the FULL default grid (L1-15, 20, 25, 30)
            # is the site standard for formula tables. Only abilities that
            # scale every X>1 levels get a custom step-X grid (manual).
            f'{var} = scale_pill('
            f'"{formula_text}", '
            f'lambda L: {base_s} + {inc_s}*L)'
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
    'Reworked into',          # "Reworked into a basic ability" (Spectre Shadow Step)
)

# A brand-new / introduced ability — needs an ability_change(..., tag="new")
# card whose OLD pane is the ability it replaces (lifted from prior patchnotes).
_NEW_ABILITY_TRIGGERS = (
    'New innate ability',
    'New basic ability',
    'New ability',
    'New Point Targeted',     # "New Point Targeted basic ability"
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


# Two emission shapes for the same semantic case (net cost zero):
#   A) "Recipe cost X from A to B. Total cost unchanged at C ..." — single string
#   B) "Recipe cost X from A to B"  +  inline_note("Total cost unchanged ...")
# Both should become t("MISC") + inline badge.
_RECIPE_COST_UNCHANGED_INLINE_RE = re.compile(
    r'^W\(li\("(Recipe cost (?:increased|decreased) from )(\d+)( to )(\d+)'
    r'(\. Total cost unchanged[^"]*)",\s*'
    r'b\(\d+,\s*\d+,\s*l=True\)\)\)$'
)
_RECIPE_COST_UNCHANGED_SPLIT_RE = re.compile(
    r'^W\(li\("(Recipe cost (?:increased|decreased) from )(\d+)( to )(\d+)",\s*'
    r'b\(\d+,\s*\d+,\s*l=True\),\s*'
    r'extra=inline_note\("(Total cost unchanged[^"]*)"\)\)\)$'
)


def _postprocess_recipe_cost_zero_net(lines):
    """Rewrite recipe-cost-changed-but-total-unchanged rows from badge-
    as-tag form to t("MISC") + inline badge form. Net cost to the player
    is zero (sub-component shift cancels), so the row shouldn't tally as
    BUFF/NERF in the entity's dyn-cell. Per memory rule
    sloppy_recipe_cost_zero_net_is_misc.
    """
    out = []
    for line in lines:
        m = _RECIPE_COST_UNCHANGED_INLINE_RE.match(line)
        if m:
            prefix, a, mid, b_val, tail = m.groups()
            out.append(
                f'W(li("{prefix}{a}{mid}{b_val} " + b({a}, {b_val}, l=True) + "{tail}", '
                f't("MISC")))'
            )
            continue
        m = _RECIPE_COST_UNCHANGED_SPLIT_RE.match(line)
        if m:
            prefix, a, mid, b_val, note_text = m.groups()
            out.append(
                f'W(li("{prefix}{a}{mid}{b_val} " + b({a}, {b_val}, l=True), '
                f't("MISC"), extra=inline_note("{note_text}")))'
            )
            continue
        out.append(line)
    return out


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
    announces a REWORKED ability ("Innate ability reworked" / "Ability
    reworked" / "Reworked into …") OR a brand-NEW ability ("New innate/
    basic/Point Targeted ability"). Building the full ability_change() swap
    card from the datafeed alone is unsafe — the OLD-pane desc lives in the
    PREVIOUS patch's tooltip (for reworks) or in the REPLACED ability (for
    new ones), neither of which is in this patch's notes. So we mark the
    spot for manual conversion per memory rules sloppy_innate_rework_pattern
    / sloppy_ability_change_pattern.
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
            elif any(trig in line for trig in _NEW_ABILITY_TRIGGERS):
                out.insert(
                    pending_ability_idx,
                    '# v2-todo: convert to ability_change(old=<replaced ability>, new=..., '
                    'summary="New innate ability." / "New ability.", tag="new") '
                    '— OLD pane = the ability this replaces (lift its desc from prior patchnotes)'
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

def fetch_datafeed(version):
    """Download /datafeed/patchnotes?version=X from Valve and cache it under
    data/<version>_datafeed.json. Returns the parsed dict.
    Safe to call multiple times — skips the download if the cache already exists.
    Cache miss triggers a live HTTP request to dota2.com; ensure network access
    or pre-populate data/<version>_datafeed.json manually."""
    import urllib.request
    p = os.path.join(_HERE, 'data', f'{version}_datafeed.json')
    if os.path.exists(p):
        print(f'Using cached datafeed: {p}')
        return json.load(open(p, encoding='utf-8'))
    url = f'https://www.dota2.com/datafeed/patchnotes?version={version}&language=english'
    print(f'Fetching {url} ...')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    d = json.loads(raw)
    # Valve wraps in {"success": true, "result": {...}} — unwrap if needed
    if 'result' in d and 'patch_notes' in d.get('result', {}):
        d = d['result']['patch_notes']
    os.makedirs(os.path.join(_HERE, 'data'), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'Saved -> {p} ({len(raw):,} bytes)')
    return d


# ---------- NORMALIZED JSON LAYER ----------
# Parallel output to the W()-scaffold: walks the same datafeed and emits a
# structured JSON artifact (data/normalized/patches/<version>.json). This is
# the "data as source of truth" layer — pages/validators read it instead of
# re-deriving meaning from the generated Python/HTML. Built only going forward
# (current patch onward); legacy content/p*.py files are NOT back-converted.


def _mean(v):
    """Mean of a level-list, or the scalar itself."""
    if isinstance(v, list):
        return sum(v) / len(v) if v else 0
    return v


def _numeric_direction(old, new, lower_is_better):
    """buff/nerf/misc from old→new means, respecting lower_is_better."""
    if old is None or new is None:
        return None
    o, n = _mean(old), _mean(new)
    if n == o:
        return 'misc'
    better = n > o
    if lower_is_better:
        better = not better
    return 'buff' if better else 'nerf'


def _resolve_tag(text, old, new, lower):
    """Final tag for a note, mirroring the scaffold's precedence:
    1. Canonical phrase tags (rescaled→rework, added→new, removed→del, …).
    2. Numeric change → direction from old/new values (the b() badge drives it).
    3. Text-heuristic fallback (increased→buff / decreased→nerf).

    This deliberately puts numeric direction ABOVE the increased/decreased word
    heuristic: a "Cooldown increased from 70 to 100/85/70" row reads as a buff
    by wording but is a nerf by value (longer cooldown), and the values are the
    ground truth — same call the generated b() makes.
    """
    clean = _strip_html(text or '')
    for rx, tag in CANONICAL_TAGS:
        if rx.search(clean):
            return tag.lower()
    # "improved"/"worsened" are authoritative direction words Valve uses
    # precisely when the raw value direction is counterintuitive (faster spawn
    # rate, shorter penalty duration, smaller "decrease" penalty). Trust the
    # word over the value comparison — otherwise e.g. "spawn rate improved from
    # 0.35s to 0.25s" reads as a nerf by value.
    if re.search(r'\bimproved\b', clean, re.I):
        return 'buff'
    if re.search(r'\bworsened\b', clean, re.I):
        return 'nerf'
    if old is not None and new is not None:
        direction = _numeric_direction(old, new, lower)
        if direction:
            return direction
    guessed = _guess_tag(text or '')
    return (guessed or 'misc').lower()


# "A–B to C–D" min–max ranges (en-dash/em-dash/hyphen). Used for damage rows
# like "Damage increased from 22–24 to 24–26" which _FROM_TO_RE/_split_levels
# intentionally reject (ranges aren't level progressions). Captured as
# old=[min,max], new=[min,max] with range=True so consumers can disambiguate
# from level-lists; direction still derives from the midpoint via _mean.
_RANGE_TO_RE = re.compile(
    r'\bfrom\s+([-+]?\d+(?:\.\d+)?)[–—-]([-+]?\d+(?:\.\d+)?)\s+'
    r'to\s+([-+]?\d+(?:\.\d+)?)[–—-]([-+]?\d+(?:\.\d+)?)'
)


def _num(x):
    f = float(x)
    return int(f) if f == int(f) else f


def _normalize_note_text(text):
    """One note → structured change dict.

    Returns {text, tag, old, new, lower_is_better, range}. `old`/`new` are
    scalars or level-lists when a parseable "from X to Y" is present, min–max
    pairs when a range is present (with range=True), else absent. `tag` is
    lowercase (buff/nerf/rework/new/del/misc/qol).

    Numeric extraction runs on the HTML-stripped text — Valve wraps changed
    numbers in <font color=…> tags ("from <font>10%</font> to …"), which would
    otherwise defeat the from-to regex.
    """
    clean = _strip_html(text or '').strip()
    lower = _is_lower_better(clean)
    old = new = None
    is_range = False
    m = _FROM_TO_RE.search(clean)
    if m:
        po, pn = _split_levels(m.group(1)), _split_levels(m.group(2))
        if po is not None and pn is not None:
            old, new = po, pn
    if old is None:
        rm = _RANGE_TO_RE.search(clean)
        if rm:
            old = [_num(rm.group(1)), _num(rm.group(2))]
            new = [_num(rm.group(3)), _num(rm.group(4))]
            is_range = True

    rec = {'text': clean, 'tag': _resolve_tag(clean, old, new, lower)}
    if old is not None:
        rec['old'] = old
        rec['new'] = new
        if is_range:
            rec['range'] = True
        if lower:
            rec['lower_is_better'] = True
    return rec


def _normalize_notes(notes, scope):
    """List of datafeed notes → list of change dicts with a `scope` label.
    Skips hide_dot separators and empty rows."""
    out = []
    for n in notes or []:
        if n.get('hide_dot'):
            continue
        txt = (n.get('note') or '').strip()
        if not txt:
            continue
        rec = _normalize_note_text(txt)
        rec['scope'] = scope
        info = n.get('info')
        if info:
            rec['info'] = _strip_html(info).strip()
        out.append(rec)
    return out


def _normalize_hero(hero):
    """heroes[] entry → {entity_type, id, name, changes[]}."""
    hid = hero.get('hero_id')
    name, slug = HEROES.get(hid, (f'hero_{hid}', f'hero_{hid}'))
    changes = []
    changes += _normalize_notes(hero.get('hero_notes'), 'base')
    for a in hero.get('abilities', []):
        aid = a.get('ability_id')
        aname, _aslug = ABILS.get(aid, (f'ability_{aid}', f'ability_{aid}'))
        changes += _normalize_notes(a.get('ability_notes'), aname)
    changes += _normalize_notes(hero.get('talent_notes'), 'talent')
    for s in hero.get('subsections', []):
        if s.get('style') == 'hero_facet':
            fslug = s.get('facet')
            for a in s.get('abilities', []):
                changes += _normalize_notes(a.get('ability_notes'), f'facet:{fslug}')
    return {'entity_type': 'hero', 'id': slug, 'name': name, 'changes': changes}


def _normalize_item(item, neutral=False):
    aid = item.get('ability_id')
    if aid == -1:
        # Section-header pseudo-entry (e.g. "Artifact Changes"). Skip entirely
        # if it carries no notes of its own — these are pure layout labels
        # ("Basic Items", "Upgrades"), not data.
        changes = _normalize_notes(item.get('ability_notes'), 'base')
        if not changes:
            return None
        title = _strip_html(item.get('title') or '').strip()
        return {
            'entity_type': 'neutral_item' if neutral else 'item',
            'id': None, 'name': title or 'Section',
            'changes': changes,
        }
    name, slug = ITEMS.get(aid, (f'item_{aid}', f'item_{aid}'))
    return {
        'entity_type': 'neutral_item' if neutral else 'item',
        'id': slug, 'name': name,
        'changes': _normalize_notes(item.get('ability_notes'), 'base'),
    }


def _normalize_neutral_creep(creep):
    name = creep.get('name', '') or ''
    display = creep.get('localized_name') or name or 'Unknown Creep'
    if creep.get('is_general_note'):
        return None
    notes = creep.get('neutral_creep_notes') or creep.get('notes') or []
    # Reuse the same ability-name substring matching as _render_neutral_creep
    # so JSON scopes line up with the generated ability() blocks.
    abil_pairs = []
    for a_slug in CREEP_ABILS.get(name, []):
        dname = (ABILS_SLIM.get(a_slug) or {}).get('dname') or ''
        if dname:
            abil_pairs.append(dname)
    changes = []
    for n in notes:
        if n.get('hide_dot'):
            continue
        txt = (n.get('note') or '').strip()
        if not txt:
            continue
        low = _strip_html(txt).lower()
        scope = 'base'
        for dname in abil_pairs:
            if dname.lower() in low:
                scope = dname
                break
        rec = _normalize_note_text(txt)
        rec['scope'] = scope
        changes.append(rec)
    slug = name.replace('npc_dota_neutral_', '', 1) if name else name
    return {'entity_type': 'neutral_creep', 'id': slug, 'name': display, 'changes': changes}


def _normalize_general(note):
    title = _strip_html(note.get('title') or '').strip()
    return {
        'entity_type': 'general', 'id': None, 'name': title or 'General',
        'changes': _normalize_notes(note.get('generic'), 'base'),
    }


def normalize(version, d=None):
    """Build the normalized JSON dict for a patch (data-as-source-of-truth).
    `d` may be passed to reuse an already-fetched datafeed."""
    if d is None:
        d = fetch_datafeed(version)
    entities = []
    for note in d.get('general_notes', []) or []:
        entities.append(_normalize_general(note))
    for creep in d.get('neutral_creeps', []) or []:
        ent = _normalize_neutral_creep(creep)
        if ent:
            entities.append(ent)
    for item in d.get('items', []) or []:
        ent = _normalize_item(item)
        if ent:
            entities.append(ent)
    for item in d.get('neutral_items', []) or []:
        ent = _normalize_item(item, neutral=True)
        if ent:
            entities.append(ent)
    for hero in sorted(d.get('heroes', []) or [],
                       key=lambda h: HEROES.get(h['hero_id'], ('', ''))[0]):
        entities.append(_normalize_hero(hero))
    return {
        'patch': version,
        'generated_from': f'data/{version}_datafeed.json',
        'entities': entities,
    }


def generate(version):
    d = fetch_datafeed(version)

    out = [f'# Auto-generated v2 scaffold for {version}',
           f'# Source: data/{version}_datafeed.json',
           '']

    # Determine section order: prefer patchnotes_english.txt (matches the
    # official patch page order); fall back to datafeed JSON key order.
    # patchnotes_english.txt groups items + neutral_items under 'items'.
    # We expand 'items' into ('items', 'neutral_items') so both sections are
    # emitted together in sequence.
    # Use the canonical section order. The official Dota 2 patch page ordering
    # cannot be reliably derived from the datafeed or patchnotes_english.txt —
    # after generation, reorder sections manually if needed.
    section_order = _CANONICAL_SECTION_ORDER

    _SECTION_KEYS = {
        'general_notes':  ('GENERAL UPDATES',        'General Updates'),
        'items':          ('ITEM UPDATES',            'Item Updates'),
        'neutral_creeps': ('NEUTRAL CREEP UPDATES',   'Neutral Creep Updates'),
        'neutral_items':  ('NEUTRAL ITEM UPDATES',    'Neutral Item Updates'),
        'heroes':         ('HERO UPDATES',            'Hero Updates'),
    }
    _first = True
    for key in section_order:
        if key not in _SECTION_KEYS or not d.get(key):
            continue
        cap_title, section_title = _SECTION_KEYS[key]
        prefix = '# =====' if _first else '\n# ====='
        out.append(f'{prefix} {cap_title} =====')
        out.append(f'W(section("{section_title}"))')
        _first = False
        if key == 'general_notes':
            for note in d['general_notes']:
                out.extend(_render_general_note(note))
        elif key == 'items':
            for item in d['items']:
                out.extend(_render_item(item, version))
        elif key == 'neutral_creeps':
            for creep in d['neutral_creeps']:
                out.extend(_render_neutral_creep(creep))
        elif key == 'neutral_items':
            for item in d['neutral_items']:
                out.extend(_render_item(item, version, neutral=True))
        elif key == 'heroes':
            for hero in sorted(d['heroes'], key=lambda h: HEROES.get(h['hero_id'], ('', ''))[0]):
                out.extend(_render_hero(hero, version=version))

    # Post-process passes that operate on the full emitted line list:
    # 1. Collapse aghs upgrade-row + description into canonical merged li.
    # 2. Auto-emit scale_pill(...) for per-level formula text.
    # 3. Drop a v2-todo breadcrumb above ability blocks tagged "reworked".
    out = _postprocess_aghs_merge(out)
    out = _postprocess_scale_pill(out)
    out = _postprocess_properties_change(out)
    out = _postprocess_drop_now_requires(out)
    out = _postprocess_recipe_cost_zero_net(out)
    out = _postprocess_rework_marker(out)

    return '\n'.join(out)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python generate_patch_code_v2.py <version>', file=sys.stderr)
        sys.exit(1)
    version = sys.argv[1]
    d = fetch_datafeed(version)

    # 1. W()-scaffold (existing primary output).
    src = generate(version)
    out_path = os.path.join(_HERE, f'_generated_p_{version}_v2.py')
    open(out_path, 'w', encoding='utf-8').write(src)
    print(f'Wrote {out_path} ({len(src):,} chars, {src.count(chr(10)):,} lines)')

    # 2. Normalized JSON (parallel data-as-source-of-truth artifact).
    norm = normalize(version, d)
    json_dir = os.path.join(_HERE, 'data', 'normalized', 'patches')
    os.makedirs(json_dir, exist_ok=True)
    json_path = os.path.join(json_dir, f'{version}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(norm, f, ensure_ascii=False, indent=2)
    n_changes = sum(len(e['changes']) for e in norm['entities'])
    print(f'Wrote {json_path} ({len(norm["entities"])} entities, {n_changes} changes)')

    # 3. Auto-validate the JSON we just wrote (no separate command needed).
    try:
        from tools.validate_data import validate_patch, _report
        print('\n--- validating normalized data ---')
        _report(version, validate_patch(version))
    except Exception as e:
        print(f'(validation skipped: {e})')
