---
name: verification-triage
description: Use when deciding what to verify and how deeply under time pressure — reimplementing or rebuilding a system clean-room, driving a coverage/completeness tool (capcov), or when a "completeness is a vector" model tempts you to max every axis before shipping. Symptoms — "I could validate one thing perfectly or cover everything fast", breadth-vs-depth, "is this verified enough or do I go deeper", rigor instinct vs limited time, differential/parity testing against an existing system.
---

# Verification Triage

## Overview

A completeness model tells you the full denominator. It does not tell you to fill every cell before shipping. **Verify to the depth of observable distinguishability, breadth-first, with the running original as your oracle. Depth tracks blast radius, never the vector uniformly.**

## When to use

- Rebuilding or reimplementing a system (clean-room) with limited time.
- Running a coverage tool that enumerates far more obligations than you can deeply check.
- A formal model (obligations, "completeness is a vector") is tempting you to perfect one axis.
- You are asking "is this verified enough, or do I go deeper?"

## The reasoning rule

Sort every obligation by the **cost of being wrong**, not by how interesting it is to verify.

- **A missing obligation** (a surface or entity you never discovered) is an unbuilt feature. Cost unbounded, found in production. So the *list* must be complete.
- **A shallowly-verified obligation** (found, smoke-tested) is a bug. Cost bounded, found through use. So verify the list shallow.

Therefore: **complete the list cheap, verify it shallow, deepen only the spine.** Breadth before depth. One endpoint perfected next to thirty-nine undiscovered is worse than forty that each answer correctly.

## "Verified enough" = observable distinguishability

An obligation is verified enough when a **differential test against the oracle** (the running original) agrees on the happy path and on every outcome class a caller can tell apart. Stop when a wrong answer would be invisible to every client — all-500s-look-alike exceptions, internal helpers, unexercised paths. Parity against the oracle beats abstract branch coverage: it is checked against ground truth, not against a model that can be wrong the same way twice.

## The spine — deep regardless of cost

State mutations. Distinguishable error contracts. Auth and authz branches. A wrong write, or a 403 that leaks as a 200, is silent and expensive. Depth tracks blast radius.

## Quick reference

| Do fully (cheap, essential) | Do shallow (cheap, high value) | Defer (expensive, marginal) |
|---|---|---|
| surface + entity discovery; the obligation list | oracle parity per surface | sound call-graph resolution |
| blind-spot enumeration | contract-shape checks | per-branch/exception obligations to uniform depth |
| | | hand-authored transition models (spine only) |

Run order: discover → contract-level obligations → rebuild → observe/reconcile against the oracle → eyeball the blind-spot list → deepen the spine.

## Blind spots are the stopping rule

Enumerate what the tool could not resolve (getattr/eval/dynamic dispatch) **early, not last** — green over an unresolved dispatch is a stale-green lie. You do not automatically conquer the hard cases; you *list* them and eyeball them by hand. That is a ten-minute review, not a day building a perfect resolver. It is the escape hatch from "I could validate one thing all day."

## Common mistakes

- **Uniform depth (the rigor trap):** gold-plating error paths no caller can distinguish. Depth tracks blast radius, not the vector.
- **Trusting green before the blind-spot map:** a covered or "converged" result over an unresolved edge is not complete. Converged is not complete.
- **Treating the model as a gate:** the vector is a dashboard. Ship consciously at partial depth on the expensive axes, complete on the cheap ones, and know exactly what you traded.

Anchors the practice side of capcov's design. Theory and citations: ADR-0001 (capcov's literature foundations).
