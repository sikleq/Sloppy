"""Regression tests for the normalized per-patch JSON artifacts written by
generate_patch_code_v2.py.

The flagship guarantee: no committed normalized JSON may contain an entity
with an empty `changes` list. Previously this surfaced for heroes whose
only changes lived inside facet subsections' general_notes — _normalize_hero
read the facet's per-ability ability_notes but skipped its general_notes,
so 5 heroes across 7.39 and 7.39b ended up with `changes: []`.

If a future patch legitimately needs a zero-changes entity (e.g. a header-
only placeholder), add it to ALLOW_ZERO_CHANGES below WITH a comment
explaining why; do not just delete the test.
"""
import json
from pathlib import Path

import pytest

NORMALIZED_DIR = Path(__file__).resolve().parents[1] / "data" / "normalized" / "patches"

# Format: {(patch_version, entity_id)}. Empty by design; populate only when
# a genuinely zero-changes entity needs to ship.
ALLOW_ZERO_CHANGES: set[tuple[str, str]] = set()


def _patch_files():
    return sorted(NORMALIZED_DIR.glob("*.json"))


@pytest.mark.parametrize("path", _patch_files(), ids=lambda p: p.stem)
def test_no_empty_entities(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("patch") or path.stem
    offenders = [
        e for e in data.get("entities", [])
        if not e.get("changes")
        and (version, e.get("id")) not in ALLOW_ZERO_CHANGES
    ]
    assert not offenders, (
        f"{path.name}: {len(offenders)} entit(y/ies) with empty changes — "
        f"if this is intentional, allowlist via ALLOW_ZERO_CHANGES with a "
        f"comment. First offenders: "
        f"{[(e.get('entity_type'), e.get('name')) for e in offenders[:5]]}"
    )


@pytest.mark.parametrize("path", _patch_files(), ids=lambda p: p.stem)
def test_basic_shape(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path.name}: top-level must be dict"
    assert "entities" in data, f"{path.name}: missing 'entities' key"
    for e in data["entities"]:
        assert "entity_type" in e
        assert "name" in e
        assert "changes" in e
        assert isinstance(e["changes"], list)
