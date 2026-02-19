---
id: FLOW-036
type: flow
title: Customer Onboarding Flow
status: approved
owner: QA Engineer
created: '2024-10-10T23:24:48.542Z'
updated: '2026-03-22T13:10:36.894Z'
tags:
  - flow
  - customer-portal
summary: Customer Onboarding Flow
feature_area: Customer Portal
related_prds:
  - PRD-043
example: true
---

## Steps

### Step 1: First login triggers the wizard

Customer completes email verification and logs in for the first time. The portal reads the `onboarding.wizard.status` preference (absent or `not_started`). The Onboarding Wizard overlay renders on top of the dashboard. Dashboard content is visible but dimmed behind the overlay.

### Step 2: Welcome — account summary

The wizard displays Step 1: a welcome message with the customer's display name, their account tier badge, and a brief description of the portal's three main sections (Tickets, Notifications, Settings). Customer clicks "Let's go" to continue.

### Step 3: Set notification preferences

The wizard displays Step 2: the notification preferences form embedded in the wizard. Customer toggles notification categories on or off. Customer clicks "Save and continue". The portal sends an `UpdateNotificationSettings` mutation. Wizard progress is written to the Preference Service (`onboarding.wizard.last_step = 2`).

### Step 4: Optional ticket submission

The wizard displays Step 3 with an optional guided ticket form. Customer can either fill in the subject and description and click "Submit ticket" to create a real ticket, or click "Skip for now". Either path advances to Step 4.

### Step 5: Search demo

The wizard displays Step 4: a search bar pre-populated with an example query. Customer can edit the query and press Enter to see live search results from the portal search integration. Results appear within the wizard panel. Customer clicks "Continue" to advance.

### Step 6: Completion

The wizard displays Step 5: a summary card listing the portal's key features with links to relevant sections (Submit a Ticket, View Notifications, Manage Settings). Customer clicks "Take me to the dashboard". The wizard closes, the overlay dismisses, and a welcome notification appears in the Notification Center. `onboarding.wizard.status` is set to `completed`.

## Expected Results

- The wizard is shown exactly once, on the customer's first login
- Notification preferences saved in Step 3 are immediately active
- Optional ticket created in Step 4 appears in the customer's ticket list
- A welcome notification is delivered to the Notification Center on wizard completion
- The wizard does not appear on subsequent logins

## User Info

| Field | Value |
|-------|-------|
| Role | New customer (first login, email verified) |
| Permissions | Can read and write own preferences, create support tickets |
| Test account | portal-test-new@example.com (account created same day, wizard status: not_started) |
| Environment | Staging (portal.staging.example.com) |
| Prerequisites | Customer must have completed email verification; account must be < 14 days old |
