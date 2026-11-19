# Copyright: J.P. Picard aka Macro-Harder.
"""Run entry, slice 8: the single entry point of the deployable unit.

The run entry receives an invocation in the call shape at plan
section 9 (DP-11), calls the kernel module, hands the result record
to the presentation module, receives the comparison outcome, and
returns the calling side outcome the run contract states: the
printed forms, or the defect reports in their place, or a cannot
start outcome where no result record stands. Every invocation ends
in exactly one of the five outcome kinds at plan section 9.

The run entry adds no mode of its own: no batch mode, no digest and
no ordering of results stands in it, under grill G33. The form
agreement comparison unit itself stands inside the presentation
module. In a run, this file reaches the unit only through the
presentation module run comparison path, which calls the unit on
each rendered form, and holds no part of the comparison itself.
Kind selection for the test harness stands apart from the
invocation contract in the harness surface further down this file;
the run entry itself takes the DP-11 call shape alone.

Exit codes, plan section 9: code 1 names a cannot start outcome of
kind invocation, code 2 names a cannot start outcome of kind tool
failure, and no code stands for a run that produces a result record.
"""

import json
import re
import sys
from pathlib import Path

from muster_restart import kernel as _kernel_module
from muster_restart import presentation as _presentation_module

# The four verdict words at grill G24, in their closed list form.
VERDICT_WORDS = ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE")

OPEN_CASE_STATE = "OPEN CASE"
CANNOT_START_WORD = "CANNOT START"

# Runner capacities at brief section 5.2, the stated values only.
VALID_RUNNER_CAPACITIES = (
    "Auditor",
    "coordinator as precheck",
    "board member other than the stage coordinator",
)

# Outcome kind names at plan section 9, in kind order 1 to 5.
KIND_NAMES = {
    1: "completed gate run",
    2: "open case run",
    3: "precheck run under the listed not run condition",
    4: "form agreement disagreement",
    5: "cannot start run",
}

# Generated form order for comparison and for defect report order,
# plan section 10: Simple, Advanced, Agentic.
FORM_ORDER = ("Simple", "Advanced", "Agentic")

PRECHECK_LABEL = (
    "Precheck: this run was a coordinator precheck.")
PRECHECK_CONSEQUENCE = (
    "Consequence: a precheck is not a gate run and classifies "
    "no stage.")

TOOL_DEFECT_STATEMENT = (
    "This disagreement is a defect in the tool and not a finding "
    "about the stage records.")
TOOL_DEFECT_REPAIR_ACT = "a tool repair, not a restaffing act"

_CANNOT_START_FIELDS = [
    "outcome word",
    "kind",
    "invocation as received",
    "cause",
]

_EXIT_CODE_TABLE = [
    {"code": 1, "outcome": CANNOT_START_WORD, "kind": "invocation",
     "result_record": None, "verdict": None, "rollup": None},
    {"code": 2, "outcome": CANNOT_START_WORD, "kind": "tool failure",
     "result_record": None, "verdict": None, "rollup": None},
]


# ------------------------------------------------------------------
# Cannot start outcome type, DP-18: a closed field list, carrying no
# result record, no verdict and no rollup.
# ------------------------------------------------------------------

def cannot_start_outcome_fields():
    """The closed field list of the CannotStartOutcome type."""
    return list(_CANNOT_START_FIELDS)


def cannot_start_outcome_field_values():
    """One value per field of the type, none a verdict word."""
    return [
        CANNOT_START_WORD,
        "invocation",
        "the invocation as received, for diagnosis",
        "the cause, in plain words",
    ]


def make_cannot_start_outcome(kind, invocation, cause):
    """Build one CannotStartOutcome in its closed field form."""
    return {
        "outcome word": CANNOT_START_WORD,
        "kind": kind,
        "invocation as received": invocation,
        "cause": cause,
    }


# ------------------------------------------------------------------
# Exit code table and the mechanical check surfaces, plan section 9.
# ------------------------------------------------------------------

def exit_code_table():
    """The exit codes table at plan section 9, option X1."""
    return [dict(row) for row in _EXIT_CODE_TABLE]


def cannot_start_codes():
    """The set of codes naming cannot start outcomes: 1 and 2."""
    return [row["code"] for row in _EXIT_CODE_TABLE]


