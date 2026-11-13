"""The Step 13 share remainder, the specimen tests, and the Step 12
roster test: TM-STEP13-4, TM-STEP13-6, the specimen charge in the held
block, the IV-2 omitted group fixture record.

Settled parts, standing with this module in words: the two held items
stand settled by Manager settlement and their encodings stand landed
in this suite. H-7 (claim kind determinism) stands settled by the use
versus mention rule: its determination fixtures stand in the held
parts of tests/test_core_freshness.py, tests/test_core_linkage.py,
and tests/test_shell.py, in the held block own terms, and no test in
this module asserts a claiming rule for an H-7 shape. C2-3 (the AC-16
specimen result) stands settled by the amended specimen set: the
specimen expectation for the Step 4 result stands encoded in this
module at TestSpecimens, on the amended supplied set the settlement
names, and AC-16 stands fully evidenced when that encoding stands.
Each encoding covers the settled determination only, and forms
outside it stand as they stood. CQ-14 stands reserved to Step 18:
AC-19 is not mapped as a Step 13 test group and no test group for it
stands in this suite. S5-E42: no test, fixture, or result in this
module presents the counting table as complete.
"""

import json

from tests.support import DESIGN_DIR, FIXTURES_DIR, MusterCase

GOLD = FIXTURES_DIR / "golden"


class TestNoneWordingCombinations(MusterCase):
    """TM-STEP13-4, none wording combination proof."""

    NONE_WORDINGS = (
        "stage not named in the supplied records",
        "Pinned base: none named in the supplied records.",
        "not proven from the supplied records",
        "not stated in the records identifying the base",
        "Counts: none. No count in the supplied records decides this "
        "stage.",
        "runner not named",
        "capacity not stated",
        "Unclaimed freshness families: none. Every freshness family is "
        "claimed in the supplied records.",
        "Claimed freshness families with facts not stated: none.",
        "Single document: this result does not rest on a single document.",
        "Basis: no seat in this stage rests on the roster alone.",
        "Blockers: none. No check stands below PASS.",
        "Context files supplied by manifest: none. No context files were "
        "supplied.",
        "Inputs supplied and ignored: none.",
        "none named. The missing fact must be supplied in a record named "
        "in the supplied set line.",
    )

    def test_each_none_wording_reads_as_a_complete_sentence_in_a_golden(self):
        texts = ""
        for path in GOLD.glob("golden-*.txt"):
            texts += path.read_text(encoding="utf-8")
        for wording in self.NONE_WORDINGS:
            with self.subTest(wording=wording[:40]):
                # A wording is covered where a golden rendering stands it
                # inside a complete sentence in its slot.
                self.assertTrue(
                    wording in texts or wording.rstrip(".") in texts,
                    "none wording stands in no golden rendering: %s"
                    % wording)
        self.require_product()

    def test_maximal_none_and_pass_variants_cover_the_slot9_pair(self):
        maximal = (GOLD / "golden-gate-unverifiable-maximal-none.txt") \
            .read_text(encoding="utf-8")
        gate_pass = (GOLD / "golden-gate-pass.txt").read_text(
            encoding="utf-8")
        self.assertIn("Blockers: none. No check stands below PASS.",
                      gate_pass)
        self.assertIn("none named. The missing fact must be supplied",
                      maximal)
        self.require_product()


