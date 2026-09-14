---
name: verification-triage
description: Use when clean-room reimplementing a system with a coverage tool (capcov) and deciding how to map its capabilities and prove the rebuild actually works — under time pressure, when a green gate tempts you to declare "done", when a state-mutating or auth path needs proving, or when you are about to wait on CI instead of iterating locally. Symptoms — "is the gate green enough to ship", "did I verify it or only map it", "how do I keep iteration fast", clean-room rebuild, differential/mutation testing, false green.
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

- `outcome` — the caller-distinguishable result, plain words. Two transitions with the same outcome means one is not a real capability.
- `obligations` — the surface(s) it binds (`http:/ask`).
- `evidence` — `file:line` into the **original**. The clean-room anchor: rebuild from here, do not guess.
- `bindings` — the concrete check.

Within an assigned capability, scenario order falls out of the fact machine: `plan` walks `requires`/`adds` from `initial` and generates the scenarios. Take the shortest path to the headline outcome first, then branch **refusal and security paths ahead of happy-path variants** (a wrong refusal is costlier than a missing convenience).

You map one capability's surfaces at a time, not the system. But **filtering a route out of THIS capability's run does not make it "outside the product."** A scoped-out surface must be **accounted globally** — assigned to some other capability's gate, or listed as explicitly unresolved in a global denominator. "Correctly absent from this gate" is a per-run fact, never a product-completeness claim; the excluded set is a ledger to reconcile, not a set to forget.

## The check must DETECT WRONG BEHAVIOR, not reproduce right behavior

For every **state-mutating or auth** transition (one that `adds`/`removes` a fact, or is a guard), one happy assert is not enough — it cannot tell apart two systems that agree on the trajectory and diverge on a mutation (a session stopped twice minting two ledger rows; `expire` reordered before `stop`; a reply clearing the wrong open demand). Such a transition carries **≥1 seeded mutation the binding must turn RED**:

- **idempotency** — apply it twice;
- **ordering** — swap it with a sibling;
- **scoping** — apply it to the neighbor's subject.

Green means "catches the wrong behaviors", not "matched one path". The repo already does this — `prove.py` runs an 8-fault matrix and asserts the gate reddens. Generalize that.

**Mutations and differential testing are complementary — neither subsumes the other.** A mutation proves your *check* can catch a fault you thought of; a differential (running the rebuild against the reference and asserting agreement) catches a divergence you did *not* think to seed. Each exposes errors the other misses — tests can kill every chosen mutant while still enforcing the wrong contract. Use mutations to prove the check has power on the spine, and a differential to catch unseeded drift; do not drop one because you have the other.

**A mutation's evidence is a SPECIFIC failing assertion, not a red aggregate gate.** The gate may already be red for unrelated reasons (incomplete coverage — `prove.py`'s gate stays red even on a good run). "Still red when I inject the fault" proves nothing. Assert that *this transition's binding* reddens *for this fault*, and is green without it. Aggregate red is not caught-the-fault.

**"Observable" includes later and persisted effects, not just the immediate response.** Two calls that both return `500` can leave different persisted state, different permissions, or different retry behavior. On a state-mutating or auth transition, the check must assert the *downstream* effect a later request reveals — matching the immediate response is insufficient exactly where the risk is highest.

## Read the ratio beside its denominator's edge

`covered/N` is meaningless alone. Always render it next to: what `discover` **scoped out** (routes the query filtered, languages with no adapter), and which transitions are **unreachable-from-initial** and **where they are proven instead**. The model's `note.moved_out` block and the baseline reasons ARE that ledger — hand-authored, the tool cannot generate it, and it is the **stopping rule**: the map is not done until every excluded surface and every unreachable transition has a one-line "proven elsewhere / not built / out of tier" reason. This is the soundiness discipline (name what you did not resolve); cutting it deletes the science and keeps a blind counter.

## Keep the loop ripping — never block on the slow signal

The inner loop is local and sub-10s. A signal you block a turn on had better be the cheapest one that can catch what you just changed; a 10-minute CI wait for a one-line edit is a loop bug, not caution.

| tier | signal | latency | run |
|---|---|---|---|
| 0 | compile the one binary | ~1s | every edit |
| 1 | static gate (`scripts/capcov.sh`) | seconds | every edit — proves wiring; says `unproven`, not `covered`, and is honest for it |
| 2 | `--only <transition>` + its seeded mutations | seconds | every edit to that transition |
| 3 | full behavioral run (`capcov flows run`) | minutes | transition boundary |
| 4 | CI / e2e against a real instance | minutes+ | pre-merge and the done-check only |

Rules, dependency-aware (not absolute): **run every available local check first; block on a slow or live signal only when the next decision actually depends on it.** Don't `git push` to answer a question a local check already answers. But some facts only the live environment teaches — IAM, certificates, managed-DB and Fargate behavior — and waiting on those is informing, not stalling, when your next step depends on them. Scope regression by **blast radius, not line count**: a one-line change to a shared composition can justify broad checks because it moves a fleet. When a signal is slower than your next edit and nothing downstream needs it yet, fire it async and keep working. The fast proxy must be a **strict subset** of the authoritative check (a proxy failure is always a real failure); drift between proxy and authoritative is itself a bug to fix, not tolerate.

## The single worst failure

Run `capcov.sh`, see the gate exit 0 with its baselined lines, declare the rebuild verified — having never run the behavioral step, never seeded a wrong behavior, over a denominator of one route in one tier while dozens of routes and other languages sit outside it by construction. Every honest marker (`unproven`, `moved_out`, "discovery unresolved", the deliberately-red gate) was present and read as a formality. Green meant "the three things I chose to look at are shaped the way I said"; it was reported as "works".

## Know when to stop extending the tool

Extending capcov is a means, not the work. **Stop the moment an engine change no longer *blocks* evaluating a required product outcome, and go back to qualifying the product.** A tool extension is justified only while its absence prevents you from trusting a real outcome (e.g. no way to prove a write's effect). The failure mode this session's whole thread warns about is the reverse: accumulating infrastructure while most of the product stays unassessed. The loop is: discover across the surface → classify each gap (measurement / implementation / acceptance) → pick a high-value user outcome → run targeted checks and the relevant faults → qualify that outcome → update the backlog. Reach a usable end-to-end flow early; do not let engine work outrun a single qualified capability.

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
