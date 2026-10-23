"""Engine constants of the hero attributes — the ONE place they are typed in.

They live in the game DLL, not in any KV file we read, so they cannot be loaded like hero or item values.
The game repeats them in its own tooltips (data/dota_english.txt: DOTA_HeroStats_Strength_Desc,
_Agility_Desc, _Intelligence_Desc, DOTA_Loadout_PrimaryAttribute_Universal_Tooltip):
tests/test_game_constants.py fails the day a tooltip disagrees with a value here, so a Valve change
cannot slip by. Hero Stats, Hero Lab (both in Python and, via for_js(), in scripts.js), Mana Items,
the patch pages' attribute cards and the Hero Changes summaries all read these names.

A history is ((patch, release date, old, new), ...), oldest first; the LAST row is the value in the game
today, so a Valve change is one new row. Sources: data/patchnotes_english.txt, Liquipedia changelogs."""
import re

# ---- Strength / Agility / Intelligence: today's values are the LAST row of each history below ----
AS_PER_AGI = 1.0           # +1 attack speed per Agility (every patch; the 7.13–7.20 primary bonus is below)
DMG_PER_PRIMARY = 1.0      # Str/Agi/Int hero: +1 attack damage per point of the primary attribute

# Each secondary bonus by patch (owner 2026-10-22, after PR #14's HP history). Sources: Valve's 7.13 table
# ("Old Strength / New Strength ..."), 7.20 tooltips (its General notes are missing from patchnotes_english.txt:
# DOTA_HeroStats_*_Desc switch from "% Regen Amplification" to flat regen there), 7.26, 7.27 and 7.33 notes.
STR_HPREG_HIST = (                                  # flat HP regen per Strength
    # 0.1 from 7.20 (its notes; server.dll of 7.20 … 7.41 all hold 0.1) — the "0.09" of the 7.20–7.40c tooltips
    # was a text error (owner 2026-10-22, DLL check)
    ("7.20", "19.11.2018", 0.0, 0.1),
)
STR_HPREG_AMP_HIST = (                              # % HP regen amplification per Strength (before 7.20)
    ("7.13", "12.04.2018", 0.71, 0.55),
    ("7.20", "19.11.2018", 0.55, 0.0),
)
STR_MR_HIST = (                                     # % magic resistance per Strength
    ("7.13", "12.04.2018", 0.0, 0.08),
    ("7.26", "17.04.2020", 0.08, 0.0),               # "Attributes no longer provide Magic Resistance ... for Strength"
)
AGI_ARMOR_HIST = (                                  # armor per Agility
    ("7.13", "12.04.2018", 0.17, 0.16),
    ("7.27", "28.06.2020", 0.16, 1 / 6),             # "Armor per agility increased slightly from 0.16 to 1/6"
)
AGI_MS_HIST = (                                     # % movement speed per Agility
    ("7.13", "12.04.2018", 0.06, 0.05),
    ("7.26", "17.04.2020", 0.05, 0.0),               # "... Movement Speed for ... Agility"
)
INT_MR_HIST = (                                     # % magic resistance per Intelligence
    ("7.13", "12.04.2018", 0.15, 0.0),               # 7.13 Old Intelligence "+0.15% Magic Resistance"; New: none
    ("7.33", "20.04.2023", 0.0, 0.1),                # "Intelligence now grants 0.1% base Magic Resistance per point"
)
# Physical damage reduction by armor: formula 0 = 0.06·A / (1 + 0.06·|A|), 1 = 0.052·A / (0.9 + 0.048·|A|),
# 2 = 0.05·A / (1 + 0.05·|A|). 7.20 (blog notes, not in the game's patchnotes file): "Changed the Armor formula to:
# ( 0.052 * Armor ) / ( 0.9+ 0.048 * Armor)"; 7.27: "Armor formula is now ( Armor * 0.06 / ( 1 + Armor * 0.06 )".
# The 0.05 before 7.20 is server.dll's (build of 17.11.2018; 7.20 / 7.26c / 7.27 checked too, owner 2026-10-22).
ARMOR_FORMULA_HIST = (
    ("7.20", "19.11.2018", 2, 1),
    ("7.27", "28.06.2020", 1, 0),
)
_ARMOR_FORMULAS = {0: (0.06, 1.0, 0.06), 1: (0.052, 0.9, 0.048), 2: (0.05, 1.0, 0.05)}


def armor_reduction(armor: float, patch: str | None = None) -> float:
    """The share of physical damage armor blocks in that patch (negative armor: negative share)."""
    a, b, c = _ARMOR_FORMULAS[int(at(ARMOR_FORMULA_HIST, patch))]
    return a * armor / (b + c * abs(armor))


