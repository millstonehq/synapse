"""Tests for the resolver seam that folds SCIP into the entity pipeline.

The pure tests run against the checked-in normalized fixture and hand-built
inputs -- no node/go tooling, the same way the mapper and differ are tested. They
cover the whole seam: SCIP symbol -> AST node translation, the fixpoint ``calls``
graph, the residue subtraction, and the hybrid assembly. The one live test
indexes a real tree with scip-python + the scip CLI and skips cleanly when either
is absent.
"""

from __future__ import annotations

import json
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

from capcov.adapters import python_fastapi_sqlalchemy as adapter
from capcov.core import fixpoint
from capcov.scip import resolve
from capcov.scip import runner

from .support import APP, Project

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "scip_normalized_router_service.json"
)

_PY = "scip-python python spike 0.0.1 "


class SymbolTranslationTest(unittest.TestCase):
    def test_a_plain_function_symbol_becomes_module_qualname(self) -> None:
        self.assertEqual(
            resolve.scip_symbol_to_node(_PY + "`shop.router`/make_job()."),
            "shop.router:make_job",
        )

    def test_a_method_keeps_its_enclosing_class_in_the_qualname(self) -> None:
        # The AST walker builds `module:Class.method`; the `#` (type) and `().`
        # (method) descriptors must dot-join to exactly that.
        self.assertEqual(
            resolve.scip_symbol_to_node(_PY + "`app.repo`/Repo#fetch()."),
            "app.repo:Repo.fetch",
        )

    def test_a_nested_function_keeps_its_factory_scope(self) -> None:
        # Matches the adapter's `app.main:create_app.healthz` for a handler
        # defined inside an app factory.
        self.assertEqual(
            resolve.scip_symbol_to_node(_PY + "`app.main`/create_app().healthz()."),
            "app.main:create_app.healthz",
        )

    def test_a_type_symbol_translates_too(self) -> None:
        self.assertEqual(
            resolve.scip_symbol_to_node(_PY + "`shop.models`/Job#"),
            "shop.models:Job",
        )

    def test_a_parameter_or_local_or_meta_is_not_a_node(self) -> None:
        # A parameter descriptor, a scip local, and a module meta symbol are not
        # fixpoint nodes -- each yields None so its edge is dropped, never a
        # fabricated node.
        self.assertIsNone(
            resolve.scip_symbol_to_node(_PY + "`shop.router`/make_job().(session)")
        )
        self.assertIsNone(resolve.scip_symbol_to_node("local 0"))
        self.assertIsNone(resolve.scip_symbol_to_node(_PY + "shop/__init__:"))
        self.assertIsNone(resolve.scip_symbol_to_node(None))
        self.assertIsNone(resolve.scip_symbol_to_node(""))


class CallsGraphFromFixtureTest(unittest.TestCase):
    """The seam over the real scip-python fixture: the cross-file edge the
    mapper recovered must become a fixpoint `calls` entry in AST node space."""

    def setUp(self) -> None:
        self.normalized = json.loads(FIXTURE.read_text())
        from capcov.scip import map as scip_map

        self.edges = scip_map.call_edges(self.normalized)

    def test_calls_graph_is_the_cross_file_edge_in_ast_node_space(self) -> None:
        calls = resolve.calls_graph(self.edges)
        self.assertEqual(
            calls, {"shop.router:make_job": {"shop.service:create_job"}}
        )

    def test_resolved_sites_lift_scip_zero_based_lines_to_one_based(self) -> None:
        # The one call reference sits at SCIP 0-based line 4; the AST pass and the
        # residue speak 1-based, so it must surface as line 5.
        self.assertEqual(
            resolve.resolved_sites(self.edges),
            [{"file": "shop/router.py", "line": 5}],
        )

    def test_is_node_filter_drops_edges_outside_the_ast_namespace(self) -> None:
        # An edge whose endpoints are not known AST nodes (an external library)
        # is dropped, exactly as the AST pass drops external calls.
        calls = resolve.calls_graph(self.edges, is_node={"nothing"}.__contains__)
        self.assertEqual(calls, {})


