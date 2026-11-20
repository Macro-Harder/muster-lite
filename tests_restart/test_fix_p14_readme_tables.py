"""Audit fix P1-4: the README states the pinned table limit.

The audit measured that the shipped counting tables hold one row
each, for Step 13, the Low tier and the Design team, while the
README "Running it" example judges Step 14 and the "Potential
problem causers" list never mentions the limit, so a reader meets
an UNVERIFIABLE check 1 with no stated cause. These tests pin the
corrected text: the example judges Step 13, and the problem
causers list states the table limit.

This module imports no conftest helpers, so it collects and runs
in every suite configuration.
"""

from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def _section(text, heading):
    start = text.index(heading)
    rest = text[start + len(heading):]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_running_it_example_judges_step_13():
    text = README.read_text(encoding="utf-8")
    section = _section(text, "## Running it")
    assert '--stage "Step 13"' in section
    assert "Step 14" not in section


def test_problem_causers_states_the_table_limit():
    text = README.read_text(encoding="utf-8")
    section = _section(text, "## Potential problem causers")
    bullets = [line for line in section.splitlines()
               if line.startswith("- ")]
    stating = [line for line in bullets
               if "Step 13" in line and "Low" in line
               and "Design team" in line and "only" in line]
    assert stating, (
        "no problem causers bullet states that the pinned tables "
        "cover Step 13, Low and the Design team only")
