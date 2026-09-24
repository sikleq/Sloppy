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
except Exception as _e:
    print(f'[WARN] patch.images.ITEM_SLUG unavailable: {_e}', file=sys.stderr)
    _KNOWN_ITEM_SLUGS = {}


# ---------- PATCHNOTES LOC LOADER ----------

def _load_patchnotes_loc(version):
    """Parse data/patchnotes_english.txt and return a per-hero lookup.

    Returns dict: hero_slug → {normalized_text → ability_slug}
    where ability_slug is the slug extracted from the key, or None for
    hero-level (stat) notes.

    Key format: DOTA_Patch_{ver}_{hero}[_{ability_slug}[_{N}[_info]]]
    Example: DOTA_Patch_7_39_kez_kez_kazurai_katana_4
    """
    p = os.path.join(_HERE, 'data', 'patchnotes_english.txt')
    if not os.path.exists(p):
        return {}
    ver_key = version.replace('.', '_')
    prefix = f'DOTA_Patch_{ver_key}_'
    result = {}  # hero_slug -> {text_norm -> ability_slug or None}
    # Regex to parse KV lines: "KEY"\t\t"VALUE"
    _KV = re.compile(r'^"([^"]+)"\s+"([^"]*)"')
    with open(p, encoding='utf-8') as f:
        for line in f:
            m = _KV.match(line.strip())
            if not m:
                continue
            key, text = m.group(1), m.group(2).strip()
            if not key.startswith(prefix):
                continue
            rest = key[len(prefix):]  # e.g. "kez_kez_kazurai_katana_4" or "kez_3"
            # Split to identify hero slug (first token) vs ability slug
            parts = rest.split('_')
            if not parts:
                continue
            hero_slug = parts[0]
            # The ability slug follows the hero slug. Hero slugs can be
            # multi-word (e.g. "ancient_apparition"), so we match greedily:
            # look for the longest prefix of parts that is a known hero slug,
            # then the next segment(s) before a trailing _N or _info form the
            # ability slug.  We approximate: if parts[1] == hero_slug_part[0]
            # (i.e. the ability slug also starts with the hero slug), then the
            # ability slug starts at parts[0] and extends until we hit a
            # pure-numeric suffix or "_info".
            # Simpler heuristic: strip trailing _N and _info suffixes, then
            # if what remains has more tokens than the hero part, the extras
            # are the ability slug.
            tail = parts[1:]  # everything after hero_slug
            # Strip trailing _info
            if tail and tail[-1] == 'info':
                tail = tail[:-1]
            # Strip trailing pure-numeric token
            if tail and tail[-1].isdigit():
                tail = tail[:-1]
            # Remaining tail: if non-empty AND starts with hero_slug (ability
            # slugs typically start with hero slug, e.g. kez_kazurai_katana),
            # reconstruct ability slug as hero_slug + _ + '_'.join(tail).
            if tail and tail[0] == hero_slug:
                ability_slug = '_'.join([hero_slug] + tail[1:]) if len(tail) > 1 else None
            elif tail:
                # ability slug doesn't share hero prefix (rare) — use as-is
                ability_slug = '_'.join([hero_slug] + tail)
            else:
                ability_slug = None  # hero-level note
            text_norm = re.sub(r'\s+', ' ', text).lower().strip()
            if text_norm:
                result.setdefault(hero_slug, {})[text_norm] = ability_slug
    return result


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
    (re.compile(r'\bno longer has (?:an? |the )?(?:\w+ ){0,3}(?:penalt(?:y|ies)|restrictions?|drawbacks?|downsides?|debuff slow)\b', re.I), 'BUFF'),
    # ── 2026-09-22 generator-vs-proofread diff (7.38): confident direction flips ──
    (re.compile(r"\bno longer (?:reduces|decreases) (?:enemy |enemies'? |their |the target'?s? )?vision\b", re.I), 'DEL'),  # enemy vision debuff removed (NS Void)
    (re.compile(r'\bno longer freezes enem', re.I), 'DEL'),                              # freezing ENEMY cooldowns = a benefit removed
    (re.compile(r"\b(?:isn't|is not|no longer|won't be|will not be) (?:be )?removed\b", re.I), 'BUFF'),  # own effect now persists
    (re.compile(r'\bloss\b[^.]*?\b(?:reduced|decreased|lowered)\b(?![^.]*\bfrom\s+[-+]?\d)', re.I), 'BUFF'),  # "Gold loss on death is reduced"
    (re.compile(r'\bloss\b[^.]*?\bincreased\b(?![^.]*\bfrom\s+[-+]?\d)', re.I), 'NERF'),
    (re.compile(r'\b(?:makes|causes) enem(?:y|ies)\b[^.]*\b(?:decreased|reduced|lowered)\b', re.I), 'BUFF'),  # a debuff put on enemies
    (re.compile(r'\baffected (?:units|enemies|targets) no longer (?:take|receive|suffer|have)\b', re.I), 'NERF'),  # enemy debuff lifted
    (re.compile(r"^Added (?:an? |the )?(?:[\w']+ ){0,4}(?:icon|indicator|marker)\b", re.I), 'QoL'),  # user rule: new icon = QoL
    (re.compile(r'^\s*Now is (?:an? )?innate ability\.?\s*$', re.I), 'REWORK'),   # bare conversion only; "…that improves with X" is judged per case
    (re.compile(r'\bnow levels with\b', re.I), 'REWORK'),
    # removing an Aghs upgrade / benefit ("no longer decreases cooldown / stun delay") = DEL, not BUFF
    (re.compile(r'\bno longer (?:decreases|reduces)\b(?:(?!wind[- ]?up).)*?\b(?:cooldown|stun delay)\b', re.I), 'DEL'),
    (re.compile(r'\bno longer (?:reduces|decreases) ', re.I),       'BUFF'),
    (re.compile(r'\bno longer requires (?:a |an )?(?:skill point|mana|charge)', re.I), 'BUFF'),
    # ── classes from the 2026-09-18 datafeed proofread (memory: sloppy-datafeed-proofread-method) ──
    # a restriction / self-penalty on the OWNER is lifted → BUFF
    (re.compile(r'\bno longer (?:be )?(?:disabled|interrupted|cancell?ed|blocked|prevented|stopped) by\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer (?:interrupts?|cancels?) (?:movement|channel)', re.I), 'BUFF'),
    (re.compile(r'\b(?:can now|now can) be (?:cast|used|toggled|activated) (?:without|while)\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer has (?:a |an )?(?:reduced|decreased|lower|fixed|illusion vision)\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer (?:freezes|loses|pauses|resets|delays)\b', re.I), 'BUFF'),
    (re.compile(r'\bis no longer (?:decreased|reduced|lowered) on \w+ from (?:his|her|their|its) own\b', re.I), 'BUFF'),
    (re.compile(r'\brequirement\b.*\b(?:is |was )?removed\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer dispellable\b', re.I),                'BUFF'),   # own (de)buff can't be removed any more
    # a restriction / limit / delay is ADDED → NERF
    (re.compile(r'\bis now dispellable\b', re.I),                   'NERF'),   # own buff can now be removed
    (re.compile(r'\bis now disjointable\b', re.I),                  'NERF'),   # own projectile can now be dodged
    (re.compile(r'\bnow (?:only|solely) (?:affects?|available|applies|works|triggers?|targets?|hits?)\b', re.I), 'NERF'),
    (re.compile(r'\bnow (?:affects?|applies|works) only\b', re.I),  'NERF'),
    (re.compile(r'\bnow has (?:a |an )?\d[\d./]*\s?(?:s|seconds?)? ?(?:cast point|cast time|internal cooldown|break distance|cooldown|mana cost|delay|health cost)\b', re.I), 'NERF'),
    (re.compile(r'\bnow (?:ends|expires|dies?|breaks?|is (?:cancell?ed|interrupted|removed)) (?:if|when|once|after)\b', re.I), 'NERF'),
    (re.compile(r'\b(?:may|can) only (?:trigger|proc|be cast|be used|target|affect|stack)\b', re.I), 'NERF'),
    (re.compile(r'\bnow disabled by\b', re.I),                      'NERF'),
    (re.compile(r'\bdoes not affect .* in (?:the )?fountain\b', re.I), 'NERF'),
    # a capability is taken away → DEL
    (re.compile(r'\bno longer (?:stealable|copyable|benefits? from|blinks?|copy|copies|has an alt-cast)\b', re.I), 'DEL'),
    # structural change of the entity → REWORK
    (re.compile(r'^(?:Now|Is now) (?:a|an) (?:universal|strength|agility|intelligence)\b', re.I), 'REWORK'),
    (re.compile(r'\bgained (?:a |an )?(?:\d+% )?creep penalty\b', re.I), 'NERF'),   # lifesteal now hits a creep penalty
    (re.compile(r"^Now \w+'s? (?:ultimate|basic|innate) ability\b", re.I), 'REWORK'),
    (re.compile(r'\b(?:ability )?is now (?:an? )?innate\b', re.I),  'REWORK'),
    # NERF — adding a penalty/restriction is negative (inverse of no-longer-has-penalty)
    (re.compile(r'\bnow has (?:an? |the )?(?:\w+ ){0,3}(?:penalty|restriction|drawback|downside)\b', re.I), 'NERF'),
    # NEW — new mechanic / capability added
    (re.compile(r'\bAdded to Captains Mode\b', re.I),               'NEW'),
    (re.compile(r'\bCan now be disassembled\b', re.I),              'NEW'),
    (re.compile(r'\bno longer disjointable\b', re.I),               'DEL'),
    (re.compile(r'^Now (?:also )?(?:passively |actively )?(?:grants|provides|gains?|adds?|applies?|deals?|increases|fires?|spawns?|summons?)', re.I), 'NEW'),
    (re.compile(r"\bAghanim's (?:Scepter|Shard) now (?:also )?(?:grants|provides|applies?|adds?|deals?|allows?|gives?|causes?)", re.I), 'NEW'),
    (re.compile(r'^Added\b', re.I),                                 'NEW'),
    # QoL — UI / display / convenience, no gameplay change
    (re.compile(r'\bpressing (?:and holding )?alt\b', re.I),        'QoL'),
    (re.compile(r'\bholding (?:and pressing )?alt\b', re.I),        'QoL'),
    (re.compile(r'\balt[\s-]clicking?\b', re.I),                    'QoL'),
    # MISC — mechanic toggle, classification change, polish, fix, no effective change
    (re.compile(r'\bClassified as\b', re.I),                        'MISC'),
    (re.compile(r'\btooltip now (?:shows?|displays?|reflects?)\b', re.I), 'QoL'),  # "The tooltip now shows..." — display-only improvement
    (re.compile(r'^\s*Fixed\s+(?:item\s+|ability\s+|spell\s+)?(?:description|tooltip|text)\b', re.I), 'QoL'),  # "Fixed description stating..." — tooltip fix
    (re.compile(r'^\s*Fixed\b', re.I),                              'MISC'),  # "Fixed X" — gameplay bug fix
    (re.compile(r'\bunchanged\b', re.I),                            'MISC'),  # "X is unchanged"
    # DEL — explicit removal / no-longer-targets / no-longer-applies
    (re.compile(r'\bcan no longer (?:target|be cast|be used|trigger|attack|move|stack|proc|crit|bash|leap|fly|deny|sell|disassemble)', re.I), 'DEL'),
    (re.compile(r'\bno longer (?:be )?applied by illusions\b', re.I), 'DEL'),
    (re.compile(r'\bno longer (?:applies?|affects?) ', re.I),       'DEL'),
    (re.compile(r'\bis not applied if\b', re.I),                    'DEL'),   # "X is not applied if Debuff Immune"
    (re.compile(r'\bno longer upgraded with Aghanim', re.I),        'DEL'),
    (re.compile(r"\bno longer.*'s? ability\b", re.I),               'DEL'),
    (re.compile(r'\bno longer (?:provides|grants|deals|fires|spawns|summons|adds|increases|works|considered|active|applied|kills|slows|buffs|restores|heals|casts|silences|freezes|suspends|manipulates|instantly)\b', re.I), 'DEL'),
    (re.compile(r'\bno longer levels with\b', re.I),                'REWORK'),  # memory rule: structural
    (re.compile(r'\bno longer has\b(?! (?:an? |the )?(?:\w+ )?(?:penalty|restriction|drawback|downside|debuff slow|separate))', re.I), 'DEL'),  # "X no longer has True Strike/feature" → DEL; excludes BUFF-pattern exceptions
    (re.compile(r'\bno longer counts? as\b', re.I),                 'DEL'),    # "Hero Creeps no longer count as heroes"
    (re.compile(r'\bRemoved\b', re.I),                              'DEL'),
    # REWORK
    (re.compile(r'\breplaced with\b', re.I),                        'REWORK'),
    (re.compile(r'\breworked\b', re.I),                             'REWORK'),
    (re.compile(r'\brescaled\b', re.I),                             'REWORK'),
    (re.compile(r'\bchanged from\b', re.I),                         'REWORK'),
    (re.compile(r'\bis now cancell?ed if.*interrupted\b', re.I),    'NERF'),    # movement now breaks on interrupt — a new restriction
    (re.compile(r'\bare now treated as\b', re.I),                   'REWORK'),  # reclassification: "X are now treated as Y"
    (re.compile(r'\bno longer considers?\b', re.I),                 'REWORK'),  # scoping: "no longer considers X for Y"
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
    r'|incoming damage|damage taken|damage vulnerability|building damage penalty'
    r'|status duration|stun resistance'
    r'|attack point|projectile speed.*incoming'
    r'|penalty'
    r'|(?:intelligence|agility|strength)\s+required'
    r'|recharge\s+(?:time|cooldown)'
    r'|channel\s+time'
    r'|activation\s+time'
    r'|restore\s+time'
    r'|respawn\s+time'
    # 2026-09-18 proofread: self-penalties, owner-side timers and thresholds
    r'|disable\s+(?:range|radius|duration)'
    r'|(?:damage|attack|tick|pulse|explosion|spawn)\s+interval'
    r'|flight\s+time'
    r'|stun\s+duration\s+from\s+falling'
    r'|slow\s+resistance\s+loss|status\s+resistance\s+loss'   # self-penalty (Spirit Breaker Relentless); NOT enemy armor/AS/MR reduction
    r'|creep\s+penalty|max\s+mana\s+penalty|vision\s+penalty'
    r'|mana\s+per\s+second'
    r'|health\s+cost'
    r'|(?:damage|hit)\s+threshold'
    # 2026-09-22: owner-side timers and trigger requirements
    r'|restock\s+time'
    r'|base\s+attack\s+rate'                     # seconds per attack (Kez Sai/Katana) — like BAT
    r'|required\s+to\s+(?:trigger|cast|activate|proc)'
    r'|(?:familiar|summon(?:ed)?|illusion|ward|spirit)s?\s+(?:gold\s+)?bounty'   # own summon's bounty
    r')\b',
    re.I,
)
_NOT_LOWER_IS_BUFF = re.compile(
    r'\bcooldown\s+reduction\b'
    r'|\bcooldown\s+advance\b'
    r'|\bcooldown\s+(?:speed|recovery)\b'
    r'|\bmana\s+cost\s+reduction\b'
    r'|\bpenalty\s+reduction\b'
    # "Magic Resistance bonus" is higher-is-better (item stat), not incoming damage
    r'|\bmagic\s+resistance\s+bonus\b'
    # enemy-side values scaling "per cooldown" / max slow (Faceless Void, Open Wounds): higher is better
    r'|\bper\s+cooldown\b'
    r'|\bmax\s+slow\b'
    r'|\bsearch\s+radius\b'
    r'|\bmax\s+health\s+minimum\b'
    # "damage threshold reduction" is the opposite of a raw "damage threshold": more reduction = better
    r'|\bthreshold\s+reduction\b'
    # own bonuses that merely mention a lower-is-better word (2026-09-22)
    r'|\b(?:BAT|base\s+attack\s+time)\s+reduction\b'
    r'|\b(?:while|when|during)\s+(?:on\s+)?cooldown\b'
    r'|\bdamage\s+taken\s+as\s+(?:damage\s+)?bonus\b'
    # a NEGATIVE cooldown amount ("-5s Unstable Concoction Cooldown") is a reduction talent
    r'|-\d[\d./]*s?\s+(?:[\w\']+\s+){0,4}cooldown\b',
    re.I,
)


