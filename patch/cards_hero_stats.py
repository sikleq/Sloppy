"""The hero stat card: the base stats and attribute gains a patch changed, one card per hero (render_hs_card), and its per-page cache. Split out of patch/elements.py (audit 2026-10-26 #8)."""

import re

from .state import _State, page_cache
from .elements import _DMG_ROW_RE, info_tip


# ---- A hero's attack damage: starting damage + damage gain per level (owner 2026-09-28) ----
# 7.38 lowered the Universal damage per attribute 0.7 -> 0.45 and raised base damage and attribute gains to make
# up for it: "Base Damage increased by 26" (+650%) alone meant nothing. The damage rows of such a hero (base
# damage, damage at level 1 / 30, damage gain per level) become two rows, "Starting damage" and "Damage gain per
# level", each with its own tag; the old rows stay in the page hidden (weights as before). Attribute rows stay rows.
_HS_CARDS = page_cache({})      # "<ek>|<pv>" -> {"hero", "before", "after", "valve": {1: ..., 30: ..., "gain": ...}}


_HS_GAIN_VALVE_RE = re.compile(r"damage gain per level \w+ from \+?([\d.]+) to \+?([\d.]+)", re.I)


# Valve writes "decreased by 36 (from 189-195 to 153-159)", "decreased by 51-49 (from …)" (min and max moved
# apart: Sand King, Mirana, Marci 7.38), "rescaled from 46-54 to 45-55" and, in 7.40, an en dash (Spectre)
_HS_DMG_VALVE_RE = re.compile(r"damage at level (1|30) (?:\w+ by \d+(?:[-–]\d+)? \(from|rescaled from) "
                              r"(\d+)[-–](\d+) to (\d+)[-–](\d+)", re.I)


def hero_stat_card(before=None):
    """Called right after the GENERAL ul_open() of a hero block. `before` = the patch compared against (the
    previous one by default). Drawn when the page is saved (render_hs_card), after the rows under it have been
    matched: they are hidden."""
    from .hero_stats import attrs_changed
    from .weights import _prev_version
    ek, pv, hero = _State.current_entity_key or "", _State.current_patch_version, _State.current_hero
    before = before or _prev_version(pv)
    if not (ek.startswith("hero|") and pv and hero and before and attrs_changed(hero, before, pv)):
        return ""
    key = f"{ek}|{pv}"
    _HS_CARDS[key] = {"hero": hero, "before": before, "after": pv, "valve": {}}
    _State.hs_card = {"ek": ek, "pv": pv, "key": key}
    return f"<!--HSCARD:{key}-->"


def _hs_covered(text, tags):
    """A GENERAL damage row the two damage rows show: base damage, damage at level 1 / 30 and damage gain per
    level (hidden; its tag still counts for weights, `tags` unused here). Valve's level-1 / level-30 damage and
    gain per level are kept: the rows and their (?) show them as Valve stated them."""
    card = getattr(_State, "hs_card", None)
    if not card or (card["ek"], card["pv"]) != (_State.current_entity_key, _State.current_patch_version):
        return False
    plain = re.sub(r"<[^>]+>", " ", re.sub(r"<!--TIP-->.*?<!--/TIP-->", " ", text, flags=re.S))
    plain = re.sub(r"\s+", " ", plain).strip()
    rec = _HS_CARDS[card["key"]]
    m = _HS_DMG_VALVE_RE.search(plain)
    if m:
        rec["valve"][int(m.group(1))] = ((int(m.group(2)), int(m.group(3))), (int(m.group(4)), int(m.group(5))))
    g = _HS_GAIN_VALVE_RE.search(plain)
    if g:                                            # Valve's own damage gain per level (3.6 -> 2.7)
        rec["valve"]["gain"] = (float(g.group(1)), float(g.group(2)))
    # only the damage rows: the attribute rows and a main attribute change stay rows (owner 2026-09-28)
    return bool(m or _DMG_ROW_RE.match(plain))


def _hs_damage(rec, old, new, level):
    """(old (min, max), new (min, max)) at level 1 or 30: Valve's own figures when the notes state them, else
    the game files'. Level 30 counts all 7 Attribute Bonus levels, as Valve's notes do ("match Valve")."""
    from .hero_stats import damage_at
    if rec["valve"].get(level):
        return rec["valve"][level]
    at = lambda st, ver: tuple(int(x + 1e-9) for x in damage_at(st, ver, level, bonus=level == 30))
    return at(old, rec["before"]), at(new, rec["after"])


