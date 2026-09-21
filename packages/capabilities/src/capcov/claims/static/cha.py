"""Class-hierarchy expansion for the ``--static scip`` profile (opt-in, ``--dispatch cha``).

A SCIP index resolves a call through an interface to the *interface's* member,
not to the implementations that could run.  ``scip_facts`` exports that faithfully
and the resolver puts the site in its residue, so ``call_graph_closed`` is
withheld and every negative claim over such a target stays unresolved.  This
module adds the expansion that class-hierarchy analysis (Doop's terminology, and
its discipline of keeping the expansion a *separate* relation) licenses, and adds
it beside the export exactly as ``closure`` does.

MEASURED, NOT ASSUMED
---------------------
Whether an indexer emits implementation relationships at all is a property of
the indexer, and this module refuses to guess.  ``scip-go`` 0.2.7 was measured on
``tests/fixtures/go_iface_app``: it emits ``is_implementation`` for both the
method (``SQL#Fetch().`` -> ``Repo#Fetch.``) and the type (``SQL#`` -> ``Repo#``),
and they arrive in the export as ``scip_relationship(index, symbol, related,
"implementation")`` -- a primitive the frozen schema already declares, so nothing
in the export changes.  The same measurement showed the other half of the
problem: scip-go types an interface member as ``MethodSpecification``, which
``scip.map._category`` classifies as a *term*, so the dispatch site is not in
``scip_may_reference`` and the caller side of the expansion has to be named here.

``MEASURED_INDEXERS`` is that measurement, and an indexer not in it is refused by
name (:class:`DispatchUnsupported`): an absent relationship is indistinguishable
from an indexer that never emits one, and inferring "no implementations" from an
indexer nobody has measured would be support from silence.

WHAT IS EMITTED
---------------
``static_interface_dispatch_site(index, caller, interface_symbol, path, line)``
    A caller-attributed reference to a symbol this index declares an interface
    member of -- the site whose callee the index could not pin down.  The
    attribution is ``scip.map``'s innermost-caller rule, the same one
    ``scip_may_reference`` uses, so a dispatch site is attributed exactly as a
    resolved call is.

``static_cha_unexpanded_site(index, path, line, interface_symbol, reason)``
    Every dispatch site the expansion could not cover, with the reason:
    ``caller_unattributed`` (module scope -- there is no ``from`` to expand from),
    ``no_implementation_in_index`` (nothing implements it here),
    ``implementation_out_of_scope`` (an implementation this slice does not
    define) or ``co_located_residue`` (the census gives this line more than one
    unresolved callee, and discharge cannot tell them apart -- see below).
    Enumerated, never dropped: these are the sites that keep the expansion from
    being complete, and they are why the witness below is withheld.

``static_edge_cha_closed(index)``
    The expansion's own completeness witness, emitted only when no site was
    enumerated as unexpanded and the export's scope is the whole index (a slice
    does not export the relationship rows of the documents it leaves out, so it
    cannot see the implementation it is missing).  It completes ``static_edge_cha`` -- never
    ``static_edge``, which is what ``call_graph_closed`` completes and which this
    module does not touch.

``call_graph_closed_cha(index, scope)``
    The call graph *with* the expansion, over one scope token: emitted when the
    expansion is closed, the census was taken, and every unresolved call site in
    that scope is discharged by an expansion **of that exact site**.  A residue
    row that is not a dispatch site (reflection, a dynamic method name) is never
    discharged, and one unexpanded site withholds the witness for every token.
    "That exact site" is a ``(path, line)`` join -- the residue's callee is not a
    column the dispatch site carries -- so a line carrying both a dispatch and a
    reflective call is expanded not at all rather than expanded and joined
    loosely, which would discharge the reflective call along with it.

    It completes ``static_reaches_cha``, and it is what the ``*_cha`` verdicts
    rest on instead of ``call_graph_closed``, which is withheld on precisely the
    targets this profile exists for.

MAY, NOT MUST
-------------
A CHA edge is an over-approximation: the expansion says the dispatch *could*
land there, never that it does.  So no ``*_cha`` row is ever merged into the
relation it twins -- they are read as a separate account, stronger than the
resolved graph on the negative side (an entity no expansion reaches is more
convincingly dead) and weaker on the positive side (a lifted edge may not be
realisable).  ``static_edge`` keeps its meaning and its witness.

PRODUCER
--------
``scip``, like ``closure``: the rows are the index's relationships and the
index's occurrences, read through the resolver's own attribution.  The
dispatch-site and unexpanded rows name the indexer that produced the index; each
witness names the emission contract that was checked.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any, Iterable, Mapping

from ...scip import map as scip_map
from ..ir import Bundle, RelationDecl, bundle_from_json
from . import closure, reflexion, scip_facts
from .combine import combine

PACK_NAME = "rules-static-cha-v1.json"
PACK_ID = "rules-static-cha-v1"
BASE_PACK_ID = "rules-static-v1"
CLOSURE_PACK_ID = "rules-static-closure-v1"
REFLEXION_PACK_ID = "rules-static-reflexion-v1"

#: Producer class of every row this module emits.
PRODUCER_CLASS = "scip"
EMITTER = "capcov.claims.static.cha"
#: Each witness's emission contract, named in its evidence source.
WITNESS_EDGE_CHA = "static-edge-cha-closed-v1"
WITNESS_CALL_GRAPH_CHA = "call-graph-closed-cha-v1"

DISPATCH_RELATION = "static_interface_dispatch_site"
UNEXPANDED_RELATION = "static_cha_unexpanded_site"
EDGE_CLOSED_RELATION = "static_edge_cha_closed"
CLOSED_RELATION = "call_graph_closed_cha"

#: The export relation this module reads the hierarchy off, and the kind column
#: value that makes a row an implementation edge.
RELATIONSHIP_RELATION = "scip_relationship"
IMPLEMENTATION = "implementation"

#: The export relation that says what a symbol IS, and the kinds that make one an
#: interface member -- the callee a dispatch resolves to.  ``MethodSpecification``
#: is scip-go's ``SymbolKind`` 67, measured on ``tests/fixtures/go_iface_app``.
#: Membership is read from the kind and not from the hierarchy, so an interface
#: member nothing in this index implements is still SEEN as a dispatch site and
#: enumerated, instead of vanishing with the relationships it does not have.
SYMBOL_RELATION = "scip_symbol"
INTERFACE_MEMBER_KINDS = frozenset({"MethodSpecification"})

#: Reasons a dispatch site is enumerated instead of expanded.
REASON_UNATTRIBUTED = "caller_unattributed"
REASON_NO_IMPLEMENTATION = "no_implementation_in_index"
REASON_OUT_OF_SCOPE = "implementation_out_of_scope"
#: A site the census gives more than one unresolved callee for.  Discharge is a
#: join on ``(path, line)`` -- the residue row's callee is not a column the
#: dispatch site carries -- so expanding one call on a line would discharge
#: every unresolved call on it, including calls no expansion covers.  Such a
#: site is expanded not at all and enumerated instead.
REASON_CO_LOCATED_RESIDUE = "co_located_residue"

#: What a ``source_tree_observed`` row emitted by this module says it is.
TREE_OBSERVATION_SOURCE = "scip claim-time observation of the indexed tree"

#: Indexer -> the version on which implementation relationships were MEASURED to
#: be emitted (see the module docstring).  An indexer absent from this mapping is
#: refused rather than treated as emitting none.
MEASURED_INDEXERS = {"scip-go": "0.2.7"}


class ChaInputError(ValueError):
    """The export this fragment is built against is not one this module can read."""


class DispatchUnsupported(ChaInputError):
    """No measurement says this indexer emits SCIP implementation relationships."""


class MapCoverageUnsatisfied(reflexion.ReflexionInputError):
    """A closed capability map omits a symbol the expansion's edges run through.

    A ``ReflexionInputError``: the document at fault is the reviewer's map, and
    a caller that already treats a map/index mismatch as a usage refusal treats
    this one the same way.
    """


def load_pack() -> dict[str, Any]:
    """The CHA rule pack document, read as package data (source tree or wheel)."""
    return json.loads(resources.files(__package__).joinpath(PACK_NAME).read_text(encoding="utf-8"))


def pack_relations(pack: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Every relation declaration the pack carries, owned and borrowed alike."""
    pack = pack or load_pack()
    return [*pack["primitives"], *pack["borrowed_declarations"], *pack["derived"]]


