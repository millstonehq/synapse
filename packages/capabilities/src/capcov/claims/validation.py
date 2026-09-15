"""Static validation for the restricted, finite claim-rule language."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .ir import (Aggregation, Atom, Bundle, Claim, Comparison, Constant,
                 RelationDecl, Rule, TypeName, Variable, Evidence, EvidenceMapping, DiagnosticRule, EvidenceEffect, OutputTemplate, OutputKind, canonical_json)

DIAGNOSTIC_VOCABULARY = frozenset({"same_surface", "row_committed", "mail_sent", "same_context", "independent_support", "all_compatible_histories_agree", "model_complete", "sql_terminal_ack", "no_resend_forever"})

# These names are identity/correlation dimensions in the frozen Stage B
# contract.  A support/refutation mapping is not aggregation authority and may
# not silently project them away when both relations carry them.
_CAUSAL_IDENTITY_COLUMNS = frozenset({
    "tenant", "actor", "run", "request", "event", "notification",
    "recipient", "message", "attempt", "interval", "environment",
    "configuration", "candidate_build", "reference_build", "source_digest",
    "model_digest",
})

# The reviewed bounded-history domain carries an explanatory outcome label in
# addition to its ``history`` member key. It is payload, not another identity
# that the Boolean aggregate source must duplicate.
_AGGREGATE_DOMAIN_PAYLOAD_COLUMNS = frozenset({("compatible_history", "outcome")})

# Static identity omission is an exact schema fingerprint, never a naming
# convention.  Section 29 declares only source_tree_observed as genuinely
# context-free; tenant/event/surface keyed legacy observations still need an
# index because those payloads do not identify the source snapshot.
_CONTEXT_FREE_STATIC_DECLARATIONS = frozenset({
    ("source_tree_observed", (("tree_digest", TypeName.DIGEST, False),), ()),
})


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str = ""
    def __str__(self): return f"{self.code}: {self.message}" + (f" ({self.path})" if self.path else "")


class ValidationError(ValueError):
    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(map(str, self.issues)))


def _variables(term): return {term.name} if isinstance(term, Variable) else set()
def _atom_vars(atom): return set().union(*(_variables(t) for t in atom.terms)) if atom.terms else set()
def _ground_atom_key(atom):
    values = tuple(term.value if isinstance(term, Constant) else None for term in atom.terms)
    return atom.relation, canonical_json(values)


def validate_bundle(bundle: Bundle) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    policy = bundle.diagnostic_policy
    policy_fields = {
        "missing_premises": {"unresolved", "refuted", "invalid-input", "out-of-scope"},
        "inconsistent_premises": {"inconsistent-premises"},
        "out_of_scope": {"out-of-scope"},
        "forbidden_evidence": {"invalid-input", "out-of-scope"},
        "revocation": {"refutation", "stale"},
        "completeness": {"required", "unresolved"},
    }
    for field_name, allowed in policy_fields.items():
        value = getattr(policy, field_name, None)
        if not isinstance(value, str) or value not in allowed:
            issues.append(ValidationIssue("diagnostic-policy", f"invalid {field_name} policy value", f"diagnostic_policy.{field_name}"))
    relations = {r.name: r for r in bundle.relations if isinstance(r, RelationDecl)}
    if len(relations) != len(bundle.relations):
        issues.append(ValidationIssue("duplicate-relation", "relation names must be unique", "relations"))
    for relation in bundle.relations:
        if isinstance(relation, RelationDecl): _validate_relation(relation, relations, issues)
        else: issues.append(ValidationIssue("relation-type", "expected RelationDecl", "relations"))
    for i, fact in enumerate(bundle.facts):
        _validate_atom(fact, relations, issues, f"facts[{i}]", {}, fact_only=True)
        if isinstance(fact, Atom) and fact.negated: issues.append(ValidationIssue("negative-fact", "facts must be positive", f"facts[{i}]"))
    evidence_ids = set()
    for i, record in enumerate(bundle.evidence):
        path = f"evidence[{i}]"
        if not isinstance(record, Evidence):
            issues.append(ValidationIssue("evidence-type", "expected Evidence", path)); continue
        if not isinstance(record.id, str) or not record.id: issues.append(ValidationIssue("evidence-id", "evidence id must be a non-empty string", path))
        if record.id in evidence_ids: issues.append(ValidationIssue("duplicate-evidence-id", record.id, path))
        evidence_ids.add(record.id)
        _validate_atom(record.atom, relations, issues, path + ".atom", {}, fact_only=True)
        if record.atom.negated: issues.append(ValidationIssue("negative-evidence", "evidence atoms must be positive", path))
        declared = relations.get(record.atom.relation)
        if declared and set(record.context.as_dict()) != set(declared.context_indices):
            issues.append(ValidationIssue("evidence-context", "evidence context must exactly match relation context indices", path))
        if not isinstance(record.source, str) or not record.source: issues.append(ValidationIssue("evidence-source", "evidence source must be a non-empty string", path))
        if not isinstance(record.kind, str) or not record.kind: issues.append(ValidationIssue("evidence-kind", "evidence kind must be a non-empty string", path))
        if declared:
            names = [c.name for c in declared.columns]
            for name, value in record.context.values:
                if name in names:
                    index = names.index(name)
                    if not isinstance(record.atom.terms[index], Constant) or record.atom.terms[index].value != value:
                        issues.append(ValidationIssue("evidence-context", f"context value does not equal atom column {name!r}", path))
    fact_keys = {_ground_atom_key(fact) for fact in bundle.facts if isinstance(fact, Atom)}
    evidence_keys = {_ground_atom_key(record.atom) for record in bundle.evidence if isinstance(record, Evidence)}
    for i, record in enumerate(bundle.evidence):
        if isinstance(record, Evidence) and _ground_atom_key(record.atom) not in fact_keys:
            issues.append(ValidationIssue("evidence-without-fact", record.id, f"evidence[{i}]"))
    if bundle.evidence:
        for i, fact in enumerate(bundle.facts):
            if isinstance(fact, Atom) and _ground_atom_key(fact) not in evidence_keys:
                issues.append(ValidationIssue("fact-without-evidence", "evidence-bearing bundles require attribution", f"facts[{i}]"))
    for i, rule in enumerate(bundle.rules):
        if isinstance(rule, Rule): _validate_rule(rule, relations, issues, f"rules[{i}]")
        else: issues.append(ValidationIssue("rule-type", "expected Rule", f"rules[{i}]"))
    for i, claim in enumerate(bundle.claims):
        if isinstance(claim, Claim): _validate_claim(claim, relations, issues, f"claims[{i}]")
        else: issues.append(ValidationIssue("claim-type", "expected Claim", f"claims[{i}]"))
    seen_claim_ids = set()
    requires_claim_ids = bool(bundle.evidence or bundle.mappings or bundle.diagnostics)
    for i, claim in enumerate(bundle.claims):
        if requires_claim_ids and isinstance(claim, Claim) and (not isinstance(claim.id, str) or not claim.id):
            issues.append(ValidationIssue("claim-id", "claim id is mandatory", f"claims[{i}]"))
        if isinstance(claim, Claim) and claim.id:
            if claim.id in seen_claim_ids: issues.append(ValidationIssue("duplicate-claim-id", claim.id, f"claims[{i}]"))
            seen_claim_ids.add(claim.id)
    claim_by_id = {claim.id: claim for claim in bundle.claims
                   if isinstance(claim, Claim) and claim.id}
    if claim_by_id:
        for i, mapping in enumerate(bundle.mappings):
            if not mapping.claim_id or mapping.claim_id not in seen_claim_ids:
                issues.append(ValidationIssue("mapping-claim-id", "mapping must name an existing claim id", f"mappings[{i}]"))
        for i, diagnostic in enumerate(bundle.diagnostics):
            if not diagnostic.claim_id or diagnostic.claim_id not in seen_claim_ids:
                issues.append(ValidationIssue("diagnostic-claim-id", "diagnostic must name an existing claim id", f"diagnostics[{i}]"))
    join_eligible_mappings = []
    for i, mapping in enumerate(bundle.mappings):
        path = f"mappings[{i}]"
        if not isinstance(mapping, EvidenceMapping):
            issues.append(ValidationIssue("mapping-type", "expected EvidenceMapping", path)); continue
        if not isinstance(mapping.effect, EvidenceEffect): issues.append(ValidationIssue("mapping-effect", "unsupported evidence effect", path))
        if mapping.claim_relation not in relations: issues.append(ValidationIssue("mapping-claim", mapping.claim_relation, path))
        if mapping.evidence_relation not in relations: issues.append(ValidationIssue("mapping-evidence", mapping.evidence_relation, path))
        named_claim = claim_by_id.get(mapping.claim_id)
        if named_claim is not None and mapping.claim_relation != named_claim.relation:
            issues.append(ValidationIssue(
                "mapping-claim-relation",
                f"mapping relation {mapping.claim_relation!r} does not match claim {mapping.claim_id!r} relation {named_claim.relation!r}",
                path))
            # Never use a decoy declaration to authorize projection coverage or
            # mixed-binding compatibility for the claim selected by id.
            continue
        join_eligible_mappings.append(mapping)
        for context_name in mapping.context_indices:
            claim_decl = relations.get(mapping.claim_relation)
            evidence_decl = relations.get(mapping.evidence_relation)
            if not claim_decl or context_name not in claim_decl.context_indices: issues.append(ValidationIssue("mapping-context", context_name, path))
            if not evidence_decl or context_name not in evidence_decl.context_indices: issues.append(ValidationIssue("mapping-context", context_name, path))
        claim_decl = relations.get(mapping.claim_relation); evidence_decl = relations.get(mapping.evidence_relation)
        if claim_decl and evidence_decl:
            c_names = {c.name for c in claim_decl.columns}; e_names = {c.name for c in evidence_decl.columns}
            c_types = {c.name: c.type for c in claim_decl.columns}
            e_types = {c.name: c.type for c in evidence_decl.columns}
            for left, right in mapping.bindings:
                if left not in c_names or right not in e_names:
                    issues.append(ValidationIssue("mapping-binding", f"unknown projection {left!r}->{right!r}", path))
                elif c_types[left] != e_types[right]:
                    issues.append(ValidationIssue("mapping-binding", f"projection {left!r}->{right!r} changes type", path))
            if len({left for left, _ in mapping.bindings}) != len(mapping.bindings) or len({right for _, right in mapping.bindings}) != len(mapping.bindings):
                issues.append(ValidationIssue("mapping-binding", "duplicate projection binding", path))
            covered = {left for left, _ in mapping.bindings}
            if not set(mapping.context_indices).issubset(covered):
                issues.append(ValidationIssue("mapping-coverage", "context mapping is not covered by bindings", path))
            if mapping.required or mapping.allow_out_of_scope:
                issues.append(ValidationIssue(
                    "mapping-option",
                    "required/allow_out_of_scope mappings are reserved until their semantics are implemented",
                    path))
            if isinstance(mapping.effect, EvidenceEffect) and mapping.effect.value in {"support", "refutation"}:
                omitted = (c_names & e_names & _CAUSAL_IDENTITY_COLUMNS) - covered
                if omitted:
                    issues.append(ValidationIssue(
                        "mapping-coverage",
                        "support/refutation mapping omits causal identities without aggregation authority: "
                        + ", ".join(sorted(omitted)), path))
    _validate_mapping_context_joins(join_eligible_mappings, relations, issues)
    allowed_status = {"complete", "invalid-input", "inconsistent-premises", "resource-exhausted", "unsupported-construct", "stale", "out-of-scope"}
    for i, diagnostic in enumerate(bundle.diagnostics):
        path = f"diagnostics[{i}]"
        if not isinstance(diagnostic, DiagnosticRule): issues.append(ValidationIssue("diagnostic-type", "expected DiagnosticRule", path)); continue
        if not isinstance(diagnostic.effect, EvidenceEffect): issues.append(ValidationIssue("diagnostic-effect", "unsupported diagnostic effect", path))
        predicate = dict(diagnostic.predicate)
        if predicate:
            operator = predicate.get("operator")
            relation = relations.get(diagnostic.trigger_relation)
            column = next((c for c in relation.columns if c.name == predicate.get("column")), None) if relation else None
            if operator not in {"=", "!=", "in", "not-in", "exists"}:
                issues.append(ValidationIssue("diagnostic-predicate", "unsupported diagnostic predicate operator", path))
            if column is None: issues.append(ValidationIssue("diagnostic-predicate", "predicate column is not declared by trigger relation", path))
            value = predicate.get("value")
            values = value if operator in {"in", "not-in"} and isinstance(value, (list, tuple)) else ([] if operator in {"in", "not-in"} else [value])
            if operator in {"in", "not-in"} and not isinstance(value, (list, tuple)): issues.append(ValidationIssue("diagnostic-predicate", "set predicate value must be a list", path))
            if operator in {"=", "!=", "in", "not-in"} and column:
                for item in values:
                    inferred = TypeName.BOOLEAN if isinstance(item, bool) else TypeName.INTEGER if isinstance(item, int) else TypeName.SYMBOL if isinstance(item, str) else None
                    if inferred != column.type: issues.append(ValidationIssue("diagnostic-predicate", "predicate value type does not match column", path))
        if diagnostic.trigger_relation not in relations: issues.append(ValidationIssue("diagnostic-trigger", diagnostic.trigger_relation, path))
        if diagnostic.operational_status not in allowed_status: issues.append(ValidationIssue("diagnostic-status", diagnostic.operational_status, path))
        relation = relations.get(diagnostic.trigger_relation)
        if relation and not set(diagnostic.context_indices).issubset(set(relation.context_indices)):
            issues.append(ValidationIssue("diagnostic-context", "diagnostic context is not declared by trigger relation", path))
    known_ids = set(evidence_ids)
    for i, record in enumerate(bundle.evidence):
        for dependency in record.depends_on:
            if not isinstance(dependency, str) or not dependency: issues.append(ValidationIssue("evidence-dependency", "dependency ids must be non-empty strings", f"evidence[{i}]"))
            elif dependency not in known_ids and not dependency.startswith("external:"):
                issues.append(ValidationIssue("unknown-evidence-dependency", dependency, f"evidence[{i}]"))
    claim_ids = {claim.id for claim in bundle.claims if isinstance(claim, Claim) and claim.id}
    evidence_by_id = {record.id: record for record in bundle.evidence if isinstance(record, Evidence)}
    for i, output in enumerate(bundle.outputs):
        path = f"outputs[{i}]"
        if not isinstance(output, OutputTemplate): issues.append(ValidationIssue("output-type", "expected OutputTemplate", path)); continue
        if not isinstance(output.kind, OutputKind): issues.append(ValidationIssue("output-kind", "unknown output kind", path)); continue
        if output.claim_id not in claim_ids: issues.append(ValidationIssue("output-claim", output.claim_id, path))
        explicit_triggers = (*output.requires_all_evidence, *output.requires_any_evidence, *output.excludes_evidence)
        all_triggers = (*explicit_triggers, *((output.evidence_id,) if output.evidence_id else ()))
        if len(set(explicit_triggers)) != len(explicit_triggers): issues.append(ValidationIssue("output-trigger", "duplicate evidence trigger", path))
        # The output's payload evidence_id is the value being rendered; only
        # explicit trigger declarations are causal prerequisites.
        for evidence_id in explicit_triggers:
            if not isinstance(evidence_id, str) or not evidence_id or evidence_id not in evidence_by_id:
                issues.append(ValidationIssue("output-trigger", "trigger evidence is not declared", path))
        if output.requires_any_evidence is not None and not isinstance(output.requires_any_evidence, tuple): issues.append(ValidationIssue("output-trigger", "any-evidence trigger must be a sequence", path))
        if output.when_claim not in {None, "derived", "underived", "supported", "refuted", "unresolved", "conflicting", "always"}:
            issues.append(ValidationIssue("output-trigger", "unknown claim trigger", path))
        if output.when_claim == "always" and output.kind in {OutputKind.DISCREPANCY, OutputKind.MISSING_PREMISE}:
            issues.append(ValidationIssue("output-trigger", "diagnostic output cannot use always claim trigger", path))
        if output.relation and output.kind != OutputKind.MISSING_PREMISE:
            issues.append(ValidationIssue("output-relation", "relation is only valid for missing premise outputs", path))
        if output.kind in {OutputKind.DISCREPANCY, OutputKind.MISSING_PREMISE} and not (output.requires_all_evidence or output.requires_any_evidence or output.when_claim or output.relation):
            issues.append(ValidationIssue("output-trigger", "diagnostic output has no trigger", path))
        if output.kind in {OutputKind.OBSERVED, OutputKind.FORBIDDEN} and (not output.evidence_id or output.evidence_id not in evidence_by_id):
            issues.append(ValidationIssue("output-evidence", "observed/forbidden output must reference evidence", path))
        if output.kind == OutputKind.MISSING_PREMISE and not output.relation: issues.append(ValidationIssue("output-relation", "missing premise output needs a relation", path))
        if output.kind == OutputKind.MISSING_PREMISE and output.relation not in relations and output.relation not in DIAGNOSTIC_VOCABULARY:
            issues.append(ValidationIssue("output-relation", "unknown diagnostic vocabulary relation", path))
        causal_relations = {mapping.evidence_relation for mapping in bundle.mappings if mapping.claim_id == output.claim_id}
        causal_relations.update(diagnostic.trigger_relation for diagnostic in bundle.diagnostics if diagnostic.claim_id == output.claim_id)
        claim = next((claim for claim in bundle.claims if claim.id == output.claim_id), None)
        if claim:
            causal_relations.update(atom.relation for rule in bundle.rules if rule.head.relation == claim.relation for atom in rule.body)
        for evidence_id in explicit_triggers:
            evidence = evidence_by_id.get(evidence_id)
            if evidence and evidence.atom.relation not in causal_relations:
                issues.append(ValidationIssue("output-trigger", "trigger evidence is not causally connected to claim", path))
        for name, value in output.fields:
            if not isinstance(name, str) or not name: issues.append(ValidationIssue("output-field", "field names must be non-empty strings", path))
            if value.source not in {"constant", "claim", "evidence"}: issues.append(ValidationIssue("output-source", "unknown template value source", path)); continue
            if value.source == "constant":
                _validate_term(Constant(value.value, value.type), value.type, {}, issues, f"{path}.fields.{name}")
                continue
            relation = None
            if value.source == "claim":
                claim = next((c for c in bundle.claims if isinstance(c, Claim) and c.id == output.claim_id), None)
                relation = relations.get(claim.relation) if claim else None
            elif value.source == "evidence":
                evidence = evidence_by_id.get(value.evidence_id or output.evidence_id or "")
                relation = relations.get(evidence.atom.relation) if evidence else None
            if value.source != "constant" and not relation: issues.append(ValidationIssue("output-reference", "template relation reference is unavailable", path)); continue
            if value.source != "constant":
                if value.column == "id" and value.type != TypeName.SYMBOL: issues.append(ValidationIssue("output-type", "evidence id references are symbols", path))
                elif value.column not in {column.name for column in relation.columns}: issues.append(ValidationIssue("output-column", value.column, path))
                elif value.type != next(column.type for column in relation.columns if column.name == value.column): issues.append(ValidationIssue("output-type", "template reference type mismatch", path))
    output_keys = []
    for output in bundle.outputs:
        output_keys.append(repr((output.kind, output.claim_id, output.evidence_id, output.relation, output.fields, output.requires_all_evidence, output.requires_any_evidence, output.excludes_evidence, output.when_claim)))
    if len(output_keys) != len(set(output_keys)):
        issues.append(ValidationIssue("output-duplicate", "duplicate canonical output template", "outputs"))
    _validate_recursion(bundle, relations, issues)
    return tuple(issues)


def assert_valid(bundle: Bundle) -> Bundle:
    issues = validate_bundle(bundle)
    if issues: raise ValidationError(issues)
    return bundle


def validate(bundle: Bundle): return validate_bundle(bundle)


def _validate_relation(r, relations, issues):
    if not r.name or not r.name.replace("_", "a").isalnum() or r.name[0].isdigit():
        issues.append(ValidationIssue("name", "relation name must be an identifier", f"relations.{r.name}"))
    if not all(hasattr(c, "name") and hasattr(c, "type") and hasattr(c, "context") for c in r.columns):
        issues.append(ValidationIssue("column-type", "columns must be Column values", f"relations.{r.name}")); return
    names = [c.name for c in r.columns]
    if len(names) != len(set(names)): issues.append(ValidationIssue("duplicate-column", "column names must be unique", f"relations.{r.name}"))
    if len(r.context_indices) != len(set(r.context_indices)): issues.append(ValidationIssue("duplicate-context", "context positions must be unique", f"relations.{r.name}"))
    for index in r.context_indices:
        if index not in names: issues.append(ValidationIssue("context-index", f"unknown context column {index!r}", f"relations.{r.name}"))
        elif not r.columns[names.index(index)].context: issues.append(ValidationIssue("context-index", f"column {index!r} is not marked context", f"relations.{r.name}"))
    marked_context = {column.name for column in r.columns if column.context}
    if (r.context_indices or r.binding.value == "static") and marked_context != set(r.context_indices):
        # Runtime declarations predating explicit context_indices retain their
        # legacy column flags.  New scoped declarations and all static inputs
        # must make the two representations agree exactly.
        issues.append(ValidationIssue("context-index", "context flags must exactly equal declared context indices", f"relations.{r.name}"))
    if r.binding.value == "static" and r.modality.value in {"observation", "assumption", "completeness"}:
        index_column = next((column for column in r.columns if column.name == "index"), None)
        fingerprint = (r.name, tuple((column.name, column.type, column.context)
                                     for column in r.columns), r.context_indices)
        explicitly_context_free = fingerprint in _CONTEXT_FREE_STATIC_DECLARATIONS
        if index_column is None and not explicitly_context_free:
            issues.append(ValidationIssue(
                "static-context",
                "static observations require an index digest unless they match a frozen context-free declaration",
                f"relations.{r.name}",
            ))
        elif index_column is not None and (r.context_indices != ("index",)
                                           or index_column.type != TypeName.DIGEST
                                           or not index_column.context):
            issues.append(ValidationIssue("static-context", "indexed static observations use one digest context column named 'index'", f"relations.{r.name}"))
    if r.modality.value == "completeness":
        if not r.completes: issues.append(ValidationIssue("completeness-target", "completeness relation must name its target relation", f"relations.{r.name}"))
        elif r.completes not in relations: issues.append(ValidationIssue("completeness-target", f"unknown target {r.completes!r}", f"relations.{r.name}"))
        elif r.binding != relations[r.completes].binding:
            issues.append(ValidationIssue(
                "completeness-binding",
                "completeness relation binding must match its target relation",
                f"relations.{r.name}"))
    elif r.completes is not None: issues.append(ValidationIssue("completeness-target", "only completeness relations may name a target", f"relations.{r.name}"))
    if r.modality.value == "compatibility":
        if len(r.compatibility_targets) < 2: issues.append(ValidationIssue("compatibility-target", "compatibility relation must name at least two target relations", f"relations.{r.name}"))
        for target in r.compatibility_targets:
            if target not in relations: issues.append(ValidationIssue("compatibility-target", f"unknown target {target!r}", f"relations.{r.name}"))
        for index in r.compatibility_context_indices:
            if index not in names:
                issues.append(ValidationIssue("compatibility-context", f"payload position {index!r} is not a declared column", f"relations.{r.name}"))
        if len(r.compatibility_context_indices) != len(set(r.compatibility_context_indices)):
            issues.append(ValidationIssue("compatibility-context", "compatibility payload positions must be unique", f"relations.{r.name}"))
        if len(r.compatibility_targets) != len(set(r.compatibility_targets)): issues.append(ValidationIssue("compatibility-target", "compatibility targets must be unique", f"relations.{r.name}"))
    elif r.compatibility_targets or r.compatibility_context_indices:
        issues.append(ValidationIssue("compatibility-target", "only compatibility relations may declare targets/positions", f"relations.{r.name}"))


def _python_type(value):
    if isinstance(value, bool): return TypeName.BOOLEAN
    if isinstance(value, int): return TypeName.INTEGER
    if isinstance(value, float): return None
    if isinstance(value, str): return TypeName.SYMBOL
    if isinstance(value, (tuple, list, Mapping)): return TypeName.JSON_METADATA_ONLY
    return None


def _validate_term(term, expected, env, issues, path, fact_only=False):
    if isinstance(term, Variable):
        if fact_only: issues.append(ValidationIssue("fact-variable", "facts must contain constants", path)); return
        old = env.setdefault(term.name, expected)
        if old != expected: issues.append(ValidationIssue("type-mismatch", f"variable {term.name!r} has incompatible types", path))
        return
    if not isinstance(term, Constant):
        issues.append(ValidationIssue("term-type", "term must be Variable or Constant", path)); return
    inferred = _python_type(term.value)
    declared = term.type
    actual = declared or inferred
    declared_ok = declared is None or inferred == declared or (declared == TypeName.UNSIGNED and inferred == TypeName.INTEGER and isinstance(term.value, int) and term.value >= 0) or (declared == TypeName.TIMESTAMP and inferred == TypeName.INTEGER and isinstance(term.value, int) and term.value >= 0) or (declared == TypeName.DIGEST and inferred == TypeName.SYMBOL) or (declared == TypeName.JSON_METADATA_ONLY and inferred == TypeName.JSON_METADATA_ONLY)
    if expected == TypeName.UNSIGNED and isinstance(term.value, int) and term.value < 0: declared_ok = False
    compatible = actual == expected or (expected == TypeName.UNSIGNED and inferred == TypeName.INTEGER and isinstance(term.value, int) and term.value >= 0) or (expected == TypeName.TIMESTAMP and inferred == TypeName.INTEGER and isinstance(term.value, int) and term.value >= 0) or (expected == TypeName.DIGEST and inferred == TypeName.SYMBOL)
    if actual is None or not declared_ok or not compatible:
        issues.append(ValidationIssue("type-mismatch", f"expected {expected.value}, got {getattr(actual, 'value', actual)}", path))


def _validate_atom(atom, relations, issues, path, env, fact_only=False):
    if not isinstance(atom, Atom): issues.append(ValidationIssue("atom-type", "expected atom", path)); return
    relation = relations.get(atom.relation)
    if relation is None: issues.append(ValidationIssue("unknown-relation", atom.relation, path)); return
    if fact_only and not relation.primitive:
        issues.append(ValidationIssue("nonprimitive-fact", "facts and evidence may target only primitive relations", path))
    if fact_only and relation.modality.value == "claim":
        issues.append(ValidationIssue(
            "producer-authored-claim",
            "facts and evidence report premises; claim relations require a reviewed rule or mapping",
            path))
    if len(atom.terms) != relation.arity: issues.append(ValidationIssue("arity", f"expected {relation.arity}, got {len(atom.terms)}", path)); return
    for i, (term, column) in enumerate(zip(atom.terms, relation.columns)):
        _validate_term(term, column.type, env, issues, f"{path}.terms[{i}]", fact_only)


def _validate_rule(rule, relations, issues, path):
    env = {}
    if not any(isinstance(item, Atom) and not item.negated for item in rule.body):
        issues.append(ValidationIssue(
            "evidence-free-rule",
            "rules require at least one positive relational premise",
            path))
    for j, atom in enumerate(rule.body):
        if isinstance(atom, Comparison):
            if atom.operator not in {"=", "!=", "<", "<=", ">", ">="}: issues.append(ValidationIssue("operator", atom.operator, f"{path}.body[{j}]"))
            left_type = env.get(atom.left.name) if isinstance(atom.left, Variable) else (atom.left.type or _python_type(atom.left.value)) if isinstance(atom.left, Constant) else None
            right_type = env.get(atom.right.name) if isinstance(atom.right, Variable) else (atom.right.type or _python_type(atom.right.value)) if isinstance(atom.right, Constant) else None
            if left_type is None or right_type is None: issues.append(ValidationIssue("unsafe-comparison", "comparison variables must be positively bound", f"{path}.body[{j}]"))
            elif left_type != right_type: issues.append(ValidationIssue("type-mismatch", "comparison operands must have equal types", f"{path}.body[{j}]"))
            continue
        if not isinstance(atom, Atom):
            _validate_atom(atom, relations, issues, f"{path}.body[{j}]", env)
            continue
        before = set(env)
        target_env = dict(env) if atom.negated else env
        _validate_atom(atom, relations, issues, f"{path}.body[{j}]", target_env)
        if atom.negated and not _atom_vars(atom).issubset(before):
            issues.append(ValidationIssue("unsafe-negation", "negation variables must be positively bound", f"{path}.body[{j}]"))
    bound = set(env)
    _validate_atom(rule.head, relations, issues, f"{path}.head", dict(env))
    if isinstance(rule.head, Atom) and not _atom_vars(rule.head).issubset(bound):
        issues.append(ValidationIssue("unsafe-variable", "head variables must be positively bound", path))
    _validate_context_joins(rule, relations, issues, path)
    for neg in (a for a in rule.body if isinstance(a, Atom) and a.negated): _validate_completeness(neg, rule, relations, issues, path)
    if rule.aggregation:
        if isinstance(rule.aggregation, Aggregation): _validate_aggregation(rule.aggregation, rule, relations, issues, path)
        else: issues.append(ValidationIssue("aggregation-type", "expected Aggregation", path))


def _validate_completeness(negated, rule, relations, issues, path):
    target = negated.relation
    matches = [a for a in rule.body if isinstance(a, Atom) and not a.negated and relations.get(a.relation) and relations[a.relation].modality.value == "completeness" and relations[a.relation].completes == target]
    target_decl = relations.get(target)
    for witness in matches:
        witness_decl = relations[witness.relation]
        if target_decl and witness_decl.context_indices != target_decl.context_indices:
            continue
        ok = True
        target_names = [c.name for c in target_decl.columns] if target_decl else []
        witness_names = [c.name for c in witness_decl.columns]
        # Every shared scope column (not only context columns) must be bound to
        # the same term.  A path witness for one document cannot close another.
        for name in set(target_names) & set(witness_names):
            ti = target_names.index(name); wi = witness_names.index(name)
            if repr(negated.terms[ti]) != repr(witness.terms[wi]): ok = False
        if ok: return
    issues.append(ValidationIssue("missing-completeness", f"negation of {target!r} needs an exact scoped completeness witness", path))


def _validate_mapping_context_joins(mappings, relations, issues):
    """Require an index/run witness inside each mixed support conjunction.

    Support mappings for one claim are AND premises in both kernels.  Checking
    each projection independently would let static and runtime observations
    manufacture a claim without proving that the index describes that run.
    Observation-only mappings deliberately do not authorize the conjunction.
    """
    grouped = {}
    for index, mapping in enumerate(mappings):
        if (not isinstance(mapping, EvidenceMapping)
                or not isinstance(mapping.effect, EvidenceEffect)
                or mapping.effect.value != "support"):
            continue
        declaration = relations.get(mapping.evidence_relation)
        if declaration is not None:
            grouped.setdefault(mapping.claim_id, []).append((index, mapping, declaration))

    for claim_id, entries in grouped.items():
        ordinary = [entry for entry in entries
                    if entry[2].modality.value != "compatibility"]
        static_entries = [entry for entry in ordinary
                          if entry[2].binding.value == "static"]
        runtime_entries = [entry for entry in ordinary
                           if entry[2].binding.value == "runtime"]
        witnesses = [entry for entry in entries
                     if entry[2].modality.value == "compatibility"]
        for static_index, static_mapping, static_decl in static_entries:
            static_columns = {column.name: column for column in static_decl.columns}
            static_claim_index = next(
                (left for left, right in static_mapping.bindings if right == "index"), None)
            for runtime_index, runtime_mapping, runtime_decl in runtime_entries:
                runtime_columns = {column.name: column for column in runtime_decl.columns}
                runtime_claim_run = next(
                    (left for left, right in runtime_mapping.bindings if right == "run"), None)
                path = f"mappings[{static_index}],mappings[{runtime_index}]"
                if ("index" not in static_columns
                        or static_columns["index"].type != TypeName.DIGEST
                        or static_claim_index is None):
                    issues.append(ValidationIssue(
                        "mixed-binding-join",
                        "mixed support mappings require a static digest index bound through the claim",
                        path))
                    continue
                if "run" not in runtime_columns or runtime_claim_run is None:
                    issues.append(ValidationIssue(
                        "mixed-binding-join",
                        "mixed support mappings require a runtime run bound through the claim",
                        path))
                    continue

                found = False
                for _, witness_mapping, witness_decl in witnesses:
                    if not {static_decl.name, runtime_decl.name}.issubset(
                            set(witness_decl.compatibility_targets)):
                        continue
                    witness_names = {column.name for column in witness_decl.columns}
                    if (not {"index", "run"}.issubset(witness_names)
                            or not {"index", "run"}.issubset(
                                set(witness_decl.compatibility_context_indices))):
                        continue
                    witness_bindings = {right: left
                                        for left, right in witness_mapping.bindings}
                    if (witness_bindings.get("index") == static_claim_index
                            and witness_bindings.get("run") == runtime_claim_run):
                        found = True
                        break
                if not found:
                    issues.append(ValidationIssue(
                        "mixed-binding-join",
                        f"claim {claim_id!r} mixed support mappings require an exact index/run compatibility support premise",
                        path))


def _validate_context_joins(rule, relations, issues, path):
    # Negation reads a relation just as surely as a positive atom does.  Keep
    # compatibility witnesses positive, but include negated ordinary inputs in
    # the mixed-binding trust boundary.  A completeness atom inherits the
    # binding and compatibility identity of the relation it closes; a producer
    # cannot relabel static closure as runtime to evade the check.
    atoms = [a for a in rule.body
             if isinstance(a, Atom) and a.relation in relations]
    compatibility = [(a, relations[a.relation]) for a in atoms
                     if not a.negated
                     and relations[a.relation].modality.value == "compatibility"]
    ordinary = []
    for atom in atoms:
        declaration = relations[atom.relation]
        if declaration.modality.value == "compatibility":
            continue
        effective = (relations.get(declaration.completes)
                     if declaration.modality.value == "completeness"
                     else declaration)
        effective = effective or declaration
        ordinary.append((atom, declaration, effective))
    static_atoms = [entry for entry in ordinary
                    if entry[2].binding.value == "static"]
    runtime_atoms = [entry for entry in ordinary
                     if entry[2].binding.value == "runtime"]
    for static_atom, static_decl, static_effective in static_atoms:
        static_names = [c.name for c in static_decl.columns]
        if "index" not in static_names:
            issues.append(ValidationIssue(
                "mixed-binding-join",
                "context-free static relations cannot join runtime evidence without an index/run witness",
                path))
            return
        index_term = static_atom.terms[static_names.index("index")]
        for runtime_atom, runtime_decl, runtime_effective in runtime_atoms:
            runtime_names = [c.name for c in runtime_decl.columns]
            if "run" not in runtime_names:
                issues.append(ValidationIssue("mixed-binding-join", "indexed static/runtime joins require a runtime run column", path))
                return
            run_term = runtime_atom.terms[runtime_names.index("run")]
            found = False
            for witness, witness_decl in compatibility:
                if not {static_effective.name, runtime_effective.name}.issubset(
                        witness_decl.compatibility_targets):
                    continue
                witness_names = [c.name for c in witness_decl.columns]
                if ("index" not in witness_names or "run" not in witness_names
                        or not {"index", "run"}.issubset(
                            set(witness_decl.compatibility_context_indices))):
                    continue
                if (repr(witness.terms[witness_names.index("index")]) == repr(index_term)
                        and repr(witness.terms[witness_names.index("run")]) == repr(run_term)):
                    found = True; break
            if not found:
                issues.append(ValidationIssue("mixed-binding-join", "static/runtime joins require an exact index/run compatibility witness", path))
                return
    context_bindings = []
    for atom in atoms:
        decl = relations[atom.relation]; names = [c.name for c in decl.columns]
        context_bindings.append((atom, {n: atom.terms[names.index(n)] for n in decl.context_indices}))
    for i, (_, left) in enumerate(context_bindings):
        for _, right in context_bindings[i + 1:]:
            differing = {k for k in left.keys() & right.keys() if repr(left[k]) != repr(right[k])}
            differing_terms = tuple(term for key in differing for term in (left[key], right[key]))
            left_rel = next((a.relation for a, b in context_bindings if b is left), None)
            right_rel = next((a.relation for a, b in context_bindings if b is right), None)
            def witness_matches(atom, decl):
                if not {left_rel, right_rel}.issubset(set(decl.compatibility_targets)): return False
                names = [c.name for c in decl.columns]
                positions = decl.compatibility_context_indices or decl.context_indices
                payload = tuple(atom.terms[names.index(p)] for p in positions if p in names)
                return bool(differing) and all(term in payload for term in differing_terms)
            witnessed = any(witness_matches(atom, decl) for atom, decl in compatibility)
            if differing and not witnessed:
                issues.append(ValidationIssue("missing-compatibility", "cross-context joins require an explicit compatibility witness", path)); return


def _validate_aggregation(a, rule, relations, issues, path):
    source = relations.get(a.relation); domain = relations.get(a.domain) if a.domain else None; closure = relations.get(a.closure_witness) if a.closure_witness else None
    if a.operator not in {"count", "sum", "min", "max", "any", "all"}: issues.append(ValidationIssue("aggregation", f"unsupported operator {a.operator!r}", path))
    if source is None: issues.append(ValidationIssue("aggregation-source", "aggregation source relation is unknown", path))
    else:
        names = {c.name: c.type for c in source.columns}
        for g in a.group_by:
            if g not in names: issues.append(ValidationIssue("aggregation-group", f"unknown group column {g!r}", path))
        if a.value_variable not in names: issues.append(ValidationIssue("aggregation-value", f"unknown value column {a.value_variable!r}", path))
        if a.operator in {"sum", "min", "max"} and a.value_variable in names and names[a.value_variable] not in {TypeName.INTEGER, TypeName.UNSIGNED}:
            issues.append(ValidationIssue("aggregation-value", "numeric aggregation requires an integer or decimal value", path))
        source_atoms = [x for x in rule.body if isinstance(x, Atom) and not x.negated and x.relation == a.relation]
        if not source_atoms: issues.append(ValidationIssue("aggregation-source", "aggregation source must be a positive body atom", path))
        else:
            source_atom = source_atoms[0]; source_names = [c.name for c in source.columns]
            domain_atoms = [x for x in rule.body if isinstance(x, Atom) and not x.negated and x.relation == a.domain]
            closure_atoms = [x for x in rule.body if isinstance(x, Atom) and not x.negated and x.relation == a.closure_witness]
            if not domain_atoms: issues.append(ValidationIssue("aggregation-domain", "finite aggregation domain must be a positive body atom", path))
            if not closure_atoms: issues.append(ValidationIssue("aggregation-closure", "aggregation closure witness must be a positive body atom", path))
            if domain_atoms and domain:
                domain_atom = domain_atoms[0]; domain_names = [c.name for c in domain.columns]
                scope_names = set((*source.context_indices, *a.group_by))
                for scope_name in scope_names:
                    if (scope_name not in domain_names
                            or repr(source_atom.terms[source_names.index(scope_name)])
                            != repr(domain_atom.terms[domain_names.index(scope_name)])):
                        issues.append(ValidationIssue("aggregation-domain", f"domain binding does not match source group/context {scope_name!r}", path))
                if a.operator == "all":
                    source_types = {column.name: column.type for column in source.columns}
                    # Domain member identity must be present in the source;
                    # otherwise projection can collapse distinct members to the
                    # group/context and manufacture universal success. The one
                    # reviewed ``outcome`` label is explicit non-key payload.
                    member_names = [name for name in domain_names
                                    if name not in scope_names
                                    and name != a.value_variable
                                    and (domain.name, name)
                                    not in _AGGREGATE_DOMAIN_PAYLOAD_COLUMNS]
                    for member_name in member_names:
                        if member_name not in source_types:
                            issues.append(ValidationIssue(
                                "aggregation-domain",
                                f"all source omits domain member identity {member_name!r}", path))
                            continue
                        domain_column = domain.columns[domain_names.index(member_name)]
                        if source_types[member_name] != domain_column.type:
                            issues.append(ValidationIssue(
                                "aggregation-domain",
                                f"all source/domain member {member_name!r} has incompatible types", path))
                        elif repr(source_atom.terms[source_names.index(member_name)]) != repr(
                                domain_atom.terms[domain_names.index(member_name)]):
                            issues.append(ValidationIssue(
                                "aggregation-domain",
                                f"all source/domain member {member_name!r} is not identically bound", path))
            if closure_atoms and domain:
                closure_atom = closure_atoms[0]; closure_names = [c.name for c in closure.columns]
                for context_name in domain.context_indices:
                    if context_name not in closure_names or repr(domain_atoms[0].terms[[c.name for c in domain.columns].index(context_name)]) != repr(closure_atom.terms[closure_names.index(context_name)]):
                        issues.append(ValidationIssue("aggregation-closure", f"closure binding does not match domain context {context_name!r}", path))
            head_decl = relations.get(rule.head.relation)
            required_head_columns = set(a.group_by) | set(source.context_indices)
            head_names = [c.name for c in head_decl.columns] if head_decl else []
            for group in required_head_columns:
                if group not in source_names or group not in head_names:
                    issues.append(ValidationIssue("aggregation-head", f"head must preserve group/context column {group!r}", path)); continue
                si = source_names.index(group); hi = head_names.index(group)
                if repr(source_atom.terms[si]) != repr(rule.head.terms[hi]):
                    issues.append(ValidationIssue("aggregation-head", f"head does not preserve group/context column {group!r}", path))
    if domain is None: issues.append(ValidationIssue("aggregation-domain", "aggregation requires a named domain", path))
    elif not domain.finite: issues.append(ValidationIssue("aggregation-domain", "aggregation domain must be finite", path))
    elif a.operator == "all" and not domain.nonempty: issues.append(ValidationIssue("aggregation-domain", "all aggregation requires a non-empty domain", path))
    if closure is None: issues.append(ValidationIssue("aggregation-closure", "aggregation requires a closure witness", path))
    elif closure.modality.value != "completeness" or closure.completes != a.domain: issues.append(ValidationIssue("aggregation-closure", "closure witness must complete the named domain", path))
    elif domain and closure.context_indices != domain.context_indices: issues.append(ValidationIssue("aggregation-closure", "closure witness context positions must match its finite domain", path))
    if source and rule.head.relation == source.name: issues.append(ValidationIssue("recursive-aggregation", "aggregation source cannot be the rule head relation", path))


def _validate_claim(claim, relations, issues, path):
    relation = relations.get(claim.relation)
    if relation is None: issues.append(ValidationIssue("unknown-relation", claim.relation, path)); return
    if len(claim.terms) != relation.arity: issues.append(ValidationIssue("arity", f"expected {relation.arity}, got {len(claim.terms)}", path)); return
    env = {}
    for i, (term, col) in enumerate(zip(claim.terms, relation.columns)): _validate_term(term, col.type, env, issues, f"{path}.terms[{i}]")
    known_context = set(relation.context_indices)
    if not hasattr(claim.context, "as_dict"):
        issues.append(ValidationIssue("claim-context", "claim context must be a Context", path)); context = {}
    else: context = claim.context.as_dict()
    if set(context) != known_context: issues.append(ValidationIssue("claim-context", "claim context must exactly match relation context indices", path))
    relation_names = [column.name for column in relation.columns]
    for name in known_context:
        if name in context:
            position = relation_names.index(name)
            column = relation.columns[position]
            _validate_term(Constant(context[name]), column.type, {}, issues, f"{path}.context.{name}")
            term = claim.terms[position]
            if isinstance(term, Constant) and term.value != context[name]:
                issues.append(ValidationIssue(
                    "claim-context",
                    f"context value does not equal claim term for column {name!r}", path))
    if claim.quantifier.value == "forall":
        domain = relations.get(claim.domain) if claim.domain else None
        if domain is None or not domain.finite:
            issues.append(ValidationIssue("forall-domain", "FORALL requires a named finite domain", path))
        else:
            if not domain.nonempty:
                issues.append(ValidationIssue("forall-domain", "FORALL domain must be explicitly non-empty", path))
            claim_values = {column.name for column, term in zip(relation.columns, claim.terms)
                            if isinstance(term, Constant)} | set(context)
            unbound_domain_context = set(domain.context_indices) - claim_values
            if unbound_domain_context:
                issues.append(ValidationIssue(
                    "forall-context",
                    "FORALL claim must ground every domain context position: "
                    + ", ".join(sorted(unbound_domain_context)), path))
            closure_decls = [decl for decl in relations.values()
                             if decl.modality.value == "completeness"
                             and decl.completes == domain.name
                             and decl.context_indices == domain.context_indices
                             and tuple(column.name for column in decl.columns)
                             == domain.context_indices]
            if not closure_decls:
                issues.append(ValidationIssue(
                    "forall-closure",
                    "FORALL requires a whole-domain completeness relation over exactly the domain context",
                    path))
            domain_types = {column.name: column.type for column in domain.columns}
            for position, term in enumerate(claim.terms):
                if not isinstance(term, Variable):
                    continue
                if term.name not in domain_types:
                    issues.append(ValidationIssue("forall-binding", f"variable {term.name!r} is absent from the domain", path))
                elif domain_types[term.name] != relation.columns[position].type:
                    issues.append(ValidationIssue("forall-binding", f"variable {term.name!r} has an incompatible domain type", path))


def _validate_recursion(bundle, relations, issues):
    edges = {r.name: [] for r in bundle.relations}
    for rule in bundle.rules:
        if not isinstance(rule, Rule) or not isinstance(rule.head, Atom) or rule.head.relation not in edges: continue
        for atom in rule.body:
            if isinstance(atom, Atom) and atom.relation in edges: edges[rule.head.relation].append((atom.relation, atom.negated))
        if isinstance(rule.aggregation, Aggregation) and rule.aggregation.relation in edges: edges[rule.head.relation].append((rule.aggregation.relation, False))
    components = _scc(edges)
    for start in edges:
        for dst, negative in edges[start]:
            if negative and start in _reachable(edges, dst): issues.append(ValidationIssue("recursive-negation", f"negative cycle involving {start} and {dst}", "rules"))
    for rule in bundle.rules:
        if isinstance(rule, Rule) and isinstance(rule.head, Atom) and isinstance(rule.aggregation, Aggregation) and rule.head.relation in components and rule.aggregation.relation in components and components[rule.head.relation] == components[rule.aggregation.relation]:
            issues.append(ValidationIssue("recursive-aggregation", "aggregation dependency is recursively cyclic", "rules"))


def _reachable(edges, source):
    seen = set(); stack = [source]
    while stack:
        node = stack.pop()
        if node in seen: continue
        seen.add(node); stack.extend(dst for dst, _ in edges[node])
    return seen


def _scc(edges):
    index = 0; stack = []; on_stack = set(); indices = {}; low = {}; result = {}
    def visit(node):
        nonlocal index
        indices[node] = low[node] = index; index += 1; stack.append(node); on_stack.add(node)
        for child, _ in edges[node]:
            if child not in indices: visit(child); low[node] = min(low[node], low[child])
            elif child in on_stack: low[node] = min(low[node], indices[child])
        if low[node] == indices[node]:
            component = len(result); members = []
            while True:
                item = stack.pop(); on_stack.remove(item); result[item] = component; members.append(item)
                if item == node: break
    for node in edges:
        if node not in indices: visit(node)
    return result
