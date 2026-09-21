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


def _require_content_address(
    artifact: Mapping[str, Any], *, prefix: str, path: str = "artifact"
) -> None:
    """Reject a stored advisory whose body no longer matches its identity."""
    assessment_id = artifact.get("assessment_id")
    if not isinstance(assessment_id, str):
        raise JevError("invalid-input", f"{path}.assessment_id must be a string")
    core = dict(artifact)
    core.pop("assessment_id", None)
    try:
        expected = f"{prefix}{_digest(_plain_json(core, path))}"
    except (TypeError, ValueError) as exc:
        raise JevError("invalid-input", f"{path} is not canonical JSON") from exc
    if assessment_id != expected:
        raise JevError("invalid-input", f"{path}.assessment_id does not match its content")


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


def _exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    _strict_keys(value, expected, path)
    missing = expected - set(value)
    if missing:
        raise JevError("invalid-input", f"{path} is missing fields: {', '.join(sorted(missing))}")


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


def build_artifact(request: AssessmentRequest, response: Any, *,
                   raw_response: bytes | None = None,
                   response_mode: str = "in-memory-unattested") -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise JevError("invalid-response", "TypeSafe response must be an object")
    _exact_keys(response, {"model", "answers", "usage"}, "response")
    answers = response.get("answers")
    if not isinstance(answers, Mapping):
        raise JevError("invalid-response", "TypeSafe response.answers must be an object")
    _exact_keys(answers, {SELECTION_QUESTION, PRESENCE_QUESTION}, "response.answers")
    selection, presence = answers.get(SELECTION_QUESTION), answers.get(PRESENCE_QUESTION)
    if not isinstance(selection, Mapping) or selection.get("type") != "choice":
        raise JevError("invalid-response", f"answers.{SELECTION_QUESTION} must be a Choice")
    if not isinstance(presence, Mapping) or presence.get("type") != "noul":
        raise JevError("invalid-response", f"answers.{PRESENCE_QUESTION} must be a Noul")
    _exact_keys(selection, {"type", "choice", "probabilities", "confidence"},
                 f"response.answers.{SELECTION_QUESTION}")
    _exact_keys(presence, {"type", "noul"}, f"response.answers.{PRESENCE_QUESTION}")
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
    _exact_keys(usage, {"input_tokens", "output_tokens"}, "response.usage")
    parsed_usage: dict[str, int] = {}
    for key in ("input_tokens", "output_tokens"):
        value = usage.get(key, 0)
        if type(value) is not int or value < 0:
            raise JevError("invalid-response", f"response.usage.{key} must be nonnegative")
        parsed_usage[key] = value

    payload = request.payload()
    candidate_document = [candidate.as_state() for candidate in request.candidates]
    raw_text = None
    raw_digest = None
    if raw_response is not None:
        try:
            raw_text = raw_response.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise JevError("invalid-response", "raw response is not UTF-8 JSON") from exc
        raw_digest = hashlib.sha256(raw_response).hexdigest()
    response_document = _plain_json(response, "response")
    core = {
        "schema_version": SCHEMA_VERSION,
        "kind": ARTIFACT_KIND,
        "producer": {"class": "jev", "source": f"jev {response_model} typesafe-systemone-v1"},
        "subject_id": request.subject_id,
        "model": response_model,
        "requested_model": request.model,
        "request": payload,
        "state_sha256": _digest(payload["state"]),
        "request_sha256": _digest(payload),
        "candidate_set_sha256": _digest(candidate_document),
        "response_provenance": {
            "mode": response_mode,
            "raw_sha256": raw_digest,
            "canonical_sha256": _digest(response_document),
            "service_attested": False,
        },
        "response": response_document,
        "raw_response_utf8": raw_text,
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


def claims_bundle(artifact: Mapping[str, Any]):
    """Translate a validated advisory artifact into Datalog input assumptions.

    The relations intentionally have no completeness or compatibility modality,
    and contain no claim relation.  Combining this fragment with a rule pack can
    therefore prioritize work, but cannot close an evidence domain by itself.
    """
    from .ir import (
        Atom, BindingTime, Bundle, Column, Constant, Evidence, Modality,
        RelationDecl, TypeName,
    )
    from .validation import ValidationError, validate_bundle

    if not isinstance(artifact, Mapping) or artifact.get("kind") != ARTIFACT_KIND:
        raise JevError("invalid-input", f"artifact.kind must be {ARTIFACT_KIND!r}")
    expected_artifact_keys = {
        "schema_version", "kind", "producer", "subject_id", "model", "requested_model",
        "request", "state_sha256", "request_sha256", "candidate_set_sha256",
        "response_provenance", "response", "raw_response_utf8",
        "candidates", "judgments", "usage",
        "evidence_semantics", "assessment_id",
    }
    if set(artifact) != expected_artifact_keys:
        raise JevError("invalid-input", "artifact fields are not the exact advisory schema")
    _require_content_address(artifact, prefix="jev:")
    assessment_id = artifact.get("assessment_id")
    subject_id = artifact.get("subject_id")
    producer = artifact.get("producer")
    judgments = artifact.get("judgments")
    semantics = artifact.get("evidence_semantics")
    request = artifact.get("request")
    response = artifact.get("response")
    raw_response = artifact.get("raw_response_utf8")
    provenance = artifact.get("response_provenance")
    candidates = artifact.get("candidates")
    usage = artifact.get("usage")
    if (not isinstance(assessment_id, str) or not assessment_id
            or not isinstance(subject_id, str) or not subject_id
            or not isinstance(producer, Mapping) or set(producer) != {"class", "source"}
            or producer.get("class") != "jev"
            or not isinstance(producer.get("source"), str)
            or not producer["source"].startswith("jev ")
            or not isinstance(judgments, Mapping)
            or set(judgments) != {SELECTION_QUESTION, PRESENCE_QUESTION}
            or not isinstance(semantics, Mapping)
            or set(semantics) != {"kind", "may_rank_or_request_probe", "may_establish_fact",
                                  "may_establish_compatibility", "may_establish_completeness",
                                  "may_qualify_claim"}
            or semantics.get("kind") != "assumption"
            or any(semantics.get(name) is not False for name in (
                "may_establish_fact", "may_establish_compatibility",
                "may_establish_completeness", "may_qualify_claim",
            ))):
        raise JevError("invalid-input", "artifact does not satisfy the Jev advisory contract")
    if (not isinstance(request, Mapping)
            or set(request) != {"state", "model", "questions"}
            or artifact.get("request_sha256") != _digest(request)
            or artifact.get("state_sha256") != _digest(request.get("state"))
            or not isinstance(candidates, list)
            or artifact.get("candidate_set_sha256") != _digest(candidates)):
        raise JevError("invalid-input", "artifact request or state digests do not match their content")
    state = request.get("state")
    questions = request.get("questions")
    if (not isinstance(state, Mapping)
            or set(state) != {"subject_id", "subject", "candidates"}
            or state.get("candidates") != candidates
            or not isinstance(questions, Mapping)
            or set(questions) != {SELECTION_QUESTION, PRESENCE_QUESTION}):
        raise JevError("invalid-input", "artifact candidates differ from the bound request")
    selection_question = questions.get(SELECTION_QUESTION)
    presence_question = questions.get(PRESENCE_QUESTION)
    if (not isinstance(selection_question, Mapping)
            or set(selection_question) != {"type", "instructions", "criteria"}
            or not isinstance(presence_question, Mapping)
            or set(presence_question) != {"type", "instructions", "criteria"}):
        raise JevError("invalid-input", "artifact request question schemas are malformed")
    if (not isinstance(provenance, Mapping)
            or set(provenance) != {"mode", "raw_sha256", "canonical_sha256", "service_attested"}
            or provenance.get("mode") not in {"in-memory-unattested", "offline-file-unattested",
                                               "https-unattested"}
            or provenance.get("service_attested") is not False
            or not isinstance(provenance.get("canonical_sha256"), str)
            or (provenance.get("raw_sha256") is not None
                and not isinstance(provenance.get("raw_sha256"), str))):
        raise JevError("invalid-input", "artifact response provenance is malformed")
    if not isinstance(response, Mapping) or provenance["canonical_sha256"] != _digest(response):
        raise JevError("invalid-input", "artifact canonical response digest does not match")
    if set(response) != {"model", "answers", "usage"}:
        raise JevError("invalid-input", "artifact response fields are not exact")
    response_answers = response.get("answers")
    response_usage = response.get("usage")
    if (not isinstance(response.get("model"), str) or not response["model"]
            or not isinstance(response_answers, Mapping)
            or set(response_answers) != {SELECTION_QUESTION, PRESENCE_QUESTION}
            or not isinstance(response_usage, Mapping)
            or set(response_usage) != {"input_tokens", "output_tokens"}):
        raise JevError("invalid-input", "artifact response schema is malformed")
    response_selection = response_answers.get(SELECTION_QUESTION)
    response_presence = response_answers.get(PRESENCE_QUESTION)
    if (not isinstance(response_selection, Mapping)
            or set(response_selection) != {"type", "choice", "probabilities", "confidence"}
            or not isinstance(response_presence, Mapping)
            or set(response_presence) != {"type", "noul"}):
        raise JevError("invalid-input", "artifact response answers are malformed")
    candidate_ids = {
        candidate.get("id") for candidate in candidates if isinstance(candidate, Mapping)
    } | {NO_MATCH}
    response_probabilities = response_selection.get("probabilities")
    if (response_selection.get("type") != "choice"
            or response_selection.get("choice") not in candidate_ids
            or not isinstance(response_probabilities, Mapping)
            or set(response_probabilities) != candidate_ids
            or response_presence.get("type") != "noul"):
        raise JevError("invalid-input", "artifact response answer values are malformed")
    try:
        normalized_probabilities = {
            key: _probability(value, f"response.probabilities.{key}")
            for key, value in response_probabilities.items()
        }
        normalized_confidence = _probability(
            response_selection.get("confidence"), "response.choice.confidence")
        normalized_noul = _probability(
            response_presence.get("noul"), "response.presence.noul")
    except JevError as exc:
        raise JevError("invalid-input", "artifact response probabilities are malformed") from exc
    if abs(sum(normalized_probabilities.values()) - 1.0) > 0.02:
        raise JevError("invalid-input", "artifact response probabilities do not sum to 1")
    if any(type(response_usage[name]) is not int or response_usage[name] < 0
           for name in response_usage):
        raise JevError("invalid-input", "artifact response usage is malformed")
    if (artifact.get("model") != response.get("model")
            or judgments.get(SELECTION_QUESTION) != {
                "type": "choice",
                "choice": response_selection.get("choice"),
                "probabilities": dict(sorted(normalized_probabilities.items())),
                "confidence": normalized_confidence,
            }
            or judgments.get(PRESENCE_QUESTION) != {
                "type": "noul", "noul": normalized_noul,
            }
            or usage != response_usage):
        raise JevError("invalid-input", "artifact response disagrees with derived advisory fields")
    if raw_response is None:
        if provenance["raw_sha256"] is not None:
            raise JevError("invalid-input", "artifact raw response digest has no retained response")
    elif (not isinstance(raw_response, str)
          or provenance["raw_sha256"] != hashlib.sha256(raw_response.encode("utf-8")).hexdigest()):
        raise JevError("invalid-input", "artifact raw response digest does not match")
    try:
        if raw_response is not None and json.loads(raw_response) != response:
            raise JevError("invalid-input", "artifact raw and parsed responses differ")
    except json.JSONDecodeError as exc:
        raise JevError("invalid-input", "artifact raw response is not JSON") from exc
    if (not isinstance(usage, Mapping) or set(usage) != {"input_tokens", "output_tokens"}
            or any(type(usage[name]) is not int or usage[name] < 0 for name in usage)):
        raise JevError("invalid-input", "artifact usage is malformed")
    selection = judgments.get(SELECTION_QUESTION)
    presence = judgments.get(PRESENCE_QUESTION)
    if (not isinstance(selection, Mapping) or set(selection) != {"type", "choice", "probabilities", "confidence"}
            or not isinstance(presence, Mapping) or set(presence) != {"type", "noul"}
            or selection.get("type") != "choice" or presence.get("type") != "noul"):
        raise JevError("invalid-input", "artifact judgments are malformed")
    probabilities = selection.get("probabilities")
    if not isinstance(probabilities, Mapping):
        raise JevError("invalid-input", "artifact probabilities are malformed")
    for index, candidate in enumerate(candidates):
        if (not isinstance(candidate, Mapping)
                or set(candidate) != {"id", "description", "evidence_ids"}
                or not isinstance(candidate.get("id"), str) or not candidate["id"]
                or not isinstance(candidate.get("description"), str) or not candidate["description"]
                or not isinstance(candidate.get("evidence_ids"), list)
                or any(not isinstance(item, str) or not item for item in candidate["evidence_ids"])):
            raise JevError("invalid-input", f"artifact candidates[{index}] is malformed")

    probability_relation = RelationDecl(
        "jev_candidate_probability",
        (Column("assessment", TypeName.SYMBOL), Column("subject", TypeName.SYMBOL),
         Column("candidate", TypeName.SYMBOL), Column("probability_ppm", TypeName.UNSIGNED)),
        modality=Modality.ASSUMPTION, binding=BindingTime.RUNTIME,
        producer_classes=("jev",),
    )
    selection_relation = RelationDecl(
        "jev_selected_candidate",
        (Column("assessment", TypeName.SYMBOL), Column("subject", TypeName.SYMBOL),
         Column("candidate", TypeName.SYMBOL), Column("confidence_ppm", TypeName.UNSIGNED),
         Column("direct_match_ppm", TypeName.UNSIGNED)),
        modality=Modality.ASSUMPTION, binding=BindingTime.RUNTIME,
        producer_classes=("jev",),
    )
    facts = []
    evidence = []
    for candidate, value in sorted(probabilities.items()):
        probability = _probability(value, f"artifact.probabilities.{candidate}")
        if not isinstance(candidate, str) or not candidate:
            raise JevError("invalid-input", "artifact candidate ids must be nonempty")
        atom = Atom("jev_candidate_probability", (
            Constant(assessment_id), Constant(subject_id), Constant(candidate),
            Constant(round(probability * 1_000_000)),
        ))
        facts.append(atom)
        evidence.append(Evidence(
            f"{assessment_id}:probability:{_digest([candidate, probability])[:16]}",
            atom, source=producer["source"], kind="assumption"))
    choice = selection.get("choice")
    if choice not in probabilities:
        raise JevError("invalid-input", "artifact selection is outside its distribution")
    selected = Atom("jev_selected_candidate", (
        Constant(assessment_id), Constant(subject_id), Constant(choice),
        Constant(round(_probability(selection.get("confidence"),
                                    "artifact.confidence") * 1_000_000)),
        Constant(round(_probability(presence.get("noul"),
                                    "artifact.direct_match") * 1_000_000)),
    ))
    facts.append(selected)
    evidence.append(Evidence(
        f"{assessment_id}:selection", selected,
        source=producer["source"], kind="assumption"))
    bundle = Bundle(
        (probability_relation, selection_relation), facts=tuple(facts),
        evidence=tuple(evidence), metadata=tuple(sorted({
            "artifact_kind": ARTIFACT_KIND,
            "assessment_id": assessment_id,
            "candidate_set_sha256": artifact.get("candidate_set_sha256"),
            "model": artifact.get("model"),
            "request_sha256": artifact.get("request_sha256"),
            "state_sha256": artifact.get("state_sha256"),
        }.items())),
    )
    issues = validate_bundle(bundle)
    if issues:
        raise ValidationError(issues)
    return bundle


Transport = Callable[[str, bytes, Mapping[str, str], float], bytes]


def _transport(endpoint: str, body: bytes, headers: Mapping[str, str], timeout: float) -> bytes:
    try:
        with urlopen(Request(endpoint, data=body, headers=dict(headers), method="POST"),
                     timeout=timeout) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        # An error page is controlled by the endpoint and may echo request or
        # credential material.  Keep operational output bounded and secret-free.
        raise JevError("api-error", f"TypeSafe returned HTTP {exc.code}") from exc
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
    return build_artifact(
        request, response,
        raw_response=body,
        response_mode="https-unattested")
