"""Retained target-go runtime receipts as typed claim evidence (section 30 join).

This module is the only admitted producer path for the causal-trace primitives
``runtime_function_entered``, ``runtime_sql_executed``, ``runtime_tx_committed``
and ``runtime_route_completed``.  Those relations declare the producer class
``target-go-runtime-trace-v2``; evidence whose ``source`` token is anything else is
rejected at ingestion (``evidence-producer``) and again by the ground checker.

A receipt is a *retained artifact*.  This module validates and imports one; it
never synthesizes a fake target-go run.  Loading is skip-gated by
``CAPCOV_TARGET_GO_RUNTIME_RECEIPT`` (and, for the live pilot, by
``CAPCOV_GO_FIXTURE_ROOT``).  The committed fixture
``tests/claim_semantics/target_go/artifacts/runtime-recipient-route.json`` is a
real disposable-MariaDB receipt, not a hand-written stand-in.

Static and runtime certificates stay independent: ``index_describes_run``
joins a run to an index, and ``runtime_route_reaches_sql_on_index`` requires
agreeing run/request/transaction/surface/index witnesses.  That is not one
end-to-end proof that a static call-graph path was the runtime stack.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from ..ir import (Atom, Bundle, Column, Constant, Context, Evidence, RelationDecl,
                  Rule, Variable, canonical_json)

RECEIPT_SCHEMA = "capcov-target-go-runtime-route/v2"
TRACE_PRODUCER = "target-go-runtime-trace-v2"
RECEIPT_ENV = "CAPCOV_TARGET_GO_RUNTIME_RECEIPT"
REQUIRED_KEYS = frozenset({
    "schema", "run", "candidate_commit", "tenant", "request_id", "surface",
    "http_status", "unsubscribe_http_status", "terminal_sql", "trace",
    "cleanup", "recorded_at",
})
EXPECTED_TERMINAL_SQL = {
    "notification_unsubscribed": 0,
    "go_notification_confirmation_cancelled": 1,
}
EXPECTED_CLEANUP = {"status": "complete", "owned_resources_remaining": 0}
CHANGE_SUBSCRIPTION = (
    "git.internal.example/org/target-go/internal/legacyissues.ChangeSubscription"
)
CHANGE_SUBSCRIPTION_TX = "change-subscription"
CANCEL_CONFIRMATION = "cancel-notification-confirmation"
DELETE_UNSUBSCRIBED = "delete-notification-unsubscribed"

# Synthetic index used only by fixture-backed correspondence tests.  It is not
# the target-go static-relations-v1 identity and must never be described as one.
FIXTURE_INDEX_KIND = "fixture-correspondence-v1"
FIXTURE_INDEX_SEED = b"capcov-fixture-correspondence-index-v1"


class RuntimeReceiptError(ValueError):
    """The retained artifact is missing, malformed, or fails a declared check."""


def row_digest(relation: str, row: list[Any]) -> str:
    """Same formula as ``scip_facts.row_digest``; kept here to avoid an import cycle."""
    return hashlib.sha256(canonical_json([relation, list(row)]).encode("utf-8")).hexdigest()


def fixture_index_digest() -> str:
    return hashlib.sha256(FIXTURE_INDEX_SEED).hexdigest()


# ---------------------------------------------------------------------------
# declarations (shared with the scip_facts stub set)


RUNTIME_ROUTE_OBSERVED = RelationDecl(
    "runtime_route_observed",
    (Column("tenant", "symbol", True), Column("surface", "symbol", True),
     Column("event", "symbol", True), Column("run", "symbol", True)),
    context_indices=("tenant", "surface", "event", "run"))

TRACE_PRIMITIVE_DECLS = (
    RelationDecl("runtime_function_entered",
                 (Column("run", "symbol", True), Column("request", "symbol", True),
                  Column("symbol", "symbol")),
                 producer_classes=(TRACE_PRODUCER,), context_indices=("run", "request")),
    RelationDecl("runtime_sql_executed",
                 (Column("run", "symbol", True), Column("request", "symbol", True),
                  Column("tx", "symbol", True), Column("operation", "symbol"),
                  Column("ordinal", "unsigned")),
                 producer_classes=(TRACE_PRODUCER,), context_indices=("run", "request", "tx")),
    RelationDecl("runtime_tx_committed",
                 (Column("run", "symbol", True), Column("request", "symbol", True),
                  Column("tx", "symbol", True)),
                 producer_classes=(TRACE_PRODUCER,), context_indices=("run", "request", "tx")),
    RelationDecl("runtime_route_completed",
                 (Column("run", "symbol", True), Column("request", "symbol", True),
                  Column("surface", "symbol", True)),
                 producer_classes=(TRACE_PRODUCER,), context_indices=("run", "request", "surface")),
)

RUNTIME_ROUTE_REACHES_SQL = RelationDecl(
    "runtime_route_reaches_sql_on_index",
    (Column("index", "digest", True), Column("run", "symbol", True),
     Column("request", "symbol", True), Column("surface", "symbol", True),
     Column("symbol", "symbol"), Column("tx", "symbol", True),
     Column("operation", "symbol")),
    modality="derived", binding="runtime", primitive=False,
    context_indices=("index", "run", "request", "surface", "tx"))

RUNTIME_ROUTE_ON_INDEX = RelationDecl(
    "runtime_route_observed_on_index",
    (Column("index", "digest", True), Column("tenant", "symbol", True),
     Column("surface", "symbol", True), Column("run", "symbol", True)),
    modality="derived", binding="runtime", primitive=False,
    context_indices=("index", "tenant", "surface", "run"))

RUNTIME_ROUTE_ON_INDEX_RULE = Rule(
    Atom("runtime_route_observed_on_index",
         (Variable("IX"), Variable("T"), Variable("S"), Variable("Run"))),
    (Atom("runtime_route_observed", (Variable("T"), Variable("S"), Variable("Request"), Variable("Run"))),
     Atom("index_describes_run", (Variable("IX"), Variable("Run"))),
     Atom("scip_index", (Variable("IX"), Variable("Indexer"), Variable("Version"),
                         Variable("Language"), Variable("Root"), Variable("Kind")))),
    name="runtime_route_matches_scip_index")

RUNTIME_ROUTE_REACHES_SQL_RULE = Rule(
    Atom("runtime_route_reaches_sql_on_index",
         (Variable("IX"), Variable("Run"), Variable("Request"), Variable("Surface"),
          Variable("Symbol"), Variable("Tx"), Variable("Operation"))),
    (Atom("runtime_route_observed", (Variable("Tenant"), Variable("Surface"),
                                    Variable("Request"), Variable("Run"))),
     Atom("runtime_function_entered", (Variable("Run"), Variable("Request"), Variable("Symbol"))),
     Atom("runtime_sql_executed", (Variable("Run"), Variable("Request"), Variable("Tx"),
                                  Variable("Operation"), Variable("Ordinal"))),
     Atom("runtime_tx_committed", (Variable("Run"), Variable("Request"), Variable("Tx"))),
     Atom("runtime_route_completed", (Variable("Run"), Variable("Request"), Variable("Surface"))),
     Atom("index_describes_run", (Variable("IX"), Variable("Run"))),
     Atom("scip_index", (Variable("IX"), Variable("Indexer"), Variable("Version"),
                         Variable("Language"), Variable("Root"), Variable("Kind")))),
    name="runtime_route_executes_committed_sql_on_index")


def expected_trace(request_id: str, surface: str) -> list[dict[str, Any]]:
    """The ordered causal-trace the v2 receipt must carry for the recipient route."""
    return [
        {"kind": "route_entered", "request_id": request_id, "symbol": surface},
        {"kind": "function_entered", "request_id": request_id, "symbol": CHANGE_SUBSCRIPTION},
        {"kind": "sql_executed", "request_id": request_id, "tx": CHANGE_SUBSCRIPTION_TX,
         "operation": DELETE_UNSUBSCRIBED, "ordinal": 1},
        {"kind": "sql_executed", "request_id": request_id, "tx": CHANGE_SUBSCRIPTION_TX,
         "operation": CANCEL_CONFIRMATION, "ordinal": 2},
        {"kind": "tx_committed", "request_id": request_id, "tx": CHANGE_SUBSCRIPTION_TX},
        {"kind": "route_completed", "request_id": request_id, "symbol": surface},
    ]


def _unique_object(pairs):
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RuntimeReceiptError(f"duplicate runtime receipt key: {key}")
        value[key] = item
    return value


@dataclass(frozen=True)
class RuntimeReceipt:
    """A validated retained receipt.  Mapping access forwards to the raw object."""

    values: Mapping[str, Any]
    sha256: str
    path: str | None = None

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    @property
    def run(self) -> str:
        return self.values["run"]

    @property
    def request_id(self) -> str:
        return self.values["request_id"]

    @property
    def surface(self) -> str:
        return self.values["surface"]

    @property
    def tenant(self) -> str:
        return self.values["tenant"]

    @property
    def candidate_commit(self) -> str:
        return self.values["candidate_commit"]

    def causal_row(self) -> tuple[str, str, str, str, str, str]:
        """``(run, request, surface, symbol, tx, operation)`` for the cancel write."""
        return (self.run, self.request_id, self.surface, CHANGE_SUBSCRIPTION,
                CHANGE_SUBSCRIPTION_TX, CANCEL_CONFIRMATION)


def load_runtime_receipt(path: str | Path, *,
                         expected_commit: str | None = None,
                         expected_surface: str | None = None) -> RuntimeReceipt:
    """Load a retained v2 receipt.  Raises rather than inventing fields.

    ``expected_commit`` / ``expected_surface`` bind the artifact to a live
    checkout (the target-go pilot).  Fixture-backed tests omit both: the committed
    receipt already names the checkout that produced it.
    """
    raw_path = Path(path)
    if not raw_path.is_file():
        raise RuntimeReceiptError(f"runtime receipt is not a file: {raw_path}")
    raw = raw_path.read_bytes()
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, RuntimeReceiptError) as exc:
        raise RuntimeReceiptError(f"runtime receipt is not unique JSON: {exc}") from exc
    if not isinstance(value, dict) or set(value) != REQUIRED_KEYS:
        raise RuntimeReceiptError("invalid target-go runtime receipt schema")
    if value["schema"] != RECEIPT_SCHEMA:
        raise RuntimeReceiptError(
            f"runtime receipt schema {value['schema']!r} is not {RECEIPT_SCHEMA}")
    if not value["run"] or value["request_id"] != value["run"] + "-subscribe":
        raise RuntimeReceiptError("runtime receipt identity differs")
    if value["http_status"] != 200 or value["unsubscribe_http_status"] != 200:
        raise RuntimeReceiptError("runtime route did not succeed")
    if value["terminal_sql"] != EXPECTED_TERMINAL_SQL:
        raise RuntimeReceiptError("runtime SQL terminal state differs")
    if value["cleanup"] != EXPECTED_CLEANUP:
        raise RuntimeReceiptError("runtime fixture cleanup differs")
    if value["trace"] != expected_trace(value["request_id"], value["surface"]):
        raise RuntimeReceiptError("runtime causal trace differs")
    if expected_commit is not None and value["candidate_commit"] != expected_commit:
        raise RuntimeReceiptError("runtime receipt does not describe the indexed checkout")
    if expected_surface is not None and value["surface"] != expected_surface:
        raise RuntimeReceiptError("runtime receipt does not describe the declared surface")
    return RuntimeReceipt(value, hashlib.sha256(raw).hexdigest(), str(raw_path))


def receipt_from_env(env: Mapping[str, str] | None = None, **kwargs: Any) -> RuntimeReceipt | None:
    """``None`` when ``CAPCOV_TARGET_GO_RUNTIME_RECEIPT`` is unset; otherwise load it."""
    env = os.environ if env is None else env
    path = env.get(RECEIPT_ENV)
    if not path:
        return None
    return load_runtime_receipt(path, **kwargs)


def _atom(decl: RelationDecl, values: list[Any]) -> Atom:
    return Atom(decl.name, tuple(Constant(item, column.type)
                                 for item, column in zip(values, decl.columns)))


def _evidence(decl: RelationDecl, atom: Atom, values: list[Any], *,
              run: str, sha256: str, commit: str, source: str) -> Evidence:
    context = {column.name: item for item, column in zip(values, decl.columns) if column.context}
    return Evidence(
        f"runtime:{run}:{decl.name}:{row_digest(decl.name, values)[:12]}",
        atom, Context.from_mapping(context), source,
        depends_on=(f"external:run:{run}", f"external:git-commit:{commit}"))


def runtime_bundle(receipt: RuntimeReceipt | Mapping[str, Any], *,
                   sha256: str | None = None,
                   producer: str = TRACE_PRODUCER) -> Bundle:
    """Facts + evidence + join rules from a validated receipt.

    ``producer`` defaults to the admitted class.  Passing another class is the
    unauthorized-producer test hook: the resulting bundle must fail closed.
    """
    values = receipt.values if isinstance(receipt, RuntimeReceipt) else dict(receipt)
    digest = sha256 if sha256 is not None else (
        receipt.sha256 if isinstance(receipt, RuntimeReceipt) else "")
    if not digest:
        raise RuntimeReceiptError("runtime bundle requires the receipt sha256")
    source = f"{producer} receipt sha256:{digest}"
    decls = {decl.name: decl for decl in (RUNTIME_ROUTE_OBSERVED, *TRACE_PRIMITIVE_DECLS)}
    route_values = [values["tenant"], values["surface"], values["request_id"], values["run"]]
    facts = [_atom(decls["runtime_route_observed"], route_values)]
    evidence = [_evidence(decls["runtime_route_observed"], facts[0], route_values,
                          run=values["run"], sha256=digest, commit=values["candidate_commit"],
                          source=source)]
    trace_rows = (
        ("runtime_function_entered", [values["run"], values["request_id"], values["trace"][1]["symbol"]]),
        ("runtime_sql_executed", [values["run"], values["request_id"], CHANGE_SUBSCRIPTION_TX,
                                  DELETE_UNSUBSCRIBED, 1]),
        ("runtime_sql_executed", [values["run"], values["request_id"], CHANGE_SUBSCRIPTION_TX,
                                  CANCEL_CONFIRMATION, 2]),
        ("runtime_tx_committed", [values["run"], values["request_id"], CHANGE_SUBSCRIPTION_TX]),
        ("runtime_route_completed", [values["run"], values["request_id"], values["surface"]]),
    )
    for relation, row in trace_rows:
        atom = _atom(decls[relation], row)
        facts.append(atom)
        evidence.append(_evidence(decls[relation], atom, row, run=values["run"], sha256=digest,
                                  commit=values["candidate_commit"], source=source))
    return Bundle(
        (RUNTIME_ROUTE_ON_INDEX, RUNTIME_ROUTE_REACHES_SQL, RUNTIME_ROUTE_OBSERVED,
         *TRACE_PRIMITIVE_DECLS),
        facts=tuple(facts),
        rules=(RUNTIME_ROUTE_ON_INDEX_RULE, RUNTIME_ROUTE_REACHES_SQL_RULE),
        evidence=tuple(evidence),
        metadata=(("runtime_receipt_sha256", digest), ("runtime_producer", producer),
                  ("runtime_schema", RECEIPT_SCHEMA)))


def fixture_index_facts(run: str, *, index: str | None = None
                       ) -> tuple[str, tuple[Atom, ...], tuple[Evidence, ...]]:
    """Synthetic ``scip_index`` + ``index_describes_run`` atoms for correspondence tests.

    Declarations come from the rule pack at ``combine`` time so the frozen
    ``index_describes_run`` compatibility set is not restated here.  The digest
    is not an target-go identity and is not a substitute for the live pilot.
    """
    index = index or fixture_index_digest()
    scip_values = [index, "fixture", "correspondence", "go", "file:///fixture", FIXTURE_INDEX_KIND]
    scip_atom = Atom("scip_index", (
        Constant(index, "digest"), Constant("fixture", "symbol"),
        Constant("correspondence", "symbol"), Constant("go", "symbol"),
        Constant("file:///fixture", "symbol"), Constant(FIXTURE_INDEX_KIND, "symbol")))
    describes_values = [index, run]
    describes_atom = Atom("index_describes_run", (
        Constant(index, "digest"), Constant(run, "symbol")))
    scip_evidence = Evidence(
        f"scip:{index[:12]}:scip_index:{row_digest('scip_index', scip_values)[:12]}",
        scip_atom, Context.from_mapping({"index": index}),
        source="fixture correspondence index")
    describes_evidence = Evidence(
        f"runtime:{run}:index_describes_run:{row_digest('index_describes_run', describes_values)[:12]}",
        describes_atom, Context.from_mapping({"index": index, "run": run}),
        source="capcov.claims.static.scip_facts v1",
        depends_on=(scip_evidence.id, f"external:run:{run}"))
    return index, (scip_atom, describes_atom), (scip_evidence, describes_evidence)


__all__ = [
    "RECEIPT_SCHEMA", "TRACE_PRODUCER", "RECEIPT_ENV", "REQUIRED_KEYS",
    "CHANGE_SUBSCRIPTION", "CHANGE_SUBSCRIPTION_TX", "CANCEL_CONFIRMATION",
    "DELETE_UNSUBSCRIBED", "FIXTURE_INDEX_KIND", "RuntimeReceiptError",
    "RuntimeReceipt", "row_digest", "fixture_index_digest",
    "RUNTIME_ROUTE_OBSERVED", "TRACE_PRIMITIVE_DECLS", "RUNTIME_ROUTE_REACHES_SQL",
    "RUNTIME_ROUTE_ON_INDEX",
    "RUNTIME_ROUTE_ON_INDEX_RULE", "RUNTIME_ROUTE_REACHES_SQL_RULE",
    "expected_trace", "load_runtime_receipt", "receipt_from_env",
    "runtime_bundle", "fixture_index_facts",
]
