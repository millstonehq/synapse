---
id: TDD-008
type: tdd
title: RBAC Permission Engine TDD
status: approved
owner: Tech Lead
created: '2024-04-22T13:28:07.379Z'
updated: '2026-10-03T16:14:02.156Z'
tags:
  - tdd
  - user-authentication
summary: RBAC Permission Engine TDD
related_adrs:
  - ADR-0006
  - ADR-0009
example: true
---

## Summary

Design a Role-Based Access Control (RBAC) Permission Engine that evaluates user permissions at request time based on roles assigned in Auth0 (as adopted in [[ADR-0006|ADR-0006: Adopt Auth0 as Identity Provider]]) and enriches JWT claims with a flattened permission list. The engine resolves role-to-permission mappings and caches results in Redis (as described in [[ADR-0009|ADR-0009: Choose Redis for Session Storage]]) to minimize latency impact on the token issuance path.

## Overview

The RBAC Permission Engine is a library embedded in the OAuth Authorization Server that resolves permissions for a user at token issuance time. Rather than performing permission checks at each resource server (which would require distributed policy evaluation), permissions are resolved once at token issuance and embedded in the JWT `permissions` claim.

Key design principles:
- **Claim-embedded permissions**: All permissions are resolved at token issuance and embedded in the access token; resource servers do simple claim presence checks rather than policy engine calls
- **Role hierarchy**: Roles can inherit permissions from parent roles, allowing a compact role definition without duplicating permissions across similar roles
- **Org-scoped permissions**: Permissions are always scoped to an organization; a user can have different roles in different organizations
- **Cache-first resolution**: Role-to-permission mappings are cached aggressively (24-hour TTL) since they change infrequently; user role assignments are cached for 60 seconds

## Architecture

- **Role Registry**: Stores role definitions (name, description, permissions list, parent roles) in PostgreSQL. Loaded into an in-memory role graph on service startup with background refresh every 5 minutes.
- **Assignment Store**: Stores user-to-role assignments scoped by organization ID. Backed by Auth0 user metadata with a local Redis cache (60-second TTL) to reduce Auth0 API calls during burst token issuance.
- **Permission Resolver**: Given a user ID and org ID, looks up assigned roles from the Assignment Store, resolves inherited permissions via the role graph, deduplicates, and returns a flattened permission list.
- **Claim Enricher**: Called during JWT assembly to add the `roles` and `permissions` claims to the access token.
- **Admin API**: REST endpoints for managing role definitions and user role assignments, callable by platform administrators.

## Information Model

- **Role**: Role ID, name, description, direct permissions (string list), parent role IDs
- **Permission**: Permission string in `resource:action` format (e.g., `users:read`, `billing:write`)
- **UserRoleAssignment**: User ID, org ID, role IDs (list), assigned-at, assigned-by
- **PermissionCacheEntry**: User ID + org ID key, resolved permission list, cached-at

## Interfaces

- `GET /internal/permissions?user_id=&org_id=` — Internal endpoint for permission resolution (used by token issuer)
- `POST /admin/roles` — Create a new role definition
- `PUT /admin/roles/{id}` — Update role permissions or parent roles
- `GET /admin/users/{id}/roles` — List role assignments for a user across organizations
- `POST /admin/users/{id}/roles` — Assign roles to a user in an organization
- `DELETE /admin/users/{id}/roles/{role_id}` — Remove a role assignment

## Files and Layout

```
rbac-permission-engine/
├── internal/
│   ├── registry/
│   │   └── role_registry.go       # Role definitions and hierarchy graph
│   ├── assignment/
│   │   └── assignment_store.go    # User-role assignments with cache
│   ├── resolver/
│   │   └── permission_resolver.go # Role graph traversal and flattening
│   ├── enricher/
│   │   └── claim_enricher.go      # JWT claim population hook
│   └── admin/
│       └── handler.go             # Admin API handlers
└── migrations/
    └── 001_rbac_schema.sql        # PostgreSQL schema for roles and assignments
```

## Work Plan

1. **Phase 1 — Data model and schema**: Define PostgreSQL schema for roles and assignments. Seed default platform roles (admin, member, viewer, billing_admin). Target: Week 1.
2. **Phase 2 — Role registry**: Implement role definition storage and in-memory role graph with hierarchy resolution. Unit tests for circular inheritance detection. Target: Week 2.
3. **Phase 3 — Assignment store with caching**: Implement Auth0-backed assignment store with Redis cache. Target: Week 3.
4. **Phase 4 — Permission resolver and claim enricher**: Integrate with OAuth Authorization Server token issuance path. Benchmark to ensure < 5ms P99 addition to token issuance latency. Target: Week 4.
5. **Phase 5 — Admin API**: Implement role and assignment management endpoints with Auth0 webhook sync. Target: Week 5.
6. **Phase 6 — Migration**: Migrate existing role-like attributes from Auth0 metadata to the new RBAC store. Validate claim equivalence before cutting over. Target: Week 7.

## Risks and Mitigations

- **Risk**: Backward-incompatible change to JWT claim schema breaks existing resource server authorization logic. Mitigation: Deploy with both old and new claim formats for a 30-day overlap period; update resource servers to use new format before removing old claims.
- **Risk**: Role hierarchy allows inadvertent privilege escalation through inherited permissions. Mitigation: Require admin approval for role definition changes; add a permission diff view in the admin UI when editing role hierarchies.
- **Risk**: Redis cache miss during burst token issuance causes latency spikes from Auth0 API calls. Mitigation: Pre-warm cache on startup for all roles with active users; set cache miss timeout to 2 seconds to fail fast rather than pile up.
