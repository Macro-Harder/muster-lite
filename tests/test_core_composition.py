"""Slice 3 at C6 and C3 to C5 order groups, composition first as tested.

TM-CORE-COMP-1, TM-CORE-COMP-2, with the D-02 stub families. The stubs
stand only inside this test suite (tests/stubs.py). The Step 13 tests
record that no stub stands in any product path: test_no_stub_in_product_path
below reads the shipped tree when it stands.
"""

from tests import stubs
from tests.support import MusterCase, roster_text, sid

AUDIT = [("Colour lens Red", 1, "counted in base"),
         ("Colour lens Blue", 2, "counted in base"),
         ("Colour lens Purple", 3, "counted in base")]
BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]


def stub_words(**overrides):
    words = {family: "PASS" for family in stubs.COMPOSING_FAMILIES}
    words.update(overrides)
    return words


class TestCompositionWithStubs(MusterCase):
    """Composition proved against stub families returning fixed words.

    D-02 form: the stubs stand on the test side only. Each test below
    sets the stub words in the test side stub families, derives the
    expected rollup from those words through the test side ladder, and
    runs the product on a fixture supplied set in the run's own supplied
    set whose records make the real composing families take those same
    words. No stub word is passed into a product run through any option,
    and no stub stands in a product path.
    """

    def run_with_stubs(self, words_by_family, files):
        self.require_product()
        family_set = stubs.stub_set(words_by_family)
        got = [family.result() for family in family_set]
        expected = stubs.compose_stub_words(got)
        res, _ = self.run_stage(files)
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), expected)
        # Beside the final rollup, the per family words the fixture is
        # stated to induce stand asserted against the words the run
        # itself reports for those families, in the Agentic form check
        # list. The team minimums and distinctness kinds stand in
        # every run and their words are required here. The review
        # board minimum and artefact linkage words are asserted where
        # the run reports those kinds, a carried seat kind is asserted
        # where the run reports a kind naming it, and the claimed
        # freshness word is asserted over the freshness kinds the run
        # reports: a non PASS freshness word must stand among them,
        # and where freshness kinds stand beside a PASS stub word
        # every one of them is PASS.
        checks = self.agentic(res)["checks"]
        by_kind = {}
        for check in checks:
            by_kind.setdefault(check["kind"], []).append(check["verdict"])
        for kind in ("team minimums", "distinctness"):
            self.assertIn(kind, by_kind)
            for verdict in by_kind[kind]:
                self.assertEqual(verdict, words_by_family[
                    "team minimums" if kind == "team minimums"
                    else "distinctness"])
        for family, kind in (("review board minimum",
                              "review board minimum"),
                             ("artefact linkage", "artefact linkage")):
            if kind in by_kind:
                for verdict in by_kind[kind]:
                    self.assertEqual(verdict, words_by_family[family])
        for kind, verdicts in by_kind.items():
            if "carried" in kind:
                for verdict in verdicts:
                    self.assertEqual(verdict,
                                     words_by_family["carried seats"])
        freshness = [verdict for kind, verdicts in by_kind.items()
                     if "freshness" in kind for verdict in verdicts]
        wanted_fresh = words_by_family["claimed freshness"]
        if wanted_fresh != "PASS":
            self.assertIn(wanted_fresh, freshness)
        elif freshness:
            self.assertEqual(freshness, ["PASS"] * len(freshness))
        return res

    def staffed_files(self, **kw):
        return {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."], **kw)}

    def test_all_pass_stubs_give_pass_rollup(self):
        self.run_with_stubs(stub_words(), self.staffed_files())

    def test_one_fail_stub_gives_fail_rollup(self):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 1, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=BOARD)}
        self.run_with_stubs(stub_words(**{"team minimums": "FAIL"}),
                            files)

    def test_fail_outranks_unverifiable_stub(self):
        # A proven shortfall FAIL stands even where truncation also
        # stands in the same fixture set.
        files = {"roster.md": roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 1, "counted in base")])],
            board=BOARD,
            extra_lines=["The rest of this roster file is truncated."])}
        self.run_with_stubs(stub_words(
            **{"team minimums": "FAIL", "distinctness": "UNVERIFIABLE"}),
            files)

    def test_unverifiable_outranks_not_proven_stub(self):
        files = {"note.md": "# A record with no roster for the stage.\n"}
        self.run_with_stubs(stub_words(
            **{"distinctness": "UNVERIFIABLE",
               "artefact linkage": "NOT PROVEN"}), files)

    def test_not_proven_outranks_pass_stub(self):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)}
        self.run_with_stubs(stub_words(
            **{"claimed freshness": "NOT PROVEN"}), files)

    def test_stub_word_set_carries_every_result_word(self):
        # Test side machinery check: this test checks the stub fixture
        # itself. It is recorded as a stub check, not as a product test.
        for word in stubs.WORDS:
            with self.subTest(word=word):
                family_set = stubs.uniform_stub_set(word)
                self.assertEqual([f.result() for f in family_set],
                                 [word] * len(stubs.COMPOSING_FAMILIES))
        self.require_product()

    def test_exit_outcomes_carried_by_stub_set(self):
        # Test side machinery check, recorded as a stub check: the stub
        # set carries the usage error and tool fault exit outcomes as
        # data beside the four result words.
        self.assertEqual(dict(stubs.EXIT_OUTCOMES)["USAGE ERROR"], 5)
        self.assertEqual(dict(stubs.EXIT_OUTCOMES)["TOOL FAULT"], 6)
        self.require_product()

    def test_no_stub_in_product_path(self):
        # Stub harness state: the stubs stand only inside the test suite.
        from tests.support import find_entry, REPO_ROOT
        entry = find_entry()
        if entry is None:
            self.fail("product does not exist: no shipped tree stands to "
                      "check for stubs, and the stub harness stands only "
                      "inside this test suite")
        tree_text = ""
        for path in REPO_ROOT.rglob("*.py"):
            if "tests" not in path.parts:
                tree_text += path.read_text(encoding="utf-8",
                                            errors="replace")
        self.assertNotIn("StubFamily", tree_text)


