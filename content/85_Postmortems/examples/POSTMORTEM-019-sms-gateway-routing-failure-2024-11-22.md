---
id: POSTMORTEM-019
type: postmortem
title: SMS Gateway Routing Failure 2024-11-22
status: approved
owner: Incident Commander
created: '2025-09-10T00:40:54.609Z'
updated: '2026-09-30T23:22:33.415Z'
tags:
  - postmortem
  - notification-service
summary: SMS Gateway Routing Failure 2024-11-22
incident_number: INC-360
severity: SEV-2
incident_date: '2025-06-26'
detection_time: '2025-04-30T15:52:55.506Z'
resolution_time: '2024-04-02T13:46:43.589Z'
total_duration: ~4 hours
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-037
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On November 22, 2024, the SMS Dispatch Service experienced a 4-hour routing failure in which all SMS messages were incorrectly routed to the Vonage provider instead of the Twilio primary. A configuration deployment that afternoon had swapped the `PRIMARY_SMS_PROVIDER` and `FALLBACK_SMS_PROVIDER` environment variable values. Vonage's throughput capacity is lower than Twilio's, and under normal send volume the service quickly hit Vonage's rate limits, causing SMS queuing and eventual delivery delays.

Approximately 18,400 SMS messages were delayed by 30 minutes to 4 hours. All queued messages were eventually delivered after the configuration was corrected and the service restarted.

## Timeline

- **13:45** - Configuration deployment updates SMS provider environment variables (values accidentally swapped)
- **13:46** - SMS Dispatch Service restarts and picks up new configuration; begins routing all SMS to Vonage
- **13:52** - Vonage rate limit exceeded for the first time as normal send volume exceeds Vonage's capacity
- **13:55** - SMS queue depth begins rising on Kafka
- **14:10** - `sms_queue_depth_high` alert fires. On-call acknowledges
- **14:15** - On-call notes higher-than-usual error rate from SMS provider logs; identifies Vonage as active provider (expects Twilio)
- **14:22** - On-call identifies the configuration swap in the deployment diff
- **14:30** - Configuration corrected and SMS Dispatch Service restarted
- **14:32** - SMS routing restored to Twilio; queue drain begins
- **17:45** - All 18,400 queued SMS messages delivered; incident formally closed

## Impact

- **Duration**: 4 hours 3 minutes (13:45 - 17:45 UTC) for full queue drain
- **SMS affected**: ~18,400 messages delayed
- **Maximum delivery delay**: 4 hours 3 minutes
- **Users impacted**: ~18,400 users expecting time-sensitive SMS (OTPs, alerts)
- **SLA impact**: SMS delivery latency SLA breached for affected messages; platform remained available

## Root Cause Analysis

1. **Copy-paste error in configuration deployment**: The engineer updating the provider configuration accidentally transposed the `PRIMARY_SMS_PROVIDER` and `FALLBACK_SMS_PROVIDER` values when editing the ConfigMap. The error was not caught in code review because the reviewer was not familiar with the expected correct values.

2. **No configuration smoke test**: The SMS Dispatch Service lacked a startup health check that verified the configured primary provider could accept messages before beginning job processing. A smoke test would have immediately flagged the Vonage rate limit issue.

## Resolution

1. Identified the transposed configuration values by reviewing the deployment diff
2. Corrected the ConfigMap to restore `twilio` as `PRIMARY_SMS_PROVIDER`
3. Restarted the SMS Dispatch Service to pick up the corrected configuration
4. Monitored the Kafka queue drain until all delayed messages were delivered

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add startup provider health check to SMS Dispatch Service | Notification Engineering | P1 | 2024-11-29 | Completed |
| Add configuration validation: primary and fallback providers must differ | Notification Engineering | P1 | 2024-11-29 | Completed |
| Update ConfigMap review checklist to include provider configuration verification | On-Call | P2 | 2024-12-06 | Completed |
| Add `sms_provider_mismatch` alert (actual provider != configured primary for > 5 min) | SRE | P2 | 2024-12-06 | In progress |

## Lessons Learned

- **What went well**: On-call identified the wrong provider in logs within 5 minutes of acknowledging the alert. Root cause was identified within 17 minutes.
- **What went poorly**: A trivial configuration swap caused a 4-hour impact. There was no guardrail to catch the error at deploy time or startup.
- **What was lucky**: Kafka's durable queue ensured no SMS messages were permanently dropped. All 18,400 delayed messages were eventually delivered.
