"""build_mana_items.py — Generate mana_items.html: a sortable table of every
purchasable item with a mana / mana-regen contribution, plus derived
gold-efficiency metrics.

Scope (per request):
  • Skip neutrals (ItemPurchasable=0), charms, recipes, consumables, courier
    gear, side-shop fluff.
  • Include Intelligence items — each Int point gives +12 max mana and
    +0.05 mana regen (7.41c engine hardcoded values).
  • For items whose ACTIVE literally restores mana to the caster (Soul Ring,
    Arcane Boots' replenish), amortise the active as equivalent passive
    regen:  equivalent_regen = active_mana_gained / AbilityCooldown.
    Bloodstone in 7.41c has bonus_mp_regen=0 and no active mana_gain — its
    mana economy is via spell-lifesteal, not regen, so the table reflects
    only its Intelligence contribution.
  • Columns (English, per user request): Item, Price, Intelligence, MP,
    MP regen, Cost per 1 MP regen, MP regen per 1 gold, Mana per 60 sec.

Output: mana_items.html under the Materials section's sub-nav.
"""
from __future__ import annotations

import json as _json
import os as _os
import re
import sys as _sys
from pathlib import Path

_HERE = Path(_os.path.dirname(_os.path.abspath(__file__))).parent
_sys.path.insert(0, str(_HERE))

import site_common as _site
ASSET_VERSION = _site.compute_asset_version()

# ── Engine constants ───────────────────────────────────────────────────────
INT_TO_MAX_MANA = 12.0   # +12 max mana per Int point
INT_TO_REGEN    = 0.05   # +0.05 mana regen per Int point

# ── Source data ────────────────────────────────────────────────────────────
ITEMS_TXT = _HERE / "data" / "stats" / "7.41c" / "items.txt"
STATS_ROOT = _HERE / "data" / "stats"

def _load_release_history() -> list[tuple[str, str]]:
    """Parse RELEASE_HISTORY out of build_patch.py via regex (don't import —
    that file runs the whole patch build on import). Falls back to a small
    inline list (newest only) if build_patch.py is unreachable. Returns
    newest-first list of (version, date)."""
    out: list[tuple[str, str]] = []
    bp = _HERE / "builders" / "patch.py"
    if bp.exists():
        src = bp.read_text(encoding="utf-8")
        # Anchor on the RELEASE_HISTORY assignment to avoid duplicating
        # entries from the parallel PATCHES list (which has an extra
        # `filename` key per entry).
        block_m = re.search(
            r'RELEASE_HISTORY\s*=\s*\[(.+?)\n\]', src, re.DOTALL
        )
        if block_m:
            for m in re.finditer(
                r'\{"version":\s*"([^"]+)",\s*"date":\s*"([^"]+)"',
                block_m.group(1),
            ):
                out.append((m.group(1), m.group(2)))
    if out:
        return out
    # Minimum-viable fallback (current cycle only)
    return [("7.41c", "06.05.2026")]


RELEASE_HISTORY = _load_release_history()

# ── Field name variants (Valve isn't consistent across items) ─────────────
PASSIVE_REGEN_FIELDS = (
    "bonus_mana_regen", "mana_regen", "bonus_mp_regen", "mp_regen",
    "aura_mana_regen",  # treated as self-effective (auras include self)
)
# Multiplier on the hero's TOTAL mana regen (Kaya = +30%, Kaya+Sange = +40%,
# Meteor Hammer = +35%, etc). Shown as a small "+X%" chip beside the flat
# regen number — derived columns intentionally ignore it because the
# absolute boost depends on the hero's other mana-regen sources.
MULTIPLIER_FIELD = "mana_regen_multiplier"
MAX_MANA_FIELDS = ("bonus_mana", "max_mana")
INT_FIELDS      = ("bonus_intellect", "bonus_int", "bonus_intelligence")
# Items that grant +X to all stats — Holy Locket, Crellas Crozier, Vladmir's,
# Aeon Disk, etc. The Int portion contributes to mana + regen, so we count
# it as an Int bonus equal to the all-stats value.
ALL_STATS_FIELDS = ("bonus_all_stats",)
ACTIVE_MANA_FIELDS = (
    "mana_gain", "replenish_amount", "mana_restore", "mana_pool",
    "mana_amount",
)

# Slug-prefix exclusions: recipes, consumables, charms, etc.
EXCLUDE_PREFIXES = (
    "item_recipe_",
    "item_consumable_",     # courier-purchase consumables
    "item_courier",
    "item_flying_courier",
    "item_tpscroll",        # TP scroll — not a regen item
    "item_smoke_of_deceit",
    "item_dust",
    "item_ward_",
    "item_sentry",
    # item_clarity is INCLUDED (modelled as an active mana restore — see load_items).
    "item_tango",
    "item_faerie_fire",
    "item_healing_salve",
    "item_enchanted_mango",
    "item_bottle",          # consumable, not relevant for regen
    "item_river_painter",
    "item_present",
    "item_winter_lord",
    "item_greater_clarity",
)

