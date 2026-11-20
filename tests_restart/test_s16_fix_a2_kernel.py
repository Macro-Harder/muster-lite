# Copyright: J.P. Picard aka Macro-Harder.
"""Step 16 Round 2 Fix A2 cure tests: kernel.py only.

Findings: S16A21-06 with the record limb of S16A21-02 (field 7 of
the result record states one consistent standing), S16A21-04
kernel limb (checks 10 and 12 to 16 on an empty supplied set),
S16A21-05 (per check PASS citation correspondence), with the cure
test shapes of S16A22-02 (record limb), S16A22-04 and S16A22-05.
"""

from tests_restart.conftest import check, field


def _kernel():
    from muster_restart import kernel
    return kernel


def _no_derivation_input():
    return {
        "runner_identity": "fix-a2-runner",
        "runner_capacity": "Auditor",
        "build": "muster-lite",
        "stage_judged": "Step 15",
        "tier": "Low",
        "pinned_base": "base-a2",
        "supplied_files": [],
        "roster": {
            "file": "records/step-15-roster.md",
            "seats": [
                {"seat_key": "seat-1",
                 "agent_identifier": "agent-1",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location":
                     "records/step-15-roster.md line 4"},
                {"seat_key": "seat-2",
                 "agent_identifier": "agent-2",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location":
                     "records/step-15-roster.md line 5"},
                {"seat_key": "seat-3",
                 "agent_identifier": "agent-3",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location":
                     "records/step-15-roster.md line 6"},
            ],
        },
    }


def _empty_input():
    return {
        "runner_identity": "fix-a2-runner",
        "runner_capacity": "Auditor",
        "build": "muster-lite",
        "stage_judged": "Step 99",
        "tier": "Low",
        "supplied_files": [],
    }


def _staffed_input():
    return {
        "runner_identity": "fix-a2-runner",
        "runner_capacity": "Auditor",
        "build": "muster-lite",
        "stage_judged": "Step 13",
        "tier": "Low",
        "pinned_base": "base-a2",
        "supplied_files": [],
        "roster": {
            "file": "records/roster.md",
            "seats": [
                {"seat_key": "seat-1", "team": "Design team",
                 "agent_identifier": "agent-1",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location": "records/roster.md line 4"},
                {"seat_key": "seat-2", "team": "Design team",
                 "agent_identifier": "agent-2",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location": "records/roster.md line 5"},
                {"seat_key": "seat-3", "team": "Design team",
                 "agent_identifier": "agent-3",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "carried_seat_kind": "Contrarian",
                 "roster_line_location": "records/roster.md line 6"},
            ],
            "board_seats": [
                {"seat_key": "board-1", "agent_identifier": "agent-1",
                 "agent_kind": "full identifier",
                 "roster_line_location": "records/roster.md line 9"},
                {"seat_key": "board-2", "agent_identifier": "agent-2",
                 "agent_kind": "full identifier"},
                {"seat_key": "board-3", "agent_identifier": "agent-3",
                 "agent_kind": "full identifier"},
            ],
        },
        "tables": {
            "layer1": [{"tier": "Low", "team_form": "Design team",
                        "base_size": 2}],
            "layer2": [{"step": "Step 13", "unit": "Design team",
                        "unit_count": 1}],
            "mapping": [{"step": "Step 13", "unit": "Design team",
                         "team_form": "Design team"}],
        },
    }


def test_s16a21_06_field7_one_consistent_standing_no_derivation():
    result = _kernel().compute_result(_no_derivation_input())
    field7 = field(result, 7)
    assert field7["absence_words"] is not None
    assert "no team count stands for Step 15" in field7["absence_words"]
    assert field7["team_counts"] == [], (
        "field 7 stated the absence words and stood a team count "
        "in the same field: %s" % (field7["team_counts"],))


def test_s16a22_02_record_limb_stage_count_stands_team_counts_empty():
    result = _kernel().compute_result(_no_derivation_input())
    field7 = field(result, 7)
    assert field7["stage_count"]["entries_counted"] == 3
    assert field7["stage_count"]["counted_total"] == 3
    assert field7["team_counts"] == []


def test_s16a21_06_field7_team_count_stands_where_derivation_fires():
    result = _kernel().compute_result(_staffed_input())
    field7 = field(result, 7)
    assert field7["absence_words"] is None
    assert field7["team_counts"] != []
    assert field7["team_counts"][0]["counted_total"] == 3


def test_s16a22_04_empty_set_full_verdict_vector():
    result = _kernel().compute_result(_empty_input())
    expected = {
        1: "UNVERIFIABLE", 2: "UNVERIFIABLE", 3: "UNVERIFIABLE",
        4: "UNVERIFIABLE", 5: "UNVERIFIABLE", 6: "UNVERIFIABLE",
        7: "UNVERIFIABLE", 8: "UNVERIFIABLE", 9: "UNVERIFIABLE",
        10: "UNVERIFIABLE", 11: "UNVERIFIABLE", 12: "UNVERIFIABLE",
        13: "UNVERIFIABLE", 14: "NOT PROVEN", 15: "UNVERIFIABLE",
        16: "UNVERIFIABLE", 17: "UNVERIFIABLE",
    }
    for number, word in expected.items():
        entry = check(result, number)
        assert entry["verdict"] == word, (
            "check %s stood at %s on an empty supplied set, "
            "expected %s" % (number, entry["verdict"], word))
    assert field(result, 12) == "UNVERIFIABLE"


def test_s16a22_04_empty_set_no_pass_citation_names_no_seat():
    result = _kernel().compute_result(_empty_input())
    for entry in result["check_results"]:
        assert entry["verdict"] != "PASS", (
            "check %s stood at PASS on an empty supplied set"
            % entry["check"])


def test_s16a22_05_pass_citations_name_the_seat_each_check_rests_on():
    result = _kernel().compute_result(_staffed_input())
    carried = check(result, 3)
    assert carried["verdict"] == "PASS"
    assert "records/roster.md" in carried["citations"][0]
    assert "line 6" in carried["citations"][0]
    assert "seat-3" in carried["citations"][0]
    board = check(result, 4)
    assert board["verdict"] == "PASS"
    assert "records/roster.md" in board["citations"][0]
    assert "line 9" in board["citations"][0]
    assert "board-1" in board["citations"][0]
    assert carried["citations"][0] != board["citations"][0]


def test_s16a22_05_check1_citation_names_the_seat_completing_the_count():
    result = _kernel().compute_result(_staffed_input())
    entry = check(result, 1)
    assert entry["verdict"] == "PASS"
    assert "line 5" in entry["citations"][0]
    assert "seat-2" in entry["citations"][0]
