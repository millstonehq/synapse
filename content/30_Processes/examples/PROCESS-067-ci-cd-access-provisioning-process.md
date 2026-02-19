---
id: PROCESS-067
type: process
title: CI/CD Access Provisioning Process
status: approved
owner: Platform Lead
created: '2024-10-09T19:00:16.630Z'
updated: '2025-06-09T21:20:29.668Z'
tags:
  - process
  - ci-cd-platform
summary: CI/CD Access Provisioning Process
related_standards:
  - STANDARD-040
  - STANDARD-037
related_sops:
  - SOP-061
  - SOP-066
related_systems:
  - SYSTEM-035
example: true
---

## Purpose

Govern the provisioning, modification, and revocation of access to CI/CD platform systems — specifically GitHub Actions, Harbor container registry, ArgoCD, and the Release Dashboard — to ensure that access rights are granted with appropriate authorization, tracked for audit purposes, and revoked promptly when no longer needed. This process exists because CI/CD platform access carries elevated risk: an engineer with deployment permissions can affect production systems, and a user with Harbor push access can introduce unauthorized artifacts into the pipeline.

The process integrates with the organization's identity provider (SSO/OIDC) for authentication but manages CI/CD-specific authorization separately, as the access tiers in CI/CD systems do not map directly to standard RBAC roles.

## Scope

- GitHub Actions: runner access, secret access, and organization-level workflow permissions
- Harbor container registry: project read access, push access, and administration
- ArgoCD: application sync permissions, cluster administration
- Release Dashboard: viewer access, approver role, and platform admin
- CI/CD service account credentials (non-human identities used by pipelines)

## Roles and Responsibilities

- **Requester**: The engineer or engineering manager requesting access. Responsible for: submitting a completed access request with business justification and selecting the minimum required access tier.
- **Platform Team Member**: Reviews and approves standard access requests. Responsible for: verifying the justification, confirming the requested tier is appropriate, and provisioning access within the SLA.
- **Platform Team Lead**: Approves elevated access requests (ArgoCD cluster admin, Harbor registry admin). Responsible for: additional scrutiny of high-privilege requests and quarterly access reviews.
- **IT/Security**: Receives copies of access grant and revocation events for audit log purposes. Responsible for: flagging anomalous access patterns in quarterly reviews.
- **[[SYSTEM-035|Release Dashboard Service]]**: The system of record for approver role assignments; updated as part of this process.

## Triggers

- New engineer onboarding requiring CI/CD platform access
- Engineer changing teams with different access requirements
- Engineer offboarding (revocation path)
- Service team requiring a new CI/CD service account for a new pipeline
- Quarterly access review identifying stale or excessive access rights

## Inputs

- Completed access request ticket (Jira template: "CI/CD Access Request") with: requester identity, systems requested, access tier, business justification, manager approval
- For elevated access (ArgoCD admin, Harbor admin): Platform Team Lead sign-off
- For service account requests: service name, owning team, and description of pipeline use case

## Outputs

- Access provisioned in the requested system(s) within the SLA (standard: 1 business day, elevated: 2 business days)
- Access grant recorded in the CI/CD access log (maintained by the Platform team in the access management spreadsheet)
- Slack notification to the requester confirming access has been granted
- For service accounts: Kubernetes Secret containing the generated credential, scoped to the service's namespace

## Steps

1. Requester submits a Jira ticket using the "CI/CD Access Request" template, selecting the system, access tier, and providing business justification; manager approval is required for tiers above "read"
2. Platform Team Member reviews the request: verifies the justification, confirms the requested tier matches the stated need, and checks that the requester does not already have equivalent access
3. For standard access (Harbor read, Release Dashboard viewer, ArgoCD read): Platform Team Member provisions access and marks the ticket resolved
4. For elevated access (Harbor push, ArgoCD sync, Release Dashboard approver): Platform Team Lead reviews and approves before provisioning; Platform Team Member then provisions
5. For service account requests: Platform Team Member generates a service account credential, stores it as a Kubernetes Secret in the requesting service's namespace, and records the credential metadata (not the credential value) in the access log
6. Platform Team Member notifies the requester via Slack with confirmation and any relevant access documentation links
7. Platform Team Member updates the access log with: system, access tier, requester, approver, date granted, and review date (set to 90 days for standard access, 30 days for elevated access)
8. On offboarding: Engineering Manager submits a revocation request; Platform Team Member revokes access across all CI/CD systems within 1 business day and updates the access log

## Controls

- All access grants require a recorded justification; zero-justification access grants are prohibited
- Elevated access (ArgoCD cluster admin, Harbor registry admin) is restricted to a maximum of 3 platform engineers at any time
- Access is reviewed every 90 days for standard tiers and every 30 days for elevated tiers; stale access is revoked without re-request
- Service account credentials must be rotated every 180 days; the access log tracks rotation due dates
- Offboarding revocation must complete within 1 business day; violations are reported to the security team
