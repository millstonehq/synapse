"""Reflexion over the static facts: a reviewer model, the lift, and dead/blocked.

``scip_facts`` exports what the index says; ``closure`` adds the residue rows
and the ``call_graph_closed`` witness a negative static claim needs.  This
module adds the third account a reflexion model (Murphy/Notkin/Sullivan) needs
and that neither of those can produce: the **reviewer's** high-level model of
the system, and the rules that compare it with the call graph.

It is a fragment merged beside an export, exactly as ``closure`` is, and it is
emitted only when a map is supplied: with no ``--capability-map`` the profile's
bundle is byte-for-byte what it was.

WHAT THE REVIEWER OWNS
----------------------
``capability_map(index, symbol, capability)``
    "This index symbol belongs to that capability."  A judgement about
    architecture, not a fact about code: producer class ``reviewer``.

``capability_edge(index, src, dst)``
    "Capability ``src`` is supposed to use capability ``dst``."  The intended
    architecture -- the *high-level* model the lifted call graph is compared
    against.  Also ``reviewer``.

``capability_map_closed(index)`` / ``capability_edge_closed(index)``
    The reviewer's own completeness witnesses, emitted only when the model
    document says so.  Without the first there is no closed lift and therefore
    no ``static_absence``; without the second a code edge the model omits can
    never be ``static_divergence``, because the model's silence about it might
    only mean the model is partial.  This is the producer that can know
    closure: nobody but the author of a map knows whether it is exhaustive.

``capability_map_describes_index(map, index)``
    The compatibility witness binding one model *document* (``map`` is its
    digest) to one static index.  Every rule that consumes the map reads it, so
    a model that was never asserted against this index derives nothing, and the
    certificate for any lifted row names the document it came from.

WHAT IS DERIVED
---------------
``static_low_edge`` lifts ``static_edge`` through the map (self-edges within one
capability are dropped: a capability calling itself is not an architectural
edge).  ``static_convergence`` is a model edge the lift exhibits,
``static_divergence`` a lifted edge the closed model does not declare, and
``static_absence`` a model edge the code does not realise.

``static_capability_op`` is reused as the binding relation -- this pack does not
re-derive it.  ``static_entity_bound`` is only its verb-projected form, which a
negation needs because negated variables must be positively bound; the verbs
themselves stay in ``static_capability_op``.

TWO CLOSURES, AND WHY THEY ARE NOT THE SAME
-------------------------------------------
There are two different questions about a missing row, and this pack keeps them
apart by name:

1. *Does this index exhibit it?*  Always answerable from the bundle, because
   the bundle is all the index said.  ``static_low_edge_closed`` (given a closed
   map) and ``static_entity_bound_closed`` (given a current index) are these,
   and the relations they license are named for what they are:
   ``static_model_edge_unlifted`` and ``static_entity_unbound_in_index``.
   Neither is a statement about the program.

2. *Does the program have it?*  Only answerable when the call graph is closed.
   ``static_absence`` and ``static_entity_dead`` are these, and each is derived
   from the step-1 relation **plus** ``call_graph_closed`` over the export's own
   scope.  Drop the witness -- inject one unresolved call site -- and they go
   empty: the question stops being settled, and that is the honest answer.

What is said instead depends on how much is known about the residue, and both
cases are said, because an entity or a model edge that appears in no relation at
all is indistinguishable from one nothing applies to:

*The residue site has an owning symbol* (``static_site_owner``, which
``scip_facts`` emits only for a site whose enclosing symbol the index resolved).
``static_entity_blocked(index, surface, entity, via)``: the index exhibits no
binding, and an unresolved call site sits on a symbol reachable from the
handler.  ``via`` names that symbol, so "unresolved" comes with the place the
doubt enters.

*The residue site has no owner* -- scip-php's synthesized enclosing symbols, a
module-scope call, anything the exporter could not attribute.  There is no
``via`` to name and no reachability to test, so the weaker
``static_entity_unresolved(index, surface, entity)`` is what is derived: the
index has residue, so this entity's absence is not settled either.

``static_absence_unresolved`` is the same service for a model edge -- the model
declares it, the lift does not exhibit it, and the index has residue -- and it
is gated on the residue *row*, not on its owner, so it holds in both cases.  All
three are the weakest status, and none is ever read as a verdict.

PRODUCER
--------
Every row this module emits is ``reviewer``-classed and depends on the export's
own ``scip_index``/``scip_index_tree`` evidence: a map is always a map *of* an
index.  A ``scip``-sourced ``capability_map`` row is refused by
``validation``'s producer-class check, which is the point of declaring the
class: an indexer cannot manufacture architectural intent.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Mapping

from ..ir import Bundle, RelationDecl, bundle_from_json, digest
from . import scip_facts
from .combine import combine

PACK_NAME = "rules-static-reflexion-v1.json"
PACK_ID = "rules-static-reflexion-v1"
BASE_PACK_ID = "rules-static-v1"
CLOSURE_PACK_ID = "rules-static-closure-v1"

#: Producer class of every row this module emits.
PRODUCER_CLASS = "reviewer"
EMITTER = "capcov.claims.static.reflexion"
#: Emission contracts, named in each row's evidence source.
CONTRACT_MAP = "capability-map-v1"
CONTRACT_MAP_CLOSED = "capability-map-closed-v1"
CONTRACT_EDGE = "capability-edge-v1"
CONTRACT_EDGE_CLOSED = "capability-edge-closed-v1"
CONTRACT_DESCRIBES = "capability-map-describes-index-v1"

MAP_RELATION = "capability_map"
MAP_CLOSED_RELATION = "capability_map_closed"
EDGE_RELATION = "capability_edge"
EDGE_CLOSED_RELATION = "capability_edge_closed"
DESCRIBES_RELATION = "capability_map_describes_index"
#: The export relation whose endpoints a closed map has to cover.
INDEX_EDGE_RELATION = "scip_may_reference"

#: The model document's schema version, carried in the file and checked here.
MODEL_SCHEMA_VERSION = 1
#: What a ``source_tree_observed`` row emitted by this module says it is.
TREE_OBSERVATION_SOURCE = "reviewer claim-time observation of the indexed tree"


class ReflexionInputError(ValueError):
    """The model, or the export it is asserted against, is not one this reads."""


@dataclass(frozen=True)
class CapabilityModel:
    """One reviewer model: symbol -> capability, the intended edges, and closure.

    ``digest`` is the content identity of the whole model (both documents), and
    is the ``map`` column of ``capability_map_describes_index``.  Two runs that
    read the same files produce the same digest; editing either file changes it,
    so a certificate cannot be replayed against a model that has since moved.
    """

    capabilities: tuple[tuple[str, str], ...] = ()
    closed: bool = False
    edges: tuple[tuple[str, str], ...] = ()
    edges_closed: bool = False

    @property
    def document(self) -> dict[str, Any]:
        return {"capabilities": [list(pair) for pair in self.capabilities],
                "closed": self.closed,
                "edges": [list(pair) for pair in self.edges],
                "edges_closed": self.edges_closed}

    @property
    def digest(self) -> str:
        return digest(self.document)

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(sorted({symbol for symbol, _ in self.capabilities}))


def load_pack() -> dict[str, Any]:
    """The reflexion rule pack document, read as package data."""
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


def _strict(document: Any, allowed: set[str], what: str) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise ReflexionInputError(f"the {what} document must be a JSON object")
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise ReflexionInputError(f"the {what} document has unknown fields {unknown}")
    if document.get("schema_version") != MODEL_SCHEMA_VERSION:
        raise ReflexionInputError(
            f"the {what} document must declare schema_version {MODEL_SCHEMA_VERSION}")
    return dict(document)


def model_from_documents(map_document: Any, edges_document: Any = None) -> CapabilityModel:
    """Read the reviewer's two documents into a model, refusing anything unclear.

    The map is ``{"schema_version": 1, "closed": bool, "capabilities": {symbol:
    capability}}``; the optional edge model is ``{"schema_version": 1, "closed":
    bool, "edges": [[src, dst], ...]}``.  ``closed`` defaults to ``false`` in
    both: a reviewer who does not say their model is complete has not said it,
    and every negation over that model stays unresolved.
    """
    map_document = _strict(map_document, {"schema_version", "closed", "capabilities"}, "capability map")
    capabilities = map_document.get("capabilities")
    if not isinstance(capabilities, Mapping) or not capabilities:
        raise ReflexionInputError("the capability map needs a non-empty 'capabilities' object")
    rows = []
    for symbol, capability in capabilities.items():
        if not (isinstance(symbol, str) and symbol and isinstance(capability, str) and capability):
            raise ReflexionInputError("a capability map entry maps a symbol string to a capability string")
        rows.append((symbol, capability))
    closed = map_document.get("closed", False)
    edges: list[tuple[str, str]] = []
    edges_closed = False
    if edges_document is not None:
        edges_document = _strict(edges_document, {"schema_version", "closed", "edges"},
                                 "capability edge model")
        declared = edges_document.get("edges")
        if not isinstance(declared, (list, tuple)):
            raise ReflexionInputError("the capability edge model needs an 'edges' list")
        for entry in declared:
            if (not isinstance(entry, (list, tuple)) or len(entry) != 2
                    or not all(isinstance(value, str) and value for value in entry)):
                raise ReflexionInputError("a capability edge is a [src, dst] pair of names")
            edges.append((entry[0], entry[1]))
        edges_closed = edges_document.get("closed", False)
    for flag, what in ((closed, "capability map"), (edges_closed, "capability edge model")):
        if not isinstance(flag, bool):
            raise ReflexionInputError(f"the {what} document's 'closed' must be true or false")
    return CapabilityModel(tuple(sorted(set(rows))), bool(closed),
                           tuple(sorted(set(edges))), bool(edges_closed))


def load_model(map_path: str | Path, edges_path: str | Path | None = None) -> CapabilityModel:
    """``model_from_documents`` over two files, naming the file that is wrong."""
    def read(path):
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReflexionInputError(f"cannot read {path}: {exc}") from exc

    return model_from_documents(read(map_path),
                                read(edges_path) if edges_path is not None else None)


def index_symbols(export: Bundle) -> frozenset[str]:
    """Every symbol the export's index declares (``scip_symbol``)."""
    return frozenset(fact.terms[1].value for fact in export.facts
                     if fact.relation == "scip_symbol")


