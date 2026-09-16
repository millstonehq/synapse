# Replay rule pack and adversarial replay cases (Phase 4, judge side)

This directory holds the reviewed program that turns one replay receipt --
the PHP system, the Go system and the Shen model replaying the same recorded
requests under one nonce and one snapshot, plus the mutation tool's verdicts
-- into the claim `op_qualified(index, run, op)`: *the op declared by the PHP
census is qualified by this replay*.  The replay harness is a producer of
observations, never an oracle; the judge is these rules.

* `rules-replay-v1.json` - the rule pack in raw IR JSON wire form.
* `cases/NN-*.json` - one positive control (`00`) and seven adversarial
  shapes; `rejected/07-producer-class-violation.json` is the case the
  ingestion boundary must refuse.
* `expected.json` / `rejected.json` - the per-claim review tables duplicated
  from every case, and what the rejected case would have yielded.

The adapter `tests/claim_semantics/replay_rules/adapter.py` mirrors the static
one (`load_pack, pack_relations, bundle_payload, load_case, pack_bundle`); the
case format is the static format, so `expected.json` tooling is shared.  The
case *facts* are not hand-written: `tests/claim_semantics/replay_rules/cases.py`
builds every case by running `replay_facts.export_bundle` over a small edit of
`tests/claim_semantics/fixtures/replay_receipt_min` and adding the claim-time
reviewer/census rows; `test_replay_corpus_schema` regenerates each file and
requires it to be identical up to `expected`, so the cases cannot drift from
the exporter.  Claims, diagnostics, output templates and the reviewer's verdict
table (`cases.REVIEW`) are hand-authored; `python -m replay_rules.cases` refuses
to write a case whose evaluator verdict, status, missing premises or
discrepancies differ from that table.

Tests: `test_replay_corpus_schema.py` (evaluator independent),
`test_replay_corpus_evaluation.py` (Python reference evaluator and the
Python/Soufflé differential), `test_replay_adversarial_both_engines.py`
(never skips; certificates from both closures) and
`test_replay_evidence_policy.py` (why-not: the absent leaf is named, adding it
flips the claim).

## The rule pack

`primitives` is a byte-identical copy of
`src/capcov/claims/replay/schema_replay_v1.json` (`relations`).
`supplementary_primitives` is empty: the frozen file declares everything the
judge reads, including the reviewer's claim-time witnesses
(`run_nonce_observed`, `snapshot_observed`, `model_observed`), the PHP census
(`op_declared`, static binding) and the two compatibility relations
(`model_describes_run`, `index_describes_replay`).  `derived` opens with the
two rule-less stubs the exporter carries (`mutant_killed_in`,
`op_qualified_rt`), byte-identical to `replay_facts._DERIVED_TARGET_DECLS` --
`combine` refuses a non-identical duplicate -- and then declares the reviewed
program.  Every derived relation is `binding=runtime` with context `run`,
except `op_qualified_rt` / `op_qualified` (context `index, run`).  The only
claim-modality relation is `op_qualified`.  Derived completeness relations
(precedent: the static `static_route_authorized_closed`): `requested_closed`,
`op_surviving_closed`, `php_disagreement_closed`, `go_disagreement_closed`,
`undeclared_writes_closed`.

Rules, in Datalog shorthand (`M` the model, `IX` the census index):

