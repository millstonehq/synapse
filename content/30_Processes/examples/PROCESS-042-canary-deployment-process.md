---
id: PROCESS-042
type: process
title: Canary Deployment Process
status: approved
owner: Engineering Manager
created: '2024-03-08T13:00:34.098Z'
updated: '2025-05-15T22:22:11.159Z'
tags:
  - process
  - ci-cd-platform
summary: Canary Deployment Process
related_standards:
  - STANDARD-042
  - STANDARD-041
related_sops:
  - SOP-068
  - SOP-065
related_systems:
  - SYSTEM-035
example: true
---

## Purpose

This process governs canary deployments — a deployment strategy in which a new version of a service receives a small, controlled slice of production traffic while the previous version continues serving the majority. Canary deployments reduce the blast radius of production changes by providing real-world validation before full rollout. This process applies to all services that are configured to support canary traffic splitting via the service mesh or ingress controller.

## Scope

- Production canary deployments for application services with canary traffic splitting configured
- Automated and manual canary promotion workflows
- Services enrolled in the canary deployment program (minimum 80% test coverage and active SLO monitoring required)
- Does not apply to batch jobs, one-off scripts, or services without HTTP/gRPC traffic to split

## Roles and Responsibilities

- **Change Owner**: Initiates the canary, monitors the canary's health metrics, and makes promotion or abort decisions at each traffic increment
- **On-Call Engineer**: Monitors broad service health during the canary and escalates if anomalies appear in non-canary traffic
- **SRE**: Configures and validates the traffic splitting rules in the service mesh; available for escalation if traffic splitting behaves unexpectedly

## Triggers

- A merged pull request for a medium or high-risk service change where the team has opted into canary deployment
- An automated canary pipeline is triggered by a new tagged release on an enrolled service

## Inputs

- Signed and tagged container image passing all CI gates
- Approved deployment record noting the canary strategy and traffic increment plan
- Defined canary success criteria: error rate delta, latency delta, and business metric thresholds

## Outputs

- Service fully promoted to the new version, or canary aborted and service fully reverted
- Canary deployment report recording traffic percentages, metrics at each increment, and final outcome
- Deployment record updated with canary history

## Steps

1. Change Owner creates a deployment record specifying canary strategy and the increment plan (e.g., 1% → 10% → 25% → 100%)
2. SRE validates that traffic splitting is configured correctly and that the canary deployment target is isolated from the stable deployment
3. Change Owner deploys the canary at 1% traffic and starts a 15-minute observation window
4. Change Owner compares canary error rate and latency against the stable baseline; if canary metrics exceed the defined thresholds, abort immediately
5. If metrics are within thresholds, increment traffic to 10% and observe for another 15 minutes
6. Repeat traffic increments per the approved plan, observing for the defined period at each increment
7. If all checkpoints pass, Change Owner promotes the canary to 100% and terminates the stable deployment
8. Change Owner closes the deployment record with canary metrics summary and promotion timestamp

## Controls

- Canary abort must occur within 5 minutes of a threshold breach being detected; delays require escalation to the on-call engineer
- Canary traffic must not remain at a partial percentage overnight without active ownership and documented justification
- Canary deployments must produce a machine-readable metrics report that is attached to the deployment record
