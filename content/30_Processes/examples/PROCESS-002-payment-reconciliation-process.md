---
id: PROCESS-002
type: process
title: Payment Reconciliation Process
status: review
owner: Platform Lead
created: '2025-02-01T14:17:35.490Z'
updated: '2026-09-02T22:45:01.903Z'
tags:
  - process
  - payment-processing
summary: Payment Reconciliation Process
related_standards:
  - STANDARD-002
  - STANDARD-005
related_sops:
  - SOP-010
  - SOP-002
related_systems:
  - SYSTEM-005
example: true
---

## Purpose

This process ensures that the internal transaction ledger remains synchronized with settlement reports from payment gateways. Daily reconciliation identifies discrepancies between what the platform recorded and what the gateway settled, enabling timely financial corrections and preventing undetected revenue leakage or overcharges.

## Scope

- Daily reconciliation of all settled transactions against gateway settlement files
- Identification and classification of discrepancies: missing settlements, over/under captures, and failed refunds
- Escalation of unresolved discrepancies to Finance and the relevant gateway account manager

## Roles and Responsibilities

- **Reconciliation Engineer**: Operates and maintains the automated reconciliation pipeline and investigates technical discrepancies
- **Finance Analyst**: Reviews discrepancy reports, approves adjustments, and escalates to gateway account managers
- **On-Call Engineer**: Responds to reconciliation pipeline failures flagged by monitoring alerts
- **Platform Lead**: Reviews monthly reconciliation summary and approves process improvements

## Triggers

- Daily scheduled job runs at 06:00 UTC after gateway settlement files are available
- Manual trigger by Finance Analyst when a discrepancy is reported outside the automated window
- Gateway incident that may have affected settlement accuracy

## Inputs

- Gateway settlement files delivered via SFTP or API
- Internal transaction ledger export for the reconciliation period
- Previous reconciliation report (for carry-forward discrepancy tracking)

## Outputs

- Daily reconciliation report with match rate, discrepancy count, and total discrepancy value
- Discrepancy ticket for each unmatched item, classified by type and assigned to the responsible team
- Updated ledger adjustments for confirmed gateway errors, approved by Finance

## Steps

1. Automated job downloads settlement files from all active gateways for the prior business day
2. Settlement records are normalized to the internal transaction schema and matched against ledger records by transaction ID
3. Unmatched records are classified: platform-only (missing settlement), gateway-only (unrecorded charge), or value mismatch
4. Reconciliation report is generated and posted to the Finance Slack channel and email distribution list
5. Discrepancy tickets are auto-created for items exceeding $1.00 in value; smaller items are batched into a daily summary
6. Finance Analyst reviews tickets and either approves auto-adjustment or escalates to the gateway account manager
7. Platform Lead reviews the weekly summary for trend analysis and process improvement opportunities
8. Resolved discrepancies are closed in the ticket system with adjustment reference numbers

## Controls

- Reconciliation jobs that fail to complete must trigger a PagerDuty alert within 15 minutes
- Discrepancies exceeding $10,000 in aggregate must be escalated to Finance VP within 4 hours
- All ledger adjustments require dual approval: Reconciliation Engineer and Finance Analyst
- Reconciliation reports are retained for 7 years per financial record-keeping requirements
