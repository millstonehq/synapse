---
id: RUNBOOK-079
type: runbook
title: Customer Portal SSL Certificate Runbook
status: approved
owner: On-Call Engineer
created: '2024-03-18T06:46:36.290Z'
updated: '2025-01-23T19:29:41.355Z'
tags:
  - runbook
  - customer-portal
summary: Customer Portal SSL Certificate Runbook
example: true
---

## Service

- **System**: [[SYSTEM-041|Customer Portal Web Application]]
- **Owner team**: Portal Engineering
- **On-call rotation**: PagerDuty schedule "portal-oncall"
- **Slack channel**: #portal-incidents
- **Runtime**: Vercel (portal frontend) + Kubernetes (Customer API Gateway, backend services)

## Alerts

- `portal_ssl_cert_expiry_14d` - Portal TLS certificate expires in less than 14 days
- `portal_ssl_cert_expiry_3d` - Portal TLS certificate expires in less than 3 days (critical)
- `portal_ssl_handshake_error_rate_high` - TLS handshake error rate exceeds 0.5% for 5 minutes
- `portal_api_gateway_ssl_cert_expiry_7d` - Customer API Gateway TLS certificate expires in less than 7 days

## Diagnosis Steps

1. **Identify which certificate is expiring or erroring** — Check the alert details for the certificate domain. The portal has two certificate domains: `portal.company.com` (Vercel-managed) and `api.portal.company.com` (internal Kubernetes API Gateway). The remediation path differs by domain.

2. **For portal.company.com (Vercel-managed certificate)** — Log into the Vercel dashboard at `https://vercel.com/dashboard`. Navigate to the Customer Portal project > Settings > Domains. Check the certificate status for `portal.company.com`. Vercel auto-renews certificates 30 days before expiry via Let's Encrypt. If the cert shows "Failed" or "Pending", proceed to Remediation.

3. **For api.portal.company.com (Kubernetes cert-manager)** — Run `kubectl get certificate -n portal` and `kubectl describe certificate portal-api-tls -n portal` to check certificate status and renewal events. Check cert-manager logs: `kubectl logs -n cert-manager deploy/cert-manager | tail -100 | grep portal-api-tls`.

4. **Check for DNS issues** — Certificate renewal failures are often caused by DNS propagation issues. Run `dig portal.company.com` and verify the A record points to the expected Vercel edge IP. Run `dig api.portal.company.com` and verify the A record points to the internal load balancer IP. A stale or incorrect DNS record will cause ACME HTTP-01 challenge failures.

5. **Check for ACME challenge failures** — In cert-manager, look for `CertificateRequest` and `Order` resources in the `portal` namespace: `kubectl get certificaterequest,order -n portal`. A failed `Order` will have a `reason` field describing the ACME challenge error.

6. **Verify current certificate details** — From any host: `openssl s_client -connect portal.company.com:443 -servername portal.company.com 2>/dev/null | openssl x509 -noout -dates`. Confirms the current certificate's `notAfter` date.

## Remediation Steps

1. **Vercel certificate shows "Pending" or "Failed"** — In the Vercel dashboard, click the domain `portal.company.com` and click "Refresh" or "Retry" on the certificate. If the error is "DNS verification failed," check that the DNS A record for `portal.company.com` points to the Vercel edge and that no proxy (Cloudflare proxy) is intercepting the ACME HTTP-01 challenge path (`/.well-known/acme-challenge/`).

2. **cert-manager certificate renewal failure (Kubernetes)** — Delete the failed `Order` object to trigger a retry: `kubectl delete order -n portal -l cert-manager.io/certificate-name=portal-api-tls`. cert-manager will create a new Order automatically. Monitor with `kubectl get order -n portal -w` until status is `valid`.

3. **DNS record incorrect** — Update the DNS record in Route 53 (or the authoritative DNS provider). For `portal.company.com`, confirm the record with the Platform team before changing. DNS TTL is 300 seconds; wait for propagation before retrying certificate renewal.

4. **Emergency: certificate already expired (portal.company.com)** — Contact Vercel support immediately (support.vercel.com) with the project ID and domain name. Vercel can manually trigger certificate issuance. If Vercel support SLA is too slow, add a temporary CNAME override to a subdomain with a valid certificate while the renewal is in progress.

5. **Emergency: certificate already expired (api.portal.company.com)** — Apply a manually-issued certificate from the company CA: `kubectl create secret tls portal-api-tls-emergency --cert=emergency.crt --key=emergency.key -n portal`. Update the Ingress to reference the new secret. File a follow-up ticket to restore automated cert-manager renewal.

6. **TLS handshake errors but certificate is valid** — Check if the error is caused by a cipher suite mismatch. Run `nmap --script ssl-enum-ciphers -p 443 api.portal.company.com` to list supported ciphers. If old TLS 1.0/1.1 clients are being rejected, this is expected behavior; confirm with the security team before relaxing cipher policy.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and checks certificate status |
| 10 min | Post status update in #portal-incidents |
| 20 min | If renewal not progressing: page Portal tech lead via PagerDuty |
| 60 min | If cert expired and portal is unreachable: declare SEV-1, page Engineering Manager, begin customer communication |

**Who to escalate to:**
- Portal tech lead: PagerDuty schedule "portal-leads"
- DNS and infrastructure issues: PagerDuty schedule "infra-oncall"
- Vercel platform issues: Vercel support portal (https://vercel.com/support)
- cert-manager issues: Platform Engineering team via #platform-engineering

## Dashboards

- [Portal Certificate Monitor](https://grafana.example.com/d/portal-certs) - Certificate expiry countdown for all portal domains
- [Portal TLS Errors](https://grafana.example.com/d/portal-tls) - TLS handshake error rate over time
- [Vercel Project Dashboard](https://vercel.com/dashboard) - Deployment status, domain health
- [cert-manager Status](https://grafana.example.com/d/cert-manager) - Certificate issuance and renewal status across all namespaces
