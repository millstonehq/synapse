"""Finite fact-state flow planning. No inferred edge is treated as confirmed."""

from __future__ import annotations

import hashlib
import json
import re
from collections import deque


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def repository_path(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not any(part in {"", ".", ".."} for part in value.split("/"))
        and not any(char in value for char in ("\\", ":", "\0"))
    )


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
                if c.get("op") not in {"goto", "fill", "click", "drag", "select", "upload", "assert", "remember-path", "visit-path"}:
                    raise ValueError(f"{name}/{target}: unsupported command {c.get('op')}")
                if c["op"] == "goto" and (
                    not c.get("path", "").startswith("/") or c["path"].startswith("//")
                ):
                    raise ValueError(f"{name}/{target}: goto must be an absolute local path")
                if (c["op"] not in {"goto", "remember-path", "visit-path"}
                    and not (c["op"] == "assert" and c.get("mode") == "http")
                    and not c.get("selector")):
                    raise ValueError(f"{name}/{target}: selector required")
                if c["op"] in {"remember-path", "visit-path"} and (
                    not isinstance(c.get("name"), str)
                    or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", c["name"])
                    or any(key in c for key in ("selector", "path", "value"))
                ):
                    raise ValueError(f"{name}/{target}: saved path requires an unambiguous name")
                if c["op"] == "visit-path" and (
                    type(c.get("expect_status")) is not int
                    or not 200 <= c["expect_status"] <= 599
                ):
                    raise ValueError(f"{name}/{target}: visit-path requires an expected HTTP status")
                if c["op"] == "remember-path" and "expect_status" in c:
                    raise ValueError(f"{name}/{target}: remembering a path performs no HTTP request")
                if c["op"] == "drag":
                    points = (c.get("from"), c.get("to"))
                    if any(
                        not isinstance(point, list) or len(point) != 2
                        or any(type(value) not in (int, float) or not 0 <= value <= 1
                               for value in point)
                        for point in points
                    ) or points[0] == points[1]:
                        raise ValueError(
                            f"{name}/{target}: drag requires distinct from/to coordinate "
                            "pairs within the element's normalized 0..1 bounds"
                        )
                if "confirmation" in c:
                    confirmation = c["confirmation"]
                    if (
                        c["op"] != "click"
                        or not isinstance(confirmation, dict)
                        or set(confirmation) != {"message", "action"}
                        or not isinstance(confirmation["message"], str)
                        or not 1 <= len(confirmation["message"]) <= 1024
                        or confirmation["action"] not in ("accept", "dismiss")
                    ):
                        raise ValueError(
                            f"{name}/{target}: confirmation requires a click, exact message "
                            "(1..1024 characters), and accept/dismiss action"
                        )
                if c["op"] == "select" and not isinstance(c.get("value"), str):
                    raise ValueError(f"{name}/{target}: select requires a string option value")
                if c["op"] == "upload":
                    files = c.get("files")
                    if not isinstance(files, list) or not files or any(
                        not repository_path(path) for path in files
                    ):
                        raise ValueError(
                            f"{name}/{target}: upload requires repository-relative POSIX file paths"
                        )
                if "refresh_timeout_ms" in c and (
                    c["op"] != "assert"
                    or type(c["refresh_timeout_ms"]) is not int
                    or not 1 <= c["refresh_timeout_ms"] <= 60_000
                ):
                    raise ValueError(
                        f"{name}/{target}: refresh_timeout_ms requires an assertion and 1..60000 integer milliseconds"
                    )
                if c["op"] == "assert":
                    mode = c.get("mode", "text")
                    if not isinstance(mode, str) or mode not in {"text", "absent", "download", "http"}:
                        raise ValueError(f"{name}/{target}: unsupported assertion mode {mode!r}")
                    if mode == "http":
                        form = c.get("form", {})
                        path = c.get("path")
                        if (
                            not isinstance(c.get("method"), str) or c["method"] not in {"GET", "POST"}
                            or not isinstance(path, str)
                            or not re.fullmatch(r"/(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]*", path)
                            or type(c.get("expect_status")) is not int
                            or not (200 <= c["expect_status"] <= 299 or 400 <= c["expect_status"] <= 599)
                            or not isinstance(c.get("text"), str) or not c["text"]
                            or not isinstance(form, dict) or len(form) > 32
                            or any(not isinstance(k, str) or not 1 <= len(k) <= 128
                                   or not isinstance(v, str) or len(v) > 4096
                                   for k, v in form.items())
                            or (c["method"] == "GET" and "form" in c)
                            or any(k in c for k in ("selector", "file", "files", "name", "value", "refresh_timeout_ms", "headers", "body"))
                        ):
                            raise ValueError(f"{name}/{target}: invalid HTTP assertion path, method, response or form")
                    if mode == "text" and not c.get("text"):
                        raise ValueError(f"{name}/{target}: content assertion required")
                    if mode == "absent" and "text" in c:
                        raise ValueError(f"{name}/{target}: absence assertion cannot carry text")
                    if mode == "download" and (
                        not repository_path(c.get("file"))
                        or "text" in c
                        or "refresh_timeout_ms" in c
                    ):
                        raise ValueError(
                            f"{name}/{target}: download assertion requires a repository-relative expected file, without text or refresh"
                        )


