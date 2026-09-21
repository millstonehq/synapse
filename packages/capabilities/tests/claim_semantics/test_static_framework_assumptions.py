"""Framework assumptions: a reviewed edge, and what it is allowed to settle.

Seven properties, one per section.

1. **A document, not a note.**  Every row names its framework, its mechanism and
   the file:line it stands for; the document names its reviewer, the commit it
   was signed against and the date it expires.  A framework or mechanism nobody
   enumerated, a missing signature, an expired review, a document signed against
   another commit than the index was taken at, and a symbol this index does not
   declare are each refused *by name* -- an assumption that cannot be checked
   for what it is about is not a weaker assumption, it is an unreviewable one.

2. **The pack is a layer, not a fork.**  ``rules-static-framework-v1`` owns five
   ``framework-assumption`` primitives and re-declares -- byte for byte -- the
   fifteen relations it borrows from the frozen schema, ``rules-static-v1``,
   ``rules-static-closure-v1`` and ``rules-static-reflexion-v1``.  No rule of it
   heads ``static_edge``, ``static_reaches``, ``static_capability_op`` or
   ``call_graph_closed``: the relation ``call_graph_closed`` completes is exactly
   the relation this pack does not touch.

3. **What the fragment emits.**  The reviewed row, the compatibility witness and
   the two closures -- every row ``framework-assumption``-classed, depending on
   the index's own evidence, and every reviewer-owned one carrying
   ``Evidence.kind == "assumption"`` so the registry can give it a run-independent
   ``asm:`` id and withdraw it.

4. **Without the document the route is blocked.**  ``go_app`` with a synthetic
   registry route -- the recognizer sees the surface and can attribute only the
   registry's dispatcher, whose call of the stored handler value is the census's
   one residue row.  The route binds no entity, ``static_entity_blocked`` names
   the dispatcher as the symbol the doubt enters through, and
   ``call_graph_closed`` is withheld for the whole index.

5. **With the document the route binds, and the certificate says whose say-so
   it was.**  ``static_capability_op_assumed`` carries the registry route's two
   operations, the certificate for one of them rechecks, and the assumption ids
   its leaves carry are exactly the reviewed rows it rests on.  The assumed
   closure settles what the resolved one cannot: the entity nothing reaches is
   ``static_entity_dead_assumed`` while ``static_entity_dead`` stays empty.

6. **Withdrawing the row puts it back.**  ``assumptions.withdraw`` of the one
   reviewed edge -- the counterfactual the registry exists to make askable --
   takes ``call_graph_closed_assumed`` with it (a witness that says every site
   is covered rests on the rows that cover them), leaves the reviewer's own
   closure standing, and re-derives ``static_entity_blocked_assumed`` naming the
   dispatcher again.  Nothing becomes dead: a dropped assumption is a missing
   premise, never a verdict.

7. **A row the producer cannot apply is enumerated, and the witness goes.**  A
   site the census gives a second unresolved callee is applied not at all
   (discharge is a ``(path, line)`` join, so applying it would discharge that
   other call too); a row for a site with no residue at all stands for nothing;
   a row for a document out of scope cannot be seen.  Each is a
   ``framework_assumption_unapplied`` row with its reason, each withholds
   ``assumptions_closed``, and the resolved account is byte-identical with the
   fragment merged and without it.

The souffle sections skip, by name, where the executable is absent.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from capcov.claims import Bundle, Column, RelationDecl, validate_bundle
from capcov.claims import assumptions as assumption_registry
from capcov.claims.evaluator import evaluate
from capcov.claims.static import certificate, closure, framework, pilot, reflexion
from capcov.claims.static.combine import CombineError, combine

try:
    from .static_rules import go_app
    from .static_rules.adapter import PACK_PATH, load_pack, pack_bundle, read_json
except ImportError:  # unittest discover -s imports this directory as top-level
    from static_rules import go_app
    from static_rules.adapter import PACK_PATH, load_pack, pack_bundle, read_json

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SRC = PACKAGE_ROOT / "src"
FROZEN = SRC / "capcov" / "claims" / "static" / "schema_static_v1.json"
CLOSURE_PACK = SRC / "capcov" / "claims" / "static" / closure.PACK_NAME
REFLEXION_PACK = SRC / "capcov" / "claims" / "static" / reflexion.PACK_NAME

#: The synthetic registry route.  ``go_app``'s ``handle(pattern, fn)`` is the
#: registry's dispatcher: a route registered into a package-level slice by an
#: ``init()`` and served by a loop is visible to the recognizer as a surface
#: whose only attributable callable is that dispatcher, and the call of the
#: stored handler value inside it is what no index resolves.
REGISTRY_SURFACE = "http:GET /jobs"
REGISTRY_NODE = f"{go_app.MODULE}/api:handle"
DISPATCHER = go_app.HANDLE                  # api/jobs.go:20, func handle(...)
HANDLER = go_app.GET_JOB
DISPATCH_PATH = "api/jobs.go"
DISPATCH_LINE = 20
#: A third entity nothing reaches, under the assumptions or without them.
UNREACHED_ENTITY = "sessions"
RESOLVED_SURFACE = go_app.SURFACE

#: The census of the fixture with that route: one residue row, the registry's
#: call of the handler value it holds.
REGISTRY_RESIDUE = [{"file": DISPATCH_PATH, "line": DISPATCH_LINE, "callee": "fn",
                     "kind": "unresolved", "reason": "handler value from an init registry"}]
#: A second unresolved callee on the dispatcher's own line: discharge joins on
#: ``(path, line)``, so applying the row here would discharge this call too.
CO_LOCATED_RESIDUE = [{"file": DISPATCH_PATH, "line": DISPATCH_LINE,
                       "callee": "reflect.ValueOf(fn).Call", "kind": "unresolved",
                       "reason": "reflection"}]

REVIEWER = "a reviewer <review@example.invalid>"
COMMIT = "0" * 40
EXPIRES = "2999-01-01"

_HAVE_SOUFFLE = shutil.which(os.environ.get("SOUFFLE") or "souffle") is not None


def _row(*, src: str = DISPATCHER, dst: str = HANDLER, framework_name: str = "net/http",
         mechanism: str = "init-registry", path: str = DISPATCH_PATH,
         line: int = DISPATCH_LINE) -> dict:
    return {"src": src, "dst": dst, "framework": framework_name, "mechanism": mechanism,
            "path": path, "line": line}


def _document(*rows: dict, closed: bool = True, **overrides) -> dict:
    document = {"schema_version": 1, "reviewer": REVIEWER, "commit": COMMIT,
                "expires": EXPIRES, "closed": closed,
                "assumptions": list(rows) or [_row()]}
    document.update(overrides)
    return document


def _assumptions(*rows: dict, closed: bool = True, **overrides) -> framework.AssumptionSet:
    return framework.assumptions_from_document(_document(*rows, closed=closed, **overrides))


def _ast(residue=None, *, registry_route: bool = True) -> dict:
    """``go_app``'s hand-built tree-sitter side plus the synthetic registry route."""
    ast = go_app.ast_raw()
    ast["entities"].append({"name": UNREACHED_ENTITY, "symbol": "Session", "module": "",
                            "file": "models/models.go", "line": 19})
    if registry_route:
        ast["surfaces"].append({
            "id": REGISTRY_SURFACE, "kind": "http", "method": "GET", "path": "/jobs",
            "handler": REGISTRY_NODE, "handler_symbol": "handle",
            "file": DISPATCH_PATH, "line": go_app.ROUTE_LINE, "mounted": True})
        ast["_node_locations"][REGISTRY_NODE] = [DISPATCH_PATH, DISPATCH_LINE]
    ast["scip_residue"] = [dict(entry) for entry in
                           (REGISTRY_RESIDUE if residue is None else residue)]
    return ast


