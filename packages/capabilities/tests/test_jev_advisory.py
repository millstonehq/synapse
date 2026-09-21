from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from capcov.claims.cli import main as experiment_main
from capcov.claims import Modality
from capcov.claims.jev import (
    ARTIFACT_KIND, AssessmentRequest, JevError, assess, build_artifact,
    claims_bundle,
)
from capcov.claims.jev_patterns import (
    ARTIFACT_KIND as PATTERN_ARTIFACT_KIND, PatternRequest, VARIANTS,
    assess as assess_pattern, build_artifact as build_pattern_artifact,
    claims_bundle as pattern_claims_bundle,
)
from capcov.claims import jev_binding
from capcov.claims.validation import validate_bundle


def request_document() -> dict:
    return {
        "schema_version": 1,
        "subject_id": "capability:notification.unsubscribe",
        "subject": {
            "definition": "The recipient disables a notification category.",
            "route": "GET /notification-unsubscribe/{action}-email",
        },
        "candidates": [
            {
                "id": "change-subscription",
                "description": "Deletes the selected subscription and pending confirmation.",
                "evidence_ids": ["static:route-to-change"],
            },
            {
                "id": "audit-request",
                "description": "Records that the request occurred.",
                "evidence_ids": ["static:route-to-audit"],
            },
        ],
        "instructions": "Which candidate directly implements the modeled business outcome?",
        "presence_criteria": {
            "true": "At least one candidate directly creates the modeled outcome.",
            "false": "Candidates are incidental, observational, or unrelated.",
        },
    }


def api_response() -> dict:
    return {
        "model": "jev-latest",
        "answers": {
            "best_candidate": {
                "type": "choice",
                "choice": "change-subscription",
                "probabilities": {
                    "change-subscription": 0.91,
                    "audit-request": 0.04,
                    "no_match": 0.05,
                },
                "confidence": 0.88,
            },
            "has_direct_match": {"type": "noul", "noul": 0.94},
        },
        "usage": {"input_tokens": 300, "output_tokens": 20},
    }


def pattern_request_document() -> dict:
    return {
        "schema_version": 1,
        "subject_id": "patch:42",
        "pattern": {
            "id": "lost-update",
            "definition": "A read-modify-write can overwrite a concurrent update.",
            "positive_signatures": ["read and write are separated without serialization"],
            "required_evidence": ["write ordering or synchronization evidence"],
            "exclusions": ["the operation is serialized by a lock or transaction"],
        },
        "evidence": [
            {"id": "scip:read", "kind": "static", "fact": {"call": "load", "line": 20}},
            {"id": "patch:write", "kind": "patch", "fact": {"call": "store", "line": 24}},
        ],
        "missing_evidence": ["runtime interleaving trace"],
    }


def pattern_response(match: float = .8, sufficient: float = .3,
                     exclusion: float = .1) -> dict:
    return {"model": "jev-1.13.0", "answers": {
        "pattern_match": {"type": "noul", "noul": match},
        "evidence_sufficient": {"type": "noul", "noul": sufficient},
        "exclusion_applies": {"type": "noul", "noul": exclusion},
    }, "usage": {"input_tokens": 100, "output_tokens": 10}}


