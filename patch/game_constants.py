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

# ---- Strength / Agility / Intelligence: today's values ----
HPREG_PER_STR = 0.1        # +0.1 HP regen per Strength
AS_PER_AGI = 1.0           # +1 attack speed per Agility
ARMOR_PER_AGI = 1 / 6      # 7.27 "Armor per agility increased slightly from 0.16 to 1/6"
MR_PER_INT = 0.1           # 7.33 "Intelligence now grants 0.1% base Magic Resistance per point"
DMG_PER_PRIMARY = 1.0      # Str/Agi/Int hero: +1 attack damage per point of the primary attribute

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
    ("7.07", "31.10.2017", 13, 14),
    ("7.20", "19.11.2018", 14, 12),
    ("7.36", "22.05.2024", 12, 11),
    ("7.39", "21.05.2025", 11, 12),
)
INT_REGEN_HIST = (
    ("7.07", "31.10.2017", 0.04, 0.05),
)
# Universal heroes: damage per point of EVERY attribute (the sum is floored before it is added).
UNIVERSAL_DMG_HIST = (
    ("7.33", "20.04.2023", 0.0, 0.6),    # "Universal heroes ... get 0.6 damage per point of each attribute"
    ("7.33c", "13.05.2023", 0.6, 0.7),   # "Universal Heroes damage per attribute increased from 0.6 to 0.7"
    ("7.38", "19.02.2025", 0.7, 0.45),   # "Universal Heroes' damage per attribute decreased from 0.7 to 0.45"
)

HP_PER_STR = float(STR_HP_HIST[-1][3])
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
    multiplier = at(PRIMARY_ATTRIBUTE_BONUS_HIST, patch) if primary else 1.0
    return at(STR_HP_HIST, patch) * multiplier


def for_js() -> dict:
    """Today's values for scripts.js (Hero Stats / Hero Lab embed them in the page; JS types no numbers)."""
    return {
        "hpStr": HP_PER_STR, "hprStr": HPREG_PER_STR, "mpInt": MANA_PER_INT, "mprInt": MANAREG_PER_INT,
        "armorAgi": ARMOR_PER_AGI, "mrInt": MR_PER_INT, "asAgi": AS_PER_AGI, "uniDmg": UNIVERSAL_DMG_PER_ATTR,
    }
