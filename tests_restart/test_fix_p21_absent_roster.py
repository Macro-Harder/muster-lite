"""Audit fix P2-1: no PASS for checks 10 and 12 to 16 when the
roster record is absent.

The audit measured the README "Running it" example: the named
records do not stand on disk, no roster record is assembled, the
roster resting checks stand UNVERIFIABLE, and yet checks 10, 12,
13, 14, 15 and 16 print PASS with the citation "not applicable:
linkage did not pass for this seat". That is a pass for work that
did not happen. These tests pin the corrected words: on an absent
roster, checks 10, 12, 13, 15 and 16 stand UNVERIFIABLE, and
check 14 stands NOT PROVEN, the word the kernel already pins for
colour completeness on a bare absence.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_ON_ABSENT_ROSTER = {
    10: "UNVERIFIABLE",
    12: "UNVERIFIABLE",
    13: "UNVERIFIABLE",
    14: "NOT PROVEN",
    15: "UNVERIFIABLE",
    16: "UNVERIFIABLE",
}


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


def _check_verdicts(outcome):
    fields = outcome["result_record"]["fields"]
    return {entry["check"]: entry["verdict"]
            for entry in fields["6"]["check_results"]}


def test_readme_shape_absent_roster_checks_do_not_pass(tmp_path):
    supplied = [
        "records/step-14-roster.md:stage records",
        "records/step-14-roster.md:claim bearing files",
        "records/step-14-record.md:stage records",
        "records/step-14-record.md:claim bearing files",
        "records/TIER-RECORD.md:stage records",
        "records/step-14-gate-record.md:claim bearing files",
    ]
    outcome = _run_cli(tmp_path, "Step 14", supplied)
    verdicts = _check_verdicts(outcome)
    for number, expected in EXPECTED_ON_ABSENT_ROSTER.items():
        assert verdicts[number] == expected, (
            "check %s stands %s on an absent roster, expected %s"
            % (number, verdicts[number], expected))


def test_absolute_missing_roster_checks_do_not_pass(tmp_path):
    missing = str(tmp_path / "no-such-dir" / "roster.md")
    supplied = [
        missing + ":stage records",
        missing + ":claim bearing files",
    ]
    outcome = _run_cli(tmp_path, "Step 13", supplied)
    verdicts = _check_verdicts(outcome)
    for number, expected in EXPECTED_ON_ABSENT_ROSTER.items():
        assert verdicts[number] == expected, (
            "check %s stands %s on an absent roster, expected %s"
            % (number, verdicts[number], expected))