class JevAdvisoryTests(unittest.TestCase):
    def _judge(self, exit_code: int = 5) -> dict:
        verdict = {0: "supported", 1: "not-supported", 5: "pending-premise"}[exit_code]
        digest = "a" * 64
        from capcov.claims.souffle import compile as souffle_compile
        program = "c" * 64
        souffle = "1" * 64
        compiler = "2" * 64
        flags = ["--no-preprocessor", "-j1", "-o"]
        operation = ({"verdict": "supported", "qualification": "qualified",
                      "op_qualified": {"semantic": "supported", "operational": "complete",
                                       "missing_premises": []}}
                     if exit_code == 0 else
                     {"verdict": "not-supported",
                      "qualification": ("pending model_well_formed"
                                        if exit_code == 5 else "unsupported"),
                      "op_qualified": {"semantic": "unresolved", "operational": "complete",
                                       "missing_premises": (["model_well_formed"]
                                                            if exit_code == 5 else ["model_writes"])}})
        return {
            "schema": "capcov-compiled-judge-v1",
            "receipt": {"run": "run-17", "model": "b" * 64,
                        "snapshot": "d" * 64},
            "pack": {"id": "replay-v1", "program_digest": program},
            "compiled": {"schema": "capcov-souffle-compiled-v1",
                         "program_digest": program, "binary_sha256": "3" * 64,
                         "souffle_sha256": souffle,
                         "compiler_config_sha256": compiler,
                         "compile_flags": flags,
                         "compile_key": souffle_compile.compile_key(
                             program, souffle, flags,
                             compiler_config_sha256=compiler)},
            "kernels": {"matched": True, "closure_digest_equal": True,
                        "python_digest": digest, "souffle_digest": digest,
                        "compiled_digest": digest,
                        "souffle_closure_digest": "e" * 64,
                        "compiled_closure_digest": "e" * 64,
                        "closure_digest": "e" * 64, "failures": {}},
            "ops": {"delete-issue": {**operation, "certificate_sha256": None},
                    "corpus": {"verdict": "supported", "qualification": "qualified",
                               "op_qualified": {"semantic": "supported",
                                                "operational": "complete",
                                                "missing_premises": []},
                               "certificate_sha256": "f" * 64}},
            "required_ops": ["delete-issue"],
            "contract_findings": [],
            "verdict": verdict, "exit_code": exit_code,
        }

    def test_binding_pins_advisory_and_judge_without_changing_verdict(self) -> None:
        advisory = build_artifact(AssessmentRequest.parse(request_document()), api_response())
        judge = self._judge(5)
        binding = jev_binding.bind(advisory, judge)
        self.assertEqual(binding["judge"]["exit_code"], 5)
        self.assertEqual(binding["judge"]["verdict"], "pending-premise")
        self.assertEqual(binding["judge"]["run"], "run-17")
        self.assertEqual(binding["judge"]["model_digest"], "b" * 64)
        self.assertEqual(binding["judge"]["rule_program_digest"], "c" * 64)
        self.assertEqual(binding["judge"]["kernel_semantics_digest"], "a" * 64)
        self.assertEqual(binding["judge"]["closure_digest"], "e" * 64)
        self.assertEqual(binding["judge"]["snapshot_digest"], "d" * 64)
        self.assertEqual(binding["judge"]["certificate_digests"],
                         {"corpus": "f" * 64, "delete-issue": None})
        self.assertFalse(binding["authority"]["advisory_may_change_verdict"])
        self.assertFalse(binding["authority"]["advisory_may_satisfy_missing_premise"])
        jev_binding.validate(binding, advisory, judge)

    def test_binding_rejects_mismatch_and_kernel_or_verdict_ambiguity(self) -> None:
        advisory = build_artifact(AssessmentRequest.parse(request_document()), api_response())
        judge = self._judge()
        binding = jev_binding.bind(advisory, judge)
        changed = deepcopy(judge)
        changed["receipt"]["run"] = "other-run"
        with self.assertRaisesRegex(JevError, "binding does not match"):
            jev_binding.validate(binding, advisory, changed)

        mismatch = deepcopy(judge)
        mismatch["kernels"]["compiled_digest"] = "d" * 64
        with self.assertRaisesRegex(JevError, "semantic digests"):
            jev_binding.bind(advisory, mismatch)

        closure_mismatch = deepcopy(judge)
        closure_mismatch["kernels"]["compiled_closure_digest"] = "9" * 64
        with self.assertRaisesRegex(JevError, "closure digests"):
            jev_binding.bind(advisory, closure_mismatch)

        contradictory = deepcopy(judge)
        contradictory["verdict"] = "supported"
        with self.assertRaisesRegex(JevError, "verdict and exit code"):
            jev_binding.bind(advisory, contradictory)

        forged_compile = deepcopy(judge)
        forged_compile["compiled"]["binary_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(JevError, "binary_sha256"):
            jev_binding.bind(advisory, forged_compile)

        forged_key = deepcopy(judge)
        forged_key["compiled"]["compile_key"] = "9" * 64
        with self.assertRaisesRegex(JevError, "key does not match"):
            jev_binding.bind(advisory, forged_key)

        wrong_result = deepcopy(judge)
        wrong_result["ops"]["delete-issue"]["qualification"] = "unsupported"
        with self.assertRaisesRegex(JevError, "required operation"):
            jev_binding.bind(advisory, wrong_result)

        fake_supported = self._judge(0)
        fake_supported["ops"]["delete-issue"]["qualification"] = "unsupported"
        with self.assertRaisesRegex(JevError, "required operation"):
            jev_binding.bind(advisory, fake_supported)

        supported_with_gap = self._judge(0)
        supported_with_gap["ops"]["delete-issue"]["op_qualified"]["missing_premises"] = ["model_writes"]
        with self.assertRaisesRegex(JevError, "required operation"):
            jev_binding.bind(advisory, supported_with_gap)

        duplicate = deepcopy(judge)
        duplicate["required_ops"] = ["delete-issue", "delete-issue"]
        with self.assertRaisesRegex(JevError, "duplicates"):
            jev_binding.bind(advisory, duplicate)

        failed = deepcopy(judge)
        failed["kernels"]["failures"] = {"souffle": "timeout"}
        with self.assertRaisesRegex(JevError, "operational failures"):
            jev_binding.bind(advisory, failed)

        finding = deepcopy(judge)
        finding["contract_findings"] = ["bad receipt"]
        with self.assertRaisesRegex(JevError, "contract findings"):
            jev_binding.bind(advisory, finding)

        extended = deepcopy(advisory)
        extended["may_qualify_claim"] = True
        core = dict(extended)
        core.pop("assessment_id")
        from capcov.claims import jev as jev_module
        extended["assessment_id"] = f"jev:{jev_module._digest(core)}"
        with self.assertRaisesRegex(JevError, "unknown"):
            jev_binding.bind(extended, judge)

        missing = deepcopy(advisory)
        missing.pop("usage")
        core = dict(missing)
        core.pop("assessment_id")
        missing["assessment_id"] = f"jev:{jev_module._digest(core)}"
        with self.assertRaisesRegex(JevError, "missing usage"):
            jev_binding.bind(missing, judge)

        def readdress(document):
            document = deepcopy(document)
            document.pop("assessment_id", None)
            document["assessment_id"] = f"jev:{jev_module._digest(document)}"
            return document

        nested_extra = deepcopy(advisory)
        nested_extra["producer"]["authority"] = "invented"
        with self.assertRaisesRegex(JevError, "advisory contract"):
            jev_binding.bind(readdress(nested_extra), judge)

        wrong_request_digest = deepcopy(advisory)
        wrong_request_digest["request_sha256"] = "0" * 64
        with self.assertRaisesRegex(JevError, "digests"):
            jev_binding.bind(readdress(wrong_request_digest), judge)

        wrong_state_digest = deepcopy(advisory)
        wrong_state_digest["state_sha256"] = "0" * 64
        with self.assertRaisesRegex(JevError, "digests"):
            jev_binding.bind(readdress(wrong_state_digest), judge)

        wrong_candidates_digest = deepcopy(advisory)
        wrong_candidates_digest["candidate_set_sha256"] = "0" * 64
        with self.assertRaisesRegex(JevError, "digests"):
            jev_binding.bind(readdress(wrong_candidates_digest), judge)

        request_extra = deepcopy(advisory)
        request_extra["request"]["private_note"] = "not admitted"
        request_extra["request_sha256"] = jev_module._digest(request_extra["request"])
        with self.assertRaisesRegex(JevError, "digests|schema"):
            jev_binding.bind(readdress(request_extra), judge)

        state_extra = deepcopy(advisory)
        state_extra["request"]["state"]["private_note"] = "not admitted"
        state_extra["request_sha256"] = jev_module._digest(state_extra["request"])
        state_extra["state_sha256"] = jev_module._digest(state_extra["request"]["state"])
        with self.assertRaisesRegex(JevError, "candidates differ"):
            jev_binding.bind(readdress(state_extra), judge)

        false_response_digest = deepcopy(advisory)
        false_response_digest["response_provenance"]["canonical_sha256"] = "0" * 64
        with self.assertRaisesRegex(JevError, "canonical response digest"):
            jev_binding.bind(readdress(false_response_digest), judge)

        response_extra = deepcopy(advisory)
        response_extra["response"]["untrusted"] = True
        response_extra["response_provenance"]["canonical_sha256"] = jev_module._digest(
            response_extra["response"])
        with self.assertRaisesRegex(JevError, "response fields"):
            jev_binding.bind(readdress(response_extra), judge)

        for mutate in (
            lambda item: item["response"]["answers"]["best_candidate"].__setitem__(
                "type", "invented"),
            lambda item: item["response"]["answers"]["best_candidate"].__setitem__(
                "probabilities", "not-an-object"),
            lambda item: item["response"]["answers"]["has_direct_match"].__setitem__(
                "noul", "not-a-number"),
            lambda item: item["response"]["usage"].__setitem__(
                "input_tokens", "not-an-int"),
        ):
            malformed = deepcopy(advisory)
            mutate(malformed)
            malformed["response_provenance"]["canonical_sha256"] = jev_module._digest(
                malformed["response"])
            with self.assertRaisesRegex(JevError, "response"):
                jev_binding.bind(readdress(malformed), judge)

    def test_binding_cli_does_not_disclose_missing_input_paths(self) -> None:
        output = StringIO()
        private_path = "/private/operator/name/advisory.json"
        with redirect_stdout(output):
            self.assertEqual(experiment_main([
                "claims", "jev", "bind", "--advisory", private_path,
                "--judge", "/missing/judge.json", "--out", "/tmp/out.json"]), 3)
        self.assertNotIn(private_path, output.getvalue())

    def test_binding_cli_does_not_disclose_unwritable_output_path(self) -> None:
        advisory = build_artifact(AssessmentRequest.parse(request_document()), api_response())
        with tempfile.TemporaryDirectory() as tmp:
            advisory_path = Path(tmp) / "advisory.json"
            judge_path = Path(tmp) / "judge.json"
            advisory_path.write_text(json.dumps(advisory), encoding="utf-8")
            judge_path.write_text(json.dumps(self._judge()), encoding="utf-8")
            private_path = "/private/operator/name/out/binding.json"
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(experiment_main([
                    "claims", "jev", "bind", "--advisory", str(advisory_path),
                    "--judge", str(judge_path), "--out", private_path]), 3)
            self.assertNotIn(private_path, output.getvalue())

    def test_binding_cli_writes_content_addressed_artifact(self) -> None:
        advisory = build_artifact(AssessmentRequest.parse(request_document()), api_response())
        with tempfile.TemporaryDirectory() as tmp:
            advisory_path = Path(tmp) / "advisory.json"
            judge_path = Path(tmp) / "judge.json"
            out = Path(tmp) / "binding.json"
            advisory_path.write_text(json.dumps(advisory), encoding="utf-8")
            judge_path.write_text(json.dumps(self._judge()), encoding="utf-8")
            self.assertEqual(experiment_main([
                "claims", "jev", "bind", "--advisory", str(advisory_path),
                "--judge", str(judge_path), "--out", str(out)]), 0)
            written = json.loads(out.read_text(encoding="utf-8"))
            self.assertTrue(written["binding_id"].startswith("jev-judge:"))

    def test_pattern_packet_has_no_freeform_hypothesis_slot(self) -> None:
        request = PatternRequest.parse(pattern_request_document())
        payload = request.payload()
        self.assertEqual(set(payload["questions"]), {
            "pattern_match", "evidence_sufficient", "exclusion_applies"})
        framed = pattern_request_document()
        framed["diagnosis"] = "This is definitely a lost update."
        with self.assertRaises(JevError):
            PatternRequest.parse(framed)

    def test_pattern_variants_change_form_not_evidence_content(self) -> None:
        request = PatternRequest.parse(pattern_request_document())
        baseline = request.payload("baseline")
        reversed_packet = request.payload("reversed_evidence")
        opaque = request.payload("opaque_ids")
        self.assertEqual(list(reversed(baseline["state"]["evidence"])),
                         reversed_packet["state"]["evidence"])
        self.assertEqual(opaque["state"]["subject_id"], "subject")
        self.assertEqual([item["fact"] for item in opaque["state"]["evidence"]],
                         [item["fact"] for item in baseline["state"]["evidence"]])

    def test_pattern_sensitivity_labels_unstable_results(self) -> None:
        request = PatternRequest.parse(pattern_request_document())
        responses = {variant: pattern_response() for variant in VARIANTS}
        responses["neutral_paraphrase"] = pattern_response(match=.45)
        artifact = build_pattern_artifact(request, responses, max_spread=.2)
        self.assertEqual(artifact["kind"], PATTERN_ARTIFACT_KIND)
        self.assertFalse(artifact["sensitivity"]["stable"])
        self.assertAlmostEqual(artifact["sensitivity"]["spreads"]["pattern_match"], .35)
        self.assertEqual(artifact["evidence_semantics"]["kind"], "assumption")
        self.assertFalse(artifact["evidence_semantics"]["may_qualify_claim"])
        bundle = pattern_claims_bundle(artifact)
        self.assertEqual(validate_bundle(bundle), ())
        self.assertEqual({relation.modality for relation in bundle.relations},
                         {Modality.ASSUMPTION})
        self.assertFalse(bundle.claims)
        self.assertFalse(bundle.rules)

    def test_pattern_assessment_fans_variants_out(self) -> None:
        seen = []
        def transport(endpoint, body, headers, timeout):
            seen.append(json.loads(body))
            return json.dumps(pattern_response()).encode()
        artifact = assess_pattern(PatternRequest.parse(pattern_request_document()),
                                  max_spread=.2, api_key="secret", transport=transport)
        self.assertEqual(len(seen), 4)
        self.assertTrue(artifact["sensitivity"]["stable"])

    def test_payload_fans_out_bounded_choice_and_presence(self) -> None:
        request = AssessmentRequest.parse(request_document())
        payload = request.payload()
        self.assertEqual(set(payload["questions"]), {"best_candidate", "has_direct_match"})
        self.assertEqual(
            set(payload["questions"]["best_candidate"]["criteria"]),
            {"change-subscription", "audit-request", "no_match"},
        )
        self.assertEqual(payload["questions"]["has_direct_match"]["type"], "noul")

    def test_artifact_is_content_bound_and_explicitly_non_authoritative(self) -> None:
        request = AssessmentRequest.parse(request_document())
        first = build_artifact(request, api_response())
        second = build_artifact(request, api_response())
        self.assertEqual(first, second)
        self.assertEqual(first["kind"], ARTIFACT_KIND)
        self.assertEqual(first["requested_model"], "jev-latest")
        self.assertEqual(first["model"], "jev-latest")
        self.assertTrue(first["assessment_id"].startswith("jev:"))
        semantics = first["evidence_semantics"]
        self.assertEqual(semantics["kind"], "assumption")
        self.assertTrue(semantics["may_rank_or_request_probe"])
        for authority in (
            "may_establish_fact", "may_establish_compatibility",
            "may_establish_completeness", "may_qualify_claim",
        ):
            self.assertFalse(semantics[authority])

    def test_claim_fragment_contains_only_producer_authorized_assumptions(self) -> None:
        artifact = build_artifact(AssessmentRequest.parse(request_document()), api_response())
        bundle = claims_bundle(artifact)
        self.assertEqual(validate_bundle(bundle), ())
        self.assertEqual({relation.modality for relation in bundle.relations},
                         {Modality.ASSUMPTION})
        self.assertEqual({relation.producer_classes for relation in bundle.relations},
                         {("jev",)})
        self.assertFalse(bundle.claims)
        self.assertFalse(bundle.rules)
        self.assertTrue(bundle.facts)
        self.assertTrue(all(record.kind == "assumption" for record in bundle.evidence))

    def test_claim_fragments_reject_content_address_tampering(self) -> None:
        artifact = build_artifact(AssessmentRequest.parse(request_document()), api_response())
        tampered = deepcopy(artifact)
        tampered["judgments"]["best_candidate"]["choice"] = "audit-request"
        with self.assertRaisesRegex(JevError, "assessment_id does not match"):
            claims_bundle(tampered)

        pattern_request = PatternRequest.parse(pattern_request_document())
        responses = {variant: pattern_response() for variant in VARIANTS}
        pattern = build_pattern_artifact(pattern_request, responses, max_spread=.2)
        tampered_pattern = deepcopy(pattern)
        tampered_pattern["sensitivity"]["stable"] = False
        with self.assertRaisesRegex(JevError, "assessment_id does not match"):
            pattern_claims_bundle(tampered_pattern)

    def test_pattern_claim_fragment_rejects_non_jev_producer(self) -> None:
        request = PatternRequest.parse(pattern_request_document())
        artifact = build_pattern_artifact(
            request, {variant: pattern_response() for variant in VARIANTS}, max_spread=.2)
        artifact["producer"] = {"class": "modelcheck", "source": "modelcheck forged"}
        core = dict(artifact)
        core.pop("assessment_id")
        from capcov.claims import jev as jev_module
        artifact["assessment_id"] = f"jev-pattern:{jev_module._digest(core)}"
        with self.assertRaisesRegex(JevError, "producer is malformed"):
            pattern_claims_bundle(artifact)

    def test_assess_uses_jev_key_without_leaking_it(self) -> None:
        seen = {}

        def transport(endpoint, body, headers, timeout):
            seen.update(endpoint=endpoint, body=json.loads(body), headers=dict(headers), timeout=timeout)
            return json.dumps(api_response()).encode()

        with patch.dict(os.environ, {"JEV_API_KEY": "secret-value"}, clear=True):
            artifact = assess(AssessmentRequest.parse(request_document()), transport=transport)
        self.assertEqual(seen["headers"]["Authorization"], "Bearer secret-value")
        self.assertNotIn("secret-value", json.dumps(artifact))
        self.assertEqual(artifact["judgments"]["best_candidate"]["choice"], "change-subscription")

    def test_rejects_response_outside_candidate_set(self) -> None:
        response = api_response()
        response["answers"]["best_candidate"]["choice"] = "invented-symbol"
        with self.assertRaises(JevError) as caught:
            build_artifact(AssessmentRequest.parse(request_document()), response)
        self.assertEqual(caught.exception.kind, "invalid-response")

    def test_preserves_requested_alias_and_resolved_model(self) -> None:
        response = api_response()
        response["model"] = "jev-1.13.0"
        artifact = build_artifact(AssessmentRequest.parse(request_document()), response)
        self.assertEqual(artifact["requested_model"], "jev-latest")
        self.assertEqual(artifact["model"], "jev-1.13.0")
        self.assertIn("jev-1.13.0", artifact["producer"]["source"])

    def test_rejects_missing_no_match_distribution(self) -> None:
        response = api_response()
        del response["answers"]["best_candidate"]["probabilities"]["no_match"]
        with self.assertRaises(JevError):
            build_artifact(AssessmentRequest.parse(request_document()), response)

    def test_rejects_duplicate_candidates_and_unknown_fields(self) -> None:
        duplicate = request_document()
        duplicate["candidates"][1]["id"] = duplicate["candidates"][0]["id"]
        with self.assertRaises(JevError):
            AssessmentRequest.parse(duplicate)
        unknown = request_document()
        unknown["authority"] = "covered"
        with self.assertRaises(JevError):
            AssessmentRequest.parse(unknown)

    def test_missing_key_is_named(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(JevError) as caught:
                assess(AssessmentRequest.parse(request_document()))
        self.assertEqual(caught.exception.kind, "missing-credential")

    def test_cli_replays_response_and_writes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_path, response_path, output_path, claims_path = (
                root / "request.json", root / "response.json", root / "artifact.json",
                root / "claims.json")
            request_path.write_text(json.dumps(request_document()))
            response_path.write_text(json.dumps(api_response()))
            stdout = StringIO()
            with redirect_stdout(stdout):
                status = experiment_main([
                    "claims", "jev", "assess", "--request", str(request_path),
                    "--response", str(response_path), "--out", str(output_path),
                    "--claims-out", str(claims_path),
                ])
            self.assertEqual(status, 0)
            emitted = json.loads(stdout.getvalue())
            stored = json.loads(output_path.read_text())
            self.assertEqual(emitted, stored)
            self.assertEqual(stored["evidence_semantics"]["kind"], "assumption")
            claim_document = json.loads(claims_path.read_text())
            self.assertEqual(
                {relation["modality"] for relation in claim_document["relations"]},
                {"assumption"})


if __name__ == "__main__":
    unittest.main()
