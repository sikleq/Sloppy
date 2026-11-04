"""Where the repo is, and what every part of the generator needs from it."""
import os
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the repo root
sys.path.insert(0, _HERE)
try:
    from patch.images import ITEM_SLUG as _KNOWN_ITEM_SLUGS
except Exception as _e:
    print(f'[WARN] patch.images.ITEM_SLUG unavailable: {_e}', file=sys.stderr)
    _KNOWN_ITEM_SLUGS = {}
