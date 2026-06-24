"""Build aoe_increase.html — the "AoE Increase" table (Heroes sub-tab).

One row per hero; columns are that hero's abilities whose radii carry the
game flag ``affected_by_aoe_increase "1"`` — i.e. radii that grow when the
hero holds an AoE-bonus item. Each ability cell shows its icon plus one line
per affected radius: ``<base> > <increased>``, where the increase is computed
live from the item filter selected at the top.

Item filter (verified from data/stats/<patch>/items.txt):
  * Chasm Stone   — ``aoe_bonus``  +40 flat
  * Shiva's Guard — ``bonus_aoe``  +75 flat
  * Gleipnir      — ``bonus_aoe``  +75 flat  (engine slug item_gungir)
  * Dezun Bloodrite (neutral) — ``aoe_pct`` +20% of the ability radius
The three flat items do not stack with each other ("Aoe bonuses from multiple
Chasm Stones or its upgrades do not stack"), so the UI treats them as a radio
group; the neutral Dezun Bloodrite stacks on top as a separate toggle.

The radius KV ``value`` block is also scanned for upgrade siblings so the line
can be tinted: ``special_bonus_scepter`` (Scepter), ``special_bonus_shard``
(Shard) or any other ``special_bonus_*`` (talent) means the radius value is
tied to that upgrade.

Run AFTER build_patches.py (needs data/site_meta.json):
    python build_site.py stats   # or the whole site
"""
from __future__ import annotations

import html as _html
import json as _json
import re as _re
import sys as _sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_sys.path.insert(0, str(_HERE))
_sys.path.insert(0, str(_HERE / "builders"))

import builders.site_common as _site
from mana_items import parse_kv
from heroes_stats import (
    STATS_DIR,
    _versions,
    _load_display_names,
    _display_name,
    _EXCLUDE,
    _latest_href,
)

_esc = lambda s: _html.escape(str(s), quote=True)

# Item filter definitions: (key, label, icon, kind, amount).
# Upgrade toggles: reveal/raise radii gated behind a talent / Scepter / Shard.
# (key, label, icon path). Off by default — gated radii stay hidden until on.
UPGRADE_FILTERS = [
    ("talent",  "Talent",            "icons/misc/talents.svg"),
    ("scepter", "Aghanim's Scepter", "icons/items/ultimate_scepter.png"),
    ("shard",   "Aghanim's Shard",   "icons/items/aghanims_shard.png"),
]

# Abilities whose KV block omits IsGrantedByShard/IsGrantedByScepter even though
# they are shard/scepter replacements in-game. Keyed by slug → granted_by value.
KV_GRANTED_OVERRIDE: dict[str, str] = {
    "disruptor_kinetic_fence": "shard",  # replaces Kinetic Field; KV lacks IsGrantedByShard
}

# Sub-abilities folded into their parent that DON'T share a slug prefix.
# Slug → canonical slug.
MANUAL_CANON = {
    "phoenix_launch_fire_spirit": "phoenix_fire_spirits",
    # Largo's three song forms are sub-abilities of Amphibian Rhapsody; all share
    # the same radius so they fold into one cell.
    "largo_song_fight_song":       "largo_amphibian_rhapsody",
    "largo_song_double_time":      "largo_amphibian_rhapsody",
    "largo_song_good_vibrations":  "largo_amphibian_rhapsody",
}

