"""One patch note as one W(li(...)) line: its badge, tag and level values."""
import json
import os
import re

from .common import _HERE
from .data import _strip_html
from .tags import _FROM_TO_RE, _guess_tag, _is_lower_better

def _split_levels(s):
    """'5/7/9/11' or '5' or '52–56' → list or scalar. Strips trailing unit suffix (%/s/x/g).
    En-dash ranges (52–56) are kept as-is (string); / separates levels."""
    s = s.rstrip('%sxg')
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


_MISSING_FROM_RE = re.compile(r'\b(increased|decreased|rescaled|reduced)\s+(?=[-+]?\d[\d./%s]*\s+to\s+[-+]?\d)', re.I)


def _add_missing_from(text):
    """"Damage increase per armor decreased 0.3% to 0.25%", "Split Amount rescaled 80/85/90/95/100% to 85/90/95/100%"
    (7.37): Valve left out "from" — the row still has its old and new values."""
    return _MISSING_FROM_RE.sub(r'\1 from ', text)


def _emit_badge(text, hero_side=False):
    """Try to extract from-N-to-M and emit b(...). Returns badge code str
    (e.g. 'b([5,7,9,15], [5,7,9,11])') or None if no numeric change.
    hero_side: the row sits under a hero, so a bounty is what the ENEMY gets for killing the hero's unit
    (Spirit Bear, Tempest Double: lower is better — audit 2026-10-05); a neutral creep's bounty stays higher-is-better."""
    text = _add_missing_from(text)
    flat = _emit_flat_to_pct_badge(text)
    if flat:
        return flat
    m = _TALENT_INSTEAD_RE.search(text)
    if m:                           # "Level 25 Talent is +4s Burning Spears Duration instead of +6s" (7.37 Huskar): 6 → 4
        old, new = float(m.group("old")), float(m.group("new"))
        num = lambda v: int(v) if v.is_integer() else v
        return f'b({num(old)!r}, {num(new)!r}{", l=True" if _is_lower_better(text) else ""})'
    m = _FROM_TO_RE.search(text)
    if not m:
        return _emit_range_badge(text, hero_side)
    old = _split_levels(m.group(1))
    new = _split_levels(m.group(2))
    if old is None or new is None:
        return None
    # every value negative: Valve's word and the effect follow the size ("Armor Corruption decreased from -4 to -3",
    # 7.37 Hoodwink talent: a weaker armor reduction) — compare the sizes; mixed signs (7.38 Self Speed) stay as they are
    old, new = _by_size(old, new)
    # A tier/level added at the end ("+125/135 to +125/135/145", 7.41 Keen-Eyed): compare the new top tier with
    # the old top one. b() zips the lists, so the new tier was dropped and the row read a grey 0% (audit 2026-10-05).
    if isinstance(old, list) and isinstance(new, list) and len(new) > len(old) and new[:len(old)] == old:
        old = old + [old[-1]] * (len(new) - len(old))
    said = _said_lower_better(text, old, new)
    l = _is_lower_better(text) if said is None else said
    if hero_side and said is None and re.search(r'\bbounty\b', text, re.I):
        l = True
    l_arg = ', l=True' if l else ''
    force_arg = ', force_overall="buff"' if _l1_only_dip(old, new, l) else ''
    return f'b({old!r}, {new!r}{l_arg}{force_arg})'


_TALENT_INSTEAD_RE = re.compile(r"\bTalent is [+\-]?(?P<new>\d+(?:\.\d+)?)(?P<u>%|s)?\s+[A-Za-z' ]+?\s+instead of\s+"
                                r"[+\-]?(?P<old>\d+(?:\.\d+)?)(?P=u)?\s*$")


# "bonus changed from flat +110 to +40% (results in +48)" (7.37e Rolling Thunder): the % is of a base the row itself
# gives (48 / 40% = 120), so the badge compares the totals 120+110 = 230 → 168 (owner 2026-10-29: "да", −27%)
_FLAT_TO_PCT_RE = re.compile(
    r'\bfrom\s+flat\s+\+?(\d+(?:\.\d+)?)\s+to\s+\+?(\d+(?:\.\d+)?)%\s*\(results?\s+in\s+\+?(\d+(?:\.\d+)?)\)', re.I)


def _emit_flat_to_pct_badge(text):
    m = _FLAT_TO_PCT_RE.search(text)
    if not m:
        return None
    old_bonus, pct, new_bonus = (float(x) for x in m.groups())
    if not pct:
        return None
    num = lambda v: int(round(v)) if abs(v - round(v)) < 1e-6 else round(v, 2)
    base = new_bonus * 100 / pct
    l_arg = ', l=True' if _is_lower_better(text) else ''
    return f'b({num(base + old_bonus)!r}, {num(base + new_bonus)!r}{l_arg})'


# "from 18-24 on all levels to 16/24/32/40" (7.37e Treant bounty), "from 14-20 to 17-20" (Eidolon bounty): a min-max
# range on the old side — compared by its middle (owner 2026-10-28: "среднее от 18-24 взять для сравнения")
_RANGE_FROM_RE = re.compile(
    r'\bfrom\s+(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)(?:\s+on\s+all\s+levels)?\s+to\s+'
    r'(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?|(?:/\d+(?:\.\d+)?)+)?)\b')


