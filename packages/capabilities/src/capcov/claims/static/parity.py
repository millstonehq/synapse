"""Static store parity: what the incumbent's routes reach and the candidate's do not.

Two static indexes in one bundle -- an incumbent (``phpstan_facts``, a PHP
tree) and a candidate (``scip_facts``, the port) -- and one reviewer document
saying which route of each answers the same operation.  The index is a column,
so two of them coexist without anything being renamed; what does *not* come for
free is the right to join them, and this module is that right made explicit.

WHAT THE REVIEWER OWNS
----------------------
``op_maps(index, op, incumbent_surface, candidate_surface)``
    "Operation ``op`` is served by this route of the incumbent and that route
    of the candidate."  A judgement about intent -- nobody can read it off
    either tree -- so producer class ``reviewer``, keyed by the incumbent index
    the map is a map *of*.

``op_maps_closed(index)``
    The reviewer's completeness witness: "these are all the operations".
    Without it an incumbent route the map omits is only unmentioned; with it,
    ``parity_route_unmapped`` names it.  A parity run over a partial map is
    still a parity run -- it simply cannot say that what it did not compare
    does not exist.

``op_maps_describes_indexes(map, incumbent, candidate)``
    The compatibility witness that licenses the cross-index join, and the only
    thing that does: every rule reading a row of one index beside a row of the
    other carries it, and ``map`` is the content digest of the reviewer's
    document, so a certificate names the map it was derived under.

WHAT IS DERIVED, AND UNDER WHICH CLOSURE
----------------------------------------
``static_parity(index, op, table)``
    Both sides' routes reach that table.  Positive on both sides: no witness
    needed, and the strongest thing a static account can say before a vector is
    recorded.

``parity_static_only_incumbent(index, op, table)``
    The incumbent reaches it and the candidate *cannot*: a missing capability,
    found before anything is run.  A negation about a program, so it is gated
    on the candidate's own ``static_route_reaches_table_closed`` -- which is
    gated on ``call_graph_closed`` -- and on nothing weaker.

``parity_blocked(index, op, table, via)`` / ``parity_unresolved(index, op, table)``
    The same table, the same absence, with the candidate's call graph *not*
    closed: an unresolved call site is reachable from the candidate's handler
    (``via`` names the symbol the doubt enters through), or there is residue in
    the candidate index and no owner to name.  Neither is a verdict, and both
    are said out loud rather than folded into the one above.

The intermediate ``parity_table_unreached_in_index`` is the step-1 relation
``reflexion`` names in its own words: *does this bundle exhibit the reach?*,
answerable from the bundle alone and therefore gated only on
``parity_reach_in_index_closed`` (the candidate index is current, and these are
the reaches it has).  It is not a statement about the program, nothing reports
it as one, and both program-level readings of it -- settled and blocked -- are
derived separately above.  The table domain comes from the *incumbent* side, so
a store the candidate has never heard of is compared rather than quietly
skipped.

NOTHING RUNS
------------
No repository is cloned, no analysis is executed and no private name appears:
the inputs are two exported bundles and a JSON document of route spellings.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..ir import Bundle, RelationDecl, bundle_from_json, digest
from . import scip_facts
from .combine import combine

PACK_NAME = "rules-static-parity-v1.json"
PACK_ID = "rules-static-parity-v1"
BASE_PACK_ID = "rules-static-v1"
CLOSURE_PACK_ID = "rules-static-closure-v1"
REFLEXION_PACK_ID = "rules-static-reflexion-v1"

#: Producer class of every row this module emits.
PRODUCER_CLASS = "reviewer"
EMITTER = "capcov.claims.static.parity"
#: Emission contracts, named in each row's evidence source.
CONTRACT_MAP = "op-maps-v1"
CONTRACT_MAP_CLOSED = "op-maps-closed-v1"
CONTRACT_DESCRIBES = "op-maps-describes-indexes-v1"

MAP_RELATION = "op_maps"
MAP_CLOSED_RELATION = "op_maps_closed"
DESCRIBES_RELATION = "op_maps_describes_indexes"
#: The relation whose rule ``parity_blocked`` needs; it lives in the reflexion pack.
UNRESOLVED_ON_RELATION = "static_unresolved_on"
#: The export relation a mapped surface has to appear in.
SURFACE_RELATION = "route_site"

#: The model document's schema version, carried in the file and checked here.
MODEL_SCHEMA_VERSION = 1


class ParityInputError(ValueError):
    """The map, or an export it is asserted against, is not one this module reads."""


@dataclass(frozen=True)
class OperationMap:
    """One reviewer map: operation -> (incumbent route, candidate route), and closure.

    ``digest`` is the content identity of the document and is the ``map``
    column of ``op_maps_describes_indexes``: editing the map changes it, so a
    certificate cannot be replayed against a map that has since moved.
    """

    operations: tuple[tuple[str, str, str], ...] = ()
    closed: bool = False

    @property
    def document(self) -> dict[str, Any]:
        return {"closed": self.closed,
                "operations": {op: [incumbent, candidate]
                               for op, incumbent, candidate in self.operations}}

    @property
    def digest(self) -> str:
        return digest(self.document)

    @property
    def incumbent_surfaces(self) -> tuple[str, ...]:
        return tuple(sorted({incumbent for _op, incumbent, _c in self.operations}))

    @property
    def candidate_surfaces(self) -> tuple[str, ...]:
        return tuple(sorted({candidate for _op, _i, candidate in self.operations}))


def load_pack() -> dict[str, Any]:
    """The parity rule pack document, read as package data (source tree or wheel)."""
    return json.loads(resources.files(__package__).joinpath(PACK_NAME).read_text(encoding="utf-8"))


def pack_relations(pack: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    pack = pack or load_pack()
    return [*pack["primitives"], *pack["borrowed_declarations"], *pack["derived"]]


def pack_bundle(pack: Mapping[str, Any] | None = None) -> Bundle:
    """The pack alone -- declarations and rules, no facts -- as a validated Bundle."""
    pack = pack or load_pack()
    return bundle_from_json({"schema_version": 1, "relations": pack_relations(pack),
                             "rules": [dict(rule) for rule in pack["rules"]]}, validate=True)


def relation_decls(pack: Mapping[str, Any] | None = None) -> dict[str, RelationDecl]:
    return {decl.name: decl for decl in pack_bundle(pack).relations}


def model_from_document(document: Any) -> OperationMap:
    """Read the reviewer's document, refusing anything unclear.

    ``{"schema_version": 1, "closed": bool, "operations": {op: [incumbent_route,
    candidate_route]}}``.  ``closed`` defaults to ``false``: a reviewer who has
    not said the map is complete has not said it, and the negation that reads
    it stays underived.
    """
    if not isinstance(document, Mapping):
        raise ParityInputError("the operation map document must be a JSON object")
    unknown = sorted(set(document) - {"schema_version", "closed", "operations"})
    if unknown:
        raise ParityInputError(f"the operation map document has unknown fields {unknown}")
    if document.get("schema_version") != MODEL_SCHEMA_VERSION:
        raise ParityInputError(
            f"the operation map document must declare schema_version {MODEL_SCHEMA_VERSION}")
    operations = document.get("operations")
    if not isinstance(operations, Mapping) or not operations:
        raise ParityInputError("the operation map needs a non-empty 'operations' object")
    rows = []
    for op, pair in operations.items():
        if (not isinstance(op, str) or not op or not isinstance(pair, (list, tuple))
                or len(pair) != 2 or not all(isinstance(v, str) and v for v in pair)):
            raise ParityInputError(
                "an operation maps a name to an [incumbent_route, candidate_route] pair")
        rows.append((op, pair[0], pair[1]))
    closed = document.get("closed", False)
    if not isinstance(closed, bool):
        raise ParityInputError("the operation map document's 'closed' must be true or false")
    return OperationMap(tuple(sorted(set(rows))), closed)


def load_model(path: str | Path) -> OperationMap:
    """``model_from_document`` over a file, naming the file that is wrong."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ParityInputError(f"cannot read {path}: {exc}") from exc
    return model_from_document(document)


