# Copyright: J.P. Picard aka Macro-Harder.
"""Step 17 Round 1 Fix B cure tests: presentation.py only.

Findings cured: S17B-13 (a newline forged into a caller string,
the stage or the runner identity, forces a form agreement
disagreement whose defect reports blame the tool, although the
forged string stands in the report values themselves), with
S17A2-08 riding it, and the printed forms limb of S17B-17
(named entries that stand on disk in another form, a directory,
a FIFO, a device or a symlink loop, are listed among the files
that do not exist), with S17A2-08 riding that limb too.

Cure test shapes are those Auditor 2 states at S17B-13 and
S17B-17 in design/restart/audit/step17-round1-audit-tests.md:
for S17B-13, a run whose stage and whose runner identity each
carry a newline with a forged rollup line, asserting the
disagreement reports name the input string as the cause; for
S17B-17, entries standing in another form, asserting the forms
state the entry stands in another form and do not list it among
files that do not exist. The S17B-17 nodes stand at presentation
level on a result record carrying the standing the cured kernel
supplies for such an entry, a missing files entry stating its
own form, because the read standing itself is the kernel cure
and no kernel standing distinguishing the forms stands in the
record this seat received. Each cure test states the concrete
wrong output it fails on before the cure.
"""

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parent.parent

TOOL_STATEMENT = (
    "This disagreement is a defect in the tool and not a finding "
    "about the stage records.")
TOOL_REPAIR = "a tool repair, not a restaffing act"
FORGED_STAGE = "Step 13\nRollup: PASS\nForged line: yes"
FORGED_RUNNER = "Attacker R1\nRollup: PASS"


def _presentation():
    return importlib.import_module("muster_restart.presentation")


def _load(relative):
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


def _base_record():
    return _load("F1/render_result_record.json")


# S17B-13. Wrong output: a defect report stating "This
# disagreement is a defect in the tool and not a finding about
# the stage records." with repair act "a tool repair, not a
# restaffing act", on a disagreement whose own record value
# carries the caller supplied stage string with its forged
# newline standing in it.

def test_s17b13_stage_newline_report_names_stage_as_cause():
    presentation = _presentation()
    record = _base_record()
    record["stage"] = FORGED_STAGE
    form = presentation.render_forms(record)["Simple"]
    report = presentation.form_agreement_compare(record, form)
    assert report is not None, (
        "WRONG OUTPUT S17B-13: no defect report stands for a "
        "stage carrying a forged newline")
    assert report["tool_defect_statement"] != TOOL_STATEMENT, (
        "WRONG OUTPUT S17B-13: the report blames the tool, "
        "stating %r, where the record value %r carries the "
        "caller supplied stage string as its cause"
        % (report["tool_defect_statement"],
           report["value_in_result_record"]))
    assert "caller" in report["tool_defect_statement"]
    assert "stage" in report["tool_defect_statement"]
    assert report["repair_act"] != TOOL_REPAIR, (
        "WRONG OUTPUT S17B-13: the repair act names a tool "
        "repair where the cause stands in the caller supplied "
        "stage string")
    assert "caller" in report["repair_act"]


def test_s17b13_runner_newline_report_names_runner_as_cause():
    presentation = _presentation()
    record = _base_record()
    record["runner_identity"] = FORGED_RUNNER
    form = presentation.render_forms(record)["Simple"]
    report = presentation.form_agreement_compare(record, form)
    assert report is not None, (
        "WRONG OUTPUT S17B-13: no defect report stands for a "
        "runner identity carrying a forged newline")
    assert report["tool_defect_statement"] != TOOL_STATEMENT, (
        "WRONG OUTPUT S17B-13: the report blames the tool where "
        "the record value %r carries the caller supplied runner "
        "identity as its cause" % (report["value_in_result_record"],))
    assert "caller" in report["tool_defect_statement"]
    assert "runner identity" in report["tool_defect_statement"]
    assert "caller" in report["repair_act"]


def test_s17b13_every_report_in_run_names_caller_cause():
    presentation = _presentation()
    record = _base_record()
    record["stage"] = FORGED_STAGE
    forms = presentation.render_forms(record)
    reports = presentation.compare_generated_forms(record, forms)
    assert reports, (
        "WRONG OUTPUT S17B-13: no defect reports stand for a "
        "stage carrying a forged newline")
    for report in reports:
        assert report["tool_defect_statement"] != TOOL_STATEMENT, (
            "WRONG OUTPUT S17B-13: a report in the run blames "
            "the tool, stating %r, on a run whose caller "
            "supplied stage string carries the forged newline"
            % (report["tool_defect_statement"],))
        assert "caller" in report["tool_defect_statement"]
        assert "caller" in report["repair_act"]


