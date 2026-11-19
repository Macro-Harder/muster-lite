"""Slice 4 tests, groups K4-T9 to K4-T17. Plan section 6, slice 4.

Fixture sources: F1, F2 and F5 item fixtures at brief section 5.8.1, the
kind closure matrix columns for items 9 and 12, F4 precheck halves for
the precheck limb parts, brief section 5.5 items 9 to 15, the absence
rule at brief section 5.5.1, and the precheck form at brief section
5.6.1. Group K4-T16 branch 4 is the open case branch: no fixture in this
module states a result for that branch, under brief section 5.5.2, and
no test in this module rests a verdict on it.
"""

import json
from pathlib import Path

from conftest import check, checks, field, result_text, run_case

CASES = "F5/k4_items_09_to_17_cases.json"


def _assert_precheck_pair_content(pair_relative_path):
    pair = json.loads(
        (Path(__file__).parent / "fixtures" / pair_relative_path).read_text(
            encoding="utf-8"))
    precheck_input = pair["precheck_half"]["run_input"]
    gate_input = pair["gate_half"]["run_input"]
    assert precheck_input["shared_inputs"] == gate_input["shared_inputs"], (
        "WRONG OUTPUT PAIR: the shared inputs of a precheck pair differing between its halves, "
        + pair_relative_path
    )
    assert pair["gate_half"]["precheck_listing_copied_beside_the_gate_half"] == \
        pair["precheck_half"]["precheck_listing"], (
            "WRONG OUTPUT PAIR: the precheck listing standing beside the gate half differing from the listing in the precheck half, "
            + pair_relative_path
        )
    assert "runs in full every check" in \
        pair["gate_half"]["gate_expectation_in_words"], (
            "WRONG OUTPUT PAIR: the gate expectation in words standing beside the gate half in a form other than the paired fixtures form, "
            + pair_relative_path
        )

WRONG_OUTPUT_K4_T9 = (
    "PASS: logic audit distribution proven, form stated in neither "
    "the heads form nor the named slices form"
)
WRONG_OUTPUT_K4_T10 = (
    "PASS: reduced tier accepted for the claim, no invocation record standing"
)
WRONG_OUTPUT_K4_T12 = "PASS: linkage proven for the seat, author record absent"
WRONG_OUTPUT_K4_T13 = (
    "field 13: table defect, a table entry figure stands in conflict "
    "with a source figure (statement naming neither the table, its "
    "entry and figure, the source and its figure, nor the words source wins)"
)
WRONG_OUTPUT_K4_T15 = (
    "Plaid claim standing on the tier claimed field, refusal form absent from field 13"
)


def test_k4t9_distribution_in_neither_form_not_returned_as_proven():
    result, expected = run_case(CASES, "t9_neither_form")
    entry = check(result, 9)
    assert entry["verdict"] == expected["verdict"]
    assert WRONG_OUTPUT_K4_T9 not in result_text(result), (
        "WRONG OUTPUT K4-T9: " + WRONG_OUTPUT_K4_T9
    )


def test_k4t9_distribution_in_named_slices_form_read_in_that_form():
    result, expected = run_case(CASES, "t9_named_slices_form")
    assert check(result, 9)["distribution_form"] == "by named slices"
    assert expected["form_accepted"] is True
    assert WRONG_OUTPUT_K4_T9 not in result_text(result), (
        "WRONG OUTPUT K4-T9: " + WRONG_OUTPUT_K4_T9
    )


def test_k4t10_reduced_tier_with_no_invocation_record_not_accepted():
    result, expected = run_case(CASES, "t10_reduced_tier_no_invocation")
    entry = check(result, 10)
    assert entry["verdict"] == expected["verdict"]
    assert expected["missing_fact"] in entry["missing_fact"]
    assert WRONG_OUTPUT_K4_T10 not in result_text(result), (
        "WRONG OUTPUT K4-T10: " + WRONG_OUTPUT_K4_T10
    )


def test_k4t10_precheck_part_listed_limb_carries_no_check_result():
    result, expected = run_case(CASES, "t10_precheck_check10")
    assert checks(result, 10) == [], (
        "WRONG OUTPUT K4-T10: a CheckResult printed for check 10 in a precheck, fixture pair F4/k4_t10_precheck_pair.json"
    )
    assert field(result, 6)["limb_results"] is not None
    _assert_precheck_pair_content("F4/k4_t10_precheck_pair.json")


def test_k4t10_tier_statement_limb_runs_in_precheck():
    result, expected = run_case(CASES, "t10_precheck_check10")
    limbs = [e for e in field(result, 6)["limb_results"] if e["check"] == 10]
    assert any(e["limb"] == "tier statement limb" for e in limbs), (
        "WRONG OUTPUT K4-T10: the tier statement run limb of check 10 absent from the precheck limb results"
    )


