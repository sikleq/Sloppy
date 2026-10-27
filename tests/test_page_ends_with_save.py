"""Nothing is written after a page's save_html (2026-10-27: 7.38c's last talent block sat after it, so the 7.39 page
opened with that row above its header and lost its layout)."""
import ast
import glob
import os

import pytest

from patch import output, page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_no_content_file_writes_after_save_html():
    bad = []
    for path in glob.glob(os.path.join(ROOT, "content", "p*.py")):
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
            saved = False
            for st in fn.body:
                call = st.value if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) else None
                name = getattr(getattr(call, "func", None), "id", None)
                if name == "save_html":
                    saved = True
                elif saved and name == "W":
                    bad.append(f"{os.path.basename(path)}:{st.lineno}")
    assert not bad, bad


def test_a_page_refuses_to_start_on_leftovers(monkeypatch):
    monkeypatch.setattr(output, "H", ["<li>left over</li>"])
    monkeypatch.setattr(page, "H", output.H)
    with pytest.raises(RuntimeError, match="written after the previous page was saved"):
        page.write_head("7.39", "21.05.2025")
