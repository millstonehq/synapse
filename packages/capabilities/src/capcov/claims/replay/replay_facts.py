"""Export a replay receipt directory as claim facts + evidence (Phase 4, judge side).

The replay harness is a *producer of runtime observations*, never an oracle.
This module turns one receipt directory -- written by the Go replay driver
after replaying a recorded request set against the PHP system, the Go system
and the Shen model, under one nonce and one snapshot -- into a validated claims
``Bundle`` whose every fact carries the receipt's ``run`` context (or the
``model`` context for model-scoped relations), whose every fact has an
``Evidence`` record with a content-derived id, an explicit ``depends_on`` chain
and a ``source`` naming the *producer class* the row is attributed to, and
whose completeness witnesses are emitted only when the receipt says the
corresponding table is closed.  The bundle's ``digest()`` is a pure function of
the receipt's content: permuting the rows of any file changes nothing.

It mirrors ``capcov.claims.static.scip_facts`` deliberately -- same
``ExportResult``, same ``_Facts`` accumulator, same identity/receipt
separation -- so a reader of one can read the other.

RECEIPT DIRECTORY CONTRACT
--------------------------
This is the contract the Go replay driver writes.  ``receipt.json``::

    {"version": 1,
     "run": "<run id>",                      # symbol; the bundle's run context
     "nonce": "<sha256>", "snapshot": "<sha256>", "model": "<sha256>",
     "php_commit": "<git sha>", "go_commit": "<git sha>",
     "closed": {"replay_requests": true, "php_effects": true, "go_effects": true,
                "model_admissible": true, "mutant_kills": true},
     "model_writes_closed": [{"model": "<sha256>", "op": "<op>"}, ...],
     "mutants_closed":      [{"model": "<sha256>", "op": "<op>"}, ...],
     "receipts": {...}}                      # wall clock, paths, container ids

plus one JSON file per observation relation, named ``<relation>.json``::

    {"rows": [{"<column>": <value>, ...}, ...],
     "producer": "<class> <detail>"}         # optional, see EVIDENCE

for each of ``replay_request``, ``php_post_state``, ``go_post_state``,
``php_effect``, ``go_effect``, ``model_effect``, ``model_admissible``,
``model_writes``, ``mutant`` and ``mutant_killed`` (``OBSERVATION_FILES``).
Row objects carry the relation's columns by name; a ``run`` column may be
omitted (it is the receipt's ``run``) and a ``model`` column may be omitted (it
is the receipt's ``model``).  A row naming *another* run is a leftover of a
different replay and makes the export ``stale``; a row naming another model,
an unknown column, a missing column or a value of the wrong type is
``invalid-input``.  A missing ``<relation>.json`` means zero rows -- and the
corresponding ``*_closed`` witness is still emitted only if ``closed`` says so,
because "no rows" and "no rows exist" are different statements.  Every key of
``closed`` defaults to ``false``; ``model_writes_closed`` / ``mutants_closed``
default to empty.  ``replay_run`` has no file: its one row is the receipt
header.

One observation per write and per post-state (``UNIQUE_KEYS``): two
``php_effect`` / ``go_effect`` / ``model_effect`` rows sharing
``(run, [model,] req, table, kind, pk)`` with different ``cols_digest``, or
two ``php_post_state`` / ``go_post_state`` rows for one ``(run, req)`` with
different ``state_digest``, are contradictory reports of the same event and
make the export ``invalid-input`` naming the key -- the judge never carries
both as facts and lets a rule pick.  A row repeated verbatim is one fact.
``model_admissible`` is a set of admissible states per request and is not
constrained.

IDENTITY
--------
The bundle's identity (metadata ``replay_digest``, kind
``REPLAY_IDENTITY = "replay-relations-v1"``) is a content digest of the
normalized relations the exporter emits, never of the files' bytes::

    replay_digest = sha256("replay-relations-v1:" + canonical_json({
        "relations": sorted(<every relation name the bundle declares>),
        "rows": {relation: sorted(canonical rows) for every exported primitive
                 relation with at least one row, except the compatibility
                 relations (``model_describes_run``, ``index_describes_replay``)}}))

Unlike the static exporter's ``index``, the ``run`` context is *not* derived
from the identity: it is the receipt's run id, content the harness reported,
and it takes part in the identity like every other column.  Compatibility
relations bind the run to *other* contexts (a model, a static index) and are
keyed by the identity rather than part of it: declaring that index ``i``
describes the replay does not make it a different replay.

Every fact is first built under a placeholder identity, the identity is
computed from the finished rows, then the evidence ids (which embed
``replay_digest[:12]`` and the row digest) are computed -- content digest, then
ids.  The ``receipts`` object of ``receipt.json`` (wall-clock timestamps, file
paths, container ids) and the directory the receipt was read from are *run
receipts*: carried in bundle metadata under ``RECEIPT_METADATA_KEYS`` and
excluded from ``bundle_digest``, so a receipt never becomes identity.

EVIDENCE
--------
Ids are ``<prefix>:<replay12>:<relation>:<row12>`` where ``prefix`` is the
evidence-id prefix of the relation's producer class (``EVIDENCE_PREFIXES``:
``replay``, ``php``, ``go``, ``shen``, ``mut``, ``reviewer``; the ``php-census``
class shares the ``php`` prefix; witnesses and compatibility rows, which no
producer class owns, use ``replay``) and ``row12 =
sha256(canonical_json([relation, row]))[:12]``.

``Evidence.source`` is the producer string and its first whitespace-delimited
token is the *producer class* that ``claims.validation`` checks against the
relation's declared ``producer_classes`` (issue ``evidence-producer``).  The
default source for an observation row is ``"<class> capcov.claims.replay.replay_facts v1"``
(the class the schema attributes the relation to, then the transcriber); a
``<relation>.json`` may name its real producer in ``producer`` (for example
``"php target-cloud 1a2b3c"``) and that string is carried verbatim -- so a file
that claims a producer class the relation does not admit is rejected at
ingestion, which is the single boundary at which producer authority is
enforced.  Completeness witnesses use
``"capcov.claims.replay.replay_facts <predicate>-v1"``, naming the predicate
whose emission condition was checked.  Rows depend on the ``replay_run`` row,
on the ``replay_request`` row of their request when one is exported, and on
``external:model:<model>``, ``external:git-commit:<commit>``,
``external:snapshot:<snapshot>`` and ``external:index:<index>`` for the
identities the receipt only names.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..ir import (Atom, Bundle, Column, Constant, Context, Evidence,
                  RelationDecl, TypeName, canonical_json, digest as ir_digest)
from ..validation import ValidationError, assert_valid
from . import load_replay_schema

EXPORT_VERSION = "v1"
EXPORTER = "capcov.claims.replay.replay_facts"
PRODUCER = f"{EXPORTER} {EXPORT_VERSION}"

STATUS_COMPLETE = "complete"
STATUS_RESOURCE_EXHAUSTED = "resource-exhausted"
STATUS_INVALID_INPUT = "invalid-input"
STATUS_STALE = "stale"

RECEIPT_VERSION = 1
RECEIPT_FILE = "receipt.json"

# The identity scheme (module docstring, IDENTITY): the value of metadata
# ``replay_digest_kind``.
REPLAY_IDENTITY = "replay-relations-v1"
_IDENTITY_PREFIX = REPLAY_IDENTITY + ":"
# Facts are assembled under this identity and re-keyed once the real one is
# known; it never appears in an exported bundle.
_PLACEHOLDER_IDENTITY = "0" * 64
# Run receipts carried in bundle metadata but excluded from ``bundle_digest``:
# the receipt.json ``receipts`` object (wall clock, file paths, container ids)
# and the directory the receipt was read from.
RECEIPT_METADATA_KEYS = ("receipts", "receipt_dir")

# Producer classes the schema attributes rows to, and the evidence-id prefix
# of each (module docstring, EVIDENCE).
EVIDENCE_PREFIXES = {
    "replay": "replay", "php": "php", "go": "go", "shen": "shen", "mut": "mut",
    "reviewer": "reviewer", "php-census": "php",
}
_UNOWNED_PREFIX = "replay"

# The observation relations read from ``<relation>.json``; ``replay_run`` is
# the receipt header and has no file.
OBSERVATION_FILES = (
    "replay_request", "php_post_state", "go_post_state", "php_effect", "go_effect",
    "model_effect", "model_admissible", "model_writes", "mutant", "mutant_killed",
)

# Relations that admit one observation per key (module docstring, RECEIPT
# DIRECTORY CONTRACT): relation -> the columns that identify the event; the
# remaining column is the observed value and may not differ between rows.
UNIQUE_KEYS = {
    "php_effect": ("run", "req", "table", "kind", "pk"),
    "go_effect": ("run", "req", "table", "kind", "pk"),
    "model_effect": ("run", "model", "req", "table", "kind", "pk"),
    "php_post_state": ("run", "req"),
    "go_post_state": ("run", "req"),
}

# The witnesses' predicate versions. Each Evidence.source names one of these so
# a reviewer knows which emission contract was checked.
WITNESS_REQUESTS = "requests-closed-v1"
WITNESS_PHP_EFFECTS = "php-effects-closed-v1"
WITNESS_GO_EFFECTS = "go-effects-closed-v1"
WITNESS_MODEL_ADMISSIBLE = "model-admissible-closed-v1"
WITNESS_MUTANT_KILLS = "mutant-kills-closed-v1"
WITNESS_MODEL_WRITES = "model-writes-closed-v1"
WITNESS_MUTANTS = "mutants-closed-v1"

# receipt.json ``closed`` key -> (witness relation, predicate version).
_RUN_WITNESSES = {
    "replay_requests": ("replay_requests_closed", WITNESS_REQUESTS),
    "php_effects": ("php_effects_closed", WITNESS_PHP_EFFECTS),
    "go_effects": ("go_effects_closed", WITNESS_GO_EFFECTS),
    "model_admissible": ("model_admissible_closed", WITNESS_MODEL_ADMISSIBLE),
    "mutant_kills": ("mutant_kills_closed", WITNESS_MUTANT_KILLS),
}
_RECEIPT_KEYS = frozenset({
    "version", "run", "nonce", "snapshot", "model", "php_commit", "go_commit",
    "closed", "model_writes_closed", "mutants_closed", "receipts",
})

# Relations the frozen primitive schema points at but does not declare: the
# derived ``completes`` target of ``mutant_kills_closed`` and the derived
# compatibility target of ``index_describes_replay``.  They are declared here
# as rule-less stubs only so an exported bundle validates on its own; the
# replay rule pack owns their rules and declares them again, byte-identically
# (``combine.combine`` refuses a non-identical duplicate).  ``mutant_killed_in``
# is the (run, mutant) projection of ``mutant_killed``; ``op_qualified_rt`` is
# the (index, run, op) join of a statically declared op with a replayed request
# for it, which is why it carries both contexts and is runtime-bound.
_DERIVED_TARGET_DECLS = (
    RelationDecl("mutant_killed_in",
                 (Column("run", "symbol", True), Column("mutant", "symbol")),
                 modality="derived", binding="runtime", primitive=False,
                 context_indices=("run",)),
    RelationDecl("op_qualified_rt",
                 (Column("index", "digest", True), Column("run", "symbol", True),
                  Column("op", "symbol")),
                 modality="derived", binding="runtime", primitive=False,
                 context_indices=("index", "run")),
)
STUB_RELATIONS = frozenset(decl.name for decl in _DERIVED_TARGET_DECLS)


# ---------------------------------------------------------------------------
# Public parameter / result types


@dataclass(frozen=True)
class ExportLimits:
    """Finite execution bars. Tripping one is ``resource-exhausted``, never an
    exception and never silently raised. ``rows`` mirrors the Soufflé kernel's
    100k-row cap over every relation, inputs included; ``file_bytes`` bounds
    what is read from any one ``<relation>.json``."""
    rows: int = 100_000
    file_bytes: int = 64 * 1024 * 1024


@dataclass(frozen=True)
class ExportResult:
    status: str
    bundle: Bundle | None
    counts: dict[str, int] = field(default_factory=dict)
    messages: tuple[str, ...] = ()


class ExportInputError(ValueError):
    """A receipt row or header broke an exporter precondition."""


class StaleReceiptError(ExportInputError):
    """A row file names a run other than the receipt's."""


