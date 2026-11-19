"""Step 22 cure pins for the V12-T1 clean clone node.

These pins read the source of test_v12_release_install.py and pin
the cured form of test_v12t1_clean_clone_suite_runs_green: its
recursive suite call carries a bounded timeout inside the bench
guard one hour cap, and its inner command excludes the node own
identity, by a deselect of its own node id and by an environment
marker the node honours by not re-entering. The pins execute no
part of the node they pin.
"""

import ast
from pathlib import Path

SOURCE = (Path(__file__).parent
          / "test_v12_release_install.py").read_text(encoding="utf-8")
NODE_NAME = "test_v12t1_clean_clone_suite_runs_green"
NODE_ID = ("tests_restart/test_v12_release_install.py::"
           "test_v12t1_clean_clone_suite_runs_green")
MARKER = "MUSTER_V12T1_INNER"
GUARD_CAP_SECONDS = 3600


def _node_function():
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == NODE_NAME:
            return node
    raise AssertionError(
        "WRONG OUTPUT V12 CURE PIN: the clean clone node does not "
        "stand in the module source")


def _run_call(function):
    for node in ast.walk(function):
        if isinstance(node, ast.Call) \
                and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "run":
            return node
    return None


def test_v12_cure_pin_recursive_call_carries_bounded_timeout():
    call = _run_call(_node_function())
    assert call is not None, (
        "WRONG OUTPUT V12 CURE PIN: no recursive suite call stands "
        "in the clean clone node")
    timeouts = [kw.value for kw in call.keywords if kw.arg == "timeout"]
    assert timeouts, (
        "WRONG OUTPUT V12 CURE PIN: the recursive suite call "
        "carries no timeout")
    value = timeouts[0]
    assert isinstance(value, ast.Constant) \
        and isinstance(value.value, (int, float)), (
            "WRONG OUTPUT V12 CURE PIN: the timeout is no stated "
            "finite number")
    assert 0 < value.value < GUARD_CAP_SECONDS, (
        "WRONG OUTPUT V12 CURE PIN: the timeout stands outside "
        "the bench guard one hour cap: %s" % (value.value,))


def test_v12_cure_pin_inner_command_deselects_own_node():
    call = _run_call(_node_function())
    assert call is not None, (
        "WRONG OUTPUT V12 CURE PIN: no recursive suite call stands "
        "in the clean clone node")
    constants = [node.value for node in ast.walk(call)
                 if isinstance(node, ast.Constant)
                 and isinstance(node.value, str)]
    assert "--deselect" in constants, (
        "WRONG OUTPUT V12 CURE PIN: the inner command carries no "
        "deselect")
    assert NODE_ID in constants, (
        "WRONG OUTPUT V12 CURE PIN: the inner command does not "
        "deselect the node own identity: %s" % NODE_ID)


def test_v12_cure_pin_inner_marker_honoured():
    function = _node_function()
    segment = ast.get_source_segment(SOURCE, function)
    assert segment is not None and segment.count(MARKER) >= 2 \
        and "environ.get" in segment, (
            "WRONG OUTPUT V12 CURE PIN: the node does not honour "
            "an environment marker by not re-entering: %s" % MARKER)
