"""A new condition on using an ability is a restriction — NERF, not DEL (owner 2026-10-27, Helm of the Dominator 7.39e
"Dominate can no longer be used if the currently dominated creep took damage …"). "Can no longer be cast while
rooted" stays DEL (owner 2026-09-27), as does a use taken away."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import generate_patch_code_v2 as gen  # noqa: E402


def test_a_new_condition_on_use_is_nerf():
    assert gen._guess_tag("Dominate can no longer be used if the currently dominated creep took damage from "
                          "hero-based sources in the last 3s") == "NERF"


def test_cast_while_and_a_use_taken_away_stay_del():
    assert gen._guess_tag("Can no longer be cast while rooted") == "DEL"
    assert gen._guess_tag("Aghanim's Scepter's Martyrdom can no longer be cast on enemies to damage them") == "DEL"


def test_the_site_tags_those_rows_nerf():
    rx = re.compile(r'li\("[^"]*can no longer be used (?:if|when|after|within)\b[^"]*", t\("(\w+)"\)', re.I)
    tags = []
    for name in os.listdir(os.path.join(ROOT, "content")):
        if name.startswith("p") and name.endswith(".py"):
            with open(os.path.join(ROOT, "content", name), encoding="utf-8") as f:
                tags += rx.findall(f.read())
    assert tags and set(tags) == {"NERF"}
