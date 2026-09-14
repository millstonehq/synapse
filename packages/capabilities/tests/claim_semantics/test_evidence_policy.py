"""Evaluator-independent proof that corpus semantics compile into policy IR."""
import json
import unittest
from pathlib import Path

from .adapter import ROOT, bundle_payload, load_fixture
from capcov.claims import EvidenceEffect, bundle_from_json, canonical_json, schema_digest


class EvidencePolicyCompilationTests(unittest.TestCase):
    def test_every_fixture_has_authoritative_evidence_and_real_rules(self):
        for path in sorted(ROOT.glob("[0-9][0-9]-*.json")):
            fixture = json.loads(path.read_text())
            bundle = load_fixture(path)
            with self.subTest(case=fixture["id"]):
                self.assertTrue(bundle.evidence)
                self.assertTrue(bundle.rules)
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

    def test_malformed_evidence_policy_is_rejected(self):
        payload = bundle_payload(json.loads((ROOT / "01-correlated-positive.json").read_text()))
        payload["evidence"][0]["depends_on"] = ["missing-id"]
        with self.assertRaises(ValueError): bundle_from_json(payload, validate=True)
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


if __name__ == "__main__":
    unittest.main()