def verdict_or_rollup_codes():
    """Codes associated with verdicts or rollups: the empty set."""
    return []


def codes_for_result_producing_runs():
    """No code stands for a run that produces a result record."""
    return []


def code_table_position_words():
    """Words in outcome, verdict or rollup positions in the table."""
    return [CANNOT_START_WORD]


def outcome_type_position_words():
    """Words in outcome positions in the CannotStartOutcome type."""
    return [CANNOT_START_WORD]


def form_template_position_words():
    """Words in verdict or rollup positions in the form templates."""
    return list(VERDICT_WORDS) + [OPEN_CASE_STATE]


def consumer_classification(outcome_word):
    """Calling side mapping for an outcome word, grill G33.

    A cannot start outcome maps to no verdict word at all; the
    consumer classification for it is None, distinct from PASS,
    from FAIL and from every verdict word.
    """
    if outcome_word == CANNOT_START_WORD:
        return None
    if outcome_word in VERDICT_WORDS:
        return outcome_word
    return None


def consumer_record(outcome_word):
    """How the calling side records an outcome, grill G33."""
    if outcome_word == CANNOT_START_WORD:
        return "a call that did not run"
    return "a completed run"


# ------------------------------------------------------------------
# Outcome construction.
# ------------------------------------------------------------------

def _base_outcome(kind_number):
    return {
        "kind": KIND_NAMES[kind_number],
        "kind_number": kind_number,
        "result_record": None,
        "printed_forms": [],
        "defect_reports": [],
        "cannot_start_outcome": None,
        "rollup": None,
        "verdict": None,
        "label": None,
        "consequence_line": None,
        "recorded_as": "a completed run",
        "exit_code": 0,
    }


def _cannot_start(kind, invocation, cause):
    outcome = _base_outcome(5)
    outcome["cannot_start_outcome"] = make_cannot_start_outcome(
        kind, invocation, cause)
    outcome["recorded_as"] = "a call that did not run"
    outcome["exit_code"] = 1 if kind == "invocation" else 2
    return outcome


def _rollup_word(result_record):
    """The rollup word of a result record, or None where none stands."""
    if not isinstance(result_record, dict):
        return None
    fields = result_record.get("fields")
    if isinstance(fields, dict):
        value = fields.get("12")
        if isinstance(value, str) and value in VERDICT_WORDS:
            return value
    value = result_record.get("rollup")
    if isinstance(value, str) and value in VERDICT_WORDS:
        return value
    return None


def _is_open_case(result_record):
    if not isinstance(result_record, dict):
        return False
    if result_record.get("open_case"):
        return True
    fields = result_record.get("fields")
    if isinstance(fields, dict):
        value = fields.get("12")
        if isinstance(value, str) and OPEN_CASE_STATE in value:
            return True
        if isinstance(value, str) and value.startswith(
                "Rollup not stated. This run meets an open case"):
            return True
        field4 = fields.get("4")
        if isinstance(field4, dict) and (
                field4.get("base_position") == OPEN_CASE_STATE):
            return True
    for entry in result_record.get("check_results") or []:
        if isinstance(entry, dict) and (
                entry.get("verdict_position") == OPEN_CASE_STATE):
            return True
    return False


def _is_precheck(result_record, invocation):
    if isinstance(invocation, dict) and (
            invocation.get("run_kind") == "precheck"):
        return True
    if not isinstance(result_record, dict):
        return False
    fields = result_record.get("fields")
    if isinstance(fields, dict):
        field2 = fields.get("2")
        if isinstance(field2, dict) and (
                field2.get("run_kind") == "precheck"):
            return True
    return result_record.get("run_kind") == "precheck"


def _compare_forms(result_record, forms):
    """Reach the comparison through the presentation run path.

    The comparison unit takes exactly two inputs, a result record
    and one generated form, and returns one output, a DefectReport
    or no defect. Its only callers stand as the presentation module
    in a run and the test harness in test custody. The presentation
    module in a run calls the unit through its own run comparison
    path, compare_generated_forms, which takes the result record
    and the rendered forms and returns one DefectReport for each
    disagreement across every form. The run entry reaches that
    path directly here and calls the unit itself nowhere in a run.
    The path stands called with no fallback: where it does not
    stand or does not run, the call raises and the run finishes as
    a tool defect outcome in _finish_started_run, with no form
    printed and no clean outcome returned.
    """
    reports = _presentation_module.compare_generated_forms(
        result_record, forms)
    collected = []
    for entry in reports:
        if isinstance(entry, dict):
            collected.append(dict(entry))
    return collected


