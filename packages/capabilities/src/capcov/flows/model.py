"""Finite fact-state flow planning. No inferred edge is treated as confirmed."""

from __future__ import annotations

import hashlib
import json
from collections import deque


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def validate(model: dict) -> None:
    if model.get("version") != 1:
        raise ValueError("flow model version must be 1")
    if not model.get("scope") or not model.get("transitions"):
        raise ValueError("a named scope and nonempty transitions are required")
    facts = model.get("facts", [])
    if len(facts) != len(set(facts)):
        raise ValueError("duplicate facts")
    known = set(facts)
    if not set(model.get("initial", [])) <= known:
        raise ValueError("unknown initial fact")
    ids = set()
    for t in model["transitions"]:
        name = t["id"]
        if not name or name in ids:
            raise ValueError(f"duplicate or empty transition: {name}")
        ids.add(name)
        for field in ("requires", "forbids", "adds", "removes"):
            if not set(t.get(field, [])) <= known:
                raise ValueError(f"{name}: unknown fact in {field}")
        if set(t.get("adds", [])) & set(t.get("removes", [])):
            raise ValueError(f"{name}: adds and removes the same fact")
        if set(t.get("requires", [])) & set(t.get("forbids", [])):
            raise ValueError(f"{name}: contradictory preconditions")
        if not all(t.get(k) for k in ("actor", "outcome", "evidence")):
            raise ValueError(f"{name}: actor, outcome, and source evidence required")
        if not t.get("obligations"):
            raise ValueError(f"{name}: no inventory obligations")
        bindings = t.get("bindings", {})
        for target, binding in bindings.items():
            commands = binding.get("commands", [])
            assertions = [c for c in commands if c.get("op") == "assert"]
            if not assertions:
                raise ValueError(f"{name}/{target}: no observable assertion")
            assertion_ids = [a["id"] for a in assertions]
            if len(set(assertion_ids)) != len(assertion_ids):
                raise ValueError(f"{name}/{target}: duplicate assertion")
            for c in commands:
                if c.get("op") not in {"goto", "fill", "click", "assert"}:
                    raise ValueError(f"{name}/{target}: unsupported command {c.get('op')}")
                if c["op"] == "goto" and (
                    not c.get("path", "").startswith("/") or c["path"].startswith("//")
                ):
                    raise ValueError(f"{name}/{target}: goto must be an absolute local path")
                if c["op"] != "goto" and not c.get("selector"):
                    raise ValueError(f"{name}/{target}: selector required")
                if c["op"] == "assert" and not c.get("text"):
                    raise ValueError(f"{name}/{target}: content assertion required")


def enabled(t: dict, state: frozenset[str]) -> bool:
    return set(t.get("requires", [])) <= state and not set(t.get("forbids", [])) & state


def advance(t: dict, state: frozenset[str]) -> frozenset[str]:
    return frozenset((state - set(t.get("removes", []))) | set(t.get("adds", [])))


def plan(model: dict, target: str, max_states: int = 10000) -> dict:
    """Shortest prerequisite path to every transition; bounds fail explicitly."""
    validate(model)
    initial = frozenset(model.get("initial", []))
    queue = deque([(initial, [])])
    seen = {initial}
    paths: dict[str, list[str]] = {}
    transitions = {t["id"]: t for t in model["transitions"]}
    while queue:
        state, path = queue.popleft()
        for name, t in sorted(transitions.items()):
            if target not in t.get("bindings", {}) or not enabled(t, state):
                continue
            candidate = [*path, name]
            paths.setdefault(name, candidate)
            after = advance(t, state)
            if after not in seen:
                seen.add(after)
                if len(seen) > max_states:
                    raise ValueError(
                        f"state budget exceeded ({max_states}); no complete plan emitted"
                    )
                queue.append((after, candidate))
    scenarios = []
    for name, path in sorted(paths.items()):
        scenarios.append(
            {
                "id": name,
                "steps": [
                    {
                        "transition": step,
                        "commands": transitions[step]["bindings"][target]["commands"],
                    }
                    for step in path
                ],
            }
        )
    return {
        "version": 1,
        "scope": model["scope"],
        "target": target,
        "model_sha256": digest(model),
        "scenarios": scenarios,
        "blocked": [
            {
                "transition": name,
                "reason": (
                    "missing target binding"
                    if target not in t.get("bindings", {})
                    else "unreachable preconditions"
                ),
            }
            for name, t in sorted(transitions.items())
            if name not in paths
        ],
        "states_explored": len(seen),
    }


