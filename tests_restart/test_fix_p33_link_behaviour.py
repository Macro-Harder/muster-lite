"""Audit fix P3-3: the README states the link behaviour.

The audit measured that a supplied path standing as a symlink
to a file is followed and read as the file it names, and a hard
link is accepted as the file, because standing is judged by the
named path being a file and no link check stands anywhere in
the product. Neither behaviour stood in the README. This test
pins the documentation: both behaviours are stated.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_readme_states_the_link_behaviour():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "symlink" in text, (
        "the README does not state that a symlink to a file is "
        "followed")
    assert "hard link" in text, (
        "the README does not state that a hard link is accepted "
        "as the file")