def _export(ast: dict):
    result = go_app.export(ast=ast)
    assert result.status == "complete", result.messages
    return result


def _bundle(ast: dict, assumptions: framework.AssumptionSet | None = None, *,
            model: reflexion.CapabilityModel | None = None) -> tuple[Bundle, str]:
    """Export + closure fragment + the base and reflexion packs (+ the assumptions)."""
    exported = _export(ast)
    export = exported.bundle
    index = dict(export.metadata)["index_digest"]
    tree = dict(dict(export.metadata)["tree"])["digest"]
    fragments = [closure.closure_bundle(export, ast), pack_bundle(), reflexion.pack_bundle()]
    if model is not None:
        fragments.append(reflexion.model_bundle(export, model))
    if assumptions is None:
        decls = {decl.name: decl for decl in export.relations}
        atom, record = pilot.source_tree_observation(decls, tree,
                                                     source=framework.TREE_OBSERVATION_SOURCE)
        observed = Bundle(export.relations, facts=(atom,), evidence=(record,))
        return combine(export, observed, *fragments, validate=True), index
    return framework.attach(export, ast, assumptions, *fragments, model=model,
                            tree_digest=None if model else tree), index


def _closure_of(bundle: Bundle) -> dict[str, list[list]]:
    report = evaluate(bundle)
    assert report.status.value == "complete", report.message
    return {name: sorted(list(row) for row in rows) for name, rows in report.relations}


def _payload(relations: dict[str, list[list]], name: str) -> list[list]:
    """The rows of ``name`` with the index context column dropped."""
    return sorted(row[1:] for row in relations.get(name, ()))


def _rows(bundle: Bundle, relation: str) -> list[list]:
    return sorted([term.value for term in fact.terms][1:]
                  for fact in bundle.facts if fact.relation == relation)


