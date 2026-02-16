---
id: change-management-policy
type: policy
title: Change Management Policy
status: approved
owner: CTO
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - policy
  - governance
summary: >-
  Governs how production changes are proposed, reviewed, executed, and
  audited. USE A POLICY when you need to state organizational RULES that
  must be followed. Policies are high-level mandates from leadership -
  they say "what must happen" without specifying how. They are enforced,
  not optional. Compare: a Standard specifies the measurable controls
  that implement this policy; a Process defines the workflow for
  carrying it out; an SOP gives the exact steps. Policies sit at the
  top of the governance hierarchy: Policy > Standard > Process > SOP.
example: true
---

## Scope

All production systems and infrastructure owned or operated by the engineering organization. This includes application deployments, database changes, infrastructure modifications, third-party integrations, and feature flag changes that affect production behavior.

This policy applies to all engineers, contractors, and automated systems that make changes to production environments.

## Rationale

Uncontrolled changes are the leading cause of production incidents. This policy exists to:

- Reduce the risk of outages caused by untested or uncoordinated changes
- Maintain an audit trail for compliance and incident investigation
- Ensure changes are reviewed by someone other than the author
- Guarantee that every change has a viable rollback plan

## Policy Statements

- All production changes must originate from a tracked, approved change ticket
- Every change must have a documented rollback plan before execution
- High-risk changes (database migrations, new services, breaking API changes) require senior engineer approval
- Peer review is mandatory for all changes - no self-approvals
- Changes must be executed during approved maintenance windows unless classified as emergency hotfixes
- Emergency hotfixes must be retroactively documented within 24 hours
- All change tickets are retained for a minimum of 12 months for audit purposes
- Automated deployments must enforce the same approval gates as manual deployments

## Related Standards

- [[change-control-standard|Change Control Standard]]