def _finish_started_run(result_record, invocation):
    """Render, compare, and return the outcome for a started run."""
    try:
        forms = _presentation_module.render_forms(result_record)
        reports = _compare_forms(result_record, forms)
    except Exception as exc:
        outcome = _base_outcome(4)
        outcome["result_record"] = result_record
        outcome["defect_reports"] = [{
            "form": None,
            "element": None,
            "defect_field": "UNVERIFIABLE",
            "tool_defect_statement": (
                "The tool failed after a result record stood: %s"
                % (exc,)),
            "repair_act": TOOL_DEFECT_REPAIR_ACT,
        }]
        return outcome
    if reports:
        outcome = _base_outcome(4)
        outcome["result_record"] = result_record
        outcome["printed_forms"] = []
        outcome["defect_reports"] = reports
        outcome["rollup"] = None
        return outcome
    if _is_open_case(result_record):
        outcome = _base_outcome(2)
        outcome["result_record"] = result_record
        outcome["printed_forms"] = forms
        outcome["rollup"] = None
        return outcome
    if _is_precheck(result_record, invocation):
        outcome = _base_outcome(3)
        outcome["result_record"] = result_record
        outcome["printed_forms"] = forms
        outcome["rollup"] = None
        outcome["label"] = PRECHECK_LABEL
        outcome["consequence_line"] = PRECHECK_CONSEQUENCE
        return outcome
    outcome = _base_outcome(1)
    outcome["result_record"] = result_record
    outcome["printed_forms"] = forms
    rollup = _rollup_word(result_record)
    outcome["rollup"] = rollup
    outcome["verdict"] = rollup
    return outcome


# ------------------------------------------------------------------
# Comparison case surface, group P8-T2 form: a case stating its
# disagreements, compared over every form, one report each. This
# surface stands in the harness form for that group: it renders the
# forms from the fixture result record standing behind the case
# family, corrupts the named element in each named form in the
# manner the test custody pair names, and calls the comparison
# unit on each form in test custody. Every report it returns is a
# report the unit itself returned; no report is built here.
# ------------------------------------------------------------------

def _case_fixture(name):
    path = (Path(__file__).resolve().parent.parent
            / "tests_restart" / "fixtures" / "F1" / name)
    return json.loads(path.read_text(encoding="utf-8"))


def _corrupt_text_form(form_name, generated_form, element, pair):
    """Corrupt one element of a text form, custody pair manner.

    The custody pair manner replaces the value the form carries
    for the named element with a differing value for that same
    element, as the pair replaces the counts figure in the counts
    lines. The counts lines take the pair own replacement where
    the pair names that element. The rollup line takes a differing
    rollup word in place of the word the form carries. Any other
    element takes a differing standing appended to the line that
    carries that element in the named form.
    """
    if element == pair.get("generated_form_element"):
        before = pair.get("value_in_generated_form_before_corruption")
        after = pair.get("value_in_generated_form_after_corruption")
        if before and after and before in generated_form:
            return generated_form.replace(before, after, 1)
    if element == "rollup line":
        match = re.search(
            r"Rollup: (PASS|FAIL|NOT PROVEN|UNVERIFIABLE)",
            generated_form)
        if match:
            word = match.group(1)
            other = "FAIL" if word != "FAIL" else "PASS"
            return (generated_form[:match.start()]
                    + "Rollup: " + other
                    + generated_form[match.end():])
    lines = generated_form.splitlines()
    if form_name == "Advanced":
        prefix = "%s: " % element
        for index, line in enumerate(lines):
            if line.startswith(prefix):
                lines[index] = line + " corrupted standing"
                return "\n".join(lines)
    else:
        elements = list(_presentation_module.CANONICAL_ELEMENTS)
        record_is_precheck = False
        position = 0
        target = None
        for name in elements:
            if name == "precheck not yet run section" and (
                    not record_is_precheck):
                continue
            if name == element:
                target = position
                break
            position += 1
        if target is not None and target < len(lines):
            lines[target] = lines[target] + " corrupted standing"
            return "\n".join(lines)
    return generated_form + "\ncorrupted standing"


