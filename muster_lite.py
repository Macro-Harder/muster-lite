"""muster-lite, a grade L2 records checker.

Module 3, the entry and rendering module. The entry parses the run
arguments, has the shell capture the supplied set, loads the shipped
counting table and diagnostic catalogue from beside the entry, runs
the pure core, and renders the one result in the three forms: the
Simple form, the Advanced form, and the Agentic form, delivered in
that order.

Exit outcomes: 0 PASS, 1 FAIL, 2 NOT PROVEN, 3 UNVERIFIABLE, 4 where
no named input can be read and the run cannot start, 5 for a
malformed invocation, and 6 for a tool fault in a run that started.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import muster_core
import muster_shell

USAGE_OPTIONS = ("--stage", "--runner", "--capacity", "--context",
                 "--base-record", "--kind", "--fixture-fault")

# Every character a line reader splits text on: newline, carriage
# return, U+2028, U+2029, U+000B, U+000C, and U+0085. A printed value
# carrying any of them could write a line of its own into an output,
# so each one prints as a space in every printed value, on every
# output path.
LINE_BREAK_CHARS = tuple(
    chr(code) for code in (0x0A, 0x0D, 0x2028, 0x2029, 0x0B, 0x0C,
                           0x85))


def _printed_value(value):
    """A value with every line break character printed as a space."""
    for break_char in LINE_BREAK_CHARS:
        value = value.replace(break_char, " ")
    return value


def _report_text(text):
    """Report text with every line break character that a value
    could carry printed as a space. The newline character stands:
    it is the line break the report forms themselves are built
    from, and no value reaches it unsanitised."""
    for break_char in LINE_BREAK_CHARS:
        if break_char == "\n":
            continue
        text = text.replace(break_char, " ")
    return text


class UsageError(Exception):
    pass


def parse_arguments(argv):
    """Parse the run arguments under the suite convention.

    Positional arguments are the supplied files in the order named.
    Named options are --stage, --runner, --capacity, --context
    (repeatable), --base-record (repeatable), and --kind.
    """
    parsed = {"files": [], "context": [], "base_record": [],
              "stage": None, "runner": None, "capacity": None,
              "kind": "gate run", "fixture_fault": None}
    single_value_seen = set()
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg.startswith("--"):
            if arg not in USAGE_OPTIONS:
                raise UsageError("unknown option: %s" % arg)
            if index + 1 >= len(argv):
                raise UsageError("option needs a value: %s" % arg)
            value = argv[index + 1]
            if value.startswith("--"):
                # An option word standing where a value belongs is a
                # malformed invocation, never a value.
                raise UsageError("option needs a value: %s" % arg)
            if arg not in ("--context", "--base-record"):
                # A single value option given twice is a malformed
                # invocation: no value silently governs over another.
                if arg in single_value_seen:
                    raise UsageError(
                        "option given more than once: %s" % arg)
                single_value_seen.add(arg)
            index += 2
            if arg in ("--stage", "--runner", "--capacity"):
                # These values are printed into the fixed report
                # lines, so every line break character inside one is
                # printed as a space: a value can never write a line
                # of its own into a report.
                value = _printed_value(value)
            if arg == "--stage":
                parsed["stage"] = value
            elif arg == "--runner":
                parsed["runner"] = value
            elif arg == "--capacity":
                parsed["capacity"] = value
            elif arg == "--context":
                parsed["context"].append(value)
            elif arg == "--base-record":
                parsed["base_record"].append(value)
            elif arg == "--kind":
                if value == "precheck":
                    parsed["kind"] = "PRECHECK"
                elif value in ("gate run", "gate"):
                    parsed["kind"] = "gate run"
                else:
                    raise UsageError("unknown run kind: %s" % value)
            elif arg == "--fixture-fault":
                parsed["fixture_fault"] = value
        else:
            parsed["files"].append(arg)
            index += 1
    return parsed


# ----------------------------------------------------------------
# Agentic form serialisation


def _escape_string(value):
    out = []
    for char in value:
        code = ord(char)
        if char == '"':
            out.append('\\"')
        elif char == "\\":
            out.append("\\\\")
        elif code < 0x20:
            out.append("\\u%04x" % code)
        elif code < 0x7F or code == 0x7F:
            out.append(char)
        elif code <= 0xFFFF:
            out.append("\\u%04x" % code)
        else:
            code -= 0x10000
            out.append("\\u%04x\\u%04x" % (
                0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF)))
    return '"%s"' % "".join(out)


def serialise(value, depth=0):
    """Serialise in the Agentic form: keys alphabetical at every
    level, indent 2, a colon and a space, LF line breaks."""
    indent = "  " * depth
    inner = "  " * (depth + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = []
        for key in sorted(value):
            parts.append("%s%s: %s" % (
                inner, _escape_string(str(key)),
                serialise(value[key], depth + 1)))
        return "{\n%s\n%s}" % (",\n".join(parts), indent)
    if isinstance(value, (list, tuple)):
        if not value:
            return "[]"
        parts = ["%s%s" % (inner, serialise(item, depth + 1))
                 for item in value]
        return "[\n%s\n%s]" % (",\n".join(parts), indent)
    if isinstance(value, str):
        return _escape_string(value)
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def agentic_object(result):
    pinned = result["pinned_base"] or {}
    return {
        "tool_name": result["tool_name"],
        "tool_version": result["tool_version"],
        "grade": result["grade"],
        "claim_cap_sentence": result["claim_cap_sentence"],
        "run_kind": result["run_kind"],
        "stage": result["stage"],
        "tier_applied": result["tier_applied"],
        "pinned_base_name": pinned.get("name"),
        "pinned_base_hash": pinned.get("hash"),
        "pinned_base_bytes": pinned.get("bytes"),
        "runner_name": result["runner_name"],
        "runner_capacity": result["runner_capacity"],
        "rollup": result["rollup"],
        "exit_code": result["exit_code"],
        "checks": [check.as_dict(index + 1) for index, check
                   in enumerate(result["checks"])],
        "counting_table_version": result["counting_table_version"],
        "counting_table_hash": result["counting_table_hash"],
        "diagnostic_catalogue_version":
            result["diagnostic_catalogue_version"],
        "counts": [count.as_dict() for count in result["counts"]],
        "coverage": result["coverage"],
        "standing_limits": result["standing_limits"],
        "context_files": result["context_files"],
        "uncounted_appendix": result["uncounted_appendix"],
        "exempt_account": result["exempt_account"],
        "consequence": result["consequence"],
        "missing_seats": result["missing_seats"],
        "duplicate_holdings": result["duplicate_holdings"],
        "claim_disagreements": result["claim_disagreements"],
        "inputs_read": result["inputs_read"],
        "inputs_ignored": result["inputs_ignored"],
        "inputs_unread": result["inputs_unread"],
        "seats": result["seats"],
        "team_results": result["team_results"],
    }


# ----------------------------------------------------------------
# The Simple form


def _join(names):
    return ", ".join(names) if names else "none"


def _blockers(result):
    severity_rank = {"Critical": 0, "High": 1, "record defect": 2,
                     "none": 3}
    verdict_rank = {"FAIL": 0, "UNVERIFIABLE": 1, "NOT PROVEN": 2}
    lines = []
    seen = set()
    candidates = [check for check in result["checks"]
                  if check.verdict != "PASS"]
    # Where a distinctness FAIL already names the duplicate holding
    # that proves a team minimum shortfall for the same team and
    # round, the minimum blocker does not stand beside it: the one
    # proven cause carries one blocker line.
    distinctness_blocks = {
        (check.scope, check.round_key) for check in candidates
        if check.kind == "distinctness" and check.verdict == "FAIL"}
    candidates = [
        check for check in candidates
        if not (check.kind == "team minimums"
                and check.verdict == "FAIL"
                and (check.scope, check.round_key)
                in distinctness_blocks)]
    candidates.sort(key=lambda check: (
        severity_rank.get(check.severity, 3),
        verdict_rank.get(check.verdict, 3),
        check.kind, check.scope,
        muster_core.round_sort(check.round_key),
        check.check_index if hasattr(check, "check_index") else 0))
    for index, check in enumerate(candidates):
        key = (check.kind, check.missing_fact, check.evidence_text)
        if key in seen:
            continue
        seen.add(key)
        consequence = "this stage may not be claimed as staffed on " \
                      "this run."
        if check.missing_fact:
            lines.append(
                "Blocker: %s: %s: %s: %s: expected %s, observed %s, "
                "evidence %s. Missing fact: %s. Consequence: %s" % (
                    check.diagnostic_code, check.kind, check.scope,
                    check.rule_reference, check.expected,
                    check.observed, check.evidence_text,
                    check.missing_fact, consequence))
        else:
            lines.append(
                "Blocker: %s: %s: %s: %s: expected %s, observed %s, "
                "evidence %s. Shortfall proven on the records "
                "supplied. Consequence: %s" % (
                    check.diagnostic_code, check.kind, check.scope,
                    check.rule_reference, check.expected,
                    check.observed, check.evidence_text, consequence))
    return lines


def _records_to_change(result, blocker_lines):
    files = []
    for check in result["checks"]:
        if check.verdict == "PASS":
            continue
        change_class = check.missing_fact is None or \
            check.kind == "artefact linkage"
        if change_class:
            for name in check.evidence_files:
                if name and name not in files:
                    files.append(name)
    return files


def simple_form(result):
    lines = []
    title = "Muster-lite staffing report: "
    if result["run_kind"] == "PRECHECK":
        title += "PRECHECK: "
    if result["roster_evidence_only"]:
        title += "roster evidence only: "
    title += result["stage"] + "."
    lines.append(title)
    lines.append(result["claim_cap_sentence"])
    lines.append(result["grade_sentence"])
    # Slot 4, the identity line.
    slot4 = ["Stage: %s." % result["stage"],
             "Tier applied: %s." % result["tier_applied"]]
    if result["base_disagreement"]:
        # Slot 4 disagreement form, Section 5.8: the disagreement
        # sentence, one Identification sentence per distinct base,
        # and the sentence that no pinned base is applied.
        slot4.append("Pinned base: disagreement in the records "
                     "identifying the base.")
        for base in result["base_identifications"]:
            slot4.append("Identification: %s, hash %s, %d bytes." % (
                base["name"], base["hash"], base["bytes"]))
        slot4.append("No pinned base is applied for this run.")
    elif result["pinned_base"]:
        base = result["pinned_base"]
        slot4.append("Pinned base: %s, hash %s, %s bytes." % (
            base["name"], base["hash"], base["bytes"]))
    else:
        slot4.append("Pinned base: none named in the supplied "
                     "records.")
    slot4.append("Counting table: version %s, hash %s." % (
        result["counting_table_version"],
        result["counting_table_hash"]))
    slot4.append("Diagnostic catalogue: version %s." %
                 result["diagnostic_catalogue_version"])
    if result["base_disagreement"]:
        # The called for sentences print per identification in this
        # form, never in single value form, as Section 5.8 states.
        not_stated = "not stated in the records identifying the base"
        for entry in result["called_by_base"]:
            for fact, values in (
                    ("version", entry["versions"]),
                    ("hash", entry["hashes"])):
                head = ("Table %s the base in this identification "
                        "calls for: %s: " % (fact, entry["name"]))
                if len(values) > 1:
                    slot4.append(head + "disagreement in the "
                                 "records identifying the base.")
                    for value in values:
                        slot4.append("Stated value: %s." % value)
                elif values:
                    slot4.append(head + "%s." % values[0])
                else:
                    slot4.append(head + "%s." % not_stated)
    else:
        # A called for fact in disagreement prints in the called for
        # disagreement form at Section 5.8; an agreed fact prints in
        # its single value form.
        for fact, disagreed, driving, printed in (
                ("version", result["called_version_disagreement"],
                 result["driving_called_versions"],
                 result["called_versions"]),
                ("hash", result["called_hash_disagreement"],
                 result["driving_called_hashes"],
                 result["called_hashes"])):
            if disagreed:
                slot4.append(
                    "Table %s the base calls for: disagreement in "
                    "the records identifying the base." % fact)
                for value in driving:
                    slot4.append("Stated value: %s." % value)
            elif printed:
                slot4.append("Table %s the base calls for: %s." % (
                    fact, ", ".join(printed)))
            else:
                slot4.append(
                    "Table %s the base calls for: not stated in the "
                    "records identifying the base." % fact)
    lines.append(" ".join(slot4))
    # Slot 5, the rollup line.
    if result["run_kind"] == "PRECHECK":
        lines.append("Rollup: PRECHECK %s, run by %s, %s. Exit "
                     "code: %d." % (
                         result["rollup"],
                         result["runner_name"] or "runner not named",
                         result["runner_capacity"] or
                         "capacity not stated",
                         result["exit_code"]))
    else:
        lines.append("Rollup: %s. Exit code: %d." % (
            result["rollup"], result["exit_code"]))
    # Slot 6, counts and totals.
    counts = [count for count in result["counts"]]
    if counts and any(count.entries > 0 for count in counts):
        for count in counts:
            data = count.as_dict()
            lines.append(
                "Count: %s: %d minus %d minus %d equals %d, against "
                "a minimum of %s. Round: %s. Result: %s." % (
                    count.team, count.entries,
                    count.duplicates_removed,
                    count.exempt_or_uncounted_removed,
                    count.counted_total, data["minimum"],
                    data["round"], count.result))
    else:
        lines.append("Counts: none. No count in the supplied "
                     "records decides this stage.")
    for total in result["step_totals"]:
        lines.append(
            "Step total: %d counted in this stage, against the "
            "expected step total of %d in the counting table. "
            "Round: %s. Difference: %s." % (
                total["observed"], total["expected"],
                total["round"], total["difference"]))
    if result["holders_across_rounds"] is not None:
        lines.append(
            "Holders across rounds: %d distinct holders across the "
            "rounds of this stage. This figure is holders only. It "
            "is not a team size and it is not a step total." %
            result["holders_across_rounds"])
    if result["step"] == 12:
        lines.append(
            "Build union: not computable in a one stage run. A one "
            "stage run reads no other stage as seat evidence. Step "
            "12 bound: Step 12 is in scope for this stage. Its "
            "amounts are checked as counts only, and no identity is "
            "asserted in either direction.")
    else:
        lines.append(
            "Build union: not computable in a one stage run. A one "
            "stage run reads no other stage as seat evidence. Step "
            "12 bound: Step 12 is not in scope for this stage.")
    # Slot 7, the run record line.
    lines.append("Run by: %s, acting as %s." % (
        result["runner_name"] or "runner not named",
        result["runner_capacity"] or "capacity not stated"))
    # Slot 8, the standing limits and bounds.
    lines.append("Standing limits on this rollup:")
    for line in result["coverage"]:
        text = ("Coverage: %s: claimed seats checked %d, claimed "
                "seats not checked %d, claimed seats total %d, seats "
                "presented with the form contract unsettled %d, "
                "seats outside the check %d." % (
                    line["scope"], line["checked"],
                    line["not_checked"], line["total"],
                    line["indeterminate"], line["outside"]))
        if line["total"] == 0:
            text += " coverage not applicable"
        lines.append(text)
    claimed = set(result["freshness_claimed"])
    unclaimed = [family for family in (1, 2, 3, 4)
                 if family not in claimed]
    quirk_none = result["colour"] is None
    if quirk_none or not unclaimed:
        lines.append("Unclaimed freshness families: none. Every "
                     "freshness family is claimed in the supplied "
                     "records.")
    else:
        lines.append(
            "Unclaimed freshness families: %s. Each named family "
            "is unproven and does not cap this rollup." % ", ".join(
                "family %d" % family for family in unclaimed))
    if result["freshness_not_stated"]:
        lines.append(
            "Claimed freshness families with facts not stated: %s."
            % ", ".join("family %d" % family for family in
                        result["freshness_not_stated"]))
    else:
        lines.append("Claimed freshness families with facts not "
                     "stated: none.")
    colour = result["colour"]
    if colour is not None:
        if colour["form"] == "none named":
            lines.append(
                "Colour completeness: NOT PROVEN. No audit plan or "
                "round charge is named in the supplied records. "
                "This result does not compose the rollup.")
        elif colour["form"] == "none qualifies":
            lines.append(
                "Colour completeness: NOT PROVEN. A round charge "
                "is named in the supplied records, and none of "
                "them qualifies as the colour set for this stage. "
                "This result does not compose the rollup.")
        elif colour["missing"]:
            names = " and ".join(
                label for label, _c, _s, _q in colour["suppliers"])
            source = colour["suppliers"][0][2]
            lines.append(
                "Colour completeness: NOT PROVEN. The colour set "
                "supplied by %s in %s does not stand complete in "
                "the papers supplied. This result does not compose "
                "the rollup." % (names, source))
            for missing in colour["missing"]:
                lines.append("Missing seat: %s" % missing)
        else:
            label, _c, source, _q = colour["suppliers"][0]
            describe = "the named audit plan" if label == \
                "Audit plan" else "the named round charge"
            if len(colour["suppliers"]) > 1:
                describe = "the named suppliers " + " and ".join(
                    entry[0] for entry in colour["suppliers"])
            lines.append(
                "Colour completeness: PASS on the colour set "
                "supplied by %s in %s. This result does not "
                "compose the rollup." % (describe, source))
    for defect in result["record_defects"]:
        lines.append(defect)
    lines.append("Single document: this result does not rest on a "
                 "single document.")
    lines.append("Basis: no seat in this stage rests on the "
                 "roster alone.")
    lines.append(
        "Plaid: NOT PROVEN. Version 1 of this tool computes no "
        "Plaid figure, and unpassable at Plaid is a limit of the "
        "tool, not a finding about the records supplied for this "
        "run. The pinned base supplied for this run carries no "
        "Plaid amounts the tool may use. This result does not "
        "compose the rollup where the stage does not claim a "
        "Plaid limb.")
    lines.append(
        "Counting table: PARTIAL. The counting table this run "
        "computed from stands as the table as far as swept, under "
        "S5-E42, and the full exception line recheck at encoding "
        "time stands outstanding.")
    if result["completeness_difference"]:
        totals = " and ".join(
            "%d seats" % value
            for value in result["completeness_difference"])
        lines.append(
            "A completeness difference stands in the supplied "
            "records: the records state different seat totals for "
            "this stage, %s. This result does not compose the "
            "rollup." % totals)
    for shape in (1, 2, 3):
        lines.append(
            "Chain: advisory only. Shape %d: not run. Chain "
            "results do not compose the rollup except where an "
            "ordering failure prevents proof of a claim check, "
            "and that check then stands in the blocker lines."
            % shape)
    if result["fm9"]:
        lines.append(
            "FM-9: a reduced tier is claimed for this stage and no "
            "Captain JP invocation record stands in the supplied "
            "records. The claim and the missing invocation stand "
            "side by side. This flag does not compose the rollup.")
    if result["completeness_difference"]:
        lines.append(
            "Bound: a completeness difference stands between the "
            "supplied records, which state %s seats for this "
            "stage, and the difference lands in no composing "
            "claim check." % " and ".join(
                str(value) for value in
                result["completeness_difference"]))
    for disagreement in result["claim_disagreements"]:
        lines.append(disagreement[:1].upper() + disagreement[1:])
    for entry in result["exempt_account"]:
        lines.append("Exempt account: %s" % entry)
    # Slot 9, the blockers.
    blocker_lines = _blockers(result)
    if blocker_lines:
        lines.extend(blocker_lines)
    else:
        lines.append("Blockers: none. No check stands below PASS.")
    # Slot 10, the supplied set line.
    slot10 = ["Supplied set: this run read %s." %
              _join(result["inputs_read"])]
    if result["context_files"]:
        slot10.append("Context files supplied by manifest: %s." %
                      _join(result["context_files"]))
    else:
        slot10.append("Context files supplied by manifest: none. "
                      "No context files were supplied.")
    slot10.append("Inputs supplied and ignored: %s." %
                  _join(result["inputs_ignored"]))
    if result["inputs_unread"]:
        slot10.append("Inputs supplied and unread: %s." % ", ".join(
            "%s (unread)" % name for name in result["inputs_unread"]))
    lines.append(" ".join(slot10))
    # Slot 11, the consequence.
    records = _records_to_change(result, blocker_lines)
    if records:
        records_text = ", ".join(records) + "."
    else:
        records_text = "none named. The missing fact must be " \
                       "supplied in a record named in the supplied " \
                       "set line."
    if result["run_kind"] == "PRECHECK":
        if result["rollup"] == "PASS":
            lines.append(
                "Consequence: this run is a precheck. No gate may "
                "cite it as an independent verdict. An Auditor "
                "run, or a run the Auditor commissioned and "
                "repeats or verifies, is required.")
        else:
            lines.append(
                "Consequence: this run is a precheck. This stage "
                "may not be claimed as staffed on this run. No "
                "gate may cite this run as an independent verdict. "
                "An Auditor run, or a run the Auditor commissioned "
                "and repeats or verifies, is required. Records "
                "that must change before a gate can cite a clean "
                "result: %s" % records_text)
    else:
        if result["rollup"] == "PASS":
            lines.append(
                "Consequence: this stage may be claimed as "
                "staffed on this run, and a gate may cite this "
                "run as its staffing evidence.")
        else:
            lines.append(
                "Consequence: this stage may not be claimed as "
                "staffed on this run. It may not close as a clean "
                "closure on staffing. Closure, if the Auditor "
                "allows it at all, is a qualified closure with "
                "the shortfall named in the gate record. Records "
                "that must change before a gate can cite a clean "
                "result: %s" % records_text)
    # Slot 12, the closing line.
    lines.append(result["closing_line"])
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------
# The Advanced form


def advanced_form(result):
    lines = ["Advanced form"]
    lines.append("Stage: %s. Run kind: %s." % (
        result["stage"], result["run_kind"]))
    lines.append("Runner: %s. Capacity: %s." % (
        result["runner_name"] or "runner not named",
        result["runner_capacity"] or "capacity not stated"))
    lines.append("Counting table hash as captured: %s." %
                 result["counting_table_hash_captured"])
    groups = result["manifest_groups"]
    lines.append("Supplied set manifest, by input group:")
    lines.append(
        "Group 1, roster artifact, step record and tier record: %s."
        % _join(groups["group 1"]))
    lines.append("Group 3, work products: %s."
                 % _join(groups["group 3"]))
    lines.append("Group 4, claim bearing files: %s."
                 % _join(groups["group 4"]))
    lines.append("Context files supplied by manifest: %s."
                 % _join(result["context_files"]))
    if result["stage_mismatch"]:
        lines.append("Stage named in a supplied record: %s. The "
                     "run stage is %s." % (
                         result["stage_mismatch"][0],
                         result["stage_arg"]))
    lines.append("Checks in this run:")
    for index, check in enumerate(result["checks"]):
        data = check.as_dict(index + 1)
        lines.append("Check: %s: %s: %s. Severity: %s. Rule: %s." %
                     (data["kind"], data["scope"], data["verdict"],
                      data["severity"], data["rule_reference"]))
    lines.append("Coverage account:")
    for line in result["coverage"]:
        lines.append(
            "Coverage: %s: checked %d, not checked %d, total %d, "
            "indeterminate %d, outside %d." % (
                line["scope"], line["checked"], line["not_checked"],
                line["total"], line["indeterminate"],
                line["outside"]))
    uncovered = []
    for line in result["coverage"]:
        for form in line.get("uncovered_forms", []):
            if form not in uncovered:
                uncovered.append(form)
    lines.append("Uncovered forms: %s." % _join(uncovered))
    lines.append("Uncounted appendix:")
    if result["uncounted_appendix"]:
        lines.extend(result["uncounted_appendix"])
    else:
        lines.append("none.")
    lines.append("Exempt account:")
    if result["exempt_account"]:
        lines.extend(result["exempt_account"])
    else:
        lines.append("none.")
    lines.append("Waste account:")
    if result["waste"]:
        lines.extend(result["waste"])
    else:
        lines.append("none.")
    if result["lost_spawns"]:
        lines.append("Declared lost spawns:")
        for spawn in result["lost_spawns"]:
            if spawn["date"]:
                lines.append(
                    "Lost spawn declared in %s, dated %s." % (
                        spawn["source"], spawn["date"]))
            else:
                lines.append(
                    "Lost spawn declared in %s. No incident "
                    "timing is recorded, so the declaration "
                    "stands as declaration basis only." %
                    spawn["source"])
    lines.append("Claim disagreements:")
    if result["claim_disagreements"]:
        lines.extend(result["claim_disagreements"])
    else:
        lines.append("none.")
    lines.append("Record defects:")
    if result["record_defects"]:
        lines.extend(result["record_defects"])
    else:
        lines.append("none.")
    if result["truncated_files"]:
        lines.append("The following records stand truncated: %s."
                     % ", ".join(result["truncated_files"]))
    lines.append(
        "Result mapping: PASS takes exit code 0, FAIL takes exit "
        "code 1, NOT PROVEN takes exit code 2, UNVERIFIABLE takes "
        "exit code 3, USAGE ERROR takes exit code 5, and TOOL "
        "FAULT takes exit code 6.")
    lines.append("Chain flags: shape 1 not run, shape 2 not run, "
                 "shape 3 not run.")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------
# The run


def run(argv):
    try:
        parsed = parse_arguments(argv)
    except UsageError as exc:
        # The usage error output echoes invocation text, so it is
        # sanitised on the same rule as the report forms: no line
        # break character in an echoed argument or value can write
        # a line of its own into this output either.
        sys.stdout.write("USAGE ERROR: %s\n" % _printed_value(str(exc)))
        return 5
    entry_dir = os.path.dirname(os.path.abspath(__file__))
    named = [(path, "supplied") for path in parsed["files"]]
    named += [(path, "base") for path in parsed["base_record"]]
    named += [(path, "context") for path in parsed["context"]]
    captured = muster_shell.capture_inputs(named)
    files = []
    usable = False
    for entry in captured:
        kind = muster_core.classify_file(entry)
        files.append((entry, kind))
        if entry.status == "read" and kind != "ignored":
            usable = True
    if not usable:
        # The cannot start outcome issues no report and no verdict,
        # and it prints one plain notice naming the outcome, so a
        # user at a gate does not meet a blank screen.
        sys.stderr.write(
            "Cannot start: none of the named inputs could be read, "
            "so no run started and no report is issued.\n")
        return 4
    try:
        table_data, _raw, table_hash = muster_shell.load_data_file(
            entry_dir, "counting-table.json")
        catalogue_data, _raw2, _hash2 = \
            muster_shell.load_data_file(
                entry_dir, "diagnostic-catalogue.json")
    except muster_shell.DataFault:
        sys.stdout.write("TOOL FAULT: a shipped data file cannot "
                         "be read or parsed.\n")
        return 6
    if parsed["fixture_fault"] is not None:
        raise RuntimeError("fixture fault: %s" %
                           parsed["fixture_fault"])
    params = {"stage": parsed["stage"], "runner": parsed["runner"],
              "capacity": parsed["capacity"],
              "run_kind": parsed["kind"]}
    result = muster_core.compute(files, table_data, catalogue_data,
                                 table_hash, params)
    text = _report_text(simple_form(result)) + \
        _report_text(advanced_form(result)) + \
        serialise(agentic_object(result)) + "\n"
    sys.stdout.write(text)
    sys.stdout.flush()
    return result["exit_code"]


def main():
    try:
        code = run(sys.argv[1:])
    except BrokenPipeError:
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except OSError:
            pass
        return 6
    except Exception:
        try:
            sys.stdout.write("TOOL FAULT: an uncaught fault ended "
                             "this run.\n")
            sys.stdout.flush()
        except BrokenPipeError:
            try:
                devnull = os.open(os.devnull, os.O_WRONLY)
                os.dup2(devnull, sys.stdout.fileno())
            except OSError:
                pass
            return 6
        return 6
    return code


if __name__ == "__main__":
    sys.exit(main())
