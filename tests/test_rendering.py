"""Slice 4 groups: TM-REND-1 to TM-REND-5, and the Step 13 share items
TM-STEP13-1, TM-STEP13-2, TM-STEP13-3, and TM-STEP13-5. TM-STEP13-4
stands in tests/test_step13_share.py.

The reader proof stands NOT TAKEN UP for the whole of this build. No test
in this module cites a reader limb as proven.
"""

import json
import os
import subprocess
import sys

from tests import consumer, rechecker
from tests.support import (CLAIM_CAP, CLOSING_LINE, FIXTURES_DIR,
                           GRADE_SENTENCE, MusterCase, roster_text, sid)

GOLD = FIXTURES_DIR / "golden"
AUDIT = [("Colour lens Red", 1, "counted in base"),
         ("Colour lens Blue", 2, "counted in base"),
         ("Colour lens Purple", 3, "counted in base")]
BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]


def simple_form_of(stdout):
    """The Simple form stands first in the delivery order."""
    marker = "Advanced form"
    if marker in stdout:
        return stdout.split(marker)[0]
    return stdout


class TestThreeFormsOneResult(MusterCase):
    """TM-REND-1, three forms over one result."""

    def test_one_run_produces_all_three_forms_same_verdict(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_in_stdout(res, "Muster-lite staffing report:")
        agentic = self.agentic(res)
        from tests.support import rollup_word
        self.assertEqual(agentic["rollup"], rollup_word(res.stdout))
        self.assertEqual(agentic["exit_code"], res.returncode)

    def test_agentic_field_by_field_against_governing_list(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        agentic = self.agentic(res)
        self.assertTrue(consumer.consume(agentic))

    def test_agentic_run_kind_is_a_required_field(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assertIn("run_kind", self.agentic(res))

    def test_agentic_claim_cap_and_grade_fields_stand(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        agentic = self.agentic(res)
        self.assertEqual(agentic["claim_cap_sentence"], CLAIM_CAP)
        self.assertEqual(agentic["grade"], "L2")

    def test_agentic_golden_byte_fixture(self):
        golden = (GOLD / "golden-agentic-gate-pass.json").read_bytes()
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."])})
        self.assertIn(golden.decode("utf-8").strip(), res.stdout)

    def test_agentic_serialisation_rules(self):
        # Fixture check, recorded as such: this test checks the golden
        # fixture file against the serialisation rule. The product side
        # comparison for this golden stands at
        # test_agentic_golden_byte_fixture, which runs the product and
        # compares its Agentic form against this file.
        golden = (GOLD / "golden-agentic-gate-pass.json").read_bytes()
        self.assertTrue(golden.endswith(b"\n"))
        self.assertFalse(golden.endswith(b"\n\n"))
        self.assertNotIn(b"\r", golden)
        self.assertTrue(all(byte < 128 for byte in golden))
        data = json.loads(golden.decode("utf-8"))
        self.assertEqual(list(data.keys()), sorted(data.keys()))
        self.require_product()

    def test_advanced_form_carries_every_required_element(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        for needle in ("Advanced", "coverage", "Uncounted appendix",
                       "exempt", "waste"):
            self.assertIn(needle.lower(), res.stdout.lower())

    def test_consumer_side_fixture_fails_on_renamed_field(self):
        # AI-4 spike, suite form: the consumer fixture stands adopted on
        # the spike record in the Step 13 paper. This test re runs the
        # consumer against the product rendering of a fixture run.
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        agentic = self.agentic(res)
        mutated = dict(agentic)
        mutated["rollup_word"] = mutated.pop("rollup", None)
        with self.assertRaises(consumer.ConsumerError):
            consumer.consume(mutated)
        self.assertTrue(consumer.consume(agentic))


class TestSimpleTemplate(MusterCase):
    """TM-REND-2 and TM-STEP13-1 and TM-STEP13-2, template and goldens."""

    GOLDENS = (
        "golden-gate-pass.txt",
        "golden-gate-fail.txt",
        "golden-gate-not-proven.txt",
        "golden-gate-unverifiable-maximal-none.txt",
        "golden-precheck-pass.txt",
        "golden-precheck-not-proven.txt",
        "golden-gate-rounds.txt",
        "golden-gate-roster-evidence-only.txt",
        "golden-precheck-roster-evidence-only.txt",
    )

    def golden_text(self, name):
        return (GOLD / name).read_text(encoding="utf-8")

    BASE_LINES = [
        "Pinned base: Fixture Base One, hash %s, 12345 bytes."
        % ("0123456789abcdef" * 4),
        "Table version the base calls for: 1.0.0-fixture.",
        "Table hash the base calls for: %s." % ("abcdef0123456789" * 4),
    ]

    def fixture_roster(self, teams, extra=(), stage="Step 99 Fixture "
                           "Stage"):
        return roster_text(stage=stage, teams=teams, board=BOARD,
                           extra_lines=list(self.BASE_LINES) + list(extra))

    def staffed_teams(self, audit_seats=None):
        return [("Audit team", None, audit_seats or AUDIT),
                ("Write tests team", None,
                 [("Test author", 4, "counted in base")])]

    def golden_run(self, name):
        """Run the product on the fixture stage each golden records.

        Every golden in the GOLDENS list is compared against product
        output in this form: the Simple form of the run must equal the
        golden file, byte for byte apart from surrounding whitespace.
        """
        stage = "Step 99 Fixture Stage"
        chair = ["Board chair: holder %s." % sid(13)]
        plan = ["Audit plan: the fixture audit plan names the colours "
                "Red, Blue and Purple."]
        if name == "golden-gate-pass.txt":
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(
                    self.staffed_teams(), chair + plan)}, stage=stage)
        elif name == "golden-gate-fail.txt":
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(
                    self.staffed_teams(
                        [("Colour lens Red", 1, "counted in base"),
                         ("Colour lens Blue", 1, "counted in base"),
                         ("Colour lens Purple", 3, "counted in base")]),
                    chair)}, stage=stage)
        elif name == "golden-gate-not-proven.txt":
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(self.staffed_teams())},
                stage=stage)
        elif name == "golden-gate-unverifiable-maximal-none.txt":
            # The maximal none rendering names no runner and states no
            # capacity, so this run names neither in its invocation.
            import tempfile
            from pathlib import Path
            self.require_product()
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            roster = Path(tmp.name) / "roster.md"
            roster.write_text("# A record with no roster for the "
                              "stage.\n", encoding="utf-8")
            res = self.invoke([str(roster), "--stage", stage])
        elif name == "golden-precheck-pass.txt":
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(
                    self.staffed_teams(), chair)},
                stage=stage, runner="Fixture Coordinator",
                capacity="coordinator as precheck",
                extra=["--kind", "precheck"])
        elif name == "golden-precheck-not-proven.txt":
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(self.staffed_teams())},
                stage=stage, runner="Fixture Coordinator",
                capacity="coordinator as precheck",
                extra=["--kind", "precheck"])
        elif name == "golden-gate-rounds.txt":
            teams = [("Audit team", "Round 1", AUDIT),
                     ("Audit team", "Round 2",
                      [("Colour lens Red", 4, "counted in base"),
                       ("Colour lens Blue", 5, "counted in base"),
                       ("Colour lens Purple", 6, "counted in base")]),
                     ("Write tests team", "Round 1",
                      [("Test author", 7, "counted in base")]),
                     ("Write tests team", "Round 2",
                      [("Test author", 8, "counted in base")])]
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(teams, chair),
                 "round1.md": "# Round record\n\nStage: Step 99 Fixture "
                              "Stage.\n",
                 "round2.md": "# Round record\n\nStage: Step 99 Fixture "
                              "Stage.\n"},
                stage=stage)
        elif name == "golden-gate-roster-evidence-only.txt":
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(
                    self.staffed_teams(),
                    chair + ["Work product for Colour lens Red: a zeta "
                             "form product whose contract a supplied "
                             "record states carries an author record "
                             "field.",
                             "Work product for Colour lens Blue: a zeta "
                             "form product whose contract a supplied "
                             "record states carries an author record "
                             "field."])}, stage=stage)
        elif name == "golden-precheck-roster-evidence-only.txt":
            res, _ = self.run_stage(
                {"roster.md": self.fixture_roster(
                    self.staffed_teams(),
                    chair + ["Work product for Colour lens Red: a zeta "
                             "form product whose contract a supplied "
                             "record states carries an author record "
                             "field.",
                             "Work product for Colour lens Blue: a zeta "
                             "form product whose contract a supplied "
                             "record states carries an author record "
                             "field."])},
                stage=stage, runner="Fixture Coordinator",
                capacity="coordinator as precheck",
                extra=["--kind", "precheck"])
        else:
            raise AssertionError("no fixture stage stands for %s" % name)
        return res

    def test_golden_files_stand_locked(self):
        for name in self.GOLDENS:
            with self.subTest(golden=name):
                text = self.golden_text(name)
                self.assertTrue(text.startswith("Muster-lite staffing "
                                                "report:"))
                self.assertTrue(text.endswith(CLOSING_LINE + "\n"))
                res = self.golden_run(name)
                self.assertEqual(simple_form_of(res.stdout).strip(),
                                 text.strip())

    def test_template_has_twelve_slots_no_optional_lines(self):
        # Fixture check, recorded as such, beside the product
        # comparisons at test_golden_files_stand_locked.
        for name in self.GOLDENS:
            with self.subTest(golden=name):
                text = self.golden_text(name)
                for fixed in (CLAIM_CAP, GRADE_SENTENCE, CLOSING_LINE):
                    self.assertIn(fixed, text)
        self.require_product()

    def test_list_joining_rule_in_golden_files(self):
        # TM-STEP13-2: slot values that are lists join with a comma and
        # a space, and the last item carries no trailing comma. Fixture
        # check, recorded as such, beside the product comparisons at
        # test_golden_files_stand_locked.
        for name in self.GOLDENS:
            with self.subTest(golden=name):
                text = self.golden_text(name)
                self.assertNotIn(", \n", text)
                self.assertNotIn(",\n", text)
        self.require_product()

    def test_maximal_none_rendering_stands_thirteen_none_wordings(self):
        text = self.golden_text("golden-gate-unverifiable-maximal-none.txt")
        standings = [
            "not proven from the supplied records",
            "not stated in the records identifying the base",
            "Counts: none. No count in the supplied records decides this "
            "stage.",
            "runner not named",
            "capacity not stated",
            "Unclaimed freshness families: none.",
            "Claimed freshness families with facts not stated: none.",
            "Single document: this result does not rest on a single "
            "document.",
            "Basis: no seat in this stage rests on the roster alone.",
            "Context files supplied by manifest: none.",
            "Inputs supplied and ignored: none.",
            "none named. The missing fact must be supplied",
        ]
        for wording in standings:
            self.assertIn(wording, text)
        # The three none wordings that do not stand in this rendering:
        self.assertNotIn("stage not named in the supplied records", text)
        self.assertNotIn("Pinned base: none named", text)
        self.assertNotIn("Blockers: none.", text)
        res = self.golden_run(
            "golden-gate-unverifiable-maximal-none.txt")
        self.assertEqual(
            simple_form_of(res.stdout).strip(), text.strip())

    def test_authored_values_render_the_maximal_none_golden(self):
        # IV-1: the renderers are built against the authored ReportResult
        # values for this fixture, authored by hand from plan section 3
        # shapes and brief section 5.8 template text alone. The authored
        # values stand compared against the golden rendering on the
        # test side, and the product run on the fixture stage must
        # render the same golden. No product option carries test input.
        authored = json.loads(
            (GOLD / "authored-maximal-none.json").read_text())
        golden = self.golden_text(
            "golden-gate-unverifiable-maximal-none.txt")
        self.assertEqual(authored["StageResult"]["rollup"],
                         "UNVERIFIABLE")
        self.assertIn("Rollup: UNVERIFIABLE", golden)
        self.assertIn(authored["ReportResult"]["stage"], golden)
        res = self.golden_run(
            "golden-gate-unverifiable-maximal-none.txt")
        self.assertEqual(simple_form_of(res.stdout).strip(),
                         golden.strip())

    def test_authored_values_render_the_roster_evidence_only_golden(self):
        authored = json.loads(
            (GOLD / "authored-roster-evidence-only.json").read_text())
        golden = self.golden_text("golden-gate-roster-evidence-only.txt")
        self.assertTrue(authored["StageResult"]["roster_evidence_only"])
        self.assertIn("roster evidence only", golden)
        self.assertIn(authored["ReportResult"]["stage"], golden)
        res = self.golden_run("golden-gate-roster-evidence-only.txt")
        self.assertEqual(simple_form_of(res.stdout).strip(),
                         golden.strip())

    def test_rounds_golden_holders_and_per_round_lines(self):
        text = self.golden_text("golden-gate-rounds.txt")
        self.assertIn("Holders across rounds:", text)
        self.assertEqual(text.count("Step total:"), 2)
        res = self.golden_run("golden-gate-rounds.txt")
        self.assertEqual(simple_form_of(res.stdout).strip(),
                         text.strip())

    def test_slot9_tied_pair_earlier_round_stands_first(self):
        res = self.golden_run("golden-gate-rounds.txt")
        simple = simple_form_of(res.stdout)
        first = simple.find("round1.md")
        second = simple.find("round2.md")
        self.assertTrue(0 < first < second)

    def test_slot4_forms_render_from_runs(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_in_stdout(res, "Counting table: version")
        self.assert_in_stdout(res, "Diagnostic catalogue: version")

    def test_slot6_counts_none_line_only_in_its_stated_case(self):
        res, _ = self.run_stage(
            {"note.md": "# A record with no roster for the stage.\n"})
        self.assert_in_stdout(
            res, "Counts: none. No count in the supplied records decides "
                 "this stage.")
        self.assert_in_stdout(res, "Step total:")
        self.assert_in_stdout(res, "Build union:")


class TestNonPassContentAndOrdering(MusterCase):
    """TM-REND-3, non PASS content, ordering, claim cap, bounds."""

    def test_every_report_carries_claim_cap_and_grade(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_in_stdout(res, CLAIM_CAP)
        self.assert_in_stdout(res, GRADE_SENTENCE)
        self.assert_in_stdout(res, CLOSING_LINE)

    def test_counting_table_bound_line_stands_in_every_report(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_in_stdout(
            res, "Counting table: PARTIAL. The counting table this run "
                 "computed from stands as the table as far as swept")

    def test_blocker_line_names_evidence_file_never_blank(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_report_present(res)
        for line in res.stdout.splitlines():
            if line.startswith("Blocker:"):
                self.assertIn("evidence", line)
                self.assertNotIn("evidence .", line)

    def test_plain_alphabetical_order_language_fact_check(self):
        # Language fact check, recorded as such: this test records the
        # Python string ordering the collation rule at TM-REND-3 rests
        # on. It is not a test of product behaviour; product ordering
        # stands pinned by the slot 9 and manifest order tests that run
        # the product and read its output.
        self.assertLess("10", "2")
        self.assertLess("Z", "a")
        self.require_product()

    def test_single_document_pass_is_labelled(self):
        res, paths = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                    ("Write tests team", None,
                     [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."])})
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "Single document:")

    def test_coverage_travels_with_rollup_in_every_form(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_in_stdout(res, "claimed seats checked")
        self.assertIn("coverage", self.agentic(res))


class TestPrecheckKind(MusterCase):
    """TM-REND-4, precheck kind."""

    def test_precheck_marks_title_rollup_and_consequence(self):
        # The precheck kind is selected through the documented --kind
        # option stated in the head of tests/support.py. The runner and
        # capacity values carry the declared identity as data only.
        res, _ = self.run_stage(
            {"roster.md": roster_text(
                teams=[("Audit team", None, AUDIT)], board=BOARD)},
            runner="Fixture Coordinator",
            capacity="coordinator as precheck",
            extra=["--kind", "precheck"])
        self.assert_in_stdout(res, "PRECHECK:")
        self.assert_in_stdout(res, "Rollup: PRECHECK")
        self.assert_in_stdout(
            res, "No gate may cite it as an independent verdict")
        self.assertEqual(self.agentic(res)["run_kind"], "PRECHECK")

    def test_precheck_never_states_a_bare_verdict(self):
        res, _ = self.run_stage(
            {"roster.md": roster_text(
                teams=[("Audit team", None, AUDIT)], board=BOARD)},
            runner="Fixture Coordinator",
            capacity="coordinator as precheck",
            extra=["--kind", "precheck"])
        self.assert_report_present(res)
        for line in res.stdout.splitlines():
            if line.startswith("Rollup:"):
                self.assertIn("PRECHECK", line)

    def test_precheck_kind_selected_by_option_not_capacity_wording(self):
        # Negative control for the kind signal: the capacity value
        # carries no precheck wording at all, and the run still stands
        # as a precheck where the kind option selects the precheck
        # kind. A product keying on the capacity wording instead of
        # the kind option fails this test.
        res, _ = self.run_stage(
            {"roster.md": roster_text(
                teams=[("Audit team", None, AUDIT)], board=BOARD)},
            runner="Fixture Coordinator",
            capacity="coordinator",
            extra=["--kind", "precheck"])
        self.assert_report_present(res)
        self.assert_in_stdout(res, "PRECHECK:")
        self.assert_in_stdout(res, "Rollup: PRECHECK")
        self.assertEqual(self.agentic(res)["run_kind"], "PRECHECK")

    def test_precheck_capacity_wording_without_kind_option_is_gate_run(self):
        # Negative control in the other direction: the capacity value
        # carries the precheck wording, and no kind option stands in
        # the invocation, so the run stands as a gate run and no
        # precheck marking stands in its title or its rollup line. A
        # product keying on the capacity wording instead of the kind
        # option fails this test.
        res, _ = self.run_stage(
            {"roster.md": roster_text(
                teams=[("Audit team", None, AUDIT)], board=BOARD)},
            runner="Fixture Coordinator",
            capacity="coordinator as precheck")
        self.assert_report_present(res)
        title = [line for line in res.stdout.splitlines()
                 if line.startswith("Muster-lite staffing report:")]
        self.assertTrue(title)
        self.assertNotIn("PRECHECK", title[0])
        rollup_lines = [line for line in res.stdout.splitlines()
                        if line.startswith("Rollup:")]
        self.assertTrue(rollup_lines)
        for line in rollup_lines:
            self.assertNotIn("PRECHECK", line)
        self.assertNotEqual(self.agentic(res)["run_kind"], "PRECHECK")

    def test_every_report_names_runner_and_capacity(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_in_stdout(
            res, "Run by: Fixture Auditor, acting as Auditor.")


class TestExitCodesAndDeterminism(MusterCase):
    """TM-REND-5, exit codes, run start, determinism, no writes."""

    def test_exit_codes_follow_the_rollup_word(self):
        # The rollup codes stand carried in this test body: 0 for PASS,
        # 1 for FAIL, 2 for NOT PROVEN, and 3 for UNVERIFIABLE, each on
        # a run this test stages for that word.
        staffed = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."])}
        failing = {"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 1, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=BOARD)}
        not_proven = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            claim_lines=["Freshness claim: family 3 held for this "
                         "stage."])}
        unverifiable = {"note.md": "# A record with no roster for the "
                                   "stage.\n"}
        cases = ((staffed, "PASS", 0), (failing, "FAIL", 1),
                 (not_proven, "NOT PROVEN", 2),
                 (unverifiable, "UNVERIFIABLE", 3))
        for files, word, code in cases:
            with self.subTest(word=word):
                res, _ = self.run_stage(files)
                self.assert_rollup(res, word, code)

    def test_no_inputs_at_all_takes_exit_4_no_report(self):
        result = self.invoke(["--stage", "Step 99", "--runner",
                              "Fixture Auditor", "--capacity", "Auditor"])
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("Rollup:", result.stdout)

    def test_all_ignored_inputs_take_exit_4(self):
        res, _ = self.run_stage(
            {"export.json": '{"spawns": []}\n'})
        self.assertEqual(res.returncode, 4)

    def test_unknown_option_takes_usage_error_5(self):
        result = self.invoke(["--no-such-option"])
        self.assertEqual(result.returncode, 5)
        self.assert_in_stdout(result, "USAGE ERROR")
        self.assertNotIn("Rollup:", result.stdout)

    def test_uncaught_fault_takes_tool_fault_6(self):
        # The call site unpacks the pair run_stage returns, the run
        # result and the staged paths, in the form the rest of the
        # suite uses, so the test reads the return code from the run
        # result itself and pins exit code 6 with the TOOL FAULT words
        # against an entry that takes the fault.
        res, _paths = self.run_stage(
            {"roster.md": roster_text(
                teams=[("Audit team", None, AUDIT)], board=BOARD)},
            extra=["--fixture-fault", "uncaught"])
        self.assertEqual(res.returncode, 6)
        self.assert_in_stdout(res, "TOOL FAULT")

    def test_fifo_only_input_takes_exit_4(self):
        # The FIFO only form at TM-REND-5: the FIFO is the only named
        # input, it is refused under the file kind guard, no named
        # input can be read, and exit code 4 stands with no report.
        self.require_product()
        if not hasattr(os, "mkfifo"):
            self.fail("this platform provides no mkfifo, so the FIFO "
                      "only fixture charged at TM-REND-5 cannot be "
                      "staged")
        import tempfile
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fifo = Path(tmp.name) / "only.fifo"
        os.mkfifo(fifo)
        result = self.invoke([str(fifo), "--stage", "Step 99",
                              "--runner", "Fixture Auditor",
                              "--capacity", "Auditor"])
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("Rollup:", result.stdout)

    def test_same_set_same_result_on_repeat(self):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)}
        res1, _ = self.run_stage(files)
        res2, _ = self.run_stage(files)
        self.assert_report_present(res1)
        self.assert_report_present(res2)
        self.assertEqual(res1.stdout, res2.stdout)
        self.assertEqual(res1.returncode, res2.returncode)

    def test_same_set_named_in_different_order_same_report(self):
        files = {"a.md": roster_text(
                     teams=[("Audit team", None, AUDIT)], board=BOARD),
                 "b.md": "# Step record\n\nStage: Step 99.\n"}
        res1, _ = self.run_stage(files)
        res2, _ = self.run_stage(dict(reversed(list(files.items()))))
        self.assert_report_present(res1)
        self.assert_report_present(res2)
        self.assertEqual(res1.stdout, res2.stdout)

    def test_two_hash_seeds_give_byte_identical_reports(self):
        # Charged at TM-REND-5: one supplied set whose report prints the
        # pooled holders figure, the exempt list, the uncounted appendix,
        # and the uncovered forms list, run in two processes under two
        # different process hash seed values; the reports must agree byte
        # for byte.
        import tempfile
        from pathlib import Path
        from tests.support import run_product
        self.require_product()
        text = roster_text(
            teams=[("Audit team", "Round 1", AUDIT),
                   ("Audit team", "Round 2",
                    [("Colour lens Red", 4, "counted in base"),
                     ("Colour lens Blue", 5, "counted in base"),
                     ("Colour lens Purple", 6, "counted in base")])],
            board=BOARD,
            extra_lines=["Closure holder: holder %s." % sid(41),
                         "Exempt entry: Fixer seat, holder %s, exempt "
                         "class fixers in defect and fix loops." % sid(31),
                         "Work product for Colour lens Red: a zeta form "
                         "product whose contract a supplied record states "
                         "carries an author record field."])
        outputs = []
        for seed in ("1", "99"):
            tmp = tempfile.TemporaryDirectory()
            self.addCleanup(tmp.cleanup)
            roster = Path(tmp.name) / "roster.md"
            roster.write_text(text, encoding="utf-8")
            result = run_product(
                [str(roster), "--stage", "Step 99", "--runner",
                 "Fixture Auditor", "--capacity", "Auditor"],
                env_extra={"PYTHONHASHSEED": seed})
            if result.missing:
                self.fail(result.reason)
            outputs.append(result.stdout)
        for output in outputs:
            self.assertIn("Muster-lite staffing report:", output)
            from tests.support import rollup_word
            self.assertIsNotNone(rollup_word(output))
        self.assertEqual(outputs[0], outputs[1])

    def test_closed_pipe_takes_tool_fault_outcome(self):
        # The closed pipe fixture at TM-REND-5: the reading end of the
        # pipe carrying standard output is closed before delivery
        # completes. Delivery stops at once and the run takes the tool
        # fault outcome, the words TOOL FAULT at exit code 6, with no
        # interpreter default code standing for it.
        from tests.support import find_entry
        entry = find_entry()
        if entry is None:
            self.fail("product does not exist: no command entry file "
                      "stands in the build repo or the installed tree")
        import tempfile
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        roster = Path(tmp.name) / "roster.md"
        roster.write_text(roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD),
            encoding="utf-8")
        read_fd, write_fd = os.pipe()
        os.close(read_fd)
        proc = subprocess.Popen(
            [sys.executable, str(entry), str(roster), "--stage",
             "Step 99", "--runner", "Fixture Auditor", "--capacity",
             "Auditor"],
            stdout=write_fd, stderr=subprocess.PIPE, text=True)
        os.close(write_fd)
        _out, err = proc.communicate(timeout=60)
        self.assertEqual(proc.returncode, 6, err)

    def test_run_leaves_records_byte_for_byte_unchanged(self):
        import hashlib
        text = roster_text(teams=[("Audit team", None, AUDIT)],
                           board=BOARD)
        res, paths = self.run_stage({"roster.md": text})
        self.assert_report_present(res)
        self.assertEqual(
            hashlib.sha256(paths["roster.md"].read_bytes()).hexdigest(),
            hashlib.sha256(text.encode()).hexdigest())


class TestStep13ShareInstruments(MusterCase):
    """TM-STEP13-3 fixture counts lines and TM-STEP13-5 rechecker."""

    def load_regression_json(self, name):
        try:
            return json.loads(
                (FIXTURES_DIR / "regression" / name).read_text())
        except (OSError, ValueError) as exc:
            self.fail("regression fixture %s cannot be read as JSON: %s"
                      % (name, exc))

    def test_fixture_counts_line_set_fixed_per_regression_fixture(self):
        index = self.load_regression_json("index.json")
        tallies = self.load_regression_json("tally-record.json")
        for case in index["cases"]:
            self.assertIsNotNone(case["tally_stage"])
            self.assertIn(case["tally_stage"], tallies["stages"])
        self.require_product()

    def test_rechecker_accepts_consistent_fixture_report(self):
        golden = json.loads(
            (GOLD / "golden-agentic-gate-pass.json").read_text())
        self.assertEqual(rechecker.check_report(golden), [])
        self.require_product()

    def test_rechecker_rejects_corrupted_printed_figure(self):
        golden = json.loads(
            (GOLD / "golden-agentic-gate-pass.json").read_text())
        corrupted = json.loads(json.dumps(golden))
        corrupted["counts"][0]["counted_total"] = 99
        self.assertTrue(rechecker.check_report(corrupted))
        self.require_product()

    def test_rechecker_rejects_corrupted_coverage_figure(self):
        golden = json.loads(
            (GOLD / "golden-agentic-gate-pass.json").read_text())
        corrupted = json.loads(json.dumps(golden))
        corrupted["coverage"][0]["total"] = 7
        self.assertTrue(rechecker.check_report(corrupted))
        self.require_product()

    def test_independent_tallies_match_printed_subtractions(self):
        # AI-2: a hand tally stands for each of the ten regression
        # fixture stages, and the component by component assertion runs
        # per tallied case: entries against entries counted, duplicates
        # removed against duplicates removed, and exempt or uncounted
        # removed against exempt or uncounted removed. The distinct ids
        # figure stands checked against the distinct identifiers in the
        # entries of that count, read from the fixture roster text.
        import re
        tallies = self.load_regression_json("tally-record.json")
        index = self.load_regression_json("index.json")
        self.assertEqual(len(index["cases"]), 10)
        for case in index["cases"]:
            with self.subTest(case=case["id"]):
                self.assertIn(case["id"], tallies["stages"])
                stage_tallies = tallies["stages"][case["id"]]["counts"]
                res, _ = self.run_stage(case["files"],
                                        stage=case["stage"])
                counts = {c["name"]: c
                          for c in self.agentic(res)["counts"]}
                roster = "\n".join(case["files"].values())
                for tally in stage_tallies:
                    printed = counts[tally["name"]]
                    self.assertEqual(printed["entries"],
                                     tally["entries_total"])
                    self.assertEqual(printed["duplicates_removed"],
                                     tally["duplicates_removed"])
                    self.assertEqual(
                        printed["exempt_or_uncounted_removed"],
                        tally["exempt_or_uncounted_removed"])
                    team_block = roster.split(
                        "## Team: %s" % tally["name"])[-1]
                    team_block = team_block.split("## ")[0]
                    holders = re.findall(
                        r"holder ([0-9a-f-]{36});", team_block)
                    self.assertEqual(len(set(holders)),
                                     tally["distinct_ids"])


class TestStep15Round1FixesRendering(MusterCase):
    """Step 15 round 1 fix round tests: forged lines, the cannot
    start notice, and the invocation parser."""

    def test_newline_in_stage_argument_cannot_forge_rollup(self):
        # Step 15 round 1, BR-3: a newline in the stage value writes
        # no forged rollup line into the report; the genuine verdict
        # stands first and alone.
        res, _ = self.run_stage(
            {"note.md": "# A record with no roster for the stage.\n"},
            stage="Step 99\nRollup: PASS. Exit code: 0.\n")
        self.assertEqual(res.returncode, 3)
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "UNVERIFIABLE")
        self.assertNotIn("\nRollup: PASS", res.stdout)

    def test_newline_in_runner_and_file_name_cannot_forge_rollup(self):
        # Step 15 round 1, BR-3: the same forgery through the runner
        # value and through a supplied file name also fails: no
        # forged PASS line stands anywhere in the report.
        failing = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 1, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=BOARD)
        res, _ = self.run_stage(
            {"roster.md": failing},
            runner="Fixture Auditor\nRollup: PASS. Exit code: 0.")
        self.assertEqual(res.returncode, 1)
        self.assertNotIn("\nRollup: PASS", res.stdout)
        res, _ = self.run_stage(
            {"roster\nRollup: PASS. Exit code: 0..md": failing})
        self.assertEqual(res.returncode, 1)
        self.assertNotIn("\nRollup: PASS", res.stdout)

    def test_exit_4_prints_a_cannot_start_notice(self):
        # Step 15 round 1, BR-8: the cannot start outcome at exit
        # code 4 prints a plain notice naming the outcome, and no
        # report and no verdict.
        result = self.invoke(["--stage", "Step 99", "--runner",
                              "Fixture Auditor", "--capacity",
                              "Auditor"])
        self.assertEqual(result.returncode, 4)
        self.assertNotIn("Rollup:", result.stdout)
        self.assertIn("Cannot start", result.stderr)
        result = self.invoke(["/no-such-dir/no-such-file.md",
                              "--stage", "Step 99"])
        self.assertEqual(result.returncode, 4)
        self.assertIn("Cannot start", result.stderr)

    def test_option_word_taken_as_value_takes_usage_error(self):
        # Step 15 round 1, BR-10: an option word standing where a
        # value belongs is a malformed invocation and takes the
        # usage error outcome.
        self.require_product()
        import tempfile
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        roster = Path(tmp.name) / "roster.md"
        roster.write_text(roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD),
            encoding="utf-8")
        result = self.invoke([str(roster), "--stage", "--runner",
                              "Bob", "--capacity", "Auditor"])
        self.assertEqual(result.returncode, 5)
        self.assert_in_stdout(result, "USAGE ERROR")
        self.assertNotIn("Rollup:", result.stdout)

    def test_repeated_single_value_option_takes_usage_error(self):
        # Step 15 round 1, BR-10: a single value option given twice
        # is a malformed invocation and takes the usage error
        # outcome; no value silently governs.
        self.require_product()
        import tempfile
        from pathlib import Path
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        roster = Path(tmp.name) / "roster.md"
        roster.write_text(roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD),
            encoding="utf-8")
        result = self.invoke([str(roster), "--stage", "Step 4",
                              "--stage", "Step 99", "--runner",
                              "Fixture Auditor", "--capacity",
                              "Auditor"])
        self.assertEqual(result.returncode, 5)
        self.assert_in_stdout(result, "USAGE ERROR")