def _certified_relations(artifact: dict) -> set[str]:
    seen: set[str] = set()

    def walk(node):
        if not isinstance(node, dict):
            return
        if "relation" in node:
            seen.add(node["relation"])
        for premise in node.get("premises") or ():
            walk(premise)
        for absent in node.get("negated") or ():
            walk(absent)

    walk(artifact.get("derivation"))
    return seen


class ADocumentNotANoteTests(unittest.TestCase):
    """Section 1."""

    def test_a_well_formed_document_reads_into_one_signed_row(self) -> None:
        assumptions = _assumptions()
        self.assertEqual(assumptions.rows, (framework.FrameworkAssumption(
            DISPATCHER, HANDLER, "net/http", "init-registry", DISPATCH_PATH, DISPATCH_LINE),))
        self.assertTrue(assumptions.closed)
        self.assertEqual(assumptions.commit, COMMIT)
        self.assertEqual(assumptions.symbols, tuple(sorted({DISPATCHER, HANDLER})))

    def test_the_digest_covers_the_signature_the_commit_and_the_expiry(self) -> None:
        """A certificate names the document; editing any of it must move the name."""
        base = _assumptions().digest
        for field, value in (("commit", "1" * 40), ("expires", "2998-01-01"),
                             ("reviewer", "someone else")):
            with self.subTest(field=field):
                self.assertNotEqual(_assumptions(**{field: value}).digest, base)
        self.assertNotEqual(_assumptions(closed=False).digest, base)

    def test_an_unenumerated_framework_or_mechanism_is_refused_by_name(self) -> None:
        with self.assertRaises(framework.AssumptionsInputError) as unknown_framework:
            _assumptions(_row(framework_name="spring"))
        self.assertIn("unknown framework 'spring'", str(unknown_framework.exception))
        with self.assertRaises(framework.AssumptionsInputError) as unknown_mechanism:
            _assumptions(_row(mechanism="magic"))
        self.assertIn("unknown net/http mechanism 'magic'", str(unknown_mechanism.exception))

    def test_the_three_frameworks_this_layer_exists_for_are_all_readable(self) -> None:
        """net/http registries, Laravel container/facade, FastAPI Depends."""
        self.assertEqual(sorted(framework.MECHANISMS), ["fastapi", "laravel", "net/http"])
        for framework_name, mechanisms in framework.MECHANISMS.items():
            for mechanism in mechanisms:
                with self.subTest(framework=framework_name, mechanism=mechanism):
                    assumptions = _assumptions(_row(framework_name=framework_name,
                                                    mechanism=mechanism))
                    self.assertEqual(assumptions.rows[0].framework, framework_name)
                    self.assertEqual(assumptions.rows[0].mechanism, mechanism)

    def test_an_unsigned_undated_or_uncommitted_document_is_refused(self) -> None:
        for field in ("reviewer", "commit"):
            with self.subTest(field=field):
                with self.assertRaises(framework.AssumptionsInputError) as ctx:
                    _assumptions(**{field: ""})
                self.assertIn(field, str(ctx.exception))
        with self.assertRaises(framework.AssumptionsInputError) as expiry:
            _assumptions(expires="soon")
        self.assertIn("ISO date", str(expiry.exception))
        with self.assertRaises(framework.AssumptionsInputError):
            framework.assumptions_from_document({"schema_version": 2})

    def test_an_expired_document_is_refused_rather_than_used(self) -> None:
        assumptions = _assumptions(expires="2020-01-01")
        with self.assertRaises(framework.AssumptionsExpired) as ctx:
            framework.require_unexpired(assumptions, date(2020, 1, 2))
        self.assertIn("expired on 2020-01-01", str(ctx.exception))
        # the boundary: the day it expires is still a day it holds
        framework.require_unexpired(assumptions, date(2020, 1, 1))

    def test_the_expiry_is_enforced_where_the_fragment_is_built(self) -> None:
        ast = _ast()
        export = _export(ast).bundle
        with self.assertRaises(framework.AssumptionsExpired):
            framework.assumptions_bundle(export, ast, _assumptions(expires="2020-01-01"),
                                         today=date(2021, 1, 1))

    def test_a_symbol_this_index_does_not_declare_is_named_not_dropped(self) -> None:
        ast = _ast()
        export = _export(ast).bundle
        with self.assertRaises(framework.AssumptionsInputError) as ctx:
            framework.assumptions_bundle(export, ast, _assumptions(_row(dst="not/a/symbol")))
        self.assertIn("not/a/symbol", str(ctx.exception))

    def test_a_commit_binding_is_checked_when_the_index_names_one(self) -> None:
        """And reported unverified, never checked, when it does not."""
        ast = _ast()
        export = _export(ast).bundle
        self.assertIsNone(framework.index_commit(export))
        self.assertFalse(framework.require_commit_binding(export, _assumptions()))

        decls = {decl.name: decl for decl in export.relations}
        atom, record = go_app._fact(
            "scip_index_commit", decls["scip_index_commit"],
            {"index": dict(export.metadata)["index_digest"], "commit": "1" * 40},
            "external:test:scip_index_commit", "scip test")
        with_commit = Bundle(export.relations, facts=(*export.facts, atom),
                             evidence=(*export.evidence, record), metadata=export.metadata)
        self.assertTrue(
            framework.require_commit_binding(with_commit, _assumptions(commit="1" * 40)))
        with self.assertRaises(framework.AssumptionsInputError) as ctx:
            framework.require_commit_binding(with_commit, _assumptions())
        self.assertIn("signed against commit", str(ctx.exception))


