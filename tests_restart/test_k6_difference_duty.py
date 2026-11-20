"""Slice 6 tests, groups K6-T1 to K6-T6. Plan section 8, slice 6.

Fixture sources: F1 and F5 at brief section 5.8.1, the seat identity and
difference model and the tying rule and verdict limbs at brief section
5.6.2, and the RecordedPrecheck shape at brief section 5.4, shape 17.
Criterion AC P14 in full, with the listing part of AC P25 at group K6-T5.
Written before any K5 field 9 completion claim in this charge, under the
Edge 11 form three scheduling consequence at plan section 4, item 11:
no test in the K5 module of this charge claims field 9 completion.
"""

import json
from pathlib import Path

from tests_restart.conftest import check, field, result_text, run_case

CASES = "F5/k6_difference_cases.json"
RECORDING = "F1/k6_recording_cases.json"

WRONG_OUTPUT_K6_T1 = (
    "differing seats: seat-old and seat-new returned as one tied rekeyed seat"
)
WRONG_OUTPUT_K6_T3 = {
    "fail_claim": "NOT PROVEN where a claim stands read and contradicted",
    "no_claim": "FAIL where no claim stands",
    "unreadable_claim": (
        "a verdict other than NOT PROVEN where the claim passage "
        "cannot be read without guessing"
    ),
    "honest_reseat_outside": (
        "FAIL for the honest reseat whose record stands outside the supplied set"
    ),
    "frozen_absent": (
        "a word other than UNVERIFIABLE for the frozen roster absence"
    ),
    "gate_absent": (
        "a word other than UNVERIFIABLE for the gate instance absence, "
        "or field 9 silent on that absence"
    ),
    "same_standing_twice": (
        "a word other than UNVERIFIABLE for two records stating the same standing"
    ),
}
WRONG_OUTPUT_K6_T5 = "field 9 in a precheck: gate run difference result stands here"


def test_k6t1_added_seat_difference_kind():
    result, expected = run_case(CASES, "added_seat")
    seats = field(result, 9)["differing_seats"]
    assert seats == expected["differing_seats"]
    assert WRONG_OUTPUT_K6_T1 not in result_text(result)


def test_k6t1_removed_seat_difference_kind():
    result, expected = run_case(CASES, "removed_seat")
    assert field(result, 9)["differing_seats"] == expected["differing_seats"]
    assert WRONG_OUTPUT_K6_T1 not in result_text(result), (
        "WRONG OUTPUT K6-T1: " + WRONG_OUTPUT_K6_T1
        + ", fixture pair F5/k6_difference_cases.json case removed_seat against its wrong output"
    )


def test_k6t1_changed_holder_difference_kind():
    result, expected = run_case(CASES, "changed_holder")
    assert field(result, 9)["differing_seats"] == expected["differing_seats"]
    assert WRONG_OUTPUT_K6_T1 not in result_text(result), (
        "WRONG OUTPUT K6-T1: " + WRONG_OUTPUT_K6_T1
        + ", fixture pair F5/k6_difference_cases.json case changed_holder against its wrong output"
    )


def test_k6t1_removed_and_added_pair_difference_kind():
    result, expected = run_case(CASES, "removed_added_pair")
    assert field(result, 9)["differing_seats"] == expected["differing_seats"]
    assert WRONG_OUTPUT_K6_T1 not in result_text(result), (
        "WRONG OUTPUT K6-T1: " + WRONG_OUTPUT_K6_T1
        + ", fixture pair F5/k6_difference_cases.json case removed_added_pair against its wrong output"
    )


def test_k6t1_rekeyed_configuration_not_tied_without_reseat_record():
    result, expected = run_case(CASES, "rekeyed")
    difference = field(result, 9)
    assert difference["differing_seats"] == expected["differing_seats"]
    assert difference["tied"] is False, (
        "WRONG OUTPUT K6-T1: " + WRONG_OUTPUT_K6_T1
    )


