"""Screenshots for the site changelog (icons/changelog/*.webp) — tight, on the change itself.

Point it at a running copy of dist/ (default http://localhost:8799: `python -m http.server
8799` from dist/). A shot = a page + a SCOPE (the whole page, one patch-page entity block by
its name, or one row by its text) + the PARTS inside it to frame (CSS selectors, their
union is captured, not the whole block) + optional elements to CLICK first (e.g. a formula
trigger so its table is open) + a max height.

    python tools/changelog_shots.py            # all shots
    python tools/changelog_shots.py tormentor  # shots whose file name contains "tormentor"
"""
import io
import pathlib
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "icons" / "changelog"
BASE = "http://localhost:8799/"
WIDTH = 1280
PAD = 6

# file: (page, scope, parts, clicks, max_h)
#   scope = None (page) | ("block", "<entity name>") | ("row", "<row text>")
#   parts = selectors inside the scope (":scope" = the scope itself)
SHOTS = {
    "2026-09-24_tormentor.webp": ("patches/7.38.html", ("block", "Tormentor"),
                                  [":scope > .entity", ":scope > ul.changes"], [], 560),
    "2026-09-24_tormentor_card.webp": ("patches/7.38.html", ("block", "Tormentor"),
                                       [":scope > .ability-change-block >> nth=0"],
                                       [":scope > .ability-change-block >> nth=0 >> .ability-change-new .formula-trigger >> nth=0"], 520),
    "2026-09-24_lifesteal.webp": ("patches/7.38.html", ("block", "Lifesteal"), [":scope"], [], 300),
    "2026-09-24_abyssal.webp": ("patches/7.38.html", ("block", "Abyssal Blade"),
                                [":scope > .properties-change", ":scope > ul.changes"], [], 260),
    "2026-09-24_orb_of_frost.webp": ("patches/7.38.html", ("block", "Orb of Frost"), [":scope"], [], 220),
    "2026-09-24_bounty.webp": ("patches/7.38.html", ("row", "Gold provided after the initial set"),
                               [":scope"], [":scope .formula-trigger >> nth=0"], 220),
    "2026-09-23_roshan.webp": ("units/roshan.html", None,
                               [".container > section >> nth=0", ".container > section >> nth=1"], [], 330),
    "2026-09-22_unit_changes.webp": ("unit_changes.html", None, [".ec-ugrid"], [], 420),
    "2026-09-17_hero_changes.webp": ("hero_changes.html", None, [".ec-index-body"], [], 420),
}


def _scope(page, scope):
    if scope is None:
        return page.locator("body")
    kind, text = scope
    if kind == "block":
        name = page.locator(".entity-name").filter(has_text=text)
        return page.locator(".entity-block").filter(has=name).first
    return page.locator("li").filter(has_text=text).last          # the row itself, not its parents


def _union_box(page, locs):
    boxes = [loc.evaluate("e => { const r = e.getBoundingClientRect();"
                          " return [r.left + scrollX, r.top + scrollY, r.right + scrollX, r.bottom + scrollY]; }")
             for loc in locs]
    x0 = min(b[0] for b in boxes) - PAD
    y0 = min(b[1] for b in boxes) - PAD
    x1 = max(b[2] for b in boxes) + PAD
    y1 = max(b[3] for b in boxes) + PAD
    return {"x": max(0, x0), "y": max(0, y0), "width": x1 - max(0, x0), "height": y1 - max(0, y0)}


def shoot(page, name, spec):
    url, scope, parts, clicks, max_h = spec
    page.goto(BASE + url, wait_until="networkidle")
    root = _scope(page, scope)
    root.scroll_into_view_if_needed()
    for sel in clicks:
        root.locator(sel).first.click()
        page.wait_for_timeout(250)
    locs = [root if p == ":scope" else root.locator(p).first for p in parts]
    locs[0].scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    # pinned header / toolbars / floating buttons would paint over the shot: hide every
    # fixed or sticky element that doesn't hold the framed parts
    for loc in locs:
        loc.evaluate("e => e.setAttribute('data-shot', '1')")
    page.evaluate("""() => {
        const keep = [...document.querySelectorAll('[data-shot]')];
        for (const el of document.querySelectorAll('body *')) {
            const pos = getComputedStyle(el).position;
            if ((pos === 'fixed' || pos === 'sticky') && !keep.some(k => el.contains(k)))
                el.style.setProperty('opacity', '0', 'important');
        }
    }""")
    clip = _union_box(page, locs)
    clip["height"] = min(clip["height"], max_h)
    img = Image.open(io.BytesIO(page.screenshot(full_page=True, clip=clip))).convert("RGB")
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / name, "WEBP", quality=85, method=6)
    print(f"  {name}: {img.width}x{img.height}")


def main(only=None):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": 900})
        for name, spec in SHOTS.items():
            if not only or only in name:
                shoot(page, name, spec)
        browser.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
