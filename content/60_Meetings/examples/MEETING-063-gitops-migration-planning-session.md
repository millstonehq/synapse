---
id: MEETING-063
type: meeting
title: GitOps Migration Planning Session
status: accepted
owner: Product Manager
created: '2024-05-16T18:22:24.342Z'
updated: '2025-10-06T16:16:29.162Z'
tags:
  - meeting
  - ci-cd-platform
summary: GitOps Migration Planning Session
company: CI/CDPlatform
topic: GitOps Migration Planning Session
meeting_date: '2024-07-30T11:01:46.535Z'
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

- **Project**: GitOps Migration Initiative
- **Topic**: Planning session to scope and sequence the migration from imperative deployment scripts to ArgoCD-managed GitOps
- **Date/Time**: 2024-07-30 11:01 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: 23 services currently deploy via shell scripts invoked by CI; goal is to migrate all to ArgoCD GitOps by end of Q4 2024

## Observations by Domain

- **Current Deployment State**: 23 services use imperative `kubectl apply` scripts; 4 services already use ArgoCD from a pilot; the pilot services have significantly fewer deployment incidents
- **Manifest Management**: Service manifests live inside application repositories alongside source code; GitOps requires separation into a dedicated manifests repository, which is a meaningful change to team workflows
- **Rollback Capability**: Current imperative deployments have no standardized rollback; teams manually re-run old pipeline jobs or apply previous manifests ad-hoc
- **QA Environment Parity**: QA environments diverge from production because they are not driven by the same manifests; GitOps would enforce parity by reconciling QA manifests from the same source
- **Migration Risk**: High-traffic services (payments, auth) require extra care; downtime during migration would be customer-impacting

## Key Metrics & Data Points

- **Services to migrate**: 23 services (4 already on ArgoCD pilot)
- **Deployment incident rate (pre-GitOps)**: 3.1 incidents per 100 deployments
- **Deployment incident rate (ArgoCD pilot)**: 0.4 incidents per 100 deployments (87% reduction)
- **Average rollback time (current)**: 12 minutes; ArgoCD pilot rollback time: 45 seconds
- **Estimated migration effort**: 2 engineering weeks per service cohort of 5 services

## Preliminary Scorecard Hooks

- Migration Readiness: 3/5 - ArgoCD pilot successful; tooling proven but process documentation incomplete
- Team Workflow Impact: 2/5 - Manifest repository separation requires significant workflow change for all service teams
- Rollback Improvement: 5/5 - ArgoCD rollback is dramatically faster and more reliable than current approach
- QA Environment Parity: 2/5 - Currently poor; GitOps would significantly improve parity
- Risk Management: 3/5 - High-traffic service migration needs careful sequencing and rollback testing

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Payments service migration causes downtime | High | Medium | Principal Engineer | Perform migration on staging first with load testing; use maintenance window | 2024-09-15 |
| Teams resist manifest repository workflow change | Medium | High | Engineering Manager | Run training sessions before migration; provide tooling to automate manifest generation | 2024-08-15 |
| ArgoCD cluster becomes overloaded with 23 applications | Medium | Low | Tech Lead | Size ArgoCD cluster based on pilot metrics; implement application sync batching | 2024-09-01 |

## Decisions & Next Steps

### Decisions
- Migrate services in cohorts of 5 starting with low-traffic, non-critical services; payments and auth migrate last
- Create a shared GitOps manifests repository (`infra/k8s-manifests`) with a per-service directory structure
- Mandate ArgoCD for all new services starting immediately; no new services may use imperative deployment scripts

### Action Items
- Principal Engineer to create the `infra/k8s-manifests` repository structure and migration guide by 2024-08-15
- QA Lead to define acceptance criteria for each migrated service before cohort migration begins
- Engineering Manager to schedule team training sessions for GitOps workflow changes

### Follow-ups
- Present migration progress at the next engineering all-hands
- Review deployment incident rate 30 days after each cohort migration to validate improvement
