"""Evaluator-independent conditional diagnostic output rendering."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .ir import Bundle, Claim, Constant, Evidence, EvidenceMapping, OutputKind, OutputTemplate


@dataclass(frozen=True)
class VerifiedProofEvidence:
    """Evaluator-issued ground proof leaves; not a certificate verifier."""
    claim_id: str
    leaf_ids: frozenset[str]
    claim_row_digest: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, str) or not self.claim_id:
            raise ValueError("verified proof requires a claim id")
        object.__setattr__(self, "leaf_ids", frozenset(self.leaf_ids))

    @classmethod
    def from_bundle(cls, bundle: Bundle, claim_id: str, leaf_ids: set[str] | frozenset[str], claim_row_digest: str | None = None) -> "VerifiedProofEvidence":
        known = {record.id for record in bundle.evidence}
        unknown = set(leaf_ids) - known
        if unknown:
            raise ValueError(f"unknown proof leaves: {sorted(unknown)}")
        if not any(claim.id == claim_id for claim in bundle.claims):
            raise ValueError(f"unknown proof claim: {claim_id}")
        return cls(claim_id, frozenset(leaf_ids), claim_row_digest)


def _claim(bundle: Bundle, claim_id: str) -> Claim | None:
    return next((claim for claim in bundle.claims if claim.id == claim_id), None)


def _evidence_values(bundle: Bundle, evidence_id: str) -> dict[str, Any]:
    record = next((item for item in bundle.evidence if item.id == evidence_id), None)
    if record is None:
        return {}
    relation = next((item for item in bundle.relations if item.name == record.atom.relation), None)
    values = {"id": evidence_id}
    if relation:
        for column, term in zip(relation.columns, record.atom.terms):
            if isinstance(term, Constant):
                values[column.name] = term.value
    return values


def _predicate_matches(value: Any, operator: str, expected: Any) -> bool:
    if operator == "=": return value == expected
    if operator == "!=": return value != expected
    if operator == "in": return value in expected if isinstance(expected, (list, tuple)) else False
    if operator == "not-in": return value not in expected if isinstance(expected, (list, tuple)) else False
    return False


def _relevant(bundle: Bundle, claim_id: str, evidence_id: str, proof: set[str]) -> bool:
    evidence = next((item for item in bundle.evidence if item.id == evidence_id), None)
    claim = _claim(bundle, claim_id)
    if evidence is None or claim is None:
        return False
    values = _evidence_values(bundle, evidence_id)
    claim_context = claim.context.as_dict()
    for mapping in bundle.mappings:
        if mapping.claim_id != claim_id or mapping.evidence_relation != evidence.atom.relation:
            continue
        if any(evidence.context.as_dict().get(index) != claim_context.get(index) for index in mapping.context_indices):
            continue
        claim_relation = next((r for r in bundle.relations if r.name == claim.relation), None)
        claim_values = {c.name: t.value for c, t in zip(claim_relation.columns, claim.terms) if isinstance(t, Constant)} if claim_relation else {}
        if all(claim_values.get(left) == values.get(right) for left, right in mapping.bindings):
            return True
    for diagnostic in bundle.diagnostics:
        if diagnostic.claim_id != claim_id or diagnostic.trigger_relation != evidence.atom.relation or diagnostic.when_missing:
            continue
        if any(evidence.context.as_dict().get(index) != claim_context.get(index) for index in diagnostic.context_indices):
            continue
        predicate = dict(diagnostic.predicate)
        if predicate and not _predicate_matches(values.get(predicate.get("column")), predicate.get("operator"), predicate.get("value")):
            continue
        return True
    if evidence_id in proof:
        claim_context = claim.context.as_dict()
        if any(evidence.context.as_dict().get(name) != value for name, value in claim_context.items() if name in evidence.context.as_dict()):
            return False
        claim_relation = next((r for r in bundle.relations if r.name == claim.relation), None)
        claim_values = {column.name: term.value for column, term in zip(claim_relation.columns, claim.terms) if isinstance(term, Constant)} if claim_relation else {}
        if any(name in values and values[name] != value for name, value in claim_values.items()):
            return False
        return any(rule.head.relation == claim.relation and any(atom.relation == evidence.atom.relation for atom in rule.body) for rule in bundle.rules)
    return False


def relevant_evidence_ids(bundle: Bundle, claim_id: str,
                          active_evidence: set[str] | frozenset[str],
                          proof_evidence: set[str] | frozenset[str] = frozenset()) -> set[str]:
    """Return active Evidence ids scoped to one claim's causal declarations."""
    proof = set(proof_evidence)
    return {evidence_id for evidence_id in active_evidence
            if _relevant(bundle, claim_id, evidence_id, proof)}


