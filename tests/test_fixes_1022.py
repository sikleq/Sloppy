"""Content fixes of 2026-10-22 (owner's 7.41 review): the old -> new arrow already names the replaced ability."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _calls(path, name):
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.split("\n")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
            yield node, lines


def _kw(node, name):
    return next((k.value for k in node.keywords if k.arg == name), None)


def _rows_after(node, lines):
    """The li() lines of the list right under a card."""
    k = node.end_lineno
    while k < len(lines) and lines[k].strip() in ("))", ")", ""):
        k += 1
    if k >= len(lines) or "ul_open" not in lines[k]:
        return []
    out = []
    k += 1
    while k < len(lines) and "ul_close" not in lines[k]:
        out.append(lines[k])
        k += 1
    return out


def _name(side):
    if isinstance(side, ast.Call):
        v = _kw(side, "name")
        if isinstance(v, ast.Constant):
            return v.value
    return None


def test_no_summary_names_the_replaced_ability():
    # Beastmaster 7.41 "Inner Beast is now the innate ability (replaces Rugged)."
    bad = []
    for f in sorted((ROOT / "content").glob("p*.py")):
        for node, _ in _calls(f, "ability_change"):
            s = _kw(node, "summary")
            if isinstance(s, ast.Constant) and ("replaces" in s.value or "removed;" in s.value):
                bad.append(f"{f.name}:{node.lineno} {s.value}")
    assert not bad, bad


def test_no_rename_row_under_an_arrow_header():
    # Dark Seer 7.41 "Aggrandize renamed to Quick Wit" under the Aggrandize -> Quick Wit card
    bad = []
    for f in sorted((ROOT / "content").glob("p*.py")):
        for node, lines in _calls(f, "ability_change"):
            old, new = _name(_kw(node, "old")), _name(_kw(node, "new"))
            if old and new and old != new:
                bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if "renamed to" in r]
        for node, lines in _calls(f, "ability"):
            if _kw(node, "old_title") is not None:
                bad += [f"{f.name}: {r.strip()}" for r in _rows_after(node, lines) if "renamed to" in r]
    assert not bad, bad


def test_ability_audit_ignores_sub_ability_slugs():
    # audit-live 2026-10-22 failed: sub_ability("rattletrap_jetpack", "Jetpack") was read as ability("rattletrap_jetpack")
    import subprocess
    import sys
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit" / "audit_abilities.py")],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0, r.stdout[-2000:]
    assert "rattletrap_rattletrap" not in r.stdout


def test_quick_wit_card_highlights_the_new_attack_speed():
    import pytest
    page = ROOT / "dist" / "patches" / "7.41.html"
    if not page.exists():
        pytest.skip("site not built")
    html = page.read_text(encoding="utf-8")
    assert '<span class="iab-hl iab-hl-new">Also provides Dark Seer with' in html
    assert "Aggrandize renamed to Quick Wit" not in html
