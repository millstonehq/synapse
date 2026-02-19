---
id: REPORT-082
type: report
title: Auth Service Latency Benchmark Report
status: approved
owner: User Tech Lead
created: '2025-09-17T19:35:17.789Z'
updated: '2026-06-26T17:26:23.383Z'
tags:
  - report
  - user-authentication
summary: Auth Service Latency Benchmark Report
company: UserAuthentication
report_month: 2024-06
report_type: portfolio
overall_health: poor
confidence: low
active_initiatives_count: 8
critical_risks_count: 1
example: true
---

## Service Health

| Endpoint | Load (RPS) | P50 | P95 | P99 | Max | SLO (P99) |
|----------|-----------|-----|-----|-----|-----|-----------|
| POST /auth/login | 80 | 62ms | 128ms | 241ms | 1.4s | 300ms |
| POST /token (auth_code) | 120 | 48ms | 112ms | 189ms | 820ms | 200ms |
| POST /token (client_creds) | 200 | 12ms | 28ms | 51ms | 180ms | 100ms |
| POST /token (refresh) | 150 | 31ms | 74ms | 138ms | 450ms | 150ms |
| GET /userinfo | 90 | 18ms | 42ms | 78ms | 310ms | 100ms |
| POST /auth/mfa/challenge | 40 | 95ms | 210ms | 388ms | 2.1s | 400ms |
| GET /.well-known/jwks.json | 500 | 2ms | 4ms | 8ms | 22ms | 20ms |

All endpoints are within their P99 SLOs under the load levels tested. The login endpoint and MFA challenge endpoint show the highest tail latency due to the multi-step nature of those operations. The JWKS endpoint is extremely fast due to in-memory caching.

## Key Highlights

- **Login P99 at 241ms** is within the 300ms SLO but leaves only 59ms of headroom. The login path involves credential validation, User Directory lookup, and MFA Gateway call sequentially — any single component degradation cascades to the overall latency.
- **MFA challenge P99 at 388ms** is within the 400ms SLO. The outliers (max 2.1s) occur during SMS OTP delivery when Twilio experiences brief latency. The email fallback path is faster (P99 ~150ms via SendGrid).
- **Authorization code token exchange at P99 189ms** is the tightest path; headroom against the 200ms SLO is only 11ms. At 2x current load (projected for Q4), this endpoint would breach SLO.
- **Refresh token exchange and client credentials are well within SLO** with significant headroom, indicating no concern for those paths.

## Active Initiatives

1. **Login path fast-path for non-MFA users** — Profile analysis shows 40ms of the login P50 is a conditional MFA Gateway call that returns immediately for non-enrolled users. Adding a User Directory cache hit for MFA enrollment status will eliminate this call for ~20% of users. Expected P50 improvement: 30-40ms.
2. **Authorization code token exchange optimization** — P99 headroom is critical for Q4. Profiling shows 45ms of P99 is Redis round-trip latency. Evaluating Redis connection pool tuning and pipelining.

## Incidents

No latency incidents in the benchmarking period.

## Risks

- **High**: Authorization code token exchange P99 headroom (11ms) is insufficient for Q4 peak traffic. If volume doubles, this endpoint will breach SLO. Capacity planning and optimization must complete before peak season.

## Next Month Focus

- Implement and benchmark the non-MFA fast-path optimization
- Run load test at 2x current volume to validate Q4 capacity
- Publish per-endpoint latency dashboards to Grafana for ongoing tracking
- Evaluate Redis pipelining for the token exchange path
