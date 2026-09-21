"""The ``--static scip`` profile's addition: the residue as rows, and the closure it licenses.

Four properties, one per section.

1. **The pack is a layer, not a fork.**  ``rules-static-closure-v1`` declares the
   two new primitives and the rules that use them, and re-declares -- byte for
   byte -- the five relations it borrows from the frozen static schema and from
   ``rules-static-v1``.  ``combine`` merges declarations by identity, so a
   borrowed declaration that drifted would be caught there; this asserts it
   directly, because a silent widening of ``static_entity`` is exactly the
   failure a merge-by-name cannot see coming.

2. **The residue becomes rows, and only an empty one licenses the witness.**
   The resolver's ``scip_residue`` is emitted as ``static_unresolved_call_site`` in
   every case -- "name unresolved, do not drop" -- and ``call_graph_closed`` is
   emitted for a scope if and only if the census was taken and no residue row
   falls inside it.  Per-document scopes are closed one document at a time.

3. **The negative claim resolves under closure and not otherwise.**  "route R
   does not reach table T" is supported when the call graph is closed and R
   reaches no such table, refuted -- with or without closure -- when R does
   reach it, and unresolved when the residue is not empty.  The three run in
   the Python kernel here and, where Souffle is present, in both.

4. **The export does not change.**  The profile's rows are a separate fragment:
   an export made with the profile has the same index identity and the same
   bundle digest as one made without it, so turning the profile on cannot
   renumber a single existing evidence id.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from capcov.claims import (Claim, Constant, Context, EvidenceMapping, validate_bundle)
from capcov.claims.evaluator import evaluate
from capcov.claims.static import closure, scip_facts
from capcov.claims.static.combine import CombineError, combine
from capcov.scip import resolve

try:
    from .static_rules import go_app
    from .static_rules.adapter import PACK_PATH, load_pack, pack_bundle, read_json
except ImportError:  # unittest discover -s imports this directory as top-level
    from static_rules import go_app
    from static_rules.adapter import PACK_PATH, load_pack, pack_bundle, read_json

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SRC = PACKAGE_ROOT / "src"
FROZEN = SRC / "capcov" / "claims" / "static" / "schema_static_v1.json"
GO_APP = PACKAGE_ROOT / "tests" / "fixtures" / "go_app"

#: A table the go_app route reaches nothing of: ``sessions`` is declared as an
#: entity with no op site, so under a closed call graph "GET /jobs/{id} does not
#: reach sessions" is a statement the facts settle.
UNREACHED_TABLE = "sessions"
#: A table the route does reach (GetJob -> Service.Fetch -> Repo.Get -> jobs).
REACHED_TABLE = "jobs"
#: One unresolved call site, in a document of the slice.
RESIDUE = [{"file": "internal/service/service.go", "line": 12, "callee": "h.dispatch",
            "kind": "unresolved", "reason": "untyped receiver"}]
CLAIM_ID = "claim-route-reaches-no-table"

_HAVE_SOUFFLE = shutil.which(os.environ.get("SOUFFLE") or "souffle") is not None
_HAVE_SCIP = bool(shutil.which("scip-go") and shutil.which("scip") and shutil.which("go"))


def _have_treesitter() -> bool:
    """The go call-site census needs the ``treesitter`` extra, and says so when it
    is absent rather than returning an empty census -- so the live profile run
    needs it too."""
    try:
        from capcov.scip import blindspots

        blindspots._ts_language("go")
    except Exception:  # noqa: BLE001 - any failure means no census
        return False
    return True


_HAVE_TREESITTER = _have_treesitter()


def _ast(residue=(), *, census: bool = True) -> dict:
    """go_app's tree-sitter side plus a third entity and a chosen residue."""
    ast = go_app.ast_raw()
    ast["entities"].append({"name": UNREACHED_TABLE, "symbol": "Session", "module": "",
                            "file": "models/models.go", "line": 19})
    ast["scip_residue"] = [dict(entry) for entry in residue]
    if not census:
        del ast["blind_spots"]
    return ast


def _export(ast: dict, scope=None):
    raw = go_app.golden_raw()
    from capcov.scip import runner

    result = scip_facts.export_bundle(
        go_app.normalized(raw), ast_raw=ast, source_root=go_app.GO_APP, language="go",
        scope=scope, index_digest=go_app.json_file_digest(raw),
        index_digest_kind=runner.INDEX_DIGEST_JSON)
    assert result.status == scip_facts.STATUS_COMPLETE, result.messages
    return result


def _rows(bundle, relation) -> list[list]:
    return sorted([term.value for term in fact.terms][1:]
                  for fact in bundle.facts if fact.relation == relation)


