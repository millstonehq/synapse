---
id: SOP-067
type: sop
title: Handle Container Registry Quota SOP
status: review
owner: SRE Lead
created: '2024-06-19T09:41:20.900Z'
updated: '2025-10-30T08:10:43.748Z'
tags:
  - sop
  - ci-cd-platform
summary: Handle Container Registry Quota SOP
related_process: PROCESS-037
related_systems:
  - SYSTEM-035
example: true
---

## Preconditions

- A CI pipeline job is failing with an error indicating container registry quota exhaustion (e.g., "QUOTA_EXCEEDED," "storage quota limit reached," or "too many requests — rate limited")
- You have identified whether the issue is storage quota exhaustion or API rate limiting (these require different remediation)
- You have admin access to the container registry management console

## Materials/Access

- Admin access to the container registry (GCR, ECR, GHCR, or organization-hosted Harbor instance)
- Access to the registry's usage dashboard showing current storage and quota consumption
- The retention policy configuration for the registry
- Access to #platform-ops Slack channel for team notification

## Procedure

1. Log into the registry management console and navigate to the quota/usage dashboard; confirm the specific quota that is exhausted (storage GB, image count, or API request rate).
2. Notify #platform-ops: "Registry quota issue detected on [registry-name]. Investigating. Expect up to [N] minutes of pipeline impact."
3. If storage quota is exhausted: run the registry garbage collection tool (for Harbor: `Harbor UI → System → Garbage Collection`; for ECR: use the lifecycle policy API) to reclaim space from untagged and orphaned layers.
4. Identify the top consumers of registry storage by listing image repositories sorted by size; delete images that are older than 90 days in feature branch namespaces using the registry's bulk delete API.
5. If image count quota is exhausted: apply a retention policy that keeps only the 10 most recent tags per repository, removing all others. Confirm no production-pinned tags are deleted.
6. If API rate limiting is the cause: identify the pipeline jobs consuming the most registry API calls and add pull-through caching for frequently used base images to reduce external registry requests.
7. Re-trigger the failing pipeline job to confirm quota is no longer blocking it.
8. If quotas cannot be immediately resolved, request a quota increase from the registry vendor or infrastructure team and document the request in the #platform-ops channel.

## Validation

- The failing pipeline job that triggered this SOP now succeeds without quota errors
- The registry usage dashboard shows storage consumption below 80% of the quota limit
- No production image tags have been deleted during cleanup (verify by checking deployment records against remaining registry tags)

## Rollback

1. If production image tags were inadvertently deleted during cleanup, escalate immediately: open a P1 incident and attempt to restore from backup if the registry supports it.
2. If the garbage collection or retention policy run corrupts registry metadata, contact the registry vendor support team and freeze all new pushes until the issue is resolved.
3. Document all images deleted during cleanup in the #platform-ops channel with timestamps for audit purposes.
