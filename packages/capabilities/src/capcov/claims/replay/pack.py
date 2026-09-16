"""Load the reviewed replay rule pack (``rules-replay-v1.json``) as a validated Bundle.

The pack lives under ``experiments/claim-semantics/replay/`` relative to the
package root (a source checkout, not package data), and is kept in raw IR
JSON wire form and merged verbatim: every relation declaration and rule comes
from the file, nothing is evaluated here.  This is the same loader
``tests/claim_semantics/replay_rules/adapter.py`` implements; it is in ``src``
so ``capcov.claims.replay.join`` and ``scripts/`` can build the judge's
combined bundle without the tests on ``sys.path`` -- and build it identically,
because the compiled checker's program identity depends on the declaration
order the combiner yields.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..ir import Bundle, bundle_from_json

PACKAGE_ROOT = Path(__file__).resolve().parents[4]
REPLAY_ROOT = PACKAGE_ROOT / "experiments" / "claim-semantics" / "replay"
PACK_PATH = REPLAY_ROOT / "rules-replay-v1.json"
PACK_ID = "rules-replay-v1"

DIAGNOSTIC_POLICY = {"missing_premises": "unresolved", "inconsistent_premises": "inconsistent-premises",
                     "out_of_scope": "out-of-scope", "forbidden_evidence": "invalid-input",
                     "revocation": "refutation", "completeness": "required"}
RELATION_FIELDS = {"name", "columns", "modality", "polarity", "binding", "primitive", "producer_classes",
                   "context_indices", "completes", "finite", "nonempty", "compatibility_targets",
                   "compatibility_context_indices"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pack(path: Path = PACK_PATH) -> dict[str, Any]:
    pack = read_json(path)
    if pack.get("schema_version") != 1 or pack.get("id") != PACK_ID:
        raise ValueError("unsupported replay rule pack")
    for section in ("primitives", "supplementary_primitives", "derived", "rules"):
        if not isinstance(pack.get(section), list):
            raise ValueError(f"rule pack section {section!r} must be a list")
    return pack


def pack_relations(pack: dict[str, Any]) -> list[dict[str, Any]]:
    relations = [*pack["primitives"], *pack["supplementary_primitives"], *pack["derived"]]
    names = [relation["name"] for relation in relations]
    if len(names) != len(set(names)):
        raise ValueError("rule pack declares a relation twice")
    for relation in relations:
        if set(relation) != RELATION_FIELDS:
            raise ValueError(f"relation {relation.get('name')!r} has unknown or missing fields")
    return relations


def pack_bundle(pack: dict[str, Any] | None = None) -> Bundle:
    """The rule pack alone (declarations and rules, no facts) as a validated Bundle."""
    pack = pack or load_pack()
    return bundle_from_json({"schema_version": 1, "relations": pack_relations(pack),
                             "rules": [dict(rule) for rule in pack["rules"]],
                             "diagnostic_policy": dict(DIAGNOSTIC_POLICY)}, validate=True)


__all__ = ["PACKAGE_ROOT", "REPLAY_ROOT", "PACK_PATH", "PACK_ID", "DIAGNOSTIC_POLICY", "RELATION_FIELDS",
           "read_json", "load_pack", "pack_relations", "pack_bundle"]