def unknown_symbols(export: Bundle, model: CapabilityModel) -> tuple[str, ...]:
    """Mapped symbols this index does not have -- a stale or mistyped map."""
    known = index_symbols(export)
    return tuple(symbol for symbol in model.symbols if symbol not in known)


def edge_endpoint_symbols(export: Bundle) -> frozenset[str]:
    """Every symbol this index's edges run through (``scip_may_reference``).

    These are the symbols the lift has to carry.  ``index_symbols`` is the
    larger set -- everything the index declares, most of which no edge touches.
    """
    return frozenset(value
                     for fact in export.facts if fact.relation == INDEX_EDGE_RELATION
                     for value in (fact.terms[1].value, fact.terms[2].value))


def unmapped_edge_symbols(export: Bundle, model: CapabilityModel) -> tuple[str, ...]:
    """Edge endpoints the map omits -- what a map claiming closure may not have.

    The mirror of ``unknown_symbols``: that one asks whether every mapped symbol
    is in the index, this one whether every symbol the index's edges run through
    is in the map.  Only the second can turn a real edge into a ``static_absence``.
    """
    mapped = frozenset(model.symbols)
    return tuple(sorted(symbol for symbol in edge_endpoint_symbols(export)
                        if symbol not in mapped))


def _metadata(export: Bundle) -> dict[str, Any]:
    metadata = dict(export.metadata)
    for key in ("index_digest", "producers"):
        if key not in metadata:
            raise ReflexionInputError(
                f"the export carries no {key!r} metadata; pass a bundle from "
                f"scip_facts.export_bundle")
    return metadata


