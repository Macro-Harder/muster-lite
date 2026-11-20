# Copyright: J.P. Picard aka Macro-Harder.
"""Step 17 Round 1 Fix A cure tests: kernel.py only.

These tests pin the Fix A cures of the Step 17 Round 1 fix
register, items 1, 2, 5, 8, 14, 15, 17 and 18, the primary seat
on item 17, and the kernel acceptance standings for the item 6
and item 16 limbs. Kernel nodes call compute_result directly in
the structured RunInput form; command line nodes drive the
shipped command line as a subprocess over fixtures written into
a temporary directory, in the form of the Step 16 Fix C module.

Item 1, S17B-01: the duplicate holding scan covers the seats of
the stage as a whole, across teams; a doubled holding stands
named, check 2 at FAIL, no PASS rollup over it.
Item 2, S17B-02: a counted seat stating no holder, by an absent
or a null agent_identifier, leaves the holders standing unproven
on the affected checks rather than passing at 0; the rollup over
such seats is not PASS; the outcome states the unproven standing
in words.
Item 5, S17B-05: a counting_position outside the stated list
(counted thrice, banana, Exempt, EXEMPT) does not count toward a
team minimum on its own wording in any form, and the outcome
names the out of list values received.
Item 8, S17B-08: table verification. A missing table part is
reported as missing in the manifest, stands in no fabricated
form, and the check resting on it does not PASS on its absence;
figures outside the stated sense are carried as UNVERIFIABLE,
never silently counted; two rows for one step and unit take the
differing rows outcome, never a silent last row win.
Item 14, S17B-14: the item 1 scan covers board seats with team
seats.
Item 15, S17B-15: two seats in one roster carrying one seat key
are named as a defect in the outcome; no PASS rollup stands over
the duplication.
Item 17, S17B-17, kernel limb: the read standing distinguishes
a path that does not stand from an entry that stands in another
form (directory, FIFO, device, symlink loop) and states that
standing.
Item 18, S17B-18: where a seat states a full identifier in
writing, the duplicate holding stands named and check 2 at FAIL
whatever kind the seat declares; the kind governs only seats
stating no full identifier. The markdown form stands under its
recorded grill G6 bound and is not this cure.
Item 6 kernel limb: the kernel accepts the claim records the
wiring supplies in the stated structured forms.
Item 16 kernel limb: a stated empty roster stands distinct from
a roster absent in the kernel branch decision.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from tests_restart.conftest import check, field, require_kernel

REPO_ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DIR = REPO_ROOT / "muster_restart"


def _seat(key, agent, team="Design team", **extra):
    seat = {"seat_key": key, "agent_identifier": agent,
            "agent_kind": "full identifier",
            "counting_position": "counted in base", "team": team}
    seat.update(extra)
    return seat


def _board(key, agent):
    return {"seat_key": key, "agent_identifier": agent,
            "agent_kind": "full identifier"}


def _board_set():
    return [_board("board-1", "board-a"), _board("board-2", "board-b"),
            _board("board-3", "board-c")]


def _run_input(seats, board=None, **extra):
    roster = {"file": "records/roster.md", "seats": seats}
    if board is not None:
        roster["board_seats"] = board
    run_input = {
        "runner_identity": "Fix A cure runner",
        "runner_capacity": "Auditor",
        "stage_judged": "Step 13",
        "tier": "Low",
        "pinned_base": "base tables v1",
        "supplied_files": [],
        "roster": roster,
    }
    run_input.update(extra)
    return run_input


def _duplicate_seats(result):
    return [entry["evidence"]["seat"] for entry in
            field(result, 11)["duplicate_holdings"]]


# ------------------------------------------------------------------
# Item 1, S17B-01: cross team duplicate holding.
# ------------------------------------------------------------------

def test_s17b01_cross_team_duplicate_holding_named_check2_fail():
    kernel = require_kernel()
    result = kernel.compute_result(_run_input(
        [_seat("seat-1", "agent-1"),
         _seat("seat-2", "agent-2"),
         _seat("seat-3", "agent-1", team="Build team")],
        board=_board_set()))
    assert _duplicate_seats(result) == ["seat-3"], (
        "WRONG OUTPUT S17B-01: the cross team duplicate holding "
        "stands named as %s" % (_duplicate_seats(result),))
    assert check(result, 2)["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-01: check 2 stands at %s over an agent "
        "holding seats in two teams of one stage"
        % check(result, 2)["verdict"])
    assert field(result, 12) != "PASS", (
        "WRONG OUTPUT S17B-01: a PASS rollup stands over a doubled "
        "holding across teams")


def test_s17b01_cli_cross_team_duplicate_no_pass_rollup(tmp_path):
    roster = _write_roster_json(
        tmp_path / "step-13-roster.json",
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2"),
         _seat("seat-3", "agent-1", team="Build team")],
        board=_board_set())
    outcome = _run_cli_outcome(roster, tmp_path)
    assert outcome["kind"] == "completed gate run"
    checks = _cli_checks(outcome)
    assert checks[2]["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-01: through the command line check 2 "
        "stands at %s over the C16 shape" % checks[2]["verdict"])
    holdings = outcome["result_record"]["fields"]["11"][
        "duplicate_holdings"]
    assert [entry["evidence"]["seat"] for entry in holdings] == \
        ["seat-3"], (
        "WRONG OUTPUT S17B-01: the command line outcome names "
        "duplicate holdings %s" % (holdings,))
    assert outcome["rollup"] != "PASS", (
        "WRONG OUTPUT S17B-01: a citable PASS rollup stands over "
        "one agent holding seats in two teams")


# ------------------------------------------------------------------
# Item 14, S17B-14: board seat and team seat held by one agent.
# ------------------------------------------------------------------

def test_s17b14_board_and_team_seat_duplicate_named():
    kernel = require_kernel()
    result = kernel.compute_result(_run_input(
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")],
        board=[_board("board-1", "agent-1"),
               _board("board-2", "board-b"),
               _board("board-3", "board-c")]))
    assert _duplicate_seats(result) == ["board-1"], (
        "WRONG OUTPUT S17B-14: the board and team duplicate "
        "holding stands named as %s" % (_duplicate_seats(result),))
    assert check(result, 2)["verdict"] == "FAIL"
    assert field(result, 12) != "PASS", (
        "WRONG OUTPUT S17B-14: a PASS rollup stands over a board "
        "member holding a team seat of the same stage")


def test_s17b14_cli_board_and_team_seat_no_pass_rollup(tmp_path):
    roster = _write_roster_json(
        tmp_path / "step-13-roster.json",
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")],
        board=[_board("board-1", "agent-1"),
               _board("board-2", "board-b"),
               _board("board-3", "board-c")])
    outcome = _run_cli_outcome(roster, tmp_path)
    checks = _cli_checks(outcome)
    assert checks[2]["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-14: through the command line check 2 "
        "stands at %s over the C20 shape" % checks[2]["verdict"])
    assert outcome["rollup"] != "PASS"


# ------------------------------------------------------------------
# Item 18, S17B-18: a stated kind does not soften a proven
# duplicate where a full identifier stands in writing.
# ------------------------------------------------------------------

def test_s17b18_not_recorded_kind_keeps_duplicate_at_fail():
    kernel = require_kernel()
    seats = [
        _seat("seat-1", "agent-1", agent_kind="not recorded"),
        _seat("seat-2", "agent-1", agent_kind="not recorded")]
    result = kernel.compute_result(_run_input(seats,
                                              board=_board_set()))
    assert _duplicate_seats(result) == ["seat-2"], (
        "WRONG OUTPUT S17B-18: the duplicate holding over a full "
        "identifier stated in writing stands named as %s"
        % (_duplicate_seats(result),))
    assert check(result, 2)["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-18: check 2 stands at %s where the "
        "seats declare the kind not recorded over a full "
        "identifier in writing" % check(result, 2)["verdict"])


def test_s17b18_cli_not_recorded_kind_duplicate_fails(tmp_path):
    roster = _write_roster_json(
        tmp_path / "step-13-roster.json",
        [_seat("seat-1", "agent-1", agent_kind="not recorded"),
         _seat("seat-2", "agent-1", agent_kind="not recorded")],
        board=_board_set())
    outcome = _run_cli_outcome(roster, tmp_path)
    checks = _cli_checks(outcome)
    assert checks[2]["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-18: through the command line the C03 "
        "shape answers check 2 %s, softened from the FAIL the "
        "same seats earn with the kind unstated"
        % checks[2]["verdict"])
    assert outcome["rollup"] != "PASS"


def test_s17b18_markdown_form_bound_stands():
    # Guard: the markdown form of the shape stands under the
    # recorded grill G6 bound and is not this cure. A markdown
    # assembled seat carries its label as its role name and as
    # its holder value with the kind not recorded; two such seats
    # stating one label prove no distinct holder and stand at
    # NOT PROVEN on check 2, with no duplicate holding named.
    kernel = require_kernel()
    seats = [
        {"seat_key": "seat-1", "role_name": "Seat Alpha",
         "agent_identifier": "Seat Alpha",
         "agent_kind": "not recorded",
         "counting_position": "counted in base",
         "team": "Design team"},
        {"seat_key": "seat-2", "role_name": "Seat Alpha",
         "agent_identifier": "Seat Alpha",
         "agent_kind": "not recorded",
         "counting_position": "counted in base",
         "team": "Design team"}]
    result = kernel.compute_result(_run_input(seats,
                                              board=_board_set()))
    assert _duplicate_seats(result) == [], (
        "WRONG OUTPUT S17B-18: a duplicate holding stands named "
        "over the markdown form, which stands under the grill "
        "G6 bound: %s" % (_duplicate_seats(result),))
    assert check(result, 2)["verdict"] == "NOT PROVEN", (
        "WRONG OUTPUT S17B-18: the markdown form answers check "
        "2 %s, outside its recorded bound"
        % check(result, 2)["verdict"])


# ------------------------------------------------------------------
# Item 2, S17B-02: counted seats stating no holder.
# ------------------------------------------------------------------

def test_s17b02_absent_identifier_holders_unproven():
    kernel = require_kernel()
    seats = [
        {"seat_key": "seat-1", "agent_kind": "full identifier",
         "counting_position": "counted in base",
         "team": "Design team"},
        {"seat_key": "seat-2", "agent_kind": "full identifier",
         "counting_position": "counted in base",
         "team": "Design team"}]
    result = kernel.compute_result(_run_input(seats,
                                              board=_board_set()))
    assert check(result, 2)["verdict"] == "NOT PROVEN", (
        "WRONG OUTPUT S17B-02: check 2 stands at %s over counted "
        "seats stating no agent_identifier at all"
        % check(result, 2)["verdict"])
    assert field(result, 12) != "PASS", (
        "WRONG OUTPUT S17B-02: a PASS rollup stands over seats "
        "naming no holder")
    stage = field(result, 7)["stage_count"]
    assert "unproven" in str(stage.get("holders_standing", "")), (
        "WRONG OUTPUT S17B-02: the stage count states the "
        "holders standing as %s, with no unproven standing in "
        "words" % (stage.get("holders_standing"),))


def test_s17b02_null_identifier_holders_unproven():
    kernel = require_kernel()
    seats = [_seat("seat-1", None), _seat("seat-2", None)]
    result = kernel.compute_result(_run_input(seats,
                                              board=_board_set()))
    assert check(result, 2)["verdict"] == "NOT PROVEN", (
        "WRONG OUTPUT S17B-02: check 2 stands at %s over counted "
        "seats stating the agent_identifier as null"
        % check(result, 2)["verdict"])
    assert field(result, 12) != "PASS"
    stage = field(result, 7)["stage_count"]
    assert "unproven" in str(stage.get("holders_standing", ""))


def test_s17b02_cli_absent_and_null_twins_no_pass(tmp_path):
    for label, seats in (
            ("absent", [
                {"seat_key": "seat-1",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "team": "Design team"},
                {"seat_key": "seat-2",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "team": "Design team"}]),
            ("null", [_seat("seat-1", None), _seat("seat-2", None)])):
        roster = _write_roster_json(
            tmp_path / ("step-13-roster-%s.json" % label),
            seats, board=_board_set())
        outcome = _run_cli_outcome(roster, tmp_path)
        checks = _cli_checks(outcome)
        assert checks[2]["verdict"] == "NOT PROVEN", (
            "WRONG OUTPUT S17B-02: through the command line the "
            "%s twin answers check 2 %s" % (label,
                                            checks[2]["verdict"]))
        assert outcome["rollup"] != "PASS", (
            "WRONG OUTPUT S17B-02: the %s twin reaches a PASS "
            "rollup over seats naming no holder" % label)
        assert "unproven" in json.dumps(
            outcome["result_record"]), (
            "WRONG OUTPUT S17B-02: the %s twin outcome states "
            "no unproven holders standing in words" % label)


# ------------------------------------------------------------------
# Item 5, S17B-05: the counting position closed list.
# ------------------------------------------------------------------

OUT_OF_LIST = ["counted thrice", "banana", "Exempt", "EXEMPT"]


def test_s17b05_out_of_list_positions_do_not_count_and_are_named():
    kernel = require_kernel()
    seats = [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")]
    for index, value in enumerate(OUT_OF_LIST):
        seats.append(_seat("seat-x%d" % index,
                           "agent-x%d" % index,
                           counting_position=value))
    result = kernel.compute_result(_run_input(seats,
                                              board=_board_set()))
    design = [t for t in field(result, 7)["team_counts"]
              if t["team"] == "Design team"]
    assert design and design[0]["counted_total"] == 2, (
        "WRONG OUTPUT S17B-05: the Design team counted total "
        "stands at %s, counting out of list positions toward "
        "the minimum" % (design,))
    named = design[0].get("out_of_list_counting_positions")
    assert named == sorted(OUT_OF_LIST), (
        "WRONG OUTPUT S17B-05: the team count names the out of "
        "list values as %s" % (named,))
    stage = field(result, 7)["stage_count"]
    assert stage.get("out_of_list_counting_positions") == \
        sorted(OUT_OF_LIST), (
        "WRONG OUTPUT S17B-05: the stage count names the out "
        "of list values as %s"
        % (stage.get("out_of_list_counting_positions"),))


def test_s17b05_cli_out_of_list_positions_no_pass(tmp_path):
    for label, values in (("invented", ["counted thrice", "banana"]),
                          ("case", ["Exempt", "EXEMPT"])):
        seats = [
            _seat("seat-1", "agent-1", counting_position=values[0]),
            _seat("seat-2", "agent-2", counting_position=values[1])]
        roster = _write_roster_json(
            tmp_path / ("step-13-roster-%s.json" % label),
            seats, board=_board_set())
        outcome = _run_cli_outcome(roster, tmp_path)
        assert outcome["rollup"] != "PASS", (
            "WRONG OUTPUT S17B-05: the %s positions %s reach a "
            "PASS rollup through the command line"
            % (label, values))
        text = json.dumps(outcome["result_record"])
        for value in values:
            assert value in text, (
                "WRONG OUTPUT S17B-05: the outcome names no out "
                "of list value %s" % value)


# ------------------------------------------------------------------
# Item 15, S17B-15: two seats in one roster carrying one seat key.
# ------------------------------------------------------------------

def test_s17b15_duplicate_seat_key_named_as_defect_no_pass():
    kernel = require_kernel()
    result = kernel.compute_result(_run_input(
        [_seat("seat-1", "agent-1"), _seat("seat-1", "agent-2")],
        board=_board_set()))
    stage = field(result, 7)["stage_count"]
    assert stage.get("duplicate_seat_keys") == ["seat-1"], (
        "WRONG OUTPUT S17B-15: the stage count names the "
        "duplicated seat keys as %s"
        % (stage.get("duplicate_seat_keys"),))
    assert check(result, 1)["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-15: check 1 stands at %s over two "
        "seats in one roster carrying one seat key"
        % check(result, 1)["verdict"])
    assert field(result, 12) != "PASS", (
        "WRONG OUTPUT S17B-15: a PASS rollup stands over a "
        "duplicated seat key")


def test_s17b15_cli_duplicate_seat_key_no_pass(tmp_path):
    roster = _write_roster_json(
        tmp_path / "step-13-roster.json",
        [_seat("seat-1", "agent-1"), _seat("seat-1", "agent-2")],
        board=_board_set())
    outcome = _run_cli_outcome(roster, tmp_path)
    assert outcome["rollup"] != "PASS", (
        "WRONG OUTPUT S17B-15: the C19 shape reaches a PASS "
        "rollup through the command line")
    assert "seat-1" in json.dumps(
        outcome["result_record"]["fields"]["7"]), (
        "WRONG OUTPUT S17B-15: the outcome names no duplicated "
        "seat key in its counts")


# ------------------------------------------------------------------
# Item 8, S17B-08: the pinned tables, at kernel level.
# ------------------------------------------------------------------

def _tables(layer1=None, layer2=None, mapping=None):
    return {
        "layer1": layer1 if layer1 is not None else [
            {"team_form": "Design team", "tier": "Low",
             "base_size": 2}],
        "layer2": layer2 if layer2 is not None else [
            {"step": "Step 13", "unit": "Design team",
             "unit_count": 1}],
        "mapping": mapping if mapping is not None else [
            {"step": "Step 13", "unit": "Design team",
             "team_form": "Design team"}],
    }


def _unit_seats():
    return [
        _seat("seat-1", "agent-1", unit="Design team"),
        _seat("seat-2", "agent-2", unit="Design team")]


def test_s17b08_negative_unit_count_unverifiable():
    kernel = require_kernel()
    tables = _tables(layer2=[
        {"step": "Step 13", "unit": "Design team",
         "unit_count": -5}])
    result = kernel.compute_result(_run_input(
        _unit_seats(), board=_board_set(), tables=tables))
    assert check(result, 1)["verdict"] == "UNVERIFIABLE", (
        "WRONG OUTPUT S17B-08: a required count of -5 answers "
        "check 1 %s, silently counted"
        % check(result, 1)["verdict"])
    stage = field(result, 7)["stage_count"]
    assert stage["required_count"] != -5, (
        "WRONG OUTPUT S17B-08: the stage required count stands "
        "at the out of sense figure -5")


def test_s17b08_oversized_unit_count_unverifiable():
    kernel = require_kernel()
    tables = _tables(layer2=[
        {"step": "Step 13", "unit": "Design team",
         "unit_count": 1000000000000}])
    result = kernel.compute_result(_run_input(
        _unit_seats(), board=_board_set(), tables=tables))
    assert check(result, 1)["verdict"] == "UNVERIFIABLE", (
        "WRONG OUTPUT S17B-08: a unit count of 1000000000000 "
        "answers check 1 %s, silently counted"
        % check(result, 1)["verdict"])
    stage = field(result, 7)["stage_count"]
    assert stage["required_count"] != 1000000000000


def test_s17b08_two_rows_for_one_step_and_unit_differing_outcome():
    kernel = require_kernel()
    tables = _tables(layer2=[
        {"step": "Step 13", "unit": "Design team", "unit_count": 1},
        {"step": "Step 13", "unit": "Design team",
         "unit_count": 99}])
    result = kernel.compute_result(_run_input(
        _unit_seats(), board=_board_set(), tables=tables))
    assert check(result, 1)["verdict"] == "UNVERIFIABLE", (
        "WRONG OUTPUT S17B-08: two rows for one step and unit "
        "answer check 1 %s, where the differing rows outcome "
        "stands" % check(result, 1)["verdict"])
    stage = field(result, 7)["stage_count"]
    assert stage["required_count"] != 99, (
        "WRONG OUTPUT S17B-08: the later of two differing rows "
        "governs the stage required count silently at 99")


# ------------------------------------------------------------------
# Item 8, S17B-08: the pinned tables as files, in scratch copies.
# ------------------------------------------------------------------

def _scratch_unit(tmp_path):
    scratch = tmp_path / "unit"
    shutil.copytree(PRODUCT_DIR, scratch / "muster_restart")
    return scratch


def _run_scratch_cli(scratch, roster_path, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(scratch)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry",
         "--runner-identity", "Fix A cure runner",
         "--runner-capacity", "Auditor",
         "--build", "muster-lite",
         "--stage", "Step 13",
         "--tier", "Low",
         "--supplied-file", "%s:stage records" % roster_path],
        cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _pass_roster_path(tmp_path):
    return _write_roster_json(
        tmp_path / "step-13-roster.json",
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")],
        board=_board_set())


def test_s17b08_cli_missing_layer2_reported_missing_no_pass(
        tmp_path):
    scratch = _scratch_unit(tmp_path)
    (scratch / "muster_restart" / "layer2.json").unlink()
    roster = _pass_roster_path(tmp_path)
    outcome = _run_scratch_cli(scratch, roster, tmp_path)
    record = outcome["result_record"]
    manifest = record["fields"]["4"]["manifest"]
    entries = {entry["table_name"]: entry
               for entry in manifest["entries"]}
    layer2 = entries["layer2"]
    assert layer2.get("standing") == "missing" or \
        "no hash stands" in str(layer2.get("hash")), (
        "WRONG OUTPUT S17B-08: the manifest entry for the "
        "missing layer2 part stands as %s, a fabricated form "
        "in place of a missing report" % (layer2,))
    assert layer2.get("byte_size") != 2, (
        "WRONG OUTPUT S17B-08: the manifest prints byte size "
        "2 for a table part that does not stand")
    checks = _cli_checks(outcome)
    assert checks[1]["verdict"] != "PASS", (
        "WRONG OUTPUT S17B-08: check 1 PASSes for Step 13 on "
        "a partial table set with layer2 deleted")
    assert outcome["rollup"] != "PASS"


def test_s17b08_cli_out_of_sense_figures_unverifiable(tmp_path):
    for label, figure in (("negative", -5),
                          ("oversized", 1000000000000)):
        scratch = _scratch_unit(tmp_path / label)
        layer2_path = scratch / "muster_restart" / "layer2.json"
        rows = json.loads(layer2_path.read_text(encoding="utf-8"))
        rows[0]["unit_count"] = figure
        layer2_path.write_text(json.dumps(rows), encoding="utf-8")
        roster = _pass_roster_path(tmp_path)
        outcome = _run_scratch_cli(scratch, roster, tmp_path)
        checks = _cli_checks(outcome)
        assert checks[1]["verdict"] == "UNVERIFIABLE", (
            "WRONG OUTPUT S17B-08: the %s figure %s answers "
            "check 1 %s in a scratch copy"
            % (label, figure, checks[1]["verdict"]))
        stage = outcome["result_record"]["fields"]["7"][
            "stage_count"]
        assert stage["required_count"] != figure


def test_s17b08_cli_two_shipped_rows_differing_outcome(tmp_path):
    scratch = _scratch_unit(tmp_path)
    layer2_path = scratch / "muster_restart" / "layer2.json"
    rows = json.loads(layer2_path.read_text(encoding="utf-8"))
    rows.append({"step": "Step 13", "unit": "Design team",
                 "unit_count": 99})
    layer2_path.write_text(json.dumps(rows), encoding="utf-8")
    roster = _pass_roster_path(tmp_path)
    outcome = _run_scratch_cli(scratch, roster, tmp_path)
    checks = _cli_checks(outcome)
    assert checks[1]["verdict"] == "UNVERIFIABLE", (
        "WRONG OUTPUT S17B-08: two shipped rows for Step 13 "
        "and Design team answer check 1 %s, the later row "
        "governing silently" % checks[1]["verdict"])
    stage = outcome["result_record"]["fields"]["7"]["stage_count"]
    assert stage["required_count"] != 99


def test_s17b08_cli_untampered_scratch_control_still_passes(
        tmp_path):
    scratch = _scratch_unit(tmp_path)
    roster = _pass_roster_path(tmp_path)
    outcome = _run_scratch_cli(scratch, roster, tmp_path)
    checks = _cli_checks(outcome)
    assert checks[1]["verdict"] == "PASS", (
        "WRONG OUTPUT S17B-08: the untampered scratch control "
        "answers check 1 %s" % checks[1]["verdict"])
    assert outcome["rollup"] == "PASS"


# ------------------------------------------------------------------
# Item 17, S17B-17, kernel limb: entries standing in another form.
# ------------------------------------------------------------------

def test_s17b17_other_form_entries_state_their_standing(tmp_path):
    kernel = require_kernel()
    directory = tmp_path / "named-record-dir"
    directory.mkdir()
    fifo = tmp_path / "named-fifo"
    os.mkfifo(fifo)
    missing = tmp_path / "named-absent-record.md"
    present = tmp_path / "named-record.md"
    present.write_text("a record\n", encoding="utf-8")
    entries = [
        {"path": str(directory), "group": "stage records"},
        {"path": str(fifo), "group": "stage records"},
        {"path": "/dev/null", "group": "claim bearing files"},
        {"path": str(missing), "group": "stage records"},
        {"path": str(present), "group": "stage records",
         "content": "a record\n"},
    ]
    result = kernel.compute_result(_run_input(
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")],
        board=_board_set(), supplied_files=entries))
    missing_files = field(result, 5)["missing_files"]
    plain = [entry for entry in missing_files
             if isinstance(entry, str)]
    stated = {entry["path"]: entry["standing"]
              for entry in missing_files if isinstance(entry, dict)}
    assert plain == [str(missing)], (
        "WRONG OUTPUT S17B-17: the missing files list stands "
        "as %s, listing entries that stand on disk in another "
        "form among the files that do not exist"
        % (missing_files,))
    assert stated.get(str(directory)) == "directory", (
        "WRONG OUTPUT S17B-17: the directory entry states its "
        "standing as %s" % (stated,))
    assert stated.get(str(fifo)) == "FIFO"
    assert stated.get("/dev/null") == "device"


def test_s17b17_cli_directory_and_fifo_not_listed_as_missing(
        tmp_path):
    directory = tmp_path / "named-record-dir"
    directory.mkdir()
    fifo = tmp_path / "named-fifo"
    os.mkfifo(fifo)
    roster = _pass_roster_path(tmp_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry",
         "--runner-identity", "Fix A cure runner",
         "--runner-capacity", "Auditor",
         "--build", "muster-lite",
         "--stage", "Step 13",
         "--tier", "Low",
         "--supplied-file", "%s:stage records" % roster,
         "--supplied-file", "%s:claim bearing files" % directory,
         "--supplied-file", "%s:claim bearing files" % fifo],
        cwd=str(tmp_path), env=env, capture_output=True,
        text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    outcome = json.loads(proc.stdout)
    missing_files = outcome["result_record"]["fields"]["5"][
        "missing_files"]
    plain = [entry for entry in missing_files
             if isinstance(entry, str)]
    assert str(directory) not in plain and str(fifo) not in plain, (
        "WRONG OUTPUT S17B-17: the command line outcome lists "
        "%s among the files that do not exist"
        % (missing_files,))
    stated = {entry["path"]: entry["standing"]
              for entry in missing_files if isinstance(entry, dict)}
    assert stated.get(str(directory)) == "directory"
    assert stated.get(str(fifo)) == "FIFO"


# ------------------------------------------------------------------
# Item 6 kernel limb acceptance: the kernel accepts the claim
# records the wiring supplies in the stated structured forms.
# This node passed before the cure and passes after it; it pins
# that no kernel limb of item 6 arises.
# ------------------------------------------------------------------

def test_s17b06_kernel_accepts_claim_records_in_stated_forms():
    kernel = require_kernel()
    result = kernel.compute_result(_run_input(
        [_seat("seat-1", "agent-1"), _seat("seat-2", "agent-2")],
        board=_board_set(),
        claim_kind="cohort counts",
        direction="claim point with no generated point",
        claim_standing="claim standing read and contradicted",
        frozen_roster=[
            {"seat_key": "seat-1", "agent_identifier": "agent-1",
             "team": "Design team"}],
        gate_roster=[
            {"seat_key": "seat-1", "agent_identifier": "agent-1",
             "team": "Build team"}]))
    assert check(result, 16)["verdict"] != "PASS", (
        "WRONG OUTPUT S17B-06 kernel limb: check 16 answers "
        "PASS over a claim record in the stated form")
    assert check(result, 17)["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-06 kernel limb: check 17 answers "
        "%s over a contradicted claim in the stated form"
        % check(result, 17)["verdict"])


# ------------------------------------------------------------------
# Item 16 kernel limb acceptance: a stated empty roster stands
# distinct from a roster absent in the kernel branch decision.
# This node passed before the cure and passes after it; it pins
# that no kernel limb of item 16 arises.
# ------------------------------------------------------------------

def test_s17b16_kernel_empty_roster_distinct_from_absent():
    kernel = require_kernel()
    empty = kernel.compute_result(_run_input(
        [], board=_board_set()))
    absent_input = _run_input([], board=_board_set())
    del absent_input["roster"]
    absent = kernel.compute_result(absent_input)
    assert check(empty, 1)["verdict"] == "FAIL", (
        "WRONG OUTPUT S17B-16 kernel limb: a stated empty "
        "roster answers check 1 %s in the kernel"
        % check(empty, 1)["verdict"])
    assert check(absent, 1)["verdict"] == "UNVERIFIABLE", (
        "WRONG OUTPUT S17B-16 kernel limb: a roster absent "
        "answers check 1 %s in the kernel"
        % check(absent, 1)["verdict"])


# ------------------------------------------------------------------
# Command line helpers, in the Step 16 Fix C module form.
# ------------------------------------------------------------------

def _write_roster_json(path, seats, board=None):
    roster = {"file": path.name, "seats": seats}
    if board is not None:
        roster["board_seats"] = board
    path.write_text(json.dumps(roster), encoding="utf-8")
    return path


def _run_cli_outcome(roster_path, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, "-m", "muster_restart.run_entry",
         "--runner-identity", "Fix A cure runner",
         "--runner-capacity", "Auditor",
         "--build", "muster-lite",
         "--stage", "Step 13",
         "--tier", "Low",
         "--supplied-file", "%s:stage records" % roster_path],
        cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=120)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _cli_checks(outcome):
    record = outcome["result_record"]
    return {entry["check"]: entry
            for entry in record["check_results"]}
