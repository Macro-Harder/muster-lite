"""Slice 7 groups P7-T1 to P7-T5: presentation, one result in three forms.

Loci: plan sections 8 (slice 7) and 10; brief sections 5.7.1 to 5.7.6.
Every test states its concrete wrong output in the form the Step 13
test plan charges for its group. The restart product does not exist,
so each test fails on the import of muster_restart.presentation and
on no other ground.

Presentation surface pinned by these tests for the Step 14 build:
muster_restart.presentation.render_forms(result_record) returns a
mapping with keys "Simple" and "Advanced" holding form text and
"Agentic" holding the structured field mapping of the one result.

This module is the Step 13 home of the presentation order track
under RI-15: the AC-P8 cross form test at P7-T2, carrying the
Advanced additions sequence (test plan section 7.2) and the AC-P8
value limb (test plan section 7.3). No test in this module imports,
loads, or rests on a kernel gap track fixture or module.
"""

import importlib
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def _load(relative):
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


def _presentation():
    return importlib.import_module("muster_restart.presentation")


def _forms():
    record = _load("F1/render_result_record.json")
    return _presentation().render_forms(record), record


# P7-T1 wrong output form charged: assertion message per slot, any word
# in the Simple form differing from the fixed template at that slot.
# The template stands at fixtures/F1/simple_template_slots.json,
# authored from plan section 10 and brief section 5.7.3.

def _slot_test(slot_number):
    forms, _record = _forms()
    slots = _load("F1/simple_template_slots.json")["slots"]
    slot = [s for s in slots if s["slot"] == slot_number][0]
    lines = forms["Simple"].splitlines()
    # The gate run Simple form carries 13 lines: slot five stands
    # in a precheck run only and carries no gate run line, so each
    # slot from 06 onward reads the line one index earlier than
    # its slot number, and slots 01 to 04 read at their own index.
    line_index = slot_number - 1 if slot_number < 5 else (
        slot_number - 2)
    assert lines[line_index] == slot["expected_line"], (
        "WRONG OUTPUT P7-T1: Simple form slot %d (%s) reading %r "
        "instead of the fixed template line %r"
        % (slot_number, slot["name"], lines[line_index],
           slot["expected_line"]))


def test_p7t1_slot_01_title():
    _slot_test(1)


def test_p7t1_slot_02_standing_grade_sentence():
    _slot_test(2)


def test_p7t1_slot_03_stage_tier_pinned_base_line():
    _slot_test(3)


def test_p7t1_slot_04_rollup_line():
    _slot_test(4)


def test_p7t1_slot_05_precheck_section_stands_only_in_precheck():
    forms, _record = _forms()
    slots = _load("F1/simple_template_slots.json")["slots"]
    slot = [s for s in slots if s["slot"] == 5][0]
    assert slot["expected_line"] is None
    gate_lines = forms["Simple"].splitlines()
    assert len(gate_lines) == 13, (
        "WRONG OUTPUT P7-T1: a precheck not yet run section line "
        "standing in a gate run Simple form at slot five")
    pair = _load("F4/precheck_pair.json")
    pre = _presentation().render_forms(
        dict(_load("F1/render_result_record.json"), run_kind="precheck"))
    assert pair["precheck_label"] in pre["Simple"], (
        "WRONG OUTPUT P7-T1: a precheck Simple form whose slot five "
        "section stands without the precheck label")


def test_p7t1_slot_06_build_union_state_line():
    _slot_test(6)


def test_p7t1_slot_07_counts_lines():
    _slot_test(7)


def test_p7t1_slot_08_runner_identity_and_capacity_line():
    _slot_test(8)


def test_p7t1_slot_09_standing_limits_lines():
    _slot_test(9)


def test_p7t1_slot_10_roster_match_line():
    _slot_test(10)


def test_p7t1_slot_11_missing_and_duplicate_seats_short_form():
    _slot_test(11)


def test_p7t1_slot_12_supplied_set_line_and_receipt():
    _slot_test(12)


def test_p7t1_slot_13_consequence_line():
    _slot_test(13)


def test_p7t1_slot_14_closing_line():
    _slot_test(14)


# P7-T2 wrong output form charged: named constant. One element named
# differently across forms, one element out of canonical order in the
# Advanced or Agentic form, or one verdict, count, coverage figure or
# rollup differing between forms. The fixture pair stands at
# fixtures/F1/shared_elements_expected.json (expected) and
# fixtures/F1/shared_elements_wrong.json (wrong).
WRONG_OUTPUT_P7_T2 = (
    "counts lines named as count lines in the Advanced form, with "
    "counted total 3 where the result record carries counted total 4")


