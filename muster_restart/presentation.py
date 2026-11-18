# Copyright: J.P. Picard aka Macro-Harder.
"""Presentation module: one result in three forms, with the form
agreement comparison and the presentation run printing standing.

Seam, kept from the tracer miniature this build replaces: one
ComputedResult mapping in through the contract at brief section
5.4.2 alone, and the three generated forms out. This file carries
both build parts that stand in the presentation module: the
rendering of the three forms from the one result record, and the
form agreement comparison unit at brief section 5.7.9 together
with the run comparison path that calls it and the printing
standing for a run whose comparison found disagreements. The
comparison unit and the printing standing stand in this file,
below the rendering part.

Rules held here, from plan section 10 and brief sections 5.7.1 to
5.7.10, 5.6.1, 5.6.2 and 6: the Simple form, the Advanced form and
the Agentic form are built together in one rendering pass under
DP-17, each rendered from the one result record alone and no form
rendered from the text of another form. This module reads no record
file, computes no check in the set at brief section 5.5, counts
nothing and selects no verdict. Every value a form carries is a
value the record carries, copied and not recomputed, so no verdict,
count, coverage figure or rollup differs between forms. Rendering
is a pure function of the record: the same record renders to the
same forms, with no turn on run time, disk file order, or any state
outside the record.
"""

# Canonical element order for the Advanced form and the Agentic
# form, brief section 5.7.2 in its narrowed D8 form and plan
# section 10. The Simple form keeps its fixed template order at
# brief section 5.7.3 as the one stated exception.
CANONICAL_ELEMENTS = (
    "title",
    "standing grade sentence",
    "stage, tier and pinned base line",
    "rollup line",
    "precheck not yet run section",
    "build union state line",
    "counts lines",
    "runner identity and capacity line",
    "standing limits lines",
    "roster match element",
    "repair list content",
    "supplied set line with coverage statement and run receipt",
    "consequence line",
    "closing line",
)

# The Advanced form additions, closed at brief section 5.7.4, in
# their canonical sequence. The PASS rollup header stands among
# them only where the rollup the record carries is PASS.
ADVANCED_ADDITIONS = (
    "full repair list",
    "full bounds list",
    "per check detail",
    "PASS evidence citations",
    "PASS rollup header",
    "claim disagreement flags",
)

_VERDICT_WORDS = ("PASS", "FAIL", "NOT PROVEN", "UNVERIFIABLE")

# Fixed texts. Each text stands in plan section 10 or in brief
# section 5.7 as the fixed wording of its element, and carries no
# value of any run.
_TITLE = "Muster-lite staffing report"
_GRADE = "Standing grade: grade L2 records checker."
_LIMITS = (
    "Standing limits: this report checks the records named in it "
    "and proves nothing beyond them."
)
_CLOSING = (
    "What this tool did not prove: that any agent was actually "
    "spawned, or that any work was done independently."
)
_GATE_CONSEQUENCE = (
    "Consequence: the rollup may be cited as gate evidence for "
    "this stage only."
)
_PRECHECK_LABEL = "Precheck"
_PRECHECK_CONSEQUENCE = (
    "Consequence: a precheck is not a gate run and classifies "
    "no stage."
)
_NO_ROLLUP_LINE = (
    "Precheck. No rollup stands, because a composing check "
    "has not run."
)
_OPEN_CASE_ROLLUP_LINE = (
    "Rollup not stated. This run meets an open case, named here, "
    "and the single result for that case stands open."
)
_GLOSSES = {
    "NOT PROVEN": "the records supplied do not prove the check",
    "UNVERIFIABLE": (
        "the records needed for the check cannot be read or do "
        "not stand in the supplied set"
    ),
}
_LINKAGE_WORDS = "not applicable: linkage did not pass for this seat"
_WORDS_ONLY_HEADER = (
    "PASS rollup. No team count stands in this stage, and no "
    "smallest slack stands."
)
# The G-47 bound at brief section 5.7.10, stated in full, printed
# with the bounds in the Advanced form.
_G47_BOUND = (
    "the receipt settles nothing at register group G-47, the open "
    "item on editing of ordinary records after a claim. The "
    "receipt changes no verdict, proves nothing about when a file "
    "changed, proves nothing about who wrote a file, and imposes "
    "no hash or sequence requirement on any input contract. It is "
    "a record of what this run read, and of nothing else."
)
# No default receipt and no default ignored input stand in this
# module. A record that carries no receipt list renders no receipt
# entries in any form, and a record that carries no ignored inputs
# list renders none; what a form prints in those positions is
# exactly what the record carries, and nothing else.


def _field(result, number, *names):
    """Read one contract position from the result mapping.

    The contract form, plan section 5 shape 12 and the suite
    conftest, carries a fields mapping keyed by contract field
    number as text, a check_results list, and the remaining
    contract content under its shape names. A flat record carrying
    the same content under plain names is read through the same
    names. Nothing is derived here: the value found is returned
    as carried, or None where the record carries none.
    """
    fields = result.get("fields")
    if isinstance(fields, dict):
        value = fields.get(str(number))
        if isinstance(value, dict):
            for name in names:
                if name in value:
                    return value[name]
        elif value is not None:
            return value
    for name in names:
        if name and name in result:
            return result[name]
    return None


def _shown(value):
    return "not stated" if value is None else value


def _text(value, fallback):
    if isinstance(value, str) and value:
        return value
    return fallback


def _check_label(entry):
    check = entry.get("check")
    if isinstance(check, int):
        return "check %d" % check
    if isinstance(check, str) and check:
        return check if check.startswith("check") else (
            "check %s" % check)
    return "check"


def _check_verdict(entry):
    word = entry.get("verdict_position")
    if isinstance(word, str) and word:
        return word
    word = entry.get("verdict")
    return word if isinstance(word, str) and word else None


