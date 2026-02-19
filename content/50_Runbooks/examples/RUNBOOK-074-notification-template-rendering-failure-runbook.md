---
id: RUNBOOK-074
type: runbook
title: Notification Template Rendering Failure Runbook
status: review
owner: On-Call Engineer
created: '2025-08-01T18:50:27.432Z'
updated: '2025-07-12T14:33:11.096Z'
tags:
  - runbook
  - notification-service
summary: Notification Template Rendering Failure Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Routing Engine]]
- **Owner team**: Notification Platform Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / PostgreSQL 15 / Redis 7 (LRU template cache)

## Alerts

- `notification_template_render_error_rate_high` - Template rendering error rate exceeds 1% over 5 minutes; indicates missing variables or corrupted template AST
- `notification_dlq_depth_high` - Dead-letter queue depth exceeds 50 messages; rendering failures are accumulating faster than they are being investigated
- `notification_template_cache_miss_rate_high` - LRU cache miss rate above 30% for 10 minutes; may indicate cache eviction pressure or a Redis connectivity issue
- `notification_render_p99_latency_high` - P99 rendering latency above 2 seconds for 5 minutes; indicates PostgreSQL template fetch slowdown on cache miss

## Diagnosis Steps

1. **Check the dead-letter queue** - In the RabbitMQ management console, inspect the `notifications.email.dlq` queue. Open a sample DLQ message and examine the `x-death` headers to identify the failure reason. Common reasons: `missing_variable` (template variable not in the variable map), `template_not_found` (invalid slug or version reference), `parse_error` (corrupted template AST in the database).
2. **Check recent template publishes** - In the template registry admin UI (or via `GET /v1/templates?since=<1h ago>`), look for templates published in the last hour. A new template version with a missing required variable definition is the most common cause of a `missing_variable` spike.
3. **Check the template cache hit rate** - In Grafana, open the Notification Template Renderer dashboard and inspect the Redis cache hit rate panel. A sudden drop to near zero indicates Redis is unreachable or the cache was flushed. Check Redis health: `redis-cli -h notification-cache ping`. If Redis is unreachable, the renderer will fall back to PostgreSQL for every job, causing latency spikes.
4. **Check PostgreSQL for corrupted AST records** - If `parse_error` appears in DLQ messages, query: `SELECT id, slug, version, updated_at FROM notification_templates WHERE status = 'published' ORDER BY updated_at DESC LIMIT 10;` and verify the `compiled_ast` column is not null for the affected template.
5. **Check for a missing variable in a producer's request** - If `missing_variable` errors are scoped to a single notification type, query recent notification jobs for that type in the delivery log and verify whether the variable map is consistently missing a field. This usually indicates a producer-side bug in a recently deployed service.

## Remediation Steps

1. **If caused by a newly published template with a missing required variable**: Roll back the template to the previous version using `POST /v1/templates/{slug}/rollback` with the last known good `version`. Notify the template author in #notifications-incidents. The DLQ messages for the affected jobs will need to be replayed after the rollback — use the DLQ replay script (`scripts/replay-dlq.sh notifications.email.dlq`).
2. **If caused by Redis cache unavailability**: The renderer degrades gracefully by fetching from PostgreSQL on cache miss. The primary concern is latency, not correctness. Page the infrastructure on-call to restore Redis. Do not restart renderer pods unless PostgreSQL is also showing connection saturation — a restart would worsen the cache cold-start period.
3. **If caused by a producer sending an incomplete variable map**: Contact the owning team for the affected producer and ask them to redeploy with the correct variable map. DLQ messages for jobs with missing variables cannot be safely replayed without the missing variable values — they must be re-submitted by the producer with corrected payloads.
4. **If caused by a corrupted template AST in PostgreSQL**: Re-publish the affected template via the template registry UI. If re-publish fails, restore from the latest PostgreSQL backup for the `notification_templates` table. Coordinate with the DBA on-call.
5. **If DLQ depth is growing faster than investigation can proceed**: Pause the email consumer by setting replicas to zero (`kubectl scale deployment/email-delivery-service -n notifications --replicas=0`) to stop new jobs from failing. This stops email delivery but prevents unbounded DLQ growth. Escalate immediately.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 5 min | Post initial assessment in #notifications-incidents with DLQ depth and failure reason |
| 15 min | If not resolved: page the Notification Platform tech lead via PagerDuty |
| 30 min | If not resolved: page the Engineering Manager; assess customer impact and draft status page update |
| 60 min | If email delivery is fully stopped: initiate major incident process, assemble war room in #incident-war-room |

## Dashboards

- [Notification Template Renderer](https://grafana.example.com/d/notif-template-renderer) - Render error rate, cache hit rate, P99 latency, DLQ depth
- [Notification Dead-Letter Queue](https://grafana.example.com/d/notif-dlq) - DLQ depth by queue, failure reason breakdown, oldest message age
- [Notification Redis Cache](https://grafana.example.com/d/notif-redis) - Hit rate, memory usage, eviction rate, connection count
- [Email Delivery Service](https://grafana.example.com/d/email-delivery) - Jobs enqueued, jobs delivered, jobs failed, P95 end-to-end latency
- [Notification Logs](https://kibana.example.com/app/discover#/notifications) - Error logs with template slug, version, and missing variable name
