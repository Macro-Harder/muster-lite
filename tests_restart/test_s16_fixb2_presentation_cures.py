# Copyright: J.P. Picard aka Macro-Harder.
"""Step 16 Round 2 Fix B2 cure tests: presentation.py only.

Findings cured: S16A21-01 (the printed forms state the missing
files the result record carries, in the Simple, Advanced and
Agentic forms), the forms limb of S16A21-02 (the forms print the
stage count the result record carries, and where no team count
stands the forms state that plainly instead of printing a zero
count team line as the count; the gate form and the open case
form on the same records state the same missing seats standing),
S16A21-03 (where check 1 is UNVERIFIABLE because the shipped
tables hold no Layer 2 or mapping rows for the stage, the Simple
gloss and the repair entry state that true cause and name no
seating cure for it), and the forms limb of S16A21-04 (where the
roster record itself is absent, the forms state that absence
instead of printing a missing seats none line).

Cure test shapes are those Auditor 2 states at S16A22-01,
S16A22-02 (forms limb) and S16A22-03: presentation level nodes
on records carrying the standings the findings rest on, with the
expected values stated in the tests. Each cure test states the
concrete wrong output it fails on before the cure.
"""

import importlib
import json


def _presentation():
    return importlib.import_module("muster_restart.presentation")


MISSING_FILE = "design/restart/steps/step-16-gate-record.md"
SEATING_CURE = (
    "seat a distinct agent, holding no other seat in the stage, "
    "in the named seat, and record that holding in the roster "
    "record")
ABSENCE_WORDS = (
    "no team count stands for Step 15, because no Layer 2 row "
    "stands for Step 15 and no mapping row stands for Step 15")
TABLE_CAUSE = (
    "the shipped tables hold no Layer 2 row or mapping row "
    "for the stage")


def _no_derivation_record():
    """A contract form record in the Step 15 no derivation shape.

    Field 5 carries a missing file. Field 7 carries a stage
    count of 56 counted from 56 entries beside a single Design
    team count at 0, and the field 7 absence words stating that
    no team count stands for the stage because no Layer 2 row
    and no mapping row stand for it. Check 1 stands
    UNVERIFIABLE on that missing fact, field 11 carries the
    check 1 missing seat entry with its seating cure act, and
    field 12 stands UNVERIFIABLE.
    """
    return {
        "fields": {
            "2": {"run_kind": "gate run",
                  "runner_identity": "runner-a",
                  "runner_capacity": "Auditor"},
            "3": {"stage_judged": "Step 15", "tier_applied": "Low"},
            "4": {"pinned_base": "base tables v1",
                  "base_position": "identified"},
            "5": {"coverage": {
                      "records_needed": 6, "records_supplied": 5,
                      "records_read": 5},
                  "receipt": [], "ignored_inputs": [],
                  "missing_files": [MISSING_FILE]},
            "7": {"team_counts": [
                      {"team": "Design team", "counted_total": 0,
                       "entries_counted": 0, "duplicates_removed": 0,
                       "exempt_or_uncounted_removed": 0,
                       "required_count": 2, "slack": -2}],
                  "stage_count": {
                      "entries_counted": 56, "counted_total": 56,
                      "duplicates_removed": 0,
                      "exempt_or_uncounted_removed": 0,
                      "required_count": 0},
                  "absence_words": ABSENCE_WORDS},
            "11": {"missing_seats": [
                       {"entry_kind": "missing seat", "check": 1,
                        "rule": "brief section 5.4 shape 15",
                        "evidence": {"file": "roster record",
                                     "seat": "Design team"},
                        "cure_act": SEATING_CURE}],
                   "duplicate_holdings": [], "unproven_seats": []},
            "12": "UNVERIFIABLE",
        },
        "check_results": [
            {"check": 1, "verdict": "UNVERIFIABLE",
             "verdict_position": "UNVERIFIABLE",
             "missing_fact": (
                 "the Layer 2 row for Step 15 and the mapping "
                 "row for Step 15")},
            {"check": 4, "verdict": "PASS",
             "verdict_position": "PASS"},
        ],
    }


def _roster_absent_record():
    """A contract form record for a stage with no roster record.

    The roster resting checks name the absent roster record for
    the stage as their missing fact, field 11 carries no repair
    entry, and field 12 stands UNVERIFIABLE.
    """
    record = _no_derivation_record()
    record["fields"]["3"] = {"stage_judged": "Step 99",
                             "tier_applied": "Low"}
    record["fields"]["5"] = {
        "coverage": {}, "receipt": [], "ignored_inputs": [],
        "missing_files": []}
    record["fields"]["7"] = {
        "team_counts": [],
        "stage_count": {"entries_counted": 0, "counted_total": 0,
                        "duplicates_removed": 0,
                        "exempt_or_uncounted_removed": 0,
                        "required_count": 0},
        "absence_words": None}
    record["fields"]["11"] = {
        "missing_seats": [], "duplicate_holdings": [],
        "unproven_seats": []}
    record["check_results"] = [
        {"check": number, "verdict": "UNVERIFIABLE",
         "verdict_position": "UNVERIFIABLE",
         "missing_fact": "the absent roster record for the stage"}
        for number in (1, 2, 3)]
    return record


