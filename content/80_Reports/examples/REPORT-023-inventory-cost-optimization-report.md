---
id: REPORT-023
type: report
title: Inventory Cost Optimization Report
status: approved
owner: Inventory Tech Lead
created: '2024-05-01T03:38:08.796Z'
updated: '2026-04-24T19:13:51.540Z'
tags:
  - report
  - inventory-management
summary: Inventory Cost Optimization Report
company: InventoryManagement
report_month: 2024-05
report_type: portfolio
overall_health: fair
confidence: low
active_initiatives_count: 5
critical_risks_count: 2
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Platform infra spend | Budget | 12% over budget | Below target |
| DynamoDB monthly cost | $4,200 | $5,800 | Over budget |
| ScyllaDB storage cost | $2,100 | $2,380 | Slightly over |
| Lambda invocation cost | $800 | $720 | On target |
| PostgreSQL RDS cost | $3,600 | $3,420 | On target |
| Redis ElastiCache cost | $1,200 | $1,050 | Under budget |

Platform infrastructure spend is 12% over budget in May. The primary driver is DynamoDB, where on-demand pricing is costing significantly more than provisioned capacity would at current usage patterns. ScyllaDB storage growth from the expanded event retention window is a secondary factor.

## Key Highlights

- **DynamoDB cost spike identified**: On-demand mode is consuming 38% more than the equivalent provisioned capacity for the idempotency store's current read/write pattern. Migration to provisioned capacity with auto-scaling is the recommended action.
- **Event retention window cost impact**: Extending event retention from 30 to 90 days (implemented in Q1) added $280/month in ScyllaDB storage. Retention tiering (hot 30 days, cold archive) could reduce this to $80/month.
- **Lambda cost stable**: Warehouse sync Lambda invocations are within budget despite the connection count increase. Per-invocation cost is well-optimized.

## Active Initiatives

1. **DynamoDB provisioned capacity migration**: Modelling optimal provisioned capacity with auto-scaling; estimated savings $1,600/month.
2. **ScyllaDB event retention tiering**: Implementing hot/cold tiering with S3 Glacier for events older than 30 days; estimated savings $200/month.
3. **Redis right-sizing**: Current ElastiCache nodes are slightly under-utilized; evaluating downgrade to smaller instance type for $150/month savings.
4. **Idle resource audit**: Scanning for unused Lambda functions, orphaned DynamoDB tables, and stale log groups from deprecated services.
5. **Cost attribution tagging**: Implementing resource tagging policy to attribute costs to individual services and teams for accountability.

## Incidents

No service incidents this period.

## Risks

- **Critical**: DynamoDB on-demand costs will continue to escalate as event volume grows without migration to provisioned capacity. On current trajectory, costs will exceed $8,000/month by Q3.
- **Critical**: Cost attribution tagging is incomplete. 40% of infrastructure costs cannot currently be attributed to a specific service, preventing targeted optimization.

## Next Month Focus

- Complete DynamoDB provisioned capacity migration and realize savings
- Deploy ScyllaDB retention tiering to S3 Glacier
- Complete cost attribution tagging for all inventory platform resources
- Publish idle resource audit findings and begin cleanup
