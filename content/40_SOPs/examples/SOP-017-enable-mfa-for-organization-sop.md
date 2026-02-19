---
id: SOP-017
type: sop
title: Enable MFA for Organization SOP
status: approved
owner: SRE Lead
created: '2024-09-20T12:46:30.683Z'
updated: '2026-12-06T08:32:13.104Z'
tags:
  - sop
  - user-authentication
summary: Enable MFA for Organization SOP
related_process: PROCESS-012
related_systems:
  - SYSTEM-007
example: true
---

## Preconditions

- The MFA enablement has been authorized by the CISO or Director of Engineering
- An approved change ticket exists for this configuration change
- User communication has been drafted and approved for distribution prior to enforcement
- All users have been given a minimum 14-day enrollment grace period notice before enforcement begins
- The MFA enrollment completion rate has been tracked and is above 80% for the target group

## Materials/Access

- Admin access to the identity management system with organization policy configuration permissions
- Access to the authentication service feature flag configuration
- User communication templates and email distribution list
- MFA enrollment status report from the identity management system
- Change ticket ID

## Procedure

1. Pull the MFA enrollment status report from the identity management system to confirm current enrollment percentages by team or user group.
2. Send the MFA enforcement notice to all users who have not yet enrolled, including the deadline date and enrollment instructions link.
3. Configure the MFA enforcement policy in the identity management system in "advisory" mode (prompt but do not block) for a 7-day transition period.
4. Monitor MFA enrollment rate daily during the transition period; escalate to team leads if any team is below 70% enrollment.
5. After the 7-day transition period, switch the MFA enforcement policy to "enforced" mode, which blocks login for non-enrolled users.
6. Monitor login success rate and MFA challenge failure rate for the first 24 hours after enforcement begins.
7. Review the list of users blocked by MFA enforcement; contact each blocked user's manager to coordinate enrollment.
8. After 48 hours of stable enforcement, close the change ticket and publish the MFA adoption metrics to the security dashboard.

## Validation

- MFA enforcement policy shows "enforced" status in the identity management system
- Login attempts from non-enrolled users are rejected with an MFA enrollment required error
- MFA challenge success rate is above 95% for enrolled users
- No elevated helpdesk ticket volume beyond anticipated enrollment support requests

## Rollback

1. If a critical operational user group is inadvertently blocked, temporarily exempt that group in the identity management policy while coordinating their enrollment.
2. If the MFA enforcement causes authentication service errors beyond the SLO, revert the policy to "advisory" mode immediately by updating the configuration in the identity management system.
3. If a defect in the MFA challenge flow is discovered post-enforcement, revert to advisory mode and open an urgent bug ticket; do not leave users permanently blocked by a broken MFA flow.
4. Document all rollback actions in the change ticket with the reason for rollback and the re-enforcement target date.
