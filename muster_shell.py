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
        # a line break inside a file name is printed as a space: a
        # name can never write a line of its own into a report.
        self.display = os.path.basename(named_path).replace(
            "\r", " ").replace("\n", " ")
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
    return min(group_entries,
               key=lambda entry: (_GROUP_RANK.get(entry.group, 0),
                                  entry.named_path))


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


def _validate_counting_table(data):
    """Refuse a counting table whose rule data is missing or mistyped.

    A table that parses as a JSON object but carries no rules, or
    carries a rule value of the wrong kind, is a damaged shipped
    file, not a table with no rules: it takes the tool fault outcome
    through DataFault, as a shipped file that cannot be used. Keys
    the table form does not require may stand absent; a key that
    stands must carry its stated kind.
    """
    version = data.get("table_version")
    if not isinstance(version, str) or not version:
        raise DataFault("counting table carries no table version")
    if "per_step_rows" in data:
        # A table in the shipped six part form stands complete or
        # not at all: a part deleted from that form is damage, and
        # the table takes the tool fault outcome. A table in the
        # minimal rows form carries no such parts and stands in its
        # own form.
        for part in ("team_bases", "counting_positions",
                     "carried_seats", "exempt_list", "pool_families"):
            if part not in data:
                raise DataFault("counting table in the shipped form "
                                "is missing its %s part" % part)
    keyed = data.get("keyed_base")
    if keyed is not None:
        if not isinstance(keyed, dict):
            raise DataFault("counting table keyed base is not an "
                            "object")
        for field in ("name", "hash"):
            if field in keyed and not isinstance(keyed[field], str):
                raise DataFault("counting table keyed base %s is not "
                                "a string" % field)
        if "bytes" in keyed and not _is_int(keyed["bytes"]):
            raise DataFault("counting table keyed base bytes is not "
                            "a number")
    bases = data.get("team_bases")
    if bases is not None:
        if not isinstance(bases, dict):
            raise DataFault("counting table team bases is not an "
                            "object")
        for team, tiers in bases.items():
            if not isinstance(tiers, dict):
                raise DataFault("counting table base for %s is not "
                                "an object" % team)
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
    for rows_key in ("per_step_rows", "rows"):
        rows = data.get(rows_key)
        if rows is None:
            continue
        if not isinstance(rows, list):
            raise DataFault("counting table %s is not a list"
                            % rows_key)
        for row in rows:
            if not isinstance(row, dict):
                raise DataFault("counting table row is not an object")
            if "minimum" in row and not _is_int(row["minimum"]):
                raise DataFault("counting table row minimum is not "
                                "a number")
            if "step" in row and not _is_int(row["step"]):
                raise DataFault("counting table row step is not a "
                                "number")
    for totals_key in ("step_totals", "board_additions"):
        totals = data.get(totals_key)
        if totals is None:
            continue
        if not isinstance(totals, dict) or not all(
                _is_int(value) for value in totals.values()):
            raise DataFault("counting table %s is not an object of "
                            "counts" % totals_key)
    for list_key in ("counting_positions", "carried_seats",
                     "exempt_list", "pool_families"):
        if list_key in data and not isinstance(data[list_key], list):
            raise DataFault("counting table %s is not a list"
                            % list_key)


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
    return data, raw, hashlib.sha256(raw).hexdigest()
