---
id: TDD-034
type: tdd
title: Deployment Approval Workflow TDD
status: approved
owner: Principal Engineer
created: '2024-03-13T10:15:42.607Z'
updated: '2025-12-22T03:08:24.554Z'
tags:
  - tdd
  - ci-cd-platform
summary: Deployment Approval Workflow TDD
related_adrs:
  - ADR-0027
  - ADR-0029
example: true
---

## Summary

Design the Deployment Approval Workflow, an asynchronous gate system that requires one or more designated approvers to explicitly authorize a production deployment before the Deployment Controller proceeds. The workflow integrates with GitHub Actions (CI trigger), Slack (approval UI), and ArgoCD (deployment execution) to provide a lightweight but auditable approval gate that does not require engineers to log into multiple systems.

This design integrates with the GitHub Actions-based CI pipeline described in [[ADR-0027|ADR-0027]] and the Harbor artifact registry described in [[ADR-0029|ADR-0029]].

## Overview

- **Async gate model**: When a deployment is queued, the Deployment Controller creates an `ApprovalRequest` and pauses; designated approvers receive a Slack notification with approve/reject buttons; the Controller resumes when approved or cancels when rejected or timed out
- **RBAC-driven approver lists**: Each service has a configured approver group (e.g., `service-owners`, `platform-leads`); approvals from engineers not in the group are rejected with a descriptive error
- **Configurable gate modes**: Services can configure `auto` (skip approval for low-risk services), `required` (always require approval), or `conditional` (require approval only outside business hours or above a risk score threshold)
- **Audit trail**: Every approval decision is persisted with approver identity, timestamp, and the deployment context (service, version, commit SHA)
- **Timeout with escalation**: If no approval is received within the configured window (default 4 hours), the request expires and an escalation notification is sent to the service owner

## Architecture

- **Approval Controller**: Orchestrates the workflow state machine; watches `ApprovalRequest` objects; transitions state from `Pending` → `Approved`/`Rejected`/`Expired`
- **Slack Integration**: Posts formatted approval cards to designated channels; handles button action callbacks via Slack API webhook; translates Slack user IDs to internal engineer identities
- **RBAC Resolver**: Looks up approver group membership from the internal directory service; validates that the acting approver is authorized for the service being deployed
- **Persistence Layer**: PostgreSQL-backed storage for `ApprovalRequest` records and `ApprovalDecision` audit entries; supports querying approval history by service and time range
- **Deployment Controller Hook**: A webhook endpoint that the Deployment Controller polls or receives callbacks on to learn when an approval request is resolved

## Information Model

- **ApprovalRequest**: Fields: `id`, `service_name`, `version`, `commit_sha`, `requester`, `approver_group`, `gate_mode`, `status` (Pending/Approved/Rejected/Expired), `created_at`, `expires_at`
- **ApprovalDecision**: Immutable audit record: `id`, `request_id`, `approver_identity`, `action` (Approve/Reject), `comment`, `decided_at`
- **ApproverGroup**: Configuration entity mapping a group name to a list of engineer identities; managed via GitOps in the platform config repository
- **GateConfig**: Per-service configuration for gate mode, approver group, timeout window, and notification channel; stored as a Kubernetes ConfigMap

## Interfaces

- `POST /v1/approvals` - Create a new approval request (called by Deployment Controller)
- `GET /v1/approvals/{id}` - Poll approval request status
- `POST /v1/approvals/{id}/decide` - Submit an approval decision (used for CLI and API-based approval, separate from Slack)
- `POST /webhooks/slack/actions` - Slack action callback endpoint for approve/reject button interactions
- `GET /v1/approvals?service={name}&since={date}` - Query approval history for audit reporting

## Files and Layout

```
cmd/approval-workflow/main.go   - Entry point, HTTP server and controller startup
internal/
  controller/
    approval.go                 - ApprovalRequest state machine controller
    expiry.go                   - Timeout and expiry job
  slack/
    notifier.go                 - Send approval card to Slack
    callback.go                 - Handle Slack action webhook
  rbac/
    resolver.go                 - Approver group membership lookup
  store/
    requests.go                 - PostgreSQL ApprovalRequest CRUD
    decisions.go                - Immutable ApprovalDecision audit log
deploy/
  helm/                         - Helm chart
migrations/                     - PostgreSQL schema
```

## Work Plan

1. **Phase 1 - Core State Machine (Week 1-2)**: ApprovalRequest model and PostgreSQL persistence; controller state transitions; REST API for create/poll/decide
2. **Phase 2 - Slack Integration (Week 3)**: Send approval card on request creation; handle approve/reject button callbacks; map Slack user to engineer identity
3. **Phase 3 - RBAC Resolver (Week 4)**: Integrate with directory service for group membership; reject approvals from unauthorized engineers; unit tests for edge cases
4. **Phase 4 - Deployment Controller Integration (Week 5)**: Wire approval gate into the Deployment Controller's pre-deploy check; end-to-end test in staging
5. **Phase 5 - Expiry and Escalation (Week 6)**: Implement timeout expiry job; escalation notification on expiry; configurable per-service timeout windows
6. **Phase 6 - Audit Reporting (Week 7)**: Query API for approval history; Grafana panel showing approval rate and time-to-approve; production rollout

## Risks and Mitigations

- **Risk**: Slack API is unavailable, blocking all approval notifications and leaving engineers unaware of pending requests. **Mitigation**: Email fallback notification if the Slack API call fails after 2 retries; approval can always be submitted via the CLI or REST API independent of Slack.
- **Risk**: Approver group configuration is stale and an authorized approver is blocked while an unauthorized engineer has access. **Mitigation**: Cache approver group membership for a maximum of 5 minutes; allow service owners to override via an emergency approval path with additional audit logging.
- **Risk**: Approval workflow becomes a bottleneck for high-frequency deploying teams using `auto` gate mode. **Mitigation**: Auto gate mode can be set per service; monitor approval wait time as a DORA lead time component and alert if median wait exceeds 30 minutes.
