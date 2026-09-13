"""Discovery must expose what its query narrowed, not just what it kept.

A `covered/N` over a silently shrunk N reads as done when it is not. Two
provenance fields make the narrowing legible: `excluded_surfaces` (candidates the
query could see but filtered out) and `unresolved` (declared adapters that
produced no surface obligations). These are first-class inventory fields, never
implied by absence, and they never change which obligations are produced.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from capcov.flows.discovery import discover


class ExcludedSurfacesTests(unittest.TestCase):
    def test_route_shaped_candidates_dropped_by_the_verb_whitelist_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes.py").write_text(
                '@router.get("/items")\ndef items():\n    return []\n\n'
                '@router.head("/items")\ndef head_items():\n    return None\n\n'
                '@router.websocket("/ws")\ndef ws():\n    return None\n'
            )
            config = root / "discovery.json"
            config.write_text(
                json.dumps(
                    {
                        "scope": "fixture",
                        "root": ".",
                        "adapters": [{"kind": "python-routes", "files": ["routes.py"]}],
                    }
                )
            )
            inventory = discover(config)

            # The scope could see three route-shaped decorators; the verb whitelist
            # kept only GET. The other two are filtered, not absent.
            self.assertGreater(inventory["excluded_surfaces"]["count"], 0)
            self.assertEqual(inventory["excluded_surfaces"]["count"], 2)
            methods = {s["method"] for s in inventory["excluded_surfaces"]["surfaces"]}
            self.assertEqual(methods, {"HEAD", "WEBSOCKET"})
            paths = {s["path"] for s in inventory["excluded_surfaces"]["surfaces"]}
            self.assertEqual(paths, {"/items", "/ws"})

            # The obligations themselves are unchanged: only the recognised GET is a
            # surface. Filtering is now visible without inflating the denominator.
            surfaces = {o["id"] for o in inventory["obligations"] if o["kind"] == "surface"}
            self.assertEqual(surfaces, {"http:GET /items"})

    def test_clean_config_reports_zero_excluded_surfaces_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes.py").write_text('@router.get("/items")\ndef items():\n    return []\n')
            config = root / "discovery.json"
            config.write_text(
                json.dumps(
                    {
                        "scope": "fixture",
                        "root": ".",
                        "adapters": [{"kind": "python-routes", "files": ["routes.py"]}],
                    }
                )
            )
            inventory = discover(config)
            self.assertEqual(inventory["excluded_surfaces"]["count"], 0)
            self.assertEqual(inventory["excluded_surfaces"]["surfaces"], [])


class UnresolvedAdapterTests(unittest.TestCase):
    def test_adapter_that_yields_no_surfaces_is_named_under_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes.py").write_text('@router.get("/items")\ndef items():\n    return []\n')
            # A valid OpenAPI 3.0.x document that declares no inline operations:
            # it contributes only boundary markers and zero surfaces.
            (root / "api.json").write_text(json.dumps({"openapi": "3.0.0", "paths": {}}))
            config = root / "discovery.json"
            config.write_text(
                json.dumps(
                    {
                        "scope": "fixture",
                        "root": ".",
                        "adapters": [
                            {"kind": "python-routes", "files": ["routes.py"]},
                            {"kind": "openapi-json", "document": "api.json"},
                        ],
                    }
                )
            )
            inventory = discover(config)

            unresolved_kinds = {u["kind"] for u in inventory["unresolved"]}
            self.assertIn("openapi-json", unresolved_kinds)
            # The python-routes adapter did produce a surface, so it is NOT unresolved.
            self.assertNotIn("python-routes", unresolved_kinds)

            # The openapi adapter's index is carried so the language is identifiable.
            openapi = next(u for u in inventory["unresolved"] if u["kind"] == "openapi-json")
            self.assertEqual(openapi["adapter"], 1)

            # Obligations are untouched: the recognised GET is still the only surface.
            surfaces = {o["id"] for o in inventory["obligations"] if o["kind"] == "surface"}
            self.assertEqual(surfaces, {"http:GET /items"})

    def test_every_adapter_producing_surfaces_leaves_unresolved_empty(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes.py").write_text('@router.get("/items")\ndef items():\n    return []\n')
            config = root / "discovery.json"
            config.write_text(
                json.dumps(
                    {
                        "scope": "fixture",
                        "root": ".",
                        "adapters": [{"kind": "python-routes", "files": ["routes.py"]}],
                    }
                )
            )
            inventory = discover(config)
            self.assertEqual(inventory["unresolved"], [])


if __name__ == "__main__":
    unittest.main()