# Radii that exist in KV but are no longer active (removed facets / aspects).
# Set of (ability_slug, radius_key).
EXCLUDE_RADII = {
    ("bounty_hunter_shuriken_toss", "passthrough_width"),
    # Open Wounds targets a single unit; spread_radius is a secondary mechanic
    # radius (other heroes "spread" the debuff), not the ability's own AoE.
    ("life_stealer_open_wounds", "spread_radius"),
    # Stroke of Fate's vector_reticle_radius is a UI targeting overlay, not AoE.
    ("grimstroke_dark_artistry", "vector_reticle_radius"),
    # Abyssal Horde summons use search_radius for pathfinding, not spell AoE.
    ("abyssal_underlord_abyssal_horde", "underling_search_radius"),
    # Mana Void thirst_range is a passive attack-range modifier (base 0), not AoE.
    ("antimage_mana_void", "thirst_range"),
    # Nether Ward's self_restoration_range is a heal aura, not a spell AoE.
    ("pugna_nether_ward", "self_restoration_range"),
    # Kill-steal ranges (steal on kill), not the ability's damaging AoE.
    ("silencer_last_word", "permanent_int_steal_range"),
    ("muerta_pierce_the_veil", "spell_amp_steal_range"),
    # Remnant watch distance is the trigger detection line, not the AoE.
    ("void_spirit_aether_remnant", "remnant_watch_distance"),
    # Chakram break_distance is a linear leash, not a radial AoE.
    ("shredder_chakram", "break_distance"),
    ("shredder_return_chakram", "break_distance"),
    # Static Field thresholds are attack-range modifiers (base 0), not AoE.
    ("zuus_static_field", "distance_threshold_min"),
    ("zuus_static_field", "distance_threshold_max"),
    # Torrent max_distance is a cast-range cap, not a radius of effect.
    ("kunkka_torrent_storm", "torrent_max_distance"),
}

# AoE-bonus item filters. The bonus amount is read live from items.txt (key
# below) so a balance change updates the page automatically; the number here is
# only a fallback if the parse fails.
#   (filter_key, label, icon, item_id, value_key, kind, fallback_amount)
ITEM_DEFS = [
    ("chasm_stone",  "Chasm Stone",     "chasm_stone.png",    "item_chasm_stone",    "aoe_bonus", "flat", 40),
    ("shivas_guard", "Shiva's Guard",   "shivas_guard.png",   "item_shivas_guard",   "bonus_aoe", "flat", 75),
    ("gungir",       "Gleipnir",        "gungir.png",         "item_gungir",         "bonus_aoe", "flat", 75),
    ("dezun",        "Dezun Bloodrite", "dezun_bloodrite.png", "item_dezun_bloodrite", "aoe_pct",  "pct",  20),
]


def _resolve_items(version: str) -> list[tuple]:
    """Build the item filter list with bonus amounts read from items.txt so the
    page tracks balance changes. Returns (key, label, icon, kind, amount)."""
    amounts: dict[str, float] = {}
    path = STATS_DIR / version / "items.txt"
    if path.exists():
        try:
            root = parse_kv(_strip_backslash_lines(
                path.read_text(encoding="utf-8", errors="replace"))).get("DOTAAbilities", {})
            for _k, _l, _i, item_id, vkey, _kind, _fb in ITEM_DEFS:
                block = root.get(item_id, {})
                av = block.get("AbilityValues", {}) if isinstance(block, dict) else {}
                node = av.get(vkey)
                if isinstance(node, dict):
                    node = node.get("value")
                if node is not None:
                    vals = _level_values(node)
                    if vals:
                        amounts[item_id] = vals[0]
        except Exception:
            pass
    out = []
    for key, label, icon, item_id, _vkey, kind, fb in ITEM_DEFS:
        amt = amounts.get(item_id, fb)
        out.append((key, label, icon, kind, int(round(amt))))
    return out


def _is_junk_key(key: str) -> bool:
    """True for keys that carry non-AoE values even though they have
    affected_by_aoe_increase "1": vision/sight ranges, AI search radii,
    knockback/push distances."""
    words = set(key.split("_"))
    # Vision and sight ranges are detection/Ward vision, not spell AoE.
    if words & {"vision", "sight"}:
        return True
    # *_search_radius = AI search range, not the ability's effect radius.
    if "search" in words and "radius" in words:
        return True
    # Linear knockback / push distances — not radial AoE.
    if "knockback" in words:
        return True
    if "push" in words and "distance" in words:
        return True
    # Distortion Field's slow_distance_max is a line length, not a radius.
    if words >= {"slow", "distance"}:
        return True
    # Keys with "tooltip" are display-only duplicates of a real radius key.
    if "tooltip" in words:
        return True
    return False


