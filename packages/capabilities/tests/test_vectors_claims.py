from __future__ import annotations

from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from capcov.claims.differential import run_python
from capcov.claims.ir import canonical_json
from capcov.vectors.claims import VectorClaimError, artifact_digest, build_bundle, judge
from capcov.vectors.recorder import read_vectors, record, write_vectors
from capcov.vectors.replay import read_replay, replay as replay_vectors
from capcov.vectors.schema import Operation, ReplayArtifact, ReplayResult, StepSpec, Vector, VectorsArtifact


CANDIDATE = "c" * 64
PROVENANCE = {"incumbent_commit": "a" * 40, "fixture_sha256": "f" * 64}


def pair(*, passed: bool = True, gaps=()):
    vectors = VectorsArtifact(
        operation="orders.update", template_version="boundary-v1", declared_stores="*",
        provenance=PROVENANCE,
        vectors=[Vector("orders.update:authorized", "authorized", "actor-1",
                        [StepSpec(actor="actor-1", role="permitted")],
                        {"steps": [{"status": 200}], "delta": {}, "informational": {}})],
        gaps=list(gaps), required_cells=["authorized", *[item["cell"] for item in gaps]])
    replay = ReplayArtifact(
        operation=vectors.operation, mutant=None, vectors_recorded=1,
        vectors_passing=int(passed), gaps_recorded=len(vectors.gaps),
        candidate_sha256=CANDIDATE, vectors_provenance=PROVENANCE,
        vectors_sha256=artifact_digest(vectors), run_id="run-1",
        results=[ReplayResult("orders.update:authorized", "authorized", passed,
                              None if passed else "/steps[0]/status: expected 200 got 500")])
    return vectors, replay


def verdicts(bundle):
    return {claim.key: claim for claim in run_python(bundle).claims}


class Authority:
    ok = True
    def failed_checks(self): return []