def _view(result):
    """The one record reading every form renders from.

    Each value is copied from the record: the run kind, the stage,
    tier and base standing, the rollup standing at contract field
    12, the per check results, the counts with their subtraction
    fields, the coverage figures, the receipt and ignored inputs,
    the roster difference result at field 9, the precheck section
    at field 10, the repair lists at field 11, the claim
    differences at field 8 and the standing bounds at field 13.
    No figure is computed and no word is selected: where a total
    stands in the Agentic values it is a figure the record itself
    carries for the counts element, and the coverage figures are
    the totals the record itself carries for the coverage element.
    Where the record carries a per group coverage standing and no
    totals, no total stands in the reading: the coverage positions
    carry no value, and the forms state that standing in words.
    """
    if not isinstance(result, dict):
        result = {}
    fields = result.get("fields")
    fields = fields if isinstance(fields, dict) else {}

    def field_dict(number):
        value = fields.get(str(number))
        return value if isinstance(value, dict) else {}

    run_kind = _field(result, 2, "run_kind")
    run_kind = run_kind if isinstance(run_kind, str) else ""
    stage = _field(result, 3, "stage_judged", "stage")
    tier = _field(result, 3, "tier_applied", "tier")
    base_dict = field_dict(4)
    base_position = base_dict.get("base_position")
    if base_position is None and "base_position" in result:
        base_position = result.get("base_position")
    pinned_base = _field(result, 4, "pinned_base")
    if base_position == "OPEN CASE":
        base_shown = "OPEN CASE"
    elif isinstance(pinned_base, str) and pinned_base:
        base_shown = pinned_base
    else:
        base_shown = "not stated"

    rollup_raw = _field(result, 12, "rollup")
    rollup_word = rollup_raw if rollup_raw in _VERDICT_WORDS else None

    checks = []
    raw_checks = result.get("check_results")
    if not isinstance(raw_checks, list):
        raw_checks = _field(result, 6, "check_results", "checks")
    if isinstance(raw_checks, list):
        for entry in raw_checks:
            if isinstance(entry, dict):
                checks.append(entry)

    open_case = bool(result.get("open_case"))
    if isinstance(rollup_raw, str) and (
            rollup_raw.startswith("Rollup not stated")):
        open_case = True
    if base_position == "OPEN CASE":
        open_case = True
    for entry in checks:
        if entry.get("verdict_position") == "OPEN CASE":
            open_case = True

    counts = []
    flat_counts = result.get("counts")
    if isinstance(flat_counts, dict):
        counts = [flat_counts]
    else:
        field7 = field_dict(7)
        team_counts = field7.get("team_counts")
        if isinstance(team_counts, list):
            counts = [c for c in team_counts if isinstance(c, dict)]
        elif isinstance(field7.get("counts"), dict):
            counts = [field7["counts"]]
        elif isinstance(field7.get("counts"), list):
            counts = [c for c in field7["counts"]
                      if isinstance(c, dict)]

    coverage = _field(result, 5, "coverage")
    coverage = coverage if isinstance(coverage, dict) else {}
    cov = {"records_needed": None, "records_supplied": None,
           "records_read": None}
    totals = None
    if "records_needed" in coverage:
        totals = coverage
    elif isinstance(coverage.get("totals"), dict):
        totals = coverage["totals"]
    elif isinstance(_field(result, 5, "coverage_totals"), dict):
        totals = _field(result, 5, "coverage_totals")
    if isinstance(totals, dict):
        for key, group_key in (("records_needed", "needed"),
                               ("records_supplied", "supplied"),
                               ("records_read", "read")):
            if key in totals:
                cov[key] = totals.get(key)
            elif group_key in totals:
                cov[key] = totals.get(group_key)

    receipt = []
    raw_receipt = _field(result, 5, "receipt")
    if isinstance(raw_receipt, list) and raw_receipt:
        for entry in raw_receipt:
            if isinstance(entry, dict):
                receipt.append({
                    "path": entry.get("path") or entry.get(
                        "file_path"),
                    "name": entry.get("name") or entry.get(
                        "file_name"),
                    "hash": entry.get("hash"),
                    "hash_form": entry.get("hash_form"),
                    "byte_size": entry.get("byte_size"),
                })
            elif isinstance(entry, str):
                receipt.append({"path": entry, "name": entry,
                                "hash": None, "hash_form": None,
                                "byte_size": None})

    ignored = []
    raw_ignored = _field(result, 5, "ignored_inputs", "ignored")
    if isinstance(raw_ignored, list):
        for entry in raw_ignored:
            if isinstance(entry, dict):
                name = entry.get("path") or entry.get("name")
            else:
                name = entry
            if name:
                ignored.append(name)

    if "9" in fields:
        field9 = fields.get("9")
    else:
        field9 = _field(result, 9, "roster_match")
    differing = []
    if isinstance(field9, dict):
        raw_diff = field9.get("differing_seats")
        if raw_diff is None:
            raw_diff = field9.get("difference_list")
        if isinstance(raw_diff, list):
            differing = [d for d in raw_diff if isinstance(d, dict)]

    field10 = _field(result, 10, "precheck_not_yet_run_section")
    # Contract field 11 stands as a grouped mapping, brief section
    # 5.4.2 field 11: the missing seats list, the duplicate
    # holdings list and the unproven seats list, each entry a
    # RepairEntry at shape 15. The reading takes the grouped
    # mapping itself from the fields mapping, key by key, because
    # _field returns a single named value and field 11 carries
    # three lists under its own keys and no shape name. A field 11
    # standing as one flat RepairEntry list is read by entry kind
    # into the same three lists, and a flat record carrying a list
    # under a plain list name fills only a list the contract form
    # leaves empty.
    raw11 = fields.get("11")
    if raw11 is None:
        raw11 = result.get("repair_lists")
    grouped11 = raw11 if isinstance(raw11, dict) else {}
    repair = {
        "missing_seats": grouped11.get("missing_seats"),
        "duplicate_holdings": grouped11.get("duplicate_holdings"),
        "unproven_seats": grouped11.get("unproven_seats"),
    }
    if isinstance(raw11, list):
        kind_keys = {
            "missing seat": "missing_seats",
            "duplicate holding": "duplicate_holdings",
            "unproven seat": "unproven_seats",
        }
        for entry in raw11:
            if not isinstance(entry, dict):
                continue
            key = kind_keys.get(entry.get("entry_kind"))
            if key is None:
                continue
            if not isinstance(repair[key], list):
                repair[key] = []
            repair[key].append(entry)
    for key, value in repair.items():
        repair[key] = [e for e in value if isinstance(e, dict)] \
            if isinstance(value, list) else []
    for key in repair:
        if repair[key]:
            continue
        flat_list = result.get(key)
        if isinstance(flat_list, list):
            repair[key] = [
                e for e in flat_list if isinstance(e, dict)]

    differences = _field(result, 8, "claim_differences")
    if differences is None:
        generated = field_dict(8)
        differences = generated.get("differences")
    differences = [d for d in differences if isinstance(d, dict)] \
        if isinstance(differences, list) else []

    field13 = _field(result, 13, "bounds")
    bounds = []
    if isinstance(field13, list):
        bounds = [b for b in field13 if isinstance(b, str)]
    elif isinstance(field13, dict):
        raw_bounds = field13.get("bounds")
        if isinstance(raw_bounds, list):
            bounds = [b for b in raw_bounds if isinstance(b, str)]

    union = _field(result, 7, "build_union_state")
    if not isinstance(union, str):
        field7 = field_dict(7)
        union_dict = field7.get("build_union")
        if isinstance(union_dict, dict):
            state = union_dict.get("state")
            reason = union_dict.get("reason")
            if isinstance(state, str) and state:
                union = state
                if isinstance(reason, str) and reason:
                    union = "%s, because %s" % (state, reason)
        if not isinstance(union, str):
            union = None

    listed = bool(result.get("listed_not_run_condition"))
    if run_kind == "precheck":
        if rollup_raw is None:
            listed = True
        if isinstance(field10, str) and "listed" in field10:
            listed = True

    primary = counts[0] if counts else {}
    first_verdict = _check_verdict(checks[0]) if checks else None
    return {
        "record": result,
        "run_kind": run_kind,
        "is_precheck": run_kind == "precheck",
        "stage": stage,
        "tier": tier,
        "base_shown": base_shown,
        "base_position": base_position,
        "rollup_raw": rollup_raw,
        "rollup_word": rollup_word,
        "open_case": open_case,
        "listed_not_run": listed,
        "checks": checks,
        "first_verdict": first_verdict,
        "counts": counts,
        "primary_count": primary,
        "coverage": cov,
        "receipt": receipt,
        "ignored": ignored,
        "field9": field9,
        "differing": differing,
        "field10": field10,
        "repair": repair,
        "differences": differences,
        "bounds": bounds,
        "union": union,
        "runner": _field(result, 2, "runner_identity"),
        "capacity": _field(result, 2, "runner_capacity"),
    }