# ---------------------------------------------------------------------------
# Identity helpers


def row_digest(relation: str, row: list[Any]) -> str:
    return hashlib.sha256(canonical_json([relation, list(row)]).encode("utf-8")).hexdigest()


def evidence_prefix(relation: RelationDecl) -> str:
    """The evidence-id prefix of a relation's producer class (module docstring, EVIDENCE)."""
    if relation.producer_classes:
        return EVIDENCE_PREFIXES.get(relation.producer_classes[0], _UNOWNED_PREFIX)
    return _UNOWNED_PREFIX


def evidence_id(replay_digest: str, relation: RelationDecl, row: list[Any]) -> str:
    """``<prefix>:<replay12>:<relation>:<row12>``."""
    return (f"{evidence_prefix(relation)}:{replay_digest[:12]}:{relation.name}:"
            f"{row_digest(relation.name, row)[:12]}")


def replay_relations_identity(rows_by_relation: Mapping[str, Iterable[list[Any]]],
                              relation_names: Iterable[str]) -> str:
    """The ``replay-relations-v1`` identity of a set of exported rows.

    ``rows_by_relation`` maps a relation to its full rows; only relations with
    at least one row take part. Row order and relation order do not matter;
    the declared relation names do.
    """
    payload = {
        "relations": sorted(set(relation_names)),
        "rows": {
            relation: sorted((list(row) for row in rows), key=canonical_json)
            for relation, rows in rows_by_relation.items() if rows
        },
    }
    return hashlib.sha256((_IDENTITY_PREFIX + canonical_json(payload)).encode("utf-8")).hexdigest()