# "from 28-32/44-48/60-64/76-80 to 22-26/40-44/58-62/76-80" (7.37d Treant Damage): a min-max range per level — each
# level compared by its middle, as the single range above
_LEVEL_RANGES_RE = re.compile(
    r'\bfrom\s+((?:\d+(?:\.\d+)?-\d+(?:\.\d+)?/)+\d+(?:\.\d+)?-\d+(?:\.\d+)?)\s+to\s+'
    r'((?:\d+(?:\.\d+)?-\d+(?:\.\d+)?/)+\d+(?:\.\d+)?-\d+(?:\.\d+)?)\b')


def _level_range_middles(s):
    num = lambda v: int(v) if v == int(v) else v
    return [num(sum(float(x) for x in r.split('-')) / 2) for r in s.split('/')]


def _emit_range_badge(text, hero_side=False):
    lv = _LEVEL_RANGES_RE.search(text)
    if lv:
        old, new = _level_range_middles(lv.group(1)), _level_range_middles(lv.group(2))
        if len(old) == len(new):
            l = _is_lower_better(text) or bool(hero_side and re.search(r'\bbounty\b', text, re.I))
            return f'b({old!r}, {new!r}{", l=True" if l else ""})'
    m = _RANGE_FROM_RE.search(text)
    if not m:
        return None
    lo, hi, new = float(m.group(1)), float(m.group(2)), m.group(3)
    l = _is_lower_better(text) or bool(hero_side and re.search(r'\bbounty\b', text, re.I))
    l_arg = ', l=True' if l else ''
    num = lambda v: int(v) if v == int(v) else v
    if '-' in new:
        n_lo, n_hi = (float(x) for x in new.split('-'))
        return f'br({num(lo)}, {num(hi)}, {num(n_lo)}, {num(n_hi)}{l_arg})'
    levels = _split_levels(new)
    if levels is None:
        return None
    return f'b({num((lo + hi) / 2)!r}, {levels!r}{l_arg})'


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


_HERO_SIDE = [False]      # True while generate() renders the Heroes section
# the draft clock (7.08 "All Pick drafting time per hero selection reduced from 30s to 25s" was a red -17%)
_DRAFT_TIME_RE = re.compile(r'\b(?:drafting|pick(?:ing)?|ban(?:ning)?|strategy|hero selection)\s+(?:phase\s+)?time\b', re.I)


def _emit_li(text, tag_override=None, aghs=None, info=None, hero_name=None, version=None):
    """Render one W(li(...)) call. tag_override overrides heuristic; aghs is
    'scepter'/'shard' (already encoded in text if from datafeed); info is
    optional inline_note text appended. hero_name+version enable bstat_h."""
    txt = text.strip()
    # "Active: Disarm can now be dispelled" is a CHANGE to the active, not its description
    # ("Active: Name. What it does …") — drop the prefix so it renders as a plain change row
    chg = re.match(r"^(?:Active|Passive|Toggle): ([A-Z][\w' ]{1,30}?) (?:can now|can no longer|no longer|now|is now|is no longer)\b", txt)
    if chg and '. ' not in txt[:len(chg.group(0))]:
        txt = txt.split(': ', 1)[1]
    clean = _strip_html(txt)
    if re.match(r'^Level (?:increased|decreased|changed) from \d+ to \d+$', clean):
        return f'W(li("{txt}", t("MISC")))'        # a creep's level: classification, not a buff/nerf
    if _DRAFT_TIME_RE.search(clean):
        return f'W(li("{txt}", t("MISC")))'        # both teams draft under the same clock: nobody gains (audit 2026-10-05)

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

    badge_call = _emit_badge(txt, hero_side=bool(hero_name) or _HERO_SIDE[0])
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


_AGHS_NOW_RE = re.compile(r"Now upgraded with Aghanim's (Scepter|Shard)\.?", re.I)
# a kid that is a row of its own, not the upgrade's description ("is decreased by 2s" is description: Storm Surge 7.41)
_NOT_AGHS_DESC = re.compile(r"^No longer\b|Aghanim's", re.I)


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


def _said_lower_better(text, old, new):
    """Valve's own "improved" / "worsened" settles the direction: improved toward a smaller number (or worsened
    toward a bigger one) means lower is better ("Ghost spawn rate improved from 0.35s to 0.25s", "Duration improved
    from 10s to 8s"; 2026-10-03 cross-check of 7.40-7.41). None when the row doesn't say or the means are equal."""
    word = re.search(r'\b(improved|worsened)\b', text, re.I)
    if not word or old is None or new is None:
        return None
    o, n = _mean(old), _mean(new)
    if o == n:
        return None
    return (n < o) == (word.group(1).lower() == 'improved')


def _by_size(old, new):
    """(old, new) by size when every value is negative — the direction of an armor reduction "-4 → -3" (7.37 Hoodwink
    talent) is its size's, as the b() badge (_emit_badge); else as they are."""
    if old is None or new is None:
        return old, new
    vals = [*(old if isinstance(old, list) else [old]), *(new if isinstance(new, list) else [new])]
    if not all(isinstance(v, (int, float)) and v < 0 for v in vals):
        return old, new
    flip = lambda x: [abs(v) for v in x] if isinstance(x, list) else abs(x)
    return flip(old), flip(new)
