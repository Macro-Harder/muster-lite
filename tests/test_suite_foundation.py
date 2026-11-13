"""Step 13 suite foundation groups: TM-TEST-1, TM-TEST-2, TM-TEST-3,
plus the counting table generation determinism charge at plan section 3
and the Python floor at plan sections 1 and 8.
"""

import json

from tests.support import FIXTURES_DIR, MusterCase, roster_text, sid

BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]


REGRESSION_CASE_IDS = (
    "staffed-roster",
    "staffed-roster-without-two-facts",
    "passes-as-members",
    "panel-simulation",
    "grouped-papers",
    "roster-entry-no-spawn-record",
    "missing-records",
    "mutation-coordinator-as-member",
    "mutation-two-seats-one-agent",
    "shared-product-notes",
)


def load_cases():
    """Load the regression index inside a test, never at import time.

    A corrupt index is converted by the caller into a failure inside
    the test, so collection holds the same method count and no module
    becomes a loader error.
    """
    return json.loads(
        (FIXTURES_DIR / "regression" / "index.json").read_text())["cases"]


class TestRegressionSet(MusterCase):
    """TM-TEST-1, regression set classification, fixture by fixture."""

    def run_case(self, case_id):
        try:
            cases = load_cases()
        except (OSError, ValueError) as exc:
            self.fail("regression index cannot be read as JSON: %s"
                      % exc)
        case = [entry for entry in cases if entry["id"] == case_id]
        if not case:
            self.fail("regression case stands missing from the index: "
                      "%s" % case_id)
        case = case[0]
        res, _ = self.run_stage(case["files"], stage=case["stage"])
        if case["rollup"] is not None:
            self.assert_rollup(res, case["rollup"], case["exit"])
        for needle in case["needles"]:
            self.assertIn(needle.lower(), res.stdout.lower())


def _make_case_test(case_id):
    def test(self):
        self.run_case(case_id)
    return test


for _case_id in REGRESSION_CASE_IDS:
    setattr(TestRegressionSet,
            "test_regression_%s" % _case_id.replace("-", "_"),
            _make_case_test(_case_id))


