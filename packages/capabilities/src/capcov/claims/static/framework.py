"""Framework assumption rows: the edges no indexer can see, signed by a reviewer.

``scip_facts`` exports what the index says, ``closure`` turns what it could not
resolve into rows and a witness, and ``cha`` expands what the index's own
hierarchy licenses.  None of them can produce the edge a *framework* makes at
run time out of data: a ``net/http`` handler registered into a package-level
registry by an ``init()`` and invoked by a loop at startup, a Laravel container
binding or facade accessor Larastan cannot type, a FastAPI ``Depends``.  Those
edges are real and they are nobody's observation.  This module is where they
enter -- named, dated, signed, and kept in a relation of their own.

OPT IN, ADDITIVE, SEPARATE
--------------------------
The fragment exists only when ``--assumptions FILE.json`` names a document: with
no flag nothing under this module is imported and the bundle is byte-for-byte
what it was.  What it adds is ``static_edge_assumed`` -- never ``static_edge``,
which is what ``call_graph_closed`` completes -- and every verdict read off the
assumed graph is a separate ``*_assumed`` row.  An assumed edge is somebody's
say-so about a framework, not something the index exhibited, and a reader must
be able to tell the two apart without re-running anything.

WHAT A ROW SAYS
---------------
``framework_edge(index, src, dst, framework, mechanism, path, line)``
    "At ``path:line``, the ``framework`` binds ``src`` to ``dst`` through
    ``mechanism``."  The ``(framework, mechanism)`` pair is checked against
    :data:`MECHANISMS`: a mechanism nobody enumerated is refused rather than
    accepted as a free-text excuse, because the vocabulary is what makes a
    reader able to ask "is this true of that framework?" at all.  The ``path``
    and ``line`` are the site the row *stands for*, and the only site its
    discharge can cover.

``framework_assumption_unapplied(index, path, line, src, dst, reason)``
    Every row the producer could not apply, enumerated, never dropped:
    ``co_located_residue`` (the census gives that line more than one unresolved
    callee, and discharge is a ``(path, line)`` join, so applying this row would
    discharge a call no row covers -- the row is applied not at all, exactly as
    ``cha`` refuses a co-located dispatch site), ``no_unresolved_site`` (the
    census has no residue at that site: the row stands for nothing this index
    could not already see) and ``document_out_of_scope`` (the site is in a
    document this export does not carry).  These are why the witness below is
    withheld.

``assumptions_describe_index(assumptions, index)``
    The compatibility witness binding one document -- ``assumptions`` is its
    content digest, so the commit and expiry it was signed with are inside the
    identity -- to one static index.  Every assumed edge reads it, so a document
    that was never asserted against this index derives nothing.

``assumptions_closed(index, assumptions)``
    The reviewer's completeness witness: "this document enumerates every
    framework dispatch of this index."  Emitted only when the document says
    ``closed``, no row was enumerated unapplied, and the export's scope is the
    whole index (a slice cannot see the site it is missing).  It is the
    producer that can know it: nobody but the author of the document knows
    whether it is exhaustive.

``call_graph_closed_assumed(index, scope)``
    The call graph *with* the assumptions, over one scope token: the reviewer's
    closure, a census, and every unresolved call site in that scope discharged
    by a row for that exact site.  A residue row no assumption names is never
    discharged, and one such row withholds the witness for its scope.

WITHDRAWING ONE ROW
-------------------
Each reviewer-owned row is ``Evidence.kind == "assumption"``, so
``claims/assumptions.py`` gives it a run-independent ``asm:`` id, lists what it
carries, and can withdraw it.  What a withdrawal does depends on which witness
rests on what, and the two are deliberately different:

``call_graph_closed_assumed`` says *every unresolved site in this scope is
covered by a row*, so it depends on the rows that cover them and goes when one
of them goes.  Keeping it would leave a site nothing covers inside a closed call
graph, and its entity would read as dead.

``assumptions_closed`` is the reviewer's statement about the *document* -- "this
is every framework dispatch of this index" -- not about one row's truth, so it
stands.  That is what turns the newly uncovered site into
``static_assumed_site_undischarged`` and brings the entity back as
``static_entity_blocked_assumed``, naming the symbol the doubt re-enters
through, rather than into silence.

EXPIRY AND COMMIT
-----------------
A framework assumption is a statement about code at a moment.  The document
carries ``commit`` (what the reviewer signed against) and ``expires`` (the date
after which it must be re-reviewed); both are inside the digest, so a
certificate cannot be replayed against a document that has since moved, and an
expired document is refused by name rather than used.  Where the export carries
``scip_index_commit`` the two commits must agree or the document is refused;
where it does not, the binding is recorded and reported *unverified* rather
than treated as checked.

PRODUCER
--------
``framework-assumption``, its own class, distinct from ``scip`` (what an index
said), ``phpstan`` (what an analyser typed) and ``reviewer`` (architectural
intent over symbols).  A framework assumption is none of those three: it is a
claim about what a framework does with values at run time, and a row of it
wearing an indexer's class would be indistinguishable from something measured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..ir import Bundle, RelationDecl, bundle_from_json, digest
from . import closure, reflexion, scip_facts
from .combine import combine

PACK_NAME = "rules-static-framework-v1.json"
PACK_ID = "rules-static-framework-v1"
BASE_PACK_ID = "rules-static-v1"
CLOSURE_PACK_ID = "rules-static-closure-v1"
REFLEXION_PACK_ID = "rules-static-reflexion-v1"

#: Producer class of every row this module emits.
PRODUCER_CLASS = "framework-assumption"
EMITTER = "capcov.claims.static.framework"
#: Each row's emission contract, named in its evidence source.
CONTRACT_EDGE = "framework-edge-v1"
CONTRACT_UNAPPLIED = "framework-assumption-unapplied-v1"
CONTRACT_DESCRIBES = "assumptions-describe-index-v1"
CONTRACT_CLOSED = "assumptions-closed-v1"
WITNESS_CALL_GRAPH_ASSUMED = "call-graph-closed-assumed-v1"

EDGE_RELATION = "framework_edge"
UNAPPLIED_RELATION = "framework_assumption_unapplied"
DESCRIBES_RELATION = "assumptions_describe_index"
CLOSED_RELATION = "assumptions_closed"
CALL_GRAPH_CLOSED_RELATION = "call_graph_closed_assumed"

#: The document's schema version, carried in the file and checked here.
DOCUMENT_SCHEMA_VERSION = 1
#: What a ``source_tree_observed`` row emitted by this module says it is.
TREE_OBSERVATION_SOURCE = "framework-assumption claim-time observation of the indexed tree"

#: ``framework -> the mechanisms a row of it may name``.  Enumerated, never
#: open: these are the three dispatches this layer exists for, each one a thing
#: a reader can check against the framework's documented behaviour.
#:
#: ``net/http``  ``init-registry`` -- a package-level registry appended to by an
#:     ``init()`` and iterated at startup, the handler reached only as a value;
#:     ``mux-handler-value`` -- a handler passed to a mux as a value through a
#:     helper the index resolves to the helper and no further.
#: ``laravel``   ``container-bind`` / ``container-singleton`` -- a provider's
#:     ``bind``/``singleton`` whose implementation is a closure or a runtime
#:     value (a binding to a *class literal* is typed by Larastan and arrives as
#:     a ``larastan-container`` edge of the ``phpstan`` producer: it is measured,
#:     and re-declaring it here would put an assumption's class on a typed edge);
#:     ``facade-accessor`` -- a facade whose ``getFacadeAccessor`` resolves to a
#:     binding no analyser typed.
#: ``fastapi``   ``depends`` -- a dependency injected by ``Depends(...)``, whose
#:     call happens in the framework and not at the annotated site.
MECHANISMS = {
    "net/http": ("init-registry", "mux-handler-value"),
    "laravel": ("container-bind", "container-singleton", "facade-accessor"),
    "fastapi": ("depends",),
}

#: Reasons a row is enumerated instead of applied.
REASON_CO_LOCATED_RESIDUE = "co_located_residue"
REASON_NO_UNRESOLVED_SITE = "no_unresolved_site"
REASON_DOCUMENT_OUT_OF_SCOPE = "document_out_of_scope"


class AssumptionsInputError(ValueError):
    """The document, or the export it is asserted against, is not one this reads."""


class AssumptionsExpired(AssumptionsInputError):
    """The document's ``expires`` date has passed: it must be re-reviewed, not used."""


