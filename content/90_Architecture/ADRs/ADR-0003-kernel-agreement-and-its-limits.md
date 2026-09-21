---
id: ADR-0003
type: adr
title: Kernel agreement is useful but bounded evidence
status: accepted
owner: capabilities
created: '2026-09-17T00:00:00.000Z'
updated: '2026-09-17T00:00:00.000Z'
tags: [adr, claims, souffle, testing]
summary: Compare Python and Souffle closure results when both execute, while stating which semantics and environment were actually checked.
---

## Context

A single evaluator can have implementation defects. An independent Datalog
runtime provides a useful cross-check, but the two paths do not currently
implement every part of verdict semantics independently.

## Decision

Keep a Python kernel for the portable/default path and optional interpreted or
compiled Souffle evaluators for named invocations. Compare all applicable
relations and verdicts when the requested kernels execute. A requested kernel
that cannot start is unavailable, not a disagreement and not a passing
comparison. A single selected kernel is never reported as differential
agreement. Preserve the distinction between closure evaluation and shared
Python-side claim folding, quantifiers, missing-premise policy and certificate
construction.

## Alternatives considered

- Trusting only one kernel gives less independent defect detection.
- Treating an unavailable kernel as an empty result manufactures disagreement.
- Calling Python-only output “two-kernel agreement” overstates execution.

## Consequences

Kernel selection and availability must appear in reports. Agreement raises
confidence only in the code paths actually compared; it does not establish
producer truth, rule correctness, or independence of shared semantics.

## Evidence and limits

The opt-in evaluator and differential handling are in
`packages/capabilities/src/capcov/claims/differential.py` at `79c08a6`.
Current observation measurement exercised Python only. The saved run reports
Souffle unavailable and therefore is not a three-kernel result. Replay-pack
agreement across Python, interpreted Souffle and compiled Souffle remains a
separate pending integration gate.
