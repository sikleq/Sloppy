"""Validate a normalized patch JSON (data/normalized/patches/<ver>.json).

Catches interpretation errors BEFORE they reach the generated page — the main
recurring pain of the project (wrong buff/nerf direction, unparsed numbers,
stale facet slugs). Reads the JSON artifact emitted by generate_patch_code_v2.py
and reports issues by severity.

Usage:
    python tools/validate_data.py 7.41
    python tools/validate_data.py                # validates all patches found

Exit code is non-zero if any HIGH/CRITICAL issue is found (CI-friendly).

Severity:
  HIGH    — likely wrong: word/value direction contradiction
  MEDIUM  — structural: unknown facet slug, empty entity, duplicate id
  LOW     — worth a glance: numeric change not captured as old/new
  INFO    — summary only
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)

# Reuse the generator's regexes/reference data so checks stay in lock-step
# with what the normalizer actually produced.
from generate_patch_code_v2 import _FROM_TO_RE, CANONICAL_TAGS  # noqa: E402

try:
    from patch.badges import FACETS  # facet slug -> (display, icon)
    _FACET_SLUGS = set(FACETS.keys())
except Exception:
    _FACET_SLUGS = set()

NORM_DIR = os.path.join(_HERE, 'data', 'normalized', 'patches')

_INCREASED_RE = re.compile(r'\b(increased|raised|improved)\b', re.I)
_DECREASED_RE = re.compile(r'\b(decreased|reduced|lowered|worsened)\b', re.I)


def _canonical_tag(text):
    """Return the canonical-phrase tag for text, or None. Mirrors the first
    pass of _resolve_tag — used to know when a non-buff/nerf tag is expected."""
    for rx, tag in CANONICAL_TAGS:
        if rx.search(text):
            return tag.lower()
    return None


def _check_change(entity, change, issues):
    text = change.get('text', '')
    tag = change.get('tag', '')
    has_old = 'old' in change
    lower = change.get('lower_is_better', False)
    canon = _canonical_tag(text)
    where = f"{entity['name']} / {change.get('scope', '?')}"

    # HIGH — word/value direction contradiction (only when not explained by
    # lower_is_better or a canonical rework/del/new override).
    if canon is None:
        if _INCREASED_RE.search(text) and tag == 'nerf' and not lower:
            issues.append(('HIGH', where,
                           f'"increased" wording but tagged NERF (no lower_is_better): {text}'))
        if _DECREASED_RE.search(text) and tag == 'buff' and not lower:
            issues.append(('HIGH', where,
                           f'"decreased" wording but tagged BUFF (no lower_is_better): {text}'))

    # MEDIUM — buff/nerf with equal old==new (direction is meaningless).
    if has_old and tag in ('buff', 'nerf'):
        if change['old'] == change['new']:
            issues.append(('MEDIUM', where,
                           f'old == new but tagged {tag.upper()}: {text}'))

    # LOW — text has a "from X to Y" but no old/new captured (parse miss or
    # en-dash range). Worth a human glance; not necessarily wrong.
    if not has_old and _FROM_TO_RE.search(text):
        issues.append(('LOW', where,
                       f'numeric change not captured as old/new: {text}'))


def validate_patch(version):
    path = os.path.join(NORM_DIR, f'{version}.json')
    if not os.path.exists(path):
        print(f'  ! not found: {path}')
        return [('HIGH', version, 'normalized JSON missing — run generate_patch_code_v2.py')]

    d = json.load(open(path, encoding='utf-8'))
    issues = []
    seen_ids = {}
    n_changes = 0

    for ent in d.get('entities', []):
        eid = ent.get('id')
        name = ent.get('name', '?')
        changes = ent.get('changes', [])
        n_changes += len(changes)

        # MEDIUM — duplicate non-null entity id.
        if eid:
            if eid in seen_ids:
                issues.append(('MEDIUM', name, f'duplicate entity id "{eid}" (also {seen_ids[eid]})'))
            else:
                seen_ids[eid] = name

        # MEDIUM — entity with no changes (empty section / parse gap).
        if not changes:
            issues.append(('MEDIUM', name, f'entity "{eid}" has zero changes'))

        for ch in changes:
            # MEDIUM — facet scope referencing an unknown slug.
            scope = ch.get('scope', '')
            if scope.startswith('facet:'):
                fslug = scope.split(':', 1)[1]
                if _FACET_SLUGS and fslug not in _FACET_SLUGS:
                    issues.append(('MEDIUM', name, f'unknown facet slug "{fslug}"'))
            _check_change(ent, ch, issues)

    return issues, len(d.get('entities', [])), n_changes


_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}


def _report(version, result):
    if isinstance(result, list):  # missing-file shortcut
        issues, n_ent, n_chg = result, 0, 0
    else:
        issues, n_ent, n_chg = result

    from collections import Counter
    counts = Counter(sev for sev, _, _ in issues)
    print(f'\n=== {version} — {n_ent} entities, {n_chg} changes ===')
    print('  ' + ', '.join(f'{sev}: {counts.get(sev, 0)}'
                            for sev in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')))

    for sev, where, msg in sorted(issues, key=lambda x: _ORDER.get(x[0], 9)):
        print(f'  [{sev}] {where}: {msg}')

    return counts.get('CRITICAL', 0) + counts.get('HIGH', 0)


def main(argv):
    if argv:
        versions = argv
    else:
        if not os.path.isdir(NORM_DIR):
            print(f'No normalized patches dir: {NORM_DIR}')
            return 1
        versions = sorted(f[:-5] for f in os.listdir(NORM_DIR) if f.endswith('.json'))
        if not versions:
            print('No normalized patch JSON files found.')
            return 1

    blocking = 0
    for v in versions:
        blocking += _report(v, validate_patch(v))

    print(f'\n{"FAIL" if blocking else "OK"} — {blocking} HIGH/CRITICAL issue(s)')
    return 1 if blocking else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