class TestCatalogueFixtureAttempts(MusterCase):
    """TM-STEP13-6, one emitting fixture attempted for every named shape."""

    def load_record(self):
        return json.loads(
            (FIXTURES_DIR / "catalogue" / "attempt-record.json")
            .read_text(encoding="utf-8"))

    EXPECTED_SHAPES = (
        "team minimum proven shortfall",
        "team minimum not proven on an unparsable or unread roster "
        "passage",
        "banded team chosen size not stated",
        "distinctness duplicate holding making a minimum appear met",
        "distinctness resting on fragments alone",
        "carried seat breach, one holder holding both Principles "
        "holdings or a counted seat beside a carried seat",
        "review board seat with no identifier",
        "review board minimum shortfall",
        "pool role held by two agents in one stage holding",
        "tier invocation flag FM-9, claimed reduced tier with no "
        "invocation record",
        "colour completeness with no plan or qualifying charge named",
        "colour completeness with a named charge that does not qualify",
        "colour completeness missing seat inside the bound",
        "Plaid amount needed on a Plaid target",
        "linkage blank author record field",
        "linkage author record naming a different agent as the only "
        "linkage for a counted seat",
        "linkage indeterminate limb, form contract unsettled",
        "linkage author record unreadable, product truncated",
        "linkage author record passage not parseable without guessing",
        "linkage zero coverage bar, whole team unchecked",
        "linkage assertion bar on an asserting team with no checked "
        "seat",
        "one product counted for two seats",
        "freshness proven breach, self audit presented as audit, "
        "Critical",
        "freshness proven breach, other, High",
        "freshness claimed family with facts not stated",
        "freshness holding or involvement entry with a holder value "
        "that is not an identifier",
        "freshness family 1 fixer holding naming no round",
        "claim disagreement, claim contradicted by the computed result",
        "mechanical completeness difference landing in no composing "
        "claim check",
        "chain shape with no stated ordering fact",
    )

    def test_every_attempt_stands_recorded_in_one_of_two_forms(self):
        # Fixture record check, recorded as such beside the product
        # test at test_scoped_acceptance_only_is_pinned: the record
        # covers the named catalogue list exactly, by name, at the
        # exact count the list gives, 30 attempts as the record stands.
        record = self.load_record()
        self.assertEqual(len(record["attempts"]), 30)
        self.assertEqual(len(self.EXPECTED_SHAPES), 30)
        self.assertEqual({attempt["shape"]
                          for attempt in record["attempts"]},
                         set(self.EXPECTED_SHAPES))
        for attempt in record["attempts"]:
            self.assertIn(attempt["outcome"], ("emitted", "not emitted"))
            if attempt["outcome"] == "emitted":
                self.assertIn("attempt", attempt)
            else:
                self.assertIn("obstacle", attempt)
                self.assertNotEqual(
                    attempt["obstacle"].strip(),
                    "same Step 13 state as the record head states")
                self.assertGreater(len(attempt["obstacle"]), 40)
        self.require_product()

    def test_no_fixture_is_built_on_a_dishonest_record(self):
        # Fixture record check, recorded as such.
        record = self.load_record()
        for attempt in record["attempts"]:
            self.assertNotIn("fabricated", attempt.get("attempt", ""))
        self.require_product()

    def test_scoped_acceptance_only_is_pinned(self):
        record = self.load_record()
        self.assertIn("no code a regression fixture emits stands outside "
                      "the catalogue", record["duty"])
        self.assertIn("not claimed", record["duty"])
        res, _ = self.run_stage(
            {"roster.md": "# Roster artifact: Step 99\n"})
        codes = {c.get("diagnostic_code")
                 for c in self.agentic(res)["checks"]}
        catalogue = self.require_data_file("diagnostic-catalogue.json")
        known = {row["code"] for row in
                 json.loads(catalogue.read_text())["rows"]}
        self.assertTrue(codes <= known | {"none", None})


class TestOmittedGroupFixture(MusterCase):
    """IV-2 omitted group fixture, fixture limb only.

    The fixture record at fixtures/golden/omitted-group-record.md carries
    the two bounds in its head. The visibility judgement on this fixture
    is a design inspection of the fixture rendering only, under those
    bounds, as that record states.
    """

    def test_record_carries_both_bounds(self):
        # The guard reads the head as the head: bound one must stand in
        # the head of the record, in its exact words, including the
        # closing words. The Q7 bound must stand in the body in the
        # words the plan gives. A shortened head fails this guard.
        text = (GOLD / "omitted-group-record.md").read_text(
            encoding="utf-8")
        head = text.split("Fixture:", 1)[0]
        body = text.split("Fixture:", 1)[1] if "Fixture:" in text else ""
        self.assertIn(
            "the reader proof stands NOT TAKEN UP, the CQ-1, CQ-2, "
            "CQ-6, CQ-8 and CQ-11 reader limbs stay proven in design "
            "only for the whole of this build, and the visibility "
            "judgement on this fixture is a design inspection of the "
            "fixture rendering only and is cited as proof of no reader "
            "limb", head)
        self.assertIn(
            "on a run whose supplied set omits one whole named input "
            "group, the Simple form alone does not make the omission "
            "visible, because slot 10 lists the files read with no "
            "group labels and no absence line; the Advanced form makes "
            "the same omission visible through the group labelled "
            "manifest it renders in full", body)
        self.require_product()

    def test_golden_rendering_matches_the_fixed_expectation(self):
        text = (GOLD / "golden-omitted-group.txt").read_text(
            encoding="utf-8")
        self.assertIn("Supplied set: this run read roster.md.", text)
        self.require_product()

    def test_advanced_form_names_the_omitted_group_by_label(self):
        res, _ = self.run_stage(
            {"roster.md": "# Roster artifact: Step 99\n\nStage: Step 99.\n"})
        self.assert_in_stdout(res, "work products")


