"""Build data/rules/aghs_granted_old.json — the Aghanim grant flags of patches whose data/stats/<v>/ has no
per-hero KV (before 7.34e only slim JSON is kept there), for patch/aghs_granted.py (owner 2026-10-22: the 7.08
page had no data for its Aghanim stripes).

Source: the full npc_abilities.txt of each patch from dotabuff/d2vpkr, kept with the weights model
(outputs/valve-revealed-weights-20260915/abilities_history/<v>/npc_abilities.txt, not in git). Rerun only if that
history changes; new patches have per-hero snapshots and need nothing here.

    python tools/build_aghs_granted_old.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from builders.silent import _decode_bytes  # noqa: E402
from patch.aghs_granted import OLD_PATH, scan  # noqa: E402

HIST = os.path.join(HERE, "outputs", "valve-revealed-weights-20260915", "abilities_history")


def main():
    out = {}
    for v in sorted(os.listdir(HIST)):
        src = os.path.join(HIST, v, "npc_abilities.txt")
        if os.path.isdir(os.path.join(HERE, "data", "stats", v, "heroes")) or not os.path.exists(src):
            continue                                 # a per-hero snapshot covers it
        with open(src, "rb") as fh:
            grants, hidden = scan(_decode_bytes(fh.read()))
        # only what kind_of() can use: the flags, and hidden one-level abilities some patch granted
        out[v] = {"granted": dict(sorted(grants.items())), "hidden_one_level": sorted(hidden)}
    ever = {s for rec in out.values() for s in rec["granted"]}
    for rec in out.values():
        rec["hidden_one_level"] = [s for s in rec["hidden_one_level"] if s in ever]
    with open(OLD_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"source": "dotabuff/d2vpkr npc_abilities.txt per patch (tools/build_aghs_granted_old.py)",
                   "versions": out}, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"{len(out)} patch(es), {len(ever)} granted abilities -> {os.path.relpath(OLD_PATH, HERE)}")


if __name__ == "__main__":
    main()
