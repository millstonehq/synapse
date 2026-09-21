"""``capcov experiment claims vectors-static``: the static parity precheck.

``capcov.vectors`` records what the incumbent did at a boundary operation and
replays it against a candidate; a static bundle (``capcov experiment claims
static --static scip --out BUNDLE.json``, with the rule packs merged) accounts
for what the candidate's *code* can reach before any run.  This module joins
the two into **one** bundle and judges it with the kernel the caller selected,
so a store the candidate wrote and a store its routes can reach are compared
by the same kernel, with one certificate set, and with each side's rows still
owned by the producer that could know them.

WHAT BINDS THEM
---------------
``index_describes_candidate(index, run, candidate_sha256)``.  A static bundle is
a statement about a *tree*; a replay artifact is a statement about a *binary*
identified by ``candidate_sha256``.  Nothing in either document binds the two:
the replay never saw the index and the indexer never saw the build.  Somebody
has to say so, and saying so is a judgement, not an observation -- so the
witness is ``reviewer``-classed, asserted explicitly (``--describes-candidate``)
and refused outright when it names a digest the replay did not declare.  Without
it nothing below derives: the divergence claim is *unresolved*, which is the
honest verdict for "these two documents may be about different binaries".

It carries ``run`` as well as ``index`` because every rule here joins static
rows to runtime rows, and this repository's validator requires such a join to
carry an exact typed index/run compatibility witness
(``validation._validate_context_joins``).  The run is the replay's own
``run_id``; the recording it replayed is bound to it by
``vector_run_recording``, whose identity ``claims.build_bundle`` has already
checked (``replay.vectors_sha256`` is the digest of the exact vectors artifact).

THE TWO SIDES, AND WHO OWNS WHICH ROW
-------------------------------------
``vector_store_changed(run, operation, cell, table)`` [replay]
    A table the **candidate** wrote while replaying one cell.  Emitted only for
    a cell whose replay *passed*: a pass is the comparison policy's statement
    that the candidate's delta equalled the recorded one, so the recorded
    delta's tables are the candidate's tables.  For a failed cell the delta may
    be exactly what differed, so nothing is emitted -- and nothing is dropped
    either: ``vector_replay_failed`` already enumerates those cells, and they
    withhold the completeness witness below.

``vector_store_uncompared(run, operation, cell, table)`` [replay]
    A table the recording saw change that the comparison policy did not compare
    (the operation's ``informational`` list, or a table outside its ``declared``
    set).  A pass says nothing about it.  Enumerated rather than dropped, and it
    withholds the witness too.

``vector_operation_surface(run, operation, surface)`` [recorder]
    The route surface id of the operation, read from the recorder's own
    ``operation_record`` in ``vectors.json`` -- ``http:<METHOD> <prefix><path>``,
    the spelling the route adapter gives a surface.  An operation whose request
    is not an HTTP route yields no row and is named in the document instead.

``vector_stores_closed(run, operation)`` [replay]
    The completeness witness the *unexercised* negation is licensed by, and the
    only one this module emits.  It says: every required cell of this operation
    produced a vector, every one of them replayed and passed, the recording
    compared **every** table (``declared_stores`` is ``"*"``), and no change was
    left uncompared.  Anything less and the candidate's write set is a lower
    bound, so "no cell wrote that table" would be a silence.

The static side is borrowed from the bundle byte-for-byte and re-derived here by
the selected kernel: ``static_route_no_table`` (the closure pack's own negation,
already gated on ``call_graph_closed``) and ``static_route_reaches_table``.

WHAT IS DERIVED
---------------
``vector_store_divergence(index, run, operation, table)`` -- a **claim**, and a
negative-polarity one: deriving it *refutes* the parity precheck for that store.
It is exactly "the candidate wrote a table that the route's closed store set
does not contain":

    vector_store_divergence(IX, Run, Op, T) :-
        vector_store_changed(Run, Op, Cell, T),
        vector_operation_surface(Run, Op, S),
        vector_run_recording(Run, Rec, C),
        index_describes_candidate(IX, Run, C),
        static_route_no_table(IX, S, T).

There is no negation in that rule.  The negation lives in
``static_route_no_table``, which the closure pack derives only under
``call_graph_closed`` over the export's own scope -- so "REFUTED only under
closure and the witness" is not a convention this module applies, it is the
shape of the premise.  Drop either and the claim is unresolved, with the
missing premise named.  A table the index's own entity census never saw has no
``static_table`` row and therefore no ``static_route_no_table`` row: the
document lists it as ``unindexed`` rather than calling it a divergence, because
a census that never saw a table did not say the route cannot reach it.

``static_store_unexercised(index, run, operation, table)`` -- **advisory, never a
gate**: a store the route statically reaches that no recorded cell wrote.
``retry`` and ``invalid-input`` cells are supposed to write nothing, so this is
a coverage hint for the recorder, not a finding about the candidate.  It is
still licensed like any negation: the replay producer's ``vector_stores_closed``
completes ``vector_store_touched``, the cell-projected form of what was written.

Nothing here is an outcome and no static row moves a vector's verdict: a static
path is not a run.  ``vector_matches`` and ``vector_cell_recorded`` are exactly
the claims ``vectors.claims`` already builds, judged unchanged beside these.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .. import artifacts
from ..claims.ir import (Atom, Bundle, Claim, Column, Constant, Context, Evidence,
                         RelationDecl, Rule, Variable, digest)
from ..claims.static.combine import CombineError, combine
from ..claims.static.join import (KERNEL, StaticBundle, StaticBundleError, closure,
                                  derivable_relations, load)
from . import claims as vector_claims
from .claims import RECORDER_PRODUCER, REPLAY_PRODUCER, VectorClaimError
from .recorder import REPLAY_FILE, VECTORS_FILE, VECTORS_KIND, op_id_of, read_vectors
from .replay import read_replay
from .schema import ReplayArtifact, VectorsArtifact

#: The producer class of the witness that binds an index to a candidate binary.
REVIEWER_PRODUCER = "reviewer"

DESCRIBES_RELATION = "index_describes_candidate"
RUN_RECORDING_RELATION = "vector_run_recording"
OPERATION_SURFACE_RELATION = "vector_operation_surface"
STORE_CHANGED_RELATION = "vector_store_changed"
STORE_UNCOMPARED_RELATION = "vector_store_uncompared"
STORE_TOUCHED_RELATION = "vector_store_touched"
STORES_CLOSED_RELATION = "vector_stores_closed"
DIVERGENCE_RELATION = "vector_store_divergence"
UNEXERCISED_RELATION = "static_store_unexercised"

#: Borrowed from the static bundle byte-for-byte, never re-declared here: a
#: local copy that drifted by one column would silently stop joining.
NO_TABLE_RELATION = "static_route_no_table"
REACHES_TABLE_RELATION = "static_route_reaches_table"
BORROWED_RELATIONS = (NO_TABLE_RELATION, REACHES_TABLE_RELATION)

#: The surface id prefix the route adapter gives an HTTP route.
HTTP_SURFACE_PREFIX = "http:"
#: The one driver whose request is a route template this join can spell as a
#: surface id.  Every other driver (shell, webhook, form post) is named in the
#: document instead: a surface id guessed from a request that is not a route is
#: a join key nothing on the static side ever declared.
HTTP_DRIVER = "http"
#: The recorded delta's key prefixes, and the store kind each stands for.  Both
#: reduce to the bare name: the static entity census names a table, not a store
#: kind, so ``rows.notes`` and ``collections.notes`` are the same ``notes``.
DELTA_PREFIXES = ("rows.", "collections.")
#: ``declared_stores`` that compares every table.  Anything else compares a
#: subset, and a subset cannot close what the candidate wrote.
DECLARED_ALL = "*"


class VectorStaticError(ValueError):
    """The artifacts and the bundle cannot safely be joined, in its own words.

    A usage error about the command line -- exit 2 -- never a verdict about the
    candidate and never a finding about the code.
    """


@dataclass(frozen=True)
class OperationPair:
    """One operation's recorded vectors, its replay, and the surface it drives."""

    operation: str
    vectors: VectorsArtifact
    replay: ReplayArtifact
    surface: str | None
    surface_reason: str

    @property
    def run(self) -> str:
        return str(self.replay.run_id)

    @property
    def recording(self) -> str:
        return vector_claims.artifact_digest(self.vectors)

    @property
    def candidate(self) -> str:
        return str(self.replay.candidate_sha256)


