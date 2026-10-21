"""build_silent_changes.py — Diff per-hero KV files between consecutive patches
and emit a `patches/silent/{version}.html` "silent changes" page for each pair
where both `data/stats/{prev}/heroes/` and `data/stats/{curr}/heroes/` exist.

The KV files in data/stats/{version}/heroes/ are Valve's raw npc_dota_hero_*.txt
files (synced by fetch_stats.py + extract_patchnotes.py). They carry every field
of every ability — including hidden / service abilities the official patchnotes
don't mention.

Since 2026-10-21 the page also diffs the root files items.txt, npc_units.txt and npc_abilities.txt (sections Items,
Units, Other abilities) whenever both patches have them (7.41c on): the per-hero files alone missed the Necronomicon
rework of client 6946 (cost 2050 -> 2700, Staff of Wizardry instead of 2 Sobi Masks, Intelligence instead of mana
regen), which lives in items.txt.

Usage:
  python build_silent_changes.py             # all available pairs
  python build_silent_changes.py 7.41c       # one specific patch (vs prev)

This script intentionally stays standalone — it does NOT import or modify the
main builders/build_patches.py monolith. The generated pages live under patches/silent/
and are linked from each regular patch page header (added separately).
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
DATA_DIR = _HERE / "data" / "stats"
OUT_DIR = _HERE / "dist" / "patches" / "silent"

# When this file is executed as `python builders/silent.py`, Python puts the
# `builders/` directory first on sys.path. That shadows the real `patch/`
# package with `builders/patch.py`, so force the repo root to the front.
sys.path.insert(0, str(_HERE))

# Import from canonical source instead of maintaining a duplicate list.
from patch.meta import RELEASE_HISTORY as _RH
import builders.site_common as _site   # hero_ability_blocks: per-hero KV layout (7.41f+)
RELEASE_HISTORY = [p["version"] for p in _RH]

# Field-path patterns we suppress as engine-noise: visual FX, sound events,
# animation hooks, particle resource paths. Matched case-insensitively against
# the flattened key path (e.g. "Modifier_X.OnCreated.FireSound").
NOISE_PATTERNS = (
    "fx", "particle", "vpcf", "vsndevt", "vsnd", "sound", "animation",
    "anim_activity", "vmdl", "model", "thinkinterval",
    "scriptfile", "lua_", "abilityentityname", "abilityresource",
)

# Only these top-level field categories actually matter for gameplay; everything
# else is engine plumbing. Empty = no whitelist (diff everything except noise).
# Set the env var SC_FULL_DIFF=1 to bypass the whitelist for debugging.
INTERESTING_FIELDS = {
    "AbilityBehavior", "AbilityCastRange", "AbilityCastPoint", "AbilityCooldown",
    "AbilityManaCost", "AbilityDamage", "AbilityDuration",
    "AbilityCharges", "AbilityChargeRestoreTime",
    "AbilityUnitTargetTeam", "AbilityUnitTargetType", "AbilityUnitTargetFlags",
    "AbilityUnitDamageType", "SpellImmunityType", "SpellDispellableType",
    "FightRecapLevel", "MaxLevel",
    "HasScepterUpgrade", "HasShardUpgrade", "IsGrantedByScepter", "IsGrantedByShard",
    "ItemRequirements", "AbilityValues",  # whole AbilityValues block iterated below
}

# items.txt: the ability fields above + what an item is in the shop.
ITEM_FIELDS = {
    "ItemCost", "ItemRecipe", "ItemResult", "ItemPurchasable", "ItemSellable", "ItemDroppable",
    "ItemStockMax", "ItemStockTime", "ItemStockInitial", "ItemInitialStockTime", "ItemInitialCharges",
    "ItemDisplayCharges", "ItemRequiresCharges", "ItemPermanent", "ItemStackable", "ItemShareability",
    "ItemIsNeutralActiveDrop", "ItemIsNeutralPassiveDrop", "IsObsolete",
}
# npc_units.txt: the unit's gameplay numbers and its abilities (Ability1..N); models, sounds, FX are left out.
UNIT_FIELDS = {
    "Level", "StatusHealth", "StatusHealthRegen", "StatusMana", "StatusManaRegen", "StatusStartingMana",
    "ArmorPhysical", "MagicalResistance", "AttackCapabilities", "AttackDamageMin", "AttackDamageMax",
    "AttackDamageType", "AttackRate", "BaseAttackSpeed", "AttackAnimationPoint", "AttackAcquisitionRange",
    "AttackRange", "AttackRangeBuffer", "ProjectileSpeed", "BountyXP", "BountyGoldMin", "BountyGoldMax",
    "MovementCapabilities", "MovementSpeed", "MovementTurnRate", "VisionDaytimeRange", "VisionNighttimeRange",
    "CombatClassAttack", "CombatClassDefend", "IsAncient", "IsNeutralUnitType", "ConsideredHero", "HasInventory",
}
# (file in data/stats/<v>/, section title, which fields count)
ROOT_FILES = (
    ("items.txt", "Items", "item"),
    ("npc_units.txt", "Units", "unit"),
    ("npc_abilities.txt", "Other abilities", "ability"),
)


# ───────────────────────── KV PARSER ───────────────────────────────────────

def _decode_bytes(raw: bytes) -> str:
    if raw.startswith(b"\xff\xfe"):
        return raw[2:].decode("utf-16-le", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def _tokenize_kv(text: str) -> list[str]:
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "#":  # #base / #include directives
            while i < n and text[i] != "\n":
                i += 1
        elif c in "{}":
            out.append(c)
            i += 1
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
    """Parse Valve KV-1 text. Returns the top-level {root_key: {...}} dict.
    Tolerates duplicate keys (last write wins) and unbalanced braces."""
    tokens = _tokenize_kv(text)
    pos = [0]

    def parse_block() -> dict:
        result: dict = {}
        while pos[0] < len(tokens) and tokens[pos[0]] != "}":
            key = tokens[pos[0]]
            pos[0] += 1
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
    root = tokens[pos[0]]
    pos[0] += 1
    if pos[0] < len(tokens) and tokens[pos[0]] == "{":
        pos[0] += 1
        body = parse_block()
        if pos[0] < len(tokens) and tokens[pos[0]] == "}":
            pos[0] += 1
        return {root: body}
    return {}


# ───────────────────────── LOAD HEROES DIR ─────────────────────────────────

def _is_noise(key_path: str) -> bool:
    low = key_path.lower()
    return any(p in low for p in NOISE_PATTERNS)


def _flatten(d: dict, prefix: str = "") -> dict:
    """Flatten nested dict into {a.b.c: value}, skipping engine-noise paths."""
    out: dict = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if _is_noise(key):
            continue
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


_SKIP_TOP_KEYS = {"Version"}


def load_hero_abilities(version: str) -> dict[str, dict[str, dict]]:
    """Return { hero_slug: { ability_slug: { flat_field: value } } } for the
    given version. Empty dict if the heroes/ folder is missing.

    Per-hero files are structured as
        "DOTAAbilities" { "Version" "1" ability_slug { ... } ability_slug2 {...} }
    i.e. abilities are top-level inside DOTAAbilities. The hero identity comes
    from the filename, NOT from the KV body."""
    heroes_dir = DATA_DIR / version / "heroes"
    if not heroes_dir.exists():
        return {}
    out: dict[str, dict[str, dict]] = {}
    for p in sorted(heroes_dir.glob("npc_dota_hero_*.txt")):
        if p.name == "npc_dota_hero_base.txt": continue   # parent template (7.41f+), not a hero
        try:
            text = _decode_bytes(p.read_bytes())
            kv = parse_kv(text)
        except Exception as e:
            print(f"  ⚠ parse failed: {p.name}: {e}", file=sys.stderr)
            continue
        hero_slug = p.stem
        root = _site.hero_ability_blocks(kv)       # DOTAAbilities, or 7.41f+ AbilityDefinitions
        if not isinstance(root, dict):
            continue
        abilities: dict[str, dict] = {}
        for key, val in root.items():
            if key in _SKIP_TOP_KEYS or not isinstance(val, dict):
                continue
            abilities[key] = _flatten(val)
        if abilities:
            out[hero_slug] = abilities
    return out


def load_root_file(version: str, name: str) -> dict[str, dict]:
    """{ entity: { flat_field: value } } of one root KV file of data/stats/<version>/ (items.txt, npc_units.txt,
    npc_abilities.txt). Empty dict if the file is missing (the snapshots before 7.41c keep only heroes/)."""
    path = DATA_DIR / version / name
    if not path.exists():
        return {}
    kv = parse_kv(_decode_bytes(path.read_bytes()))
    root = next(iter(kv.values()), {}) if kv else {}
    return {k: _flatten(v) for k, v in root.items() if isinstance(v, dict) and k not in _SKIP_TOP_KEYS}


# ───────────────────────── DIFF ────────────────────────────────────────────

def _interesting(field: str) -> bool:
    if os.environ.get("SC_FULL_DIFF") == "1":
        return True
    top = field.split(".", 1)[0]
    if top in INTERESTING_FIELDS:
        return True
    # av_* per-level values (e.g. av_damage, av_duration) — always interesting.
    if top.startswith("av_"):
        return True
    return False


def _interesting_item(field: str) -> bool:
    return _interesting(field) or field.split(".", 1)[0] in ITEM_FIELDS


def _interesting_unit(field: str) -> bool:
    if os.environ.get("SC_FULL_DIFF") == "1":
        return True
    top = field.split(".", 1)[0]
    return top in UNIT_FIELDS or (top.startswith("Ability") and top[len("Ability"):].isdigit())


_FILTERS = {"ability": _interesting, "item": _interesting_item, "unit": _interesting_unit}


def diff_root_files(prev: str, curr: str) -> list[tuple[str, str, dict]]:
    """[(section title, kind, { entity: { field: (old, new) } })] for the root files both patches have."""
    out = []
    for name, title, kind in ROOT_FILES:
        a, b = load_root_file(prev, name), load_root_file(curr, name)
        if not a or not b:
            continue
        d = diff_versions({title: a}, {title: b}, _FILTERS[kind]).get(title)
        if d:
            out.append((title, kind, d))
    return out


def diff_versions(prev: dict, curr: dict, interesting=_interesting) -> dict:
    """Return { hero: { ability: { field: (old, new) } } }.
    None as old → added field/ability. None as new → removed."""
    out: dict = {}
    heroes = set(prev) | set(curr)
    for h in sorted(heroes):
        pabs = prev.get(h, {})
        cabs = curr.get(h, {})
        abilities = set(pabs) | set(cabs)
        h_diff: dict = {}
        for a in sorted(abilities):
            pf = pabs.get(a, {})
            cf = cabs.get(a, {})
            fields = set(pf) | set(cf)
            f_diff: dict = {}
            for f in sorted(fields):
                if not interesting(f):
                    continue
                pv = pf.get(f)
                cv = cf.get(f)
                if pv != cv:
                    f_diff[f] = (pv, cv)
            if f_diff:
                h_diff[a] = f_diff
        if h_diff:
            out[h] = h_diff
    return out


# ───────────────────────── HTML RENDER ─────────────────────────────────────

def _esc(s) -> str:
    return _site.esc(s, quote=False)


def _val_cell(v) -> str:
    if v is None:
        return '<span class="sc-absent">—</span>'
    s = str(v)
    # Pretty-print AbilityBehavior flag soup (split on |).
    if "DOTA_ABILITY_BEHAVIOR" in s and "|" in s:
        parts = [p.strip() for p in s.split("|")]
        return ''.join(f'<span class="sc-flag">{_esc(p)}</span>' for p in parts)
    return _esc(s)


@lru_cache(maxsize=1)
def _names() -> tuple[dict[str, str], dict[str, str]]:
    """(hero engine name → in-game name, ability slug → in-game name). Before this the page read
    "Zuus", "Nevermore", "Abyssal Underlord" and "abaddon_aphotic_shield" (audit 2026-10-05)."""
    from builders.heroes_stats import _load_display_names
    from builders.aoe_increase import _load_ability_names
    return _load_display_names(), _load_ability_names()


def _hero_display(slug: str) -> str:
    from builders.heroes_stats import _display_name
    return _display_name(slug, _names()[0])


def _ability_display(slug: str) -> str:
    return _names()[1].get(slug) or slug


@lru_cache(maxsize=1)
def _entity_names() -> tuple[dict[str, str], dict[str, str]]:
    """(item slug → in-game name from data/itemlist.json, unit name → in-game name from abilities_english.txt)."""
    import json
    items: dict[str, str] = {}
    try:
        with open(_HERE / "data" / "itemlist.json", encoding="utf-8") as f:
            items = {i["name"]: i.get("name_loc") or i["name"]
                     for i in json.load(f)["result"]["data"]["itemabilities"]}
    except (OSError, ValueError, KeyError) as exc:
        print(f"  ! itemlist.json unreadable ({exc}) — item slugs shown", file=sys.stderr)
    from tools.build_abilities_slim import load_loc
    return items, load_loc()


def _entity_display(kind: str, slug: str) -> str:
    if kind == "item":
        items = _entity_names()[0]
        if slug in items:
            return items[slug]
        if slug.startswith("item_recipe_") and "item_" + slug[len("item_recipe_"):] in items:
            return items["item_" + slug[len("item_recipe_"):]] + " Recipe"   # the datafeed's own wording
        return slug
    if kind == "unit":
        return _entity_names()[1].get(slug.lower()) or slug
    return _ability_display(slug)


def _section_names(kind: str, slugs) -> dict[str, str]:
    """slug → heading; a name several entities share (Dagon 1-5, three Zealots) gets its slug in brackets."""
    names = {s: _entity_display(kind, s) for s in slugs}
    seen: dict[str, int] = {}
    for n in names.values():
        seen[n] = seen.get(n, 0) + 1
    return {s: (f"{n} ({s})" if seen[n] > 1 and n != s else n) for s, n in names.items()}


def _ability_tables(version: str, prev: str, abilities: dict, name) -> list[str]:
    parts: list[str] = []
    for ability, fields in abilities.items():
        parts.append(
            f'<div class="sc-ability">'
            f'<h3 class="sc-ability-name">{_esc(name(ability))}</h3>'
            f'<table class="sc-table">'
            f'<thead><tr><th>Field</th>'
            f'<th>{_esc(prev)}</th><th>{_esc(version)}</th></tr></thead>'
            f'<tbody>'
        )
        for f, (pv, cv) in fields.items():
            parts.append(
                f'<tr><td class="sc-field">{_esc(f)}</td>'
                f'<td class="sc-old">{_val_cell(pv)}</td>'
                f'<td class="sc-new">{_val_cell(cv)}</td></tr>'
            )
        parts.append('</tbody></table></div>')
    return parts


def render_diff_html(version: str, prev: str, diff: dict, root_diffs=()) -> str:
    """Heroes first (one section per hero, its abilities inside), then a section per root file that changed
    (Items / Units / Other abilities, one table per entity) — the same markup and classes."""
    if not diff and not root_diffs:
        return '<p class="sc-empty">No diff detected (or both patches are identical for tracked fields).</p>'
    parts: list[str] = []
    for hero, abilities in diff.items():
        parts.append(f'<section class="sc-hero"><h2>{_esc(_hero_display(hero))}</h2>')
        parts += _ability_tables(version, prev, abilities, _ability_display)
        parts.append('</section>')
    for title, kind, entities in root_diffs:
        parts.append(f'<section class="sc-hero sc-group"><h2>{_esc(title)}</h2>')
        parts += _ability_tables(version, prev, entities, _section_names(kind, entities).get)
        parts.append('</section>')
    return ''.join(parts)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SIKLE | Silent Changes {version}</title>
{head}<link rel="stylesheet" href="../../styles.css?v={asset}">
</head>
<body>
<div class="sc-page">
{back_link}
<h1>Silent Changes</h1>
<p class="sc-sub">Raw KV-field deltas between <strong>{prev}</strong> → <strong>{version}</strong>, parsed
from the game's own {sources} of both patches. These may overlap with the
official patchnotes — this is the source-of-truth view. Engine noise (FX, sounds,
animation, particle resources) is filtered out.</p>
{body}
</div>
</body>
</html>
"""


