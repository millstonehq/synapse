"""Cross-check the review table without running any evaluator."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent / "corpus"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ExpectedSemanticsTests(unittest.TestCase):
    def test_expected_table_matches_each_fixture_byte_for_byte_as_data(self) -> None:
        table = read(ROOT / "expected.json")
        self.assertEqual(1, table["schema_version"])
        self.assertEqual(14, len(table["cases"]))
        for fixture_path in sorted(ROOT.glob("[0-9][0-9]-*.json")):
            fixture = read(fixture_path)
            with self.subTest(case=fixture["id"]):
                self.assertEqual(fixture["expected"], table["cases"][fixture["id"]])

    def test_expected_table_has_no_orphan_or_duplicate_case_ids(self) -> None:
        files = {p.stem for p in ROOT.glob("[0-9][0-9]-*.json")}
        table = read(ROOT / "expected.json")["cases"]
        self.assertEqual(files, set(table))
        self.assertEqual(len(table), len(set(table)))

    def test_each_case_names_a_discriminating_semantic_control(self) -> None:
        table = read(ROOT / "expected.json")["cases"]
        self.assertEqual("supported", table["01-correlated-positive"]["semantic_verdict"])
        self.assertEqual("unresolved", table["02-surface-mismatch"]["semantic_verdict"])
        self.assertEqual("supported", table["03-post-without-creation"]["semantic_verdict"])
        self.assertEqual("refuted", table["08-rejection-versus-missing"]["semantic_verdict"])
        self.assertEqual("conflicting", table["09-support-and-refutation"]["semantic_verdict"])
        self.assertEqual("inconsistent-premises", table["11-compatible-history-sets"]["operational_status"])
        self.assertEqual("unresolved", table["14-bounded-no-resend"]["semantic_verdict"])


if __name__ == "__main__":
    unittest.main()
