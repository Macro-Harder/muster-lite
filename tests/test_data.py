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


class TestStep15Round2FixesData(MusterCase):
    """Step 15 round 2 fix round tests: placeholder phrases, data
    file validation completeness, and disagreement form order."""

    BOARD = [("Board member one", 11), ("Board member two", 12),
             ("Board chair", 13)]

    def roster_with_holder(self, value):
        return roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", value, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=self.BOARD)

    def test_placeholder_phrases_never_count(self):
        # Step 15 round 2, NB-1 and C2-F1: a placeholder stated as a
        # phrase of more than one word, or carrying ordinary sentence
        # punctuation, spacing, or repetition, never counts as a full
        # identifier. The brief at Section 5.3 governs: a placeholder
        # is not a full identifier, judged on the whole value.
        phrases = (
            # NB-1 phrases.
            "To be decided", "Pending approval", "Not yet assigned",
            "To be announced", "No holder", "No one", "Someone TBD",
            "TBD Smith", "T B D", "TBD TBD", "Unknown Person",
            "Vacant seat", "Awaiting someone", "Pending review",
            "To be confirmed later", "Not assigned yet", "Holder TBD",
            "TBD [pending]",
            # C2-F1 punctuation and spacing variants of charged
            # phrases.
            "to be determined.", "to be confirmed.",
            "to be assigned.", "awaiting assignment.",
            "awaiting  assignment", "awaiting assignment,",
            "pending assignment", "assignment pending.",
        )
        for value in phrases:
            with self.subTest(value=value):
                res, _ = self.run_stage(
                    {"roster.md": self.roster_with_holder(value)})
                self.assert_report_present(res)
                self.assertNotEqual(rollup_of(res), "PASS")
                counts = {c["name"]: c
                          for c in self.agentic(res)["counts"]}
                self.assertLess(counts["Audit team"]["counted_total"],
                                3)

    def test_full_placeholder_rosters_do_not_pass(self):
        # Step 15 round 2, NB-1: rosters whose three team seats are
        # held by placeholder phrases alone name nobody and do not
        # pass.
        rosters = (
            ("To be decided", "Pending approval", "Not yet assigned"),
            ("TBD TBD", "TBC TBC", "Unknown Unknown"),
            ("T B D", "T B C", "No one"),
        )
        roles = ("Colour lens Red", "Colour lens Blue",
                 "Colour lens Purple")
        for holders in rosters:
            with self.subTest(holders=holders):
                text = roster_text(
                    teams=[("Audit team", None,
                            [(role, holder, "counted in base")
                             for role, holder in zip(roles, holders)])],
                    board=self.BOARD)
                res, _ = self.run_stage({"roster.md": text})
                self.assert_report_present(res)
                self.assertNotEqual(rollup_of(res), "PASS")
                counts = {c["name"]: c
                          for c in self.agentic(res)["counts"]}
                self.assertEqual(
                    counts["Audit team"]["counted_total"], 0)

    def test_names_containing_placeholder_words_count(self):
        # Step 15 round 2, NB-7: a complete name of more than one
        # word that merely contains a placeholder word as one word
        # of the name stands on its own form and counts. The rule
        # judges the whole value, not a substring of it.
        for value in ("Placeholder Smith", "Fragment Jones",
                      "Pending Sutton", "Vacant Lotus", "John Pending",
                      "Fixture Name One", "Todd Bridges"):
            with self.subTest(value=value):
                res, _ = self.run_stage(
                    {"roster.md": self.roster_with_holder(value)})
                self.assert_rollup(res, "PASS", 0)
                counts = {c["name"]: c
                          for c in self.agentic(res)["counts"]}
                self.assertEqual(counts["Audit team"]["counted_total"],
                                 3)

    def staged_table_run(self, table, name="counting-table.json"):
        import tempfile
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fixture = Path(tmp.name) / "table-variant.json"
        fixture.write_text(json.dumps(table), encoding="utf-8")
        return TestCountingTableAsData.run_with_data_file(
            self, name, fixture)

    def test_counting_table_validation_covers_every_part(self):
        # Step 15 round 2, NB-3 and C2-F2: the counting table
        # validation covers every part the counting reads. A table
        # missing or mistyping any of them takes the tool fault
        # outcome at exit 6, in the shipped form and in the rows
        # form alike.
        shipped = json.loads(
            self.require_data_file("counting-table.json").read_text(
                encoding="utf-8"))
        variants = {}
        no_rows = dict(shipped)
        del no_rows["per_step_rows"]
        variants["per_step_rows deleted"] = no_rows
        no_totals = dict(shipped)
        del no_totals["step_totals"]
        variants["step_totals deleted"] = no_totals
        no_keyed = dict(shipped)
        del no_keyed["keyed_base"]
        variants["keyed_base deleted"] = no_keyed
        nb1 = dict(shipped)
        del nb1["per_step_rows"]
        nb1["team_bases"] = {}
        variants["per_step_rows deleted, empty team_bases"] = nb1
        nb2 = json.loads(json.dumps(shipped))
        nb2["per_step_rows"] = []
        nb2["team_bases"] = {}
        variants["empty per_step_rows, empty team_bases"] = nb2
        variants["rows form row with no minimum"] = {
            "table_version": "1.0.0-fixture",
            "keyed_base": shipped["keyed_base"],
            "rows": [{"step": 99, "team": "Audit team"}]}
        nb4 = json.loads(json.dumps(shipped))
        del nb4["per_step_rows"][0]["minimum"]
        nb4["team_bases"] = None
        variants["shipped row with no minimum, null team_bases"] = nb4
        for label, table in variants.items():
            with self.subTest(variant=label):
                res = self.staged_table_run(table)
                self.assertEqual(res.returncode, 6)
                self.assert_in_stdout(res, "TOOL FAULT")
                self.assertIsNone(rollup_of(res))

    def test_rows_form_table_with_minimums_still_governs(self):
        # Step 15 round 2 control for NB-3: a table in the minimal
        # rows form, its rows carrying their minimums, stands in its
        # own form and governs the run as before.
        res = TestCountingTableAsData.run_with_data_file(
            self, "counting-table.json", DATA / "table-lf.json")
        self.assert_rollup(res, "PASS", 0)

    def test_gutted_diagnostic_catalogue_takes_tool_fault(self):
        # Step 15 round 2, NB-6 and C2-F4: the diagnostic catalogue
        # stands validated on the same brief Section 6 footing as
        # the counting table. An empty object, a missing or numeric
        # version, or rows of the wrong type fault the same way.
        shipped = json.loads(
            self.require_data_file(
                "diagnostic-catalogue.json").read_text(
                encoding="utf-8"))
        variants = {}
        variants["empty object"] = {}
        no_version = dict(shipped)
        del no_version["catalogue_version"]
        variants["version missing"] = no_version
        numeric = dict(shipped)
        numeric["catalogue_version"] = 100
        variants["version numeric"] = numeric
        word_rows = dict(shipped)
        word_rows["rows"] = "word"
        variants["rows as a word"] = word_rows
        for label, catalogue in variants.items():
            with self.subTest(variant=label):
                res = self.staged_table_run(
                    catalogue, name="diagnostic-catalogue.json")
                self.assertEqual(res.returncode, 6)
                self.assert_in_stdout(res, "TOOL FAULT")
                self.assertIsNone(rollup_of(res))


    def test_identification_sentences_follow_manifest_order(self):
        # Step 15 round 2, C2-F3: Identification sentences print in
        # the canonical manifest order of the records that identify
        # each base, so the same set named in any order gives a byte
        # identical report.
        one = ("# Tier record\n\n"
               "Pinned base: Fixture Base One, hash %s, 12345 bytes.\n"
               "Table version the base calls for: 1.0.0-fixture.\n"
               % ("0123456789abcdef" * 4))
        two = ("# Tier record\n\n"
               "Pinned base: Fixture Base Two, hash %s, 999 bytes.\n"
               "Table version the base calls for: 1.0.0-fixture.\n"
               % ("fedcba9876543210" * 4))
        first, _ = self.run_stage({"roster.md": simple_roster(),
                                   "aaa-tier.md": one,
                                   "zzz-tier.md": two})
        second, _ = self.run_stage({"roster.md": simple_roster(),
                                    "zzz-tier.md": two,
                                    "aaa-tier.md": one})
        for res in (first, second):
            self.assert_rollup(res, "UNVERIFIABLE", 3)
            one_at = res.stdout.find(
                "Identification: Fixture Base One")
            two_at = res.stdout.find(
                "Identification: Fixture Base Two")
            self.assertTrue(0 <= one_at < two_at)
        self.assertEqual(first.stdout, second.stdout)

    def test_stated_value_sentences_follow_manifest_order(self):
        # Step 15 round 2, C2-F3: Stated value sentences in the
        # called for disagreement form print in the canonical
        # manifest order of the records that state them, so the same
        # set named in any order gives a byte identical report.
        aaa = ("# Tier record\n\n"
               "Pinned base: Fixture Base One, hash %s, 12345 bytes.\n"
               "Table version the base calls for: 2.0.0-aaa.\n"
               % ("0123456789abcdef" * 4))
        zzz = ("# Tier record\n\n"
               "Pinned base: Fixture Base One, hash %s, 12345 bytes.\n"
               "Table version the base calls for: 3.0.0-zzz.\n"
               % ("0123456789abcdef" * 4))
        first, _ = self.run_stage({"roster.md": simple_roster(),
                                   "aaa-tier.md": aaa,
                                   "zzz-tier.md": zzz})
        second, _ = self.run_stage({"roster.md": simple_roster(),
                                    "zzz-tier.md": zzz,
                                    "aaa-tier.md": aaa})
        for res in (first, second):
            self.assert_rollup(res, "UNVERIFIABLE", 3)
            aaa_at = res.stdout.find("Stated value: 2.0.0-aaa.")
            zzz_at = res.stdout.find("Stated value: 3.0.0-zzz.")
            self.assertTrue(0 <= aaa_at < zzz_at)
        self.assertEqual(first.stdout, second.stdout)