def replay_relations() -> tuple[RelationDecl, ...]:
    """The frozen primitive declarations plus the derived-target stubs."""
    frozen = tuple(_relation_from_json(item) for item in load_replay_schema()["relations"])
    return frozen + _DERIVED_TARGET_DECLS


def primitive_relations() -> tuple[RelationDecl, ...]:
    """The frozen primitive declarations alone (what the exporter produces rows for)."""
    return tuple(_relation_from_json(item) for item in load_replay_schema()["relations"])


def _relation_from_json(raw: dict) -> RelationDecl:
    return RelationDecl(
        raw["name"],
        tuple(Column(c["name"], c["type"], c["context"]) for c in raw["columns"]),
        raw["modality"], raw["polarity"], raw["binding"], raw["primitive"],
        tuple(raw["producer_classes"]), tuple(raw["context_indices"]), raw["completes"],
        raw["finite"], raw["nonempty"], tuple(raw["compatibility_targets"]),
        tuple(raw["compatibility_context_indices"]),
    )


def default_source(relation: RelationDecl) -> str:
    """``"<class> <PRODUCER>"`` for an owned relation, ``PRODUCER`` otherwise."""
    if relation.producer_classes:
        return f"{relation.producer_classes[0]} {PRODUCER}"
    return PRODUCER


