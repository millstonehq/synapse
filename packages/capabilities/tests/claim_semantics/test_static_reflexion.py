"""The reflexion layer: a reviewer model over the static facts, and what it settles.

Five properties, one per section.

1. **The pack is a layer, not a fork.**  ``rules-static-reflexion-v1`` declares
   the reviewer's five primitives and the rules over them, and re-declares --
   byte for byte -- the ten relations it borrows from the frozen schema, from
   ``rules-static-v1`` and from ``rules-static-closure-v1``.  ``combine`` merges
   declarations by identity, so a borrowed declaration that drifted would be
   caught there; this asserts it directly.

2. **The reviewer owns the model, and says so.**  Every emitted row carries
   producer class ``reviewer`` and depends on the index's own evidence; the two
   closure witnesses appear only when the model documents declare closure; and a
   map that does not line up with the index is refused, naming the symbols,
   rather than silently lifting nothing for them -- in both directions: a mapped
   symbol the index does not declare, and (only when the map claims closure) a
   symbol the index's edges run through that the map does not carry.  The second
   is the one that can fabricate a ``static_absence`` about a real edge.

3. **The reflexion rows on go_app are the pilot's rows.**  Clean census:
   6 lifted edges, 5 convergences, one divergence (``bootstrap -> jobs_api``,
   the ``Register -> GetJob`` function-as-value reference), one absence
   (``jobs_api -> metrics``, declared by the reviewer and absent from the code)
   and one dead entity (``sessions``).  ``static_capability_op`` is untouched:
   the pack reuses it as the binding relation and re-derives nothing.

4. **One unresolved call site turns every verdict back into a question.**  With
   the closure test's own ``RESIDUE`` injected, ``static_absence`` and
   ``static_entity_dead`` go empty and are replaced by
   ``static_absence_unresolved`` and ``static_entity_blocked(..., via)``, which
   names ``Service#Fetch`` -- the symbol the unresolved site sits on.  The lifted
   edges, the convergences and the divergence do not move: the residue changes
   what is closed, not what is reached.  With residue at a site no symbol owns
   (``UNATTRIBUTED_RESIDUE``) there is no ``via``, and the weaker
   ``static_entity_unresolved`` is what is said: the doubt is reported either
   way, because an entity in no relation at all reads as "not applicable".

   The other closure gate is ``static_index_current``: with no
   ``source_tree_observed`` row the entity relations that rest on it are empty,
   so an unobserved index cannot call a live table dead.

5. **A model that does not claim closure closes nothing.**  Drop ``closed`` from
   the two documents and every negation over them stays unresolved: no
   ``static_low_edge_closed``, so no ``static_absence``; no
   ``capability_edge_closed``, so no ``static_divergence``.  The positive rows
   are unchanged, and the ``static_absence`` claim evaluates ``unresolved``
   rather than ``supported``.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from capcov.claims import (Bundle, Claim, Column, Constant, Context, Evidence,
                           RelationDecl, validate_bundle)
from capcov.claims.evaluator import evaluate
from capcov.claims.static import certificate, closure, reflexion, scip_facts
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
GO_APP = PACKAGE_ROOT / "tests" / "fixtures" / "go_app"
#: The reviewer model the pilot hand-authored, now a document the CLI can read.
PILOT = PACKAGE_ROOT / "experiments" / "claim-semantics" / "static" / "reflexion-pilot"
MAP_DOCUMENT = PILOT / "capability-map.json"
EDGES_DOCUMENT = PILOT / "capability-edges.json"

#: The third entity, declared but reached by nothing (the closure test's own).
UNREACHED_ENTITY = "sessions"
#: One unresolved call site, in a document of the slice (the closure test's own).
RESIDUE = [{"file": "internal/service/service.go", "line": 12, "callee": "h.dispatch",
            "kind": "unresolved", "reason": "untyped receiver"}]
#: The symbol that site sits on -- what ``static_entity_blocked``'s ``via`` names.
VIA = ("scip-go gomod github.com/example/jobsvc . "
       "`github.com/example/jobsvc/internal/service`/Service#Fetch().")
#: One unresolved call site the exporter cannot attribute to any symbol: the
#: models file declares types, so no definition encloses line 19 and
#: ``static_site_owner`` has no row for it.  This is the ordinary case for
#: scip-php (synthesized enclosing symbols) and for module-scope calls.
UNATTRIBUTED_RESIDUE = [{"file": "models/models.go", "line": 19, "callee": "x.dyn",
                         "kind": "unresolved", "reason": "untyped receiver"}]

LIFTED_EDGES = [["audit_store", "gorm"], ["bootstrap", "jobs_api"],
                ["jobs_api", "jobs_service"], ["jobs_service", "audit_store"],
                ["jobs_service", "jobs_store"], ["jobs_store", "gorm"]]
CONVERGENCE = [edge for edge in LIFTED_EDGES if edge != ["bootstrap", "jobs_api"]]
DIVERGENCE = [["bootstrap", "jobs_api"]]
ABSENCE = [["jobs_api", "metrics"]]
CAPABILITY_OPS = [[go_app.SURFACE, "audit_logs", "create"], [go_app.SURFACE, "jobs", "read"]]

ABSENCE_CLAIM = "claim-model-edge-absent"

_HAVE_SOUFFLE = shutil.which(os.environ.get("SOUFFLE") or "souffle") is not None
_HAVE_SCIP = bool(shutil.which("scip-go") and shutil.which("scip") and shutil.which("go"))


def _have_treesitter() -> bool:
    """The go call-site census needs the ``treesitter`` extra, and says so rather
    than returning an empty census -- so the live profile run needs it too."""
    try:
        from capcov.scip import blindspots

        blindspots._ts_language("go")
    except Exception:  # noqa: BLE001 - any failure means no census
        return False
    return True


_HAVE_TREESITTER = _have_treesitter()


def _model(*, closed: bool = True, edges_closed: bool = True) -> reflexion.CapabilityModel:
    """The pilot's documents, optionally with their closure declarations dropped."""
    map_document = dict(read_json(MAP_DOCUMENT), closed=closed)
    edges_document = dict(read_json(EDGES_DOCUMENT), closed=edges_closed)
    return reflexion.model_from_documents(map_document, edges_document)


