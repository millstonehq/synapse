"""The runtime half of the target-go pilot: judge a real replay receipt with the replay pack.

``build`` exports the receipt directory named by ``CAPCOV_REPLAY_RECEIPT_DIR``
(``replay_facts.export_bundle``; a refusal is a *contract finding* the caller
reports, never something to work around), combines it with
``rules-replay-v1`` and the claim-time rows a judge adds, and states two claims
per replayed op: ``op_qualified(index, run, op)`` and
``corpus_constrains(run, op)``.  Until a PHP SCIP census exists, the
``op_declared`` rows and the ``index_describes_replay`` witness are labelled
*assumptions* (``Evidence.kind == "assumption"``, ids ``<prefix>:assumed:...``)
under a synthetic index digest; their sources name the class the schema
requires and say they are reviewer assumptions.  ``summary`` is what the
static pilot records under ``replay_join``.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SRC = Path(__file__).resolve().parents[3] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capcov.claims import (Atom, Bundle, Claim, Constant, Context, DiagnosticRule, Evidence,  # noqa: E402
                           OutputTemplate, TemplateValue, Variable, canonical_json)
from capcov.claims.differential import DifferentialMismatch, compare  # noqa: E402
from capcov.claims.replay import replay_facts  # noqa: E402
from capcov.claims.static.certificate import certify, claim_conclusions, recheck  # noqa: E402
from capcov.claims.static.combine import combine  # noqa: E402

try:
    from ..replay_rules.adapter import pack_bundle
except ImportError:  # unittest discover -s imports this directory as top-level
    from replay_rules.adapter import pack_bundle

RECEIPT_DIR_ENV = "CAPCOV_REPLAY_RECEIPT_DIR"
OUT_ENV = "CAPCOV_TARGET_GO_REPLAY_OUT"
SYNTHETIC_INDEX = hashlib.sha256(b"target-go replay pilot: synthetic PHP census index pending a SCIP census").hexdigest()
REVIEWER_SOURCE = "reviewer claim-time observation"
CENSUS_ASSUMPTION_SOURCE = "php-census assumed by the reviewer pending the PHP SCIP census"
INDEX_ASSUMPTION_SOURCE = "reviewer assumed: synthetic census index pending the PHP SCIP census"
MODEL_WITNESSES = ("model_describes_run", "model_observed", "model_admissible_closed")
REASONS = {
    "model_describes_run": "no model runner vouched that a model describes the run",
    "model_observed": "the receipt names no model, so the reviewer has no model digest to observe",
    "model_admissible_closed": "the receipt names no model, so no admissible-state set is closed",
}
UNDECLARED_REASON = "blocked by undeclared writes: PHP or Go wrote a table the model's closed write set does not declare for this op"
# The premises op_qualified_rt needs, in the order a reviewer checks them; the
# first one that fails (or the first "any" that holds) is the blocking premise.
_BLOCKING_ORDER = (
    ("replay_run_current", False), ("model_describes_run", False), ("replayed", False), ("op_exercised", False),
    ("corpus_constrains", False), ("php_disagreement_closed", False), ("php_disagree_any", True),
    ("go_disagreement_closed", False), ("go_disagree_any", True), ("undeclared_writes_closed", False),
    ("undeclared_any", True), ("post_state_gap_closed", False), ("post_state_any", True),
    ("kill_gap_closed", False), ("kill_closure_gap_any", True), ("index_describes_replay", False),
    ("op_declared", False),
)


def receipt_dir() -> Path | None:
    value = os.environ.get(RECEIPT_DIR_ENV)
    return Path(value) if value else None


def _row_id(prefix: str, segment: str, relation: str, row: list[Any]) -> str:
    return f"{prefix}:{segment}:{relation}:{replay_facts.row_digest(relation, row)[:12]}"


def _values(decls, relation: str, row) -> dict[str, Any]:
    return dict(zip((column.name for column in decls[relation].columns), row))


def undeclared_tables(relations, decls, run: str, op: str) -> dict[str, list[str]]:
    """Per side, the tables ``undeclared_write(run, op, _)`` names that that side wrote for a request of ``op``."""
    rows = dict(relations) if not isinstance(relations, dict) else relations
    undeclared = {r[2] for r in rows.get("undeclared_write", ()) if r[0] == run and r[1] == op}
    requests = {r[1] for r in rows.get("replay_request", ()) if r[0] == run and r[4] == op}
    out = {}
    for side in ("php", "go"):
        written = {r[2] for r in rows.get(f"{side}_effect", ()) if r[0] == run and r[1] in requests}
        out[side] = sorted(undeclared & written)
    return out


def blocking_premise(relations, run: str, op: str, index: str = SYNTHETIC_INDEX) -> dict[str, Any] | None:
    """The first premise of op_qualified that blocks ``op`` in ``run``, or ``None`` when it is qualified."""
    rows = dict(relations) if not isinstance(relations, dict) else relations
    if any(r[0] == index and r[1] == run and r[2] == op for r in rows.get("op_qualified", ())):
        return None

    def holds(name: str) -> bool:
        for r in rows.get(name, ()):
            if name == "op_declared" and r == (index, op):
                return True
            if name == "index_describes_replay" and r == (index, run):
                return True
            if name in ("replay_run_current", "kill_gap_closed") and r == (run,):
                return True
            if name == "model_describes_run" and r[1] == run:
                return True
            if r[:2] == (run, op):
                return True
        return False

    for name, is_blocker in _BLOCKING_ORDER:
        present = holds(name)
        if is_blocker and present:
            return {"relation": name, "holds": True}
        if not is_blocker and not present:
            return {"relation": name, "holds": False}
    return {"relation": "op_qualified_rt", "holds": False}


def _fact(decls, relation: str, values: dict[str, Any], evidence_id: str, source: str, *,
          kind: str = "fact", depends_on=()) -> tuple[Atom, Evidence]:
    decl = decls[relation]
    atom = Atom(relation, tuple(Constant(values[column.name], column.type) for column in decl.columns))
    context = {name: values[name] for name in decl.context_indices}
    return atom, Evidence(evidence_id, atom, Context.from_mapping(context), source, tuple(depends_on), kind)


@dataclass
class ReplayJoin:
    receipt_dir: Path
    receipt: dict[str, Any]
    run: str
    exported: Any
    contract_findings: list[str] = field(default_factory=list)
    bundle: Bundle | None = None
    ops: tuple[str, ...] = ()
    index: str = SYNTHETIC_INDEX
    assumption_ids: tuple[str, ...] = ()
    result: Any = None
    mismatch: Any = None
    certificates: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def model_absent(self) -> bool:
        return not self.receipt.get("model")

    def claim_id(self, kind: str, op: str) -> str:
        return f"claim-{kind}-{op}"

    def report(self):
        return self.result.python if self.result is not None else (self.mismatch.python if self.mismatch else None)

    def verdict(self, claim_id: str) -> dict[str, Any] | None:
        report = self.report()
        if report is None:
            return None
        claim = next((c for c in report.claims if c.key == claim_id), None)
        if claim is None:
            return None
        return {"semantic": claim.semantic, "operational": claim.operational,
                "missing_premises": list(claim.missing_premises)}


def build(directory: Path) -> ReplayJoin:
    receipt = json.loads((directory / replay_facts.RECEIPT_FILE).read_text(encoding="utf-8"))
    run = receipt["run"]
    exported = replay_facts.export_bundle(directory, run=run)
    join = ReplayJoin(directory, receipt, run, exported)
    if exported.status != replay_facts.STATUS_COMPLETE:
        join.contract_findings = [f"exporter refused the receipt ({exported.status}): {m}" for m in exported.messages]
        return join
    pack = pack_bundle()
    decls = {decl.name: decl for decl in (*exported.bundle.relations, *pack.relations)}
    ops = tuple(sorted({fact.terms[4].value for fact in exported.bundle.facts if fact.relation == "replay_request"}))
    join.ops = ops
    additions = [
        _fact(decls, "run_nonce_observed", {"run": run, "nonce": receipt["nonce"]},
              _row_id("reviewer", "claim-time", "run_nonce_observed", [run, receipt["nonce"]]), REVIEWER_SOURCE),
        _fact(decls, "snapshot_observed", {"snapshot": receipt["snapshot"]},
              _row_id("reviewer", "claim-time", "snapshot_observed", [receipt["snapshot"]]), REVIEWER_SOURCE),
    ]
    if not join.model_absent:  # the strict exporter never exports an empty model; kept for the summary
        additions.append(_fact(decls, "model_observed", {"model": receipt["model"]},
                               _row_id("reviewer", "claim-time", "model_observed", [receipt["model"]]), REVIEWER_SOURCE))
    assumptions = [_fact(decls, "index_describes_replay", {"index": SYNTHETIC_INDEX, "run": run},
                         _row_id("reviewer", "assumed", "index_describes_replay", [SYNTHETIC_INDEX, run]),
                         INDEX_ASSUMPTION_SOURCE, kind="assumption", depends_on=[f"external:index:{SYNTHETIC_INDEX}"])]
    for op in ops:
        assumptions.append(_fact(decls, "op_declared", {"index": SYNTHETIC_INDEX, "op": op},
                                 _row_id("php", "assumed", "op_declared", [SYNTHETIC_INDEX, op]),
                                 CENSUS_ASSUMPTION_SOURCE, kind="assumption",
                                 depends_on=[f"external:index:{SYNTHETIC_INDEX}"]))
    join.assumption_ids = tuple(record.id for _, record in assumptions)
    present = {record.atom.relation: record.id for record in exported.bundle.evidence
               if record.atom.relation in MODEL_WITNESSES}
    present.update({record.atom.relation: record.id for _, record in additions if record.atom.relation in MODEL_WITNESSES})
    # the effect rows the model's closed write set does not cover, per op (what
    # the undeclared_write rules will derive from), so the why-not can name them
    exported_rows = {name: [] for name in ("replay_request", "php_effect", "go_effect", "model_writes", "model_writes_closed")}
    evidence_of: dict[tuple[str, tuple], str] = {}
    for record in exported.bundle.evidence:
        if record.atom.relation in exported_rows:
            row = tuple(term.value for term in record.atom.terms)
            exported_rows[record.atom.relation].append(row)
            evidence_of[(record.atom.relation, row)] = record.id
    declared = {(r[1], r[2]) for r in exported_rows["model_writes"]}
    closed_ops = {r[1] for r in exported_rows["model_writes_closed"]}
    claims, diagnostics, outputs = [], [], []
    for op in ops:
        qualified = Claim("op_qualified", (Constant(SYNTHETIC_INDEX, "digest"), Constant(run, "symbol"), Constant(op, "symbol")),
                          Context.from_mapping({"index": SYNTHETIC_INDEX, "run": run}), id=join.claim_id("qualified", op))
        constrains = Claim("corpus_constrains", (Constant(run, "symbol"), Constant(op, "symbol")),
                           Context.from_mapping({"run": run}), id=join.claim_id("corpus-constrains", op))
        undeclared = Claim("undeclared_write", (Constant(run, "symbol"), Constant(op, "symbol"), Variable("table")),
                           Context.from_mapping({"run": run}), id=join.claim_id("undeclared-write", op))
        claims.extend([qualified, constrains, undeclared])
        requests = {r[1] for r in exported_rows["replay_request"] if r[4] == op}
        offending = [evidence_of[(side, row)] for side in ("php_effect", "go_effect") for row in exported_rows[side]
                     if row[1] in requests and op in closed_ops and (op, row[2]) not in declared]
        if offending:
            for side in ("php_effect", "go_effect"):
                diagnostics.append(DiagnosticRule(side, "observation", "complete", ("run",), claim_id=qualified.id))
            outputs.append(OutputTemplate(
                "missing_premise", qualified.id, relation="model_writes",
                fields=(("reason", TemplateValue("constant", "", "symbol", UNDECLARED_REASON)),),
                requires_any_evidence=tuple(sorted(offending)), when_claim="unresolved"))
        for relation in MODEL_WITNESSES:
            context = ("run",) if relation != "model_observed" else ()
            diagnostics.append(DiagnosticRule(relation, "observation", "complete", context, claim_id=qualified.id))
            excludes = (present[relation],) if relation in present else ()
            outputs.append(OutputTemplate(
                "missing_premise", qualified.id, relation=relation,
                fields=(("reason", TemplateValue("constant", "", "symbol", REASONS[relation])),),
                excludes_evidence=excludes, when_claim="unresolved"))
    join.bundle = combine(
        exported.bundle, pack,
        facts=[atom for atom, _ in (*additions, *assumptions)],
        evidence=[record for _, record in (*additions, *assumptions)],
        claims=claims, diagnostics=diagnostics, outputs=outputs,
        metadata={"experiment": "target-go replay receipt join (Phase 4, judge side)",
                  "synthetic_index": SYNTHETIC_INDEX, "model_absent": join.model_absent,
                  "assumptions": list(join.assumption_ids)})
    return join


def evaluate_join(join: ReplayJoin, replay_root: str) -> ReplayJoin:
    """Run both kernels and certify every corpus_constrains / op_qualified row from both closures."""
    if join.bundle is None:
        return join
    try:
        join.result = compare(join.bundle, replay_root=replay_root)
    except DifferentialMismatch as exc:
        join.mismatch = exc.result
        return join
    for claim in join.bundle.claims:
        rows = claim_conclusions(join.bundle, join.result.python.relations, claim)
        if rows != claim_conclusions(join.bundle, join.result.souffle.relations, claim):
            raise AssertionError(f"{claim.id}: the kernels disagree on the claim rows")
        for row in rows:
            from_python = certify(join.bundle, join.result.python.relations, claim.relation, row)
            from_souffle = certify(join.bundle, join.result.souffle.relations, claim.relation, row)
            if from_python != from_souffle:
                raise AssertionError(f"{claim.id}: certificates differ between closures")
            for relations in (join.result.python.relations, join.result.souffle.relations):
                checked = recheck(join.bundle, from_python, relations)
                if not checked.ok:
                    raise AssertionError(f"{claim.id}: recheck failed: {checked}")
            join.certificates[claim.id] = from_python
    return join


def summary(join: ReplayJoin) -> dict[str, Any]:
    """What the static pilot records under ``replay_join``."""
    if join.bundle is None:
        return {"status": "blocked", "run": join.run, "receipt": join.receipt_dir.name,
                "contract_findings": list(join.contract_findings)}
    out: dict[str, Any] = {
        "status": "complete" if join.result is not None and join.result.matched else "kernel-mismatch",
        "run": join.run,
        "replay_identity": dict(join.exported.bundle.metadata)["replay_digest"],
        "replay_bundle_digest": replay_facts.bundle_digest(join.exported.bundle),
        "combined_bundle_digest": replay_facts.bundle_digest(join.bundle),
        "model_absent": join.model_absent,
        "synthetic_index": SYNTHETIC_INDEX,
        "assumptions": list(join.assumption_ids),
        "ops": list(join.ops),
    }
    relations = dict(join.report().relations) if join.report() is not None else {}
    for op in join.ops:
        constrains = join.verdict(join.claim_id("corpus-constrains", op)) or {}
        qualified = join.verdict(join.claim_id("qualified", op)) or {}
        undeclared = join.verdict(join.claim_id("undeclared-write", op)) or {}
        blocking = blocking_premise(relations, join.run, op) if relations else None
        tables = undeclared_tables(relations, None, join.run, op) if relations else {}
        entry = {"corpus_constrains": constrains.get("semantic") == "supported",
                 "op_qualified": qualified.get("semantic"),
                 "operational": qualified.get("operational"),
                 # template-rendered absent leaves; the evaluator's claim-id fallback is never reported here
                 "missing_premise": [json.loads(item)["relation"] for item in qualified.get("missing_premises", [])
                                     if item.startswith("{")],
                 "undeclared_write": undeclared.get("semantic"),
                 "blocking_premise": blocking}
        if blocking and blocking["relation"] == "undeclared_any":
            entry["blocked_by"] = "blocked by undeclared writes: " + json.dumps(tables, sort_keys=True)
            entry["undeclared_tables"] = tables
        out[op] = entry
    return out


def write_artifacts(join: ReplayJoin, out_dir: Path) -> dict[str, Any]:
    """Digests, counts and verdicts only; no source text and no local paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    receipts = join.receipt.get("receipts", {})
    digests_only = {k: v for k, v in receipts.items()
                    if isinstance(v, (int, bool)) or (isinstance(v, str) and k.endswith("sha256"))
                    or k in {"canonicalizer", "recorded_at"}}
    document = {
        "pilot": "target-go replay receipt join (Phase 4, judge side)",
        "receipt": {"run": join.run, "nonce": join.receipt.get("nonce"), "snapshot": join.receipt.get("snapshot"),
                    "model": join.receipt.get("model"), "php_commit": join.receipt.get("php_commit"),
                    "go_commit": join.receipt.get("go_commit"), "closed": join.receipt.get("closed"),
                    "receipts": digests_only},
        "export": {"status": join.exported.status, "row_counts": dict(join.exported.counts),
                   "messages": [m for m in join.exported.messages if "receipt directory" not in m]},
        "contract_findings": list(join.contract_findings),
        "join": summary(join),
        "kernels": None if join.result is None and join.mismatch is None else {
            "matched": join.result is not None and join.result.matched,
            "python_digest": join.report().canonical_digest,
            "souffle_digest": (join.result.souffle if join.result else join.mismatch.souffle).canonical_digest},
        "certificates": {claim_id: {"sha256": hashlib.sha256(canonical_json(cert).encode()).hexdigest(),
                                    "leaves": len(cert["leaves"]), "nodes": cert["nodes"], "truncated": cert["truncated"]}
                         for claim_id, cert in join.certificates.items()},
    }
    for claim_id, cert in join.certificates.items():
        (out_dir / f"certificate-{claim_id}.json").write_text(json.dumps(cert, indent=1, sort_keys=True) + "\n",
                                                              encoding="utf-8")
    (out_dir / "receipt.json").write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return document


__all__ = ["RECEIPT_DIR_ENV", "OUT_ENV", "SYNTHETIC_INDEX", "ReplayJoin", "receipt_dir", "build", "evaluate_join",
           "summary", "write_artifacts", "blocking_premise", "undeclared_tables"]
