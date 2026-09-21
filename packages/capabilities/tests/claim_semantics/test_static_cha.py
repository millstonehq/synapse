"""Class-hierarchy expansion: a second account of the call graph, never a wider one.

Six properties, one per section.

1. **The measurement, not an assumption.**  ``scip-go`` 0.2.7 emits SCIP
   ``is_implementation`` relationships for Go interfaces -- for the method
   (``SQL#Fetch().`` -> ``Repo#Fetch.``) and for the type (``SQL#`` -> ``Repo#``)
   -- and the committed golden ``scip_go_iface_app_index.json`` is what a fresh
   index of ``tests/fixtures/go_iface_app`` says.  The same index shows why the
   expansion needs a caller-side primitive of its own: scip-go types an interface
   member ``MethodSpecification``, which ``scip.map`` classifies as a *term*, so
   the dispatch site never reaches ``scip_may_reference`` and ``static_edge`` has
   no edge into the interface at all.  The live test re-indexes and compares; it
   skips, by name, where the toolchain is absent.

2. **The pack is a layer, not a fork.**  ``rules-static-cha-v1`` owns four
   ``scip`` primitives and re-declares -- byte for byte -- the sixteen relations
   it borrows from the frozen schema, ``rules-static-v1``,
   ``rules-static-closure-v1`` and ``rules-static-reflexion-v1``.  No rule of it
   heads ``static_edge``, ``static_reaches`` or ``call_graph_closed``: the
   relation ``call_graph_closed`` completes is exactly the relation this pack
   does not touch.

3. **What the fragment emits.**  One dispatch site on the fixture, the expansion
   witness, and the CHA call-graph witness -- every row ``scip``-classed and
   depending on the index's own evidence.

4. **What the expansion settles that the resolved graph cannot.**  The fixture's
   handler reaches its store only through the interface.  ``static_capability_op``
   is empty and ``static_reaches`` has no row from the handler; under CHA the
   same bundle derives ``static_capability_op_cha`` for ``(things, read)``,
   discharges the one residue row (the dispatch site itself) and settles
   ``static_entity_dead_cha`` for the entity nothing reaches even under CHA.
   Meanwhile every relation of the resolved account is byte-identical with the
   fragment merged and without it: the expansion widens nothing.

5. **Every witness can be withheld, and each withholding says something
   different.**  A residue row that is *not* a dispatch site is never discharged:
   ``call_graph_closed_cha`` goes, ``static_entity_dead_cha`` goes with it, and
   ``static_entity_blocked_cha`` names the symbol the undischarged site sits on.
   An index that declares an interface member and implements it nowhere -- a Go
   interface whose implementations live in another module -- still *sees* the
   site (membership is read from the symbol's kind, not from the hierarchy it
   lacks), reports it as ``static_cha_unexpanded_site`` with its reason and
   withholds ``static_edge_cha_closed``.  A slice that drops the document the
   interface lives in sees neither the member nor its implementations, so it
   claims nothing at all: the witness is licensed only over the whole index.

6. **An unmeasured indexer is refused.**  Not "emits none": this module cannot
   tell that from "nobody looked", and only one of those is a fact.

The two live classes index the fixture with the real toolchain -- one checks the
committed golden against a fresh index, the other runs ``--dispatch cha`` end to
end -- and both skip, by name, where the toolchain (or the ``treesitter`` extra
the census needs) is absent.
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

from capcov.claims import Bundle, Column, RelationDecl, validate_bundle
from capcov.claims.evaluator import evaluate
from capcov.claims.static import certificate, cha, closure, reflexion, scip_facts
from capcov.claims.static.combine import CombineError, combine
from capcov.scip import runner

try:
    from .static_rules.adapter import PACK_PATH, load_pack, pack_bundle, read_json
except ImportError:  # unittest discover -s imports this directory as top-level
    from static_rules.adapter import PACK_PATH, load_pack, pack_bundle, read_json

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SRC = PACKAGE_ROOT / "src"
FIXTURES = PACKAGE_ROOT / "tests" / "fixtures"
FROZEN = SRC / "capcov" / "claims" / "static" / "schema_static_v1.json"
CLOSURE_PACK = SRC / "capcov" / "claims" / "static" / closure.PACK_NAME
REFLEXION_PACK = SRC / "capcov" / "claims" / "static" / reflexion.PACK_NAME
IFACE_APP = FIXTURES / "go_iface_app"
GOLDEN = FIXTURES / "scip_go_iface_app_index.json"

MODULE = "github.com/example/ifacesvc"
_PREFIX = f"scip-go gomod {MODULE} . "
GET_THING = _PREFIX + f"`{MODULE}/api`/GetThing()."
REGISTER = _PREFIX + f"`{MODULE}/api`/Register()."
REPO_FETCH = _PREFIX + f"`{MODULE}/store`/Repo#Fetch."          # the interface member
REPO_TYPE = _PREFIX + f"`{MODULE}/store`/Repo#"
SQL_FETCH = _PREFIX + f"`{MODULE}/store`/SQL#Fetch()."
SQL_TYPE = _PREFIX + f"`{MODULE}/store`/SQL#"
MEMORY_FETCH = _PREFIX + f"`{MODULE}/store`/Memory#Fetch()."
MEMORY_TYPE = _PREFIX + f"`{MODULE}/store`/Memory#"
QUERY = _PREFIX + f"`{MODULE}/store`/query()."

SURFACE = "http:GET /things/{id}"
ENTITY = "things"
#: A second entity, declared and reached by nothing -- not even under CHA.
UNREACHED_ENTITY = "sessions"

# 1-based lines, read off the fixture source.
HANDLER_LINE = 6            # api/api.go: func GetThing(...)
DISPATCH_LINE = 7           # api/api.go: return repo.Fetch(id)
ROUTE_LINE = 12             # api/api.go: handle("GET /things/{id}", GetThing)
ENTITY_LINE = 4             # store/store.go: type Thing struct
OP_LINE = 18                # store/store.go: return query(id) inside SQL.Fetch

#: The census of this fixture: the call through the interface is the one call
#: site the SCIP fold does not resolve to a callable, so it is in the residue.
DISPATCH_RESIDUE = [{"file": "api/api.go", "line": DISPATCH_LINE, "callee": "repo.Fetch",
                     "kind": "unresolved", "reason": "interface dispatch"}]
#: A residue row no expansion can discharge: it is not a dispatch site at all.
REFLECTIVE_RESIDUE = [{"file": "store/store.go", "line": OP_LINE, "callee": "m.byName",
                       "kind": "unresolved", "reason": "dynamic method"}]

_HAVE_SOUFFLE = shutil.which(os.environ.get("SOUFFLE") or "souffle") is not None
_HAVE_SCIP = bool(shutil.which("scip-go") and shutil.which("scip") and shutil.which("go"))


def _ast(residue=DISPATCH_RESIDUE) -> dict:
    """The tree-sitter side of ``go_iface_app``, written from the fixture source.

    Five short Go declarations reviewed by hand, as ``static_rules/go_app.py``
    does for its own fixture: the route and its handler, the two entities, the
    one op site (inside ``SQL.Fetch``) and the census.
    """
    return {
        "surfaces": [{"id": SURFACE, "kind": "http", "method": "GET", "path": "/things/{id}",
                      "handler": f"{MODULE}/api:GetThing", "handler_symbol": "GetThing",
                      "file": "api/api.go", "line": ROUTE_LINE, "mounted": True}],
        "_node_locations": {f"{MODULE}/api:GetThing": ["api/api.go", HANDLER_LINE]},
        "excluded_surfaces": {"count": 0, "surfaces": []},
        "entities": [
            {"name": ENTITY, "symbol": "Thing", "module": "", "file": "store/store.go",
             "line": ENTITY_LINE},
            {"name": UNREACHED_ENTITY, "symbol": "Session", "module": "",
             "file": "store/store.go", "line": 22},
        ],
        "op_sites": [{"file": "store/store.go", "line": OP_LINE, "entity": ENTITY,
                      "crud": "read"}],
        "blind_spots": [],
        "scip_residue": [dict(entry) for entry in residue],
        "unresolved": [],
    }


def _golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def _normalized(raw: dict | None = None) -> dict:
    return runner.normalize_scip_json(raw if raw is not None else _golden(), retain=True)


def _export(ast: dict, scope=None):
    raw = _golden()
    kwargs = {"scope": scope} if scope is not None else {}
    result = scip_facts.export_bundle(
        _normalized(raw), ast_raw=ast, source_root=IFACE_APP, language="go",
        index_digest=runner.json_index_digest(raw),
        index_digest_kind=runner.INDEX_DIGEST_JSON, **kwargs)
    assert result.status == scip_facts.STATUS_COMPLETE, result.messages
    return result


def _bundle(ast: dict, *, dispatch: bool = True, scope=None) -> tuple[Bundle, str]:
    """Export + closure fragment + (optionally) the CHA fragment + the base pack."""
    exported = _export(ast, scope=scope)
    index = dict(exported.bundle.metadata)["index_digest"]
    tree = dict(dict(exported.bundle.metadata)["tree"])["digest"]
    fragments = [closure.closure_bundle(exported.bundle, ast), pack_bundle()]
    if dispatch:
        bundle = cha.attach(exported.bundle, _normalized(), ast, *fragments, tree_digest=tree)
    else:
        from capcov.claims.static import pilot

        decls = {decl.name: decl for decl in exported.bundle.relations}
        atom, record = pilot.source_tree_observation(decls, tree,
                                                     source=cha.TREE_OBSERVATION_SOURCE)
        observed = Bundle(exported.bundle.relations, facts=(atom,), evidence=(record,))
        bundle = combine(exported.bundle, observed, *fragments, validate=True)
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


class TheGoldenIsWhatTheIndexerSaysTests(unittest.TestCase):
    """Section 1, on the committed index -- the live half is below."""

    def setUp(self) -> None:
        self.export = _export(_ast()).bundle

    def test_scip_go_emits_implementation_relationships(self) -> None:
        self.assertEqual(_rows(self.export, cha.RELATIONSHIP_RELATION), sorted([
            [MEMORY_TYPE, REPO_TYPE, cha.IMPLEMENTATION],
            [MEMORY_FETCH, REPO_FETCH, cha.IMPLEMENTATION],
            [SQL_TYPE, REPO_TYPE, cha.IMPLEMENTATION],
            [SQL_FETCH, REPO_FETCH, cha.IMPLEMENTATION],
        ]))

    def test_the_interface_member_is_not_a_callable_reference(self) -> None:
        """Why the caller side of a dispatch needs a primitive of its own."""
        callees = {row[1] for row in _rows(self.export, "scip_may_reference")}
        self.assertNotIn(REPO_FETCH, callees)
        self.assertEqual(sorted(row[:2] for row in _rows(self.export, "scip_may_reference")),
                         [[REGISTER, GET_THING],
                          [REGISTER, _PREFIX + f"`{MODULE}/api`/handle()."],
                          [SQL_FETCH, QUERY]])

    def test_the_hierarchy_read_off_the_export_is_the_method_level_one(self) -> None:
        self.assertEqual(cha.implementations(self.export)[REPO_FETCH],
                         (MEMORY_FETCH, SQL_FETCH))

    def test_an_interface_member_is_known_by_its_declared_kind(self) -> None:
        """Membership comes from the kind, so an unimplemented member is still seen."""
        self.assertEqual(cha.interface_members(self.export), frozenset({REPO_FETCH}))


class TheChaPackIsALayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = cha.load_pack()

    def test_the_pack_validates_alone(self) -> None:
        self.assertEqual(validate_bundle(cha.pack_bundle()), ())

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
            "capability_map_closed", "capability_map_describes_index", "scip_relationship",
            "static_edge", "static_entity", "static_index_current", "static_op_owner",
            "static_reaches", "static_root", "static_route_handler", "static_scope",
            "static_site_owner", "static_unresolved_call_site"})
        self.assertEqual(self.pack["base_pack"], base["id"])
        self.assertEqual(self.pack["closure_pack"], closure.PACK_ID)
        self.assertEqual(self.pack["reflexion_pack"], reflexion.PACK_ID)
        for name, declaration in borrowed.items():
            with self.subTest(relation=name):
                source = frozen.get(name) or owned[name]
                self.assertEqual(declaration, source,
                                 f"{name} drifted from {PACK_PATH.name} / {FROZEN.name} / "
                                 f"{closure.PACK_NAME} / {reflexion.PACK_NAME}")

    def test_the_primitives_declare_the_indexers_producer_class_and_what_they_close(self) -> None:
        primitives = {item["name"]: item for item in self.pack["primitives"]}
        self.assertEqual(set(primitives), {cha.DISPATCH_RELATION, cha.UNEXPANDED_RELATION,
                                           cha.EDGE_CLOSED_RELATION, cha.CLOSED_RELATION})
        for name, item in primitives.items():
            with self.subTest(relation=name):
                self.assertEqual(item["producer_classes"], [cha.PRODUCER_CLASS])
                self.assertTrue(item["primitive"])
        self.assertEqual(primitives[cha.EDGE_CLOSED_RELATION]["completes"], "static_edge_cha")
        self.assertEqual(primitives[cha.CLOSED_RELATION]["completes"], "static_reaches_cha")

    def test_no_rule_touches_the_relation_call_graph_closed_completes(self) -> None:
        """``static_edge`` is the ``completes`` target of ``call_graph_closed``."""
        heads = {rule["head"]["relation"] for rule in self.pack["rules"]}
        self.assertEqual(heads & {"static_edge", "static_reaches", "static_reaches_eq",
                                  "call_graph_closed", "static_capability_op"}, set())
        self.assertIn("static_edge_cha", heads)
        self.assertIn("static_reaches_cha", heads)

    def test_a_borrowed_declaration_that_widened_would_be_refused_by_combine(self) -> None:
        widened = RelationDecl(
            "static_edge",
            (Column("index", "digest", True), Column("src", "symbol"),
             Column("dst", "symbol"), Column("via_interface", "symbol")),
            modality="derived", binding="static", primitive=False, context_indices=("index",))
        with self.assertRaises(CombineError):
            combine(cha.pack_bundle(), Bundle((widened,)))


class WhatTheFragmentEmitsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ast = _ast()
        self.export = _export(self.ast).bundle
        self.fragment = cha.cha_bundle(self.export, _normalized(), self.ast)

    def test_the_dispatch_site_is_the_call_through_the_interface(self) -> None:
        self.assertEqual(_rows(self.fragment, cha.DISPATCH_RELATION),
                         [[GET_THING, REPO_FETCH, "api/api.go", DISPATCH_LINE]])
        self.assertEqual(_rows(self.fragment, cha.UNEXPANDED_RELATION), [])

    def test_both_witnesses_are_emitted_on_a_fully_expanded_index(self) -> None:
        self.assertEqual(_rows(self.fragment, cha.EDGE_CLOSED_RELATION), [[]])
        self.assertEqual(_rows(self.fragment, cha.CLOSED_RELATION), [[closure.SCOPE_TOKEN_ALL]])

    def test_every_row_is_the_indexers_and_depends_on_the_index(self) -> None:
        for record in self.fragment.evidence:
            with self.subTest(evidence=record.id):
                self.assertEqual(record.source.split(" ", 1)[0], cha.PRODUCER_CLASS)
                self.assertTrue(record.depends_on, "a row with no provenance is not evidence")
        sources = {record.atom.relation: record.source for record in self.fragment.evidence}
        self.assertIn("scip-go 0.2.7", sources[cha.DISPATCH_RELATION])
        self.assertIn(cha.WITNESS_EDGE_CHA, sources[cha.EDGE_CLOSED_RELATION])
        self.assertIn(cha.WITNESS_CALL_GRAPH_CHA, sources[cha.CLOSED_RELATION])

    def test_the_fragment_carries_no_row_of_the_relations_it_borrows(self) -> None:
        emitted = {fact.relation for fact in self.fragment.facts}
        self.assertEqual(emitted - {"source_tree_observed"},
                         {cha.DISPATCH_RELATION, cha.EDGE_CLOSED_RELATION, cha.CLOSED_RELATION})


class WhatTheExpansionSettlesTests(unittest.TestCase):
    """Section 4: the handler reaches its store only through the interface."""

    def setUp(self) -> None:
        self.bundle, self.index = _bundle(_ast())
        self.relations = _closure_of(self.bundle)

    def test_the_resolved_graph_reaches_nothing_from_the_handler(self) -> None:
        self.assertEqual(_payload(self.relations, "static_reaches"), [])
        self.assertEqual(_payload(self.relations, "static_capability_op"), [])
        self.assertEqual(_payload(self.relations, "call_graph_closed"), [],
                         "the dispatch site is in the residue, so nothing is closed")

    def test_the_expansion_is_a_relation_of_its_own(self) -> None:
        self.assertEqual(_payload(self.relations, "static_edge_cha"),
                         sorted([[GET_THING, MEMORY_FETCH, REPO_FETCH],
                                 [GET_THING, SQL_FETCH, REPO_FETCH]]))
        self.assertNotIn([GET_THING, SQL_FETCH], _payload(self.relations, "static_edge"))

    def test_reachability_under_cha_runs_through_the_implementation(self) -> None:
        self.assertEqual(_payload(self.relations, "static_reaches_cha"),
                         sorted([[GET_THING, MEMORY_FETCH], [GET_THING, SQL_FETCH],
                                 [GET_THING, QUERY]]))

    def test_the_capability_is_claimable_only_under_cha(self) -> None:
        self.assertEqual(_payload(self.relations, "static_capability_op_cha"),
                         [[SURFACE, ENTITY, "read"]])

    def test_the_dispatch_residue_is_discharged_by_the_expansion_of_that_site(self) -> None:
        self.assertEqual(_payload(self.relations, "static_cha_site_discharged"),
                         [["api/api.go", DISPATCH_LINE]])
        self.assertEqual(_payload(self.relations, "static_cha_site_undischarged"), [])
        self.assertEqual(_payload(self.relations, cha.CLOSED_RELATION),
                         [[closure.SCOPE_TOKEN_ALL]])

    def test_an_entity_no_expansion_reaches_is_dead_under_cha(self) -> None:
        self.assertEqual(_payload(self.relations, "static_entity_dead_cha"),
                         [[SURFACE, UNREACHED_ENTITY]])
        self.assertEqual(_payload(self.relations, "static_entity_blocked_cha"), [])

    def test_a_certificate_for_a_cha_capability_rechecks(self) -> None:
        row = [self.index, SURFACE, ENTITY, "read"]
        artifact = certificate.certify(self.bundle, self.relations,
                                       "static_capability_op_cha", row)
        self.assertFalse(artifact.get("truncated"), artifact)
        result = certificate.recheck(self.bundle, artifact, self.relations)
        self.assertTrue(result.ok, result.problems)

    def test_the_resolved_account_is_the_same_with_the_fragment_and_without(self) -> None:
        """The expansion widens nothing: it adds relations, it does not move one."""
        plain = _closure_of(_bundle(_ast(), dispatch=False)[0])
        for relation in sorted(plain):
            with self.subTest(relation=relation):
                self.assertEqual(plain[relation], self.relations[relation])
        self.assertEqual(set(plain) & {"static_edge_cha", "static_reaches_cha",
                                       cha.CLOSED_RELATION}, set(),
                         "without the fragment not one CHA relation is even declared")

    @unittest.skipUnless(_HAVE_SOUFFLE, "needs the souffle executable")
    def test_both_kernels_agree(self) -> None:
        from capcov.claims.differential import compare

        with tempfile.TemporaryDirectory() as tmp:
            result = compare(self.bundle, replay_root=str(Path(tmp) / "cha"))
            self.assertTrue(result.matched, result.replay_path)


class AWitnessCanAlwaysBeWithheldTests(unittest.TestCase):
    def test_a_residue_row_that_is_not_a_dispatch_site_is_never_discharged(self) -> None:
        bundle, _ = _bundle(_ast(DISPATCH_RESIDUE + REFLECTIVE_RESIDUE))
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, "static_cha_site_discharged"),
                         [["api/api.go", DISPATCH_LINE]])
        self.assertEqual(_payload(relations, "static_cha_site_undischarged"),
                         [["store/store.go", OP_LINE]])
        self.assertEqual(_payload(relations, cha.CLOSED_RELATION), [])
        self.assertEqual(_payload(relations, "static_entity_dead_cha"), [])
        self.assertEqual(_payload(relations, "static_unresolved_on_cha"), [[SQL_FETCH]])
        self.assertEqual(_payload(relations, "static_entity_blocked_cha"),
                         [[SURFACE, UNREACHED_ENTITY, SQL_FETCH]],
                         "the doubt is reported, and it names where it enters")
        self.assertEqual(_payload(relations, "static_entity_unresolved_cha"),
                         [[SURFACE, UNREACHED_ENTITY]])
        self.assertEqual(_payload(relations, "static_capability_op_cha"),
                         [[SURFACE, ENTITY, "read"]],
                         "what is reached does not move; only what is closed does")

    def test_a_slice_cannot_see_what_it_is_missing_and_claims_nothing(self) -> None:
        """The interface lives in the document the slice drops: no rows, no witness."""
        bundle, _ = _bundle(_ast(), scope=scip_facts.Scope.document_set(["api/api.go"]))
        relations = _closure_of(bundle)
        self.assertEqual(_payload(relations, cha.DISPATCH_RELATION), [])
        self.assertEqual(_payload(relations, cha.UNEXPANDED_RELATION), [])
        self.assertEqual(_payload(relations, cha.EDGE_CLOSED_RELATION), [])
        self.assertEqual(_payload(relations, cha.CLOSED_RELATION), [],
                         "the dispatch residue row is still there and still undischarged")
        self.assertEqual(_payload(relations, "static_edge_cha"), [])
        self.assertEqual(_payload(relations, "static_cha_site_discharged_closed"), [],
                         "with an open expansion nothing about a site is settled")
        self.assertEqual(_payload(relations, "static_entity_dead_cha"), [])

    def test_a_whole_index_scope_is_what_the_expansion_can_close_over(self) -> None:
        """The same fixture, sliced to every document it has, still closes nothing."""
        exported = _export(_ast(), scope=scip_facts.Scope.document_set(
            ["api/api.go", "store/store.go"]))
        fragment = cha.cha_bundle(exported.bundle, _normalized(), _ast())
        self.assertEqual(_rows(fragment, cha.DISPATCH_RELATION),
                         [[GET_THING, REPO_FETCH, "api/api.go", DISPATCH_LINE]],
                         "the sites and the expansion are unaffected by the scope KIND")
        self.assertEqual(_rows(fragment, cha.EDGE_CLOSED_RELATION), [],
                         "only a scope of the whole index licenses the witness")

    def test_an_interface_implemented_outside_the_index_is_enumerated(self) -> None:
        """The export declares the member; nothing in this index implements it.

        What a Go interface whose implementations live in another module looks
        like, built by dropping this index's relationship rows -- the site is
        still seen (the member's kind says what it is), reported with its reason,
        and the expansion refuses to call itself complete.
        """
        ast = _ast()
        exported = _export(ast).bundle
        without = Bundle(
            exported.relations,
            facts=tuple(f for f in exported.facts if f.relation != cha.RELATIONSHIP_RELATION),
            rules=exported.rules,
            evidence=tuple(r for r in exported.evidence
                           if r.atom.relation != cha.RELATIONSHIP_RELATION),
            metadata=exported.metadata)
        fragment = cha.cha_bundle(without, _normalized(), ast)
        self.assertEqual(_rows(fragment, cha.UNEXPANDED_RELATION),
                         [["api/api.go", DISPATCH_LINE, REPO_FETCH,
                           cha.REASON_NO_IMPLEMENTATION]])
        self.assertEqual(_rows(fragment, cha.DISPATCH_RELATION), [])
        self.assertEqual(_rows(fragment, cha.EDGE_CLOSED_RELATION), [])
        self.assertEqual(_rows(fragment, cha.CLOSED_RELATION), [])

    def test_the_reasons_a_site_cannot_be_expanded_are_distinguished(self) -> None:
        hierarchy = {REPO_FETCH: (SQL_FETCH, MEMORY_FETCH)}
        defined = frozenset({SQL_FETCH, MEMORY_FETCH})
        self.assertIsNone(cha.unexpanded_reason(GET_THING, REPO_FETCH, hierarchy, defined))
        self.assertEqual(cha.unexpanded_reason(None, REPO_FETCH, hierarchy, defined),
                         cha.REASON_UNATTRIBUTED)
        self.assertEqual(cha.unexpanded_reason(GET_THING, REPO_FETCH, {}, defined),
                         cha.REASON_NO_IMPLEMENTATION)
        self.assertEqual(cha.unexpanded_reason(GET_THING, REPO_FETCH, hierarchy,
                                               frozenset({SQL_FETCH})),
                         cha.REASON_OUT_OF_SCOPE)

    def test_a_census_that_was_not_taken_closes_nothing(self) -> None:
        ast = _ast()
        ast.pop("blind_spots")
        exported = _export(ast)
        self.assertFalse(dict(exported.bundle.metadata)["census_available"])
        fragment = cha.cha_bundle(exported.bundle, _normalized(), ast)
        self.assertEqual(_rows(fragment, cha.EDGE_CLOSED_RELATION), [[]],
                         "the expansion is still complete: that is a fact about the index")
        self.assertEqual(_rows(fragment, cha.CLOSED_RELATION), [],
                         "but a call graph nobody censused is not closed by it")


class AnUnmeasuredIndexerIsRefusedTests(unittest.TestCase):
    def test_the_measured_indexer_passes(self) -> None:
        self.assertIsNone(cha.require_measured_indexer(
            {"indexer": "scip-go", "indexer_version": "0.2.7"}))

    def test_an_unmeasured_indexer_is_named_and_refused(self) -> None:
        with self.assertRaises(cha.DispatchUnsupported) as caught:
            cha.require_measured_indexer({"indexer": "scip-php", "indexer_version": "dev-main"})
        message = str(caught.exception)
        self.assertTrue(message.startswith("unsupported: "), message)
        self.assertIn("scip-php dev-main", message)
        self.assertIn("scip-go 0.2.7", message)
        self.assertNotIn("emits no", message,
                         "'never measured' is not 'emits none'; only one of them is a fact")


class TheFlagIsOptionalTests(unittest.TestCase):
    """With no ``--dispatch cha`` the profile is what it was."""

    def _run(self, *extra: str):
        return subprocess.run(
            [sys.executable, "-m", "capcov", "experiment", "claims", "static",
             "--static", "scip", "--target", str(IFACE_APP), *extra],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"})

    def test_the_default_run_says_nothing_about_dispatch(self) -> None:
        proc = self._run()
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        document = json.loads(proc.stdout)
        self.assertIn(document["operational_failure"],
                      ("scip-tools-unavailable", "census-unavailable"))
        for key in ("dispatch", "cha_pack", cha.DISPATCH_RELATION, cha.CLOSED_RELATION):
            self.assertNotIn(key, document)

    def test_an_unknown_dispatch_mode_is_refused_by_the_parser(self) -> None:
        proc = self._run("--dispatch", "rta")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--dispatch", proc.stderr)


@unittest.skipUnless(_HAVE_SCIP, "needs scip-go, the scip CLI and go on PATH")
class LiveIndexerMeasurementTests(unittest.TestCase):
    """The measurement this whole layer rests on, re-taken against the real tool."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        tree = Path(cls.tmp.name) / "go_iface_app"
        shutil.copytree(IFACE_APP, tree)
        index_path = runner.run_scip_index(tree, "go", timeout=600)
        try:
            cls.normalized = runner.read_scip_index(index_path, retain=True)
        finally:
            index_path.unlink(missing_ok=True)
        cls.result = scip_facts.export_bundle(
            cls.normalized, ast_raw=_ast(), source_root=tree, language="go",
            index_digest=cls.normalized["index_digest"],
            index_digest_kind=cls.normalized["index_digest_kind"])

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_the_live_index_emits_the_same_implementation_relationships(self) -> None:
        self.assertEqual(self.result.status, scip_facts.STATUS_COMPLETE, self.result.messages)
        live = _rows(self.result.bundle, cha.RELATIONSHIP_RELATION)
        self.assertEqual(live, _rows(_export(_ast()).bundle, cha.RELATIONSHIP_RELATION),
                         f"{GOLDEN.name} is stale: re-take it from scip-go")
        self.assertIn([SQL_FETCH, REPO_FETCH, cha.IMPLEMENTATION], live)
        self.assertIn([SQL_TYPE, REPO_TYPE, cha.IMPLEMENTATION], live)

    def test_the_live_index_expands_to_the_same_dispatch_site(self) -> None:
        fragment = cha.cha_bundle(self.result.bundle, self.normalized, _ast())
        self.assertEqual(_rows(fragment, cha.DISPATCH_RELATION),
                         [[GET_THING, REPO_FETCH, "api/api.go", DISPATCH_LINE]])


def _have_treesitter() -> bool:
    """The go call-site census needs the ``treesitter`` extra, and the profile
    refuses rather than censusing nothing -- so a live profile run needs it."""
    try:
        from capcov.scip import blindspots

        blindspots._ts_language("go")
    except Exception:  # noqa: BLE001 - any failure means no census
        return False
    return True


@unittest.skipUnless(_HAVE_SCIP and _have_treesitter(),
                     "needs scip-go, the scip CLI, go and the treesitter extra")
class LiveDispatchProfileTests(unittest.TestCase):
    """``--dispatch cha`` end to end: index for real, expand, write the bundle.

    Only what the INDEX fixes is asserted -- the sites, the expansion and its
    witness.  What the real call-site census finds is the census's business and
    is asserted by the tests above, on a census this file writes.
    """

    def test_the_profile_expands_a_real_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "go_iface_app"
            shutil.copytree(IFACE_APP, tree)
            ast_raw = Path(tmp) / "ast.json"
            ast_raw.write_text(json.dumps(_ast()), encoding="utf-8")
            out = Path(tmp) / "bundle.json"
            proc = subprocess.run(
                [sys.executable, "-m", "capcov", "experiment", "claims", "static",
                 "--static", "scip", "--target", str(tree), "--language", "go",
                 "--ast-raw", str(ast_raw), "--dispatch", "cha", "--out", str(out)],
                text=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(SRC)})
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            document = json.loads(proc.stdout)
            self.assertEqual(document["dispatch"], "cha")
            self.assertEqual(document["cha_pack"], cha.PACK_ID)
            self.assertEqual(document[cha.DISPATCH_RELATION], 1)
            self.assertEqual(document[cha.UNEXPANDED_RELATION], 0)
            self.assertTrue(document[cha.EDGE_CLOSED_RELATION])
            payload = json.loads(out.read_text(encoding="utf-8"))
        from capcov.claims import bundle_from_json

        relations = _closure_of(combine(bundle_from_json(payload, validate=True), pack_bundle()))
        self.assertEqual(_payload(relations, "static_edge_cha"),
                         sorted([[GET_THING, MEMORY_FETCH, REPO_FETCH],
                                 [GET_THING, SQL_FETCH, REPO_FETCH]]))
        self.assertEqual(_payload(relations, "static_capability_op"), [])
        self.assertEqual(_payload(relations, "static_capability_op_cha"),
                         [[SURFACE, ENTITY, "read"]])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
