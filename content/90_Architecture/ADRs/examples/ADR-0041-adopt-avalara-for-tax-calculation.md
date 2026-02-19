---
id: ADR-0041
type: adr
title: Adopt Avalara for Tax Calculation
status: draft
owner: Principal Engineer
created: '2024-08-10T18:52:17.301Z'
updated: '2026-10-21T14:22:51.702Z'
tags:
  - adr
  - billing-engine
summary: Adopt Avalara for Tax Calculation
example: true
---

## Context

The Billing Engine must collect and remit sales tax, VAT, and GST for customers in applicable jurisdictions. As the business crosses economic nexus thresholds in new US states and international markets, the number of active tax jurisdictions has grown from 5 to 42 states and 28 countries over the past 18 months. Managing tax rates, nexus registrations, and filing requirements manually is no longer feasible.

The current implementation applies a static tax rate table maintained by Finance, which is updated manually when rate changes occur. This approach has resulted in two tax calculation errors in Q1 2025 due to stale rates, both requiring invoice reissue and customer credits. Finance has escalated the tax calculation accuracy risk as a critical compliance issue.

We evaluated three approaches: Avalara AvaTax, TaxJar, and an in-house tax rate database.

## Decision

Adopt **Avalara AvaTax** as the tax calculation provider for the Billing Engine.

Integration approach: The Tax Calculation Engine will call the Avalara AvaTax v2 REST API for all tax calculations on invoice line items. Tax results will be cached in Redis with a 1-hour TTL. Avalara will also be used for address validation and nexus registration management. Tax filing and remittance will be handled by the Finance team via the Avalara portal; the Tax Calculation Engine is responsible for calculation only.

## Consequences

**Positive:**
- Avalara maintains tax rate tables for all US jurisdictions and 100+ countries, eliminating the manual rate maintenance burden
- AvaTax v2 API is well-documented with SDKs for Python; integration complexity is low
- Avalara's audit trail and tax return preparation features will reduce Finance overhead at filing time
- Address validation reduces the risk of assigning incorrect tax jurisdictions to customers

**Negative:**
- Avalara pricing is consumption-based; at scale, API call costs will grow with invoice volume (primary risk: exceeding contracted tier)
- Integration introduces a new external dependency in the invoice generation critical path; Avalara outages become billing outages without a fallback
- The Tax Calculation Engine must cache results aggressively to meet latency targets; cache invalidation errors (as seen in POSTMORTEM-048) are a known risk

**Neutral:**
- TaxJar (alternative) would be lower cost for US-only; Avalara's international coverage justifies the premium given our growth trajectory
- Avalara requires periodic nexus review as revenue thresholds are crossed; this is a Finance process change, not an engineering one

## Alternatives Considered

**TaxJar:**
- Pro: Lower cost than Avalara for US-only use cases; simpler API
- Con: International tax coverage is limited compared to Avalara. As we expand into EU and APAC markets, TaxJar's coverage would require supplementation with a second provider.
- Rejected because: International expansion is on the 12-month roadmap; adopting a US-only provider now would require a migration later.

**In-house tax rate database:**
- Pro: No external dependency; full control over rate data and update cadence
- Con: Maintaining accurate tax rate tables for 70+ jurisdictions is a full-time function. The March 2025 tax error (POSTMORTEM-048) and the February 2025 error were both caused by in-house rate management failures. This approach does not scale.
- Rejected because: The incident history demonstrates that in-house rate management at current jurisdictional footprint is not viable.
