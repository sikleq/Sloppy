"""Local mirror of the CI 'ability slugs registered in known_exceptions' audit.

Every ability(slug="X") in content/*.py must resolve to either abilities_slim.json
(the datafeed-derived slug set) or an entry in patch/known_exceptions.py. This ran
only in CI before, so a bad slug (e.g. a generator-invented one) passed locally and
failed the build. Running it as a test catches it before push.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from patch.known_exceptions import (  # noqa: E402
    KNOWN_NON_DATAFEED_ABILITIES,
    KNOWN_ICON_URL_PSEUDO_SLUGS,
    KNOWN_SYNTHETIC_SUBBLOCKS,
)

_SLUG_RE = re.compile(r'ability\([^)]*slug\s*=\s*"([^"]+)"')


def _exempt_slugs():
    return (
        {s for _, s in KNOWN_NON_DATAFEED_ABILITIES}
        | KNOWN_ICON_URL_PSEUDO_SLUGS
        | KNOWN_SYNTHETIC_SUBBLOCKS
    )


def test_all_ability_slugs_registered():
    slim = set(json.load(open(os.path.join(ROOT, "data", "abilities_slim.json"),
                               encoding="utf-8")).keys())
    exempt = _exempt_slugs()
    content_dir = os.path.join(ROOT, "content")
    issues = []
    for fn in sorted(os.listdir(content_dir)):
        if not fn.endswith(".py"):
            continue
        text = open(os.path.join(content_dir, fn), encoding="utf-8").read()
        for m in _SLUG_RE.finditer(text):
            slug = m.group(1)
            if slug not in slim and slug not in exempt:
                issues.append(f'{fn}: slug "{slug}" not in abilities_slim.json '
                              f'and not in KNOWN_NON_DATAFEED_ABILITIES')
    assert not issues, (
        "Unregistered ability slug(s) — add (HeroName, slug) to "
        "KNOWN_NON_DATAFEED_ABILITIES in patch/known_exceptions.py, or fix the "
        "slug to a real datafeed name:\n  " + "\n  ".join(issues)
    )
