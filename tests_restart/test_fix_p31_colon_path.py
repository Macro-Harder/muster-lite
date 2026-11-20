"""Audit fix P3-1: a colon inside a supplied path parses whole.

The audit measured a supplied file entry whose path contains a
colon, the Windows drive form C:\\records\\x.md, refused at parse:
the parser split the entry at its first colon, taking the group
from there, so the path was cut to "C" and the group stood as the
rest of the string. These tests pin the corrected parse: the
group is taken from the last colon, a colon bearing path is
accepted whole, and an unknown group after the last colon is
still refused naming that group.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(tmp_path, supplied_value):
    args = [
        sys.executable, "-m", "muster_restart.run_entry",
        "--runner-identity", "A. Auditor",
        "--runner-capacity", "Auditor",
        "--build", "muster-lite",
        "--stage", "Step 13",
        "--tier", "Low",
        "--supplied-file", supplied_value,
    ]
    env = {"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"}
    result = subprocess.run(
        args, cwd=str(tmp_path), capture_output=True, text=True,
        env=env, timeout=120)
    return json.loads(result.stdout)


def test_colon_in_path_is_accepted_whole(tmp_path):
    outcome = _run_cli(
        tmp_path, "C:\\records\\x.md:stage records")
    assert outcome["cannot_start_outcome"] is None, (
        "a supplied path carrying a colon was refused: %s"
        % outcome["cannot_start_outcome"])
    assert outcome["kind"] == "completed gate run"


def test_unknown_group_after_last_colon_still_refused(tmp_path):
    outcome = _run_cli(
        tmp_path, "C:\\records\\x.md:bogus group")
    cannot = outcome["cannot_start_outcome"]
    assert cannot is not None
    assert "bogus group" in cannot["cause"]
