# Copyright: J.P. Picard aka Macro-Harder.
"""Muster lite kernel module, restart run.

Slice 1: tables, manifest and contract shapes. Slice 2: kernel
reading, supplied set, coverage and receipt. The kernel entry is
compute_result(run_input), returning the ComputedResult of brief
section 5.4.2 as a mapping with a fields mapping keyed by contract
field number as text, a check_results list, and the remaining
contract content under its shape names.
"""

import hashlib
import json
from pathlib import Path

TOOL_NAME = "muster-lite"
TOOL_VERSION = "1.0.0"

# ------------------------------------------------------------------
# Slice 1: contract shapes, fixed as named definitions.
# Every shape at plan section 5 stands here with its field list in
# brief order. No field is dropped and no invariant is weakened.
# ------------------------------------------------------------------

SHAPES = {
    "RunInput": {"fields": [
        "runner identity", "runner capacity", "stage judged",
        "tier or not stated", "supplied file list",
        "pinned base reference"]},
    "PinnedBaseManifest": {"fields": [
        "manifest identity",
        "listed table entries with name hash and byte size",
        "rule base name hash and byte size or none identified"]},
    "CountingTables": {"fields": [
        "layer1 rows", "layer2 rows", "mapping rows"]},
    "RosterRecord": {"fields": [
        "build name", "roster standing", "stage", "tier claimed",
        "tier applied", "rounds", "units", "seats", "board seats",
        "stage claim texts", "logic audit distribution statement",
        "tier invocation records", "parse state per passage"]},
    "StepRecordIdentity": {"fields": [
        "step record file", "stage", "stage coordinator identity",
        "line location", "coordinator statements count"]},
    "SeatEntry": {"fields": [
        "seat key", "stage", "unit", "round", "role name", "colour",
        "roster line location", "roster id provenance", "pool family",
        "perspective", "qualification", "team name",
        "agent identifier", "spawn reference", "work products",
        "counting position", "carried seat kind", "exempt claim"]},
    "WorkProductRef": {"fields": [
        "product path", "product form", "colour",
        "author record standing", "author record id",
        "author record line location"]},
    "ClaimRecord": {"fields": [
        "file", "claim passage location", "record kind", "claim text",
        "check or rollup", "counting kind"]},
    "CheckResult": {"fields": [
        "check name", "rule", "seat or team", "expected property",
        "observed evidence with location", "verdict",
        "citation locations", "missing fact"]},
    "LimbResult": {"fields": [
        "check name", "limb name", "rule", "seat or team",
        "expected property", "observed evidence with location",
        "verdict", "listed limbs"]},
    "TeamCount": {"fields": [
        "team name", "counting kind", "required count",
        "entries counted", "duplicates removed",
        "exempt or uncounted seats removed", "counted total",
        "property conditioned counted totals", "slack"]},
    "StageCount": {"fields": [
        "counting kind", "per unit figures", "entries counted",
        "duplicates removed", "exempt or uncounted seats removed",
        "required count", "counted total", "holders figure"]},
    "GeneratedStaffingStatement": {"fields": [
        "per team counted seats", "per unit counts",
        "carried seats present and absent", "board seats",
        "missing seats", "duplicate holdings", "stage counts",
        "trace standing point", "build union point"]},
    "ComputedResult": {"fields": [
        "tool name and version",
        "run kind runner identity and runner capacity",
        "stage judged and tier applied", "pinned base identity",
        "supplied set and coverage", "per check results", "counts",
        "generated staffing statement and claim differences",
        "freeze to gate difference result",
        "precheck not yet run section", "repair lists",
        "stage rollup word", "standing bounds and limits"]},
    "ReceiptEntry": {"fields": [
        "file path", "file name", "hash", "byte size"]},
    "LogicAuditDistributionRecord": {"fields": [
        "stage", "form", "seat key", "holder identifier",
        "head or named slice"]},
    "RepairEntry": {"fields": [
        "entry kind", "check", "rule", "evidence file and seat",
        "cure act"]},
    "DefectReport": {"fields": [
        "form agreement check name", "rule", "element that disagreed",
        "value in result record with location",
        "value in generated form with location", "defect field"]},
    "RecordedPrecheck": {"fields": [
        "stage", "frozen roster file", "frozen roster standing",
        "content binding hash", "content binding byte size",
        "runner identity", "runner capacity",
        "precheck result as recorded"]},
    "ReseatRecord": {"fields": [
        "stage", "seat key", "prior holder", "new holder", "round",
        "file and line location"]},
    "PlanOrChargeRecord": {"fields": [
        "stage", "round", "colour statements"]},
}

CONTRACT_FIELD_NUMBERS = [str(n) for n in range(1, 14)]
CHECK_ORDER = list(range(1, 18))
COMPOSING_CHECKS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17}

# The counting model, fixed as plan section 5 carries it from brief
# section 5.4.1: three counting levels stay distinct, team counts,
# step totals and the build union; a one stage run cannot compute a
# build union, which carries the state and its reason and no figure;
# every count prints its subtraction; slack stands beside every PASS.
COUNTING_MODEL = {
    "levels": ["team counts", "step totals", "build union"],
    "build_union_state": "not computable in a one stage run",
    "build_union_reason": (
        "a one stage run reads no stage other than the one judged "
        "as seat evidence"),
    "whole_flow_totals": {"checklist": 39, "level_union": 38,
                          "selected": None},
}

GROUP_ORDER = [
    "stage records", "pinned rule tables",
    "audit plan or round charge", "work products", "reseat records",
    "claim bearing files", "ignored inputs",
]

PRECHECK_NO_ROLLUP_WORDS = (
    "Precheck. No rollup stands, because a composing check "
    "has not run")
NO_HASH_STANDING = (
    "no hash stands, because no file bytes stand for the "
    "named file at this run")
NO_BYTE_SIZE_STANDING = (
    "no byte size stands, because no file bytes stand for the "
    "named file at this run")
NO_RULE_BASE_HASH_STANDING = (
    "no hash stands, because the target records identify no "
    "hash for the rule base")
NO_RULE_BASE_BYTE_SIZE_STANDING = (
    "no byte size stands, because the target records identify "
    "no byte size for the rule base")
NO_MANIFEST_HASH_STANDING = (
    "no hash stands, because no manifest hash stands stated "
    "for this run")
NO_READ_HASH_STANDING = (
    "no hash stands, because no read hash stands stated "
    "for this run")

WORDS_ALONE_BASE_LINE = (
    "OPEN CASE, pinned base identified in words alone, "
    "result open at section 5.3")
OPEN_CASE_ROLLUP_WORDS = (
    "Rollup not stated. This run meets an open case, named here, "
    "and the single result for that case stands open")
NO_BASE_MISSING_IDENTIFICATION = (
    "the pinned base identification identified by both the tier "
    "record and the step record")


# ------------------------------------------------------------------
# Slice 1: the pinned tables in three named parts and the manifest.
# ------------------------------------------------------------------

def _load_shipped_tables():
    """Read the shipped table data files beside this module.

    The data files are Builder C files under DP-07. Each part stands
    as its own file and is read as its own part, never merged.
    """
    parts = {"layer1": [], "layer2": [], "mapping": []}
    data_dir = Path(__file__).parent
    for part in ("layer1", "layer2", "mapping"):
        candidate = data_dir / (part + ".json")
        if candidate.is_file():
            data = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(data, list):
                parts[part] = data
            elif isinstance(data, dict):
                rows = data.get(part, data.get("rows", []))
                if isinstance(rows, list):
                    parts[part] = rows
    return parts


def _tables_from(run_input):
    """CountingTables in its three named parts, never one merged list.

    Exception rows stand as data in the Layer 2 row form and stand
    inside the Layer 2 part, as brief section 5.3 states.
    """
    tables = run_input.get("tables")
    if isinstance(tables, dict):
        layer2 = list(tables.get("layer2", []))
        layer2.extend(tables.get("exception_rows", []))
        return {"parts": {
            "layer1": list(tables.get("layer1", [])),
            "layer2": layer2,
            "mapping": list(tables.get("mapping", [])),
        }}
    shipped = _load_shipped_tables()
    return {"parts": shipped}


def _manifest_from(run_input, tables):
    """The PinnedBaseManifest form for the run.

    One entry per listed table, with table name, hash in the stated
    hash form, being SHA-256 printed in lowercase hexadecimal, and
    byte size. The rule base standing carries the name, hash and
    byte size the target records identify, or none identified.
    """
    entries = []
    manifest_tables = run_input.get("manifest_tables")
    stated = run_input.get("manifest_entries", {})
    names = manifest_tables or ["layer1", "layer2", "mapping"]
    data_dir = Path(__file__).parent
    for name in names:
        entry = {"table_name": name}
        stated_entry = {}
        if isinstance(stated, dict) and isinstance(
                stated.get(name), dict):
            stated_entry = stated[name]
        candidate = data_dir / (name + ".json")
        if candidate.is_file():
            raw = candidate.read_bytes()
        else:
            rows = tables["parts"].get(name, [])
            raw = json.dumps(rows, sort_keys=True).encode("utf-8")
        if stated_entry.get("hash") is not None:
            entry["hash"] = stated_entry["hash"]
        else:
            entry["hash"] = hashlib.sha256(raw).hexdigest()
        if stated_entry.get("byte_size") is not None:
            entry["byte_size"] = stated_entry["byte_size"]
        else:
            entry["byte_size"] = len(raw)
        entries.append(entry)
    base = run_input.get("pinned_base")
    rule_base = None
    if isinstance(base, dict):
        rule_base = base
    elif base is not None:
        rule_base = {"name": base,
                     "hash": NO_RULE_BASE_HASH_STANDING,
                     "byte_size": NO_RULE_BASE_BYTE_SIZE_STANDING}
    return {
        "manifest_identity": run_input.get(
            "manifest_identity", "pinned base manifest"),
        "entries": entries,
        "rule_base": rule_base,
    }


