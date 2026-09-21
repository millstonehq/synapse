---
id: ADR-0010
type: adr
title: Separate evidence identity by lifecycle stage and refuse unverifiable reuse
status: accepted
owner: replay
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, provenance, cache, replay]
summary: Capture, comparison, export and judgment have different inputs; reuse requires exact identities at the layer being reused.
---

## Context

A single commit-wide key invalidates too much for exporter-only changes and may
still omit behaviorally relevant inputs. Conversely, treating an old result as
current because a few known files match can preserve stale authority.

## Decision

Define separate identities for the SUT and build, incumbent/oracle closure,
fixture and seed, request tape, mutant set and implementation, campaign policy,
capture producer, comparison policy, exporter, model, checker, rule pack,
evaluator and receipt schema. Reuse a capture campaign only when every
behavioral producer input matches. Re-export only from retained captures whose
identity is exact. Recompute judgments when comparison or rules change unless
complete raw observations support recomputation; never relabel a stored verdict
as a new observation. Preserve the original producer provenance and record
accept/refuse reasons. Missing legacy identity means refusal.

## Alternatives considered

- Whole-commit identity is easy but couples documentation/export changes to
  expensive producer runs.
- A small handwritten allowlist can miss active dependencies and create false
  cache hits.
- Reconstructing historical inputs from today's source misstates what was
  actually executed.

## Consequences

Identity schemas and exporters become more explicit. Any unbound behavior or
authority input must fail closed until the identity graph is complete. Existing
campaigns without captured identity remain useful as historical records, not
reusable evidence.

## Evidence and limits

The current SUT provenance implementation remains isolated pending fixes to
export enforcement, incumbent application closure, verdict semantics, producer
and toolchain closure, and path privacy. The retained 98-mutant artifact lacks
campaign identity and was refused. No campaign was rerun or reused. See the
public replay and export sources under
`packages/capabilities/src/capcov/claims/` for the currently published
boundaries. This ADR records the intended design, not completed campaign-cache
qualification.
