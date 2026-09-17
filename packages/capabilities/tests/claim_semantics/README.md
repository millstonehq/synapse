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

## Model well-formedness (Stage D placeholder)

The committed replay receipts `replay_receipt_min`,
`replay_receipt_target_go_qualified` and `replay_receipt_target_go_unqualified`
carry a `model_well_formed.json` and a `model_checkers.json`.  Both are
**placeholders**: the certificate is `sha256("pending: checker not yet built")`
under checker `stage-d-typecheck` version `0.1-pending`, and the reviewer's
list admits exactly that pair.  They exist so the corpus and the fixtures
exercise the *shape* of the premise `op_qualified_rt` now carries -- a typed
checker, named by class `modelcheck`, certifying the same model
`model_describes_run` binds to the run, at a version the reviewer admits --
not because any model has been typechecked.  Replace both files with the real
checker's output when Stage D emits one; nothing else in the pack or the
exporter has to change.  `replay_receipt_target_go_repeat` deliberately has
neither file, which is how the join reports `model_well_formed: missing`.

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
