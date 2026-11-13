"""Slice 1 groups: TM-DATA-1 to TM-DATA-4, TM-SHIP-1, TM-SHIP-2.

The counting table stands at PARTIAL under S5-E42. No test, fixture, or
result in this module presents the counting table as complete, and the
scoped forms at TM-DATA-4, AC-4, and AC-8 stand as scoped.
"""

import json

from tests.support import (FIXTURES_DIR, MusterCase, roster_text, sha256_hex,
                           sid)

DATA = FIXTURES_DIR / "data"


def base_record(called_version="1.0.0-fixture", called_hash=None):
    lines = ["# Tier record", "",
             "Pinned base: Fixture Base One, hash %s, 12345 bytes."
             % ("0123456789abcdef" * 4)]
    if called_version is not None:
        lines.append("Table version the base calls for: %s." % called_version)
    if called_hash is not None:
        lines.append("Table hash the base calls for: %s." % called_hash)
    return "\n".join(lines) + "\n"


def simple_roster():
    return roster_text(
        teams=[("Audit team", None,
                [("Colour lens Red", 1, "counted in base"),
                 ("Colour lens Blue", 2, "counted in base"),
                 ("Colour lens Purple", 3, "counted in base")])],
        board=[("Board member one", 11), ("Board member two", 12),
               ("Board chair", 13)])


class TestDataShapes(MusterCase):
    """TM-DATA-1, shape invariants."""

    def test_seat_entry_carries_exactly_one_of_seven(self):
        res, _ = self.run_stage(
            {"roster.md": roster_text(teams=[(
                "Audit team", None,
                [("Seat A", 1, "counted in base"),
                 ("Seat B", 2, "over base at team level"),
                 ("Seat C", 3, "uncounted at this step"),
                 ("Seat D", 4, "board additional"),
                 ("Seat E", 5, "exempt"),
                 ("Seat F", 6, "step unit"),
                 ("Seat G", 7, "unplaced")])])})
        agentic = self.agentic(res)
        positions = [s["position"] for s in agentic["seats"]]
        self.assertEqual(len(positions), 7)
        self.assertEqual(len(set(positions)), 7)

    def test_full_identifier_session_form_counts(self):
        res, _ = self.run_stage({"roster.md": simple_roster()})
        self.assert_rollup(res, "PASS", 0)

    def test_shortened_session_identifier_never_counts(self):
        short = sid(1)[:20]
        res, _ = self.run_stage({"roster.md": roster_text(teams=[(
            "Audit team", None,
            [("Colour lens Red", short, "counted in base"),
             ("Colour lens Blue", 2, "counted in base"),
             ("Colour lens Purple", 3, "counted in base")])])})
        self.assert_report_present(res)
        self.assertNotEqual(rollup_of(res), "PASS")

    def test_placeholder_blank_fragment_never_count(self):
        for value in ("placeholder value", "", "fragment 0000"):
            with self.subTest(value=value):
                res, _ = self.run_stage({"roster.md": roster_text(teams=[(
                    "Audit team", None,
                    [("Colour lens Red", value, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])])})
                self.assert_report_present(res)
                self.assertNotEqual(rollup_of(res), "PASS")

    def test_name_form_identifier_counts_only_as_issued(self):
        text = roster_text(teams=[(
            "Audit team", None,
            [("Colour lens Red", "Fixture Name One", "counted in base"),
             ("Colour lens Blue", "Fixture Name Two", "counted in base"),
             ("Colour lens Purple", "Fixture Name Three",
              "counted in base")])])
        res, _ = self.run_stage({"roster.md": text})
        agentic = self.agentic(res)
        counts = {c["name"]: c for c in agentic["counts"]}
        self.assertEqual(counts["Audit team"]["entries"], 3)
        self.assertEqual(counts["Audit team"]["counted_total"], 3)

    def test_succession_seat_counted_once_on_second_holder(self):
        text = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            extra_lines=[
                "Seat Colour lens Red: the first holder %s was superseded; "
                "the second holder %s is the holder of the seat."
                % (sid(8), sid(1))])
        res, _ = self.run_stage({"roster.md": text})
        agentic = self.agentic(res)
        counts = {c["name"]: c for c in agentic["counts"]}
        self.assertEqual(counts["Audit team"]["counted_total"], 3)

    def test_combined_scope_is_one_seat_one_agent(self):
        res, _ = self.run_stage({"roster.md": roster_text(teams=[(
            "Design team", None,
            [("Combined scope seat", 1, "counted in base")])])})
        agentic = self.agentic(res)
        self.assertEqual(len(agentic["seats"]), 1)

    def test_board_seats_stand_apart_from_team_seats(self):
        res, _ = self.run_stage({"roster.md": simple_roster()})
        agentic = self.agentic(res)
        team_ids = {s["holder"] for s in agentic["seats"]
                    if s.get("team") == "Audit team"}
        self.assertNotIn(sid(11), team_ids)

    def test_unplaced_seat_carried_with_failure_named(self):
        text = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base")])],
            extra_lines=["Seat with no placeable role: holder %s; the "
                         "roster states no team for this seat." % sid(9)])
        res, _ = self.run_stage({"roster.md": text})
        agentic = self.agentic(res)
        self.assertTrue(agentic["uncounted_appendix"])


