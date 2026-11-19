"""Plan section 12 groups V12-T1 and V12-T2: release and install.

Loci: plan section 12 in full. Every test states its concrete wrong
output in the form the Step 13 test plan charges for its group.
These groups stand written at Step 13 and fail in the failure form
of the test plan section 9: the restart product does not exist and
the shipped contents stand unshipped. They run as a release test at
Step 22 and as an install test at Step 18 readiness, as plan
section 12 states.

Surfaces pinned by these tests for the later steps: the shipped tree
stands in the build repo root beside this suite package, holding the
kernel module file, the presentation module file and the run entry
file of the package muster_restart, the counting table data files in
their three named parts with the manifest, the regression fixtures,
the README and the LICENSE.
"""

import ast
import importlib
import json
import sys
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
REPO_ROOT = Path(__file__).resolve().parents[1]

SHIPPED_CONTENTS_LIST = [
    "muster_restart/kernel.py",
    "muster_restart/presentation.py",
    "muster_restart/run_entry.py",
    "counting tables, Layer 1",
    "counting tables, Layer 2 with exception rows",
    "counting tables, mapping rows",
    "counting tables manifest",
    "regression fixtures with their expected results",
    "README",
    "LICENSE",
]

PYTHON_FLOOR = (3, 11)


def _load(relative):
    return json.loads((FIXTURES / relative).read_text(encoding="utf-8"))


# V12-T1 wrong output form charged: named constant. An import failing
# under the Python floor, a non standard library import found, the
# clean clone suite not green, or the first run over the shipped
# staffed roster fixture returning a rollup other than its expected
# rollup.
WRONG_OUTPUT_V12_T1 = (
    "first run over the shipped staffed roster fixture returning "
    "rollup PASS instead of its expected rollup UNVERIFIABLE")


def test_v12t1_both_modules_import_under_python_floor():
    assert sys.version_info[:2] >= PYTHON_FLOOR
    for name in ("muster_restart.kernel", "muster_restart.presentation"):
        module = importlib.import_module(name)
        assert module is not None, (
            "WRONG OUTPUT V12-T1: an import failing under the "
            "Python floor for %s" % name)


def test_v12t1_no_non_standard_library_import_in_shipped_modules():
    importlib.import_module("muster_restart.kernel")
    stdlib = set(sys.stdlib_module_names)
    for relative in ("muster_restart/kernel.py",
                     "muster_restart/presentation.py",
                     "muster_restart/run_entry.py"):
        tree = ast.parse((REPO_ROOT / relative).read_text(
            encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[0]]
            else:
                continue
            for name in names:
                assert name in stdlib or name == "muster_restart", (
                    "WRONG OUTPUT V12-T1: a non standard library "
                    "import found in %s: %s" % (relative, name))


# The clean clone node excludes itself from its inner run, by a
# deselect of its own node id and by the MUSTER_V12T1_INNER
# environment marker the node honours by not re-entering, and its
# recursive call carries a timeout of 1800 seconds, inside the
# bench guard one hour cap, so the inner run can neither re-enter
# this node nor run without bound.
def test_v12t1_clean_clone_suite_runs_green():
    import os
    import subprocess
    if os.environ.get("MUSTER_V12T1_INNER") == "1":
        return
    importlib.import_module("muster_restart.kernel")
    inner_env = dict(os.environ)
    inner_env["MUSTER_V12T1_INNER"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests_restart", "-q",
         "--deselect",
         "tests_restart/test_v12_release_install.py::"
         "test_v12t1_clean_clone_suite_runs_green"],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
        env=inner_env, timeout=1800)
    assert result.returncode == 0, (
        "WRONG OUTPUT V12-T1: the clean clone suite not green: %s"
        % result.stdout[-400:])


def test_v12t1_first_run_over_shipped_staffed_roster_fixture():
    kernel = importlib.import_module("muster_restart.kernel")
    fixture = _load("F1/shipped_staffed_roster.json")
    result = kernel.compute_result({"roster_fixture": fixture["roster"]})
    rollup = result["fields"]["12"]
    assert rollup == fixture["expected_rollup"], (
        "WRONG OUTPUT V12-T1: %s" % WRONG_OUTPUT_V12_T1)