STR_STATUS_RES_HIST = (                             # % status resistance per Strength (shown in history only)
    ("7.13", "12.04.2018", 0.15, 0.0),               # 7.13 "Removed Status Resistance as a Strength based attribute bonus"
)
INT_SPELL_AMP_HIST = (                              # % spell amplification per Intelligence (shown in history only)
    ("7.26", "17.04.2020", 0.07, 0.0),               # "Attributes no longer provide ... Spell Amplification ..."
)
INT_REGEN_AMP_HIST = (                              # % mana regen amplification per Intelligence (before 7.20)
    ("7.13", "12.04.2018", 2.0, 1.8),
    ("7.20", "19.11.2018", 1.8, 0.0),
)

# Maximum health per Strength. Valve's 7.13, 7.21 and 7.33 General notes
# are preserved in data/patchnotes_english.txt.
STR_HP_HIST = (
    ("7.13", "12.04.2018", 20, 18),
    ("7.21", "29.01.2019", 18, 20),
    ("7.33", "20.04.2023", 20, 22),
)
# From 7.13 until 7.21, primary attributes granted 25% more secondary
# benefits. For HP this applies only to Strength heroes, not to base HP.
PRIMARY_ATTRIBUTE_BONUS_HIST = (
    ("7.13", "12.04.2018", 1.0, 1.25),
    ("7.21", "29.01.2019", 1.25, 1.0),
)

# Intelligence history (Mana Items history cells use the value in effect at each patch).
INT_MANA_HIST = (
    # 12 from 7.07 on: Valve's 7.13 table ("Old Intelligence: 12 Mana"), the tooltips and server.dll of 11 builds
    # 2018–2026 (7.19 … 7.41). The old rows 13 -> 14 (7.07), 14 -> 12 (7.20), 12 -> 11 (7.36) and 11 -> 12 (7.39)
    # had no source and the game never had them (owner 2026-10-22, DLL check)
    ("7.07", "31.10.2017", 11, 12),                  # 7.06 had 11 (Liquipedia Intelligence changelog)
)
INT_REGEN_HIST = (                                  # flat mana regen per Intelligence: from 7.20 (amplification before)
    ("7.20", "19.11.2018", 0.0, 0.05),
)
# Universal heroes: damage per point of EVERY attribute (the sum is floored before it is added).
UNIVERSAL_DMG_HIST = (
    ("7.33", "20.04.2023", 0.0, 0.6),    # "Universal heroes ... get 0.6 damage per point of each attribute"
    ("7.33c", "13.05.2023", 0.6, 0.7),   # "Universal Heroes damage per attribute increased from 0.6 to 0.7"
    ("7.38", "19.02.2025", 0.7, 0.45),   # "Universal Heroes' damage per attribute decreased from 0.7 to 0.45"
)

HP_PER_STR = float(STR_HP_HIST[-1][3])
HPREG_PER_STR = float(STR_HPREG_HIST[-1][3])
ARMOR_PER_AGI = float(AGI_ARMOR_HIST[-1][3])
MR_PER_INT = float(INT_MR_HIST[-1][3])
MANA_PER_INT = float(INT_MANA_HIST[-1][3])
MANAREG_PER_INT = float(INT_REGEN_HIST[-1][3])
UNIVERSAL_DMG_PER_ATTR = float(UNIVERSAL_DMG_HIST[-1][3])


def _vkey(v: str) -> tuple:
    """'7.36' < '7.36a' < '7.37' — numeric major/minor, then the letter."""
    m = re.match(r"(\d+)\.(\d+)([a-z]?)", v or "")
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, "")


def at(hist, patch: str | None = None) -> float:
    """The value IN EFFECT at `patch` (today's value when patch is None)."""
    if not patch:
        return float(hist[-1][3])
    val = float(hist[0][2])
    for p, _date, _old, new in hist:
        if _vkey(p) <= _vkey(patch):
            val = float(new)
    return val


def hp_per_strength(patch: str | None = None, *, primary: bool = False) -> float:
    """HP granted by one Strength point at a patch, including primary bonuses."""
    return per_point(STR_HP_HIST, patch, primary=primary)


def per_point(hist, patch: str | None = None, *, primary: bool = False) -> float:
    """One point's secondary bonus at a patch; `primary` — the hero's primary attribute is the one giving it
    (7.13–7.20: +25% to every bonus of the primary attribute, items' points too)."""
    multiplier = at(PRIMARY_ATTRIBUTE_BONUS_HIST, patch) if primary else 1.0
    return at(hist, patch) * multiplier