def _bundle(ast: dict, *, table: str = UNREACHED_TABLE, refutation: bool = False, scope=None):
    exported = _export(ast, scope)
    index = dict(exported.bundle.metadata)["index_digest"]
    claim = Claim("static_route_no_table",
                  (Constant(index, "digest"), Constant(go_app.SURFACE, "symbol"),
                   Constant(table, "symbol")),
                  Context.from_mapping({"index": index}), id=CLAIM_ID)
    mappings = []
    if refutation:
        # A route that DOES reach the table refutes the negative claim, and needs
        # no completeness witness to do it: one positive reach is a counterexample.
        mappings = [EvidenceMapping("static_route_no_table", "static_route_reaches_table",
                                    "refutation", context_indices=("index",),
                                    bindings=(("index", "index"), ("surface", "surface"),
                                              ("table", "table")),
                                    claim_id=CLAIM_ID)]
    bundle = closure.attach(exported.bundle, ast, pack_bundle(), claims=[claim],
                            mappings=mappings)
    return bundle, exported, index


class ClosurePackIsALayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = closure.load_pack()

    def test_the_pack_validates_alone(self) -> None:
        self.assertEqual(validate_bundle(closure.pack_bundle()), ())

    def test_the_borrowed_declarations_are_the_frozen_and_base_pack_declarations(self) -> None:
        frozen = {item["name"]: item for item in read_json(FROZEN)["relations"]}
        base = load_pack()
        base_derived = {item["name"]: item for item in base["derived"]}
        borrowed = {item["name"]: item for item in self.pack["borrowed_declarations"]}
        self.assertEqual(set(borrowed),
                         {"static_entity", "static_scope", "static_edge",
                          "static_path_to_storage", "static_route_declared_surface"})
        self.assertEqual(self.pack["base_pack"], base["id"])
        for name, declaration in borrowed.items():
            with self.subTest(relation=name):
                source = frozen.get(name) or base_derived[name]
                self.assertEqual(declaration, source,
                                 f"{name} drifted from {PACK_PATH.name} / {FROZEN.name}")

    def test_the_new_primitives_are_the_resolvers_and_declare_it(self) -> None:
        primitives = {item["name"]: item for item in self.pack["primitives"]}
        self.assertEqual(set(primitives), {closure.UNRESOLVED_RELATION, closure.CLOSED_RELATION})
        for name, item in primitives.items():
            with self.subTest(relation=name):
                self.assertEqual(item["producer_classes"], [closure.PRODUCER_CLASS])
                self.assertTrue(item["primitive"])
                self.assertEqual(item["context_indices"], ["index"])
        self.assertEqual(primitives[closure.CLOSED_RELATION]["modality"], "completeness")
        self.assertEqual(primitives[closure.CLOSED_RELATION]["completes"], "static_edge")

    def test_a_borrowed_declaration_that_widened_would_be_refused_by_combine(self) -> None:
        """The merge is by identity, and this is the negative control for it."""
        from capcov.claims import Bundle, Column, RelationDecl

        widened = RelationDecl(
            "static_entity",
            (Column("index", "digest", True), Column("entity", "symbol"),
             Column("path", "symbol"), Column("line", "unsigned"), Column("table", "symbol"),
             Column("extra", "symbol")),
            modality="observation", binding="static", primitive=True, context_indices=("index",))
        with self.assertRaises(CombineError):
            combine(closure.pack_bundle(), Bundle((widened,)))


