"""The Neutral Abilities table's rows of the creeps 7.42 added say what each ability does (owner 2026-11-20: "А в
Neutral abilities вкладке обновил?" — Odobenus Blight's row was dashes only)."""
from builders.creeps_abilities import ABIL_MANUAL


def test_the_new_creeps_abilities_have_their_property():
    for slug in ("odobenus_blight", "mud_golem_hurl_big_boulder", "eimermole_miners_slam", "ogre_seal_flop",
                 "radigull_eggstremism"):
        assert ABIL_MANUAL.get(slug, {}).get("effect"), slug
    assert ABIL_MANUAL["odobenus_blight"]["effect"].endswith("2/3/4/5")   # its four levels, as the KV has them
