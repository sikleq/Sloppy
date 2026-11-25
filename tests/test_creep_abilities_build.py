"""data/creep_abilities.json comes from the repo's data/stats (the script once looked in scripts/data and quietly
wrote nothing: 7.42's new creeps were missing, 7.42a Radigull's Eggstremism row had no ability block)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_the_new_creeps_are_in_the_map():
    data = json.loads((ROOT / "data" / "creep_abilities.json").read_text(encoding="utf-8"))
    assert data.get("npc_dota_neutral_radigull") == ["radigull_eggstremism"]


def test_a_missing_patch_is_an_error():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "gen" / "build_creep_abilities.py"), "0.00"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "Not found" in r.stderr
