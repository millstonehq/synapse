---
id: REPORT-015
type: report
title: Auth Service Performance Benchmark Report
status: approved
owner: User Tech Lead
created: '2024-06-24T05:56:40.722Z'
updated: '2026-09-04T12:35:42.272Z'
tags:
  - report
  - user-authentication
summary: Auth Service Performance Benchmark Report
company: UserAuthentication
report_month: 2025-10
report_type: analytics
overall_health: fair
confidence: medium
active_initiatives_count: 1
critical_risks_count: 1
example: true
---

## Service Health

| Endpoint | P50 | P95 | P99 | Max | SLO |
|----------|-----|-----|-----|-----|-----|
| POST /token (authorization_code) | 48ms | 112ms | 189ms | 820ms | < 200ms P99 |
| POST /token (client_credentials) | 12ms | 28ms | 51ms | 180ms | < 100ms P99 |
| POST /token (refresh_token) | 31ms | 74ms | 138ms | 450ms | < 150ms P99 |
| GET /userinfo | 18ms | 42ms | 78ms | 310ms | < 100ms P99 |
| GET /.well-known/jwks.json | 2ms | 4ms | 8ms | 22ms | < 20ms P99 |

All endpoints meet their P99 SLOs under normal load conditions. The authorization_code grant type shows the highest tail latency due to the additional MFA Gateway call and Redis code redemption step.

## Key Highlights

- **Authorization code flow P99 is 189ms**, within the 200ms SLO but with limited headroom. A 20% increase in traffic volume could push this above target.
- **Client credentials flow is significantly faster** (P99 51ms) because it bypasses MFA and session management, requiring only a database client lookup and JWT signing.
- **Max latency spikes** (820ms for authorization_code) occur during Redis cluster leader elections following scheduled maintenance. These are infrequent but affect a small number of users during the election window.
- **JWKS endpoint is extremely fast** (P99 8ms) due to in-memory caching of the key set. No database calls are required for key delivery.

## Active Initiatives

1. **Authorization code flow optimization** — Profiling shows 40ms of the P50 latency is spent in the MFA Gateway gRPC call even for non-MFA users. Adding a fast-path that skips the MFA Gateway call for users without MFA enrolled. Expected to reduce P50 to ~28ms.

## Incidents

No performance incidents in the reporting period.

## Risks

- **High**: Authorization code flow P99 headroom is only 11ms. A moderate traffic spike (during a product launch or marketing campaign) could push latency above SLO. Capacity planning review is needed before Q4 peak season.

## Next Month Focus

- Implement and benchmark the MFA Gateway fast-path for non-MFA users
- Run capacity planning simulation for Q4 peak traffic
- Establish automated performance regression tests in CI to catch regressions before deployment
