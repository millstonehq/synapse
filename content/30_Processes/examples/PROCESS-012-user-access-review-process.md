---
id: PROCESS-012
type: process
title: User Access Review Process
status: draft
owner: Director of Engineering
created: '2025-11-18T08:55:17.676Z'
updated: '2025-10-15T18:31:48.442Z'
tags:
  - process
  - user-authentication
summary: User Access Review Process
related_standards:
  - STANDARD-009
  - STANDARD-012
related_sops:
  - SOP-019
  - SOP-014
related_systems:
  - SYSTEM-008
example: true
---

## Purpose

User access reviews ensure that authentication privileges and role assignments remain appropriate over time. As users change roles, leave the organization, or reduce their scope of work, their access should be adjusted accordingly. This process defines the quarterly review cycle used to validate that all active user accounts and their granted permissions remain justified.

## Scope

- All human user accounts with access to production systems or sensitive data
- Service accounts and OAuth clients with long-lived credentials
- Privileged accounts including administrative roles and break-glass access
- Third-party integrations and partner OAuth applications with access to internal APIs

## Roles and Responsibilities

- **Director of Engineering**: Sponsors the quarterly review cycle and escalates unresolved access items
- **Team Leads**: Review and certify access for their direct reports and team-owned service accounts
- **Security Engineer**: Generates the access inventory report and validates that deprovisions are completed
- **HR**: Provides employee status data to identify accounts that should be deprovisioned due to termination or role change

## Triggers

- Quarterly review cycle begins (January, April, July, October)
- An employee termination or role change requiring immediate access review
- A security incident that prompts an out-of-cycle review

## Inputs

- Access inventory report from the identity management system including all active users, roles, and last-login timestamps
- HR employee status feed indicating active, terminated, or role-changed personnel
- List of OAuth clients and service accounts with their granted scopes per [[STANDARD-009|Password Hashing Standard]] logging data

## Outputs

- Certified access list with team lead signatures confirming each active account is justified
- Completed deprovisioning actions for all accounts identified for removal
- Findings report documenting access anomalies (orphaned accounts, excessive permissions, stale access) per [[STANDARD-012|Authentication Logging Standard]]

## Steps

1. Security Engineer generates the access inventory report and distributes it to team leads 5 business days before the review deadline
2. HR provides the current employee status feed; Security Engineer flags any mismatches between active accounts and HR data
3. Each team lead reviews their section of the access inventory and marks each account as: Approved, Modify, or Revoke
4. Team leads submit their certified access lists to Security Engineer within the review window (10 business days)
5. Security Engineer compiles all responses and identifies accounts with no certification received (treated as Revoke)
6. All Revoke and Modify actions are executed via the identity management system within 5 business days of the certification deadline
7. Deprovisioning is verified by Security Engineer by re-running the access inventory report and confirming removals
8. Director of Engineering reviews the findings report and signs off on completion

## Controls

- Access reviews must be completed within 20 business days of the review cycle start
- Accounts with no certification received within the review window are automatically deprovisioned
- Access review results are retained for 3 years for compliance audit purposes
- Privileged accounts that have not been used in 60 days are flagged for immediate review outside the quarterly cycle