def pack_bundle(pack: Mapping[str, Any] | None = None) -> Bundle:
    """The pack alone -- declarations and rules, no facts -- as a validated Bundle."""
    pack = pack or load_pack()
    return bundle_from_json({"schema_version": 1, "relations": pack_relations(pack),
                             "rules": [dict(rule) for rule in pack["rules"]]}, validate=True)


def relation_decls(pack: Mapping[str, Any] | None = None) -> dict[str, RelationDecl]:
    return {decl.name: decl for decl in pack_bundle(pack).relations}


def require_measured_indexer(producers: Mapping[str, Any]) -> None:
    """Refuse, by name, an indexer no measurement covers.

    ``producers`` is the export metadata's ``{"indexer", "indexer_version", ...}``.
    The refusal says what was measured rather than asserting what the unmeasured
    indexer does: this module cannot tell "emits none" from "was never looked at",
    and only one of those is a fact.  It ends with the remedy, as every other
    absent-capability refusal in this package does: ``--dispatch cha`` is an
    optional expansion, and dropping it still produces the resolved bundle.
    """
    indexer = str(producers.get("indexer") or "")
    version = str(producers.get("indexer_version") or "")
    if indexer in MEASURED_INDEXERS:
        return
    measured = ", ".join(f"{name} {ver}" for name, ver in sorted(MEASURED_INDEXERS.items()))
    named = " ".join(part for part in (indexer or "this indexer", version) if part)
    raise DispatchUnsupported(
        f"unsupported: no measurement that {named} emits SCIP implementation "
        f"relationships; --dispatch cha is measured for {measured}. "
        f"Re-run with --dispatch none (the default) for the resolved account alone, "
        f"or index with an indexer the measurement covers")


