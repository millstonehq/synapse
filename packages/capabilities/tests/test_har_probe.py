"""The `har` probe: runtime bindings harvested from an existing browser run.

FacilityGrid and Leap have no Python test suite to hook, but both already run
Playwright suites that can record a HAR. This probe projects those requests
onto the static surfaces so a route that a real session reached lands in
`both` and one nobody reached stays `static_only` -- the split that would have
caught a feature that was merged, deployed and never exercised.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from capcov.probes.har_probe import match_surface, project_har, template_regex


SURFACES = [
    {"id": "http:GET /api/jobs", "method": "GET", "path": "/api/jobs"},
    {"id": "http:GET /api/jobs/{id}", "method": "GET", "path": "/api/jobs/{id}"},
    {"id": "http:POST /api/jobs/:id/close", "method": "POST", "path": "/api/jobs/:id/close"},
    {"id": "http:DELETE /api/jobs/{id}", "method": "DELETE", "path": "/api/jobs/{id}"},
]


def _har(entries: list[tuple[str, str]]) -> dict:
    return {"log": {"entries": [
        {"request": {"method": m, "url": f"https://app.example.com{u}"},
         "response": {"status": 200}} for m, u in entries]}}


class TemplateTests(unittest.TestCase):
    def test_brace_and_colon_params_match_one_segment(self) -> None:
        self.assertTrue(template_regex("/api/jobs/{id}").fullmatch("/api/jobs/42"))
        self.assertTrue(template_regex("/api/jobs/:id/close").fullmatch("/api/jobs/42/close"))
        self.assertFalse(template_regex("/api/jobs/{id}").fullmatch("/api/jobs/42/close"))

    def test_literal_beats_template_when_both_match(self) -> None:
        surfaces = SURFACES + [{"id": "http:GET /api/jobs/new", "method": "GET", "path": "/api/jobs/new"}]
        self.assertEqual(match_surface("GET", "/api/jobs/new", surfaces), "http:GET /api/jobs/new")
        self.assertEqual(match_surface("GET", "/api/jobs/7", surfaces), "http:GET /api/jobs/{id}")

    def test_method_must_match(self) -> None:
        self.assertIsNone(match_surface("PUT", "/api/jobs/7", SURFACES))


class ProjectTests(unittest.TestCase):
    def test_requests_become_bindings_with_crud_and_test_name(self) -> None:
        har = _har([("GET", "/api/jobs"), ("GET", "/api/jobs/7?x=1"), ("DELETE", "/api/jobs/7")])
        result = project_har({"smoke.har": har}, SURFACES, strip_prefixes=[])
        by_surface = {b["surface"]: b for b in result["bindings"]}
        self.assertEqual(by_surface["http:GET /api/jobs"]["operations"], ["read"])
        self.assertEqual(by_surface["http:GET /api/jobs"]["entity"], "http:GET /api/jobs")
        self.assertEqual(by_surface["http:GET /api/jobs"]["tests"], ["smoke.har"])
        self.assertEqual(by_surface["http:DELETE /api/jobs/{id}"]["operations"], ["delete"])
        self.assertEqual(result["unresolved"], [])

    def test_unmatched_requests_are_reported_not_dropped(self) -> None:
        har = _har([("GET", "/api/jobs"), ("GET", "/static/app.js"), ("GET", "/api/ghost")])
        result = project_har({"smoke.har": har}, SURFACES, strip_prefixes=[])
        self.assertEqual(len(result["bindings"]), 1)
        self.assertEqual(len(result["unresolved"]), 1)
        entry = result["unresolved"][0]
        self.assertEqual(entry["kind"], "unmatched-requests")
        self.assertFalse(entry["gating"])
        self.assertEqual(entry["count"], 2)
        self.assertIn("GET /api/ghost", entry["samples"])

    def test_strip_prefixes_before_matching(self) -> None:
        har = _har([("GET", "/v2/api/jobs")])
        result = project_har({"a.har": har}, SURFACES, strip_prefixes=["/v2"])
        self.assertEqual([b["surface"] for b in result["bindings"]], ["http:GET /api/jobs"])

    def test_same_surface_from_two_runs_merges_tests(self) -> None:
        result = project_har(
            {"a.har": _har([("GET", "/api/jobs")]), "b.har": _har([("GET", "/api/jobs")])},
            SURFACES, strip_prefixes=[],
        )
        self.assertEqual(result["bindings"][0]["tests"], ["a.har", "b.har"])


class ObserveTests(unittest.TestCase):
    def test_observe_writes_a_valid_observed_artifact(self) -> None:
        from capcov.probes.har_probe import observe
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "app.php").write_text("<?php\n")
            (root / "capcov.capabilities.json").write_text(json.dumps({"surfaces": SURFACES}))
            (root / "run.har").write_text(json.dumps(_har([("GET", "/api/jobs")])))
            observed = observe(source_root=root / "src", target=root, out=root / "observed.json",
                               nonce="n1", har_paths=[root / "run.har"])
            written = json.loads((root / "observed.json").read_text())
        self.assertEqual(written["kind"], "observed")
        self.assertEqual(written["bindings"][0]["surface"], "http:GET /api/jobs")
        self.assertEqual(written["exercises"], 1)
        self.assertEqual(observed["bindings"], written["bindings"])