class TestStep15Round2PrinciplesCureData(MusterCase):
    """Step 15 round 2 principles cure tests: the probed and widened
    placeholder forms pinned in the suite, and the closed phrase
    rule for complete names built from former vocabulary words.

    The pinning tests in this class stand written after the Family 1
    widening they pin. They are a cure act for a test first breach,
    and no record presents them as having preceded the widening.
    The Chosen One class test and the removed words test in this
    class stand written before the product change that cures them,
    in test first form for that change.
    """

    BOARD = [("Board member one", 11), ("Board member two", 12),
             ("Board chair", 13)]

    def roster_with_holder(self, value):
        return roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", value, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=self.BOARD)

    def assert_holder_refuses(self, value):
        res, _ = self.run_stage(
            {"roster.md": self.roster_with_holder(value)})
        self.assert_report_present(res)
        self.assertNotEqual(rollup_of(res), "PASS")
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertLess(counts["Audit team"]["counted_total"], 3)

    def assert_holder_counts(self, value):
        res, _ = self.run_stage(
            {"roster.md": self.roster_with_holder(value)})
        self.assert_rollup(res, "PASS", 0)
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(counts["Audit team"]["counted_total"], 3)

    def test_probed_variants_never_count(self):
        # Every probed form the round 2 fix register Family 1 entry
        # records: the six forms that refused on probing, and the
        # three forms that still counted and prompted the widening.
        for value in ("Awaiting confirmation", "Decision pending",
                      "Unassigned seat", "Seat vacant",
                      "To be appointed", "Assignee unknown",
                      "Pending appointment", "Not yet known",
                      "To be filled"):
            with self.subTest(value=value):
                self.assert_holder_refuses(value)

    def test_nine_widened_words_in_recorded_phrase_forms_never_count(self):
        # One recorded phrase form for each of the nine widened
        # words: appointment, appointee, designated, designation,
        # known, filled, fill, selected, and chosen.
        for value in ("Pending appointment", "Unknown appointee",
                      "To be designated", "Designation pending",
                      "Not yet known", "To be filled", "Seat to fill",
                      "To be selected", "To be chosen"):
            with self.subTest(value=value):
                self.assert_holder_refuses(value)

    def test_added_closed_phrases_never_count(self):
        # Phrases added to the closed phrase set by the principles
        # cure act itself, each a placeholder statement in its own
        # form, pinned here before the phrase set carried them.
        for value in ("Determination pending", "Name unknown",
                      "Still pending", "Unfilled seat",
                      "Unnamed holder"):
            with self.subTest(value=value):
                self.assert_holder_refuses(value)

    def test_chosen_one_class_counts(self):
        # A complete name in the form of a widened word followed by
        # the word One, whose whole value stands in no placeholder
        # phrase, counts on its own form under the brief Section
        # 5.3 definition, as Placeholder Smith and Fragment Jones
        # count. Chosen One is the named member of the class.
        for value in ("Chosen One", "Selected One", "Known One",
                      "Designated One"):
            with self.subTest(value=value):
                self.assert_holder_counts(value)

    def test_removed_vocabulary_words_no_longer_refuse_on_their_own(self):
        # The six former vocabulary words removed as free standing
        # words by the cure (an, anybody, anyone, nobody, somebody,
        # and the) no longer refuse a complete name built with the
        # word One, a form that stands in no placeholder phrase.
        for value in ("The One", "An One", "Anybody One",
                      "Anyone One", "Somebody One", "Nobody One"):
            with self.subTest(value=value):
                self.assert_holder_counts(value)