# Exact-substring overrides for cases where heuristics give the wrong tag.
# Key = substring to look for (case-insensitive), Value = forced tag.
# Add here when a generated scaffold consistently gets the wrong tag.
TAG_OVERRIDES = {
    "starts with all":              "MISC",
    "separate heal reduction":      "MISC",
    "health restoration consolidat": "MISC",  # "consolidated Health Restoration" = structural
    "now shares cooldown":          "MISC",
    "now has a shared cooldown":    "MISC",
    "now requires aghanim's":       "NERF",    # a capability now gated behind Aghs (checked before "now requires")
    "now requires":                 "REWORK",  # "Now requires X instead of Y"
    "instead of":                   "REWORK",  # component/requirement swap
    "respawn time increased":       "NERF",    # "increased" heuristic gives BUFF, but higher respawn = worse
    "respawn time decreased":       "BUFF",
    "no longer reduces cooldown":   "DEL",     # removal of a CD-reduction effect; lower-is-buff logic wrongly gives BUFF
    "no longer reduces the cooldown": "DEL",   # same, "the cooldown" phrasing
    "cycled out":                   "DEL",     # item removed from the pool
    "moved from tier":              "REWORK",  # tier-change is a structural move, not a buff/nerf
    "dormant curio increases":      "NEW",     # first-ever curio upgrade on an item = new capability
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
    # Unparseable values ("from 3 minutes to 4 minutes") can't become b(), so the
    # direction must come from here — honour lower-is-better (intervals, costs…).
    lower = _is_lower_better(clean)
    if re.search(r'\b(increased|raised)\b', clean, re.I):
        return None if has_parseable_from_to else ('NERF' if lower else 'BUFF')
    if re.search(r'\b(decreased|reduced|lowered|worsened)\b', clean, re.I):
        return None if has_parseable_from_to else ('BUFF' if lower else 'NERF')
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


def _l1_only_dip(old, new, l=False):
    """Return True if only L1 dropped (or rose for l=True), L2 is equal,
    and all later levels moved in the buff direction — the 'L1-only-dip' pattern
    (memory rule: sloppy_backloaded_rescale_nerf borderline refinement).
    b() avg-signed-pct would call this NERF, but it should be force_overall='buff'."""
    if not isinstance(old, list) or not isinstance(new, list) or len(old) != len(new) or len(old) < 3:
        return False
    # L1: worse for the player
    l1_worse = (new[0] > old[0]) if l else (new[0] < old[0])
    if not l1_worse:
        return False
    # L2: unchanged
    if old[1] != new[1]:
        return False
    # L3+: better for the player
    if not all((new[i] < old[i]) if l else (new[i] > old[i]) for i in range(2, len(old))):
        return False
    # Confirm avg signed pct is negative (would show NERF without override)
    signed = []
    for o, n in zip(old, new):
        if o == n or o == 0:
            signed.append(0.0)
        else:
            pct = (n - o) / o * 100
            is_buff = (n < o) if l else (n > o)
            signed.append(abs(pct) if is_buff else -abs(pct))
    return (sum(signed) / len(signed)) < 0


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
    l = _is_lower_better(text)
    l_arg = ', l=True' if l else ''
    force_arg = ', force_overall="buff"' if _l1_only_dip(old, new, l) else ''
    return f'b({old!r}, {new!r}{l_arg}{force_arg})'


# "Damage at level N increased/decreased from X–Y to A–B" (any level, not just 1)
# also matches "decreased by N (from X–Y to A–B)" and "decreased by 51-49 (from …)"
_DMG_L1_RE = re.compile(
    r'\bDamage at level \d+\s+(?:increased|decreased)(?:\s+by\s+[\d.\-–]+\s*\()?'
    r'\s*from\s+(\d+)[–\-](\d+)\s+to\s+(\d+)[–\-](\d+)',
    re.I,
)

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


_ATTR_NOW_RE = re.compile(r'^(?:Is now|Now) an? (Strength|Agility|Intelligence|Universal) Hero\.?$', re.I)
_ATTR_KV = {"DOTA_ATTRIBUTE_STRENGTH": "Strength", "DOTA_ATTRIBUTE_AGILITY": "Agility",
            "DOTA_ATTRIBUTE_INTELLECT": "Intelligence", "DOTA_ATTRIBUTE_ALL": "Universal"}


def _hero_attr(hero_name, stats_version):
    """Main attribute ("Agility"…) of a hero (display name) in data/stats/<version>/heroes.json, or None."""
    try:
        heroes = json.load(open(os.path.join(_HERE, 'data', 'stats', stats_version, 'heroes.json'), encoding='utf-8'))
        roster = json.load(open(os.path.join(_HERE, 'data', 'herolist.json'), encoding='utf-8'))
    except (OSError, ValueError):
        return None
    npc = next((h['name'] for h in roster['result']['data']['heroes'] if h['name_english_loc'] == hero_name), None)
    return _ATTR_KV.get((heroes.get(npc) or {}).get('AttributePrimary')) if npc else None


def _emit_li(text, tag_override=None, aghs=None, info=None, hero_name=None, version=None):
    """Render one W(li(...)) call. tag_override overrides heuristic; aghs is
    'scepter'/'shard' (already encoded in text if from datafeed); info is
    optional inline_note text appended. hero_name+version enable bstat_h."""
    txt = text.strip()
    clean = _strip_html(txt)

    # "Damage at level 1 changed from X–Y to A–B" → br(X, Y, A, B)
    dmg_m = _DMG_L1_RE.search(clean)
    if dmg_m:
        old_min, old_max, new_min, new_max = (int(x) for x in dmg_m.groups())
        txt_esc = txt.replace('"', '\\"')
        return f'W(li("{txt_esc}", br({old_min}, {old_max}, {new_min}, {new_max})))'

    # "Is now an Agility Hero" → attr_change(old, new): both attributes with icons, old from
    # the stats snapshot before this patch
    attr_m = _ATTR_NOW_RE.match(clean) if hero_name and version else None
    if attr_m:
        old_attr = _hero_attr(hero_name, _prev_version_in_stats(version))
        if old_attr and old_attr != attr_m.group(1):
            rest = f', extra=inline_note("{info}")' if info else ''
            return f'W(li(attr_change("{old_attr}", "{attr_m.group(1)}"), t("REWORK"){rest}))'

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

    # Aghs reworked: merge description into main text instead of inline_note
    # (memory rule: sloppy_aghs_reworked_no_hidden_info)
    _aghs_rework_re = re.compile(
        r"^(?:Reworked\s+)?Aghanim'?s\s+(?:Shard|Scepter)\s+(?:upgrade\s+)?reworked?$", re.I)
    if info and _aghs_rework_re.match(clean):
        aghs_type = 'Shard' if 'shard' in clean.lower() else 'Scepter'
        merged = f"Aghanim's {aghs_type} reworked: {info}"
        merged_esc = merged.replace('"', '\\"')
        return f'W(li("{merged_esc}", t("REWORK")))'

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


# ---------- SOURCE TAG-ORDER SORT ----------

def _source_li_rank(line):
    """Rank a W(li(...)) source line for tag-order sorting (lower = first).
    Mirrors the HTML-level _li_rank() in patch/page.py:
      1 NEW  2 REWORK  3 BUFF/numeric  4 NERF  5 DEL  6 QoL  7 MISC  8 untagged
    Numeric b()/br()/bf() calls default to rank 3 (buff position) because
    buff/nerf can't be determined reliably without evaluating the arguments;
    the HTML post-pass in page.py will refine these at render time."""
    if 't("NEW")' in line:    return 1
    if 't("REWORK")' in line: return 2
    if 't("BUFF")' in line:   return 3
    if 't("NERF")' in line:   return 4
    if 't("DEL")' in line:    return 5
    if 't("QoL")' in line:    return 6
    if 't("MISC")' in line:   return 7
    if re.search(r'\bb\s*\(|\bbr\s*\(|\bbf\s*\(|\bli_formula\s*\(|\bbstat_[hi]\s*\(', line):
        return 3
    return 8


def _sort_source_ul_blocks(lines):
    """Sort W(li(...)) lines within each ul_open/ul_close block by tag rank.
    Stable sort: lines of equal rank keep their authored order.
    Patchnotes-warning comments (# [patchnotes: ...]) stay attached to their li."""
    result = []
    i = 0
    while i < len(lines):
        if lines[i] != 'W(ul_open())':
            result.append(lines[i])
            i += 1
            continue
        result.append(lines[i])
        i += 1
        # Collect block until matching ul_close
        items = []   # list of (rank, original_idx, [lines])
        while i < len(lines) and lines[i] != 'W(ul_close())':
            item_lines = []
            # Gather any preceding patchnotes-warning comments
            while i < len(lines) and lines[i].startswith('#') and lines[i] != 'W(ul_close())':
                item_lines.append(lines[i])
                i += 1
            if i < len(lines) and lines[i] != 'W(ul_close())':
                item_lines.append(lines[i])
                rank = _source_li_rank(lines[i]) if lines[i].startswith('W(li(') else 0
                items.append((rank, len(items), item_lines))
                i += 1
            elif item_lines:
                items.append((0, len(items), item_lines))
        items_sorted = sorted(items, key=lambda x: (x[0], x[1]))
        for _, _, item_lines in items_sorted:
            result.extend(item_lines)
        if i < len(lines):  # W(ul_close())
            result.append(lines[i])
            i += 1
    return result


# ---------- INDENT-TREE WALKER ----------

# Parents whose nested notes are NOT info: they are the body of a card that the
# proofread builds (ability_change / Aghanim upgrade rows merge their kids).
_KIDS_ARE_BODY = re.compile(
    r"^(?:Ability Reworked|New (?:Ultimate |innate |basic )?ability"
    r"|Now upgraded with Aghanim|Aghanim's (?:Shard|Scepter)(?: slightly)? reworked)",
    re.I,
)


def _descendants(notes, i):
    """Indices of every note nested under notes[i] (deeper indent, contiguous)."""
    lvl = notes[i].get('indent_level', 1)
    out = []
    for j in range(i + 1, len(notes)):
        if notes[j].get('indent_level', 1) <= lvl:
            break
        out.append(j)
    return out


def _nested_info_text(notes, lvl, desc):
    """Nested notes → one popup text: each direct child on its own line; a
    single deeper note is appended to its line after " — ", several deeper
    notes follow on their own indented "– " lines."""
    groups = []                                  # [direct child text, [deeper texts]]
    for j in desc:
        t = (notes[j].get('note') or '').strip()
        if notes[j].get('indent_level', 1) == lvl + 1 or not groups:
            groups.append([t, []])
        else:
            groups[-1][1].append(t)
    lines = []
    for head, deeper in groups:
        if len(deeper) == 1:
            lines.append(f'{head} — {deeper[0]}')
        else:
            lines.append(head)
            lines.extend(f'&nbsp;&nbsp;– {d}' for d in deeper)
    return '<br>'.join(lines)


def _fold_into_row(lines, idx, text):
    """Append `text` to the "?" popup of the W(li(…)) at lines[idx]: extend an
    existing inline_note with <br>, otherwise add one. A row that already has
    another extra= (e.g. note_box on a "Base X increased" row) is concatenated,
    never given a second `extra=` kwarg (SyntaxError)."""
    esc = text.replace('"', '\\"')
    old_line = lines[idx]
    if 'extra=inline_note' in old_line:
        lines[idx] = re.sub(
            r'(extra=inline_note\(")(.*?)("\)+)$',
            lambda m: f'{m.group(1)}{m.group(2)}<br>{esc}{m.group(3)}',
            old_line, count=1,
        )
        return
    k = old_line.rfind('))')
    if k >= 0:
        joiner = (f' + inline_note("{esc}")))' if 'extra=' in old_line
                  else f', extra=inline_note("{esc}")))')
        lines[idx] = old_line[:k] + joiner

def _emit_notes(notes, ul_open_called=False, hero_name=None, version=None,
                loc_map=None, current_ability_slug=None):
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

    consumed = set()                # sub-note indices already folded into a parent row

    for i, n in enumerate(notes):
        if i in consumed:
            continue
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

        open_ul_if_needed()
        # Check patchnotes_english: warn if this text belongs to a different ability.
        if loc_map is not None and current_ability_slug is not None:
            txt_norm = re.sub(r'\s+', ' ', _strip_html(txt)).lower().strip()
            expected_slug = loc_map.get(txt_norm)
            if expected_slug is not None and expected_slug != current_ability_slug:
                lines.append(f'# [patchnotes: belongs to {expected_slug}]')
        lines.append(_emit_li(txt, info=info, aghs=aghs, hero_name=hero_name, version=version))
        pending_parent_text = txt
        last_indent = lvl
        has_content = True

        # Nested notes (the official patch page indents them under this bullet)
        # go into this row's "?" popup — all of them, lists and sub-changes
        # alike, the trailing ":" dropped. Kept as rows: "Damage at level N"
        # consequences (a visible row by rule) and the body of card-type
        # parents (_KIDS_ARE_BODY).
        desc = _descendants(notes, i)
        if (desc and lines[-1].startswith('W(li(') and not aghs
                and not _KIDS_ARE_BODY.match(clean)
                and not any(notes[j].get('hide_dot') for j in desc)):
            folded = [j for j in desc
                      if not _DMG_L1_RE.search(_strip_html(notes[j].get('note') or ''))]
            if folded:
                lines[-1] = re.sub(r':(?=")', '', lines[-1], count=1)   # "…the following:" → "…the following"
                _fold_into_row(lines, len(lines) - 1, _nested_info_text(notes, lvl, folded))
                consumed.update(folded)

    if open_ul:
        lines.append('W(ul_close())')
    lines = _sort_source_ul_blocks(lines)
    return lines, has_content


# ---------- ENTITY RENDERERS ----------

def _entity_title_decoration(entity):
    """Map raw `title` HTML (e.g. '<span class="New">New Tier 1 Artifact</span>')
    to item_header() decoration args."""
    title = entity.get('title')
    if not title:
        return ''
    txt = _strip_html(title).strip()
    if 'New' in txt or 'Returning' in txt:
        return f', new="{txt}"'
    if 'Rework' in txt:
        return f', changed="{txt}"'
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
        if 'changed=' not in deco:          # "Item Reworked" label already set
            deco += ', changed=True'
        notes = notes[1:]
    # "Item Reworked" title: the component diff renders from items.json, so the
    # datafeed's "Requires A, B and C. Total cost: N" row would only repeat it.
    is_reworked = not is_enchantment and 'changed="' in deco
    if is_reworked and notes and re.match(
            r'^Requires\b', _strip_html(notes[0].get('note', '')).strip()):
        notes = notes[1:]
    # Detect "New Tier N Artifact" / "Returning as a Tier N Neutral Artifact" as
    # the first note in neutral items — convert to item_header(new="...") and drop.
    _NEW_RET_RE = re.compile(
        r'^(New|Returning(?:\s+as\s+a))\s+Tier\s+\d+\s+(?:Neutral\s+)?Artifact$',
        re.I,
    )
    if neutral and not deco and notes:
        first_txt = _strip_html(notes[0].get('note', '')).strip()
        m = _NEW_RET_RE.match(first_txt)
        if m:
            # Normalise: "Returning as a Tier 2 Neutral Artifact" → "Returning Tier 2 Artifact"
            norm = re.sub(r'\s+as\s+a\b', '', first_txt, flags=re.I)
            norm = re.sub(r'\s+Neutral\b', '', norm, flags=re.I)
            deco = f', new="{norm}"'
            notes = notes[1:]
    # "New basic Equipment item. Costs 250 gold" under a generic "New Item" title → the
    # header label says it ("New Basic Equipment Item"); the row would only repeat it.
    # Its nested notes stay as the item's rows.
    if deco == ', new="New Item"' and notes:
        m = re.match(r'^(New\s+(?:\w+\s+)?\w+\s+item)\b\.?(?:\s*Costs\s+\d+\s+gold\.?)?$',
                     _strip_html(notes[0].get('note', '')).strip(), re.I)
        if m:
            deco = f', new="{m.group(1).title()}"'
            lvl = notes[0].get('indent_level', 1)
            notes = [dict(n, indent_level=max(1, n.get('indent_level', 1) - 1)) if i and n.get('indent_level', 1) > lvl
                     else n for i, n in enumerate(notes)][1:]
    if is_enchantment:
        out.append(f'W(enchant_header("{name}"))')
    else:
        out.append(f'W(item_header("{name}"{deco}))')
    if is_recipe_changed or is_reworked:
        out.append(f'W(auto_components_change("{name}", "{version}"))')
    body, _ = _emit_notes(notes)
    out.extend(body)
    return out


def _facet_card(slug, style, body_lines):
    """Valve-flagged facet → card lines, else None. NewFacet → new_facet(desc=rows);
    ReworkedFacet → facet_change with the rows as NEW and an OLD pane the proofreader
    fills from the previous patch's state (KV values + earlier patch notes)."""
    kind = 'new' if 'NewFacet' in style else ('rework' if 'ReworkedFacet' in style else None)
    if not kind:
        return None
    import ast as _ast
    items = []
    for line in body_lines:
        if not line.startswith('W(li('):
            continue
        try:
            call = _ast.parse(line, mode='eval').body.args[0]
        except SyntaxError:
            return None
        if not call.args or not isinstance(call.args[0], _ast.Constant):
            return None
        text = call.args[0].value.replace('\\', '\\\\').replace('"', '\\"')
        item = f'"{text}"'
        for a in call.args[1:]:
            if not (isinstance(a, _ast.Call) and getattr(a.func, 'id', '') == 't'):
                item += ' + " " + ' + _ast.get_source_segment(line, a)
        extra = next((k.value for k in call.keywords if k.arg == 'extra'), None)
        if extra is not None:
            item += ' + " " + ' + _ast.get_source_segment(line, extra)
        items.append(item)
    if not items:
        return None
    rows = ''.join(f'\n    {it},' for it in items)
    if kind == 'new':
        return [f'W(new_facet("{slug}", desc=[{rows}\n]))']
    return [f'W(facet_change("{slug}",\n'
            f'    old_desc=["TODO: the facet as it was in the previous patch (KV values + earlier notes)"],\n'
            f'    new_desc=[{rows}\n]))']


def _render_hero(hero, version=None, patchnotes_loc=None, prev_hero_abils=None):
    """One heroes[] entry: hero_header + hero_notes + abilities + subsections.

    prev_hero_abils: {hero_id: {ability_slug: {'dname': str, 'is_innate': bool}}}
    Built from the previous patch datafeed in generate() to detect renamed/removed
    abilities and correctly attribute hero_notes with "AbilityName: ..." prefixes.
    """
    out = []
    hid = hero.get('hero_id')
    name, slug = HEROES.get(hid, (f'hero_{hid}', f'hero_{hid}'))
    # Per-hero loc_map from patchnotes_english (text_norm → ability_slug).
    hero_loc = (patchnotes_loc or {}).get(slug, {})
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
        # Build display-name → slug reverse map for ALL currently-existing abilities
        # (from abilities_slim.json, which reflects current KV files).
        # A prefix present here belongs to a CURRENT ability — don't wrap it.
        # A prefix absent here means the ability no longer exists in the game
        # (renamed/removed in this or an earlier patch) — it's a previous-patch
        # ability and should be emitted under an ability() block.
        _current_abil_dname_to_slug = {
            v.get('dname', '').lower(): k
            for k, v in ABILS_SLIM.items()
            if v.get('dname')
        }
        # Whether this hero currently has a known innate in abilities_slim.
        # Used to infer innate status for old (now-renamed) innate abilities.
        _hero_has_current_innate = any(
            v.get('is_innate')
            for k, v in ABILS_SLIM.items()
            if k.startswith(slug + '_')
        )
        # Partition notes: bucket by facet name prefix, or keep as general
        _general_notes = []
        _facet_buckets = {}   # facet_slug -> [notes]
        _abil_buckets = {}    # abil_slug -> {'name': str, 'is_innate': bool, 'notes': [...]}
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
                    else:
                        print(f'[WARN] Removed facet "{part}" not in FACETS — '
                              f'add slug to badges.py, then re-generate')
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
                # Check for "AbilityName: change text" where AbilityName refers to
                # an ability that no longer exists in the current game (renamed or
                # removed in this or a prior patch). If the prefix IS a current
                # ability (found in abilities_slim by dname), it's not a routing
                # signal — fall through to _general_notes.
                if prefix.lower() not in _current_abil_dname_to_slug:
                    # Derive slug: hero_slug + "_" + display name words
                    derived_slug = slug + '_' + re.sub(r"[^a-z0-9]+", '_', prefix.lower()).strip('_')
                    # Innate status: check if the hero currently has a known innate
                    # (abilities_slim). If yes, the old ability being discussed was
                    # likely the previous innate — mark innate=True.
                    is_innate_flag = _hero_has_current_innate
                    stripped_note = dict(n)
                    stripped_note['note'] = re.sub(
                        re.escape(prefix) + r':\s*', '', n.get('note', ''), count=1, flags=re.I
                    )
                    entry = _abil_buckets.setdefault(
                        derived_slug, {'name': prefix, 'is_innate': is_innate_flag, 'notes': []}
                    )
                    entry['notes'].append(stripped_note)
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
        # Emit ability blocks from "AbilityName: ..." hero_notes (removed/renamed abilities)
        for abil_slug, entry in _abil_buckets.items():
            innate_kwarg = ', innate=True' if entry.get('is_innate') else ''
            out.append(f'W(ability("{entry["name"]}", slug="{abil_slug}"{innate_kwarg}))')
            body, _ = _emit_notes(entry['notes'])
            out.extend(body)
    # Facet subsections — before Abilities (order: stats > innates > facets > abilities > talents)
    from patch.badges import FACETS as _FACETS
    for s in hero.get('subsections', []):
        if s.get('style', '').startswith('hero_facet'):
            facet_slug = s.get('facet')
            facet_title = s.get('title', '')
            facet_color = s.get('facet_color', '')
            # Warn if slug missing from FACETS so user can register it in badges.py
            if facet_slug not in _FACETS:
                print(f'[WARN] facet "{facet_slug}" not in FACETS — add to badges.py: '
                      f'"{facet_slug}": ("{facet_title}", "{facet_color}")')
            facet_start = len(out)
            out.append(f'W(facet_header("{facet_slug}"))')
            # general_notes on the facet subsection itself (e.g. radius changes)
            general_notes = s.get('general_notes', [])
            if general_notes:
                gbody, _ = _emit_notes(general_notes)
                out.extend(gbody)
            # Collect all notes from all abilities in this facet into one list
            all_facet_notes = []
            for a in s.get('abilities', []):
                aid = a.get('ability_id')
                abil_name = ABILS.get(aid, (None, None))[0]
                # Prefix "AbilityName: " unless facet display name == ability name
                prefix = ''
                if abil_name and abil_name.lower() != facet_title.lower():
                    prefix = f'{abil_name}: '
                notes = a.get('ability_notes', [])
                if prefix and notes:
                    prefixed = []
                    for note in notes:
                        n2 = dict(note)
                        n2['note'] = prefix + n2.get('note', '')
                        prefixed.append(n2)
                    all_facet_notes.extend(prefixed)
                else:
                    all_facet_notes.extend(notes)
            body, _ = _emit_notes(all_facet_notes)
            out.extend(body)
            # talent_notes inside facet subsection (e.g. NP Soothing Saplings).
            # Emit directly (no subgroup call) so notes land inside the facet block.
            facet_talents = s.get('talent_notes', [])
            if facet_talents:
                tbody, _ = _emit_notes(facet_talents)
                out.extend(tbody)
            # Valve flags the facet itself: "hero_facet NewFacet" / "hero_facet ReworkedFacet"
            card = _facet_card(facet_slug, s.get('style', ''), out[facet_start + 1:])
            if card:
                out[facet_start:] = card
    # Abilities
    for a in hero.get('abilities', []):
        aid = a.get('ability_id')
        aname, aslug = ABILS.get(aid, (f'ability_{aid}', f'ability_{aid}'))
        innate_kwarg = ', innate=True' if '_innate_' in aslug else ''
        out.append(f'W(ability("{aname}", slug="{aslug}"{innate_kwarg}))')
        # Strip "AbilityName: " prefix from notes — the ability() block already shows the name
        notes = a.get('ability_notes', [])
        stripped = []
        for ni, note in enumerate(notes):
            n2 = dict(note)
            txt = n2.get('note', '')
            if ni == 0 and aname and txt.lower().startswith(aname.lower() + ': '):
                n2['note'] = txt[len(aname) + 2:]
            stripped.append(n2)
        body, _ = _emit_notes(stripped, loc_map=hero_loc, current_ability_slug=aslug)
        out.extend(body)
    # Talents — always last
    talents = hero.get('talent_notes', [])
    if talents:
        out.append('W(subgroup("Talents"))')
        body, _ = _emit_notes(talents)
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
    icon = f'NEUTRAL_CDN + "{slug}.png"' if slug else '""'
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
        # Strip "AbilityName: " prefix from first note — ability() block already shows the name
        stripped = []
        for ni, note in enumerate(bucket):
            n2 = dict(note)
            txt = n2.get('note', '')
            if ni == 0 and txt.lower().startswith(dname.lower() + ': '):
                n2['note'] = txt[len(dname) + 2:]
            stripped.append(n2)
        body, _ = _emit_notes(stripped)
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


# NOTE: These regexes are tightly coupled to _emit_li() output format.
# Two emission shapes for the same semantic case (net cost zero):
#   A) "Recipe cost X from A to B. Total cost unchanged at C ..." — single string
#   B) "Recipe cost X from A to B"  +  inline_note("Total cost unchanged ...")
# A cheaper recipe with an unchanged total is a BUFF (component stats arrive
# earlier and the final combine is cheaper); a pricier recipe is a NERF. So the
# recipe b() badge drives the row tag — NOT t("MISC").
# "Recipe cost X→Y. Total cost decreased/increased X→Y" — both changed.
# Badge by total cost; recipe % goes inline in the text.
_RECIPE_COST_BOTH_CHANGED_RE = re.compile(
    r'^W\(li\("(Recipe cost (?:increased|decreased) from )(\d+)( to )(\d+)'
    r'(\. Total [Cc]ost (?:increased|decreased) from )(\d+)( to )(\d+)",\s*'
    r'b\(\d+,\s*\d+,\s*l=True\)\)\)$'
)

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
    """Rewrite recipe-cost rows to the correct badge form:
    - Both recipe and total changed: recipe % inline, total badge as main.
    - Recipe changed, total unchanged: recipe badge as main (BUFF if cheaper,
      NERF if pricier) — a cheaper recipe is a real player benefit.
    """
    out = []
    for line in lines:
        m = _RECIPE_COST_BOTH_CHANGED_RE.match(line)
        if m:
            rpre, ra, rmid, rb, tpre, ta, tmid, tb = m.groups()
            # Total cost direction determines l=True (lower=buff for costs)
            out.append(
                f'W(li("{rpre}{ra}{rmid}{rb} " + b({ra}, {rb}, l=True)'
                f' + "{tpre}{ta}{tmid}{tb}", b({ta}, {tb}, l=True)))'
            )
            continue
        m = _RECIPE_COST_UNCHANGED_INLINE_RE.match(line)
        if m:
            prefix, a, mid, b_val, tail = m.groups()
            out.append(
                f'W(li("{prefix}{a}{mid}{b_val}{tail}", b({a}, {b_val}, l=True)))'
            )
            continue
        m = _RECIPE_COST_UNCHANGED_SPLIT_RE.match(line)
        if m:
            prefix, a, mid, b_val, note_text = m.groups()
            out.append(
                f'W(li("{prefix}{a}{mid}{b_val}", b({a}, {b_val}, l=True), '
                f'extra=inline_note("{note_text}")))'
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


# "36 + (9 per 5 minutes)" / "40 + 6 per minute" — a value that grows with GAME
# TIME. A "from <formula> to <formula>" line of two such formulas becomes a
# li_formula with a minute table (memory sloppy_per_minute_formula_table).
_PER_MINUTES_FORMULA_RE = re.compile(
    r'^(?P<base>\d+(?:\.\d+)?)\s*\+\s*\(?\s*(?P<inc>\d+(?:\.\d+)?)\s+(?:\w+\s+)?'
    r'(?:per|every)\s+(?:(?P<n>\d+)\s+)?min(?:ute)?s?\s*\)?$'
)
_MINUTE_GRID = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]


def _minute_lambda(m):
    base, inc, n = m.group('base'), m.group('inc'), m.group('n')
    return (f'lambda M: {base} + {inc} * (M // {n})' if n and n != '1'
            else f'lambda M: {base} + {inc} * M')


def _postprocess_minute_formula(lines):
    """W(li("X from A + (B per N minutes) to C + (D per K minutes)", t(..)))
    -> W(li_formula(...)) with a minute table (5:00 … 60:00)."""
    out = []
    for line in lines:
        diff = _FORMULA_DIFF_LINE_RE.match(line)
        mo = mn = None
        if diff:
            mo = _PER_MINUTES_FORMULA_RE.match(diff.group('old').strip())
            mn = _PER_MINUTES_FORMULA_RE.match(diff.group('new').strip())
        if not (mo and mn):
            out.append(line)
            continue
        out.append(
            f'W(li_formula("{diff.group("prefix")}", "{diff.group("old")}", "{diff.group("new")}", '
            f'{_minute_lambda(mo)}, {_minute_lambda(mn)}, levels={_MINUTE_GRID}, '
            f'level_fmt=lambda M: f"{{M}}:00", headline_level=5, jump_at=None))'
        )
    return out


# A block (plain_header / subgroup) that introduces something brand new gets a
# label after its title: "New objective" for map objectives (buildings, shrines,
# runes, bosses), "New mechanic" otherwise. Its MISC rows become NEW.
_NEW_BLOCK_RE = re.compile(
    r'\breplaced with (?:a )?new\b|\bnew (?:buildings?|objectives?|structures?|mechanics?)\b'
    r'|\b(?:has|have) been added to the map\b', re.I)
_NEW_OBJECTIVE_RE = re.compile(
    r'\b(?:buildings?|objectives?|structures?|shrines?|runes?|outposts?|pools?|boss(?:es)?)\b', re.I)
_BLOCK_HEAD_RE = re.compile(r'^W\((?P<fn>plain_header|subgroup)\("(?P<title>[^"]+)"(?P<rest>.*)\)\)$')


def _postprocess_new_block_label(lines):
    out = list(lines)
    section = ''
    for i, line in enumerate(out):
        head = _BLOCK_HEAD_RE.match(line)
        if not head:
            continue
        if head.group('fn') == 'plain_header':
            section = head.group('title')
        if 'new=' in head.group('rest'):
            continue
        j = i + 1
        rows = []
        while j < len(out) and not _BLOCK_HEAD_RE.match(out[j]):
            if out[j].startswith('W(li("'):
                rows.append(j)
            j += 1
        # the announcing row must be the block's FIRST row — a later "replaced
        # with new …" line inside an old block is an ordinary change
        if not rows or not _NEW_BLOCK_RE.search(out[rows[0]]):
            continue
        objective = (section.lower() == 'map objectives'
                     or _NEW_OBJECTIVE_RE.search(out[rows[0]]))
        label = 'New objective' if objective else 'New mechanic'
        out[i] = line[:-2] + f', new="{label}"))'
        for r in rows:
            out[r] = out[r].replace('t("MISC")', 't("NEW")')
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
    pending_facet_idx = None
    for line in lines:
        if line.startswith('W(ability('):
            pending_ability_idx = len(out)
            pending_facet_idx = None
            out.append(line)
            continue
        if line.startswith('W(facet_header('):
            pending_facet_idx = len(out)
            pending_ability_idx = None
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
        elif pending_facet_idx is not None and line.startswith('W(li("'):
            if any(trig in line for trig in _REWORK_TRIGGERS):
                out.insert(
                    pending_facet_idx,
                    '# v2-todo: facet reworked — convert to facet_change(slug, old_desc=[...], new_desc=[...]) '
                    '— verify "Reworked" badge on dota2.com/patches, lift OLD desc from prior patchnotes'
                )
            pending_facet_idx = None
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


def _build_prev_hero_abils(version):
    """Load the previous patch's datafeed and return a per-hero ability snapshot.

    Returns {hero_id: {slug: {'dname': str, 'is_innate': bool}}} so that
    _render_hero() can diff current vs previous abilities and correctly route
    hero_notes with "AbilityName: ..." prefixes to the right ability() block.
    """
    from patch.meta import _prev_patch_version
    prev_ver = _prev_patch_version(version)
    if not prev_ver:
        return {}
    prev_path = os.path.join(_HERE, 'data', f'{prev_ver}_datafeed.json')
    try:
        prev_d = fetch_datafeed(prev_ver)
    except Exception:
        return {}
    result = {}
    for hero in prev_d.get('heroes', []):
        hid = hero.get('hero_id')
        abils = {}
        for a in hero.get('abilities', []):
            aid = a.get('ability_id')
            resolved = ABILS.get(aid)
            if not resolved:
                continue
            aname, aslug = resolved
            abils[aslug] = {
                'dname': aname,
                'is_innate': ABILS_SLIM.get(aslug, {}).get('is_innate', False),
            }
        result[hid] = abils
    return result


def generate(version):
    d = fetch_datafeed(version)
    patchnotes_loc = _load_patchnotes_loc(version)
    prev_hero_abils = _build_prev_hero_abils(version)

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
                out.extend(_render_hero(hero, version=version, patchnotes_loc=patchnotes_loc, prev_hero_abils=prev_hero_abils))

    # Post-process passes that operate on the full emitted line list:
    # 1. Collapse aghs upgrade-row + description into canonical merged li.
    # 2. Auto-emit scale_pill(...) for per-level formula text.
    # 3. Drop a v2-todo breadcrumb above ability blocks tagged "reworked".
    out = _postprocess_aghs_merge(out)
    out = _postprocess_minute_formula(out)
    out = _postprocess_scale_pill(out)
    out = _postprocess_new_block_label(out)
    out = _postprocess_properties_change(out)
    out = _postprocess_drop_now_requires(out)
    out = _postprocess_recipe_cost_zero_net(out)
    out = _postprocess_rework_marker(out)

    # Close the page: footer + save. Emitted so the wrapped content/pXXX.py is
    # complete — without these the site build runs green but the patch HTML is
    # never written to dist/ (save_html is what flushes the page to disk). Match
    # the two trailing lines every content/p*.py ends with.
    out.append('')
    out.append('write_footer()')
    out.append(f"save_html('patches/{version}.html')")

    return '\n'.join(out)


def _auto_register_facets(version, datafeed):
    """Add any missing facet slugs from datafeed into patch/badges.py FACETS dict.

    Reads the datafeed for facet subsections, checks each slug against the
    current FACETS dict, and appends missing entries at the end of the FACETS
    block in badges.py.
    """
    from patch.badges import FACETS
    badges_path = os.path.join(_HERE, 'patch', 'badges.py')

    missing = {}
    for hero in datafeed.get('heroes', []):
        for s in hero.get('subsections', []):
            if s.get('style', '').startswith('hero_facet'):
                slug = s.get('facet', '')
                if slug and slug not in FACETS and slug not in missing:
                    missing[slug] = (s.get('title', slug), s.get('facet_color', 'Gray3'))

    if not missing:
        return

    src = open(badges_path, encoding='utf-8').read()
    # Find the closing brace of the FACETS dict specifically.
    # FACETS is followed by the _FACET_COLOR_GRADIENT comment block, so we
    # search for "}\n\n# Mapping from Valve" which is unique to the FACETS end.
    import re as _re
    facets_end = _re.search(r'\n}\n\n# Mapping from Valve', src)
    if not facets_end:
        print(f'[WARN] Could not auto-register facets — could not locate FACETS closing brace')
        return
    last_brace_idx = facets_end.start()

    new_lines = [f'    # {version} — auto-registered by generate_patch_code_v2.py']
    for slug, (title, color) in missing.items():
        new_lines.append(f'    "{slug}": ("{title}", "{color}"),')
        print(f'[INFO] Auto-registered facet: "{slug}": ("{title}", "{color}")')

    insertion = '\n'.join(new_lines)
    new_src = src[:last_brace_idx] + '\n' + insertion + src[last_brace_idx:]
    open(badges_path, 'w', encoding='utf-8').write(new_src)
    print(f'[INFO] Updated patch/badges.py with {len(missing)} new facet(s)')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python generate_patch_code_v2.py <version>', file=sys.stderr)
        sys.exit(1)
    version = sys.argv[1]
    d = fetch_datafeed(version)

    # 0. Auto-register any new facet slugs into patch/badges.py
    _auto_register_facets(version, d)

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
        print(f'[WARN] validation skipped: {e}', file=sys.stderr)
