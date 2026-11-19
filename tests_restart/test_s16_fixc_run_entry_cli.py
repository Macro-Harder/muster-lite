# Copyright: J.P. Picard aka Macro-Harder.
"""Step 16 Round 1 Fix C cure tests: the command line path.

These tests drive the shipped command line end to end, as a
subprocess running python3 -m muster_restart.run_entry, over record
fixtures written into a temporary directory. They pin two cures:

S16U-01 (with S16A1-01 and S16A2-01 riding it): the command line
reads the named records' content and assembles the kernel input
from that content, in the structured RunInput form the kernel
surface states (brief section 5.4 shapes 4 and 5, the form the
test harness uses), and, for a roster in the markdown form in use
(brief grill G6), from the seat lines that roster carries. The
verdicts and counts must rest on the content read: the same
invocation over a roster naming three counted seats counts three,
and over a roster naming one counted seat counts one and earns
the FAIL that content earns against the pinned Layer 1 figure.

S16U-06 parser limb (with S16A2-05 riding it): an invocation
carrying a name or a positional the contract at plan section 9
does not state is refused with a cannot start outcome of kind
invocation and exit code 1, naming the cause; no argument is
silently dropped and no verdict issues on discarded evidence.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _seat(key, agent, team="Design team"):
    return {
        "seat_key": key,
        "agent_identifier": agent,
        "agent_kind": "full identifier",
        "counting_position": "counted in base",
        "team": team,
    }


def _board(key, agent):
    return {
        "seat_key": key,
        "agent_identifier": agent,
        "agent_kind": "full identifier",
    }


def _write_roster_json(path, seats, board=None):
    roster = {"file": path.name, "seats": seats}
    if board is not None:
        roster["board_seats"] = board
    path.write_text(json.dumps(roster), encoding="utf-8")
    return path


def _run_cli(args, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry"] + args,
        cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=120)
    return proc


def _gate_args(roster_path, group="stage records"):
    return [
        "--runner-identity", "Fix C cure runner",
        "--runner-capacity", "Auditor",
        "--build", "muster-lite",
        "--stage", "Step 13",
        "--tier", "Low",
        "--supplied-file", "%s:%s" % (roster_path, group),
    ]


def _checks(outcome):
    record = outcome["result_record"]
    return {entry["check"]: entry for entry in record["check_results"]}


def _stage_count(outcome):
    return outcome["result_record"]["fields"]["7"]["stage_count"]


def _team_counts(outcome):
    return outcome["result_record"]["fields"]["7"]["team_counts"]


def test_cli_counts_seats_named_in_structured_roster_content(tmp_path):
    roster = _write_roster_json(
        tmp_path / "step-13-roster.json",
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2"),
         _seat("seat-3", "agent-3")],
        board=[_board("board-1", "agent-b1"),
               _board("board-2", "agent-b2"),
               _board("board-3", "agent-b3")])
    proc = _run_cli(_gate_args(roster), tmp_path)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    assert outcome["kind"] == "completed gate run"
    stage = _stage_count(outcome)
    assert stage["entries_counted"] == 3, (
        "WRONG OUTPUT S16U-01: a roster naming three seats counted "
        "%s entries" % stage["entries_counted"])
    assert stage["counted_total"] == 3
    design = [t for t in _team_counts(outcome)
              if t["team"] == "Design team"]
    assert design and design[0]["counted_total"] == 3, (
        "WRONG OUTPUT S16U-01: the Design team count does not rest "
        "on the roster content: %s" % (_team_counts(outcome),))
    checks = _checks(outcome)
    assert checks[1]["verdict"] == "PASS"
    assert checks[4]["verdict"] == "PASS", (
        "WRONG OUTPUT S16A1-01: the board seats the content names "
        "did not reach check 4: %s" % checks[4])
    assert outcome["rollup"] == "PASS", (
        "WRONG OUTPUT S16A1-01: PASS stands unreachable as a rollup "
        "through the command line: %s" % outcome["rollup"])


def test_cli_one_seat_roster_earns_the_fail_its_content_earns(tmp_path):
    roster = _write_roster_json(
        tmp_path / "step-13-roster.json",
        [_seat("seat-1", "agent-1")])
    proc = _run_cli(_gate_args(roster), tmp_path)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    stage = _stage_count(outcome)
    assert stage["entries_counted"] == 1
    assert stage["counted_total"] == 1
    checks = _checks(outcome)
    assert checks[1]["verdict"] == "FAIL", (
        "WRONG OUTPUT S16U-01: one counted seat against the pinned "
        "figure of 2 did not earn FAIL on check 1: %s"
        % checks[1]["verdict"])
    assert checks[1]["evidence"].get("observed_count") == 1
    assert outcome["rollup"] == "FAIL", (
        "WRONG OUTPUT S16A1-01: FAIL stands unreachable as a rollup "
        "through the command line: %s" % outcome["rollup"])


def test_cli_verdict_follows_the_content_when_the_content_changes(
        tmp_path):
    roster = tmp_path / "step-13-roster.json"
    _write_roster_json(
        roster,
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2"),
         _seat("seat-3", "agent-3")],
        board=[_board("board-1", "agent-b1"),
               _board("board-2", "agent-b2"),
               _board("board-3", "agent-b3")])
    first = json.loads(_run_cli(_gate_args(roster), tmp_path).stdout)
    _write_roster_json(roster, [_seat("seat-1", "agent-1")])
    second = json.loads(_run_cli(_gate_args(roster), tmp_path).stdout)
    assert _stage_count(first)["counted_total"] == 3
    assert _stage_count(second)["counted_total"] == 1
    assert first["rollup"] == "PASS"
    assert second["rollup"] == "FAIL", (
        "WRONG OUTPUT S16U-01: changing the roster content did not "
        "change the verdict, so the verdict does not rest on the "
        "content read")


def test_cli_counts_seat_lines_of_a_markdown_roster_in_use(tmp_path):
    roster = tmp_path / "step-13-roster.md"
    roster.write_text(
        "# Step 13 roster: Design. Muster-lite build, restart run\n"
        "\n"
        "Design team (counted):\n"
        "- Seat Alpha: design perspective one.\n"
        "- Seat Beta: design perspective two.\n"
        "\n"
        "Money: 0 dollars external. Tokens: NOT RECORDED.\n",
        encoding="utf-8")
    proc = _run_cli(_gate_args(roster), tmp_path)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    stage = _stage_count(outcome)
    assert stage["entries_counted"] == 2, (
        "WRONG OUTPUT S16U-01: a markdown roster naming two seat "
        "lines counted %s entries" % stage["entries_counted"])
    assert stage["counted_total"] == 2
    design = [t for t in _team_counts(outcome)
              if t["team"] == "Design team"]
    assert design and design[0]["counted_total"] == 2
    checks = _checks(outcome)
    assert checks[2]["verdict"] == "NOT PROVEN", (
        "WRONG OUTPUT S16U-01: seat lines stating no full "
        "identifier must degrade under grill G6, not count as "
        "proven distinct holders: %s" % checks[2]["verdict"])


def _assert_cannot_start(proc, needle):
    assert proc.returncode == 1, (
        "WRONG OUTPUT S16U-06: exit code %s for an invocation the "
        "contract does not state" % proc.returncode)
    outcome = json.loads(proc.stdout)
    assert outcome["kind"] == "cannot start run"
    assert outcome["result_record"] is None
    assert outcome["rollup"] is None
    cannot = outcome["cannot_start_outcome"]
    assert cannot is not None
    assert cannot["kind"] == "invocation"
    assert cannot["outcome word"] == "CANNOT START"
    assert needle in cannot["cause"], (
        "WRONG OUTPUT S16U-06: the cause does not name %s: %s"
        % (needle, cannot["cause"]))
    assert outcome["recorded_as"] == "a call that did not run"


def test_cli_refuses_the_readme_call_shape_names(tmp_path):
    roster = tmp_path / "step-13-roster.md"
    roster.write_text("# roster\n", encoding="utf-8")
    proc = _run_cli([
        "--stage", "Step 13", "--runner", "A. Auditor",
        "--capacity", "Auditor", str(roster)], tmp_path)
    _assert_cannot_start(proc, "--runner")


def test_cli_refuses_a_positional_record_argument(tmp_path):
    roster = tmp_path / "step-13-roster.md"
    roster.write_text("# roster\n", encoding="utf-8")
    args = _gate_args(roster) + [str(roster)]
    proc = _run_cli(args, tmp_path)
    _assert_cannot_start(proc, str(roster))


def test_cli_refuses_an_unknown_option_name(tmp_path):
    args = _gate_args(tmp_path / "step-13-roster.json") + [
        "--digest", "yes"]
    proc = _run_cli(args, tmp_path)
    _assert_cannot_start(proc, "--digest")


def test_cli_refuses_a_known_option_with_no_value(tmp_path):
    proc = _run_cli(["--runner-identity", "Fix C cure runner",
                     "--stage"], tmp_path)
    _assert_cannot_start(proc, "--stage")
