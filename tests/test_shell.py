"""Slice 2 shell groups: TM-SHELL-1, TM-SHELL-2, TM-SHELL-3.

Settled rule note, standing with this module: the CR-41 precedence is a
settled plan rule, stated at TM-SHELL-1, TM-SHELL-3, TM-DATA-1, and
TM-TEST-2: section level exclusion under the priority rule is applied
before seat level succession parsing, and a seat inside a superseded
section enters no count and no total. That outcome stands asserted at
test_succession_inside_superseded_section_enters_no_count in
tests/test_suite_foundation.py and at the superseded section tests in
this module. The held test block at the end of plan section 2 names two
held parts only, the H-7 held determination and the AC-16 specimen
result; the CR-41 precedence is not one of them.

Settled H-7 note, standing with TM-SHELL-3 in this module: the H-7
claim kind determinism item stands settled by Manager settlement, the
use versus mention rule, and the ClaimRecord parsing limb of that
determination stands encoded in the held part of TM-SHELL-3 below: a
candidate sentence standing in a supplied claim bearing file that
only mentions a claim takes no claim kind from that sentence, and a
candidate sentence with no marker takes the kind its text asserts.
The markers name mention shapes only. The encoding covers the settled
determination only, and forms outside it stand as they stood.
"""

import os
import tempfile
from pathlib import Path

from tests.support import (ChangingFileWatcher, MusterCase, roster_text,
                           sid)

BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]
AUDIT = [("Colour lens Red", 1, "counted in base"),
         ("Colour lens Blue", 2, "counted in base"),
         ("Colour lens Purple", 3, "counted in base")]


def staffed(**kw):
    return roster_text(teams=[("Audit team", None, AUDIT)], board=BOARD,
                       **kw)


