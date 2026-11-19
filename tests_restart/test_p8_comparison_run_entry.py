"""Slice 8 groups P8-T1 to P8-T4: form agreement comparison, defect
report, and run entry.

Loci: plan sections 8 (slice 8) and 9; brief sections 5.1, 5.4
(shape 16) and 5.7.9. Every test states its concrete wrong output in
the form the Step 13 test plan charges for its group. The restart
product does not exist, so each test fails on the import of
muster_restart.presentation or muster_restart.run_entry and on no
other ground.

Surfaces pinned by these tests for the Step 14 build:
muster_restart.presentation.form_agreement_compare(result_record,
generated_form) returns a DefectReport mapping or None, and
muster_restart.run_entry.run_invocation(invocation) returns the
calling side outcome mapping of plan section 9.
"""

import importlib
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _load(relative):
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


def _presentation():
    return importlib.import_module("muster_restart.presentation")


def _run_entry():
    return importlib.import_module("muster_restart.run_entry")


# P8-T1 wrong output form charged: fixture pair in test custody only.
# The pair stands at fixtures/F1/test_custody_pair.json: the fixture
# result record and a generated form the harness corrupts between
# generation and comparison, against the same pair uncorrupted
# returning a DefectReport, or a corrupted pair returning no
# DefectReport, a clean rollup, or the defect word in a rollup
# position. No live run corruption test and no same code second
# rendering comparison stands in this group.
def test_p8t1_corrupted_pair_returns_defect_report():
    pair = _load("F1/test_custody_pair.json")
    record = _load("F1/render_result_record.json")
    presentation = _presentation()
    form = presentation.render_forms(record)["Simple"]
    corrupted = form.replace(
        pair["value_in_generated_form_before_corruption"],
        pair["value_in_generated_form_after_corruption"])
    assert corrupted != form
    report = presentation.form_agreement_compare(record, corrupted)
    assert report is not None, (
        "WRONG OUTPUT P8-T1: a corrupted pair returning no "
        "DefectReport")
    assert report["element"] == pair["generated_form_element"]
    assert report["value_in_result_record"] == (
        pair["value_in_result_record"])
    assert report["value_in_generated_form"] == (
        pair["value_in_generated_form_after_corruption"])
    assert report["location_in_result_record"] == (
        pair["location_in_result_record"])
    assert report["location_in_generated_form"] == (
        pair["location_in_generated_form"])


def test_p8t1_uncorrupted_pair_returns_no_defect():
    record = _load("F1/render_result_record.json")
    presentation = _presentation()
    form = presentation.render_forms(record)["Simple"]
    report = presentation.form_agreement_compare(record, form)
    assert report is None, (
        "WRONG OUTPUT P8-T1: the same pair uncorrupted returning a "
        "DefectReport")


def test_p8t1_defect_word_in_defect_field_only_no_clean_rollup():
    pair = _load("F1/test_custody_pair.json")
    record = _load("F1/render_result_record.json")
    presentation = _presentation()
    form = presentation.render_forms(record)["Simple"]
    corrupted = form.replace(
        pair["value_in_generated_form_before_corruption"],
        pair["value_in_generated_form_after_corruption"])
    report = presentation.form_agreement_compare(record, corrupted)
    assert report["defect_field"] == "UNVERIFIABLE", (
        "WRONG OUTPUT P8-T1: a corrupted pair returning the defect "
        "word in a rollup position, or no defect word in the defect "
        "field")
    assert "rollup" not in report, (
        "WRONG OUTPUT P8-T1: a corrupted pair returning a clean "
        "rollup")
    statement = _load("F1/defect_report_form.json")["expected"][
        "tool_defect_statement"]
    assert report["tool_defect_statement"] == statement


# P8-T2 wrong output form charged: named constant. A form printed in
# a run where the comparison found a disagreement, or the comparison
# stopping at the first disagreement. Fixture source: F1 rendering
# fixtures at fixtures/F1/comparison_disagreements.json.
WRONG_OUTPUT_P8_T2 = (
    "Simple form printed in full in a run where the comparison "
    "found a disagreement on the counts lines element")


def test_p8t2_one_disagreement_one_form_one_report_no_form_printed():
    cases = _load("F1/comparison_disagreements.json")["cases"]
    case = cases[0]
    outcome = _run_entry().run_comparison_case(case)
    assert len(outcome["defect_reports"]) == case["expected_reports"]
    assert outcome["printed_forms"] == [], (
        "WRONG OUTPUT P8-T2: %s" % WRONG_OUTPUT_P8_T2)


