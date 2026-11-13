"""Bad-input corpus (robust-tests, owner 2026-11-13, from sqlite.org/testing.html): every outside page that once
broke a parser, or could, is checked forever.

tests/corpus/<parser>/:
  bad_*   - not the page we expect (block page, error JSON, empty): the parser MUST raise PipelineCheckError,
            never answer "0 builds";
  others  - real pages (trimmed): the parser must give a non-empty result.
A new incident = a new file here."""
import importlib.util
from pathlib import Path

import pytest

from patch.checks import PipelineCheckError

ROOT = Path(__file__).resolve().parent.parent
CORPUS = Path(__file__).parent / "corpus"

_spec = importlib.util.spec_from_file_location("fetch_branch_builds", ROOT / "scripts" / "fetch" / "fetch_branch_builds.py")
fetch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fetch)

PARSERS = {
    "telegram": lambda text: fetch.parse_telegram_page(text)[1],
    "history": fetch.parse_history,
}
FILES = sorted((d.name, p) for d in CORPUS.iterdir() if d.is_dir() for p in d.iterdir() if p.is_file())


def test_every_parser_has_good_and_bad_inputs():
    for name in PARSERS:
        names = [p.name for d, p in FILES if d == name]
        assert any(n.startswith("bad_") for n in names) and any(not n.startswith("bad_") for n in names), name


@pytest.mark.parametrize("parser,path", FILES, ids=lambda x: x if isinstance(x, str) else x.name)
def test_corpus_input(parser, path):
    text = path.read_text(encoding="utf-8")
    if path.name.startswith("bad_"):
        with pytest.raises(PipelineCheckError):
            PARSERS[parser](text)
    else:
        assert PARSERS[parser](text), f"{parser}/{path.name}: the parser gave nothing"
