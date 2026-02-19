---
id: POLICY-024
type: policy
title: Search Content Moderation Policy
status: approved
owner: VP Engineering
created: '2024-07-18T16:18:01.196Z'
updated: '2026-10-12T19:16:06.185Z'
tags:
  - policy
  - search-platform
summary: Search Content Moderation Policy
example: true
related_standards:
  - STANDARD-027
  - STANDARD-026
---

## Scope

This policy governs the mechanisms by which content is filtered, suppressed, or demoted in search results returned by the Search Platform. It applies to blocklists, safe-search filters, content classification models, and any human-reviewed moderation queues. All product and engineering teams that contribute to or consume moderation signals are subject to this policy.

## Rationale

- Unmoderated search results can surface harmful, illegal, or misleading content that creates legal and reputational risk
- Consistent content moderation rules are required to meet platform trust and safety obligations across jurisdictions
- Ad-hoc suppression of content without documented justification creates legal liability and undermines due process
- Automated content moderation must be regularly audited to detect false positive rates that reduce search quality

## Policy Statements

- All content suppression decisions must be logged with reason codes and the identity of the triggering rule or human reviewer
- Automated content classifiers used for moderation must achieve a documented false-positive rate below 0.5% on the quarterly quality benchmark
- Hard-blocklisted query terms and result URLs must be stored in a version-controlled registry reviewed monthly by the Trust and Safety team
- Appeals for suppressed content must be responded to within 5 business days
- Safe-search filtering must be enabled by default for all unauthenticated users; users may opt out only after explicit age verification
- Content moderation rule changes must be tested against the regression query set defined in [[STANDARD-026|Search Index Schema Standard]] before production deployment

## Related Standards

- [[STANDARD-027|Query Parameter Naming Standard]]
- [[STANDARD-026|Search Index Schema Standard]]
