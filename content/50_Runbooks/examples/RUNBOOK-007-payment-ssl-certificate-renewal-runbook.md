---
id: RUNBOOK-007
type: runbook
title: Payment SSL Certificate Renewal Runbook
status: approved
owner: On-Call Engineer
created: '2025-11-01T11:08:41.312Z'
updated: '2025-06-08T23:26:19.669Z'
tags:
  - runbook
  - payment-processing
summary: Payment SSL Certificate Renewal Runbook
example: true
---

## Service

- **System**: [[SYSTEM-001|Payment Gateway Service]]
- **Owner team**: Payments Engineering
- **On-call rotation**: PagerDuty schedule "payments-oncall"
- **Slack channel**: #payments-incidents
- **Runtime**: ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache

## Alerts

- `PaymentSSLCertExpiringSoon` — payment API TLS certificate expires within 30 days
- `PaymentSSLCertExpiringCritical` — payment API TLS certificate expires within 7 days
- `PaymentSSLCertExpired` — TLS certificate has expired; payment endpoints returning TLS handshake errors
- `GatewayMTLSCertExpiring` — mutual TLS client certificate for gateway communication expires within 14 days

## Diagnosis Steps

1. **Identify expiring certificate** - Confirm which certificate is expiring: check the payment API load balancer certificate (ACM or manual cert), the mutual TLS client certificate used for gateway communication, and the webhook endpoint certificate.
2. **Check certificate details** - Run `openssl s_client -connect payment-api.example.com:443 -showcerts` to confirm current certificate expiry date and issuing CA.
3. **Verify ACM auto-renewal status** - If using AWS ACM, check the certificate status in the ACM console; ACM auto-renews certificates if DNS validation is properly configured and the domain is accessible.
4. **Check DNS validation records** - For ACM certificates, confirm the required CNAME DNS validation records are present in Route 53; missing records block auto-renewal.
5. **Review gateway mTLS requirements** - Confirm the certificate format and key type required by the gateway provider; some gateways require specific CA-signed certificates not eligible for ACM.

## Remediation Steps

1. **If ACM auto-renewal is failing due to DNS**: Add the missing DNS validation CNAME record in Route 53; ACM will retry validation and renew automatically within minutes.
2. **If manual certificate renewal is required**: Generate a new CSR, obtain a signed certificate from the approved CA, and upload it to ACM or the load balancer certificate store.
3. **If gateway mTLS certificate is expiring**: Generate a new key pair and CSR; submit to the gateway provider for signing per their onboarding instructions; update in secrets manager before the old cert expires.
4. **If certificate has already expired**: Immediately issue an emergency certificate via ACM or Let's Encrypt; update the load balancer listener certificate; monitor for TLS handshake recovery.
5. **If webhook endpoint certificate expired**: Update the certificate on the webhook endpoint load balancer; notify affected merchant integrations of brief disruption.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms certificate expiry timeline and renewal path |
| 15 min | If certificate expires within 24 hours and renewal is blocked, notify Engineering Manager |
| 30 min | Engineering Manager escalates to DevOps Lead for emergency certificate issuance |
| 60 min | If certificate expired and payment endpoints are returning TLS errors, declare P1 incident |

## Dashboards

- [SSL Certificate Expiry Monitor](https://grafana.example.com/d/ssl-certs) - Certificate expiry dates for all payment endpoints
- [Payment TLS Error Rate](https://grafana.example.com/d/payment-tls) - TLS handshake failures and connection errors by endpoint
- [Gateway Connectivity Health](https://grafana.example.com/d/gateway-connectivity) - mTLS connection success rate per gateway
