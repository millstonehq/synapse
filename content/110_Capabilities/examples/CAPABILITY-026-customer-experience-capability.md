---
id: CAPABILITY-026
type: capability
title: Customer Experience Capability
status: approved
owner: Head of Engineering
created: '2025-10-12T15:49:50.386Z'
updated: '2025-08-28T02:15:28.408Z'
tags:
  - capability
  - customer-portal
summary: Customer Experience Capability
evidence_links:
  - POLICY-044
  - STANDARD-053
  - POLICY-042
example: true
---

## Domain

- Customer Portal
- Product
- UX and Design

## Maturity (0-5)

**Current score: 2 / 5 (Repeatable)**

- **Level 0 - Initial**: No structured customer experience design. Portal features are built without user research or usability testing. No accessibility standards applied.
- **Level 1 - Ad hoc**: Some design review happens but is not systematic. CX improvements are reactive (driven by support complaints) rather than proactive.
- **Level 2 - Repeatable** (current): Design reviews occur for major features. A design system provides component consistency. Customer satisfaction is measured via post-survey but not acted on systematically. Accessibility audit runs annually.
- **Level 3 - Defined**: CX policy and standards are formally documented and enforced. Design review is mandatory for all portal features. CSAT targets are set per feature area. Accessibility is tested in CI on every PR.
- **Level 4 - Managed**: CX metrics (CSAT, task completion, NPS) are tracked in real-time dashboards. User research sessions conducted monthly. A/B testing infrastructure enables systematic improvement.
- **Level 5 - Optimizing**: Personalized experiences based on customer behavior signals. Continuous experimentation culture with defined test-and-learn cadence. CSAT > 4.5 sustained.

**Gap to Level 3**: CX policy (POLICY-044) is drafted but not enforced via a gating mechanism. Design review is optional for small changes. Accessibility is only checked in quarterly audits, not in CI.

## Metrics

- Portal CSAT: Currently 4.1 / 5.0, target 4.5
- Net Promoter Score (portal): Currently 34, target 45
- Accessibility violations (WCAG 2.2 AA) in quarterly audit: Currently 3, target 0
- Design review coverage for new features: Currently 70%, target 100%
- User research sessions per quarter: Currently 1, target 3

## Evidence Links

- [[POLICY-044|Customer Experience Policy]] - Policy mandating CX standards for all customer-facing features
- [[STANDARD-053|Customer Portal Accessibility Standard]] - WCAG 2.2 compliance requirements and testing procedures
- [[POLICY-042|Customer Data Privacy Policy]] - Policy governing customer data use in CX analytics and personalization

## Notes

The portal team is working toward Level 3 as part of the Q2 2025 CX improvement OKR.

Priority actions for Level 3:
- Formalize and publish the CX policy (POLICY-044) and make design review a blocking gate for all PRDs
- Add axe-core accessibility checks to the CI pipeline for all portal PRs
- Set per-page CSAT targets and build a dashboard to monitor them weekly
- Conduct quarterly user research sessions with 5 customers to identify the top friction points