def _partial_model(*, closed: bool) -> reflexion.CapabilityModel:
    """The pilot's model with one edge endpoint (``Service#Fetch``) dropped."""
    map_document = dict(read_json(MAP_DOCUMENT), closed=closed)
    map_document["capabilities"] = {symbol: capability
                                    for symbol, capability
                                    in map_document["capabilities"].items()
                                    if symbol != VIA}
    return reflexion.model_from_documents(
        map_document, dict(read_json(EDGES_DOCUMENT), closed=closed))


def _ast(residue=()) -> dict:
    """go_app's tree-sitter side plus the third entity and a chosen residue."""
    ast = go_app.ast_raw()
    ast["entities"].append({"name": UNREACHED_ENTITY, "symbol": "Session", "module": "",
                            "file": "models/models.go", "line": 19})
    ast["scip_residue"] = [dict(entry) for entry in residue]
    return ast


def _export(ast: dict):
    from capcov.scip import runner

    raw = go_app.golden_raw()
    result = scip_facts.export_bundle(
        go_app.normalized(raw), ast_raw=ast, source_root=go_app.GO_APP, language="go",
        index_digest=go_app.json_file_digest(raw), index_digest_kind=runner.INDEX_DIGEST_JSON)
    assert result.status == scip_facts.STATUS_COMPLETE, result.messages
    return result


#: ``_bundle``'s default: observe the tree the export actually indexed.
_OBSERVED = object()


def _bundle(ast: dict, model: reflexion.CapabilityModel | None = None, *,
            claims=(), tree_digest=_OBSERVED) -> tuple[Bundle, str]:
    """Export + closure fragment + reflexion fragment + the base pack's rules.

    ``tree_digest=None`` builds the same bundle with no ``source_tree_observed``
    row -- an index nobody has observed against a tree -- which is what
    ``static_index_current`` gates on.
    """
    exported = _export(ast)
    index = dict(exported.bundle.metadata)["index_digest"]
    observed = (dict(dict(exported.bundle.metadata)["tree"])["digest"]
                if tree_digest is _OBSERVED else tree_digest)
    bundle = reflexion.attach(
        exported.bundle, model if model is not None else _model(),
        closure.closure_bundle(exported.bundle, ast), pack_bundle(),
        tree_digest=observed, claims=list(claims))
    return bundle, index


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


class ReflexionPackIsALayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = reflexion.load_pack()

    def test_the_pack_validates_alone(self) -> None:
        self.assertEqual(validate_bundle(reflexion.pack_bundle()), ())

    def test_the_borrowed_declarations_are_their_owners_declarations(self) -> None:
        frozen = {item["name"]: item for item in read_json(FROZEN)["relations"]}
        base = load_pack()
        base_all = {item["name"]: item
                    for section in ("primitives", "supplementary_primitives", "derived")
                    for item in base[section]}
        closure_owned = {item["name"]: item for item in read_json(CLOSURE_PACK)["primitives"]}
        borrowed = {item["name"]: item for item in self.pack["borrowed_declarations"]}
        self.assertEqual(set(borrowed),
                         {"call_graph_closed", "static_capability_op", "static_edge",
                          "static_entity", "static_index_current", "static_reaches_eq",
                          "static_route_handler", "static_scope", "static_site_owner",
                          "static_unresolved_call_site"})
        self.assertEqual(self.pack["base_pack"], base["id"])
        self.assertEqual(self.pack["closure_pack"], closure.PACK_ID)
        for name, declaration in borrowed.items():
            with self.subTest(relation=name):
                source = frozen.get(name) or base_all.get(name) or closure_owned[name]
                self.assertEqual(declaration, source,
                                 f"{name} drifted from {PACK_PATH.name} / {FROZEN.name} / "
                                 f"{closure.PACK_NAME}")

    def test_the_reviewer_primitives_declare_their_producer_and_their_closures(self) -> None:
        primitives = {item["name"]: item for item in self.pack["primitives"]}
        self.assertEqual(set(primitives),
                         {reflexion.MAP_RELATION, reflexion.MAP_CLOSED_RELATION,
                          reflexion.EDGE_RELATION, reflexion.EDGE_CLOSED_RELATION,
                          reflexion.DESCRIBES_RELATION})
        for name, item in primitives.items():
            with self.subTest(relation=name):
                self.assertEqual(item["producer_classes"], [reflexion.PRODUCER_CLASS])
                self.assertTrue(item["primitive"])
        self.assertEqual(primitives[reflexion.MAP_CLOSED_RELATION]["completes"],
                         reflexion.MAP_RELATION)
        self.assertEqual(primitives[reflexion.EDGE_CLOSED_RELATION]["completes"],
                         reflexion.EDGE_RELATION)

    def test_the_compatibility_witness_binds_the_map_to_the_index(self) -> None:
        witness = next(item for item in self.pack["primitives"]
                       if item["name"] == reflexion.DESCRIBES_RELATION)
        self.assertEqual(witness["modality"], "compatibility")
        self.assertEqual(sorted(witness["compatibility_targets"]),
                         ["capability_map", "static_edge"])
        self.assertEqual(witness["compatibility_context_indices"], ["map", "index"])

    def test_the_lift_is_the_only_derivation_of_a_capability_edge_from_code(self) -> None:
        """``static_capability_op`` is reused, never re-derived: no rule heads it."""
        heads = {rule["head"]["relation"] for rule in self.pack["rules"]}
        self.assertNotIn("static_capability_op", heads)
        self.assertIn("static_low_edge", heads)

    def test_a_borrowed_declaration_that_widened_would_be_refused_by_combine(self) -> None:
        """The merge is by identity, and this is the negative control for it."""
        widened = RelationDecl(
            "static_edge",
            (Column("index", "digest", True), Column("src", "symbol"),
             Column("dst", "symbol"), Column("extra", "symbol")),
            modality="derived", binding="static", primitive=False, context_indices=("index",))
        with self.assertRaises(CombineError):
            combine(reflexion.pack_bundle(), Bundle((widened,)))