def test_k6t2_row1_multiple_satisfying_records_unexplained():
    result, expected = run_case(CASES, "row1")
    seat = field(result, 9)["differing_seats"][0]
    assert seat["tying_row"] == expected["row"]
    assert seat["classification"] == expected["classification"], (
        "WRONG OUTPUT K6-T2: row 1 seat classified as tied on two satisfying records"
    )


def test_k6t2_row2_one_satisfying_beside_non_matching_unexplained():
    result, expected = run_case(CASES, "row2")
    seat = field(result, 9)["differing_seats"][0]
    assert seat["tying_row"] == expected["row"]
    assert seat["classification"] == expected["classification"], (
        "WRONG OUTPUT K6-T2: row 2 seat classified as tied beside a non matching record"
    )


def test_k6t2_row3_exactly_one_satisfying_no_non_matching_tied():
    result, expected = run_case(CASES, "row3")
    seat = field(result, 9)["differing_seats"][0]
    assert seat["tying_row"] == expected["row"]
    assert seat["classification"] == expected["classification"], (
        "WRONG OUTPUT K6-T2: row 3 seat classified as unexplained on its own counts"
    )


def test_k6t2_row4_no_satisfying_record_holder_kind_named_as_missing_fact():
    result, expected = run_case(CASES, "row4")
    seat = field(result, 9)["differing_seats"][0]
    assert seat["tying_row"] == expected["row"]
    assert expected["missing_fact_names"] in check(result, 17)["missing_fact"], (
        "WRONG OUTPUT K6-T2: row 4 missing fact standing that does not name the non full holder kind"
    )


def test_k6t2_shared_record_cited_and_named_as_shared_ties_no_two_seats():
    result, expected = run_case(CASES, "shared_record")
    difference = field(result, 9)
    assert difference["shared_record_cited_and_named_as_shared"] is True
    assert difference["one_record_ties_two_seats"] is expected["one_record_ties_two_seats"], (
        "WRONG OUTPUT K6-T2: one record tying two differing seats outside the companion exception"
    )


def test_k6t2_companion_exception_pair_sentinel_records_each_tie_one_seat():
    result, expected = run_case(CASES, "companion_pair")
    for seat in field(result, 9)["differing_seats"]:
        assert seat["classification"] == expected["classification_per_seat"], (
            "WRONG OUTPUT K6-T2: one sentinel record of a pair counted as satisfying both seats of the pair"
        )


def test_k6t3_fail_where_claim_standing_read_and_contradicted():
    result, expected = run_case(CASES, "fail_claim")
    assert check(result, 17)["verdict"] == expected["verdict"], (
        "WRONG OUTPUT K6-T3: " + WRONG_OUTPUT_K6_T3["fail_claim"]
    )


def test_k6t3_not_proven_where_no_claim_stands():
    result, expected = run_case(CASES, "no_claim")
    assert check(result, 17)["verdict"] == expected["verdict"], (
        "WRONG OUTPUT K6-T3: " + WRONG_OUTPUT_K6_T3["no_claim"]
    )


def test_k6t3_not_proven_where_claim_passage_cannot_be_read_without_guessing():
    result, expected = run_case(CASES, "unreadable_claim")
    assert check(result, 17)["verdict"] == expected["verdict"], (
        "WRONG OUTPUT K6-T3: " + WRONG_OUTPUT_K6_T3["unreadable_claim"]
    )


def test_k6t3_not_proven_for_honest_reseat_record_outside_supplied_set():
    result, expected = run_case(CASES, "honest_reseat_outside")
    assert check(result, 17)["verdict"] == expected["verdict"], (
        "WRONG OUTPUT K6-T3: " + WRONG_OUTPUT_K6_T3["honest_reseat_outside"]
    )


def test_k6t3_unverifiable_for_frozen_roster_absence():
    result, expected = run_case(CASES, "frozen_absent")
    assert check(result, 17)["verdict"] == expected["verdict"], (
        "WRONG OUTPUT K6-T3: " + WRONG_OUTPUT_K6_T3["frozen_absent"]
    )