class TestHonestShapes(MusterCase):
    """TM-TEST-2, honest shapes, no false FAIL."""

    def honest(self, extra_lines=(), teams=None, **kw):
        teams = teams or [("Audit team", None,
                           [("Colour lens Red", 1, "counted in base"),
                            ("Colour lens Blue", 2, "counted in base"),
                            ("Colour lens Purple", 3,
                             "counted in base")])]
        return self.run_stage({"roster.md": roster_text(
            teams=teams, board=BOARD, extra_lines=list(extra_lines),
            **kw)})[0]

    def assert_no_false_fail(self, res):
        # Beside the no false FAIL assertion, a report stands in the
        # output: the report heading stands and a rollup word stands,
        # so the assertion cannot hold on empty output.
        self.assert_report_present(res)
        from tests.support import rollup_word
        self.assertNotEqual(rollup_word(res.stdout), "FAIL")

    def test_per_round_reseating_with_distinct_holders(self):
        teams = [("Audit team", "Round 1",
                  [("Colour lens Red", 1, "counted in base"),
                   ("Colour lens Blue", 2, "counted in base"),
                   ("Colour lens Purple", 3, "counted in base")]),
                 ("Audit team", "Round 2",
                  [("Colour lens Red", 4, "counted in base"),
                   ("Colour lens Blue", 5, "counted in base"),
                   ("Colour lens Purple", 6, "counted in base")])]
        self.assert_no_false_fail(self.honest(teams=teams))

    def test_declared_lost_spawn_reported_in_recorded_form(self):
        res = self.honest(extra_lines=[
            "Declared lost spawn: the spawn for Colour lens Purple was "
            "declared lost in the step record, dated 2026-11-01, source "
            "the step record."])
        self.assert_no_false_fail(res)
        self.assert_in_stdout(res, "2026-11-01")

    def test_uncounted_waste_spawns_named_as_waste(self):
        res = self.honest(extra_lines=[
            "Waste spawn: holder %s, spun and uncounted, named as waste "
            "in this record." % sid(31)])
        self.assert_no_false_fail(res)

    def test_superseded_projections_labelled_as_projections(self):
        res = self.honest(extra_lines=[
            "A projected roster stands in this record labelled as a "
            "projection and superseded by the roster above."])
        self.assert_no_false_fail(res)

    def test_suspension_recorded_with_release_and_lift(self):
        res = self.honest(extra_lines=[
            "A suspension stands recorded with its release condition, "
            "and its lift stands recorded after it."])
        self.assert_no_false_fail(res)

    def test_qualified_closure_naming_its_shortfall(self):
        res = self.honest(extra_lines=[
            "This closure is a qualified closure and names its shortfall "
            "in this record."])
        self.assert_no_false_fail(res)

    def test_succession_fixture_counts_seat_once(self):
        res = self.honest(extra_lines=[
            "Seat Colour lens Red: the first holder %s was superseded; "
            "the second holder %s is the holder of the seat."
            % (sid(8), sid(1))],
            teams=[("Audit team", None,
                    [("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])])
        self.assert_no_false_fail(res)
        count = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertEqual(count["Audit team"]["counted_total"], 3)

    def test_succession_inside_superseded_section_enters_no_count(self):
        res = self.honest(extra_lines=[
            "## Superseded section",
            "Seat Colour lens Red: the first holder %s was superseded; "
            "the second holder %s is the holder of the seat."
            % (sid(8), sid(9)),
            "The section above is superseded under the priority rule "
            "and enters nothing for this run."],
            teams=[("Audit team", None,
                    [("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])])
        count = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertNotEqual(count["Audit team"]["counted_total"], 3)


class TestFailureExpectations(MusterCase):
    """TM-TEST-3, failure expectations and the per check split."""

    def test_none_readable_cannot_start_exit_4(self):
        result = self.invoke(["--stage", "Step 99", "--runner",
                              "Fixture Auditor", "--capacity", "Auditor",
                              "/nonexistent/fixture-roster.md"])
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("Rollup:", result.stdout)

    def test_settling_record_absent_unverifiable_on_affected_only(self):
        res, _ = self.run_stage(
            {"note.md": "# A record with no roster for the stage.\n"})
        self.assert_rollup(res, "UNVERIFIABLE", 3)

    def test_records_read_not_settling_give_not_proven(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", "not recorded",
                      "counted in base")])], board=BOARD)})
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")

    def test_proven_shortfall_fails_even_where_truncation_stands(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 1, "counted in base")])],
            board=BOARD,
            extra_lines=["The rest of this roster file is truncated."])})
        self.assert_rollup(res, "FAIL", 1)
        self.assert_in_stdout(res, "truncated")

    def test_no_pinned_base_unverifiable_on_affected_rule_checks(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base")])],
            board=BOARD)})
        self.assert_in_stdout(res, "UNVERIFIABLE")

    def test_no_tier_or_no_step_unverifiable_and_run_still_reports(self):
        res, _ = self.run_stage({"roster.md":
                                 "# A record naming no stage and no "
                                 "tier.\n"})
        self.assert_rollup(res, "UNVERIFIABLE", 3)

    def test_undecodable_bytes_case_stands_in_this_group(self):
        bad = b"# Roster\n\nBytes: \xff\xfe.\n"
        res, _ = self.run_stage({"roster.md": bad})
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")
        self.assertNotEqual(res.returncode, 4)

    def test_defective_roster_corollary_both_limbs(self):
        # Provable limb: the roster is proven defective and the true
        # staffing is provable from records independent of it, so the
        # defect stands as a record defect and the check takes its
        # result on the independent records.
        provable = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=BOARD,
            extra_lines=["This roster is proven defective as a record; "
                         "the step record states the true staffing "
                         "independently of it."])})[0]
        self.assert_in_stdout(provable, "record defect")
        # Unprovable limb: the roster is proven defective and no record
        # independent of it proves the true staffing, so the affected
        # claim check is NOT PROVEN.
        unprovable = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 2, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=BOARD,
            extra_lines=["This roster is proven defective as a record; "
                         "no other record in this set speaks to the "
                         "true staffing."])})[0]
        self.assert_rollup(unprovable, "NOT PROVEN", 2)


class TestGenerationAndFloor(MusterCase):
    """Generation determinism (plan section 3, D-06) and the floor."""

    def test_generation_twice_from_same_sources_same_hash(self):
        # NOT RUNNABLE, with its reason recorded in this form: counting
        # table generation stands charged at plan section 3, generating
        # twice from the same per step source files giving the same
        # shipped bytes and the same hash, but no per step source files
        # and no generation act stand in the tree, so no generation act
        # can be driven in this form. The path stands recorded not
        # runnable here and in the Step 13 paper, and no result is
        # cited from it.
        self.require_product()
        self.fail("NOT RUNNABLE: no per step source files and no "
                  "generation act stand in the tree, so the generation "
                  "determinism path cannot be driven in this form")

    def test_python_floor_refusal_below_311_at_install(self):
        # The floor stands at every install plan section 8 names and at
        # the start of every post install run that section names, and
        # nowhere else: at Python below 3.11 the install act and the
        # post install run are refused. NOT RUNNABLE, with its reason
        # recorded in this form: no interpreter below Python 3.11
        # stands in this run environment and no install act can be
        # driven while no installable product stands, so the refusal
        # behaviour, its outcome word, and its exit consequence cannot
        # be driven in this form. The path stands recorded not runnable
        # here and in the Step 13 paper, and no result is cited from
        # it.
        self.require_product()
        self.fail("NOT RUNNABLE: no interpreter below Python 3.11 "
                  "stands in this run environment and no install act "
                  "can be driven, so the floor refusal path cannot be "
                  "driven in this form")
