---
name: verification-triage
description: Use when rebuilding a system with capcov to classify capability gaps, select a bounded behavioral outcome, and qualify it through reference comparisons, fault controls, and real execution. Also use when designing deterministic advancement gates for that workflow.
---

# Verification Triage

Bare-minimum, brutally pragmatic methodology to map a system's capabilities and prove a clean-room rebuild works. Grounded in capcov's real machinery, not a parallel theory. It is deliberately NOT formal verification.

## Quasi-formality and breadth-first work selection

Quasi-formality means fast, executable, falsifiable claims that catch meaningful
classes of bugs, with explicit limits. Optimize confidence gained per unit of work
across the system; do not pursue exhaustive proof of one pilot while other
capabilities remain untouched. "80/20" is a prioritization principle, not a measured
coverage percentage. Runtime usage complements deliberate checks; it does not
replace required authorization, data-integrity or release acceptance evidence.

A deterministic verdict over a bounded execution is useful; it does not make the
system, observation process, or authored contract complete.

For multi-capability rebuilds, use **one parent orchestrator plus implementation
workers**, with each worker owning its own verification. The parent owns global
coverage, task selection, scope extensions and integration; no permanent reviewer
agent is required. Read [the orchestration workflow](references/orchestration.md)
before assigning or resuming this mode. It provides assignment/checkpoint formats,
parallel ownership, explicit worker-model selection and continuation decisions.
Default to the provider's workhorse model for workers (Sol / Sonnet when available),
with the selected capable parent orchestrating; resolve supported IDs in the host. For a single bounded capability,
work directly without manufacturing orchestration overhead.

**Scheduling and qualification are different decisions.** The depth requirements
below govern what evidence permits a claim or release. They do not authorize a
worker to keep deepening its capability or override breadth-first task selection.
Return partial implementation with visible unproven requirements when a packet
ends; the orchestrator compares further depth against other capability gaps.

## The one rule: done is the deployment, not the gate

A capability is rebuilt when its e2e rows are green **against a real running instance** AND each row has a check that **fails when its guard is removed** (`GOAL.md`'s rule). The capcov gate is a **floor** that proves you *mapped* the capability — never that it *works*. Its denominator is the model's edge, not the system's. The moment you read gate-green as "done", you have built a false-green machine: the credential config scopes discovery to three routes with ~65 excluded, and the gate is designed to exit red (`test/browser/models/prove.py`, `expected=1`, "Coverage remains incomplete"). Certify against the territory, never the map.

## Map the capability — the flow model, four fields per step

**Discovery is automatic; the model is authored, and authoring is progressive — never a prerequisite for starting.** `discover` derives the surface/entity obligations from the code on its own. The flow model (`tools/axon/capcov/credential-acquisition.model.json`) is the *behavior* layer you author on top to make outcomes checkable: you begin from auto-discovery and fill the model in as you go. A human clarifies ambiguous semantics; a human does not hand-author the map before discovery can run.

A transition is **ready to prove** (not "allowed to exist") when all four are filled:

- `outcome` — the caller-distinguishable result, including relevant actor, scope, preconditions, and later effects. Identical outcome wording does not establish that two transitions are redundant.
- `obligations` — the surface(s) it binds (`http:/ask`).
- `evidence` — `file:line` into the **original**. The clean-room anchor: rebuild from here, do not guess.
- `bindings` — the concrete check.

Within an assigned capability, scenario order falls out of the fact machine: `plan` walks `requires`/`adds` from `initial` and generates the scenarios. Take the shortest path to the headline outcome first, then branch **refusal and security paths ahead of happy-path variants** (a wrong refusal is costlier than a missing convenience).

You map one capability's surfaces at a time, not the system. But **filtering a route out of THIS capability's run does not make it "outside the product."** A scoped-out surface must be **accounted globally** — assigned to some other capability's gate, or listed as explicitly unresolved in a global denominator. "Correctly absent from this gate" is a per-run fact, never a product-completeness claim; the excluded set is a ledger to reconcile, not a set to forget.

## The check must DETECT WRONG BEHAVIOR, not reproduce right behavior

For every **state-mutating or auth** transition (one that `adds`/`removes` a fact, or is a guard), one happy assert is not enough. Choose adversarial scenarios around the consequential boundary:

- **idempotency** — apply it twice;
- **ordering** — swap it with a sibling;
- **scoping** — apply it to the neighbor's subject.

These are input scenarios, not implementation mutations. Separately, seed at least one relevant implementation fault (such as removing the ownership guard or suppressing the committed write) and show that the specific binding detects it. Receipt corruption instead tests the verifier; it does not establish application fault tolerance. Record which mechanism each control challenges.

**Mutations and differential testing are complementary — neither subsumes the other.** A mutation proves your *check* can catch a fault you thought of; a differential (running the rebuild against the reference and asserting agreement) catches a divergence you did *not* think to seed. Each exposes errors the other misses — tests can kill every chosen mutant while still enforcing the wrong contract. Use mutations to prove the check has power on the spine, and a differential to catch unseeded drift; do not drop one because you have the other.

**A mutation's evidence is a SPECIFIC failing assertion, not a red aggregate gate.** The gate may already be red for unrelated reasons (incomplete coverage — `prove.py`'s gate stays red even on a good run). "Still red when I inject the fault" proves nothing. Assert that *this transition's binding* reddens *for this fault*, and is green without it. Aggregate red is not caught-the-fault.

