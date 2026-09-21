---
id: ADR-0012
type: adr
title: Defer a native Shen checker and persistent worker until measured
status: deferred
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, shen, performance, build]
summary: A native Shake/Yggdrasil checker or service is justified only by exact reproducible builds, semantic equivalence and measured end-to-end savings.
---

## Context

Repeated Shen startup and toolchain setup may add cost, but orchestration,
lock waits, fixtures, hooks and other tests can dominate a developer cycle.
Building a binary or daemon without timing the actual critical path risks
adding another maintained system without reducing elapsed time.

## Decision

Keep the existing shen-go path as the reference implementation. Do not treat a successful
`bifrost --shake` probe as a compiled Stage D checker. Before adopting a native
checker, bind checker source order and digests, model closure, Bifrost and
Yggdrasil versions/digests, generated Go, toolchain, flags and final binary.
Differentially test all positive, negative, skipped and adversarial model cases
against the reference. Treat disagreement as operational failure. Consider a
local worker only if repeated requests materially improve measured end-to-end
time and isolation, cancellation, limits and identity checks are demonstrated.

## Alternatives considered

- Immediately building a worker assumes process startup is the bottleneck.
- Replacing shen-go after a narrow sample risks silent semantic drift.
- Reusing a binary without all build inputs permits stale executable authority.

## Consequences

Compilation and service work are deferred. Report cold and warm measurements
separately and include lock wait. If native execution is already sub-second or
irrelevant to total cycle time, optimize orchestration and test selection first.

## Evidence and limits

The measured Stage D minimal fixture took 5.37 seconds; a Python observation
fixture took 0.64 seconds, and a cold Nix attempt spent 60 seconds waiting for
another lock holder without executing Nix. A native Shake Fibonacci probe is
not a Stage D compilation. No compiled Stage D binary, equivalence corpus or
persistent service is claimed.
