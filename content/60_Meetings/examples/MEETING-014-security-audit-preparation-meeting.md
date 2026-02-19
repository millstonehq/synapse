---
id: MEETING-014
type: meeting
title: Security Audit Preparation Meeting
status: approved
owner: Principal Engineer
created: '2025-02-28T12:20:55.305Z'
updated: '2025-01-13T21:04:05.884Z'
tags:
  - meeting
  - user-authentication
summary: Security Audit Preparation Meeting
company: UserAuthentication
topic: Security Audit Preparation Meeting
meeting_date: '2026-08-04T04:15:21.711Z'
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

- **Project**: SOC 2 Type II Audit Preparation
- **Topic**: Security Audit Preparation — Authentication Controls Review
- **Date/Time**: 2026-08-04 9:00 AM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, QA Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Preparation session ahead of the annual SOC 2 Type II audit scheduled for 2026-09-15. Focus on authentication and access control evidence collection.

## Observations by Domain

- **Access Logging**: Authentication event logs are being collected but the retention period is currently 6 months; auditors require 12 months of evidence — retention policy needs immediate update
- **MFA Enforcement**: MFA enforcement is active for all privileged accounts but 3 service accounts are missing MFA enrollment documentation; auditors will flag these as gaps
- **Password Policy**: Password complexity policy is implemented in the identity system but the documented policy version in Confluence is 18 months out of date — documentation must be updated before auditors review it
- **User Access Reviews**: Last quarterly access review was completed on schedule; review records are retained but stored in a Google Drive folder, not the official GRC system
- **Key Rotation**: JWT key rotation has been performed but the rotation log shows one missed rotation event 4 months ago; need to document the compensating control that was in place

## Key Metrics & Data Points

- **Authentication log retention current**: 6 months (required: 12 months)
- **Privileged accounts with MFA**: 97% (3 service accounts missing documentation)
- **Last access review completion date**: 2026-07-01 (on schedule)
- **Password policy document last updated**: 2024-12-01 (18 months out of date)
- **JWT key rotations completed in last 12 months**: 3 of 4 scheduled (one missed)

## Preliminary Scorecard Hooks

- Audit Readiness: 2/5 - Multiple evidence gaps identified that will require remediation before audit
- Access Logging: 2/5 - Logs exist but retention period is insufficient for audit requirements
- Policy Documentation: 2/5 - Outdated documentation is a significant audit finding risk
- Access Controls: 4/5 - MFA and access review controls are functioning; documentation gaps present

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Log retention gap results in audit finding | High | High | DevOps Lead | Extend log retention to 12 months; backfill from cold storage if possible | 2026-08-11 |
| Outdated policy documentation creates compliance gap | High | High | Principal Engineer | Update password policy and session management policy docs before audit | 2026-08-18 |
| Missing MFA documentation for service accounts | Medium | High | Tech Lead | Document MFA status for all 3 service accounts or remediate enrollment | 2026-08-11 |
| Missed key rotation event flagged as control failure | Medium | Medium | Platform Lead | Document compensating control for missed rotation; implement rotation automation | 2026-08-25 |

## Decisions & Next Steps

### Decisions

- Log retention will be extended to 12 months immediately; cold storage backfill will be evaluated but not guaranteed
- All authentication-related policy documentation must be updated and reviewed before the audit date
- Access review records will be migrated from Google Drive to the GRC system

### Action Items

- Extend authentication log retention policy to 12 months (DevOps Lead — 2026-08-11)
- Update password complexity and session management policy documents (Principal Engineer — 2026-08-18)
- Document MFA status for 3 service accounts (Tech Lead — 2026-08-11)
- Migrate access review records to GRC system (Engineering Manager — 2026-08-20)
- Document compensating control for missed JWT rotation (Platform Lead — 2026-08-25)

### Follow-ups

- Pre-audit readiness review scheduled for 2026-09-08
- Auditor briefing call on authentication controls scheduled for 2026-09-15
