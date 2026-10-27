"""Build data/rules/abilities_not_in_game.json — the hero abilities and facets that sit in the game files but were
never in the game (owner 2026-10-27: Ice Age 7.39 and Naga's Critical Strike showed up in Aghanim's cards; "we must
keep track of which abilities / facets / innates exist and which only gather dust in the files").

An ability is in the game in a patch when a hero or unit has it in an Ability slot, or a facet grants it
(Facets → Abilities → AbilityName), in that patch's own build (the game-files store, patch/game_files.py). Every hero
ability the KV defines but no slot or facet ever names (7.08 → today) goes to the file, with its evidence:

  kind "never"   a tooltip name, but no patch note and no Liquipedia page names it for the hero
  kind "old"     Liquipedia knows it as an ability the hero had before 7.08 (Naga's Critical Strike) — a leftover
  kind "helper"  no tooltip name, or a plumbing one ("Ice Shards Stop", "Fling Release", "Empty"): stop / release
                 actions, empty slots, innate sub-parts — never shown to players as an ability
  kind "draft"   an Ability Draft copy (…_ad)
  kind "code"    in the game after all: the game grants it in code (patch/known_exceptions.KNOWN_UNSLOTTED_REAL, with
                 the evidence) — listed for the record, not filtered

Facets: a facet whose every patch marks it "Deprecated" never reached players.

The site reads the file through patch/aghs_text.holders (an Aghanim's card names only abilities in the game).

    python tools/build_ability_registry.py [--liquipedia DIR]   # DIR: the Liquipedia cache (default outputs/liquipedia)

Needs the game-files store (~2.5 min for every patch). Rerun after a new patch.
"""
import argparse
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from patch import game_files  # noqa: E402
from patch.known_exceptions import KNOWN_UNSLOTTED_REAL  # noqa: E402
from patch.kv import hero_ability_blocks, parse_kv  # noqa: E402
from patch.loc_history import tooltip  # noqa: E402
from patch.meta import RELEASE_HISTORY  # noqa: E402

OUT = ROOT / "data" / "rules" / "abilities_not_in_game.json"
_SLOT = re.compile(r"^Ability\d+$")
_NOT_HERO = ("special_bonus", "generic", "dota_", "ability_", "item_")
# a tooltip name that is plumbing, not an ability: "Ice Shards Stop", "Fling Release", "End Meditation", "Empty"
_HELPER_NAME = re.compile(r"\b(?:Stop|Release|End|Empty|Creep Ability)\b|\s-\s")


def ver_key(v):
    m = re.match(r"(\d+)\.(\d+)([a-z]*)", v)
    return (int(m.group(1)), int(m.group(2)), m.group(3))


def _slots(entity):
    return {v for k, v in entity.items() if _SLOT.match(k) and isinstance(v, str) and v}


def _heroes(v):
    """{npc_dota_hero_x: merged hero block} of one build (npc_heroes.txt + the per-hero files of 7.41f+)."""
    per = [parse_kv(game_files.read(v, r) or "") for r in game_files.listing(v, "scripts/npc/heroes")
           if r.rsplit("/", 1)[-1].startswith("npc_dota_hero_") and not r.endswith("_base.txt")]
    heroes = {}
    for kv in [parse_kv(game_files.npc(v, "npc_heroes.txt") or "")] + per:
        for hn, h in (kv.get("DOTAHeroes") or {}).items():
            if isinstance(h, dict) and hn.startswith("npc_dota_hero_"):
                heroes.setdefault(hn, {}).update(h)
    return heroes, per


def scan(versions):
    """(defined, in_game, flags, facets): slug -> versions defined / in a slot or facet; slug -> grant flags;
    hero -> facet -> [(version, deprecated)]."""
    defined, in_game, flags = defaultdict(list), defaultdict(list), {}
    facets = defaultdict(lambda: defaultdict(list))
    for v in versions:
        heroes, per = _heroes(v)
        for hn, h in heroes.items():
            for s in _slots(h):
                in_game[s].append(v)
            for fname, f in (h.get("Facets") or {}).items():
                if not isinstance(f, dict):
                    continue
                facets[hn[len("npc_dota_hero_"):]][fname].append((v, bool(f.get("Deprecated"))))
                for a in (f.get("Abilities") or {}).values():
                    if isinstance(a, dict) and a.get("AbilityName"):
                        in_game[a["AbilityName"]].append(v)
        for root in parse_kv(game_files.npc(v, "npc_units.txt") or "").values():
            for u in (root.values() if isinstance(root, dict) else []):
                if isinstance(u, dict):
                    for s in _slots(u):
                        in_game[s].append(v)
        kv = parse_kv(game_files.npc(v, "npc_abilities.txt") or "")
        blocks = dict(next(iter(kv.values()), {}) if kv else {})
        for k in per:
            blocks.update(hero_ability_blocks(k))
        for slug, b in blocks.items():
            if isinstance(b, dict):
                defined[slug].append(v)
                flags[slug] = {f: b[f] for f in ("IsGrantedByShard", "IsGrantedByScepter", "Innate") if b.get(f)}
        print(f"  {v}: {len(heroes)} heroes, {len(blocks)} abilities", file=sys.stderr)
    return defined, in_game, flags, facets


