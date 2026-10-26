"""The icon files are what the pages expect (audit 2026-10-26): every .png is a real PNG (skywrath_mage_ancient_seal.png
was a saved "301 Moved Permanently" page, a broken icon on five pages), and every hero / item / ability icon has the
small WebP copy the pages use (11 were missing: those went to the site full size)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PNG = b"\x89PNG\r\n\x1a\n"


def test_every_png_is_a_png():
    bad = [str(p.relative_to(ROOT)) for p in (ROOT / "icons").rglob("*.png") if p.read_bytes()[:8] != PNG]
    assert not bad, f"not PNG inside (refetch: python scripts/fetch/fetch_icons.py): {bad}"


def test_every_page_icon_has_its_thumbnail():
    missing = [f"{d}/{p.name}" for d in ("heroes", "items", "abilities") for p in (ROOT / "icons" / d).glob("*.png")
               if not (ROOT / "icons" / "_t" / d / (p.stem + ".webp")).exists()]
    assert not missing, f"run python tools/make_thumbs.py: {missing}"
