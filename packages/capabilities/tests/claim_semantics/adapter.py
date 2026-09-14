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
                 "context": {k: dict(zip(entry["arg_order"], entry["args"]))[k] for k in schema["relations"][entry["relation"]]["context_indices"] if k in entry["context"]},
                 "source": entry.get("source", entry.get("provenance", {}).get("source", "fixture")),
                 "depends_on": entry.get("provenance", {}).get("depends_on", []),
                 "kind": "assumption" if entry in fixture["assumptions"] else "fact"} for entry in all_entries]
    claims = []
    for entry in fixture["claims"]:
        declaration = schema["relations"][entry["relation"]]
        context = {key: entry["context"][key] for key in declaration["context_indices"]}
        claims.append({"id": entry["id"], "relation": entry["relation"], "terms": terms(entry), "context": context, "quantifier": entry["quantifier"], "domain": entry["domain"]})
    # Versioned domain rule library.  It is keyed by semantic relation shape,
    # never by fixture id or expected verdicts.  A rule only fires after every
    # listed premise is present in the same projected claim context.
    RULE_LIBRARY = {
        "notification_delivery_terminal": (("http_save_succeeded", "issue_changed_observed", "smtp_accepted", "sql_terminal_state"),),
        "effect_reached": (("static_route_exists", "runtime_route_observed"),),
        "post_request_succeeded": (("http_post_accepted",),),
        "row_created": (("sql_row_exists", "sql_snapshot_current__accepted"),),
        "authorized": (("http_authorization",),),
        "smtp_accepted__claim": (("smtp_accepted",),),
        "provider_accepted": (("smtp_accepted",),),
        "capability_holds_in_all_compatible_histories": (("compatible_history",),),
        "no_resend_during_window": (("one_delivery", "no_resend_observed", "observation_window_closed__accepted"),),
    }
    rules, mappings, diagnostics = [], [], []
    for claim_entry in fixture["claims"]:
        cdecl = schema["relations"][claim_entry["relation"]]
        c_names = [c["name"] for c in cdecl["columns"]]
        claim_values = dict(zip(c_names, claim_entry["args"]))
        for wave, premises in enumerate(RULE_LIBRARY.get(claim_entry["relation"], ())):
            body = []
            bindings = []
            for source_name in premises:
                sdecl = schema["relations"][source_name]; s_names = [c["name"] for c in sdecl["columns"]]
                source_terms = []
                source_bindings = []
                for col in sdecl["columns"]:
                    if col["name"] in claim_values:
                        source_terms.append(_term(claim_values[col["name"]], col["type"]))
                        source_bindings.append((col["name"], col["name"]))
                    else: source_terms.append({"variable": f"_{col['name']}"})
                body.append({"relation": source_name, "terms": source_terms})
                mappings.append({"claim_relation": claim_entry["relation"], "evidence_relation": source_name,
                                 "effect": "support" if sdecl["polarity"] == "positive" else "refutation",
                                 "context_indices": sorted(set(cdecl["context_indices"]) & set(sdecl["context_indices"])),
                                 "bindings": sorted(set(source_bindings)), "required": True})
            rules.append({"name": f"domain_v1_{claim_entry['relation']}_{wave}", "head": {"relation": claim_entry["relation"], "terms": [_term(v, c["type"]) for v, c in zip(claim_entry["args"], cdecl["columns"])]}, "body": body})
        # Negative observed relations are explicit refutation evidence; rejected
        # or revoked assumptions become typed diagnostic triggers instead.
        for entry in fixture["facts"]:
            sdecl = schema["relations"][entry["relation"]]
            if sdecl["polarity"] == "negative":
                bindings = [(n, n) for n in c_names if n in [c["name"] for c in sdecl["columns"]]]
                mappings.append({"claim_relation": claim_entry["relation"], "evidence_relation": entry["relation"], "effect": "refutation", "context_indices": sorted(set(cdecl["context_indices"]) & set(sdecl["context_indices"])), "bindings": bindings})
    for entry in fixture["assumptions"]:
        relation = entry["relation"]
        if relation.endswith("__revoked"): effect, status = "refutation", "stale"
        elif relation.endswith("__rejected"): effect, status = "forbidden", "invalid-input"
        else: effect, status = "observation", "complete"
        diagnostics.append({"trigger_relation": relation, "effect": effect, "operational_status": status,
                            "context_indices": schema["relations"][relation]["context_indices"],
                            "required": True, "message": f"policy trigger: {relation}"})
    # Scope-only claims still compile a rule into a non-claim candidate
    # relation.  This preserves a tangible rule for the evaluator while
    # preventing an unexpected runtime surface from becoming support.
    if not rules:
        claim_entry = fixture["claims"][0]
        cdecl = schema["relations"][claim_entry["relation"]]
        candidate = f"{claim_entry['relation']}_scope_candidate"
        relations.append({"name": candidate, "columns": cdecl["columns"],
                          "modality": "derived", "polarity": "positive", "binding": "runtime", "primitive": False,
                          "producer_classes": [], "context_indices": cdecl["context_indices"], "completes": None,
                          "finite": False, "nonempty": False, "compatibility_targets": [], "compatibility_context_indices": []})
        source = next((x for x in schema["relations"] if x == "runtime_surface_observed"), None)
        if source:
            sdecl = schema["relations"][source]; snames = [c["name"] for c in sdecl["columns"]]
            rules.append({"name": f"scope_v1_{candidate}", "head": {"relation": candidate, "terms": [_term(v, c["type"]) for v, c in zip(claim_entry["args"], cdecl["columns"])]},
                          "body": [{"relation": source, "terms": [{"variable": f"_{n}"} for n in snames]}]})
            mappings.append({"claim_relation": claim_entry["relation"], "evidence_relation": source,
                             "effect": "observation", "context_indices": sorted(set(cdecl["context_indices"]) & set(sdecl["context_indices"])),
                             "bindings": [(n, n) for n in cdecl["context_indices"] if n in snames]})
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
