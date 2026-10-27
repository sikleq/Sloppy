"""tools/new_patch.py — the one command for the data side of a new patch."""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools import new_patch as np_  # noqa: E402

META = '''RELEASE_HISTORY = [
    # 7.41 cycle
    {"version": "7.41f", "date": "15.09.2026", "filename": "patches/7.41f.html"},
    {"version": "7.41e", "date": "30.07.2026", "filename": "patches/7.41e.html"},
    {"version": "7.41",  "date": "24.03.2026", "filename": "patches/7.41.html"},
    # 7.40 cycle
    {"version": "7.40c", "date": "21.01.2026", "filename": "patches/7.40c.html"},
    {"version": "7.08",  "date": "01.02.2018", "filename": "patches/7.08.html"},
]
'''


def _block(text):
    return text.split("RELEASE_HISTORY = [\n", 1)[1].split("\n]", 1)[0].split("\n")


def test_letter_patch_goes_on_top_of_its_cycle():
    out = _block(np_.register(META, "7.41g", "21.10.2026"))
    assert out[:3] == ["    # 7.41 cycle",
                       '    {"version": "7.41g", "date": "21.10.2026", "filename": "patches/7.41g.html"},',
                       '    {"version": "7.41f", "date": "15.09.2026", "filename": "patches/7.41f.html"},']


def test_new_cycle_gets_its_comment_above_the_old_one_and_the_files_spacing():
    out = _block(np_.register(META, "7.42", "21.10.2026"))
    assert out[:3] == ["    # 7.42 cycle",
                       '    {"version": "7.42",  "date": "21.10.2026", "filename": "patches/7.42.html"},',
                       "    # 7.41 cycle"]


def test_a_late_row_lands_in_date_order_and_registering_twice_changes_nothing():
    once = np_.register(META, "7.40d", "01.03.2026")
    out = _block(once)
    i = out.index('    {"version": "7.40d", "date": "01.03.2026", "filename": "patches/7.40d.html"},')
    assert out[i - 1] == "    # 7.40 cycle" and "7.41" in out[i - 2] and "7.40c" in out[i + 1]
    assert np_.register(once, "7.40d", "01.03.2026") == once
    assert np_.registered(once, "7.40d") == "01.03.2026" and np_.registered(META, "7.99") is None


def test_the_real_meta_file_takes_a_new_patch_and_stays_importable(tmp_path):
    with open(np_.META, encoding="utf-8") as f:
        text = f.read()
    new = np_.register(text, "9.01", "01.01.2099")
    assert new.count('"version": "9.01"') == 1 and new.replace(np_.entry_line("9.01", "01.01.2099") + "\n", "") \
        .replace("    # 9.01 cycle\n", "") == text
    ns = {}
    exec(compile(new.split("\n# A patch page exists")[0], "meta", "exec"), ns)   # the list itself still parses
    assert ns["RELEASE_HISTORY"][0]["version"] == "9.01"


def test_plan_skips_what_does_not_apply(monkeypatch, tmp_path):
    monkeypatch.setattr(np_, "STORE", str(tmp_path / "absent"))
    steps = {s.name: s for s in np_.plan("7.41f", None, "gametracking", "abc123", dota_path=str(tmp_path))}
    assert steps["register"].skip.startswith("already registered")
    assert steps["fetch"].argv[1:] == ["scripts/fetch/fetch_gametracking.py", "7.41f", "--ref", "abc123"]
    assert steps["shops"].skip and steps["item_stat_lines"].skip and steps["talent_slots"].skip
    assert steps["store"].skip and steps["publish"].skip          # no store on this PC
    assert "exists" in steps["draft"].skip                        # a proofread page is never regenerated
    # 7.41f changes Greedy: the enchant table steps run (since 2026-10-26 any changed enchantment, not only tier boxes)
    assert steps["enchant_values"].skip is None and steps["enchant_table"].skip is None
    assert steps["build"].skip is None and steps["check"].argv[-1] == "7.41f"
    names = list(steps)
    # the store goes to GitHub right after its new patch: Sloppy's CI reads it there (2026-10-24)
    assert names.index("register") < names.index("fetch") < names.index("slim") < names.index("meta") \
        < names.index("store") < names.index("publish") < names.index("npc_units") < names.index("abilities_slim") \
        < names.index("draft") < names.index("thumbs") < names.index("build") < names.index("check")
    # new icons get their small WebP copies before the build points the pages at them (audit 2026-10-26)
    assert steps["thumbs"].argv[1:] == ["tools/make_thumbs.py"] and steps["thumbs"].skip is None
    assert steps["publish"].argv[-1].endswith("publish.py")
    # source game without a local game: the fetch says why it cannot run
    game = {s.name: s for s in np_.plan("7.41f", None, "game", dota_path=str(tmp_path))}
    assert "pak01_dir.vpk" in game["fetch"].skip


