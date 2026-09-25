"""Publish tools/telegraph_post/out/post.json to telegra.ph (run it YOURSELF).

    python tools/telegraph_post/publish.py            # first run creates a Telegraph account
    python tools/telegraph_post/publish.py --edit URL # update an already published page

The first run creates a Telegraph account (author "sikle | dota.vpk") and keeps its token in
tools/telegraph_post/.telegraph_token (git-ignored) — later runs reuse it, so you can edit the page.
Images must already be live on the site (commit + push icons/telegraph/ first).
"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
TOKEN_FILE = HERE / ".telegraph_token"
API = "https://api.telegra.ph/"
AUTHOR = "sikle | dota.vpk"
AUTHOR_URL = "https://sikleq.github.io/Sloppy/"


def call(method, **params):
    data = urllib.parse.urlencode({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                                   for k, v in params.items()}).encode()
    with urllib.request.urlopen(API + method, data=data, timeout=30) as r:
        res = json.loads(r.read().decode())
    if not res.get("ok"):
        sys.exit(f"Telegraph error in {method}: {res.get('error')}")
    return res["result"]


def token():
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    acc = call("createAccount", short_name="sloppy", author_name=AUTHOR, author_url=AUTHOR_URL)
    TOKEN_FILE.write_text(acc["access_token"], encoding="utf-8")
    print("  Telegraph account created, token saved to", TOKEN_FILE.name)
    return acc["access_token"]


def main():
    post = json.loads((HERE / "out" / "post.json").read_text(encoding="utf-8"))
    tok = token()
    common = dict(access_token=tok, title=post["title"], author_name=AUTHOR, author_url=AUTHOR_URL,
                  content=post["content"], return_content="false")
    if "--edit" in sys.argv:
        path = sys.argv[sys.argv.index("--edit") + 1].rstrip("/").rsplit("/", 1)[-1]
        page = call("editPage/" + path, **common)
    else:
        page = call("createPage", **common)
    print("  ", page["url"])


if __name__ == "__main__":
    main()
