---
id: RUNBOOK-013
type: runbook
title: MFA Service Degradation Runbook
status: approved
owner: On-Call Engineer
created: '2024-12-08T16:07:03.963Z'
updated: '2025-06-02T22:31:18.779Z'
tags:
  - runbook
  - user-authentication
summary: MFA Service Degradation Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Identity Provider Service]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Node.js 20 / Redis 7 / DynamoDB

## Alerts

- `mfa_challenge_success_rate_low` - MFA challenge success rate drops below 90% for 3 minutes
- `mfa_totp_validation_error_rate_high` - TOTP validation errors exceed 5% for 5 minutes
- `mfa_sms_delivery_failure_rate_high` - SMS OTP delivery failure rate exceeds 10% for 5 minutes
- `mfa_service_latency_high` - MFA challenge P95 latency exceeds 3 seconds for 5 minutes

## Diagnosis Steps

1. **Identify the MFA factor type affected** - In Grafana, view MFA metrics broken down by factor type (TOTP, SMS, WebAuthn, email). Determine if degradation is limited to one factor or all factors; this determines whether the issue is in the MFA service or a specific factor provider.
2. **Check for SMS gateway issues** - If SMS OTP delivery is failing, check the SMS gateway's status page (Twilio status, AWS SNS health dashboard). Review the `mfa_sms_provider_errors` log stream for specific error codes.
3. **Check TOTP clock synchronization** - If TOTP validation errors are elevated, clock skew between users' devices and the server is the most common cause. Check `mfa_totp_clock_skew_distribution` metric to see if failures are clustered around specific skew values.
4. **Check MFA service dependencies** - The MFA service depends on the user database to look up enrolled factors. Verify database connectivity and query latency in the `mfa_db_query_duration` metric.
5. **Check for a recent MFA service deployment** - Review the deployment history. If a deployment occurred within the last hour, roll back as the first remediation step.

## Remediation Steps

1. **If caused by a recent deployment**: Roll back the MFA service immediately: revert the image tag in the deployment dashboard and sync. Do not wait for further diagnosis.
2. **If SMS gateway is down**: Enable the TOTP fallback prompt for SMS-enrolled users via the feature flag `MFA_SMS_FALLBACK_TO_TOTP=true`. Post an announcement in #status about SMS OTP delays.
3. **If TOTP clock skew is causing failures**: Increase the TOTP validation window to +/- 2 time steps in the MFA service configuration (`MFA_TOTP_WINDOW=2`). This accepts codes 60 seconds before or after the current window.
4. **If database connectivity issues are causing MFA degradation**: Restart the MFA service pods to reset connection pools: `kubectl rollout restart deployment/mfa-service -n auth`. If the database is unhealthy, escalate to the database on-call.
5. **If WebAuthn is failing**: Check whether the relying party (RP) origin configuration matches the current hostname. A misconfigured RP origin will cause all WebAuthn assertions to fail.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and identifies affected MFA factor types |
| 10 min | Post initial diagnosis in #auth-incidents |
| 20 min | If not resolved: page Platform Lead via PagerDuty |
| 30 min | If MFA is completely unavailable: notify CISO; evaluate temporary MFA bypass policy |
| 60 min | Escalate to Director of Engineering; prepare user communication |

## Dashboards

- [MFA Service Metrics](https://grafana.example.com/d/mfa-service) - Challenge success rates by factor type, latency, error breakdown
- [Auth Service Overview](https://grafana.example.com/d/auth-overview) - Overall login flow completion rates including MFA steps
- [SMS Gateway Health](https://grafana.example.com/d/sms-gateway) - SMS delivery rates, provider error codes, latency
