---
id: POSTMORTEM-005
type: postmortem
title: Payment Gateway Timeout Cascade 2025-03-01
status: approved
owner: On-Call Engineer
created: '2024-07-10T04:43:08.641Z'
updated: '2026-10-12T14:14:41.416Z'
tags:
  - postmortem
  - payment-processing
summary: Payment Gateway Timeout Cascade 2025-03-01
incident_number: INC-76
severity: SEV-2
incident_date: '2024-04-22'
detection_time: '2026-08-12T18:28:32.575Z'
resolution_time: '2026-10-28T16:07:58.784Z'
total_duration: ~30 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-010
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On March 1, 2025, the payment processing service experienced a 30-minute SEV-2 outage caused by a timeout cascade originating from Stripe API rate limiting. A Stripe 429 (Too Many Requests) response was incorrectly classified as a transient network error, triggering exponential-backoff retries that saturated the gateway adapter thread pool. The cascade propagated to the use case layer, causing all payment authorization requests to time out. The circuit breaker eventually opened after 5 minutes, routing traffic to PayPal. PayPal handled the load successfully and all payment processing resumed.

The incident was detected by automated alerting at 14:23 UTC and resolved at 15:47 UTC when the long-running query was identified and terminated. A subsequent pod restart cleared the exhausted connection pool.

## Timeline

- **10:32** - Stripe begins rate-limiting the payment service (429 responses). Root cause: burst traffic from end-of-month billing cycle.
- **10:33** - Gateway adapter retries 429 responses as transient errors, saturating retry thread pool within 60 seconds.
- **10:34** - Incoming authorization requests begin timing out. `payments_5xx_rate_high` alert fires.
- **10:35** - On-call acknowledges alert. Begins diagnosis.
- **10:38** - On-call checks deploys — none since February 28.
- **10:40** - On-call identifies `stripe_429_rate` metric spiking in gateway dashboard.
- **10:42** - Circuit breaker opens after 5 failures in 30s. Traffic begins routing to PayPal.
- **10:45** - PayPal absorbs traffic. Authorization success rate recovers to 96%.
- **10:50** - On-call updates #payments-incidents: circuit breaker open, PayPal handling traffic.
- **11:00** - On-call escalates to tech lead per runbook (15-minute mark).
- **11:02** - Stripe rate limit window expires. Stripe circuit breaker enters half-open state.
- **11:04** - Circuit breaker closes. Stripe traffic resumes normally.
- **11:05** - Error rate drops to baseline. All metrics normal.
- **11:10** - Incident closed after 5-minute stable observation window.

## Impact

- **Duration**: ~30 minutes of degraded processing (10:34 - 11:04 UTC)
- **Failed authorizations**: ~180 requests failed during the initial 8-minute window before PayPal took over
- **Revenue impact**: Estimated $6,200 in delayed authorization processing; no permanent losses
- **SLA impact**: Monthly availability dropped to 99.88%, breaching the 99.9% target for March

## Root Cause Analysis

1. **Stripe 429 responses treated as transient errors**: The gateway adapter classified HTTP 429 responses as transient network errors and applied exponential-backoff retry logic. 429 responses are rate limits — not transient errors — and should not be retried against the same gateway. The retries saturated the adapter thread pool and propagated timeouts to all callers.

2. **Circuit breaker threshold tuned too conservatively**: The circuit breaker was configured to open after 5 failures in 30 seconds. During the 5-minute window before the circuit opened, 180 requests failed. A tighter threshold (e.g., 3 failures in 10 seconds) would have triggered faster failover.

## Resolution

1. Waited for circuit breaker to open and route traffic to PayPal — this resolved the cascade
2. Verified PayPal was handling authorization requests successfully
3. Monitored circuit breaker recovery and confirmed Stripe resumed normally after rate limit window expired

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Classify HTTP 429 as non-retryable in gateway adapter | Payments team | P1 | 2025-03-08 | Completed |
| Tighten circuit breaker threshold to 3 failures in 10s | Payments team | P1 | 2025-03-08 | Completed |
| Add `stripe_429_rate` metric to the primary on-call dashboard | SRE | P2 | 2025-03-15 | Completed |
| Implement Stripe rate limit header parsing to predict exhaustion | Payments team | P3 | 2025-04-01 | In progress |

## Lessons Learned

- **What went well**: The circuit breaker eventually worked as designed, routing traffic to PayPal and enabling recovery. On-call correctly identified the Stripe rate limit from the gateway metrics.
- **What went poorly**: 429 responses being treated as transient errors was a classification bug that amplified a minor Stripe rate-limit event into a full cascade. This should have been caught in code review.
- **What was lucky**: PayPal had sufficient capacity to absorb the burst traffic. Had both gateways been degraded simultaneously, the outage would have been significantly worse.
