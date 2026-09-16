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
static pilot records under ``runtime_join``.
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
                           OutputTemplate, TemplateValue, canonical_json)
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


def receipt_dir() -> Path | None:
    value = os.environ.get(RECEIPT_DIR_ENV)
    return Path(value) if value else None


def _row_id(prefix: str, segment: str, relation: str, row: list[Any]) -> str:
    return f"{prefix}:{segment}:{relation}:{replay_facts.row_digest(relation, row)[:12]}"


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
    claims, diagnostics, outputs = [], [], []
    for op in ops:
        qualified = Claim("op_qualified", (Constant(SYNTHETIC_INDEX, "digest"), Constant(run, "symbol"), Constant(op, "symbol")),
                          Context.from_mapping({"index": SYNTHETIC_INDEX, "run": run}), id=join.claim_id("qualified", op))
        constrains = Claim("corpus_constrains", (Constant(run, "symbol"), Constant(op, "symbol")),
                           Context.from_mapping({"run": run}), id=join.claim_id("corpus-constrains", op))
        claims.extend([qualified, constrains])
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
    """What the static pilot records under ``runtime_join``."""
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
    for op in join.ops:
        constrains = join.verdict(join.claim_id("corpus-constrains", op)) or {}
        qualified = join.verdict(join.claim_id("qualified", op)) or {}
        out[op] = {"corpus_constrains": constrains.get("semantic") == "supported",
                   "op_qualified": qualified.get("semantic"),
                   "operational": qualified.get("operational"),
                   "missing_premise": [json.loads(item)["relation"] if item.startswith("{") else item
                                       for item in qualified.get("missing_premises", [])]}
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
           "summary", "write_artifacts"]