class MapCoverageUnsatisfied(reflexion.ReflexionInputError):
    """A closed capability map omits a symbol an assumed edge runs through.

    A ``ReflexionInputError``: the document at fault is the reviewer's map, and
    a caller that already treats a map/index mismatch as a usage refusal treats
    this one the same way.
    """


@dataclass(frozen=True)
class FrameworkAssumption:
    """One reviewed row: the edge, the framework, the mechanism, the site."""

    src: str
    dst: str
    framework: str
    mechanism: str
    path: str
    line: int

    @property
    def site(self) -> tuple[str, int]:
        return (self.path, self.line)

    @property
    def row(self) -> list[Any]:
        """The fact row's payload, in declared column order after ``index``."""
        return [self.src, self.dst, self.framework, self.mechanism, self.path, self.line]


@dataclass(frozen=True)
class AssumptionSet:
    """One signed document: its rows, its closure claim, and what binds it.

    ``digest`` is the content identity of the whole document -- rows, closure,
    reviewer, commit and expiry -- and is the ``assumptions`` column of
    ``assumptions_describe_index`` and ``assumptions_closed``.  Editing any of
    them changes it, so a certificate names the exact document it rests on.
    """

    rows: tuple[FrameworkAssumption, ...] = ()
    closed: bool = False
    reviewer: str = ""
    commit: str = ""
    expires: str = ""

    @property
    def document(self) -> dict[str, Any]:
        return {"assumptions": [list(row.row) for row in self.rows],
                "closed": self.closed, "commit": self.commit,
                "expires": self.expires, "reviewer": self.reviewer}

    @property
    def digest(self) -> str:
        return digest(self.document)

    @property
    def symbols(self) -> tuple[str, ...]:
        """Every symbol an assumed edge runs through, sorted."""
        return tuple(sorted({value for row in self.rows for value in (row.src, row.dst)}))

    @property
    def sites(self) -> frozenset[tuple[str, int]]:
        return frozenset(row.site for row in self.rows)


