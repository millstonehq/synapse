---
id: MEETING-067
type: meeting
title: CI/CD Cost Optimization Discussion
status: approved
owner: Principal Engineer
created: '2025-01-18T00:19:40.738Z'
updated: '2025-11-18T10:17:39.068Z'
tags:
  - meeting
  - ci-cd-platform
summary: CI/CD Cost Optimization Discussion
company: CI/CDPlatform
topic: CI/CD Cost Optimization Discussion
meeting_date: '2025-11-10T21:32:10.864Z'
example: true
our_attendees:
  - Principal Engineer
  - Tech Lead
  - Product Manager
their_attendees:
  - Engineering Manager
  - QA Lead
---

## Meeting Details

- **Project**: Engineering Cost Reduction Initiative
- **Topic**: Analysis of CI/CD platform cost drivers and identification of optimization opportunities targeting 30% cost reduction
- **Date/Time**: 2025-11-10 21:32 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Q3 2025 cloud bill showed CI/CD platform spend increased 58% year-over-year; Finance has asked Engineering to identify a path to 30% reduction before budget planning

## Observations by Domain

- **Runner Instance Types**: 70% of runners are on-demand compute at full price; spot instance pricing for non-blocking CI jobs would reduce compute cost by approximately 60%
- **Idle Runner Capacity**: Runner fleet maintains 30% idle capacity at all hours; autoscaler minimum floor is set conservatively but peak demand only occurs for 4 hours per day
- **Storage Costs**: Container registry stores all image layers including those from deleted branches; no lifecycle policy has been applied; registry storage has grown 340 GB in 12 months
- **Redundant Pipeline Runs**: Analysis shows 22% of pipeline runs are triggered by low-value events (whitespace commits, documentation-only changes); these could be conditionally skipped
- **Build Cache Bandwidth**: Pipelines are transferring full cache archives on every cache miss; partial cache restore would reduce cache-related data transfer by an estimated 45%

## Key Metrics & Data Points

- **Monthly CI/CD platform cloud spend**: $34,200 (Q3 2025 average)
- **Compute cost as % of total**: 71% ($24,300/month)
- **Storage cost as % of total**: 18% ($6,200/month)
- **Estimated spot instance savings**: $14,600/month (60% of on-demand compute)
- **Registry storage growth rate**: 340 GB over 12 months; lifecycle policy could reduce by 60%

## Preliminary Scorecard Hooks

- Compute Efficiency: 2/5 - All-on-demand runner fleet is significantly over-priced for interruptible CI workloads
- Storage Management: 1/5 - No lifecycle policies; unbounded growth is unsustainable
- Pipeline Trigger Efficiency: 3/5 - Redundant runs identified but path filtering not yet implemented
- Cache Efficiency: 3/5 - Caching works but bandwidth optimization not explored
- Cost Visibility: 2/5 - No per-team or per-service cost attribution; difficult to hold teams accountable

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Spot instance interruption causes deployment pipeline failures | High | Medium | Tech Lead | Restrict spot instances to non-deployment CI jobs; keep deployment runners on-demand | 2025-12-15 |
| Registry lifecycle policy deletes production-pinned image layers | High | Low | Principal Engineer | Protect tagged production images; lifecycle policy only removes untagged layers | 2025-12-01 |
| Path filtering skips required security scans for sneaky changes | Medium | Low | QA Lead | Ensure security scan stage is never path-filtered; run on all pushes regardless | 2025-12-01 |

## Decisions & Next Steps

### Decisions
- Migrate non-deployment CI runners to spot instances; retain on-demand runners only for production deployment pipelines
- Implement container registry lifecycle policy to remove untagged layers older than 30 days and feature-branch images older than 14 days after branch deletion
- Implement path-based pipeline filtering to skip full pipeline runs for documentation-only and whitespace changes

### Action Items
- Tech Lead to configure the spot instance autoscaler and test with non-blocking CI jobs before end of November
- Principal Engineer to design and apply the registry lifecycle policy; validate no production images are deleted before activation
- Engineering Manager to implement per-team cost attribution tagging to enable cost accountability dashboards

### Follow-ups
- Review cloud spend in 60 days after optimizations are live; target 30% reduction validated against baseline
- Present cost optimization results to Finance at the Q1 2026 budget review
