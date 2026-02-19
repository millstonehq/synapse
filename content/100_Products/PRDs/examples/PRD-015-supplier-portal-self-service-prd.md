---
id: PRD-015
type: prd
title: Supplier Portal Self-Service PRD
status: approved
owner: Senior PM
created: '2024-01-27T16:39:30.214Z'
updated: '2026-02-26T06:09:43.879Z'
tags:
  - prd
  - inventory-management
summary: Supplier Portal Self-Service PRD
related_tdds:
  - TDD-011
  - TDD-014
example: true
related_standards:
  - STANDARD-013
---

## Summary

Build a self-service supplier portal that allows suppliers to acknowledge purchase orders, provide estimated delivery dates, and submit advance shipping notices (ASNs) directly through a web interface. This replaces the current email and phone-based supplier coordination workflow and gives merchants real-time visibility into inbound shipment status through the Stock Level Calculator ([[TDD-011|TDD-011]]) and the Warehouse Integration Adapter ([[TDD-014|TDD-014]]).

## Goals

- Eliminate email back-and-forth between merchants and suppliers for PO acknowledgements and delivery date confirmations
- Give merchants real-time inbound shipment visibility by surfacing ASN data in the inventory platform
- Reduce inbound stock discrepancies by enabling suppliers to submit accurate unit counts before goods arrive
- Provide suppliers with a branded, self-service interface that reduces support burden on merchant operations teams

## In Scope

