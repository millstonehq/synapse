# Handoff: capcov claim semantics, SCIP → Datalog, and the target-go static/runtime pilot

Written 2026-09-16. `EXPERIMENT-PLAN.md` is the authoritative running record
(sections 26–32); this file is the short map. Section 32 is the 2026-09-16
deepen (runtime join, Stage C why/why-not, producer-class authority).

## What exists and where

| Piece | Path | State |
|---|---|---|
| Typed claims IR, validation, verdict algebra | `packages/capabilities/src/capcov/claims/{ir,validation,verdicts,output}.py` | Reviewed corpus of 14 cases passes; ingestion fails closed on malformed input (section 27). |
| Two independent Datalog kernels | `claims/evaluator.py` (Python, indexed, semi-naive, proof-carrying), `claims/souffle.py` (Soufflé 2.5 subprocess, bounded) | Differentially compared on every corpus and adversarial case; disagreements produce a minimized replay bundle (`claims/differential.py`, `claims/shrinker.py`). |
| SCIP → static facts | `claims/static/scip_facts.py` (exporter), `scip/runner.py` (`retain=True`), `claims/static/schema_static_v1.json` (frozen primitives) | Identity of a static bundle = sha256 of the exported relations (`static-relations-v1`); the index file digest is only a run receipt. |
| Static rule pack + adversarial static corpus | `packages/capabilities/experiments/claim-semantics/static/` | 22 derived relations, 27 rules, 13 reviewed cases; both kernels agree on all 30 claims. |
| Certificates + Stage C why/why-not | `claims/static/certificate.py`, `claims/static/ground.py` | Bounded backward chaining over either engine's rows; identical certificates from Python and Soufflé; `recheck` detects tampering **and** unauthorized producer tokens on leaves. `why` / `why_not` / `impact` / `shared_assumptions` are engine-independent and never upgrade unresolved to refuted. |
| Retained runtime receipt path | `claims/static/runtime_receipt.py` | Loads schema `capcov-target-go-runtime-route/v2`; emits only `target-go-runtime-trace-v2` evidence; join rules `runtime_route_observed_on_index` and `runtime_route_reaches_sql_on_index`. Never synthesizes a fake target-go run. |
| Shen semantic workbench (Stage D) | `packages/capabilities/shen/{rule-authority,claim-workbench,certificate-output}.shen`, `claims/shen.py`, `claims/cli.py` (`capcov experiment claims shen authority\|evaluate\|why-not`) | shen-go `c12933d` driven through bifrost (`BIFROST_SHEN_GO`), hard per-call timeouts. Elaborates the rule pack, runs 8 per-rule + 2 pack-level authority checks, derives conclusions with bounded search, emits `capcov-static-certificate-v1` certificates that `recheck` accepts and that equal the Python extractor's in full on go_app; bounded why-not. Aggregation rules and non-linear recursion are refused as `unsupported-construct`. |
| Stage D, redefined (2026-09-16, not yet built) | plan section 18, decision record | Typed well-formedness of the Shen domain model: invariants as Shen typing rules, one signed `model_well_formed` fact the judge requires; the rule-pack walker is retired as Stage D's purpose. Architecture: Shen types define correctness, Soufflé derives (compiled checker as the production evaluator), Python keeps ingestion/validation/certificates and is an oracle only. Blocked on shen1's r2 worktrees landing. |
| Replay judge (shen1 session) | `claims/replay/`, `experiments/claim-semantics/replay/`, `tests/claim_semantics/test_replay_*` | Receipt directory → strict bundle; rule pack with owned witnesses and contradiction detectors; reviewed corpus, certificates identical from both kernels. Schema `schema_replay_v1` is receipt-backed (real target-go receipt committed as a fixture); `op_qualified` on it is honestly `unresolved` until target-go declares its write set. Reviewer-owned model scope exclusions (`experiment/replay-claims-rewritten`, `6f003f6`): assumption-modality rows gated by their own closure; the pilot's `replay_join` summary names the exclusions applied and the undeclared writes that remain. With the default (qualified) fixture `op_qualified(delete-issue)` is supported under four reviewer exclusions; the unqualified receipt is kept as the negative path. The Shen domain model it consumes is a fact PRODUCER (below the IR); Stage D is the rule workbench (above it). |
| Cross-check vs. the production resolver | `tests/claim_semantics/test_static_crosscheck_fixpoint.py` | On the go_app fixture, Datalog `static_capability_op` equals `core/fixpoint.bind` with zero differences. |
| target-go static + optional runtime pilot | `claims/static/pilot.py`, `tests/claim_semantics/target_go/`, section 30 / 32 | Real route → SQL path derived in both kernels with certificates. Runtime join is skip-gated on `CAPCOV_TARGET_GO_RUNTIME_RECEIPT` + live checkout; fixture-backed correspondence lives in `test_runtime_join_fixture.py` and does **not** require the target-go tree. |
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

A retained runtime receipt (schema v2, producer `target-go-runtime-trace-v2`) joins the run to the
index through `index_describes_run` when `CAPCOV_TARGET_GO_RUNTIME_RECEIPT` is set and the receipt's
`candidate_commit` matches the indexed HEAD. Both kernels then derive
`runtime_route_reaches_sql_on_index` only when run/request/transaction/surface/index witnesses
agree. The static certificate (handler → `Tx.ExecContext`) and the runtime certificate (receipt
leaves + `index_describes_run`) are complementary; they are not one end-to-end proof.

Reproduce the live pilot (about 2–3 minutes, network needed once for Go modules):

