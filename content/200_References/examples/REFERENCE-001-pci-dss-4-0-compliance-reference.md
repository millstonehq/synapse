---
id: REFERENCE-001
type: reference
title: PCI DSS 4.0 Compliance Reference
status: draft
owner: Security Team
created: '2025-05-13T11:16:38.233Z'
updated: '2025-04-05T22:07:30.878Z'
tags:
  - reference
  - payment-processing
summary: PCI DSS 4.0 Compliance Reference
upstream_url: https://docs.example.com/pci-dss-4-0-compliance-reference
last_synced: '2025-06-15T03:41:00.257Z'
attribution: OWASP Foundation
license: CC BY-SA 4.0
category: other
example: true
---

## Overview

PCI DSS (Payment Card Industry Data Security Standard) version 4.0 was published by the PCI Security Standards Council in March 2022, replacing PCI DSS 3.2.1. It introduces customized implementation options alongside the traditional defined approach, focuses on security outcomes rather than prescriptive controls, and adds new requirements for authentication, vulnerability management, and targeted risk analysis.

Our organization processes card-not-present transactions exclusively and uses Stripe Elements for card data collection, which scopes us to SAQ A (the simplest self-assessment questionnaire). This reference summarizes the PCI DSS 4.0 requirements relevant to SAQ A merchants and our specific implementation.

## SAQ A Scope

SAQ A applies to merchants who have fully outsourced all card data functions to a PCI DSS compliant third-party service provider (Stripe). Requirements for SAQ A merchants:

- No storage, processing, or transmission of cardholder data on merchant systems
- Website pages that capture card data hosted and/or delivered from a PCI DSS compliant service provider
- All elements of the payment page(s) delivered only and directly from a PCI DSS validated third-party service provider

**How we satisfy this**: Stripe Elements (JavaScript hosted by Stripe) collects card data directly in the customer's browser. The tokenized payment method ID is the only value sent to our servers. We qualify for SAQ A.

## Key PCI DSS 4.0 Requirements (SAQ A Relevant)

### Requirement 6.4.3 - Payment Page Script Integrity

New in PCI DSS 4.0 (effective March 2025). All payment page scripts loaded and executed in the customer's browser must be managed, authorized, and have their integrity validated.

**How we address this**: Stripe Elements is loaded via an approved CDN URL with a Content Security Policy header restricting script sources. Subresource integrity (SRI) hashes are verified on script load. CSP violation reporting is enabled and alerts are reviewed monthly.

### Requirement 6.4.3 - Third-Party Script Management

Merchants must maintain an inventory of all third-party scripts used on payment pages and confirm their integrity and authorization.

**How we address this**: Monthly audit of all third-party scripts on checkout pages. Authorized scripts list maintained in the security team's Confluence page. Any new script requires security review before deployment to checkout pages.

### Requirement 12.3.2 - Targeted Risk Analysis

PCI DSS 4.0 requires a targeted risk analysis for requirements that allow entity-specific frequency. This applies to our annual PCI compliance review schedule.

**How we address this**: Annual risk assessment conducted by the security team. Assessment documented and reviewed by the CTO. Next review due Q4 2025.

## What Changed from PCI DSS 3.2.1

- **Multi-factor authentication**: Now required for all accounts with access to the cardholder data environment, not just remote access. Our Stripe dashboard access uses MFA via Google Authenticator.
- **Password requirements**: Minimum 12 characters (up from 7 in 3.2.1). Applied to all admin accounts.
- **Vulnerability scanning**: Authenticated internal scans now required. Covered by our quarterly Nessus scan schedule.
- **Customized approach**: PCI DSS 4.0 allows organizations to implement alternative controls if they can demonstrate equivalent protection. We use the traditional defined approach — not applicable to SAQ A but relevant if we expand scope.

## Sync Notes

This reference covers PCI DSS 4.0 requirements as they apply to our SAQ A scope as of the last sync date. The full PCI DSS 4.0 specification is available from the PCI Security Standards Council. Re-sync annually before the compliance review or when we expand our payment scope.