def implementations(export: Bundle) -> dict[str, tuple[str, ...]]:
    """``interface member -> the symbols this index says implement it``.

    Read off the export's own ``scip_relationship`` rows, so the hierarchy is the
    indexer's statement and not a re-reading of the index.
    """
    out: dict[str, set[str]] = {}
    for fact in export.facts:
        if fact.relation != RELATIONSHIP_RELATION:
            continue
        _, symbol, related, kind = (term.value for term in fact.terms)
        if kind == IMPLEMENTATION:
            out.setdefault(related, set()).add(symbol)
    return {member: tuple(sorted(symbols)) for member, symbols in out.items()}


def interface_members(export: Bundle) -> frozenset[str]:
    """Every symbol this index declares an interface member (``scip_symbol`` kind)."""
    return frozenset(fact.terms[1].value for fact in export.facts
                     if fact.relation == SYMBOL_RELATION
                     and fact.terms[2].value in INTERFACE_MEMBER_KINDS)


def defined_symbols(export: Bundle) -> frozenset[str]:
    """Every symbol this slice defines (``scip_definition_site``).

    An implementation outside it is an expansion point this bundle cannot carry,
    which is what ``implementation_out_of_scope`` reports.
    """
    return frozenset(fact.terms[3].value for fact in export.facts
                     if fact.relation == "scip_definition_site")