def rollup_of(result):
    from tests.support import rollup_word
    return rollup_word(result.stdout)


class TestCountingTableAsData(MusterCase):
    """TM-DATA-2, counting table as data."""

    def test_table_ships_as_inspectable_data_file(self):
        path = self.require_data_file("counting-table.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)

    def test_table_has_six_part_form(self):
        path = self.require_data_file("counting-table.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)
        for part in ("table_version", "team_bases", "per_step_rows",
                     "counting_positions", "carried_seats", "exempt_list",
                     "pool_families"):
            self.assertIn(part, data)

    def test_positions_part_carries_five_positions_only(self):
        path = self.require_data_file("counting-table.json")
        text = path.read_text(encoding="utf-8")
        for kind in ("step unit", "unplaced"):
            self.assertNotIn('"%s"' % kind,
                             text.split("counting_positions")[1]
                             .split("]")[0])

    def test_table_carries_no_plaid_cells(self):
        path = self.require_data_file("counting-table.json")
        self.assertNotIn("Plaid", path.read_text(encoding="utf-8"))

    def test_one_table_version_under_one_hash(self):
        path = self.require_data_file("counting-table.json")
        digest = sha256_hex(path.read_bytes())
        self.assertEqual(len(digest), 64)
        res, _ = self.run_stage({"roster.md": simple_roster()})
        self.assert_in_stdout(res, digest)

    def test_duplicate_key_table_takes_tool_fault(self):
        res = self.run_with_data_file(
            "counting-table.json", DATA / "table-duplicate-key.json")
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")
        self.assertIsNone(rollup_of(res))

    def test_nonfinite_table_takes_tool_fault(self):
        res = self.run_with_data_file(
            "counting-table.json", DATA / "table-nan.json")
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")

    def run_with_data_file(self, name, fixture_path):
        """Stage a shipped data fixture beside the entry and run.

        The staging carries the entry with its module files and its
        relative place intact, through stage_entry_tree in the support
        runner, with the fixture standing at the shipped data file name
        beside the staged entry, in the installed tree form plan
        section 3 states: the staged copy is the shipped file set the
        entry belongs to. Where no entry stands, the run cannot be
        made and the test fails on the product absence.
        """
        from tests.support import find_entry, run_entry_direct
        from tests.support import stage_entry_tree
        import shutil
        import tempfile
        from pathlib import Path
        entry = find_entry()
        if entry is None:
            self.fail("product does not exist: no command entry file "
                      "stands in the build repo or the installed tree")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        staged_entry = stage_entry_tree(entry, Path(tmp.name))
        staged_data = staged_entry.parent / name
        shutil.copyfile(fixture_path, staged_data)
        roster = Path(tmp.name) / "roster.md"
        roster.write_text(simple_roster(), encoding="utf-8")
        # The entry that runs is the staged entry in this same tree, and
        # the data file the run reads is the staged file beside it: the
        # path this helper stages and the path the run uses are the
        # same path, the staged data file in the staging tree.
        result = run_entry_direct(
            staged_entry,
            [str(roster), "--stage", "Step 99",
             "--runner", "Fixture Auditor", "--capacity", "Auditor"],
            cwd=tmp.name)
        if result.missing:
            self.fail(result.reason)
        return result


class TestTableAndBaseIdentity(MusterCase):
    """TM-DATA-3, table and base identity."""

    def run_identity(self, base_text, roster=None):
        files = {"roster.md": roster or simple_roster()}
        if base_text is not None:
            files["base.md"] = base_text
        return self.run_stage(files)[0]

    def test_keyed_base_mismatch_gives_unverifiable(self):
        other = base_record().replace("Fixture Base One", "Fixture Base Two")
        res = self.run_identity(other)
        self.assert_rollup(res, "UNVERIFIABLE", 3)

    def test_version_mismatch_gives_unverifiable_both_printed(self):
        res = self.run_identity(base_record(called_version="9.9.9-other"))
        self.assert_rollup(res, "UNVERIFIABLE", 3)
        self.assert_in_stdout(res, "9.9.9-other")

    def test_substituted_table_gives_unverifiable_both_hashes(self):
        wrong = "f" * 64
        res = self.run_identity(base_record(called_hash=wrong))
        self.assert_rollup(res, "UNVERIFIABLE", 3)
        self.assert_in_stdout(res, wrong)

    def test_no_called_for_hash_asserts_no_substitution(self):
        # No called for hash case, TM-DATA-3: no substitution detection
        # is asserted from silence and no check takes UNVERIFIABLE on
        # that ground. The version and keyed base comparisons still
        # run, and each check takes its own word on its own rule: the
        # table dependent composing checks take PASS on this complete
        # roster, and the non composing colour completeness result
        # takes NOT PROVEN, because no audit plan or round charge is
        # named in the supplied records.
        res = self.run_identity(base_record(called_hash=None))
        self.assertNotIn("substitut", res.stdout.lower().split("rollup")[0])
        self.assert_rollup(res, "PASS", 0)
        agentic = self.agentic(res)
        self.assertEqual(agentic["rollup"], "PASS")
        checks = agentic["checks"]
        kinds = {c["kind"]: c["verdict"] for c in checks}
        self.assertEqual(kinds["team minimums"], "PASS")
        self.assertEqual(kinds["distinctness"], "PASS")
        self.assertEqual(kinds["review board minimum"], "PASS")
        self.assertEqual(kinds["pool family and role"], "PASS")
        composing = [c["verdict"] for c in checks if c.get("composing")]
        self.assertTrue(composing)
        self.assertEqual(composing, ["PASS"] * len(composing))
        self.assertNotIn("UNVERIFIABLE",
                         [c["verdict"] for c in checks])
        self.assert_in_stdout(res, "Colour completeness: NOT PROVEN")

    def test_called_for_disagreement_gives_unverifiable_dependent_set(self):
        text = base_record(called_version="1.0.0-fixture") + (
            "Table version the base calls for: 2.0.0-other.\n")
        res = self.run_identity(text)
        self.assert_rollup(res, "UNVERIFIABLE", 3)
        self.assert_in_stdout(res, "2.0.0-other")

    def test_base_disagreement_no_base_applied(self):
        text = base_record() + (
            "\nPinned base: Fixture Base Two, hash %s, 999 bytes.\n"
            % ("fedcba9876543210" * 4))
        res = self.run_identity(text)
        self.assert_rollup(res, "UNVERIFIABLE", 3)

    def test_corrupt_table_takes_tool_fault_no_report(self):
        res = TestCountingTableAsData.run_with_data_file(
            self, "counting-table.json", DATA / "table-truncated.json")
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")
        self.assertIsNone(rollup_of(res))

    def test_crlf_table_hash_is_hash_of_crlf_bytes(self):
        record = json.loads((DATA / "hash-record.json").read_text())
        crlf = (DATA / "table-crlf.json").read_bytes()
        self.assertEqual(sha256_hex(crlf), record["crlf_sha256"])
        self.assertNotEqual(record["crlf_sha256"], record["lf_sha256"])
        res = TestCountingTableAsData.run_with_data_file(
            self, "counting-table.json", DATA / "table-crlf.json")
        self.assert_in_stdout(res, record["crlf_sha256"])

    def test_changing_table_file_uses_first_capture(self):
        # The table file limb of the one changing file fixture: the
        # staged counting table presents one content on its first
        # reading and a different content on any later reading in the
        # same run, through the test side ChangingFileWatcher. The
        # printed hash must be the hash of the first capture and the
        # counts must be the counts of the table parsed from that same
        # capture.
        from tests.support import (ChangingFileWatcher, find_entry,
                                   run_entry_direct, stage_entry_tree)
        import tempfile
        from pathlib import Path
        entry = find_entry()
        if entry is None:
            self.fail("product does not exist: no command entry file "
                      "stands in the build repo or the installed tree")
        first = (DATA / "table-lf.json").read_bytes()
        second_table = json.loads(first.decode("utf-8"))
        second_table["rows"] = [{"step": 99, "team": "Audit team",
                                 "minimum": 99}]
        second = json.dumps(second_table).encode("utf-8")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        staged_entry = stage_entry_tree(entry, Path(tmp.name))
        staged_table = staged_entry.parent / "counting-table.json"
        roster = Path(tmp.name) / "roster.md"
        roster.write_text(simple_roster(), encoding="utf-8")
        with ChangingFileWatcher(staged_table, first, second) as watch:
            result = run_entry_direct(
                staged_entry,
                [str(roster), "--stage", "Step 99",
                 "--runner", "Fixture Auditor", "--capacity", "Auditor"],
                cwd=tmp.name)
        if result.missing:
            self.fail(result.reason)
        self.assertTrue(watch.fired)
        self.assertEqual(staged_table.read_bytes(), second)
        self.assert_in_stdout(result, sha256_hex(first))
        self.assertNotIn(sha256_hex(second), result.stdout)
        counts = {c["name"]: c
                  for c in self.agentic(result)["counts"]}
        self.assertEqual(counts["Audit team"]["minimum"], 3)


class TestFeedTableAndPartition(MusterCase):
    """TM-DATA-4, feed table and partition, scoped.

    Scoping limit, standing with the group: this check states nothing on
    a row that stands only in the remainder, and the counting table bound
    at S5-E42 PARTIAL stands on the table while it stands.
    """

    def test_entered_rows_match_table_data_for_step_judged(self):
        path = self.require_data_file("counting-table.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = [row for row in data.get("per_step_rows", [])
                if row.get("step") == 99]
        self.assertTrue(rows)
        res, _ = self.run_stage({"roster.md": simple_roster()})
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        for row in rows:
            team = row.get("team")
            if team in counts:
                self.assertEqual(counts[team]["minimum"],
                                 row.get("minimum"))
                # The counted total limb asserts the entered row value
                # itself: the row must carry its team_count value, and
                # the printed counted total must equal that entered
                # value. No fallback to the run own counted total
                # stands here, so the limb is not vacuous for a row
                # without the key: such a row fails this assertion.
                self.assertIn("team_count", row)
                self.assertEqual(counts[team]["counted_total"],
                                 row["team_count"])

    def test_partition_sum_equals_entries_per_round(self):
        # The sum over the combined list of seven, applied to the one
        # count this fixture stage decides, equals the number of entries
        # for that count: the fixture roster carries 6 entries in all,
        # 3 team seats and 3 board seats.
        res, _ = self.run_stage({"roster.md": simple_roster()})
        agentic = self.agentic(res)
        seats = agentic["seats"]
        seven = ("counted in base", "over base at team level",
                 "uncounted at this step", "board additional", "exempt",
                 "step unit", "unplaced")
        by_position = {position: 0 for position in seven}
        for seat in seats:
            self.assertIn(seat["position"], by_position)
            by_position[seat["position"]] += 1
        self.assertEqual(sum(by_position.values()), 6)
        self.assertEqual(len(seats), 6)

    def test_build_union_column_checked_against_state_only(self):
        res, _ = self.run_stage({"roster.md": simple_roster()})
        self.assert_in_stdout(res, "not computable in a one stage run")

    def test_board_and_chair_stand_in_no_team_account(self):
        res, _ = self.run_stage({"roster.md": simple_roster()})
        agentic = self.agentic(res)
        totals = {c["name"]: c["counted_total"] for c in agentic["counts"]}
        self.assertEqual(totals.get("Audit team"), 3)


class TestShipIdentity(MusterCase):
    """TM-SHIP-1 and TM-SHIP-2."""

    def test_every_report_prints_table_and_base_identity(self):
        res, _ = self.run_stage({"roster.md": simple_roster(),
                                 "base.md": base_record()})
        for needle in ("Counting table: version", "Diagnostic catalogue: "
                       "version", "Pinned base:"):
            self.assert_in_stdout(res, needle)

    def test_catalogue_carries_one_version_printed_in_reports(self):
        path = self.require_data_file("diagnostic-catalogue.json")
        self.assertTrue(path.is_file())
        res, _ = self.run_stage({"roster.md": simple_roster()})
        self.assert_in_stdout(res, "Diagnostic catalogue: version")

    def test_catalogue_code_never_reused_across_versions(self):
        path = self.require_data_file("diagnostic-catalogue.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        codes = [row["code"] for row in data.get("rows", [])]
        self.assertEqual(len(codes), len(set(codes)))

    def test_catalogue_truncated_takes_tool_fault(self):
        res = TestCountingTableAsData.run_with_data_file(
            self, "diagnostic-catalogue.json",
            DATA / "catalogue-truncated.json")
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")

    def test_catalogue_duplicate_key_takes_tool_fault(self):
        res = TestCountingTableAsData.run_with_data_file(
            self, "diagnostic-catalogue.json",
            DATA / "catalogue-duplicate-key.json")
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")

    def test_catalogue_nonfinite_takes_tool_fault(self):
        res = TestCountingTableAsData.run_with_data_file(
            self, "diagnostic-catalogue.json",
            DATA / "catalogue-nan.json")
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")


class TestStep15Round1FixesData(MusterCase):
    """Step 15 round 1 fix round tests: identifiers, slot 4 forms,
    and the shipped counting table."""

    BOARD = [("Board member one", 11), ("Board member two", 12),
             ("Board chair", 13)]

    def roster_with_holder(self, value):
        return roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", value, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=self.BOARD)

    def test_placeholder_holder_words_never_count(self):
        # Step 15 round 1, BR-1: a placeholder holder word, and a
        # name standing alone that no record in the set issues as an
        # identifier form, never count toward a minimum.
        for value in ("TBD", "TBC", "unknown", "pending",
                      "awaiting assignment", "NA", "N/A", "Bob", "A",
                      "x"):
            with self.subTest(value=value):
                res, _ = self.run_stage(
                    {"roster.md": self.roster_with_holder(value)})
                self.assert_report_present(res)
                self.assertNotEqual(rollup_of(res), "PASS")
                counts = {c["name"]: c
                          for c in self.agentic(res)["counts"]}
                self.assertLess(counts["Audit team"]["counted_total"],
                                3)

    def test_roster_of_placeholder_holders_does_not_pass(self):
        # Step 15 round 1, BR-1: three placeholder holders together
        # count as nobody, and the run does not pass.
        text = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", "TBD", "counted in base"),
                     ("Colour lens Blue", "TBC", "counted in base"),
                     ("Colour lens Purple", "unknown",
                      "counted in base")])],
            board=self.BOARD)
        res, _ = self.run_stage({"roster.md": text})
        self.assert_report_present(res)
        self.assertNotEqual(rollup_of(res), "PASS")
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(counts["Audit team"]["counted_total"], 0)

    def test_base_disagreement_slot4_stands_in_brief_form(self):
        # Step 15 round 1, C-F3: where the records identifying the
        # base disagree, slot 4 prints the disagreement sentence, one
        # Identification sentence per distinct base, the sentence
        # that no pinned base is applied, and the called for values
        # per identification, and the Agentic form presents no base
        # as pinned.
        other = ("# Tier record\n\n"
                 "Pinned base: Fixture Base Two, hash %s, 999 bytes.\n"
                 "Table version the base calls for: 1.0.0-fixture.\n"
                 % ("fedcba9876543210" * 4))
        res, _ = self.run_stage({"roster.md": simple_roster(),
                                 "base.md": base_record(),
                                 "tier-two.md": other})
        self.assert_rollup(res, "UNVERIFIABLE", 3)
        self.assert_in_stdout(
            res, "Pinned base: disagreement in the records "
                 "identifying the base.")
        self.assert_in_stdout(
            res, "Identification: Fixture Base One, hash %s, 12345 "
                 "bytes." % ("0123456789abcdef" * 4))
        self.assert_in_stdout(
            res, "Identification: Fixture Base Two, hash %s, 999 "
                 "bytes." % ("fedcba9876543210" * 4))
        self.assert_in_stdout(res, "No pinned base is applied for "
                                   "this run.")
        self.assert_in_stdout(
            res, "Table version the base in this identification "
                 "calls for: Fixture Base One: 1.0.0-fixture.")
        agentic = self.agentic(res)
        self.assertIsNone(agentic["pinned_base_name"])
        self.assertIsNone(agentic["pinned_base_hash"])

    def test_called_for_disagreement_slot4_stands_in_brief_form(self):
        # Step 15 round 1, C-F4: where the identifying records agree
        # on the base but state two called for versions, the sentence
        # for that fact prints the disagreement sentence and one
        # Stated value sentence per stated value.
        text = base_record(called_version="1.0.0-fixture") + (
            "Table version the base calls for: 2.0.0-other.\n")
        res, _ = self.run_stage({"roster.md": simple_roster(),
                                 "base.md": text})
        self.assert_rollup(res, "UNVERIFIABLE", 3)
        self.assert_in_stdout(
            res, "Table version the base calls for: disagreement in "
                 "the records identifying the base.")
        self.assert_in_stdout(res, "Stated value: 1.0.0-fixture.")
        self.assert_in_stdout(res, "Stated value: 2.0.0-other.")

    def test_gutted_counting_table_takes_tool_fault(self):
        # Step 15 round 1, BR-4: a counting table that parses as a
        # JSON object but carries missing or wrongly typed rule data
        # is a damaged shipped file and takes the tool fault outcome.
        import tempfile
        from pathlib import Path
        shipped = json.loads(
            self.require_data_file("counting-table.json").read_text(
                encoding="utf-8"))
        variants = {}
        variants["empty object"] = {}
        no_bases = dict(shipped)
        del no_bases["team_bases"]
        variants["team_bases deleted"] = no_bases
        word_bases = dict(shipped)
        word_bases["team_bases"] = "word"
        variants["team_bases as a word"] = word_bases
        word_minimum = json.loads(json.dumps(shipped))
        word_minimum["team_bases"]["Audit team"]["Low"] = "three"
        variants["a minimum as the word three"] = word_minimum
        for label, table in variants.items():
            with self.subTest(variant=label):
                tmp = tempfile.TemporaryDirectory()
                self.addCleanup(tmp.cleanup)
                fixture = Path(tmp.name) / "table-variant.json"
                fixture.write_text(json.dumps(table), encoding="utf-8")
                res = TestCountingTableAsData.run_with_data_file(
                    self, "counting-table.json", fixture)
                self.assertEqual(res.returncode, 6)
                self.assert_in_stdout(res, "TOOL FAULT")
                self.assertIsNone(rollup_of(res))

    def test_table_position_occupied_by_directory_takes_tool_fault(self):
        # Step 15 round 1, BR-5: where the counting table position
        # beside the entry is occupied, by a directory, that position
        # governs: the run faults instead of borrowing a table from
        # another tree.
        from tests.support import (find_entry, run_entry_direct,
                                   stage_entry_tree)
        import shutil
        import tempfile
        from pathlib import Path
        entry = find_entry()
        if entry is None:
            self.fail("product does not exist: no command entry "
                      "stands in the build repo or the installed "
                      "tree")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        staged_entry = stage_entry_tree(entry, Path(tmp.name))
        (staged_entry.parent / "counting-table.json").mkdir()
        catalogue = self.require_data_file("diagnostic-catalogue.json")
        shutil.copyfile(catalogue,
                        staged_entry.parent / "diagnostic-catalogue.json")
        roster = Path(tmp.name) / "roster.md"
        roster.write_text(simple_roster(), encoding="utf-8")
        res = run_entry_direct(
            staged_entry,
            [str(roster), "--stage", "Step 99", "--runner",
             "Fixture Auditor", "--capacity", "Auditor"],
            cwd=tmp.name)
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")

    def test_env_named_tree_table_never_governs(self):
        # Step 15 round 1, BR-5: a tree named by the MUSTER_LITE_HOME
        # environment variable never supplies the counting table: its
        # altered minimum of 99 does not govern the run.
        from tests.support import (find_entry, run_entry_direct,
                                   stage_entry_tree)
        import tempfile
        from pathlib import Path
        entry = find_entry()
        if entry is None:
            self.fail("product does not exist: no command entry "
                      "stands in the build repo or the installed "
                      "tree")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        staged_entry = stage_entry_tree(entry, Path(tmp.name))
        env_tree = Path(tmp.name) / "env-tree"
        env_tree.mkdir()
        shipped = json.loads(
            self.require_data_file("counting-table.json").read_text(
                encoding="utf-8"))
        altered = json.loads(json.dumps(shipped))
        altered["team_bases"]["Audit team"]["Low"] = 99
        altered["per_step_rows"] = [
            {"minimum": 99, "step": 99, "team": "Audit team",
             "team_count": 3}]
        (env_tree / "counting-table.json").write_text(
            json.dumps(altered), encoding="utf-8")
        roster = Path(tmp.name) / "roster.md"
        roster.write_text(simple_roster(), encoding="utf-8")
        res = run_entry_direct(
            staged_entry,
            [str(roster), "--stage", "Step 99", "--runner",
             "Fixture Auditor", "--capacity", "Auditor"],
            cwd=tmp.name, env_extra={"MUSTER_LITE_HOME": str(env_tree)})
        if res.returncode == 6:
            self.assert_in_stdout(res, "TOOL FAULT")
        else:
            counts = {c["name"]: c
                      for c in self.agentic(res)["counts"]}
            self.assertEqual(counts["Audit team"]["minimum"], 3)
