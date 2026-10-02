"""Which map file every patch shipped, and the Terrain pages' steps built from it.

data/map/patch_maps.json = {patch: {"sha1", "manifest"}} (scripts/gen/map_history.py, Steam's depot history);
data/map/renders.json "pictures" = the map files we hold a picture of, each named by the FIRST patch that shipped it
(icons/maps/map_<ver>.webp, data/map/mapdata_<code>.json).

A step = one patch whose map file differs from the patch before's: the Terrain page of that patch compares the two
(the owner 2026-10-02: "the difference between the letter patches has to be shown too, not just two major
versions"). A patch that shipped the same file as the one before (7.40b, 7.41b) is no step.
"""
import json
import os
import re
from typing import NamedTuple

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MAP = os.path.join(_ROOT, "data", "map")


def ver_key(v):
    """'7.40' < '7.40b' < '7.41'."""
    m = re.match(r"^(\d+)\.(\d+)([a-z]*)$", v)
    return (int(m.group(1)), int(m.group(2)), m.group(3)) if m else (0, 0, v)


def code(v):
    """'7.39b' -> '739b' (the file-name form)."""
    return v.replace(".", "")


class Step(NamedTuple):
    patch: str        # the patch this page is about
    before: str       # the patch right before it (the OLD side's label)
    old_pic: str      # the picture/mapdata version of the old map file (the first patch that shipped it)
    new_pic: str      # the same for the new map file


def load_patch_maps():
    """{patch: sha1}, oldest first."""
    with open(os.path.join(_MAP, "patch_maps.json"), encoding="utf-8") as f:
        pm = json.load(f)["patches"]
    return {v: pm[v]["sha1"] for v in sorted(pm, key=ver_key)}


def load_pictures():
    """The map-file versions we hold a picture of (data/map/renders.json)."""
    try:
        with open(os.path.join(_MAP, "renders.json"), encoding="utf-8") as f:
            return set(json.load(f)["pictures"])
    except (OSError, ValueError, KeyError):
        return set()


def first_shipped(patch_maps):
    """{sha1: the first patch that shipped it}."""
    out = {}
    for v, sha in patch_maps.items():
        out.setdefault(sha, v)
    return out


def steps(patch_maps=None, pictures=None):
    """Every patch whose map file differs from the patch before's and whose both files have a picture, oldest
    first. A step's old side is the patch right before it, shown with the picture of the map file that patch ran."""
    pm = load_patch_maps() if patch_maps is None else patch_maps
    pics = load_pictures() if pictures is None else pictures
    first = first_shipped(pm)
    out, prev = [], None
    for v, sha in pm.items():
        if prev is not None and sha != pm[prev]:
            old_pic, new_pic = first[pm[prev]], first[sha]
            if old_pic in pics and new_pic in pics:
                out.append(Step(v, prev, old_pic, new_pic))
        prev = v
    return out


def same_file_as(patch_maps=None):
    """{patch: the earlier patch whose very map file it shipped} — for patches that changed nothing on the map."""
    pm = load_patch_maps() if patch_maps is None else patch_maps
    first = first_shipped(pm)
    return {v: first[sha] for v, sha in pm.items() if first[sha] != v}
