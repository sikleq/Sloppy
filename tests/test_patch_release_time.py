"""A patch's exact release time (owner 2026-11-11: "из билдов"): the minute the live game first had the patch's own
build — its ClientVersion (data/patch_client_versions.json, tools/build_patch_client_versions.py) looked up in the
live-game log of data/branch_builds.json. "The first live build of the patch's day" was wrong for 17 of 46 patches."""
import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path

from patch import branch_builds as bb

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("bpcv", ROOT / "tools" / "build_patch_client_versions.py")
bpcv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bpcv)


def _pub(version, iso):
    return {"branch": "public", "version": version, "time": datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)}


def test_the_patch_build_wins_over_an_earlier_hotfix_of_its_day():
    # 7.41: 24.03 00:00 was a fix of 7.40c; 7.41 itself (6728) came at 23:49
    builds = [_pub(6727, "2026-03-24T00:00:37"), _pub(6728, "2026-03-24T23:49:10")]
    m = bb.patch_moments([("7.41", date(2026, 3, 24))], builds, client_versions={"7.41": 6728})
    assert m["7.41"] == (datetime(2026, 3, 24, 23, 49, 10, tzinfo=timezone.utc), True)


def test_without_a_client_version_the_first_build_of_the_day_stays():
    builds = [_pub(6727, "2026-03-24T00:00:37"), _pub(6728, "2026-03-24T23:49:10")]
    m = bb.patch_moments([("7.41", date(2026, 3, 24))], builds, client_versions={})
    assert m["7.41"] == (datetime(2026, 3, 24, 0, 0, 37, tzinfo=timezone.utc), True)


def test_a_client_version_missing_from_the_log_falls_back():
    builds = [_pub(6727, "2026-03-24T00:00:37")]
    m = bb.patch_moments([("7.41", date(2026, 3, 24))], builds, client_versions={"7.41": 6728})
    assert m["7.41"][0].strftime("%H:%M") == "00:00"


def test_the_real_data_gives_the_release_minutes():
    assert bb.release_time("7.41").strftime("%d.%m.%Y %H:%M") == "24.03.2026 23:49"
    assert bb.release_time("7.39").strftime("%d.%m.%Y %H:%M") == "22.05.2025 22:12"
    assert bb.release_time("7.41a").strftime("%d.%m.%Y %H:%M") == "27.03.2026 22:17"
    assert bb.release_time("7.08") is None                      # older than the builds log


def test_steam_inf_client_version():
    assert bpcv.client_version("ClientVersion=6412\nServerVersion=6412\n") == 6412
    assert bpcv.client_version("") is None and bpcv.client_version(None) is None


def test_the_table_keeps_old_rows_and_sorts_by_build():
    assert list(bpcv.merge({"7.41": 6728, "7.40": 6644}, {"7.41a": 6743, "7.41": 6729})) == ["7.40", "7.41", "7.41a"]


def test_the_patch_card_says_the_minute_and_old_patches_their_date():
    from patch.page import patch_info_html
    assert '<span class="pi-val"><b>24.03.2026</b> 23:49 UTC</span>' in patch_info_html("7.41", "24.03.2026")
    assert '<span class="pi-val"><b>01.02.2018</b></span>' in patch_info_html("7.08", "01.02.2018")


def test_new_patch_records_the_client_version():
    text = (ROOT / "tools" / "new_patch.py").read_text(encoding="utf-8")
    assert 'Step("client_version"' in text and "build_patch_client_versions.py" in text
