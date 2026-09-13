"""Tests for the SCIP -> capcov fact mapper.

The core suite runs entirely against a checked-in normalized fixture
(tests/fixtures/scip_normalized_router_service.json). That fixture is REAL:
it is the output of ``runner.normalize_scip_json`` over a genuine
``scip-python`` index of a two-module ``router -> service`` project, so the
symbol strings, line spans and the null ``display_name`` (scip-python does not
emit one) are exactly what the runner delivers in production. Mapping is a pure
function over that dict; no scip tools and no network are needed.

The end-to-end path -- index a tree with scip-python, read it with the scip
CLI, then map it -- lives in ``LiveToolTest`` and skips cleanly wherever either
tool is absent, the same way the runner's own live tests do.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from capcov.scip import map as scip_map
from capcov.scip import runner

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "scip_normalized_router_service.json"
)

# The three type definitions the fixture contains, by their SCIP symbol.
_PY = "scip-python python spike 0.0.1 "
_JOB = _PY + "`shop.models`/Job#"
_RUN = _PY + "`shop.models`/Run#"
_BASE = _PY + "`shop.db`/Base#"
_MAKE_JOB = _PY + "`shop.router`/make_job()."
_CREATE_JOB = _PY + "`shop.service`/create_job()."


class EntitiesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalized = json.loads(FIXTURE.read_text())
        self.entities = scip_map.entities(self.normalized)
        self.by_id = {e["id"]: e for e in self.entities}

    def test_every_type_definition_is_enumerated(self) -> None:
        # Base, Job and Run are the three class defs (suffix `#`). Nothing else.
        self.assertEqual(set(self.by_id), {_BASE, _JOB, _RUN})

    def test_entity_carries_file_line_and_derived_display_name(self) -> None:
        job = self.by_id[_JOB]
        self.assertEqual(job["file"], "shop/models.py")
        self.assertEqual(job["line"], 3)  # 0-based SCIP line, as the runner reports
        # scip-python leaves display_name null; the mapper derives it from the
        # symbol's trailing descriptor.
        self.assertEqual(job["display_name"], "Job")
        self.assertEqual(self.by_id[_RUN]["display_name"], "Run")
        self.assertEqual(self.by_id[_BASE]["display_name"], "Base")

    def test_fields_modules_methods_params_and_locals_are_not_entities(self) -> None:
        names = {e["display_name"] for e in self.entities}
        # __tablename__ is a term (suffix `.`), make_job/create_job are methods
        # (suffix `().`), the modules are meta (`:`), params/locals carry no
        # type suffix. None of them is a type definition.
        self.assertNotIn("__tablename__", names)
        self.assertNotIn("make_job", names)
        self.assertNotIn("create_job", names)
        for entity in self.entities:
            self.assertFalse(entity["id"].endswith("()."))
            self.assertTrue(entity["id"].endswith("#"))

    def test_result_is_deterministically_ordered(self) -> None:
        again = scip_map.entities(json.loads(FIXTURE.read_text()))
        self.assertEqual(self.entities, again)
        self.assertEqual(
            self.entities, sorted(self.entities, key=lambda e: (e["file"], e["line"]))
        )


class CallEdgesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.normalized = json.loads(FIXTURE.read_text())
        self.edges = scip_map.call_edges(self.normalized)

    def test_the_cross_file_call_edge_is_present(self) -> None:
        # THE edge this fixture proves: router.make_job -> service.create_job,
        # resolved across files by SCIP's global symbol. The caller is attributed
        # by the enclosing_range of make_job's definition; the callee is the very
        # symbol that service.py defines.
        self.assertIn(
            {
                "caller": _MAKE_JOB,
                "callee": _CREATE_JOB,
                "file": "shop/router.py",
                "line": 4,
            },
            self.edges,
        )

    def test_that_is_the_only_edge(self) -> None:
        # The only callable reference in the tree is create_job(). session.add()
        # resolves to nothing scip could type, so scip emits no occurrence for it
        # at all -- the silent gap the ast pass must enumerate, not this mapper.
        self.assertEqual(len(self.edges), 1)

    def test_caller_and_callee_live_in_different_documents(self) -> None:
        edge = self.edges[0]
        # caller defined in router.py, callee defined in service.py: the whole
        # point of renting SCIP as the resolver.
        self.assertTrue(edge["caller"].startswith(_PY + "`shop.router`/"))
        self.assertTrue(edge["callee"].startswith(_PY + "`shop.service`/"))

    def test_constructor_is_a_type_reference_not_a_call_edge(self) -> None:
        # `Job()` in service.py surfaces as a REFERENCE to the Job type (suffix
        # `#`), never as a call edge -- so no edge points at a type symbol.
        for edge in self.edges:
            self.assertFalse(edge["callee"].endswith("#"))


class ClassificationUnitTest(unittest.TestCase):
    """The two signals the mapper reads: the runner's normalized `kind`
    (populated for scip-go) and, when it is absent, the descriptor suffix."""

    def _doc(self, symbols, occurrences):
        return {"documents": [{"path": "x", "symbols": symbols, "occurrences": occurrences}]}

    def test_go_populated_kinds_drive_classification(self) -> None:
        symbols = [
            {"symbol": "s Server#", "kind": "Struct", "display_name": "Server"},
            {"symbol": "s Start().", "kind": "Function", "display_name": "Start"},
            {"symbol": "s Addr.", "kind": "Field", "display_name": "Addr"},
        ]
        occ = [
            {"symbol": "s Server#", "is_definition": True, "start_line": 1,
             "start_col": 0, "enclosing_start_line": 1, "enclosing_end_line": 9},
            {"symbol": "s Addr.", "is_definition": True, "start_line": 2,
             "start_col": 0, "enclosing_start_line": None, "enclosing_end_line": None},
            {"symbol": "s Start().", "is_definition": False, "start_line": 4,
             "start_col": 0, "enclosing_start_line": None, "enclosing_end_line": None},
        ]
        normalized = self._doc(symbols, occ)
        ents = scip_map.entities(normalized)
        self.assertEqual([e["display_name"] for e in ents], ["Server"])  # Struct only
        edges = scip_map.call_edges(normalized)
        self.assertEqual([e["callee"] for e in edges], ["s Start()."])  # Function ref

    def test_null_kind_falls_back_to_the_suffix(self) -> None:
        # A callee whose definition lives outside every indexed document has no
        # symbol-table entry; suffix parsing must still classify it.
        occ = [
            {"symbol": "p caller().", "is_definition": True, "start_line": 0,
             "start_col": 0, "enclosing_start_line": 0, "enclosing_end_line": 5},
            {"symbol": "external lib thing().", "is_definition": False,
             "start_line": 2, "start_col": 0,
             "enclosing_start_line": None, "enclosing_end_line": None},
        ]
        edges = scip_map.call_edges(self._doc([], occ))
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["callee"], "external lib thing().")
        self.assertEqual(edges[0]["caller"], "p caller().")


class CallerAttributionUnitTest(unittest.TestCase):
    def test_innermost_enclosing_definition_wins(self) -> None:
        # A method reference sitting inside a method inside a class must bind to
        # the method, not the class, even though both enclose the line.
        symbols = [{"symbol": "m outer().", "kind": "method", "display_name": "outer"}]
        occ = [
            {"symbol": "m Cls#", "is_definition": True, "start_line": 0,
             "start_col": 0, "enclosing_start_line": 0, "enclosing_end_line": 20},
            {"symbol": "m outer().", "is_definition": True, "start_line": 2,
             "start_col": 0, "enclosing_start_line": 2, "enclosing_end_line": 8},
            {"symbol": "m callee().", "is_definition": False, "start_line": 5,
             "start_col": 0, "enclosing_start_line": None, "enclosing_end_line": None},
        ]
        edges = scip_map.call_edges({"documents": [{"path": "x", "symbols": symbols, "occurrences": occ}]})
        self.assertEqual(edges[0]["caller"], "m outer().")

    def test_module_scope_reference_has_no_caller(self) -> None:
        # A callable reference with no enclosing definition (module/import scope)
        # is preserved with caller None rather than silently dropped.
        occ = [
            {"symbol": "m thing().", "is_definition": False, "start_line": 0,
             "start_col": 0, "enclosing_start_line": None, "enclosing_end_line": None},
        ]
        edges = scip_map.call_edges({"documents": [{"path": "x", "symbols": [], "occurrences": occ}]})
        self.assertEqual(len(edges), 1)
        self.assertIsNone(edges[0]["caller"])


class RobustnessUnitTest(unittest.TestCase):
    def test_empty_input_yields_empty_results(self) -> None:
        self.assertEqual(scip_map.entities({}), [])
        self.assertEqual(scip_map.call_edges({}), [])
        self.assertEqual(scip_map.entities({"documents": []}), [])

    def test_display_name_is_derived_for_methods_fields_and_types(self) -> None:
        self.assertEqual(scip_map._leaf_name(_JOB), "Job")
        self.assertEqual(scip_map._leaf_name(_CREATE_JOB), "create_job")
        self.assertEqual(
            scip_map._leaf_name("s go/pkg/Server#Addr."), "Addr"
        )
        self.assertEqual(
            scip_map._leaf_name("s foo(a).").__class__, str
        )


# ---------------------------------------------------------------------------
# Live: index a real tree, read it, map it. Skips when the tools are absent.

_HAVE_SCIP_PYTHON = shutil.which("scip-python") is not None


def _have_scip_cli() -> bool:
    try:
        runner._locate_scip_cli()
        return True
    except runner.ScipCliNotFound:
        return False


class LiveToolTest(unittest.TestCase):
    @unittest.skipUnless(
        _HAVE_SCIP_PYTHON and _have_scip_cli(),
        "needs both scip-python and the scip CLI (set SCIP_CLI)",
    )
    def test_index_read_map_recovers_the_cross_file_edge(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "service.py").write_text(
                "def create_job(session, name):\n    return name\n"
            )
            (root / "router.py").write_text(
                "import service\n\n\ndef make_job(session, name):\n"
                "    return service.create_job(session, name)\n"
            )
            index = runner.run_scip_index(d, "python")
            normalized = runner.read_scip_index(index)
            edges = scip_map.call_edges(normalized)
            pairs = {
                (scip_map._leaf_name(e["caller"] or ""), scip_map._leaf_name(e["callee"]))
                for e in edges
            }
            self.assertIn(("make_job", "create_job"), pairs)


if __name__ == "__main__":
    unittest.main()
