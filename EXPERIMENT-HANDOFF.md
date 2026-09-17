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
| Stage D: typed model checker (2026-09-17) | `claims/modelcheck.py`, `shen/modelcheck/`, `capcov experiment claims modelcheck --model DIR --out DIR`, `tests/claim_semantics/test_modelcheck.py` | Shen's type checker decides well-formedness of the domain model: reified literals judged under `(tc +)` against one-datatype-per-file rules (writes, admissibility matrix, atlas, registry). Emits `model_well_formed.json` + certificate; `recheck` without a runtime. Real qualified model well-formed; the older model ill-formed on its declared write-set. Measured type-checker facts are at the top of `prelude.shen`; read them before touching the rules. Admitted-checker row is the reviewer's signature, not the checker's. |
| Replay judge (shen1 session) | `claims/replay/`, `experiments/claim-semantics/replay/`, `tests/claim_semantics/test_replay_*` | Receipt directory → strict bundle; rule pack with owned witnesses and contradiction detectors; reviewed corpus, certificates identical from both kernels. Schema `schema_replay_v1` is receipt-backed (real target-go receipt committed as a fixture); `op_qualified` on it is honestly `unresolved` until target-go declares its write set. Reviewer-owned model scope exclusions (`experiment/replay-claims-rewritten`, `6f003f6`): assumption-modality rows gated by their own closure; the pilot's `replay_join` summary names the exclusions applied and the undeclared writes that remain. Round two (`experiment/r2-judge`): assumption registry with invalidation, ordering / repeat-delete / stability claims, a compiled Soufflé checker gate with a three-kernel differential and a judge CLI (exit 5 = pending premise). The Stage D contract is live: `model_well_formed` + `model_checker_admitted` are positive premises of qualification, so the real qualified receipt honestly reads `unresolved`, `qualification: pending model_well_formed`, until the typed checker exists; the unqualified receipt is the negative path. A placeholder certificate that briefly filled that gate was removed before integration. The Shen domain model it consumes is a fact PRODUCER (below the IR); Stage D is the rule workbench (above it). |
| Ordering, cross-request and cross-run replay claims | `claims/replay/schema_replay_v1.json`, `experiments/claim-semantics/replay/`, `tests/claim_semantics/test_replay_*`, `.../test_target_go_replay_receipt.py` | Branch `experiment/r2-ordering`, capcov `932b8cd` (base `1e6656b`); candidate commit `d584f44a` -- the `go_commit` of run `eca6e7930af3`, the build that produced the committed receipt, not the candidate worktree head. Seven new observation relations (per-statement `php`/`go`/`model_effect_seq`, `replay_request_seq`, `php`/`go_response`, `replay_stability`) with their closures; ~25 rules add order refinement, the repeat-delete claim `repeat_delete_not_found(run, target)` and oracle stability. `op_qualified_rt` is gated on the order and on cross-run stability; the repeat delete is a claim of its own and **not** an op gate (a bad repeat reaches `op_qualified` through the model's admissible set). Reviewer scope exclusions apply to the repeat exactly as to `undeclared_write`, and `first_delete_committed` names the first delete of a (tenant, target). Corpus is 23 cases + 4 rejected, both kernels agreeing. Committed target-go fixture from run `eca6e7930af3` (17 relations, all seven closures true): `op_qualified(delete-issue)` supported under the four reviewer exclusions, order exercised and unviolated, oracle stable. That run is a three-request tape, so `repeat_delete` is empty on it.  A second committed fixture is the live four-request tape (run `271d2dde86a0`, candidate `7f2238a4`, oracle `9ff51ce5`, model `08380c9c`): owner 200, forbidden 403, missing 404, repeat 404, and on it `repeat_delete_not_found` is **supported against real rows** (the repeat wrote nothing at all on either side).  `op_qualified` there is honestly unresolved at `corpus_constrains`: the mutants were not re-baselined on that tape and the selftest did not run (`closed.mutant_kills` / `closed.replay_stability` false).  Re-baselining that tape is the open item. |
| Model well-formedness as a premise of qualification (Stage D admission point) | `claims/replay/schema_replay_v1.json`, `claims/replay/replay_facts.py`, `experiments/claim-semantics/replay/` (cases 27-29, rejected 30), `claims/replay/join.py`, `tests/claim_semantics/fixtures/replay_receipt_*` | `op_qualified_rt` now carries the **positive** atom `model_well_formed(M, Checker, Version, Cert)`, joined on the same `M` as `model_describes_run(M, Run)`, plus the reviewer-owned `model_checker_admitted(Checker, Version)`: the judge qualifies an op against a model only when a typed checker certified *that* model at a version the reviewer admits. New producer class **`modelcheck`** (evidence-id prefix `modelcheck`); `shen` and `reviewer` are **not** admitted for `model_well_formed`, so a model host cannot certify its own model (rejected case 30 is that refusal). The exporter reads `model_well_formed.json` (a row naming another model is **`stale`** with its own message, not `invalid-input`: the certificate is for another artifact) and the reviewer's `model_checkers.json`. **No closure relation** on either -- nothing negates well-formedness, so a receipt with no certificate is unresolved (case 27), never qualified by silence. Cases: 00 is the positive control (both rows are support leaves of every `op_qualified` proof), 27 no certificate, 28 a certificate for another model (claim-time: the exporter refuses such a row inside a receipt), 29 no admitted checker; both kernels agree on all 26 cases + 5 rejected. **Pack identity moved**: the pack is now **100 relations / 64 rules**, program digest `dfb0a33a5a9257324ab55ae7426a24d77ccdaa410b73cab281b9de996e99e095`, 100 outputs, 309 program lines -- these supersede the `98 relations / 64 rules` and `5043a715770e26e6…` of the round-2 merge note below, which are historical from here on; the compile key, binary sha256 and every wall-clock figure in the compiled row were **not** re-measured. **The certificate is a placeholder**: the committed fixtures carry checker `stage-d-typecheck`, version `0.1-pending`, certificate `sha256("pending: checker not yet built")` until the real Stage D checker emits one, so what is evidenced here is the *shape and authority* of the premise, not that any model has actually been typechecked. The `replay_receipt_target_go_repeat` fixture deliberately carries no certificate; its `op_qualified` still blocks at `corpus_constrains` (the well-formedness premise is checked after the corpus gate in `_BLOCKING_ORDER`), and the join summary reports `model_well_formed: missing` for it. |
| Cross-check vs. the production resolver | `tests/claim_semantics/test_static_crosscheck_fixpoint.py` | On the go_app fixture, Datalog `static_capability_op` equals `core/fixpoint.bind` with zero differences. |
| target-go static + optional runtime pilot | `claims/static/pilot.py`, `tests/claim_semantics/target_go/`, section 30 / 32 | Real route → SQL path derived in both kernels with certificates. Runtime join is skip-gated on `CAPCOV_TARGET_GO_RUNTIME_RECEIPT` + live checkout; fixture-backed correspondence lives in `test_runtime_join_fixture.py` and does **not** require the target-go tree. |
| Toolchain | `flake.nix` (pinned `scip` 0.9.0, `scip-go` 0.2.7, `souffle` 2.5, Go 1.27, Python 3.12), `tests/scip/canonicalize.jq`, `packages/capabilities/tests/fixtures/scip_go_app_index.json` | `nix flake check` includes a sandboxed scip-go index smoke. |
| Performance | section 31, `packages/capabilities/benchmarks/claims_evaluator_bench.py`, `capcov/cas.py` | Equijoin 1,000 rows 85 s → 0.13 s; 200-node closure 226 s → 0.72 s. `cas.py` has no caller yet. PR #49 (upstream) covers incremental source hashing. |
| Compiled Soufflé checker as a third kernel + the gate | `claims/souffle/{__init__,compile}.py`, `claims/differential.py` (`run_souffle_compiled`, `compare_three`, `ThreeWayResult`), `claims/replay/{pack,join}.py`, `scripts/compiled_checker.py`, `tests/claim_semantics/test_souffle_compile_unit.py`, `test_souffle_compiled_kernel.py`, `test_differential_three_kernels.py`, `test_compiled_checker_script.py` | `souffle.py` is now a package whose `_execute` (temp root, Popen/budget loop, output parse, claim fold) is shared by the interpreter and the compiled binary, so the two Soufflé kernels cannot drift. One `souffle --no-preprocessor -j1 -o` per pack, cached by sha256(schema, program digest, souffle executable sha256, flags, `souffle-compile.py` sha256 — the C++ toolchain the binary is actually built with) with a `provenance.json` the judge receipt embeds verbatim; `--version` is recorded but never keyed on (the pinned build prints an empty `Version:`). The cache directory is made absolute before the key is formed (a relative `--cache-dir`, which is every library default, produced an unrunnable `binary_path` and surfaced as a misnamed `kernel-mismatch`), an entry appears under its final name only once it is complete, and an unusable cache or an absent `souffle-compile.py` is exit 4 (environment), never a kernel verdict. There is no separate sorted pack digest: `pack_digest` **is** the `translate_bundle` program digest — the join, both receipt fixtures and all 14 replay cases share one — and a future combiner-order change fails closed as `compiled-program-mismatch`. One deliberate flag asymmetry, recorded in `compile_flags`: the binary is built `--no-preprocessor` while the interpreter runs with mcpp on, so the two kernels run the same program *text* and a macro collision would surface as an interpreter failure, never as a silent disagreement. With no `--require-op` the judge derives its verdict from every replayed op (over zero requirements it used to write a vacuous `supported`). All 28 reviewed cases (14 replay + 14 static) and both committed receipt fixtures agree in python / interpreted / compiled Soufflé — same relations, claims, canonical digest and closure digest — and the rejected cases fail the compiled kernel under the interpreter's own name (still non-admissible). **Measured on aarch64-darwin in the pinned devShell** (souffle 2.5 `/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5`, sha256 `5da8ab2cb6b74d68fb4e3d923492c45287b29de812c3f7c9e1751f8b5470851b`) **at capcov `ed53bcb`**: cold compile of the replay pack **59.6 s**, and on the qualified receipt **1x interpreter 0.33 s vs compiled 0.33 s median** (3 runs), **50x (3,663 fact rows) interpreter 2.10 s vs compiled 2.81 s median** (5 runs; the compiled runs span 1.93–3.98 s, so run-to-run variance is larger than the difference). No throughput win at either scale — the value of the item is a third independent evaluator with recorded provenance, not wall time. The design's pre-measured 51.7 s compile / 0.71 s interpreter / 1.07 s compiled at 1x were taken elsewhere and are **not** reproduced here; the figures above supersede them, as does the 115.3 s cold compile an earlier revision of this row reported on the same machine under load. Evidence, all from one gate run: capcov **`ed53bcb`** on `experiment/r2-compiled` (the branch head moves; this is the implementation commit the numbers were measured at, with the whole `tests/claim_semantics` suite green there — 456 tests, 28 pre-existing skips), candidate repo HEAD `15bfef43270022035f9f16cf814e5805791f1d95`, replay pack program digest `99ab0f1377e3d5e9675cb2346d9b18013e665f4ba4fd2531cad9deaea82cbb14`, compile key `d081fa19d61b084fdf3a77cd5679e889e02ccc1cf7cbac3ac5af874cbaf24296`, `souffle-compile.py` sha256 `e12c7ce76c45946d1b180a4bd1dbf8fc424e24ecbd50282919bba9ae5859a4fd`, judge.json sha256 `3e53dc9ddb57227febd98b4c9421f1972158a973fc5312813761eb060981cc9c` (`binary_sha256` `e5bb8c09a2c8d9db…` on that run; binary reproducibility is **not** claimed — provenance records the sha256 that actually ran, `375f554ec621…` from a second cache on the same machine). **The judged receipt is stale**: run `eca6e7930af3`, `go_commit d584f44a7b9d5e265ed826b3f44395b7bb667c09`, which is not the candidate HEAD above, so the gate ran only under the candidate Makefile's `ALLOW_STALE_RECEIPT=1`. The acceptance bullet `judge.json.receipt.go_commit == git rev-parse HEAD` after a fresh producer chain is therefore **not satisfied**; it stays open as U4b (Docker + the incumbent oracle). Limits: `compare_three` reuses the pairwise shrinker for python-vs-interpreter only, so a compiled-vs-interpreter disagreement is persisted **unshrunk** as `<replay_root>/compiled-<digest>.json`; `kernels.interpreter_seconds` / `python_seconds` are sums over every run of that kernel in the call (shrinker re-runs included), not one run; the cache is bounded to one souffle build but not to a number of entries. Acceptance: `nix develop --command bash -lc 'cd packages/capabilities && PYTHONPATH=$PWD/src python -m unittest discover -s tests/claim_semantics -t .'`; `python3 packages/capabilities/scripts/compiled_checker.py compile --pack replay --cache-dir /tmp/cc`; `… compiled_checker.py judge --receipt packages/capabilities/tests/claim_semantics/fixtures/replay_receipt_target_go_qualified --out /tmp/j --require-op delete-issue` → exit 0, `.verdict == "supported"`, `.kernels.matched == true` (the `_unqualified` fixture → exit 1, `not-supported`, missing premise `model_writes`); `… compiled_checker.py bench --receipt <qualified fixture> --scale 50 --out /tmp/b` → `closures_identical: true`. Set `CAPCOV_SOUFFLE_CACHE_DIR` to reuse a warm compile. |
| Pi workflow driver | `.pi/workflows/capcov-experiment.json`, `.pi/extensions/capcov-experiment.ts`, `.pi/workflows/README.md` | Optional orchestration with gates and two reviewers; `CAPCOV_AGENT_BACKEND=codex` supported. Not required; see "How work actually got done". |
| Assumption registry | `claims/assumptions.py`, `target_go/replay_join.py`, `test_assumption_registry.py`, `claims assumptions registry\|invalidate` | Run-independent ids (`asm:` + `sha256(canonical_json([producer_class, relation, row]))`), a registry of what each assumption carries (`assumptions.json` beside the join's `receipt.json`), and withdrawal: drop an assumption from the combined bundle, re-run both kernels, re-certify (`invalidation-<id12>.json`). No receipt or exporter contract change. A drop may only leave a claim `supported`/`unresolved`; `refuted` raises. Finding: the reviewer's scope exclusions guard `op_qualified` through a **negated** atom, so they are not leaves of it and `ground.impact` cannot predict that fall — `prediction_agrees` is `false` there, which is why re-evaluation exists. **Not delivered, do not read as done:** the candidate repo's `make replay-assumptions` target does not exist, and the live cross-run acceptance (a fresh replay run, exported and registered, with the ids compared across two real runs) is **NOT RUN / UNKNOWN** — cross-run id stability is evidenced only by `CrossRunIdStabilityTest`, an in-process re-export of a copied receipt whose run id is rewritten in place, which is a faithful stand-in for the per-run stamping the exporter does but is not live evidence. Fixture-backed evidence binds to capcov `30072a6` (66 tests green under Soufflé 2.5: 44 + 22), `assumptions.json` sha256 `7c1f9d049cba96d1407ba46be37cdf09ca2f963c2ddcc2dc92c4e599f49677cb`, combined bundle digest `bca7f43fca509191e2ff4228604ff570c8b65b118c2e604b0d6f880204b2eabc`. Four places where the code deviates from the design and the design is what should move: `missing_premise` is `[]` for the exclusion drop and `prediction_agrees` `false` (the `model_writes` template exists only where the baseline had offending rows); `ALLOWED_AFTER` admits `unresolved → supported`, with a separate `gained` list so a headline claim gaining support stays visible; an exclusion's `carried_by` / `shared_across` name only `exclusion_applied` (the negation finding above); and the unreferenced-drop case compares certificate `derivation` rather than `certificate_sha256`, because a certificate embeds its bundle digest. `reviewed_against.run` is stamped by the exporter out of the receipt, not signed by the reviewer. |
| Three judge gaps closed on `experiment/r2-judge` (critic round 3) | `claims/replay/{schema_replay_v1.json,replay_facts.py,join.py}`, `experiments/claim-semantics/replay/`, `scripts/compiled_checker.py`, `tests/claim_semantics/{test_replay_*,test_target_go_replay_receipt,test_compiled_checker_script,test_souffle_compile_unit}.py`, `tests/claim_semantics/fixtures/replay_receipt_target_go_qualified/learn/` | Three commits. **(1) `e2ef499` — the Stage D certificate was a placeholder on real receipts.** The three real receipt fixtures carried `model_well_formed.json` with checker `stage-d-typecheck 0.1-pending` and certificate `sha256("pending: checker not yet built")`, and a `model_checkers.json` admitting exactly that pair: a fabricated observation satisfying the very gate the premise imposes. Deleted; the reviewer's list is now empty on both real fixtures. Only the **synthetic** `replay_receipt_min` (run `run-fixture-1`, commits `php0000…`/`go0000…`), from which the labelled-synthetic corpus is generated, keeps a certificate, and it is what keeps the positive control alive (case 00, `FixtureJoinTest`, the CLI's exit-0 path). Consequence: `op_qualified` on the real qualified receipt is **unresolved with `model_well_formed` as its only missing premise**, reported as `qualification: "pending model_well_formed"` and **exit 5** (`EXIT_PENDING_PREMISE`) rather than exit 1, so a consumer gate can tell "the typed checker has not been built" from "this port is not qualified"; a real blocker still wins (the `_unqualified` fixture is exit 1 on `undeclared_any`). `replay.join.PENDING_PREMISES` sits last in `_BLOCKING_ORDER` and the Stage D pair last in `op_qualified_rt`'s body, so an op reported as pending is one where every other premise held. `test_assumption_registry` stages a **test-local synthetic** certificate into a temp copy and says why. **(2) `f073faa` — the cross-request claim is now load-bearing.** `repeat_delete_violation` was derived and read nowhere. Case 18 plants an `issue` update — a *declared* table — on the second DELETE of a committed target; every per-request premise held and the op qualified, so the receipt's only defect lived in a claim nothing read. `op_qualified_rt` now carries `repeat_delete_closed(Run,Op), !repeat_delete_any(Run,Op)`, joined on the *violating request's* op so one op's repeat does not poison the run; `repeat_delete_closed` gained `model_describes_run` + `model_scope_exclusions_closed` so it lists the closure of every positive input of the chain it negates. New case 31 opens `closed.php_responses`: every op unresolved on `php_responses_closed` while the positive per-target claim stays supported. Mutations: dropping the negation or the whole gate flips case 18 back to supported, dropping `php_responses_closed` flips case 31, and dropping `repeat_delete_closed` is refused at ingestion (`missing-completeness`). **(3) `cb015a4` — the learn receipt has a judge.** New primitives `learn_run(run, campaign, model, learn, php_commit, snapshot)`, `learn_prediction(run, model, learn, tape, req, op, predicted, state_digest)` [`shen`], `learn_observation(run, tape, req, op, observed, state_digest)` [`php`], `learn_unmodeled(model, learn, op)` [`shen`], closures `learn_predictions_closed(run, model)` [`shen`], `learn_observations_closed(run)` [`replay`], `learn_unmodeled_closed(model, learn)` [`shen`], and the compatibility row `learn_describes_model(learn, model)` [`shen`]; read from a `learn/` subdirectory whose header is `learn/learn_receipt.json`. Claim `learn_consistent(run, op)`: under both closures no tape position of the op has the model predicting a class the oracle did not produce (`learn_counterexample(run, tape, req, op, predicted, observed)` names the step; the reserved predicted class `"unknown"` is never a counterexample). `op_qualified_rt` is **downgraded** by `!learn_unmodeled_any(Run, Op)` under `learn_unmodeled_gate_closed`. **Read this limit:** every input of `learn_unmodeled_any` is positive (the campaign must be bound to the run and the model and must have closed its list), so a receipt with no `learn/` derives nothing and is judged exactly as before — **absence of a learn campaign is not evidence that the model covers every op**, and the gate can only take qualification away, never grant it. Fixture: `replay_receipt_target_go_qualified/learn/` is a **real** campaign against the same model (12 tapes, 20 predictions, 32 observations, 3 unmodelled ops, no counterexample), scrubbed — only the `run` column (rescoped to the replay run, the campaign's own id moved to `campaign`) and the `class` column name (`predicted` / `observed`) were rewritten. **Pack identity moves twice and lands at `9addbe396147` — 115 relations / 71 rules / 115 outputs / 354 program lines** (`dfb0a33a5a92` → `c0a28dec1448` after the Stage D reorder → `a47bbd118a4a` after the repeat gate → `9addbe396147`), superseding the `100 relations / 64 rules / dfb0a33a5a92` of the row above; corpus is 27 cases + 5 rejected. **Not re-measured:** the compile key, the binary sha256 and every wall-clock figure in the compiled row. **Open on the producer side:** the candidate repo's learn exporter writes `run` = the *campaign's* run id and a `class` column, and writes to `.work/replay/learn/receipt/`; to be read by this judge it must set `run` to the replay run (or omit it), move the campaign id to `campaign`, rename `class` to `predicted` / `observed`, and write the directory as `learn/` inside the replay receipt with a `learn_receipt.json` carrying `{version, learn, model?, closed}`. |


### What the round-2 merge moved (read before trusting a digest above)

The three round-2 items were cut from the same commit and merged in one
lineage (`experiment/r2-judge`): the assumption registry, then the ordering /
cross-request / cross-run claims, then the compiled Soufflé kernel.  The
ordering item adds relations and rules to `rules-replay-v1`, so **the replay
pack the compiled checker compiles is not the pack the compiled row's numbers
were measured against**.  Post-merge, on the merge head, the pack is **98
relations / 64 rules**, program digest
`5043a715770e26e6b0b3aa1495540630d0137b12a38f671564ee5e292a47b03d`, 98 outputs,
303 program lines; the compiled row's `99ab0f1377e3…`, 65 relations and 40
rules are that item's own evidence **at `ed53bcb`, before the merge**, and are
historical from here on.  The recorded pins in
`test_souffle_compile_unit.py` and `test_compiled_checker_script.py` were
refreshed to the merged pack in the merge commit; the compile key, binary
sha256 and the wall-clock figures in that row were **not** re-measured after
the merge and remain `ed53bcb` evidence.  Two other post-merge facts, both
from the merge head: `tests/claim_semantics` is **524 tests green, 28 skipped**
(the compiled row's 456/28 is pre-merge), and
`scripts/compiled_checker.py judge --receipt <qualified fixture> --require-op
delete-issue` exits **0** with `verdict "supported"`, `kernels.matched true`
and `closure_digest_equal true`.  Everything the compiled row says about the
judged receipt being **stale** (run `eca6e7930af3`) is unchanged by the merge:
U4b stays open.

Certification is now one function.  The compiled item widened certification to
every closure a result carries so the third kernel is held to the same
agreement; the assumption item had factored certification into
`assumptions.certify_claims`.  The merge kept the single certifier —
`certify_claims` derives its closures from the result (python, interpreted
Soufflé, and compiled when present) and names the disagreeing backend — so the
withdrawal path re-certifies against three kernels wherever three ran.  This is
a merge decision, not something either item tested: **no test yet withdraws an
assumption under `kernels="three"`.**

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
When other agents share the machine, wrap every heavy step (nix builds, indexers, full
snapshots, full suites) in `packages/capabilities/scripts/with-heavy-lock.py --label … --` (upstream
PR #51) and run them one at a time; the host kills background work when memory runs low.

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
