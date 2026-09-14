"""Static validation for the restricted, finite claim-rule language."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .ir import (Aggregation, Atom, Bundle, Claim, Comparison, Constant,
                 RelationDecl, Rule, TypeName, Variable, Evidence, EvidenceMapping, DiagnosticRule, EvidenceEffect)


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


def validate_bundle(bundle: Bundle) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
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
    for i, rule in enumerate(bundle.rules):
        if isinstance(rule, Rule): _validate_rule(rule, relations, issues, f"rules[{i}]")
        else: issues.append(ValidationIssue("rule-type", "expected Rule", f"rules[{i}]"))
    for i, claim in enumerate(bundle.claims):
        if isinstance(claim, Claim): _validate_claim(claim, relations, issues, f"claims[{i}]")
        else: issues.append(ValidationIssue("claim-type", "expected Claim", f"claims[{i}]"))
    seen_claim_ids = set()
    for i, claim in enumerate(bundle.claims):
        if isinstance(claim, Claim) and (not isinstance(claim.id, str) or not claim.id):
            issues.append(ValidationIssue("claim-id", "claim id is mandatory", f"claims[{i}]"))
        if isinstance(claim, Claim) and claim.id:
            if claim.id in seen_claim_ids: issues.append(ValidationIssue("duplicate-claim-id", claim.id, f"claims[{i}]"))
            seen_claim_ids.add(claim.id)
    if any(isinstance(c, Claim) and c.id for c in bundle.claims):
        for i, mapping in enumerate(bundle.mappings):
            if not mapping.claim_id or mapping.claim_id not in seen_claim_ids:
                issues.append(ValidationIssue("mapping-claim-id", "mapping must name an existing claim id", f"mappings[{i}]"))
        for i, diagnostic in enumerate(bundle.diagnostics):
            if not diagnostic.claim_id or diagnostic.claim_id not in seen_claim_ids:
                issues.append(ValidationIssue("diagnostic-claim-id", "diagnostic must name an existing claim id", f"diagnostics[{i}]"))
    for i, mapping in enumerate(bundle.mappings):
        path = f"mappings[{i}]"
        if not isinstance(mapping, EvidenceMapping):
            issues.append(ValidationIssue("mapping-type", "expected EvidenceMapping", path)); continue
        if not isinstance(mapping.effect, EvidenceEffect): issues.append(ValidationIssue("mapping-effect", "unsupported evidence effect", path))
        if mapping.claim_relation not in relations: issues.append(ValidationIssue("mapping-claim", mapping.claim_relation, path))
        if mapping.evidence_relation not in relations: issues.append(ValidationIssue("mapping-evidence", mapping.evidence_relation, path))
        for context_name in mapping.context_indices:
            claim_decl = relations.get(mapping.claim_relation)
            evidence_decl = relations.get(mapping.evidence_relation)
            if not claim_decl or context_name not in claim_decl.context_indices: issues.append(ValidationIssue("mapping-context", context_name, path))
            if not evidence_decl or context_name not in evidence_decl.context_indices: issues.append(ValidationIssue("mapping-context", context_name, path))
        claim_decl = relations.get(mapping.claim_relation); evidence_decl = relations.get(mapping.evidence_relation)
        if claim_decl and evidence_decl:
            c_names = {c.name for c in claim_decl.columns}; e_names = {c.name for c in evidence_decl.columns}
            for left, right in mapping.bindings:
                if left not in c_names or right not in e_names:
                    issues.append(ValidationIssue("mapping-binding", f"unknown projection {left!r}->{right!r}", path))
            covered = {left for left, _ in mapping.bindings}
            if not set(mapping.context_indices).issubset(covered):
                issues.append(ValidationIssue("mapping-coverage", "context mapping is not covered by bindings", path))
    allowed_status = {"complete", "invalid-input", "inconsistent-premises", "resource-exhausted", "unsupported-construct", "stale", "out-of-scope"}
    for i, diagnostic in enumerate(bundle.diagnostics):
        path = f"diagnostics[{i}]"
        if not isinstance(diagnostic, DiagnosticRule): issues.append(ValidationIssue("diagnostic-type", "expected DiagnosticRule", path)); continue
        if not isinstance(diagnostic.effect, EvidenceEffect): issues.append(ValidationIssue("diagnostic-effect", "unsupported diagnostic effect", path))
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
    if r.modality.value == "completeness":
        if not r.completes: issues.append(ValidationIssue("completeness-target", "completeness relation must name its target relation", f"relations.{r.name}"))
        elif r.completes not in relations: issues.append(ValidationIssue("completeness-target", f"unknown target {r.completes!r}", f"relations.{r.name}"))
    elif r.completes is not None: issues.append(ValidationIssue("completeness-target", "only completeness relations may name a target", f"relations.{r.name}"))
    if r.modality.value == "compatibility":
        if len(r.compatibility_targets) < 2: issues.append(ValidationIssue("compatibility-target", "compatibility relation must name at least two target relations", f"relations.{r.name}"))
        for target in r.compatibility_targets:
            if target not in relations: issues.append(ValidationIssue("compatibility-target", f"unknown target {target!r}", f"relations.{r.name}"))
        for index in r.compatibility_context_indices:
            if index not in r.context_indices: issues.append(ValidationIssue("compatibility-context", f"context position {index!r} is not declared", f"relations.{r.name}"))
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
    if len(atom.terms) != relation.arity: issues.append(ValidationIssue("arity", f"expected {relation.arity}, got {len(atom.terms)}", path)); return
    for i, (term, column) in enumerate(zip(atom.terms, relation.columns)):
        _validate_term(term, column.type, env, issues, f"{path}.terms[{i}]", fact_only)


def _validate_rule(rule, relations, issues, path):
    env = {}
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
        for name in target_decl.context_indices if target_decl else ():
            if name not in witness_decl.context_indices: ok = False; break
            ti = [c.name for c in target_decl.columns].index(name); wi = [c.name for c in witness_decl.columns].index(name)
            if repr(negated.terms[ti]) != repr(witness.terms[wi]): ok = False
        if ok: return
    issues.append(ValidationIssue("missing-completeness", f"negation of {target!r} needs an exact scoped completeness witness", path))


def _validate_context_joins(rule, relations, issues, path):
    atoms = [a for a in rule.body if isinstance(a, Atom) and not a.negated and a.relation in relations]
    compatibility = [(a, relations[a.relation]) for a in atoms if relations[a.relation].modality.value == "compatibility"]
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
                for context_name in source.context_indices:
                    if context_name not in domain_names or repr(source_atom.terms[source_names.index(context_name)]) != repr(domain_atom.terms[domain_names.index(context_name)]):
                        issues.append(ValidationIssue("aggregation-domain", f"domain binding does not match source context {context_name!r}", path))
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
    for name in known_context:
        if name in context:
            column = relation.columns[[c.name for c in relation.columns].index(name)]
            _validate_term(Constant(context[name]), column.type, {}, issues, f"{path}.context.{name}")
    if claim.quantifier.value == "forall":
        domain = relations.get(claim.domain) if claim.domain else None
        if domain is None or not domain.finite: issues.append(ValidationIssue("forall-domain", "FORALL requires a named finite domain", path))
        elif not domain.nonempty: issues.append(ValidationIssue("forall-domain", "FORALL domain must be explicitly non-empty", path))


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
