"""Shared loading code for the restart run suite.

This file holds no test and no expected result of its own. It loads
fixtures from the fixtures directory beside it and it calls the restart
product. The restart product import surface used by every test in this
package is the package muster_restart, with its kernel module at
muster_restart.kernel, its presentation module at
muster_restart.presentation and its run entry at muster_restart.run_entry,
as plan section 1 and brief section 5.1 state the product form: two
modules, the kernel module and the presentation module, plus the run
entry, one deployable unit. That product does not exist at Step 13, so
every product test in this package fails on its absence and on no other
ground. The kernel entry the tests call is compute_result(run_input),
which returns the ComputedResult of brief section 5.4.2 as a mapping with
a fields mapping keyed by contract field number as text, a check_results
list, and the remaining contract content under its shape names.
"""

import importlib
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
PRODUCT_KERNEL = "muster_restart.kernel"


def require_kernel():
    return importlib.import_module(PRODUCT_KERNEL)


def load_case(relative_path, case_name):
    data = json.loads((FIXTURES / relative_path).read_text(encoding="utf-8"))
    return data["cases"][case_name]


def run_case(relative_path, case_name):
    kernel = require_kernel()
    case = load_case(relative_path, case_name)
    result = kernel.compute_result(case["run_input"])
    return result, case["expected"]


def field(result, number):
    return result["fields"][str(number)]


def checks(result, item):
    return [entry for entry in result["check_results"] if entry["check"] == item]


def check(result, item):
    found = checks(result, item)
    assert len(found) == 1, "expected exactly one CheckResult for check %s" % item
    return found[0]


def result_text(result):
    return json.dumps(result, sort_keys=True)
