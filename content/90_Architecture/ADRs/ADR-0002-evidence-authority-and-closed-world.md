---
id: ADR-0002
type: adr
title: Typed evidence, producer authority, and witnessed negation
status: accepted
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, claims, evidence, trust]
summary: Claims are derived from typed, attributable evidence; absence is usable only within an explicitly witnessed complete scope.
---

## Context

A verdict assembled from facts can hide who observed them, whether a statement
is an assumption, and whether an empty relation means “none exist” or “none
were collected.” Those distinctions are essential for PHP-to-Go comparison.

## Decision

Represent evidence with a relation, typed values, context, evidence identifier,
producer identity and modality. Keep observations, assumptions, completeness
witnesses, compatibility witnesses and claims distinguishable. Validate that a
producer class is authorized to assert each relation. Permit negation only when
a matching completeness witness covers the same relation and scope. Require an
explicit compatibility witness for joins across evidence contexts. Missing
premises stay unresolved; they are not silently treated as false.

## Alternatives considered

- A hand-maintained obligation ledger is straightforward but makes each new
  behavior depend on a person writing and binding another test.
- Treating missing rows as false makes negative claims cheap but confuses
  unobserved behavior with observed absence.
- Letting any producer assert any relation removes useful separation between
  measurement, modeling, review and inference.

## Consequences

Every claim can explain its derivation and missing premises. Completeness and
cross-context compatibility become explicit work. Hashes bind bytes and
provenance; they do not establish that an observation is truthful. Producer
authority tables and witness scope require independent review.

## Evidence and limits

Implemented in `packages/capabilities/src/capcov/claims/validation.py` and
`evaluator.py` at PR #50 (`0af3b71`). Static and replay schemas are packaged
with their rule packs. This is a fail-closed policy design, not a formal proof
that every producer or rule is sound.