def model_bundle(export: Bundle, model: CapabilityModel, *,
                 tree_digest: str | None = None) -> Bundle:
    """The fragment: the reviewer's rows, their witnesses, and the pack's rules.

    Refuses a model naming a symbol the index does not have: a map that has
    drifted from the code would otherwise lift nothing for that symbol and turn
    a real edge into a silent ``static_absence``.  Naming the symbols is the
    only safe failure, and it is a refusal rather than a dropped row.

    Refuses the other direction too, and only when the map says ``closed``: a
    symbol the index's edges run through that the map does not carry.  The
    witness ``capability_map_closed`` is what licenses ``static_absence``, and
    it is the reviewer's say-so; a map that declares completeness while omitting
    an edge endpoint fails to lift that edge and then reports it absent from
    code that demonstrably has it.  Coverage is the one part of that say-so this
    module can check, so it checks it before the witness is emitted.  An open
    map is free to be partial: it licenses no negation.

    ``tree_digest`` is for a caller that has just indexed the tree it is
    describing (the ``--static scip`` profile has): it adds the frozen
    ``source_tree_observed`` claim-time row, without which ``static_index_current``
    -- and so ``static_capability_op``, and so dead/blocked -- cannot derive.  A
    caller that already supplies that row must not pass it twice.
    """
    metadata = _metadata(export)
    index = str(metadata["index_digest"])
    missing = unknown_symbols(export, model)
    if missing:
        raise ReflexionInputError(
            f"the capability map names {len(missing)} symbol(s) this index does not "
            f"declare: {', '.join(missing[:5])}"
            + (" ..." if len(missing) > 5 else ""))
    unmapped = unmapped_edge_symbols(export, model) if model.closed else ()
    if unmapped:
        raise ReflexionInputError(
            f"the capability map declares closure but does not map {len(unmapped)} "
            f"symbol(s) this index's edges run through: {', '.join(unmapped[:5])}"
            + (" ..." if len(unmapped) > 5 else ""))
    decls = relation_decls()
    depends_on = tuple(sorted(
        record.id for record in export.evidence
        if record.atom.relation in ("scip_index", "scip_index_tree")))
    if not depends_on:
        raise ReflexionInputError("the export declares no scip_index evidence to depend on")
    model_digest = model.digest

    facts, evidence = [], []

    def add(relation: str, row: list[Any], contract: str) -> None:
        source = f"{PRODUCER_CLASS} {EMITTER} {contract} {model_digest}"
        facts.append(_atom(decls[relation], relation, row))
        evidence.append(_evidence(decls[relation], relation, row, index, source, depends_on))

    for symbol, capability in model.capabilities:
        add(MAP_RELATION, [index, symbol, capability], CONTRACT_MAP)
    if model.closed:
        add(MAP_CLOSED_RELATION, [index], CONTRACT_MAP_CLOSED)
    for src, dst in model.edges:
        add(EDGE_RELATION, [index, src, dst], CONTRACT_EDGE)
    if model.edges_closed:
        add(EDGE_CLOSED_RELATION, [index], CONTRACT_EDGE_CLOSED)
    add(DESCRIBES_RELATION, [model_digest, index], CONTRACT_DESCRIBES)

    if tree_digest is not None:
        from . import pilot

        export_decls = {decl.name: decl for decl in export.relations}
        if "source_tree_observed" not in export_decls:
            raise ReflexionInputError(
                "the export declares no 'source_tree_observed' relation to observe the "
                "tree against; pass a bundle from scip_facts.export_bundle")
        atom, record = pilot.source_tree_observation(
            export_decls, tree_digest, source=TREE_OBSERVATION_SOURCE)
        facts.append(atom)
        evidence.append(record)

    pack = pack_bundle()
    return Bundle(pack.relations, facts=tuple(facts), rules=pack.rules,
                  evidence=tuple(evidence),
                  metadata=(("emitter", EMITTER), ("pack", PACK_ID),
                            ("base_pack", BASE_PACK_ID), ("closure_pack", CLOSURE_PACK_ID),
                            ("index_digest", index), ("model_digest", model_digest),
                            ("capability_map_rows", len(model.capabilities)),
                            ("capability_map_closed", model.closed),
                            ("capability_edge_rows", len(model.edges)),
                            ("capability_edge_closed", model.edges_closed)))


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


