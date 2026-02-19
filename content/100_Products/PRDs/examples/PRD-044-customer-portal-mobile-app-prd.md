---
id: PRD-044
type: prd
title: Customer Portal Mobile App PRD
status: approved
owner: Head of Product
created: '2025-05-19T19:27:16.299Z'
updated: '2025-10-13T22:48:46.807Z'
tags:
  - prd
  - customer-portal
summary: Customer Portal Mobile App PRD
related_tdds:
  - TDD-044
  - TDD-045
example: true
related_standards:
  - STANDARD-052
---

## Summary

Build a native mobile application for iOS and Android that provides customers with a mobile-optimized Customer Portal experience: push notifications for ticket updates, quick ticket submission from a mobile device, and fast access to account status. The app shares the Customer API Gateway GraphQL API with the web portal, leveraging the search integration from [[TDD-044|TDD-044]] and the real-time update infrastructure from [[TDD-045|TDD-045]].

## Goals

- Serve the 34% of portal sessions that are currently mobile, which suffer from poor performance on the existing desktop-first web app
- Achieve a 15% increase in mobile session completion rate (sessions where the customer completes the intended task)
- Enable push notifications for ticket status changes, reducing time-to-awareness from hours to minutes for mobile customers
- Achieve >= 4.3 / 5.0 average rating in App Store and Google Play within 60 days of launch

## In Scope

- Native iOS (Swift) and Android (Kotlin) apps
- Authentication via existing SSO (OAuth 2.0 / PKCE flow)
- Dashboard: account summary, open ticket count, recent activity
- Ticket list, ticket detail, ticket creation, and comment submission
- Push notifications for ticket status changes and new notifications
- Portal search integrated from the mobile app search bar
- Account settings (display name, language, notification preferences)

## Out of Scope

- Chat support widget (web-only in v1; mobile chat is a future phase)
- Biometric authentication (Face ID / fingerprint — planned for v1.1)
- Offline support (cached data viewable offline — future phase)
- Tablet-optimized layout (phone layout only in v1)

## Users and Flows

**Mobile-first customers**: The 34% of customers who primarily access the portal from a mobile device. These customers have historically had a poor experience on the desktop-optimized web app.

**Notification-driven customers**: Customers who primarily interact with the portal reactively — they receive a push notification about a ticket update and open the app to read and respond.

## Requirements

- App must support iOS 16+ and Android 10+
- Authentication must use OAuth 2.0 Authorization Code with PKCE; tokens must be stored in the device keychain / keystore
- Dashboard must display account summary, open ticket count, and the 5 most recent activity items
- Ticket list must support pull-to-refresh and paginated scroll
- Ticket creation must accept a subject, description, and photo attachment from the device camera or photo library
- Push notifications must be delivered for ticket status changes and new notifications within 60 seconds of the event
- Search bar must query the portal search integration and display results grouped by type (tickets, help articles, activity)
- App must display a connectivity error if the API Gateway is unreachable

## KPIs

- **Mobile session completion rate**: >= 50% (up from 35% on mobile web)
- **Push notification open rate**: >= 40% within 5 minutes of delivery
- **App Store / Play Store rating**: >= 4.3 within 60 days of launch
- **App crash rate**: < 0.1% of sessions

## Information Architecture

Mobile app documentation:

- This PRD defines mobile product requirements
- TDD-044 covers search integration (shared API with mobile)
- TDD-045 covers real-time update infrastructure (used for push notification delivery)
- A dedicated mobile app runbook covers crash triage and push notification delivery failures

## Data Model

The mobile app consumes the same Customer API Gateway GraphQL API as the web portal. No new data model is introduced. Mobile-specific additions:

- **DeviceToken**: `{ customerId, platform: (ios|android), token, updatedAt }` — stores push notification device tokens; persisted in the Customer Notification Ingestion Service

Relationships:
- Customer has many DeviceTokens (1:N), one per device

## Non-Functional

- All API calls must be authenticated with a short-lived JWT (15-minute expiry) with silent token refresh using a refresh token
- Device tokens must be re-registered on app launch; stale tokens must be cleaned up by the notification service
- App binary size must not exceed 50 MB on iOS or Android to minimize download friction on mobile data
- App must handle background app refresh for push notification pre-fetching on iOS

## Constraints

- Must use the Customer API Gateway GraphQL API; no direct calls to backend services
- Push notification delivery must use APNs (iOS) and FCM (Android); no third-party push service
- Budget: 4 engineers for 16 weeks (2 iOS, 2 Android)
- App store submission reviews add 1–3 days latency to each release; release calendar must account for this

## Risks

- **App store review rejection** could delay launch. Mitigation: submit a TestFlight / internal test track build 2 weeks before target launch date; address any review issues in that window.
- **Push notification delivery failure** if APNs or FCM has an outage. Mitigation: monitor push delivery success rate; fall back to in-app notification badge on next app open if push is undelivered after 5 minutes.
- **GraphQL API changes** could break the mobile app if breaking changes are deployed to the web without mobile coordination. Mitigation: use versioned persisted queries; mobile team must approve any breaking schema changes.

## Milestones

### M1: Authentication and Dashboard (Week 1-5)

#### Deliverables

- OAuth 2.0 PKCE authentication flow (iOS and Android)
- Dashboard screen with account summary and activity list
- Ticket list and ticket detail screens

#### Acceptance Criteria

- Customer can sign in and sign out successfully
- Dashboard displays correct data from the API Gateway
- Ticket list loads and paginates correctly

### M2: Ticket Actions and Push Notifications (Week 6-11)

#### Deliverables

- Ticket creation form with camera/photo attachment
- Comment submission on open tickets
- Push notification registration (APNs + FCM)
- Push notifications for ticket status changes

#### Acceptance Criteria

- Customer can create a ticket with a photo attachment from a device
- Push notification received within 60 seconds of a ticket status change in a staging environment test
- Device token registration succeeds on app launch

### M3: Search, Settings, and Launch (Week 12-16)

#### Deliverables

- Search bar integrated with portal search API
- Account settings screen (display name, language, notification preferences)
- Beta test with 100 volunteer customers (TestFlight and Android internal track)
- App Store and Google Play submission

#### Acceptance Criteria

- Search returns grouped results within 2 seconds P95
- Settings changes saved and reflected in the web portal
- Beta test crash rate < 0.1%
- App approved and available in both stores
