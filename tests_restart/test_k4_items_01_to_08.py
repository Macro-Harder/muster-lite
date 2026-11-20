"""Slice 4 groups K4-T1 to K4-T8: check items 1 to 8.

Loci: plan sections 4 (slice 4) and 6; brief section 5.5 items 1 to
8, brief section 5.3 for the item 1 derivation, brief section 5.4
shape 4A for item 6, and brief section 5.8.1 for families F1, F2 and
F5, including the kind closure fixture matrix columns for items 4,
6 and 8. Every test states its concrete wrong output in the form
charged for its group. The restart product does not exist, so each
test fails on the import of muster_restart.kernel inside
conftest.require_kernel and on no other ground.
"""

import json
from pathlib import Path

from tests_restart.conftest import check, checks, field, result_text, run_case

FIXTURES = Path(__file__).parent / "fixtures"
DERIVATION = "F5/k4_item1_derivation.json"
ITEMS = "F1/k4_items.json"

# K4-T2 wrong output, named constant form: the mixed evidence state
# decided by two rules instead of the item single decision rule.
WRONG_OUTPUT_K4_T2 = "mixed evidence state: FAIL under one rule and NOT PROVEN under another, two words for one state"

# K4-T3 wrong output, named constant form: a carried seat dropped
# from its position, or a carried seat holder counted in a step total.
WRONG_OUTPUT_K4_T3 = "build Fold in Tracer holding counted in the Step 13 step total"

# K4-T4 wrong output, named constant form: the review board holders
# figure printed as a team size.
WRONG_OUTPUT_K4_T4 = "review board: team size 3"

# K4-T6 wrong output, named constant form: a verdict word printed
# for item 6 where the shape 4A stage or single coordinator
# premise fails.
WRONG_OUTPUT_K4_T6 = "check 6 verdict PASS where the step record states two differing coordinator identities"

# K4-T7 wrong output, named constant form: a combined scope claimed
# in report text with no holder in the roster.
WRONG_OUTPUT_K4_T7 = "combined scope Design combining claimed in report text, no holder in the roster, returned as proven"

# K4-T8 wrong output, named constant form: an unrecorded selection
# returned as proven for the affected seats.
WRONG_OUTPUT_K4_T8 = "selection unrecorded, affected seats returned as proven"


