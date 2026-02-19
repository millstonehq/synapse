---
id: RUNBOOK-024
type: runbook
title: Push Notification Service Degradation Runbook
status: draft
owner: On-Call Engineer
created: '2024-02-28T07:21:46.298Z'
updated: '2025-06-23T15:38:44.780Z'
tags:
  - runbook
  - notification-service
summary: Push Notification Service Degradation Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Service]]
- **Owner team**: Notification Service Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / FCM / APNs

## Alerts

- `push_delivery_rate_low` - Push delivery success rate below 85% for 5 minutes
- `push_provider_error_rate_high` - FCM or APNs error rate exceeds 5% for 3 minutes
- `push_worker_pod_crashloop` - Push worker pod restarting more than 3 times in 10 minutes
- `push_token_invalid_rate_high` - InvalidRegistration error rate exceeds 10% of dispatches

## Diagnosis Steps

1. **Check whether degradation is iOS (APNs) or Android (FCM)** - Review error logs filtered by `channel:push platform:ios` and `channel:push platform:android` separately to isolate the affected platform.
2. **Check FCM/APNs error codes** - In Kibana, look for the specific provider error codes: `InvalidRegistration`, `NotRegistered` (stale tokens), `QuotaExceeded` (rate limit), `InternalServerError` (provider-side).
3. **Check push worker pod health** - Run `kubectl get pods -n notifications -l component=push-worker` and check for crashloops, OOM kills, or pending pods indicating resource pressure.
4. **Check device token validity rate** - If `InvalidRegistration` errors are spiking, the device token table may contain a large number of stale tokens from app uninstalls. This requires token cleanup rather than infrastructure fixes.
5. **Check for a recent push payload schema change** - Review recent deployments in the #notifications-releases channel. A schema change that breaks APNs or FCM payload structure causes rejections at the provider level.

## Remediation Steps

1. **If push worker pods are crashlooping**: Check pod logs for the crash reason — `kubectl logs -n notifications -l component=push-worker --previous`. Restart pods if OOM: `kubectl rollout restart deployment/push-worker -n notifications`.
2. **If FCM/APNs is returning 5xx errors**: Check the Firebase Status Dashboard and Apple Developer System Status. If provider-side, monitor and wait; consider queuing messages for retry rather than dropping them.
3. **If token invalid rate is spiking**: Schedule an async token cleanup job to remove `NotRegistered` tokens from the device_tokens table. This reduces noise but does not resolve active delivery.
4. **If a payload schema regression is suspected**: Roll back the recent push-related deployment and verify delivery rate recovers.
5. **If cause is unknown after 15 minutes**: Escalate to Platform Lead.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #notifications-incidents |
| 20 min | If not resolved: page Notification Service Platform Lead |
| 45 min | If affecting critical push alerts: page Engineering Manager |
| 60 min | Major incident if all push delivery is stopped |

## Dashboards

- [Push Delivery Overview](https://grafana.example.com/d/push-delivery) - Delivery rate by platform, error rate, token validity
- [Push Worker Health](https://grafana.example.com/d/push-workers) - Pod health, CPU, memory, processing rate
- [FCM/APNs Error Codes](https://grafana.example.com/d/push-provider-errors) - Provider error distribution over time
- [Notification Service Logs](https://kibana.example.com/app/discover#/notifications) - Push error logs with provider responses