_HS_CHIPS = {"buff": '<span class="badge buff-text" data-tag="buff" data-overall="buff">BUFF</span>',
             "nerf": '<span class="badge nerf-text" data-tag="nerf" data-overall="nerf">NERF</span>',
             "misc": '<span class="badge misc" data-tag="misc">MISC</span>'}


def _hs_tag(badge):
    rule = re.search(r'data-overall="(\w+)"', badge)
    return rule.group(1) if rule and rule.group(1) in ("buff", "nerf") else "misc"


def _hs_row(name, before, after, badge, tail=""):
    """One row "<name> increased from A to B" with its own chip by the direction of its own number."""
    tag = _hs_tag(badge)
    verb = {"buff": "increased", "nerf": "decreased"}.get(tag, "changed")
    return (f'<li data-tag="{tag}" class="li-bg hs-dmg-li">{_HS_CHIPS[tag]}<span class="row-text">{name} {verb} '
            f'from {before} to {after}{tail}</span>{badge}</li>')


def render_hs_card(key):
    """TWO rows in place of the hero's damage rows (owner 2026-09-28: one row could not carry one tag when the
    start went up and the growth went down, Abaddon 7.38): "Starting damage increased from 40–50 to 50–60" and
    "Damage gain per level decreased from 3.6 to 2.7", each with its own % and chip. No table by level: the two
    numbers already say it (owner 2026-09-28); the damage at level 30 and what damage is made of (damage per
    attribute, base damage) are in the (?). A number that did not change has no row. Attribute rows stay rows."""
    from .badges import b
    from .hero_stats import damage_at, hero_stats, universal_multiplier
    rec = _HS_CARDS.get(key)
    if not rec:
        return ""
    old, new = hero_stats(rec["hero"], rec["before"]), hero_stats(rec["hero"], rec["after"])
    avg = lambda p: (p[0] + p[1]) / 2
    (o1, n1), (o30, n30) = _hs_damage(rec, old, new, 1), _hs_damage(rec, old, new, 30)
    # Valve's own per-level figures when the notes state them, else the game files' rounded to 0.1
    model = lambda st, ver: round(damage_at(st, ver, 2)[0] - damage_at(st, ver, 1)[0], 1)
    per_o, per_n = rec["valve"].get("gain") or (model(old, rec["before"]), model(new, rec["after"]))
    s1, s2 = f"{o1[0]}–{o1[1]}", f"{n1[0]}–{n1[1]}"
    g1, g2 = f"{per_o:.1f}", f"{per_n:.1f}"
    notes = []
    if "all" in (old["primary"], new["primary"]):
        mo = universal_multiplier(rec["before"]) if old["primary"] == "all" else None
        mn = universal_multiplier(rec["after"]) if new["primary"] == "all" else None
        if mo and mn and mo != mn:
            notes.append(f"Universal heroes: {mo:g} → {mn:g} damage per attribute")
    if (old["dmg_min"], old["dmg_max"]) != (new["dmg_min"], new["dmg_max"]):
        notes.append(f'Base damage {old["dmg_min"]:g}–{old["dmg_max"]:g} → {new["dmg_min"]:g}–{new["dmg_max"]:g}'
                     + (" makes up for it" if notes else ""))
    if o1 == n1:                                     # Batrider 7.38: the start stayed, only the growth moved
        notes.append(f"Starting damage unchanged at {s1}")
    if g1 == g2:
        notes.append(f"Damage gain per level unchanged at {g1}")
    pct30 = round((avg(n30) - avg(o30)) / avg(o30) * 100)
    notes.append(f"Damage at level 30: {o30[0]}–{o30[1]} → {n30[0]}–{n30[1]} ({pct30:+d}%), with all 7 Attribute "
                 f"Bonus levels, as Valve counts it")
    tip = f'<span class="li-tail">{info_tip(*notes)}</span>'
    start = (("Starting damage", s1, s2, b(avg(o1), avg(n1))),) if o1 != n1 else ()
    gain = (("Damage gain per level", g1, g2, b(per_o, per_n)),) if g1 != g2 else ()
    shown = start + gain or (("Starting damage", s1, s2, b(avg(o1), avg(n1))),)
    # each row only its own tag: the hidden rows' tags (Base Damage +26 = BUFF) do not put a NERF row under BUFF;
    # a hidden row never keeps a block on screen (scripts.js rowOnScreen). The last row carries the (?).
    return "".join(_hs_row(*row, tail=tip if i == len(shown) - 1 else "") for i, row in enumerate(shown))
