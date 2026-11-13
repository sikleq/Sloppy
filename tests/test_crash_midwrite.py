"""Killed mid-write (robust-tests, owner 2026-11-13, from sqlite.org/testing.html): data/branch_builds.json and the
Liquipedia cache are read by the site, the auto-deploy and later runs, so after a crash they are the old file whole or
the new file whole, never half of one. A child process rewrites the file in a loop; the test kills it at a random
moment and reads the file."""
import gzip
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ROUNDS = 6
BUILDS = 40_000            # ~3 MB of JSON: long enough to be killed in the middle of writing

SAVE_WRITER = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("f", r"{root}/scripts/fetch/fetch_branch_builds.py")
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
path = Path(sys.argv[1])
def data(v):
    return {{"checks": {{}}, "builds": [{{"branch": "staging", "from": i, "version": v, "time": "2026-01-01T00:00:00Z",
                                       "source": "x", "timed": True}} for i in range({n})]}}
a, b = data(1), data(2)
open(str(path) + ".ready", "w").close()
while True:
    f.save(b, path)
    f.save(a, path)
"""

LP_WRITER = """
import sys
sys.path.insert(0, r"{root}")
from tools import liquipedia_cache as lc
lc.ROOT = sys.argv[1]
open(sys.argv[1] + "/.ready", "w").close()
while True:
    lc._write("wikitext", "Page", "B" * {n})
    lc._write("wikitext", "Page", "A" * {n})
"""


def _kill_midway(code, arg, ready):
    proc = subprocess.Popen([sys.executable, "-c", code, str(arg)], cwd=ROOT)
    try:
        deadline = time.monotonic() + 20
        while not ready.exists():
            assert time.monotonic() < deadline, "the writer did not start"
            time.sleep(0.01)
        time.sleep(random.uniform(0.02, 0.4))
    finally:
        proc.kill()
        proc.wait()
    ready.unlink()


def _builds(v):
    return {"checks": {}, "builds": [{"branch": "staging", "from": i, "version": v, "time": "2026-01-01T00:00:00Z",
                                      "source": "x", "timed": True} for i in range(BUILDS)]}


@pytest.fixture(scope="module")
def fetch():
    import importlib.util
    spec = importlib.util.spec_from_file_location("fetch_branch_builds",
                                                  ROOT / "scripts" / "fetch" / "fetch_branch_builds.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_branch_builds_json_is_old_or_new_after_a_crash(tmp_path, fetch):
    old, new = tmp_path / "old.json", tmp_path / "new.json"
    fetch.save(_builds(1), old)
    fetch.save(_builds(2), new)
    whole = {old.read_bytes(), new.read_bytes()}
    target = tmp_path / "branch_builds.json"
    code = SAVE_WRITER.format(root=ROOT.as_posix(), n=BUILDS)
    for n in range(ROUNDS):
        target.write_bytes(old.read_bytes())
        _kill_midway(code, target, Path(str(target) + ".ready"))
        got = target.read_bytes()
        assert got in whole, f"round {n}: branch_builds.json is cut ({len(got)} bytes)"


def test_liquipedia_cache_page_is_old_or_new_after_a_crash(tmp_path):
    size = 3_000_000
    page = tmp_path / "wikitext" / "Page.txt.gz"
    code = LP_WRITER.format(root=ROOT.as_posix(), n=size)
    for n in range(ROUNDS):
        page.parent.mkdir(exist_ok=True)
        page.write_bytes(gzip.compress(b"A" * size))
        _kill_midway(code, tmp_path, tmp_path / ".ready")
        try:
            text = gzip.decompress(page.read_bytes())
        except (EOFError, OSError) as e:
            pytest.fail(f"round {n}: cached page is cut ({e})")
        assert text in (b"A" * size, b"B" * size), f"round {n}: cached page is mixed"
    leftovers = [p for p in page.parent.iterdir() if p.suffix == ".tmp"]
    for p in leftovers:          # a killed writer may leave its temp file: harmless, the real one is whole
        os.unlink(p)