# ---------------------------------------------------------------------------
# Row accumulator


class _Facts:
    """Deduplicating fact/evidence accumulator.

    A row is identified by ``(relation, values)``; adding it twice merges the
    dependency sets (the union is sorted by ``Evidence``), so a row reported
    twice yields one fact with one content-derived evidence id.
    """

    def __init__(self, replay_digest: str, relations: dict[str, RelationDecl]) -> None:
        self.replay_digest = replay_digest
        self.relations = relations
        self.rows: dict[tuple[str, tuple], dict] = {}

    def add(self, relation: str, values: dict[str, Any], *, source: str,
            depends_on: Iterable[str] = (), kind: str = "fact") -> str:
        decl = self.relations[relation]
        row: list[Any] = []
        for column in decl.columns:
            if column.name not in values:
                raise ExportInputError(f"{relation}: missing column {column.name!r}")
            row.append(_checked(relation, column, values[column.name]))
        key = (relation, tuple(row))
        eid = evidence_id(self.replay_digest, decl, row)
        entry = self.rows.get(key)
        if entry is None:
            entry = {"id": eid, "row": row, "source": source, "kind": kind,
                     "depends_on": set()}
            self.rows[key] = entry
        entry["depends_on"].update(d for d in depends_on if d and d != eid)
        return eid

    def count(self, relation: str) -> int:
        return sum(1 for rel, _ in self.rows if rel == relation)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for rel, _ in self.rows:
            out[rel] = out.get(rel, 0) + 1
        return dict(sorted(out.items()))

    def __len__(self) -> int:
        return len(self.rows)

    def identity(self) -> str:
        """``replay_relations_identity`` over every accumulated row of a
        non-compatibility relation (module docstring, IDENTITY)."""
        by_relation: dict[str, list[list[Any]]] = {}
        for (relation, _), entry in self.rows.items():
            if self.relations[relation].modality.value == "compatibility":
                continue
            by_relation.setdefault(relation, []).append(list(entry["row"]))
        return replay_relations_identity(by_relation, self.relations)

    def rebase(self, replay_digest: str) -> None:
        """Recompute every evidence id under ``replay_digest``.

        No column is rewritten -- the ``run`` context is receipt content, not a
        placeholder -- but every id embeds the identity, so ``depends_on``
        entries are rewritten through the old->new id map and every external
        id is left alone.
        """
        rename: dict[str, str] = {}
        rebased: dict[tuple[str, tuple], dict] = {}
        for (relation, _), entry in self.rows.items():
            row = list(entry["row"])
            eid = evidence_id(replay_digest, self.relations[relation], row)
            rename[entry["id"]] = eid
            rebased[(relation, tuple(row))] = {**entry, "id": eid, "row": row}
        for entry in rebased.values():
            entry["depends_on"] = {rename.get(d, d) for d in entry["depends_on"]} - {entry["id"]}
        self.rows = rebased
        self.replay_digest = replay_digest

    def materialize(self) -> tuple[tuple[Atom, ...], tuple[Evidence, ...]]:
        facts: list[Atom] = []
        evidence: list[Evidence] = []
        for (relation, _), entry in self.rows.items():
            decl = self.relations[relation]
            atom = Atom(relation, tuple(
                Constant(value, column.type)
                for value, column in zip(entry["row"], decl.columns)))
            context = {
                name: entry["row"][[c.name for c in decl.columns].index(name)]
                for name in decl.context_indices
            }
            facts.append(atom)
            evidence.append(Evidence(
                entry["id"], atom, Context.from_mapping(context), entry["source"],
                tuple(sorted(entry["depends_on"])), entry["kind"]))
        return tuple(facts), tuple(evidence)


