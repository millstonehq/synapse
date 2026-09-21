"""Export go_app static facts (rules-static-v1 + rules-static-closure-v1 closure, Python kernel)
as Souffle .facts, in two variants: clean census and one injected residue row.
Also prints core.fixpoint.bind for the agreement check."""
import json, sys, time
from pathlib import Path
PKG = Path(sys.argv[1]); OUT = Path(sys.argv[2])
sys.path.insert(0, str(PKG / "src")); sys.path.insert(0, str(PKG / "tests" / "claim_semantics"))
from static_rules import go_app
from static_rules.adapter import pack_bundle
from capcov.claims.evaluator import evaluate
from capcov.claims.static import closure, scip_facts
from capcov.scip import runner, resolve, map as scip_map
from capcov.core import fixpoint

RESIDUE = [{"file": "internal/service/service.go", "line": 12, "callee": "h.dispatch",
            "kind": "unresolved", "reason": "untyped receiver"}]
EXPORT = ["static_edge", "static_root", "static_route_handler", "static_op_owner", "static_site_owner",
          "static_entity", "static_unresolved_call_site", "call_graph_closed", "static_capability_op",
          "static_route_declared_surface", "static_index_current"]

def variant(name, residue):
    ast = go_app.ast_raw()
    ast["entities"].append({"name": "sessions", "symbol": "Session", "module": "", "file": "models/models.go", "line": 19})
    ast["scip_residue"] = [dict(r) for r in residue]
    raw = go_app.golden_raw()
    exported = scip_facts.export_bundle(go_app.normalized(raw), ast_raw=ast, source_root=go_app.GO_APP, language="go",
                                        index_digest=go_app.json_file_digest(raw), index_digest_kind=runner.INDEX_DIGEST_JSON)
    assert exported.status == scip_facts.STATUS_COMPLETE, exported.messages
    bundle = closure.attach(exported.bundle, ast, pack_bundle())
    # claim-time fact the pack needs for static_index_current: source_tree_observed
    decls = {d.name: d for d in bundle.relations}
    atom, ev = go_app.source_tree_fact(decls, dict(dict(exported.bundle.metadata)["tree"])["digest"])
    from dataclasses import replace
    bundle = replace(bundle, facts=(*bundle.facts, atom), evidence=(*bundle.evidence, ev))
    t0 = time.perf_counter(); report = evaluate(bundle); dt = time.perf_counter() - t0
    assert report.status.value == "complete", report.message
    rel = dict(report.relations)
    d = OUT / name; d.mkdir(parents=True, exist_ok=True)
    for r in EXPORT:
        rows = sorted(rel.get(r, ()))
        (d / f"{r}.facts").write_text("".join("\t".join(str(v) for v in row) + "\n" for row in rows))
        print(f"{name}: {r}: {len(rows)} rows")
    print(f"{name}: python kernel closure wall {dt:.3f}s; index={dict(bundle.metadata).get('index_digest','?')[:12]}")
    return rel

rel = variant("clean", [])
variant("residue", RESIDUE)
# fixpoint.bind on the same golden (the stdlib resolver path the crosscheck test uses)
normalized = go_app.normalized(); edges = scip_map.call_edges(normalized)
calls = resolve.calls_graph(edges, language="go"); ops = go_app.ast_raw()["op_sites"]; direct = {}
to_node = resolve.normalizer("go").symbol_to_node
for owner, op in zip(scip_map.site_owners(normalized, ops, line_base=1), ops):
    direct.setdefault(to_node(owner["owner"]), set()).add(op["entity"])
node_of = {s: n for _, s, n in rel["scip_symbol_node"]}
roots = sorted({node_of[h] for _, _, h in rel["static_route_handler"]})
per_root, history = fixpoint.bind(roots, calls, direct)
print("fixpoint.bind:", json.dumps(per_root), "history", history)
print("static_capability_op:", sorted((e, v) for _, _, e, v in rel["static_capability_op"]))
