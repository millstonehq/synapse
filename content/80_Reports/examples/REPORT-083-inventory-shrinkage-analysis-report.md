---
id: REPORT-083
type: report
title: Inventory Shrinkage Analysis Report
status: draft
owner: Inventory Tech Lead
created: '2024-01-28T19:32:11.609Z'
updated: '2026-04-24T08:31:50.566Z'
tags:
  - report
  - inventory-management
summary: Inventory Shrinkage Analysis Report
company: InventoryManagement
report_month: 2026-08
report_type: portfolio
overall_health: fair
confidence: high
active_initiatives_count: 5
critical_risks_count: 2
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Platform-wide shrinkage rate | < 0.5% of GMV | 0.74% of GMV | Off target |
| Reconciliation discrepancy resolution rate | > 90% within 7 days | 83% | Off target |
| Cycle count completion rate | > 95% of scheduled counts | 91% | At risk |
| Stock accuracy (system vs physical) | > 99% of SKUs within tolerance | 98.2% | At risk |
| Adjustment event processing latency (P95) | < 30s | 18s | On target |
| Shrinkage write-off processing time | < 48 hours | 31 hours avg | On target |

Inventory shrinkage remains above the platform target of 0.5% of GMV, with the August rate reaching 0.74%. The primary contributors are damage write-offs at three high-throughput warehouse locations and a cluster of persistent discrepancies in a fast-fashion merchant's apparel category.

## Key Highlights

- **Shrinkage hotspot identified**: Three warehouse locations (WH-007, WH-014, WH-022) account for 58% of total platform damage write-offs by value. All three are third-party logistics (3PL) providers where our damage inspection process is applied inconsistently. Engagement with the 3PL operators is underway to standardise inspection workflows.
- **Apparel category anomaly**: One merchant's apparel SKUs show a 2.1% shrinkage rate, six times the platform median for apparel. Investigation found that colour and size variants are frequently miscounted during cycle counts because the SKU Registry does not surface variant groupings clearly in the count interface. A UX improvement is planned for Q4.
- **Blind count enforcement improved**: Rolled out enforcement of blind count mode (hiding system quantities from counters during cycle counts) to all warehouse locations. Previously, 4 of 14 integrated warehouses were still showing system quantities to counters. The change is expected to reduce anchoring bias and improve count accuracy.
- **Write-off approval workflow deployed**: A new two-step approval workflow for damage write-offs over $500 was deployed in August. Write-offs now require supervisor approval before the adjustment event is published. 47 write-offs were intercepted for review; 12 were rejected as erroneous, preventing $14,200 in incorrect write-offs.

## Active Initiatives

1. **3PL Damage Inspection Standardisation** (in progress): Engaging WH-007, WH-014, WH-022 operators to align their receiving inspection process with our damage grading standard. Target: reduce 3PL damage write-off rate by 30% within 90 days.
2. **Apparel Variant Display Improvement** (planned Q4): Update the cycle count interface to group SKU variants by parent product for apparel and other variant-heavy categories, reducing miscounting.
3. **Automated Shrinkage Anomaly Detection** (design): Build a weekly shrinkage anomaly detection job that flags merchants and warehouses with shrinkage rates more than 2 standard deviations above their 90-day baseline. Reduces reliance on manual review to catch outliers.
4. **Reconciliation SLA Enforcement** (in progress): Implementing automatic escalation when a reconciliation discrepancy is open for more than 5 days without resolution action. Currently 11% of discrepancies exceed 7 days without closure.
5. **Shrinkage Dashboard for Operations** (in progress): Building a dedicated shrinkage analytics dashboard in the operations portal showing write-off trends by category, warehouse, and merchant. Replaces the current monthly manual report.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Aug 09 | SEV-3 | 4 hours | Write-off approval service was unreachable for 4 hours due to a failed Kubernetes pod eviction. All large write-offs were queued and processed once the service recovered. No stock data was lost. |

## Risks

- **Critical**: The 0.74% shrinkage rate exceeds the 0.5% GMV target. Without intervention at the three 3PL hotspot locations, the annual shrinkage cost is projected to exceed $1.2M. The 3PL engagement process is underway but results are not yet visible in the metrics.
- **Critical**: Cycle count completion rate at 91% means approximately 9% of scheduled counts are not being executed. Uncounted SKUs cannot be reconciled and accumulate undetected discrepancies. Escalation to warehouse managers is needed where count completion is consistently below 95%.
- **Medium**: The apparel variant miscounting issue affects a single high-GMV merchant. If the issue is not resolved before the merchant's peak trading period in Q4, shrinkage in this category could worsen significantly during high-volume periods.

## Next Month Focus

- Complete 3PL engagement at WH-007 and WH-014; measure damage write-off rate change at those locations
- Launch shrinkage anomaly detection in shadow mode to validate alert accuracy before enabling notifications
- Resolve remaining reconciliation discrepancies older than 7 days (currently 34 open)
- Publish the new shrinkage dashboard to the operations portal for the platform team and merchant success teams
