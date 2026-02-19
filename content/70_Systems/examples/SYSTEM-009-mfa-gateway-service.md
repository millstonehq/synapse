---
id: SYSTEM-009
type: system
title: MFA Gateway Service
status: accepted
owner: User Engineering
owner_team: User Engineering
runtime: ECS Fargate / Python 3.12 / OpenSearch / Redis 7
created: '2024-06-07T10:22:15.422Z'
updated: '2026-06-06T13:40:03.332Z'
tags:
  - system
  - user-authentication
summary: MFA Gateway Service
sla: 99.95% monthly uptime
repos:
  - https://git.example.com/acme/mfa-gateway-service
dependencies:
  - User Directory Service
  - OAuth Authorization Server
runbooks:
  - RUNBOOK-012
  - RUNBOOK-008
example: true
---

## Overview

The MFA Gateway Service orchestrates multi-factor authentication challenges for users during login and step-up authentication flows. It supports TOTP (authenticator apps), SMS OTP, email OTP, and WebAuthn (hardware security keys and passkeys). The service determines which factor to challenge based on user enrollment and risk signals passed by the OAuth Authorization Server.

The service processes approximately 45,000 MFA challenges per day, with peak demand during business hours. Challenge codes are short-lived (60 seconds for OTP, 5 minutes for WebAuthn assertion) and stored in Redis to prevent replay attacks.

## Architecture

The service is built as a stateless Python FastAPI application running on ECS Fargate:

- **Challenge Router**: Receives step-up authentication requests from the OAuth Authorization Server and selects the appropriate factor based on user enrollment priority and request context.
- **TOTP Handler**: Validates time-based one-time passwords using RFC 6238. Implements a 1-period drift window (±30 seconds) and tracks used codes to prevent replay.
- **OTP Delivery**: Sends SMS and email OTPs through provider integrations (Twilio for SMS, SendGrid for email). Codes are stored in Redis with 60-second TTL.
- **WebAuthn Handler**: Implements WebAuthn Level 2 for passkey and security key verification. Relying party state is maintained in OpenSearch for audit and device management.
- **Enrollment API**: Allows users to register and remove MFA factors. TOTP enrollment generates QR-code provisioning URIs. WebAuthn enrollment stores credential public keys in OpenSearch.

## Repositories

- [mfa-gateway-service](https://git.example.com/acme/mfa-gateway-service) - Application code, Dockerfile, ECS task definition

## Runtime Environment

- **Platform**: ECS Fargate across 3 availability zones
- **Language**: Python 3.12 with FastAPI
- **Replicas**: 2 tasks minimum, autoscaling to 8 based on CPU utilization
- **Resources**: 0.5 vCPU / 1GB memory per task
- **Deployment**: Blue-green via AWS CodeDeploy with ALB weighted target groups
- **Secrets**: AWS Secrets Manager for Twilio and SendGrid API keys

## Dependencies

- Redis 7 — OTP code storage with TTL, challenge session state
- OpenSearch — WebAuthn credential storage and MFA audit log
- User Directory Service — user MFA enrollment lookups
- OAuth Authorization Server — receives step-up challenge requests, returns challenge results
- Twilio — SMS OTP delivery
- SendGrid — email OTP delivery

## SLA

| Metric | Target |
|--------|--------|
| Availability | 99.95% monthly uptime |
| Latency (challenge creation) | P50 < 100ms, P99 < 300ms |
| OTP delivery (SMS) | P50 < 3s, P99 < 10s |
| Error rate | < 0.2% 5xx responses |
| Recovery | MTTR < 30 minutes for SEV-1 incidents |

## Runbooks

- [[RUNBOOK-012|MFA Gateway Challenge Failures Runbook]]
- [[RUNBOOK-008|MFA Gateway Delivery Degradation Runbook]]
