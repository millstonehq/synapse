"""Lossless bridge from review fixtures to the authoritative claims IR."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capcov.claims import (Atom, Bundle, Claim, Constant, Evidence, EvidenceEffect,
                           EvidenceMapping, RelationDecl, Rule, Variable,
                           bundle_from_json, canonical_dict)  # noqa: E402

ROOT = Path(__file__).parent / "corpus"


def _term(value: Any, type_name: str) -> dict[str, Any]:
    return {"value": value, "type": type_name}


def bundle_payload(fixture: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads((ROOT / "schema-v1.json").read_text(encoding="utf-8"))
    if schema.get("program_schema_version") != 1 or fixture.get("program_schema_version") != 1 or "rules" not in fixture:
        raise ValueError("fixture lacks required schema-v1 semantic program declarations")
    relations = []
    for name, declaration in schema["relations"].items():
        relations.append({"name": name, **{k: v for k, v in declaration.items() if k != "arg_order"}})

    def terms(entry: dict[str, Any]) -> list[dict[str, Any]]:
        declaration = schema["relations"][entry["relation"]]
        return [_term(value, column["type"]) for value, column in zip(entry["args"], declaration["columns"])]

    all_entries = [*fixture["facts"], *fixture["assumptions"]]
    facts = [{"relation": entry["relation"], "terms": terms(entry)} for entry in all_entries]
    evidence = [{"id": entry["id"], "relation": entry["relation"], "terms": terms(entry),
                 "context": {k: dict(zip(entry["arg_order"], entry["args"]))[k] for k in schema["relations"][entry["relation"]]["context_indices"]},
                 "source": entry.get("source", entry.get("provenance", {}).get("source", "fixture")),
                 "depends_on": entry.get("provenance", {}).get("depends_on", []),
                 "kind": "assumption" if entry in fixture["assumptions"] else "fact"} for entry in all_entries]
    claims = []
    for entry in fixture["claims"]:
        declaration = schema["relations"][entry["relation"]]
        context = {key: entry["context"][key] for key in declaration["context_indices"]}
        claims.append({"id": entry["id"], "relation": entry["relation"], "terms": terms(entry), "context": context, "quantifier": entry["quantifier"], "domain": entry["domain"]})
    # Compile only declarations supplied by the fixture input.  No expected
    # verdicts, fixture IDs, or relation-name heuristics participate here.
    rules, mappings, diagnostics = [], [], []
    declarations = fixture.get("rules", ())
    claim_by_id = {entry["id"]: entry for entry in fixture["claims"]}
    rule_names = set()
    for declaration in declarations:
        if set(declaration) != {"name", "claim_id", "premises"}:
            raise ValueError("rule declaration has unknown or missing fields")
        if not isinstance(declaration["name"], str) or not declaration["name"] or declaration["name"] in rule_names:
            raise ValueError("rule names must be unique non-empty strings")
        rule_names.add(declaration["name"])
        if declaration["claim_id"] not in claim_by_id or not isinstance(declaration["premises"], list) or not declaration["premises"]:
            raise ValueError("rule declaration claim_id/premises are invalid")
        claim_entry = claim_by_id[declaration["claim_id"]]
        cdecl = schema["relations"][claim_entry["relation"]]
        claim_values = dict(zip((c["name"] for c in cdecl["columns"]), claim_entry["args"]))
        body = []
        for premise in declaration["premises"]:
            if set(premise) - {"relation", "bindings", "predicates", "scope"} or "relation" not in premise or "bindings" not in premise:
                raise ValueError("premise declaration has unknown or missing fields")
            if not isinstance(premise["bindings"], list) or any(set(binding) != {"claim_column", "evidence_column", "type"} for binding in premise["bindings"]):
                raise ValueError("binding declaration has unknown or missing fields")
            if not premise["bindings"] and premise.get("scope") != "global":
                raise ValueError("unbound premise requires explicit global scope")
            if premise.get("scope") not in (None, "global", "claim"):
                raise ValueError("unknown premise scope")
            if any(set(predicate) != {"column", "type", "value"} for predicate in premise.get("predicates", ())):
                raise ValueError("predicate declaration has unknown or missing fields")
            sdecl = schema["relations"][premise["relation"]]
            bindings = {binding["evidence_column"]: binding for binding in premise["bindings"]}
            predicates = {predicate["column"]: predicate for predicate in premise.get("predicates", ())}
            claim_columns = {column["name"]: column for column in cdecl["columns"]}
            source_terms = []
            for col in sdecl["columns"]:
                binding = bindings.get(col["name"])
                predicate = predicates.get(col["name"])
                if predicate:
                    if predicate["type"] != col["type"]: raise ValueError("typed predicate does not match evidence column")
                    source_terms.append(_term(predicate["value"], predicate["type"]))
                elif binding:
                    if binding["claim_column"] not in claim_columns or binding["type"] != col["type"] or binding["type"] != claim_columns[binding["claim_column"]]["type"]:
                        raise ValueError("typed rule binding does not match claim/evidence columns")
                    source_terms.append(_term(claim_values[binding["claim_column"]], binding["type"]))
                else: source_terms.append({"variable": f"_{col['name']}"})
            body.append({"relation": premise["relation"], "terms": source_terms})
        rules.append({"name": declaration["name"], "head": {"relation": claim_entry["relation"], "terms": [_term(v, c["type"]) for v, c in zip(claim_entry["args"], cdecl["columns"])]}, "body": body})
    for claim_entry in fixture["claims"]:
        cdecl = schema["relations"][claim_entry["relation"]]
        for mapping in claim_entry.get("mappings", ()):
            mapping = dict(mapping); mapping["claim_relation"] = claim_entry["relation"]; mapping["claim_id"] = claim_entry["id"]
            mappings.append(mapping)
        for diagnostic in claim_entry.get("diagnostics", ()):
            diagnostic = dict(diagnostic); diagnostic["claim_id"] = claim_entry["id"]
            diagnostics.append(diagnostic)
    semantic_inputs = {
        "fixture_id": fixture["id"],
        "context": fixture["context"],
        "facts": [dict(entry) for entry in fixture["facts"]],
        "assumptions": [dict(entry) for entry in fixture["assumptions"]],
        "claims": [dict(entry) for entry in fixture["claims"]],
    }
    return {"schema_version": 1, "relations": relations, "facts": facts, "evidence": evidence,
            "mappings": mappings, "diagnostics": diagnostics, "rules": rules, "claims": claims,
            "diagnostic_policy": {"missing_premises": "unresolved", "inconsistent_premises": "inconsistent-premises",
                                   "out_of_scope": "out-of-scope", "forbidden_evidence": "invalid-input",
                                   "revocation": "refutation", "completeness": "required"},
            "metadata": {"fixture_id": fixture["id"], "semantic_inputs": semantic_inputs}}


def load_fixture(path: Path) -> Any:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    return bundle_from_json(bundle_payload(fixture), validate=True)


def canonical_metadata(bundle: Any) -> dict[str, Any]:
    """Expose the parser's frozen metadata in JSON-compatible form for tests."""
    return dict(canonical_dict(bundle)["metadata"])