class ResidueAndWitnessTests(unittest.TestCase):
    def test_an_empty_residue_closes_the_whole_index_scope(self) -> None:
        bundle, _, _ = _bundle(_ast())
        self.assertEqual(_rows(bundle, closure.CLOSED_RELATION), [[closure.SCOPE_TOKEN_ALL]])
        self.assertEqual(_rows(bundle, closure.UNRESOLVED_RELATION), [])

    def test_a_residue_is_enumerated_and_withholds_the_witness(self) -> None:
        bundle, _, _ = _bundle(_ast(RESIDUE))
        self.assertEqual(_rows(bundle, closure.UNRESOLVED_RELATION),
                         [["internal/service/service.go", 12, "h.dispatch"]])
        self.assertEqual(_rows(bundle, closure.CLOSED_RELATION), [],
                         "an unresolved call site is exactly what closure may not assume away")

    def test_a_document_set_scope_is_closed_one_document_at_a_time(self) -> None:
        documents = ["api/jobs.go", "gorm/gorm.go", "internal/jobs/repo.go",
                     "internal/service/service.go", "models/models.go"]
        bundle, _, _ = _bundle(_ast(RESIDUE), scope=scip_facts.Scope.document_set(documents))
        closed = [row[0] for row in _rows(bundle, closure.CLOSED_RELATION)]
        self.assertEqual(closed, [d for d in documents if d != "internal/service/service.go"])

    def test_no_census_means_no_witness_even_with_no_residue(self) -> None:
        """'No residue' cannot be asserted about a census nobody took."""
        ast = _ast(census=False)
        exported = _export(ast)
        self.assertFalse(dict(exported.bundle.metadata)["census_available"])
        fragment = closure.closure_bundle(exported.bundle, ast)
        self.assertEqual(_rows(fragment, closure.CLOSED_RELATION), [])

    def test_every_emitted_row_is_attributed_to_the_resolver(self) -> None:
        bundle, _, _ = _bundle(_ast(RESIDUE))
        emitted = [record for record in bundle.evidence
                   if record.atom.relation in (closure.UNRESOLVED_RELATION,
                                               closure.CLOSED_RELATION)]
        self.assertTrue(emitted)
        for record in emitted:
            with self.subTest(evidence=record.id):
                self.assertEqual(record.source.split(" ", 1)[0], closure.PRODUCER_CLASS)
                self.assertTrue(record.id.startswith("scip:"), record.id)
                self.assertTrue(record.depends_on, "a row with no provenance is not evidence")

    def test_the_residue_row_carries_the_callee_the_source_spells(self) -> None:
        """An unresolved site has no SCIP symbol; the text is what there is."""
        self.assertEqual(closure.residue_rows({"scip_residue": RESIDUE}),
                         [("internal/service/service.go", 12, "h.dispatch")])


class NegativeClaimResolutionTests(unittest.TestCase):
    def _verdict(self, bundle):
        report = evaluate(bundle)
        self.assertEqual(report.status.value, "complete", report.message)
        [entry] = [e for e in report.claims if e.claim.id == CLAIM_ID]
        return entry.result.semantic.value, entry.result.operational.value

    def test_supported_when_the_call_graph_is_closed_and_the_table_is_unreached(self) -> None:
        bundle, _, _ = _bundle(_ast())
        self.assertEqual(self._verdict(bundle), ("supported", "complete"))

    def test_unresolved_when_the_residue_is_not_empty(self) -> None:
        bundle, _, _ = _bundle(_ast(RESIDUE))
        self.assertEqual(self._verdict(bundle), ("unresolved", "complete"))

    def test_refuted_when_the_route_reaches_the_table(self) -> None:
        bundle, _, _ = _bundle(_ast(), table=REACHED_TABLE, refutation=True)
        self.assertEqual(self._verdict(bundle), ("refuted", "complete"))

    def test_refutation_needs_no_closure_witness(self) -> None:
        """One positive reach refutes a negative claim whatever the residue says."""
        bundle, _, _ = _bundle(_ast(RESIDUE), table=REACHED_TABLE, refutation=True)
        self.assertEqual(_rows(bundle, closure.CLOSED_RELATION), [])
        self.assertEqual(self._verdict(bundle), ("refuted", "complete"))

    def test_the_profile_and_the_exporter_count_the_same_census(self) -> None:
        """One residue, two readings of it: the exporter's rows and the profile's agree.

        ``scip_facts`` already exports the residue as ``scip_unresolved_site``
        (its own, exporter-attributed reading).  The profile's rows are the
        producer-attributed reading the closure witness is defined against, and
        a witness defined against a *different* census than the one the bundle
        already carries would be a closure of nothing.
        """
        bundle, _, _ = _bundle(_ast(RESIDUE))
        self.assertEqual([row[:2] for row in _rows(bundle, "scip_unresolved_site")],
                         [row[:2] for row in _rows(bundle, closure.UNRESOLVED_RELATION)])

    @unittest.skipUnless(_HAVE_SOUFFLE, "needs the souffle executable")
    def test_both_kernels_agree_on_all_three_outcomes(self) -> None:
        from capcov.claims.differential import compare

        with tempfile.TemporaryDirectory() as tmp:
            for label, bundle in (
                    ("supported", _bundle(_ast())[0]),
                    ("unresolved", _bundle(_ast(RESIDUE))[0]),
                    ("refuted", _bundle(_ast(), table=REACHED_TABLE, refutation=True)[0])):
                with self.subTest(outcome=label):
                    result = compare(bundle, replay_root=str(Path(tmp) / label))
                    self.assertTrue(result.matched, result.replay_path)


