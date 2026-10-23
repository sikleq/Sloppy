"""Local cache of Liquipedia Dota 2 pages for mechanics research (owner 2026-10-23: no repeat requests for the same
page, only the sections we need, never get blocked again).

    python tools/liquipedia_cache.py sync heroes items mechanics   # hero / item / mechanics pages + their /Changelogs
    python tools/liquipedia_cache.py sync --title "Roshan" --title "Lane Creeps"
    python tools/liquipedia_cache.py get "Anti-Mage/Changelogs"     # wikitext from the cache
    python tools/liquipedia_cache.py html "Roshan"                  # rendered text (templates filled in), cached
    python tools/liquipedia_cache.py grep "Glyph" --in Changelogs   # search the cache, no network

Liquipedia API terms (liquipedia.net/api-terms-of-use): gzip, a User-Agent with contact, one request per 2 s, action=parse
one per 30 s. Every request here goes through `_throttle`, which keeps the pause across processes (a time stamp file), so
two runs at once still respect it. Wikitext comes from action=query in batches (up to 50 titles per request); a page is
downloaded again only when its revision id on Liquipedia changed. On HTTP 429 the run stops at once and keeps what it has.

The cache lives in outputs/liquipedia/ (not in git: Liquipedia text is CC BY-SA, and the files are large).
"""
import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(HERE, "outputs", "liquipedia")
API = "https://liquipedia.net/dota2/api.php"
UA = "SloppyResearch/1.0 (https://github.com/sikleq/Sloppy)"
QUERY_PAUSE = 2.2          # seconds between any two requests
PARSE_PAUSE = 31.0         # action=parse
BATCH_INFO = 50            # titles per prop=info request (API maximum)
BATCH_TEXT = 20            # titles per content request (keeps answers small)
SETS = {                   # set -> category whose members (and their /Changelogs) we keep
    "heroes": "Category:Heroes",
    "items": "Category:Items",
    "mechanics": "Category:Mechanics",
}


class Blocked(RuntimeError):
    """Liquipedia answered 429: stop, do not retry in this run."""


def _stamp_path():
    return os.path.join(ROOT, ".last_request")


def _throttle(pause, now=time.time, sleep=time.sleep):
    """Wait until `pause` seconds passed since the last request of ANY run, then mark this one."""
    os.makedirs(ROOT, exist_ok=True)
    try:
        last = float(open(_stamp_path()).read() or 0)
    except (OSError, ValueError):
        last = 0.0
    wait = last + pause - now()
    if wait > 0:
        sleep(wait)
    with open(_stamp_path(), "w") as f:
        f.write(str(now()))


def _request(params, pause=QUERY_PAUSE):
    _throttle(pause)
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            if r.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise Blocked("Liquipedia: 429 Too Many Requests — stopped, try again later") from e
        raise
    data = json.loads(raw)
    if "error" in data:
        raise RuntimeError(f"Liquipedia API error: {data['error'].get('code')} {data['error'].get('info')}")
    return data


# ---- cache files ----

def _safe(title):
    return re.sub(r'[<>:"/\\|?*]', "_", title).strip() or "_"


def _index_path():
    return os.path.join(ROOT, "index.json")


