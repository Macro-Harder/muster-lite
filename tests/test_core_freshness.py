"""Slice 3 at C4: TM-CORE-FRESH-1 to TM-CORE-FRESH-3.

Settled note, standing with the freshness tests in words: held item
H-7 (claim kind determinism) stands settled by Manager settlement,
the use versus mention rule. The determination fixtures for that rule
stand encoded in the held parts of this module, at
TestFreshnessFamilies for the negation marker kind and at
TestFreshnessClaimedAndUnclaimed for the remaining marker kinds, the
third Red shape, and the unmarked fallback, in the held block own
terms: one fixture per mention marker kind, each showing its family
unclaimed with the standing limit printed, and a candidate sentence
with no marker counting as asserted. The markers name mention shapes
only, and no phrase list of assertions stands as a fixture in this
module. The encoding covers the settled determination only, and
forms outside it stand as they stood. The remaining fixtures in this
module are the fixtures whose claiming facts the settled text at
brief section 5.5 determines in their own form.
"""

from tests.support import MusterCase, roster_text, sid

AUDIT = [("Colour lens Red", 1, "counted in base"),
         ("Colour lens Blue", 2, "counted in base"),
         ("Colour lens Purple", 3, "counted in base")]
BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]


def fresh_files(claim_line, context_text=None, roster_extra=()):
    files = {"roster.md": roster_text(
        teams=[("Audit team", None, AUDIT)], board=BOARD,
        extra_lines=list(roster_extra),
        claim_lines=[claim_line] if claim_line else [])}
    if context_text is not None:
        files["context.md"] = context_text
    return files


def mention_files(claim_line):
    """A staffed stage whose checks all pass, with one candidate line.

    The roster stands complete on the form the PASS fixtures in this
    suite use, so the rollup stands at PASS unless the candidate line
    claims a family or engages a bar. Used by the settled H-7
    determination fixtures in this module.
    """
    return {"roster.md": roster_text(
        teams=[("Audit team", None, AUDIT),
               ("Write tests team", None,
                [("Test author", 4, "counted in base")])],
        board=BOARD,
        extra_lines=["Board chair: holder %s." % sid(13),
                     "Audit plan: the fixture audit plan names the "
                     "colours Red, Blue and Purple."],
        claim_lines=[claim_line] if claim_line else [])}


def unclaimed_line(result):
    for line in result.stdout.splitlines():
        if line.startswith("Unclaimed freshness families:"):
            return line
    return ""


def claimed_unstated_line(result):
    for line in result.stdout.splitlines():
        if line.startswith(
                "Claimed freshness families with facts not stated:"):
            return line
    return ""


