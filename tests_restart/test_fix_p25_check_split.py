"""Audit fix P2-5: _check_results stands split by check group.

The audit measured _check_results at 668 lines in one body
(kernel.py), the file's largest unit, carrying items 1 to 15 in
one if and elif chain with its entry helpers nested inside.
This test pins the split: the composing function itself stands
short, and the per group helpers stand at module level for
checks 1 to 3, 4 to 5, 6 to 9 and 10 to 15. Behaviour is
unchanged by construction and is proven by the full suite,
which exercises every check.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

import inspect
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from muster_restart import kernel


def test_check_results_is_split_by_check_group():
    source = inspect.getsource(kernel._check_results)
    lines = source.splitlines()
    assert len(lines) < 250, (
        "_check_results still stands at %d lines in one body"
        % len(lines))
    for helper in ("_checks_1_to_3", "_checks_4_to_5",
                   "_checks_6_to_9", "_checks_10_to_15"):
        assert callable(getattr(kernel, helper, None)), (
            "no %s helper stands in the kernel" % helper)