class ThePackIsALayerTests(unittest.TestCase):
    """Section 2."""

    def setUp(self) -> None:
        self.pack = framework.load_pack()

    def test_the_pack_validates_alone(self) -> None:
        self.assertEqual(validate_bundle(framework.pack_bundle()), ())

    def test_the_borrowed_declarations_are_their_owners_declarations(self) -> None:
        frozen = {item["name"]: item for item in read_json(FROZEN)["relations"]}
        base = load_pack()
        owned = {item["name"]: item
                 for section in ("primitives", "supplementary_primitives", "derived")
                 for item in base[section]}
        for pack_path in (CLOSURE_PACK, REFLEXION_PACK):
            document = read_json(pack_path)
            for section in ("primitives", "derived"):
                for item in document.get(section, ()):
                    owned.setdefault(item["name"], item)
        borrowed = {item["name"]: item for item in self.pack["borrowed_declarations"]}
        self.assertEqual(set(borrowed), {
            "capability_edge", "capability_edge_closed", "capability_map",
            "capability_map_closed", "capability_map_describes_index", "static_edge",
            "static_entity", "static_index_current", "static_op_owner", "static_reaches",
            "static_root", "static_route_handler", "static_scope", "static_site_owner",
            "static_unresolved_call_site"})
        self.assertEqual(self.pack["base_pack"], base["id"])
        self.assertEqual(self.pack["closure_pack"], closure.PACK_ID)
        self.assertEqual(self.pack["reflexion_pack"], reflexion.PACK_ID)
        for name, declaration in borrowed.items():
            with self.subTest(relation=name):
                source = frozen.get(name) or owned[name]
                self.assertEqual(declaration, source,
                                 f"{name} drifted from {PACK_PATH.name} / {FROZEN.name} / "
                                 f"{closure.PACK_NAME} / {reflexion.PACK_NAME}")

    def test_the_primitives_declare_the_assumption_producer_and_what_they_close(self) -> None:
        primitives = {item["name"]: item for item in self.pack["primitives"]}
        self.assertEqual(set(primitives), {
            framework.EDGE_RELATION, framework.UNAPPLIED_RELATION, framework.DESCRIBES_RELATION,
            framework.CLOSED_RELATION, framework.CALL_GRAPH_CLOSED_RELATION})
        for name, item in primitives.items():
            with self.subTest(relation=name):
                self.assertEqual(item["producer_classes"], [framework.PRODUCER_CLASS])
                self.assertTrue(item["primitive"])
        self.assertEqual(primitives[framework.EDGE_RELATION]["modality"], "assumption")
        self.assertEqual(primitives[framework.CLOSED_RELATION]["completes"],
                         "static_edge_assumed")
        self.assertEqual(primitives[framework.CALL_GRAPH_CLOSED_RELATION]["completes"],
                         "static_reaches_assumed")
        self.assertEqual(primitives[framework.DESCRIBES_RELATION]["compatibility_targets"],
                         [framework.EDGE_RELATION, "static_edge"])

    def test_the_producer_class_is_its_own(self) -> None:
        """Not scip (what an index said), not phpstan, not reviewer."""
        self.assertEqual(framework.PRODUCER_CLASS, "framework-assumption")
        self.assertNotIn(framework.PRODUCER_CLASS,
                         (closure.PRODUCER_CLASS, reflexion.PRODUCER_CLASS))

    def test_no_rule_touches_the_relation_call_graph_closed_completes(self) -> None:
        heads = {rule["head"]["relation"] for rule in self.pack["rules"]}
        self.assertEqual(heads & {"static_edge", "static_reaches", "static_reaches_eq",
                                  "call_graph_closed", "static_capability_op",
                                  "static_entity_dead", "static_entity_blocked"}, set())
        self.assertIn("static_edge_assumed", heads)
        self.assertIn("static_reaches_assumed", heads)

    def test_a_borrowed_declaration_that_widened_would_be_refused_by_combine(self) -> None:
        widened = RelationDecl(
            "static_edge",
            (Column("index", "digest", True), Column("src", "symbol"),
             Column("dst", "symbol"), Column("framework", "symbol")),
            modality="derived", binding="static", primitive=False, context_indices=("index",))
        with self.assertRaises(CombineError):
            combine(framework.pack_bundle(), Bundle((widened,)))


