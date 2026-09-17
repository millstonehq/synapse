# CapCov integration comments

## Ground explanations belong in acceptance receipts

- Keep the certificate as the replayable proof object and publish a compact
  `why` summary beside the verdict. Do not embed a second copy of the full
  certificate in the receipt.
- Ask `why_not` about the relation that owns the real gate. For the replay
  judge, querying the thin `op_qualified` wrapper only reports that
  `op_qualified_rt` is absent; querying `op_qualified_rt` identifies the
  actual missing or blocking premise.
- Record assumption leaves explicitly. A supported verdict carried by a
  synthetic census or reviewer exclusion is useful incremental evidence, but
  it is not equivalent to replacing that assumption with observed evidence.
- Generate explanations from the agreed relation closure. This keeps Python
  and Souffle responsible for evaluation while making the explanation
  engine-independent and certificate-recheckable.

## Running the target-go pilot

- The retained runtime receipt is source-bound to target-go commit `01fe913`;
  running it against another checkout must fail closed.
- Stage the candidate CapCov diff and run `git diff --cached --check` before
  the source-bound fixture so the expensive run is not invalidated by later
  formatting cleanup.
- The focused replay suite needs Souffle. The live static/runtime pilot also
  needs the pinned `scip-go`, `scip`, and Go tools.
- Low free disk can make a Souffle differential run look like a kernel
  mismatch with an empty operational message. Check storage and rerun before
  diagnosing a semantic disagreement; retain the replay bundle either way.

## Current evidence

- The qualified replay receipt derives `op_qualified(delete-issue)` and its
  ground explanation names the two remaining census assumptions.
- The deliberately under-declared receipt remains unresolved; its ground
  why-not identifies `undeclared_any` as present.
- The source-bound target-go pilot derives and explains both the static route
  to SQL and the causal runtime route-to-SQL claim from commit `01fe913`.
