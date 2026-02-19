---
id: RUNBOOK-040
type: runbook
title: Schema Registry Unavailable Runbook
status: draft
owner: On-Call Engineer
created: '2025-10-12T16:42:04.986Z'
updated: '2026-12-25T02:38:09.134Z'
tags:
  - runbook
  - data-pipeline
summary: Schema Registry Unavailable Runbook
example: true
---

## Service

- **System**: [[SYSTEM-028|Schema Registry]]
- **Owner team**: Data Platform Engineering
- **On-call rotation**: PagerDuty schedule "data-platform-oncall"
- **Slack channel**: #data-incidents
- **Runtime**: Confluent Schema Registry / Kubernetes / Kafka

## Alerts

- `schema_registry_health_check_failed` - Schema Registry `/healthcheck` endpoint returning non-200 for 2 minutes
- `schema_registry_pod_not_running` - Schema Registry pod is not in Running state
- `kafka_producer_schema_registration_errors` - Producers unable to register or fetch schemas
- `schema_registry_leader_election_failed` - Schema Registry cluster has no leader node

## Diagnosis Steps

1. **Check Schema Registry pod status** - Run `kubectl get pods -n confluent -l app=schema-registry` to confirm pod state and restart count.
2. **Test the health endpoint directly** - Curl the health endpoint: `curl -s http://[schema-registry-host]:8081/subjects | head`. A connection refused or error response confirms the service is down.
3. **Review Schema Registry logs** - Run `kubectl logs -n confluent -l app=schema-registry --since=30m` and look for Kafka broker connectivity errors, disk space issues, or leader election failures.
4. **Check underlying Kafka broker connectivity** - Schema Registry uses Kafka as its storage backend; verify the Kafka cluster is healthy and the `_schemas` internal topic is accessible.
5. **Check Schema Registry configuration** - Confirm the `kafkastore.bootstrap.servers` and security configuration in the Schema Registry config map match the current Kafka cluster endpoints.
6. **Check for a recent version upgrade** - Review #data-releases for any Schema Registry version changes in the past hour.

## Remediation Steps

1. **If Schema Registry pod is crashlooping**: Inspect the pod exit reason, address the root cause (usually Kafka connectivity or config error), then restart: `kubectl rollout restart deployment/schema-registry -n confluent`.
2. **If Kafka broker is unreachable from Schema Registry**: Verify the network policy and service account permissions; restore Kafka broker connectivity before restarting Schema Registry.
3. **If leader election has failed in a multi-node cluster**: Restart all Schema Registry nodes sequentially; the cluster will re-elect a leader on startup.
4. **If producers are failing due to Schema Registry being down**: Producers with `schema.registry.url.unavailability.retry.ms` configured will retry; check if this is set and how long before alert escalation is warranted.
5. **If a recent upgrade caused the failure**: Roll back the Schema Registry Helm chart to the previous version.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges and tests Schema Registry endpoint |
| 10 min | Post status in #data-incidents; notify if Kafka producers are impacted |
| 20 min | If not resolved: page Data Platform tech lead |
| 45 min | If Kafka producers are backed up: escalate to Engineering Manager |

## Dashboards

- [Schema Registry Health](https://grafana.example.com/d/schema-registry) - Request rate, error rate, pod status
- [Kafka Producer Errors](https://grafana.example.com/d/kafka-producers) - Schema registration errors per topic
- [Confluent Platform Overview](https://grafana.example.com/d/confluent-platform) - Cluster health including Schema Registry
- [Kubernetes Confluent Namespace](https://grafana.example.com/d/k8s-confluent) - Pod restarts and resource usage
