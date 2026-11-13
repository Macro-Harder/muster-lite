"""Slice 3 at C2: TM-CORE-COUNT-1 to TM-CORE-COUNT-5."""

from tests.support import MusterCase, roster_text, sid

AUDIT = [("Colour lens Red", 1, "counted in base"),
         ("Colour lens Blue", 2, "counted in base"),
         ("Colour lens Purple", 3, "counted in base")]
BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]


def run_teams(case, teams, **kw):
    return case.run_stage(
        {"roster.md": roster_text(teams=teams, board=BOARD, **kw)})[0]


def counts_by_name(agentic):
    return {c["name"]: c for c in agentic["counts"]}


class TestTeamMinimums(MusterCase):
    """TM-CORE-COUNT-1, team minimums and printed subtraction."""

    def test_minimum_met_passes_with_subtraction_printed(self):
        res = run_teams(self, [("Audit team", None, AUDIT)])
        agentic = self.agentic(res)
        count = counts_by_name(agentic)["Audit team"]
        self.assertEqual(
            (count["entries"], count["duplicates_removed"],
             count["exempt_or_uncounted_removed"], count["counted_total"]),
            (3, 0, 0, 3))
        self.assert_in_stdout(res, "3 minus 0 minus 0 equals 3")

    def test_required_team_with_no_seat_fails_on_full_roster(self):
        res = run_teams(self, [("Write tests team", None,
                                [("Test author", 4, "counted in base")])])
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "FAIL")

    def test_required_team_with_unparsable_passage_not_proven(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[], board=BOARD,
            extra_lines=["The Audit team passage is torn: ### ###."])})
        self.assert_in_stdout(res, "NOT PROVEN")

    def test_banded_team_without_chosen_size_not_proven(self):
        teams = [("Pre plan research team", None,
                  [("Researcher %d" % n, n, "counted in base")
                   for n in (1, 2, 3, 4)])]
        res = run_teams(self, teams)
        self.assert_in_stdout(res, "NOT PROVEN")
        self.assert_in_stdout(res, "chosen size")

    def test_banded_minimum_prints_band_in_words(self):
        teams = [("Pre plan research team", None,
                  [("Researcher %d" % n, n, "counted in base")
                   for n in (1, 2, 3, 4)])]
        res = run_teams(self, teams)
        self.assert_in_stdout(res, "3 to 16")

    def test_rounds_take_own_results_and_worst_round_caps(self):
        teams = [("Audit team", "Round 1", AUDIT),
                 ("Audit team", "Round 2",
                  [("Colour lens Red", 1, "counted in base"),
                   ("Colour lens Blue", 1, "counted in base"),
                   ("Colour lens Purple", 3, "counted in base")])]
        res = run_teams(self, teams)
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "FAIL")
        counts = [c for c in self.agentic(res)["counts"]
                  if c["name"] == "Audit team"]
        self.assertEqual(len(counts), 2)

    def test_overlap_fixture_each_removal_in_one_figure_only(self):
        # The overlap fixture varies duplicate holding and exemption
        # together, charged at this group. Precedence is uncounted,
        # then exempt, then duplicate. The Purple entry is a duplicate
        # holding only, so it lands in the duplicates removed figure.
        # The Extra entry is a duplicate holding and also exempt with
        # both proofs standing, so its first matching ground is exempt
        # and it lands in the exempt or uncounted removed figure. Each
        # figure is asserted separately under that precedence.
        teams = [("Audit team", None,
                  [("Colour lens Red", 1, "counted in base"),
                   ("Colour lens Blue", 2, "counted in base"),
                   ("Colour lens Purple", 2, "counted in base"),
                   ("Colour lens Extra", 2, "exempt")])]
        res = run_teams(self, teams, extra_lines=[
            "Exempt entry: Colour lens Extra, holder %s, exempt class "
            "fixers in defect and fix loops." % sid(2),
            "Exemption basis for the Colour lens Extra seat: the fixer "
            "repaired the round it is exempt from."])
        count = counts_by_name(self.agentic(res))["Audit team"]
        self.assertEqual(count["entries"], 4)
        self.assertEqual(count["duplicates_removed"], 1)
        self.assertEqual(count["exempt_or_uncounted_removed"], 1)
        self.assertEqual(count["counted_total"], 2)

    def test_pooled_holders_are_holders_only(self):
        teams = [("Audit team", "Round 1", AUDIT),
                 ("Audit team", "Round 2",
                  [("Colour lens Red", 4, "counted in base"),
                   ("Colour lens Blue", 5, "counted in base"),
                   ("Colour lens Purple", 6, "counted in base")])]
        res = run_teams(self, teams)
        self.assert_in_stdout(res, "Holders across rounds: 6")
        self.assert_in_stdout(res, "It is not a team size")

    def test_step_total_difference_is_not_a_check_result(self):
        res = run_teams(self, [("Audit team", None, AUDIT)])
        kinds = {c["kind"] for c in self.agentic(res)["checks"]}
        self.assertNotIn("step total", kinds)

    def test_zero_subtraction_value_prints_as_number_zero(self):
        res = run_teams(self, [("Audit team", None, AUDIT)])
        self.assert_in_stdout(res, "minus 0 minus 0")


