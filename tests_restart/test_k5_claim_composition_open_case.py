"""Slice 5 tests, groups K5-T1 to K5-T7. Plan section 6, slice 5.

Fixture sources: F1 and F3 at brief section 5.8.1 for groups K5-T1 to
K5-T4, F5 and the composition fixtures at brief section 5.8.1 for group
K5-T5, F1 and F2 for group K5-T6, and the open case fixtures at brief
section 5.8.1 with the OPEN CASE machinery at brief section 5.4.2 for
group K5-T7. The cure acts at group K5-T6 stand in the words of the
RepairEntry derivation table at brief section 5.4, shape 15.

Scheduling, in the open: the K6 groups of this charge stand written
before this module, and no test in this module claims a field 9
completion, under the Edge 11 form three consequence at plan section 4,
item 11. The gap track tests, group K5-T7 and the withdrawal absence
sweep at the foot of this file, stand written last in this charge, under
the RI-15 decoupling at the Step 13 test plan section 4.
"""

import json
from pathlib import Path

from conftest import check, field, load_case, require_kernel, result_text, run_case

CASES = "F1/k5_cases.json"
COMPOSITION = "F5/k5_composition_cases.json"

WRONG_OUTPUT_K5_T1 = (
    "generated statement point: the stage ran with the roster as frozen, "
    "a point standing only in the written claim"
)
WRONG_OUTPUT_K5_T3_KINDLESS = "FAIL for the kindless claim point"
WRONG_OUTPUT_K5_T3_UNKNOWN = "numeric disagreement printed for the cohort claim point: 9 against 5, a subtraction over the unknown kind"
WRONG_OUTPUT_K5_T3_UNGUESSABLE = "claim point read as figure 4 from a passage that cannot be read without guessing"
WRONG_OUTPUT_K5_T5 = "a rollup word carried at field 12 in an open case run that is not a precheck"
WRONG_OUTPUT_K5_T5_BOUND = "the trace standing bound standing at a field other than field 13"


def test_k5t1_generated_statement_carries_no_point_from_the_claim_alone():
    result, expected = run_case(CASES, "t1_point_from_claim_only")
    generated = result["generated_statement"]["points"]
    assert expected["generated_statement_contains_point"] is False
    assert "the stage ran with the roster as frozen" not in generated, (
        "WRONG OUTPUT K5-T1: " + WRONG_OUTPUT_K5_T1
    )


def test_k5t1_generation_does_not_read_the_written_claim():
    result, expected = run_case(CASES, "t1_generation_without_claim_read")
    assert result["generated_statement"]["claim_read_during_generation"] is \
        expected["generation_read_claim"], (
            "WRONG OUTPUT K5-T1: a generated statement point that could only stand if the written claim had been read during generation"
        )


def test_k5t2_claim_point_with_no_generated_point_carried_as_difference():
    result, expected = run_case(CASES, "t2_claim_point_no_generated")
    differences = field(result, 8)
    assert differences != [], (
        "WRONG OUTPUT K5-T2: a claim point with no generated point passed over in silence, fixture pair F2 and F3 at brief s5.8.1"
    )
    assert expected["difference_carried"] is True


def test_k5t2_generated_point_no_claim_mentions_carried_as_difference():
    result, expected = run_case(CASES, "t2_generated_point_no_claim")
    differences = field(result, 8)
    assert differences != [], (
        "WRONG OUTPUT K5-T2: a generated point no claim mentions passed over in silence, fixture pair F2 and F3 at brief s5.8.1"
    )
    assert expected["difference_carried"] is True


def test_k5t2_build_union_claim_figure_not_printed_as_computed_figure():
    result, expected = run_case(CASES, "t2_build_union")
    union = field(result, 7)["build_union"]
    assert union["state"] == expected["state"]
    assert "39" not in result_text(union), (
        "WRONG OUTPUT K5-T2: a claim figure printed as a computed figure for the build union"
    )
    assert check(result, 16)["verdict"] == expected["claim_point_verdict"]


def test_k5t2_trace_standing_below_100_percent_not_reported_as_closed():
    result, expected = run_case(CASES, "t2_trace_below_100")
    assert expected["field_13_carries"] in result_text(field(result, 13)), (
        "WRONG OUTPUT K5-T2: a trace standing below 100 percent LANDED reported in a form that reads as closed"
    )
    assert expected["reported_as_closed"] is False


