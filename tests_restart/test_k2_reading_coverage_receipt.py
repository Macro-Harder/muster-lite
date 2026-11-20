"""Slice 2 groups K2-T1 to K2-T5: reading, coverage and receipt.

Loci: plan sections 4 (slice 2) and 6; brief sections 5.2, 5.3 and
5.7.10; brief section 5.8.1 for families F1, F2, F3 and F5. This module
also carries the Question 6 named fixture, the step record alone
fixture, inside group K2-T5 under fixtures/F5/, as the Step 13 test
plan section 7.4 charges. Every test states its concrete wrong output
in the form charged for its group. The restart product does not exist,
so each test fails on the import of muster_restart.kernel inside
conftest.require_kernel and on no other ground.
"""

import json
from pathlib import Path

from tests_restart.conftest import field, result_text, run_case

FIXTURES = Path(__file__).parent / "fixtures"
COVERAGE = "F1/k2_coverage.json"
RESEAT = "F3/k2_reseat_coverage.json"
TABLES = "F5/k2_table_verification.json"

# K2-T1 wrong output, fixture pair form: the coverage standings of all
# groups flattened into one coverage count. The pair stands at
# fixtures/F1/k2t1_expected.json and fixtures/F1/k2t1_wrong.json.
WRONG_OUTPUT_K2_T1 = "coverage: one flattened count of 3 for every group"

# K2-T2 wrong output, named constant form: the roster record or the
# step record counted twice in one coverage count.
WRONG_OUTPUT_K2_T2 = "records read for the stage records group: 2, the roster record counted twice"

# K2-T4 wrong output, named constant form: a ReceiptEntry printed for
# a file offered and not read.
WRONG_OUTPUT_K2_T4 = "ReceiptEntry: offered-not-read.md, sha256 0000, 10 bytes"

# K2-T5 wrong output for the standing cases: counting allowed to
# proceed on a failed table verification standing.
WRONG_OUTPUT_K2_T5 = "counting proceeded on a failed table verification standing"

# Question 6 named fixture wrong output, in the RF-03 form the Step 11
# gate record charges: verdicts returned on the affected rule checks
# on the footing that the step record identification is the pinned base.
WRONG_OUTPUT_K2_T5_STEP_RECORD_ALONE = "verdicts returned on the affected rule checks on the footing that the step record identification is the pinned base"


def _coverage(case_name, source=COVERAGE):
    result, expected = run_case(source, case_name)
    return field(result, 5)["coverage"], expected


def test_k2t1_audit_plan_group_at_zero_named_records():
    coverage, expected = _coverage("audit_plan_zero")
    assert coverage["audit plan or round charge"] == expected["group"]
    assert WRONG_OUTPUT_K2_T1 not in json.dumps(coverage, sort_keys=True)


def test_k2t1_audit_plan_group_at_one_named_record():
    coverage, expected = _coverage("audit_plan_one")
    assert coverage["audit plan or round charge"] == expected["group"]
    assert WRONG_OUTPUT_K2_T1 not in json.dumps(coverage, sort_keys=True)
    wrong = json.loads(
        (FIXTURES / "F1" / "k2t1_wrong.json").read_text(encoding="utf-8"))
    assert coverage != wrong["coverage"]


def test_k2t1_audit_plan_group_at_two_named_records():
    coverage, expected = _coverage("audit_plan_two")
    assert coverage["audit plan or round charge"] == expected["group"]
    wrong = json.loads(
        (FIXTURES / "F1" / "k2t1_wrong.json").read_text(encoding="utf-8"))
    assert coverage != wrong["coverage"]


def test_k2t1_reseat_group_no_differing_seat():
    coverage, expected = _coverage("reseat_no_differing_seat", RESEAT)
    assert coverage["reseat records"] == expected["group"]
    assert WRONG_OUTPUT_K2_T1 not in json.dumps(coverage, sort_keys=True)
    wrong = json.loads(
        (FIXTURES / "F1" / "k2t1_wrong.json").read_text(encoding="utf-8"))
    assert coverage != wrong["coverage"]


def test_k2t1_reseat_group_differing_seat_with_no_record():
    coverage, expected = _coverage("reseat_differing_no_record", RESEAT)
    assert coverage["reseat records"] == expected["group"]
    assert WRONG_OUTPUT_K2_T1 not in json.dumps(coverage, sort_keys=True)
    wrong = json.loads(
        (FIXTURES / "F1" / "k2t1_wrong.json").read_text(encoding="utf-8"))
    assert coverage != wrong["coverage"]


def test_k2t1_reseat_group_no_instance_pair_selected():
    coverage, expected = _coverage("reseat_no_instance_pair", RESEAT)
    assert coverage["reseat records"] == expected["group"]
    assert coverage["reseat records"]["needed"] == "not determined on the roster comparison"
    assert WRONG_OUTPUT_K2_T1 not in json.dumps(coverage, sort_keys=True)
    wrong = json.loads(
        (FIXTURES / "F1" / "k2t1_wrong.json").read_text(encoding="utf-8"))
    assert coverage != wrong["coverage"]


def test_k2t2_roster_record_counted_once_in_each_count():
    coverage, expected = _coverage("two_group_file")
    assert coverage["stage records"] == expected["stage_records"]
    assert coverage["claim bearing files"] == expected["claim_bearing"]
    assert WRONG_OUTPUT_K2_T2 not in json.dumps(coverage, sort_keys=True)


