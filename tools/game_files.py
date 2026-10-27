"""Command line of the game-files store; the library is patch/game_files.py (audit 2026-10-26 #6: patch/ is the core,
tools/ only the commands).

    python tools/game_files.py materialize [<version> ...]     (env DOTA_FILES_DIR = the store)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patch.game_files import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
