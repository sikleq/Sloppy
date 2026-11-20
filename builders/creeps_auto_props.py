"""The Neutral Abilities table's cells read from the game files, not typed by hand (owner 2026-11-20: "мы разве
автоматически из патчей и файлов не должны подтягивать, чтобы всё на сайте автоматически было?").

Property: what an ability does, from its KV keys, which Valve names alike across abilities ("stun_duration",
"armor_reduction", "silence_duration" …); when no key tells it, the first clause of the game's own description.
Damage and Duration: from more of the keys the abilities use. builders/creeps_abilities.ABIL_MANUAL keeps only what
the files can't say (Wildkin's Tornado, whose damage lives in another unit; a toggle's mana per second …) and wins
over these cells.
"""
import re

# (key regex, the property's words; "{v}" = the key's values as levels, "2/3/4/5"); the first rules that match win,
# up to three — the table has three Property columns
_KEY_RULES = (
    (r"^av_(?:hero_|non_hero_)?stun_duration$", "Stun"),
    (r"^av_bash_chance$|^av_bash_damage$", "Bash"),
    (r"^av_silence_duration$|^av_(?:hero_)?silence$", "Silence"),
    (r"^av_break_duration$", "Break"),
    (r"^av_disarm_duration$", "Disarm"),
    (r"^av_hex_duration$", "Hex"),
    (r"^av_root_duration$|^av_entangle_duration$", "Root"),
    (r"^av_armor_reduction$", "Armor reduction {v}"),
    (r"^av_armor_bonus$|^av_bonus_armor$", "Armor bonus {v}"),
    (r"^av_magic_resistance_reduction$", "Magic resistance reduction {v}"),
    (r"^av_movespeed_slow$", "Slow {v}%"),
    (r"^av_(?:movement_)?slow(?:_pct)?$|^av_move_slow$", "Slow"),
    (r"^av_(?:health_)?restoration_reduction$|^av_heal(?:th_regen)?_reduction(?:_pct)?$", "Health restoration −{v}%"),
    (r"^av_lifesteal(?:_pct)?$", "Lifesteal {v}%"),
    (r"^av_(?:heal|heal_amount)$", "Heal {v}"),
    (r"^av_cleave_damage(?:_pct)?$", "Cleave {v}%"),
    (r"^av_crit_(?:chance|multiplier)$", "Critical strike"),
    (r"^av_evasion$", "Evasion {v}%"),
    (r"^av_mana_burn$|^av_burn_amount$", "Mana burn {v}"),
    (r"^av_purge|^av_dispel", "Dispel"),
)
_AREA_KEYS = re.compile(r"^av_(?:radius|impact_radius|aoe)$")
_AREA_WORDS = {"Stun", "Silence", "Slow", "Break", "Disarm", "Root"}
# a key worth zero is no effect ("av_slow": "0" on Eggstremism)
_ZERO = re.compile(r"^[\s0.\-]*$")
_DAMAGE_KEYS = ("av_damage", "AbilityDamage", "av_base_damage", "av_flop_damage", "av_slam_damage",
                "av_impact_damage", "av_explosion_damage")
# the stun first: "av_duration" 1.0 of Hurl Big Boulder is not how long the target is stunned (2)
_DURATION_KEYS = ("av_stun_duration", "av_duration", "AbilityDuration", "av_silence_duration", "av_slow_duration",
                  "av_armor_reduction_duration", "av_debuff_duration", "av_buff_duration")
# when no key tells it: the description's own verb (Eggstremism "damaging and silencing nearby enemies")
_DESC_RULES = ((r"\bstun", "Stun"), (r"\bsilenc", "Silence"), (r"\bdisarm", "Disarm"), (r"\broot", "Root"),
               (r"\bbreak\b|\bbroken\b", "Break"), (r"\bslow", "Slow"))


def _levels(v):
    vals = str(v).split()
    return "/".join(f"{float(x):g}" for x in vals) if vals else ""


def auto_effects(fields, description=""):
    """Up to three Property texts for an ability's KV `fields` ({"av_radius": "300", …}) and its game description."""
    out = []
    keys = [k for k, v in fields.items() if not _ZERO.match(str(v))]
    area = any(_AREA_KEYS.match(k) for k in keys)
    for rx, words in _KEY_RULES:
        hit = next((k for k in keys if re.match(rx, k)), None)
        if not hit:
            continue
        text = words.format(v=_levels(fields[hit]))
        if text.split(" ")[0] in _AREA_WORDS and area and not text.endswith("%"):
            text += " in an area"
        if text not in out:
            out.append(text)
        if len(out) == 3:
            break
    for rx, word in _DESC_RULES if description else ():
        if len(out) < 3 and re.search(rx, description, re.I) and not any(o.startswith(word) for o in out):
            out.append(word + (" in an area" if area else ""))
    if not out and description:
        first = re.split(r"(?<=[.!?])\s|,\s", re.sub(r"<[^>]+>|%[^%]*%", "", description).strip())[0].rstrip(".")
        if first:
            out.append(first if len(first) <= 70 else first[:67].rsplit(" ", 1)[0] + "…")
    return out