def _rollup_line(view, gloss):
    """The rollup line, brief sections 5.4.2, 5.6.1 and 5.7.6.

    Where the listed not run condition stands, no rollup word
    prints and the line carries the precheck no rollup statement.
    In an open case run that is not a precheck, the line carries
    the open case statement and no rollup word. In a precheck the
    line never states a bare verdict: the label stands beside the
    word the record carries. In the Simple form the verdict word
    glosses at G25 print beside NOT PROVEN and beside UNVERIFIABLE
    where either stands as a rollup, and beside no other word.
    """
    if view["listed_not_run"]:
        return _NO_ROLLUP_LINE
    if view["open_case"] and not view["is_precheck"]:
        return _OPEN_CASE_ROLLUP_LINE
    word = view["rollup_word"]
    if word is None:
        raw = view["rollup_raw"]
        if isinstance(raw, str) and raw:
            return raw
        return "Rollup: not stated"
    if view["is_precheck"]:
        return "Rollup: %s (%s)" % (word, _PRECHECK_LABEL)
    line = "Rollup: %s" % word
    if gloss and word in _GLOSSES:
        line = "%s (%s)" % (line, _GLOSSES[word])
    return line


def _counts_line(count):
    return (
        "%s: %s counted, from %s entries counted, %s duplicates "
        "removed, %s exempt or uncounted seats removed, against "
        "%s required. Slack: %s." % (
            _text(count.get("team"), "Team"),
            _shown(count.get("counted_total")),
            _shown(count.get("entries_counted")),
            _shown(count.get("duplicates_removed")),
            _shown(count.get("exempt_or_uncounted_removed")),
            _shown(count.get("required_count")),
            _shown(count.get("slack")),
        )
    )


def _check17_verdict(view):
    for entry in view["checks"]:
        if _check_label(entry) == "check 17":
            return _check_verdict(entry)
    return None


def _carried_by_kind(field9):
    """The differing seat counts by kind the record itself carries.

    Contract field 9 carries no per kind count in its difference
    list form, so this reading copies a by kind count only where
    field 9 carries one under a by kind key, as a mapping or as a
    list of kind and count entries. Where field 9 carries none,
    no count stands here and the roster line states that standing
    in words; no seat in the difference list is counted here.
    """
    if not isinstance(field9, dict):
        return None
    for key in ("differing_by_kind", "differing_seats_by_kind",
                "counts_by_kind", "by_kind"):
        carried = field9.get(key)
        if isinstance(carried, dict) and carried:
            return ", ".join(
                "%s: %s" % (kind, _shown(carried[kind]))
                for kind in carried)
        if isinstance(carried, list) and carried:
            parts = []
            for entry in carried:
                if isinstance(entry, dict) \
                        and entry.get("kind") is not None:
                    parts.append("%s: %s" % (
                        entry["kind"], _shown(entry.get("count"))))
            if parts:
                return ", ".join(parts)
    return None


def _roster_match_line(view):
    """The roster match element in its Simple rendering.

    One line in the standing limits position, brief section 5.6.2
    as rendered at plan section 10 slot ten: the standing contract
    field 9 carries, and the differing seats by kind as that field
    carries them. A match claim with the plain figure zero stands
    only where field 9 carries a gate run comparison standing that
    is a match: a difference list standing present and empty, with
    no absence statement, no duplication statement and no
    UNVERIFIABLE standing for check 17 in the record. Where field
    9 carries an absence, a duplication, an UNVERIFIABLE standing
    or the not a gate run value, the line states that standing and
    claims no match, and no differing seat count stands. Where the
    rosters differ, the by kind position carries the counts field
    9 itself carries, or states in words that no count by kind
    stands in the record. Where no field 9 standing stands in the
    record at all, the line states that standing in words. No
    verdict for the stage stands in this line.
    """
    field9 = view["field9"]
    if isinstance(field9, str) and field9:
        return (
            "Roster match: %s. Differing seats by kind: not stated."
            % field9)
    if isinstance(field9, dict):
        for key in ("absence_statement", "duplication"):
            statement = field9.get(key)
            if isinstance(statement, str) and statement:
                return (
                    "Roster match: %s. Differing seats by kind: "
                    "not stated." % statement)
        if _check17_verdict(view) == "UNVERIFIABLE":
            return (
                "Roster match: the roster comparison stands "
                "UNVERIFIABLE. Differing seats by kind: not stated.")
        if view["differing"]:
            by_kind = _carried_by_kind(field9)
            return (
                "Roster match: the rosters differ. Differing seats "
                "by kind: %s." % (
                    by_kind if by_kind else
                    "no count by kind stands in the record"))
        if "differing_seats" in field9 \
                or "difference_list" in field9:
            return (
                "Roster match: the rosters match. Differing seats "
                "by kind: 0.")
    return (
        "Roster match: no roster comparison standing stands in "
        "the record. Differing seats by kind: not stated.")


def _seat_label(entry):
    for key in ("seat", "seat_key", "evidence_seat"):
        value = entry.get(key)
        if value:
            return str(value)
    evidence = entry.get("evidence")
    if isinstance(evidence, dict) and evidence.get("seat"):
        return str(evidence["seat"])
    team = entry.get("team")
    return str(team) if team else "a seat"


def _repair_short(view):
    repair = view["repair"]
    missing = repair["missing_seats"]
    duplicates = repair["duplicate_holdings"]
    missing_text = "none" if not missing else ", ".join(
        _seat_label(e) for e in missing)
    duplicate_text = "none" if not duplicates else ", ".join(
        _seat_label(e) for e in duplicates)
    return missing_text, duplicate_text


def _precheck_section_text(view):
    field10 = view["field10"]
    if isinstance(field10, str) and field10:
        return field10
    if isinstance(field10, dict):
        text = field10.get("section")
        if isinstance(text, str) and text:
            return text
    return (
        "Precheck. The checks listed as not yet run stand named "
        "in the result record, each with the input it waits for."
    )


