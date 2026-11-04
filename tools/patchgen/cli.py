"""The command line: python tools/generate_patch_code_v2.py <version>."""
import json
import os
import sys

from .common import _HERE
from .facets_auto import _auto_register_facets
from .normalize import fetch_datafeed, normalize
from .pipeline import generate


def main():
    if len(sys.argv) != 2:
        print('Usage: python tools/generate_patch_code_v2.py <version>', file=sys.stderr)
        sys.exit(1)
    version = sys.argv[1]
    d = fetch_datafeed(version)

    # 0. Auto-register any new facet slugs into patch/badges.py
    _auto_register_facets(version, d)

    # 1. W()-scaffold (existing primary output).
    src = generate(version)
    out_path = os.path.join(_HERE, f'_generated_p_{version}_v2.py')
    open(out_path, 'w', encoding='utf-8').write(src)
    print(f'Wrote {out_path} ({len(src):,} chars, {src.count(chr(10)):,} lines)')

    # 2. Normalized JSON (parallel data-as-source-of-truth artifact).
    norm = normalize(version, d)
    json_dir = os.path.join(_HERE, 'data', 'normalized', 'patches')
    os.makedirs(json_dir, exist_ok=True)
    json_path = os.path.join(json_dir, f'{version}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(norm, f, ensure_ascii=False, indent=2)
    n_changes = sum(len(e['changes']) for e in norm['entities'])
    print(f'Wrote {json_path} ({len(norm["entities"])} entities, {n_changes} changes)')

    # 3. Auto-validate the JSON we just wrote (no separate command needed).
    try:
        from tools.validate_data import validate_patch, _report
        print('\n--- validating normalized data ---')
        _report(version, validate_patch(version))
    except Exception as e:
        print(f'[WARN] validation skipped: {e}', file=sys.stderr)
