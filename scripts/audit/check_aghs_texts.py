"""Audit of every Aghanim's Scepter / Shard text the generator builds (patch/aghs_text.py), in every patch of the
game-files store (7.08 -> now; owner 2026-10-25: "мы должны решать такое и добыть все данные", and "генератор должен
уметь" — nobody runs it by hand: build_site.py runs `--site` on every build, CI runs the full audit on every push).

Two checks per patch:
1. a number the upgrade sets (special_bonus_<kind>, "RequiresScepter" / "RequiresShard") that the game labels must be
   in the text;
2. every hero's upgrade must have a text on at least one of its abilities (the flag sits on one ability, the text
   often on another: Thundergod's Wrath -> Nimbus, Omnislash -> Swift Slash).
Abilities with no tooltip at all are leftovers in the files and are skipped. A tooltip the game itself broke — a
%placeholder% no ability of the hero has a value for, or the line commented out in the file — is the game's, not ours:
counted, not failed. Exit 1 on anything else.

    python scripts/audit/check_aghs_texts.py           # all 118 patches, ~2 min
    python scripts/audit/check_aghs_texts.py --site    # the patches the site draws cards for (and the one before each)
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from builders.silent import parse_kv  # noqa: E402
from patch.ability_kv import _hero_blocks  # noqa: E402
from patch.aghs_text import _FLAGS, _HEADER_LABELS, _KEYS, _granted, _num, _values, _with_kin_values, aghs_text  # noqa: E402
from patch.meta import RELEASE_HISTORY, _prev_patch_version  # noqa: E402
from tools import game_files  # noqa: E402
from tools.loc_history import tooltip  # noqa: E402

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


def _holds(block, kind):
    return isinstance(block, dict) and (str(block.get(_FLAGS[kind][0], "0")).strip() == "1" or _granted(block, kind))


def _game_broke(slug, kind, version, block):
    """Why the game's own tooltip of this upgrade can't be shown, or "": a placeholder no ability of the hero has a
    value for, or the line commented out in the file."""
    desc = next((d for d in (tooltip(f"DOTA_Tooltip_ability_{slug}_{pre}{k}", version)
                             for pre in ("", "ad_") for k in _KEYS[kind]) if d), None)
    if not desc and _granted(block, kind):
        desc = tooltip(f"DOTA_Tooltip_ability_{slug}_Description", version)
    if desc:
        vals = _with_kin_values(desc, _values(block, kind), slug, kind, version)
        miss = sorted({m.group(1) for m in re.finditer(r"%([A-Za-z_]\w*)%", desc) if m.group(1).lower() not in vals})
        return f"%{miss[0]}% has no value in the game files" if miss else ""
    text = game_files.read(version, "resource/localization/abilities_english.txt") or ""
    if re.search(rf'^\s*//\s*"DOTA_Tooltip_ability_{re.escape(slug)}_(?:aghanim|scepter|shard)_description"',
                 text, re.I | re.M):
        return "the line is commented out in the game file"
    return ""


def audit(version):
    """(problems, the game's own gaps) of one patch: ["<slug> <kind>: …"]."""
    blocks = _hero_blocks(version)
    problems, notext = [], []
    for slug, b in blocks.items():
        for kind in ("scepter", "shard"):
            if not _holds(b, kind):
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
    mates, gaps = _hero_mates(version), []
    for slug, kind in notext:
        if not tooltip(f"DOTA_Tooltip_ability_{slug}", version):
            continue                                              # a leftover in the files, not a real ability
        pre = slug.split("_")[0] + "_"
        team = ((mates.get(slug) or set()) | {o for o in blocks if o.startswith(pre)}) - {slug}
        if any(aghs_text(o, kind, version) for o in team if _holds(blocks.get(o), kind)):
            continue                                              # the hero's text sits on another ability
        why = next((w for w in (_game_broke(o, kind, version, blocks[o]) for o in [slug, *sorted(team)]
                                if _holds(blocks.get(o), kind)) if w), "")
        (gaps if why else problems).append(f"{slug} {kind}: " + (why or "no text on any of the hero's abilities"))
    return problems, gaps


def _site_versions():
    """The patches the site draws Aghanim's cards for (content/p*.py) and the patch before each (their old side)."""
    stems = [f[1:-3] for f in os.listdir(os.path.join(ROOT, "content")) if re.match(r"p\d{3}[a-z]?\.py$", f)]
    out = set()
    for s in stems:
        v = f"{s[0]}.{s[1:3]}{s[3:]}"
        out.update(x for x in (v, _prev_patch_version(v)) if x)
    return out


NO_STORE = """Aghanim's texts audit: no patch to check — the game-files store has none of them (store: {store}).
The audit reads the store itself, not data/stats/: clone dota-patch-files and point DOTA_FILES_DIR at it."""


def main(argv):
    site = "--site" in argv
    wanted = _site_versions() if site else None
    versions = [p["version"] for p in RELEASE_HISTORY if p["version"] in game_files.versions()
                and (wanted is None or p["version"] in wanted)]
    if not versions:                     # audit 2026-10-26: no store printed "0 patches, 0 problem(s)" and passed
        print(NO_STORE.format(store=game_files.STORE), file=sys.stderr)
        return 2
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    bad = broke = 0
    for v in versions:
        problems, gaps = audit(v)
        for p in problems:
            print(f"  PROBLEM {v} {p}")
        bad += len(problems)
        broke += len(gaps)
    print(f"  Aghanim's texts: {len(versions)} patches, {bad} problem(s); the game's own broken tooltips: {broke}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
