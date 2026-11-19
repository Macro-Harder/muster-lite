# Copyright: J.P. Picard aka Macro-Harder.
"""Step 16 Round 1 Fix B cure tests: presentation.py only.

Findings cured: S16U-04 (coverage figures the result record
carries stand in all three forms), S16U-05 with S16A2-03 riding
it (no Agentic element copies the first check verdict; on a
NOT PROVEN rollup no element prints PASS and the form agrees
with the rollup), S16U-09 (no gate evidence consequence line
stands where no rollup stands).

Each cure test states the concrete wrong output it fails on, in
the Step 13 form. Guard tests pin the standing behaviours the
cures must not move: the flat coverage form, the PASS rollup
element standing, the gate consequence line where a rollup does
stand under plan section 9 kind 1, and the not stated coverage
standing where the record carries no coverage figure at all.
"""

import importlib
import json


def _presentation():
    return importlib.import_module("muster_restart.presentation")


GATE_CONSEQUENCE = (
    "Consequence: the rollup may be cited as gate evidence for "
    "this stage only.")


def _per_group_record():
    """A contract form record in the INV-02 shape.

    Field 5 coverage stands per group, as the kernel assembles
    it: stage records needed 3, supplied 3, read 3; claim
    bearing files needed 2, supplied 2, read 2. No totals stand
    in the record. Check 1 stands PASS, check 4 stands
    NOT PROVEN, and field 12 stands NOT PROVEN.
    """
    return {
        "fields": {
            "2": {"run_kind": "gate run",
                  "runner_identity": "runner-a",
                  "runner_capacity": "Auditor"},
            "3": {"stage_judged": "Step 15", "tier_applied": "Low"},
            "4": {"pinned_base": "base tables v1",
                  "base_position": "identified"},
            "5": {"coverage": {
                      "stage records": {
                          "needed": 3, "supplied": 3, "read": 3},
                      "claim bearing files": {
                          "needed": 2, "supplied": 2, "read": 2}},
                  "receipt": [], "ignored_inputs": []},
            "12": "NOT PROVEN",
        },
        "check_results": [
            {"check": 1, "verdict": "PASS",
             "verdict_position": "PASS"},
            {"check": 4, "verdict": "NOT PROVEN",
             "verdict_position": "NOT PROVEN",
             "missing_fact": "the board record for the stage"},
        ],
    }


def _open_case_record():
    """A contract form record in the INV-10 shape: open case."""
    record = _per_group_record()
    record["fields"]["4"] = {"pinned_base": "words alone",
                             "base_position": "OPEN CASE"}
    record["fields"]["12"] = (
        "Rollup not stated. This run meets an open case, named "
        "here, and the single result for that case stands open.")
    for entry in record["check_results"]:
        entry["verdict"] = "OPEN CASE"
        entry["verdict_position"] = "OPEN CASE"
    return record


def _supplied_line(text):
    lines = [line for line in text.splitlines()
             if "Supplied set:" in line]
    assert len(lines) == 1
    return lines[0]


# S16U-04. Wrong output: "Supplied set: not stated records
# needed, not stated supplied, not stated read" in the Simple
# and Advanced forms, and records needed, records supplied and
# records read standing null on every Agentic element, on a
# record whose field 5 carries per group coverage figures.

def test_s16u04_simple_prints_carried_coverage():
    forms = _presentation().render_forms(_per_group_record())
    line = _supplied_line(forms["Simple"])
    assert "not stated records needed" not in line, (
        "WRONG OUTPUT S16U-04: Simple form supplied line %r on a "
        "record carrying per group coverage figures" % line)
    assert "5 records needed, 5 supplied, 5 read" in line, (
        "WRONG OUTPUT S16U-04: Simple form supplied line %r "
        "carrying no total of the figures the record carries"
        % line)
    assert "stage records: 3 records needed, 3 supplied, 3 read" \
        in line, (
            "WRONG OUTPUT S16U-04: Simple form supplied line %r "
            "carrying no stage records figure the record carries"
            % line)
    assert ("claim bearing files: 2 records needed, 2 supplied, "
            "2 read") in line, (
                "WRONG OUTPUT S16U-04: Simple form supplied line "
                "%r carrying no claim bearing files figure the "
                "record carries" % line)


