"""Module 1, the file reading shell for muster-lite.

The shell captures every named input exactly once, as bytes, in the
run that uses it, and hands the captures to the pure core. It reads no
file that was not named for the run. It applies the file kind guard:
a named input that is not a regular file is refused before any read,
and a symbolic link whose target is not named in any other form is
refused with it. Captures are grouped by resolved identity, so two
namings of one file are read once and stand under the kept naming,
the first of its namings under the completed key at brief
Section 5.3.
"""

import functools
import hashlib
import json
import os
import stat


class DataFault(Exception):
    """A shipped data file cannot be captured or parsed."""


class CapturedFile(object):
    def __init__(self, named_path, group):
        self.named_path = named_path
        self.group = group
        self.groups = {group}
        # The display name is printed into the fixed report lines, so
        # every line break character inside a file name is printed as
        # a space: a name can never write a line of its own into a
        # report. The line break characters are the closed splitlines
        # boundary set: newline, carriage return, U+2028, U+2029,
        # U+000B, U+000C, U+001C, U+001D, U+001E, and U+0085, every
        # character a line reader splits text on.
        self.display = os.path.basename(named_path)
        for break_char in ("\n", "\r", "\u2028", "\u2029",
                           "\u000b", "\u000c", "\u0085",
                           "\u001c", "\u001d", "\u001e"):
            self.display = self.display.replace(break_char, " ")
        self.identity = None
        self.raw = None
        self.text = None
        self.status = "unread"
        self.decode_failed = False


def _decode(raw):
    """Decode captured bytes as text, or return None where undecodable.

    A byte order mark is stripped and line endings are left for the
    line reader, which treats every ending form the same.
    """
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    return text


_GROUP_RANK = {"supplied": 0, "base": 1, "context": 2}


def _path_compare(left, right):
    """Compare two paths as named, under the path part rule at
    brief Section 5.3, in the same form the core carries: a maximal
    run of ASCII digit characters compares by its integer value,
    two runs of equal integer value compare in plain alphabetical
    order, and every other character compares by its code point."""
    li = 0
    ri = 0
    while li < len(left) and ri < len(right):
        lc = left[li]
        rc = right[ri]
        if "0" <= lc <= "9" and "0" <= rc <= "9":
            lj = li
            while lj < len(left) and "0" <= left[lj] <= "9":
                lj += 1
            rj = ri
            while rj < len(right) and "0" <= right[rj] <= "9":
                rj += 1
            lrun = left[li:lj]
            rrun = right[ri:rj]
            if int(lrun) != int(rrun):
                return -1 if int(lrun) < int(rrun) else 1
            if lrun != rrun:
                return -1 if lrun < rrun else 1
            li = lj
            ri = rj
            continue
        if lc != rc:
            return -1 if ord(lc) < ord(rc) else 1
        li += 1
        ri += 1
    if li == len(left) and ri == len(right):
        return 0
    return -1 if li == len(left) else 1


def _kept_naming(group_entries):
    """The naming of one file that the run keeps, under the key.

    Where two or more namings name the same file, the kept naming is
    the first under the completed key at brief Section 5.3: the
    input group of the naming first, a supplied naming before a base
    record naming and a base record naming before a context naming,
    a context naming carrying the shared component that stands after
    the supplied groups, and then the path as named. The kept naming
    is a property of the supplied set as a set, never of the order
    an operator named its files in.
    """
    def _naming_compare(left, right):
        left_rank = _GROUP_RANK.get(left.group, 0)
        right_rank = _GROUP_RANK.get(right.group, 0)
        if left_rank != right_rank:
            return -1 if left_rank < right_rank else 1
        return _path_compare(left.named_path, right.named_path)

    return sorted(group_entries,
                  key=functools.cmp_to_key(_naming_compare))[0]


