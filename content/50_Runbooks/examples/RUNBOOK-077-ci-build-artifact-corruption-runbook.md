---
id: RUNBOOK-077
type: runbook
title: CI Build Artifact Corruption Runbook
status: draft
owner: On-Call Engineer
created: '2024-05-15T16:36:08.610Z'
updated: '2026-06-11T06:42:28.356Z'
tags:
  - runbook
  - ci-cd-platform
summary: CI Build Artifact Corruption Runbook
example: true
---

## Service

- **System**: [[SYSTEM-032|Artifact Registry]]
- **Owner team**: Platform Engineering
- **On-call rotation**: PagerDuty schedule "platform-oncall"
- **Slack channel**: #platform-incidents
- **Runtime**: Harbor 2.9.x / Kubernetes / PostgreSQL 15 / MinIO S3

## Alerts

- `harbor_manifest_pull_error_rate_high` - Manifest pull errors exceed 5% for 2 minutes
- `harbor_gc_job_failed` - Nightly garbage collection job exited with a non-zero status
- `harbor_db_connection_pool_exhausted` - Harbor PostgreSQL connections below 5% available
- `artifact_registry_push_failure_rate_high` - Image push failure rate exceeds 2% for 5 minutes
- `harbor_blob_storage_utilization_critical` - S3 bucket utilization exceeds 85%

## Diagnosis Steps

1. **Identify the failure scope** - Determine whether the issue affects pulls only, pushes only, or both. Run `curl -sk https://harbor.example.com/api/v2.0/ping` to check Harbor API health. If Harbor API is unresponsive, the problem is at the infrastructure level; skip to Remediation Step 4.
2. **Check Harbor system logs** - Inspect the `harbor-core` and `harbor-registry` pods: `kubectl logs -n harbor deployment/harbor-core --tail=100 | grep -i error`. Common errors: `manifest unknown` (manifest record missing from DB), `blob unknown` (layer missing from storage), `too many connections` (DB pool exhaustion).
3. **Verify the specific manifest or blob** - For a named image that is failing, check whether the manifest exists in the Harbor DB: query `harbor` database table `harbor_artifact` for the image name and tag. If the record is absent, the artifact was not pushed or was corrupted during GC.
4. **Check recent GC job status** - Inspect the GC job log via the Harbor Admin UI (Administration → Garbage Collection → History). If the most recent GC run shows an error status, cross-reference the GC timestamp against the list of affected images — images pushed after the GC started may have been affected.
5. **Verify blob storage integrity** - For corrupted artifacts, check whether the blob layers exist in S3: `aws s3api head-object --bucket harbor-registry --key {layer-digest-path}`. Missing objects indicate a storage-level problem rather than a database issue.

## Remediation Steps

1. **If manifest records are missing and a recent backup exists**: Restore the affected manifest records from the Harbor PostgreSQL backup. Identify the backup point before the corruption, extract the `harbor_artifact` and `artifact_blob` rows for the affected images, and insert them into the current database. Re-trigger affected deployments after verification.
2. **If GC caused the corruption**: Halt any in-progress GC jobs immediately via the Harbor Admin UI (Administration → Garbage Collection → Stop). Do not re-run GC until the root cause is identified. Restore corrupted manifests from the most recent pre-GC backup.
3. **If blob layers are missing from S3**: Identify which CI build produced the affected image using the commit SHA in the image tag. Re-trigger the CI build for that commit to re-push the image with a fresh set of layers. Tag the image with the original SHA to avoid downstream reference changes.
4. **If Harbor API is completely unresponsive**: Check Harbor core pod health and PostgreSQL connectivity. If Harbor pods are crashlooping, scale down and restart: `kubectl rollout restart deployment/harbor-core -n harbor`. Check for OOM events with `kubectl describe pod`.
5. **If pushes are failing due to storage capacity**: Check MinIO bucket utilization. If above 85%, run an emergency GC dry-run to identify deletable objects, then proceed with full GC after verifying the list is safe.

## Escalation

| Time | Action |
|------|--------|
| 0 min | On-call engineer acknowledges alert and begins diagnosis |
| 10 min | Post initial assessment in #platform-incidents; notify CI/CD tech lead if deployments are blocked |
| 20 min | If not resolved: escalate to Platform team lead via PagerDuty schedule "platform-leads" |
| 30 min | If deployments are blocked for 30+ minutes: initiate SEV-2 incident process |
| 60 min | If not resolved: escalate to Engineering Manager; assess impact on release schedule |

## Dashboards

- [Harbor Overview](https://grafana.example.com/d/harbor-overview) - Push/pull error rates, GC job status, storage utilization
- [Artifact Registry Storage](https://grafana.example.com/d/harbor-storage) - S3 bucket size, growth rate, layer count
- [Harbor Database](https://grafana.example.com/d/harbor-db) - PostgreSQL connection pool, query latency, table sizes
- [CI Build Pipeline](https://grafana.example.com/d/ci-builds) - Build artifact push success rate, build durations
- [Harbor Logs](https://kibana.example.com/app/discover#/harbor) - Harbor core and registry error logs