# V12-T2 wrong output form charged: assertion message per unlisted
# file. A file standing in the shipped tree that the contents list
# does not name, design material or a builder mention found inside
# file contents and not only in file names. The contents list stands
# at plan section 12 and in SHIPPED_CONTENTS_LIST above.
# The shipped tree the plan section 12 contents list names, walked
# from the clone root the release verification states. The list
# names the three module files by their paths, the counting table
# data files by their three named parts, the regression fixtures as
# the one set, and the README and the LICENSE by their bare names.
# The walker walks the shipped tree where it stands in the clone:
# the package directory, the fixtures directory, and the README and
# LICENSE at the root. It yields each shipped file under the name
# the contents list states for it, and a file standing in the
# walked places that the list does not name under its own path, so
# the contents sweep names it and fails on it. The package file
# __init__.py stands in the package directory as the package
# machinery: the contents list states the shipped tree without it,
# as the module head above states that tree, and the walker does
# not yield it. Interpreter artefact files under __pycache__
# directories are not shipped files and are not yielded.
_SHIPPED_NAME_BY_PATH = {
    "muster_restart/layer1.json": "counting tables, Layer 1",
    "muster_restart/layer2.json":
        "counting tables, Layer 2 with exception rows",
    "muster_restart/mapping.json": "counting tables, mapping rows",
    "README.md": "README",
}
_SHIPPED_PATH_BY_NAME = {
    name: path for path, name in _SHIPPED_NAME_BY_PATH.items()}
_FIXTURE_NAME_PREFIX = "regression fixtures/"
_PACKAGE_FILE = "muster_restart/__init__.py"


def _shipped_files():
    importlib.import_module("muster_restart.kernel")
    shipped = []
    for path in sorted((REPO_ROOT / "muster_restart").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts \
                or path.suffix == ".pyc":
            continue
        relative = str(path.relative_to(REPO_ROOT))
        if relative == _PACKAGE_FILE:
            continue
        shipped.append(_SHIPPED_NAME_BY_PATH.get(relative, relative))
    for path in sorted(FIXTURES.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts \
                or path.suffix == ".pyc":
            continue
        shipped.append(_FIXTURE_NAME_PREFIX
                       + str(path.relative_to(FIXTURES)))
    for root_file in ("README.md", "LICENSE"):
        if (REPO_ROOT / root_file).is_file():
            shipped.append(
                _SHIPPED_NAME_BY_PATH.get(root_file, root_file))
    return sorted(shipped)


def _shipped_file_path(name):
    if name in _SHIPPED_PATH_BY_NAME:
        return _SHIPPED_PATH_BY_NAME[name]
    if name.startswith(_FIXTURE_NAME_PREFIX):
        return "tests_restart/fixtures/" + name[
            len(_FIXTURE_NAME_PREFIX):]
    return name


def test_v12t2_every_shipped_file_stands_on_contents_list():
    named = {entry for entry in SHIPPED_CONTENTS_LIST
             if "/" in entry or entry in ("README", "LICENSE")}
    for relative in _shipped_files():
        assert relative in named or relative.startswith(
            "counting tables") or relative.startswith(
            "regression fixtures"), (
            "WRONG OUTPUT V12-T2: a file standing in the shipped "
            "tree that the contents list does not name: %s" % relative)


def test_v12t2_no_design_material_inside_file_contents():
    for relative in _shipped_files():
        text = (REPO_ROOT / _shipped_file_path(relative)).read_text(
            encoding="utf-8", errors="ignore")
        for marker in ("DESIGN-BRIEF", "DESIGN-PLAN", "design brief",
                       "design plan"):
            assert marker not in text, (
                "WRONG OUTPUT V12-T2: design material found inside "
                "the contents of shipped file %s, not only in its "
                "file name" % relative)


# TD-04 licence exception data for the builder mention sweep node
# below, and for no other node: the Apache 2.0 licence text that
# plan section 12 requires to ship carries the words "generated by"
# inside its Derivative Works sentence in the LICENSE file. The
# exception removes that one licence phrase, as licence text, from
# the LICENSE file alone before the sweep reads it. Every other
# occurrence of every marker, in any file and in any other position
# of the LICENSE file, still fails the sweep.
LICENCE_EXCEPTION_FILE = "LICENSE"
LICENCE_EXCEPTION_PHRASE = (
    "within a display generated by the Derivative Works")


def test_v12t2_no_builder_mention_inside_file_contents():
    for relative in _shipped_files():
        text = (REPO_ROOT / _shipped_file_path(relative)).read_text(
            encoding="utf-8", errors="ignore")
        if relative == LICENCE_EXCEPTION_FILE:
            text = text.replace(LICENCE_EXCEPTION_PHRASE, "")
        for marker in ("Builder:", "built by Muse", "generated by"):
            assert marker not in text, (
                "WRONG OUTPUT V12-T2: a builder mention found "
                "inside the contents of shipped file %s, not only "
                "in its file name" % relative)