def capture_inputs(named):
    """Capture the named inputs once each.

    named is a list of (path, group) pairs in the order the run named
    them. The result is a list of CapturedFile, one per resolved
    identity (plus one per unreadable naming). A file named under
    two or more namings is read once and stands under the kept
    naming, chosen by _kept_naming under the completed key.
    """
    entries = []
    by_identity = {}
    for path, group in named:
        entry = CapturedFile(path, group)
        entries.append(entry)
        try:
            info = os.stat(path)
        except OSError:
            continue
        if not stat.S_ISREG(info.st_mode):
            continue
        entry.identity = (info.st_dev, info.st_ino)
        by_identity.setdefault(entry.identity, []).append(entry)
    keep = []
    seen = set()
    for entry in entries:
        if entry.identity is None:
            keep.append(entry)
            continue
        if entry.identity in seen:
            continue
        seen.add(entry.identity)
        group_entries = by_identity[entry.identity]
        kept = _kept_naming(group_entries)
        kept.groups = {e.group for e in group_entries}
        direct = [e for e in group_entries
                  if not os.path.islink(e.named_path)]
        if not direct and len(group_entries) < 2:
            # A lone symbolic link to a target named in no other form.
            keep.append(kept)
            continue
        try:
            with open(kept.named_path, "rb") as handle:
                kept.raw = handle.read()
        except OSError:
            keep.append(kept)
            continue
        kept.status = "read"
        kept.text = _decode(kept.raw)
        if kept.text is None:
            kept.decode_failed = True
        keep.append(kept)
    # Family G of round 3: two different files sharing a basename
    # do not collapse into one line in the files read list. Where
    # captured files with different named paths share one display
    # basename, each stands under the path as named for it, the
    # brief Section 5.3 list form, with line break characters
    # printed as spaces on the display rule above. A file whose
    # basename stands alone keeps the basename display form.
    by_display = {}
    for entry in keep:
        by_display.setdefault(entry.display, []).append(entry)
    for _display, entries in by_display.items():
        if len({entry.named_path for entry in entries}) > 1:
            for entry in entries:
                display = entry.named_path
                for break_char in ("\n", "\r", "\u2028", "\u2029",
                                   "\u000b", "\u000c", "\u0085",
                                   "\u001c", "\u001d", "\u001e"):
                    display = display.replace(break_char, " ")
                entry.display = display
    return keep


def _reject_constant(value):
    raise DataFault("non finite token in shipped data file: %s" % value)


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DataFault("duplicate key in shipped data file: %s" % key)
        result[key] = value
    return result


def find_data_path(entry_dir, name):
    """Find a shipped data file, beside the entry first.

    The shipped file set stands beside the entry in the installed
    tree. A position beside the entry, or in its src tree, governs
    where anything stands at that position, a file or any other
    shape: the run uses that position and faults where it cannot be
    read, and never borrows a file past an occupied position. Where
    no position beside the entry stands occupied and a staged entry
    carries only part of the set, the remaining files are found in
    the build and installed trees of this estate, and in no other
    place: no environment variable and no working directory ever
    supplies a shipped data file.
    """
    own = [os.path.join(entry_dir, name),
           os.path.join(entry_dir, "src", name)]
    for candidate in own:
        if os.path.exists(candidate):
            return candidate
    candidates = own + [
        os.path.join(os.path.expanduser("~"), "workspace",
                     "muster-lite", "repo", name),
        os.path.join(os.path.expanduser("~"), "workspace",
                     "muster-lite", "installed", name)]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return candidates[0]


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_keyed_base(keyed):
    """A keyed base that stands must stand in its whole form."""
    if not isinstance(keyed, dict):
        raise DataFault("counting table keyed base is not an object")
    for field in ("name", "hash"):
        if not isinstance(keyed.get(field), str) or not keyed[field]:
            raise DataFault("counting table keyed base %s is not a "
                            "string" % field)
    if not _is_int(keyed.get("bytes")):
        raise DataFault("counting table keyed base bytes is not a "
                        "number")


def _validate_team_bases(bases):
    """Team bases that stand must stand whole and typed."""
    if not isinstance(bases, dict) or not bases:
        raise DataFault("counting table team bases is not a non "
                        "empty object")
    for team, tiers in bases.items():
        if not isinstance(tiers, dict) or not tiers:
            raise DataFault("counting table base for %s is not a "
                            "non empty object" % team)
        for tier, value in tiers.items():
            if _is_int(value):
                continue
            if isinstance(value, dict) and all(
                    _is_int(value.get(end))
                    for end in ("minimum", "maximum")):
                continue
            raise DataFault(
                "counting table base for %s at %s is not a count "
                "or a band" % (team, tier))