def load_pack() -> dict[str, Any]:
    """The framework rule pack document, read as package data (source tree or wheel)."""
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


def _iso_date(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise AssumptionsInputError(f"the assumptions document needs a {field!r} date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise AssumptionsInputError(
            f"the assumptions document's {field!r} must be an ISO date "
            f"(YYYY-MM-DD): {exc}") from exc
    return value


def assumptions_from_document(document: Any) -> AssumptionSet:
    """Read the reviewer's document, refusing anything it does not say clearly.

    ``{"schema_version": 1, "reviewer": str, "commit": str, "expires":
    "YYYY-MM-DD", "closed": bool, "assumptions": [{"src", "dst", "framework",
    "mechanism", "path", "line"}, ...]}``.  ``closed`` defaults to ``false``: a
    reviewer who has not said the set is complete has not said it, and every
    negation over the assumed graph stays unresolved.  Everything else is
    required -- an unsigned, undated, uncommitted assumption is not one.
    """
    if not isinstance(document, Mapping):
        raise AssumptionsInputError("the assumptions document must be a JSON object")
    allowed = {"schema_version", "reviewer", "commit", "expires", "closed", "assumptions"}
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise AssumptionsInputError(f"the assumptions document has unknown fields {unknown}")
    if document.get("schema_version") != DOCUMENT_SCHEMA_VERSION:
        raise AssumptionsInputError(
            f"the assumptions document must declare schema_version {DOCUMENT_SCHEMA_VERSION}")
    reviewer = document.get("reviewer")
    commit = document.get("commit")
    for value, field in ((reviewer, "reviewer"), (commit, "commit")):
        if not isinstance(value, str) or not value:
            raise AssumptionsInputError(
                f"the assumptions document needs a non-empty {field!r}: a framework "
                f"assumption is signed and bound to a commit, or it is not one")
    expires = _iso_date(document.get("expires"), "expires")
    closed = document.get("closed", False)
    if not isinstance(closed, bool):
        raise AssumptionsInputError("the assumptions document's 'closed' must be true or false")
    declared = document.get("assumptions")
    if not isinstance(declared, (list, tuple)) or not declared:
        raise AssumptionsInputError("the assumptions document needs a non-empty 'assumptions' list")
    rows = []
    fields = ("src", "dst", "framework", "mechanism", "path", "line")
    for entry in declared:
        if not isinstance(entry, Mapping) or set(entry) != set(fields):
            raise AssumptionsInputError(
                f"an assumption row is an object with exactly {list(fields)}")
        for field in fields[:-1]:
            if not isinstance(entry[field], str) or not entry[field]:
                raise AssumptionsInputError(
                    f"an assumption row's {field!r} must be a non-empty string")
        line = entry["line"]
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            raise AssumptionsInputError("an assumption row's 'line' must be a 1-based line number")
        framework, mechanism = entry["framework"], entry["mechanism"]
        if framework not in MECHANISMS:
            raise AssumptionsInputError(
                f"unknown framework {framework!r}; this layer enumerates "
                f"{', '.join(sorted(MECHANISMS))}")
        if mechanism not in MECHANISMS[framework]:
            raise AssumptionsInputError(
                f"unknown {framework} mechanism {mechanism!r}; enumerated mechanisms are "
                f"{', '.join(MECHANISMS[framework])}")
        rows.append(FrameworkAssumption(entry["src"], entry["dst"], framework, mechanism,
                                        entry["path"], line))
    return AssumptionSet(tuple(sorted(set(rows), key=lambda row: row.row)), bool(closed),
                         reviewer, commit, expires)


def load_assumptions(path: str | Path) -> AssumptionSet:
    """``assumptions_from_document`` over a file, naming the file that is wrong."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssumptionsInputError(f"cannot read {path}: {exc}") from exc
    return assumptions_from_document(document)


def require_unexpired(assumptions: AssumptionSet, today: date | None = None) -> None:
    """Refuse a document whose review has expired, naming both dates.

    An expired assumption is not a weaker assumption, it is one nobody has
    looked at since; using it would be reading stale evidence as current.
    """
    today = today or date.today()
    if date.fromisoformat(assumptions.expires) < today:
        raise AssumptionsExpired(
            f"the assumptions document expired on {assumptions.expires} (today is "
            f"{today.isoformat()}): re-review it and update 'expires', or drop "
            f"--assumptions for the resolved account alone")


def index_commit(export: Bundle) -> str | None:
    """The commit the export says it indexed, when it says one (``scip_index_commit``)."""
    for fact in export.facts:
        if fact.relation == "scip_index_commit":
            return str(fact.terms[1].value)
    return None


def require_commit_binding(export: Bundle, assumptions: AssumptionSet) -> bool:
    """Refuse a document signed against another commit; report whether it was checked.

    Returns ``True`` when the export named a commit and it matched, ``False``
    when the export named none -- in which case the binding is carried in the
    row's source and in the summary as *unverified*, never as checked.
    """
    commit = index_commit(export)
    if commit is None:
        return False
    if commit != assumptions.commit:
        raise AssumptionsInputError(
            f"the assumptions document is signed against commit {assumptions.commit!r} and "
            f"this index was taken at {commit!r}: a framework assumption is a statement "
            f"about one tree")
    return True


def unknown_symbols(export: Bundle, assumptions: AssumptionSet) -> tuple[str, ...]:
    """Assumed endpoints this index does not declare -- a stale or mistyped row."""
    known = reflexion.index_symbols(export)
    return tuple(symbol for symbol in assumptions.symbols if symbol not in known)


def require_mapped_assumptions(model: reflexion.CapabilityModel | None,
                               symbols: Iterable[str]) -> None:
    """Refuse a *closed* capability map that omits a symbol an assumed edge runs through.

    ``reflexion.model_bundle`` makes this check against ``scip_may_reference``,
    which cannot see an endpoint that exists only because of an assumption.  An
    omitted one fails to lift the assumed edge and then reports the reviewer's
    own model edge as ``static_absence_assumed`` -- a claim that the code lacks
    an edge this bundle demonstrably carries.  An open map licenses no negation
    and is free to be partial.
    """
    if model is None or not model.closed:
        return
    mapped = frozenset(model.symbols)
    unmapped = tuple(sorted(symbol for symbol in symbols if symbol not in mapped))
    if not unmapped:
        return
    raise MapCoverageUnsatisfied(
        f"the capability map declares closure but does not map {len(unmapped)} "
        f"symbol(s) an assumed framework edge runs through: "
        f"{', '.join(unmapped[:5])}" + (" ..." if len(unmapped) > 5 else ""))


def co_located_residue_sites(ast_raw: Mapping[str, Any]) -> frozenset[tuple[str, int]]:
    """``(path, line)`` the census gives more than one unresolved callee for.

    ``static_assumed_site_discharged`` joins the residue to the reviewed row on
    ``(path, line)`` alone -- the residue's callee is the census's column, not
    the reviewer's -- so a line carrying two unresolved calls, only one of them
    the framework's, would have both discharged by the one row.  Naming those
    sites is what lets :func:`assumptions_bundle` apply none of them.
    """
    seen: dict[tuple[str, int], set[str]] = {}
    for path, line, callee in closure.residue_rows(ast_raw):
        seen.setdefault((path, line), set()).add(callee)
    return frozenset(site for site, callees in seen.items() if len(callees) > 1)


def unapplied_reason(row: FrameworkAssumption, *, residue: Mapping[tuple[str, int], int],
                     co_located: frozenset[tuple[str, int]],
                     in_scope: frozenset[str]) -> str | None:
    """Why this row cannot be applied, or ``None`` when it can."""
    if row.path not in in_scope:
        return REASON_DOCUMENT_OUT_OF_SCOPE
    if row.site not in residue:
        return REASON_NO_UNRESOLVED_SITE
    if row.site in co_located:
        return REASON_CO_LOCATED_RESIDUE
    return None


def assumptions_bundle(export: Bundle, ast_raw: Mapping[str, Any], assumptions: AssumptionSet, *,
                       model: reflexion.CapabilityModel | None = None,
                       tree_digest: str | None = None,
                       today: date | None = None) -> Bundle:
    """The fragment: the reviewed rows, what could not be applied, both witnesses.

    Built against a finished ``scip_facts`` export (its identity, its scope and
    its in-scope documents) and returned *unvalidated* -- its evidence depends
    on the export's own ``scip_index`` rows, so it is a fragment of that bundle
    and :func:`attach` is what validates the whole.  ``ast_raw`` is the
    resolver's raw dict, read for the residue rows exactly as ``closure`` reads
    them, so both modules count the same census.

    ``tree_digest`` adds the claim-time ``source_tree_observed`` row that
    ``static_index_current`` -- and so ``static_capability_op_assumed`` -- rests
    on.  ``reflexion.model_bundle`` and ``cha.cha_bundle`` emit the same row, so
    a caller merging several fragments passes it to exactly one of them.
    """
    require_unexpired(assumptions, today)
    commit_verified = require_commit_binding(export, assumptions)
    missing = unknown_symbols(export, assumptions)
    if missing:
        raise AssumptionsInputError(
            f"the assumptions document names {len(missing)} symbol(s) this index does not "
            f"declare: {', '.join(missing[:5])}" + (" ..." if len(missing) > 5 else ""))
    metadata = closure._metadata(export)
    index = str(metadata["index_digest"])
    decls = relation_decls()
    depends_on = tuple(sorted(
        record.id for record in export.evidence
        if record.atom.relation in ("scip_index", "scip_index_tree")))
    if not depends_on:
        raise AssumptionsInputError("the export declares no scip_index evidence to depend on")
    document_digest = assumptions.digest
    signature = (f"{assumptions.reviewer} commit:{assumptions.commit} "
                 f"expires:{assumptions.expires}")

    facts, evidence = [], []

    def emit(relation: str, row: list[Any], source: str, *, kind: str = "fact",
             rests_on: Iterable[str] = ()) -> str:
        facts.append(closure._atom(decls[relation], relation, row))
        record = _evidence(decls[relation], relation, row, index, source,
                           tuple(depends_on) + tuple(rests_on), kind=kind)
        evidence.append(record)
        return record.id

    def add(relation: str, values: list[Any], source: str, *, kind: str = "fact",
            rests_on: Iterable[str] = ()) -> str:
        """Emit an index-scoped row: every relation here but the compatibility one."""
        return emit(relation, [index, *values], source, kind=kind, rests_on=rests_on)

    residue: dict[tuple[str, int], int] = {}
    for path, line, _callee in closure.residue_rows(ast_raw):
        residue[(path, line)] = residue.get((path, line), 0) + 1
    co_located = co_located_residue_sites(ast_raw)
    in_scope = frozenset(metadata["in_scope_documents"])

    applied: list[FrameworkAssumption] = []
    unapplied: list[tuple[FrameworkAssumption, str]] = []
    for row in assumptions.rows:
        reason = unapplied_reason(row, residue=residue, co_located=co_located, in_scope=in_scope)
        (applied.append(row) if reason is None else unapplied.append((row, reason)))

    # Refuse before a row is emitted: an assumed edge running through a symbol a
    # CLOSED map omits would lift incompletely and read as an absence in code
    # this bundle shows the edge for.
    require_mapped_assumptions(
        model, {value for row in applied for value in (row.src, row.dst)})

    reviewed_source = f"{PRODUCER_CLASS} {signature} {CONTRACT_EDGE} {document_digest}"
    covered: dict[tuple[str, int], list[str]] = {}
    for row in applied:
        covered.setdefault(row.site, []).append(
            add(EDGE_RELATION, row.row, reviewed_source, kind="assumption"))
    for row, reason in unapplied:
        add(UNAPPLIED_RELATION, [row.path, row.line, row.src, row.dst, reason],
            f"{PRODUCER_CLASS} {EMITTER} {CONTRACT_UNAPPLIED}")

    # The compatibility witness and the closure are the reviewer's, and they
    # depend on the INDEX and not on the edge rows: withdrawing one edge must
    # leave the closure standing, so the site it used to cover comes back as
    # undischarged rather than as nothing at all.
    describes_id = emit(DESCRIBES_RELATION, [document_digest, index],
                        f"{PRODUCER_CLASS} {signature} {CONTRACT_DESCRIBES} "
                        f"{document_digest}",
                        kind="assumption")
    scope_kind = dict(metadata["scope"]).get("kind")
    closed = bool(assumptions.closed) and not unapplied and scope_kind == scip_facts.SCOPE_ALL
    if closed:
        add(CLOSED_RELATION, [document_digest],
            f"{PRODUCER_CLASS} {signature} {CONTRACT_CLOSED} {document_digest}",
            kind="assumption")

    closed_tokens: list[str] = []
    if closed and metadata["census_available"]:
        undischarged = {site for site in residue if site not in covered}
        witness_source = f"{PRODUCER_CLASS} {EMITTER} {WITNESS_CALL_GRAPH_ASSUMED}"
        tokens = closure.scope_tokens(dict(metadata["scope"]), metadata["in_scope_documents"])
        for token, documents in sorted(tokens.items()):
            if any(path in documents for path, _ in undischarged):
                continue
            # The witness is "every unresolved site in this scope is covered by
            # a reviewed row of THIS document for THIS index", so it rests on
            # those rows AND on the binding: withdrawing one must take the
            # witness with it, or a site nothing covers any more would still be
            # inside a closed call graph and its entity would read as dead.
            add(CALL_GRAPH_CLOSED_RELATION, [token], witness_source,
                rests_on=[describes_id,
                          *(eid for site, ids in covered.items() if site[0] in documents
                            for eid in ids)])
            closed_tokens.append(token)

    if tree_digest is not None:
        from . import pilot

        export_decls = {decl.name: decl for decl in export.relations}
        if "source_tree_observed" not in export_decls:
            raise AssumptionsInputError(
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
                            ("assumptions_digest", document_digest),
                            ("reviewer", assumptions.reviewer),
                            ("commit", assumptions.commit),
                            ("commit_verified", commit_verified),
                            ("expires", assumptions.expires),
                            ("applied_rows", len(applied)),
                            ("unapplied_rows", len(unapplied)),
                            ("assumptions_closed", closed),
                            ("call_graph_closed_assumed", tuple(closed_tokens))))


def _evidence(decl: RelationDecl, relation: str, row: list[Any], index: str,
              source: str, depends_on: tuple[str, ...], *, kind: str = "fact"):
    from ..ir import Context, Evidence

    atom = closure._atom(decl, relation, row)
    context = {column.name: value for column, value in zip(decl.columns, row) if column.context}
    return Evidence(scip_facts.evidence_id(index, relation, row), atom,
                    Context.from_mapping(context), source, tuple(depends_on), kind=kind)


def assumption_ids(bundle: Bundle) -> dict[str, str]:
    """``evidence id -> asm: id`` for every reviewed row of this fragment.

    Contract A1 from ``claims/assumptions.py``, applied here so a caller can
    report which assumptions a ``*_assumed`` row rests on without importing the
    registry: the id is run-independent, so the same signed row keeps the same
    id across runs and across exports of the same index.
    """
    from ..assumptions import assumption_id, assumption_records

    return {record.id: assumption_id(record) for record in assumption_records(bundle)
            if record.source.split(" ", 1)[0] == PRODUCER_CLASS}


def attach(export: Bundle, ast_raw: Mapping[str, Any], assumptions: AssumptionSet, *bundles: Bundle,
           model: reflexion.CapabilityModel | None = None, tree_digest: str | None = None,
           today: date | None = None, validate: bool = True, **combine_kwargs: Any) -> Bundle:
    """``export`` plus the assumption fragment (plus any further bundles), validated.

    The base pack is what derives ``static_edge`` and ``static_route_handler``,
    and the closure fragment is what carries the residue rows this pack's
    discharge rules read; both are merged by the caller in ``bundles``, exactly
    as ``cha.attach`` expects them.
    """
    return combine(export,
                   assumptions_bundle(export, ast_raw, assumptions, model=model,
                                      tree_digest=tree_digest, today=today),
                   *bundles, validate=validate, **combine_kwargs)


__all__ = ["PACK_NAME", "PACK_ID", "BASE_PACK_ID", "CLOSURE_PACK_ID", "REFLEXION_PACK_ID",
           "PRODUCER_CLASS", "EMITTER", "CONTRACT_EDGE", "CONTRACT_UNAPPLIED",
           "CONTRACT_DESCRIBES", "CONTRACT_CLOSED", "WITNESS_CALL_GRAPH_ASSUMED",
           "EDGE_RELATION", "UNAPPLIED_RELATION", "DESCRIBES_RELATION", "CLOSED_RELATION",
           "CALL_GRAPH_CLOSED_RELATION", "DOCUMENT_SCHEMA_VERSION", "TREE_OBSERVATION_SOURCE",
           "MECHANISMS", "REASON_CO_LOCATED_RESIDUE", "REASON_NO_UNRESOLVED_SITE",
           "REASON_DOCUMENT_OUT_OF_SCOPE", "AssumptionsInputError", "AssumptionsExpired",
           "MapCoverageUnsatisfied", "FrameworkAssumption", "AssumptionSet", "load_pack",
           "pack_relations", "pack_bundle", "relation_decls", "assumptions_from_document",
           "load_assumptions", "require_unexpired", "index_commit", "require_commit_binding",
           "unknown_symbols", "require_mapped_assumptions", "co_located_residue_sites",
           "unapplied_reason", "assumptions_bundle", "assumption_ids", "attach"]