class ShellStaging(MusterCase):
    """Staging helper: write files, then name only the paths given."""

    def stage_dir(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def write_file(self, root, name, content):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def invoke_paths(self, paths, stage="Step 99"):
        args = [str(p) for p in paths]
        args += ["--stage", stage, "--runner", "Fixture Auditor",
                 "--capacity", "Auditor"]
        return self.invoke(args)


class TestShellReading(ShellStaging):
    """TM-SHELL-1, supplied set reading and input classification."""

    def test_named_input_read_and_counted(self):
        res, _ = self.run_stage({"roster.md": staffed()})
        self.assert_rollup(res, "PASS", 0)

    def test_fifo_input_refused_before_any_read(self):
        # A named FIFO is refused before any read: it is reported as
        # unread, never as empty, no content is taken from it, and the
        # run completes on the other named files in the set.
        self.require_product()
        if not hasattr(os, "mkfifo"):
            self.fail("this platform provides no mkfifo, so the FIFO "
                      "fixture charged at TM-SHELL-1 cannot be staged")
        root = self.stage_dir()
        roster = self.write_file(root, "roster.md", staffed())
        fifo = root / "input.fifo"
        os.mkfifo(fifo)
        res = self.invoke_paths([fifo, roster])
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "input.fifo")
        self.assert_in_stdout(res, "unread")

    def test_named_link_to_roster_read_once(self):
        # One roster file named under two namings, its own name and a
        # link naming that resolves to it: the file is read once,
        # parsed once, and listed once, so its seats count once.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root, "roster.md", staffed())
        link = root / "roster-link.md"
        os.symlink(roster, link)
        res = self.invoke_paths([roster, link])
        self.assert_rollup(res, "PASS", 0)
        count = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(count["Audit team"]["counted_total"], 3)
        self.assertEqual(count["Audit team"]["entries"], 3)

    def test_two_links_to_one_file_deduplicated(self):
        # Two named paths, each a link to the same readable roster file
        # that is named in no other form: neither path is refused, and
        # the file is read once, parsed once, and listed once under the
        # earliest of its namings.
        self.require_product()
        root = self.stage_dir()
        target = self.write_file(root, "target-roster.md", staffed())
        first = root / "a-link.md"
        second = root / "b-link.md"
        os.symlink(target, first)
        os.symlink(target, second)
        res = self.invoke_paths([second, first])
        self.assert_rollup(res, "PASS", 0)
        count = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(count["Audit team"]["counted_total"], 3)
        self.assertEqual(count["Audit team"]["entries"], 3)

    def test_duplicate_naming_of_one_file_read_once(self):
        # One roster file named twice under two different spellings
        # that resolve to the same resolved identity (a hard linked
        # second name): read once, parsed once, listed once.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root, "roster.md", staffed())
        twin = root / "roster-twin.md"
        os.link(roster, twin)
        res = self.invoke_paths([roster, twin])
        count = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(count["Audit team"]["counted_total"], 3)
        self.assertEqual(count["Audit team"]["entries"], 3)

    def test_bom_and_crlf_forms_read_equal_to_plain(self):
        plain, _ = self.run_stage({"roster.md": staffed()})
        self.assert_report_present(plain)
        bom = b"\xef\xbb\xbf" + staffed().encode("utf-8")
        crlf = staffed().replace("\n", "\r\n").encode("utf-8")
        for variant in (bom, crlf):
            res, _ = self.run_stage({"roster.md": variant})
            self.assert_report_present(res)
            self.assertEqual(res.stdout, plain.stdout)

    def test_undecodable_file_unread_and_seats_not_proven(self):
        bad = staffed().encode("utf-8") + b"\nNote: \xff\xfe.\n"
        res, _ = self.run_stage({"roster.md": bad})
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")
        self.assertNotEqual(res.returncode, 4)

    def test_superseded_section_enters_nothing(self):
        res, _ = self.run_stage({"roster.md": staffed(extra_lines=[
            "## Superseded section",
            "Colour lens Red: holder %s, counted in base." % sid(21),
            "The section above is superseded under the priority rule "
            "and enters nothing for this run."])})
        count = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(count["Audit team"]["counted_total"], 3)

    def test_two_rosters_with_no_governing_statement(self):
        first = staffed()
        second = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 4, "counted in base"),
                     ("Colour lens Blue", 5, "counted in base"),
                     ("Colour lens Purple", 6, "counted in base")])],
            board=BOARD)
        res, _ = self.run_stage({"one.md": first, "two.md": second})
        self.assert_in_stdout(res, "NOT PROVEN")

    def test_mismatched_stage_takes_unverifiable(self):
        res, _ = self.run_stage({"roster.md": staffed()},
                                stage="Step 100")
        self.assert_rollup(res, "UNVERIFIABLE", 3)

    def test_changing_file_fixture_charged(self):
        # The record file limb of the one changing file fixture: a
        # supplied record file presents one content on its first
        # reading and a different content on any later reading in the
        # same run, through the test side ChangingFileWatcher. The run
        # must build every shape, count, and manifest entry from the
        # first capture only.
        self.require_product()
        root = self.stage_dir()
        roster = root / "roster.md"
        second = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 4, "counted in base"),
                     ("Colour lens Blue", 5, "counted in base"),
                     ("Colour lens Purple", 6, "counted in base")])],
            board=BOARD)
        with ChangingFileWatcher(roster, staffed(), second) as watch:
            res = self.invoke_paths([roster])
        self.assertTrue(watch.fired)
        self.assertEqual(roster.read_text(encoding="utf-8"), second)
        self.assert_rollup(res, "PASS", 0)
        holders = {s["holder"] for s in self.agentic(res)["seats"]}
        self.assertIn(sid(1), holders)
        self.assertNotIn(sid(4), holders)

    def test_needed_record_present_but_not_named_is_not_found_or_read(self):
        # A needed record stands in the same tree as the named files
        # but is not named for the run: the shell must not find it,
        # read it, or rest any seat or count on it.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root, "roster.md", staffed())
        self.write_file(root, "unnamed-needed.md", roster_text(
            teams=[("Write tests team", None,
                    [("Test author", 44, "counted in base")])],
            board=BOARD))
        res = self.invoke_paths([roster])
        self.assert_rollup(res, "PASS", 0)
        holders = {s["holder"] for s in self.agentic(res)["seats"]}
        self.assertNotIn(sid(44), holders)
        self.assertNotIn("unnamed-needed.md", res.stdout)

    def test_mixed_name_manifest_order_fixture(self):
        # A supplied set whose paths as named mix letter case,
        # separators, and digit runs, carrying the step2 and step10
        # forms of one name, two names that differ only in letter case,
        # and two names that differ only at a separator. The manifest
        # order of the set is the completed key order at brief section
        # 5.3: input group first, then the path as named in plain
        # alphabetical order, character by character by code point, so
        # digit runs carry no numeric value.
        self.require_product()
        root = self.stage_dir()
        names = ["step2.md", "step10.md", "STEP2.md", "step-2.md",
                 "step_2.md"]
        paths = {}
        for name in names:
            paths[name] = self.write_file(
                root, name, "# Step record\n\nStage: Step 99.\n")
        roster = self.write_file(root, "roster.md", staffed())
        named = [paths[name] for name in
                 ("step2.md", "step_2.md", "STEP2.md", "step10.md",
                  "step-2.md")]
        res = self.invoke_paths(named + [roster])
        supplied_lines = [text for text in res.stdout.splitlines()
                          if text.startswith("Supplied set:")]
        if not supplied_lines:
            self.fail("product output carries no Supplied set line, "
                      "so the manifest order this test pins stands in "
                      "no output")
        line = supplied_lines[0]
        expected = ["STEP2.md", "step-2.md", "step10.md", "step2.md",
                    "step_2.md"]
        positions = [line.find(name) for name in expected]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))

    def test_identifier_variant_spellings_handed_on_as_two_strings(self):
        # Each pair below is handed on as two different strings: no
        # stripping, no case folding, and no normalisation form is
        # applied to an identifier as read.
        pairs = (
            ("Fixture Name One", " Fixture Name One "),
            ("Caf\u00e9 Fixture Name", "Cafe\u0301 Fixture Name"),
            ("Fixture Case Name", "fixture case name"),
        )
        for first, second in pairs:
            with self.subTest(first=first, second=second):
                text = roster_text(teams=[(
                    "Audit team", None,
                    [("Colour lens Red", first, "counted in base"),
                     ("Colour lens Blue", second, "counted in base"),
                     ("Colour lens Purple", "Fixture Name Three",
                      "counted in base")])], board=BOARD)
                res, _ = self.run_stage({"roster.md": text})
                count = {c["name"]: c
                         for c in self.agentic(res)["counts"]}
                self.assertEqual(count["Audit team"]["entries"], 3)
                self.assertEqual(count["Audit team"]["counted_total"], 3)

    def test_outside_supplied_set_refusal_in_link_form(self):
        # A named path that is a link to a readable roster file that is
        # not named for the run in any form is refused: the target file
        # is not read, its content enters no shape, count, or check,
        # and the named path is reported as unread, never as empty.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root, "roster.md", staffed())
        target = self.write_file(root, "outside-roster.md", roster_text(
            teams=[("Write tests team", None,
                    [("Test author", 44, "counted in base")])],
            board=BOARD))
        link = root / "outside-link.md"
        os.symlink(target, link)
        res = self.invoke_paths([link, roster])
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "outside-link.md")
        self.assert_in_stdout(res, "unread")
        holders = {s["holder"] for s in self.agentic(res)["seats"]}
        self.assertNotIn(sid(44), holders)


