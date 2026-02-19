---
id: GUIDE-048
type: guide
title: Alert Fatigue Reduction Guide
status: approved
owner: Developer Experience
created: '2024-01-20T06:40:47.916Z'
updated: '2026-11-27T01:20:24.173Z'
tags:
  - guide
  - monitoring-stack
summary: Alert Fatigue Reduction Guide
audience: partner
related_systems:
  - SYSTEM-039
  - SYSTEM-038
related_sops:
  - SOP-073
  - SOP-078
example: true
---

## The Alert Fatigue Problem

When too many alerts fire that don't require action, engineers start ignoring all alerts — including the ones that matter. Alert fatigue is one of the most dangerous failure modes in a monitoring system because it causes real incidents to go unnoticed. The goal is not to eliminate alerts, but to ensure that every alert that fires is: actionable, urgent enough to page, and linked to a runbook that tells the responder exactly what to do.

This guide explains how to identify noisy alerts and how to fix them.

## Diagnosing Your Alert Quality

Start with the numbers. Pull your team's alert history from PagerDuty for the last 30 days. For each alert, calculate the action rate: what percentage of fires resulted in an engineer actually doing something (vs. acknowledging and resolving without action).

An alert with an action rate below 50% is noisy. An alert with an action rate below 20% should be evaluated for removal or threshold adjustment.

Also look at the time distribution. Alerts that fire almost exclusively during business hours but wake engineers at night suggest the threshold is too sensitive relative to nighttime traffic patterns.

## Five Fixes for Noisy Alerts

**Fix 1: Raise the threshold.** If an alert fires for conditions that engineers routinely assess as "normal," the threshold is too low. Use historical Prometheus data to find the 99th percentile value for normal operation, then set the alert threshold above that.

**Fix 2: Increase the for duration.** A `for: 1m` alert fires on brief spikes that self-resolve. Increasing to `for: 5m` or `for: 10m` eliminates transient noise. Most alerts should have a minimum `for: 5m` duration.

**Fix 3: Add symptom-based alerting instead of cause-based.** Alert on "error rate is high" rather than "memory is above 80%." Symptom-based alerts are directly tied to user impact and have much higher action rates.

**Fix 4: Consolidate related alerts.** If you have three alerts that all fire at the same time during the same incident, merge them into one alert with a better description. AlertManager's grouping rules can help here.

**Fix 5: Delete alerts that no longer correspond to actionable conditions.** If there is no runbook for an alert and engineers have never taken action on it, delete it. The monitoring system is not a "we might need this someday" archive.

## Implementing the Alert Tuning Process

Alert quality improvement is not a one-time project — it requires regular review. Follow the Alert Tuning Process to establish a monthly cadence for reviewing alert quality metrics and implementing improvements.

Before each tuning cycle, generate an alert action rate report from PagerDuty. Any alert below 60% action rate is a candidate for tuning. Focus first on P1 alerts that are noisy, as they are most directly damaging to on-call engineer wellbeing.

## Measuring Success

Track your team's alert action rate as a monthly metric. Target: 70% or higher overall, 85% or higher for P1 alerts. Also track mean-time-to-acknowledge (MTTA) and mean-time-to-resolve (MTTR). If alert fatigue is decreasing, MTTA should decrease as engineers become more confident that alerts are real.

## Next Steps

- Run the Alert Tuning Process with your team using last month's alert statistics
- Review the Alert Definition Standard for requirements on `for` durations and runbook linkage
- Use the Silence Noisy Alert SOP for immediate relief while root cause fixes are in progress
