"""Passes over the scaffold's lines: boss blocks, new item cards, innate rows, rework markers."""
import json
import os
import re

from .common import _HERE, _KNOWN_ITEM_SLUGS
from .lines import _BOSSES, _ROW_RE, _boss_abilities, _row
from .post_stats import _NEW_ABILITY_TRIGGERS, _REWORK_TRIGGERS
from .rows import _emit_li

def _postprocess_boss_blocks(lines, version=None):
    """W(subgroup("Tormentor")) + flat rows  ->  unit_header(..., general=False, track=True),
    general rows, then one block per ability:
      "Alleviation: New ability. X"            -> new-ability card (ability_change(None, …, tag="new"))
      "The Shining: <change>" / "Roar of Retribution" + info lines -> ability(...) + its rows
      info line "Unyielding Shield: … rescaled from A + (B per death) to …" -> a "Scaling reworked" card when the
      formula's variable changed (_scaling_cards, patch/scaling_card.py), else a TODO.
    If every general row is REWORK except NEW ones (and ≥3 REWORK) -> new_mech="Reworked objective":
    the REWORK rows become the description box, the NEW rows stay changes."""
    out = []
    i = 0
    while i < len(lines):
        m = re.match(r'^W\(subgroup\("(?P<name>[^"]+)"\)\)$', lines[i])
        if not (m and m.group('name') in _BOSSES and i + 1 < len(lines) and lines[i + 1] == 'W(ul_open())'):
            out.append(lines[i])
            i += 1
            continue
        name = m.group('name')
        icon, prefix = _BOSSES[name]
        abil_icons = _boss_abilities(prefix)
        j = i + 2
        body = []
        while j < len(lines) and lines[j] != 'W(ul_close())':
            body.append(lines[j])
            j += 1
        general, per_abil, todos, new_cards = [], {}, [], []
        for ln in body:
            r = _ROW_RE.match(ln)
            raw = re.match(r'^W\(li(?:_formula)?\("((?:[^"\\]|\\.)*)"', ln)
            text = raw.group(1) if raw else ''
            hit = next((a for a in sorted(abil_icons, key=len, reverse=True)
                        if text == a or text.startswith(a + ': ')), None)
            # Valve without the colon (7.41: "Unyielding Shield Base barrier increased from 2000 to 3000") — the
            # ability block too, its name off the row (owner 2026-10-16: "оформить, как мы уже делали")
            bare = next((a for a in sorted(abil_icons, key=len, reverse=True)
                         if not hit and re.match(re.escape(a) + r' [A-Za-z]', text)), None)
            if bare:
                m2 = re.match(r'^(W\(li(?:_formula)?\(")' + re.escape(bare) + r' ([A-Za-z])', ln)
                per_abil.setdefault(bare, []).append(m2.group(1) + m2.group(2).upper() + ln[m2.end():])
                continue
            if r and hit and text.startswith(hit + ': New ability. '):
                new_cards.append((hit, text[len(hit) + len(': New ability. '):]))
                continue
            if r and hit and text == hit and r.group('note'):          # "Roar of Retribution" + nested lines
                for part in r.group('note').split('<br>'):
                    per_abil.setdefault(hit, []).append(_emit_li(part))
                continue
            if hit:                                                     # "The Shining: Damage … increased …"
                per_abil.setdefault(hit, []).append(ln.replace(f'W(li("{hit}: ', 'W(li("', 1))
                continue
            if not raw:
                general.append(ln)
                continue
            if r and r.group('note'):                                   # info lines that belong to abilities
                keep = []
                for part in r.group('note').split('<br>'):
                    ab = next((a for a in abil_icons if part.startswith(a + ': ')), None)
                    if ab and re.search(r'\bper (?:death|minute)\b', part):
                        todos.append((ab, part))
                    else:
                        keep.append(part)
                if len(keep) != len(r.group('note').split('<br>')):
                    ln = _row(text, r.group('tag'), '<br>'.join(keep) or None)
            general.append(ln)
        tags = [mt.group('tag') if (mt := _ROW_RE.match(g)) else None for g in general]
        reworked = tags.count('REWORK') >= 3 and all(t_ in ('REWORK', 'NEW') for t_ in tags)
        mech = ', new_mech="Reworked objective"' if reworked else ''
        out.append(f'W(unit_header("{name}", "{icon}", general=False, track=True{mech}))')
        out += ['W(ul_open())'] + general + ['W(ul_close())']
        out += _scaling_cards(todos, abil_icons, version)
        for ab, rows in per_abil.items():
            out += [f'W(ability("{ab}", icon_url="{abil_icons[ab]}"))', 'W(ul_open())'] + rows + ['W(ul_close())']
        for ab, desc in new_cards:
            out.append(f'W(ability_change(None, {{"name": "{ab}", "icon_url": "{abil_icons[ab]}", '
                       f'"desc": ["{desc}"]}}, summary="New ability", tag="new"))')
        i = j + 1
    return out


