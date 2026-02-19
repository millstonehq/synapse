---
id: REFERENCE-019
type: reference
title: ASC 606 Revenue Recognition Reference
status: published
owner: Engineering Team
created: '2024-12-04T07:26:21.795Z'
updated: '2026-05-21T00:55:14.792Z'
tags:
  - reference
  - billing-engine
summary: ASC 606 Revenue Recognition Reference
upstream_url: https://docs.example.com/asc-606-revenue-recognition-reference
last_synced: '2025-10-14T19:07:26.464Z'
attribution: IETF
license: CC BY-SA 4.0
category: blog-post
example: true
---

## Overview

ASC 606 (Accounting Standards Codification Topic 606, "Revenue from Contracts with Customers") is the US GAAP standard governing how companies recognize revenue. It replaced the prior revenue recognition guidance in 2018 and requires a consistent, principles-based five-step model. For SaaS companies like ours with subscription and usage-based billing, ASC 606 has significant implications for when and how subscription revenue, usage revenue, and deferred revenue are recorded. This reference documents the five-step model and its application to the Billing Engine's financial ledger.

## The Five-Step Model

### Step 1: Identify the Contract with the Customer

A contract exists when there is an approved agreement that creates enforceable rights and obligations. For the Billing Engine, this corresponds to the customer accepting our terms of service and activating a subscription. The contract includes the subscription plan, its pricing, and any commitments made at the time of purchase (e.g., annual commitment at a discount).

**Billing Engine implication**: The subscription creation event in the Subscription Management Service marks the inception of the contract. The subscription ID is the contract identifier for all revenue recognition purposes.

### Step 2: Identify the Performance Obligations

A performance obligation is a promise to transfer a distinct good or service to the customer. For subscription products, the primary performance obligation is providing access to the platform for the subscription period. For usage-based billing, a separate performance obligation exists for each unit of metered service consumed.

**Billing Engine implication**: Flat-rate subscriptions have a single time-based performance obligation (access per period). Usage-based components create a variable consideration obligation that is recognized as the customer consumes units.

### Step 3: Determine the Transaction Price

The transaction price is the amount expected to be received in exchange for fulfilling the performance obligations. For fixed-price subscriptions, this is straightforward. For usage-based components, variable consideration rules apply — the transaction price includes an estimate of usage-based charges using the expected value method.

**Billing Engine implication**: Usage-based revenue estimates are constrained by the variable consideration constraint (only include amounts that are highly probable not to result in a significant revenue reversal). In practice, usage revenue is recognized as usage occurs rather than estimated in advance.

### Step 4: Allocate the Transaction Price

When a contract contains multiple performance obligations, the transaction price is allocated based on the standalone selling price of each obligation. For bundled plans (flat rate + metered components), the price must be allocated between the components.

**Billing Engine implication**: The Invoice Generation Pipeline allocates contract price between flat-rate and metered line items at invoice generation time. The double-entry ledger records the allocation in separate revenue accounts (deferred revenue, revenue recognized).

### Step 5: Recognize Revenue When Performance Obligations Are Satisfied

Revenue is recognized when control of the promised service is transferred to the customer. For subscription services, this means recognizing revenue ratably over the subscription period. For usage-based components, revenue is recognized as the customer consumes the metered units.

**Billing Engine implication**: Subscription prepayments are recorded as deferred revenue (liability) and recognized ratably each day of the period. The Billing Event Processor moves amounts from deferred revenue to recognized revenue on a daily basis for active subscriptions.

## Sync Notes

This reference summarizes ASC 606 as it applies to SaaS subscription and usage-based billing at our company. For the complete standard text, consult the FASB Accounting Standards Codification. Review with the Controller when pricing model changes are made or when new revenue streams are added. Last reviewed by Finance in Q4 2024.