class TheReviewerOwnsTheModelTests(unittest.TestCase):
    def test_the_documents_become_rows_keyed_on_the_index(self) -> None:
        bundle, index = _bundle(_ast())
        self.assertEqual(len(_rows(bundle, reflexion.MAP_RELATION)), 8)
        self.assertEqual(_rows(bundle, reflexion.EDGE_RELATION),
                         sorted(LIFTED_EDGES[:0] + [list(edge) for edge in _model().edges]))
        self.assertEqual(_rows(bundle, reflexion.MAP_CLOSED_RELATION), [[]])
        self.assertEqual(_rows(bundle, reflexion.EDGE_CLOSED_RELATION), [[]])
        [describes] = [fact for fact in bundle.facts
                       if fact.relation == reflexion.DESCRIBES_RELATION]
        self.assertEqual([term.value for term in describes.terms],
                         [_model().digest, index])

    def test_a_model_that_declares_no_closure_emits_no_witness(self) -> None:
        bundle, _ = _bundle(_ast(), _model(closed=False, edges_closed=False))
        self.assertEqual(_rows(bundle, reflexion.MAP_CLOSED_RELATION), [])
        self.assertEqual(_rows(bundle, reflexion.EDGE_CLOSED_RELATION), [])
        self.assertEqual(len(_rows(bundle, reflexion.MAP_RELATION)), 8,
                         "the map itself is unaffected; only the claim of completeness is")

    def test_an_absent_edge_document_leaves_the_map_alone(self) -> None:
        model = reflexion.model_from_documents(read_json(MAP_DOCUMENT))
        self.assertEqual(model.edges, ())
        self.assertFalse(model.edges_closed)
        bundle, _ = _bundle(_ast(), model)
        self.assertEqual(_rows(bundle, reflexion.EDGE_RELATION), [])
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, "static_low_edge"), LIFTED_EDGES)
        self.assertEqual(_payload(relations, "static_convergence"), [])
        self.assertEqual(_payload(relations, "static_entity_dead"),
                         [[go_app.SURFACE, UNREACHED_ENTITY]],
                         "dead is a fact about the code, not about the reviewer's edges")

    def test_every_emitted_row_is_attributed_to_the_reviewer(self) -> None:
        bundle, _ = _bundle(_ast())
        emitted = [record for record in bundle.evidence
                   if record.atom.relation in (reflexion.MAP_RELATION,
                                               reflexion.MAP_CLOSED_RELATION,
                                               reflexion.EDGE_RELATION,
                                               reflexion.EDGE_CLOSED_RELATION,
                                               reflexion.DESCRIBES_RELATION)]
        self.assertEqual(len(emitted), 8 + 1 + 6 + 1 + 1)
        for record in emitted:
            with self.subTest(evidence=record.id):
                self.assertEqual(record.source.split(" ", 1)[0], reflexion.PRODUCER_CLASS)
                self.assertIn(_model().digest, record.source,
                              "a reviewer row names the document it came from")
                self.assertTrue(record.depends_on,
                                "a row with no provenance is not evidence")

    def test_a_scip_sourced_map_row_is_refused(self) -> None:
        """An indexer cannot manufacture architectural intent."""
        decls = reflexion.relation_decls()
        index = "a" * 64
        atom = reflexion._atom(decls[reflexion.MAP_RELATION], reflexion.MAP_RELATION,
                               [index, "Sym", "cap"])
        record = Evidence("static:forged", atom, Context.from_mapping({"index": index}),
                          "scip scip-go 0.2.7", ("scip:whatever",))
        issues = validate_bundle(Bundle(reflexion.pack_bundle().relations, facts=(atom,),
                                        evidence=(record,)))
        self.assertTrue(any(issue.code == "evidence-producer" for issue in issues),
                        [str(issue) for issue in issues])

    def test_a_map_naming_a_symbol_the_index_lacks_is_refused_by_name(self) -> None:
        exported = _export(_ast())
        stale = reflexion.model_from_documents(
            {"schema_version": 1, "closed": True,
             "capabilities": {"scip-go gomod example . `example`/Removed().": "ghost"}})
        with self.assertRaises(reflexion.ReflexionInputError) as caught:
            reflexion.model_bundle(exported.bundle, stale)
        self.assertIn("Removed()", str(caught.exception))

    def test_a_closed_map_that_omits_an_edge_endpoint_is_refused_by_name(self) -> None:
        """The other direction, and the one that can fabricate an absence.

        ``capability_map_closed`` is the reviewer's say-so, and it is what
        licenses ``static_absence``.  Drop one symbol the index's edges run
        through, keep ``closed: true``, and the edges through it lift nothing --
        so model edges the code does exhibit would be reported absent.  Coverage
        of the edge endpoints is the part of that say-so this module can check.
        """
        exported = _export(_ast())
        with self.assertRaises(reflexion.ReflexionInputError) as caught:
            reflexion.model_bundle(exported.bundle, _partial_model(closed=True))
        message = str(caught.exception)
        self.assertIn("Service#Fetch()", message)
        self.assertIn("closure", message)
        self.assertEqual(reflexion.unmapped_edge_symbols(exported.bundle,
                                                         _partial_model(closed=True)),
                         (VIA,))

    def test_the_same_partial_map_is_read_when_it_claims_nothing(self) -> None:
        """A map that does not claim closure may be as partial as it likes.

        It licenses no negation, so the rows it fails to lift cost nothing:
        ``static_absence`` is empty because there is no closed lift, not because
        the code was consulted.
        """
        bundle, _ = _bundle(_ast(), _partial_model(closed=False))
        self.assertEqual(len(_rows(bundle, reflexion.MAP_RELATION)), 7)
        self.assertEqual(_rows(bundle, reflexion.MAP_CLOSED_RELATION), [])
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, "static_low_edge"),
                         [["audit_store", "gorm"], ["bootstrap", "jobs_api"],
                          ["jobs_store", "gorm"]],
                         "the three edges through the unmapped symbol do not lift")
        self.assertEqual(_payload(relations, "static_low_edge_closed"), [])
        self.assertEqual(_payload(relations, "static_model_edge_unlifted"), [])
        self.assertEqual(_payload(relations, "static_absence"), [])

    def test_a_document_that_does_not_say_what_it_is_gets_no_benefit_of_the_doubt(self) -> None:
        for document, reason in (
                ({"capabilities": {"a": "b"}}, "no schema_version"),
                ({"schema_version": 1}, "no capabilities"),
                ({"schema_version": 1, "capabilities": {"a": "b"}, "extra": 1}, "unknown field"),
                ({"schema_version": 1, "capabilities": {"a": "b"}, "closed": "yes"},
                 "closed is not a boolean")):
            with self.subTest(reason=reason):
                with self.assertRaises(reflexion.ReflexionInputError):
                    reflexion.model_from_documents(document)

    def test_the_export_identity_does_not_move(self) -> None:
        """The fragment is beside the export, so no existing evidence id is renumbered."""
        ast = _ast(RESIDUE)
        exported = _export(ast)
        before = (dict(exported.bundle.metadata)["index_digest"],
                  scip_facts.bundle_digest(exported.bundle),
                  sorted(record.id for record in exported.bundle.evidence))
        reflexion.model_bundle(exported.bundle, _model())
        after = (dict(exported.bundle.metadata)["index_digest"],
                 scip_facts.bundle_digest(exported.bundle),
                 sorted(record.id for record in exported.bundle.evidence))
        self.assertEqual(before, after)

    def test_the_export_declares_none_of_the_reviewer_relations(self) -> None:
        names = {declaration.name for declaration in _export(_ast()).bundle.relations}
        for relation in (reflexion.MAP_RELATION, reflexion.EDGE_RELATION,
                         reflexion.DESCRIBES_RELATION):
            self.assertNotIn(relation, names)


class ReflexionOnGoAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle, self.index = _bundle(_ast())
        self.relations = _closure_of(self.bundle)

    def test_the_lift_drops_edges_inside_one_capability(self) -> None:
        self.assertEqual(_payload(self.relations, "static_low_edge"), LIFTED_EDGES)

    def test_convergence_divergence_and_absence(self) -> None:
        self.assertEqual(_payload(self.relations, "static_convergence"), CONVERGENCE)
        self.assertEqual(_payload(self.relations, "static_divergence"), DIVERGENCE)
        self.assertEqual(_payload(self.relations, "static_absence"), ABSENCE)
        self.assertEqual(_payload(self.relations, "static_absence_unresolved"), [])

    def test_the_unreached_entity_is_dead_and_nothing_is_blocked(self) -> None:
        self.assertEqual(_payload(self.relations, "static_entity_dead"),
                         [[go_app.SURFACE, UNREACHED_ENTITY]])
        self.assertEqual(_payload(self.relations, "static_entity_blocked"), [])
        self.assertEqual(_payload(self.relations, "static_unresolved_on"), [])

    def test_the_binding_relation_is_reused_not_re_derived(self) -> None:
        self.assertEqual(_payload(self.relations, "static_capability_op"), CAPABILITY_OPS)
        self.assertEqual(_payload(self.relations, "static_entity_bound"),
                         [row[:2] for row in CAPABILITY_OPS])

    def test_a_certificate_for_an_absence_rechecks(self) -> None:
        row = [self.index, *ABSENCE[0]]
        artifact = certificate.certify(self.bundle, self.relations, "static_absence", row)
        self.assertFalse(artifact.get("truncated"), artifact)
        result = certificate.recheck(self.bundle, artifact, self.relations)
        self.assertTrue(result.ok, result.problems)

    @unittest.skipUnless(_HAVE_SOUFFLE, "needs the souffle executable")
    def test_both_kernels_agree(self) -> None:
        from capcov.claims.differential import compare

        with tempfile.TemporaryDirectory() as tmp:
            result = compare(self.bundle, replay_root=str(Path(tmp) / "clean"))
            self.assertTrue(result.matched, result.replay_path)


class OneUnresolvedCallSiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle, self.index = _bundle(_ast(RESIDUE))
        self.relations = _closure_of(self.bundle)

    def test_what_is_reached_does_not_move(self) -> None:
        self.assertEqual(_payload(self.relations, "static_low_edge"), LIFTED_EDGES)
        self.assertEqual(_payload(self.relations, "static_convergence"), CONVERGENCE)
        self.assertEqual(_payload(self.relations, "static_divergence"), DIVERGENCE)
        self.assertEqual(_payload(self.relations, "static_capability_op"), CAPABILITY_OPS)

    def test_absence_becomes_a_question(self) -> None:
        self.assertEqual(_payload(self.relations, "static_absence"), [])
        self.assertEqual(_payload(self.relations, "static_absence_unresolved"), ABSENCE)

    def test_dead_becomes_blocked_and_the_residue_node_is_named(self) -> None:
        self.assertEqual(_payload(self.relations, "static_entity_dead"), [])
        self.assertEqual(_payload(self.relations, "static_unresolved_on"), [[VIA]])
        self.assertEqual(_payload(self.relations, "static_entity_blocked"),
                         [[go_app.SURFACE, UNREACHED_ENTITY, VIA]])

    def test_a_certificate_for_a_blocked_entity_rechecks(self) -> None:
        row = [self.index, go_app.SURFACE, UNREACHED_ENTITY, VIA]
        artifact = certificate.certify(self.bundle, self.relations, "static_entity_blocked", row)
        self.assertFalse(artifact.get("truncated"), artifact)
        result = certificate.recheck(self.bundle, artifact, self.relations)
        self.assertTrue(result.ok, result.problems)

    @unittest.skipUnless(_HAVE_SOUFFLE, "needs the souffle executable")
    def test_both_kernels_agree(self) -> None:
        from capcov.claims.differential import compare

        with tempfile.TemporaryDirectory() as tmp:
            result = compare(self.bundle, replay_root=str(Path(tmp) / "residue"))
            self.assertTrue(result.matched, result.replay_path)


