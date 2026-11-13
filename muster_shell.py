"""Module 1, the file reading shell for muster-lite.

The shell captures every named input exactly once, as bytes, in the
run that uses it, and hands the captures to the pure core. It reads no
file that was not named for the run. It applies the file kind guard:
a named input that is not a regular file is refused before any read,
and a symbolic link whose target is not named in any other form is
refused with it. Captures are grouped by resolved identity, so two
namings of one file are read once and stand under the earliest naming.
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
        self.display = os.path.basename(named_path)
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


def capture_inputs(named):
    """Capture the named inputs once each, in naming order.

    named is a list of (path, group) pairs in the order the run named
    them. The result is a list of CapturedFile, one per resolved
    identity (plus one per unreadable naming), in first naming order.
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
        direct = [e for e in group_entries
                  if not os.path.islink(e.named_path)]
        if not direct and len(group_entries) < 2:
            # A lone symbolic link to a target named in no other form.
            keep.append(entry)
            continue
        try:
            with open(entry.named_path, "rb") as handle:
                entry.raw = handle.read()
        except OSError:
            keep.append(entry)
            continue
        entry.status = "read"
        entry.text = _decode(entry.raw)
        if entry.text is None:
            entry.decode_failed = True
        keep.append(entry)
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
    tree. Where a staged entry stands in a tree carrying only part
    of the set, the remaining files are found in the working
    directory, in the tree named by MUSTER_LITE_HOME, or in the
    build and installed trees of this estate.
    """
    candidates = [os.path.join(entry_dir, name),
                  os.path.join(entry_dir, "src", name),
                  os.path.join(os.getcwd(), name)]
    home = os.environ.get("MUSTER_LITE_HOME")
    if home:
        candidates.append(os.path.join(home, name))
    candidates.append(os.path.join(
        os.path.expanduser("~"), "workspace", "muster-lite", "repo",
        name))
    candidates.append(os.path.join(
        os.path.expanduser("~"), "workspace", "muster-lite",
        "installed", name))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return candidates[0]


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
    return data, raw, hashlib.sha256(raw).hexdigest()