def _corrupt_generated_form(form_name, generated_form, element, pair):
    """The named form with the named element corrupted."""
    if isinstance(generated_form, dict):
        corrupted = json.loads(json.dumps(generated_form))
        entries = corrupted.get("elements")
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and (
                        entry.get("name") == element):
                    entry["rollup"] = (
                        "FAIL" if entry.get("rollup") != "FAIL"
                        else "PASS")
                    total = entry.get("counted_total")
                    entry["counted_total"] = (
                        total + 1 if isinstance(total, int) else 999)
        if element == "rollup line":
            corrupted["rollup"] = (
                "FAIL" if corrupted.get("rollup") != "FAIL"
                else "PASS")
        return corrupted
    return _corrupt_text_form(
        form_name, generated_form, element, pair)


def run_comparison_case(case):
    """Run the comparison over the forms a case names.

    The case states its disagreements as form and element pairs.
    The forms stand rendered from the fixture result record
    standing behind the case family, at fixtures/F1/
    render_result_record.json. Each named element stands
    corrupted in its named form in the manner the test custody
    pair at fixtures/F1/test_custody_pair.json names, and the
    comparison unit stands called on each named form with the
    fixture record. One DefectReport stands for each disagreement,
    the report the unit returns for that form, the comparison
    continues over the remaining forms after a first disagreement,
    and no form is printed in that run. The completion standing
    rests on the unit having been called over every named form.
    """
    disagreements = []
    if isinstance(case, dict):
        disagreements = case.get("disagreements") or []
    order = {name: index for index, name in enumerate(FORM_ORDER)}
    pairs = [(entry.get("form"), entry.get("element"))
             for entry in disagreements if isinstance(entry, dict)]
    pairs.sort(key=lambda pair: order.get(pair[0], len(order)))
    record = _case_fixture("render_result_record.json")
    pair_fixture = _case_fixture("test_custody_pair.json")
    forms = _presentation_module.render_forms(record)
    reports = []
    called_forms = []
    for form_name, element in pairs:
        if form_name not in forms:
            continue
        corrupted = _corrupt_generated_form(
            form_name, forms[form_name], element, pair_fixture)
        report = _presentation_module.form_agreement_compare(
            record, corrupted)
        called_forms.append(form_name)
        if report is not None:
            entry = dict(report)
            entry["form"] = form_name
            reports.append(entry)
    named_forms = {form_name for form_name, _element in pairs}
    completed = all(
        form_name in called_forms for form_name in named_forms)
    return {
        "defect_reports": reports,
        "printed_forms": [],
        "comparison_completed_all_forms": completed,
    }


# ------------------------------------------------------------------
# Harness kind selection, the harness form at group P8-T4, standing
# apart from the invocation contract: a harness invocation stating
# an outcome kind number returns that kind in its own form, each
# kind built through the real module seams. This surface is the
# harness form it is named as. It is not the run entry: the run
# entry below takes the DP-11 call shape alone and reads no kind
# selection key of any kind.
# ------------------------------------------------------------------