def enabled(t: dict, state: frozenset[str]) -> bool:
    return set(t.get("requires", [])) <= state and not set(t.get("forbids", [])) & state


def advance(t: dict, state: frozenset[str]) -> frozenset[str]:
    return frozenset((state - set(t.get("removes", []))) | set(t.get("adds", [])))


def plan(model: dict, target: str, max_states: int = 10000) -> dict:
    """Shortest prerequisite path to every transition; bounds fail explicitly."""
    if type(max_states) is not int or max_states < 1:
        raise ValueError("max_states must be a positive integer")
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
        **({"max_states": max_states} if max_states != 10000 else {}),
    }


def reconcile(inventory: dict, model: dict, execution_plan: dict, run: dict | None) -> dict:
    """Accounted, executable, and proven are different denominators."""
    validate(model)
    failures = []
    if execution_plan["model_sha256"] != digest(model):
        raise ValueError("plan was built from a different model")
    expected = plan(model, execution_plan["target"], execution_plan.get("max_states", 10000))
    if expected != execution_plan:
        raise ValueError("plan does not match the derived scenarios")
    obligations = {o["id"]: o for o in inventory["obligations"]}
    if len(obligations) != len(inventory["obligations"]):
        raise ValueError("duplicate inventory obligations")
    if not obligations:
        raise ValueError("empty inventory cannot establish completeness")
    # Branch/exception IDs share the http: namespace, but are not URLs. Their
    # request evidence belongs to the declared parent route. Never discard a
    # missing parent and accidentally waive the HTTP evidence requirement.
    for name, item in obligations.items():
        if name.startswith("http:"):
            parent = name if item.get("kind") == "surface" else item.get("surface")
            if (
                not isinstance(parent, str) or not parent.startswith("http:")
                or obligations.get(parent, {}).get("kind") != "surface"
            ):
                raise ValueError(f"invalid or missing parent surface: {name}")
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
    execution_scope = (run or {}).get("execution_scope", "full")
    if execution_scope not in ("full", "diagnostic"):
        raise ValueError("unknown execution scope")
    if execution_scope == "diagnostic":
        failures.append("diagnostic execution does not qualify coverage")
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
        if (
            static_http and mounted == static_http and run.get("status") == "passed"
            and execution_scope == "full"
        ):
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
                    o if obligations[o].get("kind") == "surface" else obligations[o]["surface"]
                    for o in by_transition[step["transition"]]["obligations"]
                    if o.startswith("http:") and o in obligations
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
                if execution_scope == "full":
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
        "execution_scope": execution_scope,
        "rows": rows,
        "blocked": execution_plan["blocked"],
        "failures": failures,
        "summary": {
            status: sum(r["status"] == status for r in rows)
            for status in ("covered", "unproven", "unmapped")
        },
        "complete": not failures,
    }
