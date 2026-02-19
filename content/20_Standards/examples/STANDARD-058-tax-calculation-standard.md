---
id: STANDARD-058
type: standard
title: Tax Calculation Standard
status: approved
owner: Head of Engineering
created: '2024-12-03T21:39:44.451Z'
updated: '2025-10-25T03:35:04.972Z'
tags:
  - standard
  - billing-engine
summary: Tax Calculation Standard
related_policies:
  - POLICY-049
  - POLICY-048
example: true
related_systems:
  - SYSTEM-050
  - SYSTEM-049
---

## Area

This standard defines requirements for tax rate determination, tax amount calculation, tax jurisdiction identification, and tax record keeping across all Billing Engine invoices. It applies to the tax calculation service and all billing workflows that produce taxable line items.

Tax compliance is a legal requirement in all jurisdictions where the platform operates. Errors in tax calculation carry direct financial liability and potential regulatory penalties.

## Controls

- Tax jurisdiction must be determined from the customer's billing address at the time of invoice generation; changes to billing address after invoice finalization must not retroactively affect tax on issued invoices
- Tax rates must be sourced from the authoritative tax rate configuration table, which must be updated within 5 business days of any jurisdiction rate change
- Tax amounts must be calculated and stored independently for each applicable jurisdiction; combined tax lines are not permitted
- All tax calculations must be logged with the rate applied, the jurisdiction code, the taxable amount, and the calculated tax, linked to the invoice ID
- Reverse-charge VAT scenarios must be identified and handled programmatically; the platform must not invoice VAT on cross-border B2B transactions within applicable regions

## Compliance Mappings

- SOC 2 CC6.6: Tax calculation logic changes must go through the standard change control process with audit trail
- US Sales Tax Nexus Rules (post-Wayfair): Economic nexus thresholds by state must be evaluated quarterly and enforced in tax determination logic
- EU VAT Directive 2006/112/EC: VAT rates and exemption logic for EU member states must comply with current directive schedules

## Related Policies

- [[POLICY-049|Invoice Retention Policy]]
- [[POLICY-048|Billing Dispute Resolution Policy]]