def test_k6t3_unverifiable_for_gate_instance_absence_field9_in_words():
    result, expected = run_case(CASES, "gate_absent")
    assert check(result, 17)["verdict"] == expected["verdict"]
    assert field(result, 9)["absence_statement"] == expected["field_9_carries"], (
        "WRONG OUTPUT K6-T3: " + WRONG_OUTPUT_K6_T3["gate_absent"]
    )


def test_k6t3_unverifiable_for_two_records_stating_the_same_standing():
    result, expected = run_case(CASES, "same_standing_twice")
    assert check(result, 17)["verdict"] == expected["verdict"], (
        "WRONG OUTPUT K6-T3: " + WRONG_OUTPUT_K6_T3["same_standing_twice"]
    )


def test_k6t4_recording_mismatch_file_row_value_none_recorded():
    result, expected = run_case(RECORDING, "file")
    element = field(result, 9)["d12_element"]
    assert element["rows"]["file"] == expected["field_9_value_for_row"], (
        "WRONG OUTPUT K6-T4: a value other than none recorded for this frozen roster on the file row"
    )
    assert element["other_roster_recording_named_apart"] is True
    assert expected["named_apart_words"] in result_text(element), (
        "WRONG OUTPUT K6-T4: the recording for the file row carried for this frozen roster, or named apart in words other than the words brief section 5.6.2 states"
    )


def test_k6t4_recording_mismatch_stage_row_value_none_recorded():
    result, expected = run_case(RECORDING, "stage")
    element = field(result, 9)["d12_element"]
    assert element["rows"]["stage"] == expected["field_9_value_for_row"], (
        "WRONG OUTPUT K6-T4: a value other than none recorded for this frozen roster on the stage row"
    )
    assert element["other_roster_recording_named_apart"] is True
    assert expected["named_apart_words"] in result_text(element), (
        "WRONG OUTPUT K6-T4: the recording for the stage row carried for this frozen roster, or named apart in words other than the words brief section 5.6.2 states"
    )


def test_k6t4_recording_mismatch_hash_row_value_none_recorded():
    result, expected = run_case(RECORDING, "hash")
    element = field(result, 9)["d12_element"]
    assert element["rows"]["hash"] == expected["field_9_value_for_row"], (
        "WRONG OUTPUT K6-T4: a value other than none recorded for this frozen roster on the hash row"
    )
    assert element["other_roster_recording_named_apart"] is True
    assert expected["named_apart_words"] in result_text(element), (
        "WRONG OUTPUT K6-T4: the recording for the hash row carried for this frozen roster, or named apart in words other than the words brief section 5.6.2 states"
    )


def test_k6t4_recording_mismatch_byte_size_row_value_none_recorded():
    result, expected = run_case(RECORDING, "byte size")
    element = field(result, 9)["d12_element"]
    assert element["rows"]["byte size"] == expected["field_9_value_for_row"], (
        "WRONG OUTPUT K6-T4: a value other than none recorded for this frozen roster on the byte size row"
    )
    assert element["other_roster_recording_named_apart"] is True
    assert expected["named_apart_words"] in result_text(element), (
        "WRONG OUTPUT K6-T4: the recording for the byte size row carried for this frozen roster, or named apart in words other than the words brief section 5.6.2 states"
    )


def test_k6t4_two_matching_recordings_conflict_carried_without_check17_effect():
    result, expected = run_case(RECORDING, "two_matching_conflict")
    element = field(result, 9)["d12_element"]
    assert element["recordings_carried"] == expected["both_carried"]
    assert element["order"] == expected["order"]
    assert element["conflict_named"] is True
    assert element["check_17_effect"] == expected["check_17_effect"], (
        "WRONG OUTPUT K6-T4: check 17 changed by a recording conflict that stands apart from it"
    )