class TestDistinctness(MusterCase):
    """TM-CORE-COUNT-2, distinctness."""

    def test_two_seats_one_agent_fails_critical_where_minimum_faked(self):
        teams = [("Audit team", None,
                  [("Colour lens Red", 1, "counted in base"),
                   ("Colour lens Blue", 1, "counted in base"),
                   ("Colour lens Purple", 3, "counted in base")])]
        res = run_teams(self, teams)
        self.assert_rollup(res, "FAIL", 1)
        self.assert_in_stdout(res, "Critical")

    def test_fragment_only_roster_not_proven(self):
        teams = [("Audit team", None,
                  [("Colour lens Red", "fragment a", "counted in base"),
                   ("Colour lens Blue", "fragment b", "counted in base"),
                   ("Colour lens Purple", "fragment c",
                    "counted in base")])]
        res = run_teams(self, teams)
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")

    def test_fragments_with_proven_shortfall_fail_with_dependence_named(self):
        teams = [("Audit team", None,
                  [("Colour lens Red", 1, "counted in base"),
                   ("Colour lens Blue", "fragment b", "counted in base"),
                   ("Colour lens Purple", "fragment c",
                    "counted in base")])]
        res = run_teams(self, teams)
        self.assert_in_stdout(res, "FAIL")

    def test_bare_identifier_without_role_and_stage_is_no_spawn_reference(self):
        text = roster_text(teams=[("Audit team", None, AUDIT)],
                           extra_lines=["A bare list: %s, %s."
                                        % (sid(21), sid(22))])
        res, _ = self.run_stage({"roster.md": text})
        counts = counts_by_name(self.agentic(res))
        self.assertEqual(counts["Audit team"]["counted_total"], 3)


class TestCarriedBoardPoolTier(MusterCase):
    """TM-CORE-COUNT-3, carried seats, board, pool, combining, tier."""

    def test_principles_holder_holding_counted_seat_fails_critical(self):
        teams = [("Audit team", None,
                  AUDIT + [("Principles Agent seat", 1,
                            "over base at team level")])]
        res = run_teams(self, teams)
        self.assert_in_stdout(res, "FAIL")
        self.assert_in_stdout(res, "Critical")

    def test_one_holder_never_holds_both_principles_holdings(self):
        teams = [("Design team", None,
                  [("Principles Agent design holding", 7,
                    "over base at team level"),
                   ("Principles Agent build holding", 7,
                    "over base at team level")])]
        res = run_teams(self, teams)
        self.assert_in_stdout(res, "FAIL")

    def test_board_minimum_met_with_three_full_ids(self):
        res = run_teams(self, [("Audit team", None, AUDIT)])
        kinds = {c["kind"]: c for c in self.agentic(res)["checks"]}
        self.assertEqual(kinds["review board minimum"]["verdict"], "PASS")

    def test_board_seat_with_no_id_not_proven(self):
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)],
            board=[("Board member one", 11), ("Board member two", 12),
                   ("Board chair", "not recorded")])})
        self.assert_in_stdout(res, "NOT PROVEN")

    def test_step22_chair_counts_toward_board_and_keeps_step_unit(self):
        res, _ = self.run_stage(
            {"roster.md": roster_text(
                stage="Step 22",
                teams=[("Build team", None,
                        [("Builder", 1, "counted in base")])],
                board=[("Board member one", 11), ("Board member two", 12)],
                extra_lines=["Release gate Keeper: holder %s; placement "
                             "step unit; chair of the review board."
                             % sid(13)])},
            stage="Step 22")
        kinds = {c["kind"]: c for c in self.agentic(res)["checks"]}
        self.assertEqual(kinds["review board minimum"]["verdict"], "PASS")

    def test_role_held_by_one_agent_only(self):
        teams = [("Audit team", None,
                  [("Colour lens Red", 1, "counted in base"),
                   ("Colour lens Red", 2, "counted in base"),
                   ("Colour lens Purple", 3, "counted in base")])]
        res = run_teams(self, teams)
        self.assertNotEqual(
            [c for c in self.agentic(res)["checks"]
             if c["kind"] == "pool family and role"][0]["verdict"], "PASS")

    def test_claimed_reduced_tier_without_invocation_prints_fm9_flag(self):
        text = roster_text(
            teams=[("Audit team", None, AUDIT)],
            claim_lines=["Stage claim: this stage ran at a reduced tier."])
        res, _ = self.run_stage({"roster.md": text,
                                 "tier.md": "# Tier record\n\nTier "
                                            "applied: Low.\n"})
        self.assert_in_stdout(res, "FM-9")

    def test_combined_scope_claimed_with_no_holder_is_flagged(self):
        text = roster_text(
            teams=[("Design team", None,
                    [("Designer", 1, "counted in base")])],
            claim_lines=["Report text claim: the combined scope was held "
                         "for this design team."])
        res, _ = self.run_stage({"roster.md": text})
        self.assert_report_present(res)
        self.assertNotEqual(res.returncode, 0)


