---
id: POLICY-035
type: policy
title: Release Cadence Policy
status: review
owner: VP Engineering
created: '2024-11-20T22:35:28.436Z'
updated: '2026-11-12T04:05:04.823Z'
tags:
  - policy
  - ci-cd-platform
summary: Release Cadence Policy
example: true
related_standards:
  - STANDARD-041
  - STANDARD-039
---

## Scope

This policy governs the frequency, scheduling, and communication requirements for all production software releases. It applies to all product teams shipping deployable services, including backend APIs, frontend applications, data pipelines, and platform components. Release cadence requirements apply regardless of whether the release is deployed manually or through automated continuous delivery pipelines.

Teams operating under Service Level Agreements with external partners or customers must align their release cadence with contractual notification obligations.

## Rationale

- Irregular or ad-hoc release schedules make it difficult to coordinate cross-team dependencies and increase the risk of conflicting deployments
- Batching many changes into infrequent releases increases deployment risk and complicates rollback decisions
- A defined cadence allows support, operations, and customer-facing teams to prepare for changes and communicate proactively with stakeholders
- Predictable release windows enable on-call teams to allocate appropriate coverage and reduce incident response fatigue
- Continuous delivery to production is the preferred model; the cadence policy sets minimum expectations while encouraging higher-frequency, lower-risk deployments

## Policy Statements

- Teams must deploy to production at minimum once per two-week sprint cycle; teams that have not deployed in 14 days must document a reason and a plan to resume delivery
- Production deployments are restricted to the hours of 09:00–16:00 local time on weekdays; deployments outside this window require engineering manager approval except for emergency hotfixes
- Friday deployments after 14:00 and deployments on the day before a public holiday are prohibited unless classified as emergency hotfixes
- All planned releases must be communicated in the #releases channel at least one hour before execution; the notification must include the service name, change summary, and on-call contact
- Release notes summarizing user-facing changes must be published to the internal changelog within 24 hours of every production deployment
- Teams shipping breaking API changes must provide a minimum 30-day deprecation notice to consumers before removing or modifying existing interfaces

## Related Standards

- [[STANDARD-041|CI/CD Secret Management Standard]]
- [[STANDARD-039|Deployment Manifest Standard]]