def _kind_outcome(kind_number):
    if kind_number == 5:
        return _cannot_start(
            "invocation", {"outcome_kind": kind_number},
            "the invocation states a cannot start outcome kind")
    if kind_number == 4:
        record = _kernel_module.compute_result({
            "runner_identity": "run entry",
            "runner_capacity": "Auditor",
            "stage_judged": "kind selection",
            "tier": "not stated",
            "supplied_files": [],
            "pinned_base": "base tables v1",
        })
        outcome = _base_outcome(4)
        outcome["result_record"] = record
        outcome["printed_forms"] = []
        outcome["defect_reports"] = run_comparison_case({
            "disagreements": [
                {"form": "Simple", "element": "counts lines"}],
        })["defect_reports"]
        return outcome
    if kind_number == 2:
        record = _kernel_module.compute_result({
            "runner_identity": "run entry",
            "runner_capacity": "Auditor",
            "stage_judged": "kind selection",
            "tier": "not stated",
            "supplied_files": [],
            "pinned_base": "words alone",
            "open_case": "words alone base",
        })
        outcome = _base_outcome(2)
        outcome["result_record"] = record
        outcome["rollup"] = None
        return outcome
    if kind_number == 3:
        record = _kernel_module.compute_result({
            "runner_identity": "run entry",
            "runner_capacity": "coordinator as precheck",
            "run_kind": "precheck",
            "stage_judged": "kind selection",
            "tier": "not stated",
            "supplied_files": [],
            "pinned_base": "base tables v1",
        })
        outcome = _base_outcome(3)
        outcome["result_record"] = record
        outcome["rollup"] = None
        outcome["label"] = PRECHECK_LABEL
        outcome["consequence_line"] = PRECHECK_CONSEQUENCE
        return outcome
    record = _kernel_module.compute_result({
        "runner_identity": "run entry",
        "runner_capacity": "Auditor",
        "stage_judged": "kind selection",
        "tier": "not stated",
        "supplied_files": [],
        "pinned_base": "base tables v1",
    })
    # The finished run stands returned as it finished. Where the
    # comparison produced defect reports, the outcome is the kind 4
    # outcome the run produced, with its reports standing and no
    # form printed: a result producing path never discards a
    # comparison report and never renders forms in its place.
    return _finish_started_run(record, {"run_kind": "gate run"})


def harness_kind_invocation(invocation):
    """The harness form for outcome kind selection, group P8-T4.

    A harness invocation stating an outcome kind number, in a
    mapping under the outcome_kind key or as the number itself,
    returns that outcome kind in its own form, each kind built
    through the real module seams by _kind_outcome. This surface
    stands apart from the invocation contract: the key it reads
    stands in no RunInput field, and the run entry itself,
    run_invocation, does not read it.
    """
    kind_number = None
    if isinstance(invocation, dict):
        try:
            kind_number = int(invocation.get("outcome_kind"))
        except (TypeError, ValueError):
            kind_number = None
    elif isinstance(invocation, int):
        kind_number = invocation
    if kind_number in KIND_NAMES:
        return _kind_outcome(kind_number)
    return _cannot_start(
        "invocation", invocation,
        "the harness invocation states no outcome kind in the "
        "harness form")


# ------------------------------------------------------------------
# The run entry itself.
# ------------------------------------------------------------------

def _entry_has_no_group(entry):
    if not isinstance(entry, dict):
        return True
    if entry.get("input_group"):
        return False
    if entry.get("group"):
        return False
    groups = entry.get("groups")
    if isinstance(groups, list) and groups:
        return False
    return True


def _cannot_start_cause(invocation):
    """Return a cannot start outcome for an invocation, or None.

    Cases at plan section 9: a runner capacity outside the values
    at brief section 5.2, a supplied file entry carrying no input
    group, and a tool failure before a result record stands.
    """
    if not isinstance(invocation, dict):
        return _cannot_start(
            "invocation", invocation,
            "the invocation does not state a run input in the "
            "RunInput form")
    if invocation.get("tool_failure_before_result"):
        return _cannot_start(
            "tool failure", invocation,
            "a failure of the tool itself before a result record "
            "stands")
    capacity = invocation.get("runner_capacity")
    if capacity is not None and capacity not in VALID_RUNNER_CAPACITIES:
        return _cannot_start(
            "invocation", invocation,
            "the runner capacity stands outside the values at "
            "brief section 5.2, so the invocation does not state "
            "a run input in the RunInput form")
    single = invocation.get("supplied_file_entry")
    if single is not None and _entry_has_no_group(single):
        return _cannot_start(
            "invocation", invocation,
            "a supplied file entry carries no input group, so the "
            "invocation does not state a run input in the RunInput "
            "form")
    supplied = invocation.get("supplied_files")
    if isinstance(supplied, list):
        for entry in supplied:
            if _entry_has_no_group(entry):
                return _cannot_start(
                    "invocation", invocation,
                    "a supplied file entry carries no input group, "
                    "so the invocation does not state a run input "
                    "in the RunInput form")
    return None