_RESCALED_RE = re.compile(r"^(?P<ab>[^:]+): (?P<stat>.+?) rescaled from (?P<old>.+?) to (?P<new>.+)$")


def _scaling_cards(todos, abil_icons, version):
    """Info lines "Unyielding Shield: Damage absorb rescaled from 2500 + (200 per death) to 1900 + (20 per minute of game
    time)" -> one scaling_rework(...) card per ability when the formula's variable changed (owner 2026-11-06, 7.38
    Tormentor: was by hand); the description is the game's own of each patch. Anything else stays a TODO."""
    from patch.loc_history import tooltip
    from patch.meta import _prev_patch_version
    from patch.scaling_card import variable
    out, cards = [], {}
    for ab, part in todos:
        m = _RESCALED_RE.match(part)
        old_var, new_var = (variable(m.group("old")), variable(m.group("new"))) if m else (None, None)
        if not (old_var and new_var and old_var != new_var):
            out.append(f'# v2-todo: {ab} — scaling changed ({part}). Make an ability_change(old=…, new=…, '
                       f'tag="rework") card: formulas as scale_pill tables — see patch/scaling_card.py')
            continue
        cards.setdefault(ab, []).append((m.group("stat")[:1].upper() + m.group("stat")[1:], m.group("old"), m.group("new")))
    prev = _prev_patch_version(version) if version else None
    for ab, stats in cards.items():
        icon = abil_icons[ab]
        slug = icon.rsplit("/", 1)[-1].split(".")[0]
        desc = lambda v: (tooltip(f"DOTA_Tooltip_ability_{slug}_Description", v) or "") if v else ""
        out.append(f'W(scaling_rework({json.dumps(ab)}, {json.dumps(icon)}, {json.dumps(desc(prev), ensure_ascii=False)}, '
                   f'{json.dumps(desc(version), ensure_ascii=False)}, {stats!r}))')
    return out


_NEW_ITEM_COST_RE = re.compile(r'^Costs? (\d+)(?: gold|g)\.?$', re.I)   # "Costs 250 gold" / 7.42 Quarterstaff "Costs 900g"
_ABILITY_COSTS_ROW_RE = re.compile(
    r'^(?:(?:Global Cast Range|Cast Range: \d+|No Mana Cost|Mana Cost: \d+|No cooldown|Cooldown: [\d.]+s?)\.?\s*)+$', re.I)
_GENERIC_NEW_LABEL_RE = re.compile(r'new="(New|Returning) Item"')


def _py_str_item(s):
    return json.dumps(s, ensure_ascii=False)


def _li_text(row):
    m = re.match(r'^\s*W\(li\("((?:[^"\\]|\\.)*)"', row)
    return m.group(1) if m else ""


def _item_kind(name, version):
    """The shop tab of an item ("Equipment", "Miscellaneous" …), or "Consumable" for an item no shop sells whose
    ItemQuality says so (7.42 Greater Horn of Battle, a Tormentor drop), else None."""
    slug = _KNOWN_ITEM_SLUGS.get(name, name.lower().replace(' ', '_').replace("'", ''))
    try:
        from patch.rosters import _SHOP_CATEGORIES
    except ImportError:
        _SHOP_CATEGORIES = {}
    if f'item_{slug}' in _SHOP_CATEGORIES:
        return _SHOP_CATEGORIES[f'item_{slug}']
    try:
        with open(os.path.join(_HERE, 'data', 'stats', version or '', 'items.txt'), encoding='utf-8') as f:
            txt = f.read()
    except OSError:
        return None
    m = re.search(r'"item_' + re.escape(slug) + r'"\s*\{(.*?)\n\t\}', txt, re.S)
    q = re.search(r'"ItemQuality"\s*"(\w+)"', m.group(1)) if m else None
    return "Consumable" if q and q.group(1) == 'consumable' else None