def _receipt_names(view):
    names = []
    for entry in view["receipt"]:
        name = entry.get("name") or entry.get("path")
        if name:
            names.append(str(name))
    return names


def _receipt_detail(view):
    parts = []
    for entry in view["receipt"]:
        name = entry.get("name") or entry.get("path")
        if not name:
            continue
        detail = str(name)
        if entry.get("hash"):
            detail = "%s (hash %s, byte size %s)" % (
                detail, entry["hash"], _shown(entry.get("byte_size")))
        elif entry.get("hash_form"):
            detail = "%s (hash form %s, byte size %s)" % (
                detail, entry["hash_form"],
                _shown(entry.get("byte_size")))
        parts.append(detail)
    if not parts:
        return "no receipt entry stands in the record"
    return ", ".join(parts)


def _receipt_names_text(view):
    names = _receipt_names(view)
    if not names:
        return "no receipt entry stands in the record"
    return ", ".join(names)


def _shared_contents(view):
    """Content of the shared elements, keyed by canonical name.

    Each content is built from the record reading alone. The
    Simple form and the Advanced form each take their contents
    from this reading in their own order statement; neither form
    reads the other form text, and the Agentic form takes its
    values from the same reading.
    """
    precheck = view["is_precheck"]
    title = _TITLE
    if precheck:
        title = "%s: %s" % (_PRECHECK_LABEL, _TITLE)
    missing_text, duplicate_text = _repair_short(view)
    contents = {
        "title": title,
        "standing grade sentence": _GRADE,
        "stage, tier and pinned base line": (
            "Stage: %s. Tier applied: %s. Pinned base: %s." % (
                _text(view["stage"], "not stated"),
                _text(view["tier"], "not stated"),
                view["base_shown"],
            )
        ),
        "build union state line": "Build union: %s." % _text(
            view["union"], "not stated"),
        "counts lines": "; ".join(
            _counts_line(c) for c in view["counts"]
        ) if view["counts"] else "no team count stands in this result",
        "runner identity and capacity line": (
            "Runner: %s. Capacity: %s." % (
                _text(view["runner"], "not stated"),
                _text(view["capacity"], "not stated"),
            )
        ),
        "standing limits lines": _LIMITS,
        "roster match element": _roster_match_line(view),
        "repair list content": (
            "Missing seats: %s. Duplicate seats: %s." % (
                missing_text, duplicate_text)
        ),
        "supplied set line with coverage statement and run receipt": (
            "Supplied set: %s records needed, %s supplied, %s "
            "read. Receipt: %s." % (
                _shown(view["coverage"].get("records_needed")),
                _shown(view["coverage"].get("records_supplied")),
                _shown(view["coverage"].get("records_read")),
                _receipt_names_text(view),
            )
        ),
        "consequence line": (
            _PRECHECK_CONSEQUENCE if precheck else _GATE_CONSEQUENCE
        ),
        "closing line": _CLOSING,
    }
    if precheck:
        contents["precheck not yet run section"] = (
            "precheck not yet run section: %s"
            % _precheck_section_text(view)
        )
    return contents


def _render_simple(view):
    """The Simple form, in its fixed template order.

    Slot order follows plan section 10 and brief section 5.7.3:
    title, standing grade sentence, stage tier and pinned base
    line, rollup line, the precheck not yet run section in a
    precheck run only, build union state line, counts lines,
    runner line, standing limits lines, the roster match line in
    the standing limits position, the missing and duplicate seats
    in short form, the supplied set line with its coverage
    statement and the run receipt beside it, the consequence line
    and the closing line. No element of the form specific set at
    brief section 5.7.2 stands in this form.
    """
    contents = _shared_contents(view)
    lines = [
        contents["title"],
        contents["standing grade sentence"],
        contents["stage, tier and pinned base line"],
        _rollup_line(view, gloss=True),
    ]
    if view["is_precheck"]:
        lines.append(contents["precheck not yet run section"])
    lines.extend([
        contents["build union state line"],
        contents["counts lines"],
        contents["runner identity and capacity line"],
        contents["standing limits lines"],
        contents["roster match element"],
        contents["repair list content"],
        contents[
            "supplied set line with coverage statement and run receipt"],
        contents["consequence line"],
        contents["closing line"],
    ])
    return "\n".join(lines)


def _repair_rows(view):
    rows = []
    repair = view["repair"]
    entries = []
    for key in ("missing_seats", "duplicate_holdings",
                "unproven_seats"):
        entries.extend(repair[key])
    for entry in entries:
        evidence = entry.get("evidence")
        if isinstance(evidence, dict):
            evidence_text = "%s, seat %s" % (
                _text(evidence.get("file"), "not stated"),
                _shown(evidence.get("seat")))
        else:
            evidence_text = _text(
                entry.get("evidence_file_and_seat"), "not stated")
        rows.append(
            "%s: check %s, rule %s, evidence %s, cure act %s" % (
                _text(entry.get("entry_kind"), "repair entry"),
                _shown(entry.get("check")),
                _text(entry.get("rule"), "not stated"),
                evidence_text,
                _text(entry.get("cure_act"), "not stated"),
            )
        )
    return rows


def _check_detail(view):
    parts = []
    for entry in view["checks"]:
        detail = "%s: verdict %s" % (
            _check_label(entry), _shown(_check_verdict(entry)))
        if entry.get("team"):
            detail = "%s, team %s" % (detail, entry["team"])
        if entry.get("rule"):
            detail = "%s, rule %s" % (detail, entry["rule"])
        if entry.get("missing_fact"):
            detail = "%s, missing fact %s" % (
                detail, entry["missing_fact"])
        locations = []
        if entry.get("roster_line_location"):
            locations.append(str(entry["roster_line_location"]))
        if entry.get("author_record_line_location"):
            locations.append(str(entry["author_record_line_location"]))
        if locations:
            detail = "%s, citations %s" % (
                detail, " and ".join(locations))
        parts.append(detail)
    return "; ".join(parts) if parts else "none in this result"


def _pass_citations(view):
    """PASS evidence citations, brief section 5.7.7.

    Each PASS check cites the roster line location it rests on
    and, where linkage passed for that seat, the artefact author
    record line location. Where linkage did not pass or did not
    apply, the second location stands in words, so no citation
    reads as artefact proof it does not hold.
    """
    parts = []
    for entry in view["checks"]:
        if _check_verdict(entry) != "PASS":
            continue
        first = entry.get("roster_line_location")
        if not first and isinstance(entry.get("citations"), list) \
                and entry["citations"]:
            first = entry["citations"][0]
        if not first:
            continue
        second = entry.get("author_record_line_location")
        if not second:
            second = _LINKAGE_WORDS
        parts.append("%s: %s and %s" % (
            _check_label(entry), first, second))
    return "; ".join(parts) if parts else "none in this result"