def operation_surface(record: Mapping[str, Any] | None) -> tuple[str | None, str]:
    """The route surface id of a recorded operation, or why there is none.

    ``operation_record`` is what ``recorder.write_vectors`` puts in the artifact:
    the consumer's own ``Operation``.  The ``http`` driver's request describes a
    route template (``{id}`` placeholders) and an optional ``prefix``, which is
    exactly how the route adapter spells a surface id, so the join key is that
    spelling and nothing is guessed.  Every other driver -- a shell helper, a
    queue drain, a webhook -- has no route surface, and this says so rather than
    inventing one.
    """
    if not isinstance(record, Mapping):
        return None, "the vectors artifact carries no operation_record"
    request = record.get("request")
    if not isinstance(request, Mapping):
        return None, "the operation record carries no request"
    driver = record.get("driver")
    if driver != HTTP_DRIVER:
        return None, (f"the operation is driven by {driver!r}, not the {HTTP_DRIVER!r} route "
                      f"driver, so it names no route surface")
    method = request.get("method")
    path = request.get("path") or request.get("uri")
    if not isinstance(method, str) or not method or not isinstance(path, str) or not path:
        return None, "the operation request names no method and path"
    prefix = request.get("prefix") or ""
    if not isinstance(prefix, str):
        return None, "the operation request prefix is not a string"
    return f"{HTTP_SURFACE_PREFIX}{method.upper()} {prefix}{path}", ""


