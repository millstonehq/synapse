---
id: RUNBOOK-023
type: runbook
title: Email Delivery Rate Drop Runbook
status: accepted
owner: On-Call Engineer
created: '2024-03-14T13:51:58.389Z'
updated: '2026-05-09T07:17:31.897Z'
tags:
  - runbook
  - notification-service
summary: Email Delivery Rate Drop Runbook
example: true
---

## Service

- **System**: [[SYSTEM-016|Notification Service]]
- **Owner team**: Notification Service Engineering
- **On-call rotation**: PagerDuty schedule "notifications-oncall"
- **Slack channel**: #notifications-incidents
- **Runtime**: Kubernetes / Node.js 20 / SendGrid / Amazon SES

## Alerts

- `email_delivery_rate_low` - Email delivery success rate drops below 90% for 5 minutes
- `email_bounce_rate_high` - Bounce rate exceeds 5% over a 10-minute window
- `email_provider_5xx_rate` - Provider API returning 5xx errors for more than 2 minutes
- `email_send_latency_high` - P95 provider API latency exceeds 5 seconds

## Diagnosis Steps

1. **Check provider status page** - Visit the SendGrid status page to determine if there is an active provider-side incident affecting delivery or API availability.
2. **Check Notification Service error logs** - In Kibana, filter by `service:notification-service channel:email level:error` for the past 30 minutes. Look for provider error codes (4xx auth errors, 5xx server errors, rate limit 429s).
3. **Check bounce type distribution** - In the SendGrid Activity Feed, review the bounce events. Separate hard bounces (permanent) from soft bounces (temporary). A spike in hard bounces indicates a data quality issue; soft bounces indicate provider or receiving server issues.
4. **Check sending IP reputation** - In the SendGrid IP Warmup and Reputation section, verify the sending IP is not on a blocklist or in a degraded reputation state.
5. **Check for authentication failures** - Look for DKIM, SPF, or DMARC failures in the email headers of bounced messages, which could indicate a recent DNS misconfiguration.

## Remediation Steps

1. **If provider is down**: Initiate the Email Provider Failover Process (PROCESS-020) to route traffic to Amazon SES.
2. **If bounce rate is elevated due to data quality**: Pause the affected notification type or campaign, add hard-bounced addresses to the suppression list, and create a ticket for the data source team.
3. **If API credentials are returning 401 errors**: Verify the SendGrid API key is valid in the secrets manager. If the key has been revoked or expired, follow the Rotate SendGrid API Keys SOP (SOP-035).
4. **If IP reputation is degraded or blacklisted**: Reduce sending volume immediately, contact SendGrid support, and begin the IP warmup recovery process.
5. **If DKIM/SPF failures are occurring**: Do not attempt to fix DNS under pressure. Page the Platform Lead and assess whether the DNS change should be rolled back per SOP-033.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post assessment in #notifications-incidents |
| 20 min | If not resolved: page Notification Service Platform Lead |
| 30 min | If affecting transactional email (receipts, security alerts): page Engineering Manager |
| 60 min | Major incident process if delivery is stopped for transactional flows |

## Dashboards

- [Email Delivery Overview](https://grafana.example.com/d/email-delivery) - Delivery rate, bounce rate, complaint rate
- [SendGrid Provider Metrics](https://grafana.example.com/d/sendgrid-metrics) - API latency, error rate, queue depth
- [Email Authentication](https://grafana.example.com/d/email-auth) - DKIM/SPF/DMARC pass rates
- [Notification Service Logs](https://kibana.example.com/app/discover#/notifications) - Error logs with provider response codes
