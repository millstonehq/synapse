---
id: RUNBOOK-075
type: runbook
title: Search Suggest Index Stale Runbook
status: accepted
owner: On-Call Engineer
created: '2025-07-10T19:31:24.890Z'
updated: '2025-03-03T16:21:29.647Z'
tags:
  - runbook
  - search-platform
summary: Search Suggest Index Stale Runbook
example: true
---

## Service

- **System**: [[SYSTEM-023|Search Autocomplete Service]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Lambda (Node.js 20) / DynamoDB / Redis 7

## Alerts

- `search_suggest_stale_lag_high` - Suggestion index last-updated timestamp is more than 30 minutes behind the current time
- `search_suggest_zero_results_rate` - More than 40% of autocomplete requests return an empty suggestion list for prefixes longer than 3 characters
- `search_suggest_dynamodb_error_rate` - DynamoDB error rate on the `search-suggestions` table exceeds 5% for 5 minutes
- `search_suggest_redis_cache_miss_rate_high` - Redis CTR signal cache miss rate exceeds 80% for 10 minutes (indicates cache was flushed or Redis is down)

## Diagnosis Steps

1. **Confirm the staleness window** - Check the `search_suggest_stale_lag_high` alert details for the exact last-updated timestamp. Query DynamoDB: `aws dynamodb get-item --table-name search-suggestions-metadata --key '{"key":{"S":"last_updated"}}'` to retrieve the indexing pipeline's last write timestamp.
2. **Check the Indexing Pipeline status** - The suggestion index is populated by the Search Indexing Pipeline (Kubernetes). Check the `indexing-pipeline` namespace: `kubectl get pods -n indexing-pipeline`. Look for pods in `CrashLoopBackOff` or `Error` state. If the pipeline is down, this is the root cause.
3. **Check the Kafka consumer lag** - Open the Grafana indexing pipeline dashboard and check the `content.mutations` consumer group lag. A lag above 10,000 events indicates the pipeline is backlogged, not just stalled.
4. **Check for DynamoDB throttling** - In the AWS console, view the `search-suggestions` table CloudWatch metrics. Check `ConsumedWriteCapacityUnits` and `ThrottledRequests`. If throttled requests are non-zero, the indexing pipeline is being throttled on writes. This is distinct from a hot-key read event — write throttling appears as sustained elevated `ThrottledRequests` across all partitions.
5. **Check Redis availability** - The Autocomplete Lambda reads CTR scores from Redis. Verify Redis is responding: `redis-cli -h search-redis.internal ping`. If Redis is down, the Lambda falls back to DynamoDB-stored base CTR scores, which may cause degraded ranking but not empty results.
6. **Check for a recent deployment** - Review the #deployments Slack channel and the ArgoCD dashboard for any deployments to the indexing pipeline or Autocomplete Lambda in the last hour. A bad deployment to the indexing pipeline can halt suggestion writes.
7. **Verify the Lambda is serving** - Test the Autocomplete Service directly: `curl "https://search-platform-staging.example.com/v1/suggest?q=sea&limit=8"`. If the Lambda returns stale results (old suggestions visible), the index is stale but the Lambda is functioning. If it returns an empty list, verify whether DynamoDB is reachable from the Lambda (check VPC endpoint configuration in the Lambda console).

## Remediation Steps

1. **If the Indexing Pipeline pods are down**: Restart the deployment: `kubectl rollout restart deployment/indexing-pipeline -n indexing-pipeline`. Monitor pod startup and watch for errors: `kubectl logs -f deployment/indexing-pipeline -n indexing-pipeline`. If pods fail to start, check for a recent bad deployment and roll back via ArgoCD.
2. **If DynamoDB write throttling is causing staleness**: The indexing pipeline has exponential backoff built in — if writes are throttled, the pipeline slows but does not halt. Check if a burst of content mutations caused a spike in suggestion writes. If capacity is the bottleneck, temporarily increase the `search-suggestions` table write capacity: `aws dynamodb update-table --table-name search-suggestions --billing-mode PROVISIONED --provisioned-throughput ReadCapacityUnits=5000,WriteCapacityUnits=2000`. Revert to on-demand billing once the burst passes.
3. **If Kafka consumer lag is high (> 10,000)**: The pipeline is behind but running. Do not restart it — restart will increase lag further during pod startup. Monitor the lag reduction rate in Grafana. If lag is not decreasing after 10 minutes, check for a document that is repeatedly failing transformation: `kubectl logs -f deployment/indexing-pipeline -n indexing-pipeline | grep ERROR`.
4. **If Redis is down**: The Autocomplete Lambda degrades gracefully to DynamoDB-stored CTR scores. Suggestion ranking quality will be degraded but results will still be served. Escalate to the infrastructure on-call to restore Redis. Do not attempt to restart the Redis cluster yourself.
5. **If the issue is a bad deployment**: Roll back the indexing pipeline via ArgoCD. Select the previous healthy deployment revision. Confirm the pipeline restarts successfully and suggestion writes resume (watch DynamoDB `ConsumedWriteCapacityUnits` to confirm writes are flowing).
6. **Trigger a manual suggestion index rebuild** (only if staleness is > 2 hours and root cause is resolved): Run the bulk reindex job: `kubectl create job --from=cronjob/suggestion-rebuild suggestion-rebuild-manual -n indexing-pipeline`. This re-scans all documents in Elasticsearch and rebuilds the `search-suggestions` DynamoDB table. Completion time is approximately 45 minutes for a full corpus of 500,000 documents.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Post initial assessment in #search-incidents |
| 15 min | If not resolved: page the Search Platform tech lead via PagerDuty schedule "search-leads" |
| 30 min | If not resolved: page the Engineering Manager; assess user-facing impact |
| 60 min | If not resolved and suggestions are returning empty results for > 30% of users: initiate SEV-2 incident process |

**Who to escalate to:**
- Search Platform tech lead: PagerDuty schedule "search-leads"
- Infrastructure issues (DynamoDB, Redis, VPC): PagerDuty schedule "infra-oncall"
- Kafka issues: PagerDuty schedule "data-platform-oncall"
- AWS service issues (DynamoDB, Lambda): open AWS Support ticket if AWS service health dashboard shows an active event

## Dashboards

- [Search Autocomplete Overview](https://grafana.example.com/d/search-autocomplete) - Suggestion request volume, empty result rate, DynamoDB latency
- [Search Indexing Pipeline](https://grafana.example.com/d/search-indexing) - Kafka consumer lag, pipeline throughput, DynamoDB write rate
- [Search Redis Cache](https://grafana.example.com/d/search-redis) - Hit rate, memory usage, evictions
- [Search Autocomplete Logs](https://kibana.example.com/app/discover#/search-autocomplete) - Lambda error logs with full stack traces
- [DynamoDB search-suggestions Metrics](https://console.aws.amazon.com/dynamodb/home#/tables/search-suggestions) - Consumed capacity, throttled requests