def test_p7t2_element_naming_identical_across_forms():
    forms, _record = _forms()
    expected = _load("F1/shared_elements_expected.json")
    names = [e["name"] for e in expected["elements"]]
    slots = _load("F1/simple_template_slots.json")["slots"]
    simple_lines = forms["Simple"].splitlines()
    agentic_names = [e["name"] for e in forms["Agentic"]["elements"]]
    for element in expected["elements"]:
        # The canonical names stand word for word in the Advanced
        # form and as the Agentic element names. In the Simple form
        # the same element stands under its fixed template line, at
        # the slot the fixture states for it: the template lines
        # this module pins carry the element content and no element
        # name, so the name is reconciled with its template line.
        assert element["name"] in forms["Advanced"], (
            "element %s not named in the Advanced form"
            % element["name"])
        assert element["name"] in agentic_names, (
            "element %s not named in the Agentic form"
            % element["name"])
        slot = [s for s in slots if s["slot"] == element["slot"]][0]
        if slot["expected_line"] is None:
            # Slot five stands in a precheck run only: the gate run
            # Simple form carries no line for this element, and its
            # 13 lines are the other thirteen template lines.
            assert len(simple_lines) == 13, (
                "element %s standing in the gate run Simple form "
                "under a line, where its slot carries none"
                % element["name"])
        else:
            assert slot["expected_line"] in simple_lines, (
                "element %s not standing in the Simple form under "
                "its fixed template line %r"
                % (element["name"], slot["expected_line"]))
    assert names == agentic_names
    assert WRONG_OUTPUT_P7_T2 not in forms["Advanced"]


def test_p7t2_canonical_order_in_advanced_and_agentic_forms():
    forms, record = _forms()
    order = record["elements_in_canonical_order"]
    advanced_positions = [forms["Advanced"].index(name) for name in order]
    assert advanced_positions == sorted(advanced_positions), (
        "WRONG OUTPUT P7-T2: one element out of canonical order in "
        "the Advanced form")
    agentic_names = [e["name"] for e in forms["Agentic"]["elements"]]
    assert agentic_names == order, (
        "WRONG OUTPUT P7-T2: one element out of canonical order in "
        "the Agentic form")


def test_p7t2_advanced_additions_sequence():
    # The Advanced additions sequence, at its Step 13 home (test plan
    # section 7.2): the additions at brief section 5.7.4 stand in the
    # Advanced form in the canonical sequence, element by element.
    forms, _record = _forms()
    additions = _load("F1/advanced_additions.json")[
        "additions_in_canonical_sequence"]
    positions = [forms["Advanced"].index(name) for name in additions]
    assert positions == sorted(positions), (
        "WRONG OUTPUT P7-T2: the Advanced additions standing in the "
        "Advanced form in an order other than the canonical sequence "
        "at brief section 5.7.2 and plan section 10")


def test_p7t2_cross_form_values_identical():
    # The AC-P8 value limb, at its Step 13 home (test plan section
    # 7.3): no verdict, count, coverage figure or rollup differs
    # between forms, value by value, including the counts lines with
    # their printed subtraction and the slack beside every PASS.
    forms, _record = _forms()
    expected = _load("F1/shared_elements_expected.json")
    wrong = _load("F1/shared_elements_wrong.json")
    for element in expected["elements"]:
        rendered = [e for e in forms["Agentic"]["elements"]
                    if e["name"] == element["name"]]
        assert len(rendered) == 1
        for key in ("verdict", "rollup", "counted_total",
                    "entries_counted", "duplicates_removed",
                    "exempt_or_uncounted_removed", "required_count",
                    "slack", "records_needed", "records_supplied",
                    "records_read"):
            assert rendered[0][key] == element[key], (
                "WRONG OUTPUT P7-T2: %s of element %s differing "
                "between forms" % (key, element["name"]))
    wrong_counts = [e for e in wrong["elements"]
                    if e["name"] == "count lines"]
    assert len(wrong_counts) == 1
    assert all(e["counted_total"] != wrong_counts[0]["counted_total"]
               for e in forms["Agentic"]["elements"]), (
        "WRONG OUTPUT P7-T2: a form carrying the wrong fixture "
        "counted total of the counts lines element")


def test_p7t2_no_form_derived_from_another_form_text():
    forms, record = _forms()
    again = _presentation().render_forms(record)
    assert again == forms, (
        "WRONG OUTPUT P7-T2: a form rendered from the text of "
        "another form, so a second rendering of the same record "
        "differs from the first")


# P7-T3 wrong output form charged: assertion message in the group own
# failure form, stated in plan text. An element present in one form
# and absent from another that is not one of the four named elements
# fails; a named element standing in a form brief section 5.7.2 does
# not place it in fails.
def _form_specific():
    return _load("F1/form_specific_elements.json")["elements"]


def test_p7t3_per_check_detail_in_advanced_only():
    forms, _record = _forms()
    entry = [e for e in _form_specific()
             if e["name"] == "per check detail"][0]
    assert entry["forms"] == ["Advanced"]
    assert "per check detail" in forms["Advanced"]
    assert "per check detail" not in forms["Simple"], (
        "WRONG OUTPUT P7-T3: per check detail standing in the Simple "
        "form, which brief section 5.7.2 does not place it in")
    assert "per check detail" not in forms["Agentic"]["elements"], (
        "WRONG OUTPUT P7-T3: per check detail standing as an element "
        "of the Agentic form, which brief section 5.7.2 does not "
        "place it in")


