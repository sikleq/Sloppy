"""tools/check_game_build.py — the scheduled check for a game build newer than the newest snapshot (offline parts)."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import check_game_build as cgb  # noqa: E402
from patch.meta import latest_stats_version  # noqa: E402


def _local(path):
    with open(path, "rb") as f:
        return f.read()


def test_the_same_files_report_nothing_and_a_changed_one_is_named():
    latest = latest_stats_version()
    pairs = {}

    def same(p):
        local = (os.path.join(ROOT, "data", "patchnotes_english.txt") if p.endswith("patchnotes_english.txt")
                 else os.path.join(ROOT, "data", "stats", latest, p.rsplit("/", 1)[-1]))
        pairs[p] = local
        return _local(local).replace(b"\r\n", b"\n")          # GameTracking ships LF
    assert cgb.changed_files(latest, same) == []
    assert "scripts/npc/items.txt" in pairs

    def items_changed(p):
        return b'"ItemCost" "2700"' if p == "scripts/npc/items.txt" else same(p)
    assert [p for p, _ in cgb.changed_files(latest, items_changed)] == ["scripts/npc/items.txt"]


def test_only_patches_newer_than_the_site_count_as_new():
    notes = '"DOTA_Patch_7_42_General" "x"\n"DOTA_Patch_7_41f_X" "y"\n"DOTA_Patch_6_88_Y" "z"\n"DOTA_Patch_7_42b_A" "b"'
    assert cgb.new_patch_keys(notes, ["7.41f", "7.41e"]) == ["7.42", "7.42b"]
    assert cgb.new_patch_keys(notes, ["7.42b"]) == []


def test_issue_text_says_what_to_run():
    changed = [("scripts/npc/items.txt", "x")]
    silent = cgb.issue_body("6946", "a" * 40, "2026-10-07", "7.41f", changed, [])
    assert "`scripts/npc/items.txt`" in silent and "Do not refresh the `7.41f` snapshot" in silent
    patch = cgb.issue_body("7001", "b" * 40, "2026-11-01", "7.41f", changed, ["7.42"])
    assert "python tools/new_patch.py 7.42" in patch
    assert cgb.TITLE.format(build="6946", latest="7.41f") == \
        "Game build 6946 changes the game files (newest snapshot: 7.41f)"


def test_the_workflow_uses_only_its_own_token():
    with open(os.path.join(ROOT, ".github", "workflows", "game-build-watch.yml"), encoding="utf-8") as f:
        text = f.read()
    assert "issues: write" in text and "contents: read" in text
    # its own token, plus (2026-10-24) the read-only deploy key of the game-files store, used by the store checkout only
    assert sorted(re.findall(r"secrets\.(\w+)", text)) == ["DOTA_FILES_DEPLOY_KEY", "GITHUB_TOKEN"]
    store_step = text[text.index("Check out the game-files store"):text.index("Set up Python")]
    assert "secrets.DOTA_FILES_DEPLOY_KEY" in store_step and "repository: sikleq/dota-patch-files" in store_step
    assert "tools/check_game_build.py --open-issue" in text
