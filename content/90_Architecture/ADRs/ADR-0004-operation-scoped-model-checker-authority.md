---
id: ADR-0004
type: adr
title: Scope model-checker authority to the checked operation
status: accepted
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, claims, shen, authority]
summary: A typed Shen result and reviewer admission qualify only the exact model-operation-checker-certificate tuple they name.
---

## Context

Stage D checks the model's well-formedness judgements, while some operations
may have live witnesses and others may be skipped. A global “model checked”
fact would let checked coverage flow to operations never examined. The model
also cannot be trusted to declare its own checker or admission.

## Decision

Keep Shen model checking an explicit producer profile. Emit global structural
well-formedness separately from per-operation checked coverage. Qualification
joins the exact model digest, operation, checker identity/name, checker version,
native executable digest and semantic certificate. Reviewer admission is
external to the receipt and binds that same six-field tuple. Placeholder
identities and receipt-local
self-admission grant no authority. A skipped operation produces no operation
authority and remains pending.

## Alternatives considered

- One global certificate is simpler but permits unchecked operations to inherit
  another operation's result.
- A model-supplied certificate or receipt-local signature lets the evidence
  being judged create its own authority.
- Refusing to distinguish structural validity from operation evidence hides
  which part of checking was actually performed.

## Consequences

Schemas, rules, exporter authority, expected tables and diagnostics must evolve
together. A valid checker result is not reviewer admission. A reviewer row
authenticates a scoped policy decision only under the repository's external
identity controls; a digest alone does not identify a human.

## Evidence and limits

The operation-scoped schema and authority join are in
`packages/capabilities/src/capcov/claims/replay/` at `c684099` and
`79c08a6`. Focused authority tests and technical review cover exact joins and
placeholder refusal. The complete replay corpus has not yet been demonstrated
across all authoritative kernels, and no human checker admission is claimed.
