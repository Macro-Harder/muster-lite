"""Slice 3 at C3: TM-CORE-LINK-1, TM-CORE-LINK-2, TM-CORE-LINK-3.

Settled note, standing with this module in words: held item H-7 (claim
kind determinism) stands settled by Manager settlement, the use versus
mention rule, and its determination fixtures stand encoded in the held
parts of this module: at TM-CORE-LINK-1, a mention moving no seat and
no coverage figure; at TM-CORE-LINK-2, a mention standing beside a
join PASS; and at TM-CORE-LINK-3, one fixture per mention marker kind
for the assertion bar, the two register Red shapes, and the unmarked
fallback, each showing the assertion bar not engaging on a mention
and engaging on an unmarked assertion. The markers name mention
shapes only, and no phrase list of assertions stands as a fixture in
this module. Held item C2-3 stands settled by its own settlement; its
specimen encoding stands in tests/test_step13_share.py, and no test
in this module states a specimen expectation. Each encoding covers
the settled determination only, and forms outside it stand as they
stood.
"""

from tests.support import MusterCase, roster_text, sid

AUDIT = [("Colour lens Red", 1, "counted in base"),
         ("Colour lens Blue", 2, "counted in base"),
         ("Colour lens Purple", 3, "counted in base")]
BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]


def notes_product(author_ids, name="notes.md"):
    parts = []
    for index, author in enumerate(author_ids, start=1):
        parts.append("Part %d. Author record: %s." % (index, author))
    return "# Notes product\n\n" + "\n\n".join(parts) + "\n"


class TestLinkageClaimingStates(MusterCase):
    """TM-CORE-LINK-1, claiming, states, and coverage account."""

    def run_case(self, files, **kw):
        return self.run_stage(files, **kw)[0]

    def base_files(self, extra_lines, products=None):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=extra_lines)}
        if products:
            files.update(products)
        return files

    def test_checked_linkage_where_author_record_agrees(self):
        files = self.base_files(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12."],
            {"notes.md": notes_product([sid(1)])})
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["checked"], 1)

    def test_settled_with_no_field_seat_outside_the_check(self):
        files = self.base_files(
            ["Work product for Colour lens Red: the grill decisions "
             "register entry for this seat. The evidence register entry "
             "for this run states that the grill decisions register form "
             "carries no author record in its contract."])
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["outside"], 1)
        self.assertEqual(line["total"], 0)

    def test_unsettled_form_contract_takes_indeterminate_limb(self):
        files = self.base_files(
            ["Work product for Colour lens Red: a widget file, widget.md."],
            {"widget.md": "# Widget\n"})
        res = self.run_case(files)
        self.assert_in_stdout(res, "NOT PROVEN")
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["indeterminate"], 1)
        self.assertEqual(line["total"], 0)

    def test_product_file_alone_settles_nothing(self):
        files = self.base_files(
            ["Work product for Colour lens Red: widget.md."],
            {"widget.md": "# Widget\n\nThis file states its own template "
                          "provides an author record field.\n"})
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["indeterminate"], 1)

    def test_opposite_settlements_leave_state_unsettled(self):
        files = self.base_files(
            ["Work product for Colour lens Red: widget.md.",
             "Record A states the widget form template provides an author "
             "record field. Record B states the widget form template "
             "provides no author record field."])
        res = self.run_case(files)
        self.assert_in_stdout(res, "NOT PROVEN")

    def test_combination_any_unsettled_makes_seat_indeterminate(self):
        files = self.base_files(
            ["Work products for Colour lens Red: notes.md, a notes part "
             "under R-12, and widget.md."],
            {"notes.md": notes_product([sid(1)]),
             "widget.md": "# Widget\n"})
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["indeterminate"], 1)

    def test_combination_one_settled_field_makes_seat_claimed(self):
        files = self.base_files(
            ["Work products for Colour lens Red: notes.md, a notes part "
             "under R-12, and the grill decisions register entry for this "
             "seat, whose form the evidence register entry for this run "
             "states carries no author record in its contract."],
            {"notes.md": notes_product([sid(1)])})
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["checked"], 1)

    def test_coverage_line_prints_where_no_team_claims_linkage(self):
        res = self.run_case(self.base_files([]))
        self.assert_in_stdout(res, "coverage not applicable")
        self.assert_in_stdout(res, "claimed seats checked 0")

    def test_uncovered_forms_listed_per_stage_in_order(self):
        files = self.base_files(
            ["Work product for Colour lens Red: a zeta form product "
             "whose contract a supplied record states carries an author "
             "record field."])
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "stage"][0]
        self.assertTrue(line["uncovered_forms"])

    def test_mention_moves_no_seat_and_no_coverage_figure(self):
        # Settled H-7 determination, held part of TM-CORE-LINK-1: a
        # stage claim sentence that only mentions artefact proven
        # staffing, in the quotation form, moves no seat into or out
        # of the claimed set and changes no coverage figure. The one
        # presented seat stands claimed on its form alone, checked
        # once, exactly as the same fixture without the mention gives.
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=["Work product for Colour lens Red: notes.md, "
                         "a notes part under R-12."],
            claim_lines=["Stage claim note: the gate record claim "
                         "that staffing for this stage is artefact "
                         "proven is quoted here to dispute it."]),
            "notes.md": notes_product([sid(1)])}
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["checked"], 1)
        self.assertEqual(line["total"], 1)

    def test_claim_bearing_file_of_other_kind_presents_no_product(self):
        files = self.base_files(
            [], {"chat.md": "Work product for Colour lens Red: notes.md.\n"})
        res = self.run_case(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["total"], 0)