def attach(export: Bundle, model: CapabilityModel, *bundles: Bundle,
           tree_digest: str | None = None, validate: bool = True,
           **combine_kwargs: Any) -> Bundle:
    """``export`` plus the reflexion fragment (plus any further bundles), validated.

    The base pack (``rules-static-v1``) is what derives ``static_edge``,
    ``static_route_handler`` and ``static_capability_op``, and the closure pack
    is what carries the residue and ``call_graph_closed``; this fragment borrows
    their declarations byte-for-byte and merges beside them, so a caller passes
    whichever of those it wants evaluated in ``bundles``.
    """
    return combine(export, model_bundle(export, model, tree_digest=tree_digest), *bundles,
                   validate=validate, **combine_kwargs)


__all__ = ["PACK_NAME", "PACK_ID", "BASE_PACK_ID", "CLOSURE_PACK_ID", "PRODUCER_CLASS",
           "EMITTER", "CONTRACT_MAP", "CONTRACT_MAP_CLOSED", "CONTRACT_EDGE",
           "CONTRACT_EDGE_CLOSED", "CONTRACT_DESCRIBES", "MAP_RELATION",
           "MAP_CLOSED_RELATION", "EDGE_RELATION", "EDGE_CLOSED_RELATION",
           "DESCRIBES_RELATION", "MODEL_SCHEMA_VERSION", "TREE_OBSERVATION_SOURCE",
           "ReflexionInputError", "CapabilityModel", "load_pack", "pack_relations",
           "pack_bundle", "relation_decls", "model_from_documents", "load_model",
           "index_symbols", "unknown_symbols", "edge_endpoint_symbols",
           "unmapped_edge_symbols", "model_bundle", "attach", "INDEX_EDGE_RELATION"]
