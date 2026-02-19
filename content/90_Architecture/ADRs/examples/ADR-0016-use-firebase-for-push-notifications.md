---
id: ADR-0016
type: adr
title: Use Firebase for Push Notifications
status: approved
owner: Principal Engineer
created: '2024-05-14T05:30:57.968Z'
updated: '2026-10-19T09:14:59.631Z'
tags:
  - adr
  - notification-service
summary: Use Firebase for Push Notifications
example: true
---

## Context

The Notification Platform needs to deliver push notifications to iOS and Android mobile devices. Push notification delivery to mobile platforms requires integration with platform-specific provider systems: Apple Push Notification service (APNs) for iOS and either Firebase Cloud Messaging (FCM) or a direct manufacturer-specific service for Android.

We need to decide how to structure the Android push delivery integration. The two primary options are: using Firebase Cloud Messaging as a unified abstraction layer over both APNs and Android, or integrating directly with APNs for iOS and maintaining a separate Android integration pathway. Additionally, some enterprise customers are requesting support for web push notifications, which is a third delivery surface to consider.

## Decision

We will use **Firebase Cloud Messaging (FCM)** as the delivery layer for Android push notifications, and continue using APNs directly for iOS. We will not use FCM as a unified layer for both iOS and Android.

FCM v1 HTTP API will be used (not the legacy REST API). Service account credentials will be rotated every 90 days and stored as Kubernetes Secrets. The Push Notification Gateway will maintain separate APNs and FCM adapter implementations behind the `PushProvider` interface.

## Consequences

**Positive:**
- FCM is the de facto standard for Android push delivery and is supported by all Android device manufacturers
- FCM v1 API provides per-message delivery reports and richer error codes than the legacy API
- Maintaining separate APNs and FCM adapters gives us fine-grained control over platform-specific features (APNs push types, FCM Android notification channels, collapse keys)
- FCM's free tier covers our current volumes with no per-message cost

**Negative:**
- Two separate provider integrations to maintain (APNs and FCM) rather than one unified FCM layer for both platforms
- FCM dependency means all Android push delivery is routed through Google's infrastructure; no fallback for Android if FCM is unavailable
- Service account credential management adds operational overhead (90-day rotation)

**Neutral:**
- Web push support is deferred and will be evaluated as a separate ADR when there is product demand for it

## Alternatives Considered

**FCM as unified iOS + Android layer:**
- Pro: Single integration for both platforms; FCM handles APNs forwarding transparently
- Con: Adding a hop through FCM for iOS introduces additional latency and a dependency; FCM's APNs forwarding does not expose the full set of APNs-specific features (e.g., `apns-collapse-id`, `apns-push-type` control)
- Rejected because: iOS is our higher-engagement platform and we want full access to APNs features without working around FCM's abstraction layer

**OneSignal or similar managed push service:**
- Pro: Handles both APNs and FCM, includes analytics dashboard, simpler integration
- Con: Adds a paid third-party dependency into the critical notification path; less control over retry behavior and delivery prioritization; per-notification costs at scale
- Rejected because: We want to maintain direct provider relationships and avoid adding a vendor to the critical delivery path
