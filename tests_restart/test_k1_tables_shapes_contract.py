"""Slice 1 groups K1-T1 to K1-T4: tables, manifest and contract shapes.

Loci: plan sections 4 (slice 1), 5 and 6; brief sections 5.3, 5.4,
5.4.1 and 5.4.2; brief section 5.8.1 for the F5 table derivation matrix.
Every test states its concrete wrong output in the form the Step 13
test plan charges for its group. The restart product does not exist,
so each test fails on the import of muster_restart.kernel inside
conftest.require_kernel and on no other ground.
"""

import json
from pathlib import Path

from conftest import field, load_case, require_kernel, result_text, run_case

FIXTURES = Path(__file__).parent / "fixtures"

TABLES = "F5/k1_tables.json"
SHAPES = "F1/k1_shapes.json"

# K1-T1 wrong output, fixture pair form: the three named parts of the
# counting tables carried as one merged list. The pair stands at
# fixtures/F5/k1t1_expected.json and fixtures/F5/k1t1_wrong.json.
WRONG_OUTPUT_K1_T1 = "merged_tables: one list holding the Layer 1 rows, the Layer 2 rows and the mapping rows together"

# K1-T2 wrong output, named constant form: a TeamCount figure printed
# for a unit under differing exception rows, where brief section 5.3
# and plan slice 1 require the absence stated in words.
WRONG_OUTPUT_K1_T2 = "TeamCount for unit Design team at Step 13: counted total 5"

# K1-T4 wrong output, named constant form: the contract fields printed
# out of contract order, fields 1 to 13.
WRONG_OUTPUT_K1_T4 = "12,1,2,3,4,5,6,7,8,9,10,11,13"


def test_k1t1_three_named_parts_kept_apart():
    result, expected = run_case(TABLES, "three_parts")
    tables = result["CountingTables"]
    assert list(tables["parts"].keys()) == expected["part_names"]
    assert WRONG_OUTPUT_K1_T1 not in result_text(result)
    wrong = json.loads(
        (FIXTURES / "F5" / "k1t1_wrong.json").read_text(encoding="utf-8"))
    assert tables != wrong["merged_tables"]


def test_k1t1_layer1_rows_carry_team_form_tier_and_base_size():
    result, expected = run_case(TABLES, "three_parts")
    rows = result["CountingTables"]["parts"]["layer1"]
    assert rows == expected["layer1_rows"]
    assert WRONG_OUTPUT_K1_T1 not in result_text(result)
    wrong = json.loads(
        (FIXTURES / "F5" / "k1t1_wrong.json").read_text(encoding="utf-8"))
    assert result["CountingTables"] != wrong["merged_tables"]
    for row in rows:
        assert set(row.keys()) == {"team_form", "tier", "base_size"}


def test_k1t1_mapping_rows_state_no_count():
    result, expected = run_case(TABLES, "three_parts")
    rows = result["CountingTables"]["parts"]["mapping"]
    assert rows == expected["mapping_rows"]
    assert WRONG_OUTPUT_K1_T1 not in result_text(result)
    wrong = json.loads(
        (FIXTURES / "F5" / "k1t1_wrong.json").read_text(encoding="utf-8"))
    assert result["CountingTables"] != wrong["merged_tables"]
    for row in rows:
        assert set(row.keys()) == {"step", "unit", "team_form"}


def test_k1t2_no_teamcount_figure_for_differing_unit():
    result, expected = run_case(TABLES, "differing_exception_rows")
    counts = field(result, 7)
    assert counts["team_counts"] == expected["team_counts"]
    assert counts["absence_words"] == expected["absence_words"]
    assert WRONG_OUTPUT_K1_T2 not in result_text(result)


def test_k1t2_item1_word_is_unverifiable_for_differing_unit():
    result, expected = run_case(TABLES, "differing_exception_rows")
    entries = [c for c in result["check_results"] if c["check"] == 1]
    assert len(entries) == 1
    assert entries[0]["verdict"] == expected["item1_verdict"]
    assert entries[0]["missing_fact"] == expected["item1_missing_fact"]
    assert WRONG_OUTPUT_K1_T2 not in result_text(result)


def test_k1t2_stagecount_required_count_carries_no_figure_for_unit():
    result, expected = run_case(TABLES, "differing_exception_rows")
    stage = field(result, 7)["stage_count"]
    assert stage["required_count_units"] == expected["required_count_units"]
    assert stage["absence_words"] == expected["stage_absence_words"]
    assert WRONG_OUTPUT_K1_T2 not in result_text(result)


def _shape_fields(shape_name):
    kernel = require_kernel()
    case = load_case(SHAPES, "shape_fields")
    result = kernel.compute_result(case["run_input"])
    return result["Shapes"][shape_name]["fields"], case["expected"][shape_name]


