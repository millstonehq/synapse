---
id: ADR-0005
type: adr
title: Static indexes expose residue and scope their completeness claims
status: accepted
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, scip, static-analysis, completeness]
summary: SCIP facts describe the index and its unresolved call residue; a negative call-graph claim requires a separately justified witness.
---

## Context

Static structure helps identify code surfaces and connect handlers to storage,
but language features, dynamic dispatch, generated code and indexer limits can
leave edges unknown. Empty residue is meaningful only if the relevant census
is complete.

## Decision

Treat SCIP output as sourced static facts with index provenance. Preserve
unresolved residue rather than dropping it. An index must never declare its own
call graph complete. Emit `call_graph_closed` only when a separate, suitably
authoritative complete call-site census covers the precise language and source
scope, every indexed call site is reconciled to that census, and all unresolved
residue in that scope is discharged. Rules may use that independently justified
witness for scoped negation; they must not infer global absence from a partial
or unavailable index. The optional `--static scip` profile may emit residue
facts, but it must withhold the witness unless those preconditions are met.

## Alternatives considered

- Silently treating unindexed calls as no calls creates false negative claims.
- Requiring SCIP for every capcov invocation couples the baseline to external
  binaries and a partial analysis.
- Hiding residue makes the analysis look more complete than it is.

## Consequences

SCIP remains useful as a structural producer without becoming a behavioral
oracle or its own completeness authority. Users must install and pin the
indexer separately. A witness's scope must include the authoritative census,
language, source closure, indexer identity, discharged residue and known
exclusions.

## Evidence and limits

Static claim schema and closure rules are in
`packages/capabilities/src/capcov/claims/static/`; SCIP mapping and resolver
are in `packages/capabilities/src/capcov/scip/` (PR #50, `0af3b71`).
The static pipeline does not establish runtime behavior. The proposed optional
profile must not imply that SCIP automatically enumerates all dynamic call
sites or proves call-graph closure.