class TestSpecimens(MusterCase):
    """Specimen tests for the settled specimen results.

    These tests stand as a named fixture exception beside the Step 12
    roster test. Each specimen states its expected result from the brief
    rules at AC-16, and each specimen names its supplied set as a closed
    list inside the test, under the general specimen rule the C2-3
    settlement adopts: a specimen result may rest only on inputs in
    that list. The Step 4 specimen below stands on the amended set the
    settlement names, the Step 4 record set as it stands in this build
    records plus the evidence register file as a supplied record.
    """

    # The Step 4 specimen supplied set, as a closed list. The specimen
    # run below names exactly these files and no other file, and its
    # expected result rests only on inputs in this list.
    STEP4_SUPPLIED_SET = (
        "steps/step-04-board-member-1.md",
        "steps/step-04-board-member-2.md",
        "steps/step-04-gate-record.md",
        "steps/step-04-opening-record.md",
        "steps/step-04-record.md",
        "steps/step-04-trace.md",
        "preplan/evidence-register.md",
    )

    def run_specimen(self, paths, stage):
        args = [str(p) for p in paths]
        args += ["--stage", stage, "--runner", "Fixture Auditor",
                 "--capacity", "Auditor"]
        return self.invoke(args)

    def test_specimen_step5_set_s5_e53_form(self):
        # Predecessor Step 5 set, S5-E53 form: team amount and
        # distinctness PASS, stage rollup NOT PROVEN at exit code 2 on
        # the board chair limb alone, C6 printed as a bound.
        # Source: design/steps/step-05-roster-artifact.md.
        source = DESIGN_DIR / "steps" / "step-05-roster-artifact.md"
        record = DESIGN_DIR / "steps" / "step-05-record.md"
        self.assertTrue(source.is_file())
        res = self.run_specimen([source, record], "Step 5")
        self.assert_rollup(res, "NOT PROVEN", 2)
        self.assert_in_stdout(res, "board chair")

    def test_specimen_step20_set_s5_e26_form(self):
        # Predecessor Step 20 set, S5-E26 form. NOT RUNNABLE, with its
        # reason recorded in this form: the source named for this set,
        # design/research/step10-round-2-threshold-record.md, holds a
        # Step 10 threshold record and not a Step 20 specimen record
        # set, so no Step 20 specimen run can be made and no specimen
        # expectation is asserted on that record or on any substitute
        # subject. No specimen is invented to fill the gap. The test
        # asserts nothing on the Step 10 threshold record.
        self.require_product()
        source = (DESIGN_DIR / "research"
                  / "step10-round-2-threshold-record.md")
        self.assertTrue(source.is_file())
        self.fail("NOT RUNNABLE: the named source holds a Step 10 "
                  "threshold record and not a Step 20 specimen record "
                  "set, so the Step 20 specimen test cannot run")

    def test_specimen_step4_set_s5_e49_form_amended_set(self):
        # This build Step 4 set, S5-E49 form, on the amended supplied
        # set the C2-3 settlement names: the Step 4 record set as it
        # stands in this build records, the six Step 4 step records in
        # design/steps/, plus the evidence register file,
        # design/preplan/evidence-register.md, named as a supplied
        # record for the specimen run. The fixture record for this
        # specimen is the closed list at STEP4_SUPPLIED_SET in this
        # class head: the run names exactly the files in that list,
        # and the expected result rests only on inputs in that list,
        # under the general specimen rule the settlement adopts for
        # every specimen criterion in brief section 10. Expected, from
        # AC-16 as the settlement leaves it: PASS, exit code 0, with
        # the C6 bound, the freshness standing limits, the basis bound
        # and the coverage line of claimed seats 0 and coverage not
        # applicable printed beside the rollup. The source rule at
        # brief section 5.6 stands unamended and stands not restated
        # here.
        paths = []
        for relative in self.STEP4_SUPPLIED_SET:
            path = DESIGN_DIR / relative
            self.assertTrue(path.is_file(),
                            "supplied record stands missing: %s"
                            % relative)
            paths.append(path)
        res = self.run_specimen(paths, "Step 4")
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "coverage not applicable")
        stage_line = [c for c in self.agentic(res)["coverage"]
                      if c["scope"] == "stage"][0]
        self.assertEqual(stage_line["total"], 0)
        self.assertEqual(stage_line["checked"], 0)

    def test_specimen_step3_set_s5_e59_form(self):
        # This build Step 3 set, S5-E59 form: specimen rollup NOT PROVEN
        # on the linkage limb at exit code 2, on the indeterminate limb
        # for the research and imagination teams.
        # Source: the one record file this test supplies,
        # design/steps/step-03-record.md.
        source = DESIGN_DIR / "steps" / "step-03-record.md"
        self.assertTrue(source.is_file())
        res = self.run_specimen([source], "Step 3")
        self.assert_rollup(res, "NOT PROVEN", 2)
        self.assert_in_stdout(res, "linkage")


