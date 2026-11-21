"""patch/game_files.read_bytes reads through one `git cat-file --batch` (Fable review 2026-11-21: ~2 700 `git show`
processes were half the build) and gives byte for byte what `git show` gives; a missing file is None."""
import subprocess

import pytest

from patch import game_files


def test_the_batch_reader_matches_git_show():
    if not game_files.available():
        pytest.skip("no game-files store")
    v = sorted(game_files.versions())[-1]
    for rel in ("scripts/npc/items.txt", "scripts/npc/heroes/npc_dota_hero_nyx_assassin.txt",
                "resource/localization/abilities_english.txt"):
        want = subprocess.run(["git", "-C", str(game_files.STORE), "show", f"{v}:files/{rel}"],
                              capture_output=True).stdout
        if not want:
            continue
        assert game_files.read_bytes(v, rel) == want
    assert game_files.read_bytes(v, "no/such/file.txt") is None
    assert game_files.read_bytes("0.00-no-such-tag", "scripts/npc/items.txt") is None
    # still in step after a miss: the next read is right
    assert game_files.read_bytes(v, "scripts/npc/items.txt")[:2] in (b'"D', b"\xef\xbb", b"//", b"\xff\xfe")
