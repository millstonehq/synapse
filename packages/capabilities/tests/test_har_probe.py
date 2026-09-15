"""The `har` probe: runtime bindings harvested from an existing browser run.

the target system and Leap have no Python test suite to hook, but both already run
Playwright suites that can record a HAR. This probe projects those requests
onto the static surfaces so a route that a real session reached lands in
`both` and one nobody reached stays `static_only` -- the split that would have
caught a feature that was merged, deployed and never exercised.
"""

from __future__ import annotations

import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from capcov.probes import har_probe
from capcov.probes.har_probe import (
    index_surfaces,
    match_indexed,
    match_surface,
    observe,
    project_har,
    template_regex,
)


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

    def test_trailing_slash_is_ignored_on_both_sides(self) -> None:
        self.assertEqual(match_surface("GET", "/api/jobs/", SURFACES), "http:GET /api/jobs")
        self.assertEqual(match_surface("GET", "/api/jobs/7/", SURFACES), "http:GET /api/jobs/{id}")
        surfaces = [{"id": "http:GET /api/jobs/", "method": "GET", "path": "/api/jobs/"}]
        self.assertEqual(match_surface("GET", "/api/jobs", surfaces), "http:GET /api/jobs/")

    def test_slashless_surface_path_matches_rooted_request(self) -> None:
        surfaces = [{"id": "http:GET admin/tows", "method": "GET", "path": "admin/tows"}]
        self.assertEqual(match_surface("GET", "/admin/tows", surfaces), "http:GET admin/tows")


class IndexTests(unittest.TestCase):
    def test_indexed_matching_agrees_with_the_unindexed_path(self) -> None:
        surfaces = SURFACES + [
            {"id": "http:GET /api/jobs/new", "method": "GET", "path": "/api/jobs/new"},
            {"id": "http:GET admin/tows", "method": "GET", "path": "admin/tows"},
        ]
        index = index_surfaces(surfaces)
        for method, path in [
            ("GET", "/api/jobs"), ("GET", "/api/jobs/new"), ("GET", "/api/jobs/7"),
            ("GET", "/api/jobs/7/"), ("POST", "/api/jobs/7/close"), ("DELETE", "/api/jobs/7"),
            ("PUT", "/api/jobs/7"), ("GET", "/admin/tows"), ("GET", "/nowhere"),
        ]:
            with self.subTest(method=method, path=path):
                self.assertEqual(
                    match_indexed(method, path, index), match_surface(method, path, surfaces)
                )

    def test_index_normalises_missing_slash_and_splits_literals_from_templates(self) -> None:
        literals, templates = index_surfaces(
            [{"id": "a", "method": "get", "path": "admin/tows"},
             {"id": "b", "method": "GET", "path": "/admin/tows/{id}"}]
        )
        self.assertEqual(literals, {("GET", "/admin/tows"): "a"})
        self.assertEqual([(m, sid) for m, _, sid in templates], [("GET", "b")])

    def test_repeated_requests_hit_the_memo_not_the_index(self) -> None:
        calls = []
        real = har_probe.candidates_indexed

        def counting(method, path, index):
            calls.append((method, path))
            return real(method, path, index)

        har = _har([("GET", "/api/jobs/7"), ("GET", "/api/jobs/7?page=2"), ("GET", "/api/jobs/7")])
        with unittest.mock.patch.object(har_probe, "candidates_indexed", counting):
            result = project_har({"a.har": har}, SURFACES, strip_prefixes=[])
        self.assertEqual(calls, [("GET", "/api/jobs/7")])
        self.assertEqual(result["requests"], 3)
        self.assertEqual(result["bindings"][0]["surface"], "http:GET /api/jobs/{id}")


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
        self.assertIn("GET app.example.com/api/ghost", entry["samples"])

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

    def test_hars_are_keyed_by_path_and_labelled_by_basename(self) -> None:
        result = project_har(
            {"ci/smoke.har": _har([("GET", "/api/jobs")]), "local/other.har": _har([("GET", "/api/jobs")])},
            SURFACES, strip_prefixes=[],
        )
        self.assertEqual(result["bindings"][0]["tests"], ["other.har", "smoke.har"])

    def test_two_hars_sharing_a_basename_are_refused_by_name(self) -> None:
        with self.assertRaises(ValueError) as caught:
            project_har(
                {"ci/smoke.har": _har([]), "local/smoke.har": _har([])}, SURFACES, strip_prefixes=[]
            )
        self.assertIn("ci/smoke.har", str(caught.exception))
        self.assertIn("local/smoke.har", str(caught.exception))

    def test_samples_carry_the_host_and_non_http_urls_are_counted(self) -> None:
        har = {"log": {"entries": [
            {"request": {"method": "GET", "url": "https://cdn.example.com/font.woff2"}},
            {"request": {"method": "GET", "url": "data:image/png;base64,AAAA"}},
            {"request": {"method": "GET", "url": "blob:https://app.example.com/1234"}},
            {"request": {"method": "GET", "url": "about:blank"}},
            {"request": {"method": "GET", "url": "/api/jobs"}},
        ]}}
        result = project_har({"a.har": har}, SURFACES, strip_prefixes=[])
        self.assertEqual([b["surface"] for b in result["bindings"]], ["http:GET /api/jobs"])
        self.assertEqual(result["requests"], 5)
        entry = result["unresolved"][0]
        self.assertEqual(entry["kind"], "unmatched-requests")
        self.assertEqual(entry["count"], 1)
        self.assertEqual(entry["samples"], ["GET cdn.example.com/font.woff2"])
        self.assertEqual(entry["non_http"], 3)

    def test_ambiguous_template_hits_are_reported_not_bound(self) -> None:
        surfaces = [
            {"id": "http:GET /x/{a}", "method": "GET", "path": "/x/{a}"},
            {"id": "http:GET /{regionCode}/zones", "method": "GET", "path": "/{regionCode}/zones"},
        ]
        result = project_har({"a.har": _har([("GET", "/x/zones"), ("GET", "/x/1")])}, surfaces, strip_prefixes=[])
        self.assertEqual([b["surface"] for b in result["bindings"]], ["http:GET /x/{a}"])
        self.assertEqual(result["bindings"][0]["tests"], ["a.har"])
        entry = result["unresolved"][0]
        self.assertEqual(entry["kind"], "ambiguous-match")
        self.assertFalse(entry["gating"])
        self.assertEqual(entry["count"], 1)
        self.assertEqual(entry["samples"], ["GET /x/zones -> [http:GET /x/{a}, http:GET /{regionCode}/zones]"])

    def test_head_options_and_unknown_verbs_bind_nothing(self) -> None:
        surfaces = SURFACES + [{"id": "http:HEAD /api/jobs", "method": "HEAD", "path": "/api/jobs"}]
        har = _har([("HEAD", "/api/jobs"), ("OPTIONS", "/api/jobs"), ("PROPFIND", "/api/jobs"), ("GET", "/api/jobs")])
        result = project_har({"a.har": har}, surfaces, strip_prefixes=[])
        self.assertEqual([b["surface"] for b in result["bindings"]], ["http:GET /api/jobs"])
        self.assertEqual(result["bindings"][0]["operations"], ["read"])
        kinds = {e["kind"]: e for e in result["unresolved"]}
        self.assertEqual(set(kinds), {"non-binding-verbs"})
        self.assertFalse(kinds["non-binding-verbs"]["gating"])
        self.assertEqual(kinds["non-binding-verbs"]["count"], 3)
        self.assertIn("HEAD app.example.com/api/jobs", kinds["non-binding-verbs"]["samples"])

    def test_entries_without_url_or_method_never_reach_the_root_surface(self) -> None:
        surfaces = SURFACES + [{"id": "http:GET /", "method": "GET", "path": "/"}]
        har = {"log": {"entries": [
            {"request": {"method": "GET"}},
            {"request": {"url": "https://app.example.com/api/jobs"}},
            {"response": {"status": 200}},
        ]}}
        result = project_har({"a.har": har}, surfaces, strip_prefixes=[])
        self.assertEqual(result["bindings"], [])
        self.assertEqual(result["requests"], 3)
        entry = result["unresolved"][0]
        self.assertEqual(entry["kind"], "malformed-entries")
        self.assertFalse(entry["gating"])
        self.assertEqual(entry["count"], 3)


