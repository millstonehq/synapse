---
id: RUNBOOK-072
type: runbook
title: Auth Service Certificate Expiry Runbook
status: review
owner: On-Call Engineer
created: '2024-06-26T11:50:52.775Z'
updated: '2026-09-08T13:48:33.971Z'
tags:
  - runbook
  - user-authentication
summary: Auth Service Certificate Expiry Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Auth Service]]
- **Owner team**: User Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7

## Alerts

- `auth_cert_expiry_30d` — TLS certificate for auth.example.com expires in 30 days. Non-urgent; begin renewal planning.
- `auth_cert_expiry_7d` — TLS certificate expires in 7 days. Urgent; certificate renewal must be completed before this window closes or users will see TLS errors.
- `auth_cert_expiry_24h` — TLS certificate expires in 24 hours. Critical; if not already renewed, service will become unavailable to users at expiry.
- `auth_jwks_cert_expiry_14d` — JWT signing certificate (in JWKS) expires in 14 days. Begin key rotation procedure.

## Diagnosis Steps

1. **Confirm alert scope** - Determine whether the alert is for the TLS certificate (affects HTTPS connectivity) or the JWT signing key certificate (affects token validation). Run `kubectl get secret auth-tls -n auth -o json | jq '.data."tls.crt"' | base64 -d | openssl x509 -noout -dates` to check TLS cert expiry. Run `curl -s https://auth.example.com/.well-known/jwks.json | jq '.keys[].x5c[0]' -r | base64 -d | openssl x509 -noout -dates` to check JWT signing cert expiry.
2. **Check renewal automation status** - The cert-manager controller should handle TLS certificate renewal automatically 30 days before expiry. Run `kubectl describe certificate auth-tls -n auth` to see the last renewal attempt and any errors. If cert-manager has a failed renewal, look for errors in `kubectl logs -n cert-manager deployment/cert-manager`.
3. **Verify current service connectivity** - If within 7 days of expiry, verify the certificate is still valid and users are not yet experiencing TLS errors. Check the `auth_login_error_rate` dashboard for anomalous 5xx errors, which may indicate expired certificates are already causing failures.
4. **Check key rotation status** - If the alert is for the JWKS signing certificate, check whether a new signing key has been added to the JWKS endpoint (`curl https://auth.example.com/.well-known/jwks.json | jq '.keys | length'`). A value of 2 indicates rotation is in progress (old + new key). A value of 1 with an expiring cert means rotation has not started.
5. **Identify the blockers** - If automatic renewal failed, identify the cause: ACME challenge failure (DNS or HTTP), cert-manager misconfiguration, or a Vault lease expiry for JWT signing keys.
6. **Assess impact timeline** - Calculate time remaining until expiry. Alert at 7 days is the latest safe point to begin manual intervention. If within 24 hours, treat as a SEV-1 and escalate immediately.

## Remediation Steps

1. **If TLS cert renewal failed in cert-manager**: Delete the existing certificate request to trigger a fresh renewal: `kubectl delete certificaterequest -n auth -l cert-manager.io/certificate-name=auth-tls`. Monitor cert-manager logs for the new renewal attempt. If ACME challenge is failing, check that the DNS challenge record or HTTP challenge endpoint is accessible.
2. **If TLS cert must be renewed manually**: Generate a CSR, submit to the CA (Let's Encrypt or internal CA), and create a new Kubernetes Secret: `kubectl create secret tls auth-tls --cert=fullchain.pem --key=privkey.pem -n auth --dry-run=client -o yaml | kubectl apply -f -`. Trigger a rolling restart: `kubectl rollout restart deployment/auth-service -n auth`.
3. **If JWT signing key rotation is needed**: Follow the key rotation SOP. Add a new signing key to Vault, update the JWKS endpoint to include both old and new keys, switch new token issuance to use the new key, wait 7 days for old tokens to expire, then remove the old key from JWKS. Do NOT remove the old key before the overlap period ends.
4. **If certificate has already expired (TLS)**: This is a SEV-1. Immediately follow remediation step 2 with manual renewal. Update the status page. Notify the on-call manager. Service will be unavailable until the new certificate is deployed.
5. **If JWT signing cert has expired**: Tokens signed with the expired key will fail JWKS validation but the keys themselves are still mathematically valid. The `exp` claim in issued tokens provides the actual security boundary. Proceed with rotation per step 3 and monitor for 401 error rate increases.
6. **After remediation**: Verify TLS cert expiry: `kubectl get certificate auth-tls -n auth` should show `READY=True` and a new expiry date. Verify JWKS: `curl https://auth.example.com/.well-known/jwks.json` should show the new key ID. Monitor login error rate for 30 minutes post-remediation.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 15 min | If not resolved or root cause unclear, escalate to auth tech lead via PagerDuty |
| 30 min | If service is actively degraded (users experiencing TLS errors), declare SEV-1, notify engineering manager and open status page incident |
| 60 min | If not resolved, escalate to platform/infra team for cert-manager or Vault assistance |

## Dashboards

- [Auth Service TLS Certificate Status](https://grafana.example.com/d/auth-certs) - Certificate expiry dates and renewal status for all auth TLS certs
- [Auth Service Error Rate](https://grafana.example.com/d/auth-errors) - Login error rates; will spike on TLS cert expiry
- [JWKS Health](https://grafana.example.com/d/auth-jwks) - JWKS endpoint availability and key count over time
- [cert-manager Dashboard](https://grafana.example.com/d/certmanager) - cert-manager renewal status and failure rates across all services
- [Token Validation Error Rate](https://grafana.example.com/d/auth-token-validation) - 401 error rates from resource servers; useful for detecting JWKS key rotation issues