def declared_surfaces(export: Bundle) -> frozenset[str]:
    """Every surface this index declares a route site for."""
    return frozenset(fact.terms[1].value for fact in export.facts
                     if fact.relation == SURFACE_RELATION)


def unknown_surfaces(export: Bundle, surfaces: Iterable[str]) -> tuple[str, ...]:
    """Mapped surfaces this index does not declare -- a stale or mistyped map."""
    declared = declared_surfaces(export)
    return tuple(surface for surface in surfaces if surface not in declared)


def _index_of(export: Bundle, side: str) -> str:
    metadata = dict(export.metadata)
    if "index_digest" not in metadata:
        raise ParityInputError(
            f"the {side} export carries no 'index_digest' metadata; pass a bundle from "
            f"scip_facts.export_bundle or phpstan_facts.export_bundle")
    return str(metadata["index_digest"])


def map_bundle(incumbent: Bundle, candidate: Bundle, model: OperationMap) -> Bundle:
    """The fragment: the reviewer's rows, the witnesses, and the pack's rules.

    Refuses a map naming a route either index does not declare.  A mistyped
    route spelling would otherwise silently reach no table on that side and be
    reported as a missing capability of the candidate -- the one mistake this
    precheck must not make -- so it is named, on the side it is missing from,
    and nothing is derived.
    """
    incumbent_index = _index_of(incumbent, "incumbent")
    candidate_index = _index_of(candidate, "candidate")
    if incumbent_index == candidate_index:
        raise ParityInputError(
            "the incumbent and the candidate are the same index; parity compares two")
    for side, export, surfaces in (("incumbent", incumbent, model.incumbent_surfaces),
                                   ("candidate", candidate, model.candidate_surfaces)):
        missing = unknown_surfaces(export, surfaces)
        if missing:
            raise ParityInputError(
                f"the operation map names {len(missing)} route(s) the {side} index does not "
                f"declare: {', '.join(missing[:5])}" + (" ..." if len(missing) > 5 else ""))
    decls = relation_decls()
    depends_on = tuple(sorted(
        record.id
        for export in (incumbent, candidate)
        for record in export.evidence
        if record.atom.relation in ("scip_index", "scip_index_tree")))
    if not depends_on:
        raise ParityInputError("the exports declare no scip_index evidence to depend on")
    model_digest = model.digest

    facts, evidence = [], []

    def add(relation: str, row: list[Any], contract: str) -> None:
        source = f"{PRODUCER_CLASS} {EMITTER} {contract} {model_digest}"
        facts.append(_atom(decls[relation], relation, row))
        evidence.append(_evidence(decls[relation], relation, row, incumbent_index, source,
                                  depends_on))

    for op, incumbent_surface, candidate_surface in model.operations:
        add(MAP_RELATION, [incumbent_index, op, incumbent_surface, candidate_surface],
            CONTRACT_MAP)
    if model.closed:
        add(MAP_CLOSED_RELATION, [incumbent_index], CONTRACT_MAP_CLOSED)
    add(DESCRIBES_RELATION, [model_digest, incumbent_index, candidate_index], CONTRACT_DESCRIBES)

    pack = pack_bundle()
    return Bundle(pack.relations, facts=tuple(facts), rules=pack.rules,
                  evidence=tuple(evidence),
                  metadata=(("emitter", EMITTER), ("pack", PACK_ID),
                            ("base_pack", BASE_PACK_ID), ("closure_pack", CLOSURE_PACK_ID),
                            ("reflexion_pack", REFLEXION_PACK_ID),
                            ("incumbent_index", incumbent_index),
                            ("candidate_index", candidate_index),
                            ("model_digest", model_digest),
                            ("op_maps_rows", len(model.operations)),
                            ("op_maps_closed", model.closed)))


