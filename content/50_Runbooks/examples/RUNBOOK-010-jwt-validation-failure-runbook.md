---
id: RUNBOOK-010
type: runbook
title: JWT Validation Failure Runbook
status: review
owner: On-Call Engineer
created: '2025-07-21T09:09:30.487Z'
updated: '2026-08-29T16:45:22.179Z'
tags:
  - runbook
  - user-authentication
summary: JWT Validation Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Identity Provider Service]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Node.js 20 / DynamoDB / Redis 7

## Alerts

- `jwt_validation_error_rate_high` - JWT validation errors exceed 1% of requests for 3 minutes
- `jwks_fetch_failure` - Authorization server JWKS endpoint returns errors for 2 consecutive fetches
- `token_signature_mismatch_spike` - Token signature validation failures exceed 0.5% for 5 minutes
- `jwt_expired_token_rate_high` - Expired token rejections exceed 5% of requests for 10 minutes

## Diagnosis Steps

1. **Determine the error type** - In Kibana, filter by `service:auth` and `event_type:jwt_validation_failed` for the last 15 minutes. Categorize by error subtype: `signature_invalid`, `token_expired`, `audience_mismatch`, `issuer_mismatch`, or `algorithm_not_allowed`.
2. **Check for a recent key rotation** - Look at the deployment history and change ticket system. If a JWT signing key rotation occurred in the last 2 hours, this is the likely cause; proceed to Remediation Step 1.
3. **Check JWKS endpoint health** - Call `GET /.well-known/jwks.json` directly from the production cluster and confirm the response includes the expected `kid` values. If the endpoint is returning an error or missing keys, proceed to Remediation Step 2.
4. **Check token clock skew** - If error type is `token_expired`, investigate whether the authentication service and consuming services have clock synchronization issues. Run `kubectl exec -it <auth-pod> -- date` on multiple pods to compare timestamps.
5. **Check for a misconfigured audience** - If error type is `audience_mismatch`, a recent service configuration change may have modified the `aud` claim value. Compare the `aud` in failing tokens against the expected value in the service's JWT validation configuration.

## Remediation Steps

1. **If caused by key rotation with old tokens still active**: Re-add the previous key to the JWKS endpoint temporarily so tokens signed with the old key can still be validated. Deploy updated authorization server config with both keys published.
2. **If JWKS endpoint is returning errors**: Restart the authorization server pods to clear any in-memory state issues: `kubectl rollout restart deployment/auth-service -n auth`. If the issue persists, check the secrets manager for JWKS key availability.
3. **If clock skew is causing expired token errors**: Enable the `jwt_clock_skew_tolerance` configuration (set to 60 seconds) in the authorization server to accommodate minor clock drift. File a ticket to investigate and fix NTP synchronization.
4. **If audience mismatch is due to a misconfigured service**: Identify the service with the incorrect `aud` configuration, roll back its configuration to the previous correct value, and redeploy.
5. **If the root cause cannot be identified after 15 minutes**: Escalate to the Platform Lead and enable JWT debug logging (`JWT_DEBUG=true`) on one auth pod for detailed token inspection.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks error type distribution |
| 10 min | Post diagnosis findings in #auth-incidents |
| 20 min | If not resolved: page Platform Lead via PagerDuty |
| 30 min | If not resolved: notify Engineering Manager; consider enabling emergency authentication fallback |
| 60 min | Escalate to Director of Engineering; assess user impact scope |

## Dashboards

- [JWT Validation Metrics](https://grafana.example.com/d/jwt-validation) - Error rates by type, validation latency, JWKS cache hit rate
- [Auth Service Overview](https://grafana.example.com/d/auth-overview) - Overall authentication success rate and error breakdown
- [Auth Error Logs](https://kibana.example.com/app/discover#/auth-errors) - Detailed JWT validation error logs with token metadata