def test_k2t2_step_record_counted_once_in_each_count():
    coverage, expected = _coverage("two_group_file")
    assert coverage["stage records"]["read"] == expected["stage_records"]["read"]
    assert coverage["claim bearing files"]["read"] == expected["claim_bearing"]["read"]
    assert WRONG_OUTPUT_K2_T2 not in json.dumps(coverage, sort_keys=True)


def test_k2t3_unparsed_passage_carried_not_guessed():
    result, expected = run_case("F2/k2_degradation.json", "unparsed_passage")
    reading = result["reading"]
    assert reading["unparsed_passages"] == expected["unparsed_passages"]
    wrong = json.loads(
        (FIXTURES / "F2" / "k2t3_wrong.json").read_text(encoding="utf-8"))
    assert reading["counts"] != wrong["guessed_count"]


def test_k2t3_unparsed_passage_yields_not_proven_for_affected_seats():
    result, expected = run_case("F2/k2_degradation.json", "unparsed_passage")
    entries = [c for c in result["check_results"] if c["check"] == expected["check"]]
    assert entries[0]["verdict"] == "NOT PROVEN"
    wrong = json.loads(
        (FIXTURES / "F2" / "k2t3_wrong.json").read_text(encoding="utf-8"))
    assert result["reading"]["counts"] != wrong["guessed_count"]


def test_k2t3_no_guessed_count_stands_in_counts():
    result, expected = run_case("F2/k2_degradation.json", "unparsed_passage")
    assert field(result, 7)["team_counts"] == expected["team_counts"]
    wrong = json.loads(
        (FIXTURES / "F2" / "k2t3_wrong.json").read_text(encoding="utf-8"))
    assert field(result, 7)["team_counts"] != wrong["guessed_count"]["team_counts"]


def test_k2t4_no_receipt_entry_for_offered_and_unread_file():
    result, expected = run_case(COVERAGE, "receipt_and_ignored")
    receipt = field(result, 5)["receipt"]
    names = [entry["file_name"] for entry in receipt]
    assert names == expected["receipt_names"]
    assert WRONG_OUTPUT_K2_T4 not in result_text(result)


def test_k2t4_offered_and_unread_file_stands_in_ignored_inputs_only():
    result, expected = run_case(COVERAGE, "receipt_and_ignored")
    ignored = field(result, 5)["ignored_inputs"]
    assert "offered-not-read.md" in ignored
    assert ignored == expected["ignored_inputs"]
    assert WRONG_OUTPUT_K2_T4 not in result_text(result)


def test_k2t4_spawn_record_export_ignored_and_named():
    result, expected = run_case(COVERAGE, "receipt_and_ignored")
    ignored = field(result, 5)["ignored_inputs"]
    assert "spawn-record-export.json" in ignored
    assert field(result, 5)["receipt"] == expected["receipt"]
    assert WRONG_OUTPUT_K2_T4 not in result_text(result)


def test_k2t4_receipt_entry_carries_hash_form_and_byte_size():
    result, expected = run_case(COVERAGE, "receipt_and_ignored")
    receipt = field(result, 5)["receipt"]
    assert receipt == expected["receipt"]
    for entry in receipt:
        assert entry["hash"] == (
            "no hash stands, because no file bytes stand for the "
            "named file at this run")
        assert entry["byte_size"] == (
            "no byte size stands, because no file bytes stand for "
            "the named file at this run")
    assert WRONG_OUTPUT_K2_T4 not in result_text(result)


def test_k2t5_match_standing_allows_counting():
    result, expected = run_case(TABLES, "match")
    assert result["table_verification"] == expected["standing"]
    assert field(result, 12) == expected["rollup"]
    assert WRONG_OUTPUT_K2_T5 not in result_text(result)


def test_k2t5_mismatch_standing_blocks_counting_and_names_values():
    result, expected = run_case(TABLES, "mismatch")
    assert result["table_verification"] == expected["standing"]
    assert WRONG_OUTPUT_K2_T5 not in result_text(result)
    assert field(result, 7)["team_counts"] == expected["team_counts"]


def test_k2t5_single_listed_table_absent_layer1():
    result, expected = run_case(TABLES, "absent_layer1")
    assert result["table_verification"] == expected["standing"]
    assert WRONG_OUTPUT_K2_T5 not in result_text(result)


def test_k2t5_single_listed_table_absent_layer2():
    result, expected = run_case(TABLES, "absent_layer2")
    assert result["table_verification"] == expected["standing"]
    assert WRONG_OUTPUT_K2_T5 not in result_text(result)


def test_k2t5_single_listed_table_absent_mapping():
    result, expected = run_case(TABLES, "absent_mapping")
    assert result["table_verification"] == expected["standing"]
    assert WRONG_OUTPUT_K2_T5 not in result_text(result)


def test_k2t5_step_record_alone_fixture_no_base_handling():
    result, expected = run_case(TABLES, "step_record_alone")
    assert WRONG_OUTPUT_K2_T5_STEP_RECORD_ALONE not in result_text(result)
    entries = [c for c in result["check_results"]
               if c["check"] in expected["affected_checks"]]
    assert entries
    for entry in entries:
        assert entry["verdict"] == "UNVERIFIABLE"
        assert entry["missing_fact"] == expected["missing_identification"]
