"""The one place the replay review tables meet an engine (Phase 4, judge side).

Every reviewed expectation is compared with the Python reference evaluator
and, when Souffle is on PATH, both kernels are compared through the
fail-closed differential.  A disagreement is a finding to investigate, never
a reason to edit the expectation in place.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest

try:
    from .replay_rules.adapter import CASES_DIR, case_paths, load_case, load_pack, read_json
    from .replay_rules.cases import CLOSE, CREATE, INDEX, RUN
except ImportError:  # unittest discover -s imports this directory as top-level
    from replay_rules.adapter import CASES_DIR, case_paths, load_case, load_pack, read_json
    from replay_rules.cases import CLOSE, CREATE, INDEX, RUN

from capcov.claims import canonical_json
from capcov.claims.differential import DifferentialMismatch, compare
from capcov.claims.evaluator import evaluate
from capcov.claims.output import VerifiedProofEvidence, render_outputs


def sorted_json(values):
    return sorted(canonical_json(value) for value in values)


class PythonEvaluatorAgreesWithReviewedExpectations(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = load_pack()

    def _report(self, stem: str):
        return evaluate(load_case(CASES_DIR / f"{stem}.json", self.pack))

    def test_every_claim_matches_its_reviewed_table(self) -> None:
        for path in case_paths():
            case = read_json(path)
            bundle = load_case(path, self.pack)
            report = evaluate(bundle)
            with self.subTest(case=path.name):
                self.assertEqual(report.status.value, "complete", report.message)
                self.assertEqual({entry.claim.id for entry in report.claims}, set(case["expected"]["claims"]))
            evidence_ids = {record.id for record in bundle.evidence}
            for entry in report.claims:
                expected = case["expected"]["claims"][entry.claim.id]
                result = entry.result
                with self.subTest(case=path.name, claim=entry.claim.id):
                    self.assertEqual(result.semantic.value, expected["semantic_verdict"])
                    self.assertEqual(result.operational.value, expected["operational_status"])
                    self.assertEqual(sorted(result.support), expected["support_leaves"])
                    self.assertEqual(sorted(result.refutation), expected["refutation_leaves"])
                    self.assertEqual(sorted_json(result.missing_premises), sorted_json(expected["missing_premises"]))
                    leaves = set(result.support) | set(result.refutation)
                    proof = VerifiedProofEvidence.from_bundle(bundle, entry.claim.id, leaves) if leaves else None
                    rendered = render_outputs(bundle, entry.claim.id, evidence_ids, proof,
                                              claim_state=result.semantic.value)
                    discrepancies = [item["fields"] for item in rendered if item["kind"] == "discrepancy"]
                    self.assertEqual(sorted_json(discrepancies), sorted_json(expected["discrepancies"]))
                    self.assertEqual(result.basis.value, "derivational")
                    # an unresolved op_qualified names exactly one absent leaf
                    if result.semantic.value == "unresolved":
                        self.assertEqual(len(result.missing_premises), 1)
                        missing = {item["relation"] for item in result.missing_premises}
                        rendered_missing = render_outputs(bundle, entry.claim.id, evidence_ids, None,
                                                          "unresolved", missing)
                        self.assertEqual([item["relation"] for item in rendered_missing], sorted(missing))

    def test_control_case_qualifies_exactly_the_two_declared_ops(self) -> None:
        report = self._report("00-positive-control")
        self.assertEqual(set(report.relation_rows("op_qualified")), {(INDEX, RUN, CREATE), (INDEX, RUN, CLOSE)})
        self.assertEqual(set(report.relation_rows("op_qualified_rt")), set(report.relation_rows("op_qualified")))
        self.assertEqual(set(report.relation_rows("replayed")), {(RUN, CREATE), (RUN, CLOSE)})
        self.assertEqual(set(report.relation_rows("corpus_constrains")), {(RUN, CREATE), (RUN, CLOSE)})
        self.assertEqual(len(report.relation_rows("php_model_agree")), 3)
        self.assertEqual(len(report.relation_rows("go_model_agree")), 3)
        for empty in ("php_model_disagree", "go_model_disagree", "undeclared_write", "surviving_mutant",
                      "kill_closure_gap", "replay_run_stale", "php_disagree_any", "go_disagree_any", "undeclared_any"):
            self.assertEqual(report.relation_rows(empty), (), empty)
        self.assertEqual(report.relation_rows("replay_run_current"), ((RUN,),))

    def test_planted_faults_derive_exactly_their_blocker(self) -> None:
        report = self._report("01-planted-disagreement")
        self.assertEqual(len(report.relation_rows("php_model_disagree")), 1)
        self.assertEqual(report.relation_rows("go_model_disagree"), ())
        self.assertEqual(set(report.relation_rows("php_disagree_any")), {(RUN, CLOSE)})
        self.assertEqual(set(report.relation_rows("op_qualified")), {(INDEX, RUN, CREATE)})
        report = self._report("02-planted-undeclared-write")
        self.assertEqual(set(report.relation_rows("undeclared_write")), {(RUN, CLOSE, "audit_log")})
        self.assertEqual(set(report.relation_rows("op_qualified")), {(INDEX, RUN, CREATE)})
        report = self._report("03-surviving-mutant")
        self.assertEqual(set(report.relation_rows("surviving_mutant")), {(RUN, CLOSE, "m-2")})
        self.assertEqual(set(report.relation_rows("corpus_constrains")), {(RUN, CREATE)})
        self.assertEqual(set(report.relation_rows("op_qualified")), {(INDEX, RUN, CREATE)})

    def test_missing_witnesses_leave_no_derived_rows_behind(self) -> None:
        report = self._report("04-missing-model-witness")
        for relation in ("php_model_agree", "php_model_disagree", "go_model_agree", "go_model_disagree",
                         "corpus_constrains", "op_surviving_closed", "php_disagreement_closed",
                         "undeclared_writes_closed", "op_qualified_rt", "op_qualified"):
            self.assertEqual(report.relation_rows(relation), (), relation)
        self.assertEqual(report.relation_rows("replay_run_current"), ((RUN,),))
        report = self._report("05-missing-snapshot-witness")
        self.assertEqual(report.relation_rows("replay_run_current"), ())
        self.assertEqual(report.relation_rows("replay_run_stale"), ())
        self.assertEqual(len(report.relation_rows("php_model_agree")), 3)
        self.assertEqual(report.relation_rows("op_qualified"), ())

    def test_stale_case_derives_replay_run_stale_and_not_replay_run_current(self) -> None:
        report = self._report("06-stale-replay")
        self.assertEqual(report.relation_rows("replay_run_current"), ())
        self.assertEqual(len(report.relation_rows("replay_run_stale")), 1)
        self.assertEqual(report.relation_rows("op_qualified"), ())

    def test_lying_closure_qualifies_both_ops_and_exposes_the_gap(self) -> None:
        report = self._report("08-lying-closure")
        self.assertEqual(set(report.relation_rows("kill_closure_gap")), {(RUN, "m-1", "req-9")})
        self.assertEqual(set(report.relation_rows("mutant_killed_in")), {(RUN, "m-1"), (RUN, "m-2")})
        self.assertEqual(report.relation_rows("surviving_mutant"), ())
        self.assertEqual(set(report.relation_rows("op_qualified")), {(INDEX, RUN, CREATE), (INDEX, RUN, CLOSE)})


    def test_missing_post_state_is_a_gap_only_the_gate_catches(self) -> None:
        report = self._report("09-missing-post-state")
        self.assertEqual(set(report.relation_rows("post_state_gap")), {(RUN, "req-3", "php")})
        self.assertEqual(set(report.relation_rows("post_state_any")), {(RUN, CREATE)})
        # the hole the gate closes: op_exercised and both disagreement closures still hold for issues.create
        self.assertIn((RUN, CREATE), set(report.relation_rows("op_exercised")))
        self.assertIn((RUN, CREATE), set(report.relation_rows("php_disagreement_closed")))
        self.assertEqual(report.relation_rows("php_disagree_any"), ())
        self.assertEqual(set(report.relation_rows("op_qualified")), {(INDEX, RUN, CLOSE)})


class PackMutationsFailTheCorpus(unittest.TestCase):
    """Dropping a post-state closure input, or the gate, is caught by the corpus."""

    def _mutated(self, mutate):
        pack = json.loads(json.dumps(load_pack()))
        mutate(pack)
        return pack

    def _create_verdict(self, pack) -> str:
        report = evaluate(load_case(CASES_DIR / "09-missing-post-state.json", pack))
        self.assertEqual(report.status.value, "complete", report.message)
        return next(entry.result.semantic.value for entry in report.claims if entry.claim.id == "claim-qualified-create")

    def test_the_reviewed_pack_leaves_the_planted_gap_unresolved(self) -> None:
        self.assertEqual(self._create_verdict(load_pack()), "unresolved")

    def test_dropping_the_gate_from_op_qualified_rt_flips_the_case(self) -> None:
        def drop_gate(pack):
            rule = next(r for r in pack["rules"] if r["name"] == "op_qualified_rt")
            rule["body"] = [a for a in rule["body"] if a.get("relation") not in {"post_state_any", "post_state_gap_closed"}]
        self.assertEqual(self._create_verdict(self._mutated(drop_gate)), "supported")

    def test_dropping_the_post_state_closure_from_a_closure_rule_flips_a_witnessless_variant(self) -> None:
        # With php_post_states_closed withheld the gate is open only because the
        # closures that carry it are absent; a closure rule that no longer lists
        # the witness re-admits the omission.
        case = read_json(CASES_DIR / "09-missing-post-state.json")
        case["facts"] = [f for f in case["facts"] if f["relation"] != "php_post_states_closed"]
        case["outputs"] = [o for o in case["outputs"]
                           if not (set(o.get("excludes_evidence", ())) & {f["id"] for f in read_json(CASES_DIR / "09-missing-post-state.json")["facts"] if f["relation"] == "php_post_states_closed"})]
        from capcov.claims import bundle_from_json
        try:
            from .replay_rules.adapter import bundle_payload
        except ImportError:
            from replay_rules.adapter import bundle_payload

        def verdict(pack):
            report = evaluate(bundle_from_json(bundle_payload(case, pack), validate=True))
            self.assertEqual(report.status.value, "complete", report.message)
            return next(entry.result.semantic.value for entry in report.claims if entry.claim.id == "claim-qualified-create")

        self.assertEqual(verdict(load_pack()), "unresolved")

        def drop_witness_inputs_and_the_php_gap_rule(pack):
            for name in ("php_disagreement_closed", "post_state_gap_closed"):
                rule = next(r for r in pack["rules"] if r["name"] == name)
                rule["body"] = [a for a in rule["body"] if a.get("relation") != "php_post_states_closed"]
            pack["rules"] = [r for r in pack["rules"] if r["name"] != "post_state_gap_php"]
        # with the witness no longer an input to either closure and no PHP gap
        # rule, the omitted post-state is admitted: the inputs are load-bearing
        self.assertEqual(verdict(self._mutated(drop_witness_inputs_and_the_php_gap_rule)), "supported")

        def drop_from_one_closure(pack):
            rule = next(r for r in pack["rules"] if r["name"] == "php_disagreement_closed")
            rule["body"] = [a for a in rule["body"] if a.get("relation") != "php_post_states_closed"]
        # one closure alone cannot re-admit it: the gate still needs post_state_gap_closed
        self.assertEqual(verdict(self._mutated(drop_from_one_closure)), "unresolved")

        def drop_witness_inputs_but_keep_the_gap_rule(pack):
            for name in ("php_disagreement_closed", "post_state_gap_closed"):
                rule = next(r for r in pack["rules"] if r["name"] == name)
                rule["body"] = [a for a in rule["body"] if a.get("relation") != "php_post_states_closed"]
            rule = next(r for r in pack["rules"] if r["name"] == "php_observed_closed")
            rule["body"] = [{"relation": "replay_requests_closed", "terms": [{"variable": "Run"}]}]
        # the gap rule alone still catches the omission once its closure is derivable
        self.assertEqual(verdict(self._mutated(drop_witness_inputs_but_keep_the_gap_rule)), "unresolved")


@unittest.skipIf(shutil.which("souffle") is None, "souffle is not on PATH; run inside the nix devShell")
class SouffleAgreesWithPythonOnEveryReplayCase(unittest.TestCase):
    def test_kernels_agree_on_closure_and_verdicts(self) -> None:
        pack = load_pack()
        replay_root = tempfile.mkdtemp(prefix="capcov-replay-differential-")
        try:
            for path in case_paths():
                bundle = load_case(path, pack)
                with self.subTest(case=path.name):
                    try:
                        result = compare(bundle, replay_root=replay_root)
                    except DifferentialMismatch as exc:
                        self.fail(f"kernels disagree on {path.name}; replay bundle: {exc.result.replay_path}; "
                                  f"python={exc.result.python.operational_failure!r} "
                                  f"souffle={exc.result.souffle.operational_failure!r} {exc.result.souffle.message[:400]}")
                    self.assertTrue(result.matched)
                    self.assertIsNone(result.python.operational_failure)
                    self.assertIsNone(result.souffle.operational_failure)
                    self.assertEqual(result.python.canonical_digest, result.souffle.canonical_digest)
        finally:
            shutil.rmtree(replay_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
