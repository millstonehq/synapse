"""The small, serialisable intermediate representation for claim rules.

This module intentionally contains no evaluation code.  Values are frozen so a
bundle can safely be hashed and handed to independent evaluators.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping, Sequence
import math


SCHEMA_VERSION = 1


class _TextEnum(str, Enum):
    def __str__(self) -> str: return self.value


class TypeName(_TextEnum):
    SYMBOL = "symbol"
    INTEGER = "integer"
    UNSIGNED = "unsigned"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"  # epoch microseconds
    DIGEST = "digest"
    JSON_METADATA_ONLY = "json-metadata-only"


class Modality(_TextEnum):
    OBSERVATION = "observation"
    ASSUMPTION = "assumption"
    COMPATIBILITY = "compatibility"
    COMPLETENESS = "completeness"
    CLAIM = "claim"
    DERIVED = "derived"


class Polarity(_TextEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class BindingTime(_TextEnum):
    STATIC = "static"
    RUNTIME = "runtime"


class Quantifier(_TextEnum):
    EXISTS = "exists"
    FORALL = "forall"


class EvidenceEffect(_TextEnum):
    """How a relation contributes to a claim's semantic polarity."""
    SUPPORT = "support"
    REFUTATION = "refutation"
    OBSERVATION = "observation"
    FORBIDDEN = "forbidden"


class OutputKind(_TextEnum):
    OBSERVED = "observed"
    FORBIDDEN = "forbidden"
    DISCREPANCY = "discrepancy"
    MISSING_PREMISE = "missing_premise"


@dataclass(frozen=True)
class TemplateValue:
    """Typed constant or column reference used by a diagnostic output."""
    source: str = "constant"  # constant, claim, evidence
    column: str = ""
    type: TypeName | str = TypeName.SYMBOL
    value: Any = None
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "type", TypeName(self.type))


@dataclass(frozen=True)
class OutputTemplate:
    kind: OutputKind | str
    claim_id: str
    evidence_id: str | None = None
    relation: str | None = None
    fields: tuple[tuple[str, TemplateValue], ...] = ()
    requires_all_evidence: tuple[str, ...] = ()
    requires_any_evidence: tuple[str, ...] = ()
    excludes_evidence: tuple[str, ...] = ()
    when_claim: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", OutputKind(self.kind))
        object.__setattr__(self, "fields", tuple(sorted(self.fields)))
        object.__setattr__(self, "requires_all_evidence", tuple(sorted(self.requires_all_evidence)))
        object.__setattr__(self, "requires_any_evidence", tuple(sorted(self.requires_any_evidence)))
        object.__setattr__(self, "excludes_evidence", tuple(sorted(self.excludes_evidence)))


@dataclass(frozen=True)
class Column:
    name: str
    type: TypeName | str
    context: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "type", TypeName(self.type))


@dataclass(frozen=True)
class RelationDecl:
    name: str
    columns: tuple[Column, ...]
    modality: Modality | str = Modality.OBSERVATION
    polarity: Polarity | str = Polarity.POSITIVE
    binding: BindingTime | str = BindingTime.RUNTIME
    primitive: bool = True
    producer_classes: tuple[str, ...] = ()
    context_indices: tuple[str, ...] = ()
    completes: str | None = None
    finite: bool = False
    nonempty: bool = False
    compatibility_targets: tuple[str, ...] = ()
    compatibility_context_indices: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "modality", Modality(self.modality))
        object.__setattr__(self, "polarity", Polarity(self.polarity))
        object.__setattr__(self, "binding", BindingTime(self.binding))
        object.__setattr__(self, "producer_classes", tuple(sorted(self.producer_classes)))
        object.__setattr__(self, "context_indices", tuple(self.context_indices))
        object.__setattr__(self, "compatibility_targets", tuple(sorted(self.compatibility_targets)))
        object.__setattr__(self, "compatibility_context_indices", tuple(self.compatibility_context_indices))

    @property
    def arity(self) -> int: return len(self.columns)


@dataclass(frozen=True)
class Context:
    values: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "Context":
        return cls(tuple(sorted(values.items())))

    def __post_init__(self) -> None:
        if any(not isinstance(k, str) for k, _ in self.values): raise TypeError("context keys must be strings")
        keys = [k for k, _ in self.values]
        if len(keys) != len(set(keys)): raise ValueError("duplicate context keys")
        object.__setattr__(self, "values", tuple((k, _freeze_value(v)) for k, v in sorted(self.values)))

    def as_dict(self) -> dict[str, Any]: return dict(self.values)


