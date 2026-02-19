---
id: STANDARD-022
type: standard
title: SMS Gateway Integration Standard
status: proposed
owner: Compliance Officer
created: '2024-11-14T16:10:18.441Z'
updated: '2025-07-23T10:45:44.731Z'
tags:
  - standard
  - notification-service
summary: SMS Gateway Integration Standard
related_policies:
  - POLICY-019
  - POLICY-020
example: true
related_systems:
  - SYSTEM-020
  - SYSTEM-018
---

## Area

This standard defines the integration requirements for SMS gateway providers (e.g., Twilio, Vonage) used by the Notification Service. It covers API authentication, message formatting, status callback handling, and failover configuration for SMS delivery.

## Controls

- SMS gateway API credentials must be stored in the secrets manager and rotated on a 90-day schedule; hardcoded credentials are prohibited
- All SMS API calls must use HTTPS; plaintext HTTP connections to gateway endpoints are not permitted
- Outbound SMS messages must not exceed 160 characters per segment; messages exceeding this must be reviewed for splitting behavior across carriers
- Gateway status callbacks (delivered, failed, undelivered) must be received and processed via a webhook endpoint secured with HMAC signature validation
- A secondary failover gateway must be configured; automatic failover must trigger within 2 minutes of primary gateway P95 latency exceeding 10 seconds
- Phone number validation (E.164 format) must occur before dispatch; invalid numbers must be rejected and logged without attempting delivery

## Compliance Mappings

- TCPA (Telephone Consumer Protection Act): Prior express written consent requirements
- NIST SP 800-53: SC-12 (Cryptographic Key Establishment and Management)
- SOC 2: CC6.7 (Transmission and Disclosure Controls)

## Related Policies

- [[POLICY-019|Push Notification Data Privacy Policy]]
- [[POLICY-020|Email Deliverability Standards Policy]]
