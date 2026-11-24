"""Screenshots of the real hero-page filter rail on the 8765 site."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "shots"
PICK = {"heroes/invoker": "Quas", "heroes/brewmaster": "Primal Split", "heroes/chen": "Martyrdom", "items/blink-dagger": ""}


def main() -> None:
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", args=["--browser-test"])
        try:
            pg = b.new_context(viewport=dict(width=1440, height=900)).new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            for page, ab in PICK.items():
                pg.goto(f"http://localhost:8765/{page}.html")
                pg.wait_for_timeout(600)
                if ab:
                    pg.click(f'.ec-ab-btn[data-ec-ability="{ab}"]')
                    pg.hover(f'.ec-ab-btn[data-ec-ability="{ab}"]')
                pg.wait_for_timeout(300)
                info = pg.evaluate("() => { const r=document.getElementById('filter-pop'); const c=document.querySelector('.container').getBoundingClientRect(); return {hidden: r && r.hidden, left: r && Math.round(r.getBoundingClientRect().left), right: Math.round(c.right), shown: document.querySelectorAll('section.ec-patch:not(.ec-scope-hide)').length}; }")
                print(page, info)
                pg.screenshot(path=str(OUT / f"real_{page.split('/')[1]}.png"))
            print("errors:", errs)
        finally:
            b.close()


if __name__ == "__main__":
    main()
