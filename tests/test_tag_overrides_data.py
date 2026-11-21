"""The tag overrides live in data/rules/tag_overrides.json (Fable review 2026-11-21: decisions are data, the code was 796
lines): an ordered list, the first substring found wins, each entry a text and a canonical tag."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAGS = {"BUFF", "NERF", "NEW", "DEL", "REWORK", "MISC", "QoL", "SWAP"}


def test_the_overrides_file_is_the_generators():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from patchgen.tags import TAG_OVERRIDES, _guess_tag
    data = json.loads((ROOT / "data" / "rules" / "tag_overrides.json").read_text(encoding="utf-8"))["overrides"]
    assert [(e["text"], e["tag"]) for e in data] == list(TAG_OVERRIDES.items())
    assert all(e["tag"] in TAGS and e["text"] == e["text"].lower() for e in data)
    assert len({e["text"] for e in data}) == len(data)                     # no entry twice
    # order matters: "instead of removed" (MISC) before "instead of" (REWORK)
    keys = [e["text"] for e in data]
    assert keys.index("instead of removed") < keys.index("instead of")
    assert _guess_tag("Now applies to Shrines of Wisdom instead of removed Wisdom Runes") == "MISC"
    assert _guess_tag("Now requires Blade of Alacrity instead of Band of Elvenskin") == "REWORK"
