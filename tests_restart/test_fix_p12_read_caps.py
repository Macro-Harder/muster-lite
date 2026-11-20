"""Audit fix P1-2: bounded reads of supplied files.

The audit measured a 400 MiB supplied regular file killing the
run at the roster read with MemoryError, empty stdout and process
exit 1, where the documented outcome for a tool failure before a
result record stands is a cannot start JSON and exit 2. These
tests pin the capped behavior: a supplied file standing larger
than the read cap is not read, an invocation naming one ends as a
cannot start run of kind tool failure with exit code 2 and the
JSON outcome printed, and the kernel receipt takes no hash and
no byte size from an oversize standing file.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

import json
import subprocess
import sys
from pathlib import Path

from muster_restart import run_entry
from muster_restart.kernel import compute_result

REPO_ROOT = Path(__file__).resolve().parents[1]

NO_HASH = (
    "no hash stands, because no file bytes stand for the named "
    "file at this run")
NO_SIZE = (
    "no byte size stands, because no file bytes stand for the "
    "named file at this run")


def _oversize_file(directory, name):
    from muster_restart.kernel import MAX_READ_BYTES
    path = directory / name
    with open(path, "wb") as handle:
        handle.truncate(MAX_READ_BYTES + 1)
    return path


def _run_cli(tmp_path, supplied):
    args = [
        sys.executable, "-m", "muster_restart.run_entry",
        "--runner-identity", "A. Auditor",
        "--runner-capacity", "Auditor",
        "--build", "muster-lite",
        "--stage", "Step 13",
        "--tier", "Low",
    ]
    for entry in supplied:
        args += ["--supplied-file", entry]
    env = {"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"}
    return subprocess.run(
        args, cwd=str(tmp_path), capture_output=True, text=True,
        env=env, timeout=120)


def test_oversize_roster_file_cannot_start_as_tool_failure(tmp_path):
    big = _oversize_file(tmp_path, "big-roster.md")
    result = _run_cli(tmp_path, ["%s:stage records" % big])
    assert result.returncode == 2, result.stdout[-400:]
    outcome = json.loads(result.stdout)
    assert outcome["exit_code"] == 2
    assert outcome["result_record"] is None
    cannot = outcome["cannot_start_outcome"]
    assert cannot is not None
    assert cannot["kind"] == "tool failure"


def test_oversize_claim_file_cannot_start_as_tool_failure(tmp_path):
    big = _oversize_file(tmp_path, "big-claims.md")
    result = _run_cli(tmp_path, ["%s:claim bearing files" % big])
    assert result.returncode == 2, result.stdout[-400:]
    outcome = json.loads(result.stdout)
    assert outcome["exit_code"] == 2
    cannot = outcome["cannot_start_outcome"]
    assert cannot is not None
    assert cannot["kind"] == "tool failure"


def test_kernel_receipt_takes_no_hash_from_oversize_file(tmp_path):
    big = _oversize_file(tmp_path, "big-record.md")
    result = compute_result({
        "runner_identity": "restart-test-runner",
        "runner_capacity": "Auditor",
        "stage_judged": "Step 13",
        "tier": "Low",
        "supplied_files": [
            {"group": "stage records", "path": str(big),
             "read": True},
        ],
    })
    receipt = result["fields"]["5"]["receipt"]
    entries = [e for e in receipt if e["file_path"] == str(big)]
    assert len(entries) == 1
    assert entries[0]["hash"] == NO_HASH
    assert entries[0]["byte_size"] == NO_SIZE


def test_memory_error_in_assembly_is_a_tool_failure_outcome(
        monkeypatch, capsys):
    def raising(invocation):
        raise MemoryError()

    monkeypatch.setattr(run_entry, "_assemble_content", raising)
    code = run_entry.main([
        "--runner-identity", "A. Auditor",
        "--runner-capacity", "Auditor",
        "--build", "muster-lite",
        "--stage", "Step 13",
        "--tier", "Low",
    ])
    outcome = json.loads(capsys.readouterr().out)
    assert code == 2
    assert outcome["exit_code"] == 2
    cannot = outcome["cannot_start_outcome"]
    assert cannot is not None
    assert cannot["kind"] == "tool failure"
