---
id: MEETING-006
type: meeting
title: Stripe to Adyen Migration Kickoff
status: deprecated
owner: Engineering Manager
created: '2024-12-05T05:18:41.643Z'
updated: '2025-06-04T19:12:45.218Z'
tags:
  - meeting
  - payment-processing
summary: Stripe to Adyen Migration Kickoff
company: PaymentProcessing
topic: Stripe to Adyen Migration Kickoff
meeting_date: '2025-04-01T02:31:45.904Z'
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

- **Project**: Stripe to Adyen Migration
- **Topic**: Stripe to Adyen Migration Kickoff
- **Date/Time**: 2025-04-01, 02:31 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Official kickoff meeting for the Stripe to Adyen primary provider migration; aligns the team on scope, timeline, success criteria, and communication plan

## Observations by Domain

- **Scope Confirmation**: Migration covers all card transactions (Visa, Mastercard, Amex); PayPal and bank transfer flows remain on Stripe for this phase
- **Adyen Adapter Readiness**: Adapter is feature-complete with 100% test pass rate; production credentials have been received and stored in secrets manager
- **Reconciliation Adapter**: Reconciliation format adapter for Adyen is complete and validated against 30 days of sample Adyen settlement files
- **Token Migration Plan**: Silent background re-tokenization approved for stored cards; new transactions will be tokenized via Adyen from Phase 1 start
- **Monitoring Readiness**: Adyen-specific Grafana dashboards are live in staging; on-call runbook for Adyen-specific alerts has been written and reviewed

## Key Metrics & Data Points

- **Adyen Adapter Load Test Result**: 1,800 TPS sustained (130% of current Stripe peak volume)
- **Reconciliation Format Validation**: 100% match rate against 30-day Adyen sample data
- **Phase 1 Merchant Count**: 12 merchants, representing 3.1% of transaction volume
- **Estimated Phase 1 Duration**: 2 weeks before assessment for Phase 2
- **Rollback Time Estimate**: <5 minutes (routing config change only)
- **Token Migration Progress**: 0% (begins at Phase 1 start)

## Preliminary Scorecard Hooks

- Technical Readiness: 5/5 - All pre-migration gates passed; adapter, reconciliation, and monitoring ready
- Rollback Confidence: 5/5 - Fast routing rollback tested; token rollback is not needed due to phased approach
- Migration Risk: 4/5 - Phase 1 scope is minimal; main risk is unforeseen Adyen behavior at scale
- Stakeholder Alignment: 4/5 - Finance, Product, and Engineering aligned; merchant communication sent
- Timeline Confidence: 4/5 - All dependencies resolved; schedule is realistic

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| Unexpected Adyen behavior in production not seen in load test | Medium | Low | Principal Engineer | Monitor Phase 1 closely for 48 hours with senior engineer on standby | 2025-04-03 |
| Merchant impact from token re-tokenization | Low | Low | Product Manager | Monitor checkout conversion rate for Phase 1 merchants; pause if conversion drops >2% | 2025-04-15 |
| Adyen settlement timing differs from Stripe | Low | Medium | Tech Lead | Validate Adyen settlement schedule against Finance reconciliation window | 2025-04-05 |

## Decisions & Next Steps

### Decisions

- Phase 1 migration approved to start 2025-04-02 at 10:00 UTC during low-traffic window
- Success criteria for Phase 1 to Phase 2 promotion: >98.5% success rate and <500ms P95 latency sustained for 5 business days
- Senior engineer on standby for first 48 hours of Phase 1

### Action Items

- Principal Engineer to initiate Phase 1 routing change at scheduled time and post status in #payment-migration channel
- Tech Lead to validate Adyen settlement timing with Finance by 2025-04-05
- Engineering Manager to send merchant communication to Phase 1 merchants before migration start

### Follow-ups

- Phase 1 assessment meeting in 5 business days to review metrics and decide on Phase 2 timing
- QA Lead to run full regression suite against Phase 1 merchants' transaction data
