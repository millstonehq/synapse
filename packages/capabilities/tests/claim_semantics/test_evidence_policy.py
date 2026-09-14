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


if __name__ == "__main__":
    unittest.main()