def test_k4t1_no_mapping_row_case():
    result, expected = run_case(DERIVATION, "no_mapping_row")
    entry = check(result, 1)
    assert entry["verdict"] == expected["verdict"]
    assert entry["missing_fact"] == expected["missing_fact"]
    assert field(result, 7)["absence_words"] == expected["absence_words"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert entry["verdict"] != wrong["no_mapping_row_verdict"]


def test_k4t1_no_layer1_row_case():
    result, expected = run_case(DERIVATION, "no_layer1_row")
    entry = check(result, 1)
    assert entry["verdict"] == expected["verdict"]
    assert entry["missing_fact"] == expected["missing_fact"]
    assert field(result, 7)["team_counts"] == expected["team_counts"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert entry["verdict"] != wrong["no_mapping_row_verdict"]


def test_k4t1_differing_exception_rows_case():
    result, expected = run_case(DERIVATION, "differing_exception_rows")
    entry = check(result, 1)
    assert entry["verdict"] == expected["verdict"]
    assert entry["missing_fact"] == expected["missing_fact"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert entry["verdict"] != wrong["no_mapping_row_verdict"]


def test_k4t1_plaid_position_no_item1_word_on_missing_layer1():
    result, expected = run_case(DERIVATION, "plaid_position")
    assert checks(result, 1) == expected["item1_results"]
    assert field(result, 7)["absence_words"] == expected["absence_words"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert [entry["verdict"] for entry in checks(result, 1)] != [wrong["no_mapping_row_verdict"]]


def test_k4t1_count_limb_below_figure_fail():
    result, expected = run_case(DERIVATION, "count_limb_below")
    entry = check(result, 1)
    assert entry["verdict"] == "FAIL"
    assert entry["evidence"]["counted_set_number"] == expected["counted"]
    assert entry["evidence"]["figure"] == expected["figure"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert entry["verdict"] != wrong["no_mapping_row_verdict"]


def test_k4t1_count_limb_unproven_not_proven():
    result, expected = run_case(DERIVATION, "count_limb_unproven")
    entry = check(result, 1)
    assert entry["verdict"] == "NOT PROVEN"
    assert entry["missing_fact"] == expected["missing_fact"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert entry["verdict"] != wrong["no_mapping_row_verdict"]


def test_k4t1_field7_silence_whole_stage_form():
    result, expected = run_case(DERIVATION, "field7_whole_stage_absence")
    counts = field(result, 7)
    assert counts["team_counts"] == []
    assert counts["absence_words"] == expected["absence_words"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert [entry["verdict"] for entry in checks(result, 1)] != [wrong["no_mapping_row_verdict"]]


def test_k4t1_required_team_at_zero_observed_fail():
    result, expected = run_case(DERIVATION, "required_team_absent")
    entry = check(result, 1)
    assert entry["verdict"] == "FAIL"
    assert entry["evidence"]["observed_count"] == 0
    assert entry["evidence"]["required_count"] == expected["required_count"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t1_wrong.json").read_text(encoding="utf-8"))
    assert entry["verdict"] != wrong["no_mapping_row_verdict"]


def test_k4t2_mixed_state_favourable_reading_reaches_minimum():
    result, expected = run_case("F2/k4_mixed_evidence.json", "mixed_reaches")
    entry = check(result, 2)
    assert entry["verdict"] == "NOT PROVEN"
    assert WRONG_OUTPUT_K4_T2 not in result_text(result)


def test_k4t2_mixed_state_favourable_reading_still_below_minimum():
    result, expected = run_case("F2/k4_mixed_evidence.json", "mixed_below")
    entry = check(result, 2)
    assert entry["verdict"] == "FAIL"
    assert WRONG_OUTPUT_K4_T2 not in result_text(result)


def test_k4t2_duplicate_holding_on_full_identifiers_fail():
    result, expected = run_case("F2/k4_mixed_evidence.json", "duplicate_holding")
    entry = check(result, 2)
    assert entry["verdict"] == "FAIL"
    repairs = field(result, 11)["duplicate_holdings"]
    assert repairs == expected["duplicate_holdings"]
    assert WRONG_OUTPUT_K4_T2 not in result_text(result)


def test_k4t3_carried_seats_stand_in_their_positions():
    result, expected = run_case(ITEMS, "carried_seats_present")
    entry = check(result, 3)
    assert entry["verdict"] == "PASS"
    assert WRONG_OUTPUT_K4_T3 not in result_text(result)


def test_k4t3_build_fold_in_tracer_over_base_in_no_step_total():
    result, expected = run_case(ITEMS, "carried_seats_present")
    stage = field(result, 7)["stage_count"]
    assert stage["counted_total"] == expected["stage_counted_total"]
    assert WRONG_OUTPUT_K4_T3 not in result_text(result)


def test_k4t3_carried_seat_proven_absent_fail():
    result, expected = run_case(ITEMS, "carried_seat_absent")
    entry = check(result, 3)
    assert entry["verdict"] == "FAIL"
    assert WRONG_OUTPUT_K4_T3 not in result_text(result)


def test_k4t3_carried_seat_unproven_not_proven():
    result, expected = run_case(ITEMS, "carried_seat_unproven")
    entry = check(result, 3)
    assert entry["verdict"] == "NOT PROVEN"
    assert entry["missing_fact"] == expected["missing_fact"]
    assert WRONG_OUTPUT_K4_T3 not in result_text(result)


def test_k4t4_board_holders_count_not_a_team_size():
    result, expected = run_case("F5/k4_kind_closure_item4.json", "board_three_holders")
    entry = check(result, 4)
    assert entry["verdict"] == "PASS"
    assert entry["evidence"]["holders_count"] == expected["holders_count"]
    assert entry["evidence"]["counting_kind"] == "rollup"
    assert WRONG_OUTPUT_K4_T4 not in result_text(result)


def test_k4t4_board_favourable_reading_below_three_fail():
    result, expected = run_case("F5/k4_kind_closure_item4.json", "board_below_three")
    entry = check(result, 4)
    assert entry["verdict"] == "FAIL"
    assert WRONG_OUTPUT_K4_T4 not in result_text(result)


def test_k4t4_board_non_full_values_could_reach_three_not_proven():
    result, expected = run_case("F5/k4_kind_closure_item4.json", "board_could_reach")
    entry = check(result, 4)
    assert entry["verdict"] == "NOT PROVEN"
    assert entry["missing_fact"] == expected["missing_fact"]
    assert WRONG_OUTPUT_K4_T4 not in result_text(result)


def test_k4t5_check_composes_where_property_total_differs():
    result, expected = run_case("F5/k4_item5_composition.json", "composes")
    entry = check(result, 5)
    assert entry["composing"] is True
    assert entry["evidence"]["counted_total"] == expected["counted_total"]
    assert entry["evidence"]["property_conditioned_counted_total"] == \
        expected["property_conditioned_counted_total"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t5_wrong.json").read_text(encoding="utf-8"))
    assert entry["composing"] != wrong["composes_case_beside_rollup"]


def test_k4t5_check_beside_rollup_where_all_totals_equal():
    result, expected = run_case("F5/k4_item5_composition.json", "beside_rollup")
    entry = check(result, 5)
    assert entry["composing"] is False
    bounds = field(result, 13)
    assert bounds["check5_beside_rollup"] == expected["beside_entry"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t5_wrong.json").read_text(encoding="utf-8"))
    assert entry["composing"] != (not wrong["composes_case_beside_rollup"])


def test_k4t5_reverse_pair_beside_case_does_not_compose():
    result, expected = run_case("F5/k4_item5_composition.json", "beside_rollup")
    assert field(result, 12) == expected["rollup"]
    wrong = json.loads(
        (FIXTURES / "F5" / "k4t5_wrong.json").read_text(encoding="utf-8"))
    assert check(result, 5)["composing"] != (not wrong["composes_case_beside_rollup"])


def test_k4t6_coordinator_counted_as_member_fail():
    result, expected = run_case("F5/k4_item6_shape4a.json", "coordinator_counted_as_member")
    entry = check(result, 6)
    assert entry["verdict"] == "FAIL"
    assert WRONG_OUTPUT_K4_T6 not in result_text(result)


def test_k4t6_two_differing_coordinator_statements_not_proven():
    result, expected = run_case("F5/k4_item6_shape4a.json", "two_coordinators")
    entry = check(result, 6)
    assert entry["verdict"] == "NOT PROVEN"
    assert entry["missing_fact"] == expected["missing_fact"]
    assert WRONG_OUTPUT_K4_T6 not in result_text(result)


def test_k4t6_no_coordinator_stated_not_proven():
    result, expected = run_case("F5/k4_item6_shape4a.json", "no_coordinator")
    entry = check(result, 6)
    assert entry["verdict"] == "NOT PROVEN"
    assert WRONG_OUTPUT_K4_T6 not in result_text(result)


def test_k4t6_non_full_coordinator_kind_not_proven():
    result, expected = run_case("F5/k4_item6_shape4a.json", "coordinator_placeholder")
    entry = check(result, 6)
    assert entry["verdict"] == "NOT PROVEN"
    assert entry["missing_fact"] == expected["missing_fact"]
    assert WRONG_OUTPUT_K4_T6 not in result_text(result)


def test_k4t6_stage_stated_is_not_stage_judged_not_proven():
    result, expected = run_case("F5/k4_item6_shape4a.json", "wrong_stage")
    entry = check(result, 6)
    assert entry["verdict"] == "NOT PROVEN"
    assert entry["missing_fact"] == expected["missing_fact"]
    assert WRONG_OUTPUT_K4_T6 not in result_text(result)


def test_k4t7_combined_scope_with_holder_and_base_met_pass():
    result, expected = run_case(ITEMS, "combined_scope_held")
    entry = check(result, 7)
    assert entry["verdict"] == "PASS"
    assert WRONG_OUTPUT_K4_T7 not in result_text(result)


def test_k4t7_combined_scope_claimed_with_no_holder_fail():
    result, expected = run_case(ITEMS, "combined_scope_no_holder")
    entry = check(result, 7)
    assert entry["verdict"] == "FAIL"
    assert WRONG_OUTPUT_K4_T7 not in result_text(result)


def test_k4t7_combined_scope_unproven_not_proven():
    result, expected = run_case(ITEMS, "combined_scope_unproven")
    entry = check(result, 7)
    assert entry["verdict"] == "NOT PROVEN"
    assert WRONG_OUTPUT_K4_T7 not in result_text(result)


def test_k4t8_unrecorded_selection_not_proven():
    result, expected = run_case("F5/k4_kind_closure_item8.json", "unrecorded_selection")
    entry = check(result, 8)
    assert entry["verdict"] == "NOT PROVEN"
    assert WRONG_OUTPUT_K4_T8 not in result_text(result)


def test_k4t8_recorded_holders_not_distinct_fail():
    result, expected = run_case("F5/k4_kind_closure_item8.json", "holders_not_distinct")
    entry = check(result, 8)
    assert entry["verdict"] == "FAIL"
    assert WRONG_OUTPUT_K4_T8 not in result_text(result)


def test_k4t8_recorded_holder_non_full_kind_not_proven():
    result, expected = run_case("F5/k4_kind_closure_item8.json", "holder_fragment")
    entry = check(result, 8)
    assert entry["verdict"] == "NOT PROVEN"
    assert entry["missing_fact"] == expected["missing_fact"]
    assert WRONG_OUTPUT_K4_T8 not in result_text(result)
