---
id: SOP-078
type: sop
title: Handle Prometheus Cardinality Explosion SOP
status: approved
owner: DevOps Lead
created: '2025-06-06T19:21:57.964Z'
updated: '2025-02-19T23:25:46.084Z'
tags:
  - sop
  - monitoring-stack
summary: Handle Prometheus Cardinality Explosion SOP
related_process: PROCESS-068
related_systems:
  - SYSTEM-036
example: true
---

## Preconditions

- The `PrometheusHighCardinalityMetrics` alert has fired, OR Prometheus memory usage has spiked significantly (above 80% of limit) without a corresponding traffic increase
- You have identified the metric or service responsible for the cardinality explosion using `topk` queries
- A change ticket has been opened for the cardinality remediation if it requires a code or configuration change

## Materials/Access

- Prometheus UI access (admin-level for enabling/disabling targets)
- `kubectl` access to the monitoring namespace for checking Prometheus pod resource usage
- Access to the source code or configuration of the offending service
- AlertManager access to silence secondary alerts if memory pressure causes false positives during remediation

## Procedure

1. Open the Prometheus UI and navigate to `Status > TSDB Status`. Review `Top 10 metric names by number of series` and `Top 10 label names by number of values` to identify the high-cardinality metric.
2. Run the following query to quantify the cardinality: `topk(10, count by (__name__)({__name__!=""}))`. Note the offending metric names and their series count.
3. Identify the label causing the explosion. Run: `count by (the_suspect_label) ({metric_name="offending_metric"})`. High-cardinality labels are often dynamic values like user IDs, session tokens, or request IDs.
4. Check when the cardinality started increasing: use the Prometheus graph to plot `count({offending_metric_name})` over time. Correlate the onset with recent deployments.
5. Silence secondary memory-pressure alerts in AlertManager to reduce noise while you work. Set a 2-hour silence max.
6. Apply an immediate mitigation to reduce cardinality: either drop the high-cardinality label via a metric_relabel_config in the Prometheus scrape config, or temporarily drop the entire metric if the service cannot be fixed quickly.
7. Edit the Prometheus scrape config or service monitor to add the relabeling rule. Commit and push via GitOps. Verify with `promtool check config`.
8. After the config reloads, run a TSDB compaction to free memory: `curl -X POST http://prometheus:9090/api/v1/admin/tsdb/clean_tombstones`.
9. Monitor Prometheus memory usage and series count. The series count for the offending metric should decrease within 15 minutes as old blocks are compacted.
10. Open a follow-up ticket for the service team to permanently fix the high-cardinality label in the application code.

## Validation

- Prometheus memory usage has returned below 70% of limit
- The series count for the offending metric has decreased to an acceptable level (below 10,000 series)
- No Prometheus OOM or restart events have occurred since remediation
- A follow-up ticket is open for permanent code-level fix

## Rollback

1. If the metric relabeling rule was too aggressive and dropped important data, revert the scrape config change from the monitoring repository.
2. If Prometheus OOMs before remediation is complete, restart the pod: `kubectl rollout restart statefulset/prometheus -n monitoring`. Note that this will cause a scrape gap.
3. Escalate to the Platform Lead if memory pressure continues after relabeling and compaction.
