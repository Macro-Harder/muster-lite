# Copyright: J.P. Picard aka Macro-Harder.
"""Step 17 Round 1 Fix C cure tests: run_entry.py only.

Each node drives the shipped command line end to end, as a
subprocess running python3 -m muster_restart.run_entry, over
record fixtures written into a temporary directory. The nodes pin
the Fix C cures of the Step 17 Round 1 fix register: items 3, 4,
6, 7, 9, 10, 11, 12 and 16, in the cure test shapes Auditor 2
stated. Every node failed on the defective behaviour before its
cure and passes after it, except where a node states a standing
shape the cure preserves.
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


def _pass_roster(path):
    return _write_roster_json(
        path,
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")],
        board=[_board("board-1", "agent-b1"),
               _board("board-2", "agent-b2"),
               _board("board-3", "agent-b3")])


def _run_cli(args, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry"] + args,
        cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=120)


def _args(supplied, capacity="Auditor", tier="Low", run_kind=None,
          stage="Step 13"):
    args = [
        "--runner-identity", "Fix C Round 1 cure runner",
        "--runner-capacity", capacity,
        "--build", "muster-lite",
        "--stage", stage,
        "--tier", tier,
    ]
    if run_kind is not None:
        args += ["--run-kind", run_kind]
    for path, group in supplied:
        args += ["--supplied-file", "%s:%s" % (path, group)]
    return args


def _checks(outcome):
    record = outcome["result_record"]
    return {entry["check"]: entry for entry in record["check_results"]}


def _assert_cannot_start(proc, needle=None, kind="invocation",
                         exit_code=1):
    assert proc.returncode == exit_code, (
        "expected exit %s, got %s: %s"
        % (exit_code, proc.returncode, proc.stdout[:400]))
    outcome = json.loads(proc.stdout)
    assert outcome["kind"] == "cannot start run", outcome["kind"]
    assert outcome["result_record"] is None
    assert outcome["rollup"] is None
    cannot = outcome["cannot_start_outcome"]
    assert cannot is not None
    assert cannot["kind"] == kind, cannot
    assert cannot["outcome word"] == "CANNOT START"
    if needle is not None:
        assert needle in cannot["cause"], (
            "the cause does not name %s: %s" % (needle, cannot["cause"]))
    return cannot


# Item 3, S17B-03: a coordinator capacity without the precheck
# kind produces no completed gate run carrying a citable rollup.

def test_s17b03_coordinator_without_precheck_kind_cannot_start(
        tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    proc = _run_cli(_args(
        [(roster, "stage records")],
        capacity="coordinator as precheck"), tmp_path)
    cannot = _assert_cannot_start(proc, "coordinator")
    assert "precheck" in cannot["cause"]


def test_s17b03_coordinator_with_precheck_kind_still_prechecks(
        tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    proc = _run_cli(_args(
        [(roster, "stage records")],
        capacity="coordinator as precheck", run_kind="precheck"),
        tmp_path)
    assert proc.returncode == 0, proc.stdout[:400]
    outcome = json.loads(proc.stdout)
    assert outcome["kind"].startswith("precheck run")
    assert outcome["rollup"] is None


# Item 4, S17B-04: every supplied roster is read and assembled;
# the verdict does not turn on entry order.

def test_s17b04_two_rosters_verdict_does_not_turn_on_order(tmp_path):
    first = _write_roster_json(
        tmp_path / "step-13-roster-a.json",
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")])
    second = _write_roster_json(
        tmp_path / "step-13-roster-b.json",
        [_seat("seat-1", "agent-3")])
    forward = json.loads(_run_cli(_args(
        [(first, "stage records"), (second, "stage records")]),
        tmp_path).stdout)
    reverse = json.loads(_run_cli(_args(
        [(second, "stage records"), (first, "stage records")]),
        tmp_path).stdout)
    for outcome in (forward, reverse):
        assert outcome["kind"] == "completed gate run"
        stage = outcome["result_record"]["fields"]["7"]["stage_count"]
        assert stage["entries_counted"] == 3, (
            "a supplied roster was set aside: %s" % stage)
    assert forward["rollup"] == reverse["rollup"], (
        "the verdict turned on entry order: %s against %s"
        % (forward["rollup"], reverse["rollup"]))


# Item 6, S17B-06: the invocation path reads the named claim
# bearing files' content and assembles the claim records from
# that content, in the structured RunInput form the kernel
# surface states, so checks 16 and 17 answer on claims read.

def test_s17b06_claim_bearing_content_moves_checks_16_and_17(
        tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    plain = tmp_path / "step-13-claims.json"
    plain.write_text("{}", encoding="utf-8")
    contra = tmp_path / "step-13-claims-contra.json"
    contra.write_text(json.dumps({
        "claim_kind": "cohort counts",
        "direction": "claim point with no generated point",
        "claim_standing": "claim standing read and contradicted",
        "frozen_roster": [
            {"seat_key": "seat-1", "agent_identifier": "agent-1",
             "team": "Design team"}],
        "gate_roster": [
            {"seat_key": "seat-1", "agent_identifier": "agent-1",
             "team": "Build team"}],
    }), encoding="utf-8")
    plain_out = json.loads(_run_cli(_args(
        [(roster, "stage records"), (plain, "claim bearing files")]),
        tmp_path).stdout)
    contra_out = json.loads(_run_cli(_args(
        [(roster, "stage records"), (contra, "claim bearing files")]),
        tmp_path).stdout)
    plain_checks = _checks(plain_out)
    contra_checks = _checks(contra_out)
    assert plain_checks[16]["verdict"] == "PASS", plain_checks[16]
    assert plain_checks[17]["verdict"] == "PASS", plain_checks[17]
    assert contra_checks[16]["verdict"] != "PASS", (
        "check 16 answered on no claim read: %s" % contra_checks[16])
    assert contra_checks[17]["verdict"] == "FAIL", (
        "check 17 answered on no claim read: %s" % contra_checks[17])


# Item 7, S17B-07: an input defect on the command line ends at a
# cannot start outcome naming the input and the defect in plain
# words, carrying no internal error text and no result record.

def test_s17b07_unreadable_named_file_cannot_start_plain(tmp_path):
    if os.geteuid() == 0:
        import pytest
        pytest.skip("mode 000 is readable for the root user")
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    record = tmp_path / "step-13-record.md"
    record.write_text("a record\n", encoding="utf-8")
    record.chmod(0)
    try:
        proc = _run_cli(_args(
            [(roster, "stage records"), (record, "stage records")]),
            tmp_path)
    finally:
        record.chmod(0o644)
    cannot = _assert_cannot_start(proc, str(record))
    assert "Errno" not in cannot["cause"]
    assert "Permission denied" not in cannot["cause"]


def test_s17b07_seat_entries_of_wrong_type_cannot_start_plain(
        tmp_path):
    roster = tmp_path / "step-13-roster.json"
    roster.write_text(json.dumps(
        {"file": roster.name, "seats": ["seat as a string", 7]}),
        encoding="utf-8")
    proc = _run_cli(_args([(roster, "stage records")]), tmp_path)
    cannot = _assert_cannot_start(proc, roster.name)
    assert "has no attribute" not in cannot["cause"]


def test_s17b07_table_content_of_wrong_type_cannot_start_plain(
        tmp_path):
    import shutil
    scratch = tmp_path / "unit"
    shutil.copytree(REPO_ROOT / "muster_restart",
                    scratch / "muster_restart")
    layer1 = scratch / "muster_restart" / "layer1.json"
    rows = json.loads(layer1.read_text(encoding="utf-8"))
    rows[0]["base_size"] = "two"
    layer1.write_text(json.dumps(rows), encoding="utf-8")
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(scratch)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry"]
        + _args([(roster, "stage records")]),
        cwd=str(tmp_path), env=env, capture_output=True, text=True,
        timeout=120)
    cannot = _assert_cannot_start(proc, "layer1.json")
    assert "base_size" in cannot["cause"]


# Item 9, S17B-09: an invocation missing the run input fields
# ends at a cannot start outcome of kind invocation at exit 1.

def test_s17b09_no_arguments_cannot_start(tmp_path):
    _assert_cannot_start(_run_cli([], tmp_path))


def test_s17b09_stage_only_cannot_start(tmp_path):
    _assert_cannot_start(_run_cli(["--stage", "Step 13"], tmp_path))


def test_s17b09_empty_string_fields_cannot_start(tmp_path):
    proc = _run_cli([
        "--runner-identity", "", "--runner-capacity", "Auditor",
        "--build", "", "--stage", "", "--tier", ""], tmp_path)
    _assert_cannot_start(proc)


def test_s17b09_supplied_file_with_empty_path_cannot_start(tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    args = _args([(roster, "stage records")])
    args += ["--supplied-file", ":stage records"]
    _assert_cannot_start(_run_cli(args, tmp_path))


# Item 10, S17B-10: a repeated option name is refused, naming
# the repeated name.

def test_s17b10_repeated_stage_cannot_start(tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    args = _args([(roster, "stage records")]) + [
        "--stage", "Step 99"]
    _assert_cannot_start(_run_cli(args, tmp_path), "--stage")


def test_s17b10_repeated_tier_cannot_start(tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    args = _args([(roster, "stage records")]) + ["--tier", "Plaid"]
    _assert_cannot_start(_run_cli(args, tmp_path), "--tier")


# Item 11, S17B-11: a run kind outside the stated values is
# refused naming the value; the precheck kind stands only for
# the coordinator capacity.

def test_s17b11_bogus_run_kind_cannot_start(tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    proc = _run_cli(_args(
        [(roster, "stage records")], run_kind="bogus"), tmp_path)
    _assert_cannot_start(proc, "bogus")


def test_s17b11_precheck_kind_with_auditor_capacity_refused(
        tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    proc = _run_cli(_args(
        [(roster, "stage records")], run_kind="precheck"), tmp_path)
    cannot = _assert_cannot_start(proc, "precheck")
    assert "coordinator" in cannot["cause"]


def test_s17b11_empty_pinned_base_cannot_start(tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    args = _args([(roster, "stage records")]) + ["--pinned-base", ""]
    _assert_cannot_start(_run_cli(args, tmp_path))


# Item 12, S17B-12: a tier outside the stated list and a supplied
# file group outside the closed group list are each refused,
# naming the value.

def test_s17b12_tier_outside_the_stated_list_cannot_start(tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    for tier in ("Bogus", "low", "Low "):
        proc = _run_cli(_args(
            [(roster, "stage records")], tier=tier), tmp_path)
        _assert_cannot_start(proc, tier)


def test_s17b12_group_outside_the_closed_list_cannot_start(tmp_path):
    roster = _pass_roster(tmp_path / "step-13-roster.json")
    for group in ("stage records:extra", "bogus group"):
        proc = _run_cli(_args([(roster, group)]), tmp_path)
        _assert_cannot_start(proc, group)


# Item 16, S17B-16: a roster file that stands and was read,
# stating a team heading and no seats, stands as a stated empty
# roster, distinct from a roster absent, and receives the same
# verdict word as the JSON empty seats form of the same fact.

def test_s17b16_empty_roster_same_verdict_in_both_syntaxes(tmp_path):
    markdown = tmp_path / "step-13-roster.md"
    markdown.write_text(
        "# Step 13 roster\n\nDesign team (counted):\n",
        encoding="utf-8")
    structured = _write_roster_json(
        tmp_path / "step-13-roster.json", [])
    md_out = json.loads(_run_cli(_args(
        [(markdown, "stage records")]), tmp_path).stdout)
    json_out = json.loads(_run_cli(_args(
        [(structured, "stage records")]), tmp_path).stdout)
    md_checks = _checks(md_out)
    json_checks = _checks(json_out)
    assert json_checks[1]["verdict"] == "FAIL", json_checks[1]
    assert md_checks[1]["verdict"] == json_checks[1]["verdict"], (
        "the same empty roster fact answered %s in markdown and "
        "%s in JSON" % (md_checks[1]["verdict"],
                        json_checks[1]["verdict"]))
    assert md_out["rollup"] == json_out["rollup"]
