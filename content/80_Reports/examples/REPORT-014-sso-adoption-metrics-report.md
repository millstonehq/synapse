---
id: REPORT-014
type: report
title: SSO Adoption Metrics Report
status: accepted
owner: User Tech Lead
created: '2025-10-30T13:54:31.790Z'
updated: '2026-12-19T20:57:36.005Z'
tags:
  - report
  - user-authentication
summary: SSO Adoption Metrics Report
company: UserAuthentication
report_month: 2025-09
report_type: analytics
overall_health: good
confidence: medium
active_initiatives_count: 3
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Enterprise orgs with SSO enabled | 60% | 64% | On target |
| SSO login success rate | > 99% | 99.4% | On target |
| SSO config self-service adoption | 40% | 29% | Below target |
| Avg SSO setup time (admin-assisted) | < 2 days | 1.3 days | On target |
| IdP integration errors per day | < 10 | 7 | On target |

SSO adoption among enterprise organizations continues to grow. The headline metric of 64% of enterprise orgs with SSO enabled exceeds the 60% target. However, self-service SSO configuration adoption (29%) is below the 40% target, suggesting the self-service tooling needs improvement.

## Key Highlights

- **64% SSO adoption among enterprise customers**: Up from 58% last quarter. Top configured identity providers are Okta (41%), Azure AD (35%), and Google Workspace (18%).
- **SAML remains dominant**: 72% of SSO connections use SAML 2.0; 28% use OIDC. OIDC share is growing as new integrations default to OIDC.
- **Self-service configuration gap**: Only 29% of new SSO setups were completed by admins without opening a support ticket. The main drop-off point is the SAML metadata XML upload step, which has a 24% error rate due to expired or malformed metadata files from IdPs.
- **Integration errors trending down**: Daily IdP integration errors decreased from 14 to 7 over the quarter, driven by improved error messaging and an automated certificate expiry pre-warning at 30 days.

## Active Initiatives

1. **SSO self-service UX improvements** — Redesigning the SAML metadata upload step with validation feedback and guided troubleshooting. Target: reduce upload error rate from 24% to under 5%.
2. **OIDC provider wizard** — A step-by-step wizard for common OIDC providers (Okta, Azure AD, Google Workspace) that pre-fills configuration from a provider template.
3. **SSO adoption campaigns** — Customer success is reaching out to the 36% of enterprise orgs without SSO to understand blockers.

## Incidents

No SSO-specific incidents in the reporting period.

## Risks

- **Low**: SAML certificate expiry is a recurring source of SSO outages for customers. The 30-day pre-warning email is not always acted on. Evaluating automatic certificate renewal for supported IdPs.

## Next Month Focus

- Launch SAML metadata upload UX improvements
- Begin OIDC provider wizard development for Okta and Azure AD
- Publish SSO adoption breakdown by industry vertical for customer success team
