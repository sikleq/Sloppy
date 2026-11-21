"""Hero Lab's innate formulas read the patch's numbers from the history entry, not from the effect's KV-key fields.
Sonnet check 2026-11-21: Tinker Eureka! showed 30 / 59 / 99.9% item cooldown reduction at levels 1 / 10 / 30 — the
whole Intelligence, uncapped — instead of 1% per 3 Intelligence, at most 60% (10 / 19 / 46%)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_attr_floor_capped_reads_the_entry():
    js = (ROOT / "src" / "js" / "hero-lab.js").read_text(encoding="utf-8")
    assert ("Math.floor(a[eff.source] / (entry.divisor || eff.divisor || 1)), entry.cap || eff.cap || 100)"
            in js)


def test_tinkers_numbers_are_in_the_history():
    rules = json.loads((ROOT / "data" / "rules" / "hero_stat_innates.json").read_text(encoding="utf-8"))
    rules = rules.get("heroes", rules)
    eff = rules["tinker"]["effects"][0]
    assert eff["formula"] == "attr_floor_capped" and "divisor" not in eff and "cap" not in eff
    last = eff["history"][-1]
    assert (last["divisor"], last["cap"]) == (3, 60)
    # Int 59 at level 10 -> 19%, Int 139 at level 30 -> 46%
    assert min(59 // last["divisor"], last["cap"]) == 19 and min(139 // last["divisor"], last["cap"]) == 46
