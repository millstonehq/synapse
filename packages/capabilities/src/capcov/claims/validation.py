"""Static validation for the restricted, finite claim-rule language."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .ir import Aggregation, Atom, Bundle, Comparison, RelationDecl, Rule, Variable


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        return f"{self.code}: {self.message}" + (f" ({self.path})" if self.path else "")


class ValidationError(ValueError):
    def __init__(self, issues: Iterable[ValidationIssue]):
        self.issues = tuple(issues)
        super().__init__("; ".join(map(str, self.issues)))


def _variables(term):
    return {term.name} if isinstance(term, Variable) else set()


def _atom_vars(atom: Atom):
    result = set()
    for term in atom.terms: result.update(_variables(term))
    return result


def validate_bundle(bundle: Bundle) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    relations = {r.name: r for r in bundle.relations}
    if len(relations) != len(bundle.relations):
        issues.append(ValidationIssue("duplicate-relation", "relation names must be unique", "relations"))
    for relation in bundle.relations:
        _validate_relation(relation, issues)
    for i, fact in enumerate(bundle.facts):
        _validate_atom(fact, relations, issues, f"facts[{i}]")
        if fact.negated:
            issues.append(ValidationIssue("negative-fact", "facts must be positive", f"facts[{i}]"))
    for i, rule in enumerate(bundle.rules):
        _validate_rule(rule, relations, issues, f"rules[{i}]")
    for i, claim in enumerate(bundle.claims):
        relation = relations.get(claim.relation)
        if relation is None:
            issues.append(ValidationIssue("unknown-relation", claim.relation, f"claims[{i}]"))
        elif len(claim.terms) != relation.arity:
            issues.append(ValidationIssue("arity", f"expected {relation.arity}, got {len(claim.terms)}", f"claims[{i}]"))
    _validate_recursion(bundle, relations, issues)
    return tuple(issues)


def assert_valid(bundle: Bundle) -> Bundle:
    issues = validate_bundle(bundle)
    if issues: raise ValidationError(issues)
    return bundle


def validate(bundle: Bundle) -> tuple[ValidationIssue, ...]:
    """Alias with a deliberately non-throwing API for corpus tooling."""
    return validate_bundle(bundle)


def _validate_relation(r: RelationDecl, issues, path="relations"):
    if not r.name or not r.name.replace("_", "a").isalnum() or r.name[0].isdigit():
        issues.append(ValidationIssue("name", "relation name must be an identifier", f"{path}.{r.name}"))
    names = [c.name for c in r.columns]
    if len(names) != len(set(names)):
        issues.append(ValidationIssue("duplicate-column", "column names must be unique", f"{path}.{r.name}"))
    for index in r.context_indices:
        if index not in names:
            issues.append(ValidationIssue("context-index", f"unknown context column {index!r}", f"{path}.{r.name}"))
        elif not r.columns[names.index(index)].context:
            issues.append(ValidationIssue("context-index", f"column {index!r} is not marked context", f"{path}.{r.name}"))


def _validate_atom(atom, relations, issues, path):
    relation = relations.get(atom.relation)
    if relation is None:
        issues.append(ValidationIssue("unknown-relation", atom.relation, path)); return
    if len(atom.terms) != relation.arity:
        issues.append(ValidationIssue("arity", f"expected {relation.arity}, got {len(atom.terms)}", path))


def _validate_rule(rule: Rule, relations, issues, path):
    _validate_atom(rule.head, relations, issues, f"{path}.head")
    for j, atom in enumerate(rule.body):
        if isinstance(atom, Comparison):
            if atom.operator not in {"=", "!=", "<", "<=", ">", ">="}:
                issues.append(ValidationIssue("operator", atom.operator, f"{path}.body[{j}]"))
        else:
            _validate_atom(atom, relations, issues, f"{path}.body[{j}]")
    positive_vars = set().union(*(_atom_vars(a) for a in rule.body if isinstance(a, Atom) and not a.negated)) if rule.body else set()
    head_vars = _atom_vars(rule.head)
    missing = head_vars - positive_vars
    if missing:
        issues.append(ValidationIssue("unsafe-variable", f"head variables not positively bound: {sorted(missing)}", path))
    bound = set(positive_vars)
    for j, atom in enumerate(rule.body):
        vars_ = (_atom_vars(atom) if isinstance(atom, Atom) else _variables(atom.left) | _variables(atom.right))
        if isinstance(atom, Atom) and atom.negated:
            if not vars_.issubset(bound):
                issues.append(ValidationIssue("unsafe-negation", f"variables not bound before negation: {sorted(vars_ - bound)}", f"{path}.body[{j}]"))
        elif isinstance(atom, Comparison) and not vars_.issubset(bound):
            issues.append(ValidationIssue("unsafe-comparison", f"variables not bound: {sorted(vars_ - bound)}", f"{path}.body[{j}]"))
    for j, negated in enumerate(a for a in rule.body if isinstance(a, Atom) and a.negated):
        # A generic completeness flag is not enough: its context must bind the
        # same scope as the predicate whose absence is being asserted.
        complete_atoms = [a for a in rule.body if isinstance(a, Atom) and not a.negated
                          and relations.get(a.relation) is not None
                          and relations[a.relation].modality.value == "completeness"]
        neg_vars = _atom_vars(negated)
        if not any(neg_vars.issubset(_atom_vars(c)) for c in complete_atoms):
            issues.append(ValidationIssue("missing-completeness", "negated telemetry requires a scoped completeness premise", path))
    if rule.aggregation:
        _validate_aggregation(rule.aggregation, relations, issues, path)


def _validate_aggregation(a: Aggregation, relations, issues, path):
    if a.operator not in {"count", "sum", "min", "max", "any", "all"}:
        issues.append(ValidationIssue("aggregation", f"unsupported operator {a.operator!r}", path))
    if a.relation not in relations: issues.append(ValidationIssue("unknown-relation", a.relation, path))
    if not a.domain: issues.append(ValidationIssue("aggregation-domain", "aggregation requires a named finite domain", path))
    if not a.closure_witness: issues.append(ValidationIssue("aggregation-closure", "aggregation requires a closure witness", path))
    if a.operator == "all" and not a.domain:
        issues.append(ValidationIssue("aggregation-domain", "universal aggregation needs a non-empty domain", path))


def _validate_recursion(bundle, relations, issues):
    edges: dict[str, list[tuple[str, bool]]] = {r.name: [] for r in bundle.relations}
    for rule in bundle.rules:
        for atom in rule.body:
            if isinstance(atom, Atom) and atom.relation in edges:
                edges[rule.head.relation].append((atom.relation, atom.negated))
    # A negative edge inside a recursive strongly connected component is
    # recursive negation, which this fragment intentionally rejects.
    nodes = set(edges)
    for start in nodes:
        seen = set(); stack = [start]
        while stack:
            node = stack.pop()
            if node in seen: continue
            seen.add(node); stack.extend(dst for dst, _ in edges[node])
        for dst, negative in edges[start]:
            if negative and dst in seen and start in _reachable(edges, dst, start):
                issues.append(ValidationIssue("recursive-negation", f"negative cycle involving {start} and {dst}", "rules"))


def _reachable(edges, source, target):
    seen = set(); stack = [source]
    while stack:
        n = stack.pop()
        if n == target: return seen | {n}
        if n in seen: continue
        seen.add(n); stack.extend(x for x, _ in edges[n])
    return seen