@dataclass(frozen=True)
class Variable:
    name: str


@dataclass(frozen=True)
class Constant:
    value: Any
    type: TypeName | str | None = None

    def __post_init__(self) -> None:
        if self.type is not None: object.__setattr__(self, "type", TypeName(self.type))
        object.__setattr__(self, "value", _freeze_value(self.value))


Term = Variable | Constant


@dataclass(frozen=True)
class Atom:
    relation: str
    terms: tuple[Term, ...]
    negated: bool = False

    def __post_init__(self) -> None: object.__setattr__(self, "terms", tuple(self.terms))


@dataclass(frozen=True)
class Evidence:
    """Authoritative fact identity and provenance, separate from its atom."""
    id: str
    atom: Atom
    context: Context = field(default_factory=Context)
    source: str = ""
    depends_on: tuple[str, ...] = ()
    kind: str = "fact"

    def __post_init__(self) -> None:
        if not self.id: raise ValueError("evidence id must not be empty")
        object.__setattr__(self, "depends_on", tuple(sorted(set(self.depends_on))))


@dataclass(frozen=True)
class EvidenceMapping:
    """Explicit relation-to-relation polarity mapping used by evaluators."""
    claim_relation: str
    evidence_relation: str
    effect: EvidenceEffect | str
    context_indices: tuple[str, ...] = ()
    bindings: tuple[tuple[str, str], ...] = ()
    required: bool = False
    allow_out_of_scope: bool = False
    claim_id: str = ""

    def __post_init__(self) -> None:
        try: effect = EvidenceEffect(self.effect)
        except (TypeError, ValueError): effect = self.effect
        object.__setattr__(self, "effect", effect)
        object.__setattr__(self, "context_indices", tuple(sorted(set(self.context_indices))))
        object.__setattr__(self, "bindings", tuple(sorted(self.bindings)))


@dataclass(frozen=True)
class DiagnosticRule:
    """Typed trigger for an operational/semantic diagnostic."""
    trigger_relation: str
    effect: EvidenceEffect | str
    operational_status: str = "complete"
    context_indices: tuple[str, ...] = ()
    when_missing: bool = False
    required: bool = False
    message: str = ""
    claim_id: str = ""
    predicate: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        try: effect = EvidenceEffect(self.effect)
        except (TypeError, ValueError): effect = self.effect
        object.__setattr__(self, "effect", effect)
        object.__setattr__(self, "context_indices", tuple(sorted(set(self.context_indices))))
        object.__setattr__(self, "predicate", tuple(sorted(self.predicate)))


@dataclass(frozen=True)
class DiagnosticPolicy:
    """Declared handling policy for evidence diagnostics and revocation."""
    missing_premises: str = "unresolved"
    inconsistent_premises: str = "inconsistent-premises"
    out_of_scope: str = "out-of-scope"
    forbidden_evidence: str = "invalid-input"
    revocation: str = "refutation"
    completeness: str = "required"


@dataclass(frozen=True)
class Comparison:
    left: Term
    operator: str
    right: Term


@dataclass(frozen=True)
class Aggregation:
    name: str
    relation: str
    group_by: tuple[str, ...]
    value_variable: str
    operator: str = "count"
    domain: str | None = None
    closure_witness: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "group_by", tuple(self.group_by))


@dataclass(frozen=True)
class Rule:
    head: Atom
    body: tuple[Atom | Comparison, ...]
    name: str = ""
    aggregation: Aggregation | None = None

    def __post_init__(self) -> None: object.__setattr__(self, "body", tuple(self.body))


@dataclass(frozen=True)
class Claim:
    relation: str
    terms: tuple[Term, ...]
    context: Context = field(default_factory=Context)
    quantifier: Quantifier | str = Quantifier.EXISTS
    domain: str | None = None
    id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "terms", tuple(self.terms))
        object.__setattr__(self, "quantifier", Quantifier(self.quantifier))


