"""Audit of every Aghanim's Scepter / Shard text the generator builds (patch/aghs_text.py), in every patch of the
game-files store (7.08 -> now; owner 2026-10-25: "мы должны решать такое и добыть все данные").

Two checks per patch:
1. a number the upgrade sets (special_bonus_<kind>, "RequiresScepter" / "RequiresShard") that the game labels must be
   in the text;
2. every hero's upgrade must have a text on at least one of its abilities (the flag sits on one ability, the text
   often on another: Thundergod's Wrath -> Nimbus, Omnislash -> Swift Slash).
Abilities with no tooltip at all are leftovers in the files and are skipped. The game's own broken tooltips, checked by
hand, are listed in outputs/aghs_valve_gaps.json ({"<ability> <kind>": "why"}) — local only, like every finding about
the game we keep out of the public repo. Exit 1 on anything else. ~2-4 minutes (it reads 118 builds).

    python scripts/audit/check_aghs_texts.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from builders.silent import parse_kv  # noqa: E402
from patch.ability_kv import _hero_blocks  # noqa: E402
from patch.aghs_text import _FLAGS, _HEADER_LABELS, _granted, _num, aghs_text  # noqa: E402
from patch.meta import RELEASE_HISTORY  # noqa: E402
from tools import game_files  # noqa: E402
from tools.loc_history import tooltip  # noqa: E402

def _valve_gaps():
    """{(ability, kind): why} the game itself had no usable text — the local list (outputs/, not in git)."""
    import json
    path = os.path.join(ROOT, "outputs", "aghs_valve_gaps.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return {tuple(k.split()): v for k, v in json.load(f).items()}


VALVE_GAPS = _valve_gaps()
_SKIP_KEYS = ("var_type", "LinkedSpecialBonus", "RequiresScepter", "RequiresShard", "CalculateSpellDamageTooltip")


def _upgrade_values(block, kind):
    """(key, raw) of the values the upgrade sets in one ability block, both KV layouts."""
    req = "RequiresScepter" if kind == "scepter" else "RequiresShard"
    out = []
    av = block.get("AbilityValues") if isinstance(block.get("AbilityValues"), dict) else {}
    for key, val in av.items():
        if isinstance(val, dict):
            raw = val.get(f"special_bonus_{kind}", val.get("special_bonus_aghanim") if kind == "scepter" else None)
            if raw is None and str(val.get(req, "0")).strip() == "1":
                raw = val.get("value")
            out.append((key, raw))
    asp = block.get("AbilitySpecial") if isinstance(block.get("AbilitySpecial"), dict) else {}
    for d in asp.values():
        if isinstance(d, dict) and str(d.get(req, "0")).strip() == "1":
            out += [(k, x) for k, x in d.items() if k not in _SKIP_KEYS]
    return out


def _hero_mates(version):
    """{ability: the abilities of its hero} from the build's npc_heroes.txt."""
    kv = parse_kv(game_files.npc(version, "npc_heroes.txt") or "")
    out = {}
    for hero in (kv.get("DOTAHeroes") or {}).values():
        if isinstance(hero, dict):
            abil = {x for k, x in hero.items() if k.startswith("Ability") and k[7:].isdigit() and isinstance(x, str) and x}
            out.update({a: abil for a in abil})
    return out


def audit(version):
    """Problems of one patch: ["<slug> <kind>: …"]."""
    blocks = _hero_blocks(version)
    problems, notext = [], []
    for slug, b in blocks.items():
        if not isinstance(b, dict):
            continue
        for kind in ("scepter", "shard"):
            if str(b.get(_FLAGS[kind][0], "0")).strip() != "1" and not _granted(b, kind):
                continue
            text = aghs_text(slug, kind, version)
            if not text:
                notext.append((slug, kind))
                continue
            for key, raw in _upgrade_values(b, kind):
                n = _num(raw) if raw is not None else None
                if not n or not any(float(x.rstrip("%")) for x in n.split("/")):
                    continue
                if n.lstrip("-") == "1" and str(raw).strip().lstrip("+") in ("1", "1.0"):
                    continue                                      # a flag: "+1" = on
                if not (tooltip(f"DOTA_Tooltip_ability_{slug}_{key}", version) or _HEADER_LABELS.get(key.lower())):
                    continue                                      # the game shows no label for it either
                if not re.search(rf"(?<![\d.]){re.escape(n.lstrip('-+'))}(?!\d|\.\d)", text):
                    problems.append(f"{slug} {kind}: {key}={raw} not in the text")
    mates = _hero_mates(version)
    for slug, kind in notext:
        if not tooltip(f"DOTA_Tooltip_ability_{slug}", version) or (slug, kind) in VALVE_GAPS:
            continue                                              # a leftover / Valve's own gap
        pre = slug.split("_")[0] + "_"
        team = (mates.get(slug) or set()) | {o for o in blocks if o.startswith(pre)}
        if not any(aghs_text(o, kind, version) for o in team - {slug} if isinstance(blocks.get(o), dict)
                   and (str(blocks[o].get(_FLAGS[kind][0], "0")) == "1" or _granted(blocks[o], kind))):
            problems.append(f"{slug} {kind}: no text on any of the hero's abilities")
    return problems


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    bad = 0
    versions = [p["version"] for p in RELEASE_HISTORY if p["version"] in game_files.versions()]
    for v in versions:
        for p in audit(v):
            print(f"{v} {p}")
            bad += 1
    print(f"{len(versions)} patches, {bad} problem(s); Valve's own gaps: {len(VALVE_GAPS)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
