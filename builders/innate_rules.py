"""Hero innate rules = data/rules/hero_stat_innates.json + the game files of every newer patch.

The JSON holds the hand-checked history of each innate effect, verified against the game files up to
`_checked_version` (older snapshots are not always trustworthy: data/stats/7.41/heroes/ is a copy of 7.40c).
An effect whose numbers are plain AbilityValues of the hero's innate carries a "kv" map:

    "kv": {"factor": ["secondary_stat_bonus_pct", "value", 0.01]}
          entry field <- AbilityValues key, its "value" (or "hero_levelup") part, times a scale

load() reads those keys from data/stats/<v>/heroes/npc_dota_hero_<slug>.txt for every patch NEWER than
`_checked_version` and opens a new history entry wherever the game's number moves — a new patch needs no
edit. Effects without "kv" are guarded instead: tests/test_innate_rules_kv.py fails when the latest game
files change such an innate (or a hero gets a new one), naming what to re-check.

Hero Stats (Python + its embedded JSON for scripts.js) and Hero Lab read the rules through load()."""
from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
RULES_PATH = _HERE / "data" / "rules" / "hero_stat_innates.json"
STATS_DIR = _HERE / "data" / "stats"


def _vkey(v: str) -> tuple:
    from patch.game_constants import _vkey as key
    return key(v)


def stats_versions() -> list[str]:
    """Every patch with a stats snapshot, oldest first."""
    return sorted((p.name for p in STATS_DIR.iterdir() if (p / "heroes.json").exists()), key=_vkey)


@lru_cache(maxsize=None)
def innate_blocks(slug: str, version: str) -> dict:
    """{ability: KV block} of the hero's abilities flagged "Innate" "1" in that patch ({} without a file)."""
    from tools.slim_from_kv import load_kv
    from builders.site_common import hero_ability_blocks
    path = STATS_DIR / version / "heroes" / f"npc_dota_hero_{slug}.txt"
    if not path.exists():
        return {}
    blocks = hero_ability_blocks(load_kv(path))
    return {name: b for name, b in blocks.items()
            if isinstance(b, dict) and str(b.get("Innate", "")).strip() == "1"}


def _number(raw) -> float | None:
    """'30' / '+0.1' / '2 4 6' (first level) -> float."""
    tok = str(raw).strip().split()
    if not tok:
        return None
    try:
        return float(tok[0].lstrip("+"))
    except ValueError:
        return None


def kv_values(slug: str, ability: str, spec: dict, version: str) -> dict | None:
    """The entry fields `spec` maps, read from the game files of `version` (None if any is missing)."""
    block = innate_blocks(slug, version).get(ability)
    if not block:
        return None
    values = block.get("AbilityValues") or {}
    out = {}
    for field, (key, part, scale) in spec.items():
        node = values.get(key)
        if node is None:
            return None                               # the key itself is gone: stop following
        # a part Valve leaves out is 0 ("movespeed_pct" { "hero_levelup" "+1" } has no "value")
        raw = node.get(part, "0") if isinstance(node, dict) else (node if part == "value" else "0")
        num = _number(raw)
        if num is None:
            return None
        out[field] = round(num * scale, 10)
    return out


def _same(a: dict, b: dict) -> bool:
    return all(abs(float(a[k]) - float(b.get(k, float("nan")))) < 1e-9 for k in a)


def _extend(slug: str, ability: str, eff: dict, newer: list[str], checked: str) -> None:
    """Append a history entry for every newer patch whose game value differs from the open entry
    (the entry before it then ends at the previous patch)."""
    spec = eff["kv"]
    history = eff.get("history")
    if history is None:
        if eff.get("until"):
            return                                    # effect removed — nothing to follow
        entry_fields = {k: v for k, v in eff.items()
                        if k not in ("target", "formula", "source", "note", "kv", "history", "since", "until")}
        # an effect without history applies to every patch it is not gated from — keep that range
        open_entry = {"since": eff.get("since", "7.00"), **entry_fields}
        pending = [open_entry]
    else:
        if not history or history[-1].get("until"):
            return
        open_entry = history[-1]
        pending = None
    prev = checked
    for v in newer:
        vals = kv_values(slug, ability, spec, v)
        if vals is not None and not _same(vals, open_entry):
            open_entry["until"] = prev
            open_entry = {**{k: x for k, x in open_entry.items() if k != "until"}, "since": v, **vals}
            (pending if pending is not None else history).append(open_entry)
        prev = v
    if pending is not None and len(pending) > 1:
        eff["history"] = pending
        eff.update({k: pending[-1][k] for k in spec})   # readers of the effect itself get today's value


