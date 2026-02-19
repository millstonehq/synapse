---
id: SOP-084
type: sop
title: Update Customer Portal Feature Flag SOP
status: approved
owner: DevOps Lead
created: '2024-09-05T16:24:50.533Z'
updated: '2025-01-20T01:16:24.842Z'
tags:
  - sop
  - customer-portal
summary: Update Customer Portal Feature Flag SOP
related_process: PROCESS-069
related_systems:
  - SYSTEM-044
example: true
---

## Preconditions

- The feature flag change is documented in an approved change ticket
- The flag being updated exists in the feature flag console and the change is for a defined, understood flag
- The impact scope of the flag is known (what percentage of users, which accounts, or which portal features are affected)
- On-call engineer is aware of the flag change and is monitoring the portal dashboards

## Materials/Access

- Access to the feature flag management console (LaunchDarkly or equivalent)
- Access to Grafana portal monitoring dashboard
- Change ticket ID referencing the flag update
- Slack access to #customer-portal-deployments

## Procedure

1. Post in #customer-portal-deployments: "Updating feature flag [FLAG-KEY] for [CHANGE-TICKET]. Target: [audience/percentage]. On-call: [name]."
2. Open Grafana portal dashboard and note current baseline metrics: error rate, P95 latency, and active session count.
3. In the feature flag console, navigate to the flag identified in the change ticket and review its current configuration before making any changes.
4. Apply the change as described in the change ticket (toggle on/off, percentage rollout adjustment, audience rule update).
5. Save the change and verify it is applied in the console (check the flag's evaluation status and targeting rules).
6. Monitor Grafana for 10 minutes after the flag change; check error rate and latency for any degradation.
7. If the flag enables a new UI component or flow, verify the affected flow is functioning correctly by testing the portal in the affected environment.
8. Post in #customer-portal-deployments: "Flag [FLAG-KEY] updated. Metrics stable. Change: [brief description of what changed]."
9. Update the change ticket: mark as completed with timestamp and a note on the flag's current state.

## Validation

- Feature flag console shows the flag in the expected state (on/off, correct targeting rules)
- Error rate has not increased more than 0.1% following the flag change
- P95 latency is within 100ms of pre-change baseline
- If the flag controls a customer-facing feature, a smoke test confirms the feature works as expected

## Rollback

1. Post in #customer-portal-deployments: "REVERTING flag [FLAG-KEY]. Reason: [brief description]."
2. In the feature flag console, revert the flag to its previous state (toggle off, restore previous percentage, or restore previous targeting rules).
3. Verify the revert is applied in the console's evaluation log.
4. Monitor Grafana for 5 minutes and confirm metrics return to baseline.
5. Update the change ticket to reflect the rollback with timestamp and reason.