class TestRollupLadder(MusterCase):
    """TM-CORE-COMP-1 against real fixture stages."""

    def run_audit(self, seats, **kw):
        return self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, seats)], board=BOARD, **kw)})[0]

    def test_pass_rollup_where_every_claim_check_passes(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."])})
        self.assert_rollup(res, "PASS", 0)

    def test_proven_fail_outranks_stage_level_unverifiable(self):
        res = self.run_audit(
            [("Colour lens Red", 1, "counted in base"),
             ("Colour lens Blue", 1, "counted in base"),
             ("Colour lens Purple", 3, "counted in base")])
        self.assert_rollup(res, "FAIL", 1)

    def test_no_roster_artifact_rollup_unverifiable(self):
        res, _ = self.run_stage(
            {"note.md": "# A record with no roster for the stage.\n"})
        self.assert_rollup(res, "UNVERIFIABLE", 3)

    def test_team_level_pass_never_printed_as_stage_result(self):
        res = self.run_audit(AUDIT)
        self.assertNotIn("Stage result: PASS for Audit team", res.stdout)
        agentic = self.agentic(res)
        team_results = {t["team"]: t["result"]
                        for t in agentic.get("team_results", [])}
        # The team result is asserted as the word this fixture gives
        # it, not as membership in the four word vocabulary: on this
        # complete Audit team, whose team checks all take PASS, the
        # team result is PASS, and a merely well formed team result
        # carrying any other word fails this assertion.
        self.assertEqual(team_results.get("Audit team"), "PASS")
        self.assertIn("rollup", agentic)

    def test_non_composing_results_do_not_change_rollup(self):
        # Colour completeness NOT PROVEN beside a PASS rollup.
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13)])})
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "Colour completeness: NOT PROVEN")


class TestPerCheckSplit(MusterCase):
    """TM-CORE-COMP-2, per check split assignments."""

    def test_one_missing_record_bears_differently_on_two_checks(self):
        # One missing record, the round named in a freshness holding,
        # bears on two named checks and takes a different word on each:
        # the freshness check takes NOT PROVEN with the missing fact
        # named, and the team minimums check, which the missing round
        # does not settle, takes PASS on the complete roster.
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=["Re auditor seat for Round 1: holder %s."
                         % sid(1)],
            claim_lines=["Freshness claim: family 1 held for this "
                         "stage."]),
            "context.md": "# Context\n\nHolding: fixer, holder %s, "
                          "round not stated.\n" % sid(9)}
        res, _ = self.run_stage(files, context=["context.md"])
        kinds = {c["kind"]: c["verdict"]
                 for c in self.agentic(res)["checks"]}
        freshness = [word for kind, word in kinds.items()
                     if "freshness" in kind]
        self.assertIn("NOT PROVEN", freshness)
        self.assertEqual(kinds["team minimums"], "PASS")
        self.assert_in_stdout(res, "round for that holding")

    def test_pinned_words_are_not_reassigned_by_the_split(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD)})
        self.assert_in_stdout(res, "Colour completeness: NOT PROVEN")

    def test_split_assignment_under_stubs_matches_real_family_words(self):
        # Stub only check, recorded as such: this test asserts a local
        # stub composition result only and records no product behaviour.
        # It stands gated on the product presence, as every test in
        # this suite stands at this step, so it passes against no
        # absence and against no entry that is not the product.
        self.require_product()
        family_set = stubs.stub_set(
            stub_words(**{"team minimums": "NOT PROVEN",
                          "distinctness": "UNVERIFIABLE"}))
        self.assertEqual(
            stubs.compose_stub_words([f.result() for f in family_set]),
            "UNVERIFIABLE")