def _liquipedia(lp_dir):
    d = Path(lp_dir)
    return {p.name: gzip.open(p, "rt", encoding="utf-8", errors="replace").read()
            for p in d.glob("*.txt.gz")} if d.is_dir() else {}


def _mentions(name, hero, texts, template=False):
    """The first line of `texts` ({file: text}) naming `name` next to the hero (in the line or the file name).
    template: Liquipedia's ability link {{A|Hero|Name…}} only — a bare word ("Silence Duration") is not the ability."""
    word_rx = re.escape(name)
    rx = re.compile(r"\{\{A\|[^|}]*\|" + word_rx + r"[}|( ]" if template
                    else r"(?<![A-Za-z])" + word_rx + r"(?![A-Za-z])")
    word = hero.split("_")[0].lower()
    for fn, t in texts.items():
        for m in rx.finditer(t):
            line = t[t.rfind("\n", 0, m.start()) + 1: t.find("\n", m.end())]
            if word in (fn + line).lower().replace(" ", "_"):
                return f"{fn}: {line.strip()[:160]}"
    return None


def build(versions, lp_texts, notes_text):
    defined, in_game, flags, facets = scan(versions)
    heroes = sorted({h for h in facets} | _hero_names(versions[-1]), key=len, reverse=True)
    notes = {"patchnotes_english.txt": notes_text}
    abilities = {}
    for slug, vs in sorted(defined.items()):
        if slug.startswith(_NOT_HERO) or slug in in_game:
            continue
        hero = next((h for h in heroes if slug.startswith(h + "_")), None)
        if not hero:
            continue
        name = next((t for t in (tooltip(f"DOTA_Tooltip_ability_{slug}", x) for x in (vs[-1], vs[0])) if t), None)
        row = {"hero": hero, "name": name, "first": vs[0], "last": vs[-1], "flags": flags.get(slug, {})}
        if slug in KNOWN_UNSLOTTED_REAL:
            row.update(kind="code", evidence=KNOWN_UNSLOTTED_REAL[slug])
        elif slug.endswith("_ad"):
            row.update(kind="draft")
        elif not name or _HELPER_NAME.search(name):
            row.update(kind="helper")
        else:
            # a name a slotted ability of the hero also has (luna_lunar_grace "Lunar Blessing" = luna_lunar_blessing):
            # Liquipedia's mention is the real one's, this copy never played
            twin = any(tooltip(f"DOTA_Tooltip_ability_{s}", vs[-1]) == name for s in in_game
                       if s.startswith(hero + "_") and s != slug)
            lp = None if twin else _mentions(name, hero, lp_texts, template=True)
            note = _mentions(name, hero, notes)
            row.update(kind="old" if lp else "never", liquipedia=lp, patch_notes=note)
        abilities[slug] = row
    never_facets = {f"{h}/{f}": {"first": xs[0][0], "last": xs[-1][0]}
                    for h, fs in sorted(facets.items()) for f, xs in sorted(fs.items()) if all(d for _, d in xs)}
    return {"source": "every patch's own build, 7.08 → today (tools/build_ability_registry.py)",
            "abilities": abilities, "facets_never_live": never_facets}


def _hero_names(v):
    heroes, _ = _heroes(v)
    return {hn[len("npc_dota_hero_"):] for hn in heroes}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--liquipedia", default=str(ROOT / "outputs" / "liquipedia" / "wikitext"))
    a = ap.parse_args(argv)
    if not game_files.available():
        print(f"no game-files store at {game_files.STORE} (set DOTA_FILES_DIR)", file=sys.stderr)
        return 1
    versions = sorted((p["version"] for p in RELEASE_HISTORY if p["version"] in game_files.versions()), key=ver_key)
    notes = (ROOT / "data" / "patchnotes_english.txt").read_text(encoding="utf-8", errors="replace")
    lp = _liquipedia(a.liquipedia)
    if not lp:
        print(f"no Liquipedia cache at {a.liquipedia}: kind 'old' cannot be told from 'never'", file=sys.stderr)
        return 1
    reg = build(versions, lp, notes)
    OUT.write_text(json.dumps(reg, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    kinds = defaultdict(int)
    for r in reg["abilities"].values():
        kinds[r["kind"]] += 1
    print(f"{OUT.relative_to(ROOT)}: {dict(kinds)}, facets never live: {len(reg['facets_never_live'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
