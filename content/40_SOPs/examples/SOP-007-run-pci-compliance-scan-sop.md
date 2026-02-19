---
id: SOP-007
type: sop
title: Run PCI Compliance Scan SOP
status: draft
owner: DevOps Lead
created: '2025-04-29T13:05:20.819Z'
updated: '2025-03-11T01:59:37.954Z'
tags:
  - sop
  - payment-processing
summary: Run PCI Compliance Scan SOP
related_process: PROCESS-003
related_systems:
  - SYSTEM-004
example: true
---

## Preconditions

- The PCI scanning tool (ASV-approved scanner) is configured and has valid credentials for all in-scope IP ranges
- The CDE system inventory has been reviewed and confirmed as current within the last 30 days
- Scan window has been agreed with the on-call team (scans may generate elevated traffic on scanned systems)
- Compliance Officer has been notified that a scan is about to commence
- Any recent network topology changes have been documented and the scan configuration updated to reflect them

## Materials/Access

- Access to the ASV-approved PCI scanning platform (e.g., Qualys, Tenable)
- CDE asset inventory list with IP addresses and hostnames for all in-scope systems
- Access to the security findings dashboard for reviewing scan results
- Access to #security-compliance Slack channel for status communication
- Ticket system access to file remediation tickets for any findings

## Procedure

1. Log in to the PCI scanning platform and navigate to the scan configuration for the cardholder data environment.
2. Verify the scan target list matches the current CDE asset inventory; add or remove any IPs that have changed since the last scan.
3. Notify #security-compliance: "PCI compliance scan starting now. Scope: [CDE systems]. Estimated duration: [X hours]."
4. Launch the scan from the scanning platform and record the scan job ID.
5. Monitor scan progress; if any scanned system shows unexpected downtime or performance degradation, pause the scan and notify the on-call engineer.
6. After scan completion, download the scan report in PDF and CSV formats.
7. Review the findings: categorize as Pass, Fail, or Exception Required; note all Fail items with CVSS score and affected system.
8. Create remediation tickets for all failing findings; assign priority based on CVSS score (Critical/High = 30-day SLA, Medium = 90-day SLA).
9. Submit the scan report to the Compliance Officer; update the compliance calendar with the next scheduled scan date.

## Validation

- Scan completed successfully with no scan errors or unreachable targets
- All in-scope CDE systems appear in the scan results
- Remediation tickets created for every failing finding with correct priority and owner assignment
- Compliance Officer has received and acknowledged the scan report
- Scan report archived in the compliance document store with scan date and job ID

## Rollback

1. If the scan causes service disruption on a CDE system, immediately stop the scan from the scanning platform console.
2. Notify the on-call engineer and post in #security-compliance with the systems affected and time of disruption.
3. Work with the on-call engineer to confirm the affected service has recovered to normal operation.
4. Reschedule the scan for a lower-traffic maintenance window and update scan rate-limiting settings to reduce impact.
5. Document the disruption in the compliance log and notify the Compliance Officer of the postponement.
