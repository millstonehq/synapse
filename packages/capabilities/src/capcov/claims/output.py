"""Evaluator-independent conditional diagnostic output rendering."""
from __future__ import annotations

from typing import Any, Mapping

from .ir import Bundle, Claim, Constant, Evidence, EvidenceMapping, OutputKind, OutputTemplate


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


def _triggered(output: OutputTemplate, active: set[str], claim_state: str | None) -> bool:
    if not set(output.requires_all_evidence).issubset(active):
        return False
    if output.requires_any_evidence and not set(output.requires_any_evidence) & active:
        return False
    if set(output.excludes_evidence) & active:
        return False
    return output.when_claim in (None, "always") or output.when_claim == claim_state


def _relevant(bundle: Bundle, claim_id: str, evidence_id: str, derived: set[str]) -> bool:
    evidence = next((item for item in bundle.evidence if item.id == evidence_id), None)
    claim = _claim(bundle, claim_id)
    if evidence is None or claim is None:
        return False
    for mapping in bundle.mappings:
        if mapping.claim_id != claim_id or mapping.evidence_relation != evidence.atom.relation:
            continue
        values = _evidence_values(bundle, evidence_id)
        claim_relation = next((r for r in bundle.relations if r.name == claim.relation), None)
        claim_values = {c.name: t.value for c, t in zip(claim_relation.columns, claim.terms) if isinstance(t, Constant)} if claim_relation else {}
        if all(claim_values.get(left) == values.get(right) for left, right in mapping.bindings):
            return True
    for diagnostic in bundle.diagnostics:
        if diagnostic.claim_id == claim_id and diagnostic.trigger_relation == evidence.atom.relation:
            return True
    if evidence_id in derived:
        return any(rule.head.relation == claim.relation and any(atom.relation == evidence.atom.relation for atom in rule.body) for rule in bundle.rules)
    return False


def render_outputs(bundle: Bundle, claim_id: str, active_evidence: set[str] | frozenset[str], derived_evidence: set[str] | frozenset[str] = frozenset(), claim_state: str | None = None, missing_relations: set[str] | frozenset[str] = frozenset()) -> tuple[dict[str, Any], ...]:
    """Render active, typed output templates for one claim deterministically."""
    active = set(active_evidence)
    derived = set(derived_evidence)
    rendered = []
    for output in bundle.outputs:
        if output.claim_id != claim_id or not _triggered(output, active, claim_state):
            continue
        if output.evidence_id and (output.evidence_id not in active or not _relevant(bundle, claim_id, output.evidence_id, derived)):
            continue
        if output.kind == OutputKind.MISSING_PREMISE and output.relation not in set(missing_relations) and not output.causal_missing:
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
                if not evidence_id or evidence_id not in active or not _relevant(bundle, claim_id, evidence_id, derived):
                    break
                value = _evidence_values(bundle, evidence_id).get(template.column)
            fields[name] = value
        else:
            if fields:
                item["fields"] = dict(sorted(fields.items()))
            rendered.append(item)
    unique = {repr(item): item for item in rendered}
    return tuple(unique[key] for key in sorted(unique))
