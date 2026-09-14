"""Evaluator-independent proof that corpus semantics compile into policy IR."""
import json
import unittest
from pathlib import Path

from .adapter import ROOT, bundle_payload, load_fixture
from capcov.claims import (Bundle, Claim, Column, Constant, EvidenceEffect,
                           RelationDecl, assert_valid, bundle_from_json,
                           canonical_json, schema_digest)


class EvidencePolicyCompilationTests(unittest.TestCase):
    def test_every_fixture_has_authoritative_evidence_and_real_rules(self):
        for path in sorted(ROOT.glob("[0-9][0-9]-*.json")):
            fixture = json.loads(path.read_text())
            bundle = load_fixture(path)
            with self.subTest(case=fixture["id"]):
                self.assertTrue(bundle.evidence)
                self.assertTrue(bundle.rules or bundle.diagnostics or bundle.mappings)
                self.assertTrue(bundle.mappings)
                self.assertEqual({e.id for e in bundle.evidence},
                                 {x["id"] for x in fixture["facts"] + fixture["assumptions"]})
                self.assertNotIn('"expected"', canonical_json(bundle))

    def test_mapping_has_explicit_support_and_refutation_effects(self):
        effects = set()
        for path in ROOT.glob("[0-9][0-9]-*.json"):
            effects.update(mapping.effect for mapping in load_fixture(path).mappings)
        self.assertIn(EvidenceEffect.SUPPORT, effects)
        self.assertIn(EvidenceEffect.REFUTATION, effects)

    def test_provenance_context_and_dependencies_are_not_metadata_only(self):
        fixture = json.loads((ROOT / "07-shared-mistaken-assumption.json").read_text())
        bundle = load_fixture(ROOT / "07-shared-mistaken-assumption.json")
        records = {e.id: e for e in bundle.evidence}
        self.assertIn("assumption-false", records["fact-static"].depends_on)
        self.assertIn("assumption-false", records["fact-runtime"].depends_on)
        self.assertEqual(records["fact-static"].source, "static")
        self.assertEqual(records["fact-static"].context.as_dict()["tenant"], fixture["context"]["tenant"])

    def test_round_trip_is_canonical_and_expected_table_is_not_ingested(self):
        path = ROOT / "09-support-and-refutation.json"
        payload = bundle_payload(json.loads(path.read_text()))
        first = bundle_from_json(payload, validate=True)
        second = bundle_from_json(json.loads(canonical_json(first)), validate=True)
        self.assertEqual(schema_digest(first), schema_digest(second))
        self.assertNotIn("expected", payload)

    def test_domain_rules_require_conjunction_and_preserve_scope(self):
        positive = load_fixture(ROOT / "01-correlated-positive.json")
        rule = next(r for r in positive.rules if r.head.relation == "notification_delivery_terminal")
        self.assertEqual({a.relation for a in rule.body}, {"http_save_succeeded", "issue_changed_observed", "smtp_accepted", "sql_terminal_state"})
        scoped = load_fixture(ROOT / "11-compatible-history-sets.json")
        self.assertTrue(all(any(a.relation == "compatible_history" for a in rule.body) for rule in scoped.rules if rule.head.relation == "capability_holds_in_all_compatible_histories"))
        out_of_scope = load_fixture(ROOT / "12-unexpected-runtime-surface.json")
        self.assertFalse(any(rule.head.relation == "model_complete" for rule in out_of_scope.rules))
        self.assertTrue(any(mapping.effect == EvidenceEffect.OBSERVATION for mapping in out_of_scope.mappings))
        history = json.loads((ROOT / "11-compatible-history-sets.json").read_text())
        compatible = next(x for x in history["facts"] if x["relation"] == "compatible_history")
        self.assertEqual(["tenant", "run", "history", "capability", "outcome", "holds"], compatible["arg_order"])
        self.assertIsInstance(compatible["arguments"]["holds"], bool)
        aggregate = load_fixture(ROOT / "11-compatible-history-sets.json")
        self.assertTrue(any(rule.aggregation and rule.aggregation.operator == "all" for rule in aggregate.rules))
        self.assertIn("history_holds", {relation.name for relation in aggregate.relations})
        sql = load_fixture(ROOT / "10-revoked-assumption-alternative.json")
        self.assertTrue(any(rule.name == "row_requires_independent_current_sql" for rule in sql.rules))
        self.assertTrue(all(p.get("scope") != "global" for rule in json.loads((ROOT / "10-revoked-assumption-alternative.json").read_text())["rules"] for p in rule["premises"]))
        terminal = load_fixture(ROOT / "13-acceptance-sql-ack-failure.json")
        self.assertTrue(any(rule.head.relation == "notification_delivery_terminal" for rule in terminal.rules))
        self.assertTrue(any(d.claim_id == "claim-terminal" and d.trigger_relation == "sql_ack_failed" for d in terminal.diagnostics))

    def test_history_aggregation_requires_explicit_closed_domain_witness(self):
        bundle = load_fixture(ROOT / "11-compatible-history-sets.json")
        aggregate = [rule for rule in bundle.rules if rule.aggregation]
        self.assertEqual({rule.aggregation.closure_witness for rule in aggregate}, {"compatible_history_domain_closed"})
        self.assertTrue(all(any(atom.relation == "compatible_history_domain_closed" for atom in rule.body) for rule in aggregate))
        payload = bundle_payload(json.loads((ROOT / "11-compatible-history-sets.json").read_text()))
        payload["facts"] = [fact for fact in payload["facts"] if fact["relation"] != "compatible_history_domain_closed"]
        payload["evidence"] = [fact for fact in payload["evidence"] if fact["relation"] != "compatible_history_domain_closed"]
        missing = bundle_from_json(payload, validate=True)
        self.assertTrue(all(rule.aggregation.closure_witness == "compatible_history_domain_closed" for rule in missing.rules if rule.aggregation))

    def test_all_fixture_bundles_canonically_reingest(self):
        for path in ROOT.glob("[0-9][0-9]-*.json"):
            with self.subTest(case=path.stem):
                first = load_fixture(path)
                second = bundle_from_json(json.loads(canonical_json(first)), validate=True)
                self.assertEqual(schema_digest(first), schema_digest(second))

    def test_mixed_history_false_rows_are_observation_discrepancies(self):
        bundle = load_fixture(ROOT / "11-compatible-history-sets.json")
        self.assertTrue(all(mapping.effect == EvidenceEffect.OBSERVATION for mapping in bundle.mappings if mapping.evidence_relation == "compatible_history"))
        effects = {diagnostic.effect for diagnostic in bundle.diagnostics if diagnostic.trigger_relation == "compatible_history"}
        self.assertEqual({EvidenceEffect.OBSERVATION}, effects)

    def test_malformed_evidence_policy_is_rejected(self):
        payload = bundle_payload(json.loads((ROOT / "01-correlated-positive.json").read_text()))
        payload["evidence"][0]["depends_on"] = ["missing-id"]
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)

    def test_claim_ids_are_required_only_for_evidence_policy_bundles(self):
        relation = RelationDecl("legacy_claim", (Column("value", "symbol"),), modality="claim")
        assert_valid(Bundle((relation,), claims=(Claim("legacy_claim", (Constant("v", "symbol"),)),)))
        payload = bundle_payload(json.loads((ROOT / "01-correlated-positive.json").read_text()))
        payload["diagnostics"] = [{"trigger_relation": "smtp_accepted", "effect": "support", "operational_status": "not-a-status"}]
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)
        payload = bundle_payload(json.loads((ROOT / "01-correlated-positive.json").read_text()))
        payload["claims"][0].pop("id")
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)
        payload = bundle_payload(json.loads((ROOT / "01-correlated-positive.json").read_text()))
        payload["mappings"][0]["bindings"] = [["not-a-column", "tenant"]]
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)
        payload = bundle_payload(json.loads((ROOT / "01-correlated-positive.json").read_text()))
        payload["evidence"][0]["context"]["tenant"] = "wrong-tenant"
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)
        payload = bundle_payload(json.loads((ROOT / "01-correlated-positive.json").read_text()))
        payload["diagnostic_policy"]["revocation"] = "not-an-effect"
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)
        payload = bundle_payload(json.loads((ROOT / "12-unexpected-runtime-surface.json").read_text()))
        payload["diagnostics"][0]["predicate"]["column"] = "missing"
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)
        payload = bundle_payload(json.loads((ROOT / "12-unexpected-runtime-surface.json").read_text()))
        payload["diagnostics"][0]["predicate"]["value"] = "route-known"
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)


if __name__ == "__main__":
    unittest.main()
