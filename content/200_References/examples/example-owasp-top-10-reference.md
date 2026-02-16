---
id: owasp-top-10-2021-reference
type: reference
title: OWASP Top 10 - 2021
status: published
owner: Security Team
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - reference
  - security
  - owasp
summary: >-
  Synced copy of the OWASP Top 10 Web Application Security Risks (2021
  edition) for offline reference and internal linking. USE A REFERENCE
  when you need to bring EXTERNAL CONTENT into the vault for offline
  access, searchability, and cross-linking. References answer "where is
  that external doc we keep citing?" They are synced copies of upstream
  content (vendor docs, standards, blog posts) with attribution and a
  last_synced timestamp. Compare: a Standard defines your internal
  controls; a Reference links to the external standard you're
  implementing. A Wiki is auto-generated from code; a Reference is
  manually curated from external sources.
upstream_url: https://owasp.org/Top10/
last_synced: '2025-10-18T00:00:00.000Z'
attribution: OWASP Foundation
license: CC BY-SA 4.0
category: standard
example: true
---

## Overview

The OWASP Top 10 is a standard awareness document for developers and web application security. It represents a broad consensus about the most critical security risks to web applications. This 2021 edition includes significant changes from the 2017 version, with three new categories and updated scope.

Our internal [[example-change-control-standard|Change Control Standard]] references OWASP Top 10 as the baseline for application security requirements.

## The 2021 Top 10

### A01:2021 - Broken Access Control

Moved up from #5. 94% of applications were tested for some form of broken access control. Access control enforces that users cannot act outside their intended permissions. Failures lead to unauthorized information disclosure, modification, or destruction of data.

**How we address this**: JWT validation on every API request, role-based access control enforced at the handler layer, row-level database filtering by tenant ID.

### A02:2021 - Cryptographic Failures

Previously "Sensitive Data Exposure" - renamed to focus on the root cause rather than the symptom. Relates to failures in cryptography that lead to exposure of sensitive data.

**How we address this**: TLS 1.3 for all external traffic, mTLS between services, AES-256 encryption at rest for payment data, secrets rotated every 90 days via Kubernetes Secrets.

### A03:2021 - Injection

Dropped from #1 to #3. Includes SQL injection, NoSQL injection, OS command injection, and LDAP injection. Cross-site scripting is now part of this category.

**How we address this**: Parameterized queries exclusively (no string concatenation in SQL), input validation at API boundaries, Content Security Policy headers.

### A04:2021 - Insecure Design

New category for 2021. Focuses on risks related to design flaws - distinct from implementation bugs. Calls for threat modeling and secure design patterns.

**How we address this**: TDD process requires a "Risks and Mitigations" section, threat modeling during architecture reviews, state machine design for payment lifecycle prevents invalid transitions.

### A05:2021 - Security Misconfiguration

Moved up from #6. Includes missing security hardening, misconfigured permissions, unnecessary features enabled, and default credentials.

**How we address this**: Infrastructure as Code (Terraform) ensures consistent configuration, CIS benchmark scans in CI, no default credentials in any environment.

### A06:2021 - Vulnerable and Outdated Components

Previously "Using Components with Known Vulnerabilities." Refers to using libraries, frameworks, or software modules with known vulnerabilities.

**How we address this**: Dependabot alerts enabled on all repos, monthly dependency update cycle, Go module vulnerability scanning via `govulncheck` in CI.

### A07:2021 - Identification and Authentication Failures

Previously "Broken Authentication." Covers weaknesses in authentication mechanisms.

**How we address this**: Centralized auth service with JWT, token expiration enforced, rate limiting on auth endpoints, no custom cryptography.

### A08:2021 - Software and Data Integrity Failures

New category. Focuses on assumptions about software updates, critical data, and CI/CD pipelines without verifying integrity.

**How we address this**: Signed container images, immutable deployment artifacts tagged by commit SHA, blue-green deployments with health check gates.

### A09:2021 - Security Logging and Monitoring Failures

Previously "Insufficient Logging & Monitoring." Without logging and monitoring, breaches cannot be detected.

**How we address this**: Structured logging for all authentication and payment state changes, audit trail via immutable payment_events table, alerting on anomalous patterns.

### A10:2021 - Server-Side Request Forgery (SSRF)

New category for 2021. SSRF flaws occur when a web application fetches a remote resource without validating the user-supplied URL.

**How we address this**: Gateway adapter layer uses allowlisted URLs only (Stripe and PayPal endpoints), no user-supplied URLs in backend-to-backend calls.

## Sync Notes

This reference summarizes the OWASP Top 10 2021 with annotations specific to our stack. For the full original content, see the upstream URL. Re-sync when a new edition is published (typically every 3-4 years).