@dataclass(frozen=True)
class Bundle:
    relations: tuple[RelationDecl, ...]
    facts: tuple[Atom, ...] = ()
    rules: tuple[Rule, ...] = ()
    claims: tuple[Claim, ...] = ()
    metadata: tuple[tuple[str, Any], ...] = ()
    schema_version: int = SCHEMA_VERSION
    evidence: tuple[Evidence, ...] = ()
    mappings: tuple[EvidenceMapping, ...] = ()
    diagnostic_policy: DiagnosticPolicy = field(default_factory=DiagnosticPolicy)
    diagnostics: tuple[DiagnosticRule, ...] = ()
    outputs: tuple[OutputTemplate, ...] = ()

    def __post_init__(self) -> None:
        # These collections denote sets in the language.  Normalize their
        # order at construction time so independently assembled bundles hash
        # identically even when their producers enumerate inputs differently.
        object.__setattr__(self, "relations", tuple(sorted(self.relations, key=_sort_key)))
        object.__setattr__(self, "facts", tuple(sorted(self.facts, key=_sort_key)))
        object.__setattr__(self, "rules", tuple(sorted(self.rules, key=_sort_key)))
        object.__setattr__(self, "claims", tuple(sorted(self.claims, key=_sort_key)))
        object.__setattr__(self, "evidence", tuple(sorted(self.evidence, key=_sort_key)))
        object.__setattr__(self, "mappings", tuple(sorted(self.mappings, key=_sort_key)))
        object.__setattr__(self, "diagnostics", tuple(sorted(self.diagnostics, key=_sort_key)))
        object.__setattr__(self, "outputs", tuple(sorted(self.outputs, key=_sort_key)))
        metadata_keys = [k for k, _ in self.metadata]
        if any(not isinstance(k, str) for k in metadata_keys): raise TypeError("metadata keys must be strings")
        if len(metadata_keys) != len(set(metadata_keys)): raise ValueError("duplicate metadata keys")
        object.__setattr__(self, "metadata", tuple((k, _freeze_value(v)) for k, v in sorted(self.metadata)))
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported claim schema version: {self.schema_version}")


def _plain(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if isinstance(value, (str, int, float, bool)) or value is None: return value
    if isinstance(value, _FrozenMap): return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, Mapping): raise TypeError("mapping must be recursively frozen before canonicalisation")
    if isinstance(value, (tuple, list, set, frozenset)): return [_plain(v) for v in value]
    if is_dataclass(value):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    raise TypeError(f"not canonicalisable: {type(value).__name__}")


def canonical_dict(value: Any) -> dict[str, Any] | Any:
    """Return JSON-compatible data with deterministic field and set ordering."""
    return _plain(value if is_dataclass(value) else _freeze_value(value))


def canonical_json(value: Any) -> str:
    return json.dumps(canonical_dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def schema_digest(bundle: Bundle) -> str: return digest(bundle)


def to_json(value: Any) -> str: return canonical_json(value)


def canonical_digest(value: Any) -> str: return digest(value)


def _sort_key(value: Any) -> str:
    """Canonical structural key; malformed IR gets a deterministic type key."""
    try:
        return canonical_json(value)
    except (TypeError, ValueError):
        if is_dataclass(value):
            return value.__class__.__module__ + "." + value.__class__.__qualname__ + "{" + ",".join(f.name + ":" + _sort_key(getattr(value, f.name)) for f in fields(value)) + "}"
        return type(value).__module__ + "." + type(value).__qualname__


class _FrozenMap(Mapping[str, Any]):
    __slots__ = ("_items",)
    def __init__(self, items): self._items = tuple(items)
    def __getitem__(self, key): return dict(self._items)[key]
    def __iter__(self): return (k for k, _ in self._items)
    def __len__(self): return len(self._items)
    def items(self): return self._items


def _freeze_value(value: Any) -> Any:
    """Copy supported JSON values into immutable values before they enter IR."""
    if value is None or isinstance(value, (str, bool, int)): return value
    if isinstance(value, float):
        if not math.isfinite(value): raise ValueError("non-finite floats are not canonical JSON values")
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value):
            raise TypeError("canonical JSON object keys must be strings")
        return _FrozenMap((k, _freeze_value(v)) for k, v in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(v) for v in value)
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def _strict_object(raw, allowed, path):
    if not isinstance(raw, dict): raise TypeError(f"{path} must be an object")
    unknown = set(raw) - set(allowed)
    if unknown: raise ValueError(f"{path} has unknown fields: {sorted(unknown)}")
    return raw


