---
id: RUNBOOK-066
type: runbook
title: Usage Metering Discrepancy Runbook
status: draft
owner: On-Call Engineer
created: '2025-06-05T22:51:50.101Z'
updated: '2025-09-28T19:53:03.622Z'
tags:
  - runbook
  - billing-engine
summary: Usage Metering Discrepancy Runbook
example: true
---

## Service

- **System**: [[SYSTEM-050|Billing Engine]]
- **Owner team**: Billing Platform Engineering
- **On-call rotation**: PagerDuty schedule "billing-oncall"
- **Slack channel**: #billing-incidents
- **Runtime**: Kubernetes / Java 21 / PostgreSQL 15 / Kafka

## Alerts

- `billing_usage_aggregate_discrepancy_detected` - Automated reconciliation found a discrepancy between raw event count and aggregate total exceeding 0.1%
- `billing_metering_event_ingestion_lag_high` - Usage event ingestion lag exceeds 15 minutes for any producer
- `billing_dead_letter_queue_depth_high` - Metering event dead-letter queue depth exceeds 20 messages
- `billing_usage_aggregate_job_failed` - The usage aggregation job for one or more accounts failed during billing cycle preparation

## Diagnosis Steps

1. **Check the discrepancy alert details** - The `billing_usage_aggregate_discrepancy_detected` alert includes the account ID and the period with the discrepancy. Open the Billing Engine admin console and navigate to the Usage Metering section for that account and period.
2. **Compare raw events to aggregates** - Use the usage event query tool to count raw events for the account and period: `SELECT count(*), SUM(quantity) FROM usage_events WHERE account_id = ? AND occurred_at BETWEEN ? AND ?`. Compare to the aggregate stored in the billing_aggregates table.
3. **Check the dead-letter queue** - Navigate to the metering event dead-letter queue in the admin console. Review failed events for the affected account. Common failure reasons: schema validation errors, duplicate event_id conflicts, or malformed quantity fields.
4. **Check event ingestion lag** - On the Kafka Consumers dashboard, find the `billing-metering-consumer` group and check the lag for each partition. High lag means events were emitted but not yet processed; they will be included in the aggregate when lag clears.
5. **Check for duplicate events** - Query for duplicate event IDs: `SELECT event_id, count(*) FROM usage_events WHERE account_id = ? GROUP BY event_id HAVING count(*) > 1;`. Duplicates that passed deduplication indicate a bug in the deduplication logic.

## Remediation Steps

1. **If dead-letter queue has failed events**: Review each failed event, fix the data quality issue, and reprocess the event via the admin console **Reprocess Event** function. Monitor that reprocessed events are picked up by the consumer.
2. **If event ingestion lag is causing the discrepancy**: Wait for the Kafka consumer lag to clear (check the dashboard). The aggregate job should be re-run after lag clears. If lag is not clearing, scale up the metering consumer replicas.
3. **If duplicates are present**: Remove duplicate events using the deduplication cleanup script (requires `billing-dba` role). File a bug ticket for the deduplication logic before the next billing cycle.
4. **If the discrepancy affects an already-finalized invoice**: Follow the Handle Billing Discrepancy SOP to investigate and, if warranted, issue a corrective credit or regenerate the invoice.
5. **If the aggregate job itself failed**: Check the job logs for the failure reason. Re-trigger the aggregate job for the affected account via the admin console **Usage > Re-aggregate** function.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks alert details and identifies affected accounts |
| 15 min | Post assessment in #billing-incidents: discrepancy magnitude, affected accounts, suspected cause |
| 30 min | If discrepancy affects a currently running billing cycle: page Billing Platform tech lead |
| 45 min | If discrepancy affects more than 10 accounts: page Engineering Manager |
| 60 min | If root cause is not identified: escalate to billing data team for deep investigation |

## Dashboards

- [Billing Metering Overview](https://grafana.example.com/d/billing-metering) - Event ingestion rate, lag, dead-letter queue depth
- [Billing Kafka Consumers](https://grafana.example.com/d/billing-kafka) - Consumer group lag per partition
- [Billing Usage Aggregation](https://grafana.example.com/d/billing-aggregation) - Aggregate job success/failure rate, reconciliation metrics
- [Billing Engine Logs](https://kibana.example.com/app/discover#/billing) - Metering error logs with event IDs
