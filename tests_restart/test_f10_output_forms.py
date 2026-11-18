"""Plan section 10 groups F10-T1 to F10-T7: the output forms.

Loci: plan section 10 in full; brief sections 5.4.2, 5.7.4, 5.7.8,
5.7.9 and 5.7.10. Every test states its concrete wrong output in the
form the Step 13 test plan charges for its group. The restart
product does not exist, so each test fails on the import of
muster_restart.presentation and on no other ground.

Group F10-T1 carries the completeness limb of the AC-P8 cross form
test whose sequence limb stands at group P7-T2 in
test_p7_rendering.py, over the same closed additions list at brief
section 5.7.4.
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


# F10-T1 wrong output form charged: named constant. An Advanced form
# missing one required element, or carrying one element beyond the
# closed additions list at brief section 5.7.4.
WRONG_OUTPUT_F10_T1 = (
    "Advanced form carrying the addition named scoring summary, "
    "beyond the closed additions list at brief section 5.7.4")


def test_f10t1_advanced_form_carries_every_required_element():
    forms, _record = _forms()
    additions = _load("F1/advanced_additions.json")
    for name in additions["additions_in_canonical_sequence"]:
        assert name in forms["Advanced"], (
            "WRONG OUTPUT F10-T1: an Advanced form missing the "
            "required element %s" % name)
    shared = _load("F1/shared_elements_expected.json")
    for element in shared["elements"]:
        assert element["name"] in forms["Advanced"], (
            "WRONG OUTPUT F10-T1: an Advanced form missing the "
            "shared element %s, which grill G26 requires in substance"
            % element["name"])


def test_f10t1_advanced_form_carries_no_element_beyond_closed_list():
    forms, record = _forms()
    additions = _load("F1/advanced_additions.json")
    allowed = additions["additions_in_canonical_sequence"]
    carried = _presentation().advanced_form_additions(record)
    assert carried == allowed, (
        "WRONG OUTPUT F10-T1: %s" % WRONG_OUTPUT_F10_T1)
    assert "scoring summary" not in forms["Advanced"]


# F10-T2 wrong output form charged: fixture pair. A PASS check in the
# Advanced or Agentic form carrying one citation location instead of
# both, or the second location as a location instead of in words
# where linkage did not pass or did not apply; and a citation standing
# in the Simple form beyond its template. The pair stands in
# fixtures/F1/pass_citations.json, from plan section 5 shape 8.
def test_f10t2_pass_check_carries_both_citation_locations_advanced():
    forms, _record = _forms()
    fixture = _load("F1/pass_citations.json")["pass_check"]
    assert fixture["first_location"] in forms["Advanced"]
    assert fixture["second_location_where_linkage_passed"] in (
        forms["Advanced"]), (
        "WRONG OUTPUT F10-T2: a PASS check in the Advanced form "
        "carrying one citation location instead of both")


def test_f10t2_second_location_in_words_where_linkage_did_not_pass():
    record = _load("F1/render_result_record.json")
    record["checks"][0]["author_record_line_location"] = None
    forms = _presentation().render_forms(record)
    fixture = _load("F1/pass_citations.json")["pass_check"]
    words = fixture[
        "second_location_in_words_where_linkage_did_not_pass_or_apply"]
    assert words in forms["Advanced"], (
        "WRONG OUTPUT F10-T2: the second citation location standing "
        "as a location instead of in words where linkage did not "
        "pass")
    assert words in str(forms["Agentic"]), (
        "WRONG OUTPUT F10-T2: the second citation location standing "
        "as a location instead of in words in the Agentic form "
        "where linkage did not pass")


def test_f10t2_no_citation_in_simple_form_beyond_its_template():
    forms, _record = _forms()
    fixture = _load("F1/pass_citations.json")["pass_check"]
    assert fixture["second_location_where_linkage_passed"] not in (
        forms["Simple"]), (
        "WRONG OUTPUT F10-T2: a citation standing in the Simple "
        "form beyond its template")


# F10-T3 wrong output form charged: named constant. A figured header
# naming a slack value standing nowhere else in its report, a figured
# header over a result with no TeamCount, or a header standing where
# the rollup is not PASS. Fixture source: brief section 5.7.8 at
# fixtures/F1/pass_rollup_headers.json.
WRONG_OUTPUT_F10_T3 = (
    "PASS rollup header: smallest slack 2, Audit team, standing "
    "over a report whose only printed slack figure is 1")


def test_f10t3_figured_header_uses_slack_printed_in_same_report():
    forms, _record = _forms()
    fixture = _load("F1/pass_rollup_headers.json")["figured_header"]
    slack = fixture["slack_figures_in_the_same_report"]["Audit team"]
    header_lines = [line for line in forms["Advanced"].splitlines()
                    if "smallest slack" in line]
    assert len(header_lines) == 1
    assert str(slack) in header_lines[0], (
        "WRONG OUTPUT F10-T3: %s" % WRONG_OUTPUT_F10_T3)
    assert "Audit team" in header_lines[0]


def test_f10t3_words_only_header_where_no_teamcount_stands():
    record = _load("F1/render_result_record.json")
    record["counts"] = None
    forms = _presentation().render_forms(record)
    fixture = _load("F1/pass_rollup_headers.json")["words_only_header"]
    assert fixture["text"] in forms["Advanced"], (
        "WRONG OUTPUT F10-T3: a figured header over a result with "
        "no TeamCount, instead of the words only header at brief "
        "section 5.7.8")


def test_f10t3_no_header_where_rollup_is_not_pass():
    record = dict(_load("F1/render_result_record.json"), rollup="FAIL")
    forms = _presentation().render_forms(record)
    assert "smallest slack" not in forms["Advanced"], (
        "WRONG OUTPUT F10-T3: a PASS rollup header standing where "
        "the rollup is not PASS")
    fixture = _load("F1/pass_rollup_headers.json")["words_only_header"]
    assert fixture["text"] not in forms["Advanced"]


# F10-T4 wrong output form charged: assertion message per guard, in
# the form plan section 10 states for the P12 guard tests.
def test_f10t4_guard_citation_in_simple_form_beyond_template_fails():
    forms, _record = _forms()
    fixture = _load("F1/pass_citations.json")["pass_check"]
    standing = (fixture["second_location_where_linkage_passed"]
                in forms["Simple"])
    assert not standing, (
        "WRONG OUTPUT F10-T4: a citation standing in the Simple "
        "form beyond its template fails this guard")


def test_f10t4_guard_header_figure_nowhere_else_in_report_fails():
    forms, _record = _forms()
    body = [line for line in forms["Advanced"].splitlines()
            if "smallest slack" not in line]
    header = [line for line in forms["Advanced"].splitlines()
              if "smallest slack" in line]
    assert len(header) == 1
    figures = [token for token in header[0].split() if token.isdigit()]
    assert figures and all(
        any(figure in line for line in body) for figure in figures), (
        "WRONG OUTPUT F10-T4: a header figure standing nowhere "
        "else in its report fails this guard")


def test_f10t4_guard_figured_header_over_no_teamcount_fails():
    record = _load("F1/render_result_record.json")
    record["counts"] = None
    forms = _presentation().render_forms(record)
    assert "smallest slack" not in forms["Advanced"], (
        "WRONG OUTPUT F10-T4: a figured header over a result with "
        "no TeamCount fails this guard")


# F10-T5 wrong output form charged: fixture pair. A read file missing
# from the receipt or out of its stated order, an offered and unread
# file standing in the receipt instead of the ignored inputs list
# only, or the G-47 bound printed in other than its full form. The
# pair stands at fixtures/F1/receipt_files.json, from brief section
# 5.7.10.
def test_f10t5_every_read_file_in_receipt_in_stated_order():
    forms, _record = _forms()
    fixture = _load("F1/receipt_files.json")
    receipt = forms["Agentic"]["receipt"]
    paths = [entry["path"] for entry in receipt]
    expected = [entry["path"]
                for entry in fixture["read_files_in_receipt_order"]]
    assert paths == expected, (
        "WRONG OUTPUT F10-T5: a read file missing from the receipt "
        "or out of its stated order: %s" % paths)


def test_f10t5_unread_file_in_ignored_inputs_list_only():
    forms, _record = _forms()
    fixture = _load("F1/receipt_files.json")
    unread = fixture["offered_and_unread_files"][0]["path"]
    receipt_paths = [entry["path"]
                     for entry in forms["Agentic"]["receipt"]]
    assert unread not in receipt_paths, (
        "WRONG OUTPUT F10-T5: an offered and unread file standing "
        "in the receipt instead of the ignored inputs list only")
    assert unread in forms["Agentic"]["ignored_inputs"]


def test_f10t5_g47_bound_printed_in_its_full_form():
    forms, _record = _forms()
    fixture = _load("F1/receipt_files.json")
    assert fixture["g47_bound_in_full"] in forms["Advanced"], (
        "WRONG OUTPUT F10-T5: the G-47 bound printed in other than "
        "its full form at brief section 5.7.10")


# F10-T6 wrong output form charged: named constant. A word outside
# the four standing as a verdict in any form, header, marker, or
# defect report defect field, or the OPEN CASE state standing
# outside its brief section 5.4.2 positions.
WRONG_OUTPUT_F10_T6 = "SATISFACTORY standing as a verdict"


def test_f10t6_no_word_outside_the_four_as_verdict_in_any_form():
    forms, _record = _forms()
    fixture = _load("F1/open_case_positions.json")
    for element in forms["Agentic"]["elements"]:
        assert element["verdict"] in fixture["verdict_words"], (
            "WRONG OUTPUT F10-T6: %s" % WRONG_OUTPUT_F10_T6)
    assert "SATISFACTORY" not in forms["Simple"]
    assert "SATISFACTORY" not in forms["Advanced"]


def test_f10t6_no_word_outside_the_four_in_header_marker_or_defect_field():
    forms, _record = _forms()
    fixture = _load("F1/defect_report_form.json")["expected"]
    assert fixture["defect_field_word"] == "UNVERIFIABLE"
    headers = [line for line in forms["Advanced"].splitlines()
               if "header" in line.lower()]
    for line in headers:
        assert "SATISFACTORY" not in line, (
            "WRONG OUTPUT F10-T6: a word outside the four standing "
            "in a header or marker position")


def test_f10t6_open_case_state_only_in_brief_542_positions():
    record = dict(_load("F1/render_result_record.json"),
                  open_case=True)
    forms = _presentation().render_forms(record)
    fixture = _load("F1/open_case_positions.json")
    assert forms["Agentic"]["field_12"] == fixture[
        "field_12_in_open_case_run_not_precheck"], (
        "WRONG OUTPUT F10-T6: the OPEN CASE state standing outside "
        "its brief section 5.4.2 positions, or a rollup word "
        "standing at field 12 in an open case run")
    for position in forms["Agentic"]["open_case_positions"]:
        assert position in fixture["allowed_positions"], (
            "WRONG OUTPUT F10-T6: the OPEN CASE state standing in "
            "the position %s, outside its brief section 5.4.2 "
            "positions" % position)


# F10-T7 wrong output form charged: fixture pair. A form printed on a
# disagreement, one report covering two disagreements, the defect
# word standing outside the defect field, or the tool defect
# statement missing its plain words that the disagreement is a defect
# in the tool and not a stage finding. The pair stands at
# fixtures/F1/defect_report_form.json, expected and wrong, from brief
# section 5.7.9.
def test_f10t7_no_form_printed_and_one_report_per_disagreement():
    fixture = _load("F1/defect_report_form.json")
    presentation = _presentation()
    outcome = presentation.print_run_with_disagreements(2)
    assert outcome["printed_forms"] == [], (
        "WRONG OUTPUT F10-T7: a form printed on a disagreement")
    assert len(outcome["defect_reports"]) == 2, (
        "WRONG OUTPUT F10-T7: one report covering two "
        "disagreements, as the wrong fixture at fixtures/F1/"
        "defect_report_form.json stands")
    assert fixture["wrong"]["one_report_covering_two_disagreements"]


def test_f10t7_defect_word_in_defect_field_only():
    fixture = _load("F1/defect_report_form.json")["expected"]
    presentation = _presentation()
    outcome = presentation.print_run_with_disagreements(1)
    report = outcome["defect_reports"][0]
    assert report["defect_field"] == fixture["defect_field_word"]
    assert "rollup" not in report, (
        "WRONG OUTPUT F10-T7: the defect word standing outside the "
        "defect field, in a rollup position")


def test_f10t7_tool_defect_statement_in_plain_words():
    fixture = _load("F1/defect_report_form.json")["expected"]
    presentation = _presentation()
    outcome = presentation.print_run_with_disagreements(1)
    report = outcome["defect_reports"][0]
    assert report["tool_defect_statement"] == fixture[
        "tool_defect_statement"], (
        "WRONG OUTPUT F10-T7: the tool defect statement missing "
        "its plain words that the disagreement is a defect in the "
        "tool and not a stage finding")
    assert report["repair_act"] == fixture["repair_act"]
