---
id: SOP-080
type: sop
title: Onboard Team to PagerDuty SOP
status: approved
owner: Release Manager
created: '2024-09-10T02:37:08.855Z'
updated: '2026-12-08T04:45:00.409Z'
tags:
  - sop
  - monitoring-stack
summary: Onboard Team to PagerDuty SOP
related_process: PROCESS-046
related_systems:
  - SYSTEM-038
example: true
---

## Preconditions

- The new team has completed service observability onboarding and has alerts defined in AlertManager
- All engineers who will be on-call have PagerDuty accounts (request via IT ticketing system if needed)
- The team lead has provided a list of team members, their shift preferences, and the initial on-call rotation schedule
- The AlertManager routing rules for the team's services have been configured (see SOP-076)

## Materials/Access

- PagerDuty admin access or access to a PagerDuty account with team management permissions
- The team's alert names and severity classifications from AlertManager
- List of team members' names, email addresses, and phone numbers for PagerDuty contact methods
- Access to the PagerDuty Slack integration for configuring the team's incident channel

## Procedure

1. Log into PagerDuty and navigate to Teams. Create a new team with the naming convention `{Team Name} Engineering` (e.g., `Auth Engineering`). Add the team lead as the team manager.
2. Add all on-call engineers to the new team. Confirm each engineer's contact methods (phone, SMS, email) are configured and they have downloaded the PagerDuty mobile app.
3. Create an Escalation Policy named `{Team Name} Escalation Policy` with the following tiers: Tier 1 — primary on-call engineer (5 min ack timeout), Tier 2 — backup on-call engineer (15 min), Tier 3 — team lead (30 min).
4. Create an On-Call Schedule named `{Team Name} Primary` with the rotation type (weekly is standard), team members, and handoff time. Add a backup schedule `{Team Name} Backup` offset by 30 minutes.
5. Create a PagerDuty Service named `{Team Name} - Production` and associate it with the escalation policy created in step 3.
6. Generate the PagerDuty integration key for the new service. Add this key to the AlertManager configuration for the team's routing rules (follow SOP-076 for the AlertManager change).
7. Send a test incident from AlertManager: `amtool alert add alertname="ONBOARDING_TEST" team="{team}" severity="critical"`. Verify the test alert reaches the primary on-call engineer's PagerDuty notification.
8. Confirm the engineer receives the notification and can acknowledge/resolve from the PagerDuty mobile app. Resolve the test incident.
9. Schedule the first on-call handoff walkthrough call with the team lead to confirm all engineers understand the SOP-071 response process.

## Validation

- All team engineers appear in the PagerDuty team roster with correctly configured contact methods
- The escalation policy shows the correct tier structure and timeouts
- The on-call schedule covers 24x7 with no gaps in coverage
- A test incident was received and acknowledged successfully by the primary on-call
- AlertManager is routing the team's production alerts to the new PagerDuty service

## Rollback

1. If the PagerDuty service was created in error, delete the service and revoke the integration key.
2. Update the AlertManager routing rules to remove the incorrect PagerDuty integration key.
3. If the test incident was not received, check the AlertManager routing configuration and the PagerDuty integration key before troubleshooting further.