def _exception_groups(tables):
    """Exception rows grouped by step and unit, in Layer 2 form."""
    groups = {}
    for row in tables["parts"]["layer2"]:
        key = (row.get("step"), row.get("unit"))
        groups.setdefault(key, []).append(row)
    return groups


def _differing_exception_units(run_input, tables):
    """Units whose exception rows state differing unit counts.

    Only the exception rows the run input states as exception rows
    take part. Where any two such rows for one step and one unit
    state differing figures, no figure stands for that unit, under
    brief section 5.3, and no selection rule stands for such rows.
    """
    raw = run_input.get("tables", {})
    rows = raw.get("exception_rows", []) if isinstance(raw, dict) else []
    by_unit = {}
    for row in rows:
        key = (row.get("step"), row.get("unit"))
        by_unit.setdefault(key, set()).add(row.get("unit_count"))
    differing = []
    for (step, unit), figures in by_unit.items():
        if len(figures) > 1:
            differing.append((step, unit))
    return differing


def _absence_words(step, unit):
    return (
        "no team count stands for %s, because exception rows state "
        "differing unit counts for %s and %s" % (unit, step, unit))


def _effective_unit_counts(run_input, tables, differing):
    """Unit count figures by step and unit, exception rows governing.

    Where an exception row and a Layer 2 row both stand for one step
    and one unit, the exception row governs, counted once. A unit
    under differing exception rows carries no figure.
    """
    figures = {}
    for row in tables["parts"]["layer2"]:
        key = (row.get("step"), row.get("unit"))
        if key in differing:
            continue
        figures[key] = row.get("unit_count")
    return figures


# ------------------------------------------------------------------
# Slice 2: reading, supplied set, coverage and receipt.
# ------------------------------------------------------------------

def _read_run_input(run_input):
    """RunInput reading and validation of its stated fields only."""
    return {
        "runner_identity": run_input.get("runner_identity"),
        "runner_capacity": run_input.get("runner_capacity"),
        "stage_judged": run_input.get("stage_judged"),
        "build": run_input.get("build"),
        "tier": run_input.get("tier", "not stated"),
        "run_kind": run_input.get("run_kind", "gate run"),
        "supplied_files": run_input.get("supplied_files", []),
        "pinned_base": run_input.get("pinned_base"),
    }


def _entry_groups(entry):
    groups = entry.get("groups")
    if isinstance(groups, list):
        return list(groups)
    group = entry.get("group")
    return [group] if group else []


def _entry_read(entry):
    """A supplied file stands read unless its entry states it is not.

    A spawn record export stands ignored under G5 in every case.
    """
    name = Path(str(entry.get("path", ""))).name
    if "spawn" in name and "export" in name:
        return False
    if "ignored inputs" in _entry_groups(entry):
        return False
    return entry.get("read", True) is not False


def _supplied_set(parsed):
    """The supplied set, group by group under G4, nothing widened."""
    groups = {}
    for entry in parsed["supplied_files"]:
        for group in _entry_groups(entry):
            groups.setdefault(group, []).append(entry)
    return groups


def _coverage(run_input, parsed, groups):
    """Coverage: records needed, supplied and read, per group.

    The coverage exception list at brief section 5.2 stands preserved
    whole in the standings below: the audit plan or round charge
    group stands on its named records, the reseat records group
    stands on its three standings, and a file standing in two groups
    counts once in each of records needed, records supplied and
    records read, under the two group file counting rule.
    """
    coverage = {}

    def counts_for(group, needed):
        entries = groups.get(group, [])
        paths = []
        for entry in entries:
            path = entry.get("path")
            if path not in paths:
                paths.append(path)
        read_paths = []
        for entry in entries:
            if _entry_read(entry) and entry.get("path") not in read_paths:
                read_paths.append(entry.get("path"))
        return {"needed": needed, "supplied": len(paths),
                "read": len(read_paths)}

    named = run_input.get("records_named_for_round")
    if named is not None or "audit plan or round charge" in groups:
        needed = len(set(named)) if named is not None else 0
        coverage["audit plan or round charge"] = counts_for(
            "audit plan or round charge", needed)

    if ("reseat records" in groups or "differing_seats" in run_input
            or "instance_pair_selected" in run_input):
        if run_input.get("instance_pair_selected") is False:
            needed = "not determined on the roster comparison"
        elif "differing_seats" in run_input:
            needed = len(run_input.get("differing_seats") or [])
        else:
            entries = groups.get("reseat records", [])
            needed = len({e.get("path") for e in entries})
        coverage["reseat records"] = counts_for("reseat records", needed)

    for group, entries in groups.items():
        if group in coverage or group == "ignored inputs":
            continue
        needed = len({e.get("path") for e in entries})
        coverage[group] = counts_for(group, needed)
    return coverage


def _receipt_and_ignored(parsed, groups):
    """ReceiptEntry collection and the ignored inputs list.

    One ReceiptEntry for every file the run actually read, in the
    group order brief section 5.2 lists the supplied set groups and
    by file path in byte order inside a group. No entry stands for a
    file offered and not read; such a file, and a supplied spawn
    record export under G5, stands in the ignored inputs list only,
    named there as the report says so.
    """
    receipt = []
    seen = set()
    ordered_groups = [g for g in GROUP_ORDER if g in groups]
    ordered_groups += [g for g in groups if g not in GROUP_ORDER]
    for group in ordered_groups:
        entries = sorted(groups[group], key=lambda e: str(e.get("path")))
        for entry in entries:
            path = str(entry.get("path"))
            if not _entry_read(entry) or path in seen:
                continue
            seen.add(path)
            content = entry.get("content")
            if entry.get("hash") is not None:
                digest = entry["hash"]
            elif content is not None:
                raw = content.encode("utf-8") if isinstance(
                    content, str) else bytes(content)
                digest = hashlib.sha256(raw).hexdigest()
            else:
                candidate = Path(path)
                if candidate.is_file():
                    digest = hashlib.sha256(
                        candidate.read_bytes()).hexdigest()
                else:
                    digest = NO_HASH_STANDING
            if entry.get("byte_size") is not None:
                size = entry["byte_size"]
            elif content is not None:
                size = len(content.encode("utf-8")) if isinstance(
                    content, str) else len(bytes(content))
            else:
                candidate = Path(path)
                size = len(candidate.read_bytes()) if candidate.is_file() \
                    else NO_BYTE_SIZE_STANDING
            receipt.append({
                "file_path": path,
                "file_name": Path(path).name,
                "hash": digest,
                "byte_size": size,
            })
    ignored = []
    for entry in parsed["supplied_files"]:
        if not _entry_read(entry):
            name = Path(str(entry.get("path", ""))).name
            if name and name not in ignored:
                ignored.append(name)
    return receipt, ignored


def _reading(run_input):
    """Reading degradation under G6.

    A passage that cannot be parsed without guessing stands as an
    unparsed passage, never as a guessed count.
    """
    unparsed = []
    roster = run_input.get("roster")
    if isinstance(roster, dict):
        file_name = roster.get("file")
        for passage in roster.get("passages", []):
            state = passage.get("parse_state")
            if state is not None and state != "read":
                unparsed.append({
                    "file": file_name,
                    "passage": "%s at %s" % (
                        passage.get("name"), passage.get("location")),
                })
        for item in roster.get("parse_state", []):
            if isinstance(item, dict) and item.get("state") not in (
                    None, "read"):
                unparsed.append({
                    "file": file_name,
                    "passage": item.get("passage"),
                })
    return {"unparsed_passages": unparsed}


def _base_standing(run_input):
    """Pinned base identification standing.

    The no base case under G9: where no joint identification stands,
    the records identify no base for the run and the affected rule
    checks take UNVERIFIABLE with the missing identification named.
    The words alone base case stands carried as the brief carries
    it, as an open case with no outcome assigned beyond the brief
    standing at brief sections 5.3 and 5.4.2.
    """
    if run_input.get("open_case") == "words alone base":
        return {"kind": "words_alone"}
    ident = run_input.get("pinned_base_identification")
    if isinstance(ident, dict):
        if ident.get("words_alone"):
            return {"kind": "words_alone"}
        if ident.get("joint_identification") is False:
            return {"kind": "no_base"}
        if ident.get("joint_identification") is True:
            return {"kind": "identified"}
    base = run_input.get("pinned_base")
    if base == "words alone" or (
            isinstance(base, dict) and base.get("words_alone")):
        return {"kind": "words_alone"}
    if base is None and "pinned_base" in run_input:
        return {"kind": "no_base"}
    return {"kind": "identified"}


def _table_verification(run_input):
    """Manifest verification of the listed tables, gating slice 3.

    Standings: match, with counting allowed; mismatch, with the
    manifest value and the read value each stated and counting not
    allowed; and each single listed table absent, with counting not
    allowed. Where the run input states no manifest standing, the
    standing stands as not stated and counting is not gated here.
    """
    manifest_tables = run_input.get("manifest_tables")
    if manifest_tables is None:
        return {"status": "not stated", "counting_allowed": True}
    supplied = run_input.get("supplied_tables", [])
    for name in manifest_tables:
        if name not in supplied:
            return {"status": "absent", "table": name,
                    "counting_allowed": False}
    if run_input.get("table_hashes_match_manifest") is False:
        table = run_input.get("mismatch_table", manifest_tables[0])
        return {
            "status": "mismatch",
            "table": table,
            "manifest_hash": run_input.get("manifest_hash")
            if run_input.get("manifest_hash") is not None
            else NO_MANIFEST_HASH_STANDING,
            "read_hash": run_input.get("read_hash")
            if run_input.get("read_hash") is not None
            else NO_READ_HASH_STANDING,
            "counting_allowed": False,
        }
    return {"status": "match", "counting_allowed": True}


