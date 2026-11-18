"""Plan section 9 groups R9-T1 to R9-T5: the run contract mechanical
checks 1 to 5.

Loci: plan section 9 in full; brief section 8.3 and grill G33 for
check 5. Every test states its concrete wrong output in the form the
Step 13 test plan charges for its group. The restart product does
not exist, so each test fails on the import of
muster_restart.run_entry and on no other ground.

Surface pinned by these tests for the Step 14 build:
muster_restart.run_entry exposes the plan section 9 code table, the
CannotStartOutcome type field list, the exit code sets, and the
consumer mapping for a cannot start outcome, as data the calling
side contract states.
"""

import importlib
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _load(relative):
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


def _run_entry():
    return importlib.import_module("muster_restart.run_entry")


# R9-T1 wrong output form charged: named constant. A word outside the
# closed list standing in an outcome, verdict, rollup, header or
# marker position. The closed list stands at
# fixtures/cannot_start/closed_vocabulary.json, from plan section 9
# check 1.
WRONG_OUTPUT_R9_T1 = "SATISFACTORY"


def test_r9t1_code_table_words_drawn_from_closed_list():
    vocab = _load("cannot_start/closed_vocabulary.json")
    allowed = set(vocab["result_bearing_words"]) | {
        vocab["cannot_start_outcome_word"]}
    entry = _run_entry()
    words = entry.code_table_position_words()
    assert set(words) <= allowed, (
        "a word outside the closed list in the code table: %s"
        % sorted(set(words) - allowed))
    assert WRONG_OUTPUT_R9_T1 not in words


def test_r9t1_outcome_type_and_form_template_words_closed():
    vocab = _load("cannot_start/closed_vocabulary.json")
    allowed = set(vocab["result_bearing_words"]) | {
        vocab["cannot_start_outcome_word"], "OPEN CASE"}
    entry = _run_entry()
    words = (entry.outcome_type_position_words()
             + entry.form_template_position_words())
    assert set(words) <= allowed, (
        "a word outside the closed list in an outcome, verdict, "
        "rollup, header or marker position: %s"
        % sorted(set(words) - allowed))
    assert WRONG_OUTPUT_R9_T1 not in words


# R9-T2 wrong output form charged: assertion message on the closed
# field list. A result record field, a per check results field, a
# verdict field, a rollup field, or a field whose value is one of the
# four verdict words. The type stands at
# fixtures/cannot_start/cannot_start_outcome_type.json, from plan
# section 9 (CannotStartOutcome, DP-18).
def test_r9t2_cannot_start_outcome_field_list_is_closed():
    spec = _load("cannot_start/cannot_start_outcome_type.json")
    fields = _run_entry().cannot_start_outcome_fields()
    assert fields == spec["fields_in_order"], (
        "WRONG OUTPUT R9-T2: the CannotStartOutcome field list "
        "standing as %s instead of the closed list %s"
        % (fields, spec["fields_in_order"]))


def test_r9t2_no_verdict_valued_field_on_cannot_start_outcome():
    vocab = _load("cannot_start/closed_vocabulary.json")
    entry = _run_entry()
    fields = entry.cannot_start_outcome_fields()
    for banned in ("result record", "per check results", "verdict",
                   "rollup"):
        assert banned not in fields, (
            "WRONG OUTPUT R9-T2: a %s field standing on the "
            "CannotStartOutcome type" % banned)
    values = entry.cannot_start_outcome_field_values()
    for value in values:
        assert value not in vocab["result_bearing_words"], (
            "WRONG OUTPUT R9-T2: a field of the CannotStartOutcome "
            "type whose value is one of the four verdict words: %s"
            % value)


# R9-T3 wrong output form charged: named constant. A code standing in
# both the cannot start set, codes 1 and 2, and the set of codes
# associated with verdicts or rollups, which plan section 9 states
# as the empty set. The table stands at
# fixtures/cannot_start/exit_codes.json.
WRONG_OUTPUT_R9_T3 = "code 1 standing as a verdict code"


