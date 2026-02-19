---
id: REPORT-088
type: report
title: Mean Time to Detect Analysis Report
status: approved
owner: Monitoring Tech Lead
created: '2024-02-06T14:47:21.974Z'
updated: '2026-12-01T17:13:18.397Z'
tags:
  - report
  - monitoring-stack
summary: Mean Time to Detect Analysis Report
company: MonitoringStack
report_month: 2025-10
report_type: analytics
overall_health: excellent
confidence: high
active_initiatives_count: 5
critical_risks_count: 1
example: true
---

## Service Health

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| MTTD (SEV-1) | < 3 min | 8.4 min | Off target |
| MTTD (SEV-2) | < 8 min | 11.2 min | Off target |
| Automated detection rate (SEV-1/2) | 95% | 78% | Off target |
| Alert false positive rate | < 5% | 12% | Off target |
| Alert evaluation availability | 99.9% | 99.96% | On target |
| Alert rule coverage (on-call services) | 100% | 100% | On target |

October data shows the monitoring platform remains healthy operationally but the core MTTD and automated detection metrics continue to trail targets established at the start of the year. No monitoring blackout incidents occurred in October.

## Key Highlights

- **MTTD regression root cause identified**: Analysis of the 34 SEV-1/2 incidents this quarter shows that 19 of them (56%) had detection delays caused by evaluation window sizes set to 10 minutes or longer on alert rules that were originally written for less critical services. These rules were never updated when the services were promoted to on-call. A rule audit is underway.
- **22% manual detection rate remains elevated**: The incidents not caught by automated alerting in October were primarily concentrated in three services: the distributed tracing ingestion endpoint, the status page webhook handler, and the log pipeline compaction job. These services have threshold alerts but are missing error-rate SLO alerts. Adding burn rate alerting to these three services is the highest-priority gap closure item.
- **False positive improvement**: False positive rate improved from 17% in Q2 to 12% in October following the inhibition rule changes deployed in August. The quarterly alert review process identified 14 alert rules for threshold adjustment. Progress is encouraging but the 5% target requires further tuning of the remaining noisy rules.
- **New MTTD baseline established for SLO-bearing services**: Services with defined SLOs and burn rate alerts have a measured MTTD of 4.1 minutes, versus 13.6 minutes for services without SLOs. This confirms that SLO-driven alerting is the primary lever for MTTD improvement. Expanding SLO coverage is directly tied to MTTD target achievement.

## Active Initiatives

1. **Alert rule evaluation window audit** (In progress): Systematically reviewing all 247 alert rules for evaluation window appropriateness. 142 of 247 reviewed. Target completion: November. Expected MTTD improvement: 2-3 minutes reduction for SEV-1 incidents where evaluation window was the delay factor.
2. **SLO and burn rate alert expansion** (In progress): Adding SLO definitions and burn rate alerts for the 35% of on-call services currently without them. Three services added in October; 18 remaining. Directly tied to MTTD improvement and automated detection rate targets.
3. **Anomaly detection POC** (Planning): PRD-038 product initiative for ML-based anomaly detection. POC environment provisioned. Initial evaluation of threshold-less detection for the metrics collection service underway. If the POC succeeds, anomaly detection will address the class of failures that threshold-based alerting cannot catch.
4. **Alert noise reduction — second pass** (In progress): Following the Q3 inhibition rule changes, a second pass targets the remaining high false-positive-rate rules. 9 of 14 identified rules have been adjusted. Projected to reach 8% false positive rate by end of November.
5. **MTTD tracking dashboard** (Complete): Grafana dashboard for MTTD tracking launched in October. Enables per-service, per-severity MTTD tracking against targets. Data is now available to service teams without requiring a manual query.

## Incidents

| Date | Severity | Duration | Description |
|------|----------|----------|-------------|
| Oct 3 | SEV-2 | 34 min | Log aggregation pipeline disk exhaustion — detected via node exporter alert 22 minutes after pipeline began dropping logs; 12-minute data gap |
| Oct 9 | SEV-3 | 11 min | Grafana dashboard rendering latency elevated due to ScyllaDB read replica lag; detected via P95 latency alert firing; no customer-visible impact |
| Oct 21 | SEV-2 | 28 min | AlertManager route misconfiguration during config update caused 14 minutes of alert silence on two services; detected via Watchdog alert gap |

The Oct 3 incident is the most significant for MTTD: the 22-minute detection time was caused entirely by the absence of a log pipeline-specific error rate alert. A threshold alert on disk usage caught it late. This has been added to the burn rate alerting expansion initiative.

## Risks

- **Critical**: The 78% automated detection rate means that approximately 1 in 5 SEV-1/2 incidents is still being reported by customers before it is caught by automated alerting. This is a reliability and customer experience risk. The three services identified above (tracing ingestion, status page webhooks, log pipeline compaction) account for the majority of these incidents and must have burn rate alerts added before Q4 ends.
- **Medium**: Alert rule evaluation window audit is on track but scope creep is possible. If the 247-rule audit reveals systemic issues requiring architectural changes to the AlertManager routing tree, timeline may slip to December.
- **Low**: The anomaly detection POC depends on the PRD-038 engineering resources being available. If the team is pulled onto other priorities, the POC may not complete before the end of Q4.

## Next Month Focus

- Complete alert rule evaluation window audit (remaining 105 rules) and deploy all threshold adjustments
- Add burn rate alerts to the three high-priority services missing them
- Complete false positive reduction pass — target 8% false positive rate by November 30
- Publish first monthly MTTD trending report using the new dashboard to establish historical baseline
- Complete anomaly detection POC and present findings to engineering leadership for investment decision