class HybridAssemblyTest(unittest.TestCase):
    """hybrid_raw over a controlled tree + a matching hand-built SCIP index:
    _calls is re-sourced from SCIP, the AST halves are preserved, and the residue
    names the site SCIP stayed silent about."""

    FILES = {
        "service.py": "def create_job(session, name):\n    return name\n",
        "router.py": textwrap.dedent(
            """\
            from app import service


            def make_job(session, name):
                handler = getattr(service, name)
                return service.create_job(session, name)
            """
        ),
    }

    def _normalized(self) -> dict:
        svc = _PY + "`app.service`/"
        rtr = _PY + "`app.router`/"
        return {
            "documents": [
                {
                    "path": "app/service.py",
                    "symbols": [
                        {"symbol": svc + "create_job().", "kind": "method",
                         "display_name": None}
                    ],
                    "occurrences": [
                        {"symbol": svc + "create_job().", "is_definition": True,
                         "start_line": 0, "start_col": 4,
                         "enclosing_start_line": 0, "enclosing_end_line": 1},
                    ],
                },
                {
                    "path": "app/router.py",
                    "symbols": [
                        {"symbol": rtr + "make_job().", "kind": "method",
                         "display_name": None}
                    ],
                    "occurrences": [
                        {"symbol": rtr + "make_job().", "is_definition": True,
                         "start_line": 3, "start_col": 4,
                         "enclosing_start_line": 3, "enclosing_end_line": 5},
                        # the resolved call: service.create_job(...) at 1-based line 6
                        {"symbol": svc + "create_job().", "is_definition": False,
                         "start_line": 5, "start_col": 11,
                         "enclosing_start_line": None, "enclosing_end_line": None},
                    ],
                },
            ]
        }

    def test_hybrid_resources_the_call_graph_and_keeps_the_ast_halves(self) -> None:
        with Project(self.FILES) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.hybrid_raw(ast_raw, self._normalized(), project.source)

        # _calls is now the SCIP-resolved graph, in AST node space.
        self.assertEqual(
            hybrid["_calls"], {"app.router:make_job": {"app.service:create_job"}}
        )
        # the AST halves are preserved unchanged.
        self.assertEqual(hybrid["_direct"], ast_raw["_direct"])
        self.assertEqual(hybrid["surfaces"], ast_raw["surfaces"])
        self.assertEqual(hybrid["blind_spots"], ast_raw["blind_spots"])
        self.assertEqual(hybrid["resolver"], "scip")

    def test_the_residue_names_the_site_scip_left_unresolved(self) -> None:
        with Project(self.FILES) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.hybrid_raw(ast_raw, self._normalized(), project.source)

        # SCIP resolved service.create_job (line 6) and stayed silent about the
        # getattr (line 5). The residue recovers that silent gap, named.
        residue = {(r["file"], r["line"]) for r in hybrid["scip_residue"]}
        self.assertIn(("app/router.py", 5), residue)
        self.assertNotIn(("app/router.py", 6), residue)
        for site in hybrid["scip_residue"]:
            self.assertFalse(site["resolved"])
            self.assertTrue(site["reason"], "an unresolved site is named, not dropped")

    def test_the_summary_reports_both_halves_never_a_bare_number(self) -> None:
        with Project(self.FILES) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.hybrid_raw(ast_raw, self._normalized(), project.source)

        s = hybrid["scip_residue_summary"]
        self.assertEqual(s["scip_resolved_edges"], 1)
        self.assertEqual(s["scip_rooted_edges"], 1)
        self.assertGreaterEqual(s["unresolved_enumerated"], 1)
        self.assertGreaterEqual(s["ast_call_sites"], s["unresolved_enumerated"])
        # the full resolved edge list survives whole in the artifact.
        self.assertEqual(len(hybrid["scip_resolved_edges"]), 1)


