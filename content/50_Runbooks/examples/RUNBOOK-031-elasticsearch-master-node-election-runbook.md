---
id: RUNBOOK-031
type: runbook
title: Elasticsearch Master Node Election Runbook
status: approved
owner: On-Call Engineer
created: '2024-06-26T13:54:31.456Z'
updated: '2026-10-31T19:57:08.378Z'
tags:
  - runbook
  - search-platform
summary: Elasticsearch Master Node Election Runbook
example: true
---

## Service

- **System**: [[SYSTEM-021|Search Cluster]]
- **Owner team**: Search Platform Engineering
- **On-call rotation**: PagerDuty schedule "search-oncall"
- **Slack channel**: #search-incidents
- **Runtime**: Kubernetes / Elasticsearch 8 / 3-node dedicated master pool

## Alerts

- `search_no_master_node` - Elasticsearch cluster has no elected master node for more than 30 seconds
- `search_master_node_changed` - Master node election completed (informational; watch for repeated elections indicating instability)
- `search_cluster_not_green` - Cluster health is not green (often a symptom of master instability)

## Diagnosis Steps

1. **Confirm master election status** - Run `GET /_cat/master?v` to check whether a master is currently elected. If the command times out or returns an error, the cluster has no master and write operations are blocked.
2. **Check master-eligible node status** - Run `GET /_cat/nodes?v&h=name,master,ip,node.role`. Confirm the expected number of master-eligible nodes (`m` in node.role) are present in the cluster. A quorum (majority) of master-eligible nodes must be reachable for election to succeed.
3. **Check Elasticsearch logs on master-eligible nodes** - Use `kubectl logs` or your log aggregation tool to review the logs on master-eligible pods. Look for `master not discovered yet` or `failed to join` messages that explain why election is failing.
4. **Check for network partitions** - Verify all master-eligible nodes can communicate with each other. Run a ping test between node IPs from inside the cluster network. A network partition preventing quorum will prevent master election.
5. **Check for JVM GC pauses** - A master node experiencing a very long GC pause may temporarily lose cluster leadership, triggering a new election. Check GC logs or Grafana JVM metrics for pause durations exceeding 30 seconds.

## Remediation Steps

1. **If a quorum of master-eligible nodes is present but election is not completing**: Restart one master-eligible node to break a potential split-brain deadlock. Use `kubectl rollout restart` on one master pod.
2. **If a master-eligible node has crashed and quorum is lost**: Bring the crashed node back online. Check `kubectl get pods -n search` for nodes in `CrashLoopBackOff` or `Error` state and investigate logs before restarting.
3. **If the network partition is confirmed**: Resolve the network issue first (escalate to infrastructure on-call). Once network connectivity is restored, Elasticsearch will automatically elect a new master within seconds.
4. **If GC pauses are causing repeated master leadership loss**: Increase the master node JVM heap and set GC tuning parameters. As an immediate measure, scale the master-eligible node pool to 5 nodes if it is currently 3, to provide more resilience to individual node pauses.
5. **Do NOT reduce master-eligible nodes below 3** - This will prevent quorum from ever being reached with a single node failure.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer confirms no master is elected and begins node check |
| 5 min | Post status in #search-incidents; search writes are blocked |
| 15 min | If not resolved: page Search Platform tech lead via PagerDuty |
| 30 min | If not resolved: page Engineering Manager; begin user communication |
| 60 min | Escalate to Elasticsearch vendor support if internal resolution is not possible |

## Dashboards

- [Search Cluster Overview](https://grafana.example.com/d/search-cluster-overview) - Master node identity, cluster health, node count
- [Search Cluster JVM](https://grafana.example.com/d/search-cluster-jvm) - GC pause duration, heap usage per master node
- [Kubernetes Search Namespace](https://grafana.example.com/d/k8s-search) - Pod health and restart count for master pods