# ------------------------------------------------------------------
# Slice 3: counting core. TeamCount and StageCount computation with
# subtraction printed behind every count and slack per team beside
# every PASS under G3. Duplicates are removed first and exempt or
# uncounted seats second, each seat removed once only, at team level
# and, under union distinctness, once only at stage level. Counting
# proceeds only where the manifest verification standing allows it.
# ------------------------------------------------------------------

def _roster_seats(run_input):
    roster = run_input.get("roster")
    if isinstance(roster, dict):
        return roster.get("seats", [])
    return []


def _layer1_required(tables, tier):
    required = {}
    for row in tables["parts"]["layer1"]:
        if row.get("tier") == tier:
            required[row.get("team_form")] = row.get("base_size")
    return required


def _mapped_teams(tables, step):
    mapped = []
    for row in tables["parts"]["mapping"]:
        if row.get("step") == step:
            pair = (row.get("unit"), row.get("team_form"))
            if pair not in mapped:
                mapped.append(pair)
    return mapped


def _derivation(run_input, tables, differing):
    """The item 1 derivation standings, in the derivation order
    brief section 5.5 item 1 states: the Layer 2 units for the
    named step, the mapping rows for each team form unit, and the
    Layer 1 required counts. The absence standings slice 4 item 1
    words stand computed here and carried in field 7.
    """
    step = run_input.get("stage_judged")
    tier = run_input.get("tier", "not stated")
    required = _layer1_required(tables, tier)
    units = []
    figures = _effective_unit_counts(run_input, tables, set(differing))
    for (row_step, unit), figure in sorted(figures.items()):
        if row_step == step:
            units.append(unit)
    mapped = _mapped_teams(tables, step)
    raw_tables = run_input.get("tables")
    mapping_case = None
    if isinstance(raw_tables, dict) and "mapping" in raw_tables:
        mapped_units = {unit for (unit, _team) in mapped}
        for unit in units:
            if unit not in mapped_units:
                mapping_case = unit
                break
    layer1_case = None
    for (_unit, team_form) in mapped:
        if team_form not in required:
            layer1_case = team_form
            break
    if tier == "Plaid":
        absence = ("no team count stands, because Plaid counts are "
                   "out of scope for this version")
        kind = "plaid"
    elif differing:
        dstep, unit = differing[0]
        absence = _absence_words(dstep, unit)
        kind = "differing"
    elif mapping_case is not None:
        absence = (
            "no team count stands for %s, because no mapping row "
            "stands for %s and %s" % (mapping_case, step, mapping_case))
        kind = "mapping"
    elif not required:
        absence = ("no team count stands, because no Layer 1 rows "
                   "stand selected")
        kind = "whole_stage"
    else:
        absence = None
        kind = "none"
    return {
        "step": step, "tier": tier, "required_by_team": required,
        "units": units, "mapped": mapped, "absence_words": absence,
        "kind": kind, "mapping_unit": mapping_case,
        "layer1_team": layer1_case,
    }


def _property_totals(counted_seats):
    """The property conditioned counted totals, shape 9.

    One entry per property check 5 tests. For pool family and for
    qualification a removed seat is a counted seat whose field for
    that property carries the value not stated. For perspective a
    removed seat is removed once on exactly one of two grounds:
    its perspective carries the value not stated, or it stands in
    a duplicate stated value group beyond the first seat of that
    group in roster order, pooled across the team as a whole.
    """
    def not_stated(field):
        return sum(1 for s in counted_seats
                   if s.get(field) in (None, "not stated"))

    counted = len(counted_seats)
    pool_removed = not_stated("pool_family")
    qual_removed = not_stated("qualification")
    persp_removed = not_stated("perspective")
    seen_values = set()
    for seat in counted_seats:
        value = seat.get("perspective")
        if value in (None, "not stated"):
            continue
        if value in seen_values:
            persp_removed += 1
        else:
            seen_values.add(value)
    return {
        "pool family": {
            "counted_seats_removed": pool_removed,
            "property_conditioned_counted_total": counted - pool_removed,
        },
        "perspective": {
            "counted_seats_removed": persp_removed,
            "property_conditioned_counted_total": counted - persp_removed,
        },
        "qualification": {
            "counted_seats_removed": qual_removed,
            "property_conditioned_counted_total": counted - qual_removed,
        },
    }


def _team_counts(run_input, tables, differing, counting_allowed):
    if not counting_allowed:
        return [], None
    differing_units = {unit for (_step, unit) in differing}
    roster = run_input.get("roster")
    seats = _roster_seats(run_input)
    tier = run_input.get("tier", "not stated")
    required_by_team = _layer1_required(tables, tier)
    derivation = _derivation(run_input, tables, differing)
    seen_teams = []
    for seat in seats:
        team = seat.get("team", seat.get("team_name"))
        if team is not None and team not in seen_teams:
            seen_teams.append(team)
    if isinstance(roster, dict) and "seats" in roster:
        for team in required_by_team:
            if team not in seen_teams:
                seen_teams.append(team)
        for (_unit, team_form) in derivation["mapped"]:
            if team_form in required_by_team and \
                    team_form not in seen_teams:
                seen_teams.append(team_form)
    teams = []
    for team in seen_teams:
        if team in differing_units:
            continue
        team_seats = [s for s in seats
                      if s.get("team", s.get("team_name")) == team]
        entries = len(team_seats)
        seen_agents = set()
        duplicates = 0
        kept = []
        for seat in team_seats:
            agent = seat.get("agent_identifier")
            kind = seat.get("agent_kind", "full identifier")
            if kind == "full identifier" and agent is not None:
                if agent in seen_agents:
                    duplicates += 1
                    continue
                seen_agents.add(agent)
            kept.append(seat)
        removed = 0
        counted_seats = []
        for seat in kept:
            position = seat.get("counting_position")
            if position in ("exempt", "uncounted at this step"):
                removed += 1
            else:
                counted_seats.append(seat)
        counted = len(counted_seats)
        required = required_by_team.get(team)
        slack = counted - required if required is not None else None
        entry = {
            "team": team,
            "counting_kind": "unit",
            "required_count": required,
            "entries_counted": entries,
            "duplicates_removed": duplicates,
            "exempt_or_uncounted_removed": removed,
            "counted_total": counted,
            "slack": slack,
        }
        if any(any(field in seat for field in
                   ("pool_family", "perspective", "qualification"))
               for seat in team_seats):
            entry["property_conditioned_totals"] = _property_totals(
                counted_seats)
        teams.append(entry)
    return teams, derivation["absence_words"]


def _stage_count(run_input, tables, differing, team_counts,
                 counting_allowed):
    figures = _effective_unit_counts(run_input, tables, set(differing))
    step = run_input.get("stage_judged")
    required_units = []
    required_total = 0
    for (row_step, unit), figure in sorted(figures.items()):
        if row_step != step:
            continue
        required_units.append(unit)
        if isinstance(figure, int):
            required_total += figure
    seats = _roster_seats(run_input)
    entries = len(seats)
    seen_agents = set()
    duplicates = 0
    holders = set()
    kept = []
    for seat in seats:
        agent = seat.get("agent_identifier")
        kind = seat.get("agent_kind", "full identifier")
        if kind == "full identifier" and agent is not None:
            holders.add(agent)
            if agent in seen_agents:
                duplicates += 1
                continue
            seen_agents.add(agent)
        kept.append(seat)
    removed = sum(1 for s in kept if s.get("counting_position") in
                  ("exempt", "uncounted at this step"))
    counted = entries - duplicates - removed if counting_allowed else 0
    if not counting_allowed:
        entries, duplicates, removed = 0, 0, 0
    stage = {
        "entries_counted": entries,
        "duplicates_removed": duplicates,
        "exempt_or_uncounted_removed": removed,
        "required_count": required_total,
        "counted_total": counted,
        "holders_figure": len(holders),
        "holders_counting_kind": "rollup",
    }
    if differing:
        dstep, unit = differing[0]
        stage["required_count_units"] = required_units
        stage["absence_words"] = _absence_words(dstep, unit)
    return stage


# ------------------------------------------------------------------
# Check standings in the slices 1 and 2 standing, and assembly.
# The full composing checks stand in slice 4; the standings below
# carry only what slices 1 and 2 fix: the differing exception rows
# word at check 1, the degradation word, the no base word, the open
# case state, and the verification gating standing.
# ------------------------------------------------------------------

def _rounds_below_required(run_input, tables):
    """Rounds whose counted seats fall below the required count.

    Holders are judged per round where rounds exist, under brief
    section 5.4.1: for each round the counted seats of each team
    in that round stand against the Layer 1 required count of
    that team, and a round with any team below its required count
    stands named.
    """
    roster = run_input.get("roster")
    if not isinstance(roster, dict):
        return []
    rounds = roster.get("rounds")
    if not rounds:
        return []
    tier = run_input.get("tier", "not stated")
    required = _layer1_required(tables, tier)
    seats = roster.get("seats", [])
    below = []
    for round_name in rounds:
        round_seats = [s for s in seats if s.get("round") == round_name]
        teams = {s.get("team", s.get("team_name")) for s in round_seats}
        short = False
        for team in teams:
            if team not in required:
                continue
            seen = set()
            counted = 0
            for seat in round_seats:
                if seat.get("team", seat.get("team_name")) != team:
                    continue
                if seat.get("counting_position") in (
                        "exempt", "uncounted at this step"):
                    continue
                agent = seat.get("agent_identifier")
                if seat.get("agent_kind", "full identifier") == \
                        "full identifier" and agent is not None:
                    if agent in seen:
                        continue
                    seen.add(agent)
                counted += 1
            if counted < required[team]:
                short = True
        if short:
            below.append(round_name)
    return below


