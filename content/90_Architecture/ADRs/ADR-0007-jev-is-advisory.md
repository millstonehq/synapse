---
id: ADR-0007
type: adr
title: Jev output is a triage assumption, never qualification authority
status: accepted
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, jev, advisory, trust]
summary: Learned judgments may rank bounded probes but cannot assert facts, completeness, compatibility, or qualification.
---

## Context

An advisory model can help prioritize missing evidence, but prompts and framing
can dominate its answers. Its output is not an observation from the PHP or Go
system and cannot carry producer authority.

## Decision

Represent Jev results only as assumption-modality evidence from the Jev
producer class. Bound candidate selection to IDs discovered independently and
include a mandatory no-match option. Pattern assessment receives typed
evidence, exclusions and known missing evidence without a hypothesis-bearing
preamble; repeated meaning-preserving perturbations expose answer instability.
Rules must not let Jev assert facts, witnesses, close relations or qualify a
claim.

## Alternatives considered

- Letting the model invent candidates expands the choice set without evidence.
- Treating a confidence score as an observation turns a heuristic into
  unreviewed authority.
- A free-form explanation invites framing effects that cannot be measured.

## Consequences

Jev can reduce triage time but adds cost and may be unstable or wrong. Reports
must preserve its advisory status and perturbation spread. Human review and
authoritative producers remain responsible for disposition.

## Evidence and limits

The PR #52 source at `54e2b89` is in
`packages/capabilities/src/capcov/claims/jev_patterns.py` and
`packages/capabilities/experiments/claim-semantics/jev/`. That experiment
reported opposite unanimous answers under two different framings, then 6/8
hand-verified pattern assessments with 4/24 perturbed cells unstable. These
historical observations support the boundary, not predictive accuracy. Jev
remains an experiment; it cannot resolve a pending or unsupported verdict.