class TestStep12Roster(MusterCase):
    """The Step 12 roster test, a named test of this suite.

    Subject: a real Step 12 roster, produced by a Step 12 of a build,
    with full ids for both seatings kept distinct (the Step 12 seating
    and the plan loop seating). No synthetic roster stands in for it, and
    it does not stand in the TM-TEST-1 regression set. Its result is
    recorded in the Step 13 test record beside the suite results, stated
    as run or as not run with its reason, under the home decision at plan
    section 2. The counts only bound at TM-CORE-COUNT-5 stands until this
    test runs, and no identity is asserted in either direction before it
    runs.
    """

    def test_step12_roster_full_ids_both_seatings(self):
        # The subject of this test is the roster artifact standing in
        # the Step 12 step record set, as the home decision at plan
        # section 2 names it: the preserved roster artifact of Step 12,
        # holding both seatings, the Step 12 seating and the plan loop
        # seating, with full ids for both seatings kept distinct. The
        # test binds to that artifact by that identity only. No other
        # Step 12 record stands in for it, and no first match over a
        # name pattern is taken as its subject. Where no preserved
        # artifact with full ids for both seatings stands, the test
        # records NOT RUNNABLE with that reason, inside the test, and
        # substitutes nothing.
        self.require_product()
        import re
        steps_dir = DESIGN_DIR / "steps"
        artifacts = [path for path in sorted(steps_dir.glob("step-12-*.md"))
                     if "roster" in path.name]
        full_id = re.compile(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-"
            r"[0-9a-f]{12}")

        def seating_id_sets(text):
            """Identifier sets tied to each seating, by section.

            The artifact text is split at its headings. A section
            belongs to the Step 12 seating where its heading names
            Step 12, and to the plan loop seating where its heading
            names the plan loop. A seating set stands only where a
            section of that seating carries at least one full
            identifier under its own heading. Identifiers standing
            outside every seating section tie to no seating.
            """
            sets = {"step12": set(), "planloop": set()}
            current = None
            for line in text.splitlines():
                if line.lstrip().startswith("#"):
                    lowered = line.lower()
                    if "plan loop" in lowered:
                        current = "planloop"
                    elif "step 12" in lowered:
                        current = "step12"
                    else:
                        current = None
                elif current is not None:
                    sets[current].update(full_id.findall(line))
            return sets

        subject = None
        for path in artifacts:
            text = path.read_text(encoding="utf-8", errors="replace")
            sets = seating_id_sets(text)
            # Acceptance ties an identifier set to each seating: each
            # seating carries its own set under its own heading, the
            # two sets are disjoint, with full ids for both seatings
            # kept distinct, and together they carry at least two
            # distinct full identifiers. Phrase presence and
            # identifiers anywhere in the file alone do not accept a
            # candidate.
            if (sets["step12"] and sets["planloop"]
                    and sets["step12"].isdisjoint(sets["planloop"])
                    and len(sets["step12"] | sets["planloop"]) >= 2):
                subject = (path, text, sets)
                break
        if subject is None:
            self.fail(
                "NOT RUNNABLE: no preserved roster artifact with full "
                "ids for both seatings stands in the Step 12 step "
                "record set, so the Step 12 roster test cannot run")
        path, text, sets = subject
        args = [str(path), "--stage", "Step 12",
                "--runner", "Fixture Auditor", "--capacity", "Auditor"]
        res = self.invoke(args)
        agentic = self.agentic(res)
        holders = {seat["holder"] for seat in agentic["seats"]
                   if full_id.fullmatch(str(seat.get("holder", "")))}
        self.assertTrue(holders)
        # The reported holders are checked against the identifier set
        # of the seatings together, as the union of the two tied sets
        # and against no wider text, and the run reports holders from
        # each seating set, so each seating stands evidenced in the
        # run and not only in the artifact.
        self.assertTrue(
            holders <= (sets["step12"] | sets["planloop"]))
        self.assertTrue(holders & sets["step12"])
        self.assertTrue(holders & sets["planloop"])
        self.assertTrue(agentic["counts"])
