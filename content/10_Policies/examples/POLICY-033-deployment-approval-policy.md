---
id: POLICY-033
type: policy
title: Deployment Approval Policy
status: approved
owner: CTO
created: '2025-05-14T22:46:58.045Z'
updated: '2026-04-29T10:13:43.662Z'
tags:
  - policy
  - ci-cd-platform
summary: Deployment Approval Policy
example: true
related_standards:
  - STANDARD-040
  - STANDARD-041
---

## Scope

This policy applies to all deployments to production environments, including application services, infrastructure components, database migrations, and configuration changes. It covers deployments executed manually, via automated pipelines, and via GitOps controllers. All teams with production deployment access must comply, including contractors and third-party operators acting on behalf of the organization.

Deployments to non-production environments (development, staging) are not subject to mandatory approval gates but are encouraged to follow the same review practices.

## Rationale

- Unreviewed deployments to production are a leading cause of service outages and data integrity incidents
- Approval gates provide a checkpoint to verify that quality gates have passed and rollback plans are in place before changes reach customers
- Documented approval creates an audit trail necessary for regulatory compliance and post-incident investigation
- Requiring human sign-off for high-risk changes reduces the blast radius of automated pipeline misconfigurations
- Approval workflows enforce separation of duties, ensuring no single engineer can both author and deploy a change without oversight

## Policy Statements

- All production deployments must be associated with an approved deployment record before execution; automated pipelines must enforce this gate programmatically
- Low-risk deployments (bug fixes, minor configuration changes) require approval from one peer reviewer
- Medium-risk deployments (new features, dependency upgrades, schema changes) require approval from one peer reviewer and one senior engineer
- High-risk deployments (new services, breaking API changes, auth system changes) require explicit CTO or VP Engineering approval and must be executed within an approved maintenance window
- Emergency deployments may bypass normal approval gates with verbal authorization from an engineering manager, but must be retroactively documented within four hours
- No engineer may approve their own deployment; self-approval by automated systems is prohibited
- Approval records must include the approver's identity, timestamp, risk classification, and reference to the passing CI run

## Related Standards

- [[STANDARD-040|Build Artifact Naming Standard]]
- [[STANDARD-041|CI/CD Secret Management Standard]]
