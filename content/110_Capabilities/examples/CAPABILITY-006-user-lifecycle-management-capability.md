---
id: CAPABILITY-006
type: capability
title: User Lifecycle Management Capability
status: approved
owner: Head of Engineering
created: '2025-09-20T06:34:27.746Z'
updated: '2025-02-02T11:40:28.860Z'
tags:
  - capability
  - user-authentication
summary: User Lifecycle Management Capability
evidence_links:
  - POLICY-008
  - PROCESS-007
  - STANDARD-009
example: true
---

## Domain

- User account creation and initial provisioning (invitation flow, JIT SSO provisioning, social login registration)
- Profile management (name, email, verified contact information, avatar)
- Account status management (active, suspended, locked, deleted)
- Access review and privilege recertification
- Account recovery (password reset, MFA factor recovery, backup codes)
- Offboarding and deprovisioning (session termination, data retention, account deletion)

## Maturity (0-5)

- User provisioning: 3/5 - JIT SSO provisioning and invitation flow are implemented; automated SCIM provisioning is not yet available; manual provisioning by admins is required for non-SSO users
- Profile management: 4/5 - Users can manage name, email, avatar, and verified contact information; email change requires re-verification; bulk profile management is available to org admins
- Account status management: 4/5 - Suspension, reactivation, and deletion are available via admin console with immediate session termination; automated suspension on inactivity is not implemented
- Access review: 2/5 - Manual access reviews are conducted quarterly via the PROCESS-012 process; no tooling support for automated access review workflows or recertification campaigns
- Account recovery: 4/5 - Password reset, backup codes, and admin-mediated MFA reset are available; account recovery for users who have lost both their MFA factor and backup codes requires an identity verification step
- Offboarding/deprovisioning: 3/5 - Admin-initiated suspension and session termination are available; automated deprovisioning on HR system termination is not yet integrated; SCIM DELETE is not implemented

## Metrics

- Average time to provision a new user: < 5 minutes via invitation; < 60 seconds via JIT SSO
- Account deletion request fulfillment time: < 30 days (meets GDPR requirement)
- MFA factor recovery support tickets per month: ~40 (target: < 20; driving passkey adoption to reduce)
- Suspended accounts reactivated erroneously: 0 in last 12 months

## Evidence Links

- [[POLICY-008|User Account Lifecycle Policy]] — Policy governing account creation, modification, and deletion
- [[PROCESS-007|User Onboarding Process]] — Provisioning process for new users
- [[STANDARD-009|Authentication Credential Standard]] — Credential requirements during account creation

## Notes

- SCIM integration is on the 12-month roadmap; it is the primary gap preventing a maturity increase for User Provisioning
- Automated suspension on inactivity (>90 days) has been requested by multiple enterprise customers for compliance; this is planned for Q3
- Account deletion currently soft-deletes records; hard deletion after 30-day retention period is implemented but not fully automated
