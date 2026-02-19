---
id: GUIDE-051
type: guide
title: Customer Portal API Integration Guide
status: approved
owner: Engineering Team
created: '2025-03-24T04:33:29.571Z'
updated: '2026-11-11T04:13:16.219Z'
tags:
  - guide
  - customer-portal
summary: Customer Portal API Integration Guide
audience: customer
related_systems:
  - SYSTEM-044
  - SYSTEM-042
related_sops:
  - SOP-083
  - SOP-087
example: true
---

## Overview of the Portal API

The Customer Portal frontend communicates with a dedicated BFF (Backend for Frontend) API at `/api/`. The BFF handles authentication, request authorization, data aggregation from upstream services, and response shaping. All portal API calls go through this BFF; the frontend never calls upstream microservices directly.

The BFF API follows the response format defined in the Customer API Response Format Standard: all responses use a top-level `data` key for success payloads and an `error` object for failures. Authentication is handled via HTTP-only session cookies set during the SSO login flow.

## Making API Calls from the Frontend

Use the portal's HTTP client wrapper (`src/lib/api-client.ts`) for all API calls — never call `fetch` directly:

```typescript
import { apiClient } from '@/lib/api-client';

// In a React Query hook:
const { data, isLoading, error } = useQuery({
  queryKey: ['account', accountId],
  queryFn: () => apiClient.get<Account>(`/accounts/${accountId}`),
});
```

The API client handles:
- Attaching the CSRF token header to mutating requests
- Mapping 4xx/5xx responses to typed `ApiError` objects
- Retrying idempotent requests on network failure (configurable)
- Logging request IDs for error tracking correlation

Do not bypass the client for any reason; if it is missing a feature you need, extend it and submit a PR.

## Handling API Errors

Every API call can fail. The portal's error handling pattern:

- **Form submission errors**: Display inline field errors using the `InlineError` component; map `error.code` values to user-facing messages via the error message catalog in `src/lib/error-messages.ts`
- **Page-level errors**: If data required to render a page fails to load, render the `PageError` component with a retry action
- **Background errors**: Log to Sentry via `captureApiError(error)` from `src/lib/error-tracking.ts`; do not surface background errors as blocking UI unless they affect critical functionality

Never display raw `error.message` strings from the API to customers; always use the catalog-mapped user-facing message.

## Authentication and Session Handling

The portal uses HTTP-only session cookies; no JWT tokens are accessible from JavaScript. Session expiry and renewal are handled automatically by the API client's response interceptor. If you receive a `401` response on an authenticated endpoint, the client will redirect the user to the login page.

For server components (Next.js), use the `getServerSession()` utility to access the session; do not attempt to read cookies directly.

## Testing API Integrations

Use Mock Service Worker (MSW) for integration tests of API-dependent components:

- Define request handlers in `src/mocks/handlers/` grouped by feature
- Use `server.use()` in individual tests to override default handlers for error scenarios
- Test both the happy path and the error state (network failure, 404, 500) for every data-fetching component