def _with_item_kind(header, version):
    """A generic label "New Item" / "Returning Item" (7.42 Quarterstaff, Greater Horn of Battle) says what kind of
    item it is, as 7.41's "New Equipment Item" (owner 2026-11-19: "не по правилам сделаны")."""
    m = _GENERIC_NEW_LABEL_RE.search(header)
    name = re.match(r'^\s*W\(item_header\("([^"]+)"', header)
    kind = _item_kind(name.group(1), version) if m and name else None
    return header.replace(m.group(0), f'new="{m.group(1)} {kind} Item"') if kind else header
_REQ_ROW_RE = re.compile(r'^Requires (?P<parts>.+?)\. Total cost: (?P<total>\d+)g?$', re.I)
_REQ_PART_RE = re.compile(r"(?:and )?(?:an? )?(?P<name>[A-Za-z][\w' -]+?) \((?P<cost>\d+)\)")


_BONUS_ROW_RE = re.compile(r"^[+-]\d[\d./]*%? [A-Za-z][\w' ]+(?:, [+-]\d[\d./]*%? [A-Za-z][\w' ]+)*\.?$")


def _new_item_card_parts(text, note):
    """One row of a NEW item -> a card piece, or None if the row is a normal NEW row."""
    if re.match(r'^Provides no bonuses\.?$', text, re.I):
        return []                                          # nothing to show: no bonus box at all
    m = _NEW_ITEM_COST_RE.match(text)
    if m:
        return [f'cost={m.group(1)}']                      # the header takes it: a tag on the icon
    if re.match(r'^Dropped (?:from|by) ', text):           # where it comes from: a line under the name (2026-11-19)
        return [f'source={_py_str_item(text.rstrip("."))}']
    m = _REQ_ROW_RE.match(text)
    if m:
        parts = [(pm.group('name'), pm.group('cost')) for pm in _REQ_PART_RE.finditer(m.group('parts'))]
        recipe = next((c for n, c in parts if n.lower().endswith('recipe')), None)
        comps = ', '.join(f'("{n}", {c})' for n, c in parts if not n.lower().endswith('recipe'))
        rec = f', recipe=("Recipe", {recipe})' if recipe else ''
        return [f'W(components({comps}{rec}, total={m.group("total")}))']
    if _BONUS_ROW_RE.match(text):                         # "+100 Health" / "+125 Cast Range, -20% Max Mana"
        return [f'W(provides("{text.rstrip(".")}"))']
    m = re.match(r'^Provides (.+)$', text)
    if m:
        tip = f' + info_tip("{note}")' if note else ''
        bonuses = re.sub(r',? and ', ', ', m.group(1))          # "A, B, and C" -> one box row each
        return [f'W(provides("{bonuses}"{tip}))']
    return None


def _kv_item_cost(name, version):
    """ItemCost of a (new) item in this patch's KV snapshot, or None."""
    try:
        from patch.stats import _STATS_I
    except ImportError:
        return None
    slug = _KNOWN_ITEM_SLUGS.get(name, name.lower().replace(' ', '_').replace("'", ''))
    cost = (_STATS_I.get(version, {}).get(f'item_{slug}') or {}).get('ItemCost')
    try:
        return int(cost) if cost and int(cost) > 0 else None
    except (TypeError, ValueError):
        return None


_ENTITY_HEAD_RE = re.compile(r'^\s*W\((?:item_header|hero_header|unit_header|plain_header|section)\(')
_AUTO_COMP_RE = re.compile(r'^(\s*)W\(auto_components_change\("([^"]+)",\s*"([^"]+)"\)\)')
_COST_ROW_RE = re.compile(r'W\(li\("[^"]*\bcost\b[^"]*\d', re.I)


def _prev_version(version):
    try:
        from patch.meta import RELEASE_HISTORY
    except ImportError:
        return None
    order = [r["version"] for r in RELEASE_HISTORY]          # newest first
    return order[order.index(version) + 1] if version in order and order.index(version) + 1 < len(order) else None



_INNATE_NAMES = {}


