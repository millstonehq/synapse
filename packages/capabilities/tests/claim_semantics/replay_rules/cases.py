"""Build the replay review cases from receipt variants of ``fixtures/replay_receipt_min``.

Every case's ``facts`` section is what ``replay_facts.export_bundle`` emits
over a small edit of the checked-in receipt (plus the claim-time reviewer /
census rows a judge adds), so the cases can never drift from the exporter:
``test_replay_corpus_schema`` regenerates each case through ``build`` and
requires the checked-in file to be identical up to its ``expected`` table.
Claims, diagnostics, output templates and the reviewer's verdict table
(``REVIEW``) are hand-authored here; ``python -m replay_rules.cases`` (from
``tests/claim_semantics``) rewrites the case files, refusing to write a case
whose Python-evaluator verdict, status, missing premises or discrepancies
differ from ``REVIEW``.  Support leaves are recorded from the evaluator and
frozen in the file; the differential and certificate tests then bind both
kernels to them.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

SRC = Path(__file__).resolve().parents[3] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capcov.claims import canonical_json  # noqa: E402
from capcov.claims.replay import replay_facts  # noqa: E402

try:
    from .adapter import CASES_DIR, PACK_ID, REJECTED_DIR
except ImportError:  # unittest discover -s imports this directory as top-level
    from replay_rules.adapter import CASES_DIR, PACK_ID, REJECTED_DIR

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "replay_receipt_min"
RUN = "run-fixture-1"
RECEIPT = json.loads((FIXTURE / "receipt.json").read_text(encoding="utf-8"))
MODEL = RECEIPT["model"]
NONCE = RECEIPT["nonce"]
SNAPSHOT = RECEIPT["snapshot"]
# The synthetic PHP census index the op_declared rows and index_describes_replay bind to.
INDEX = hashlib.sha256(b"rules-replay-v1 synthetic php census index").hexdigest()
CREATE, CLOSE = "issues.create", "issues.close"
OPS = (CREATE, CLOSE)
OTHER_NONCE = hashlib.sha256(b"rules-replay-v1 another nonce").hexdigest()
DISAGREEING_STATE = hashlib.sha256(b"rules-replay-v1 php post-state outside the model").hexdigest()

REVIEWER_SOURCE = "reviewer claim-time observation"
CENSUS_SOURCE = "php-census target-cloud route census v1"
REJECTED_SOURCE = "shen shen-model-host v1"
REJECTED_CLOSURE_SOURCE = "replay capcov.claims.replay.replay_facts model-admissible-closed-v1"

Edit = Callable[[Any], Any]


# ---------------------------------------------------------------------------
# receipt variants


@contextmanager
def variant(edits: dict[str, Edit]) -> Iterator[Path]:
    """A copy of the fixture with ``<stem>.json`` documents rewritten by ``edits``
    (``None`` deletes the file; the callable receives ``None`` when absent)."""
    with tempfile.TemporaryDirectory(prefix="replay-case-") as d:
        root = Path(d) / "receipt"
        shutil.copytree(FIXTURE, root)
        for stem, edit in edits.items():
            path = root / f"{stem}.json"
            document = json.loads(path.read_text()) if path.exists() else None
            replacement = edit(copy.deepcopy(document))
            if replacement is None:
                path.unlink(missing_ok=True)
            else:
                path.write_text(json.dumps(replacement, indent=1, sort_keys=True))
        yield root


def _edit_row(index: int, **changes: Any) -> Edit:
    def edit(document: Any) -> Any:
        document["rows"][index].update(changes)
        return document
    return edit


def _append_row(**row: Any) -> Edit:
    def edit(document: Any) -> Any:
        document["rows"].append(row)
        return document
    return edit


def _drop_row(index: int) -> Edit:
    def edit(document: Any) -> Any:
        del document["rows"][index]
        return document
    return edit


# ---------------------------------------------------------------------------
# claim-time rows (what a judge adds to an exported receipt)


def claim_time_id(prefix: str, relation: str, row: list[Any]) -> str:
    return f"{prefix}:claim-time:{relation}:{replay_facts.row_digest(relation, row)[:12]}"


def _claim_time_fact(relation: str, arg_order: list[str], args: list[Any], context: dict[str, Any],
                     prefix: str, source: str, depends_on: list[str]) -> dict[str, Any]:
    return {"id": claim_time_id(prefix, relation, args), "kind": "fact", "relation": relation,
            "arg_order": arg_order, "args": args, "context": context, "source": source,
            "provenance": {"depends_on": depends_on}}


def reviewer_facts(*, nonce: str | None = NONCE, snapshot: str | None = SNAPSHOT,
                   model: str | None = MODEL) -> list[dict[str, Any]]:
    out = []
    if nonce is not None:
        out.append(_claim_time_fact("run_nonce_observed", ["run", "nonce"], [RUN, nonce], {},
                                    "reviewer", REVIEWER_SOURCE, []))
    if snapshot is not None:
        out.append(_claim_time_fact("snapshot_observed", ["snapshot"], [snapshot], {},
                                    "reviewer", REVIEWER_SOURCE, []))
    if model is not None:
        out.append(_claim_time_fact("model_observed", ["model"], [model], {},
                                    "reviewer", REVIEWER_SOURCE, []))
    return out


def census_facts(ops: tuple[str, ...] = OPS) -> list[dict[str, Any]]:
    return [_claim_time_fact("op_declared", ["index", "op"], [INDEX, op], {"index": INDEX},
                             "php", CENSUS_SOURCE, [f"external:index:{INDEX}"]) for op in ops]


# ---------------------------------------------------------------------------
# exporter rows -> case facts


def exported_facts(receipt_dir: Path, *, drop_relations: tuple[str, ...] = ()) -> tuple[list[dict[str, Any]], str]:
    result = replay_facts.export_bundle(receipt_dir, run=RUN, describes_indexes=(INDEX,))
    if result.status != replay_facts.STATUS_COMPLETE:
        raise AssertionError(f"export failed: {result.status} {result.messages}")
    bundle = result.bundle
    decls = {decl.name: decl for decl in bundle.relations}
    facts = []
    for record in bundle.evidence:
        if record.atom.relation in drop_relations:
            continue
        decl = decls[record.atom.relation]
        facts.append({"id": record.id, "kind": record.kind, "relation": decl.name,
                      "arg_order": [column.name for column in decl.columns],
                      "args": [term.value for term in record.atom.terms],
                      "context": record.context.as_dict(), "source": record.source,
                      "provenance": {"depends_on": list(record.depends_on)}})
    order = [decl.name for decl in bundle.relations]
    facts.sort(key=lambda entry: (order.index(entry["relation"]), canonical_json(entry["args"])))
    return facts, dict(bundle.metadata)["replay_digest"]


def ir_facts(entries: list[dict[str, Any]], decls: dict[str, Any]) -> list[tuple[Any, Any]]:
    """Case-format fact entries as ``(Atom, Evidence)`` pairs for ``combine``."""
    from capcov.claims import Atom, Constant, Context, Evidence
    out = []
    for entry in entries:
        decl = decls[entry["relation"]]
        atom = Atom(decl.name, tuple(Constant(value, column.type)
                                     for value, column in zip(entry["args"], decl.columns)))
        out.append((atom, Evidence(entry["id"], atom, Context.from_mapping(entry["context"]), entry["source"],
                                   tuple(entry["provenance"]["depends_on"]), entry["kind"])))
    return out


def find_id(facts: list[dict[str, Any]], relation: str, **columns: Any) -> str:
    matches = [entry["id"] for entry in facts if entry["relation"] == relation
               and all(dict(zip(entry["arg_order"], entry["args"])).get(k) == v for k, v in columns.items())]
    if len(matches) != 1:
        raise LookupError(f"{relation} {columns}: {len(matches)} matches")
    return matches[0]


# ---------------------------------------------------------------------------
# claims, diagnostics and templates


def _claim(claim_id: str, relation: str, arg_order: list[str], args: list[Any], context: dict[str, Any],
           reading: str, diagnostics: list[dict[str, Any]] = ()) -> dict[str, Any]:
    return {"id": claim_id, "relation": relation, "arg_order": arg_order, "args": args, "context": context,
            "quantifier": "exists", "domain": None, "mappings": [], "diagnostics": list(diagnostics),
            "reading": reading}


def qualified_claim(op: str, reading: str, diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    return _claim(f"claim-qualified-{op.split('.')[1]}", "op_qualified", ["index", "run", "op"],
                  [INDEX, RUN, op], {"index": INDEX, "run": RUN}, reading, diagnostics)


def observation(trigger: str, context: list[str], predicate: dict[str, Any] | None = None,
                status: str = "complete") -> dict[str, Any]:
    out = {"trigger_relation": trigger, "effect": "observation", "operational_status": status,
           "context_indices": context}
    if predicate:
        out["predicate"] = predicate
    return out


# The witnesses every op_qualified claim weighs.  Each is made relevant to the
# claim by an observation diagnostic so a missing-premise template can be
# suppressed by the witness's presence (excludes_evidence).
WITNESS_DIAGNOSTICS = [observation("model_describes_run", ["run"]), observation("run_nonce_observed", []),
                       observation("snapshot_observed", []), observation("model_observed", []),
                       observation("php_post_states_closed", ["run"]), observation("go_post_states_closed", ["run"])]
WITNESS_REASONS = {
    "model_describes_run": "no model_describes_run witness binds the receipt's model to the run",
    "run_nonce_observed": "the reviewer did not observe the run's nonce",
    "snapshot_observed": "the reviewer did not observe the run's snapshot digest",
    "model_observed": "the reviewer did not observe the model digest",
    "php_post_states_closed": "the harness did not close the PHP post-state table for the run",
    "go_post_states_closed": "the harness did not close the Go post-state table for the run",
}


def missing(claim_id: str, relation: str, reason: str, *, excludes: list[str] = (),
            requires: list[str] = ()) -> dict[str, Any]:
    out = {"kind": "missing_premise", "claim_id": claim_id, "relation": relation,
           "fields": {"reason": {"value": reason}}, "when_claim": "unresolved"}
    if excludes:
        out["excludes_evidence"] = list(excludes)
    if requires:
        out["requires_all_evidence"] = list(requires)
    return out


def witness_templates(claim_id: str, facts: list[dict[str, Any]], *, absent: tuple[str, ...] = (),
                      override: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """One ``missing_premise`` template per witness: excluded by the witness row
    when the case carries it; absent witnesses get a template with no exclusion
    (nothing exists to name), so exactly the absent ones fire."""
    out = []
    override = override or {}
    for relation, reason in WITNESS_REASONS.items():
        if relation in override:
            out.append(override[relation])
            continue
        if relation in absent:
            out.append(missing(claim_id, relation, reason))
        else:
            out.append(missing(claim_id, relation, reason, excludes=[find_id(facts, relation)]))
    return out


def discrepancy(claim_id: str, kind: str, requires: list[str], **fields: Any) -> dict[str, Any]:
    values = {"kind": {"value": kind}, **{name: {"value": value} for name, value in fields.items()}}
    return {"kind": "discrepancy", "claim_id": claim_id, "when_claim": "supported", "fields": values,
            "requires_all_evidence": list(requires)}


# ---------------------------------------------------------------------------
# the cases


def _case(stem: str, title: str, seeded_fault: str | None, notes: list[str], facts: list[dict[str, Any]],
          claims: list[dict[str, Any]], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": 1, "id": stem, "title": title, "rule_pack": PACK_ID,
            "provenance": {"kind": "synthetic",
                           "source": "replay_facts.export_bundle over an edit of tests/claim_semantics/fixtures/replay_receipt_min",
                           "seeded_fault": seeded_fault},
            "context": {"run": RUN, "model": MODEL, "index": INDEX},
            "review_notes": notes, "facts": facts, "assumptions": [], "claims": claims, "outputs": outputs}


def _both_qualified(facts, readings, *, absent=(), extra_diagnostics=None, override=None):
    extra_diagnostics = extra_diagnostics or {}
    claims, outputs = [], []
    for op in OPS:
        claim = qualified_claim(op, readings[op], WITNESS_DIAGNOSTICS + extra_diagnostics.get(op, []))
        claims.append(claim)
        outputs.extend(witness_templates(claim["id"], facts, absent=absent,
                                         override=(override or {}).get(op)))
    return claims, outputs


def build_00() -> dict[str, Any]:
    with variant({}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts() + census_facts()
    claims, outputs = _both_qualified(facts, {
        CREATE: "issues.create is declared by the census, replayed (req-1, req-3), exercised with PHP/Go post-states "
                "the model admits, has no disagreement, no undeclared write and no surviving mutant (m-1 killed by req-1).",
        CLOSE: "issues.close is declared, replayed by req-2, agreed by PHP/Go/model, writes only the declared table "
               "and its mutant m-2 is killed by req-2."})
    notes = [
        "The receipt is the fixture unchanged: one run, two ops, three requests, PHP/Go/model agreeing row for row, "
        "two mutants both killed, every closure witness present.",
        "The reviewer observed the run's nonce, snapshot and model, and the PHP census declares both ops for the synthetic "
        "index; index_describes_replay binds that index to the run, which is the only static/runtime join in the pack.",
        "op_qualified support for issues.create uses req-1 (the canonical proof is the shortest, then lexically least, "
        "so req-1 is chosen over req-3 for replayed/op_exercised); leaves span the replay, php, go, shen, mut, "
        "reviewer and php-census producer classes.",
        "Every missing_premise template is excluded by the witness row it names, so none renders.",
    ]
    return _case("00-positive-control", "Positive control: both ops qualify from a clean receipt", None, notes,
                 facts, claims, outputs)


def build_01() -> dict[str, Any]:
    with variant({"php_post_state": _edit_row(1, state_digest=DISAGREEING_STATE)}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts() + census_facts()
    php_req2 = find_id(facts, "php_post_state", req="req-2")
    claims, outputs = _both_qualified(facts, {
        CREATE: "issues.create is untouched by the planted disagreement and qualifies as in the control.",
        CLOSE: "req-2's PHP post-state is not in the model's closed admissible set, so php_model_disagree derives, "
               "php_disagree_any(issues.close) holds and the negation in op_qualified_rt fails."},
        extra_diagnostics={CLOSE: [observation("php_post_state", ["run"],
                                               {"column": "req", "operator": "=", "value": "req-2"})]})
    outputs.append(missing("claim-qualified-close", "php_model_agree",
                           "the PHP post-state of req-2 lies outside the model's admissible set for issues.close",
                           requires=[php_req2]))
    companion = _claim("claim-php-disagrees-req-2", "php_model_disagree", ["run", "req", "state_digest"],
                       [RUN, "req-2", DISAGREEING_STATE], {"run": RUN},
                       "model_admissible is closed for the run and model and has no row with req-2's PHP digest.")
    claims.append(companion)
    outputs.append(discrepancy(companion["id"], "php-state-outside-model", [php_req2], req="req-2"))
    notes = [
        "php_post_state.json row 1 (req-2, issues.close) carries a digest the model's admissible set does not contain; "
        "everything else is the control.",
        "op_qualified(issues.close) is unresolved: the missing premise names php_model_agree for req-2, triggered by the "
        "disagreeing PHP row, while every witness template is excluded by its present witness.",
        "The companion php_model_disagree claim is supported from the PHP row, the model_describes_run witness and the "
        "model_admissible_closed witness; its discrepancy output renders php-state-outside-model.",
    ]
    return _case("01-planted-disagreement", "Planted PHP/model disagreement on issues.close", "php-state-outside-model",
                 notes, facts, claims, outputs)


def build_02() -> dict[str, Any]:
    audit = {"req": "req-2", "run": RUN, "table": "audit_log", "kind": "insert",
             "pk": hashlib.sha256(b"audit_log pk 1").hexdigest(),
             "cols_digest": hashlib.sha256(b"audit_log cols 1").hexdigest()}
    with variant({"go_effect": _append_row(**audit)}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts() + census_facts()
    go_audit = find_id(facts, "go_effect", table="audit_log")
    claims, outputs = _both_qualified(facts, {
        CREATE: "issues.create is untouched by the undeclared write and qualifies as in the control.",
        CLOSE: "Go wrote audit_log while serving req-2; model_writes is closed for (model, issues.close) and does not "
               "declare audit_log, so undeclared_write derives and undeclared_any(issues.close) blocks qualification."},
        extra_diagnostics={CLOSE: [observation("go_effect", ["run"],
                                               {"column": "table", "operator": "=", "value": "audit_log"})]})
    outputs.append(missing("claim-qualified-close", "model_writes",
                           "Go wrote table audit_log for issues.close, which the model's closed write set does not declare",
                           requires=[go_audit]))
    companion = _claim("claim-undeclared-audit-log", "undeclared_write", ["run", "op", "table"],
                       [RUN, CLOSE, "audit_log"], {"run": RUN},
                       "The go_effect row for req-2/audit_log joins the replay_request for issues.close and the closed "
                       "model_writes set that lacks audit_log.")
    claims.append(companion)
    outputs.append(discrepancy(companion["id"], "undeclared-table", [go_audit], table="audit_log"))
    notes = [
        "go_effect.json gains an insert into audit_log for req-2 (issues.close); model_writes still declares only issues "
        "for that op and model_writes_closed covers it.",
        "op_qualified(issues.close) is unresolved with model_writes as the missing premise, triggered by the audit_log "
        "row; op_qualified(issues.create) is supported.",
        "The companion undeclared_write claim is supported through the go rule; PHP wrote no audit_log row so the php "
        "rule contributes nothing.",
    ]
    return _case("02-planted-undeclared-write", "Go writes an undeclared table for issues.close", "undeclared-table",
                 notes, facts, claims, outputs)


def build_03() -> dict[str, Any]:
    with variant({"mutant_killed": _drop_row(1)}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts() + census_facts()
    m2 = find_id(facts, "mutant", mutant="m-2")
    claims, outputs = _both_qualified(facts, {
        CREATE: "issues.create keeps its killed mutant m-1 and qualifies as in the control.",
        CLOSE: "mutant m-2 of issues.close has no mutant_killed row while mutant_kills_closed is asserted, so "
               "surviving_mutant derives, op_has_surviving_mutant holds and corpus_constrains fails."},
        extra_diagnostics={CLOSE: [observation("mutant", [],
                                               {"column": "mutant", "operator": "=", "value": "m-2"})]})
    outputs.append(missing("claim-qualified-close", "mutant_killed",
                           "mutant m-2 of issues.close was never killed by a replayed request", requires=[m2]))
    companion = _claim("claim-m2-survives", "surviving_mutant", ["run", "op", "mutant"], [RUN, CLOSE, "m-2"],
                       {"run": RUN}, "mutants are closed for (model, issues.close), kills are closed for the run, and "
                                     "no mutant_killed_in(run, m-2) exists.")
    claims.append(companion)
    outputs.append(discrepancy(companion["id"], "mutant-not-killed", [m2], mutant="m-2"))
    notes = [
        "mutant_killed.json loses its m-2 row; mutant.json still declares m-2 for issues.close and the receipt still "
        "asserts mutant_kills closed.",
        "op_qualified(issues.close) is unresolved, missing premise mutant_killed (for m-2); issues.create is supported.",
        "The companion surviving_mutant claim is supported from the mutant row, model_describes_run, mutants_closed and "
        "mutant_kills_closed; the negated mutant_killed_in contributes no leaf.",
    ]
    return _case("03-surviving-mutant", "A mutant of issues.close survives the replay", "surviving-mutant",
                 notes, facts, claims, outputs)


def build_04() -> dict[str, Any]:
    with variant({}) as root:
        exported, _ = exported_facts(root, drop_relations=("model_describes_run",))
    facts = exported + reviewer_facts() + census_facts()
    claims, outputs = _both_qualified(facts, {
        CREATE: "Without model_describes_run no model-scoped relation joins the run: no agreement, no closure, no "
                "corpus, so op_qualified_rt cannot derive.",
        CLOSE: "As for issues.create: the model witness is the missing premise."},
        absent=("model_describes_run",))
    companion = _claim("claim-php-agrees-req-1", "php_model_agree", ["run", "req"], [RUN, "req-1"], {"run": RUN},
                       "Even plain agreement needs the compatibility witness; without it no php_model_* row exists.")
    claims.append(companion)
    outputs.append(missing(companion["id"], "model_describes_run", WITNESS_REASONS["model_describes_run"]))
    notes = [
        "The exported model_describes_run row is withheld; every other row of the control is present.",
        "Both op_qualified claims and the php_model_agree companion are unresolved with model_describes_run as the only "
        "missing premise; the three reviewer witness templates are excluded by their present rows.",
        "No php_model_agree, php_model_disagree, go_model_agree or go_model_disagree row derives (evaluation test).",
    ]
    return _case("04-missing-model-witness", "No model_describes_run witness", None, notes, facts, claims, outputs)


def build_05() -> dict[str, Any]:
    with variant({}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts(snapshot=None) + census_facts()
    reason = "the run's snapshot digest was not observed, so replay_run_current does not hold"
    override = {op: {"snapshot_observed": missing(f"claim-qualified-{op.split('.')[1]}", "replay_run_current", reason)}
                for op in OPS}
    claims, outputs = _both_qualified(facts, {
        CREATE: "replay_run_current needs run_nonce_observed, snapshot_observed and model_observed; the snapshot witness "
                "is absent, so every *_closed relation of the run is absent and op_qualified_rt cannot derive.",
        CLOSE: "As for issues.create."}, override=override)
    notes = [
        "The receipt is the control; the reviewer's snapshot_observed row is not added.",
        "Both op_qualified claims are unresolved with replay_run_current as the missing premise (reason: snapshot not "
        "observed); the model_describes_run, run_nonce_observed and model_observed templates are excluded by their rows.",
    ]
    return _case("05-missing-snapshot-witness", "No snapshot_observed witness", None, notes, facts, claims, outputs)


def build_06() -> dict[str, Any]:
    with variant({}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts(nonce=OTHER_NONCE) + census_facts()
    nonce_id = find_id(facts, "run_nonce_observed")
    reason = "the observed nonce differs from the run's nonce, so the replay is stale rather than current"
    override = {op: {"run_nonce_observed": missing(f"claim-qualified-{op.split('.')[1]}", "replay_run_current", reason,
                                                    requires=[nonce_id])} for op in OPS}
    claims, outputs = _both_qualified(facts, {
        CREATE: "run_nonce_observed names another nonce: replay_run_stale derives (operational status stale) and "
                "replay_run_current does not, so no closure and no qualification.",
        CLOSE: "As for issues.create."},
        extra_diagnostics={op: [observation("replay_run_stale", ["run"], status="stale")] for op in OPS},
        override=override)
    companion = _claim("claim-run-stale", "replay_run_stale", ["run", "nonce", "observed"],
                       [RUN, NONCE, OTHER_NONCE], {"run": RUN},
                       "replay_run and run_nonce_observed bind different digests and the comparison holds.")
    claims.append(companion)
    notes = [
        "The reviewer's run_nonce_observed row carries a nonce other than the receipt's.",
        "Both op_qualified claims are unresolved with operational status stale (diagnostic on replay_run_stale) and "
        "replay_run_current as the missing premise, triggered by the mismatching nonce row.",
        "The companion replay_run_stale claim is supported from the replay_run header and the nonce row.",
    ]
    return _case("06-stale-replay", "Observed nonce differs from the run's nonce", "stale-replay", notes, facts,
                 claims, outputs)


def build_08() -> dict[str, Any]:
    with variant({"mutant_killed": _edit_row(0, req="req-9")}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts() + census_facts()
    kill = find_id(facts, "mutant_killed", mutant="m-1")
    closed = find_id(facts, "mutant_kills_closed")
    reason = "mutant m-1 is recorded as killed by req-9, which is not a replayed request: the run's kill closure is contradicted"
    claims, outputs = _both_qualified(facts, {
        CREATE: "m-1 is recorded as killed by req-9, a request the closed replay_request set does not contain; "
                "kill_closure_gap derives, kill_closure_gap_any poisons every op of the run (the per-run "
                "mutant_kills_closed witness is demonstrably wrong) and the gate in op_qualified_rt fails.",
        CLOSE: "issues.close's own mutant m-2 is honestly killed by req-2, but its qualification rests on the same "
               "contradicted per-run kill closure, so it is unresolved too."},
        extra_diagnostics={op: [observation("mutant_killed", ["run"],
                                            {"column": "mutant", "operator": "=", "value": "m-1"})] for op in OPS})
    for op in OPS:
        outputs.append(missing(f"claim-qualified-{op.split('.')[1]}", "replay_request", reason, requires=[kill]))
    companion = _claim("claim-kill-outside-corpus", "kill_closure_gap", ["run", "mutant", "req"], [RUN, "m-1", "req-9"],
                       {"run": RUN}, "mutant_kills_closed and replay_requests_closed are both asserted, yet the kill "
                                     "names req-9 which requested/replay_request does not contain.")
    claims.append(companion)
    outputs.append(discrepancy(companion["id"], "kill-outside-replayed-requests", [kill, closed],
                               mutant="m-1", req="req-9"))
    notes = [
        "mutant_killed.json row 0 names req-9; replay_request.json is unchanged and the receipt still asserts "
        "replay_requests and mutant_kills closed.",
        "The kill_closure_gap claim is supported and its support includes the mutant_kills_closed witness that the "
        "harness should have withheld; that witness is listed under forbidden_leaves (seeded_fault "
        "lying-completeness-witness).",
        "Both op_qualified claims are unresolved: kill_gap_closed holds (kills and requests both closed) and "
        "kill_closure_gap_any(run, op) holds for every replayed op, so the contradiction gate fails; the missing "
        "premise names replay_request (the req-9 the kill relies on), triggered by the m-1 kill row.",
    ]
    return _case("08-lying-closure", "mutant_kills_closed asserted over a kill outside the replayed requests",
                 "lying-completeness-witness", notes, facts, claims, outputs)


def build_09() -> dict[str, Any]:
    with variant({"php_post_state": _drop_row(2)}) as root:
        exported, _ = exported_facts(root)
    facts = exported + reviewer_facts() + census_facts()
    req3 = find_id(facts, "replay_request", req="req-3")
    claims, outputs = _both_qualified(facts, {
        CREATE: "req-1 still agrees on both sides, so op_exercised(issues.create) holds; req-3's PHP post-state is "
                "omitted while php_post_states_closed is asserted, so post_state_gap(req-3, php) derives, "
                "post_state_any(issues.create) holds and the gate in op_qualified_rt fails.",
        CLOSE: "issues.close (req-2) is fully observed and qualifies as in the control."},
        extra_diagnostics={CREATE: [observation("replay_request", ["run"],
                                                {"column": "req", "operator": "=", "value": "req-3"})]})
    outputs.append(missing("claim-qualified-create", "php_post_state",
                           "req-3 of issues.create was replayed but the PHP runner reported no post-state for it",
                           requires=[req3]))
    companion = _claim("claim-req-3-php-post-state-gap", "post_state_gap", ["run", "req", "side"],
                       [RUN, "req-3", "php"], {"run": RUN},
                       "replay_request is closed and contains req-3; php_post_states_closed is asserted and no "
                       "php_post_state(run, req-3, _) exists.",
                       # the gap rule reads the request through the requested projection; the
                       # diagnostic makes the request row itself relevant to the discrepancy
                       [observation("replay_request", ["run"], {"column": "req", "operator": "=", "value": "req-3"})])
    claims.append(companion)
    outputs.append(discrepancy(companion["id"], "post-state-missing", [req3], req="req-3", side="php"))
    notes = [
        "php_post_state.json loses its req-3 row; receipt.json still asserts php_post_states closed and every other "
        "row of the control is present.",
        "Without the post-state gate, issues.create would qualify: req-1 satisfies op_exercised and the omitted req-3 "
        "is invisible to php_disagree_any.  With it, op_qualified(issues.create) is unresolved with php_post_state as "
        "the missing premise (for req-3); issues.close is supported.",
        "The companion post_state_gap claim is supported from the req-3 request row, replay_requests_closed and "
        "php_post_states_closed.",
    ]
    return _case("09-missing-post-state", "A replayed request of issues.create has no PHP post-state",
                 "post-state-omitted", notes, facts, claims, outputs)


def build_rejected_12() -> dict[str, Any]:
    case = build_00()
    case["id"] = "12-closure-producer-violation"
    case["title"] = "Positive control whose model_admissible_closed witness is emitted by the harness"
    case["provenance"]["seeded_fault"] = "closure-producer-violation"
    relabelled = 0
    for entry in case["facts"]:
        if entry["relation"] == "model_admissible_closed":
            entry["source"] = REJECTED_CLOSURE_SOURCE
            relabelled += 1
    assert relabelled == 1
    case["review_notes"] = [
        "The facts are the control's; only the model_admissible_closed witness names the replay class, i.e. the "
        "harness closing the model runner's admissible set on its behalf.",
        "load_case refuses the file (evidence-producer: model_admissible_closed admits shen); evaluated unvalidated "
        "both op_qualified verdicts would be supported (rejected.json).",
    ]
    return case


def build_rejected_07() -> dict[str, Any]:
    case = build_00()
    case["id"] = "07-producer-class-violation"
    case["title"] = "Positive control whose php_post_state rows claim the shen producer class"
    case["provenance"]["seeded_fault"] = "producer-class-violation"
    relabelled = 0
    for entry in case["facts"]:
        if entry["relation"] == "php_post_state":
            entry["source"] = REJECTED_SOURCE
            relabelled += 1
    assert relabelled == 3
    case["review_notes"] = [
        "The facts are the control's; only the three php_post_state evidence sources name the shen class.",
        "load_case refuses the file (evidence-producer); validate_bundle on the unvalidated bundle reports exactly three "
        "evidence-producer issues; the closure and both op_qualified verdicts are otherwise those of the control, which "
        "is why validation is the sole barrier (rejected.json).",
    ]
    return case


BUILDERS: dict[str, Callable[[], dict[str, Any]]] = {
    "00-positive-control": build_00,
    "01-planted-disagreement": build_01,
    "02-planted-undeclared-write": build_02,
    "03-surviving-mutant": build_03,
    "04-missing-model-witness": build_04,
    "05-missing-snapshot-witness": build_05,
    "06-stale-replay": build_06,
    "08-lying-closure": build_08,
    "09-missing-post-state": build_09,
}
REJECTED_BUILDERS: dict[str, Callable[[], dict[str, Any]]] = {
    "07-producer-class-violation": build_rejected_07,
    "12-closure-producer-violation": build_rejected_12,
}

# The reviewer's table: claim -> (verdict, status, missing-premise relations, discrepancy kinds).
REVIEW: dict[str, dict[str, tuple[str, str, list[str], list[str]]]] = {
    "00-positive-control": {"claim-qualified-create": ("supported", "complete", [], []),
                            "claim-qualified-close": ("supported", "complete", [], [])},
    "01-planted-disagreement": {"claim-qualified-create": ("supported", "complete", [], []),
                                "claim-qualified-close": ("unresolved", "complete", ["php_model_agree"], []),
                                "claim-php-disagrees-req-2": ("supported", "complete", [], ["php-state-outside-model"])},
    "02-planted-undeclared-write": {"claim-qualified-create": ("supported", "complete", [], []),
                                    "claim-qualified-close": ("unresolved", "complete", ["model_writes"], []),
                                    "claim-undeclared-audit-log": ("supported", "complete", [], ["undeclared-table"])},
    "03-surviving-mutant": {"claim-qualified-create": ("supported", "complete", [], []),
                            "claim-qualified-close": ("unresolved", "complete", ["mutant_killed"], []),
                            "claim-m2-survives": ("supported", "complete", [], ["mutant-not-killed"])},
    "04-missing-model-witness": {"claim-qualified-create": ("unresolved", "complete", ["model_describes_run"], []),
                                 "claim-qualified-close": ("unresolved", "complete", ["model_describes_run"], []),
                                 "claim-php-agrees-req-1": ("unresolved", "complete", ["model_describes_run"], [])},
    "05-missing-snapshot-witness": {"claim-qualified-create": ("unresolved", "complete", ["replay_run_current"], []),
                                    "claim-qualified-close": ("unresolved", "complete", ["replay_run_current"], [])},
    "06-stale-replay": {"claim-qualified-create": ("unresolved", "stale", ["replay_run_current"], []),
                        "claim-qualified-close": ("unresolved", "stale", ["replay_run_current"], []),
                        "claim-run-stale": ("supported", "complete", [], [])},
    "08-lying-closure": {"claim-qualified-create": ("unresolved", "complete", ["replay_request"], []),
                         "claim-qualified-close": ("unresolved", "complete", ["replay_request"], []),
                         "claim-kill-outside-corpus": ("supported", "complete", [], ["kill-outside-replayed-requests"])},
    "09-missing-post-state": {"claim-qualified-create": ("unresolved", "complete", ["php_post_state"], []),
                              "claim-qualified-close": ("supported", "complete", [], []),
                              "claim-req-3-php-post-state-gap": ("supported", "complete", [], ["post-state-missing"])},
}
# Evidence a derivation must not use, per case: the lying witness of 08.
FORBIDDEN: dict[str, Callable[[list[dict[str, Any]]], list[str]]] = {
    "08-lying-closure": lambda facts: [find_id(facts, "mutant_kills_closed")],
}


def build(stem: str) -> dict[str, Any]:
    """The case document without its ``expected`` table."""
    builders = {**BUILDERS, **REJECTED_BUILDERS}
    return builders[stem]()


def build_all() -> dict[str, dict[str, Any]]:
    return {stem: build(stem) for stem in BUILDERS}


def _dump(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _expected_table(case: dict[str, Any]) -> dict[str, Any]:
    """Evaluate the case with the Python kernel and check it against REVIEW."""
    from capcov.claims import bundle_from_json
    from capcov.claims.evaluator import evaluate
    from capcov.claims.output import VerifiedProofEvidence, relevant_evidence_ids, render_outputs

    try:
        from .adapter import bundle_payload
    except ImportError:
        from replay_rules.adapter import bundle_payload

    bundle = bundle_from_json(bundle_payload(case), validate=True)
    report = evaluate(bundle)
    if report.status.value != "complete":
        raise AssertionError(f"{case['id']}: {report.message}")
    ids = {record.id for record in bundle.evidence}
    forbidden = FORBIDDEN.get(case["id"], lambda facts: [])(case["facts"])
    table = {}
    for entry in report.claims:
        result = entry.result
        leaves = set(result.support) | set(result.refutation)
        proof = VerifiedProofEvidence.from_bundle(bundle, entry.claim.id, leaves) if leaves else None
        rendered = render_outputs(bundle, entry.claim.id, ids, proof, claim_state=result.semantic.value)
        discrepancies = [item["fields"] for item in rendered if item["kind"] == "discrepancy"]
        observed = relevant_evidence_ids(bundle, entry.claim.id, ids, leaves)
        review = REVIEW[case["id"]][entry.claim.id]
        actual = (result.semantic.value, result.operational.value,
                  sorted(item["relation"] for item in result.missing_premises),
                  sorted(item["kind"] for item in discrepancies))
        if actual != (review[0], review[1], sorted(review[2]), sorted(review[3])):
            raise AssertionError(f"{case['id']} {entry.claim.id}: evaluator says {actual}, reviewer says {review}")
        table[entry.claim.id] = {
            "semantic_verdict": result.semantic.value,
            "operational_status": result.operational.value,
            "support_leaves": sorted(result.support),
            "refutation_leaves": sorted(result.refutation),
            "observed_leaves": sorted(observed | leaves),
            "forbidden_leaves": sorted(leaf for leaf in forbidden if leaf in (observed | leaves)),
            "discrepancies": sorted(discrepancies, key=canonical_json),
            "missing_premises": sorted(result.missing_premises, key=canonical_json),
        }
    return {"claims": table}


def write_cases() -> None:
    expected = {"schema_version": 1, "description": "Per-claim reviewed expectations duplicated from each replay case",
                "rule_pack": PACK_ID,
                "evaluation_basis_by_quantifier": {"exists": "derivational", "forall": "bounded-history-model"},
                "cases": {}}
    for stem, case in build_all().items():
        case["expected"] = _expected_table(case)
        expected["cases"][stem] = case["expected"]
        _dump(CASES_DIR / f"{stem}.json", case)
    _dump(CASES_DIR.parent / "expected.json", expected)
    for stem, builder in REJECTED_BUILDERS.items():
        _dump(REJECTED_DIR / f"{stem}.json", builder())
    print(f"wrote {len(BUILDERS)} cases and {len(REJECTED_BUILDERS)} rejected case(s)")


if __name__ == "__main__":
    write_cases()