class TestStep15Round3FixesData(MusterCase):
    """Step 15 round 3 fix round tests: the placeholder battery,
    context file governing statements, duplicate counting table
    rows, and shipped data content validation."""

    BOARD = [("Board member one", 11), ("Board member two", 12),
             ("Board chair", 13)]

    def roster_with_holder(self, value):
        return roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", value, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=self.BOARD)

    def assert_holder_refuses(self, value):
        res, _ = self.run_stage(
            {"roster.md": self.roster_with_holder(value)})
        self.assert_report_present(res)
        self.assertNotEqual(rollup_of(res), "PASS")
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertLess(counts["Audit team"]["counted_total"], 3)

    def test_breaker_battery_placeholder_phrases_never_count(self):
        # Step 15 round 3, R3-NB-1: the Breaker paper battery, its
        # two groups of phrases standing outside the round 2 closed
        # phrase set, each a placeholder on the face of the whole
        # value under brief Section 5.3, never counts.
        phrases = (
            # Group 1, ordinary English dress of a charged or set
            # phrase.
            "Awaiting the assignment", "To be finally decided",
            "Pending final approval", "Not yet been assigned",
            "To be decided later", "To be announced later",
            "To be filled later", "Seat unfilled",
            "Seat to be filled", "Not yet appointed",
            "Not yet confirmed", "Yet to be assigned",
            "Holder to be determined", "Name to be announced",
            "Assignment to be confirmed", "Awaiting a decision",
            "Appointment pending", "Confirmation pending",
            # Group 2, fresh noun and act words.
            "Holder unknown", "Identity unknown", "Position vacant",
            "Vacant position", "Unassigned holder", "No assignee",
            "Empty seat", "Assignee to be named",
            "Pending a decision", "Holder pending", "Role unfilled",
            "Awaiting allocation", "Pending allocation",
            "To be allocated",
        )
        self.assertEqual(len(phrases), 32)
        for value in phrases:
            with self.subTest(value=value):
                self.assert_holder_refuses(value)

    def test_breaker_battery_full_rosters_do_not_pass(self):
        # Step 15 round 3, R3-NB-1: the Breaker paper two full
        # rosters built from battery phrases alone name nobody and
        # do not pass.
        roles = ("Colour lens Red", "Colour lens Blue",
                 "Colour lens Purple")
        rosters = (
            ("Holder unknown", "Seat unfilled", "To be decided later"),
            ("Awaiting the assignment", "Pending final approval",
             "Not yet appointed"),
        )
        for holders in rosters:
            with self.subTest(holders=holders):
                text = roster_text(
                    teams=[("Audit team", None,
                            [(role, holder, "counted in base")
                             for role, holder in zip(roles, holders)])],
                    board=self.BOARD)
                res, _ = self.run_stage({"roster.md": text})
                self.assert_report_present(res)
                self.assertNotEqual(rollup_of(res), "PASS")
                counts = {c["name"]: c
                          for c in self.agentic(res)["counts"]}
                self.assertEqual(
                    counts["Audit team"]["counted_total"], 0)

    def test_context_file_base_and_called_for_statements_do_not_govern(self):
        # Step 15 round 3, C3-F2: a context file states freshness
        # facts only. Its base identification and called for values
        # move neither slot 4, nor the comparison, nor the rollup.
        two = ("Pinned base: Fixture Base Two, hash %s, 999 bytes.\n"
               % ("fedcba9876543210" * 4))
        # A context only base statement does not rewrite slot 4:
        # the run stands on the keyed base and passes.
        res, _ = self.run_stage(
            {"roster.md": simple_roster(),
             "ctx.md": "# Context\n\n" + two},
            context=["ctx.md"])
        self.assert_rollup(res, "PASS", 0)
        self.assertEqual(self.agentic(res)["pinned_base_name"],
                         "Fixture Base One")
        # A context called for version does not stand in slot 4
        # and does not enter the comparison.
        res, _ = self.run_stage(
            {"roster.md": simple_roster(),
             "base.md": base_record(),
             "ctx.md": "# Context\n\nTable version the base calls "
                       "for: 9.9.9-ctx.\n"},
            context=["ctx.md"])
        self.assert_rollup(res, "PASS", 0)
        self.assertNotIn("9.9.9-ctx", res.stdout)
        self.assert_in_stdout(
            res, "Table version the base calls for: 1.0.0-fixture.")
        # A context identification does not enter the distinct
        # base list: the tier record identification governs alone.
        tier_two = base_record().replace(
            "Fixture Base One, hash %s, 12345"
            % ("0123456789abcdef" * 4),
            "Fixture Base Two, hash %s, 999"
            % ("fedcba9876543210" * 4))
        res, _ = self.run_stage(
            {"roster.md": simple_roster(),
             "tier.md": tier_two,
             "ctx.md": "# Context\n\n" + (
                 "Pinned base: Fixture Base One, hash %s, 12345 "
                 "bytes.\n" % ("0123456789abcdef" * 4))},
            context=["ctx.md"])
        self.assertEqual(self.agentic(res)["pinned_base_name"],
                         "Fixture Base Two")
        self.assertNotIn("disagreement in the records identifying "
                         "the base", res.stdout)

    def staged_table_run(self, table, name="counting-table.json"):
        import tempfile
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fixture = Path(tmp.name) / "table-variant.json"
        fixture.write_text(json.dumps(table), encoding="utf-8")
        return TestCountingTableAsData.run_with_data_file(
            self, name, fixture)

    def test_duplicate_rows_in_counting_table_take_tool_fault(self):
        # Step 15 round 3, R3-NB-3: two rows for one step and team
        # in any of the counting table row parts take the TOOL
        # FAULT outcome, in both row orders, as duplicate keys do.
        shipped = json.loads(
            self.require_data_file("counting-table.json").read_text(
                encoding="utf-8"))
        row3 = {"minimum": 3, "step": 99, "team": "Audit team",
                "team_count": 3}
        row1 = {"minimum": 1, "step": 99, "team": "Audit team",
                "team_count": 3}
        variants = {}
        first = json.loads(json.dumps(shipped))
        first["per_step_rows"] = [row3, row1]
        variants["per_step_rows minimum 3 then 1"] = first
        second = json.loads(json.dumps(shipped))
        second["per_step_rows"] = [row1, row3]
        variants["per_step_rows minimum 1 then 3"] = second
        variants["rows form duplicate rows"] = {
            "table_version": "1.0.0-fixture",
            "keyed_base": shipped["keyed_base"],
            "rows": [row3, row1]}
        for label, table in variants.items():
            with self.subTest(variant=label):
                res = self.staged_table_run(table)
                self.assertEqual(res.returncode, 6)
                self.assert_in_stdout(res, "TOOL FAULT")
                self.assertIsNone(rollup_of(res))

    def test_counting_table_list_contents_validated(self):
        # Step 15 round 3, R3-NB-4 and C3-F6: the counting table
        # list parts stand validated in content as in form. An
        # empty list, a nonsense counting position, or a wrong
        # kind value inside a list takes the TOOL FAULT outcome.
        shipped = json.loads(
            self.require_data_file("counting-table.json").read_text(
                encoding="utf-8"))
        variants = {}
        for part in ("counting_positions", "carried_seats",
                     "exempt_list", "pool_families"):
            table = json.loads(json.dumps(shipped))
            table[part] = []
            variants["%s empty" % part] = table
        table = json.loads(json.dumps(shipped))
        table["counting_positions"] = ["counted in base"]
        variants["counting_positions emptied in kind"] = table
        table = json.loads(json.dumps(shipped))
        table["counting_positions"] = ["nonsense", "words", "here",
                                       "more", "junk"]
        variants["counting_positions nonsense"] = table
        table = json.loads(json.dumps(shipped))
        table["carried_seats"] = [123, True]
        variants["carried_seats wrong kind values"] = table
        table = json.loads(json.dumps(shipped))
        table["exempt_list"] = [{"kind": "object inside list"}]
        variants["exempt_list object inside list"] = table
        table = json.loads(json.dumps(shipped))
        table["pool_families"] = [None, 7]
        variants["pool_families wrong kind values"] = table
        for label, table in variants.items():
            with self.subTest(variant=label):
                res = self.staged_table_run(table)
                self.assertEqual(res.returncode, 6)
                self.assert_in_stdout(res, "TOOL FAULT")
                self.assertIsNone(rollup_of(res))

    def test_catalogue_contents_validated(self):
        # Step 15 round 3, R3-NB-4 and C3-F6: catalogue codes stand
        # unique and rows complete in kind. A duplicated code, a
        # code only row, and a one row catalogue take the TOOL
        # FAULT outcome.
        shipped = json.loads(
            self.require_data_file(
                "diagnostic-catalogue.json").read_text(
                encoding="utf-8"))
        variants = {}
        duplicate = json.loads(json.dumps(shipped))
        duplicate["rows"][1]["code"] = duplicate["rows"][0]["code"]
        variants["duplicated catalogue code"] = duplicate
        code_only = json.loads(json.dumps(shipped))
        code_only["rows"][0] = {"code": "ML-01"}
        variants["code only catalogue row"] = code_only
        one_row = json.loads(json.dumps(shipped))
        one_row["rows"] = one_row["rows"][:1]
        variants["one row catalogue"] = one_row
        for label, catalogue in variants.items():
            with self.subTest(variant=label):
                res = self.staged_table_run(
                    catalogue, name="diagnostic-catalogue.json")
                self.assertEqual(res.returncode, 6)
                self.assert_in_stdout(res, "TOOL FAULT")
                self.assertIsNone(rollup_of(res))