def reconcile(inventory: dict, model: dict, execution_plan: dict, run: dict | None) -> dict:
    """Accounted, executable, and proven are different denominators."""
    validate(model)
    failures = []
    if execution_plan["model_sha256"] != digest(model):
        raise ValueError("plan was built from a different model")
    expected = plan(model, execution_plan["target"])
    if expected != execution_plan:
        raise ValueError("plan does not match the derived scenarios")
    obligations = {o["id"]: o for o in inventory["obligations"]}
    if len(obligations) != len(inventory["obligations"]):
        raise ValueError("duplicate inventory obligations")
    if not obligations:
        raise ValueError("empty inventory cannot establish completeness")
    mapped: dict[str, set[str]] = {}
    claimed_outcomes: dict[tuple[str, str], set[str]] = {}
    for t in model["transitions"]:
        for obligation in t["obligations"]:
            if obligation not in obligations:
                failures.append(f"unknown obligation: {t['id']} -> {obligation}")
            mapped.setdefault(obligation, set()).add(t["id"])
            for outcome in t.get("covers_outcomes", {}).get(obligation, []):
                required = obligations.get(obligation, {}).get("outcomes", [])
                if outcome not in required:
                    failures.append(f"unknown outcome: {t['id']} -> {obligation}:{outcome}")
                claimed_outcomes.setdefault((obligation, outcome), set()).add(t["id"])
    passed = set()
    resolved_boundaries = set()
    if run is not None:
        if run.get("plan_sha256") != digest(execution_plan):
            raise ValueError("run was produced from a different plan")
        if run.get("inventory_sha256") != digest(inventory):
            raise ValueError("run was produced from a different inventory")
        if run.get("status") != "passed":
            failures.append("execution did not pass")
        static_http = {
            name
            for name, item in obligations.items()
            if name.startswith("http:") and item.get("kind") == "surface"
        }
        mounted = set(run.get("mounted_surfaces", []))
        if static_http and mounted == static_http and run.get("status") == "passed":
            resolved_boundaries.add("boundary:python:mounted-route-confirmation")
        elif mounted:
            for name in sorted(mounted - static_http):
                failures.append(f"runtime-only surface: {name}")
            for name in sorted(static_http - mounted):
                failures.append(f"unmounted surface: {name}")
        results = run.get("scenarios", [])
        by_id = {s["id"]: s for s in results}
        expected_ids = {s["id"] for s in execution_plan["scenarios"]}
        if len(by_id) != len(results) or set(by_id) != expected_ids:
            failures.append("execution scenario set differs from plan")
        for scenario in execution_plan["scenarios"]:
            result = by_id.get(scenario["id"], {})
            by_transition = {t["id"]: t for t in model["transitions"]}
            missing_surfaces = []
            for i, step in enumerate(scenario["steps"]):
                expected_surfaces = {
                    o
                    for o in by_transition[step["transition"]]["obligations"]
                    if o.startswith("http:")
                }
                actual_surfaces = {
                    o["surface"]
                    for o in result.get("observed_requests", [])
                    if o["step"] == f"{i}:{step['transition']}"
                }
                missing_surfaces.extend(expected_surfaces - actual_surfaces)
            for surface in sorted(set(missing_surfaces)):
                failures.append(f"missing surface evidence: {scenario['id']} -> {surface}")
            required = [
                f"{i}:{step['transition']}:{c['id']}"
                for i, step in enumerate(scenario["steps"])
                for c in step["commands"]
                if c["op"] == "assert"
            ]
            if (
                result.get("status") == "passed"
                and result.get("assertions") == required
                and run.get("status") == "passed"
                and not missing_surfaces
            ):
                passed.update(s["transition"] for s in scenario["steps"])
            else:
                failures.append(f"missing outcome evidence: {scenario['id']}")
    rows = []
    for name, obligation in sorted(obligations.items()):
        owners = mapped.get(name, set())
        missing_outcomes = [
            outcome
            for outcome in obligation.get("outcomes", [])
            if not (claimed_outcomes.get((name, outcome), set()) & passed)
        ]
        can_cover = (
            owners <= passed and not missing_outcomes and obligation.get("kind") != "unresolved"
        )
        rows.append(
            {
                **obligation,
                "transitions": sorted(owners),
                "missing_outcomes": missing_outcomes,
                "status": (
                    "covered"
                    if name in resolved_boundaries
                    else "unmapped"
                    if not owners
                    else "covered"
                    if can_cover
                    else "unproven"
                ),
                "resolution": "runtime-mount-census" if name in resolved_boundaries else None,
            }
        )
    for row in rows:
        if row["status"] != "covered":
            failures.append(f"{row['status']}: {row['id']}")
    for blocked in execution_plan["blocked"]:
        failures.append(f"blocked: {blocked['transition']}: {blocked['reason']}")
    return {
        "version": 1,
        "scope": model["scope"],
        "target": execution_plan["target"],
        "assurance": (run or {}).get("assurance", "unexecuted"),
        "rows": rows,
        "blocked": execution_plan["blocked"],
        "failures": failures,
        "summary": {
            status: sum(r["status"] == status for r in rows)
            for status in ("covered", "unproven", "unmapped")
        },
        "complete": not failures,
    }
