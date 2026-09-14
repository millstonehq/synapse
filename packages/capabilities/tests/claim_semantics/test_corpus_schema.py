"""Evaluator-independent validation for the Stage A semantic corpus.

These checks intentionally use only the standard library.  The corpus is a
review artifact: loading it must not import the claim evaluator or award a
verdict by executing rules.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus"
FIXTURES = sorted(CORPUS.glob("[0-9][0-9]-*.json"))
EXPECTED = CORPUS / "expected.json"

REQUIRED_TOP = {
    "schema_version", "id", "title", "provenance", "context", "claims",
    "facts", "assumptions", "expected",
}
VERDICTS = {"supported", "refuted", "unresolved", "conflicting"}
OPERATIONAL = {"complete", "incomplete", "inconsistent-premises", "out-of-scope"}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise AssertionError(f"{path} is not an object")
    return value


class CorpusSchemaTests(unittest.TestCase):
    def test_has_exactly_fourteen_numbered_fixtures(self) -> None:
        self.assertEqual(14, len(FIXTURES))
        self.assertEqual([f"{i:02d}" for i in range(1, 15)], [p.name[:2] for p in FIXTURES])

    def test_fixture_shape_is_explicit_and_evaluator_independent(self) -> None:
        ids = set()
        for path in FIXTURES:
            with self.subTest(path=path.name):
                fixture = load(path)
                self.assertTrue(REQUIRED_TOP <= fixture.keys())
                self.assertEqual(1, fixture["schema_version"])
                self.assertRegex(fixture["id"], r"^[0-9]{2}-[a-z0-9-]+$")
                self.assertEqual(path.stem, fixture["id"])
                self.assertNotIn(fixture["id"], ids)
                ids.add(fixture["id"])
                provenance = fixture["provenance"]
                self.assertIn(provenance["kind"], {"synthetic", "real"})
                self.assertIn("seeded_fault", provenance)
                self.assertIsInstance(fixture["context"], dict)
                self.assertTrue(fixture["claims"])
                schema = load(CORPUS / "schema-v1.json")
                self.assertEqual("schema-v1", fixture["schema_ref"])
                self.assertEqual(list(fixture["context"]), fixture["context_indices"])
                self.assertTrue(set(fixture["context"]) <= set(schema["context_indices"]))
                self.assertTrue(set(fixture["context"]) <= set(schema["types"]))
                for section in ("claims", "facts", "assumptions"):
                    self.assertIsInstance(fixture[section], list)
                    self.assertEqual(
                        len(fixture[section]),
                        len({entry["id"] for entry in fixture[section]}),
                        f"duplicate {section} IDs",
                    )
                for section in ("claims", "facts", "assumptions"):
                    for leaf in fixture[section]:
                        with self.subTest(section=section, leaf=leaf["id"]):
                            self.assertIn(leaf["relation"], schema["relations"])
                            relation = schema["relations"][leaf["relation"]]
                            self.assertEqual(relation["arg_order"], leaf["arg_order"])
                            self.assertEqual(leaf["args"], [leaf["arguments"].get(key) for key in leaf["arg_order"]])
                            self.assertEqual(set(fixture["context"]), set(leaf["context"]))
                            self.assertIsInstance(leaf["provenance"]["depends_on"], list)
                            known_assumptions = {a["id"] for a in fixture["assumptions"]}
                            self.assertTrue(set(leaf["provenance"]["depends_on"]) <= known_assumptions)
                            self.assertEqual(relation["modality"], "claim" if section == "claims" else "assumption" if section == "assumptions" else relation["modality"])
                            self.assertNotIn("status", leaf) if section == "facts" else None
                expected = fixture["expected"]
                self.assertEqual({c["id"] for c in fixture["claims"]}, set(expected["claims"]))
                leaves = {entry["id"] for entry in fixture["facts"] + fixture["assumptions"]}
                for claim_id, outcome in expected["claims"].items():
                    self.assertIn(outcome["semantic_verdict"], VERDICTS)
                    self.assertIn(outcome["operational_status"], OPERATIONAL)
                    for key in ("support_leaves", "refutation_leaves", "observed_leaves", "forbidden_leaves", "discrepancies", "missing_premises"):
                        self.assertIn(key, outcome)
                        self.assertIsInstance(outcome[key], list)
                    for key in ("support_leaves", "refutation_leaves", "observed_leaves", "forbidden_leaves"):
                        self.assertTrue(set(outcome[key]) <= leaves)
                    self.assertTrue(set(outcome["support_leaves"]).isdisjoint(outcome["refutation_leaves"]))
                    verdict = outcome["semantic_verdict"]
                    if verdict == "supported":
                        self.assertFalse(outcome["refutation_leaves"])
                        self.assertTrue(outcome["support_leaves"])
                    elif verdict == "refuted":
                        self.assertFalse(outcome["support_leaves"])
                        self.assertTrue(outcome["refutation_leaves"])
                    elif verdict == "conflicting":
                        self.assertTrue(outcome["support_leaves"])
                        self.assertTrue(outcome["refutation_leaves"])
                    else:
                        self.assertFalse(outcome["support_leaves"])
                        self.assertFalse(outcome["refutation_leaves"])

    def test_leaf_references_are_reviewable(self) -> None:
        for path in FIXTURES:
            fixture = load(path)
            leaves = {entry["id"] for entry in fixture["facts"] + fixture["assumptions"]}
            expected = fixture["expected"]
            with self.subTest(path=path.name):
                for outcome in expected["claims"].values():
                    support = set(outcome["support_leaves"])
                    refutation = set(outcome["refutation_leaves"])
                    observed = set(outcome["observed_leaves"])
                    forbidden = set(outcome["forbidden_leaves"])
                    self.assertTrue(support <= observed)
                    self.assertTrue(refutation <= observed)
                    self.assertTrue(forbidden.isdisjoint(support | refutation))

    def test_provenance_marks_only_the_external_execution_as_real(self) -> None:
        self.assertEqual([], [p.name for p in FIXTURES if load(p)["provenance"]["kind"] == "real"])

    def test_schema_declares_ordered_typed_polarity_and_context_metadata(self) -> None:
        schema = load(CORPUS / "schema-v1.json")
        self.assertEqual(schema["context_indices"], list(dict.fromkeys(schema["context_indices"])))
        self.assertTrue(schema["types"])
        self.assertTrue(schema["operational_statuses"])
        for name, relation in schema["relations"].items():
            with self.subTest(relation=name):
                self.assertTrue(relation["arg_order"])
                self.assertIn(relation["polarity"], {"positive", "negative", "neutral"})
                self.assertIn(relation["modality"], {"claim", "observed", "assumption", "completeness"})
                self.assertEqual(len(relation["arg_order"]), len(set(relation["arg_order"])))
                self.assertTrue(set(relation["arg_order"]) <= set(schema["types"]))


if __name__ == "__main__":
    unittest.main()
