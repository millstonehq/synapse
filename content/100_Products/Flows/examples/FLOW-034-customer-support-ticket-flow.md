---
id: FLOW-034
type: flow
title: Customer Support Ticket Flow
status: approved
owner: QA Engineer
created: '2025-12-30T21:34:19.726Z'
updated: '2025-05-13T23:53:34.381Z'
tags:
  - flow
  - customer-portal
summary: Customer Support Ticket Flow
feature_area: Customer Portal
related_prds:
  - PRD-045
example: true
---

## Steps

### Step 1: Navigate to Support and open the ticket form

User clicks "Submit Ticket" from the Quick Actions on the dashboard or navigates to `/support/tickets/new`. The ticket creation form loads with fields for Subject, Description, and optional file attachments.

### Step 2: Fill in the ticket details

User enters a subject line (5–120 characters) and a description (10–5000 characters). User optionally attaches up to 3 files (JPG, PNG, PDF; max 5 MB each) using the file picker. The form shows a character count for the description field.

### Step 3: Submit the ticket

User clicks "Submit Ticket". The portal sends a `createSupportTicket` GraphQL mutation to the Customer API Gateway. The form enters a loading state while the request is in flight.

### Step 4: Confirmation and redirect

On success, the portal redirects the user to the new ticket's detail page at `/support/tickets/{id}`. A success toast notification confirms "Ticket submitted — we'll respond within 4 business hours." A `ticket_update` notification is published to the Notification Center.

On validation error (e.g., subject too short, attachment too large), inline field-level error messages are shown. The form does not clear; the user can correct the errors and resubmit.

## Expected Results

- A new support ticket is created in the backend with status `open`
- The customer can see the ticket in their ticket list at `/support/tickets`
- An email notification is sent to the customer confirming ticket creation within 60 seconds
- The ticket is visible in the Zendesk agent console immediately
- An optional in-app notification appears in the Notification Center badge

## User Info

| Field | Value |
|-------|-------|
| Role | Customer (authenticated, email verified) |
| Permissions | Can create tickets, view own tickets, add comments to own tickets |
| Test account | portal-test-customer@example.com |
| Environment | Staging (portal.staging.example.com) |
| Prerequisites | Customer must have a verified account and an active session |
