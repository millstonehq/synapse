---
id: RUNBOOK-009
type: runbook
title: SSO Provider Outage Runbook
status: approved
owner: On-Call Engineer
created: '2024-11-04T22:42:02.005Z'
updated: '2025-10-15T17:42:26.812Z'
tags:
  - runbook
  - user-authentication
summary: SSO Provider Outage Runbook
example: true
---

## Service

- **System**: [[SYSTEM-006|Identity Provider Service]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "auth-oncall"
- **Slack channel**: #auth-incidents
- **Runtime**: Kubernetes / Node.js 20 / Redis 7 / DynamoDB

## Alerts

- `sso_login_success_rate_low` - SSO login success rate drops below 95% for 3 minutes
- `sso_provider_callback_timeout` - SSO provider callback response time exceeds 5s for 2 minutes
- `auth_sso_error_rate_high` - SSO-specific authentication errors exceed 2% for 5 minutes
- `sso_jwks_fetch_failure` - Authorization server cannot fetch provider JWKS for 3 consecutive retries

## Diagnosis Steps

1. **Check SSO provider status page** - Navigate to the affected provider's status page (e.g., status.okta.com, status.google.com). If the provider reports an active incident, this is the root cause; proceed to Remediation Step 1.
2. **Check SSO provider response times** - In Grafana, view the `sso_provider_latency_p95` metric for the affected provider. If latency has spiked above 5s in the last 15 minutes, the provider is degraded rather than fully down.
3. **Check authentication error logs** - In the log aggregation system, filter by `service:auth` and `sso_provider:<name>` for the last 30 minutes. Look for: OAuth callback errors, JWKS fetch failures, or token validation errors from the provider.
4. **Verify JWKS endpoint reachability** - Run `curl -s https://<provider-oidc-discovery-url> | jq .jwks_uri` then `curl -s <jwks_uri>` to confirm the provider's JWKS endpoint is reachable from the production cluster.
5. **Check fallback authentication availability** - Confirm that password-based and alternative SSO providers are operational so users can authenticate via a fallback method during the outage.

## Remediation Steps

1. **If provider is fully down per their status page**: Enable the SSO fallback banner in the authentication service (`AUTH_SSO_FALLBACK_ENABLED=true`) to redirect users to password or alternative SSO authentication. Post in #auth-incidents with the provider's incident URL.
2. **If JWKS fetch is failing**: Check if the authorization server can reach the provider's discovery endpoint. If not, temporarily configure the authorization server to use a cached copy of the JWKS (if available) to allow existing token validations to continue.
3. **If the provider is slow but not fully down**: Increase the SSO timeout threshold in the authentication service configuration to reduce timeout errors during the degraded period. Set `SSO_TIMEOUT_MS=10000`.
4. **If the outage is extended (>30 min)**: Publish an in-app notification directing users to use alternative login methods. Notify the customer success team of the impact.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks provider status page |
| 5 min | Post initial assessment in #auth-incidents with provider status link |
| 15 min | If not resolved: page the Platform Lead via PagerDuty |
| 30 min | If not resolved: notify Engineering Manager and activate customer communications |
| 60 min | If not resolved: escalate to Director of Engineering and open major incident |

## Dashboards

- [Auth Service Overview](https://grafana.example.com/d/auth-overview) - Login success rates by provider, latency, error rates
- [SSO Provider Health](https://grafana.example.com/d/sso-health) - Per-provider success rate, callback latency, JWKS fetch status
- [Auth Error Logs](https://kibana.example.com/app/discover#/auth-errors) - Authentication error logs with provider context