def output_triggered(output: OutputTemplate, relevant: set[str],
                     claim_state: str | Iterable[str] | None) -> bool:
    """Apply every declarative output condition to a reviewed evidence set."""
    if not set(output.requires_all_evidence).issubset(relevant):
        return False
    if output.requires_any_evidence and not set(output.requires_any_evidence) & relevant:
        return False
    if set(output.excludes_evidence) & relevant:
        return False
    states = ({claim_state} if isinstance(claim_state, str)
              else set(claim_state or ()))
    return output.when_claim in (None, "always") or output.when_claim in states


def render_outputs(bundle: Bundle, claim_id: str, active_evidence: set[str] | frozenset[str], proof_evidence: VerifiedProofEvidence | None = None, claim_state: str | None = None, missing_relations: set[str] | frozenset[str] = frozenset()) -> tuple[dict[str, Any], ...]:
    """Render active, typed output templates for one claim deterministically."""
    active = set(active_evidence)
    if proof_evidence is not None and not isinstance(proof_evidence, VerifiedProofEvidence):
        raise TypeError("proof_evidence must be VerifiedProofEvidence")
    if proof_evidence is not None and proof_evidence.claim_id != claim_id:
        raise ValueError("proof claim does not match rendered claim")
    known_ids = {record.id for record in bundle.evidence}
    if proof_evidence and not proof_evidence.leaf_ids.issubset(known_ids):
        raise ValueError("proof contains unknown evidence leaves")
    proof = set(proof_evidence.leaf_ids) if proof_evidence else set()
    relevant = relevant_evidence_ids(bundle, claim_id, active, proof)
    rendered = []
    for output in bundle.outputs:
        if output.claim_id != claim_id or not output_triggered(output, relevant, claim_state):
            continue
        if output.evidence_id and output.evidence_id not in relevant:
            continue
        if output.kind == OutputKind.MISSING_PREMISE and output.relation not in set(missing_relations):
            continue
        item: dict[str, Any] = {"kind": output.kind.value, "claim_id": output.claim_id}
        if output.evidence_id:
            item["evidence_id"] = output.evidence_id
        if output.relation:
            item["relation"] = output.relation
        fields = {}
        claim = _claim(bundle, claim_id)
        claim_values = {}
        if claim:
            relation = next((r for r in bundle.relations if r.name == claim.relation), None)
            if relation:
                claim_values = {column.name: term.value for column, term in zip(relation.columns, claim.terms) if isinstance(term, Constant)}
        for name, template in output.fields:
            if template.source == "constant":
                value = template.value
            elif template.source == "claim":
                value = claim_values.get(template.column)
            else:
                evidence_id = template.evidence_id or output.evidence_id
                if not evidence_id or evidence_id not in relevant:
                    break
                value = _evidence_values(bundle, evidence_id).get(template.column)
            fields[name] = value
        else:
            if fields:
                item["fields"] = dict(sorted(fields.items()))
            rendered.append(item)
    unique = {repr(item): item for item in rendered}
    return tuple(unique[key] for key in sorted(unique))