class TestShellKinds(MusterCase):
    """TM-SHELL-2, supplied kinds and ignored inputs."""

    def test_spawn_export_kind_ignored_and_listed(self):
        res, _ = self.run_stage(
            {"roster.md": staffed(), "export.json": '{"spawns": []}\n'})
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "export.json")

    def test_unknown_file_listed_as_ignored_not_read(self):
        res, _ = self.run_stage(
            {"roster.md": staffed(), "notes.bin": b"\x00\x01\x02"})
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "notes.bin")

    def test_context_file_named_by_manifest_stands_supplied(self):
        res, _ = self.run_stage(
            {"roster.md": staffed(), "ctx.md": "# Context\n"},
            context=["ctx.md"])
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "ctx.md")


class TestShellLabels(MusterCase):
    """TM-SHELL-3, round label equivalence and the CR-41 fixtures."""

    SAME_ROUND = (
        "Round 1",
        "R1",
        "round 1",
        "ROUND 1",
        "Round 01",
        "Round 1 2026-11-01",
        " Round 1 ",
    )

    OUTSIDE_FORM = (
        "Round1",
        "Round  1",
        "R 1",
        "Round\t1",
        "Pre Round 1",
        "Round 1 draft",
        "Round 2",
        "Round",
    )

    def two_block_roster(self, first_label, second_label):
        return roster_text(
            teams=[("Audit team", first_label,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base")]),
                   ("Audit team", second_label,
                    [("Colour lens Purple", 3, "counted in base")])],
            board=BOARD)

    def test_round_label_spellings_in_the_form_count_the_same_round(self):
        for label in self.SAME_ROUND:
            with self.subTest(label=label):
                res, _ = self.run_stage(
                    {"roster.md": self.two_block_roster("Round 1", label)})
                counts = [c for c in self.agentic(res)["counts"]
                          if c["name"] == "Audit team"]
                self.assertEqual(len(counts), 1)
                self.assertEqual(counts[0]["counted_total"], 3)
                self.assertEqual(counts[0]["entries"], 3)

    def test_round_label_spellings_outside_the_form_count_apart(self):
        for label in self.OUTSIDE_FORM:
            with self.subTest(label=label):
                res, _ = self.run_stage(
                    {"roster.md": self.two_block_roster("Round 1", label)})
                counts = [c for c in self.agentic(res)["counts"]
                          if c["name"] == "Audit team"]
                self.assertEqual(len(counts), 2)
                self.assertEqual(
                    sorted(c["counted_total"] for c in counts), [1, 2])

    def test_cr41_one_file_superseded_projection(self):
        res, _ = self.run_stage({"roster.md": staffed(extra_lines=[
            "A projected roster stands in this record labelled as a "
            "projection and superseded by the roster above."])})
        self.assert_rollup(res, "PASS", 0)

    def test_claim_kind_mention_in_register_takes_no_claim(self):
        # Settled H-7 determination, held part of TM-SHELL-3: the
        # shell parses claim bearing files into ClaimRecord shapes,
        # and the claim kind is taken from what the claim text asserts
        # under the use versus mention rule. A register sentence that
        # only mentions the family 1 claim, in the conditional form,
        # asserts nothing: family 1 stands unclaimed in the run, its
        # standing limit prints, and the rollup is not capped by it.
        res, _ = self.run_stage({
            "roster.md": staffed(),
            "register.md": "# Stage register\n\nStage: Step 99.\n\n"
                           "Freshness note: if the holding records "
                           "are supplied, the family 1 exclusion would "
                           "be claimed as held for this stage.\n"})
        self.assert_rollup(res, "PASS", 0)
        unclaimed = [line for line in res.stdout.splitlines()
                     if line.startswith("Unclaimed freshness "
                                        "families:")]
        self.assertTrue(unclaimed)
        self.assertIn("family 1", unclaimed[0].lower())

    def test_claim_kind_unmarked_sentence_in_register_asserts(self):
        # The unmarked fallback at the same parsing limb: a register
        # sentence with no marker counts as asserted, so family 1
        # stands claimed, its facts stand not stated in this set, and
        # the claimed family takes NOT PROVEN and caps the rollup.
        res, _ = self.run_stage({
            "roster.md": staffed(),
            "register.md": "# Stage register\n\nStage: Step 99.\n\n"
                           "Freshness claim: family 1 held for this "
                           "stage.\n"})
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")
        claimed = [line for line in res.stdout.splitlines()
                   if line.startswith("Claimed freshness families "
                                      "with facts not stated:")]
        self.assertTrue(claimed)
        self.assertIn("family 1", claimed[0].lower())

    def test_cr41_two_file_superseded_projection(self):
        projection = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 7, "counted in base"),
                     ("Colour lens Blue", 8, "counted in base"),
                     ("Colour lens Purple", 9, "counted in base")])],
            board=BOARD,
            extra_lines=["This roster is a projection and is superseded "
                         "by the governing roster in roster.md."])
        res, _ = self.run_stage({"roster.md": staffed(),
                                 "projection.md": projection})
        count = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(count["Audit team"]["counted_total"], 3)


