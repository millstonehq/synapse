---
id: PRD-008
type: prd
title: Admin User Management Console PRD
status: approved
owner: Head of Product
created: '2025-04-08T22:14:17.157Z'
updated: '2025-08-23T09:06:46.615Z'
tags:
  - prd
  - user-authentication
summary: Admin User Management Console PRD
related_tdds:
  - TDD-007
  - TDD-008
example: true
related_standards:
  - STANDARD-012
---

## Summary

The Admin User Management Console is a web interface that gives organization administrators full visibility and control over their organization's users, roles, authentication policies, and active sessions. It replaces a mix of API scripts and support-mediated workflows with a self-service UI. This product builds on the token infrastructure from [[TDD-007|TDD-007: Token Refresh Service TDD]] and the RBAC Permission Engine from [[TDD-008|TDD-008: RBAC Permission Engine TDD]].

## Goals

- Reduce admin-related support tickets by 60% by enabling self-service user management
- Enable admins to enforce security policies (MFA requirement, SSO enforcement, session limits) without engineering involvement
- Provide audit log visibility for compliance and incident investigation
- Support organizations with up to 50,000 users without performance degradation

## In Scope

- User listing, search, and filtering (by status, role, MFA status, last login)
- User profile viewing and editing (name, email, role assignments)
- Role assignment and revocation (using RBAC roles from TDD-008)
- User suspension and reactivation
- Session management: view and terminate active sessions for any user
- MFA policy enforcement: require MFA for all org users or specific roles
- Bulk operations: bulk role assignment, bulk suspension, bulk invitation
- Authentication audit log: view login events, failures, MFA challenges per user
- Admin activity log: record all admin actions (who changed what, when)

## Out of Scope

- Cross-organization user management (each admin manages only their own org)
- Billing and subscription management (separate product area)
- API key management (separate feature)
- User data export in bulk (covered separately by data portability PRD)

## Users and Flows

Organization administrators (users with the `org:admin` role) are the primary audience. An admin navigating to the console sees their organization's user list with key status indicators: MFA status, last login date, active sessions, and assigned roles. From the list, they can click into a user profile to view detailed history, change roles, or take actions like suspending the account or terminating all active sessions.

Compliance officers use the audit log view to investigate security events. They can filter by user, date range, and event type (login, MFA challenge, role change, session termination) and export results to CSV for external review.

Security engineers use the policy configuration section to set org-wide requirements: MFA enforcement, session timeout overrides, SSO enforcement, and IP allowlists for admin access.

## Requirements

- User list must load within 2 seconds for organizations with up to 10,000 users
- All user management actions must be recorded in the admin activity log with actor, action, target, and timestamp
- Session termination must be effective within 30 seconds (session invalidated in Redis within one TTL refresh cycle)
- Bulk operations must support up to 500 users at a time with async processing and a completion notification
- Role changes must be reflected in newly issued tokens within 60 seconds (cache TTL from TDD-008)
- MFA enforcement policy must prevent non-MFA users from completing login after the policy is activated (grace period: configurable, default 7 days)
- Admin activity log must be immutable and retained for 90 days minimum
- The console must be accessible (WCAG 2.1 AA) and responsive for desktop and tablet viewports

## KPIs

- **Support ticket reduction**: Target 60% fewer admin-related support tickets within 3 months of launch
- **Admin action completion rate**: Target > 95% of admin actions completed without support intervention
- **Time to suspend**: Target < 60 seconds from admin decision to user session termination
- **Audit log usage**: Target > 40% of organizations with >50 users using audit log monthly

## Information Architecture

- Admin console: /admin/users — user list with search and filter
- /admin/users/{id} — user detail and management actions
- /admin/users/{id}/sessions — active sessions with terminate action
- /admin/users/{id}/audit-log — user-specific authentication event history
- /admin/audit-log — org-wide audit log with full filter capabilities
- /admin/policies — authentication policy configuration
- Technical design: [[TDD-008|TDD-008: RBAC Permission Engine TDD]]

## Data Model

- **AdminActionLog**: admin_user_id, action_type, target_user_id, target_resource, before_state, after_state, timestamp, ip_address
- **OrgPolicy**: org_id, mfa_required (bool), mfa_grace_period_days, sso_enforced (bool), session_timeout_hours, allowed_ip_ranges

## Non-Functional

- User list search must use full-text search with sub-500ms response time
- All admin actions must be logged asynchronously (do not block the action on log write)
- Console must handle concurrent access from multiple admins without race conditions on policy changes

## Constraints

- Admin console access requires the `org:admin` role; super-admin access (cross-org) is platform-staff only
- Policy changes take effect for new sessions only (existing sessions are not retroactively terminated unless explicitly done via bulk session termination)

## Risks

- **Risk**: Admin accidentally suspends a large number of users via bulk operation. Mitigation: Require explicit confirmation for bulk operations affecting > 50 users; show a preview before executing.
- **Risk**: Admin audit log is used as evidence in employment disputes; immutability is critical. Mitigation: Write audit log to append-only storage (PostgreSQL with row-level security preventing deletes); replicate to separate audit archive.

## Milestones

### M1: User Management Core (Month 1-2)
#### Deliverables
- User listing, search, filtering, and basic profile view
- Role assignment and revocation using RBAC roles
- User suspension and reactivation
- Admin activity log for all user management actions

#### Acceptance Criteria
- User list loads in < 2 seconds for 10,000-user org
- All role changes reflected in new tokens within 60 seconds
- 100% of admin actions recorded in audit log

### M2: Session Management and Policy Controls (Month 3)
#### Deliverables
- Active session view and per-user/bulk session termination
- MFA enforcement policy with configurable grace period
- Authentication audit log per user and org-wide
- Bulk user operations (role assignment, suspension)

#### Acceptance Criteria
- Session termination effective within 30 seconds
- MFA enforcement policy blocks non-MFA logins after grace period
- Bulk operations support up to 500 users
