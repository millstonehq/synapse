# Capcov claim-semantics Pi workflow

This project-local Pi extension drives the staged experiment in
[`EXPERIMENT-PLAN.md`](../../EXPERIMENT-PLAN.md). It is intentionally a repository-work
harness, not part of capcov's production engine.

## Run

1. Trust the checkout and load project resources (`pi -a`, then `/reload` if Pi was
   already open).
2. Ensure `HEAD` descends from the reviewed PR #45 integration base
   `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765`.
3. Commit the workflow and any other existing changes. A new run requires a clean
   worktree.
4. Run one checkpoint (the safe default):

   ```text
   /capcov-workflow start
   ```

5. Inspect progress or continue later:

   ```text
   /capcov-workflow status
   /capcov-workflow resume
   /capcov-workflow resume --tasks 3
   /capcov-workflow stop
   /capcov-workflow retry <task-id>
   ```

Pin the devShell closure with a GC root before any long run. `nix develop` creates no
root, so a garbage collection during a gate deletes Soufflé, Python, or Go mid-run
and every external-binary gate fails for infrastructure reasons:

```sh
nix build --no-update-lock-file .#devShells.aarch64-darwin.default \
  --out-link .capcov/pi-workflow/devshell-gcroot
```

Before `start` or any long resume, prove the installed Pi subprocess and parser
contract cheaply in an interactive Pi session:

```text
/capcov-workflow smoke
```

The deterministic manifest seam can be checked without Pi or a model:

```text
node .pi/workflows/test-capcov-experiment.mjs
node .pi/workflows/test-capcov-runtime.mjs
```

The smoke is capped at two minutes, uses a read-only worker, requires an exact JSON
result, appends a `smoke-result` event, and must leave actionable start/end details in
`.capcov/pi-workflow/driver.log`.

State, bounded worker diagnostics, patches, and gate evidence are journaled under ignored
`.capcov/pi-workflow/`. `start` refuses to overwrite an existing journal. Remove that
directory only when deliberately beginning a distinct experiment run.

## Control model

For each dependency-ready task in
[`capcov-experiment.json`](capcov-experiment.json), the driver:

1. launches two bounded, read-only scouts with independent semantic and testing
   lenses;
2. launches one writer in the main worktree with the exact task, write set,
   acceptance statements, prior backpressure, and scout evidence;
3. rejects agent-created commits and changes outside the declared write set;
4. runs manifest-authored gates directly, outside the model;
5. writes a review patch and launches independent read-only skeptics;
6. accepts the task only when every gate passes and every reviewer approves;
7. creates the task's git checkpoint itself and appends a completion event.

Tasks are admitted through ordered waves. A wave may fan out read-only scouts,
and parallel workers run in real detached Git worktrees. Their patches and gate
results are persisted, then a single reducer integrates them into the root in
manifest order. Only that reducer can mutate or commit the root checkout.
Parallel tasks are accepted only when they declare distinct isolated `worktree`
paths and their glob write sets are disjoint; the manifest loader rejects unsafe
overlap instead of guessing. Each wave emits a `wave-checkpoint` event and
pauses by default, so `/capcov-workflow resume` is the explicit admission to the
next wave. `admission.requiresCompleted` and `admission.requiresEvents` provide
hard conditional downstream admission for the Shen, specialization, and real-Go
tracks without treating an agent's report as evidence. Existing task checkpoints
are treated as virtual legacy checkpoints through the configured alias map.

Differential/mismatch failures are identified only by the manifest's explicit
gate `failureKind`, never by matching diagnostic text. They are recorded as
`wave-repair` events. A wave is
blocked after its configured (default three) repair attempts; retries cannot
silently turn an unresolved counterexample into a pass.

An implementer's `status: ready` is never the completion predicate. Failed tools,
invalid structured output, failed gates, refuted reviews, missing external fixtures,
and timeouts remain failures or blockers in the journal rather than being replaced
with guessed output. A crash is resumable: completed checkpoints are reconstructed
by replaying `events.jsonl`; an interrupted attempt is retried rather than declared
complete.