class TestStep15Round1FixesShell(ShellStaging):
    """Step 15 round 1 fix round tests: manifest order, naming,
    classification, and ignored inputs."""

    def test_files_read_order_groups_before_names(self):
        # Step 15 round 1, C-F1: the files read list stands in
        # canonical manifest order, by input group first and then by
        # the path as named, in the Simple slot 10 line and in the
        # Agentic inputs_read list alike.
        res, _ = self.run_stage({
            "roster.md": staffed(),
            "zzz-step-record.md": "# Step record\n",
            "aaa-gate.md": "# Gate record\n"})
        self.assert_rollup(res, "PASS", 0)
        self.assertEqual(self.agentic(res)["inputs_read"],
                         ["roster.md", "zzz-step-record.md",
                          "aaa-gate.md"])
        supplied = [line for line in res.stdout.splitlines()
                    if line.startswith("Supplied set:")]
        self.assertTrue(supplied)
        line = supplied[0]
        positions = [line.find(name) for name in
                     ("roster.md", "zzz-step-record.md", "aaa-gate.md")]
        self.assertTrue(all(position >= 0 for position in positions))
        self.assertEqual(positions, sorted(positions))

    def test_two_namings_keep_the_completed_key_naming(self):
        # Step 15 round 1, C-F2: where two namings name one file, the
        # naming kept is the first under the completed key, group
        # first and then the path as named, whichever order the
        # operator named them in.
        self.require_product()
        root = self.stage_dir()
        first = self.write_file(root, "a-roster-copy.md", staffed())
        second = root / "b-roster-copy.md"
        os.link(first, second)
        for order in ((first, second), (second, first)):
            with self.subTest(order=[p.name for p in order]):
                res = self.invoke_paths(list(order))
                self.assert_rollup(res, "PASS", 0)
                self.assertEqual(self.agentic(res)["inputs_read"],
                                 ["a-roster-copy.md"])

    def test_roster_named_supplied_and_context_stays_supplied(self):
        # Step 15 round 1, BR-6: a roster named both as a supplied
        # file and as a context file stands in the supplied set under
        # the supplied naming; the context naming does not remove it.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root, "roster.md", staffed())
        res = self.invoke([str(roster), "--context", str(roster),
                           "--stage", "Step 99", "--runner",
                           "Fixture Auditor", "--capacity", "Auditor"])
        self.assert_rollup(res, "PASS", 0)
        self.assertIn("roster.md", self.agentic(res)["inputs_read"])

    def test_shared_basename_context_file_does_not_collide(self):
        # Step 15 round 1, BR-6: two different files sharing one
        # basename in different directories do not collide: the
        # roster named as a supplied file stands as the roster, and
        # the note named as context stands as context.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root / "one", "shared.md", staffed())
        note = self.write_file(root / "two", "shared.md",
                               "# Context\n")
        res = self.invoke([str(roster), "--context", str(note),
                           "--stage", "Step 99", "--runner",
                           "Fixture Auditor", "--capacity", "Auditor"])
        self.assert_rollup(res, "PASS", 0)

    def test_roster_sharing_basename_with_base_record_stays_supplied(self):
        # Step 15 round 1, BR-6: a roster sharing a basename with a
        # base record file in another directory stands as the roster
        # under its own supplied naming.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root / "one", "base.md", staffed())
        record = self.write_file(
            root / "two", "base.md",
            "# Tier record\n\n"
            "Pinned base: Fixture Base One, hash %s, 12345 bytes.\n"
            "Table version the base calls for: 1.0.0-fixture.\n"
            % ("0123456789abcdef" * 4))
        res = self.invoke([str(roster), "--base-record", str(record),
                           "--stage", "Step 99", "--runner",
                           "Fixture Auditor", "--capacity", "Auditor"])
        self.assert_rollup(res, "PASS", 0)

    def test_roster_not_ignored_for_name_substrings(self):
        # Step 15 round 1, BR-7: a genuine roster is not ignored for
        # substrings in its file name.
        for name in ("chat-roster.md", "prompt-roster.md",
                     "transcript-roster.md", "chatham-roster.md",
                     "promptly-roster.md", "rosterchat.md",
                     "roster.json", "roster.bin"):
            with self.subTest(name=name):
                res, _ = self.run_stage({name: staffed()})
                self.assert_rollup(res, "PASS", 0)

    def test_roster_not_ignored_for_a_prose_spawn_word(self):
        # Step 15 round 1, BR-7: a roster is not ignored whole for
        # the quoted word spawns standing in its text, in a prose
        # mention or in an export field line.
        for line in ('Note: the word "spawns" appears in this '
                     'prose.',
                     '"spawns": []'):
            with self.subTest(line=line):
                res, _ = self.run_stage(
                    {"roster.md": staffed(extra_lines=[line])})
                self.assert_rollup(res, "PASS", 0)

    def test_undecodable_file_listed_unread_only(self):
        # Step 15 round 1, C-F5: a file whose bytes are undecodable
        # stands in the unread list only, never in both lists of one
        # report.
        bad = staffed().encode("utf-8") + b"\nNote: \xff\xfe.\n"
        res, _ = self.run_stage({"roster.md": bad})
        agentic = self.agentic(res)
        self.assertNotIn("roster.md", agentic["inputs_read"])
        self.assertIn("roster.md", agentic["inputs_unread"])
        self.assertNotIn("this run read roster.md", res.stdout)


