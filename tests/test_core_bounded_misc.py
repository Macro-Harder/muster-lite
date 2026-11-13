"""Slice 3 at C5: TM-CORE-BOUND-1, TM-CORE-BOUND-2, TM-CORE-MISC-1 to 3."""

import json

from tests.support import FIXTURES_DIR, MusterCase, roster_text, sid

AUDIT = [("Colour lens Red", 1, "counted in base"),
         ("Colour lens Blue", 2, "counted in base"),
         ("Colour lens Purple", 3, "counted in base")]
BOARD = [("Board member one", 11), ("Board member two", 12),
         ("Board chair", 13)]


def stage_files(extra_lines=(), claim_lines=(), extra_files=None):
    files = {"roster.md": roster_text(
        teams=[("Audit team", None, AUDIT)], board=BOARD,
        extra_lines=list(extra_lines), claim_lines=list(claim_lines))}
    if extra_files:
        files.update(extra_files)
    return files


class TestColourCompletenessBound(MusterCase):
    """TM-CORE-BOUND-1, colour completeness as a bounded gap."""

    def test_no_plan_no_charge_not_proven_missing_plan_named(self):
        res = self.run_stage(stage_files())[0]
        self.assert_in_stdout(
            res, "Colour completeness: NOT PROVEN. No audit plan or round "
                 "charge is named in the supplied records.")

    def test_named_non_qualifying_charge_uses_named_charge_form(self):
        files = stage_files(extra_lines=[
            "Round charge for Round 1: colours Red, Blue, Purple. This "
            "charge first stands in this closure record."])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "none of them qualifies")

    def test_plan_and_charge_union_with_missing_colour(self):
        files = stage_files(extra_lines=[
            "Audit plan: colours Red and Blue.",
            "Round charge, stated in the step record as opened for Round "
            "1: colours Red, Blue and Purple.",
            "Colour papers supplied: Red paper, Blue paper."])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "Missing seat: Purple")
        self.assert_in_stdout(res, "Audit plan")
        self.assert_in_stdout(res, "Round charge")

    def test_two_qualifying_charges_union(self):
        files = stage_files(extra_lines=[
            "Round charge one, stated in the step record as opened for "
            "Round 1: colours Red and Blue.",
            "Round charge two, stated in a supplied record to stand "
            "before Round 1: colour Purple.",
            "Colour papers supplied: Red paper, Blue paper."])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "Missing seat: Purple")
        self.assert_in_stdout(res, "Round charge one")
        self.assert_in_stdout(res, "Round charge two")

    def test_two_missing_colours_print_one_line_each(self):
        files = stage_files(extra_lines=[
            "Audit plan: colours Red, Blue and Purple.",
            "Colour papers supplied: Red paper."])
        res = self.run_stage(files)[0]
        self.assertEqual(res.stdout.count("Missing seat:"), 2)

    def test_colour_result_never_composes_rollup(self):
        files = stage_files(extra_lines=[
            "Board chair: holder %s." % sid(13)],
        )
        files["roster.md"] = roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13)])
        res = self.run_stage(files)[0]
        self.assert_rollup(res, "PASS", 0)
        self.assert_in_stdout(res, "Colour completeness: NOT PROVEN")


class TestPlaidBound(MusterCase):
    """TM-CORE-BOUND-2, the Plaid bound."""

    def test_plaid_target_checks_needing_amount_not_proven(self):
        files = {"roster.md": roster_text(
            stage="Plaid Stage", teams=[("Audit team", None, AUDIT)],
            board=BOARD)}
        files["tier.md"] = "# Tier record\n\nTier applied: Plaid.\n"
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "NOT PROVEN")
        from tests.support import rollup_word
        self.assertNotEqual(rollup_word(res.stdout), "PASS")

    def test_plaid_slot8_line_prints_in_fixed_form(self):
        res = self.run_stage(stage_files())[0]
        self.assert_in_stdout(
            res, "Plaid: NOT PROVEN. Version 1 of this tool computes no "
                 "Plaid figure")

    def test_non_plaid_unclaimed_plaid_limb_does_not_compose(self):
        res = self.run_stage(stage_files())[0]
        kinds = {c["kind"]: c["verdict"]
                 for c in self.agentic(res)["checks"]}
        self.assertNotIn("Plaid", [k for k, v in kinds.items()
                                   if v == "FAIL"])


class TestChainAndCompleteness(MusterCase):
    """TM-CORE-MISC-1, chain advisory and mechanical completeness."""

    def test_chain_shape_without_ordering_fact_reports_not_run(self):
        res = self.run_stage(stage_files())[0]
        self.assert_in_stdout(res, "Shape 1: not run")
        self.assert_in_stdout(res, "Shape 2: not run")
        self.assert_in_stdout(res, "Shape 3: not run")

    def test_chain_with_date_only_evidence_reports_not_run(self):
        files = stage_files(extra_lines=[
            "The roster artifact is dated 2026-11-01 and the gate record "
            "is dated 2026-11-02."])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "not run")

    def test_suspension_with_lift_is_chain_evidence_not_a_defect(self):
        files = stage_files(extra_lines=[
            "A suspension stands recorded with its release condition, "
            "and its lift stands recorded after it in that order."])
        res = self.run_stage(files)[0]
        self.assert_report_present(res)
        self.assert_in_stdout(res, "Shape 1:")
        self.assertNotIn("Chain: advisory only. Shape 1: FAIL",
                         res.stdout)

    def test_completeness_difference_landing_nowhere_prints_as_bound(self):
        files = stage_files(extra_lines=[
            "The stage register states 5 seats for this stage; the "
            "roster states 4 seats for this stage."])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "completeness difference")

    def test_ordering_failure_preventing_proof_makes_claim_not_proven(self):
        files = stage_files(extra_lines=[
            "Ordering statement: the work product stands after its seat "
            "first appears, and no earlier record settles the check."])
        res = self.run_stage(files)[0]
        self.assert_in_stdout(res, "NOT PROVEN")


