---
id: ADR-0014
type: adr
title: Freeze interfaces and bound integration work around executable outcomes
status: accepted
owner: repository-maintainers
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, process, testing, review]
summary: Parallel work proceeds only across frozen contracts; tests and reviews are staged by risk, with bounded integration runs and explicit unknowns.
---

## Context

Parallel implementation repeatedly produced individually passing components
that disagreed at their shared wire boundary. Broad suites on a changing tree
consumed time without yielding clean evidence. Several important trust-boundary
defects were found only by independent negative-case review.

## Decision

Name one observable outcome and its proving command before implementation.
Freeze wire schemas, source identities, private/public artifact layout and exit
semantics before parallel producer/consumer work. Use isolated worktrees and
one integration owner. Review provenance, authority, admission, comparison and
privacy narrowly, with one finding-specific re-review after fixes. Run cheap
focused checks during coding, then one coherent regression and CI gate. Keep
each integration run bounded to ten minutes; split or defer a longer campaign
instead of making it a prerequisite for ordinary iteration. Serialize shared
heavy work with the lock. Preserve UNKNOWN or pending until its authoritative
producer premise exists. Record implementation, tests, execution, review,
publication and qualification as separate states.

## Alternatives considered

- Maximizing agent count without a frozen interface increases integration
  rework.
- Repeating broad suites after each small edit adds cost without improving
  trust-boundary coverage.
- Treating passing unit tests as live parity conflates code, execution and
  qualification.

## Consequences

The critical path should be one producer-to-judge crossing plus only an
independently useful repair. Lock waits and test time are recorded separately.
If two iterations fail to advance the end-to-end path, change approach and
state why. Required repository hooks remain required; schedule and scope work
so they do not become surprise multi-hour gates.

## Evidence and limits

Public workflow and integration history are recorded in `EXPERIMENT-PLAN.md`,
`EXPERIMENT-HANDOFF.md`, and `.github/workflows/ci.yml`. A real wire contract
reduced one integration round to focused review and rework, but the historical
crossing still used a synthetic receipt. The process is intended to reduce
avoidable iteration cost; it does not promise that every complete campaign
fits within ten minutes.