def _checked(relation: str, column: Column, value: Any) -> Any:
    t = column.type
    if t in (TypeName.SYMBOL, TypeName.DIGEST):
        if not isinstance(value, str):
            raise ExportInputError(f"{relation}.{column.name}: expected str, got {value!r}")
        return value
    if t == TypeName.UNSIGNED:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ExportInputError(f"{relation}.{column.name}: expected unsigned, got {value!r}")
        return value
    if t == TypeName.BOOLEAN:
        if not isinstance(value, bool):
            raise ExportInputError(f"{relation}.{column.name}: expected bool, got {value!r}")
        return value
    raise ExportInputError(f"{relation}.{column.name}: unsupported column type {t}")


# ---------------------------------------------------------------------------
# Receipt reading


def _require_str(receipt: Mapping[str, Any], key: str) -> str:
    value = receipt.get(key)
    if not isinstance(value, str) or not value:
        raise ExportInputError(f"{RECEIPT_FILE}: {key!r} must be a non-empty string")
    return value


def _read_json(path: Path, limit: int) -> Any:
    size = path.stat().st_size
    if size > limit:
        raise ExportInputError(f"{path.name}: {size} bytes exceed the {limit}-byte file limit")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExportInputError(f"{path.name}: not valid JSON ({exc})") from exc