# ── Manual display-name overrides for items where the auto-pretty-print
#    diverges from Valve's canonical in-game name. ─────────────────────────
ITEM_DISPLAY_OVERRIDES = {
    "item_diffusal_blade": "Diffusal Blade",
    "item_eul_scepter": "Eul's Scepter of Divinity",
    "item_lotus_orb": "Lotus Orb",
    "item_orchid": "Orchid Malevolence",
    "item_bloodthorn": "Bloodthorn",
    "item_octarine_core": "Octarine Core",
    "item_aether_lens": "Aether Lens",
    "item_yasha_and_kaya": "Yasha and Kaya",
    "item_kaya_and_sange": "Kaya and Sange",
    "item_holy_locket": "Holy Locket",
    "item_pavise": "Pavise",
    "item_pers": "Perseverance",
    "item_sobi_mask": "Sage's Mask",
    "item_sheepstick": "Scythe of Vyse",
    "item_crellas_crozier": "Crella's Crozier",
    "item_null_talisman": "Null Talisman",
    "item_void_stone": "Void Stone",
    "item_arcane_boots": "Arcane Boots",
    "item_soul_ring": "Soul Ring",
    "item_bloodstone": "Bloodstone",
    "item_falcon_blade": "Falcon Blade",
    "item_arcane_blink": "Arcane Blink",
    "item_holy_locket": "Holy Locket",
    "item_aeon_disk": "Aeon Disk",
    "item_soul_booster": "Soul Booster",
    "item_ring_of_basilius": "Ring of Basilius",
    "item_urn_of_shadows": "Urn of Shadows",
    "item_refresher": "Refresher Orb",
    "item_tiara_of_selemene": "Tiara of Selemene",
    "item_branches": "Iron Branch",
    "item_mantle": "Mantle of Intelligence",
    "item_robe": "Robe of the Magi",
    "item_circlet": "Circlet",
    "item_crown": "Crown",
    "item_bracer": "Bracer",
    "item_wraith_band": "Wraith Band",
    "item_cyclone": "Eul's Scepter of Divinity",
    "item_sphere": "Linken's Sphere",
    "item_bfury": "Battle Fury",
    "item_vladmir": "Vladmir's Offering",
    "item_skadi": "Eye of Skadi",
    "item_manta": "Manta Style",
    "item_ghost": "Ghost Scepter",
    "item_gungir": "Gleipnir",
    "item_ultimate_scepter": "Aghanim's Scepter",
    "item_consecrated_wraps": "Consecrated Wraps",
    "item_diadem": "Diadem",
    "item_phylactery": "Phylactery",
    "item_witch_blade": "Witch Blade",
    "item_bloodthorn": "Bloodthorn",
    "item_mage_slayer": "Mage Slayer",
    "item_meteor_hammer": "Meteor Hammer",
    "item_rod_of_atos": "Rod of Atos",
    "item_force_staff": "Force Staff",
    "item_hurricane_pike": "Hurricane Pike",
    "item_infused_raindrop": "Infused Raindrop",
    "item_oblivion_staff": "Oblivion Staff",
    "item_staff_of_wizardry": "Staff of Wizardry",
    "item_mystic_staff": "Mystic Staff",
    "item_ultimate_orb": "Ultimate Orb",
    "item_echo_sabre": "Echo Sabre",
    "item_spirit_vessel": "Spirit Vessel",
    "item_guardian_greaves": "Guardian Greaves",
    "item_harpoon": "Harpoon",
    "item_devastator": "Devastator",
    "item_wind_waker": "Wind Waker",
    "item_essence_distiller": "Essence Distiller",
    "item_disperser": "Disperser",
    "item_veil_of_discord": "Veil of Discord",
    "item_kaya": "Kaya",
    "item_dagon": "Dagon",
    "item_dagon_2": "Dagon 2",
    "item_dagon_3": "Dagon 3",
    "item_dagon_4": "Dagon 4",
    "item_dagon_5": "Dagon 5",
    "item_ethereal_blade": "Ethereal Blade",
    "item_magic_wand": "Magic Wand",
    "item_magic_stick": "Magic Stick",
    "item_angels_demise": "Angel's Demise",
}


# ─────────────────────── KV parser (minimal) ───────────────────────────────

def _tokenize(text: str) -> list[str]:
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "#":
            while i < n and text[i] != "\n":
                i += 1
        elif c in "{}":
            out.append(c); i += 1
        elif c == '"':
            i += 1
            j = i
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                else:
                    j += 1
            out.append(text[i:j])
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n{}"':
                j += 1
            if j > i:
                out.append(text[i:j])
            i = j
    return out


def parse_kv(text: str) -> dict:
    tokens = _tokenize(text)
    pos = [0]

    def parse_block() -> dict:
        result: dict = {}
        while pos[0] < len(tokens) and tokens[pos[0]] != "}":
            key = tokens[pos[0]]; pos[0] += 1
            if pos[0] >= len(tokens):
                break
            val = tokens[pos[0]]
            if val == "{":
                pos[0] += 1
                result[key] = parse_block()
                if pos[0] < len(tokens) and tokens[pos[0]] == "}":
                    pos[0] += 1
            else:
                pos[0] += 1
                result[key] = val
        return result

    if not tokens:
        return {}
    root = tokens[pos[0]]; pos[0] += 1
    if pos[0] < len(tokens) and tokens[pos[0]] == "{":
        pos[0] += 1
        body = parse_block()
        if pos[0] < len(tokens) and tokens[pos[0]] == "}":
            pos[0] += 1
        return {root: body}
    return {}


def _patches_with_items() -> list[tuple[str, str]]:
    """RELEASE_HISTORY entries that actually have an items.json on disk,
    oldest → newest."""
    return [
        (p, d) for p, d in reversed(RELEASE_HISTORY)
        if (STATS_ROOT / p / "items.json").exists()
    ]