def test_p7t3_pass_evidence_citations_in_advanced_and_agentic_only():
    forms, _record = _forms()
    assert "PASS evidence citations" in forms["Advanced"]
    assert "PASS evidence citations" not in forms["Simple"], (
        "WRONG OUTPUT P7-T3: PASS evidence citations standing in "
        "the Simple form, which brief section 5.7.2 does not place "
        "it in")


def test_p7t3_pass_rollup_header_in_advanced_only():
    forms, _record = _forms()
    assert "PASS rollup header" in forms["Advanced"]
    assert "PASS rollup header" not in forms["Simple"], (
        "WRONG OUTPUT P7-T3: the PASS rollup header standing in the "
        "Simple form, which brief section 5.7.2 does not place it in")


def test_p7t3_claim_disagreement_flags_in_advanced_only():
    forms, _record = _forms()
    assert "claim disagreement flags" in forms["Advanced"]
    assert "claim disagreement flags" not in forms["Simple"], (
        "WRONG OUTPUT P7-T3: claim disagreement flags standing in "
        "the Simple form, which brief section 5.7.2 does not place "
        "it in")
    agentic_names = [e["name"] for e in forms["Agentic"]["elements"]]
    assert "claim disagreement flags" not in agentic_names, (
        "WRONG OUTPUT P7-T3: claim disagreement flags standing as "
        "an element of the Agentic form, where the same differences "
        "stand as field 8 fields and not as that element")


def test_p7t3_no_unnamed_element_is_form_specific():
    forms, record = _forms()
    named = {e["name"] for e in _form_specific()}
    shared = set(record["elements_in_canonical_order"])
    agentic_names = {e["name"] for e in forms["Agentic"]["elements"]}
    extra = agentic_names - shared - named
    assert extra == set(), (
        "WRONG OUTPUT P7-T3: an element present in one form and "
        "absent from another that is not one of the four named "
        "elements: %s" % sorted(extra))


# P7-T4 wrong output form charged: fixture pair, the same result
# record rendered twice, with any element order, naming or wording
# turning on run time, disk file order, or state outside the run.
# The pair stands at fixtures/F1/render_result_record.json rendered
# once and rendered again under changed outside state.
def test_p7t4_same_record_renders_to_same_three_forms():
    forms, record = _forms()
    again = _presentation().render_forms(record)
    assert again == forms, (
        "WRONG OUTPUT P7-T4: the same result record rendered twice "
        "with an element order, naming or wording difference")


def test_p7t4_rendering_turns_on_no_state_outside_the_run():
    import os
    import time
    forms, record = _forms()
    os.environ["MUSTER_TEST_OUTSIDE_STATE"] = "changed"
    time.sleep(0)
    again = _presentation().render_forms(record)
    del os.environ["MUSTER_TEST_OUTSIDE_STATE"]
    assert again == forms, (
        "WRONG OUTPUT P7-T4: a rendering that turns on run time, on "
        "disk file order, or on state outside the run")


# P7-T5 wrong output form charged: named constant. A precheck form
# printed without its label or its consequence line, a bare precheck
# verdict in a rollup line, or a rollup word printed where the listed
# not run condition stands. Fixture source: F4 paired fixtures at
# fixtures/F4/precheck_pair.json.
WRONG_OUTPUT_P7_T5 = "Rollup: PASS"


def _precheck_forms():
    record = dict(_load("F1/render_result_record.json"),
                  run_kind="precheck")
    return _presentation().render_forms(record)


def test_p7t5_precheck_label_and_consequence_line_in_every_form():
    forms = _precheck_forms()
    pair = _load("F4/precheck_pair.json")
    for form_name in pair["forms"]:
        text = forms[form_name]
        if form_name == "Agentic":
            assert text["run_kind"] == "precheck", (
                "WRONG OUTPUT P7-T5: a precheck Agentic form without "
                "the run kind field carrying the precheck label")
            continue
        assert pair["precheck_label"] in text, (
            "WRONG OUTPUT P7-T5: a precheck form printed without "
            "its label")
        assert pair["precheck_consequence_line"] in text, (
            "WRONG OUTPUT P7-T5: a precheck form printed without "
            "its consequence line")


def test_p7t5_no_bare_precheck_verdict_in_a_rollup_line():
    forms = _precheck_forms()
    rollup_lines = [line for line in forms["Simple"].splitlines()
                    if line.startswith("Rollup:")]
    assert len(rollup_lines) == 1
    assert rollup_lines[0] != WRONG_OUTPUT_P7_T5, (
        "WRONG OUTPUT P7-T5: a bare precheck verdict in a rollup "
        "line, reading %r" % rollup_lines[0])


def test_p7t5_no_rollup_word_where_listed_not_run_condition_stands():
    pair = _load("F4/precheck_pair.json")
    record = dict(_load("F1/render_result_record.json"),
                  run_kind="precheck", rollup=None,
                  listed_not_run_condition=pair["listed_not_run_condition"])
    forms = _presentation().render_forms(record)
    assert pair["rollup_line_under_listed_not_run"] in forms["Simple"], (
        "WRONG OUTPUT P7-T5: a rollup word printed where the listed "
        "not run condition stands")
    for word in ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE"):
        assert ("Rollup: " + word) not in forms["Simple"]
