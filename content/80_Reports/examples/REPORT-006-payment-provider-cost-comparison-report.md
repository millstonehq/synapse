---
id: REPORT-006
type: report
title: Payment Provider Cost Comparison Report
status: accepted
owner: Payment Tech Lead
created: '2024-11-01T03:00:03.469Z'
updated: '2025-12-26T10:05:44.656Z'
tags:
  - report
  - payment-processing
summary: Payment Provider Cost Comparison Report
company: PaymentProcessing
report_month: 2025-04
report_type: company
overall_health: excellent
confidence: low
active_initiatives_count: 6
critical_risks_count: 0
example: true
---

## Service Health

| Metric | Stripe (Primary) | PayPal (Secondary) | Adyen (Evaluated) |
|--------|------------------|--------------------|-------------------|
| Transaction fee | 2.9% + $0.30 | 3.49% + $0.49 | 0.3% + interchange |
| Monthly platform fee | $0 | $0 | $120 |
| Availability (90-day) | 99.95% | 99.72% | 99.98% |
| Auth success rate | 97.8% | 96.1% | 98.3% |
| P95 response time | 180ms | 340ms | 155ms |

This report compares the total cost of ownership and reliability metrics for the three payment providers evaluated during Q1 2025. All figures are based on actual production data for Stripe and PayPal, and vendor-provided benchmarks for Adyen.

## Key Highlights

- **Stripe remains most cost-effective at current volume**: At 50,000 transactions/day, Stripe costs approximately $51,000/month in processing fees. PayPal is 24% more expensive per transaction with lower reliability. Adyen's interchange-plus pricing would save approximately $8,000/month but requires PCI DSS Level 1 compliance, which we do not currently hold.
- **PayPal reliability concern**: PayPal's 90-day availability of 99.72% is below our 99.9% SLA requirement. It is adequate as a fallback gateway but unsuitable as a primary processor.
- **Adyen deferred**: Adyen offers the best per-transaction economics and performance, but onboarding requires 3-month implementation and PCI Level 1 certification. Recommended for evaluation in H2 2025.

## Active Initiatives

1. **Volume discount renegotiation with Stripe**: Finance is in discussions with Stripe for a volume discount tier. Current volume qualifies for custom pricing at the enterprise tier.
2. **PayPal fallback SLA review**: Assess whether PayPal's reliability warrants keeping it as the secondary gateway, or whether a different failover strategy is needed.

## Incidents

No payment provider incidents to report this period.

## Risks

- **Medium**: Single primary provider creates concentration risk. Adyen evaluation is the medium-term mitigation.
- **Low**: Stripe pricing changes announced for Q3 2025. Impact estimated at +4% on international card transactions.

## Next Month Focus

- Complete Stripe volume discount negotiation
- Finalize Adyen feasibility assessment for H2 planning
- Publish provider reliability data to the SRE dashboard