def test_k5t3_kindless_claim_point_not_proven_and_no_false_fail():
    result, expected = run_case(CASES, "t3_kindless")
    entry = check(result, 16)
    assert entry["verdict"] == expected["verdict"], (
        "WRONG OUTPUT K5-T3: " + WRONG_OUTPUT_K5_T3_KINDLESS
    )


def test_k5t3_unknown_kind_claim_point_not_proven_kind_named_no_disagreement():
    result, expected = run_case(CASES, "t3_unknown_kind")
    entry = check(result, 16)
    assert entry["verdict"] == expected["verdict"]
    assert expected["unknown_kind_named"] in entry["missing_fact"], (
        "WRONG OUTPUT K5-T3: the unknown kind standing unnamed in the missing fact for the cohort claim point"
    )
    assert "disagreement" not in result_text(field(result, 8)), (
        "WRONG OUTPUT K5-T3: " + WRONG_OUTPUT_K5_T3_UNKNOWN
    )


def test_k5t3_unguessable_passage_not_proven_and_no_guessed_reading():
    result, expected = run_case(CASES, "t3_unguessable")
    entry = check(result, 16)
    assert entry["verdict"] == expected["verdict"]
    assert "figure 4" not in result_text(entry), (
        "WRONG OUTPUT K5-T3: " + WRONG_OUTPUT_K5_T3_UNGUESSABLE
    )


def test_k5t4_first_form_no_difference_on_recording_capacity_alone():
    data = json.loads(
        (Path(__file__).parent / "fixtures" / "F3"
         / "k5_t4_recording_pair_first.json").read_text(encoding="utf-8"))
    kernel = require_kernel()
    result = kernel.compute_result(data["expected_fixture"]["run_input"])
    assert field(result, 8) == [], (
        "WRONG OUTPUT K5-T4: a difference raised on recording capacity alone, first form, wrong fixture F3/k5_t4_recording_pair_first.json"
    )
    assert data["expected_fixture"]["expected"]["d12_carrying"] == (
        "carried in the D12 element at section 5.6.2 as recorded"
    )
    recorded = data["expected_fixture"]["run_input"]["recording_record"]
    assert recorded["precheck_result_as_recorded"] in result_text(field(result, 9)), (
        "WRONG OUTPUT K5-T4: the recording record for the recording capacity case standing in a position other than the D12 element, first form"
    )


def test_k5t4_second_form_no_difference_on_recording_capacity_alone():
    data = json.loads(
        (Path(__file__).parent / "fixtures" / "F3"
         / "k5_t4_recording_pair_second.json").read_text(encoding="utf-8"))
    kernel = require_kernel()
    result = kernel.compute_result(data["expected_fixture"]["run_input"])
    assert field(result, 8) == [], (
        "WRONG OUTPUT K5-T4: a difference raised on recording capacity alone, second form, wrong fixture F3/k5_t4_recording_pair_second.json"
    )
    assert data["expected_fixture"]["expected"]["d12_carrying"] == (
        "carried in the D12 element at section 5.6.2 as recorded"
    )
    recorded = data["expected_fixture"]["run_input"]["recording_record"]
    assert recorded["precheck_result_as_recorded"] in result_text(field(result, 9)), (
        "WRONG OUTPUT K5-T4: the recording record for the recording capacity case standing in a position other than the D12 element, second form"
    )


def test_k5t4_first_form_ordinary_difference_outside_the_recording_fields():
    data = json.loads(
        (Path(__file__).parent / "fixtures" / "F3"
         / "k5_t4_recording_pair_first.json").read_text(encoding="utf-8"))
    kernel = require_kernel()
    result = kernel.compute_result(data["outside_fields_fixture"]["run_input"])
    assert field(result, 8) != [], (
        "WRONG OUTPUT K5-T4: no difference raised for a passage outside the six recording fields, first form"
    )


def test_k5t4_second_form_ordinary_difference_outside_the_recording_fields():
    data = json.loads(
        (Path(__file__).parent / "fixtures" / "F3"
         / "k5_t4_recording_pair_second.json").read_text(encoding="utf-8"))
    kernel = require_kernel()
    result = kernel.compute_result(data["outside_fields_fixture"]["run_input"])
    assert field(result, 8) != [], (
        "WRONG OUTPUT K5-T4: no difference raised for a passage outside the six recording fields, second form"
    )
    expected = data["outside_fields_fixture"]["expected"]
    assert expected["difference_direction"] == "second direction of the comparison"
    assert check(result, 16)["verdict"] == expected["omitted_point_verdict"], (
        "WRONG OUTPUT K5-T4: a word other than NOT PROVEN for the omitted point in the second form of the passage outside recording capacity fixture"
    )
    assert expected["d12_carrying"] == (
        "carried in the D12 element at section 5.6.2 as recorded, for its recording capacity"
    )


