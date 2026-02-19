---
id: REPORT-075
type: report
title: Billing Platform March 2025 Status Report
status: review
owner: Billing Tech Lead
created: '2025-07-27T06:21:01.576Z'
updated: '2025-08-02T17:34:55.201Z'
tags:
  - report
  - billing-engine
summary: Billing Platform March 2025 Status Report
company: BillingEngine
report_month: 2024-01
report_type: company
overall_health: good
confidence: medium
active_initiatives_count: 6
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Billing Engine availability | 99.95% | 99.96% | On target |
| Invoice generation P95 latency | < 30s | 25s | On target |
| Tax calculation P95 latency | < 800ms | 780ms | At risk |
| Usage ingest error rate | < 0.05% | 0.04% | On target |
| Invoices generated | — | 44,100 | Tracking |
| Avalara API calls | < 3.5M/month | 2.8M | On target (new tier) |

March performance was broadly on target. Tax calculation P95 latency crept up to 780ms (target: 800ms) during end-of-month invoice generation due to Avalara rate limiting before the new tier was fully activated. Availability SLA was met.

## Key Highlights

- **Avalara contract upgraded to 5M calls/month tier**: Tier upgrade completed March 3. Retroactive to March 1. Overage risk eliminated for the foreseeable future given current growth trajectory.
- **Self-Service Billing Portal Phase 2 shipped**: Dispute submission and usage breakdown views are live. Support ticket volume for billing inquiries fell 48% vs. January baseline.
- **Usage Metering data loss incident resolved**: The March 25 incident (POSTMORTEM-050) resulted in approximately 4 hours of raw usage events lost for ~200 customers. Events were reconstructed from product-side logs. All affected invoices reissued.

## Active Initiatives

1. **Self-Service Billing Portal** (Phase 3 of 3): Revenue forecasting view and bulk export in development. Target: April release.
2. **ClickHouse migration** (Phase 1): Cluster provisioned. Schema migration scripts in review. Shadow writing to ClickHouse begins April 1.
3. **Usage Metering resilience hardening**: Following the March 25 incident, adding event replay capability and cross-region replication for raw event storage.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Mar 25 | SEV-1 | ~2 hrs | Usage Metering data loss — raw event storage failure during a SQL Server maintenance window that was not properly quiesced. See POSTMORTEM-050. |
| Mar 3 | SEV-4 | 30 min | Avalara rate limiting during peak invoice generation before new tier activated. Tax calculation fell back to cached results; no invoice failures. |

## Risks

- **High**: Usage Metering raw event storage relies on a single SQL Server instance without cross-region replication. This was the root cause of the March 25 incident. Mitigation in progress.
- **Medium**: ClickHouse shadow writing begins in April. If data divergence is found between SQL Server and ClickHouse aggregates, the migration timeline will slip.

## Next Month Focus

- Complete Self-Service Billing Portal Phase 3
- Begin ClickHouse shadow writing and validate aggregate consistency
- Ship usage event replay capability
- Conduct Q1 retrospective and update billing platform roadmap
