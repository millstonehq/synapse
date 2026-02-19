---
id: POLICY-045
type: policy
title: Customer Portal Third-Party Integration Policy
status: approved
owner: VP Engineering
created: '2024-02-29T08:53:56.806Z'
updated: '2026-08-25T15:20:01.258Z'
tags:
  - policy
  - customer-portal
summary: Customer Portal Third-Party Integration Policy
example: true
related_standards:
  - STANDARD-054
  - STANDARD-052
---

## Scope

This policy governs the evaluation, approval, and ongoing operation of third-party services integrated into the Customer Portal. It covers analytics platforms, identity providers, payment processors, chat and support tools, CDN providers, and any external API or SDK loaded into the portal frontend or backend. Engineering teams proposing new integrations and the teams maintaining existing ones are subject to this policy.

## Rationale

- Third-party code executes with portal privileges and can exfiltrate customer data or degrade portal reliability
- Supply chain attacks via third-party dependencies are a growing threat vector requiring proactive controls
- Unreviewed integrations can introduce GDPR/CCPA compliance violations through uncontrolled data sharing
- Vendor lock-in risk must be assessed before committing to integrations that affect core customer workflows

## Policy Statements

- All new third-party integrations must undergo a security and privacy review before being deployed to production
- Third parties receiving customer PII must have a signed Data Processing Agreement on file before integration goes live
- Frontend third-party scripts must be loaded via a Content Security Policy allowlist; unlisted scripts must be blocked
- Third-party integrations must be evaluated annually for continued necessity, security posture, and vendor stability
- Integration credentials and API keys must be stored in the secrets manager, not in source code or environment files checked into version control
- Any third-party service experiencing a breach must be evaluated for impact within 24 hours and customers notified if their data was affected

## Related Standards

- [[STANDARD-054|Customer Portal Accessibility Standard]]
- [[STANDARD-052|Customer Portal Internationalization Standard]]
