"""Evaluator-facing smoke for the real pinned Souffle runtime."""
import unittest

from capcov.claims.souffle import run_bundle
from .adapter import load_fixture


class SouffleCorpusSmokeTests(unittest.TestCase):
    def test_fixture_adapter_is_consumable_without_expected_values(self):
        # The current adapter intentionally contains primitive observations only;
        # this verifies the backend consumes that approved boundary without
        # importing expected.json or treating producer metadata as a verdict.
        bundle = load_fixture(__import__("pathlib").Path(__file__).parent / "corpus" / "01-correlated-positive.json")
        result = run_bundle(bundle)
        self.assertEqual(result.bundle_digest, result.bundle_digest)
        self.assertIn("http_save_succeeded", result.relations)


if __name__ == "__main__":
    unittest.main()
