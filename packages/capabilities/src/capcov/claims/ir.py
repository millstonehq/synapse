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


SCHEMA_VERSION = 1


class _TextEnum(str, Enum):
    def __str__(self) -> str: return self.value


class TypeName(_TextEnum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DECIMAL = "decimal"
    IDENTIFIER = "identifier"
    TIMESTAMP = "timestamp"
    JSON = "json"


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "modality", Modality(self.modality))
        object.__setattr__(self, "polarity", Polarity(self.polarity))
        object.__setattr__(self, "binding", BindingTime(self.binding))
        object.__setattr__(self, "producer_classes", tuple(sorted(self.producer_classes)))
        object.__setattr__(self, "context_indices", tuple(self.context_indices))

    @property
    def arity(self) -> int: return len(self.columns)


@dataclass(frozen=True)
class Context:
    values: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "Context":
        return cls(tuple(sorted(values.items())))

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(sorted(self.values)))

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


Term = Variable | Constant


@dataclass(frozen=True)
class Atom:
    relation: str
    terms: tuple[Term, ...]
    negated: bool = False

    def __post_init__(self) -> None: object.__setattr__(self, "terms", tuple(self.terms))


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

    def __post_init__(self) -> None:
        # These collections denote sets in the language.  Normalize their
        # order at construction time so independently assembled bundles hash
        # identically even when their producers enumerate inputs differently.
        object.__setattr__(self, "relations", tuple(sorted(self.relations, key=lambda x: x.name)))
        object.__setattr__(self, "facts", tuple(sorted(self.facts, key=lambda x: repr(x))))
        object.__setattr__(self, "rules", tuple(sorted(self.rules, key=lambda x: (x.name, repr(x)))))
        object.__setattr__(self, "claims", tuple(sorted(self.claims, key=lambda x: repr(x))))
        object.__setattr__(self, "metadata", tuple(sorted(self.metadata)))
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported claim schema version: {self.schema_version}")


def _plain(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if isinstance(value, (str, int, float, bool)) or value is None: return value
    if isinstance(value, Mapping): return {str(k): _plain(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (tuple, list, set, frozenset)): return [_plain(v) for v in value]
    if is_dataclass(value):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    raise TypeError(f"not canonicalisable: {type(value).__name__}")


def canonical_dict(value: Any) -> dict[str, Any] | Any:
    """Return JSON-compatible data with deterministic field and set ordering."""
    return _plain(value)


def canonical_json(value: Any) -> str:
    return json.dumps(canonical_dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def schema_digest(bundle: Bundle) -> str: return digest(bundle)


def to_json(value: Any) -> str: return canonical_json(value)


def canonical_digest(value: Any) -> str: return digest(value)