def _read_receipt(receipt_dir: Path, run: str, limits: ExportLimits) -> dict[str, Any]:
    path = receipt_dir / RECEIPT_FILE
    if not receipt_dir.is_dir():
        raise ExportInputError(f"receipt directory {str(receipt_dir)!r} does not exist")
    if not path.is_file():
        raise ExportInputError(f"{RECEIPT_FILE} is missing from {str(receipt_dir)!r}")
    receipt = _read_json(path, limits.file_bytes)
    if not isinstance(receipt, Mapping):
        raise ExportInputError(f"{RECEIPT_FILE}: must be an object")
    unknown = set(receipt) - _RECEIPT_KEYS
    if unknown:
        raise ExportInputError(f"{RECEIPT_FILE}: unknown keys {sorted(unknown)}")
    version = receipt.get("version")
    if isinstance(version, bool) or version != RECEIPT_VERSION:
        raise ExportInputError(f"{RECEIPT_FILE}: version must be {RECEIPT_VERSION}, got {version!r}")
    header = {key: _require_str(receipt, key)
              for key in ("run", "nonce", "snapshot", "model", "php_commit", "go_commit")}
    if header["run"] != run:
        raise ExportInputError(f"{RECEIPT_FILE}: receipt is for run {header['run']!r}, "
                               f"caller asked for {run!r}")
    closed_raw = receipt.get("closed", {})
    if not isinstance(closed_raw, Mapping):
        raise ExportInputError(f"{RECEIPT_FILE}: 'closed' must be an object")
    unknown = set(closed_raw) - set(_RUN_WITNESSES)
    if unknown:
        raise ExportInputError(f"{RECEIPT_FILE}: unknown 'closed' keys {sorted(unknown)}")
    closed = {}
    for key in _RUN_WITNESSES:
        value = closed_raw.get(key, False)
        if not isinstance(value, bool):
            raise ExportInputError(f"{RECEIPT_FILE}: closed.{key} must be a boolean")
        closed[key] = value
    scoped = {}
    for key in ("model_writes_closed", "mutants_closed"):
        entries = receipt.get(key, [])
        if not isinstance(entries, list):
            raise ExportInputError(f"{RECEIPT_FILE}: {key!r} must be an array")
        rows = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, Mapping) or set(entry) - {"model", "op"}:
                raise ExportInputError(f"{RECEIPT_FILE}: {key}[{index}] must be {{model?, op}}")
            model = entry.get("model", header["model"])
            if model != header["model"]:
                raise ExportInputError(f"{RECEIPT_FILE}: {key}[{index}] names model "
                                       f"{str(model)[:12]!r}, the receipt's model is "
                                       f"{header['model'][:12]!r}")
            if not isinstance(entry.get("op"), str) or not entry["op"]:
                raise ExportInputError(f"{RECEIPT_FILE}: {key}[{index}].op must be a non-empty string")
            rows.append({"model": model, "op": entry["op"]})
        scoped[key] = rows
    receipts = receipt.get("receipts", {})
    if not isinstance(receipts, Mapping):
        raise ExportInputError(f"{RECEIPT_FILE}: 'receipts' must be an object")
    return {**header, "closed": closed, **scoped, "receipts": dict(receipts)}


def _read_rows(receipt_dir: Path, relation: RelationDecl, header: Mapping[str, str],
               limits: ExportLimits) -> tuple[str | None, list[dict[str, Any]]]:
    """``(producer, rows)`` of ``<relation>.json``; ``(None, [])`` when absent."""
    path = receipt_dir / f"{relation.name}.json"
    if not path.is_file():
        return None, []
    document = _read_json(path, limits.file_bytes)
    if not isinstance(document, Mapping) or set(document) - {"rows", "producer"}:
        raise ExportInputError(f"{path.name}: must be {{rows, producer?}}")
    producer = document.get("producer")
    if producer is not None and (not isinstance(producer, str) or not producer.strip()):
        raise ExportInputError(f"{path.name}: 'producer' must be a non-empty string")
    raw_rows = document.get("rows", [])
    if not isinstance(raw_rows, list):
        raise ExportInputError(f"{path.name}: 'rows' must be an array")
    names = [column.name for column in relation.columns]
    rows = []
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, Mapping):
            raise ExportInputError(f"{path.name}: rows[{index}] must be an object")
        unknown = set(raw) - set(names)
        if unknown:
            raise ExportInputError(f"{path.name}: rows[{index}] has unknown columns {sorted(unknown)}")
        row = dict(raw)
        if "run" in names:
            row.setdefault("run", header["run"])
            if row["run"] != header["run"]:
                raise StaleReceiptError(f"{path.name}: rows[{index}] names run {row['run']!r}, "
                                        f"the receipt is for {header['run']!r}")
        if "model" in names:
            row.setdefault("model", header["model"])
            if row["model"] != header["model"]:
                raise ExportInputError(f"{path.name}: rows[{index}] names model "
                                       f"{str(row['model'])[:12]!r}, the receipt's model is "
                                       f"{header['model'][:12]!r}")
        missing = [name for name in names if name not in row]
        if missing:
            raise ExportInputError(f"{path.name}: rows[{index}] lacks columns {missing}")
        rows.append(row)
    key_columns = UNIQUE_KEYS.get(relation.name)
    if key_columns:
        seen: dict[tuple, tuple[int, dict[str, Any]]] = {}
        value_columns = [name for name in names if name not in key_columns]
        for index, row in enumerate(rows):
            key = tuple(canonical_json(row[name]) for name in key_columns)
            previous = seen.setdefault(key, (index, row))
            if previous[1] != row:
                raise ExportInputError(
                    f"{path.name}: rows[{previous[0]}] and rows[{index}] report the same "
                    f"{dict(zip(key_columns, (row[name] for name in key_columns)))} with different "
                    f"{value_columns}: one observation per {relation.name} key")
    return producer, rows