def test_k5t5_composition_row1_open_case_no_rollup_word():
    result, expected = run_case(COMPOSITION, "row1")
    assert result["composition"]["governing_row"] == expected["row_governs"], (
        "WRONG OUTPUT K5-T5: composition row 1, a rollup word standing at field 12 in a run meeting an open case"
    )
    assert field(result, 12) not in ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE"), (
        "WRONG OUTPUT K5-T5: composition row 1, a rollup word standing at field 12 in a run meeting an open case"
    )


def test_k5t5_composition_row2_proven_failure_carries_fail():
    result, expected = run_case(COMPOSITION, "row2")
    assert result["composition"]["governing_row"] == expected["row_governs"], (
        "WRONG OUTPUT K5-T5: composition row 2, a word other than FAIL standing where a composing check takes FAIL"
    )
    assert field(result, 12) == expected["rollup"], (
        "WRONG OUTPUT K5-T5: composition row 2, a word other than FAIL standing where a composing check takes FAIL"
    )


def test_k5t5_composition_row3_plaid_bound():
    result, expected = run_case(COMPOSITION, "row3")
    assert result["composition"]["governing_row"] == expected["row_governs"], (
        "WRONG OUTPUT K5-T5: composition row 3, a PASS rollup standing on a Plaid claim, or the bound word standing as a composed word in case two"
    )
    assert field(result, 12) == expected["rollup"], (
        "WRONG OUTPUT K5-T5: composition row 3, a PASS rollup standing on a Plaid claim"
    )


def test_k5t5_composition_row4_composed_word_order():
    result, expected = run_case(COMPOSITION, "row4")
    assert result["composition"]["governing_row"] == expected["row_governs"], (
        "WRONG OUTPUT K5-T5: composition row 4, the rollup standing as a word later in the order FAIL, UNVERIFIABLE, NOT PROVEN, PASS than the first word a composing check takes"
    )
    assert field(result, 12) == expected["rollup"], (
        "WRONG OUTPUT K5-T5: composition row 4, the rollup standing as a word later in the order FAIL, UNVERIFIABLE, NOT PROVEN, PASS than the first word a composing check takes"
    )


def test_k5t5_composition_row5_all_pass():
    result, expected = run_case(COMPOSITION, "row5")
    assert result["composition"]["governing_row"] == expected["row_governs"], (
        "WRONG OUTPUT K5-T5: composition row 5, a PASS rollup standing where a composing check takes a word other than PASS"
    )
    assert field(result, 12) == expected["rollup"], (
        "WRONG OUTPUT K5-T5: composition row 5, a PASS rollup standing where a composing check takes a word other than PASS"
    )


def test_k5t5_law_order_of_listing():
    kernel = require_kernel()
    case = load_case(COMPOSITION, "law_order")
    expected = case["expected"]
    result_a = kernel.compute_result(case["run_input_a"])
    result_b = kernel.compute_result(case["run_input_b"])
    assert field(result_a, 12) == expected["rollup_a"]
    assert field(result_b, 12) == expected["rollup_b"], (
        "WRONG OUTPUT K5-T5: a rollup that changes when the composing checks are listed in another order, against the order of listing law"
    )


def test_k5t5_law_grouping():
    kernel = require_kernel()
    case = load_case(COMPOSITION, "law_grouping")
    expected = case["expected"]
    result_a = kernel.compute_result(case["run_input_a"])
    result_b = kernel.compute_result(case["run_input_b"])
    assert field(result_a, 12) == expected["rollup_a"]
    assert field(result_b, 12) == expected["rollup_b"], (
        "WRONG OUTPUT K5-T5: a rollup of grouped composing checks differing from the rollup of the whole set, against the grouping law"
    )


def test_k5t5_law_pass_identity():
    kernel = require_kernel()
    case = load_case(COMPOSITION, "law_pass")
    expected = case["expected"]
    result_a = kernel.compute_result(case["run_input_a"])
    result_b = kernel.compute_result(case["run_input_b"])
    assert field(result_a, 12) == expected["rollup_a"]
    assert field(result_b, 12) == expected["rollup_b"], (
        "WRONG OUTPUT K5-T5: a rollup changed by adding a composing PASS check, against the PASS identity law"
    )