class ResidueNoSymbolOwnsTests(unittest.TestCase):
    """The same doubt, at a site the exporter could not attribute to a symbol.

    ``scip_facts`` emits ``static_site_owner`` only for a site whose enclosing
    definition the index resolved, so on PHP -- where scip-php synthesizes
    enclosing symbols -- and at module scope it is empty by construction.  The
    witness is withheld either way; what must not happen is that the doubt then
    goes unreported, leaving a downstream judge to read silence as "nothing to
    say".
    """

    def setUp(self) -> None:
        self.bundle, self.index = _bundle(_ast(UNATTRIBUTED_RESIDUE))
        self.relations = _closure_of(self.bundle)

    def test_the_site_has_no_owner_and_the_call_graph_is_not_closed(self) -> None:
        self.assertEqual(len(_rows(self.bundle, "static_unresolved_call_site")), 1)
        self.assertEqual(_payload(self.relations, "static_unresolved_on"), [],
                         "no definition encloses models/models.go:19")
        self.assertEqual(_payload(self.relations, closure.CLOSED_RELATION), [])

    def test_absence_is_still_reported_as_unresolved(self) -> None:
        self.assertEqual(_payload(self.relations, "static_absence"), [])
        self.assertEqual(_payload(self.relations, "static_absence_unresolved"), ABSENCE,
                         "the doubt is the residue row, not the symbol under it")

    def test_the_entity_is_neither_dead_nor_silent(self) -> None:
        self.assertEqual(_payload(self.relations, "static_entity_dead"), [])
        self.assertEqual(_payload(self.relations, "static_entity_blocked"), [],
                         "there is no via to name")
        self.assertEqual(_payload(self.relations, "static_entity_unresolved"),
                         [[go_app.SURFACE, UNREACHED_ENTITY]])

    def test_what_is_reached_does_not_move(self) -> None:
        self.assertEqual(_payload(self.relations, "static_low_edge"), LIFTED_EDGES)
        self.assertEqual(_payload(self.relations, "static_convergence"), CONVERGENCE)
        self.assertEqual(_payload(self.relations, "static_capability_op"), CAPABILITY_OPS)

    def test_an_attributed_site_says_both(self) -> None:
        """The attributed case is the stronger one: blocked *and* unresolved."""
        relations = _closure_of(_bundle(_ast(RESIDUE))[0])
        self.assertEqual(_payload(relations, "static_entity_blocked"),
                         [[go_app.SURFACE, UNREACHED_ENTITY, VIA]])
        self.assertEqual(_payload(relations, "static_entity_unresolved"),
                         [[go_app.SURFACE, UNREACHED_ENTITY]])


class AModelWithoutClosureSettlesNothingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.open_model = _model(closed=False, edges_closed=False)

    def _claim(self, index: str) -> Claim:
        return Claim("static_absence",
                     (Constant(index, "digest"), Constant(ABSENCE[0][0], "symbol"),
                      Constant(ABSENCE[0][1], "symbol")),
                     Context.from_mapping({"index": index}), id=ABSENCE_CLAIM)

    def test_no_map_closure_means_no_closed_lift_and_no_absence(self) -> None:
        bundle, _ = _bundle(_ast(), self.open_model)
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, "static_low_edge"), LIFTED_EDGES)
        self.assertEqual(_payload(relations, "static_convergence"), CONVERGENCE)
        self.assertEqual(_payload(relations, "static_low_edge_closed"), [])
        self.assertEqual(_payload(relations, "static_model_edge_unlifted"), [])
        self.assertEqual(_payload(relations, "static_absence"), [])

    def test_an_unobserved_index_settles_nothing_about_an_entity(self) -> None:
        """``static_index_current`` is the other closure gate, and it holds.

        ``static_entity_bound_closed`` is "this index is current, so what it does
        not exhibit it does not have"; without a ``source_tree_observed`` row
        nobody has checked the index against the tree, and every entity relation
        that rests on it must stay empty -- otherwise a stale index reports the
        tables the route really reads and writes as dead code.  The lift is a
        statement about the index alone, so it does not move.
        """
        bundle, _ = _bundle(_ast(), tree_digest=None)
        relations = _closure_of(bundle)
        for relation in ("static_index_current", "static_entity_bound_closed",
                         "static_entity_unbound_in_index", "static_entity_dead",
                         "static_entity_blocked"):
            with self.subTest(relation=relation):
                self.assertEqual(_payload(relations, relation), [])
        self.assertEqual(_payload(relations, "static_low_edge"), LIFTED_EDGES)
        self.assertEqual(_payload(relations, "static_convergence"), CONVERGENCE)

    def test_no_edge_closure_means_no_divergence(self) -> None:
        bundle, _ = _bundle(_ast(), _model(closed=True, edges_closed=False))
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, "static_divergence"), [],
                         "a code edge the model omits is only divergence if the model is closed")
        self.assertEqual(_payload(relations, "static_absence"), ABSENCE)

    def test_the_absence_claim_is_unresolved_without_closure_and_supported_with_it(self) -> None:
        for model, expected in ((self.open_model, "unresolved"), (_model(), "supported")):
            with self.subTest(closed=model.closed):
                exported = _export(_ast())
                index = dict(exported.bundle.metadata)["index_digest"]
                bundle, _ = _bundle(_ast(), model, claims=[self._claim(index)])
                report = evaluate(bundle)
                self.assertEqual(report.status.value, "complete", report.message)
                [entry] = [e for e in report.claims if e.claim.id == ABSENCE_CLAIM]
                self.assertEqual(entry.result.semantic.value, expected)


