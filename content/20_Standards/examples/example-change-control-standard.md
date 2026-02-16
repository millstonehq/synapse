---
id: change-control-standard
type: standard
title: Change Control Standard
status: approved
owner: Head of Engineering
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - standard
  - governance
  - compliance
summary: >-
  Specifies the measurable controls and approval requirements for
  production changes. USE A STANDARD when you need to define MEASURABLE
  CONTROLS that implement a policy. Standards are the "what specifically"
  layer - they translate high-level policy mandates into concrete,
  auditable requirements with compliance mappings. Compare: a Policy
  says "changes must be reviewed" (the rule); a Standard says "reviews
  must include test coverage verification and risk assessment scored
  on a 3-point scale" (the measurable control); a Process defines the
  workflow for executing the standard; an SOP gives the exact steps.
related_policies:
  - change-management-policy
example: true
---

## Area

Software Development Lifecycle (SDLC) - Change Management

This standard applies to all changes in the production deployment pipeline, including application code, infrastructure-as-code, database schemas, and configuration changes.

## Controls

- Change requests must include: description, risk level (low/medium/high), impact assessment, and a tested rollback plan
- Risk levels are classified as: **Low** (config changes, minor bug fixes), **Medium** (new features, dependency updates), **High** (database migrations, new services, breaking API changes, auth changes)
- Low-risk changes require one peer reviewer approval
- Medium-risk changes require one peer reviewer plus one senior engineer acknowledgment
- High-risk changes require one peer reviewer plus explicit senior engineer approval with maintenance window sign-off
- All changes must have CI passing (test suite, linting, type checking) before deployment is permitted
- Post-deployment verification must occur within 15 minutes of deploy completion, checking error rate, latency, and business metrics
- Failed deployments must trigger rollback within 5 minutes of SLO breach detection
- Change tickets must be closed within 24 hours of deployment with evidence (commit SHA, timestamp, metrics screenshot)

## Compliance Mappings

- NIST SP 800-53: CM-3 (Configuration Change Control)
- ISO 27001: A.12.1.2 (Change Management)
- SOC 2: CC8.1 (Change Management)

## Related Policies

- [[change-management-policy|Change Management Policy]]