def test_k5t5_law_monotonicity():
    kernel = require_kernel()
    case = load_case(COMPOSITION, "law_monotonicity")
    expected = case["expected"]
    result_a = kernel.compute_result(case["run_input_a"])
    result_b = kernel.compute_result(case["run_input_b"])
    order = ["FAIL", "UNVERIFIABLE", "NOT PROVEN", "PASS"]
    assert field(result_a, 12) == expected["rollup_a"]
    assert field(result_b, 12) == expected["rollup_b"]
    assert order.index(field(result_b, 12)) <= order.index(field(result_a, 12)), (
        "WRONG OUTPUT K5-T5: a rollup that improves when a composing word is weakened along the D16 order, against the monotonicity law"
    )


def test_k5t5_law_isolation():
    kernel = require_kernel()
    case = load_case(COMPOSITION, "law_isolation")
    expected = case["expected"]
    result_a = kernel.compute_result(case["run_input_a"])
    result_b = kernel.compute_result(case["run_input_b"])
    assert field(result_a, 12) == expected["rollup_a"]
    assert field(result_b, 12) == expected["rollup_b"], (
        "WRONG OUTPUT K5-T5: a word from a non composing check entering the rollup, against the isolation law"
    )


def test_k5t5_no_rollup_word_at_field12_in_open_case_run_not_a_precheck():
    result, expected = run_case(CASES, "t5_open_case_rollup")
    assert field(result, 12) not in ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE"), (
        "WRONG OUTPUT K5-T5: " + WRONG_OUTPUT_K5_T5
    )


def test_k5t5_bound_standing_at_field13_and_nowhere_else():
    result, expected = run_case(CASES, "t5_bound_position")
    assert expected["bounds_stand_at"] == "field 13"
    for number in ("6", "7", "8", "12"):
        assert "standing bound" not in result_text(field(result, int(number))), (
            "WRONG OUTPUT K5-T5: " + WRONG_OUTPUT_K5_T5_BOUND
        )


def test_k5t6_missing_seat_entry_carries_its_derivation_table_cure_act():
    result, expected = run_case(CASES, "t6_missing_seat")
    entries = [e for e in field(result, 11) if e["entry_kind"] == "missing seat"]
    assert entries and entries[0]["cure_act"] == expected["cure_act"], (
        "WRONG OUTPUT K5-T6: a missing seat entry carrying a cure act other than the act its derivation table produces, fixture pair F1 and F2 at brief s5.8.1"
    )


def test_k5t6_duplicate_holding_entry_carries_its_derivation_table_cure_act():
    result, expected = run_case(CASES, "t6_duplicate_holding")
    entries = [e for e in field(result, 11) if e["entry_kind"] == "duplicate holding"]
    assert entries and entries[0]["cure_act"] == expected["cure_act"], (
        "WRONG OUTPUT K5-T6: a duplicate holding entry carrying a cure act other than the act its derivation table produces, fixture pair F1 and F2 at brief s5.8.1"
    )


def test_k5t6_unproven_seat_absent_record_cure_act():
    result, expected = run_case(CASES, "t6_unproven_absent_record")
    entries = [e for e in field(result, 11) if e["entry_kind"] == "unproven seat"]
    assert entries and entries[0]["cure_act"] == expected["cure_act"], (
        "WRONG OUTPUT K5-T6: an unproven seat entry on an absent record carrying a restaffing act as its cure, fixture pair F1 and F2 at brief s5.8.1"
    )


def test_k5t6_unproven_seat_other_reason_cure_act_names_the_fact():
    result, expected = run_case(CASES, "t6_unproven_other_reason")
    entries = [e for e in field(result, 11) if e["entry_kind"] == "unproven seat"]
    assert entries and entries[0]["cure_act"] == expected["cure_act_form"], (
        "WRONG OUTPUT K5-T6: an unproven seat entry carrying a cure act that does not name the missing fact it would settle, fixture pair F1 and F2 at brief s5.8.1"
    )


# Gap track, written last in this charge. Group K5-T7: OPEN CASE carrying,
# field by field, for the single absent file case and for the words alone
# base case, under RI-10 and the Step 13 test plan section 7.1. No test in
# this group rests a verdict on G-38, and no test in the words alone part
# states, implies, or rests on an outcome for the words alone case: that
# part asserts output positions only, as brief section 5.3 and brief
# section 5.4.2 state them.


