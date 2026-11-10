"""A hero, an item, a neutral creep as lines of the scaffold."""
import os
import re

from .common import _HERE, _KNOWN_ITEM_SLUGS
from .data import ABILS, ABILS_SLIM, CREEP_ABILS, HEROES, ITEMS, _strip_html
from .general import _entity_title_decoration
from .notes import _emit_notes

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
    # "Item Reworked" over "Now is a Tier 5 Neutral Artifact" (7.38 Pirate Hat, owner 2026-11-05): the header says both,
    # "Reworked Tier 5 Artifact", and the texts nested under it are the new abilities the card shows
    if is_reworked and neutral and notes:
        tier = re.match(r'^Now\s+is\s+a\s+(Tier\s+\d+)\s+Neutral\s+Artifact$', _strip_html(notes[0].get('note', '')).strip(), re.I)
        if tier:
            lvl = notes[0].get('indent_level', 1)
            deco = f', changed="Reworked {tier.group(1)} Artifact"'
            notes = [dict(n, indent_level=max(1, n.get('indent_level', 1) - 1)) if n.get('indent_level', 1) > lvl else n
                     for n in notes[1:]]
    # Detect "New Tier N Artifact" / "Returning as a Tier N Neutral Artifact" as
    # the first note in neutral items — convert to item_header(new="...") and drop.
    # Owner 2026-09-27: "Now is a Tier 1 Neutral Artifact" (7.38, an old neutral item in the new artifact
    # list) is a header too — "Now a Tier 1 Artifact" (not "New": the item existed before) — and its
    # ability description, nested under that note, becomes the item's own row(s), not an inline_note.
    # 7.37 and before: "Returning as a Tier 1 Neutral item", "Now is a Tier 3 Neutral item" (owner 2026-10-30:
    # "Ironwood Tree, Iron Talon … смотри примеры в 7.38") → "Returning Tier 1 Neutral Item"
    _NEW_RET_RE = re.compile(
        r'^(New|Returning(?:\s+as\s+a)|Now\s+is\s+a)\s+Tier\s+\d+\s+(?:Neutral\s+)?(?:Artifact|item)$',
        re.I,
    )
    if neutral and not deco and notes:
        first_txt = _strip_html(notes[0].get('note', '')).strip()
        m = _NEW_RET_RE.match(first_txt)
        if m:
            # Normalise: "Returning as a Tier 2 Neutral Artifact" → "Returning Tier 2 Artifact"
            norm = re.sub(r'^Now\s+is\s+a\b', 'Now a', first_txt, flags=re.I)
            norm = re.sub(r'\s+as\s+a\b', '', norm, flags=re.I)
            norm = re.sub(r'\s+Neutral\b', '', norm, flags=re.I) if re.search(r'Artifact$', norm, re.I) else \
                re.sub(r'\s+Neutral\s+item$', ' Neutral Item', norm, flags=re.I)
            deco = f', new="{norm}"'
            lvl = notes[0].get('indent_level', 1)
            notes = [dict(n, indent_level=max(1, n.get('indent_level', 1) - 1)) if i and n.get('indent_level', 1) > lvl
                     else n for i, n in enumerate(notes)][1:]
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


def _facet_card(slug, style, body_lines, version=None):
    """Valve-flagged facet → card lines, else None. NewFacet → new_facet(desc=rows);
    ReworkedFacet → facet_change with the rows as NEW and an OLD pane: the facet's text of the previous patch with
    its numbers (patch/aghs_text.facet_text, 7.37 Ferocity / Voidblades); a TODO only when the files lack it."""
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
    from patch.aghs_text import facet_text
    from patch.meta import _prev_patch_version
    prev = _prev_patch_version(version) if version else None
    old = facet_text(slug, prev) if prev else None
    old_item = (f'"{old.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"' if old else
                '"TODO: the facet as it was in the previous patch (KV values + earlier notes)"')
    return [f'W(facet_change("{slug}",\n'
            f'    old_desc=[{old_item}],\n'
            f'    new_desc=[{rows}\n]))']


