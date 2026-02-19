---
id: MEETING-002
type: meeting
title: PCI Audit Preparation Sync
status: draft
owner: Principal Engineer
created: '2025-12-21T02:10:46.112Z'
updated: '2026-04-15T01:19:44.137Z'
tags:
  - meeting
  - payment-processing
summary: PCI Audit Preparation Sync
company: PaymentProcessing
topic: PCI Audit Preparation Sync
meeting_date: '2024-06-13T21:49:09.581Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
---

## Meeting Details

- **Project**: Annual PCI DSS Audit
- **Topic**: PCI Audit Preparation Sync
- **Date/Time**: 2024-06-13, 21:49 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager
- **Context**: Pre-audit sync to review evidence readiness, identify gaps in control documentation, and assign owners for outstanding audit deliverables

## Observations by Domain

- **Access Controls**: MFA is enforced on all CDE access; access review log for the last 12 months is complete and ready for auditors
- **Logging and Monitoring**: Transaction log retention meets the 12-month requirement; log integrity checks are passing but the verification report needs to be exported in auditor-friendly format
- **Vulnerability Management**: ASV scans are current for Q1 and Q2; Q2 scan shows two medium findings that require remediation evidence before the audit
- **Encryption**: TLS 1.2+ is enforced on all CDE endpoints; a legacy internal service was identified using TLS 1.1 and requires immediate remediation
- **Network Segmentation**: Firewall rules between CDE and non-CDE segments are documented; one undocumented rule added during the March incident response needs to be formalized

## Key Metrics & Data Points

- **Open High/Critical Vulnerability Findings**: 0 (all resolved in Q1)
- **Open Medium Findings from ASV Scan**: 2 (remediation in progress)
- **CDE Asset Inventory Last Updated**: 45 days ago (requires refresh before audit)
- **Access Review Completion**: 100% of CDE access reviewed in last 90 days
- **Evidence Documents Ready**: 23 of 28 required documents complete
- **Estimated Days to Audit**: 14

## Preliminary Scorecard Hooks

- Access Control Documentation: 5/5 - Complete and audit-ready
- Logging Evidence: 4/5 - Content complete; format export needed
- Vulnerability Remediation: 3/5 - Two open medium findings require evidence before audit
- Network Documentation: 3/5 - One undocumented firewall rule needs formalization
- Encryption Posture: 4/5 - One legacy TLS 1.1 service needs urgent remediation

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| TLS 1.1 service identified in CDE | High | High | Tech Lead | Disable TLS 1.1 and enforce TLS 1.2 minimum this week | 2024-06-17 |
| Open medium ASV findings at audit time | Medium | Medium | Principal Engineer | Deploy patches and generate remediation evidence | 2024-06-20 |
| CDE inventory out of date | Medium | High | Tech Lead | Refresh CDE asset inventory and have Compliance Officer sign off | 2024-06-18 |

## Decisions & Next Steps

### Decisions

- TLS 1.1 remediation is classified as a blocker; must be completed before the audit window opens
- CDE inventory refresh is assigned to Tech Lead with a 5-day deadline
- Audit evidence package to be assembled in the shared compliance folder by 2024-06-25

### Action Items

- Tech Lead to disable TLS 1.1 on the legacy internal service by 2024-06-17
- Principal Engineer to deploy ASV finding patches and capture remediation screenshots by 2024-06-20
- Principal Engineer to export log integrity verification report in auditor format by 2024-06-21

### Follow-ups

- Final readiness review scheduled for 2024-06-26 (one week before audit)
- Compliance Officer to review assembled evidence package and identify any remaining gaps
