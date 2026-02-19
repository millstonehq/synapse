---
id: POSTMORTEM-037
type: postmortem
title: Alert Storm During Deploy 2024-12-22
status: deprecated
owner: Incident Commander
created: '2025-04-18T00:52:54.481Z'
updated: '2026-11-26T15:54:42.554Z'
tags:
  - postmortem
  - monitoring-stack
summary: Alert Storm During Deploy 2024-12-22
incident_number: INC-738
severity: SEV-3
incident_date: '2025-08-18'
detection_time: '2026-06-25T09:18:52.832Z'
resolution_time: '2025-09-04T23:58:58.194Z'
total_duration: ~15 minutes
affected_customers:
  - All customers using payment processing
revenue_impact: Estimated $12,000 in delayed payment processing
related_sop: SOP-077
action_items:
  - Implement connection pool monitoring alerts
  - Add circuit breaker for database connections
  - Update runbook with connection pool diagnosis
example: true
---

## Executive Summary

On December 22, 2024, a routine deployment of the Alert Management Service triggered a 15-minute alert storm that generated 312 alert firings across 8 services simultaneously. The storm was caused by a misconfigured alert inhibition rule that was inadvertently disabled as part of the deployment, combined with the rolling restart of Alert Management Service pods temporarily reducing its webhook processing capacity. PagerDuty received 47 high-urgency pages in 8 minutes, waking multiple on-call engineers. No actual production degradation occurred — all 312 alerts were false positives triggered by brief pod startup periods during the rolling restart.

## Timeline

- **22:14** - Alert Management Service deploy begins (rolling restart, 3 pods)
- **22:15** - Pod 0 restarts; brief AlertManager webhook processing delay as routing reconverges
- **22:16** - AlertManager inhibition rule referencing `alert-management-svc` target fails to resolve (deployment in progress); inhibition disabled
- **22:16** - 312 inhibited alerts become uninhibited simultaneously and begin evaluating
- **22:17** - First wave of PagerDuty pages: 47 high-urgency pages sent in 8 minutes
- **22:19** - On-call engineer acknowledges storm; silences all alerting for 30 minutes via AlertManager API
- **22:22** - Deploy completes; all 3 pods healthy
- **22:23** - Inhibition rules re-enable as Alert Management Service returns to healthy state
- **22:29** - Silence lifted; normal alerting resumes with no further storms

## Impact

- **Duration**: 15 minutes of alert storm (22:14-22:29)
- **Engineers paged**: 6 engineers woken up at 22:17 UTC (10:17 PM local time)
- **PagerDuty pages**: 47 high-urgency pages sent; all resolved within 15 minutes
- **Production impact**: Zero — all alerts were false positives from the rolling restart window
- **On-call disruption**: Significant — Christmas holiday period, on-call engineers woken unnecessarily

## Root Cause Analysis

1. **Inhibition rule tied to service health**: The inhibition rule suppressing rolling-restart noise referenced the Alert Management Service's own health check endpoint as the source target. When the service was mid-deploy and pods were restarting, the inhibition source was briefly unreachable, disabling all inhibitions simultaneously rather than gracefully.

2. **Missing pre-deploy alert silence**: Standard operating procedure for monitoring-stack deploys did not include creating a pre-emptive AlertManager silence for the duration of the rolling restart. This gap allowed transient pod startup alerts to propagate uninhibited.

## Resolution

1. Created a 30-minute AlertManager silence to stop the alert storm
2. Waited for deploy to complete (3 minutes)
3. Lifted silence; confirmed inhibition rules re-enabled
4. Sent acknowledgement to all paged engineers; confirmed no production issue

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Add pre-deploy silence creation to Alert Management Service deploy SOP | On-call | P1 | 2025-01-06 | Completed |
| Refactor inhibition rules to use label-based matching instead of service health endpoints | SRE | P1 | 2025-01-15 | Completed |
| Add deployment runbook step: verify inhibition rules active post-deploy | Monitoring Eng | P2 | 2025-01-10 | Completed |
| Create automated deploy silence script for monitoring-stack service deploys | SRE | P2 | 2025-01-31 | Completed |

## Lessons Learned

- **What went well**: On-call engineer identified the storm was deploy-related quickly (5 minutes) and used the AlertManager silence API to stop the pages before escalation was needed.
- **What went poorly**: The deploy runbook had no step for creating a pre-emptive silence. An inhibition rule architecture that depends on the service being deployed is fragile by design.
- **What was lucky**: This happened during a low-traffic period. Had it been during business hours, the false-positive storm would have masked any real alerts firing simultaneously.