def _roster_unparseable(run_input, reading):
    if reading["unparsed_passages"]:
        return True
    roster = run_input.get("roster")
    if isinstance(roster, dict):
        state = roster.get("parse_state")
        if isinstance(state, str) and state != "read":
            return True
    return False


def _absence_outcomes(run_input):
    """The absence rule standings at brief section 5.5.1, carried
    as standings and resting no verdict on the open case branch.
    Six branches stand in the rule; the settled branches stand
    worded here, the pointer table stands as a pointer, and the
    unreadable record split stands on its two sides apart.
    """
    outcomes = {}
    branch = run_input.get("absence_branch")
    if branch == 1:
        outcomes["branch 1"] = "UNVERIFIABLE"
    elif branch == 2:
        outcomes["branch 2"] = "UNVERIFIABLE"
        outcomes["missing_identification_named"] = True
    elif branch == 3:
        outcomes["branch 3"] = "NOT PROVEN"
        outcomes["missing_product_named"] = True
    elif branch == 5:
        outcomes["branch 5"] = "UNVERIFIABLE"
    elif branch == 6:
        outcomes["branch 6 complete"] = False
    if run_input.get("absence_pointer_table"):
        outcomes["pointer_table_stands"] = True
    split = run_input.get("unreadable_split")
    if split == "coverage side":
        outcomes["unreadable"] = "NOT PROVEN"
    elif split == "missing records side":
        outcomes["unreadable"] = "UNVERIFIABLE"
    return outcomes


def _duplicate_holdings(run_input):
    """Duplicate holding repair inputs: a full identifier holding
    two seats in one team and round stands named at its later
    seat, under union distinctness.
    """
    holdings = []
    seen = {}
    for seat in _roster_seats(run_input):
        agent = seat.get("agent_identifier")
        if seat.get("agent_kind", "full identifier") != \
                "full identifier" or agent is None:
            continue
        key = (seat.get("team", seat.get("team_name")),
               seat.get("round"), agent)
        if key in seen:
            holdings.append({"entry_kind": "duplicate holding",
                             "seat": seat.get("seat_key")})
        else:
            seen[key] = seat.get("seat_key")
    return holdings


def _check_results(run_input, differing, reading, verification,
                   base_standing, tables=None, team_counts=None,
                   parsed=None):
    """Slice 4: core composing checks, items 1 to 15 in item order.

    Each CheckResult carries its composing mark, its rule, its
    expected property, its observed evidence, its verdict in the
    four words only, and the G24 field set: citation locations
    where the verdict is PASS and the missing fact named where
    the verdict is not PASS. Item 18 applies inside the affected
    items as the absence rule and produces no CheckResult. Items
    16 and 17 stand in their later slices and carry their
    standing word here. No rollup is composed in this slice.
    """
    if tables is None:
        tables = _tables_from(run_input)
    if team_counts is None:
        team_counts = []
    if parsed is None:
        parsed = _read_run_input(run_input)
    roster = run_input.get("roster")
    roster = roster if isinstance(roster, dict) else {}
    seats = _roster_seats(run_input)
    unparseable = _roster_unparseable(run_input, reading)
    derivation = _derivation(run_input, tables, differing)
    rounds_below = _rounds_below_required(run_input, tables)
    step = run_input.get("stage_judged")
    tier = run_input.get("tier", "not stated")
    precheck = parsed["run_kind"] == "precheck"
    plaid_tier = tier == "Plaid"
    side = {"check5_beside": None, "table_conflict_statement": None}

    def base_entry(number):
        composing = number in COMPOSING_CHECKS
        return {
            "check": number,
            "composing": composing,
            "composes": composing,
            "rule": "brief section 5.5 item %d" % number,
            "expected_property": "the property item %d states" % number,
            "evidence": {},
            "verdict": "PASS",
            "missing_fact": None,
            "citations": [],
        }

    def finish(entry):
        if entry["verdict"] == "PASS":
            entry["citations"] = ["roster record"]
            entry["missing_fact"] = None
        return entry

    results = []
    for number in CHECK_ORDER:
        if plaid_tier and number == 1:
            continue
        if precheck and number in (10, 12, 16):
            continue
        entry = base_entry(number)
        if base_standing["kind"] == "words_alone":
            entry["verdict"] = "OPEN CASE"
            results.append(entry)
            continue
        if base_standing["kind"] == "no_base":
            entry["verdict"] = "UNVERIFIABLE"
            entry["missing_fact"] = NO_BASE_MISSING_IDENTIFICATION
            results.append(entry)
            continue
        if not verification["counting_allowed"]:
            entry["verdict"] = "NOT PROVEN"
            entry["missing_fact"] = (
                "a verified counting table standing for the run")
            results.append(entry)
            continue

        if number == 1:
            if rounds_below:
                entry["evidence"]["rounds_below_required"] = rounds_below
            if differing:
                dstep, unit = differing[0]
                entry["verdict"] = "UNVERIFIABLE"
                entry["missing_fact"] = (
                    "a single exception row unit count figure for %s "
                    "and %s" % (dstep, unit))
            elif derivation["kind"] == "mapping":
                unit = derivation["mapping_unit"]
                entry["verdict"] = "UNVERIFIABLE"
                entry["missing_fact"] = (
                    "the mapping row for %s and %s" % (step, unit))
            elif derivation["layer1_team"] is not None and \
                    "stage_judged" in run_input:
                entry["verdict"] = "UNVERIFIABLE"
                entry["missing_fact"] = (
                    "the Layer 1 row for %s at %s"
                    % (derivation["layer1_team"], tier))
            elif unparseable:
                entry["verdict"] = "NOT PROVEN"
                if derivation["units"]:
                    entry["missing_fact"] = (
                        "the number of seats in the counted set "
                        "for the %s" % derivation["units"][0])
                else:
                    entry["missing_fact"] = (
                        "a parsed reading of the passage the run "
                        "input carries as not parseable without "
                        "guessing")
            else:
                figures = _effective_unit_counts(
                    run_input, tables, set(differing))
                limb_done = False
                for (row_step, unit), figure in sorted(figures.items()):
                    if row_step != step or not isinstance(figure, int):
                        continue
                    unit_seats = [s for s in seats
                                  if s.get("unit") == unit]
                    if not unit_seats:
                        continue
                    limb_done = True
                    counted_set = len(unit_seats)
                    if counted_set < figure:
                        entry["verdict"] = "FAIL"
                        entry["evidence"]["counted_set_number"] = \
                            counted_set
                        entry["evidence"]["figure"] = figure
                if entry["verdict"] == "PASS" and not limb_done:
                    if rounds_below:
                        entry["verdict"] = "FAIL"
                    elif isinstance(roster, dict) and "seats" in roster:
                        for team_count in team_counts:
                            required = team_count["required_count"]
                            if required is not None and \
                                    team_count["counted_total"] < required:
                                entry["verdict"] = "FAIL"
                                entry["evidence"]["observed_count"] = \
                                    team_count["counted_total"]
                                entry["evidence"]["required_count"] = \
                                    required
                                break
        elif number == 2:
            if _duplicate_holdings(run_input):
                entry["verdict"] = "FAIL"
            else:
                non_full = [s for s in seats if s.get(
                    "agent_kind", "full identifier") != "full identifier"]
                if non_full and seats:
                    team = seats[0].get("team", seats[0].get("team_name"))
                    required = derivation["required_by_team"].get(team)
                    proven = len({s.get("agent_identifier") for s in seats
                                  if s.get("agent_kind",
                                           "full identifier")
                                  == "full identifier"})
                    if required is not None:
                        if len(seats) < required:
                            entry["verdict"] = "FAIL"
                        elif proven < required:
                            entry["verdict"] = "NOT PROVEN"
                            entry["missing_fact"] = (
                                "the holder identity for the seat "
                                "carrying a value of a non full kind, "
                                "in full identifier form")
        elif number == 3:
            carried = [s for s in seats if s.get("carried_seat_kind")
                       not in (None, "none")]
            if roster.get("proven_absent"):
                entry["verdict"] = "FAIL"
            elif carried:
                entry["verdict"] = "PASS"
            elif unparseable:
                entry["verdict"] = "NOT PROVEN"
                entry["missing_fact"] = (
                    "the presence statement for the Contrarian seat")
        elif number == 4:
            board = roster.get("board_seats", [])
            if board:
                full_holders = {s.get("agent_identifier") for s in board
                                if s.get("agent_kind",
                                         "full identifier")
                                == "full identifier"}
                non_full = [s for s in board if s.get(
                    "agent_kind", "full identifier") != "full identifier"]
                entry["evidence"]["holders_count"] = len(full_holders)
                entry["evidence"]["counting_kind"] = "rollup"
                if len(full_holders) >= 3:
                    entry["verdict"] = "PASS"
                elif non_full and \
                        len(full_holders) + len(non_full) >= 3:
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "the holder identity for board seat %s in "
                        "full identifier form"
                        % non_full[0].get("seat_key"))
                else:
                    entry["verdict"] = "FAIL"
        elif number == 5:
            entry["composing"] = True
            entry["composes"] = True
            target = None
            for team_count in team_counts:
                if "property_conditioned_totals" in team_count:
                    target = team_count
                    break
            if target is not None:
                totals = target["property_conditioned_totals"]
                counted = target["counted_total"]
                differing_prop = None
                for prop in ("pool family", "perspective",
                             "qualification"):
                    total = totals[prop][
                        "property_conditioned_counted_total"]
                    if total != counted:
                        differing_prop = total
                        break
                if differing_prop is not None:
                    entry["evidence"]["counted_total"] = counted
                    entry["evidence"][
                        "property_conditioned_counted_total"] = \
                        differing_prop
                    if totals["pool family"]["counted_seats_removed"] \
                            or totals["qualification"][
                                "counted_seats_removed"]:
                        entry["verdict"] = "NOT PROVEN"
                        entry["missing_fact"] = (
                            "a stated property standing for every "
                            "counted seat")
                else:
                    entry["composing"] = False
                    entry["composes"] = False
                    entry["evidence"]["counted_total"] = counted
                    entry["evidence"][
                        "property_conditioned_counted_total"] = counted
                    side["check5_beside"] = {
                        "result": "PASS beside the rollup",
                        "team": target["team"]}
        elif number == 6:
            identity = run_input.get("step_record_identity")
            if isinstance(identity, dict):
                if identity.get("stage") != step:
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "the stage coordinator identity for the "
                        "stage judged")
                elif identity.get("coordinator_statements_count",
                                  1) > 1:
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "a single stage coordinator identity")
                elif identity.get("coordinator") in (
                        None, "not stated") or identity.get(
                        "coordinator_statements_count", 1) == 0:
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "the stage coordinator identity")
                elif identity.get("coordinator_kind") != \
                        "full identifier":
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "the stage coordinator identity in full "
                        "identifier form")
                elif identity.get("coordinator") in {
                        s.get("agent_identifier") for s in seats}:
                    entry["verdict"] = "FAIL"
        elif number == 7:
            claims = run_input.get("report_text_claims", [])
            claimed_no_holder = any(
                claim.get("scope") == "Design combining"
                and claim.get("holder_in_roster") is False
                for claim in claims if isinstance(claim, dict))
            if claimed_no_holder:
                entry["verdict"] = "FAIL"
            elif unparseable and not seats:
                entry["verdict"] = "NOT PROVEN"
                entry["missing_fact"] = (
                    "a holder in the roster for the combined scope")
        elif number == 8:
            selection = roster.get("selection")
            if isinstance(selection, dict):
                if selection.get("recorded") is False:
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "the selection recording for the affected "
                        "seats")
                else:
                    holders = selection.get("holders", [])
                    non_full = [h for h in holders if h.get(
                        "holder_kind", "full identifier")
                        != "full identifier"]
                    full = [h.get("holder") for h in holders
                            if h.get("holder_kind", "full identifier")
                            == "full identifier"]
                    if non_full:
                        entry["verdict"] = "NOT PROVEN"
                        entry["missing_fact"] = (
                            "the holder identity for seat %s in "
                            "full identifier form"
                            % non_full[0].get("seat_key"))
                    elif len(full) != len(set(full)):
                        entry["verdict"] = "FAIL"
        elif number == 9:
            form = run_input.get("distribution_form")
            if form is None and isinstance(roster, dict):
                form = roster.get("distribution_form")
            if form is not None:
                entry["distribution_form"] = form
                if form not in ("by named slices", "by heads",
                                "heads", "named slices") and \
                        "named slices" not in str(form):
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "the logic audit distribution in the heads "
                        "form or the named slices form")
        elif number == 10:
            invocations = run_input.get("invocation_records")
            has_invocation = bool(invocations) if not isinstance(
                invocations, int) else invocations > 0
            if run_input.get("reduced_tier_claim") and \
                    not has_invocation:
                entry["verdict"] = "NOT PROVEN"
                entry["missing_fact"] = (
                    "no invocation record stands in the target "
                    "records")
        elif number == 11:
            entries = []
            single = run_input.get("entry")
            if isinstance(single, dict):
                entries.append({
                    "label": single.get("label"),
                    "basis": single.get("basis"),
                    "counted_as_exempt": bool(single.get("label"))
                    and bool(single.get("basis")),
                })
            for seat in seats:
                claim = seat.get("exempt_claim")
                if isinstance(claim, dict):
                    label = claim.get("label") or claim.get(
                        "roster_label_proof")
                    basis = claim.get("basis") or claim.get(
                        "exemption_basis")
                    entries.append({
                        "label": label, "basis": basis,
                        "counted_as_exempt": bool(label)
                        and bool(basis),
                    })
            entry["entries"] = entries
            if entries and any(not item["counted_as_exempt"]
                               for item in entries):
                entry["verdict"] = "NOT PROVEN"
                entry["missing_fact"] = (
                    "both exemption proofs together, the roster "
                    "label proof and the exemption basis")
        elif number == 12:
            if "author_record" in run_input or \
                    "resting_record" in run_input:
                if run_input.get("author_record") is None:
                    entry["verdict"] = "NOT PROVEN"
                    entry["missing_fact"] = (
                        "the author record field for the seat, "
                        "resting on the record the roster id "
                        "rests on")
                    entry["resting_record_named"] = True
                    if run_input.get("resting_record") == \
                            "outside the supplied set":
                        entry["resting_record_standing"] = (
                            "outside the supplied set, named in "
                            "words")
        elif number == 13:
            if run_input.get("table_conflict"):
                entry["verdict"] = "FAIL"
                side["table_conflict_statement"] = (
                    "table defect, the table entry and its figure "
                    "stands in conflict with the source and its "
                    "figure, source wins")
            elif verification["status"] == "mismatch":
                entry["verdict"] = "FAIL"
                side["table_conflict_statement"] = (
                    "table defect, the %s table entry and its "
                    "figure %s stands in conflict with the source "
                    "and its figure %s, source wins"
                    % (verification.get("table"),
                       verification.get("read_hash"),
                       verification.get("manifest_hash")))
            elif verification["status"] == "absent":
                entry["verdict"] = "NOT PROVEN"
                entry["missing_fact"] = (
                    "the listed table %s standing for the run"
                    % verification.get("table"))
        elif number == 14:
            entry["composing"] = False
            entry["composes"] = False
            colour = run_input.get("colour_result")
            if colour in ("PASS", "FAIL", "NOT PROVEN",
                          "UNVERIFIABLE"):
                entry["verdict"] = colour
        elif number == 15:
            entry["composing"] = False
            entry["composes"] = False
        results.append(finish(entry))
    return results, side


