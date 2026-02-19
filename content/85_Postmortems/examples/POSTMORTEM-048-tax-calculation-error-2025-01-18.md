---
id: POSTMORTEM-048
type: postmortem
title: Tax Calculation Error 2025-01-18
status: approved
owner: Incident Commander
created: '2024-06-13T00:06:19.495Z'
updated: '2025-02-26T01:06:06.205Z'
tags:
  - postmortem
  - billing-engine
summary: Tax Calculation Error 2025-01-18
incident_number: INC-929
severity: SEV-2
incident_date: '2025-05-02'
detection_time: '2026-04-25T20:18:21.876Z'
resolution_time: '2024-12-19T07:43:12.688Z'
total_duration: ~30 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-092
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On January 18, 2025, the Tax Calculation Engine began returning incorrect tax amounts for customers in California due to a stale Avalara tax rate cache. Avalara updated California sales tax rates for 2025 on January 1, but the Tax Calculation Engine's Redis cache still contained the pre-2025 rates. The cache TTL was set to 24 hours, but a bug in the cache invalidation logic prevented the new rates from being loaded. The error affected approximately 1,200 invoices generated between January 1 and January 18, which were reissued with corrected amounts. Total tax overcollection was $8,340, which was credited back to affected customers.

The error was detected on January 18 by the Finance team during their monthly tax reconciliation review, not by automated monitoring. The issue was present from January 1 but went undetected for 18 days.

## Timeline

- **2025-01-01 00:00** - Avalara tax rate update for 2025 takes effect, including California rate changes
- **2025-01-01 01:00** - Tax Calculation Engine cache TTL expires; cache invalidation logic runs but fails silently due to a key format mismatch introduced in a December 31 deploy
- **2025-01-01 01:01** - Engine begins serving cached 2024 California tax rates for new calculations; existing cached entries for non-California jurisdictions are unaffected
- **2025-01-18 14:20** - Finance team queries Avalara reconciliation report; identifies systematic 0.25% overcollection on California invoices since January 1
- **2025-01-18 14:35** - Finance escalates to Billing Engineering
- **2025-01-18 15:10** - Engineer identifies cache invalidation bug introduced in the December 31 deploy
- **2025-01-18 15:30** - Hotfix deployed: cache invalidation key format corrected; all California tax cache entries flushed
- **2025-01-18 15:45** - Tax calculations verified correct against Avalara for a sample of California customers
- **2025-01-18 16:00** - Incident resolved. Finance team begins audit of affected invoices.

## Impact

- **Duration**: 18 days (2025-01-01 to 2025-01-18)
- **Customers affected**: ~1,200 California customers billed during the period
- **Revenue impact**: $8,340 in tax overcollection; credits issued to all affected customers
- **SLA impact**: No availability SLA breach; Tax calculation accuracy SLA missed
- **Customer communications**: Proactive email sent to affected customers with explanation and credit confirmation

## Root Cause Analysis

1. **Cache invalidation key format regression**: A December 31 deploy changed the Redis key format for tax rate cache entries (from `tax_rate:{jurisdiction}` to `taxrate:{jurisdiction}`). The cache invalidation logic that runs on Avalara rate updates still used the old key format, so it found no matching keys to invalidate. New calculations continued to read from the old keys, which had not yet expired.

2. **No tax rate freshness monitoring**: There was no alert or monitoring for cache age relative to the last known Avalara rate update date. The stale cache condition was undetectable by automated systems.

## Resolution

1. Deployed hotfix correcting cache invalidation key format to match current schema
2. Flushed all California tax rate cache entries to force recalculation from Avalara
3. Audited all California invoices generated January 1-18 and identified 1,200 affected invoices
4. Reissued corrected invoices and issued customer credits totaling $8,340

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add test asserting cache invalidation runs correctly after a key format change | Billing Engineering | P1 | 2025-01-25 | Completed |
| Add monitoring alert for tax rate cache age exceeding 26 hours | SRE | P1 | 2025-01-25 | Completed |
| Add automated tax rate correctness spot-check after each Avalara rate update | Billing Engineering | P2 | 2025-02-01 | In progress |
| Add cache key format version to configuration for visibility | Billing Engineering | P2 | 2025-02-07 | Pending |

## Lessons Learned

- **What went well**: Finance team's monthly reconciliation process caught the error before it compounded further. Customer credit process was smooth and completed within 48 hours of detection.
- **What went poorly**: The error was undetected for 18 days because there was no monitoring for tax rate cache freshness. A deploy that changed cache key format had no test coverage for the invalidation path.
- **What was lucky**: The California rate change was 0.25% overcollection rather than undercollection; undercollection would have created a tax liability rather than a customer credit obligation.