# ---------------------------------------------------------------------------
# The exporter


def export_bundle(
    receipt_dir: str | Path,
    *,
    run: str,
    describes_indexes: Iterable[str] = (),
    limits: ExportLimits | None = None,
) -> ExportResult:
    """Export one receipt directory as a validated replay-facts ``Bundle``.

    ``run`` is the run the caller expects the receipt to be for; a receipt for
    another run is ``invalid-input``.  ``describes_indexes`` adds one
    ``index_describes_replay(index, run)`` row per static index digest the
    caller vouches for.  Returns ``ExportResult`` with status ``complete``
    (bundle present), ``resource-exhausted`` (a limit tripped; no bundle),
    ``stale`` (a row file names another run; no bundle) or ``invalid-input``
    (a receipt precondition or bundle validation failed; no bundle).  Never
    raises for a limit or a malformed receipt.
    """
    receipt_dir = Path(receipt_dir)
    limits = limits or ExportLimits()
    messages: list[str] = []
    if not isinstance(run, str) or not run:
        return ExportResult(STATUS_INVALID_INPUT, None, {}, ("run must be a non-empty string",))

    relations = {decl.name: decl for decl in replay_relations()}
    facts = _Facts(_PLACEHOLDER_IDENTITY, relations)
    try:
        header = _read_receipt(receipt_dir, run, limits)
        model = header["model"]
        model_ext = f"external:model:{model}"

        # --- header row ------------------------------------------------------
        run_eid = facts.add("replay_run", {
            "run": header["run"], "nonce": header["nonce"], "php_commit": header["php_commit"],
            "go_commit": header["go_commit"], "snapshot": header["snapshot"], "model": model,
        }, source=default_source(relations["replay_run"]), depends_on=[
            f"external:git-commit:{header['php_commit']}",
            f"external:git-commit:{header['go_commit']}",
            f"external:snapshot:{header['snapshot']}", model_ext,
        ])

        # --- observation files ---------------------------------------------------
        producers: dict[str, str] = {"replay_run": default_source(relations["replay_run"])}
        request_eids: dict[str, str] = {}
        for name in OBSERVATION_FILES:
            decl = relations[name]
            producer, rows = _read_rows(receipt_dir, decl, header, limits)
            source = producer if producer is not None else default_source(decl)
            producers[name] = source
            if producer is None and not rows:
                messages.append(f"{name}.json absent: zero rows")
            names = [column.name for column in decl.columns]
            for row in rows:
                deps = []
                if "run" in names:
                    deps.append(run_eid)
                if "model" in names:
                    deps.append(model_ext)
                if "req" in names and name != "replay_request":
                    req_eid = request_eids.get(row["req"])
                    if req_eid is not None:
                        deps.append(req_eid)
                eid = facts.add(name, row, source=source, depends_on=deps)
                if name == "replay_request":
                    request_eids[row["req"]] = eid
            if len(facts) > limits.rows:
                return ExportResult(STATUS_RESOURCE_EXHAUSTED, None, facts.counts(),
                                    (f"rows {len(facts)} exceed limit {limits.rows}",))

        # --- compatibility rows --------------------------------------------------
        facts.add("model_describes_run", {"model": model, "run": header["run"]},
                  source=PRODUCER, depends_on=[run_eid, model_ext])
        for index in sorted(set(describes_indexes)):
            if not isinstance(index, str) or not index:
                raise ExportInputError("describes_indexes must contain non-empty digest strings")
            facts.add("index_describes_replay", {"index": index, "run": header["run"]},
                      source=PRODUCER, depends_on=[run_eid, f"external:index:{index}"])

        # --- completeness witnesses ----------------------------------------------
        witness = f"{EXPORTER} "
        for key, (relation, predicate) in _RUN_WITNESSES.items():
            if not header["closed"][key]:
                messages.append(f"closed.{key} is false: no {relation} witness")
                continue
            values = {"run": header["run"]}
            deps = [run_eid]
            if relation == "model_admissible_closed":
                values["model"] = model
                deps.append(model_ext)
            facts.add(relation, values, source=witness + predicate, depends_on=deps)
        for entry in header["model_writes_closed"]:
            facts.add("model_writes_closed", entry, source=witness + WITNESS_MODEL_WRITES,
                      depends_on=[model_ext])
        for entry in header["mutants_closed"]:
            facts.add("mutants_closed", entry, source=witness + WITNESS_MUTANTS,
                      depends_on=[model_ext])
    except StaleReceiptError as exc:
        return ExportResult(STATUS_STALE, None, facts.counts(), (str(exc),))
    except ExportInputError as exc:
        return ExportResult(STATUS_INVALID_INPUT, None, facts.counts(), (str(exc),))
    except OSError as exc:
        return ExportResult(STATUS_INVALID_INPUT, None, facts.counts(),
                            (f"receipt directory unreadable: {exc}",))

    # --- bounds, assembly, validation ----------------------------------------
    if len(facts) > limits.rows:
        return ExportResult(STATUS_RESOURCE_EXHAUSTED, None, facts.counts(),
                            (f"rows {len(facts)} exceed limit {limits.rows}",))
    # content digest -> evidence ids (module docstring, IDENTITY)
    identity = facts.identity()
    facts.rebase(identity)
    messages.append(f"replay identity {identity} ({REPLAY_IDENTITY}); the receipt directory "
                    f"{str(receipt_dir)!r} and its receipts object are run receipts, not identity")
    fact_atoms, evidence = facts.materialize()
    metadata = {
        "export_version": EXPORT_VERSION,
        "exporter": EXPORTER,
        "run": header["run"],
        "replay_digest": identity,
        "replay_digest_kind": REPLAY_IDENTITY,
        "nonce": header["nonce"],
        "snapshot": header["snapshot"],
        "model": header["model"],
        "php_commit": header["php_commit"],
        "go_commit": header["go_commit"],
        "closed": header["closed"],
        "producers": {**producers, "exporter": PRODUCER},
        "describes_indexes": sorted(set(describes_indexes)),
        "row_counts": facts.counts(),
        "receipts": header["receipts"],
        "receipt_dir": str(receipt_dir),
    }
    bundle = Bundle(tuple(relations.values()), fact_atoms, (), (), tuple(metadata.items()),
                    evidence=evidence)
    try:
        assert_valid(bundle)
    except ValidationError as exc:
        return ExportResult(STATUS_INVALID_INPUT, None, facts.counts(),
                            tuple(f"{i.code}: {i.message} at {i.path}" for i in exc.issues)
                            if hasattr(exc, "issues") else (str(exc),))
    return ExportResult(STATUS_COMPLETE, bundle, facts.counts(), tuple(messages))