class WhatTheFragmentEmitsTests(unittest.TestCase):
    """Section 3."""

    def setUp(self) -> None:
        self.ast = _ast()
        self.export = _export(self.ast).bundle
        self.assumptions = _assumptions()
        self.fragment = framework.assumptions_bundle(self.export, self.ast, self.assumptions)

    def test_the_reviewed_row_names_the_framework_the_mechanism_and_the_site(self) -> None:
        self.assertEqual(_rows(self.fragment, framework.EDGE_RELATION),
                         [[DISPATCHER, HANDLER, "net/http", "init-registry",
                           DISPATCH_PATH, DISPATCH_LINE]])
        self.assertEqual(_rows(self.fragment, framework.UNAPPLIED_RELATION), [])

    def test_both_witnesses_and_the_binding_are_emitted_on_an_applied_document(self) -> None:
        self.assertEqual(_rows(self.fragment, framework.CLOSED_RELATION),
                         [[self.assumptions.digest]])
        self.assertEqual(_rows(self.fragment, framework.CALL_GRAPH_CLOSED_RELATION),
                         [[closure.SCOPE_TOKEN_ALL]])
        index = dict(self.export.metadata)["index_digest"]
        self.assertEqual([fact.terms[0].value for fact in self.fragment.facts
                          if fact.relation == framework.DESCRIBES_RELATION],
                         [self.assumptions.digest])
        self.assertEqual(_rows(self.fragment, framework.DESCRIBES_RELATION), [[index]])

    def test_every_row_is_the_assumption_producers_and_depends_on_the_index(self) -> None:
        for record in self.fragment.evidence:
            with self.subTest(evidence=record.id):
                self.assertEqual(record.source.split(" ", 1)[0], framework.PRODUCER_CLASS)
                self.assertTrue(record.depends_on, "a row with no provenance is not evidence")
        sources = {record.atom.relation: record.source for record in self.fragment.evidence}
        self.assertIn(f"commit:{COMMIT}", sources[framework.EDGE_RELATION])
        self.assertIn(f"expires:{EXPIRES}", sources[framework.EDGE_RELATION])
        self.assertIn(REVIEWER, sources[framework.EDGE_RELATION])
        self.assertIn(framework.WITNESS_CALL_GRAPH_ASSUMED,
                      sources[framework.CALL_GRAPH_CLOSED_RELATION])

    def test_the_reviewed_rows_are_assumptions_the_registry_can_name(self) -> None:
        kinds = {record.atom.relation: record.kind for record in self.fragment.evidence}
        self.assertEqual(kinds[framework.EDGE_RELATION], "assumption")
        self.assertEqual(kinds[framework.CLOSED_RELATION], "assumption")
        self.assertEqual(kinds[framework.DESCRIBES_RELATION], "assumption")
        self.assertEqual(kinds[framework.CALL_GRAPH_CLOSED_RELATION], "fact",
                         "the coverage witness is computed, not signed")
        ids = framework.assumption_ids(self.fragment)
        self.assertEqual(len(ids), 3)
        for evidence_id, asm in ids.items():
            with self.subTest(evidence=evidence_id):
                self.assertTrue(asm.startswith(assumption_registry.ASSUMPTION_PREFIX))

    def test_the_assumption_id_does_not_move_when_the_export_is_rebuilt(self) -> None:
        """Contract A1: one signed row, one id, across exports of the same index."""
        again = framework.assumptions_bundle(_export(_ast()).bundle, self.ast, _assumptions())
        self.assertEqual(sorted(framework.assumption_ids(again).values()),
                         sorted(framework.assumption_ids(self.fragment).values()))


class WithoutTheDocumentTheRouteIsBlockedTests(unittest.TestCase):
    """Section 4."""

    def setUp(self) -> None:
        self.bundle, self.index = _bundle(_ast())
        self.relations = _closure_of(self.bundle)

    def test_the_registry_route_is_a_surface_whose_handler_is_the_dispatcher(self) -> None:
        self.assertEqual(_payload(self.relations, "static_route_handler"),
                         sorted([[REGISTRY_SURFACE, DISPATCHER],
                                 [RESOLVED_SURFACE, HANDLER]]))

    def test_the_registry_route_binds_nothing(self) -> None:
        self.assertEqual(_payload(self.relations, "static_capability_op"),
                         [[RESOLVED_SURFACE, "audit_logs", "create"],
                          [RESOLVED_SURFACE, "jobs", "read"]])

    def test_the_doubt_is_reported_and_names_where_it_enters(self) -> None:
        self.assertEqual(_payload(self.relations, "static_unresolved_call_site"),
                         [[DISPATCH_PATH, DISPATCH_LINE, "fn"]])
        self.assertEqual(_payload(self.relations, "static_unresolved_on"), [[DISPATCHER]])
        self.assertEqual(_payload(self.relations, "static_entity_blocked"),
                         [[REGISTRY_SURFACE, "audit_logs", DISPATCHER],
                          [REGISTRY_SURFACE, "jobs", DISPATCHER],
                          [REGISTRY_SURFACE, UNREACHED_ENTITY, DISPATCHER]])

    def test_the_residue_withholds_the_witness_for_the_whole_index(self) -> None:
        self.assertEqual(_payload(self.relations, closure.CLOSED_RELATION), [])
        self.assertEqual(_payload(self.relations, "static_entity_dead"), [],
                         "nothing is dead while one call site is unresolved")

    def test_not_one_assumed_relation_is_even_declared(self) -> None:
        self.assertEqual(set(self.relations) & {framework.EDGE_RELATION, "static_edge_assumed",
                                                framework.CALL_GRAPH_CLOSED_RELATION}, set())


