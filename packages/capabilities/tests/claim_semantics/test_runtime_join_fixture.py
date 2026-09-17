"""Fixture-backed static/runtime correspondence (no live target-go tree required).

The committed artifact ``target_go/artifacts/runtime-recipient-route.json`` is a
real retained disposable-MariaDB receipt (schema
``capcov-target-go-runtime-route/v2``).  This module joins it to a *synthetic*
``scip_index`` through ``index_describes_run``.  That proves the typed
receipt path, producer-gated primitives, and dual-kernel derivation of
``runtime_route_reaches_sql_on_index`` when run/request/tx/surface/index
witnesses agree.

It does **not** prove that the synthetic index describes the target-go checkout.
The live pilot (``target_go/test_target_go_static_pilot.py``) is the only test that
binds the receipt's ``candidate_commit`` to an indexed tree, and it skips
unless ``CAPCOV_GO_FIXTURE_ROOT`` and the pinned Go/SCIP tools are present.
Static and runtime certificates stay independent.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from capcov.claims import Claim, Constant, Context, validate_bundle
from capcov.claims.differential import DifferentialMismatch, compare
from capcov.claims.evaluator import evaluate
from capcov.claims.static.certificate import certify, claim_conclusions, recheck
from capcov.claims.static.combine import combine
from capcov.claims.static.ground import why, why_not
from capcov.claims.static.runtime_receipt import (CANCEL_CONFIRMATION, CHANGE_SUBSCRIPTION,
                                                 CHANGE_SUBSCRIPTION_TX, RECEIPT_ENV,
                                                 TRACE_PRODUCER, fixture_index_digest,
                                                 fixture_index_facts, load_runtime_receipt,
                                                 receipt_from_env, runtime_bundle)

try:
    from .static_rules.adapter import pack_bundle
except ImportError:
    from static_rules.adapter import pack_bundle

ARTIFACTS = Path(__file__).resolve().parent / "target_go" / "artifacts"
COMMITTED_RECEIPT = ARTIFACTS / "runtime-recipient-route.json"
CLAIM_ON_INDEX = "claim-runtime-route-observed-on-index"
CLAIM_CAUSAL = "claim-runtime-route-reaches-sql-on-index"


def _claims(index: str, receipt) -> tuple[Claim, Claim]:
    return (
        Claim("runtime_route_observed_on_index",
              (Constant(index, "digest"), Constant(receipt.tenant, "symbol"),
               Constant(receipt.surface, "symbol"), Constant(receipt.run, "symbol")),
              Context.from_mapping({"index": index, "tenant": receipt.tenant,
                                    "surface": receipt.surface, "run": receipt.run}),
              id=CLAIM_ON_INDEX),
        Claim("runtime_route_reaches_sql_on_index",
              (Constant(index, "digest"), Constant(receipt.run, "symbol"),
               Constant(receipt.request_id, "symbol"), Constant(receipt.surface, "symbol"),
               Constant(CHANGE_SUBSCRIPTION, "symbol"), Constant(CHANGE_SUBSCRIPTION_TX, "symbol"),
               Constant(CANCEL_CONFIRMATION, "symbol")),
              Context.from_mapping({"index": index, "run": receipt.run,
                                    "request": receipt.request_id, "surface": receipt.surface,
                                    "tx": CHANGE_SUBSCRIPTION_TX}),
              id=CLAIM_CAUSAL),
    )


def _correspondence_bundle(receipt, *, run: str | None = None):
    index, facts, evidence = fixture_index_facts(run or receipt.run)
    return combine(pack_bundle(), runtime_bundle(receipt),
                   facts=facts, evidence=evidence, claims=_claims(index, receipt),
                   metadata={"experiment": "fixture-backed runtime correspondence",
                             "index_kind": "synthetic", "live_target_go": False}), index


@unittest.skipUnless(COMMITTED_RECEIPT.is_file(),
                     "committed target-go runtime receipt fixture is missing")
class RuntimeJoinFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = load_runtime_receipt(COMMITTED_RECEIPT)
        cls.bundle, cls.index = _correspondence_bundle(cls.receipt)
        cls.python = evaluate(cls.bundle)

    def test_committed_receipt_is_the_retained_v2_artifact(self) -> None:
        self.assertEqual(self.receipt["schema"], "capcov-target-go-runtime-route/v2")
        self.assertEqual(self.receipt.run, "claims-runtime-trace-20260915-02")
        self.assertEqual(self.receipt.request_id, self.receipt.run + "-subscribe")
        self.assertEqual(len(self.receipt["trace"]), 6)
        self.assertTrue(self.receipt.sha256)
        self.assertEqual(validate_bundle(self.bundle), ())
        # every causal-trace evidence names the admitted producer class
        for record in runtime_bundle(self.receipt).evidence:
            self.assertEqual(record.source.split(" ", 1)[0], TRACE_PRODUCER)

    def test_env_gate_is_none_when_unset_and_loads_when_set(self) -> None:
        self.assertIsNone(receipt_from_env({}))
        loaded = receipt_from_env({RECEIPT_ENV: str(COMMITTED_RECEIPT)})
        self.assertEqual(loaded.sha256, self.receipt.sha256)
        self.assertEqual(os.environ.get(RECEIPT_ENV), None)

    def test_python_kernel_derives_the_join_only_when_witnesses_agree(self) -> None:
        self.assertEqual(self.python.status.value, "complete", self.python.message)
        verdicts = {entry.claim.id: entry.result.semantic.value for entry in self.python.claims}
        self.assertEqual(verdicts[CLAIM_ON_INDEX], "supported")
        self.assertEqual(verdicts[CLAIM_CAUSAL], "supported")
        causal = (self.index, self.receipt.run, self.receipt.request_id, self.receipt.surface,
                  CHANGE_SUBSCRIPTION, CHANGE_SUBSCRIPTION_TX, CANCEL_CONFIRMATION)
        self.assertIn(causal, set(self.python.relation_rows("runtime_route_reaches_sql_on_index")))
        self.assertIn((self.index, self.receipt.run),
                      set(self.python.relation_rows("index_describes_run")))

    def test_mismatched_run_witness_stays_unresolved_never_refuted(self) -> None:
        bundle, index = _correspondence_bundle(self.receipt, run="other-run")
        report = evaluate(bundle)
        self.assertEqual(report.status.value, "complete", report.message)
        verdicts = {entry.claim.id: entry.result for entry in report.claims}
        self.assertEqual(verdicts[CLAIM_ON_INDEX].semantic.value, "unresolved")
        self.assertEqual(verdicts[CLAIM_CAUSAL].semantic.value, "unresolved")
        self.assertNotEqual(verdicts[CLAIM_CAUSAL].semantic.value, "refuted")
        self.assertEqual(report.relation_rows("runtime_route_reaches_sql_on_index"), ())
        self.assertEqual(set(report.relation_rows("index_describes_run")),
                         {(index, "other-run")})
        explanation = why_not(bundle, dict(report.relations),
                              "runtime_route_reaches_sql_on_index",
                              (index, self.receipt.run, self.receipt.request_id,
                               self.receipt.surface, CHANGE_SUBSCRIPTION,
                               CHANGE_SUBSCRIPTION_TX, CANCEL_CONFIRMATION))
        self.assertFalse(explanation["holds"])
        self.assertFalse(explanation["refuted"])
        self.assertIn("unresolved", explanation["soundiness"])
        self.assertTrue(any(item.get("relation") == "index_describes_run"
                            for item in explanation["attempts"]))

    def test_certificates_are_independent_of_the_static_path(self) -> None:
        relations = dict(self.python.relations)
        claim = next(c for c in self.bundle.claims if c.id == CLAIM_CAUSAL)
        [row] = claim_conclusions(self.bundle, relations, claim)
        certificate = certify(self.bundle, relations, claim.relation, row)
        self.assertFalse(certificate["truncated"])
        self.assertTrue(recheck(self.bundle, certificate, relations).ok)
        leaves = set(certificate["leaves"])
        self.assertTrue(any(leaf.startswith("runtime:") for leaf in leaves))
        self.assertTrue(any(":index_describes_run:" in leaf for leaf in leaves))
        self.assertTrue(any(":runtime_sql_executed:" in leaf for leaf in leaves))
        # no static call-graph leaf: this is not an end-to-end path certificate
        self.assertFalse(any(":scip_may_reference:" in leaf or ":static_edge:" in leaf
                             for leaf in leaves))
        support = why(self.bundle, relations, claim.relation, row)
        self.assertTrue(support["holds"])
        self.assertEqual(support["leaves"], certificate["leaves"])

    @unittest.skipUnless(shutil.which("souffle"),
                         "souffle must be on PATH: run inside the nix devShell")
    def test_both_kernels_agree_on_the_fixture_join(self) -> None:
        replay_root = tempfile.mkdtemp(prefix="capcov-runtime-join-fixture-")
        try:
            result = compare(self.bundle, replay_root=replay_root)
        except DifferentialMismatch as exc:
            self.fail(f"kernels disagree; replay bundle: {exc.result.replay_path}")
        finally:
            shutil.rmtree(replay_root, ignore_errors=True)
        self.assertTrue(result.matched)
        self.assertIsNone(result.python.operational_failure)
        self.assertIsNone(result.souffle.operational_failure)
        self.assertEqual(dict(result.python.relations)["runtime_route_reaches_sql_on_index"],
                         dict(result.souffle.relations)["runtime_route_reaches_sql_on_index"])
        claim = next(c for c in self.bundle.claims if c.id == CLAIM_CAUSAL)
        [row] = claim_conclusions(self.bundle, result.python.relations, claim)
        from_python = certify(self.bundle, result.python.relations, claim.relation, row)
        from_souffle = certify(self.bundle, result.souffle.relations, claim.relation, row)
        self.assertEqual(from_python, from_souffle)
        self.assertTrue(recheck(self.bundle, from_python, result.souffle.relations).ok)


class RuntimeJoinSkipGateTest(unittest.TestCase):
    def test_fixture_index_digest_is_stable_and_not_an_target_go_identity(self) -> None:
        digest = fixture_index_digest()
        self.assertEqual(len(digest), 64)
        self.assertNotEqual(digest, "0759ccef8fbb6024b7d215c8adc3019e93bfd277e112090acaa1304813323a3b")

    @unittest.skipUnless(COMMITTED_RECEIPT.is_file(), "committed receipt missing")
    def test_a_tampered_trace_is_refused_not_imported(self) -> None:
        import json
        import tempfile
        from capcov.claims.static.runtime_receipt import RuntimeReceiptError
        raw = json.loads(COMMITTED_RECEIPT.read_text(encoding="utf-8"))
        raw["trace"] = raw["trace"][:3]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(raw, handle)
            path = handle.name
        try:
            with self.assertRaises(RuntimeReceiptError):
                load_runtime_receipt(path)
        finally:
            Path(path).unlink(missing_ok=True)

    @unittest.skipUnless(COMMITTED_RECEIPT.is_file(), "committed receipt missing")
    def test_checkout_mismatch_is_refused_when_the_pilot_binds_a_head(self) -> None:
        from capcov.claims.static.runtime_receipt import RuntimeReceiptError
        with self.assertRaises(RuntimeReceiptError):
            load_runtime_receipt(COMMITTED_RECEIPT, expected_commit="0" * 40)


if __name__ == "__main__":
    unittest.main()