class TheFlagIsOptionalTests(unittest.TestCase):
    """With no ``--capability-map`` the profile is what it was."""

    def _run(self, *extra: str):
        return subprocess.run(
            [sys.executable, "-m", "capcov", "experiment", "claims", "static",
             "--static", "scip", "--target", str(GO_APP), *extra],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"})

    def test_edges_without_a_map_is_refused_before_anything_is_indexed(self) -> None:
        proc = self._run("--capability-edges", str(EDGES_DOCUMENT))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--capability-edges needs --capability-map",
                      json.loads(proc.stdout)["refusal"])

    def test_an_unreadable_map_is_refused_before_anything_is_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "map.json"
            bad.write_text("{not json", encoding="utf-8")
            proc = self._run("--capability-map", str(bad))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot read", json.loads(proc.stdout)["refusal"])

    def test_the_static_subcommand_still_accepts_no_reflexion_flag_at_all(self) -> None:
        """No map: the run gets as far as the toolchain check, not to a reviewer row."""
        proc = self._run()
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        document = json.loads(proc.stdout)
        self.assertIn(document["operational_failure"],
                      ("scip-tools-unavailable", "census-unavailable"))
        self.assertNotIn("reflexion_pack", document)


@unittest.skipUnless(_HAVE_SCIP and _HAVE_TREESITTER,
                     "needs scip-go, the scip CLI, go and the treesitter extra")
class LiveReflexionProfileTests(unittest.TestCase):
    """The plan's acceptance: index go_app for real, hand it the model, evaluate."""

    def test_the_profile_lifts_a_real_index_through_the_reviewers_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "go_app"
            shutil.copytree(GO_APP, tree)
            ast_raw = Path(tmp) / "ast.json"
            ast_raw.write_text(json.dumps(_ast()), encoding="utf-8")
            out = Path(tmp) / "bundle.json"
            proc = subprocess.run(
                [sys.executable, "-m", "capcov", "experiment", "claims", "static",
                 "--static", "scip", "--target", str(tree), "--language", "go",
                 "--ast-raw", str(ast_raw), "--capability-map", str(MAP_DOCUMENT),
                 "--capability-edges", str(EDGES_DOCUMENT), "--out", str(out)],
                text=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(SRC)})
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            document = json.loads(proc.stdout)
            self.assertEqual(document["reflexion_pack"], reflexion.PACK_ID)
            self.assertEqual(document["model_digest"], _model().digest)
            self.assertEqual((document["capability_map"], document["capability_edge"]), (8, 6))
            self.assertTrue(document["capability_map_closed"])
            self.assertTrue(document["capability_edge_closed"])
            # go_app has no dynamic dispatch: the real census closes the scope, so
            # the real index settles both negatives.
            self.assertEqual(document[closure.CLOSED_RELATION], [closure.SCOPE_TOKEN_ALL])
            payload = json.loads(out.read_text(encoding="utf-8"))
        from capcov.claims import bundle_from_json

        # The written bundle carries the facts and this pack's rules; the base
        # pack is what derives static_edge, so a consumer merges it -- exactly
        # what the closure layer already asks of one.
        relations = _closure_of(combine(bundle_from_json(payload, validate=True), pack_bundle()))
        self.assertEqual(_payload(relations, "static_low_edge"), LIFTED_EDGES)
        self.assertEqual(_payload(relations, "static_convergence"), CONVERGENCE)
        self.assertEqual(_payload(relations, "static_divergence"), DIVERGENCE)
        self.assertEqual(_payload(relations, "static_absence"), ABSENCE)
        self.assertEqual(_payload(relations, "static_capability_op"), CAPABILITY_OPS)
        self.assertEqual(_payload(relations, "static_entity_dead"),
                         [[go_app.SURFACE, UNREACHED_ENTITY]])
        self.assertEqual(_payload(relations, "static_entity_blocked"), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
