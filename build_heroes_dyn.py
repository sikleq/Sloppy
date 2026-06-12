"""Build heroes_dyn.html — the Hero Dynamics matrix.

A matrix table: ROWS = every hero (icon + name, alphabetical), COLUMNS = every
patch (version + release date), and each CELL = that hero's patch-dynamics
"dyn-cell" for that patch (the same diamond-pill widget used on patch pages).
Lets you read at a glance how a hero was buffed/nerfed/reworked across the whole
patch history.

The actual table renderer lives in `dyn_matrix_common.save_dyn_matrix` — it is
ENTITY-AGNOSTIC and is reused as-is by `build_items_dyn.py` (Item Dynamics). This
file is just the hero configuration + entry point.

Data comes entirely from `_dynamics.json` (written by build_patch.py):
  - `patches`  : ordered newest-first list of {version, filename, date}
  - `entities` : per-entity tag tallies, keyed "hero|<slug>" / "item|<slug>"
  - `heroes`   : full alphabetical roster [{name, icon, key}]

Run AFTER build_patch.py (it needs the fresh _dynamics.json + site_meta.json):
    python build_patch.py
    python build_heroes_dyn.py
"""
from dyn_matrix_common import save_dyn_matrix
from build_heroes_stats import _load_raw_heroes, _extract_hero_block, _RAW_DEFAULTS, _raw_field
import json as _json
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _latest_stats_version() -> str:
    meta = _json.loads((_HERE / "data" / "site_meta.json").read_text(encoding="utf-8"))
    return meta["latest_patch_version"]


def _hero_attack_types() -> dict[str, dict[str, str]]:
    latest = _latest_stats_version()
    raw = _load_raw_heroes(latest)
    out = {}
    manifest = _json.loads((_HERE / "_dynamics.json").read_text(encoding="utf-8"))
    for rec in manifest.get("heroes", []):
        slug = rec.get("icon") or rec["key"].split("|", 1)[-1]
        if slug == "spirit_bear":
            out[slug] = {"attack_type": "melee"}
            continue
        hero = f"npc_dota_hero_{slug}"
        cap = str(_raw_field(raw, hero, "AttackCapabilities") or "")
        if not cap or cap == str(_RAW_DEFAULTS["AttackCapabilities"]):
            cap = _extract_hero_block(latest, hero).get("AttackCapabilities", cap)
        out[slug] = {"attack_type": "ranged" if "RANGED" in cap else "melee"}
    return out


def save_heroes_dyn_html():
    save_dyn_matrix(
        kind="hero",
        roster_key="heroes",
        out_file="heroes_dyn.html",
        page_title="Hero Dynamics",
        subtab="heroes_dyn",
        noun="Hero",
        icon_dir="icons/heroes",
        from_token="heroes_dyn",
        attack_filter=True,
        row_meta_by_slug=_hero_attack_types(),
        search_ph="Search heroes — anci, aba, brood…",
        blurb=(
            "Every hero down the side, every patch across the top. Each diamond "
            "is that hero’s balance-change summary for that patch — hover it for "
            "the buff/nerf/rework breakdown, click to jump to the hero on that "
            "patch page. Hover a patch column for its release date. Empty diamonds "
            "mean the hero was untouched. The coloured <strong>tag chips</strong> "
            "drop a tag from the diamonds (it still shows on hover); the <strong>search</strong> "
            "box filters heroes by name — comma-separate for several (partial names "
            "work: <em>anci, aba, brood</em>)."),
    )


if __name__ == "__main__":
    save_heroes_dyn_html()