class TheExportItselfIsUnchangedTests(unittest.TestCase):
    def test_the_index_identity_and_digest_do_not_move(self) -> None:
        """The fragment is beside the export, so no existing evidence id is renumbered."""
        ast = _ast(RESIDUE)
        exported = _export(ast)
        before = (dict(exported.bundle.metadata)["index_digest"],
                  scip_facts.bundle_digest(exported.bundle),
                  sorted(record.id for record in exported.bundle.evidence))
        closure.attach(exported.bundle, ast, pack_bundle())
        after = (dict(exported.bundle.metadata)["index_digest"],
                 scip_facts.bundle_digest(exported.bundle),
                 sorted(record.id for record in exported.bundle.evidence))
        self.assertEqual(before, after)

    def test_the_export_declares_neither_new_relation(self) -> None:
        exported = _export(_ast(RESIDUE))
        names = {declaration.name for declaration in exported.bundle.relations}
        self.assertNotIn(closure.CLOSED_RELATION, names)
        self.assertNotIn(closure.UNRESOLVED_RELATION, names)


class AbsentScipToolsAreNamedTests(unittest.TestCase):
    """The profile refuses in ``capcov discover --resolver scip``'s own words."""

    def test_require_scip_tools_raises_the_resolvers_own_message(self) -> None:
        with unittest.mock.patch.object(resolve.shutil, "which", return_value=None):
            with self.assertRaises(resolve.ScipToolsUnavailable) as caught:
                closure.require_scip_tools("go", GO_APP)
        self.assertIn("--resolver scip needs the go indexer 'scip-go'", str(caught.exception))
        self.assertIn("Install it with:", str(caught.exception))

    def test_an_unsupported_language_is_named_not_swallowed(self) -> None:
        with self.assertRaises(ValueError):
            closure.require_scip_tools("cobol", GO_APP)

    def test_the_cli_reports_it_as_an_operational_failure(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "capcov", "experiment", "claims", "static",
             "--static", "scip", "--target", str(GO_APP)],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"})
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        document = json.loads(proc.stdout)
        self.assertEqual(document["operational_failure"], "scip-tools-unavailable")
        self.assertIn("--resolver scip needs the go indexer 'scip-go'", document["error"])

    def test_the_cli_checks_census_dependencies_before_starting_scip(self) -> None:
        from capcov.claims.cli import main as claims_main

        output = io.StringIO()
        with unittest.mock.patch(
            "capcov.scip.blindspots.require_census_tools",
            side_effect=ValueError("blind-spot enumeration for 'go' needs the 'treesitter' extra"),
        ) as census, unittest.mock.patch(
            "capcov.claims.static.closure.require_scip_tools"
        ) as scip_tools, unittest.mock.patch(
            "capcov.scip.runner.run_scip_index"
        ) as indexer, contextlib.redirect_stdout(output):
            status = claims_main([
                "claims", "static", "--static", "scip", "--target", str(GO_APP),
                "--language", "go",
            ])

        self.assertEqual(status, 3)
        self.assertEqual(census.call_args.args, ("go",))
        scip_tools.assert_not_called()
        indexer.assert_not_called()
        document = json.loads(output.getvalue())
        self.assertEqual(document["operational_failure"], "census-unavailable")
        self.assertIn("treesitter' extra", document["error"])

    def test_the_cli_refuses_an_unknown_profile(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "capcov", "experiment", "claims", "static",
             "--static", "ast", "--target", str(GO_APP)],
            text=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(SRC)})
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("unknown static profile 'ast'", proc.stdout)


@unittest.skipUnless(_HAVE_SCIP and _HAVE_TREESITTER,
                     "needs scip-go, the scip CLI, go and the treesitter extra")
class LiveStaticProfileTests(unittest.TestCase):
    """The present path: index go_app for real and emit the closure beside the export."""

    def test_the_profile_writes_a_bundle_carrying_the_closure_relations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "go_app"
            shutil.copytree(GO_APP, tree)
            ast_raw = Path(tmp) / "ast.json"
            ast_raw.write_text(json.dumps(_ast()), encoding="utf-8")
            out = Path(tmp) / "bundle.json"
            proc = subprocess.run(
                [sys.executable, "-m", "capcov", "experiment", "claims", "static",
                 "--static", "scip", "--target", str(tree), "--language", "go",
                 "--ast-raw", str(ast_raw), "--out", str(out)],
                text=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(SRC)})
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            document = json.loads(proc.stdout)
            self.assertEqual(document["profile"], "scip")
            self.assertTrue(document["census_available"])
            # go_app is a hand-written fixture with no dynamic dispatch: the real
            # census over the real index finds nothing unresolved, so the scope closes
            self.assertEqual(document[closure.UNRESOLVED_RELATION], 0)
            self.assertEqual(document[closure.CLOSED_RELATION], [closure.SCOPE_TOKEN_ALL])
            payload = json.loads(out.read_text())
            relations = {item["name"] for item in payload["relations"]}
            self.assertIn(closure.CLOSED_RELATION, relations)
            self.assertIn(closure.UNRESOLVED_RELATION, relations)


if __name__ == "__main__":
    unittest.main()
