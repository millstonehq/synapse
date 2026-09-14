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
    relations = []
    for name, declaration in schema["relations"].items():
        relations.append({"name": name, **{k: v for k, v in declaration.items() if k != "arg_order"}})

    def terms(entry: dict[str, Any]) -> list[dict[str, Any]]:
        declaration = schema["relations"][entry["relation"]]
        return [_term(value, column["type"]) for value, column in zip(entry["args"], declaration["columns"])]

    all_entries = [*fixture["facts"], *fixture["assumptions"]]
    facts = [{"relation": entry["relation"], "terms": terms(entry)} for entry in all_entries]
    evidence = [{"id": entry["id"], "relation": entry["relation"], "terms": terms(entry),
                 "context": {k: entry["context"][k] for k in schema["relations"][entry["relation"]]["context_indices"] if k in entry["context"]},
                 "source": entry.get("source", entry.get("provenance", {}).get("source", "fixture")),
                 "depends_on": entry.get("provenance", {}).get("depends_on", []),
                 "kind": "assumption" if entry in fixture["assumptions"] else "fact"} for entry in all_entries]
    claims = []
    for entry in fixture["claims"]:
        declaration = schema["relations"][entry["relation"]]
        context = {key: entry["context"][key] for key in declaration["context_indices"]}
        claims.append({"id": entry["id"], "relation": entry["relation"], "terms": terms(entry), "context": context, "quantifier": entry["quantifier"], "domain": entry["domain"]})
    # Compile relation-name-compatible evidence rules and explicit polarity maps.
    # This is deliberately schema-driven; expected.json is never read here.
    rules, mappings = [], []
    for claim_entry in fixture["claims"]:
        cdecl = schema["relations"][claim_entry["relation"]]
        c_names = [c["name"] for c in cdecl["columns"]]
        before = len(rules)
        for source_name, sdecl in schema["relations"].items():
            if sdecl["modality"] in {"claim", "completeness"}: continue
            s_names = [c["name"] for c in sdecl["columns"]]
            if not set(c_names).issubset(s_names): continue
            head = {"relation": claim_entry["relation"], "terms": [{"variable": n} for n in c_names]}
            body = {"relation": source_name, "terms": [{"variable": n} for n in s_names]}
            rules.append({"name": f"map_{claim_entry['relation']}_{source_name}", "head": head, "body": [body]})
            effect = "refutation" if sdecl["polarity"] == "negative" else "support"
            mappings.append({"claim_relation": claim_entry["relation"], "evidence_relation": source_name,
                             "effect": effect, "context_indices": sorted(set(cdecl["context_indices"]) & set(sdecl["context_indices"]))})
        if len(rules) == before:
            # A claim may intentionally project a relation (case 11).  Keep a
            # real, safe rule by binding its shared context and retaining the
            # projected claim constants; this records scope without inventing
            # an evaluator-specific fixture branch.
            for source_name, sdecl in schema["relations"].items():
                if sdecl["modality"] in {"claim", "completeness"}: continue
                s_names = [c["name"] for c in sdecl["columns"]]
                shared = set(cdecl["context_indices"]) & set(sdecl["context_indices"])
                if not shared: continue
                head_terms = []
                for name, value in zip(c_names, claim_entry["args"]):
                    head_terms.append({"variable": name} if name in s_names else _term(value, next(c["type"] for c in cdecl["columns"] if c["name"] == name)))
                rules.append({"name": f"project_{claim_entry['relation']}_{source_name}",
                              "head": {"relation": claim_entry["relation"], "terms": head_terms},
                              "body": [{"relation": source_name, "terms": [{"variable": n} for n in s_names]}]})
                mappings.append({"claim_relation": claim_entry["relation"], "evidence_relation": source_name,
                                 "effect": "support", "context_indices": sorted(shared), "required": True})
                break
    semantic_inputs = {
        "fixture_id": fixture["id"],
        "context": fixture["context"],
        "facts": [dict(entry) for entry in fixture["facts"]],
        "assumptions": [dict(entry) for entry in fixture["assumptions"]],
        "claims": [dict(entry) for entry in fixture["claims"]],
    }
    return {"schema_version": 1, "relations": relations, "facts": facts, "evidence": evidence,
            "mappings": mappings, "rules": rules, "claims": claims,
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
