"""With the Liquipedia cache and without it the answer is the same (robust-tests, owner 2026-11-13, from
sqlite.org/testing.html): the cold read (fills the cache), the warm read (from the cache) and a fresh download into an
empty cache all give the same text. And a broken cache index is an error, not a silent re-download of everything."""
import pytest

from patch.checks import PipelineCheckError
from tools import liquipedia_cache as lc

PAGES = {
    "Roshan": "<p>Roshan &amp; the <b>Aegis</b></p>\n<p>respawns   in 8-11 min</p>",
    "Tormentor": "<div>Tormentor<br/>shield &lt;absorbs&gt; damage</div>",
    "Patch 7.41": "<ul><li>Mana&nbsp;Regen</li><li>+1</li></ul>",
}


@pytest.fixture
def fake_liquipedia(tmp_path, monkeypatch):
    calls = []

    def fake_request(params, pause=lc.QUERY_PAUSE):
        calls.append(params["action"])
        if params["action"] == "query":
            return {"query": {"pages": {t: {"title": t, "lastrevid": 7} for t in params["titles"].split("|")}}}
        return {"parse": {"text": {"*": PAGES[params["page"]]}}}

    monkeypatch.setattr(lc, "_request", fake_request)
    monkeypatch.setattr(lc, "ROOT", str(tmp_path / "a"))
    return calls


@pytest.mark.parametrize("title", sorted(PAGES))
def test_cache_does_not_change_the_answer(title, fake_liquipedia, tmp_path, monkeypatch):
    quiet = lambda *_: None  # noqa: E731
    cold = lc.html_text(title, log=quiet)
    warm = lc.html_text(title, log=quiet)
    assert fake_liquipedia.count("parse") == 1, "the warm read downloaded again"
    monkeypatch.setattr(lc, "ROOT", str(tmp_path / "b"))       # a second, empty cache: a plain download
    plain = lc.html_text(title, log=quiet)
    assert cold == plain, "the first read through the cache changes the text"
    assert warm == plain, "the read from the cache changes the text"
    assert plain.strip()


def test_a_broken_index_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(lc, "ROOT", str(tmp_path))
    assert lc.load_index() == {}                                   # no cache yet: empty, fine
    (tmp_path / "index.json").write_text('{"Roshan": {"revid": 3', encoding="utf-8")
    with pytest.raises(PipelineCheckError):
        lc.load_index()
