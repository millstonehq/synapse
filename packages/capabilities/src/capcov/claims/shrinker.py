"""Validity-preserving bounded ddmin for differential claim bundles."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from .ir import Atom, Bundle, Constant, bundle_from_json, canonical_json, digest
from .validation import assert_valid


MAX_SHRINK_STEPS = 200


@dataclass(frozen=True)
class ShrinkResult:
    bundle: Bundle
    path: Path
    steps: int
    truncated: bool
    reproduced: bool


class ReplayPersistenceError(RuntimeError):
    """A differential mismatch could not be persisted and reload-checked."""


def persist_bundle(bundle: Bundle, replay_root: str | Path) -> Path:
    """Persist and independently reload-check one canonical replay bundle."""
    root = Path(replay_root)
    path = root / f"{digest(bundle)}.json"
    try:
        root.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(bundle) + "\n", encoding="utf-8")
        # Strict parsing and digest identity apply even when the differential
        # input is itself invalid.  Candidate validity is checked separately.
        reloaded = bundle_from_json(path.read_text(encoding="utf-8"), validate=False)
    except (OSError, TypeError, ValueError) as exc:
        raise ReplayPersistenceError(f"differential replay persistence failed: {path}: {exc}") from exc
    if digest(reloaded) != digest(bundle):
        raise ReplayPersistenceError("persisted replay digest changed on reload")
    return path


def _key(atom: Atom) -> tuple[str, str]:
    return atom.relation, canonical_json(tuple(term.value if isinstance(term, Constant) else None
                                                for term in atom.terms))


Unit = tuple[str, str, str]


def _fact_unit(atom: Atom) -> Unit:
    relation, row = _key(atom)
    return "fact", relation, row


def _evidence_unit(record: Any) -> Unit:
    return "evidence", record.id, ""


def _units(bundle: Bundle) -> set[Unit]:
    return ({_fact_unit(fact) for fact in bundle.facts}
            | {_evidence_unit(record) for record in bundle.evidence})


def _candidate(bundle: Bundle, selected: set[Unit]) -> Bundle | None:
    """Build a valid candidate while preserving fact/evidence dependencies."""
    facts = tuple(fact for fact in bundle.facts if _fact_unit(fact) in selected)
    fact_keys = {_key(fact) for fact in facts}
    original_ids = {record.id for record in bundle.evidence}
    evidence = [record for record in bundle.evidence
                if _evidence_unit(record) in selected and _key(record.atom) in fact_keys]

    # A retained evidence record must retain every in-bundle dependency.
    # Removing a dependency therefore removes its dependants rather than
    # manufacturing an independent producer.
    changed = True
    while changed:
        retained_ids = {record.id for record in evidence}
        next_evidence = [record for record in evidence
                         if all(dependency.startswith("external:")
                                or dependency not in original_ids
                                or dependency in retained_ids
                                for dependency in record.depends_on)]
        changed = len(next_evidence) != len(evidence)
        evidence = next_evidence

    if bundle.evidence:
        attributed = {_key(record.atom) for record in evidence}
        facts = tuple(fact for fact in facts if _key(fact) in attributed)
        fact_keys = {_key(fact) for fact in facts}
        evidence = [record for record in evidence if _key(record.atom) in fact_keys]

    retained_ids = {record.id for record in evidence}
    outputs = []
    for output in bundle.outputs:
        references = set((*output.requires_all_evidence, *output.requires_any_evidence,
                          *output.excludes_evidence))
        if output.evidence_id:
            references.add(output.evidence_id)
        references.update(value.evidence_id for _, value in output.fields if value.evidence_id)
        if references.issubset(retained_ids):
            outputs.append(output)
    candidate = replace(bundle, facts=facts, evidence=tuple(evidence), outputs=tuple(outputs))
    try:
        assert_valid(candidate)
    except ValueError:
        return None
    return candidate


def _difference_shape(left: Any, right: Any) -> tuple[Any, ...]:
    # Operational reductions preserve which side failed and each named
    # failure. Relation payloads from a surviving side are not frozen into the
    # shape, allowing irrelevant facts to be removed.
    if left.operational_failure or right.operational_failure:
        return "operational", left.operational_failure, right.operational_failure
    left_relations = dict(left.relations)
    right_relations = dict(right.relations)
    relation_names = tuple(name for name in sorted(set(left_relations) | set(right_relations))
                           if left_relations.get(name) != right_relations.get(name))
    left_claims = {claim.key: claim for claim in left.claims}
    right_claims = {claim.key: claim for claim in right.claims}
    claim_fields = []
    for key in sorted(set(left_claims) | set(right_claims)):
        a, b = left_claims.get(key), right_claims.get(key)
        fields = tuple(field for field in ("semantic", "operational", "basis", "missing_premises")
                       if a is None or b is None or getattr(a, field) != getattr(b, field))
        if fields:
            claim_fields.append((key, fields))
    return "semantic", relation_names, tuple(claim_fields)


def shrink_mismatch(bundle: Bundle, *, python_runner: Callable[[Bundle], Any],
                    souffle_runner: Callable[[Bundle], Any], replay_root: str | Path,
                    max_steps: int = MAX_SHRINK_STEPS,
                    baseline_left: Any | None = None,
                    baseline_right: Any | None = None) -> ShrinkResult:
    """Minimise fact/Evidence units within at most 200 comparisons.

    One step invokes both kernel runners.  The caller's initial comparison (or
    the optional direct-call baseline below) is outside ``steps``.  One step is
    reserved to rerun the persisted, strictly reloaded replay.
    """
    if max_steps < 1:
        raise ValueError("max_steps must be positive")
    if max_steps > MAX_SHRINK_STEPS:
        raise ValueError(f"max_steps cannot exceed {MAX_SHRINK_STEPS}")
    from .differential import reports_match

    current = _units(bundle)
    steps = 0
    truncated = False
    if baseline_left is None or baseline_right is None:
        baseline_left = python_runner(bundle)
        baseline_right = souffle_runner(bundle)
    if reports_match(baseline_left, baseline_right):
        raise ValueError("shrinking requires a differential mismatch")
    baseline_shape = _difference_shape(baseline_left, baseline_right)
    minimization_limit = max_steps - 1

    def mismatch(candidate: Bundle) -> bool:
        nonlocal steps
        if steps >= minimization_limit:
            return False
        steps += 1
        left, right = python_runner(candidate), souffle_runner(candidate)
        return (not reports_match(left, right)
                and _difference_shape(left, right) == baseline_shape)

    # Generalized ddmin first removes large chunks.
    granularity = 2
    while len(current) > 1 and steps < minimization_limit:
        ordered = sorted(current)
        size = max(1, (len(ordered) + granularity - 1) // granularity)
        chunks = [set(ordered[i:i + size]) for i in range(0, len(ordered), size)]
        reduced = False
        for chunk in chunks:
            if steps >= minimization_limit:
                truncated = True
                break
            trial = _candidate(bundle, current - chunk)
            if trial is not None and mismatch(trial):
                current = _units(trial)
                granularity = max(2, granularity - 1)
                reduced = True
                break
        if reduced:
            continue
        if granularity >= len(current):
            break
        granularity = min(len(current), granularity * 2)

    # Certify one-minimality over both facts and individual producer records.
    # Restart after every deletion because dependency pruning can expose a new
    # removable unit. If the execution budget ends, the replay is explicitly
    # bounded rather than labelled minimized.
    while True:
        removed = False
        checked_all = True
        for unit in sorted(current):
            if steps >= minimization_limit:
                truncated = True
                checked_all = False
                break
            trial = _candidate(bundle, current - {unit})
            if trial is not None and mismatch(trial):
                current = _units(trial)
                removed = True
                break
        if not removed:
            if not checked_all:
                truncated = True
            break

    minimized = _candidate(bundle, current)
    if minimized is None:
        minimized = bundle
        truncated = True
    # Persistence is not enough: execute the strictly reloaded bytes.  This
    # catches transient/nondeterministic external failures instead of calling a
    # digest match reproduction evidence.
    path = persist_bundle(minimized, replay_root)
    reloaded = bundle_from_json(path.read_text(encoding="utf-8"), validate=False)
    steps += 1
    replay_left, replay_right = python_runner(reloaded), souffle_runner(reloaded)
    reproduced = (not reports_match(replay_left, replay_right)
                  and _difference_shape(replay_left, replay_right) == baseline_shape)
    if not reproduced:
        # Preserve the originally observed disagreement input.  It remains a
        # blocking replay, but minimization/reproduction is explicitly not
        # established and must never be described as minimal.
        path = persist_bundle(bundle, replay_root)
        reloaded = bundle_from_json(path.read_text(encoding="utf-8"), validate=False)
        truncated = True
    return ShrinkResult(reloaded, path, steps, truncated, reproduced)


__all__ = ["MAX_SHRINK_STEPS", "ReplayPersistenceError", "ShrinkResult",
           "persist_bundle", "shrink_mismatch"]