def run_invocation(invocation):
    """The single entry point: one invocation, one outcome kind.

    Receives an invocation in the call shape at plan section 9,
    calls the kernel module, hands the result record to the
    presentation module, receives the comparison outcome, and
    returns the calling side outcome: the printed forms, or the
    defect reports in their place, or a cannot start outcome where
    no result record stands.

    The invocation stands in the DP-11 call shape alone: exactly
    the RunInput fields. No kind selection key stands in that
    shape, and none is read here; kind selection for the test
    harness stands apart in harness_kind_invocation above.
    """
    blocked = _cannot_start_cause(invocation)
    if blocked is not None:
        return blocked
    try:
        result_record = _kernel_module.compute_result(invocation)
    except Exception as exc:
        return _cannot_start(
            "tool failure", invocation,
            "a failure of the tool itself before a result record "
            "stands: %s" % (exc,))
    if result_record is None:
        return _cannot_start(
            "tool failure", invocation,
            "a failure of the tool itself before a result record "
            "stands")
    return _finish_started_run(result_record, invocation)


# ------------------------------------------------------------------
# Command line reading of the named records, the S16U-01 cure.
#
# The kernel surface that reads content is kernel.compute_result
# with a structured RunInput: a roster mapping carrying its seats
# in the SeatEntry form at brief section 5.4 shape 5, and its
# board seats apart. The command line states paths and groups
# only, so this section reads each named roster record's content
# and assembles that roster mapping from the content read, in the
# two forms the governing texts state:
#
# 1. The structured form: a roster record whose content is a JSON
#    document carrying seats, and board seats where it states
#    them, in the shape 5 field form. The field contract is the
#    recommended structured form the brief publishes at grill G6.
# 2. The markdown roster form in use, which grill G6 states
#    version 1 reads: seat lines standing as bullet lines under a
#    team heading, each line naming its seat before its first
#    colon. A seat line states no full identifier, so its holder
#    value is carried with its kind named as not recorded, under
#    grill G6: it counts as an entry the roster names, and it
#    proves no distinct holder. A line under a heading stating
#    uncounted seats carries the uncounted counting position the
#    heading states. A seat line that states its work product in
#    the Paper statement form the rosters in use carry, naming
#    the product path after the words Paper:, carries that path
#    in its work products, in the SeatEntry form at brief
#    section 5.4 shape 5, as the structured form carries it: the
#    product path as named in the roster record, and nothing
#    about the product beyond the path the statement names.
#    Where the words after Paper: do not stand as a path, the
#    statement names no product in that form and none is
#    assembled from it. No
#    other content is read into the kernel input: no board seat
#    is assembled from a markdown roster, because no markdown
#    line form states a board holder, and no claim, coordinator
#    identity or other structured key is assembled from prose,
#    because no line form for those keys stands in the brief or
#    the plan. No selection record and no author record is
#    assembled from a markdown roster either, because no line
#    form for either record stands in the brief, the plan or
#    the rosters in use: the selection record stands only in
#    the structured form, and an author record stands, where
#    one stands, inside a work product itself, which this
#    section does not read.
# ------------------------------------------------------------------

def _parse_roster_content(text, path):
    """Assemble the roster mapping from one roster record's content.

    Returns the mapping, or None where the content states no seat
    in either stated form.
    """
    stripped = text.strip()
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
        except ValueError:
            data = None
        if isinstance(data, dict) and (
                isinstance(data.get("seats"), list)
                or isinstance(data.get("board_seats"), list)):
            roster = dict(data)
            roster.setdefault("file", path)
            return roster
    seats = []
    team = None
    uncounted = False
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line.startswith("- "):
            heading = line.lstrip("#").strip().rstrip(":")
            lowered = heading.lower()
            if "team" in lowered:
                candidate = heading.split("(")[0].strip()
                if candidate.lower().endswith("team"):
                    team = candidate
            if "uncounted" in lowered or "exempt" in lowered:
                uncounted = True
            elif line.startswith("#") or line.endswith(":"):
                uncounted = False
            continue
        body = line[2:].strip()
        label = body.split(":", 1)[0].strip().rstrip(",")
        if not label:
            continue
        seat = {
            "seat_key": "seat-%d" % (len(seats) + 1),
            "role_name": label,
            "agent_identifier": label,
            "agent_kind": "not recorded",
            "counting_position": (
                "uncounted at this step" if uncounted
                else "counted in base"),
            "roster_line_location": "%s line %d" % (path, number),
        }
        marker = body.find("Paper: ")
        if marker != -1:
            words = body[marker + len("Paper: "):].split()
            if words:
                product = words[0].rstrip(".,;)")
                if product and "/" in product:
                    seat["work_products"] = [product]
        if team is not None:
            seat["team"] = team
        seats.append(seat)
    if not seats:
        return None
    return {"file": path, "seats": seats}


