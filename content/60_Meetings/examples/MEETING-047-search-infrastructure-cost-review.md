---
id: MEETING-047
type: meeting
title: Search Infrastructure Cost Review
status: approved
owner: Principal Engineer
created: '2024-01-25T23:47:37.604Z'
updated: '2026-10-21T20:01:33.581Z'
tags:
  - meeting
  - search-platform
summary: Search Infrastructure Cost Review
company: SearchPlatform
topic: Search Infrastructure Cost Review
meeting_date: '2024-03-04T15:18:18.347Z'
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

- **Project**: Search Platform - Q1 Cost Review
- **Topic**: Search Infrastructure Cost Review
- **Date/Time**: 2024-03-04 03:00 PM CT
- **Attendees (engineering)**: Principal Engineer, DevOps Lead, SRE Lead
- **Attendees (product)**: Engineering Manager, FinOps Analyst
- **Context**: Monthly infrastructure cost review. Search platform costs exceeded budget by 18% in February, primarily due to unplanned scaling event and retained snapshot storage.

## Observations by Domain

- **Compute**: 8 data nodes running at r6g.2xlarge ($0.504/hr each); 3 master nodes at r6g.xlarge; total compute cost of $3,150/month — 20% above the $2,625 budget
- **Storage**: EBS volumes totaling 12TB attached to data nodes; additionally, 8TB of snapshot storage in S3 has been accumulating since cluster inception with no retention policy
- **Data Transfer**: Cross-AZ data transfer for shard replication generating $420/month in unexpected costs; single-AZ replication was not considered in the original architecture
- **Idle Resources**: Staging cluster runs at full production size 24/7; reducing staging to 50% capacity during off-hours could save approximately $800/month
- **Snapshot Retention**: No snapshot retention policy exists; oldest snapshots date back 14 months; retaining only the last 30 days of snapshots would recover 6TB of S3 storage
- **Reserved Instances**: All Elasticsearch nodes are running on on-demand pricing; converting to 1-year reserved instances would reduce compute cost by approximately 35%

## Key Metrics & Data Points

- **February actual spend**: $5,890 (budget: $5,000; 18% over)
- **Compute cost**: $3,150/month (47% over compute budget)
- **S3 snapshot storage**: 8TB at $0.023/GB = $184/month; growing at ~400GB/month with no retention policy
- **Cross-AZ data transfer**: $420/month (not budgeted)
- **Staging cluster cost**: $1,600/month (could be reduced to ~$800 with off-hours scaling)
- **Estimated savings from reserved instances**: ~$1,100/month

## Preliminary Scorecard Hooks

- Cost vs Budget Alignment: 2/5 - Consistently over budget; no cost controls or reserved capacity in place
- Storage Efficiency: 2/5 - No snapshot retention policy; growing unbounded
- Resource Right-Sizing: 3/5 - Production nodes appropriately sized; staging is over-provisioned
- Cost Visibility: 3/5 - Cost tagging implemented; per-component breakdown available but no alerting on budget thresholds

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Snapshot storage cost growing unbounded | Medium | Certain | DevOps Lead | Implement 30-day snapshot retention policy immediately | 2024-03-15 |
| Cross-AZ transfer costs continuing to grow with traffic | Medium | High | Principal Engineer | Evaluate single-AZ replication topology for non-critical replica shards | 2024-04-01 |
| On-demand compute costs unsustainable at planned growth rate | High | Certain | Engineering Manager | Purchase 1-year reserved instances for 6 of 8 data nodes | 2024-03-31 |

## Decisions & Next Steps

### Decisions

- Implement 30-day snapshot retention policy before end of March
- Purchase 1-year reserved instances for the 6 steady-state data nodes (keep 2 on-demand for burst)
- Implement staging cluster off-hours scaling (scale to 3 nodes at 8pm, restore at 8am)

### Action Items

- Configure snapshot lifecycle policy with 30-day retention (DevOps Lead - 2024-03-15)
- Submit reserved instance purchase order for 6 r6g.2xlarge nodes (Engineering Manager - 2024-03-31)
- Implement Kubernetes CronJob for staging cluster auto-scaling (DevOps Lead - 2024-03-25)

### Follow-ups

- Cost review in 60 days to validate savings from reserved instance and snapshot changes
- Add budget threshold alerting at 90% of monthly allocation