def _table_of(key: str) -> str | None:
    for prefix in DELTA_PREFIXES:
        if key.startswith(prefix) and len(key) > len(prefix):
            return key[len(prefix):]
    return None


def changed_tables(vector) -> tuple[str, ...]:
    """The tables the recording compared and saw change for this vector."""
    delta = vector.expected.get("delta") if isinstance(vector.expected, Mapping) else None
    if not isinstance(delta, Mapping):
        return ()
    return tuple(sorted({table for key in delta if (table := _table_of(key)) is not None}))


def uncompared_tables(vector) -> tuple[str, ...]:
    """The tables that changed and were *not* compared: informational, or undeclared."""
    information = (vector.expected.get("informational")
                   if isinstance(vector.expected, Mapping) else None)
    if not isinstance(information, Mapping):
        return ()
    return tuple(sorted({table for key in information
                         if (table := _table_of(key)) is not None}))


def _read_pair(vectors_dir: Path, replay_dir: Path, operation_dir: str) -> OperationPair:
    vectors_path = vectors_dir / operation_dir / VECTORS_FILE
    replay_path = replay_dir / operation_dir / REPLAY_FILE
    try:
        document = artifacts.read(vectors_path, expect_kind=VECTORS_KIND)
        vectors = read_vectors(vectors_path)
        replay = read_replay(replay_path)
    except SystemExit as exc:  # artifacts.read refuses the wrong kind this way
        raise VectorStaticError(str(exc)) from exc
    except (OSError, ValueError, KeyError) as exc:
        raise VectorStaticError(
            f"cannot read the artifacts for {op_id_of(Path(operation_dir))!r}: {exc}") from exc
    surface, reason = operation_surface(document.get("operation_record"))
    return OperationPair(vectors.operation, vectors, replay, surface, reason)


def read_pairs(vectors_dir: str | Path, replay_dir: str | Path) -> tuple[OperationPair, ...]:
    """Every operation both directories hold, refusing a set that does not line up.

    A replay without its recording, or a recording nothing replayed, is named
    rather than skipped: judging the intersection would quietly shrink the
    denominator, which is the one thing a vectors artifact exists to keep.
    """
    vectors_dir, replay_dir = Path(vectors_dir), Path(replay_dir)
    for directory, what in ((vectors_dir, "--vectors"), (replay_dir, "--replay")):
        if not directory.is_dir():
            raise VectorStaticError(f"{what} {str(directory)!r} is not a directory")
    recorded = {path.parent.name for path in sorted(vectors_dir.glob(f"*/{VECTORS_FILE}"))}
    replayed = {path.parent.name for path in sorted(replay_dir.glob(f"*/{REPLAY_FILE}"))}
    if not recorded:
        raise VectorStaticError(
            f"--vectors {str(vectors_dir)!r} holds no <operation>/{VECTORS_FILE}")
    missing = sorted(op_id_of(Path(name)) for name in recorded - replayed)
    extra = sorted(op_id_of(Path(name)) for name in replayed - recorded)
    if missing or extra:
        raise VectorStaticError(
            "the vectors and replay directories do not name the same operations: "
            + "; ".join(filter(None, [
                f"recorded but not replayed: {', '.join(missing)}" if missing else "",
                f"replayed but not recorded: {', '.join(extra)}" if extra else ""])))
    return tuple(_read_pair(vectors_dir, replay_dir, name) for name in sorted(recorded))


def _column_names(decl: RelationDecl) -> list[str]:
    return [column.name for column in decl.columns]