def _flat_metric(d: dict, kind: str) -> float:
    """Compute a single Mana-Items column metric from a FLAT items.json item
    dict (the slim per-patch JSON has one flat level per slug after the
    DEEP_ITEM_FIELDS flattening in fetch_stats.py). Mirrors load_items()."""
    def g(*keys: str) -> float:
        return sum(_to_float(str(d.get(k, 0))) for k in keys)
    intel = g(*INT_FIELDS) + g(*ALL_STATS_FIELDS)
    if kind == "intel":
        return intel
    if kind == "mana":
        return g(*MAX_MANA_FIELDS) + intel * INT_TO_MAX_MANA
    if kind == "regen":
        passive = g(*PASSIVE_REGEN_FIELDS) + intel * INT_TO_REGEN
        active_mana = max(
            (_to_float(str(d.get(k, 0))) for k in ACTIVE_MANA_FIELDS),
            default=0.0,
        )
        cd = _to_float(str(d.get("AbilityCooldown", 0)))
        active = active_mana / cd if (active_mana > 0 and cd > 0) else 0.0
        mult = 1.0 + g(MULTIPLIER_FIELD) / 100.0
        return (passive + active) * mult
    # Computed columns — derived from regen + cost, matching load_items().
    if kind in ("cost_per_regen", "regen_per_gold", "mana_per_60s"):
        regen = _flat_metric(d, "regen")
        cost = _to_float(str(d.get("ItemCost", 0)))
        if kind == "mana_per_60s":
            return regen * 60
        if regen <= 0 or cost <= 0:
            return 0.0
        if kind == "cost_per_regen":
            return cost / regen
        if kind == "regen_per_gold":
            return regen / cost * 1000   # ×1000, same scale as displayed
    return 0.0


# Manual pre-7.33 history. Our game-file source (muk-as) only goes back to
# 7.33, so changes that happened in or before 7.33 from an earlier value are
# invisible to the auto-diff. Sourced from Liquipedia item changelogs. Keyed
# by (slug, column-kind). Entries are ('V', patch, date, old, new), oldest
# first — they're prepended to the auto-computed history.
_MANUAL_METRIC_HISTORY: dict[tuple[str, str], list] = {
    # Wind Waker: "Reduced mana regeneration bonus from 6 to 3" (7.33).
    ("item_wind_waker", "regen"): [("V", "7.33", "20.04.2023", 6, 3)],
}