def build_page(version: str) -> str | None:
    try:
        idx = RELEASE_HISTORY.index(version)
    except ValueError:
        print(f"  ⚠ unknown version: {version}")
        return None
    if idx + 1 >= len(RELEASE_HISTORY):
        print(f"  ⚠ {version} is the oldest patch — nothing to diff against")
        return None
    prev = RELEASE_HISTORY[idx + 1]

    prev_data = load_hero_abilities(prev)
    curr_data = load_hero_abilities(version)
    if not prev_data:
        print(f"  ⚠ no heroes/ data for {prev} — skip")
        return None
    if not curr_data:
        print(f"  ⚠ no heroes/ data for {version} — skip")
        return None

    diff = diff_versions(prev_data, curr_data)
    root_diffs = diff_root_files(prev, version)
    body = render_diff_html(version, prev, diff, root_diffs)
    n_heroes = len(diff)
    n_changes = sum(len(f) for ab in diff.values() for f in ab.values())
    n_root = sum(len(f) for _, _, ents in root_diffs for f in ents.values())
    print(f"  -> silent/{version}.html  ({n_heroes} heroes, {n_changes} field deltas"
          + "".join(f"; {t}: {len(e)}" for t, _, e in root_diffs) + (f", {n_root} field deltas)" if root_diffs else ")"))
    both_roots = all((DATA_DIR / v / name).exists() for v in (prev, version) for name, _, _ in ROOT_FILES)
    sources = "hero, item and unit files" if both_roots else "hero files"
    # Only show back-link when the annotated patch page actually exists
    has_content = any(
        p.stem == f"p{version.replace('.', '')}"
        for p in Path("content").glob("p*.py")
    )
    back_link = (
        f'<a class="sc-back" href="../{version}.html">← Back to {version} changelog</a>'
        if has_content else
        '<a class="sc-back" href="../../">← All Patches</a>'
    )
    return PAGE_TEMPLATE.format(version=version, prev=prev, body=body, back_link=back_link, sources=sources,
                                asset=_site.compute_asset_version(), head=_site.head_common("../../"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        versions = [sys.argv[1]]
    else:
        versions = [
            v for i, v in enumerate(RELEASE_HISTORY)
            if i + 1 < len(RELEASE_HISTORY)
            and (DATA_DIR / v / "heroes").exists()
            and (DATA_DIR / RELEASE_HISTORY[i + 1] / "heroes").exists()
        ]
    if not versions:
        print("No patch pairs with both heroes/ folders available — nothing to do.")
        print("Run fetch_stats.py / extract_patchnotes.py first to populate heroes/.")
        return 0
    print(f"Building silent-changes pages for {len(versions)} patch(es)...")
    for v in versions:
        html = build_page(v)
        if html is not None:
            (OUT_DIR / f"{v}.html").write_text(html, encoding="utf-8")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
