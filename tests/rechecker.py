"""Bounded test side rechecker, Step 13 share item (5), TM-STEP13-5.

The rechecker sits inside the test suite and nowhere else. It reads the
Agentic form of a fixture run and the shipped tables, and verifies internal
consistency among the printed fields only: the rollup word against the
composing check words under the ladder at brief section 5.6; the arithmetic
of a printed count against its printed subtraction components, under the
assignment rule and precedence at TM-CORE-COUNT-1 (each removed entry
stands in exactly one printed figure); and the figures of a coverage line
against each other.

Bound, in full: the rechecker does not rederive the components themselves
from seat level inputs, because no printed field carries those inputs. A
derivation error the core printed consistently in every field the
rechecker reads is outside what it can catch, and no test states its scope
wider than that bound. No second computation of the results stands inside
the runtime core under this item.
"""

LADDER = ("FAIL", "UNVERIFIABLE", "NOT PROVEN", "PASS")


def expected_rollup(composing_words):
    for word in LADDER:
        if word in composing_words:
            return word
    return "PASS"


def check_report(agentic):
    """Return a list of inconsistency strings; empty means consistent."""
    problems = []
    checks = agentic.get("checks", [])
    composing = [c.get("verdict") for c in checks if c.get("composing")]
    if composing:
        want = expected_rollup(composing)
        if agentic.get("rollup") != want:
            problems.append(
                "rollup %r does not match composing checks %r"
                % (agentic.get("rollup"), composing))
    for count in agentic.get("counts", []):
        total = (count.get("entries", 0)
                 - count.get("duplicates_removed", 0)
                 - count.get("exempt_or_uncounted_removed", 0))
        if total != count.get("counted_total"):
            problems.append(
                "count arithmetic fails for %r: printed total %r, "
                "subtraction gives %r"
                % (count.get("name"), count.get("counted_total"), total))
    for line in agentic.get("coverage", []):
        total = (line.get("checked", 0) + line.get("not_checked", 0))
        if total != line.get("total"):
            problems.append(
                "coverage figures fail for %r: checked plus not checked "
                "is %r, total printed %r"
                % (line.get("scope"), total, line.get("total")))
    return problems