def test_r9t3_code_sets_are_disjoint():
    table = _load("cannot_start/exit_codes.json")
    entry = _run_entry()
    cannot_start = set(entry.cannot_start_codes())
    verdict_codes = set(entry.verdict_or_rollup_codes())
    assert cannot_start == {int(c) for c in table["cannot_start_codes"]}
    assert verdict_codes == set(table[
        "codes_associated_with_verdicts_or_rollups"])
    assert cannot_start & verdict_codes == set(), (
        "WRONG OUTPUT R9-T3: %s" % WRONG_OUTPUT_R9_T3)


def test_r9t3_no_code_stands_for_a_result_producing_run():
    entry = _run_entry()
    assert entry.codes_for_result_producing_runs() == [], (
        "WRONG OUTPUT R9-T3: a code standing for a run that "
        "produces a result record, paired with a verdict or a "
        "rollup under the DP-13 mapping")


# R9-T4 wrong output form charged: fixture pair per case. A result
# record, a verdict word or a rollup word standing for a cannot start
# case, or the call recorded as other than a call that did not run.
# The fixtures stand at fixtures/cannot_start/cannot_start_cases.json
# beside the regression set, joining neither group at brief section
# 5.8.2.
def _cannot_start_case(index):
    cases = _load("cannot_start/cannot_start_cases.json")
    case = cases["cases"][index]
    outcome = _run_entry().run_invocation(case["invocation"])
    expected = cases["expected_for_each_case"]
    assert outcome["result_record"] is expected["result_record"], (
        "WRONG OUTPUT R9-T4: a result record standing for the "
        "cannot start case: %s" % case["case"])
    assert outcome["verdict"] is expected["verdict_word"], (
        "WRONG OUTPUT R9-T4: a verdict word standing for the "
        "cannot start case: %s" % case["case"])
    assert outcome["rollup"] is expected["rollup_word"], (
        "WRONG OUTPUT R9-T4: a rollup word standing for the "
        "cannot start case: %s" % case["case"])
    assert outcome["recorded_as"] == expected["recorded_as"], (
        "WRONG OUTPUT R9-T4: the call recorded as other than a call "
        "that did not run for the case: %s" % case["case"])


def test_r9t4_runner_capacity_outside_stated_values():
    _cannot_start_case(0)


def test_r9t4_supplied_file_entry_carrying_no_input_group():
    _cannot_start_case(1)


def test_r9t4_tool_failure_before_a_result_record_stands():
    _cannot_start_case(2)


# R9-T5 wrong output form charged: named constant. A consumer mapping
# a cannot start outcome to PASS, to FAIL, or to any verdict word.
# The contract stands at
# fixtures/cannot_start/calling_side_contract.json, from plan
# section 9, grill G33 and brief section 8.3.
WRONG_OUTPUT_R9_T5 = "consumer classification: PASS"


def test_r9t5_consumer_maps_cannot_start_to_no_verdict_word():
    contract = _load("cannot_start/calling_side_contract.json")
    entry = _run_entry()
    mapping = entry.consumer_classification("CANNOT START")
    assert mapping is None, (
        "WRONG OUTPUT R9-T5: %s" % WRONG_OUTPUT_R9_T5)
    for word in contract["cannot_start_outcome_is_distinct_from"]:
        assert entry.consumer_classification("CANNOT START") != word


def test_r9t5_consumer_records_cannot_start_as_call_that_did_not_run():
    contract = _load("cannot_start/calling_side_contract.json")
    entry = _run_entry()
    recorded = entry.consumer_record("CANNOT START")
    assert recorded == contract["consumer_records_it_as"], (
        "WRONG OUTPUT R9-T5: a consumer recording a cannot start "
        "outcome as %r instead of a call that did not run" % recorded)
