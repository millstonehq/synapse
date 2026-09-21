"""Framing-resistant Jev pattern triage over neutral, mechanically sourced facts."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import json
import os
from typing import Any

from . import jev


ARTIFACT_KIND = "capcov-jev-pattern-sensitivity-v1"
VARIANTS = ("baseline", "reversed_evidence", "opaque_ids", "neutral_paraphrase")
QUESTIONS = ("pattern_match", "evidence_sufficient", "exclusion_applies")


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    kind: str
    fact: Any

    @classmethod
    def parse(cls, raw: Any, index: int) -> "EvidenceItem":
        path = f"request.evidence[{index}]"
        if not isinstance(raw, Mapping):
            raise jev.JevError("invalid-input", f"{path} must be an object")
        jev._strict_keys(raw, {"id", "kind", "fact"}, path)
        item_id, kind = raw.get("id"), raw.get("kind")
        if not isinstance(item_id, str) or not item_id:
            raise jev.JevError("invalid-input", f"{path}.id must be nonempty")
        if kind not in {"patch", "static", "runtime", "oracle"}:
            raise jev.JevError("invalid-input", f"{path}.kind is not an evidence class")
        return cls(item_id, kind, jev._plain_json(raw.get("fact"), f"{path}.fact"))

    def state(self, item_id: str | None = None) -> dict[str, Any]:
        return {"id": item_id or self.id, "kind": self.kind, "fact": self.fact}


@dataclass(frozen=True)
class PatternRequest:
    subject_id: str
    pattern_id: str
    definition: str
    positive_signatures: tuple[str, ...]
    required_evidence: tuple[str, ...]
    exclusions: tuple[str, ...]
    evidence: tuple[EvidenceItem, ...]
    missing_evidence: tuple[str, ...]
    model: str = jev.DEFAULT_MODEL

    @classmethod
    def parse(cls, raw: Any) -> "PatternRequest":
        if not isinstance(raw, Mapping):
            raise jev.JevError("invalid-input", "request must be an object")
        jev._strict_keys(raw, {"schema_version", "subject_id", "pattern", "evidence",
                               "missing_evidence", "model"}, "request")
        if raw.get("schema_version") != 1 or type(raw.get("schema_version")) is not int:
            raise jev.JevError("invalid-input", "request.schema_version must be integer 1")
        subject_id = raw.get("subject_id")
        if not isinstance(subject_id, str) or not subject_id:
            raise jev.JevError("invalid-input", "request.subject_id must be nonempty")
        pattern = raw.get("pattern")
        if not isinstance(pattern, Mapping):
            raise jev.JevError("invalid-input", "request.pattern must be an object")
        jev._strict_keys(pattern, {"id", "definition", "positive_signatures",
                                   "required_evidence", "exclusions"}, "request.pattern")
        pattern_id, definition = pattern.get("id"), pattern.get("definition")
        if not isinstance(pattern_id, str) or not pattern_id:
            raise jev.JevError("invalid-input", "request.pattern.id must be nonempty")
        if not isinstance(definition, str) or not definition:
            raise jev.JevError("invalid-input", "request.pattern.definition must be nonempty")

        def strings(name: str) -> tuple[str, ...]:
            value = pattern.get(name, [])
            if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
                raise jev.JevError("invalid-input", f"request.pattern.{name} must be strings")
            return tuple(value)

        raw_evidence = raw.get("evidence")
        if not isinstance(raw_evidence, list) or not raw_evidence or len(raw_evidence) > 256:
            raise jev.JevError("invalid-input", "request.evidence must contain 1..256 items")
        evidence = tuple(EvidenceItem.parse(item, i) for i, item in enumerate(raw_evidence))
        if len({item.id for item in evidence}) != len(evidence):
            raise jev.JevError("invalid-input", "request.evidence contains duplicate ids")
        missing = raw.get("missing_evidence", [])
        if not isinstance(missing, list) or any(not isinstance(x, str) or not x for x in missing):
            raise jev.JevError("invalid-input", "request.missing_evidence must be strings")
        model = raw.get("model", jev.DEFAULT_MODEL)
        if not isinstance(model, str) or not model:
            raise jev.JevError("invalid-input", "request.model must be nonempty")
        return cls(subject_id, pattern_id, definition, strings("positive_signatures"),
                   strings("required_evidence"), strings("exclusions"), evidence,
                   tuple(missing), model)

    def payload(self, variant: str = "baseline") -> dict[str, Any]:
        if variant not in VARIANTS:
            raise jev.JevError("invalid-input", f"unknown sensitivity variant {variant!r}")
        evidence = list(self.evidence)
        if variant == "reversed_evidence":
            evidence.reverse()
        opaque = variant == "opaque_ids"
        items = [item.state(f"e{i + 1}" if opaque else None) for i, item in enumerate(evidence)]
        state = {
            "subject_id": "subject" if opaque else self.subject_id,
            "pattern": {
                "id": "pattern" if opaque else self.pattern_id,
                "definition": self.definition,
                "positive_signatures": list(self.positive_signatures),
                "required_evidence": list(self.required_evidence),
                "exclusions": list(self.exclusions),
            },
            "evidence": items,
            "missing_evidence": list(self.missing_evidence),
        }
        normal = {
            "pattern_match": "Do the supplied facts exhibit the defined pattern? Treat missing evidence as unknown, not false.",
            "evidence_sufficient": "Are the supplied facts sufficient to assess this pattern without additional runtime or oracle evidence?",
            "exclusion_applies": "Do the supplied facts establish any listed exclusion for this pattern?",
        }
        paraphrase = {
            "pattern_match": "Considering only these facts, is the pattern definition satisfied? Absence of evidence is not contrary evidence.",
            "evidence_sufficient": "Can this pattern be assessed from this evidence alone, with no missing runtime or oracle fact needed?",
            "exclusion_applies": "Does this evidence satisfy one or more of the pattern's explicit exclusions?",
        }
        wording = paraphrase if variant == "neutral_paraphrase" else normal
        criteria = {
            "pattern_match": {"true": "The facts satisfy a positive signature and the definition.",
                              "false": "They do not; uncertainty or missing evidence favors false."},
            "evidence_sufficient": {"true": "Required evidence is present for this assessment.",
                                    "false": "A listed missing fact or required runtime/oracle fact could change it."},
            "exclusion_applies": {"true": "A listed exclusion is established by a supplied fact.",
                                  "false": "No listed exclusion is established."},
        }
        return {"state": state, "model": self.model,
                "questions": {name: {"type": "noul", "instructions": wording[name],
                                     "criteria": criteria[name]} for name in QUESTIONS}}


def _parse_response(request: PatternRequest, variant: str, response: Any) -> dict[str, Any]:
    if not isinstance(response, Mapping) or not isinstance(response.get("answers"), Mapping):
        raise jev.JevError("invalid-response", f"{variant} response has no answers")
    values = {}
    for name in QUESTIONS:
        answer = response["answers"].get(name)
        if not isinstance(answer, Mapping) or answer.get("type") != "noul":
            raise jev.JevError("invalid-response", f"{variant}.{name} must be a Noul")
        values[name] = jev._probability(answer.get("noul"), f"{variant}.{name}.noul")
    model = response.get("model")
    if not isinstance(model, str) or not model:
        raise jev.JevError("invalid-response", f"{variant}.model must be nonempty")
    usage = response.get("usage", {})
    if not isinstance(usage, Mapping):
        raise jev.JevError("invalid-response", f"{variant}.usage must be an object")
    return {"variant": variant, "model": model, "request_sha256": jev._digest(request.payload(variant)),
            "judgments": values, "usage": {k: v for k, v in usage.items()
                                               if k in {"input_tokens", "output_tokens"}
                                               and type(v) is int and v >= 0}}


def build_artifact(request: PatternRequest, responses: Mapping[str, Any], *, max_spread: float) -> dict[str, Any]:
    threshold = jev._probability(max_spread, "max_spread")
    if set(responses) != set(VARIANTS):
        raise jev.JevError("invalid-response", "responses must cover exactly the sensitivity variants")
    runs = [_parse_response(request, variant, responses[variant]) for variant in VARIANTS]
    spreads = {name: max(run["judgments"][name] for run in runs) -
                     min(run["judgments"][name] for run in runs) for name in QUESTIONS}
    core = {
        "schema_version": 1, "kind": ARTIFACT_KIND,
        "producer": {"class": "jev", "source": "jev pattern-sensitivity typesafe-systemone-v1"},
        "subject_id": request.subject_id, "pattern_id": request.pattern_id,
        "state_sha256": jev._digest(request.payload()["state"]), "runs": runs,
        "sensitivity": {"max_allowed_spread": threshold, "spreads": spreads,
                        "stable": all(value <= threshold for value in spreads.values())},
        "evidence_semantics": {"kind": "assumption", "may_rank_or_request_probe": True,
                               "may_establish_fact": False, "may_establish_compatibility": False,
                               "may_establish_completeness": False, "may_qualify_claim": False},
    }
    core["assessment_id"] = f"jev-pattern:{jev._digest(core)}"
    return core


def claims_bundle(artifact: Mapping[str, Any]):
    """Expose baseline judgments and sensitivity as assumption-only Datalog facts."""
    from .ir import (Atom, BindingTime, Bundle, Column, Constant, Evidence,
                     Modality, RelationDecl, TypeName)
    from .validation import ValidationError, validate_bundle

    if not isinstance(artifact, Mapping) or artifact.get("kind") != ARTIFACT_KIND:
        raise jev.JevError("invalid-input", f"artifact.kind must be {ARTIFACT_KIND!r}")
    jev._require_content_address(artifact, prefix="jev-pattern:")
    runs = artifact.get("runs")
    sensitivity = artifact.get("sensitivity")
    semantics = artifact.get("evidence_semantics")
    if (not isinstance(runs, list) or len(runs) != len(VARIANTS)
            or not isinstance(sensitivity, Mapping) or not isinstance(semantics, Mapping)
            or semantics.get("kind") != "assumption"
            or any(semantics.get(name) is not False for name in (
                "may_establish_fact", "may_establish_compatibility",
                "may_establish_completeness", "may_qualify_claim"))):
        raise jev.JevError("invalid-input", "artifact violates the pattern advisory contract")
    baseline = next((run for run in runs if run.get("variant") == "baseline"), None)
    if not isinstance(baseline, Mapping) or not isinstance(baseline.get("judgments"), Mapping):
        raise jev.JevError("invalid-input", "artifact has no baseline judgments")
    identity = [artifact.get(name) for name in ("assessment_id", "subject_id", "pattern_id")]
    if any(not isinstance(value, str) or not value for value in identity):
        raise jev.JevError("invalid-input", "artifact identity is malformed")
    assessment_id, subject_id, pattern_id = identity
    producer = artifact.get("producer")
    if (not isinstance(producer, Mapping) or producer.get("class") != "jev"
            or producer.get("source") != "jev pattern-sensitivity typesafe-systemone-v1"):
        raise jev.JevError("invalid-input", "artifact producer is malformed")
    result_relation = RelationDecl(
        "jev_pattern_assumption",
        (Column("assessment", TypeName.SYMBOL), Column("subject", TypeName.SYMBOL),
         Column("pattern", TypeName.SYMBOL), Column("match_ppm", TypeName.UNSIGNED),
         Column("sufficient_ppm", TypeName.UNSIGNED), Column("exclusion_ppm", TypeName.UNSIGNED)),
        modality=Modality.ASSUMPTION, binding=BindingTime.RUNTIME, producer_classes=("jev",))
    sensitivity_relation = RelationDecl(
        "jev_pattern_sensitivity",
        (Column("assessment", TypeName.SYMBOL), Column("pattern", TypeName.SYMBOL),
         Column("max_spread_ppm", TypeName.UNSIGNED), Column("stable", TypeName.BOOLEAN)),
        modality=Modality.ASSUMPTION, binding=BindingTime.RUNTIME, producer_classes=("jev",))
    judgments = baseline["judgments"]
    values = [jev._probability(judgments.get(name), f"baseline.{name}") for name in QUESTIONS]
    spreads = sensitivity.get("spreads")
    if not isinstance(spreads, Mapping) or type(sensitivity.get("stable")) is not bool:
        raise jev.JevError("invalid-input", "artifact sensitivity is malformed")
    max_spread = max(jev._probability(spreads.get(name), f"spread.{name}") for name in QUESTIONS)
    result = Atom("jev_pattern_assumption", tuple(Constant(value) for value in (
        assessment_id, subject_id, pattern_id, *(round(value * 1_000_000) for value in values))))
    stability = Atom("jev_pattern_sensitivity", (
        Constant(assessment_id), Constant(pattern_id), Constant(round(max_spread * 1_000_000)),
        Constant(sensitivity["stable"])))
    evidence = tuple(Evidence(f"{assessment_id}:{i}", atom, source=producer["source"],
                              kind="assumption") for i, atom in enumerate((result, stability)))
    bundle = Bundle((result_relation, sensitivity_relation), facts=(result, stability),
                    evidence=evidence, metadata=(("artifact_kind", ARTIFACT_KIND),
                                                 ("assessment_id", assessment_id)))
    issues = validate_bundle(bundle)
    if issues:
        raise ValidationError(issues)
    return bundle


Transport = Callable[[str, bytes, Mapping[str, str], float], bytes]


def assess(request: PatternRequest, *, max_spread: float, api_key: str | None = None,
           endpoint: str | None = None, timeout: float = 30.0,
           transport: Transport = jev._transport) -> dict[str, Any]:
    key = api_key or os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise jev.JevError("missing-credential", "set JEV_API_KEY or TYPESAFE_API_KEY")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise jev.JevError("invalid-input", "timeout must be positive")
    target = endpoint or os.environ.get("TYPESAFE_ENDPOINT") or jev.DEFAULT_ENDPOINT
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "Accept": "application/json"}

    def run(variant: str) -> tuple[str, Any]:
        body = transport(target, jev._canonical(request.payload(variant)), headers, float(timeout))
        try:
            return variant, json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise jev.JevError("invalid-response", f"{variant} response is not JSON") from exc

    with ThreadPoolExecutor(max_workers=len(VARIANTS)) as pool:
        responses = dict(pool.map(run, VARIANTS))
    return build_artifact(request, responses, max_spread=max_spread)