class TestStep15Round4FixesData(MusterCase):
    """Step 15 round 4 fix round tests: label holders, the general
    context rule, the fragment label form as written, and duplicate
    counting table rows across the two row parts."""

    BOARD = [("Board member one", 11), ("Board member two", 12),
             ("Board chair", 13)]

    def roster_with_holder(self, value):
        return roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", value, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=self.BOARD)

    def assert_holder_refuses(self, value):
        res, _ = self.run_stage(
            {"roster.md": self.roster_with_holder(value)})
        self.assert_report_present(res)
        self.assertNotEqual(rollup_of(res), "PASS")
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertLess(counts["Audit team"]["counted_total"], 3)

    def assert_holder_counts(self, value):
        res, _ = self.run_stage(
            {"roster.md": self.roster_with_holder(value)})
        self.assert_rollup(res, "PASS", 0)
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(counts["Audit team"]["counted_total"], 3)

    def test_label_holders_never_count(self):
        # Step 15 round 4, R4-NB-3: a value standing as a slot label
        # rather than an issued identifier never counts as a full
        # identifier. The staged label forms are a single letter and
        # a digit, Seat and a digit, and Holder and a digit, with
        # the further members of their class: a multi digit number
        # after the label, and label tokens standing together with
        # single letters and digits and no name word at all.
        for value in ("A 1", "B 2", "Z 9", "A 12", "Seat 1",
                      "Seat 2", "Seat 12", "Holder 1", "Holder 3",
                      "Holder 007", "Seat A 1"):
            with self.subTest(value=value):
                self.assert_holder_refuses(value)

    def test_label_holder_full_rosters_do_not_pass(self):
        # Step 15 round 4, R4-NB-3: full rosters held by label
        # values alone name nobody and do not pass, and one label
        # value beside two session identifiers does not count.
        roles = ("Colour lens Red", "Colour lens Blue",
                 "Colour lens Purple")
        rosters = (
            ("A 1", "B 2", "C 3"),
            ("Seat 1", "Seat 2", "Seat 3"),
            ("Holder 1", "Holder 2", "Holder 3"),
        )
        for holders in rosters:
            with self.subTest(holders=holders):
                text = roster_text(
                    teams=[("Audit team", None,
                            [(role, holder, "counted in base")
                             for role, holder in zip(roles, holders)])],
                    board=self.BOARD)
                res, _ = self.run_stage({"roster.md": text})
                self.assert_report_present(res)
                self.assertNotEqual(rollup_of(res), "PASS")
                counts = {c["name"]: c
                          for c in self.agentic(res)["counts"]}
                self.assertEqual(
                    counts["Audit team"]["counted_total"], 0)
        self.assert_holder_refuses("A 1")

    def test_genuine_names_still_count_beside_label_rule(self):
        # Control for R4-NB-3: a complete name in the issued name
        # form, and a name carrying a label word as one word of a
        # complete name, stand in no label form and keep counting.
        for value in ("Fixture Name One", "Holder Smith",
                      "Seat Jones"):
            with self.subTest(value=value):
                self.assert_holder_counts(value)

    def test_fragment_label_multi_letter_forms_never_count(self):
        # Step 15 round 4, R4-NB-1: the fragment label form is
        # judged on the value components as written, before any
        # joining normalisation. Fragment followed by single
        # letters in any count stands in the fragment label form
        # and refuses, as the single component forms already do.
        for value in ("Fragment A B", "Fragment A B C",
                      "Fragment A B C D", "fragment a b"):
            with self.subTest(value=value):
                self.assert_holder_refuses(value)

    def test_fragment_label_single_component_forms_still_refuse(self):
        # R4-NB-1 controls: the single component fragment forms
        # that refused in every round keep refusing.
        for value in ("Fragment A", "fragment b", "Fragment 7",
                      "Fragment 12", "fragment 0000", "Fragment A 0",
                      "Fragment 0 A"):
            with self.subTest(value=value):
                self.assert_holder_refuses(value)

    def test_fragment_label_full_roster_does_not_pass(self):
        # R4-NB-1: a full roster held by fragment labels names
        # nobody and does not pass.
        roles = ("Colour lens Red", "Colour lens Blue",
                 "Colour lens Purple")
        holders = ("Fragment A B", "Fragment C D", "Fragment E F")
        text = roster_text(
            teams=[("Audit team", None,
                    [(role, holder, "counted in base")
                     for role, holder in zip(roles, holders)])],
            board=self.BOARD)
        res, _ = self.run_stage({"roster.md": text})
        self.assert_report_present(res)
        self.assertNotEqual(rollup_of(res), "PASS")
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(counts["Audit team"]["counted_total"], 0)

    def test_names_outside_fragment_label_form_still_count(self):
        # R4-NB-1 controls: genuine names caught by neither form
        # keep counting. Fragment AB stands as the Fragment Jones
        # shape, one token with letters beside the word fragment,
        # and counts as a complete name on its own form.
        for value in ("Fragment Jones", "Fragment AB",
                      "Fixture Name One"):
            with self.subTest(value=value):
                self.assert_holder_counts(value)

    def run_with_context(self, roster, context_text):
        return self.run_stage(
            {"roster.md": roster, "ctx.md": context_text},
            context=["ctx.md"])[0]

    def staged_table_run(self, table, name="counting-table.json"):
        import tempfile
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fixture = Path(tmp.name) / "table-variant.json"
        fixture.write_text(json.dumps(table), encoding="utf-8")
        return TestCountingTableAsData.run_with_data_file(
            self, name, fixture)

    def test_duplicate_rows_across_table_parts_take_tool_fault(self):
        # Step 15 round 4, R4-NB-5 and C4-F3: the two row parts of
        # the counting table are validated as one row set. A step
        # and team standing in both per_step_rows and rows takes
        # the TOOL FAULT outcome, as duplicates within a part
        # already do, whichever minimum each part states and also
        # where both parts state the same minimum.
        shipped = json.loads(
            self.require_data_file("counting-table.json").read_text(
                encoding="utf-8"))
        row3 = {"minimum": 3, "step": 99, "team": "Audit team",
                "team_count": 3}
        row1 = {"minimum": 1, "step": 99, "team": "Audit team",
                "team_count": 3}
        variants = {}
        first = json.loads(json.dumps(shipped))
        first["rows"] = [row1]
        variants["per_step_rows 3, rows 1"] = first
        second = json.loads(json.dumps(shipped))
        second["per_step_rows"] = [row1]
        second["rows"] = [row3]
        variants["per_step_rows 1, rows 3"] = second
        third = json.loads(json.dumps(shipped))
        third["per_step_rows"] = [row3]
        third["rows"] = [row3]
        variants["same minimum in both parts"] = third
        for label, table in variants.items():
            with self.subTest(variant=label):
                res = self.staged_table_run(table)
                self.assertEqual(res.returncode, 6)
                self.assert_in_stdout(res, "TOOL FAULT")
                self.assertIsNone(rollup_of(res))

    def test_distinct_rows_across_table_parts_still_govern(self):
        # Control for R4-NB-5: a rows part row for a step and team
        # that stands in no other part is no duplicate, and the
        # table stands and governs as before.
        shipped = json.loads(
            self.require_data_file("counting-table.json").read_text(
                encoding="utf-8"))
        table = json.loads(json.dumps(shipped))
        table["rows"] = [{"minimum": 1, "step": 98,
                          "team": "Audit team", "team_count": 3}]
        res = self.staged_table_run(table)
        self.assert_rollup(res, "PASS", 0)

    def test_context_tier_statement_does_not_govern(self):
        # Step 15 round 4, R4-NB-2 and C4-F2: a context file states
        # freshness facts only. Its Tier applied statement supplies
        # no tier: the run stands as it stands with no context file,
        # tier applied not proven and the Imagination team judged
        # at the standing figure.
        roster = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")]),
                   ("Imagination team", None,
                    [("Imagineer Red", 4, "counted in base"),
                     ("Imagineer Blue", 5, "counted in base"),
                     ("Imagineer Purple", 6, "counted in base")])],
            board=self.BOARD).replace(". Tier: Low.", ".")
        control, _ = self.run_stage({"roster.md": roster})
        self.assert_rollup(control, "PASS", 0)
        res = self.run_with_context(
            roster, "# Context\n\nTier applied: High.\n")
        self.assert_rollup(res, "PASS", 0)
        self.assertEqual(self.agentic(res)["tier_applied"],
                         "not proven from the supplied records")
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(counts["Imagination team"]["minimum"], 2)

    def test_context_board_statements_do_not_govern(self):
        # R4-NB-2 and C4-F2: a Board chair line and board member
        # lines in a context file name no holder for the stage
        # judged and complete no review board.
        short_board = [("Board member one", 11),
                       ("Board member two", 12)]
        roster = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=short_board)
        control, _ = self.run_stage({"roster.md": roster})
        self.assert_rollup(control, "FAIL", 1)
        res = self.run_with_context(
            roster, "# Context\n\nBoard chair: holder %s.\n"
                    % sid(13))
        self.assert_rollup(res, "FAIL", 1)
        one_board = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=[("Board member one", 11)])
        res = self.run_with_context(
            one_board,
            "# Context\n\n- Member 1: holder session %s.\n"
            "Holder: review board member 2, session %s.\n"
            % (sid(12), sid(13)))
        self.assert_rollup(res, "FAIL", 1)

    def test_context_chosen_size_statement_does_not_govern(self):
        # R4-NB-2 and C4-F2: a chosen size statement in a context
        # file chooses no size. The banded team stands NOT PROVEN
        # for its unstated chosen size, as it stands alone.
        roster = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")]),
                   ("Pre plan research team", None,
                    [("Researcher Red", 21, "counted in base"),
                     ("Researcher Blue", 22, "counted in base"),
                     ("Researcher Purple", 23, "counted in base")])],
            board=self.BOARD)
        control, _ = self.run_stage({"roster.md": roster})
        self.assert_rollup(control, "NOT PROVEN", 2)
        for size in ("3", "10"):
            with self.subTest(size=size):
                res = self.run_with_context(
                    roster, "# Context\n\nChosen size for the Pre "
                            "plan research team is %s.\n" % size)
                self.assert_rollup(res, "NOT PROVEN", 2)

    def test_context_defective_and_exempt_statements_do_not_govern(self):
        # R4-NB-2 and C4-F2: a defective roster statement and the
        # two exempt proofs in a context file move no verdict. The
        # passing roster stays PASS beside the defective statement,
        # and the exempt position seat stays counted in the open
        # beside the context proofs, as it stands alone.
        res = self.run_with_context(
            simple_roster(),
            "# Context\n\nThis roster is proven defective as a "
            "record and no other record speaks to the true "
            "staffing.\n")
        self.assert_rollup(res, "PASS", 0)
        roster = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "exempt")])],
            board=self.BOARD)
        control, _ = self.run_stage({"roster.md": roster})
        self.assert_rollup(control, "PASS", 0)
        res = self.run_with_context(
            roster,
            "# Context\n\nExempt entry: Colour lens Purple, holder "
            "%s, exempt class fixers in defect and fix loops.\n"
            "Exemption basis for the Colour lens Purple seat: the "
            "fixer repaired the round it is exempt from.\n"
            % sid(3))
        self.assert_rollup(res, "PASS", 0)
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(counts["Audit team"]["counted_total"], 3)

    def test_context_claim_statements_do_not_govern(self):
        # R4-NB-2 and C4-F2: claim statements in a context file are
        # not claims of the run. A freshness claim, a combined scope
        # claim, and an artefact proven claim in a context file move
        # no verdict, and a staffing claim in one prints no claim
        # disagreement.
        for line in (
                "Freshness claim: family 3 held for this stage.",
                "Report text claim: a combined scope is claimed "
                "for this stage.",
                "Claim: the Audit team is artefact proven for this "
                "stage.",
                "Stage register text: the three audit passes are "
                "members of the Audit team."):
            with self.subTest(line=line):
                res = self.run_with_context(
                    simple_roster(), "# Context\n\n%s\n" % line)
                self.assert_rollup(res, "PASS", 0)
                self.assertNotIn("claim disagreement", res.stdout)

    def test_context_printed_result_statements_do_not_govern(self):
        # R4-NB-2 and C4-F2, the printed result kinds: an Audit plan
        # line, a Captain JP invocation line, seat total statements,
        # a closure holder line, and a lost spawn line in a context
        # file move no printed result and no flag.
        res = self.run_with_context(
            simple_roster(),
            "# Context\n\nAudit plan: colours Red, Blue and "
            "Purple.\n")
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(
            res, "Colour completeness: NOT PROVEN. No audit plan "
                 "or round charge is named")
        roster = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=self.BOARD,
            claim_lines=["Stage claim: this stage ran at a reduced "
                         "tier."])
        res = self.run_stage(
            {"roster.md": roster,
             "tier.md": "# Tier record\n\nTier applied: Low.\n",
             "ctx.md": "# Context\n\nCaptain JP invocation record "
                       "stands for this stage.\n"},
            context=["ctx.md"])[0]
        self.assert_in_stdout(res, "FM-9")
        res = self.run_with_context(
            simple_roster(),
            "# Context\n\nThe context states 5 seats for this "
            "stage. The context states 4 seats for this stage.\n"
            "Closure holder: holder %s.\n"
            "A lost spawn stands declared in this context.\n"
            % sid(41))
        self.assert_rollup(res, "PASS", 0)
        self.assertNotIn("completeness difference", res.stdout)
        self.assertEqual(self.agentic(res)["uncounted_appendix"], [])
        self.assertNotIn("Declared lost spawns", res.stdout)

    def test_context_freshness_entries_still_reach_freshness(self):
        # Control for the general context rule: holding entries in
        # a context file are the freshness facts the brief assigns
        # to context files, and they still reach the freshness
        # checks after the cure.
        roster = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=self.BOARD,
            extra_lines=["Re auditor seat for Round 1: holder %s."
                         % sid(1)],
            claim_lines=["Freshness claim: family 1 held for this "
                         "stage."])
        res = self.run_with_context(
            roster, "# Context\n\nHolding: fixer in Round 1, holder "
                    "%s.\n" % sid(1))
        self.assert_rollup(res, "FAIL", 1)