def borrow(static: StaticBundle, names: Iterable[str] = BORROWED_RELATIONS) -> dict[str, RelationDecl]:
    """The static bundle's own declarations for ``names``, or a named refusal."""
    declared = {decl.name: decl for decl in static.bundle.relations}
    missing = [name for name in names if name not in declared]
    if missing:
        raise VectorStaticError(
            f"the static bundle declares no {', '.join(missing)}: export it with the "
            f"closure rule pack merged (capcov experiment claims static --static scip), "
            f"or there is no closed store set to compare a recorded write with")
    return {name: declared[name] for name in names}


def relations(borrowed: Mapping[str, RelationDecl]) -> tuple[RelationDecl, ...]:
    """Every relation the fragment declares: the borrowed pair plus this join's own."""
    joined = tuple(sorted({*BORROWED_RELATIONS, STORE_CHANGED_RELATION, STORE_TOUCHED_RELATION,
                           OPERATION_SURFACE_RELATION, RUN_RECORDING_RELATION}))
    run = Column("run", "symbol", True)
    operation = Column("operation", "symbol", True)
    return (
        *(borrowed[name] for name in BORROWED_RELATIONS),
        RelationDecl(DESCRIBES_RELATION,
                     (Column("index", "digest", True), run,
                      Column("candidate_sha256", "digest")),
                     modality="compatibility", binding="runtime", primitive=True,
                     producer_classes=(REVIEWER_PRODUCER,),
                     context_indices=("index", "run"),
                     compatibility_targets=joined,
                     compatibility_context_indices=("index", "run")),
        RelationDecl(RUN_RECORDING_RELATION,
                     (run, Column("recording", "digest"), Column("candidate_sha256", "digest")),
                     modality="observation", binding="runtime", primitive=True,
                     producer_classes=(REPLAY_PRODUCER,), context_indices=("run",)),
        RelationDecl(OPERATION_SURFACE_RELATION,
                     (run, operation, Column("surface", "symbol")),
                     modality="observation", binding="runtime", primitive=True,
                     producer_classes=(RECORDER_PRODUCER,),
                     context_indices=("run", "operation")),
        RelationDecl(STORE_CHANGED_RELATION,
                     (run, operation, Column("cell", "symbol"), Column("table", "symbol")),
                     modality="observation", binding="runtime", primitive=True,
                     producer_classes=(REPLAY_PRODUCER,),
                     context_indices=("run", "operation")),
        RelationDecl(STORE_UNCOMPARED_RELATION,
                     (run, operation, Column("cell", "symbol"), Column("table", "symbol")),
                     modality="observation", binding="runtime", primitive=True,
                     producer_classes=(REPLAY_PRODUCER,),
                     context_indices=("run", "operation")),
        RelationDecl(STORE_TOUCHED_RELATION,
                     (run, operation, Column("table", "symbol")),
                     modality="derived", binding="runtime", primitive=False,
                     context_indices=("run", "operation")),
        RelationDecl(STORES_CLOSED_RELATION, (run, operation),
                     modality="completeness", binding="runtime", primitive=True,
                     producer_classes=(REPLAY_PRODUCER,),
                     context_indices=("run", "operation"),
                     completes=STORE_TOUCHED_RELATION),
        RelationDecl(DIVERGENCE_RELATION,
                     (Column("index", "digest"), run, operation, Column("table", "symbol")),
                     modality="claim", polarity="negative", binding="runtime", primitive=False,
                     context_indices=("run", "operation")),
        RelationDecl(UNEXERCISED_RELATION,
                     (Column("index", "digest"), run, operation, Column("table", "symbol")),
                     modality="derived", binding="runtime", primitive=False,
                     context_indices=("run", "operation")),
    )


def rules() -> tuple[Rule, ...]:
    """The three rules: the cell projection, the divergence, and the advisory."""
    ix, run, op = Variable("IX"), Variable("Run"), Variable("Op")
    cell, table, surface = Variable("Cell"), Variable("T"), Variable("S")
    recording, candidate = Variable("Rec"), Variable("C")
    binding = (Atom(OPERATION_SURFACE_RELATION, (run, op, surface)),
               Atom(RUN_RECORDING_RELATION, (run, recording, candidate)),
               Atom(DESCRIBES_RELATION, (ix, run, candidate)))
    return (
        Rule(Atom(STORE_TOUCHED_RELATION, (run, op, table)),
             (Atom(STORE_CHANGED_RELATION, (run, op, cell, table)),),
             "vector_store_touched_in_some_cell"),
        Rule(Atom(DIVERGENCE_RELATION, (ix, run, op, table)),
             (Atom(STORE_CHANGED_RELATION, (run, op, cell, table)), *binding,
              Atom(NO_TABLE_RELATION, (ix, surface, table))),
             "vector_store_divergence_outside_the_closed_store_set"),
        Rule(Atom(UNEXERCISED_RELATION, (ix, run, op, table)),
             (*binding, Atom(REACHES_TABLE_RELATION, (ix, surface, table)),
              Atom(STORES_CLOSED_RELATION, (run, op)),
              Atom(STORE_TOUCHED_RELATION, (run, op, table), negated=True)),
             "static_store_unexercised_by_a_closed_cell_set"),
    )