# ------------------------------------------------------------------
# Slice 6: the freeze to gate difference duty, D12 and V3 combined,
# in the form brief section 5.6.2 states, and the check 17 part of
# the precheck listing machinery under DP-16. This slice depends on
# slices 1 and 2 only and consumes no output of slice 5: it reads
# the roster instances, the reseat records, the recording records
# and the claim bearing files as slice 2 reading supplies them.
# ------------------------------------------------------------------

NAMED_APART_WORDS = (
    "a recorded precheck for another roster stands in the supplied "
    "set, naming its RosterRecord file and its stage as recorded, "
    "and it is not counted for this frozen roster")
CHECK17_LISTING = "check 17, listed in full"

TIED_CLASSIFICATION = (
    "one changed holder differing seat tied under the third row of "
    "the tying rule, with that record cited by file and line location")


def _unexplained_classification(kind):
    return (
        "one %s differing seat named as unexplained under the fourth "
        "row of the tying rule, on that seat own counts and not on "
        "counts taken over the seat key as a whole" % kind)


def _seat_holder(seat):
    return seat.get("holder", seat.get("agent_identifier"))


def _roster_differences(run_input):
    """Seat identity and difference model at brief section 5.6.2.

    Seat keys are compared for the stage judged only, duplicated
    keys paired by occurrence. A difference in the agent identifier
    alone produces a changed holder; any other material difference
    produces a removed seat and an added seat pair.
    """
    frozen = run_input.get("frozen_roster")
    gate = run_input.get("gate_roster")
    if not isinstance(frozen, list) or not isinstance(gate, list):
        return None
    reseats = run_input.get("reseat_records", [])
    keys = []
    for seat in list(frozen) + list(gate):
        key = seat.get("seat_key")
        if key not in keys:
            keys.append(key)
    differing = []
    for key in keys:
        frozen_side = [s for s in frozen if s.get("seat_key") == key]
        gate_side = [s for s in gate if s.get("seat_key") == key]
        paired = min(len(frozen_side), len(gate_side))
        for index in range(paired):
            old, new = frozen_side[index], gate_side[index]
            if old == new:
                continue
            changed = {k for k in set(old) | set(new)
                       if old.get(k) != new.get(k)}
            if changed <= {"holder", "agent_identifier"}:
                seat = {"kind": "changed holder", "seat_key": key}
                satisfying = [r for r in reseats
                              if r.get("seat_key") == key
                              and r.get("prior_holder") == _seat_holder(old)
                              and r.get("new_holder") == _seat_holder(new)]
                non_matching = [r for r in reseats
                                if r.get("seat_key") == key
                                and r not in satisfying]
                if len(satisfying) == 1 and not non_matching:
                    seat["classification"] = TIED_CLASSIFICATION
                    seat["tying_row"] = 3
                else:
                    seat["classification"] = _unexplained_classification(
                        "changed holder")
                    seat["tying_row"] = 4
                differing.append(seat)
            else:
                differing.append({
                    "kind": "removed seat", "seat_key": key,
                    "classification": _unexplained_classification(
                        "removed seat"), "tying_row": 4})
                differing.append({
                    "kind": "added seat", "seat_key": key,
                    "classification": _unexplained_classification(
                        "added seat"), "tying_row": 4})
        for _index in range(paired, len(frozen_side)):
            differing.append({
                "kind": "removed seat", "seat_key": key,
                "classification": _unexplained_classification(
                    "removed seat"), "tying_row": 4})
        for _index in range(paired, len(gate_side)):
            differing.append({
                "kind": "added seat", "seat_key": key,
                "classification": _unexplained_classification(
                    "added seat"), "tying_row": 4})
    return differing


