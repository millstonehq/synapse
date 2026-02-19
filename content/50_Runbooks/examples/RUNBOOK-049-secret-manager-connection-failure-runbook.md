---
id: RUNBOOK-049
type: runbook
title: Secret Manager Connection Failure Runbook
status: approved
owner: On-Call Engineer
created: '2025-03-22T01:45:47.338Z'
updated: '2025-09-28T18:09:48.098Z'
tags:
  - runbook
  - ci-cd-platform
summary: Secret Manager Connection Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-033|Secret Manager]]
- **Owner team**: Platform Engineering / Security Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: HashiCorp Vault / AWS Secrets Manager / Kubernetes

## Alerts

- `SecretManagerConnectionFailed` — CI pipeline jobs are failing with "connection refused" or "dial tcp: i/o timeout" when attempting to retrieve secrets from the secrets manager at job startup
- `SecretManagerAuthTokenExpired` — Pipeline jobs are failing with 401/403 responses from the secrets manager, indicating the OIDC federation token or AppRole credentials have expired or been revoked
- `SecretManagerResponseTimeP95High` — The secrets manager is responding to pipeline secret fetch requests with P95 latency above 5 seconds, causing job startup timeouts

## Diagnosis Steps

1. **Confirm the failure type** - Review the pipeline job logs to find the exact error when secrets are fetched; distinguish between connection refused (service down), authentication failure (credential issue), and timeout (performance degradation).
2. **Check secrets manager service health** - If using Vault, check the Vault UI or run `vault status` from a pod with Vault access; for AWS Secrets Manager, check the AWS Health Dashboard for the relevant region.
3. **Check OIDC/authentication configuration** - If using OIDC federation, verify the OIDC provider configuration in the secrets manager matches the CI platform's JWKS endpoint; check if the trust policy has been modified recently.
4. **Check secrets manager network accessibility** - From a runner host or pipeline pod, attempt to connect to the secrets manager endpoint: `curl -I https://vault.internal:8200/v1/sys/health`; check Security Group or network policy rules if connection is refused.
5. **Review Vault/secrets manager audit logs** - Check the secrets manager's audit log for authentication failures or unusual access patterns that may indicate a misconfiguration or credential revocation.

## Remediation Steps

1. **If secrets manager is down (Vault sealed or AWS outage)**: For Vault, initiate unseal procedure per the Vault operations runbook; for AWS Secrets Manager regional outage, switch to the backup region if configured and notify teams.
2. **If authentication is failing due to expired AppRole credentials**: Rotate the AppRole secret ID per the Rotate CI/CD Service Account Credentials SOP and update the CI platform's secret reference.
3. **If OIDC trust policy has been modified**: Restore the previous OIDC trust policy in the secrets manager configuration; coordinate with the security team to determine if the change was authorized.
4. **If performance degradation is causing timeouts**: Check Vault cluster resource utilization; if Vault is under heavy load, scale the Vault cluster or temporarily increase the pipeline secret fetch timeout.
5. **If network policies are blocking access**: Work with the network team to verify that the runner subnet has egress access to the secrets manager endpoint on the correct port; update security group or network policy rules as needed.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms secrets manager failure is affecting pipelines |
| 10 min | Notify #platform-incidents; advise teams to pause deployments requiring secrets |
| 20 min | Escalate to Security Engineer if authentication/OIDC configuration requires changes |
| 45 min | Escalate to Platform Lead if Vault cluster requires unsealing or infrastructure-level intervention |

## Dashboards

- [Vault Health](https://grafana.internal/d/vault-health) - Vault seal status, request latency, and error rates
- [Pipeline Secret Fetch Metrics](https://grafana.internal/d/secret-fetch) - Secret retrieval success rate and latency from CI jobs
- [Auth Token Expiry Tracker](https://grafana.internal/d/auth-tokens) - AppRole and OIDC token validity and rotation schedule