class VectorClaimTests(unittest.TestCase):
    def test_replay_producer_binds_exact_vectors_and_candidate(self):
        operation = Operation("health", "route", "custom", "http", request={"method": "GET", "path": "/health"})
        step = StepSpec(actor=None, role="anonymous", method="GET", path="/health", drain=False)
        expected = {"steps": [{"request": {"kind": "http", "method": "GET", "path": "/health",
                                                  "headers": {"Accept": "application/json"}, "body": None, "argv": []},
                                "status": 200, "body": {"ok": True}}],
                    "delta": {}, "informational": {}, "observed_by": "inspect-diff"}
        vectors = VectorsArtifact(operation.id, "boundary-v1", "*", PROVENANCE,
                                  [Vector("health:anonymous", "anonymous", None, [step], expected)],
                                  [], ["anonymous"])

        class Fixture:
            def snapshot(self): return "snapshot"
            def restore(self, token): pass
            def inspect(self): return {"rows": {}, "collections": {}, "queues": {}, "redis_keys": []}
            def drain(self): pass

        class Candidate:
            base_url = "http://127.0.0.1"
            candidate_sha256 = CANDIDATE
            def send(self, request): return 200, {"ok": True}

        with tempfile.TemporaryDirectory() as directory:
            write_vectors(Path(directory), operation, vectors)
            summary = replay_vectors([operation], Fixture(), Candidate(), directory,
                                     candidate_sha256=CANDIDATE, run_id="run-1")
            replay = read_replay(Path(directory) / "health" / "replay.json")
            self.assertEqual((Path(directory) / "health" / "vectors.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((Path(directory) / "health" / "replay.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(summary["vectors_passing"], 1)
        self.assertEqual(replay.vectors_sha256, artifact_digest(vectors))
        self.assertEqual(replay.run_id, "run-1")

    def test_replay_json_rejects_string_boolean(self):
        vectors, replay = pair()
        data = replay.to_json()
        data["results"][0]["pass"] = "false"
        with self.assertRaisesRegex(ValueError, "must be a boolean"):
            ReplayArtifact.from_json(data)

    def test_real_template_record_replay_and_claim_join(self):
        operation = Operation("sync", "command", "command", "shell",
                              request={"mode": "command", "target": "sync"})

        class Fixture:
            def snapshot(self): return "snapshot"
            def restore(self, token): pass
            def inspect(self): return {"rows": {}, "collections": {}, "queues": {}, "redis_keys": []}
            def drain(self): pass

        class Endpoint:
            candidate_sha256 = CANDIDATE
            base_url = None
            def run_shell(self, request): return 0, {"ok": True}

        fixture, endpoint = Fixture(), Endpoint()
        with tempfile.TemporaryDirectory() as directory:
            record([operation], fixture, endpoint, {}, {}, Path(directory), provenance=PROVENANCE)
            vectors = read_vectors(Path(directory) / "sync" / "vectors.json")
            replay_vectors([operation], fixture, endpoint, directory, run_id="run-real")
            replay = read_replay(Path(directory) / "sync" / "replay.json")
            bundle = build_bundle(vectors, replay)
        self.assertEqual(vectors.required_cells, ["retry", "run"])
        self.assertEqual([vector.cell for vector in vectors.vectors], ["run", "retry"])
        self.assertEqual([vector.note for vector in vectors.vectors], ["run once", "run twice"])
        self.assertEqual({claim.semantic for claim in run_python(bundle).claims}, {"supported"})

    def test_passing_vector_supports_match_and_recorded_cell(self):
        vectors, replay = pair()
        bundle = build_bundle(vectors, replay)
        got = verdicts(bundle)
        self.assertEqual([claim.semantic for claim in got.values()], ["supported", "supported"])
        self.assertEqual(dict(bundle.metadata)["vectors_sha256"], artifact_digest(vectors))
        self.assertEqual(dict(bundle.metadata)["producer_authority"], "local-unattested")
        self.assertEqual({record.kind for record in bundle.evidence
                          if record.atom.relation.startswith("vector_replay_")}, {"assumption"})

    def test_failed_vector_refutes_match_but_still_records_cell(self):
        vectors, replay = pair(passed=False)
        got = verdicts(build_bundle(vectors, replay))
        by_prefix = {key.split(":", 1)[0]: value.semantic for key, value in got.items()}
        self.assertEqual(by_prefix, {"vector-cell-recorded": "supported", "vector-match": "refuted"})

    def test_gap_is_unresolved_and_never_support(self):
        vectors, replay = pair(gaps=({"cell": "retry", "reason": "no fault injector"},))
        got = verdicts(build_bundle(vectors, replay))
        gap_claim = next(claim for key, claim in got.items()
                         if key.startswith("vector-cell-recorded:") and claim.semantic == "unresolved")
        self.assertEqual(gap_claim.operational, "complete")

    def test_exact_vectors_digest_is_required(self):
        vectors, replay = pair()
        with self.assertRaisesRegex(VectorClaimError, "exact vectors artifact"):
            build_bundle(vectors, replace(replay, vectors_sha256="0" * 64))

    def test_required_cell_cannot_disappear_from_both_vectors_and_gaps(self):
        vectors, replay = pair()
        vectors.required_cells.append("anonymous")
        replay = replace(replay, vectors_sha256=artifact_digest(vectors))
        with self.assertRaisesRegex(VectorClaimError, "required cell set"):
            build_bundle(vectors, replay)

    def test_cell_cannot_be_both_vector_and_gap(self):
        vectors, replay = pair()
        vectors.gaps.append({"cell": "authorized", "reason": "contradiction"})
        replay = replace(replay, gaps_recorded=1, vectors_sha256=artifact_digest(vectors))
        with self.assertRaisesRegex(VectorClaimError, "both vectors and gaps"):
            build_bundle(vectors, replay)

    def test_candidate_endpoint_digest_cannot_be_overridden(self):
        class Candidate:
            candidate_sha256 = "d" * 64
        from capcov.vectors.replay import _candidate_digest
        with self.assertRaisesRegex(ValueError, "disagrees"):
            _candidate_digest(Candidate(), CANDIDATE)

    def test_claim_bundle_contains_hashes_not_sensitive_vector_payloads(self):
        vectors, replay = pair()
        vectors.vectors[0].steps[0].body = {"tenant_private_marker": "do-not-publish"}
        replay = replace(replay, vectors_sha256=artifact_digest(vectors))
        rendered = canonical_json(build_bundle(vectors, replay))
        self.assertNotIn("tenant_private_marker", rendered)
        self.assertNotIn("do-not-publish", rendered)

    def test_rejects_missing_results_count_lies_and_mutants(self):
        vectors, replay = pair()
        cases = (
            replace(replay, results=[]),
            replace(replay, vectors_passing=0),
            replace(replay, mutant="skip-auth"),
        )
        for bad in cases:
            with self.subTest(bad=bad), self.assertRaises(VectorClaimError):
                build_bundle(vectors, bad)

    def test_two_kernel_agreement_produces_certificates(self):
        vectors, replay = pair()
        with tempfile.TemporaryDirectory() as directory:
            result = judge(vectors, replay, replay_root=directory,
                           python_runner=run_python,
                           souffle_runner=lambda bundle: replace(run_python(bundle), backend="souffle"),
                           authority_runner=lambda bundle: Authority())
        self.assertTrue(result.result.matched)
        self.assertEqual(len(result.certificates), 2)
        self.assertTrue(all(value["certificate_sha256"] for value in result.verdicts().values()))


if __name__ == "__main__":
    unittest.main()