**"Observable" includes later and persisted effects, not just the immediate response.** Two calls that both return `500` can leave different persisted state, different permissions, or different retry behavior. On a state-mutating or auth transition, the check must assert the *downstream* effect a later request reveals — matching the immediate response is insufficient exactly where the risk is highest.

## Read the ratio beside its denominator's edge

`covered/N` is meaningless alone. Always render it next to: what `discover` **scoped out** (routes the query filtered, languages with no adapter), and which transitions are **unreachable-from-initial** and **where they are proven instead**. The model's `note.moved_out` block and the baseline reasons ARE that ledger — hand-authored, the tool cannot generate it, and it is the **stopping rule**: the map is not done until every excluded surface and every unreachable transition has a one-line "proven elsewhere / not built / out of tier" reason. This is the soundiness discipline (name what you did not resolve); cutting it deletes the science and keeps a blind counter.

## Keep the loop ripping — never block on the slow signal

Aim for a local sub-10s feedback loop. A signal you block a turn on should be the cheapest one that can catch what you just changed. A target latency does not authorize omitting required behavior checks.

| tier | signal | latency | run |
|---|---|---|---|
| 0 | compile the one binary | ~1s | every edit |
| 1 | static gate (`scripts/capcov.sh`) | seconds | every edit — proves wiring; says `unproven`, not `covered`, and is honest for it |
| 2 | `--only <transition>` + its seeded mutations | seconds | every edit to that transition |
| 3 | full behavioral run (`capcov flows run`) | minutes | transition boundary |
| 4 | CI / e2e against a real instance | minutes+ | pre-merge and the done-check only |

Rules, dependency-aware (not absolute): **run relevant available local checks first; block on a slow or live signal only when the next decision actually depends on it.** Don't `git push` to answer a question a local check already answers. Some facts require the live environment — IAM, certificates, managed databases, and deployment behavior. Scope regression by blast radius. Independent work may continue while a slow check runs, but freeze the inputs that check is evaluating. A fast check may establish the same narrower predicate as part of the authoritative check; a mock-based approximation is advisory until that relationship is demonstrated. Neither a fast pass nor an infrastructure failure establishes the live outcome.

## Deterministic advancement, useful feedback

Use the existing runner or CI boundary to enforce acceptance. The agent proposes changes and receives diagnostics; the runner decides whether the selected outcome may advance. **A skill instruction alone is advisory.** If no external boundary enforces it, say so. Read [DETERMINISTIC-GATING.md](DETERMINISTIC-GATING.md) for the implementation boundary and source research.

For a consumer outcome map, use `capcov outcomes check MAP --inventory INVENTORY --target TARGET --python TARGET_PYTHON --timeout SECONDS --out RUN_JSON` as the host's advancement command. It executes the full mapped test set and requires every outcome to be demonstrated. `outcomes run` and `coverage` alone are diagnostic operations; a zero exit from either is not acceptance. The browser path requires `observe --probe browser`, `reconcile`, and `gate`: scenario failures survive route aggregation, and structural exemptions cannot waive them. Full-plan gating refuses `--only`/diagnostic runs. Use a separately authored model for a smaller accepted scope.

These code checks do not install a protected CI boundary, validate business meaning, or prevent a candidate with write access to its checker from changing it. The host must use the verdict and protect its acceptance authority. The requirements below include host responsibilities beyond capcov itself.

Before implementing the selected outcome, record in the existing task or model:

- Its reference behavior, actor/scope, required observable effects, and allowed differences.
- Required check IDs and executable bindings, including the relevant fault controls.
- Candidate/build, contract, checker, and fixture identities needed to interpret a run.
- Attempt/time budget and which evidence will allow local qualification, merge, or deployment. These are distinct decisions; use the project's existing release rules.

This is one bounded acceptance contract, not a new planning hierarchy. It may evolve when evidence exposes a wrong assumption. Record the reason, establish the revised authoritative version through the project's existing review rules, and invalidate dependent results. Never silently weaken it to turn a failure green.

The enforcing boundary must:

1. Load the required check set from the accepted contract, not infer it from whichever checks happened to execute. Missing, skipped, unknown, malformed, stale, contradictory, or partial results cannot satisfy a required check. An intentionally smaller release has its own explicit scope; it does not relabel omissions as passes.
2. Derive verdicts from actual check execution and validated observations. Agent-written status text and process exit zero without the required assertions are insufficient. Bind results to the evaluated inputs; rerun dependent checks after those inputs change.
3. Keep contract/checker authority outside the candidate's unilateral write authority, or explicitly label the run cooperative rather than independently enforced. Hashes detect change against a trusted reference; an agent that can rewrite both inputs and expected hashes can bypass them.
4. Distinguish product assertion failure from unavailable infrastructure and invalid evidence. All prevent acceptance where required, but require different repairs. Return the check ID, expected/observed facts, and a bounded reproduction command. Keep full raw output outside the prompt and link it.
5. Bound attempts across the whole repair cycle, including workflow back-edges and restarts. On exhaustion, preserve the failed outcome and checkpoint the blocker; never convert exhaustion into success. Cleanup obligations survive failure and cancellation.