def dispatch_sites(export: Bundle, normalized: Mapping[str, Any],
                   in_scope: Iterable[str]) -> list[tuple[str | None, str, str, int]]:
    """``(caller, interface member, path, line)`` per dynamic-dispatch site.

    Every *term*-category reference to a symbol the index declares an interface
    member, attributed to its innermost enclosing definition by
    ``scip.map.reference_edges`` -- the same walk, and so the same attribution,
    that ``scip_may_reference`` is built from.  ``caller`` is ``None`` at module
    scope; the row is kept and enumerated rather than dropped.
    """
    members = interface_members(export)
    documents = set(in_scope)
    rows = []
    for edge in scip_map.reference_edges(normalized, "term"):
        path, line = edge["file"], edge["line"]
        if edge["symbol"] not in members or path not in documents or line is None:
            continue
        rows.append((edge["owner"], edge["symbol"], path,
                     line + scip_facts._SCIP_LINE_IS_ZERO_BASED))
    return sorted(set(rows), key=lambda row: (row[2], row[3], row[1], row[0] or ""))


def co_located_residue_sites(ast_raw: Mapping[str, Any]) -> frozenset[tuple[str, int]]:
    """``(path, line)`` the census gives more than one unresolved callee for.

    ``static_cha_site_discharged`` joins the residue to the dispatch site on
    ``(path, line)`` alone -- the residue row's callee is the census's column,
    not the index's, and the dispatch site has no such column to join on.  So a
    line carrying two unresolved calls, only one of them a dispatch, would have
    both discharged by the one expansion, and ``call_graph_closed_cha`` would be
    emitted over a call graph that still contains the other.  Naming those sites
    is what lets :func:`cha_bundle` expand none of them.
    """
    seen: dict[tuple[str, int], set[str]] = {}
    for path, line, callee in closure.residue_rows(ast_raw):
        seen.setdefault((path, line), set()).add(callee)
    return frozenset(site for site, callees in seen.items() if len(callees) > 1)


def expansion_edge_symbols(expanded: Iterable[tuple[str, str]],
                           hierarchy: Mapping[str, tuple[str, ...]]) -> frozenset[str]:
    """Every symbol ``static_edge_cha`` runs through, from ``(caller, member)`` pairs.

    The ``src`` and ``dst`` of the edges the expansion will derive -- the CHA
    mirror of :func:`reflexion.edge_endpoint_symbols`, which reads
    ``scip_may_reference`` and therefore cannot see an endpoint that exists only
    because of this expansion.  The interface is not among them: it is the
    edge's ``via_interface`` witness, not one of the two symbols the lift reads.
    """
    out: set[str] = set()
    for caller, member in expanded:
        out.add(caller)
        out.update(hierarchy.get(member) or ())
    return frozenset(out)


def require_mapped_expansion(model: reflexion.CapabilityModel | None,
                             symbols: Iterable[str]) -> None:
    """Refuse a *closed* capability map that omits a symbol the expansion runs through.

    ``reflexion.model_bundle`` makes exactly this check for the resolved graph,
    reading ``scip_may_reference``; a CHA endpoint is in neither that relation
    nor that check, so a closed map may omit one, fail to lift the expanded edge
    and then report the reviewer's edge as ``static_absence_cha`` -- a claim that
    the code lacks an edge the bundle demonstrably carries.  Same shape, same
    refusal, same reason: coverage is the one part of a reviewer's say-so this
    package can check, and it is checked before the witness is emitted.  An open
    map licenses no negation and is free to be partial.
    """
    if model is None or not model.closed:
        return
    mapped = frozenset(model.symbols)
    unmapped = tuple(sorted(symbol for symbol in symbols if symbol not in mapped))
    if not unmapped:
        return
    raise MapCoverageUnsatisfied(
        f"the capability map declares closure but does not map {len(unmapped)} "
        f"symbol(s) the dispatch expansion's edges run through: "
        f"{', '.join(unmapped[:5])}" + (" ..." if len(unmapped) > 5 else ""))


def unexpanded_reason(caller: str | None, member: str,
                      hierarchy: Mapping[str, tuple[str, ...]],
                      defined: frozenset[str]) -> str | None:
    """Why this dispatch site cannot be expanded, or ``None`` when it can."""
    if caller is None:
        return REASON_UNATTRIBUTED
    targets = hierarchy.get(member) or ()
    if not targets:
        return REASON_NO_IMPLEMENTATION
    if any(target not in defined for target in targets):
        return REASON_OUT_OF_SCOPE
    return None