def load_index():
    try:
        return json.load(open(_index_path(), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_index(index):
    os.makedirs(ROOT, exist_ok=True)
    tmp = _index_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, _index_path())


def _file(kind, title):
    return os.path.join(ROOT, kind, _safe(title) + (".txt.gz" if kind == "wikitext" else ".html.txt.gz"))


def _write(kind, title, text):
    path = _file(kind, title)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(text)


def read(kind, title):
    path = _file(kind, title)
    if not os.path.exists(path):
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return f.read()


# ---- what to fetch ----

def category_members(category):
    titles, cont = [], {}
    while True:
        d = _request({"action": "query", "list": "categorymembers", "cmtitle": category, "cmlimit": 500,
                      "cmnamespace": 0, **cont})
        titles += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" not in d:
            return titles
        cont = d["continue"]


def revisions(titles):
    """title -> last revision id (None = page missing), batched by 50."""
    out = {}
    for i in range(0, len(titles), BATCH_INFO):
        d = _request({"action": "query", "prop": "info", "titles": "|".join(titles[i:i + BATCH_INFO])})
        for p in d["query"]["pages"].values():
            out[p["title"]] = None if "missing" in p else p.get("lastrevid")
    return out


def stale(titles, remote, index):
    """Titles whose wikitext must be (re)downloaded: present on Liquipedia and new or changed since the cache."""
    return [t for t in titles if remote.get(t) and index.get(t, {}).get("revid") != remote[t]]


def fetch_wikitext(titles, index):
    for i in range(0, len(titles), BATCH_TEXT):
        d = _request({"action": "query", "prop": "revisions", "rvprop": "content|ids", "rvslots": "main",
                      "titles": "|".join(titles[i:i + BATCH_TEXT])})
        for p in d["query"]["pages"].values():
            rev = (p.get("revisions") or [None])[0]
            if not rev:
                continue
            _write("wikitext", p["title"], rev["slots"]["main"]["*"])
            index.setdefault(p["title"], {}).update(revid=rev["revid"], fetched=time.strftime("%Y-%m-%d"))
        save_index(index)                     # keep progress if a later batch is blocked


def sync(titles, log=print):
    index = load_index()
    remote = revisions(titles)
    missing = sorted(t for t in titles if remote.get(t) is None)
    todo = stale(titles, remote, index)
    log(f"{len(titles)} pages: {len(todo)} new or changed, {len(titles) - len(todo) - len(missing)} up to date, "
        f"{len(missing)} not on Liquipedia")
    fetch_wikitext(todo, index)
    return todo


def html_text(title, log=print):
    """Rendered page as plain text (templates filled in) — action=parse, 31 s apart, cached per revision."""
    index = load_index()
    rev = revisions([title]).get(title)
    if rev is None:
        raise KeyError(f"no page {title!r} on Liquipedia")
    entry = index.setdefault(title, {})
    if entry.get("html_revid") == rev and read("html", title) is not None:
        return read("html", title)
    log(f"parse {title} (rev {rev})")
    d = _request({"action": "parse", "page": title, "prop": "text"}, pause=PARSE_PAUSE)
    import html as _html
    text = _html.unescape(re.sub(r"<[^>]+>", " ", d["parse"]["text"]["*"]))
    text = re.sub(r"\s+", " ", text)
    _write("html", title, text)
    entry.update(html_revid=rev)
    save_index(index)
    return text


def set_titles(names, log=print):
    titles = []
    for name in names:
        members = category_members(SETS[name])
        log(f"{name}: {len(members)} pages in {SETS[name]}")
        titles += members + [m + "/Changelogs" for m in members]
    return sorted(set(titles))


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync")
    s.add_argument("sets", nargs="*", choices=sorted(SETS))
    s.add_argument("--title", action="append", default=[])
    sub.add_parser("get").add_argument("title")
    sub.add_parser("html").add_argument("title")
    g = sub.add_parser("grep")
    g.add_argument("pattern")
    g.add_argument("--in", dest="title_rx", default="", help="only titles matching this regex")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "sync":
            titles = set_titles(a.sets) + a.title
            if not titles:
                ap.error("name a set or --title")
            sync(sorted(set(titles)))
        elif a.cmd == "get":
            text = read("wikitext", a.title)
            if text is None:
                sync([a.title])
                text = read("wikitext", a.title)
            print(text if text is not None else f"no page {a.title!r}")
        elif a.cmd == "html":
            print(html_text(a.title))
        else:
            rx = re.compile(a.pattern, re.I)
            trx = re.compile(a.title_rx, re.I)
            for title in sorted(load_index()):
                text = read("wikitext", title) if trx.search(title) else None
                for line in (text or "").splitlines():
                    if rx.search(line):
                        print(f"{title}: {line.strip()[:300]}")
    except Blocked as e:
        print(e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