class TestFreshnessFamilies(MusterCase):
    """TM-CORE-FRESH-1, the four families on stated facts."""

    def run_fresh(self, files, context=()):
        return self.run_stage(files, context=context)[0]

    def family_words(self, res):
        return {c["kind"]: c["verdict"]
                for c in self.agentic(res)["checks"]
                if "freshness" in c["kind"]}

    def test_family1_re_auditor_who_fixed_in_same_round_fails(self):
        files = fresh_files(
            "Freshness claim: family 1 held for this stage.",
            context_text=("# Context\n\nHolding: fixer in Round 1, holder "
                          "%s.\n" % sid(1)),
            roster_extra=["Re auditor seat for Round 1: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("FAIL", self.family_words(res).values())

    def test_family1_fixer_holding_naming_no_round_not_proven(self):
        files = fresh_files(
            "Freshness claim: family 1 held for this stage.",
            context_text=("# Context\n\nHolding: fixer, holder %s, round "
                          "not stated.\n" % sid(9)),
            roster_extra=["Re auditor seat for Round 1: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("NOT PROVEN", self.family_words(res).values())
        self.assert_in_stdout(res, "round for that holding")

    def test_family1_no_re_auditor_seat_not_proven(self):
        files = fresh_files(
            "Freshness claim: family 1 held for this stage.",
            context_text=("# Context\n\nHolding: fixer in Round 1, holder "
                          "%s.\n" % sid(9)))
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("NOT PROVEN", self.family_words(res).values())
        self.assert_in_stdout(res, "re auditor identifier")

    def test_family2_attacker_with_build_seat_fails(self):
        files = fresh_files(
            "Freshness claim: family 2 held for this stage.",
            context_text=("# Context\n\nHolding: build team seat, holder "
                          "%s.\n" % sid(1)),
            roster_extra=["Attacker seat at the break it step: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("FAIL", self.family_words(res).values())

    def test_family2_attacker_with_step15_audit_seat_fails(self):
        files = fresh_files(
            "Freshness claim: family 2 held for this stage.",
            context_text=("# Context\n\nHolding: Step 15 audit seat, "
                          "holder %s.\n" % sid(1)),
            roster_extra=["Attacker seat at the break it step: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("FAIL", self.family_words(res).values())

    def test_family1_proven_breach_governs_over_no_round_holding(self):
        # A proven family 1 breach in one round and a fixer holding
        # naming no round stand in the same family in one fixture: the
        # proven breach governs over the partly stated shape, and the
        # family gives FAIL, not the NOT PROVEN of the no round shape.
        files = fresh_files(
            "Freshness claim: family 1 held for this stage.",
            context_text=("# Context\n\nHolding: fixer in Round 1, "
                          "holder %s.\n\nHolding: fixer, holder %s, "
                          "round not stated.\n" % (sid(1), sid(9))),
            roster_extra=["Re auditor seat for Round 1: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("FAIL", self.family_words(res).values())
        self.assert_rollup(res, "FAIL", 1)

    def test_family2_no_attacker_seat_not_proven(self):
        files = fresh_files(
            "Freshness claim: family 2 held for this stage.",
            context_text=("# Context\n\nHolding: build team seat, holder "
                          "%s.\n" % sid(9)))
        res = self.run_fresh(files, context=["context.md"])
        self.assert_in_stdout(res, "attacker identifier")

    def test_family3_first_user_with_any_prior_seat_fails(self):
        files = fresh_files(
            "Freshness claim: family 3 held for this stage.",
            context_text=("# Context\n\nHolding: any prior seat, holder "
                          "%s.\n" % sid(2)),
            roster_extra=["First user seat: holder %s." % sid(2)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("FAIL", self.family_words(res).values())

    def test_family4_assessor_with_involvement_fails(self):
        files = fresh_files(
            "Freshness claim: family 4 held for this stage.",
            context_text=("# Context\n\nInvolvement: producing, holder "
                          "%s.\n" % sid(50)),
            roster_extra=["Assessor seat for this stage: holder %s."
                          % sid(50)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("FAIL", self.family_words(res).values())

    def test_family4_no_match_and_one_unestablished_gives_not_proven(self):
        files = fresh_files(
            "Freshness claim: family 4 held for this stage.",
            context_text=("# Context\n\nInvolvement: producing, holder "
                          "%s.\n" % sid(99)),
            roster_extra=["Assessor seat for this stage: holder %s."
                          % sid(50),
                          "Assessor seat for this stage: holder not "
                          "recorded."])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("NOT PROVEN", self.family_words(res).values())
        self.assert_in_stdout(res, "assessor identifier")

    def test_family4_pass_only_where_all_established_and_no_match(self):
        files = fresh_files(
            "Freshness claim: family 4 held for this stage.",
            context_text=("# Context\n\nInvolvement: producing, holder "
                          "%s.\n" % sid(99)),
            roster_extra=["Assessor seat for this stage: holder %s."
                          % sid(50)])
        res = self.run_fresh(files, context=["context.md"])
        self.assertIn("PASS", self.family_words(res).values())

    def test_self_audit_presented_as_audit_takes_critical(self):
        files = fresh_files(
            "Freshness claim: family 1 held for this stage. The re audit "
            "is presented as audit of the round the holder fixed.",
            context_text=("# Context\n\nHolding: fixer in Round 1, holder "
                          "%s.\n" % sid(1)),
            roster_extra=["Re auditor seat for Round 1: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        self.assert_in_stdout(res, "Critical")

    def test_proven_breach_removes_holder_from_count(self):
        files = fresh_files(
            "Freshness claim: family 1 held for this stage.",
            context_text=("# Context\n\nHolding: fixer in Round 1, holder "
                          "%s.\n" % sid(1)),
            roster_extra=["Re auditor seat for Round 1: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        counts = {c["name"]: c for c in self.agentic(res)["counts"]}
        self.assertLess(counts["Audit team"]["counted_total"], 3)

    def test_mention_negation_of_the_claim_does_not_claim_family(self):
        # Settled H-7 determination, held part of TM-CORE-FRESH-1: the
        # negation marker kind. The only candidate sentence for family
        # 1 negates the claim itself, so it is a mention under the use
        # versus mention rule: family 1 stands unclaimed, its standing
        # limit prints in the slot 8 line under S5-E27, and the
        # unclaimed family does not cap the rollup.
        res = self.run_fresh(mention_files(
            "Freshness note: no claim is made that the family 1 "
            "exclusion held for this stage."))
        self.assert_rollup(res, "PASS", 0)
        self.assertIn("family 1", unclaimed_line(res).lower())
        self.assertNotIn("family 1",
                         claimed_unstated_line(res).lower())

    def test_holder_value_not_an_identifier_gives_not_proven(self):
        files = fresh_files(
            "Freshness claim: family 2 held for this stage.",
            context_text=("# Context\n\nHolding: build team seat, holder "
                          "placeholder value.\n"),
            roster_extra=["Attacker seat at the break it step: holder %s."
                          % sid(1)])
        res = self.run_fresh(files, context=["context.md"])
        self.assert_in_stdout(res, "holder identifier")


class TestFreshnessClaimedAndUnclaimed(MusterCase):
    """TM-CORE-FRESH-2 and TM-CORE-FRESH-3.

    Settled note for the held part of this group: the claiming
    determination under H-7 stands encoded here under the Manager
    settlement, the use versus mention rule, in the held block own
    terms. The fixtures below carry one candidate sentence per mention
    marker kind not already carried at TM-CORE-FRESH-1, the third Red
    shape in the form the build records name it, and the unmarked
    fallback. Each marker fixture shows its family unclaimed, the
    standing limit printed under S5-E27, and no rollup cap from that
    family. The markers name mention shapes only.
    """

    def test_claimed_family_facts_not_stated_not_proven_and_caps(self):
        files = fresh_files("Freshness claim: family 3 held for this stage.")
        res = self.run_stage(files)[0]
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")

    def test_unclaimed_family_prints_as_limit_and_does_not_cap(self):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."])}
        res = self.run_stage(files)[0]
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "Unclaimed freshness families:")

    def test_family_facts_in_judged_records_run_without_context(self):
        files = fresh_files(
            "Freshness claim: family 4 held for this stage.",
            roster_extra=["Assessor seat for this stage: holder %s."
                          % sid(50),
                          "Involvement stated in this record: producing, "
                          "holder %s." % sid(99)])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "FAIL")

    def test_family_needing_unsupplied_record_not_proven_context_named(self):
        files = fresh_files("Freshness claim: family 1 held for this stage.")
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "NOT PROVEN")

    def test_mention_quotation_or_citation_does_not_claim_family(self):
        # Marker kind: a quotation or citation of another record
        # claim. The only candidate sentence for family 2 cites the
        # step record claim in order to dispute it, so it is a
        # mention: family 2 stands unclaimed with its standing limit
        # printed, and the rollup is not capped by that family.
        res = self.run_stage(mention_files(
            "Freshness note: the step record for this stage is quoted "
            "here as claiming that the family 2 exclusion held; this "
            "record cites that claim to dispute it."))[0]
        self.assert_rollup(res, "PASS", 0)
        self.assertIn("family 2", unclaimed_line(res).lower())
        self.assertNotIn("family 2",
                         claimed_unstated_line(res).lower())

    def test_mention_conditional_marker_does_not_claim_family(self):
        # Marker kind: a conditional marker making the assertion
        # depend on an unstated condition. The only candidate sentence
        # for family 3 is conditional, so it is a mention: family 3
        # stands unclaimed with its standing limit printed.
        res = self.run_stage(mention_files(
            "Freshness note: if the holding records are supplied, "
            "the family 3 exclusion would be claimed as held for "
            "this stage."))[0]
        self.assert_rollup(res, "PASS", 0)
        self.assertIn("family 3", unclaimed_line(res).lower())
        self.assertNotIn("family 3",
                         claimed_unstated_line(res).lower())

    def test_mention_future_or_open_marker_does_not_claim_family(self):
        # Marker kind: a future or open marker stating the claim as
        # not yet made or not yet settled. The only candidate sentence
        # for family 4 is in that form, so it is a mention: family 4
        # stands unclaimed with its standing limit printed.
        res = self.run_stage(mention_files(
            "Freshness note: whether the family 4 exclusion held for "
            "this stage remains open and is not yet settled."))[0]
        self.assert_rollup(res, "PASS", 0)
        self.assertIn("family 4", unclaimed_line(res).lower())
        self.assertNotIn("family 4",
                         claimed_unstated_line(res).lower())

    def test_red_shape_family_remains_open_passage_is_a_mention(self):
        # The third Red shape, in the form the build records name it
        # at the H-7 register entry: a freshness passage stating that
        # family 3 remains open because a prior holding is possible.
        # Under the settled rule the passage is a mention, decided
        # deterministically: family 3 stands unclaimed, its standing
        # limit prints, and the rollup is not capped by that family.
        res = self.run_stage(mention_files(
            "Freshness passage: family 3 remains open because the "
            "first user may have held a prior seat."))[0]
        self.assert_rollup(res, "PASS", 0)
        self.assertIn("family 3", unclaimed_line(res).lower())
        self.assertNotIn("family 3",
                         claimed_unstated_line(res).lower())

    def test_unmarked_candidate_sentence_counts_as_asserted(self):
        # The unmarked fallback of the settled rule: a candidate
        # sentence with no marker counts as asserted. This plain
        # assertion claims family 2, its facts stand not stated, and
        # the claimed family takes NOT PROVEN and caps the rollup, in
        # the claimed with facts not stated line.
        files = fresh_files(
            "Freshness claim: family 2 held for this stage.")
        res = self.run_stage(files)[0]
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")
        self.assertIn("family 2", claimed_unstated_line(res).lower())
        self.assertNotIn("family 2", unclaimed_line(res).lower())

    def test_context_files_supplied_are_named_in_every_form(self):
        files = fresh_files(
            "Freshness claim: family 3 held for this stage.",
            context_text="# Context\n\nNo holdings stated.\n")
        res = self.run_stage(files, context=["context.md"])[0]
        self.assert_in_stdout(res, "context.md")
