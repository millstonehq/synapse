---
id: ADR-0009
type: adr
title: Freeze producer intent and keep policy admission external
status: accepted
owner: observation
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, observation, provenance, privacy]
summary: Bind expected run identity before fixture setup, preserve private byte-pair evidence, and admit only externally supplied exact bytes.
---

## Context

The process that observes behavior also writes a receipt. Without a pre-run
identity, it can change the claimed inputs after seeing results. Normalization
may mask differences, but an unreviewed mask can turn a real divergence into a
false agreement. Receipt-local admissions also let the judged artifact vouch
for itself.

## Decision

Require a caller-supplied unique run nonce and immutable invocation identity
captured before fixture provisioning. Bind candidate and incumbent identities,
fixture expectation, source expectation and policy identity. Record fixture
setup as producer attestation, not independent verification. Keep raw
observations and masked byte pairs in a private, access-restricted run packet;
publish the receipt only after that packet is durably verified. Scan both raw
and masked response material for credentials. The judge ignores receipt-local
admission and consumes the exact externally digested admission bytes, without
reopening a mutable path. Missing admission leaves the related claim pending.

## Alternatives considered

- Hashing the invocation after the run allows the producer to select its own
  identity after observing output.
- Recording only that fields were normalized hides the bytes that differ.
- Putting review rows in the receipt creates self-admission.
- Hashing one admission file and reopening it later permits a time-of-check /
  time-of-use substitution.

## Consequences

The run produces both public and private artifacts and requires unique storage
per nonce. A digest proves byte identity, not that a human approved the policy;
the caller must obtain and retain genuine review. The privacy scan is a
specific control, not a guarantee that all sensitive data is impossible.

## Evidence and limits

Producer hardening commits `092e030` and `0bcb44a`; consumer admission-byte fix
`97c3b12`. Technical review covered nonce reuse, immutable-field mutation,
masked packet binding and the admission replacement race. Fixture setup remains
producer-attested. No real oracle receipt or human admission is claimed.