def _innate_names():
    """display name -> engine slug of every innate (abilities_slim is_innate)."""
    if not _INNATE_NAMES:
        slim = json.load(open(os.path.join(_HERE, "data", "abilities_slim.json"),
                              encoding="utf-8"))
        _INNATE_NAMES.update({v["dname"]: k for k, v in slim.items() if v and v.get("is_innate") and v.get("dname")})
        _ALL_NAMES.update({v["dname"]: k for k, v in slim.items() if v and v.get("dname")})
        # removed abilities are gone from abilities_slim but their tooltip name stays in the game's text
        loc = os.path.join(_HERE, "data", "abilities_english.txt")
        if os.path.exists(loc):
            for slug, name in re.findall(r'"DOTA_Tooltip_ability_([a-z0-9_]+)"\s+"([^"]+)"',
                                         open(loc, encoding="utf-8", errors="replace").read()):
                _ALL_NAMES.setdefault(name, slug)
    return _INNATE_NAMES


_ALL_NAMES = {}                  # any ability: a REMOVED innate is often no longer flagged is_innate
_EVER_IDS = set()


def _removed_innate_slug(hero_display, name):
    """Slug of an innate that is gone from today's data (Barracuda 7.40): <hero npc>_<snake name>, if some
    snapshot's ability_ids.json ever had it."""
    if not _EVER_IDS:
        import glob
        for f in glob.glob(os.path.join(_HERE, "data", "stats", "*", "ability_ids.json")):
            _EVER_IDS.update(json.load(open(f, encoding="utf-8")).values())
    from patch.images import HERO_SLUG
    npc = HERO_SLUG.get(hero_display, "")
    cand = f"{npc}_{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}"
    return cand if npc and cand in _EVER_IDS else None


_INNATE_ROW_RE = re.compile(r'^(\s*)W\(li\("([^":]{3,40}): (.*)$')
_INNATE_REMOVED_RE = re.compile(r'^\s*W\(li\("(?:Removed ([^"]+?) innate ability|([^":]{3,40}): Innate ability removed)')


def _postprocess_innate_rows_out_of_stats(lines):
    """Valve writes an innate's change in the hero's general notes ("Sticky Fingers: ...", "Removed Gift
    Bearer innate ability"); Sloppy puts it in the innate's own block after the stats ul (owner 2026-09-26,
    rule "innate + facet changes go under Abilities"). A plain change -> ability(<name>, innate=True) block;
    a removal -> the same block plus a TODO to render it as ability_change(old=<removed>, new=<the hero's new
    innate>) with the OLD description lifted from the previous patch's abilities_english (patch/loc_history.py) (never
    invented)."""
    names = _innate_names()
    out, i = [], 0
    while i < len(lines):
        out.append(lines[i])
        if not lines[i].lstrip().startswith("W(hero_header(") or i + 1 >= len(lines) \
                or lines[i + 1].strip() != "W(ul_open())":
            i += 1
            continue
        j = i + 2
        while j < len(lines) and lines[j].strip() != "W(ul_close())":
            j += 1
        keep, moved = [], []
        hero = re.search(r'hero_header\("([^"]+)"', lines[i]).group(1)
        for ln in lines[i + 2:j]:
            m = _INNATE_ROW_RE.match(ln)
            r = _INNATE_REMOVED_RE.match(ln)
            name = (r and (r.group(1) or r.group(2))) or (m and m.group(2) in names and m.group(2))
            slug = name and (names.get(name) or (r and (_ALL_NAMES.get(name) or _removed_innate_slug(hero, name))))
            if slug:
                moved.append((name, ln, bool(r), slug))
            else:
                keep.append(ln)
        if not moved:
            i += 1
            continue
        ind = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        if keep:
            out += [lines[i + 1]] + keep + [lines[j]]
        for name, ln, removed, slug in moved:
            if removed:
                out.append(f"{ind}# TODO[innate-swap]: ability_change(old={name!r} desc from patch/loc_history.py "
                           f"before this patch, new=<the hero's new innate>) — never invent the old text")
            out.append(f'{ind}W(ability("{name}", slug="{slug}", innate=True))')
            out += [f"{ind}W(ul_open())", ln.replace(f'W(li("{name}: ', 'W(li("', 1), f"{ind}W(ul_close())"]
        i = j + 1
    return out


