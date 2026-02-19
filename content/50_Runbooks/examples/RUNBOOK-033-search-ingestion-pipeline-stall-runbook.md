---
id: RUNBOOK-033
type: runbook
title: Search Ingestion Pipeline Stall Runbook
status: approved
owner: On-Call Engineer
created: '2025-06-18T09:28:45.710Z'
updated: '2026-05-03T12:04:16.315Z'
tags:
  - runbook
  - search-platform
summary: Search Ingestion Pipeline Stall Runbook
example: true
---

## Service

- **System**: [[SYSTEM-022|Search Ingestion Pipeline]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Kubernetes / Apache Kafka / Logstash / Elasticsearch 8

## Alerts

- `search_pipeline_consumer_lag_high` - Kafka consumer group lag for the search ingestion topic exceeds 50,000 messages for more than 10 minutes
- `search_pipeline_throughput_zero` - Ingestion pipeline has indexed zero documents in 5 consecutive minutes during expected high-traffic hours
- `search_pipeline_dlq_growth` - Dead letter queue (DLQ) document count is growing at more than 100 messages per minute

## Diagnosis Steps

1. **Check pipeline consumer lag** - Use the Kafka consumer group CLI or the Grafana Kafka dashboard to check the lag for the search ingestion consumer group. A growing lag indicates the pipeline is falling behind the producer rate.
2. **Check pipeline worker health** - Inspect Logstash or pipeline worker pod status: `kubectl get pods -n search -l role=ingestion`. Look for pods in `CrashLoopBackOff`, `Pending`, or `OOMKilled` state.
3. **Check pipeline error logs** - Review ingestion worker logs for repeated errors: `kubectl logs -n search <ingestion-pod> --since=30m`. Common errors: Elasticsearch bulk API rejections (429), connection timeouts, or document mapping exceptions.
4. **Check Elasticsearch bulk indexing capacity** - Run `GET /_cat/thread_pool/write?v` to see if the Elasticsearch bulk write thread pool is fully queued or rejecting requests. Rejections indicate the cluster cannot absorb the indexing rate.
5. **Check the DLQ** - If the DLQ is growing, examine the DLQ contents to understand what types of documents are failing. Mapping errors and schema violations are common DLQ failure causes.

## Remediation Steps

1. **If pipeline workers are crashing (OOMKilled)**: Increase the memory limit on the ingestion worker deployment: `kubectl edit deployment search-ingestion -n search` and raise the memory limit. Then restart the pods.
2. **If Elasticsearch is rejecting bulk requests (429)**: Reduce the ingestion batch size and increase the batch interval in the pipeline configuration. Also check if a reindex job is running concurrently and consuming write capacity.
3. **If the pipeline has completely stalled with zero throughput**: Restart the ingestion worker pods: `kubectl rollout restart deployment/search-ingestion -n search`. Monitor that lag begins decreasing after restart.
4. **If the DLQ is growing with mapping errors**: Examine the malformed documents and either fix the upstream data source or update the pipeline's document normalization logic to handle the edge case. Do not silently discard DLQ messages without understanding the root cause.
5. **If consumer lag is very large (> 500K messages)**: Temporarily scale up the ingestion worker replicas to increase throughput and catch up: `kubectl scale deployment search-ingestion -n search --replicas=5`.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer checks pipeline worker health and consumer lag |
| 15 min | Post status in #search-incidents with lag numbers and worker state |
| 30 min | If lag is still growing: page Search Platform tech lead |
| 60 min | If lag exceeds 24 hours of data: page Engineering Manager; assess freshness SLO breach |

## Dashboards

- [Search Ingestion Pipeline](https://grafana.example.com/d/search-ingestion) - Consumer lag, throughput, DLQ depth, error rate
- [Search Cluster Write Performance](https://grafana.example.com/d/search-write-perf) - Bulk indexing rate, bulk rejection rate
- [Kubernetes Search Namespace](https://grafana.example.com/d/k8s-search) - Ingestion pod health, restart counts, memory usage
