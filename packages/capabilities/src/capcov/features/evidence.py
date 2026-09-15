"""Derive FODA feature coverage from capcov's native outcome evidence."""

from __future__ import annotations

from pathlib import Path

from ..flows import model as flow_model
from ..flows.model import digest
from .. import outcomes
from . import coverage, model as feature_model


def flow_inventory(value: dict) -> dict:
    """Use a unified capability inventory directly as the legacy flow denominator."""
    if value.get("kind") != "capabilities":
        return value
    return {
        "obligations": [
            {"id": row["id"], "kind": "surface", **({"outcomes": row["outcomes"]} if row.get("outcomes") else {})}
            for row in value.get("surfaces", [])
        ],
        "unresolved": value.get("unresolved", []),
        "excluded_surfaces": value.get("excluded_surfaces", {"count": 0, "surfaces": []}),
    }


def reconcile(
    model: dict,
    outcome_map: dict,
    inventory: dict,
    run: dict | None,
    root: Path,
    selected: set[str],
    *,
    flow_inputs: tuple[dict, dict, dict, dict] | None = None,
) -> dict:
    """Reconcile native pytest/browser evidence into feature-owned outcome sets.

    Outcome ``capability`` values are feature ids. Browser evidence can supplement
    pytest evidence, but only through the raw model/plan/inventory/run chain that
    ``flows.model.reconcile`` validates itself.
    """
    feature_model.validate(model)
    ok, reasons = feature_model.is_valid_configuration(model, selected)
    if not ok:
        raise ValueError("invalid configuration: " + "; ".join(reasons))
    feature_ids = {f["id"] for f in model["features"]}
    outcomes.validate(outcome_map, inventory)
    unknown_features = sorted(
        {row["capability"] for row in outcome_map["outcomes"]} - feature_ids
    )
    if unknown_features:
        raise ValueError(f"outcomes reference unknown feature ids: {unknown_features}")

    current = outcomes.provenance(root, outcome_map, inventory)
    if run is None:
        pytest_report = {
            "rows": [{**row, "status": "missing"} for row in outcome_map["outcomes"]],
            "run_errors": [], "complete": False,
        }
        native_reports = []
    else:
        pytest_report = outcomes.reconcile(outcome_map, inventory, run, current)
        native_reports = [{"source": "pytest", **pytest_report}]

    flow_report = None
    if flow_inputs is not None:
        fm, plan, raw_fi, fr = flow_inputs
        fi = flow_inventory(raw_fi)
        expected_context = {
            "environment": outcome_map["environment"],
            "limitations": outcome_map["limitations"],
        }
        if fm.get("evidence_context") != expected_context:
            raise ValueError("flow evidence context does not match the outcome map")
        if fr.get("outcome_input_provenance") != current:
            raise ValueError("flow run does not attest current outcome evidence inputs")
        flow_report = flow_model.reconcile(fi, fm, plan, fr)
        native_reports.append(
            {
                "source": "browser-flow",
                "model_sha256": digest(fm),
                "plan_sha256": digest(plan),
                "inventory_sha256": digest(fi),
                "run_sha256": digest(fr),
                "complete": flow_report["complete"],
            }
        )

    passed_flow_bindings: set[tuple[str, str]] = set()
    if flow_report is not None and fr.get("status") == "passed" and fr.get("execution_scope", "full") == "full":
        by_scenario = {row["id"]: row for row in fr.get("scenarios", [])}
        for scenario in plan.get("scenarios", []):
            actual = by_scenario.get(scenario["id"], {})
            if actual.get("status") != "passed":
                continue
            attested = set(actual.get("assertions", []))
            for index, step in enumerate(scenario["steps"]):
                for command in step["commands"]:
                    assertion = f"{index}:{step['transition']}:{command.get('id')}"
                    if command.get("op") == "assert" and assertion in attested:
                        passed_flow_bindings.add((step["transition"], command["id"]))
    evidence_rows = []
    known_bindings = {
        (step["transition"], command["id"])
        for scenario in (plan.get("scenarios", []) if flow_inputs is not None else [])
        for step in scenario["steps"]
        for command in step["commands"]
        if command.get("op") == "assert"
    }
    owned: dict[str, list[str]] = {fid: [] for fid in feature_ids}
    demonstrated: dict[str, list[str]] = {fid: [] for fid in feature_ids}
    for row in pytest_report["rows"]:
        fid = row["capability"]
        owned[fid].append(row["id"])
        bindings = row.get("flow_bindings", [])
        if bindings and (row.get("tests") or row["policy"] != "required"):
            raise ValueError(f"{row['id']}: flow bindings require a test-free required outcome")
        malformed = [binding for binding in bindings if
                     (binding.get("transition"), binding.get("assertion")) not in known_bindings]
        if malformed:
            raise ValueError(f"{row['id']}: unknown flow binding: {malformed}")
        flow_proven = bool(bindings) and all(
            (binding.get("transition"), binding.get("assertion")) in passed_flow_bindings
            for binding in bindings
        )
        status = "demonstrated" if row["status"] == "demonstrated" or flow_proven else row["status"]
        sources = (["pytest"] if row["status"] == "demonstrated" else []) + (
            ["browser-flow"] if flow_proven else []
        )
        if status == "demonstrated":
            demonstrated[fid].append(row["id"])
        evidence_rows.append(
            {
                "id": row["id"],
                "feature": fid,
                "source_refs": row["source_refs"],
                "flow_bindings": bindings,
                "status": status,
                "evidence_sources": sources,
            }
        )

    selected_parents = {
        f["parent"] for f in model["features"]
        if f["id"] in selected and f["id"] != model["root"]
    }
    obligations = {}
    missing_leaf_outcomes = []
    for fid in feature_ids:
        total = len(owned[fid])
        covered_count = len(demonstrated[fid])
        if fid in selected and fid not in selected_parents and total == 0:
            missing_leaf_outcomes.append(fid)
        obligations[fid] = {"covered": covered_count, "total": total}

    vector = coverage.rollup(model, obligations, selected)
    for row in vector["tree_rows"]:
        fid = row["feature"]
        row["own_outcome_ids"] = sorted(owned[fid])
        row["demonstrated_outcome_ids"] = sorted(demonstrated[fid])
        row["missing_required_outcomes"] = sorted(set(owned[fid]) - set(demonstrated[fid]))
        if fid in missing_leaf_outcomes:
            row["missing_required_outcomes"].append("<no-outcome-defined>")
        row["acceptance_status"] = (
            "missing"
            if row["covered"] == 0 and (row["total"] or row["missing_required_outcomes"])
            else "demonstrated"
            if row["covered"] == row["total"] and not row["missing_required_outcomes"]
            else "partial"
        )

    referenced = {ref for row in outcome_map["outcomes"] for ref in row["source_refs"]}
    discovered = {surface["id"] for surface in inventory.get("surfaces", [])}
    unknown_discovery = sorted(discovered - referenced)
    selected_rows = [r for r in vector["tree_rows"] if r["status"] in ("required", "selected")]
    behavioral_complete = (
        not (pytest_report.get("run_errors") or [])
        and not missing_leaf_outcomes
        and all(r["self_covered"] == r["self_total"] for r in selected_rows)
    )
    unresolved_discovery = [
        *inventory.get("unresolved", []),
        *((flow_report or {}).get("unresolved", [])),
    ]
    excluded_discovery = [
        inventory.get("excluded_surfaces", {"count": 0, "surfaces": []}),
        (flow_report or {}).get("excluded_surfaces", {"count": 0, "surfaces": []}),
    ]
    excluded_count = sum(item.get("count", len(item.get("surfaces", []))) for item in excluded_discovery)
    discovery_accounted = not unknown_discovery and not unresolved_discovery and excluded_count == 0
    return {
        "version": 1,
        "kind": "feature-evidence",
        "root": model["root"],
        "selected": sorted(selected),
        "context": {
            "environment": outcome_map["environment"],
            "limitations": outcome_map["limitations"],
            "feature_model_sha256": digest(model),
            "outcome_map_sha256": current["map_sha256"],
            "inventory_sha256": current["inventory_sha256"],
            "inputs_sha256": current["inputs_sha256"],
            "engine_sha256": current["engine_sha256"],
        },
        "native_evidence": native_reports,
        "evidence_rows": evidence_rows,
        "unknown_discovery": unknown_discovery,
        "unresolved_discovery": unresolved_discovery,
        "excluded_discovery": excluded_discovery,
        **vector,
        "behavioral_complete": behavioral_complete,
        "discovery_accounted": discovery_accounted,
        "complete": behavioral_complete and discovery_accounted,
    }
