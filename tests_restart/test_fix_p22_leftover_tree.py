"""Audit fix P2-2: the leftover first run tree is not in the repo.

The audit measured 48 tracked paths of the superseded first run
still standing in the public tree: three product modules, two
data files and the whole legacy tests/ tree, whose own suite
stands red at this head (405 tests, 13 failures) beside the green
release suite. A reader meets two products. These tests pin the
removal: none of the leftover paths stands in the tree.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

LEFTOVER_ROOT_FILES = [
    "muster_core.py",
    "muster_lite.py",
    "muster_shell.py",
    "counting-table.json",
    "diagnostic-catalogue.json",
]


def test_leftover_root_files_are_absent():
    standing = [name for name in LEFTOVER_ROOT_FILES
                if (REPO_ROOT / name).exists()]
    assert not standing, (
        "leftover first run files still stand: %s" % standing)


def test_leftover_legacy_test_tree_is_absent():
    assert not (REPO_ROOT / "tests").exists(), (
        "the leftover legacy tests tree still stands")
