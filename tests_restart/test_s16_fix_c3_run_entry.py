# Copyright: J.P. Picard aka Macro-Harder.
"""Step 16 Round 3 Fix C3 cure tests: run_entry.py only.

Finding: the remaining limb of the S16A21-05 citation residual
(S16RA21-01 and S16RA22-01). Fix A3 cured checks 2, 3 and 11 in
the kernel and proved in the open that checks 8 and 12 cannot be
cured in the kernel on the command line path: the markdown roster
assembly in run_entry.py returns only file and seats, so the
selection record that check 8's evidence rests on and the author
record and work products that check 12's evidence rests on never
stand in the kernel input.

These tests drive the documented command line, as a subprocess
running python3 -m muster_restart.run_entry, over a markdown
roster of the form in use, the form the Step 15 roster stands in:
wave headings, bullet seat lines naming each seat before its
first colon, and a Paper statement naming the seat's work product
where the roster states one.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_cli(args, cwd, pythonpath):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pythonpath)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry"] + args,
        cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=120)
    return proc


def _gate_args(stage, supplied, run_kind=None, capacity="Auditor"):
    args = [
        "--runner-identity", "Fix C3 cure runner",
        "--runner-capacity", capacity,
        "--build", "muster-lite",
        "--stage", stage,
        "--tier", "Low",
    ]
    if run_kind is not None:
        args += ["--run-kind", run_kind]
    for path, group in supplied:
        args += ["--supplied-file", "%s:%s" % (path, group)]
    return args


def _checks(outcome):
    record = outcome["result_record"]
    return {entry["check"]: entry for entry in record["check_results"]}


def _line_of(text, needle):
    for number, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return number
    raise AssertionError("no line states %s" % needle)


MARKDOWN_ROSTER = (
    "# Step 13 roster: Design. Muster-lite build, restart run\n"
    "\n"
    "Step 13 of 23 (Design), Tier Low, grade L2, restart run. "
    "Base seats at Low: Audit 3 and Fix 3 per round, step total 6.\n"
    "\n"
    "## Wave 1 (opening wave)\n"
    "\n"
    "- Coordinator: Step 13 coordinator, first tour. "
    "Not counted in the step total.\n"
    "- Records Clerk, Step 13: rolling collection from the first "
    "wave start. Paper: records/step-13-clerk-notes.md, sittings "
    "appended as papers land.\n"
    "\n"
    "## Wave 2 (Round 1 audit wave)\n"
    "\n"
    "- Auditor 1, Step 13 Round 1, product correctness lens. "
    "Paper: records/step-13-audit-product.md.\n"
    "- Auditor 2, Step 13 Round 1, tests and verdicts lens. "
    "Paper: records/step-13-audit-tests.md.\n"
    "- Auditor 3, Step 13 Round 1, records lens. "
    "Paper: records/step-13-audit-records.md.\n"
)


def test_s16ra21_01_selection_and_author_record_absent_from_assembly(
        tmp_path):
    # Proof node for the stopped limbs recorded in the Fix C3
    # paper. The combined citation node this module first carried
    # asserted that the PASS citations for checks 8 and 12 name
    # seat-3 (the first Auditor seat, filling the Audit 3 count
    # the roster's opening prose states) and seat-2 (the Records
    # Clerk, the first seat stating a work product). It failed
    # before the cure and failed after it, on check 8 first:
    # check 8 cited step-13-roster.md line 7, seat seat-1, not
    # line 12. No selection record and no author record stands
    # assembled from a markdown roster, because no line form for
    # either record stands in the brief, the plan or the rosters
    # in use, so no seat for check 8 or for the gate form of
    # check 12 stands in the kernel input on this path. This
    # node pins that standing fact of the assembly.
    sys.path.insert(0, str(REPO_ROOT))
    from muster_restart.run_entry import (
        _assemble_content, _parse_roster_content)
    assembled = _parse_roster_content(
        MARKDOWN_ROSTER, "step-13-roster.md")
    assert assembled is not None
    assert "selection" not in assembled, (
        "a selection record stands assembled from the markdown "
        "roster, so the stopped limb proof fails")
    roster = tmp_path / "step-13-roster.md"
    roster.write_text(MARKDOWN_ROSTER, encoding="utf-8")
    invocation = {"supplied_files": [
        {"path": str(roster), "group": "stage records"}]}
    _assemble_content(invocation)
    assert "author_record" not in invocation, (
        "an author record stands assembled from the markdown "
        "roster, so the stopped limb proof fails")
    proc = _run_cli(
        _gate_args("Step 13", [(roster, "stage records")]),
        tmp_path, REPO_ROOT)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    checks = _checks(outcome)
    for number in (8, 12):
        entry = checks[number]
        assert entry["verdict"] == "PASS"
        citation = entry["citations"][0]
        assert "line %d" % _line_of(
            MARKDOWN_ROSTER, "Coordinator") in citation
        assert "seat seat-1" in citation, (
            "check %s moved from the first seat standing the "
            "stopped limb record states for it: %s"
            % (number, citation))


def test_s16ra21_01_work_products_assembled_from_paper_statements(
        tmp_path):
    roster = tmp_path / "step-13-roster.md"
    roster.write_text(MARKDOWN_ROSTER, encoding="utf-8")
    sys.path.insert(0, str(REPO_ROOT))
    from muster_restart.run_entry import _parse_roster_content
    assembled = _parse_roster_content(
        MARKDOWN_ROSTER, "step-13-roster.md")
    assert assembled is not None
    seats = {seat["seat_key"]: seat for seat in assembled["seats"]}
    assert "work_products" not in seats["seat-1"], (
        "a seat stating no Paper statement carries work products")
    assert seats["seat-2"]["work_products"] == [
        "records/step-13-clerk-notes.md"], (
        "the Records Clerk work product the roster states does "
        "not stand assembled: %s" % (seats["seat-2"],))
    assert seats["seat-3"]["work_products"] == [
        "records/step-13-audit-product.md"]
    proc = _run_cli(
        _gate_args("Step 13", [(roster, "stage records")],
                   run_kind="precheck",
                   capacity="coordinator as precheck"),
        tmp_path, REPO_ROOT)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    limbs = outcome["result_record"]["fields"]["6"]["limb_results"]
    linkage = [entry for entry in limbs if entry["check"] == 12]
    assert linkage, "no check 12 limb result stands in the precheck"
    entry = linkage[0]
    assert entry["verdict"] == "PASS", (
        "the check 12 linkage limb stood at %s on a roster stating "
        "work products" % entry["verdict"])
    assert entry["seat_or_team"] == "seat-2", (
        "the check 12 linkage limb rests on %s, not on seat-2, "
        "the first seat the roster states a work product for"
        % entry["seat_or_team"])
    assert entry["evidence"]["observed"] == (
        "records/step-13-clerk-notes.md")