class ObserveTests(unittest.TestCase):
    def test_observe_writes_a_valid_observed_artifact(self) -> None:
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

    def test_observe_reads_har_surfaces_and_strip_prefixes_from_capcov_toml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "capcov.toml").write_text(
                '[capcov]\nhar_surfaces = "build/inventory.json"\nhar_strip_prefixes = ["/v2"]\n'
            )
            (root / "build").mkdir()
            (root / "build" / "inventory.json").write_text(json.dumps({"surfaces": SURFACES}))
            (root / "run.har").write_text(json.dumps(_har([("GET", "/v2/api/jobs/9")])))
            observed = observe(source_root=root / "src", target=root, out=root / "observed.json",
                               nonce="n1", har_paths=[root / "run.har"])
        self.assertEqual([b["surface"] for b in observed["bindings"]], ["http:GET /api/jobs/{id}"])
        self.assertEqual(observed["unresolved"], [])

    def test_observe_refuses_a_missing_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "run.har").write_text(json.dumps(_har([])))
            with self.assertRaises(ValueError) as caught:
                observe(source_root=root / "src", target=root, out=root / "observed.json",
                        nonce="n1", har_paths=[root / "run.har"])
            self.assertFalse((root / "observed.json").exists())
        self.assertIn("capcov.capabilities.json", str(caught.exception))

    def test_observe_refuses_two_hars_with_one_basename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "capcov.capabilities.json").write_text(json.dumps({"surfaces": SURFACES}))
            for sub in ("ci", "local"):
                (root / sub).mkdir()
                (root / sub / "smoke.har").write_text(json.dumps(_har([("GET", "/api/jobs")])))
            with self.assertRaises(ValueError) as caught:
                observe(source_root=root / "src", target=root, out=root / "observed.json",
                        nonce="n1", har_paths=[root / "ci" / "smoke.har", root / "local" / "smoke.har"])
        self.assertIn("smoke.har", str(caught.exception))
