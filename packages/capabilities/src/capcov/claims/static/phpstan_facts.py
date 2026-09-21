"""The incumbent's edge producer: a PHPStan/Larastan report as static facts.

``scip_facts`` exports what a SCIP index says.  On a Laravel-shaped PHP tree a
SCIP index says very little about the edges that matter: ``scip-php`` resolves
*symbols* well and *calls through the framework* not at all, so ``DB::``,
``Auth::``, ``Route::`` and every Eloquent static forward lands in the
resolver's residue as ``facade_magic`` (``scip/blindspots.py``'s PHP census
kinds), and a call graph whose framework edges are all residue never earns
``call_graph_closed``.  PHPStan with Larastan is the producer that *can* type
those receivers, so this module makes it one: it reads the JSON report of the
bundled collector (``packages/capabilities/phpstan/CapcovCallCollector.php``)
and emits the **same static schema** -- ``schema_static_v1`` plus one relation
of its own -- so ``rules-static-v1``, ``rules-static-closure-v1``,
``rules-static-reflexion-v1`` and the vectors join apply to a PHP index
unchanged.

PRODUCER CLASS
--------------
``phpstan``, never ``scip``.  Larastan's resolution *is* an assumption about
framework behaviour -- that ``DB::table()`` returns a query builder, that an
Eloquent static forwards to one -- and an assumption that arrives wearing the
indexer's class would be indistinguishable from something the index said.  Each
row's ``Evidence.source`` therefore begins with ``phpstan``, and the two
relations the closure layer owns (``static_unresolved_call_site``,
``call_graph_closed``) declare ``["phpstan", "scip"]``: two producers that can
each know that closure, and no third.

WHAT THE COLLECTOR REPORTS, AND WHAT IS DONE WITH IT
----------------------------------------------------
The report is PHPStan's own ``--error-format=json`` document; every message the
bundled rules emit is ``capcov-fact:`` followed by one JSON object, and every
other message in the report is ignored (a real analysis has real errors in it,
and they are not facts about the call graph).  The objects, and the rows each
becomes:

``analysed``  -> the in-scope document set, and ``scip_document``.  The census
    is the analysis: a file PHPStan analysed had every call node of it visited,
    so ``census_available`` is true exactly when the report names its files.
``symbol``    -> ``scip_symbol`` + ``scip_definition_site``.  ``category``
    ``callable`` is what ``static_route_handler`` joins on.
``entity``    -> ``static_entity`` (the model's literal ``$table``, or the
    literal a facade names).
``op``        -> ``static_op_site``: the storage verb at that site.
``call``      -> ``phpstan_call_edge(index, caller, callee, path, line, kind)``,
    lifted into ``static_edge`` by ``rules-static-phpstan-v1``, plus
    ``static_site_owner`` for the caller.  ``kind`` records *which resolution*
    produced the edge -- ``direct``, ``larastan-facade``,
    ``larastan-model-forward``, ``larastan-container``, ``direct-propel`` -- so
    a reader can tell a typed call from a framework assumption without
    re-running anything.  The column never widens ``static_edge``: the lift
    drops it, and a consumer that cares reads the ``phpstan_call_edge`` row.
``unresolved`` -> ``scip_unresolved_site`` (with the reason in ``kind``) and,
    in the closure fragment, ``static_unresolved_call_site``.  A ``mixed``
    receiver is PHPStan's own "call on mixed": the analyser names the site it
    cannot type, and that named site *is* the residue.  Nothing is dropped and
    nothing is guessed.
``route`` / ``route_excluded`` -> ``route_site`` + ``route_handler_location``
    (joined to the handler's own definition site) / ``route_site_excluded``.

CLOSURE
-------
``closure_fragment`` is ``closure``'s emission contract with this producer's
rows: ``call_graph_closed(index, scope)`` fires for a scope token if and only
if the report enumerated its files and **no** unresolved site falls in any of
them -- zero ``mixed`` receivers, zero magic calls, zero unattributed sites.
On the fixture the ``*`` token is withheld for exactly one ``__call`` site, and
a ``document_set`` scope closes the files that do not contain it, one document
at a time.

IDENTITY
--------
``scip_facts``'s recipe, unchanged (``static-relations-v1``): a content digest
of the emitted rows, computed after the rows are assembled and before the
evidence ids are, so two exports of one report agree on the ``index`` digest,
on every evidence id and on ``bundle_digest`` whatever order the report lists
its messages in.  The report file's own digest is a *receipt*
(``index_file_digest``), not identity.  Reusing the recipe rather than minting
a second one is what lets an incumbent and a candidate index live in one bundle
and be told apart by their digests alone (``parity``).

LINE FRAME
----------
1-based, PHP's own and the frame every other static relation is in.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from ... import artifacts
from ..ir import Bundle, RelationDecl, bundle_from_json, canonical_json
from ..validation import ValidationError, assert_valid
from . import closure, scip_facts
from .scip_facts import (ExportLimits, ExportResult, STATUS_COMPLETE,
                         STATUS_INVALID_INPUT, STATUS_RESOURCE_EXHAUSTED, Scope)

PACK_NAME = "rules-static-phpstan-v1.json"
PACK_ID = "rules-static-phpstan-v1"
BASE_PACK_ID = "rules-static-v1"
CLOSURE_PACK_ID = "rules-static-closure-v1"

EXPORT_VERSION = "v1"
EMITTER = "capcov.claims.static.phpstan_facts"
PRODUCER = f"{EMITTER} {EXPORT_VERSION}"

#: Producer class of every row this module emits.
PRODUCER_CLASS = "phpstan"
#: The bundled collector's contract version, named in every collected row's source.
COLLECTOR = "CapcovCallCollector-v1"
#: Emission contracts, named in each witness's source.
WITNESS_ROUTE_INVENTORY = "route-inventory-closed-v1"
WITNESS_CALL_GRAPH = "call-graph-closed-v1"

#: The prefix that marks a report message as one of the collector's facts.
FACT_PREFIX = "capcov-fact:"
#: The language every row of this producer is about.
LANGUAGE = "php"

EDGE_RELATION = "phpstan_call_edge"

#: How an edge was resolved.  Enumerated, never open: a kind this module does
#: not know is a collector it was not built against, and reading it as
#: ``direct`` would launder an assumption into a typed call.
KIND_DIRECT = "direct"
KIND_FACADE = "larastan-facade"
KIND_MODEL_FORWARD = "larastan-model-forward"
KIND_CONTAINER = "larastan-container"
KIND_PROPEL = "direct-propel"
EDGE_KINDS = frozenset({KIND_DIRECT, KIND_FACADE, KIND_MODEL_FORWARD,
                        KIND_CONTAINER, KIND_PROPEL})

#: Why a call site is unresolved.  ``mixed-receiver`` is PHPStan's own; the
#: others name the shape the collector saw and could not follow.
REASON_MIXED = "mixed-receiver"
REASON_MAGIC = "magic-call"
REASON_DYNAMIC = "dynamic-method"
REASON_UNATTRIBUTED = "caller-unattributed"
REASON_ENTITY_NOT_LITERAL = "non-literal-entity"
UNRESOLVED_REASONS = frozenset({REASON_MIXED, REASON_MAGIC, REASON_DYNAMIC,
                                REASON_UNATTRIBUTED, REASON_ENTITY_NOT_LITERAL})

#: The storage verbs ``static_op_site`` is written in (``core`` CRUD).
OP_VERBS = frozenset({"create", "read", "update", "delete"})

#: ``scip_symbol.category`` values this module emits; ``callable`` is the one
#: ``static_route_handler`` joins on.
CATEGORIES = frozenset({"callable", "type", "term", "other"})

_FACT_KINDS = frozenset({"analysed", "symbol", "entity", "op", "call",
                         "unresolved", "route", "route_excluded"})

#: The report's content identity, which every emitted row depends on.
REPORT_IDENTITY = "phpstan-report-v1"


class ReportInputError(ValueError):
    """The report is not one this module can read."""


# ---------------------------------------------------------------------------
# Reading the report


def read_report(document: Any) -> tuple[dict[str, Any], ...]:
    """Every ``capcov-fact:`` payload of a PHPStan JSON report, canonically ordered.

    Messages that are not the collector's are ignored -- a report of a real
    analysis carries real errors, and they are not facts about the call graph.
    The result is sorted, so the identity of an export does not depend on the
    order PHPStan happened to group its files in.
    """
    if not isinstance(document, Mapping):
        raise ReportInputError("a PHPStan report is a JSON object")
    files = document.get("files")
    if not isinstance(files, Mapping):
        raise ReportInputError("the report carries no 'files' object; pass the output of "
                               "phpstan analyse --error-format=json")
    payloads: list[dict[str, Any]] = []
    for entry in files.values():
        if not isinstance(entry, Mapping):
            continue
        for message in entry.get("messages") or ():
            text = message.get("message") if isinstance(message, Mapping) else None
            if not isinstance(text, str) or not text.startswith(FACT_PREFIX):
                continue
            try:
                payload = json.loads(text[len(FACT_PREFIX):])
            except json.JSONDecodeError as exc:
                raise ReportInputError(f"a capcov-fact message is not JSON: {exc}") from exc
            if not isinstance(payload, Mapping) or payload.get("fact") not in _FACT_KINDS:
                raise ReportInputError(f"unknown collector fact {payload!r}")
            payloads.append(dict(payload))
    return tuple(sorted(payloads, key=canonical_json))


def load_report(path: str | Path) -> tuple[dict[str, Any], ...]:
    """``read_report`` over a file, naming the file that is wrong."""
    try:
        return read_report(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportInputError(f"cannot read {path}: {exc}") from exc


def report_digest(facts: Iterable[Mapping[str, Any]]) -> str:
    """The content identity of a report's collected facts (a receipt, not the index)."""
    payload = canonical_json({"recipe": REPORT_IDENTITY,
                              "facts": sorted((dict(f) for f in facts), key=canonical_json)})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _of(facts: Iterable[Mapping[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [dict(fact) for fact in facts if fact.get("fact") == kind]


def _str(fact: Mapping[str, Any], key: str) -> str:
    value = fact.get(key)
    if not isinstance(value, str) or not value:
        raise ReportInputError(f"{fact.get('fact')!r} fact needs a non-empty {key!r}: {fact!r}")
    return value


def _line(fact: Mapping[str, Any]) -> int:
    value = fact.get("line")
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ReportInputError(f"{fact.get('fact')!r} fact needs a 1-based line: {fact!r}")
    return value


# ---------------------------------------------------------------------------
# The pack


def load_pack() -> dict[str, Any]:
    """The phpstan rule pack document, read as package data (source tree or wheel)."""
    from importlib import resources

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


def export_relations() -> tuple[RelationDecl, ...]:
    """The frozen static schema, the derived stubs, and this pack's own primitive.

    ``phpstan_call_edge`` is declared here as well as in the pack because the
    export carries its rows and must validate alone; ``combine`` merges the two
    declarations by identity, so the pack's is what both say.
    """
    own = {decl.name: decl for decl in pack_bundle().relations}
    frozen = scip_facts.static_relations()
    names = {decl.name for decl in frozen}
    return frozen + tuple(decl for name, decl in sorted(own.items()) if name not in names)


# ---------------------------------------------------------------------------
# The export


def export_bundle(
    facts: Iterable[Mapping[str, Any]],
    *,
    source_root: str | Path,
    analyser: str = "phpstan",
    analyser_version: str,
    scope: Scope | None = None,
    limits: ExportLimits | None = None,
    commit: str | None = None,
    describes_runs: Iterable[str] = (),
    observe_tree: bool = False,
) -> ExportResult:
    """Export one collector report as a validated static-facts ``Bundle``.

    Pure over its inputs but for the language-scoped tree walk that produces
    ``scip_index_tree`` and ``static_source_file`` -- the same walk
    ``scip_facts`` does, over the same pattern set, so an incumbent index and a
    candidate index are hashed by one recipe.

    ``observe_tree`` adds the claim-time ``source_tree_observed`` row for the
    tree just walked, without which ``static_index_current`` -- and so
    ``static_capability_op``, and so every parity verdict -- cannot derive.  It
    is off by default: a caller that already observes the tree (the reflexion
    fragment does) must not observe it twice.
    """
    scope = scope or Scope.all()
    limits = limits or ExportLimits()
    facts = tuple(dict(fact) for fact in facts)
    messages: list[str] = []

    problem = _input_problem(facts, scope, analyser_version)
    if problem:
        return ExportResult(STATUS_INVALID_INPUT, None, {}, (problem,))

    analysed = sorted({_str(fact, "path") for fact in _of(facts, "analysed")})
    if len(analysed) > limits.documents:
        return ExportResult(STATUS_RESOURCE_EXHAUSTED, None, {"documents": len(analysed)},
                            (f"documents {len(analysed)} exceed limit {limits.documents}",))

    patterns = artifacts.patterns_for(LANGUAGE)
    manifest = artifacts.tree_manifest(Path(source_root), patterns)
    tree_digest = artifacts.manifest_sha256(manifest)
    tracked = {path for path, _sha in manifest}
    untracked = [path for path in analysed if path not in tracked]
    if untracked:
        return ExportResult(
            STATUS_INVALID_INPUT, None, {},
            (f"the report analysed {len(untracked)} file(s) the source tree does not carry "
             f"({', '.join(untracked[:3])}); the report and the tree are not the same tree",))

    relations = {decl.name: decl for decl in export_relations()}
    accumulator = scip_facts._Facts(scip_facts._PLACEHOLDER_INDEX, relations)
    ix = {"index": scip_facts._PLACEHOLDER_INDEX}
    digest = report_digest(facts)
    receipt = f"external:phpstan-report:{digest[:12]}"
    collector_source = f"{PRODUCER_CLASS} {analyser} {analyser_version} {COLLECTOR}"
    emitter_source = f"{PRODUCER_CLASS} {PRODUCER}"
    witness_source = f"{PRODUCER_CLASS} {EMITTER} "

    try:
        index_eid = accumulator.add("scip_index", {
            **ix, "indexer": analyser, "indexer_version": analyser_version,
            "language": LANGUAGE, "project_root": "",
            "digest_kind": scip_facts.INDEX_IDENTITY,
        }, source=collector_source, depends_on=[receipt])
        tree_eid = accumulator.add("scip_index_tree", {
            **ix, "tree_digest": tree_digest, "file_count": len(manifest),
            "pattern": " ".join(patterns),
        }, source=emitter_source, depends_on=[index_eid])
        base = [index_eid, tree_eid, receipt]
        if commit:
            accumulator.add("scip_index_commit", {**ix, "commit": commit}, source=emitter_source,
                            depends_on=[index_eid, f"external:git-commit:{commit}"])
        for value in scope.rows():
            accumulator.add("static_scope", {**ix, "scope_kind": scope.kind,
                                             "scope_value": value},
                            source=emitter_source, depends_on=[index_eid])
        accumulator.add("static_language_covered", {**ix, "language": LANGUAGE},
                        source=collector_source, depends_on=[index_eid])
        for rel_path, _sha in manifest:
            accumulator.add("static_source_file", {**ix, "path": rel_path,
                                                   "language": LANGUAGE},
                            source=emitter_source, depends_on=[tree_eid])
        for run in sorted(set(describes_runs)):
            accumulator.add("index_describes_run", {**ix, "run": run}, source=emitter_source,
                            depends_on=[index_eid, f"external:run:{run}"])

        in_file: dict[str, int] = {path: 0 for path in analysed}
        symbols_in: dict[str, int] = {path: 0 for path in analysed}
        for fact in facts:
            path = fact.get("path")
            if isinstance(path, str) and path in in_file:
                in_file[path] += 1
                if fact.get("fact") == "symbol":
                    symbols_in[path] += 1
        for path in analysed:
            accumulator.add("scip_document", {
                **ix, "path": path, "language": LANGUAGE,
                "occurrence_count": in_file[path], "symbol_count": symbols_in[path],
                "enclosing_synthesized": False,
            }, source=collector_source, depends_on=base)

        definitions: dict[str, tuple[str, int]] = {}
        for fact in _of(facts, "symbol"):
            symbol, path, line = _str(fact, "symbol"), _str(fact, "path"), _line(fact)
            category = _str(fact, "category")
            if category not in CATEGORIES:
                raise ReportInputError(f"unknown symbol category {category!r}")
            accumulator.add("scip_symbol", {
                **ix, "symbol": symbol, "kind": _str(fact, "kind"), "category": category,
                "display_name": str(fact.get("display") or symbol),
            }, source=collector_source, depends_on=base)
            accumulator.add("scip_definition_site", {
                **ix, "path": path, "line": line, "symbol": symbol,
            }, source=collector_source, depends_on=base)
            definitions.setdefault(symbol, (path, line))

        for fact in _of(facts, "entity"):
            accumulator.add("static_entity", {
                **ix, "entity": _str(fact, "entity"), "path": _str(fact, "path"),
                "line": _line(fact), "table": _str(fact, "table"),
            }, source=collector_source, depends_on=base)

        for fact in _of(facts, "op"):
            verb = _str(fact, "verb")
            if verb not in OP_VERBS:
                raise ReportInputError(f"unknown storage verb {verb!r}")
            accumulator.add("static_op_site", {
                **ix, "path": _str(fact, "path"), "line": _line(fact), "verb": verb,
                "entity": _str(fact, "entity"),
            }, source=collector_source, depends_on=base)

        owners: set[tuple[str, int, str]] = set()
        for fact in _of(facts, "call"):
            kind = _str(fact, "kind")
            if kind not in EDGE_KINDS:
                raise ReportInputError(f"unknown call resolution kind {kind!r}")
            caller, path, line = _str(fact, "caller"), _str(fact, "path"), _line(fact)
            accumulator.add(EDGE_RELATION, {
                **ix, "caller": caller, "callee": _str(fact, "callee"), "path": path,
                "line": line, "kind": kind,
            }, source=collector_source, depends_on=base)
            owners.add((path, line, caller))

        for fact in _of(facts, "unresolved"):
            reason = _str(fact, "reason")
            if reason not in UNRESOLVED_REASONS:
                raise ReportInputError(f"unknown unresolved reason {reason!r}")
            path, line = _str(fact, "path"), _line(fact)
            accumulator.add("scip_unresolved_site", {
                **ix, "path": path, "line": line, "callee_text": _str(fact, "callee"),
                "kind": reason,
            }, source=collector_source, depends_on=base)
            caller = fact.get("caller")
            if isinstance(caller, str) and caller:
                owners.add((path, line, caller))

        for path, line, symbol in sorted(owners):
            accumulator.add("static_site_owner", {
                **ix, "path": path, "line": line, "symbol": symbol,
            }, source=collector_source, depends_on=base)

        undefined_handlers = []
        for fact in _of(facts, "route"):
            surface, handler = _str(fact, "surface"), _str(fact, "handler")
            accumulator.add("route_site", {
                **ix, "surface": surface, "path": _str(fact, "path"), "line": _line(fact),
                "handler_name": handler,
            }, source=collector_source, depends_on=base)
            definition = definitions.get(handler)
            if definition is None:
                undefined_handlers.append(surface)
                accumulator.add("static_unresolved", {
                    **ix, "kind": "route-handler-undefined", "node": handler,
                    "path": _str(fact, "path"), "line": _line(fact),
                }, source=collector_source, depends_on=base)
                continue
            accumulator.add("route_handler_location", {
                **ix, "surface": surface, "path": definition[0], "line": definition[1],
            }, source=emitter_source, depends_on=base)

        excluded = _of(facts, "route_excluded")
        for fact in excluded:
            accumulator.add("route_site_excluded", {
                **ix, "surface": _str(fact, "surface"), "reason": _str(fact, "reason"),
            }, source=collector_source, depends_on=base)

        if analysed and not excluded and not undefined_handlers:
            accumulator.add("static_route_inventory_closed", ix,
                            source=witness_source + WITNESS_ROUTE_INVENTORY,
                            depends_on=[index_eid, tree_eid])
    except (ReportInputError, scip_facts.ExportInputError) as exc:
        return ExportResult(STATUS_INVALID_INPUT, None, accumulator.counts(), (str(exc),))

    if len(accumulator) > limits.rows:
        return ExportResult(STATUS_RESOURCE_EXHAUSTED, None, accumulator.counts(),
                            (f"rows {len(accumulator)} exceed limit {limits.rows}",))

    index = accumulator.identity()
    accumulator.rebase(index)
    messages.append(f"index identity {index} ({scip_facts.INDEX_IDENTITY}); the report digest "
                    f"{digest} (json) is a run receipt, not identity")
    fact_atoms, evidence = accumulator.materialize()
    if observe_tree:
        from . import pilot

        atom, record = pilot.source_tree_observation(
            relations, tree_digest,
            source=f"{PRODUCER_CLASS} {EMITTER} claim-time observation of the analysed tree")
        fact_atoms, evidence = (*fact_atoms, atom), (*evidence, record)

    metadata = {
        "export_version": EXPORT_VERSION,
        "exporter": EMITTER,
        "index_digest": index,
        "index_digest_kind": scip_facts.INDEX_IDENTITY,
        "index_file_digest": digest,
        "index_file_digest_kind": "json",
        "language": LANGUAGE,
        "profile": scip_facts.PROFILE_SLICE,
        "scope": {"kind": scope.kind, "values": scope.rows()},
        "producers": {"indexer": analyser, "indexer_version": analyser_version,
                      "collector": COLLECTOR, "exporter": PRODUCER},
        "tree": {"digest": tree_digest, "file_count": len(manifest),
                 "pattern": " ".join(patterns)},
        "line_frame": scip_facts.LINE_FRAME,
        "census_available": bool(analysed),
        "in_scope_documents": analysed,
        "row_counts": accumulator.counts(),
    }
    if commit:
        metadata["commit"] = commit
    bundle = Bundle(tuple(relations.values()), fact_atoms, (), (), tuple(metadata.items()),
                    evidence=evidence)
    try:
        assert_valid(bundle)
    except ValidationError as exc:
        return ExportResult(STATUS_INVALID_INPUT, None, accumulator.counts(),
                            tuple(f"{i.code}: {i.message} at {i.path}" for i in exc.issues)
                            if hasattr(exc, "issues") else (str(exc),))
    return ExportResult(STATUS_COMPLETE, bundle, accumulator.counts(), tuple(messages))


def _input_problem(facts: tuple[dict[str, Any], ...], scope: Scope,
                   analyser_version: str) -> str | None:
    if not isinstance(analyser_version, str) or not analyser_version:
        return "analyser_version must be a non-empty string; it is part of the index identity"
    if scope.kind not in scip_facts._SCOPE_KINDS:
        return f"unknown scope kind {scope.kind!r}"
    if scope.kind != scip_facts.SCOPE_ALL and not scope.values:
        return f"scope {scope.kind!r} needs at least one value"
    if not _of(facts, "analysed"):
        return ("the report names no analysed file; without them there is no census and no "
                "scope, and 'no unresolved site' would be a claim about nothing")
    return None


# ---------------------------------------------------------------------------
# The closure fragment


def unresolved_rows(facts: Iterable[Mapping[str, Any]]) -> list[tuple[str, int, str]]:
    """``(file, line, callee)`` per unresolved site, in canonical order."""
    return sorted({(_str(fact, "path"), _line(fact), _str(fact, "callee"))
                   for fact in _of(tuple(facts), "unresolved")})


def closure_fragment(export: Bundle, facts: Iterable[Mapping[str, Any]]) -> Bundle:
    """``closure``'s two relations, with this producer's rows and this producer's class.

    Same emission contract as ``closure.closure_bundle`` -- the residue as rows
    in every case, the witness only for a scope token whose documents carry
    none of them -- over the collector's census instead of the SCIP resolver's.
    """
    facts = tuple(dict(fact) for fact in facts)
    metadata = dict(export.metadata)
    for key in ("index_digest", "scope", "in_scope_documents", "census_available"):
        if key not in metadata:
            raise ReportInputError(f"the export carries no {key!r} metadata; pass a bundle "
                                   f"from phpstan_facts.export_bundle")
    index = str(metadata["index_digest"])
    decls = closure.relation_decls()
    depends_on = tuple(sorted(record.id for record in export.evidence
                              if record.atom.relation in ("scip_index", "scip_index_tree")))
    if not depends_on:
        raise ReportInputError("the export declares no scip_index evidence to depend on")
    producers = dict(metadata.get("producers") or {})
    collected = (f"{PRODUCER_CLASS} {producers.get('indexer', 'phpstan')} "
                 f"{producers.get('indexer_version', 'unknown')} {COLLECTOR}")
    witness = f"{PRODUCER_CLASS} {EMITTER} {WITNESS_CALL_GRAPH}"

    atoms, evidence = [], []

    def add(relation: str, values: list[Any], source: str) -> None:
        row = [index, *values]
        atoms.append(closure._atom(decls[relation], relation, row))
        evidence.append(closure._evidence(decls[relation], relation, row, index, source,
                                          depends_on))

    residue = unresolved_rows(facts)
    for file, line, callee in residue:
        add(closure.UNRESOLVED_RELATION, [file, line, callee], collected)

    if metadata["census_available"]:
        unresolved_files = {file for file, _, _ in residue}
        for token, documents in sorted(closure.scope_tokens(
                dict(metadata["scope"]), metadata["in_scope_documents"]).items()):
            if unresolved_files.intersection(documents):
                continue
            add(closure.CLOSED_RELATION, [token], witness)

    pack = closure.pack_bundle()
    return Bundle(pack.relations, facts=tuple(atoms), rules=pack.rules,
                  evidence=tuple(evidence),
                  metadata=(("emitter", EMITTER), ("pack", closure.PACK_ID),
                            ("base_pack", BASE_PACK_ID), ("index_digest", index),
                            ("residue_rows", len(residue))))


def attach(export: Bundle, facts: Iterable[Mapping[str, Any]], *bundles: Bundle,
           validate: bool = True, **combine_kwargs: Any) -> Bundle:
    """``export`` plus the closure fragment (plus any further bundles), validated.

    The lifting rule lives in this module's own pack and the call-graph rules in
    ``rules-static-v1``, so a caller merges whichever of those it wants
    evaluated -- exactly as the SCIP side does.
    """
    from .combine import combine

    return combine(export, closure_fragment(export, facts), *bundles,
                   validate=validate, **combine_kwargs)


__all__ = ["PACK_NAME", "PACK_ID", "BASE_PACK_ID", "CLOSURE_PACK_ID", "EXPORT_VERSION",
           "EMITTER", "PRODUCER", "PRODUCER_CLASS", "COLLECTOR", "FACT_PREFIX", "LANGUAGE",
           "EDGE_RELATION", "EDGE_KINDS", "UNRESOLVED_REASONS", "OP_VERBS", "CATEGORIES",
           "REPORT_IDENTITY", "WITNESS_ROUTE_INVENTORY", "WITNESS_CALL_GRAPH",
           "ReportInputError", "read_report", "load_report", "report_digest", "load_pack",
           "pack_relations", "pack_bundle", "relation_decls", "export_relations",
           "export_bundle", "unresolved_rows", "closure_fragment", "attach"]