def _humanize(key: str) -> str:
    """radius / explosion_radius / proximity_bonus_radius → readable label."""
    words = key.replace("_", " ").strip()
    if not words:
        return "Radius"
    return words[0].upper() + words[1:]


def _load_ability_names() -> dict[str, str]:
    """engine ability slug → display name from abilities_slim.json."""
    try:
        data = _json.loads((_HERE / "data" / "abilities_slim.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {slug: (info.get("dname") or "") for slug, info in data.items()}


def _strip_backslash_lines(text: str) -> str:
    """Hero KV files carry raw ``\\ Ability: ...`` comment lines between the
    //==== fences. The minimal KV tokenizer treats the backslash + words as
    stray tokens and desyncs the parse, so drop those lines first."""
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("\\"):
            continue
        out.append(line)
    return "\n".join(out)


def _level_values(raw: str) -> list[float]:
    nums = []
    for tok in str(raw).replace("+", " ").split():
        try:
            nums.append(float(tok))
        except ValueError:
            pass
    return nums


def _strip_leading_zeros(vals: list[float]) -> list[float]:
    """Drop leading zero levels when later levels are non-zero (e.g. Dragon
    Knight Dragon Form splash radius 0/275/275/350 → 275/275/350)."""
    first_nonzero = next((i for i, v in enumerate(vals) if v != 0), len(vals))
    if first_nonzero > 0 and first_nonzero < len(vals):
        return vals[first_nonzero:]
    return vals


def _base_display(vals: list[float]) -> str:
    if not vals:
        return ""
    shown = _strip_leading_zeros(vals)
    ints = [int(round(v)) for v in shown]
    if len(set(ints)) == 1:
        return str(ints[0])
    return "/".join(str(i) for i in ints)


def _delta_for(raw) -> tuple[list[float], bool]:
    """Parse a special_bonus value. Returns (values, is_override).
    '+350' / '-1' → delta added to the base; '=800' → override that REPLACES
    the base when the upgrade is on."""
    s = str(raw).strip()
    override = s.startswith("=")
    if override:
        s = s[1:]
    out = []
    for tok in s.split():
        try:
            out.append(float(tok.replace("+", "")))
        except ValueError:
            pass
    return out, override


def _apply_delta(base: list[float], delta: list[float]) -> list[float]:
    if not delta:
        return base
    if len(delta) == 1:
        return [b + delta[0] for b in base]
    if len(delta) == len(base):
        return [b + d for b, d in zip(base, delta)]
    return base


def _sum_levels(a: list[float], b: list[float]) -> list[float]:
    """Add two per-level delta lists (broadcasting a single value)."""
    if not a:
        return b
    if not b:
        return a
    if len(b) == 1:
        return [x + b[0] for x in a]
    if len(a) == 1:
        return [a[0] + x for x in b]
    n = max(len(a), len(b))
    a = a + [a[-1]] * (n - len(a))
    b = b + [b[-1]] * (n - len(b))
    return [x + y for x, y in zip(a, b)]


def _find_aoe_radii(block: dict) -> list[dict]:
    """Walk an ability block; return every sub-block flagged
    affected_by_aoe_increase, in document order. Each entry keeps the RAW base
    value plus the per-upgrade deltas separately, so the page can apply
    Talent / Scepter / Shard only when their filter is on:
        {key, base (level floats), talent, scepter, shard (delta level floats)}.

    A radius gated behind an upgrade (e.g. Mist Coil's effect_radius = 0 +
    special_bonus_unique_abaddon_4 +350) keeps base 0 and a talent delta of
    350; it stays hidden until the Talent filter is enabled."""
    found: list[dict] = []

    def walk(d: dict):
        for k, v in d.items():
            if not isinstance(v, dict):
                continue
            if str(v.get("affected_by_aoe_increase", "")).strip() == "1":
                vals = _level_values(v.get("value", ""))
                if not vals:
                    # No baseline value — keep the entry as base 0 so any
                    # special_bonus override ("=N") still feeds through.
                    vals = [0.0]
                # Per upgrade we track BOTH an additive delta and an absolute
                # override (last `=N` wins). The renderer applies whichever
                # exists when the upgrade toggle is on.
                row = {"key": k, "base": vals,
                       "talent": [], "scepter": [], "shard": [],
                       "talent_set": [], "scepter_set": [], "shard_set": []}
                for mk, mv in v.items():
                    if not mk.startswith("special_bonus_"):
                        continue
                    delta, is_override = _delta_for(mv)
                    if mk == "special_bonus_scepter":
                        bucket = "scepter"
                    elif mk == "special_bonus_shard":
                        bucket = "shard"
                    else:
                        bucket = "talent"
                    if is_override:
                        row[bucket + "_set"] = delta
                    else:
                        row[bucket] = _sum_levels(row[bucket], delta)
                found.append(row)
            else:
                walk(v)

    walk(block)
    return found


def _load_hero_kits(version: str) -> dict[str, set[str]]:
    """hero slug → set of ability slugs in its CURRENT kit, from npc_heroes.txt.
    Deprecated ability blocks linger in the per-hero KV files (e.g. Chaos
    Knight still ships Phantasmagoria though his innate is now Fundamental
    Forging), so the kit list is the authority on what to show."""
    path = STATS_DIR / version / "npc_heroes.txt"
    if not path.exists():
        return {}
    text = _strip_backslash_lines(path.read_text(encoding="utf-8", errors="replace"))
    try:
        root = parse_kv(text).get("DOTAHeroes", {})
    except Exception:
        return {}
    kits: dict[str, set[str]] = {}

    def collect(d: dict, out: set[str]):
        for k, val in d.items():
            if isinstance(val, dict):
                collect(val, out)
            elif _re.fullmatch(r"Ability\d+", k):
                s = str(val).strip()
                if s and s != "generic_hidden" and not s.startswith("special_bonus_"):
                    out.add(s)

    for hero, block in root.items():
        if hero.startswith("npc_dota_hero_") and isinstance(block, dict):
            acc: set[str] = set()
            collect(block, acc)
            kits[hero.replace("npc_dota_hero_", "")] = acc
    return kits


def _dedupe_abilities(abilities: list[dict]) -> list[dict]:
    """Collapse sub-ability variants into their base ability. A slug that
    extends another with an underscore suffix is the same ability cast a second
    way — Alchemist's unstable_concoction + _throw, Invoker's *_ad spell
    variants, Elder Titan's *_spirit echoes. Each is folded into the shortest
    slug it extends; radii merge and de-dupe by (key, base, mod); the icon
    prefers a slug whose PNG exists on disk."""
    slugs = [ab["slug"] for ab in abilities]

    def canonical(s: str) -> str:
        # Explicit folds for sub-abilities that don't share a slug prefix with
        # their parent (e.g. Phoenix's launch-cast is the same Fire Spirits).
        if s in MANUAL_CANON:
            return MANUAL_CANON[s]
        best = s
        for other in slugs:
            if other != s and s.startswith(other + "_") and len(other) < len(best):
                best = other
        return best

    by_canon: dict[str, dict] = {}
    order: list[str] = []
    for ab in abilities:
        c = canonical(ab["slug"])
        if c not in by_canon:
            by_canon[c] = {"slug": ab["slug"], "name": ab["name"], "radii": [],
                           "innate": False, "granted_by": ""}
            order.append(c)
        entry = by_canon[c]
        if ab.get("innate"):
            entry["innate"] = True
        if ab.get("granted_by"):
            entry["granted_by"] = ab["granted_by"]
        # The canonical (base) slug owns the display name + preferred icon.
        if ab["slug"] == c:
            entry["name"] = ab["name"]
            entry["slug"] = ab["slug"]
        elif not (_HERE / "icons" / "abilities" / f'{entry["slug"]}.png').exists() \
                and (_HERE / "icons" / "abilities" / f'{ab["slug"]}.png').exists():
            entry["slug"] = ab["slug"]
        seen = {(r["key"], tuple(r["base"])) for r in entry["radii"]}
        for r in ab["radii"]:
            sig = (r["key"], tuple(r["base"]))
            if sig not in seen:
                seen.add(sig)
                entry["radii"].append(r)
    return [by_canon[c] for c in order]


def _hero_abilities(version: str, hero_slug: str, kit: set[str] | None) -> list[dict]:
    """Return the AoE-affected abilities for one hero, file order. Only
    abilities in the hero's current kit are kept (deprecated KV blocks dropped).
    Each: {slug, name (filled later), radii:[...]}."""
    path = STATS_DIR / version / "heroes" / f"npc_dota_hero_{hero_slug}.txt"
    if not path.exists():
        return []
    text = _strip_backslash_lines(path.read_text(encoding="utf-8", errors="replace"))
    try:
        parsed = parse_kv(text)
    except Exception as exc:
        print(f"  ! parse failed for {hero_slug}: {exc}")
        return []
    root = parsed.get("DOTAAbilities", {})
    abilities = []
    for slug, block in root.items():
        if slug == "Version" or not isinstance(block, dict):
            continue
        if slug.startswith("special_bonus_"):
            continue
        if kit and slug not in kit:
            continue
        radii = _find_aoe_radii(block)
        radii = [r for r in radii if (slug, r["key"]) not in EXCLUDE_RADII
                 and not _is_junk_key(r["key"])]
        if radii:
            granted_by = ""
            if str(block.get("IsGrantedByScepter", "")).strip() == "1":
                granted_by = "scepter"
            elif str(block.get("IsGrantedByShard", "")).strip() == "1":
                granted_by = "shard"
            elif slug in KV_GRANTED_OVERRIDE:
                granted_by = KV_GRANTED_OVERRIDE[slug]
            # Scepter/shard ultimates carry Innate "1" in KV but are not true innates.
            innate = (str(block.get("Innate", "")).strip() == "1" and not granted_by)
            abilities.append({"slug": slug, "radii": radii, "innate": innate,
                              "granted_by": granted_by})
    return abilities


def _item_filter_bar(items: list[tuple]) -> str:
    def _item_btn(key, label, icon, kind, amt):
        sign = f"+{amt}%" if kind == "pct" else f"+{amt}"
        return (
            f'<button type="button" class="hs-attr-filter aoe-item-btn" '
            f'data-aoe-kind="{kind}" data-aoe-amount="{amt}" data-aoe-key="{key}" '
            f'aria-pressed="false" title="{_esc(label)} ({sign} AoE)">'
            f'<img src="icons/items/{icon}" alt="{_esc(label)}" loading="lazy"></button>'
        )

    def _up_btn(key, label, icon):
        return (
            f'<button type="button" class="hs-attr-filter aoe-up-btn" '
            f'data-aoe-upgrade="{key}" aria-pressed="false">'
            f'<img src="{icon}" alt="{_esc(label)}" loading="lazy"></button>'
        )

    # All four items live in ONE group: the three flat items are mutually
    # exclusive (radio), Dezun Bloodrite (pct) stacks on top.
    items_html = "".join(_item_btn(*it) for it in items)
    upgrades_html = "".join(_up_btn(*u) for u in UPGRADE_FILTERS)
    return (
        '<div class="cal-toggle-bar mr-toolbar inbox-bar aoe-toolbar">'
        '<div class="toolbar-panel">'
        '<span class="hs-attr-filter-group aoe-filter-group" '
        'aria-label="AoE bonus item">'
        f'<strong>AoE item</strong>{items_html}</span>'
        '<span class="hs-attr-filter-group aoe-filter-group" '
        'aria-label="Upgrade radii (talent / scepter / shard)">'
        f'<strong>Upgrade</strong>{upgrades_html}</span>'
        '<span class="search-box hd-search">'
        '<input type="text" id="mr-search" autocomplete="off" spellcheck="false" '
        'placeholder="Search heroes — axe, crystal, wisp…">'
        '</span>'
        '</div></div>\n'
    )


def render_html() -> str:
    versions = _versions()
    latest = versions[-1]
    names = _load_display_names()
    abil_names = _load_ability_names()

    # Hero slugs present this patch (heroes.json), alphabetical by display name.
    cur = _json.loads((STATS_DIR / latest / "heroes.json").read_text(encoding="utf-8"))
    heroes = sorted(
        (h for h in cur if h.startswith("npc_dota_hero_") and h not in _EXCLUDE),
        key=lambda h: _display_name(h, names).lower())

    kits = _load_hero_kits(latest)

    rows = []
    max_slots = 1  # at minimum: Innate slot always exists
    for hero in heroes:
        slug = hero.replace("npc_dota_hero_", "")
        abilities = _hero_abilities(latest, slug, kits.get(slug))
        for ab in abilities:
            ab["name"] = abil_names.get(ab["slug"]) or _humanize(
                ab["slug"].replace(slug + "_", ""))
        abilities = _dedupe_abilities(abilities)
        abilities = [a for a in abilities if any(
            max(r["base"], default=0) > 0
            or r["talent"] or r["scepter"] or r["shard"]
            or r["talent_set"] or r["scepter_set"] or r["shard_set"]
            for r in a["radii"])]
        # Slot #0 reserved for INNATE; heroes with no AoE abilities still get a row
        # (all cells will be empty dashes).
        innate = next((a for a in abilities if a.get("innate")), None)
        rest = [a for a in abilities if a is not innate]
        ordered: list[dict | None] = [innate] + rest
        max_slots = max(max_slots, len(ordered))
        rows.append((hero, slug, ordered))

    # ---- header ---- (Hero column is the only sortable one)
    head = ['<th class="mr-th hs-th hs-name aoe-name sortable" data-col="name">'
            '<span class="th-label">Hero</span><span class="sort-ind"></span></th>']
    for i in range(max_slots):
        # Slot 0 = Innate; everything after restarts at #1.
        label = "Innate" if i == 0 else f"#{i}"
        head.append(f'<th class="mr-th aoe-slot-th">{label}</th>')
    thead = "".join(head)

    innate_fallback = "this.onerror=null;this.src='icons/misc/innate_icon.png'"

    # ---- body ----
    body = []
    for hero, slug, abilities in rows:
        name = _display_name(hero, names)
        icon = (f'<img class="mr-ico hs-ico" src="icons/heroes/{slug}.png" '
                f'alt="" loading="lazy" width="256" height="144">'
                if (_HERE / "icons" / "heroes" / f"{slug}.png").exists()
                else '<span class="mr-ico mr-ico-blank"></span>')
        cells = [
            f'<td class="mr-name hs-name aoe-name" data-sort="{_esc(name)}">'
            f'{icon}<span class="mr-name-body">'
            f'<span class="mr-name-text">{_esc(name)}</span></span></td>'
        ]
        for i in range(max_slots):
            ab = abilities[i] if i < len(abilities) else None
            if ab is None:
                cells.append('<td class="aoe-cell aoe-cell-empty">'
                             '<span class="ua-dash">—</span></td>')
                continue
            # Drop radii that have no base, no delta, no override across every
            # upgrade — they'd render as a stuck-zero phantom row (e.g. Mana
            # Void's secondary aoe_radius keyed off base 0 with nothing else).
            ab = {**ab, "radii": [
                r for r in ab["radii"]
                if max(r["base"], default=0) > 0
                or r["talent"] or r["scepter"] or r["shard"]
                or r["talent_set"] or r["scepter_set"] or r["shard_set"]
            ]}
            if not ab["radii"]:
                cells.append('<td class="aoe-cell aoe-cell-empty">'
                             '<span class="ua-dash">—</span></td>')
                continue
            has = {u: any(r[u] or r[u + "_set"] for r in ab["radii"])
                   for u in ("talent", "scepter", "shard")}
            # Abilities fully granted by an upgrade always carry its mark even
            # when the radius itself doesn't change with that upgrade.
            if ab.get("granted_by") in has:
                has[ab["granted_by"]] = True
            # Ability icon (innate-marker fallback for CDN-less innates) wrapped
            # so upgrade mini-markers can pin to its bottom-centre, like the
            # innate markers on /patches/. Name shows via the hover title; the
            # icon pops on hover exactly like a hero icon.
            marks = "".join(
                f'<img class="aoe-mark aoe-mark-{u[0]}" src="{u[2]}" alt="" hidden>'
                for u in UPGRADE_FILTERS if has[u[0]])
            # Innate marker — but only if the ability has its OWN icon. When the
            # ability has no PNG, the onerror handler already shows the generic
            # innate icon, so a mini-marker on top would just duplicate it.
            has_own_icon = (_HERE / "icons" / "abilities" / f'{ab["slug"]}.png').exists()
            if ab.get("innate") and has_own_icon:
                marks += ('<img class="aoe-mark aoe-mark-innate" '
                          'src="icons/misc/innate_icon.png" alt="" title="Innate">')
            ab_icon = (
                f'<span class="aoe-ico-wrap">'
                f'<img class="aoe-ico" src="icons/abilities/{ab["slug"]}.png" '
                f'alt="" loading="lazy" width="32" height="32" '
                f'title="{_esc(ab["name"])}" onerror="{innate_fallback}">'
                f'<span class="aoe-marks" aria-hidden="true">{marks}</span>'
                f'</span>')

            def _attr(vals):
                return " ".join(str(round(v, 2)) for v in vals)

            def _val_span(r):
                return (
                    f'<span class="aoe-val"'
                    f' data-base="{_attr(r["base"])}"'
                    f' data-talent="{_attr(r["talent"])}"'
                    f' data-scepter="{_attr(r["scepter"])}"'
                    f' data-shard="{_attr(r["shard"])}"'
                    f' data-talent-set="{_attr(r["talent_set"])}"'
                    f' data-scepter-set="{_attr(r["scepter_set"])}"'
                    f' data-shard-set="{_attr(r["shard_set"])}">'
                    f'{_base_display(r["base"])}</span>')

            def _line(inner, label=""):
                lbl = (f'<span class="aoe-sep">-</span>'
                       f'<span class="aoe-lbl">{_esc(label)}</span>') if label else ""
                return f'<div class="aoe-line">{inner}{lbl}</div>'

            # Strip the ability's own slug words from a radius-key label
            # ("mana_void_aoe_radius" on Mana Void → "Aoe radius") and drop
            # filler words so the label is just the distinguishing part.
            ab_short = ab["slug"]
            if hero.startswith("npc_dota_hero_"):
                # ability slugs are "hero_*"; strip the hero prefix so we keep
                # the ability noun for stripping (e.g. "mana_void").
                pass
            slug_words = set(ab_short.split("_"))
            slug_words.discard("")

            def _clean_label(key: str) -> str:
                parts = [w for w in key.split("_") if w and w not in slug_words]
                # Generic AoE-description words add no info ("area of effect" = radius).
                filler = {"aoe", "area", "of", "effect"}
                parts = [w for w in parts if w not in filler]
                if not parts:
                    return ""
                txt = " ".join(parts).strip()
                return txt[:1].upper() + txt[1:] if txt else ""

            # Auto-merge opposed-pair radii (start/end, min/max, near/far,
            # inner/outer) onto a single "X/Y - <left>/<right> radius" line.
            PAIRS = [("start", "end"), ("min", "max"),
                     ("near", "far"), ("inner", "outer")]

            def _pair_words(key: str) -> tuple[str, set[str]] | None:
                """If the key contains exactly one pair-word, return
                (pair_word, remaining_words_set) so two keys can match by
                having the same remaining-words and complementary pair-words."""
                words = key.split("_")
                for L, R in PAIRS:
                    for w in (L, R):
                        if w in words:
                            rest = set(words)
                            rest.discard(w)
                            return (w, frozenset(rest), (L, R))
                return None

            radii = ab["radii"]
            handled: set[int] = set()
            pair_lines: list[tuple[int, str]] = []
            for i_a, ra in enumerate(radii):
                if i_a in handled:
                    continue
                pa = _pair_words(ra["key"])
                if not pa:
                    continue
                wa, rest_a, (L, R) = pa
                opposite = R if wa == L else L
                for i_b in range(i_a + 1, len(radii)):
                    if i_b in handled:
                        continue
                    pb = _pair_words(radii[i_b]["key"])
                    if not pb:
                        continue
                    wb, rest_b, _ = pb
                    if wb == opposite and rest_a == rest_b:
                        left, right = (ra, radii[i_b]) if wa == L else (radii[i_b], ra)
                        rest_words = [w for w in ra["key"].split("_")
                                      if w not in (L, R) and w not in slug_words and w != "aoe"]
                        label_tail = " ".join(rest_words).strip() or "radius"
                        lines_html = (
                            f'{_val_span(left)}<span class="aoe-slash">/</span>'
                            f'{_val_span(right)}')
                        merged_label = f"{L}/{R} {label_tail}".strip()
                        pair_lines.append((i_a, _line(lines_html, merged_label)))
                        handled.update({i_a, i_b})
                        break

            kept = [(i, r) for i, r in enumerate(radii) if i not in handled]
            multi = (len(kept) + len(pair_lines)) > 1
            lines = []
            # Emit lines in their original radius-order, interleaving merged
            # pair lines at the position of their first member.
            merged_map = dict(pair_lines)
            for i, r in enumerate(radii):
                if i in merged_map:
                    lines.append(merged_map[i])
                elif i not in handled:
                    lbl = _clean_label(r["key"])
                    # Always show label when it carries real context (not just
                    # generic "Radius"). For multi-radius cells labels are always
                    # shown so values can be told apart.
                    label = lbl if (multi or lbl.lower() not in {"", "radius", "area of effect", "scepter radius", "shard radius", "talent radius"}) else ""
                    lines.append(_line(_val_span(r), label))
            granted_by = ab.get("granted_by", "")
            data_has = (f' data-has-talent="{1 if has["talent"] else 0}"'
                        f' data-has-scepter="{1 if has["scepter"] else 0}"'
                        f' data-has-shard="{1 if has["shard"] else 0}"'
                        + (f' data-granted-by="{granted_by}"' if granted_by else ''))
            cells.append(
                f'<td class="aoe-cell">'
                f'<div class="aoe-ability"{data_has}>'
                f'{ab_icon}'
                f'<div class="aoe-radii">{"".join(lines)}</div>'
                f'</div></td>')
        body.append(
            f'<tr data-slug="{slug}" data-name="{_esc(name.lower())}">'
            f'{"".join(cells)}</tr>')

    table = (
        '<table class="mr-table hs-table aoe-table sortable-table">'
        f'<thead><tr class="col-row">{thead}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody>'
        '</table>'
    )

    blurb = (
        '<p class="mr-blurb inbox-bar">Every ability radius the game flags '
        '<code>affected_by_aoe_increase</code> — the radii that grow with an '
        'AoE-bonus item. Pick an <strong>AoE item</strong> and the numbers update '
        'in place: the three flat items don\'t stack with each other (one choice), '
        'and <em>Dezun Bloodrite</em> adds +20% of the boosted radius on top. '
        'The <strong>Upgrade</strong> toggles reveal radii that only exist with a '
        'talent / Scepter / Shard (e.g. Mist Coil 0 → 350 with its talent); when '
        'one changes an ability, that upgrade\'s mini-icon appears under the '
        'ability icon.</p>\n'
    )

    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active='aoe_increase',
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav('aoe_increase')
    asset_version = _site.compute_asset_version()

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<title>SIKLE | AoE Increase</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={asset_version}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page">\n'
        '<div class="sticky-frame hs-sticky-frame"></div>\n'
        '<div class="creeps-scroll">\n'
        f'{subnav}'
        f'{blurb}'
        f'{_item_filter_bar(_resolve_items(latest))}'
        f'{table}\n'
        '</div>\n'
        '</div>\n'
        f'<script defer src="src/scripts.js?v={asset_version}"></script>\n'
        '</body>\n</html>\n'
    )


def main() -> int:
    html = render_html()
    (_HERE / "dist").mkdir(exist_ok=True)
    out = _HERE / "dist" / "aoe_increase.html"
    out.write_text(html, encoding="utf-8")
    n_rows = html.count("<tr data-slug=")
    print(f"  -> dist/aoe_increase.html: {len(html):,} bytes ({n_rows} heroes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