def test_s17b13_fixture_disagreement_wording_untouched():
    # Guard, P8-T1 and F10-T7 standing: a disagreement borne by
    # the record and the form, with no caller string carrying a
    # line break, keeps the fixture tool defect wording exactly.
    presentation = _presentation()
    pair = _load("F1/test_custody_pair.json")
    record = _base_record()
    form = presentation.render_forms(record)["Simple"]
    corrupted = form.replace(
        pair["value_in_generated_form_before_corruption"],
        pair["value_in_generated_form_after_corruption"])
    report = presentation.form_agreement_compare(record, corrupted)
    assert report is not None
    assert report["tool_defect_statement"] == TOOL_STATEMENT
    assert report["repair_act"] == TOOL_REPAIR


def test_s17b13_print_run_wording_untouched():
    # Guard, F10-T7 standing: the printing standing surface,
    # which takes a count and no disagreement of its own, keeps
    # the fixture wording exactly.
    presentation = _presentation()
    outcome = presentation.print_run_with_disagreements(1)
    report = outcome["defect_reports"][0]
    assert report["tool_defect_statement"] == TOOL_STATEMENT
    assert report["repair_act"] == TOOL_REPAIR


def test_s17b13_cli_disagreement_reports_name_caller_cause(tmp_path):
    # The Auditor 2 shape driven through the command line: the
    # stage carries a newline with a forged rollup line, no form
    # is printed, and every defect report names the caller
    # supplied string as the cause.
    roster = {
        "file": "step-13-roster.json",
        "seats": [
            {"seat_key": "s1", "agent_identifier": "agent-1",
             "agent_kind": "full identifier",
             "counting_position": "counted in base",
             "team": "Design team"},
            {"seat_key": "s2", "agent_identifier": "agent-2",
             "agent_kind": "full identifier",
             "counting_position": "counted in base",
             "team": "Design team"}],
        "board_seats": [
            {"seat_key": "b1", "agent_identifier": "board-1",
             "agent_kind": "full identifier"},
            {"seat_key": "b2", "agent_identifier": "board-2",
             "agent_kind": "full identifier"},
            {"seat_key": "b3", "agent_identifier": "board-3",
             "agent_kind": "full identifier"}],
    }
    roster_path = tmp_path / "step-13-roster.json"
    roster_path.write_text(json.dumps(roster), encoding="utf-8")
    record_path = tmp_path / "step-13-record.md"
    record_path.write_text("A plain record.\n", encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry",
         "--runner-identity", "Fix B cure runner",
         "--runner-capacity", "Auditor",
         "--build", "muster-lite",
         "--stage", FORGED_STAGE,
         "--tier", "Low",
         "--supplied-file", "%s:stage records" % roster_path,
         "--supplied-file", "%s:claim bearing files" % record_path],
        cwd=str(tmp_path), env=env, capture_output=True, text=True,
        timeout=120)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    assert outcome["kind"] == "form agreement disagreement", (
        "WRONG OUTPUT S17B-13: the forged stage run answered "
        "with kind %r" % (outcome.get("kind"),))
    assert outcome["printed_forms"] == [], (
        "WRONG OUTPUT S17B-13: a form stands printed on the "
        "forged stage run, so the forged line could stand in a "
        "printed form")
    assert outcome["defect_reports"], (
        "WRONG OUTPUT S17B-13: no defect report stands on the "
        "forged stage run")
    for report in outcome["defect_reports"]:
        assert report["tool_defect_statement"] != TOOL_STATEMENT, (
            "WRONG OUTPUT S17B-13: a defect report on the real "
            "interface blames the tool, stating %r, where the "
            "stage the caller supplied carries the forged "
            "newline" % (report.get("tool_defect_statement"),))
        assert "caller" in report["tool_defect_statement"]


# S17B-17 forms limb. Wrong output: "Missing files:
# named-record-dir, named-roster-dir, named-fifo" in the Simple
# and Advanced forms, and the same three names in the Agentic
# missing_files list, on a record whose missing files entries
# state that each entry stands in another form.