class TestCheckedLinkageAndJoin(MusterCase):
    """TM-CORE-LINK-2, checked linkage, disagreement, and the join."""

    def run_files(self, files):
        return self.run_stage(files)[0]

    def files_for(self, extra_lines, products=None):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=extra_lines)}
        if products:
            files.update(products)
        return files

    def linkage_word(self, res):
        kinds = {c["kind"]: c for c in self.agentic(res)["checks"]}
        return kinds["artefact linkage"]["verdict"]

    def test_every_claimed_seat_checked_and_agreeing_gives_pass(self):
        files = self.files_for(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12."],
            {"notes.md": notes_product([sid(1)])})
        self.assertEqual(self.linkage_word(self.run_files(files)), "PASS")

    def test_disagreeing_record_defect_where_staffing_provable(self):
        files = self.files_for(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12."],
            {"notes.md": notes_product([sid(77)])})
        res = self.run_files(files)
        self.assertEqual(self.linkage_word(res), "PASS")
        self.assert_in_stdout(res, "record defect")

    def test_disagreeing_record_only_linkage_gives_not_proven(self):
        files = self.files_for(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12. No other record speaks to this seat."],
            {"notes.md": notes_product([sid(77)])})
        res = self.run_files(files)
        self.assertEqual(self.linkage_word(res), "NOT PROVEN")

    def test_one_product_two_seats_fails_high_not_critical_alone(self):
        files = self.files_for(
            ["Work product for Colour lens Red and for Colour lens Blue: "
             "notes.md, a notes part under R-12."],
            {"notes.md": notes_product([sid(1)])})
        res = self.run_files(files)
        self.assert_in_stdout(res, "FAIL")
        self.assert_in_stdout(res, "High")

    def test_shared_notes_product_matches_by_full_id(self):
        files = self.files_for(
            ["Work product shared by the Audit team seats: notes.md, a "
             "notes file with per part author records."],
            {"notes.md": notes_product([sid(1), sid(2), sid(3)])})
        res = self.run_files(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["checked"], 3)

    def test_shared_product_other_form_reported_not_checked(self):
        files = self.files_for(
            ["Work product shared by the Audit team seats: papers.md, a "
             "grouped paper whose contract a supplied record states "
             "carries an author record field."],
            {"papers.md": "# Grouped paper\n"})
        res = self.run_files(files)
        line = [c for c in self.agentic(res)["coverage"]
                if c["scope"] == "Audit team"][0]
        self.assertEqual(line["checked"], 0)
        self.assertEqual(line["not_checked"], 3)

    def test_partial_coverage_with_one_agreeing_gives_pass_with_limit(self):
        files = self.files_for(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12.",
             "Work product for Colour lens Blue: a zeta form product "
             "whose contract a supplied record states carries an author "
             "record field."],
            {"notes.md": notes_product([sid(1)])})
        self.assertEqual(self.linkage_word(self.run_files(files)), "PASS")

    def test_mention_standing_beside_join_pass_keeps_pass(self):
        # Settled H-7 determination, held part of TM-CORE-LINK-2: a
        # stage claim sentence that only mentions artefact proven
        # staffing, in the future or open form, stands beside a join
        # in which every claimed seat is checked and agreeing. The
        # mention engages no bar, and the team linkage result stands
        # at PASS on the join limb alone.
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=["Work product for Colour lens Red: notes.md, "
                         "a notes part under R-12."],
            claim_lines=["Stage claim note: whether staffing for "
                         "this stage is artefact proven remains open "
                         "and is not yet settled."]),
            "notes.md": notes_product([sid(1)])}
        self.assertEqual(self.linkage_word(self.run_files(files)),
                         "PASS")

    def test_checked_with_no_agreeing_gives_not_proven(self):
        files = self.files_for(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12.",
             "Work product for Colour lens Blue: a zeta form product "
             "whose contract a supplied record states carries an author "
             "record field."],
            {"notes.md": notes_product([sid(77)])})
        res = self.run_files(files)
        self.assertEqual(self.linkage_word(res), "NOT PROVEN")