class TestClaimDisagreement(MusterCase):
    """TM-CORE-MISC-2, claim disagreement and no correction."""

    def test_contradicted_claim_flagged_side_by_side_no_writes(self):
        import hashlib
        text = roster_text(
            teams=[("Audit team", None,
                    [("Colour lens Red", 1, "counted in base"),
                     ("Colour lens Blue", 1, "counted in base"),
                     ("Colour lens Purple", 3, "counted in base")])],
            board=BOARD,
            claim_lines=["Stage claim: the Audit team is fully staffed "
                         "with 3 distinct members."])
        res, paths = self.run_stage({"roster.md": text})
        self.assert_in_stdout(res, "claim disagreement")
        after = paths["roster.md"].read_bytes()
        self.assertEqual(hashlib.sha256(after).hexdigest(),
                         hashlib.sha256(text.encode()).hexdigest())

    def test_passes_as_members_text_flags_disagreement_at_high(self):
        text = roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            claim_lines=["Stage register text: the three audit passes "
                         "are members of the Audit team."])
        res = self.run_stage({"roster.md": text})[0]
        self.assert_in_stdout(res, "claim disagreement")

    def test_supplied_total_including_unplaced_entry_is_flagged(self):
        text = roster_text(
            teams=[("Audit team", None, AUDIT)], board=BOARD,
            extra_lines=["Closure holder: holder %s." % sid(41),
                         "Stage claim: the step total for this stage is "
                         "5, counting every holder named."])
        res = self.run_stage({"roster.md": text})[0]
        self.assert_in_stdout(res, "claim disagreement")

    def test_fabricated_consistent_set_takes_pass_under_the_cap(self):
        text = roster_text(
            teams=[("Audit team", None, AUDIT),
                   ("Write tests team", None,
                    [("Test author", 4, "counted in base")])],
            board=BOARD,
            extra_lines=["Board chair: holder %s." % sid(13),
                         "Audit plan: the fixture audit plan names the "
                         "colours Red, Blue and Purple."])
        res = self.run_stage({"roster.md": text})[0]
        self.assert_rollup(res, "PASS", 0)


class TestDiagnosticCatalogueAsData(MusterCase):
    """TM-CORE-MISC-3, diagnostic catalogue as data."""

    def test_catalogue_rows_carry_four_things_and_no_more(self):
        path = self.require_data_file("diagnostic-catalogue.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data["rows"]:
            self.assertEqual(set(row.keys()),
                             {"code", "kind", "shape", "rule_reference"})

    def test_catalogue_states_no_severity_anywhere(self):
        path = self.require_data_file("diagnostic-catalogue.json")
        self.assertNotIn("severity", path.read_text(encoding="utf-8"))

    def test_no_kind_row_code_stands_on_no_check_result(self):
        res = self.run_stage(stage_files(extra_lines=[
            "The stage register states 5 seats for this stage; the "
            "roster states 4 seats for this stage."]))[0]
        codes = {c.get("diagnostic_code")
                 for c in self.agentic(res)["checks"]}
        path = self.require_data_file("diagnostic-catalogue.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        no_kind = [r["code"] for r in data["rows"]
                   if r["kind"] == "no check kind"]
        for code in no_kind:
            self.assertNotIn(code, codes)

    def test_catalogue_acceptance_scoped_to_emitted_codes(self):
        record = json.loads(
            (FIXTURES_DIR / "catalogue" / "attempt-record.json")
            .read_text(encoding="utf-8"))
        self.assertIn("scoped", record["duty"])
        self.require_product()


class TestStep15Round1LongToken(MusterCase):
    """Step 15 round 1 fix round test: one long unbroken token."""

    def test_long_unbroken_token_completes_inside_a_generous_bound(self):
        # Step 15 round 1, BR-2: a single unbroken token of 20,000
        # characters, in a roster comment line and in a note file
        # beside the roster, does not hang the run: the run completes
        # inside a generous bound of 25 seconds on each staging.
        import time
        token = "A" * 20000
        stagings = (
            stage_files(extra_lines=["# " + token]),
            stage_files(extra_files={"note.md": "# Note\n\n" + token
                                     + "\n"}),
        )
        for files in stagings:
            started = time.time()
            res, _ = self.run_stage(files)
            elapsed = time.time() - started
            self.assertLess(elapsed, 25)
            self.assert_rollup(res, "PASS", 0)