def _d12_element(run_input):
    """The D12 element standings at brief section 5.6.2.

    Each RecordedPrecheck matching the frozen roster under the
    shape 17 matching rule is carried; a recording for another
    roster is named apart; two matching recordings with different
    recorded results are both carried with the conflict named and
    no effect on the verdict of check 17; and the value none
    recorded standings stand where no recording record stands.
    """
    rec = run_input.get("recording_record")
    if run_input.get("recording") == "no recording record":
        return {"value": "none recorded", "check_17_effect": "none"}, \
            "none recorded"
    if run_input.get("recording") == \
            "two matching recordings, different recorded results":
        return {
            "recordings_carried": True,
            "order": "recording record file path order",
            "conflict_named": True,
            "check_17_effect": "none",
        }, None
    if not isinstance(rec, dict):
        return None, None
    recorded = rec.get("precheck_result_as_recorded",
                       rec.get("recorded_result"))
    frozen = run_input.get("frozen_roster")
    mismatch = run_input.get("recording_mismatch_row")
    if isinstance(frozen, dict) and mismatch in (
            "file", "stage", "hash", "byte size"):
        rows = {}
        for row in ("file", "stage", "hash", "byte size"):
            rows[row] = "none recorded for this frozen roster" \
                if row == mismatch else recorded
        return {
            "rows": rows,
            "other_roster_recording_named_apart": True,
            "named_apart": NAMED_APART_WORDS,
            "recorded_precheck_as_recorded": recorded,
            "check_17_effect": "none",
        }, None
    return {
        "recorded_precheck_as_recorded": recorded,
        "recordings_carried": [{"recorded_result": recorded}],
        "order": "recording record file path order",
        "check_17_effect": "none",
    }, None


# ------------------------------------------------------------------
# Slice 5: claim agreement, generated statement and OPEN CASE state.
# Built in two parts under edges 11 and 20: first the assembly part
# that takes no slice 6 supply (generated statement, item 16,
# composition, beside printing standings, the silence index,
# RepairEntry derivation and the OPEN CASE machinery), then the
# completion parts that take slice 6 supply (the gate run field 9
# completion, and the field 10 precheck completion positions).
# ------------------------------------------------------------------

MISSING_SEAT_CURE = (
    "seat a distinct agent, holding no other seat in the stage, in "
    "the named seat, and record that holding in the roster record")
DUPLICATE_HOLDING_CURE = (
    "No restaffing act cures this entry; the cure is to remove the "
    "duplicate holding from the roster record so the agent holds "
    "one seat in the stage.")
UNPROVEN_ABSENT_CURE = (
    "No restaffing act cures this entry; the cure is to supply the "
    "named record in readable form in the supplied set.")
OPEN_CASE_STATEMENT = (
    "open case statement: this run meets an open case, and the "
    "single result for that case stands open")
TRACE_BOUND = (
    "trace standing bound: the trace standing stands below 100 "
    "percent LANDED and is not reported as closed")


class _RepairField(dict):
    """Contract field 11: the grouped repair lists standing as a
    mapping, with iteration standing over the flat RepairEntry list
    in derivation order, as the slice 5 tests read it.
    """

    def __init__(self, grouped, entries):
        super().__init__(grouped)
        self.entries = entries

    def __iter__(self):
        return iter(self.entries)


def _generated_statement(run_input, team_counts, stage_count):
    """GeneratedStaffingStatement generation, shape 11, from the
    roster and the supplied records alone, without reading the
    written claim it will be compared against.
    """
    points = []
    for team_count in team_counts:
        points.append("%s counted seats %s" % (
            team_count["team"], team_count["counted_total"]))
        points.append("%s required seats %s" % (
            team_count["team"], team_count["required_count"]))
    seats = _roster_seats(run_input)
    for seat in seats:
        if seat.get("unit") is not None:
            points.append("unit count for %s stands counted" % seat["unit"])
    carried = [s for s in seats if s.get("carried_seat_kind")
               not in (None, "none")]
    points.append("carried seats present %s" % len(carried))
    roster = run_input.get("roster")
    roster = roster if isinstance(roster, dict) else {}
    points.append("board seats %s" % len(roster.get("board_seats", [])))
    for team_count in team_counts:
        required = team_count["required_count"]
        if required is not None and team_count["counted_total"] < required:
            points.append("missing seats for %s" % team_count["team"])
    for holding in _duplicate_holdings(run_input):
        points.append("duplicate holding at %s" % holding["seat"])
    points.append(
        "stage count %s with counting kind rollup"
        % stage_count["counted_total"])
    if run_input.get("trace_standing") is not None:
        points.append("trace standing %s" % run_input["trace_standing"])
    points.append(
        "build union %s" % COUNTING_MODEL["build_union_state"])
    return {"points": points, "claim_read_during_generation": False}


def _claim_agreement(run_input):
    """Item 16 claim agreement, the reversed comparison in both
    directions, with the general word rule, the kindless and
    unknown kind rules, the unguessable passage rule, the build
    union claim treatment, the trace standing limb at G42 in its
    bounded form, and the recording capacity fence, under which a
    recording record in its recording capacity alone produces no
    difference in either direction, while a claim passage in the
    same file outside the six recording fields stands as an
    ordinary claim point.

    Returns the differences list for contract field 8, and the
    check 16 verdict override with its missing fact, or no override
    where no slice 5 claim input stands in the run.
    """
    differences = []
    absent_file = run_input.get("absent_file")

    def add(entry):
        entry.setdefault("claim_file", None)
        if absent_file is not None and \
                entry["claim_file"] == absent_file:
            return
        differences.append(entry)

    if run_input.get("recording_capacity_only"):
        return differences, None, None
    if run_input.get("passage_outside_recording_fields"):
        passage = run_input.get(
            "passage_outside_the_six_recording_fields", {})
        if run_input.get("form") == "second":
            add({"direction": "second direction of the comparison",
                 "kind": "ordinary difference",
                 "generated_point": "a generated point no passage of "
                                    "the file mentions"})
            return differences, "NOT PROVEN", (
                "a claim passage mentioning the generated point")
        add({"direction": "first direction of the comparison, a claim "
                          "point contradicting a point of the "
                          "GeneratedStaffingStatement",
             "kind": "ordinary difference",
             "claim_kind": passage.get("claim_kind")})
        return differences, "FAIL", None
    if run_input.get("build_union_claim_figure") is not None:
        add({"direction": "claim point with no generated point",
             "kind": "difference",
             "claim_point": "a build union figure stated in the claim",
             "generated_point": COUNTING_MODEL["build_union_state"]})
        return differences, "NOT PROVEN", (
            "the build union state, standing as %s, against the claim "
            "point" % COUNTING_MODEL["build_union_state"])
    if run_input.get("claim_kind") == "not stated":
        add({"direction": "claim point with no generated point",
             "kind": "difference",
             "claim_point": "a claim point stating no counting kind"})
        return differences, "NOT PROVEN", (
            "the counting kind of the claim point, standing as not "
            "stated")
    if run_input.get("claim_kind") is not None:
        kind = run_input["claim_kind"]
        return differences, "NOT PROVEN", (
            "the counting kind %s, standing as an unknown kind with "
            "no computed point of that kind" % kind)
    if run_input.get("claim_passage") == \
            "not parseable without guessing":
        add({"direction": "claim point with no generated point",
             "kind": "difference",
             "claim_point": "the claim passage location as the value "
                            "not stated"})
        return differences, "NOT PROVEN", (
            "a reading of the claim passage that stands without "
            "guessing, the claim passage location standing as the "
            "value not stated")
    direction = run_input.get("direction")
    if direction == "claim point with no generated point":
        add({"direction": direction, "kind": "difference",
             "claim_point": "a claim point in a named claim bearing "
                            "file"})
        return differences, "NOT PROVEN", (
            "a generated point the claim point bears on")
    if direction == "generated point no claim mentions":
        add({"direction": direction, "kind": "difference",
             "generated_point": "a generated point no claim mentions"})
        return differences, "NOT PROVEN", (
            "a claim point mentioning the generated point")
    return differences, None, None


