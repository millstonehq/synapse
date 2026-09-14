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
OPERATIONAL = {
    "complete", "incomplete", "inconsistent-premises", "complete-with-discrepancy",
}


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
                for section in ("claims", "facts", "assumptions"):
                    self.assertIsInstance(fixture[section], list)
                    self.assertEqual(
                        len(fixture[section]),
                        len({entry["id"] for entry in fixture[section]}),
                        f"duplicate {section} IDs",
                    )
                for claim in fixture["claims"]:
                    self.assertIsInstance(claim["predicate"], str)
                    self.assertIsInstance(claim["arguments"], dict)
                for leaf in [*fixture["facts"], *fixture["assumptions"]]:
                    self.assertIsInstance(leaf["predicate"], str)
                    self.assertIsInstance(leaf["arguments"], dict)
                expected = fixture["expected"]
                self.assertIn(expected["semantic_verdict"], VERDICTS)
                self.assertIn(expected["operational_status"], OPERATIONAL)
                for key in ("required_leaves", "forbidden_leaves", "discrepancies", "missing_premises"):
                    self.assertIn(key, expected)
                    self.assertIsInstance(expected[key], list)

    def test_leaf_references_are_reviewable(self) -> None:
        for path in FIXTURES:
            fixture = load(path)
            leaves = {entry["id"] for entry in fixture["facts"] + fixture["assumptions"]}
            expected = fixture["expected"]
            with self.subTest(path=path.name):
                self.assertTrue(set(expected["required_leaves"]) <= leaves)
                self.assertTrue(set(expected["forbidden_leaves"]) <= leaves)
                self.assertTrue(set(expected["required_leaves"]).isdisjoint(expected["forbidden_leaves"]))

    def test_provenance_marks_only_the_external_execution_as_real(self) -> None:
        self.assertEqual([], [p.name for p in FIXTURES if load(p)["provenance"]["kind"] == "real"])


if __name__ == "__main__":
    unittest.main()
