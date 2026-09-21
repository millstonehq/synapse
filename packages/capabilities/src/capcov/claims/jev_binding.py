"""Content-addressed binding of a Jev advisory to an authoritative judge run.

The binding is provenance, not authority.  It records which exact advisory was
available beside which exact deterministic judgment, but never changes the
judgment's verdict or exit code and exports no claim facts or rules.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from . import jev
from .souffle import compile as souffle_compile


ARTIFACT_KIND = "capcov-jev-judge-binding-v1"
ALLOWED_EXIT_CODES = {0, 1, 5}
ADVISORY_KEYS = frozenset({
    "schema_version", "kind", "producer", "subject_id", "model",
    "requested_model", "request", "state_sha256", "request_sha256",
    "candidate_set_sha256", "candidates", "judgments", "usage",
    "response_provenance", "response", "raw_response_utf8",
    "evidence_semantics", "assessment_id",
})
PATTERN_KEYS = frozenset({
    "schema_version", "kind", "producer", "subject_id", "pattern_id",
    "state_sha256", "runs", "sensitivity", "evidence_semantics",
    "assessment_id",
})


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise jev.JevError("invalid-input", f"{path} must be an object")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise jev.JevError("invalid-input", f"{path} must be nonempty")
    return value


def _digest(value: Any, path: str) -> str:
    value = _text(value, path)
    if len(value) != 64 or value != value.lower():
        raise jev.JevError("invalid-input", f"{path} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise jev.JevError("invalid-input", f"{path} must be a lowercase sha256 digest") from exc
    return value


def _judge_identity(judge: Mapping[str, Any]) -> dict[str, Any]:
    if judge.get("schema") != "capcov-compiled-judge-v1":
        raise jev.JevError("invalid-input", "judge must be capcov-compiled-judge-v1")
    receipt = _object(judge.get("receipt"), "judge.receipt")
    pack = _object(judge.get("pack"), "judge.pack")
    kernels = _object(judge.get("kernels"), "judge.kernels")
    compiled = _object(judge.get("compiled"), "judge.compiled")
    findings = judge.get("contract_findings")
    if findings != []:
        raise jev.JevError("invalid-input", "judge must have no contract findings")
    failures = kernels.get("failures")
    if failures != {}:
        raise jev.JevError("invalid-input", "judge must have no kernel operational failures")
    if kernels.get("matched") is not True or kernels.get("closure_digest_equal") is not True:
        raise jev.JevError("invalid-input", "judge kernels must agree before an advisory is bound")
    semantic_digests = [_digest(kernels.get(name), f"judge.kernels.{name}") for name in (
        "python_digest", "souffle_digest", "compiled_digest")]
    if len(set(semantic_digests)) != 1:
        raise jev.JevError("invalid-input", "judge kernel semantic digests must be identical")
    closure_digests = [_digest(kernels.get(name), f"judge.kernels.{name}") for name in (
        "souffle_closure_digest", "compiled_closure_digest", "closure_digest")]
    if len(set(closure_digests)) != 1:
        raise jev.JevError("invalid-input", "judge Souffle closure digests must be identical")
    exit_code = judge.get("exit_code")
    if type(exit_code) is not int or exit_code not in ALLOWED_EXIT_CODES:
        raise jev.JevError("invalid-input", "judge.exit_code must be 0, 1, or 5")
    verdict = _text(judge.get("verdict"), "judge.verdict")
    expected_verdict = {0: "supported", 1: "not-supported", 5: "pending-premise"}[exit_code]
    if verdict != expected_verdict:
        raise jev.JevError("invalid-input", "judge verdict and exit code disagree")
    program_digest = _digest(pack.get("program_digest"), "judge.pack.program_digest")
    if compiled.get("schema") != "capcov-souffle-compiled-v1":
        raise jev.JevError("invalid-input", "judge compiled checker schema is invalid")
    compiled_program = _digest(compiled.get("program_digest"), "judge.compiled.program_digest")
    if compiled_program != program_digest:
        raise jev.JevError("invalid-input", "judge pack and compiled program digests disagree")
    souffle_digest = _digest(compiled.get("souffle_sha256"), "judge.compiled.souffle_sha256")
    compiler_digest = _digest(
        compiled.get("compiler_config_sha256"), "judge.compiled.compiler_config_sha256")
    binary_digest = _digest(compiled.get("binary_sha256"), "judge.compiled.binary_sha256")
    flags = compiled.get("compile_flags")
    if (not isinstance(flags, list) or not flags
            or any(not isinstance(flag, str) or not flag for flag in flags)):
        raise jev.JevError("invalid-input", "judge.compiled.compile_flags must be nonempty strings")
    compile_key = _digest(compiled.get("compile_key"), "judge.compiled.compile_key")
    expected_key = souffle_compile.compile_key(
        program_digest, souffle_digest, flags,
        compiler_config_sha256=compiler_digest)
    if compile_key != expected_key:
        raise jev.JevError("invalid-input", "judge compiled checker key does not match its inputs")
    ops = _object(judge.get("ops"), "judge.ops")
    certificates: dict[str, str | None] = {}
    for op, entry in sorted(ops.items()):
        if not isinstance(op, str) or not op:
            raise jev.JevError("invalid-input", "judge op names must be nonempty")
        entry = _object(entry, f"judge.ops.{op}")
        certificate = entry.get("certificate_sha256")
        certificates[op] = None if certificate is None else _digest(
            certificate, f"judge.ops.{op}.certificate_sha256")
    required_ops = judge.get("required_ops")
    if (not isinstance(required_ops, list)
            or any(not isinstance(op, str) or not op for op in required_ops)):
        raise jev.JevError("invalid-input", "judge.required_ops must be an array of names")
    if len(required_ops) != len(set(required_ops)):
        raise jev.JevError("invalid-input", "judge.required_ops contains duplicates")
    judged = required_ops or sorted(ops)
    unmet = []
    pending = []
    for op in judged:
        entry = ops.get(op)
        qualified = (isinstance(entry, Mapping)
                     and entry.get("verdict") == "supported"
                     and entry.get("qualification") == "qualified"
                     and isinstance(entry.get("op_qualified"), Mapping)
                     and entry["op_qualified"].get("semantic") == "supported"
                     and entry["op_qualified"].get("operational") == "complete"
                     and entry["op_qualified"].get("missing_premises") == [])
        if not qualified:
            unmet.append(op)
            op_qualified = entry.get("op_qualified") if isinstance(entry, Mapping) else None
            if (isinstance(entry, Mapping)
                    and entry.get("verdict") == "not-supported"
                    and str(entry.get("qualification", "")).startswith("pending ")
                    and isinstance(op_qualified, Mapping)
                    and op_qualified.get("semantic") == "unresolved"
                    and op_qualified.get("operational") == "complete"
                    and isinstance(op_qualified.get("missing_premises"), list)
                    and op_qualified["missing_premises"]):
                pending.append(op)
    derived_exit = 0 if judged and not unmet else (5 if unmet and pending == unmet else 1)
    if exit_code != derived_exit:
        raise jev.JevError(
            "invalid-input", "judge exit code disagrees with required operation qualifications")
    return {
        "run": _text(receipt.get("run"), "judge.receipt.run"),
        "model_digest": _digest(receipt.get("model"), "judge.receipt.model"),
        "snapshot_digest": _digest(receipt.get("snapshot"), "judge.receipt.snapshot"),
        "rule_pack_id": _text(pack.get("id"), "judge.pack.id"),
        "rule_program_digest": program_digest,
        "compiled": {"compile_key": compile_key, "binary_sha256": binary_digest,
                     "souffle_sha256": souffle_digest,
                     "compiler_config_sha256": compiler_digest,
                     "compile_flags": list(flags)},
        "kernel_semantics_digest": semantic_digests[0],
        "closure_digest": closure_digests[0],
        "certificate_digests": certificates,
        "required_ops": list(required_ops),
        "verdict": verdict,
        "exit_code": exit_code,
    }


def bind(advisory: Mapping[str, Any], judge: Mapping[str, Any]) -> dict[str, Any]:
    """Bind exact advisory and judge documents without changing authority."""
    if advisory.get("kind") not in {jev.ARTIFACT_KIND, "capcov-jev-pattern-sensitivity-v1"}:
        raise jev.JevError("invalid-input", "unsupported Jev advisory kind")
    if advisory.get("schema_version") != 1:
        raise jev.JevError("invalid-input", "advisory.schema_version must be 1")
    allowed = ADVISORY_KEYS if advisory.get("kind") == jev.ARTIFACT_KIND else PATTERN_KEYS
    if set(advisory) != allowed:
        missing, extra = allowed - set(advisory), set(advisory) - allowed
        detail = []
        if missing:
            detail.append("missing " + ", ".join(sorted(missing)))
        if extra:
            detail.append("unknown " + ", ".join(sorted(extra)))
        raise jev.JevError("invalid-input", "advisory fields are invalid: " + "; ".join(detail))
    if advisory.get("kind") == jev.ARTIFACT_KIND:
        jev.claims_bundle(advisory)
    else:
        # Import here to keep the generic Jev module below its pattern adapter.
        from . import jev_patterns
        jev_patterns.claims_bundle(advisory)
    identity = _judge_identity(judge)
    core = {
        "schema_version": 1,
        "kind": ARTIFACT_KIND,
        "producer": {"class": "binding", "source": "capcov deterministic jev-judge-binding-v1"},
        "advisory": {
            "kind": advisory["kind"],
            "assessment_id": advisory["assessment_id"],
            "sha256": jev._digest(jev._plain_json(advisory, "advisory")),
            "response_raw_sha256": advisory.get("response_provenance", {}).get("raw_sha256"),
            "response_canonical_sha256": advisory.get("response_provenance", {}).get("canonical_sha256"),
            "response_mode": advisory.get("response_provenance", {}).get("mode"),
            "service_attested": advisory.get("response_provenance", {}).get("service_attested"),
        },
        "judge": {**identity, "sha256": jev._digest(jev._plain_json(judge, "judge"))},
        "authority": {
            "advisory_may_rank_or_request_probe": True,
            "advisory_may_change_verdict": False,
            "advisory_may_change_exit_code": False,
            "advisory_may_satisfy_missing_premise": False,
            "advisory_may_qualify_claim": False,
            "authoritative_source": "judge",
        },
    }
    core["binding_id"] = f"jev-judge:{jev._digest(core)}"
    return core


def validate(binding: Mapping[str, Any], advisory: Mapping[str, Any],
             judge: Mapping[str, Any]) -> None:
    """Require a binding to be exactly reproducible from both input artifacts."""
    if not isinstance(binding, Mapping) or binding != bind(advisory, judge):
        raise jev.JevError("invalid-input", "binding does not match the advisory and judge")
