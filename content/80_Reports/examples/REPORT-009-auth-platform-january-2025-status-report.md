---
id: REPORT-009
type: report
title: Auth Platform January 2025 Status Report
status: approved
owner: User Tech Lead
created: '2025-06-10T18:46:28.487Z'
updated: '2025-01-09T17:37:48.838Z'
tags:
  - report
  - user-authentication
summary: Auth Platform January 2025 Status Report
company: UserAuthentication
report_month: 2024-07
report_type: portfolio
overall_health: poor
confidence: medium
active_initiatives_count: 7
critical_risks_count: 2
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Auth service availability | 99.95% | 99.71% | Below target |
| Token issuance P50 latency | < 50ms | 68ms | Below target |
| Token issuance P99 latency | < 200ms | 310ms | Below target |
| Login success rate | > 99.5% | 99.2% | Below target |
| MFA challenge delivery rate | > 99% | 98.4% | Below target |
| Session validation P99 | < 20ms | 17ms | On target |

January was a challenging month for the Auth Platform. Two incidents (INC-102 and INC-104) affected token issuance latency and contributed to the below-target availability and login success rate. Recovery efforts are ongoing.

## Key Highlights

- **INC-102 — Redis cluster split-brain**: A network partition on Jan 9 caused a Redis cluster split-brain that temporarily made session tokens unresolvable. The incident lasted 34 minutes and affected all users attempting login. Redis Sentinel failover triggered correctly but the 2-minute failover window was user-facing.
- **INC-104 — JWT signing key cache miss**: A new deployment on Jan 18 introduced a timing bug in the JWKS cache warm-up, causing a 12-minute window where token issuance latency spiked to P99 > 2s. Rolling back the deployment resolved the issue.
- **MFA delivery degradation**: Twilio experienced elevated SMS latency for two 20-minute windows on Jan 12 and Jan 21. Users on SMS-only MFA experienced timeouts. Email fallback is being prioritized as a follow-up.

## Active Initiatives

1. **Redis HA upgrade** — Migrating from Redis Sentinel to Redis Cluster mode with automatic sharding. Reduces single-node failure blast radius. Target: February end.
2. **JWKS cache preloading** — Adding a startup health gate that blocks traffic until the JWKS cache is fully warm. Prevents the Jan 18 regression class.
3. **Email MFA fallback** — When SMS delivery exceeds 5 seconds, the MFA Gateway will automatically offer an email OTP. Design complete, implementation in progress.
4. **Auth latency SLO review** — Current SLOs do not account for burst patterns during password reset campaigns. Reviewing with product to set realistic targets.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Jan 9 | SEV-2 | 34 min | Redis cluster split-brain during network partition; session validation unavailable |
| Jan 18 | SEV-3 | 12 min | JWKS cache warm-up bug caused elevated token issuance latency post-deploy |

## Risks

- **Critical**: Redis cluster operating in Sentinel mode has a 2-minute minimum failover window. Any Redis primary failure results in a user-visible outage. Mitigation: Redis Cluster migration in progress.
- **Critical**: SMS OTP delivery depends on a single Twilio account. No secondary SMS provider is configured. Mitigation: Evaluating AWS SNS as a secondary channel.

## Next Month Focus

- Complete Redis Cluster migration in staging and begin production cutover
- Ship email MFA fallback feature
- Deploy JWKS cache preloading fix
- Conduct a chaos engineering exercise to validate new Redis failover behavior