class TestUnreadableZeroAndAssertionBar(MusterCase):
    """TM-CORE-LINK-3, unreadable records, zero coverage, assertion bar.

    Settled note for the held part of this group: the assertion bar
    determination under H-7 stands encoded here under the Manager
    settlement, the use versus mention rule, in the held block own
    terms. The fixtures below carry one candidate sentence per mention
    marker kind, the two register Red shapes in the forms the build
    records name them, and the unmarked fallback. Each marker fixture
    shows the assertion bar not engaging: the stage stands staffed on
    the PASS fixture form, no seat is checked, and the run takes PASS
    with no roster evidence only naming. The fallback fixture shows
    the bar engaging on a sentence with no marker. The markers name
    mention shapes only.
    """

    def files_for(self, extra_lines, products=None):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=extra_lines)}
        if products:
            files.update(products)
        return files

    def test_truncated_product_gives_unverifiable(self):
        files = self.files_for(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12."],
            {"notes.md": "# Notes product\n\nPart 1. Author record: "
                         + sid(1)[:18]})
        res = self.run_stage(files)[0]
        kinds = {c["kind"]: c for c in self.agentic(res)["checks"]}
        self.assertEqual(kinds["artefact linkage"]["verdict"],
                         "UNVERIFIABLE")

    def test_unparsable_author_passage_gives_not_proven(self):
        files = self.files_for(
            ["Work product for Colour lens Red: notes.md, a notes part "
             "under R-12."],
            {"notes.md": "# Notes product\n\nAuthor record: ### ###.\n"})
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "NOT PROVEN")

    def test_zero_coverage_bar_names_run_roster_evidence_only(self):
        files = self.files_for(
            ["Work product for Colour lens Red: a zeta form product "
             "whose contract a supplied record states carries an author "
             "record field."])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "roster evidence only")
        from tests.support import rollup_word
        self.assertNotEqual(rollup_word(res.stdout), "PASS")

    def test_assertion_bar_engages_for_team_presenting_no_product(self):
        text = roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            claim_lines=["Stage claim: staffing for this stage is "
                         "artefact proven."])
        res = self.run_stage({"roster.md": text})[0]
        self.assert_in_stdout(res, "NOT PROVEN")
        self.assert_in_stdout(res, "roster evidence only")

    def bar_fixture(self, claim_line, register_text=None):
        """A staffed stage at PASS form, with no product presented.

        No seat is checked in this fixture, so an engaging assertion
        bar caps the rollup at NOT PROVEN and names the run roster
        evidence only, and a bar that does not engage leaves the PASS
        standing. The candidate sentence stands in the roster claim
        lines, or in a supplied stage register file where
        register_text is given.
        """
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."],
            claim_lines=[claim_line] if claim_line else [])}
        if register_text is not None:
            files["register.md"] = register_text
        return files

    def assert_bar_not_engaged(self, files):
        res = self.run_stage(files)[0]
        self.assert_rollup(res, "PASS", 0)
        self.assertNotIn("roster evidence only", res.stdout)

    def test_bar_mention_negation_of_the_claim_does_not_engage(self):
        # Marker kind: a negation of the claim itself.
        self.assert_bar_not_engaged(self.bar_fixture(
            "Stage claim note: no claim of artefact proven staffing "
            "is made for this stage."))

    def test_bar_mention_quotation_or_citation_does_not_engage(self):
        # Marker kind: a quotation or citation of another record
        # claim.
        self.assert_bar_not_engaged(self.bar_fixture(
            "Stage claim note: the gate record is quoted as claiming "
            "artefact proven staffing for this stage; this record "
            "cites that claim to dispute it."))

    def test_bar_mention_conditional_marker_does_not_engage(self):
        # Marker kind: a conditional marker making the assertion
        # depend on an unstated condition.
        self.assert_bar_not_engaged(self.bar_fixture(
            "Stage claim note: if the work products are supplied, "
            "staffing for this stage would be claimed as artefact "
            "proven."))

    def test_bar_mention_future_or_open_marker_does_not_engage(self):
        # Marker kind: a future or open marker stating the claim as
        # not yet made or not yet settled.
        self.assert_bar_not_engaged(self.bar_fixture(
            "Stage claim note: whether staffing for this stage is "
            "artefact proven remains open and is not yet settled."))

    def test_red_shape_register_quoting_to_dispute_is_a_mention(self):
        # The first Red shape, in the form the build records name it
        # at the H-7 register entry: a register quoting another stage
        # claim of artefact proven staffing in order to dispute it.
        # Under the settled rule it is a mention, decided
        # deterministically, and the assertion bar does not engage.
        self.assert_bar_not_engaged(self.bar_fixture(
            None,
            register_text=("# Stage register\n\nStage: Step 99.\n\n"
                           "The gate record claim that staffing for "
                           "this stage is artefact proven is quoted "
                           "here in order to dispute it.\n")))

    def test_red_shape_register_stating_no_claim_is_a_mention(self):
        # The second Red shape, in the form the build records name
        # it: a register sentence stating that no claim of artefact
        # proven staffing is made. Under the settled rule it is a
        # mention, and the assertion bar does not engage.
        self.assert_bar_not_engaged(self.bar_fixture(
            None,
            register_text=("# Stage register\n\nStage: Step 99.\n\n"
                           "No claim of artefact proven staffing is "
                           "made for this stage.\n")))

    def test_bar_unmarked_candidate_sentence_counts_as_asserted(self):
        # The unmarked fallback of the settled rule: a candidate
        # sentence with no marker counts as asserted. This plain
        # assertion asserts artefact proven staffing, no seat is
        # checked, and the bar engages on this team: the rollup is
        # capped at NOT PROVEN and the run is named roster evidence
        # only.
        res = self.run_stage(self.bar_fixture(
            "Stage claim: staffing for this stage is artefact "
            "proven."))[0]
        from tests.support import rollup_word
        self.assertEqual(rollup_word(res.stdout), "NOT PROVEN")
        self.assert_in_stdout(res, "roster evidence only")

    def test_assertion_bar_does_not_engage_with_one_checked_seat(self):
        files = {"roster.md": roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=["Work product for Colour lens Red: notes.md, "
                         "a notes part under R-12."],
            claim_lines=["Stage claim: staffing for this stage is "
                         "artefact proven."]),
            "notes.md": notes_product([sid(1)])}
        res = self.run_stage(files)[0]
        kinds = {c["kind"]: c for c in self.agentic(res)["checks"]}
        self.assertEqual(kinds["artefact linkage"]["verdict"], "PASS")