def cha_bundle(export: Bundle, normalized: Mapping[str, Any], ast_raw: Mapping[str, Any],
               *, model: reflexion.CapabilityModel | None = None,
               tree_digest: str | None = None) -> Bundle:
    """The fragment: dispatch sites, unexpanded sites, both witnesses, the rules.

    Built against a finished ``scip_facts`` export (its identity, its scope and
    its in-scope documents) and the normalized index that export was made from,
    and returned *unvalidated* -- its evidence depends on the export's own
    ``scip_index`` rows, so it is a fragment of that bundle and :func:`attach` is
    what validates the whole.  ``ast_raw`` is the resolver's raw dict, read for
    the residue rows exactly as ``closure`` reads them, so both modules count the
    same census.

    ``tree_digest`` is for a caller that has just indexed the tree it is
    describing, and adds the claim-time ``source_tree_observed`` row that
    ``static_index_current`` -- and so ``static_capability_op_cha``, and so every
    ``*_cha`` entity row -- rests on.  ``reflexion.model_bundle`` emits the same
    row, so a caller merging both fragments passes it to exactly one of them.

    ``model`` is the reviewer's :class:`reflexion.CapabilityModel` when this
    fragment is built beside one.  A *closed* map that omits a symbol the
    expansion's edges run through is refused by name
    (:func:`require_mapped_expansion`): ``reflexion``'s own coverage check reads
    ``scip_may_reference`` and cannot see a CHA endpoint, and an omitted one
    turns a real expanded edge into a ``static_absence_cha`` the code refutes.
    """
    metadata = closure._metadata(export)
    producers = dict(metadata["producers"])
    require_measured_indexer(producers)
    index = str(metadata["index_digest"])
    indexer_source = f"{PRODUCER_CLASS} {producers['indexer']} {producers['indexer_version']}"
    decls = relation_decls()
    depends_on = tuple(sorted(
        record.id for record in export.evidence
        if record.atom.relation in ("scip_index", "scip_index_tree")))
    if not depends_on:
        raise ChaInputError("the export declares no scip_index evidence to depend on")

    facts, evidence = [], []

    def add(relation: str, values: list[Any], source: str) -> None:
        row = [index, *values]
        facts.append(closure._atom(decls[relation], relation, row))
        evidence.append(closure._evidence(decls[relation], relation, row, index, source,
                                          depends_on))

    hierarchy = implementations(export)
    defined = defined_symbols(export)
    sites = dispatch_sites(export, normalized, metadata["in_scope_documents"])
    co_located = co_located_residue_sites(ast_raw)
    expanded: set[tuple[str, int]] = set()
    expansions: list[tuple[str, str, str, int]] = []
    unexpanded = []
    for caller, member, path, line in sites:
        reason = unexpanded_reason(caller, member, hierarchy, defined)
        # Discharge is a join on (path, line), so a dispatch site sharing its
        # line with another unresolved callee is expanded not at all: expanding
        # it would discharge that other call too, and close a call graph that
        # still runs through it.
        if reason is None and (path, line) in co_located:
            reason = REASON_CO_LOCATED_RESIDUE
        if reason is None:
            expansions.append((caller, member, path, line))
        else:
            unexpanded.append((path, line, member, reason))
    # Refuse before a row is emitted: edges running through a symbol a CLOSED
    # map omits would lift incompletely and read as an absence in the code.
    require_mapped_expansion(
        model,
        expansion_edge_symbols(((caller, member) for caller, member, _, _ in expansions),
                               hierarchy))
    for caller, member, path, line in expansions:
        add(DISPATCH_RELATION, [caller, member, path, line], indexer_source)
        expanded.add((path, line))
    for path, line, member, reason in sorted(set(unexpanded)):
        add(UNEXPANDED_RELATION, [path, line, member, reason], indexer_source)

    # A narrower scope can hide an implementation the INDEX knows about -- the
    # relationship rows of an out-of-scope document are not exported, so the
    # expansion cannot even see what it is missing.  Completeness is therefore
    # claimed only over the whole index; a slice gets the rows and no witness.
    scope_kind = dict(metadata["scope"]).get("kind")
    edge_closed = not unexpanded and scope_kind == scip_facts.SCOPE_ALL
    if edge_closed:
        add(EDGE_CLOSED_RELATION, [], f"{PRODUCER_CLASS} {EMITTER} {WITNESS_EDGE_CHA}")

    closed_tokens: list[str] = []
    if edge_closed and metadata["census_available"]:
        residue = closure.residue_rows(ast_raw)
        undischarged = {(path, line) for path, line, _ in residue
                        if (path, line) not in expanded}
        witness_source = f"{PRODUCER_CLASS} {EMITTER} {WITNESS_CALL_GRAPH_CHA}"
        tokens = closure.scope_tokens(dict(metadata["scope"]), metadata["in_scope_documents"])
        for token, documents in sorted(tokens.items()):
            if any(path in documents for path, _ in undischarged):
                continue
            add(CLOSED_RELATION, [token], witness_source)
            closed_tokens.append(token)

    if tree_digest is not None:
        from . import pilot

        export_decls = {decl.name: decl for decl in export.relations}
        if "source_tree_observed" not in export_decls:
            raise ChaInputError(
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
                            ("reflexion_pack", REFLEXION_PACK_ID), ("index_digest", index),
                            ("dispatch_sites", len(sites) - len(unexpanded)),
                            ("unexpanded_sites", len(unexpanded)),
                            ("edge_cha_closed", edge_closed),
                            ("call_graph_closed_cha", tuple(closed_tokens))))


