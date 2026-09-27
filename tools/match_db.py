"""Path of the Tier 1-2 pro match database used by the weights tools, or None.

It is never written in the repo: the MATCH_DB environment variable, else the first line of
~/.sloppy/match_db.txt (a local file outside the repo).
"""
import os


def match_db_path():
    p = os.environ.get("MATCH_DB")
    if not p:
        cfg = os.path.join(os.path.expanduser("~"), ".sloppy", "match_db.txt")
        if os.path.exists(cfg):
            with open(cfg, encoding="utf-8") as f:
                p = f.readline().strip()
    return p or None
