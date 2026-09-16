"""Producer-class authority for the target-go causal-trace primitives, end to end.

Only ``target-go-runtime-trace-v2`` may admit ``runtime_function_entered``,
``runtime_sql_executed``, ``runtime_tx_committed`` and
``runtime_route_completed``.  An unauthorized source fails at ingestion
(``evidence-producer``) and both kernels report ``invalid-input``; they do
not evaluate the unauthorized facts.  The committed receipt is the producer
input; nothing here fabricates a run.
"""
from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from capcov.claims import ValidationError, assert_valid, validate_bundle
from capcov.claims.differential import run_python, run_souffle
from capcov.claims.evaluator import evaluate
from capcov.claims.static.combine import combine
from capcov.claims.static.runtime_receipt import (TRACE_PRIMITIVE_DECLS, TRACE_PRODUCER,
                                                 fixture_index_facts, load_runtime_receipt,
                                                 runtime_bundle)

try:
    from .static_rules.adapter import pack_bundle
except ImportError:
    from static_rules.adapter import pack_bundle

COMMITTED_RECEIPT = (Path(__file__).resolve().parent / "target_go" / "artifacts"
                     / "runtime-recipient-route.json")
UNAUTHORIZED = "generic-json"


def _joined(producer: str):
    receipt = load_runtime_receipt(COMMITTED_RECEIPT)
    runtime = runtime_bundle(receipt, producer=producer)
    index, facts, evidence = fixture_index_facts(receipt.run)
    return combine(pack_bundle(), runtime, facts=facts, evidence=evidence, validate=False), receipt, index


@unittest.skipUnless(COMMITTED_RECEIPT.is_file(),
                     "committed target-go runtime receipt fixture is missing")
class RuntimeProducerAuthorityTest(unittest.TestCase):
    def test_trace_primitives_admit_only_the_declared_class(self) -> None:
        self.assertTrue(all(decl.producer_classes == (TRACE_PRODUCER,)
                            for decl in TRACE_PRIMITIVE_DECLS))

    def test_authorized_receipt_validates_and_both_ingestion_paths_accept_it(self) -> None:
        bundle, _, _ = _joined(TRACE_PRODUCER)
        self.assertEqual(validate_bundle(bundle), ())
        assert_valid(bundle)
        report = evaluate(bundle)
        self.assertEqual(report.status.value, "complete", report.message)
        python = run_python(bundle)
        self.assertIsNone(python.operational_failure, python.message)

    def test_unauthorized_producer_fails_closed_at_ingestion(self) -> None:
        bundle, _, _ = _joined(UNAUTHORIZED)
        issues = validate_bundle(bundle)
        codes = {issue.code for issue in issues}
        self.assertIn("evidence-producer", codes)
        # every causal-trace fact is refused, not just one
        producer_issues = [issue for issue in issues if issue.code == "evidence-producer"]
        self.assertGreaterEqual(len(producer_issues), 4)
        relations = {issue.message.split(" admits", 1)[0].strip("'") for issue in producer_issues
                     if "admits" in issue.message}
        self.assertTrue({"runtime_function_entered", "runtime_sql_executed",
                         "runtime_tx_committed", "runtime_route_completed"} <= relations)
        with self.assertRaises(ValidationError) as ctx:
            assert_valid(bundle)
        self.assertTrue(any(issue.code == "evidence-producer" for issue in ctx.exception.issues))

    def test_python_kernel_does_not_evaluate_unauthorized_facts(self) -> None:
        bundle, _, _ = _joined(UNAUTHORIZED)
        report = evaluate(bundle)
        self.assertEqual(report.status.value, "invalid-input")
        self.assertIn("evidence-producer", report.message)
        self.assertEqual(report.relations, ())
        python = run_python(bundle)
        self.assertEqual(python.operational_failure, "invalid-input")
        # the differential wrapper still lists declared names; no derived row
        self.assertTrue(all(rows == () for _, rows in python.relations))
        self.assertEqual(dict(python.relations).get("runtime_sql_executed"), ())

    @unittest.skipUnless(shutil.which("souffle"),
                         "souffle must be on PATH: run inside the nix devShell")
    def test_souffle_kernel_does_not_evaluate_unauthorized_facts(self) -> None:
        bundle, _, _ = _joined(UNAUTHORIZED)
        souffle = run_souffle(bundle)
        self.assertEqual(souffle.operational_failure, "invalid-input")
        self.assertIn("evidence-producer", souffle.message)
        self.assertEqual(souffle.relations, ())
        authorized, _, _ = _joined(TRACE_PRODUCER)
        ok = run_souffle(authorized)
        self.assertIsNone(ok.operational_failure, ok.message)
        self.assertTrue(dict(ok.relations).get("runtime_sql_executed"))


if __name__ == "__main__":
    unittest.main()
