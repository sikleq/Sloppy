"""Guard: every hero and every facet subsection in a patch's Valve datafeed must be
represented in its annotated content file.

The datafeed sometimes puts a hero's ONLY change inside a facet subsection
(`heroes[].subsections[].general_notes`). That spot was missed repeatedly:
7.38 Queen of Pain (Masochist), 7.39b Lina (Slow Burn), 7.40b Tidehunter
(Krill Eater) and Ursa (Bear Down). A facet counts as represented when its slug,
its title, or the opening words of one of its notes appear in the content file
(facet changes are sometimes folded into an ability block instead of a
facet_header).
"""
import glob
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Datafeed hero ids that are not playable heroes in herolist.json.
NON_HERO_IDS = {1961}          # Spirit Bear ("New Hero?") — lives in the Lone Druid section

_norm = lambda s: re.sub(r"[^a-z0-9%]+", " ", re.sub(r"<[^>]+>", " ", s).lower()).strip()


def _hero_names():
    data = json.load(open(os.path.join(ROOT, "data", "herolist.json"), encoding="utf-8"))
    return {h["id"]: h["name_english_loc"] for h in data["result"]["data"]["heroes"]}


def _annotated_versions():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "content", "p7*.py"))):
        b = os.path.basename(f)[1:-3]
        v = f"{b[0]}.{b[1:3]}{b[3:]}"
        if os.path.exists(os.path.join(ROOT, "data", f"{v}_datafeed.json")):
            out.append((v, f))
    return out


@pytest.mark.parametrize("version,path", _annotated_versions())
def test_datafeed_heroes_and_facets_present(version, path):
    names = _hero_names()
    src = open(path, encoding="utf-8").read()
    body = _norm(src)
    headers = set(re.findall(r'hero_header\("([^"]+)"', src))
    feed = json.load(open(os.path.join(ROOT, "data", f"{version}_datafeed.json"), encoding="utf-8"))
    missing_heroes, missing_facets = [], []
    for h in feed.get("heroes", []):
        hid = h.get("hero_id")
        if hid in NON_HERO_IDS:
            continue
        name = names.get(hid)
        assert name, f"{version}: unknown datafeed hero id {hid} — add to herolist or NON_HERO_IDS"
        if name not in headers:
            missing_heroes.append(name)
        for sub in h.get("subsections", []):
            slug, title = sub.get("facet"), sub.get("title", "")
            if not slug:
                continue
            notes = [n.get("note", "") for n in sub.get("general_notes", [])]
            notes += [an.get("note", "") for a in sub.get("abilities", []) for an in a.get("ability_notes", [])]
            probes = [slug.lower(), _norm(title)] + [" ".join(_norm(n).split()[:5]) for n in notes if len(_norm(n)) > 12]
            if not any(p and (p in src or p in body) for p in probes):
                missing_facets.append(f"{name}: {title} ({slug})")
    assert not missing_heroes, f"{version}: datafeed heroes missing from content: {missing_heroes}"
    assert not missing_facets, f"{version}: datafeed facet changes missing from content: {missing_facets}"
