---
id: SOP-046
type: sop
title: Update Search Synonyms Dictionary SOP
status: deprecated
owner: DevOps Lead
created: '2025-04-29T02:38:12.328Z'
updated: '2025-07-01T12:50:15.172Z'
tags:
  - sop
  - search-platform
summary: Update Search Synonyms Dictionary SOP
related_process: PROCESS-065
related_systems:
  - SYSTEM-023
example: true
---

## Preconditions

- The synonym additions or removals have been reviewed and approved by the Search Platform team lead
- The synonyms file is stored in version control; a PR with the changes has been merged
- You have confirmed that adding the new synonyms will not cause unexpected result collisions by testing in staging
- No active reindex or cluster scaling operation is in progress

## Materials/Access

- Access to the Elasticsearch cluster management APIs
- The updated synonyms file committed to the config repository
- Elasticsearch Analyze API to validate synonym tokenization
- Grafana: Search Query Performance dashboard to monitor post-update query behavior
- Kibana Dev Tools or cURL for executing API calls against the cluster

## Procedure

1. Verify the updated synonyms file has been deployed to the cluster's shared config path (or the object storage location referenced by the index settings) by checking the last-modified timestamp or file hash.
2. Test the new synonyms using the Analyze API before reloading: `POST /<index-name>/_analyze` with `{"analyzer": "synonym_analyzer", "text": "<test phrase>"}`. Confirm the synonyms expand as expected.
3. Reload the synonyms on the live index without a full reindex using the Update Index Settings API: `POST /<index-name>/_reload_search_analyzers`. This hot-reloads synonym files without downtime on Elasticsearch 7.3+.
4. Verify the reload succeeded by checking the response — it should list each node and confirm the analyzer was reloaded successfully with no errors.
5. Test several representative queries in production that should exercise the new synonyms. Confirm the expected synonym-expanded results appear.
6. Monitor Grafana's Search Query Performance dashboard for 10 minutes post-reload: check that zero-result rate has not increased (unexpected synonym collisions can cause query failures) and that P95 latency is stable.
7. Update the synonyms change log in the config repository with the list of additions/removals, the reason, and the deployment timestamp.

## Validation

- `POST /_analyze` confirms the new synonyms produce the expected token output
- Representative test queries return results that demonstrate synonym expansion is working
- Zero-result rate on Grafana has not increased after the reload
- The synonyms change log is updated with the deployment record

## Rollback

1. Revert the synonyms file to the previous version in version control and deploy the reverted file to the cluster config path.
2. Execute `POST /<index-name>/_reload_search_analyzers` again to reload the reverted synonyms.
3. Verify the rollback by running the Analyze API and confirming the new synonyms no longer appear in token output.
4. Open a post-incident ticket to analyze why the synonym update caused problems before attempting the change again.