def test_k6t4_no_recording_record_field9_none_and_check17_unaffected():
    result, expected = run_case(RECORDING, "no_recording")
    assert field(result, 9)["recorded_precheck"] == expected["field_9_value"]
    assert "OPEN CASE" not in result_text(result), (
        "WRONG OUTPUT K6-T4: an OPEN CASE state standing in a position of the no recording record case"
    )
    assert check(result, 17)["verdict"] in ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE"), (
        "WRONG OUTPUT K6-T4: check 17 changed in its verdict word by the absence of a recording record"
    )


def test_k6t5_precheck_field9_carries_not_a_gate_run():
    result, expected = run_case("F4/k6_t5_precheck_cases.json", "precheck")
    assert field(result, 9) == expected["field_9"], (
        "WRONG OUTPUT K6-T5: " + WRONG_OUTPUT_K6_T5
    )


def test_k6t5_precheck_no_check_result_or_limb_result_for_check17():
    result, expected = run_case("F4/k6_t5_precheck_cases.json", "precheck")
    assert expected["check_17_check_result"] is None
    from tests_restart.conftest import checks
    assert checks(result, 17) == [], (
        "WRONG OUTPUT K6-T5: a CheckResult standing for check 17 in a precheck"
    )
    assert field(result, 6)["limb_results_for_check_17"] == [], (
        "WRONG OUTPUT K6-T5: a LimbResult standing for check 17 in a precheck"
    )


def test_k6t5_precheck_check17_listed_in_full_at_field10():
    result, expected = run_case("F4/k6_t5_precheck_cases.json", "precheck")
    assert expected["check_17_listing"] in field(result, 10), (
        "WRONG OUTPUT K6-T5: check 17 standing in the field 10 section in a form other than listed in full"
    )
    pair = json.loads(
        (Path(__file__).parent / "fixtures" / "F4"
         / "k6_t5_precheck_pair.json").read_text(encoding="utf-8"))
    assert pair["precheck_half"]["run_input"]["shared_inputs"] == \
        pair["gate_half"]["run_input"]["shared_inputs"], (
            "WRONG OUTPUT K6-T5: the shared inputs of the check 17 precheck pair differing between its halves"
        )
    assert pair["gate_half"]["precheck_listing_copied_beside_the_gate_half"] == \
        pair["precheck_half"]["precheck_listing"], (
            "WRONG OUTPUT K6-T5: the precheck listing standing beside the gate half differing from the listing in the precheck half"
        )
    assert "runs in full every check" in \
        pair["gate_half"]["gate_expectation_in_words"], (
            "WRONG OUTPUT K6-T5: the gate expectation in words standing beside the gate half in a form other than the paired fixtures form"
        )


def test_k6t6_duplicated_seat_key_frozen_side_form():
    result, expected = run_case(CASES, "dup_frozen")
    seats = field(result, 9)["differing_seats"]
    by_kind = {seat["kind"]: seat for seat in seats}
    assert by_kind["changed holder"]["classification"] == expected["paired_first"]
    assert by_kind["removed seat"]["classification"] == expected["unpaired_second"], (
        "WRONG OUTPUT K6-T6: the unpaired second entry classified on counts taken over the seat key as a whole, frozen side form"
    )
    assert check(result, 17)["verdict"] == expected["check_17_verdict"]


def test_k6t6_duplicated_seat_key_gate_side_form():
    result, expected = run_case(CASES, "dup_gate")
    seats = field(result, 9)["differing_seats"]
    by_kind = {seat["kind"]: seat for seat in seats}
    assert by_kind["changed holder"]["classification"] == expected["paired_first"]
    assert by_kind["added seat"]["classification"] == expected["unpaired_second"], (
        "WRONG OUTPUT K6-T6: the unpaired second entry classified on counts taken over the seat key as a whole, gate side form"
    )
    assert check(result, 17)["verdict"] == expected["check_17_verdict"]