class TestStep15Round2FixesShell(ShellStaging):
    """Step 15 round 2 fix round tests: dual role classification
    and spawn export classification."""

    def test_roster_named_supplied_and_base_record_stays_supplied(self):
        # Step 15 round 2, NB-4 and C2-F6: a roster named both as a
        # supplied file and as a base record does not drop out of
        # the supplied set. Its standing is stated in the report
        # without contradiction: the run passes on it, and no line
        # states that no roster artifact stood in the supplied set.
        self.require_product()
        root = self.stage_dir()
        roster = self.write_file(root, "roster.md", staffed())
        namings = (
            ["--base-record", str(roster)],
            ["--base-record", str(roster), "--context", str(roster)],
        )
        for extra in namings:
            with self.subTest(extra=extra):
                res = self.invoke(
                    [str(roster)] + extra +
                    ["--stage", "Step 99", "--runner", "Fixture Auditor",
                     "--capacity", "Auditor"])
                self.assert_rollup(res, "PASS", 0)
                self.assertIn("roster.md",
                              self.agentic(res)["inputs_read"])
                self.assertNotIn("no roster artifact in the supplied "
                                 "set", res.stdout)

    def spawn_export_text(self, claim=False):
        # A file in the spawn export form, a JSON object carrying a
        # spawns key, whose string value carries a roster heading
        # line on its own line inside the string, and, in the claim
        # staging, one claim line inside the same string.
        note = "intro\n## Team: Audit team\n"
        if claim:
            note += "Freshness claim: family 3 held for this stage.\n"
        note += "outro"
        return '{\n  "spawns": [\n    {"note": "%s"}\n  ]\n}\n' % note

    def test_spawn_export_with_heading_in_string_is_ignored(self):
        # Step 15 round 2, NB-5: a spawn export is classified by its
        # export form, not by roster shaped strings inside its
        # values. Alone it is ignored and the run cannot start;
        # beside a passing roster it stands under ignored inputs and
        # never under inputs read; and a claim line inside its
        # string does not cap the rollup.
        self.require_product()
        root = self.stage_dir()
        export = self.write_file(root, "export.json",
                                 self.spawn_export_text())
        res = self.invoke_paths([export])
        self.assertEqual(res.returncode, 4)
        self.assertIn("Cannot start", res.stderr)
        roster = self.write_file(root, "roster.md", staffed())
        res = self.invoke_paths([roster, export])
        self.assert_rollup(res, "PASS", 0)
        agentic = self.agentic(res)
        self.assertIn("export.json", agentic["inputs_ignored"])
        self.assertNotIn("export.json", agentic["inputs_read"])
        claim_export = self.write_file(
            root, "export-claim.json", self.spawn_export_text(True))
        res = self.invoke_paths([roster, claim_export])
        self.assert_rollup(res, "PASS", 0)
        agentic = self.agentic(res)
        self.assertIn("export-claim.json", agentic["inputs_ignored"])
        self.assertNotIn("export-claim.json", agentic["inputs_read"])
