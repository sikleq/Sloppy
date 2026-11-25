"""Silent Changes sees an ability's health cost (7.42a Bloodslinger Sling Grenade 75 -> 100 was missing)."""
from builders import silent


def test_health_cost_is_a_gameplay_field():
    assert "AbilityHealthCost" in silent.INTERESTING_FIELDS
