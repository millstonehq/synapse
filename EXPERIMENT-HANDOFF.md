# Handoff: capcov claim semantics, SCIP → Datalog, and the target-go static pilot

Written 2026-09-15 for the next agent. `EXPERIMENT-PLAN.md` is the authoritative,
running record (sections 26–31 cover the last two days); this file is the short map.

## What exists and where

| Piece | Path | State |
|---|---|---|
| Typed claims IR, validation, verdict algebra | `packages/capabilities/src/capcov/claims/{ir,validation,verdicts,output}.py` | Reviewed corpus of 14 cases passes; ingestion fails closed on malformed input (section 27). |
| Two independent Datalog kernels | `claims/evaluator.py` (Python, indexed, semi-naive, proof-carrying), `claims/souffle.py` (Soufflé 2.5 subprocess, bounded) | Differentially compared on every corpus and adversarial case; disagreements produce a minimized replay bundle (`claims/differential.py`, `claims/shrinker.py`). |
| SCIP → static facts | `claims/static/scip_facts.py` (exporter), `scip/runner.py` (`retain=True`), `claims/static/schema_static_v1.json` (frozen primitives) | Identity of a static bundle = sha256 of the exported relations (`static-relations-v1`); the index file digest is only a run receipt. |
| Static rule pack + adversarial static corpus | `packages/capabilities/experiments/claim-semantics/static/` | 22 derived relations, 27 rules, 13 reviewed cases; both kernels agree on all 30 claims. |
| Certificates | `claims/static/certificate.py` | Bounded backward chaining over either engine's rows; identical certificates from Python and Soufflé; `recheck` detects tampering. Ground checker with why/why-not (Stage C) is NOT done. |
| Cross-check vs. the production resolver | `tests/claim_semantics/test_static_crosscheck_fixpoint.py` | On the go_app fixture, Datalog `static_capability_op` equals `core/fixpoint.bind` with zero differences. |
| target-go static pilot | `claims/static/pilot.py`, `tests/claim_semantics/target_go/`, section 30 | Real route → SQL path derived in both kernels with certificates; see below. |
| Toolchain | `flake.nix` (pinned `scip` 0.9.0, `scip-go` 0.2.7, `souffle` 2.5, Go 1.27, Python 3.12), `tests/scip/canonicalize.jq`, `packages/capabilities/tests/fixtures/scip_go_app_index.json` | `nix flake check` includes a sandboxed scip-go index smoke. |
| Performance | section 31, `packages/capabilities/benchmarks/claims_evaluator_bench.py`, `capcov/cas.py` | Equijoin 1,000 rows 85 s → 0.13 s; 200-node closure 226 s → 0.72 s. `cas.py` has no caller yet. PR #49 (upstream) covers incremental source hashing. |
| Pi workflow driver | `.pi/workflows/capcov-experiment.json`, `.pi/extensions/capcov-experiment.ts`, `.pi/workflows/README.md` | Optional orchestration with gates and two reviewers; `CAPCOV_AGENT_BACKEND=codex` supported. Not required; see "How work actually got done". |

## The target-go pilot result (the first "for real" claim)

Target `/Users/dev/fg/target-go` at `7e339e0`, indexed from a `git archive HEAD` copy with pinned
scip-go. Route `GET /api/cloud/notification-unsubscribe/<action>-email` → `Runtime.recipientLinks`
→ `legacyissues.ChangeSubscription` → `database/sql.Tx.ExecContext`. Slice = import closure of
`internal/pilot` (9 packages, 54 documents, ~20.6k facts). Python and Soufflé agree; certificates
identical across engines; coverage 1,714/1,714 rooted edges, none unrooted on the route closure.
Negative control (route → `SendDueDigests`) is `unresolved`, never `refuted`, because no
call-graph completeness witness exists. The handler binding is a labelled assumption fact naming
the router file:line (target-go's `net/http` mux does not match the go_app tree-sitter route query).
No runtime join was made: there is no retained target-go receipt, and none was fabricated.

Reproduce (about 2–3 minutes, network needed once for Go modules):

```sh
cd packages/capabilities
CAPCOV_GO_FIXTURE_ROOT=/Users/dev/fg/target-go \
nix develop --no-update-lock-file --command bash -lc \
  'PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p "test_target_go_static*.py" -t .'
```

Set `CAPCOV_GO_CACHE_ROOT` to a persistent directory to avoid re-downloading modules per run.

## Two identity traps you will hit if you touch the exporter

1. scip-go emits symbols in Go map order: never hash `index.scip` bytes as identity.
2. Go's generated `_testmain.go` for every `<pkg>.test` package lives in `GOCACHE`, and scip-go
   spells its path relative to the project root, leaking the cache location. Out-of-tree
   documents are excluded from facts and recorded as receipts (commit `3630c84`).
   Verify identity pins from fresh `nix develop` shells, not warm caches.

## Known limits (recorded, not hidden)

- Soufflé computes relational closure only; claim folding, quantifiers, diagnostics, and
  missing-premise rendering are shared Python policy, so differential agreement is weak evidence
  for those. Engine-independent certificates exist for closure, not for that policy.
- Producer-class authority (`RelationDecl.producer_classes`) is declared but not enforced;
  generic rules may still project away non-context causal columns. Owner: `datalog-certificates`.
- Replay minimization is bounded (`max_steps=200`, `shrink_truncated` reported honestly).
- `scip_references_closed` is emitted only when a tree-sitter call-site census is available;
  tree-sitter is not in the devShell, so on target-go every negative claim stays `unresolved`.
- The experimental `capcov experiment claims validate|evaluate` CLI does not exist; the claims
  package is library + tests only. Production commands are untouched.
- Linux execution of the claim kernels is evaluation-only in the flake; all runs were aarch64-darwin.

## How work actually got done, and what to do next time

The Pi driver (gates + two reviewers per attempt) cost about an hour per round and needed
manual intervention roughly every other round (timeouts, a garbage-collected devShell, and
acceptance statements no implementer could satisfy). Twelve review rounds found real defects but
converged slowly. The SCIP → Datalog wave was then delivered by four subagents in isolated
worktrees, each given the manifest task's write set, acceptance, and exact gate commands, with
the integrator rerunning every gate before merging; that took under two hours for the whole wave.
Recommendation: keep the manifest as the checklist and gate source, use isolated worktrees and
independent gate reruns, and reserve the two-reviewer driver loop for trust-boundary code.

Operational notes: pin the devShell with a GC root before long runs
(`nix build --no-update-lock-file .#devShells.aarch64-darwin.default --out-link .capcov/devshell-gcroot`);
gate commands must use `PYTHONPATH="$PWD/src"` (absolute) because upstream tests spawn
`python -m capcov` from a temporary cwd; macOS has no `timeout`.

## Suggested next steps

1. Runtime join for the target-go pilot: capture a real receipt for the unsubscribe route (nonce,
   tenant, request id, SQL terminal state) and join it through `index_describes_run`; the
   evidence-policy test (`test_static_evidence_policy.py`) shows the shape on synthetic data.
2. `datalog-certificates`: ground checker + why/why-not, and enforce producer-class authority.
3. Decide whether the claims package goes to upstream `main` as an opt-in package PR.
4. Wire `capcov/cas.py` into a consumer or drop it; it currently has no caller.