def _atom(decl: RelationDecl, values: tuple[str, ...]) -> Atom:
    return Atom(decl.name, tuple(Constant(value, column.type)
                                 for value, column in zip(values, decl.columns)))


def _record(decl: RelationDecl, values: tuple[str, ...], source: str, *,
            depends_on: Iterable[str] = (), kind: str = "assumption") -> tuple[Atom, Evidence]:
    atom = _atom(decl, values)
    names = _column_names(decl)
    context = Context.from_mapping({name: values[names.index(name)]
                                    for name in decl.context_indices})
    identity = digest({"relation": decl.name, "row": list(values), "source": source})
    return atom, Evidence(f"ev:vector-static:{identity}", atom, context, source,
                          tuple(depends_on), kind=kind)


def _pass_evidence(pair_bundle: Bundle) -> dict[str, str]:
    """Per cell, the id of the replay evidence that says that cell passed.

    Every row this module emits about what the candidate wrote depends on one of
    these: the pass *is* the statement that the candidate's delta equalled the
    recording's, so a certificate for a divergence names the replay record it
    rests on rather than asserting the write on its own authority.
    """
    return {record.atom.terms[3].value: record.id for record in pair_bundle.evidence
            if record.atom.relation == "vector_replay_passed"}


@dataclass(frozen=True)
class ClosureReport:
    """Why an operation's written-store set is (not) closed, in the producer's words."""

    closed: bool
    reasons: tuple[str, ...]


def stores_closed(pair: OperationPair) -> ClosureReport:
    """Whether the replay producer can close what the candidate wrote for this operation.

    Four things have to hold, and each failure is named rather than folded into
    a bare ``false``: no recording gap (a cell that never ran could have written
    anything), no failed cell (a failure may be the delta itself), a recording
    that compared every table, and no change left uncompared.
    """
    reasons: list[str] = []
    if pair.vectors.gaps:
        reasons.append(f"{len(pair.vectors.gaps)} recorded gap(s): "
                       f"{', '.join(sorted(str(item.get('cell')) for item in pair.vectors.gaps))}")
    failed = sorted(result.id for result in pair.replay.results if not result.passed)
    if failed:
        reasons.append(f"{len(failed)} cell(s) did not replay: {', '.join(failed)}")
    if pair.vectors.declared_stores != DECLARED_ALL:
        reasons.append(f"the recording declared a store subset, not {DECLARED_ALL!r}")
    uncompared = sorted({table for vector in pair.vectors.vectors
                         for table in uncompared_tables(vector)})
    if uncompared:
        reasons.append(f"{len(uncompared)} table(s) changed uncompared: {', '.join(uncompared)}")
    return ClosureReport(not reasons, tuple(reasons))


def fragment(pairs: Iterable[OperationPair], pair_bundles: Mapping[str, Bundle], *,
             index: str, borrowed: Mapping[str, RelationDecl],
             describes_candidate: str | None) -> Bundle:
    """The join fragment: the runtime rows, the reviewer witness, and the rules."""
    decls = {decl.name: decl for decl in relations(borrowed)}
    facts: list[Atom] = []
    evidence: list[Evidence] = []
    claims: list[Claim] = []
    seen: set[tuple] = set()

    def add(relation: str, values: tuple[str, ...], source: str, **kwargs) -> None:
        if (relation, values) in seen:
            return
        seen.add((relation, values))
        atom, record = _record(decls[relation], values, source, **kwargs)
        facts.append(atom)
        evidence.append(record)

    for pair in pairs:
        replay_source = f"{REPLAY_PRODUCER} {digest(pair.replay.to_json())}"
        recorder_source = f"{RECORDER_PRODUCER} {pair.recording}"
        passes = _pass_evidence(pair_bundles[pair.operation])
        add(RUN_RECORDING_RELATION, (pair.run, pair.recording, pair.candidate), replay_source)
        if pair.surface is not None:
            add(OPERATION_SURFACE_RELATION, (pair.run, pair.operation, pair.surface),
                recorder_source)
        results = {result.id: result for result in pair.replay.results}
        written: set[str] = set()
        for vector in pair.vectors.vectors:
            depends = [passes[vector.cell]] if vector.cell in passes else []
            for table in uncompared_tables(vector):
                add(STORE_UNCOMPARED_RELATION, (pair.run, pair.operation, vector.cell, table),
                    replay_source, depends_on=depends)
            if not results[vector.id].passed:
                continue
            for table in changed_tables(vector):
                add(STORE_CHANGED_RELATION, (pair.run, pair.operation, vector.cell, table),
                    replay_source, depends_on=depends)
                written.add(table)
        if stores_closed(pair).closed:
            add(STORES_CLOSED_RELATION, (pair.run, pair.operation), replay_source)
        if describes_candidate is not None:
            add(DESCRIBES_RELATION, (index, pair.run, pair.candidate),
                f"{REVIEWER_PRODUCER} capcov.vectors.static_join "
                f"index-describes-candidate-v1 {index}")
        for table in sorted(written):
            values = (index, pair.run, pair.operation, table)
            claims.append(Claim(DIVERGENCE_RELATION, _atom(decls[DIVERGENCE_RELATION], values).terms,
                                Context.from_mapping({"run": pair.run, "operation": pair.operation}),
                                id=f"vector-store-divergence:{digest(list(values))}"))
    return Bundle(tuple(decls.values()), facts=tuple(facts), rules=rules(), claims=tuple(claims),
                  evidence=tuple(evidence),
                  metadata=(("emitter", "capcov.vectors.static_join"),
                            ("index_digest", index),
                            ("operations", len(tuple(pairs))),
                            ("producer_authority", "local-unattested")))


