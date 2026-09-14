"""A small, deterministic evaluator for the schema-v1 claim language.

This module intentionally has no dependency on a second rule engine.  It is
the executable reference for the finite part of the IR: facts and Horn rules
are closed to a fixed point, and claims are evaluated over that closure.  The
implementation favours inspectable data structures and conservative failure
statuses over cleverness or implicit open-world assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import operator
import time
from typing import Any, Iterable, Mapping

from .ir import (Aggregation, Atom, Bundle, Claim, Comparison, Constant,
                 RelationDecl, Rule, Variable, canonical_json)
from .validation import ValidationError, assert_valid
from .verdicts import (EvaluationBasis, EvaluationResult, OperationalStatus,
                       SemanticVerdict, verdict)


Row = tuple[Any, ...]
Environment = dict[str, Any]
_MAX_PROOFS_PER_ROW = 32
_MAX_CHILD_PROOFS_PER_MATCH = 4


@dataclass(frozen=True)
class ResourceLimits:
    """Hard bounds used by the evaluator.

    ``max_iterations`` is per stratum, while rows and provenance are bundle
    wide.  ``None`` means no bound; the defaults are deliberately finite.
    """

    max_iterations: int | None = 10_000
    max_derived_rows: int | None = 100_000
    max_provenance: int | None = 100_000
    max_seconds: float | None = 30.0


@dataclass(frozen=True)
class Derivation:
    """A ground rule application, or a stable fact leaf."""

    relation: str
    row: Row
    rule: str = "fact"
    children: tuple["Derivation", ...] = ()
    leaf_id: str | None = None
    kind: str = "rule"

    def __post_init__(self) -> None:
        object.__setattr__(self, "row", tuple(self.row))
        object.__setattr__(self, "children", tuple(self.children))

    @property
    def leaves(self) -> tuple[str, ...]:
        if self.leaf_id is not None:
            return (self.leaf_id,)
        values: set[str] = set()
        for child in self.children:
            values.update(child.leaves)
        return tuple(sorted(values))

    def as_dict(self) -> dict[str, Any]:
        return {
            "relation": self.relation,
            "row": list(self.row),
            "rule": self.rule,
            "kind": self.kind,
            "leaf_id": self.leaf_id,
            "children": [child.as_dict() for child in self.children],
            "leaves": list(self.leaves),
        }


@dataclass(frozen=True)
class ClaimResult:
    index: int
    claim: Claim
    result: EvaluationResult

    @property
    def semantic(self) -> SemanticVerdict:
        return self.result.semantic

    @property
    def operational(self) -> OperationalStatus:
        return self.result.operational

    def as_dict(self) -> dict[str, Any]:
        return {"index": self.index, "claim": canonical_json(self.claim), "result": self.result.as_dict()}


@dataclass(frozen=True)
class EvaluationReport:
    relations: tuple[tuple[str, tuple[Row, ...]], ...]
    provenance: tuple[tuple[str, tuple[tuple[Row, tuple[Derivation, ...]], ...]], ...]
    claims: tuple[ClaimResult, ...]
    status: OperationalStatus = OperationalStatus.COMPLETE
    message: str = ""
    resources: tuple[tuple[str, int | float], ...] = ()

    def relation_rows(self, name: str) -> tuple[Row, ...]:
        return dict(self.relations).get(name, ())

    @property
    def results(self) -> tuple[ClaimResult, ...]:
        return self.claims

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "resources": dict(self.resources),
            "relations": {name: [list(row) for row in rows] for name, rows in self.relations},
            "claims": [entry.as_dict() for entry in self.claims],
        }


class _LimitReached(RuntimeError):
    pass


class _UnsupportedConstruct(RuntimeError):
    pass


class _Engine:
    def __init__(self, bundle: Bundle, limits: ResourceLimits) -> None:
        self.bundle = bundle
        self.limits = limits
        self.started = time.monotonic()
        self.relations = {r.name: r for r in bundle.relations}
        self.rows: dict[str, set[Row]] = {name: set() for name in self.relations}
        self.proofs: dict[str, dict[Row, list[Derivation]]] = {name: {} for name in self.relations}
        self.derived_rows = 0
        self.provenance_count = 0

    def check_limits(self) -> None:
        if self.limits.max_seconds is not None and time.monotonic() - self.started > self.limits.max_seconds:
            raise _LimitReached("evaluation exceeded the time limit")
        if self.limits.max_derived_rows is not None and self.derived_rows > self.limits.max_derived_rows:
            raise _LimitReached("evaluation exceeded the derived-row limit")
        if self.limits.max_provenance is not None and self.provenance_count > self.limits.max_provenance:
            raise _LimitReached("evaluation exceeded the provenance limit")

    def add(self, relation: str, row: Row, proof: Derivation) -> bool:
        self.check_limits()
        row = tuple(row)
        if row in self.rows[relation]:
            # Keep the first canonical ground proof for each tuple.  Retaining
            # every recursive alternative would recursively duplicate proof
            # trees and make a finite closure exceed its resource budget.
            return False
        self.rows[relation].add(row)
        self.proofs[relation][row] = [proof]
        self.derived_rows += 1
        self.provenance_count += 1
        self.check_limits()
        return True

    def seed(self) -> None:
        for fact in self.bundle.facts:
            if fact.negated:
                continue
            row = tuple(_ground_term(term, {}) for term in fact.terms)
            # Evidence-policy revisions may add an authoritative id to Atom.
            # Keep the old stable row-derived id for the current IR and use
            # the explicit id whenever it exists.
            authoritative_id = next((getattr(fact, name, None)
                                     for name in ("evidence_id", "fact_id", "id", "source_id")
                                     if getattr(fact, name, None)), None)
            leaf = str(authoritative_id) if authoritative_id is not None else "fact:" + fact.relation + ":" + canonical_json(row)
            self.add(fact.relation, row, Derivation(fact.relation, row, leaf_id=leaf, kind="fact"))

    def strata(self) -> dict[str, int]:
        levels = {name: 0 for name in self.relations}
        # Validation has already rejected negative cycles.  Repeated relaxation
        # also handles dependencies that are not in the same positive SCC.
        for _ in range(max(1, len(levels) * len(levels))):
            changed = False
            for rule in self.bundle.rules:
                head = rule.head.relation
                for atom in rule.body:
                    if isinstance(atom, Atom):
                        proposed = levels[atom.relation] + (1 if atom.negated else 0)
                        if proposed > levels[head]:
                            levels[head] = proposed
                            changed = True
                if rule.aggregation is not None:
                    proposed = levels[rule.aggregation.relation]
                    if proposed > levels[head]:
                        levels[head] = proposed
                        changed = True
            if not changed:
                break
        return levels

    def run(self) -> None:
        self.seed()
        levels = self.strata()
        for level in range(max(levels.values(), default=0) + 1):
            rules = [r for r in self.bundle.rules if levels[r.head.relation] == level]
            iterations = 0
            previous_delta: Mapping[str, set[Row]] | None = None
            while True:
                iterations += 1
                if self.limits.max_iterations is not None and iterations > self.limits.max_iterations:
                    raise _LimitReached(f"stratum {level} exceeded the iteration limit")
                changed = False
                additions: dict[str, set[Row]] = {name: set() for name in self.relations}
                delta = None if iterations == 1 else previous_delta
                for rule in sorted(rules, key=lambda r: canonical_json(r)):
                    for row, proof in self._derive_rule(rule, delta):
                        if self.add(rule.head.relation, row, proof):
                            additions[rule.head.relation].add(row)
                            changed = True
                self.check_limits()
                if not changed:
                    break
                previous_delta = additions

    def _derive_rule(self, rule: Rule, delta: Mapping[str, set[Row]] | None) -> Iterable[tuple[Row, Derivation]]:
        aggregate = rule.aggregation
        source_index = None
        if aggregate is not None:
            source_index = next((i for i, atom in enumerate(rule.body)
                                 if isinstance(atom, Atom) and not atom.negated and atom.relation == aggregate.relation), None)
        body = tuple(atom for i, atom in enumerate(rule.body) if i != source_index)
        # Aggregates are non-recursive by contract, so a complete pass is
        # sufficient and avoids accidentally treating a partial group as a
        # closed finite aggregate.
        if aggregate is not None:
            for env, children in self._match_body(body, {}):
                source_atom = rule.body[source_index]  # type: ignore[index]
                candidates = list(self._match_atom(source_atom, env, positive_only=True))
                if not candidates and aggregate.operator in {"sum", "min", "max"}:
                    continue
                source_decl = self.relations[aggregate.relation]
                source_names = [c.name for c in source_decl.columns]
                try:
                    index = source_names.index(aggregate.value_variable)
                except ValueError:
                    continue
                if aggregate.operator == "count":
                    result: Any = len(candidates)
                elif aggregate.operator == "sum":
                    result = sum(_ground_term(source_atom.terms[index], candidate_env) for candidate_env, _ in candidates)
                elif aggregate.operator == "min":
                    result = min(_ground_term(source_atom.terms[index], candidate_env) for candidate_env, _ in candidates)
                elif aggregate.operator == "max":
                    result = max(_ground_term(source_atom.terms[index], candidate_env) for candidate_env, _ in candidates)
                elif aggregate.operator == "any":
                    result = any(bool(_ground_term(source_atom.terms[index], candidate_env))
                                 for candidate_env, _ in candidates)
                elif aggregate.operator == "all":
                    result = bool(candidates) and all(bool(_ground_term(source_atom.terms[index], candidate_env))
                                                       for candidate_env, _ in candidates)
                else:
                    raise _UnsupportedConstruct(f"unsupported aggregate: {aggregate.operator}")
                aggregate_env = dict(env)
                aggregate_env[aggregate.name] = result
                if aggregate.operator != "count":
                    aggregate_env.setdefault(aggregate.value_variable, result)
                row = tuple(_ground_term(t, aggregate_env) for t in rule.head.terms)
                proof_children = list(children)
                for _, proofs in candidates:
                    proof_children.extend(proofs)
                yield row, Derivation(rule.head.relation, row, rule.name or "rule", tuple(proof_children), kind="aggregate")
            return

        if delta is None:
            for env, children in self._match_body(rule.body, {}):
                row = tuple(_ground_term(t, env) for t in rule.head.terms)
                yield row, Derivation(rule.head.relation, row, rule.name or "rule", tuple(children))
            return

        # Semi-naive delta step: each positive body atom is used once as the
        # pivot against only rows added in the previous iteration.  Unioning
        # pivots prevents old tuples from redoing the full Cartesian product.
        pivots = [i for i, atom in enumerate(rule.body)
                  if isinstance(atom, Atom) and not atom.negated and delta.get(atom.relation)]
        seen: set[str] = set()
        for pivot in pivots:
            overrides = {pivot: delta[rule.body[pivot].relation]}  # type: ignore[index]
            for env, children in self._match_body(rule.body, {}, overrides):
                row = tuple(_ground_term(t, env) for t in rule.head.terms)
                proof = Derivation(rule.head.relation, row, rule.name or "rule", tuple(children))
                key = canonical_json((row, proof.as_dict()))
                if key not in seen:
                    seen.add(key)
                    yield row, proof

    def _match_body(self, body: Iterable[Atom | Comparison], env: Environment,
                    overrides: Mapping[int, set[Row]] | None = None,
                    offset: int = 0) -> Iterable[tuple[Environment, list[Derivation]]]:
        items = tuple(body)
        if not items:
            yield dict(env), []
            return
        first, rest = items[0], items[1:]
        first_index = offset
        if isinstance(first, Comparison):
            if _compare(first, env):
                yield from self._match_body(rest, env, overrides, offset + 1)
            return
        if first.negated:
            matches = list(self._match_atom(first, env, positive_only=True))
            if not matches:
                yield from self._match_body(rest, env, overrides, offset + 1)
            return
        rows_override = overrides.get(first_index) if overrides else None
        for next_env, proofs in self._match_atom(first, env, positive_only=True, rows_override=rows_override):
            for final_env, rest_proofs in self._match_body(rest, next_env, overrides, offset + 1):
                yield final_env, proofs + rest_proofs

    def _match_atom(self, atom: Atom, env: Environment, *, positive_only: bool,
                    rows_override: set[Row] | None = None) -> Iterable[tuple[Environment, list[Derivation]]]:
        del positive_only  # reserved for the future explicit negative relation form
        decl = self.relations[atom.relation]
        rows = self.rows[atom.relation] if rows_override is None else rows_override
        for row in sorted(rows, key=canonical_json):
            next_env = dict(env)
            ok = True
            for term, value in zip(atom.terms, row):
                if isinstance(term, Variable):
                    if term.name in next_env and next_env[term.name] != value:
                        ok = False
                        break
                    next_env[term.name] = value
                elif _ground_term(term, next_env) != value:
                    ok = False
                    break
            if ok:
                proofs = self.proofs[decl.name].get(row, ())
                yield next_env, list(proofs[:_MAX_CHILD_PROOFS_PER_MATCH])

    def evaluate_claim(self, index: int, claim: Claim) -> ClaimResult:
        decl = self.relations[claim.relation]
        matches: list[tuple[Row, list[Derivation]]] = []
        if claim.quantifier.value == "forall":
            domain = self.relations[claim.domain]  # validator guarantees this
            domain_names = [c.name for c in domain.columns]
            domain_rows = sorted(self.rows[domain.name], key=canonical_json)
            if not domain_rows:
                result = EvaluationResult(SemanticVerdict.UNRESOLVED, OperationalStatus.INCONSISTENT_PREMISES,
                                          EvaluationBasis.BOUNDED_HISTORY_MODEL, message="universal domain is empty")
                return ClaimResult(index, claim, result)
            subresults = []
            for drow in domain_rows:
                env = {name: value for name, value in zip(domain_names, drow)}
                claim_decl = self.relations[claim.relation]
                subclaim_terms = tuple(
                    Constant(env[t.name], claim_decl.columns[position].type)
                    if isinstance(t, Variable) and t.name in env else t
                    for position, t in enumerate(claim.terms)
                )
                subclaim = Claim(claim.relation, subclaim_terms, claim.context, "exists", None)
                subresults.append(self.evaluate_claim(index, subclaim).result)
            if any(r.operational != OperationalStatus.COMPLETE for r in subresults):
                status = next(r.operational for r in subresults if r.operational != OperationalStatus.COMPLETE)
            else:
                status = OperationalStatus.COMPLETE
            # FORALL is conjunction: every typed domain substitution must be
            # supported.  A refuted instance is evidence against the whole
            # conjunction; support from some other instance does not erase it.
            all_supported = all(r.semantic == SemanticVerdict.SUPPORTED for r in subresults)
            any_refuted = any(r.semantic in {SemanticVerdict.REFUTED, SemanticVerdict.CONFLICTING} for r in subresults)
            result = EvaluationResult(verdict(all_supported, any_refuted), status,
                                      EvaluationBasis.BOUNDED_HISTORY_MODEL,
                                      support=tuple(x for r in subresults for x in r.support),
                                      refutation=tuple(x for r in subresults for x in r.refutation),
                                      missing_premises=tuple(x for r in subresults for x in r.missing_premises))
            return ClaimResult(index, claim, result)
        for env, proofs in self._match_atom(Atom(claim.relation, claim.terms), {}, positive_only=True):
            row = tuple(_ground_term(term, env) for term in claim.terms)
            names = [c.name for c in decl.columns]
            if any(env.get(name, claim.context.as_dict().get(name)) != claim.context.as_dict().get(name) for name in decl.context_indices):
                continue
            matches.append((row, proofs))
        support = tuple(p for _, proofs in matches for p in _proof_payload(proofs, decl.polarity.value == "positive"))
        refutation = tuple(p for _, proofs in matches for p in _proof_payload(proofs, decl.polarity.value == "negative"))
        has_support = bool(support)
        has_refutation = bool(refutation)
        missing = () if matches else (f"claim:{claim.relation}:{canonical_json(claim.context.as_dict())}",)
        result = EvaluationResult(verdict(has_support, has_refutation), OperationalStatus.COMPLETE,
                                  EvaluationBasis.DERIVATIONAL, support=support, refutation=refutation,
                                  missing_premises=missing)
        return ClaimResult(index, claim, result)


def _proof_payload(proofs: Iterable[Derivation], include: bool) -> tuple[Any, ...]:
    if not include:
        return ()
    seen: dict[str, Derivation] = {}
    for proof in proofs:
        seen.update({leaf: proof for leaf in proof.leaves})
    return tuple(sorted(seen, key=str))


def _ground_term(term: Any, env: Mapping[str, Any]) -> Any:
    if isinstance(term, Variable):
        return env.get(term.name)
    if isinstance(term, Constant):
        return term.value
    return None


def _compare(comparison: Comparison, env: Mapping[str, Any]) -> bool:
    left = _ground_term(comparison.left, env)
    right = _ground_term(comparison.right, env)
    if left is None or right is None:
        return False
    operations = {"=": operator.eq, "!=": operator.ne, "<": operator.lt,
                  "<=": operator.le, ">": operator.gt, ">=": operator.ge}
    try:
        return bool(operations[comparison.operator](left, right))
    except (KeyError, TypeError):
        return False


def evaluate(bundle: Bundle, limits: ResourceLimits | None = None) -> EvaluationReport:
    """Evaluate a validated bundle and return deterministic closure/results."""
    limits = limits or ResourceLimits()
    try:
        assert_valid(bundle)
        engine = _Engine(bundle, limits)
        engine.run()
        claims = tuple(engine.evaluate_claim(i, claim) for i, claim in enumerate(bundle.claims))
        relations = tuple((name, tuple(sorted(rows, key=canonical_json))) for name, rows in sorted(engine.rows.items()))
        provenance = tuple((name, tuple((row, tuple(proofs)) for row, proofs in sorted(data.items(), key=lambda x: canonical_json(x[0]))))
                           for name, data in sorted(engine.proofs.items()))
        # Runtime is intentionally not part of the canonical result: it would
        # make shuffle/differential comparisons nondeterministic.  Callers can
        # measure wall time around evaluate() when benchmarking.
        resources = (("derived_rows", engine.derived_rows), ("provenance_nodes", engine.provenance_count))
        return EvaluationReport(relations, provenance, claims, resources=resources)
    except ValidationError as exc:
        claims = tuple(ClaimResult(i, claim, EvaluationResult(SemanticVerdict.UNRESOLVED,
                                                               OperationalStatus.INVALID_INPUT,
                                                               message=str(exc))) for i, claim in enumerate(bundle.claims))
        return EvaluationReport((), (), claims, OperationalStatus.INVALID_INPUT, str(exc))
    except _LimitReached as exc:
        claims = tuple(ClaimResult(i, claim, EvaluationResult(SemanticVerdict.UNRESOLVED,
                                                               OperationalStatus.RESOURCE_EXHAUSTED,
                                                               message=str(exc))) for i, claim in enumerate(bundle.claims))
        return EvaluationReport((), (), claims, OperationalStatus.RESOURCE_EXHAUSTED, str(exc))
    except _UnsupportedConstruct as exc:
        claims = tuple(ClaimResult(i, claim, EvaluationResult(SemanticVerdict.UNRESOLVED,
                                                               OperationalStatus.UNSUPPORTED_CONSTRUCT,
                                                               message=str(exc))) for i, claim in enumerate(bundle.claims))
        return EvaluationReport((), (), claims, OperationalStatus.UNSUPPORTED_CONSTRUCT, str(exc))


evaluate_bundle = evaluate


class PythonEvaluator:
    """Object-oriented facade useful to callers that retain configuration."""

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        self.limits = limits or ResourceLimits()

    def evaluate(self, bundle: Bundle) -> EvaluationReport:
        return evaluate(bundle, self.limits)
