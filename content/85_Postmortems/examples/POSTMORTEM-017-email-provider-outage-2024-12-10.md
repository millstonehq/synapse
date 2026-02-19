---
id: POSTMORTEM-017
type: postmortem
title: Email Provider Outage 2024-12-10
status: accepted
owner: On-Call Engineer
created: '2025-01-29T04:59:52.087Z'
updated: '2025-12-10T02:13:35.407Z'
tags:
  - postmortem
  - notification-service
summary: Email Provider Outage 2024-12-10
incident_number: INC-358
severity: SEV-1
incident_date: '2024-04-17'
detection_time: '2025-10-28T10:14:39.846Z'
resolution_time: '2025-11-20T21:24:48.984Z'
total_duration: ~2 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-036
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On December 10, 2024, the primary email provider (SendGrid) experienced a complete API outage lasting approximately 2 hours and 10 minutes. During this window, all outbound email notifications failed at the provider submission layer. Approximately 94,000 email notifications were queued and could not be delivered until the provider recovered. The Notification Platform's email failover mechanism to Mailgun was not automated at the time; failover required manual intervention, which delayed switching by 38 minutes.

All queued notifications were successfully delivered after service was restored, with a maximum delay of 2 hours and 48 minutes from the original send time. The incident prompted the implementation of automated email provider failover that was shipped in February 2025.

## Timeline

- **14:02** - SendGrid API begins returning `503 Service Unavailable` errors for all submission requests
- **14:04** - Email Delivery Service circuit breaker trips after 5 consecutive errors
- **14:06** - `email_delivery_failure_rate_critical` alert fires. On-call acknowledges
- **14:09** - On-call checks SendGrid status page — confirms outage in progress across all regions
- **14:12** - On-call checks runbook for provider failover steps. Steps exist but require manual config change
- **14:15** - On-call pages Notification tech lead for provider failover assistance
- **14:28** - Tech lead and on-call begin manual failover procedure
- **14:40** - Mailgun credentials loaded and Email Delivery Service restarted with Mailgun as primary
- **14:42** - Queued emails begin processing via Mailgun. Delivery resuming
- **16:12** - SendGrid reports full recovery on status page
- **16:20** - Email Delivery Service switched back to SendGrid as primary
- **16:50** - All queued notifications delivered. Incident formally closed

## Impact

- **Duration**: 2 hours 10 minutes (SendGrid outage), 38 minutes until failover to Mailgun
- **Emails affected**: ~94,000 email notifications queued and delayed
- **Maximum delivery delay**: 2 hours 48 minutes
- **User impact**: Users did not receive time-sensitive notifications (order confirmations, account alerts) for up to 2 hours 48 minutes
- **SLA impact**: Monthly email availability dropped to 99.7% against a 99.9% target

## Root Cause Analysis

1. **Primary provider single point of failure**: The Email Delivery Service had only one active email provider at any time. No automatic failover to the secondary provider (Mailgun) was implemented. The fallback required manual reconfiguration and service restart.

2. **Runbook gap**: The failover runbook existed but required 5 manual steps and knowledge of the deployment configuration. Under incident pressure, the tech lead needed to be paged to assist, adding 14 minutes of diagnosis time before failover could begin.

## Resolution

1. Manually reconfigured the Email Delivery Service to use Mailgun as the primary provider
2. Restarted the service and verified email delivery resumed via Mailgun
3. Monitored queue drain until all 94,000 delayed emails were delivered
4. Switched back to SendGrid after its recovery was confirmed

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Implement automatic email provider failover (circuit breaker → Mailgun) | Notification Engineering | P1 | 2025-01-31 | Completed |
| Update email failover runbook with automated procedure | On-Call | P1 | 2025-01-31 | Completed |
| Add SendGrid status page to monitoring dashboard | SRE | P2 | 2025-01-20 | Completed |
| Conduct monthly email failover drill | Notification Engineering | P3 | Ongoing | In progress |

## Lessons Learned

- **What went well**: Circuit breaker fired correctly within 2 minutes. All queued notifications were preserved and delivered after recovery — no messages were lost.
- **What went poorly**: No automatic failover meant a 38-minute delay before Mailgun was activated. The runbook was too manual for an incident situation.
- **What was lucky**: RabbitMQ's durable queue ensured no notifications were dropped during the 2+ hour outage window.
