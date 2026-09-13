# capcov tooling extensions the verification-triage method demands

The method (see `SKILL.md`) is grounded in the literature (model-based testing, coverage
obligations, reflexion model-vs-reality, soundiness). Where capcov as built cannot express
what the science requires, the fix is to **extend capcov**, not to weaken the method to fit
the current tool. These came out of a 2026-09-13 expert review (Linus / Fournier / Majors /
Karpathy / red-team-Taleb) grounded in the real tree under `tools/axon/`.

Ranked by how much a missing one lets a false green through.

## 1. A `mutations` field + a generalized fault-matrix runner (highest value)

**Gap.** A binding with one happy-path assert cannot distinguish two systems that agree on
the trajectory and diverge on a mutation (idempotency, ordering, scoping). This is the
governing correctness risk for every state-mutating or auth transition.

**The pattern already exists** — `tools/axon/test/browser/models/prove.py` runs an 8-fault
matrix: it injects a wrong behavior and asserts the gate goes RED. It is per-model and
hand-built for the conversation model; the credential model has none.

**Extension.** Each transition may declare `mutations: [{kind: idempotency|ordering|scoping,
...}]`. The runner applies each mutation to the rebuild and asserts the transition's binding
reddens. A transition's coverage is not `covered` until its happy assert passes AND every
declared mutation is caught. "Green" becomes "detects the wrong behaviors", not "reproduced
one right path". This subsumes and is stronger than a live-oracle dual-hit, which only ever
drives the happy path.

## 2. First-class denominator provenance from `discover`

**Gap.** The discovery query silently filters (credential config matches 3 routes; ~65 on
`web.go` are excluded; some models set `adapters: []` with "discovery unresolved"). A
`covered/N` ratio over a silently-narrowed `N` reads as "done" when it means "done for the
sliver I chose to look at".

**Extension.** `discover` emits, as first-class fields, the **excluded-surface count** (what
the scope query could see but filtered) and the **unresolved-language list** (extensions
missing). `report`/`gate` render `covered` next to `excluded` and `unresolved`, never a bare
percentage.

## 3. `plan` emits the unreachable-from-initial transition set

**Gap.** Transitions excluded from the plan (unreachable from `initial`, or moved out) can
never surface as a gap — they are invisible to the gate. Today the reasoning about them lives
in hand-authored `note.moved_out` prose that the tool cannot generate or check.

**Extension.** `plan` outputs the set of declared transitions that its BFS did not reach from
`initial`. The human's job becomes annotating **where each is proven instead** (a Go suite, an
acceptance row), turning the soundiness ledger from remembered prose into a checked list.

## 4. A `--only <transition>` selector for the sub-10s inner loop

**Gap.** `reconcile()` always folds the whole plan, so the tightest scope the tool can express
is the whole capability — minutes at scale, when the loop wants one transition in seconds.

**Extension.** `--only <transition|scenario>` on `run`/`coverage` scopes to a single unit so
the inner loop is: edit → build the one thing → check the one transition (+ its mutations) →
red/green in seconds. Whole-capability gate stays the outer (CI) loop.

## 5. Wire the behavioral step into the driver, or make its omission loud

**Gap.** `tools/axon/scripts/capcov.sh` omits `capcov flows run` — the only step that produces
behavioral evidence — so the operator's loop reads `unproven` for every surface and baselines
it as accepted. Running it daily trains "unproven = fine".

**Extension.** Either wire `run` into the driver behind the same freshness guards, or have the
driver print a loud, unbaselineable banner that behavioral assurance was NOT collected and the
result is structural-only. A done-check MUST run `run` against a real instance.

## 6. (If a live run is added) stamp the original's identity into `assurance`

**Gap.** `assurance` is a provenance string that currently says *injected boundaries +
fixtures*. Reading it as a liveness flag manufactures a false green.

**Extension.** When a run executes against a real original, record the original's commit/build
id into the `assurance` value, so "live" is a fact the artifact carries, not an adjective the
reader supplies. Print `assurance` verbatim; "injected fixtures" is not-done for a parity claim.

---

**The load-bearing disagreement, recorded rather than averaged.** Majors proposed a live-oracle
dual-hit against the running original as the inner-loop check. Red-team (Taleb) showed that for
the spine (state-mutating / auth transitions) a happy-path dual-hit is a weaker reinvention of
the seeded-mutation matrix that already exists in `prove.py`, because it only ever drives the
one agreed trajectory. **Resolution: seeded mutations (extension 1) are primary for the spine;
a live oracle or a corpus generated from the live original is a secondary, optional broad
happy-path check — never hand-transcribed literals.** The evidence that would flip it: if
seeded mutations prove too sparse to catch real regressions that a live diff would, add the
live oracle as a complement, not a replacement.
