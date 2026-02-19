---
id: REPORT-071
type: report
title: Customer Portal Accessibility Audit Report
status: review
owner: Customer Tech Lead
created: '2024-01-27T21:51:35.667Z'
updated: '2026-09-28T11:10:33.504Z'
tags:
  - report
  - customer-portal
summary: Customer Portal Accessibility Audit Report
company: CustomerPortal
report_month: 2025-09
report_type: analytics
overall_health: poor
confidence: medium
active_initiatives_count: 6
critical_risks_count: 0
example: true
---

## Service Health

| Criterion | WCAG 2.2 Level | Findings | Status |
|-----------|---------------|---------|--------|
| Perceivable | A + AA | 3 issues | Partially compliant |
| Operable | A + AA | 7 issues | Partially compliant |
| Understandable | A + AA | 4 issues | Partially compliant |
| Robust | A + AA | 8 issues | Partially compliant |
| Overall compliance | AA | 22 issues total | Below target |

Audit was conducted by the internal accessibility working group in September 2025 using axe-core automated scanning supplemented by manual keyboard-navigation and screen-reader testing (NVDA/Chrome and VoiceOver/Safari).

## Key Highlights

- **5 Level A failures found**: All five are in the forms and interactive widget areas. These prevent screen reader users from completing core tasks (ticket submission, preference updates) and are classified as critical. Remediation is required before the next major release.
- **Focus management gaps**: The support chat widget iframe does not return keyboard focus to the triggering button on close. This affects all keyboard-only users. Fix requires changes to the Customer Support Widget Service JavaScript.
- **Color contrast failures on secondary text**: 8 instances of body text and labels failing 4.5:1 contrast ratio requirement. Affects the DataTable component and SettingsForm helper text. Fixable via design token update.

## Active Initiatives

1. **Level A remediation sprint**: 5 Level A failures prioritized for immediate fix. Target: resolved within 2 weeks of audit publication.
2. **Color contrast token update**: Design system token for `--color-text-muted` will be darkened to meet 4.5:1 ratio. Affects all consumers of the token.
3. **Widget focus management fix**: Coordinating fix with Customer Support Widget Service team. Estimated 1-week effort.

## Incidents

No incidents during audit period.

## Risks

- **High**: Level A failures represent legal compliance risk under accessibility legislation. Must be resolved before next major release.
- **Medium**: Widget focus management fix requires coordination between portal and widget service teams; scheduling dependency.

## Next Month Focus

- Close all 5 Level A failures
- Ship color contrast design token update
- Retest Level A items with screen reader after fix deployment
- Schedule follow-up audit in 6 months to verify full AA compliance
