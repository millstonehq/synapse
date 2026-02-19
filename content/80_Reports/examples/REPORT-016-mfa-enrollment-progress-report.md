---
id: REPORT-016
type: report
title: MFA Enrollment Progress Report
status: approved
owner: User Tech Lead
created: '2024-07-03T05:09:47.901Z'
updated: '2026-06-08T07:29:03.065Z'
tags:
  - report
  - user-authentication
summary: MFA Enrollment Progress Report
company: UserAuthentication
report_month: 2025-06
report_type: portfolio
overall_health: excellent
confidence: high
active_initiatives_count: 4
critical_risks_count: 3
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Overall MFA enrollment rate | 75% | 79.4% | On target |
| Admin accounts with MFA | 100% | 100% | On target |
| Enterprise org users with MFA | 85% | 88.2% | On target |
| Free tier users with MFA | 40% | 31.7% | Below target |
| TOTP adoption share | — | 52% | — |
| SMS OTP adoption share | — | 39% | — |
| WebAuthn adoption share | — | 9% | — |

Overall MFA enrollment has reached 79.4% of active users, exceeding the 75% target. Admin account enforcement (100%) has been maintained. Free tier users remain below target, which is expected given the voluntary enrollment model for that segment.

## Key Highlights

- **79.4% of active users now have at least one MFA factor enrolled**, up from 71% six months ago. The increase is largely driven by mandatory MFA enforcement for enterprise organizations rolled out in March.
- **TOTP is the most popular factor** (52% of enrolled users), followed by SMS OTP (39%) and WebAuthn (9%). WebAuthn share is growing following the launch of passkey support.
- **100% of admin accounts have MFA**: Achieved through a mandatory enrollment campaign with a 30-day grace period that concluded in April. Two accounts required manual intervention to complete enrollment.
- **Free tier enrollment lags**: At 31.7% vs. 40% target, free tier users have a lower enrollment rate. Users who enabled MFA within 7 days of signup have 4x lower churn, providing a retention incentive for a nudge campaign.
- **WebAuthn passkey adoption accelerating**: WebAuthn share has grown from 4% to 9% in the past quarter, driven by passkey support in mobile and browser platforms.

## Active Initiatives

1. **Free tier MFA nudge campaign** — In-app prompts and email sequence targeting free tier users who have not enrolled. A/B test of incentive messaging in progress.
2. **Passkey enrollment wizard** — Simplified enrollment flow for WebAuthn passkeys targeting non-technical users. Design in review.
3. **MFA policy enforcement for high-risk actions** — Requiring step-up MFA for sensitive operations (API key creation, payment method changes) regardless of session age.
4. **Hardware security key support** — Expanding WebAuthn support to include NFC/USB FIDO2 keys. Procurement and testing underway.

## Incidents

No MFA enrollment incidents in the reporting period.

## Risks

- **High**: SMS OTP remains the second-most-used factor at 39%, but SMS is susceptible to SIM-swap attacks. The security team recommends reducing SMS share to under 20% within 12 months.
- **High**: Free tier MFA enrollment at 31.7% means a large portion of accounts rely solely on passwords. A credential stuffing campaign targeting free tier accounts would have high impact.
- **Medium**: WebAuthn device keys are bound to physical devices. Users who lose their primary device without a backup factor may face account recovery friction.

## Next Month Focus

- Launch free tier MFA nudge campaign (Phase 1: in-app prompt)
- Begin A/B test on MFA enrollment incentive messaging
- Ship passkey enrollment wizard to beta
- Present SIM-swap risk analysis and SMS reduction roadmap to security committee