def _counts_line(text):
    lines = [line for line in text.splitlines()
             if "counted, from" in line or "team count" in line]
    assert lines, "no counts line stands in %r" % text
    return " ".join(lines)


# S16A21-01, S16A22-01. Wrong output: the absent file name at 0
# mentions in all three printed forms, while the result record
# names it in its missing_files list.

def test_s16a21_01_simple_states_missing_file_by_name():
    forms = _presentation().render_forms(_no_derivation_record())
    assert MISSING_FILE in forms["Simple"], (
        "WRONG OUTPUT S16A21-01: Simple form %r naming no "
        "missing file where the record missing_files list "
        "carries %s" % (forms["Simple"], MISSING_FILE))
    assert "Missing files:" in forms["Simple"]


def test_s16a21_01_advanced_states_missing_file_by_name():
    forms = _presentation().render_forms(_no_derivation_record())
    assert MISSING_FILE in forms["Advanced"], (
        "WRONG OUTPUT S16A21-01: Advanced form naming no "
        "missing file where the record carries %s" % MISSING_FILE)
    assert "Missing files:" in forms["Advanced"]


def test_s16a21_01_agentic_carries_missing_files_list():
    forms = _presentation().render_forms(_no_derivation_record())
    assert forms["Agentic"].get("missing_files") == [MISSING_FILE], (
        "WRONG OUTPUT S16A21-01: Agentic form carrying "
        "missing_files %r where the record carries [%s]"
        % (forms["Agentic"].get("missing_files"), MISSING_FILE))
    assert MISSING_FILE in json.dumps(forms["Agentic"])


# S16A21-02 forms limb, S16A22-02 forms limb. Wrong output: the
# Simple and Advanced forms print only the Design team 0 line
# and never the stage count 56 of 56 the record carries, and
# every Agentic element carries entries counted 0.

def test_s16a21_02_simple_prints_stage_count_and_no_team_count():
    forms = _presentation().render_forms(_no_derivation_record())
    line = _counts_line(forms["Simple"])
    assert "56 counted, from 56 entries counted" in line, (
        "WRONG OUTPUT S16A21-02: Simple counts line %r carrying "
        "no stage count where the record stage count stands at "
        "56 counted from 56 entries" % line)
    assert "no team count stands" in line, (
        "WRONG OUTPUT S16A21-02: Simple counts line %r stating "
        "nothing plainly where no team count stands" % line)
    assert "Design team: 0 counted" not in forms["Simple"], (
        "WRONG OUTPUT S16A21-02: Simple form printing the zero "
        "count team line %r as the count" % line)


def test_s16a21_02_advanced_prints_stage_count_and_no_team_count():
    forms = _presentation().render_forms(_no_derivation_record())
    line = _counts_line(forms["Advanced"])
    assert "56 counted, from 56 entries counted" in line, (
        "WRONG OUTPUT S16A21-02: Advanced counts line %r "
        "carrying no stage count" % line)
    assert "no team count stands" in line
    assert "Design team: 0 counted" not in forms["Advanced"]


def test_s16a21_02_agentic_carries_stage_count():
    forms = _presentation().render_forms(_no_derivation_record())
    agentic = forms["Agentic"]
    assert agentic.get("stage_count", {}).get("counted_total") == 56, (
        "WRONG OUTPUT S16A21-02: Agentic form carrying stage "
        "count %r where the record carries 56"
        % agentic.get("stage_count"))
    assert agentic["stage_count"]["entries_counted"] == 56
    for element in agentic["elements"]:
        assert element["counted_total"] == 56, (
            "WRONG OUTPUT S16A21-02: Agentic element %s carrying "
            "counted total %r where the record stage count "
            "stands at 56" % (element["name"],
                              element["counted_total"]))
        assert element["entries_counted"] == 56


def test_s16a21_02_gate_and_open_case_state_same_missing_seats():
    # The same records rendered as a gate run and as an open
    # case run state the same missing seats standing: where no
    # team count stands, no missing seat standing rests on a
    # team count in either form.
    presentation = _presentation()
    gate = presentation.render_forms(_no_derivation_record())
    open_record = _no_derivation_record()
    open_record["fields"]["4"] = {
        "pinned_base": "words alone", "base_position": "OPEN CASE"}
    open_record["fields"]["12"] = (
        "Rollup not stated. This run meets an open case, named "
        "here, and the single result for that case stands open.")
    open_case = presentation.render_forms(open_record)
    for forms in (gate, open_case):
        assert "Missing seats: Design team" not in forms["Simple"], (
            "WRONG OUTPUT S16A21-02: a form stating a Design "
            "team seat missing where no team count stands for "
            "the stage")
        assert "Missing seats: Design team" not in forms["Advanced"]


