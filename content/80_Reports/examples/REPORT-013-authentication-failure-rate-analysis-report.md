---
id: REPORT-013
type: report
title: Authentication Failure Rate Analysis Report
status: approved
owner: User Tech Lead
created: '2025-01-26T03:04:44.439Z'
updated: '2025-12-12T13:57:29.817Z'
tags:
  - report
  - user-authentication
summary: Authentication Failure Rate Analysis Report
company: UserAuthentication
report_month: 2026-07
report_type: portfolio
overall_health: good
confidence: medium
active_initiatives_count: 8
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Baseline (Jan) | Current | Trend |
|--------|---------------|---------|-------|
| Overall auth failure rate | 0.82% | 0.49% | Improving |
| Invalid credentials failures | 0.61% | 0.38% | Improving |
| MFA timeout failures | 0.14% | 0.07% | Improving |
| Token validation failures | 0.05% | 0.03% | Stable |
| Account lockout rate | 0.02% | 0.01% | Stable |

Authentication failure rates have decreased significantly over the reporting period, driven by the email MFA fallback feature and improved SMS delivery reliability through the secondary provider.

## Key Highlights

- **Credential failures remain the top failure category** at 0.38% of attempts, primarily from users with expired passwords and users logging in from new devices without saved credentials.
- **MFA timeout failures halved** from 0.14% to 0.07% following the email fallback launch. Users who previously abandoned the login flow after SMS delays now complete via email OTP.
- **Bot activity accounts for ~30% of invalid credential failures**: Rate limiting and CAPTCHA on the login page are blocking the majority of automated attempts, but there is a residual long-tail of distributed credential stuffing.
- **Account lockouts are low**: The lockout policy (10 failed attempts in 10 minutes) triggers for approximately 0.01% of accounts per day. The majority are resolved by self-service password reset within 15 minutes.

## Active Initiatives

1. **Passwordless rollout** — Expected to eliminate credential-based failures for enrolled users. Currently in beta.
2. **Adaptive rate limiting** — Per-IP and per-org rate limits targeting credential stuffing clusters.
3. **Device trust signals** — Reducing friction for recognized devices to improve success rates for legitimate users on new devices.

## Incidents

No incidents directly related to authentication failure rates in the reporting period.

## Risks

- **Low**: Credential stuffing volume is increasing at ~5% month-over-month. Current rate limits are effective but may need tuning if the trend continues.

## Next Month Focus

- Analyze impact of passwordless beta on credential failure rates among enrolled users
- Tune per-org rate limits based on observed bot traffic patterns
- Publish failure rate breakdown by client application to identify integration issues
