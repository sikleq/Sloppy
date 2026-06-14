"""Stats database loading and lookup helpers."""

import json as _json
import os as _os
import re

from .images import HERO_SLUG, ITEM_SLUG


def _load_stats_db():
    db_h, db_i, db_u = {}, {}, {}
    base = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "stats")
    if not _os.path.isdir(base):
        return db_h, db_i, db_u
    for ver in _os.listdir(base):
        vdir = _os.path.join(base, ver)
        if not _os.path.isdir(vdir):
            continue
        for fname, target in (("heroes.json", db_h),
                              ("items.json",  db_i),
                              ("units.json",  db_u)):
            fp = _os.path.join(vdir, fname)
            if _os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    target[ver] = _json.load(f)
    return db_h, db_i, db_u

_STATS_H, _STATS_I, _STATS_U = _load_stats_db()


def _load_item_classes(version):
    """Parse data/stats/<version>/items.txt -> (neutral, obsolete, present) sets of
    game slugs ('item_<x>'). Authoritative item classification for items_dyn,
    straight from Valve's KV (no patch-note dependency):
      - neutral item     : "ItemIsNeutralActiveDrop" "1"
      - removed/obsolete  : "IsObsolete" "1"  (kept in the file for old replays,
                            but no longer in the game — e.g. Cornucopia)
      - enchantments are detected by the item_enhancement_ prefix (caller side).
      - regular item      : present, not neutral, not obsolete.
    'current' (still in the game) = present AND not obsolete. NOTE: neutral items
    carry ItemPurchasable "0" too, so DON'T use purchasable as the removed signal.
    Returns empty sets if the file is absent (degrade gracefully)."""
    path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "stats", version, "items.txt")
    present, neutral, obsolete = set(), set(), set()
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return neutral, obsolete, present
    cur = None
    name_re = re.compile(r'^\s*"(item_[a-z0-9_]+)"\s*$')
    for ln in lines:
        m = name_re.match(ln)
        if m:
            cur = m.group(1)
            present.add(cur)
            continue
        if not cur:
            continue
        if 'ItemIsNeutralActiveDrop' in ln and '"1"' in ln:
            neutral.add(cur)
        if 'IsObsolete' in ln and '"1"' in ln:
            obsolete.add(cur)
    return neutral, obsolete, present


def _stat_h_raw(npc_key: str, field: str, version: str):
    """Look up `field` for `npc_key` at `version`; fall back to npc_dota_hero_base
    when the hero doesn't override (Valve KV inheritance)."""
    bucket = _STATS_H.get(version, {})
    val = bucket.get(npc_key, {}).get(field)
    if val is None:
        val = bucket.get("npc_dota_hero_base", {}).get(field)
    return val


def stat_h(hero_display: str, field: str, version: str):
    """
    Возвращает числовое значение стата героя в указанном патче или None.
    Если у героя нет явного значения в KV — берёт из npc_dota_hero_base
    (Valve использует наследование, скрейпер выгребает только явные поля).
    """
    raw_slug = HERO_SLUG.get(hero_display,
                              hero_display.lower().replace(" ", "_").replace("'", ""))
    return _stat_h_raw("npc_dota_hero_" + raw_slug, field, version)


def stat_i(item_display: str, field: str, version: str):
    """
    Возвращает числовое значение стата предмета в указанном патче или None.

    item_display — отображаемое имя (как в ITEM_SLUG), например "Blink Dagger"
    field        — ключ из items.txt, например "ItemCost", "ItemCooldown"
    version      — патч, например "7.41"
    """
    raw_slug = ITEM_SLUG.get(item_display,
                              item_display.lower().replace(" ", "_").replace("'", ""))
    item_key = "item_" + raw_slug
    return _STATS_I.get(version, {}).get(item_key, {}).get(field)