def _pass_rollup_header(view):
    """The PASS rollup header, brief section 5.7.8, Advanced only.

    A figured header naming the smallest slack value in the stage
    and each team at that value, using only slack figures the
    report already prints, where a slack figure stands for at
    least one TeamCount; the words only header, using no figure
    and naming no team, where no TeamCount stands. No header
    stands where the rollup is not PASS, and no header stands
    where a TeamCount stands in the result but no TeamCount
    carries a slack figure: brief section 5.7.8 states no header
    form for that case, and the words only text would state that
    no team count stands in a form that carries one.
    """
    if view["rollup_word"] != "PASS":
        return None
    figured = [c for c in view["counts"]
               if isinstance(c.get("slack"), int)]
    if not figured:
        if view["counts"]:
            return None
        return _WORDS_ONLY_HEADER
    smallest = min(c["slack"] for c in figured)
    teams = [str(c.get("team")) for c in figured
             if c["slack"] == smallest]
    return "PASS rollup header: smallest slack %s (%s)" % (
        smallest, ", ".join(teams))


def _claim_flags(view):
    if not view["differences"]:
        return "none in this result"
    parts = []
    verdict16 = None
    for entry in view["checks"]:
        if _check_label(entry) == "check 16":
            verdict16 = _check_verdict(entry)
    for difference in view["differences"]:
        claim = difference.get("claim_point") or difference.get(
            "claim") or difference.get("claim_text")
        generated = difference.get("generated_point")
        parts.append(
            "claim %s, generated statement point %s, computed "
            "verdict %s" % (
                _shown(claim), _shown(generated),
                _shown(verdict16)))
    return "; ".join(parts)


def _advanced_additions_carried(view):
    carried = ["full repair list", "full bounds list",
               "per check detail", "PASS evidence citations"]
    if _pass_rollup_header(view) is not None:
        carried.append("PASS rollup header")
    carried.append("claim disagreement flags")
    return carried


def advanced_form_additions(result_record):
    """The Advanced form additions the record carries, in order.

    The additions closed at brief section 5.7.4 in their canonical
    sequence, for the result record given. The PASS rollup header
    stands in the list only where the rollup the record carries
    is PASS, as brief section 5.7.8 states.
    """
    return _advanced_additions_carried(_view(result_record))


def _render_advanced(view):
    """The Advanced form, in canonical order and canonical naming.

    The shared elements stand in substance, in canonical order,
    each headed by its canonical name, taken from the same record
    reading as the other forms and not from any form text. After
    them the additions closed at brief section 5.7.4 stand in
    their canonical sequence: the full repair list as one fixed
    table in contract field 11 order, the full bounds list, per
    check detail in contract field 6 order, PASS evidence
    citations in their two location form, the PASS rollup header
    in its figured or words only form where the rollup is PASS,
    and claim disagreement flags in contract field 8 order with
    claim and computed verdict side by side. The roster match
    element stands in this form as the gate report element for
    the frozen roster, with the full difference list in contract
    field 9 order. The precheck section content stands as the
    shared precheck element carries it, in a precheck run, and as
    the field 10 standing in a gate run.
    """
    contents = _shared_contents(view)
    contents["rollup line"] = _rollup_line(view, gloss=False)
    if not view["is_precheck"]:
        field10 = view["field10"]
        contents["precheck not yet run section"] = (
            field10 if isinstance(field10, str) and field10
            else "not a precheck"
        )
    else:
        contents["precheck not yet run section"] = (
            _precheck_section_text(view))
    limits = contents["standing limits lines"]
    if view["bounds"]:
        limits = "%s Bounds carried: %s." % (
            limits, "; ".join(view["bounds"]))
    contents["standing limits lines"] = limits
    roster = contents["roster match element"]
    if view["differing"]:
        detail = "; ".join(
            "%s %s" % (
                _text(seat.get("kind"), "differing seat"),
                _shown(seat.get("seat_key") or seat.get("seat")))
            for seat in view["differing"])
        roster = "%s Difference list: %s." % (roster, detail)
    contents["roster match element"] = roster
    supplied = (
        "Supplied set: %s records needed, %s supplied, %s read. "
        "Receipt: %s." % (
            _shown(view["coverage"].get("records_needed")),
            _shown(view["coverage"].get("records_supplied")),
            _shown(view["coverage"].get("records_read")),
            _receipt_detail(view),
        )
    )
    contents[
        "supplied set line with coverage statement and run receipt"
    ] = supplied

    lines = []
    for name in CANONICAL_ELEMENTS:
        lines.append("%s: %s" % (name, contents[name]))

    rows = _repair_rows(view)
    lines.append("full repair list: %s" % (
        "; ".join(rows) if rows else "none in this result"))
    bounds_parts = [_GRADE]
    bounds_parts.extend(view["bounds"])
    bounds_parts.append("G-47 bound: %s" % _G47_BOUND)
    lines.append("full bounds list: %s" % "; ".join(bounds_parts))
    lines.append("per check detail: %s" % _check_detail(view))
    lines.append("PASS evidence citations: %s" % _pass_citations(view))
    header = _pass_rollup_header(view)
    if header is not None:
        lines.append(header)
    lines.append("claim disagreement flags: %s" % _claim_flags(view))
    return "\n".join(lines)


def _element_values(view):
    """The shared values every Agentic element carries, as data.

    Each value is copied from the record reading: the verdict of
    the first check the record carries, the rollup word, the
    counts figures with their subtraction fields from the first
    TeamCount the record carries, and the coverage figures. No
    figure is computed and no word is selected.
    """
    count = view["primary_count"]
    coverage = view["coverage"]
    effective_rollup = None if view["listed_not_run"] \
        else view["rollup_word"]
    return {
        "verdict": view["first_verdict"] or effective_rollup,
        "rollup": effective_rollup,
        "counted_total": count.get("counted_total"),
        "entries_counted": count.get("entries_counted"),
        "duplicates_removed": count.get("duplicates_removed"),
        "exempt_or_uncounted_removed": count.get(
            "exempt_or_uncounted_removed"),
        "required_count": count.get("required_count"),
        "slack": count.get("slack"),
        "records_needed": coverage.get("records_needed"),
        "records_supplied": coverage.get("records_supplied"),
        "records_read": coverage.get("records_read"),
    }


def _field_12_text(view):
    if view["listed_not_run"]:
        return _NO_ROLLUP_LINE
    if view["open_case"] and not view["is_precheck"]:
        return _OPEN_CASE_ROLLUP_LINE
    raw = view["rollup_raw"]
    if isinstance(raw, str) and raw:
        return raw
    return "not stated"


def _open_case_positions(view):
    if not view["open_case"]:
        return []
    positions = []
    for entry in view["checks"]:
        if entry.get("verdict_position") == "OPEN CASE":
            positions.append("verdict position of an affected check")
            break
    if not positions and view["checks"]:
        positions.append("verdict position of an affected check")
    if view["base_position"] == "OPEN CASE":
        positions.append(
            "base position at contract field 4, words alone case only")
    return positions


