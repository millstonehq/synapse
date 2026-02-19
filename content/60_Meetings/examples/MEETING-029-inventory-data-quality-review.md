---
id: MEETING-029
type: meeting
title: Inventory Data Quality Review
status: review
owner: Engineering Manager
created: '2025-03-08T04:48:25.005Z'
updated: '2025-02-04T01:17:38.643Z'
tags:
  - meeting
  - inventory-management
summary: Inventory Data Quality Review
company: InventoryManagement
topic: Inventory Data Quality Review
meeting_date: '2025-05-21T23:23:35.686Z'
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

- **Project**: Inventory Data Quality Program
- **Topic**: Inventory Data Quality Review
- **Date/Time**: 2025-05-21 5:23 PM CT
- **Attendees (engineering)**: Principal Engineer, Tech Lead, Data Analyst, QA Lead
- **Attendees (product)**: Product Manager, Engineering Manager
- **Context**: Quarterly data quality review covering inventory record completeness, accuracy metrics from cycle counts, and progress on the data quality improvement initiatives launched in Q1.

## Observations by Domain

- **Record Completeness**: 2.3% of active SKU records are missing at least one required attribute (unit_cost, category, or supplier_id); these are legacy records from the pre-standard era that were never back-filled
- **Quantity Accuracy**: Post-cycle-count reconciliation shows 97.8% accuracy across all warehouses (target: 99.5%); three warehouses are consistently below target and account for 78% of all discrepancies
- **Stale Records**: 4,200 SKU records have not had a stock movement in 180+ days but remain in `active` status (dead stock candidates per the Dead Stock Disposal Policy)
- **Duplicate Detection**: The duplicate detection job identified 34 likely duplicate SKUs introduced via bulk imports in Q1 where the naming convention was not enforced at ingestion
- **Data Quality Monitoring**: New data quality dashboard launched in April is being used by 6 of 8 warehouse teams; the two non-adopting teams are the ones with below-target accuracy

## Key Metrics & Data Points

- **SKU records missing required attributes**: 2.3% of active SKUs (~48,000 records)
- **Inventory quantity accuracy (cycle count)**: 97.8% (target: 99.5%)
- **Warehouses below accuracy target**: 3 of 11 (account for 78% of discrepancies)
- **Dead stock candidate SKUs**: 4,200
- **Duplicate SKUs detected from Q1 imports**: 34
- **Data quality dashboard adoption**: 6 of 8 warehouse teams

## Preliminary Scorecard Hooks

- Record Completeness: 3/5 - 2.3% missing attributes is manageable but back-fill is overdue
- Quantity Accuracy: 3/5 - 97.8% is below target; concentrated in 3 warehouses
- Dead Stock Management: 3/5 - 4,200 candidates identified; disposal workflow needs to start
- Duplicate Prevention: 3/5 - 34 duplicates is a low count but indicates ingestion validation gaps
- Monitoring Adoption: 4/5 - 6/8 teams adopting; targeted outreach needed for the two laggards

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Quantity accuracy at 3 warehouses continues dragging overall metric below target | High | High | Data Analyst | Deep-dive accuracy investigation at the 3 below-target warehouses; identify systematic causes | 2025-06-15 |
| 48,000 legacy SKUs missing required attributes affect downstream data quality | Medium | Certain | Platform Engineer | Run back-fill script for missing attributes using supplier catalog data; validate before applying | 2025-07-01 |
| 4,200 dead stock SKUs tying up system resources and warehouse space | Medium | Certain | Product Manager | Initiate Dead Stock Disposal Policy workflow for all 4,200 candidates | 2025-06-01 |
| Bulk import naming convention violations producing duplicates | Medium | High | Tech Lead | Add naming convention validation to bulk import API; reject non-compliant SKU IDs at ingestion | 2025-06-15 |

## Decisions & Next Steps

### Decisions

- Deep-dive accuracy investigation at the 3 below-target warehouses is the highest priority data quality action for Q2
- Back-fill of 48,000 legacy SKU attributes will be scoped as a batch job; Platform Engineer to build and test before July
- Naming convention validation will be enforced at the bulk import API layer, not just documented as a guideline

### Action Items

- Schedule accuracy investigation visits to the 3 below-target warehouses (Data Analyst - 2025-05-28)
- Design back-fill script for missing SKU attributes (Platform Engineer - 2025-06-07)
- Add naming convention validation to bulk import API (Tech Lead - 2025-06-15)
- Initiate dead stock disposal review for 4,200 candidates (Product Manager - 2025-06-01)

### Follow-ups

- Accuracy metric check at next quarterly review
- Dashboard adoption outreach to the two non-adopting warehouse teams
- Back-fill script dry run review before production execution