def test_k4t11_entry_with_label_and_no_basis_not_counted_exempt():
    result, expected = run_case(CASES, "t11_label_no_basis")
    entry = check(result, 11)
    assert entry["entries"][0]["counted_as_exempt"] is expected["counted_as_exempt"], (
        "WRONG OUTPUT K4-T11: an entry with a label and no basis counted as exempt, fixture pair F1 and F2 item fixtures at brief s5.8.1"
    )
    assert entry["verdict"] == expected["verdict"]


def test_k4t11_entry_with_basis_and_no_matching_label_not_counted_exempt():
    result, expected = run_case(CASES, "t11_basis_no_label")
    entry = check(result, 11)
    assert entry["entries"][0]["counted_as_exempt"] is expected["counted_as_exempt"], (
        "WRONG OUTPUT K4-T11: an entry with a basis and no matching label counted as exempt, fixture pair F1 and F2 item fixtures at brief s5.8.1"
    )
    assert entry["verdict"] == expected["verdict"]


def test_k4t12_seat_with_no_author_record_not_proven_on_linkage():
    result, expected = run_case(CASES, "t12_no_author_record")
    entry = check(result, 12)
    assert entry["verdict"] == expected["verdict"]
    assert expected["missing_fact_names"] in entry["missing_fact"], (
        "WRONG OUTPUT K4-T12: " + WRONG_OUTPUT_K4_T12
    )
    assert entry["resting_record_named"] is True, (
        "WRONG OUTPUT K4-T12: NOT PROVEN standing without naming the record the roster id rests on"
    )


def test_k4t12_resting_record_outside_supplied_set_still_not_proven():
    result, expected = run_case(CASES, "t12_resting_record_outside")
    entry = check(result, 12)
    assert entry["verdict"] == expected["verdict"]
    assert entry["resting_record_standing"] == "outside the supplied set, named in words", (
        "WRONG OUTPUT K4-T12: a seat proven on linkage where the resting record stands outside the supplied set"
    )


def test_k4t13_field13_conflict_statement_names_all_parts():
    result, expected = run_case(CASES, "t13_conflict")
    statement = field(result, 13)["table_conflict_statement"]
    for part in expected["field_13_statement_parts"]:
        assert part in statement, (
            "WRONG OUTPUT K4-T13: " + WRONG_OUTPUT_K4_T13
        )


def test_k4t13_field13_conflict_statement_carries_both_figures():
    result, expected = run_case(CASES, "t13_conflict")
    statement = field(result, 13)["table_conflict_statement"]
    assert "table entry" in statement and "figure" in statement
    assert "source" in statement and "source wins" in statement, (
        "WRONG OUTPUT K4-T13: the field 13 conflict statement missing its source and figure, or the words source wins"
    )


def test_k4t13_item13_result_composes_as_its_own_check_result():
    result, expected = run_case(CASES, "t13_conflict")
    assert check(result, 13)["check"] == 13
    assert WRONG_OUTPUT_K4_T13 not in result_text(result), (
        "WRONG OUTPUT K4-T13: " + WRONG_OUTPUT_K4_T13
    )


def test_k4t14_item14_stands_beside_the_rollup_and_never_composes():
    result, expected = run_case(CASES, "t14_beside")
    entry = check(result, 14)
    assert entry["composes"] is expected["composes_rollup"], (
        "WRONG OUTPUT K4-T14: item 14 composing into the rollup, fixture pair beside standing at brief s5.5 item 14"
    )
    assert expected["position"] in result_text(field(result, 13))


def test_k4t14_pass_rollup_stands_where_item14_not_proven_is_only_non_pass_word():
    result, expected = run_case(CASES, "t14_pass_rollup_stands")
    assert field(result, 12) == expected["rollup"], (
        "WRONG OUTPUT K4-T14: a PASS rollup standing where the cured checks compose no PASS rollup, check 4 UNVERIFIABLE on the absent roster beside item 14 NOT PROVEN, fixture pair at brief s5.5 item 14"
    )


def test_k4t14_omission_guard_named_fixture_proves_item14_present():
    result, expected = run_case(CASES, "t14_present")
    assert checks(result, 14) != [], (
        "WRONG OUTPUT K4-T14: item 14 absent from the result, against the omission guard fixture of plan s4 slice 4"
    )


def test_k4t15_plaid_claim_stands_on_tier_applied_only():
    result, expected = run_case(CASES, "t15_plaid_applied")
    assert field(result, 13)["plaid_refusal"] == expected["field_13_carries"], (
        "WRONG OUTPUT K4-T15: " + WRONG_OUTPUT_K4_T15
    )