def _agentic_citations(view):
    """The Agentic PASS evidence citations, as fields.

    Built by the one reading the Agentic form renders from and
    the comparison reads from, so both sides state the same
    citations for the same record.
    """
    citations = []
    for entry in view["checks"]:
        if _check_verdict(entry) != "PASS":
            continue
        first = entry.get("roster_line_location")
        if not first and isinstance(entry.get("citations"), list) \
                and entry["citations"]:
            first = entry["citations"][0]
        if not first:
            continue
        second = entry.get("author_record_line_location")
        if not second:
            second = _LINKAGE_WORDS
        citations.append({
            "check": _check_label(entry),
            "roster_line_location": first,
            "author_record_line_location": second,
        })
    return citations


def _agentic_per_check(view):
    """The Agentic per check results, as fields, from the reading."""
    per_check = []
    for entry in view["checks"]:
        per_check.append({
            "check": _check_label(entry),
            "verdict": _check_verdict(entry),
            "team": entry.get("team"),
            "rule": entry.get("rule"),
            "missing_fact": entry.get("missing_fact"),
            "roster_line_location": entry.get(
                "roster_line_location"),
            "author_record_line_location": entry.get(
                "author_record_line_location"),
        })
    return per_check


def _render_agentic(view):
    """The Agentic form, as a structured field mapping.

    The shared elements stand as named fields in canonical order,
    each carrying the shared values as data, so no consumer parses
    prose for a verdict, a count, a coverage figure or a rollup.
    Its additions, closed at brief section 5.7.5, stand as fields
    of the one result: PASS evidence citations as fields, the
    roster difference result as a field, and the per check results
    as fields, which field rendering is not the Advanced form per
    check detail element. The run kind stands as a required field
    of the form, carrying precheck in a precheck run, as brief
    section 5.7.6 requires. The receipt and the ignored inputs
    stand as fields of the shared supplied set element. Claim
    differences stand as the field 8 fields of the record, not as
    the Advanced form flags element.
    """
    values = _element_values(view)
    elements = []
    for name in CANONICAL_ELEMENTS:
        entry = {"name": name}
        entry.update(values)
        elements.append(entry)
    citations = _agentic_citations(view)
    per_check = _agentic_per_check(view)
    return {
        "run_kind": view["run_kind"] or "gate run",
        "rollup": values["rollup"],
        "elements": elements,
        "PASS evidence citations": citations,
        "roster_difference": view["field9"],
        "per_check_results": per_check,
        "claim_differences": view["differences"],
        "receipt": view["receipt"],
        "ignored_inputs": view["ignored"],
        "field_12": _field_12_text(view),
        "open_case_positions": _open_case_positions(view),
    }


def render_forms(result_record):
    """Render the three generated forms from one result record.

    One rendering pass, DP-17: the Simple form, the Advanced form
    and the Agentic form are built together here, each from the
    record alone and none from the text of another, and all three
    are returned generated and not yet printed. A caller that
    needs one form takes that one generated form from the mapping.
    The input is the ComputedResult mapping through the contract
    alone and no other input stands.
    """
    view = _view(result_record)
    return {
        "Simple": _render_simple(view),
        "Advanced": _render_advanced(view),
        "Agentic": _render_agentic(view),
    }


# Slice 8: form agreement comparison, defect report, and the
# presentation run printing standing. Brief sections 5.1, 5.4
# shape 16 and 5.7.9, plan section 8 slice 8 and plan section 10.
# The comparison unit below takes exactly two inputs, a result
# record and one generated form, and returns exactly one output,
# a DefectReport mapping or None. It compares the generated form
# against the result record element by element, deriving the
# record side values from the record reading, element by element.
# The kernel module takes no part in the comparison.

_TOOL_DEFECT_STATEMENT = (
    "This disagreement is a defect in the tool and not a finding "
    "about the stage records."
)
_TOOL_REPAIR_ACT = "a tool repair, not a restaffing act"
_FORM_AGREEMENT_CHECK = "form agreement check"
_FORM_AGREEMENT_RULE = (
    "G23: every form is a reading of the one computed result"
)
_NUMBER_WORDS = (
    "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "thirteen",
    "fourteen",
)
# Contract field carrying each canonical element, for the record
# side location form. The counts lines and the build union state
# line both stand at contract field 7.
_ELEMENT_CONTRACT_FIELD = {
    "title": 1,
    "standing grade sentence": 13,
    "stage, tier and pinned base line": 3,
    "rollup line": 12,
    "precheck not yet run section": 10,
    "build union state line": 7,
    "counts lines": 7,
    "runner identity and capacity line": 2,
    "standing limits lines": 13,
    "roster match element": 9,
    "repair list content": 11,
    "supplied set line with coverage statement and run receipt": 5,
    "consequence line": 12,
    "closing line": 13,
    "full repair list": 11,
    "full bounds list": 13,
    "per check detail": 6,
    "PASS evidence citations": 6,
    "PASS rollup header": 12,
    "claim disagreement flags": 8,
    "per check results": 6,
    "roster difference result": 9,
    "claim differences": 8,
    "receipt": 5,
    "ignored inputs": 5,
    "field 12": 12,
    "run kind": 2,
    "open case positions": 12,
}


def _number_word(index):
    if 1 <= index <= len(_NUMBER_WORDS):
        return _NUMBER_WORDS[index - 1]
    return str(index)


def _counts_segment(count):
    return (
        "%s counted, from %s entries counted, %s duplicates "
        "removed, %s exempt or uncounted seats removed, against "
        "%s required. Slack: %s." % (
            _shown(count.get("counted_total")),
            _shown(count.get("entries_counted")),
            _shown(count.get("duplicates_removed")),
            _shown(count.get("exempt_or_uncounted_removed")),
            _shown(count.get("required_count")),
            _shown(count.get("slack")),
        )
    )


def _counts_record_value(view):
    if not view["counts"]:
        return "no team count stands in this result"
    return "; ".join(_counts_segment(c) for c in view["counts"])


def _strip_counts_prefix(text):
    if text == "no team count stands in this result":
        return text
    parts = []
    for chunk in text.split("; "):
        if ": " in chunk and " counted, from " in chunk:
            chunk = chunk.split(": ", 1)[1]
        parts.append(chunk)
    return "; ".join(parts)


def _advanced_limits(view, contents):
    limits = contents["standing limits lines"]
    if view["bounds"]:
        limits = "%s Bounds carried: %s." % (
            limits, "; ".join(view["bounds"]))
    return limits


def _advanced_roster(view, contents):
    roster = contents["roster match element"]
    if view["differing"]:
        detail = "; ".join(
            "%s %s" % (
                _text(seat.get("kind"), "differing seat"),
                _shown(seat.get("seat_key") or seat.get("seat")))
            for seat in view["differing"])
        roster = "%s Difference list: %s." % (roster, detail)
    return roster