def test_s16u04_advanced_prints_carried_coverage():
    forms = _presentation().render_forms(_per_group_record())
    line = _supplied_line(forms["Advanced"])
    assert "not stated records needed" not in line, (
        "WRONG OUTPUT S16U-04: Advanced form supplied line %r on "
        "a record carrying per group coverage figures" % line)
    assert "5 records needed, 5 supplied, 5 read" in line
    assert "stage records: 3 records needed, 3 supplied, 3 read" \
        in line
    assert ("claim bearing files: 2 records needed, 2 supplied, "
            "2 read") in line


def test_s16u04_agentic_carries_carried_coverage():
    forms = _presentation().render_forms(_per_group_record())
    for element in forms["Agentic"]["elements"]:
        assert element["records_needed"] == 5, (
            "WRONG OUTPUT S16U-04: Agentic element %s carrying "
            "records needed %r where the record carries per "
            "group figures totalling 5"
            % (element["name"], element["records_needed"]))
        assert element["records_supplied"] == 5
        assert element["records_read"] == 5


def test_s16u04_flat_coverage_form_unchanged():
    # Guard: a record carrying flat totals renders them as
    # before, with no per group breakdown invented.
    record = _per_group_record()
    record["fields"]["5"]["coverage"] = {
        "records_needed": 2, "records_supplied": 2,
        "records_read": 2}
    forms = _presentation().render_forms(record)
    line = _supplied_line(forms["Simple"])
    assert "2 records needed, 2 supplied, 2 read" in line
    assert "stage records:" not in line
    for element in forms["Agentic"]["elements"]:
        assert element["records_needed"] == 2
        assert element["records_supplied"] == 2
        assert element["records_read"] == 2


def test_s16u04_no_coverage_in_record_stays_not_stated():
    # Guard: where the record carries no coverage figure, no
    # figure is invented; the not stated standing stands.
    record = _per_group_record()
    record["fields"]["5"]["coverage"] = {}
    forms = _presentation().render_forms(record)
    line = _supplied_line(forms["Simple"])
    assert "not stated records needed" in line
    for element in forms["Agentic"]["elements"]:
        assert element["records_needed"] is None


# S16U-05, S16A2-03 riding. Wrong output: every Agentic element
# carrying verdict PASS on a NOT PROVEN run, the verdict of the
# first check copied onto elements that are not checks.

def test_s16u05_no_element_pass_on_not_proven_rollup():
    forms = _presentation().render_forms(_per_group_record())
    assert forms["Agentic"]["rollup"] == "NOT PROVEN"
    for element in forms["Agentic"]["elements"]:
        assert element["verdict"] != "PASS", (
            "WRONG OUTPUT S16U-05: Agentic element %s carrying "
            "verdict PASS on a NOT PROVEN rollup whose first "
            "check stands PASS and whose check 4 stands "
            "NOT PROVEN" % element["name"])
        assert element["verdict"] == "NOT PROVEN", (
            "WRONG OUTPUT S16U-05: Agentic element %s carrying "
            "verdict %r, not the rollup word the form as a "
            "whole carries" % (element["name"], element["verdict"]))


def test_s16u05_per_check_results_carry_each_own_verdict():
    forms = _presentation().render_forms(_per_group_record())
    per_check = {entry["check"]: entry["verdict"]
                 for entry in forms["Agentic"]["per_check_results"]}
    assert per_check == {"check 1": "PASS",
                         "check 4": "NOT PROVEN"}, (
        "WRONG OUTPUT S16U-05: per check results %r, where "
        "check 1 carries its own PASS and check 4 carries its "
        "own NOT PROVEN" % per_check)