def _validate_table_rows(rows, rows_key, seen_keys=None):
    """Every row, in every rows form, carries its whole form.

    The counting reads the minimum inside every row, so a row with
    no minimum, no step, or no team is damage in the shipped form
    and in the minimal rows form alike, and an empty rows list
    carries no rule at all.

    The duplicate check reads the row parts as one row set: a
    caller validating more than one part of one table passes the
    same seen set to each part, so a step and team standing in
    two parts faults exactly as a step and team standing twice
    in one part does.
    """
    if not isinstance(rows, list) or not rows:
        raise DataFault("counting table %s is not a non empty list"
                        % rows_key)
    for row in rows:
        if not isinstance(row, dict):
            raise DataFault("counting table row is not an object")
        if not _is_int(row.get("step")):
            raise DataFault("counting table row step is not a "
                            "number")
        if not isinstance(row.get("team"), str) or not row["team"]:
            raise DataFault("counting table row team is not a "
                            "string")
        if not _is_int(row.get("minimum")):
            raise DataFault("counting table row carries no minimum "
                            "as a number")
    if seen_keys is None:
        seen_keys = set()
    for row in rows:
        key = (row.get("step"), row.get("team"))
        if key in seen_keys:
            raise DataFault("counting table %s carries two rows "
                            "for one step and team" % rows_key)
        seen_keys.add(key)


def _validate_table_totals(totals, totals_key, non_empty):
    if not isinstance(totals, dict):
        raise DataFault("counting table %s is not an object of "
                        "counts" % totals_key)
    if non_empty and not totals:
        raise DataFault("counting table %s stands empty"
                        % totals_key)
    for key, value in totals.items():
        try:
            int(key)
        except (TypeError, ValueError):
            raise DataFault("counting table %s key is not a number"
                            % totals_key)
        if not _is_int(value):
            raise DataFault("counting table %s is not an object of "
                            "counts" % totals_key)


_SHIPPED_TABLE_PARTS = ("team_bases", "per_step_rows", "step_totals",
                        "keyed_base", "board_additions",
                        "counting_positions", "carried_seats",
                        "exempt_list", "pool_families")


def _validate_counting_table(data):
    """Refuse a counting table whose rule data is missing or mistyped.

    A table that parses as a JSON object but carries no rules, or
    carries a rule value of the wrong kind, is a damaged shipped
    file, not a table with no rules: it takes the tool fault outcome
    through DataFault, as a shipped file that cannot be used. The
    validation covers every part the counting reads: team_bases,
    per_step_rows, step_totals, keyed_base, and the minimum inside
    every row, in every rows form the shipped table and the suite
    use. A part that stands in either form must stand whole and
    typed, a part present as a null value is mistyped and faults,
    and damage by absence inside a standing shape faults the same
    way. Keys the table form does not name may stand in the table
    and govern nothing.

    A table standing in the shipped form, which is any table
    carrying a shipped form part, must stand complete in that
    form: every shipped part present, its rows and bases non
    empty. A table in the minimal rows form, carrying rows and no
    shipped form part, stands in its own form and is not refused
    for lacking parts of the other form.
    """
    version = data.get("table_version")
    if not isinstance(version, str) or not version:
        raise DataFault("counting table carries no table version")
    shipped_form = any(
        part in data for part in _SHIPPED_TABLE_PARTS
        if part != "keyed_base")
    if shipped_form:
        for part in _SHIPPED_TABLE_PARTS:
            if part not in data:
                raise DataFault("counting table in the shipped form "
                                "is missing its %s part" % part)
        _validate_team_bases(data["team_bases"])
        row_keys = set()
        _validate_table_rows(data["per_step_rows"], "per_step_rows",
                             row_keys)
        _validate_keyed_base(data["keyed_base"])
        _validate_table_totals(data["step_totals"], "step_totals",
                               non_empty=True)
        _validate_table_totals(data["board_additions"],
                               "board_additions", non_empty=True)
        positions = data["counting_positions"]
        if not isinstance(positions, list) or \
                len(positions) != 5 or set(positions) != {
                    "counted in base", "over base at team level",
                    "uncounted at this step", "board additional",
                    "exempt"}:
            raise DataFault("counting table counting_positions "
                            "does not stand as the five positions")
        carried = data["carried_seats"]
        if not isinstance(carried, list) or not carried:
            raise DataFault("counting table carried_seats is not "
                            "a non empty list")
        for entry in carried:
            if not isinstance(entry, dict) or any(
                    not isinstance(entry.get(field), str)
                    or not entry[field]
                    for field in ("kind", "position", "teams")):
                raise DataFault("counting table carried_seats "
                                "entry does not stand in its form")
        for list_key in ("exempt_list", "pool_families"):
            values = data[list_key]
            if not isinstance(values, list) or not values or any(
                    not isinstance(value, str) or not value
                    for value in values):
                raise DataFault("counting table %s does not stand "
                                "as a non empty list of strings"
                                % list_key)
        if "rows" in data:
            _validate_table_rows(data["rows"], "rows", row_keys)
    else:
        if "rows" not in data:
            raise DataFault("counting table carries no rows in any "
                            "form the table ships in")
        _validate_table_rows(data["rows"], "rows")
        if "keyed_base" in data:
            _validate_keyed_base(data["keyed_base"])
        if "team_bases" in data:
            _validate_team_bases(data["team_bases"])
        for totals_key in ("step_totals", "board_additions"):
            if totals_key in data:
                _validate_table_totals(data[totals_key], totals_key,
                                       non_empty=False)