class WithTheDocumentTheRouteBindsTests(unittest.TestCase):
    """Section 5."""

    def setUp(self) -> None:
        self.assumptions = _assumptions()
        self.bundle, self.index = _bundle(_ast(), self.assumptions)
        self.relations = _closure_of(self.bundle)

    def test_the_assumed_edge_is_lifted_and_carries_its_framework(self) -> None:
        self.assertEqual(_payload(self.relations, "static_edge_assumed"),
                         [[DISPATCHER, HANDLER, "net/http"]])
        self.assertNotIn([DISPATCHER, HANDLER], _payload(self.relations, "static_edge"),
                         "static_edge is never widened: it is what call_graph_closed completes")

    def test_the_registry_route_binds_under_the_assumption(self) -> None:
        self.assertEqual(_payload(self.relations, "static_capability_op_assumed"),
                         [[REGISTRY_SURFACE, "audit_logs", "create"],
                          [REGISTRY_SURFACE, "jobs", "read"],
                          [RESOLVED_SURFACE, "audit_logs", "create"],
                          [RESOLVED_SURFACE, "jobs", "read"]])
        self.assertEqual(_payload(self.relations, "static_entity_blocked_assumed"), [])

    def test_the_site_is_discharged_and_the_assumed_call_graph_closes(self) -> None:
        self.assertEqual(_payload(self.relations, "static_assumed_site_discharged"),
                         [[DISPATCH_PATH, DISPATCH_LINE]])
        self.assertEqual(_payload(self.relations, "static_assumed_site_undischarged"), [])
        self.assertEqual(_payload(self.relations, framework.CALL_GRAPH_CLOSED_RELATION),
                         [[closure.SCOPE_TOKEN_ALL]])

    def test_the_assumed_closure_settles_what_the_resolved_one_cannot(self) -> None:
        self.assertEqual(_payload(self.relations, "static_entity_dead_assumed"),
                         [[REGISTRY_SURFACE, UNREACHED_ENTITY],
                          [RESOLVED_SURFACE, UNREACHED_ENTITY]])
        self.assertEqual(_payload(self.relations, "static_entity_dead"), [])
        self.assertEqual(_payload(self.relations, closure.CLOSED_RELATION), [])

    def test_the_certificate_rechecks_and_names_the_assumptions_it_rests_on(self) -> None:
        row = [self.index, REGISTRY_SURFACE, "jobs", "read"]
        artifact = certificate.certify(self.bundle, self.relations,
                                       "static_capability_op_assumed", row)
        self.assertFalse(artifact.get("truncated"), artifact)
        result = certificate.recheck(self.bundle, artifact, self.relations)
        self.assertTrue(result.ok, result.problems)
        supported = _certified_relations(artifact)
        self.assertIn(framework.EDGE_RELATION, supported)
        self.assertIn(framework.DESCRIBES_RELATION, supported)
        ids = framework.assumption_ids(self.bundle)
        leaves = set(artifact.get("leaves") or ())
        carried = {ids[leaf] for leaf in leaves if leaf in ids}
        edge = [record for record in assumption_registry.assumption_records(self.bundle)
                if record.atom.relation == framework.EDGE_RELATION]
        self.assertEqual(len(edge), 1)
        self.assertIn(assumption_registry.assumption_id(edge[0]), carried,
                      "a row that rests on a framework assumption names it")

    def test_a_dead_certificate_names_both_assumed_witnesses(self) -> None:
        row = [self.index, REGISTRY_SURFACE, UNREACHED_ENTITY]
        artifact = certificate.certify(self.bundle, self.relations,
                                       "static_entity_dead_assumed", row)
        self.assertFalse(artifact.get("truncated"), artifact)
        self.assertTrue(certificate.recheck(self.bundle, artifact, self.relations).ok)
        supported = _certified_relations(artifact)
        self.assertIn(framework.CALL_GRAPH_CLOSED_RELATION, supported)
        self.assertIn(framework.CLOSED_RELATION, supported)

    def test_the_resolved_account_is_the_same_with_the_fragment_and_without(self) -> None:
        """The assumptions add relations; they do not move one."""
        plain = _closure_of(_bundle(_ast())[0])
        for relation in sorted(plain):
            with self.subTest(relation=relation):
                self.assertEqual(plain[relation], self.relations[relation])

    @unittest.skipUnless(_HAVE_SOUFFLE, "needs the souffle executable")
    def test_both_kernels_agree(self) -> None:
        from capcov.claims.differential import compare

        with tempfile.TemporaryDirectory() as tmp:
            result = compare(self.bundle, replay_root=str(Path(tmp) / "assumed"))
            self.assertTrue(result.matched, result.replay_path)


