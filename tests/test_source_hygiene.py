"""Source hygiene: no invisible control characters in our own text files.

Why (owner 2026-09-26, "backslashes keep breaking things"): code written through shell heredocs and
Python string literals gets its escapes processed twice. A "\\b" meant for a regex becomes chr(8)
(backspace), which compiles fine and silently breaks the regex (Dark Seer innate titles, the
"Damage at level 1" row). "\\n" turning into a real newline breaks the syntax and is caught
anyway; a control character is not. This test catches it.

Game files copied from the client (data/*.txt, data/stats) keep their own bytes and are skipped.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {"\t", "\n", "\r"}
SKIP_PREFIXES = ("data/", "icons/", "dist/")


def _tracked_sources():
    out = subprocess.run(["git", "ls-files", "*.py", "*.js", "*.css", "*.md", "*.html", "*.json"],
                         cwd=HERE, capture_output=True, text=True).stdout.split("\n")
    return [f for f in out if f and not f.startswith(SKIP_PREFIXES)]


def test_no_control_characters_in_sources():
    bad = []
    for f in _tracked_sources():
        path = os.path.join(HERE, f)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                hits = [hex(ord(c)) for c in line if ord(c) < 32 and c not in ALLOWED]
                if hits:
                    bad.append(f"{f}:{n} {hits[:3]}")
    assert bad == [], "invisible control characters (a double-escaped '\\b' / '\\x..'?):\n" + "\n".join(bad[:20])


def test_no_double_full_stop_in_patch_text():
    """A shortened Valve sentence left "250 gold.. Cast Range" on Helm of the Overlord 7.38c (audit 2026-10-05).
    Exactly two dots before a word; "..." stays allowed."""
    import re
    two_dots = re.compile(r"(?<!\.)\.\.(?!\.)\s+[A-Za-z]")
    bad = []
    for f in sorted(os.listdir(os.path.join(HERE, "content"))):
        if not (f.startswith("p") and f.endswith(".py")):
            continue
        with open(os.path.join(HERE, "content", f), encoding="utf-8") as fh:
            bad += [f"{f}:{n}" for n, line in enumerate(fh, 1) if two_dots.search(line)]
    assert bad == [], "'..' inside patch text:\n" + "\n".join(bad[:20])
