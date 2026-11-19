# Copyright: J.P. Picard aka Macro-Harder.
"""Step 16 Round 3 Fix A3 cure tests: kernel.py only.

Finding: the S16A21-05 residual (S16RA21-01 and S16RA22-01, both
Low). On real markdown roster drives through the documented CLI,
the PASS citations for checks 2, 3, 5, 8, 11 and 12 all named the
first seat of the roster, although Fix A2 recorded per check
evidence seats for exactly these checks on structured inputs.

These tests drive the documented command line, as a subprocess
running python3 -m muster_restart.run_entry, over markdown rosters
in the form in use. The first two nodes are the cure nodes: they
assert that the PASS citations name the seats the checks evidence
rests on, differing where the evidence differs. The third node is
a proof node for the stopped limb recorded in the Fix A3 paper:
it proves, on the assembly the command line itself produces, that
no selection record and no author record stands in the assembled
input, so no seat for checks 8 and 12 stands in the kernel input
on the markdown path at all.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = REPO_ROOT.parent


def _run_cli(args, cwd, pythonpath):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pythonpath)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry"] + args,
        cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=120)
    return proc


def _gate_args(stage, supplied):
    args = [
        "--runner-identity", "Fix A3 cure runner",
        "--runner-capacity", "Auditor",
        "--build", "muster-lite",
        "--stage", stage,
        "--tier", "Low",
    ]
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
    "Audit team (counted):\n"
    "- Seat Alpha: audit perspective one.\n"
    "- Seat Beta: audit perspective two.\n"
    "\n"
    "Design team (counted):\n"
    "- Seat Gamma: design perspective one.\n"
    "- Contrarian: design contrarian seat.\n"
    "- Seat Delta: design perspective two.\n"
    "\n"
    "Uncounted seats:\n"
    "- Fold-in Tracer, Step 13 (uncounted exception). "
    "Paper: records/tracer.md.\n"
)


def test_s16a21_05_markdown_roster_pass_citations_name_evidence_seats(
        tmp_path):
    roster = tmp_path / "step-13-roster.md"
    roster.write_text(MARKDOWN_ROSTER, encoding="utf-8")
    proc = _run_cli(
        _gate_args("Step 13", [(roster, "stage records")]),
        tmp_path, REPO_ROOT)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    checks = _checks(outcome)
    expected = {
        2: ("seat-2", _line_of(MARKDOWN_ROSTER, "Seat Beta")),
        3: ("seat-4", _line_of(MARKDOWN_ROSTER, "Contrarian")),
        5: ("seat-3", _line_of(MARKDOWN_ROSTER, "Seat Gamma")),
        11: ("seat-6", _line_of(MARKDOWN_ROSTER, "Fold-in Tracer")),
    }
    seen = set()
    for number, (seat_key, line) in expected.items():
        entry = checks[number]
        assert entry["verdict"] == "PASS", (
            "check %s stood at %s on the markdown roster drive"
            % (number, entry["verdict"]))
        citation = entry["citations"][0]
        assert "step-13-roster.md" in citation
        assert "line %d" % line in citation, (
            "check %s cited %s, not the line %d its evidence "
            "rests on" % (number, citation, line))
        assert "seat %s" % seat_key in citation, (
            "check %s cited %s, not the seat %s its evidence "
            "rests on" % (number, citation, seat_key))
        assert entry["citations"][1] == (
            "not applicable: linkage did not pass for this seat")
        seen.add(citation)
    assert len(seen) == len(expected), (
        "the four citations did not differ where the evidence "
        "differs: %s" % (seen,))


def test_s16a21_05_real_step15_roster_pass_citations_name_evidence_seats():
    base = "design/restart/steps/step-15"
    supplied = [
        (base + "-roster.md", "stage records"),
        (base + "-roster.md", "claim bearing files"),
        (base + "-record.md", "stage records"),
        (base + "-record.md", "claim bearing files"),
        ("design/restart/TIER-RECORD.md", "stage records"),
        (base + "-gate-record.md", "claim bearing files"),
    ]
    proc = _run_cli(_gate_args("Step 15", supplied),
                    PROJECT_ROOT, REPO_ROOT)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    checks = _checks(outcome)
    expected = {
        2: ("seat-2", 8),
        3: ("seat-8", 17),
        11: ("seat-8", 17),
    }
    for number, (seat_key, line) in expected.items():
        entry = checks[number]
        assert entry["verdict"] == "PASS"
        citation = entry["citations"][0]
        assert "step-15-roster.md" in citation
        assert "line %d" % line in citation, (
            "check %s cited %s on the real Step 15 roster drive, "
            "not the line %d its evidence rests on"
            % (number, citation, line))
        assert "seat %s" % seat_key in citation, (
            "check %s cited %s on the real Step 15 roster drive, "
            "not the seat %s its evidence rests on"
            % (number, citation, seat_key))
    for number in (6, 7, 9, 10, 13, 14, 15, 16, 17):
        entry = checks[number]
        assert entry["verdict"] == "PASS"
        citation = entry["citations"][0]
        assert "line 7" in citation and "seat seat-1" in citation, (
            "roster wide check %s moved from the first seat line "
            "the in open record states for it: %s"
            % (number, citation))


def test_s16ra21_01_check8_check12_evidence_absent_from_markdown_assembly():
    sys.path.insert(0, str(REPO_ROOT))
    from muster_restart.run_entry import _parse_roster_content
    roster = _parse_roster_content(
        MARKDOWN_ROSTER, "step-13-roster.md")
    assert roster is not None
    assert "selection" not in roster, (
        "a selection record stands assembled from the markdown "
        "roster, so the stopped limb proof fails")
    assert "board_seats" not in roster
    for seat in roster["seats"]:
        assert "carried_seat_kind" not in seat
        assert "exempt_claim" not in seat
    seats = {seat["seat_key"]: seat for seat in roster["seats"]}
    assert seats["seat-6"]["work_products"] == ["records/tracer.md"]
