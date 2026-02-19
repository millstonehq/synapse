---
id: POSTMORTEM-050
type: postmortem
title: Usage Metering Data Loss 2025-03-25
status: deprecated
owner: On-Call Engineer
created: '2024-09-02T02:01:01.468Z'
updated: '2025-03-25T10:30:47.870Z'
tags:
  - postmortem
  - billing-engine
summary: Usage Metering Data Loss 2025-03-25
incident_number: INC-931
severity: SEV-1
incident_date: '2024-04-27'
detection_time: '2026-12-16T15:12:28.581Z'
resolution_time: '2024-06-02T02:15:22.028Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-095
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On March 25, 2025, the Usage Metering Service lost approximately 4 hours of raw usage events for ~200 customers due to a SQL Server storage failure during a maintenance window. The maintenance operation quiesced the primary SQL Server node without properly redirecting writes to the secondary, resulting in write failures that the ingest API silently swallowed rather than returning errors to callers. Events submitted during this window were accepted by the API but never persisted.

The data loss was detected approximately 2 hours after the maintenance window ended when an aggregation job produced anomalously low usage totals. Affected events were reconstructed from product-side logs over a 2-hour recovery process.

## Timeline

- **01:00** - Scheduled SQL Server maintenance window begins. DBA initiates failover to secondary node.
- **01:08** - Primary SQL Server node quiesced. Writes should be directed to secondary, but the ODBC connection string used by the Usage Metering Service still points to the primary.
- **01:09** - Usage event writes begin failing silently; the ingest API's error handler incorrectly returns HTTP 202 on SQL write failure instead of 503.
- **01:09 - 05:00** - ~180,000 usage events across ~200 customers accepted by the API but not persisted.
- **05:00** - Maintenance window ends. Primary SQL Server restored. Writes resume normally.
- **07:12** - Aggregation job detects anomalously low usage totals for the 01:00-05:00 window; triggers alert.
- **07:18** - On-call acknowledges alert; begins investigation.
- **07:40** - Engineer confirms no raw events exist in the database for the affected window; correlates with maintenance window timing.
- **08:00** - Data recovery begins using product-side event logs as the source of truth.
- **10:00** - Approximately 95% of affected events reconstructed and backfilled. Remaining 5% (~9,000 events) not recoverable due to log rotation.
- **10:30** - Affected invoices for the 200 customers recalculated using reconstructed data. Incident closed.

## Impact

- **Duration**: ~4 hours of data loss (01:09 - 05:00 UTC, March 25)
- **Customers affected**: ~200 customers with active usage during the window
- **Data loss**: ~180,000 usage events; ~9,000 events (~5%) not recoverable
- **Revenue impact**: Estimated $12,000 in usage charges not billed due to unrecoverable events (company absorbed the loss rather than retroactive billing)
- **SLA impact**: Usage Metering availability SLA breached; data durability SLA breached (SEV-1)
- **Customer communications**: Affected customers notified proactively; those with material usage discrepancies received credit

## Root Cause Analysis

1. **Ingest API silently swallowed SQL write failures**: The event ingest API had a bug in its error handler that returned HTTP 202 (Accepted) on database write failure instead of HTTP 503 (Service Unavailable). This prevented callers from detecting the failure and retrying.

2. **Connection string not updated for failover**: The Usage Metering Service used a static ODBC connection string pointing to the primary SQL Server hostname rather than the Always On Availability Group listener, which automatically routes to the available node during failover. This is a known anti-pattern for SQL Server high availability.

## Resolution

1. Identified the data loss window from aggregation anomaly alert
2. Reconstructed events from product-side logs using an emergency backfill script
3. Recalculated affected customer usage aggregates with reconstructed data
4. Reissued invoices for customers with material discrepancies

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Fix ingest API error handler to return 503 on SQL write failure | Billing Engineering | P1 | 2025-04-01 | Completed |
| Switch SQL Server connection string to Always On Availability Group listener | Billing Engineering | P1 | 2025-04-01 | Completed |
| Add integration test asserting ingest API returns 503 on database unavailability | Billing Engineering | P1 | 2025-04-07 | Completed |
| Implement cross-region event replication for raw usage events | Billing Engineering | P2 | 2025-05-01 | In progress |
| Add event replay capability to recover from ingest failures | Billing Engineering | P2 | 2025-05-15 | In progress |
| Update maintenance runbook: verify all service connection strings before quiescing primary | Platform SRE | P1 | 2025-04-03 | Completed |

## Lessons Learned

- **What went well**: Aggregation anomaly detection caught the data loss within 2 hours of the maintenance window ending. Event reconstruction from product logs was successful for 95% of events.
- **What went poorly**: The ingest API silently accepting failures was the worst possible failure mode for a data pipeline — it made the failure invisible to callers. The connection string maintenance oversight compounded the impact.
- **What was lucky**: Product-side event logs were not yet rotated, enabling 95% data recovery. If the incident had been detected 12 hours later, recovery would have been impossible for all events.
