---
id: PROCESS-007
type: process
title: User Account Provisioning Process
status: draft
owner: Platform Lead
created: '2024-05-30T04:53:12.783Z'
updated: '2025-04-16T01:58:38.399Z'
tags:
  - process
  - user-authentication
summary: User Account Provisioning Process
related_standards:
  - STANDARD-010
  - STANDARD-009
related_sops:
  - SOP-016
  - SOP-013
related_systems:
  - SYSTEM-010
example: true
---

## Purpose

This process governs the end-to-end lifecycle of creating, configuring, and activating user accounts across the organization's systems and platforms. It ensures that every new account is provisioned with the correct identity attributes, role assignments, and access entitlements before the user is permitted to log in.

By standardizing provisioning steps, this process reduces misconfiguration risk, enforces the principle of least privilege, and produces an auditable record of who authorized each account and when. It applies equally to employees, contractors, and service accounts, with appropriate variation in the approval chain for each category.

## Scope

- All new human user accounts in [[SYSTEM-010|the identity platform]], including employees, contractors, and temporary staff
- Service and application accounts that authenticate on behalf of systems
- Role and group assignments made at provisioning time
- Initial credential issuance and MFA enrollment in accordance with [[STANDARD-009|Authentication Standards]]

## Roles and Responsibilities

- **Requesting Manager**: Submits the provisioning request, specifies required roles and systems, and attests that access is necessary for the user's job function
- **IT Administrator**: Validates the request against [[STANDARD-010|Access Control Standards]], creates the account in [[SYSTEM-010|the identity platform]], and assigns the approved role set
- **Security Team**: Reviews and approves requests for privileged or elevated access; performs periodic spot-checks on provisioned accounts
- **New User**: Completes MFA enrollment per [[SOP-016|MFA Enrollment SOP]] and acknowledges the acceptable use policy before first login
- **HR System**: Acts as the authoritative source for employee identity data; triggers automated provisioning workflows on hire events

## Triggers

- HR system generates a new-hire event for an incoming employee or contractor
- A manager submits a manual access request for an existing user who requires access to an additional system
- An automated pipeline requests creation of a service account for a new application deployment
- A user transfers to a new role or department and requires a reprovisioning of entitlements

## Inputs

- Approved access request ticket containing: user full name, job title, department, required roles, and start date
- HR record confirming employment or engagement status
- Manager attestation that the requested access level is appropriate for the user's responsibilities
- For privileged accounts: Security Team approval and documented business justification

## Outputs

- Active user account in [[SYSTEM-010|the identity platform]] with correct attributes and role assignments
- Completed provisioning ticket with account ID, assigned roles, approver name, and timestamp
- MFA enrollment confirmation recorded against the account per [[SOP-016|MFA Enrollment SOP]]
- Audit log entry satisfying [[STANDARD-010|Access Control Standards]] retention requirements

## Steps

1. Requesting Manager opens a provisioning ticket, specifies the target user, required systems, and desired roles, and submits it for approval.
2. IT Administrator validates the request: confirms the user does not already have an active account, checks that the requested roles exist and are appropriately scoped, and verifies manager authorization.
3. Security Team reviews any request that includes privileged or administrative roles; approves or requests scoping reduction before the ticket advances.
4. IT Administrator creates the account in [[SYSTEM-010|the identity platform]], applies the approved role assignments, and sets an initial credential that forces a reset on first login.
5. IT Administrator follows [[SOP-013|Account Configuration SOP]] to configure profile attributes, group memberships, and any system-specific entitlements required by the ticket.
6. New User receives onboarding credentials via secure delivery channel and completes MFA enrollment per [[SOP-016|MFA Enrollment SOP]]; enrollment must be confirmed before the account is marked active.
7. IT Administrator marks the provisioning ticket as completed, attaches the account ID and enrollment confirmation, and closes the request.
8. Security Team is notified of any privileged accounts provisioned within the period; these are logged for the next access review cycle.

## Controls

- No account may be activated without a closed, approved provisioning ticket referencing a valid HR record or approved access request
- Privileged and administrative accounts require explicit Security Team sign-off, enforced as a mandatory approval gate in the ticketing workflow
- All provisioning actions are logged in the identity platform audit trail and retained in accordance with [[STANDARD-010|Access Control Standards]]
- Accounts not completed with MFA enrollment within 72 hours of creation are automatically suspended pending remediation
