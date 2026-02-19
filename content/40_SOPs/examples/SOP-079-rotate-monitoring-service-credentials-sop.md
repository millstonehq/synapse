---
id: SOP-079
type: sop
title: Rotate Monitoring Service Credentials SOP
status: approved
owner: DevOps Lead
created: '2024-03-02T14:48:11.383Z'
updated: '2025-04-30T03:16:28.365Z'
tags:
  - sop
  - monitoring-stack
summary: Rotate Monitoring Service Credentials SOP
related_process: PROCESS-048
related_systems:
  - SYSTEM-040
example: true
---

## Preconditions

- A scheduled credential rotation is due, OR a credential has been flagged as potentially compromised
- You have identified all monitoring stack components that use the credential being rotated (Grafana data source password, Prometheus remote write token, AlertManager SMTP credentials, etc.)
- A change ticket is open for this rotation and has been approved by the SRE Lead
- You have confirmed with the on-call engineer that now is an appropriate time for the rotation

## Materials/Access

- Access to the secrets management system (Vault, AWS Secrets Manager, or equivalent) where monitoring credentials are stored
- `kubectl` access to the monitoring namespace for updating Kubernetes Secrets
- Grafana admin access for updating data source credentials
- Access to all services that consume the credential being rotated
- The change ticket ID for this rotation

## Procedure

1. Generate the new credential in the secrets management system. Store the new credential value securely; do not log or paste it in Slack or tickets.
2. Identify all places where the current credential is used: search the monitoring configuration repository for references to the credential name (not the value).
3. Update the credential in the secrets management system. Keep the old credential active for now — do not revoke it yet.
4. Update the Kubernetes Secret in the monitoring namespace: `kubectl create secret generic monitoring-credentials --from-literal=key=NEW_VALUE -n monitoring --dry-run=client -o yaml | kubectl apply -f -`.
5. Restart the affected monitoring components to pick up the new secret: `kubectl rollout restart deployment/{component} -n monitoring`. Restart one component at a time and verify health before proceeding.
6. Verify the component is functioning correctly after restart by checking its health endpoint and the monitoring dashboard. Specifically confirm that metrics ingestion, alerting, and dashboard rendering are all working.
7. After all components have been restarted and verified healthy, revoke the old credential in the secrets management system.
8. Update the change ticket with completion timestamp, list of components rotated, and the date the next rotation is due.

## Validation

- All monitoring components are in a healthy, running state after the credential rotation
- Metrics are ingesting into Prometheus with no gaps in the scrape history
- Grafana dashboards are rendering data from all data sources
- AlertManager is connected to its notification channels (PagerDuty, Slack)
- The old credential has been revoked in the secrets management system

## Rollback

1. If a component fails to start after picking up the new credential, revert the Kubernetes Secret to the old credential value immediately.
2. Do not revoke the old credential until all components have been verified healthy with the new credential.
3. If the secrets management system itself is unavailable, use the emergency break-glass procedure to recover credentials.
4. Escalate to the Platform Lead if credential rotation causes a monitoring outage lasting more than 15 minutes.
