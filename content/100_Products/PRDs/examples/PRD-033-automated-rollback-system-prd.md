---
id: PRD-033
type: prd
title: Automated Rollback System PRD
status: approved
owner: Product Manager
created: '2025-12-25T17:30:30.765Z'
updated: '2026-11-16T10:52:11.182Z'
tags:
  - prd
  - ci-cd-platform
summary: Automated Rollback System PRD
related_tdds:
  - TDD-032
  - TDD-033
example: true
related_standards:
  - STANDARD-038
---

## Summary

Implement an automated rollback system that detects post-deployment metric degradation and triggers a rollback without requiring manual on-call intervention. Currently, rollbacks depend on an on-call engineer noticing an alert, diagnosing the cause, and manually initiating the ArgoCD rollback process. The median time from deploy to rollback initiation is 8 minutes, during which customer-facing errors accumulate. The automated rollback system will reduce this to under 3 minutes by acting on metric signals directly from the monitoring system.

## Goals

- Reduce mean time to rollback (MTTR) from 8 minutes to under 3 minutes for deploy-caused incidents
- Eliminate the manual diagnosis step for clear-cut deploy regressions (error rate spike immediately post-deploy)
- Maintain a human approval path for ambiguous situations where automated rollback could cause more harm than good
- Reduce on-call engineer cognitive load during incidents by handling the most common recovery action automatically

## In Scope

- Automated detection of post-deployment error rate spikes and P95 latency regressions
- Automatic rollback trigger via Deployment Controller API when configured thresholds are breached
- Pre-rollback notification to on-call engineer with a configurable veto window (default: 60 seconds)
- Post-rollback notification confirming completion and prompting a follow-up investigation
- Per-service configuration of rollback thresholds and veto window duration
- Audit log of all automated rollback decisions with metric evidence

## Out of Scope

- Rollback for incidents not caused by deployments (infrastructure failures, upstream dependency outages)
- Rollback of database migrations (migrations must be backward-compatible; rollback is at the application layer only)
- Non-Kubernetes services
- Rollback based on business metrics (e.g., order completion rate) — this requires human judgment

## Users and Flows

**On-call engineers** are the primary users, though the system acts autonomously on their behalf. When a deploy-caused regression is detected, the on-call engineer receives a Slack notification: "Automated rollback triggered for `order-processing` v2.4.2 due to error rate 4.2% (threshold 1%). Rollback will proceed in 60 seconds. Click here to cancel." The engineer can let it proceed (most common) or cancel if they have information the system does not. After rollback, they receive a confirmation and are prompted to investigate root cause.

**Service owners** configure rollback thresholds per service via a YAML config file in the service repository. They set the error rate threshold, the observation window, and whether automated rollback is enabled at all. Services with complex rollback implications (e.g., services with non-reversible side effects) can opt out and require manual-only rollback.

## Requirements

- Monitor post-deployment error rate and P95 latency for a configurable observation window (default: 10 minutes) after each deployment
- Trigger rollback if error rate exceeds the configured threshold (default: 1%) for more than 2 consecutive minutes
- Send a Slack notification to the configured on-call channel before rollback with a cancel button and countdown
- Wait for the veto window before submitting the rollback to the Deployment Controller
- Cancel rollback if the on-call engineer clicks the cancel button within the veto window
- Complete the rollback within 5 minutes of submission (enforced by the Deployment Controller SLA)
- Record the rollback decision with metric evidence (error rate at trigger time, P95 latency, deployment ID)
- Support per-service opt-out of automated rollback via configuration

## KPIs

- **Mean time to rollback**: Target < 3 minutes from deploy to rollback complete for automated cases
- **False positive rate**: Fewer than 1 automated rollback per month triggered without a genuine regression
- **Veto rate**: Target < 10% of automated rollbacks vetoed by on-call engineers (indicates appropriate threshold calibration)
- **Coverage**: > 80% of services enrolled in automated rollback within 3 months of launch

## Information Architecture

- Technical design in `90_Architecture/TDDs/` (see [[TDD-032|TDD-032]] and [[TDD-033|TDD-033]])
- Post-deployment monitoring configuration lives with each service's deployment config
- This PRD in `100_Products/PRDs/`

## Data Model

- **RollbackTrigger**: `id`, `deployment_id`, `service_name`, `trigger_metric`, `trigger_value`, `threshold`, `detected_at`, `veto_expires_at`, `status` (Pending/Vetoed/Executed/Cancelled)
- **RollbackDecision**: Immutable audit record: `trigger_id`, `decision` (Execute/Veto), `decided_by` (system or engineer identity), `decided_at`, `rollback_completed_at`
- **ServiceRollbackConfig**: `service_name`, `enabled`, `error_rate_threshold`, `latency_p95_threshold_ms`, `observation_window_minutes`, `veto_window_seconds`, `notification_channel`

## Non-Functional

- Rollback trigger decision must be made within 30 seconds of threshold breach detection
- Veto Slack notification must be delivered within 10 seconds of trigger decision
- System must not trigger rollback if the service has no recent deployment (within 30 minutes)
- All rollback actions must be logged before execution; no silent rollbacks

## Constraints

- Rollback is always to the previous known-good deployment version; no arbitrary version selection
- Must use the Deployment Controller API for rollback; no direct ArgoCD API calls
- Metric data source must be the existing Prometheus/Alertmanager stack; no new monitoring infrastructure
- Database migrations are explicitly excluded; application-layer rollback only

## Risks

- **False positives cause unnecessary rollbacks** of healthy deployments during transient spikes. Mitigation: require 2 consecutive minutes above threshold rather than a single data point; tune thresholds per service based on historical baseline.
- **On-call engineer is unavailable during veto window**, meaning the rollback proceeds even if the engineer would have vetoed. Mitigation: this is acceptable behavior by design; when in doubt, roll back.
- **Rollback worsens the incident** if the previous version had a different bug. Mitigation: this is rare and addressed by the veto window; engineers who know their service well will cancel inappropriate rollbacks.

## Milestones

### M1: Metric Monitoring and Trigger Detection (Weeks 1-2)

#### Deliverables

- Post-deployment monitoring job that watches error rate and latency for 10 minutes after each deployment
- Threshold evaluation logic with configurable per-service settings
- Trigger detection producing a `RollbackTrigger` record

#### Acceptance Criteria

- Trigger correctly fires for a simulated error rate spike in staging
- Trigger does not fire for transient 1-minute spikes below the 2-consecutive-minute requirement

### M2: Veto Notification and Rollback Execution (Weeks 3-4)

#### Deliverables

- Slack notification with cancel button and countdown timer
- Veto window handling with cancel button callback
- Rollback submission to Deployment Controller on veto window expiry
- Post-rollback confirmation notification

#### Acceptance Criteria

- On-call engineer receives Slack notification within 10 seconds of trigger
- Cancel button successfully prevents rollback submission
- Rollback completes within 5 minutes of submission in staging test