- Supplier registration and account management (invitation-based, linked to a merchant's supplier record)
- Purchase order acknowledgement: supplier confirms receipt of a PO and accepts or rejects line items
- Estimated delivery date submission and updates
- Advance Shipping Notice (ASN) creation: supplier submits item quantities, pallet/carton counts, and carrier tracking numbers before shipment
- ASN status tracking for merchants: in-preparation, shipped, in-transit, delivered
- In-app notification to merchant when supplier acknowledges a PO or submits an ASN
- Supplier activity audit log per merchant (which supplier user performed which action, when)

## Out of Scope

- Supplier payment or invoicing workflows
- Automated EDI 856 ASN transmission to warehouse systems (phase 2)
- Multi-supplier catalogue or RFQ features
- Supplier performance scoring or analytics
- Integration with carrier tracking APIs for real-time shipment location

## Users and Flows

**Suppliers** receive an email invitation from a merchant to join the portal. After registering, they see a dashboard of open purchase orders from that merchant. When a PO arrives, they acknowledge it (accepting or flagging discrepancies), enter an estimated delivery date, and later submit an ASN when goods are packed and ready to ship. The portal guides them through each step with in-product prompts.

**Merchants** initiate supplier invitations from the portal settings. They see a real-time view of which POs have been acknowledged, what delivery dates suppliers have committed to, and which shipments are in transit with confirmed unit counts. This replaces the manual email tracking spreadsheets currently used by merchant operations teams.

**Merchant operations staff** monitor the supplier activity dashboard to chase overdue PO acknowledgements, review ASN accuracy against PO quantities, and flag discrepancies to the relevant supplier before goods arrive at the warehouse.

## Requirements

- Invite a supplier to the portal via email with a time-limited registration link (72-hour expiry)
- Supplier account scoped to a single merchant; a supplier can hold accounts across multiple merchants independently
- Display all open and recently closed POs for a supplier on their dashboard, sourced from the purchase order store
- Allow suppliers to acknowledge a PO with status: accepted, partially accepted (with line-item notes), or rejected with reason
- Allow suppliers to set and update an estimated delivery date per PO; notify merchant on each update
- Allow suppliers to create an ASN against a PO with: carton count, total units per SKU, carrier name, and tracking number
- Display ASN status to merchants in the inbound shipments view, refreshed within 15 seconds of supplier action
- Enforce that ASN total units do not exceed the PO ordered quantity per SKU (with override allowed by merchant)
- Require two-factor authentication for supplier portal login
- All supplier actions logged in an immutable audit trail accessible to the merchant

## KPIs

- **PO acknowledgement time**: Median time from PO creation to supplier acknowledgement reduced from 48 hours to < 8 hours within 90 days
- **ASN coverage**: 70% of POs have an ASN submitted before expected delivery date within 6 months
- **Inbound discrepancy rate**: Receiving discrepancies (actual vs ASN unit count) < 5% of line items within 6 months
- **Supplier adoption**: 60% of invited suppliers complete registration and acknowledge at least one PO within 30 days

## Information Architecture

- Supplier portal served at `suppliers.example.com` (separate subdomain from merchant portal)
- Supplier-facing API calls the Stock Level Calculator's inbound shipment endpoints ([[TDD-011|TDD-011]])
- Warehouse adapter ([[TDD-014|TDD-014]]) receives ASN data and forwards it to the relevant WMS upon delivery confirmation
- PO data sourced from the Automated Reorder System's purchase order store
- Supplier accounts, ASNs, and acknowledgements stored in a dedicated PostgreSQL schema

## Data Model

- **SupplierAccount**: `supplier_id`, `merchant_id`, `contact_name`, `contact_email`, `registered_at`, `status` (invited|active|suspended)
- **POAcknowledgement**: `ack_id`, `po_id`, `supplier_id`, `status` (accepted|partial|rejected), `notes`, `estimated_delivery_date`, `acknowledged_at`
- **AdvanceShippingNotice**: `asn_id`, `po_id`, `supplier_id`, `carrier`, `tracking_number`, `total_cartons`, `status` (draft|submitted|in_transit|delivered), `submitted_at`
- **ASNLineItem**: `line_id`, `asn_id`, `sku_id`, `qty_shipped`

## Non-Functional

- Supplier portal must support 500 concurrent supplier sessions without degradation
- Invitation link generation and email delivery must complete within 30 seconds
- All supplier-facing endpoints must enforce merchant-scoped data isolation: suppliers can only view their own merchant's POs
- Supplier portal pages must load within 3 seconds on a standard broadband connection
- Audit log entries must be immutable; no soft-delete on supplier action records

## Constraints

- Supplier portal authentication is independent of the merchant portal SSO; suppliers authenticate via email/password with enforced MFA
- No raw card or payment data is collected on the supplier portal
- ASN data is transmitted to WMS only via the existing Warehouse Integration Adapter; no direct WMS connections from the supplier portal

## Risks

- **Supplier adoption friction**: Suppliers unfamiliar with self-service portals may resist using the tool. Mitigation: Provide a simple onboarding wizard, supplier-facing help documentation, and a fallback email-to-ASN parsing feature for phase 2.
- **ASN accuracy**: Inaccurate ASNs submitted by suppliers could cause receiving teams to plan incorrectly. Mitigation: Display variance alerts to merchants when ASN quantities diverge from PO quantities by > 10%.
- **Invitation link security**: Compromised invitation links could allow unauthorized supplier registrations. Mitigation: Single-use tokens with 72-hour expiry, rate-limited per merchant.

## Milestones

### M1: Supplier Registration and PO Acknowledgement (Week 1-5)

#### Deliverables

- Supplier invitation flow (email + registration)
- PO acknowledgement (accept / partial / reject with notes)
- Estimated delivery date entry and merchant notification
- Merchant supplier management dashboard

#### Acceptance Criteria

- Supplier can receive an invitation, register an account, and acknowledge a test PO end-to-end
- Merchant receives in-app notification within 60 seconds of supplier acknowledgement
- Supplier cannot view POs belonging to a different merchant

### M2: Advance Shipping Notices (Week 6-9)

#### Deliverables

- ASN creation form with SKU-level unit counts and carrier information
- ASN status tracking in merchant inbound shipments view
- ASN quantity validation against PO ordered quantities
- Warehouse adapter integration to forward ASN on delivery confirmation

#### Acceptance Criteria

- Supplier can submit an ASN and merchant sees it in inbound view within 15 seconds
- System rejects ASN line item quantities exceeding PO ordered quantity (unless merchant override is set)
- ASN data forwarded to WMS via warehouse adapter on delivery status update

### M3: Audit, Security, and Production Launch (Week 10-12)

#### Deliverables

- Immutable supplier activity audit log accessible to merchants
- Two-factor authentication enforcement for supplier logins
- Security penetration test and findings remediation
- Supplier onboarding guide and merchant setup documentation

#### Acceptance Criteria

- Audit log records all supplier actions with timestamp, actor, and affected record
- MFA is enforced for all supplier accounts; bypass is not possible
- Penetration test has zero critical findings before launch