def _validate_diagnostic_catalogue(data):
    """Refuse a diagnostic catalogue that cannot stand as shipped.

    The catalogue stands on the same brief Section 6 footing as
    the counting table: it ships as a version and its rows, and a
    catalogue carrying no version, a version of the wrong kind, or
    rows of the wrong kind is a damaged shipped file and takes the
    tool fault outcome through DataFault. Catalogue rows drive no
    check, so this validation changes no verdict on a catalogue
    that stands whole.
    """
    version = data.get("catalogue_version")
    if not isinstance(version, str) or not version:
        raise DataFault("diagnostic catalogue carries no catalogue "
                        "version")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        raise DataFault("diagnostic catalogue rows is not a non "
                        "empty list")
    codes = []
    for row in rows:
        if not isinstance(row, dict):
            raise DataFault("diagnostic catalogue row is not an "
                            "object")
        if set(row.keys()) != {"code", "kind", "shape",
                               "rule_reference"} or any(
                not isinstance(row.get(field), str)
                or not row[field]
                for field in ("code", "kind", "shape",
                              "rule_reference")):
            raise DataFault("diagnostic catalogue row does not "
                            "carry its four things as strings")
        codes.append(row["code"])
    if len(codes) != len(set(codes)):
        raise DataFault("diagnostic catalogue carries a code "
                        "more than once")
    if set(codes) != {"ML-%02d" % number for number in range(1, 31)}:
        raise DataFault("diagnostic catalogue rows do not stand "
                        "as the shipped row set")


def load_data_file(entry_dir, name):
    """Capture and strictly parse one shipped data file.

    Returns (data, raw bytes, sha256 hex of the exact bytes captured).
    Raises DataFault where the file cannot be read or parsed.
    """
    path = find_data_path(entry_dir, name)
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise DataFault("shipped data file cannot be read: %s" % exc)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DataFault("shipped data file cannot be decoded: %s" % exc)
    try:
        data = json.loads(text, object_pairs_hook=_no_duplicate_keys,
                          parse_constant=_reject_constant)
    except DataFault:
        raise
    except ValueError as exc:
        raise DataFault("shipped data file cannot be parsed: %s" % exc)
    if not isinstance(data, dict):
        raise DataFault("shipped data file is not a JSON object")
    if name == "counting-table.json":
        _validate_counting_table(data)
    if name == "diagnostic-catalogue.json":
        _validate_diagnostic_catalogue(data)
    return data, raw, hashlib.sha256(raw).hexdigest()