def test_k4t15_no_plaid_claim_where_only_tier_claimed_is_plaid():
    result, expected = run_case(CASES, "t15_plaid_claimed_only")
    assert "Plaid refusal" not in result_text(field(result, 13)), (
        "WRONG OUTPUT K4-T15: a Plaid claim made to stand on a field other than tier applied"
    )
    assert field(result, 12) in ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE")


def test_k4t16_branch1_roster_absent():
    result, expected = run_case(CASES, "t16_branch1")
    assert result["absence_outcomes"]["branch 1"] == expected["affected_word"], (
        "WRONG OUTPUT K4-T16: branch 1, roster absent, applied in a form other than the branch form at brief s5.5.1"
    )


def test_k4t16_branch2_base_identification_absent():
    result, expected = run_case(CASES, "t16_branch2")
    assert result["absence_outcomes"]["branch 2"] == expected["affected_word"], (
        "WRONG OUTPUT K4-T16: branch 2, pinned base identification absent, applied in a form other than the branch form at brief s5.5.1"
    )
    assert result["absence_outcomes"]["missing_identification_named"] is True


def test_k4t16_branch3_one_named_work_product_absent():
    result, expected = run_case(CASES, "t16_branch3")
    assert result["absence_outcomes"]["branch 3"] == expected["affected_word"], (
        "WRONG OUTPUT K4-T16: branch 3, one named work product absent, applied in a form other than the branch form at brief s5.5.1"
    )


def test_k4t16_branch5_tier_record_absent():
    result, expected = run_case(CASES, "t16_branch5")
    assert result["absence_outcomes"]["branch 5"] == expected["affected_word"], (
        "WRONG OUTPUT K4-T16: branch 5, tier record absent, applied in a form other than the branch form at brief s5.5.1"
    )


def test_k4t16_branch6_one_listed_table_absent():
    result, expected = run_case(CASES, "t16_branch6")
    assert result["absence_outcomes"]["branch 6 complete"] is expected["verification_complete"], (
        "WRONG OUTPUT K4-T16: branch 6, one listed table absent, verification of the pinned base stated as proven complete"
    )


def test_k4t16_pointer_table_stands_for_settled_branches():
    result, expected = run_case(CASES, "t16_pointer")
    assert result["absence_outcomes"]["pointer_table_stands"] is True, (
        "WRONG OUTPUT K4-T16: the pointer table for the settled absence branches absent or restating a branch word"
    )


def test_k4t16_unreadable_record_split_coverage_side():
    result, expected = run_case(CASES, "t16_unreadable_coverage")
    assert result["absence_outcomes"]["unreadable"] == expected["affected_word"], (
        "WRONG OUTPUT K4-T16: the unreadable record split applied on the missing records side for a coverage side case"
    )


def test_k4t16_unreadable_record_split_missing_records_side():
    result, expected = run_case(CASES, "t16_unreadable_missing")
    assert result["absence_outcomes"]["unreadable"] == expected["affected_word"], (
        "WRONG OUTPUT K4-T16: the unreadable record split applied on the coverage side for a missing records side case"
    )


def test_k4t16_no_check_result_for_item18_in_any_run():
    result, expected = run_case(CASES, "t16_item18")
    assert checks(result, 18) == [], (
        "WRONG OUTPUT K4-T16: a CheckResult printed for item 18 in a run"
    )


def test_k4t17_precheck_check10_limbs_run_and_listed_apart():
    result, expected = run_case(CASES, "t10_precheck_check10")
    assert checks(result, 10) == [], (
        "WRONG OUTPUT K4-T17: a CheckResult printed for check 10 in a precheck, fixture pair F4/k4_t17_precheck_pair.json"
    )
    assert "check 10" in field(result, 10), (
        "WRONG OUTPUT K4-T17: listed limbs of check 10 standing in a position other than contract field 10"
    )
    _assert_precheck_pair_content("F4/k4_t17_precheck_pair.json")


def test_k4t17_precheck_check12_limbs_run_and_listed_apart():
    result, expected = run_case(CASES, "t17_check12")
    assert checks(result, 12) == [], (
        "WRONG OUTPUT K4-T17: a CheckResult printed for check 12 in a precheck, fixture pair F4/k4_t17_precheck_pair.json"
    )
    assert "check 12" in field(result, 10)
    _assert_precheck_pair_content("F4/k4_t17_precheck_pair.json")


def test_k4t17_precheck_run_limbs_stand_as_limb_results_at_field6():
    result, expected = run_case(CASES, "t17_check12")
    limbs = field(result, 6)["limb_results"]
    assert all(e["kind"] == "LimbResult" for e in limbs), (
        "WRONG OUTPUT K4-T17: a run limb of a part listed check standing as a CheckResult instead of a LimbResult at field 6"
    )
    _assert_precheck_pair_content("F4/k4_t17_precheck_pair.json")
