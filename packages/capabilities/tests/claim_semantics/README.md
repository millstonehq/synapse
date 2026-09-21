# Stage A claim-semantics corpus

The numbered JSON files are evaluator-independent semantic controls.  A
reviewer can inspect `claims`, `facts`, `assumptions`, and `expected` without
running Python, Soufflé, Shen, or the capcov claim package.

Each fixture references `corpus/schema-v1.json`, which fixes ordered typed
relation arguments, context indices, polarity, and modality. Every claim,
fact, and assumption carries its ordered `args`, complete context-key map, and
explicit provenance dependencies.

Each per-claim expected result keeps five things separate:

* `semantic_verdict`: `supported`, `refuted`, `unresolved`, or `conflicting`;
* `operational_status`: one of the canonical claims statuses (`complete`,
  `invalid-input`, `inconsistent-premises`, `resource-exhausted`,
  `unsupported-construct`, `stale`, or `out-of-scope`);
* `support_leaves` and `refutation_leaves`: polarity-specific derivation IDs;
* `observed_leaves` and `forbidden_leaves`: all observed inputs versus IDs a
  derivation must not use;
* `discrepancies` and `missing_premises`: why a tempting Boolean answer is not
  sufficient.

`expected.json` is a review table duplicated from each fixture.  The tests
only validate that the table and fixtures agree; they do not evaluate rules.
The fixtures are synthetic controls until a real retained execution is added.
`adapter.py` converts each fixture to strict bundle JSON and invokes the real
`bundle_from_json(..., validate=True)` parser; it does not evaluate rules.

## Checker authority is operation scoped

The typed checker emits two producer facts. `model_well_formed.json` records
global model structure. `model_operation_checked.json` records a positive row
only for each operation whose local write, matrix, atlas, and registry
judgements all pass. A skipped or failing operation has no row and cannot
borrow another operation's result. The modelcheck certificate digest includes
stable semantic inputs and judgements; it excludes nonce, elapsed time, and
other run-envelope values. Its `checker_binary` is the SHA-256 of the resolved
native Shen executable. The Bifrost launcher hash remains a separate input to
the semantic certificate.

Reviewer authority is supplied separately to the exporter. Each
`model_checker_admitted` row must match the model, operation, checker name,
version, native binary digest, and semantic certificate digest of one exact
`model_operation_checked` row. Receipt-local `model_checkers.json` is ignored,
and placeholder reviewer names contribute no authority. Structural validity,
operation coverage, and reviewer admission remain positive premises with no
closure relation.

The three real target-go fixtures have no checker observations or caller
admissions, so their qualification remains pending at the first missing
checker-authority premise. That is distinct from a finding against the port:
the checker premises stay last in `_BLOCKING_ORDER`, the summary reports
`pending <premise>`, and `scripts/compiled_checker.py` exits **5** when every
required operation reaches only a pending checker premise. Exit **1** wins
when an operation has a real blocker such as `undeclared_any`.

`replay_receipt_min` and the corpus derived from it remain explicitly
synthetic. Their made-up structural, operation, and reviewer rows exercise the
positive join. Corpus case `32-partial-operation-check` has checker authority
for `delete-issue` only; the other operations stay pending at
`model_operation_checked`.

## The learn campaign fixture

`fixtures/replay_receipt_target_go_qualified/learn/` is a **real** learn receipt,
derived from a campaign the candidate repo ran against the same model
(`08380c9c…`) as the receipt it sits under, with the identifiers scrubbed: 12
generated tapes, 20 model predictions, 32 oracle observations, 3 ops the model
does not model (`create-issue`, `edit`, `delete-issues`), and no counterexample.
Two things were rewritten and nothing else: the `run` column of every row is the
*replay* run this receipt is for (the campaign's own run id moved to the
`campaign` column of `learn_run`, which is where the contract puts it), and the
producer's `class` column is named `predicted` / `observed` by the side that
wrote it.  The learn digest, the tape and step names, the classes, the state
digests and the oracle commit are the campaign's own.

Because none of the three unmodelled ops is `delete-issue`, the committed fixture
is the *consistent* case: `learn_consistent(run, delete-issue)` is supported and
nothing the receipt would qualify is downgraded.  The other shapes
(`LearnCampaignTest` in `test_target_go_replay_receipt.py`) are temp copies of it
with one row edited — a planted counterexample, an unmodelled `delete-issue`, the
same with the list left open — and `NoLearnReceiptTest` is the receipt with no
campaign at all, judged exactly as it was before the learn relations existed.

## Assumption registry and invalidation

`test_assumption_registry.py` covers `capcov.claims.assumptions` over the
committed `replay_receipt_target_go_qualified` fixture: the run-independent
`asm:` id (producer class + relation + row, so one reviewed row keeps one id
across runs), the registry of what each assumption carries, and withdrawal —
dropping an assumption and re-evaluating both kernels to see which claims lose
support. Reachable from the command line as

```
python -m capcov.claims.cli claims assumptions registry   --receipt DIR [--out DIR]
python -m capcov.claims.cli claims assumptions invalidate --receipt DIR --drop ID
```

Exit 0 when the documents were produced, 2 for a refusal (an unknown id, or a
withdrawal that would refute a claim rather than leave a premise missing), 3
when the kernels disagree. Needs Soufflé, no replay environment.
