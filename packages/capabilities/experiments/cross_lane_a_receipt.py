"""Cross the bridge: judge one REAL Lane A receipt directory with the observation pack.

Usage (from packages/capabilities, with ``src`` importable)::

    PYTHONPATH=src python experiments/cross_lane_a_receipt.py <receipt-dir> <out-dir>

Nothing here edits the engine or the receipt.  The script reports, verbatim:

1. what ``observation_facts.export_bundle`` said about the receipt directory;
2. the pure-Python kernel's verdict for ``observations_agree`` and the blocking
   premise (``join.blocking_premise``), read off the closure;
3. the two-kernel differential's outcome (``join.evaluate_join``) -- on a
   machine without ``souffle`` this is ``souffle-unavailable`` and the summary
   status is ``kernel-mismatch``, which is NOT kernel agreement and is not
   reported as such;
4. the judge's ``summary`` as printed, so the reader can see whether model
   conformance appears as an explicit ``unassessed`` row in the output;
5. a premise audit: every relation the ``observations_agree`` derivation
   transitively depends on in the observation pack, every leaf the certificate
   actually used, and the intersection of both with the replay pack's
   model-dependent relations (the premises ``op_qualified`` requires and this
   claim deliberately does not).

Local paths in the printed output are redacted to ``<receipt-dir>`` by the
judge's own ``exporter_messages``; this script prints only the directory's
basename itself.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from capcov.claims.evaluator import evaluate
from capcov.claims.differential import run_python
from capcov.claims.observation import join as observation_join
from capcov.claims.observation import observation_facts as facts
from capcov.claims.observation.pack import load_pack as load_observation_pack
from capcov.claims.replay.pack import load_pack as load_replay_pack
from capcov.claims.static.ground import why, why_not, shared_assumptions

MODEL_PATTERN = re.compile(r"model|mutant|checker|learn_unmodeled|php_|go_", re.IGNORECASE)


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def rule_index(pack: dict) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for rule in pack["rules"]:
        index.setdefault(rule["head"]["relation"], []).append(rule)
    return index


def transitive_body(index: dict[str, list[dict]], root: str) -> tuple[set[str], set[str]]:
    """(derived relations reached, primitive relations reached) under ``root``."""
    seen_derived: set[str] = set()
    primitives: set[str] = set()
    stack = [root]
    while stack:
        name = stack.pop()
        if name in seen_derived:
            continue
        if name not in index:
            primitives.add(name)
            continue
        seen_derived.add(name)
        for rule in index[name]:
            for item in rule["body"]:
                relation = item.get("relation")
                if relation is None:
                    continue  # a comparison, not an atom
                stack.append(relation)
    return seen_derived, primitives


def holds(relations: dict, name: str, run: str) -> bool:
    return any(r and r[0] == run for r in relations.get(name, ()))


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    receipt_dir = Path(argv[1])
    out_dir = Path(argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt = json.loads((receipt_dir / facts.RECEIPT_FILE).read_text(encoding="utf-8"))
    run = receipt["run"]["id"]

    # ------------------------------------------------------------------ 1. export
    section("1. EXPORTER: observation_facts.export_bundle")
    exported = facts.export_bundle(receipt_dir, run=run, allow_receipt_admissions=True)
    print("receipt dir:", receipt_dir.name)
    print("run:", run)
    print("status:", exported.status)
    print("messages:")
    for message in exported.messages:
        print("  -", message.replace(str(receipt_dir), "<receipt-dir>"))
    print("row counts:")
    for name, count in sorted(exported.counts.items()):
        print(f"  {name}: {count}")
    if exported.status != facts.STATUS_COMPLETE:
        print("\nRESULT: the exporter REFUSED the receipt; the bridge is not crossed.")
        return 1

    # ------------------------------------------------- 2. pure-Python kernel verdict
    section("2. JUDGE (pure-Python kernel): build(fixture=True) + evaluate")
    join = observation_join.build(receipt_dir, fixture=True)
    print("contract_findings:", join.contract_findings)
    if join.bundle is None:
        print("no bundle; not crossed")
        return 1
    report = evaluate(join.bundle)
    relations = dict(report.relations)
    print("python kernel status:", report.status.value, "| message:", report.message)
    agree = next(c for c in report.claims if c.claim.id == join.agree_claim)
    stable = next(c for c in report.claims if c.claim.id == join.stable_claim)
    print(f"{join.agree_claim}: semantic={agree.semantic.value} operational={agree.operational.value} "
          f"basis={agree.result.basis.value} missing_premises={list(agree.result.missing_premises)}")
    print(f"{join.stable_claim}: semantic={stable.semantic.value} operational={stable.operational.value}")
    blocking = observation_join.blocking_premise(relations, run)
    print("blocking_premise:", json.dumps(blocking))
    print("qualification:", observation_join.qualification(agree.semantic.value,
                                                            agree.operational.value, blocking))
    print("premise ledger for this run (in _BLOCKING_ORDER):")
    for name, is_blocker in observation_join._BLOCKING_ORDER:
        present = holds(relations, name, run)
        ok = (not present) if is_blocker else present
        kind = "must be ABSENT" if is_blocker else "must HOLD"
        print(f"  [{'ok' if ok else 'BLOCKS'}] {name:40s} {kind:15s} present={present}")
    print("observations_agree rows:", [list(r) for r in relations.get("observations_agree", ())])
    print("observation_masked_difference rows:",
          len([r for r in relations.get("observation_masked_difference", ()) if r[0] == run]))
    print("masked_difference_admitted rows:", len(relations.get("masked_difference_admitted", ())))
    print("observation_masked_unadmitted rows:",
          [list(r) for r in relations.get("observation_masked_unadmitted", ())])
    print("body_masked rows:", [list(r) for r in relations.get("body_masked", ())])
    print("observation_mask_undisclosed rows:",
          [list(r) for r in relations.get("observation_mask_undisclosed", ())])

    # ------------------------------------------- 2b. the same, without fixture mode
    section("2b. JUDGE without fixture mode (no tree, no nonce): fail-closed check")
    strict = observation_join.build(receipt_dir, fixture=False)
    print("contract_findings:")
    for finding in strict.contract_findings:
        print("  -", finding.replace(str(receipt_dir), "<receipt-dir>"))
    if strict.bundle is not None:
        strict_report = evaluate(strict.bundle)
        strict_relations = dict(strict_report.relations)
        strict_agree = next(c for c in strict_report.claims if c.claim.id == strict.agree_claim)
        print(f"{strict.agree_claim}: semantic={strict_agree.semantic.value} "
              f"operational={strict_agree.operational.value}")
        print("blocking_premise:",
              json.dumps(observation_join.blocking_premise(strict_relations, run)))

    # ---------------------------------------------- 3. two-kernel differential
    section("3. TWO-KERNEL DIFFERENTIAL: evaluate_join(kernels='two')")
    replay_root = out_dir / "differential"
    join = observation_join.evaluate_join(join, replay_root=str(replay_root), kernels="two")
    outcome = join.result if join.result is not None else join.mismatch
    print("join.result is None:", join.result is None)
    print("join.mismatch is None:", join.mismatch is None)
    print("python kernel: operational_failure =", outcome.python.operational_failure,
          "| message:", (outcome.python.message or "")[:200])
    print("souffle kernel: operational_failure =", outcome.souffle.operational_failure,
          "| message:", (outcome.souffle.message or "")[:200])
    print("matched:", outcome.matched)
    if join.mismatch is not None and outcome.souffle.operational_failure == "souffle-unavailable":
        print("VERDICT ON KERNEL AGREEMENT: UNAVAILABLE. The second kernel did not run, so no "
              "kernel-agreement claim is made here. The verdict above is single-kernel only.")

    # ------------------------------------------------------- 4. printed summary
    section("4. JUDGE SUMMARY (observation_join.summary) -- exactly as printed")
    summary = observation_join.summary(join)
    print(json.dumps(summary, indent=1, sort_keys=True))
    mc = [row for row in summary["unassessed"] if row["dimension"] == "model_conformance"]
    print()
    print("model_conformance row present in printed summary:", bool(mc))
    print("unassessed_source:", summary["unassessed_source"])
    if mc:
        print("model_conformance row:", json.dumps(mc[0]))
    print("model_conformance_unassessed holds in closure:",
          holds(relations, "model_conformance_unassessed", run))
    print("observation_unassessed_closed holds in closure:",
          holds(relations, "observation_unassessed_closed", run))

    # --------------------------------------------------------- 5. premise audit
    section("5. PREMISE AUDIT: what the derivation depends on, and what it does not")
    obs_pack = load_observation_pack()
    obs_index = rule_index(obs_pack)
    derived, primitives = transitive_body(obs_index, "observations_agree")
    print(f"observation pack: observations_agree transitively reaches {len(derived)} derived "
          f"and {len(primitives)} primitive relations")
    print("derived:", sorted(derived))
    print("primitives:", sorted(primitives))

    replay_pack = load_replay_pack()
    replay_index = rule_index(replay_pack)
    rq_derived, rq_primitives = transitive_body(replay_index, "op_qualified")
    model_derived = sorted(n for n in rq_derived if MODEL_PATTERN.search(n))
    model_primitives = sorted(n for n in rq_primitives if MODEL_PATTERN.search(n))
    print()
    print(f"replay pack: op_qualified transitively reaches {len(rq_derived)} derived and "
          f"{len(rq_primitives)} primitive relations")
    print("op_qualified model-dependent DERIVED premises (name-matched):", model_derived)
    print("op_qualified model-dependent PRIMITIVE premises (name-matched):", model_primitives)
    print()
    reached = derived | primitives
    print("intersection(observations_agree reach, op_qualified model-dependent):",
          sorted(reached & set(model_derived + model_primitives)))
    print("intersection(observations_agree reach, ALL op_qualified reach):",
          sorted(reached & (rq_derived | rq_primitives)))
    print("observations_agree reach relations matching the model pattern:",
          sorted(n for n in reached if MODEL_PATTERN.search(n)))
    print("bundle relations matching the model pattern with rows:",
          sorted(n for n, rows in relations.items() if MODEL_PATTERN.search(n) and rows))

    # the certificate's leaves: what the derivation ACTUALLY used
    target = (run, join.check, join.scenario_set, join.policy)
    if agree.semantic.value == "supported":
        explanation = why(join.bundle, relations, "observations_agree", target)
    else:
        explanation = why_not(join.bundle, relations, "observations_agree", target)
    print()
    print("explanation.holds:", explanation.get("holds"), "| truncated:", explanation.get("truncated"),
          "| reason:", explanation.get("reason"))
    leaves = explanation.get("leaves") or []
    print("certificate leaves used:", len(leaves))
    leaf_relations: dict[str, int] = {}
    for leaf in leaves:
        name = leaf.get("relation") if isinstance(leaf, dict) else str(leaf)
        leaf_relations[name] = leaf_relations.get(name, 0) + 1
    for name, count in sorted(leaf_relations.items()):
        flag = "  <-- MODEL PATTERN" if MODEL_PATTERN.search(name) else ""
        print(f"  {name}: {count}{flag}")
    if explanation.get("certificate"):
        print("shared assumptions (reviewer-admitted rows the derivation rests on):")
        for ident in shared_assumptions(join.bundle, explanation["certificate"]):
            print("  -", ident)
    walk = explanation.get("walk") or []
    print("walk nodes:", len(walk))
    (out_dir / "explanation.json").write_text(json.dumps(explanation, indent=1, sort_keys=True,
                                                          default=str), encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True),
                                          encoding="utf-8")
    print("written:", out_dir / "explanation.json", out_dir / "summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