# What one point of each attribute gives, for the Hero Stats header tooltips (owner 2026-10-22): (label, history,
# unit). A new row in a history above shows up there by itself. "attr" = the rules of the attribute types.
ATTRIBUTE_RULES = {
    "str": (("HP", STR_HP_HIST, ""), ("HP regen", STR_HPREG_HIST, ""),
            ("HP regen amplification", STR_HPREG_AMP_HIST, "%"), ("Magic resistance", STR_MR_HIST, "%"),
            ("Status resistance", STR_STATUS_RES_HIST, "%")),
    "agi": (("Armor", AGI_ARMOR_HIST, ""), ("Movement speed", AGI_MS_HIST, "%")),
    "int": (("Mana", INT_MANA_HIST, ""), ("Mana regen", INT_REGEN_HIST, ""),
            ("Mana regen amplification", INT_REGEN_AMP_HIST, "%"), ("Magic resistance", INT_MR_HIST, "%"),
            ("Spell amplification", INT_SPELL_AMP_HIST, "%")),
    "attr": (("Primary attribute bonus", PRIMARY_ATTRIBUTE_BONUS_HIST, "pct-mult"),
             ("Universal damage per attribute", UNIVERSAL_DMG_HIST, "")),
}


def _show(v, unit):
    if unit == "pct-mult":                           # 1.25 -> "+25%"
        return f"+{round((v - 1) * 100):g}%"
    return f"{round(v, 3):g}{unit}"


_ATTR_TITLE = {"str": "Per Strength", "agi": "Per Agility", "int": "Per Intelligence", "attr": "Attributes"}


def attribute_today(key: str) -> str:
    """The tooltip header: what one point gives today, one value per line so the tip stays narrow (owner
    2026-10-23: a one-line header made the window too wide) — 'Per Strength<span …>22 HP</span>…'."""
    now = [f"{_show(hist[-1][3], unit)} {label}" for label, hist, unit in ATTRIBUTE_RULES[key]
           if hist[-1][3] and unit != "pct-mult"]
    if key == "agi":
        now.append(f"{AS_PER_AGI:g} Attack speed")
    if key == "attr":
        now = [f"Primary: +{DMG_PER_PRIMARY:g} damage per point",
               f"Universal: +{UNIVERSAL_DMG_PER_ATTR:g} per point of each"]
    return _ATTR_TITLE[key] + "".join(f'<span class="tip-now">{v}</span>' for v in now)


def attribute_history(key: str) -> str:
    """The stat-hist-tip payload of one attribute: 'patch|date|F|label|old|new|hi;…', oldest patch first, the
    rows of one patch together (scripts.js groups them under one patch header)."""
    rows = [(_vkey(p), p, d, label, _show(o, unit), _show(n, unit))
            for label, hist, unit in ATTRIBUTE_RULES[key] for p, d, o, n in hist]
    rows.sort(key=lambda r: r[0])
    return ";".join(f"{p}|{d}|F|{label}|{o}|{n}|hi" for _k, p, d, label, o, n in rows)


# column -> the engine histories its Starting value depends on (Hero Stats: a change of one of them is that
# patch's own change, never shifted to an earlier hero note)
RULES_OF_COLUMN = {
    "hp": (STR_HP_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "hpr": (STR_HPREG_HIST, STR_HPREG_AMP_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "mp": (INT_MANA_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "mpr": (INT_REGEN_HIST, INT_REGEN_AMP_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "armor": (AGI_ARMOR_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "armor_pct": (AGI_ARMOR_HIST, ARMOR_FORMULA_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "mr": (STR_MR_HIST, INT_MR_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "aspd": (PRIMARY_ATTRIBUTE_BONUS_HIST,),
    "t_per_attack": (PRIMARY_ATTRIBUTE_BONUS_HIST,),
    "ms": (AGI_MS_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "ehp_phys": (STR_HP_HIST, AGI_ARMOR_HIST, ARMOR_FORMULA_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
    "ehp_mag": (STR_HP_HIST, STR_MR_HIST, INT_MR_HIST, PRIMARY_ATTRIBUTE_BONUS_HIST),
}


def for_js() -> dict:
    """Today's values for scripts.js (Hero Stats / Hero Lab embed them in the page; JS types no numbers)."""
    return {
        "hpStr": HP_PER_STR, "hprStr": HPREG_PER_STR, "mpInt": MANA_PER_INT, "mprInt": MANAREG_PER_INT,
        "armorAgi": ARMOR_PER_AGI, "mrInt": MR_PER_INT, "asAgi": AS_PER_AGI, "uniDmg": UNIVERSAL_DMG_PER_ATTR,
    }