def index_of(static: StaticBundle) -> str:
    """The one index this bundle is about; more than one is more than one join."""
    indexes = sorted({fact.terms[0].value for fact in static.bundle.facts
                      if fact.relation == "scip_index"})
    if len(indexes) != 1:
        raise VectorStaticError(
            f"the static bundle is about {len(indexes)} index(es); a parity precheck "
            f"against more than one index is more than one precheck -- export one "
            f"bundle per index")
    return indexes[0]


def build_bundle(pairs: Iterable[OperationPair], static: StaticBundle, *,
                 describes_candidate: str | None) -> Bundle:
    """One bundle: every vectors/replay pair, the static account, and the join.

    ``describes_candidate`` is the reviewer's assertion that this index describes
    the replayed binary.  It must equal what every replay declared: a witness
    naming another digest is not a witness about this run, and quietly ignoring
    the mismatch is how a bundle for one binary judges another.
    """
    pairs = tuple(pairs)
    if not pairs:
        raise VectorStaticError("no operation to join")
    index = index_of(static)
    borrowed = borrow(static)
    if describes_candidate is not None:
        wrong = sorted({pair.operation for pair in pairs
                        if pair.candidate != describes_candidate})
        if wrong:
            raise VectorStaticError(
                f"--describes-candidate names {describes_candidate[:12]}..., which is not the "
                f"candidate {', '.join(wrong)} was replayed against; the witness would bind "
                f"this index to another binary")
    pair_bundles = {pair.operation: vector_claims.build_bundle(pair.vectors, pair.replay)
                    for pair in pairs}
    return combine(static.bundle, *pair_bundles.values(),
                   fragment(pairs, pair_bundles, index=index, borrowed=borrowed,
                            describes_candidate=describes_candidate),
                   metadata={"static_bundle_sha256": static.sha256,
                             "claim_join": "capcov-vectors-static-v1"})


def judge(pairs: Iterable[OperationPair], static: StaticBundle, *,
          describes_candidate: str | None, kernel: str = "python", **kwargs: Any):
    """Build the joined bundle and judge it with ``vectors.claims``' kernel selection."""
    return vector_claims.judge_bundle(
        build_bundle(pairs, static, describes_candidate=describes_candidate),
        kernel=kernel, **kwargs)


#: Per written table, what the join made of it.  ``divergence`` is the refuted
#: claim; ``reached`` is a positive static path; ``unindexed`` is a table the
#: index's own entity census never declared, which is not a claim that the
#: route cannot reach it; ``unresolved`` is everything else, and says so.
STORE_DIVERGENCE = "divergence"
STORE_REACHED = "reached"
STORE_UNINDEXED = "unindexed"
STORE_UNRESOLVED = "unresolved"

JOIN_BOUND = "bound"
JOIN_UNWITNESSED = "unwitnessed"

TABLE_RELATION = "static_table"
#: The static relations the document reads, so ``underived`` is one list a
#: reader can check a status against rather than a fact about this source.
READ_RELATIONS = (NO_TABLE_RELATION, REACHES_TABLE_RELATION, TABLE_RELATION)


