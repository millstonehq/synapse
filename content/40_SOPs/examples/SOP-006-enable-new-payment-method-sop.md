---
id: SOP-006
type: sop
title: Enable New Payment Method SOP
status: approved
owner: DevOps Lead
created: '2024-02-08T11:04:55.906Z'
updated: '2026-06-26T15:39:05.204Z'
tags:
  - sop
  - payment-processing
summary: Enable New Payment Method SOP
related_process: PROCESS-061
related_systems:
  - SYSTEM-001
example: true
---

## Preconditions

- The payment method has completed the Payment Method Certification Process and holds a valid certification sign-off
- The payment method adapter is deployed to production behind a feature flag in the disabled state
- Gateway credentials for the payment method are stored in the secrets management system
- Merchant documentation for the payment method has been published
- Product and Finance teams have been notified of the planned enablement date

## Materials/Access

- Access to the feature flag management console with write permissions for payment method flags
- Access to the payment service configuration to update the enabled payment methods list
- Access to the payment observability dashboard to monitor enablement metrics
- Merchant sandbox environment for post-enablement smoke tests
- #payments-releases Slack channel for stakeholder communication

## Procedure

1. Confirm all prerequisites are met: certification sign-off on file, credentials in secrets manager, documentation published.
2. In the feature flag console, locate the payment method feature flag and set the rollout percentage to 1% of eligible merchants.
3. Monitor the payment observability dashboard for 30 minutes; confirm the payment method is processing transactions successfully at the 1% rollout.
4. If no errors are observed, increase the rollout to 10%, then 50%, then 100% in 30-minute increments, monitoring between each step.
5. Run the smoke test suite in the merchant sandbox environment to confirm end-to-end flows (authorization, capture, refund) are working correctly.
6. Update the payment method status in the merchant portal from "coming soon" to "available."
7. Post in #payments-releases: "[Payment Method] enabled for 100% of eligible merchants. Success rate: X%."
8. Notify the Product and Finance teams that enablement is complete via email or Slack.

## Validation

- Payment method is processing transactions at 100% rollout with a success rate above 98%
- No elevated error rates or latency anomalies observed in the observability dashboard
- Smoke test suite passes for all required payment flows
- Merchant portal shows the payment method as available
- Finance has confirmed the payment method will appear correctly in settlement reports

## Rollback

1. If elevated error rates or failures are observed at any rollout stage, set the feature flag rollout percentage back to 0%.
2. Post in #payments-releases: "[Payment Method] rollout paused. Error rate: X%. Investigating."
3. Investigate the root cause using payment service logs and gateway error responses.
4. After identifying and resolving the issue, re-run the certification smoke tests before resuming rollout.
5. If the issue cannot be resolved within 4 hours, notify the Platform Lead and schedule a root cause review before any further rollout attempts.