def _advanced_supplied(view):
    return (
        "Supplied set: %s records needed, %s supplied, %s read. "
        "Receipt: %s." % (
            _shown(view["coverage"].get("records_needed")),
            _shown(view["coverage"].get("records_supplied")),
            _shown(view["coverage"].get("records_read")),
            _receipt_detail(view),
        )
    )


def _record_value(element, view, form_kind):
    contents = _shared_contents(view)
    if element == "counts lines":
        return _counts_record_value(view)
    if element == "rollup line":
        return _rollup_line(view, gloss=(form_kind == "Simple"))
    if element == "precheck not yet run section":
        if form_kind == "Advanced":
            if not view["is_precheck"]:
                field10 = view["field10"]
                return field10 if isinstance(field10, str) \
                    and field10 else "not a precheck"
            return _precheck_section_text(view)
        return contents.get(element)
    if element == "standing limits lines" \
            and form_kind == "Advanced":
        return _advanced_limits(view, contents)
    if element == "roster match element" \
            and form_kind == "Advanced":
        return _advanced_roster(view, contents)
    if element == (
            "supplied set line with coverage statement and run "
            "receipt") and form_kind == "Advanced":
        return _advanced_supplied(view)
    return contents.get(element)


def _defect_report(element, form_kind, record_value, form_value):
    position = CANONICAL_ELEMENTS.index(element) + 1 \
        if element in CANONICAL_ELEMENTS else 1
    field_number = _ELEMENT_CONTRACT_FIELD.get(element, 7)
    if element in ADVANCED_ADDITIONS:
        addition_position = ADVANCED_ADDITIONS.index(element) + 1
        form_location = "%s, Advanced form addition %s" % (
            element, _number_word(addition_position))
    elif form_kind == "Simple":
        form_location = "%s, Simple form slot %s" % (
            element, _number_word(position))
    elif form_kind == "Advanced":
        form_location = "%s, Advanced form element %s" % (
            element, _number_word(position))
    elif form_kind == "Agentic":
        form_location = "%s, Agentic form element %s" % (
            element, _number_word(position))
    else:
        form_location = "%s, %s form slot %s" % (
            element, form_kind, _number_word(position))
    return {
        "check_name": _FORM_AGREEMENT_CHECK,
        "form_agreement_check_name": _FORM_AGREEMENT_CHECK,
        "rule": _FORM_AGREEMENT_RULE,
        "element": element,
        "value_in_result_record": record_value,
        "value_in_generated_form": form_value,
        "location_in_result_record": (
            "%s, contract field %s" % (element, field_number)),
        "location_in_generated_form": form_location,
        "defect_field": "UNVERIFIABLE",
        "tool_defect_statement": _TOOL_DEFECT_STATEMENT,
        "repair_act": _TOOL_REPAIR_ACT,
    }


def _simple_lines_by_element(view, generated_form):
    lines = generated_form.splitlines()
    mapping = {}
    index = 0
    for element in CANONICAL_ELEMENTS:
        if element == "precheck not yet run section" \
                and not view["is_precheck"]:
            continue
        if index < len(lines):
            mapping[element] = lines[index]
        index += 1
    return mapping


def _advanced_lines_by_element(generated_form):
    mapping = {}
    for line in generated_form.splitlines():
        for element in CANONICAL_ELEMENTS:
            prefix = "%s: " % element
            if line.startswith(prefix) \
                    and element not in mapping:
                mapping[element] = line[len(prefix):]
                break
    return mapping


def _addition_record_value(element, view):
    """The record side value of one Advanced form addition.

    Each value is built by the same rendering reading that builds
    the Advanced form itself, from the record alone: the full
    repair list from the repair rows, the full bounds list from
    the grade sentence, the carried bounds and the G-47 bound, per
    check detail, PASS evidence citations, the PASS rollup header
    and the claim disagreement flags. The PASS rollup header
    carries no record side value where the rollup is not PASS,
    because no header stands in that case.
    """
    if element == "full repair list":
        rows = _repair_rows(view)
        return "; ".join(rows) if rows else "none in this result"
    if element == "full bounds list":
        bounds_parts = [_GRADE]
        bounds_parts.extend(view["bounds"])
        bounds_parts.append("G-47 bound: %s" % _G47_BOUND)
        return "; ".join(bounds_parts)
    if element == "per check detail":
        return _check_detail(view)
    if element == "PASS evidence citations":
        return _pass_citations(view)
    if element == "PASS rollup header":
        return _pass_rollup_header(view)
    if element == "claim disagreement flags":
        return _claim_flags(view)
    return None


def _advanced_additions_by_name(generated_form):
    mapping = {}
    for line in generated_form.splitlines():
        for element in ADVANCED_ADDITIONS:
            if element == "PASS rollup header":
                continue
            prefix = "%s: " % element
            if line.startswith(prefix) \
                    and element not in mapping:
                mapping[element] = line[len(prefix):]
                break
        if "PASS rollup header" not in mapping:
            if line.startswith("PASS rollup header: "):
                mapping["PASS rollup header"] = line
            elif line == _WORDS_ONLY_HEADER:
                mapping["PASS rollup header"] = line
    return mapping


def _compare_text_one(generated_form, view, skip):
    """The first text form disagreement not standing in skip.

    The shared elements stand compared first, in canonical order,
    and the Advanced form additions stand compared after them, in
    their canonical sequence, each addition extracted from the
    form and compared against the value the record reading
    carries for that addition. Skip carries the element names
    already reported for this form, so a caller collecting every
    disagreement in the form reaches each remaining one in turn.
    """
    lines = generated_form.splitlines()
    first_line = lines[0] if lines else ""
    if first_line.startswith("title: ") or any(
            line.startswith("full repair list: ")
            for line in lines):
        form_kind = "Advanced"
        form_map = _advanced_lines_by_element(generated_form)
    else:
        form_kind = "Simple"
        form_map = _simple_lines_by_element(view, generated_form)
    for element in CANONICAL_ELEMENTS:
        if element in skip:
            continue
        if element == "precheck not yet run section" \
                and form_kind == "Simple" \
                and not view["is_precheck"]:
            continue
        if element not in form_map:
            return _defect_report(
                element, form_kind,
                _record_value(element, view, form_kind),
                "not stated in the generated form"), element
        record_value = _record_value(element, view, form_kind)
        form_raw = form_map[element]
        if element == "counts lines":
            form_value = _strip_counts_prefix(form_raw)
        else:
            form_value = form_raw
        if form_value != record_value:
            return _defect_report(
                element, form_kind, record_value, form_value), element
    if form_kind == "Advanced":
        additions = _advanced_additions_by_name(generated_form)
        for element in ADVANCED_ADDITIONS:
            if element in skip:
                continue
            record_value = _addition_record_value(element, view)
            if record_value is None:
                if element in additions:
                    return _defect_report(
                        element, form_kind,
                        "no value stands in the result record",
                        additions[element]), element
                continue
            if element not in additions:
                return _defect_report(
                    element, form_kind, record_value,
                    "not stated in the generated form"), element
            if additions[element] != record_value:
                return _defect_report(
                    element, form_kind, record_value,
                    additions[element]), element
    return None, None