def _rows(derived: Mapping[str, Any], relation: str) -> tuple[tuple, ...]:
    return tuple(tuple(row) for row in derived.get(relation, ()))


def document(judgment, pairs: Iterable[OperationPair], static: StaticBundle, *,
             describes_candidate: str | None, kernel: str) -> dict[str, Any]:
    """The report: per operation, what was written, what is reached, and what neither says.

    Every null here means "withheld", never "none": a store set that is not
    closed reports ``null`` for ``unexercised`` with the replay producer's own
    reasons beside it, and a table the index never declared is ``unindexed``
    rather than a divergence.
    """
    pairs = tuple(pairs)
    derived = {name: tuple(rows) for name, rows in judgment.report.relations}
    derivable = derivable_relations(judgment.bundle)
    index = index_of(static)
    divergence = {(row[1], row[2], row[3]) for row in _rows(derived, DIVERGENCE_RELATION)}
    reaches = {(row[1], row[2]) for row in _rows(derived, REACHES_TABLE_RELATION)
               if row[0] == index}
    tables = {row[1] for row in _rows(derived, TABLE_RELATION) if row[0] == index}
    closed_runs = {(row[0], row[1]) for row in _rows(derived, STORES_CLOSED_RELATION)}
    unexercised: dict[tuple[str, str], list[str]] = {}
    for row in _rows(derived, UNEXERCISED_RELATION):
        unexercised.setdefault((row[1], row[2]), []).append(row[3])
    written: dict[tuple[str, str], set[str]] = {}
    for row in _rows(derived, STORE_CHANGED_RELATION):
        written.setdefault((row[0], row[1]), set()).add(row[3])

    operations: dict[str, Any] = {}
    for pair in pairs:
        key = (pair.run, pair.operation)
        report = stores_closed(pair)
        withheld: list[str] = list(report.reasons)
        if describes_candidate is None:
            withheld.append(f"no {DESCRIBES_RELATION} row: nothing binds this index to the "
                            f"candidate the replay declared")
        if REACHES_TABLE_RELATION not in derivable:
            withheld.append(f"{REACHES_TABLE_RELATION} is not derivable in this bundle")
        stores = {}
        for table in sorted(written.get(key, ())):
            if (*key, table) in divergence:
                stores[table] = STORE_DIVERGENCE
            elif pair.surface is not None and (pair.surface, table) in reaches:
                stores[table] = STORE_REACHED
            elif table not in tables:
                stores[table] = STORE_UNINDEXED
            else:
                stores[table] = STORE_UNRESOLVED
        operations[pair.operation] = {
            "run": pair.run,
            "recording_sha256": pair.recording,
            "candidate_sha256": pair.candidate,
            "surface": pair.surface,
            "surface_reason": pair.surface_reason,
            "cells_recorded": len(pair.vectors.vectors),
            "cells_failed": sorted(result.id for result in pair.replay.results
                                   if not result.passed),
            "gaps": sorted(str(item.get("cell")) for item in pair.vectors.gaps),
            "stores_written": sorted(written.get(key, ())),
            "stores_uncompared": sorted({table for vector in pair.vectors.vectors
                                         for table in uncompared_tables(vector)}),
            "stores": stores,
            "stores_closed": key in closed_runs,
            "stores_closed_withheld": list(report.reasons),
            "static_stores": (sorted({table for surface, table in reaches
                                      if surface == pair.surface})
                              if pair.surface is not None
                                 and REACHES_TABLE_RELATION in derivable else None),
            DIVERGENCE_RELATION: sorted(table for table, status in stores.items()
                                        if status == STORE_DIVERGENCE),
            # advisory, and null rather than empty when nothing licensed it
            UNEXERCISED_RELATION: (sorted(unexercised.get(key, ())) if not withheld else None),
            "unexercised_withheld": withheld,
        }
    refuted = sorted(key for key, verdict in judgment.verdicts().items()
                     if key.startswith("vector-store-divergence:")
                     and verdict["semantic"] == "refuted")
    return {
        "join": {
            "status": JOIN_BOUND if describes_candidate is not None else JOIN_UNWITNESSED,
            "witness": DESCRIBES_RELATION,
            "index": index,
            "candidate_sha256": describes_candidate,
            "message": (f"{DESCRIBES_RELATION} binds index {index[:12]} to candidate "
                        f"{describes_candidate[:12]}"
                        if describes_candidate is not None else
                        f"no {DESCRIBES_RELATION} was asserted, so every divergence claim is "
                        f"unresolved: nothing says this index describes the replayed binary"),
        },
        "bundle": {"static_sha256": static.sha256, "facts": len(judgment.bundle.facts),
                   "rules": len(judgment.bundle.rules),
                   "relations": len(judgment.bundle.relations)},
        "kernel": kernel,
        "backend": judgment.report.backend,
        "producers": {DESCRIBES_RELATION: REVIEWER_PRODUCER,
                      STORE_CHANGED_RELATION: REPLAY_PRODUCER,
                      STORES_CLOSED_RELATION: REPLAY_PRODUCER,
                      OPERATION_SURFACE_RELATION: RECORDER_PRODUCER},
        "underived": [name for name in READ_RELATIONS if name not in derivable],
        "operations": operations,
        "divergence_claims_refuted": refuted,
        "verdicts": judgment.verdicts(),
    }