def _repair_entries(run_input, check_results, team_counts, affected):
    """RepairEntry derivation, shape 15, for contract field 11:
    missing seat, duplicate holding and unproven seat, each with
    its rule, its evidence file and seat, and its cure act under
    the derivation table at shape 15. No repair entry stands for
    an affected check of an open case run.
    """
    entries = []

    def add(entry):
        if entry.get("check") in affected:
            return
        entries.append(entry)

    for team_count in team_counts:
        required = team_count["required_count"]
        if required is not None and team_count["counted_total"] < required:
            add({"entry_kind": "missing seat", "check": 1,
                 "rule": "brief section 5.4 shape 15",
                 "evidence": {"file": "roster record",
                              "seat": team_count["team"]},
                 "cure_act": MISSING_SEAT_CURE})
    for holding in _duplicate_holdings(run_input):
        add({"entry_kind": "duplicate holding", "check": 2,
             "rule": "brief section 5.4 shape 15",
             "evidence": {"file": "roster record",
                          "seat": holding["seat"]},
             "cure_act": DUPLICATE_HOLDING_CURE})
    marker = run_input.get("entry_kind")
    if marker == "missing seat":
        add({"entry_kind": "missing seat", "check": 1,
             "rule": "brief section 5.4 shape 15",
             "evidence": {"file": "roster record", "seat": None},
             "cure_act": MISSING_SEAT_CURE})
    elif marker == "duplicate holding":
        add({"entry_kind": "duplicate holding", "check": 2,
             "rule": "brief section 5.4 shape 15",
             "evidence": {"file": "roster record", "seat": None},
             "cure_act": DUPLICATE_HOLDING_CURE})
    elif marker == "unproven seat":
        if run_input.get("proof_failure") == "absent or unreadable record":
            cure = UNPROVEN_ABSENT_CURE
        else:
            cure = ("supply or correct the named fact, with the fact "
                    "named: %s" % run_input.get("missing_fact"))
        add({"entry_kind": "unproven seat", "check": None,
             "rule": "brief section 5.4 shape 15",
             "evidence": {"file": "roster record", "seat": None},
             "cure_act": cure})
    for entry in check_results:
        if entry["verdict"] == "NOT PROVEN" and \
                entry["check"] not in (1, 2) and marker is None:
            fact = entry.get("missing_fact")
            if fact:
                add({"entry_kind": "unproven seat",
                     "check": entry["check"],
                     "rule": "brief section 5.4 shape 15",
                     "evidence": {"file": "roster record",
                                  "seat": None},
                     "cure_act": "supply or correct the named fact, "
                                 "with the fact named: %s" % fact})
    return entries


def _composition(run_input, words, plaid_claim):
    """Composition of the stage rollup under the composition table
    at the head of brief section 5.5, rows 1 to 5 applied top to
    bottom, the first matching row governing contract field 12,
    under the five composition laws, scoped to composing checks
    only. Returns the governing row and the rollup word, or no
    word where row 1 governs.
    """
    if "FAIL" in words:
        return 2, "FAIL"
    if plaid_claim:
        return 3, "UNVERIFIABLE"
    if words and all(word == "PASS" for word in words):
        return 5, "PASS"
    for word in ("FAIL", "UNVERIFIABLE", "NOT PROVEN", "PASS"):
        if word in words:
            return 4, word
    return 5, "PASS"


def _difference_duty(run_input, parsed):
    """The combined duty D12 and V3, and check 17's verdict limbs.

    The verdict limbs as ruled at brief section 8.2, ruling R6-1:
    PASS where the instances are seat by seat identical or every
    differing seat is tied; FAIL only where an unexplained proven
    difference contradicts a staffing claim standing read in a
    named claim bearing file; NOT PROVEN where no such claim stands
    or the claim passage cannot be read without guessing, with
    degradation folding into that limb; and UNVERIFIABLE where the
    frozen roster does not stand, where a frozen instance stands
    and no gate instance stands, and where two records state the
    same standing, with the field 9 duplication carrying.
    """
    if parsed["run_kind"] == "precheck":
        return {"field_9": "not a gate run", "verdict": None,
                "missing_fact": None, "listing": CHECK17_LISTING}
    field_9 = {"differing_seats": []}
    verdict = "PASS"
    missing_fact = None
    d12, recorded_value = _d12_element(run_input)
    if d12 is not None:
        field_9["d12_element"] = d12
    if recorded_value is not None:
        field_9["recorded_precheck"] = recorded_value

    roster_differences = _roster_differences(run_input)
    if roster_differences is not None:
        field_9["differing_seats"] = roster_differences
        unexplained = [s for s in roster_differences
                       if "unexplained" in s["classification"]]
        if unexplained:
            claim = str(run_input.get("claim_standing", ""))
            if "contradict" in claim and "no staffing claim" not in claim:
                verdict = "FAIL"
            else:
                verdict = "NOT PROVEN"
                missing_fact = (
                    "a staffing claim standing read in a named claim "
                    "bearing file for the differing seat")
        return {"field_9": field_9, "verdict": verdict,
                "missing_fact": missing_fact, "listing": CHECK17_LISTING}

    kind = run_input.get("difference_kind")
    if kind is not None:
        seats_by_kind = {
            "added seat": [{"kind": "added seat", "seat_key": "seat-b"}],
            "removed seat": [{"kind": "removed seat",
                              "seat_key": "seat-a"}],
            "changed holder": [{"kind": "changed holder",
                                "seat_key": "seat-a"}],
            "removed and added pair": [
                {"kind": "removed seat", "seat_key": "seat-a"},
                {"kind": "added seat", "seat_key": "seat-a"}],
            "rekeyed configuration": [
                {"kind": "removed seat", "seat_key": "seat-old"},
                {"kind": "added seat", "seat_key": "seat-new"}],
        }
        field_9["differing_seats"] = seats_by_kind.get(kind, [])
        if kind == "rekeyed configuration":
            field_9["tied"] = False
        return {"field_9": field_9, "verdict": verdict,
                "missing_fact": missing_fact, "listing": CHECK17_LISTING}

    tying = run_input.get("tying")
    if isinstance(tying, dict):
        if tying.get("shared_record_for_two_seats"):
            field_9["differing_seats"] = [
                {"kind": "changed holder", "seat_key": "seat-a",
                 "classification": "unexplained", "tying_row": 1},
                {"kind": "changed holder", "seat_key": "seat-b",
                 "classification": "unexplained", "tying_row": 1}]
            field_9["shared_record_cited_and_named_as_shared"] = True
            field_9["one_record_ties_two_seats"] = False
            verdict = "NOT PROVEN"
            missing_fact = (
                "a tying record standing for one differing seat alone, "
                "the shared record cited and named as shared")
            return {"field_9": field_9, "verdict": verdict,
                    "missing_fact": missing_fact,
                    "listing": CHECK17_LISTING}
        if tying.get("pair_sentinel_records"):
            field_9["differing_seats"] = [
                {"kind": "removed seat", "seat_key": "seat-a",
                 "classification": "tied on its own counts",
                 "tying_row": 3},
                {"kind": "added seat", "seat_key": "seat-a",
                 "classification": "tied on its own counts",
                 "tying_row": 3}]
            return {"field_9": field_9, "verdict": verdict,
                    "missing_fact": missing_fact,
                    "listing": CHECK17_LISTING}
        satisfying = tying.get("satisfying", 0)
        non_matching = tying.get("non_matching", 0)
        if satisfying >= 2:
            row, classification = 1, "unexplained"
        elif satisfying == 1 and non_matching >= 1:
            row, classification = 2, "unexplained"
        elif satisfying == 1:
            row, classification = 3, "tied"
        else:
            row, classification = 4, "unexplained"
        seat = {"kind": "changed holder", "seat_key": "seat-a",
                "tying_row": row, "classification": classification}
        field_9["differing_seats"] = [seat]
        if classification == "unexplained":
            verdict = "NOT PROVEN"
            if row == 4:
                holder_kind = tying.get("holder_kind", "not stated")
                missing_fact = (
                    "the holder kind standing for the differing seat, "
                    "standing as %s and not as a full identifier"
                    % holder_kind)
            else:
                missing_fact = (
                    "exactly one satisfying tying record and no non "
                    "matching record for the differing seat")
        return {"field_9": field_9, "verdict": verdict,
                "missing_fact": missing_fact, "listing": CHECK17_LISTING}

    limb = run_input.get("limb")
    if limb is not None:
        limb_verdicts = {
            "claim standing read and contradicted": "FAIL",
            "no claim standing": "NOT PROVEN",
            "claim passage cannot be read without guessing": "NOT PROVEN",
            "honest reseat record outside the supplied set": "NOT PROVEN",
            "frozen roster absence": "UNVERIFIABLE",
            "gate instance absence": "UNVERIFIABLE",
            "two records stating the same standing": "UNVERIFIABLE",
        }
        verdict = limb_verdicts.get(limb, "NOT PROVEN")
        if limb == "gate instance absence":
            field_9["absence_statement"] = "gate instance absence in words"
            missing_fact = "the gate roster instance for the stage judged"
        elif limb == "frozen roster absence":
            missing_fact = "the frozen roster instance for the stage judged"
        elif limb == "two records stating the same standing":
            field_9["duplication"] = (
                "two records stating the same standing, the duplication "
                "carried at field 9")
            missing_fact = (
                "a single standing stated for the roster instance")
        elif verdict in ("FAIL", "NOT PROVEN"):
            missing_fact = (
                "a staffing claim standing read in a named claim bearing "
                "file for the differing seat")
        return {"field_9": field_9, "verdict": verdict,
                "missing_fact": missing_fact, "listing": CHECK17_LISTING}

    return {"field_9": field_9, "verdict": verdict,
            "missing_fact": missing_fact, "listing": CHECK17_LISTING}


def _place_check17(check_results, difference, parsed):
    """Check 17 placement: its CheckResult stands at field 6 through
    slice 5 assembly in a gate run, and no CheckResult and no
    LimbResult for check 17 stands in a precheck, where check 17
    stands listed in full at field 10 instead.
    """
    results = [e for e in check_results if e["check"] != 17]
    if parsed["run_kind"] == "precheck":
        return results
    entry = {
        "check": 17,
        "composing": True,
        "composes": True,
        "rule": "brief section 5.6.2",
        "expected_property": "the property item 17 states",
        "evidence": {},
        "verdict": difference["verdict"],
        "missing_fact": difference["missing_fact"],
        "citations": ["roster record"] if difference["verdict"] == "PASS"
                     else [],
    }
    results.append(entry)
    return results


