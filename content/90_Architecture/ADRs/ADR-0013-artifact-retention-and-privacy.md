---
id: ADR-0013
type: adr
title: Separate reviewed source artifacts from bulky private run outputs
status: proposed
owner: repository-maintainers
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, artifacts, privacy, operations]
summary: Version small reviewable fixtures and manifests; retain large or sensitive run material by immutable digest with bounded access and retention.
---

## Context

Repeated machine-generated receipts create repository churn and retain raw
observations longer and more broadly than review requires. Local paths,
credentials, tenant data and internal names can leak through generated output.

## Decision

Keep schemas, compact golden fixtures, reviewed policy manifests and provenance
summaries in version control. Store bulky campaign outputs and sensitive raw
packets outside Git, address them by immutable digest, and publish a minimal
manifest with size, producer identity, access class and retention policy.
Scan complete outgoing diffs and public generated artifacts for secrets,
private identifiers and local paths. Keep raw and masked observations in
private storage with narrower access than the public receipt.

## Alternatives considered

- Committing every receipt preserves local discoverability but creates
  unbounded churn and broad retention.
- Publishing only an opaque pointer makes evidence difficult to retrieve and
  verify without a retention contract.
- Publishing raw observations simplifies review but increases privacy risk.

## Consequences

The artifact store, retention owner, retrieval procedure and digest verification
must be established before moving existing evidence. Garbage collection can
reclaim unreachable Git objects but cannot remove reachable history. Privacy
scans are necessary checks, not exhaustive proof of absence.

## Evidence and limits

The experiment review recorded substantial generated receipt churn and a
pattern-based outgoing-diff scan. No artifact-store migration or retention
service is claimed. This decision remains proposed until storage, access and
retention are assigned and tested.