def _patch_sort_key(v: str):
    """Sort key for patch versions like '7.41', '7.41b'. Returns (major, minor, suffix)."""
    parts = v.split(".")
    major = int(parts[0]) if parts[0].isdigit() else 0
    rest = parts[1] if len(parts) > 1 else "0"
    num = ""
    suf = ""
    for c in rest:
        if c.isdigit():
            num += c
        else:
            suf += c
    return (major, int(num) if num else 0, suf)


def _prev_change_patch(db: dict, key_with_prefix: str, field: str, before_patch: str):
    """Returns the patch in which the value at `before_patch` was first set
    (i.e. the most recent earlier patch where the value differs from the
    target, +1 step). None if value never changed within known history.
    Falls back to npc_dota_hero_base / item_base when the entity doesn't
    override the field (Valve KV inheritance)."""
    base_key = "npc_dota_hero_base" if key_with_prefix.startswith("npc_dota_hero_") else None

    def _at(v):
        bucket = db.get(v, {})
        val = bucket.get(key_with_prefix, {}).get(field)
        if val is None and base_key:
            val = bucket.get(base_key, {}).get(field)
        return val

    target = _at(before_patch)
    if target is None:
        return None
    versions = sorted([v for v in db
                       if _patch_sort_key(v) <= _patch_sort_key(before_patch)],
                      key=_patch_sort_key)
    last_with_target = before_patch
    for v in reversed(versions[:-1]):
        if _at(v) != target:
            return last_with_target
        last_with_target = v
    # No transition found — value held since the oldest patch in our DB.
    # Signal this with a "<oldest" marker so the caller can render "before X".
    return f"<{versions[0]}" if versions else last_with_target


def prev_change_patch_h(hero_display: str, field: str, before_patch: str):
    raw_slug = HERO_SLUG.get(hero_display,
                              hero_display.lower().replace(" ", "_").replace("'", ""))
    return _prev_change_patch(_STATS_H, "npc_dota_hero_" + raw_slug, field, before_patch)


def prev_change_patch_i(item_display: str, field: str, before_patch: str):
    raw_slug = ITEM_SLUG.get(item_display,
                              item_display.lower().replace(" ", "_").replace("'", ""))
    return _prev_change_patch(_STATS_I, "item_" + raw_slug, field, before_patch)


def bstat_h(hero_display: str, field: str, patch_before: str, delta,
            l: bool = False):
    """
    Бейдж для изменения стата героя на delta от патча patch_before.

    Автоматически берёт старое значение из БД и вычисляет новое.
    delta — число: положительное = увеличение, отрицательное = уменьшение.

    Пример:
        # "Base Armor decreased by 1" в 7.41a, до этого патча было 7.41
        W(li("Base Armor decreased by 1", bstat_h("Doom", "ArmorPhysical", "7.41", -1)))
    """
    from .badges import b, t
    old = stat_h(hero_display, field, patch_before)
    if old is None:
        return t("NERF") if delta < 0 else t("BUFF")
    new = old + delta
    return b(old, new, l=l)


def bstat_i(item_display: str, field: str, patch_before: str, delta,
            l: bool = False):
    """Аналог bstat_h для предметов."""
    from .badges import b, t
    old = stat_i(item_display, field, patch_before)
    if old is None:
        return t("NERF") if delta < 0 else t("BUFF")
    new = old + delta
    return b(old, new, l=l)


def stat_u(unit_key: str, field: str, version: str):
    """Unit stat lookup. `unit_key` is the full npc key, e.g.
    'npc_dota_beastmaster_boar'. Returns None when missing."""
    return _STATS_U.get(version, {}).get(unit_key, {}).get(field)


def prev_change_patch_u(unit_key: str, field: str, before_patch: str):
    return _prev_change_patch(_STATS_U, unit_key, field, before_patch)


def bstat_u(unit_key: str, field: str, patch_before: str, delta,
            l: bool = False):
    """Same as bstat_h/_i but for summons / neutral creeps."""
    from .badges import b, t
    old = stat_u(unit_key, field, patch_before)
    if old is None:
        return t("NERF") if delta < 0 else t("BUFF")
    new = old + delta
    return b(old, new, l=l)