def _compare_agentic_one(generated_form, view, skip):
    """The first Agentic disagreement not standing in skip.

    Each element entry stands compared value by value against the
    values the record reading carries: where one value of an
    element differs, the report carries that one value from the
    record and that one value from the form, and no whole shared
    value mapping stands in either position. An element whose
    entry the form does not carry stands reported as a missing
    entry. Skip carries the element and value key pairs already
    reported for this form. The form level rollup field stands
    compared against the rollup standing the record reading
    carries for the form, and the Agentic form additions and
    fields stand compared after it, field by field.
    """
    expected = _element_values(view)
    elements = generated_form.get("elements")
    entries_by_name = {}
    if isinstance(elements, list):
        for entry in elements:
            if isinstance(entry, dict) \
                    and entry.get("name") in CANONICAL_ELEMENTS \
                    and entry.get("name") not in entries_by_name:
                entries_by_name[entry["name"]] = entry
    for element in CANONICAL_ELEMENTS:
        if element not in entries_by_name:
            if (element, "element entry") in skip:
                continue
            return _defect_report(
                element, "Agentic", expected,
                "not stated in the generated form"), (
                    element, "element entry")
    if isinstance(elements, list):
        for entry in elements:
            if not isinstance(entry, dict):
                continue
            element = entry.get("name")
            if element not in CANONICAL_ELEMENTS:
                continue
            for key, value in expected.items():
                if (element, key) in skip:
                    continue
                if entry.get(key) != value:
                    return _defect_report(
                        element, "Agentic", value,
                        entry.get(key)), (element, key)
    if ("rollup line", "rollup field") not in skip:
        if generated_form.get("rollup") != expected["rollup"]:
            return _defect_report(
                "rollup line", "Agentic",
                expected["rollup"],
                generated_form.get("rollup")), (
                    "rollup line", "rollup field")
    # The Agentic form additions and fields at brief section
    # 5.7.5, compared field by field against the same reading
    # the form renders from: the per check results, the PASS
    # evidence citations, the roster difference result, the
    # claim differences, the receipt, the ignored inputs, the
    # field 12 standing, the run kind and the open case
    # positions. A field the form does not carry, or carries
    # with a value the record does not carry, disagrees.
    field_checks = (
        ("per check results", "per_check_results",
         _agentic_per_check(view)),
        ("PASS evidence citations", "PASS evidence citations",
         _agentic_citations(view)),
        ("roster difference result", "roster_difference",
         view["field9"]),
        ("claim differences", "claim_differences",
         view["differences"]),
        ("receipt", "receipt", view["receipt"]),
        ("ignored inputs", "ignored_inputs", view["ignored"]),
        ("field 12", "field_12", _field_12_text(view)),
        ("run kind", "run_kind", view["run_kind"] or "gate run"),
        ("open case positions", "open_case_positions",
         _open_case_positions(view)),
    )
    for element, key, record_value in field_checks:
        if (element, "form field") in skip:
            continue
        form_value = generated_form.get(key)
        if form_value != record_value:
            return _defect_report(
                element, "Agentic", record_value, form_value), (
                    element, "form field")
    return None, None


def _compare_one(result_record, generated_form, view, skip):
    if isinstance(generated_form, dict):
        return _compare_agentic_one(generated_form, view, skip)
    if not isinstance(generated_form, str):
        return None, None
    return _compare_text_one(generated_form, view, skip)


def form_agreement_compare(result_record, generated_form):
    """Compare one generated form against the result record.

    The form agreement comparison unit at brief section 5.7.9.
    Exactly two inputs stand: the result record and one generated
    form, the form standing as a supplied input. Exactly one
    output stands: a DefectReport mapping in the shape 16 fixed
    field set at G24, for the first element that disagrees, or
    None where no element disagrees. Each element value in the
    form is compared against the value the record reading carries
    for that element, element by element, so a disagreement names
    its element and both values with their locations. The defect
    field, and no rollup position, carries the word UNVERIFIABLE.
    """
    view = _view(result_record)
    report, _identity = _compare_one(
        result_record, generated_form, view, frozenset())
    return report


def compare_generated_forms(result_record, generated_forms):
    """The presentation module run comparison path.

    In a run the presentation module calls the comparison unit
    through this path, over every generated form the run rendered
    and has not yet printed: the unit stands called once per
    disagreement, each call returning the first disagreement not
    already reported for that form, so the comparison continues
    within a form and across forms and one DefectReport stands
    for each disagreement, in the order the forms stand given.
    The input generated_forms is the mapping render_forms returns,
    or a single generated form. The output is the list of
    DefectReports the calls return, empty where no element of any
    form disagrees with the record.
    """
    if isinstance(generated_forms, dict) and "elements" not in \
            generated_forms:
        forms = list(generated_forms.values())
    else:
        forms = [generated_forms]
    view = _view(result_record)
    reports = []
    for generated_form in forms:
        skip = set()
        while True:
            report, identity = _compare_one(
                result_record, generated_form, view, skip)
            if report is None:
                break
            reports.append(report)
            skip.add(identity)
    return reports


def comparison_call_paths():
    """The only two call paths to the comparison unit.

    Brief section 5.1 and plan section 8 slice 8: the presentation
    module in a run, and the test harness in test custody. No
    other call path stands.
    """
    return ["presentation module in a run",
            "test harness in test custody"]


def print_run_with_disagreements(disagreement_count):
    """The presentation run printing standing, plan section 10.

    Where the comparison found disagreements in a run, no form is
    printed in that run, and one DefectReport stands for each
    disagreement. Each report carries the fields that rest on a
    standing of their own: the form agreement check name and the
    rule at G23, which brief section 5.7.9 names; the defect field
    word UNVERIFIABLE, which shape 16 at G24 fixes; and the tool
    defect statement and the repair act, whose words brief section
    5.7.9 fixes. No element, value or location field stands in a
    report here, because the count this surface takes carries no
    disagreement of its own for such a field to rest on; the
    reports a real comparison produces, carrying those fields,
    stand at form_agreement_compare and compare_generated_forms.
    No rollup key stands in any report here.
    """
    try:
        count = int(disagreement_count)
    except (TypeError, ValueError):
        count = 0
    if count < 0:
        count = 0
    reports = []
    for _index in range(count):
        reports.append({
            "check_name": _FORM_AGREEMENT_CHECK,
            "form_agreement_check_name": _FORM_AGREEMENT_CHECK,
            "rule": _FORM_AGREEMENT_RULE,
            "defect_field": "UNVERIFIABLE",
            "tool_defect_statement": _TOOL_DEFECT_STATEMENT,
            "repair_act": _TOOL_REPAIR_ACT,
        })
    return {"printed_forms": [], "defect_reports": reports}
