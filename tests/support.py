"""Support runner and shared helpers for the muster-lite test suite.

The runner invokes the product exactly as an operator would, through its
command line entry. The brief and the plan name the product form (a Python
command line tool, Module 3 entry, run arguments at brief section 5.2) but
name no entry file and no flag spelling; plan section 8 leaves the entry
file name to the Step 14 build record. The runner therefore discovers the
entry among the candidate names below, in the build repo and in the
installed tree, and treats the absence of every candidate as the absence
of the product. Absence is converted into an assertion failure inside each
test through MusterCase.invoke and MusterCase.require_product, so a missing
product gives failures, never errors, never skips, and never a pass.

Run argument convention used by this suite, stated once here: positional
arguments are the supplied files in the order named; named options are
--stage, --runner, --capacity, --context (repeatable), --base-record
(repeatable), and --kind. The --kind option selects the run kind, gate run
or precheck. The runner and capacity options carry the declared runner
identity and capacity as data only; no wording inside a capacity value
selects a run kind or any other product behaviour. This convention is
suite machinery. It pins no product behaviour beyond the run input
contents brief section 5.2 names.

Entry identity condition, stated once here: a candidate file counts as
the product entry only where the file text carries the product name,
muster-lite, the tool name every report prints. A file standing under a
candidate name whose text does not carry that name is not the product
entry: it counts as the absence of the product, and every product
dependent test fails for that absence. This condition is the suite side
form of the Step 14 Entry Binding Verification Condition recorded with
GAP-1; Step 14 verifies the bound entry against the entry its build
record names.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

def _ensure_usable_tempdir():
    """Point tempfile at a usable root when the default probe fails.

    Some run environments refuse the default temporary directory probe.
    The suite stages supplied sets in temporary directories either way;
    where the default root is unusable, a root under the user home stands
    in. This is suite machinery only and pins no product behaviour.
    """
    try:
        with tempfile.TemporaryDirectory():
            pass
        return
    except Exception:
        pass
    fallback = Path.home() / ".tmp" / "muster-lite-tests"
    fallback.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(fallback)


_ensure_usable_tempdir()

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
BUILD_HOME = REPO_ROOT.parent
DESIGN_DIR = BUILD_HOME / "design"
INSTALLED_DIR = BUILD_HOME / "installed"
FIXTURES_DIR = TESTS_DIR / "fixtures"

ENTRY_CANDIDATES = (
    "muster_lite.py",
    "muster-lite.py",
    "musterlite.py",
    "main.py",
    "__main__.py",
    "cli.py",
    "src/muster_lite.py",
    "src/muster-lite.py",
    "src/main.py",
    "muster_lite/__main__.py",
    "muster_lite/cli.py",
    "muster_lite/main.py",
)

DATA_FILE_NAMES = ("counting-table.json", "diagnostic-catalogue.json")

MISSING_REASON = (
    "product does not exist: no command entry file stands in the build "
    "repo or in the installed tree, so the run this test pins cannot be made"
)

CLAIM_CAP = (
    "This report checks the records named in it for consistency with the "
    "staffing rules named in it. It does not prove that any agent was "
    "actually spawned, that any work was done independently, or that the "
    "records supplied are complete."
)

GRADE_SENTENCE = (
    "Muster-lite is a grade L2 records checker. It is not the DQ-012 "
    "isolated checker, and grade L3 is not available for labelling any "
    "record from this tool."
)

CLOSING_LINE = (
    "What this tool did not prove: it did not prove that any agent was "
    "actually spawned, that any work was done independently, or that the "
    "records supplied are complete."
)


PRODUCT_NAME_MARK = "muster-lite"


def is_product_entry(candidate):
    """The entry identity condition stated in the module head."""
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return PRODUCT_NAME_MARK in text


def find_entry():
    for base in (REPO_ROOT, INSTALLED_DIR):
        for rel in ENTRY_CANDIDATES:
            candidate = base / rel
            if candidate.is_file() and is_product_entry(candidate):
                return candidate
    return None


def run_entry_direct(entry, arguments, cwd=None, env_extra=None,
                     timeout=60):
    """Run one named entry file directly, with no discovery step.

    Used where a test stages its own copy of the entry beside staged
    data files: the entry that runs is the entry the files were staged
    beside, and no other entry is discovered or substituted.
    """
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            [sys.executable, str(entry)] + [str(a) for a in arguments],
            cwd=str(cwd or REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return RunResult(False, None, "", "", "run timed out")
    return RunResult(False, proc.returncode, proc.stdout, proc.stderr)


class ChangingFileWatcher:
    """Test side machinery for the changing file fixtures.

    The file at the given path is written with the first content and its
    access time is set older than its modification time, so the first
    read of the file updates its access time under the usual relatime
    rule. A watcher thread polls the access time; on the first change it
    rewrites the file with the second content. A run that captures the
    file once therefore works from the first content only, and a run
    that reads the file a second time meets the second content. The
    attribute fired records whether the change was triggered.
    """

    def __init__(self, path, first_content, second_content):
        self.path = Path(path)
        self.second_content = second_content
        if isinstance(first_content, bytes):
            self.path.write_bytes(first_content)
        else:
            self.path.write_text(first_content, encoding="utf-8")
        stat = self.path.stat()
        os.utime(self.path, (stat.st_atime - 1000, stat.st_mtime))
        self._first_atime = self.path.stat().st_atime
        self.fired = False
        self._stop = False
        import threading
        self._thread = threading.Thread(target=self._watch, daemon=True)

    def _watch(self):
        import time
        while not self._stop:
            try:
                current = self.path.stat().st_atime
            except OSError:
                return
            if current != self._first_atime:
                if isinstance(self.second_content, bytes):
                    self.path.write_bytes(self.second_content)
                else:
                    self.path.write_text(self.second_content,
                                         encoding="utf-8")
                self.fired = True
                return
            time.sleep(0.001)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop = True
        self._thread.join(timeout=2)
        return False


def stage_entry_tree(entry, dest_root):
    """Stage the shipped file set the entry belongs to, in place.

    The product ships as the command entry file and its module files,
    at most 3 modules, with the data files beside the command entry in
    the installed tree. Staging copies every Python file standing in
    the entry directory at its relative place under dest_root, so the
    staged entry keeps its sibling module files and its relative place:
    a top level entry stages with the top level module files beside it,
    and an entry standing in a subdirectory, in the package form or the
    source tree form, stages inside that same subdirectory. Returns the
    staged entry path.
    """
    entry = Path(entry)
    dest_root = Path(dest_root)
    try:
        relative = entry.relative_to(REPO_ROOT)
        base = REPO_ROOT
    except ValueError:
        relative = entry.relative_to(INSTALLED_DIR)
        base = INSTALLED_DIR
    entry_dir = (base / relative).parent
    staged_entry = dest_root / relative
    staged_entry.parent.mkdir(parents=True, exist_ok=True)
    for sibling in sorted(entry_dir.iterdir()):
        if sibling.is_file() and sibling.suffix == ".py":
            target = staged_entry.parent / sibling.name
            target.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copyfile(sibling, target)
    return staged_entry


def find_data_file(name):
    for base in (REPO_ROOT, REPO_ROOT / "src", INSTALLED_DIR):
        candidate = base / name
        if candidate.is_file():
            return candidate
    return None


def sid(number):
    """A deterministic full session identifier in the issued session form."""
    return "00000000-0000-4000-8000-%012d" % number


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


class RunResult:
    def __init__(self, missing, returncode, stdout, stderr, reason=""):
        self.missing = missing
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.reason = reason


def run_product(arguments, cwd=None, env_extra=None, timeout=60):
    entry = find_entry()
    if entry is None:
        return RunResult(True, None, "", "", MISSING_REASON)
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            [sys.executable, str(entry)] + [str(a) for a in arguments],
            cwd=str(cwd or REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return RunResult(False, None, "", "", "run timed out")
    return RunResult(False, proc.returncode, proc.stdout, proc.stderr)


def split_agentic(stdout):
    """Return the Agentic form parsed as JSON, or None if not present."""
    start = stdout.find("{")
    while start != -1:
        try:
            value, _end = json.JSONDecoder().raw_decode(stdout[start:])
            if isinstance(value, dict):
                return value
        except ValueError:
            pass
        start = stdout.find("{", start + 1)
    return None


def rollup_word(stdout):
    match = re.search(
        r"^Rollup: (?:PRECHECK )?(PASS|FAIL|NOT PROVEN|UNVERIFIABLE)\b",
        stdout,
        flags=re.MULTILINE,
    )
    return match.group(1) if match else None


def roster_text(stage="Step 99", tier="Low", teams=(), board=(), extra_lines=(),
                claim_lines=()):
    """Build a synthetic roster artifact in markdown form from brief shapes.

    teams: list of (team name, round label or None, list of (role, id number
    or raw value, position)) tuples. board: list of (role, id number or raw
    value). The text is fixture data only; it copies no real build record.
    """
    lines = ["# Roster artifact: %s" % stage, "",
             "Stage: %s. Tier: %s." % (stage, tier), ""]
    for team_name, round_label, seats in teams:
        heading = "## Team: %s" % team_name
        if round_label:
            heading += " (%s)" % round_label
        lines.append(heading)
        for role, holder, position in seats:
            value = sid(holder) if isinstance(holder, int) else holder
            lines.append("- Seat: %s; holder %s; position %s; spawn reference "
                         "names role %s and stage %s."
                         % (role, value, position, role, stage))
        lines.append("")
    if board:
        lines.append("## Review board")
        for role, holder in board:
            value = sid(holder) if isinstance(holder, int) else holder
            lines.append("- Board seat: %s; holder %s." % (role, value))
        lines.append("")
    lines.extend(extra_lines)
    lines.extend(claim_lines)
    return "\n".join(lines) + "\n"


class MusterCase(unittest.TestCase):
    """Base case: every test reaches the product through the runner."""

    def require_product(self):
        if find_entry() is None:
            self.fail(MISSING_REASON)

    def require_data_file(self, name):
        path = find_data_file(name)
        if path is None:
            self.fail(
                "product does not exist: the shipped data file %s stands "
                "nowhere in the build repo or the installed tree" % name)
        return path

    def invoke(self, arguments, **kwargs):
        result = run_product(arguments, **kwargs)
        if result.missing:
            self.fail(result.reason)
        return result

    def run_stage(self, files, stage="Step 99", runner="Fixture Auditor",
                  capacity="Auditor", context=(), extra=()):
        """Write a supplied set to a temp dir and run the product on it.

        files: dict of file name to text (str) or bytes. Returns
        (RunResult, dict of name to Path). The temp dir is removed when the
        test finishes.
        """
        self.require_product()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        paths = {}
        args = []
        for name, content in files.items():
            path = Path(tmp.name) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
            paths[name] = path
            args.append(str(path))
        args += ["--stage", stage, "--runner", runner, "--capacity", capacity]
        for ctx in context:
            args += ["--context", str(paths[ctx]) if ctx in paths else ctx]
        args += list(extra)
        return self.invoke(args), paths

    def assert_report_present(self, result):
        """A report stands in the output this result carries.

        The report heading stands in the output and a rollup word
        stands in it. An output that is empty, or that carries no
        report, fails this assertion whatever else it satisfies.
        """
        self.assertIn("Muster-lite staffing report:", result.stdout)
        self.assertIsNotNone(
            rollup_word(result.stdout),
            "no rollup word stands in the output, so no report stands")

    def assert_rollup(self, result, word, code):
        self.assertEqual(result.returncode, code,
                         "exit code for rollup %s" % word)
        self.assertEqual(rollup_word(result.stdout), word)

    def assert_in_stdout(self, result, needle):
        self.assertIn(needle, result.stdout)

    def agentic(self, result):
        value = split_agentic(result.stdout)
        self.assertIsNotNone(value, "Agentic form JSON object stands in output")
        return value