def attach(export: Bundle, normalized: Mapping[str, Any], ast_raw: Mapping[str, Any],
           *bundles: Bundle, model: reflexion.CapabilityModel | None = None,
           tree_digest: str | None = None, validate: bool = True,
           **combine_kwargs: Any) -> Bundle:
    """``export`` plus the CHA fragment (plus any further bundles), validated.

    The closure fragment is what carries the residue rows this pack's discharge
    rules read, and the base pack is what derives ``static_edge`` and
    ``static_reaches``; both are merged by the caller in ``bundles``, exactly as
    ``reflexion.attach`` expects them.
    """
    return combine(export,
                   cha_bundle(export, normalized, ast_raw, model=model,
                              tree_digest=tree_digest),
                   *bundles, validate=validate, **combine_kwargs)


__all__ = ["PACK_NAME", "PACK_ID", "BASE_PACK_ID", "CLOSURE_PACK_ID", "REFLEXION_PACK_ID",
           "PRODUCER_CLASS", "EMITTER", "WITNESS_EDGE_CHA", "WITNESS_CALL_GRAPH_CHA",
           "DISPATCH_RELATION", "UNEXPANDED_RELATION", "EDGE_CLOSED_RELATION",
           "CLOSED_RELATION", "RELATIONSHIP_RELATION", "IMPLEMENTATION",
           "SYMBOL_RELATION", "INTERFACE_MEMBER_KINDS", "REASON_UNATTRIBUTED",
           "REASON_NO_IMPLEMENTATION", "REASON_OUT_OF_SCOPE",
           "REASON_CO_LOCATED_RESIDUE",
           "TREE_OBSERVATION_SOURCE", "MEASURED_INDEXERS", "ChaInputError", "DispatchUnsupported",
           "MapCoverageUnsatisfied", "load_pack",
           "pack_relations", "pack_bundle", "relation_decls", "require_measured_indexer",
           "implementations", "interface_members", "defined_symbols", "dispatch_sites",
           "co_located_residue_sites", "expansion_edge_symbols", "require_mapped_expansion",
           "unexpanded_reason", "cha_bundle", "attach"]