class WithdrawingTheRowPutsItBackTests(unittest.TestCase):
    """Section 6."""

    def setUp(self) -> None:
        self.bundle, self.index = _bundle(_ast(), _assumptions())
        self.before = _closure_of(self.bundle)
        edge = [record for record in assumption_registry.assumption_records(self.bundle)
                if record.atom.relation == framework.EDGE_RELATION]
        self.assumption = assumption_registry.assumption_id(edge[0])
        self.reduced = assumption_registry.withdraw(self.bundle, [edge[0].id])
        self.after = _closure_of(self.reduced)

    def test_the_withdrawal_can_be_asked_for_by_the_run_independent_id(self) -> None:
        resolved = assumption_registry.resolve(self.bundle, self.assumption)
        self.assertEqual([record.atom.relation for record in resolved],
                         [framework.EDGE_RELATION])

    def test_the_capability_it_carried_goes(self) -> None:
        self.assertEqual(_payload(self.after, "static_capability_op_assumed"),
                         [[RESOLVED_SURFACE, "audit_logs", "create"],
                          [RESOLVED_SURFACE, "jobs", "read"]])
        self.assertEqual(_payload(self.after, "static_edge_assumed"), [])

    def test_blocked_is_re_derived_and_names_the_dispatcher_again(self) -> None:
        self.assertEqual(_payload(self.after, "static_assumed_site_undischarged"),
                         [[DISPATCH_PATH, DISPATCH_LINE]])
        self.assertEqual(_payload(self.after, "static_entity_blocked_assumed"),
                         [[REGISTRY_SURFACE, "audit_logs", DISPATCHER],
                          [REGISTRY_SURFACE, "jobs", DISPATCHER],
                          [REGISTRY_SURFACE, UNREACHED_ENTITY, DISPATCHER]])

    def test_the_coverage_witness_goes_with_the_row_and_the_reviewers_closure_stays(self) -> None:
        """A witness saying every site is covered rests on the rows that cover them.

        The reviewer's own closure is a statement about the document, not about
        this row's truth, so it stands -- which is exactly what turns the
        uncovered site into ``undischarged`` rather than into silence.
        """
        self.assertEqual(_payload(self.after, framework.CALL_GRAPH_CLOSED_RELATION), [])
        self.assertEqual(_payload(self.after, framework.CLOSED_RELATION),
                         _payload(self.before, framework.CLOSED_RELATION))

    def test_nothing_becomes_dead_because_an_assumption_was_dropped(self) -> None:
        self.assertEqual(_payload(self.after, "static_entity_dead_assumed"), [])
        self.assertEqual(_payload(self.after, "static_entity_dead"), [])

    def test_the_resolved_account_never_moved(self) -> None:
        for relation in ("static_edge", "static_capability_op", "static_entity_blocked",
                         closure.CLOSED_RELATION):
            with self.subTest(relation=relation):
                self.assertEqual(_payload(self.after, relation),
                                 _payload(self.before, relation))