def test_a_new_patch_gets_a_draft_and_enchant_steps_wait_for_the_content(monkeypatch, tmp_path):
    steps = {s.name: s for s in np_.plan("9.01", "01.01.2099", "gametracking")}
    assert steps["register"].skip is None and steps["draft"].skip is None
    assert steps["draft"].argv[1:] == ["tools/generate_patch_code_v2.py", "9.01"]
    assert "no enchantment changes" in steps["enchant_values"].skip
    assert steps["store"].argv[-2:] == ["add", "9.01"]              # archives: no --local for the gametracking source
    local = {s.name: s for s in np_.plan("9.01", "01.01.2099", "game")}
    assert local["store"].argv[-3:] == ["add", "9.01", "--local"]


def test_map_status_from_patch_maps_and_from_the_local_map_file(tmp_path):
    maps = {"7.41e": {"sha1": "a" * 40}, "7.41f": {"sha1": "b" * 40}, "7.41g": {"sha1": "b" * 40}}
    assert np_.map_status("7.41f", "game", str(tmp_path), maps)[0] == "changed"
    assert np_.map_status("7.41g", "game", str(tmp_path), maps)[0] == "same"
    assert np_.map_status("7.42", "gametracking", str(tmp_path), maps)[0] == "unknown"
    (tmp_path / "maps").mkdir()
    (tmp_path / "maps" / "dota.vpk").write_bytes(b"new map")
    assert np_.map_status("7.42", "game", str(tmp_path), maps)[0] == "changed"
    maps["7.41g"]["sha1"] = np_._sha1(str(tmp_path / "maps" / "dota.vpk"))
    assert np_.map_status("7.42", "game", str(tmp_path), maps)[0] == "same"


def test_dry_run_runs_and_writes_nothing(monkeypatch, capsys):
    def boom(*a, **k):
        raise AssertionError("dry run must not run anything")
    monkeypatch.setattr(subprocess, "run", boom)
    monkeypatch.setattr(np_, "_run", boom)
    assert np_.main(["9.01", "01.01.2099", "--dry-run", "--source", "gametracking"]) == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out and "tools/generate_patch_code_v2.py 9.01" in out and "Still human" in out
    assert "proofread _generated_p_9.01_v2.py" in out


def test_first_failure_stops_and_says_how_to_resume(monkeypatch, capsys):
    ran = []

    def fake_run(step, version, date):
        ran.append(step.name)
        return 3 if step.name == "slim" else 0
    monkeypatch.setattr(np_, "_run", fake_run)
    assert np_.main(["7.41f", "--source", "gametracking", "--from", "fetch"]) == 1
    assert ran == ["fetch", "slim"]
    out = capsys.readouterr().out
    assert "FAILED at step 'slim' (exit 3)" in out and "--from slim" in out


def test_bad_arguments_are_refused():
    with pytest.raises(SystemExit):
        np_.main(["742", "--dry-run"])
    with pytest.raises(SystemExit):
        np_.main(["7.42", "2026-10-21", "--dry-run"])
    with pytest.raises(SystemExit):
        np_.main(["7.42", "--from", "nope", "--dry-run"])