# an innate the patch itself turns into another kind of ability — its KV flag may still say innate (7.41 Feast "Now
# is a basic ability", Minefield Sign "Now only available with Aghanim's Scepter": data/stats/7.41 keeps
# "Innate" "1" on both; the new innates Ghoul Frenzy / M.A.D. come as cards)
INNATE_DEMOTED = re.compile(r"\bNow (?:is )?a (?:basic|regular) ability\b|\bno longer (?:an? )?innate\b"
                            r"|\bnow only available with Aghanim", re.I)
_INNATE_BY_VERSION = {}
_KV_BLOCK_RE = re.compile(r'\n\t"([a-z0-9_]+)"\s*\n\t\{(.*?)\n\t\}', re.S)


def innate_slugs_of(version):
    """Slugs flagged "Innate" "1" in that patch's hero KV (data/stats/<version>/heroes/*.txt); empty when the patch
    has no per-hero files."""
    if version not in _INNATE_BY_VERSION:
        folder = os.path.join(_HERE, "data", "stats", str(version), "heroes")
        found = set()
        if version and os.path.isdir(folder):
            for f in os.listdir(folder):
                text = open(os.path.join(folder, f), encoding="utf-8", errors="replace").read()
                found |= {s for s, body in _KV_BLOCK_RE.findall(text) if re.search(r'"Innate"\s+"1"', body)}
        _INNATE_BY_VERSION[version] = found
    return _INNATE_BY_VERSION[version]


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
                # "Cold Comfort Facet: Blueheart Floe: …" (7.37): Valve's prefix may carry the word "Facet"
                facet_name = re.sub(r'\s+Facet$', '', prefix, flags=re.I) or prefix
                facet_slug = _facet_name_to_slug.get(facet_name.lower())
                if not facet_slug and version:
                    # a facet of this patch the registry lacks (7.37b "Elitist: Exort: …" became an innate block)
                    from patch.ability_kv import hero_facets
                    facet_slug = next((fs for fs, (fname, _c, _i) in hero_facets(slug, version).items()
                                       if fname.lower() == facet_name.lower()), None)
                if facet_slug:
                    stripped_note = dict(n)
                    stripped_note['note'] = re.sub(
                        re.escape(prefix) + r':\s*', '', n.get('note', ''), count=1, flags=re.I
                    )
                    _facet_buckets.setdefault(facet_slug, []).append(stripped_note)
                    continue
                # "Duelist: Bonus damage increased …" (7.37d innate), "Defense Matrix: Cast Range …" (7.37c): the prefix is
                # an ability of the hero in this patch → its own block
                from patch.ability_kv import hero_abilities
                own = hero_abilities(slug, version).get(prefix.lower()) if version else None
                if own:
                    stripped_note = dict(n)
                    stripped_note['note'] = re.sub(
                        re.escape(prefix) + r':\s*', '', n.get('note', ''), count=1, flags=re.I
                    )
                    _abil_buckets.setdefault(
                        own[0], {'name': prefix, 'is_innate': own[1], 'notes': []})['notes'].append(stripped_note)
                    continue
                # Check for "AbilityName: change text" where AbilityName refers to
                # an ability that no longer exists in the current game (renamed or
                # removed in this or a prior patch). If the prefix IS a current
                # ability (found in abilities_slim by dname), it's not a routing
                # signal — fall through to _general_notes.
                if prefix.lower() not in _current_abil_dname_to_slug:
                    # The patch before names it (7.37 "Selemene's Favor: Ability removed" = luna_selemenes_faithful?
                    # the files say which); else derive: hero_slug + "_" + display name words
                    from patch.meta import _prev_patch_version as _pv
                    before = hero_abilities(slug, _pv(version)).get(prefix.lower()) if version and _pv(version) else None
                    derived_slug = before[0] if before else \
                        slug + '_' + re.sub(r"[^a-z0-9]+", '_', prefix.lower()).strip('_')
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
        # Emit "Removed" blocks (one facet_header per removed facet). Just "Removed": the header already names the
        # facet and the Facets group says it is one (owner 2026-10-09: not "Resonance: Facet removed")
        for facet_slug, _dname in _facet_removed:
            out.append(f'W(facet_header("{facet_slug}"))')
            out.append('W(ul_open())')
            out.append('W(li("Removed", t("DEL")))')
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
    facet_talent_rows = []
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
            # talent_notes inside a facet subsection (NP Soothing Saplings 7.39): they go to the hero's Talents with the
            # facet's chip (li(facet=...)) — the talents in one place, the chip says whose (owner 2026-10-27)
            facet_talents = s.get('talent_notes', [])
            if facet_talents:
                tbody, _ = _emit_notes(facet_talents)
                facet_talent_rows.extend(_with_facet(_ul_inner(tbody), facet_slug))
            # Valve flags the facet itself: "hero_facet NewFacet" / "hero_facet ReworkedFacet"
            card = _facet_card(facet_slug, s.get('style', ''), out[facet_start + 1:], version)
            if card:
                out[facet_start:] = card
    # Abilities — the innate first, whatever Valve's order (owner 2026-10-16: Invoke, Feast, Minefield Sign 7.41 stood
    # after the basic abilities). Innate = "Innate" "1" in THAT patch's KV: today's flag can mean another ability
    # (Precision Aura / Vantage Point, Liquid Courage before 7.41d).
    _inn = innate_slugs_of(version)

    def _stays_innate(a):
        return (ABILS.get(a.get('ability_id'), ('', ''))[1] in _inn
                and not any(INNATE_DEMOTED.search(n.get('note', '')) for n in a.get('ability_notes', [])))
    abilities = sorted(hero.get('abilities', []), key=lambda a: not _stays_innate(a))
    for a in abilities:
        aid = a.get('ability_id')
        aname, aslug = ABILS.get(aid, (f'ability_{aid}', f'ability_{aid}'))
        # the patch's own KV flag too: 7.37b Predator and Maul were innates, their slugs say nothing
        innate_kwarg = ', innate=True' if '_innate_' in aslug or _stays_innate(a) else ''
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
    # Talents — always last; the facets' talents after the hero's own, each with its facet's chip
    talents = hero.get('talent_notes', [])
    if talents or facet_talent_rows:
        out.append('W(subgroup("Talents"))')
        body = _emit_notes(talents)[0] if talents else ['W(ul_open())', 'W(ul_close())']
        inner = _ul_inner(body)
        out.extend(['W(ul_open())'] + inner + facet_talent_rows + ['W(ul_close())'])
    return out


