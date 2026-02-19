---
id: SOP-050
type: sop
title: Search Service Circuit Breaker Reset SOP
status: approved
owner: DevOps Lead
created: '2025-12-14T19:13:44.465Z'
updated: '2026-01-04T05:01:30.907Z'
tags:
  - sop
  - search-platform
summary: Search Service Circuit Breaker Reset SOP
related_process: PROCESS-065
related_systems:
  - SYSTEM-022
example: true
---

## Preconditions

- The search service's circuit breaker is in OPEN state, causing queries to fail-fast with circuit breaker errors rather than reaching the Elasticsearch cluster
- You have confirmed the underlying cause that originally tripped the circuit breaker (e.g., cluster unavailability, latency spike) has been resolved
- The Elasticsearch cluster health is green and query latency has returned to normal levels
- The on-call engineer is informed and monitoring during the reset

## Materials/Access

- Access to the search service's circuit breaker control plane (service admin API or feature flag console)
- Grafana: Search Query Performance dashboard (error rate, circuit breaker state, P95 latency)
- Elasticsearch cluster health API to confirm the cluster is healthy before reset
- #search-incidents Slack channel for status communication

## Procedure

1. Confirm the Elasticsearch cluster is healthy before resetting the circuit breaker: `GET /_cluster/health` must return `green`. Also verify P95 query latency on Grafana is within SLO (below 200ms) for at least 3 consecutive minutes.
2. Post in #search-incidents: "Preparing to reset search service circuit breaker. Cluster is healthy. On-call: [name]."
3. Transition the circuit breaker from OPEN to HALF-OPEN state using the service admin API or configuration panel. In HALF-OPEN state, a limited probe of queries will be allowed through to test cluster responsiveness.
4. Monitor the probe query error rate on Grafana for 2 minutes. In HALF-OPEN state, a single error will return the circuit breaker to OPEN — if this happens, re-investigate the cluster before trying again.
5. If the probe queries succeed, close the circuit breaker (transition from HALF-OPEN to CLOSED) to resume normal traffic flow.
6. Monitor query error rate and P95 latency on Grafana for 10 minutes post-reset. Confirm error rate is below 0.5% and latency is within SLO.
7. If metrics are stable after 10 minutes, post in #search-incidents: "Circuit breaker reset complete. Search service fully restored. Metrics stable."
8. Update the incident ticket with the timeline of events, root cause of the original trip, and the reset timestamp.

## Validation

- Circuit breaker is in CLOSED state (confirmed via admin API or service health endpoint)
- Query error rate is below 0.5% for 10 consecutive minutes post-reset
- P95 query latency is within SLO (below 200ms)
- No new circuit breaker trips occur within the 10-minute monitoring window

## Rollback

1. If the circuit breaker trips again immediately after reset, do not attempt multiple rapid resets — each failed reset prolongs recovery.
2. Return the circuit breaker to OPEN state and re-investigate the Elasticsearch cluster for residual issues.
3. Escalate to the Platform Lead if two consecutive reset attempts have failed; do not attempt a third without expert guidance.