def _postprocess_unstated_total_cost(lines):
    """An item with a components panel whose total cost changed in the game files, but the patch
    notes say nothing about the price (Revenant's Brooch 7.38: 4900 -> 3300), gets its own row
    "Total cost decreased from A to B" with a note that it comes from the game files (owner,
    2026-09-25). Works on generator output and on indented content/p*.py lines alike."""
    out = []
    i = 0
    while i < len(lines):
        m = _AUTO_COMP_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        ind, name, ver = m.groups()
        j = i + 1
        while j < len(lines) and not _ENTITY_HEAD_RE.match(lines[j]):
            j += 1
        block = lines[i:j]
        # no look-ahead to a later snapshot: the stale items.json copies it covered are fixed at the
        # root (tools/resync_snapshots.py, 2026-09-27); it would put a later patch's price here
        old, new = _kv_item_cost(name, _prev_version(ver) or ""), _kv_item_cost(name, ver)
        if not (old and new and old != new) or any(_COST_ROW_RE.search(x) for x in block):
            out.extend(block)
            i = j
            continue
        verb = "increased" if new > old else "decreased"
        # no "Read from the item's components" note (owner 2026-09-27: remove it everywhere)
        row = f'{ind}W(li("Total cost {verb} from {old} to {new}", b({old}, {new}, l=True)))'
        k = next((n for n, x in enumerate(block) if x.strip() == "W(ul_open())"), None)
        if k is not None:
            block = block[:k + 1] + [row] + block[k + 1:]
        else:
            tail = 0 if block[-1].strip() else 1        # keep a trailing blank line after the block
            cut = len(block) - (1 - tail) if not block[-1].strip() else len(block)
            block = block[:cut] + [f"{ind}W(ul_open())", row, f"{ind}W(ul_close())"] + block[cut:]
        out.extend(block)
        i = j
    return out


def _postprocess_new_item_card(lines, version=None):
    """A NEW item is a card, not a change list (docs/agent-rules/patch-tags.md "Новый предмет"):
    header with label and price on the icon (or components under it) -> bonuses (provides box; none -> no box)
    -> Passive:/Active: ability rows and other notes, all t("NEW")."""
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not (re.match(r'^W\(item_header\("[^"]+", new="(?:New|Returning) ', ln) and i + 1 < len(lines)
                and lines[i + 1] == 'W(ul_open())'):
            out.append(ln)
            i += 1
            continue
        j = i + 2
        body = []
        while j < len(lines) and lines[j] != 'W(ul_close())':
            body.append(lines[j])
            j += 1
        price, bonus, rows, cost, source = [], [], [], None, None
        for b_ in body:
            raw = re.match(r'^W\(li\("((?:[^"\\]|\\.)*)"', b_)
            note = re.search(r'extra=inline_note\("((?:[^"\\]|\\.)*)"\)', b_)
            piece = _new_item_card_parts(raw.group(1), note.group(1) if note else None) if raw else None
            if piece is None and raw and _ABILITY_COSTS_ROW_RE.match(raw.group(1)) and rows \
                    and _li_text(rows[-1]).startswith('Active: '):
                # "Global Cast Range. No Mana Cost. No cooldown" under "Use: …" (7.42 Greater Horn of Battle): the
                # ability's own numbers go to its card header, so into its row, not a row of their own
                prev = _li_text(rows[-1])
                rows[-1] = rows[-1].replace(f'"{prev}"', f'"{prev.rstrip(".")}. {raw.group(1)}"', 1)
                continue
            if piece is None:
                b_ = re.sub(r'^(\s*)W\(li\("Use: ', r'\1W(li("Active: ', b_)     # "Use: Grand Call to Arms." = its active
                row = re.sub(r't\("(?:MISC|BUFF|NERF|REWORK)"\)', 't("NEW")', b_, count=1)
                if raw and not re.search(r', (?:t|b|bf|br)\(', row):
                    # a row with no tag at all ("Passive: Hallowed. …", extra=…): NEW too (audit 2026-10-16:
                    # 42 such rows in 7.38-7.41 had none — the filter missed them)
                    row = row[:raw.end()] + ', t("NEW")' + row[raw.end():]
                rows.append(row)
            elif piece and 'provides(' in piece[0]:
                bonus += piece
            elif piece and piece[0].startswith('cost='):
                cost = piece[0][len('cost='):]
            elif piece and piece[0].startswith('source='):
                source = piece[0][len('source='):]
            else:
                price += piece
        if not price and not cost and 'Artifact' not in ln and 'Enchantment' not in ln:
            name = re.match(r'^W\(item_header\("([^"]+)"', ln).group(1)
            cost = _kv_item_cost(name, version) if version else None
        ln = _with_item_kind(ln, version)
        if cost:
            ln = f'{ln.rstrip()[:-2]}, cost={cost}))'
        if source:
            ln = f'{ln.rstrip()[:-2]}, source={source}))'
        out += [ln] + price + bonus
        if rows:
            out += ['W(ul_open())'] + rows + ['W(ul_close())']
        i = j + 1
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