def bundle_from_json(source: str | bytes | Mapping[str, Any], *, validate: bool = True) -> Bundle:
    """Strictly ingest a schema-v1 JSON object; unknown fields are rejected."""
    def reject_constant(value): raise ValueError(f"non-standard JSON constant: {value}")
    def reject_duplicate(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    raw = json.loads(source, parse_constant=reject_constant, object_pairs_hook=reject_duplicate) if isinstance(source, (str, bytes)) else source
    _strict_object(raw, {"schema_version", "relations", "facts", "evidence", "mappings", "diagnostic_policy", "diagnostics", "outputs", "rules", "claims", "metadata"}, "bundle")
    if isinstance(raw.get("schema_version"), bool) or raw.get("schema_version") != SCHEMA_VERSION: raise ValueError("unsupported claim schema version")
    def column(x):
        x = _strict_object(x, {"name", "type", "context"}, "column")
        return Column(x["name"], x["type"], x.get("context", False))
    def relation(x):
        x = _strict_object(x, {"name", "columns", "modality", "polarity", "binding", "primitive", "producer_classes", "context_indices", "completes", "finite", "nonempty", "compatibility_targets", "compatibility_context_indices"}, "relation")
        return RelationDecl(x["name"], tuple(column(c) for c in x.get("columns", ())), x.get("modality", "observation"), x.get("polarity", "positive"), x.get("binding", "runtime"), x.get("primitive", True), tuple(x.get("producer_classes", ())), tuple(x.get("context_indices", ())), x.get("completes"), x.get("finite", False), x.get("nonempty", False), tuple(x.get("compatibility_targets", ())), tuple(x.get("compatibility_context_indices", ())))
    def term(x):
        # Accept both wire form (variable) and canonical dataclass form
        # (name), so canonical bundles are strict-ingestible again.
        if isinstance(x, dict) and "name" in x and "variable" not in x:
            x = {"variable": x["name"]}
        x = _strict_object(x, {"variable", "value", "type"}, "term")
        if "variable" in x:
            if set(x) != {"variable"}: raise ValueError("variable term cannot have value/type")
            return Variable(x["variable"])
        if "value" not in x: raise ValueError("term needs variable or value")
        return Constant(x["value"], x.get("type"))
    def atom(x):
        x = _strict_object(x, {"relation", "terms", "negated"}, "atom")
        return Atom(x["relation"], tuple(term(t) for t in x.get("terms", ())), x.get("negated", False))
    def comparison(x):
        x = _strict_object(x, {"left", "operator", "right"}, "comparison")
        return Comparison(term(x["left"]), x["operator"], term(x["right"]))
    def rule(x):
        x = _strict_object(x, {"head", "body", "name", "aggregation"}, "rule")
        agg = x.get("aggregation")
        if agg is not None:
            _strict_object(agg, {"name", "relation", "group_by", "value_variable", "operator", "domain", "closure_witness"}, "aggregation")
            agg = Aggregation(agg["name"], agg["relation"], tuple(agg.get("group_by", ())), agg["value_variable"], agg.get("operator", "count"), agg.get("domain"), agg.get("closure_witness"))
        body = tuple(comparison(a["comparison"]) if isinstance(a, dict) and "comparison" in a else atom(a) for a in x.get("body", ()))
        return Rule(atom(x["head"]), body, x.get("name", ""), agg)
    def claim(x):
        x = _strict_object(x, {"id", "relation", "terms", "context", "quantifier", "domain"}, "claim")
        context_raw = x.get("context", {})
        if isinstance(context_raw, dict) and set(context_raw) == {"values"}:
            context_raw = dict(context_raw["values"])
        return Claim(x["relation"], tuple(term(t) for t in x.get("terms", ())), Context.from_mapping(context_raw), x.get("quantifier", "exists"), x.get("domain"), x.get("id", ""))
    def evidence(x):
        x = _strict_object(x, {"id", "atom", "relation", "terms", "context", "source", "depends_on", "kind"}, "evidence")
        raw_atom = x.get("atom")
        if raw_atom is None: raw_atom = {"relation": x["relation"], "terms": x.get("terms", ())}
        context_raw = x.get("context", {})
        if isinstance(context_raw, dict) and set(context_raw) == {"values"}:
            context_raw = dict(context_raw["values"])
        return Evidence(x["id"], atom(raw_atom), Context.from_mapping(context_raw), x.get("source", ""), tuple(x.get("depends_on", ())), x.get("kind", "fact"))
    def mapping(x):
        x = _strict_object(x, {"claim_id", "claim_relation", "evidence_relation", "effect", "context_indices", "bindings", "required", "allow_out_of_scope"}, "mapping")
        return EvidenceMapping(x["claim_relation"], x["evidence_relation"], x["effect"], tuple(x.get("context_indices", ())), tuple(tuple(pair) for pair in x.get("bindings", ())), x.get("required", False), x.get("allow_out_of_scope", False), x.get("claim_id", ""))
    def diagnostic(x):
        x = _strict_object(x, {"claim_id", "trigger_relation", "effect", "operational_status", "context_indices", "when_missing", "required", "message", "predicate"}, "diagnostic")
        predicate = x.get("predicate") or {}
        if isinstance(predicate, (list, tuple)):
            pairs = []
            for pair in predicate:
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    raise ValueError("diagnostic predicate canonical form requires key/value pairs")
                pairs.append(tuple(pair))
            keys = [key for key, _ in pairs]
            if len(keys) != len(set(keys)): raise ValueError("duplicate diagnostic predicate key")
            predicate = dict(pairs)
        if predicate: _strict_object(predicate, {"column", "operator", "value"}, "diagnostic.predicate")
        if predicate and (not isinstance(predicate.get("column"), str) or not isinstance(predicate.get("operator"), str)):
            raise ValueError("diagnostic predicate column/operator must be strings")
        return DiagnosticRule(x["trigger_relation"], x["effect"], x.get("operational_status", "complete"), tuple(x.get("context_indices", ())), x.get("when_missing", False), x.get("required", False), x.get("message", ""), x.get("claim_id", ""), tuple(sorted(predicate.items())))
    def output(x):
        x = _strict_object(x, {"kind", "claim_id", "evidence_id", "relation", "fields", "requires_all_evidence", "requires_any_evidence", "excludes_evidence", "when_claim"}, "output")
        fields_raw = x.get("fields") or {}
        if isinstance(fields_raw, (list, tuple)):
            pairs = []
            for pair in fields_raw:
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    raise ValueError("canonical output fields require key/value pairs")
                pairs.append(tuple(pair))
            names = [name for name, _ in pairs]
            if len(names) != len(set(names)): raise ValueError("duplicate output field")
            fields_raw = dict(pairs)
        if not isinstance(fields_raw, dict): raise ValueError("output fields must be an object")
        values = []
        for name, value in fields_raw.items():
            value = _strict_object(value, {"source", "column", "type", "value", "evidence_id"}, "output field")
            values.append((name, TemplateValue(value.get("source", "constant"), value.get("column", ""), value.get("type", "symbol"), value.get("value"), value.get("evidence_id"))))
        kind = x["kind"]
        default_when = "underived" if kind == "discrepancy" else None
        return OutputTemplate(kind, x["claim_id"], x.get("evidence_id"), x.get("relation"), tuple(values), tuple(x.get("requires_all_evidence", ())), tuple(x.get("requires_any_evidence", ())), tuple(x.get("excludes_evidence", ())), x.get("when_claim", default_when))
    policy_raw = raw.get("diagnostic_policy") or {}
    _strict_object(policy_raw, {"missing_premises", "inconsistent_premises", "out_of_scope", "forbidden_evidence", "revocation", "completeness"}, "diagnostic_policy")
    policy = DiagnosticPolicy(**policy_raw)
    metadata_raw = raw.get("metadata") or {}
    metadata_items = metadata_raw if isinstance(metadata_raw, list) else metadata_raw.items()
    bundle = Bundle(tuple(relation(x) for x in raw.get("relations", ())), tuple(atom(x) for x in raw.get("facts", ())), tuple(rule(x) for x in raw.get("rules", ())), tuple(claim(x) for x in raw.get("claims", ())), tuple(sorted(metadata_items)), SCHEMA_VERSION, tuple(evidence(x) for x in raw.get("evidence", ())), tuple(mapping(x) for x in raw.get("mappings", ())), policy, tuple(diagnostic(x) for x in raw.get("diagnostics", ())), tuple(output(x) for x in raw.get("outputs", ())))
    if validate:
        from .validation import assert_valid
        assert_valid(bundle)
    return bundle


def from_json(source): return bundle_from_json(source)
