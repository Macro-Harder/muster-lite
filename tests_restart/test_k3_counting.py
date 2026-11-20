"""Slice 3 groups K3-T1 to K3-T5: the counting core.

Loci: plan sections 4 (slice 3) and 6; brief sections 5.4 shapes 9
and 10, 5.4.1 and 5.3; brief section 5.8.1 for families F1, F2, F3
and F5. Every test states its concrete wrong output in the form
charged for its group. The restart product does not exist, so each
test fails on the import of muster_restart.kernel inside
conftest.require_kernel and on no other ground.
"""

import json
from pathlib import Path

from tests_restart.conftest import check, field, result_text, run_case

FIXTURES = Path(__file__).parent / "fixtures"
STAFFED = "F1/k3_staffed_roster.json"
PROPERTY = "F5/k3_property_totals.json"
WHOLE_FLOW = "F3/k3_whole_flow.json"

# K3-T1 wrong output, named constant form: a count printed without
# its subtraction, and a PASS printed without slack beside it.
WRONG_OUTPUT_K3_T1 = "Design team counted total: 3. PASS."

# K3-T3 wrong output, named constant form: the union across two short
# rounds printed as a team size instead of as holders.
WRONG_OUTPUT_K3_T3 = "team size 3, pooled across Round 1 and Round 2"

# K3-T5 wrong output, named constant form: one whole flow total
# selected from 39 and 38, and a build union figure printed where
# the state and its reason must stand.
WRONG_OUTPUT_K3_T5 = "whole flow total: 39. Build union: 12 distinct agents."


def test_k3t1_every_team_count_prints_its_subtraction():
    result, expected = run_case(STAFFED, "staffed")
    for entry in field(result, 7)["team_counts"]:
        assert entry["entries_counted"] - entry["duplicates_removed"] \
            - entry["exempt_or_uncounted_removed"] == entry["counted_total"]
    assert field(result, 7)["team_counts"] == expected["team_counts"]
    assert WRONG_OUTPUT_K3_T1 not in result_text(result)


def test_k3t1_slack_printed_beside_every_pass():
    result, expected = run_case(STAFFED, "staffed")
    entry = check(result, 1)
    assert entry["verdict"] == "PASS"
    for team in field(result, 7)["team_counts"]:
        assert team["slack"] == team["counted_total"] - team["required_count"]
    assert WRONG_OUTPUT_K3_T1 not in result_text(result)


def test_k3t1_stage_count_prints_its_subtraction():
    result, expected = run_case(STAFFED, "staffed")
    stage = field(result, 7)["stage_count"]
    assert stage == expected["stage_count"]
    assert WRONG_OUTPUT_K3_T1 not in result_text(result)


def test_k3t2_balancing_equation_team_level():
    result, expected = run_case(STAFFED, "duplicate_and_exempt")
    for entry in field(result, 7)["team_counts"]:
        assert entry["entries_counted"] == entry["duplicates_removed"] \
            + entry["exempt_or_uncounted_removed"] + entry["counted_total"], (
            "WRONG OUTPUT K3-T2: entries counted not equal to duplicates "
            "removed plus exempt or uncounted seats removed plus counted total")


def test_k3t2_balancing_equation_stage_level():
    result, expected = run_case(STAFFED, "duplicate_and_exempt")
    stage = field(result, 7)["stage_count"]
    assert stage["entries_counted"] == stage["duplicates_removed"] \
        + stage["exempt_or_uncounted_removed"] + stage["counted_total"], (
        "WRONG OUTPUT K3-T2: stage entries counted not equal to duplicates "
        "removed plus exempt or uncounted seats removed plus counted total, "
        "with the holders figure counted in the equation")


def test_k3t2_one_seat_removed_as_both_duplicate_and_exempt_fails():
    result, expected = run_case("F2/k3_double_removal.json", "double_removal")
    for entry in field(result, 7)["team_counts"]:
        assert entry["entries_counted"] == entry["duplicates_removed"] \
            + entry["exempt_or_uncounted_removed"] + entry["counted_total"], (
            "WRONG OUTPUT K3-T2: one seat removed as both a duplicate and "
            "an exempt or uncounted seat")


def test_k3t3_both_short_rounds_named():
    result, expected = run_case(STAFFED, "two_short_rounds")
    entry = check(result, 1)
    assert entry["evidence"]["rounds_below_required"] == expected["rounds_below"]
    assert WRONG_OUTPUT_K3_T3 not in result_text(result)


def test_k3t3_union_reported_as_holders_never_as_team_size():
    result, expected = run_case(STAFFED, "two_short_rounds")
    stage = field(result, 7)["stage_count"]
    assert stage["holders_figure"] == expected["holders_figure"]
    assert stage["holders_counting_kind"] == "rollup"
    assert WRONG_OUTPUT_K3_T3 not in result_text(result)


def test_k3t3_holders_figure_stands_in_stagecount_home():
    result, expected = run_case(STAFFED, "two_short_rounds")
    assert "holders_figure" in field(result, 7)["stage_count"]
    for team in field(result, 7)["team_counts"]:
        assert "holders_figure" not in team
    assert WRONG_OUTPUT_K3_T3 not in result_text(result)


def test_k3t4_pool_family_total_after_duplicates_and_exempt_steps():
    result, expected = run_case(PROPERTY, "property_totals")
    team = field(result, 7)["team_counts"][0]
    prop = team["property_conditioned_totals"]["pool family"]
    assert prop == expected["pool_family"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k3t4_wrong.json").read_text(encoding="utf-8"))
    assert prop["property_conditioned_counted_total"] != wrong["pool_family_before_steps"]


def test_k3t4_perspective_total_uses_duplicate_value_group_rule():
    result, expected = run_case(PROPERTY, "property_totals")
    team = field(result, 7)["team_counts"][0]
    prop = team["property_conditioned_totals"]["perspective"]
    assert prop == expected["perspective"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k3t4_wrong.json").read_text(encoding="utf-8"))
    assert prop["property_conditioned_counted_total"] != wrong["pool_family_before_steps"]


def test_k3t4_qualification_total_after_duplicates_and_exempt_steps():
    result, expected = run_case(PROPERTY, "property_totals")
    team = field(result, 7)["team_counts"][0]
    prop = team["property_conditioned_totals"]["qualification"]
    assert prop == expected["qualification"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k3t4_wrong.json").read_text(encoding="utf-8"))
    assert prop != wrong


def test_k3t5_both_whole_flow_totals_printed_neither_selected():
    result, expected = run_case(WHOLE_FLOW, "whole_flow_claim")
    position = field(result, 13)["whole_flow_total"]
    assert position == expected["whole_flow_total"]
    assert WRONG_OUTPUT_K3_T5 not in result_text(result)


def test_k3t5_build_union_state_with_reason_and_no_figure():
    result, expected = run_case(WHOLE_FLOW, "whole_flow_claim")
    union = field(result, 7)["build_union"]
    assert union == expected["build_union"]
    assert "figure" not in union
    assert WRONG_OUTPUT_K3_T5 not in result_text(result)