class ARowThatCannotBeAppliedIsEnumeratedTests(unittest.TestCase):
    """Section 7."""

    def test_a_co_located_unresolved_callee_stops_the_row_being_applied(self) -> None:
        ast = _ast(REGISTRY_RESIDUE + CO_LOCATED_RESIDUE)
        bundle, _ = _bundle(ast, _assumptions())
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, framework.UNAPPLIED_RELATION),
                         [[DISPATCH_PATH, DISPATCH_LINE, DISPATCHER, HANDLER,
                           framework.REASON_CO_LOCATED_RESIDUE]])
        self.assertEqual(_payload(relations, framework.EDGE_RELATION), [],
                         "applying it would discharge the reflective call beside it")
        self.assertEqual(_payload(relations, framework.CLOSED_RELATION), [])
        self.assertEqual(_payload(relations, "static_capability_op_assumed"),
                         [[RESOLVED_SURFACE, "audit_logs", "create"],
                          [RESOLVED_SURFACE, "jobs", "read"]])

    def test_a_row_for_a_site_with_no_residue_stands_for_nothing(self) -> None:
        ast = _ast()
        bundle, _ = _bundle(ast, _assumptions(_row(line=17)))
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, framework.UNAPPLIED_RELATION),
                         [[DISPATCH_PATH, 17, DISPATCHER, HANDLER,
                           framework.REASON_NO_UNRESOLVED_SITE]])
        self.assertEqual(_payload(relations, framework.CLOSED_RELATION), [])

    def test_a_row_for_a_document_out_of_scope_cannot_be_seen(self) -> None:
        ast = _ast()
        export = _export(ast).bundle
        fragment = framework.assumptions_bundle(
            export, ast, _assumptions(_row(path="internal/jobs/repo.go", line=15)))
        self.assertEqual(_rows(fragment, framework.UNAPPLIED_RELATION),
                         [["internal/jobs/repo.go", 15, DISPATCHER, HANDLER,
                           framework.REASON_NO_UNRESOLVED_SITE]])
        out_of_tree = framework.assumptions_bundle(
            export, ast, _assumptions(_row(path="api/other.go", line=3)))
        self.assertEqual(_rows(out_of_tree, framework.UNAPPLIED_RELATION),
                         [["api/other.go", 3, DISPATCHER, HANDLER,
                           framework.REASON_DOCUMENT_OUT_OF_SCOPE]])

    def test_an_open_document_licenses_no_negation(self) -> None:
        """``closed: false`` is a reviewer who has not said the set is complete."""
        bundle, _ = _bundle(_ast(), _assumptions(closed=False))
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, framework.EDGE_RELATION),
                         [[DISPATCHER, HANDLER, "net/http", "init-registry",
                           DISPATCH_PATH, DISPATCH_LINE]])
        self.assertEqual(_payload(relations, framework.CLOSED_RELATION), [])
        self.assertEqual(_payload(relations, framework.CALL_GRAPH_CLOSED_RELATION), [])
        self.assertEqual(_payload(relations, "static_entity_dead_assumed"), [])
        self.assertEqual(_payload(relations, "static_capability_op_assumed"),
                         [[REGISTRY_SURFACE, "audit_logs", "create"],
                          [REGISTRY_SURFACE, "jobs", "read"],
                          [RESOLVED_SURFACE, "audit_logs", "create"],
                          [RESOLVED_SURFACE, "jobs", "read"]],
                         "a positive reach needs no completeness")

    def test_a_closed_capability_map_omitting_an_assumed_endpoint_is_refused(self) -> None:
        ast = _ast()
        export = _export(ast).bundle
        model = reflexion.model_from_documents(
            {"schema_version": 1, "closed": True,
             "capabilities": {go_app.REGISTER: "bootstrap", DISPATCHER: "bootstrap",
                              HANDLER: "jobs_api", go_app.FETCH: "jobs_service",
                              go_app.REPO_GET: "jobs_store", go_app.REPO_WRITE: "jobs_store",
                              go_app.DB_FIRST: "gorm", go_app.DB_CREATE: "gorm"}})
        framework.assumptions_bundle(export, ast, _assumptions(), model=model)
        partial = reflexion.model_from_documents(
            {"schema_version": 1, "closed": True,
             "capabilities": {symbol: capability
                              for symbol, capability in model.capabilities
                              if symbol != HANDLER}})
        with self.assertRaises(framework.MapCoverageUnsatisfied) as ctx:
            framework.assumptions_bundle(export, ast, _assumptions(), model=partial)
        self.assertIn(HANDLER, str(ctx.exception))

    @unittest.skipUnless(_HAVE_SOUFFLE, "needs the souffle executable")
    def test_both_kernels_agree_with_the_witness_withheld(self) -> None:
        from capcov.claims.differential import compare

        bundle, _ = _bundle(_ast(REGISTRY_RESIDUE + CO_LOCATED_RESIDUE), _assumptions())
        with tempfile.TemporaryDirectory() as tmp:
            result = compare(bundle, replay_root=str(Path(tmp) / "unapplied"))
            self.assertTrue(result.matched, result.replay_path)


class TheFlagIsReachedFromTheCliTests(unittest.TestCase):
    """``claims static --assumptions``: the document is read before anything runs.

    A document that cannot be read is a statement about the command line, so it
    is answered where the command line is -- with exit 2, before the indexer is
    started and before the toolchain is even checked, which is why this runs
    without one.
    """

    def _run(self, path: str) -> tuple[int, dict]:
        from capcov.claims.cli import main as claims_main

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = claims_main(["claims", "static", "--static", "scip",
                                  "--target", str(go_app.GO_APP), "--language", "go",
                                  "--assumptions", path])
        return status, json.loads(output.getvalue())

    def test_an_absent_document_is_a_usage_refusal_naming_the_file(self) -> None:
        status, document = self._run("/nonexistent/assumptions.json")
        self.assertEqual(status, 2)
        self.assertIn("/nonexistent/assumptions.json", document["refusal"])

    def test_an_unenumerated_mechanism_is_refused_before_the_indexer_starts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "assumptions.json"
            path.write_text(json.dumps(_document(_row(mechanism="magic"))), encoding="utf-8")
            status, document = self._run(str(path))
        self.assertEqual(status, 2)
        self.assertIn("unknown net/http mechanism 'magic'", document["refusal"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
