"""Consumer side fixture for the Agentic form, TM-REND-1, AI-4 part one.

A small reader that consumes a fixture Agentic rendering using only the
governing field list at brief section 5.3, and that fails on any missing
or renamed required field in that list. Test suite only.
"""

REQUIRED_FIELDS = (
    "tool_name",
    "tool_version",
    "grade",
    "claim_cap_sentence",
    "run_kind",
    "stage",
    "tier_applied",
    "pinned_base_name",
    "pinned_base_hash",
    "pinned_base_bytes",
    "runner_name",
    "runner_capacity",
    "rollup",
    "exit_code",
    "checks",
    "counting_table_version",
    "counting_table_hash",
    "diagnostic_catalogue_version",
    "coverage",
    "standing_limits",
    "context_files",
    "uncounted_appendix",
    "exempt_account",
    "consequence",
    "missing_seats",
    "duplicate_holdings",
    "claim_disagreements",
    "inputs_read",
    "inputs_ignored",
)

REQUIRED_CHECK_FIELDS = (
    "check_id",
    "diagnostic_code",
    "rule_reference",
    "scope",
    "expected",
    "counted_total",
    "duplicates_removed",
    "exempt_or_uncounted_removed",
    "verdict",
    "evidence_files",
)


class ConsumerError(Exception):
    pass


def consume(agentic):
    """Raise ConsumerError on any missing or renamed required field."""
    if not isinstance(agentic, dict):
        raise ConsumerError("Agentic form is not one JSON object")
    for field in REQUIRED_FIELDS:
        if field not in agentic:
            raise ConsumerError("required field missing or renamed: %s" % field)
    for check in agentic.get("checks", []):
        for field in REQUIRED_CHECK_FIELDS:
            if field not in check:
                raise ConsumerError(
                    "required check field missing or renamed: %s" % field)
    return True