```text
mutant_killed_in(Run,Mu)        :- mutant_killed(Run,Mu,_).
replay_run_current(Run)         :- replay_run(Run,Nonce,_,_,Snap,Model), run_nonce_observed(Run,Nonce),
                                   snapshot_observed(Snap), model_observed(Model).
replay_run_stale(Run,Nonce,Obs) :- replay_run(Run,Nonce,_,_,_,_), run_nonce_observed(Run,Obs), Nonce != Obs.
requested(Run,Req)              :- replay_request(Run,Req,_,_,_).
requested_closed(Run)           :- replay_requests_closed(Run).
replayed(Run,Op)                :- replay_request(Run,_,_,_,Op).
php_model_agree(Run,Req)        :- php_post_state(Run,Req,S), model_describes_run(M,Run), model_admissible(Run,M,Req,S).
php_model_disagree(Run,Req,S)   :- php_post_state(Run,Req,S), model_describes_run(M,Run),
                                   model_admissible_closed(Run,M), !model_admissible(Run,M,Req,S).
go_model_agree / go_model_disagree: the same over go_post_state.
op_exercised(Run,Op)            :- replay_request(Run,Req,_,_,Op), php_model_agree(Run,Req), go_model_agree(Run,Req).
php_observed(Run,Req)           :- php_post_state(Run,Req,_).         go_observed: the same over go_post_state.
php_observed_closed(Run)        :- php_post_states_closed(Run).        go_observed_closed: from go_post_states_closed.
post_state_gap(Run,Req,"php")   :- requested(Run,Req), replay_requests_closed(Run), php_observed_closed(Run),
                                   !php_observed(Run,Req).             post_state_gap(Run,Req,"go"): the same.
post_state_any(Run,Op)          :- replay_request(Run,Req,_,_,Op), post_state_gap(Run,Req,_).
post_state_gap_closed(Run,Op)   :- replayed(Run,Op), replay_requests_closed(Run), php_post_states_closed(Run),
                                   go_post_states_closed(Run).
undeclared_write(Run,Op,Tb)     :- replay_request(Run,Req,_,_,Op), php_effect(Run,Req,Tb,_,_,_), model_describes_run(M,Run),
                                   model_writes_closed(M,Op), !model_writes(M,Op,Tb).
undeclared_write(Run,Op,Tb)     :- ... the same over go_effect.
surviving_mutant(Run,Op,Mu)     :- model_describes_run(M,Run), mutant(M,Mu,Op), mutants_closed(M,Op),
                                   mutant_kills_closed(Run), !mutant_killed_in(Run,Mu).
op_has_surviving_mutant(Run,Op) :- surviving_mutant(Run,Op,_).
op_surviving_closed(Run,Op)     :- model_describes_run(M,Run), mutants_closed(M,Op), mutant_kills_closed(Run).
corpus_constrains(Run,Op)       :- model_describes_run(M,Run), mutant(M,_,Op), op_surviving_closed(Run,Op),
                                   !op_has_surviving_mutant(Run,Op).
kill_closure_gap(Run,Mu,Req)    :- mutant_killed(Run,Mu,Req), mutant_kills_closed(Run), requested_closed(Run),
                                   !requested(Run,Req).
php_disagree_any(Run,Op)        :- replay_request(Run,Req,_,_,Op), php_model_disagree(Run,Req,_).
go_disagree_any(Run,Op)         :- replay_request(Run,Req,_,_,Op), go_model_disagree(Run,Req,_).
undeclared_any(Run,Op)          :- undeclared_write(Run,Op,_).
php_disagreement_closed(Run,Op) :- replayed(Run,Op), replay_run_current(Run), model_describes_run(M,Run),
                                   replay_requests_closed(Run), php_post_states_closed(Run),
                                   model_admissible_closed(Run,M).
go_disagreement_closed(Run,Op)  :- the same body with go_post_states_closed(Run).
undeclared_writes_closed(Run,Op):- replayed(Run,Op), replay_run_current(Run), model_describes_run(M,Run),
                                   replay_requests_closed(Run), php_effects_closed(Run), go_effects_closed(Run),
                                   model_writes_closed(M,Op).
op_qualified_rt(IX,Run,Op)      :- index_describes_replay(IX,Run), replayed(Run,Op), op_exercised(Run,Op),
                                   corpus_constrains(Run,Op),
                                   php_disagreement_closed(Run,Op), !php_disagree_any(Run,Op),
                                   go_disagreement_closed(Run,Op),  !go_disagree_any(Run,Op),
                                   undeclared_writes_closed(Run,Op), !undeclared_any(Run,Op),
                                   post_state_gap_closed(Run,Op), !post_state_any(Run,Op).
op_qualified(IX,Run,Op)         :- op_declared(IX,Op), index_describes_replay(IX,Run), op_qualified_rt(IX,Run,Op).
```

Design points a reviewer should check:

* **Every model/run join carries `model_describes_run(M, Run)`.**  The
  `model` and `run` context columns have different names, so the validator's
  cross-context check does not force this; the pack lint in
  `test_replay_corpus_schema` does, for every rule that reads a model-context
  relation and a run-context relation.  Without the witness no `php_model_*`,
  `go_model_*`, `undeclared_write`, `surviving_mutant` or closure row exists
  (case 04).
