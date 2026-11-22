# Copyright: J.P. Picard aka Macro-Harder.
"""Audit fix P1-3: the standing of a named file is stated at the
filesystem boundary, where the command line assembles the
invocation.

The audit's prescribed kernel fix, any named path that is not a
file returns absent, breaks the pinned brief F1 and F3 fixture
contract: a structured kernel input states its supplied set, and
entries naming files not on disk are counted as the input states
them. Kernel visible entries from the command line and from
fixtures are identical in shape, so no kernel only change can
give both outcomes. Captain JP ruled on 2026-11-21 that the
standing is stated at the boundary instead: when the command
line assembles the invocation, each supplied entry is marked
file_stands from Path.is_file(), so a named file that does not
stand on disk enters the kernel as absent under the existing
entry contract, and a structured input assembled elsewhere
keeps the standing it states.

These tests pin both halves. Through the command line, a named
file missing on disk counts as absent: it stands in the missing
files list, and its group counts supplied 0 and read 0. A named
file present on disk keeps its standing. At the kernel surface,
a fixture shaped input carrying no file_stands mark keeps its
stated standing unchanged.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

import importlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

README_PATHS = [
    "records/step-14-roster.md",
    "records/step-14-record.md",
    "records/TIER-RECORD.md",
    "records/step-14-gate-record.md",
]


def _run_cli(tmp_path, stage, supplied):
    args = [
        sys.executable, "-m", "muster_restart.run_entry",
        "--runner-identity", "A. Auditor",
        "--runner-capacity", "Auditor",
        "--build", "muster-lite",
        "--stage", stage,
        "--tier", "Low",
    ]
    for entry in supplied:
        args += ["--supplied-file", entry]
    env = {"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"}
    result = subprocess.run(
        args, cwd=str(tmp_path), capture_output=True, text=True,
        env=env, timeout=120)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _field5(outcome):
    return outcome["result_record"]["fields"]["5"]


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


def test_p13_readme_shape_missing_records_count_as_absent(tmp_path):
    supplied = [
        "records/step-14-roster.md:stage records",
        "records/step-14-roster.md:claim bearing files",
        "records/step-14-record.md:stage records",
        "records/step-14-record.md:claim bearing files",
        "records/TIER-RECORD.md:stage records",
        "records/step-14-gate-record.md:claim bearing files",
    ]
    outcome = _run_cli(tmp_path, "Step 14", supplied)
    field5 = _field5(outcome)
    assert sorted(field5["missing_files"]) == sorted(README_PATHS), (
        "the four records paths of the README example do not stand "
        "in the missing files list: %s" % (field5["missing_files"],))
    for group in ("stage records", "claim bearing files"):
        counts = field5["coverage"][group]
        assert counts["supplied"] == 0, (
            "group %s counts supplied %s for files that do not "
            "stand on disk" % (group, counts["supplied"]))
        assert counts["read"] == 0, (
            "group %s counts read %s for files that do not stand "
            "on disk" % (group, counts["read"]))
        assert field5["supplied_set"][group] == [], (
            "group %s supplied set names files that do not stand "
            "on disk: %s" % (group, field5["supplied_set"][group]))


def test_p13_cli_missing_named_file_counts_as_absent(tmp_path):
    missing = "records/step-13-record.md"
    outcome = _run_cli(
        tmp_path, "Step 13", [missing + ":stage records"])
    field5 = _field5(outcome)
    assert field5["missing_files"] == [missing], (
        "a named file missing on disk does not stand in the "
        "missing files list: %s" % (field5["missing_files"],))
    counts = field5["coverage"]["stage records"]
    assert counts == {"needed": 1, "supplied": 0, "read": 0}, (
        "a named file missing on disk is counted as supplied or "
        "read: %s" % (counts,))


def test_p13_cli_present_named_file_keeps_its_standing(tmp_path):
    roster = tmp_path / "step-13-roster.json"
    roster.write_text(json.dumps({
        "file": roster.name,
        "seats": [_seat("seat-1", "agent-1"),
                  _seat("seat-2", "agent-2")],
        "board_seats": [_board("board-1", "agent-b1"),
                        _board("board-2", "agent-b2"),
                        _board("board-3", "agent-b3")],
    }), encoding="utf-8")
    outcome = _run_cli(
        tmp_path, "Step 13", ["%s:stage records" % roster])
    field5 = _field5(outcome)
    assert str(roster) not in field5["missing_files"], (
        "a named file present on disk stands in the missing "
        "files list: %s" % (field5["missing_files"],))
    counts = field5["coverage"]["stage records"]
    assert counts == {"needed": 1, "supplied": 1, "read": 1}, (
        "a named file present on disk is not counted as supplied "
        "and read: %s" % (counts,))
    stage_count = outcome["result_record"]["fields"]["7"]["stage_count"]
    assert stage_count["entries_counted"] == 2, (
        "the seats of a roster present on disk are not counted: "
        "%s" % (stage_count,))


def test_p13_cli_directory_named_keeps_other_form_standing(tmp_path):
    directory = tmp_path / "named-record-dir"
    directory.mkdir()
    outcome = _run_cli(
        tmp_path, "Step 13", ["%s:stage records" % directory])
    field5 = _field5(outcome)
    plain = [entry for entry in field5["missing_files"]
             if isinstance(entry, str)]
    assert str(directory) not in plain, (
        "a directory named on the command line is listed among "
        "the files that do not exist: %s"
        % (field5["missing_files"],))
    forms = [entry for entry in field5["missing_files"]
             if isinstance(entry, dict)]
    assert {"path": str(directory), "standing": "directory"} in forms, (
        "a directory named on the command line does not stand "
        "in the missing files list in its other form: %s"
        % (field5["missing_files"],))


def test_p13_fixture_shaped_kernel_input_keeps_stated_standing():
    kernel = importlib.import_module("muster_restart.kernel")
    run_input = {
        "pinned_base": "base-a",
        "records_named_for_round": ["plan-or-charge-1.md"],
        "runner_capacity": "Auditor",
        "runner_identity": "restart-test-runner",
        "stage_judged": "Step 13",
        "supplied_files": [
            {"group": "audit plan or round charge",
             "path": "plan-or-charge-1.md"},
        ],
        "tier": "Low",
    }
    result = kernel.compute_result(run_input)
    field5 = result["fields"]["5"]
    counts = field5["coverage"]["audit plan or round charge"]
    assert counts == {"needed": 1, "supplied": 1, "read": 1}, (
        "a fixture shaped entry naming a file not on disk lost "
        "the standing its input states: %s" % (counts,))
    assert field5["missing_files"] == [], (
        "a fixture shaped entry stands in the missing files "
        "list: %s" % (field5["missing_files"],))
