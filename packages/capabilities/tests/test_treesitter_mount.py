"""`mount` on a treesitter-routes adapter entry composes a prefix into the path.

An Express router mounted at app.use('/api/v1', router) serves '/api/v1/jobs',
not '/jobs'. The literal in the file is the second; the runtime surface is the
first. Without a mount two routers with the same literals collide, and no
runtime probe can match the id. `mount` is per adapter entry, so each mounted
router gets its own entry and its own prefix.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from capcov.flows.discovery import discover

_HAVE_TS = (
    importlib.util.find_spec("tree_sitter") is not None
    and importlib.util.find_spec("tree_sitter_language_pack") is not None
)

JS_QUERY = (
    "((call_expression function: (member_expression property: (property_identifier) @method) "
    "arguments: (arguments (string) @path)) "
    "(#match? @method \"^(get|post|put|patch|delete)$\"))"
)
SRC = "router.get('/jobs', h);\nrouter.post('/jobs/:id', h);\n"


@unittest.skipUnless(_HAVE_TS, "treesitter extra not installed")
class MountTests(unittest.TestCase):
    def _discover(self, mount: str | None) -> set[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes.js").write_text(SRC)
            entry = {"kind": "treesitter-routes", "language": "javascript",
                     "files": ["routes.js"], "query": JS_QUERY}
            if mount is not None:
                entry["mount"] = mount
            config = root / "discovery.json"
            config.write_text(json.dumps({"scope": "t", "root": ".", "adapters": [entry]}))
            inventory = discover(config)
        return {o["id"] for o in inventory["obligations"] if o["kind"] == "surface"}

    def test_mount_prefixes_every_route(self) -> None:
        self.assertEqual(self._discover("/api/v1"), {"http:/api/v1/jobs", "http:/api/v1/jobs/:id"})

    def test_mount_joins_with_a_single_slash(self) -> None:
        self.assertEqual(self._discover("/api/v1/"), {"http:/api/v1/jobs", "http:/api/v1/jobs/:id"})

    def test_no_mount_is_unchanged(self) -> None:
        self.assertEqual(self._discover(None), {"http:/jobs", "http:/jobs/:id"})