def load(versions: list[str] | None = None) -> dict:
    """The full rules dict (same shape as the JSON) with KV-derived history for patches after
    `_checked_version`. `versions` (oldest first) defaults to every stats snapshot."""
    rules = copy.deepcopy(_raw())
    checked = rules.get("_checked_version")
    versions = stats_versions() if versions is None else versions
    newer = [v for v in versions if checked and _vkey(v) > _vkey(checked)]
    if not newer:
        return rules
    for slug, hero in rules.get("heroes", {}).items():
        for eff in hero.get("effects", []):
            if eff.get("kv"):
                _extend(slug, eff.get("kv_ability") or hero["innate"], eff, newer, checked)
    return rules


@lru_cache(maxsize=1)
def _raw() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


# AbilityValues keys of an innate that look like a hero stat — a hero WITHOUT a rule whose innate gains one
# may now move a Hero Stats column (hp / mana / regen / armor / resist / attack speed / move speed / damage …).
_STAT_KEY = ("strength", "agility", "intellect", "intelligence", "all_stats", "attribute", "armor",
             "magic_resist", "health", "hp_regen", "mana", "regen", "attack_speed", "attackspeed",
             "move_speed", "movespeed", "movement_speed", "attack_range", "evasion", "damage")


def _hero_slugs(version: str) -> set[str]:
    d = STATS_DIR / version / "heroes"
    return {p.stem[len("npc_dota_hero_"):] for p in d.glob("npc_dota_hero_*.txt")} if d.is_dir() else set()


def _values(block: dict) -> dict:
    return {k: v for k, v in (block.get("AbilityValues") or {}).items()}


def review(old: str, new: str) -> list[str]:
    """What changed in the heroes' innates between two patches that the rules do NOT follow by themselves
    (each line says what to re-check). Empty = the rules are still right for `new`."""
    heroes = _raw().get("heroes", {})
    out = []
    for slug in sorted(_hero_slugs(new)):
        now, before = innate_blocks(slug, new), innate_blocks(slug, old)
        rule = heroes.get(slug)
        if rule:
            name = rule["innate"]
            if name not in now:
                out.append(f"{slug}: innate {name} is gone in {new} (now: {sorted(now) or 'none'}) — "
                           f"rewrite its rule in hero_stat_innates.json")
                continue
            followed = {spec[0] for eff in rule.get("effects", []) for spec in (eff.get("kv") or {}).values()}
            a, b = _values(before.get(name, {})), _values(now[name])
            changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k) and k not in followed)
            if changed:
                out.append(f"{slug}: {name} changed in {new} ({', '.join(changed)}) — check its rule")
            continue
        if not before and slug not in _hero_slugs(old):
            new_stats = sorted(k for blk in now.values() for k in _values(blk)
                               if any(w in k for w in _STAT_KEY))
            if new_stats:
                out.append(f"{slug}: new hero, innate {sorted(now)} has stat-like values {new_stats} — "
                           f"add a rule if it moves a Hero Stats column")
            continue
        if sorted(now) != sorted(before):
            out.append(f"{slug}: innate changed in {new}: {sorted(before)} -> {sorted(now)} — "
                       f"add a rule if it moves a Hero Stats column")
            continue
        added = sorted(k for name, blk in now.items() for k in _values(blk)
                       if k not in _values(before.get(name, {})) and any(w in k for w in _STAT_KEY))
        if added:
            out.append(f"{slug}: innate gained {added} in {new} — add a rule if it moves a Hero Stats column")
    return out
