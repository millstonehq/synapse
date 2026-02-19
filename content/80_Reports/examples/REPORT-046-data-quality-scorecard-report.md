---
id: REPORT-046
type: report
title: Data Quality Scorecard Report
status: approved
owner: Data Tech Lead
created: '2025-02-07T20:05:41.455Z'
updated: '2025-09-16T07:14:02.225Z'
tags:
  - report
  - data-pipeline
summary: Data Quality Scorecard Report
company: DataPipeline
report_month: 2024-05
report_type: portfolio
overall_health: poor
confidence: high
active_initiatives_count: 6
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Overall quality pass rate | > 99.5% | 98.9% | Below target |
| Completeness checks pass rate | > 99% | 99.3% | On target |
| Uniqueness checks pass rate | > 99.9% | 99.7% | Below target |
| Referential integrity pass rate | > 99.5% | 98.1% | Below target |
| Schema compliance pass rate | > 99.9% | 99.8% | On target |
| CRITICAL violations | 0 per week | 3 this period | Below target |

The data quality scorecard for this period shows overall quality below the 99.5% target. Three CRITICAL violations occurred, all related to referential integrity failures in the orders-to-customers join dimension. Uniqueness violations are a separate concern, traced to an upstream deduplication gap in the inventory events producer.

## Key Highlights

- **Referential integrity failures**: 3 CRITICAL violations were triggered when the orders fact table referenced customer IDs that did not exist in the customers dimension. Root cause: a race condition where the orders stream processes faster than the customers dimension refresh. Mitigation: introduced a 5-minute hold on orders records for customer IDs not yet seen in dimension.
- **Uniqueness violation root cause identified**: The inventory events Kafka producer is not using idempotent produce, resulting in occasional duplicate event IDs. Producer configuration fix deployed; monitoring for recurrence.
- **Rule coverage expansion**: 14 new quality rules added this period, bringing total active rules to 412. New rules cover statistical range checks on pricing fields (previously uncovered).

## Active Initiatives

1. **Orders-customers join latency fix**: Implementing a lookup join with a 5-minute tolerance window to eliminate referential integrity false positives.
2. **Producer idempotency enforcement**: Auditing all pipeline producers for idempotent produce configuration; 6 of 15 producers confirmed compliant.
3. **Quality rule documentation**: Documenting rule rationale and acceptable violation thresholds for all CRITICAL rules.

## Incidents

No quality-related incidents escalated to SEV-1 or SEV-2 this period.

## Risks

- **Critical**: Referential integrity rules continue to generate violations until the orders-customers join fix is deployed (target: 2 weeks).
- **Medium**: 9 of 15 producers not yet confirmed as using idempotent produce; uniqueness violation recurrence possible.

## Next Month Focus

- Deploy orders-customers join latency fix and verify CRITICAL violation count drops to zero
- Complete producer idempotency audit across all 15 producers
- Publish updated quality rule documentation for all CRITICAL rules