Feedback checks can run frequently without authorizing advancement. Hard acceptance checks cannot be replaced by an LLM's explanation, a structural coverage ratio, or an aggregate satisfaction score. Subjective evaluation may supplement hard invariants; record its judge, rubric, sample, and uncertainty separately.

Before calling an integration enforced, demonstrate that it refuses advancement when a required check is omitted, a real check fails, source evidence is stale, or success is forged in agent output. This tests the boundary itself. Start with existing commands and an existing runner; do not build another orchestrator merely to implement this prose.

## The single worst failure

Run `capcov.sh`, see the gate exit 0 with its baselined lines, declare the rebuild verified — having never run the behavioral step, never seeded a wrong behavior, over a denominator of one route in one tier while dozens of routes and other languages sit outside it by construction. Every honest marker (`unproven`, `moved_out`, "discovery unresolved", the deliberately-red gate) was present and read as a formality. Green meant "the three things I chose to look at are shaped the way I said"; it was reported as "works".

## Know when to stop extending the tool

Extending capcov is a means, not the work. **Stop the moment an engine change no longer *blocks* evaluating a required product outcome, and go back to qualifying the product.** A tool extension is justified only while its absence prevents you from trusting a real outcome (e.g. no way to prove a write's effect). The failure mode this session's whole thread warns about is the reverse: accumulating infrastructure while most of the product stays unassessed. The loop is: discover across the surface → classify each gap (measurement / implementation / acceptance) → pick a high-value user outcome → run targeted checks and the relevant faults → qualify that outcome → update the backlog. Reach a usable end-to-end flow early; do not let engine work outrun a single qualified capability.

Breadth-first product progress is not the planner's breadth-first graph traversal. Keep a coarse global inventory, then work one selected deployable outcome through its bounded checks before taking happy-path variants. Additional required cases stay in the existing backlog. At each iteration identify the outcome advanced, the execution that supports that claim, or the demonstrated blocker removed. If two consecutive iterations produce none of these, reassess the approach before expanding tooling. A hard gate can prevent premature acceptance; it cannot by itself make an agent choose useful work.

## Partial shipment is an explicit scope decision, and the spine is never shallow

Shipping less than the whole is legitimate — but it is a *decision that preserves the full goal*, not a silent redefinition. A limited release names exactly what it covers and leaves the rest assigned or unresolved in the global denominator; it never lets discovery's filtering *authorize* dropping a required capability. And the "verify it shallow" default has a hard exception: **for authentication, writes, and delivery, a shallow bug's cost is not bounded** — a wrong write, a leaked permission, or a dropped message is silent and expensive. Those are the spine; they are deep-always, differential *and* mutation, effect-and-ownership asserted, regardless of the release's scope.

## Use capcov's own words

Verbs: `discover` / `plan` / `coverage` / `run` / `report` / `gate`. States: `covered` / `unproven` / `unmapped` / `unknown-obligation` / `OBSOLETE`.

**Classify every gap before prescribing work — three kinds, three different actions:**

- **measurement** — discovery failed to extract, identify, or map it (a duplicate-route collision, an unresolved language, a scoping mistake). Fix the tool or the model; do NOT build anything.
- **implementation** — genuinely not built. A build task.
- **acceptance** — built, but not yet qualified against reference behavior. A test/qualification task.

`unknown-obligation` is usually measurement OR implementation, and prescribing "go build it" on a measurement gap builds a duplicate or chases a phantom — your duplicate-route blocker is exactly this. `unproven` is an acceptance gap. Split the cause first; only a confirmed *implementation* gap is a build task. Then fix confirmed `unknown-obligation` before `unproven`; `unmapped` means your model missed a scoped surface.

Do not re-teach the gate/baseline discipline — `tools/axon/capcov/baseline.README.md` already does, correctly; point at it rather than forking it.

Tooling gaps this method exposes (extend the tool, do not file the method down to fit it): a `mutations` field + generalized fault-matrix runner; `discover` emitting the excluded-surface count and unresolved-language list as first-class fields; `plan` emitting the unreachable-from-initial set; a `--only <transition>` selector; and wiring `capcov flows run` into the driver that currently omits it. See `TOOLING-EXTENSIONS.md` beside this file.

## Keep fixture premises independent of the candidate

Build SQL fixtures from pinned incumbent DDL or executed migrations, and retain
the source identity. Do not infer column names or types from candidate queries: a
test schema that repeats the implementation can pass while the real database
rejects it. Check required columns against the migrated fixture before running
behavior. Likewise, a missing-object fixture cannot establish present-object
serialization; retain that conditional dependency instead of hardcoding its
observed output as the general contract. A discovered shared assumption invalidates
the affected earlier evidence until the independent comparison is rerun.