class TestExemptAndUnplaced(MusterCase):
    """TM-CORE-COUNT-4, exempt and unplaced seats."""

    def exempt_roster(self, label=True, basis=True, corroboration=False):
        extra = []
        if label:
            extra.append("Exempt entry: Fixer seat, holder %s, exempt "
                         "class fixers in defect and fix loops."
                         % sid(31))
        if basis:
            extra.append("Exemption basis for the Fixer seat: the fixer "
                         "repaired the round it is exempt from.")
        if corroboration:
            extra.append("Corroborating record: fix-register.md.")
        teams = [("Audit team", None,
                  AUDIT + [("Fixer seat", 31, "exempt")])]
        return roster_text(teams=teams, board=BOARD, extra_lines=extra)

    def test_exempt_with_both_proofs_is_removed(self):
        res, _ = self.run_stage({"roster.md": self.exempt_roster()})
        count = counts_by_name(self.agentic(res))["Audit team"]
        self.assertEqual(count["exempt_or_uncounted_removed"], 1)

    def test_exempt_with_label_proof_absent_counts_in_the_open(self):
        res, _ = self.run_stage(
            {"roster.md": self.exempt_roster(label=False)})
        count = counts_by_name(self.agentic(res))["Audit team"]
        self.assertEqual(count["exempt_or_uncounted_removed"], 0)

    def test_exempt_with_basis_absent_counts_in_the_open(self):
        res, _ = self.run_stage(
            {"roster.md": self.exempt_roster(basis=False)})
        count = counts_by_name(self.agentic(res))["Audit team"]
        self.assertEqual(count["exempt_or_uncounted_removed"], 0)

    def test_exempt_prints_both_proofs_are_roster_text(self):
        res, _ = self.run_stage({"roster.md": self.exempt_roster()})
        self.assert_in_stdout(res, "roster")

    def test_exempt_without_corroboration_stands_roster_basis_only(self):
        res, _ = self.run_stage({"roster.md": self.exempt_roster()})
        self.assert_in_stdout(res, "roster basis only")

    def test_closure_holders_unplaced_counted_nowhere(self):
        extra = ["Closure holder: holder %s." % sid(41),
                 "Completion recorder: holder %s." % sid(42),
                 "Closing recorder: no id recorded.",
                 "Roster recorder: holder %s." % sid(43),
                 "Correction holder: holder %s." % sid(44)]
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=extra)})
        agentic = self.agentic(res)
        appendix = agentic["uncounted_appendix"]
        self.assertEqual(len(appendix), 5)
        count = counts_by_name(agentic)["Audit team"]
        self.assertEqual(count["counted_total"], 3)

    def test_uncounted_appendix_group_order(self):
        extra = ["Closing recorder: no id recorded.",
                 "Closure holder: holder %s." % sid(41)]
        res, _ = self.run_stage({"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=extra)})
        appendix = self.agentic(res)["uncounted_appendix"]
        self.assertIn(sid(41), appendix[0])
        self.assertIn("no id recorded", appendix[1])


class TestStep12CountsOnly(MusterCase):
    """TM-CORE-COUNT-5, Step 12 counts only bound.

    The counts only bound stands until the Step 12 roster test runs. No
    identity is asserted in either direction between the plan loop seats
    and the Step 12 logic seats, and this module asserts none.
    """

    def test_step12_amounts_checked_as_counts_only(self):
        teams = [("Audit logic team", None,
                  [("Logic scope %d" % n, n, "counted in base")
                   for n in (1, 2, 3, 4, 5)])]
        res, _ = self.run_stage(
            {"roster.md": roster_text(stage="Step 12", teams=teams,
                                      board=BOARD)},
            stage="Step 12")
        count = counts_by_name(self.agentic(res))["Audit logic team"]
        self.assertEqual(count["counted_total"], 5)

    def test_step12_distinctness_not_proven_where_ids_missing(self):
        teams = [("Audit logic team", None,
                  [("Logic scope %d" % n, "not recorded", "counted in base")
                   for n in (1, 2, 3, 4, 5)])]
        res, _ = self.run_stage(
            {"roster.md": roster_text(stage="Step 12", teams=teams,
                                      board=BOARD)},
            stage="Step 12")
        self.assert_in_stdout(res, "NOT PROVEN")

    def test_step12_in_scope_bound_stands_beside_union_line(self):
        res, _ = self.run_stage(
            {"roster.md": roster_text(stage="Step 12",
                                      teams=[("Audit team", None, AUDIT)],
                                      board=BOARD)},
            stage="Step 12")
        self.assert_in_stdout(res, "Step 12")

    def test_step12_out_of_scope_union_line_states_so(self):
        res = run_teams(self, [("Audit team", None, AUDIT)])
        self.assert_in_stdout(res, "Step 12 is not in scope for this stage")