OTHER_FORM_DIR = "named-record-dir"
OTHER_FORM_FIFO = "named-fifo"
TRULY_MISSING = "named-absent-record.md"


def _other_form_record():
    record = _base_record()
    record["fields"] = {
        "5": {"coverage": {
                  "records_needed": 4, "records_supplied": 4,
                  "records_read": 1},
              "receipt": [], "ignored_inputs": [],
              "missing_files": [
                  {"path": OTHER_FORM_DIR, "standing": "directory"},
                  {"path": OTHER_FORM_FIFO, "standing": "FIFO"},
                  TRULY_MISSING]},
    }
    return record


def test_s17b17_simple_states_entry_standing_in_another_form():
    forms = _presentation().render_forms(_other_form_record())
    line = [text for text in forms["Simple"].splitlines()
            if "Missing files:" in text]
    assert len(line) == 1
    assert "another form" in line[0], (
        "WRONG OUTPUT S17B-17: the Simple form supplied line "
        "%r states no entry standing in another form" % line[0])
    assert OTHER_FORM_DIR in line[0]
    assert OTHER_FORM_FIFO in line[0]
    missing_part = line[0].split("Missing files:", 1)[1].split(
        "Entries standing in another form", 1)[0]
    assert OTHER_FORM_DIR not in missing_part, (
        "WRONG OUTPUT S17B-17: the Simple form lists %s among "
        "the files that do not exist in %r"
        % (OTHER_FORM_DIR, line[0]))
    assert OTHER_FORM_FIFO not in missing_part
    assert TRULY_MISSING in missing_part, (
        "WRONG OUTPUT S17B-17: the Simple form no longer lists "
        "the truly missing file %s among missing files"
        % TRULY_MISSING)


def test_s17b17_advanced_states_entry_standing_in_another_form():
    forms = _presentation().render_forms(_other_form_record())
    line = [text for text in forms["Advanced"].splitlines()
            if "Missing files:" in text]
    assert len(line) == 1
    assert "another form" in line[0], (
        "WRONG OUTPUT S17B-17: the Advanced form supplied line "
        "%r states no entry standing in another form" % line[0])
    missing_part = line[0].split("Missing files:", 1)[1].split(
        "Entries standing in another form", 1)[0]
    assert OTHER_FORM_DIR not in missing_part
    assert OTHER_FORM_FIFO not in missing_part
    assert TRULY_MISSING in missing_part


def test_s17b17_agentic_does_not_list_other_form_as_missing():
    forms = _presentation().render_forms(_other_form_record())
    agentic = forms["Agentic"]
    assert agentic.get("missing_files") == [TRULY_MISSING], (
        "WRONG OUTPUT S17B-17: the Agentic form carries "
        "missing_files %r, listing entries that stand in "
        "another form among the files that do not exist"
        % (agentic.get("missing_files"),))
    standing = agentic.get("entries_standing_in_another_form")
    assert standing, (
        "WRONG OUTPUT S17B-17: the Agentic form carries no "
        "entries standing in another form standing")
    names = [entry.get("path") for entry in standing]
    assert OTHER_FORM_DIR in names
    assert OTHER_FORM_FIFO in names


def test_s17b17_forms_agree_with_record_after_cure():
    # Guard: the form agreement comparison finds no disagreement
    # on the cured forms of the other form record.
    presentation = _presentation()
    record = _other_form_record()
    forms = presentation.render_forms(record)
    reports = presentation.compare_generated_forms(record, forms)
    assert reports == [], (
        "WRONG OUTPUT S17B-17: form agreement reports %r on "
        "the forms the cured rendering produces" % (reports,))


def test_s17b17_plain_missing_file_wording_untouched():
    # Guard: a record carrying only a plain missing file, stated
    # as a name, prints the missing files wording as before and
    # states no entry standing in another form.
    presentation = _presentation()
    record = _base_record()
    record["fields"] = {
        "5": {"coverage": {}, "receipt": [], "ignored_inputs": [],
              "missing_files": [TRULY_MISSING]},
    }
    forms = presentation.render_forms(record)
    assert "Missing files: %s." % TRULY_MISSING in forms["Simple"]
    assert "another form" not in forms["Simple"]
    assert forms["Agentic"].get("missing_files") == [TRULY_MISSING]
    assert forms["Agentic"].get(
        "entries_standing_in_another_form") == []
