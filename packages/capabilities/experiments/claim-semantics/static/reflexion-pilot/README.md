# Reflexion pilot over capcov's static facts (go_app)

A throwaway experiment, not a rule pack: does a Murphy/Notkin/Sullivan reflexion
model over the facts `rules-static-v1` + `rules-static-closure-v1` already derive
give `static_bind`, `convergence`/`divergence`/`absence`, `dead` and `blocked`
before any runner starts?  Yes, on the go_app fixture, in 33 lines of Soufflé.

* `export_facts.py PKG OUT` — Python kernel closure of the go_app bundle with the
  closure fragment attached (`closure.attach`), dumped as `.facts`, in two
  variants: `clean` (empty residue, `call_graph_closed(*)` present) and `residue`
  (one unresolved site in `Service.Fetch`, witness withheld).  Also prints
  `core.fixpoint.bind` for the same golden.
* `reflexion.dl` — `reaches`, `static_bind`, the three reflexion rules over a
  hand-authored `maps`/`high_edge` (in `facts/`), `unresolved_on`, `dead`, `blocked`.
* `expected/{clean,residue}` — the Soufflé outputs recorded on 2026-09-21.

Run:

    python3 export_facts.py <packages/capabilities> facts
    cp facts/maps.facts facts/high_edge.facts facts/clean/; cp facts/maps.facts facts/high_edge.facts facts/residue/
    souffle -F facts/clean -D out/clean reflexion.dl; souffle -F facts/residue -D out/residue reflexion.dl

Findings: `static_bind` = `static_capability_op` = `fixpoint.bind`
(`{jobs:read, audit_logs:create}`) in both variants; the residue variant turns
`absence(jobs_api,metrics)` into `absence_unresolved` and `dead(sessions)` into
`blocked(sessions via Service#Fetch)`.  The rules here gate every negation on
`call_graph_closed`; a production pack must additionally attribute `maps` and
`high_edge` to a reviewer producer class and put them behind their own closure.

**Landed.**  `rules-static-reflexion-v1` (`src/capcov/claims/static/reflexion.py`)
is that production pack: the same rows, with `maps`/`high_edge` as
`capability_map`/`capability_edge` under producer class `reviewer`, a closure
witness each, and `capability_map_describes_index` binding the model document to
the index.  `facts/{maps,high_edge}.facts` are kept as the experiment's record;
`capability-map.json` / `capability-edges.json` are the same model as documents
the profile reads:

    capcov experiment claims static --static scip --target tests/fixtures/go_app \
        --capability-map experiments/claim-semantics/static/reflexion-pilot/capability-map.json \
        --capability-edges experiments/claim-semantics/static/reflexion-pilot/capability-edges.json \
        --out bundle.json

`tests/claim_semantics/test_static_reflexion.py` pins the derived rows to the
`expected/` tables above, in both kernels.