def test_s16a21_02_team_count_prints_where_one_stands():
    # Guard: where a team count stands and no absence words
    # stand, the team counts line prints as before beside the
    # stage count.
    record = _no_derivation_record()
    record["fields"]["7"] = {
        "team_counts": [
            {"team": "Design team", "counted_total": 3,
             "entries_counted": 3, "duplicates_removed": 0,
             "exempt_or_uncounted_removed": 0, "required_count": 2,
             "slack": 1}],
        "stage_count": {"entries_counted": 3, "counted_total": 3,
                        "duplicates_removed": 0,
                        "exempt_or_uncounted_removed": 0,
                        "required_count": 2},
        "absence_words": None}
    record["fields"]["11"] = {
        "missing_seats": [], "duplicate_holdings": [],
        "unproven_seats": []}
    forms = _presentation().render_forms(record)
    assert "Design team: 3 counted, from 3 entries counted" \
        in forms["Simple"]
    assert "3 counted, from 3 entries counted" in forms["Advanced"]


# S16A21-03, S16A22-03. Wrong output: the Simple gloss blames
# the supplied set, reading that the records needed cannot be
# read or do not stand in the supplied set, and the Advanced
# full repair list prescribes seating a distinct agent for
# check 1, a cure that adds no table row.

def test_s16a21_03_simple_gloss_states_table_row_cause():
    forms = _presentation().render_forms(_no_derivation_record())
    rollup = [line for line in forms["Simple"].splitlines()
              if line.startswith("Rollup:")]
    assert len(rollup) == 1
    assert "do not stand in the supplied set" not in rollup[0], (
        "WRONG OUTPUT S16A21-03: Simple rollup line %r blaming "
        "the supplied set where check 1 rests on rows missing "
        "from the shipped tables" % rollup[0])
    assert TABLE_CAUSE in rollup[0], (
        "WRONG OUTPUT S16A21-03: Simple rollup line %r stating "
        "no table row cause" % rollup[0])


def test_s16a21_03_repair_entry_names_no_seating_cure():
    forms = _presentation().render_forms(_no_derivation_record())
    assert SEATING_CURE not in forms["Advanced"], (
        "WRONG OUTPUT S16A21-03: Advanced form prescribing the "
        "seating cure for a check 1 table row absence")
    assert "seat a distinct agent" not in forms["Advanced"]
    repair = [line for line in forms["Advanced"].splitlines()
              if line.startswith("full repair list:")]
    assert len(repair) == 1
    assert TABLE_CAUSE in repair[0], (
        "WRONG OUTPUT S16A21-03: full repair list %r stating no "
        "table row cause for the check 1 entry" % repair[0])
    assert TABLE_CAUSE in forms["Simple"] or \
        "no team count stands" in forms["Simple"]


# S16A21-04 forms limb, S16A22-04 forms limb. Wrong output: the
# Simple form prints "Missing seats: none." for a stage whose
# roster record itself is absent.

def test_s16a21_04_forms_state_roster_record_absent():
    forms = _presentation().render_forms(_roster_absent_record())
    for name in ("Simple", "Advanced"):
        assert "Missing seats: none" not in forms[name], (
            "WRONG OUTPUT S16A21-04: %s form printing a missing "
            "seats none line where the roster record itself is "
            "absent" % name)
        assert "roster record itself is absent" in forms[name], (
            "WRONG OUTPUT S16A21-04: %s form stating nothing "
            "about the absent roster record" % name)
    assert forms["Agentic"].get("roster_record_absent") is True, (
        "WRONG OUTPUT S16A21-04: Agentic form carrying roster "
        "record absent standing %r"
        % forms["Agentic"].get("roster_record_absent"))


def test_s16a21_04_missing_seats_none_where_roster_stands():
    # Guard: where a roster record stands and no seat is
    # missing, the missing seats none line stands as before.
    record = _no_derivation_record()
    record["fields"]["7"]["absence_words"] = None
    record["fields"]["11"] = {
        "missing_seats": [], "duplicate_holdings": [],
        "unproven_seats": []}
    record["check_results"] = [
        {"check": 4, "verdict": "PASS", "verdict_position": "PASS"}]
    forms = _presentation().render_forms(record)
    assert "Missing seats: none" in forms["Simple"]


def test_s16_fixb2_forms_agree_with_record_after_cures():
    # Guard: the form agreement comparison finds no disagreement
    # on the cured forms of either cure record.
    presentation = _presentation()
    for record in (_no_derivation_record(), _roster_absent_record()):
        forms = presentation.render_forms(record)
        reports = presentation.compare_generated_forms(record, forms)
        assert reports == [], (
            "WRONG OUTPUT S16 FIX B2: form agreement reports %r "
            "on the forms the cured rendering produces" % reports)