def test_k1t3_runinput_shape_complete():
    got, expected = _shape_fields("RunInput")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: RunInput shape with one field dropped "
        "or an invariant weakened")


def test_k1t3_pinnedbasemanifest_shape_complete():
    got, expected = _shape_fields("PinnedBaseManifest")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: PinnedBaseManifest shape with one field "
        "dropped or an invariant weakened")


def test_k1t3_countingtables_shape_names_three_parts():
    got, expected = _shape_fields("CountingTables")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: CountingTables shape carried as one "
        "merged list instead of three named parts")


def test_k1t3_seatentry_shape_complete():
    got, expected = _shape_fields("SeatEntry")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: SeatEntry shape with the colour field "
        "dropped")


def test_k1t3_teamcount_shape_complete():
    got, expected = _shape_fields("TeamCount")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: TeamCount shape with the property "
        "conditioned counted totals dropped")


def test_k1t3_stagecount_shape_complete():
    got, expected = _shape_fields("StageCount")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: StageCount shape with the holders "
        "figure dropped or carried as a team size")


def test_k1t3_rosterrecord_shape_complete():
    got, expected = _shape_fields("RosterRecord")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: RosterRecord shape with the board "
        "seats field dropped")


def test_k1t3_steprecordidentity_shape_complete():
    got, expected = _shape_fields("StepRecordIdentity")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: StepRecordIdentity shape with the "
        "coordinator statements count field dropped")


def test_k1t3_workproductref_shape_complete():
    got, expected = _shape_fields("WorkProductRef")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: WorkProductRef shape with the author "
        "record line location field dropped")


def test_k1t3_claimrecord_shape_complete():
    got, expected = _shape_fields("ClaimRecord")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: ClaimRecord shape with the counting "
        "kind field dropped")


def test_k1t3_checkresult_shape_complete():
    got, expected = _shape_fields("CheckResult")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: CheckResult shape with the missing "
        "fact field dropped")


def test_k1t3_limbresult_shape_complete():
    got, expected = _shape_fields("LimbResult")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: LimbResult shape with the listed "
        "limbs field dropped")


def test_k1t3_generatedstaffingstatement_shape_complete():
    got, expected = _shape_fields("GeneratedStaffingStatement")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: GeneratedStaffingStatement shape with "
        "the build union point dropped")


def test_k1t3_computedresult_shape_complete():
    got, expected = _shape_fields("ComputedResult")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: ComputedResult shape with the stage "
        "rollup word field dropped")


def test_k1t3_receiptentry_shape_complete():
    got, expected = _shape_fields("ReceiptEntry")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: ReceiptEntry shape with the byte size "
        "field dropped")


def test_k1t3_logicauditdistributionrecord_shape_complete():
    got, expected = _shape_fields("LogicAuditDistributionRecord")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: LogicAuditDistributionRecord shape "
        "with the head or named slice field dropped")


def test_k1t3_repairentry_shape_complete():
    got, expected = _shape_fields("RepairEntry")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: RepairEntry shape with the cure act "
        "field dropped")


def test_k1t3_defectreport_shape_complete():
    got, expected = _shape_fields("DefectReport")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: DefectReport shape with the defect "
        "field dropped")


def test_k1t3_recordedprecheck_shape_complete():
    got, expected = _shape_fields("RecordedPrecheck")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: RecordedPrecheck shape with the "
        "content binding field dropped")


def test_k1t3_reseatrecord_shape_complete():
    got, expected = _shape_fields("ReseatRecord")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: ReseatRecord shape with the prior "
        "holder field dropped")


def test_k1t3_planorchargerecord_shape_complete():
    got, expected = _shape_fields("PlanOrChargeRecord")
    assert got == expected, (
        "WRONG OUTPUT K1-T3: PlanOrChargeRecord shape with the "
        "colour statements field dropped")


def test_k1t4_contract_fields_1_to_13_in_contract_order():
    result, expected = run_case(TABLES, "three_parts")
    order = ",".join(result["fields"].keys())
    assert order == expected["contract_order"]
    assert order != WRONG_OUTPUT_K1_T4


def test_k1t4_field6_check_results_in_item_order_omitting_item18():
    result, expected = run_case(TABLES, "three_parts")
    order = [c["check"] for c in result["check_results"]]
    assert order == expected["check_order"]
    assert 18 not in order
    assert ",".join(str(c) for c in order) != WRONG_OUTPUT_K1_T4


def test_k1t4_field6_limb_results_grouped_checks_10_12_16():
    result, expected = run_case(TABLES, "precheck_limbs")
    limbs = result["limb_results"]
    assert [entry["check"] for entry in limbs] == expected["limb_check_order"]
    assert ",".join(str(entry["check"]) for entry in limbs) != WRONG_OUTPUT_K1_T4
