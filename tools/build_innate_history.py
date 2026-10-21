"""data/rules/innate_history.json — which ability was each hero's innate in every patch (owner 2026-10-21: «нам
нужно знать, как менялись innate в патчах, не только значения, но и какие способности были»).

Sources, in this order of trust:
  data/stats/<v>/heroes/npc_dota_hero_<x>.txt   abilities flagged "Innate" "1" (per-hero files exist from 7.34e)
  data/patchnotes_english.txt                   for the patches before those files (Treant 7.23c, Alchemist and
                                                Ogre Magi 7.33) and for LAGGED snapshots
A lagged snapshot was taken from a build before its own patch (its hero files barely differ from the patch before
while its notes touch many heroes — 7.41's files are build 6726, the day before 7.41's build 6728). Its innates are
read from the next snapshot instead, minus what the next patch's notes add and plus what they remove.

{"heroes": {slug: [{"since": v, "innates": [ability, ...], "source": "files" | "notes" | "next snapshot"}, ...]},
 "lagged": [v, ...]} — one row per change, oldest first.

    python tools/build_innate_history.py            # write the file
    python tools/build_innate_history.py --check    # exit 1 when it is stale
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "data", "rules", "innate_history.json")
NOTES = os.path.join(ROOT, "data", "patchnotes_english.txt")
# innates before the per-hero files, from the patch notes (key -> the note)
EARLY = [
    ("7.23c", "treant", "treant_natures_guise"),     # DOTA_Patch_7_23c_treant: "Now has an innate Nature's Guise"
    ("7.33", "alchemist", "alchemist_goblins_greed"),  # DOTA_Patch_7_33_alchemist_alchemist_goblins_greed
    ("7.33", "ogre_magi", "ogre_magi_dumb_luck"),      # DOTA_Patch_7_33_ogre_magi_ogre_magi_dumb_luck
]
_ADDED = re.compile(r"new innate|now (?:an |\w+'s )?innate|moved to innate|reworked into (?:an )?innate|"
                    r"returns as an innate", re.I)
_REMOVED = re.compile(r"no longer an innate", re.I)
LAG_SHARE = 0.6          # >60% of the heroes a patch's notes touch unchanged in its files = a lagged snapshot
LAG_MIN_NOTED = 5


def _ir():
    from builders import innate_rules as ir
    return ir


def _notes():
    with open(NOTES, encoding="utf-8", errors="replace") as f:
        return f.read()


def _hero_file(v, slug):
    p = os.path.join(_ir().STATS_DIR, v, "heroes", f"npc_dota_hero_{slug}.txt")
    if not os.path.exists(p):
        return None
    with open(p, "rb") as f:
        return f.read().replace(b"\r\n", b"\n")


def noted_heroes(v, slugs, notes):
    code = re.escape("DOTA_Patch_" + v.replace(".", "_") + "_")
    keys = re.findall(r'"' + code + r'([a-z0-9_]+)"', notes)
    return {s for s in slugs for k in keys if k == s or k.startswith(s + "_")}


def note_events(v, slug, notes):
    """(added, removed) abilities of `slug` the notes of `v` call innate / no longer innate."""
    code = re.escape(f"DOTA_Patch_{v.replace('.', '_')}_{slug}_")
    added, removed = set(), set()
    for key, text in re.findall(r'"' + code + r'([a-z0-9_]+?)(?:_\d+)?"\s+"([^"]*)"', notes):
        if not key.startswith(slug + "_"):
            continue
        if _REMOVED.search(text):
            removed.add(key)
        elif _ADDED.search(text):
            added.add(key)
    return added, removed


def lagged(versions, slugs, notes):
    out, prev = [], None
    for v in versions:
        if prev:
            n = noted_heroes(v, slugs, notes)
            unchanged = {s for s in n if _hero_file(v, s) == _hero_file(prev, s)}
            if len(n) >= LAG_MIN_NOTED and len(unchanged) > LAG_SHARE * len(n):
                out.append(v)
        prev = v
    return out


def build():
    ir = _ir()
    notes = _notes()
    file_vers = [v for v in ir.stats_versions() if os.path.isdir(os.path.join(ir.STATS_DIR, v, "heroes"))]
    slugs = sorted({f[len("npc_dota_hero_"):-4] for v in file_vers
                    for f in os.listdir(os.path.join(ir.STATS_DIR, v, "heroes")) if f.startswith("npc_dota_hero_")})
    lag = lagged(file_vers, slugs, notes)
    heroes = {}
    for slug in slugs:
        rows = [{"since": v, "innates": [a], "source": "notes"} for v, s, a in EARLY if s == slug]
        for i, v in enumerate(file_vers):
            if v in lag and i + 1 < len(file_vers):
                nxt = file_vers[i + 1]
                added, removed = note_events(nxt, slug, notes)
                cur, src = (set(ir.innate_blocks(slug, nxt)) - added) | removed, "next snapshot"
            else:
                cur, src = set(ir.innate_blocks(slug, v)), "files"
            if rows and set(rows[-1]["innates"]) == cur:
                continue
            if rows and rows[-1]["source"] == "notes" and not cur:
                continue          # the early files lack the flag (Ogre 7.34e): the notes stand
            if not rows and not cur:
                continue
            rows.append({"since": v, "innates": sorted(cur), "source": src})
        if rows:
            heroes[slug] = rows
    return {"_doc": "Which ability was each hero's innate in every patch, oldest first; written by "
                    "tools/build_innate_history.py (game files, patch notes for the early ones and for lagged "
                    "snapshots).",
            "lagged": lag, "heroes": heroes}


def text(data):
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    new = text(build())
    if "--check" in argv:
        try:
            with open(OUT, encoding="utf-8") as f:
                old = f.read()
        except OSError:
            old = ""
        if old != new:
            print("data/rules/innate_history.json is stale: python tools/build_innate_history.py")
            return 1
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    d = json.loads(new)
    print(f"{len(d['heroes'])} heroes, lagged snapshots: {', '.join(d['lagged'])} -> {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