```sh
cd packages/capabilities
CAPCOV_GO_FIXTURE_ROOT=<checkout at the receipt's candidate commit> \
CAPCOV_TARGET_GO_RUNTIME_RECEIPT="$PWD/tests/claim_semantics/target_go/artifacts/runtime-recipient-route.json" \
nix develop --no-update-lock-file --command bash -lc \
  'PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p "test_target_go_static*.py" -t .'
```

The committed receipt was produced at target-go `01fe913`. Binding it to a different HEAD fails
closed (commit mismatch). Use a checkout at `01fe913`; the target's main HEAD is not.
The replay judge's join (recorded under `replay_join` in the pilot receipt) runs by default
against the committed receipt `tests/claim_semantics/fixtures/replay_receipt_target_go_5988859/`;
`CAPCOV_REPLAY_RECEIPT_DIR` overrides it. Set `CAPCOV_GO_CACHE_ROOT` to a persistent directory to avoid
re-downloading modules per run.

Reproduce the fixture-backed correspondence (no target-go tree, no scip-go):

```sh
cd packages/capabilities
PYTHONPATH="$PWD/src" python -m unittest \
  tests.claim_semantics.test_runtime_join_fixture \
  tests.claim_semantics.test_runtime_producer_authority \
  tests.claim_semantics.test_ground_certificate
```

Dual-kernel agreement on the fixture join skips unless `souffle` is on PATH (nix devShell).

## Publication rules

The public history was rewritten on 2026-09-16 (no company, host, module path, ticket prefix or
target name). Keep it that way: the pilot reads the module path from the checkout's `go.mod` and
names no real path; committed pilot artifacts are redacted copies whose digests are of the real
run (see the `redaction` block in `tests/claim_semantics/target_go/artifacts/receipt.json`); the
retained runtime receipt's symbol strings are neutral and the join never uses them.

## Repositories

`origin` = millstonehq/synapse (production `main`, PR #50 targets it). `pyrex41/synapse-capcov` is
GitHub's registered fork and the PR head repo; other agents push to its `experiment/claim-semantics`.
`pyrex41/synapse` is a separate repo whose `main` mirrors the experiment head. Push to both.

Open PRs to know about (2026-09-16): upstream #50 (this line → `main`); fork `synapse-capcov`
#1 (same branch → fork `main`, stale body), #2 (perf, superseded by upstream #49), #3 (a Cursor
agent's deepen branch targeting this line; see the plan's section 26 for its disposition).

## Two identity traps you will hit if you touch the exporter

0. The identity hashes the *declared relation names* as well as the rows. Adding a stub
   declaration to the exporter moves every identity while leaving every row unchanged; re-pin
   with the cause recorded (section 26, 2026-09-16), do not widen the pin.

1. scip-go emits symbols in Go map order: never hash `index.scip` bytes as identity.
2. Go's generated `_testmain.go` for every `<pkg>.test` package lives in `GOCACHE`, and scip-go
   spells its path relative to the project root, leaking the cache location. Out-of-tree
   documents are excluded from facts and recorded as receipts (commit `3630c84`).
   Verify identity pins from fresh `nix develop` shells, not warm caches.

## Known limits (recorded, not hidden)

- Soufflé computes relational closure only; claim folding, quantifiers, diagnostics, and
  missing-premise rendering are shared Python policy, so differential agreement is weak evidence
  for those. Engine-independent certificates exist for closure; why/why-not is also
  engine-independent but is not a second claim-folding implementation.
- Producer-class authority (`RelationDecl.producer_classes`) is enforced at evidence
  ingestion (`evidence-producer` in `claims/validation.py`: the first token of
  `Evidence.source` must be one of the relation's declared classes; an empty tuple is
  unconstrained, so the frozen static schema is unaffected) and again by `recheck` on
  certificate leaves. The causal-trace primitives admit only `target-go-runtime-trace-v2`.
  `runtime_route_observed` stays unconstrained (go_app probe + target-go receipt both write it).
- Replay minimization is bounded (`max_steps=200`, `shrink_truncated` reported honestly).
- `scip_references_closed` is emitted only when a tree-sitter call-site census is available;
  tree-sitter is not in the devShell, so on target-go every negative claim stays `unresolved`.
- The experimental CLI exists only for the Shen workbench (`capcov experiment claims shen …`);
  `validate|evaluate` for the kernels is still library-only. Production commands and
  `core/reconcile.py` are untouched.
- Linux execution of the claim kernels is evaluation-only in the flake; most recorded runs
  were aarch64-darwin. The 2026-09-16 deepen (PR #3) ran on Linux without nix/Soufflé; its
  Soufflé-dependent tests and the live pilot were then rerun here in the pinned devShell
  (plan, end of file).

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

1. Done on this line: the target-go runtime join (route trace receipt, `5c22a89`), producer-class
   authority at ingestion and on certificate leaves, Stage C why/why-not over static
   certificates (`ground.py`, PR #3) and in Shen (Stage D), the replay judge's real-receipt
   join (`replay_join`), and the Soufflé reruns PR #3 could not do.
2. Apply the ground why/why-not to replay certificates and to the target-go pilot's runtime
   certificate; the replay judge's real receipt is `unresolved` on `op_qualified` until target-go
   declares its write set (`model_writes`), which is an target-go task, not a kernel task.
3. Decide whether the claims package goes to upstream `main` as an opt-in package PR.
4. Wire `capcov/cas.py` into a consumer or drop it; it currently has no caller.
5. Stage D Shen workbench remains open; Python still owns ingestion, IR validation, claim
   folding, and certificate construction. Soufflé is not the sole evaluator.