def _ul_inner(body):
    """The rows of one emitted ul (its W(ul_open()) / W(ul_close()) lines dropped)."""
    return [ln for ln in body if ln.strip() not in ('W(ul_open())', 'W(ul_close())')]


def _with_facet(rows, facet_slug):
    """A facet's talent rows with facet="<slug>": each li call's last line ("…))") gets the keyword."""
    return [re.sub(r'\)\)\s*$', f', facet="{facet_slug}"))', ln) if ln.rstrip().endswith('))') else ln for ln in rows]


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
    matched = None
    for i, n in enumerate(notes):
        # a nested note goes where its parent went, whatever it names itself ("Mana Burn reworked" > "Now burns 100
        # mana" stood as the unit's own row, its children under other rows — pilot 2026-11-10 on indent levels 3-4);
        # the first note is a parent whatever its level says
        if i == 0 or (n.get('indent_level') or 1) <= 1:
            txt = _strip_html(n.get('note') or '').lower()
            matched = next((a_slug for a_slug, dname in abil_pairs if dname.lower() in txt), None)
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
        # Strip "AbilityName: " from every note — ability() block already shows the name (owner 2026-11-04, 7.38 Petrify)
        stripped = []
        for note in bucket:
            n2 = dict(note)
            txt = n2.get('note', '')
            if txt.lower().startswith(dname.lower() + ': '):
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
