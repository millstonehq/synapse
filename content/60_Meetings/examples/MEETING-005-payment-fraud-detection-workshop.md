---
id: MEETING-005
type: meeting
title: Payment Fraud Detection Workshop
status: review
owner: Product Manager
created: '2025-08-31T19:03:27.759Z'
updated: '2025-10-21T02:52:20.841Z'
tags:
  - meeting
  - payment-processing
summary: Payment Fraud Detection Workshop
company: PaymentProcessing
topic: Payment Fraud Detection Workshop
meeting_date: '2024-05-21T06:59:21.218Z'
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

- **Project**: Fraud Detection Improvement Initiative
- **Topic**: Payment Fraud Detection Workshop
- **Date/Time**: 2024-05-21, 06:59 UTC
- **Attendees (engineering)**: Principal Engineer, Tech Lead
- **Attendees (product)**: Product Manager, Engineering Manager, QA Lead
- **Context**: Workshop to review current fraud detection capabilities, analyze recent fraud patterns, and design improvements to reduce both fraud losses and false positive rates

## Observations by Domain

- **Fraud Detection Coverage**: Rule-based engine covers 92% of transaction volume; ML scoring model covers 78% (model not yet deployed for all payment methods)
- **False Positive Rate**: Current 0.8% false positive rate translates to approximately 960 legitimate transactions declined daily at current volume
- **Card Testing Attacks**: Three card testing attacks detected in April; velocity rules caught them within 4 minutes on average but caused elevated decline noise during detection window
- **Cross-Border Fraud**: Transactions from high-risk geographies show 3.5x average fraud rate; current rule set does not distinguish between first-time and returning customers from these regions
- **3D Secure Utilization**: 3DS is only enforced above $200; lowering the threshold could reduce fraud but adds customer friction at lower amounts

## Key Metrics & Data Points

- **Fraud Rate (chargebacks)**: 0.31% of transaction volume
- **ML Model Coverage**: 78% of transactions scored (target: 100%)
- **False Positive Rate**: 0.8% (industry benchmark: 0.5%)
- **Average Card Testing Attack Detection Time**: 4.2 minutes
- **3DS Trigger Rate**: 12% of transactions (would increase to ~22% if threshold lowered to $100)
- **Fraud Losses Q1 2024**: $142,000 net of recovered chargebacks

## Preliminary Scorecard Hooks

- ML Model Coverage: 3/5 - 78% coverage leaves a significant gap; all payment methods need scoring
- False Positive Rate: 3/5 - Above industry benchmark; hurts conversion and customer experience
- Velocity Rule Effectiveness: 4/5 - Card testing detection is fast; noise during attacks needs reduction
- Cross-Border Controls: 2/5 - Rules do not account for customer history; too blunt for high-risk geographies
- 3DS Strategy: 3/5 - Current threshold may be leaving fraud exposure; needs data-driven review

## Risks and Mitigations

| Risk | Severity | Likelihood | Owner | Mitigation | Due Date |
|------|----------|------------|-------|------------|----------|
| ML model gap enables fraud on uncovered payment methods | High | Medium | Tech Lead | Extend ML scoring to all payment methods by Q3 | 2024-09-01 |
| High false positive rate causing merchant churn | Medium | Medium | Product Manager | A/B test tighter false positive threshold on low-risk merchant segment | 2024-07-01 |
| 3DS threshold too high leaving fraud exposure | Medium | Low | Principal Engineer | Analyze chargeback data by transaction value to determine optimal threshold | 2024-06-15 |

## Decisions & Next Steps

### Decisions

- ML model coverage expansion is approved as a Q3 initiative; target 100% payment method coverage
- 3DS threshold analysis approved; Product Manager to present data-driven recommendation at next workshop
- False positive rate improvement target set at 0.5% by end of Q3

### Action Items

- Tech Lead to create a roadmap for extending ML scoring to all payment methods
- Principal Engineer to pull chargeback data segmented by transaction value for 3DS threshold analysis
- Product Manager to design A/B test framework for false positive threshold tuning

### Follow-ups

- Second fraud workshop scheduled in 6 weeks to review ML expansion plan and 3DS analysis results
- QA Lead to create fraud simulation test scenarios for ML model validation