class HybridBeatsAstAmbiguityTest(unittest.TestCase):
    """The whole point of the hybrid, on ONE fixture.

    Two modules define a ``persist`` method; a caller invokes it on an untyped
    parameter (``store.persist(job)``). The AST name-match cannot type ``store``
    and finds TWO project candidates, so it declares the cross-file call
    *ambiguous* and roots no edge -- the honest AST failure this hybrid exists to
    fix. SCIP, type-aware, resolves that same call to the one correct target. And
    a ``getattr(store, name)`` on the very next line has no static target for ANY
    resolver: SCIP emits nothing for it, so it must still surface, named, in the
    residue. Both properties hold together or the hybrid is pointless -- a
    resolver that hides its gaps is only safe paired with the AST enumerator.
    """

    FILES = {
        "alpha.py": "class Alpha:\n    def persist(self, job):\n        return job\n",
        "beta.py": "class Beta:\n    def persist(self, job):\n        return job\n",
        # line 1 def; line 2 getattr (blind); line 3 the ambiguous cross-file call
        "router.py": textwrap.dedent(
            """\
            def make_job(store, name, job):
                handler = getattr(store, name)
                return store.persist(job)
            """
        ),
    }

    def _normalized(self) -> dict:
        al = _PY + "`app.alpha`/"
        bt = _PY + "`app.beta`/"
        rt = _PY + "`app.router`/"
        return {
            "documents": [
                {
                    "path": "app/alpha.py",
                    "symbols": [
                        {"symbol": al + "Alpha#", "kind": "type", "display_name": None},
                        {"symbol": al + "Alpha#persist().", "kind": "method",
                         "display_name": None},
                    ],
                    "occurrences": [
                        {"symbol": al + "Alpha#", "is_definition": True,
                         "start_line": 0, "start_col": 6,
                         "enclosing_start_line": 0, "enclosing_end_line": 2},
                        {"symbol": al + "Alpha#persist().", "is_definition": True,
                         "start_line": 1, "start_col": 8,
                         "enclosing_start_line": 1, "enclosing_end_line": 2},
                    ],
                },
                {
                    "path": "app/beta.py",
                    "symbols": [
                        {"symbol": bt + "Beta#", "kind": "type", "display_name": None},
                        {"symbol": bt + "Beta#persist().", "kind": "method",
                         "display_name": None},
                    ],
                    "occurrences": [
                        {"symbol": bt + "Beta#", "is_definition": True,
                         "start_line": 0, "start_col": 6,
                         "enclosing_start_line": 0, "enclosing_end_line": 2},
                        {"symbol": bt + "Beta#persist().", "is_definition": True,
                         "start_line": 1, "start_col": 8,
                         "enclosing_start_line": 1, "enclosing_end_line": 2},
                    ],
                },
                {
                    "path": "app/router.py",
                    "symbols": [
                        {"symbol": rt + "make_job().", "kind": "method",
                         "display_name": None}
                    ],
                    "occurrences": [
                        {"symbol": rt + "make_job().", "is_definition": True,
                         "start_line": 0, "start_col": 4,
                         "enclosing_start_line": 0, "enclosing_end_line": 2},
                        # SCIP typed `store` as Alpha and bound store.persist ->
                        # Alpha.persist at 0-based line 2 (== AST 1-based line 3).
                        {"symbol": al + "Alpha#persist().", "is_definition": False,
                         "start_line": 2, "start_col": 17,
                         "enclosing_start_line": None, "enclosing_end_line": None},
                    ],
                },
            ]
        }

    def test_the_ast_name_match_calls_this_cross_file_call_ambiguous(self) -> None:
        # No SCIP involved: the AST adapter alone. `store` is untyped, two project
        # methods are named persist, so the edge is NOT rooted and the call lands
        # in the residue marked ambiguous with both candidates named.
        with Project(self.FILES) as project:
            ast_raw = adapter.discover(project.source, project.root)

        self.assertNotIn(
            "app.alpha:Alpha.persist",
            ast_raw["_calls"].get("app.router:make_job", set()),
            "the AST must NOT have rooted the ambiguous cross-file edge",
        )
        ambiguous = [r for r in ast_raw["residue"] if r["callee"] == "store.persist"]
        self.assertEqual(len(ambiguous), 1, "the call is in the AST residue")
        self.assertEqual(ambiguous[0]["why"], "ambiguous name")
        self.assertEqual(
            sorted(ambiguous[0]["candidates"]),
            ["app.alpha:Alpha.persist", "app.beta:Beta.persist"],
        )

    def test_scip_resolves_the_call_the_ast_left_ambiguous(self) -> None:
        with Project(self.FILES) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.hybrid_raw(ast_raw, self._normalized(), project.source)

        # SCIP disambiguated store.persist to exactly Alpha.persist, across files,
        # and the fixpoint-shaped graph now carries the edge the AST could not.
        self.assertEqual(
            hybrid["_calls"]["app.router:make_job"], {"app.alpha:Alpha.persist"}
        )
        self.assertNotIn("app.beta:Beta.persist", hybrid["_calls"]["app.router:make_job"])

    def test_the_getattr_scip_is_silent_about_is_still_enumerated(self) -> None:
        with Project(self.FILES) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.hybrid_raw(ast_raw, self._normalized(), project.source)

        by_key = {(r["file"], r["line"]): r for r in hybrid["scip_residue"]}
        # the getattr (line 2) SCIP said nothing about is named as unresolved ...
        self.assertIn(("app/router.py", 2), by_key)
        spot = by_key[("app/router.py", 2)]
        self.assertFalse(spot["resolved"])
        self.assertEqual(spot["kind"], "attribute_by_name")
        self.assertTrue(spot["reason"], "the blind spot is named, not dropped")
        # ... while the call SCIP DID resolve (line 3) is absent from the residue.
        self.assertNotIn(("app/router.py", 3), by_key)

    def test_both_halves_are_reported_together(self) -> None:
        with Project(self.FILES) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.hybrid_raw(ast_raw, self._normalized(), project.source)

        s = hybrid["scip_residue_summary"]
        self.assertEqual(s["scip_rooted_edges"], 1, "SCIP resolved one edge")
        self.assertGreaterEqual(
            s["unresolved_enumerated"], 1, "and one blind spot stayed enumerated"
        )


