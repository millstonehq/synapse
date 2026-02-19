---
id: REPORT-024
type: report
title: SKU Growth Forecast Report
status: proposed
owner: Inventory Tech Lead
created: '2024-03-19T20:16:09.618Z'
updated: '2025-07-19T01:28:15.962Z'
tags:
  - report
  - inventory-management
summary: SKU Growth Forecast Report
company: InventoryManagement
report_month: 2024-07
report_type: portfolio
overall_health: poor
confidence: high
active_initiatives_count: 8
critical_risks_count: 2
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Active SKU count | — | 872,000 | Informational |
| SKU creation rate (monthly) | — | 18,400 | Growing fast |
| Registry query P95 | < 50ms | 62ms | Below target |
| Bulk export completion | < 30 min | 44 min | Below target |
| Barcode resolution cache hit rate | > 95% | 93.2% | Below target |
| Duplicate SKU detection rate | 100% | 97.8% | Below target |

SKU count crossed 872,000 in July with a monthly growth rate of 18,400 new SKUs. At this rate the registry will reach 1M SKUs by October 2024. Current system performance is showing strain at scale: query latency, bulk export time, and cache hit rates are all below target.

## Key Highlights

- **1M SKU threshold approaching**: Projected to reach 1M active SKUs by October 2024. Performance profiling shows the PostgreSQL full-text search index becomes the bottleneck above 900,000 records at current hardware.
- **Bulk export degradation**: Full catalog exports now take 44 minutes against a 30-minute target. The export job uses a sequential read scan that does not benefit from partitioning.
- **Duplicate detection gap**: The 97.8% duplicate detection rate means approximately 400 duplicate SKUs may have been created in July. Investigation into the 2.2% miss rate is underway.

## Active Initiatives

1. **PostgreSQL index optimization**: Partitioning the SKU table by category_id to reduce index size per partition; estimated 35% query improvement.
2. **Bulk export parallelization**: Rewriting the export job to use parallel partition reads; target: < 15 minutes for 1M SKU catalog.
3. **Duplicate detection hardening**: Adding composite unique index on (supplier_id, supplier_sku_code) to prevent duplicates at the database level.
4. **Barcode cache warm-up**: Implementing predictive cache warm-up for high-frequency barcodes to improve hit rates.
5. **SKU archiving policy**: Defining and implementing archival criteria for inactive SKUs (no movements in 18 months) to control active count growth.
6. **Search service migration**: Evaluating Elasticsearch as a dedicated SKU search backend to offload full-text queries from PostgreSQL.
7. **Capacity planning documentation**: Formal capacity model for the registry service at 1M, 2M, and 5M SKU counts.
8. **API rate limiting**: Adding per-client rate limits to the SKU lookup API to prevent uncontrolled bulk scan consumers from impacting latency.

## Incidents

No incidents this period.

## Risks

- **Critical**: Registry will exceed 900,000 SKUs in August, at which point query P95 is projected to exceed 120ms based on load testing. Index optimization must be deployed before then.
- **Critical**: Bulk export jobs are taking 44 minutes and growing. WMS onboarding processes depend on daily full exports; if export time exceeds the nightly window, onboarding will fail.

## Next Month Focus

- Deploy PostgreSQL table partitioning before 900,000 SKU threshold is reached
- Ship bulk export parallelization to restore < 30 minute SLA
- Fix duplicate detection gap with composite unique index
- Complete formal capacity planning documentation for 1M+ scale