_SHORTHAND_ROW_RE = re.compile(
    r'^(?P<ind>\s*)W\(li\("(?P<kind>Active|Passive|Toggle|Aura|Use): (?P<name>[^."]+)\. '
    r'(?P<short>(?:Identical to|Same as|Stronger version of|Weaker version of)[^"]*)"(?P<rest>.*)\)\)\s*$')


def _postprocess_shorthand_ability(lines, version=None):
    """"Active: Force. Identical to Force Staff's active" / "Active: Meteor Hammer. Stronger version of basic Meteor
    Hammer" (7.42 Caduceus, Starforge — Valve's own words): the row gets the ability's full text from the game's
    tooltip, Valve's short phrase goes first in its (?) (owner 2026-11-19: "не ленись писать всё. Если в игре написано
    подробно, то и мы пишем так"), as 7.42 Skypiercer's Disarm. No tooltip found: the row stays as it is."""
    try:
        from patch.item_ability_text import item_abilities
    except ImportError:
        return lines
    out, item = [], None
    for ln in lines:
        h = re.match(r'^\s*W\(item_header\("([^"]+)"', ln)
        if h:
            item = h.group(1)
        m = _SHORTHAND_ROW_RE.match(ln)
        if m and item and version:
            slug = _KNOWN_ITEM_SLUGS.get(item, item.lower().replace(' ', '_').replace("'", ''))
            full = next((t for t in (item_abilities(slug, version) or [])
                         if t.startswith(f'{m.group("kind")}: {m.group("name")}.')), None)
            if full:
                short = m.group("short").rstrip(".")
                rest = m.group("rest")
                note = re.search(r'extra=inline_note\("((?:[^"\\]|\\.)*)"\)', rest)
                if note:
                    rest = rest.replace(note.group(0), f'extra=inline_note("{short}<br>{note.group(1)}")', 1)
                else:
                    rest += f', extra=inline_note("{short}")'
                ln = f'{m.group("ind")}W(li({_py_str_item(full.rstrip("."))}{rest}))'
        out.append(ln)
    return out


_DUE_TO_ROW_RE = re.compile(r'^(?P<ind>\s*)W\(li\("(?P<text>Total cost (?:increased|decreased) from \d+g? to \d+g?) '
                            r'\((?P<why>[Dd]ue to[^"]*)\)"(?P<rest>, b\([^)]*\))\)\)\s*$')


def _postprocess_due_to_note(lines):
    """"Total cost decreased from 4200g to 4000g (due to... Kaya and Sange cost decrease. Individually)": the why goes
    under the row's (?), as "Total cost unchanged at 2575g (due to Pavise cost decrease)" does (owner 2026-11-19, 7.42:
    "под [?] мб надо")."""
    out = []
    for ln in lines:
        m = _DUE_TO_ROW_RE.match(ln)
        if m:
            why = m.group("why")
            ln = (f'{m.group("ind")}W(li("{m.group("text")}"{m.group("rest")}, '
                  f'extra=inline_note("{why[:1].upper() + why[1:]}")))')
        out.append(ln)
    return out


_RESULT_NOTE_RE = re.compile(r', extra=inline_note\("(?P<note>As a result, for (?P<what>\w+)[^"]*)"\)')


def _postprocess_result_note_to_its_row(lines):
    """"As a result, for buildings impact damage increased from 90 to 112.5 …" under a number row goes to the row of the
    same item that says what changed for buildings ("now deals 75% … to buildings"), under its (?) (owner 2026-11-19,
    7.42 Meteor Hammer: "спрятать под [?] внутри как раз этой строки")."""
    out = list(lines)
    for i, ln in enumerate(out):
        m = _RESULT_NOTE_RE.search(ln)
        if not m:
            continue
        what = m.group("what").lower()
        j = i - 1
        while j >= 0 and not re.match(r'\s*W\((?:item_header|hero_header|section)\(', out[j]):
            row = re.match(r'\s*W\(li\("((?:[^"\\]|\\.)*)"', out[j])
            if row and f"to {what}" in row.group(1).lower() and "extra=" not in out[j]:
                out[j] = re.sub(r'\)\)\s*$', f', extra=inline_note("{m.group("note")}")))', out[j])
                out[i] = ln.replace(m.group(0), "", 1)
                break
            j -= 1
    return out