def _atom(decl: RelationDecl, relation: str, row: list[Any]):
    from ..ir import Atom, Constant

    return Atom(relation, tuple(Constant(scip_facts._checked(relation, column, value), column.type)
                                for column, value in zip(decl.columns, row)))


def _evidence(decl: RelationDecl, relation: str, row: list[Any], index: str,
              source: str, depends_on: tuple[str, ...]):
    from ..ir import Context, Evidence

    atom = _atom(decl, relation, row)
    context = {column.name: value for column, value in zip(decl.columns, row) if column.context}
    return Evidence(scip_facts.evidence_id(index, relation, row), atom,
                    Context.from_mapping(context), source, tuple(depends_on))


def attach(incumbent: Bundle, candidate: Bundle, model: OperationMap, *bundles: Bundle,
           validate: bool = True, **combine_kwargs: Any) -> Bundle:
    """Both exports, the map fragment and any further bundles, validated as one.

    Refuses a merge in which ``static_unresolved_on`` has a declaration and no
    rule: ``parity_blocked`` is the only reading of an unsettled comparison that
    names where the doubt enters, and a bundle missing the reflexion pack would
    derive it empty and report the same case as the weaker
    ``parity_unresolved`` -- a silent downgrade rather than a missing pack.
    """
    result = combine(incumbent, candidate, map_bundle(incumbent, candidate, model), *bundles,
                     validate=validate, **combine_kwargs)
    if not any(rule.head.relation == UNRESOLVED_ON_RELATION for rule in result.rules):
        raise ParityInputError(
            f"the merged bundle declares {UNRESOLVED_ON_RELATION!r} with no rule; merge "
            f"{REFLEXION_PACK_ID} (reflexion.pack_bundle()) so parity_blocked can derive")
    return result


__all__ = ["PACK_NAME", "PACK_ID", "BASE_PACK_ID", "CLOSURE_PACK_ID", "REFLEXION_PACK_ID",
           "PRODUCER_CLASS", "EMITTER", "CONTRACT_MAP", "CONTRACT_MAP_CLOSED",
           "CONTRACT_DESCRIBES", "MAP_RELATION", "MAP_CLOSED_RELATION", "DESCRIBES_RELATION",
           "UNRESOLVED_ON_RELATION", "SURFACE_RELATION", "MODEL_SCHEMA_VERSION",
           "ParityInputError", "OperationMap", "load_pack", "pack_relations", "pack_bundle",
           "relation_decls", "model_from_document", "load_model", "declared_surfaces",
           "unknown_surfaces", "map_bundle", "attach"]