def load_metric_history(kind: str) -> dict[str, list[tuple[str, str, float, float]]]:
    """Per-slug change history for a derived column (intel / mana / regen),
    computed across every patch's items.json. Returns
    {slug: [(patch, date, old, new), ...]} oldest-first. Empty until the
    DEEP_ITEM_FIELDS backfill (fetch_stats.py REFRESH_ITEMS_ONLY) lands —
    older items.json only carry ItemCost so every metric reads 0 there and
    no spurious history is emitted (0 == 0)."""
    deep_keys = set(INT_FIELDS) | set(ALL_STATS_FIELDS) | set(MAX_MANA_FIELDS) \
        | set(PASSIVE_REGEN_FIELDS) | {MULTIPLIER_FIELD} | set(ACTIVE_MANA_FIELDS)
    last: dict[str, float] = {}
    hist: dict[str, list[tuple[str, str, float, float]]] = {}
    for patch, date in _patches_with_items():
        try:
            data = _json.loads((STATS_ROOT / patch / "items.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        # Only patches whose items.json actually carries the deep mana fields
        # count toward history. Older slim JSON (pre-backfill / pre-7.33) hold
        # only ItemCost, so every metric reads 0 there — counting them would
        # fake a "0 → real" jump on the first covered patch.
        has_deep = any(
            isinstance(f, dict) and any(k in f for k in deep_keys)
            for f in data.values()
        )
        if not has_deep:
            continue
        for slug, fields in data.items():
            if not isinstance(fields, dict):
                continue
            val = _flat_metric(fields, kind)
            prev = last.get(slug)
            if prev is not None and round(prev, 3) != round(val, 3):
                # ('V', ...) shape so _encode_hist treats it like a value change.
                hist.setdefault(slug, []).append(("V", patch, date, prev, val))
            last[slug] = val
    # Merge manual pre-7.33 entries (prepend — they're older than the auto data).
    for (slug, k), entries in _MANUAL_METRIC_HISTORY.items():
        if k == kind:
            hist[slug] = list(entries) + hist.get(slug, [])
    return hist


def load_cost_history() -> dict[str, list]:
    """Per-slug ItemCost change history + an ADDED marker on the patch the
    item first appeared (only when that's later than the earliest patch we
    have data for — items present since 7.08 predate our window and get no
    ADDED tag). Entry tuples: ('V', patch, date, old, new) for a cost change,
    ('A', patch, date) for the introduction."""
    patches = _patches_with_items()
    earliest_patch = patches[0][0] if patches else None
    last_cost: dict[str, float] = {}
    first_seen: dict[str, tuple[str, str]] = {}
    history: dict[str, list] = {}
    for patch, date in patches:
        try:
            data = _json.loads((STATS_ROOT / patch / "items.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        for slug, fields in data.items():
            if not isinstance(fields, dict):
                continue
            cost_raw = fields.get("ItemCost")
            if cost_raw is None:
                continue
            try:
                cost = float(cost_raw)
            except (TypeError, ValueError):
                continue
            if slug not in first_seen:
                first_seen[slug] = (patch, date)
            prev = last_cost.get(slug)
            if prev is not None and prev != cost:
                history.setdefault(slug, []).append(("V", patch, date, prev, cost))
            last_cost[slug] = cost
    # Prepend ADDED entries for items introduced after our window start.
    for slug, (patch, date) in first_seen.items():
        if patch != earliest_patch:
            history.setdefault(slug, []).insert(0, ("A", patch, date))
    return history


def _decode(b: bytes) -> str:
    if b.startswith(b"\xff\xfe"):
        return b[2:].decode("utf-16-le", errors="replace")
    if b.startswith(b"\xef\xbb\xbf"):
        return b[3:].decode("utf-8", errors="replace")
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("latin-1", errors="replace")


# ─────────────────────── extraction helpers ────────────────────────────────

def _walk_values(node, want_keys: tuple, out: dict | None = None) -> dict:
    """Recursively collect first-occurrence numeric values for keys in
    `want_keys`. Useful since Valve nests fields inside AbilityValues /
    AbilitySpecial / itemref subblocks inconsistently."""
    if out is None:
        out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            if k in want_keys and k not in out:
                # Value can be a string scalar or a nested {"value":"...",...} block.
                if isinstance(v, str):
                    out[k] = v
                elif isinstance(v, dict) and "value" in v and isinstance(v["value"], str):
                    out[k] = v["value"]
            if isinstance(v, dict):
                _walk_values(v, want_keys, out)
    return out


def _to_float(s: str) -> float:
    """Parse Valve's level-list values (`"45 50 55 60"`) — take the first
    numeric token. Returns 0.0 on parse failure."""
    if not s:
        return 0.0
    tok = s.strip().split()[0]
    try:
        return float(tok)
    except ValueError:
        return 0.0


_AE_NAMES: dict[str, str] = {}


def _load_ae_names() -> dict[str, str]:
    """Parse Valve's abilities_english.txt for canonical item display names.
    Valve indexes them as `DOTA_Tooltip_[Aa]bility_item_<slug>` (note the
    inconsistent capital A — we accept either). Recipes / descriptions /
    notes / lore variants are filtered out."""
    if _AE_NAMES:
        return _AE_NAMES
    p = _HERE / "data" / "abilities_english.txt"
    if not p.exists():
        return _AE_NAMES
    text = _decode(p.read_bytes())
    drop_suffixes = (
        "_Description", "_description", "_Lore", "_lore",
        "_aghanim_description", "_shard_description",
    )
    note_re = re.compile(r"_Note\d+$|_note\d+$")
    for m in re.finditer(
        r'"DOTA_Tooltip_[Aa]bility_(item_[a-z0-9_]+)"\s+"([^"]+)"', text
    ):
        slug, val = m.group(1), m.group(2)
        if slug.startswith("item_recipe_"):
            continue
        if any(slug.endswith(suf) for suf in drop_suffixes):
            continue
        if note_re.search(slug):
            continue
        # Last-wins is fine — Valve sometimes ships an old alias and the
        # newer canonical right after; the second one wins.
        _AE_NAMES[slug] = val
    return _AE_NAMES


def _display_name(slug: str) -> str:
    # Canonical in-game name from Valve's localization wins over any hand
    # override and over the slug-pretty-print fallback.
    ae = _load_ae_names()
    if slug in ae:
        return ae[slug]
    if slug in ITEM_DISPLAY_OVERRIDES:
        return ITEM_DISPLAY_OVERRIDES[slug]
    name = slug.replace("item_", "").replace("_", " ")
    parts = name.split()
    small = {"of", "the", "and", "or"}
    return " ".join(p if (i and p in small) else p.title() for i, p in enumerate(parts))


# ─────────────────────── main item parse ───────────────────────────────────

def load_items() -> list[dict]:
    text = _decode(ITEMS_TXT.read_bytes())
    kv = parse_kv(text)
    root = next(iter(kv.values()), {})

    rows: list[dict] = []
    for slug, body in root.items():
        if not isinstance(body, dict):
            continue
        if not slug.startswith("item_"):
            continue
        if any(slug.startswith(p) for p in EXCLUDE_PREFIXES):
            continue
        if body.get("ItemPurchasable", "1") == "0":
            continue

        # Cost — required.
        cost_s = body.get("ItemCost", "")
        if not cost_s:
            # Walk subblocks for ItemCost.
            cost_walk = _walk_values(body, ("ItemCost",))
            cost_s = cost_walk.get("ItemCost", "")
        cost = _to_float(cost_s)
        if cost <= 0:
            continue

        # Stat / regen fields — walk nested AbilityValues subblocks.
        fields = _walk_values(
            body,
            PASSIVE_REGEN_FIELDS + MAX_MANA_FIELDS + INT_FIELDS
            + ALL_STATS_FIELDS + ACTIVE_MANA_FIELDS
            + ("AbilityCooldown", MULTIPLIER_FIELD),
        )
        # Clarity: a consumable that restores mana over a duration via a temporary
        # `mana_regen` buff (mana_regen=6 for buff_duration=25 → 150 mana). That's
        # NOT permanent regen, so model it as an ACTIVE restore (like Soul Ring):
        # reclassify the buff as a total active grant (rate × duration) amortised
        # over its own duration → its in-buff regen rate (6/sec). Renders as
        # "Clarity (Active)".
        if slug == "item_clarity":
            _dur = _to_float(_walk_values(body, ("buff_duration",)).get("buff_duration", "0"))
            _rate = _to_float(fields.get("mana_regen", "0"))
            if _dur > 0 and _rate > 0:
                fields.pop("mana_regen", None)          # not a permanent passive regen
                fields["mana_gain"] = str(_rate * _dur)  # total restored (ACTIVE_MANA_FIELDS)
                fields["AbilityCooldown"] = str(_dur)    # amortise over the buff duration
        # all_stats contributes to every primary attribute → for mana purposes
        # we treat it as additional Int.
        intel = (
            sum(_to_float(fields.get(k, "0")) for k in INT_FIELDS) +
            sum(_to_float(fields.get(k, "0")) for k in ALL_STATS_FIELDS)
        )
        max_mana = sum(_to_float(fields.get(k, "0")) for k in MAX_MANA_FIELDS)
        passive_regen = sum(
            _to_float(fields.get(k, "0")) for k in PASSIVE_REGEN_FIELDS
        )
        active_mana = max(
            (_to_float(fields.get(k, "0")) for k in ACTIVE_MANA_FIELDS),
            default=0.0,
        )
        cd = _to_float(fields.get("AbilityCooldown", "0"))
        active_regen = (active_mana / cd) if (active_mana > 0 and cd > 0) else 0.0

        multiplier_pct = _to_float(fields.get(MULTIPLIER_FIELD, "0"))

        # Derived totals
        int_max_mana   = intel * INT_TO_MAX_MANA
        int_regen      = intel * INT_TO_REGEN
        total_mp       = max_mana + int_max_mana
        passive_total  = passive_regen + int_regen
        # mana_regen_multiplier (Kaya = +30%, Kaya+Sange = +40% etc.) at
        # minimum scales the item's own self-contribution to regen — the
        # multiplier also amplifies the hero's base + other items' regen,
        # but that depends on the build, so we surface only the self-effect
        # here (the chip in the cell still reminds the reader that the %
        # bonus applies on top of any external mana-regen sources too).
        mult_factor = 1.0 + (multiplier_pct / 100.0)
        passive_total *= mult_factor
        active_regen  *= mult_factor
        total_regen    = passive_total + active_regen
        # Table is regen-focused — drop items with no regen contribution at
        # all (pure max-mana boosters like Soul Booster / Aeon Disk are
        # interesting in another view, but they sink everything to "infinity
        # cost per regen" here and clutter the rankings). Items whose only
        # regen contribution is a multiplier still qualify (Kaya etc.).
        if total_regen <= 0 and multiplier_pct <= 0:
            continue

        # Decision: split into a base row + (Active) sub-row when this item
        # both has a mana-relevant stat (Int / MP / passive regen / mult)
        # AND an active mana grant. Items with only an active (Soul Ring)
        # stay as a single row whose regen IS the active contribution.
        has_mana_stats = (
            intel > 0 or max_mana > 0 or passive_regen > 0 or multiplier_pct > 0
        )
        has_active = active_regen > 0
        split_active = has_mana_stats and has_active

        def make(name, regen, is_active_sub=False, parent_slug=None):
            return {
                "slug": slug + ("__active" if is_active_sub else ""),
                "parent_slug": parent_slug,
                "name": name,
                "is_active_sub": is_active_sub,
                "has_active_child": split_active and not is_active_sub,
                "cost": cost,
                "intel": intel,
                "max_mana": total_mp,
                "max_mana_base": max_mana,
                "max_mana_from_int": int_max_mana,
                "regen": regen,
                "regen_passive": passive_regen,
                "regen_from_int": int_regen,
                "regen_active": active_regen if is_active_sub or not split_active else 0.0,
                "active_mana": active_mana,
                "active_cd": cd,
                "multiplier_pct": multiplier_pct if not is_active_sub else 0.0,
                "cost_per_regen": cost / regen if regen > 0 else 0.0,
                "regen_per_gold": regen / cost if cost > 0 else 0.0,
                "mana_per_60s": regen * 60,
            }

        display_name = _display_name(slug)
        if split_active:
            # Base row: passive (incl. Int) only — no active component.
            rows.append(make(display_name, passive_total))
            # Hidden sub-row: passive + active.
            rows.append(make(
                f"{display_name} (Active)", total_regen,
                is_active_sub=True, parent_slug=slug,
            ))
        elif has_active:
            # Active-only item (Soul Ring): its entire regen comes from the
            # active (Sacrifice), so mark it as an Active row — it reads with
            # the "(Active)" suffix and groups/filters with the other actives.
            rows.append(make(
                f"{display_name} (Active)", total_regen,
                is_active_sub=True, parent_slug=slug,
            ))
        else:
            # Single-row passive item: regen is the passive total.
            rows.append(make(display_name, total_regen))

    # Default sort: by mana regen (descending). Active sub-rows compete
    # independently with base rows so Arcane Blink (Active) lands above
    # Soul Ring on default load.
    rows.sort(key=lambda r: r["regen"], reverse=True)
    return rows


# ─────────────────────── HTML render ───────────────────────────────────────

def _esc(s) -> str:
    return (str(s).replace("&", "&amp;")
                  .replace("<", "&lt;").replace(">", "&gt;"))


def _fmt(v: float, decimals: int = 2) -> str:
    # `0` cells render as a muted short dash matching the convention used by
    # the Creeps / Unit Abilities tables (.ua-dash).
    if v == 0:
        return '<span class="ua-dash">—</span>'
    return f"{v:,.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{v:,.0f}"


def _short(v: float) -> str:
    """Compact format with comma-as-decimal for values ≥ 1000 — the column
    holds thousands implicitly so "5000" reads as "5,0" and "17,833" reads
    as "17,83". Three significant digits are kept; trailing zeros stripped
    down to one decimal."""
    if v == 0:
        return '<span class="ua-dash">—</span>'
    if v >= 1000:
        # Two decimals max; strip trailing zeros but keep at least one
        # decimal so "5000" doesn't degenerate to a bare "5".
        s = f'{v / 1000:.2f}'.rstrip('0').rstrip('.')
        if '.' not in s:
            s += '.0'
        return s.replace('.', ',')
    if v >= 100:
        return f'{v:.0f}'
    if v >= 10:
        return f'{v:.1f}'.rstrip('0').rstrip('.')
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def _short_plain(v: float) -> str:
    """Same compact rule as _short but returns a bare string (for tooltip
    payloads): ≥1000 → 'X,Y' thousands with comma-decimal, else trimmed."""
    if v >= 1000:
        s = f'{v / 1000:.2f}'.rstrip('0').rstrip('.')
        if '.' not in s:
            s += '.0'
        return s.replace('.', ',')
    if v >= 100:
        return f'{v:.0f}'
    if v >= 10:
        return f'{v:.1f}'.rstrip('0').rstrip('.')
    return f'{v:.2f}'.rstrip('0').rstrip('.')


def _has_icon(slug: str) -> bool:
    """Items reuse the same icon CDN we serve abilities from; the local
    convention is icons/items/<short>.png."""
    short = slug.replace("item_", "")
    return (_HERE / "icons" / "items" / f"{short}.png").exists()


def _icon_html(slug: str) -> str:
    short = slug.replace("item_", "")
    if _has_icon(slug):
        # Plain icon — no hover description tooltip. The effect popups were
        # redundant (the page is about mana metrics, not item descriptions) and
        # added a tooltip payload + JS hint handler to every row.
        return (f'<img class="mr-ico" src="icons/items/{short}.png" '
                f'alt="" loading="lazy">')
    return '<span class="mr-ico mr-ico-blank"></span>'


# Intelligence engine-constant history (hardcoded in the Source 2 engine,
# not in any of our scraped KV files). Sourced from Liquipedia's curated
# /Intelligence/Changelogs page. Format: (patch, date, old, new).
_INT_MANA_HIST = [
    ("7.07",  "31.10.2017", 13, 14),
    ("7.20",  "19.11.2018", 14, 12),
    ("7.36",  "10.05.2024", 12, 11),
    ("7.39",  "21.05.2025", 11, 12),
]
_INT_REGEN_HIST = [
    ("7.07",  "31.10.2017", 0.04, 0.05),
]


def _int_const_chip(label: str, hist: list[tuple]) -> str:
    """Styled like a Mana Items `has-history` cell: dotted underline + the
    same data-hist payload the stat-hist-tip JS reads. `pol="hi"` because
    HIGHER mana / regen per Int is the buff (positive for the hero)."""
    parts = [f'{p}|{d}|V|{_short(o)}|{_short(n)}|hi'
             for p, d, o, n in hist]
    payload = ';'.join(parts)
    return (
        f'<span class="mr-const has-history" '
        f'data-name="Per Intelligence" data-hist="{_esc(payload)}">'
        f'{_esc(label)}</span>'
    )


def _full(v: float) -> str:
    """Plain full integer, NO thousands separator (Price column). Matches the
    tooltip payload formatting so cell and popup read identically (5000, not
    5,000). 0 → muted dash."""
    if v == 0:
        return '<span class="ua-dash">—</span>'
    return f"{v:.0f}"


def _encode_hist(hist: list, pol: str, value_fmt, kind: str = "V") -> str:
    """Turn a mixed history list into the data-hist payload string the
    stat-hist-tip JS reads. Supports ('V', patch, date, old, new) value
    changes, ('A', patch, date) introduction markers, and — via `kind="C"` —
    a computed column: the pretty short display is sent for old/new, plus the
    RAW numeric old/new (comma-free, dot-decimal) so the JS computes a correct
    % delta. (The short display alone can't drive the %: values ≥1000 are
    rendered as thousands "5,0" while smaller ones stay plain "714", so the two
    sides aren't on the same scale.)"""
    parts = []
    for e in hist:
        if e[0] == "A":
            _, p, d = e
            parts.append(f"{p}|{d}|A|New item")
        elif kind == "C":
            _, p, d, o, n = e
            parts.append(
                f"{p}|{d}|C|{value_fmt(o)}|{value_fmt(n)}|{o:g}|{n:g}|{pol}")
        else:
            _, p, d, o, n = e
            parts.append(f"{p}|{d}|V|{value_fmt(o)}|{value_fmt(n)}|{pol}")
    return ";".join(parts)


def _cost_cell(r: dict, cost_hist: dict[str, list]) -> str:
    """Price cell — full numbers, with cost-change + ADDED history on hover."""
    slug = r["slug"].replace("__active", "")
    hist = cost_hist.get(slug, [])
    display = _full(r["cost"])
    if not hist:
        return f'<td data-sort="{r["cost"]}">{display}</td>'
    # Payload numbers stay comma-free (plain integers) — the stat-hist-tip JS
    # parses them with parseFloat after a ','→'.' swap, so a thousands comma
    # would be misread as a decimal once a value crosses 1000.
    payload = _encode_hist(hist, "lo", lambda v: f"{v:.0f}")
    # No data-name: the row already identifies the item, so an item-name header
    # in the tooltip is just a duplicate. data-net adds the overall summary.
    return (
        f'<td class="has-history" data-sort="{r["cost"]}" '
        f'data-net="" data-hist="{_esc(payload)}">{display}</td>'
    )


def _metric_cell(r: dict, col_key: str, value: float, display: str,
                 metric_hist: dict[str, list], sort_val=None,
                 pol: str = "hi", css: str = "", computed: bool = False) -> str:
    """Generic numeric cell that attaches per-patch history (data-hist) when
    the item has a recorded change for this column. `display` is the already-
    formatted inner HTML; `value` the numeric sort key; `pol` the buff
    polarity for the tooltip colour ('hi' = higher better, 'lo' = lower);
    `css` an extra class (e.g. the section-divider marker). `computed=True`
    columns use the short notation in the tooltip AND a % delta computed from
    the raw values (kind="C")."""
    sort_val = value if sort_val is None else sort_val
    cls = f' class="{css}"' if css else ''
    slug = r["slug"].replace("__active", "")
    hist = metric_hist.get(slug, [])
    if not hist:
        return f'<td{cls} data-sort="{sort_val}">{display}</td>'
    if computed:
        # Short notation in the tooltip (e.g. 288,3 / 5,0) plus a % delta
        # derived from the raw values carried alongside.
        payload = _encode_hist(hist, pol, lambda v: _short_plain(v), kind="C")
    else:
        payload = _encode_hist(hist, pol, lambda v: f"{v:g}")
    # No data-name (row already identifies the item — see _cost_cell). data-net
    # adds the overall first→today summary at the top of the tooltip.
    hcls = (css + " has-history").strip()
    return (
        f'<td class="{hcls}" data-sort="{sort_val}" '
        f'data-net="" data-hist="{_esc(payload)}">{display}</td>'
    )


def render_html(rows: list[dict], cost_hist: dict[str, list] | None = None,
                intel_hist: dict | None = None, mana_hist: dict | None = None,
                regen_hist: dict | None = None, cpr_hist: dict | None = None,
                rpg_hist: dict | None = None, m60_hist: dict | None = None) -> str:
    cost_hist = cost_hist or {}
    intel_hist = intel_hist or {}
    mana_hist = mana_hist or {}
    regen_hist = regen_hist or {}
    cpr_hist = cpr_hist or {}
    rpg_hist = rpg_hist or {}
    m60_hist = m60_hist or {}
    # subnav_in_header=False: the Materials sub-tab bar is placed INSIDE the
    # scroll box (below), exactly like Neutral Creeps / Neutral Abilities — not
    # as a separate strip under the header. Keeps all three pages identical.
    nav = _site.render_top_nav('materials', _latest_href(),
                               patch_context=False, subtabs_active='mana_items',
                               subnav_in_header=False)
    subnav = _site.render_materials_subnav('mana_items')

    # `direction` drives per-column conditional formatting (scripts.js):
    # "higher" cells go green at top of range, red at bottom; "lower" cells
    # invert; "" leaves the column uncoloured.
    head_cells = [
        ('name',           'Item',                  ''),
        ('cost',           'Price',                 'lower'),
        ('intel',          'Intelligence',          'higher'),
        ('max_mana',       'Mana',                  'higher'),
        ('regen',          'Mana regen',            'higher'),
        ('cost_per_regen', 'Cost per 1 Mana regen', 'lower'),
        ('regen_per_gold', 'Mana regen per 1 gold', 'higher'),
        ('mana_per_60s',   'Mana per 60 sec',       'higher'),
    ]
    # Server-side default sort lives on "regen" (descending). Mark that
    # header with `sort-desc` so the indicator already reflects the visual
    # order on first paint, before any click handlers run.
    thead = ''.join(
        f'<th class="mr-th mr-col-{k} sortable'
        f'{" sort-desc" if k == "regen" else ""}" '
        f'data-col="{k}"'
        f'{f" data-direction={dr}" if dr else ""}>'
        f'<span class="th-label">{label}</span>'
        f'<span class="sort-ind"></span></th>'
        for k, label, dr in head_cells
    )

    body_rows = []
    for r in rows:
        # Mana-regen multiplier chip (Kaya family etc.) shown inline next to
        # the flat regen value.
        # Multiplier shown as a `?` hint badge (same pattern as Unit
        # Abilities), not a permanent chip. Hover explains it.
        if r["multiplier_pct"]:
            tip = (f'+{_fmt(r["multiplier_pct"], 0)}% mana-regen multiplier '
                   f'(included in this value). It also amplifies the hero’s '
                   f'other mana-regen sources.')
            mult_chip = (f'<span class="qhint" tabindex="0" role="button" '
                         f'aria-label="{_esc(tip)}" data-tooltip="{_esc(tip)}">'
                         f'?</span>')
        else:
            mult_chip = ''
        regen_display = (f'{_short(r["regen"])}{mult_chip}')

        # Active sub-rows are first-class siblings (no dropdown). Hidden in
        # bulk by the "Hide Active" toggle via the .mr-active-row class.
        row_cls = ' class="mr-active-row"' if r["is_active_sub"] else ''
        row_attrs = f' data-slug="{r["slug"]}"'

        body_rows.append(
            f'<tr id="mr-{r["slug"]}"{row_cls}{row_attrs}>'
            f'<td class="mr-name">{_icon_html(r["slug"].replace("__active", ""))}'
            f'<span class="mr-name-text">{_esc(r["name"])}</span></td>'
            f'{_cost_cell(r, cost_hist)}'
            f'{_metric_cell(r, "intel", r["intel"], _short(r["intel"]), intel_hist)}'
            f'{_metric_cell(r, "mana", r["max_mana"], _short(r["max_mana"]), mana_hist)}'
            f'{_metric_cell(r, "regen", r["regen"], regen_display, regen_hist)}'
            # Section divider before the first COMPUTED column (.mr-sep).
            f'{_metric_cell(r, "cost_per_regen", r["cost_per_regen"], _short(r["cost_per_regen"]), cpr_hist, pol="lo", css="mr-sep", computed=True)}'
            f'{_metric_cell(r, "regen_per_gold", r["regen_per_gold"] * 1000, _short(r["regen_per_gold"] * 1000), rpg_hist, sort_val=f"{r["regen_per_gold"]:.6f}", computed=True)}'
            f'{_metric_cell(r, "mana_per_60s", r["mana_per_60s"], _short(r["mana_per_60s"]), m60_hist, computed=True)}'
            f'</tr>'
        )

    table = (
        '<table class="mr-table sortable-table">'
        f'<thead><tr>{thead}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody>'
        '</table>'
    )

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<title>SIKLE | Mana Items</title>\n'
        + _site.favicon_links() +
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" '
        'href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=block">\n'
        f'<link rel="stylesheet" href="styles.css?v={ASSET_VERSION}">\n'
        '</head>\n<body>\n'
        f'{nav}\n'
        '<div class="container creeps-page">\n'
        '<div class="creeps-scroll">\n'
        # Sub-tab bar + blurb + toolbar live INSIDE the scroll box (above the
        # table) so they scroll away with it — identical to Neutral Creeps /
        # Neutral Abilities. Only the site nav + the sticky table header stay
        # pinned. `inbox-bar` makes them sticky-left so they don't slide off on
        # horizontal scroll.
        f'{subnav}'
        '<p class="mr-blurb inbox-bar">Every purchasable item that contributes mana regen, '
        'sorted by total <em>Mana regen</em> by default. Intelligence contributes '
        f'{_int_const_chip("+12 max mana", _INT_MANA_HIST)} and '
        f'{_int_const_chip("+0.05 mana regen", _INT_REGEN_HIST)} per '
        'point. Active items that literally restore mana to the caster '
        '(Soul Ring, Arcane Boots’ replenish) are amortised as '
        '<code>active_mana / cooldown</code> and added to passive regen. '
        '<em>Mana regen per 1 gold</em> is ×1000 for readability. '
        'Click any column header to re-sort.</p>\n'
        # Toolbar — Price min/max + Hide Active + Heatmap. Layout matches
        # the cal-toggle-bar / ua-upgrades-toggle convention used on the
        # Neutral Creeps & Unit Abilities pages.
        '<div class="cal-toggle-bar mr-toolbar inbox-bar"><div class="toolbar-panel">'
        # Flat price pill matching items_dyn: "Price" label inside, underlined inputs,
        # no nested box — same height as the rest of the panel. X visible when a bound set.
        '<span class="mr-price-range hd-price-range">'
        '<span class="mr-price-label" aria-hidden="true">Price</span>'
        '<input type="number" class="mr-price-input" id="mr-price-min" '
        'placeholder="min" min="0" step="50" inputmode="numeric" '
        'aria-label="Minimum price">'
        '<span class="mr-price-sep" aria-hidden="true">–</span>'
        '<input type="number" class="mr-price-input" id="mr-price-max" '
        'placeholder="max" min="0" step="50" inputmode="numeric" '
        'aria-label="Maximum price">'
        '<button type="button" class="mr-price-clear" id="mr-price-clear" '
        'aria-label="Clear price range" hidden>'
        '<svg viewBox="0 0 12 12" width="10" height="10" aria-hidden="true">'
        '<path d="M2 2 L10 10 M10 2 L2 10" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" fill="none"/>'
        '</svg></button>'
        '</span>'
        '<label class="ua-upgrades-toggle">'
        '<span class="ua-upgrades-label">Hide Active</span>'
        '<input type="checkbox" id="mr-hide-active" class="ua-switch-input">'
        '<span class="ua-switch" aria-hidden="true"></span>'
        '</label>'
        '<label class="ua-upgrades-toggle">'
        '<span class="ua-upgrades-label">Heatmap</span>'
        '<input type="checkbox" id="mr-heatmap-toggle" '
        'class="ua-switch-input" checked>'
        '<span class="ua-switch" aria-hidden="true"></span>'
        '</label>'
        '<span class="search-box hd-search">'
        '<input type="text" id="mr-search" autocomplete="off" spellcheck="false" '
        'placeholder="Search items — blink, kaya, arcane…">'
        '</span>'
        '</div></div>\n'
        f'{table}\n'
        '</div>\n'   # close .creeps-scroll
        '</div>\n'   # close .creeps-page
        f'<script src="src/scripts.js?v={ASSET_VERSION}"></script>\n'
        '</body>\n</html>\n'
    )


def _latest_href() -> str:
    """Read the latest patch HTML path from data/site_meta.json (written by
    build_patch.py). The key is `latest_patch_filename` (same one build_creeps
    reads); falls back to the current newest patch if missing."""
    meta_path = _HERE / "data" / "site_meta.json"
    if not meta_path.exists():
        return "patches/7.41c.html"
    try:
        meta = _json.loads(meta_path.read_text(encoding="utf-8"))
        return meta.get("latest_patch_filename", "patches/7.41c.html")
    except Exception:
        return "patches/7.41c.html"


def main() -> int:
    if not ITEMS_TXT.exists():
        print(f"  ! {ITEMS_TXT} missing — skipping mana_regen.html")
        return 0
    rows = load_items()
    cost_hist = load_cost_history()
    intel_hist = load_metric_history("intel")
    mana_hist = load_metric_history("mana")
    regen_hist = load_metric_history("regen")
    cpr_hist = load_metric_history("cost_per_regen")
    rpg_hist = load_metric_history("regen_per_gold")
    m60_hist = load_metric_history("mana_per_60s")
    html = render_html(rows, cost_hist, intel_hist, mana_hist, regen_hist,
                       cpr_hist, rpg_hist, m60_hist)
    out = _HERE / "mana_items.html"
    out.write_text(html, encoding="utf-8")
    print(f"  -> mana_items.html: {len(html):,} bytes "
          f"({len(rows)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
