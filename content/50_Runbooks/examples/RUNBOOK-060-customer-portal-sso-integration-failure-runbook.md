---
id: RUNBOOK-060
type: runbook
title: Customer Portal SSO Integration Failure Runbook
status: draft
owner: On-Call Engineer
created: '2025-04-24T20:50:56.053Z'
updated: '2025-06-03T05:23:58.697Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal SSO Integration Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal]]
- **Owner team**: Customer Portal Engineering
- **On-call rotation**: PagerDuty schedule "portal-oncall"
- **Slack channel**: #customer-portal-incidents
- **Runtime**: Node.js 20 / OAuth 2.0 / SAML 2.0 / Redis session store

## Alerts

- `portal_sso_auth_failure_rate_high` - SSO authentication failures exceed 5% of login attempts for 3 minutes
- `portal_login_timeout_rate_high` - Login flow timeouts exceed 2% for 5 minutes
- `portal_idp_callback_errors` - Identity provider callback endpoint returning errors for more than 1 minute
- `portal_session_creation_failure` - Session creation failures after successful SSO token exchange

## Diagnosis Steps

1. **Check identity provider status** - Visit the SSO identity provider's status page (Okta, Azure AD, or the customer's IdP) and check for active outages or degradations; an IdP outage immediately explains portal SSO failures.
2. **Check portal SSO callback logs** - Filter portal API logs for `/auth/callback` endpoint; look for error codes from the IdP (token validation failures, expired assertions, mismatched redirect URIs).
3. **Check SSO configuration** - Verify the SSO application configuration has not changed: client ID/secret validity, redirect URI allowlist, certificate expiry, and SAML entity IDs are all common sources of sudden SSO failures.
4. **Check session store health** - Verify Redis is available and responding; a Redis failure can cause session creation to fail even after successful SSO token exchange.
5. **Test SSO flow end-to-end** - Use the portal's test account to attempt SSO login and capture the full redirect chain; identify at which step the flow breaks.

## Remediation Steps

1. **If IdP is experiencing an outage**: Enable the "SSO temporarily unavailable" fallback message in the portal feature flag console; communicate to affected customers via the status page.
2. **If SSO certificate has expired**: Renew the certificate in the IdP application configuration and update the portal's SP metadata; this requires coordination with the customer's IT admin for customer-managed IdPs.
3. **If redirect URI mismatch**: Correct the redirect URI in the IdP application registration to match the portal's configured callback URL; ensure no trailing slash discrepancies.
4. **If Redis is down and causing session failures**: Restart the Redis session store; customers will need to re-authenticate. Follow the portal session issue runbook for Redis recovery.
5. **If a portal deploy changed SSO configuration**: Roll back the portal deployment to restore the previous SSO configuration.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #customer-portal-incidents |
| 20 min | If not resolved: page Portal Tech Lead; notify affected enterprise customers |
| 30 min | If IdP-related: engage customer IT admin or IdP vendor support |
| 60 min | Engineering Manager paged; status page updated |

## Dashboards

- [Portal Authentication](https://grafana.example.com/d/portal-auth) - Login success/failure rates, SSO callback errors
- [Portal Session Store](https://grafana.example.com/d/portal-redis) - Redis availability, session creation rates
- [Portal API Errors](https://grafana.example.com/d/portal-api-errors) - Auth endpoint error breakdown
- [Portal Login Funnel](https://grafana.example.com/d/portal-login-funnel) - Login step completion rates and drop-off
