"""check_icons.py — Verify every ability icon referenced in built HTML
either exists as a local file under icons/abilities/, or is on the
explicit KNOWN_INNATE_NO_CDN_ICON allowlist (innates Valve publishes no
public CDN art for; rendered via the elements.py fallback path).

A missing file that is NOT on the allowlist fails the build, even if the
HTML carries an onerror fallback — the allowlist is the authoritative
source of "intentionally fallback-rendered", not the markup itself.
Run after build_site.py.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = ROOT / "dist"
ICONS_DIR = ROOT / "icons" / "abilities"

# Mirror of audit_abilities.py's KNOWN_INNATE_NO_CDN_ICON. Duplicated to
# avoid making this script depend on the patch package / live Valve
# fetch that audit_abilities.py performs at import time.
KNOWN_INNATE_NO_CDN_ICON = {
    "queenofpain_succubus.png",
    "terrorblade_dark_unity.png",
}

if not DIST_DIR.exists():
    print("dist/ not found. Run python build_site.py first.")
    sys.exit(1)

# Collect <img ...> tags whose src references icons/abilities/*.png, and note
# whether each tag also carries an onerror fallback to innate_icon.png.
img_re = re.compile(r'<img\b[^>]*\bsrc="[^"]*icons/abilities/([^"/]+\.png)"[^>]*>')
referenced = {}  # slug -> True if every occurrence has the innate fallback
for html_file in DIST_DIR.rglob("*.html"):
    text = html_file.read_text(encoding="utf-8", errors="replace")
    for m in img_re.finditer(text):
        slug = m.group(1)
        has_fallback = "innate_icon.png" in m.group(0)
        referenced[slug] = referenced.get(slug, True) and has_fallback

print(f"Ability icon references found in dist/: {len(referenced)}")

missing = sorted(s for s in referenced if not (ICONS_DIR / s).exists())
allowed_missing = [s for s in missing if s in KNOWN_INNATE_NO_CDN_ICON]
real_missing = [s for s in missing if s not in KNOWN_INNATE_NO_CDN_ICON]
ok_count = len(referenced) - len(missing)

# A markup-level onerror fallback is necessary for allowlisted slugs but
# not sufficient on its own — a missing fallback on an allowlisted slug
# is still a bug worth surfacing.
fallback_gap = [s for s in allowed_missing if not referenced[s]]

print(f"OK:                          {ok_count}")
print(f"Missing (allowlisted, no CDN): {len(allowed_missing)}")
print(f"Missing (not allowlisted):    {len(real_missing)}")

if allowed_missing:
    print("\nAllowlisted innates with no public Valve CDN art (rendered via")
    print("elements.py innate-icon fallback path):")
    for fname in allowed_missing:
        print(f"  ok-fallback  {fname}")

if fallback_gap:
    print("\nAllowlisted slugs missing the onerror fallback in HTML:")
    for fname in fallback_gap:
        print(f"  NO-FALLBACK  {fname}")
    sys.exit(1)

if real_missing:
    print("\nMissing local icon files NOT on KNOWN_INNATE_NO_CDN_ICON allowlist:")
    print("(either restore the file under icons/abilities/, or add the slug to")
    print(" KNOWN_INNATE_NO_CDN_ICON in check_icons.py + audit_abilities.py")
    print(" after confirming it's a real innate Valve doesn't host CDN art for.)")
    for fname in real_missing:
        print(f"  MISSING  {fname}")
    sys.exit(1)

print("\nAll referenced ability icons present locally or allowlisted fallback.")
