---
name: verification-triage
description: Use when clean-room reimplementing a system with a coverage tool (capcov) and deciding how to map its capabilities and prove the rebuild actually works — under time pressure, when a green gate tempts you to declare "done", when a state-mutating or auth path needs proving, or when you are about to wait on CI instead of iterating locally. Symptoms — "is the gate green enough to ship", "did I verify it or only map it", "how do I keep iteration fast", clean-room rebuild, differential/mutation testing, false green.
---

# Verification Triage

Bare-minimum, brutally pragmatic methodology to map a system's capabilities and prove a clean-room rebuild works. Grounded in capcov's real machinery, not a parallel theory. It is deliberately NOT formal verification.

## The one rule: done is the deployment, not the gate

A capability is rebuilt when its e2e rows are green **against a real running instance** AND each row has a check that **fails when its guard is removed** (`GOAL.md`'s rule). The capcov gate is a **floor** that proves you *mapped* the capability — never that it *works*. Its denominator is the model's edge, not the system's. The moment you read gate-green as "done", you have built a false-green machine: the credential config scopes discovery to three routes with ~65 excluded, and the gate is designed to exit red (`test/browser/models/prove.py`, `expected=1`, "Coverage remains incomplete"). Certify against the territory, never the map.

## Map the capability — the flow model, four fields per step

One JSON file per capability (`tools/axon/capcov/credential-acquisition.model.json` is the real one). A transition is **ready to rebuild** only when all four are filled:

- `outcome` — the caller-distinguishable result, plain words. Two transitions with the same outcome means one is not a real capability.
- `obligations` — the surface(s) it binds (`http:/ask`).
- `evidence` — `file:line` into the **original**. The clean-room anchor: rebuild from here, do not guess.
- `bindings` — the concrete check.

Order falls out of the fact machine: `plan` walks `requires`/`adds` from `initial` and generates the scenarios. Take the shortest path to the headline outcome first, then branch **refusal and security paths ahead of happy-path variants** (a wrong refusal is costlier than a missing convenience).

Skip everything outside `scope`, provably — the discovery query already filters, and the baseline README records the excluded routes as *correctly absent*. You map one capability's surfaces, not the system.

## The check must DETECT WRONG BEHAVIOR, not reproduce right behavior

For every **state-mutating or auth** transition (one that `adds`/`removes` a fact, or is a guard), one happy assert is not enough — it cannot tell apart two systems that agree on the trajectory and diverge on a mutation (a session stopped twice minting two ledger rows; `expire` reordered before `stop`; a reply clearing the wrong open demand). Such a transition carries **≥1 seeded mutation the binding must turn RED**:

- **idempotency** — apply it twice;
- **ordering** — swap it with a sibling;
- **scoping** — apply it to the neighbor's subject.

Green means "catches the wrong behaviors", not "matched one path". The repo already does this — `prove.py` runs an 8-fault matrix and asserts the gate reddens. Generalize that; a happy-path oracle (dual-hitting a live original) is a weaker reinvention of it.

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

Rules: never `git push` to find out if a change works — CI **confirms**, it does not **inform**. Change one transition → check one; never re-run all of them or rebuild the world for a one-line edit. When a signal is slower than your next edit, fire it async and keep working. The fast proxy must be a **strict subset** of the authoritative check (a proxy failure is always a real failure); drift between proxy and authoritative is itself a bug to fix, not tolerate.

## The single worst failure

Run `capcov.sh`, see the gate exit 0 with its baselined lines, declare the rebuild verified — having never run the behavioral step, never seeded a wrong behavior, over a denominator of one route in one tier while dozens of routes and other languages sit outside it by construction. Every honest marker (`unproven`, `moved_out`, "discovery unresolved", the deliberately-red gate) was present and read as a formality. Green meant "the three things I chose to look at are shaped the way I said"; it was reported as "works".

## Use capcov's own words

Verbs: `discover` / `plan` / `coverage` / `run` / `report` / `gate`. States: `covered` / `unproven` / `unmapped` / `unknown-obligation` / `OBSOLETE`. Fix `unknown obligation` (not built) before `unproven` (built, not exercised); `unmapped` means your model missed a scoped surface. Do not re-teach the gate/baseline discipline — `tools/axon/capcov/baseline.README.md` already does, correctly; point at it rather than forking it.

Tooling gaps this method exposes (extend the tool, do not file the method down to fit it): a `mutations` field + generalized fault-matrix runner; `discover` emitting the excluded-surface count and unresolved-language list as first-class fields; `plan` emitting the unreachable-from-initial set; a `--only <transition>` selector; and wiring `capcov flows run` into the driver that currently omits it. See `TOOLING-EXTENSIONS.md` beside this file.