* **Negation only through named completeness.**  `!model_admissible` needs
  `model_admissible_closed(Run, M)`, `!model_writes` needs
  `model_writes_closed(M, Op)`, `!mutant_killed_in` needs
  `mutant_kills_closed(Run)`, `!requested` needs `requested_closed(Run)`, and
  the three per-op "any" relations are negated only under their derived
  closures, whose bodies list the closure of *every* positive input --
  `replay_run_current`, `model_describes_run`, `replay_requests_closed`,
  `model_admissible_closed` and, for the write check, `php_effects_closed`,
  `go_effects_closed`, `model_writes_closed(M, Op)`.  A run that is not current
  (missing witness, case 05; nonce mismatch, case 06) therefore has no closure
  and cannot qualify anything.
* **`corpus_constrains` needs at least one declared mutant** for the op
  (positive `mutant(M, _, Op)`) and the closed absence of survivors:
  `op_surviving_closed` is the derived completeness of
  `op_has_surviving_mutant`.  An op with no mutants is never constrained.
* **The static join is isolated in the final rule.**  `op_qualified_rt` is
  runtime-only (it reads `index_describes_replay` only to carry the index);
  `op_qualified` is the one rule that reads a static relation
  (`op_declared`) and it carries `index_describes_replay(IX, Run)`, whose
  `compatibility_targets` name both `op_declared` and `op_qualified_rt`.
  `test_replay_evidence_policy` shows that the same join without the witness
  is rejected with `mixed-binding-join`.
* **`op_exercised`** is not in the section's original list.  Every PHP/Go/Shen
  observation enters `op_qualified_rt` only through negated atoms, which
  contribute no support leaf; requiring at least one replayed request of the
  op whose PHP and Go post-states the model admits closes that vacuity (an op
  with zero agreeing requests is not qualified by "no disagreement") and is
  what makes the control's support leaves span the `php`, `go` and `shen`
  producer classes.  `replayed` is kept as the spec writes it; `op_exercised`
  implies it.
* **Post-state completeness** (schema addition, pre-consumer):
  `php_post_states_closed(run)` / `go_post_states_closed(run)` complete the
  post-state relations (`receipt.json` `closed.php_post_states` /
  `closed.go_post_states`).  Without them a replayed request whose post-state
  the runner omitted was invisible to `php_disagree_any` while the
  disagreement closure still held, so one agreeing request could satisfy
  `op_exercised` and every other request's disagreement could be hidden by
  omission.  Both disagreement closures now require the witness, and
  `op_qualified_rt` is gated on `!post_state_any(Run, Op)` under
  `post_state_gap_closed`, where `post_state_gap(Run, Req, side)` is a
  replayed request with no post-state on that side (case 09; the mutation
  tests in `test_replay_corpus_evaluation` show that dropping the gate flips
  the case).
* **`kill_closure_gap`** (case 08) is the replay analogue of the static
  `02-lying-witness` gap: a kill that names a request outside the closed
  request set while `mutant_kills_closed` is asserted.  It is derived *from*
  the lying witness, so its support intersects `forbidden_leaves`.

## One observation per key

The exporter, not the pack, settles duplicate observations: two `php_effect`
/ `go_effect` / `model_effect` rows sharing `(run, [model,] req, table, kind,
pk)` with different `cols_digest`, or two `php_post_state` / `go_post_state`
rows for one `(run, req)` with different `state_digest`, are contradictory
reports of the same event and make `export_bundle` return `invalid-input`
naming the key (`replay_facts.UNIQUE_KEYS`).  A pack-side uniqueness
completeness was rejected because it would let both rows into the fact set
and leave a rule to choose between them; the judge never carries a
contradiction it could have refused at ingestion.  A row repeated verbatim is
one fact, and `model_admissible` stays a set (several admissible states per
request).

## Validator findings

None.  The pack validates alone with zero issues (`pack_bundle`), every case
ingests with `validate=True`, and `combine(export_bundle(...), pack_bundle())`
accepts the exporter's stubs.  No rule needed restructuring for
`missing-completeness`, `unsafe-negation`, `mixed-binding-join`,
`missing-compatibility` or `recursive-negation`; the pack has no recursion at
all.

## How a reviewer decides a case

As for the static pack: `facts` are the only inputs (there are no
assumptions), `claims` name the rows in question, `review_notes` say why the
table holds, `expected.claims` is the table.  `supported` means one ground
instantiation exists and `support_leaves` is the evidence of the canonical
proof (shortest, then lexically least: for `issues.create`, replayed by
`req-1` and `req-3`, the proof uses `req-1`).  Negated atoms and the witnesses
that license them contribute the witness row, never the absent row.
`unresolved` means no instantiation exists and `missing_premises` names the
absent leaf.