def summary_line(report: Mapping[str, Any]) -> str:
    """One line for stdout: what diverged, what is advisory, and what was not settled."""
    operations = report["operations"]
    diverged = sorted({f"{name}:{table}" for name, entry in operations.items()
                       for table in entry[DIVERGENCE_RELATION]})
    advisory = sum(len(entry[UNEXERCISED_RELATION] or ()) for entry in operations.values())
    withheld = sum(1 for entry in operations.values() if entry[UNEXERCISED_RELATION] is None)
    return (f"capcov vectors-static: {len(operations)} operation(s) against index "
            f"{report['join']['index'][:12]} ({report['join']['status']}, kernel "
            f"{report['kernel']}): {len(diverged)} store divergence(s)"
            + (f" -- {', '.join(diverged)}" if diverged else "")
            + f"; {advisory} unexercised store(s) advisory, {withheld} operation(s) withheld")


def declared_stores(static: StaticBundle, surface: str) -> dict[str, Any]:
    """The recorder's ``declared`` list for one surface, from the static account.

    ``recorder.record(..., static_declared=...)`` takes the ``declared`` value of
    this result: ``{"tables": [...]}``, the store set the index says that route
    reaches.  It is returned only when the index closed that set
    (``static_route_reaches_table_closed``, which the closure pack derives from
    ``call_graph_closed``): an open set is a *lower bound*, and using a lower
    bound as the compared-store list would stop observing exactly the tables the
    index could not see.  Otherwise ``declared`` is ``None`` and ``reason`` says
    why, and the caller keeps whatever its inputs declared.
    """
    derived = closure(static.bundle)
    index = index_of(static)
    closed = {row[1] for row in derived.get("static_route_reaches_table_closed", ())
              if row[0] == index}
    tables = sorted({row[2] for row in derived.get(REACHES_TABLE_RELATION, ())
                     if row[0] == index and row[1] == surface})
    declared = {"surface": surface, "index": index, "tables": tables,
                "declared": None, "reason": ""}
    if REACHES_TABLE_RELATION not in derivable_relations(static.bundle):
        declared["reason"] = (f"this bundle has no rule and no fact for "
                              f"{REACHES_TABLE_RELATION}, so it names no store for any surface")
        return declared
    if surface not in closed:
        declared["reason"] = (f"the index does not close this surface's store set "
                              f"(no static_route_reaches_table_closed row), so "
                              f"{len(tables)} table(s) is a lower bound, not a declaration")
        return declared
    declared["declared"] = {"tables": tables}
    declared["reason"] = "static_route_reaches_table_closed closes this surface's store set"
    return declared


__all__ = ["REVIEWER_PRODUCER", "DESCRIBES_RELATION", "RUN_RECORDING_RELATION",
           "OPERATION_SURFACE_RELATION", "STORE_CHANGED_RELATION", "STORE_UNCOMPARED_RELATION",
           "STORE_TOUCHED_RELATION", "STORES_CLOSED_RELATION", "DIVERGENCE_RELATION",
           "UNEXERCISED_RELATION", "NO_TABLE_RELATION", "REACHES_TABLE_RELATION",
           "BORROWED_RELATIONS", "DECLARED_ALL", "HTTP_DRIVER", "HTTP_SURFACE_PREFIX", "VectorStaticError", "OperationPair",
           "ClosureReport", "StaticBundle", "StaticBundleError", "load", "operation_surface",
           "changed_tables", "uncompared_tables", "read_pairs", "borrow", "relations", "rules",
           "stores_closed", "fragment", "index_of", "build_bundle", "judge",
           "declared_stores", "document", "summary_line", "READ_RELATIONS", "TABLE_RELATION",
           "STORE_DIVERGENCE", "STORE_REACHED", "STORE_UNINDEXED", "STORE_UNRESOLVED",
           "JOIN_BOUND", "JOIN_UNWITNESSED"]