def test_s16u05_elements_pass_only_on_pass_rollup():
    # Guard: on a PASS rollup, where every check the record
    # carries stands PASS, the elements carry PASS, as the
    # pinned shared elements fixture states.
    record = _per_group_record()
    record["fields"]["12"] = "PASS"
    record["check_results"] = [
        {"check": 1, "verdict": "PASS", "verdict_position": "PASS"}]
    forms = _presentation().render_forms(record)
    for element in forms["Agentic"]["elements"]:
        assert element["verdict"] == "PASS"
        assert element["rollup"] == "PASS"


def test_s16u05_first_check_fail_does_not_colour_elements():
    # A FAIL first check with a NOT PROVEN rollup: no element
    # copies the first check word either.
    record = _per_group_record()
    record["check_results"] = [
        {"check": 1, "verdict": "FAIL", "verdict_position": "FAIL"},
        {"check": 4, "verdict": "NOT PROVEN",
         "verdict_position": "NOT PROVEN"}]
    forms = _presentation().render_forms(record)
    for element in forms["Agentic"]["elements"]:
        assert element["verdict"] == "NOT PROVEN", (
            "WRONG OUTPUT S16U-05: Agentic element %s carrying "
            "verdict %r copied from the first check"
            % (element["name"], element["verdict"]))


# S16U-09. Wrong output: "Consequence: the rollup may be cited
# as gate evidence for this stage only." standing in a form
# whose rollup line states that no rollup stands.

def test_s16u09_open_case_carries_no_gate_consequence():
    forms = _presentation().render_forms(_open_case_record())
    assert GATE_CONSEQUENCE not in forms["Simple"], (
        "WRONG OUTPUT S16U-09: the gate evidence consequence "
        "line standing in the Simple form of an open case run "
        "where no rollup stands")
    assert GATE_CONSEQUENCE not in forms["Advanced"]
    assert GATE_CONSEQUENCE not in json.dumps(forms["Agentic"])
    simple_consequence = [line for line in
                          forms["Simple"].splitlines()
                          if line.startswith("Consequence:")]
    assert len(simple_consequence) == 1
    assert "no rollup stands" in simple_consequence[0], (
        "WRONG OUTPUT S16U-09: open case consequence line %r "
        "stating nothing about the absent rollup"
        % simple_consequence[0])


def test_s16u09_no_rollup_record_carries_no_gate_consequence():
    # A record carrying no rollup at all, over no records: the
    # no records case in its no rollup form.
    record = _per_group_record()
    del record["fields"]["12"]
    record["fields"]["5"]["coverage"] = {}
    record["check_results"] = []
    forms = _presentation().render_forms(record)
    assert GATE_CONSEQUENCE not in forms["Simple"], (
        "WRONG OUTPUT S16U-09: the gate evidence consequence "
        "line standing where no rollup stands")
    assert GATE_CONSEQUENCE not in forms["Advanced"]
    assert GATE_CONSEQUENCE not in json.dumps(forms["Agentic"])


def test_s16u09_gate_consequence_where_rollup_stands():
    # Guard, plan section 9 kind 1: a completed gate run whose
    # rollup stands may cite the rollup as gate evidence, and
    # the consequence line states exactly that, no more.
    forms = _presentation().render_forms(_per_group_record())
    assert GATE_CONSEQUENCE in forms["Simple"]
    assert GATE_CONSEQUENCE in forms["Advanced"]


def test_s16_fixb_forms_agree_with_record_after_cures():
    # Guard: the form agreement comparison finds no disagreement
    # on the cured forms of either cure record.
    presentation = _presentation()
    for record in (_per_group_record(), _open_case_record()):
        forms = presentation.render_forms(record)
        reports = presentation.compare_generated_forms(record, forms)
        assert reports == [], (
            "WRONG OUTPUT S16 FIX B: form agreement reports %r on "
            "the forms the cured rendering produces" % reports)
