"""patch/aghs_granted.scan reads the Aghanim flags of every hero file of every patch, once per process. It walked each
block character by character and copied the rest of the file for each name: ~4 s of the suite, paid by whichever test
called kind_of first (audit 2026-11-02)."""
import time

from patch import aghs_granted as ag

ABILITY = '"AbilityBehavior" "DOTA_ABILITY_BEHAVIOR_PASSIVE"'


def test_scan_reads_the_flags_of_a_granted_ability_and_of_a_hidden_one():
    text = f'''"DOTAAbilities"
{{
    "axe_shard"
    {{
        {ABILITY}
        "IsGrantedByShard" "1"
        "AbilityValues"
        {{
            "damage"
            {{
                "value" "1"
            }}
        }}
    }}
    "axe_hidden"
    {{
        "AbilityBehavior" "DOTA_ABILITY_BEHAVIOR_HIDDEN"
        "MaxLevel" "1"
    }}
    "axe_innate"
    {{
        "AbilityBehavior" "DOTA_ABILITY_BEHAVIOR_HIDDEN"
        "MaxLevel" "1"
        "Innate" "1"
    }}
    "axe_scepter"

    {{
        {ABILITY}  // "IsGrantedByShard" "1" in a comment
        "IsGrantedByScepter" "1"
    }}
}}
'''
    assert ag.scan(text) == ({"axe_shard": "shard", "axe_scepter": "scepter"}, {"axe_hidden"})


def test_scan_takes_a_block_only_after_a_name_alone_on_its_line():
    assert ag.scan(f'"on_the_same_line" {{\n{ABILITY}\n"IsGrantedByShard" "1"\n}}\n') == ({}, set())
    assert ag.scan(f'"no_block"\n"real"\n{{\n{ABILITY}\n"IsGrantedByShard" "1"\n}}\n') == ({"real": "shard"}, set())


def test_scan_of_a_block_that_never_closes_reads_to_the_end():
    assert ag.scan(f'"cut"\n{{\n{ABILITY}\n"IsGrantedByScepter" "1"\n') == ({"cut": "scepter"}, set())


def test_scan_does_not_copy_the_rest_of_the_file_for_every_name():
    block = f'"a_block"\n{{\n{ABILITY}\n"Padding" "{"x" * 20}"\n}}\n'
    text = block * 40000
    start = time.perf_counter()
    assert ag.scan(text) == ({}, set())
    assert time.perf_counter() - start < 3             # the quadratic scan took over 30 s on this text


def _one_patch(tmp_path, monkeypatch):
    """A repo of one patch with one hero file, and scan calls counted."""
    heroes = tmp_path / "data" / "stats" / "9.99" / "heroes"
    heroes.mkdir(parents=True)
    (heroes / "npc_dota_hero_axe.txt").write_text(f'"axe_shard"\n{{\n{ABILITY}\n"IsGrantedByShard" "1"\n}}\n',
                                                  encoding="utf-8")
    (tmp_path / "data" / "stats" / "9.99" / "heroes.json").write_text('{"axe": {"Ability1": "axe_shard"}}',
                                                                      encoding="utf-8")
    monkeypatch.setattr(ag, "_HERE", str(tmp_path))
    monkeypatch.setattr(ag, "OLD_PATH", str(tmp_path / "none.json"))
    for name, empty in (("_OLD", None), ("_DATA", {}), ("_ANY", {}), ("_PRESENT", {})):
        monkeypatch.setattr(ag, name, empty)
    calls = []
    real = ag.scan
    monkeypatch.setattr(ag, "scan", lambda text: calls.append(1) or real(text))
    return calls


def test_a_second_call_does_not_scan_again_and_gives_the_same_answer(tmp_path, monkeypatch):
    calls = _one_patch(tmp_path, monkeypatch)
    assert ag.kind_of("axe_shard") == "shard"
    assert len(calls) == 1
    assert ag.kind_of("axe_shard") == "shard"
    assert ag.kind_of("axe_shard", "9.99") == "shard"
    assert ag.kind_of("axe_other", "9.99") == ""
    assert len(calls) == 1
