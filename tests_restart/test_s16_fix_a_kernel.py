# Copyright: J.P. Picard aka Macro-Harder.
"""Step 16 Round 1 Fix A cure tests: kernel.py only.

Findings: S16U-02 (roster absent, brief section 5.5.1 branch 1),
S16U-03 (a named file that does not exist), S16U-07 (PASS citation
form), S16U-08 (no derivation for the stage in the shipped tables),
S16U-10 (contract field 5 claim_bearing_list on the grill G7 closed
list), and the S16U-01 kernel acceptance limb standing.
"""

import hashlib

from tests_restart.conftest import check, field


def _staffed_input(**overrides):
    run_input = {
        "runner_identity": "fix-a-runner",
        "runner_capacity": "Auditor",
        "build": "muster-lite",
        "stage_judged": "Step 13",
        "tier": "Low",
        "pinned_base": "base-a",
        "supplied_files": [],
        "roster": {
            "file": "records/roster.md",
            "seats": [
                {"seat_key": "seat-1", "team": "Design team",
                 "agent_identifier": "agent-1",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location": "records/roster.md line 4"},
                {"seat_key": "seat-2", "team": "Design team",
                 "agent_identifier": "agent-2",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location": "records/roster.md line 5"},
                {"seat_key": "seat-3", "team": "Design team",
                 "agent_identifier": "agent-3",
                 "agent_kind": "full identifier",
                 "counting_position": "counted in base",
                 "roster_line_location": "records/roster.md line 6"},
            ],
            "board_seats": [
                {"seat_key": "board-1", "agent_identifier": "agent-1",
                 "agent_kind": "full identifier"},
                {"seat_key": "board-2", "agent_identifier": "agent-2",
                 "agent_kind": "full identifier"},
                {"seat_key": "board-3", "agent_identifier": "agent-3",
                 "agent_kind": "full identifier"},
            ],
        },
        "tables": {
            "layer1": [{"tier": "Low", "team_form": "Design team",
                        "base_size": 2}],
            "layer2": [{"step": "Step 13", "unit": "Design team",
                        "unit_count": 1}],
            "mapping": [{"step": "Step 13", "unit": "Design team",
                         "team_form": "Design team"}],
        },
    }
    run_input.update(overrides)
    return run_input


def _kernel():
    from muster_restart import kernel
    return kernel


ROSTER_RESTING = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11]


def test_s16u02_no_records_roster_resting_checks_unverifiable():
    result = _kernel().compute_result({
        "runner_identity": "fix-a-runner",
        "runner_capacity": "Auditor",
        "build": "muster-lite",
        "stage_judged": "Step 13",
        "tier": "Low",
        "supplied_files": [],
    })
    for number in ROSTER_RESTING:
        entry = check(result, number)
        assert entry["verdict"] == "UNVERIFIABLE", (
            "check %s stood at %s on bare absence"
            % (number, entry["verdict"]))
        assert "roster record" in entry["missing_fact"]
    assert field(result, 12) == "UNVERIFIABLE"


def test_s16u02_nonexistent_stage_no_roster_check_passes():
    result = _kernel().compute_result({
        "runner_identity": "fix-a-runner",
        "runner_capacity": "Auditor",
        "build": "muster-lite",
        "stage_judged": "Step 99",
        "tier": "Low",
        "supplied_files": [],
    })
    for number in ROSTER_RESTING:
        entry = check(result, number)
        assert entry["verdict"] == "UNVERIFIABLE", (
            "check %s stood at %s for a stage with no records"
            % (number, entry["verdict"]))
    assert check(result, 17)["verdict"] == "UNVERIFIABLE"
    assert field(result, 12) == "UNVERIFIABLE"


def test_s16u02_roster_absent_pass_citation_fallback_nowhere():
    result = _kernel().compute_result({
        "runner_identity": "fix-a-runner",
        "runner_capacity": "Auditor",
        "build": "muster-lite",
        "stage_judged": "Step 99",
        "tier": "Low",
        "supplied_files": [],
    })
    for entry in result["check_results"]:
        if entry["verdict"] == "PASS":
            assert "roster record, seat not stated" not in str(
                entry.get("citations"))


def test_s16u03_absent_named_file_not_supplied_not_read(tmp_path):
    present = tmp_path / "step-16-record.md"
    present.write_text("record body", encoding="utf-8")
    absent = tmp_path / "step-16-gate-record.md"
    result = _kernel().compute_result(_staffed_input(
        supplied_files=[
            {"path": str(present), "group": "stage records"},
            {"path": str(absent), "group": "claim bearing files"},
        ]))
    coverage = field(result, 5)["coverage"]
    assert coverage["stage records"] == {
        "needed": 1, "supplied": 1, "read": 1}
    assert coverage["claim bearing files"]["supplied"] == 0
    assert coverage["claim bearing files"]["read"] == 0
    receipt = field(result, 5)["receipt"]
    names = [entry["file_name"] for entry in receipt]
    assert "step-16-gate-record.md" not in names
    assert "step-16-record.md" in names
    for entry in receipt:
        assert entry["hash"] != (
            "no hash stands, because no file bytes stand for the "
            "named file at this run")
        assert entry["byte_size"] != (
            "no byte size stands, because no file bytes stand for "
            "the named file at this run")
    present_entry = [e for e in receipt
                     if e["file_name"] == "step-16-record.md"][0]
    assert present_entry["hash"] == hashlib.sha256(
        b"record body").hexdigest()
    assert str(absent) in field(result, 5)["missing_files"]
    assert str(absent) not in field(result, 5)["supplied_set"].get(
        "claim bearing files", [])


def test_s16u07_pass_citation_names_file_line_and_seat():
    result = _kernel().compute_result(_staffed_input())
    entry = check(result, 4)
    assert entry["verdict"] == "PASS"
    citation = entry["citations"][0]
    assert "records/roster.md" in citation
    assert "line 4" in citation
    assert "seat-1" in citation
    for item in result["check_results"]:
        if item["verdict"] == "PASS":
            assert "roster record, seat not stated" not in str(
                item.get("citations"))
            assert item.get("roster_line_location") != (
                "roster record, seat not stated")


def test_s16u08_no_derivation_for_stage_check1_not_pass():
    run_input = _staffed_input(stage_judged="Step 15")
    del run_input["tables"]
    result = _kernel().compute_result(run_input)
    entry = check(result, 1)
    assert entry["verdict"] == "UNVERIFIABLE"
    assert "Layer 2 row" in entry["missing_fact"]
    assert "mapping row" in entry["missing_fact"]
    assert "Step 15" in entry["missing_fact"]
    absence = field(result, 7)["absence_words"]
    assert absence is not None
    assert "Layer 2 row" in absence
    assert "mapping row" in absence
    assert "Step 15" in absence


def test_s16u10_claim_bearing_list_is_g7_closed_list_group():
    result = _kernel().compute_result(_staffed_input(
        supplied_files=[
            {"path": "records/roster.md", "group": "stage records"},
            {"path": "records/roster.md",
             "group": "claim bearing files"},
            {"path": "records/step-13-record.md",
             "group": "stage records"},
            {"path": "records/step-13-record.md",
             "group": "claim bearing files"},
            {"path": "records/step-13-gate-record.md",
             "group": "claim bearing files"},
            {"path": "design/restart/TIER-RECORD.md",
             "group": "stage records"},
            {"path": "design/restart/TIER-RECORD.md",
             "group": "claim bearing files"},
            {"path": "records/notes.md",
             "group": "claim bearing files"},
        ]))
    assert field(result, 5)["claim_bearing_list"] == [
        "records/roster.md",
        "records/step-13-gate-record.md",
        "records/step-13-record.md",
    ]


def test_s16u01_kernel_accepts_roster_assembled_from_record_content():
    result = _kernel().compute_result(_staffed_input())
    stage_count = field(result, 7)["stage_count"]
    assert stage_count["entries_counted"] == 3
    assert stage_count["counted_total"] == 3
    team_counts = field(result, 7)["team_counts"]
    assert team_counts[0]["counted_total"] == 3
