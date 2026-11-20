"""Audit fix P3-2: the run entry catches only expected failures.

The audit measured two broad except Exception catches in
run_entry (the presentation calls in _finish_started_run and the
kernel call in run_invocation), so a coding error inside either
module read the same as an input defect: a NameError from a typo
would end the run as a tool failure or a form disagreement.
These tests pin the narrowed catches: an expected failure (a
type or value error from malformed input) still ends the run in
the stated outcome, the kernel catch names the failure kind in
its cause, and a coding error propagates instead of being
dressed as a result.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from muster_restart import kernel, presentation, run_entry

_INVOCATION = {
    "runner_identity": "A. Auditor",
    "runner_capacity": "Auditor",
    "stage_judged": "Step 13",
    "tier": "Low",
    "supplied_files": [],
}


def _raise(exc):
    def _inner(*args, **kwargs):
        raise exc
    return _inner


def test_kernel_coding_error_propagates(monkeypatch):
    monkeypatch.setattr(
        kernel, "compute_result", _raise(NameError("typo")))
    with pytest.raises(NameError):
        run_entry.run_invocation(dict(_INVOCATION))


def test_kernel_expected_failure_still_cannot_start(monkeypatch):
    monkeypatch.setattr(
        kernel, "compute_result", _raise(TypeError("bad shape")))
    outcome = run_entry.run_invocation(dict(_INVOCATION))
    cannot = outcome["cannot_start_outcome"]
    assert cannot is not None
    assert cannot["kind"] == "tool failure"
    assert "TypeError" in cannot["cause"]


def test_presentation_coding_error_propagates(monkeypatch):
    monkeypatch.setattr(
        presentation, "render_forms", _raise(NameError("typo")))
    with pytest.raises(NameError):
        run_entry._finish_started_run({}, {})


def test_presentation_expected_failure_still_defect(monkeypatch):
    monkeypatch.setattr(
        presentation, "render_forms",
        _raise(ValueError("bad record")))
    outcome = run_entry._finish_started_run({}, {})
    assert outcome["kind_number"] == 4
    assert outcome["defect_reports"]
