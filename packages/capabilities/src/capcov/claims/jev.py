"""Jev advisory judgments over mechanically bounded candidate sets.

This module is deliberately outside the claim evaluator.  A Jev assessment is
an attributed semantic *assumption*: it can rank work or request a probe, but it
cannot close a relation, establish compatibility, report an observation, or
qualify a CapCov claim.  Deterministic evidence must perform those upgrades.

The transport is standard-library only so the production CapCov dependency
contract remains unchanged.  ``JEV_API_KEY`` is the experiment-facing secret;
``TYPESAFE_API_KEY`` is accepted as the SDK-compatible fallback.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import hashlib
import json
import math
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SCHEMA_VERSION = 1
ARTIFACT_KIND = "capcov-jev-advisory-v1"
DEFAULT_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
NO_MATCH = "no_match"
SELECTION_QUESTION = "best_candidate"
PRESENCE_QUESTION = "has_direct_match"
MAX_CANDIDATES = 64
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


class JevError(RuntimeError):
    """Named operational failure safe for CLI rendering."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _plain_json(value: Any, path: str = "request") -> Any:
    """Copy a bounded-shape JSON value and reject surprising Python values."""
    if value is None or isinstance(value, (str, bool)):
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise JevError("invalid-input", f"{path} contains a non-finite number")
        return value
    if isinstance(value, list):
        return [_plain_json(item, f"{path}[]") for item in value]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise JevError("invalid-input", f"{path} object keys must be strings")
        return {key: _plain_json(item, f"{path}.{key}")
                for key, item in value.items()}
    raise JevError("invalid-input", f"{path} is not JSON data")


def _strict_keys(value: Mapping[str, Any], allowed: set[str], path: str) -> None:
    extra = set(value) - allowed
    if extra:
        raise JevError("invalid-input", f"{path} has unknown fields: {', '.join(sorted(extra))}")