def _without_receipts(items: Any) -> Any:
    """``items`` (a mapping or a frozen sequence of pairs) minus the receipt keys."""
    pairs = list(items.items()) if isinstance(items, Mapping) else list(items)
    return tuple((k, v) for k, v in pairs if k not in RECEIPT_METADATA_KEYS)


def bundle_digest(bundle: Bundle) -> str:
    """The canonical digest of an exported bundle (``claims.ir.digest``) with
    the run receipts ``RECEIPT_METADATA_KEYS`` removed from the metadata, so
    the digest is a function of the exported content and not of when, where
    or in which container the replay happened. ``combine.combine`` nests each
    input's metadata under ``source_<i>``; the receipts are removed there too,
    so a combined bundle's digest is receipt-free as well."""
    metadata = []
    for key, value in _without_receipts(bundle.metadata):
        if key.startswith("source_") and isinstance(value, (Mapping, tuple, list)) \
                and all(isinstance(item, (tuple, list)) and len(item) == 2 for item in
                        (value.items() if isinstance(value, Mapping) else value)):
            value = _without_receipts(value)
        metadata.append((key, value))
    return ir_digest(replace(bundle, metadata=tuple(metadata)))


__all__ = [
    "EXPORT_VERSION", "EXPORTER", "PRODUCER", "REPLAY_IDENTITY", "RECEIPT_VERSION",
    "RECEIPT_FILE", "RECEIPT_METADATA_KEYS", "EVIDENCE_PREFIXES", "OBSERVATION_FILES",
    "STATUS_COMPLETE", "STATUS_RESOURCE_EXHAUSTED", "STATUS_INVALID_INPUT", "STATUS_STALE", "UNIQUE_KEYS",
    "ExportLimits", "ExportResult", "ExportInputError", "StaleReceiptError",
    "evidence_id", "evidence_prefix", "row_digest", "replay_relations_identity",
    "replay_relations", "primitive_relations", "STUB_RELATIONS", "default_source",
    "export_bundle", "bundle_digest",
]
