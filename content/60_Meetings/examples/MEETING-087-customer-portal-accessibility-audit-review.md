---
id: MEETING-087
type: meeting
title: Customer Portal Accessibility Audit Review
status: approved
owner: Product Manager
created: '2025-11-30T18:21:44.917Z'
updated: '2026-08-17T18:37:49.461Z'
tags:
  - meeting
  - customer-portal
summary: Customer Portal Accessibility Audit Review
company: CustomerPortal
topic: Customer Portal Accessibility Audit Review
meeting_date: '2025-07-15T06:35:05.834Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Customer Portal Platform
- **Topic**: Annual Accessibility Audit Results Review and Remediation Planning
- **Date/Time**: 2025-07-15 9:30 AM PT
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Review of the annual third-party accessibility audit conducted in June 2025 against WCAG 2.1 AA. 23 issues were identified across 8 portal pages.

## Observations by Domain

- **Critical Issues**: 2 critical issues found: the support ticket submission form has no visible focus indicator on its file upload button, and the billing page date picker is not keyboard accessible
- **High Issues**: 5 high-severity issues including missing ARIA labels on icon-only action buttons throughout the portal and missing form group labels in the account settings page
- **Color Contrast**: 8 instances of insufficient color contrast identified, primarily in secondary text and disabled state indicators
- **Screen Reader**: 4 instances of non-meaningful link text ("click here", "more") that provide no context to screen reader users
- **Positive Findings**: The new account overview page (redesigned in Sprint 23) received no accessibility findings; the redesign process is working

## Key Metrics & Data Points

- **Total issues identified**: 23 across 8 portal pages
- **Critical issues**: 2 (require immediate fix)
- **High issues**: 5 (fix within 30 days)
- **Medium issues**: 8 (fix within 90 days)
- **Low issues**: 8 (fix within 6 months)
- **Pages with zero issues**: 3 (all redesigned pages)

## Preliminary Scorecard Hooks

- Critical Accessibility: 2/5 - Two critical issues require immediate attention
- Color Contrast: 2/5 - 8 contrast failures across the portal
- Keyboard Navigation: 3/5 - Most flows work but date picker is non-functional without mouse
- Screen Reader Experience: 3/5 - Mostly functional but non-meaningful link text is a significant gap
- Redesign Quality: 5/5 - Redesigned pages are fully accessible; new process is effective

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Critical issues create legal accessibility compliance risk | High | Medium | Principal Engineer | Fix 2 critical issues in current sprint | 2025-07-25 |
| Contrast failures affect visually impaired customers | High | High | Tech Lead | Audit and update all secondary text and disabled state colors | 2025-08-15 |
| Non-meaningful link text degrades screen reader UX | Medium | High | Tech Lead | Replace all generic link text with descriptive text this sprint | 2025-07-31 |
| Audit cadence is insufficient for ongoing compliance | Medium | Low | Product Manager | Add axe-core to E2E test suite to catch regressions between audits | 2025-08-30 |

## Decisions & Next Steps

### Decisions

- The 2 critical issues are added to the current sprint as P1 bugs; no new feature work until they are resolved
- All 5 high-severity issues must be resolved within 30 days; assigned to Tech Lead for distribution
- axe-core integration into the E2E test suite is added to the Q3 engineering roadmap

### Action Items

- Tech Lead to create tickets for all 23 audit findings and assign severity-appropriate milestones (due 2025-07-17)
- Principal Engineer to fix the file upload focus indicator and billing date picker keyboard access (due 2025-07-25)
- Tech Lead to fix all non-meaningful link text instances (due 2025-07-31)

### Follow-ups

- Remediation progress review scheduled for 2025-08-15
- Next annual audit to be scheduled for June 2026