@dataclass(frozen=True)
class Candidate:
    id: str
    description: str
    evidence_ids: tuple[str, ...] = ()

    @classmethod
    def parse(cls, raw: Any, index: int) -> "Candidate":
        path = f"request.candidates[{index}]"
        if not isinstance(raw, Mapping):
            raise JevError("invalid-input", f"{path} must be an object")
        _strict_keys(raw, {"id", "description", "evidence_ids"}, path)
        candidate_id = raw.get("id")
        description = raw.get("description")
        evidence = raw.get("evidence_ids", [])
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id == NO_MATCH:
            raise JevError("invalid-input", f"{path}.id must be nonempty and not {NO_MATCH!r}")
        if not isinstance(description, str) or not description:
            raise JevError("invalid-input", f"{path}.description must be a nonempty string")
        if (not isinstance(evidence, list)
                or any(not isinstance(item, str) or not item for item in evidence)):
            raise JevError("invalid-input", f"{path}.evidence_ids must be nonempty strings")
        if len(evidence) != len(set(evidence)):
            raise JevError("invalid-input", f"{path}.evidence_ids contains duplicates")
        return cls(candidate_id, description, tuple(sorted(evidence)))

    def as_state(self) -> dict[str, Any]:
        return {"id": self.id, "description": self.description,
                "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class AssessmentRequest:
    subject_id: str
    subject: Any
    candidates: tuple[Candidate, ...]
    instructions: str
    true_criteria: str
    false_criteria: str
    model: str = DEFAULT_MODEL

    @classmethod
    def parse(cls, raw: Any) -> "AssessmentRequest":
        if not isinstance(raw, Mapping):
            raise JevError("invalid-input", "request must be an object")
        _strict_keys(raw, {
            "schema_version", "subject_id", "subject", "candidates", "instructions",
            "presence_criteria", "model",
        }, "request")
        if raw.get("schema_version") != SCHEMA_VERSION or type(raw.get("schema_version")) is not int:
            raise JevError("invalid-input", "request.schema_version must be integer 1")
        subject_id = raw.get("subject_id")
        if not isinstance(subject_id, str) or not subject_id:
            raise JevError("invalid-input", "request.subject_id must be a nonempty string")
        subject = _plain_json(raw.get("subject"), "request.subject")
        candidate_raw = raw.get("candidates")
        if not isinstance(candidate_raw, list) or not candidate_raw:
            raise JevError("invalid-input", "request.candidates must be a nonempty array")
        if len(candidate_raw) > MAX_CANDIDATES:
            raise JevError("invalid-input", f"request.candidates exceeds {MAX_CANDIDATES}")
        candidates = tuple(Candidate.parse(item, index)
                           for index, item in enumerate(candidate_raw))
        ids = [candidate.id for candidate in candidates]
        if len(ids) != len(set(ids)):
            raise JevError("invalid-input", "request.candidates contains duplicate ids")
        instructions = raw.get("instructions")
        if not isinstance(instructions, str) or not instructions:
            raise JevError("invalid-input", "request.instructions must be a nonempty string")
        presence = raw.get("presence_criteria")
        if not isinstance(presence, Mapping):
            raise JevError("invalid-input", "request.presence_criteria must be an object")
        _strict_keys(presence, {"true", "false"}, "request.presence_criteria")
        true_criteria, false_criteria = presence.get("true"), presence.get("false")
        if not isinstance(true_criteria, str) or not true_criteria:
            raise JevError("invalid-input", "request.presence_criteria.true must be nonempty")
        if not isinstance(false_criteria, str) or not false_criteria:
            raise JevError("invalid-input", "request.presence_criteria.false must be nonempty")
        model = raw.get("model", DEFAULT_MODEL)
        if not isinstance(model, str) or not model:
            raise JevError("invalid-input", "request.model must be a nonempty string")
        return cls(subject_id, subject, candidates, instructions,
                   true_criteria, false_criteria, model)

    def payload(self) -> dict[str, Any]:
        criteria = {candidate.id: candidate.description for candidate in self.candidates}
        criteria[NO_MATCH] = "None of the supplied candidates directly matches the subject."
        return {
            "state": {
                "subject_id": self.subject_id,
                "subject": self.subject,
                "candidates": [candidate.as_state() for candidate in self.candidates],
            },
            "model": self.model,
            "questions": {
                SELECTION_QUESTION: {
                    "type": "choice",
                    "instructions": self.instructions,
                    "criteria": criteria,
                },
                PRESENCE_QUESTION: {
                    "type": "noul",
                    "instructions": (
                        "Does at least one candidate directly match the subject under the "
                        "stated semantic goal?"
                    ),
                    "criteria": {"true": self.true_criteria, "false": self.false_criteria},
                },
            },
        }


def _probability(value: Any, path: str) -> float:
    if type(value) not in (int, float) or isinstance(value, bool):
        raise JevError("invalid-response", f"{path} must be a number")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= 1:
        raise JevError("invalid-response", f"{path} must be between 0 and 1")
    return result


def build_artifact(request: AssessmentRequest, response: Any) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise JevError("invalid-response", "TypeSafe response must be an object")
    answers = response.get("answers")
    if not isinstance(answers, Mapping):
        raise JevError("invalid-response", "TypeSafe response.answers must be an object")
    selection, presence = answers.get(SELECTION_QUESTION), answers.get(PRESENCE_QUESTION)
    if not isinstance(selection, Mapping) or selection.get("type") != "choice":
        raise JevError("invalid-response", f"answers.{SELECTION_QUESTION} must be a Choice")
    if not isinstance(presence, Mapping) or presence.get("type") != "noul":
        raise JevError("invalid-response", f"answers.{PRESENCE_QUESTION} must be a Noul")
    candidate_ids = {candidate.id for candidate in request.candidates} | {NO_MATCH}
    choice = selection.get("choice")
    if choice not in candidate_ids:
        raise JevError("invalid-response", "Choice answer is outside the candidate set")
    probabilities = selection.get("probabilities")
    if not isinstance(probabilities, Mapping) or set(probabilities) != candidate_ids:
        raise JevError("invalid-response", "Choice probabilities must cover exactly the candidate set")
    parsed_probabilities = {key: _probability(value, f"probabilities.{key}")
                            for key, value in probabilities.items()}
    if abs(sum(parsed_probabilities.values()) - 1.0) > 0.02:
        raise JevError("invalid-response", "Choice probabilities do not sum to 1")
    confidence = _probability(selection.get("confidence"), "choice.confidence")
    noul = _probability(presence.get("noul"), "presence.noul")
    # ``jev-latest`` is an alias: the service records the resolved concrete
    # model (for example ``jev-1.13.0``) in the response. Preserve both rather
    # than pretending the alias itself performed the evaluation.
    response_model = response.get("model")
    if not isinstance(response_model, str) or not response_model:
        raise JevError("invalid-response", "response.model must be nonempty")
    usage = response.get("usage", {})
    if not isinstance(usage, Mapping):
        raise JevError("invalid-response", "response.usage must be an object")
    parsed_usage: dict[str, int] = {}
    for key in ("input_tokens", "output_tokens"):
        value = usage.get(key, 0)
        if type(value) is not int or value < 0:
            raise JevError("invalid-response", f"response.usage.{key} must be nonnegative")
        parsed_usage[key] = value

    payload = request.payload()
    candidate_document = [candidate.as_state() for candidate in request.candidates]
    core = {
        "schema_version": SCHEMA_VERSION,
        "kind": ARTIFACT_KIND,
        "producer": {"class": "jev", "source": f"jev {response_model} typesafe-systemone-v1"},
        "subject_id": request.subject_id,
        "model": response_model,
        "requested_model": request.model,
        "state_sha256": _digest(payload["state"]),
        "request_sha256": _digest(payload),
        "candidate_set_sha256": _digest(candidate_document),
        "candidates": candidate_document,
        "judgments": {
            SELECTION_QUESTION: {
                "type": "choice", "choice": choice,
                "probabilities": dict(sorted(parsed_probabilities.items())),
                "confidence": confidence,
            },
            PRESENCE_QUESTION: {"type": "noul", "noul": noul},
        },
        "usage": parsed_usage,
        "evidence_semantics": {
            "kind": "assumption",
            "may_rank_or_request_probe": True,
            "may_establish_fact": False,
            "may_establish_compatibility": False,
            "may_establish_completeness": False,
            "may_qualify_claim": False,
        },
    }
    core["assessment_id"] = f"jev:{_digest(core)}"
    return core


Transport = Callable[[str, bytes, Mapping[str, str], float], bytes]


def _transport(endpoint: str, body: bytes, headers: Mapping[str, str], timeout: float) -> bytes:
    try:
        with urlopen(Request(endpoint, data=body, headers=dict(headers), method="POST"),
                     timeout=timeout) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", "replace")
        raise JevError("api-error", f"TypeSafe returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise JevError("transport-error", f"TypeSafe request failed: {exc}") from exc
    if len(data) > MAX_RESPONSE_BYTES:
        raise JevError("invalid-response", "TypeSafe response exceeds the size bound")
    return data


def assess(request: AssessmentRequest, *, api_key: str | None = None,
           endpoint: str | None = None, timeout: float = 30.0,
           transport: Transport = _transport) -> dict[str, Any]:
    key = api_key or os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise JevError("missing-credential", "set JEV_API_KEY or TYPESAFE_API_KEY")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise JevError("invalid-input", "timeout must be positive")
    payload = request.payload()
    body = transport(endpoint or os.environ.get("TYPESAFE_ENDPOINT") or DEFAULT_ENDPOINT,
                     _canonical(payload), {
                         "Authorization": f"Bearer {key}",
                         "Content-Type": "application/json",
                         "Accept": "application/json",
                     }, float(timeout))
    try:
        response = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise JevError("invalid-response", "TypeSafe response is not JSON") from exc
    return build_artifact(request, response)
