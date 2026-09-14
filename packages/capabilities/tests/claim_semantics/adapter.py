"""Lossless bridge from review fixtures to the authoritative claims IR."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capcov.claims import bundle_from_json, canonical_dict  # noqa: E402

ROOT = Path(__file__).parent / "corpus"


def _term(value: Any, type_name: str) -> dict[str, Any]:
    return {"value": value, "type": type_name}


def bundle_payload(fixture: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads((ROOT / "schema-v1.json").read_text(encoding="utf-8"))
    relations = []
    for name, declaration in schema["relations"].items():
        relations.append({"name": name, **{k: v for k, v in declaration.items() if k != "arg_order"}})

    def terms(entry: dict[str, Any]) -> list[dict[str, Any]]:
        declaration = schema["relations"][entry["relation"]]
        return [_term(value, column["type"]) for value, column in zip(entry["args"], declaration["columns"])]

    facts = [{"relation": entry["relation"], "terms": terms(entry)} for entry in [*fixture["facts"], *fixture["assumptions"]]]
    claims = []
    for entry in fixture["claims"]:
        declaration = schema["relations"][entry["relation"]]
        context = {key: entry["context"][key] for key in declaration["context_indices"]}
        claims.append({"relation": entry["relation"], "terms": terms(entry), "context": context, "quantifier": entry["quantifier"], "domain": entry["domain"]})
    semantic_inputs = {
        "fixture_id": fixture["id"],
        "context": fixture["context"],
        "facts": [dict(entry) for entry in fixture["facts"]],
        "assumptions": [dict(entry) for entry in fixture["assumptions"]],
        "claims": [dict(entry) for entry in fixture["claims"]],
    }
    return {"schema_version": 1, "relations": relations, "facts": facts, "rules": [], "claims": claims, "metadata": {"fixture_id": fixture["id"], "semantic_inputs": semantic_inputs}}


def load_fixture(path: Path) -> Any:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return bundle_from_json(bundle_payload(fixture), validate=True)


def canonical_metadata(bundle: Any) -> dict[str, Any]:
    """Expose the parser's frozen metadata in JSON-compatible form for tests."""
    return dict(canonical_dict(bundle)["metadata"])
