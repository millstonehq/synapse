---
id: SOP-049
type: sop
title: Search Index Rollback SOP
status: approved
owner: SRE Lead
created: '2024-02-21T00:26:03.210Z'
updated: '2025-04-19T08:20:20.763Z'
tags:
  - sop
  - search-platform
summary: Search Index Rollback SOP
related_process: PROCESS-029
related_systems:
  - SYSTEM-021
example: true
---

## Preconditions

- A recent index alias swap or schema deployment has caused query quality degradation, elevated error rates, or incorrect result counts
- The previous index version is still available in the cluster (indexes are retained 48 hours post-swap)
- The production alias name and the old index name are known
- The on-call SRE and Platform Lead are informed of the rollback decision

## Materials/Access

- Elasticsearch alias management API: `POST /_aliases`
- `GET /_cat/aliases?v` to inspect current alias state
- `GET /_cat/indices?v` to confirm the old index is still present
- Grafana: Search Query Performance and Index Health dashboards
- Change ticket ID for the original index deployment that is being rolled back

## Procedure

1. Post in #search-incidents: "Initiating index rollback for [alias-name]. Rolling back from [new-index-name] to [old-index-name]. Reason: [brief description]."
2. Confirm the old index is still present and healthy: `GET /_cat/indices?v` — look for the old index name with status `green` and a document count matching the expected value.
3. Confirm the production alias currently points to the new index: `GET /_cat/aliases?v`. Note the exact alias name and current target index.
4. Execute the atomic alias swap to restore the old index: `POST /_aliases` with the body `{"actions": [{"remove": {"index": "<new-index>", "alias": "<alias-name>"}}, {"add": {"index": "<old-index>", "alias": "<alias-name>"}}]}`.
5. Immediately verify the alias now points to the old index: `GET /_cat/aliases?v`. Confirm the old index name appears in the alias output.
6. Run 3-5 representative test queries and confirm results are consistent with pre-deployment behavior.
7. Monitor Grafana for 10 minutes: confirm query error rate and P95 latency have returned to pre-deployment baselines.
8. Post in #search-incidents: "Index rollback complete. Alias [alias-name] now pointing to [old-index-name]. Metrics stable."
9. Update the original change ticket with rollback timestamp, reason, and post-rollback metrics. Schedule a post-incident review within 48 hours.

## Validation

- `GET /_cat/aliases?v` confirms the production alias points to the old index
- Query error rate has returned to pre-deployment baseline
- P95 query latency has returned to pre-deployment baseline
- Test query spot check shows results consistent with expected pre-deployment behavior

## Rollback

1. If the alias swap itself fails (e.g., API error), attempt the swap again using the same command — alias updates are idempotent.
2. If the old index has been deleted (outside the 48-hour retention window), a rollback is not possible via this SOP — escalate to Platform Lead to initiate a full index rebuild from source data.
3. Document any partial actions taken and their outcomes in the incident ticket.