The Go milestone may stop honestly when `CAPCOV_GO_FIXTURE_ROOT` is absent. Synthetic
Python notification behavior cannot satisfy it.

The active manifest is Datalog-first: semantic contract, adversarial corpus,
parallel Python-reference and real Souffle kernels, differential shrinking with
kernel provenance repair, a pinned SCIP toolchain, the SCIP-facts-to-Datalog
wave (parallel exporter and rule-pack workers reduced by a static differential),
certificates, an target-go static path pilot, fresh target-go qualification, and bounded
Datalog evaluation (EXPERIMENT-PLAN.md sections 27-30). The older
Shen/specialization chain remains represented only for journal aliasing.
Legacy tasks are disabled and cannot run or satisfy the independent
Python-plus-Souffle evidence gate.

Gates that depend on an external binary (`souffle`, `scip`, `scip-go`) are
fail-closed: they require the tool to resolve under `/nix/store` and reject a
test run whose output contains `skipped`. Locally the same test modules skip
when the tool is absent so `unittest discover -s tests` stays honest outside
`nix develop`; a skip is never accepted as gate evidence.

Manifest, harness, or driver edits made by a human between checkpoints are
committed by the human and journaled as a `manifest-checkpoint` event whose
`checkpoint` is that commit. Resume accepts it as the expected HEAD; it completes
no task and satisfies no admission requirement. A `task-reset` appended by a
human must carry a `reason` naming the infrastructure failure (timeout
misconfiguration, host kill) that consumed the attempts; it is never used after
a gate or review failure.

Tasks that were delivered manually from `codex/*` worktrees before the driver
ran them are recorded in `events.jsonl` as `task-completed` events carrying
`manual: true` and `integrated_from` revisions, with `checkpoint` set to the
manifest realignment commit. That backfill is a human decision recorded in
EXPERIMENT-PLAN.md section 26; the driver treats it exactly like its own
checkpoints and will not re-run those tasks.

## Trust and safety

- The committed manifest owns commands; agents cannot invent executable gate
  commands.
- Writers receive normal coding tools and therefore execute with the user's OS
  authority. Use this only in a trusted checkout/container.
- Reviewers receive only Pi's `read` tool. They inspect the persisted patch and
  source but cannot invoke shell commands or edit.
- Only one reducer writer integrates a wave at a time. Read-only scouts and
  declared parallel workers run in isolated worktrees. Parallel worktrees and
  disjoint manifest write sets are validated at load time.
- The run is bounded by task count, three attempts per task, subprocess timeouts,
  dependency edges, and explicit cancellation.
- Manual retry cannot reset an exhausted attempt budget, and cannot race an active run.
- Resume pins HEAD to the journal's initial base/latest checkpoint and permits dirty
  files only inside the next task's declared write set.
- Checkpoint commits are enabled in the manifest. The driver requires a clean tree
  on `start`, owns commits, and never pushes.
- Project-controlled extensions and prompts are code. Review them before approving
  the project in Pi.

## Why this shape

The workflow combines useful patterns from the reviewed prior art without copying
its weakest trust assumptions:

- **Pi extensions:** project command, lifecycle cancellation, status/widget UI,
  isolated child Pi processes, and restricted tool activation.
- **Shen-Backpressure/Ralph:** fresh live context per iteration, deterministic gates,
  bounded retries, and gate failures fed into the next attempt.
- **Grok build workflows:** event-sourced state, fixed phase contracts, explicit
  dependency edges, independent skeptics, and failure-preserving resume.
- **Ultracode/dynamic workflows:** fan-out/fan-in for independent read-only work,
  structured worker returns, evidence-first review, and one authoritative reducer.
- **Git checkpoints:** coherent, reviewable checkpoints owned by the harness rather
  than trusting an agent's completion claim.

The workflow remains deliberately specific to this experiment. The canonical IR,
expected verdicts, and semantic decisions continue to have one integrator: the
ordered task chain and `EXPERIMENT-PLAN.md`, not competing worker-authored schemas.
