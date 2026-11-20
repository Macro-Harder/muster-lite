"""Audit fix P2-4: user facing cannot start causes state the
values, not a design citation.

The audit measured the two cannot start causes a user actually
reads citing design documents: a bad runner capacity was refused
with "the values at brief section 5.2" and an unknown option with
"the call shape at plan section 9". A user of the shipped tool
has neither document. These tests pin the corrected causes: the
capacity cause states the allowed capacity values, the unknown
name cause states the allowed option names, and neither cause
cites a brief or plan section.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(tmp_path, extra_args):
    args = [
        sys.executable, "-m", "muster_restart.run_entry",
        "--runner-identity", "A. Auditor",
        "--build", "muster-lite",
        "--stage", "Step 13",
        "--tier", "Low",
    ] + extra_args
    env = {"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"}
    result = subprocess.run(
        args, cwd=str(tmp_path), capture_output=True, text=True,
        env=env, timeout=120)
    return result


def _cause(outcome):
    return outcome["cannot_start_outcome"]["cause"]


def test_bad_capacity_cause_states_the_allowed_values(tmp_path):
    result = _run_cli(tmp_path, ["--runner-capacity", "Boss"])
    outcome = json.loads(result.stdout)
    cause = _cause(outcome)
    assert "Auditor" in cause
    assert "coordinator as precheck" in cause
    assert "board member other than the stage coordinator" in cause
    assert "brief section" not in cause
    assert "plan section" not in cause


def test_unknown_name_cause_states_the_call_shape(tmp_path):
    result = _run_cli(tmp_path, ["--runner-capacity", "Auditor",
                                 "--extra-flag", "x"])
    outcome = json.loads(result.stdout)
    cause = _cause(outcome)
    assert "--extra-flag" in cause
    assert "--runner-identity" in cause
    assert "--supplied-file" in cause
    assert "brief section" not in cause
    assert "plan section" not in cause
