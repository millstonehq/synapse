from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from capcov.claims.cli import main as experiment_main
from capcov.claims import Modality
from capcov.claims.jev import (
    ARTIFACT_KIND, AssessmentRequest, JevError, assess, build_artifact,
    claims_bundle,
)
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


class JevAdvisoryTests(unittest.TestCase):
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
