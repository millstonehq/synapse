# Capcov architecture decisions

This set records the decisions behind the claims engine, the capability
observation bridge, and the optional-profile work. Status describes the
decision, not completion of every implementation or qualification step.

| ID | Decision | Status | Implementation owner / evidence |
|---|---|---|---|
| [ADR-0002](ADR-0002-evidence-authority-and-closed-world.md) | Typed evidence, producer authority, and witnessed negation | Accepted | `packages/capabilities/src/capcov/claims/validation.py` and evaluator; PR #50, `0af3b71` |
| [ADR-0003](ADR-0003-kernel-agreement-and-its-limits.md) | Python and Souffle kernels; agreement is bounded | Accepted | `claims/differential.py`, replay/static packs; `79c08a6` |
| [ADR-0004](ADR-0004-operation-scoped-model-checker-authority.md) | Shen Stage D is optional evidence; admission is operation-scoped | Accepted | `claims/replay/`; `c684099`, authority fix `79c08a6` |
| [ADR-0005](ADR-0005-static-index-and-completeness-scope.md) | SCIP residue is visible; closure requires a scoped witness | Accepted | `claims/static/`, `scip/`; PR #50, `0af3b71` |
| [ADR-0006](ADR-0006-cache-identity-and-heavy-work-lock.md) | Reuse exact Git blobs and serialize machine-heavy work | Accepted | PR #51, `649be7f`; cache and lock scripts |
| [ADR-0007](ADR-0007-jev-is-advisory.md) | Jev can prioritize probes, never discharge premises | Accepted | PR #52 source at `54e2b89`; `claims/jev_patterns.py` and the Jev experiment README |
| [ADR-0008](ADR-0008-observation-claims-and-qualification.md) | Lane A comparison claims do not imply model or migration qualification | Accepted | `5503b35`, `97c3b12`, `79c08a6` |
| [ADR-0009](ADR-0009-invocation-and-external-admission.md) | Bind immutable invocation before setup; admission is external and byte-exact | Accepted | Companion observation producer commits `092e030`, `0bcb44a`; consumer `97c3b12` |
| [ADR-0010](ADR-0010-layered-provenance-and-legacy-refusal.md) | Separate capture, comparison, export, and judgment identity | Accepted; reuse enforcement incomplete | Public replay/export sources under `packages/capabilities/src/capcov/claims/`; legacy reuse remains refused |
| [ADR-0011](ADR-0011-optional-profiles-and-default-compatibility.md) | Optional profiles preserve upstream behavior unless explicitly selected | Accepted; implementation in progress | optional-profile branch `d8cdeba`, based on upstream `1b6a47a` |
| [ADR-0012](ADR-0012-native-checker-and-worker-gates.md) | Compile or serve Shen only after measured, reviewed equivalence and benefit | Deferred | Measurement report at `79c08a6`; no compiled Stage D checker |
| [ADR-0013](ADR-0013-artifact-retention-and-privacy.md) | Keep small reviewed evidence in Git; retain bulky outputs by immutable digest | Proposed | Repository owners; publication controls in current process |
| [ADR-0014](ADR-0014-integration-and-test-budget.md) | Freeze interfaces, review trust boundaries, and bound test cost | Accepted | `EXPERIMENT-PLAN.md`, `EXPERIMENT-HANDOFF.md`, and `.github/workflows/ci.yml` |

Private run records, worktree paths, and raw evidence are intentionally excluded
from this publication set. Historical program counts in review prose are
deliberately not repeated here as current counts.