def test_p8t2_one_element_in_each_of_two_forms_two_reports():
    cases = _load("F1/comparison_disagreements.json")["cases"]
    case = cases[1]
    outcome = _run_entry().run_comparison_case(case)
    assert len(outcome["defect_reports"]) == case["expected_reports"]
    forms_seen = [r["form"] for r in outcome["defect_reports"]]
    assert forms_seen == ["Simple", "Advanced"]
    assert outcome["printed_forms"] == [], (
        "WRONG OUTPUT P8-T2: %s" % WRONG_OUTPUT_P8_T2)


def test_p8t2_comparison_continues_after_first_disagreement():
    cases = _load("F1/comparison_disagreements.json")["cases"]
    case = cases[1]
    outcome = _run_entry().run_comparison_case(case)
    assert outcome["comparison_completed_all_forms"] is True, (
        "WRONG OUTPUT P8-T2: the comparison stopping at the first "
        "disagreement")


# P8-T3 wrong output form charged: assertion message in the group own
# failure form, stated in plan text. A third call path to the
# comparison unit stands as a build defect under the module split.
# The only call paths are the presentation module call in a run and
# the test harness call in test custody (brief section 5.1, plan
# section 8 slice 8).
def test_p8t3_only_two_call_paths_to_comparison_unit():
    presentation = _presentation()
    paths = presentation.comparison_call_paths()
    assert paths == ["presentation module in a run",
                     "test harness in test custody"], (
        "WRONG OUTPUT P8-T3: a third call path to the comparison "
        "unit stands in the shipped code: %s" % (paths,))


def test_p8t3_kernel_module_takes_no_part_in_comparison():
    kernel = importlib.import_module("muster_restart.kernel")
    assert not hasattr(kernel, "form_agreement_compare"), (
        "WRONG OUTPUT P8-T3: a call path to the comparison unit "
        "standing in the kernel module, a third call path under the "
        "module split")


# P8-T4 wrong output form charged: fixture pair per outcome kind at
# plan section 9, each kind returned in a form belonging to another
# kind. The kinds stand at fixtures/cannot_start/outcome_kinds.json
# and the cannot start fixtures at
# fixtures/cannot_start/cannot_start_cases.json. Kind selection
# stands apart from the invocation contract in the form the product
# states it, at run_entry.harness_kind_invocation: the run entry
# itself reads no kind selection key.
def _kind_outcome(kind_number):
    kinds = _load("cannot_start/outcome_kinds.json")["kinds"]
    kind = [k for k in kinds if k["kind"] == kind_number][0]
    outcome = _run_entry().harness_kind_invocation(
        {"outcome_kind": kind_number})
    return outcome, kind


def test_p8t4_kind1_completed_gate_run_in_its_own_form():
    outcome, kind = _kind_outcome(1)
    assert outcome["kind"] == kind["name"]
    assert outcome["result_record"] is not None
    assert outcome["cannot_start_outcome"] is None, (
        "WRONG OUTPUT P8-T4: a completed gate run returned in the "
        "cannot start form")


def test_p8t4_kind2_open_case_run_in_its_own_form():
    outcome, kind = _kind_outcome(2)
    assert outcome["kind"] == kind["name"]
    assert outcome["result_record"] is not None
    assert outcome["rollup"] is None, (
        "WRONG OUTPUT P8-T4: an open case run returned carrying a "
        "rollup word, in the completed gate run form")


def test_p8t4_kind3_precheck_run_in_its_own_form():
    outcome, kind = _kind_outcome(3)
    assert outcome["kind"] == kind["name"]
    assert outcome["rollup"] is None
    assert outcome["label"] is not None, (
        "WRONG OUTPUT P8-T4: a precheck run returned without its "
        "label, in the completed gate run form")


def test_p8t4_kind4_disagreement_run_in_its_own_form():
    outcome, kind = _kind_outcome(4)
    assert outcome["kind"] == kind["name"]
    assert outcome["printed_forms"] == []
    assert len(outcome["defect_reports"]) >= 1, (
        "WRONG OUTPUT P8-T4: a form agreement disagreement returned "
        "with printed forms and no defect report, in the completed "
        "gate run form")


def test_p8t4_kind5_cannot_start_run_in_its_own_form():
    outcome, kind = _kind_outcome(5)
    assert outcome["kind"] == kind["name"]
    assert outcome["result_record"] is None
    assert outcome["cannot_start_outcome"] is not None, (
        "WRONG OUTPUT P8-T4: a cannot start run returned carrying a "
        "result record, in a result bearing form")
    cases = _load("cannot_start/cannot_start_cases.json")
    for case in cases["cases"]:
        one = _run_entry().run_invocation(case["invocation"])
        assert one["result_record"] is None
        assert one["recorded_as"] == cases["expected_for_each_case"][
            "recorded_as"]
