# -*- coding: utf-8 -*-
"""Canonical-phrase tag linter (adversarial re-tagging) for content/p<version>.py.

Silent-wrong-tag catcher. For every hand-written `W(li("<text>", t("<TAG>")))`
row it RE-DERIVES the tag from the text alone with generate_patch_code_v2._guess_tag
(the same canonical-phrase heuristic used to seed drafts) and flags any row whose
declared t("...") tag disagrees. A disagreement is NOT proof of a bug — it is a
mandatory human decision point (the whole reason a plausible-but-wrong tag is easy
to miss by eye).

Scope on purpose: only rows tagged with a TEXT tag t("NEW/DEL/REWORK/BUFF/NERF/
QoL/MISC"). Numeric-badge rows (b()/bf()/bstat_*) carry direction in the badge, not
a text tag, and are checked by test_badges.py / the l=True rules instead.

Usage:
    python tools/lint_tags.py content/p742.py
    python tools/lint_tags.py            # all content/p*.py

Exit code 1 if any disagreement is found (so it can gate a build step).
"""
import ast
import glob
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _ROOT)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from tools.generate_patch_code_v2 import _guess_tag  # noqa: E402   (tools/ since 2026-10-27)

# Every li(...) call is read with the AST (2026-10-16: a regex over the source skipped 448 of 1100 rows of 7.41 —
# a row without t() swallowed the next row, so Pipe of Insight's "no longer affects" NERF and the neutral items'
# "Tier 1 availability" BUFF went unseen). Rows with a numeric badge (b()/bf()/br()/bstat_*) carry their direction
# in the badge: the text tag there is a render bucket, not a phrase claim -> skipped.
_BADGES = {"b", "bf", "br", "bstat_h", "bstat_i"}
_TARGETING_RE = re.compile(r"\b(?:Unit|Point|Vector|No)[\w ]*Target(?:ed)?\b|\btargeting\b", re.I)


def _name(node):
    return node.func.id if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) else None


def _text_of(node):
    """The row text: string constants joined (a concatenated scale pill's own text is left out)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp):
        return _text_of(node.left) + _text_of(node.right)
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value for v in node.values if isinstance(v, ast.Constant))
    return ""


def li_rows(path):
    """(lineno, text, declared tag or "", force_tag or "", has_badge) of every li() call in the file."""
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    for node in ast.walk(tree):
        if _name(node) != "li" or not node.args:
            continue
        calls = [a for a in node.args[1:] if isinstance(a, ast.Call)]
        tag = next((c.args[0].value for c in calls if _name(c) == "t" and c.args
                    and isinstance(c.args[0], ast.Constant)), "")
        force = next((k.value.value for k in node.keywords if k.arg == "force_tag"
                      and isinstance(k.value, ast.Constant)), "")
        badge = any(_name(c) in _BADGES for c in calls)
        yield node.lineno, _strip_html(_text_of(node.args[0])), str(tag), str(force), badge


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s).strip()


def lint_file(path: str):
    """Return list of (lineno, text, declared, guessed) disagreements."""
    out = []
    rows = sorted(li_rows(path))
    for i, (lineno, text, declared, force, badge) in enumerate(rows):
        declared = declared.strip().upper()
        # a targeting change ("Now a Unit Vector Target Spell") with the new behaviour on the very next row tagged
        # NEW is MISC: the novelty is counted once, on the behaviour row (Bane 7.41). Alone, it is NEW itself
        # (Grimstroke 7.39). docs/agent-rules/patch-tags.md, owner 2026-10-21.
        nxt = rows[i + 1] if i + 1 < len(rows) else None
        if (declared == "MISC" and _TARGETING_RE.search(text) and nxt and nxt[0] - lineno <= 3
                and nxt[2].strip().upper() == "NEW"):
            continue
        if not text or not declared or badge:
            continue
        guessed = (_guess_tag(text) or "").upper()
        # MISC is the heuristic's "no opinion" fallback for prose without a canonical phrase -> not a signal. Only
        # positive canonical assertions (NEW/DEL/REWORK/BUFF/NERF/QoL) are worth a mandatory decision.
        if not guessed or guessed == "MISC":
            continue
        # accept if the guess matches the visible tag OR any token in a force_tag combo
        allowed = {t.upper() for t in declared.split()} | {t.upper() for t in force.split()}
        if guessed not in allowed:
            out.append((lineno, text, declared, guessed))
    return sorted(out)


def main(argv):
    targets = argv[1:] or sorted(glob.glob(os.path.join(_ROOT, "content", "p*.py")))
    total = 0
    for path in targets:
        rows = lint_file(path)
        if not rows:
            continue
        rel = os.path.relpath(path, _ROOT)
        print(f"\n{rel}: {len(rows)} tag disagreement(s) to decide")
        for lineno, text, declared, guessed in rows:
            snippet = text if len(text) <= 90 else text[:87] + "..."
            print(f"  L{lineno}: declared {declared:7} | canonical says {guessed:7} | {snippet}")
        total += len(rows)
    if total:
        print(f"\n{total} disagreement(s). Each is a REQUIRED decision, not an auto-fix:")
        print("  - canonical right -> fix the tag in content/pX.py")
        print("  - canonical wrong -> it's a real exception; leave tag, note why in review report")
        return 1
    print("No canonical-phrase tag disagreements.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
