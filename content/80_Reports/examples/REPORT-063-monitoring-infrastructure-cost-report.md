---
id: REPORT-063
type: report
title: Monitoring Infrastructure Cost Report
status: approved
owner: Monitoring Tech Lead
created: '2024-10-19T07:46:48.866Z'
updated: '2025-09-05T17:24:47.330Z'
tags:
  - report
  - monitoring-stack
summary: Monitoring Infrastructure Cost Report
company: MonitoringStack
report_month: 2024-08
report_type: portfolio
overall_health: poor
confidence: high
active_initiatives_count: 6
critical_risks_count: 2
example: true
---

## Service Health

| Component | Monthly Cost | Budget | Status |
|-----------|-------------|--------|--------|
| ScyllaDB cluster (Metrics) | $4,200 | $3,500 | Over budget |
| SQL Server (Log pipeline) | $3,100 | $2,800 | Over budget |
| ClickHouse cluster (Tracing) | $2,600 | $2,500 | Slightly over |
| Kubernetes compute (all services) | $3,800 | $4,000 | On target |
| Network egress | $1,400 | $1,200 | Over budget |

Total monthly spend is $15,100 against a $14,000 budget — 7.9% over. Cost growth is driven primarily by metric and log data volume increases (both up ~30% year-over-year) without corresponding retention policy tightening.

## Key Highlights

- **ScyllaDB 20% over budget**: Metrics data volume grew 28% year-over-year, but ScyllaDB storage provisioning was not revised. Immediate action: reduce metric retention from 90 to 60 days for non-critical services (saves ~$800/month).
- **SQL Server log storage**: Log volume grew due to new services onboarding in Q2. Cold storage migration (in progress) will move 90-180 day data to Azure Blob Storage, expected to save $900/month.
- **Network egress**: Grafana is fetching raw metric data for dashboard panels rather than using pre-computed recording rules. Switching to recording rules for the 10 highest-traffic dashboards is estimated to cut egress by 30%.

## Active Initiatives

1. **Metric retention tiering**: Reducing retention for low-priority service metrics to 60 days. High-priority and SLO metrics retain 90 days. Estimated saving: $800/month.
2. **Log cold storage migration**: Moving 90-180 day logs to Azure Blob. Estimated saving: $900/month. Target: Q4.
3. **Recording rule optimization**: Replacing raw metric queries in top dashboards with pre-computed recording rules. Estimated network egress saving: $420/month.

## Incidents

No cost-related incidents this month. One alert fired for ScyllaDB disk utilization at 85% — mitigated by adding a 200GB volume before it impacted operations.

## Risks

- **High**: At current growth rate (28%/year), ScyllaDB will require a 7th node in 6 months, adding ~$700/month before retention tiering is implemented.
- **High**: SQL Server is at 72% storage utilization. Cold storage migration must complete before disk pressure causes a service incident.

## Next Month Focus

- Deploy metric retention tiering policy
- Advance log cold storage migration to production
- Implement recording rules for top 10 dashboard queries
- Review cost budgets for FY2025 with updated growth projections
