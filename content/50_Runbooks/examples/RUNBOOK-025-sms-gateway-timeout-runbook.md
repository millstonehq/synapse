---
id: RUNBOOK-025
type: runbook
title: SMS Gateway Timeout Runbook
status: review
owner: On-Call Engineer
created: '2024-07-01T19:01:42.984Z'
updated: '2025-01-02T12:30:51.083Z'
tags:
  - runbook
  - notification-service
summary: SMS Gateway Timeout Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Service]]
- **Owner team**: Notification Service Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / Twilio / Vonage

## Alerts

- `sms_gateway_timeout_rate_high` - SMS gateway timeout rate exceeds 5% for 3 consecutive minutes
- `sms_delivery_rate_low` - SMS delivery success rate below 80% for 5 minutes
- `sms_p95_latency_high` - P95 SMS gateway API response time exceeds 10 seconds
- `sms_worker_error_rate` - SMS worker error rate exceeds 10% for 2 minutes

## Diagnosis Steps

1. **Check Twilio status page** - Go to status.twilio.com to verify if there is an active incident affecting SMS delivery or API response times in the relevant region.
2. **Check SMS worker logs for timeout patterns** - In Kibana, filter by `service:notification-service channel:sms level:error` for the past 15 minutes. Identify whether timeouts are on connection establishment or response receipt.
3. **Check gateway response time trend** - On the SMS latency dashboard, check the trend over the past hour. A gradual increase suggests load or provider degradation; a sudden spike suggests a network or configuration event.
4. **Check Notification Service network connectivity** - Verify outbound connectivity from the notification worker pods to the Twilio API endpoint: `kubectl exec -n notifications <pod> -- curl -I https://api.twilio.com` to rule out cluster-level network issues.
5. **Check for recent configuration changes** - Review the `#notifications-releases` channel for any recent SMS-related configuration changes (gateway credentials, timeout settings, retry policies) that coincide with the onset of timeouts.

## Remediation Steps

1. **If Twilio is having an active incident**: Initiate the Handle SMS Provider Outage SOP (SOP-039) to fail over to the secondary SMS provider (Vonage).
2. **If timeouts are network-related (cluster connectivity)**: Page the infrastructure on-call to investigate outbound network policy or DNS resolution issues affecting the notification worker namespace.
3. **If a configuration change increased timeout sensitivity**: Revert the configuration change and verify timeout rate returns to normal.
4. **If the issue is intermittent and below SLA breach threshold**: Increase the SMS gateway client timeout configuration, document the change, and monitor.
5. **If cause is unknown after 15 minutes of diagnosis**: Escalate to Platform Lead and consider initiating failover as a precaution.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #notifications-incidents |
| 15 min | If not resolved: assess whether to initiate SMS provider failover |
| 30 min | Page Notification Service Platform Lead if SMS delivery SLA is breached |
| 60 min | Page Engineering Manager if critical SMS (MFA codes, security alerts) is affected |

## Dashboards

- [SMS Delivery Overview](https://grafana.example.com/d/sms-delivery) - Delivery rate, timeout rate, error distribution
- [SMS Gateway Latency](https://grafana.example.com/d/sms-latency) - P50/P95/P99 gateway response times
- [SMS Worker Health](https://grafana.example.com/d/sms-workers) - Pod health, error rate, queue depth
- [Notification Service Logs](https://kibana.example.com/app/discover#/notifications) - SMS error logs with gateway responses
