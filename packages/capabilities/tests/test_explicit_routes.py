"""Explicit registrations preserve source identity and unresolved limits."""

import json
import tempfile
import unittest
from pathlib import Path

from capcov.flows.discovery import discover


class ExplicitRoutesTests(unittest.TestCase):
    def inventory(self, source):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "app.py").write_text(source)
            config = root / "discovery.json"
            config.write_text(json.dumps({"root": ".", "scope": "core", "adapters": [{
                "kind": "python-routes", "files": ["app.py"], "source_namespace": "worker",
                "prefix": "/api",
            }]}))
            return discover(config)["obligations"]

    def test_factory_registration_retains_handler_and_branches(self):
        rows = self.inventory('''def health():
    if ready:
        return "ok"
    try:
        return "starting"
    except ValueError:
        return "unknown"
def create_app():
    app.add_api_route("/health", health, methods=["GET", "HEAD"])
''')
        surfaces = [r for r in rows if r["kind"] == "surface"]
        self.assertEqual({r["http_surface"] for r in surfaces},
                         {"http:GET /api/health", "http:HEAD /api/health"})
        self.assertEqual({r["handler"] for r in surfaces}, {"health"})
        self.assertEqual({r["source"]["line"] for r in surfaces}, {9})
        self.assertEqual(len([r for r in rows if r["kind"] == "branch-candidate"]), 4)
        self.assertEqual(len([r for r in rows if r["kind"] == "exception-candidate"]), 2)

    def test_keyword_arguments_and_default_get(self):
        rows = self.inventory('def health(): return "ok"\napp.add_api_route(endpoint=health, path="/health")')
        self.assertEqual([r["http_surface"] for r in rows if r["kind"] == "surface"],
                         ["http:GET /api/health"])

    def test_dynamic_or_ambiguous_registration_stays_unresolved(self):
        snippets = [
            'app.add_api_route(secret_path, health)',
            'app.add_api_route("/health", health, methods=method_list)',
            'app.add_api_route("/health", imported_handler)',
            'app.add_api_route("/health", handlers.health)',
            'app.add_api_route("/health", health, methods=[])',
            'app.add_api_route("/health", health, **options)',
            'try: pass\nexcept Exception as health:\n    app.add_api_route("/health", health)',
            'health = replacement\napp.add_api_route("/health", health)',
            'def factory(health):\n    app.add_api_route("/health", health)',
            'def health(): return "replacement"\napp.add_api_route("/health", health)',
        ]
        for snippet in snippets:
            with self.subTest(snippet=snippet):
                rows = self.inventory('def health(): return "ok"\n' + snippet)
                self.assertFalse([r for r in rows if r["kind"] == "surface"])
                unresolved = [r for r in rows if ":registration:" in r["id"]]
                self.assertEqual(len(unresolved), 1)
                self.assertEqual(unresolved[0]["kind"], "unresolved")
                self.assertNotIn("secret_path", json.dumps(rows))

    def test_duplicate_explicit_and_decorated_surface_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate obligation IDs"):
            self.inventory('@app.get("/health")\ndef health(): return "ok"\napp.add_api_route("/health", health)')


if __name__ == "__main__":
    unittest.main()
