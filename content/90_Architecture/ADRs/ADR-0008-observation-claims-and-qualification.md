---
id: ADR-0008
type: adr
title: Capability observation claims are distinct from model qualification
status: accepted
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, observation, qualification, claims]
summary: Judge real capability-check receipts on their observational premises while keeping model conformance and migration qualification explicitly separate.
---

## Context

The differential capability checks exercise much more of the port than the
single-operation replay model currently covers. Their results should be
consumable without making Shen a prerequisite, but an observed PHP/Go match is
not proof of the model, unobserved cases or the full migration boundary.

## Decision

Add a narrow `observations_agree` claim derived from a capability receipt's
observed rows, scenario coverage and comparison policy. The claim can be
supported, refuted or pending based on those premises alone. Keep
`model_conformance` explicitly unassessed where no model evidence is bound;
do not translate the result into correctness, complete capability parity or
migration qualification. Preserve the existing four-cell coverage artifact
and report the observation verdict beside it.

## Alternatives considered

- Requiring a Shen model for every check excludes useful observations from
  existing capabilities.
- Treating observed agreement as model conformance overstates the evidence.
- Replacing the four-cell artifact with a new verdict mixes distinct
  denominators and consumers.

## Consequences

The bridge can reuse Lane A checks incrementally. Each check must emit a
complete receipt with per-side observations, policy provenance, scenario
coverage, and setup failures. The claim remains bounded to those cases and that
policy.

## Evidence and limits

The observation producer/consumer bridge is in the companion producer's
`test-harness/observation/` and capcov's `claims/observation/` at `ce6da40`,
`5503b35` and `79c08a6`. The recorded judge crossing used a synthetic wire
fixture. No live oracle receipt has yet been demonstrated, so the design is
implemented but the intended live outcome remains unverified.
