"""The datafeed, and the normalized JSON written next to the scaffold (data/normalized/patches)."""
import json
import os
import re

from .common import _HERE
from .data import ABILS, ABILS_SLIM, CREEP_ABILS, HEROES, ITEMS, _strip_html
from .rows import _add_missing_from, _by_size, _mean, _said_lower_better, _split_levels
from .tags import CANONICAL_TAGS, _FROM_TO_RE, _guess_tag, _is_lower_better

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
    if not isinstance(d, dict):     # Valve sometimes answers "null": say so instead of a TypeError further down
        raise RuntimeError(f'{url} returned {raw[:40]!r} instead of patch notes; try again later')
    # Valve wraps in {"success": true, "result": {...}} — unwrap if needed
    if 'result' in d and 'patch_notes' in d.get('result', {}):
        d = d['result']['patch_notes']
    os.makedirs(os.path.join(_HERE, 'data'), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'Saved -> {p} ({len(raw):,} bytes)')
    return d


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
    m = _FROM_TO_RE.search(_add_missing_from(clean))
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

    said = _said_lower_better(clean, old, new)
    if said is not None:
        lower = said
    rec = {'text': clean, 'tag': _resolve_tag(clean, *_by_size(old, new), lower)}
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
        if s.get('style', '').startswith('hero_facet'):
            fslug = s.get('facet')
            # A facet subsection can carry its own general_notes (facet-level
            # tweaks like "Spell Amp now affects only total spell damage")
            # AND/OR per-ability changes nested under that facet. Skipping
            # general_notes was the cause of the empty-entity false-positive
            # for Mirana/Razor (7.39) and Lina/Silencer/Tinker (7.39b).
            changes += _normalize_notes(s.get('general_notes'), f'facet:{fslug}')
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
