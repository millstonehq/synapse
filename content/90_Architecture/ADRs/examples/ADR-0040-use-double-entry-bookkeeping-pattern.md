---
id: ADR-0040
type: adr
title: Use Double-Entry Bookkeeping Pattern
status: proposed
owner: Staff Engineer
created: '2025-10-19T02:54:51.519Z'
updated: '2025-11-05T11:39:15.259Z'
tags:
  - adr
  - billing-engine
summary: Use Double-Entry Bookkeeping Pattern
example: true
---

## Context

The Billing Engine's internal financial ledger currently uses a single-entry accounting model where each billing event creates a single row recording either a charge or a credit. As the platform has grown to support refunds, proration credits, credit notes, and tax adjustments, the single-entry model has become increasingly difficult to reconcile accurately. Finance has reported recurring discrepancies between the internal ledger and Stripe that require manual investigation.

The Finance team and external auditors have requested that the ledger meet Generally Accepted Accounting Principles (GAAP) requirements, including the ability to produce a trial balance and audit trail that is verifiable by a third party. The current single-entry model cannot satisfy these requirements. At $1M+ MRR, the accounting accuracy risk is material.

## Decision

Implement a **double-entry bookkeeping pattern** for the Billing Engine's internal financial ledger.

Every financial transaction will create two entries in the ledger: a debit and a corresponding credit of equal amount. The ledger will maintain account classifications (accounts receivable, deferred revenue, revenue, tax liability, refund expense) aligned with GAAP categories. The sum of all debits must always equal the sum of all credits; any imbalance is a system invariant violation and will trigger an alert.

The existing single-entry event log will be retained as an audit trail but will no longer be the primary ledger. The double-entry ledger will be the source of truth for revenue reporting and reconciliation.

## Consequences

**Positive:**
- Ledger self-validates: any processing error that creates an imbalance is immediately detectable
- Revenue reconciliation against Stripe becomes trivial: Stripe charges map 1:1 to ledger debit entries
- Supports production of a GAAP-compliant trial balance for Finance and auditors
- Refunds, credits, and proration adjustments have a natural representation (reversing entries)

**Negative:**
- Migration from single-entry to double-entry requires a full ledger restatement — significant one-time engineering and Finance effort
- All billing event handlers must be updated to create balanced entry pairs rather than single rows
- Developers unfamiliar with accounting concepts will need training on double-entry semantics

**Neutral:**
- The double-entry ledger is internal only; Stripe remains the external payment record and the two are reconciled daily
- The account taxonomy will initially be minimal (5 accounts) and can be expanded as Finance requirements evolve

## Alternatives Considered

**Improve single-entry model with better reconciliation tooling:**
- Pro: Lower migration cost; no conceptual shift for engineering
- Con: Does not address the fundamental auditability problem. A single-entry model cannot produce a self-validating trial balance. Reconciliation discrepancies will continue.
- Rejected because: Finance and auditors have explicitly stated that the current model is insufficient for GAAP compliance at current revenue scale.

**Delegate revenue recognition entirely to Stripe Revenue Recognition:**
- Pro: No internal ledger engineering required; Stripe Revenue Recognition handles ASC 606 deferral and recognition automatically
- Con: Stripe Revenue Recognition costs $0.05 per transaction; at $5M MRR this is $50K/year. More importantly, it does not support our custom usage-based billing complexity and proration rules.
- Rejected because: Cost is significant at scale, and Stripe Revenue Recognition cannot model our complex proration and credit note patterns.
