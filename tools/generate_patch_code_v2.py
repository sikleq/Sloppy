"""
Datafeed-aware patch-scaffold generator (the canonical generator).

Reads `/datafeed/patchnotes?version=X` JSON (cached under data/) and emits
Python source built on the `patch/` helper API (`b()`, `li()`, `hero_header()`,
…) — the same calls used by `content/pXXX.py`. Preserves the full indent_level
hierarchy, facet subsections, entity titles ("New Tier 1 Artifact"), aghanims
markers, and info clarifications.

Usage:
    python tools/generate_patch_code_v2.py <version>

E.g.: python tools/generate_patch_code_v2.py 7.40

Output: `_generated_p_<version>_v2.py` in the repo root — review it, then save the
reviewed block as `content/p<version>.py` wrapped in `def build():` (builders/build_patches.py
finds it by itself; until 2026-10-27 this script lay in the repo root).

Pipeline:
1. Load datafeed JSON (data/<version>_datafeed.json) + itemlist + herolist
2. Walk each top-level section:
   - general_notes[]      → section("General Updates") + plain_header per note
   - items[]              → section("Item Updates")     + item_header per item
   - neutral_creeps[]     → section("Neutral Creep Updates") + per creep
   - neutral_items[]      → section("Neutral Item Updates") + per artifact
   - heroes[]             → section("Hero Updates") + hero_header +
                            abilities + facet subsections
   (Section order matches the official patch page: General → Items →
    Neutral Creeps → Neutral Items → Heroes.)
3. For each entity, walk notes tree:
   - indent_level == 1 → top-level li
   - indent_level == N+1 immediately after N → inline_note on parent
   - hide_dot:true row → subgroup() or <br> spacer
   - info field → inline_note attached to current row
   - aghanims field → ensure text mentions "Aghanim's Scepter"/"Aghanim's Shard"
                      so patch/elements.li() auto-tags the aghs marker
4. Apply text-heuristic tag inference (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL)
   + l=True for cost/BAT/cooldown/manacost/cast-point keywords
   + canonical-phrase tags (Added to CM=NEW, No longer applied by
     illusions=DEL, etc.) per Sloppy memory rules.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the repo root

# The code lives in tools/patchgen (split 2026-11-04). Every name stays reachable here: tests, the skill's linter and the
# scripts import from this file.
_PARTS = ('common', 'data', 'tags', 'rows', 'notes', 'lines', 'general', 'entities', 'post_stats', 'post_cards', 'post_general', 'post_items', 'normalize', 'post_late', 'post_hero', 'post_shared', 'post_level_values', 'post_facets', 'pipeline', 'facets_auto')
for _part in _PARTS:
    _module = importlib.import_module(f"tools.patchgen.{_part}")
    globals().update({k: v for k, v in vars(_module).items() if not k.startswith("__")})
del _part, _module

if __name__ == '__main__':
    from tools.patchgen.cli import main
    main()
