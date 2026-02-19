---
id: RUNBOOK-006
type: runbook
title: High Payment Decline Rate Runbook
status: approved
owner: On-Call Engineer
created: '2024-07-20T21:20:36.045Z'
updated: '2025-10-01T20:38:32.761Z'
tags:
  - runbook
  - payment-processing
summary: High Payment Decline Rate Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache

## Alerts

- `PaymentDeclineRateHigh` — authorization decline rate exceeds 10% for any 5-minute window
- `PaymentDeclineRateCritical` — authorization decline rate exceeds 25% sustained for 3 minutes
- `FraudDeclineRateSpike` — fraud-rule-triggered decline rate increases by more than 5x baseline in 10 minutes
- `SpecificIssuerDeclinesHigh` — decline rate for a specific card issuer exceeds 30% indicating issuer-side issue

## Diagnosis Steps

1. **Break down decline reasons** - Query the payment observability dashboard decline breakdown by error code; differentiate between issuer declines (`do_not_honor`, `insufficient_funds`), fraud blocks, and technical errors (`gateway_timeout`, `invalid_card`).
2. **Check for fraud rule changes** - Review the fraud detection service audit log for recent rule changes; a misconfigured or overly aggressive rule can cause false-positive blocks.
3. **Check gateway-side decline reporting** - Log into the gateway dashboard and review decline reason codes from the acquiring bank; compare with what the platform is logging to confirm accuracy.
4. **Identify affected segment** - Determine if declines are concentrated on a specific card type, issuer, geographic region, or merchant; concentrated failures suggest a routing or configuration issue.
5. **Review recent platform changes** - Check for recent updates to payment request formatting, 3DS configuration, or fraud scoring weights that may be triggering issuer rejections.

## Remediation Steps

1. **If fraud rule misconfiguration**: Revert the recent fraud rule change in the fraud detection service; monitor decline rate recovery over 10 minutes.
2. **If specific issuer experiencing elevated declines**: Route affected card transactions to an alternate gateway if available; contact the gateway account manager for issuer-specific guidance.
3. **If 3DS configuration change is suspected**: Revert 3DS exemption or threshold settings to the previous values; some issuers require 3DS and will decline without it.
4. **If technical error codes dominate**: Check the gateway health check runbook; technical declines indicate a gateway connectivity or configuration issue, not issuer-side.
5. **If issuer-wide incident**: No direct remediation; communicate to merchant support team; monitor for issuer recovery; do not retry hard-decline responses.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer analyzes decline reason code breakdown |
| 15 min | If decline rate above 15% with no clear cause, notify Engineering Manager |
| 30 min | Engineering Manager notifies Product and Finance; assess merchant impact |
| 60 min | Director of Engineering and Head of Payments engaged if decline rate remains elevated |

## Dashboards

- [Payment Decline Analysis](https://grafana.example.com/d/payment-declines) - Decline rate by reason code, issuer, and card type
- [Fraud Detection Metrics](https://grafana.example.com/d/fraud-metrics) - Fraud rule trigger rates and false positive trends
- [Payment Success Rate Overview](https://grafana.example.com/d/payment-success) - Overall and segmented authorization success rates