def test_k5t7_absent_file_fields_1_to_5_stand_as_usual():
    result, expected = run_case(CASES, "t7_absent_file")
    for number in (1, 2, 3, 4, 5):
        assert field(result, number) is not None, (
            "WRONG OUTPUT K5-T7: field %d of the single absent file case standing in a form other than its usual form" % number
        )
    assert expected["fields_1_to_5_as_usual"] is True


def test_k5t7_absent_file_affected_check_verdict_position_open_case():
    result, expected = run_case(CASES, "t7_absent_file")
    affected = [e for e in result["check_results"] if e["affected"]]
    assert affected and all(
        e["verdict_position"] == expected["affected_verdict_position"]
        for e in affected), (
            "WRONG OUTPUT K5-T7: a verdict word standing for an affected check in the single absent file case"
        )


def test_k5t7_absent_file_no_difference_for_a_claim_point_of_the_absent_file():
    result, expected = run_case(CASES, "t7_absent_file")
    differences = field(result, 8)
    assert all(d["claim_file"] != "claim-bearing-file-a.md" for d in differences), (
        "WRONG OUTPUT K5-T7: a difference carried for a claim point whose file is the absent file"
    )


def test_k5t7_absent_file_no_repair_entry_for_an_affected_check():
    result, expected = run_case(CASES, "t7_absent_file")
    entries = field(result, 11)
    assert all(e["check"] not in (e2["check"] for e2 in result["check_results"] if e2["affected"]) for e in entries), (
        "WRONG OUTPUT K5-T7: a repair entry carried for an affected check in the single absent file case"
    )


def test_k5t7_absent_file_no_rollup_word_and_open_case_statement_at_field13():
    result, expected = run_case(CASES, "t7_absent_file")
    assert field(result, 12) not in ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE"), (
        "WRONG OUTPUT K5-T7: a rollup word standing in the single absent file case"
    )
    assert expected["field_13_carries"] in result_text(field(result, 13)), (
        "WRONG OUTPUT K5-T7: the open case statement standing in a position other than field 13 among the bounds"
    )


def test_k5t7_words_alone_pinned_base_line_carries_open_case():
    result, expected = run_case(CASES, "t7_words_alone")
    assert result["base_line"] == expected["base_line"], (
        "WRONG OUTPUT K5-T7: the pinned base line in a form carrying a name, hash and byte size line, or carrying no OPEN CASE state, for the words alone case"
    )


def test_k5t7_words_alone_field4_carries_open_case_in_the_base_position():
    result, expected = run_case(CASES, "t7_words_alone")
    assert field(result, 4)["base_position"] == expected["field_4_base_position"], (
        "WRONG OUTPUT K5-T7: contract field 4 carrying a base identity in the base position for the words alone case"
    )


def test_k5t7_words_alone_affected_checks_carry_open_case_and_no_verdict_word():
    result, expected = run_case(CASES, "t7_words_alone")
    affected = [e for e in result["check_results"] if e["affected"]]
    assert affected and all(
        e["verdict_position"] == expected["affected_verdict_position"]
        and e.get("verdict") is None for e in affected), (
            "WRONG OUTPUT K5-T7: a verdict word standing for an affected check in the words alone case"
        )


def test_k5t7_words_alone_field12_carries_no_rollup_word():
    result, expected = run_case(CASES, "t7_words_alone")
    assert field(result, 12) not in ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE"), (
        "WRONG OUTPUT K5-T7: a rollup word standing at field 12 for the words alone case"
    )


def test_k5t7_words_alone_no_name_hash_byte_size_line_in_base_position():
    result, expected = run_case(CASES, "t7_words_alone")
    base = result_text(field(result, 4))
    assert "byte size" not in base and "hash" not in base, (
        "WRONG OUTPUT K5-T7: a name, hash and byte size line standing in the base position for the words alone case"
    )


def test_withdrawal_absence_sweep():
    # Sweep assertion about this suite itself, charged at the Step 13 test
    # plan section 6.4. It stands in no group, rests on no criterion, and
    # is not a test of the product. The withdrawn identifier is assembled
    # in parts here so the sweep text itself does not carry it.
    withdrawn = "test_" + "specimen_" + "step20_" + "set_" + "s5_" + "e26_" + "form"
    package = Path(__file__).parent
    offenders = []
    for path in package.rglob("*"):
        if path.is_file() and "__pycache__" not in str(path):
            if withdrawn in path.read_text(encoding="utf-8", errors="ignore"):
                offenders.append(str(path))
    assert offenders == [], (
        "WRONG OUTPUT SUITE: the withdrawn specimen test standing in a test name, a fixture, or an expected result under tests_restart"
    )
