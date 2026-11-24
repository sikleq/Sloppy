"""Screenshots of the hero-page filter rail mock-ups (served by the 8765 site, pages dist/heroes/_mock_<hero>.html)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "shots"
PICK = {"invoker": "Quas", "brewmaster": "Primal Split", "pudge": "Dismember"}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", args=["--browser-test"])
        try:
            pg = b.new_context(viewport=dict(width=1440, height=900)).new_page()
            for hero, ab in PICK.items():
                for v in ("list", "grid"):
                    pg.goto(f"http://localhost:8765/heroes/_mock_{hero}.html?v={v}")
                    pg.wait_for_selector(".mock-rail")
                    pg.evaluate("n => { const b=[...document.querySelectorAll('.mock-ab')].find(x => (x.textContent||x.title)===n || x.title===n); if (b) b.click(); }", ab)
                    pg.wait_for_timeout(400)
                    pg.screenshot(path=str(OUT / f"{hero}_{v}.png"))
        finally:
            b.close()


if __name__ == "__main__":
    main()