def _assemble_content(invocation):
    """Read the named records' content into the invocation.

    Only the roster mapping is assembled, from a supplied file
    whose name names it as the roster record, and only where the
    invocation carries no roster already. A named file that does
    not stand on disk is left as named; its standing is the
    kernel's receipt and coverage matter, not this section's.
    """
    if "roster" in invocation:
        return invocation
    for entry in invocation.get("supplied_files") or []:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if not path or "roster" not in Path(str(path)).name.lower():
            continue
        candidate = Path(str(path))
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        roster = _parse_roster_content(text, str(path))
        if roster is not None:
            invocation["roster"] = roster
            break
    return invocation


# The option names the call shape at plan section 9 states, each
# carrying one value. No other name and no positional stands in
# that shape.
_KNOWN_OPTIONS = (
    "--runner-identity", "--runner-capacity", "--stage", "--build",
    "--tier", "--pinned-base", "--run-kind", "--supplied-file",
)

_OPTION_FIELDS = {
    "--runner-identity": "runner_identity",
    "--runner-capacity": "runner_capacity",
    "--stage": "stage_judged",
    "--build": "build",
    "--tier": "tier",
    "--pinned-base": "pinned_base",
    "--run-kind": "run_kind",
}


def _parse_command_line(args):
    """Parse the command line under the plan section 9 call shape.

    Returns the invocation, or a cannot start outcome of kind
    invocation where the line carries a name or a positional the
    contract does not state, or a stated name carrying no value:
    no argument is silently dropped, under the S16U-06 cure.
    """
    invocation = {"supplied_files": []}
    index = 0
    while index < len(args):
        name = args[index]
        if name not in _KNOWN_OPTIONS:
            if name.startswith("--"):
                cause = (
                    "the invocation carries the name %s, which the "
                    "call shape at plan section 9 does not state, "
                    "so the invocation does not state a run input "
                    "in the RunInput form" % name)
            else:
                cause = (
                    "the invocation carries the positional "
                    "argument %s, which the call shape at plan "
                    "section 9 does not state, so the invocation "
                    "does not state a run input in the RunInput "
                    "form" % name)
            return None, _cannot_start("invocation", list(args), cause)
        if index + 1 >= len(args):
            return None, _cannot_start(
                "invocation", list(args),
                "the invocation states the name %s with no value, "
                "so the invocation does not state a run input in "
                "the RunInput form" % name)
        value = args[index + 1]
        if name == "--supplied-file":
            path, _, group = value.partition(":")
            entry = {"path": path}
            if group:
                entry["group"] = group
            invocation["supplied_files"].append(entry)
        else:
            invocation[_OPTION_FIELDS[name]] = value
        index += 2
    return invocation, None


def main(argv=None):
    """Command form: one stage per invocation, command muster-lite.

    Arguments state exactly the RunInput fields at plan section 9.
    The outcome prints as one JSON document; the process exit code
    stands as the run contract states, 1 or 2 for a cannot start
    outcome and 0 for a run that produces a result record.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    invocation, blocked = _parse_command_line(args)
    if blocked is not None:
        outcome = blocked
    else:
        outcome = run_invocation(_assemble_content(invocation))
    record = outcome["result_record"]
    printable = {
        "kind": outcome["kind"],
        "result_record": record,
        "printed_forms": outcome["printed_forms"],
        "defect_reports": outcome["defect_reports"],
        "cannot_start_outcome": outcome["cannot_start_outcome"],
        "rollup": outcome["rollup"],
        "recorded_as": outcome["recorded_as"],
        "exit_code": outcome["exit_code"],
    }
    print(json.dumps(printable, sort_keys=True, default=str))
    return outcome["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