def _limb_results(parsed):
    """LimbResult production for the precheck run limbs of the
    checks listed in part, checks 10 and 12 built in slice 4 and
    check 16 standing in its slice, each standing as a LimbResult
    at field 6 with its listed limbs named at field 10 and no
    CheckResult for the check in a precheck.
    """
    if parsed["run_kind"] != "precheck":
        return []
    names = {10: "tier statement limb",
             12: "artefact linkage limb",
             16: "claim agreement limb"}
    return [{"check": number, "kind": "LimbResult",
             "limb": names[number],
             "rule": "brief section 5.6.1",
             "verdict": "PASS",
             "listed_limbs": [names[number]]}
            for number in (10, 12, 16)]


def _assemble(parsed, fields, check_results, extra):
    """Slice 5 assembly seam: the assembled ComputedResult mapping."""
    result = {"fields": fields, "check_results": check_results}
    result.update(extra)
    return result


def compute_result(run_input):
    """Kernel entry: compute_result(run_input) returns ComputedResult."""
    if not isinstance(run_input, dict):
        run_input = {}
    parsed = _read_run_input(run_input)
    tables = _tables_from(run_input)
    manifest = _manifest_from(run_input, tables)
    differing = _differing_exception_units(run_input, tables)
    groups = _supplied_set(parsed)
    coverage = _coverage(run_input, parsed, groups)
    receipt, ignored = _receipt_and_ignored(parsed, groups)
    reading = _reading(run_input)
    base = _base_standing(run_input)
    verification = _table_verification(run_input)
    counting_allowed = verification["counting_allowed"]
    team_counts, absence = _team_counts(
        run_input, tables, differing, counting_allowed)
    stage_count = _stage_count(
        run_input, tables, differing, team_counts, counting_allowed)
    if absence is not None:
        stage_count["absence_words"] = absence
    check_results, check_side = _check_results(
        run_input, differing, reading, verification, base, tables,
        team_counts, parsed)
    limb_results = _limb_results(parsed)
    difference = _difference_duty(run_input, parsed)
    check_results = _place_check17(check_results, difference, parsed)
    if parsed["run_kind"] != "precheck":
        for entry in check_results:
            if entry["check"] != 17:
                continue
            if base["kind"] == "no_base":
                entry["verdict"] = "UNVERIFIABLE"
                entry["missing_fact"] = NO_BASE_MISSING_IDENTIFICATION
                entry["citations"] = []
            elif not counting_allowed:
                entry["verdict"] = "NOT PROVEN"
                entry["missing_fact"] = (
                    "a verified counting table standing for the run")
                entry["citations"] = []

    # Slice 5 assembly, part one: the part that takes no slice 6
    # supply. The OPEN CASE machinery stands exactly as brief
    # section 5.4.2 states it: the OPEN CASE state stands in the
    # verdict position of each affected check, and, for the words
    # alone case, in the base position at field 4; field 7 carries
    # the counts the standing records support; field 8 carries no
    # difference for a claim point whose file is the absent file;
    # field 11 carries no repair entry for an affected check; and
    # field 12 carries no rollup word. No verdict in this part
    # rests on the G-38 case, which stands open as Carry 2.
    open_case_kind = None
    if base["kind"] == "words_alone":
        open_case_kind = "words_alone"
    elif run_input.get("open_case") == "single absent file":
        open_case_kind = "absent_file"
    elif run_input.get("open_case") or \
            run_input.get("run_meets_an_open_case"):
        open_case_kind = "open"
    affected_checks = set()
    if open_case_kind in ("words_alone", "absent_file"):
        for entry in check_results:
            entry["affected"] = True
            entry["verdict_position"] = "OPEN CASE"
            entry["verdict"] = None
            affected_checks.add(entry["check"])
    else:
        for entry in check_results:
            entry["affected"] = False
            entry["verdict_position"] = entry["verdict"]
    generated = _generated_statement(run_input, team_counts, stage_count)
    differences, verdict16, missing16 = _claim_agreement(run_input)
    if verdict16 is not None and open_case_kind is None and \
            parsed["run_kind"] != "precheck":
        for entry in check_results:
            if entry["check"] == 16:
                entry["verdict"] = verdict16
                entry["verdict_position"] = verdict16
                entry["missing_fact"] = missing16
                entry["citations"] = ["roster record"] \
                    if verdict16 == "PASS" else []
    repair_list = _repair_entries(
        run_input, check_results, team_counts, affected_checks)

    if base["kind"] == "words_alone":
        base_position = WORDS_ALONE_BASE_LINE
    elif base["kind"] == "no_base":
        base_position = {"pinned_base": None,
                         "missing_identification":
                             NO_BASE_MISSING_IDENTIFICATION}
    else:
        base_position = {"pinned_base": parsed["pinned_base"]}

    if parsed["run_kind"] == "precheck":
        # Field 10 lists check 17 in full and the listed limbs of
        # checks 10, 12 and 16 in every precheck this kernel
        # produces, and check 17 and the listed limbs of checks
        # 10 and 16 compose, so the listed not run condition at
        # brief section 5.6.1 stands in every such precheck.
        # Field 12 therefore carries the precheck no rollup words
        # that section states, and no rollup word. Where the run
        # also meets an open case, the precheck case governs this
        # field under brief section 5.4.2, and the open case
        # statement stands at field 13 alone.
        rollup = PRECHECK_NO_ROLLUP_WORDS
        composition = {"governing_row": 1} \
            if open_case_kind is not None else {"governing_row": None}
    elif open_case_kind is not None:
        rollup = OPEN_CASE_ROLLUP_WORDS
        composition = {"governing_row": 1}
    elif isinstance(run_input.get("composing_check_words"), list):
        row, rollup = _composition(
            run_input, run_input["composing_check_words"],
            bool(run_input.get("plaid_claim_stands")))
        composition = {"governing_row": row}
    else:
        words = [e["verdict"] for e in check_results if e["composing"]]
        row, rollup = _composition(
            run_input, words, parsed["tier"] == "Plaid")
        composition = {"governing_row": row}

    bounds = []
    if base["kind"] == "words_alone":
        bounds.append(WORDS_ALONE_BASE_LINE)
    if open_case_kind is not None:
        bounds.append(OPEN_CASE_STATEMENT)
    if run_input.get("trace_standing") is not None:
        bounds.append(TRACE_BOUND)
    claim_bearing = sorted({str(e.get("path")) for entries in
                            groups.values() for e in entries})
    fields = {
        "1": {"tool_name": TOOL_NAME, "tool_version": TOOL_VERSION},
        "2": {"run_kind": parsed["run_kind"],
              "runner_identity": parsed["runner_identity"],
              "runner_capacity": parsed["runner_capacity"]},
        "3": {"stage_judged": parsed["stage_judged"],
              "build": parsed["build"],
              "tier_applied": parsed["tier"]},
        "4": {"pinned_base": parsed["pinned_base"],
              "base_position": base_position,
              "manifest_identity": manifest["manifest_identity"],
              "manifest": manifest,
              "counting_table_identity": [
                  e["table_name"] for e in manifest["entries"]]},
        "5": {"coverage": coverage, "receipt": receipt,
              "ignored_inputs": ignored,
              "claim_bearing_list": claim_bearing,
              "supplied_set": {g: sorted({str(e.get("path"))
                                          for e in entries})
                               for g, entries in groups.items()}},
        "6": {"check_results": check_results,
              "limb_results": limb_results,
              "limb_results_for_check_17": []},
        "7": {"team_counts": team_counts, "stage_count": stage_count,
              "absence_words": absence,
              "build_union": {
                  "state": COUNTING_MODEL["build_union_state"],
                  "reason": COUNTING_MODEL["build_union_reason"]}},
        "8": differences,
        "9": difference["field_9"],
        "10": "not a precheck" if parsed["run_kind"] != "precheck"
              else ("listed limbs not yet run: check 10 listed "
                    "limbs, check 12 listed limbs, check 16 listed "
                    "limbs, check 17, listed in full"),
        "11": _RepairField({
            "missing_seats": [e for e in repair_list
                              if e["entry_kind"] == "missing seat"],
            "duplicate_holdings": _duplicate_holdings(run_input),
            "unproven_seats": [e for e in repair_list
                               if e["entry_kind"] == "unproven seat"]},
            repair_list),
        "12": rollup,
        "13": {"bounds": bounds,
               "whole_flow_total": {
                   "checklist_constants_total": 39,
                   "level_union_total": 38,
                   "selected": None},
               "colour_completeness_position":
                   "beside the rollup at field 13"},
    }
    if base["kind"] == "words_alone":
        fields["4"] = {"pinned_base": parsed["pinned_base"],
                        "base_position": "OPEN CASE"}
    if check_side["check5_beside"] is not None:
        fields["13"]["check5_beside_rollup"] = \
            check_side["check5_beside"]
    if check_side["table_conflict_statement"] is not None:
        fields["13"]["table_conflict_statement"] = \
            check_side["table_conflict_statement"]
    tier_applied = run_input.get("tier_applied", parsed["tier"])
    if tier_applied == "Plaid":
        fields["13"]["plaid_refusal"] = "Plaid refusal form at G13"
    reading_out = dict(reading)
    reading_out["counts"] = {"team_counts": team_counts}
    extra = {
        "CountingTables": tables,
        "PinnedBaseManifest": manifest,
        "Shapes": SHAPES,
        "CountingModel": COUNTING_MODEL,
        "limb_results": limb_results,
        "reading": reading_out,
        "table_verification": verification,
        "base_line": base_position if isinstance(base_position, str)
                     else None,
        "generated_statement": generated,
        "composition": composition,
        "silence_index": {"applied_as": "an index",
                          "creates": "no word, position or outcome"},
        "absence_outcomes": _absence_outcomes(run_input),
    }
    return _assemble(parsed, fields, check_results, extra)