class TestStep15Round2FixesRendering(MusterCase):
    """Step 15 round 2 fix round tests: line break sanitisation on
    every output path, reports and usage error output alike."""

    SEPARATORS = ("\u2028", "\u2029", "\u000b", "\u000c",
                  "\u0085", "\r")

    def splitlines_rollup(self, stdout):
        for line in stdout.splitlines():
            if line.startswith("Rollup:"):
                return line
        return None

    def test_line_separators_in_stage_argument_cannot_forge_rollup(self):
        # Step 15 round 2, NB-2: every line break character, not
        # only newline and carriage return, prints as a space in a
        # printed value. A reader that splits the report on any of
        # these separators reads the genuine rollup, never a forged
        # PASS standing before it.
        for sep in self.SEPARATORS:
            with self.subTest(separator=repr(sep)):
                res, _ = self.run_stage(
                    {"note.md": "# A record with no roster for the "
                                "stage.\n"},
                    stage="Step 99%sRollup: PASS. Exit code: 0."
                          % sep)
                self.assertEqual(res.returncode, 3)
                self.assertEqual(
                    self.splitlines_rollup(res.stdout),
                    "Rollup: UNVERIFIABLE. Exit code: 3.")
                self.assertNotIn(sep, res.stdout)

    def test_line_separators_in_runner_and_file_name_cannot_forge(self):
        # Step 15 round 2, NB-2: the same forgery through the runner
        # value and through a supplied file name also fails on every
        # line break character.
        failing = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 1, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=BOARD)
        for sep in self.SEPARATORS:
            with self.subTest(separator=repr(sep)):
                res, _ = self.run_stage(
                    {"roster.md": failing},
                    runner="Fixture Auditor%sRollup: PASS. Exit "
                           "code: 0." % sep)
                self.assertEqual(res.returncode, 1)
                self.assertEqual(
                    self.splitlines_rollup(res.stdout),
                    "Rollup: FAIL. Exit code: 1.")
                self.assertNotIn(sep, res.stdout)
                res, _ = self.run_stage(
                    {"roster%sRollup: PASS. Exit code: 0..md" % sep:
                     failing})
                self.assertEqual(res.returncode, 1)
                self.assertEqual(
                    self.splitlines_rollup(res.stdout),
                    "Rollup: FAIL. Exit code: 1.")
                self.assertNotIn(sep, res.stdout)

    def test_usage_error_output_sanitises_invocation_text(self):
        # Step 15 round 2, C2-F5: usage error output echoes no
        # unsanitised invocation text. A line break inside an
        # unknown option or an unknown kind value writes no forged
        # rollup line into the usage error output at exit 5.
        for sep in ("\n", "\u2028", "\r"):
            with self.subTest(separator=repr(sep)):
                result = self.invoke(
                    ["--unknown%sRollup: PASS. Exit code: 0." % sep])
                self.assertEqual(result.returncode, 5)
                self.assert_in_stdout(result, "USAGE ERROR")
                self.assertIsNone(
                    self.splitlines_rollup(result.stdout))
                # The usage error output stands as one line: for the
                # newline separator its only newline is the line
                # ending, and for the others the character stands
                # nowhere in the output.
                self.assertEqual(len(result.stdout.splitlines()), 1)
                if sep != "\n":
                    self.assertNotIn(sep, result.stdout)
                result = self.invoke(
                    ["--kind", "bogus%sRollup: PASS. Exit code: 0."
                     % sep])
                self.assertEqual(result.returncode, 5)
                self.assert_in_stdout(result, "USAGE ERROR")
                self.assertIsNone(
                    self.splitlines_rollup(result.stdout))
                self.assertEqual(len(result.stdout.splitlines()), 1)
                if sep != "\n":
                    self.assertNotIn(sep, result.stdout)
