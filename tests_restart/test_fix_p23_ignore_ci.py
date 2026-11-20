"""Audit fix P2-3: ignore rules stand in the repo.

The audit measured no .gitignore: run artefacts such as
__pycache__ appeared untracked from test imports, and no ignore
rule guards secret shaped files. This test pins the file: a
.gitignore covering run artefacts and secret shaped names.

The CI half of the finding stands apart: the connector token
cannot push a workflow path (the publish attempt measured a 404
on tree creation), so the workflow file is delivered in the pull
request body for a direct push, and no test in the tree asserts
it.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_gitignore_covers_artefacts_and_secrets():
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), "no .gitignore stands in the repo"
    entries = [line.strip() for line in
               gitignore.read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.startswith("#")]
    assert "__pycache__/" in entries
    assert ".env" in entries