class ToolGuardTest(unittest.TestCase):
    def test_resolve_names_a_missing_indexer_rather_than_degrading(self) -> None:
        with patch("capcov.scip.resolve.shutil.which", return_value=None):
            with self.assertRaises(resolve.ScipToolsUnavailable) as ctx:
                resolve.resolve("/some/dir", {"_direct": {}, "_calls": {}, "surfaces": []},
                                language="python")
        self.assertIn("scip-python", str(ctx.exception))

    def test_resolve_rejects_an_unsupported_language(self) -> None:
        with self.assertRaises(ValueError):
            resolve.resolve("/some/dir", {}, language="ruby")

    def test_tools_available_is_a_bool_and_never_runs_a_tool(self) -> None:
        self.assertIsInstance(resolve.tools_available("python"), bool)


# ---------------------------------------------------------------------------
# Live: index the real APP tree with SCIP, resolve, and bind through the
# fixpoint. Skips when the indexer or the scip CLI is absent.


def _have_tools() -> bool:
    return resolve.tools_available("python")


class LiveResolveTest(unittest.TestCase):
    @unittest.skipUnless(_have_tools(), "needs scip-python + the scip CLI (set SCIP_CLI)")
    def test_scip_resolved_graph_binds_an_entity_through_a_call_chain(self) -> None:
        # get_widgets touches no table itself; it reaches `widgets` two hops away
        # through service -> repo. SCIP must resolve that chain across three files.
        with Project(APP) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.resolve(project.source, ast_raw, language="python")

        handler = "app.api:get_widgets"
        bound, _ = fixpoint.bind([handler], hybrid["_calls"], hybrid["_direct"])
        self.assertIn(
            "widgets", bound.get(handler, {}),
            "SCIP must resolve get_widgets -> list_widgets -> fetch_widgets",
        )

    @unittest.skipUnless(_have_tools(), "needs scip-python + the scip CLI (set SCIP_CLI)")
    def test_scip_stays_silent_about_the_dynamic_sites_and_the_residue_names_them(
        self,
    ) -> None:
        with Project(APP) as project:
            ast_raw = adapter.discover(project.source, project.root)
            hybrid = resolve.resolve(project.source, ast_raw, language="python")

        # the computed getattr in dynamics.py is unresolvable for any resolver;
        # SCIP emits no occurrence for it, so it must surface in the residue.
        residue_files = {r["file"] for r in hybrid["scip_residue"]}
        self.assertIn("app/dynamics.py", residue_files)
        self.assertTrue(hybrid["scip_resolved_edges"], "SCIP resolved real edges")

    @unittest.skipUnless(_have_tools(), "needs scip-python + the scip CLI (set SCIP_CLI)")
    def test_the_transient_index_is_cleaned_up(self) -> None:
        with Project(APP) as project:
            ast_raw = adapter.discover(project.source, project.root)
            resolve.resolve(project.source, ast_raw, language="python")
            self.assertFalse(
                (project.source / runner._INDEX_FILENAME).exists(),
                "resolve must remove the index.scip it wrote into the tree",
            )


if __name__ == "__main__":
    unittest.main()
