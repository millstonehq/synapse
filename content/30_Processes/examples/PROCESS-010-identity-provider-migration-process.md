---
id: PROCESS-010
type: process
title: Identity Provider Migration Process
status: draft
owner: Director of Engineering
created: '2025-04-10T13:55:08.838Z'
updated: '2025-04-18T05:01:26.361Z'
tags:
  - process
  - user-authentication
summary: Identity Provider Migration Process
related_standards:
  - STANDARD-011
  - STANDARD-007
related_sops:
  - SOP-011
  - SOP-016
related_systems:
  - SYSTEM-010
example: true
---

## Purpose

Migrating from one identity provider to another is a high-risk operation that affects every authenticated user. Without a structured process, migrations risk user lockout, data loss, and security gaps during the transition period. This process defines the phased approach for safely migrating users between identity providers with no forced re-authentication for end users.

## Scope

- Full migrations from one primary identity provider to another
- Partial migrations (subset of users or tenants moving to a new provider)
- Protocol upgrades (e.g., SAML to OIDC) within the same identity provider
- Attribute schema changes that require re-mapping of user identifiers

## Roles and Responsibilities

- **Director of Engineering**: Sponsors the migration, approves the migration plan, and owns executive communication
- **Platform Lead**: Leads technical planning and coordinates engineering execution across teams
- **Identity Engineer**: Implements dual-provider support, attribute mapping, and migration tooling
- **QA Engineer**: Validates migrated user flows and confirms parity between old and new provider behavior

## Triggers

- Business decision to change primary identity provider vendor
- Current identity provider announcing end-of-life for a required protocol or feature
- Security assessment identifying unacceptable risk with the current provider

## Inputs

- Signed-off migration plan including user impact assessment and rollback strategy
- New provider configuration and metadata validated against [[STANDARD-007|JWT Token Format Standard]]
- User data export from current provider (identifiers, group memberships, MFA enrollments)

## Outputs

- All target users successfully authenticated via the new identity provider
- Decommission plan for the legacy provider with a defined sunset date
- Updated OAuth scope documentation per [[STANDARD-011|OAuth Scope Naming Standard]]

## Steps

1. Conduct discovery: audit current provider usage, user counts, attribute dependencies, and downstream service integrations
2. Configure the new identity provider in a non-production environment and validate attribute mapping and token format
3. Implement dual-provider support in the authentication service so both providers can authenticate users simultaneously
4. Migrate a pilot group (5% of users) and validate their login flows, group memberships, and downstream access
5. Monitor pilot group for 7 days; resolve any attribute mapping or permission discrepancies before continuing
6. Execute phased rollout in cohorts of 20% per week, monitoring authentication success rates after each cohort
7. Disable new user enrollment on the legacy provider once 100% of users are migrated
8. Decommission legacy provider integration after a 30-day observation period with no legacy authentications

## Controls

- Dual-provider mode must be maintained for a minimum of 30 days to allow rollback without user impact
- User identifier mapping between old and new provider must be verified before migration begins to prevent account duplication
- Migration progress and authentication success rates must be reported daily to the Director of Engineering
- Rollback to the legacy provider must be executable within 1 hour at any point during the migration
