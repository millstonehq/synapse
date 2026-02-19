---
id: GUIDE-012
type: guide
title: Adding RBAC to Your Microservice
status: approved
owner: Engineering Team
created: '2025-04-14T16:56:09.396Z'
updated: '2025-11-27T11:24:04.562Z'
tags:
  - guide
  - user-authentication
summary: Adding RBAC to Your Microservice
audience: customer
related_systems:
  - SYSTEM-008
  - SYSTEM-010
related_sops:
  - SOP-016
  - SOP-012
example: true
---

## Why RBAC Belongs in Your Service

Role-Based Access Control (RBAC) is not just a feature for the authentication service — every microservice that exposes protected operations needs to enforce authorization at its own boundary. Relying solely on the API gateway for authorization is insufficient; if a request bypasses the gateway or the gateway misconfigures a route, your service becomes an open door.

Our authentication tokens carry role and scope claims that your service can use to enforce fine-grained access control without making additional network calls.

## Reading Roles from JWT Claims

When a user authenticates, their JWT access token includes a `roles` claim (array of role strings) and a `scope` claim (space-separated OAuth scopes). Your service should validate the JWT (see GUIDE-007 for validation details) and then extract these claims for authorization decisions:

```typescript
const token = validateJWT(bearerToken, jwksClient);
const roles = token.roles ?? [];
const scopes = token.scope?.split(' ') ?? [];

if (!roles.includes('orders:admin') && !scopes.includes('orders:write')) {
  return res.status(403).json({ error: 'Insufficient permissions' });
}
```

Do not trust role claims from request headers or request body — only from the validated JWT.

## Defining Your Service's Roles

Define roles at the resource-action level. Follow the OAuth Scope Naming Standard: `<resource>:<action>`. For a service managing orders:

- `orders:read` — can read order data
- `orders:write` — can create and update orders
- `orders:admin` — can cancel, refund, or manage all orders regardless of ownership

Document your service's roles in the service registry and request them during OAuth client registration so they can be assigned to appropriate users.

## Enforcing Ownership

Roles grant access to a resource type; they do not automatically enforce data ownership. After confirming the user has the required role, verify they own or have explicit access to the specific resource being accessed:

```typescript
const order = await getOrder(orderId);
if (order.userId !== token.sub && !roles.includes('orders:admin')) {
  return res.status(403).json({ error: 'Access denied' });
}
```

This two-layer check (role check + ownership check) prevents privilege escalation where a user with a valid role accesses another user's resources.

## Testing Your RBAC Implementation

Write a test for each permission boundary in your service: correct role succeeds, missing role returns 403, wrong resource owner returns 403, and admin role bypasses ownership check where intended. Include these in your E2E test suite using the auth test helpers described in GUIDE-010.