### Why-not templates

Each `op_qualified` claim carries `missing_premise` templates
(`when_claim: "unresolved"`).  A template whose satisfying witness is present
in the case names that row in `excludes_evidence` and is therefore suppressed;
a template for an absent witness has nothing to exclude and fires.  The
witness rows are made relevant to the claim by per-claim `observation`
diagnostics (`model_describes_run`, `run_nonce_observed`, `snapshot_observed`,
`model_observed`), exactly as the static lying-witness case makes its trigger
rows relevant.  Planted blockers (cases 01-03) name the *agreement* that is
missing (`php_model_agree`, `model_writes`, `mutant_killed`) and are triggered
by the row that blocks (`requires_all_evidence`).  The result is that an
unresolved `op_qualified` renders exactly one missing premise per case.

`operational_status` is `complete` unless a claim declares a diagnostic with
another status whose trigger rows exist: `stale` on `replay_run_stale` (case
06).  `discrepancies` are `discrepancy` templates on the companion claims
whose `requires_all_evidence` rows exist.  `forbidden_leaves` names evidence a
derivation must not use (the lying `mutant_kills_closed` witness of case 08);
`observed_leaves` is every input relevant to the claim.

### Evidence ids and provenance

Exported rows: `<prefix>:<replay12>:<relation>:<row12>` exactly as
`replay_facts` emits them (`prefix` from the relation's producer class:
`replay`, `php`, `go`, `shen`, `mut`, `reviewer`; `php-census` shares `php`;
witnesses and compatibility rows use `replay`; `replay12` is the
`replay-relations-v1` identity of the case's receipt variant; `row12 =
sha256(canonical_json([relation, row]))[:12]`).  Claim-time rows the judge
adds -- the reviewer's three witnesses and the census -- use
`<prefix>:claim-time:<relation>:<row12>`, mirroring the static
`static:claim-time:...` convention.  `Evidence.source` is the producer string
and its first token is the producer class the validator checks
(`evidence-producer`).  All digests in the cases are synthetic; a live join
must take the model digest from the model's own digest script, never from a
constant in a case.

## Case table

| case | seeded edit of the fixture receipt | reviewed expectation |
|---|---|---|
| 00 positive control | none; reviewer observed nonce, snapshot, model; census declares both ops | `op_qualified` supported/complete for both ops; leaves span `replay, php, go, shen, mut, reviewer, php-census` |
| 01 planted disagreement | `php_post_state` of req-2 outside the admissible set | close: unresolved, missing `php_model_agree`; create: supported; companion `php_model_disagree` supported, discrepancy `php-state-outside-model` |
| 02 planted undeclared write | `go_effect` insert into `audit_log` for req-2 | close: unresolved, missing `model_writes`; companion `undeclared_write` supported, discrepancy `undeclared-table` |
| 03 surviving mutant | `mutant_killed` row for m-2 removed | close: unresolved, missing `mutant_killed`; companion `surviving_mutant` supported, discrepancy `mutant-not-killed` |
| 04 missing model witness | exported `model_describes_run` withheld | both unresolved, missing `model_describes_run`; no `php_model_*`/`go_model_*` rows; companion `php_model_agree` unresolved |
| 05 missing snapshot witness | no `snapshot_observed` | both unresolved, missing `replay_run_current` |
| 06 stale replay | `run_nonce_observed` carries another nonce | both unresolved, operational `stale`, missing `replay_run_current`; companion `replay_run_stale` supported |
| 09 missing post-state | `php_post_state` row for req-3 (issues.create) removed; `php_post_states` still closed | create: unresolved, missing `php_post_state` (req-1 alone satisfies `op_exercised`, so only the gate catches it); close: supported; companion `post_state_gap(run, req-3, php)` supported, discrepancy `post-state-missing` |
| 08 lying closure | `mutant_killed` m-1 names req-9, not a replayed request; closures asserted | both ops supported *from the lying witness* (seeded fault); `kill_closure_gap` supported with support ∩ forbidden = the `mutant_kills_closed` witness, discrepancy `kill-outside-replayed-requests` |
| rejected 07 | control with `php_post_state` sourced `shen shen-model-host v1` | `load_case` raises; `validate_bundle` lists `evidence-producer` ×3; evaluated unvalidated both ops would be supported |
