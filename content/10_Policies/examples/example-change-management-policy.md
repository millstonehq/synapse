---
id: change-management-policy
type: policy
title: Change Management Policy
status: draft
owner: CTO
created: '2025-10-18T19:48:03.147Z'
updated: '2025-10-18T19:48:03.147Z'
tags:
  - policy
summary: Governs how production changes are proposed, reviewed, executed, and audited.
example: true
---
## Scope

All production systems and infrastructure.

## Rationale

Reduce risk by ensuring changes are reviewed, approved, and reversible.

## Policy Statements

- All production changes must originate from a tracked ticket.
- High-risk changes require peer review and explicit approval.
- A tested rollback plan must exist for each change.
- Changes must be executed in approved maintenance windows unless urgent.

## Related Standards

- Change Control Standard
